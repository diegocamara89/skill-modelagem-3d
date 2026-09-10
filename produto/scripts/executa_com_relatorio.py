"""Dentro do Blender: executa executar(config) de um script com relatorio de excecao.

Use com roda_blender.py. CONCLUIDA significa que a funcao retornou um dict,
nao que a geometria atende ao pedido. O resultado do verificador permanece separado.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import traceback


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--script", required=True)
    p.add_argument("--config")
    p.add_argument("--resultado-em", required=True)
    a = p.parse_args(argv)
    saida = Path(a.resultado_em).resolve()
    for entrada in (a.script, a.config):
        if entrada and (Path(entrada).resolve() == saida or
                        (saida.exists() and Path(entrada).exists() and os.path.samefile(entrada, saida))):
            p.error("COLISAO_ENTRADA_SAIDA: use destino diferente do script e da configuracao")
    rel = {"estado_execucao": "ERRO", "script_sha256": None, "config_sha256": None}
    try:
        script = Path(a.script).resolve()
        rel["script_sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
        cfg = {}
        if a.config:
            raw = Path(a.config).read_bytes()
            rel["config_sha256"] = hashlib.sha256(raw).hexdigest()
            cfg = json.loads(raw)
        if not isinstance(cfg, dict):
            raise ValueError("config deve ser objeto JSON")
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(script.parent))
        ns = runpy.run_path(str(script), run_name="_modelagem_trabalho")
        if not callable(ns.get("executar")):
            raise ValueError("script deve definir executar(config) e retornar um dict de medidas/verificacao")
        resultado = ns["executar"](cfg)
        if not isinstance(resultado, dict):
            raise ValueError("executar(config) deve devolver um dict; None nao comprova resultado")
        json.dumps(resultado, allow_nan=False)
        rel.update(estado_execucao="CONCLUIDA", resultado=resultado)
    except BaseException as e:
        rel.update(tipo=type(e).__name__, motivo=str(e), traceback=traceback.format_exc())
    rel["limite"] = "Estado operacional, nao aprovacao geometrica; ler resultado e completar verificacoes. Timeout ou encerramento forcado podem impedir este relatorio."
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=saida.parent, delete=False) as f:
            temporario = f.name
            json.dump(rel, f, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(temporario, saida)
    finally:
        if temporario and os.path.exists(temporario):
            os.unlink(temporario)
    return 0 if rel["estado_execucao"] == "CONCLUIDA" else 1


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    sys.exit(main(args))
