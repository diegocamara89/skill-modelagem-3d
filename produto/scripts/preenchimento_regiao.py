"""Preenche contorno planar convexo ou liga duas arestas paralelas coplanares.

Cria superficie, nao volume. Usa holes_fill / bridge_loops nativos.
"""
import bpy,bmesh,math
from mover_regiao import _objeto

def executar(objeto,modo,tolerancia_mm):
    obj=_objeto(objeto)
    if modo not in ('contorno','ponte'):raise ValueError('Modo deve ser contorno ou ponte.')
    if type(tolerancia_mm) not in (int,float) or not math.isfinite(tolerancia_mm) or tolerancia_mm<=0:raise ValueError('Tolerancia finita positiva exigida.')
    units=bpy.context.scene.unit_settings;factor=1000*units.scale_length
    if units.system!='METRIC' or not math.isfinite(factor) or factor<=0:raise ValueError('Unidades metricas exigidas.')
    mat=obj.matrix_world.copy()
    if not all(math.isfinite(c) for row in mat for c in row):raise ValueError('Transformacao nao finita.')
    bm=bmesh.from_edit_mesh(obj.data);edges=[e for e in bm.edges if e.select and not e.hide]
    if not edges or any(len(e.link_faces)>1 for e in edges):raise ValueError('Selecione somente arestas de borda ou soltas.')
    verts={v for e in edges for v in e.verts}
    if not all(math.isfinite(c) for v in bm.verts for c in v.co):raise ValueError('Coordenadas nao finitas.')
    degree={v:sum(v in e.verts for e in edges) for v in verts}
    if modo=='ponte':
        if len(edges)!=2 or len(verts)!=4:raise ValueError('Ponte desta receita exige duas arestas sem vertices compartilhados.')
        a,b=edges;u=mat@a.verts[1].co-mat@a.verts[0].co;v=mat@b.verts[1].co-mat@b.verts[0].co
        if min(u.length,v.length)*factor<=tolerancia_mm or abs(u.normalized().dot(v.normalized()))<1-1e-6:raise ValueError('Arestas devem ser paralelas e nao degeneradas.')
        ordered=[a.verts[0],a.verts[1]]
        ordered+=list(b.verts) if u.dot(v)<0 else list(reversed(b.verts))
    else:
        if len(verts)<3 or any(x!=2 for x in degree.values()):raise ValueError('Exige um contorno fechado simples, sem bifurcacao.')
        ordered=[edges[0].verts[0]];previous=None
        while True:
            current=ordered[-1];neighbors=[e.other_vert(current) for e in edges if current in e.verts and e.other_vert(current)!=previous]
            nxt=neighbors[0]
            if nxt==ordered[0]:break
            if nxt in ordered:raise ValueError('Contorno repetido.')
            ordered.append(nxt);previous=current
        if len(ordered)!=len(verts):raise ValueError('Selecione um unico contorno.')
    points=[mat@v.co for v in ordered];normal=(points[1]-points[0]).cross(points[2]-points[0])
    if normal.length*factor*factor<=tolerancia_mm*tolerancia_mm:raise ValueError('Contorno degenerado.')
    normal.normalize()
    if max(abs((p-points[0]).dot(normal))*factor for p in points)>tolerancia_mm:raise ValueError('Contorno nao planar.')
    # All other points must stay strictly on the inner side of every edge.
    for i,p in enumerate(points):
        direction=points[(i+1)%len(points)]-p
        if any(direction.cross(q-p).dot(normal)<=0 for j,q in enumerate(points) if j not in (i,(i+1)%len(points))):raise ValueError('Exige contorno estritamente convexo e sem cruzamentos.')
    before={v:tuple(v.co) for v in bm.verts};backup=bpy.data.meshes.new('_preenchimento_rollback');bm.to_mesh(backup)
    try:
        out=(bmesh.ops.holes_fill(bm,edges=edges,sides=len(edges)) if modo=='contorno' else bmesh.ops.bridge_loops(bm,edges=edges))
        created=out.get('faces',[])
        if len(created)!=1 or set(created[0].verts)!=verts:raise ValueError('Operador nao criou a superficie delimitada esperada.')
        if any(tuple(v.co)!=co for v,co in before.items()):raise ValueError('Vertice preexistente alterado.')
        if created[0].calc_area()<=0:raise ValueError('Superficie degenerada.')
        for f in bm.faces:f.select_set(f in created)
        bm.normal_update();bmesh.update_edit_mesh(obj.data,destructive=True)
        return dict(estado='SUPERFICIE_CRIADA',objeto=objeto,modo=modo,faces_criadas=1,vertices_preservados=len(before),nao_verificado=['volume fechado','colisao','orientacao global','fabricacao'])
    except Exception:
        bm.clear();bm.from_mesh(backup);bmesh.update_edit_mesh(obj.data,destructive=True);raise
    finally:bpy.data.meshes.remove(backup)
