# -*- coding: utf-8 -*-
"""gera_cenario.py - gerador de cenario SINTETICO para ensaiar as receitas.

RODA DENTRO DO BLENDER:
  blender --background --factory-startup --python gera_cenario.py -- <parametros.json>

Todas as dimensoes foram escolhidas para este exemplo. Nenhuma vem de projeto real.

A peca: um bloco com dois patamares de alturas diferentes e um vao entre eles. O
vao e o alvo da receita de preenchimento local, e a resposta certa e conhecida de
antemao, o que permite medir o resultado em vez de olhar para ele.

    z
    |   patamar_alto                     patamar_baixo
    |   +---------+                        +---------+
   20   |         |                        |         |
    |   |         |....... vao .........   +---------+ 14
   10   +---------+------------------------+---------+
    |   |                  base                     |
    0   +-------------------------------------------+
        0        20                      40        60   x

Variante: os mesmos limites com outras dimensoes e girada, para o segundo ensaio.
"""
import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

PADRAO = {
    "nome": "peca_de_ensaio",
    "comprimento": 60.0,      # x
    "largura": 40.0,          # y
    "altura_da_base": 10.0,   # z do topo da base
    "vao_de": 20.0,           # x onde o patamar alto termina
    "vao_ate": 40.0,          # x onde o patamar baixo comeca
    "altura_alta": 20.0,      # topo do patamar alto
    "altura_baixa": 14.0,     # topo do patamar baixo
    "rotacao_z_graus": 0.0,
    "saida_blend": None,
    "saida_relatorio": None,
}


def caixa(nome, minimo, maximo):
    """Caixa por cantos em coordenada de MUNDO, sem depender de align nem de
    transformacao pendente: os vertices ja nascem no lugar certo."""
    mn, mx = Vector(minimo), Vector(maximo)
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((mn.x if v.co.x < 0 else mx.x,
                       mn.y if v.co.y < 0 else mx.y,
                       mn.z if v.co.z < 0 else mx.z))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(nome, me)
    bpy.context.collection.objects.link(obj)
    return obj


def booleana(alvo, ferramenta, operacao="UNION"):
    """Uniao pela ferramenta existente, com o retorno CONFERIDO.

    O experimento usou solver EXACT; isso vale para este dominio e nao e solucao
    universal.

    CORRIGIDO depois da terceira revisao: a versao anterior ignorava o retorno do
    operador e apagava a ferramenta mesmo com CANCELLED. Como este arquivo constroi
    a geometria de REFERENCIA dos ensaios, um cancelamento silencioso produziria um
    cenario diferente do descrito, e todo numero medido em cima dele seria sobre
    outra peca."""
    bpy.context.view_layer.objects.active = alvo
    mod = alvo.modifiers.new(name="bool_%s" % operacao.lower(), type="BOOLEAN")
    mod.operation = operacao
    mod.object = ferramenta
    mod.solver = "EXACT"
    nome_do_mod = mod.name
    retorno = bpy.ops.object.modifier_apply(modifier=nome_do_mod)
    estados = sorted(retorno) if hasattr(retorno, "__iter__") else [str(retorno)]
    pendurado = any(m.name == nome_do_mod for m in alvo.modifiers)
    if "FINISHED" not in estados or pendurado:
        raise RuntimeError(
            "a booleana do gerador nao concluiu: operador devolveu %s e o modificador "
            "%s no objeto. O cenario sintetico seria outro, e todo numero medido em "
            "cima dele seria sobre outra peca."
            % (estados, "continua" if pendurado else "saiu"))
    bpy.data.objects.remove(ferramenta, do_unlink=True)
    return alvo


def gera(p):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    L, W = p["comprimento"], p["largura"]
    zb, za, zx = p["altura_da_base"], p["altura_alta"], p["altura_baixa"]
    x1, x2 = p["vao_de"], p["vao_ate"]

    base = caixa(p["nome"], (0, 0, 0), (L, W, zb))
    alto = caixa("_patamar_alto", (0, 0, zb), (x1, W, za))
    baixo = caixa("_patamar_baixo", (x2, 0, zb), (L, W, zx))
    booleana(base, alto)
    booleana(base, baixo)

    if abs(p["rotacao_z_graus"]) > 1e-9:
        import math
        base.rotation_euler[2] = math.radians(p["rotacao_z_graus"])

    bpy.context.view_layer.objects.active = base
    base.select_set(True)

    # os limites que a receita tem que reencontrar sozinha, guardados aqui SO para
    # o teste poder conferir o resultado contra o valor conhecido
    gabarito = {
        "objeto": base.name,
        "topo_do_patamar_alto": {"x_de": 0.0, "x_ate": x1, "z": za},
        "topo_do_patamar_baixo": {"x_de": x2, "x_ate": L, "z": zx},
        "vao": {"x_de": x1, "x_ate": x2, "z_do_piso": zb,
                "largura_em_y": W,
                "queda_esperada_da_rampa": round(za - zx, 6),
                "comprimento_do_vao": round(x2 - x1, 6)},
        "volume_da_peca_antes": round(float(base_volume(base)), 6),
        "rotacao_z_graus": p["rotacao_z_graus"],
    }
    return base, gabarito


def base_volume(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return bm.calc_volume()
    finally:
        bm.free()


def medidas(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return {"vertices": len(bm.verts), "faces": len(bm.faces),
                "arestas_abertas": sum(1 for e in bm.edges if len(e.link_faces) == 1),
                "arestas_nao_manifold": sum(1 for e in bm.edges if len(e.link_faces) > 2),
                "faces_degeneradas": sum(1 for f in bm.faces if f.calc_area() <= 1e-9),
                "volume": round(bm.calc_volume(), 6)}
    finally:
        bm.free()


def destino_do_resultado(argv, do_arquivo=None):
    """Caminho onde este script tem que gravar o relatorio.

    Le a bandeira NOMEADA `--resultado-em`, que `roda_blender.py --passa-resultado`
    acrescenta. Nomeada de proposito: a versao anterior lia `argv[1]`, e com dois
    argumentos do chamador o script gravava sobre o segundo argumento dele."""
    if ROTULO_DO_RESULTADO in argv:
        i = argv.index(ROTULO_DO_RESULTADO)
        if i + 1 < len(argv) and argv[i + 1]:
            return argv[i + 1]
    return do_arquivo


ROTULO_DO_RESULTADO = "--resultado-em"


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = dict(PADRAO)
    if argv and not argv[0].startswith("--"):
        p.update(json.load(open(argv[0], encoding="utf-8")))
    # A bandeira `--resultado-em` MANDA no destino do relatorio, e e o que o
    # `--passa-resultado` do roda_blender.py preenche, para o caminho nao ter que ser
    # escrito duas vezes e poder divergir entre as duas grafias.
    p["saida_relatorio"] = destino_do_resultado(argv, p.get("saida_relatorio"))
    # CORRIGIDO depois da quinta revisao: este arquivo era apresentado como exemplo
    # COMPLETO do contrato do script de dentro do Blender, e nao cumpria duas das
    # quatro obrigacoes — nao capturava excecao e nao emitia veredito. Com o lancador
    # desanexado, um erro aqui nao deixava vestigio: nem arquivo, nem codigo, nada.
    rel = {"parametros": p,
           "aviso": ("dimensoes escolhidas para este exemplo sintetico; nenhuma "
                     "provem de projeto real")}
    try:
        obj, gabarito = gera(p)
        rel["gabarito"] = gabarito
        rel["medidas"] = medidas(obj)
        if p.get("saida_blend"):
            os.makedirs(os.path.dirname(p["saida_blend"]) or ".", exist_ok=True)
            retorno = bpy.ops.wm.save_as_mainfile(filepath=p["saida_blend"], copy=True)
            estados = sorted(retorno) if hasattr(retorno, "__iter__") else [str(retorno)]
            if "FINISHED" not in estados or not os.path.isfile(p["saida_blend"]):
                raise RuntimeError("o salvamento da cena nao concluiu: %s" % estados)
            rel["blend"] = p["saida_blend"]
            rel["bytes_do_blend"] = os.path.getsize(p["saida_blend"])
        rel["veredito_global"] = "ATENDIDO"
    except Exception as e:                                       # noqa: BLE001
        rel["veredito_global"] = "ERRO"
        rel["erro"] = {"tipo": type(e).__name__, "mensagem": str(e)}
        import traceback
        rel["traceback"] = traceback.format_exc()[-2000:]

    # grava SEMPRE, inclusive no caminho de erro: e o que torna a falha visivel para
    # quem chamou, e o que `--exigir veredito_global=ATENDIDO` transforma em codigo
    # de saida nao zero
    if p.get("saida_relatorio"):
        os.makedirs(os.path.dirname(p["saida_relatorio"]) or ".", exist_ok=True)
        open(p["saida_relatorio"], "w", encoding="utf-8").write(
            json.dumps(rel, ensure_ascii=False, indent=1))
    else:
        print(json.dumps(rel, ensure_ascii=False, indent=1))
    if rel["veredito_global"] != "ATENDIDO":
        raise SystemExit(1)
