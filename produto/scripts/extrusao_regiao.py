"""Extrusao de patch planar conectado, em sua normal GLOBAL, por distancia em mm.

Nao e deslocamento de vertices existentes. Usa bmesh.ops.extrude_face_region.
Sem certificacao de intersecoes com outras partes da peca.
"""
import bpy,bmesh,math
from mathutils import Vector

def executar(objeto,distancia_mm,tolerancia_plano_mm):
    obj=bpy.context.active_object
    if not obj or obj.name!=objeto or obj.type!='MESH' or obj.mode!='EDIT':
        raise ValueError('Ative o objeto nomeado em Edit Mode e selecione as faces do patch.')
    if len(bpy.context.objects_in_mode)!=1 or obj.data.users!=1 or obj.modifiers or obj.data.shape_keys:
        raise ValueError('Exige um unico objeto de malha exclusiva, sem modificadores/shape keys.')
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<=0 for x in (distancia_mm,tolerancia_plano_mm)):
        raise ValueError('Distancia de extrusao e tolerancia de plano devem ser finitas e positivas.')
    units=bpy.context.scene.unit_settings
    factor=1000*units.scale_length
    if units.system!='METRIC' or not math.isfinite(factor) or factor<=0:
        raise ValueError('Configure unidades metricas com escala positiva.')
    bm=bmesh.from_edit_mesh(obj.data);bm.normal_update()
    faces=[f for f in bm.faces if f.select and not f.hide]
    if not faces:raise ValueError('Selecione pelo menos uma face visivel.')
    selected=set(faces);visited={faces[0]};queue=list(visited)
    while queue:
        for e in queue.pop().edges:
            for f in e.link_faces:
                if f in selected and f not in visited:visited.add(f);queue.append(f)
    if visited!=selected:raise ValueError('Selecione um unico patch conectado por arestas.')
    matrix=obj.matrix_world.copy()
    if not all(math.isfinite(c) for row in matrix for c in row) or not all(math.isfinite(c) for v in bm.verts for c in v.co):
        raise ValueError('Coordenadas ou transformacao nao finitas.')
    inverse=matrix.to_3x3().inverted()
    normal=(inverse.transposed()@faces[0].normal).normalized()
    anchor=matrix@faces[0].verts[0].co
    if normal.length<.99:raise ValueError('Normal da face inicial degenerada.')
    for f in faces:
        n=(inverse.transposed()@f.normal).normalized()
        if n.dot(normal)<1-1e-6 or any(abs((matrix@v.co-anchor).dot(normal))*factor>tolerancia_plano_mm for v in f.verts):
            raise ValueError('Patch nao planar ou orientacao inconsistente; esta receita nao o extruda.')
    edges={e for f in faces for e in f.edges}
    boundary=[e for e in edges if sum(f in selected for f in e.link_faces)==1]
    if not boundary:raise ValueError('Patch sem contorno: nao extrudar toda uma casca fechada.')
    if any(len(e.link_faces)>2 for e in edges):raise ValueError('Patch contem aresta nao manifold.')
    # Save full mesh layers for rollback if native operation raises.
    backup=bpy.data.meshes.new('_extrusao_rollback');bm.to_mesh(backup)
    try:
        old={v:tuple(v.co) for v in bm.verts}
        result=bmesh.ops.extrude_face_region(bm,geom=faces+list(edges))
        new=[v for v in result['geom'] if isinstance(v,bmesh.types.BMVert)]
        if not new:raise ValueError('Operador nativo nao criou vertices.')
        delta=inverse@(normal*(distancia_mm/factor))
        bmesh.ops.translate(bm,verts=new,vec=delta)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if any(tuple(v.co)!=co for v,co in old.items() if v.is_valid):
            raise ValueError('Operacao alterou vertice preexistente; revertida.')
        error=max(abs((matrix@v.co-anchor).dot(normal)*factor-distancia_mm) for v in new)
        if not math.isfinite(error) or error>max(tolerancia_plano_mm,1e-5):raise ValueError('Altura medida diverge; revertida.')
        for f in bm.faces:f.select_set(all(v in new for v in f.verts))
        bm.select_flush_mode();bmesh.update_edit_mesh(obj.data,destructive=True)
        return {'estado':'EXTRUSAO_MEDIDA','objeto':objeto,'distancia_mm':distancia_mm,
                'normal_global':list(normal),'novos_vertices':len(new),'erro_altura_mm':error,
                'nao_verificado':['auto-intersecao','colisao com outras regioes','espessura','fabricacao']}
    except Exception:
        bm.clear();bm.from_mesh(backup);bmesh.update_edit_mesh(obj.data,destructive=True)
        raise
    finally:bpy.data.meshes.remove(backup)
