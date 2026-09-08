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


def avalia(peca, tmp_stl, tol, ang, representacao="solido", n_esperado=1):
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
    export_stl(peca, tmp_stl, tolerance=tol, angular_tolerance=ang)
    mm = metricas_malha(tmp_stl)
    # CORRIGIDO 07/09/2026 depois da quarta revisao externa. A representacao mudava so o
    # PRIMEIRO portao. O segundo continuava exigindo zero arestas abertas e estanqueidade, e
    # o terceiro sempre escrevia 3MF, entao superficie aberta legitima reprovava sempre.
    if representacao == "superficie":
        mm["passou"] = bool(mm["facetas_degeneradas"] == 0 and mm["arestas_abertas"] > 0)
        mm["contrato"] = ("superficie: exige borda (arestas abertas) e nenhuma faceta "
                          "degenerada. Estanqueidade NAO se aplica a casca sem espessura.")
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
    try:
        ms = Mesher()
        ms.add_shape(peca, linear_deflection=tol, angular_deflection=ang)
        ms.write(os.path.splitext(tmp_stl)[0] + ".3mf")
        r["portao_3_3mf"] = {"passou": True, "erro": None}
    except Exception as e:
        r["portao_3_3mf"] = {"passou": False, "erro": "%s: %s" % (type(e).__name__, e)}
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
        try:
            peca = fn(**kw)
            res = avalia(peca, alvo, a.tol, a.ang, a.representacao, a.n_solidos)
            res["erro_de_construcao"] = None
            res["estado"] = "AVALIADA"
        except Exception as e:
            res = {"passou_tudo": False, "estado": "ERRO_OPERACIONAL",
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
        if res.get("erro_de_construcao"):
            print("    erro de construcao:", res["erro_de_construcao"][:160])

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
                                "erro": l.get("erro_de_construcao")} for l in com_erro],
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
