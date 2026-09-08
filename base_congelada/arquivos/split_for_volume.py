"""split_for_volume.py - decide orientacao e planos de corte quando a peca estoura a maquina.

Uso:
  python split_for_volume.py --malha peca.stl --envelope 256x256x256 [--margem 5]
                             [--carga z] [--janela 15] [--amostras 120] [--json out.json]

O QUE FAZ:
  1) testa as 6 permutacoes de eixo e diz quais cabem no envelope;
  2) se nenhuma cabe, escolhe a que exige MENOS pecas;
  3) mede o perfil de area de secao ao longo do eixo que estoura;
  4) parte dos cortes em partes iguais e desloca cada corte, dentro de uma janela, para
     o plano de MAIOR area de secao. Area de secao e um critério GEOMETRICO: mais area
     e mais superficie disponivel para a junta. Nao e conclusao estrutural. Resistencia
     de junta depende de geometria de encaixe, adesivo ou fixador, orientacao de
     impressao de cada peca e direcao da carga, e nada disso e medido aqui;
  5) devolve o tamanho de cada peca e se cada uma cabe.

O QUE NAO FAZ E POR QUE:
  Nao escolhe o corte sozinho quando ha carga em jogo. Em PLA e ABS ensaiados na
  literatura, a resistencia entre camadas ficou em torno de metade da resistencia no
  plano; esse numero e do material e do ensaio, nao uma constante universal, e nao
  substitui avaliacao estrutural. O que segue dele e qualitativo e robusto: a direcao de
  impressao importa muito, logo o plano de corte e a orientacao de cada peca sao decisao
  ESTRUTURAL. Sem a direcao da carga principal declarada, o script mede e ordena
  candidatos, mas nao decide. Nao gera geometria de junta: propor macho,
  femea, pino ou rabo de andorinha com folga exige folga calibrada da maquina e do
  material, que nao e constante de tabela.
"""
import argparse, itertools, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

PERM = list(itertools.permutations(range(3)))
NOME = "XYZ"


def area_secao(malha, eixo, valor):
    """Area de material na secao. Delegado a secoes.py.

    CORRIGIDO 07/09/2026: a versao anterior tinha o codigo aqui, sem nodacao das linhas
    e com furo classificado por aninhamento 2D. Funcionava nas malhas prismaticas em que
    foi testada e devolvia ZERO poligonos numa malha com superficie curva, sem erro.
    """
    import secoes
    return secoes.area_de_material(malha, eixo, valor)


def perfil(malha, eixo, lo, hi, amostras, margem):
    zs = np.linspace(lo + margem, hi - margem, amostras)
    out = []
    for z in zs:
        a = area_secao(malha, eixo, float(z))
        if a is not None and a > 0:
            out.append((float(z), a))
    return out


def melhor_na_janela(pf, alvo, janela):
    cand = [(z, a) for z, a in pf if abs(z - alvo) <= janela]
    if not cand:
        return None
    z, a = max(cand, key=lambda t: t[1])
    a_alvo = min(pf, key=lambda t: abs(t[0] - alvo))[1]
    return {"corte_mm": round(z, 3),
            "area_secao_mm2": round(a, 2),
            "corte_ingenuo_mm": round(alvo, 3),
            "area_no_corte_ingenuo_mm2": round(a_alvo, 2),
            "ganho_de_area": round(a / a_alvo, 3) if a_alvo > 0 else None,
            "deslocamento_mm": round(z - alvo, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--malha", required=True)
    ap.add_argument("--envelope", required=True, help="ex.: 256x256x256 em mm")
    ap.add_argument("--margem", type=float, default=5.0, help="folga por peca dentro do envelope")
    ap.add_argument("--carga", choices=["x", "y", "z", "nenhuma"], default="nenhuma")
    ap.add_argument("--janela", type=float, default=15.0)
    ap.add_argument("--amostras", type=int, default=120)
    ap.add_argument("--json")
    a = ap.parse_args()

    import trimesh
    m = trimesh.load(a.malha, force="mesh", process=False)
    m.merge_vertices()
    try:
        env = np.array([float(x) for x in a.envelope.lower().split("x")], float)
    except ValueError:
        raise SystemExit("envelope invalido: use AxBxC com numeros, ex.: 256x256x256")
    # CORRIGIDO 07/09/2026 depois da terceira revisao externa. So a QUANTIDADE de
    # componentes era validada. Com envelope menor que duas margens, o util ficava
    # negativo, o teto da divisao dava numero nao positivo, o maximo com 1 transformava
    # isso em "uma peca por eixo", nenhum eixo entrava na lista de cortes, e o all() sobre
    # dicionario vazio devolvia particao_validada=True com cabe=False.
    if env.size != 3:
        raise SystemExit("envelope deve ter tres componentes, ex.: 256x256x256")
    if not np.isfinite(env).all() or (env <= 0).any():
        raise SystemExit("envelope tem que ser finito e positivo nos tres eixos: %s" % env.tolist())
    if not np.isfinite(a.margem) or a.margem < 0:
        raise SystemExit("margem tem que ser finita e nao negativa: %r" % a.margem)
    util = env - 2 * a.margem
    if (util <= 0).any():
        raise SystemExit("envelope util nao positivo em algum eixo (%s): a margem de %.3f mm "
                         "consome o envelope %s. Isso e erro de configuracao, nao particao."
                         % (util.tolist(), a.margem, env.tolist()))
    ext = np.array(m.extents, float)

    # 1) permutacoes de eixo
    ops = []
    for p in PERM:
        e = ext[list(p)]
        pecas = np.ceil(e / util).astype(int)
        pecas = np.maximum(pecas, 1)
        ops.append({
            "mapeamento": "".join(NOME[i] for i in p) + " -> " + NOME,
            "permutacao": list(p),
            "extensao_mm": [round(float(x), 2) for x in e],
            "cabe": bool((e <= util + 1e-9).all()),
            "pecas_por_eixo": pecas.tolist(),
            "total_de_pecas": int(pecas.prod()),
        })
    cabem = [o for o in ops if o["cabe"]]
    escolhida = cabem[0] if cabem else min(ops, key=lambda o: (o["total_de_pecas"], -min(o["extensao_mm"])))

    res = {
        "arquivo": a.malha,
        "envelope_mm": env.tolist(),
        "margem_mm": a.margem,
        "envelope_util_mm": util.tolist(),
        "extensao_da_peca_mm": [round(float(x), 3) for x in ext],
        "orientacoes": ops,
        "orientacao_escolhida": escolhida,
        "carga_declarada": a.carga,
    }

    if escolhida["cabe"]:
        res["veredito"] = "Cabe inteira nesta orientacao. Nenhum corte necessario."
        res["cortes"] = []
    else:
        p = escolhida["permutacao"]
        pecas = np.array(escolhida["pecas_por_eixo"])
        eixos_que_estouram = [i for i in range(3) if pecas[i] > 1]
        cortes_por_eixo = {}
        for i in eixos_que_estouram:
            eixo_orig = p[i]                       # eixo na malha original
            lo = float(m.bounds[0][eixo_orig]); hi = float(m.bounds[1][eixo_orig])
            pf = perfil(m, eixo_orig, lo, hi, a.amostras, 0.5)
            n_cortes = int(pecas[i]) - 1
            L = hi - lo
            propostas = []
            for k in range(1, n_cortes + 1):
                alvo = lo + L * k / (n_cortes + 1)
                mj = melhor_na_janela(pf, alvo, a.janela)
                if mj:
                    propostas.append(mj)
            # CORRIGIDO 07/09/2026 depois da segunda revisao externa. Os cortes eram
            # deslocados para a maior area e NAO eram revalidados: num comprimento igual a
            # duas vezes o limite util, o corte central cabe e o deslocado faz uma metade
            # estourar. Agora as pecas resultantes sao medidas e a particao so e declarada
            # VALIDADA se todas caberem, com os cortes em ordem crescente.
            limite = float(util[i])
            cortes_mm = sorted(p["corte_mm"] for p in propostas)
            fronteiras = [lo] + cortes_mm + [hi]
            pedacos = [round(fronteiras[k + 1] - fronteiras[k], 4)
                       for k in range(len(fronteiras) - 1)]
            estouram = [k for k, t_ in enumerate(pedacos) if t_ > limite + 1e-9]
            ordem_ok = cortes_mm == [p["corte_mm"] for p in propostas]
            validada = bool(propostas) and not estouram and len(propostas) == n_cortes
            # se o deslocamento estourou, cai para o corte em partes iguais, que cabe
            fallback = None
            if propostas and estouram:
                ing = sorted(p["corte_ingenuo_mm"] for p in propostas)
                fb = [lo] + ing + [hi]
                ped_ing = [round(fb[k + 1] - fb[k], 4) for k in range(len(fb) - 1)]
                if all(t_ <= limite + 1e-9 for t_ in ped_ing):
                    fallback = {"cortes_mm": ing, "pedacos_mm": ped_ing,
                                "nota": "corte em partes iguais, que cabe; a area de secao "
                                        "e menor, mas a particao e valida"}

            areas = [z_a[1] for z_a in pf]
            plano_ = bool(areas and (max(areas) - min(areas)) / max(areas) < 0.10)
            cortes_por_eixo[NOME[eixo_orig]] = {
                "particao_validada": validada,
                "limite_util_no_eixo_mm": round(limite, 4),
                "cortes_em_ordem_mm": cortes_mm,
                "pedacos_resultantes_mm": pedacos,
                "pedacos_que_estouram": estouram,
                "cortes_em_ordem_crescente": ordem_ok,
                "n_cortes_esperado": n_cortes,
                "n_propostas": len(propostas),
                "fallback_em_partes_iguais": fallback,
                "nota_validacao": (
                    "particao dimensionalmente validada: todos os pedacos cabem no limite "
                    "util deste eixo." if validada else
                    "CANDIDATOS ENCONTRADOS, PARTICAO NAO VALIDADA. %s Nao trate esta lista "
                    "como particao pronta."
                    % ("Pedacos %s estouram o limite util de %.2f mm. " % (estouram, limite)
                       if estouram else
                       "Nao ha proposta de corte utilizavel. " if not propostas else
                       "Numero de propostas diferente do numero de cortes necessario. ")),
                "perfil_de_secao_plano": plano_,
                "criterio_de_area_serve": not plano_,
                "nota_criterio": (
                    "Perfil de secao quase constante ao longo deste eixo: a area NAO distingue os "
                    "candidatos. Escolha o corte por outro criterio, e o criterio nao esta neste "
                    "script: nao atravessar feature funcional, cair em altura de piso ou degrau, "
                    "deixar a junta acessivel para montagem, e nao coincidir com a linha de carga."
                    if plano_ else
                    "Perfil de secao varia ao longo deste eixo: o corte de maior area e uma escolha "
                    "defensavel, sujeita a confirmacao da direcao de carga."),
                "eixo_na_malha_original": NOME[eixo_orig],
                "extensao_mm": round(L, 3),
                "n_cortes": n_cortes,
                "area_secao_min_mm2": round(min(areas), 2) if areas else None,
                "area_secao_max_mm2": round(max(areas), 2) if areas else None,
                "area_secao_mediana_mm2": round(float(np.median(areas)), 2) if areas else None,
                "cortes_propostos": propostas,
            }
        res["cortes"] = cortes_por_eixo
        # particao vazia NAO e particao validada quando a peca nao cabe
        res["particao_validada"] = bool(cortes_por_eixo) and all(
            c["particao_validada"] for c in cortes_por_eixo.values())
        if not cortes_por_eixo:
            res["erro_de_configuracao"] = (
                "a peca nao cabe e nenhum eixo foi marcado para corte. Isso indica envelope "
                "ou margem inconsistentes, nao particao aprovada.")
        res["veredito"] = ("NAO cabe. Melhor orientacao exige %d pecas (%s). Os cortes abaixo foram "
                           "deslocados do meio para o plano de maior area de secao dentro de uma "
                           "janela de %.0f mm." % (escolhida["total_de_pecas"],
                                                   " x ".join(map(str, escolhida["pecas_por_eixo"])),
                                                   a.janela))
        if a.carga == "nenhuma":
            res["decisao_pendente"] = (
                "DIRECAO DA CARGA NAO DECLARADA. Cada plano de corte vira uma junta, e a "
                "uniao entre pecas impressas em separado nao tem a resistencia do material "
                "continuo. Declare por onde passa a carga principal (--carga x|y|z) antes "
                "de fixar o corte.")
        else:
            paralela = [k for k in res["cortes"] if k.lower() == a.carga]
            # CORRIGIDO 07/09/2026 depois da terceira revisao externa: a versao anterior
            # concluia TRACAO e exigia junta mecanica so a partir do eixo de carga, sem
            # saber se a carga e tracao, compressao ou flexao, nem onde e aplicada. Isso e
            # diagnostico estrutural que nao foi medido.
            res["decisao_pendente"] = (
                ("A carga declarada (%s) e PARALELA a um eixo cortado, logo a junta cai no "
                 "caminho da carga. O script NAO sabe se essa carga e tracao, compressao ou "
                 "flexao, nem onde e aplicada: afirmar que a junta fica em tracao seria "
                 "diagnostico estrutural nao medido. Declare o tipo de carga e avalie."
                 % a.carga.upper()) if paralela else
                ("A carga declarada (%s) e transversal aos eixos cortados. Isso nao dispensa "
                 "avaliar o momento de flexao no plano da junta." % a.carga.upper()))
        res["nota_anisotropia"] = (
            "A uniao entre camadas e mais fraca que o material no plano. Em PLA e ABS ensaiados na "
            "literatura a razao ficou em torno de metade, mas isso e do material e do ensaio, nao "
            "uma constante para qualquer filamento. Se houver carga relevante, isso exige avaliacao "
            "com o material real. O que vale em geral: escolha a orientacao de impressao de CADA "
            "peca para que a carga corra ao longo das camadas, e trate isso como decisao de projeto, nao de acabamento.")
        res["nao_gerado"] = (
            "Geometria de junta NAO foi gerada. A folga de encaixe depende de maquina e material e "
            "tem que sair de cupom de teste medido, nao de constante. Faixas publicadas divergem em "
            "uma categoria inteira entre fontes de qualidade.")

    t = json.dumps(res, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(t)
    print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
