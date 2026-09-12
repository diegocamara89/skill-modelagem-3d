"""Operacao Blender reutilizavel: translacao GLOBAL da uniao das faces selecionadas.

Nao reconstrui conexoes: faces adjacentes acompanham seus vertices compartilhados.
Nao certifica colisao, espessura, qualidade visual ou adequacao para fabricacao.
"""
import math
import hashlib
import json
import bpy
import bmesh
from mathutils import Vector

VERSAO = "1.0.1"
_HISTORICO = []
_CURSOR = 0


def _snapshot():
    """Identidade geometrica da sessao; nao mede materiais/animacao/edicoes de outra natureza."""
    records = []
    for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        record = [obj.name, obj.type, [list(row) for row in obj.matrix_world]]
        if obj.type == 'MESH':
            if obj.mode == 'EDIT': obj.update_from_editmode()
            record.extend([[list(v.co) for v in obj.data.vertices],
                           [list(p.vertices) for p in obj.data.polygons],
                           [list(e.vertices) for e in obj.data.edges]])
        records.append(record)
    units = bpy.context.scene.unit_settings
    raw = json.dumps([bpy.data.filepath, units.system, units.scale_length, records], allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _contexto():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region:
                    return dict(window=window, area=area, region=region)
    raise ValueError('Abra uma area VIEW_3D nesta sessao; nenhum contexto foi encontrado.')


def _objeto(nome):
    obj = bpy.context.active_object
    if not obj or obj.name != nome or obj.type != 'MESH':
        raise ValueError('O objeto ativo deve ser a malha nomeada em --objeto.')
    if obj.mode != 'EDIT' or len(bpy.context.objects_in_mode) != 1:
        raise ValueError('Entre em Edit Mode somente no objeto alvo.')
    if obj.modifiers or obj.data.shape_keys or obj.data.users != 1:
        raise ValueError('Esta operacao exige malha exclusiva, sem modificadores nem shape keys.')
    return obj


def _mover(nome, distancia, eixo):
    obj = _objeto(nome)
    if eixo not in ('X', 'Y', 'Z') or not math.isfinite(distancia) or distancia == 0:
        raise ValueError('Informe eixo GLOBAL X/Y/Z e distancia finita diferente de zero em mm.')
    units = bpy.context.scene.unit_settings
    if units.system != 'METRIC' or not math.isfinite(units.scale_length) or units.scale_length <= 0:
        raise ValueError('Configure unidades METRIC com scale_length finito e positivo antes de mover.')
    matrix = obj.matrix_world.copy()
    if not all(math.isfinite(v) for row in matrix for v in row):
        raise ValueError('Transformacao do objeto nao finita.')
    inverse = matrix.to_3x3().inverted()  # singularidade e erro antes de escrever
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    bm.verts.index_update(); bm.faces.index_update()
    faces = [f for f in bm.faces if f.select and not f.hide]
    selected = {v.index for f in faces for v in f.verts}
    if not faces or not selected:
        raise ValueError('Selecione pelo menos uma face visivel; vertices isolados nao sao o alvo.')
    before = [v.co.copy() for v in bm.verts]
    if not all(math.isfinite(c) for co in before for c in co):
        raise ValueError('A malha contem coordenadas nao finitas.')
    global_delta = Vector((0, 0, 0))
    global_delta['XYZ'.index(eixo)] = distancia / (1000.0 * units.scale_length)
    local_delta = inverse @ global_delta
    selected_faces = {f.index for f in faces}
    adjacent = [f.index for f in bm.faces if f.index not in selected_faces
                and any(v.index in selected for v in f.verts)]
    try:
        for index in selected:
            bm.verts[index].co = before[index] + local_delta
        if not all(math.isfinite(c) for v in bm.verts for c in v.co):
            raise ValueError('Resultado nao finito; coordenadas restauradas.')
        factor = 1000 * units.scale_length
        target_error = max(((matrix.to_3x3() @ (bm.verts[i].co-before[i])-global_delta).length * factor
                            for i in selected), default=0)
        protected_error = max(((matrix.to_3x3() @ (v.co-before[v.index])).length * factor
                               for v in bm.verts if v.index not in selected), default=0)
        tolerance = max(1e-5, abs(distancia) * 1e-5)
        if target_error > tolerance or protected_error > tolerance:
            raise ValueError('Precisao insuficiente para este tamanho/coordenadas; coordenadas restauradas.')
        bm.normal_update()
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=False)
    except Exception:
        for v, co in zip(bm.verts, before):
            v.co = co
        bm.normal_update(); bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=False)
        raise
    return dict(estado='DESLOCAMENTO_VERIFICADO', objeto=nome, distancia_mm=distancia,
                eixo_global=eixo, vertices_movidos=len(selected), faces_selecionadas=len(faces),
                faces_adjacentes_alteradas=adjacent, erro_alvo_mm=target_error,
                erro_vertices_protegidos_mm=protected_error, tolerancia_mm=tolerance,
                papel_tolerancia='Erro numerico computacional, nao folga de fabricacao',
                nao_verificado=['colisao', 'espessura', 'qualidade das faces adjacentes',
                                'intencao da selecao', 'adequacao para fabricacao'])


def executar(acao, objeto, distancia_mm=None, eixo='Z'):
    """Uma chamada visivel, com operador UNDO temporario e historico proprio.

    Historico proprio restaura coordenadas do alvo por nova operacao UNDO.
    Nao chama undo global: assim nao desfaz trabalho externo nao identificado.
    """
    global _CURSOR
    result = {'versao': VERSAO, 'acao': acao, 'objeto': objeto}
    current = None
    try:
        _objeto(objeto)
        override = _contexto()
        if acao != 'inspecionar' and not bpy.context.preferences.edit.use_global_undo:
            raise ValueError('Undo global esta desativado; habilite-o antes. Nenhuma preferencia foi alterada.')
        if acao == 'inspecionar':
            obj = _objeto(objeto)
            bm = bmesh.from_edit_mesh(obj.data)
            result.update(estado='INSPECIONADO', hash_geometria=_snapshot(),
                          faces_selecionadas=sum(f.select and not f.hide for f in bm.faces),
                          historico_posicao=_CURSOR, historico_total=len(_HISTORICO))
        elif acao in ('mover', 'desfazer', 'refazer'):
            current = _snapshot()
            obj = _objeto(objeto)
            bm = bmesh.from_edit_mesh(obj.data)
            before_coords = [tuple(v.co) for v in bm.verts]
            entry = None
            if acao != 'mover':
                index = _CURSOR-1 if acao == 'desfazer' else _CURSOR
                if index < 0 or index >= len(_HISTORICO):
                    raise ValueError('Nenhuma operacao desta ferramenta disponivel para esta acao.')
                entry = _HISTORICO[index]
                expected = entry['depois_hash'] if acao == 'desfazer' else entry['antes_hash']
                if entry['objeto'] != objeto or current != expected:
                    raise ValueError('Geometria mudou fora desta sequencia. Historico recusado sem alterar a cena.')
            class MODELAGEM_OT_mover_regiao_temporario(bpy.types.Operator):
                bl_idname = 'mesh.modelagem_mover_regiao_temporario'
                bl_label = 'Modelagem: mover regiao em milimetros'
                bl_options = {'REGISTER', 'UNDO'}

                def execute(self, context):
                    try:
                        if acao == 'mover':
                            result.update(_mover(objeto, float(distancia_mm), eixo))
                        else:
                            coordinates = entry['antes_coords'] if acao == 'desfazer' else entry['depois_coords']
                            edit = bmesh.from_edit_mesh(_objeto(objeto).data)
                            for v, co in zip(edit.verts, coordinates): v.co = co
                            edit.normal_update()
                            bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=False)
                            result.update(estado='HISTORICO_EXECUTADO',
                                          mecanismo='Restauracao do historico proprio como nova operacao UNDO')
                        return {'FINISHED'}
                    except Exception as exc:
                        result.update(estado='RECUSADO', motivo=str(exc))
                        return {'CANCELLED'}
            cls = MODELAGEM_OT_mover_regiao_temporario
            bpy.utils.register_class(cls)
            try:
                if bpy.app.background:
                    cls.execute(None,bpy.context)
                else:
                    with bpy.context.temp_override(**override):
                        bpy.ops.mesh.modelagem_mover_regiao_temporario('EXEC_DEFAULT', True)
            finally:
                bpy.utils.unregister_class(cls)
            if result.get('estado') in ('DESLOCAMENTO_VERIFICADO', 'HISTORICO_EXECUTADO'):
                after_hash = _snapshot()
                if acao == 'mover':
                    del _HISTORICO[_CURSOR:]
                    edit = bmesh.from_edit_mesh(obj.data)
                    _HISTORICO.append(dict(objeto=objeto, antes_hash=current, depois_hash=after_hash,
                                           antes_coords=before_coords, depois_coords=[tuple(v.co) for v in edit.verts]))
                    _CURSOR += 1
                else:
                    expected_after = entry['antes_hash'] if acao == 'desfazer' else entry['depois_hash']
                    result['restauracao_exata'] = after_hash == expected_after
                    if not result['restauracao_exata']:
                        result['estado'] = 'ERRO_VERIFICACAO'
                    else:
                        _CURSOR += -1 if acao == 'desfazer' else 1
                result['hash_geometria'] = after_hash
        else:
            raise ValueError('Acao deve ser mover, desfazer, refazer ou inspecionar.')
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
    except Exception as exc:
        result.update(estado='RECUSADO', motivo=str(exc))
    if result.get('estado')=='RECUSADO' and current is not None:
        try:
            exact=_snapshot()==current
            result.update(estado='FALHA_SEM_ALTERACAO_LIQUIDA' if exact else 'FALHA_COM_ALTERACAO',restauracao_exata=exact,alcance='Geometria; nao outros dados da cena')
        except Exception:
            result.update(estado='INDETERMINADO',restauracao_exata=False)
    return result
