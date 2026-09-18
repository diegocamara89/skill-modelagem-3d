"""Headless: cubo 20 mm em cena mm. Testa mover (+2 Z na face de cima), extrudar (2 mm na face +X),
preencher (apaga uma face e fecha), arredondar (bevel das quinas da face de cima), desfazer."""
import bpy, bmesh, json, sys, io, contextlib
import os
PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "produto", "scripts")
sys.path.insert(0, PASTA)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
saida = args[args.index("--resultado-em") + 1] if "--resultado-em" in args else None
codigo = open(PASTA + r"\ponte_letras_blender.py", encoding="utf-8").read()

def ponte(acao, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(codigo, "ponte_letras_blender.py", "exec"), {"CONFIG": {"pasta": PASTA, "acao": acao, "args": kw}, "__name__": "_p"})
    for l in buf.getvalue().splitlines():
        if l.startswith("LETRAS_RESULTADO="):
            return json.loads(l[len("LETRAS_RESULTADO="):])
    return {"estado": "SEM_RESULTADO", "saida": buf.getvalue()[-800:]}

r = {}
try:
    sc = bpy.data.scenes.new("TRABALHO_AGENTE"); sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001
    bm0 = bmesh.new(); bmesh.ops.create_cube(bm0, size=20.0)
    me = bpy.data.meshes.new("cubo"); bm0.to_mesh(me); bm0.free()
    obj = bpy.data.objects.new("cubo", me); sc.collection.objects.link(obj)
    wm = bpy.data.window_managers[0]
    if wm.windows: wm.windows[0].scene = sc
    with bpy.context.temp_override(scene=sc):
        sc.view_layers[0].objects.active = obj; bpy.ops.object.mode_set(mode="EDIT")
    sc.tool_settings.mesh_select_mode = (False, False, True)
    def selecionar(pred):
        bm = bmesh.from_edit_mesh(me)
        for v in bm.verts: v.select = False
        for e in bm.edges: e.select = False
        for f in bm.faces: f.select = False
        for f in bm.faces:
            if pred(f): f.select = True
        bm.select_flush(True); bmesh.update_edit_mesh(me)
    def dims():
        obj.update_from_editmode(); bm = bmesh.from_edit_mesh(me)
        zs = [v.co.z for v in bm.verts]; xs = [v.co.x for v in bm.verts]
        return {"altura": round(max(zs) - min(zs), 4), "largura_x": round(max(xs) - min(xs), 4), "volume": round(bm.calc_volume(), 3), "faces": len(bm.faces)}
    r["inicio"] = dims()
    # 1 mover: face de cima +2 em Z
    selecionar(lambda f: f.normal.z > 0.9); r["mover"] = ponte("mover", eixo="Z", mm=2.0); r["apos_mover"] = dims()
    # 2 desfazer
    r["desfazer"] = ponte("desfazer"); r["apos_desfazer"] = dims()
    # 3 extrudar face +X em 2 mm
    selecionar(lambda f: f.normal.x > 0.9); r["extrudar"] = ponte("extrudar", mm=2.0); r["apos_extrudar"] = dims()
    # 4 preencher: apagar a face -X e fechar
    selecionar(lambda f: f.normal.x < -0.9)
    bm = bmesh.from_edit_mesh(me); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.select], context="FACES")
    for e in bm.edges: e.select = e.is_boundary
    for f in bm.faces: f.select = any(e.is_boundary for e in f.edges)
    bm.select_flush(True); bmesh.update_edit_mesh(me)
    r["furo_aberto"] = sum(1 for e in bm.edges if e.is_boundary)
    r["preencher"] = ponte("preencher", modo="contorno"); r["apos_preencher"] = dims()
    obj.update_from_editmode(); bm = bmesh.from_edit_mesh(me); r["bordas_apos_preencher"] = sum(1 for e in bm.edges if e.is_boundary)
    # 5 arredondar quinas da face de cima, raio 1, 4 seg
    selecionar(lambda f: f.normal.z > 0.9); r["arredondar"] = ponte("arredondar", raio_mm=1.0, segmentos=4); r["apos_arredondar"] = dims()
    r["estado"] = "OK"
except Exception as e:
    import traceback; r.update(estado="EXCECAO", erro=repr(e), tb=traceback.format_exc())
if saida:
    open(saida, "w", encoding="utf-8").write(json.dumps(r, ensure_ascii=False, indent=1))
print(json.dumps(r, ensure_ascii=False)[:600])
