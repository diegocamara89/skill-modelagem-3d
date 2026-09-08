"""roda_casos.py - executa os casos e confere roteamento, resultado e extras.

Uso:
  python roda_casos.py [--caso 4] [--json out.json]
              [--maquina NOME --processo NOME --filamento NOME --envelope AxBxC]
              [--sem-fatiador]

TRES COISAS QUE ESTE EXECUTOR FAZ E QUE UM TESTE INGENUO NAO FAZ

1. Confere o ROTEAMENTO antes da geometria. Um caso reprova se uma verificacao que devia
   ser exigida nao foi, e tambem se uma que devia ser dispensada foi cobrada. Sem isso a
   matriz seria decoracao.

2. Distingue CINCO estados por verificacao, e nao dois. Aprovada, reprovada, ausente,
   erro e nao aplicavel sao coisas diferentes. CORRIGIDO 07/09/2026 depois da segunda
   revisao externa: a versao anterior decidia so por "reprovadas" e deixava "nao rodadas"
   de fora, entao um verificador AUSENTE nao impedia a aprovacao do caso. Verificacao
   obrigatoria sem resultado valido agora BARRA.

3. Consome o veredito COMPLETO de cada ferramenta. A versao anterior chamava o portao de
   malha e usava dois campos favoraveis, descartando o veredito geral: uma malha com
   todas as faces invertidas mantem estanqueidade e incidencia de arestas, e passava.
   Agora cada verificacao derivada tambem reprova se o veredito da ferramenta reprovou.

Um caso tambem reprova se o resultado nao bate com o que ele declarou esperar. Caso 3
declara que espera ser BARRADO na folga: se passar, e falha do teste, nao sucesso.
"""
import argparse, json, os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import casos as CASOS
import matriz

APROVADA, REPROVADA, AUSENTE, ERRO, NAO_APLICAVEL = (
    "APROVADA", "REPROVADA", "AUSENTE", "ERRO", "NAO_APLICAVEL")
ESTADOS_VALIDOS = (APROVADA, REPROVADA, AUSENTE, ERRO, NAO_APLICAVEL)
ACEITAVEIS = (APROVADA, NAO_APLICAVEL)

# Ambiente da oficina. CORRIGIDO 07/09/2026: era fixo no codigo, o que impedia qualquer
# outra instalacao de rodar a suite. Agora vem de argumento ou de variavel de ambiente.
AMBIENTE = {
    "maquina": os.environ.get("SKILL3D_MAQUINA", "Bambu Lab A1 0.4 nozzle"),
    "processo": os.environ.get("SKILL3D_PROCESSO", "0.20mm Standard @BBL A1"),
    "filamento": os.environ.get("SKILL3D_FILAMENTO", "Generic PLA @BBL A1"),
    "envelope": os.environ.get("SKILL3D_ENVELOPE", "256x256x256"),
    "orca": os.environ.get("SKILL3D_ORCA", ""),
    "perfis": os.environ.get("SKILL3D_PERFIS", ""),
    "vendor": os.environ.get("SKILL3D_VENDOR", ""),
    "trabalho": os.environ.get("SKILL3D_TRABALHO", ""),
    "registro": os.environ.get("SKILL3D_REGISTRO", ""),
    "sem_fatiador": False,
}


def _py(script, args):
    try:
        r = subprocess.run([sys.executable, os.path.join(AQUI, script)] + args,
                           capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return {"_erro": "timeout ao rodar %s" % script}
    s = r.stdout
    i = s.find("{")
    if i < 0:
        return {"_erro": "sem JSON na saida de %s" % script,
                "_stdout": s[-400:], "_stderr": r.stderr[-400:]}
    try:
        return json.loads(s[i:])
    except Exception as e:
        return {"_erro": "JSON invalido de %s: %s" % (script, e), "_stdout": s[-400:]}


def _falhou(d):
    return isinstance(d, dict) and "_erro" in d


# ------------------------------------------------ verificadores

def ver_intencao(c):
    d = c.get("_cache_intencao")
    if d is None:
        d = _py("check_intent.py", ["--malha", c["malha"], "--requisitos", c["requisitos"]]
                + (["--referencia", c["referencia"]] if c.get("referencia") else []))
        c["_cache_intencao"] = d
    if _falhou(d):
        return ERRO, d
    det = {"aprovados": d.get("n_aprovados"), "reprovados": d.get("n_reprovados"),
           "nao_verificados": d.get("n_nao_verificados"),
           "por_estado": {k: v for k, v in (d.get("por_estado") or {}).items() if v},
           "quais_reprovaram": [x["id"] for x in (d.get("reprovados") or [])],
           "quais_nao_verificados": [x["id"] for x in (d.get("nao_verificados") or [])]}
    # CORRIGIDO 07/09/2026: erro operacional dentro da medicao virava REPROVADA, e uma
    # mutacao que so exige "reprovou na intencao" recebia credito por falha de execucao.
    if d.get("houve_erro_operacional"):
        return ERRO, dict(det, motivo="houve erro operacional em requisito da intencao")
    return (APROVADA if d.get("atende_ao_pedido") else REPROVADA), det


def ver_geometria_nao_vazia(c):
    g = c.get("geometria_nao_vazia")
    if not isinstance(g, dict) or "ok" not in g:
        return AUSENTE, {"motivo": "o caso nao declarou geometria_nao_vazia"}
    return (APROVADA if g["ok"] else REPROVADA), g


def _malha(c):
    d = c.get("_cache_malha")
    if d is None:
        d = _py("check_mesh.py", ["--malha", c["malha"]])
        c["_cache_malha"] = d
    return d


def ver_malha_estanque(c):
    d = _malha(c)
    if _falhou(d):
        return ERRO, d
    det = {"fechada": d.get("fechada_watertight"), "arestas_abertas": d.get("arestas_abertas"),
           "veredito_da_ferramenta": d.get("apto_para_booleana"),
           "motivos_da_ferramenta": d.get("motivos_de_reprovacao")}
    ok = bool(d.get("fechada_watertight")) and bool(d.get("apto_para_booleana"))
    return (APROVADA if ok else REPROVADA), det


def ver_zero_nao_manifold(c):
    d = _malha(c)
    if _falhou(d):
        return ERRO, d
    det = {"arestas_com_mais_de_2_faces": d.get("arestas_com_mais_de_2_faces"),
           "veredito_da_ferramenta": d.get("apto_para_booleana"),
           "motivos_da_ferramenta": d.get("motivos_de_reprovacao")}
    ok = d.get("arestas_com_mais_de_2_faces") == 0 and bool(d.get("apto_para_booleana"))
    return (APROVADA if ok else REPROVADA), det


def ver_portao_do_fatiador(c):
    if AMBIENTE["sem_fatiador"]:
        return AUSENTE, {"motivo": "execucao pediu --sem-fatiador: esta verificacao "
                                   "obrigatoria NAO foi feita"}
    args = ["--modelo", c["malha"], "--maquina", AMBIENTE["maquina"],
            "--processo", AMBIENTE["processo"], "--filamento", AMBIENTE["filamento"]]
    # CORRIGIDO 07/09/2026: o runner aceitava --orca e nao repassava perfis, vendor nem
    # diretorio de trabalho, entao trocar o executavel nao trocava o diretorio de perfis.
    for chave, flag in (("orca", "--orca"), ("perfis", "--perfis"),
                        ("vendor", "--vendor"), ("trabalho", "--trabalho")):
        if AMBIENTE.get(chave):
            args += [flag, AMBIENTE[chave]]
    d = _py("slice_check.py", args)
    if _falhou(d):
        return ERRO, d
    det = {"aprovado": d.get("aprovado"), "codigo": d.get("codigo_legivel"),
           "processo_concluido": d.get("processo_concluido"),
           "saida_gerada": d.get("saida_gerada"),
           "checagens_aprovadas": d.get("checagens_aprovadas"),
           "motivos": (d.get("motivos_de_reprovacao") or [])[:3]}
    return (APROVADA if d.get("aprovado") else REPROVADA), det


def ver_envelope_e_particao(c):
    d = _py("split_for_volume.py", ["--malha", c["malha"], "--envelope", AMBIENTE["envelope"]])
    if _falhou(d):
        return ERRO, d
    o = d.get("orientacao_escolhida") or {}
    cabe = bool(o.get("cabe"))
    validada = bool(d.get("particao_validada"))
    det = {"cabe_inteira": cabe, "particao_validada": validada,
           "pecas": o.get("pecas_por_eixo"),
           "veredito": (d.get("veredito") or "")[:110]}
    if cabe:
        return APROVADA, det
    # nao cabe: exige particao dimensionalmente VALIDADA, nao so candidatos
    return (APROVADA if validada else REPROVADA), det


def ver_folga_calibrada(c):
    dec = c.get("declaracoes") or {}
    if not dec.get("encaixe_declarado"):
        return NAO_APLICAVEL, {"motivo": "nenhum encaixe declarado nesta peca"}
    args = ["--ajuste", dec.get("tipo_de_ajuste", "deslizante"),
            "--maquina", dec.get("maquina", ""), "--material", dec.get("material", "")]
    if AMBIENTE["registro"]:
        args += ["--registro", AMBIENTE["registro"]]
    d = _py("tolerance_lookup.py", args)
    if _falhou(d):
        return ERRO, d
    det = {"aplicavel": d.get("medicao_aplicavel"),
           "valor_a_usar_mm": d.get("valor_a_usar_mm"),
           "origem": d.get("origem_do_valor"),
           "bloqueio": d.get("aviso_de_bloqueio"),
           "faixa_publicada_mm": d.get("faixa_publicada_mm")}
    return (APROVADA if d.get("medicao_aplicavel") else REPROVADA), det


def ver_orientacao_anisotropia(c):
    dec = c.get("declaracoes") or {}
    tem = bool(dec.get("orientacao_de_impressao")) and bool(dec.get("direcao_da_carga"))
    return (APROVADA if tem else REPROVADA), {
        "orientacao_de_impressao": dec.get("orientacao_de_impressao"),
        "direcao_da_carga": dec.get("direcao_da_carga"),
        "nota": "confere que a decisao foi DECLARADA, nao que ela esta estruturalmente correta"}


def ver_reabre_em_cad(c):
    """Confere o intercambio conforme a REPRESENTACAO declarada.

    CORRIGIDO 07/09/2026, duas vezes. Primeiro aprovava por "algum solido", e um
    intercambio de UM componente passava por uma montagem de dois. Depois exigia solido
    sempre, e reprovava superficie legitima: um STEP de casca tem zero solidos e faces.
    Agora o contrato e por representacao.
    """
    p = c.get("step")
    dec = c.get("declaracoes") or {}
    rep = c["classificacao"]["representacao"]
    if not p:
        return AUSENTE, {"motivo": "o caso nao declarou arquivo de intercambio"}
    if not os.path.isfile(p):
        return REPROVADA, {"motivo": "arquivo de intercambio nao existe: %s" % p}
    try:
        from build123d import import_step
        forma = import_step(p)
        n_sol = len(forma.solids())
        n_face = len(forma.faces())
        n_shell = len(forma.shells())
    except Exception as e:
        return ERRO, {"motivo": "%s: %s" % (type(e).__name__, e)}
    det = {"arquivo": os.path.basename(p), "representacao": rep,
           "solidos": n_sol, "faces": n_face, "shells": n_shell,
           "bytes": os.path.getsize(p)}
    if rep in ("solido", "montagem"):
        esperado = int(dec.get("componentes_esperados_no_step", 1))
        det["solidos_esperados"] = esperado
        ok = n_sol == esperado
    elif rep == "superficie":
        esperado = int(dec.get("faces_esperadas_no_step", 1))
        det["faces_esperadas"] = esperado
        det["nota"] = ("superficie: o contrato e presenca de faces, nao de solidos. "
                       "Contar zero solidos NAO seria evidencia de que a casca existe.")
        ok = n_sol == 0 and n_face >= esperado
    else:
        return NAO_APLICAVEL, dict(det, motivo="representacao %s nao tem intercambio "
                                               "analitico" % rep)
    return (APROVADA if ok else REPROVADA), det


# Cada obrigacao do roteamento e satisfeita por um TIPO de requisito, e exige pelo menos
# uma evidencia valida daquele tipo. CORRIGIDO 07/09/2026 depois da terceira revisao
# externa. Antes, a obrigacao era resolvida filtrando IDs por substring: um requisito de
# preservacao com id neutro reprovava na intencao e a obrigacao aparecia APROVADA, e
# remover o requisito por completo tambem aprovava, porque a lista filtrada ficava vazia.
# Id identifica requisito; nao e linguagem de classificacao.
TIPO_POR_OBRIGACAO = {
    "regiao_preservada": ("regiao_intacta",),
    "n_corpos_esperado": ("n_solidos",),
    "interferencia": ("interferencia",),
}


def _obrigacao_por_tipo(c, obrigacao):
    st, det = ver_intencao(c)
    if st == ERRO:
        return ERRO, det
    d = c.get("_cache_intencao") or {}
    # CORRIGIDO 07/09/2026: usava o dicionario por id, que perde evidencia quando dois
    # requisitos compartilham o id. Agora le a LISTA de estados.
    lista = d.get("estados_dos_requisitos")
    if lista is None:
        mapa = d.get("estados_por_requisito") or {}
        lista = [{"id": k, "tipo": v.get("tipo"), "estado": v.get("estado")}
                 for k, v in mapa.items()]
    tipos = TIPO_POR_OBRIGACAO[obrigacao]
    do_tipo = {}
    for i, v in enumerate(lista):
        if v.get("tipo") in tipos:
            do_tipo["%s#%d" % (v.get("id"), i)] = v
    base = {"obrigacao": obrigacao, "tipos_que_satisfazem": list(tipos),
            "requisitos_desse_tipo": do_tipo,
            "nota": ("a obrigacao exige pelo menos um requisito deste tipo, medido e "
                     "aprovado. Ausencia de requisito NAO e aprovacao.")}
    if not do_tipo:
        return AUSENTE, dict(base, motivo="nenhum requisito deste tipo foi declarado, "
                                          "logo a obrigacao nao tem evidencia")
    estados = [v["estado"] for v in do_tipo.values()]
    if any(e in ("ERRO", "ESPEC_INVALIDA") for e in estados):
        return ERRO, dict(base, motivo="requisito deste tipo com erro ou especificacao invalida")
    if any(e in ("NAO_IMPLEMENTADA", "INDETERMINADA") for e in estados):
        return AUSENTE, dict(base, motivo="requisito deste tipo sem medicao")
    if any(e == "REPROVADA" for e in estados):
        return REPROVADA, dict(base, motivo="requisito deste tipo reprovou")
    return APROVADA, base


def ver_regiao_preservada(c):
    return _obrigacao_por_tipo(c, "regiao_preservada")


def ver_n_corpos_esperado(c):
    return _obrigacao_por_tipo(c, "n_corpos_esperado")


def ver_interferencia(c):
    return _obrigacao_por_tipo(c, "interferencia")


def ver_entrada_intacta(c):
    e = c.get("entrada_intacta")
    if not isinstance(e, dict) or "ok" not in e:
        return AUSENTE, {"motivo": "o caso nao declarou entrada_intacta"}
    return (APROVADA if e["ok"] else REPROVADA), e


def ver_proveniencia_de_cota(c):
    p = c.get("proveniencia")
    if not isinstance(p, dict) or "ok" not in p:
        return AUSENTE, {"motivo": "o caso nao declarou proveniencia"}
    return (APROVADA if p["ok"] else REPROVADA), p


def ver_varredura_de_familia(c):
    g = c.get("familia")
    if not g:
        return NAO_APLICAVEL, {"motivo": "o caso nao declara familia parametrica a varrer"}
    # CORRIGIDO 07/09/2026 depois da quarta revisao externa. O arquivo temporario usava
    # somente o PID e era reaproveitado: uma varredura aprovada criava o arquivo, a
    # seguinte falhava antes de gravar outro, e o fallback lia o resultado ANTERIOR e
    # devolvia APROVADA. Agora o arquivo e exclusivo por chamada, e a identidade da
    # execucao (modulo, funcao, grade) e conferida no que voltou.
    import tempfile, uuid
    alvo = os.path.join(tempfile.gettempdir(),
                        "skill3d_varredura_%d_%s.json" % (os.getpid(), uuid.uuid4().hex[:10]))
    if os.path.exists(alvo):
        os.remove(alvo)
    argv = ["--modulo", g["modulo"], "--funcao", g.get("funcao", "constroi"),
            "--grade", g["grade"], "--json", alvo]
    # a representacao declarada chega ao verificador, e nao so seleciona o nome dele
    if g.get("representacao"):
        argv += ["--representacao", g["representacao"]]
    if g.get("n_solidos"):
        argv += ["--n-solidos", str(g["n_solidos"])]
    d = _py("sweep_params.py", argv)
    # CORRIGIDO 07/09/2026: o runner tentava extrair JSON do stdout e a ferramenta nunca o
    # imprimia, entao TODA varredura devolvia "sem JSON na saida". O caminho de
    # parametrizar estava quebrado e nenhum dos seis casos o exercitava.
    if _falhou(d) and os.path.isfile(alvo):
        try:
            d = json.load(open(alvo, encoding="utf-8"))
        except Exception as e:
            d = {"_erro": "arquivo de varredura ilegivel: %s" % e}
    try:
        if os.path.isfile(alvo):
            os.remove(alvo)
    except OSError:
        pass
    if _falhou(d):
        return ERRO, d
    esperado = {"modulo": g["modulo"], "funcao": g.get("funcao", "constroi"),
                "grade": g["grade"]}
    veio = {k: d.get(k) for k in esperado}
    if veio != esperado:
        return ERRO, {"motivo": "o relatorio de varredura NAO e desta chamada",
                      "esperado": esperado, "veio": veio}
    det = {"n_variantes": d.get("n_variantes"), "n_aprovadas": d.get("n_aprovadas"),
           "n_reprovadas": d.get("n_reprovadas"),
           "n_reprovadas_por_geometria": d.get("n_reprovadas_por_geometria"),
           "n_com_erro_operacional": d.get("n_com_erro_operacional"),
           "erros_operacionais": d.get("erros_operacionais"),
           "identidade_conferida": esperado}
    # erro operacional em variante NAO e reprovacao geometrica
    if d.get("houve_erro_operacional"):
        return ERRO, dict(det, motivo="variante com erro operacional: a varredura nao "
                                      "avaliou geometria nessas combinacoes")
    return ((APROVADA if d.get("n_reprovadas") == 0 else REPROVADA), det)


VERIFICADORES = {
    "intencao": ver_intencao,
    "geometria_nao_vazia": ver_geometria_nao_vazia,
    "malha_estanque": ver_malha_estanque,
    "zero_nao_manifold": ver_zero_nao_manifold,
    "portao_do_fatiador": ver_portao_do_fatiador,
    "envelope_e_particao": ver_envelope_e_particao,
    "folga_calibrada": ver_folga_calibrada,
    "orientacao_anisotropia": ver_orientacao_anisotropia,
    "reabre_em_cad": ver_reabre_em_cad,
    "regiao_preservada": ver_regiao_preservada,
    "entrada_intacta": ver_entrada_intacta,
    "proveniencia_de_cota": ver_proveniencia_de_cota,
    "n_corpos_esperado": ver_n_corpos_esperado,
    "interferencia": ver_interferencia,
    "varredura_de_familia": ver_varredura_de_familia,
}


def roda(fn):
    t0 = time.time()
    c = fn()
    t_build = time.time() - t0
    cl = c["classificacao"]
    rota = matriz.rotear(cl["modalidade"], cl["representacao"], cl["finalidade"])
    esp = c["espera"]

    faltando = [n for n in esp.get("exige", []) if n not in rota["exigidas"]]
    sobrando = [n for n in esp.get("nao_exige", []) if n in rota["exigidas"]]
    roteamento_ok = not faltando and not sobrando

    nao_aplicaveis_declaradas = set(esp.get("nao_aplicaveis", []))
    resultados = {}
    for nome in rota["exigidas"]:
        fnv = VERIFICADORES.get(nome)
        if fnv is None:
            resultados[nome] = {"estado": AUSENTE,
                                "detalhe": {"motivo": "nao existe verificador registrado "
                                                      "para esta verificacao obrigatoria"}}
            continue
        try:
            st, det = fnv(c)
        except Exception as e:
            st, det = ERRO, {"motivo": "%s: %s" % (type(e).__name__, e)}
        # CORRIGIDO 07/09/2026 depois da terceira revisao externa: o estado devolvido nao
        # era validado, entao um valor fora do contrato, como "EROR", nao entrava em
        # nenhuma lista e o caso podia sair com evidencia completa e aprovado.
        if st not in ESTADOS_VALIDOS:
            det = {"motivo": "verificador devolveu estado fora do contrato: %r" % (st,),
                   "detalhe_original": det}
            st = ERRO
        resultados[nome] = {"estado": st, "detalhe": det}

    reprovadas = [n for n, r in resultados.items() if r["estado"] == REPROVADA]
    ausentes = [n for n, r in resultados.items() if r["estado"] == AUSENTE]
    erros = [n for n, r in resultados.items() if r["estado"] == ERRO]
    nao_aplic = [n for n, r in resultados.items() if r["estado"] == NAO_APLICAVEL]
    # nao aplicavel so vale se o caso declarou; senao e suspeita e barra
    nao_aplic_indevidas = [n for n in nao_aplic if n not in nao_aplicaveis_declaradas]
    bloqueios = sorted(set(ausentes + erros + nao_aplic_indevidas))
    completo = not bloqueios

    esperado = esp.get("resultado")
    if not completo:
        resultado_ok = False
        obtido = "INCOMPLETO: sem resultado valido em " + ", ".join(bloqueios)
    elif esperado == "aprovado":
        resultado_ok = not reprovadas
        obtido = "aprovado" if not reprovadas else "reprovado em: " + ", ".join(reprovadas)
    elif esperado == "barrado_na_folga":
        resultado_ok = reprovadas == ["folga_calibrada"]
        obtido = ("barrado_na_folga" if reprovadas == ["folga_calibrada"]
                  else "aprovado" if not reprovadas else "reprovado em: " + ", ".join(reprovadas))
    else:
        resultado_ok, obtido = False, "expectativa desconhecida: %s" % esperado

    extras = []
    if c.get("requisitos_de_controle"):
        d = _py("check_intent.py", ["--malha", c["malha"],
                                    "--requisitos", c["requisitos_de_controle"]]
                + (["--referencia", c["referencia"]] if c.get("referencia") else []))
        divergiu = (not _falhou(d)) and bool(d.get("reprovados"))
        extras.append({"nome": "a regiao EDITADA tem que divergir", "passou": divergiu,
                       "detalhe": {"reprovados": [x["id"] for x in (d.get("reprovados") or [])]
                                   if not _falhou(d) else d}})
    if c.get("datum"):
        dt = c["datum"]
        tol = dt.get("tol_deg", 0.5)
        ok = (dt.get("erro_deg") is not None and dt["erro_deg"] <= tol)
        extras.append({"nome": "o assento reconstruido mantem a NORMAL da referencia",
                       "passou": ok, "detalhe": dt})
        # controle independente: o extrator concorda com o angulo conhecido do gerador?
        verdadeiro = dt.get("angulo_verdadeiro_da_referencia_deg")
        lido = dt.get("angulo_na_referencia_deg")
        if verdadeiro is not None and lido is not None:
            extras.append({
                "nome": "o extrator concorda com o angulo conhecido do gerador",
                "passou": abs(float(verdadeiro) - float(lido)) <= tol,
                "detalhe": {"gerador_deg": verdadeiro, "extrator_deg": lido, "tol_deg": tol,
                            "motivo": ("separa a validacao do EXTRATOR da comparacao entre "
                                       "referencia e reconstrucao. Sem isso, duas leituras "
                                       "erradas pelo mesmo metodo concordam entre si.")}})
    if c.get("fatos_da_malha"):
        f = c["fatos_da_malha"]
        extras.append({"nome": "a malha NAO e fechada e o caso passa mesmo assim",
                       "passou": (not f.get("fechada_watertight")) and completo and not reprovadas,
                       "detalhe": f})
    if esp.get("limite_de_tempo_s"):
        extras.append({"nome": "termina abaixo do limite de tempo",
                       "passou": t_build <= esp["limite_de_tempo_s"],
                       "detalhe": {"tempo_de_construcao_s": round(t_build, 3),
                                   "limite_s": esp["limite_de_tempo_s"]}})
    if "portao_do_fatiador" in esp.get("nao_exige", []):
        extras.append({"nome": "o fatiador NAO foi invocado",
                       "passou": "portao_do_fatiador" not in resultados,
                       "detalhe": {"verificacoes_rodadas": sorted(resultados)}})

    extras_ok = all(e["passou"] for e in extras) if extras else True
    passou = bool(roteamento_ok and resultado_ok and extras_ok)

    return {
        "id": c["id"], "titulo": c["titulo"], "classificacao": cl,
        "tempo_de_construcao_s": round(t_build, 3),
        "ambiente": {k: AMBIENTE[k] for k in ("maquina", "processo", "filamento",
                                              "envelope", "sem_fatiador")},
        "roteamento": {"exigidas": rota["exigidas"], "dispensadas": sorted(rota["dispensadas"]),
                       "faltando_no_roteamento": faltando,
                       "cobrado_indevidamente": sobrando, "ok": roteamento_ok},
        "verificacoes": resultados,
        "reprovadas": reprovadas, "ausentes": ausentes, "erros": erros,
        "nao_aplicaveis": nao_aplic, "nao_aplicaveis_indevidas": nao_aplic_indevidas,
        "bloqueios": bloqueios, "evidencia_completa": completo,
        "resultado_esperado": esperado, "resultado_obtido": obtido, "resultado_ok": resultado_ok,
        "extras": extras, "extras_ok": extras_ok,
        "PASSOU": passou,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", type=int)
    ap.add_argument("--json")
    ap.add_argument("--maquina"); ap.add_argument("--processo")
    ap.add_argument("--filamento"); ap.add_argument("--envelope")
    ap.add_argument("--orca"); ap.add_argument("--registro")
    ap.add_argument("--perfis"); ap.add_argument("--vendor"); ap.add_argument("--trabalho")
    ap.add_argument("--sem-fatiador", action="store_true")
    a = ap.parse_args()
    for k in ("maquina", "processo", "filamento", "envelope", "orca", "registro",
              "perfis", "vendor", "trabalho"):
        if getattr(a, k):
            AMBIENTE[k] = getattr(a, k)
    AMBIENTE["sem_fatiador"] = bool(a.sem_fatiador)

    fns = CASOS.TODOS if not a.caso else [CASOS.TODOS[a.caso - 1]]
    linhas = []
    for fn in fns:
        try:
            r = roda(fn)
        except Exception as e:
            import traceback
            r = {"id": fn.__name__, "PASSOU": False, "erro": "%s: %s" % (type(e).__name__, e),
                 "trace": traceback.format_exc()[-900:]}
        linhas.append(r)
        print("%-6s %-30s %s" % ("PASSOU" if r.get("PASSOU") else "FALHOU", r["id"],
                                 r.get("titulo", r.get("erro", ""))[:58]))
        if not r.get("PASSOU"):
            if r.get("erro"):
                print("        erro:", r["erro"][:200])
                continue
            if r["roteamento"]["faltando_no_roteamento"]:
                print("        roteamento nao exigiu:", r["roteamento"]["faltando_no_roteamento"])
            if r["roteamento"]["cobrado_indevidamente"]:
                print("        cobrou indevidamente:", r["roteamento"]["cobrado_indevidamente"])
            if r["bloqueios"]:
                print("        sem evidencia valida em:", r["bloqueios"])
                for n in r["bloqueios"]:
                    print("           %s: %s" % (n, str(r["verificacoes"][n]["detalhe"])[:130]))
            if not r["resultado_ok"] and not r["bloqueios"]:
                print("        esperado %s, obtido %s" % (r["resultado_esperado"], r["resultado_obtido"]))
            for e in r.get("extras", []):
                if not e["passou"]:
                    print("        extra falhou:", e["nome"], "|", str(e["detalhe"])[:120])

    ok = [l for l in linhas if l.get("PASSOU")]
    print()
    print("%d de %d casos passaram." % (len(ok), len(linhas)))
    out = {"n_casos": len(linhas), "n_passaram": len(ok),
           "ambiente": {k: AMBIENTE[k] for k in ("maquina", "processo", "filamento",
                                                 "envelope", "sem_fatiador")},
           "casos": linhas,
           "veredito": ("Todos os casos executados passaram."
                        if len(ok) == len(linhas) else
                        "%d de %d passaram." % (len(ok), len(linhas))),
           "aviso": ("Passar aqui significa que o roteamento e as verificacoes se comportam "
                     "como o desenho declara, NESTE ambiente. Nao significa que qualquer peca "
                     "de qualquer tipo vai sair correta. Com --sem-fatiador a suite fica "
                     "incompleta de proposito e os casos de impressao reprovam por falta de "
                     "evidencia, o que e o comportamento correto.")}
    if a.json:
        open(a.json, "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False))
    return 0 if len(ok) == len(linhas) else 1


if __name__ == "__main__":
    sys.exit(main())
