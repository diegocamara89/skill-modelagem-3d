"""Piso de espessura: engrossa feicao fina ate um minimo imprimivel sem estragar o resto.

Etapas:
  1. medir a espessura em TODOS os vertices (raio para dentro ao longo de -normal);
  2. separar feicao fina de VINCO DE RELEVO: vinco de rosto/roupa tambem da raio curto,
     mas o material em volta e grosso. Vertice so conta como fino se a MEDIANA da
     espessura dos vizinhos num raio (padrao 1,5 mm) tambem estiver abaixo do alvo;
  3. deslocar pela MAGNITUDE escalar suavizada, ao longo da normal. Nunca suavizar o
     VETOR de deslocamento: numa lamina fina as duas faces tem normais opostas e a media
     se anula — a feicao nao engrossa;
  4. Taubin (lambda 0,5 / mu -0,53) so na regiao que mexeu (+2 aneis), para nao serrilhar.

LIMITE DO FILTRO: o raio tem de ser MENOR que a feicao. Em feicao do tamanho do raio
(ex.: petala pequena) a vizinhanca pega o miolo grosso e a feicao e descartada como
vinco. Nesse caso, reduzir --raio-relevo (ex.: 0,6) e conferir no render quais vertices
mexeram.

Uso:
  python piso_espessura.py V.npy F.npy --alvo 0.9 --saida saida [--raio-relevo 1.5]
        [--suave-forte cx cy cz hx hy hz]   (caixa com Taubin forte; pode repetir)
Entrada e saida em .npy (booleana/round-trip de STL destroem topologia).
Custo: a medicao por raio leva minutos em 200 mil vertices; mostra progresso.
"""
import argparse, time, numpy as np, trimesh, scipy.sparse as sp
from scipy.spatial import cKDTree

p = argparse.ArgumentParser()
p.add_argument("V"); p.add_argument("F")
p.add_argument("--alvo", type=float, default=0.9)
p.add_argument("--saida", required=True)
p.add_argument("--raio-relevo", type=float, default=1.5)
p.add_argument("--suave-forte", nargs=6, type=float, action="append", default=[])
p.add_argument("--passos-leve", type=int, default=4)
p.add_argument("--passos-forte", type=int, default=14)
a = p.parse_args()
t0 = time.time()
m = trimesh.Trimesh(np.load(a.V), np.load(a.F), process=False)
nV = len(m.vertices); nrm = m.vertex_normals; o = m.vertices - nrm * 0.02

# 1. espessura por raio, em lotes, com recuo se faltar memoria
t = np.full(nV, np.inf); CH = 300
for i in range(0, nV, CH):
    oo, dd = o[i:i + CH], -nrm[i:i + CH]
    try:
        loc, ri, _ = m.ray.intersects_location(oo, dd, multiple_hits=False)
        if len(loc): t[i + ri] = np.linalg.norm(loc - oo[ri], axis=1)
    except MemoryError:
        for j in range(0, len(oo), 50):
            try:
                l2, r2, _ = m.ray.intersects_location(oo[j:j + 50], dd[j:j + 50], multiple_hits=False)
                if len(l2): t[i + j + r2] = np.linalg.norm(l2 - oo[j:j + 50][r2], axis=1)
            except MemoryError:
                pass
    if (i // CH) % 100 == 0:
        print(f"  espessura {i}/{nV}  {time.time()-t0:.0f}s", flush=True)
ok = np.isfinite(t)
fino = ok & (t < a.alvo)
print(f"medidos {ok.sum()}/{nV}; abaixo de {a.alvo} mm: {fino.sum()}")

# 2. filtro de vinco de relevo: mediana da vizinhanca
tree = cKDTree(m.vertices)
cand = np.where(fino)[0]
viz = tree.query_ball_point(m.vertices[cand], r=a.raio_relevo)
med = np.array([np.median(t[v][np.isfinite(t[v])]) if np.isfinite(t[v]).any() else np.inf for v in viz])
feicao = np.zeros(nV, bool); feicao[cand[med < a.alvo]] = True
print(f"feicao fina de verdade: {feicao.sum()}  |  vinco de relevo descartado: {len(cand) - feicao.sum()}")

# 3. magnitude escalar suavizada ao longo da normal
e = m.edges_unique
L = sp.coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(nV, nV)).tocsr()
grau = np.asarray(L.sum(axis=1)).ravel(); grau[grau == 0] = 1
off = np.where(feicao, np.clip((a.alvo - t) / 2.0, 0, None), 0.0)
mag = off.copy()
for _ in range(3): mag = 0.5 * mag + 0.5 * (L @ mag) / grau
V = m.vertices + nrm * mag[:, None]
print(f"deslocamento max {mag.max():.3f} mm em {(mag > 0.004).sum()} vertices")

# 4. Taubin so onde mexeu (+2 aneis); forte nas caixas pedidas
C = m.vertices
forte = np.zeros(nV, bool)
for cx, cy, cz, hx, hy, hz in a.suave_forte:
    forte |= np.all(np.abs(C - [cx, cy, cz]) < [hx, hy, hz], axis=1)
leve = (mag > 0.004) & ~forte
for _ in range(2): leve |= ((L @ leve.astype(float)) > 0) & ~forte


def taubin(V, reg, n):
    for k in range(n):
        f = 0.5 if k % 2 == 0 else -0.53
        V[reg] += f * ((L @ V) / grau[:, None] - V)[reg]
    return V


if forte.any(): V = taubin(V, forte, a.passos_forte)
V = taubin(V, leve, a.passos_leve)
m2 = trimesh.Trimesh(V, m.faces, process=False)
print(f"watertight {m2.is_watertight} | corpos {m2.body_count} | euler {m2.euler_number} | "
      f"volume {m.volume:.0f} -> {m2.volume:.0f} mm3 ({(m2.volume/m.volume-1)*100:+.2f}%)")
np.save(a.saida + "_V.npy", V); np.save(a.saida + "_F.npy", m.faces)
print(f"gravado {a.saida}_V.npy / _F.npy em {time.time()-t0:.0f}s")
