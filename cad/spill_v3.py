#!/usr/bin/env python3
"""
S-pill the tea v0.3 - modello 3D parametrico (prototipo)

Cosa cambia rispetto alla v0.2:
  - 29 scomparti: 4 dosi al giorno x 7 giorni + 1 di riposo; pillola piu' grande prevista: Augmentin 875 (22 mm)
  - fondo fino a 80 mm di raggio, mozzo da 20 mm, niente anello esterno (le palette arrivano a filo della parete)
  - ripiano largo uno scomparto, con una piastra pesata (cella di carico) che VIBRA (motorino a moneta)
  - uscita: varco nella parete chiuso dalla gonna dello sportello, scivolo a 40 gradi che si allarga,
    vaschetta lunga 40 mm inclinata di 15 gradi verso un bordino
  - lo sportello e' incernierato verso il centro: aprendolo, la gonna si alza e libera il varco

    pip install manifold3d trimesh numpy
    python3 spill_v3.py

Misure in millimetri. Z verso l'alto, lo sportello e lo scivolo sono sul lato +X.
"""
import math, os
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection, Mesh

# ---------------------------------------------------------------- parametri
N = 29                    # palette: 28 scomparti di dosi + 1 di riposo
PASSO = 360.0 / N         # 12,41 gradi
R_FONDO = 80.0            # raggio del fondo fisso
PARETE = 2.4
R_INT = R_FONDO + 0.4     # interno della parete: le palette arrivano a 0,7 mm
R_EST = R_INT + PARETE    # 82,8 -> diametro 165,6
R_MOZZO = 20.0
ALZATA = 10.0
PENDENZA = 8.0
RIPIANO = PASSO / 2 + 0.8         # mezzo angolo del ripiano piatto (uno scomparto)
PIASTRA = PASSO / 2 - 0.7         # mezzo angolo della piastra pesata: le palette restano sul fondo fisso
VARCO = PASSO / 2 - 0.4           # mezzo angolo del varco nella parete
SALITA, DISCESA = 96.0, 48.0
ARIA_SOPRA = 8.0
VANO = 22.0
SP_PALETTA = 1.2
SCIVOLO_GRADI, L_SCIVOLO, SVASO = 40.0, 26.0, 10.0
L_VASCA, PEND_VASCA, BORDINO_V = 40.0, 15.0, 7.0
SEG = int(__import__("os").environ.get("BLISTRA_SEG", "192"))   # 192 per le STL; meno per i file STEP

# ---------------------------------------------------------------- quote derivate
TAN = math.tan(math.radians(PENDENZA))
Z_APPOGGIO = 2.4 + VANO                   # 24,4
SP_FONDO = 3.0
Z_BASSO = Z_APPOGGIO + SP_FONDO           # 27,4: fondo al bordo, zona bassa
Z_RIPIANO = Z_BASSO + ALZATA              # 37,4
R_DISCO = R_MOZZO + 0.6
Z_DISCO = Z_BASSO + TAN * (R_FONDO - R_DISCO)
Z_SOTTO_COP = Z_RIPIANO + TAN * (R_FONDO - R_DISCO) + ARIA_SOPRA
SP_COP = 2.4
Z_TOP = Z_SOTTO_COP + SP_COP
R_COP = R_EST - 1.2 - 0.2
# scivolo (coordinate lungo +X)
X0_SC, Z0_SC = R_FONDO + 0.2, Z_RIPIANO - 0.6
X1_SC = X0_SC + L_SCIVOLO * math.cos(math.radians(SCIVOLO_GRADI)); Z1_SC = Z0_SC - L_SCIVOLO * math.sin(math.radians(SCIVOLO_GRADI))
X2_SC = X1_SC + L_VASCA; Z2_SC = Z1_SC - L_VASCA * math.tan(math.radians(PEND_VASCA))
W_SC = R_FONDO * math.sin(math.radians(VARCO))
def z_scivolo(x):
    if x <= X0_SC: return Z0_SC
    if x <= X1_SC: return Z0_SC - (x - X0_SC) * math.tan(math.radians(SCIVOLO_GRADI))
    return Z1_SC - (x - X1_SC) * math.tan(math.radians(PEND_VASCA))
def y_sponda(x): return W_SC + SVASO * min(1.0, max(0.0, (x - X0_SC) / (X1_SC - X0_SC)))

def quota_giro(theta):
    t = (theta + 180.0) % 360.0 - 180.0
    morbido = lambda x: 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, x)))
    if -RIPIANO <= t <= RIPIANO: return ALZATA
    if -RIPIANO - SALITA < t < -RIPIANO: return ALZATA * morbido((t + RIPIANO + SALITA) / SALITA)
    if RIPIANO < t < RIPIANO + DISCESA: return ALZATA * morbido((RIPIANO + DISCESA - t) / DISCESA)
    return 0.0

def z_fondo(theta, r):
    return Z_BASSO + quota_giro(theta) + TAN * (R_FONDO - r)

# ---------------------------------------------------------------- mattoncini
def cil(r, z0, z1, x=0.0, y=0.0, seg=SEG):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate([x, y, z0])
def scatola(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
def cil_x(r, x0, x1, y, z):
    return Manifold.cylinder(x1 - x0, r, r, 48).rotate([0, 90, 0]).translate([x0, y, z])
def cil_y(r, y0, y1, x, z):
    return Manifold.cylinder(y1 - y0, r, r, 48).rotate([-90, 0, 0]).translate([x, y0, z])
def ruota(m, gradi): return m.rotate([0, 0, gradi])
def settore(r1, r2, mezzo, z0, z1, rientro=0.0, passi=48):
    a = math.radians(mezzo)
    def arco(r, verso):
        lim = a - math.asin(max(-1.0, min(1.0, rientro / r)))
        return [(r * math.cos(t * verso), r * math.sin(t * verso)) for t in np.linspace(-lim, lim, passi)]
    return Manifold.extrude(CrossSection([arco(r2, 1) + arco(r1, -1)]), z1 - z0).translate([0, 0, z0])
def ccw(pts):
    """CrossSection tiene solo i poligoni in senso antiorario: li giro se serve."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if area > 0 else pts[::-1]
def prisma_xz(punti, y0, y1):
    """Prisma convesso: sezione nel piano XZ, esteso tra y0 e y1."""
    return Manifold.extrude(CrossSection([ccw([(x, z) for x, z in punti])]), y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])
def solido_rampa(r_int, r_est, z0, passi=1440, dz=0.0):
    v, t = [], []
    for i in range(passi):
        th = 360.0 * i / passi; c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
        v += [(r_int * c, r_int * s, z_fondo(th, r_int) + dz), (r_est * c, r_est * s, z_fondo(th, r_est) + dz), (r_est * c, r_est * s, z0), (r_int * c, r_int * s, z0)]
    for i in range(passi):
        a, b = 4 * i, 4 * ((i + 1) % passi)
        for k in range(4):
            p, q, r, s_ = a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k
            t += [(p, r, q), (p, s_, r)]
    m = Manifold(Mesh(np.array(v, dtype=np.float32), np.array(t, dtype=np.uint32)))
    if m.volume() < 0:
        m = Manifold(Mesh(np.array(v, dtype=np.float32), np.array([(a, c, b) for a, b, c in t], dtype=np.uint32)))
    return m
def guscio_sotto(dz_alto, dz_basso, r0=None, r1=None):
    """Lo strato compreso tra (superficie + dz_basso) e (superficie + dz_alto)."""
    r0 = R_DISCO - 1 if r0 is None else r0; r1 = R_FONDO + 1 if r1 is None else r1
    return solido_rampa(r0, r1, 0.0, dz=dz_alto) - solido_rampa(r0, r1, -1.0, dz=dz_basso)

# ---------------------------------------------------------------- 1. base
ANGOLI_VITI = (110, 160, 200, 250)
R_VITI = 66.0
HALL_SP = dict(ang=12.0, r=R_EST + 1.6)                    # sensore dello sportello: torretta esterna accanto al varco
X_FLANGIA = R_EST                                          # lo scivolo si avvita sulla parete davanti
Z_VITI_SC = (8.0, 18.0); Y_VITI_SC = 20.0

def base():
    m = cil(R_EST, 0, Z_TOP) - cil(R_INT, 2.4, Z_TOP + 1)
    m -= cil(R_COP + 0.2, Z_SOTTO_COP, Z_TOP + 1)                                           # sede del coperchio
    for ang in ANGOLI_VITI:                                                                 # colonnine per il fondo, attaccate alla parete
        col = cil(4.5, 2.4, Z_APPOGGIO, R_VITI, 0) + scatola(R_VITI, R_INT + 0.5, -3, 3, 2.4, Z_APPOGGIO)
        col -= cil(1.4, Z_APPOGGIO - 14, Z_APPOGGIO + 1, R_VITI, 0)
        m += ruota(col, ang)
    # varco davanti: dalla superficie dello scivolo in su (lo scivolo e' un pezzo a parte)
    taglio = settore(R_INT - 1, R_EST + 3, VARCO, z_scivolo(R_EST + 3) - 3.6, Z_TOP + 1)
    m -= taglio
    # torretta del sensore di Hall dello sportello (fuori, accanto al varco), con foro per i fili
    a, r = HALL_SP["ang"], HALL_SP["r"]
    tor = ruota(scatola(R_EST - 1, R_EST + 3.2, -3.2, 3.2, Z_SOTTO_COP - 18, Z_TOP), a) - ruota(scatola(R_EST - 0.2, R_EST + 2.0, -2.2, 2.2, Z_TOP - 5.0, Z_TOP + 1), a)
    tor -= ruota(cil_x(1.0, R_INT - 1, R_EST + 2.0, 0, Z_TOP - 4.0), a)
    m += tor
    # boccole per le viti dello scivolo (M3 autofilettanti da dentro)
    for y in (-Y_VITI_SC, Y_VITI_SC):
        for z in Z_VITI_SC:
            x = math.sqrt(R_INT ** 2 - y ** 2)
            m += cil_x(3.5, x - 5, x + 0.5, y, z) - cil_x(1.3, x - 6, R_EST + 1, y, z)
            m -= cil_x(1.6, x - 1, R_EST + 1, y, z)
    m -= ruota(scatola(R_COP - 1.0, R_EST + 1, -2.3, 2.3, Z_SOTTO_COP, Z_TOP + 1), 150)    # tacca antirotazione del coperchio
    m -= ruota(scatola(R_INT - 1, R_EST + 1, -6.5, 6.5, 5, 13), 180)                        # cavo USB (dietro)
    m -= ruota(cil_x(2.55, R_INT - 1, R_EST + 1, 0, 14), 45)                                # LED
    m -= ruota(cil_x(3.6, R_INT - 1, R_EST + 1, 0, 14), -45)                                # pulsante
    for ang in (90, 270):                                                                    # griglia: il cicalino si sente
        for k in range(4): m -= ruota(scatola(R_INT - 1, R_EST + 1, -0.8, 0.8, 6 + 3 * k, 7.6 + 3 * k), ang)
    return m

# ---------------------------------------------------------------- 2. fondo a rampa
CELLA = dict(lung=47.0, larg=12.0, alt=6.0, r0=22.0)        # cella di carico a barretta 100 g (circa 47 x 12 x 6)
FORI_CELLA_FISSO = (26.0, 34.0); FORI_CELLA_LIBERO = (60.0, 66.0)
VIBRO = dict(r=74.0, rad=4.0, alt=2.0)                       # motorino vibrante a moneta 8 x 2 mm (tipo 0820)
MOTORE_X = -8.0
HALL_ZERO = (10.0, 0.0)

def fondo_rampa():
    m = solido_rampa(R_DISCO - 0.01, R_FONDO, Z_APPOGGIO) + cil(R_DISCO, Z_APPOGGIO, Z_DISCO)
    z_fl = Z_DISCO - 2.4                                                                     # motore 28BYJ-48 da sotto
    m -= cil(14.4, Z_APPOGGIO - 1, z_fl, MOTORE_X, 0) + scatola(MOTORE_X - 3.7, MOTORE_X + 3.7, -21.6, 21.6, Z_APPOGGIO - 1, z_fl)
    m -= scatola(MOTORE_X - 26, MOTORE_X - 8, -8.5, 8.5, Z_APPOGGIO - 1, z_fl)
    m -= cil(4.8, Z_APPOGGIO, Z_DISCO + 1)
    for s in (1, -1):
        x, y = MOTORE_X, s * 17.5
        zt = z_fondo(math.degrees(math.atan2(y, x)), max(math.hypot(x, y), R_DISCO))
        m -= cil(1.7, Z_APPOGGIO, zt + 1, x, y) + cil(3.3, z_fl + 2.0, zt + 1, x, y)
    for ang in ANGOLI_VITI:
        m -= ruota(cil(1.7, Z_APPOGGIO - 1, Z_TOP, R_VITI, 0) + cil(3.3, Z_APPOGGIO + 1.6, Z_TOP, R_VITI, 0), ang)
    # sensore di Hall "posizione zero" sotto il mozzo, e foro per i fili
    hx, hy = HALL_ZERO
    m -= scatola(hx - 2.2, hx + 2.2, hy - 1.7, hy + 1.7, Z_DISCO - 1.6, Z_DISCO + 1) + cil(1.4, Z_APPOGGIO - 1, Z_DISCO, hx, hy)
    # sede della piastra (fino al bordo), vano della cella, tasca del motorino vibrante
    m -= settore(R_DISCO + 2.0, R_FONDO + 1, PIASTRA + 0.3, 0, Z_TOP) ^ guscio_sotto(0.05, -2.6)
    c = CELLA
    m -= scatola(c["r0"] - 1, c["r0"] + c["lung"] + 2, -c["larg"] / 2 - 1, c["larg"] / 2 + 1, Z_APPOGGIO + 1.6, Z_TOP) ^ solido_rampa(R_DISCO - 1, R_FONDO + 1, 0, dz=-2.5)
    m += scatola(c["r0"] - 1, c["r0"] + 15, -c["larg"] / 2 - 1, c["larg"] / 2 + 1, Z_APPOGGIO + 1.5, Z_APPOGGIO + 3.1)   # rialzo sotto l'estremo fisso (verso il mozzo)
    for x in FORI_CELLA_FISSO:
        m -= cil(1.7, Z_APPOGGIO - 1, Z_APPOGGIO + 4, x, 0) + cil(3.2, Z_APPOGGIO - 1, Z_APPOGGIO + 0.2, x, 0)
    m -= cil(VIBRO["rad"] + 0.8, 0, Z_TOP, VIBRO["r"], 0) ^ guscio_sotto(0.05, -2.6 - VIBRO["alt"] - 0.8)
    m -= scatola(c["r0"] + c["lung"] - 3, VIBRO["r"], -1.2, 1.2, 0, Z_TOP) ^ guscio_sotto(0.05, -2.6 - 2.0)   # canalina dei fili del motorino
    m -= scatola(c["r0"] + 16, c["r0"] + 22, -3, 3, Z_APPOGGIO - 1, Z_APPOGGIO + 3)                     # fili della cella verso il vano
    return m

def piastra():
    """Piastra pesata e vibrante, a filo del fondo. Si avvita all'estremo libero della cella."""
    m = settore(R_DISCO + 2.6, R_FONDO - 0.3, PIASTRA + 0.3, 0, Z_TOP, rientro=0.45) ^ guscio_sotto(0.0, -2.0)   # 0,45 mm di gioco ai lati
    c = CELLA
    piede = scatola(FORI_CELLA_LIBERO[0] - 4, FORI_CELLA_LIBERO[1] + 3, -4.5, 4.5, Z_APPOGGIO + 1.6 + 1.5 + c["alt"], Z_TOP) ^ solido_rampa(R_DISCO - 1, R_FONDO + 1, 0, dz=-1.0)
    m += piede
    for x in FORI_CELLA_LIBERO:
        m -= cil(1.7, Z_APPOGGIO, Z_TOP, x, 0) + (cil(3.1, 0, Z_TOP, x, 0) ^ solido_rampa(R_DISCO - 1, R_FONDO + 1, 0, dz=0.1) - solido_rampa(R_DISCO - 1, R_FONDO + 1, 0, dz=-1.6))
    return m

def tappi_piastra():
    """Due tappini che chiudono le svasature delle viti: la superficie resta liscia per le pillole."""
    t = []
    for x in FORI_CELLA_LIBERO:
        t.append(cil(3.0, 0, Z_TOP, x, 0) ^ guscio_sotto(0.0, -1.5))
    return t[0] + t[1]

# ---------------------------------------------------------------- 3. carosello: mozzo e palette
Z_MOZZO0, Z_MOZZO1 = Z_DISCO + 0.4, Z_SOTTO_COP - 0.5
R_PAL0 = 15.0
H_PAL = (Z_SOTTO_COP - 0.6) - (Z_RIPIANO + 0.2)             # altezza al bordo: sul ripiano arriva a 0,6 mm dal coperchio
ANG_PAL = [PASSO / 2 + j * PASSO for j in range(N)]         # a riposo lo scomparto 0 e' sul ripiano

def mozzo():
    m = cil(R_MOZZO, Z_MOZZO0, Z_MOZZO1)
    for a in ANG_PAL:
        m -= ruota(scatola(R_PAL0 - 0.5, R_MOZZO + 1, -(SP_PALETTA / 2 + 0.2), SP_PALETTA / 2 + 0.2, Z_MOZZO0 - 1, Z_MOZZO1 + 1), a)
    zs = Z_MOZZO0
    m -= cil(2.65, zs - 1, zs + 7.4) ^ scatola(-1.6, 1.6, -4, 4, zs - 1, zs + 7.4)
    m -= cil(2.65, zs - 1, zs + 1.6)
    m -= cil(2.1, zs - 1, zs + 2.2, HALL_ZERO[0], HALL_ZERO[1])                              # magnete 4x2 della posizione zero
    return m

def paletta():
    zb = lambda r: TAN * (R_FONDO - min(max(r, R_DISCO), R_FONDO)) + 0.2
    profilo = [(R_PAL0, zb(R_PAL0)), (R_DISCO, zb(R_DISCO)), (R_FONDO - 0.3, zb(R_FONDO)), (R_FONDO - 0.3, H_PAL), (R_PAL0, H_PAL)]
    return Manifold.extrude(CrossSection([ccw(profilo)]), SP_PALETTA).rotate([90, 0, 0]).translate([0, SP_PALETTA / 2, Z_BASSO])

def paletta_a(theta_carosello, j):
    a = ANG_PAL[j] + theta_carosello
    d = math.degrees(math.asin(SP_PALETTA / 2 / R_DISCO))
    su = max(quota_giro(a - d), quota_giro(a), quota_giro(a + d))
    return ruota(paletta(), a).translate([0, 0, su])

# ---------------------------------------------------------------- 4. coperchio e 5. sportello
X_APRE = 34.0                                  # l'apertura nel coperchio parte da qui
CERN = dict(x=30.5, z=Z_TOP + 2.9, r=2.6, perno=1.0)
Y_SP = 12.0                                    # mezza larghezza del tetto dello sportello

def coperchio():
    m = cil(R_COP, Z_SOTTO_COP, Z_TOP)
    m += ruota(scatola(R_COP - 0.5, R_EST - 0.2, -2.0, 2.0, Z_SOTTO_COP, Z_TOP), 150)
    m -= settore(R_MOZZO, R_EST + 2, VARCO, Z_SOTTO_COP - 1, Z_TOP + 1) - cil(X_APRE, Z_SOTTO_COP - 2, Z_TOP + 2)
    for ya, yb in ((-Y_SP, -6.2), (6.2, Y_SP)):                                             # cerniera: due occhielli sul coperchio
        occ = cil_y(CERN["r"], ya, yb, CERN["x"], CERN["z"]) + scatola(CERN["x"] - CERN["r"], CERN["x"] + CERN["r"], ya, yb, Z_TOP - 0.1, CERN["z"])
        m += occ - cil_y(CERN["perno"] - 0.05, ya - 1, yb + 1, CERN["x"], CERN["z"])
    return m

def sportello():
    z0, z1 = Z_TOP + 0.2, Z_TOP + 2.2
    m = scatola(CERN["x"] + 3.2, R_EST + 1.0, -Y_SP, Y_SP, z0, z1)                         # tetto
    m += cil_y(CERN["r"], -6.0, 6.0, CERN["x"], CERN["z"]) + scatola(CERN["x"], CERN["x"] + 3.4, -6.0, 6.0, z0, CERN["z"])
    m -= cil_y(CERN["perno"] + 0.15, -7, 7, CERN["x"], CERN["z"])
    # gonna: riempie il varco nella parete, a filo, fino allo scivolo
    gonna = settore(R_INT + 0.1, R_EST - 0.1, VARCO, 0, z1, rientro=0.3)
    gonna -= prisma_xz([(X0_SC - 3, Z0_SC + 0.4 + 3 * math.tan(math.radians(SCIVOLO_GRADI))), (X1_SC, z_scivolo(X1_SC) + 0.4), (X1_SC, -10), (X0_SC - 3, -10)], -20, 20)
    m += gonna
    m += scatola(R_INT + 0.1, R_EST + 1.0, -7.6, 7.6, Z_SOTTO_COP + 0.2, z1) ^ settore(R_INT + 0.1, R_EST + 1.0, VARCO, 0, Z_TOP + 5, rientro=0.3)
    # magnete 6x3 nell'ala che passa sopra la torretta del sensore
    a = HALL_SP["ang"]; xm, ym = (R_EST + 0.8) * math.cos(math.radians(a)), (R_EST + 0.8) * math.sin(math.radians(a))
    m += scatola(R_EST - 2, xm + 3.0, 6, ym + 3.0, z0, z1) + cil(4.3, z0, z1 + 1.0, xm, ym)
    m -= cil(3.15, z0 - 0.1, z0 + 3.0, xm, ym)
    return m

# ---------------------------------------------------------------- 6. scivolo e vaschetta
def scivolo():
    wl = W_SC + SVASO + 2.5
    m = prisma_xz([(X0_SC - 0.15, Z0_SC), (X1_SC, Z1_SC), (X1_SC, Z1_SC - 3), (X0_SC - 0.15, Z0_SC - 3)], -wl, wl)
    m += prisma_xz([(X1_SC - 0.5, Z1_SC), (X2_SC, Z2_SC), (X2_SC, Z2_SC - 3), (X1_SC - 0.5, Z1_SC - 3)], -wl, wl)
    m -= cil(X0_SC - 0.15, -50, 100)
    m -= cil(R_EST + 0.3, -50, 100) - settore(R_INT - 3, R_EST + 1, VARCO, -50, 100, rientro=0.3)
    # sponde che si allargano, poi dritte; bordino davanti
    for s in (1, -1):
        xs = [R_EST, X1_SC, X2_SC + 2]
        for xa, xb in zip(xs, xs[1:]):
            pts = [(xa, s * y_sponda(xa)), (xb, s * y_sponda(xb)), (xb, s * (y_sponda(xb) + 2.5)), (xa, s * (y_sponda(xa) + 2.5))]
            spon = Manifold.extrude(CrossSection([ccw(pts)]), 60).translate([0, 0, Z2_SC - 3])
            spon ^= prisma_xz([(xa - 1, z_scivolo(xa) + 12), (xb + 1, z_scivolo(xb) + 12), (xb + 1, -10), (xa - 1, -10)], -60, 60)
            m += spon
    m += scatola(X2_SC, X2_SC + 2.5, -wl, wl, Z2_SC - 3, Z2_SC + BORDINO_V)
    # flangia contro la parete, con 4 fori, e due gambe fino al tavolo
    fl = scatola(R_EST, R_EST + 3, -Y_VITI_SC - 5, Y_VITI_SC + 5, 0.0, Z0_SC - 2.0)
    fl -= scatola(R_EST - 1, R_EST + 4, -W_SC - 1.5, W_SC + 1.5, z_scivolo(R_EST + 3) - 3.5, 100)
    for y in (-Y_VITI_SC, Y_VITI_SC):
        for z in Z_VITI_SC:
            fl -= cil_x(1.7, R_EST - 1, R_EST + 4, y, z) + cil_x(3.0, R_EST + 1.6, R_EST + 4, y, z)
    m += fl
    for y in (-wl + 1.5, wl - 1.5):
        m += scatola(X2_SC - 6, X2_SC, y - 1.5, y + 1.5, 0.0, Z2_SC - 2.9)
    return m

def ingombro_motore():
    z = Z_DISCO - 2.4
    return cil(14.2, z - 19.5, z, MOTORE_X, 0) + cil(2.5, z, z + 4) + (cil(2.5, z + 4, z + 10) ^ scatola(-1.5, 1.5, -4, 4, z, z + 11)) + cil(4.5, z, z + 1.5)

def ingombro_cella():
    c = CELLA
    return scatola(c["r0"], c["r0"] + c["lung"], -c["larg"] / 2, c["larg"] / 2, Z_APPOGGIO + 3.1, Z_APPOGGIO + 3.1 + c["alt"])

def ingombro_vibro():
    return cil(VIBRO["rad"], 0, Z_TOP, VIBRO["r"], 0) ^ guscio_sotto(-2.05, -2.05 - VIBRO["alt"])

def sportello_aperto(gradi):
    """Lo sportello ruotato attorno alla cerniera (asse Y): positivo = si alza."""
    return sportello().translate([-CERN["x"], 0, -CERN["z"]]).rotate([0, -gradi, 0]).translate([CERN["x"], 0, CERN["z"]])

PEZZI = {"1_base": base, "2_fondo_a_rampa": fondo_rampa, "3_piastra_pesata": piastra, "3b_tappini_x2": tappi_piastra, "4_mozzo": mozzo,
         "5_paletta_x29": paletta, "6_scivolo_vaschetta": scivolo, "7_coperchio": coperchio, "8_sportello": sportello}

def a_mesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(g.vert_properties)[:, :3], faces=np.asarray(g.tri_verts), process=False)

def genera(cartella):
    for d in ("stl_per_stampa", "stl_assieme"): os.makedirs(os.path.join(cartella, d), exist_ok=True)
    solidi = {n: f() for n, f in PEZZI.items()}
    for n, m in solidi.items():
        mesh = a_mesh(m)
        if n != "5_paletta_x29": mesh.export(os.path.join(cartella, "stl_assieme", n + ".stl"))
        st = mesh.copy()
        if n == "5_paletta_x29": st.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        if n in ("3_piastra_pesata", "3b_tappini_x2"): st.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-PENDENZA), [0, 1, 0]))
        if n == "8_sportello": st.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))        # tetto sul piatto
        if n == "7_coperchio": st.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))        # piatto sul piatto, occhielli in alto
        if n == "6_scivolo_vaschetta": st.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))  # in piedi sulla flangia
        b = st.bounds
        st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
        st.export(os.path.join(cartella, "stl_per_stampa", n + ".stl"))
    for j in range(N):
        a_mesh(paletta_a(0.0, j)).export(os.path.join(cartella, "stl_assieme", f"5_paletta_{j:02d}.stl"))
    return solidi

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    solidi = genera(os.path.join(qui, ".."))
    for n, m in solidi.items():
        mesh = a_mesh(m); d = mesh.bounds[1] - mesh.bounds[0]
        print(f"{n:22s} {d[0]:6.1f} x {d[1]:6.1f} x {d[2]:5.1f} mm  {m.volume() / 1000:6.1f} cm3  pezzi: {len(m.decompose())}")
    print(f"Corpo: diametro {2 * R_EST:.1f} mm, altezza {Z_TOP:.1f} mm ({Z_TOP + 5.5:.1f} con la cerniera); con lo scivolo profondo {R_EST + X2_SC + 2.5:.0f} mm")
    print(f"Quote: ripiano {Z_RIPIANO:.1f}, sotto coperchio {Z_SOTTO_COP:.1f}, vaschetta da {Z1_SC:.1f} a {Z2_SC:.1f} (fondo a {Z2_SC - 3:.1f} dal tavolo)")
