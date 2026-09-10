"""Exemplo completo: superficie sintetica aberta, deslocamento e transicao plana.

executar(config) e chamado por executa_com_relatorio.py. Exclusivamente headless.
Nao e receita para escolher feicoes de uma peca real nem exemplo de impressao.
"""
import math
from pathlib import Path
import sys

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import edicao_guiada as G


def executar(config):
    if not bpy.app.background:
        raise ValueError("Use processo headless separado; este exemplo nao atua na sessao do usuario")
    nome = "Painel_didatico"
    if nome in bpy.data.objects:
        raise ValueError("Nome ja existe; nao repetir a criacao sem inspecionar")
    altura = config.get("altura", 1.0)
    if not isinstance(altura, (int, float)) or not math.isfinite(altura) or not 0 < altura <= 2:
        raise ValueError("Exemplo suporta altura finita entre 0 (exclusivo) e 2")
    verts = [(x,y,0) for x in (-3,-1,1,3) for y in (-1,1)]
    faces = [(a,a+2,a+3) for a in (0,2,4)] + [(a,a+3,a+1) for a in (0,2,4)]
    mesh = bpy.data.meshes.new(nome)
    mesh.from_pydata(verts, [], faces);mesh.update()
    obj = bpy.data.objects.new(nome, mesh);bpy.context.collection.objects.link(obj)
    antes = G.captura(nome)
    plano = {"assinatura_antes": antes["sha256"], "alvo": [6,7],
             "transicao": [[i, (verts[i][0]+3)/6] for i in (2,3,4,5)], "vetor": [0,0,altura]}
    mudanca = G.desloca_com_pesos(nome, plano)
    area_esperada = 2 * math.sqrt(6**2 + altura**2)
    # Limites especificos do painel: area analitica, plano sem dobra e triangulos regulares.
    ver = G.verifica_deslocamento(antes, mudanca["depois"], plano, 1e-5,
        {"area_min": area_esperada-1e-4, "area_max": area_esperada+1e-4,
         "angulo_max_graus": .1, "qualidade_min": .03})
    perfil = max(abs(z-altura*(x+3)/6) for x,y,z in mudanca["depois"]["vertices"])
    return {"estado": "MEDIDAS_CONFORMES" if ver["estado"] == "MEDIDAS_CONFORMES" and perfil <= 1e-5 else "REPROVADA",
            "verificacao": ver, "erro_perfil_analitico": perfil,
            "limite": "Superficie aberta sintetica para visualizacao. Perfil nos vertices; nenhuma validacao de fabricacao ou promessa de generalizacao."}
