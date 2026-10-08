"""Copia o complemento bancada_viva para cada Blender instalado e o liga nas preferências (persistente).
Depois disso as letras A, B, C e as marcas do agente aparecem a cada abertura do Blender, sem ninguém lembrar.

Uso: python instala_bancada_viva.py [--so-copiar]
Ligar exige o Blender aberto com o servidor MCP (127.0.0.1:9876)."""
import glob
import json
import os
import pathlib
import shutil
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from mcp_blender import chama  # noqa: E402

FONTE = AQUI.parent / "blender" / "bancada_viva.py"
LIGA = ("import addon_utils, bpy, json\n"
        "addon_utils.modules(refresh=True)\n"
        "addon_utils.enable('bancada_viva', default_set=True, persistent=True)\n"
        "bpy.ops.wm.save_userpref()\n"
        "print('BANCADA=' + json.dumps({'ligado': list(addon_utils.check('bancada_viva')), "
        "'letras': bool(bpy.app.driver_namespace.get('poc_letras_handler'))}))")


def pastas_de_addons():
    """scripts/addons de cada Blender: Microsoft Store (pasta virtualizada) e instalador comum."""
    loc, roam = os.environ.get("LOCALAPPDATA", ""), os.environ.get("APPDATA", "")
    padroes = [os.path.join(loc, "Packages", "BlenderFoundation.Blender_*", "LocalCache", "Roaming",
                            "Blender Foundation", "Blender", "*", "scripts", "addons"),
               os.path.join(roam, "Blender Foundation", "Blender", "*", "scripts", "addons")]
    return sorted({p for pad in padroes for p in glob.glob(pad)})


def instala(so_copiar=False):
    destinos = pastas_de_addons()
    if not destinos:
        return {"estado": "SEM_BLENDER", "motivo": "nenhuma pasta scripts/addons do Blender achada"}
    for d in destinos:
        shutil.copy2(FONTE, os.path.join(d, "bancada_viva.py"))
    if so_copiar:
        return {"estado": "COPIADO", "destinos": destinos}
    r = chama("execute_code", {"code": LIGA}, permitir_escrita=True)
    texto = json.dumps(r, ensure_ascii=False, default=str)
    return {"estado": "LIGADO" if "BANCADA=" in texto and r.get("estado") == "OK" else r.get("estado"),
            "destinos": destinos, "resposta": r}


if __name__ == "__main__":
    print(json.dumps(instala("--so-copiar" in sys.argv), ensure_ascii=False, indent=1, default=str))
