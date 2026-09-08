"""check_mesh.py - portao de validade de malha. BARRA booleana e exportacao.

Uso: python check_mesh.py --malha peca.stl [--json out.json]

Devolve apto_para_booleana e volume_confiavel. Se apto_para_booleana for falso, o
agente NAO deve seguir para operacao booleana nem exportar para impressao: conserta
primeiro e roda de novo.

Sobre precisao: a ponte de booleana do trimesh converte para float32. Aqui a malha vai
para o kernel por Mesh64, que preserva float64, e o campo precisao_no_kernel_de_malha
diz qual caminho foi usado de fato, em vez de deixar isso suposto. Float32 nao destroi
cota em toda situacao; depende de escala, posicao e tolerancia. O ponto e declarar.
"""
import argparse, json, sys
import numpy as np


def mede_sobreposicao(m, n_componentes, tolerancia_mm3=1e-6):
    """Os componentes desta malha se sobrepoem? Mede, em vez de supor.

    Acrescentado em 08/09/2026. `volume_confiavel` afirmava confianca a partir de
    estanqueidade, e casca fechada sobreposta a outra casca fechada e estanque. A
    unica forma de saber e comparar a soma dos volumes com o volume da UNIAO."""
    fora = {"medida": False, "ha_sobreposicao": False,
            "n_componentes": int(n_componentes) if n_componentes else None,
            "volume_da_uniao_mm3": None, "volume_sobreposto_mm3": None,
            "por_que": ("soma das cascas menos volume da uniao. Positivo significa "
                        "material contado duas vezes.")}
    if not n_componentes or n_componentes < 2:
        fora["motivo"] = "componente unico: nao ha par para se sobrepor"
        fora["medida"] = True
        return fora
    try:
        partes = m.split(only_watertight=False)
        if len(partes) < 2:
            fora["motivo"] = "a divisao em componentes nao devolveu duas partes"
            return fora
        soma = float(sum(abs(p.volume) for p in partes))
        uniao = partes[0]
        for p in partes[1:]:
            uniao = uniao.union(p)
        v_uniao = float(abs(uniao.volume))
        excesso = soma - v_uniao
        fora.update({"medida": True,
                     "soma_das_cascas_mm3": round(soma, 6),
                     "volume_da_uniao_mm3": round(v_uniao, 6),
                     "volume_sobreposto_mm3": round(excesso, 6),
                     "ha_sobreposicao": bool(excesso > tolerancia_mm3),
                     "tolerancia_mm3": tolerancia_mm3})
    except Exception as e:                                        # noqa: BLE001
        fora["motivo"] = ("nao foi possivel medir a uniao: %s: %s. Sem esta medida, "
                          "volume_confiavel NAO pode ser afirmado."
                          % (type(e).__name__, e))
        fora["ha_sobreposicao"] = True     # na duvida, nao afirmar confianca
    return fora


def analisa(caminho):
    import trimesh
    m = trimesh.load(caminho, force="mesh", process=False)
    if not hasattr(m, "faces"):
        raise SystemExit("nao e uma malha unica: " + caminho)
    v_antes = int(len(m.vertices))
    m.merge_vertices()
    v_depois = int(len(m.vertices))

    # arestas por numero de faces incidentes
    ar = np.sort(m.edges_sorted, axis=1)
    _, inv, cont = np.unique(ar, axis=0, return_inverse=True, return_counts=True)
    n_por_aresta = cont
    abertas = int((n_por_aresta == 1).sum())
    excesso = int((n_por_aresta > 2).sum())
    normais_ok = bool(m.is_winding_consistent)
    # ACRESCENTADO em M0.5: a contagem de componentes conexos e requisito de topologia
    # declaravel, e nao existia medida para ela. Sem medida, o requisito seria
    # NAO_IMPLEMENTADA, e nao aprovado por omissao.
    try:
        n_componentes = int(len(m.split(only_watertight=False)))
    except Exception as e:
        n_componentes = None
        erro_componentes = "%s: %s" % (type(e).__name__, e)
    else:
        erro_componentes = None

    areas = m.area_faces
    degeneradas = int((areas <= 1e-12).sum())
    tri = m.faces
    dup = int(len(tri) - len(np.unique(np.sort(tri, axis=1), axis=0)))

    fechada = bool(m.is_watertight)
    euler = int(m.euler_number)
    vol = float(m.volume) if fechada else None
    vol_negativo = bool(fechada and vol is not None and vol < 0)

    # status do kernel de malha, em float64
    status_manifold, auto_interseccao, precisao = None, None, None
    try:
        import manifold3d as m3
        # CORRIGIDO 07/09/2026 depois de revisao externa. Passar array float64 para
        # m3.Mesh NAO preserva precisao: a classe guarda em float32. MEDIDO neste
        # ambiente: 1,0000000000000011 entra e sai como 1,0. Quem preserva e m3.Mesh64.
        # A versao anterior deste arquivo afirmava no comentario que evitava a truncagem,
        # e nao evitava.
        vert = np.ascontiguousarray(m.vertices, dtype=np.float64)
        tri = np.ascontiguousarray(m.faces, dtype=np.uint32)
        if hasattr(m3, "Mesh64"):
            mg = m3.Mesh64(vert_properties=vert, tri_verts=tri)
            precisao = "float64 via Mesh64"
        else:
            mg = m3.Mesh(vert_properties=vert, tri_verts=tri)
            precisao = "float32: Mesh64 indisponivel nesta versao"
        man = m3.Manifold(mg)
        status_manifold = str(man.status())
        # MEDIDO 07/09/2026: o construtor solda e conserta em silencio, e devolveu
        # Error.NoError numa malha com 99 arestas nao-manifold. Portanto o status NAO
        # e oraculo de validade: serve so para detectar recusa dura do kernel.
        auto_interseccao = False
        tri_saida = int(len(man.to_mesh().tri_verts))
        if tri_saida != int(len(m.faces)):
            status_manifold += " (kernel alterou a malha: %d -> %d facetas)" % (len(m.faces), tri_saida)
    except Exception as e:
        status_manifold = "indisponivel: %s" % type(e).__name__
        precisao = None

    motivos = []
    if abertas:
        motivos.append("%d arestas abertas (uma face so)" % abertas)
    if excesso:
        motivos.append(
            "%d arestas com mais de duas faces (nao-manifold)%s" % (
                excesso,
                ". Fechada mas nao-manifold. MEDIDO 07/09/2026: a causa tipica nao e a "
                "malha, e a geometria: contato tangente entre duas features, ou uma lasca "
                "de material fino sobrando entre elas. Numa peca de teste, deixar 0,5 mm "
                "acima de um furo deu 4 arestas assim, MAIS que a tangencia exata, que deu "
                "2; separar as features por 2,5 mm limpou. O fatiador costuma aceitar; o "
                "escritor de 3MF recusa, e esta certo em recusar."
                if abertas == 0 else ""))
    if degeneradas:
        motivos.append("%d facetas de area zero" % degeneradas)
    if dup:
        motivos.append("%d facetas duplicadas" % dup)
    if not normais_ok:
        motivos.append("orientacao de faces inconsistente")
    if vol_negativo:
        motivos.append("volume assinado negativo: normais apontando para dentro")
    # CORRIGIDO 07/09/2026 depois da segunda revisao externa. A versao anterior so
    # acrescentava motivo quando o status continha "indisponivel". Um status de ERRO
    # devolvido normalmente pelo kernel era medido e nao entrava na decisao.
    st = str(status_manifold)
    if "indisponivel" in st:
        motivos.append("kernel de malha indisponivel: %s" % st)
    elif "NoError" not in st:
        motivos.append("kernel de malha recusou a malha: %s" % st)
    elif "kernel alterou a malha" in st:
        motivos.append("o kernel de malha teve que ALTERAR a malha para aceita-la: %s. "
                       "A malha entregue nao e a malha que o kernel considera valida." % st)

    apto = len(motivos) == 0
    # A sobreposicao entre componentes NAO entra em motivos_de_reprovacao, e a
    # distincao e deliberada: esta lista e sobre malha quebrada, e uma malha com duas
    # cascas sobrepostas nao esta quebrada — ela e apta a booleana. O que ela nao tem e
    # volume confiavel. Misturar as duas coisas seria o mesmo erro que este portao
    # existe para evitar: confundir malha valida com peca correta.
    sobreposicao = mede_sobreposicao(m, n_componentes)
    aviso_de_volume = None
    if sobreposicao["ha_sobreposicao"]:
        aviso_de_volume = (
            "VOLUME NAO CONFIAVEL: os %s componentes se sobrepoem em %s mm3, entao a "
            "soma das cascas conta material duas vezes. Volume da uniao: %s mm3, "
            "contra %s mm3 somados. A malha em si esta apta; o numero de volume nao "
            "pode ser usado como material da peca."
            % (n_componentes, sobreposicao["volume_sobreposto_mm3"],
               sobreposicao["volume_da_uniao_mm3"],
               sobreposicao.get("soma_das_cascas_mm3")))
    elif not sobreposicao["medida"]:
        aviso_de_volume = (
            "VOLUME NAO CONFIAVEL: nao foi possivel medir sobreposicao entre "
            "componentes (%s). Sem essa medida, confianca no volume nao pode ser "
            "afirmada." % sobreposicao.get("motivo"))
    return {
        "arquivo": caminho,
        "triangulos": int(len(m.faces)),
        "vertices_antes_de_soldar": v_antes,
        "vertices_depois_de_soldar": v_depois,
        "fechada_watertight": fechada,
        "euler": euler,
        "arestas_abertas": abertas,
        "arestas_com_mais_de_2_faces": excesso,
        "facetas_degeneradas": degeneradas,
        "facetas_duplicadas": dup,
        "orientacao_consistente": normais_ok,
        "n_componentes_conexos": n_componentes,
        "erro_ao_contar_componentes": erro_componentes,
        "volume_mm3": round(vol, 3) if vol is not None else None,
        "volume_assinado_negativo": vol_negativo,
        "status_kernel_malha": status_manifold,
        "precisao_no_kernel_de_malha": precisao,
        "caixa_mm": [round(float(x), 4) for x in m.extents],
        "apto_para_booleana": apto,
        # CORRIGIDO 08/09/2026, depois de validacao adversarial: era
        # `fechada and not vol_negativo`, e isso NAO basta. Duas cascas fechadas
        # SOBREPOSTAS somam volume e contam o material comum duas vezes. Reproduzido:
        # dois cubos de lado 10 deslocados 5 em x, na mesma malha -> 2000 mm3
        # declarados confiaveis, uniao real 1500, excesso de 500 (33% sobre a uniao),
        # com "Pode seguir". A contagem de componentes ja estava exposta e nao
        # participava desta conclusao.
        "volume_confiavel": bool(fechada and not vol_negativo
                                 and not sobreposicao["ha_sobreposicao"]),
        "sobreposicao_entre_componentes": sobreposicao,
        "motivos_de_reprovacao": motivos,
        "aviso_de_volume": aviso_de_volume,
        "acao": (("Pode seguir na malha. " + aviso_de_volume) if (apto and aviso_de_volume)
                 else "Pode seguir." if apto else
                 "BARRADO. Conserte os motivos acima e rode de novo. Nao faca booleana nem "
                 "exporte para impressao com a malha neste estado."),
        "aviso": ("Malha valida NAO significa peca correta. Este portao pega malha quebrada, "
                  "nao geometria errada. Uma peca pode passar aqui e estar totalmente fora de cota."),
        "aviso_kernel": ("status_kernel_malha nao e oraculo de validade: o construtor do manifold3d "
                         "solda e conserta em silencio. Quem reprova aqui sao as contagens "
                         "topologicas acima. E precisao_no_kernel_de_malha diz em que precisao "
                         "a malha foi entregue ao kernel: float32 nao destroi cota sempre, mas "
                         "depende de escala, posicao e tolerancia, entao a informacao fica "
                         "explicita em vez de suposta."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--malha", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    out = analisa(a.malha)
    t = json.dumps(out, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(t)
    print(t)
    return 0 if out["apto_para_booleana"] else 1


if __name__ == "__main__":
    sys.exit(main())
