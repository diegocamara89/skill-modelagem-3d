"""align_rigid.py - transformacao rigida que leva um datum sobre outro.

Uso:
  # datums vindos de find_datums.py (indice na lista datums_candidatos)
  python align_rigid.py --de d1.json --de-idx 0 --para d2.json --para-idx 0 [--json out.json]

  # ou normais e pontos explicitos
  python align_rigid.py --de-normal 0,-0.2588,0.9659 --de-ponto 0,10,20 \
                        --para-normal 0,0,1 --para-ponto 0,0,0

  # resolver a rotacao no plano com uma segunda direcao
  python align_rigid.py ... --de-dir 1,0,0 --para-dir 0,1,0

  # aplicar a uma malha
  python align_rigid.py ... --aplicar peca.stl --saida peca_alinhada.stl

TRES COISAS QUE ESTE SCRIPT FAZ DE PROPOSITO:

1. Devolve o ANGULO RELATIVO entre os dois datums em destaque. Alinhar cada peca a um
   eixo absoluto, separadamente, e um erro diferente de alinhar uma a outra, e produz
   resultado errado quando o datum e inclinado.

2. Diz quantos graus de liberdade sobraram. Casar plano com plano deixa 3 graus soltos:
   a rotacao em torno da normal e as duas translacoes no plano. Sem uma segunda
   restricao a solucao NAO e unica, e o script avisa em vez de escolher em silencio.

3. Nunca espelha. O determinante da rotacao e sempre +1. Espelhar uma interface de
   acoplamento assimetrica destroi o encaixe, e nenhuma reflexao de conveniencia visual
   compensa isso. Se a intencao for espelhar, isso e outra operacao e tem que ser
   pedida com esse nome, ciente da consequencia.
"""
import argparse, json, os, sys
import numpy as np


def vet(s):
    v = np.array([float(x) for x in s.split(",")], float)
    if v.size != 3:
        raise SystemExit("vetor deve ter 3 componentes: " + s)
    return v


def unit(v):
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise SystemExit("vetor nulo")
    return v / n


def rot_de_para(a, b):
    """Rotacao propria minima que leva o versor a no versor b."""
    a, b = unit(a), unit(b)
    c = float(np.clip(np.dot(a, b), -1, 1))
    if c > 1 - 1e-12:
        return np.eye(3), 0.0, np.array([0.0, 0, 1])
    if c < -1 + 1e-12:
        # antiparalelos: 180 graus em torno de qualquer eixo perpendicular a a
        aux = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0.0, 1, 0])
        eixo = unit(np.cross(a, aux))
        K = np.array([[0, -eixo[2], eixo[1]], [eixo[2], 0, -eixo[0]], [-eixo[1], eixo[0], 0]])
        return np.eye(3) + 2 * (K @ K), 180.0, eixo
    eixo = unit(np.cross(a, b))
    s = float(np.linalg.norm(np.cross(a, b)))
    K = np.array([[0, -eixo[2], eixo[1]], [eixo[2], 0, -eixo[0]], [-eixo[1], eixo[0], 0]])
    R = np.eye(3) + s * K + (1 - c) * (K @ K)
    return R, float(np.degrees(np.arccos(c))), eixo


def rot_em_torno(eixo, graus):
    e = unit(eixo)
    t = np.radians(graus)
    K = np.array([[0, -e[2], e[1]], [e[2], 0, -e[0]], [-e[1], e[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * (K @ K)


def le_datum(caminho, idx):
    d = json.load(open(caminho, encoding="utf-8"))
    lista = d.get("datums_candidatos") or []
    if not lista:
        raise SystemExit("%s nao tem datums_candidatos (modo=%s)" % (caminho, d.get("modo")))
    if idx >= len(lista):
        raise SystemExit("indice %d fora da lista de %d datums" % (idx, len(lista)))
    r = lista[idx]
    return np.array(r["normal"], float), np.array(r["centroide_mm"], float), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--de"); ap.add_argument("--de-idx", type=int, default=0)
    ap.add_argument("--para"); ap.add_argument("--para-idx", type=int, default=0)
    ap.add_argument("--de-normal"); ap.add_argument("--de-ponto")
    ap.add_argument("--para-normal"); ap.add_argument("--para-ponto")
    ap.add_argument("--de-dir"); ap.add_argument("--para-dir")
    ap.add_argument("--aplicar"); ap.add_argument("--saida")
    ap.add_argument("--json")
    a = ap.parse_args()

    info_de = info_para = None
    if a.de:
        nA, pA, info_de = le_datum(a.de, a.de_idx)
    elif a.de_normal and a.de_ponto:
        nA, pA = vet(a.de_normal), vet(a.de_ponto)
    else:
        raise SystemExit("informe --de/--de-idx ou --de-normal e --de-ponto")
    if a.para:
        nB, pB, info_para = le_datum(a.para, a.para_idx)
    elif a.para_normal and a.para_ponto:
        nB, pB = vet(a.para_normal), vet(a.para_ponto)
    else:
        raise SystemExit("informe --para/--para-idx ou --para-normal e --para-ponto")

    nA, nB = unit(nA), unit(nB)
    R1, ang_rel, eixo = rot_de_para(nA, nB)

    gl_resolvidos = ["normal do datum casada"]
    gl_soltos = ["rotacao em torno da normal", "translacao no plano (2 direcoes)"]
    ang_plano = None
    R = R1
    if a.de_dir and a.para_dir:
        dA = R1 @ unit(vet(a.de_dir))
        dB = unit(vet(a.para_dir))
        # projeta as duas no plano perpendicular a nB e mede o angulo com sinal
        proj = lambda v: v - np.dot(v, nB) * nB
        u, w = proj(dA), proj(dB)
        if np.linalg.norm(u) < 1e-9 or np.linalg.norm(w) < 1e-9:
            raise SystemExit("uma das direcoes secundarias e paralela a normal: nao resolve nada")
        u, w = unit(u), unit(w)
        s = float(np.dot(np.cross(u, w), nB))
        c = float(np.clip(np.dot(u, w), -1, 1))
        ang_plano = float(np.degrees(np.arctan2(s, c)))
        R = rot_em_torno(nB, ang_plano) @ R1
        gl_resolvidos.append("rotacao no plano casada pela direcao secundaria")
        gl_soltos = ["translacao no plano (2 direcoes)"]

    t = pB - R @ pA
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t
    det = float(np.linalg.det(R))
    resid = float(np.linalg.norm((R @ pA + t) - pB))
    n_result = R @ nA
    resid_normal = float(np.linalg.norm(n_result - nB))

    out = {
        "angulo_relativo_deg": round(ang_rel, 4),
        "eixo_de_rotacao": [round(float(x), 6) for x in eixo],
        "angulo_no_plano_deg": None if ang_plano is None else round(ang_plano, 4),
        "matriz_4x4": [[round(float(x), 9) for x in linha] for linha in M],
        "determinante_da_rotacao": round(det, 12),
        "espelha": bool(det < 0),
        "residuo_do_ponto_mm": round(resid, 9),
        "residuo_da_normal": round(resid_normal, 9),
        "graus_de_liberdade_resolvidos": gl_resolvidos,
        "graus_de_liberdade_soltos": gl_soltos,
        "solucao_unica": bool(not gl_soltos),
        "aviso_angulo_relativo": (
            "Use o angulo RELATIVO acima (%.4f graus). Girar cada peca contra um eixo absoluto, "
            "separadamente, da resultado diferente e errado quando o datum e inclinado." % ang_rel),
        "aviso_graus_soltos": (
            "Sobram estes graus de liberdade: %s. A solucao NAO e unica. Resolva com uma segunda "
            "restricao (--de-dir/--para-dir para a rotacao; um furo, uma aresta ou um encosto para "
            "a translacao) antes de construir geometria em cima." % "; ".join(gl_soltos)
            if gl_soltos else "Rotacao totalmente determinada pelas duas restricoes."),
        "aviso_espelho": (
            "Este script nunca espelha: o determinante da rotacao e sempre +1. Espelhar uma "
            "interface de acoplamento assimetrica destroi o encaixe."),
    }
    if info_de:
        out["datum_de"] = {k: info_de[k] for k in
                           ("area_mm2", "eixo_mais_proximo", "angulo_com_esse_eixo_deg",
                            "alinhada_a_eixo", "residuo_planaridade_mm") if k in info_de}
    if info_para:
        out["datum_para"] = {k: info_para[k] for k in
                             ("area_mm2", "eixo_mais_proximo", "angulo_com_esse_eixo_deg",
                              "alinhada_a_eixo", "residuo_planaridade_mm") if k in info_para}

    if a.aplicar:
        # CORRIGIDO 07/09/2026 depois da terceira revisao externa: aceitava o MESMO arquivo
        # em --aplicar e --saida e o sobrescrevia, contra a regra de preservar as entradas.
        alvos = [x for x in (a.saida, a.json) if x]
        for alvo in alvos:
            if os.path.abspath(alvo) == os.path.abspath(a.aplicar):
                raise SystemExit(
                    "recusado: %r e ao mesmo tempo entrada e saida. A entrada nao pode ser "
                    "sobrescrita. Use um caminho de saida diferente." % alvo)
        import trimesh
        m = trimesh.load(a.aplicar, force="mesh", process=False)
        antes = [round(float(x), 4) for x in m.extents]
        m.apply_transform(M)
        out["aplicado"] = {
            "arquivo": a.aplicar,
            "caixa_antes_mm": antes,
            "caixa_depois_mm": [round(float(x), 4) for x in m.extents],
            "nota": "a caixa muda porque a peca girou; isso NAO valida o alinhamento",
        }
        if a.saida:
            m.export(a.saida)
            out["aplicado"]["saida"] = a.saida

    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
