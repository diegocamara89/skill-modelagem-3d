"""find_datums.py - candidatos a datum numa geometria de referencia.

Uso:
  python find_datums.py --malha peca.stl [--top 8] [--tol-ang 1.5] [--tol-plano 0.05] [--json out.json]
  python find_datums.py --sem-fonte [--json out.json]

O QUE FAZ: agrupa facetas COPLANARES e CONECTADAS em regioes planas; mede area,
normal media ponderada por area, centroide, residuo de planaridade e inclinacao
contra os eixos; devolve as maiores regioes como CANDIDATOS a datum.

O QUE NAO FAZ: nao decide qual regiao e a interface de acoplamento. Essa decisao
exige confirmacao do proprietario da peca ou uma segunda medicao independente.
"""
import argparse, hashlib, json, sys
import numpy as np

EIXOS = {"X+": (1, 0, 0), "X-": (-1, 0, 0), "Y+": (0, 1, 0),
         "Y-": (0, -1, 0), "Z+": (0, 0, 1), "Z-": (0, 0, -1)}

ANTIPADRAO = (
    "A caixa envolvente NAO e datum. Alinhar por caixa envolvente, por centroide de volume "
    "ou pela maior dimensao descarta a orientacao da face de referencia. O datum e uma FACE "
    "(ou eixo/furo) com normal propria. Se ha regiao plana grande nao alinhada a eixo, o "
    "alinhamento axial NAO reproduz a orientacao dessa regiao. Isso e um fato geometrico; "
    "nada aqui diz que aquela regiao seja a interface de acoplamento, porque area e "
    "inclinacao nao estabelecem funcao.")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ang(u, v):
    c = float(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1))
    return float(np.degrees(np.arccos(c)))


def agrupa_coplanar(normais, areas, centros, tol_ang, tol_plano):
    """Clusteriza facetas por (direcao da normal, offset do plano). Greedy por area decrescente."""
    d = np.einsum("ij,ij->i", normais, centros)
    ordem = np.argsort(-areas)
    cos_tol = np.cos(np.radians(tol_ang))
    sem_n, sem_d = [], []
    rotulo = np.full(len(areas), -1, np.int64)
    for i in ordem:
        n, di = normais[i], d[i]
        achou = -1
        for k in range(len(sem_n)):
            if float(np.dot(n, sem_n[k])) >= cos_tol and abs(di - sem_d[k]) <= tol_plano:
                achou = k
                break
        if achou < 0:
            sem_n.append(n)
            sem_d.append(di)
            achou = len(sem_n) - 1
        rotulo[i] = achou
    return rotulo


def componentes(adj, rotulo, n_faces):
    """Separa cada cluster coplanar em regioes CONECTADAS: dois patches paralelos nao sao um datum."""
    pai = np.arange(n_faces)

    def raiz(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a

    for a, b in adj:
        if rotulo[a] == rotulo[b]:
            ra, rb = raiz(a), raiz(b)
            if ra != rb:
                pai[ra] = rb
    return np.array([raiz(i) for i in range(n_faces)])


def descreve(malha, idx, tol_ang):
    A = malha.area_faces[idx]
    area = float(A.sum())
    if area <= 0:
        return None
    n = (malha.face_normals[idx] * A[:, None]).sum(0)
    nn = np.linalg.norm(n)
    if nn <= 0:
        return None
    n = n / nn
    c = (malha.triangles_center[idx] * A[:, None]).sum(0) / area
    V = malha.triangles[idx].reshape(-1, 3)
    resid = float(np.abs((V - c) @ n).max())
    a1 = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(n, a1)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    P = np.column_stack([(V - c) @ e1, (V - c) @ e2])
    ext = (float(P[:, 0].max() - P[:, 0].min()), float(P[:, 1].max() - P[:, 1].min()))
    angs = {k: round(ang(n, np.array(v, float)), 3) for k, v in EIXOS.items()}
    eixo = min(angs, key=angs.get)
    a_min = angs[eixo]
    return {
        "area_mm2": round(area, 3),
        "n_facetas": int(len(idx)),
        "normal": [round(float(x), 6) for x in n],
        "centroide_mm": [round(float(x), 4) for x in c],
        "residuo_planaridade_mm": round(resid, 5),
        "extensao_no_plano_mm": [round(ext[0], 3), round(ext[1], 3)],
        "eixo_mais_proximo": eixo,
        "angulo_com_esse_eixo_deg": round(a_min, 3),
        "alinhada_a_eixo": bool(a_min <= tol_ang),
        "angulos_por_eixo_deg": angs,
    }


def com_fonte(caminho, top, tol_ang, tol_plano, area_min):
    import trimesh
    m = trimesh.load(caminho, force="mesh", process=False)
    if not hasattr(m, "faces"):
        raise SystemExit("nao e uma malha unica: " + caminho)
    # STL nao compartilha vertices: sem soldar, face_adjacency fica vazia e cada faceta
    # viraria uma regiao. Soldar vertices coincidentes NAO move geometria.
    v_antes = int(len(m.vertices))
    m.merge_vertices()
    v_depois = int(len(m.vertices))
    rot = agrupa_coplanar(m.face_normals, m.area_faces, m.triangles_center, tol_ang, tol_plano)
    comp = componentes(m.face_adjacency, rot, len(m.faces))
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa. O residuo de planaridade era
    # MEDIDO e nao entrava na decisao: a regiao entrava so pela area minima. Faces grandes
    # levemente dobradas, com offsets parecidos, viravam "regiao plana" com residuo acima da
    # tolerancia. Agora o residuo do agrupamento e comparado com tol_plano, e o que nao
    # passa sai da lista de candidatos e vai para uma lista propria.
    regioes, quase_planas = [], []
    for r in np.unique(comp):
        idx = np.nonzero(comp == r)[0]
        d = descreve(m, idx, tol_ang)
        if d is None or d["area_mm2"] < area_min:
            continue
        d["tol_planaridade_mm"] = tol_plano
        d["plana"] = bool(d["residuo_planaridade_mm"] <= tol_plano)
        (regioes if d["plana"] else quase_planas).append(d)
    quase_planas.sort(key=lambda x: -x["area_mm2"])
    regioes.sort(key=lambda x: -x["area_mm2"])
    inclinadas = [r for r in regioes if not r["alinhada_a_eixo"]]
    bb = m.bounds
    return {
        "modo": "com_fonte",
        "arquivo": caminho,
        "sha256": sha256(caminho),
        "unidade_assumida": "mm (STL nao carrega unidade; confirme antes de usar cota)",
        "malha": {
            "triangulos": int(len(m.faces)),
            "vertices_antes_de_soldar": v_antes,
            "vertices_depois_de_soldar": v_depois,
            "fechada_watertight": bool(m.is_watertight),
            "volume_mm3": round(float(m.volume), 3) if m.is_watertight else None,
            "caixa_mm": [round(float(x), 4) for x in (bb[1] - bb[0])],
            "aviso_volume": None if m.is_watertight else
                "malha nao fechada: volume e inercia nao sao confiaveis",
        },
        "parametros": {"tol_ang_deg": tol_ang, "tol_plano_mm": tol_plano, "area_min_mm2": area_min},
        "aviso_antipadrao": ANTIPADRAO,
        "n_regioes_planas": len(regioes),
        "n_regioes_reprovadas_por_planaridade": len(quase_planas),
        "regioes_reprovadas_por_planaridade": quase_planas[:5],
        "nota_planaridade": (
            "regiao so entra em datums_candidatos se o residuo de todos os vertices contra "
            "o plano medio ficar dentro de tol_plano. A tolerancia usada no agrupamento "
            "compara offsets de faces vizinhas e NAO garante isso."),
        "n_regioes_inclinadas": len(inclinadas),
        "datums_candidatos": regioes[:top],
        "maior_regiao_inclinada": inclinadas[0] if inclinadas else None,
        # CORRIGIDO 07/09/2026 depois de revisao externa. A versao anterior recomendava
        # tratar a maior regiao inclinada como candidata primaria a face de acoplamento.
        # Inclinacao e area NAO estabelecem funcao: pode ser face externa, chanfro, ou so
        # a orientacao em que o arquivo foi salvo. Este script mede geometria; a escolha
        # da referencia funcional vem dos requisitos e das evidencias.
        "leitura": (
            "Existe regiao plana de area relevante nao alinhada a nenhum eixo. Isso significa que "
            "alinhamento por eixo NAO reproduz a orientacao dessa regiao. Nao significa que essa "
            "regiao seja a interface de acoplamento." if inclinadas else
            "Nenhuma regiao plana inclinada acima da tolerancia. Isso nao identifica nenhuma face "
            "como interface: so diz que as regiao planas encontradas sao paralelas aos eixos."),
        "o_que_isto_nao_diz": (
            "Nada aqui atribui funcao a nenhuma face. Area, inclinacao e planaridade sao "
            "propriedades geometricas. Qual regiao e assento, apoio, folga ou acabamento e uma "
            "questao de requisito, respondida por quem conhece a peca ou por evidencia "
            "independente, nunca por ranking de area."),
        "decisao_pendente": (
            "Qual destas regioes e a interface de acoplamento e uma decisao NAO resolvida por este "
            "script. Confirme com o proprietario da peca ou com uma segunda medicao independente "
            "antes de construir qualquer geometria em cima."),
    }


def sem_fonte():
    return {
        "modo": "do_zero",
        "datums_candidatos": [],
        "aviso_antipadrao": ANTIPADRAO,
        "leitura": "Nao ha peca-fonte, logo nao ha datum de referencia externo a extrair.",
        "datums_a_estabelecer": [
            {"datum": "plano da mesa", "origem": "restricao de fabricacao",
             "nota": "Z=0. Considere fabricacao desde o inicio, quando a peca for fabricada; a "
                     "orientacao pode mudar ao longo do projeto e nao precisa ser cravada agora."},
            {"datum": "direcao de impressao / anisotropia", "origem": "restricao de fabricacao",
             "nota": "a uniao entre camadas e mais fraca que o material no plano. Em PLA e ABS "
                     "ensaiados na literatura a razao ficou em torno de metade, mas isso e do "
                     "material e do ensaio, nao constante universal. Regra robusta: a carga "
                     "principal deve correr AO LONGO das camadas."},
            {"datum": "envelope da maquina", "origem": "restricao de fabricacao",
             "nota": "se a peca estoura o envelope ela nasce dividida; onde cortar e decisao "
                     "estrutural, nao geometrica."},
            {"datum": "gravidade / face de apoio em uso", "origem": "requisito de uso"},
            {"datum": "faces de acoplamento com pecas compradas ou impressas em separado",
             "origem": "requisito de montagem",
             "nota": "cada uma exige folga calibrada por maquina+material, nao constante de tabela."},
        ],
        "decisao_pendente": (
            "Estabeleca os datums acima a partir dos REQUISITOS antes de desenhar qualquer geometria. "
            "Sem datum declarado nao existe verificacao possivel depois."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--malha")
    ap.add_argument("--sem-fonte", action="store_true")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--tol-ang", type=float, default=1.5)
    ap.add_argument("--tol-plano", type=float, default=0.05)
    ap.add_argument("--area-min", type=float, default=1.0)
    ap.add_argument("--json")
    a = ap.parse_args()
    out = sem_fonte() if (a.sem_fonte or not a.malha) else \
        com_fonte(a.malha, a.top, a.tol_ang, a.tol_plano, a.area_min)
    t = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(t)
    print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
