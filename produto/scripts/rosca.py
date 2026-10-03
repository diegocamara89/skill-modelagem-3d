"""Rosca impressa M6 passo 1 (parafuso, porca e furo roscado) para FDM, pronta para usar.
Referência: projetar_para_imprimir.md, seção 3a. Padrão de um parafuso impresso que funciona (Pegmount, Jalba,
MakerWorld) e que o operador já imprimiu dezenas de vezes na A1.

Medidas do Pegmount (3MF do dono, 02/10/2026):
  macho: crista Ø5,88, raiz Ø4,74 (profundidade 0,57), passo 1,0, perfil de 60° (tipo métrico)
  fêmea: maior Ø6,59, menor Ø5,36  -> folga radial 0,35 na crista e 0,31 na raiz; 10 mm de rosca
O M4 do SKÅDIS (rustichands) espana: passo 0,7 e profundidade 0,4 com a mesma folga ~0,3 -> sobra ~0,1 de fio.

Desenho próprio (só os números vêm do Pegmount). Filete gerado como malha fechada em numpy e unido por
manifold3d (projetar_para_imprimir.md seção 3). Imprimir os eixos na VERTICAL.
Uso: import rosca as R; R.parafuso(comp), R.porca(alt), furo, fil = R.furo_roscado(z0, z1) -> peca = (peca - furo) + fil
"""
import math, numpy as np, manifold3d as mf

P = 1.0                 # passo
H = 0.57                # profundidade do fio do macho
CRISTA_M = 5.9          # Ø crista do macho
FOLGA_R = 0.33          # folga radial na crista e na raiz (Pegmount: 0,31 a 0,35)
FOLGA_AX = 0.19         # folga axial em cada flanco (= FOLGA_R * tan 30°)
TAN30 = math.tan(math.radians(30))
PLANO_M = 0.15          # largura da crista do macho
SEG = 120               # segmentos por volta


def raios():
    """(raiz e crista do macho, maior e menor da fêmea) em raio."""
    rc = CRISTA_M / 2
    rr = rc - H
    return rr, rc, rc + FOLGA_R, rr + FOLGA_R


def _filete(r_base, r_ponta, w_base, w_ponta, z0, altura, enterra):
    """filete trapezoidal helicoidal, malha fechada. r_base -> r_ponta (para dentro se r_ponta < r_base)."""
    s = 1 if r_ponta > r_base else -1
    prof = np.array([(r_base - s * enterra, -w_base / 2), (r_base, -w_base / 2), (r_ponta, -w_ponta / 2),
                     (r_ponta, w_ponta / 2), (r_base, w_base / 2), (r_base - s * enterra, w_base / 2)])
    n = len(prof)
    k = max(2, int(round(altura / P * SEG)) + 1)
    th = np.linspace(0.0, 2 * math.pi * altura / P, k)
    r, zz = prof[:, 0][None, :], prof[:, 1][None, :]
    V = np.stack([r * np.cos(th)[:, None], r * np.sin(th)[:, None],
                  zz + z0 + (P * th / (2 * math.pi))[:, None]], axis=-1).reshape(-1, 3)
    F = []
    for a in range(k - 1):
        for b in range(n):
            i0, i1 = a * n + b, a * n + (b + 1) % n
            F += [(i0, i1, i1 + n), (i0, i1 + n, i0 + n)]
    for c in range(1, n - 1):
        F.append((0, c + 1, c))
        F.append(((k - 1) * n, (k - 1) * n + c, (k - 1) * n + c + 1))
    F = np.array(F, dtype=np.uint32)
    m = mf.Manifold(mf.Mesh64(vert_properties=V.astype(np.float64), tri_verts=F))
    if m.volume() <= 0:
        m = mf.Manifold(mf.Mesh64(vert_properties=V.astype(np.float64), tri_verts=F[:, ::-1].copy()))
    return m


def _cyl(r, z0, z1, n=96):
    return mf.Manifold.cylinder(z1 - z0, r, r, n).translate((0, 0, z0))


def _cone(r0, r1, z0, z1, n=96):
    return mf.Manifold.cylinder(z1 - z0, r0, r1, n).translate((0, 0, z0))


def haste(comp):
    """haste roscada de z=0 a z=comp, eixo Z, com chanfro na ponta."""
    rr, rc, _, _ = raios()
    w_base = PLANO_M + 2 * H * TAN30
    m = _cyl(rr, 0, comp) + (_filete(rr, rc, w_base, PLANO_M, -P, comp + 2 * P, 0.1) ^ _cyl(rc + 1, 0, comp))
    ponta = _cyl(rc + 2, comp - 0.6, comp + 1) - _cone(rc, rc - 1.6, comp - 0.6, comp + 1.0)
    return m - ponta


def recartilhado(r, z0, z1, n_estrias=None):
    """cabeça/porca cilíndrica com estrias para o dedo."""
    n_estrias = n_estrias or max(12, round(2.2 * r))
    c = _cyl(r, z0, z1)
    for i in range(n_estrias):
        a = 2 * math.pi * i / n_estrias
        c -= _cyl(0.9, z0 - 1, z1 + 1, 24).translate((r * math.cos(a), r * math.sin(a), 0))
    return c


def parafuso(comp, r_cabeca=7.0, alt_cabeca=4.0):
    """parafuso de dedo: cabeça recartilhada em z ∈ [-alt, 0], rosca de 0 a comp. Imprime de cabeça para baixo."""
    cab = recartilhado(r_cabeca, -alt_cabeca, 0.0)
    ch = 0.5   # chanfro na quina de cima da cabeça (encosta na peça)
    cab -= _cyl(r_cabeca + 2, -ch, 1) - _cone(r_cabeca, r_cabeca - ch - 2, -ch, -ch + 2 + ch)
    return cab + haste(comp) + _cyl(raios()[0], -0.5, 0.5)


def furo_roscado(z0, z1, entrada=(True, True)):
    """volume a SUBTRAIR e filete interno a SOMAR para um furo roscado de z0 a z1 (eixo Z).
    Uso: peca = (peca - furo) + filete."""
    rr, rc, rM, rm = raios()
    # largura do vão do macho no raio rm, menos as folgas axiais
    w_macho_rm = PLANO_M + 2 * (rc - rm) * TAN30
    w_ponta = P - w_macho_rm - 2 * FOLGA_AX
    w_base = w_ponta + 2 * (rM - rm) * TAN30
    furo = _cyl(rM, z0 - 0.1, z1 + 0.1)
    for z, s, ok in ((z0, 1, entrada[0]), (z1, -1, entrada[1])):     # chanfro de entrada
        if ok:
            furo += _cone(rM + 0.6, rM - 0.4, z - s * 0.01, z + s * 1.0) if s > 0 else _cone(rM - 0.4, rM + 0.6, z - 1.0, z + 0.01)
    fil = _filete(rM, rm, min(w_base, P - 0.04), w_ponta, z0 - P, (z1 - z0) + 2 * P, 0.1)
    fil = fil ^ _cyl(rM + 0.5, z0, z1)
    for z, s, ok in ((z0, 1, entrada[0]), (z1, -1, entrada[1])):
        if ok:
            fil -= _cone(rM + 0.6, rM - 0.4, z - s * 0.01, z + s * 1.0) if s > 0 else _cone(rM - 0.4, rM + 0.6, z - 1.0, z + 0.01)
    return furo, fil


def porca(alt=6.0, r=7.0):
    """porca recartilhada, eixo Z, de 0 a alt."""
    corpo = recartilhado(r, 0, alt)
    furo, fil = furo_roscado(0, alt)
    return (corpo - furo) + fil


def folga_passagem():
    """Ø de furo liso por onde o parafuso passa sem rosquear."""
    return CRISTA_M + 0.7


def confere_encaixe(comp=6.0, passos=72):
    """parafuso x porca coaxiais: menor interferência ao girar o parafuso (0 = encaixa)."""
    porca_ = porca(comp)
    h = haste(comp + 4).translate((0, 0, -2))
    vols = []
    for i in range(passos):
        a = 360.0 * i / passos
        vols.append((h.rotate((0, 0, a)) ^ porca_).volume())
    return min(vols), max(vols)


if __name__ == "__main__":
    rr, rc, rM, rm = raios()
    print(f"macho: raiz Ø{2*rr:.2f} crista Ø{2*rc:.2f} | fêmea: menor Ø{2*rm:.2f} maior Ø{2*rM:.2f} | passo {P}")
    lo, hi = confere_encaixe()
    print(f"interferência parafuso x porca ao girar: mínima {lo:.3f} mm³, máxima {hi:.3f} mm³")
