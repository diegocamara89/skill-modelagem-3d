"""Diagnostico fixo da sessao viva pelo transporte existente. Nao executa codigo do usuario."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from mcp_blender import chama

MARCA = "MODELAGEM_DIAGNOSTICO="


def diagnosticar(transporte=chama):
    pasta = str(Path(__file__).resolve().parent)
    codigo = ("import sys, json\nsys.dont_write_bytecode = True\n"
              f"sys.path.insert(0, {pasta!r})\n"
              "import importlib.util\n"
              f"spec = importlib.util.spec_from_file_location('_modelagem_diagnostico', {str(Path(pasta)/'edicao_guiada.py')!r})\n"
              "mod = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(mod)\n"
              f"print({MARCA!r} + json.dumps(mod.diagnostica()))\n")
    # O transporte classifica TODO execute_code como potencial escrita. Este comando
    # e fixo e exclusivamente de consulta; o sinalizador nao e autorizacao para editar.
    resposta = transporte("execute_code", {"code": codigo}, permitir_escrita=True)
    if resposta.get("estado") != "OK":
        return resposta
    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)
    resultados = []
    for texto in strings(resposta):
        for linha in texto.splitlines():
            if linha.startswith(MARCA):
                try:
                    resultados.append(json.loads(linha[len(MARCA):]))
                except ValueError:
                    pass
    if len(resultados) != 1 or not isinstance(resultados[0], dict) or resultados[0].get("versao") != "1.0.0":
        return {"estado": "DIAGNOSTICO_AUSENTE", "motivo": "O complemento respondeu sem um diagnostico unico compativel. Nao editar; confira a resposta.", "resposta": resposta}
    return {"estado": "OK", "diagnostico": resultados[0],
            "limite": "Conexao e contexto consultados; nao prova permissao ou sucesso de edicao."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnosticar", action="store_true", required=True)
    parser.parse_args()
    out = diagnosticar()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("estado") == "OK" else 1)
