"""exemplo_b123d.py - modelo parametrico minimo em build123d, modo algebra.

Geometria SINTETICA: um suporte de parede com aba, nervuras e furos. Serve para
exercitar as seis regras que a pesquisa produziu, nao para ser uma peca util.

Uso: python exemplo_b123d.py [--largura 60] [--saida .]

AS SEIS REGRAS QUE ESTE ARQUIVO DEMONSTRA:

1. Tudo sai de poucos parametros. Trocar um numero produz uma familia de pecas, nao
   uma peca. Nenhuma cota escrita duas vezes.
2. Nunca acumular com += dentro de laco. A documentacao oficial mede 4,76 s contra
   0,19 s, cerca de 25 vezes, entre acumular a cada volta e juntar tudo de uma vez.
3. Arredondamento por ultimo e com o menor raio que resolve. O defeito de fillets
   tangentes do nucleo geometrico so foi corrigido numa versao que ainda nao chegou a
   nenhum pacote de Python: se o raio consome a face plana inteira, ele falha.
4. Nunca escolher aresta por indice. A lista que o seletor devolve NAO tem ordem
   garantida. Ordenar ou filtrar por propriedade geometrica, sempre.
5. A fonte editavel do projeto e o CODIGO, com seus parametros e versoes travadas. O
   arquivo de intercambio e o RESULTADO CAD daquela execucao, e a malha e derivada dele.
   Promover o intercambio a fonte da verdade perde a capacidade de alterar o projeto.
   Tolerancia linear e angular sempre declaradas, nunca herdadas do padrao.
6. Verificar que a operacao deu certo, porque existe classe documentada de falha
   silenciosa: subtracao devolvendo forma vazia e extrusao sem peca, sem erro nenhum.
"""
import argparse, json, os, sys

from build123d import (Align, Axis, Box, Cylinder, GeomType, Mode, Plane, Pos, Rot,
                       SortBy, chamfer, export_step, export_stl, fillet)


def constroi(L=60.0, P=45.0, H=50.0, t=4.0, n_nervuras=3, d_furo=5.0, r_fillet=2.0,
             z_furo=0.50, h_nervura=0.60):
    """Suporte em L com nervuras. Toda cota derivada de L, P, H e t.

    ATENCAO ao par (z_furo, h_nervura). O topo do furo lateral fica em
    H*z_furo + d_furo/2 e o topo da nervura em H*h_nervura. Quando os dois valores
    caem perto, o nucleo geometrico produz contato tangente e a peca sai fechada mas
    nao-manifold. MEDIDO 07/09/2026 com H=50, d=5, t=4:

        z_furo  topo do furo   topo da nervura   arestas nao-manifold   3MF
        0.55       30.0             30.0                 2             recusa
        0.55       29.5*            30.0                 4             recusa
        0.50       27.5             30.0                 0             aceita

    (*) com d_furo=4. Deixar 0,5 mm de material foi PIOR que a tangencia exata.
    O padrao aqui e 0.50 justamente para nao entregar a coincidencia. Este e o
    argumento pratico para varrer a familia de parametros em vez de conferir uma peca:
    o mesmo codigo e limpo num valor e defeituoso no vizinho.
    """
    # --- corpo: duas placas em L ---
    base = Box(L, P, t, align=(Align.CENTER, Align.MIN, Align.MIN))
    costas = Box(L, t, H, align=(Align.CENTER, Align.MIN, Align.MIN))
    corpo = base + costas

    # --- REGRA 2: nervuras juntas numa lista, um unico fuse no fim ---
    passo = L / (n_nervuras + 1)
    nervuras = []
    for i in range(1, n_nervuras + 1):
        x = -L / 2 + i * passo
        nervuras.append(Pos(x, 0, 0) *
                        Box(t, P * 0.6, H * h_nervura,
                            align=(Align.CENTER, Align.MIN, Align.MIN)))
    corpo = corpo + nervuras          # uma soma, nao n somas

    # --- furos: derivados dos parametros, nunca de numero solto ---
    furos = []
    for x in (-L / 2 + passo, L / 2 - passo):
        furos.append(Pos(x, P * 0.6, H * z_furo) *
                     Rot(90, 0, 0) * Cylinder(d_furo / 2, t * 3))
    for y in (P * 0.35, P * 0.75):
        furos.append(Pos(0, y, -t) * Cylinder(d_furo / 2, t * 3,
                                              align=(Align.CENTER, Align.CENTER, Align.MIN)))
    corpo = corpo - furos

    # --- REGRA 4 e 3: seleciona por propriedade geometrica, arredonda por ultimo ---
    verticais = (corpo.edges()
                 .filter_by(GeomType.LINE)
                 .filter_by(Axis.Z)
                 .sort_by(SortBy.LENGTH)[-4:])
    if verticais:
        corpo = fillet(verticais, radius=min(r_fillet, t / 2 - 0.01))
    # chanfro na aresta que toca a mesa: escolhida por posicao, nao por indice
    na_mesa = [e for e in corpo.edges().filter_by(GeomType.LINE)
               if abs(e.center().Z) < 1e-6]
    if na_mesa:
        try:
            corpo = chamfer(na_mesa, length=0.4)
        except Exception as e:
            print("  chanfro da base recusado pelo nucleo (%s): seguindo sem ele"
                  % type(e).__name__)
    return corpo


def verifica(peca, esperado_solidos=1):
    """REGRA 6: confirmar que a operacao produziu algo, em vez de supor."""
    solidos = peca.solids()
    v = float(peca.volume)
    problemas = []
    if len(solidos) != esperado_solidos:
        problemas.append("esperava %d solido, obtive %d" % (esperado_solidos, len(solidos)))
    if v <= 0:
        problemas.append("volume %.4f nao positivo: a operacao falhou em silencio" % v)
    bb = peca.bounding_box()
    return {"n_solidos": len(solidos),
            "volume_mm3": round(v, 3),
            "caixa_mm": [round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)],
            "n_faces": len(peca.faces()),
            "n_arestas": len(peca.edges()),
            "ok": not problemas,
            "problemas": problemas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--largura", type=float, default=60.0)
    ap.add_argument("--profundidade", type=float, default=45.0)
    ap.add_argument("--altura", type=float, default=50.0)
    ap.add_argument("--parede", type=float, default=4.0)
    ap.add_argument("--nervuras", type=int, default=3)
    ap.add_argument("--saida", default=".")
    a = ap.parse_args()

    import time
    t0 = time.time()
    peca = constroi(a.largura, a.profundidade, a.altura, a.parede, a.nervuras)
    t_build = time.time() - t0
    v = verifica(peca)
    if not v["ok"]:
        print(json.dumps({"construcao": v}, indent=1, ensure_ascii=False))
        raise SystemExit("BARRADO na verificacao: " + "; ".join(v["problemas"]))

    os.makedirs(a.saida, exist_ok=True)
    base = os.path.join(a.saida, "exemplo_suporte")
    # REGRA 5: resultado CAD primeiro, malha derivada depois, tolerancia declarada.
    # A fonte editavel e este arquivo, nao o .step.
    export_step(peca, base + ".step")
    export_stl(peca, base + ".stl", tolerance=0.01, angular_tolerance=0.1)
    tam = {e: os.path.getsize(base + e) for e in (".step", ".stl")
           if os.path.isfile(base + e)}

    print(json.dumps({
        "parametros": {"L": a.largura, "P": a.profundidade, "H": a.altura,
                       "t": a.parede, "nervuras": a.nervuras},
        "tempo_de_construcao_s": round(t_build, 3),
        "construcao": v,
        "arquivos": tam,
        "tolerancia_de_malha": {"linear_mm": 0.01, "angular_rad": 0.1,
                                "nota": "declarada, nao herdada do padrao"},
        "proximo_passo": "rodar check_mesh.py no .stl e slice_check.py no mesmo arquivo",
    }, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
