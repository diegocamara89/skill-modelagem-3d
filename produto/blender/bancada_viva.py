bl_info = {
    "name": "Bancada viva",
    "author": "modelagem-3d",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "Viewport 3D",
    "description": "Letras A, B, C na ordem do clique, marcas do agente, Overlays e anotação na superfície",
    "category": "3D View",
}

import json

import blf
import bmesh
import bpy
from bpy.app.handlers import persistent
from bpy_extras import view3d_utils

CHAVE = "poc_letras_handler"  # mesma chave da instalação antiga pela ponte: reinstalar substitui, não duplica
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


def _texto(font, x, y, s, tam, cor):
    blf.size(font, tam)
    blf.color(font, *cor)
    blf.position(font, x, y, 0)
    blf.draw(font, s)


def desenha():
    ctx = bpy.context
    region, rv3d = ctx.region, ctx.region_data
    if region is None or rv3d is None:
        return
    font = 0
    blf.enable(font, blf.SHADOW)
    blf.shadow(font, 5, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font, 2, -2)
    # Marcas do agente (ciano), em qualquer modo: "meça de A até B".
    for o in ctx.view_layer.objects:
        letra = o.get("marca_agente")
        if letra:
            p = view3d_utils.location_3d_to_region_2d(region, rv3d, o.matrix_world.translation)
            if p is not None:
                _texto(font, p.x + 10, p.y + 6, str(letra), 28, (0.2, 0.9, 1.0, 1.0))
    # Cliques do operador (amarelo), na ordem do clique, só em Edit Mode.
    objs = sorted([o for o in ctx.view_layer.objects if o.type == "MESH" and o.mode == "EDIT"], key=lambda o: o.name)
    i = 0
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        hist = [e for e in bm.select_history if e.is_valid and e.select]
        fe_nomes = [f["nome"] for f in json.loads(obj["feicoes"])] if "feicoes" in obj else None
        mw = obj.matrix_world
        for e in hist:
            if i >= len(LETRAS):
                break
            p = view3d_utils.location_3d_to_region_2d(region, rv3d, _centro(e, mw))
            if p is not None:
                _texto(font, p.x + 10, p.y + 6, LETRAS[i], 28, (1.0, 0.85, 0.1, 1.0))
                r = _rotulo(e, bm, fe_nomes) or (obj.name if len(objs) > 1 else "")
                if r:
                    _texto(font, p.x + 34, p.y + 8, r, 13, (1.0, 1.0, 1.0, 1.0))
            i += 1
    blf.disable(font, blf.SHADOW)


def _prepara_vista():
    """Overlays ligados (sem eles a seleção não aparece) e anotação grudada na superfície, em toda cena."""
    try:
        for sc in bpy.data.scenes:
            sc.tool_settings.annotation_stroke_placement_view3d = "SURFACE"
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == "VIEW_3D":
                    for s in a.spaces:
                        if s.type == "VIEW_3D":
                            s.overlay.show_overlays = True
                    a.tag_redraw()
    except Exception:
        pass
    return None  # timer de uma vez só


@persistent
def _ao_abrir(_arquivo):
    bpy.app.timers.register(_prepara_vista, first_interval=0.5)


def register():
    ns = bpy.app.driver_namespace
    if ns.get(CHAVE):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(ns[CHAVE], "WINDOW")
        except Exception:
            pass
    ns[CHAVE] = bpy.types.SpaceView3D.draw_handler_add(desenha, (), "WINDOW", "POST_PIXEL")
    if _ao_abrir not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_ao_abrir)
    bpy.app.timers.register(_prepara_vista, first_interval=1.0)


def unregister():
    ns = bpy.app.driver_namespace
    if ns.get(CHAVE):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(ns.pop(CHAVE), "WINDOW")
        except Exception:
            pass
    if _ao_abrir in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_ao_abrir)
