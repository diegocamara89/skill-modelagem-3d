"""Contexto e Undo nativos reutilizados por operacoes locais registradas.

Registra no Undo nativo. Nao oferece undo remoto global.
"""
import bpy
from mover_regiao import _snapshot,_contexto

def executar(funcao,parametros):
    if not bpy.context.preferences.edit.use_global_undo:
        raise ValueError('Undo global desativado; habilite antes da operacao.')
    result={}
    class MODELAGEM_OT_operacao_local(bpy.types.Operator):
        bl_idname='mesh.modelagem_operacao_local'
        bl_label='Modelagem: operacao local'
        bl_options={'REGISTER','UNDO'}
        def execute(self,context):
            try:result.update(funcao(**parametros));return {'FINISHED'}
            except Exception as exc:result.update(estado='RECUSADO',motivo=str(exc));return {'CANCELLED'}
    bpy.utils.register_class(MODELAGEM_OT_operacao_local)
    try:
        with bpy.context.temp_override(**_contexto()):bpy.ops.mesh.modelagem_operacao_local('EXEC_DEFAULT',True)
    finally:bpy.utils.unregister_class(MODELAGEM_OT_operacao_local)
    if result.get('estado')!='RECUSADO':
        result['hash_geometria']=_snapshot()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:area.tag_redraw()
    return result
