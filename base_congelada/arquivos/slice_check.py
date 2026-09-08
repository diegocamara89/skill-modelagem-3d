"""slice_check.py - portao real: manda a geometria pelo fatiador de verdade.

Uso:
  python slice_check.py --modelo peca.stl \
      --maquina "Bambu Lab A1 0.4 nozzle" --processo "0.20mm Standard @BBL A1" \
      --filamento "Generic PLA @BBL A1" [--vendor BBL] [--json out.json]

POR QUE ESTE PORTAO E DIFERENTE DOS OUTROS: desenho de aprovacao e imagem lado a lado
mostram o que quem desenhou escolheu mostrar. O fatiador nao coopera com quem desenhou:
ele processa a geometria de verdade, com o perfil de verdade, e devolve codigo, log e
artefato conferiveis.

O QUE ELE NAO PEGA, MEDIDO 07/09/2026: casca ABERTA. Uma superficie sem espessura foi
aceita pelo fatiador sem reclamacao. Quem pega isso e o portao de malha, pela
estanqueidade. Este portao nao substitui aquele.

DUAS COISAS QUE ESTA FERRAMENTA RESOLVE E QUE MORDEM QUALQUER TENTATIVA INGENUA:

1. Os perfis do sistema usam HERANCA (campo "inherits"). Passar o arquivo do perfil
   direto para a linha de comando falha, porque a cadeia nao e resolvida. Aqui a cadeia
   e achatada antes, do topo para a folha.

2. O executavel e um aplicativo grafico do Windows: nao escreve no console em chamada
   normal, e caminho com espaco e partido na passagem de argumentos. Aqui tudo e copiado
   para um diretorio sem espaco e a saida e redirecionada para arquivo.

O QUE ELE AFIRMA, exatamente: que o fatiador produziu saida com ESTES perfis e ESTA
geometria, e que nenhuma checagem reprovou. Nada alem disso. Nao afirma que a peca esta
correta de cota, nem que vai imprimir bem em outra maquina, material ou perfil. Cota
errada fatia perfeitamente.

A saida separa tres coisas de proposito: processo_concluido (o programa terminou com
zero), saida_gerada (o arquivo existe) e checagens_aprovadas (nenhum motivo de
reprovacao). Aprovado exige os tres.
"""
import argparse, json, os, shutil, subprocess, sys, uuid, zipfile
from datetime import datetime

ORCA_PADRAO = r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
PERFIS_PADRAO = r"C:\Program Files\OrcaSlicer\resources\profiles"
# MEDIDO 07/09/2026, na ordem em que os erros apareceram:
#   1. sem achatar a heranca            -> "process not compatible with printer"
#   2. sem o campo "from"               -> "file ...json's from  unsupported"
#   3. trocando "from" para "User" e zerando compatible_*  -> falha muda, sem mensagem
# O que funciona e achatar a cadeia e NAO TOCAR EM MAIS NADA. Metadados como
# setting_id, instantiation, description e compatible_printers fazem parte da
# identidade do perfil; remover qualquer um deles torna o conjunto incompativel.
DESCARTAR = ("inherits",)


def _sha(caminho):
    """Hash de conteudo, para amarrar a evidencia aos bytes. Calculado em execucao sobre
    arquivo do usuario; nao e hash embutido no pacote."""
    import hashlib
    if not caminho or not os.path.isfile(caminho):
        return None
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def acha_perfil(nome, pastas):
    if os.path.isfile(nome):
        return nome
    for p in pastas:
        c = os.path.join(p, nome + ".json")
        if os.path.isfile(c):
            return c
    return None


def achata(nome, pastas, limite=20, tipo=None):
    """Resolve a cadeia de inherits e devolve um perfil unico e completo."""
    cam = acha_perfil(nome, pastas)
    if not cam:
        raise SystemExit("perfil nao encontrado: %s (procurei em %s)" % (nome, pastas))
    cadeia, visto, atual = [], set(), cam
    for _ in range(limite):
        d = json.load(open(atual, encoding="utf-8"))
        cadeia.append((os.path.basename(atual), d))
        pai = d.get("inherits")
        if not pai or pai in visto:
            break
        visto.add(pai)
        prox = acha_perfil(pai, [os.path.dirname(atual)] + list(pastas))
        if not prox:
            raise SystemExit("elo da heranca nao encontrado: %s (pai de %s)" % (pai, atual))
        atual = prox
    junto = {}
    for _, d in reversed(cadeia):          # base primeiro, folha por cima
        junto.update(d)
    for k in DESCARTAR:
        junto.pop(k, None)
    if not os.path.isfile(nome):
        junto["name"] = nome
    if tipo:
        junto["type"] = tipo
    junto.setdefault("from", "system")
    # CORRIGIDO 07/09/2026: ciclo de heranca ou estouro do limite devolvia o perfil como se
    # estivesse completo, sem estado de resolucao incompleta.
    ultimo = cadeia[-1][1] if cadeia else {}
    resolvida = not ultimo.get("inherits")
    if not resolvida:
        raise SystemExit(
            "heranca de perfil NAO resolvida para %r: o ultimo elo (%s) ainda aponta para "
            "%r depois de %d passos. Pode ser ciclo ou cadeia mais longa que o limite. "
            "Isso e erro de configuracao, nao perfil completo."
            % (nome, cadeia[-1][0], ultimo.get("inherits"), len(cadeia)))
    return junto, [n for n, _ in cadeia]


# MEDIDO 07/09/2026: codigos observados nesta maquina. O fatiador devolve o codigo em
# complemento de dois e a mensagem no stdout e sempre a mesma, inutil. Esta tabela e
# empirica: cobre o que foi visto, nao a enumeracao interna do programa.
CODIGOS = {
    0: "sucesso",
    -5: "problema no arquivo de perfil (visto quando faltava o campo from)",
    -17: "conjunto de perfis incompativel (visto quando metadados foram removidos)",
    -50: "nenhum objeto utilizavel (visto com peca maior que o envelope)",
}


def codigo_legivel(rc):
    if rc is None:
        return "timeout"
    assinado = rc - 2 ** 32 if rc > 2 ** 31 else rc
    return "%d: %s" % (assinado, CODIGOS.get(assinado, "codigo nao catalogado"))


def confere_envelope(modelo, perfil_maquina, margem=0.0):
    """Compara a caixa do modelo com o envelope declarado no perfil, ANTES de fatiar.

    CORRIGIDO 07/09/2026 depois da quarta revisao externa. Valor PRESENTE mas invalido
    escapava de tudo: altura "nan" era convertida sem rejeicao e a comparacao com NaN e
    sempre falsa; area ["0x0"] dava largura zero e o teste de planta era pulado pelo
    "if lx and ly"; nenhum valor era None, entao nada entrava em desconhecido. Resultado:
    cabe_no_envelope=True com a lista de problemas vazia. A correcao anterior tratava so
    a AUSENCIA de dimensao.
    """
    import math
    import trimesh
    m = trimesh.load(modelo, force="mesh", process=False)
    ext = [float(x) for x in m.extents]
    invalidos = []

    def _num(v, rotulo):
        try:
            x = float(v)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(x):
            invalidos.append("%s nao e finito: %r" % (rotulo, v))
            return None
        if x <= 0:
            invalidos.append("%s tem que ser positivo: %r" % (rotulo, v))
            return None
        return x

    h = _num(perfil_maquina.get("printable_height"), "printable_height")
    bruto = perfil_maquina.get("printable_area") or []
    pts, ruins = [], 0
    for s in bruto:
        try:
            x, y = str(s).split("x")
            fx, fy = float(x), float(y)
            if not (math.isfinite(fx) and math.isfinite(fy)):
                ruins += 1
                continue
            pts.append((fx, fy))
        except Exception:
            ruins += 1
    if ruins:
        invalidos.append("%d vertices de printable_area ilegiveis ou nao finitos" % ruins)
    if bruto and len(pts) < 3:
        invalidos.append("printable_area com %d vertices utilizaveis: uma mesa precisa de "
                         "pelo menos 3" % len(pts))
    if len(pts) >= 3:
        lx = max(p[0] for p in pts) - min(p[0] for p in pts)
        ly = max(p[1] for p in pts) - min(p[1] for p in pts)
        if not (lx > 0 and ly > 0):
            invalidos.append("printable_area degenerada: extensao %r x %r" % (lx, ly))
            lx = ly = None
    else:
        lx = ly = None
    env = [lx, ly, h]
    problemas = list(invalidos)
    if h is not None and ext[2] > h - margem:
        problemas.append("altura da peca %.1f mm passa a altura imprimivel %.1f mm" % (ext[2], h))
    if lx is not None and ly is not None:
        planta = sorted(ext[:2]); mesa = sorted([lx, ly])
        if planta[0] > mesa[0] - margem or planta[1] > mesa[1] - margem:
            problemas.append("planta da peca %.1f x %.1f mm nao entra na mesa %.1f x %.1f mm"
                             % (ext[0], ext[1], lx, ly))
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa: quando o perfil nao trazia
    # as dimensoes, a lista de problemas ficava vazia e o resultado dizia cabe=True. Falta
    # de informacao nao e aprovacao.
    desconhecido = [k for k, v in (("altura", h), ("planta", lx), ("planta", ly)) if v is None]
    return {"caixa_da_peca_mm": [round(x, 3) for x in ext],
            "envelope_do_perfil_mm": env,
            "envelope_desconhecido_em": sorted(set(desconhecido)),
            "valores_invalidos_no_perfil": invalidos,
            "cabe_no_envelope": (None if (desconhecido or invalidos) else not problemas),
            "problemas": problemas + (
                ["envelope do perfil desconhecido em %s: nao e possivel afirmar que a peca "
                 "cabe" % sorted(set(desconhecido))] if desconhecido else [])}


def le_slice_info(caminho_3mf):
    """Le Metadata/slice_info.config do 3mf de saida: gramas, tempo, camadas."""
    if not os.path.isfile(caminho_3mf):
        return None
    try:
        with zipfile.ZipFile(caminho_3mf) as z:
            nomes = z.namelist()
            alvo = next((n for n in nomes if n.endswith("slice_info.config")), None)
            if not alvo:
                return {"arquivos_no_3mf": nomes[:20]}
            bruto = z.read(alvo).decode("utf-8", "replace")
    except Exception as e:
        return {"erro": "%s: %s" % (type(e).__name__, e)}
    import re
    pares = dict(re.findall(r'key="([^"]+)"\s+value="([^"]*)"', bruto))
    inter = {k: pares[k] for k in (
        "prediction", "weight", "used_g", "used_m", "layer_height", "outer_wall_line_width",
        "nozzle_diameter", "filament_type", "printer_model_id", "support_used", "index",
        "total_layer_number") if k in pares}
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa. tem_gcode conferia apenas o
    # NOME de um membro do zip: um .gcode VAZIO satisfazia. E "campos" caia para qualquer
    # par key/value encontrado, sem exigir conteudo minimo de fatiamento.
    OBRIGATORIOS = ("prediction", "weight")
    gcodes = [n for n in nomes if n.endswith(".gcode")]
    tamanhos = {}
    try:
        with zipfile.ZipFile(caminho_3mf) as z:
            for n in gcodes:
                tamanhos[n] = int(z.getinfo(n).file_size)
    except Exception:
        pass
    gcode_util = [n for n, t in tamanhos.items() if t > 1024]
    faltando = [k for k in OBRIGATORIOS if k not in pares]
    return {"campos": inter,
            "campos_brutos_encontrados": len(pares),
            "campos_obrigatorios_faltando": faltando,
            "esquema_minimo_ok": not faltando,
            "membros_gcode": gcodes,
            "tamanhos_gcode_bytes": tamanhos,
            "tem_gcode": bool(gcode_util),
            "nota": ("tem_gcode exige membro .gcode com mais de 1 KB. Nome de membro nao e "
                     "evidencia de trajetoria: um arquivo vazio satisfazia a versao anterior.")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True)
    ap.add_argument("--maquina", required=True)
    ap.add_argument("--processo", required=True)
    ap.add_argument("--filamento", required=True)
    ap.add_argument("--vendor", default="BBL")
    ap.add_argument("--orca", default=ORCA_PADRAO)
    ap.add_argument("--perfis", default=PERFIS_PADRAO)
    ap.add_argument("--trabalho", default=r"C:\Temp\slicecheck",
                help="raiz das areas de trabalho; cada execucao cria a propria subpasta")
    ap.add_argument("--manter", action="store_true",
                    help="nao apagar a subpasta desta execucao ao terminar")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--debug", default="2")
    ap.add_argument("--json")
    a = ap.parse_args()

    if not os.path.isfile(a.orca):
        raise SystemExit("fatiador nao encontrado: " + a.orca)
    vd = os.path.join(a.perfis, a.vendor)
    pastas = [os.path.join(vd, s) for s in ("machine", "process", "filament")] + [vd, a.perfis]

    # CORRIGIDO 07/09/2026 depois de revisao externa. A versao anterior fazia rmtree
    # recursivo no caminho recebido em --trabalho. Um caminho errado apagaria dados do
    # usuario, e duas execucoes simultaneas se atropelariam. Agora: subpasta exclusiva por
    # execucao, com marcador de propriedade, e limpeza restrita ao que esta ferramenta
    # criou. Nada e apagado sem o marcador presente.
    MARCADOR = ".criado_por_slice_check"
    raiz = os.path.abspath(a.trabalho)
    t = os.path.join(raiz, "exec_%d_%s" % (os.getpid(), uuid.uuid4().hex[:8]))
    if os.path.isdir(t):                      # colisao improvavel; so limpa o que e nosso
        if os.path.isfile(os.path.join(t, MARCADOR)):
            shutil.rmtree(t, ignore_errors=True)
        else:
            raise SystemExit("diretorio de execucao existe e nao tem marcador desta "
                             "ferramenta; nao vou apagar: " + t)
    os.makedirs(t, exist_ok=True)
    open(os.path.join(t, MARCADOR), "w", encoding="utf-8").write(
        "Criado por slice_check.py em %s. Seguro apagar." % datetime.now().isoformat(timespec="seconds"))
    if " " in t:
        raise SystemExit("o diretorio de trabalho nao pode ter espaco no caminho, porque o "
                         "fatiador parte o argumento: " + t)

    cadeias, perfis_achatados = {}, {}
    for rotulo, nome in (("machine", a.maquina), ("process", a.processo), ("filament", a.filamento)):
        perfil, cadeia = achata(nome, pastas, tipo=rotulo)
        perfis_achatados[rotulo] = perfil
        json.dump(perfil, open(os.path.join(t, rotulo + ".json"), "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        cadeias[rotulo] = {"pedido": nome, "cadeia_de_heranca": cadeia, "n_chaves": len(perfil)}

    envelope = confere_envelope(a.modelo, perfis_achatados["machine"])

    ext = os.path.splitext(a.modelo)[1].lower()
    modelo = os.path.join(t, "model" + ext)
    shutil.copy2(a.modelo, modelo)

    cmd = [a.orca, "--slice", "0",
           "--load-settings", os.path.join(t, "machine.json") + ";" + os.path.join(t, "process.json"),
           "--load-filaments", os.path.join(t, "filament.json"),
           "--allow-newer-file", "--arrange", "1", "--debug", a.debug,
           "--outputdir", t, "--export-3mf", "saida.gcode.3mf", modelo]

    with open(os.path.join(t, "o.txt"), "wb") as fo, open(os.path.join(t, "e.txt"), "wb") as fe:
        try:
            # cwd=t de proposito: MEDIDO 07/09/2026, o fatiador escreve 00000.log no
            # diretorio ATUAL, nao no --outputdir. Sem isso ele sujaria a pasta do projeto.
            rc = subprocess.call(cmd, stdout=fo, stderr=fe, timeout=a.timeout, cwd=t)
        except subprocess.TimeoutExpired:
            rc = None

    ler = lambda n: (open(os.path.join(t, n), encoding="utf-8", errors="replace").read().strip()
                     if os.path.isfile(os.path.join(t, n)) else "")
    so, se = ler("o.txt"), ler("e.txt")
    # O fatiador escreve o detalhe em 00000.log no proprio outputdir, nao no stderr.
    # MEDIDO 07/09/2026: sem tela, ele sempre reclama de OpenGL e de miniatura. Isso e
    # ruido benigno em execucao sem interface, nao motivo de reprovacao.
    BENIGNO = ("invalid opengl", "glfw", "thumbnail", "opengl context unavailable",
               "no filament colors found")
    log_linhas = [l.strip() for l in ler("00000.log").splitlines() if l.strip()]
    log_relevante = [l for l in log_linhas
                     if not any(b in l.lower() for b in BENIGNO)]
    saida_3mf = os.path.join(t, "saida.gcode.3mf")
    info = le_slice_info(saida_3mf)
    gerou = os.path.isfile(saida_3mf)

    motivos = []
    for p in envelope["problemas"]:
        motivos.append("envelope: " + p)
    # CORRIGIDO 07/09/2026 depois da segunda revisao externa. A leitura do conteudo do
    # 3mf era feita e NAO participava da decisao: erro de ZIP, ausencia de metadados de
    # fatiamento e ausencia de G-code passavam calados, e a aprovacao dependia so de
    # codigo zero, arquivo existente e log sem palavra de erro.
    if gerou:
        if not isinstance(info, dict):
            motivos.append("saida: nao foi possivel inspecionar o 3mf gerado")
        elif info.get("erro"):
            motivos.append("saida: falha ao abrir o 3mf gerado: %s" % info["erro"])
        else:
            if not info.get("esquema_minimo_ok"):
                motivos.append("saida: metadados de fatiamento incompletos, faltam %s; nao ha "
                               "evidencia de que o fatiamento produziu resultado utilizavel"
                               % (info.get("campos_obrigatorios_faltando") or "campos"))
            if not info.get("tem_gcode"):
                motivos.append("saida: o 3mf nao contem G-code utilizavel (membros: %s, "
                               "tamanhos: %s); o arquivo existe mas nao carrega trajetoria"
                               % (info.get("membros_gcode"), info.get("tamanhos_gcode_bytes")))
    if rc is None:
        motivos.append("estourou o timeout de %ds" % a.timeout)
    elif rc != 0:
        motivos.append("codigo de saida " + codigo_legivel(rc))
    if not gerou:
        motivos.append("nao gerou o 3mf de saida")
    for linha in (so + "\n" + se + "\n" + "\n".join(log_relevante)).splitlines():
        b = linha.strip()
        if b and any(p in b.lower() for p in ("error", "erro", "fail", "exceed", "out of",
                                              "not done", "invalid", "empty")):
            motivos.append("mensagem do fatiador: " + b[:220])

    # CORRIGIDO 07/09/2026 depois de revisao externa. A versao anterior decidia so por
    # "gerou arquivo e saiu com zero", e portanto podia declarar aprovacao com a lista de
    # motivos cheia: problema de envelope e mensagem de erro do log nao entravam na conta.
    processo_concluido = bool(rc == 0)
    saida_gerada = bool(gerou)
    checagens_aprovadas = bool(not motivos)
    aprovado = bool(processo_concluido and saida_gerada and checagens_aprovadas)
    out = {
        "modelo": a.modelo,
        "fatiador": a.orca,
        "perfis": cadeias,
        "comando": " ".join('"%s"' % c if " " in c else c for c in cmd),
        "codigo_de_saida": rc,
        "codigo_legivel": codigo_legivel(rc),
        "envelope": envelope,
        "proveniencia": {
            "sha256_do_modelo": _sha(a.modelo),
            "sha256_dos_perfis": {k: _sha(os.path.join(t, k + ".json"))
                                  for k in ("machine", "process", "filament")},
            "sha256_da_saida": _sha(saida_3mf) if gerou else None,
            "fatiador": a.orca,
            "sha256_do_fatiador": _sha(a.orca),
            "nota": ("hashes calculados nesta execucao sobre os arquivos desta execucao. "
                     "Sem eles, uma aprovacao nao pode ser amarrada aos bytes entregues, "
                     "porque a limpeza remove a area de trabalho."),
        },
        "gerou_3mf": gerou,
        "tamanho_3mf_bytes": os.path.getsize(saida_3mf) if gerou else 0,
        "slice_info": info,
        "stdout": so[:2000],
        "stderr": se[:2000],
        "log_do_fatiador": log_relevante[:30],
        "linhas_de_log_filtradas_como_benignas": len(log_linhas) - len(log_relevante),
        "processo_concluido": processo_concluido,
        "saida_gerada": saida_gerada,
        "checagens_aprovadas": checagens_aprovadas,
        "aprovado": aprovado,
        "motivos_de_reprovacao": sorted(set(motivos)),
        "acao": ("O fatiador produziu saida nas condicoes verificadas e nenhuma checagem "
                 "reprovou." if aprovado else
                 "BARRADO. Corrija os motivos acima antes de seguir."),
        "aviso": ("Isto afirma que o fatiador produziu saida com ESTES perfis e ESTA geometria. "
                  "Nao afirma que a peca esta correta de cota, nem que vai imprimir bem em "
                  "outra maquina, material ou perfil."),
        "diretorio_de_trabalho": t,
    }
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    print(txt)
    if not a.manter and os.path.isfile(os.path.join(t, MARCADOR)):
        shutil.rmtree(t, ignore_errors=True)   # so a subpasta desta execucao, e so com marcador
    return 0 if aprovado else 1


if __name__ == "__main__":
    sys.exit(main())
