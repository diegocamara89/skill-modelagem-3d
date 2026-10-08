"""Cria a pagina de bancada (validacao de medidas e conceitos) de um projeto.

Copia assets/pagina_bancada.html para <pasta>/revisao.html, copia as fotos para
<pasta>/imagens/ (preservando o nome) e preenche projeto, data e a lista de fotos.
Depois disso, edite so o bloco DADOS da pagina (conceitos, vistas, cotas, listas).

Uso:
  python nova_pagina_bancada.py --pasta "D:/.../Projeto" --projeto "Nome" foto1.jpg foto2.jpg
Nunca sobrescreve: revisao.html existente ou foto diferente com o mesmo nome param o script.
"""
import argparse
import datetime
import filecmp
import json
import pathlib
import re
import shutil
import sys

MODELO = pathlib.Path(__file__).resolve().parent.parent / "assets" / "pagina_bancada.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--projeto", required=True)
    ap.add_argument("--saida", default="revisao.html")
    ap.add_argument("fotos", nargs="*")
    a = ap.parse_args()

    pasta = pathlib.Path(a.pasta)
    destino = pasta / a.saida
    if destino.exists():
        sys.exit(f"ja existe: {destino} (aproveite a pagina existente ou use --saida)")
    imagens = pasta / "imagens"
    imagens.mkdir(parents=True, exist_ok=True)

    fotos = []
    for i, f in enumerate(map(pathlib.Path, a.fotos), 1):
        alvo = imagens / f.name
        if alvo.exists() and not filecmp.cmp(f, alvo, shallow=False):
            sys.exit(f"foto diferente com o mesmo nome ja existe: {alvo}")
        if not alvo.exists():
            shutil.copy2(f, alvo)
        fotos.append({"id": str(i), "arquivo": f.name, "descricao": "descrever o que a foto mostra"})

    dados = {
        "projeto": a.projeto, "revisao": 1, "data": datetime.date.today().isoformat(), "unidade": "mm",
        "kicker": "Caderno de bancada", "titulo": a.projeto, "intro": "", "nota": "",
        "conceitos": [], "vistas": [], "cotas": [], "fotos": fotos, "listas": [], "renders": None,
        "rodape": "Revisão visual para definir medidas e conceito. Não é modelo de fabricação. Dimensões em mm.",
    }
    bloco = "/*DADOS*/\nconst DADOS=" + json.dumps(dados, ensure_ascii=False, indent=2) + ";\n/*FIM DADOS*/"
    html = MODELO.read_text(encoding="utf-8")
    novo, n = re.subn(r"/\*DADOS\*/.*?/\*FIM DADOS\*/", lambda _: bloco, html, flags=re.S)
    if n != 1:
        sys.exit("marcadores DADOS nao encontrados no modelo")
    destino.write_text(novo, encoding="utf-8")
    print(f"criado {destino} com {len(fotos)} foto(s) em {imagens}")


if __name__ == "__main__":
    main()
