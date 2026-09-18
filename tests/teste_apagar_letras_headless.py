"""Blender headless: cubo 20 mm com lasca 0,2 x 2 x 3 colada na face +X. Seleciona as faces da lasca
(exceto a base, que está dentro do cubo), roda apagar_selecao e confere: sem borda, manifold, volume = 8000."""
import bpy, bmesh, json, sys, numpy as np
import os
PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "produto", "scripts")
sys.path.insert(0, PASTA)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
saida = args[args.index("--resultado-em") + 1] if "--resultado-em" in args else None
r = {}
try:
    sc = bpy.data.scenes.new("TRABALHO_AGENTE")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cubo_lasca.stl"), "rb") as f:
        f.read(80); n = int(np.frombuffer(f.read(4), dtype="<u4")[0])
        dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]); d = np.frombuffer(f.read(n * 50), dtype=dt)
    tri = d["v"].astype(np.float64).reshape(-1, 3); _, idx, inv = np.unique(np.round(tri, 5), axis=0, return_index=True, return_inverse=True)
    me = bpy.data.meshes.new("cubo_lasca"); me.from_pydata(tri[idx].tolist(), [], inv.reshape(-1, 3).tolist()); me.validate(); me.update()
    obj = bpy.data.objects.new("cubo_lasca", me); sc.collection.objects.link(obj)
    bpy.context.window.scene = sc if bpy.context.window else None
    with bpy.context.temp_override(scene=sc):
        sc.view_layers[0].objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(me)
    n_sel = 0
    for f in bm.faces:
        c = f.calc_center_median()
        f.select = c.x > 10.0 + 1e-4   # tudo que sobressai da face x=10
        n_sel += f.select
    bmesh.update_edit_mesh(me)
    r["selecionadas"] = n_sel
    CONFIG = {"pasta": PASTA, "acao": "apagar", "args": {}}
    codigo = open(PASTA + r"\ponte_letras_blender.py", encoding="utf-8").read()
    import io, contextlib
    buf = io.StringIO()
    ns = {"CONFIG": CONFIG, "__name__": "_ponte"}
    with contextlib.redirect_stdout(buf):
        exec(compile(codigo, "ponte_letras_blender.py", "exec"), ns)
    for linha in buf.getvalue().splitlines():
        if linha.startswith("LETRAS_RESULTADO="):
            r["apagar"] = json.loads(linha[len("LETRAS_RESULTADO="):])
    obj.update_from_editmode()
    bm = bmesh.from_edit_mesh(me)
    r["depois"] = {"faces": len(bm.faces), "arestas_borda": sum(1 for e in bm.edges if e.is_boundary),
                   "arestas_nao_manifold": sum(1 for e in bm.edges if not e.is_manifold), "volume": round(bm.calc_volume(), 3)}
    r["estado"] = "OK"
except Exception as e:
    import traceback; r.update(estado="EXCECAO", erro=repr(e), tb=traceback.format_exc())
if saida:
    open(saida, "w", encoding="utf-8").write(json.dumps(r, ensure_ascii=False, indent=1))
print(json.dumps(r, ensure_ascii=False)[:800])
