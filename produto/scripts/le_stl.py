"""Lê STL binário ou em texto (ASCII) e devolve (vértices, faces) em numpy, vértices fundidos a 1e-5.
Roda no Python do hospedeiro e dentro do Blender (ponte_letras_blender.py usa este módulo)."""
import os
import re

import numpy as np

_FLOAT = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_VERTICE = re.compile(rf"vertex\s+({_FLOAT})\s+({_FLOAT})\s+({_FLOAT})")


def _triangulos(caminho):
    tamanho = os.path.getsize(caminho)
    with open(caminho, "rb") as f:
        cabecalho = f.read(84)
        n = int(np.frombuffer(cabecalho[80:84], dtype="<u4")[0]) if len(cabecalho) == 84 else -1
        if n >= 0 and 84 + 50 * n == tamanho:
            dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
            return np.frombuffer(f.read(n * 50), dtype=dt)["v"].astype(np.float64).reshape(-1, 3)
        f.seek(0)
        texto = f.read().decode("ascii", "ignore")
    pontos = np.array(_VERTICE.findall(texto), dtype=np.float64)
    if len(pontos) == 0 or len(pontos) % 3:
        raise ValueError(f"STL ilegível (nem binário nem texto válido): {caminho}")
    return pontos


def le_stl(caminho):
    tri = _triangulos(caminho)
    chave = np.round(tri, 5)
    _, idx, inv = np.unique(chave, axis=0, return_index=True, return_inverse=True)
    return tri[idx], inv.reshape(-1).reshape(-1, 3)
