"""Dentro do Blender: diagnostico e deslocamento com transicao EXPLICITA.

Nao escolhe feicoes, pesos, tolerancias ou criterio estetico pelo usuario.
Coordenadas, areas e tolerancias usam unidades de MUNDO da cena, nao mm implicitos.
"""
import hashlib
import json
import math

import bpy
import bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

VERSAO = "1.0.0"


def _objeto(nome, modo_objeto=False):
    obj = bpy.data.objects.get(nome)
    if obj is None or obj.type != "MESH":
        raise ValueError("OBJETO_INVALIDO: informe o nome exato de uma malha")
    if modo_objeto and obj.mode != "OBJECT":
        raise ValueError("MODO_INVALIDO: sincronize saindo de Edit Mode antes desta operacao")
    return obj


def diagnostica():
    """Somente consulta. Nao muda modo, selecao, objeto ativo nem visibilidade."""
    ativo = bpy.context.view_layer.objects.active
    em_edicao, suspeitas = [], []
    for obj in bpy.context.view_layer.objects:
        if obj.type != "MESH":
            continue
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            bm.faces.ensure_lookup_table()
            em_edicao.append({"objeto": obj.name,
                              "faces": [i for i, f in enumerate(bm.faces) if f.select],
                              "vertices": [i for i, v in enumerate(bm.verts) if v.select],
                              "fonte": "bmesh", "visivel": obj.visible_get()})
        else:
            n = sum(p.select for p in obj.data.polygons)
            if n:
                suspeitas.append({"objeto": obj.name, "flags_de_face": n,
                                  "visivel": obj.visible_get(),
                                  "uso": "NAO usar como selecao viva"})
    unidades = bpy.context.scene.unit_settings
    mm = unidades.scale_length * 1000 if unidades.system != "NONE" else None
    if len(em_edicao) > 1:
        estado, passo = "MULTIPLOS_OBJETOS_EM_EDICAO", "Escolha o objeto pelo pedido; nao use a maior contagem."
    elif not em_edicao:
        estado, passo = "SEM_SELECAO_VIVA", "Identifique a malha ativa; se necessario, oriente o usuario a entrar em Edit Mode."
    elif not em_edicao[0]["vertices"]:
        estado, passo = "SELECAO_VAZIA", "Oriente a marcacao; nao altere a geometria."
    else:
        estado, passo = "INDICACAO_DISPONIVEL", "Interprete a feicao e delimite alvo, transicao e regiao protegida antes de editar."
    return {"estado": estado, "proximo_passo": passo, "versao": VERSAO,
            "blender": bpy.app.version_string, "modo": bpy.context.mode,
            "objeto_ativo": ativo.name if ativo else None, "em_edicao": em_edicao,
            "flags_fora_de_edicao": suspeitas, "unidade": {"sistema": unidades.system,
            "escala_metros": unidades.scale_length, "mm_por_unidade": mm},
            "arquivo_salvo": bool(bpy.data.filepath), "alteracoes_nao_salvas": bpy.data.is_dirty,
            "limite": "Selecao e indicacao de feicao, nao especificacao dos vertices a mover. Sem unidade definida, confirme a escala."}


def entra_em_edicao(nome):
    """Altera somente contexto/seleção de objetos; nao geometria. Alvo explicito."""
    obj = _objeto(nome)
    if obj.name not in bpy.context.view_layer.objects or not obj.visible_get() or obj.hide_select:
        raise ValueError("ALVO_INACESSIVEL: escolha malha visivel e selecionavel na view layer atual")
    outros = [o for o in bpy.context.view_layer.objects if o.mode != "OBJECT"]
    if outros:
        if len(outros) == 1 and outros[0] == obj and obj.mode == "EDIT":
            return diagnostica()
        raise ValueError("CONTEXTO_OCUPADO: outro objeto ou modo esta ativo; preserve a marcacao antes de mudar")
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(object=obj, active_object=obj,
                                   selected_objects=[obj], selected_editable_objects=[obj]):
        if not bpy.ops.object.mode_set.poll():
            raise ValueError("CONTEXTO_INCOMPATIVEL: mode_set nao disponivel; oriente Tab no viewport, sem repetir a operacao")
        retorno = bpy.ops.object.mode_set(mode="EDIT")
    if "FINISHED" not in retorno or obj.mode != "EDIT":
        raise RuntimeError("MODO_NAO_ALTERADO: inspecione o contexto antes de tentar novamente")
    return diagnostica()


def captura(nome):
    """Snapshot de vertices e conectividade; inclui a escala usada na comparacao."""
    obj = _objeto(nome)
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        ids = {v: i for i, v in enumerate(bm.verts)}
        vertices = [list(obj.matrix_world @ v.co) for v in bm.verts]
        faces = [[ids[v] for v in f.verts] for f in bm.faces]
    else:
        vertices = [list(obj.matrix_world @ v.co) for v in obj.data.vertices]
        faces = [list(p.vertices) for p in obj.data.polygons]
    escala = bpy.context.scene.unit_settings
    corpo = {"vertices": vertices, "faces": faces,
             "unidade": [escala.system, escala.scale_length]}
    digest = hashlib.sha256(json.dumps(corpo, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return dict(corpo, sha256=digest, objeto=nome,
                materiais=[m.name if m else None for m in obj.data.materials],
                limite="Geometria base em mundo e unidades; nao inclui efeito de modificadores, material ou camera no hash.")


def copia_para_previa(nome, novo_nome):
    obj = _objeto(nome, True)
    if not novo_nome or novo_nome in bpy.data.objects:
        raise ValueError("NOME_OCUPADO: use nome novo para a previa")
    copia = obj.copy()
    copia.data = obj.data.copy()
    copia.name = novo_nome
    (obj.users_collection[0] if obj.users_collection else bpy.context.collection).objects.link(copia)
    return {"objeto": copia.name, "materiais": [m.name if m else None for m in copia.data.materials],
            "limite": "Copia de objeto e malha; materiais permanecem compartilhados. Nao editar o material compartilhado para mudar so a previa."}


def _finito(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _plano(antes, plano):
    """Valida ANTES de qualquer escrita; nenhum crescimento por vizinhanca."""
    if plano.get("assinatura_antes") != antes["sha256"]:
        raise ValueError("ESTADO_MUDOU: recapture e reavalie os indices")
    n = len(antes["vertices"])
    alvo = plano.get("alvo", [])
    trans = plano.get("transicao", [])
    vetor = plano.get("vetor", [])
    if not alvo or len(vetor) != 3 or not all(_finito(v) for v in vetor):
        raise ValueError("PLANO_INVALIDO: alvo nao vazio e vetor de tres numeros finitos obrigatorios")
    if not any(vetor):
        raise ValueError("PLANO_INVALIDO: vetor nulo nao constitui edicao")
    ids = list(alvo) + [p[0] for p in trans]
    if any(type(i) is not int or not 0 <= i < n for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("INDICES_INVALIDOS: indices unicos, validos e conjuntos disjuntos obrigatorios")
    pesos = {i: 1.0 for i in alvo}
    for i, peso in trans:
        if not _finito(peso) or not 0 < peso < 1:
            raise ValueError("PESO_INVALIDO: transicao exige 0 < peso < 1; sem propagacao automatica")
        pesos[i] = peso
    return pesos, Vector(vetor)


def desloca_com_pesos(nome, plano):
    """Previa: pesos fornecidos pelo plano, nunca inventados a partir da selecao."""
    obj = _objeto(nome, True)
    if obj.modifiers or obj.data.shape_keys or obj.data.users > 1:
        raise ValueError("MALHA_NAO_INDEPENDENTE: use copia independente, sem modificadores nem shape keys")
    antes = captura(nome)
    pesos, vetor = _plano(antes, plano)
    if abs(obj.matrix_world.determinant()) < 1e-12:
        raise ValueError("MATRIZ_SINGULAR: nao e possivel converter o deslocamento de mundo")
    delta = obj.matrix_world.inverted().to_3x3() @ vetor
    original = {i: obj.data.vertices[i].co.copy() for i in pesos}
    try:
        for i, peso in pesos.items():
            obj.data.vertices[i].co = original[i] + delta * peso
        obj.data.update()
        depois = captura(nome)
    except Exception:
        for i, co in original.items():
            obj.data.vertices[i].co = co
        obj.data.update()
        raise
    return {"estado": "PREVIA_NAO_VALIDADA", "antes": antes, "depois": depois,
            "proximo_passo": "Verifique alvo, transicao, protegido e secoes independentes; nao entregue pela contagem de vertices."}


def mede_regiao(snapshot, indices_faces):
    """Area, qualidade e angulo nao sao aprovacao estetica. Unidades da cena."""
    ids = list(indices_faces)
    if not ids or len(set(ids)) != len(ids) or any(type(i) is not int or not 0 <= i < len(snapshot["faces"]) for i in ids):
        raise ValueError("REGIAO_INVALIDA: informe faces existentes, unicas, nao vazias")
    vertices = [Vector(v) for v in snapshot["vertices"]]
    areas, qualidades, normais, arestas = [], [], {}, {}
    for fi in ids:
        face = snapshot["faces"][fi]
        pts = [vertices[i] for i in face]
        tris = tessellate_polygon([pts])
        soma = Vector((0, 0, 0))
        area = 0.0
        for a, b, c in tris:
            # Blender 5.2 retorna indices; versoes anteriores retornam vetores.
            if isinstance(a, int):
                a, b, c = pts[a], pts[b], pts[c]
            cruz = (b-a).cross(c-a)
            at = cruz.length / 2
            per = (b-a).length + (c-b).length + (a-c).length
            qualidades.append(at / per**2 if per else 0.0)
            soma += cruz
            area += at
        areas.append(area)
        normais[fi] = soma.normalized() if soma.length else Vector((0, 0, 0))
        for a, b in zip(face, face[1:] + face[:1]):
            arestas.setdefault(tuple(sorted((a, b))), []).append(fi)
    angulos = []
    for fs in arestas.values():
        if len(fs) == 2 and all(normais[f].length for f in fs):
            angulos.append(math.degrees(normais[fs[0]].angle(normais[fs[1]])))
    angulos.sort()
    def percentil(p):
        if not angulos:
            return None
        x = (len(angulos)-1)*p
        lo, hi = math.floor(x), math.ceil(x)
        return angulos[lo] + (angulos[hi]-angulos[lo])*(x-lo)
    return {"n_faces": len(ids), "area_total": sum(areas), "area_min": min(areas),
            "qualidade_min": min(qualidades) if qualidades else 0.0,
            "angulo_max_graus": max(angulos) if angulos else None,
            "angulo_p50_graus": percentil(.5), "angulo_p90_graus": percentil(.9),
            "n_pares": len(angulos), "arestas_com_mais_de_duas_faces": sum(len(v)>2 for v in arestas.values()),
            "limite": "Faces indicadas; angulos so entre pares internos, bordas externas nao avaliadas. Qualidade area/perimetro^2 por triangulo; equilatero = sqrt(3)/36. Areas em unidades de mundo ao quadrado. Nao e prova de ausencia de auto-intersecao."}


def verifica_deslocamento(antes, depois, plano, tolerancia, limites_transicao=None):
    pesos, vetor = _plano(antes, plano)
    if not _finito(tolerancia) or tolerancia <= 0:
        raise ValueError("TOLERANCIA_INVALIDA: informe numero finito positivo nas unidades da cena")
    if antes["faces"] != depois["faces"] or len(antes["vertices"]) != len(depois["vertices"]) or antes["unidade"] != depois["unidade"]:
        return {"estado": "INDETERMINADA", "motivo": "CORRESPONDENCIA_PERDIDA: conectividade, vertices ou unidade mudou; nao compare por indice"}
    if any(len(v) != 3 or not all(_finito(x) for x in v) for s in (antes,depois) for v in s["vertices"]):
        return {"estado": "INDETERMINADA", "motivo": "MEDICAO_INVALIDA: coordenada nao finita ou incompleta"}
    alvo = set(plano["alvo"])
    movidos = set(pesos)
    # Toda face incidente a pesos DIFERENTES e transicao, mesmo sem vertice de peso intermediario.
    fronteira = [i for i, f in enumerate(antes["faces"]) if len({pesos.get(v, 0) for v in f}) > 1]
    # Inclui uma camada de vizinhos por ARESTA para medir tambem a dobra no
    # encontro da transicao com alvo/protegido, nao apenas dentro da faixa.
    edges = lambda f: {tuple(sorted((a,b))) for a,b in zip(f,f[1:]+f[:1])}
    bordas = set().union(*(edges(antes["faces"][i]) for i in fronteira))
    zona = [i for i,f in enumerate(antes["faces"]) if edges(f) & bordas]
    erros_alvo, erros_protegido, erros_pesos = [], [], []
    for i, (a,b) in enumerate(zip(antes["vertices"], depois["vertices"])):
        delta = Vector(b)-Vector(a)
        erro = (delta-vetor*pesos.get(i,0)).length
        erros_pesos.append(erro)
        if i in alvo:
            erros_alvo.append(erro)
        if i not in movidos:
            erros_protegido.append(delta.length)
    falhas = []
    if max(erros_pesos, default=0) > tolerancia:
        falhas.append("DESLOCAMENTO_DIVERGE_DO_PLANO")
    if max(erros_protegido, default=0) > tolerancia:
        falhas.append("REGIAO_PROTEGIDA_MUDOU")
    out = {"erro_max_alvo": max(erros_alvo), "erro_max_protegido": max(erros_protegido, default=0),
           "erro_max_pesos": max(erros_pesos), "n_vertices_protegidos": len(erros_protegido),
           "faces_de_transicao": fronteira, "faces_da_zona_medida": zona, "falhas": falhas, "tolerancia": tolerancia,
           "limite": "Correspondencia por indice, geometria base. Nao prova silhueta, auto-intersecao, resistencia nem qualidade visual; completar com secoes e comparacao visual controlada."}
    if not fronteira:
        return dict(out, estado="REPROVADA" if falhas else "INDETERMINADA", motivo="SEM_TRANSICAO: este verificador e de edicao localizada")
    out["transicao_antes"] = mede_regiao(antes, zona)
    out["transicao_depois"] = mede_regiao(depois, zona)
    obrigatorios = {"area_min", "area_max", "angulo_max_graus", "qualidade_min"}
    if limites_transicao is None:
        return dict(out, estado="REPROVADA" if falhas else "INDETERMINADA", motivo="FALTAM_LIMITES_DA_TRANSICAO: medidas nao sao aprovacao")
    if set(limites_transicao) != obrigatorios or not all(_finito(v) for v in limites_transicao.values()):
        raise ValueError("LIMITES_INVALIDOS: area_min, area_max, angulo_max_graus e qualidade_min finitos obrigatorios")
    l = limites_transicao
    if not (0 <= l["area_min"] <= l["area_max"] and 0 <= l["angulo_max_graus"] <= 180 and 0 <= l["qualidade_min"] <= math.sqrt(3)/36):
        raise ValueError("LIMITES_INVALIDOS: confira ordem, sinal e dominio dos limites")
    m = out["transicao_depois"]
    if not l["area_min"] <= m["area_total"] <= l["area_max"]:
        falhas.append("AREA_DA_TRANSICAO_FORA")
    if m["angulo_max_graus"] is None:
        return dict(out, estado="REPROVADA" if falhas else "INDETERMINADA", motivo="SEM_PARES_DE_FACES: angulo nao medido")
    if m["angulo_max_graus"] > l["angulo_max_graus"]:
        falhas.append("DOBRA_DA_TRANSICAO_FORA")
    if m["qualidade_min"] < l["qualidade_min"]:
        falhas.append("QUALIDADE_DA_TRANSICAO_FORA")
    if m["arestas_com_mais_de_duas_faces"]:
        falhas.append("TOPOLOGIA_DA_TRANSICAO_FORA")
    return dict(out, estado="REPROVADA" if falhas else "MEDIDAS_CONFORMES", limites_transicao=l)
