"""Um Blender por sessão de agente: cada sessão fala com o seu Blender, numa porta própria.

RODA FORA DO BLENDER. Usado por mcp_blender.py (porta padrão) e por mostrar_no_blender.py (abrir o Blender certo).

A sessão vem de MODS_SESSAO (o gancho passa), CLAUDE_CODE_SESSION_ID (Claude Code) ou CODEX_SESSION_ID.
Sem sessão conhecida, usa 9876, como antes. Porta que já escuta e não está no registro é de alguém: não é tomada.

Uso:
  python porta_sessao.py                 # porta desta sessão
  python porta_sessao.py --registra 9876 # liga esta sessão a um Blender já aberto nessa porta
  python porta_sessao.py --lista
"""
import argparse
import contextlib
import json
import os
import pathlib
import socket
import time

PASTA = pathlib.Path(os.environ.get("LOCALAPPDATA") or pathlib.Path.home()) / "mods-diego"
REGISTRO = PASTA / "blender-sessoes.json"
PRIMEIRA, ULTIMA = 9876, 9899


def sessao():
    return (os.environ.get("MODS_SESSAO") or os.environ.get("CLAUDE_CODE_SESSION_ID")
            or os.environ.get("CODEX_SESSION_ID") or "")


def escutando(porta):
    with contextlib.suppress(OSError), socket.create_connection(("127.0.0.1", porta), timeout=0.3):
        return True
    return False


@contextlib.contextmanager
def _trava():
    """duas sessões alocando ao mesmo tempo não pegam a mesma porta"""
    PASTA.mkdir(parents=True, exist_ok=True)
    trava = REGISTRO.with_suffix(".trava")
    for _ in range(300):  # até 30 s: cada porta sondada pelo dono da trava custa até 0,3 s
        try:
            fd = os.open(trava, os.O_CREAT | os.O_EXCL)
            break
        except FileExistsError:
            with contextlib.suppress(FileNotFoundError):  # o dono pode soltar entre o open e o stat
                if time.time() - trava.stat().st_mtime > 40:  # trava largada por processo que morreu
                    trava.unlink(missing_ok=True)
            time.sleep(0.1)
    else:
        raise RuntimeError(f"registro de portas travado: {trava}")
    try:
        yield
    finally:
        os.close(fd)
        trava.unlink(missing_ok=True)


def _le():
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _grava(reg):
    tmp = REGISTRO.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=1), encoding="utf-8")
    os.replace(tmp, REGISTRO)


def porta(sid=None):
    sid = sid or sessao()
    if not sid:
        return PRIMEIRA
    with _trava():
        reg = _le()
        if sid in reg:
            return reg[sid]["porta"]
        # reserva de outra sessão sem Blender escutando há mais de 30 min fica livre
        reg = {k: v for k, v in reg.items() if time.time() - v.get("t", 0) < 1800 or escutando(v["porta"])}  # idade primeiro: sondar custa 0,3 s
        usadas = {v["porta"] for v in reg.values()}
        for p in range(PRIMEIRA, ULTIMA + 1):
            if p not in usadas and not escutando(p):
                reg[sid] = {"porta": p, "desde": time.strftime("%Y-%m-%d %H:%M"), "t": time.time()}
                _grava(reg)
                return p
    raise RuntimeError(f"nenhuma porta livre entre {PRIMEIRA} e {ULTIMA}")


def registra(p, sid=None):
    sid = sid or sessao()
    with _trava():
        reg = {k: v for k, v in _le().items() if v["porta"] != p}
        reg[sid] = {"porta": p, "desde": time.strftime("%Y-%m-%d %H:%M"), "t": time.time()}
        _grava(reg)
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--registra", type=int)
    ap.add_argument("--lista", action="store_true")
    a = ap.parse_args()
    if a.lista:
        print(json.dumps({k: {**v, "escutando": escutando(v["porta"])} for k, v in _le().items()}, indent=1))
    else:
        print(registra(a.registra) if a.registra else porta())
