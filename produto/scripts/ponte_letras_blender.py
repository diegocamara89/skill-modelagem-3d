"""Lado BLENDER da ponte das letras. Executado dentro da sessão viva via execute_code (MCP).

A cena de trabalho do agente chama-se CENA (abaixo); carregar/atualizar só mexem nela. letras/tracos/apagar e os
verbos operam na cena que está na janela do operador, em TODAS as malhas em Edit Mode.
Não usa bpy.ops para geometria (contexto do MCP não é confiável): lê STL binário com
numpy, cria a malha com from_pydata, grupos de vértices e atributo de face por API de dados.
Espera CONFIG (dict) definido antes do exec.
"""
import bpy
import bmesh
import json
import sys
import numpy as np

sys.path.insert(0, CONFIG["pasta"])
import feicoes as F

CENA = "TRABALHO_AGENTE"
MARCA = "LETRAS_RESULTADO="


def _le_stl(caminho):
    with open(caminho, "rb") as f:
        f.read(80)
        n = int(np.frombuffer(f.read(4), dtype="<u4")[0])
        dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        dados = np.frombuffer(f.read(n * 50), dtype=dt)
    tri = dados["v"].astype(np.float64).reshape(-1, 3)
    chave = np.round(tri, 5)
    _, idx, inv = np.unique(chave, axis=0, return_index=True, return_inverse=True)
    verts = tri[idx]
    faces = inv.reshape(-1, 3)
    return verts, faces


def _cena():
    sc = bpy.data.scenes.get(CENA)
    if sc is None:
        sc = bpy.data.scenes.new(CENA)
        sc.unit_settings.system = "METRIC"
        sc.unit_settings.scale_length = 0.001
        sc.unit_settings.length_unit = "MILLIMETERS"
    return sc


def _janela():
    wm = bpy.data.window_managers[0]
    return wm.windows[0] if wm.windows else None


def _mostra_cena(sc):
    win = _janela()
    if win is not None and win.scene != sc:
        win.scene = sc
    return win


def _redesenha():
    win = _janela()
    if win is None:
        return 0
    n = 0
    for area in win.screen.areas:
        area.tag_redraw()
        n += 1
    return n


def _enquadra(obj):
    win = _janela()
    if win is None:
        return False
    for area in win.screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region is None:
            continue
        try:
            with bpy.context.temp_override(window=win, area=area, region=region, scene=bpy.data.scenes[CENA]):
                bpy.ops.view3d.view_all(center=True)
            return True
        except Exception:
            return False
    return False


def _malha_de(stl, nome):
    verts, faces = _le_stl(stl)
    me = bpy.data.meshes.new(nome)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.validate(verbose=False)
    me.update()
    return me, verts, faces


def _rotula(obj, me, verts, faces, fe):
    normais = np.array([p.normal[:] for p in me.polygons])
    centros = np.array([p.center[:] for p in me.polygons])
    rot = F.classifica_faces(centros, normais, fe)
    att = me.attributes.get("rasgo") or me.attributes.new("rasgo", "INT", "FACE")
    att.data.foreach_set("value", rot.astype(np.int32).tolist())
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    resumo = {}
    for k, f in enumerate(fe):
        idx = np.unique(faces[rot == k].ravel()).tolist()
        vg = obj.vertex_groups.new(name=f["nome"])
        if idx:
            vg.add(idx, 1.0, "REPLACE")
        resumo[f["nome"]] = {"faces": int((rot == k).sum()), "vertices": len(idx)}
    obj["feicoes"] = json.dumps(fe, ensure_ascii=False)
    return resumo


def carregar(stl, feicoes_json, nome):
    fe = F.carrega(feicoes_json)["feicoes"]
    sc = _cena()
    obj = sc.objects.get(nome) or bpy.data.objects.get(nome)
    me, verts, faces = _malha_de(stl, f"{nome}.malha")
    if obj is None:
        obj = bpy.data.objects.new(nome, me)
        sc.collection.objects.link(obj)
    else:
        obj.data = me
    obj["fonte_stl"] = stl
    resumo = _rotula(obj, me, verts, faces, fe)
    win = _mostra_cena(sc)
    if win is not None:
        sc.view_layers[0].objects.active = obj
    enquadrou = _enquadra(obj)
    return {"estado": "CARREGADO", "objeto": obj.name, "vertices": len(me.vertices), "faces": len(me.polygons),
            "grupos": resumo, "cena_na_janela": win.scene.name if win else None, "enquadrou": enquadrou,
            "redesenho_pedido": _redesenha()}


def identificar(nome):
    obj = bpy.data.objects.get(nome)
    if obj is None:
        return {"estado": "RECUSADO", "motivo": f"objeto {nome} não existe"}
    if obj.mode != "EDIT":
        return {"estado": "SEM_SELECAO_VIVA", "modo": obj.mode, "motivo": "objeto não está em Edit Mode"}
    fe = json.loads(obj["feicoes"])
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    camada = bm.faces.layers.int.get("rasgo")
    if camada is None:
        return {"estado": "RECUSADO", "motivo": "malha sem atributo 'rasgo'"}
    sel = [f for f in bm.faces if f.select]
    rot = [f[camada] for f in sel]
    out = F.identifica(rot, fe)
    out["faces_selecionadas"] = len(sel)
    return out


def expandir(nome):
    """Identifica pela seleção do usuário e, se for uma feição só, seleciona a feição inteira."""
    r = identificar(nome)
    if r.get("estado") != "IDENTIFICADO":
        return r
    obj = bpy.data.objects[nome]
    fe = json.loads(obj["feicoes"])
    k = [f["nome"] for f in fe].index(r["feicao"])
    bm = bmesh.from_edit_mesh(obj.data)
    camada = bm.faces.layers.int["rasgo"]
    n = 0
    for f in bm.faces:
        sel = f[camada] == k
        f.select = sel
        n += sel
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    r.update(estado="FEICAO_ACESA", faces_da_feicao=n, redesenho_pedido=_redesenha())
    return r


def _alvo(nome):
    win = _janela()
    if nome:
        o = bpy.data.objects.get(nome)
        if o is not None:
            return o
    if win is not None:
        for o in win.scene.objects:
            if o.type == "MESH" and o.mode == "EDIT":
                return o
    return None


def _em_edicao():
    win = _janela()
    sc = win.scene if win else bpy.data.scenes[CENA]
    return sc, sorted([o for o in sc.objects if o.type == "MESH" and o.mode == "EDIT"], key=lambda o: o.name)


def letras(nome=None):
    """Lê a ORDEM dos cliques (select_history) em TODOS os objetos em edição: A, B, C..."""
    sc, objs = _em_edicao()
    if not objs:
        return {"estado": "SEM_SELECAO_VIVA", "cena": sc.name, "motivo": "nenhuma malha em Edit Mode"}
    out, i, total = [], 0, 0
    for obj in objs:
        fe = json.loads(obj["feicoes"]) if "feicoes" in obj else []
        nomes = [f["nome"] for f in fe]
        bm = bmesh.from_edit_mesh(obj.data)
        camada = bm.faces.layers.int.get("rasgo")
        mw = obj.matrix_world
        total += sum(1 for f in bm.faces if f.select)
        for e in [x for x in bm.select_history if x.is_valid and x.select]:
            if i >= 26:
                break
            if isinstance(e, bmesh.types.BMFace):
                tipo, c = "face", mw @ e.calc_center_median()
                k = e[camada] if camada else -1
                extra = {"normal": [round(v, 3) for v in (mw.to_3x3() @ e.normal)], "area_mm2": round(e.calc_area(), 3)}
            elif isinstance(e, bmesh.types.BMEdge):
                tipo, c = "aresta", mw @ ((e.verts[0].co + e.verts[1].co) / 2)
                ks = {f[camada] for f in e.link_faces} if camada else set()
                k = ks.pop() if len(ks) == 1 else -1
                extra = {"comprimento_mm": round(e.calc_length(), 3)}
            else:
                tipo, c = "vertice", mw @ e.co
                ks = {f[camada] for f in e.link_faces} if camada else set()
                k = ks.pop() if len(ks) == 1 else -1
                extra = {}
            out.append({"letra": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i], "objeto": obj.name, "tipo": tipo, "indice": e.index,
                        "feicao": nomes[k] if 0 <= k < len(nomes) else None,
                        "centro_mm": [round(v, 3) for v in c], **extra})
            i += 1
    return {"estado": "OK", "cena": sc.name, "objetos_em_edicao": [o.name for o in objs], "letras": out,
            "faces_selecionadas_total": total,
            "nota": "letras só para elementos CLICADOS; seleção por caixa entra no total sem letra"}


def _kd_cena(sc):
    import mathutils
    itens = []
    for o in sc.objects:
        if o.type != "MESH" or not o.visible_get():
            continue
        if o.mode == "EDIT":
            o.update_from_editmode()
        me = o.data
        rot = np.array([d.value for d in me.attributes["rasgo"].data]) if "rasgo" in me.attributes else None
        nomes = [f["nome"] for f in json.loads(o["feicoes"])] if "feicoes" in o else []
        for p in me.polygons:
            k = int(rot[p.index]) if rot is not None else -1
            itens.append((o.matrix_world @ p.center, o.name, nomes[k] if 0 <= k < len(nomes) else None))
    kd = mathutils.kdtree.KDTree(len(itens))
    for i, (co, _, _) in enumerate(itens):
        kd.insert(co, i)
    kd.balance()
    return kd, itens


def tracos(nome=None, limpar=False):
    """Lê os traços da ferramenta Anotar (grudados na superfície) e diz o que cada um tocou, em qualquer peça da cena."""
    win = _janela()
    sc = win.scene if win else bpy.data.scenes[CENA]
    an = sc.annotation
    if an is None:
        return {"estado": "SEM_TRACOS", "cena": sc.name, "motivo": "nenhuma anotação na cena"}
    kd, itens = _kd_cena(sc)

    def perto(co):
        _, idx, dist = kd.find(co)
        _, objeto, feicao = itens[idx]
        return objeto, feicao, round(dist, 2)
    out = []
    for cam in an.layers:
        for fr in cam.frames:
            for st in fr.strokes:
                P = np.array([p.co[:] for p in st.points], dtype=float)
                if len(P) < 2:
                    continue
                seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
                comp = float(seg.sum())
                fecho = float(np.linalg.norm(P[0] - P[-1]))
                fechado = fecho < max(3.0, 0.15 * comp)
                passo = max(1, len(P) // 40)
                tocou = {}
                for co in P[::passo]:
                    o, f, d = perto(co)
                    if d <= 3.0:
                        chave = f"{o}" + (f"/{f}" if f else "")
                        tocou[chave] = tocou.get(chave, 0) + 1
                oa, fa, da = perto(P[0]); ob, fb, db = perto(P[-1])
                out.append({"camada": cam.info, "pontos": len(P), "comprimento_mm": round(comp, 1),
                            "forma": "laco_fechado" if fechado else "linha",
                            "inicio": {"mm": [round(x, 2) for x in P[0]], "objeto": oa, "feicao": fa, "dist_superficie": da},
                            "fim": {"mm": [round(x, 2) for x in P[-1]], "objeto": ob, "feicao": fb, "dist_superficie": db},
                            "centro_mm": [round(x, 2) for x in P.mean(axis=0)],
                            "caixa_mm": [round(x, 1) for x in (P.max(axis=0) - P.min(axis=0))],
                            "pecas_tocadas": tocou})
    r = {"estado": "OK", "cena": sc.name, "tracos": out}
    if limpar:
        n = 0
        for cam in an.layers:
            for fr in cam.frames:
                for st in list(fr.strokes):
                    fr.strokes.remove(st); n += 1
        r["apagados"] = n
        _redesenha()
    return r


def apagar_selecao(nome=None):
    """Apaga as faces selecionadas (em todos os objetos em edição) e fecha o furo com triângulos.
    Guarda a malha anterior. Se não fechar limpo, restaura e recusa."""
    sc, objs = _em_edicao()
    out = {"estado": "OK", "cena": sc.name, "objetos": {}}
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        sel = [f for f in bm.faces if f.select]
        if not sel:
            continue
        backup = bm.copy()
        antes_abertas = {e.index for e in bm.edges if e.is_boundary}
        n_apagadas = len(sel)
        bmesh.ops.delete(bm, geom=sel, context="FACES")
        bm.edges.ensure_lookup_table()
        novas = [e for e in bm.edges if e.is_boundary]
        # arestas de borda que ja existiam antes nao sao furo meu: identificar por geometria
        antes_geo = set()
        backup.edges.ensure_lookup_table()
        for i in antes_abertas:
            e = backup.edges[i]
            antes_geo.add(tuple(sorted((tuple(round(c, 5) for c in e.verts[0].co), tuple(round(c, 5) for c in e.verts[1].co)))))
        furo = [e for e in novas if tuple(sorted((tuple(round(c, 5) for c in e.verts[0].co), tuple(round(c, 5) for c in e.verts[1].co)))) not in antes_geo]
        preenchidas = 0
        if furo:
            r = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=furo)
            preenchidas = len([g for g in r.get("geom", []) if isinstance(g, bmesh.types.BMFace)])
        bm.normal_update()
        restam = [e for e in bm.edges if e.is_boundary]
        restam_geo = {tuple(sorted((tuple(round(c, 5) for c in e.verts[0].co), tuple(round(c, 5) for c in e.verts[1].co)))) for e in restam}
        furo_aberto = len(restam_geo - antes_geo)
        nao_manifold = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        if furo_aberto or (nao_manifold and preenchidas):
            bm.clear(); bm.from_mesh(backup_mesh := obj.data) if False else None
            # restaurar a partir do backup bmesh
            bm.clear()
            backup_tmp = bpy.data.meshes.new("_tmp_restaura"); backup.to_mesh(backup_tmp)
            bm.from_mesh(backup_tmp); bpy.data.meshes.remove(backup_tmp)
            bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
            out["objetos"][obj.name] = {"estado": "RECUSADO_RESTAURADO", "faces_apagadas_tentadas": n_apagadas,
                                        "arestas_de_furo_abertas": furo_aberto, "nao_manifold": nao_manifold,
                                        "motivo": "o furo não fechou limpo; geometria restaurada"}
            out["estado"] = "PARCIAL"
            continue
        guarda = bpy.data.meshes.new(f"{obj.name}.ANTES_APAGAR"); backup.to_mesh(guarda); guarda.use_fake_user = True
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
        obj.update_from_editmode()
        me = obj.data
        out["objetos"][obj.name] = {"estado": "APAGADO_E_FECHADO", "faces_apagadas": n_apagadas, "arestas_do_furo": len(furo),
                                    "faces_de_fechamento": preenchidas, "nao_manifold_restante": nao_manifold,
                                    "backup": guarda.name, "faces_agora": len(me.polygons)}
        backup.free()
    if not out["objetos"]:
        out.update(estado="SEM_SELECAO", motivo="nenhuma face selecionada nos objetos em edição")
    out["redesenho_pedido"] = _redesenha()
    return out


# ---------------------------------------------------------------- verbos ligados às letras
def _fator_mm(sc, obj):
    """Quantas unidades do Blender valem 1 mm. Cena em mm (scale 0.001) -> 1. Cena em metros com peça
    de dezenas de unidades -> assume 1 unidade = 1 mm e declara."""
    u = sc.unit_settings
    if u.system == "METRIC" and abs(u.scale_length - 0.001) < 1e-9:
        return 1.0, "cena em mm"
    dim = max(obj.dimensions) if obj else 0
    if u.scale_length == 1.0 and dim > 0.5:
        return 1.0, "cena em metros mas peça com dezenas de unidades: assumido 1 unidade = 1 mm"
    return 1.0 / (1000.0 * u.scale_length), f"convertido pela escala da cena ({u.scale_length})"


def _guarda(obj, bm):
    g = bpy.data.meshes.new(f"{obj.name}.ANTES_VERBO"); bm.to_mesh(g); g.use_fake_user = True
    return g


def _restaura(obj, bm, guarda):
    bm.clear(); bm.from_mesh(guarda)
    bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)


def _saude(bm):
    return {"arestas_borda": sum(1 for e in bm.edges if e.is_boundary),
            "arestas_nao_manifold": sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary),
            "faces": len(bm.faces), "vertices": len(bm.verts)}


def _hash_protegido(bm, sel_verts):
    import hashlib
    ids = set(v.index for v in sel_verts)
    h = hashlib.sha256()
    for v in bm.verts:
        if v.index not in ids:
            h.update(("%.6f,%.6f,%.6f;" % tuple(v.co)).encode())
    return h.hexdigest()[:16]


def _piorou(antes, depois):
    return depois["arestas_borda"] > antes["arestas_borda"] or depois["arestas_nao_manifold"] > antes["arestas_nao_manifold"]


def _alvos():
    sc, objs = _em_edicao()
    alvos = []
    for o in objs:
        bm = bmesh.from_edit_mesh(o.data)
        if any(f.select for f in bm.faces):
            alvos.append((o, bm))
    return sc, alvos


def _executa_verbo(nome_verbo, corpo):
    """corpo(obj, bm, sel_faces, fator) -> dict com medidas. Aplica guarda, saúde antes/depois, restaura se piorar."""
    sc, alvos = _alvos()
    if not alvos:
        return {"estado": "SEM_SELECAO", "motivo": "nenhuma face selecionada em objeto em edição"}
    out = {"estado": "OK", "verbo": nome_verbo, "cena": sc.name, "objetos": {}}
    for obj, bm in alvos:
        bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.verts.index_update()
        sel = [f for f in bm.faces if f.select]
        sel_verts = {v for f in sel for v in f.verts}
        fator, nota = _fator_mm(sc, obj)
        antes = _saude(bm); hp = _hash_protegido(bm, sel_verts)
        guarda = _guarda(obj, bm)
        try:
            med = corpo(obj, bm, sel, fator)
        except Exception as e:
            _restaura(obj, bm, guarda)
            out["objetos"][obj.name] = {"estado": "FALHA_RESTAURADA", "erro": repr(e), "backup": guarda.name}; out["estado"] = "PARCIAL"
            continue
        bm.normal_update()
        depois = _saude(bm)
        if _piorou(antes, depois):
            _restaura(obj, bm, guarda)
            out["objetos"][obj.name] = {"estado": "RECUSADO_RESTAURADO", "motivo": "a malha ficou com borda ou aresta não-manifold a mais", "antes": antes, "depois": depois, "backup": guarda.name}
            out["estado"] = "PARCIAL"
            continue
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
        obj.update_from_editmode()
        bm2 = bmesh.from_edit_mesh(obj.data); bm2.verts.ensure_lookup_table(); bm2.verts.index_update()
        sel2 = {v for f in bm2.faces if f.select for v in f.verts}
        out["objetos"][obj.name] = {"estado": "APLICADO", "faces_selecionadas": len(sel), "unidade": nota, **med,
                                    "saude_antes": antes, "saude_depois": depois, "backup": guarda.name,
                                    "nota": "hash do protegido comparado só quando o conjunto de vértices não muda"}
        if depois["vertices"] == antes["vertices"]:
            out["objetos"][obj.name]["protegido_igual"] = (_hash_protegido(bm2, sel2) == hp)
    out["redesenho_pedido"] = _redesenha()
    return out


def mover(eixo="Z", mm=1.0, nome=None):
    import mathutils
    def corpo(obj, bm, sel, fator):
        d = mathutils.Vector((0, 0, 0)); d["XYZ".index(eixo.upper())] = mm * fator
        d_local = obj.matrix_world.to_3x3().inverted() @ d
        vs = {v for f in sel for v in f.verts}
        for v in vs: v.co += d_local
        return {"eixo_global": eixo.upper(), "distancia_mm": mm, "vertices_movidos": len(vs)}
    return _executa_verbo("mover", corpo)


def extrudar(mm=1.0, nome=None):
    import mathutils
    def corpo(obj, bm, sel, fator):
        n = mathutils.Vector((0, 0, 0))
        for f in sel: n += f.normal
        if n.length < 1e-9: raise ValueError("normais da seleção se anulam; escolha faces de um lado só")
        n.normalize()
        r = bmesh.ops.extrude_face_region(bm, geom=sel)
        novos = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
        for v in novos: v.co += n * (mm * fator)
        # as faces de origem ficaram no interior: apagar só elas (como o operador do Blender faz)
        bmesh.ops.delete(bm, geom=sel, context="FACES_ONLY")
        for g in r["geom"]:
            if isinstance(g, bmesh.types.BMFace): g.select = True
        bm.select_flush_mode()
        return {"distancia_mm": mm, "normal_local": [round(x, 3) for x in n], "vertices_novos": len(novos)}
    return _executa_verbo("extrudar", corpo)


def preencher(modo="contorno", nome=None):
    def corpo(obj, bm, sel, fator):
        # seleção de faces é indicação; o furo são as arestas de borda tocadas pela seleção (ou todas as de borda selecionadas)
        bordas = [e for e in bm.edges if e.select and e.is_boundary]
        if not bordas:
            bordas = [e for f in sel for e in f.edges if e.is_boundary]
        bordas = list({e.index: e for e in bordas}.values())
        if not bordas: raise ValueError("nenhuma aresta de borda na seleção; não há furo para fechar")
        if modo == "ponte":
            r = bmesh.ops.bridge_loops(bm, edges=bordas)
            criadas = len(r.get("faces", []))
        else:
            r = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bordas)
            criadas = len([g for g in r.get("geom", []) if isinstance(g, bmesh.types.BMFace)])
        if criadas == 0: raise ValueError("nada foi criado; o contorno não fecha ou não são dois laços")
        return {"modo": modo, "arestas_de_borda_usadas": len(bordas), "faces_criadas": criadas}
    return _executa_verbo("preencher", corpo)


def arredondar(raio_mm=1.0, segmentos=4, nome=None):
    def corpo(obj, bm, sel, fator):
        arestas = [e for e in bm.edges if e.select]
        if not arestas:
            # arestas compartilhadas entre faces selecionadas e não selecionadas = quinas da região
            arestas = [e for e in bm.edges if any(f.select for f in e.link_faces) and not all(f.select for f in e.link_faces)]
        if not arestas: raise ValueError("nenhuma aresta para arredondar")
        r = bmesh.ops.bevel(bm, geom=arestas, offset=raio_mm * fator, offset_type="OFFSET", segments=int(segmentos), profile=0.5, affect="EDGES", clamp_overlap=True)
        return {"raio_mm": raio_mm, "segmentos": int(segmentos), "arestas": len(arestas), "faces_criadas": len(r.get("faces", []))}
    return _executa_verbo("arredondar", corpo)


def desfazer_verbo(nome=None):
    """Restaura a última guarda .ANTES_VERBO de cada objeto em edição."""
    sc, objs = _em_edicao(); out = {"estado": "OK", "objetos": {}}
    for o in objs:
        g = bpy.data.meshes.get(f"{o.name}.ANTES_VERBO") or bpy.data.meshes.get(f"{o.name}.ANTES_APAGAR")
        if g is None: continue
        bm = bmesh.from_edit_mesh(o.data); _restaura(o, bm, g); o.update_from_editmode()
        out["objetos"][o.name] = {"estado": "RESTAURADO_DE", "backup": g.name}
    if not out["objetos"]: out.update(estado="SEM_BACKUP")
    out["redesenho_pedido"] = _redesenha(); return out


def atualizar(stl, feicoes_json, nome):
    obj = bpy.data.objects.get(nome)
    if obj is None:
        return {"estado": "RECUSADO", "motivo": f"objeto {nome} não existe"}
    if obj.mode != "OBJECT":
        win = _janela()
        saiu = False
        if win is not None:
            for area in win.screen.areas:
                if area.type != "VIEW_3D":
                    continue
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                try:
                    with bpy.context.temp_override(window=win, area=area, region=region,
                                                   active_object=obj, object=obj, selected_objects=[obj],
                                                   scene=bpy.data.scenes[CENA]):
                        bpy.ops.object.mode_set(mode="OBJECT")
                    saiu = True
                    break
                except Exception as e:
                    erro = str(e)
        if not saiu:
            return {"estado": "PRECISA_OBJECT_MODE", "motivo": "não consegui sair do Edit Mode pelo MCP; peça Tab ao usuário", "erro": erro if 'erro' in dir() else None}
    fe = F.carrega(feicoes_json)["feicoes"]
    antiga = obj.data
    me, verts, faces = _malha_de(stl, f"{nome}.malha")
    obj.data = me
    antiga.name = f"{nome}.anterior"
    antiga.use_fake_user = True
    obj["fonte_stl"] = stl
    resumo = _rotula(obj, me, verts, faces, fe)
    return {"estado": "ATUALIZADO", "objeto": obj.name, "vertices": len(me.vertices), "faces": len(me.polygons),
            "malha_anterior_guardada": antiga.name, "grupos": resumo, "redesenho_pedido": _redesenha()}


def salvar_copia(caminho):
    sc = bpy.data.scenes.get(CENA)
    if sc is None:
        return {"estado": "RECUSADO", "motivo": "cena POC não existe"}
    bpy.data.libraries.write(caminho, {sc}, fake_user=True)
    import os
    return {"estado": "SALVO", "caminho": caminho, "bytes": os.path.getsize(caminho),
            "arquivo_do_usuario": bpy.data.filepath, "arquivo_do_usuario_alterado": bpy.data.is_dirty}


def exportar_stl(nome, caminho):
    obj = bpy.data.objects.get(nome)
    me = obj.data
    if obj.mode == "EDIT":
        obj.update_from_editmode()
    me.calc_loop_triangles()
    tris = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int64)
    V = np.array([v.co[:] for v in me.vertices], dtype=np.float64)
    N = np.array([t.normal[:] for t in me.loop_triangles], dtype=np.float32)
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    dados = np.zeros(len(tris), dtype=dt)
    dados["n"] = N
    dados["v"] = V[tris].astype(np.float32)
    with open(caminho, "wb") as f:
        f.write(b"poc_rasgos".ljust(80, b"\0"))
        f.write(np.array([len(tris)], dtype="<u4").tobytes())
        f.write(dados.tobytes())
    return {"estado": "EXPORTADO", "caminho": caminho, "triangulos": int(len(tris))}


def estado(nome):
    obj = bpy.data.objects.get(nome)
    win = _janela()
    return {"estado": "OK", "objeto_existe": obj is not None, "modo": obj.mode if obj else None,
            "cena_na_janela": win.scene.name if win else None, "arquivo_do_usuario": bpy.data.filepath,
            "alteracoes_nao_salvas": bpy.data.is_dirty}


ACOES = {"carregar": carregar, "identificar": identificar, "expandir": expandir, "letras": letras, "tracos": tracos, "apagar": apagar_selecao, "mover": mover, "extrudar": extrudar, "preencher": preencher, "arredondar": arredondar, "desfazer": desfazer_verbo, "atualizar": atualizar,
         "salvar_copia": salvar_copia, "exportar_stl": exportar_stl, "estado": estado}

try:
    _r = ACOES[CONFIG["acao"]](**CONFIG.get("args", {}))
except Exception as _e:
    import traceback
    _r = {"estado": "EXCECAO", "erro": repr(_e), "traceback": traceback.format_exc()}
print(MARCA + json.dumps(_r, ensure_ascii=False, default=str))
