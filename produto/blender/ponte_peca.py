"""Ponte ao vivo: um gera.py (manifold3d) vira peça no Blender com painel de medidas e acabamentos.

RODA DENTRO DO BLENDER. Quem carrega é scripts/mostrar_no_blender.py (peca: gera.py); não chame à mão.

Contrato do gera.py:
  PARAMS = [("chave", "Rótulo", padrão, mínimo, máximo), ...]   # mm
  def gera(**medidas) -> manifold3d.Manifold

Painel: Propriedades > chave inglesa (Modificadores) > "Medidas da peça".
- Medidas: mudar refaz a peça (ms) a partir do gera.py; valor fora do mínimo/máximo é trazido para dentro.
- Acabamentos: arredondar/chanfrar arestas escolhidas no modo de edição; cada um com tamanho próprio, refeito a
  cada geração (como a árvore de recursos de um CAD).
- Face lógica: triângulos do mesmo plano viram uma face (face com furo fica em 2: o Blender não aceita furo dentro
  de face). Aresta viva = dobra > 30° ou separa formas diferentes do gera.py fora do mesmo plano; "Selecionar face
  inteira" pega tudo até as arestas vivas, plano ou curvo.
Várias peças ao mesmo tempo: cada objeto guarda o caminho do seu gera.py.
"""
import bpy, bmesh, contextlib, importlib.util, json, math, os, sys, time
import numpy as np
from mathutils import Vector

for _p in (bpy.utils.user_resource("SCRIPTS", path="modules"),
           os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender",
                        "%d.%d" % bpy.app.version[:2], "scripts", "modules")):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

CENA = "TRABALHO_AGENTE"
DENSIDADE_PETG = 1.27  # g/cm³
ANGULO_VIVO = math.radians(30)
NOME_TIPO = {"arredonda": "Arredondamento", "chanfra": "Chanfro"}
GERAS = {}  # caminho -> (mtime, módulo)
TRAVA = {"on": False}


@contextlib.contextmanager
def _travado():
    """segura as atualizações enquanto vários campos mudam; solta mesmo se der erro no meio"""
    TRAVA["on"] = True
    try:
        yield
    finally:
        TRAVA["on"] = False


# ---------------------------------------------------------------- geração

def _modulo(caminho):
    mt = os.path.getmtime(caminho)
    if caminho not in GERAS or GERAS[caminho][0] != mt:
        spec = importlib.util.spec_from_file_location("gera_" + str(abs(hash(caminho))), caminho)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "PARAMS") or not hasattr(mod, "gera"):
            raise ValueError("o gera.py precisa de PARAMS e de def gera(**medidas)")
        GERAS[caminho] = (mt, mod)
    return GERAS[caminho][1]


def _acha_aresta(bm, lo, tam, ac):
    """aresta cujo meio está mais perto do ponto gravado (em fração da caixa) e com a mesma direção"""
    alvo = Vector(lo) + Vector([a * b for a, b in zip(ac.p, tam)])
    d = Vector(ac.d)
    cand = [e for e in bm.edges if e.is_valid and abs((e.verts[1].co - e.verts[0].co).normalized().dot(d)) > 0.999]
    e = min(cand, key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - alvo).length, default=None)
    limite = 0.5 + 0.05 * Vector(tam).length  # aresta que sumiu não vira "a paralela mais perto", longe que seja
    return e if e is not None and ((e.verts[0].co + e.verts[1].co) / 2 - alvo).length <= limite else None


def _troca_malha(ob, peca):
    m = peca.to_mesh()
    v = np.asarray(m.vert_properties, dtype=np.float64)[:, :3]
    lo, tam = v.min(0), np.maximum(v.max(0) - v.min(0), 1e-9)
    # origem de cada triângulo: qual caixa/cilindro/cone do gera.py o criou (o manifold3d guarda isso nas booleanas)
    origem_tri = np.repeat(np.asarray(m.run_original_id), np.diff(np.asarray(m.run_index) // 3))
    bm = bmesh.new()
    origem = bm.faces.layers.int.new("origem")
    vs = [bm.verts.new(p) for p in v.tolist()]
    for (a, b, c), o in zip(np.asarray(m.tri_verts).tolist(), origem_tri.tolist()):
        bm.faces.new((vs[a], vs[b], vs[c]))[origem] = o
    bm.normal_update()  # sem normais o dissolve não junta nada
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1), verts=bm.verts[:], edges=bm.edges[:])
    falhas = []
    for i, ac in enumerate(ob.peca_acab):  # reaplica, a cada geração, os acabamentos gravados
        e = _acha_aresta(bm, lo, tam, ac)
        if e is None:
            falhas.append(f"{i + 1}. {NOME_TIPO[ac.tipo]}")
            continue
        r = bmesh.ops.bevel(bm, geom=[e], offset=ac.tamanho, offset_type="OFFSET",
                            segments=8 if ac.tipo == "arredonda" else 1, profile=0.5, affect="EDGES", clamp_overlap=True)
        for f in r["faces"]:
            f[origem] = 100000 + i  # cada acabamento é uma face lógica própria
    bm.normal_update()
    for e in bm.edges:  # aresta viva: dobra > 30°, ou separa origens diferentes fora do mesmo plano
        if len(e.link_faces) == 2:
            f1, f2 = e.link_faces
            ang = e.calc_face_angle(0.0)
            e.smooth = not (ang > ANGULO_VIVO or (f1[origem] != f2[origem] and ang > math.radians(0.5)))
    for f in bm.faces:
        f.smooth = True
    vol = bm.calc_volume(signed=True)
    abertas = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    ob.peca_int.bbox_lo, ob.peca_int.bbox_tam = lo.tolist(), tam.tolist()
    return vol, abertas, falhas


def atualiza(ob):
    """refaz a peça a partir do gera.py com as medidas do painel; erro mantém a peça anterior e avisa"""
    if TRAVA["on"] or not ob.peca_int.caminho:
        return None
    if ob.mode == "EDIT":
        bpy.ops.object.mode_set(mode="OBJECT")
    t0 = time.perf_counter()
    try:
        peca = _modulo(ob.peca_int.caminho).gera(**{p.chave: p.valor for p in ob.peca_params})
        if peca.is_empty():
            raise ValueError("a peça ficou vazia com essas medidas")
        vol, abertas, falhas = _troca_malha(ob, peca)
        ob.peca_int.volume, ob.peca_int.erro = vol, ""
        if abertas or falhas:
            ob.peca_int.erro = f"{abertas} arestas abertas; acabamento sem aresta: {', '.join(falhas)}"
    except Exception as e:
        ob.peca_int.erro = f"{type(e).__name__}: {e}"[:160]
    ob.peca_int.ms = (time.perf_counter() - t0) * 1000
    return {"volume_mm3": round(ob.peca_int.volume, 1), "ms": round(ob.peca_int.ms, 1), "erro": ob.peca_int.erro}


# ---------------------------------------------------------------- propriedades

def _param_mudou(self, context):
    if TRAVA["on"]:
        return
    v = min(max(self.valor, self.minimo), self.maximo)
    if v != self.valor:
        with _travado():
            self.valor = v
    atualiza(self.id_data)


def _acab_mudou(self, context):
    atualiza(self.id_data)


class PecaParam(bpy.types.PropertyGroup):
    chave: bpy.props.StringProperty()
    rotulo: bpy.props.StringProperty()
    valor: bpy.props.FloatProperty(subtype="DISTANCE", unit="LENGTH", precision=2, update=_param_mudou)
    minimo: bpy.props.FloatProperty()
    maximo: bpy.props.FloatProperty()
    padrao: bpy.props.FloatProperty()  # padrão do gera.py quando foi carregado: valor igual a ele = operador não mexeu


class PecaAcabamento(bpy.types.PropertyGroup):
    tipo: bpy.props.EnumProperty(items=[("arredonda", "Arredondar", ""), ("chanfra", "Chanfrar", "")],
                                 update=_acab_mudou)
    tamanho: bpy.props.FloatProperty(name="Tamanho", default=1.0, min=0.1, max=10.0, subtype="DISTANCE",
                                     unit="LENGTH", precision=2, update=_acab_mudou)
    p: bpy.props.FloatVectorProperty(size=3)  # meio da aresta, em fração da caixa da peça
    d: bpy.props.FloatVectorProperty(size=3)  # direção da aresta


class PecaInterno(bpy.types.PropertyGroup):
    caminho: bpy.props.StringProperty()
    rotulo: bpy.props.StringProperty()
    bbox_lo: bpy.props.FloatVectorProperty(size=3)
    bbox_tam: bpy.props.FloatVectorProperty(size=3)
    volume: bpy.props.FloatProperty()
    ms: bpy.props.FloatProperty()
    erro: bpy.props.StringProperty()


# ---------------------------------------------------------------- botões e painel

def _peca(context):
    ob = context.active_object
    return ob if ob is not None and hasattr(ob, "peca_int") and ob.peca_int.caminho else None


class PECA_OT_acabamento(bpy.types.Operator):
    """Grava arredondamento ou chanfro nas arestas selecionadas; ele é refeito sozinho quando as medidas mudam"""
    bl_idname, bl_label, bl_options = "peca.acabamento", "Acabamento nas arestas", {"REGISTER", "UNDO"}
    tipo: bpy.props.EnumProperty(items=[("arredonda", "Arredondar", ""), ("chanfra", "Chanfrar", "")])

    def execute(self, context):
        ob = _peca(context)
        if ob is None or ob.mode != "EDIT":
            self.report({"ERROR"}, "Aperte Tab, tecla 2 (arestas) e clique na aresta")
            return {"CANCELLED"}
        sel = [e for e in bmesh.from_edit_mesh(ob.data).edges if e.select]
        if not sel:
            self.report({"ERROR"}, "Nenhuma aresta selecionada")
            return {"CANCELLED"}
        lo, tam = ob.peca_int.bbox_lo, ob.peca_int.bbox_tam
        with _travado():  # grava tudo antes de refazer a peça uma vez só
            for e in sel:
                meio = (e.verts[0].co + e.verts[1].co) / 2
                ac = ob.peca_acab.add()
                ac.tipo, ac.tamanho = self.tipo, 1.0
                ac.p = [(meio[i] - lo[i]) / tam[i] for i in range(3)]
                ac.d = (e.verts[1].co - e.verts[0].co).normalized()
        atualiza(ob)
        return {"FINISHED"}


class PECA_OT_apaga_acabamento(bpy.types.Operator):
    """Apaga este acabamento"""
    bl_idname, bl_label, bl_options = "peca.apaga_acabamento", "Apagar acabamento", {"REGISTER", "UNDO"}
    indice: bpy.props.IntProperty()

    def execute(self, context):
        ob = _peca(context)
        ob.peca_acab.remove(self.indice)
        atualiza(ob)
        return {"FINISHED"}


class PECA_OT_face_inteira(bpy.types.Operator):
    """Seleciona a face inteira (plana ou curva) a partir de um pedaço clicado: tudo até as arestas vivas"""
    bl_idname, bl_label, bl_options = "peca.face_inteira", "Selecionar face inteira", {"REGISTER", "UNDO"}

    def execute(self, context):
        ob = context.active_object
        if ob is None or ob.mode != "EDIT":
            self.report({"ERROR"}, "Aperte Tab, tecla 3 (faces) e clique num pedaço da face")
            return {"CANCELLED"}
        bpy.ops.mesh.select_linked(delimit={"SHARP"})
        return {"FINISHED"}


class PROPERTIES_PT_peca_medidas(bpy.types.Panel):
    bl_space_type, bl_region_type, bl_context, bl_label = "PROPERTIES", "WINDOW", "modifier", "Medidas da peça"

    @classmethod
    def poll(cls, context):
        return _peca(context) is not None

    def draw(self, context):
        ob, col = _peca(context), self.layout.column()
        if ob.peca_int.rotulo:
            col.label(text=ob.peca_int.rotulo, icon="LINKED")
        for p in ob.peca_params:
            col.prop(p, "valor", text=p.rotulo)
        if any(abs(s - 1) > 1e-6 for s in ob.scale) or ob.modifiers:
            col.label(text="Escala diferente de 1 ou modificador extra muda a medida real", icon="ERROR")
        if ob.peca_int.erro:
            col.label(text="Não deu: " + ob.peca_int.erro, icon="ERROR")
        vol = ob.peca_int.volume
        col.label(text=f"Volume {vol:.0f} mm³  ·  ≈ {vol / 1000 * DENSIDADE_PETG:.1f} g de PETG maciço")
        col.label(text=f"Refeita em {ob.peca_int.ms:.0f} ms")
        caixa = self.layout.box()
        caixa.label(text="Acabamentos (aresta selecionada no modo de edição)")
        linha = caixa.row()
        linha.operator("peca.acabamento", text="Arredondar").tipo = "arredonda"
        linha.operator("peca.acabamento", text="Chanfrar").tipo = "chanfra"
        for i, ac in enumerate(ob.peca_acab):
            linha = caixa.row(align=True)
            linha.label(text=f"{i + 1}. {NOME_TIPO[ac.tipo]}")
            linha.prop(ac, "tamanho", text="")
            linha.operator("peca.apaga_acabamento", text="", icon="X").indice = i
        self.layout.operator("peca.face_inteira", icon="FACESEL")


CLASSES = (PecaParam, PecaAcabamento, PecaInterno, PECA_OT_acabamento, PECA_OT_apaga_acabamento,
           PECA_OT_face_inteira, PROPERTIES_PT_peca_medidas)


def registra():
    """registra (ou re-registra, ao trocar este arquivo) mantendo os dados das peças já abertas"""
    for nome in ("peca_params", "peca_acab", "peca_int"):
        if hasattr(bpy.types.Object, nome):
            delattr(bpy.types.Object, nome)
    for cls in CLASSES:
        velha = getattr(bpy.types, cls.__name__, None)
        if velha is not None:
            bpy.utils.unregister_class(velha)
        bpy.utils.register_class(cls)
    bpy.types.Object.peca_params = bpy.props.CollectionProperty(type=PecaParam)
    bpy.types.Object.peca_acab = bpy.props.CollectionProperty(type=PecaAcabamento)
    bpy.types.Object.peca_int = bpy.props.PointerProperty(type=PecaInterno)


# ---------------------------------------------------------------- entrada (mostrar_no_blender.py)

def _cena():
    sc = bpy.data.scenes.get(CENA)
    nova = sc is None
    if nova:
        sc = bpy.data.scenes.new(CENA)
        sc.unit_settings.system, sc.unit_settings.scale_length = "METRIC", 0.001
        sc.unit_settings.length_unit = "MILLIMETERS"
        win = bpy.data.window_managers[0].windows[0] if bpy.data.window_managers[0].windows else None
        if win is not None:
            win.scene = sc
    return sc


def exporta(ob, caminho):
    """STL binário da peça como está (com acabamentos), nas coordenadas da própria peça, em mm"""
    me = ob.data
    me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    t = co[tri.reshape(-1, 3)]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    reg = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    reg["n"], reg["v"] = n, t
    with open(caminho, "wb") as f:
        f.write(b"ponte_peca".ljust(80, b" "))
        f.write(np.uint32(len(t)).tobytes())
        f.write(reg.tobytes())
    return {"stl": caminho, "triangulos": int(len(t))}


def carrega(caminho, objeto, rotulo="", exportar=None):
    """mostra/atualiza a peça do gera.py; mantém medidas e acabamentos que já estavam no objeto"""
    caminho = os.path.abspath(caminho)
    ob = bpy.data.objects.get(objeto)
    try:
        mod = _modulo(caminho)
        params = [tuple(p) for p in mod.PARAMS]
        ruins = [p for p in params if len(p) != 5]
        if ruins:
            raise ValueError(f"cada item de PARAMS precisa de (chave, rótulo, padrão, mín, máx): {ruins[:2]}")
    except Exception as e:
        erro = f"erro no gera.py: {type(e).__name__}: {e}"[:300]
        if ob is not None and hasattr(ob, "peca_int"):
            ob.peca_int.erro = erro[:160]
        return {"estado": "ERRO_NO_GERA", "objeto": objeto, "erro": erro}
    sc = _cena()
    if ob is None:
        ob = bpy.data.objects.new(objeto, bpy.data.meshes.new(objeto))
        sc.collection.objects.link(ob)
        outros = [o for o in sc.objects if o is not ob and o.type == "MESH" and o.name.startswith("AG_")]
        ob.location.x = max((o.location.x + o.dimensions.x for o in outros), default=-10.0) + 10.0  # ao lado
        bpy.context.view_layer.objects.active = ob
    antes = {p.chave: (p.valor, p.padrao) for p in ob.peca_params}
    with _travado():
        ob.peca_params.clear()
        for chave, rot, pad, mn, mx in params:
            valor, pad_antigo = antes.get(chave, (pad, pad))
            if abs(valor - pad_antigo) < 1e-6:  # o operador não mexeu: segue o padrão novo do gera.py
                valor = pad
            p = ob.peca_params.add()
            p.chave, p.rotulo, p.minimo, p.maximo, p.padrao = chave, rot, mn, mx, pad
            p.valor = min(max(valor, mn), mx)
        ob.peca_int.caminho, ob.peca_int.rotulo = caminho, rotulo
    out = {"estado": "MOSTRADO_AO_VIVO", "objeto": ob.name, **(atualiza(ob) or {}),
           "medidas": {p.chave: round(p.valor, 3) for p in ob.peca_params}, "acabamentos": len(ob.peca_acab)}
    if exportar and ob.peca_int.erro:
        out.update(exportado=False, motivo="peça com erro; STL não gravado")
    elif exportar:
        out.update(exporta(ob, exportar))
    for area in (bpy.data.window_managers[0].windows[0].screen.areas if bpy.data.window_managers[0].windows else []):
        area.tag_redraw()
    return out
