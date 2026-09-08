"""empacota.py - monta o pacote distribuivel por LISTA DE PERMISSAO e recusa vazamento.

Uso:
  python empacota.py --verificar            # so audita, nao copia
  python empacota.py --destino ..\\pacote     # copia os permitidos, se limpo

POR QUE EXISTE: uma revisao externa encontrou, na pasta de prototipos, dados de um projeto
privado do autor: nome de arquivo de referencia, hash, cotas, e uma normal e um centroide
reais dentro do exemplo de uso de uma FERRAMENTA, que e material distribuido. A causa raiz
nao foi descuido pontual: foi empacotar por exclusao. Quem empacota a pasta inteira
publica tudo o que caiu nela, inclusive saida de execucao contra arquivo privado.

A regra passa a ser lista de PERMISSAO explicita, mais varredura de vazamento que BARRA a
montagem do pacote. Arquivo que nao esta na lista nao vai, mesmo que seja inofensivo.
"""
import argparse, json, os, re, shutil, sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Somente estes vao para o pacote. Ordem e agrupamento sao para leitura humana.
PERMITIDOS = [
    # nucleo
    "matriz.py",
    "check_intent.py",
    # geometria e malha
    "secoes.py",
    "check_mesh.py",
    "find_datums.py",
    "align_rigid.py",
    # cad parametrico
    "sweep_params.py",
    "exemplo_b123d.py",
    # fabricacao
    "split_for_volume.py",
    "slice_check.py",
    # adaptador de oficina
    "tolerance_lookup.py",
    "folgas_publicadas.json",
    # contrato de ambiente
    "ambiente.json",
    # testes
    "casos.py",
    "roda_casos.py",
    "mutacoes.py",
    "empacota.py",
]

# Nunca vao, mesmo se alguem adicionar por engano. Cinto e suspensorio.
NEGADOS = [
    "folgas_medidas.json",          # dado da oficina, nao do pacote
    "LEIA-ME.md",                   # notas de trabalho: citam medidas do arquivo real
    "req_exemplo.json",             # gerado contra o exemplo local
    "gera_caso2.py",                # apoio de investigacao, nao ferramenta
    "padroes_de_vazamento.json",    # nomeia o projeto privado do autor: nunca viaja
]

# Padroes GENERICOS, que valem em qualquer instalacao e podem viajar no pacote.
PADROES_GENERICOS = [
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa: o padrao de caminho cobria
    # so barra invertida, e caminho Python costuma usar barra normal; o padrao de hash
    # cobria so hexadecimal minusculo.
    (r"[A-Za-z]:[\\/]Users[\\/][^\\/\s\"']+", "caminho absoluto com nome de usuario"),
    (r"(?i)\b[0-9a-f]{64}\b", "possivel hash SHA256 literal: confira se e de arquivo sintetico"),
    (r"(?i)\b[0-9a-f]{40}\b", "possivel hash SHA1 literal"),
    # A palavra e montada em pedacos de proposito: escrita inteira, o padrao casaria
    # consigo mesmo e o auditor se auto-acusaria. Isso aconteceu na primeira versao.
    (r"(?i)confid" + r"enc[a-z]*|sigi" + r"los[a-z]*|segr" + r"edo\s+industrial",
     "marca de restricao no texto"),
]

# Padroes ESPECIFICOS de cada instalacao ficam num arquivo LOCAL, que esta em NEGADOS.
# Motivo: esses padroes nomeiam o projeto que se quer proteger. Publicar o auditor com eles
# dentro seria o proprio vazamento que ele existe para impedir. Sem o arquivo, o auditor cai
# para os genericos e declara que caiu.
ARQUIVO_DE_PADROES = "padroes_de_vazamento.json"


# --------------------------------------------------------------------------------------
# Identidade de caminho. CORRIGIDO em M0.1: a versao anterior comparava TEXTO, com
# os.path.abspath mais prefixo. Isso e sensivel a caixa e cego a junção e a vinculo. No
# Windows, ...\\Pacote e ...\\PACOTE\\rel.json sao a mesma pasta, e uma junção L apontando
# para o destino nao tem nenhuma semelhanca textual com ele. Pior: a validacao rodava
# somente quando --destino estava presente, entao auditar com o relatorio apontado para um
# arquivo de codigo sobrescrevia a propria entrada DEPOIS de audita-la.
CODIGOS_DE_CAMINHO = ("E_CAMINHO_NO_DESTINO", "E_CAMINHO_SOBRE_ENTRADA",
                      "E_CAMINHO_NOME_DE_PACOTE")


def canon(caminho):
    """Forma canonica: resolve junção e vinculo no trecho que existe, e normaliza caixa."""
    return os.path.normcase(os.path.realpath(os.path.abspath(caminho)))


def mesmo_arquivo(a, b):
    """Identidade FISICA quando os dois lados existem, porque samefile enxerga junção,
    vinculo e unidade mapeada. Texto canonico como recurso quando um dos lados nao existe
    ainda, que e o caso normal de um relatorio a ser gravado."""
    try:
        if os.path.exists(a) and os.path.exists(b):
            return os.path.samefile(a, b)
    except OSError:
        pass
    return canon(a) == canon(b)


def ancestral_existente(caminho):
    """Primeiro diretorio que existe, subindo a arvore. Um relatorio ainda inexistente
    dentro de uma junção so revela a identidade pelo ancestral que existe de fato."""
    d = os.path.dirname(os.path.abspath(caminho))
    while d and not os.path.isdir(d):
        pai = os.path.dirname(d)
        if pai == d:
            return ""
        d = pai
    return d


def dentro_da_arvore(alvo, raiz):
    """O alvo e a propria raiz, ou fica sob ela, por identidade fisica ou canonicamente."""
    if not raiz:
        return False
    if mesmo_arquivo(alvo, raiz):
        return True
    anc = ancestral_existente(alvo)
    if anc and mesmo_arquivo(anc, raiz):
        return True
    craiz, calvo = canon(raiz), canon(alvo)
    if calvo == craiz or calvo.startswith(craiz + os.sep):
        return True
    canc = canon(anc) if anc else ""
    return bool(canc) and (canc == craiz or canc.startswith(craiz + os.sep))


def valida_caminho_do_relatorio(caminho_json, destino):
    """Devolve (codigo, mensagem) ou None. RODA EM TODOS OS MODOS, inclusive auditoria
    sem destino. Recusa o relatorio que resolva para dentro da arvore distribuida ou
    para qualquer arquivo de entrada."""
    if destino and dentro_da_arvore(caminho_json, destino):
        return ("E_CAMINHO_NO_DESTINO",
                "o relatorio (--json %s) resolve para DENTRO do destino (%s). O relatorio "
                "e gravado depois da auditoria, entao ele invalidaria o que foi auditado. "
                "Grave o relatorio fora do pacote." % (caminho_json, destino))
    for nome in sorted(os.listdir(AQUI)):
        entrada = os.path.join(AQUI, nome)
        if os.path.isfile(entrada) and mesmo_arquivo(caminho_json, entrada):
            return ("E_CAMINHO_SOBRE_ENTRADA",
                    "o relatorio (--json %s) resolve para o arquivo de entrada %s. Gravar "
                    "ali sobrescreve o que esta sendo auditado." % (caminho_json, nome))
    permitidos_normalizados = {os.path.normcase(f) for f in PERMITIDOS}
    if os.path.basename(canon(caminho_json)) in permitidos_normalizados:
        return ("E_CAMINHO_NOME_DE_PACOTE",
                "o relatorio se chama %r, que e nome de arquivo do pacote. Isso confunde "
                "evidencia com codigo entregue." % os.path.basename(caminho_json))
    return None


def carrega_padroes():
    p = os.path.join(AQUI, ARQUIVO_DE_PADROES)
    if not os.path.isfile(p):
        return list(PADROES_GENERICOS), False
    d = json.load(open(p, encoding="utf-8"))
    esp = [(pat, motivo) for pat, motivo in d.get("padroes", [])]
    return list(PADROES_GENERICOS) + esp, True

# Arquivos sinteticos e gerados que podem existir na pasta sem ir para o pacote.
IGNORAR_NA_AUDITORIA = re.compile(
    r"(^__pycache__)|(^casos_saida)|(^varredura)|(\.stl$)|(\.step$)|(\.3mf$)|"
    r"(_resultado\.json$)|(^caso\d.*\.json$)|(^intent_)|(^s_)|(^mut_)|(^\.)")


def varre(caminho, padroes):
    try:
        t = open(caminho, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return [("nao_pude_ler", "%s: %s" % (type(e).__name__, e))]
    achados = []
    for pat, motivo in padroes:
        for m in re.finditer(pat, t):
            linha = t[:m.start()].count("\n") + 1
            achados.append(("linha %d" % linha, motivo))
    return achados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()

    padroes, tem_especificos = carrega_padroes()
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa. Tres brechas: --verificar era
    # declarado e nunca consultado, entao --verificar junto com --destino copiava; a lista
    # de negados nunca era confrontada com a de permitidos, logo a promessa "nunca vao"
    # nao estava implementada; e o destino era criado com exist_ok e recebia os permitidos
    # por cima, sem exigir pasta vazia nem auditar o resultado, entao um arquivo privado de
    # um pacote anterior continuava lá e a execucao ainda dizia pacote_limpo.
    if a.verificar and a.destino:
        raise SystemExit("--verificar audita e NAO escreve. Nao combine com --destino.")
    # CORRIGIDO 07/09/2026 depois da quarta revisao externa. O relatorio de --json era
    # gravado DEPOIS da auditoria do destino: apontado para dentro do destino, criava
    # arquivo nao permitido depois de conferir o inventario; apontado para um nome
    # permitido, sobrescrevia codigo ja auditado. E o retorno continuava indicando sucesso.
    # CORRIGIDO em M0.1: a guarda rodava so com --destino presente e comparava texto.
    # Agora vale em todos os modos e resolve identidade fisica. A recusa sai com CODIGO
    # estavel na frente, porque criterio que depende de frase ja falhou uma vez por acento.
    if a.json:
        falha = valida_caminho_do_relatorio(a.json, a.destino)
        if falha:
            raise SystemExit("%s recusado: %s" % falha)
    interseccao = sorted(set(PERMITIDOS) & set(NEGADOS))
    if interseccao:
        raise SystemExit("as listas de permitidos e negados se cruzam em %s. Isso torna a "
                         "promessa de negacao inexequivel. Corrija as listas." % interseccao)
    duplicados = sorted({f for f in PERMITIDOS if PERMITIDOS.count(f) > 1})
    if duplicados:
        raise SystemExit("permitidos com entrada repetida: %s" % duplicados)
    existentes = sorted(f for f in os.listdir(AQUI) if os.path.isfile(os.path.join(AQUI, f)))
    faltando = [f for f in PERMITIDOS if f not in existentes]
    nao_listados = [f for f in existentes
                    if f not in PERMITIDOS and f not in NEGADOS
                    and not IGNORAR_NA_AUDITORIA.match(f)]

    vazamentos = {}
    for f in PERMITIDOS:
        p = os.path.join(AQUI, f)
        if os.path.isfile(p):
            ach = varre(p, padroes)
            if ach:
                vazamentos[f] = ach

    # a auditoria tambem olha o que NAO vai, so para o operador saber onde esta o dado
    vazamentos_fora = {}
    for f in existentes:
        if f in PERMITIDOS:
            continue
        p = os.path.join(AQUI, f)
        ach = varre(p, padroes)
        if ach:
            vazamentos_fora[f] = ach

    limpo = not vazamentos and not faltando
    out = {
        "n_permitidos": len(PERMITIDOS),
        "padroes_especificos_carregados": tem_especificos,
        "aviso_de_padroes": (None if tem_especificos else
                             "o arquivo local de padroes especificos nao foi encontrado: a "
                             "auditoria rodou SO com os padroes genericos e nao consegue "
                             "reconhecer nomes do seu projeto"),
        "faltando_na_pasta": faltando,
        "nao_listados_e_nao_negados": nao_listados,
        "vazamentos_em_arquivo_do_pacote": vazamentos,
        "vazamentos_em_arquivo_fora_do_pacote": vazamentos_fora,
        "nenhum_padrao_conhecido_encontrado": limpo,
        "pacote_limpo": limpo,
        # CORRIGIDO 07/09/2026 depois da quarta revisao externa: existia um campo
        # autorizado_a_publicar calculado so por triagem textual, e um consumidor
        # automatico recebia uma liberacao que o proprio texto dizia nao emitir.
        # Autorizacao de publicacao nao e coisa que esta ferramenta possa emitir.
        "autorizacao_de_publicacao": "NAO EMITIDA por esta ferramenta",
        "por_que_nao_emitimos_autorizacao": (
            "triagem textual sem achados nao e ausencia de dado privado. Faltam, e estao "
            "declarados como abertos: amostra de regressao numerica mantida fora do pacote, "
            "e teste do pacote em instalacao limpa. Autorizar publicacao e decisao de quem "
            "conhece o material, com estas evidencias na mao."),
        "o_que_isto_significa": (
            "nenhum PADRAO CONHECIDO foi encontrado nos arquivos permitidos. Isso NAO e "
            "prova de ausencia de dado privado: o auditor so acha o que os padroes "
            "descrevem, e as categorias que ele nao descreve passam. Em particular, "
            "conjuntos numericos como normais, centroides e cotas nao tem padrao textual "
            "e precisam de conferencia por amostra de regressao mantida FORA do pacote."),
        "acao": (("Nenhum padrao conhecido encontrado. Pode montar, CIENTE de que isto nao "
                  "e prova de ausencia." if tem_especificos else
                  "Nenhum padrao conhecido encontrado, mas os padroes ESPECIFICOS nao foram "
                  "carregados: a auditoria rodou reduzida e NAO autoriza publicacao.")
                 if limpo else
                 "BARRADO. Nao monte o pacote enquanto houver vazamento em arquivo permitido "
                 "ou arquivo permitido ausente."),
        "triagem_textual_sem_achados": bool(limpo and tem_especificos),
        "nota": ("Vazamento em arquivo FORA do pacote nao barra a montagem, mas fica listado "
                 "de proposito: aquele dado existe na sua maquina e nao pode ser publicado "
                 "por outro caminho."),
    }

    if a.destino and limpo:
        dest = os.path.abspath(a.destino)
        if os.path.exists(dest) and os.listdir(dest):
            out["copiados_para"] = None
            out["erro_de_destino"] = (
                "o destino %s existe e NAO esta vazio. Monte o pacote em diretorio novo: "
                "copiar por cima deixa arquivo de pacote anterior no material entregue, e "
                "a lista de permissao so controla o que e ACRESCENTADO." % dest)
            out["acao"] = out["erro_de_destino"]
            print(json.dumps(out, indent=1, ensure_ascii=False))
            return 1
        os.makedirs(dest, exist_ok=True)
        for f in PERMITIDOS:
            shutil.copy2(os.path.join(AQUI, f), os.path.join(dest, f))
        # auditoria DO RESULTADO: inventario e conteudo do que ficou na pasta entregue
        no_destino = sorted(f for f in os.listdir(dest)
                            if os.path.isfile(os.path.join(dest, f)))
        sobrando = [f for f in no_destino if f not in PERMITIDOS]
        faltou = [f for f in PERMITIDOS if f not in no_destino]
        vaz_dest = {}
        for f in no_destino:
            ach = varre(os.path.join(dest, f), padroes)
            if ach:
                vaz_dest[f] = ach
        ok_dest = not sobrando and not faltou and not vaz_dest
        out["auditoria_do_destino"] = {
            "arquivos_no_destino": no_destino, "sobrando": sobrando, "faltou": faltou,
            "vazamentos": vaz_dest, "ok": ok_dest}
        out["copiados_para"] = dest if ok_dest else None
        if not ok_dest:
            out["acao"] = ("BARRADO depois da copia: a auditoria do DESTINO reprovou. "
                           "Nao distribua esta pasta.")
            print(json.dumps(out, indent=1, ensure_ascii=False))
            return 1
    elif a.destino:
        out["copiados_para"] = None

    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0 if limpo else 1


if __name__ == "__main__":
    sys.exit(main())
