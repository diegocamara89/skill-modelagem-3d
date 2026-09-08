"""mutacoes.py - prova que a suite consegue REPROVAR, e pelo motivo certo.

Uso: python mutacoes.py [--json out.json]

Uma suite que sempre passa nao testa nada. Este arquivo introduz defeitos de proposito,
um por vez, e confere que o caso reprova.

DUAS CORRECOES DE 07/09/2026, depois da segunda revisao externa:

1. Antes, qualquer excecao virava PASSOU=False, e varias mutacoes conferiam apenas
   "nao passou". Logo uma falha de dependencia, importacao ou ambiente era contada como
   deteccao do defeito plantado. Agora cada mutacao declara ONDE espera a reprovacao, e
   erro de infraestrutura invalida o experimento em vez de virar credito.

2. A mutacao do datum alterava o RELATORIO, nao a geometria. Isso provava que o executor
   rejeita um relatorio com erro alto, e nao que ele detecta reconstrucao desalinhada.
   Agora ela muda a construcao, exporta a geometria defeituosa e remede.

ESTADOS DO EXPERIMENTO
  PEGOU     o caso reprovou, e nos verificadores esperados
  ESCAPOU   o caso passou apesar do defeito, ou reprovou em lugar diferente do esperado
  INVALIDO  houve erro de execucao: o experimento nao mediu nada
"""
import argparse, io, json, os, sys, traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import casos as CASOS
import matriz
import roda_casos

PEGOU, ESCAPOU, INVALIDO = "PEGOU", "ESCAPOU", "INVALIDO"


def _roda(fn):
    """Roda um caso. Excecao NAO conta como deteccao: devolve marca de invalido."""
    try:
        return roda_casos.roda(fn), None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def _codigos_no_detalhe(x, achados=None):
    """Todo valor sob uma chave "codigo", em qualquer profundidade. Acrescentado em M0.3:
    o oraculo conferia SO em qual verificador o erro apareceu, entao tempo esgotado,
    falha de importacao ou resultado ilegivel no mesmo verificador recebiam credito por um
    defeito que nunca foi exercitado."""
    achados = [] if achados is None else achados
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "codigo" and isinstance(v, str) and v:
                achados.append(v)
            else:
                _codigos_no_detalhe(v, achados)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _codigos_no_detalhe(v, achados)
    return achados


def _texto_do_detalhe(x):
    """Detalhe achatado em texto, para procurar a evidencia PLANTADA pela mutacao."""
    try:
        return json.dumps(x, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(x)


def _normaliza_errar_em(errar_em):
    """Aceita a forma antiga, uma sequencia de nomes, e a nova, um dicionario
    {verificador: {"codigo": ..., "evidencia": ...}}. Devolve sempre dicionario."""
    if isinstance(errar_em, dict):
        return {k: (v or {}) for k, v in errar_em.items()}
    return {n: {} for n in (errar_em or ())}


def _julga(r, erro, reprovar_em=(), bloquear_em=(), errar_em=(),
           extras_que_devem_falhar=()):
    """Confere que a reprovacao aconteceu EXATAMENTE onde a mutacao previu.

    CORRIGIDO 07/09/2026: qualquer erro de verificacao invalidava o experimento, mesmo
    quando o erro era a CONSEQUENCIA ESPERADA do defeito plantado. Erro esperado e erro de
    infraestrutura sao coisas diferentes: agora a mutacao declara onde espera erro, e so o
    erro NAO previsto invalida.
    """
    if erro:
        return INVALIDO, {"erro_de_execucao": erro}
    det = {"passou": r["PASSOU"], "reprovadas": r["reprovadas"], "bloqueios": r["bloqueios"],
           "erros": r["erros"],
           "cobrado_indevidamente": r["roteamento"]["cobrado_indevidamente"],
           "faltando_no_roteamento": r["roteamento"]["faltando_no_roteamento"],
           "extras_que_falharam": [e["nome"] for e in r.get("extras", []) if not e["passou"]]}
    esperado_errar = _normaliza_errar_em(errar_em)
    inesperados = [n for n in r["erros"] if n not in esperado_errar]
    if inesperados:
        det["erros_inesperados"] = inesperados
        return INVALIDO, det
    # ACRESCENTADO em M0.3: causa diferente no MESMO lugar invalida o experimento. Erro
    # no verificador previsto, mas por outra razao, nao e credito: e experimento perdido.
    causas = {}
    for nome, exigido in esperado_errar.items():
        if nome not in r["erros"]:
            continue
        alvo = (r.get("verificacoes") or {}).get(nome) or {}
        detalhe = alvo.get("detalhe")
        codigos = _codigos_no_detalhe(detalhe)
        texto = _texto_do_detalhe(detalhe)
        causas[nome] = {"codigos_encontrados": codigos}
        cod = exigido.get("codigo")
        if cod and cod not in codigos:
            det["causa_divergente"] = {
                "verificador": nome, "codigo_esperado": cod,
                "codigos_encontrados": codigos,
                "motivo": ("o erro apareceu no verificador previsto, mas com outra causa. "
                           "Credito aqui seria credito por defeito nao exercitado.")}
            det["causas"] = causas
            return INVALIDO, det
        ev = exigido.get("evidencia")
        if ev and ev not in texto:
            det["evidencia_da_injecao_ausente"] = {
                "verificador": nome, "evidencia_esperada": ev,
                "motivo": ("a mutacao planta uma marca propria. Sem ela, o erro pode ter "
                           "vindo de qualquer outra falha no mesmo verificador.")}
            det["causas"] = causas
            return INVALIDO, det
        causas[nome]["evidencia_conferida"] = bool(ev)
    if causas:
        det["causas"] = causas
    if r["PASSOU"]:
        return ESCAPOU, det
    faltou = []
    for n in reprovar_em:
        if n not in r["reprovadas"]:
            faltou.append("esperava reprovacao em %s" % n)
    for n in bloquear_em:
        if n not in r["bloqueios"]:
            faltou.append("esperava bloqueio em %s" % n)
    for n in esperado_errar:
        if n not in r["erros"]:
            faltou.append("esperava ERRO em %s" % n)
    for n in extras_que_devem_falhar:
        if not any(n in e for e in det["extras_que_falharam"]):
            faltou.append("esperava falha no extra %r" % n)
    if faltou:
        det["divergencia"] = faltou
        return ESCAPOU, det
    return PEGOU, det


def _req_mutado(c, nome, transforma):
    spec = json.load(open(c["requisitos"], encoding="utf-8"))
    transforma(spec)
    p = os.path.join(CASOS.SAIDA, nome)
    json.dump(spec, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    c["requisitos"] = p
    return c


# ------------------------------------------------------------------ mutacoes

def m_finalidade_exige_fatiador():
    """Eixo FINALIDADE. Visualizacao passa a exigir o fatiador: o caso 6 reprova por
    cobranca indevida no roteamento."""
    orig = matriz.POR_FINALIDADE["portao_do_fatiador"]
    matriz.POR_FINALIDADE["portao_do_fatiador"] = (True,) + orig[1:]
    try:
        r, e = _roda(CASOS.caso6)
    finally:
        matriz.POR_FINALIDADE["portao_do_fatiador"] = orig
    if e:
        return INVALIDO, {"erro_de_execucao": e}
    det = {"passou": r["PASSOU"],
           "cobrado_indevidamente": r["roteamento"]["cobrado_indevidamente"]}
    ok = (not r["PASSOU"]) and "portao_do_fatiador" in r["roteamento"]["cobrado_indevidamente"]
    return (PEGOU if ok else ESCAPOU), det


def m_representacao_perde_dispensa():
    """Eixo REPRESENTACAO isolado. Superficie declarada para IMPRESSAO: com a dispensa
    passa, sem a dispensa reprova.

    MEDIDO 07/09/2026: sem a dispensa, o fatiador ACEITA a casca aberta e nao reprova.
    Quem reprova e a estanqueidade. A versao anterior deste arquivo, e o texto do desenho,
    diziam que o fatiador pegava, e isso estava errado."""
    def superficie_para_impressao():
        c = CASOS.caso4()
        c["id"] = "4b_superficie_declarada_para_impressao"
        c["classificacao"] = {"modalidade": "criar", "representacao": "superficie",
                              "finalidade": "impressao_fdm"}
        c["espera"] = {"exige": ["intencao", "geometria_nao_vazia"],
                       "nao_exige": ["portao_do_fatiador", "malha_estanque",
                                     "zero_nao_manifold", "envelope_e_particao"],
                       "resultado": "aprovado"}
        return c

    antes, e1 = _roda(superficie_para_impressao)
    if e1:
        return INVALIDO, {"erro_de_execucao": "linha de base falhou: " + e1}
    orig = dict(matriz.INAPLICAVEIS["superficie"])
    matriz.INAPLICAVEIS["superficie"] = {}
    try:
        depois, e2 = _roda(superficie_para_impressao)
    finally:
        matriz.INAPLICAVEIS["superficie"] = orig
    if e2:
        return INVALIDO, {"erro_de_execucao": e2}
    det = {"com_a_dispensa_passou": antes["PASSOU"],
           "sem_a_dispensa_passou": depois["PASSOU"],
           "sem_a_dispensa_cobrou": depois["roteamento"]["cobrado_indevidamente"],
           "sem_a_dispensa_reprovou_em": depois["reprovadas"],
           "o_fatiador_reprovou": "portao_do_fatiador" in depois["reprovadas"],
           "nota": "o fatiador aceita casca aberta; quem reprova e a estanqueidade"}
    ok = (antes["PASSOU"] and not depois["PASSOU"]
          and "malha_estanque" in depois["reprovadas"])
    return (PEGOU if ok else ESCAPOU), det


def m_impressao_dispensa_fatiador():
    """Impressao deixa de exigir o fatiador: o caso 1 reprova por falta no roteamento."""
    orig = matriz.POR_FINALIDADE["portao_do_fatiador"]
    matriz.POR_FINALIDADE["portao_do_fatiador"] = orig[:3] + (False,) + orig[4:]
    try:
        r, e = _roda(CASOS.caso1)
    finally:
        matriz.POR_FINALIDADE["portao_do_fatiador"] = orig
    if e:
        return INVALIDO, {"erro_de_execucao": e}
    ok = (not r["PASSOU"]) and "portao_do_fatiador" in r["roteamento"]["faltando_no_roteamento"]
    return (PEGOU if ok else ESCAPOU), {
        "passou": r["PASSOU"], "faltando": r["roteamento"]["faltando_no_roteamento"]}


def m_verificador_obrigatorio_ausente():
    """NOVA, pedida pela revisao. Retira um verificador obrigatorio do registro. O caso tem
    que ficar INCOMPLETO, e nunca aprovado."""
    orig = roda_casos.VERIFICADORES.pop("portao_do_fatiador")
    try:
        r, e = _roda(CASOS.caso1)
    finally:
        roda_casos.VERIFICADORES["portao_do_fatiador"] = orig
    return _julga(r, e, bloquear_em=("portao_do_fatiador",))


def m_caixa_com_erro_de_cota():
    """Declara a caixa com 2 mm de erro: a intencao reprova."""
    def mutado():
        def t(spec):
            for r in spec["requisitos"]:
                if r["id"] == "envelope":
                    r["valor"] = [r["valor"][0] + 2.0, r["valor"][1], r["valor"][2]]
        return _req_mutado(CASOS.caso1(), "mut_caixa.json", t)
    return _julga(*_roda(mutado), reprovar_em=("intencao",))


def m_furo_no_lugar_errado():
    """Declara o furo central 3 mm fora: a intencao reprova."""
    def mutado():
        def t(spec):
            for r in spec["requisitos"]:
                if r["id"] == "furo_central":
                    r["posicao"] = [3.0, 0.0]
        return _req_mutado(CASOS.caso1(), "mut_furo_pos.json", t)
    return _julga(*_roda(mutado), reprovar_em=("intencao",))


def m_abertura_nao_circular():
    """NOVA, pedida pela revisao. Troca o furo redondo por uma abertura QUADRADA de mesma
    area e mesmo centro. A verificacao de furo tem que reprovar pela FORMA, nao pela area."""
    import numpy as np
    from build123d import Align, Box, Cylinder, Pos, export_stl

    def mutado():
        c = CASOS.caso1()
        L, P, T, D, D_fix, VAO = 70.0, 40.0, 8.0, 12.0, 4.5, 50.0
        lado = float(np.sqrt(np.pi * (D / 2) ** 2))          # mesma area do circulo
        corpo = Box(L, P, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        quad = Box(lado, lado, T * 3, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        furos = [quad] + [Pos(x, 0, 0) * Cylinder(D_fix / 2, T * 3)
                          for x in (-VAO / 2, VAO / 2)]
        peca = corpo - furos
        stl = os.path.join(CASOS.SAIDA, "mut_quadrado.stl")
        export_stl(peca, stl, tolerance=0.01, angular_tolerance=0.1)
        c["id"] = "1c_abertura_quadrada"
        c["malha"] = stl
        c["step"] = None
        c["geometria_nao_vazia"] = {"ok": len(peca.solids()) == 1 and float(peca.volume) > 0,
                                    "n_solidos": len(peca.solids())}

        def t(spec):
            spec["requisitos"] = [r for r in spec["requisitos"] if r["id"] == "furo_central"]
        return _req_mutado(c, "mut_quadrado_req.json", t)

    return _julga(*_roda(mutado), reprovar_em=("intencao",))


def m_datum_perdido_de_verdade():
    """CORRIGIDA. Reconstroi com o assento ALINHADO A EIXO em vez do angulo medido,
    exporta a geometria defeituosa e REMEDE. A mutacao nao escreve o numero que o
    verificador deveria descobrir."""
    from build123d import Align, Box, Cylinder, Pos, Rot, export_step, export_stl
    import find_datums

    def mutado():
        c = CASOS.caso5()
        med = json.load(open(os.path.join(CASOS.SAIDA, "c5_medidas.json"), encoding="utf-8"))
        L = med["comprimento"]["valor"]; W = med["largura"]["valor"]
        H = med["altura_maxima"]["valor"]; D = med["diametro_do_furo"]["valor"]
        # o defeito: corta o assento a 0 grau, perdendo a inclinacao medida
        ruim = (Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
                - (Pos(0, 0, H) * Rot(0, 0.0, 0)
                   * Box(120, 90, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
                - Cylinder(D / 2, 90))
        stl = os.path.join(CASOS.SAIDA, "mut_c5_sem_datum.stl")
        step = os.path.join(CASOS.SAIDA, "mut_c5_sem_datum.step")
        export_stl(ruim, stl, tolerance=0.01, angular_tolerance=0.1)
        export_step(ruim, step)
        # remede a geometria exportada, em vez de escrever o resultado
        lido = find_datums.com_fonte(stl, top=6, tol_ang=1.5, tol_plano=0.05, area_min=5.0)
        ni = lido["maior_regiao_inclinada"]
        ang = None if ni is None else (90.0 - ni["angulos_por_eixo_deg"]["Z+"]
                                       if ni["angulos_por_eixo_deg"]["Z+"] > 45
                                       else ni["angulos_por_eixo_deg"]["Z+"])
        ref_ang = c["datum"]["angulo_na_referencia_deg"]
        c["id"] = "5b_reconstrucao_sem_o_datum"
        c["malha"] = stl
        c["step"] = step
        c["geometria_nao_vazia"] = {"ok": len(ruim.solids()) == 1 and float(ruim.volume) > 0,
                                    "n_solidos": len(ruim.solids())}
        c["datum"] = {
            "angulo_na_referencia_deg": ref_ang,
            "angulo_na_reconstruida_deg": (round(ang, 3) if ang is not None else None),
            "erro_deg": (abs(ref_ang - ang) if (ang is not None and ref_ang is not None)
                         else ref_ang),
            "tol_deg": 0.5,
            "nota": "medido na geometria exportada, nao escrito pela mutacao",
            "regioes_inclinadas_encontradas": lido["n_regioes_inclinadas"]}

        # a caixa muda porque o corte reto deixa a peca mais alta: o experimento tem que
        # medir o DATUM, nao a caixa, entao os requisitos de caixa saem
        def t(spec):
            spec["requisitos"] = [r for r in spec["requisitos"] if r["tipo"] != "caixa"]
        return _req_mutado(c, "mut_c5_req.json", t)

    return _julga(*_roda(mutado), extras_que_devem_falhar=("assento reconstruido",))


def m_regiao_editada_declarada_intacta():
    """Declara como intacta a regiao que FOI editada: o caso 2 reprova na regiao."""
    def mutado():
        def t(spec):
            spec["requisitos"].append({
                "id": "regiao_editada_declarada_como_intacta", "tipo": "regiao_intacta",
                "caixa_min": [-31.0, -6.0, -1.0], "caixa_max": [-19.0, 6.0, 9.0],
                "tol_fracao": 1e-9})
        return _req_mutado(CASOS.caso2(), "mut_regiao.json", t)
    return _julga(*_roda(mutado), reprovar_em=("intencao", "regiao_preservada"))


def m_intercambio_com_um_componente():
    """NOVA. Entrega o STEP de UM componente como intercambio de uma montagem de dois:
    reabre_em_cad tem que reprovar pela contagem."""
    from build123d import Align, Cylinder, export_step

    def mutado():
        c = CASOS.caso3()
        so_um = os.path.join(CASOS.SAIDA, "mut_c3_um_componente.step")
        export_step(Cylinder(5.0, 20.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), so_um)
        c["id"] = "3b_intercambio_incompleto"
        c["step"] = so_um
        return c
    return _julga(*_roda(mutado), reprovar_em=("reabre_em_cad", "folga_calibrada"))


def m_particao_que_estoura():
    """NOVA. Peca com o dobro do limite util: o corte deslocado faz um pedaco estourar, e
    envelope_e_particao tem que reprovar por particao nao validada."""
    from build123d import Align, Box, export_stl

    def mutado():
        c = CASOS.caso1()
        peca = Box(492.0, 100.0, 50.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        stl = os.path.join(CASOS.SAIDA, "mut_492.stl")
        export_stl(peca, stl, tolerance=0.02, angular_tolerance=0.2)
        c["id"] = "1b_peca_que_estoura_o_envelope"
        c["malha"] = stl
        c["step"] = None
        c["geometria_nao_vazia"] = {"ok": True, "n_solidos": 1}

        def t(spec):
            spec["requisitos"] = [{"id": "corpo_unico", "tipo": "n_solidos", "valor": 1}]
        return _req_mutado(c, "mut_492_req.json", t)

    return _julga(*_roda(mutado), reprovar_em=("envelope_e_particao",))



# ---------------------------------------------------- mutacoes da terceira revisao

def m_estado_fora_do_contrato():
    """NOVA. Um verificador devolve um estado que nao existe no contrato. O caso NAO pode
    sair com evidencia completa nem aprovado."""
    orig = roda_casos.VERIFICADORES["orientacao_anisotropia"]
    roda_casos.VERIFICADORES["orientacao_anisotropia"] = lambda c: ("EROR", {"x": 1})
    try:
        r, e = _roda(CASOS.caso1)
    finally:
        roda_casos.VERIFICADORES["orientacao_anisotropia"] = orig
    if e:
        return INVALIDO, {"erro_de_execucao": e}
    det = {"passou": r["PASSOU"], "evidencia_completa": r["evidencia_completa"],
           "erros": r["erros"], "bloqueios": r["bloqueios"]}
    ok = (not r["PASSOU"]) and "orientacao_anisotropia" in r["erros"]
    return (PEGOU if ok else ESCAPOU), det


def m_id_neutro_no_requisito():
    """NOVA. Renomeia o requisito de preservacao para um id NEUTRO, mantendo o tipo, e o
    faz reprovar. A obrigacao tem que reprovar mesmo assim.

    Antes, a obrigacao era resolvida filtrando ids por substring, entao um id como R17
    reprovava na intencao e a obrigacao aparecia APROVADA."""
    def mutado():
        c = CASOS.caso2()

        def t(spec):
            for r in spec["requisitos"]:
                if r.get("tipo") == "regiao_intacta":
                    r["id"] = "R17"
                    # move a caixa para a regiao que FOI editada: tem que reprovar
                    r["caixa_min"] = [-31.0, -6.0, -1.0]
                    r["caixa_max"] = [-19.0, 6.0, 9.0]
                    break
        return _req_mutado(c, "mut_id_neutro.json", t)

    return _julga(*_roda(mutado), reprovar_em=("intencao", "regiao_preservada"))


def m_sem_requisito_de_preservacao():
    """NOVA. Remove TODOS os requisitos de preservacao de um caso que exige a obrigacao.
    Ausencia de evidencia tem que BLOQUEAR, nao aprovar."""
    def mutado():
        c = CASOS.caso2()

        def t(spec):
            spec["requisitos"] = [r for r in spec["requisitos"]
                                  if r.get("tipo") != "regiao_intacta"]
        c["requisitos_de_controle"] = None
        return _req_mutado(c, "mut_sem_preservacao.json", t)

    return _julga(*_roda(mutado), bloquear_em=("regiao_preservada",))


def m_inclinacao_invertida():
    """NOVA. Reconstroi com a inclinacao do assento INVERTIDA de sinal. O angulo com Z+
    fica igual, a caixa fica igual e o numero de corpos fica igual: so a normal orientada
    denuncia."""
    from build123d import Align, Box, Cylinder, Pos, Rot, export_step, export_stl
    import find_datums
    import numpy as np

    def mutado():
        c = CASOS.caso5()
        med = json.load(open(os.path.join(CASOS.SAIDA, "c5_medidas.json"), encoding="utf-8"))
        L = med["comprimento"]["valor"]; W = med["largura"]["valor"]
        H = med["altura_maxima"]["valor"]; D = med["diametro_do_furo"]["valor"]
        ANG = med["angulo_do_assento"]["valor"]
        invertida = (Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
                     - (Pos(0, 0, H) * Rot(0, -ANG, 0)
                        * Box(120, 90, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)))
                     - Cylinder(D / 2, 90))
        stl = os.path.join(CASOS.SAIDA, "mut_c5_invertida.stl")
        step = os.path.join(CASOS.SAIDA, "mut_c5_invertida.step")
        export_stl(invertida, stl, tolerance=0.01, angular_tolerance=0.1)
        export_step(invertida, step)
        lido = find_datums.com_fonte(stl, top=6, tol_ang=1.5, tol_plano=0.05, area_min=5.0)
        ni = lido["maior_regiao_inclinada"]
        n_novo = None if ni is None else np.array(ni["normal"], float)
        n_ref = c["datum"]["normal_na_referencia"]
        n_ref = None if n_ref is None else np.array(n_ref, float)

        def ent(u, v):
            if u is None or v is None:
                return None
            cs = float(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1))
            return float(np.degrees(np.arccos(cs)))

        ang_novo = None if ni is None else (90.0 - ni["angulos_por_eixo_deg"]["Z+"]
                                            if ni["angulos_por_eixo_deg"]["Z+"] > 45
                                            else ni["angulos_por_eixo_deg"]["Z+"])
        c["id"] = "5c_inclinacao_invertida"
        c["malha"] = stl
        c["step"] = step
        c["geometria_nao_vazia"] = {"ok": len(invertida.solids()) == 1
                                    and float(invertida.volume) > 0,
                                    "n_solidos": len(invertida.solids())}
        c["datum"] = dict(c["datum"],
                          normal_na_reconstruida=(None if n_novo is None
                                                  else [round(float(x), 6) for x in n_novo]),
                          angulo_na_reconstruida_deg=(round(ang_novo, 3) if ang_novo else None),
                          angulo_entre_normais_deg=(None if ent(n_ref, n_novo) is None
                                                    else round(ent(n_ref, n_novo), 4)),
                          erro_deg=(None if ent(n_ref, n_novo) is None
                                    else round(ent(n_ref, n_novo), 4)),
                          nota="inclinacao invertida de sinal, medida na geometria exportada")

        def t(spec):
            spec["requisitos"] = [r for r in spec["requisitos"] if r["tipo"] != "caixa"]
        return _req_mutado(c, "mut_c5_inv_req.json", t)

    return _julga(*_roda(mutado), extras_que_devem_falhar=("mantem a NORMAL",))


def m_destino_contaminado():
    """NOVA. Monta o pacote num destino que JA contem um arquivo privado. O empacotador
    tem que recusar em vez de copiar por cima e declarar limpo."""
    # CORRIGIDO 07/09/2026 depois da quarta revisao externa, duas coisas. Primeira: o
    # diretorio era previsivel por PID, podia ser reaproveitado e era apagado
    # recursivamente, entao reuso de PID tornava a colisao possivel. Agora e
    # TemporaryDirectory exclusivo, e so ele e removido. Segunda: o oraculo aceitava
    # codigo de saida diferente de zero SEM JSON, entao um processo que falhasse antes de
    # chegar ao empacotador satisfazia o critério. Agora exige resposta valida e o motivo
    # especifico.
    import subprocess, tempfile
    with tempfile.TemporaryDirectory(prefix="skill3d_dest_sujo_") as raiz:
        dest = os.path.join(raiz, "pacote")
        os.makedirs(dest)
        sujo = os.path.join(dest, "resto_de_pacote_anterior.json")
        io.open(sujo, "w", encoding="utf-8").write(
            '{"nota": "arquivo de um pacote anterior que ninguem removeu"}')
        r = subprocess.run([sys.executable, os.path.join(AQUI, "empacota.py"),
                            "--destino", dest], capture_output=True, text=True, timeout=300)
        saida = r.stdout
        tem_json = "{" in saida
        d = json.loads(saida[saida.find("{"):]) if tem_json else {}
        motivo = d.get("erro_de_destino") or ""
        det = {"codigo_de_saida": r.returncode, "houve_json": tem_json,
               "copiados_para": d.get("copiados_para"),
               "erro_de_destino": motivo[:160],
               "o_arquivo_sujo_continua_la": os.path.isfile(sujo),
               "quantos_arquivos_foram_copiados": len(os.listdir(dest)) - 1,
               "stderr": (r.stderr or "")[-160:]}
        ok = (tem_json and r.returncode != 0 and d.get("copiados_para") is None
              and "nao esta vazio" in motivo.lower()
              and det["quantos_arquivos_foram_copiados"] == 0)
    return (PEGOU if ok else ESCAPOU), det


def m_perfil_sem_envelope():
    """NOVA. Perfil de maquina sem as dimensoes do envelope. Falta de informacao NAO pode
    virar cabe=True."""
    import importlib
    sc = importlib.import_module("slice_check")
    perfil_ok = {"printable_height": "256",
                 "printable_area": ["0x0", "256x0", "256x256", "0x256"]}
    perfil_cego = {"printable_area": []}
    modelo = os.path.join(CASOS.SAIDA, "c1_espacador.stl")
    if not os.path.isfile(modelo):
        CASOS.caso1()
    a = sc.confere_envelope(modelo, perfil_ok)
    b = sc.confere_envelope(modelo, perfil_cego)
    det = {"com_envelope_cabe": a["cabe_no_envelope"],
           "sem_envelope_cabe": b["cabe_no_envelope"],
           "sem_envelope_desconhecido_em": b["envelope_desconhecido_em"],
           "sem_envelope_problemas": b["problemas"]}
    ok = (a["cabe_no_envelope"] is True and b["cabe_no_envelope"] is None
          and bool(b["problemas"]))
    return (PEGOU if ok else ESCAPOU), det


def m_registro_sem_estado_explicito():
    """NOVA. Medicao sem o campo de estado, ou com estado desconhecido, nao pode contar
    como definitiva e ser recomendada."""
    # temporario exclusivo, e removido pelo proprio gerenciador de contexto
    import tempfile
    _tmp = tempfile.TemporaryDirectory(prefix="skill3d_dados_")
    dados = _tmp.name
    reg_vazio = os.path.join(dados, "registro_sem_pendencia.md")
    io.open(reg_vazio, "w", encoding="utf-8").write("# registro sintetico sem pendencia\n")
    arq = os.path.join(dados, "folgas_medidas.json")
    json.dump({"entradas": [
        {"ajuste": "deslizante", "maquina": "M", "material": "F", "folga_mm": 0.22,
         "data": "2026-09-07", "origem": "MEDIDO em cupom"},                       # sem estado
        {"ajuste": "deslizante", "maquina": "M", "material": "F", "folga_mm": 0.24,
         "data": "2026-09-07", "origem": "MEDIDO em cupom", "estado": "quem_sabe"},
    ]}, io.open(arq, "w", encoding="utf-8"), indent=1)
    velho = os.environ.get("SKILL3D_DADOS")
    os.environ["SKILL3D_DADOS"] = dados
    try:
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(AQUI, "tolerance_lookup.py"),
                            "--ajuste", "deslizante", "--maquina", "M", "--material", "F",
                            "--registro", reg_vazio],
                           capture_output=True, text=True, timeout=300,
                           env=dict(os.environ, SKILL3D_DADOS=dados))
        d = json.loads(r.stdout[r.stdout.find("{"):])
    finally:
        if velho is None:
            os.environ.pop("SKILL3D_DADOS", None)
        else:
            os.environ["SKILL3D_DADOS"] = velho
        _tmp.cleanup()
    det = {"medicao_aplicavel": d.get("medicao_aplicavel"),
           "valor_a_usar_mm": d.get("valor_a_usar_mm"),
           "n_invalidas": len(d.get("medicoes_de_esquema_invalido") or []),
           "origem": d.get("origem_do_valor")}
    ok = (d.get("medicao_aplicavel") is False and d.get("valor_a_usar_mm") is None
          and det["n_invalidas"] == 2)
    return (PEGOU if ok else ESCAPOU), det


def m_variante_geometricamente_invalida():
    """NOVA, pedida pela terceira revisao. Grade que inclui uma variante geometricamente
    invalida: a varredura tem que reprovar, e o caso de parametrizar com ela."""
    def mutado():
        c = CASOS.caso7()
        c["id"] = "7b_familia_com_variante_invalida"
        # d = 12 num furo par a par de 20 mm de vao encosta nas bordas e no vizinho:
        # a folga entre os dois furos vira zero e o kernel produz contato tangente
        c["familia"] = {"modulo": "casos", "funcao": "familia_placa",
                        "grade": "L=80;d=5,40"}
        return c
    return _julga(*_roda(mutado), reprovar_em=("varredura_de_familia",))


# ------------------------------------------- mutacoes da quarta revisao

def familia_que_explode(**kw):
    """Familia que levanta excecao: simula falha OPERACIONAL, nao geometrica."""
    raise RuntimeError("falha operacional simulada na construcao da variante")


def m_varredura_de_execucao_anterior():
    """NOVA. Uma varredura aprovada, e em seguida uma que falha por funcao inexistente.
    A segunda tem que dar ERRO, e nunca reaproveitar a aprovacao da primeira."""
    def bom():
        c = CASOS.caso7()
        c["id"] = "7c_varredura_boa"
        return c

    def ruim():
        c = CASOS.caso7()
        c["id"] = "7d_varredura_com_funcao_inexistente"
        c["familia"] = {"modulo": "casos", "funcao": "funcao_que_nao_existe",
                        "grade": "L=80;d=5"}
        return c

    r1, e1 = _roda(bom)
    if e1:
        return INVALIDO, {"erro_de_execucao": "linha de base falhou: " + e1}
    if r1["verificacoes"]["varredura_de_familia"]["estado"] != "APROVADA":
        return INVALIDO, {"motivo": "a linha de base nao aprovou a varredura",
                          "estado": r1["verificacoes"]["varredura_de_familia"]["estado"]}
    r2, e2 = _roda(ruim)
    if e2:
        return INVALIDO, {"erro_de_execucao": e2}
    est = r2["verificacoes"]["varredura_de_familia"]["estado"]
    det = {"estado_da_primeira": "APROVADA", "estado_da_segunda": est,
           "detalhe_da_segunda": str(r2["verificacoes"]["varredura_de_familia"]["detalhe"])[:200],
           "segunda_passou": r2["PASSOU"]}
    ok = est == "ERRO" and not r2["PASSOU"]
    return (PEGOU if ok else ESCAPOU), det


def m_erro_operacional_na_varredura():
    """NOVA. Variante que levanta excecao. Isso e erro OPERACIONAL: a varredura nao
    avaliou geometria, logo o estado tem que ser ERRO, e nao reprovacao geometrica."""
    def mutado():
        c = CASOS.caso7()
        c["id"] = "7e_variante_que_explode"
        c["familia"] = {"modulo": "mutacoes", "funcao": "familia_que_explode",
                        "grade": "L=80;d=5"}
        return c

    # CORRIGIDO em M0.3: exigia apenas estado ERRO naquele verificador, entao tempo
    # esgotado ou falha de importacao no mesmo lugar receberiam o mesmo credito. Agora
    # exige o CODIGO e a marca plantada pela propria mutacao.
    return _julga(*_roda(mutado),
                  errar_em={"varredura_de_familia":
                            {"codigo": "E_CONSTRUCAO",
                             "evidencia": "falha operacional simulada"}})


def m_relatorio_dentro_do_destino():
    """NOVA. Aponta o relatorio para DENTRO do destino. O empacotador tem que recusar
    antes de copiar, porque o relatorio e gravado depois da auditoria."""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory(prefix="skill3d_rel_") as raiz:
        dest = os.path.join(raiz, "pacote")
        rel = os.path.join(dest, "relatorio.json")
        r = subprocess.run([sys.executable, os.path.join(AQUI, "empacota.py"),
                            "--destino", dest, "--json", rel],
                           capture_output=True, text=True, timeout=300)
        existe = os.path.isdir(dest)
        det = {"codigo_de_saida": r.returncode,
               "mensagem": ((r.stderr or "") + (r.stdout or ""))[-200:],
               "destino_foi_criado": existe,
               "arquivos_no_destino": (sorted(os.listdir(dest)) if existe else [])}
        # CORRIGIDO em M0.1: o criterio era a frase "DENTRO do destino", sujeita a caixa
        # e a acento, e criterio por frase ja falhou uma vez neste projeto. Agora e o
        # codigo estavel emitido pelo empacotador.
        ok = (r.returncode != 0
              and "E_CAMINHO_NO_DESTINO" in ((r.stderr or "") + (r.stdout or ""))
              and not det["arquivos_no_destino"])
    with tempfile.TemporaryDirectory(prefix="skill3d_rel2_") as raiz2:
        dest2 = os.path.join(raiz2, "pacote")
        rel2 = os.path.join(raiz2, "matriz.py")
        r2 = subprocess.run([sys.executable, os.path.join(AQUI, "empacota.py"),
                             "--destino", dest2, "--json", rel2],
                            capture_output=True, text=True, timeout=300)
        # CORRIGIDO em M0.3: o criterio era so "codigo de saida diferente de zero", que
        # qualquer falha satisfaz, inclusive erro de sintaxe. Agora exige o motivo.
        saida2 = (r2.stderr or "") + (r2.stdout or "")
        det["colisao_de_nome_codigo_de_saida"] = r2.returncode
        det["colisao_de_nome_codigo"] = ("E_CAMINHO_NOME_DE_PACOTE"
                                         if "E_CAMINHO_NOME_DE_PACOTE" in saida2 else None)
        det["colisao_de_nome_mensagem"] = saida2[-140:]
        ok = ok and r2.returncode != 0 and "E_CAMINHO_NOME_DE_PACOTE" in saida2
    return (PEGOU if ok else ESCAPOU), det


def m_envelope_com_valor_invalido():
    """NOVA. Perfil com altura nao finita e area degenerada. Valor PRESENTE e invalido nao
    pode virar cabe=True. A mutacao anterior testava apenas a AUSENCIA de dimensao."""
    import importlib
    sc = importlib.import_module("slice_check")
    modelo = os.path.join(CASOS.SAIDA, "c1_espacador.stl")
    if not os.path.isfile(modelo):
        CASOS.caso1()
    bom = {"printable_height": "256",
           "printable_area": ["0x0", "256x0", "256x256", "0x256"]}
    ruins = {
        "altura_nan": {"printable_height": "nan", "printable_area": bom["printable_area"]},
        "altura_negativa": {"printable_height": "-10", "printable_area": bom["printable_area"]},
        "area_degenerada": {"printable_height": "256", "printable_area": ["0x0"]},
        "area_com_ponto_repetido": {"printable_height": "256",
                                    "printable_area": ["0x0", "0x0", "0x0"]},
    }
    a = sc.confere_envelope(modelo, bom)
    res = {k: sc.confere_envelope(modelo, v) for k, v in ruins.items()}
    det = {"com_perfil_valido_cabe": a["cabe_no_envelope"],
           "resultados": {k: {"cabe": v["cabe_no_envelope"],
                              "invalidos": v["valores_invalidos_no_perfil"]}
                          for k, v in res.items()}}
    ok = (a["cabe_no_envelope"] is True
          and all(v["cabe_no_envelope"] is not True for v in res.values())
          and all(v["valores_invalidos_no_perfil"] or v["envelope_desconhecido_em"]
                  for v in res.values()))
    return (PEGOU if ok else ESCAPOU), det


def m_ids_duplicados():
    """NOVA. Dois requisitos do MESMO tipo com o MESMO id, o primeiro reprovando. A
    obrigacao daquele tipo nao pode aprovar por sobrescrita de evidencia."""
    def mutado():
        c = CASOS.caso2()

        def t(spec):
            base = [r for r in spec["requisitos"] if r.get("tipo") == "regiao_intacta"][0]
            ruim = dict(base)
            ruim["id"] = base["id"]
            ruim["caixa_min"] = [-31.0, -6.0, -1.0]
            ruim["caixa_max"] = [-19.0, 6.0, 9.0]
            spec["requisitos"].insert(0, ruim)
        c["requisitos_de_controle"] = None
        return _req_mutado(c, "mut_ids_dup.json", t)

    # id repetido vira especificacao invalida, e a obrigacao daquele tipo passa a ERRO
    # de proposito: sem evidencia valida ela nao pode aprovar nem reprovar calada.
    return _julga(*_roda(mutado), reprovar_em=("intencao",),
                  errar_em=("regiao_preservada",))

def m_identidade_de_caminho():
    """NOVA em M0.1. Identidade FISICA de caminho, com controle positivo. A protecao
    anterior comparava texto, entao junção e vinculo passavam, e a validacao rodava so
    quando --destino estava presente. Aqui os cinco casos correm juntos de proposito:
    tres recusas e DUAS aceitacoes. Sem as aceitacoes, um empacotador que recusasse
    qualquer relatorio satisfaria a lista de recusas sozinho."""
    import subprocess, tempfile, hashlib
    emp = os.path.join(AQUI, "empacota.py")
    CODIGOS = ("E_CAMINHO_NO_DESTINO", "E_CAMINHO_SOBRE_ENTRADA", "E_CAMINHO_NOME_DE_PACOTE")

    def entradas():
        h = {}
        for nome in sorted(os.listdir(AQUI)):
            c = os.path.join(AQUI, nome)
            if os.path.isfile(c):
                h[nome] = hashlib.sha256(io.open(c, "rb").read()).hexdigest()
        return h

    def roda(*args):
        r = subprocess.run([sys.executable, emp] + list(args),
                           capture_output=True, text=True, timeout=600, cwd=AQUI)
        return r.returncode, (r.stderr or "") + (r.stdout or "")

    def codigo(txt):
        for c in CODIGOS:
            if c in txt:
                return c
        return None

    det = {}
    antes = entradas()

    # 1. recusa: mesma pasta escrita com caixa diferente
    with tempfile.TemporaryDirectory(prefix="skill3d_ident1_") as raiz:
        dest = os.path.join(raiz, "Pacote")
        rc, txt = roda("--destino", dest, "--json", os.path.join(raiz, "PACOTE", "rel.json"))
        escreveu = os.path.isdir(dest) and bool(os.listdir(dest))
        det["recusa_caixa"] = {"codigo_de_saida": rc, "codigo": codigo(txt),
                               "destino_recebeu_arquivo": escreveu}
        ok1 = rc != 0 and codigo(txt) == "E_CAMINHO_NO_DESTINO" and not escreveu

    # 2. recusa: auditoria SEM destino, relatorio sobre um arquivo de entrada
    alvo = os.path.join(AQUI, "matriz.py")
    h_pre = hashlib.sha256(io.open(alvo, "rb").read()).hexdigest()
    rc, txt = roda("--verificar", "--json", alvo)
    h_pos = hashlib.sha256(io.open(alvo, "rb").read()).hexdigest()
    det["recusa_sobre_entrada"] = {"codigo_de_saida": rc, "codigo": codigo(txt),
                                   "entrada_alterada": h_pre != h_pos}
    ok2 = rc != 0 and codigo(txt) == "E_CAMINHO_SOBRE_ENTRADA" and h_pre == h_pos

    # 3. recusa: junção REAL. Variacao de caixa nao demonstra identidade fisica.
    with tempfile.TemporaryDirectory(prefix="skill3d_ident3_") as raiz:
        dest = os.path.join(raiz, "pacote")
        os.makedirs(dest)
        link = os.path.join(raiz, "L")
        mk = subprocess.run(["cmd", "/c", "mklink", "/J", link, dest],
                            capture_output=True, text=True)
        if not os.path.isdir(link):
            det["recusa_junção"] = {"erro_de_infraestrutura":
                                    "mklink falhou: " + ((mk.stderr or "") + (mk.stdout or ""))[-120:]}
            return INVALIDO, det
        rc, txt = roda("--destino", dest, "--json", os.path.join(link, "rel.json"))
        escreveu = bool(os.listdir(dest))
        det["recusa_junção"] = {"codigo_de_saida": rc, "codigo": codigo(txt),
                                "destino_recebeu_arquivo": escreveu}
        ok3 = rc != 0 and codigo(txt) == "E_CAMINHO_NO_DESTINO" and not escreveu

    # 4. CONTROLE POSITIVO: relatorio fora da arvore, pacote monta e auditoria aprova
    with tempfile.TemporaryDirectory(prefix="skill3d_ident4_") as raiz:
        dest = os.path.join(raiz, "pacote")
        rel = os.path.join(raiz, "evidencia_da_montagem.json")
        rc, txt = roda("--destino", dest, "--json", rel)
        montou = os.path.isdir(dest) and bool(os.listdir(dest))
        rel_lido = {}
        if os.path.isfile(rel):
            try:
                rel_lido = json.loads(io.open(rel, encoding="utf-8").read())
            except ValueError:
                rel_lido = {"ilegivel": True}
        aud = rel_lido.get("auditoria_do_destino") or {}
        det["aceita_relatorio_externo"] = {
            "codigo_de_saida": rc, "codigo": codigo(txt), "pacote_montado": montou,
            "relatorio_gravado": os.path.isfile(rel),
            "sobrando": aud.get("sobrando"), "faltou": aud.get("faltou")}
        ok4 = (rc == 0 and montou and os.path.isfile(rel)
               and aud.get("sobrando") == [] and aud.get("faltou") == [])

    # 5. CONTROLE POSITIVO: auditoria sem destino grava e nao toca em entrada
    with tempfile.TemporaryDirectory(prefix="skill3d_ident5_") as raiz:
        rel = os.path.join(raiz, "auditoria.json")
        pre = entradas()
        rc, txt = roda("--verificar", "--json", rel)
        pos = entradas()
        mudou = sorted(k for k in pre if pre[k] != pos.get(k))
        det["aceita_auditoria_sem_destino"] = {
            "codigo_de_saida": rc, "codigo": codigo(txt),
            "relatorio_gravado": os.path.isfile(rel), "entradas_alteradas": mudou}
        ok5 = rc == 0 and os.path.isfile(rel) and not mudou

    depois = entradas()
    alteradas = sorted(k for k in antes if antes[k] != depois.get(k))
    det["entradas_alteradas_no_conjunto"] = alteradas
    ok = ok1 and ok2 and ok3 and ok4 and ok5 and not alteradas
    return (PEGOU if ok else ESCAPOU), det


def m_escrita_do_formato_fechado():
    """NOVA em M0.2. Tres casos, nao dois, porque dois exemplos de FALHA sao satisfeitos
    por uma implementacao que nunca aprova nada. E a injecao tem que atingir a escrita do
    formato fechado, nao uma etapa anterior: negar o diretorio inteiro faria a exportacao
    de malha falhar primeiro, e o resultado traria o codigo de outra etapa. Por isso o
    alvo .3mf e ocupado por um DIRETORIO, o que deixa a escrita do .stl funcionando.

    MEDIDO aqui: o escritor de 3MF desta versao NAO levanta OSError nessa situacao, e sim
    ELib3MFException com error_code 5, que a biblioteca chama de GENERICEXCEPTION. Logo o
    codigo dela nao separa falha de E/S de recusa de formato, e quem separa e a medicao
    do proprio caminho de saida."""
    import subprocess, tempfile
    sw = os.path.join(AQUI, "sweep_params.py")

    def varre(grade, saida, antes=None):
        os.makedirs(saida, exist_ok=True)
        if antes:
            antes(saida)
        rel = os.path.join(os.path.dirname(saida), "s.json")
        r = subprocess.run([sys.executable, sw, "--modulo", "casos", "--funcao",
                            "familia_placa", "--grade", grade, "--saida", saida,
                            "--json", rel], capture_output=True, text=True,
                           timeout=900, cwd=AQUI)
        d = {}
        if os.path.isfile(rel):
            try:
                d = json.loads(io.open(rel, encoding="utf-8").read())
            except ValueError:
                d = {"ilegivel": True}
        return r.returncode, d

    det = {}

    # 1. falha OPERACIONAL na escrita do formato fechado
    with tempfile.TemporaryDirectory(prefix="skill3d_3mf1_") as raiz:
        def ocupa(saida):
            os.makedirs(os.path.join(saida, "v_L80_d5.3mf"), exist_ok=True)
        rc, d = varre("L=80;d=5", os.path.join(raiz, "v"), antes=ocupa)
        v = (d.get("variantes") or [{}])[0]
        concl = v.get("etapas_concluidas") or []
        cam = v.get("caminho_de_saida") or ""
        det["falha_operacional"] = {
            "estado": v.get("estado"), "codigo": v.get("codigo"), "etapa": v.get("etapa"),
            "etapas_concluidas": concl, "saida": os.path.basename(cam),
            "reprovadas_por_geometria": d.get("n_reprovadas_por_geometria")}
        ok1 = (v.get("estado") == "ERRO_OPERACIONAL" and v.get("codigo") == "E_EXPORT_3MF"
               and v.get("etapa") == "exportacao" and "exportacao_malha" in concl
               and cam.endswith(".3mf") and d.get("n_reprovadas_por_geometria") == 0)

    # 2. reprovacao GEOMETRICA, com escrita permitida
    with tempfile.TemporaryDirectory(prefix="skill3d_3mf2_") as raiz:
        rc, d = varre("L=80;d=40", os.path.join(raiz, "v"))
        v = (d.get("variantes") or [{}])[0]
        det["reprovacao_geometrica"] = {
            "estado": v.get("estado"), "codigo": v.get("codigo"),
            "passou_tudo": v.get("passou_tudo"),
            "reprovadas_por_geometria": d.get("n_reprovadas_por_geometria"),
            "houve_erro_operacional": d.get("houve_erro_operacional")}
        ok2 = (v.get("estado") == "AVALIADA" and v.get("passou_tudo") is False
               and v.get("codigo") is None
               and d.get("n_reprovadas_por_geometria") == 1
               and d.get("houve_erro_operacional") is False)

    # 3. CONTROLE POSITIVO: a MESMA geometria valida, com escrita permitida, aprova
    with tempfile.TemporaryDirectory(prefix="skill3d_3mf3_") as raiz:
        rc, d = varre("L=80;d=5", os.path.join(raiz, "v"))
        v = (d.get("variantes") or [{}])[0]
        p3 = v.get("portao_3_3mf") or {}
        det["controle_positivo"] = {
            "estado": v.get("estado"), "passou_tudo": v.get("passou_tudo"),
            "bytes_do_3mf": p3.get("bytes"), "aprovadas": d.get("n_aprovadas"),
            "codigo_de_saida": rc}
        ok3 = (v.get("estado") == "AVALIADA" and v.get("passou_tudo") is True
               and (p3.get("bytes") or 0) > 0 and d.get("n_aprovadas") == 1 and rc == 0)

    det["nota"] = ("sem o caso 3 os dois primeiros seriam satisfeitos por quem nunca "
                   "aprova; sem a prova de etapa, a injecao poderia ter atingido a "
                   "exportacao de malha")
    return (PEGOU if (ok1 and ok2 and ok3) else ESCAPOU), det


def familia_que_demora(**kw):
    """Familia que estoura o tempo limite. Serve para provar que tempo esgotado no MESMO
    verificador NAO recebe credito pelo defeito que a mutacao pretendia exercitar."""
    import time
    time.sleep(120)
    raise RuntimeError("nao deveria chegar aqui")


def m_causa_divergente_no_mesmo_verificador():
    """NOVA em M0.3. Par discriminante: a MESMA declaracao de erro esperado, com dois
    motivos diferentes no mesmo verificador.

    A: tempo esgotado. Tem que dar INVALIDO, porque o defeito previsto nunca foi
       exercitado, e credito aqui seria credito por experimento perdido.
    B: CONTROLE POSITIVO, a excecao plantada de verdade. Tem que dar PEGOU.

    Sem B, um oraculo que devolvesse INVALIDO para tudo satisfaria A sozinho."""
    exigencia = {"varredura_de_familia": {"codigo": "E_CONSTRUCAO",
                                          "evidencia": "falha operacional simulada"}}
    det = {}

    # A. tempo esgotado no verificador previsto
    antes = os.environ.get("SKILL3D_TEMPO_LIMITE_S")
    os.environ["SKILL3D_TEMPO_LIMITE_S"] = "5"
    try:
        import importlib
        importlib.reload(roda_casos)

        def mutado_a():
            c = CASOS.caso7()
            c["id"] = "7f_varredura_que_estoura_o_tempo"
            c["familia"] = {"modulo": "mutacoes", "funcao": "familia_que_demora",
                            "grade": "L=80;d=5"}
            return c

        est_a, det_a = _julga(*_roda(mutado_a), errar_em=exigencia)
    finally:
        if antes is None:
            os.environ.pop("SKILL3D_TEMPO_LIMITE_S", None)
        else:
            os.environ["SKILL3D_TEMPO_LIMITE_S"] = antes
        import importlib
        importlib.reload(roda_casos)

    det["A_tempo_esgotado"] = {
        "estado_do_oraculo": est_a,
        "causa_divergente": det_a.get("causa_divergente"),
        "codigos_encontrados": ((det_a.get("causa_divergente") or {})
                                .get("codigos_encontrados"))}
    okA = est_a == INVALIDO and bool(det_a.get("causa_divergente"))

    # B. CONTROLE POSITIVO: a excecao plantada, mesma declaracao
    def mutado_b():
        c = CASOS.caso7()
        c["id"] = "7g_variante_que_explode_com_causa"
        c["familia"] = {"modulo": "mutacoes", "funcao": "familia_que_explode",
                        "grade": "L=80;d=5"}
        return c

    est_b, det_b = _julga(*_roda(mutado_b), errar_em=exigencia)
    det["B_controle_positivo"] = {"estado_do_oraculo": est_b,
                                  "causas": det_b.get("causas")}
    okB = est_b == PEGOU

    det["nota"] = ("o oraculo antigo aceitava os dois como deteccao, porque conferia so em "
                   "QUAL verificador o erro apareceu")
    return (PEGOU if (okA and okB) else ESCAPOU), det


def m_area_da_mesa_degenerada():
    """NOVA em M0.4. A mesa era validada por EXTENSAO nos dois eixos, e tres pontos
    colineares tem extensao positiva nos dois eixos e area zero.

    Os dois casos autointersectantes estao aqui de proposito. O simetrico tem area zero
    por cancelamento na soma de produtos cruzados, entao ele e pego pelo teste de AREA e
    nao exercita o teste de poligono simples. Sem o assimetrico, com area nao nula, o
    teste de autointersecao receberia credito sem nunca ter sido exercitado.

    E os dois controles positivos: mesa retangular e mesa triangular VALIDA continuam
    aprovando. Sem eles, uma validacao que recusasse qualquer mesa passaria."""
    import slice_check as sc
    modelo = os.path.join(AQUI, "caso3_cubo_ok.stl")
    alt = {"printable_height": 256}

    def confere(area):
        return sc.confere_envelope(modelo, dict(alt, printable_area=area))

    recusas = {
        "colinear": ["0x0", "128x128", "256x256"],
        "autointersectante_simetrico": ["0x0", "256x256", "256x0", "0x256"],
        "autointersectante_assimetrico": ["0x0", "200x200", "200x0", "0x120"],
    }
    aceitas = {
        "retangular": ["0x0", "256x0", "256x256", "0x256"],
        "triangular_valida": ["0x0", "256x0", "128x220"],
    }

    det = {"recusas": {}, "aceitacoes": {}}
    ok = True
    for nome, area in recusas.items():
        r = confere(area)
        det["recusas"][nome] = {"cabe": r["cabe_no_envelope"],
                                "area_mm2": r["area_da_mesa_mm2"],
                                "invalidos": r["valores_invalidos_no_perfil"]}
        ok = ok and r["cabe_no_envelope"] is None and bool(r["valores_invalidos_no_perfil"])

    # o assimetrico tem que ser pego pelo motivo CERTO, e nao pelo de area nula
    motivo_assim = " ".join(det["recusas"]["autointersectante_assimetrico"]["invalidos"])
    det["assimetrico_pego_por_autointersecao"] = "autointersectante" in motivo_assim
    det["assimetrico_area_nao_nula"] = (
        (det["recusas"]["autointersectante_assimetrico"]["area_mm2"] or 0) > 0)
    ok = ok and det["assimetrico_pego_por_autointersecao"] and det["assimetrico_area_nao_nula"]

    for nome, area in aceitas.items():
        r = confere(area)
        det["aceitacoes"][nome] = {"cabe": r["cabe_no_envelope"],
                                   "area_mm2": r["area_da_mesa_mm2"],
                                   "invalidos": r["valores_invalidos_no_perfil"]}
        ok = ok and r["cabe_no_envelope"] is True and not r["valores_invalidos_no_perfil"]

    # o resultado tem que declarar o que ele compara
    r = confere(aceitas["retangular"])
    base = r.get("base_da_comparacao") or ""
    det["declara_a_base_da_comparacao"] = "caixa envolvente" in base
    ok = ok and det["declara_a_base_da_comparacao"]

    return (PEGOU if ok else ESCAPOU), det


def m_borda_declarada_ao_contrario():
    """NOVA em M0.5. Inverte a declaracao de borda nos DOIS casos de superficie e exige
    reprovacao no verificador de TOPOLOGIA, nao em outro lugar.

    Antes, a borda era deduzida da representacao: "superficie" exigia borda sempre. Com
    isso, a casca fechada sem solido seria reprovada por ser o que ela tem que ser, e
    inverter a declaracao nao mudaria nada, porque a declaracao nao era lida.

    A terceira parte inverte a borda na varredura da familia, que e outra camada: ali a
    regra falsa vivia no portao de malha do executor."""
    det = {}

    # A. casca ABERTA declarada como borda proibida
    def a():
        c = CASOS.caso10()
        c["id"] = "10b_aberta_declarada_fechada"
        c["topologia"] = dict(c["topologia"], borda="proibida")
        return c

    est_a, det_a = _julga(*_roda(a), reprovar_em=("topologia",))
    det["A_aberta_declarada_proibida"] = {"estado": est_a,
                                          "reprovadas": det_a.get("reprovadas")}
    okA = est_a == PEGOU

    # B. casca FECHADA declarada como borda obrigatoria
    def b():
        c = CASOS.caso11()
        c["id"] = "11b_fechada_declarada_aberta"
        c["topologia"] = dict(c["topologia"], borda="obrigatoria")
        return c

    est_b, det_b = _julga(*_roda(b), reprovar_em=("topologia",))
    det["B_fechada_declarada_obrigatoria"] = {"estado": est_b,
                                              "reprovadas": det_b.get("reprovadas")}
    okB = est_b == PEGOU

    # C. a mesma inversao na VARREDURA da familia, que e outra camada
    def c_():
        c = CASOS.caso10()
        c["id"] = "10c_varredura_com_borda_invertida"
        c["familia"] = dict(c["familia"], borda="proibida")
        return c

    est_c, det_c = _julga(*_roda(c_), reprovar_em=("varredura_de_familia",))
    det["C_varredura_com_borda_invertida"] = {"estado": est_c,
                                              "reprovadas": det_c.get("reprovadas")}
    okC = est_c == PEGOU

    det["nota"] = ("os casos 10 e 11 sem inversao ja aprovam na suite de casos: esse e o "
                   "controle positivo deste par")
    return (PEGOU if (okA and okB and okC) else ESCAPOU), det


def _malha_com_duas_nao_manifold(destino):
    """Cubo fechado com duas abas coladas em duas arestas distintas. MEDIDO: 2 arestas com
    mais de 2 faces, e 4 abertas, que sao as bordas livres das abas."""
    import numpy as np, trimesh
    cubo = trimesh.creation.box(extents=(20, 20, 20))
    V, F = cubo.vertices.copy(), cubo.faces.copy()
    e1, e2 = F[0][:2], F[6][:2]
    i0 = len(V)
    V = np.vstack([V, np.array([[40.0, 0, 0], [0, 40.0, 0]])])
    F = np.vstack([F, [[e1[0], e1[1], i0], [e2[0], e2[1], i0 + 1]]])
    trimesh.Trimesh(vertices=V, faces=F, process=False).export(destino)
    return destino


def _malha_de_dois_cubos_disjuntos(destino):
    """Dois cubos fechados, separados. MEDIDO: 0 arestas abertas, 0 nao-manifold, fechada,
    orientacao consistente, nenhuma faceta degenerada, e 2 componentes conexos. Limpa em
    tudo, MENOS na contagem de componentes. E essa a geometria que permite provar o efeito
    do papel na ENTREGA, porque nenhuma outra verificacao reprova junto."""
    import trimesh
    c1 = trimesh.creation.box(extents=(20, 20, 20))
    c2 = trimesh.creation.box(extents=(20, 20, 20))
    c2.apply_translation([40, 0, 0])
    junto = trimesh.util.concatenate([c1, c2])
    junto.merge_vertices()
    junto.export(destino)
    return destino


def m_papel_da_metrica():
    """NOVA em M0.6. O papel decide se a metrica barra, e NAO altera a medida.

    A versao anterior deste criterio prometia inverter o resultado do CASO ao trocar o
    papel de uma metrica. Isso e falso: a mesma malha com duas arestas nao-manifold
    tambem reprova em outras verificacoes de impressao, entao o caso continuaria reprovado
    por outro motivo e o criterio pareceria falhar por razao errada.

    O que se prova aqui:
      PAR 1 - a decisao DAQUELA metrica muda, e o estado de TODAS as outras verificacoes
              e registrado e tem que ser IDENTICO nas duas execucoes;
      PAR 2 - numa geometria limpa em tudo EXCETO nessa metrica, o papel muda a entrega:
              informativa aprova, decisiva reprova. Este e o par que prova o efeito no
              agregado;
      PAR 3 - medidor ausente por papel: decisiva barra como NAO_IMPLEMENTADA, informativa
              nao barra, e nenhuma das duas inventa medida.
    """
    import copy
    d = CASOS._prep()
    det = {}

    # ---------------------------------------------------------------- PAR 1
    stl_a = _malha_com_duas_nao_manifold(os.path.join(d, "m06_duas_nao_manifold.stl"))
    req_a = CASOS._req(os.path.join(d, "m06_req_a.json"), {
        "peca": stl_a,
        "requisitos": [{"id": "envelope", "tipo": "caixa",
                        "valor": [60.0, 60.0, 20.0], "tol_mm": 40.0}]})

    def caso_a(papel):
        def fn():
            return {"id": "m06_par1_%s" % papel.lower(),
                    "titulo": "duas arestas nao-manifold, metrica em papel %s" % papel,
                    "classificacao": {"modalidade": "criar", "representacao": "malha",
                                      "finalidade": "impressao_fdm"},
                    "papeis": {"zero_nao_manifold": papel},
                    "malha": stl_a, "step": None, "requisitos": req_a, "referencia": None,
                    "geometria_nao_vazia": {"ok": True},
                    "declaracoes": {"encaixe_declarado": False},
                    "espera": {"exige": ["zero_nao_manifold"], "nao_exige": [],
                               "resultado": "reprovado"}}
        return fn

    r_dec, e1 = _roda(caso_a("DECISIVA"))
    r_inf, e2 = _roda(caso_a("INFORMATIVA"))
    if e1 or e2:
        return INVALIDO, {"erro_de_execucao": e1 or e2}

    METRICA = "zero_nao_manifold"

    def medida(r):
        alvo = (r.get("verificacoes") or {}).get(METRICA) or {}
        return (alvo.get("detalhe") or {}).get("arestas_com_mais_de_2_faces")

    def estados_dos_outros(r):
        return {n: v["estado"] for n, v in (r.get("verificacoes") or {}).items()
                if n != METRICA}

    outros_dec, outros_inf = estados_dos_outros(r_dec), estados_dos_outros(r_inf)
    inform = r_inf.get("informativas") or {}
    det["par1"] = {
        "medida_em_decisiva": medida(r_dec),
        "medida_em_informativa": medida(r_inf),
        "metrica_em_reprovadas_decisiva": METRICA in (r_dec.get("reprovadas") or []),
        "metrica_em_reprovadas_informativa": METRICA in (r_inf.get("reprovadas") or []),
        "metrica_em_informativas": METRICA in inform,
        "estado_em_informativa": (inform.get(METRICA) or {}).get("estado"),
        "estados_dos_outros_identicos": outros_dec == outros_inf,
        "divergencias_nos_outros": {n: (outros_dec.get(n), outros_inf.get(n))
                                    for n in set(outros_dec) | set(outros_inf)
                                    if outros_dec.get(n) != outros_inf.get(n)},
        "exigidas_identicas": (r_dec.get("roteamento") or {}).get("exigidas")
                              == (r_inf.get("roteamento") or {}).get("exigidas")}
    ok1 = (medida(r_dec) == 2 and medida(r_inf) == 2
           and det["par1"]["metrica_em_reprovadas_decisiva"]
           and not det["par1"]["metrica_em_reprovadas_informativa"]
           and det["par1"]["metrica_em_informativas"]
           and det["par1"]["estado_em_informativa"] == "REPROVADA"
           and det["par1"]["estados_dos_outros_identicos"]
           and det["par1"]["exigidas_identicas"])

    # ---------------------------------------------------------------- PAR 2
    stl_b = _malha_de_dois_cubos_disjuntos(os.path.join(d, "m06_dois_cubos.stl"))
    req_b = CASOS._req(os.path.join(d, "m06_req_b.json"), {
        "peca": stl_b,
        "requisitos": [{"id": "envelope", "tipo": "caixa",
                        "valor": [60.0, 20.0, 20.0], "tol_mm": 0.5}]})
    TOPO = {"borda": "proibida", "orientacao": "exigida", "componentes": 1,
            "estanqueidade": "exigida"}

    def caso_b(papel):
        def fn():
            return {"id": "m06_par2_%s" % papel.lower(),
                    "titulo": "limpa em tudo menos na contagem de componentes",
                    "classificacao": {"modalidade": "criar", "representacao": "malha",
                                      "finalidade": "intercambio"},
                    "topologia": TOPO, "papeis": {"topologia": papel},
                    "malha": stl_b, "step": None, "requisitos": req_b, "referencia": None,
                    "geometria_nao_vazia": {"ok": True},
                    "declaracoes": {"encaixe_declarado": False},
                    "espera": {"exige": ["topologia"], "nao_exige": [],
                               "resultado": ("aprovado" if papel == "INFORMATIVA"
                                             else {"barrado_em": ["topologia"]})}}
        return fn

    rb_dec, e3 = _roda(caso_b("DECISIVA"))
    rb_inf, e4 = _roda(caso_b("INFORMATIVA"))
    if e3 or e4:
        return INVALIDO, {"erro_de_execucao": e3 or e4}

    det["par2"] = {
        "resultado_decisiva": rb_dec.get("resultado_obtido"),
        "resultado_informativa": rb_inf.get("resultado_obtido"),
        "reprovadas_decisiva": rb_dec.get("reprovadas"),
        "reprovadas_informativa": rb_inf.get("reprovadas"),
        "topologia_em_informativas": "topologia" in (rb_inf.get("informativas") or {}),
        "outras_verificacoes_decisiva": {n: v["estado"] for n, v
                                         in (rb_dec.get("verificacoes") or {}).items()},
        "passou_decisiva": rb_dec.get("PASSOU"),
        "passou_informativa": rb_inf.get("PASSOU")}
    ok2 = (rb_dec.get("reprovadas") == ["topologia"]
           and rb_inf.get("reprovadas") == []
           and det["par2"]["topologia_em_informativas"]
           and rb_inf.get("resultado_obtido") == "aprovado"
           and rb_dec.get("resultado_obtido") == "barrado_em ['topologia']"
           and rb_dec.get("resultado_ok") is True
           and rb_inf.get("resultado_ok") is True)

    # ---------------------------------------------------------------- PAR 3
    guardado = roda_casos.VERIFICADORES.pop("topologia")
    try:
        rc_dec, e5 = _roda(caso_b("DECISIVA"))
        rc_inf, e6 = _roda(caso_b("INFORMATIVA"))
    finally:
        roda_casos.VERIFICADORES["topologia"] = guardado
    if e5 or e6:
        return INVALIDO, {"erro_de_execucao": e5 or e6}

    def estado_de(r, nome):
        return ((r.get("verificacoes") or {}).get(nome) or {}).get("estado")

    def detalhe_de(r, nome):
        return ((r.get("verificacoes") or {}).get(nome) or {}).get("detalhe") or {}

    det["par3"] = {
        "estado_decisiva": estado_de(rc_dec, "topologia"),
        "estado_informativa": estado_de(rc_inf, "topologia"),
        "barra_em_decisiva": "topologia" in (rc_dec.get("bloqueios") or []),
        "barra_em_informativa": "topologia" in (rc_inf.get("bloqueios") or []),
        "sem_medida_em_decisiva": "medido" not in detalhe_de(rc_dec, "topologia"),
        "sem_medida_em_informativa": "medido" not in detalhe_de(rc_inf, "topologia")}
    ok3 = (det["par3"]["estado_decisiva"] == "NAO_IMPLEMENTADA"
           and det["par3"]["estado_informativa"] == "NAO_IMPLEMENTADA"
           and det["par3"]["barra_em_decisiva"]
           and not det["par3"]["barra_em_informativa"]
           and det["par3"]["sem_medida_em_decisiva"]
           and det["par3"]["sem_medida_em_informativa"])

    det["nota"] = ("sem o par 2 o efeito do papel na entrega nao estaria demonstrado, e "
                   "sem o par 1 a igualdade das outras verificacoes nao estaria controlada")
    return (PEGOU if (ok1 and ok2 and ok3) else ESCAPOU), det


MUTACOES = [
    ("finalidade visualizacao exige fatiador", m_finalidade_exige_fatiador),
    ("superficie para impressao perde a dispensa", m_representacao_perde_dispensa),
    ("impressao deixa de exigir o fatiador", m_impressao_dispensa_fatiador),
    ("verificador obrigatorio ausente do registro", m_verificador_obrigatorio_ausente),
    ("caixa declarada com 2 mm de erro", m_caixa_com_erro_de_cota),
    ("furo central declarado 3 mm fora", m_furo_no_lugar_errado),
    ("abertura quadrada com a mesma area do furo", m_abertura_nao_circular),
    ("reconstrucao alinhada por eixo, geometria mudada", m_datum_perdido_de_verdade),
    ("regiao editada declarada como intacta", m_regiao_editada_declarada_intacta),
    ("intercambio da montagem com um componente so", m_intercambio_com_um_componente),
    ("particao deslocada que estoura o envelope", m_particao_que_estoura),
    # acrescentadas depois da terceira revisao externa
    ("verificador devolve estado fora do contrato", m_estado_fora_do_contrato),
    ("requisito de preservacao com id neutro", m_id_neutro_no_requisito),
    ("caso sem nenhum requisito de preservacao", m_sem_requisito_de_preservacao),
    ("reconstrucao com a inclinacao invertida", m_inclinacao_invertida),
    ("destino de pacote previamente contaminado", m_destino_contaminado),
    ("perfil de maquina sem envelope", m_perfil_sem_envelope),
    ("medicao de folga sem estado explicito", m_registro_sem_estado_explicito),
    ("grade com variante geometricamente invalida", m_variante_geometricamente_invalida),
    # acrescentadas depois da quarta revisao externa
    ("varredura reaproveitando execucao anterior", m_varredura_de_execucao_anterior),
    ("erro operacional em variante da varredura", m_erro_operacional_na_varredura),
    ("relatorio gravado dentro do destino", m_relatorio_dentro_do_destino),
    ("perfil com envelope de valor invalido", m_envelope_com_valor_invalido),
    ("dois requisitos com o mesmo identificador", m_ids_duplicados),
    # acrescentada em M0.1
    ("identidade fisica de caminho, com controle positivo", m_identidade_de_caminho),
    # acrescentada em M0.2
    ("escrita do formato fechado, com controle positivo", m_escrita_do_formato_fechado),
    # acrescentada em M0.3
    ("causa divergente no mesmo verificador", m_causa_divergente_no_mesmo_verificador),
    # acrescentada em M0.4
    ("area da mesa degenerada e autointersectante", m_area_da_mesa_degenerada),
    # acrescentada em M0.5
    ("borda declarada ao contrario nos dois sentidos", m_borda_declarada_ao_contrario),
    # acrescentada em M0.6
    ("papel da metrica em tres pares", m_papel_da_metrica),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(AQUI, "mutacoes_resultado.json"))
    a = ap.parse_args()
    linhas = []
    for nome, fn in MUTACOES:
        try:
            estado, det = fn()
        except Exception as e:
            estado, det = INVALIDO, {"erro_de_execucao": "%s: %s" % (type(e).__name__, e),
                                     "trace": traceback.format_exc()[-500:]}
        linhas.append({"mutacao": nome, "estado": estado, "detalhe": det})
        print("%-9s %s" % (estado, nome))
        if estado != PEGOU:
            print("          ", str(det)[:240])
    n_pegou = sum(1 for l in linhas if l["estado"] == PEGOU)
    n_escapou = sum(1 for l in linhas if l["estado"] == ESCAPOU)
    n_invalido = sum(1 for l in linhas if l["estado"] == INVALIDO)
    print()
    print("%d pegas, %d escaparam, %d invalidas, de %d."
          % (n_pegou, n_escapou, n_invalido, len(linhas)))
    if n_escapou:
        print("Mutacao que escapa significa teste decorativo. Conserte o teste, nao a mutacao.")
    if n_invalido:
        print("Mutacao invalida NAO conta como deteccao: o experimento nao mediu nada.")
    json.dump({"n": len(linhas), "pegou": n_pegou, "escapou": n_escapou,
               "invalido": n_invalido, "mutacoes": linhas,
               "nota": ("PEGOU exige reprovacao no verificador que a mutacao previu. Erro de "
                        "execucao vira INVALIDO em vez de credito.")},
              open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return 0 if (n_escapou == 0 and n_invalido == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
