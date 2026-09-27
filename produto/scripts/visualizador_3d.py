# -*- coding: utf-8 -*-
"""visualizador_3d.py - visualizador 3D interativo em UM arquivo .html, sem servidor.

RODA NO PYTHON DO HOSPEDEIRO (nao precisa de Blender aberto nem em segundo plano).

POR QUE ESTE ARQUIVO EXISTE. O pedido era um .html que o usuario abre por duplo
clique no Windows e gira/aproxima com o mouse, de preferencia sem depender de
internet. `trimesh.viewer.notebook.scene_to_html()` ja faz a parte dificil: embute
a malha inteira em GLB (base64) dentro do HTML e embute o PROPRIO three.js
(a biblioteca de renderizacao) no mesmo arquivo, como texto — nao ha `<script src=...>`
nem chamada de rede. MEDIDO em 26/09/2026: o HTML gerado para a peca de teste nao
contem nenhuma ocorrencia de "cdn." nem de "<script src=" (checagem no proprio
`depende_de_cdn` do relatorio); as unicas strings "http" que sobram sao um namespace
XML (`http://www.w3.org/1999/xhtml`) e um comentario de licenca do three.js, nenhum
dos dois busca nada pela rede.

O QUE O TRIMESH NAO FAZ SOZINHO, E FOI ACRESCENTADO AQUI. O template dele so desenha
a malha: sem grade, sem eixos, sem legenda. Este script:
  1. da uma cor solida distinta a cada arquivo de entrada (paleta fixa, 10 cores);
  2. desenha uma grade no plano XY, na cota Z minima do conjunto, com espacamento
     REDONDO (1-2-5 x 10^n) escolhido a partir da diagonal da caixa envolvente —
     ver `_passo_de_grade`;
  3. desenha 3 eixos coloridos (X vermelho, Y verde, Z azul) saindo do canto da grade;
  4. injeta uma legenda em HTML/CSS simples (canto superior esquerdo) com o nome e a
     cor de cada peca, SE houver 2 ou mais pecas.
Grade e eixos sao geometria real (trimesh.path.Path3D), inserida na cena ANTES do
export — por isso tambem viram parte do GLB embutido, e o visualizador nao precisa
de nenhum codigo JS proprio para desenha-los.

ESCALA REAL. Nenhuma normalizacao de tamanho e aplicada. A grade usa a MESMA unidade
numerica dos vertices do arquivo de entrada (mm, se a peca foi modelada em mm) — key
usa. Se as pecas vierem em unidades diferentes entre si, o resultado sera literalmente
essa mistura: verifique a origem antes de visualizar em conjunto.

LIMITE MEDIDO. `scene_to_html` embute a malha como GLB: cor solida por peca sim,
textura/material de origem (imagem, PBR) NAO é preservado — todo objeto vira uma cor
lisa. Para malhas muito grandes (centenas de milhares de faces por peca), o arquivo
.html cresce proporcionalmente (o GLB e binario, mas vai em base64: +33% de tamanho);
nao ha decimacao aqui.

Uso:
    python visualizador_3d.py peca1.stl peca2.stl ... --saida visualizador.html
        [--titulo "Nome do conjunto"] [--sem-grade] [--sem-eixos]

Formatos de entrada aceitos: qualquer um que o trimesh.load reconheca por extensao
(STL, 3MF, GLB/GLTF, OBJ, PLY, ...). Um arquivo com varios corpos (ex.: 3MF de
montagem) e tratado como UMA peca (concatenado) — se precisar de cor por corpo,
separe em arquivos antes de chamar.
"""
import argparse
import hashlib
import html as _html
import json
import os
import time

import numpy as np
import trimesh
import trimesh.viewer.notebook as _nb

VERSAO = "1.0.0"

# Paleta fixa, para nao depender de biblioteca externa de cores. 10 tons distintos
# o bastante em tela (nao e a paleta de acessibilidade da skill dataviz; aqui o
# criterio e so "dar para diferenciar peca por peca").
PALETA = [
    (211, 84, 0), (41, 128, 185), (39, 174, 96), (192, 57, 43),
    (142, 68, 173), (243, 156, 18), (26, 188, 156), (127, 140, 141),
    (44, 62, 80), (211, 84, 153),
]

_MARCADOR_CORPO = "<div id=\"container\"></div>"


def _carregar_peca(caminho):
    """Devolve um Trimesh unico por arquivo. Cena com varios corpos (3MF/GLB de
    montagem) e concatenada: uma entrada de linha de comando = uma peca = uma cor."""
    obj = trimesh.load(caminho, force=None)
    if isinstance(obj, trimesh.Scene):
        malha = obj.dump(concatenate=True)
    else:
        malha = obj
    if not isinstance(malha, trimesh.Trimesh) or len(malha.vertices) == 0:
        raise ValueError("SEM_GEOMETRIA: %s nao produziu malha triangular" % caminho)
    return malha


def _passo_de_grade(diagonal_mm):
    """Espacamento redondo (1-2-5 x 10^n) para a grade cruzar a peca em ~6-10
    celulas. MEDIDO: peca de ~53mm de diagonal cai em 10mm (5-6 celulas); ver
    relatorio de teste em referencias/entregas_em_movimento.md."""
    if diagonal_mm <= 0:
        return 1.0
    alvo = diagonal_mm / 8.0
    escala = 1.0
    while True:
        for c in (1, 2, 5):
            passo = c * escala
            if passo >= alvo:
                return passo
        escala *= 10


def _material_solido(cor_rgb):
    """Material PBR fosco (nao-metalico) de cor solida.

    CORRIGIDO 26/09/2026: colorir via `ColorVisuals(face_colors=...)` (a
    primeira versao) faz o exportador GLB do trimesh gravar um material SEM
    `metallicFactor`/`roughnessFactor` -- e o glTF define o PADRAO da OMISSAO
    como metallicFactor=1.0, roughnessFactor=1.0 (metal totalmente liso). Um
    material metalico nao tem componente difusa (lambertiana): a UNICA luz
    direcional do template quase nao aparece, e o que sobra e so a luz
    ambiente, IGUAL em toda face non importa o normal. MEDIDO num screenshot
    real: o canal R da peca ficou entre 91 e 98 em TODA a area alaranjada
    visivel (duas faces com normais bem diferentes, 0,44 e 0,74 de produto
    escalar com a direcao da camera) -- e 211*0.45 = 95, batendo com "so a
    ambiente" e nao com nenhuma resposta a luz direcional. Um PBRMaterial
    fosco (metallicFactor=0, roughnessFactor alto) devolve a resposta
    lambertiana e faces com normal diferente passam a sair com brilho
    diferente."""
    return trimesh.visual.material.PBRMaterial(
        baseColorFactor=(int(cor_rgb[0]), int(cor_rgb[1]), int(cor_rgb[2]), 255),
        metallicFactor=0.0, roughnessFactor=0.9)


def _pintar_solido(malha, cor_rgb):
    """Aplica `_material_solido` a `malha` (mutando .visual) e devolve `malha`."""
    malha.visual = trimesh.visual.texture.TextureVisuals(material=_material_solido(cor_rgb))
    return malha


def _eixo_mesh(origem, direcao_unit, comprimento, raio, cor_rgb):
    """Eixo como CILINDRO SOLIDO (nao Path3D).

    CORRIGIDO 26/09/2026: a primeira versao desenhava os eixos como linhas
    Path3D com `.colors` por entidade, do mesmo jeito que a grade. MEDIDO num
    screenshot real (Edge headless): as linhas aparecem, mas TODAS cinzas --
    o exportador GLB do trimesh nao propaga `Path3D.colors` para um material
    que o three.js deste template respeite. Malha solida com material PBR
    proprio (ver `_material_solido`) nao tem esse problema."""
    cyl = trimesh.creation.cylinder(radius=raio, height=comprimento, sections=12)
    cyl.apply_translation([0, 0, comprimento / 2.0])  # nasce em Z=0, nao no meio
    rot = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], np.asarray(direcao_unit, dtype=float))
    cyl.apply_transform(rot)
    cyl.apply_translation(origem)
    return _pintar_solido(cyl, cor_rgb)


def _grade_e_eixos(bounds_min, bounds_max, com_grade, com_eixos):
    """Path3D de grade (plano XY, na cota Z minima, cinza -- e so referencia, sem
    promessa de cor) e eixos coloridos (cilindro solido, ver `_eixo_mesh`) saindo
    do canto da grade. Devolve (lista_de_(nome, geometria), info_do_relatorio)."""
    geoms = []
    info = {}
    extensao = np.asarray(bounds_max) - np.asarray(bounds_min)
    diagonal = float(np.linalg.norm(extensao))
    passo = _passo_de_grade(diagonal)  # usado pela grade E pelo canto dos eixos
    margem = passo

    if com_grade:
        x0, x1 = bounds_min[0] - margem, bounds_max[0] + margem
        y0, y1 = bounds_min[1] - margem, bounds_max[1] + margem
        z0 = float(bounds_min[2])
        linhas = []
        x = np.floor(x0 / passo) * passo
        while x <= x1 + 1e-9:
            linhas.append([[x, y0, z0], [x, y1, z0]])
            x += passo
        y = np.floor(y0 / passo) * passo
        while y <= y1 + 1e-9:
            linhas.append([[x0, y, z0], [x1, y, z0]])
            y += passo
        grade = trimesh.load_path(np.array(linhas))
        grade.colors = np.tile([[160, 160, 160, 255]], (len(grade.entities), 1))
        geoms.append(("grade", grade))
        info["grade_espacamento_mm"] = passo
        info["grade_cota_z_mm"] = z0
        info["grade_linhas"] = len(linhas)

    if com_eixos:
        comprimento = max(diagonal * 0.18, 1.0)
        raio = max(comprimento * 0.025, diagonal * 0.002)
        # CORRIGIDO 26/09/2026: com a origem no canto EXATO da caixa envolvente
        # ([bounds_min]), o eixo Z sai de baixo da propria peca e uma vista
        # isometrica tipica o mostra atravessando o SOLIDO -- ficando invisivel
        # por tras da malha. MEDIDO num screenshot real: nenhum pixel azul do
        # eixo Z apareceu (so o azul, mais claro, da tampa). Empurrando o canto
        # para FORA da caixa envolvente por uma casa de grade (mesma margem da
        # grade), o eixo Z fica inteiro FORA do volume da peca em X/Y, entao a
        # vertical nunca mergulha para dentro do solido.
        origem = [float(bounds_min[0]) - margem, float(bounds_min[1]) - margem,
                  float(bounds_min[2])]
        cores = {"x": (230, 30, 30), "y": (30, 170, 30), "z": (30, 60, 230)}
        for eixo, direcao in (("x", (1, 0, 0)), ("y", (0, 1, 0)), ("z", (0, 0, 1))):
            cyl = _eixo_mesh(origem, direcao, comprimento, raio, cores[eixo])
            geoms.append(("eixo_%s" % eixo, cyl))
        info["eixos_comprimento_mm"] = comprimento
        info["eixos_raio_mm"] = raio
        info["eixos_origem_mm"] = origem
        info["eixos_cores"] = {"x": "vermelho", "y": "verde", "z": "azul"}

    return geoms, info


def _injetar_legenda(html_bruto, titulo, legenda, info_grade):
    """Acrescenta uma <div> fixa com titulo, legenda (se 2+ pecas) e a leitura da
    grade/eixos. O template do trimesh nao tem esse gancho, entao a insercao e por
    substituicao de texto no marcador conhecido `_MARCADOR_CORPO` — se uma versao
    futura do trimesh mudar o template, essa substituicao simplesmente nao encontra
    o marcador e `_html.escape`-safe HTML_LEGENDA fica de fora (falha visivel: sem
    legenda), nunca corrompe o visualizador."""
    linhas_legenda = ""
    if len(legenda) > 1:
        itens = []
        for peca in legenda:
            r, g, b = peca["cor_rgb"]
            nome = _html.escape(peca["nome"])
            itens.append(
                "<div style='display:flex;align-items:center;margin:2px 0;'>"
                "<span style='display:inline-block;width:12px;height:12px;"
                "background:rgb(%d,%d,%d);margin-right:6px;border:1px solid #000;'></span>"
                "%s</div>" % (r, g, b, nome)
            )
        linhas_legenda = "".join(itens)

    # CORRIGIDO 26/09/2026: a versao anterior juntava as partes com a ENTIDADE
    # html "&middot;" e SO DEPOIS escapava a string inteira com `_html.escape`,
    # que troca "&" por "&amp;" -- "&middot;" virava "&amp;middot;", e o
    # navegador mostra isso como texto literal "&middot;" (confirmado num
    # screenshot real). Cada parte e escapada ANTES de juntar, e o separador e
    # o CARACTERE unicode "·" (nao a entidade), que `_html.escape` nao toca.
    partes_rodape = []
    if "grade_espacamento_mm" in info_grade:
        partes_rodape.append("grade a cada %.4g mm" % info_grade["grade_espacamento_mm"])
    if "eixos_cores" in info_grade:
        partes_rodape.append("eixos: X vermelho, Y verde, Z azul")
    rodape = " · ".join(_html.escape(p) for p in partes_rodape)

    caixa = (
        "<div style=\"position:fixed;top:8px;left:8px;z-index:10;"
        "background:rgba(255,255,255,0.85);color:#111;font:12px/1.4 sans-serif;"
        "padding:8px 10px;border-radius:4px;max-width:280px;"
        "box-shadow:0 1px 4px rgba(0,0,0,0.3);\">"
        "<div style=\"font-weight:bold;margin-bottom:4px;\">%s</div>"
        "%s"
        "<div style=\"margin-top:4px;color:#444;\">%s</div>"
        "</div>"
    ) % (_html.escape(titulo), linhas_legenda, rodape)

    if _MARCADOR_CORPO not in html_bruto:
        return html_bruto  # falha visivel (sem legenda), nao corrompe o arquivo
    return html_bruto.replace(_MARCADOR_CORPO, _MARCADOR_CORPO + caixa, 1)


_MARCADOR_LUZ = "tracklight=new THREE.DirectionalLight(0xffffff,1.75);scene.add(tracklight);"


def _injetar_luz_ambiente(html_bruto):
    """Acrescenta uma luz ambiente fraca, para a face que fica de costas para a
    luz direcional (que segue a camera) nao sair preta/sem gradiente nenhum.
    MEDIDO: sem isto, face quase perpendicular a camera aparecia um tom solido
    escuro demais para diferenciar de faces vizinhas no mesmo objeto. Insercao
    por substituicao de texto no marcador conhecido; se o template mudar e o
    marcador sumir, a insercao e ignorada (falha visivel: luz padrao do
    trimesh, sem travar o arquivo)."""
    if _MARCADOR_LUZ not in html_bruto:
        return html_bruto
    return html_bruto.replace(
        _MARCADOR_LUZ,
        _MARCADOR_LUZ + "scene.add(new THREE.AmbientLight(0xffffff,0.45));",
        1,
    )


def _camera_isometrica(cena, pontos, direcao=(1.25, -0.75, 0.85), pad=1.15, fov_graus=28.0):
    """Poe a camera OLHANDO na direcao isometrica padrao (mesma convencao de
    `referencias/render_de_conferencia.md`: `direcao` = do centro da cena PARA
    a camera), enquadrando `pontos` (cantos da caixa envolvente de tudo que
    entrou na cena) com folga `pad`.

    CORRIGIDO 26/09/2026: sem isto, a camera que o `trimesh.viewer.notebook`
    embute no GLB e a que o proprio trimesh auto-gera ao acessar `scene.camera`
    pela primeira vez -- e essa camera padrao olha de CIMA, reto para baixo.
    MEDIDO num screenshot real (Edge headless): so a tampa aparecia, como um
    retangulo azul chapado, porque a vista era exatamente de topo. `look_at`
    calcula a DISTANCIA certa a partir do FOV para enquadrar `pontos`; a
    ROTACAO e informada por nos (colunas = direita, cima, direcao).

    FOV ESTREITO DE PROPOSITO. A camera embutida e de PERSPECTIVA (e o que o
    `TrackballControls` do template espera), e o FOV largo padrao do trimesh
    (60 graus) MEDIDO num screenshot real deixava a grade com uma distorcao de
    grande-angular forte (linhas divergindo para o horizonte) porque a camera
    ficava perto da cena para enquadra-la. Estreitar o FOV faz o `look_at`
    AFASTAR a camera para manter o mesmo enquadramento -- o efeito visual fica
    parecido com uma isometrica, mesmo sem ser ortografica de verdade.

    DIRECAO ASSIMETRICA DE PROPOSITO (1.25, -0.75, 0.85), NAO (1,-1,1). A unica
    luz do template (`tracklight`) segue a CAMERA e mira a origem do mundo --
    na pratica um farol que sai da propria camera, entao o brilho de cada face
    plana e proporcional a `dot(normal, direcao)` (mesma conta do MATCAP de
    `render_conferencia.py`). MEDIDO num screenshot real: com `direcao =
    (1,-1,0.85)` (|dx| = |dy|), as duas faces laterais visiveis de uma peca
    ortogonal (normais (1,0,0) e (0,-1,0)) davam O MESMO `dot`, e saiam
    EXATAMENTE da mesma cor -- 91-98 no canal R, sem gradiente nenhum, em toda
    a regiao alaranjada de um screenshot real. Com `dx != |dy|` as duas faces
    recebem `dot` diferente (aqui 0.74 vs 0.44) e ficam visivelmente distintas
    -- ainda um front-top-right generico, so sem a simetria que apaga o
    contraste entre faces ortogonais."""
    cena.camera.fov = (fov_graus, fov_graus)
    d = np.asarray(direcao, dtype=float)
    d = d / np.linalg.norm(d)
    referencia = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.99 else np.array([0.0, 1.0, 0.0])
    direita = np.cross(referencia, d)
    direita = direita / np.linalg.norm(direita)
    cima = np.cross(d, direita)
    rotacao = np.eye(4)
    rotacao[:3, 0] = direita
    rotacao[:3, 1] = cima
    rotacao[:3, 2] = d  # convencao da camera (OpenGL): eixo Z local aponta PARA TRAS

    # centro da caixa envolvente da UNIAO dos pontos -- nao a media deles (que
    # seria o centro medio de varias caixas por objeto, nao o centro da caixa
    # combinada quando os objetos tem tamanhos bem diferentes).
    centro = (pontos.min(axis=0) + pontos.max(axis=0)) / 2.0
    transform = cena.camera.look_at(pontos, rotation=rotacao, center=centro, pad=pad)
    cena.camera_transform = transform


# Rotacao Z-up -> Y-up: (x,y,z) -> (x,z,-y). Rotacao de -90 graus em torno de X.
_Z_UP_PARA_Y_UP = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
])


def _converter_z_up_para_y_up(cena):
    """Gira a cena INTEIRA (pecas, grade, eixos E a camera) -90 graus em X.

    CORRIGIDO 26/09/2026: peca renderizada DEITADA DE LADO num screenshot real
    -- tampa (o topo de verdade, em Z) aparecia como uma face LATERAL grande, a
    grade saia em pe (plano vertical) e via-se o FUNDO da caixa. Causa: STL/3MF
    de peca mecanica e Z-up (Z = "para cima" do objeto real), mas o three.js
    deste template trata Y como "para cima" -- e' o `TrackballControls`
    embutido que usa `camera.up` (que o glTF nao especifica por peca, so herda
    o padrao do three.js, (0,1,0)) para manter a orientacao durante a orbita, e
    a primeira `controls.update()` ja realinha a camera usando esse "up" errado
    ANTES do primeiro frame. Girar a CENA inteira (nao so a camera) por essa
    mesma matriz, como ultimo passo antes de exportar, resolve nas DUAS pontas:
    a malha passa a ter seu Z fisico alinhado ao Y do three.js, e a camera (que
    ja foi calculada certa em coordenadas Z-up por `_camera_isometrica`) roda
    junto e continua olhando para o mesmo lugar relativo. `Scene.apply_transform`
    atualiza so as matrizes de no do grafo (pecas, grade, eixos E camera, que
    tambem e um no do grafo) -- nao mexe em vertice nenhum, entao toda a
    matematica em mm de `_grade_e_eixos`/`_camera_isometrica` continua correta,
    so a CONVENCAO de qual eixo do MUNDO aparece vertical na tela muda."""
    cena.apply_transform(_Z_UP_PARA_Y_UP)


def gerar(caminhos, saida, titulo=None, com_grade=True, com_eixos=True):
    t0 = time.time()
    if not caminhos:
        raise ValueError("SEM_ENTRADA: informe ao menos um arquivo de malha.")

    pecas = []
    for caminho in caminhos:
        malha = _carregar_peca(caminho)
        nome = os.path.splitext(os.path.basename(caminho))[0]
        pecas.append((nome, malha))

    cena = trimesh.Scene()
    legenda = []
    limites = []
    for i, (nome, malha) in enumerate(pecas):
        cor = PALETA[i % len(PALETA)]
        malha = _pintar_solido(malha.copy(), cor)
        cena.add_geometry(malha, node_name="peca_%02d_%s" % (i, nome))
        legenda.append({
            "nome": nome, "arquivo": os.path.abspath(caminhos[i]),
            "cor_rgb": list(cor), "vertices": len(malha.vertices), "faces": len(malha.faces),
        })
        limites.append(malha.bounds)

    # cantos SO das pecas (8 por objeto), antes de acrescentar grade/eixos --
    # e o que a camera precisa enquadrar. CORRIGIDO 26/09/2026: enquadrar
    # tambem a grade (que se estende por design alem da peca, de proposito,
    # como um chao) fazia a peca ocupar so ~25% do quadro num screenshot real.
    # A grade/eixos continuam desenhados e podem se estender para FORA do
    # quadro visivel -- isso e esperado, e' um chao de referencia, nao o
    # assunto da foto.
    cantos_pecas = np.vstack(list(cena.bounds_corners.values()))

    limites = np.array(limites)
    bounds_min = limites[:, 0, :].min(axis=0)
    bounds_max = limites[:, 1, :].max(axis=0)
    geoms, info_grade = _grade_e_eixos(bounds_min, bounds_max, com_grade, com_eixos)
    for nome_geo, geo in geoms:
        cena.add_geometry(geo, node_name=nome_geo)

    _camera_isometrica(cena, cantos_pecas)
    _converter_z_up_para_y_up(cena)

    html_bruto = _nb.scene_to_html(cena)
    html_final = _injetar_legenda(html_bruto, titulo or "Visualizador 3D", legenda, info_grade)
    html_final = _injetar_luz_ambiente(html_final)

    saida = os.path.abspath(saida)
    os.makedirs(os.path.dirname(saida) or ".", exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html_final)

    dados = open(saida, "rb").read()
    minusculo = html_final.lower()
    depende_de_cdn = ("cdn." in minusculo) or ("<script src=" in minusculo)

    return {
        "versao_visualizador_3d": VERSAO,
        "arquivo": saida,
        "bytes": len(dados),
        "sha256": hashlib.sha256(dados).hexdigest(),
        "segundos": round(time.time() - t0, 2),
        "pecas": legenda,
        "grade_e_eixos": info_grade,
        "depende_de_cdn": depende_de_cdn,
        "legenda_visivel": len(legenda) > 1,
        "escala": "real, sem normalizacao; unidade = a do(s) arquivo(s) de origem",
        "alcance": (
            "HTML autocontido (malha em GLB base64 + three.js embutido pelo proprio "
            "trimesh, sem CDN). Abre por duplo clique e navega com o mouse (arrastar "
            "gira, roda do mouse aproxima, botao direito translada). NAO preserva "
            "textura/material de origem — so cor solida por peca. Grade/eixos sao "
            "geometria de apoio, medida a partir da caixa envolvente do conjunto, "
            "nao do arquivo CAD original."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pecas", nargs="+", help="arquivos de malha (STL, 3MF, GLB, OBJ, ...)")
    ap.add_argument("--saida", required=True, help="caminho do .html de saida")
    ap.add_argument("--titulo", default=None)
    ap.add_argument("--sem-grade", action="store_true")
    ap.add_argument("--sem-eixos", action="store_true")
    a = ap.parse_args()
    relatorio = gerar(a.pecas, a.saida, titulo=a.titulo,
                       com_grade=not a.sem_grade, com_eixos=not a.sem_eixos)
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
