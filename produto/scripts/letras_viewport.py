"""Instala, na sessão viva, o desenho das letras A, B, C... ao lado de cada elemento
clicado, na ORDEM do clique (bm.select_history). Some quando a seleção é limpa.
Reinstalar substitui o anterior. Instale com: python scripts/ponte_letras.py instalar_letras
Some quando o Blender fecha: reinstalar a cada sessão."""
import bpy
import bmesh
import blf
from bpy_extras import view3d_utils

CHAVE = "poc_letras_handler"
LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _centro(e, mw):
    if isinstance(e, bmesh.types.BMFace):
        return mw @ e.calc_center_median()
    if isinstance(e, bmesh.types.BMEdge):
        return mw @ ((e.verts[0].co + e.verts[1].co) / 2)
    return mw @ e.co


def _rotulo(e, bm, fe_nomes):
    camada = bm.faces.layers.int.get("rasgo")
    if camada is None or fe_nomes is None:
        return ""
    if isinstance(e, bmesh.types.BMFace):
        k = e[camada]
    else:
        ks = {f[camada] for f in e.link_faces}
        k = ks.pop() if len(ks) == 1 else -1
    return fe_nomes[k] if 0 <= k < len(fe_nomes) else "fora"


def desenha():
    ctx = bpy.context
    region, rv3d = ctx.region, ctx.region_data
    if region is None or rv3d is None:
        return
    objs = sorted([o for o in ctx.view_layer.objects if o.type == "MESH" and o.mode == "EDIT"], key=lambda o: o.name)
    if not objs:
        return
    font = 0
    blf.enable(font, blf.SHADOW)
    blf.shadow(font, 5, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font, 2, -2)
    i = 0
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        hist = [e for e in bm.select_history if e.is_valid and e.select]
        if not hist:
            continue
        fe_nomes = None
        if "feicoes" in obj:
            import json
            fe_nomes = [f["nome"] for f in json.loads(obj["feicoes"])]
        mw = obj.matrix_world
        for e in hist:
            if i >= 26:
                break
            p = view3d_utils.location_3d_to_region_2d(region, rv3d, _centro(e, mw))
            if p is not None:
                blf.size(font, 28)
                blf.color(font, 1.0, 0.85, 0.1, 1.0)
                blf.position(font, p.x + 10, p.y + 6, 0)
                blf.draw(font, LETRAS[i])
                r = _rotulo(e, bm, fe_nomes) or (obj.name if len(objs) > 1 else "")
                if r:
                    blf.size(font, 13)
                    blf.color(font, 1.0, 1.0, 1.0, 1.0)
                    blf.position(font, p.x + 34, p.y + 8, 0)
                    blf.draw(font, r)
            i += 1
    blf.disable(font, blf.SHADOW)


ns = bpy.app.driver_namespace
if ns.get(CHAVE):
    try:
        bpy.types.SpaceView3D.draw_handler_remove(ns[CHAVE], "WINDOW")
    except Exception:
        pass
ns[CHAVE] = bpy.types.SpaceView3D.draw_handler_add(desenha, (), "WINDOW", "POST_PIXEL")
for w in bpy.data.window_managers[0].windows:
    for a in w.screen.areas:
        a.tag_redraw()
print("LETRAS_INSTALADAS")
