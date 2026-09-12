# -*- coding: utf-8 -*-
"""testa_paridade_validador.py - prova que o validador ESPELHA o verificador.

RODA FORA DO BLENDER, no Python do hospedeiro. Precisa de numpy, porque importa o
proprio `check_intent.py` desta versão.

POR QUE ESTE ARQUIVO EXISTE. `valida_requisitos.py` anuncia, no seu proprio
cabecalho, que espelha o esquema de `check_intent.py`. Uma revisao independente
mediu que ele NAO espelhava, e em dois sentidos opostos:

  - aceitava o que o verificador recusa: eixo "W", NaN, tolerancia negativa,
    caixa_min >= caixa_max, `entre` com um caminho so;
  - recusava o que o verificador aceita: numero escrito como texto ("30"), que o
    verificador converte com float() sem reclamar.

Os dois lados enganam, e o primeiro engana pior: um OK do validador convida a
chamada que vai falhar la dentro. "Eu conferi o fonte tipo por tipo" nao e prova de
paridade — paridade se mede comparando as duas respostas na mesma entrada.

O QUE ESTE TESTE DECIDE, por caso:

  ESPELHO_OK        as duas respostas concordam
  EXTRA_DECLARADO   o verificador aceita, o validador recusa, e a recusa e de uma
                    checagem declarada como ALEM do espelho (ver EXTRAS_ALEM_DO_ESPELHO
                    em valida_requisitos.py)
  FALHA_PERMISSIVO  o verificador RECUSA e o validador diz OK  <- o defeito grave
  FALHA_ESTRITO     o verificador aceita, o validador recusa sem extra que justifique

Uso:
    python scripts/testa_paridade_validador.py [--relatorio saida.json]
"""
import argparse
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "verificadores"))

import valida_requisitos as V                                     # noqa: E402

NAN = float("nan")
INF = float("inf")

# Um requisito BEM FORMADO de cada tipo. As mutacoes saem daqui, entao estes casos
# tambem servem de controle positivo: se um deles ja nascer recusado, o teste avisa.
BASES = {
    "caixa": {"id": "R1", "tipo": "caixa", "valor": [60.0, 40.0, 20.0], "tol_mm": 0.05},
    "volume": {"id": "R2", "tipo": "volume", "valor": 1000.0, "tol_mm3": 1.0},
    "n_solidos": {"id": "R3", "tipo": "n_solidos", "valor": 1},
    "furo": {"id": "R4", "tipo": "furo", "eixo": "Z", "plano": 5.0,
             "posicao": [10.0, 10.0], "diametro": 6.0, "tol_pos_mm": 0.2},
    "n_furos_no_plano": {"id": "R5", "tipo": "n_furos_no_plano", "eixo": "Z",
                         "plano": 5.0, "valor": 2},
    "distancia_entre_furos": {"id": "R6", "tipo": "distancia_entre_furos", "eixo": "Z",
                              "plano": 5.0, "valor": 20.0, "tol_mm": 0.2},
    "regiao_intacta": {"id": "R7", "tipo": "regiao_intacta",
                       "caixa_min": [0.0, 0.0, 0.0], "caixa_max": [10.0, 10.0, 10.0],
                       "tol_fracao": 1e-9},
    "interferencia": {"id": "R8", "tipo": "interferencia",
                      "entre": ["a.stl", "b.stl"], "tol_mm3": 1.0},
}

# Valores ruins aplicados a CADA campo de CADA tipo. A bateria e cega de proposito:
# ela nao sabe qual campo esta mexendo, e por isso encontra combinacao que eu nao
# teria pensado em escrever a mao.
RUINS = [("ausente", "<<REMOVER>>"), ("nulo", None), ("texto", "abc"),
         ("texto_numerico", "30"), ("nan", NAN), ("infinito", INF),
         ("negativo", -1.0), ("zero", 0.0), ("booleano", True),
         ("lista_vazia", []), ("lista_curta", [1.0]), ("lista_longa", [1.0, 2.0, 3.0, 4.0]),
         ("dicionario", {"x": 1}), ("fracionario", 1.9)]

# Casos que a bateria cega nao alcanca, cada um vindo de um achado concreto.
ESPECIAIS = [
    ("eixo_fora_do_vocabulario", dict(BASES["furo"], eixo="W")),
    ("eixo_minusculo_e_valido", dict(BASES["furo"], eixo="z")),
    ("eixo_com_prosa", dict(BASES["furo"], eixo="eixo x")),
    ("caixa_invertida", dict(BASES["regiao_intacta"], caixa_min=[10.0, 0.0, 0.0])),
    ("caixa_degenerada_igual", dict(BASES["regiao_intacta"],
                                    caixa_min=[0.0, 0.0, 0.0],
                                    caixa_max=[10.0, 10.0, 0.0])),
    ("tolerancia_negativa", dict(BASES["caixa"], tol_mm=-0.05)),
    ("tolerancia_nan", dict(BASES["caixa"], tol_mm=NAN)),
    ("tolerancia_infinita", dict(BASES["caixa"], tol_mm=INF)),
    ("tolerancia_zero_e_valida", dict(BASES["caixa"], tol_mm=0.0)),
    ("tolerancia_texto", dict(BASES["caixa"], tol_mm="0.05")),
    ("entre_com_um_caminho", dict(BASES["interferencia"], entre=["a.stl"])),
    ("entre_como_texto", dict(BASES["interferencia"], entre="a.stl")),
    ("entre_com_tres", dict(BASES["interferencia"], entre=["a", "b", "c"])),
    ("interferencia_por_com", {"id": "R8", "tipo": "interferencia", "com": "b.stl",
                               "tol_mm3": 1.0}),
    ("interferencia_sem_nada", {"id": "R8", "tipo": "interferencia", "tol_mm3": 1.0}),
    ("sem_id", {k: v for k, v in BASES["caixa"].items() if k != "id"}),
    ("id_vazio", dict(BASES["caixa"], id="")),
    ("tipo_inexistente", {"id": "R9", "tipo": "parafuso", "valor": 1}),
    ("contagem_fracionaria", dict(BASES["n_solidos"], valor=1.9)),
    ("contagem_negativa", dict(BASES["n_solidos"], valor=-1)),
    ("contagem_como_texto", dict(BASES["n_solidos"], valor="3")),
    ("tolerancia_de_outro_tipo", dict(BASES["n_solidos"], tol_mm=0.1)),
    ("regiao_intacta_com_tol_errada",
     {"id": "R7", "tipo": "regiao_intacta", "caixa_min": [0.0, 0.0, 0.0],
      "caixa_max": [10.0, 10.0, 10.0], "tol_mm3": 1.0}),
]


def casos():
    """Gera (nome, requisito). Bases, bateria cega em cada campo, e os especiais."""
    for t, base in sorted(BASES.items()):
        yield "base_%s" % t, dict(base)
    for t, base in sorted(BASES.items()):
        campos = [c for c in base if c not in ("id", "tipo")]
        for campo in campos:
            for etiqueta, valor in RUINS:
                r = dict(base)
                if valor == "<<REMOVER>>":
                    r.pop(campo, None)
                else:
                    r[campo] = valor
                yield "%s.%s=%s" % (t, campo, etiqueta), r
    for nome, r in ESPECIAIS:
        yield "especial.%s" % nome, dict(r)


def julga(req, valida_esquema):
    """Compara as duas respostas na MESMA entrada."""
    try:
        do_verificador = list(valida_esquema(dict(req)))
    except Exception as e:                       # excecao tambem e recusa, e das piores
        do_verificador = ["EXCECAO %s: %s" % (type(e).__name__, e)]
    avisos = []
    try:
        do_validador = V.valida_estrutura({"requisitos": [dict(req)]}, avisos)
    except Exception as e:
        return {"estado": "FALHA_ESTRITO", "avisos": avisos,
                "verificador": do_verificador,
                "validador": ["EXCECAO %s: %s" % (type(e).__name__, e)],
                "nota": ("o validador levantou excecao: ele existe justamente para "
                         "que ninguem receba traceback em vez de veredito")}
    v_recusa, d_recusa = bool(do_verificador), bool(do_validador)
    r = {"verificador": do_verificador, "validador": do_validador, "avisos": avisos}
    if v_recusa == d_recusa:
        r["estado"] = "ESPELHO_OK"
        return r
    if v_recusa and not d_recusa:
        r["estado"] = "FALHA_PERMISSIVO"
        r["nota"] = ("o verificador RECUSA e o validador disse OK. Este e o lado que "
                     "engana pior: o OK convida a chamada que vai falhar la dentro.")
        return r
    sem_extra = [q for q in do_validador
                 if not any(m in q for m in V.EXTRAS_ALEM_DO_ESPELHO)]
    if sem_extra:
        r["estado"] = "FALHA_ESTRITO"
        r["problemas_sem_extra_que_justifique"] = sem_extra
        r["nota"] = ("o verificador aceita e o validador recusa por motivo que nao "
                     "esta declarado como extra. Recusar o que ele aceita e a mesma "
                     "divergencia, com o sinal trocado.")
    else:
        r["estado"] = "EXTRA_DECLARADO"
    return r


def paridade_da_tabela_de_tolerancia():
    """A tabela do validador tem que ser IGUAL a extraida do fonte do verificador.

    Esta checagem existe porque a tabela transcrita a mao estava errada em `furo`, e
    o erro sobreviveu a uma rodada inteira de revisao: como "tolerancia lida por
    tipo" e uma checagem ALEM do espelho, ela ficava protegida pela lista de extras,
    ou seja, por uma afirmacao minha. Extras precisam de oraculo tambem."""
    import extrai_tolerancias as X
    bruto = X.extrai()
    med = X.como_tupla(bruto)
    declarado = {k: tuple(sorted(v)) for k, v in V.TOLERANCIA_POR_TIPO.items()}
    medido = {k: tuple(sorted(v)) for k, v in med.items()}
    faltando = sorted(set(medido) - set(declarado))
    sobrando = sorted(set(declarado) - set(medido))
    divergentes = {k: {"declarado": list(declarado[k]), "medido": list(medido[k])}
                   for k in sorted(set(declarado) & set(medido))
                   if declarado[k] != medido[k]}

    # Acrescentado depois da quarta revisao: os NOMES eram comparados e os VALORES
    # padrao nao. Padrao que decide na omissao e numero que decide, e ja aprovou
    # requisito de furo numa sessao limpa; se ele divergir do fonte, a referencia
    # promete uma margem e o verificador aplica outra.
    med_pad = X.padroes(bruto)
    dec_pad = {}
    for tipo, m in V.PADRAO_DA_TOLERANCIA.items():
        d = {}
        for tol, v in m.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                d[tol] = ("expressao", "".join(str(v).split()))
            else:
                d[tol] = ("numero", float(v))
        dec_pad[tipo] = d
    pad_divergentes = {}
    for tipo in sorted(set(med_pad) | set(dec_pad)):
        a, b = dec_pad.get(tipo, {}), med_pad.get(tipo, {})
        if set(a) != set(b):
            pad_divergentes[tipo] = {"declarado": a, "medido": b,
                                     "motivo": "conjunto de tolerancias diferente"}
            continue
        dif = {t: {"declarado": a[t], "medido": b[t]} for t in sorted(a)
               if a[t][0] != b[t][0]
               or (a[t][0] == "numero" and abs(a[t][1] - b[t][1]) > 1e-12)
               or (a[t][0] == "expressao" and a[t][1] != b[t][1])}
        if dif:
            pad_divergentes[tipo] = dif

    return {"tipos_no_verificador_e_nao_no_validador": faltando,
            "tipos_no_validador_e_nao_no_verificador": sobrando,
            "divergentes": divergentes,
            "padroes_divergentes": pad_divergentes,
            "padroes_medidos": {k: {t: list(v) for t, v in m.items()}
                                for k, m in sorted(med_pad.items())},
            "estado": ("ATENDIDO" if not (faltando or sobrando or divergentes
                                          or pad_divergentes) else "FALHOU"),
            "por_que": ("tolerancia que o verificador LE e o validador recusa e um "
                        "numero que decide sendo apagado; o contrario e margem "
                        "prometida que ninguem consulta. E padrao divergente e "
                        "margem prometida diferente da aplicada, no caso mais "
                        "comum de todos: o de quem nao declarou nada")}


def roda():
    from check_intent import valida_esquema
    rel = {"validador": os.path.abspath(V.__file__),
           "verificador": os.path.abspath(sys.modules["check_intent"].__file__),
           "extras_declarados": list(V.EXTRAS_ALEM_DO_ESPELHO),
           "casos": []}
    for nome, req in casos():
        d = julga(req, valida_esquema)
        d["caso"] = nome
        d["requisito"] = json.loads(json.dumps(req, default=repr))
        rel["casos"].append(d)

    por_estado = {}
    for d in rel["casos"]:
        por_estado[d["estado"]] = por_estado.get(d["estado"], 0) + 1
    rel["por_estado"] = por_estado
    rel["n_casos"] = len(rel["casos"])

    # controle positivo: os oito requisitos bem formados tem que passar nos DOIS
    bases_recusadas = [d["caso"] for d in rel["casos"]
                       if d["caso"].startswith("base_") and d["estado"] != "ESPELHO_OK"]
    bases_com_problema = [d["caso"] for d in rel["casos"]
                          if d["caso"].startswith("base_")
                          and (d["verificador"] or d["validador"])]
    rel["controle_positivo"] = {
        "bases_divergentes": bases_recusadas,
        "bases_recusadas_por_algum_dos_dois": bases_com_problema,
        "por_que": ("se um requisito bem formado ja nascer recusado, toda a bateria "
                    "de mutacao mede a partir de um caso quebrado e a concordancia "
                    "vira coincidencia")}

    rel["paridade_da_tabela_de_tolerancia"] = paridade_da_tabela_de_tolerancia()

    falhas = [d for d in rel["casos"]
              if d["estado"] in ("FALHA_PERMISSIVO", "FALHA_ESTRITO")]
    rel["n_falhas"] = len(falhas)
    rel["falhas"] = falhas
    if rel["paridade_da_tabela_de_tolerancia"]["estado"] != "ATENDIDO":
        rel["veredito"] = "FALHOU"
        rel["motivo"] = ("a tabela de tolerancia por tipo divergiu do fonte do "
                         "verificador: nomes %s; padroes %s"
                         % (rel["paridade_da_tabela_de_tolerancia"]["divergentes"],
                            rel["paridade_da_tabela_de_tolerancia"]
                            ["padroes_divergentes"]))
    elif bases_com_problema:
        rel["veredito"] = "FALHOU"
        rel["motivo"] = ("requisito bem formado recusado: %s" % bases_com_problema)
    elif falhas:
        rel["veredito"] = "FALHOU"
    elif not rel["casos"]:
        rel["veredito"] = "SEM_CASO"
    else:
        rel["veredito"] = "ATENDIDO"
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relatorio")
    a = ap.parse_args()
    rel = roda()
    if a.relatorio:
        os.makedirs(os.path.dirname(os.path.abspath(a.relatorio)), exist_ok=True)
        io.open(a.relatorio, "w", encoding="utf-8").write(
            json.dumps(rel, ensure_ascii=False, indent=1))
    enxuto = {k: rel[k] for k in ("veredito", "n_casos", "por_estado", "n_falhas")}
    enxuto["paridade_da_tabela_de_tolerancia"] = \
        rel["paridade_da_tabela_de_tolerancia"]["estado"]
    enxuto["divergentes"] = rel["paridade_da_tabela_de_tolerancia"]["divergentes"]
    enxuto["padroes_divergentes"] = \
        rel["paridade_da_tabela_de_tolerancia"]["padroes_divergentes"]
    enxuto["falhas"] = [{"caso": d["caso"], "estado": d["estado"],
                         "verificador": d["verificador"][:2],
                         "validador": d["validador"][:2]} for d in rel["falhas"][:12]]
    enxuto["controle_positivo"] = rel["controle_positivo"]["bases_recusadas_por_algum_dos_dois"]
    print(json.dumps(enxuto, ensure_ascii=False, indent=1))
    return 0 if rel["veredito"] == "ATENDIDO" else 1


if __name__ == "__main__":
    sys.exit(main())
