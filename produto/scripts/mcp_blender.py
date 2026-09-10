# -*- coding: utf-8 -*-
"""mcp_blender.py - cliente minimo do socket do complemento MCP do Blender.

RODA FORA DO BLENDER, no Python do hospedeiro.

POR QUE ESTE ARQUIVO EXISTE. A referencia descreve o protocolo do MCP comunitario —
socket TCP em 127.0.0.1:9876, `{"type": ..., "params": {...}}` de ida,
`{"status": "success", "result": {...}}` de volta — e o pacote nao trazia cliente.
O agente tinha que escrever um, e escrever leitura incremental de JSON em socket e
justamente o trecho mecanico fragil que a receita nao deve deixar para ele
improvisar. Uma revisao independente apontou isso.

Isto NAO e servidor MCP proprio nem proxy: e cliente do que ja existe.

**Somente leitura por padrao.** A cena e do usuario, e pode ter alteracao nao salva.
Comando que muda a cena exige `permitir_escrita=True` explicito, e a lista de
comandos de leitura conhecidos esta em LEITURA.

Estados possiveis, e nenhum deles e "deu certo" por ausencia de excecao:

  OK                 resposta valida do complemento
  SEM_SERVIDOR       nada escutando na porta: o Blender esta fechado, ou o
                     complemento nao esta ativo
  TEMPO_ESGOTADO     conectou e nao respondeu no prazo. NAO prova que o codigo
                     parou dentro do Blender: inspecione antes de repetir
  RESPOSTA_ILEGIVEL  respondeu algo que nao e JSON completo
  ERRO_DO_ADDON      respondeu com status de erro
  ESCRITA_BARRADA    comando que altera a cena sem permissao explicita

Uso:
    python scripts/mcp_blender.py get_scene_info
    python scripts/mcp_blender.py get_object_info --params '{"name": "Cubo"}'
    python scripts/mcp_blender.py --testa-conexao
"""
import argparse
import json
import socket
import sys

HOST_PADRAO = "127.0.0.1"
PORTA_PADRAO = 9876
TEMPO_PADRAO = 30.0

# Comandos que apenas LEEM. Qualquer coisa fora desta lista e tratada como
# potencialmente destrutiva, o que e o padrao seguro: errar para o lado de barrar.
LEITURA = ("get_scene_info", "get_object_info", "get_viewport_screenshot",
           "get_polyhaven_status")


def chama(tipo, params=None, host=HOST_PADRAO, porta=PORTA_PADRAO,
          tempo_limite=TEMPO_PADRAO, permitir_escrita=False):
    """Uma chamada ao complemento. Devolve dicionario com 'estado' sempre presente."""
    if tipo not in LEITURA and not permitir_escrita:
        return {"estado": "ESCRITA_BARRADA", "tipo": tipo,
                "comandos_de_leitura_conhecidos": list(LEITURA),
                "motivo": ("%r nao esta na lista de comandos de leitura, e a cena e do "
                           "usuario, possivelmente com alteracao nao salva. Se for "
                           "mesmo para alterar, passe permitir_escrita=True e diga ao "
                           "usuario o que vai mudar." % tipo)}
    pedido = json.dumps({"type": tipo, "params": params or {}}).encode("utf-8")
    try:
        s = socket.create_connection((host, porta), timeout=tempo_limite)
    except (ConnectionRefusedError, OSError) as e:
        return {"estado": "SEM_SERVIDOR", "endereco": "%s:%s" % (host, porta),
                "causa": "%s: %s" % (type(e).__name__, e),
                "o_que_conferir": ("o Blender esta aberto? o complemento esta ativo e "
                                   "com o servidor iniciado? Falha de conexao NAO "
                                   "prova complemento antigo: nao reinstale por "
                                   "inferencia.")}
    try:
        s.settimeout(tempo_limite)
        s.sendall(pedido)
        pedacos = []
        while True:
            try:
                b = s.recv(65536)
            except socket.timeout:
                return {"estado": "TEMPO_ESGOTADO", "segundos": tempo_limite,
                        "bytes_recebidos": sum(len(x) for x in pedacos),
                        "aviso": ("tempo esgotado NAO prova que o codigo parou dentro "
                                  "do Blender. Inspecione o estado antes de repetir, e "
                                  "nunca encerre a sessao do usuario para cumprir "
                                  "prazo.")}
            if not b:
                break
            pedacos.append(b)
            bruto = b"".join(pedacos)
            try:
                resposta = json.loads(bruto.decode("utf-8", "replace"))
            except ValueError:
                continue                      # resposta ainda incompleta
            return _interpreta(resposta, tipo)
        bruto = b"".join(pedacos)
        if not bruto:
            return {"estado": "RESPOSTA_ILEGIVEL", "motivo": "conexao fechada vazia"}
        try:
            return _interpreta(json.loads(bruto.decode("utf-8", "replace")), tipo)
        except ValueError as e:
            return {"estado": "RESPOSTA_ILEGIVEL", "causa": "%s: %s" % (type(e).__name__, e),
                    "inicio_do_bruto": bruto[:200].decode("utf-8", "replace")}
    finally:
        try:
            s.close()
        except OSError:
            pass


def _interpreta(resposta, tipo):
    if not isinstance(resposta, dict):
        return {"estado": "RESPOSTA_ILEGIVEL",
                "motivo": "resposta nao e objeto: %s" % type(resposta).__name__}
    status = resposta.get("status")
    if status == "success":
        return {"estado": "OK", "tipo": tipo, "resultado": resposta.get("result")}
    return {"estado": "ERRO_DO_ADDON", "tipo": tipo, "status": status,
            "mensagem": resposta.get("message") or resposta.get("error"),
            "resposta": resposta}


def testa_conexao(host=HOST_PADRAO, porta=PORTA_PADRAO, tempo_limite=10.0):
    """Teste de conexao por LEITURA. Nao altera nada."""
    r = chama("get_scene_info", host=host, porta=porta, tempo_limite=tempo_limite)
    if r["estado"] != "OK":
        return r
    res = r.get("resultado") or {}
    return {"estado": "OK", "endereco": "%s:%s" % (host, porta),
            "cena": res.get("name"),
            "objetos": res.get("object_count"),
            "nota": ("conexao provada por LEITURA. Isto nao autoriza alterar a cena: "
                     "ela e do usuario.")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tipo", nargs="?")
    ap.add_argument("--params", default=None)
    ap.add_argument("--host", default=HOST_PADRAO)
    ap.add_argument("--porta", type=int, default=PORTA_PADRAO)
    ap.add_argument("--tempo-limite", type=float, default=TEMPO_PADRAO)
    ap.add_argument("--permitir-escrita", action="store_true")
    ap.add_argument("--testa-conexao", action="store_true")
    a = ap.parse_args()
    if a.testa_conexao:
        r = testa_conexao(a.host, a.porta)
    else:
        if not a.tipo:
            ap.error("informe o comando, ou use --testa-conexao")
        try:
            params = json.loads(a.params) if a.params else {}
        except ValueError as e:
            print(json.dumps({"estado": "PARAMS_ILEGIVEIS",
                              "causa": "%s: %s" % (type(e).__name__, e),
                              "recebido": a.params,
                              "esperado": "objeto JSON, por exemplo: {\"name\": \"Cubo\"}"},
                             ensure_ascii=False, indent=1))
            return 1
        if not isinstance(params, dict):
            print(json.dumps({"estado": "PARAMS_ILEGIVEIS",
                              "causa": "params tem que ser objeto, e veio %s"
                                       % type(params).__name__},
                             ensure_ascii=False, indent=1))
            return 1
        r = chama(a.tipo, params, a.host, a.porta, a.tempo_limite, a.permitir_escrita)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:8000])
    return 0 if r.get("estado") == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
