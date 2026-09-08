"""tolerance_lookup.py - consulta de folga de encaixe. Recusa inventar numero.

Uso:
  python tolerance_lookup.py --ajuste deslizante --maquina "Bambu Lab A1 0.4 nozzle" \
      --material "PLA Sunlu vermelho" [--json out.json]

  # registrar uma folga MEDIDA em cupom (e assim tirar a resposta do terreno publicado)
  python tolerance_lookup.py --registrar --ajuste deslizante \
      --maquina "Bambu Lab A1 0.4 nozzle" --material "PLA Sunlu vermelho" \
      --folga 0.22 --nota "cupom de 6 folgas, medido com paquimetro"

POR QUE ESTA FERRAMENTA EXISTE: folga de encaixe nao e constante de tabela. Ela depende
da maquina, do material, da compensacao XY e do acabamento de superficie. Duas fontes de
qualidade discordam em uma categoria inteira sobre o mesmo numero. Uma skill que cravar
um valor esta inventando.

O QUE ELE FAZ:
  1. procura uma folga MEDIDA nesta maquina com este material; se achar, essa e a
     resposta, e o resto e contexto;
  2. se nao achar, devolve a faixa publicada com rotulo de confianca, diz explicitamente
     que nao ha medicao local, e entrega o procedimento do cupom;
  3. cruza com o registro de calibracao existente e avisa quando ha pendencia
     dimensional aberta, porque erro de vazao contamina qualquer folga medida depois.
"""
import argparse, json, os, re, sys
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
PUBLICADAS = os.path.join(AQUI, "folgas_publicadas.json")

# CORRIGIDO 07/09/2026 depois da segunda revisao externa. As medicoes eram gravadas DENTRO
# da pasta de codigo, misturando instalacao distribuida com dado mutavel da oficina. Agora
# vao para um diretorio de dados fora do pacote, configuravel por variavel de ambiente.
def _dir_de_dados():
    d = os.environ.get("SKILL3D_DADOS")
    if not d:
        base = (os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
                or os.path.join(os.path.expanduser("~"), ".local", "share"))
        d = os.path.join(base, "skill3d")
    return d


DIR_DADOS = _dir_de_dados()
MEDIDAS = os.path.join(DIR_DADOS, "folgas_medidas.json")
REGISTRO_FILAMENTOS = os.environ.get(
    "SKILL3D_REGISTRO",
    os.path.join(os.path.expanduser("~"), ".claude", "skills", "bambu-a1",
                 "registro-filamentos.md"))

VAZIO = {"_nota": "Folgas MEDIDAS em cupom nesta oficina. Vazio significa vazio: nenhuma "
                  "folga foi medida ainda. Cada entrada carrega 'estado': definitiva ou "
                  "provisoria. Provisoria e a medida tirada com pendencia dimensional "
                  "aberta, e NAO e aplicavel a projeto.",
         "entradas": []}


def carrega_medidas():
    # migra o arquivo antigo, se ele existir dentro do pacote, e avisa
    antigo = os.path.join(AQUI, "folgas_medidas.json")
    if os.path.isfile(MEDIDAS):
        return json.load(open(MEDIDAS, encoding="utf-8")), None
    if os.path.isfile(antigo):
        d = json.load(open(antigo, encoding="utf-8"))
        return d, ("ha um registro de folgas ANTIGO dentro da pasta de codigo (%s). Mova-o "
                   "para %s: dado da oficina nao deve viver no pacote instalado."
                   % (antigo, MEDIDAS))
    return dict(VAZIO), None


def _sem_acento(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def classifica_estado(texto):
    """Le a coluna de estado do registro e diz se aquela linha esta CONCLUIDA.

    CORRIGIDO duas vezes em 07/09/2026. Primeiro porque "linha encontrada" contava como
    calibrada, sem olhar o estado. Depois porque a negacao era procurada SEM acento
    enquanto a afirmacao era procurada por substring: "nao validado" escrito com acento
    passava a negacao e casava "valid", e a linha era classificada como VALIDADA. Isso
    produzia conclusao factual errada no relatorio. Agora o texto e normalizado.
    """
    t = _sem_acento((texto or "").lower())
    if any(k in t for k in ("nao usar", "ruidos", "gera bolinha", "descartad", "invalid",
                            "nao utilizar", "descartar")):
        return "descartada"
    if any(k in t for k in ("nao valid", "n valid", "sem valid", "pendente")):
        return "calibrada_nao_validada"
    if "valid" in t:
        return "validada"
    if "calibrad" in t:
        return "calibrada_nao_validada"
    return "indeterminada"


def le_registro_filamentos(caminho):
    """Le a tabela markdown do registro de calibracao existente."""
    if not os.path.isfile(caminho):
        return {"encontrado": False, "caminho": caminho}
    linhas = open(caminho, encoding="utf-8").read().splitlines()
    itens, pendencias = [], []
    for ln in linhas:
        if ln.startswith("|") and ln.count("|") >= 8 and "---" not in ln:
            c = [x.strip() for x in ln.strip("|").split("|")]
            if c[0].lower().startswith("marca") or not c[0]:
                continue
            itens.append({"material": c[0], "temp": c[1], "k": c[2].replace("**", ""),
                          "chapa": c[5] if len(c) > 5 else None,
                          "estado_bruto": c[-1],
                          "estado": classifica_estado(c[-1])})
    txt = "\n".join(linhas).lower()
    for chave, aviso in (
        ("sobre-extrus", "ha pendencia de VAZAO em aberto no registro: sobre-extrusao declarada. "
                         "Erro de vazao muda dimensao, entao qualquer folga medida antes de fechar "
                         "isso carrega o erro."),
        ("nunca foi concluida", "ha calibracao declarada como nao concluida no registro."),
    ):
        if chave in txt:
            pendencias.append(aviso)
    return {"encontrado": True, "caminho": caminho, "n_entradas": len(itens),
            "entradas": itens, "pendencias_dimensionais": pendencias}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ajuste", required=True)
    ap.add_argument("--maquina", default=None)
    ap.add_argument("--material", default=None)
    ap.add_argument("--registrar", action="store_true")
    ap.add_argument("--folga", type=float)
    ap.add_argument("--nota", default="")
    ap.add_argument("--estado", choices=["definitiva", "provisoria"], default=None,
                    help="estado da medicao; sem isso, provisoria se houver pendencia aberta")
    ap.add_argument("--registro", default=REGISTRO_FILAMENTOS,
                    help="registro de calibracao da oficina; a ausencia dele nao "
                         "impede a consulta, so remove o cruzamento")
    ap.add_argument("--json")
    a = ap.parse_args()

    pub = json.load(open(PUBLICADAS, encoding="utf-8"))
    med, aviso_de_migracao = carrega_medidas()
    if a.ajuste not in pub["ajustes"]:
        raise SystemExit("ajuste desconhecido: %s. Conhecidos: %s"
                         % (a.ajuste, ", ".join(pub["ajustes"])))
    ficha = pub["ajustes"][a.ajuste]

    if a.registrar:
        if a.folga is None or not a.maquina or not a.material:
            raise SystemExit("para registrar: --folga, --maquina e --material sao obrigatorios")
        # CORRIGIDO 07/09/2026 depois da terceira revisao externa: argparse aceita nan e inf
        # como float, e o json os grava, entao um valor nao finito podia ser gravado como
        # "MEDIDO em cupom" e depois recomendado.
        import math
        if not math.isfinite(a.folga):
            raise SystemExit("folga tem que ser numero finito; veio %r" % a.folga)
        if a.folga < 0:
            raise SystemExit("folga negativa e interferencia, nao folga. Se a intencao for "
                             "interferencia, registre com ajuste 'press' e valor positivo, "
                             "declarando a convencao. Veio %r" % a.folga)
        reg0 = le_registro_filamentos(a.registro)
        tem_pend = bool(reg0.get("pendencias_dimensionais"))
        estado = a.estado or ("provisoria" if tem_pend else "definitiva")
        med["entradas"].append({
            "ajuste": a.ajuste, "maquina": a.maquina, "material": a.material,
            "folga_mm": a.folga, "data": date.today().isoformat(),
            "origem": "MEDIDO em cupom", "estado": estado,
            "pendencia_aberta_na_medicao": tem_pend, "nota": a.nota})
        os.makedirs(DIR_DADOS, exist_ok=True)
        json.dump(med, open(MEDIDAS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(json.dumps({"registrado": med["entradas"][-1], "arquivo": MEDIDAS,
                          "diretorio_de_dados": DIR_DADOS,
                          "total_de_medicoes": len(med["entradas"])},
                         indent=1, ensure_ascii=False))
        return 0

    # CORRIGIDO 07/09/2026 depois de revisao externa. A versao anterior tratava maquina e
    # material ausentes como curinga, e depois anunciava o ultimo resultado como "medido
    # nesta maquina". Isso mistura contexto. Agora: resposta definitiva SO com maquina e
    # material informados e casados. Sem isso, lista candidatos e mantem a
    # aplicabilidade indeterminada.
    do_ajuste = [e for e in med["entradas"] if e["ajuste"] == a.ajuste]
    exatos = [e for e in do_ajuste
              if a.maquina and a.material
              and e["maquina"] == a.maquina and e["material"] == a.material]
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa. Antes, QUALQUER estado
    # diferente de "provisoria" contava como definitiva, inclusive estado ausente,
    # desconhecido ou descartado. Agora so o estado explicito e valido conta, e o campo
    # de pendencia registrado na medicao continua valendo depois.
    import math
    ESTADOS_OK = ("definitiva", "provisoria")

    def _finita(e):
        try:
            return math.isfinite(float(e.get("folga_mm")))
        except (TypeError, ValueError):
            return False

    invalidas = [e for e in exatos
                 if e.get("estado") not in ESTADOS_OK or not _finita(e)]
    provisorias = [e for e in exatos if e.get("estado") == "provisoria" and _finita(e)]
    definitivas = [e for e in exatos
                   if e.get("estado") == "definitiva" and _finita(e)
                   and not e.get("pendencia_aberta_na_medicao")]
    contaminadas = [e for e in exatos
                    if e.get("estado") == "definitiva" and _finita(e)
                    and e.get("pendencia_aberta_na_medicao")]
    parciais = [e for e in do_ajuste if e not in exatos and (
        (a.maquina and e["maquina"] == a.maquina) or
        (a.material and e["material"] == a.material))]
    contexto_incompleto = not (a.maquina and a.material)
    reg = le_registro_filamentos(a.registro)
    pendencias = reg.get("pendencias_dimensionais") or []
    # CORRIGIDO 07/09/2026: pendencia dimensional aberta INVALIDA a aplicabilidade. Antes,
    # a saida podia dizer "use este valor" e emitir aviso de bloqueio ao lado, o que e
    # contradicao. Agora medicao definitiva com pendencia aberta vira NAO aplicavel.
    casa = definitivas if not pendencias else []
    linhas_do_material, concluidas = None, None
    if a.material and reg.get("encontrado"):
        linhas_do_material = [e for e in reg["entradas"]
                              if a.material.lower() in e["material"].lower()]
        concluidas = [e for e in linhas_do_material if e["estado"] == "validada"]

    out = {
        "ajuste": a.ajuste,
        "descricao": ficha["descricao"],
        "maquina": a.maquina,
        "material": a.material,
        "contexto_completo": not contexto_incompleto,
        "medicao_aplicavel": bool(casa),
        "valor_a_usar_mm": casa[-1]["folga_mm"] if casa else None,
        "origem_do_valor": ("MEDIDO nesta maquina com este material" if casa else
                            "aplicabilidade INDETERMINADA: contexto incompleto"
                            if contexto_incompleto else
                            "medicao existe mas NAO e aplicavel: pendencia dimensional aberta"
                            if (definitivas or provisorias) and pendencias else
                            "so ha medicao PROVISORIA para este contexto" if provisorias else
                            "NAO EXISTE medicao para este contexto"),
        "medicoes_definitivas": definitivas,
        "medicoes_provisorias": provisorias,
        "medicoes_contaminadas_por_pendencia": contaminadas,
        "medicoes_de_esquema_invalido": invalidas,
        "nota_de_esquema": ("entrada sem estado explicito, com estado desconhecido ou com "
                            "folga nao finita NAO conta como medicao. Registro antigo sem "
                            "estado precisa de migracao, e nao vale como definitiva."),
        "medicoes_que_casam_maquina_e_material": casa,
        "medicoes_de_contexto_diferente": parciais,
        "aviso_de_contexto": (
            "Sem --maquina E --material nao existe resposta aplicavel, porque folga depende dos "
            "dois. As medicoes listadas em medicoes_de_contexto_diferente sao de outro contexto "
            "e servem de referencia, nao de valor." if contexto_incompleto else None),
        "faixa_publicada_mm": ficha["faixa_mm"],
        "rotulo_de_confianca": ficha["rotulo"],
        "por_face": ficha.get("por_face"),
        "piso_absoluto_mm": ficha.get("piso_absoluto_mm"),
        "nota_da_faixa": ficha.get("nota"),
        "maquina_das_medicoes_publicadas": pub["_maquina_das_medicoes"],
        "divergencia_entre_fontes": pub["divergencia_conhecida"],
        "numeros_sem_fonte_primaria": pub["sem_fonte_primaria"],
        "cupom": pub["cupom"],
        "registro_de_calibracao": {
            "caminho": reg.get("caminho"),
            "encontrado": reg.get("encontrado"),
            "n_entradas": reg.get("n_entradas"),
            "linhas_encontradas_para_o_material": len(linhas_do_material or []),
            "linhas_com_calibracao_CONCLUIDA": len(concluidas or []),
            "material_tem_calibracao_concluida": bool(concluidas),
            "entradas_do_material": linhas_do_material,
            "nota_de_estado": ("linha encontrada no registro NAO significa calibracao "
                               "concluida: o estado de cada linha e classificado, e linha "
                               "descartada ou nao validada nao conta."),
            "pendencias_dimensionais": reg.get("pendencias_dimensionais", []),
        },
    }
    if casa:
        out["acao"] = ("Use %.3f mm por face, medido nesta maquina com este material em %s."
                       % (casa[-1]["folga_mm"], casa[-1]["data"]))
    elif contexto_incompleto:
        out["acao"] = ("Informe --maquina e --material. Sem os dois a folga nao tem "
                       "resposta aplicavel, e a faixa publicada de %.2f a %.2f mm por face "
                       "e so ponto de partida do cupom."
                       % (ficha["faixa_mm"][0], ficha["faixa_mm"][1]))
    else:
        out["acao"] = (
            "NAO ha folga medida para %s nesta combinacao. Nao crave numero. Use a faixa "
            "publicada de %.2f a %.2f mm por face SO como ponto de partida do cupom, imprima o "
            "corpo de prova com as seis folgas, meca com paquimetro, e registre o resultado com "
            "--registrar. Antes disso, a folga do projeto e uma suposicao, e tem que ser dita "
            "como suposicao." % (a.ajuste, ficha["faixa_mm"][0], ficha["faixa_mm"][1]))
    if pendencias:
        out["aviso_de_bloqueio"] = (
            "Ha pendencia dimensional aberta no registro de calibracao, logo NENHUMA folga "
            "medida e aplicavel a projeto agora, nem as definitivas. Feche a pendencia e "
            "remeca, ou registre a medida com --estado provisoria e trate a folga do projeto "
            "como suposicao declarada.")
        out["acao"] = out["aviso_de_bloqueio"]
    if aviso_de_migracao:
        out["aviso_de_migracao"] = aviso_de_migracao

    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
