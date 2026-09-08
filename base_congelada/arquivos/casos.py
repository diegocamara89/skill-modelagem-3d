"""casos.py - os seis casos de teste da generalidade. Implementa a secao 8 do DESENHO.md.

Toda geometria e SINTETICA e gerada aqui. Nenhuma referencia a projeto real.

O que estes casos testam nao e geometria: e o ROTEAMENTO. Os casos 4 e 6 sao os que
reprovariam a versao 1 do desenho, porque nela toda peca passava pelo processo de
impressao. Se eles passarem exigindo so intencao e geometria nao vazia, a separacao das
tres decisoes esta funcionando.

Cada caso declara o que ESPERA. Um caso que nao pode reprovar nao testa nada.
"""
import hashlib, json, os, sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SAIDA = os.path.join(AQUI, "casos_saida")


def _prep():
    os.makedirs(SAIDA, exist_ok=True)
    return SAIDA


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _req(caminho, spec):
    json.dump(spec, open(caminho, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return caminho


# ---------------------------------------------------------------- caso 1

def caso1():
    """criar / solido / impressao_fdm - o caminho completo funciona."""
    from build123d import Align, Box, Cylinder, Pos, export_step, export_stl
    d = _prep()
    L, P, T, D_centro, D_fix, VAO = 70.0, 40.0, 8.0, 12.0, 4.5, 50.0
    corpo = Box(L, P, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    furos = [Cylinder(D_centro / 2, T * 3)]
    furos += [Pos(x, 0, 0) * Cylinder(D_fix / 2, T * 3) for x in (-VAO / 2, VAO / 2)]
    peca = corpo - furos

    stl = os.path.join(d, "c1_espacador.stl")
    step = os.path.join(d, "c1_espacador.step")
    export_stl(peca, stl, tolerance=0.01, angular_tolerance=0.1)
    export_step(peca, step)

    req = _req(os.path.join(d, "c1_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [L, P, T], "tol_mm": 0.05},
            {"id": "corpo_unico", "tipo": "n_solidos", "valor": 1},
            {"id": "tres_furos", "tipo": "n_furos_no_plano", "eixo": "Z", "plano": T / 2, "valor": 3},
            {"id": "furo_central", "tipo": "furo", "eixo": "Z", "plano": T / 2,
             "posicao": [0.0, 0.0], "diametro": D_centro, "tol_mm": 0.2, "tol_pos_mm": 0.1},
            {"id": "vao_de_fixacao", "tipo": "distancia_entre_furos", "eixo": "Z", "plano": T / 2,
             "entre": [[-VAO / 2, 0.0], [VAO / 2, 0.0]], "valor": VAO, "tol_mm": 0.1},
        ]})
    return {
        "id": "1_dimensional_do_zero",
        "titulo": "peca dimensional criada do zero, para impressao",
        "classificacao": {"modalidade": "criar", "representacao": "solido",
                          "finalidade": "impressao_fdm"},
        "malha": stl, "step": step, "requisitos": req, "referencia": None,
        "geometria_nao_vazia": {"ok": len(peca.solids()) == 1 and float(peca.volume) > 0,
                                "n_solidos": len(peca.solids()),
                                "volume_mm3": round(float(peca.volume), 3)},
        "declaracoes": {"orientacao_de_impressao": "face de %g x %g mm na mesa" % (L, P),
                        "direcao_da_carga": "compressao ao longo de Z, atravessando as camadas",
                        "encaixe_declarado": False},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "malha_estanque", "zero_nao_manifold",
                      "portao_do_fatiador", "envelope_e_particao", "orientacao_anisotropia"],
            "nao_exige": ["regiao_preservada", "varredura_de_familia", "interferencia"],
            "nao_aplicaveis": ["folga_calibrada"],
            "resultado": "aprovado",
        },
    }


# ---------------------------------------------------------------- caso 2

def caso2():
    """editar / solido / intercambio - regiao preservada continua identica."""
    from build123d import Align, Box, Cylinder, Pos, export_step, export_stl
    d = _prep()
    L, P, T, D_centro, D_fix, VAO = 70.0, 40.0, 8.0, 12.0, 4.5, 50.0
    D_NOVO = 6.0                                   # a edicao: um furo de fixacao cresce

    def monta(d_esq):
        corpo = Box(L, P, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        f = [Cylinder(D_centro / 2, T * 3),
             Pos(-VAO / 2, 0, 0) * Cylinder(d_esq / 2, T * 3),
             Pos(VAO / 2, 0, 0) * Cylinder(D_fix / 2, T * 3)]
        return corpo - f

    entrada = os.path.join(d, "c2_entrada.stl")
    export_stl(monta(D_fix), entrada, tolerance=0.01, angular_tolerance=0.1)
    h_antes = sha(entrada)

    editada = monta(D_NOVO)
    stl = os.path.join(d, "c2_editada.stl")
    step = os.path.join(d, "c2_editada.step")
    export_stl(editada, stl, tolerance=0.01, angular_tolerance=0.1)
    export_step(editada, step)
    h_depois = sha(entrada)

    req = _req(os.path.join(d, "c2_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [L, P, T], "tol_mm": 0.05},
            {"id": "corpo_unico", "tipo": "n_solidos", "valor": 1},
            {"id": "regiao_do_furo_central_intacta", "tipo": "regiao_intacta",
             "descricao": "o furo central e a area em volta dele nao podem ter mudado",
             "caixa_min": [-14.0, -14.0, -1.0], "caixa_max": [14.0, 14.0, T + 1.0],
             "tol_fracao": 1e-9},
            {"id": "furo_direito_intacto", "tipo": "regiao_intacta",
             "descricao": "o furo de fixacao que NAO foi editado tem que estar igual",
             "caixa_min": [VAO / 2 - 6, -6.0, -1.0], "caixa_max": [VAO / 2 + 6, 6.0, T + 1.0],
             "tol_fracao": 1e-9},
        ]})

    # extra do caso: a regiao EDITADA tem que divergir. Se nao divergir, a edicao nao
    # aconteceu e o verificador esta cego.
    req_controle = _req(os.path.join(d, "c2_req_controle.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "regiao_editada_DEVE_divergir", "tipo": "regiao_intacta",
             "caixa_min": [-VAO / 2 - 6, -6.0, -1.0], "caixa_max": [-VAO / 2 + 6, 6.0, T + 1.0],
             "tol_fracao": 1e-9}]})

    return {
        "id": "2_edicao_localizada",
        "titulo": "edicao localizada preservando o resto, para intercambio",
        "classificacao": {"modalidade": "editar", "representacao": "solido",
                          "finalidade": "intercambio"},
        "malha": stl, "step": step, "requisitos": req, "referencia": entrada,
        "requisitos_de_controle": req_controle,
        "controle_espera": "reprovado",
        "geometria_nao_vazia": {"ok": len(editada.solids()) == 1 and float(editada.volume) > 0,
                                "n_solidos": len(editada.solids()),
                                "volume_mm3": round(float(editada.volume), 3)},
        "entrada_intacta": {"arquivo": entrada, "sha_antes": h_antes, "sha_depois": h_depois,
                            "ok": h_antes == h_depois},
        "declaracoes": {"edicao": "furo de fixacao esquerdo de %g para %g mm" % (D_fix, D_NOVO),
                        "encaixe_declarado": False,
                        "componentes_esperados_no_step": 1},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "regiao_preservada", "entrada_intacta",
                      "reabre_em_cad"],
            "nao_exige": ["malha_estanque", "zero_nao_manifold", "portao_do_fatiador",
                          "envelope_e_particao", "orientacao_anisotropia"],
            "resultado": "aprovado",
        },
    }


# ---------------------------------------------------------------- caso 3

def caso3():
    """criar / montagem / montagem - dois corpos e resultado legitimo, nao defeito."""
    from build123d import Align, Cylinder, Pos, export_step, export_stl
    import trimesh
    d = _prep()
    D_PINO, H_PINO, D_SOQ, ESP = 10.0, 20.0, 18.0, 4.0
    pino = Cylinder(D_PINO / 2, H_PINO, align=(Align.CENTER, Align.CENTER, Align.MIN))
    soquete = (Cylinder(D_SOQ / 2, H_PINO, align=(Align.CENTER, Align.CENTER, Align.MIN))
               - Cylinder(D_PINO / 2 + 0.25, H_PINO, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    soquete = Pos(40, 0, 0) * soquete           # lado a lado, sem interferencia

    p_stl = os.path.join(d, "c3_pino.stl")
    s_stl = os.path.join(d, "c3_soquete.stl")
    export_stl(pino, p_stl, tolerance=0.01, angular_tolerance=0.1)
    export_stl(soquete, s_stl, tolerance=0.01, angular_tolerance=0.1)
    # CORRIGIDO 07/09/2026 depois da segunda revisao externa. O caso entregava o STEP de UM
    # componente como intercambio da montagem, e a verificacao aprovava por achar "algum
    # solido". Agora o intercambio da montagem carrega os DOIS componentes, e o caso declara
    # quantos espera encontrar ao reabrir.
    from build123d import Compound
    montagem_cad = Compound(children=[pino, soquete])
    step_montagem = os.path.join(d, "c3_montagem.step")
    export_step(montagem_cad, step_montagem)

    junto = trimesh.util.concatenate([trimesh.load(p_stl, force="mesh", process=False),
                                      trimesh.load(s_stl, force="mesh", process=False)])
    # Soldar antes de contar corpos. Sem isso o split conta grupos de facetas soltas e
    # devolve numero absurdo: MEDIDO 1508 corpos numa montagem de duas pecas.
    junto.merge_vertices()
    stl = os.path.join(d, "c3_montagem.stl")
    junto.export(stl)

    req = _req(os.path.join(d, "c3_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "dois_corpos", "tipo": "n_solidos",
             "descricao": "montagem de duas pecas: dois corpos e o esperado, nao um defeito",
             "valor": 2},
            {"id": "sem_interferencia", "tipo": "interferencia",
             "descricao": "pino e soquete nao podem ocupar o mesmo espaco",
             "entre": [p_stl, s_stl], "tol_mm3": 1e-6},
        ]})
    return {
        "id": "3_montagem_dois_corpos",
        "titulo": "montagem com dois corpos legitimos",
        "classificacao": {"modalidade": "criar", "representacao": "montagem",
                          "finalidade": "montagem"},
        "malha": stl, "step": step_montagem,
        "requisitos": req, "referencia": p_stl,
        "geometria_nao_vazia": {"ok": len(junto.split(only_watertight=False)) == 2,
                                "n_solidos": len(junto.split(only_watertight=False)),
                                "volume_mm3": round(float(junto.volume), 3)
                                if junto.is_watertight else None},
        "declaracoes": {"encaixe_declarado": True,
                        "tipo_de_ajuste": "deslizante",
                        "material": "PLA sintetico de teste",
                        "maquina": "maquina de teste",
                        "folga_desenhada_mm": 0.25,
                        "componentes_esperados_no_step": 2},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "n_corpos_esperado", "interferencia",
                      "folga_calibrada", "reabre_em_cad"],
            "nao_exige": ["malha_estanque", "portao_do_fatiador", "orientacao_anisotropia"],
            # BARRADO de proposito: ha encaixe declarado e nao ha folga medida em cupom.
            "resultado": "barrado_na_folga",
        },
    }


# ---------------------------------------------------------------- caso 4

def caso4():
    """criar / superficie / visualizacao - o caso que reprovaria a versao 1."""
    from build123d import Cylinder, GeomType, export_stl
    import trimesh
    d = _prep()
    R, H = 25.0, 60.0
    face = Cylinder(R, H).faces().filter_by(GeomType.CYLINDER)[0]
    stl = os.path.join(d, "c4_casca.stl")
    export_stl(face, stl, tolerance=0.02, angular_tolerance=0.15)
    m = trimesh.load(stl, force="mesh", process=False)
    m.merge_vertices()

    req = _req(os.path.join(d, "c4_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [2 * R, 2 * R, H], "tol_mm": 0.5,
             "descricao": "a casca tem que ocupar o espaco previsto na cena"},
        ]})
    return {
        "id": "4_superficie_para_render",
        "titulo": "superficie aberta destinada a visualizacao",
        "classificacao": {"modalidade": "criar", "representacao": "superficie",
                          "finalidade": "visualizacao"},
        "malha": stl, "step": None, "requisitos": req, "referencia": None,
        "geometria_nao_vazia": {"ok": len(m.faces) > 0, "n_facetas": int(len(m.faces)),
                                "area_mm2": round(float(m.area), 2)},
        "declaracoes": {"encaixe_declarado": False,
                        "nota": "superficie sem espessura: nao e peca, e casca de cena"},
        "fatos_da_malha": {"fechada_watertight": bool(m.is_watertight),
                           "arestas_abertas": int(np.count_nonzero(
                               np.unique(np.sort(m.edges_sorted, axis=1), axis=0,
                                         return_counts=True)[1] == 1))},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia"],
            "nao_exige": ["malha_estanque", "zero_nao_manifold", "portao_do_fatiador",
                          "envelope_e_particao", "folga_calibrada", "orientacao_anisotropia"],
            "resultado": "aprovado",
            "extra": "a malha NAO e fechada e o caso tem que passar mesmo assim",
        },
    }


# ---------------------------------------------------------------- caso 5

def caso5():
    """reconstruir / solido / impressao_fdm - cota rotulada e datum inclinado preservado."""
    from build123d import Align, Box, Cylinder, Pos, Rot, export_step, export_stl
    import find_datums
    d = _prep()

    # --- referencia sintetica, com um assento INCLINADO de proposito ---
    ANG = 17.0
    ref = (Box(50, 30, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
           - (Pos(0, 0, 20) * Rot(0, ANG, 0)
              * Box(80, 60, 20, align=(Align.CENTER, Align.CENTER, Align.MIN)))
           - Cylinder(4, 60))
    refstl = os.path.join(d, "c5_referencia.stl")
    export_stl(ref, refstl, tolerance=0.01, angular_tolerance=0.1)
    h_antes = sha(refstl)

    # --- medicao da referencia, por script, com rotulo de origem em cada cota ---
    lido = find_datums.com_fonte(refstl, top=6, tol_ang=1.5, tol_plano=0.05, area_min=5.0)
    # CORRIGIDO 07/09/2026 depois da segunda revisao externa. O diametro era a constante do
    # gerador e recebia o rotulo MEDIDO com fonte "secao da referencia", sem haver medicao
    # nenhuma. Rotulo inventado passava pela verificacao de proveniencia, que so confere
    # existencia de rotulo. Agora o diametro sai de uma medicao real da secao.
    import secoes as _sec
    import trimesh as _tm
    _ref_m = _tm.load(refstl, force="mesh", process=False)
    _ref_m.merge_vertices()
    _sec_ref = _sec.secao(_ref_m, 2, 2.0)
    _furos = [_sec.descreve(q) for q in _sec_ref["furos"]]
    d_medido = max((f["diametro_equivalente_mm"] for f in _furos), default=None)
    incl = lido["maior_regiao_inclinada"]
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa. Reduzir a normal a um angulo
    # com Z+ descarta o SENTIDO da inclinacao e o azimute: uma reconstrucao com a inclinacao
    # invertida conservava o mesmo angulo, a mesma caixa e o mesmo numero de corpos, e o
    # erro dava zero. Agora a normal ORIENTADA e guardada e comparada.
    n_ref = None if incl is None else np.array(incl["normal"], float)
    ang_medido = None if incl is None else 90.0 - incl["angulos_por_eixo_deg"]["Z+"] \
        if incl["angulos_por_eixo_deg"]["Z+"] > 45 else incl["angulos_por_eixo_deg"]["Z+"]
    caixa = lido["malha"]["caixa_mm"]

    medidas = {
        "comprimento": {"valor": round(caixa[0], 3), "origem": "MEDIDO",
                        "fonte": "caixa da malha de referencia"},
        "largura": {"valor": round(caixa[1], 3), "origem": "MEDIDO",
                    "fonte": "caixa da malha de referencia"},
        "altura_maxima": {"valor": round(caixa[2], 3), "origem": "MEDIDO",
                          "fonte": "caixa da malha de referencia"},
        "angulo_do_assento": {"valor": round(ang_medido, 3), "origem": "MEDIDO",
                              "fonte": "maior regiao plana nao alinhada a eixo, por find_datums"},
        "altura_da_parede_traseira": {"valor": round(caixa[2] * 0.6, 3), "origem": "ESTIMADO",
                                      "nota": "lida por proporcao, sem cota direta; incerta"},
        "diametro_do_furo": {"valor": (round(d_medido, 3) if d_medido else None),
                             "origem": ("MEDIDO" if d_medido else "AUSENTE"),
                             "fonte": ("diametro equivalente do furo na secao Z=2 da "
                                       "referencia, medido por secoes.py"
                                       if d_medido else
                                       "nenhum furo encontrado na secao: cota nao obtida"),
                             "n_furos_na_secao": len(_furos)},
        "espessura_de_parede": {"valor": 3.0, "origem": "ESCOLHA",
                                "nota": "decisao de projeto, nao medida na referencia"},
        "raio_de_alivio": {"valor": 1.5, "origem": "DERIVADO",
                           "fonte": "metade da espessura de parede escolhida"},
    }
    json.dump(medidas, open(os.path.join(d, "c5_medidas.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    # --- reconstrucao usando o angulo MEDIDO, nao um eixo ---
    novo = (Box(medidas["comprimento"]["valor"], medidas["largura"]["valor"],
                medidas["altura_maxima"]["valor"], align=(Align.CENTER, Align.CENTER, Align.MIN))
            - (Pos(0, 0, medidas["altura_maxima"]["valor"])
               * Rot(0, medidas["angulo_do_assento"]["valor"], 0)
               * Box(120, 90, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
            - Cylinder(medidas["diametro_do_furo"]["valor"] / 2, 90))
    stl = os.path.join(d, "c5_reconstruida.stl")
    step = os.path.join(d, "c5_reconstruida.step")
    export_stl(novo, stl, tolerance=0.01, angular_tolerance=0.1)
    export_step(novo, step)
    h_depois = sha(refstl)

    # --- o assento reconstruido tem que ter o MESMO angulo da referencia ---
    novo_lido = find_datums.com_fonte(stl, top=6, tol_ang=1.5, tol_plano=0.05, area_min=5.0)
    ni = novo_lido["maior_regiao_inclinada"]
    n_novo = None if ni is None else np.array(ni["normal"], float)
    ang_novo = None if ni is None else (90.0 - ni["angulos_por_eixo_deg"]["Z+"]
                                        if ni["angulos_por_eixo_deg"]["Z+"] > 45
                                        else ni["angulos_por_eixo_deg"]["Z+"])

    def _ang_entre(u, v):
        if u is None or v is None:
            return None
        c = float(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1))
        return float(np.degrees(np.arccos(c)))

    sem_rotulo = [k for k, v in medidas.items() if not v.get("origem")]
    ausentes_de_valor = [k for k, v in medidas.items() if v.get("valor") is None]
    # CORRIGIDO 07/09/2026: o desenho dizia oito cotas usadas, e a reconstrucao usa cinco.
    # Cota registrada e nao usada e ruido no rastro de proveniencia, e agora e identificada.
    USADAS = ("comprimento", "largura", "altura_maxima", "angulo_do_assento",
              "diametro_do_furo")
    registradas_e_nao_usadas = [k for k in medidas if k not in USADAS]
    req = _req(os.path.join(d, "c5_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa",
             "valor": [medidas["comprimento"]["valor"], medidas["largura"]["valor"],
                       medidas["altura_maxima"]["valor"]], "tol_mm": 0.05},
            {"id": "corpo_unico", "tipo": "n_solidos", "valor": 1},
        ]})
    return {
        "id": "5_reconstrucao_incompleta",
        "titulo": "reconstrucao com informacao incompleta, cota rotulada",
        "classificacao": {"modalidade": "reconstruir", "representacao": "solido",
                          "finalidade": "impressao_fdm"},
        "malha": stl, "step": step, "requisitos": req, "referencia": refstl,
        "geometria_nao_vazia": {"ok": len(novo.solids()) == 1 and float(novo.volume) > 0,
                                "n_solidos": len(novo.solids()),
                                "volume_mm3": round(float(novo.volume), 3)},
        "entrada_intacta": {"arquivo": refstl, "sha_antes": h_antes, "sha_depois": h_depois,
                            "ok": h_antes == h_depois},
        "proveniencia": {
            "n_cotas": len(medidas),
            "sem_rotulo": sem_rotulo,
            "por_origem": {o: sorted(k for k, v in medidas.items() if v.get("origem") == o)
                           for o in ("MEDIDO", "DERIVADO", "ESTIMADO", "ESCOLHA")},
            "cotas_usadas_na_construcao": list(USADAS),
            "registradas_e_nao_usadas": registradas_e_nao_usadas,
            "cotas_sem_valor": ausentes_de_valor,
            "diametro_medido_mm": d_medido,
            "ok": (not sem_rotulo and not ausentes_de_valor
                   and any(v.get("origem") == "ESTIMADO" for v in medidas.values())),
        },
        "datum": {
            "criterio": ("angulo entre as NORMAIS ORIENTADAS da maior regiao inclinada da "
                         "referencia e da reconstruida. Comparar apenas o angulo com Z+ "
                         "aceitaria inclinacao invertida e azimute girado."),
            "normal_na_referencia": (None if n_ref is None else
                                     [round(float(x), 6) for x in n_ref]),
            "normal_na_reconstruida": (None if n_novo is None else
                                       [round(float(x), 6) for x in n_novo]),
            "angulo_entre_normais_deg": (None if _ang_entre(n_ref, n_novo) is None
                                         else round(_ang_entre(n_ref, n_novo), 4)),
            "angulo_na_referencia_deg": round(ang_medido, 3) if ang_medido else None,
            "angulo_na_reconstruida_deg": round(ang_novo, 3) if ang_novo else None,
            "erro_deg": (None if _ang_entre(n_ref, n_novo) is None
                         else round(_ang_entre(n_ref, n_novo), 4)),
            "tol_deg": 0.5,
            "angulo_verdadeiro_da_referencia_deg": ANG,
            "nota_de_independencia": ("o angulo verdadeiro do gerador fica registrado de "
                                      "proposito: se as duas leituras concordarem entre si "
                                      "e discordarem dele, o erro e do extrator, nao da "
                                      "reconstrucao.")},
        "declaracoes": {"orientacao_de_impressao": "base plana na mesa",
                        "direcao_da_carga": "compressao vertical",
                        "encaixe_declarado": False,
                        "componentes_esperados_no_step": 1},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "proveniencia_de_cota",
                      "entrada_intacta", "malha_estanque", "portao_do_fatiador",
                      "orientacao_anisotropia"],
            "nao_exige": ["regiao_preservada", "interferencia"],
            "nao_aplicaveis": ["folga_calibrada"],
            "resultado": "aprovado",
        },
    }


# ---------------------------------------------------------------- caso 6

def caso6():
    """criar / solido / visualizacao - projeto simples que termina rapido e sem fatiador."""
    from build123d import Align, Axis, Box, GeomType, chamfer, export_stl
    d = _prep()
    peca = Box(80, 50, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    topo = [e for e in peca.edges().filter_by(GeomType.LINE)
            if abs(e.center().Z - 6.0) < 1e-6]
    if topo:
        peca = chamfer(topo, length=1.0)
    stl = os.path.join(d, "c6_placa.stl")
    export_stl(peca, stl, tolerance=0.02, angular_tolerance=0.2)

    req = _req(os.path.join(d, "c6_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [80.0, 50.0, 6.0], "tol_mm": 0.05},
            {"id": "corpo_unico", "tipo": "n_solidos", "valor": 1},
        ]})
    return {
        "id": "6_simples_e_rapido",
        "titulo": "projeto simples para visualizacao, sem fatiador e sem pergunta a mais",
        "classificacao": {"modalidade": "criar", "representacao": "solido",
                          "finalidade": "visualizacao"},
        "malha": stl, "step": None, "requisitos": req, "referencia": None,
        "geometria_nao_vazia": {"ok": len(peca.solids()) == 1 and float(peca.volume) > 0,
                                "n_solidos": len(peca.solids()),
                                "volume_mm3": round(float(peca.volume), 3)},
        "declaracoes": {"encaixe_declarado": False},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia"],
            "nao_exige": ["malha_estanque", "zero_nao_manifold", "portao_do_fatiador",
                          "envelope_e_particao", "folga_calibrada", "orientacao_anisotropia",
                          "reabre_em_cad"],
            "resultado": "aprovado",
            "limite_de_tempo_s": 20.0,
        },
    }



# ---------------------------------------------------------------- caso 7

def familia_placa(L=80.0, P=50.0, T=6.0, d=5.0):
    """Familia parametrica sintetica, um solido. Usada pelo caso 7 e pela varredura."""
    from build123d import Align, Box, Cylinder, Pos
    corpo = Box(L, P, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    furos = [Pos(x, 0, 0) * Cylinder(d / 2, T * 3) for x in (-L / 4, L / 4)]
    return corpo - furos


def caso7():
    """parametrizar / solido / impressao_fdm - exercita a VARREDURA pelo runner real.

    Existe porque a terceira revisao externa apontou que a modalidade parametrizar estava
    quebrada na comunicacao com o executor, e nenhum dos seis casos a exercitava: a
    ferramenta montava o JSON e nunca o imprimia, entao toda varredura devolvia "sem JSON
    na saida" e ninguem notava.
    """
    from build123d import export_step, export_stl
    d = _prep()
    peca = familia_placa()
    stl = os.path.join(d, "c7_placa.stl")
    step = os.path.join(d, "c7_placa.step")
    export_stl(peca, stl, tolerance=0.01, angular_tolerance=0.1)
    export_step(peca, step)
    req = _req(os.path.join(d, "c7_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [80.0, 50.0, 6.0], "tol_mm": 0.05},
            {"id": "corpo_unico", "tipo": "n_solidos", "valor": 1},
        ]})
    return {
        "id": "7_familia_parametrica",
        "titulo": "familia parametrica varrida pelo executor real",
        "classificacao": {"modalidade": "parametrizar", "representacao": "solido",
                          "finalidade": "impressao_fdm"},
        "malha": stl, "step": step, "requisitos": req, "referencia": None,
        "familia": {"modulo": "casos", "funcao": "familia_placa",
                    "grade": "L=70,80,90;d=4,5"},
        "geometria_nao_vazia": {"ok": len(peca.solids()) == 1 and float(peca.volume) > 0,
                                "n_solidos": len(peca.solids())},
        "declaracoes": {"orientacao_de_impressao": "face maior na mesa",
                        "direcao_da_carga": "flexao no plano da placa",
                        "encaixe_declarado": False,
                        "componentes_esperados_no_step": 1},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "varredura_de_familia",
                      "malha_estanque", "portao_do_fatiador", "envelope_e_particao"],
            "nao_exige": ["regiao_preservada", "interferencia"],
            "nao_aplicaveis": ["folga_calibrada"],
            "resultado": "aprovado",
        },
    }


# ---------------------------------------------------------------- caso 8

def caso8():
    """criar / superficie / intercambio - superficie REABERTA em intercambio.

    Existe porque a terceira revisao externa apontou que superficie mais intercambio e uma
    classificacao legitima que o codigo nao suportava: a verificacao de intercambio exigia
    solido, e um STEP de casca correto tem zero solidos, entao reprovava. Trocar para
    esperar zero solidos tambem nao serve: contar zero nao prova que a casca existe.
    """
    from build123d import Cylinder, GeomType, export_step, export_stl
    import trimesh
    d = _prep()
    R, H = 20.0, 40.0
    face = Cylinder(R, H).faces().filter_by(GeomType.CYLINDER)[0]
    stl = os.path.join(d, "c8_casca.stl")
    step = os.path.join(d, "c8_casca.step")
    export_stl(face, stl, tolerance=0.02, angular_tolerance=0.15)
    export_step(face, step)
    m = trimesh.load(stl, force="mesh", process=False)
    m.merge_vertices()
    req = _req(os.path.join(d, "c8_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [2 * R, 2 * R, H], "tol_mm": 0.5},
        ]})
    return {
        "id": "8_superficie_em_intercambio",
        "titulo": "superficie aberta entregue como intercambio analitico",
        "classificacao": {"modalidade": "criar", "representacao": "superficie",
                          "finalidade": "intercambio"},
        "malha": stl, "step": step, "requisitos": req, "referencia": None,
        "geometria_nao_vazia": {"ok": len(m.faces) > 0, "n_facetas": int(len(m.faces)),
                                "area_mm2": round(float(m.area), 2)},
        "declaracoes": {"encaixe_declarado": False, "faces_esperadas_no_step": 1},
        "fatos_da_malha": {"fechada_watertight": bool(m.is_watertight)},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "reabre_em_cad"],
            "nao_exige": ["malha_estanque", "zero_nao_manifold", "portao_do_fatiador",
                          "envelope_e_particao", "folga_calibrada"],
            "resultado": "aprovado",
            "extra": "o intercambio tem faces e zero solidos, e isso e o contrato correto",
        },
    }


# ---------------------------------------------------------------- caso 9

def familia_montagem(folga=0.25, d_pino=10.0, h=20.0):
    """Familia parametrica de MONTAGEM: pino mais soquete, dois corpos legitimos."""
    from build123d import Align, Compound, Cylinder, Pos
    pino = Cylinder(d_pino / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    soq = (Cylinder(d_pino / 2 + 4.0, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
           - Cylinder(d_pino / 2 + folga, h, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return Compound(children=[pino, Pos(40, 0, 0) * soq])


def caso9():
    """parametrizar / montagem / montagem - varredura de familia com DOIS corpos.

    Existe porque a varredura exigia exatamente um solido em qualquer caso, o que reprova
    montagem parametrica legitima.
    """
    from build123d import export_step, export_stl
    import trimesh
    d = _prep()
    mont = familia_montagem()
    step = os.path.join(d, "c9_montagem.step")
    export_step(mont, step)
    p_stl = os.path.join(d, "c9_pino.stl")
    s_stl = os.path.join(d, "c9_soquete.stl")
    export_stl(mont.solids()[0], p_stl, tolerance=0.01, angular_tolerance=0.1)
    export_stl(mont.solids()[1], s_stl, tolerance=0.01, angular_tolerance=0.1)
    junto = trimesh.util.concatenate([trimesh.load(p_stl, force="mesh", process=False),
                                      trimesh.load(s_stl, force="mesh", process=False)])
    junto.merge_vertices()
    stl = os.path.join(d, "c9_montagem.stl")
    junto.export(stl)
    req = _req(os.path.join(d, "c9_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "dois_corpos", "tipo": "n_solidos", "valor": 2},
            {"id": "sem_interferencia", "tipo": "interferencia",
             "entre": [p_stl, s_stl], "tol_mm3": 1e-6},
        ]})
    return {
        "id": "9_montagem_parametrica",
        "titulo": "familia parametrica de montagem com dois corpos",
        "classificacao": {"modalidade": "parametrizar", "representacao": "montagem",
                          "finalidade": "montagem"},
        "malha": stl, "step": step, "requisitos": req, "referencia": p_stl,
        "familia": {"modulo": "casos", "funcao": "familia_montagem",
                    "grade": "folga=0.2,0.3", "representacao": "montagem", "n_solidos": 2},
        "geometria_nao_vazia": {"ok": len(junto.split(only_watertight=False)) == 2,
                                "n_solidos": len(junto.split(only_watertight=False))},
        # A familia varia justamente a FOLGA do encaixe, logo ha encaixe declarado, e sem
        # cupom medido este caso tem que ser BARRADO na folga. Declarar folga_calibrada
        # como nao aplicavel aqui seria fugir do proprio mecanismo de honestidade.
        "declaracoes": {"encaixe_declarado": True,
                        "tipo_de_ajuste": "deslizante",
                        "material": "PLA sintetico de teste",
                        "maquina": "maquina de teste",
                        "folga_desenhada_mm": 0.25,
                        "componentes_esperados_no_step": 2},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "varredura_de_familia",
                      "n_corpos_esperado", "interferencia", "reabre_em_cad",
                      "folga_calibrada"],
            "nao_exige": ["malha_estanque", "portao_do_fatiador"],
            "resultado": "barrado_na_folga",
        },
    }



# ---------------------------------------------------------------- caso 10

def familia_casca(R=20.0, H=40.0):
    """Familia parametrica de SUPERFICIE aberta: face lateral de um cilindro."""
    from build123d import Cylinder, GeomType
    return Cylinder(R, H).faces().filter_by(GeomType.CYLINDER)[0]


def caso10():
    """parametrizar / superficie / visualizacao - superficie ABERTA varrida.

    Existe porque a quarta revisao externa apontou que a representacao mudava so o
    primeiro portao da varredura: o segundo continuava exigindo estanqueidade e o
    terceiro sempre escrevia 3MF, entao superficie aberta legitima reprovava sempre. O
    caso 8 exercita criar/superficie, e nao parametrizar/superficie.
    """
    from build123d import export_stl
    import trimesh
    d = _prep()
    face = familia_casca()
    stl = os.path.join(d, "c10_casca.stl")
    export_stl(face, stl, tolerance=0.02, angular_tolerance=0.15)
    m = trimesh.load(stl, force="mesh", process=False)
    m.merge_vertices()
    req = _req(os.path.join(d, "c10_req.json"), {
        "peca": stl,
        "requisitos": [
            {"id": "envelope", "tipo": "caixa", "valor": [40.0, 40.0, 40.0], "tol_mm": 0.5},
        ]})
    return {
        "id": "10_superficie_parametrica",
        "titulo": "familia parametrica de superficie aberta, para visualizacao",
        "classificacao": {"modalidade": "parametrizar", "representacao": "superficie",
                          "finalidade": "visualizacao"},
        "malha": stl, "step": None, "requisitos": req, "referencia": None,
        "familia": {"modulo": "casos", "funcao": "familia_casca",
                    "grade": "R=15,20;H=30,40", "representacao": "superficie"},
        "geometria_nao_vazia": {"ok": len(m.faces) > 0, "n_facetas": int(len(m.faces)),
                                "area_mm2": round(float(m.area), 2)},
        "declaracoes": {"encaixe_declarado": False},
        "fatos_da_malha": {"fechada_watertight": bool(m.is_watertight)},
        "espera": {
            "exige": ["intencao", "geometria_nao_vazia", "varredura_de_familia"],
            "nao_exige": ["malha_estanque", "zero_nao_manifold", "portao_do_fatiador",
                          "envelope_e_particao", "folga_calibrada", "reabre_em_cad"],
            "resultado": "aprovado",
            "extra": "a malha e ABERTA e a varredura tem que aprovar mesmo assim",
        },
    }


TODOS = [caso1, caso2, caso3, caso4, caso5, caso6, caso7, caso8, caso9, caso10]
