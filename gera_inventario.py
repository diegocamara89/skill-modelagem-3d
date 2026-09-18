# -*- coding: utf-8 -*-
"""gera_inventario.py - regrava produto/INVENTARIO.json a partir da lista PERMITIDOS do empacotador.

Ferramenta de oficina, fora de produto/. Uso: python gera_inventario.py 2.9.0
"""
import hashlib, json, os, sys, datetime
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from empacota_produto import PERMITIDOS  # noqa: E402

versao = sys.argv[1] if len(sys.argv) > 1 else None
origem = os.path.join(AQUI, "produto")
caminho = os.path.join(origem, "INVENTARIO.json")
inv = json.load(open(caminho, encoding="utf-8"))
if versao:
    inv["versao_do_pacote"] = versao
inv["congelado_em"] = datetime.date.today().isoformat()
arquivos = {}
for rel in sorted(set(PERMITIDOS) - {"INVENTARIO.json"}):
    p = os.path.join(origem, rel)
    if not os.path.isfile(p):
        sys.exit(f"FALTA no produto: {rel}")
    arquivos[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
inv["arquivos"] = arquivos
json.dump(inv, open(caminho, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"INVENTARIO {inv['versao_do_pacote']}: {len(arquivos)} arquivos, congelado em {inv['congelado_em']}")
