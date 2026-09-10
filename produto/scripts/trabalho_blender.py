"""Headless com invólucro de erro pronto. Nunca se conecta a sessao aberta."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from roda_blender import roda


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--script", required=True)
    p.add_argument("--config")
    p.add_argument("--resultado", required=True)
    p.add_argument("--blender")
    p.add_argument("--tempo-limite", type=int, default=300)
    a = p.parse_args()
    destino = Path(a.resultado).resolve()
    for entrada in (a.script, a.config):
        if entrada:
            caminho = Path(entrada).resolve()
            if not caminho.is_file():
                p.error("ENTRADA_AUSENTE: " + str(caminho))
            if caminho == destino or (destino.exists() and os.path.samefile(caminho, destino)):
                p.error("COLISAO_ENTRADA_SAIDA: nao substituir script ou config pelo relatorio")
    args = ["--script", str(Path(a.script).resolve())]
    if a.config:
        args += ["--config", str(Path(a.config).resolve())]
    r = roda(str(Path(__file__).with_name("executa_com_relatorio.py")), str(destino),
             args=args, blender=a.blender, tempo_limite_s=a.tempo_limite,
             passa_resultado=True, exigir=("estado_execucao", "CONCLUIDA"))
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get("estado") == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
