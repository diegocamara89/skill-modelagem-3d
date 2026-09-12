"""Bevel nativo em uma aresta convexa de 90 graus; perfil circular medido."""
import bpy,bmesh,math
from mover_regiao import _objeto

def executar(objeto,raio_mm,segmentos):
    obj=_objeto(objeto)
    if type(raio_mm) not in (int,float) or not math.isfinite(raio_mm) or raio_mm<=0:raise ValueError('Raio finito positivo exigido.')
    if type(segmentos) is not int or not 2<=segmentos<=64:raise ValueError('Segmentos deve ser inteiro de 2 a 64.')
    units=bpy.context.scene.unit_settings;factor=1000*units.scale_length
    mat=obj.matrix_world.to_3x3();scales=[mat.col[i].length for i in range(3)]
    if units.system!='METRIC' or not math.isfinite(factor) or factor<=0:raise ValueError('Unidades metricas exigidas.')
    if not all(math.isfinite(v) for row in mat for v in row) or min(scales)<=0 or max(scales)-min(scales)>1e-6 or mat.determinant()<=0 or any(abs(mat.col[i].normalized().dot(mat.col[j].normalized()))>1e-6 for i in range(3) for j in range(i)):
        raise ValueError('Esta receita exige escala uniforme positiva e sem cisalhamento.')
    factor*=scales[0];offset=raio_mm/factor
    bm=bmesh.from_edit_mesh(obj.data);bm.normal_update();edges=[e for e in bm.edges if e.select and not e.hide]
    if len(edges)!=1:raise ValueError('Selecione exatamente uma aresta visivel.')
    edge=edges[0]
    if not edge.is_manifold or not edge.is_convex or abs(edge.calc_face_angle()-math.pi/2)>1e-5:raise ValueError('Exige aresta manifold convexa com angulo de 90 graus.')
    if not all(math.isfinite(c) for v in bm.verts for c in v.co):raise ValueError('Coordenadas nao finitas.')
    nearby={e for v in edge.verts for e in v.link_edges}
    if raio_mm>=min(e.calc_length() for e in nearby)*factor/2-1e-5:raise ValueError('Raio grande para esta vizinhanca; reduza abaixo de metade da menor aresta incidente, com margem numerica de 0.00001 mm.')
    anchor=edge.verts[0].co.copy();axis=(edge.verts[1].co-anchor).normalized()
    center=anchor-offset*(edge.link_faces[0].normal+edge.link_faces[1].normal)
    backup=bpy.data.meshes.new('_bevel_rollback');bm.to_mesh(backup)
    try:
        out=bmesh.ops.bevel(bm,geom=[edge],offset=offset,offset_type='OFFSET',segments=segmentos,profile=.5,affect='EDGES',clamp_overlap=True)
        faces=out.get('faces',[]);verts={v for f in faces for v in f.verts}
        if len(faces)!=segmentos or len(verts)<2*(segmentos+1):raise ValueError('Contagem de perfil diverge; restaurado.')
        error=max(abs(((v.co-center)-axis*(v.co-center).dot(axis)).length-offset)*factor for v in verts)
        if not math.isfinite(error) or error>1e-5:raise ValueError('Perfil nao corresponde ao raio solicitado; restaurado.')
        if any(not e.is_manifold for e in bm.edges):raise ValueError('Resultado com bordas nao manifold; restaurado.')
        for f in bm.faces:f.select_set(f in faces)
        bm.normal_update();bmesh.update_edit_mesh(obj.data,destructive=True)
        return dict(estado='PERFIL_MEDIDO',objeto=objeto,raio_mm=raio_mm,segmentos=segmentos,erro_raio_mm=error,faces_criadas=len(faces),nao_verificado=['colisao','auto-intersecao','fabricacao'])
    except Exception:
        bm.clear();bm.from_mesh(backup);bmesh.update_edit_mesh(obj.data,destructive=True);raise
    finally:bpy.data.meshes.remove(backup)
