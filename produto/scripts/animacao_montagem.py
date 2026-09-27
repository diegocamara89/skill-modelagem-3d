# -*- coding: utf-8 -*-
"""animacao_montagem.py - GIF (e opcionalmente MP4) de vista explodida: as pecas se
afastam da posicao montada e voltam a encaixar, num loop.

RODA NO PYTHON DO HOSPEDEIRO. Nao depende de Blender.

POR QUE NAO O BLENDER. A rota do Blender (`roda_blender.py`) e a certa quando o
resultado depende de shading/booleana/topologia do proprio Blender — nao e o caso
aqui: a animacao e s6 TRANSLACAO RIGIDA de corpos ja validos, sem operacao nenhuma
de malha. Um rasterizador proprio evita tres armadilhas medidas em OUTRO lugar
(nao neste pacote) com `Poly3DCollection` do matplotlib: ele ordena por COLECAO
inteira, nao por triangulo, e uma peca da frente pode ficar atras de uma peca de
tras que foi adicionada depois — o defeito e conhecido como "z-order por colecao".
A solucao medida e um z-buffer de verdade, por PIXEL, e e o que este arquivo faz:
projecao ortografica (mesma convencao de `render_conferencia.py`: direcao = do
centro da cena PARA a camera) seguida de rasterizacao de triangulo com teste de
profundidade por pixel. ~150 linhas, sem Blender, sem matplotlib, sem OpenGL.

LIMITE MEDIDO. O laco e por triangulo (vetorizado dentro de cada triangulo, nao
entre triangulos): custo cresce com (numero de triangulos) x (area de tela que
cada um ocupa). Nos tres corpos de teste (428 faces no total) uma vista de
640x480 levou uma fracao de segundo por quadro — ver o relatorio de teste em
`referencias/entregas_em_movimento.md`. Malha de centenas de milhares de faces
teria o mesmo problema ja documentado em `referencias/render_de_conferencia.md`
("malha grande: recortar antes de renderizar"): decime ou recorte antes.

SOMBREAMENTO. Iluminacao dependente so da camera (luz vem da propria direcao de
vista, como o MATCAP de `render_conferencia.py`): brilho = base + ganho *
max(0, normal . direcao_da_camera). Normais sao as da peca na pose MONTADA —
translacao rigida nao muda normal nenhuma, entao sao calculadas uma vez so.

CONVENCAO DE ENTRADA. As pecas chegam **ja na posicao montada**: as coordenadas
de cada arquivo SAO a pose final (mesma convencao usada para conferir montagem em
`referencias/verificar.md`). Este script nao alinha nem encaixa nada — so afasta
e traz de volta.

Direcao de explosao (duas opcoes):
  - padrao (sem --direcao-explosao): CADA peca vai do centro do CONJUNTO para o
    centro da PROPRIA caixa envolvente, cada uma na sua direcao. Peca com centro
    coincidindo com o centro do conjunto tem deslocamento ZERO nessa regra — o
    relatorio avisa qual peca caiu nesse caso, em vez de fingir uma direcao.
  - `--direcao-explosao dx dy dz`: eixo UNICO para todas as pecas. Cada peca se
    afasta ao longo desse eixo, para o lado em que **ja esta** (sinal de
    (centro_da_peca - centro_do_conjunto) . direcao); pecas exatamente no plano
    perpendicular a essa direcao (projecao zero) nao se movem, e tambem entram
    no aviso do relatorio.

Uso:
  python animacao_montagem.py caixa.stl tampa.stl pino.stl --saida montagem.gif
      [--distancia 40] [--direcao-explosao 0 0 1] [--quadros 24] [--fps 12]
      [--vista iso] [--resolucao 640 480] [--mp4] [--manter-quadros]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time

import numpy as np
import trimesh
from PIL import Image

VERSAO = "1.0.0"

# Mesmas quatro direcoes de referencias/render_de_conferencia.md (duplicadas de
# proposito: este script roda sozinho, sem importar o outro). Direcao = do
# centro da cena PARA a camera.
DIRECOES_VISTA = {
    "iso": (1.0, -1.0, 0.8),
    "iso_oposto": (-1.0, 1.0, -0.8),
    "topo": (0.0, 0.0, 1.0),
    "frente": (0.0, -1.0, 0.0),
}

FFMPEG_PADRAO = r"C:\ffmpeg\bin\ffmpeg.exe"


def _carregar_peca(caminho):
    obj = trimesh.load(caminho, force=None)
    malha = obj.dump(concatenate=True) if isinstance(obj, trimesh.Scene) else obj
    if not isinstance(malha, trimesh.Trimesh) or len(malha.vertices) == 0:
        raise ValueError("SEM_GEOMETRIA: %s nao produziu malha triangular" % caminho)
    return malha


def _base_camera(direcao):
    d = np.asarray(direcao, dtype=float)
    d = d / np.linalg.norm(d)
    ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.99 else np.array([0.0, 1.0, 0.0])
    direita = np.cross(ref, d)
    direita = direita / np.linalg.norm(direita)
    cima = np.cross(d, direita)
    return d, direita, cima


def _envelope(n_quadros):
    """0 -> 1 -> 0 suave, com derivada zero nas duas pontas (loop sem solavanco).
    i=0 e i=n-1 sao a pose MONTADA; o pico (totalmente explodida) fica no meio."""
    i = np.arange(n_quadros)
    if n_quadros <= 1:
        return np.zeros(n_quadros)
    fase = 2 * np.pi * i / (n_quadros - 1)
    return (1 - np.cos(fase)) / 2.0


def _vetores_explosao_pico(centros, centro_conjunto, direcao_fixa, distancia):
    """Devolve (vetor_de_deslocamento_no_PICO_por_peca, avisos).

    MEDIDO (26/09/2026, pecas de teste caixa+tampa+pino): mover toda peca pela
    MESMA distancia, cada uma na sua propria direcao, e degenerado quando duas
    pecas empilhadas tem o centro do mesmo lado do centro do conjunto -- caixa e
    tampa deram o MESMO vetor unitario (0,0,1), e mover as duas pelo mesmo vetor
    NAO as separa uma da outra (a distancia relativa entre elas fica igual).
    A correcao e escalar o deslocamento de cada peca pela PROPORCAO da sua
    propria distancia ao centro, e nao dar a mesma distancia cheia para todas:
    a peca mais afastada do centro do conjunto recebe `distancia` inteira, as
    mais proximas recebem uma fracao -- e e essa fracao que aumenta a folga
    ENTRE pecas vizinhas, nao so entre cada uma e um centro abstrato."""
    vetores = []
    avisos = []
    if direcao_fixa is not None:
        d = np.asarray(direcao_fixa, dtype=float)
        d = d / np.linalg.norm(d)
        projs = [float(np.dot(c - centro_conjunto, d)) for _, c in centros]
        pico = max(abs(p) for p in projs) if projs else 0.0
        for (nome, _c), proj in zip(centros, projs):
            if pico < 1e-9:
                avisos.append("%s: todas as pecas tem a mesma projecao no eixo fixo -- nenhuma se move" % nome)
                vetores.append(np.zeros(3))
            else:
                vetores.append(d * (proj / pico) * distancia)
    else:
        deltas = [c - centro_conjunto for _, c in centros]
        normas = [float(np.linalg.norm(x)) for x in deltas]
        pico = max(normas) if normas else 0.0
        for (nome, _c), delta, norma in zip(centros, deltas, normas):
            if pico < 1e-9:
                avisos.append("%s: todos os centros coincidem com o centro do conjunto -- nenhuma peca se move" % nome)
                vetores.append(np.zeros(3))
            elif norma < 1e-9:
                avisos.append("%s: centro coincide com o centro do conjunto -- nao se move" % nome)
                vetores.append(np.zeros(3))
            else:
                vetores.append((delta / norma) * (norma / pico) * distancia)
    return vetores, avisos


def _rasterizar_triangulo(zbuf, cor_buf, alfa_buf, p, prof, cor_rgb, brilho):
    """p: (3,2) pixels; prof: (3,) profundidade (maior = mais perto da camera).
    Escreve direto em zbuf/cor_buf/alfa_buf onde o triangulo vence o teste de
    profundidade. Vetorizado DENTRO do triangulo (bbox de pixels), nao entre
    triangulos -- e a unidade de custo documentada no cabecalho."""
    larg = zbuf.shape[1]
    alt = zbuf.shape[0]
    x0 = max(int(np.floor(p[:, 0].min())), 0)
    x1 = min(int(np.ceil(p[:, 0].max())), larg - 1)
    y0 = max(int(np.floor(p[:, 1].min())), 0)
    y1 = min(int(np.ceil(p[:, 1].max())), alt - 1)
    if x1 < x0 or y1 < y0:
        return

    xx, yy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)

    def _aresta(ax, ay, bx, by, px, py):
        return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

    area = _aresta(p[0, 0], p[0, 1], p[1, 0], p[1, 1], p[2, 0], p[2, 1])
    if abs(area) < 1e-9:
        return  # triangulo degenerado em tela (de perfil exato)
    w0 = _aresta(p[1, 0], p[1, 1], p[2, 0], p[2, 1], xx, yy)
    w1 = _aresta(p[2, 0], p[2, 1], p[0, 0], p[0, 1], xx, yy)
    w2 = _aresta(p[0, 0], p[0, 1], p[1, 0], p[1, 1], xx, yy)
    sinal = np.sign(area)
    dentro = (w0 * sinal >= 0) & (w1 * sinal >= 0) & (w2 * sinal >= 0)
    if not dentro.any():
        return

    prof_interp = (w0 * prof[0] + w1 * prof[1] + w2 * prof[2]) / area
    janela = zbuf[y0:y1 + 1, x0:x1 + 1]
    vence = dentro & (prof_interp > janela)
    if not vence.any():
        return
    janela[vence] = prof_interp[vence]
    for canal in range(3):
        buf_canal = cor_buf[y0:y1 + 1, x0:x1 + 1, canal]
        buf_canal[vence] = int(round(cor_rgb[canal] * brilho))
    alfa_buf[y0:y1 + 1, x0:x1 + 1][vence] = 255


def _renderizar_quadro(pecas, deslocamentos, direcao_cam, direita, cima, centro_cam,
                        escala_u, escala_v, larg, alt):
    zbuf = np.full((alt, larg), -np.inf)
    cor_buf = np.zeros((alt, larg, 3), dtype=np.uint8)
    alfa_buf = np.zeros((alt, larg), dtype=np.uint8)
    for (verts, faces, normais_face, cor_rgb), desloc in zip(pecas, deslocamentos):
        v = verts + desloc
        # backface culling: so desenha face cujo normal aponta para a camera --
        # valido porque a entrada e solido valido (normal para fora) e so recebeu
        # translacao rigida (normal nao muda).
        visivel = (normais_face @ direcao_cam) > 0
        if not visivel.any():
            continue
        rel = v - centro_cam
        u = rel @ direita
        w = rel @ cima
        prof = rel @ direcao_cam
        px = (u / escala_u + 0.5) * larg
        py = (1 - (w / escala_v + 0.5)) * alt
        pontos_tela = np.stack([px, py], axis=1)
        idx_faces = np.nonzero(visivel)[0]
        for fi in idx_faces:
            f = faces[fi]
            brilho = float(np.clip(0.35 + 0.65 * normais_face[fi] @ direcao_cam, 0.25, 1.0))
            _rasterizar_triangulo(zbuf, cor_buf, alfa_buf,
                                  pontos_tela[f], prof[f], cor_rgb, brilho)
    img = np.dstack([cor_buf, alfa_buf])
    return img


PALETA = [
    (211, 84, 0), (41, 128, 185), (39, 174, 96), (192, 57, 43),
    (142, 68, 173), (243, 156, 18), (26, 188, 156), (127, 140, 141),
]


def gerar(caminhos, saida_gif, distancia=None, direcao_explosao=None, quadros=24,
          fps=12, vista="iso", resolucao=(640, 480), margem=0.15, mp4=False,
          ffmpeg=FFMPEG_PADRAO, manter_quadros=False):
    t0 = time.time()
    if len(caminhos) < 2:
        raise ValueError("PECAS_INSUFICIENTES: informe 2 ou mais arquivos ja montados.")
    if vista not in DIRECOES_VISTA:
        raise ValueError("VISTA_DESCONHECIDA: %s; use uma de %s"
                          % (vista, ", ".join(DIRECOES_VISTA)))

    dados_peca = []
    for i, caminho in enumerate(caminhos):
        malha = _carregar_peca(caminho)
        nome = os.path.splitext(os.path.basename(caminho))[0]
        dados_peca.append({
            "nome": nome, "verts": malha.vertices.copy(), "faces": malha.faces.copy(),
            "normais_face": malha.face_normals.copy(), "cor": PALETA[i % len(PALETA)],
            "bounds": malha.bounds.copy(),
        })

    limites = np.array([d["bounds"] for d in dados_peca])
    bounds_min = limites[:, 0, :].min(axis=0)
    bounds_max = limites[:, 1, :].max(axis=0)
    centro_conjunto = (bounds_min + bounds_max) / 2.0
    diagonal = float(np.linalg.norm(bounds_max - bounds_min))
    if distancia is None:
        distancia = 0.5 * diagonal

    centros = [(d["nome"], (d["bounds"][0] + d["bounds"][1]) / 2.0) for d in dados_peca]
    vetores_pico, avisos = _vetores_explosao_pico(centros, centro_conjunto, direcao_explosao, distancia)

    envelope = _envelope(quadros)

    direcao_cam, direita, cima = _base_camera(DIRECOES_VISTA[vista])
    # escala da camera calculada no pico da explosao (maior extensao possivel);
    # mesma logica de referencias/render_de_conferencia.md: enquadrar TODOS os
    # cantos, com folga declarada, por construcao e nao por sorte.
    #
    # CORRIGIDO 26/09/2026: a primeira versao usava `d["bounds"]` direto, que sao
    # so 2 pontos (canto minimo e canto maximo da caixa envolvente) -- NAO os 8
    # cantos. Para uma vista isometrica (eixos direita/cima NAO alinhados com
    # X/Y/Z), a extensao projetada de uma caixa so e garantida pelos 8 cantos:
    # os 2 cantos diagonais SUBESTIMAM a extensao nos outros 6 cantos. MEDIDO
    # num quadro real do pico da explosao: a tampa encostava/cortava na borda
    # de cima do quadro com a conta antiga -- exatamente o sintoma esperado de
    # subestimar a caixa de enquadramento.
    pontos_pico = []
    for d, desloc_max in zip(dados_peca, vetores_pico):
        mn, mx = d["bounds"]
        for cx in (mn[0], mx[0]):
            for cy in (mn[1], mx[1]):
                for cz in (mn[2], mx[2]):
                    pontos_pico.append(np.array([cx, cy, cz]) + desloc_max)
    pontos_pico = np.array(pontos_pico)
    centro_cam = pontos_pico.mean(axis=0)
    rel = pontos_pico - centro_cam
    meia_larg = np.abs(rel @ direita).max()
    meia_alt = np.abs(rel @ cima).max()
    larg, alt = resolucao
    escala_u = max(2 * meia_larg, 2 * meia_alt * (larg / alt)) * (1.0 + margem)
    escala_v = escala_u * (alt / larg)

    pecas_para_render = [(d["verts"], d["faces"], d["normais_face"], d["cor"]) for d in dados_peca]

    pasta_quadros = tempfile.mkdtemp(prefix="animacao_montagem_")
    quadros_pil = []
    try:
        for i in range(quadros):
            deslocamentos = [vetor * envelope[i] for vetor in vetores_pico]
            img = _renderizar_quadro(pecas_para_render, deslocamentos, direcao_cam,
                                      direita, cima, centro_cam, escala_u, escala_v, larg, alt)
            im = Image.fromarray(img, mode="RGBA")
            im.save(os.path.join(pasta_quadros, "quadro_%04d.png" % i))
            # GIF nao tem alfa graduado; funde sobre branco so para o GIF/MP4.
            fundo_branco = Image.new("RGB", (larg, alt), (255, 255, 255))
            fundo_branco.paste(im, mask=im.split()[3])
            quadros_pil.append(fundo_branco)

        saida_gif = os.path.abspath(saida_gif)
        os.makedirs(os.path.dirname(saida_gif) or ".", exist_ok=True)
        duracao_ms = int(round(1000 / fps))
        quadros_pil[0].save(saida_gif, save_all=True, append_images=quadros_pil[1:],
                             duration=duracao_ms, loop=0, optimize=True)

        saida_mp4 = None
        if mp4:
            saida_mp4 = os.path.splitext(saida_gif)[0] + ".mp4"
            exe = ffmpeg if os.path.isfile(ffmpeg) else (shutil.which("ffmpeg") or ffmpeg)
            cmd = [exe, "-y", "-framerate", str(fps),
                   "-i", os.path.join(pasta_quadros, "quadro_%04d.png"),
                   "-vf", "format=yuv420p", saida_mp4]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if proc.returncode != 0 or not os.path.isfile(saida_mp4):
                saida_mp4 = None
                avisos.append("MP4 nao gerado: ffmpeg devolveu codigo %s. Saida: %s"
                               % (proc.returncode, (proc.stdout or "")[-800:]))
    finally:
        pasta_final_quadros = None
        if manter_quadros:
            pasta_final_quadros = os.path.join(
                os.path.dirname(saida_gif) or ".",
                os.path.splitext(os.path.basename(saida_gif))[0] + "_quadros")
            if os.path.isdir(pasta_final_quadros):
                shutil.rmtree(pasta_final_quadros)
            shutil.move(pasta_quadros, pasta_final_quadros)
        else:
            shutil.rmtree(pasta_quadros, ignore_errors=True)

    dados_gif = open(saida_gif, "rb").read()
    relatorio = {
        "versao_animacao_montagem": VERSAO,
        "arquivo_gif": saida_gif,
        "bytes_gif": len(dados_gif),
        "sha256_gif": hashlib.sha256(dados_gif).hexdigest(),
        "arquivo_mp4": saida_mp4,
        "quadros": quadros,
        "fps": fps,
        "vista_camera": vista,
        "direcao_camera_centro_para_camera": list(DIRECOES_VISTA[vista]),
        "resolucao": [larg, alt],
        "ortho_scale_mm": round(escala_u, 4),
        "distancia_explosao_mm": round(float(distancia), 4),
        "direcao_explosao_fixa": list(direcao_explosao) if direcao_explosao is not None else None,
        "pecas": [
            {"nome": d["nome"], "vertices": len(d["verts"]), "faces": len(d["faces"]),
             "cor_rgb": list(d["cor"]),
             "deslocamento_pico_mm": [round(float(x), 4) for x in vetor],
             "deslocamento_pico_norma_mm": round(float(np.linalg.norm(vetor)), 4)}
            for d, vetor in zip(dados_peca, vetores_pico)
        ],
        "avisos": avisos,
        "pasta_quadros_png": pasta_final_quadros,
        "segundos": round(time.time() - t0, 2),
        "alcance": (
            "Rasterizador proprio (z-buffer por pixel, sombreado so por camera). "
            "NAO e um render de qualidade de apresentacao: sem anti-serrilhado, sem "
            "sombra projetada, sem material de origem. Serve para CONFERIR como as "
            "pecas se encaixam durante o movimento -- a forma de cada peca continua "
            "sendo conferida pelas quatro vistas de render_de_conferencia.md, nunca "
            "por este GIF."
        ),
    }
    return relatorio


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pecas", nargs="+", help="arquivos de malha JA na pose montada")
    ap.add_argument("--saida", required=True, help="caminho do .gif de saida")
    ap.add_argument("--distancia", type=float, default=None,
                     help="deslocamento maximo em mm (padrao: metade da diagonal do conjunto)")
    ap.add_argument("--direcao-explosao", nargs=3, type=float, default=None,
                     metavar=("DX", "DY", "DZ"),
                     help="eixo fixo para todas as pecas (padrao: cada peca para o proprio centro)")
    ap.add_argument("--quadros", type=int, default=24)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--vista", default="iso", choices=list(DIRECOES_VISTA))
    ap.add_argument("--resolucao", nargs=2, type=int, default=[640, 480], metavar=("LARG", "ALT"))
    ap.add_argument("--margem", type=float, default=0.15)
    ap.add_argument("--mp4", action="store_true", help="tambem gera .mp4 via ffmpeg")
    ap.add_argument("--ffmpeg", default=FFMPEG_PADRAO)
    ap.add_argument("--manter-quadros", action="store_true",
                     help="preserva a sequencia de PNG usada para montar o GIF/MP4")
    a = ap.parse_args()
    relatorio = gerar(a.pecas, a.saida, distancia=a.distancia,
                       direcao_explosao=a.direcao_explosao, quadros=a.quadros, fps=a.fps,
                       vista=a.vista, resolucao=tuple(a.resolucao), margem=a.margem,
                       mp4=a.mp4, ffmpeg=a.ffmpeg, manter_quadros=a.manter_quadros)
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
