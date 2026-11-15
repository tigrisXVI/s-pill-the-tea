#!/usr/bin/env python3
"""
Scatoletta Blistra v0.6 - "a due piani" (prova)

Idea: invece di un carosello largo con 28 scomparti, due caroselli piu' piccoli uno sopra l'altro,
sullo stesso albero, ognuno con 14 scomparti + 1 di riposo. Ingombro in pianta quasi dimezzato.

  - i fondi sono CONI a 28 gradi (non piu' rampa + piastra che vibra): le pillole stanno contro la parete
    esterna e, quando si apre lo sportello, scivolano fuori da sole. Il fondo di sopra fa anche da
    coperchio a quello di sotto: i due piani sono annidati come due cappelli cinesi
  - i due caroselli sono sfalsati di mezzo scomparto: a ogni passo arriva davanti una dose di sotto,
    poi una di sopra (lun mattina sotto, lun mezzogiorno sopra, ...)
  - le uscite sono una sopra l'altra, davanti. Due sportelli a ghigliottina, ognuno con il suo micro servo:
    quello di sotto scende per aprire (il suo bordo fa da ponte), quello di sopra sale
  - le pillole del piano di sopra escono su un gradino e cadono sullo stesso scivolo di quelle di sotto
  - la BILANCIA e' sotto il bicchierino: pesa quello che arriva davvero
  - per ricaricare: si apre il cofanetto, si toglie il coperchio a cono e si riempie il piano di sopra;
    per il piano di sotto si sfila tutto il piano di sopra (fondo + carosello), che non ha fili

Misure in mm. Z in alto, il davanti (uscita, bicchierino, display) verso +X.
"""
import math, os
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection
import scatoletta_v5 as v5
from scatoletta_v3 import cil, scatola, cil_x, cil_y, ruota, settore, ccw, prisma_xz, a_mesh

# ---------------------------------------------------------------- misure principali
N = 15                       # scomparti per piano: 14 dosi + 1 di riposo
PASSO = 360.0 / N            # 24 gradi
R_H = 16.0                   # mozzo
R_F = 55.0                   # bordo dei fondi
R_I = R_F + 0.4              # parete, dentro
PARETE = 2.4
R_E = R_I + PARETE           # 57,8 -> diametro 115,6
CONO = 28.0                  # pendenza dei fondi verso la parete
T = math.tan(math.radians(CONO))
SP = 3.4                     # spessore (in verticale) dei coni
LUCE = 12.5                  # spazio in verticale sopra il fondo per le pillole (11 mm perpendicolari)
Z1 = 40.0                    # fondo di sotto, al bordo
D = LUCE + SP                # di quanto e' piu' alto il piano di sopra
Z2 = Z1 + D
ZC = Z2 + LUCE               # sotto del coperchio a cono, al bordo
SFASA = PASSO / 2            # il carosello di sopra e' sfalsato di mezzo scomparto
W = 10.5                     # mezza larghezza delle uscite
GIOCO = 0.4

def zcono(z_bordo, r): return z_bordo + T * (R_F - min(max(r, R_H), R_F))

def cono(z_bordo, sp, r0, r1, piatto=None):
    """Guscio conico tra r0 e r1: sopra a zcono(z_bordo), spessore sp in verticale. 'piatto': centro piatto fino a r0."""
    rr = [r0] + ([R_H] if r0 < R_H < r1 else []) + [r1]                                   # spigolo dove il centro piatto incontra il cono
    pts = [(r, zcono(z_bordo, r) - sp) for r in rr] + [(r, zcono(z_bordo, r)) for r in rr[::-1]]
    m = Manifold.revolve(CrossSection([ccw(pts)]), 192)
    return m

# ---------------------------------------------------------------- base: pavimento, parete alta due piani, uscite
H_PARETE = ZC                # la parete finisce sotto il coperchio, che ci appoggia sopra
Z_VANO = 2.4

def base():
    m = cil(R_E, 0, H_PARETE) - cil(R_I, Z_VANO, H_PARETE + 1)
    # appoggi: un anello per il fondo di sotto e uno per quello di sopra, e lo scalino per il coperchio
    for zb in (Z1, Z2):                                                                     # anelli su cui appoggiano i fondi
        m += cil(R_I + 0.1, zb - SP - 2.0, zb - SP) - cil(R_F - 1.6, zb - SP - 3, zb)
    m -= ruota(scatola(R_I - 1, R_I + 1.3, -3.4, 3.4, Z2 - SP - 0.2, H_PARETE + 1), 180)        # guida del dentino del fondo di sopra
    # uscite davanti (a 0 gradi), una per piano: dal fondo in su per tutta la luce
    for zb in (Z1, Z2):
        m -= scatola(R_I - 2, R_E + 1, -W, W, zb - 0.6, zb + LUCE - 0.3)
    # fori per i fili verso il davanti e per la USB dietro
    for ang in (-40, 40): m -= ruota(scatola(R_I - 1, R_E + 1, -8, 8, 4, 22), ang)
    m -= ruota(scatola(R_I - 1, R_E + 1, -6.5, 6.5, 5, 13), 180)
    return m

# ---------------------------------------------------------------- fondi a cono e coperchio
Z_MOT = zcono(Z1, 22.6) - SP - 0.5          # flangia del motore: sotto il cono, piu' in basso del centro
def fondo_sotto():
    """Fisso, appoggiato sull'anello della base. Il motore 28BYJ-48 e' appeso sotto, su due colonnine."""
    zc = zcono(Z1, R_H)
    m = cono(Z1, SP, 6.0, R_F)
    m -= cil(6.0, zc - SP - 1, zc + 1)                                                      # foro per il codolo del mozzo
    for y in (-17.5, 17.5):                                                                 # colonnine per le alette del motore
        m += cil(3.6, Z_MOT, zcono(Z1, math.hypot(8, y)) - SP + 0.5, -8, y)
        m -= cil(1.4, Z_MOT - 1, Z_MOT + 8, -8, y)                                            # viti M3 autofilettanti
    return m

def fondo_sopra():
    """Si sfila con il suo carosello per ricaricare il piano di sotto. Fa da coperchio al piano di sotto."""
    m = cono(Z2, SP, R_H + GIOCO, R_F)
    m += ruota(scatola(R_F - 0.01, R_I + 1.0, -3.0, 3.0, Z2 - SP, Z2 - 0.5), 180)              # dentino: non gira con il carosello
    return m

def coperchio():
    """Coperchio a cono del piano di sopra: si toglie per ricaricare."""
    m = cono(ZC + SP, SP, 8.0, R_F)                                                         # al centro passa il pomello del carosello
    m += cil(R_E, ZC, ZC + SP) - cil(R_F - 0.01, ZC - 1, ZC + SP + 1)                          # bordo che appoggia sulla parete
    for a in (90, 270): m += ruota(scatola(R_F + 0.2, R_E - 0.3, -6, 6, ZC + SP - 0.01, ZC + SP + 3.0), a)   # due prese per toglierlo
    return m

# ---------------------------------------------------------------- caroselli: mozzo + 15 palette
# Il mozzo di sotto finisce poco sotto il fondo di sopra. Quello di sopra passa nel foro del fondo di sopra e sotto
# ha un collarino: tirando il pomello in alto si sfilano insieme carosello e fondo di sopra.
SP_PAL = 1.6
R_COLL = 19.5                            # collarino del mozzo di sopra
H1T = zcono(Z2, R_COLL) - SP - 2.6       # cima del mozzo di sotto
Z_COLL1 = zcono(Z2, R_COLL) - SP - 0.3

def paletta(prof, a):
    return ruota(prisma_xz(prof, -SP_PAL / 2, SP_PAL / 2), a)

def carosello_sotto():
    zc0 = zcono(Z1, R_H)
    m = cil(R_H, zc0 + GIOCO, H1T) + cil(5.5, Z_MOT + 1.6, zc0 + 1)                          # mozzo e codolo che scende nel foro
    rs = R_F - 1.6 - GIOCO
    for j in range(N):
        prof = [(R_H - 0.5, zcono(Z1, R_H) + GIOCO), (R_F - GIOCO, zcono(Z1, R_F) + GIOCO),
                (R_F - GIOCO, Z2 - SP - 2.0 - GIOCO), (rs - 0.4, Z2 - SP - 2.0 - GIOCO), (rs - 0.4, zcono(Z2, rs) - SP - GIOCO),
                (R_COLL + GIOCO, zcono(Z2, R_COLL + GIOCO) - SP - GIOCO), (R_COLL + GIOCO, H1T - GIOCO), (R_H - 0.5, H1T - GIOCO)]
        m += paletta(prof, PASSO / 2 + j * PASSO)
    m -= cil(2.65, Z_MOT + 1.5, Z_MOT + 10.5) ^ scatola(-1.6, 1.6, -4, 4, Z_MOT, Z_MOT + 11)   # albero del motore (a D)
    m -= scatola(-3.1, 3.1, -3.1, 3.1, H1T - 6, H1T + 1)                                      # presa quadra per il mozzo di sopra
    return m

def carosello_sopra():
    z0 = zcono(Z2, R_H)
    ztop = zcono(ZC + SP, R_H) - SP - GIOCO
    m = cil(R_H, H1T + 0.1, ztop) + cil(R_COLL, H1T + 0.1, Z_COLL1)                           # mozzo con collarino sotto il fondo
    m += scatola(-3.0, 3.0, -3.0, 3.0, H1T - 5.5, H1T + 0.11)                                 # perno quadro nel mozzo di sotto
    m += cil(7.4, ztop - 0.01, H_G - 2.0)                                                     # pomello: passa nel foro del coperchio
    for j in range(N):
        prof = [(R_H - 0.5, z0 + GIOCO), (R_F - GIOCO, zcono(Z2, R_F) + GIOCO), (R_F - GIOCO, zcono(ZC + SP, R_F) - SP - GIOCO),
                (R_H - 0.5, ztop)]
        m += paletta(prof, PASSO / 2 + j * PASSO + SFASA)
    return m

# ---------------------------------------------------------------- uscita: scivolo, gradino, guide e sportelli
X_SC0 = R_E + 2.0            # lo scivolo parte dopo le guide degli sportelli
SC_ANG = 40.0
X_SC1 = 70.0
def z_sc(x): return Z1 - 0.6 - (x - X_SC0) * math.tan(math.radians(SC_ANG))
SPORT = dict(sp=1.6, x0=R_E + 0.15, larg=W + 2.5)             # sportelli: lastre sottili davanti alla parete
CORSA = LUCE + 1.0

def scivolo():
    """Un pezzo solo davanti alla parete: guide degli sportelli, ponte, scivolo, gradino del piano di sopra."""
    s = SPORT; x0, x1 = s["x0"] - 0.15, s["x0"] + s["sp"] + 0.25
    wl = W + 3.0
    # scivolo con sponde
    pav = prisma_xz([(x0, Z1 - 0.6), (X_SC1, z_sc(X_SC1)), (X_SC1, z_sc(X_SC1) - 2.4), (x0, Z1 - 3.0)], -wl, wl)
    sponde = prisma_xz([(x0, Z1 + 6), (X_SC1, z_sc(X_SC1) + 6), (X_SC1, z_sc(X_SC1) - 2.4), (x0, Z1 - 3.0)], -wl, wl) - prisma_xz(
        [(x0 - 1, Z1 + 7), (X_SC1 + 1, z_sc(X_SC1) + 7), (X_SC1 + 1, z_sc(X_SC1) - 0.6 - 0.01), (x0 - 1, Z1 - 0.6 - 0.01)], -W, W)
    m = pav + sponde
    m -= scatola(x0, x1, -s["larg"] - 0.3, s["larg"] + 0.3, Z1 - 0.6 - CORSA - 1, Z1 + 8)    # passaggio dello sportello di sotto
    # gradino del piano di sopra: esce oltre le guide, poi le pillole cadono sullo scivolo
    xg = NIC["x0"] - 0.3
    m += scatola(R_E, xg, -W, W, Z2 - 3.0, Z2 - 0.65)
    m += (scatola(x1, xg, W, W + 2.0, Z2 - 3.0, Z2 + 4) + scatola(x1, xg, -W - 2.0, -W, Z2 - 3.0, Z2 + 4))
    # guide verticali ai lati degli sportelli
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * (s["larg"] + 0.3), sgn * (s["larg"] + 2.6)))
        m += scatola(R_E, x1 + 1.6, y0, y1, Z1 - CORSA - 3, Z2 + LUCE + CORSA + 1)
        y0b, y1b = sorted((sgn * (s["larg"] - 1.2), sgn * (s["larg"] + 2.6)))
        m += scatola(x1, x1 + 1.6, y0b, y1b, Z1 - CORSA - 3, Z2 + LUCE + CORSA + 1)
    return m

def sportello(piano, aperto=0.0):
    """Lastra a ghigliottina: quello di sotto scende per aprire, quello di sopra sale."""
    s = SPORT
    if piano == 0: z0, z1, dz = Z1 - 0.6, Z1 + LUCE + 0.1, -CORSA * aperto
    else: z0, z1, dz = Z2 - 0.6, Z2 + LUCE + 0.5, CORSA * aperto
    m = scatola(s["x0"], s["x0"] + s["sp"], -s["larg"], s["larg"], z0, z1)
    return m.translate([0, 0, dz])

def ingombro_servi():
    """I due micro servi MG90S (22,8 x 12,6 x 22,5), coricati davanti alla parete, sopra e sotto le uscite."""
    a = scatola(R_E + 2.5, R_E + 2.5 + 12.6, -NIC["y"] - 2.6 - 22.8, -NIC["y"] - 2.6, Z1 - 12, Z1 + 10.5)   # piano di sotto, di lato alla nicchia
    b = scatola(R_E + 6.0, R_E + 6.0 + 12.6, W + 3, W + 3 + 22.8, Z2 + LUCE + 2, Z2 + LUCE + 24.5)   # piano di sopra, a destra
    return a + b

# ---------------------------------------------------------------- guscio, cofanetto, bicchierino sulla bilancia
R_G = R_E + 1.2 + 2.4
XF = 122.0; RC = 22.0
H_G = zcono(ZC + SP, R_H) + 5.0 + 0.6
NIC = dict(x0=62.0, y=31.0, z=52.0)
Z_CUP = 14.0                 # il bicchierino appoggia sul piatto della bilancia
CUP5 = dict(x0=64.8, x1=116.8, y=29.0, r=8.0, z0=2.6, alt=34.0, parete=2.6, basso=16.5, becco=23.5, labbro=2.5, fondo_dietro=4.6, fondo_davanti=6.2)
ALZA_CUP = Z_CUP - CUP5["z0"]  # lo stesso bicchierino della v0.5, piu' in alto
CUP = {k: (v + ALZA_CUP if k in ("z0", "alt", "basso", "fondo_dietro", "fondo_davanti") else v) for k, v in CUP5.items()}
BILANCIA = dict(x=90.0, z0=2.4)
DISPLAY = dict(y=-24.0, z=72.0); TASTO = dict(y=26.0, z=72.0, r=15.1)

def guscio():
    pg = PARETE
    m = v5.pianta(R_G, XF, RC, 0, H_G) - v5.pianta(R_G - pg, XF - pg, RC - pg, -1, H_G + 1)
    n = NIC
    m -= scatola(n["x0"] + pg, 300, -n["y"], n["y"], -1, n["z"])
    riv = (scatola(n["x0"], XF, -n["y"] - pg, n["y"] + pg, 0, n["z"] + pg) ^ v5.pianta(R_G, XF, RC, 0, H_G)) - scatola(n["x0"] + pg, 301, -n["y"], n["y"], 0, n["z"])
    riv -= scatola(n["x0"] - 1, n["x0"] + pg + 1, -W - 3.5, W + 3.5, z_sc(X_SC1) - 3, Z1 + 8)   # finestra per lo scivolo
    m += riv
    # davanti: display e tasto sopra la nicchia
    m -= cil_x(TASTO["r"], XF - 5, XF + 1, TASTO["y"], TASTO["z"])
    m -= scatola(XF - 5, XF + 1, DISPLAY["y"] - 15, DISPLAY["y"] + 15, DISPLAY["z"] - 8, DISPLAY["z"] + 8)
    m -= scatola(XF - 5, XF - 0.6, -27, 27, H_G - 9, H_G - 3)                                  # luce sotto la pelle
    m -= ruota(scatola(R_G - 4, R_G + 1, -7.0, 7.0, 4.0, 14.0), 180)                          # USB dietro
    for ang in (110, 125):
        for k in range(4): m -= ruota(scatola(R_G - 4, R_G + 1, -0.8, 0.8, 8 + 3 * k, 9.6 + 3 * k), ang)
    return m

CERN_C = dict(x=-(R_G + 1.0), z=H_G + 3.3, r=3.2, perno=1.05)
def cofanetto():
    old = (v5.CERN_C, v5.R_G, v5.XF, v5.RC, v5.H_G, v5.PARETE_G)
    v5.CERN_C, v5.R_G, v5.XF, v5.RC, v5.H_G = CERN_C, R_G, XF, RC, H_G
    try:
        c = CERN_C
        m = v5.pianta(R_G, XF, RC, H_G, H_G + v5.SP_C)
        rr = R_G - PARETE
        m += (v5.pianta(rr - 0.4, XF - PARETE - 0.4, RC - PARETE - 0.4, H_G - 3.4, H_G + 0.1) - v5.pianta(rr - 2.0, XF - PARETE - 2.0, RC - PARETE - 2.0, H_G - 4, H_G + 1))
        m += cil_y(c["r"], -10.0, 10.0, c["x"], c["z"]) + scatola(c["x"], c["x"] + 10, -10.0, 10.0, H_G, H_G + v5.SP_C)
        for s in (1, -1):
            y0, y1 = sorted((s * 10.2, s * 22.4)); m -= scatola(c["x"] - 10, c["x"] + 6, y0, y1, H_G - 5, H_G + v5.SP_C + 5)
        m -= cil_y(c["perno"], -11, 11, c["x"], c["z"])
        m -= scatola(XF - 6, XF + 1, -12, 12, H_G - 1, H_G + 1.4)                                # tacca per il dito
    finally:
        v5.CERN_C, v5.R_G, v5.XF, v5.RC, v5.H_G, v5.PARETE_G = old
    return m
def cerniere_guscio():
    c = CERN_C; m = Manifold()
    for s in (1, -1):
        y0, y1 = sorted((s * 10.6, s * 22.0))
        m += cil_y(c["r"], y0, y1, c["x"], c["z"]) + (scatola(c["x"] - 2, c["x"] + 5, y0, y1, H_G - 8, c["z"]) - cil(R_G - PARETE, H_G - 9, H_G + 9) - scatola(c["x"] + 3, c["x"] + 9, y0 - 1, y1 + 1, H_G - 0.01, H_G + 9))
        m -= cil_y(c["perno"], y0 - 1, y1 + 1, c["x"], c["z"])
    return m
def cofanetto_aperto(g):
    c = CERN_C; return cofanetto().translate([-c["x"], 0, -c["z"]]).rotate([0, -g, 0]).translate([c["x"], 0, c["z"]])

def bicchierino():
    old = v5.BICCHIERE; v5.BICCHIERE = CUP5
    try: m = v5.bicchierino()
    finally: v5.BICCHIERE = old
    return m.translate([0, 0, ALZA_CUP])

def piatto_bilancia():
    """Piatto su cui appoggia il bicchierino; sta sull'estremo libero della cella di carico."""
    m = v5.rett_arrotondato(CUP["x0"] + 4, CUP["x1"] - 4, -CUP["y"] + 4, CUP["y"] - 4, 5, CUP["z0"] - 2.4, CUP["z0"] - 0.1)
    m += scatola(BILANCIA["x"] + 8, BILANCIA["x"] + 22, -6, 6, CUP["z0"] - 4.2, CUP["z0"] - 2.3)   # piede sulla cella
    return m

def ingombro_cella():
    b = BILANCIA; return scatola(b["x"] - 25, b["x"] + 22, -6, 6, CUP["z0"] - 10.2, CUP["z0"] - 4.2)
def appoggio_cella():
    b = BILANCIA; return scatola(b["x"] - 25, b["x"] - 9, -7, 7, 0.0, CUP["z0"] - 10.2)

def ingombro_motore():
    zc = Z_MOT
    return cil(14.2, zc - 19.5, zc, -8, 0) + cil(2.5, zc, zc + 9) + scatola(-25.3, -18, -7.3, 7.3, zc - 17, zc - 0.8) + scatola(-11.5, -4.5, -17.5, 17.5, zc - 0.8, zc)

def ingombro_display():
    return scatola(XF - PARETE - 4.2, XF - PARETE - 0.2, DISPLAY["y"] - 17.7, DISPLAY["y"] + 17.7, DISPLAY["z"] - 16.8, DISPLAY["z"] + 16.8)
def ingombro_tasto():
    t = TASTO
    return cil_x(14.0, XF - 22, XF, t["y"], t["z"]) + cil_x(16.5, XF - PARETE - 6, XF - PARETE - 0.2, t["y"], t["z"]) + cil_x(18.0, XF, XF + 1.6, t["y"], t["z"]) + cil_x(14.6, XF + 1.6, XF + 4, t["y"], t["z"])
def ingombro_schede():
    """ESP32-S3 SuperMini, DRV8833, HX711 nel vano sotto il cono (appoggiate sul pavimento)."""
    return scatola(-52, -29.5, -9, 9, 5.9, 11) + scatola(-20, -1.5, 20, 36, 5.9, 12) + scatola(10, 44, 18, 39, 5.9, 9.5)

PEZZI = {"1_base": base, "2_fondo_sotto": fondo_sotto, "3_carosello_sotto": carosello_sotto, "4_fondo_sopra": fondo_sopra,
         "5_carosello_sopra": carosello_sopra, "6_coperchio": coperchio, "7_scivolo": scivolo,
         "8_sportello_sotto": lambda: sportello(0), "9_sportello_sopra": lambda: sportello(1),
         "10_guscio": lambda: guscio() + cerniere_guscio(), "11_cofanetto": cofanetto, "12_bicchierino": bicchierino,
         "13_piatto_bilancia": piatto_bilancia, "14_appoggio_cella": appoggio_cella}
COMPONENTI = {"motore": ingombro_motore, "servi": ingombro_servi, "cella": ingombro_cella, "display": ingombro_display,
              "tasto": ingombro_tasto, "schede": ingombro_schede}

def genera(cartella):
    for d in ("stampa", "assieme", "componenti"):
        dd = os.path.join(cartella, d); os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd): os.remove(os.path.join(dd, f))
    solidi = {n: f() for n, f in PEZZI.items()}
    for n, m in solidi.items():
        mesh = a_mesh(m); mesh.export(os.path.join(cartella, "assieme", n + ".stl"))
        st = mesh.copy()
        if n == "11_cofanetto": st.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        if n in ("2_fondo_sotto", "4_fondo_sopra", "6_coperchio"): st.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        b = st.bounds; st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
        st.export(os.path.join(cartella, "stampa", n + ".stl"))
    for n, f in COMPONENTI.items(): a_mesh(f()).export(os.path.join(cartella, "componenti", n + ".stl"))
    return solidi

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    solidi = genera(os.path.join(qui, "..", "v6", "stl"))
    for n, m in solidi.items():
        mesh = a_mesh(m); d = mesh.bounds[1] - mesh.bounds[0]
        print(f"{n:22s} {d[0]:6.1f} x {d[1]:6.1f} x {d[2]:5.1f} mm  {m.volume() / 1000:6.1f} cm3  pezzi: {len(m.decompose())}")
    tutto = a_mesh(solidi["10_guscio"] + solidi["11_cofanetto"] + ingombro_tasto() + solidi["12_bicchierino"])
    d = tutto.bounds[1] - tutto.bounds[0]
    print(f"Ingombro totale: {d[0]:.0f} x {d[1]:.0f} x {d[2]:.0f} mm")
