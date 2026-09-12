"""Operacao local com precondicao atomica e recuperacao geometrica conferida.

Executar so funcoes sincronas que editam exclusivamente a malha ativa.
Nao e transacao para materiais, animacao ou objetos arbitrarios.
"""
import bpy,bmesh
from mover_regiao import _snapshot,_contexto,_objeto
from captura_estado import capturar,conferir

POSITIVOS={'EXTRUSAO_MEDIDA','ALINHAMENTO_MEDIDO','SUPERFICIE_CRIADA','PERFIL_MEDIDO'}

def executar(funcao,parametros,captura,operacao):
    from cliente_operacao import valida_resultado
    nome=parametros['objeto']
    try:
        conferir(nome,captura)
        if not bpy.context.preferences.edit.use_global_undo:raise ValueError('Undo global desativado.')
        override=_contexto();obj=_objeto(nome)
    except Exception as exc:return dict(estado='RECUSADO',objeto=nome,motivo=str(exc),alteracao='NAO_INICIADA')
    data=obj.data;bm=bmesh.from_edit_mesh(data);backup=bm.copy()
    result={}
    class MODELAGEM_OT_operacao_local(bpy.types.Operator):
        bl_idname='mesh.modelagem_operacao_local'
        bl_label='Modelagem: operacao local'
        bl_options={'REGISTER','UNDO'}
        def execute(self,context):
            try:
                out=funcao(**parametros)
                if not isinstance(out,dict) or out.get('estado') not in POSITIVOS or out.get('objeto')!=nome or out.get('falhas') or out.get('motivos_de_reprovacao'):
                    raise ValueError('Operacao nao entregou resultado positivo coerente.')
                out['hash_geometria']=_snapshot();out['captura_depois']=capturar(nome)['captura']
                if not valida_resultado(out,operacao,parametros):raise ValueError('Medidas decisivas invalidas; operacao sera revertida.')
                result.update(out);return {'FINISHED'}
            except Exception as exc:
                result.update(estado='INDETERMINADO',objeto=nome,motivo=str(exc),alcance='Geometria e selecao; nao outros dados da cena.')
                try:
                    if capturar(nome)['captura']==captura:
                        result.update(estado='FALHA_SEM_ALTERACAO_LIQUIDA',restauracao_exata=True)
                        return {'CANCELLED'}
                    # Do not clear a mesh whose identity was replaced during the operation.
                    if bpy.context.active_object!=obj or obj.data!=data or obj.mode!='EDIT':raise RuntimeError('Alvo/modo mudou; recuperacao nao aplicada.')
                    # Transfer the saved BMesh through a temporary Mesh, preserving layers.
                    tmp=bpy.data.meshes.new('_modelagem_recuperacao')
                    try:
                        backup.to_mesh(tmp);current=bmesh.from_edit_mesh(obj.data)
                        current.clear();current.from_mesh(tmp);current.normal_update()
                        bmesh.update_edit_mesh(obj.data,destructive=True)
                    finally:bpy.data.meshes.remove(tmp)
                    exact=capturar(nome)['captura']==captura
                    result.update(estado='FALHA_RESTAURADA' if exact else 'FALHA_COM_ALTERACAO',restauracao_exata=exact)
                except Exception as recovery:
                    result.update(estado='INDETERMINADO',erro_recuperacao=str(recovery),restauracao_exata=False)
                return {'FINISHED'}
    registered=False
    try:
        bpy.utils.register_class(MODELAGEM_OT_operacao_local);registered=True
        if bpy.app.background:
            MODELAGEM_OT_operacao_local.execute(None,bpy.context)
        else:
            with bpy.context.temp_override(**override):bpy.ops.mesh.modelagem_operacao_local('EXEC_DEFAULT',True)
    except Exception as exc:
        return dict(estado='INDETERMINADO',objeto=nome,motivo=str(exc),aviso='Falha de contexto; inspecione antes de repetir.')
    finally:
        if registered:bpy.utils.unregister_class(MODELAGEM_OT_operacao_local)
        backup.free()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:area.tag_redraw()
    return result or dict(estado='INDETERMINADO',motivo='Operador nao executou; inspecione.')
