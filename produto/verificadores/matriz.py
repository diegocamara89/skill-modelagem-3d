"""matriz.py - roteia verificacoes a partir da classificacao. Implementa a secao 4 do DESENHO.md.

A skill nao tem um pipeline. Ela tem uma matriz: as tres decisoes escolhem quais
verificacoes sao EXIGIDAS. Superficie decorativa para render nao aciona estanqueidade,
folga calibrada, direcao de carga nem fatiador. Peca de encaixe para impressao aciona
tudo.

Este modulo e proposital e pequeno. Ele nao verifica nada; so responde o que verificar.
"""

MODALIDADES = ("criar", "editar", "reconstruir", "reparar", "parametrizar")
REPRESENTACOES = ("solido", "superficie", "malha", "montagem")
FINALIDADES = ("visualizacao", "intercambio", "montagem", "impressao_fdm", "usinagem")

# Verificacoes por finalidade. None = nao se aplica a esta finalidade.
POR_FINALIDADE = {
    #                          visualizacao intercambio montagem impressao_fdm usinagem
    "intencao":               (True,        True,       True,    True,         True),
    "geometria_nao_vazia":    (True,        True,       True,    True,         True),
    "malha_estanque":         (False,       False,      False,   True,         None),
    "zero_nao_manifold":      (False,       False,      False,   True,         None),
    "portao_do_fatiador":     (False,       False,      False,   True,         False),
    "envelope_e_particao":    (False,       False,      False,   True,         True),
    "folga_calibrada":        (False,       False,      True,    True,         True),
    "orientacao_anisotropia": (False,       False,      False,   True,         False),
    "reabre_em_cad":          (False,       True,       True,    False,        True),
}

# Verificacoes exigidas pela MODALIDADE, independentes da finalidade.
POR_MODALIDADE = {
    "editar": ("regiao_preservada", "entrada_intacta"),
    "reconstruir": ("proveniencia_de_cota", "entrada_intacta"),
    "reparar": ("entrada_intacta",),
    "parametrizar": ("varredura_de_familia",),
    "criar": (),
}

# Verificacoes exigidas pela REPRESENTACAO.
POR_REPRESENTACAO = {
    "montagem": ("n_corpos_esperado", "interferencia"),
    "solido": (),
    "superficie": (),
    "malha": (),
}

# Verificacoes que NAO se aplicam a certas representacoes, e por que.
INAPLICAVEIS = {
    "superficie": {
        "malha_estanque": "superficie aberta nao tem interior; estanqueidade nao se aplica",
        "zero_nao_manifold": "superficie aberta tem borda por definicao",
        "portao_do_fatiador": "superficie sem espessura nao e imprimivel como esta",
        "folga_calibrada": "sem espessura nao existe encaixe",
        "orientacao_anisotropia": "sem material depositado nao existe anisotropia",
        "envelope_e_particao": "nao ha peca fisica a caber na maquina",
    },
    "malha": {
        "reabre_em_cad": "malha nao carrega historico nem superficie analitica",
    },
}


# --------------------------------------------------------------------------------------
# Requisitos de TOPOLOGIA, declarados separadamente da representacao.
#
# CORRIGIDO em M0.5: a dispensa de borda vinha da REPRESENTACAO, o que faz de
# "superficie" um sinonimo de "casca aberta". Nao e. Uma casca FECHADA sem solido tambem
# e superficie legitima, e nela a borda e PROIBIDA. A regra antiga resolvia o caso da
# casca aberta e criava uma regra falsa para o resto do mundo.
#
# A representacao diz EM QUE se trabalha. A topologia diz O QUE a peca tem que ser.
# Nenhuma das duas e deduzida da outra.
VALORES_DE_TOPOLOGIA = {
    "borda": ("obrigatoria", "proibida", "indiferente"),
    "orientacao": ("exigida", "indiferente"),
    "estanqueidade": ("exigida", "nao_se_aplica", "indiferente"),
}
PADRAO_DE_TOPOLOGIA = {"borda": "indiferente", "orientacao": "indiferente",
                       "componentes": "indiferente", "estanqueidade": "indiferente"}


def valida_topologia(topologia):
    """Normaliza e valida. Declaracao invalida e ERRO, nunca aproximacao para o valor
    mais parecido: inventar o requisito e pior que nao ter requisito."""
    if topologia is None:
        return None
    if not isinstance(topologia, dict):
        raise SystemExit("topologia tem que ser um objeto com os requisitos declarados")
    fora = sorted(set(topologia) - set(PADRAO_DE_TOPOLOGIA))
    if fora:
        raise SystemExit("requisito de topologia desconhecido: %s. Conhecidos: %s"
                         % (fora, sorted(PADRAO_DE_TOPOLOGIA)))
    t = dict(PADRAO_DE_TOPOLOGIA)
    t.update(topologia)
    for chave, permitidos in VALORES_DE_TOPOLOGIA.items():
        if t[chave] not in permitidos:
            raise SystemExit("topologia.%s = %r fora do contrato. Permitidos: %s"
                             % (chave, t[chave], list(permitidos)))
    comp = t["componentes"]
    if comp != "indiferente":
        if isinstance(comp, bool) or not isinstance(comp, int) or comp < 1:
            raise SystemExit("topologia.componentes = %r: use inteiro maior que zero ou "
                             "'indiferente'" % (comp,))
    return t


# --------------------------------------------------------------------------------------
# PAPEL da verificacao. CORRIGIDO em M0.6: a matriz era binaria, entao "medida e nao
# barra" nao existia como estado. Ou a verificacao era exigida e barrava, ou nao era
# feita. Faltava o meio: metrica MEDIDA, relatada, que nao decide.
#
# Os tres papeis, e o que cada um faz com a mesma medida fora do limite:
#   DECISIVA     -> entra nos bloqueios e nos motivos de reprovacao
#   INFORMATIVA  -> aparece medida no relatorio e NUNCA barra
#   NAO_APLICAVEL-> nao e feita, e a dispensa vem com motivo
#
# O papel NAO altera a medida. A mesma geometria produz o mesmo numero nos tres papeis, e
# e isso que o aceite do M0.6 exige demonstrar.
PAPEIS = ("DECISIVA", "INFORMATIVA", "NAO_APLICAVEL")


def valida_papeis(papeis):
    """Papel declarado fora do contrato e erro, nunca o papel mais parecido."""
    if papeis is None:
        return {}
    if not isinstance(papeis, dict):
        raise SystemExit("papeis tem que ser um objeto {verificacao: papel}")
    for nome, papel in papeis.items():
        if papel not in PAPEIS:
            raise SystemExit("papel %r para %r fora do contrato. Permitidos: %s"
                             % (papel, nome, list(PAPEIS)))
    return dict(papeis)


def valida(modalidade, representacao, finalidade):
    erros = []
    if modalidade not in MODALIDADES:
        erros.append("modalidade invalida: %s" % modalidade)
    if representacao not in REPRESENTACOES:
        erros.append("representacao invalida: %s" % representacao)
    if finalidade not in FINALIDADES:
        erros.append("finalidade invalida: %s" % finalidade)
    if erros:
        raise SystemExit("; ".join(erros))


def rotear(modalidade, representacao, finalidade, topologia=None, papeis=None):
    """Devolve o que verificar, o que nao verificar, e o motivo de cada dispensa.

    topologia e OPCIONAL e, quando declarada, manda nas dispensas que dependem dela.
    Sem declaracao, o comportamento e o de antes."""
    valida(modalidade, representacao, finalidade)
    topo = valida_topologia(topologia)
    papeis_declarados = valida_papeis(papeis)
    i = FINALIDADES.index(finalidade)
    inap = dict(INAPLICAVEIS.get(representacao, {}))
    if topo:
        # borda proibida significa casca FECHADA: as dispensas que existiam "porque
        # superficie tem borda por definicao" deixam de valer, e quem decide volta a ser
        # a finalidade.
        if topo["borda"] == "proibida":
            for nome in ("zero_nao_manifold", "malha_estanque"):
                inap.pop(nome, None)
        if topo["estanqueidade"] == "nao_se_aplica":
            inap["malha_estanque"] = ("topologia declarada: estanqueidade nao se aplica a "
                                      "esta peca")

    exigidas, dispensadas = [], {}
    for nome, linha in POR_FINALIDADE.items():
        v = linha[i]
        if nome in inap:
            dispensadas[nome] = "representacao %s: %s" % (representacao, inap[nome])
        elif v is True:
            exigidas.append(nome)
        elif v is False:
            dispensadas[nome] = "finalidade %s nao exige" % finalidade
        else:
            dispensadas[nome] = "nao se aplica a finalidade %s" % finalidade

    for nome in POR_MODALIDADE.get(modalidade, ()):
        if nome not in exigidas:
            exigidas.append(nome)
    for nome in POR_REPRESENTACAO.get(representacao, ()):
        if nome not in exigidas:
            exigidas.append(nome)

    if topo:
        if "topologia" not in exigidas:
            exigidas.append("topologia")
        # estanqueidade exigida manda, mesmo que a finalidade sozinha nao exigisse
        if topo["estanqueidade"] == "exigida" and "malha_estanque" not in exigidas:
            exigidas.append("malha_estanque")
            dispensadas.pop("malha_estanque", None)

    # o papel de cada verificacao exigida: DECISIVA por padrao, e o caso pode declarar
    # INFORMATIVA. Declarar papel para verificacao nao exigida e erro de especificacao,
    # porque significaria opinar sobre algo que nem sera feito.
    fora_do_roteamento = sorted(set(papeis_declarados) - set(exigidas))
    if fora_do_roteamento:
        raise SystemExit("papel declarado para verificacao que nao esta no roteamento: %s. "
                         "Exigidas: %s" % (fora_do_roteamento, sorted(exigidas)))
    mapa_de_papeis = {n: papeis_declarados.get(n, "DECISIVA") for n in exigidas}
    for nome in dispensadas:
        mapa_de_papeis[nome] = "NAO_APLICAVEL"
    decisivas = sorted(n for n in exigidas if mapa_de_papeis[n] == "DECISIVA")
    informativas = sorted(n for n in exigidas if mapa_de_papeis[n] == "INFORMATIVA")

    return {
        "classificacao": {"modalidade": modalidade, "representacao": representacao,
                          "finalidade": finalidade},
        "topologia_declarada": topo,
        "exigidas": sorted(exigidas),
        "papeis": dict(sorted(mapa_de_papeis.items())),
        "decisivas": decisivas,
        "informativas": informativas,
        "dispensadas": dict(sorted(dispensadas.items())),
        "nota": ("Verificacao dispensada nao e verificacao aprovada: ela nao se aplica a esta "
                 "classificacao. Se a classificacao estiver errada, o roteamento inteiro esta "
                 "errado, e e por isso que a classificacao e o passo 1 do nucleo."),
        "nota_de_papel": ("Papel nao altera medida. A mesma geometria produz o mesmo "
                          "numero em DECISIVA e em INFORMATIVA; o que muda e se aquele "
                          "numero entra nos bloqueios. Verificacao INFORMATIVA aparece "
                          "medida no relatorio e nunca barra."),
        "nota_de_topologia": ("Representacao nao e topologia. 'superficie' nao implica casca "
                              "aberta: casca fechada sem solido tambem e superficie, e nela "
                              "borda e proibida. Quando a topologia nao e declarada, nada e "
                              "deduzido sobre borda."),
    }


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) in (4, 5):
        topo = json.loads(sys.argv[4]) if len(sys.argv) == 5 else None
        print(json.dumps(rotear(*sys.argv[1:4], topologia=topo), indent=1,
                         ensure_ascii=False))
    else:
        print("uso: python matriz.py <modalidade> <representacao> <finalidade> "
              "[topologia-json]")
        print('exemplo de topologia: {"borda":"proibida","estanqueidade":"exigida"}')
        print("modalidades  :", ", ".join(MODALIDADES))
        print("representacoes:", ", ".join(REPRESENTACOES))
        print("finalidades  :", ", ".join(FINALIDADES))
