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


def rotear(modalidade, representacao, finalidade):
    """Devolve o que verificar, o que nao verificar, e o motivo de cada dispensa."""
    valida(modalidade, representacao, finalidade)
    i = FINALIDADES.index(finalidade)
    inap = INAPLICAVEIS.get(representacao, {})

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

    return {
        "classificacao": {"modalidade": modalidade, "representacao": representacao,
                          "finalidade": finalidade},
        "exigidas": sorted(exigidas),
        "dispensadas": dict(sorted(dispensadas.items())),
        "nota": ("Verificacao dispensada nao e verificacao aprovada: ela nao se aplica a esta "
                 "classificacao. Se a classificacao estiver errada, o roteamento inteiro esta "
                 "errado, e e por isso que a classificacao e o passo 1 do nucleo."),
    }


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) == 4:
        print(json.dumps(rotear(*sys.argv[1:4]), indent=1, ensure_ascii=False))
    else:
        print("uso: python matriz.py <modalidade> <representacao> <finalidade>")
        print("modalidades  :", ", ".join(MODALIDADES))
        print("representacoes:", ", ".join(REPRESENTACOES))
        print("finalidades  :", ", ".join(FINALIDADES))
