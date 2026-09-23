"""De qual malha inteira este recorte (cupom, corpo de prova) saiu?

Metodo: coincidencia EXATA de vertices. O recorte foi tirado da fonte e depois movido;
seus vertices que nao estao na face de corte sao vertices da fonte + uma translacao t.
Pega um vertice do recorte, testa todas as translacoes possiveis (fonte - vertice) e
descarta com poucos vertices adicionais. Quando as candidatas tem a MESMA topologia (so
posicoes mudam), a translacao e a mesma para todas: calcula uma vez contra --base.

Medido em 23/09/2026: 1 segundo, contra mais de 7 minutos da varredura em grade.
Resultado tipico: a fonte certa tem 80-90% de vertices exatos (o resto sao as faces do
corte); as erradas ficam no patamar do que nao foi mexido.

LIMITE: recorte engrossado DEPOIS de cortado nao bate exatamente com nenhuma malha inteira
(todas ficam baixas e parecidas). Isso tambem e uma resposta.

Uso:
  python origem_do_recorte.py recorte_V.npy --base base_V.npy --candidatas versaoA_V.npy versaoB_V.npy ...
"""
import argparse, numpy as np, os
from scipy.spatial import cKDTree

p = argparse.ArgumentParser()
p.add_argument("recorte")
p.add_argument("--base", required=True, help="malha de mesma topologia das candidatas, usada para achar a translacao")
p.add_argument("--candidatas", nargs="+", required=True)
p.add_argument("--tol", type=float, default=1e-4)
a = p.parse_args()

C = np.load(a.recorte); base = np.load(a.base); tb = cKDTree(base)


def acha_t(C):
    rng = np.random.default_rng(2)
    for c0 in rng.choice(len(C), min(30, len(C)), replace=False):
        T = base - C[c0]
        d = tb.query(C[rng.integers(len(C))] + T, distance_upper_bound=1e-3)[0]
        ok = np.isfinite(d)
        for _ in range(4):
            if ok.sum() <= 1: break
            cand = np.where(ok)[0]
            d = tb.query(C[rng.integers(len(C))] + T[cand], distance_upper_bound=1e-3)[0]
            ok[cand[~np.isfinite(d)]] = False
        if ok.sum() == 1:
            return T[ok][0]
    return None


t = acha_t(C)
if t is None:
    raise SystemExit("nao achei translacao: o recorte nao compartilha vertices com a base")
print(f"translacao do recorte: {np.round(t, 4)}")
res = []
for c in [a.base] + a.candidatas:
    V = np.load(c)
    f = (cKDTree(V).query(C + t)[0] < a.tol).mean()
    res.append((f, os.path.basename(c)))
for f, n in sorted(res, reverse=True):
    print(f"   {n:32} {100*f:5.1f}% de vertices exatos")
