#!/usr/bin/env python3
"""
Scatoletta Blistra v0.4 - modello 3D parametrico (prototipo)

Parte dalla v0.3 (scatoletta_v3.py: carosello, rampa, piastra pesata, scivolo restano uguali) e aggiunge:
  - una console inclinata a 45 gradi accanto allo scivolo, con display OLED da 1,3", tasto grande da 30 mm
    e una barra di 8 luci colorate dietro una pelle sottile
  - lo sportello motorizzato: un micro servo (tipo SG90) sul coperchio lo alza con una leva; si richiude
    da solo per gravita', quindi non puo' schiacciare le dita e si puo' sempre alzare a mano
  - un interruttore di accensione incassato, dietro, protetto da un collare

    pip install manifold3d trimesh numpy
    python3 scatoletta_v4.py

Misure in millimetri. Z verso l'alto, lo sportello e lo scivolo sono sul lato +X.
"""
import math, os
import numpy as np
import trimesh
import scatoletta_v3 as v3
from scatoletta_v3 import *

# ---------------------------------------------------------------- console
ANG_CONS = -62.0                      # dove sta la console, in gradi (lo scivolo e' a 0)
CONS = dict(sporge=40.0, alta=52.0, piede=12.0, mezza=48.0, pelle=2.4)
C45 = math.sqrt(0.5)
CX, CZ = R_EST + CONS["sporge"] - 20.0, CONS["piede"] + 20.0          # centro della faccia inclinata
DISPLAY = dict(a=-22.0, b=-4.0, larg=30.0, alt=16.0)                   # finestra per OLED 1,3" (parte visibile 29,4 x 14,7)
TASTO = dict(a=24.0, b=-5.0, r=15.1)                                   # pulsante arcade da 30 mm a profilo basso
LUCI = dict(b=19.0, larg=54.0, alt=11.0, pelle=0.6)                    # barra WS2812 da 8 LED (51 x 10 mm)
INTERRUTTORE = dict(ang=225.0, larg=13.5, alt=9.0, z=13.5)             # a bilanciere tipo KCD11
ANGOLI_GRIGLIA = (90, 135)

def _mezzo_spazio(dx):
    """Tutto quello che sta oltre la faccia inclinata (spostata di dx verso l'interno)."""
    x0, z0 = R_EST + CONS["sporge"] - dx, CONS["piede"]
    return prisma_xz([(x0 + 100, z0 - 100), (x0 + 200, z0), (x0, z0 + 200), (x0 - 100, z0 + 100)], -200, 200)

def _sulla_faccia(m):
    """Porta un solido dalle coordinate della faccia (X = normale, Y = lungo la faccia, Z = in salita) al suo posto."""
    return ruota(m.rotate([0, -45, 0]).translate([CX, 0, CZ]), ANG_CONS)

def base():
    c = CONS
    m = cil(R_EST, 0, Z_TOP) - cil(R_INT, 2.4, Z_TOP + 1)
    m -= cil(R_COP + 0.2, Z_SOTTO_COP, Z_TOP + 1)
    for ang in ANGOLI_VITI:
        col = cil(4.5, 2.4, Z_APPOGGIO, R_VITI, 0) + scatola(R_VITI, R_INT + 0.5, -3, 3, 2.4, Z_APPOGGIO)
        col -= cil(1.4, Z_APPOGGIO - 14, Z_APPOGGIO + 1, R_VITI, 0)
        m += ruota(col, ang)
    m -= settore(R_INT - 1, R_EST + 3, VARCO, z_scivolo(R_EST + 3) - 3.6, Z_TOP + 1)
    a = HALL_SP["ang"]
    tor = ruota(scatola(R_EST - 1, R_EST + 3.2, -3.2, 3.2, Z_SOTTO_COP - 18, Z_TOP), a) - ruota(scatola(R_EST - 0.2, R_EST + 2.0, -2.2, 2.2, Z_TOP - 5.0, Z_TOP + 1), a)
    tor -= ruota(cil_x(1.0, R_INT - 1, R_EST + 2.0, 0, Z_TOP - 4.0), a)
    m += tor
    for y in (-Y_VITI_SC, Y_VITI_SC):
        for z in Z_VITI_SC:
            x = math.sqrt(R_INT ** 2 - y ** 2)
            m += cil_x(3.5, x - 5, x + 0.5, y, z) - cil_x(1.3, x - 6, R_EST + 1, y, z)
            m -= cil_x(1.6, x - 1, R_EST + 1, y, z)
    m -= ruota(scatola(R_COP - 1.0, R_EST + 1, -2.3, 2.3, Z_SOTTO_COP, Z_TOP + 1), 150)
    m -= ruota(scatola(R_INT - 1, R_EST + 1, -6.5, 6.5, 5, 13), 180)                        # cavo USB (dietro)
    for ang in ANGOLI_GRIGLIA:                                                              # griglia: il cicalino si sente
        for k in range(4): m -= ruota(scatola(R_INT - 1, R_EST + 1, -0.8, 0.8, 6 + 3 * k, 7.6 + 3 * k), ang)
    # interruttore incassato: foro nella parete e collare che lo protegge dai colpi
    i = INTERRUTTORE
    col = scatola(R_EST - 0.6, R_EST + 4.0, -i["larg"] / 2 - 3, i["larg"] / 2 + 3, i["z"] - i["alt"] / 2 - 3, i["z"] + i["alt"] / 2 + 3)
    col -= scatola(R_EST - 1, R_EST + 5, -i["larg"] / 2 - 1, i["larg"] / 2 + 1, i["z"] - i["alt"] / 2 - 1, i["z"] + i["alt"] / 2 + 1)
    m += ruota(col, i["ang"])
    m -= ruota(scatola(R_INT - 1, R_EST + 1, -i["larg"] / 2, i["larg"] / 2, i["z"] - i["alt"] / 2, i["z"] + i["alt"] / 2), i["ang"])
    # console: guscio fuori dalla parete, cavo dentro, aperto verso il vano dell'elettronica
    fuori = scatola(50, R_EST + c["sporge"], -c["mezza"], c["mezza"], 0, c["alta"]) - _mezzo_spazio(0) - cil(R_EST - 0.2, -1, 100)
    dentro = scatola(50, R_EST + c["sporge"] - c["pelle"], -c["mezza"] + c["pelle"], c["mezza"] - c["pelle"], 2.4, c["alta"] - c["pelle"])
    dentro = dentro - _mezzo_spazio(c["pelle"] / C45) - cil(R_EST, -1, 100)
    m += ruota(fuori, ANG_CONS)
    m -= ruota(dentro, ANG_CONS)
    m -= ruota(scatola(R_INT - 1, R_EST + 1, -30, 30, 4.0, Z_APPOGGIO - 3.0), ANG_CONS)    # passaggio dei fili verso il vano
    d, t, l = DISPLAY, TASTO, LUCI
    m -= _sulla_faccia(scatola(-4, 1, d["a"] - d["larg"] / 2, d["a"] + d["larg"] / 2, d["b"] - d["alt"] / 2, d["b"] + d["alt"] / 2))
    m -= _sulla_faccia(cil_x(t["r"], -4, 1, t["a"], t["b"]))
    m -= _sulla_faccia(scatola(-4, -l["pelle"], -l["larg"] / 2, l["larg"] / 2, l["b"] - l["alt"] / 2, l["b"] + l["alt"] / 2))
    m -= _sulla_faccia(cil_x(2.5, -4, 1, 38.0, 21.0))                                       # i fili del servo entrano qui
    return m

# ---------------------------------------------------------------- sportello motorizzato
SERVO = dict(x=CERN["x"], z=CERN["z"] + 4.0, braccio=14.0, perno=1.5)   # asse del servo: sopra la cerniera, parallelo
Y_LEVA = (-19.0, -16.5)            # spessore della leva
Y_ALETTA = (-15.6, -12.4)          # l'aletta dello sportello su cui spinge il perno
APERTO = 70.0                      # gradi di apertura comandati dal servo
Z_COP_SU = Z_TOP

def gradi_servo(gradi_sportello):
    """Di quanto deve girare il servo per alzare lo sportello di tot gradi (il perno scorre sotto la mensola)."""
    t = math.radians(gradi_sportello)
    return gradi_sportello + math.degrees(math.asin(4.0 * (1 - math.cos(t)) / SERVO["braccio"]))

def coperchio():
    m = v3.coperchio()
    sx, sz = SERVO["x"], SERVO["z"]
    culla = scatola(sx - 22.5, sx + 12.0, -46.5, -22.6, Z_TOP - 0.1, Z_TOP + 8.0)
    culla -= scatola(sx - 16.8, sx + 6.1, -46.0, -22.5, sz - 6.1, Z_TOP + 20)                # corpo del servo, coricato
    culla -= scatola(sx - 21.7, sx + 11.2, -30.4, -27.2, sz - 6.1, Z_TOP + 20)               # le due alette di fissaggio
    for x in (sx - 18.9, sx + 8.2): culla -= cil_y(0.8, -40, -27, x, sz)                     # fori guida per le sue viti
    return m + culla

def sportello():
    m = v3.sportello()
    z0, z1 = Z_TOP + 0.2, Z_TOP + 2.2
    y0, y1 = Y_ALETTA
    al = scatola(CERN["x"], CERN["x"] + 23.0, y0, y1, z0, z1) + scatola(CERN["x"] + 3.2, CERN["x"] + 23.0, y1 - 0.1, -11.5, z0, z1)
    al += scatola(CERN["x"] + 20.0, CERN["x"] + 23.0, y0, y1, z0, SERVO["z"] + 3.5)          # montante
    al += scatola(CERN["x"] + 11.0, CERN["x"] + 23.0, y0, y1, SERVO["z"] + 1.5, SERVO["z"] + 3.5)   # mensola: il perno spinge qui sotto
    return m + al

def leva_servo():
    sx, sz, b = SERVO["x"], SERVO["z"], SERVO["braccio"]
    ya, yb = Y_LEVA
    m = scatola(sx, sx + b, ya, yb, sz - 3.5, sz + 3.5) + cil_y(3.5, ya, yb, sx, sz) + cil_y(3.5, ya, yb, sx + b, sz)
    m += cil_y(SERVO["perno"], yb - 0.1, Y_ALETTA[1] - 0.3, sx + b, sz)                      # perno che alza lo sportello
    m -= scatola(sx - 3.8, sx + b - 1.0, ya - 0.1, ya + 1.5, sz - 2.8, sz + 2.8)             # sede della squadretta del servo
    m -= cil_y(1.2, ya - 1, yb + 1, sx, sz)                                                  # vite centrale
    return m

def leva_a(gradi):
    return leva_servo().translate([-SERVO["x"], 0, -SERVO["z"]]).rotate([0, -gradi, 0]).translate([SERVO["x"], 0, SERVO["z"]])

def sportello_aperto(gradi):
    return sportello().translate([-CERN["x"], 0, -CERN["z"]]).rotate([0, -gradi, 0]).translate([CERN["x"], 0, CERN["z"]])

# ---------------------------------------------------------------- ingombri dei componenti nuovi (solo per i controlli)
def ingombro_servo():
    sx, sz = SERVO["x"], SERVO["z"]
    return scatola(sx - 16.6, sx + 5.9, -45.7, -23.0, sz - 6.1, sz + 6.1) + scatola(sx - 21.5, sx + 10.8, -30.2, -27.4, sz - 6.1, sz + 6.1) + cil_y(2.4, -23.0, -19.0, sx, sz)

def ingombro_display():   # modulo OLED 1,3": 36 x 34 x 4 mm, dietro la finestra
    d = DISPLAY
    return _sulla_faccia(scatola(-CONS["pelle"] - 4.2, -CONS["pelle"] - 0.2, d["a"] - 18, d["a"] + 18, d["b"] - 17, d["b"] + 17))

def ingombro_tasto():     # corpo del pulsante: 28 mm di diametro, 22 mm sotto la faccia, ghiera da 36 mm
    t = TASTO
    return _sulla_faccia(cil_x(14.0, -22, 0, t["a"], t["b"]) + cil_x(18.0, -CONS["pelle"] - 6, -CONS["pelle"] - 0.2, t["a"], t["b"]))

def ingombro_luci():
    l = LUCI
    return _sulla_faccia(scatola(-l["pelle"] - 3.4, -l["pelle"] - 0.1, -25.5, 25.5, l["b"] - 5, l["b"] + 5))

PEZZI = {"1_base": base, "2_fondo_a_rampa": fondo_rampa, "3_piastra_pesata": piastra, "3b_tappini_x2": tappi_piastra, "4_mozzo": mozzo,
         "5_paletta_x29": paletta, "6_scivolo_vaschetta": scivolo, "7_coperchio": coperchio, "8_sportello": sportello, "9_leva_servo": leva_servo}

def genera(cartella):
    rot = trimesh.transformations.rotation_matrix
    for d in ("stampa", "assieme"): os.makedirs(os.path.join(cartella, "stl", d), exist_ok=True)
    solidi = {n: f() for n, f in PEZZI.items()}
    for n, m in solidi.items():
        mesh = a_mesh(m)
        if n != "5_paletta_x29": mesh.export(os.path.join(cartella, "stl", "assieme", n + ".stl"))
        st = mesh.copy()
        if n == "5_paletta_x29": st.apply_transform(rot(math.pi / 2, [1, 0, 0]))
        if n in ("3_piastra_pesata", "3b_tappini_x2"): st.apply_transform(rot(math.radians(-PENDENZA), [0, 1, 0]))
        if n == "8_sportello": st.apply_transform(rot(math.pi / 2, [1, 0, 0]))               # sul fianco: aletta e mensola senza supporti
        if n == "9_leva_servo": st.apply_transform(rot(-math.pi / 2, [1, 0, 0]))             # piatta, perno in alto
        if n == "6_scivolo_vaschetta": st.apply_transform(rot(-math.pi / 2, [0, 1, 0]))
        b = st.bounds
        st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
        st.export(os.path.join(cartella, "stl", "stampa", n + ".stl"))
    for j in range(N):
        a_mesh(paletta_a(0.0, j)).export(os.path.join(cartella, "stl", "assieme", f"5_paletta_{j:02d}.stl"))
    # i componenti comprati, come semplici ingombri: servono solo per le immagini e per il visore
    os.makedirs(os.path.join(cartella, "stl", "componenti"), exist_ok=True)
    for n, f in (("servo", ingombro_servo), ("display", ingombro_display), ("tasto", ingombro_tasto), ("luci", ingombro_luci)):
        a_mesh(f()).export(os.path.join(cartella, "stl", "componenti", n + ".stl"))
    return solidi

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    solidi = genera(os.path.join(qui, ".."))
    for n, m in solidi.items():
        mesh = a_mesh(m); d = mesh.bounds[1] - mesh.bounds[0]
        print(f"{n:22s} {d[0]:6.1f} x {d[1]:6.1f} x {d[2]:5.1f} mm  {m.volume() / 1000:6.1f} cm3  pezzi: {len(m.decompose())}")
    tutto = a_mesh(sum((m for n, m in solidi.items() if n != "5_paletta_x29"), Manifold()) + ingombro_servo())
    d = tutto.bounds[1] - tutto.bounds[0]
    print(f"Ingombro totale: {d[0]:.0f} x {d[1]:.0f} x {d[2]:.0f} mm. Servo: {gradi_servo(APERTO):.0f} gradi per aprire lo sportello di {APERTO:.0f}.")
