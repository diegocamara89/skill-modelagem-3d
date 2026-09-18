"""Lado HOST da ponte das letras: manda ponte_letras_blender.py para a sessão viva (MCP) e devolve o resultado.

Uso:
  python ponte_letras.py instalar_letras                      # letras A, B, C no viewport, na ordem do clique
  python ponte_letras.py letras                               # lê as letras (todas as peças em edição)
  python ponte_letras.py tracos [--limpar]                    # lê os traços da ferramenta Anotar
  python ponte_letras.py apagar                               # apaga faces selecionadas e fecha o furo
  python ponte_letras.py carregar --objeto NOME --stl a.stl --feicoes a.feicoes.json
  python ponte_letras.py atualizar --objeto NOME --stl b.stl --feicoes b.feicoes.json
  python ponte_letras.py identificar|expandir|estado --objeto NOME
  python ponte_letras.py salvar_copia --caminho copia.blend   # só a cena de trabalho, nunca o arquivo do operador
  python ponte_letras.py exportar_stl --objeto NOME --caminho saida.stl
  python ponte_letras.py captura --caminho tela.png
"""
import argparse
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from mcp_blender import chama  # noqa: E402

OBJETO = None   # passe --objeto quando a ação exigir um objeto nomeado
MARCA = "LETRAS_RESULTADO="


def executa(acao, **args):
    codigo = (AQUI / "ponte_letras_blender.py").read_text(encoding="utf-8")
    cfg = {"pasta": str(AQUI), "acao": acao, "args": args}
    prefixo = "CONFIG = " + repr(cfg) + "\n"
    r = chama("execute_code", {"code": prefixo + codigo}, permitir_escrita=True, tempo_limite=120)
    if r.get("estado") != "OK":
        return r
    achados = []

    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)
    for t in strings(r):
        for linha in t.splitlines():
            if linha.startswith(MARCA):
                achados.append(json.loads(linha[len(MARCA):]))
    if len(achados) != 1:
        return {"estado": "RESULTADO_AUSENTE", "resposta": r}
    return achados[0]


def captura(caminho, max_size=1200):
    return chama("get_viewport_screenshot", {"max_size": max_size, "filepath": str(pathlib.Path(caminho).resolve()), "format": "png"}, tempo_limite=60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("acao")
    ap.add_argument("--stl")
    ap.add_argument("--feicoes")
    ap.add_argument("--caminho")
    ap.add_argument("--limpar", action="store_true")
    ap.add_argument("--objeto")
    a = ap.parse_args()
    if a.acao == "instalar_letras":
        codigo = (AQUI / "letras_viewport.py").read_text(encoding="utf-8")
        out = chama("execute_code", {"code": codigo}, permitir_escrita=True)
    elif a.acao == "captura":
        out = captura(a.caminho)
    elif a.acao in ("carregar", "atualizar"):
        out = executa(a.acao, stl=str(pathlib.Path(a.stl).resolve()), feicoes_json=str(pathlib.Path(a.feicoes).resolve()), nome=(a.objeto or OBJETO))
    elif a.acao in ("identificar", "estado", "expandir"):
        out = executa(a.acao, nome=(a.objeto or OBJETO))
    elif a.acao == "letras":
        out = executa("letras", nome=None)
    elif a.acao == "apagar":
        out = executa("apagar", nome=None)
    elif a.acao == "tracos":
        out = executa("tracos", nome=None, limpar=a.limpar)
    elif a.acao == "salvar_copia":
        out = executa(a.acao, caminho=str(pathlib.Path(a.caminho).resolve()))
    elif a.acao == "exportar_stl":
        out = executa(a.acao, nome=(a.objeto or OBJETO), caminho=str(pathlib.Path(a.caminho).resolve()))
    else:
        out = {"estado": "ACAO_DESCONHECIDA"}
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
