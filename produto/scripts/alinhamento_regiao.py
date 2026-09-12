"""Projecao ortogonal das faces selecionadas em plano GLOBAL declarado em mm."""
import math,bpy,bmesh
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane
from mover_regiao import _objeto

def executar(objeto,ponto_mm,normal,maximo_mm):
    obj=_objeto(objeto)
    if any(not isinstance(a,(list,tuple)) or len(a)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in a) for a in (ponto_mm,normal)):
        raise ValueError('Ponto e normal exigem tres numeros finitos.')
    if type(maximo_mm) not in (int,float) or not math.isfinite(maximo_mm) or maximo_mm<=0:
        raise ValueError('Declare deslocamento maximo finito e positivo em mm.')
    n=Vector(normal)
    if n.length<1e-12:raise ValueError('Normal nula; declare a direcao do plano.')
    n.normalize();units=bpy.context.scene.unit_settings;factor=units.scale_length*1000
    if units.system!='METRIC' or not math.isfinite(factor) or factor<=0:raise ValueError('Unidades metricas com escala positiva exigidas.')
    mat=obj.matrix_world.copy()
    if not all(math.isfinite(x) for row in mat for x in row):raise ValueError('Transformacao nao finita.')
    inv=mat.inverted();point=Vector(ponto_mm)/factor
    bm=bmesh.from_edit_mesh(obj.data);verts={v for f in bm.faces if f.select and not f.hide for v in f.verts}
    if not verts:raise ValueError('Selecione faces visiveis para alinhar.')
    if not all(math.isfinite(x) for v in bm.verts for x in v.co):raise ValueError('Coordenadas nao finitas.')
    old={v:v.co.copy() for v in bm.verts};targets={}
    for v in verts:
        world=mat@v.co;d=distance_point_to_plane(world,point,n)
        if abs(d)*factor>maximo_mm:raise ValueError('Deslocamento excede limite declarado; nenhuma alteracao.')
        targets[v]=inv@(world-n*d)
    try:
        for v,co in targets.items():v.co=co
        residual=max(abs(distance_point_to_plane(mat@v.co,point,n))*factor for v in verts)
        protected=max(((mat.to_3x3()@(v.co-co)).length*factor for v,co in old.items() if v not in verts),default=0)
        if not math.isfinite(residual) or residual>1e-5 or protected>1e-5:raise ValueError('Precisao insuficiente; restaurado.')
        bm.normal_update();bmesh.update_edit_mesh(obj.data,destructive=False)
        return dict(estado='ALINHAMENTO_MEDIDO',objeto=objeto,residuo_mm=residual,erro_protegidos_mm=protected,vertices=len(verts),nao_verificado=['colisao','forma das faces adjacentes','fabricacao'])
    except Exception:
        for v,co in old.items():v.co=co
        bm.normal_update();bmesh.update_edit_mesh(obj.data,destructive=False)
        raise
