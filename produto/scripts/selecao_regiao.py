"""Expandir faces por arestas compartilhadas, com plano ancora opcional.

Opera somente selecao; nao altera coordenadas ou topologia. Preview sem escrita.
Faces ocultas sao barreiras. Nao infere a intencao do usuario.
"""
import math
import bpy
import bmesh


def planejar(objeto, modo='conectada', angulo_graus=None, distancia_mm=None):
    obj = bpy.context.active_object
    if not obj or obj.name != objeto or obj.type != 'MESH' or obj.mode != 'EDIT':
        raise ValueError('Ative o objeto informado em Edit Mode e selecione uma face semente.')
    if len(bpy.context.objects_in_mode) != 1 or obj.data.users != 1:
        raise ValueError('Selecione um unico objeto com malha exclusiva.')
    if obj.modifiers or obj.data.shape_keys:
        raise ValueError('A selecao atua na malha base; resolva modificadores/shape keys antes desta receita.')
    if modo not in ('conectada', 'plano'):
        raise ValueError('Modo deve ser conectada ou plano.')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table(); bm.faces.index_update()
    seeds = [f for f in bm.faces if f.select and not f.hide]
    if len(seeds) != 1:
        raise ValueError('Esta receita exige exatamente uma face semente visivel; escolha a regiao antes de expandir.')
    seed = seeds[0]
    matrix = obj.matrix_world.copy()
    def points(face): return [matrix @ v.co for v in face.verts]
    if modo == 'plano':
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in (angulo_graus,distancia_mm)):
            raise ValueError('Declare angulo e distancia finitos para o plano ancora.')
        if not 0 <= angulo_graus < 90 or distancia_mm < 0:
            raise ValueError('Angulo deve estar entre 0 e 90 exclusivos no topo; distancia nao negativa.')
        units = bpy.context.scene.unit_settings
        if units.system != 'METRIC' or not math.isfinite(units.scale_length) or units.scale_length <= 0:
            raise ValueError('Configure unidades metricas antes de comparar distancia em mm.')
        transform = matrix.to_3x3().inverted().transposed()
        normal = (transform @ seed.normal).normalized()
        anchor = points(seed)[0]
        cosine = math.cos(math.radians(angulo_graus))
        def allowed(face):
            n = (transform @ face.normal).normalized()
            return (n.dot(normal) >= cosine-1e-12 and
                    max(abs((p-anchor).dot(normal))*1000*units.scale_length for p in points(face)) <= distancia_mm+1e-9)
        if not allowed(seed):
            raise ValueError('A face semente nao e plana dentro da tolerancia declarada.')
    else:
        allowed = lambda face: True
    visited = {seed}
    queue = [seed]
    while queue:
        face = queue.pop()
        for edge in face.edges:
            for other in edge.link_faces:
                if other not in visited and not other.hide and allowed(other):
                    visited.add(other); queue.append(other)
    return {'estado':'SELECAO_PLANEJADA','objeto':objeto,'modo':modo,
            'semente':seed.index,'faces':sorted(f.index for f in visited),
            'nao_verificado':['intencao do usuario','superficie avaliada por modificadores']}


def executar(objeto, modo='conectada', angulo_graus=None, distancia_mm=None, aplicar=False):
    plan = planejar(objeto,modo,angulo_graus,distancia_mm)
    if aplicar:
        bm=bmesh.from_edit_mesh(bpy.context.active_object.data)
        targets=set(plan['faces'])
        for f in bm.faces: f.select_set(f.index in targets)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(bpy.context.active_object.data,destructive=False)
        plan['estado']='SELECAO_APLICADA'
    return plan
