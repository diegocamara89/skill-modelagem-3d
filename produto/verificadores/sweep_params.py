"""sweep_params.py - varre a familia de parametros e barra as variantes defeituosas.

Uso:
  python sweep_params.py --modulo exemplo_b123d --funcao constroi \
      --grade "z_furo=0.45,0.50,0.55;d_furo=4,5" [--saida var] [--json out.json]

POR QUE ESTA FERRAMENTA EXISTE: "o modelo e parametrico" e uma afirmacao, nao um fato,
enquanto alguem so conferiu um valor. MEDIDO 07/09/2026 num suporte sintetico: o MESMO
codigo saiu fechado e valido num valor de parametro e fechado mas nao-manifold no
vizinho, porque duas expressoes independentes cairam a fracao de milimetro uma da outra.
A malha exportada nao acusou; so o escritor de 3MF recusou.

Conclusao que a ferramenta implementa: quem entrega uma familia tem que varrer a
familia. Conferir a peca do meio nao diz nada sobre as pontas.

O PORTAO USADO AQUI, do mais fraco ao mais forte:
  1. solido existe e volume e positivo      -> pega falha silenciosa de booleana
  2. malha sem aresta aberta, sem degenerada -> pega casca rompida
  3. escritor de 3MF aceita                  -> pega tangencia e lasca de material fino
O terceiro e o mais severo e o unico que pegou o defeito descrito acima.
"""
import argparse, importlib, itertools, json, os, sys

import numpy as np


class ErroOperacional(Exception):
    """Falha do SISTEMA, nao da geometria. CORRIGIDO em M0.2: o portao de 3MF capturava
    qualquer excecao do escritor e devolvia passou=False, ou seja, falha de permissao, de
    disco ou de dependencia era contada como reprovacao por GEOMETRIA. O laco externo
    ainda marcava a variante como AVALIADA, e uma mutacao que exige apenas "a varredura
    reprovou" recebia credito por um defeito geometrico que nunca foi exercitado.

    Carrega codigo e etapa porque quem consome precisa saber ONDE parou, e leva as etapas
    ja concluidas como evidencia de que a injecao atingiu a etapa pretendida, e nao uma
    anterior."""

    def __init__(self, codigo, etapa, causa, caminho=None, concluidas=None):
        super().__init__("%s em %s: %s" % (codigo, etapa, causa))
        self.codigo = codigo
        self.etapa = etapa
        self.causa = causa
        self.caminho = caminho
        self.concluidas = list(concluidas or ())


def classifica_falha_de_escrita(exc):
    """ImportError e dependencia ausente. A familia OSError vem do sistema. Qualquer
    outra excecao e INDETERMINADA, e quem decide e a medicao de confere_escrita.

    MEDIDO em M0.2, e a medicao derrubou a versao anterior desta funcao: com o alvo
    ocupado por um diretorio, o escritor de 3MF nao levanta OSError. Levanta
    lib3mf.Lib3MF.ELib3MFException com error_code 5, que a propria biblioteca chama de
    GENERICEXCEPTION, e o texto vinha como "The specified file could not be created".
    Ou seja: o codigo numerico da biblioteca NAO separa falha de E/S de recusa de
    formato, e separar pela frase seria o defeito que M0.3 corrige. A versao anterior
    tratava tudo que nao fosse OSError como geometrico, e por isso contava falha de
    permissao como reprovacao por geometria. O aceite pegou isso."""
    if isinstance(exc, (ImportError, ModuleNotFoundError)):
        return ("operacional", "E_DEP_AUSENTE")
    if isinstance(exc, OSError):
        return ("operacional", "E_EXPORT_3MF")
    return ("indeterminada", None)


def confere_escrita(caminho):
    """Devolve None quando o caminho aceita escrita, ou a causa quando nao aceita.

    Existe porque a biblioteca nao permite discriminar a causa pelo codigo dela. Em vez
    de interpretar a mensagem, a pergunta e respondida por medicao propria e verificavel:
    o caminho de saida aceita escrita, sim ou nao. Isso roda ANTES de chamar o escritor,
    para que impedimento de sistema nunca chegue a virar evidencia de geometria, e
    DEPOIS de uma falha, para classificar o que a biblioteca nao classificou."""
    pasta = os.path.dirname(os.path.abspath(caminho)) or "."
    if not os.path.isdir(pasta):
        return "o diretorio de saida %s nao existe" % pasta
    if os.path.isdir(caminho):
        return "o caminho de saida %s esta ocupado por um diretorio" % caminho
    existia = os.path.isfile(caminho)
    try:
        with open(caminho, "ab"):
            pass
        if not existia and os.path.getsize(caminho) == 0:
            os.remove(caminho)
        return None
    except OSError as e:
        return "%s: %s" % (type(e).__name__, e)


def parse_grade(s):
    """z_furo=0.45,0.50;d_furo=4,5  ->  [('z_furo',[0.45,0.5]), ('d_furo',[4.0,5.0])]"""
    eixos = []
    for parte in s.split(";"):
        parte = parte.strip()
        if not parte:
            continue
        if "=" not in parte:
            raise SystemExit("eixo invalido (esperado chave=v1,v2): " + parte)
        k, vs = parte.split("=", 1)
        vals = []
        for v in vs.split(","):
            v = v.strip()
            try:
                vals.append(int(v) if re_int(v) else float(v))
            except ValueError:
                vals.append(v)
        eixos.append((k.strip(), vals))
    return eixos


def re_int(v):
    return v.lstrip("-").isdigit()


def metricas_malha(caminho):
    import trimesh
    m = trimesh.load(caminho, force="mesh", process=False)
    m.merge_vertices()
    ar = np.sort(m.edges_sorted, axis=1)
    _, _, cont = np.unique(ar, axis=0, return_inverse=True, return_counts=True)
    return {"triangulos": int(len(m.faces)),
            "arestas_abertas": int((cont == 1).sum()),
            "arestas_com_mais_de_2_faces": int((cont > 2).sum()),
            "facetas_degeneradas": int((m.area_faces <= 1e-12).sum()),
            "fechada_watertight": bool(m.is_watertight),
            "orientacao_consistente": bool(m.is_winding_consistent)}


def avalia(peca, tmp_stl, tol, ang, representacao="solido", n_esperado=1,
           borda="obrigatoria"):
    """CORRIGIDO 07/09/2026: o contrato era sempre "um solido com volume positivo", o que
    reprova montagem parametrica legitima e superficie parametrica. Agora o contrato vem
    da representacao declarada."""
    from build123d import Mesher, export_stl
    r = {"portao_1_solido": None, "portao_2_malha": None, "portao_3_3mf": None,
         "representacao": representacao}
    solidos = peca.solids()
    vol = float(peca.volume)
    if representacao == "superficie":
        ok1 = len(peca.faces()) > 0 and len(solidos) == 0
        det1 = {"n_faces": len(peca.faces()), "n_solidos": len(solidos),
                "contrato": "superficie: faces presentes e zero solidos"}
    elif representacao == "montagem":
        ok1 = len(solidos) == n_esperado and vol > 0
        det1 = {"n_solidos": len(solidos), "n_solidos_esperado": n_esperado,
                "volume_mm3": round(vol, 3), "contrato": "montagem: contagem declarada"}
    else:
        ok1 = len(solidos) == n_esperado and vol > 0
        det1 = {"n_solidos": len(solidos), "n_solidos_esperado": n_esperado,
                "volume_mm3": round(vol, 3), "contrato": "solido: contagem declarada"}
    r["portao_1_solido"] = dict(det1, passou=bool(ok1))
    # CORRIGIDO em M0.2: a exportacao de malha era chamada sem etapa propria, entao uma
    # falha de escrita aqui subia como "erro_de_construcao" e apontava a etapa errada.
    impedimento = confere_escrita(tmp_stl)
    if impedimento:
        raise ErroOperacional("E_EXPORT_STL", "exportacao_malha", impedimento,
                              caminho=tmp_stl, concluidas=["portao_1_solido"])
    try:
        export_stl(peca, tmp_stl, tolerance=tol, angular_tolerance=ang)
    except Exception as e:
        classe, codigo = classifica_falha_de_escrita(e)
        raise ErroOperacional(codigo if classe == "operacional" else "E_EXPORT_STL",
                              "exportacao_malha", "%s: %s" % (type(e).__name__, e),
                              caminho=tmp_stl, concluidas=["portao_1_solido"])
    r["etapas_concluidas"] = ["portao_1_solido", "exportacao_malha"]
    mm = metricas_malha(tmp_stl)
    # CORRIGIDO 07/09/2026 depois da quarta revisao externa. A representacao mudava so o
    # PRIMEIRO portao. O segundo continuava exigindo zero arestas abertas e estanqueidade, e
    # o terceiro sempre escrevia 3MF, entao superficie aberta legitima reprovava sempre.
    if representacao == "superficie":
        # CORRIGIDO em M0.5: exigia borda em TODA representacao de superficie, o que faz
        # de "superficie" um sinonimo de casca aberta e reprovaria casca fechada sem
        # solido, que tambem e superficie legitima. Agora a borda vem DECLARADA.
        tem_borda = mm["arestas_abertas"] > 0
        if borda == "obrigatoria":
            ok_borda = tem_borda
        elif borda == "proibida":
            ok_borda = not tem_borda
        else:
            ok_borda = True
        mm["borda_declarada"] = borda
        mm["tem_borda"] = tem_borda
        mm["passou"] = bool(mm["facetas_degeneradas"] == 0 and ok_borda)
        mm["contrato"] = ("superficie com borda declarada %r: %s, e nenhuma faceta "
                          "degenerada. A borda NAO e deduzida da representacao."
                          % (borda, {"obrigatoria": "exige arestas abertas",
                                     "proibida": "proibe arestas abertas",
                                     "indiferente": "nao julga borda"}[borda]))
        r["portao_2_malha"] = mm
        r["portao_3_3mf"] = {"passou": None, "erro": None,
                             "motivo": ("o formato 3MF exige malha manifold fechada, logo o "
                                        "portao nao se aplica a superficie aberta")}
        r["passou_tudo"] = bool(ok1 and mm["passou"])
        return r
    # CORRIGIDO 07/09/2026 depois de revisao externa. A versao anterior media
    # arestas_com_mais_de_2_faces e fechada_watertight, e NAO as usava na decisao.
    # Resultado: aprovou variante com 6 arestas nao-manifold e nao-fechada, e me levou a
    # afirmar que so o 3MF tinha pegado o defeito. Os dados tinham pegado; a decisao os
    # ignorou. Era exatamente o defeito que este projeto existe para evitar: portao
    # incapaz de revelar o erro que ele guarda.
    mm["passou"] = bool(mm["arestas_abertas"] == 0
                        and mm["arestas_com_mais_de_2_faces"] == 0
                        and mm["facetas_degeneradas"] == 0
                        and mm["orientacao_consistente"]
                        and mm["fechada_watertight"])
    r["portao_2_malha"] = mm
    # CORRIGIDO em M0.2: aqui era um except Exception unico que virava passou=False.
    # Agora recusa do formato e reprovacao geometrica, e falha do sistema PROPAGA com
    # codigo e etapa, sem entrar na contagem de reprovadas por geometria.
    alvo_3mf = os.path.splitext(tmp_stl)[0] + ".3mf"
    # impedimento de sistema e medido ANTES de chamar o escritor, para que ele nunca
    # possa aparecer como reprovacao por geometria
    impedimento = confere_escrita(alvo_3mf)
    if impedimento:
        raise ErroOperacional("E_EXPORT_3MF", "exportacao", impedimento,
                              caminho=alvo_3mf, concluidas=r.get("etapas_concluidas", []))
    try:
        ms = Mesher()
        ms.add_shape(peca, linear_deflection=tol, angular_deflection=ang)
        ms.write(alvo_3mf)
        tam = os.path.getsize(alvo_3mf) if os.path.isfile(alvo_3mf) else 0
        if tam <= 0:
            raise ErroOperacional("E_CONTRATO_SAIDA", "exportacao",
                                  "o escritor retornou sem erro e o arquivo de saida nao "
                                  "existe ou esta vazio", caminho=alvo_3mf,
                                  concluidas=r.get("etapas_concluidas", []))
        r["portao_3_3mf"] = {"passou": True, "erro": None, "caminho": alvo_3mf,
                             "bytes": tam}
        r["etapas_concluidas"] = r.get("etapas_concluidas", []) + ["escrita_3mf"]
    except ErroOperacional:
        raise
    except Exception as e:
        classe, codigo = classifica_falha_de_escrita(e)
        if classe == "operacional":
            raise ErroOperacional(codigo, "exportacao", "%s: %s" % (type(e).__name__, e),
                                  caminho=alvo_3mf,
                                  concluidas=r.get("etapas_concluidas", []))
        # a biblioteca nao disse a causa. Medir de novo: se o caminho nao aceita escrita,
        # a falha e do sistema, e chamar isso de geometria seria inventar evidencia.
        residual = confere_escrita(alvo_3mf)
        if residual:
            raise ErroOperacional("E_EXPORT_3MF", "exportacao",
                                  "o escritor falhou e o caminho de saida nao aceita "
                                  "escrita: %s (excecao: %s: %s)"
                                  % (residual, type(e).__name__, e),
                                  caminho=alvo_3mf,
                                  concluidas=r.get("etapas_concluidas", []))
        r["portao_3_3mf"] = {"passou": False, "erro": "%s: %s" % (type(e).__name__, e),
                             "caminho": alvo_3mf,
                             "classificacao": ("o caminho de saida aceita escrita, logo a "
                                               "recusa e do formato, portanto geometrica")}
    r["passou_tudo"] = all(r[k]["passou"] for k in
                           ("portao_1_solido", "portao_2_malha", "portao_3_3mf"))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", required=True)
    ap.add_argument("--funcao", default="constroi")
    ap.add_argument("--grade", required=True)
    ap.add_argument("--saida", default="varredura")
    ap.add_argument("--representacao", default="solido",
                    choices=["solido", "superficie", "montagem", "malha"])
    ap.add_argument("--n-solidos", type=int, default=1)
    ap.add_argument("--borda", default="obrigatoria",
                    choices=("obrigatoria", "proibida", "indiferente"),
                    help="requisito de topologia, so usado quando a representacao e "
                         "superficie. Nao e deduzido da representacao.")
    ap.add_argument("--tol", type=float, default=0.01)
    ap.add_argument("--ang", type=float, default=0.1)
    ap.add_argument("--json")
    a = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    mod = importlib.import_module(a.modulo)
    fn = getattr(mod, a.funcao)
    eixos = parse_grade(a.grade)
    os.makedirs(a.saida, exist_ok=True)

    nomes = [k for k, _ in eixos]
    combos = list(itertools.product(*[v for _, v in eixos]))
    linhas = []
    for i, combo in enumerate(combos):
        kw = dict(zip(nomes, combo))
        rot = "_".join("%s%s" % (k, v) for k, v in kw.items()).replace(".", "p")
        alvo = os.path.join(a.saida, "v_%s.stl" % rot)
        # CORRIGIDO 07/09/2026 depois da quarta revisao externa. Excecao de construcao ou
        # exportacao entrava em n_reprovadas como se fosse reprovacao GEOMETRICA, e uma
        # mutacao que so exige "a varredura reprovou" recebia credito por falha de
        # permissao ou dependencia. Agora cada variante tem estado operacional proprio.
        # CORRIGIDO em M0.2: o except unico dava a mesma etapa a construcao e a
        # exportacao. Agora a etapa decide o codigo, e a causa do sistema fica na causa.
        try:
            peca = fn(**kw)
            res = avalia(peca, alvo, a.tol, a.ang, a.representacao, a.n_solidos,
                         borda=a.borda)
            res["erro_de_construcao"] = None
            res["estado"] = "AVALIADA"
            res["codigo"] = None
            res["etapa"] = None
        except ErroOperacional as e:
            res = {"passou_tudo": False, "estado": "ERRO_OPERACIONAL",
                   "codigo": e.codigo, "etapa": e.etapa, "causa": e.causa,
                   "caminho_de_saida": e.caminho, "etapas_concluidas": e.concluidas,
                   "erro_de_construcao": None}
        except Exception as e:
            res = {"passou_tudo": False, "estado": "ERRO_OPERACIONAL",
                   "codigo": "E_CONSTRUCAO", "etapa": "construcao",
                   "causa": "%s: %s" % (type(e).__name__, e),
                   "etapas_concluidas": [],
                   "erro_de_construcao": "%s: %s" % (type(e).__name__, e)}
        res["parametros"] = kw
        linhas.append(res)
        m2 = res.get("portao_2_malha") or {}
        print("%-38s %s  solido=%-5s malha=%-5s 3mf=%-5s  abertas=%-3s >2faces=%-3s" % (
            rot,
            "OK " if res["passou_tudo"] else "FALHA",
            (res.get("portao_1_solido") or {}).get("passou"),
            m2.get("passou"),
            (res.get("portao_3_3mf") or {}).get("passou"),
            m2.get("arestas_abertas"), m2.get("arestas_com_mais_de_2_faces")))
        if res.get("estado") == "ERRO_OPERACIONAL":
            print("    %s em %s: %s" % (res.get("codigo"), res.get("etapa"),
                                        (res.get("causa") or "")[:140]))

    ok = [l for l in linhas if l["passou_tudo"]]
    com_erro = [l for l in linhas if l.get("estado") == "ERRO_OPERACIONAL"]
    reprovadas_geom = [l for l in linhas
                       if l.get("estado") == "AVALIADA" and not l["passou_tudo"]]
    out = {
        "modulo": a.modulo, "funcao": a.funcao, "grade": a.grade,
        "tolerancia": {"linear_mm": a.tol, "angular_rad": a.ang},
        "n_variantes": len(linhas), "n_aprovadas": len(ok),
        "n_reprovadas": len(linhas) - len(ok),
        "n_reprovadas_por_geometria": len(reprovadas_geom),
        "n_com_erro_operacional": len(com_erro),
        "houve_erro_operacional": bool(com_erro),
        "erros_operacionais": [{"parametros": l.get("parametros"),
                                "codigo": l.get("codigo"), "etapa": l.get("etapa"),
                                "causa": l.get("causa") or l.get("erro_de_construcao"),
                                "caminho_de_saida": l.get("caminho_de_saida"),
                                "etapas_concluidas": l.get("etapas_concluidas")}
                               for l in com_erro],
        "nota_de_estado": ("erro operacional NAO e reprovacao geometrica: a variante nao "
                           "foi avaliada. Quem consome este resultado tem que separar os "
                           "dois, senao falha de ambiente vira evidencia de geometria."),
        "variantes": linhas,
        "o_que_os_tres_portoes_dizem": (
            "solido existe com volume positivo, malha bem formada, e o escritor de 3MF "
            "aceita. Isso e evidencia GEOMETRICA. NAO diz imprimivel: nao passou por "
            "fatiador, envelope, perfil de maquina nem avaliacao fisica."),
        "veredito": (
            "As %d amostras da grade informada passaram nos tres portoes geometricos. Isso "
            "NAO demonstra validade dos valores intermediarios nem fora da grade, e nao "
            "afirma imprimibilidade." % len(linhas) if len(ok) == len(linhas) else
            "%d de %d amostras REPROVARAM. A familia nao pode ser entregue como parametrica "
            "sem restringir a faixa dos parametros ou corrigir a geometria."
            % (len(linhas) - len(ok), len(linhas))),
        "alcance_do_teste": ("pontos da grade informada, no dominio dado; nada e afirmado "
                             "sobre valores entre os pontos ou fora deles"),
        "aviso_cache": ("Cada variante e construida do zero de proposito. MEDIDO: reexportar a "
                        "MESMA forma com outra tolerancia devolve a malha em cache, com a "
                        "contagem de triangulos igual, sem aviso nenhum."),
        "aviso": ("Passar nos tres portoes e evidencia geometrica: solido nao vazio, malha bem "
              "formada e aceita pelo escritor de 3MF. NAO significa imprimivel, porque nao "
              "houve fatiador nem envelope, e nao significa correta de cota."),
    }
    print()
    print(out["veredito"])
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(txt)
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa: o JSON era montado e NUNCA
    # impresso. Quem chamasse esperando resultado estruturado no stdout recebia so o log,
    # e o caminho da modalidade parametrizar estava quebrado sem ninguem notar, porque
    # nenhum caso de teste o exercitava.
    print(txt)
    return 0 if len(ok) == len(linhas) else 1


if __name__ == "__main__":
    sys.exit(main())
