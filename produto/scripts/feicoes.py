"""Identidade das feições — módulo compartilhado (host e Blender). Só numpy.

Um rasgo é descrito no sistema da face onde foi cortado:
  s = coordenada ao longo da face (sobe), y = largura, d = profundidade (0 = superfície externa, negativo = para dentro).
Classifica FACES da malha como "parede do rasgo X" quando o centroide cai dentro do
retângulo (s0..s1, yc±larg/2) e a normal é perpendicular à normal da chapa.
"""
import json
import numpy as np


def carrega(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def coords_face(pontos, fe):
    """pontos (N,3) mundo -> (s, y, d) no sistema da feição."""
    p = np.asarray(pontos, dtype=float)
    ox, oz = fe["o"]
    ux, uz = fe["u"]
    nx, nz = fe["n"]
    dx, dz = p[:, 0] - ox, p[:, 2] - oz
    s = dx * ux + dz * uz
    d = dx * nx + dz * nz
    return s, p[:, 1], d


def classifica_faces(centroides, normais, feicoes, tol=0.05, cos_max=0.35):
    """Devolve array int (N,) com índice da feição (posição na lista) ou -1."""
    c = np.asarray(centroides, dtype=float)
    nrm = np.asarray(normais, dtype=float)
    rot = -np.ones(len(c), dtype=int)
    for k, fe in enumerate(feicoes):
        s, y, d = coords_face(c, fe)
        N3 = np.array([fe["n"][0], 0.0, fe["n"][1]])
        perp = np.abs(nrm @ N3) < cos_max
        m = ((s >= fe["s0"] - tol) & (s <= fe["s1"] + tol)
             & (np.abs(y - fe["yc"]) <= fe["larg"] / 2 + tol)
             & (d >= -fe["esp"] - tol) & (d <= tol) & perp)
        rot[m & (rot < 0)] = k
    return rot


def mede_rasgo(vertices, faces, rot, k, fe):
    """Comprimento (ao longo de s) e largura (em y) das paredes da feição k."""
    idx = np.unique(np.asarray(faces)[rot == k].ravel())
    if len(idx) == 0:
        return None
    s, y, _ = coords_face(np.asarray(vertices)[idx], fe)
    return {"n_faces": int((rot == k).sum()), "comprimento": float(s.max() - s.min()),
            "largura": float(y.max() - y.min()), "s_min": float(s.min()), "s_max": float(s.max())}


def identifica(rot_selecionadas, feicoes, minimo=0.8):
    """Dada a classificação das faces selecionadas, decide qual feição — ou recusa."""
    rot = np.asarray(rot_selecionadas)
    n = len(rot)
    if n == 0:
        return {"estado": "RECUSADO", "motivo": "nenhuma face selecionada"}
    ks, cont = np.unique(rot, return_counts=True)
    ordem = np.argsort(-cont)
    contagem = {(feicoes[k]["nome"] if k >= 0 else "fora_de_rasgo"): int(c)
                for k, c in zip(ks[ordem], cont[ordem])}
    k0, c0 = ks[ordem][0], cont[ordem][0]
    if k0 < 0:
        return {"estado": "RECUSADO", "motivo": "a maior parte da seleção não é parede de rasgo (ripa, moldura ou outra região)", "contagem": contagem}
    if c0 / n < minimo:
        return {"estado": "AMBIGUO", "motivo": f"feição dominante tem só {c0/n:.0%} das faces; exige >= {minimo:.0%}", "contagem": contagem}
    return {"estado": "IDENTIFICADO", "feicao": feicoes[k0]["nome"], "fracao": float(c0 / n), "contagem": contagem}
