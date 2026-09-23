"""Recorta um corpo de prova (cupom) de uma malha por caixa, com rótulo gravado no topo.

Uso:
  python recorta_cupom.py peca.ply saida.ply --caixa X0 Y0 Z0 X1 Y1 Z1 [--mesa 128 128] [--rotulo A]

Prefira PLY/OBJ/3MF na entrada: STL arredonda para float32 e pode fundir vértices distintos,
e aí a interseção recusa a malha.

--caixa   limites do recorte, em mm. Sem --mesa, nas coordenadas da malha.
--mesa    interpreta a caixa nas coordenadas da MESA: a malha é posta com o centro XY no ponto
          dado e a base em Z = 0 (o que o fatiador faz ao centralizar). Use para recortar a
          região que você mediu no G-code.
--rotulo  letra ou texto curto gravado em baixo-relevo (0,4 mm) na face plana de cima. A face
          de cima de um recorte é plana e horizontal: não pede suporte e não muda o balanço.

Recorte por interseção com caixa (manifold), sem mudar a orientação: a face de corte de baixo
vira a base na mesa. Sai fechado e com um corpo, ou o script avisa.

Um cupom só responde se reproduzir a condição crítica da peça inteira. O recorte muda, sem
avisar, o tempo de cada camada (e com ele a ventoinha automática), a altura dos suportes até a
região, o que é impresso ao lado e o tempo decorrido até ali. Ver referencias/verificar.md.
"""
import argparse, sys
import numpy as np, trimesh

ap = argparse.ArgumentParser()
ap.add_argument("entrada"); ap.add_argument("saida")
ap.add_argument("--caixa", nargs=6, type=float, required=True)
ap.add_argument("--mesa", nargs=2, type=float)
ap.add_argument("--rotulo")
ap.add_argument("--profundidade", type=float, default=0.4)
ap.add_argument("--margem", type=float, default=1.2, help="distância mínima do rótulo à borda do topo")
a = ap.parse_args()

m = trimesh.load(a.entrada, force="mesh", process=False)
if not m.is_volume:
    m.merge_vertices()                                           # STL chega com vértices soltos
if not m.is_volume:
    sys.exit("a malha não é um volume fechado. Se veio de STL, o arredondamento para float32 pode ter "
             "fundido vértices distintos: exporte em PLY/OBJ/3MF, que guardam os índices")
if a.mesa:
    lo, hi = m.bounds
    m.apply_translation([a.mesa[0] - (lo[0] + hi[0]) / 2, a.mesa[1] - (lo[1] + hi[1]) / 2, -lo[2]])
LO, HI = np.array(a.caixa[:3]), np.array(a.caixa[3:])
cx = trimesh.creation.box(extents=HI - LO); cx.apply_translation((LO + HI) / 2)
r = trimesh.boolean.intersection([m, cx], engine="manifold")
if len(r.faces) == 0:
    sys.exit("recorte vazio: a caixa não pega a malha (conferir --mesa e as coordenadas)")
print(f"recorte: {len(r.faces)} faces, fechado {r.is_watertight}, corpos {r.body_count}, "
      f"volume {r.volume:.0f} mm3, dimensões {(r.bounds[1] - r.bounds[0]).round(2)} mm")
if r.body_count > 1:
    print("AVISO: mais de um corpo — a caixa cortou feições soltas; cada corpo precisa de base própria")

if a.rotulo:
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from shapely.geometry import Polygon
    from shapely.ops import unary_union, polylabel
    from shapely import affinity
    zt = r.vertices[:, 2].max()
    M2 = np.eye(4); M2[2, 3] = -(zt - 0.05)                     # plano da seção = XY do mundo
    sec = r.section([0, 0, 1], [0, 0, zt - 0.05]).to_2D(to_2D=M2)[0]
    topo = unary_union(list(sec.polygons_full)).buffer(-a.margem)
    if topo.is_empty:
        sys.exit("topo pequeno demais para rótulo")
    topo = max(topo.geoms, key=lambda g: g.area) if topo.geom_type == "MultiPolygon" else topo
    c = polylabel(topo, tolerance=0.05)

    def texto(alt):
        tp = TextPath((0, 0), a.rotulo, size=10, prop=FontProperties(family="DejaVu Sans", weight="bold"))
        ps = sorted((Polygon(p) for p in tp.to_polygons() if len(p) > 2), key=lambda p: -p.area)
        g = Polygon()
        for p in ps:                                              # contorno externo soma, furo subtrai
            g = g.difference(p) if g.contains(p) else g.union(p)
        b = g.bounds; s = alt / (b[3] - b[1])
        g = affinity.scale(g, s, s, origin=(0, 0)); b = g.bounds
        return affinity.translate(g, c.x - (b[0] + b[2]) / 2, c.y - (b[1] + b[3]) / 2)

    for alt in np.arange(8.0, 2.9, -0.5):                         # maior rótulo que cabe inteiro
        g = texto(alt)
        if topo.contains(g): break
    else:
        sys.exit("rótulo não cabe no topo nem com 3 mm")
    ex = trimesh.creation.extrude_polygon(g, a.profundidade + 0.5)
    ex.apply_translation([0, 0, zt - a.profundidade])
    v0 = r.volume
    r = trimesh.boolean.difference([r, ex], engine="manifold")
    print(f"rótulo '{a.rotulo}': {alt:.1f} mm de altura, {a.profundidade} mm de fundo, "
          f"{v0 - r.volume:.1f} mm3 removidos, fechado {r.is_watertight}")
    print("  conferir legibilidade na camada de dentro da letra no G-code, vista de cima (não espelha)")

r.export(a.saida)
print("salvo:", a.saida)
