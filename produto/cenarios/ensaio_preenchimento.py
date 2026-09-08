# -*- coding: utf-8 -*-
"""ensaio_preenchimento.py - ensaio completo da receita de preenchimento local.

RODA DENTRO DO BLENDER, sobre o cenario sintetico do gera_cenario.py:
  blender --background --factory-startup --python ensaio_preenchimento.py -- <param.json>

param.json:
  {"cenario": <param do gera_cenario>, "variante": "correta"|"ranhura"|"tangente",
   "saida": <relatorio>, "destino_blend": <opcional>, "destino_stl": <opcional>}

TRES VARIANTES, cada defeito plantado atingindo o verificador que ele testa:

  correta   - sobreposicao positiva e topo nos limites acordados. Perfil e regiao
              protegida dentro da tolerancia; degeneracao zerada pela limpeza local.
  ranhura   - o topo da rampa comeca ABAIXO dos limites acordados. A malha continua
              FECHADA e a topologia continua limpa: quem tem que reprovar e a
              medida de PERFIL, e nenhuma outra.
  tangente  - sobreposicao zero, o volume apenas encosta. Quem tem que barrar e a
              PRE-CONDICAO do preenchimento, antes de qualquer uniao.
  parcial   - o limite b colocado ALEM da peca em x. As duas outras zonas
              interceptam e essa NAO. Discrimina o caso parcial, que um escalar
              unico de volume nao separa do caso completo.
  flutuante - limites com z ACIMA da peca, que e o que acontece quando o agente
              calcula os limites em coordenada local e os usa como se fossem de
              mundo. Os parametros passam em TODAS as pre-condicoes, a uniao conclui,
              e o volume nao toca o material. Quem acusa e a MEDIDA DE INTERSECCAO.
  duplicado - o MESMO preenchimento aplicado DUAS vezes, que e o que acontece quando
              um agente repete a operacao depois de um tempo esgotado sem saber se
              ela concluiu. Exercita a contagem de DEGENERACAO e a limpeza local,
              independentemente de ranhura: a forma final e a mesma e a topologia
              piora.

Uma falha em requisito diferente do pretendido nao da credito ao detector.
"""
import json
import os
import sys

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "scripts"))
sys.path.insert(0, AQUI)

import bl_ferramentas as F          # noqa: E402
import gera_cenario as G            # noqa: E402


def passo(rel, nome, fn, esperado=None):
    """Executa e REGISTRA. Note que `estado` aqui diz apenas se houve excecao.

    CORRIGIDO depois da revisao final, que apontou o defeito: a versao anterior
    tinha so isto, e `esperado` era TEXTO. Com isso, um passo que mediu
    `todos_dentro_da_tolerancia: false` saia como "OK", e o resumo dizia "so os
    controles barrando" sobre um resultado geometricamente errado. Quem julga agora
    e `julga()`, com predicado EXECUTAVEL, e o relatorio traz veredito global."""
    try:
        r = fn()
        rel["passos"].append({"passo": nome, "estado": "OK", "resultado": r,
                              "esperado": esperado})
        return r
    except F.ErroDePrecondicao as e:
        rel["passos"].append({"passo": nome, "estado": "PRECONDICAO",
                              "mensagem": str(e), "esperado": esperado})
        return None
    except Exception as e:
        rel["passos"].append({"passo": nome, "estado": "ERRO", "esperado": esperado,
                              "mensagem": "%s: %s" % (type(e).__name__, e)})
        return None


def resultado_de(rel, nome):
    for q in rel["passos"]:
        if q["passo"] == nome:
            return q
    return None


def julga(rel, criterio, predicado, descricao):
    """Um criterio, um predicado executavel, um veredito. Excecao no predicado e
    INDETERMINADO, nunca aprovacao."""
    try:
        ok = bool(predicado())
        rel["vereditos"].append({"criterio": criterio, "descricao": descricao,
                                 "veredito": "ATENDIDO" if ok else "FALHOU"})
    except Exception as e:
        rel["vereditos"].append({"criterio": criterio, "descricao": descricao,
                                 "veredito": "INDETERMINADO",
                                 "erro": "%s: %s" % (type(e).__name__, e)})


def fecha(rel, saida, barram_de_proposito=()):
    """Veredito global.

    CORRIGIDO depois da terceira revisao, que apontou o furo: a versao anterior
    olhava so os criterios julgados, e IGNORAVA passos com estado ERRO ou
    PRECONDICAO que nenhum predicado cobria — `salva_cena` e `exporta_malha`, por
    exemplo. Um ensaio podia sair ATENDIDO com uma entrega que falhou.

    Agora: qualquer ERRO reprova, sempre; e PRECONDICAO reprova a menos que aquele
    passo esteja na lista dos que barram de proposito. `barram_de_proposito` e
    explicita, para que barrar nunca seja aceito por omissao."""
    rel["resumo"] = {q["passo"]: q["estado"] for q in rel["passos"]}
    esperados = set(barram_de_proposito)
    inesperados = []
    for q in rel["passos"]:
        if q["estado"] == "ERRO":
            inesperados.append({"passo": q["passo"], "estado": "ERRO",
                                "mensagem": (q.get("mensagem") or "")[:200]})
        elif q["estado"] == "PRECONDICAO" and q["passo"] not in esperados:
            inesperados.append({"passo": q["passo"], "estado": "PRECONDICAO",
                                "mensagem": (q.get("mensagem") or "")[:200]})
    rel["passos_com_estado_inesperado"] = inesperados
    rel["passos_que_barram_de_proposito"] = sorted(esperados)

    falhos = [v for v in rel["vereditos"] if v["veredito"] != "ATENDIDO"]
    rel["n_criterios"] = len(rel["vereditos"])
    rel["n_falhos"] = len(falhos)
    rel["criterios_falhos"] = falhos
    if not rel["vereditos"]:
        rel["veredito_global"] = "SEM_CRITERIO"
        rel["aviso"] = ("nenhum criterio foi julgado: contagem de passos OK nao e "
                        "veredito")
    elif falhos or inesperados:
        rel["veredito_global"] = "FALHOU"
    else:
        rel["veredito_global"] = "ATENDIDO"
    _grava(saida, rel)


VARIANTES = ("correta", "ranhura", "tangente", "duplicado", "flutuante", "parcial")

# Passos que barram DE PROPOSITO em todo ensaio. A lista e explicita para que
# "barrou" nunca seja aceito por omissao: fecha() reprova PRECONDICAO fora dela.
BARRAM = ("controle_negativo_caixa_vazia",
          "controle_negativo_deslocar_selecao_vazia")


def destino_do_resultado(argv, do_arquivo=None):
    """Caminho onde este script tem que gravar o relatorio.

    Le a bandeira NOMEADA `--resultado-em`, que `roda_blender.py --passa-resultado`
    acrescenta. Nomeada de proposito: a versao anterior lia `argv[1]`, e com dois
    argumentos do chamador o script gravava sobre o segundo argumento dele."""
    if ROTULO_DO_RESULTADO in argv:
        i = argv.index(ROTULO_DO_RESULTADO)
        if i + 1 < len(argv) and argv[i + 1]:
            return argv[i + 1]
    return do_arquivo


ROTULO_DO_RESULTADO = "--resultado-em"


def perfil_esperado(vao, alto, baixo, xs, ys):
    """O perfil que os limites ACORDADOS implicam. Sai da combinacao com o usuario,
    nao do que foi construido: e por isso que ele detecta a rampa baixa demais."""
    x1, x2 = vao["x_de"], vao["x_ate"]
    za, zb = alto["z"], baixo["z"]
    pontos = []
    for y in ys:
        for x in xs:
            if x <= x1:
                z = za
            elif x >= x2:
                z = zb
            else:
                z = za + (zb - za) * (x - x1) / (x2 - x1)
            pontos.append([x, y, z])
    return pontos


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cfg = (json.load(open(argv[0], encoding="utf-8"))
           if argv and not argv[0].startswith("--") else {})
    variante = cfg.get("variante", "correta")
    # A bandeira `--resultado-em` MANDA no destino, pelo mesmo motivo do gerador:
    # assim o caminho e escrito num lugar so.
    saida = destino_do_resultado(argv, cfg.get("saida"))
    if not saida:
        raise SystemExit("informe o destino do relatorio: 'saida' no arquivo de "
                         "configuracao, ou o ultimo argumento (--passa-resultado)")
    # CORRIGIDO depois da terceira revisao: nao havia validacao do nome, e qualquer
    # erro de digitacao caia pelo caminho de "correta" e podia terminar ATENDIDO com
    # o nome invalido preservado no relatorio. Vocabulario fechado, recusado cedo.
    if variante not in VARIANTES:
        # A recusa e GRAVADA, nao so levantada. Medido: com o lancador do Blender
        # desanexado, um SystemExit nao deixa vestigio nenhum no chamador — stdout
        # vem vazio e o codigo de saida e 0. Sem arquivo, "nome invalido" fica
        # indistinguivel de "quebrou calado", que e exatamente a confusao que este
        # produto existe para evitar.
        _grava(saida, {
            "veredito_global": "ESPEC_INVALIDA",
            "variante_pedida": variante,
            "variantes_validas": sorted(VARIANTES),
            "motivo": ("variante %r nao existe. O vocabulario e fechado: um erro de "
                       "digitacao nao pode cair no caminho da variante 'correta' e "
                       "terminar ATENDIDO com o nome invalido no relatorio."
                       % variante),
            "passos": [], "vereditos": [], "n_criterios": 0, "n_falhos": 0})
        raise SystemExit(2)

    p = dict(G.PADRAO)
    p.update(cfg.get("cenario") or {})
    p["saida_blend"] = None
    p["saida_relatorio"] = None
    obj, gab = G.gera(p)
    nome = obj.name

    rel = {"variante": variante, "gabarito": gab, "passos": [], "vereditos": [],
           "versao_blender": bpy.app.version_string,
           "versao_ferramentas": F.VERSAO}
    vao = gab["vao"]
    alto, baixo = gab["topo_do_patamar_alto"], gab["topo_do_patamar_baixo"]
    W = vao["largura_em_y"]

    # a sobreposicao sai da GEOMETRIA: um vigesimo do vao. Nao e constante universal,
    # e a regiao protegida e definida DESCONTANDO ela, porque a sobreposicao entra no
    # material de proposito.
    ov = round(vao["comprimento_do_vao"] / 20.0, 6)
    # CORRIGIDO depois da revisao final. A versao anterior desta string dizia "sem
    # alcancar a regiao declarada como protegida", que e geometricamente IMPOSSIVEL:
    # qualquer sobreposicao positiva alcanca a regiao em planta, e e assim que ela
    # intercepta o material. Como este campo e de PROCEDENCIA e fica gravado na
    # evidencia, a frase anterior gravava justificativa falsa no registro. O criterio
    # correto e sobre ALTURA.
    origem_ov = ("um vigesimo do comprimento do vao (%s unidades). Em planta ela "
                 "ALCANCA a regiao protegida e a retessela, o que e esperado e e como "
                 "ela intercepta material; em ALTURA o topo da sobreposicao e "
                 "horizontal na altura de cada limite, portanto nao ultrapassa a "
                 "superficie protegida. O que se verifica e a altura."
                 % vao["comprimento_do_vao"])
    tol = 0.01
    rel["parametros_derivados"] = {"sobreposicao": ov, "origem": origem_ov,
                                   "tolerancia_de_perfil": tol}

    # ---------------------------------------------------------------- diagnostico
    passo(rel, "diagnostico", lambda: F.diagnostico(nome))

    # -------------------------------------------- selecao por criterio de MUNDO
    passo(rel, "entra_em_edicao", lambda: F.entra_em_edicao(nome, "face"))
    caixa_topo_min = [alto["x_de"] - 0.001, -0.001, alto["z"] - 0.001]
    caixa_topo_max = [alto["x_ate"] + 0.001, W + 0.001, alto["z"] + 0.001]
    passo(rel, "seleciona_topo_do_patamar_alto",
          lambda: F.seleciona_faces_por_caixa_de_mundo(nome, caixa_topo_min,
                                                       caixa_topo_max),
          esperado="1 face, contada na propria bmesh depois de marcar")
    passo(rel, "le_selecao", lambda: F.le_selecao(nome))

    # Assinatura imediatamente ANTES dos dois controles negativos, para poder
    # provar que barrar nao mexeu na peca. Nao da para usar a assinatura de mais
    # adiante: ela e capturada depois do deslocamento de controle, e nao estaria
    # ligada em tempo de execucao aqui (foi o erro que fez os oito ensaios
    # falharem com NameError na primeira tentativa desta correcao).
    a_pre_controles = F.assinatura(nome)

    # --------- CONTROLE NEGATIVO 1: caixa sem nenhuma face tem que ser BARRADA
    passo(rel, "controle_negativo_caixa_vazia",
          lambda: F.seleciona_faces_por_caixa_de_mundo(
              nome, [1000.0, 1000.0, 1000.0], [1001.0, 1001.0, 1001.0]),
          esperado="PRECONDICAO")

    # --------- CONTROLE NEGATIVO 2: deslocar sem selecao tem que ser BARRADO
    passo(rel, "limpa_selecao", lambda: F.limpa_selecao(nome))
    passo(rel, "controle_negativo_deslocar_selecao_vazia",
          lambda: F.desloca_selecao(nome, [0, 0, 5.0]),
          esperado="PRECONDICAO")

    # --------- CONTROLE POSITIVO do deslocamento, com distancia CONHECIDA
    passo(rel, "reseleciona_topo",
          lambda: F.seleciona_faces_por_caixa_de_mundo(nome, caixa_topo_min,
                                                       caixa_topo_max))
    # A regiao NAO selecionada tem que ficar intacta durante o deslocamento.
    # CORRIGIDO duas vezes. Primeiro porque a versao original media so a dimensao
    # externa, e metade do criterio ficava sem evidencia — apontado pela revisao
    # final. Depois porque a MINHA primeira correcao reselecionava pela caixa da
    # altura ORIGINAL: depois de subir 2, aquela caixa nao encontra face nenhuma, a
    # selecao fica vazia, o deslocamento de volta e barrado, e a peca segue 2
    # unidades mais alta pelo resto do ensaio. O ensaio julgador pegou isso na
    # primeira execucao, com "perfil" e "superficie protegida" reprovando.
    #
    # A regiao medida e o topo do patamar BAIXO, que nao esta na selecao. As medidas
    # sao em Object Mode, porque mede_topo_em_pontos le obj.data.
    girado = abs(gab.get("rotacao_z_graus") or 0.0) > 1e-9
    pontos_baixo = [[x, y, baixo["z"]]
                    for y in (W * 0.25, W * 0.5, W * 0.75)
                    for x in _linspace(baixo["x_de"] + 1.0, baixo["x_ate"] - 1.0, 5)]
    passo(rel, "sai_de_edicao_para_medir", F.sai_de_edicao)
    passo(rel, "patamar_baixo_antes_do_deslocamento",
          lambda: F.mede_topo_em_pontos(nome, pontos_baixo, tolerancia=tol))

    def caixa_do_topo(z):
        return ([alto["x_de"] - 0.001, -0.001, z - 0.001],
                [alto["x_ate"] + 0.001, W + 0.001, z + 0.001])

    passo(rel, "volta_para_edicao", lambda: F.entra_em_edicao(nome, "face"))
    passo(rel, "reseleciona_topo_para_subir",
          lambda: F.seleciona_faces_por_caixa_de_mundo(nome, *caixa_do_topo(alto["z"])))
    passo(rel, "controle_positivo_deslocamento",
          lambda: F.desloca_selecao(nome, [0, 0, 2.0]),
          esperado="geometria_mudou verdadeiro; assinatura lida da malha VIVA")
    passo(rel, "confere_altura_apos_deslocamento",
          lambda: F.diagnostico(nome),
          esperado="dimensions_mundo z = altura_alta + 2")
    passo(rel, "sai_de_edicao_apos_deslocar", F.sai_de_edicao)
    passo(rel, "patamar_baixo_depois_do_deslocamento",
          lambda: F.mede_topo_em_pontos(nome, pontos_baixo, tolerancia=tol),
          esperado="identico ao de antes: a regiao nao selecionada nao se move")
    # a caixa de volta usa a altura ATUAL, que e a original mais 2
    passo(rel, "volta_para_edicao_2", lambda: F.entra_em_edicao(nome, "face"))
    passo(rel, "reseleciona_topo_para_descer",
          lambda: F.seleciona_faces_por_caixa_de_mundo(
              nome, *caixa_do_topo(alto["z"] + 2.0)))
    passo(rel, "devolve_o_deslocamento", lambda: F.desloca_selecao(nome, [0, 0, -2.0]))
    passo(rel, "sai_de_edicao", F.sai_de_edicao)
    passo(rel, "confere_altura_restaurada", lambda: F.diagnostico(nome),
          esperado="dimensions_mundo z de volta a altura_alta")

    # ---- vereditos do deslocamento, com predicado executavel.
    #      Na variante GIRADA a expectativa e outra: a selecao por caixa de mundo tem
    #      que BARRAR, porque a peca nao esta alinhada aos eixos. Julgar o mesmo
    #      criterio nas duas seria cobrar de uma o que so vale para a outra.
    if girado:
        julga(rel, "girada_barra_a_selecao_por_caixa_de_mundo",
              lambda: resultado_de(rel, "seleciona_topo_do_patamar_alto")["estado"]
                      == "PRECONDICAO",
              "com o objeto girado, a caixa alinhada aos eixos nao encontra a face "
              "e a funcao barra em vez de selecionar o conjunto errado")
    else:
        julga(rel, "selecao_por_mundo_encontra_o_topo",
              lambda: (resultado_de(rel, "seleciona_topo_do_patamar_alto")["resultado"]
                       ["faces_marcadas"] >= 1),
              "a caixa de mundo do topo do patamar alto seleciona pelo menos uma face")
        julga(rel, "deslocamento_tem_efeito_medido",
              lambda: (resultado_de(rel, "controle_positivo_deslocamento")["resultado"]
                       ["geometria_mudou"] is True),
              "com selecao valida, a assinatura muda")
        julga(rel, "altura_externa_confere_com_o_pedido",
              lambda: abs(resultado_de(rel, "confere_altura_apos_deslocamento")
                          ["resultado"]["objeto"]["dimensions_mundo"][2]
                          - (alto["z"] + 2.0)) <= tol,
              "subir 2 leva a altura externa para altura_alta + 2")
        julga(rel, "altura_restaurada_apos_desfazer_o_deslocamento",
              lambda: abs(resultado_de(rel, "confere_altura_restaurada")
                          ["resultado"]["objeto"]["dimensions_mundo"][2]
                          - alto["z"]) <= tol,
              "descer 2 devolve a altura externa ao valor original")
        julga(rel, "regiao_nao_selecionada_nao_se_move",
              lambda: (resultado_de(rel, "patamar_baixo_antes_do_deslocamento")
                       ["resultado"]["todos_dentro_da_tolerancia"] is True
                       and resultado_de(rel, "patamar_baixo_depois_do_deslocamento")
                       ["resultado"]["todos_dentro_da_tolerancia"] is True),
              "o topo do patamar baixo, fora da selecao, mede o mesmo antes e depois")

    # CORRIGIDO depois da QUARTA revisao: estes dois controles conferiam SO o estado.
    # A propria referencia deste pacote conta o episodio em que um ensaio independente
    # rodou o controle da caixa vazia em Object Mode: ele barrou, com "a selecao de
    # faces exige Edit Mode", e passou SEM ter exercitado a guarda de selecao vazia.
    # Credito por defeito nao exercitado e o erro que estes controles existem para
    # evitar, e o proprio controle caiu nele. Agora a MENSAGEM decide, e a geometria
    # tem que continuar intacta.
    julga(rel, "caixa_vazia_barra",
          lambda: resultado_de(rel, "controle_negativo_caixa_vazia")["estado"]
                  == "PRECONDICAO",
          "caixa sem nenhuma face levanta ErroDePrecondicao")
    julga(rel, "caixa_vazia_barra_PELO_MOTIVO_certo",
          lambda: "nao contem nenhuma face" in (
              resultado_de(rel, "controle_negativo_caixa_vazia").get("mensagem") or ""),
          "a mensagem diz que a caixa nao contem nenhuma face, e nao outro "
          "impedimento qualquer, como estar fora de Edit Mode")
    julga(rel, "selecao_vazia_barra_a_edicao",
          lambda: resultado_de(rel, "controle_negativo_deslocar_selecao_vazia")
                  ["estado"] == "PRECONDICAO",
          "deslocar sem selecao levanta ErroDePrecondicao")
    julga(rel, "selecao_vazia_barra_PELO_MOTIVO_certo",
          lambda: "nenhum vertice selecionado" in (
              resultado_de(rel, "controle_negativo_deslocar_selecao_vazia")
              .get("mensagem") or ""),
          "a mensagem diz que nao ha vertice selecionado, e nao que falta Edit Mode")
    julga(rel, "os_dois_controles_nao_alteraram_a_peca",
          lambda: F.assinatura(nome)["sha256"] == a_pre_controles["sha256"],
          "depois dos dois controles negativos, a assinatura e a mesma de antes: "
          "barrar nao pode ter mexido na peca")

    # --------- assinatura e ponto de recuperacao antes de alterar
    a_antes = F.assinatura(nome)
    rel["assinatura_antes_da_uniao"] = a_antes["sha256"]
    passo(rel, "marca_recuperacao",
          lambda: F.marca_recuperacao("antes do preenchimento"))

    # --------- superficie protegida MEDIDA antes, por amostragem de altura
    #  Por que amostragem e nao conjunto de posicoes: a uniao RETESSELA a regiao, e
    #  comparar conjunto de vertices acusaria diferenca de tesselacao como se fosse
    #  alteracao da superficie. A referencia manda separar as duas coisas.
    xs_prot = [round(x, 4) for x in _linspace(1.0, alto["x_ate"] - ov - 1.0, 6)]
    ys_prot = [round(W * f, 4) for f in (0.2, 0.5, 0.8)]
    pontos_prot = [[x, y, alto["z"]] for y in ys_prot for x in xs_prot]
    passo(rel, "superficie_protegida_antes",
          lambda: F.mede_topo_em_pontos(nome, pontos_prot, tolerancia=tol),
          esperado="todos em z=%s" % alto["z"])

    # ---------------------------------------------------------------- preenchimento
    z_alto, z_baixo = alto["z"], baixo["z"]
    z_base_usada = vao["z_do_piso"]
    x_b_usado = vao["x_ate"]
    if variante == "ranhura":
        z_alto, z_baixo = alto["z"] - 0.5, baixo["z"] - 0.5
    elif variante == "parcial":
        # x do limite b alem do fim da peca: a zona daquele extremo fica no vazio,
        # e as outras duas continuam com material
        x_b_usado = gab["topo_do_patamar_baixo"]["x_ate"] + 1.0 + ov
    elif variante == "flutuante":
        # limites e base ACIMA do topo da peca: o prisma inteiro fica no ar
        z_alto = alto["z"] + 10.0
        z_baixo = baixo["z"] + 16.0
        z_base_usada = alto["z"] + 5.0
    ov_usada = 0.0 if variante == "tangente" else ov

    feito = passo(
        rel, "preenche_entre_limites",
        lambda: F.preenche_entre_limites(
            nome, limite_a={"x": vao["x_de"], "z": z_alto},
            limite_b={"x": x_b_usado, "z": z_baixo},
            y_de=0.0, y_ate=W, z_da_base=z_base_usada,
            sobreposicao=ov_usada, origem_da_sobreposicao=origem_ov),
        esperado=("PRECONDICAO na tangente; na flutuante a uniao conclui e "
                  "houve_interseccao tem que ser falso; uniao normal nas outras"))

    # a repeticao do MESMO preenchimento: acontece quando o agente repete a operacao
    # depois de um tempo esgotado sem inspecionar se ela concluiu
    if variante == "duplicado" and feito is not None:
        passo(rel, "preenche_segunda_vez",
              lambda: F.preenche_entre_limites(
                  nome, limite_a={"x": vao["x_de"], "z": z_alto},
                  limite_b={"x": vao["x_ate"], "z": z_baixo},
                  y_de=0.0, y_ate=W, z_da_base=vao["z_do_piso"],
                  sobreposicao=ov_usada, origem_da_sobreposicao=origem_ov),
              esperado="conclui, e a topologia piora sem a forma mudar")

    if feito is None:
        # CORRIGIDO depois da terceira revisao: exigir apenas "algum PRECONDICAO"
        # aceita a barra pelo motivo ERRADO, que e exatamente o defeito que este
        # produto ensina a evitar e que ja aconteceu com a caixa vazia. Agora cada
        # variante tem o SEU motivo, conferido no texto da mensagem.
        motivo_por_variante = {
            "tangente": "sobreposicao tem que ser positiva",
            "flutuante": "nao encontraria material em",
            "parcial": "extremo_do_limite_b",
        }
        motivo = motivo_por_variante.get(
            variante, "prisma alinhado aos eixos" if girado else None)
        # CORRIGIDO depois da QUARTA revisao, e o defeito era da propria correcao
        # anterior: este ramo tratava `feito is None` como caminho BEM-SUCEDIDO para
        # qualquer variante. Em `correta`, `ranhura` e `duplicado` nao existe motivo
        # previsto para barrar, e `motivo` ficava None — de modo que uma booleana que
        # devolvesse CANCELLED viraria ErroDePrecondicao, entraria aqui, e o ensaio
        # poderia terminar ATENDIDO por ter "barrado corretamente" algo que tinha que
        # ter sido executado. Barrar so e resposta certa onde ha motivo previsto.
        if motivo is None:
            julga(rel, "preenchimento_NAO_devia_barrar_nesta_variante",
                  lambda: False,
                  "a variante %r esta DENTRO do dominio e o preenchimento tinha que "
                  "executar. Ele barrou com %r. Barrar aqui nao e sucesso: e a "
                  "operacao que nao aconteceu."
                  % (variante, (resultado_de(rel, "preenche_entre_limites")
                                .get("mensagem") or "")[:160]))
            rel["conclusao"] = ("o preenchimento barrou numa variante que tinha que "
                                "executar. Nada a jusante foi medido, e o ensaio "
                                "FALHOU.")
            fecha(rel, saida, barram_de_proposito=BARRAM)
            return
        julga(rel, "preenchimento_barrado_na_precondicao",
              lambda: resultado_de(rel, "preenche_entre_limites")["estado"]
                      == "PRECONDICAO",
              "a pre-condicao barra antes de alterar a peca")
        if motivo:
            julga(rel, "barrou_pelo_motivo_previsto",
                  lambda: motivo in (resultado_de(rel, "preenche_entre_limites")
                                     .get("mensagem") or ""),
                  "a mensagem contem %r, e nao outro motivo qualquer" % motivo)
        julga(rel, "geometria_intacta_apos_o_barrado",
              lambda: F.assinatura(nome)["sha256"] == a_antes["sha256"],
              "a peca nao foi alterada: a assinatura e a mesma de antes")
        julga(rel, "nada_medido_depois_do_barrado",
              lambda: all(resultado_de(rel, n) is None for n in
                          ("mede_malha_apos_uniao", "mede_perfil_da_junção",
                           "limpa_degeneracoes_na_junção")),
              "resultado de uma etapa nao prova outra: nada a jusante foi medido")
        rel["conclusao"] = ("o preenchimento nao foi executado; nada depois dele foi "
                            "medido. Um resultado de etapa nao prova outra.")
        fecha(rel, saida, barram_de_proposito=BARRAM + ("preenche_entre_limites",)
              + (("seleciona_topo_do_patamar_alto", "le_selecao", "reseleciona_topo",
                  "reseleciona_topo_para_subir", "controle_positivo_deslocamento",
                  "reseleciona_topo_para_descer", "devolve_o_deslocamento")
                 if girado else ()))
        return

    # --------- a sobreposicao SERVIU? Antes de medir junção, medir se ela existe.
    inter = (feito.get("interseccao_com_o_material") or {})
    rel["interseccao"] = inter
    if not inter.get("houve_interseccao"):
        passo(rel, "mede_malha_apos_uniao", lambda: F.mede_malha(nome))
        julga(rel, "interseccao_ausente_e_acusada",
              lambda: inter.get("houve_interseccao") is False,
              "uniao sem interseccao e acusada em vez de aprovada")
        rel["conclusao"] = (
            "a uniao concluiu e o volume NAO interceptou o material: interseccao "
            "medida %s. A junção nao existe, entao medir perfil da junção seria medir "
            "coisa nenhuma. Nada mais foi verificado."
            % inter.get("interseccao_medida"))
        fecha(rel, saida, barram_de_proposito=BARRAM)
        return

    # --------- topologia, ANTES de limpar
    passo(rel, "mede_malha_apos_uniao", lambda: F.mede_malha(nome))

    # --------- limpeza LOCAL das degeneracoes que a uniao produziu
    #  MEDIDO: a uniao produz faces de area nula mesmo com sobreposicao positiva e
    #  sem abrir borda nenhuma. A limpeza e restrita a regiao da junção.
    caixa_junção_min = [vao["x_de"] - 2 * ov, -0.001, vao["z_do_piso"] - 2 * ov]
    caixa_junção_max = [vao["x_ate"] + 2 * ov, W + 0.001, alto["z"] + 2 * ov]
    passo(rel, "limpa_degeneracoes_na_junção",
          lambda: F.limpa_degeneracoes_na_regiao(
              nome, caixa_junção_min, caixa_junção_max, tolerancia=1e-5,
              justificativa_da_tolerancia=(
                  "1e-5 unidades: quatro ordens de grandeza abaixo do menor detalhe "
                  "geometrico deste cenario, que e a sobreposicao de %s, e acima da "
                  "precisao de coincidencia do solver EXACT" % ov)),
          esperado="degeneracoes zeradas sem abrir borda")

    passo(rel, "mede_malha_apos_limpeza", lambda: F.mede_malha(nome))

    # UM ponto de historico para a OPERACAO LOGICA inteira: uniao mais limpeza. A
    # limpeza escreve por bm.to_mesh, que e mutacao direta e nao entra no historico
    # sozinha; e marcar duas vezes faria um `undo` parar no meio do caminho.
    passo(rel, "marca_fim_da_operacao_logica",
          lambda: F.marca_recuperacao("preenchimento do vao concluido, com limpeza"))

    # --------- PERFIL: e esta a medida que pega ranhura e desnivel
    # CORRIGIDO depois de medir: a grade UNIFORME pulou uma saliencia de 0,3 que
    # ocupava apenas a zona de sobreposicao, entre o limite e o limite menos ov. Uma
    # amostragem que so cobre o vao nao cobre a JUNÇÃO. Agora a grade uniforme e
    # somada a pontos DENSOS na vizinhanca de cada limite.
    xs_perfil = sorted(set(
        [round(x, 4) for x in
         _linspace(vao["x_de"] - 3 * ov, vao["x_ate"] + 3 * ov, 15)]
        # a lista de k tem que ser SIMETRICA e a MESMA nos dois limites. A versao
        # anterior era assimetrica, e "para dentro do material" tem sinal oposto em
        # cada ponta: a costura do limite b, em x_ate + ov, nunca era amostrada.
        # Uma sessao limpa independente seguiu a receita ao pe da letra e mediu.
        + [round(x_ref + k * ov, 4)
           for x_ref in (vao["x_de"], vao["x_ate"])
           for k in (-1.5, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 1.5)]))
    ys_perfil = [round(W * f, 4) for f in (0.1, 0.5, 0.9)]
    pontos_perfil = perfil_esperado(vao, alto, baixo, xs_perfil, ys_perfil)
    passo(rel, "mede_perfil_da_junção",
          lambda: F.mede_topo_em_pontos(nome, pontos_perfil, tolerancia=tol),
          esperado=("correta: todos dentro de %s. ranhura: desvio proximo de 0,5 "
                    "no trecho da rampa" % tol))

    # --------- superficie protegida DEPOIS, mesmos pontos
    passo(rel, "superficie_protegida_depois",
          lambda: F.mede_topo_em_pontos(nome, pontos_prot, tolerancia=tol),
          esperado="identica a de antes, dentro da tolerancia")

    # --------- secao, como inspecao independente da junção
    passo(rel, "secao_no_meio",
          lambda: F.secao_por_plano(nome, [0.0, W / 2.0, 0.0], [0.0, 1.0, 0.0]))

    # --------- recuperacao conferida pelo CONTEUDO
    a_depois = F.assinatura(nome)
    rel["assinatura_depois_da_uniao"] = a_depois["sha256"]
    passo(rel, "contexto_de_historico", F.contexto_de_historico)
    passo(rel, "desfaz_e_confere",
          lambda: F.desfaz_e_confere(nome, a_antes["sha256"]),
          esperado="recuperou verdadeiro")
    passo(rel, "refaz_e_confere",
          lambda: F.refaz_e_confere(nome, a_depois["sha256"]),
          esperado="recuperou verdadeiro")

    # --------- entrega
    if cfg.get("destino_blend"):
        passo(rel, "salva_cena", lambda: F.salva_cena(cfg["destino_blend"]))
    if cfg.get("destino_stl"):
        passo(rel, "exporta_malha",
              lambda: F.exporta_malha(nome, cfg["destino_stl"]))

    # ---- vereditos do caminho completo, cada um com predicado executavel
    espera_perfil_dentro = (variante != "ranhura")
    julga(rel, "tres_zonas_interceptam",
          lambda: all(z["intercepta"] for z in
                      resultado_de(rel, "preenche_entre_limites")["resultado"]
                      ["interseccao_por_zona"].values()),
          "as tres zonas prometidas encontram material, medidas em copia")
    # CORRIGIDO depois da QUARTA revisao. A topologia ANTES da limpeza era medida e
    # nenhum predicado a usava: todos os criterios olhavam a malha DEPOIS. Como a
    # `ranhura` existe para provar "forma errada com topologia LIMPA", uma ranhura que
    # tambem produzisse degeneracao seria limpa e ainda receberia credito pela mesma
    # frase. A evidencia media zero por acaso; o oraculo nao exigia.
    if variante == "ranhura":
        julga(rel, "ranhura_nasce_com_topologia_limpa",
              lambda: (resultado_de(rel, "mede_malha_apos_uniao")["resultado"]
                       ["arestas_abertas"] == 0
                       and resultado_de(rel, "mede_malha_apos_uniao")["resultado"]
                       ["arestas_nao_manifold"] == 0
                       and resultado_de(rel, "mede_malha_apos_uniao")["resultado"]
                       ["faces_degeneradas"] == 0),
              "ANTES da limpeza: zero borda aberta, zero nao-manifold e zero "
              "degenerada. E o que sustenta a frase 'so o perfil reprova' — sem isto, "
              "uma ranhura que tambem sujasse a topologia ganharia o mesmo credito "
              "depois de a limpeza apagar o rastro")
    julga(rel, "malha_sem_borda_aberta_e_sem_nao_manifold",
          lambda: (resultado_de(rel, "mede_malha_apos_limpeza")["resultado"]
                   ["arestas_abertas"] == 0
                   and resultado_de(rel, "mede_malha_apos_limpeza")["resultado"]
                   ["arestas_nao_manifold"] == 0),
          "depois da limpeza, zero bordas abertas e zero nao-manifold")
    # CORRIGIDO depois da terceira revisao: "zerou e nao abriu borda" tambem passa
    # com 0 -> 0, ou seja, o criterio da variante duplicado podia ganhar credito sem
    # que o defeito de degeneracao tivesse sido plantado. Agora ela exige que o
    # defeito EXISTA e que a limpeza o remova.
    if variante == "duplicado":
        julga(rel, "degeneracao_foi_plantada_e_removida",
              lambda: (resultado_de(rel, "limpa_degeneracoes_na_junção")["resultado"]
                       ["degeneradas_antes"] > 0
                       and resultado_de(rel, "limpa_degeneracoes_na_junção")
                       ["resultado"]["degeneradas_depois"] == 0
                       and resultado_de(rel, "limpa_degeneracoes_na_junção")
                       ["resultado"]["abriu_borda"] is False),
              "repetir a uniao PRODUZ degeneracao, e a limpeza a remove sem abrir "
              "borda. Sem exigir degeneradas_antes > 0, o criterio passaria com 0 a 0")
    else:
        julga(rel, "degeneracao_zerada_sem_abrir_borda",
              lambda: (resultado_de(rel, "limpa_degeneracoes_na_junção")["resultado"]
                       ["degeneradas_depois"] == 0
                       and resultado_de(rel, "limpa_degeneracoes_na_junção")
                       ["resultado"]["abriu_borda"] is False),
              "depois da limpeza, zero degeneradas e nenhuma borda aberta nova")
    julga(rel, "um_componente_conexo",
          lambda: resultado_de(rel, "mede_malha_apos_limpeza")["resultado"]
                  ["n_componentes_conexos"] == 1,
          "a peca continua um corpo unico")
    julga(rel, "perfil_%s" % ("dentro_da_tolerancia" if espera_perfil_dentro
                              else "REPROVA_na_variante_ranhura"),
          lambda: (resultado_de(rel, "mede_perfil_da_junção")["resultado"]
                   ["todos_dentro_da_tolerancia"] is espera_perfil_dentro),
          ("o perfil fica dentro da tolerancia" if espera_perfil_dentro
           else "o perfil REPROVA, porque a rampa foi construida abaixo dos limites"))
    julga(rel, "perfil_sem_ponto_sem_material",
          lambda: resultado_de(rel, "mede_perfil_da_junção")["resultado"]
                  ["n_sem_material"] == 0,
          "todos os pontos do perfil encontram material")
    julga(rel, "costuras_amostradas_nas_duas_pontas",
          lambda: (round(vao["x_de"] - ov, 4) in
                   {a["x"] for a in resultado_de(rel, "mede_perfil_da_junção")
                    ["resultado"]["amostras"]}
                   and round(vao["x_ate"] + ov, 4) in
                   {a["x"] for a in resultado_de(rel, "mede_perfil_da_junção")
                    ["resultado"]["amostras"]}),
          "as costuras em limite-ov e limite+ov estao entre os pontos amostrados")
    julga(rel, "superficie_protegida_intacta",
          lambda: (resultado_de(rel, "superficie_protegida_antes")["resultado"]
                   ["todos_dentro_da_tolerancia"] is True
                   and resultado_de(rel, "superficie_protegida_depois")["resultado"]
                   ["todos_dentro_da_tolerancia"] is True),
          "a superficie protegida mede o mesmo antes e depois")
    # Na variante duplicado a expectativa e OUTRA, e isto e achado desta rodada:
    # aplicar a uniao duas vezes PRODUZ face nao convexa. Medido: 2 faces cortadas em
    # mais de dois pontos, 12 pontos e apenas 10 segmentos — a poligonal fica
    # incompleta de fato. O criterio certo nao e "zero"; e "a ferramenta acusa".
    if variante == "duplicado":
        julga(rel, "secao_acusa_face_ambigua_quando_ela_existe",
              lambda: (resultado_de(rel, "secao_no_meio")["resultado"]
                       ["faces_com_mais_de_dois_cruzamentos"] > 0),
              "a repeticao da uniao cria face nao convexa, e a secao ACUSA em vez de "
              "devolver poligonal incompleta em silencio")
    else:
        julga(rel, "secao_sem_face_ambigua",
              lambda: resultado_de(rel, "secao_no_meio")["resultado"]
                      ["faces_com_mais_de_dois_cruzamentos"] == 0,
              "nenhuma face nao convexa cortada em mais de dois pontos")
    julga(rel, "undo_recupera_por_assinatura",
          lambda: resultado_de(rel, "desfaz_e_confere")["resultado"]["recuperou"] is True,
          "undo devolve a assinatura anterior")
    julga(rel, "redo_recupera_por_assinatura",
          lambda: resultado_de(rel, "refaz_e_confere")["resultado"]["recuperou"] is True,
          "redo devolve a assinatura posterior")
    fecha(rel, saida, barram_de_proposito=BARRAM)


def _linspace(a, b, n):
    if n < 2:
        return [a]
    passo_ = (b - a) / (n - 1)
    return [a + i * passo_ for i in range(n)]


def _grava(saida, rel):
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    open(saida, "w", encoding="utf-8").write(json.dumps(rel, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
