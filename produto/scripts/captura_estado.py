"""Token de precondicao da sessao, geometria e selecao. Roda dentro do Blender."""
import bpy,bmesh,hashlib,json,os
from mover_regiao import _objeto,_snapshot

def capturar(objeto):
    obj=_objeto(objeto);bm=bmesh.from_edit_mesh(obj.data)
    payload=[os.getpid(),obj.as_pointer(),obj.data.as_pointer(),objeto,obj.mode,_snapshot(),
        list(bpy.context.tool_settings.mesh_select_mode),
        [(v.select,v.hide) for v in bm.verts],[(e.select,e.hide) for e in bm.edges],
        [(f.select,f.hide) for f in bm.faces]]
    token=hashlib.sha256(json.dumps(payload,allow_nan=False).encode()).hexdigest()
    return dict(estado='CAPTURA_DISPONIVEL',objeto=objeto,captura=token,pid=os.getpid(),
        faces_selecionadas=sum(f.select and not f.hide for f in bm.faces),
        arestas_selecionadas=sum(e.select and not e.hide for e in bm.edges),
        alcance='Geometria de cena, transformacoes, unidades e selecao; nao materiais/animacao.')

def conferir(objeto,esperada):
    actual=capturar(objeto)
    if not isinstance(esperada,str) or actual['captura']!=esperada:
        raise ValueError('CAPTURA_DESATUALIZADA: recapture e confirme o alvo antes de editar.')
    return actual
