# -*- coding: utf-8 -*-
"""bl_ferramentas.py - auxiliares para edicao guiada no Blender.

RODA DENTRO DO BLENDER. Duas formas:
  headless:  blender --background --factory-startup --python <este arquivo> -- <tarefa.json>
  na cena:   cole o conteudo no execute_code do MCP e chame as funcoes

POR QUE ESTE ARQUIVO EXISTE. As etapas mecanicas desta receita erram em silencio, e
foi medido:

1. `calc_center_median()` devolve coordenada LOCAL. Um cubo de aresta 20 em z=10
   ocupa 0 a 20 no mundo e -10 a +10 no local. O criterio "face acima de z=15"
   seleciona 1 face em mundo e ZERO em local. MEDIDO em 07/09/2026.
2. Operar com selecao VAZIA nao levanta excecao. `transform.translate` devolve
   {'CANCELLED'} e a geometria fica intacta. Quem ignora o retorno conclui que
   editou. MEDIDO.
3. Em modo background o sistema de undo nasce DESLIGADO: `ed.undo` nem passa no
   poll sem um `ed.undo_push()` antes. MEDIDO.
4. Malha fechada nao prova ausencia de ranhura, e uniao booleana produz face de
   area nula sem abrir borda. Sao medidas SEPARADAS.

Toda funcao aqui devolve FATO MEDIDO, nunca "sucesso". Quando a pre-condicao
falha, ela levanta ErroDePrecondicao em vez de operar em cima de nada.
"""
import hashlib
import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

# VERSAO muda SEMPRE que o comportamento muda, e nao so quando a interface muda.
# Isto foi exigido por um ensaio: o pacote foi alterado no meio de uma execucao, o
# comportamento de preenche_entre_limites mudou de perfil de 4 pontos para 6, e a
# VERSAO ficou parada em 1.0.0. O agente leu uma referencia e executou outro codigo,
# e perdeu uma execucao inteira sem ter como detectar a troca.
VERSAO = "1.5.0"
CASAS = 6                 # arredondamento da assinatura, em unidades de cena


def confere_versao(esperada):
    """Chame no inicio de um script que depende do comportamento documentado.

    Recusar cedo e melhor que descobrir pelo resultado: sem isto, a unica pista de
    que a referencia nao descreve mais o codigo e o resultado sair diferente."""
    if esperada != VERSAO:
        raise ErroDePrecondicao(
            "este script foi escrito para bl_ferramentas %s e o modulo carregado e "
            "%s. Releia a referencia da sua versao antes de executar: o comportamento "
            "pode ter mudado." % (esperada, VERSAO))
    return {"versao": VERSAO, "confere": True}


class ErroDePrecondicao(Exception):
    """A cena nao esta no estado que a operacao exige. Levantar e melhor que
    operar: operacao sobre pre-condicao falsa produz resultado sem significado."""


# ---------------------------------------------------------------------------
# diagnostico
# ---------------------------------------------------------------------------

def diagnostico(nome_do_objeto=None):
    """Lê o estado REAL antes de orientar ou editar.

    Em Edit Mode a malha de Object Mode pode estar desatualizada, por isso a
    selecao e lida por bmesh.from_edit_mesh e nao por obj.data."""
    d = {"versao_blender": bpy.app.version_string, "versao_ferramentas": VERSAO,
         "modo": bpy.context.mode, "em_background": bpy.app.background}

    cena = bpy.context.scene
    d["escala_de_unidade"] = round(float(cena.unit_settings.scale_length), 9)
    d["sistema_de_unidade"] = cena.unit_settings.system
    d["objetos_na_cena"] = [o.name for o in bpy.data.objects]

    obj = bpy.data.objects.get(nome_do_objeto) if nome_do_objeto else bpy.context.active_object
    if obj is None:
        d["objeto"] = None
        d["aviso"] = "nenhum objeto ativo nem nome informado"
        return d
    if obj.type != "MESH":
        d["objeto"] = {"nome": obj.name, "tipo": obj.type}
        d["aviso"] = "o objeto nao e malha; as operacoes desta receita nao se aplicam"
        return d

    m = obj.matrix_world
    d["objeto"] = {
        "nome": obj.name, "tipo": obj.type,
        "location": [round(v, 6) for v in obj.location],
        "scale": [round(v, 6) for v in obj.scale],
        "rotation_euler": [round(v, 6) for v in obj.rotation_euler],
        "dimensions_mundo": [round(v, 6) for v in obj.dimensions],
        "matriz_mundo_e_identidade": all(
            abs(m[i][j] - (1.0 if i == j else 0.0)) < 1e-9 for i in range(4) for j in range(4)),
        "modificadores": [{"nome": mo.name, "tipo": mo.type, "visivel": mo.show_viewport}
                          for mo in obj.modifiers],
        "vertices": len(obj.data.vertices), "faces": len(obj.data.polygons),
    }
    caixa_local = [Vector(c) for c in obj.bound_box]
    caixa_mundo = [m @ c for c in caixa_local]
    d["objeto"]["caixa_mundo_min"] = [round(min(c[i] for c in caixa_mundo), 6) for i in range(3)]
    d["objeto"]["caixa_mundo_max"] = [round(max(c[i] for c in caixa_mundo), 6) for i in range(3)]

    if bpy.context.mode == "EDIT_MESH" and obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        d["selecao_viva"] = {
            "fonte": "bmesh.from_edit_mesh, que e a selecao REAL em Edit Mode",
            "faces_selecionadas": sum(1 for f in bm.faces if f.select),
            "arestas_selecionadas": sum(1 for e in bm.edges if e.select),
            "vertices_selecionados": sum(1 for v in bm.verts if v.select),
            "modo_de_selecao": [n for n, ativo in
                                zip(("vertice", "aresta", "face"),
                                    bpy.context.tool_settings.mesh_select_mode) if ativo]}
    else:
        d["selecao_viva"] = {
            "fonte": "objeto fora de Edit Mode",
            "faces_selecionadas_em_object_mode": sum(1 for p in obj.data.polygons if p.select),
            "nota": ("contagem de Object Mode pode estar desatualizada. Entrar em Edit "
                     "Mode e reler antes de decidir.")}

    # sobreposicoes: so existem com interface. Ausencia NAO e "desligadas".
    d["sobreposicoes"] = estado_das_sobreposicoes()
    return d


def estado_das_sobreposicoes():
    """Selecao existente com destaque invisivel e sobreposicao desligada, nao clique
    falho. Sem interface a informacao NAO existe, e dizer 'desligadas' seria inventar."""
    if bpy.app.background:
        return {"disponivel": False,
                "motivo": "modo background nao tem interface; o estado nao existe"}
    for janela in bpy.context.window_manager.windows:
        for area in janela.screen.areas:
            if area.type == "VIEW_3D":
                for espaco in area.spaces:
                    if espaco.type == "VIEW_3D":
                        return {"disponivel": True,
                                "show_overlays": bool(espaco.overlay.show_overlays),
                                "shading_type": espaco.shading.type,
                                "show_xray": bool(espaco.shading.show_xray),
                                "atalho_medido_5_2_1": ("Shift+Alt+Z alterna sobreposicoes; "
                                                        "confirmar em mapa personalizado")}
    return {"disponivel": False, "motivo": "nenhuma area VIEW_3D encontrada"}


# ---------------------------------------------------------------------------
# identidade
# ---------------------------------------------------------------------------

def assinatura(nome_do_objeto, espaco="mundo", casas=CASAS, apenas_indices=None):
    """Assinatura de coordenadas E conectividade, com cobertura declarada.

    Hash de .blend prova integridade do arquivo e nao separa mudanca de geometria
    de mudanca de camera. Esta assinatura cobre so o que ela diz cobrir."""
    obj = _malha(nome_do_objeto)
    m = obj.matrix_world if espaco == "mundo" else None

    # CORRIGIDO depois de medir: a versao anterior lia SEMPRE obj.data, que fica
    # DESATUALIZADO enquanto o objeto esta em Edit Mode. O sintoma era perfeito
    # disfarce de sucesso: `transform.translate` devolvia FINISHED, a geometria
    # mudava de verdade na malha de edicao, e a comparacao de assinatura dizia
    # "geometria_mudou: False", porque comparava duas leituras da MESMA copia velha.
    # A propria referencia avisa disso, e eu cai nele.
    em_edicao = (bpy.context.mode == "EDIT_MESH" and obj.mode == "EDIT")
    if em_edicao:
        bm_ed = bmesh.from_edit_mesh(obj.data)
        bm_ed.verts.ensure_lookup_table()
        bm_ed.faces.ensure_lookup_table()
        fonte = "bmesh de edicao (malha viva)"
    else:
        fonte = "obj.data (fora de Edit Mode)"
    me = obj.data

    def co(v):
        p = (m @ v.co) if m is not None else v.co
        return (round(p.x, casas), round(p.y, casas), round(p.z, casas))

    if apenas_indices is None:
        if em_edicao:
            indice = {v: i for i, v in enumerate(bm_ed.verts)}
            verts = [co(v) for v in bm_ed.verts]
            faces = [tuple(indice[v] for v in f.verts) for f in bm_ed.faces]
        else:
            verts = [co(v) for v in me.vertices]
            faces = [tuple(p.vertices) for p in me.polygons]
        cobertura = "todos os vertices e faces do objeto"
    elif em_edicao:
        raise ErroDePrecondicao(
            "assinatura por indice de face nao e suportada em Edit Mode: o indice da "
            "malha de edicao nao corresponde ao de obj.data. Saia de Edit Mode.")
    else:
        alvo = set(apenas_indices)
        faces_alvo = [p for p in me.polygons if p.index in alvo]
        idx = sorted({i for p in faces_alvo for i in p.vertices})
        remapa = {v: n for n, v in enumerate(idx)}
        verts = [co(me.vertices[i]) for i in idx]
        faces = [tuple(remapa[i] for i in p.vertices) for p in faces_alvo]
        cobertura = "somente as %d faces de indice informado" % len(faces_alvo)

    h = hashlib.sha256()
    for t in verts:
        h.update(("%.*f,%.*f,%.*f;" % (casas, t[0], casas, t[1], casas, t[2])).encode())
    h.update(b"|")
    for f in faces:
        h.update((",".join(str(i) for i in f) + ";").encode())

    return {"objeto": obj.name, "sha256": h.hexdigest(), "espaco": espaco,
            "fonte_da_leitura": fonte,
            "casas_de_arredondamento": casas,
            "n_vertices": len(verts), "n_faces": len(faces),
            "cobertura": cobertura,
            "limite": ("indices de face valem SO para esta geometria capturada. "
                       "Retesselacao muda a assinatura sem mudar a superficie.")}


def _malha(nome):
    obj = bpy.data.objects.get(nome)
    if obj is None:
        raise ErroDePrecondicao("nao existe objeto chamado %r. Existem: %s"
                                % (nome, [o.name for o in bpy.data.objects]))
    if obj.type != "MESH":
        raise ErroDePrecondicao("o objeto %r e do tipo %s, e a operacao exige MESH"
                                % (nome, obj.type))
    return obj


# ---------------------------------------------------------------------------
# selecao
# ---------------------------------------------------------------------------

def seleciona_faces_por_caixa_de_mundo(nome_do_objeto, minimo, maximo,
                                       criterio="centro", exigir_nao_vazia=True):
    """Seleciona faces por caixa em coordenada de MUNDO.

    O erro que esta funcao existe para impedir: comparar `calc_center_median()`, que
    e LOCAL, com um limite de mundo. MEDIDO: seleciona o conjunto errado, e quando
    da vazio a edicao seguinte nao muda nada e nao acusa.

    criterio "centro": o centro da face esta na caixa.
    criterio "todos":  TODOS os vertices da face estao na caixa. Mais rigoroso, e e
                       o que serve para 'regiao protegida', porque triangulo pode
                       atravessar a caixa com o centro dentro dela."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode != "EDIT_MESH":
        raise ErroDePrecondicao("a selecao de faces exige Edit Mode; o modo atual e %s"
                                % bpy.context.mode)
    if criterio not in ("centro", "todos"):
        raise ErroDePrecondicao("criterio %r invalido: use 'centro' ou 'todos'" % criterio)
    mn, mx = Vector(minimo), Vector(maximo)
    for i in range(3):
        if mn[i] > mx[i]:
            raise ErroDePrecondicao("caixa invertida no eixo %d: min %s maior que max %s"
                                    % (i, mn[i], mx[i]))
    M = obj.matrix_world
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    def dentro(p):
        return all(mn[i] - 1e-9 <= p[i] <= mx[i] + 1e-9 for i in range(3))

    escolhidas = []
    for f in bm.faces:
        if criterio == "centro":
            ok = dentro(M @ f.calc_center_median())
        else:
            ok = all(dentro(M @ v.co) for v in f.verts)
        if ok:
            escolhidas.append(f.index)

    for f in bm.faces:
        f.select = False
    for e in bm.edges:
        e.select = False
    for v in bm.verts:
        v.select = False
    for i in escolhidas:
        bm.faces[i].select = True
    bm.select_flush(True)
    bmesh.update_edit_mesh(obj.data)

    marcadas = sum(1 for f in bm.faces if f.select)
    r = {"objeto": obj.name, "criterio": criterio,
         "caixa_mundo": {"min": [round(v, 6) for v in mn], "max": [round(v, 6) for v in mx]},
         "faces_que_atendem": len(escolhidas), "faces_marcadas": marcadas,
         "indices": escolhidas,
         "confirmacao": ("a contagem foi lida DEPOIS de marcar, na propria bmesh: "
                         "e medida, nao intencao")}
    if exigir_nao_vazia and marcadas == 0:
        raise ErroDePrecondicao(
            "a caixa de mundo informada nao contem nenhuma face pelo criterio %r. "
            "Editar agora nao mudaria nada e o operador devolveria CANCELLED sem "
            "erro. Confira a caixa contra o diagnostico: a caixa do objeto em mundo "
            "e min=%s max=%s." % (criterio,
                                  [round(min((M @ Vector(c))[i] for c in obj.bound_box), 4)
                                   for i in range(3)],
                                  [round(max((M @ Vector(c))[i] for c in obj.bound_box), 4)
                                   for i in range(3)]))
    return r


def le_selecao(nome_do_objeto):
    """Selecao viva, com os indices. Indice so vale para a geometria capturada."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode != "EDIT_MESH":
        raise ErroDePrecondicao("leitura de selecao viva exige Edit Mode; modo atual %s"
                                % bpy.context.mode)
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    faces = [f.index for f in bm.faces if f.select]
    M = obj.matrix_world
    centros = [[round(v, 6) for v in (M @ bm.faces[i].calc_center_median())] for i in faces]
    return {"objeto": obj.name, "faces_selecionadas": faces, "n": len(faces),
            "centros_em_mundo": centros,
            "assinatura_do_estado": assinatura(obj.name)["sha256"]}


def entra_em_edicao(nome_do_objeto, modo_de_selecao="face"):
    """Torna o objeto ativo e entra em Edit Mode. Sem isto, a leitura de selecao
    viva e a selecao por criterio nao tem como funcionar."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    mapa = {"vertice": (True, False, False), "aresta": (False, True, False),
            "face": (False, False, True)}
    if modo_de_selecao not in mapa:
        raise ErroDePrecondicao("modo_de_selecao %r invalido: use %s"
                                % (modo_de_selecao, sorted(mapa)))
    bpy.context.tool_settings.mesh_select_mode = mapa[modo_de_selecao]
    return {"objeto": obj.name, "modo": bpy.context.mode,
            "modo_de_selecao": modo_de_selecao}


def sai_de_edicao():
    """Sai para Object Mode e sincroniza os dados. Sair sem sincronizar deixa a
    malha de Object Mode desatualizada em relacao ao que foi editado."""
    anterior = bpy.context.mode
    if anterior == "EDIT_MESH":
        bpy.ops.object.mode_set(mode="OBJECT")
    return {"modo_anterior": anterior, "modo": bpy.context.mode}


def limpa_selecao(nome_do_objeto):
    """Desmarca tudo. Existe para o CONTROLE NEGATIVO: provar que operar com
    selecao vazia e barrado em vez de virar um nao-efeito silencioso."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode != "EDIT_MESH":
        raise ErroDePrecondicao("exige Edit Mode; modo atual %s" % bpy.context.mode)
    bm = bmesh.from_edit_mesh(obj.data)
    for f in bm.faces:
        f.select = False
    for e in bm.edges:
        e.select = False
    for v in bm.verts:
        v.select = False
    bmesh.update_edit_mesh(obj.data)
    return {"objeto": obj.name, "faces_selecionadas": sum(1 for f in bm.faces if f.select)}


def desloca_selecao(nome_do_objeto, vetor, exigir_selecao=True):
    """Desloca a selecao viva por um vetor de MUNDO, e devolve a medida do efeito.

    MEDIDO: com selecao vazia, `transform.translate` devolve {'CANCELLED'} e nada
    muda. Quem ignora o retorno conclui que editou. Aqui a selecao e contada ANTES
    e a geometria e medida DEPOIS: o efeito e fato, nao intencao."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode != "EDIT_MESH":
        raise ErroDePrecondicao("o deslocamento desta receita exige Edit Mode; modo "
                                "atual %s" % bpy.context.mode)
    bm = bmesh.from_edit_mesh(obj.data)
    n = sum(1 for f in bm.faces if f.select)
    nv = sum(1 for v in bm.verts if v.select)
    if exigir_selecao and nv == 0:
        raise ErroDePrecondicao(
            "nenhum vertice selecionado. O operador de deslocamento devolveria "
            "CANCELLED sem erro e a geometria ficaria intacta, o que se parece com "
            "sucesso em qualquer registro que so olhe excecao.")
    antes = assinatura(obj.name)
    r = bpy.ops.transform.translate(value=tuple(vetor))
    bmesh.update_edit_mesh(obj.data)
    depois = assinatura(obj.name)
    return {"objeto": obj.name, "vetor": [round(v, 6) for v in vetor],
            "faces_selecionadas_antes": n, "vertices_selecionados_antes": nv,
            "retorno_do_operador": sorted(r) if hasattr(r, "__iter__") else str(r),
            "assinatura_antes": antes["sha256"], "assinatura_depois": depois["sha256"],
            "geometria_mudou": antes["sha256"] != depois["sha256"]}


# ---------------------------------------------------------------------------
# preenchimento local entre dois limites
# ---------------------------------------------------------------------------

def preenche_entre_limites(nome_do_objeto, limite_a, limite_b, y_de, y_ate,
                           z_da_base, sobreposicao, origem_da_sobreposicao,
                           solver="EXACT", marcar_no_historico=False):
    """Constroi um volume fechado cuja superficie superior liga dois limites e o
    une ao solido existente.

    limite_a e limite_b: {"x": <mundo>, "z": <mundo>} de cada extremidade da
    ligacao. A superficie superior vai de um ao outro.

    sobreposicao: quanto o volume avanca DENTRO do material em cada extremidade e
    abaixo do piso. Nao existe valor universal para isso, e por isso o parametro e
    OBRIGATORIO e vem acompanhado de `origem_da_sobreposicao`, que registra de onde
    o numero saiu. MEDIDO no experimento: volume que apenas encosta deixa ranhura, e
    o defeito nao aparece em estanqueidade.

    Limite da receita: liga dois limites por uma superficie PLANA, ao longo de x,
    com secao constante em y. Superficie curva, limites nao paralelos a y ou vao
    com mais de dois limites estao FORA. Nesses casos, parar e dizer que nao se
    aplica, em vez de improvisar."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode == "EDIT_MESH":
        raise ErroDePrecondicao("a uniao booleana desta receita exige Object Mode; "
                                "saia de Edit Mode primeiro")
    if sobreposicao <= 0:
        raise ErroDePrecondicao(
            "sobreposicao tem que ser positiva. Com zero, o volume apenas ENCOSTA no "
            "material e a uniao produz contato tangente: foi MEDIDO que isso gera "
            "degeneracao e ranhura sem abrir nenhuma borda.")
    if not origem_da_sobreposicao:
        raise ErroDePrecondicao(
            "informe origem_da_sobreposicao. Um limiar sem procedencia e exatamente o "
            "defeito que este projeto evita; a sobreposicao sai da geometria e da "
            "tolerancia do trabalho, nao de constante universal.")
    # DOMINIO DA RECEITA. O volume construido aqui e um prisma alinhado aos eixos de
    # MUNDO, com secao constante em y. Se o objeto estiver girado, esse prisma nao
    # acompanha a peca e a "rampa" sai atravessada. Isso NAO e consertavel com um
    # ajuste de parametro: e outra receita. Melhor recusar do que improvisar.
    desalinhado = _eixos_desalinhados(obj.matrix_world)
    if desalinhado:
        raise ErroDePrecondicao(
            "esta receita constroi um prisma alinhado aos eixos de MUNDO e exige que o "
            "objeto tambem esteja alinhado. Medido: %s. Fora do dominio, portanto. "
            "Alternativas: aplicar a rotacao do objeto antes (Object > Apply > "
            "Rotation), trabalhar em coordenada local com a caixa convertida, ou usar "
            "uma receita que acompanhe a orientacao da peca. Nao improvisar."
            % desalinhado)
    xa, za = float(limite_a["x"]), float(limite_a["z"])
    xb, zb = float(limite_b["x"]), float(limite_b["z"])
    if abs(xb - xa) < 1e-9:
        raise ErroDePrecondicao("os dois limites tem o mesmo x: nao ha vao a ligar")
    if xa > xb:
        xa, za, xb, zb = xb, zb, xa, za
    if y_ate <= y_de:
        raise ErroDePrecondicao("faixa em y invalida: y_ate tem que ser maior que y_de")
    if z_da_base >= min(za, zb):
        raise ErroDePrecondicao(
            "z_da_base (%s) tem que ficar ABAIXO do menor limite (%s), senao o volume "
            "nao tem altura e nao intercepta o piso" % (z_da_base, min(za, zb)))

    ov = float(sobreposicao)
    x0, x1 = xa - ov, xb + ov
    zbase = z_da_base - ov
    incl = (zb - za) / (xb - xa)

    # CORRIGIDO depois de medir a SECAO da propria variante "correta". A versao
    # anterior prolongava a INCLINACAO da rampa para dentro do material. Consequencia
    # medida: com inclinacao -0,3 e sobreposicao 1,0, o topo do volume chegava a
    # z=20,3 em x=19, ou seja, subia 0,3 ACIMA da superficie protegida, criando uma
    # SALIENCIA sobre ela. E a amostragem uniforme de perfil PULOU esse trecho, entao
    # o defeito nao aparecia em nenhuma medida. Quem o revelou foi a secao.
    #
    # Agora o topo fica HORIZONTAL na altura do limite dentro de cada zona de
    # sobreposicao, e inclinado apenas ENTRE os limites.
    #
    # Eu previa que a coplanaridade resultante nas junções produziria degeneracao a
    # ser limpa depois. MEDIDO: produziu o OPOSTO. Com o topo inclinado avancando no
    # material, a uniao devolvia 33 faces e 4 delas de area nula; com o topo
    # horizontal na altura do limite, devolve 27 faces e ZERO degeneradas. O solver
    # EXACT lida melhor com faces coplanares coincidentes do que com a interseccao
    # obliqua. A previsao estava errada e o numero manda.
    perfil = [(x0, za), (xa, za), (xb, zb), (x1, zb), (x1, zbase), (x0, zbase)]
    me = bpy.data.meshes.new("_volume_de_preenchimento")
    bm = bmesh.new()
    try:
        baixo = [bm.verts.new((x, y_de, z)) for x, z in perfil]
        alto = [bm.verts.new((x, y_ate, z)) for x, z in perfil]
        bm.faces.new(baixo[::-1])
        bm.faces.new(alto)
        n_perfil = len(perfil)
        for i in range(n_perfil):
            j = (i + 1) % n_perfil
            bm.faces.new((baixo[i], baixo[j], alto[j], alto[i]))
        bm.normal_update()
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        volume_da_ferramenta = bm.calc_volume()
    finally:
        bm.free()
    # PREFLIGHT das tres interseccoes prometidas, ANTES de tocar no objeto.
    #
    # CORRIGIDO depois da revisao independente, que apontou dois defeitos ligados:
    # (1) a medida anterior era UM escalar de volume, e portanto provava "alguma"
    #     interseccao. Interseccao so com a base, ou so com um extremo, passava;
    # (2) a uniao era aplicada ANTES da medida, entao a falha deixava um corpo
    #     flutuante grudado na peca, e a receita mandava rever coordenadas sem
    #     desfazer nada. Uma segunda tentativa acumulava geometria defeituosa.
    #
    # As tres zonas sao exatamente as regioes que o prisma ocupa e onde ele precisa
    # encontrar material: a sobreposicao de cada extremo, e a faixa abaixo do piso.
    zonas = {
        "extremo_do_limite_a": ([x0, y_de, zbase], [xa, y_ate, za]),
        "extremo_do_limite_b": ([xb, y_de, zbase], [x1, y_ate, zb]),
        "abaixo_do_piso": ([x0, y_de, zbase], [x1, y_ate, z_da_base]),
    }
    medidas_de_zona = {}
    for rotulo, (mn, mx) in zonas.items():
        v = volume_de_material_na_caixa(obj.name, mn, mx, solver=solver)
        medidas_de_zona[rotulo] = {
            "caixa": {"min": [round(t, 6) for t in mn],
                      "max": [round(t, 6) for t in mx]},
            "volume_de_material": round(v, 6),
            "intercepta": v > 1e-9}
    sem_material = sorted(k for k, d in medidas_de_zona.items()
                          if not d["intercepta"])
    if sem_material:
        raise ErroDePrecondicao(
            "o volume de preenchimento nao encontraria material em %s, e a receita "
            "promete interceptar nos DOIS extremos e abaixo do piso. Nada foi "
            "alterado na peca: a medida e feita em copia, antes da uniao. Medidas por "
            "zona: %s. Causa mais comum: limites calculados em coordenada local e "
            "usados como se fossem de mundo."
            % (sem_material, {k: d["volume_de_material"]
                              for k, d in medidas_de_zona.items()}))

    ferramenta = bpy.data.objects.new("_volume_de_preenchimento", me)
    bpy.context.collection.objects.link(ferramenta)

    antes = mede_malha(obj.name)
    a_antes = assinatura(obj.name)
    vol_antes = _volume(obj)

    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new(name="preenchimento", type="BOOLEAN")
    mod.operation = "UNION"
    mod.object = ferramenta
    mod.solver = solver
    nome_do_mod = mod.name
    try:
        retorno = bpy.ops.object.modifier_apply(modifier=nome_do_mod)
    except Exception as e:
        obj.modifiers.remove(mod)
        bpy.data.objects.remove(ferramenta, do_unlink=True)
        raise ErroDePrecondicao("a uniao booleana falhou com solver %s: %s: %s"
                                % (solver, type(e).__name__, e))
    # CORRIGIDO depois da revisao final: a versao anterior ignorava o conjunto
    # devolvido pelo operador. E o MESMO defeito que esta receita documenta para
    # transform.translate e que ja foi corrigido na exportacao, deixado na operacao
    # CENTRAL. Com CANCELLED, o volume da uniao ficaria igual ao de antes, e a
    # aritmetica declararia como interseccao TODO o volume da ferramenta.
    estados = sorted(retorno) if hasattr(retorno, "__iter__") else [str(retorno)]
    ainda_pendurado = any(m.name == nome_do_mod for m in obj.modifiers)
    if "FINISHED" not in estados or ainda_pendurado:
        if ainda_pendurado:
            obj.modifiers.remove(obj.modifiers[nome_do_mod])
        bpy.data.objects.remove(ferramenta, do_unlink=True)
        raise ErroDePrecondicao(
            "a aplicacao da booleana nao concluiu: o operador devolveu %s e o "
            "modificador %s no objeto. CANCELLED nao levanta excecao, e sem esta "
            "guarda o volume ficaria igual ao de antes e a aritmetica declararia "
            "interseccao onde nao houve."
            % (estados, "continua" if ainda_pendurado else "saiu"))
    bpy.data.objects.remove(ferramenta, do_unlink=True)

    # UM ponto de historico por OPERACAO LOGICA, nao por chamada de ferramenta.
    # MEDIDO: empilhar um ponto aqui e outro na limpeza faz um `undo` parar no meio
    # do caminho, e a conferencia por assinatura acusa "nao recuperou" quando o que
    # aconteceu foi recuperar so metade. Por isso o padrao e NAO marcar aqui: quem
    # marca e a receita, depois de concluir o grupo inteiro. E MEDIDO tambem: em
    # background, `ed.undo` so fica pollavel com pelo menos DOIS pontos na pilha,
    # porque sem estado anterior nao ha a que voltar.
    historico = {"marcado_aqui": False}
    if marcar_no_historico:
        try:
            bpy.ops.ed.undo_push(message="preenchimento entre limites concluido")
            historico["marcado_aqui"] = True
        except Exception as e:
            historico["motivo"] = "%s: %s" % (type(e).__name__, e)
    historico["contexto"] = contexto_de_historico()

    depois = mede_malha(obj.name)
    vol_depois = _volume(obj)

    # A sobreposicao SERVIU? Volume de uniao de dois solidos que se interceptam e
    # MENOR que a soma dos dois. Se for igual a soma, os solidos apenas se
    # encostaram, e a receita nao cumpriu o que promete. Isto e medida, e nao
    # confianca no parametro que foi passado.
    soma = vol_antes + volume_da_ferramenta
    interseccao = soma - vol_depois
    tolerancia_de_volume = max(1e-9, abs(soma) * 1e-9)
    houve_interseccao = interseccao > tolerancia_de_volume

    return {"objeto": obj.name,
            "interseccao_por_zona": medidas_de_zona,
            "interseccao_com_o_material": {
                "volume_da_peca_antes": round(vol_antes, 6),
                "volume_do_volume_de_preenchimento": round(volume_da_ferramenta, 6),
                "soma_se_nao_houvesse_interseccao": round(soma, 6),
                "volume_da_uniao": round(vol_depois, 6),
                "interseccao_medida": round(interseccao, 6),
                "houve_interseccao": houve_interseccao,
                "nota": ("uniao de solidos que se interceptam tem volume MENOR que a "
                         "soma. Este escalar prova que houve ALGUMA interseccao; quem "
                         "prova as TRES prometidas e interseccao_por_zona, medida em "
                         "copia antes da uniao.")},
            "perfil_do_volume_em_xz": [[round(x, 6), round(z, 6)] for x, z in perfil],
            "faixa_em_y": [y_de, y_ate],
            "sobreposicao": ov, "origem_da_sobreposicao": origem_da_sobreposicao,
            "inclinacao_entre_os_limites": round(incl, 9),
            "topo_nas_zonas_de_sobreposicao": ("horizontal na altura do limite, para "
                                               "nao ultrapassar a superficie existente"),
            "volume_da_ferramenta": round(volume_da_ferramenta, 6),
            "volume_antes": round(vol_antes, 6), "volume_depois": round(vol_depois, 6),
            "solver": solver,
            "assinatura_antes": a_antes["sha256"],
            "assinatura_depois": assinatura(obj.name)["sha256"],
            "malha_antes": antes, "malha_depois": depois,
            "historico": historico,
            "limite": ("uniao concluida NAO prova junção correta. Ranhura e desnivel "
                       "exigem secao ou comparacao de superficie; degeneracao exige "
                       "contagem propria. Sao medidas separadas.")}


def mede_topo_em_pontos(nome_do_objeto, pontos, tolerancia=0.01):
    """Mede a altura do MATERIAL na vertical de cada ponto e compara com o valor
    esperado informado. E esta medida que pega ranhura e desnivel; nenhuma medida
    topologica pega, porque a malha pode estar fechada e a forma errada.

    pontos: [[x, y, z_esperado], ...] em coordenada de MUNDO.

    Por que comparar com o ESPERADO e nao dois lados da junção: a versao anterior
    amostrava a 0,01 de cada lado do limite e chamava a diferenca de "degrau". Numa
    superficie inclinada isso mede a INCLINACAO, nao o degrau. MEDIDO: rampa de
    inclinacao 0,3 produzia "degrau" de 0,006, que era artefato do proprio metodo."""
    obj = _malha(nome_do_objeto)
    M = obj.matrix_world
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        amostras = []
        for p in pontos:
            x, y, z_esp = float(p[0]), float(p[1]), float(p[2])
            z = _topo_na_vertical(bm, M, x, y)
            if z is None:
                amostras.append({"x": round(x, 5), "y": round(y, 5),
                                 "z_esperado": round(z_esp, 5), "estado": "SEM_MATERIAL"})
                continue
            desvio = z - z_esp
            amostras.append({"x": round(x, 5), "y": round(y, 5),
                             "z_esperado": round(z_esp, 5), "z_medido": round(z, 5),
                             "desvio": round(desvio, 5),
                             "dentro_da_tolerancia": abs(desvio) <= tolerancia})
    finally:
        bm.free()
    com_medida = [a for a in amostras if "desvio" in a]
    sem = [a for a in amostras if "desvio" not in a]
    return {"objeto": obj.name, "tolerancia": tolerancia,
            "n_pontos": len(pontos), "n_medidos": len(com_medida),
            "n_sem_material": len(sem),
            "desvio_maximo_absoluto": (round(max(abs(a["desvio"]) for a in com_medida), 5)
                                       if com_medida else None),
            "todos_dentro_da_tolerancia": bool(com_medida) and all(
                a["dentro_da_tolerancia"] for a in com_medida) and not sem,
            "amostras": amostras,
            "limite": ("a conclusao vale para os %d pontos amostrados, nas posicoes "
                       "listadas. Amostragem nao prova toda a superficie."
                       % len(pontos))}


def _topo_na_vertical(bm, M, x, y):
    """Maior z de material sobre (x, y), por ponto dentro de triangulo em projecao."""
    from mathutils.geometry import intersect_point_tri_2d
    melhor = None
    for f in bm.faces:
        pts = [M @ v.co for v in f.verts]
        for i in range(1, len(pts) - 1):
            a, b, c = pts[0], pts[i], pts[i + 1]
            if intersect_point_tri_2d((x, y), (a.x, a.y), (b.x, b.y), (c.x, c.y)):
                z = _z_no_triangulo(a, b, c, x, y)
                if z is not None and (melhor is None or z > melhor):
                    melhor = z
    return melhor


def _z_no_triangulo(a, b, c, x, y):
    d = (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)
    if abs(d) < 1e-12:
        return None
    u = ((x - a.x) * (c.y - a.y) - (c.x - a.x) * (y - a.y)) / d
    v = ((b.x - a.x) * (y - a.y) - (x - a.x) * (b.y - a.y)) / d
    return a.z + u * (b.z - a.z) + v * (c.z - a.z)


def limpa_degeneracoes_na_regiao(nome_do_objeto, minimo, maximo, tolerancia,
                                 justificativa_da_tolerancia,
                                 marcar_no_historico=False):
    """Remove vertices coincidentes e arestas degeneradas SO na regiao informada.

    MEDIDO: a uniao booleana produziu 4 faces de area nula mesmo com sobreposicao
    positiva e sem abrir nenhuma borda. Limpeza e necessaria, e limpeza GLOBAL e
    perigosa: ela pode apagar detalhe que se queria preservar.

    A tolerancia e obrigatoria e vem acompanhada de justificativa, porque tem que
    ser menor que o menor detalhe a preservar. Nao existe valor universal.

    Depois de limpar, MEDE de novo. Se a limpeza nao reduziu degeneracao, isso e
    dito; se reduziu, o quanto e dito. A funcao nao afirma que a peca ficou boa."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode == "EDIT_MESH":
        raise ErroDePrecondicao("saia de Edit Mode antes de limpar")
    if tolerancia <= 0:
        raise ErroDePrecondicao("tolerancia tem que ser positiva")
    if not justificativa_da_tolerancia:
        raise ErroDePrecondicao(
            "informe justificativa_da_tolerancia: a tolerancia tem que ser menor que o "
            "menor detalhe a preservar, e isso depende da peca, nao de constante.")
    mn, mx = Vector(minimo), Vector(maximo)
    M = obj.matrix_world
    antes = mede_malha(obj.name)

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        na_regiao = [v for v in bm.verts
                     if all(mn[k] - 1e-9 <= (M @ v.co)[k] <= mx[k] + 1e-9 for k in range(3))]
        if not na_regiao:
            raise ErroDePrecondicao(
                "nenhum vertice na regiao informada: nao ha o que limpar ali. "
                "Caixa min=%s max=%s" % (list(minimo), list(maximo)))
        n_antes = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=na_regiao, dist=tolerancia)
        bm.faces.ensure_lookup_table()
        degeneradas = [f for f in bm.faces if f.calc_area() <= 1e-9]
        bmesh.ops.dissolve_degenerate(bm, dist=tolerancia,
                                      edges=[e for f in degeneradas for e in f.edges])
        n_depois = len(bm.verts)
        bm.to_mesh(obj.data)
        obj.data.update()
    finally:
        bm.free()

    # MEDIDO, e e a advertencia da referencia confirmada: escrever por bm.to_mesh e
    # MUTACAO DIRETA DE DADOS e NAO entra no historico. Sem o push abaixo, o `redo`
    # devolvia a peca ao estado imediatamente pos-uniao, sem a limpeza, e a
    # conferencia por assinatura acusava recuperou=False. Nao era o redo que falhou:
    # era a limpeza que nunca tinha sido registrada.
    historico = {"marcado_aqui": False}
    if marcar_no_historico:
        try:
            bpy.ops.ed.undo_push(message="limpeza local de degeneracoes")
            historico["marcado_aqui"] = True
        except Exception as e:
            historico["motivo"] = "%s: %s" % (type(e).__name__, e)
    historico["nota"] = ("escrever por bm.to_mesh e MUTACAO DIRETA DE DADOS e NAO "
                         "entra no historico sozinha. Se esta limpeza fizer parte de "
                         "uma operacao logica maior, marcar UMA vez no fim dela; se "
                         "for isolada, marcar aqui com marcar_no_historico=True. Sem "
                         "nenhum push, ela e irrecuperavel por historico.")

    depois = mede_malha(obj.name)
    return {"objeto": obj.name,
            "caixa_mundo": {"min": list(minimo), "max": list(maximo)},
            "tolerancia": tolerancia,
            "justificativa_da_tolerancia": justificativa_da_tolerancia,
            "vertices_na_regiao_antes": len(na_regiao),
            "vertices_no_objeto": {"antes": n_antes, "depois": n_depois},
            "degeneradas_antes": antes["faces_degeneradas"],
            "degeneradas_depois": depois["faces_degeneradas"],
            "reduziu": depois["faces_degeneradas"] < antes["faces_degeneradas"],
            "zerou": depois["faces_degeneradas"] == 0,
            "abriu_borda": depois["arestas_abertas"] > antes["arestas_abertas"],
            "malha_antes": antes, "malha_depois": depois,
            "historico": historico,
            "limite": ("limpeza restrita a caixa declarada. Reducao de degeneracao NAO "
                       "prova que a forma esta certa, e a comparacao da regiao "
                       "protegida tem que ser refeita DEPOIS desta limpeza.")}


def _eixos_desalinhados(m, tol=1e-6):
    """Descreve o desalinhamento entre os eixos locais e os de mundo, ou None quando
    a orientacao e alinhada. Escala uniforme positiva e permitida; rotacao e
    cisalhamento nao, porque o prisma da receita e alinhado aos eixos."""
    problemas = []
    for i, eixo in enumerate("xyz"):
        col = Vector((m[0][i], m[1][i], m[2][i]))
        if col.length < tol:
            problemas.append("eixo local %s tem comprimento nulo" % eixo)
            continue
        u = col.normalized()
        # tem que apontar ao longo de UM eixo de mundo
        maiores = sorted(range(3), key=lambda k: -abs(u[k]))
        if abs(abs(u[maiores[0]]) - 1.0) > 1e-4:
            problemas.append("eixo local %s aponta para %s, que nao e eixo de mundo"
                             % (eixo, [round(v, 4) for v in u]))
    return "; ".join(problemas) if problemas else None


def _caixa_de_malha(nome, minimo, maximo):
    """Objeto-caixa por cantos de MUNDO, para uso como ferramenta de booleana."""
    mn, mx = Vector(minimo), Vector(maximo)
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    try:
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((mn.x if v.co.x < 0 else mx.x,
                           mn.y if v.co.y < 0 else mx.y,
                           mn.z if v.co.z < 0 else mx.z))
        bm.to_mesh(me)
    finally:
        bm.free()
    obj = bpy.data.objects.new(nome, me)
    bpy.context.collection.objects.link(obj)
    return obj


def volume_de_material_na_caixa(nome_do_objeto, minimo, maximo, solver="EXACT"):
    """Volume de material do objeto DENTRO da caixa de mundo informada.

    Mede numa CÓPIA e apaga tudo depois: o objeto do usuario nao e tocado. Usa
    interseccao booleana, portanto e volume exato, nao amostragem."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode == "EDIT_MESH":
        raise ErroDePrecondicao("saia de Edit Mode antes de medir por booleana")
    copia = bpy.data.objects.new("_copia_para_medir", obj.data.copy())
    copia.matrix_world = obj.matrix_world.copy()
    bpy.context.collection.objects.link(copia)
    caixa = _caixa_de_malha("_caixa_para_medir", minimo, maximo)
    try:
        bpy.context.view_layer.objects.active = copia
        mod = copia.modifiers.new(name="corta", type="BOOLEAN")
        mod.operation = "INTERSECT"
        mod.object = caixa
        mod.solver = solver
        nome_do_mod = mod.name
        retorno = bpy.ops.object.modifier_apply(modifier=nome_do_mod)
        # a mesma guarda da uniao: sem ela, um CANCELLED devolveria o volume
        # INTEGRAL da copia como se fosse o volume dentro da caixa, e o preflight
        # aprovaria interseccao onde nao ha.
        estados = sorted(retorno) if hasattr(retorno, "__iter__") else [str(retorno)]
        if "FINISHED" not in estados or any(m.name == nome_do_mod
                                            for m in copia.modifiers):
            raise ErroDePrecondicao(
                "o recorte booleano para medir volume na caixa nao concluiu: "
                "operador devolveu %s. A medida seria o volume integral da peca, e "
                "nao o volume dentro da caixa." % estados)
        return abs(_volume(copia))
    finally:
        for o in (copia, caixa):
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass


def _volume(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return bm.calc_volume()
    finally:
        bm.free()


def compara_regiao_protegida(nome_do_objeto, assinatura_anterior_por_indice,
                             minimo, maximo, casas=CASAS):
    """Preservacao exige alvo explicito e comparacao geometrica.

    MEDIDO no experimento: contar faces cujos vertices caem numa caixa NAO prova
    preservacao, porque triangulo pode atravessar a caixa. Aqui o criterio e
    'TODOS os vertices da face dentro da caixa', e o resultado declara que a
    conclusao vale SO para essa regiao.

    Compara o conjunto de POSICOES, nao os indices: retesselacao muda indice sem
    mudar superficie, e isso tem que aparecer como diferenca de tesselacao, nao
    como alteracao da superficie."""
    obj = _malha(nome_do_objeto)
    anterior = set(tuple(t) for t in assinatura_anterior_por_indice["posicoes"])
    if not anterior:
        raise ErroDePrecondicao(
            "a captura anterior esta vazia: nao ha o que comparar. Sem isto, a funcao "
            "devolveria um veredito sobre conjunto nenhum.")
    atual = _posicoes_na_caixa(obj, minimo, maximo, casas)
    faltando = sorted(anterior - atual)
    novas = sorted(atual - anterior)
    identico = not faltando and not novas

    # CORRIGIDO 08/09/2026, depois de validacao adversarial. A versao anterior
    # comparava SOMENTE o conjunto de posicoes e declarava, no proprio campo
    # `limite`, que conjunto identico com contagem de faces diferente e
    # "retesselacao, nao alteracao da superficie". Isso e falso: apagando uma face de
    # um tetraedro, os quatro vertices continuam nas tres faces restantes, o conjunto
    # fica identico e 3,4641 mm2 de superficie desapareceram. Area distingue.
    area_agora, faces_agora = _area_na_caixa(obj, minimo, maximo)
    area_antes = assinatura_anterior_por_indice.get("area_total_mm2")
    faces_antes = assinatura_anterior_por_indice.get("n_faces")
    tol_area = max(1e-6, 1e-6 * abs(area_agora))
    if area_antes is None:
        area_ok = None
        veredito = "INDETERMINADO"
        nota = ("a captura anterior nao traz area: ela foi feita por uma versao que "
                "nao a media. Conjunto de posicoes identico NAO prova superficie "
                "preservada, entao nenhum veredito de preservacao e emitido aqui.")
    else:
        area_ok = abs(area_agora - float(area_antes)) <= tol_area
        if identico and area_ok:
            veredito = "PRESERVADA"
            nota = ("conjunto de posicoes identico E area identica dentro da "
                    "tolerancia: a superficie desta caixa nao mudou. Diferenca na "
                    "CONTAGEM de faces, com estes dois iguais, e retesselacao.")
        elif identico and not area_ok:
            veredito = "ALTERADA"
            nota = ("conjunto de posicoes identico e AREA DIFERENTE: face removida ou "
                    "acrescentada. E exatamente o caso que a versao anterior desta "
                    "funcao chamava de retesselacao.")
        else:
            veredito = "ALTERADA"
            nota = "o conjunto de posicoes mudou: ha vertice novo ou desaparecido."
    return {"objeto": obj.name,
            "caixa_mundo": {"min": list(minimo), "max": list(maximo)},
            "criterio": "faces com TODOS os vertices dentro da caixa",
            "n_posicoes_antes": len(anterior), "n_posicoes_agora": len(atual),
            "posicoes_que_desapareceram": len(faltando),
            "posicoes_novas": len(novas),
            "conjunto_de_posicoes_identico": identico,
            "area_antes_mm2": area_antes, "area_agora_mm2": area_agora,
            "area_dentro_da_tolerancia": area_ok, "tolerancia_de_area_mm2": tol_area,
            "n_faces_antes": faces_antes, "n_faces_agora": faces_agora,
            "veredito": veredito, "nota": nota,
            "exemplos_desaparecidas": faltando[:6], "exemplos_novas": novas[:6],
            "limite": ("a conclusao vale SO para a caixa declarada, e exige as DUAS "
                       "medidas: conjunto de posicoes e area. Conjunto identico "
                       "sozinho nao prova superficie preservada.")}


def captura_regiao_protegida(nome_do_objeto, minimo, maximo, casas=CASAS):
    """Captura as posicoes da regiao a preservar, para comparar depois."""
    obj = _malha(nome_do_objeto)
    pos = _posicoes_na_caixa(obj, minimo, maximo, casas)
    # CORRIGIDO depois de medir: a captura devolvia conjunto VAZIO em silencio, e a
    # comparacao seguinte ainda emitia veredito. Comparar nada com nada e dar nome de
    # resultado e o defeito central que este projeto persegue.
    if not pos:
        raise ErroDePrecondicao(
            "nenhuma face tem TODOS os vertices dentro da caixa informada, entao nao "
            "existe regiao capturada para comparar depois. Caixa min=%s max=%s. A "
            "caixa precisa CONTER as faces inteiras: encolher os limites para excluir "
            "a vizinhanca costuma excluir tambem a face alvo." % (list(minimo), list(maximo)))
    area, n_faces = _area_na_caixa(obj, minimo, maximo)
    return {"objeto": obj.name, "casas": casas,
            "caixa_mundo": {"min": list(minimo), "max": list(maximo)},
            "posicoes": sorted(pos), "n": len(pos),
            "area_total_mm2": area, "n_faces": n_faces,
            "por_que_a_area": ("conjunto de posicoes nao distingue retesselacao de "
                               "face removida: os vertices de uma face apagada "
                               "continuam nas faces vizinhas. A area distingue.")}


def _area_na_caixa(obj, minimo, maximo):
    """Area total das faces com TODOS os vertices na caixa, e quantas sao.

    Acrescentado em 08/09/2026, depois de validacao adversarial: a comparacao usava
    somente o conjunto de POSICOES, e remover uma face mantem as posicoes dos seus
    vertices nas faces vizinhas. Area distingue retesselacao de superficie alterada:
    retesselar preserva area, remover face nao."""
    M = obj.matrix_world
    mn, mx = Vector(minimo), Vector(maximo)
    bm = bmesh.new()
    try:
        if bpy.context.mode == "EDIT_MESH" and bpy.context.edit_object is obj:
            bm = bmesh.from_edit_mesh(obj.data).copy()
        else:
            bm.from_mesh(obj.data)
        area, n = 0.0, 0
        for f in bm.faces:
            mundo = [M @ v.co for v in f.verts]
            if all(mn.x <= c.x <= mx.x and mn.y <= c.y <= mx.y and mn.z <= c.z <= mx.z
                   for c in mundo):
                # area no espaco de MUNDO: a matriz pode ter escala
                soma = Vector((0.0, 0.0, 0.0))
                for i in range(len(mundo)):
                    a_, b_ = mundo[i], mundo[(i + 1) % len(mundo)]
                    soma += a_.cross(b_)
                area += soma.length / 2.0
                n += 1
        return round(area, 6), n
    finally:
        try:
            bm.free()
        except Exception:                                         # noqa: BLE001
            pass


def _posicoes_na_caixa(obj, minimo, maximo, casas):
    M = obj.matrix_world
    mn, mx = Vector(minimo), Vector(maximo)
    me = obj.data
    fora = set()
    for p in me.polygons:
        pts = [M @ me.vertices[i].co for i in p.vertices]
        if all(all(mn[k] - 1e-9 <= q[k] <= mx[k] + 1e-9 for k in range(3)) for q in pts):
            for q in pts:
                fora.add((round(q.x, casas), round(q.y, casas), round(q.z, casas)))
    return fora


def confere_selecao_capturada(nome_do_objeto, captura, exigir_indices_validos=True):
    """A seleção capturada ainda vale para a geometria de agora?

    POR QUE ISTO EXISTE. `le_selecao` devolve indices de face e a assinatura do
    estado em que eles foram lidos. Indice de face so tem sentido naquela
    geometria: qualquer coisa que retessele — uma booleana, uma limpeza, um undo —
    renumera tudo. Reutilizar os indices depois disso edita OUTRAS faces, sem erro
    nenhum, e o resultado parece plausivel.

    Esta funcao compara a assinatura guardada com a atual e RECUSA quando mudou.
    O caminho sem mudanca continua funcionando: e o controle positivo."""
    if not isinstance(captura, dict) or "assinatura_do_estado" not in captura:
        raise ErroDePrecondicao(
            "captura invalida: esperava o dicionario devolvido por le_selecao, que "
            "traz 'assinatura_do_estado' e 'faces_selecionadas'.")
    obj = _malha(nome_do_objeto)
    atual = assinatura(obj.name)
    guardada = captura["assinatura_do_estado"]
    faces = captura.get("faces_selecionadas") or []
    n_faces_agora = (len(bmesh.from_edit_mesh(obj.data).faces)
                     if bpy.context.mode == "EDIT_MESH" and obj.mode == "EDIT"
                     else len(obj.data.polygons))
    fora = [i for i in faces if i >= n_faces_agora]
    igual = (atual["sha256"] == guardada)
    r = {"objeto": obj.name, "assinatura_guardada": guardada,
         "assinatura_atual": atual["sha256"], "geometria_inalterada": igual,
         "n_faces_na_captura": len(faces), "n_faces_no_objeto_agora": n_faces_agora,
         "indices_fora_do_intervalo": fora}
    if not igual:
        raise ErroDePrecondicao(
            "a geometria mudou depois da captura da seleção: assinatura guardada %s, "
            "atual %s. Os indices de face da captura nao valem mais e editar por eles "
            "atingiria outras faces sem acusar erro. Releia a seleção antes de editar. "
            "%s" % (guardada[:12], atual["sha256"][:12],
                    ("Alem disso, %d indice(s) da captura nem existem mais: %s."
                     % (len(fora), fora[:8])) if fora else
                    "Os indices ainda existem, o que torna o erro silencioso."))
    if exigir_indices_validos and fora:
        raise ErroDePrecondicao(
            "a assinatura bate mas %d indice(s) da captura estao fora do intervalo "
            "atual (%d faces): %s. Captura inconsistente."
            % (len(fora), n_faces_agora, fora[:8]))
    return r


# ---------------------------------------------------------------------------
# recuperacao
# ---------------------------------------------------------------------------

def marca_recuperacao(mensagem):
    """Ponto de undo. MEDIDO: em background o sistema de undo nasce desligado, e
    `ed.undo` falha no poll sem um push previo. Chamar isto ANTES de editar."""
    bpy.ops.ed.undo_push(message=mensagem)
    return {"marcado": mensagem, "em_background": bpy.app.background,
             "nota": ("em background o primeiro push tambem INICIALIZA o sistema de "
                      "undo. Sem ele, ed.undo nem e chamavel.")}


def contexto_de_historico():
    """Estado do que o undo depende. MEDIDO: `ed.undo` falha de dois modos
    diferentes, com mensagens diferentes, e nenhum deles e 'a operacao nao existe':

      - 'Undo disabled at startup in background-mode': nunca houve push nesta
        sessao, e o sistema nasce desligado em background;
      - 'poll() failed, context is incorrect': o sistema existe, e o contexto
        corrente nao serve para a chamada.

    Consultar isto ANTES de prometer recuperacao por historico."""
    return {"em_background": bpy.app.background,
            "janelas": len(bpy.context.window_manager.windows),
            "modo": bpy.context.mode,
            "undo_pollavel": bool(bpy.ops.ed.undo.poll()),
            "redo_pollavel": bool(bpy.ops.ed.redo.poll()),
            "objeto_ativo": getattr(bpy.context.active_object, "name", None)}


def desfaz_e_confere(nome_do_objeto, assinatura_esperada):
    """Undo conferido pelo CONTEUDO. A chamada ter retornado nao prova nada, e
    referencias a objeto/malha podem ficar invalidas: relemos pelo nome.

    Quando o historico nao esta chamavel, isto NAO tenta e nao finge: levanta
    ErroDePrecondicao dizendo o estado medido, para a receita cair na recuperacao
    por arquivo salvo em vez de prometer o que nao tem."""
    ctx = contexto_de_historico()
    if not ctx["undo_pollavel"]:
        raise ErroDePrecondicao(
            "bpy.ops.ed.undo nao esta chamavel neste contexto: %s. Nao ha recuperacao "
            "por historico aqui; usar o arquivo salvo antes da operacao. Ctrl+Z "
            "tambem nao substitui recuperacao depois de fechar a aplicacao." % ctx)
    bpy.ops.ed.undo()
    a = assinatura(nome_do_objeto)
    return {"contexto": ctx,
            "assinatura_apos_undo": a["sha256"],
            "assinatura_esperada": assinatura_esperada,
            "recuperou": a["sha256"] == assinatura_esperada,
            "nota": "objeto relido por NOME depois do undo, nao por referencia antiga"}


def refaz_e_confere(nome_do_objeto, assinatura_esperada):
    ctx = contexto_de_historico()
    if not ctx["redo_pollavel"]:
        raise ErroDePrecondicao(
            "bpy.ops.ed.redo nao esta chamavel neste contexto: %s" % ctx)
    bpy.ops.ed.redo()
    a = assinatura(nome_do_objeto)
    return {"contexto": ctx,
            "assinatura_apos_redo": a["sha256"],
            "assinatura_esperada": assinatura_esperada,
            "recuperou": a["sha256"] == assinatura_esperada}


# ---------------------------------------------------------------------------
# medidas de qualidade da malha, na propria cena
# ---------------------------------------------------------------------------

def mede_malha(nome_do_objeto, area_minima=1e-9):
    """Bordas, nao-manifold, degeneracoes e componentes, MEDIDOS SEPARADAMENTE.

    MEDIDO no experimento: uniao booleana produz face de area nula sem abrir
    nenhuma borda. Por isso 'sem borda aberta' nao substitui 'sem degeneracao'."""
    obj = _malha(nome_do_objeto)
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        abertas = [e.index for e in bm.edges if len(e.link_faces) == 1]
        nao_manifold = [e.index for e in bm.edges if len(e.link_faces) > 2]
        soltas = [e.index for e in bm.edges if len(e.link_faces) == 0]
        degeneradas = [f.index for f in bm.faces if f.calc_area() <= area_minima]
        # CORRIGIDO depois da revisao independente: o docstring desta funcao dizia
        # "e componentes" e o retorno NAO trazia contagem de componente nenhuma. O
        # mapa de ferramentas repetia a promessa. Era afirmacao sem medida atras,
        # dentro da ferramenta que existe para nao fazer isso.
        n_componentes = _componentes_conexos(bm)
        return {"objeto": obj.name,
                "n_componentes_conexos": n_componentes,
                "arestas_abertas": len(abertas), "arestas_nao_manifold": len(nao_manifold),
                "arestas_soltas": len(soltas),
                "faces_degeneradas": len(degeneradas),
                "limite_de_area_usado": area_minima,
                "faces": len(bm.faces), "vertices": len(bm.verts),
                "indices_degeneradas": degeneradas[:50],
                "indices_nao_manifold": nao_manifold[:50],
                "limite": ("estas sao medidas TOPOLOGICAS. Nenhuma delas detecta "
                           "ranhura, desnivel ou forma errada: malha fechada pode ter "
                           "a forma errada.")}
    finally:
        bm.free()


def _componentes_conexos(bm):
    """Componentes conexos por travessia de vertices ligados por aresta.

    Vertice solto conta como componente proprio, como em qualquer contagem de
    componentes: ele e material que nao encosta no resto."""
    vistos = set()
    n = 0
    for v in bm.verts:
        if v.index in vistos:
            continue
        n += 1
        pilha = [v]
        vistos.add(v.index)
        while pilha:
            atual = pilha.pop()
            for e in atual.link_edges:
                outro = e.other_vert(atual)
                if outro is not None and outro.index not in vistos:
                    vistos.add(outro.index)
                    pilha.append(outro)
    return n


def une_por_distancia(pontos, grade, p, tol, exatos=None):
    """Une um ponto ao conjunto por DISTANCIA. Devolve (indice, novo).

    `pontos` e a lista de SAIDA, arredondada para leitura. `exatos` e a lista
    paralela com as coordenadas SEM arredondar, e e contra ela que a distancia e
    medida. `grade` e o indice espacial de celula `tol`.

    Duas correcoes, as duas apontadas por revisao independente, e as duas do mesmo
    tipo de erro:

    1. a primeira versao unia por CHAVE arredondada. Dois pontos em 0.999994 e
       1.000001 distam 7e-6, cabem numa tolerancia de 1e-5, e ainda assim caiam em
       chaves diferentes, porque a fronteira de arredondamento passava entre eles;
    2. a segunda passou a medir distancia, e media contra a coordenada ARREDONDADA
       que ja estava guardada. Com tolerancia 1e-5, os pontos 0.00000051 e
       0.00001052 distam 1.001e-5 e NAO deveriam unir; o primeiro era guardado como
       0.000001 e a distancia medida virava 9.52e-6, unindo-os.

    Ou seja: eu fechei os exemplos medidos duas vezes sem fechar o contrato. Agora o
    indice guarda o valor exato e o arredondamento fica SO na representacao de
    saida."""
    if exatos is None:
        exatos = pontos
    cx, cy, cz = int(p[0] // tol), int(p[1] // tol), int(p[2] // tol)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for idx in grade.get((cx + dx, cy + dy, cz + dz), ()):
                    q = exatos[idx]
                    if ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                            + (p[2] - q[2]) ** 2) <= tol * tol:
                        return idx, False
    idx = len(pontos)
    pontos.append([round(p[0], 6), round(p[1], 6), round(p[2], 6)])
    if exatos is not pontos:
        exatos.append([p[0], p[1], p[2]])
    grade.setdefault((cx, cy, cz), []).append(idx)
    return idx, True


def secao_por_plano(nome_do_objeto, ponto, normal, tolerancia=1e-7,
                    tolerancia_de_uniao=1e-5):
    """Interseccao das arestas do objeto com um plano, em coordenada de MUNDO.

    Trata aresta coplanar ao plano, vertice exatamente no plano, e ponto coincidente.
    Devolve os pontos unidos por proximidade, os segmentos, e QUANTOS pontos foram
    unidos — a contagem existe para a promessa de uniao ser conferivel em vez de
    apenas afirmada.

    `tolerancia_de_uniao` tem que ser MAIOR que o ruido numerico da interpolacao, que
    foi medido nesta instalacao entre 1e-6 e 3e-6, e menor que o menor detalhe que se
    queira distinguir. O padrao de 1e-5 fica entre os dois. Com um limiar mais fino
    que o ruido, pontos coincidentes NAO se unem e a contagem de pontos sai dobrada.

    Serve para inspecionar a JUNCAO: e a medida que pega ranhura, que a
    estanqueidade nao pega."""
    obj = _malha(nome_do_objeto)
    p0, n = Vector(ponto), Vector(normal)
    if n.length < 1e-12:
        raise ErroDePrecondicao("a normal do plano tem comprimento zero")
    n = n.normalized()
    M = obj.matrix_world
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        pontos, segmentos, coplanares, ambiguas = [], [], 0, 0

        def dist(v):
            return (M @ v.co - p0).dot(n)

        # Historia deste trecho, porque ela e a licao. Primeira versao: chave por
        # arredondamento a 7 casas. Os pontos vem de (M @ a.co).lerp(M @ b.co, t),
        # interpolacao sobre coordenada de precisao SIMPLES, cujo ruido foi MEDIDO
        # entre 1e-6 e 3e-6 — uma a duas ordens ACIMA da granularidade da chave. Em 4
        # de 33 planos a secao devolvia 20 pontos em vez de 10, com y em 9.999999 e
        # 10.000002.
        #
        # Segunda versao: mesma chave, com o arredondamento derivado da tolerancia.
        # Isso fechou o exemplo medido e NAO o contrato: uma revisao independente
        # apontou que arredondar casas nao e unir por DISTANCIA. Dois pontos em
        # 0.999994 e 1.000001 distam 7e-6, portanto estao dentro de 1e-5, e ainda
        # assim caem em chaves diferentes, porque a fronteira de arredondamento passa
        # entre eles.
        #
        # Esta versao une por distancia de verdade: grade espacial de celula igual a
        # tolerancia, e consulta das 27 celulas vizinhas, o que garante encontrar
        # qualquer ponto a menos de uma tolerancia, inclusive atravessando fronteira
        # de celula.
        tol = float(tolerancia_de_uniao)
        if tol <= 0:
            raise ErroDePrecondicao("tolerancia_de_uniao tem que ser positiva")
        grade = {}
        exatos = []
        unidos = [0]

        def registra(p):
            idx, novo = une_por_distancia(pontos, grade, (p.x, p.y, p.z), tol,
                                          exatos=exatos)
            if not novo:
                unidos[0] += 1
            return idx

        for f in bm.faces:
            cortes = []
            ds = [dist(v) for v in f.verts]
            if all(abs(d) <= tolerancia for d in ds):
                coplanares += 1
                continue
            nv = len(f.verts)
            for i in range(nv):
                a, b = f.verts[i], f.verts[(i + 1) % nv]
                da, db = ds[i], ds[(i + 1) % nv]
                if abs(da) <= tolerancia:
                    cortes.append(registra(M @ a.co))
                elif da * db < 0:
                    t = da / (da - db)
                    cortes.append(registra((M @ a.co).lerp(M @ b.co, t)))
            unicos = []
            for c in cortes:
                if c not in unicos:
                    unicos.append(c)
            if len(unicos) > 2:
                # face nao convexa cortada em mais de dois pontos: ligar o primeiro
                # ao ultimo seria arbitrario. Conta-se e declara-se, em vez de
                # inventar o segmento.
                ambiguas += 1
            if len(unicos) >= 2:
                segmentos.append([unicos[0], unicos[-1]])

        return {"objeto": obj.name,
                "plano": {"ponto": [round(v, 6) for v in p0],
                          "normal": [round(v, 6) for v in n]},
                "n_pontos": len(pontos), "n_segmentos": len(segmentos),
                "faces_coplanares_ignoradas": coplanares,
                "faces_com_mais_de_dois_cruzamentos": ambiguas,
                "tolerancia_de_uniao": tolerancia_de_uniao,
                "pontos_unidos_por_coincidencia": unidos[0],
                "pontos": pontos, "segmentos": segmentos,
                "limite": ("a secao descreve o corte NESTE plano. Uma secao nao prova "
                           "a junção inteira: declarar as posicoes amostradas. Face nao "
                           "convexa cortada em mais de dois pontos e CONTADA em "
                           "faces_com_mais_de_dois_cruzamentos e o segmento dela nao e "
                           "confiavel; se essa contagem nao for zero, a poligonal "
                           "devolvida esta incompleta.")}
    finally:
        bm.free()


# ---------------------------------------------------------------------------
# salvar e exportar
# ---------------------------------------------------------------------------

def salva_cena(caminho, permitir_sobrescrever_a_origem=False):
    """Salva no destino combinado. Por padrao RECUSA sobrescrever o arquivo de
    origem: a referencia e explicita em nao sobrescrever a origem ao salvar uma
    previa, e o destino acordado e outro arquivo."""
    origem = bpy.data.filepath
    alvo = os.path.abspath(caminho)
    if origem and os.path.abspath(origem) == alvo and not permitir_sobrescrever_a_origem:
        raise ErroDePrecondicao(
            "o destino e o proprio arquivo de origem (%s). Salvar aqui sobrescreve a "
            "entrada. Informe outro destino, ou passe "
            "permitir_sobrescrever_a_origem=True se for isso mesmo o acordado." % origem)
    pasta = os.path.dirname(alvo)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    # CORRIGIDO depois da terceira revisao: a versao anterior ignorava o retorno de
    # save_as_mainfile. Com um arquivo ja no destino e um salvamento CANCELADO, ela
    # devolveria o tamanho e o hash do arquivo ANTIGO como se fossem da cena atual.
    # E o mesmo padrao ja corrigido na exportacao, deixado aqui.
    antes = (os.path.getsize(alvo), _hash_do_arquivo(alvo)) if os.path.isfile(alvo) else None
    retorno = bpy.ops.wm.save_as_mainfile(filepath=alvo, copy=True)
    estados = sorted(retorno) if hasattr(retorno, "__iter__") else [str(retorno)]
    if "FINISHED" not in estados:
        raise ErroDePrecondicao(
            "o salvamento nao concluiu: o operador devolveu %s. CANCELLED nao levanta "
            "excecao, e sem esta guarda o retorno traria o hash do arquivo anterior."
            % estados)
    if not os.path.isfile(alvo) or os.path.getsize(alvo) == 0:
        raise ErroDePrecondicao(
            "o operador devolveu FINISHED e o arquivo %s nao existe ou esta vazio."
            % alvo)
    depois = (os.path.getsize(alvo), _hash_do_arquivo(alvo))
    if antes is not None and antes == depois:
        raise ErroDePrecondicao(
            "havia um arquivo em %s e ele esta BYTE A BYTE identico depois do "
            "salvamento. Nao ha como distinguir salvamento efetivo de cancelado, "
            "entao o hash nao pode ser vinculado a esta cena. Salve em destino novo."
            % alvo)
    return {"arquivo": alvo, "existe": os.path.isfile(alvo),
            "retorno_do_operador": estados,
            "havia_arquivo_antes": antes is not None,
            "bytes": os.path.getsize(alvo) if os.path.isfile(alvo) else 0,
            "sha256": _hash_do_arquivo(alvo),
            "origem_preservada": origem or None,
            "limite": ("hash de .blend prova integridade do arquivo. Ele NAO separa "
                       "mudanca de geometria de mudanca de camera, selecao ou "
                       "iluminacao. Para geometria, usar a assinatura.")}


def exporta_malha(nome_do_objeto, caminho, formato="stl"):
    """Exporta so o objeto informado. MEDIDO no Blender 5.2.1: o operador de STL e
    `wm.stl_export` com `export_selected_objects`; o nome antigo `export_mesh.stl`
    nao existe mais nesta versao. A tentativa e registrada para que a receita nao
    dependa de adivinhar o nome."""
    obj = _malha(nome_do_objeto)
    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.mode_set(mode="OBJECT")
    alvo = os.path.abspath(caminho)
    pasta = os.path.dirname(alvo)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    tentativas = []
    if formato != "stl":
        raise ErroDePrecondicao("formato %r nao coberto por esta receita" % formato)
    # CORRIGIDO depois da revisao independente. A versao anterior marcava a
    # tentativa como ok apenas porque nao houve excecao, e o operador de exportacao
    # devolve {'CANCELLED'} sem levantar nada — o MESMO defeito que esta receita
    # documenta para transform.translate, deixado dentro da propria exportacao.
    # Pior: se ja existisse um STL antigo no destino, o retorno traria o hash DELE
    # junto com a assinatura da geometria atual, amarrando evidencia a artefato
    # errado. Agora: o destino e removido antes, e o retorno do operador e exigido.
    if os.path.isfile(alvo):
        try:
            os.remove(alvo)
            removeu_anterior = True
        except OSError as e:
            raise ErroDePrecondicao(
                "existe um arquivo em %s e ele nao pode ser removido (%s). Exportar "
                "por cima arriscaria devolver o hash do arquivo ANTIGO como se fosse "
                "o da geometria atual." % (alvo, e))
    else:
        removeu_anterior = False

    for nome, chamada in (
        ("wm.stl_export",
         lambda: bpy.ops.wm.stl_export(filepath=alvo, export_selected_objects=True)),
        ("export_mesh.stl",
         lambda: bpy.ops.export_mesh.stl(filepath=alvo, use_selection=True)),
    ):
        try:
            r = chamada()
            estados = sorted(r) if hasattr(r, "__iter__") else [str(r)]
            if "FINISHED" not in estados:
                tentativas.append({"operador": nome, "ok": False,
                                   "retorno_do_operador": estados,
                                   "motivo": ("o operador nao devolveu FINISHED. "
                                              "CANCELLED nao levanta excecao e nao "
                                              "escreve arquivo.")})
                continue
            tentativas.append({"operador": nome, "ok": True,
                               "retorno_do_operador": estados})
            break
        except Exception as e:
            tentativas.append({"operador": nome, "ok": False,
                               "erro": "%s: %s" % (type(e).__name__, e)})
    if not any(t.get("ok") for t in tentativas):
        raise ErroDePrecondicao(
            "nenhum operador de exportacao concluiu. Tentativas: %s" % tentativas)
    existe = os.path.isfile(alvo)
    if not existe or os.path.getsize(alvo) == 0:
        raise ErroDePrecondicao(
            "o operador devolveu FINISHED e o arquivo %s nao existe ou esta vazio. "
            "Nao ha artefato a vincular a medida." % alvo)
    modificadores = [{"nome": mo.name, "tipo": mo.type, "visivel": mo.show_viewport}
                     for mo in obj.modifiers]
    return {"objeto": obj.name, "arquivo": alvo, "tentativas": tentativas,
            "removeu_arquivo_anterior": removeu_anterior,
            "existe": existe, "bytes": os.path.getsize(alvo) if existe else 0,
            "sha256": _hash_do_arquivo(alvo) if existe else None,
            "assinatura_da_geometria": assinatura(obj.name)["sha256"],
            "modificadores_ativos": modificadores,
            "aviso_de_modificador": (
                None if not modificadores else
                "o objeto tem modificador ativo. A assinatura cobre obj.data e a "
                "matriz de mundo, e NAO o resultado do modificador. O STL exportado "
                "pode nao corresponder a assinatura: aplique o modificador antes, ou "
                "trate a assinatura como parcial."),
            "limite": ("exportacao bem-sucedida NAO prova validade geometrica. "
                       "Conferir o artefato entregue com os verificadores.")}


def _hash_do_arquivo(caminho):
    if not os.path.isfile(caminho):
        return None
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# execucao headless por tarefa
# ---------------------------------------------------------------------------

FUNCOES = {"diagnostico": diagnostico, "assinatura": assinatura,
           "entra_em_edicao": entra_em_edicao, "sai_de_edicao": sai_de_edicao,
           "limpa_selecao": limpa_selecao, "desloca_selecao": desloca_selecao,
           "seleciona_faces_por_caixa_de_mundo": seleciona_faces_por_caixa_de_mundo,
           "le_selecao": le_selecao, "marca_recuperacao": marca_recuperacao,
           "desfaz_e_confere": desfaz_e_confere, "refaz_e_confere": refaz_e_confere,
           "mede_malha": mede_malha, "secao_por_plano": secao_por_plano,
           "contexto_de_historico": contexto_de_historico,
           "confere_versao": confere_versao,
           "volume_de_material_na_caixa": volume_de_material_na_caixa,
           "mede_topo_em_pontos": mede_topo_em_pontos,
           "confere_selecao_capturada": confere_selecao_capturada,
           "limpa_degeneracoes_na_regiao": limpa_degeneracoes_na_regiao,
           "preenche_entre_limites": preenche_entre_limites,
           "captura_regiao_protegida": captura_regiao_protegida,
           "compara_regiao_protegida": compara_regiao_protegida,
           "salva_cena": salva_cena, "exporta_malha": exporta_malha}


def executa_tarefa(tarefa):
    """tarefa = {"saida": <caminho>, "passos": [{"funcao": ..., "args": {...}}, ...]}"""
    resultados = []
    for i, passo in enumerate(tarefa.get("passos", [])):
        nome = passo.get("funcao")
        fn = FUNCOES.get(nome)
        if fn is None:
            resultados.append({"passo": i, "funcao": nome, "estado": "FUNCAO_INEXISTENTE",
                               "disponiveis": sorted(FUNCOES)})
            continue
        try:
            r = fn(**(passo.get("args") or {}))
            resultados.append({"passo": i, "funcao": nome, "estado": "OK", "resultado": r})
        except ErroDePrecondicao as e:
            resultados.append({"passo": i, "funcao": nome, "estado": "PRECONDICAO",
                               "mensagem": str(e)})
        except Exception as e:
            resultados.append({"passo": i, "funcao": nome, "estado": "ERRO",
                               "mensagem": "%s: %s" % (type(e).__name__, e)})
    return resultados


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        print("uso: blender --background --python bl_ferramentas.py -- tarefa.json")
        sys.exit(0)
    tarefa = json.load(open(argv[0], encoding="utf-8"))
    res = executa_tarefa(tarefa)
    saida = tarefa.get("saida")
    texto = json.dumps({"versao_ferramentas": VERSAO,
                        "versao_blender": bpy.app.version_string,
                        "resultados": res}, ensure_ascii=False, indent=1)
    if saida:
        os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
        open(saida, "w", encoding="utf-8").write(texto)
    else:
        print(texto)
