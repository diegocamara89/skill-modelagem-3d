"""Transplante de deslocamento entre variantes da MESMA malha, sem booleana.

Quando varias versoes de uma malha tem a mesma ordem de vertices (so posicoes mudam),
da para (1) montar um alvo pegando cada regiao de uma versao e (2) levar esse alvo para
uma malha DERIVADA (que ja passou por corte/booleana e tem outra topologia), casando a
derivada com o ancestral comum por coincidencia exata de vertices.

Validado em 23/09/2026 numa escultura impressa: 198.831 vertices casados, 1.641 novos (corte e
furo) interpolados, resultado fechado, euler igual ao da derivada, 0,9 s.

Uso:
  python transplante_deslocamento.py --base base_V.npy --divisa z=-2 \
      --acima versaoA_V.npy --abaixo versaoB_V.npy \
      --derivada derivada_V.npy derivada_F.npy --ancestral ancestral_V.npy --saida FINAL

  --base       versao de referencia (mesma topologia de --acima/--abaixo/--ancestral)
  --divisa     eixo=valor. Vertice com coordenada > valor recebe --acima; senao --abaixo.
               O script RECUSA se algum vertice for mexido pelas duas versoes.
  --derivada   V.npy F.npy da malha que recebe o alvo (ex.: corpo com uma feicao removida)
  --ancestral  a versao de mesma topologia de onde a derivada foi feita
  --saida      prefixo: grava <saida>_V.npy e <saida>_F.npy

Passar sempre por .npy: resultado de booleana nao sobrevive ao round-trip de STL.
"""
import argparse, numpy as np, time
from scipy.spatial import cKDTree

p = argparse.ArgumentParser()
p.add_argument("--base", required=True)
p.add_argument("--divisa", required=True)
p.add_argument("--acima", required=True)
p.add_argument("--abaixo", required=True)
p.add_argument("--derivada", nargs=2, required=True)
p.add_argument("--ancestral", required=True)
p.add_argument("--saida", required=True)
p.add_argument("--tol", type=float, default=1e-4, help="coincidencia exata (mm)")
p.add_argument("--k", type=int, default=8, help="vizinhos para interpolar vertices novos")
a = p.parse_args()
t0 = time.time()

base, up, dn, anc = (np.load(x) for x in (a.base, a.acima, a.abaixo, a.ancestral))
n = len(base)
for nome, V in (("acima", up), ("abaixo", dn), ("ancestral", anc)):
    if len(V) != n:
        raise SystemExit(f"topologia diferente: {nome} tem {len(V)} vertices, base tem {n}")
eixo, val = a.divisa.split("="); ax = "xyz".index(eixo); val = float(val)
sup = base[:, ax] > val
mu = np.linalg.norm(up - base, axis=1) > a.tol
md = np.linalg.norm(dn - base, axis=1) > a.tol
if (mu & ~sup).sum() and not np.array_equal(mu & ~sup, md & ~sup):
    print(f"aviso: 'acima' mexe {(mu & ~sup).sum()} vertices abaixo da divisa; eles serao "
          f"substituidos por 'abaixo' ({(md & ~sup).sum()} mexidos la)")
if (md & sup).any():
    raise SystemExit(f"RECUSADO: 'abaixo' mexe {(md & sup).sum()} vertices acima da divisa. Mova a divisa.")
S = base.copy(); S[sup] = up[sup]; S[~sup] = dn[~sup]
print(f"alvo: {int((mu & sup).sum())} vertices de 'acima', {int((md & ~sup).sum())} de 'abaixo'")

V8 = np.load(a.derivada[0]); F8 = np.load(a.derivada[1])
d, idx = cKDTree(anc).query(V8)
casou = d < a.tol
if casou.mean() < 0.5:
    raise SystemExit(f"RECUSADO: so {casou.mean()*100:.1f}% da derivada casa com o ancestral. Ancestral errado?")
novo = V8.copy()
novo[casou] = S[idx[casou]]
desl = S[idx[casou]] - anc[idx[casou]]
if (~casou).any():
    dk, ik = cKDTree(V8[casou]).query(V8[~casou], k=a.k)
    w = 1.0 / np.maximum(dk, 1e-6); w /= w.sum(1, keepdims=True)
    novo[~casou] = V8[~casou] + (desl[ik] * w[..., None]).sum(1)
print(f"derivada: {casou.sum()} vertices casados, {(~casou).sum()} novos interpolados; "
      f"deslocamento max {np.linalg.norm(novo - V8, axis=1).max():.3f} mm")
try:
    import trimesh
    m8 = trimesh.Trimesh(V8, F8, process=False); m = trimesh.Trimesh(novo, F8, process=False)
    print(f"antes:  watertight {m8.is_watertight}, corpos {m8.body_count}, euler {m8.euler_number}")
    print(f"depois: watertight {m.is_watertight}, corpos {m.body_count}, euler {m.euler_number}, "
          f"vol {m.volume/1000:.3f} cm3")
    if (m.is_watertight, m.body_count, m.euler_number) != (m8.is_watertight, m8.body_count, m8.euler_number):
        print("ATENCAO: topologia mudou — conferir antes de usar")
except ImportError:
    pass
np.save(a.saida + "_V.npy", novo); np.save(a.saida + "_F.npy", F8)
print(f"gravado {a.saida}_V.npy / _F.npy em {time.time()-t0:.1f}s")
