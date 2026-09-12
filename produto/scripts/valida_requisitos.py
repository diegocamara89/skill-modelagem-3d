# -*- coding: utf-8 -*-
"""valida_requisitos.py - confere a FORMA do arquivo de requisitos antes de verificar.

RODA FORA DO BLENDER, no Python do hospedeiro.

POR QUE ESTE ARQUIVO EXISTE. Um ensaio de sessao limpa passou uma LISTA nua de
requisitos, que e a leitura mais natural do formato, e recebeu de volta um traceback
nao tratado:

    AttributeError: 'list' object has no attribute 'get'

Isso contradiz o contrato que o proprio pacote anuncia — declaracao nao executavel
sai como ESPEC_INVALIDA, e a ferramenta recusa em vez de deixar descobrir pelo
resultado. As divergencias de `check_intent.py` em relacao a base estao registradas em
PROVENIENCIA.json. Esta guarda valida o envelope antes da chamada.

Este auxiliar NAO verifica geometria e NAO substitui `check_intent.py`. Ele responde
uma pergunta so: o arquivo esta na forma que o verificador espera?

Uso:
    python scripts/valida_requisitos.py req.json
    python scripts/valida_requisitos.py --tipos          # lista os tipos e campos

Como modulo:
    from valida_requisitos import valida_arquivo
"""
import argparse
import io
import json
import os
import sys

# Espelha o ESQUEMA de check_intent.py. O numero e a quantidade de valores exigida;
# "eixo" indica campo de texto. Mantido aqui de proposito, em vez de importado: este
# auxiliar tem que funcionar mesmo se o verificador nao puder ser carregado.
CAMPOS_POR_TIPO = {
    "caixa": {"valor": 3},
    "volume": {"valor": 1},
    "n_solidos": {"valor": 1},
    "furo": {"eixo": "eixo", "plano": 1, "posicao": 2, "diametro": 1},
    "n_furos_no_plano": {"eixo": "eixo", "plano": 1, "valor": 1},
    "distancia_entre_furos": {"eixo": "eixo", "plano": 1, "valor": 1},
    "regiao_intacta": {"caixa_min": 3, "caixa_max": 3},
    "interferencia": {},
}

# Qual tolerancia cada tipo REALMENTE le, e o valor que decide quando ninguem
# declara nada.
#
# DUAS correcoes aqui, e a segunda ensina mais que a primeira.
#
# 1. A versao original aceitava QUALQUER nome de tolerancia para QUALQUER tipo. A
#    referencia documentava `regiao_intacta` com `tol_mm3` e o verificador le SOMENTE
#    `tol_fracao`: o numero documentado nao participava da decisao e o validador
#    dizia OK.
# 2. A correcao daquilo foi uma tabela TRANSCRITA a mao, com o comentario "conferido
#    no fonte tipo por tipo". Uma sessao limpa mediu que a transcricao estava errada
#    em `furo`, que le `tol_mm` como tolerancia de DIAMETRO e decide com ela. O
#    validador passou a RECUSAR um numero que o verificador usa para decidir, e a
#    referencia garantia o contrario. E o teste de paridade nao pegou, porque essa
#    checagem estava na lista de extras — protegida por uma afirmacao minha.
#
# Por isso esta tabela deixou de ser afirmacao: `scripts/extrai_tolerancias.py` a
# extrai do fonte do verificador, e `scripts/testa_paridade_validador.py` reprova se
# as duas divergirem. Ela continua LITERAL aqui porque este auxiliar tem que
# funcionar mesmo sem conseguir carregar nem ler o verificador.
TOLERANCIA_POR_TIPO = {
    "caixa": ("tol_mm",),
    "volume": ("tol_mm3",),
    "n_solidos": (),                       # contagem: exata
    "furo": ("tol_pos_mm", "tol_mm", "circularidade_min"),
    "n_furos_no_plano": (),                # contagem: exata
    "distancia_entre_furos": ("tol_mm",),
    "regiao_intacta": ("tol_fracao",),
    "interferencia": ("tol_mm3",),
}

# O valor que DECIDE quando o requisito nao declara a tolerancia. Extraido do mesmo
# fonte. Nao declarar nao significa "sem margem": significa aceitar esta, e ela
# precisa estar escrita em algum lugar. Os dois requisitos de furo de uma sessao
# limpa foram aprovados por uma tolerancia de diametro de 0,2 que ninguem escolheu e
# que nao aparecia em nenhuma referencia.
PADRAO_DA_TOLERANCIA = {
    "caixa": {"tol_mm": 0.05},
    # o valor VERBATIM do fonte, nao a parafrase: quando o padrao e expressao, a
    # comparacao com a extracao e textual, e "1% do volume esperado" nao e comparavel
    # com nada.  e o volume esperado do requisito. A leitura em portugues fica na
    # referencia, que e onde ela serve.
    "volume": {"tol_mm3": "max(1.0, 0.01 * esp)"},
    "n_solidos": {},
    "furo": {"tol_pos_mm": 0.2, "tol_mm": 0.2, "circularidade_min": 0.9},
    "n_furos_no_plano": {},
    "distancia_entre_furos": {"tol_mm": 0.2},
    "regiao_intacta": {"tol_fracao": 1e-9},
    "interferencia": {"tol_mm3": 0.0},
}

# O nome de ENTRADA e o de SAIDA nem sempre coincidem, e isso custou tempo a quem
# leu o relatorio: em `furo`, `tol_mm` entra e sai como `tol_diam_mm`.
NOME_NA_SAIDA = {("furo", "tol_mm"): "tol_diam_mm"}
# A tupla e a MESMA de check_intent.py, na mesma ordem, e nao derivada do mapa
# acima: o verificador confere o valor de toda tolerancia que reconhece, nao apenas
# das que le para aquele tipo.
TOLERANCIAS = ("tol_mm", "tol_mm3", "tol_pos_mm", "tol_fracao", "circularidade_min")
EIXOS = ("X", "Y", "Z")

# CHECAGENS ALEM DO ESPELHO. Este auxiliar confere tudo o que o verificador confere,
# e mais um punhado de coisas que ele NAO confere. Isso e legitimo — recusar cedo
# especificacao que passaria pelo esquema e morreria de outra forma e o proposito
# aqui — mas so e legitimo se estiver DECLARADO, porque senao vira a mesma
# divergencia do achado, com o sinal trocado.
#
# Cada texto abaixo e um pedaco literal da mensagem correspondente. O teste
# `testa_paridade_validador.py` usa esta lista para separar "extra deliberado" de
# "validador mais estrito que o verificador sem motivo declarado". Se uma mensagem
# mudar e o pedaco parar de casar, o teste ACUSA em vez de deixar passar.
EXTRAS_ALEM_DO_ESPELHO = (
    "nao declara tolerancia que o verificador LEIA",   # nome de tolerancia por tipo
    "que o verificador NAO le para este tipo",
    "e de CONTAGEM, comparada de forma exata",
    "e CONTAGEM e traz valor fracionario",             # contagem inteira e exata
    "traz contagem negativa",
    "identificador repetido",                          # ids repetidos entre requisitos
    "que nao existe. Tipos:",                          # tipo fora do vocabulario
)


def _numero_finito(v):
    """(ok, x, motivo). Aceita o que float() aceita, como o verificador.

    De proposito NAO usa isinstance: o verificador chama float(v), e portanto ACEITA
    "30" e True. Recusar aqui o que ele aceita e divergencia igual a aceitar o que
    ele recusa, e foi o outro lado do mesmo achado."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return False, None, "tem que ser numero, e veio %r" % (v,)
    if x != x or x in (float("inf"), float("-inf")):
        return False, None, "nao e finito: %r" % (v,)
    return True, x, None


def _avisa_forma_fragil(avisos, onde, campo, v):
    """Forma que o verificador aceita e que ainda assim merece ser dita."""
    if isinstance(v, bool):
        avisos.append("%s: %r veio como booleano %r; o verificador converte para "
                      "%.1f, mas escrever medida como True/False esconde a intencao."
                      % (onde, campo, v, float(v)))
    elif isinstance(v, str):
        avisos.append("%s: %r veio como texto %r; o verificador converte com float() "
                      "e aceita, porem numero escrito como texto quebra no primeiro "
                      "separador decimal trocado." % (onde, campo, v))
EXIGE_REFERENCIA = ("regiao_intacta",)

# `interferencia` aceita 'entre' com dois caminhos, OU 'com' com um. Sem nenhum dos
# dois o verificador nao tem o que comparar. A versao anterior deste validador nao
# exigia nada, e por isso podia devolver OK para especificacao que o verificador
# rejeita.
ALTERNATIVAS_POR_TIPO = {
    "interferencia": (("entre", "com"),),
}

# Tipos de CONTAGEM: o valor e inteiro e a comparacao e exata. Exigir tolerancia
# aqui seria erro, e foi um erro que este proprio auxiliar cometeu na primeira
# versao: ele recusava um requisito `n_solidos` que o verificador ACEITA. Contar
# tres corpos e exato; medir 30 milimetros nao e. A regra e a mesma do metodo:
# igualdade e legitima em contagem inteira e proibida em medida.
TIPOS_DE_CONTAGEM = tuple(t for t, ts in TOLERANCIA_POR_TIPO.items() if not ts)


def valida_estrutura(dados, avisos=None):
    """Devolve lista de problemas. Vazia significa forma aceitavel.

    `avisos` opcional: lista onde entram formas que o verificador ACEITA mas que sao
    fragis (numero escrito como texto, booleano no lugar de numero). Aviso NAO e
    problema: reprovar aqui o que o verificador aceita e a mesma divergencia do
    achado, com o sinal trocado."""
    p = []
    if avisos is None:
        avisos = []
    if isinstance(dados, list):
        p.append("o arquivo e uma LISTA nua. O verificador espera um OBJETO com a "
                 "chave 'requisitos': {\"requisitos\": [ ... ]}. Lista nua produz "
                 "erro nao tratado dentro do verificador.")
        return p
    if not isinstance(dados, dict):
        p.append("o arquivo tem que ser um objeto JSON, e veio %s" % type(dados).__name__)
        return p
    reqs = dados.get("requisitos")
    if reqs is None:
        p.append("falta a chave 'requisitos'. Chaves presentes: %s" % sorted(dados))
        return p
    if not isinstance(reqs, list):
        p.append("'requisitos' tem que ser uma lista, e veio %s" % type(reqs).__name__)
        return p
    if not reqs:
        p.append("'requisitos' esta vazia. Requisito que ninguem escreveu nao e "
                 "verificado por ninguem: a lista vazia nao prova nada.")
        return p

    vistos = {}
    for i, r in enumerate(reqs):
        onde = "requisitos[%d]" % i
        if not isinstance(r, dict):
            p.append("%s nao e objeto: %s" % (onde, type(r).__name__))
            continue
        rid = r.get("id")
        if not rid:
            p.append("%s nao tem 'id'" % onde)
        else:
            vistos.setdefault(rid, []).append(i)
        tipo = r.get("tipo")
        if not tipo:
            p.append("%s nao tem 'tipo'" % onde)
            continue
        if tipo not in CAMPOS_POR_TIPO:
            p.append("%s tem tipo %r, que nao existe. Tipos: %s"
                     % (onde, tipo, sorted(CAMPOS_POR_TIPO)))
            continue
        opcionais = {
            "caixa": {"tol_mm"}, "volume": {"tol_mm3"}, "n_solidos": set(),
            "furo": {"tol_mm", "tol_pos_mm", "circularidade_min", "segunda_secao_mm"},
            "n_furos_no_plano": set(), "distancia_entre_furos": {"tol_mm", "entre"},
            "regiao_intacta": {"tol_fracao"}, "interferencia": {"tol_mm3", "entre", "com"},
        }
        extras = set(r) - (set(CAMPOS_POR_TIPO[tipo]) | {"id", "tipo", "descricao"} | opcionais[tipo])
        if extras:
            p.append("%s campos nao suportados para %s: %s" % (onde, tipo, ", ".join(sorted(extras))))
        for campo, forma in CAMPOS_POR_TIPO[tipo].items():
            if campo not in r:
                p.append("%s de tipo %r nao tem o campo obrigatorio %r"
                         % (onde, tipo, campo))
                continue
            v = r[campo]
            if forma == "eixo":
                # ESPELHO: o verificador faz str(v).upper() in {"X","Y","Z"}. A versao
                # anterior daqui aceitava QUALQUER texto nao vazio, entao eixo "W" ou
                # "eixo x" passava a validacao e morria dentro do verificador com
                # KeyError, o oposto do contrato anunciado.
                if str(v).upper() not in EIXOS:
                    p.append("%s: %r tem que ser X, Y ou Z, e veio %r"
                             % (onde, campo, v))
            elif forma == 1:
                ok, x, motivo = _numero_finito(v)
                if not ok:
                    p.append("%s: %r %s" % (onde, campo, motivo))
                else:
                    _avisa_forma_fragil(avisos, onde, campo, v)
                    if tipo in TIPOS_DE_CONTAGEM and campo == "valor":
                        if not float(x).is_integer():
                            p.append("%s de tipo %r e CONTAGEM e traz valor "
                                     "fracionario %r. O verificador converte com "
                                     "int() e aprovaria por truncamento; contagem "
                                     "fracionaria e especificacao invalida."
                                     % (onde, tipo, v))
                        elif x < 0:
                            p.append("%s de tipo %r traz contagem negativa %r"
                                     % (onde, tipo, v))
            else:
                if not isinstance(v, (list, tuple)):
                    p.append("%s: %r tem que ser lista de %d numeros, e veio %s"
                             % (onde, campo, forma, type(v).__name__))
                elif len(v) != forma:
                    p.append("%s: %r tem que ter exatamente %d valores, e veio %d"
                             % (onde, campo, forma, len(v)))
                else:
                    for j, x in enumerate(v):
                        ok, _, motivo = _numero_finito(x)
                        if not ok:
                            p.append("%s: %r[%d] %s" % (onde, campo, j, motivo))
                        else:
                            _avisa_forma_fragil(avisos, onde,
                                                "%s[%d]" % (campo, j), x)

        # ESPELHO: VALOR de tolerancia. O verificador exige numero finito NAO
        # NEGATIVO. A versao anterior daqui conferia o NOME da tolerancia e nunca o
        # valor: tol_mm = -1 e tol_mm = NaN saiam como forma OK. Margem negativa
        # reprova qualquer medida, e margem NaN torna toda comparacao falsa: nos dois
        # casos o requisito decide, e decide pelo motivo errado.
        for t in TOLERANCIAS:
            if t in r:
                ok, x, motivo = _numero_finito(r[t])
                if not ok or x < 0:
                    p.append("%s: %r tem que ser numero finito nao negativo, e veio "
                             "%r" % (onde, t, r[t]))
                else:
                    _avisa_forma_fragil(avisos, onde, t, r[t])

        # ESPELHO: caixa_min < caixa_max em todos os eixos. Sem isto, uma caixa
        # invertida saia como forma OK aqui e era recusada la, depois de o agente ja
        # ter confiado no OK.
        if tipo == "regiao_intacta" and not p:
            try:
                lo = [float(x) for x in r["caixa_min"]]
                hi = [float(x) for x in r["caixa_max"]]
            except (TypeError, ValueError, KeyError):
                lo = hi = None
            if lo and hi and any(m >= M for m, M in zip(lo, hi)):
                p.append("%s: caixa_min tem que ser menor que caixa_max em todos os "
                         "eixos, e veio min=%s max=%s" % (onde, lo, hi))

        # ESPELHO: 'entre' precisa ter DOIS caminhos. A versao anterior aceitava a
        # simples PRESENCA da chave, entao entre: [a] passava aqui e era recusado la.
        if tipo == "interferencia":
            ent = r.get("entre")
            tem_entre = isinstance(ent, (list, tuple)) and len(ent) == 2
            if not tem_entre and not r.get("com"):
                p.append("%s de tipo 'interferencia' exige 'entre' com DOIS caminhos, "
                         "ou 'com' com um. Presenca da chave nao basta: veio entre=%r "
                         "com=%r." % (onde, ent, r.get("com")))

        aceitas = TOLERANCIA_POR_TIPO.get(tipo, ())
        presentes = [t for t in TOLERANCIAS if t in r]
        if aceitas and not any(t in r for t in aceitas):
            p.append("%s de tipo %r nao declara tolerancia que o verificador LEIA. "
                     "Para este tipo ele le %s%s. Comparacao de medida sem margem "
                     "declarada nao decide nada."
                     % (onde, tipo, list(aceitas),
                        (", e o requisito traz %s, que sao ignoradas para este tipo"
                         % presentes) if presentes else ""))
        ignoradas = [t for t in presentes if t not in aceitas]
        if aceitas and ignoradas and any(t in r for t in aceitas):
            p.append("%s de tipo %r traz %s, que o verificador NAO le para este tipo. "
                     "Ele le %s. Tolerancia ignorada e numero que nao decide nada."
                     % (onde, tipo, ignoradas, list(aceitas)))
        if not aceitas and presentes:
            p.append("%s de tipo %r e de CONTAGEM, comparada de forma exata, e traz "
                     "%s. Tolerancia aqui nao e lida e sugere margem que nao existe."
                     % (onde, tipo, presentes))

    for rid, idx in sorted(vistos.items()):
        if len(idx) > 1:
            p.append("identificador repetido %r nos indices %s. O verificador recusa "
                     "ids repetidos, porque a evidencia de um sobrescreveria a do "
                     "outro." % (rid, idx))
    return p


def precisa_de_referencia(dados):
    """Tipos que exigem --referencia na chamada de check_intent.py."""
    if not isinstance(dados, dict):
        return []
    return sorted({r.get("tipo") for r in (dados.get("requisitos") or [])
                   if isinstance(r, dict) and r.get("tipo") in EXIGE_REFERENCIA})


def valida_arquivo(caminho):
    if not os.path.isfile(caminho):
        return {"estado": "SEM_ARQUIVO", "problemas": ["nao existe: %s" % caminho]}
    try:
        dados = json.loads(io.open(caminho, encoding="utf-8").read())
    except ValueError as e:
        return {"estado": "JSON_INVALIDO", "problemas": ["%s: %s" % (type(e).__name__, e)]}
    avisos = []
    problemas = valida_estrutura(dados, avisos)
    return {"estado": "OK" if not problemas else "FORMA_INVALIDA",
            "avisos": avisos,
            "arquivo": os.path.abspath(caminho),
            "n_requisitos": len(dados.get("requisitos") or []) if isinstance(dados, dict) else 0,
            "tipos_que_exigem_referencia": precisa_de_referencia(dados),
            "problemas": problemas,
            "nota": ("isto confere FORMA, nao geometria. Forma aceitavel nao diz nada "
                     "sobre a peca: quem mede e check_intent.py.")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo", nargs="?")
    ap.add_argument("--tipos", action="store_true")
    a = ap.parse_args()
    if a.tipos:
        print(json.dumps({"campos_obrigatorios_por_tipo": CAMPOS_POR_TIPO,
                          "tolerancia_que_o_verificador_le_por_tipo": TOLERANCIA_POR_TIPO,
                          "valor_que_decide_se_voce_nao_declarar": PADRAO_DA_TOLERANCIA,
                          "nome_diferente_na_saida": {
                              "%s/%s" % k: v for k, v in NOME_NA_SAIDA.items()},
                          "campos_alternativos_por_tipo": {
                              k: [list(a) for a in v] for k, v in
                              ALTERNATIVAS_POR_TIPO.items()},
                          "tipos_de_contagem_sem_tolerancia": list(TIPOS_DE_CONTAGEM),
                          "exigem_referencia": list(EXIGE_REFERENCIA)},
                         ensure_ascii=False, indent=1))
        return 0
    if not a.arquivo:
        ap.error("informe o arquivo, ou use --tipos")
    r = valida_arquivo(a.arquivo)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r["estado"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
