"""Caminhos desta máquina, sem nada fixo no pacote.

Ordem: variável de ambiente > chave em %LOCALAPPDATA%/modelagem-3d/ambiente.json > padrões (aceitam coringa).
Exemplo de ambiente.json: {"freecad_exe": "D:/FreeCAD/bin/freecad.exe", "bambu_studio_exe": "...", "modelo_3mf": "..."}
"""
import glob
import json
import os
from pathlib import Path

ARQUIVO = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'modelagem-3d' / 'ambiente.json'


def caminho(chave, variavel, *padroes):
    """Primeiro caminho que existe; se nenhum existir, o primeiro candidato (para a mensagem de erro)."""
    candidatos = [os.environ.get(variavel)]
    try:
        candidatos.append(json.loads(ARQUIVO.read_text(encoding='utf-8-sig')).get(chave))
    except (OSError, ValueError):
        pass
    for p in padroes:
        p = os.path.expandvars(str(p))
        candidatos += sorted(glob.glob(p), reverse=True) or [p]  # reverse: versão mais nova primeiro
    candidatos = [Path(c) for c in candidatos if c]
    return next((c for c in candidatos if c.exists()), candidatos[0] if candidatos else None)
