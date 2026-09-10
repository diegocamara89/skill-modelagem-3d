"""check_intent.py - verifica se a geometria atende ao PEDIDO, nao se ela e bem formada.

Uso:
  python check_intent.py --malha peca.stl --requisitos req.json [--referencia ref.stl] [--json out.json]

POR QUE ESTA FERRAMENTA EXISTE: uma peca pode estar fechada, passar em todo portao de
malha, fatiar bem e ter o furo no lugar errado. Nenhuma verificacao de validade pega
isso. Validade e intencao sao eixos diferentes.

COMO FUNCIONA: cada requisito declara o proprio metodo de verificacao. Requisito sem
metodo implementado NAO e ignorado: aparece na entrega como nao verificado, com o motivo.
Silencio sobre requisito e o mesmo que reprovar sem dizer.

TIPOS IMPLEMENTADOS NESTA VERSAO:
  caixa                 dimensoes externas, com tolerancia
  volume                volume, com tolerancia
  n_solidos             quantidade de corpos desconexos
  furo                  existencia, posicao no plano e diametro, num eixo declarado
  n_furos_no_plano      quantidade de furos numa secao
  distancia_entre_furos entre dois furos detectados na mesma secao
  regiao_intacta        uma caixa da peca continua igual a referencia, por amostragem
  interferencia         dois corpos nao ocupam o mesmo espaco

TIPOS DECLARADOS E NAO IMPLEMENTADOS AQUI: parede_minima, folga_entre, silhueta.
Eles saem no relatorio como nao verificados, com o motivo.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

EIXO = {"X": 0, "Y": 1, "Z": 2}

# Contrato tipado de resultado por requisito. CORRIGIDO 07/09/2026 depois da terceira
# revisao externa: antes, excecao na medicao virava "nao verificado", indistinguivel de
# tipo nao implementado, e o chamador podia contar isso como ausencia benigna.
APROVADA = "APROVADA"                 # medido e dentro do declarado
REPROVADA = "REPROVADA"               # medido e fora do declarado
NAO_IMPLEMENTADA = "NAO_IMPLEMENTADA"  # o tipo existe no contrato e nao tem medidor
ESPEC_INVALIDA = "ESPEC_INVALIDA"     # o requisito esta malformado
ERRO = "ERRO"                         # falha operacional: nada foi medido
INDETERMINADA = "INDETERMINADA"       # falta insumo declarado, como a referencia
ESTADOS = (APROVADA, REPROVADA, NAO_IMPLEMENTADA, ESPEC_INVALIDA, ERRO, INDETERMINADA)
NAO_IMPLEMENTADOS = {
    "parede_minima": "medicao de espessura minima nao implementada nesta versao",
    "folga_entre": "folga entre corpos depende de valor calibrado; consulte tolerance_lookup.py",
    "silhueta": "comparacao com imagem de referencia nao implementada nesta versao",
}


def carrega(caminho):
    import trimesh
    m = trimesh.load(caminho, force="mesh", process=False)
    if not hasattr(m, "faces"):
        raise SystemExit("nao e uma malha unica: " + caminho)
    m.merge_vertices()
    return m


class SecaoInvalida(Exception):
    pass


def aneis_da_secao(malha, eixo, valor, exigir_valida=True):
    """Delegado a secoes.py, PROPAGANDO o aviso de secao invalida.

    CORRIGIDO 07/09/2026 depois da terceira revisao externa. O aviso do modulo de secoes
    era descartado, entao "nenhum furo" e "nao consegui fechar os contornos" viravam a
    mesma coisa, e um requisito de zero furos podia ser APROVADO por falha de
    poligonizacao.
    """
    import secoes
    s = secoes.secao(malha, eixo, valor)
    if exigir_valida and s.get("aviso"):
        raise SecaoInvalida("secao no eixo %s em %.4f: %s" % ("XYZ"[eixo], valor, s["aviso"]))
    return s["material"], s["furos"]


def descreve_furo(p):
    import secoes
    return secoes.descreve(p)


# ---------- verificadores ----------

# Esquema minimo por tipo: campos obrigatorios e, quando o campo e vetor, o tamanho exato.
# CORRIGIDO 07/09/2026: sem isso, um requisito 'caixa' com UMA dimensao era comparado por
# zip, verificava so aquele eixo e podia APROVAR. Entrada malformada passa a ser erro de
# especificacao, nao aprovacao parcial.
ESQUEMA = {
    "caixa": {"valor": 3},
    "volume": {"valor": 1},
    "n_solidos": {"valor": 1},
    "furo": {"eixo": "eixo", "plano": 1, "posicao": 2, "diametro": 1},
    "n_furos_no_plano": {"eixo": "eixo", "plano": 1, "valor": 1},
    "distancia_entre_furos": {"eixo": "eixo", "plano": 1, "valor": 1},
    "regiao_intacta": {"caixa_min": 3, "caixa_max": 3},
    "interferencia": {},
}
TOLERANCIAS = ("tol_mm", "tol_mm3", "tol_pos_mm", "tol_fracao", "circularidade_min")


def valida_esquema(r):
    """Devolve lista de problemas de especificacao. Vazia significa requisito bem formado."""
    p = []
    tipo = r.get("tipo")
    if not r.get("id"):
        p.append("requisito sem 'id'")
    esq = ESQUEMA.get(tipo)
    if esq is None:
        return p
    for campo, forma in esq.items():
        if campo not in r:
            p.append("falta o campo obrigatorio '%s'" % campo)
            continue
        v = r[campo]
        if forma == "eixo":
            if str(v).upper() not in EIXO:
                p.append("'%s' tem que ser X, Y ou Z, e veio %r" % (campo, v))
        elif forma == 1:
            try:
                x = float(v)
                if not np.isfinite(x):
                    p.append("'%s' nao e finito: %r" % (campo, v))
            except (TypeError, ValueError):
                p.append("'%s' tem que ser numero, e veio %r" % (campo, v))
        else:
            if not isinstance(v, (list, tuple)):
                p.append("'%s' tem que ser lista de %d numeros, e veio %r" % (campo, forma, type(v).__name__))
            elif len(v) != forma:
                p.append("'%s' tem que ter exatamente %d valores, e veio %d" % (campo, forma, len(v)))
            else:
                for i, x in enumerate(v):
                    try:
                        if not np.isfinite(float(x)):
                            p.append("'%s'[%d] nao e finito: %r" % (campo, i, x))
                    except (TypeError, ValueError):
                        p.append("'%s'[%d] tem que ser numero, e veio %r" % (campo, i, x))
    for t in TOLERANCIAS:
        if t in r:
            try:
                x = float(r[t])
                if not np.isfinite(x) or x < 0:
                    p.append("'%s' tem que ser numero finito nao negativo, e veio %r" % (t, r[t]))
            except (TypeError, ValueError):
                p.append("'%s' tem que ser numero, e veio %r" % (t, r[t]))
    if tipo == "regiao_intacta" and not p:
        lo = [float(x) for x in r["caixa_min"]]
        hi = [float(x) for x in r["caixa_max"]]
        if any(a >= b for a, b in zip(lo, hi)):
            p.append("caixa_min tem que ser menor que caixa_max em todos os eixos")
    if tipo == "interferencia":
        tem_entre = isinstance(r.get("entre"), (list, tuple)) and len(r.get("entre") or []) == 2
        if not tem_entre and not r.get("com"):
            p.append("interferencia exige 'entre' com dois caminhos, ou 'com' com um")
    return p


def v_caixa(m, r, ctx):
    med = [float(x) for x in m.extents]
    esp = [float(x) for x in r["valor"]]
    tol = float(r.get("tol_mm", 0.05))
    dif = [abs(a - b) for a, b in zip(med, esp)]
    return max(dif) <= tol, {"medido_mm": [round(x, 4) for x in med],
                             "esperado_mm": esp, "maior_desvio_mm": round(max(dif), 4),
                             "tol_mm": tol}


def v_volume(m, r, ctx):
    if not m.is_watertight:
        return None, {"motivo": "malha nao fechada: volume nao e confiavel"}
    med = float(m.volume)
    esp = float(r["valor"])
    tol = float(r.get("tol_mm3", max(1.0, 0.01 * esp)))
    return abs(med - esp) <= tol, {"medido_mm3": round(med, 3), "esperado_mm3": esp,
                                   "desvio_mm3": round(abs(med - esp), 3), "tol_mm3": tol}


def v_n_solidos(m, r, ctx):
    n = len(m.split(only_watertight=False))
    return n == int(r["valor"]), {"medido": n, "esperado": int(r["valor"])}


def _mede_furo(m, eixo, plano, alvo):
    """Acha o furo mais proximo de alvo na secao e devolve a descricao, ou None."""
    _, furos = aneis_da_secao(m, eixo, plano)
    if not furos:
        return None, 0
    achados = [descreve_furo(p) for p in furos]
    dists = [float(np.linalg.norm(np.array(a["centro"]) - alvo)) for a in achados]
    k = int(np.argmin(dists))
    a = dict(achados[k])
    a["distancia_ao_alvo_mm"] = round(dists[k], 4)
    return a, len(achados)


def v_furo(m, r, ctx):
    """Verifica um furo em DUAS secoes e confere a forma, nao so a area.

    CORRIGIDO 07/09/2026 depois da segunda revisao externa. A versao anterior media UMA
    secao e decidia por centro e diametro equivalente calculado a partir da area. Com
    isso, uma abertura NAO circular de mesma area e mesmo centro passava; a circularidade
    era calculada e nao entrava na decisao; uma cavidade que existisse so naquela altura
    passava como furo; e nada determinava o eixo ao longo da profundidade.

    Agora: confere circularidade contra um piso, e confere a mesma abertura numa segunda
    secao deslocada ao longo do eixo, para o furo ter extensao e eixo, nao so area. Se a
    peca nao permitir a segunda secao, o resultado diz que a extensao NAO foi verificada.
    """
    e = EIXO[r["eixo"].upper()]
    plano = float(r["plano"])
    alvo = np.array([float(x) for x in r["posicao"]])
    a, n = _mede_furo(m, e, plano, alvo)
    if a is None:
        return False, {"motivo": "nenhum furo na secao", "eixo": r["eixo"],
                       "plano": plano, "n_furos_na_secao": 0}

    tol_pos = float(r.get("tol_pos_mm", 0.2))
    tol_d = float(r.get("tol_mm", 0.2))
    circ_min = float(r.get("circularidade_min", 0.90))
    erro_pos = a["distancia_ao_alvo_mm"]
    erro_d = round(abs(a["diametro_equivalente_mm"] - float(r["diametro"])), 4)
    circ_ok = a["circularidade"] >= circ_min

    # segunda secao, para o furo ter extensao ao longo do eixo declarado
    d2 = float(r.get("segunda_secao_mm", 0.0))
    if not d2:
        lo, hi = float(m.bounds[0][e]), float(m.bounds[1][e])
        margem = 0.05 * (hi - lo)
        d2 = (margem if plano - margem < lo + 1e-9 else -margem)
    b, _ = _mede_furo(m, e, plano + d2, alvo)
    if b is None:
        ext = {"verificada": False,
               "motivo": "a segunda secao em %+.3f mm nao tem furo: a extensao do furo ao "
                         "longo do eixo NAO foi verificada" % d2}
        ext_ok = False
    else:
        dc = float(np.linalg.norm(np.array(b["centro"]) - np.array(a["centro"])))
        dd = abs(b["diametro_equivalente_mm"] - a["diametro_equivalente_mm"])
        # CORRIGIDO 07/09/2026: a circularidade da segunda secao era medida e nao entrava
        # na decisao, entao uma segunda secao QUADRADA de mesma area e centro passava.
        circ2_ok = b["circularidade"] >= circ_min
        # CORRIGIDO 08/09/2026, depois de validacao adversarial: a decisao usava SOMENTE
        # o desvio entre as duas secoes, e apenas a PRIMEIRA era confrontada com o alvo.
        # Um furo de eixo inclinado passava com uma secao efetivamente medida FORA da
        # tolerancia. Reproduzido: bloco 20x20x10, furo d=4, primeira secao a 0,19 do
        # alvo e segunda a 0,29, com tolerancia 0,20 e desvio entre secoes de 0,10 ->
        # APROVADA. Agora CADA secao medida e confrontada com o pedido, e o desvio entre
        # secoes continua sendo conferido, porque ele pega conicidade e inclinacao que a
        # comparacao absoluta de duas amostras pode nao pegar.
        erro_pos_b = float(np.linalg.norm(np.array(b["centro"]) - alvo))
        erro_d_b = abs(b["diametro_equivalente_mm"] - float(r["diametro"]))
        pos_b_ok = erro_pos_b <= tol_pos
        diam_b_ok = erro_d_b <= tol_d
        ext_ok = (dc <= tol_pos and dd <= tol_d and circ2_ok
                  and pos_b_ok and diam_b_ok)
        ext = {"verificada": True, "deslocamento_mm": round(d2, 4),
               "desvio_de_centro_mm": round(dc, 4), "desvio_de_diametro_mm": round(dd, 4),
               "erro_de_posicao_da_segunda_mm": round(erro_pos_b, 4),
               "erro_de_diametro_da_segunda_mm": round(erro_d_b, 4),
               "posicao_da_segunda_ok": pos_b_ok,
               "diametro_da_segunda_ok": diam_b_ok,
               "circularidade_da_segunda_secao": b["circularidade"],
               "circularidade_da_segunda_ok": circ2_ok,
               "o_que_cada_numero_decide": (
                   "desvio_de_centro_mm e desvio_de_diametro_mm comparam as duas "
                   "secoes ENTRE SI, e pegam inclinacao e conicidade. "
                   "erro_de_posicao_da_segunda_mm e erro_de_diametro_da_segunda_mm "
                   "comparam a segunda secao com o PEDIDO. Os dois pares decidem: "
                   "concordancia entre amostras nao e atendimento ao pedido."),
               "segunda_secao": b, "passou": ext_ok}

    ok = bool(erro_pos <= tol_pos and erro_d <= tol_d and circ_ok and ext_ok)
    return ok, {"eixo": r["eixo"], "plano": plano, "n_furos_na_secao": n,
                "furo_mais_proximo": a,
                "posicao_esperada": alvo.tolist(), "erro_de_posicao_mm": erro_pos,
                "diametro_esperado_mm": float(r["diametro"]), "erro_de_diametro_mm": erro_d,
                "circularidade": a["circularidade"], "circularidade_min": circ_min,
                "circularidade_ok": circ_ok,
                "extensao_ao_longo_do_eixo": ext,
                "tol_pos_mm": tol_pos, "tol_diam_mm": tol_d,
                "o_que_isto_nao_diz": (
                    "duas secoes sao AMOSTRAGEM, e nao provam continuidade entre elas: duas "
                    "cavidades separadas por uma membrana de material produzem as mesmas duas "
                    "secoes. Conferir as duas pontas tambem nao prova furo passante. Para "
                    "afirmar passagem seria preciso verificacao volumetrica, que nao esta "
                    "implementada aqui.")}


def v_n_furos_no_plano(m, r, ctx):
    e = EIXO[r["eixo"].upper()]
    _, furos = aneis_da_secao(m, e, float(r["plano"]))
    return len(furos) == int(r["valor"]), {
        "medido": len(furos), "esperado": int(r["valor"]),
        "eixo": r["eixo"], "plano": r["plano"],
        "furos": [descreve_furo(p) for p in furos]}


def v_distancia_entre_furos(m, r, ctx):
    e = EIXO[r["eixo"].upper()]
    _, furos = aneis_da_secao(m, e, float(r["plano"]))
    if len(furos) < 2:
        return False, {"motivo": "menos de dois furos na secao", "n_furos": len(furos)}
    cs = [np.array(descreve_furo(p)["centro"]) for p in furos]
    par = r.get("entre")
    if par:
        alvos = [np.array([float(x) for x in q]) for q in par]
        idx = [int(np.argmin([np.linalg.norm(c - t) for c in cs])) for t in alvos]
    else:
        idx = [0, 1]
    med = float(np.linalg.norm(cs[idx[0]] - cs[idx[1]]))
    esp = float(r["valor"])
    tol = float(r.get("tol_mm", 0.2))
    return abs(med - esp) <= tol, {"medido_mm": round(med, 4), "esperado_mm": esp,
                                   "desvio_mm": round(abs(med - esp), 4), "tol_mm": tol,
                                   "centros_usados": [cs[idx[0]].tolist(), cs[idx[1]].tolist()]}


class ErroDeKernel(Exception):
    pass


def _manifold(x, rotulo="malha"):
    """Converte para o kernel de malha e CONFERE o status.

    CORRIGIDO 07/09/2026 depois da terceira revisao externa. O construtor devolve um
    Manifold VAZIO com status de erro quando a entrada nao forma um 2-manifold orientado,
    e o erro se propaga pelas operacoes. Decidir por volume sozinho nao distingue
    "resultado legitimamente vazio" de "operacao invalida": os dois dao zero.
    """
    import manifold3d as m3
    cls = m3.Mesh64 if hasattr(m3, "Mesh64") else m3.Mesh
    man = m3.Manifold(cls(
        vert_properties=np.ascontiguousarray(x.vertices, dtype=np.float64),
        tri_verts=np.ascontiguousarray(x.faces, dtype=np.uint32)))
    st = str(man.status())
    if "NoError" not in st:
        raise ErroDeKernel("%s recusada pelo kernel de malha: %s" % (rotulo, st))
    return man


def _confere_status(man, rotulo):
    st = str(man.status())
    if "NoError" not in st:
        raise ErroDeKernel("%s: resultado com status de erro no kernel: %s" % (rotulo, st))
    return man


def v_regiao_intacta(m, r, ctx):
    """Compara uma caixa da peca com a mesma caixa da referencia, por VOLUME de divergencia.

    Nao usa amostragem de pontos nem ponto-dentro-do-solido. A primeira versao usava
    contains do trimesh, que exige o modulo nativo rtree e nao existe neste ambiente, e
    devolvia amostragem aleatoria, que nunca prova igualdade. Aqui: recorta as duas pecas
    pela caixa e mede o volume da diferenca simetrica. Zero e zero, nao amostra.
    """
    import manifold3d as m3
    ref = ctx.get("referencia")
    if ref is None:
        return None, {"motivo": "requisito exige --referencia e nenhuma foi informada"}
    if not (m.is_watertight and ref.is_watertight):
        return None, {"motivo": "recorte booleano exige as duas malhas fechadas"}
    lo = np.array([float(x) for x in r["caixa_min"]], float)
    hi = np.array([float(x) for x in r["caixa_max"]], float)
    tam = hi - lo
    if (tam <= 0).any():
        return None, {"motivo": "caixa_min tem que ser menor que caixa_max em todos os eixos"}
    centro = (lo + hi) / 2.0
    caixa = m3.Manifold.cube(tam.tolist(), True).translate(centro.tolist())
    A = _confere_status(_manifold(m, "peca") ^ caixa, "recorte da peca")
    B = _confere_status(_manifold(ref, "referencia") ^ caixa, "recorte da referencia")
    va, vb = float(A.volume()), float(B.volume())
    d1 = _confere_status(A - B, "diferenca peca menos referencia")
    d2_ = _confere_status(B - A, "diferenca referencia menos peca")
    div = float(d1.volume()) + float(d2_.volume())
    v_caixa_mm3 = float(np.prod(tam))
    frac = div / v_caixa_mm3 if v_caixa_mm3 > 0 else 0.0
    tol = float(r.get("tol_fracao", 1e-9))
    return frac <= tol, {
        "caixa": [lo.tolist(), hi.tolist()],
        "volume_da_caixa_mm3": round(v_caixa_mm3, 4),
        "volume_da_peca_na_caixa_mm3": round(va, 4),
        "volume_da_referencia_na_caixa_mm3": round(vb, 4),
        "volume_de_divergencia_mm3": round(div, 6),
        "fracao_divergente": round(frac, 9), "tol_fracao": tol,
        "metodo": ("diferenca simetrica booleana dentro da caixa, com status do kernel "
                   "conferido em cada operando e em cada resultado"),
        "precisao": ("volume em ponto flutuante duplo; a tolerancia de fracao declarada e o "
                     "criterio, nao ha garantia de exatidao aritmetica")}


def v_interferencia(m, r, ctx):
    """Interferencia entre DOIS componentes.

    Aceita 'entre': [a, b] com dois arquivos, ou 'com': b para comparar com a malha
    principal. CORRIGIDO 07/09/2026: so existia a forma 'com', e num caso de montagem
    isso levou a comparar a montagem inteira com um componente dela, o que sempre
    acusa interferencia porque a montagem contem o componente. Interferencia e entre
    partes, nao entre o todo e a parte.
    """
    par = r.get("entre")
    if par and len(par) == 2:
        faltando = [p for p in par if not os.path.isfile(p)]
        if faltando:
            return None, {"motivo": "arquivo nao encontrado: %s" % faltando}
        A, B = carrega(par[0]), carrega(par[1])
        rot = {"entre": list(par)}
    else:
        outro_p = r.get("com")
        if not outro_p or not os.path.isfile(outro_p):
            return None, {"motivo": "requisito exige 'entre': [a, b] ou 'com': b"}
        A, B = m, carrega(outro_p)
        rot = {"com": outro_p}
    if not (A.is_watertight and B.is_watertight):
        return None, dict(rot, motivo="interseccao exige as duas malhas fechadas")
    inter = _confere_status(_manifold(A, "componente A") ^ _manifold(B, "componente B"),
                            "interseccao dos componentes")
    v = float(inter.volume())
    tol = float(r.get("tol_mm3", 0.0))
    return v <= tol, dict(rot, volume_de_interferencia_mm3=round(v, 6), tol_mm3=tol,
                          volume_a_mm3=round(float(A.volume), 3),
                          volume_b_mm3=round(float(B.volume), 3))


VERIFICADORES = {
    "caixa": v_caixa, "volume": v_volume, "n_solidos": v_n_solidos, "furo": v_furo,
    "n_furos_no_plano": v_n_furos_no_plano, "distancia_entre_furos": v_distancia_entre_furos,
    "regiao_intacta": v_regiao_intacta, "interferencia": v_interferencia,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--malha", required=True)
    ap.add_argument("--requisitos", required=True)
    ap.add_argument("--referencia")
    ap.add_argument("--json")
    a = ap.parse_args()

    m = carrega(a.malha)
    ctx = {"referencia": carrega(a.referencia) if a.referencia else None}
    spec = json.load(open(a.requisitos, encoding="utf-8"))
    reqs = spec.get("requisitos") or []

    # CORRIGIDO 07/09/2026 depois da quarta revisao externa. O mapa de estados era um
    # dicionario indexado por id, sem exigir unicidade: dois requisitos do mesmo tipo com o
    # MESMO id, o primeiro reprovado e o segundo aprovado, deixavam so o segundo no mapa, e
    # a obrigacao daquele tipo aprovava apesar de existir uma reprovacao. Id repetido passa
    # a ser erro de especificacao, e o mapa deixa de ser a unica evidencia.
    vistos = {}
    for r in reqs:
        rid = r.get("id") or r.get("tipo")
        vistos[rid] = vistos.get(rid, 0) + 1
    ids_repetidos = sorted(k for k, n in vistos.items() if n > 1)

    linhas = []
    for r in reqs:
        tipo = r.get("tipo")
        rid = r.get("id") or tipo
        base = {"id": rid, "tipo": tipo, "descricao": r.get("descricao")}
        if rid in ids_repetidos:
            linhas.append(dict(base, estado=ESPEC_INVALIDA, passou=False, verificado=False,
                               erro_de_especificacao=["id %r aparece %d vezes" % (rid, vistos[rid])],
                               motivo="id repetido: cada requisito precisa de id unico, "
                                      "senao a evidencia de um sobrescreve a do outro"))
            continue
        problemas_de_esquema = valida_esquema(r)
        if problemas_de_esquema:
            linhas.append(dict(base, estado=ESPEC_INVALIDA, passou=False, verificado=False,
                               erro_de_especificacao=problemas_de_esquema,
                               motivo="requisito malformado: %s" % "; ".join(problemas_de_esquema),
                               nota="requisito malformado REPROVA. Aprovar o que der para "
                                    "medir e ignorar o resto seria aprovacao parcial "
                                    "disfarcada."))
            continue
        if tipo in NAO_IMPLEMENTADOS:
            linhas.append(dict(base, estado=NAO_IMPLEMENTADA, passou=None, verificado=False,
                               motivo=NAO_IMPLEMENTADOS[tipo],
                               declarado={k: v for k, v in r.items()
                                          if k not in ("id", "tipo", "descricao")}))
            continue
        fn = VERIFICADORES.get(tipo)
        if fn is None:
            linhas.append(dict(base, estado=NAO_IMPLEMENTADA, passou=None, verificado=False,
                               motivo="tipo de requisito desconhecido"))
            continue
        # CORRIGIDO 07/09/2026 depois da terceira revisao externa. Antes, QUALQUER excecao
        # virava "nao verificado", indistinguivel de tipo sem medidor, e o chamador podia
        # tratar isso como ausencia benigna. Agora falha operacional tem estado proprio.
        try:
            ok, det = fn(m, r, ctx)
        except (ErroDeKernel, SecaoInvalida) as e:
            linhas.append(dict(base, estado=ERRO, passou=False, verificado=False,
                               motivo="falha na medicao: %s: %s" % (type(e).__name__, e),
                               nota="ERRO nao e ausencia benigna: nada foi medido, e o "
                                    "requisito NAO pode ser considerado atendido."))
            continue
        except Exception as e:
            linhas.append(dict(base, estado=ERRO, passou=False, verificado=False,
                               motivo="erro na verificacao: %s: %s" % (type(e).__name__, e),
                               nota="ERRO nao e ausencia benigna: nada foi medido."))
            continue
        if ok is None:
            linhas.append(dict(base, estado=INDETERMINADA, passou=None, verificado=False,
                               detalhe=det,
                               motivo=(det or {}).get("motivo", "insumo declarado ausente")))
            continue
        linhas.append(dict(base, estado=(APROVADA if ok else REPROVADA),
                           passou=bool(ok), verificado=True, detalhe=det))

    for l in linhas:
        if l["estado"] not in ESTADOS:
            l["estado"] = ERRO
            l["passou"] = False
            l["motivo"] = "estado fora do contrato: corrigido para ERRO"

    por_estado = {e: [l for l in linhas if l["estado"] == e] for e in ESTADOS}
    aprov = por_estado[APROVADA]
    repro = por_estado[REPROVADA] + por_estado[ESPEC_INVALIDA] + por_estado[ERRO]
    nverif = por_estado[NAO_IMPLEMENTADA] + por_estado[INDETERMINADA]

    out = {
        "malha": a.malha,
        "referencia": a.referencia,
        "arquivo_de_requisitos": a.requisitos,
        "n_requisitos": len(linhas),
        "n_aprovados": len(aprov),
        "n_reprovados": len(repro),
        "n_nao_verificados": len(nverif),
        "por_estado": {e: [l["id"] for l in por_estado[e]] for e in ESTADOS},
        "tipos_por_estado": {e: sorted({l["tipo"] for l in por_estado[e]}) for e in ESTADOS},
        # lista, e nao dicionario por id: dicionario perde evidencia em caso de colisao
        "estados_dos_requisitos": [{"id": l["id"], "tipo": l["tipo"], "estado": l["estado"]}
                                   for l in linhas],
        "estados_por_requisito": {l["id"]: {"tipo": l["tipo"], "estado": l["estado"]}
                                  for l in linhas},
        "ids_repetidos": ids_repetidos,
        "houve_erro_operacional": bool(por_estado[ERRO]),
        "atende_ao_pedido": bool(reqs) and not repro and not nverif,
        "requisitos": linhas,
        "reprovados": [{"id": l["id"], "tipo": l["tipo"], "estado": l["estado"],
                        "motivo": l.get("motivo"), "detalhe": l.get("detalhe")}
                       for l in repro],
        "nao_verificados": [{"id": l["id"], "tipo": l["tipo"], "estado": l["estado"],
                             "motivo": l.get("motivo")} for l in nverif],
        "veredito": (
            "Nenhum requisito declarado: nada foi verificado quanto a intencao." if not reqs else
            "Todos os %d requisitos declarados foram verificados e aprovados." % len(aprov)
            if not repro and not nverif else
            "%d aprovados, %d REPROVADOS, %d nao verificados. Requisito nao verificado nao e "
            "requisito atendido: quem confere e uma pessoa, e a entrega tem que dizer isso."
            % (len(aprov), len(repro), len(nverif))),
        "aviso": ("Isto verifica a intencao DECLARADA. Requisito que ninguem escreveu nao e "
                  "verificado por ninguem. A qualidade desta checagem e a qualidade da lista "
                  "de requisitos."),
    }
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0 if out["atende_ao_pedido"] else 1


if __name__ == "__main__":
    sys.exit(main())
