# -*- coding: utf-8 -*-
"""extrai_tolerancias.py - descobre, LENDO o verificador, qual tolerância cada tipo
de requisito realmente lê.

RODA FORA DO BLENDER. Só biblioteca padrão: usa `ast`, não importa o verificador.

POR QUE ESTE ARQUIVO EXISTE. A tabela "tolerância que o verificador lê por tipo"
era **transcrita à mão** para `valida_requisitos.py` e para `referencias/verificar.md`,
com o comentário "conferido no fonte tipo por tipo". Uma sessão limpa mediu que a
transcrição estava errada: o tipo `furo` lê `tol_mm` como tolerância de DIÂMETRO
(`check_intent.py`, `tol_d = float(r.get("tol_mm", 0.2))`, usada na decisão), e a
tabela dizia que ele não lê. Consequência: o validador **recusava** um número que o
verificador usa para decidir, e a referência garantia o contrário com a frase mais
confiante do documento.

Pior: o teste de paridade não pegou, porque essa checagem estava na lista de
"extras além do espelho" — ou seja, protegida por uma afirmação minha. Uma tabela
transcrita é uma afirmação; uma tabela extraída é uma medida.

O que este arquivo faz: para cada tipo, encontra a função que o verifica no
despachante `VERIFICADORES`, percorre o corpo dela e das funções auxiliares que ela
chama, e coleta todo nome lido de `r.get("...")` que esteja no vocabulário de
tolerância. Também colhe o valor PADRÃO de cada leitura, que é o número que decide
quando ninguém declara nada.

Uso:
    python scripts/extrai_tolerancias.py
    python scripts/extrai_tolerancias.py --json saida.json
"""
import argparse
import ast
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
VERIFICADOR = os.path.join(RAIZ, "verificadores", "check_intent.py")
VOCABULARIO = ("tol_mm", "tol_mm3", "tol_pos_mm", "tol_fracao", "circularidade_min")


def _arvore(caminho):
    return ast.parse(io.open(caminho, encoding="utf-8").read(), filename=caminho)


def _despachante(arv):
    """tipo -> nome da funcao, lido do dicionario VERIFICADORES."""
    for no in ast.walk(arv):
        if not isinstance(no, ast.Assign):
            continue
        nomes = [t.id for t in no.targets if isinstance(t, ast.Name)]
        if "VERIFICADORES" not in nomes or not isinstance(no.value, ast.Dict):
            continue
        d = {}
        for k, v in zip(no.value.keys, no.value.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Name):
                d[k.value] = v.id
        return d
    return {}


def _funcoes(arv):
    return {n.name: n for n in arv.body if isinstance(n, ast.FunctionDef)}


def _leituras(no):
    """Nomes de tolerancia lidos por r.get("...") dentro deste nó, com o padrao."""
    achados = []
    for x in ast.walk(no):
        if not isinstance(x, ast.Call):
            continue
        f = x.func
        if not (isinstance(f, ast.Attribute) and f.attr == "get"
                and isinstance(f.value, ast.Name) and f.value.id == "r"):
            continue
        if not x.args or not isinstance(x.args[0], ast.Constant):
            continue
        nome = x.args[0].value
        if nome not in VOCABULARIO:
            continue
        padrao = None
        if len(x.args) > 1:
            try:
                padrao = ast.literal_eval(x.args[1])
            except ValueError:
                padrao = ast.unparse(x.args[1])
        achados.append({"tolerancia": nome, "padrao_quando_nao_declarada": padrao,
                        "linha": x.lineno})
    return achados


def _chamadas(no, conhecidas):
    return sorted({x.func.id for x in ast.walk(no)
                   if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                   and x.func.id in conhecidas})


def extrai(caminho=VERIFICADOR):
    arv = _arvore(caminho)
    fs = _funcoes(arv)
    desp = _despachante(arv)
    fora = {}
    detalhe = {}
    for tipo, nome_da_funcao in sorted(desp.items()):
        alvo = fs.get(nome_da_funcao)
        if alvo is None:
            detalhe[tipo] = {"erro": "funcao %r nao encontrada" % nome_da_funcao}
            continue
        vistos, fila, achados = set(), [nome_da_funcao], []
        while fila:                       # segue auxiliares, sem repetir
            atual = fila.pop()
            if atual in vistos or atual not in fs:
                continue
            vistos.add(atual)
            achados += [dict(a, funcao=atual) for a in _leituras(fs[atual])]
            fila += [c for c in _chamadas(fs[atual], fs) if c not in vistos]
        fora[tipo] = tuple(sorted({a["tolerancia"] for a in achados}))
        detalhe[tipo] = {"funcao": nome_da_funcao,
                         "funcoes_percorridas": sorted(vistos),
                         "leituras": sorted(achados, key=lambda a: a["linha"])}
    return {"verificador": os.path.abspath(caminho),
            "tolerancia_por_tipo": {k: list(v) for k, v in fora.items()},
            "detalhe": detalhe,
            "vocabulario": list(VOCABULARIO),
            "limite": ("isto le o FONTE. Prova o que o verificador consulta, nao que "
                       "a consulta esteja certa, e nao cobre nome de tolerancia "
                       "montado em tempo de execucao — hoje nao existe nenhum.")}


def como_tupla(resultado):
    return {k: tuple(v) for k, v in resultado["tolerancia_por_tipo"].items()}


def padroes(resultado):
    """tipo -> {tolerancia: padrao}, com o padrao NORMALIZADO para comparacao.

    Acrescentado depois da quarta revisao: os padroes ja eram extraidos e ficavam
    so no relatorio, entao a tabela `PADRAO_DA_TOLERANCIA` do validador podia
    divergir do fonte com o teste de paridade ATENDIDO. Padrao que decide e numero
    que decide: precisa de oraculo igual ao dos nomes.

    Normalizacao: numero vira float; expressao (como `max(1.0, 0.01 * esp)`) vira o
    proprio texto, sem espacos, porque ali nao existe valor unico a comparar."""
    fora = {}
    for tipo, d in resultado["detalhe"].items():
        m = {}
        for x in d.get("leituras", ()):
            v = x["padrao_quando_nao_declarada"]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                m[x["tolerancia"]] = ("expressao", "".join(str(v).split()))
            else:
                m[x["tolerancia"]] = ("numero", float(v))
        fora[tipo] = m
    return fora


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verificador", default=VERIFICADOR)
    ap.add_argument("--json")
    a = ap.parse_args()
    r = extrai(a.verificador)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        io.open(a.json, "w", encoding="utf-8").write(
            json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps({"tolerancia_por_tipo": r["tolerancia_por_tipo"],
                      "padroes": {t: [(x["tolerancia"], x["padrao_quando_nao_declarada"])
                                      for x in d.get("leituras", [])]
                                  for t, d in r["detalhe"].items()}},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
