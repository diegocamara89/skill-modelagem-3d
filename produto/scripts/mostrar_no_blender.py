"""Mostra peças no Blender do operador, para qualquer agente (Codex, Claude, agy).

Abre o Blender se estiver fechado e espera o servidor MCP. Na cena TRABALHO_AGENTE, cria o objeto AG_<arquivo> ou só
troca a malha dele: depois da primeira vez, nunca troca a cena da janela nem a vista. Confere peso do volume sólido e
contato com a mesa (mapa_balanco.py). Marca A/B no modelo para pedir medida.

Uso:
  python mostrar_no_blender.py peca.stl [outra.stl ...] [--sem-conferir] [--material PETG|PLA]
  python mostrar_no_blender.py --marcar A=10,0,5 B=30,0,5 [--limpar-marcas]
Saída: uma linha JSON. estado: MOSTRADO | MARCADO | BLENDER_SEM_MCP
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
from mcp_blender import chama  # noqa: E402
from roda_blender import acha_blender  # noqa: E402

DENSIDADE = {"PETG": 1.27, "PLA": 1.24}  # g/cm³


def blender_rodando():
    """Há algum processo do Blender aberto? (abrir outro por cima só empilha janelas)"""
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq blender.exe", "/NH"], capture_output=True, timeout=15)
        return b"blender.exe" in r.stdout.lower()
    except (OSError, subprocess.TimeoutExpired):
        return False


def garante_blender(espera_s=90):
    estado = chama("get_scene_info", tempo_limite=5).get("estado")
    if estado == "OK":
        return {"abriu": False}
    if estado != "SEM_SERVIDOR":
        return {"erro": f"o Blender está aberto, mas o MCP respondeu {estado} (ocupado?): tente de novo em instantes"}
    if blender_rodando():
        return {"erro": "o Blender está aberto, mas o servidor MCP está desligado: ligue 'Connect to MCP server' "
                        "no painel BlenderMCP (ou 'Auto-Start Server')"}
    exe, como = acha_blender()
    if not exe:
        return {"erro": como}
    subprocess.Popen([exe], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    fim = time.time() + espera_s
    while time.time() < fim:
        time.sleep(2)
        if chama("get_scene_info", tempo_limite=5).get("estado") == "OK":
            return {"abriu": True}
    return {"erro": f"o Blender abriu, mas o servidor MCP não respondeu em {espera_s} s: "
                    "confira 'Auto-Start Server' no painel BlenderMCP"}


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
    ap.add_argument("stls", nargs="*")
    ap.add_argument("--marcar", nargs="*", default=[])
    ap.add_argument("--limpar-marcas", action="store_true")
    ap.add_argument("--sem-conferir", action="store_true")
    ap.add_argument("--material", default="PETG", choices=sorted(DENSIDADE))
    a = ap.parse_args(argv)
    g = garante_blender()
    if "erro" in g:
        return {"estado": "BLENDER_SEM_MCP", "motivo": g["erro"]}
    out = {"estado": "MARCADO", "abriu_blender": g["abriu"]}
    if a.stls:
        stls = [str(pathlib.Path(s).resolve()) for s in a.stls]
        out.update(ponte_letras.executa("mostrar", stls=stls))
        if not a.sem_conferir:
            out["conferencia"] = [l for s in stls for l in confere(s, a.material)]
    if a.marcar or a.limpar_marcas:
        out["marcas"] = ponte_letras.executa("marcar", pontos=pontos(a.marcar), limpar=a.limpar_marcas)
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(main(), ensure_ascii=False, default=str))
