# -*- coding: utf-8 -*-
"""render_conferencia.py - pacote de 4 vistas ortograficas para conferir a FORMA.

RODA DENTRO DO BLENDER. Use por `executa_com_relatorio.py` (contrato executar(config))
ou chame `renderizar(config)` na sessao viva.

O QUE ISTO E. Um portao visual: nenhuma entrega sai sem quatro imagens conferidas
contra o que foi pedido. Duas isometricas EXATAMENTE OPOSTAS garantem que toda face
com normal nao perpendicular a direcao de vista aparece em ao menos uma das duas -
cobertura por construcao, nao por suspeita. Topo confere padrao e simetria; frente
confere perfil.

O QUE ISTO NAO E. Nao e aprovacao. Imagem e DIAGNOSTICO: toda suspeita levantada
aqui tem que virar medida antes de virar alegacao. Furo torto na imagem -> meca os
centros. Tampa deslocada -> confira a matriz. Parede fina -> meca a parede.

NAO TOCA NA CENA DO USUARIO. Todo o render acontece numa cena temporaria, criada e
removida aqui dentro; os objetos sao apenas VINCULADOS a ela, nunca copiados nem
movidos. Motor, resolucao, camera e caminho de saida do usuario ficam intocados.

EDIT MODE. Em EDIT_MESH o datablock ainda nao recebeu a edicao em curso, e o render
sairia da malha ANTERIOR - o defeito nao apareceria na imagem. Aqui chama-se
`obj.update_from_editmode()` antes de medir e renderizar, e o relatorio diz que
chamou, em `atualizado_de_edit_mode`.

FUNDO TRANSPARENTE E DE PROPOSITO. Com alfa zero no fundo, a fracao de pixels com
alfa > 0 E a silhueta medida, nao estimada. `fracao_silhueta` perto de zero prova
imagem praticamente vazia - enquadramento errado, objeto oculto ou malha sem faces -
e isso sai no relatorio em vez de virar um PNG em branco que alguem aprova de olho.

Config (dict JSON):
    objeto      nome de um objeto; ou
    objetos     lista de nomes; ou nenhum dos dois -> todos os MESH visiveis da cena
    pasta       diretorio de saida (obrigatorio)
    prefixo     prefixo dos arquivos (padrao "vista")
    resolucao   [largura, altura] (padrao [1024, 768])
    vistas      subconjunto de ["iso","iso_oposto","topo","frente"] (padrao: as quatro)
    margem      folga alem da caixa envolvente, fracao (padrao 0.12)
"""
import hashlib
import json
import os
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

VERSAO = "1.0.0"

# Direcao = do centro da peca PARA a camera, em coordenadas de mundo.
# iso_oposto e a negacao exata de iso: e dai que vem a cobertura de todas as faces.
DIRECOES = {
    "iso": (1.0, -1.0, 0.8),
    "iso_oposto": (-1.0, 1.0, -0.8),
    "topo": (0.0, 0.0, 1.0),
    "frente": (0.0, -1.0, 0.0),
}
ORDEM = ["iso", "iso_oposto", "topo", "frente"]


def _alvos(config):
    """Objetos a renderizar, ja validados. Erro nomeado em vez de imagem vazia."""
    nomes = config.get("objetos")
    if config.get("objeto"):
        nomes = [config["objeto"]]
    if nomes:
        faltando = [n for n in nomes if n not in bpy.data.objects]
        if faltando:
            raise ValueError(
                "OBJETO_INEXISTENTE: %s. Objetos na cena: %s"
                % (", ".join(faltando), ", ".join(sorted(o.name for o in bpy.data.objects)) or "(nenhum)")
            )
        objs = [bpy.data.objects[n] for n in nomes]
    else:
        objs = [o for o in bpy.context.scene.objects
                if o.type == "MESH" and o.visible_get()]
    if not objs:
        raise ValueError("SEM_ALVO: nenhum objeto MESH visivel na cena; nomeie o objeto em config['objeto'].")
    return objs


def _cantos_mundo(objs):
    """Cantos da caixa envolvente de cada objeto, em mundo. Erro se nada tem volume."""
    pts = []
    for o in objs:
        m = o.matrix_world
        for c in o.bound_box:
            pts.append(m @ Vector(c))
    if not pts:
        raise ValueError("SEM_GEOMETRIA: os alvos nao tem caixa envolvente.")
    return pts


def _camera_para(direcao, pts, centro, raio, larg, alt, margem):
    """Camera ortografica que enquadra TODOS os cantos, com folga declarada."""
    d = Vector(direcao).normalized()
    quat = (-d).to_track_quat("-Z", "Y")
    direita = quat @ Vector((1.0, 0.0, 0.0))
    cima = quat @ Vector((0.0, 1.0, 0.0))

    # Extensao real da peca nos eixos da IMAGEM, nao do mundo.
    meia_larg = max(abs((p - centro).dot(direita)) for p in pts)
    meia_alt = max(abs((p - centro).dot(cima)) for p in pts)
    # ortho_scale cobre a MAIOR dimensao do quadro; converter a altura pela proporcao.
    escala = max(2 * meia_larg, 2 * meia_alt * (larg / alt)) * (1.0 + margem)
    escala = max(escala, 1e-6)

    dados = bpy.data.cameras.new("_conf_cam")
    dados.type = "ORTHO"
    dados.ortho_scale = escala
    dados.clip_start = 1e-4
    dados.clip_end = raio * 12.0 + 1.0

    cam = bpy.data.objects.new("_conf_cam", dados)
    cam.location = centro + d * (raio * 4.0 + 1.0)
    cam.rotation_euler = quat.to_euler()
    return cam, escala


def _medir_png(caminho):
    """Silhueta medida pelo canal alfa. Prova que a imagem nao esta vazia."""
    img = None
    try:
        img = bpy.data.images.load(str(caminho))
        larg, alt = img.size
        n = larg * alt * img.channels
        if n == 0:
            return {"erro": "imagem sem pixels"}
        buf = np.empty(n, dtype=np.float32)
        img.pixels.foreach_get(buf)
        if img.channels < 4:
            return {"largura": larg, "altura": alt,
                    "erro": "sem canal alfa; silhueta nao medida"}
        alfa = buf.reshape(-1, img.channels)[:, 3]
        return {
            "largura": larg,
            "altura": alt,
            "fracao_silhueta": round(float((alfa > 0.01).mean()), 4),
        }
    except Exception as e:  # imagem ilegivel e um FATO do relatorio, nao um traceback
        return {"erro": "%s: %s" % (type(e).__name__, e)}
    finally:
        if img is not None:
            bpy.data.images.remove(img)


def _renderizar_em(cena):
    """Dispara o render na cena temporaria sem trocar a cena do usuario."""
    try:
        with bpy.context.temp_override(scene=cena):
            bpy.ops.render.render(write_still=True)
        return "temp_override"
    except Exception:
        # Sem janela (modo background) o temp_override pode nao bastar; trocar e
        # DEVOLVER a cena da janela e o unico outro caminho, e ele e reversivel.
        win = bpy.context.window
        if win is None:
            raise
        anterior = win.scene
        try:
            win.scene = cena
            bpy.ops.render.render(write_still=True)
        finally:
            win.scene = anterior
        return "troca_de_cena_revertida"


def renderizar(config):
    pasta = config.get("pasta")
    if not pasta:
        raise ValueError("PASTA_AUSENTE: informe config['pasta'] com o diretorio de saida.")
    pasta = Path(pasta).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    prefixo = config.get("prefixo", "vista")
    larg, alt = config.get("resolucao", [1024, 768])
    margem = float(config.get("margem", 0.12))
    pedidas = config.get("vistas", ORDEM)
    desconhecidas = [v for v in pedidas if v not in DIRECOES]
    if desconhecidas:
        raise ValueError("VISTA_DESCONHECIDA: %s; disponiveis: %s"
                         % (", ".join(desconhecidas), ", ".join(ORDEM)))

    objs = _alvos(config)

    # Em EDIT_MESH o datablock esta atrasado; sem isto o render sai da malha anterior.
    atualizados = []
    for o in objs:
        if o.mode == "EDIT":
            o.update_from_editmode()
            atualizados.append(o.name)

    pts = _cantos_mundo(objs)
    centro = sum(pts, Vector((0.0, 0.0, 0.0))) / len(pts)
    raio = max((p - centro).length for p in pts)
    if raio <= 0:
        raise ValueError("GEOMETRIA_DEGENERADA: caixa envolvente de tamanho zero.")

    cena = bpy.data.scenes.new("_conf_render")
    criados = []
    vistas = []
    try:
        cena.render.engine = "BLENDER_WORKBENCH"
        cena.render.resolution_x, cena.render.resolution_y = int(larg), int(alt)
        cena.render.resolution_percentage = 100
        cena.render.film_transparent = True
        cena.render.image_settings.file_format = "PNG"
        cena.render.image_settings.color_mode = "RGBA"
        cena.display.render_aa = "8"
        sombreamento = cena.display.shading
        # MATCAP ilumina em espaco de CAMERA, entao as quatro vistas recebem a luz do
        # mesmo jeito - essa consistencia e a razao da escolha.
        #
        # NAO e correcao de escuridao, e a suposicao de que seria foi DERRUBADA POR
        # MEDIDA em 17/09/2026, na vista de baixo da peca de teste com defeito:
        #   STUDIO  brilho_min 0.058  medio 0.367  contraste 0.148
        #   MATCAP  brilho_min 0.039  medio 0.341  contraste 0.159
        # MATCAP e LEVEMENTE MAIS ESCURO, com contraste levemente maior. Diferenca
        # marginal, e `use_world_space_lighting=False` tambem nao muda nada no render.
        # O fato que encerra a questao: abaixo de 0.15 de brilho ficam so 0.2-0.4% da
        # silhueta, e bolso raso e furo cego na face de baixo aparecem nos dois modos.
        # Escuridao nunca foi o problema; ver a face certa e que era.
        sombreamento.light = "MATCAP"
        sombreamento.color_type = "SINGLE"
        sombreamento.single_color = (0.62, 0.70, 0.78)
        sombreamento.show_object_outline = True
        # Cavidade realca quina, vinco e faceta sem depender da direcao da luz.
        sombreamento.show_cavity = True

        for o in objs:
            cena.collection.objects.link(o)

        for nome in pedidas:
            cam, escala = _camera_para(DIRECOES[nome], pts, centro, raio, larg, alt, margem)
            criados.append(cam)
            cena.collection.objects.link(cam)
            cena.camera = cam
            destino = pasta / ("%s_%s.png" % (prefixo, nome))
            if destino.exists():
                destino.unlink()  # render que falha nao deixa imagem velha para enganar
            cena.render.filepath = str(destino)
            modo = _renderizar_em(cena)
            registro = {
                "vista": nome,
                "direcao_centro_para_camera": list(DIRECOES[nome]),
                "ortho_scale_mm": round(escala, 4),
                "arquivo": str(destino),
                "modo_render": modo,
                "existe": destino.exists(),
            }
            if destino.exists():
                dados = destino.read_bytes()
                registro["bytes"] = len(dados)
                registro["sha256"] = hashlib.sha256(dados).hexdigest()
                registro.update(_medir_png(destino))
            vistas.append(registro)
            cena.collection.objects.unlink(cam)
    finally:
        for cam in criados:
            dados_cam = cam.data
            bpy.data.objects.remove(cam, do_unlink=True)
            if dados_cam.users == 0:
                bpy.data.cameras.remove(dados_cam)
        bpy.data.scenes.remove(cena)

    vazias = [v["vista"] for v in vistas if v.get("fracao_silhueta", 0.0) < 0.001]

    return {
        "versao_render_conferencia": VERSAO,
        "objetos": [o.name for o in objs],
        "atualizado_de_edit_mode": atualizados,
        "centro_mundo": [round(c, 4) for c in centro],
        "bbox_extensao_mundo": [
            round(max(p[i] for p in pts) - min(p[i] for p in pts), 4) for i in range(3)
        ],
        "raio_envolvente": round(raio, 4),
        "margem_aplicada": margem,
        "vistas": vistas,
        "vistas_praticamente_vazias": vazias,
        "cena_do_usuario_alterada": False,
        "alcance": (
            "Quatro vistas ortograficas da forma como ela esta AGORA no datablock. "
            "iso e iso_oposto sao direcoes opostas exatas: toda face cuja normal nao seja "
            "perpendicular a essa direcao aparece em uma das duas. NAO prova dimensao, "
            "parede, folga, passagem de furo nem malha fechada - para isso, os verificadores. "
            "Imagem e diagnostico: transforme cada suspeita em medida antes de afirmar."
        ),
    }


def executar(config):
    return renderizar(config)


if __name__ == "__main__":
    import sys
    bruto = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "{}"
    print(json.dumps(renderizar(json.loads(bruto)), ensure_ascii=False, indent=2))
