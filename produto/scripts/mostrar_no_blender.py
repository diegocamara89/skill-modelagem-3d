"""Mostra peças no Blender do operador, para qualquer agente (Codex, Claude, agy).

Abre o Blender se estiver fechado e espera o servidor MCP. Na cena TRABALHO_AGENTE, cria o objeto AG_<arquivo> ou só
troca a malha dele: depois da primeira vez, nunca troca a cena da janela nem a vista. Confere peso do volume sólido e
contato com a mesa (mapa_balanco.py). Marca A/B no modelo para pedir medida.

Peça por código (ao vivo): passe o gera.py (PARAMS + def gera(**medidas) -> Manifold). Ele vira o objeto
AG_<pasta>_<arquivo> com painel de medidas e acabamentos (blender/ponte_peca.py); chamar de novo recarrega o código e
mantém as medidas e acabamentos que o operador já mexeu. --exportar grava o STL da peça como está no Blender.

Um Blender por sessão: a porta vem de porta_sessao.py; se o Blender desta sessão não estiver aberto, abre um novo.

Uso:
  python mostrar_no_blender.py gera.py [--exportar peca.stl]
  python mostrar_no_blender.py peca.stl [outra.stl ...] [--sem-conferir] [--material PETG|PLA]
  python mostrar_no_blender.py --marcar A=10,0,5 B=30,0,5 [--limpar-marcas]
Saída: uma linha JSON. estado: MOSTRADO | MOSTRADO_AO_VIVO | ERRO_NO_GERA | MARCADO | BLENDER_SEM_MCP
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import ponte_letras  # noqa: E402
from mcp_blender import PORTA_PADRAO, chama  # noqa: E402
import porta_sessao  # noqa: E402
from roda_blender import acha_blender  # noqa: E402

DENSIDADE = {"PETG": 1.27, "PLA": 1.24}  # g/cm³


# Roda dentro do Blender recém-aberto: liga o servidor MCP na porta desta sessão (o início automático usaria a 9876).
LIGA_NA_PORTA = """import bpy
P = {porta}
def _liga():
    bpy.context.scene.blendermcp_port = P
    srv = getattr(bpy.types, "blendermcp_server", None)
    if srv and getattr(srv, "port", P) != P:
        bpy.ops.blendermcp.stop_server(); srv = None
    if not srv or not srv.running:
        bpy.ops.blendermcp.start_server()
bpy.context.scene.blendermcp_port = P
bpy.app.timers.register(_liga, first_interval=2.0)
"""


def garante_blender(espera_s=90):
    """Blender DESTA sessão (porta própria, porta_sessao.py); abre um novo se ele não estiver escutando."""
    estado = chama("get_scene_info", tempo_limite=5).get("estado")
    if estado == "OK":
        return {"abriu": False, "porta": PORTA_PADRAO}
    if estado != "SEM_SERVIDOR":
        return {"erro": f"o Blender da porta {PORTA_PADRAO} respondeu {estado} (ocupado?): tente de novo em instantes"}
    exe, como = acha_blender()
    if not exe:
        return {"erro": como}
    # Blender desta porta já abrindo (outra chamada há pouco): espera ele em vez de empilhar outra janela
    abrindo = porta_sessao.PASTA / f"abrindo-{PORTA_PADRAO}.txt"
    try:
        recente = time.time() - float(abrindo.read_text(encoding="utf-8")) < espera_s + 30
    except (OSError, ValueError):
        recente = False
    if not recente:
        porta_sessao.PASTA.mkdir(parents=True, exist_ok=True)
        abrindo.write_text(str(time.time()), encoding="utf-8")
        subprocess.Popen([exe, "--python-expr", LIGA_NA_PORTA.format(porta=PORTA_PADRAO)],
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    fim = time.time() + espera_s
    while time.time() < fim:
        time.sleep(2)
        if chama("get_scene_info", tempo_limite=5).get("estado") == "OK":
            return {"abriu": True, "porta": PORTA_PADRAO}
    return {"erro": f"o Blender abriu, mas o servidor MCP não respondeu em {espera_s} s: "
                    "confira 'Auto-Start Server' no painel BlenderMCP"}


PONTE = (AQUI.parent / "blender" / "ponte_peca.py").resolve()
CARREGA_PONTE = """import bpy, sys, os, json, importlib.util
CAM = r"{ponte}"
m = sys.modules.get("ponte_peca")
if m is None or getattr(m, "_mtime", 0) != os.path.getmtime(CAM):
    spec = importlib.util.spec_from_file_location("ponte_peca", CAM)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m._mtime = os.path.getmtime(CAM); sys.modules["ponte_peca"] = m; m.registra()
print("PONTE=" + json.dumps(m.carrega(r"{gera}", {objeto!r}, {rotulo!r}, {exportar!r})))
"""


def mostra_gera(gera, exportar=None):
    """gera.py vira peça ao vivo no Blender desta sessão (blender/ponte_peca.py)"""
    gera = pathlib.Path(gera).resolve()
    objeto = f"AG_{gera.parent.name}_{gera.stem}"[:60]
    sid = porta_sessao.sessao()
    rotulo = f"Sessão {sid[:8]} · porta {PORTA_PADRAO}" if sid else f"porta {PORTA_PADRAO}"
    codigo = CARREGA_PONTE.format(ponte=PONTE, gera=gera, objeto=objeto, rotulo=rotulo,
                                  exportar=str(pathlib.Path(exportar).resolve()) if exportar else None)
    r = chama("execute_code", {"code": codigo}, tempo_limite=60, permitir_escrita=True)
    texto = ((r.get("resultado") or {}).get("result") or "") if r.get("estado") == "OK" else ""
    linha = next((l for l in texto.splitlines() if l.startswith("PONTE=")), None)
    return json.loads(linha[6:]) if linha else {"estado": "ERRO_NA_PONTE", "resposta": r}


def pontos(itens):
    """['A=10,0,5'] -> {'A': [10.0, 0.0, 5.0]}"""
    r = {}
    for it in itens:
        letra, xyz = it.split("=", 1)
        r[letra.strip().upper()] = [float(v) for v in xyz.split(",")]
    return r


def confere(stl, material="PETG"):
    nome = pathlib.Path(stl).name
    linhas = []
    try:
        import trimesh
        m = trimesh.load(stl, force="mesh")
        if m.is_watertight:
            g = abs(m.volume) / 1000 * DENSIDADE[material]
            linhas.append(f"{nome}: volume sólido ≈ {g:.1f} g de {material} (peça maciça; o fatiador dá menos)")
        else:
            linhas.append(f"{nome}: malha aberta, peso não calculado")
    except Exception as e:
        linhas.append(f"{nome}: peso não calculado ({e})")
    r = subprocess.run([sys.executable, str(AQUI / "mapa_balanco.py"), stl], capture_output=True, timeout=120,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    sem_contato = [l.strip() for l in r.stdout.decode("utf-8", "replace").splitlines() if "<<<" in l]
    linhas += [f"{nome}: {l}" for l in sem_contato[:5]]
    if r.returncode == 0 and not sem_contato:
        linhas.append(f"{nome}: todo corpo encosta na mesa (mapa_balanco)")
    return linhas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stls", nargs="*", help="STLs e/ou gera.py")
    ap.add_argument("--exportar", help="com um gera.py: grava o STL da peça como está no Blender")
    ap.add_argument("--marcar", nargs="*", default=[])
    ap.add_argument("--limpar-marcas", action="store_true")
    ap.add_argument("--sem-conferir", action="store_true")
    ap.add_argument("--material", default="PETG", choices=sorted(DENSIDADE))
    a = ap.parse_args(argv)
    g = garante_blender()
    if "erro" in g:
        return {"estado": "BLENDER_SEM_MCP", "motivo": g["erro"]}
    out = {"estado": "MARCADO", "abriu_blender": g["abriu"], "porta": g["porta"] if "porta" in g else PORTA_PADRAO}
    geras = [s for s in a.stls if s.lower().endswith(".py")]
    if geras:
        pecas = [mostra_gera(p, a.exportar if len(geras) == 1 else None) for p in geras]
        out.update(pecas[0] if len(pecas) == 1 else {"estado": "MOSTRADO_AO_VIVO", "pecas": pecas})
    if any(not s.lower().endswith(".py") for s in a.stls):
        stls = [str(pathlib.Path(s).resolve()) for s in a.stls if not s.lower().endswith(".py")]
        out.update(ponte_letras.executa("mostrar", stls=stls))
        if not a.sem_conferir:
            out["conferencia"] = [l for s in stls for l in confere(s, a.material)]
    if a.marcar or a.limpar_marcas:
        out["marcas"] = ponte_letras.executa("marcar", pontos=pontos(a.marcar), limpar=a.limpar_marcas)
    if geras and any(p.get("estado") != "MOSTRADO_AO_VIVO" for p in pecas):  # erro no gera.py não some atrás do STL
        out.update(estado="ERRO_NO_GERA", pecas=pecas)
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(main(), ensure_ascii=False, default=str))
