"""Mapa de balanco por corpo, ANTES de fatiar: quanto de cada peca vai pedir suporte e se
ela encosta na mesa.

Para cada corpo: area voltada para baixo e no ar (centroide acima de 0,5 mm da base do
corpo), por faixa de inclinacao; e a area plana de contato com a mesa. Inclinacao medida
a partir da HORIZONTAL: 0 = teto, 90 = parede. O fatiador apoia o que fica ABAIXO do
limiar ("support_threshold_angle"), entao menor limiar = menos suporte.

Contato 0,0 mm2 = a peca flutua e imprime inteira sobre suporte (cupom de colar em
22/09/2026: 0 mm2 de contato, 2 mm de parede na 1a camada). Conferir depois no G-code.

Uso:  python mapa_balanco.py arquivo.3mf|arquivo.stl [--limiar 30]
"""
import argparse, numpy as np, trimesh

p = argparse.ArgumentParser()
p.add_argument("arquivo"); p.add_argument("--limiar", type=float, default=30.0)
a = p.parse_args()
if a.arquivo.lower().endswith(".3mf"):
    s = trimesh.load(a.arquivo, file_type="3mf"); ms = []
    for node in s.graph.nodes_geometry:
        T, g = s.graph[node]; m = s.geometry[g].copy(); m.apply_transform(T)
        ms += m.split(only_watertight=False)
else:
    ms = trimesh.load(a.arquivo, force="mesh").split(only_watertight=False)

lasca = sum(len(c.faces) < 4 for c in ms); ms = [c for c in ms if len(c.faces) >= 4]
if lasca:
    print(f"ignorados {lasca} corpo(s) com menos de 4 faces (lasca degenerada)")
L = a.limiar
print(f"{'faces':>7} {'centro x,y':>16} | {'<'+str(int(L))+'° apoia':>11} {'30-45°':>8} {'45-60°':>8} | {'contato mesa':>12} {'pior':>6}")
for c in sorted(ms, key=lambda c: (round(c.bounds[0][1]), c.bounds[0][0])):
    n = c.face_normals; ar = c.area_faces; ct = c.triangles_center; lo = c.bounds[0]
    cosd = -n[:, 2]; th = np.degrees(np.arccos(np.clip(cosd, -1, 1)))
    mesa = ar[(cosd > 0.99) & (ct[:, 2] - lo[2] < 0.3)].sum()
    ar_no_ar = (cosd > 1e-6) & (ct[:, 2] - lo[2] > 0.5)
    f = lambda x, y: ar[ar_no_ar & (th >= x) & (th < y)].sum()
    pior = th[ar_no_ar].min() if ar_no_ar.any() else 90.0
    ce = (c.bounds[0] + c.bounds[1]) / 2
    print(f"{len(c.faces):7d} {ce[0]:7.1f},{ce[1]:7.1f} | {f(0, L):9.1f}mm2 {f(30, 45):8.1f} {f(45, 60):8.1f} | "
          f"{mesa:9.1f}mm2 {pior:5.1f}°" + ("   <<< sem contato: imprime sobre suporte" if mesa < 1 else ""))
