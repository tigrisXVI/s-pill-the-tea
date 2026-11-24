#!/usr/bin/env python3
"""
S-pill the tea v0.5 - il "cofanetto" (prototipo)

Il meccanismo e' quello della v0.4 (carosello, rampa, piastra pesata, sportello alzato dal servo).
Cambia tutto l'esterno:
  - un GUSCIO unico arrotondato che nasconde il meccanismo; davanti, in alto, una fascia inclinata con
    display, tasto grande e una linea di luce; sotto, una NICCHIA
  - nella nicchia un BICCHIERINO estraibile: le pillole scendono dallo scivolo e ci cadono dentro
    (la vaschetta della v0.4 non c'e' piu': lo scivolo si ferma dove inizia il bicchierino)
  - un COFANETTO: coperchio esterno colorato con cerniera dietro; si apre per ricaricare
  - interruttore e presa USB dietro
  - lo sportello si alza di 35 gradi invece di 70: bastano per scoprire il varco e il cofanetto resta basso

    pip install manifold3d trimesh numpy
    python3 spill_v5.py

Misure in millimetri. Z in alto, il davanti (nicchia e fascia) e' verso +X.
"""
import math, os
import trimesh
import spill_v4 as v4
from spill_v4 import *

# ---------------------------------------------------------------- guscio
PARETE_G = 2.4
R_G = R_EST + 1.2 + PARETE_G          # 86,4: raggio esterno dietro
XF = 150.0                            # davanti
RC = 28.0                             # raggio degli spigoli davanti (in pianta)
H_G = 98.0                            # altezza del guscio (sopra c'e' il cofanetto)
Z_INCL, INCL = 50.0, 20.0             # da qui in su la fascia davanti pende indietro di 20 gradi
T = math.tan(math.radians(INCL))
FZ = (Z_INCL + H_G) / 2; FX = XF - (FZ - Z_INCL) * T      # centro della fascia
NICCHIA = dict(x0=93.0, y=31.0, z=46.0)                  # il muro dietro la nicchia parte a x0
X_FINE_SC = 99.5                      # lo scivolo finisce qui e le pillole cadono nel bicchierino
# bicchierino per mani che tremano: largo quanto la nicchia, alto, con il manico come una tazza, il bordo che rientra,
# il fondo che scende verso il becco dietro (si versa come da una lattiera) e 4 gommini sotto
BICCHIERE = dict(x0=96.0, x1=146.0, y=29.0, r=8.0, z0=2.6, alt=34.0, parete=2.6, basso=16.5, becco=23.5, labbro=2.5,
                 fondo_dietro=4.6, fondo_davanti=6.2)
DISPLAY = dict(a=-28.0, b=-4.0, larg=30.0, alt=16.0)      # coordinate sulla fascia: a = Y, b = in salita dal centro
TASTO = dict(a=28.0, b=-4.0, r=15.1)
LUCI = dict(b=19.5, larg=54.0, alt=10.5, pelle=0.6)
CERN_C = dict(x=-90.2, z=H_G + 1.6, r=3.2, perno=1.05)    # cerniera del cofanetto (perno da 2 mm o filamento)
SP_C = 3.2                            # spessore del cofanetto
APERTO = 35.0
INTERRUTTORE = dict(x=58.0, x_usb=88.0, z=26.0)       # sul fianco destro, a meta' altezza                         # gradi di apertura dello sportello comandati dal servo

def rett_arrotondato(x0, x1, y0, y1, r, z0, z1, n=10):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * i / n)), cy + r * math.sin(math.radians(a0 + 90 * i / n))) for i in range(n + 1)]
    return Manifold.extrude(CrossSection([ccw(pts)]), z1 - z0).translate([0, 0, z0])

def pianta(r, xf, rc, z0, z1):
    """Cerchio dietro (attorno al carosello) + rettangolo con spigoli tondi davanti."""
    pts = [(0, -r)]
    for cx, cy, a0 in ((xf - rc, -r + rc, -90), (xf - rc, r - rc, 0)):
        pts += [(cx + rc * math.cos(math.radians(a0 + 90 * i / 12)), cy + rc * math.sin(math.radians(a0 + 90 * i / 12))) for i in range(13)]
    pts += [(0, r)]
    return Manifold.extrude(CrossSection([ccw(pts)]), z1 - z0).translate([0, 0, z0]) + cil(r, z0, z1)

def taglio_fronte(rientro):
    """Tutto quello che sta davanti alla fascia inclinata (spostata di 'rientro' verso l'interno)."""
    x0 = XF - rientro
    return prisma_xz([(x0, Z_INCL), (x0 - (300 - Z_INCL) * T, 300), (500, 300), (500, Z_INCL)], -300, 300)

def sul_fronte(m):
    """Coordinate della fascia (X = fuori, Y = Y, Z = in salita) -> posto vero."""
    return m.rotate([0, -INCL, 0]).translate([FX, 0, FZ])

def esterno():
    return pianta(R_G, XF, RC, 0, H_G) - taglio_fronte(0)

def guscio():
    rin = PARETE_G / math.cos(math.radians(INCL))
    m = esterno() - (pianta(R_G - PARETE_G, XF - PARETE_G, RC - PARETE_G, -1, H_G + 1) - taglio_fronte(rin))
    # nicchia con il suo rivestimento: fondo, pareti, tetto e muro dietro (con la finestra per lo scivolo)
    n = NICCHIA
    m -= scatola(n["x0"] + PARETE_G, 300, -n["y"], n["y"], -1, n["z"])
    riv = (scatola(n["x0"], 300, -n["y"] - PARETE_G, n["y"] + PARETE_G, 0, n["z"] + PARETE_G) ^ esterno()) - scatola(n["x0"] + PARETE_G, 301, -n["y"], n["y"], 2.0, n["z"])
    riv -= scatola(n["x0"] - 1, n["x0"] + PARETE_G + 1, -21.5, 21.5, 20.0, 40.0)
    m += riv
    # fascia davanti: display, tasto, luce (la luce traspare da una pelle di 0,6 mm)
    d, t, l = DISPLAY, TASTO, LUCI
    m -= sul_fronte(scatola(-5, 1, d["a"] - d["larg"] / 2, d["a"] + d["larg"] / 2, d["b"] - d["alt"] / 2, d["b"] + d["alt"] / 2))
    m -= sul_fronte(cil_x(t["r"], -5, 1, t["a"], t["b"]))
    m -= sul_fronte(scatola(-5, -l["pelle"], -l["larg"] / 2, l["larg"] / 2, l["b"] - l["alt"] / 2, l["b"] + l["alt"] / 2))
    # dietro: foro per programmare l'ESP32 con il cavo USB (allineato a quello della base)
    m -= ruota(scatola(R_G - 4, R_G + 1, -7.0, 7.0, 4.0, 14.0), 180)
    # fianco destro (+Y, guardando la scatola da davanti): interruttore incassato e presa USB-C di alimentazione
    xi, zi = INTERRUTTORE["x"], INTERRUTTORE["z"]
    m -= scatola(xi - 6.75, xi + 6.75, R_G - 4, R_G + 1, zi - 4.5, zi + 4.5)
    m += scatola(xi - 9.5, xi + 9.5, R_G - 0.5, R_G + 2.5, zi - 7.5, zi + 7.5) - scatola(xi - 7.75, xi + 7.75, R_G - 1, R_G + 3, zi - 5.5, zi + 5.5)
    xu = INTERRUTTORE["x_usb"]
    m -= scatola(xu - 4.6, xu + 4.6, R_G - 4, R_G + 1, zi - 1.7, zi + 1.7)
    for dx in (-7.5, 7.5): m -= cil_y(1.3, R_G - 4, R_G + 1, xu + dx, zi)
    # griglia del cicalino, sui fianchi
    for ang in (100, 112, 124):
        for k in range(4): m -= ruota(scatola(R_G - 4, R_G + 1, -0.8, 0.8, 8 + 3 * k, 9.6 + 3 * k), ang)
    # cerniera del cofanetto: due nocche fisse
    c = CERN_C
    for s in (1, -1):
        y0, y1 = sorted((s * 10.6, s * 22.0))
        m += cil_y(c["r"], y0, y1, c["x"], c["z"]) + scatola(c["x"], R_G * -0.95, y0, y1, H_G - 8, c["z"])
        m -= cil_y(c["perno"], y0 - 1, y1 + 1, c["x"], c["z"])
    m -= cil_y(c["r"] + 0.5, -10.6, 10.6, c["x"], c["z"])
    return m

def cofanetto():
    c = CERN_C
    m = pianta(R_G, XF, RC, H_G, H_G + SP_C) - taglio_fronte(0)
    # bordino sotto che lo centra sul guscio (non sulla fascia davanti, dove c'e' la luce)
    rr = R_G - PARETE_G
    bordo = pianta(rr - 0.4, XF - PARETE_G - 0.4, RC - PARETE_G - 0.4, H_G - 3.4, H_G + 0.1) - pianta(rr - 2.0, XF - PARETE_G - 2.0, RC - PARETE_G - 2.0, H_G - 4, H_G + 1)
    m += bordo ^ scatola(-200, 100, -200, 200, 0, 200)
    # nocca centrale della cerniera e incavi per le nocche fisse
    m += cil_y(c["r"], -10.0, 10.0, c["x"], c["z"]) + scatola(c["x"], -80, -10.0, 10.0, H_G, H_G + SP_C)
    for s in (1, -1):
        y0, y1 = sorted((s * 10.2, s * 22.4))
        m -= scatola(-120, -80.5, y0, y1, H_G - 5, H_G + SP_C + 5)
    m -= cil_y(c["perno"], -11, 11, c["x"], c["z"])
    # una tacca davanti per sollevarlo con un dito
    m -= sul_fronte(scatola(-3, 3, -12, 12, 22.5, 30)) ^ scatola(0, 300, -12, 12, H_G - 1, H_G + 1.4)
    return m

def cofanetto_aperto(gradi):
    c = CERN_C
    return cofanetto().translate([-c["x"], 0, -c["z"]]).rotate([0, -gradi, 0]).translate([c["x"], 0, c["z"]])

def bicchierino():
    b = BICCHIERE; p = b["parete"]
    m = rett_arrotondato(b["x0"], b["x1"], -b["y"], b["y"], b["r"], b["z0"], b["alt"])
    # interno: il fondo scende verso il becco; in alto il bordo rientra (smusso a 45 gradi sotto, si stampa senza supporti)
    xi0, xi1, yi = b["x0"] + p, b["x1"] - p, b["y"] - p
    fondo = prisma_xz([(xi0 - 1, b["fondo_dietro"]), (xi1 + 1, b["fondo_davanti"]), (xi1 + 1, 60), (xi0 - 1, 60)], -50, 50)
    l = b["labbro"]; zl = b["alt"] - 2.0
    cavo = rett_arrotondato(xi0, xi1, -yi, yi, b["r"] - p, 0, zl - l)
    cavo += Manifold.batch_hull([rett_arrotondato(xi0, xi1, -yi, yi, b["r"] - p, zl - l - 0.01, zl - l),
                                 rett_arrotondato(xi0 + l, xi1 - l, -yi + l, yi - l, b["r"] - p - l, zl - 0.01, zl)])
    cavo += rett_arrotondato(xi0 + l, xi1 - l, -yi + l, yi - l, b["r"] - p - l, zl - 0.02, b["alt"] + 1)
    m -= cavo ^ fondo
    # dietro il bordo e' basso (ci passa sotto la fine dello scivolo) e fa da becco per versare
    m -= scatola(b["x0"] - 1, xi0 + 5, -b["becco"], b["becco"], b["basso"], 60)
    m -= prisma_xz([(xi0 + 5, b["basso"]), (xi0 + 5 + (b["alt"] - b["basso"]), b["alt"] + 0.01), (xi0 - 1, b["alt"] + 0.01)], -b["becco"] + l, b["becco"] - l) ^ scatola(0, 300, -50, 50, b["basso"], 60)
    # manico come quello di una tazza, davanti
    sf = lambda x, z: Manifold.sphere(4.6, 24).scale([1.0, 1.55, 1.0]).translate([x, 0, z])
    giro = [(b["x1"] - 3, b["alt"] - 5), (b["x1"] + 14, b["alt"] - 3), (b["x1"] + 24, b["alt"] - 8), (b["x1"] + 26, 19), (b["x1"] + 22, 10.5), (b["x1"] + 10, 9.0), (b["x1"] - 3, 9.0)]
    for (xa, za), (xb, zb) in zip(giro, giro[1:]): m += Manifold.batch_hull([sf(xa, za), sf(xb, zb)])
    m -= cavo ^ fondo                                                                        # il manico non entra nell'interno
    # 4 incavi per gommini adesivi da 8 mm
    for x in (b["x0"] + 8, b["x1"] - 8):
        for y in (-b["y"] + 8, b["y"] - 8): m -= cil(4.3, b["z0"] - 1, b["z0"] + 1.0, x, y)
    return m

def scivolo():
    """Lo scivolo della v0.3 fino a X_FINE_SC: senza vaschetta, gambe e bordino."""
    m = v3.scivolo() ^ scatola(-200, X_FINE_SC, -100, 100, -10, 200)
    # le sponde della v0.3 scendevano fino alle gambe: qui si fermano sotto il fondo dello scivolo
    xa, xb = R_EST + 3.0, X_FINE_SC + 1
    return m - prisma_xz([(xa, z_scivolo(xa) - 3.0), (xb, z_scivolo(xb) - 3.0), (xb, -20), (xa, -20)], -100, 100)

def base():
    """La base della v0.4 senza console e senza interruttore (ora stanno sul guscio)."""
    m = cil(R_EST, 0, Z_TOP) - cil(R_INT, 2.4, Z_TOP + 1)
    m -= cil(R_COP + 0.2, Z_SOTTO_COP, Z_TOP + 1)
    for ang in ANGOLI_VITI:
        col = cil(4.5, 2.4, Z_APPOGGIO, R_VITI, 0) + scatola(R_VITI, R_INT + 0.5, -3, 3, 2.4, Z_APPOGGIO)
        col -= cil(1.4, Z_APPOGGIO - 14, Z_APPOGGIO + 1, R_VITI, 0)
        m += ruota(col, ang)
    m -= settore(R_INT - 1, R_EST + 3, VARCO, z_scivolo(R_EST + 3) - 3.6, Z_TOP + 1)
    a = HALL_SP["ang"]
    tor = ruota(scatola(R_EST - 1, R_EST + 3.2, -3.2, 3.2, Z_SOTTO_COP - 18, Z_TOP), a) - ruota(scatola(R_EST - 0.2, R_EST + 2.0, -2.2, 2.2, Z_TOP - 5.0, Z_TOP + 1), a)
    # v0.5: i fili del sensore escono di lato, verso fuori (prima il foro portava dentro, tra le palette)
    tor -= ruota(cil_y(1.5, 0.0, 4.5, R_EST + 0.9, Z_TOP - 4.3), a)
    m += tor
    for y in (-Y_VITI_SC, Y_VITI_SC):
        for z in Z_VITI_SC:
            x = math.sqrt(R_INT ** 2 - y ** 2)
            m += cil_x(3.5, x - 5, x + 0.5, y, z) - cil_x(1.3, x - 6, R_EST + 1, y, z)
            m -= cil_x(1.6, x - 1, R_EST + 1, y, z)
    m -= ruota(scatola(R_COP - 1.0, R_EST + 1, -2.3, 2.3, Z_SOTTO_COP, Z_TOP + 1), 150)
    m -= ruota(scatola(R_INT - 1, R_EST + 1, -6.5, 6.5, 5, 13), 180)                        # cavo USB
    for ang in (100, 112, 124):                                                             # il cicalino si sente
        for k in range(4): m -= ruota(scatola(R_INT - 1, R_EST + 1, -0.8, 0.8, 8 + 3 * k, 9.6 + 3 * k), ang)
    for ang in (-40, 40, 75): m -= ruota(scatola(R_INT - 1, R_EST + 1, -9, 9, 4.0, Z_APPOGGIO - 3.0), ang)   # fili verso fascia e interruttore
    return m


# ---------------------------------------------------------------- correzioni trovate mettendo le viti nel modello
def fondo_rampa():
    """Come la v0.3, ma le viti del motore sono a testa svasata, a filo del disco: quelle a testa
    cilindrica sporgevano di 2,2 mm sotto il mozzo (che passa a 0,4 mm dal disco)."""
    m = v3.fondo_rampa()
    z_fl = Z_DISCO - 2.4
    pieno = cil(R_DISCO, 0, Z_DISCO) + solido_rampa(R_DISCO - 0.01, R_FONDO, Z_APPOGGIO)
    for y in VITI_MOTORE_Y:
        m += cil(3.4, z_fl + 1.8, Z_DISCO + 2, MOTORE_X, y) ^ pieno
        m -= cil(1.7, z_fl - 1, Z_DISCO + 1, MOTORE_X, y)
        m -= Manifold.cylinder(1.75, 1.65, 3.1, 48).translate([MOTORE_X, y, Z_DISCO - 1.7]) + cil(3.1, Z_DISCO - 0.01, Z_DISCO + 2, MOTORE_X, y)
    return m
VITI_MOTORE_Y = (-17.5, 17.5)

def piastra():
    """Come la v0.3, ma la svasatura sopra le viti e' profonda 4 mm (fondo piatto): 2 mm per la testa bassa e 2 per il
    tappino (incollato). Prima era 1,7 mm e la testa della vite non ci stava sotto il tappino."""
    m = v3.piastra()
    for x in v3.FORI_CELLA_LIBERO:
        m -= cil(3.1, z_fondo(0, x) - PROF_SVASO, Z_TOP, x, 0)          # fondo piatto: la testa appoggia tutta
    return m
PROF_SVASO = 4.0

def coperchio():
    """Come la v0.4, con lo spazio per le teste delle due viti del servo (prima finivano dentro la culla)."""
    m = v4.coperchio()
    for x in (SERVO["x"] - 18.9, SERVO["x"] + 8.2):
        m -= cil_y(2.3, -27.35, -22.0, x, SERVO["z"]) + scatola(x - 2.3, x + 2.3, -27.35, -22.0, SERVO["z"], Z_TOP + 9)
    return m

# ---------------------------------------------------------------- ingombri dei componenti (controlli e immagini)
def ingombro_display():   # modulo OLED 1,3": 36 x 34 x 4 mm
    d = DISPLAY
    return sul_fronte(scatola(-PARETE_G - 4.2, -PARETE_G - 0.2, d["a"] - 18, d["a"] + 18, d["b"] - 17, d["b"] + 17))

def ingombro_tasto():     # pulsante arcade da 30 mm: corpo, dado, cappello e ghiera fuori
    t = TASTO
    return sul_fronte(cil_x(14.0, -22, 0, t["a"], t["b"]) + cil_x(16.5, -PARETE_G - 6, -PARETE_G - 0.2, t["a"], t["b"])
                      + cil_x(18.0, 0.0, 1.6, t["a"], t["b"]) + cil_x(14.6, 1.6, 4.0, t["a"], t["b"]))

def ingombro_luci():
    l = LUCI
    return sul_fronte(scatola(-l["pelle"] - 3.4, -l["pelle"] - 0.1, -25.5, 25.5, l["b"] - 5, l["b"] + 5))

def ingombro_interruttore():   # interruttore a bilanciere KCD11 e presa USB-C da pannello con la sua schedina
    i = INTERRUTTORE
    return (scatola(i["x"] - 6.5, i["x"] + 6.5, R_G - 14, R_G, i["z"] - 4.3, i["z"] + 4.3) + scatola(i["x"] - 7.5, i["x"] + 7.5, R_G + 0.05, R_G + 1.8, i["z"] - 5, i["z"] + 5)
            + scatola(i["x_usb"] - 10, i["x_usb"] + 10, R_G - 11, R_G - 2.4, i["z"] - 6, i["z"] + 6))

def gradi_servo(gradi_sportello):
    return v4.gradi_servo(gradi_sportello)

leva_a, sportello_aperto, sportello, leva_servo, ingombro_servo = v4.leva_a, v4.sportello_aperto, v4.sportello, v4.leva_servo, v4.ingombro_servo

PEZZI = {"1_base": base, "2_fondo_a_rampa": fondo_rampa, "3_piastra_pesata": piastra, "3b_tappini_x2": tappi_piastra, "4_mozzo": mozzo,
         "5_paletta_x29": paletta, "6_scivolo": scivolo, "7_coperchio": coperchio, "8_sportello": sportello, "9_leva_servo": leva_servo,
         "10_guscio": guscio, "11_cofanetto": cofanetto, "12_bicchierino": bicchierino}
COMPONENTI = {"servo": ingombro_servo, "display": ingombro_display, "tasto": ingombro_tasto, "luci": ingombro_luci}

def genera(cartella):
    rot = trimesh.transformations.rotation_matrix
    for d in ("stampa", "assieme", "componenti"):
        dd = os.path.join(cartella, "stl", d); os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd): os.remove(os.path.join(dd, f))
    solidi = {n: f() for n, f in PEZZI.items()}
    for n, m in solidi.items():
        mesh = a_mesh(m)
        if n != "5_paletta_x29": mesh.export(os.path.join(cartella, "stl", "assieme", n + ".stl"))
        st = mesh.copy()
        if n == "5_paletta_x29": st.apply_transform(rot(math.pi / 2, [1, 0, 0]))
        if n in ("3_piastra_pesata", "3b_tappini_x2"): st.apply_transform(rot(math.radians(-PENDENZA), [0, 1, 0]))
        if n == "8_sportello": st.apply_transform(rot(math.pi / 2, [1, 0, 0]))
        if n == "9_leva_servo": st.apply_transform(rot(-math.pi / 2, [1, 0, 0]))
        if n == "6_scivolo": st.apply_transform(rot(-math.pi / 2, [0, 1, 0]))
        if n == "11_cofanetto": st.apply_transform(rot(math.pi, [1, 0, 0]))                 # capovolto: la faccia bella sul piatto
        b = st.bounds
        st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
        st.export(os.path.join(cartella, "stl", "stampa", n + ".stl"))
    for j in range(N):
        a_mesh(paletta_a(0.0, j)).export(os.path.join(cartella, "stl", "assieme", f"5_paletta_{j:02d}.stl"))
    for n, f in COMPONENTI.items():
        a_mesh(f()).export(os.path.join(cartella, "stl", "componenti", n + ".stl"))
    return solidi

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    solidi = genera(os.path.join(qui, ".."))
    for n, m in solidi.items():
        mesh = a_mesh(m); d = mesh.bounds[1] - mesh.bounds[0]
        print(f"{n:22s} {d[0]:6.1f} x {d[1]:6.1f} x {d[2]:5.1f} mm  {m.volume() / 1000:6.1f} cm3  pezzi: {len(m.decompose())}")
    tutto = a_mesh(solidi["10_guscio"] + solidi["11_cofanetto"] + ingombro_tasto())
    d = tutto.bounds[1] - tutto.bounds[0]
    print(f"Ingombro totale: {d[0]:.0f} x {d[1]:.0f} x {d[2]:.0f} mm. Servo: {gradi_servo(APERTO):.0f} gradi per alzare lo sportello di {APERTO:.0f}.")
