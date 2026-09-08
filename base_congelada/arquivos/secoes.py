"""secoes.py - seccao de malha em poligonos 2D, com material e furos separados.

Usado por split_for_volume.py e check_intent.py. Existe como modulo proprio porque as
duas armadilhas abaixo custaram tempo e nao podem ser reimplementadas errado em dois
lugares.

ARMADILHA 1, nodacao. Os segmentos que saem do corte de malha tem extremos calculados
por face, e faces vizinhas produzem coordenadas que diferem nos ultimos bits. O
polygonize do shapely exige linha nodada: com o dado cru ele devolve ZERO poligonos, sem
erro nenhum. MEDIDO 07/09/2026: 646 segmentos, zero poligonos. Arredondar as
coordenadas para 9 casas decimais resolve, e 9 casas em milimetro nao altera cota.
Passar unary_union antes NAO resolve: ele funde as linhas e devolve so um poligono.

ARMADILHA 2, quem e furo. O polygonize devolve a regiao de material JA COM os furos
subtraidos, e os aneis dos furos como poligonos separados. Logo, comparando os poligonos
entre si como estao, material e furo tem a mesma profundidade e a classificacao falha em
silencio: o verificador contava zero furos numa peca com dois.

A classificacao correta compara contra o contorno externo PREENCHIDO de cada poligono, e
resolve o aninhamento INTEIRO por paridade de profundidade. Par e material, impar e furo.
Uma regra mais simples, do tipo "esta dentro de algum vazio", parece funcionar e erra em
anel com ilha: o pino solto dentro do anel cai no vazio e e contado como furo.

Nao consulta o solido de proposito: ponto-dentro-do-solido no trimesh exige o modulo
nativo rtree, que falta em ambiente comum. Toda a decisao e 2D e so depende de shapely,
e por isso tambem nao se usa o caminho de poligonos do proprio trimesh.
"""
import numpy as np

CASAS = 9


def _linhas(malha, eixo, valor):
    from trimesh.intersections import mesh_plane
    n = np.zeros(3); n[eixo] = 1.0
    o = np.zeros(3); o[eixo] = float(valor)
    seg = mesh_plane(malha, plane_normal=n, plane_origin=o)
    if seg is None or len(seg) == 0:
        return [], []
    d = [i for i in range(3) if i != eixo]
    out = []
    for s in seg:
        a = (round(float(s[0][d[0]]), CASAS), round(float(s[0][d[1]]), CASAS))
        b = (round(float(s[1][d[0]]), CASAS), round(float(s[1][d[1]]), CASAS))
        if a != b:
            out.append((a, b))
    return out, d


def _para_3d(pt2, d, eixo, valor):
    p = np.zeros(3)
    p[d[0]] = pt2[0]
    p[d[1]] = pt2[1]
    p[eixo] = float(valor)
    return p


def secao(malha, eixo, valor):
    """Devolve dict com poligonos de material e de furo na secao perpendicular a eixo.

    eixo: 0=X, 1=Y, 2=Z. As coordenadas 2D seguem a ordem dos outros dois eixos.
    Devolve tambem 'profundidades', o nivel de aninhamento de cada poligono na ordem em
    que o polygonize os produziu, para o chamador poder auditar a classificacao.
    """
    from shapely.geometry import MultiLineString
    from shapely.ops import polygonize
    linhas, d = _linhas(malha, eixo, valor)
    if not linhas:
        return {"material": [], "furos": [], "metodo": None,
                "aviso": "a secao neste plano esta vazia"}
    pols = [p for p in polygonize(MultiLineString(linhas)) if p.area > 0]
    if not pols:
        return {"material": [], "furos": [], "metodo": None,
                "aviso": "os segmentos do corte nao fecharam nenhum anel"}

    # CORRIGIDO 07/09/2026 depois da segunda revisao externa. A versao anterior perguntava
    # "este poligono esta dentro de ALGUM vazio ancestral?" e classificava como furo. Isso
    # erra numa ilha de material dentro de uma cavidade, como um pino solto dentro de um
    # anel: a ilha caia dentro do vazio do anel e era contada como furo, corrompendo a
    # contagem de furos e a area de material da particao.
    #
    # A regra correta resolve o aninhamento INTEIRO por paridade de profundidade:
    # profundidade = quantos OUTROS poligonos, com o contorno externo PREENCHIDO, contem o
    # ponto interno deste. Par = material, impar = furo. Num anel com ilha isso da:
    # anel externo 0 (material), cavidade 1 (furo), ilha 2 (material).
    #
    # Nao usa ponto-dentro-do-solido: no trimesh isso exige o modulo nativo rtree, que
    # falta em ambiente comum. Toda a decisao e 2D e so depende de shapely.
    from shapely.geometry import Polygon
    cheios = [Polygon(p.exterior) for p in pols]
    reps = [p.representative_point() for p in pols]
    material, furos, prof = [], [], []
    for i, p in enumerate(pols):
        n = sum(1 for j in range(len(pols)) if j != i and cheios[j].contains(reps[i]))
        prof.append(n)
        (material if n % 2 == 0 else furos).append(p)
    return {"material": material, "furos": furos, "eixos_2d": d,
            "profundidades": prof,
            "metodo": "paridade de profundidade de aninhamento em 2D, sem dependencia nativa",
            "aviso": None}


def area_de_material(malha, eixo, valor):
    """Area de material na secao, ou None se a secao estiver vazia."""
    s = secao(malha, eixo, valor)
    if not s["material"]:
        return None
    return float(sum(p.area for p in s["material"]))


def descreve(p):
    c = p.centroid
    return {"centro": [round(float(c.x), 4), round(float(c.y), 4)],
            "area_mm2": round(float(p.area), 4),
            "diametro_equivalente_mm": round(float(2 * np.sqrt(p.area / np.pi)), 4),
            "circularidade": round(float(4 * np.pi * p.area / (p.length ** 2)), 4)}
