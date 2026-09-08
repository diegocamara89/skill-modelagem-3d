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
    inesperados = [n for n in r["erros"] if n not in errar_em]
    if inesperados:
        det["erros_inesperados"] = inesperados
        return INVALIDO, det
    if r["PASSOU"]:
        return ESCAPOU, det
    faltou = []
    for n in reprovar_em:
        if n not in r["reprovadas"]:
            faltou.append("esperava reprovacao em %s" % n)
    for n in bloquear_em:
        if n not in r["bloqueios"]:
            faltou.append("esperava bloqueio em %s" % n)
    for n in errar_em:
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

    r, e = _roda(mutado)
    if e:
        return INVALIDO, {"erro_de_execucao": e}
    est = r["verificacoes"]["varredura_de_familia"]["estado"]
    det = {"estado": est, "passou": r["PASSOU"],
           "detalhe": str(r["verificacoes"]["varredura_de_familia"]["detalhe"])[:220]}
    ok = est == "ERRO" and not r["PASSOU"]
    return (PEGOU if ok else ESCAPOU), det


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
        ok = (r.returncode != 0
              and "DENTRO do destino" in ((r.stderr or "") + (r.stdout or ""))
              and not det["arquivos_no_destino"])
    with tempfile.TemporaryDirectory(prefix="skill3d_rel2_") as raiz2:
        dest2 = os.path.join(raiz2, "pacote")
        rel2 = os.path.join(raiz2, "matriz.py")
        r2 = subprocess.run([sys.executable, os.path.join(AQUI, "empacota.py"),
                             "--destino", dest2, "--json", rel2],
                            capture_output=True, text=True, timeout=300)
        det["colisao_de_nome_codigo_de_saida"] = r2.returncode
        det["colisao_de_nome_mensagem"] = (r2.stderr or "")[-140:]
        ok = ok and r2.returncode != 0
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
