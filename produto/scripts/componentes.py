"""Lista os corpos de um 3MF/STL com assinatura geometrica, para identificar peca por
GEOMETRIA e nao por nome ou contagem de faces.

Por que: dois corpos podem ter a mesma contagem de faces (variantes de uma mesma malha);
e num 3MF "dividido em objetos" pelo Bambu Studio os nomes dos nos que o trimesh devolve
NAO batem com os nomes mostrados no Studio. Foi assim que duas pecas foram trocadas e
um arquivo errado foi entregue (22/09/2026).

Mostra, por corpo: faces, dimensoes, canto minimo e centro. Para 3MF com varios objetos,
mostra tambem o nome do Studio (Metadata/model_settings.config) e o centro gravado no
transform do <item> (3D/3dmodel.model) — case pelo centro.

Confirmar SEMPRE com render isolado de cada corpo, com o rotulo escrito na imagem
(ver referencias/render_de_conferencia.md). A tabela aponta; o render confirma.

Uso:  python componentes.py arquivo.3mf|arquivo.stl
"""
import sys, re, zipfile, numpy as np, trimesh

f = sys.argv[1]
if f.lower().endswith(".3mf"):
    s = trimesh.load(f, file_type="3mf")
    corpos = []
    for node in s.graph.nodes_geometry:
        T, g = s.graph[node]
        m = s.geometry[g].copy(); m.apply_transform(T)
        for c in m.split(only_watertight=False):
            corpos.append((str(node), c))
    z = zipfile.ZipFile(f)
    try:
        ms = z.read("Metadata/model_settings.config").decode()
        nomes = {}
        for mm in re.finditer(r'<object id="(\d+)">(.*?)</object>', ms, re.S):
            n = re.search(r'key="name" value="([^"]+)"', mm.group(2))
            nomes[mm.group(1)] = n.group(1) if n else "?"
        mod = z.read("3D/3dmodel.model").decode()
        print("objetos no Studio (nome -> centro gravado):")
        for mm in re.finditer(r'<item objectid="(\d+)"[^>]*transform="([^"]+)"', mod):
            t = [float(v) for v in mm.group(2).split()]
            print(f"   {nomes.get(mm.group(1), '?'):24} x={t[9]:8.2f} y={t[10]:8.2f}")
    except KeyError:
        pass
else:
    corpos = [("-", c) for c in trimesh.load(f, force="mesh").split(only_watertight=False)]

lasca = [c for c in corpos if len(c[1].faces) < 4]
corpos = [c for c in corpos if len(c[1].faces) >= 4]
if lasca:
    print(f"\nignorados {len(lasca)} corpo(s) com menos de 4 faces (lasca degenerada na malha)")
print(f"\n{len(corpos)} corpos:")
print(f"{'no':>5} {'faces':>7} {'dx':>7} {'dy':>7} {'dz':>7}  {'min x':>8} {'min y':>8}  {'centro x':>9} {'centro y':>9}")
for node, c in sorted(corpos, key=lambda t: (round(t[1].bounds[0][1]), t[1].bounds[0][0])):
    lo, hi = c.bounds; d = hi - lo; ce = (lo + hi) / 2
    print(f"{node:>5} {len(c.faces):7d} {d[0]:7.2f} {d[1]:7.2f} {d[2]:7.2f}  {lo[0]:8.2f} {lo[1]:8.2f}  {ce[0]:9.2f} {ce[1]:9.2f}")
