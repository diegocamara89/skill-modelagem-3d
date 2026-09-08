"""Gera a geometria sintetica do caso 2 (projeto do zero, sem peca-fonte).

Abrigo prismatico com escadas internas, todo alinhado a eixo, na escala do teste de
universalidade: 300 mm de altura e planta = envelope da maquina menos 10 por cento em
largura e profundidade. Serve para checar que o extrator NAO inventa datum inclinado
onde nao existe interface de acoplamento.
"""
import numpy as np
import trimesh

ENVELOPE = 256.0                 # lado do envelope da maquina, mm
PLANTA = ENVELOPE * 0.90         # -10% em largura e profundidade
ALTURA = 300.0
PAREDE = 3.0
PISO = 4.0
N_DEGRAUS = 8
PROF_DEGRAU = 40.0
LARG_DEGRAU = 90.0


def caixa(dx, dy, dz, centro):
    b = trimesh.creation.box(extents=(dx, dy, dz))
    b.apply_translation(centro)
    return b


def main():
    ext = caixa(PLANTA, PLANTA, ALTURA, (0, 0, ALTURA / 2))
    cav = caixa(PLANTA - 2 * PAREDE, PLANTA - 2 * PAREDE, ALTURA - PISO,
                (0, 0, PISO + (ALTURA - PISO) / 2))
    corpo = trimesh.boolean.difference([ext, cav])

    passo_h = (ALTURA - PISO) / (N_DEGRAUS + 1)
    degraus = []
    for i in range(N_DEGRAUS):
        h = PISO + (i + 1) * passo_h
        y = -PLANTA / 2 + PAREDE + PROF_DEGRAU / 2 + (i % 2) * (PLANTA - 2 * PAREDE - PROF_DEGRAU)
        degraus.append(caixa(LARG_DEGRAU, PROF_DEGRAU, PISO, (0, y, h)))
    peca = trimesh.boolean.union([corpo] + degraus)

    porta = caixa(70, 3 * PAREDE, 90, (0, -PLANTA / 2, PISO + 45))
    peca = trimesh.boolean.difference([peca, porta])

    peca.export("caso2_abrigo.stl")
    print("caso2_abrigo.stl")
    print("  triangulos      :", len(peca.faces))
    print("  watertight      :", peca.is_watertight)
    print("  caixa mm        :", np.round(peca.extents, 3).tolist())
    print("  volume cm3      :", round(peca.volume / 1000.0, 1) if peca.is_watertight else None)
    print("  altura vs env.  : %.1f mm de peca contra %.1f mm de envelope -> %s"
          % (peca.extents[2], ENVELOPE,
             "ESTOURA, nasce dividida" if peca.extents[2] > ENVELOPE else "cabe"))


if __name__ == "__main__":
    main()
