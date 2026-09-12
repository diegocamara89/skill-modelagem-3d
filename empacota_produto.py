# -*- coding: utf-8 -*-
"""empacota_produto.py - monta o pacote distribuivel por LISTA DE PERMISSAO.

Fica FORA de produto/: e ferramenta de oficina, nao faz parte do produto.

POR QUE POR PERMISSAO, E NUNCA POR EXCLUSAO. Em M0, uma revisao externa encontrou
dados de projeto privado dentro da pasta de prototipos: nome de arquivo de
referencia, hash, cotas, e uma normal e um centroide reais dentro do exemplo de uso
de uma ferramenta distribuida. A causa raiz nao foi descuido pontual: foi empacotar
por exclusao. Quem empacota a pasta inteira publica tudo o que caiu nela.

Uso:
  python empacota_produto.py --verificar                 # audita, nao escreve
  python empacota_produto.py --destino ..\\pacote_teste   # monta, se limpo
  python empacota_produto.py --verificar --json rel.json # audita e grava relatorio
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(AQUI, "produto")      # sobrescrito por --origem

# Somente estes vao. Caminho relativo a produto/.
PERMITIDOS = [
    "scripts/selecao_regiao.py",
    "scripts/selecionar_regiao.py",
    "scripts/operador_local.py",
    "scripts/extrusao_regiao.py",
    "scripts/extrudar_selecao.py",
    "scripts/alinhamento_regiao.py",
    "scripts/alinhar_selecao.py",
    "scripts/preenchimento_regiao.py",
    "scripts/preencher_selecao.py",
    "scripts/arredondamento_regiao.py",
    "scripts/arredondar_selecao.py",
    "referencias/expandir_selecao.md",
    "referencias/extrudar_selecao.md",
    "referencias/alinhar_selecao.md",
    "referencias/preencher_selecao.md",
    "referencias/arredondar_selecao.md",
    "referencias/fluxo_interativo.md",
    "SKILL.md",
    "INVENTARIO.json",
    "LICENSE",
    "referencias/criar_e_parametrizar.md",
    "referencias/editar_localizado.md",
    "referencias/inspecionar_e_selecionar.md",
    "referencias/mapa_de_ferramentas.md",
    "referencias/recuperar_salvar_exportar.md",
    "referencias/registro_de_trabalho.md",
    "referencias/verificar.md",
    "referencias/sessao_e_edicao_guiada.md",
    "scripts/bl_ferramentas.py",
    "scripts/mcp_blender.py",
    "scripts/mover_regiao.py",
    "scripts/mover_selecao.py",
    "referencias/mover_selecao.md",
    "scripts/roda_blender.py",
    "scripts/valida_requisitos.py",
    "scripts/testa_paridade_validador.py",
    "scripts/extrai_tolerancias.py",
    "scripts/edicao_guiada.py",
    "scripts/sessao_blender.py",
    "scripts/executa_com_relatorio.py",
    "scripts/trabalho_blender.py",
    "cenarios/ensaio_preenchimento.py",
    "cenarios/familia_exemplo.py",
    "cenarios/gera_cenario.py",
    "cenarios/exemplo_edicao_guiada.py",
    "verificadores/PROVENIENCIA.json",
    "verificadores/check_intent.py",
    "verificadores/check_mesh.py",
    "verificadores/matriz.py",
    "verificadores/secoes.py",
    "verificadores/sweep_params.py",
]

# Nunca vao, e a lista existe para a promessa ser conferivel, nao decorativa.
NEGADOS = ["__pycache__", ".pyc", "padroes_de_vazamento.json",
           "M0_RESULTADO.md", "M1_RESULTADO.md", "M2_RESULTADO.md",
           "M3_RESULTADO.md", "PLANO_IMPLEMENTACAO_PLUGIN.md", "DESENHO_PLUGIN.md",
           "DESENHO.md", "REFERENCIA_BLENDER_EDICAO_GUIADA.md",
           "REVISAO_M1_CONTEXTO.md", "LACUNAS_PARA_M2.md", "PENDENCIAS_PRODUTO.md",
           "base_congelada", "base_pos_m0", "evidencias_m1", "evidencias_finais",
           "cenas_de_teste",
           "prototipo"]

ARQUIVO_DE_PADROES = os.path.join(AQUI, "prototipo", "padroes_de_vazamento.json")


def carrega_padroes():
    """Padroes que nomeiam o projeto privado. Ficam FORA do pacote, de proposito.

    A estrutura do arquivo e [[regex, descricao], ...]. Extrair errado ja custou uma
    auditoria vazia: numa tentativa a extracao devolveu zero padroes e a varredura
    reportou "0 achados" sobre padrao nenhum. Por isso o controle positivo abaixo
    nao e opcional."""
    if not os.path.isfile(ARQUIVO_DE_PADROES):
        return [], "arquivo de padroes ausente: a varredura NAO pode ser feita"
    d = json.load(io.open(ARQUIVO_DE_PADROES, encoding="utf-8"))
    rx = []
    for x in d.get("padroes") or []:
        if isinstance(x, str):
            rx.append(x)
        elif isinstance(x, (list, tuple)) and x and isinstance(x[0], str):
            rx.append(x[0])
    return rx, None


def semente_de_controle():
    """Termo que o controle positivo usa, lido do arquivo LOCAL de padroes.

    CORRIGIDO em 08/09/2026: a semente estava cravada aqui, e e um token do projeto
    privado. O comentario ao lado dizia "fica FORA do pacote" — e ficava, este arquivo
    nao entra no pacote. Mas fora do PACOTE nao e fora do REPOSITORIO, e subir o
    repositorio levaria o token. Achado por varredura do repositorio inteiro, feita
    antes de criar um remoto."""
    if not os.path.isfile(ARQUIVO_DE_PADROES):
        return None
    try:
        d = json.load(io.open(ARQUIVO_DE_PADROES, encoding="utf-8"))
    except ValueError:
        return None
    return d.get("semente_de_controle")


def controle_da_varredura(regexes):
    """Prova que a varredura encontra algo quando ha algo. Sem isto, "nenhum achado"
    pode ser varredura quebrada, e foi."""
    if not regexes:
        return {"varredura_funciona": False, "motivo": "nenhum padrao carregado"}
    semente = semente_de_controle()
    if not semente:
        return {"varredura_funciona": False,
                "motivo": ("sem semente de controle no arquivo local de padroes: o "
                           "controle positivo NAO pode ser feito, e portanto "
                           "'nenhum achado' nao prova nada")}
    casou = []
    for r in regexes:
        try:
            if re.search(r, "controle: %s" % semente, re.I):
                casou.append(r)
        except re.error:
            pass
    return {"varredura_funciona": bool(casou), "padroes_que_casaram": len(casou),
            "nota": ("semente de controle vem do arquivo LOCAL de padroes, que nao "
                     "entra no pacote nem no repositorio")}


def varre(regexes):
    achados = []
    for rel in PERMITIDOS:
        c = os.path.join(ORIGEM, rel)
        if not os.path.isfile(c):
            continue
        txt = io.open(c, encoding="utf-8", errors="replace").read()
        for r in regexes:
            try:
                m = re.search(r, txt, re.I)
            except re.error:
                continue
            if m:
                achados.append({"arquivo": rel, "padrao": r,
                                "trecho": m.group(0)[:60]})
    return achados


def hashes(base, relativos):
    h = {}
    for rel in relativos:
        c = os.path.join(base, rel)
        if os.path.isfile(c):
            h[rel] = {"sha256": hashlib.sha256(io.open(c, "rb").read()).hexdigest(),
                      "bytes": os.path.getsize(c)}
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--origem", help=("arvore a empacotar. Existe para poder auditar "
                                      "uma COPIA com contaminacao plantada, sem "
                                      "sujar a arvore real."))
    a = ap.parse_args()
    global ORIGEM
    if a.origem:
        ORIGEM = os.path.abspath(a.origem)

    if a.verificar and a.destino:
        raise SystemExit("E_USO: --verificar audita e NAO escreve. Nao combine com "
                         "--destino.")
    if not a.verificar and not a.destino:
        raise SystemExit("E_USO: informe --verificar ou --destino.")

    # o relatorio nunca pode cair dentro do destino, nem sobre uma entrada
    if a.json:
        aj = os.path.normcase(os.path.realpath(os.path.abspath(a.json)))
        if a.destino:
            ad = os.path.normcase(os.path.realpath(os.path.abspath(a.destino)))
            if aj == ad or aj.startswith(ad + os.sep):
                raise SystemExit("E_CAMINHO_NO_DESTINO: o relatorio ficaria dentro do "
                                 "destino, e e gravado depois da auditoria.")
        for rel in PERMITIDOS:
            c = os.path.join(ORIGEM, rel)
            if os.path.isfile(c) and os.path.normcase(
                    os.path.realpath(c)) == aj:
                raise SystemExit("E_CAMINHO_SOBRE_ENTRADA: o relatorio sobrescreveria "
                                 "%s, que esta sendo auditado." % rel)

    duplicados = sorted({f for f in PERMITIDOS if PERMITIDOS.count(f) > 1})
    if duplicados:
        raise SystemExit("E_LISTA: permitidos com entrada repetida: %s" % duplicados)

    faltando = [r for r in PERMITIDOS if not os.path.isfile(os.path.join(ORIGEM, r))]
    existentes = []
    for raiz, dirs, arqs in os.walk(ORIGEM):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in arqs:
            existentes.append(os.path.relpath(os.path.join(raiz, f), ORIGEM)
                              .replace("\\", "/"))
    fora_da_lista = sorted(set(existentes) - set(PERMITIDOS))

    # BYTECODE NA ORIGEM, relatado em vez de ignorado. Achado por validacao
    # adversarial: a enumeracao acima pula `__pycache__` de proposito, e por isso
    # `--verificar` dizia "limpo" sobre uma arvore que continha .pyc com caminhos
    # absolutos do autor. A lista de permissao impede que eles cheguem ao pacote — o
    # destino montado tem zero — mas quem COPIA a pasta de trabalho direto leva os
    # binarios. Isto nao barra o pacote; nomeia o risco de copiar a arvore.
    bytecode_origem = []
    for raiz, _, arqs in os.walk(ORIGEM):
        for f in arqs:
            if f.endswith((".pyc", ".pyo")) or os.path.basename(raiz) == "__pycache__":
                bytecode_origem.append(os.path.relpath(os.path.join(raiz, f), ORIGEM)
                                       .replace("\\", "/"))

    # CONFERENCIA DE HASH NA ORIGEM. Achado por validacao adversarial em 08/09/2026:
    # `--verificar` era apresentado como o teste de integridade e nao conferia hash
    # nenhum — bytes acrescentados a um arquivo sem atualizar o INVENTARIO passavam
    # com codigo 0. Integridade e o manifesto resolvendo, nao a lista de arquivos
    # coincidindo.
    inv_na_origem = {"resolve": None}
    caminho_inv = os.path.join(ORIGEM, "INVENTARIO.json")
    devem = sorted(set(PERMITIDOS) - {"INVENTARIO.json"})
    if not os.path.isfile(caminho_inv):
        inv_na_origem = {"resolve": False, "erro": "INVENTARIO.json ausente na origem"}
    else:
        try:
            inv = json.load(io.open(caminho_inv, encoding="utf-8"))
            decl = inv.get("arquivos") or {}
            faltam_h, divergem_h = [], []
            for rel_, esperado in sorted(decl.items()):
                alvo_ = os.path.join(ORIGEM, rel_.replace("/", os.sep))
                if not os.path.isfile(alvo_):
                    faltam_h.append(rel_)
                    continue
                real = hashlib.sha256(io.open(alvo_, "rb").read()).hexdigest()
                if real != esperado:
                    divergem_h.append(rel_)
            nao_decl = sorted(set(devem) - set(decl))
            a_mais = sorted(set(decl) - set(devem))
            inv_na_origem = {
                "versao_do_pacote": inv.get("versao_do_pacote"),
                "n_declarados": len(decl),
                "n_que_deveriam_ser_declarados": len(devem),
                "nao_declarados": nao_decl, "declarados_a_mais": a_mais,
                "nao_existem": faltam_h, "hash_divergente": divergem_h,
                "resolve": (bool(decl) and not faltam_h and not divergem_h
                            and not nao_decl and not a_mais),
                "o_que_resolve_significa": (
                    "todo arquivo que deve ser identificado ESTA no manifesto, existe "
                    "e tem o hash declarado. Cobertura, e nao apenas ausencia de "
                    "divergencia numa lista possivelmente vazia")}
        except ValueError as e:
            inv_na_origem = {"resolve": False,
                             "erro": "%s: %s" % (type(e).__name__, e)}

    regexes, erro_de_padroes = carrega_padroes()
    controle = controle_da_varredura(regexes)
    achados = varre(regexes)

    out = {
        "origem": ORIGEM,
        "n_permitidos": len(PERMITIDOS),
        "faltando_na_origem": faltando,
        "na_origem_e_fora_da_lista": fora_da_lista,
        "n_padroes": len(regexes),
        "erro_de_padroes": erro_de_padroes,
        "controle_da_varredura": controle,
        "manifesto_na_origem": inv_na_origem,
        "bytecode_na_arvore_de_origem": {
            "arquivos": sorted(bytecode_origem), "quantos": len(bytecode_origem),
            "entra_no_pacote": False,
            "por_que_importa": ("um .pyc guarda o caminho absoluto do fonte, portanto "
                                "carrega nome de usuario e estrutura de pastas. A "
                                "lista de permissao os exclui do pacote, e o destino "
                                "montado tem zero. Quem copia a ARVORE direto, em vez "
                                "de montar o pacote, leva estes arquivos."),
            "o_que_fazer": ("distribuir o DESTINO montado por --destino, nunca a pasta "
                            "de trabalho. Para limpar a arvore: apagar os "
                            "__pycache__.")},
        "achados_de_vazamento": achados,
        "negados_declarados": NEGADOS,
        "autorizacao_de_publicacao": "NAO EMITIDA por esta ferramenta",
        "limite": ("a varredura prova ausencia dos padroes TESTADOS na cobertura "
                   "testada. Nao prova ausencia de qualquer dado privado, e nao "
                   "substitui revisao manual dos recursos novos."),
    }

    # o manifesto da ORIGEM entra no veredito: sem isso, `--verificar` aprovava
    # arquivo alterado sem atualizacao de hash
    limpo = (not faltando and not achados and not erro_de_padroes
             and controle.get("varredura_funciona")
             and bool(inv_na_origem.get("resolve")))
    out["pacote_limpo"] = limpo
    if not limpo:
        out["motivo_de_barrar"] = {
            "faltando": faltando, "achados": len(achados),
            "manifesto_na_origem_resolve": inv_na_origem.get("resolve"),
            "erro_de_padroes": erro_de_padroes,
            "varredura_funciona": controle.get("varredura_funciona")}

    if a.destino and limpo:
        dest = os.path.abspath(a.destino)
        if os.path.isdir(dest) and os.listdir(dest):
            out["pacote_limpo"] = False
            out["erro_de_destino"] = ("o destino %s existe e NAO esta vazio. Monte em "
                                      "diretorio novo: sobra de montagem anterior "
                                      "viaja." % dest)
            limpo = False
        else:
            for rel in PERMITIDOS:
                alvo = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(alvo), exist_ok=True)
                shutil.copy2(os.path.join(ORIGEM, rel), alvo)
            # auditoria do DESTINO extraido, que e o que o usuario recebe
            no_destino = []
            for raiz, dirs, arqs in os.walk(dest):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in arqs:
                    no_destino.append(os.path.relpath(os.path.join(raiz, f), dest)
                                      .replace("\\", "/"))
            # MEDIDO em vez de assumido, depois de uma revisao independente achar
            # que os .pyc da arvore de trabalho carregam o caminho absoluto do
            # autor: eles nao estao no pacote nem no git, e a lista de negados ja
            # os declara — mas "declarado" nao e "conferido". A varredura de
            # arquivos ignora __pycache__ de proposito; esta contagem NAO ignora.
            bytecode = []
            for raiz, _, arqs in os.walk(dest):
                for f in arqs:
                    if f.endswith((".pyc", ".pyo")) or os.path.basename(raiz) == "__pycache__":
                        bytecode.append(os.path.relpath(os.path.join(raiz, f), dest)
                                        .replace("\\", "/"))
            out["bytecode_no_destino"] = {
                "arquivos": sorted(bytecode), "quantos": len(bytecode),
                "por_que_importa": ("um .pyc guarda o caminho absoluto do arquivo de "
                                    "origem, portanto carrega nome de usuario e "
                                    "estrutura de pastas do autor"),
                "esperado": 0}
            sobrando = sorted(set(no_destino) - set(PERMITIDOS))
            sobrando = sorted(set(sobrando) | set(bytecode))
            nao_chegou = sorted(set(PERMITIDOS) - set(no_destino))
            h = hashes(dest, PERMITIDOS)
            iguais = all(h.get(r, {}).get("sha256")
                         == hashes(ORIGEM, [r]).get(r, {}).get("sha256")
                         for r in PERMITIDOS)
            # CORRIGIDO depois da revisao final: a auditoria conferia a lista
            # PERMITIDOS, que e paralela ao manifesto. Agora ela resolve o MANIFESTO
            # do pacote extraido, relativo a raiz dele, que e o contrato portatil que
            # o usuario tem em maos.
            inv_no_destino = os.path.join(dest, "INVENTARIO.json")
            # COBERTURA, e nao apenas ausencia de divergencia. Achado por validacao
            # adversarial: com INVENTARIO substituido por {"arquivos": {}}, a montagem
            # aprovava com `n_declarados: 0, resolve: true`. Lista vazia nao divergindo
            # de nada nao e integridade — e a mesma armadilha do "0 achados" sobre
            # padrao nenhum, que este projeto ja tinha corrigido na varredura.
            devem_ser_declarados = sorted(set(PERMITIDOS) - {"INVENTARIO.json"})
            manifesto = {"resolve": None}
            if os.path.isfile(inv_no_destino):
                try:
                    inv = json.load(io.open(inv_no_destino, encoding="utf-8"))
                    faltam, divergem = [], []
                    for rel, esperado in (inv.get("arquivos") or {}).items():
                        alvo = os.path.join(dest, rel.replace("/", os.sep))
                        if not os.path.isfile(alvo):
                            faltam.append(rel); continue
                        real = hashlib.sha256(io.open(alvo, "rb").read()).hexdigest()
                        if real != esperado:
                            divergem.append(rel)
                    declarados = set((inv.get("arquivos") or {}))
                    nao_declarados = sorted(set(devem_ser_declarados) - declarados)
                    declarados_a_mais = sorted(declarados - set(devem_ser_declarados))
                    manifesto = {
                        "versao_do_pacote": inv.get("versao_do_pacote"),
                        "n_declarados": len(declarados),
                        "n_que_deveriam_ser_declarados": len(devem_ser_declarados),
                        "nao_declarados": nao_declarados,
                        "declarados_a_mais": declarados_a_mais,
                        "nao_resolvem": faltam, "hash_divergente": divergem,
                        "resolve": (bool(declarados) and not faltam and not divergem
                                    and not nao_declarados and not declarados_a_mais),
                        "o_que_resolve_significa": (
                            "todo arquivo que deve ser identificado ESTA no manifesto, "
                            "existe no destino e tem o hash declarado. Cobertura, e nao "
                            "apenas ausencia de divergencia")}
                except ValueError as e:
                    manifesto = {"resolve": False, "erro": "%s: %s" % (type(e).__name__, e)}
            else:
                manifesto = {"resolve": False, "erro": "INVENTARIO.json ausente no destino"}
            out["resolucao_do_manifesto"] = manifesto
            iguais = iguais and bool(manifesto.get("resolve"))
            out["auditoria_do_destino"] = {
                "arquivos_no_destino": sorted(no_destino),
                "sobrando": sobrando, "nao_chegou": nao_chegou,
                "hashes_iguais_a_origem": iguais,
                "hashes": h}
            ok_dest = not sobrando and not nao_chegou and iguais
            out["copiados_para"] = dest if ok_dest else None
            if not ok_dest:
                out["pacote_limpo"] = False
                out["erro_de_destino"] = ("a auditoria do DESTINO reprovou. Nao "
                                          "distribua esta pasta.")
                # CORRIGIDO depois da terceira revisao. A versao anterior parava
                # aqui, devolvia rc=1 e DEIXAVA a copia no lugar. Pasta reprovada que
                # continua no disco e indistinguivel de aprovada para quem olha o
                # diretorio, e foi exatamente isso que aconteceu num ensaio: os
                # testes rodaram dentro de um pacote reprovado sem notar. Um destino
                # que nao passou na auditoria nao pode existir; se nao der para
                # apagar, ele fica com aviso escrito dentro.
                desfeito, motivo = False, None
                try:
                    shutil.rmtree(dest)
                    desfeito = True
                except OSError as e:
                    motivo = "%s: %s" % (type(e).__name__, e)
                    try:
                        io.open(os.path.join(dest, "NAO_DISTRIBUIR.txt"), "w",
                                encoding="utf-8").write(
                            "A auditoria deste destino REPROVOU e a pasta nao pudo "
                            "ser removida (%s). Nao distribua, nao teste contra ela: "
                            "os arquivos aqui nao correspondem ao manifesto.\n"
                            % motivo)
                    except OSError:
                        pass
                out["destino_desfeito"] = desfeito
                out["por_que_desfeito"] = (
                    "destino reprovado nao pode ficar no disco parecendo pacote bom"
                    if desfeito else
                    "NAO foi possivel remover (%s); gravado NAO_DISTRIBUIR.txt" % motivo)
    elif a.destino:
        out["copiados_para"] = None

    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        io.open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0 if out["pacote_limpo"] else 1


if __name__ == "__main__":
    sys.exit(main())
