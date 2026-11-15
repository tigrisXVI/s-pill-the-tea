#!/usr/bin/env python3
"""
Scatoletta Blistra v0.7 - "due ruote" (prova, dall'idea di Giuseppe)

Due ruote in piedi, una a destra e una a sinistra, ognuna con 14 scomparti + 1 chiuso e il suo motorino
28BYJ-48. Le dosi si alternano: lun mattina dalla ruota di sinistra, lun mezzogiorno da quella di destra...
Lo scomparto che arriva in basso si svuota da solo (gravita'): niente sportelli e niente servi.
Le pillole cadono in un imbuto al centro e finiscono nel bicchierino, che sta sulla bilancia.

Ogni ruota sta in una CASSETTA che si sfila di lato: si appoggia sul tavolo, si apre il coperchio trasparente
e si riempiono i 14 scomparti. Quando la cassetta e' fuori, sotto l'uscita c'e' lo scomparto chiuso.

Assi: X verso chi usa la scatola (davanti), Y destra-sinistra (asse delle ruote), Z in alto. Misure in mm.
"""
import math, os
import trimesh
from manifold3d import Manifold, CrossSection
from scatoletta_v3 import cil, scatola, cil_x, cil_y, ruota, ccw, prisma_xz, a_mesh
import scatoletta_v5 as v5

# ---------------------------------------------------------------- ruota (coordinate locali: asse Z, tasche in XY)
N = 15; PASSO = 360.0 / N          # 14 dosi + 1 chiuso, 24 gradi
R_I = 23.5                         # dentro: mozzo (la compressa grande, larga 10,4, ci sta distesa)
R_O = R_I + 24.0                   # fuori: qui le tasche sono aperte
SP_DIV = 1.2                       # pareti tra le tasche
FONDO = 1.6                        # disco dietro le tasche
PROF = 10.0                        # profondita' delle tasche (verso il coperchio)
H_RUOTA = FONDO + PROF             # 11,6
ANG_CHIUSO = -90.0                 # lo scomparto chiuso guarda in basso (sull'uscita) a riposo

def settore_xy(r0, r1, a0, a1, z0, z1, n=24):
    pts = [(r0 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r0 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r1 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r1 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Manifold.extrude(CrossSection([ccw(pts)]), z1 - z0).translate([0, 0, z0])

def ruota_locale():
    m = cil(R_O, 0, FONDO) + cil(R_I, 0, H_RUOTA)
    for k in range(N):
        a = ANG_CHIUSO + PASSO / 2 + k * PASSO
        m += ruota(scatola(R_I - 0.5, R_O, -SP_DIV / 2, SP_DIV / 2, FONDO - 0.01, H_RUOTA), a)
    m += settore_xy(R_I - 0.5, R_O, ANG_CHIUSO - PASSO / 2, ANG_CHIUSO + PASSO / 2, FONDO - 0.01, H_RUOTA)   # scomparto chiuso
    m -= cil(2.65, -1, 8.0) ^ scatola(-1.6, 1.6, -4, 4, -1, 8.0)                               # albero del motore (a D)
    m -= cil(6.0, H_RUOTA - 3.0, H_RUOTA + 1) - cil(2.0, H_RUOTA - 4, H_RUOTA + 2)            # incavo per girarla a mano
    return m

# ---------------------------------------------------------------- cassetta (locale): dietro, anello con l'uscita, coperchio
G = 0.4
R_ANELLO = R_O + G                 # 44,4
SP_ANELLO = 1.6
R_CASS = R_ANELLO + SP_ANELLO      # 46
Z_DIETRO0, Z_DIETRO1 = -G - 1.6, -G
Z_COP0 = H_RUOTA + 0.2
Z_COP1 = Z_COP0 + 1.6
Z_FLANGIA1 = Z_COP1 + 1.6
R_FLANGIA = R_CASS + 2.0
USCITA = 8.0                       # mezza larghezza della finestra in basso

def cassetta_locale():
    m = cil(R_CASS, Z_DIETRO0, Z_COP1) - cil(R_ANELLO, Z_DIETRO1, Z_COP1 + 1)
    m -= cil(4.2, Z_DIETRO0 - 1, Z_DIETRO1 + 1)                                               # passa l'albero del motore
    m -= scatola(-USCITA, USCITA, -R_CASS - 1, -R_ANELLO + 2, FONDO - 0.2, H_RUOTA + 0.01)     # uscita in basso
    m += cil(R_FLANGIA, Z_COP1, Z_FLANGIA1) - cil(R_ANELLO - 3.0, Z_COP1 - 1, Z_FLANGIA1 + 1)  # flangia: fa da fianco della scatola
    m += scatola(-12, 12, R_FLANGIA - 4, R_FLANGIA, Z_FLANGIA1 - 0.01, Z_FLANGIA1 + 6) - scatola(-10, 10, R_FLANGIA - 6, R_FLANGIA - 2.2, Z_FLANGIA1, Z_FLANGIA1 + 7)  # maniglia
    return m

def coperchio_locale():
    """Trasparente (PETG): si vedono le pillole. Si incastra nell'anello."""
    return cil(R_ANELLO - 0.15, Z_COP0, Z_COP1) + cil(R_ANELLO - 3.2, Z_COP1 - 0.01, Z_FLANGIA1 - 0.2)

# ---------------------------------------------------------------- dove stanno le cose nella scatola
Y_MOT = 19.7                       # faccia della parete su cui e' avvitato il motore
Y_PARETE = 21.3                    # parete dietro la cassetta
Y_RUOTA = Y_PARETE - Z_DIETRO0     # dove sta lo zero locale della ruota (|y|)
Y_FIANCO = Y_RUOTA + Z_FLANGIA1    # fianco della scatola
X_HALF = R_FLANGIA + 3.0
PARETE = 2.4

def metti(m, lato):
    """Da locale (asse Z) a mondo (asse Y), lato -1 = sinistra (Y negativa), +1 = destra."""
    m = m.rotate([90, 0, 0]).translate([0, -Y_RUOTA, Z_A])          # locale z -> -y
    return m if lato < 0 else m.mirror([0, 1, 0])

# ---------------------------------------------------------------- imbuto e bicchierino
Z_CUP = 13.0
CUP = dict(x0=-24.0, x1=30.0, y=22.0, alt=26.0, parete=2.0, r=6.0)
Z_IMB1 = Z_CUP + CUP["alt"] + 3.0  # bocca dell imbuto, sopra il bicchierino (e sopra il manico che passa)
Y_BOCCA = 9.0
Z_A = Z_IMB1 + 25.0 + R_FLANGIA + 1.4   # asse delle ruote: abbastanza in alto perche' l'imbuto penda 42 gradi
Z_IMB0 = Z_A - R_FLANGIA - 1.4     # sotto le cassette
Y_IMB = Y_FIANCO - PARETE - 0.3     # l'imbuto arriva fino al fianco

def imbuto():
    """Due scivoli inclinati (uno per ruota) che portano le pillole al centro, nel bicchierino."""
    larg = USCITA + 3.0
    ye = Y_IMB                                                                                  # oltre il bordo esterno della finestra
    prof = [(Y_BOCCA, Z_IMB1 - 2.4), (ye, Z_IMB0 - 2.4), (ye, Z_IMB0), (Y_BOCCA, Z_IMB1)]
    sez = Manifold.extrude(CrossSection([ccw(prof)]), 2 * larg).translate([0, 0, -larg])
    sez = sez.transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])                            # (y, z, x) -> mondo
    m = sez + sez.mirror([0, 1, 0])
    for x in (-larg - 1.6, larg):
        m += scatola(x, x + 1.6, -ye, ye, Z_IMB1 - 0.5, Z_IMB0 + 0.6)
    return m

def ingombri_percorso():
    return Manifold()

def bicchierino():
    c = CUP
    m = v5.rett_arrotondato(c["x0"], c["x1"], -c["y"], c["y"], c["r"], Z_CUP, Z_CUP + c["alt"])
    m -= v5.rett_arrotondato(c["x0"] + c["parete"], c["x1"] - c["parete"], -c["y"] + c["parete"], c["y"] - c["parete"], c["r"] - c["parete"], Z_CUP + 2.0, Z_CUP + c["alt"] + 1)
    # bordo che rientra sui fianchi e davanti
    lab = v5.rett_arrotondato(c["x0"] + c["parete"], c["x1"] - c["parete"], -c["y"] + c["parete"], c["y"] - c["parete"], c["r"] - c["parete"], Z_CUP + c["alt"] - 1.6, Z_CUP + c["alt"])
    lab -= v5.rett_arrotondato(c["x0"] + 6, c["x1"] - 4.5, -c["y"] + 4.5, c["y"] - 4.5, 3, Z_CUP + c["alt"] - 2, Z_CUP + c["alt"] + 1)
    m += lab
    # manico a tazza davanti
    sf = lambda x, z: Manifold.sphere(4.4, 24).scale([1.0, 1.55, 1.0]).translate([x, 0, z])
    giro = [(c["x1"] - 3, Z_CUP + c["alt"] - 5), (c["x1"] + 12, Z_CUP + c["alt"] - 3), (c["x1"] + 21, Z_CUP + c["alt"] - 9), (c["x1"] + 22, Z_CUP + 11),
            (c["x1"] + 16, Z_CUP + 5), (c["x1"] - 3, Z_CUP + 5)]
    for (xa, za), (xb, zb) in zip(giro, giro[1:]): m += Manifold.batch_hull([sf(xa, za), sf(xb, zb)])
    m -= v5.rett_arrotondato(c["x0"] + c["parete"], c["x1"] - c["parete"], -c["y"] + c["parete"], c["y"] - c["parete"], c["r"] - c["parete"], Z_CUP + 2.0, Z_CUP + c["alt"] - 1.6)
    for x in (c["x0"] + 7, c["x1"] - 7):
        for y in (-c["y"] + 7, c["y"] - 7): m -= cil(4.3, Z_CUP - 1, Z_CUP + 1.0, x, y)
    return m

CELLA_X = 4.0
def piatto_bilancia():
    c = CUP
    m = v5.rett_arrotondato(c["x0"] + 4, c["x1"] - 4, -c["y"] + 4, c["y"] - 4, 4, Z_CUP - 2.4, Z_CUP - 0.1)
    m += scatola(CELLA_X + 8, CELLA_X + 22, -6, 6, Z_CUP - 4.6, Z_CUP - 2.3)
    return m
def ingombro_cella(): return scatola(CELLA_X - 25, CELLA_X + 22, -6, 6, Z_CUP - 10.6, Z_CUP - 4.6)

# ---------------------------------------------------------------- telaio (guscio con le sedi delle cassette)
H = Z_A + R_FLANGIA + 3.5
RV = 12.0                          # raccordo degli spigoli verticali
DISPLAY = dict(x=-20.0); TASTO = dict(x=24.0, r=15.1)

def scatola_arrotondata(x0, x1, y0, y1, r, z0, z1):
    return v5.rett_arrotondato(x0, x1, y0, y1, r, z0, z1)

def telaio():
    m = scatola_arrotondata(-X_HALF, X_HALF, -Y_FIANCO, Y_FIANCO, RV, 0, H)
    m -= scatola_arrotondata(-X_HALF + PARETE, X_HALF - PARETE, -Y_FIANCO + PARETE, Y_FIANCO - PARETE, RV - PARETE, PARETE, H - PARETE)
    # pareti su cui sono avvitati i motori, con il foro per l'albero
    for s in (-1, 1):
        y0, y1 = sorted((s * Y_MOT, s * Y_PARETE))
        par = scatola(-X_HALF + 1, X_HALF - 1, y0, y1, Z_A - R_FLANGIA - 0.4, H - 1) - cil_y(5.0, y0 - 1, y1 + 1, 0, Z_A)
        for xm in (-17.5, 17.5): par -= cil_y(1.4, y0 - 1, y1 + 1, xm, Z_A - 8)                 # viti del motore
        m += par
    # sedi delle cassette: si sfilano di lato
    for s in (-1, 1):
        y0, y1 = sorted((s * Y_PARETE, s * (Y_FIANCO + 1)))
        m -= cil_y(R_CASS + G, y0, y1, 0, Z_A)
        y2, y3 = sorted((s * (Y_RUOTA + Z_COP1 - 0.01), s * (Y_FIANCO + 1)))
        m -= cil_y(R_FLANGIA + G, y2, y3, 0, Z_A)
        m -= scatola(-USCITA - 1, USCITA + 1, min(y0, y1), max(y0, y1), Z_IMB0 - 3, Z_A - R_CASS + 2)   # passaggio verso l'imbuto
        yr = sorted((s * Y_PARETE, s * (Y_RUOTA + Z_COP1 - 0.01)))
        m += (cil_y(R_CASS + G + 1.6, yr[0], yr[1], 0, Z_A) - cil_y(R_CASS + G, yr[0] - 1, yr[1] + 1, 0, Z_A)
              - scatola(-USCITA - 1, USCITA + 1, min(y0, y1) - 1, max(y0, y1) + 1, Z_IMB0 - 4, Z_A - R_CASS + 2)) ^ scatola_arrotondata(-X_HALF, X_HALF, -Y_FIANCO, Y_FIANCO, RV, 0, H)
    # davanti: apertura del bicchierino
    m -= scatola(CUP["x0"] - 1, X_HALF + 1, -CUP["y"] - 1, CUP["y"] + 1, Z_CUP - 0.5, Z_CUP + CUP["alt"] + 2.5)
    # sopra: display e tasto
    m -= scatola(DISPLAY["x"] - 15, DISPLAY["x"] + 15, -8, 8, H - PARETE - 1, H + 1)
    m -= cil(TASTO["r"], H - PARETE - 1, H + 1, TASTO["x"], 0)
    m -= scatola(X_HALF - PARETE - 1, X_HALF - 0.6, -14, 14, H - 12, H - 6)                     # luce sotto la pelle, davanti in alto
    m -= scatola(-X_HALF - 1, -X_HALF + PARETE + 1, -5, 5, 4, 12)                               # USB-C dietro
    for k in range(4): m -= scatola(-X_HALF - 1, -X_HALF + PARETE + 1, -14 + 7 * k, -11 + 7 * k, 20, 40)   # griglia del cicalino
    # appoggio della cella di carico
    m += scatola(CELLA_X - 25, CELLA_X - 9, -7, 7, PARETE - 0.01, Z_CUP - 10.6)
    return m

# ---------------------------------------------------------------- componenti
def motore(lato):
    """28BYJ-48 avvitato alla parete centrale, il corpo verso il centro, l'albero nella ruota."""
    s = lato
    fl = s * Y_MOT
    corpo = cil_y(14.2, min(fl, fl - s * 19.5), max(fl, fl - s * 19.5), 0, Z_A - 8)              # l'albero e' 8 mm fuori centro
    alette = scatola(-21.0, 21.0, min(fl, fl - s * 0.8), max(fl, fl - s * 0.8), Z_A - 8 - 3.5, Z_A - 8 + 3.5)
    scatolina = scatola(-7.3, 7.3, min(fl - s * 0.8, fl - s * 17.0), max(fl - s * 0.8, fl - s * 17.0), Z_A - 8 - 17.3, Z_A - 8 - 10)
    alb = cil_y(4.5, min(fl, fl + s * 1.5), max(fl, fl + s * 1.5), 0, Z_A) + cil_y(2.5, min(fl, fl + s * 9.5), max(fl, fl + s * 9.5), 0, Z_A)
    return corpo + alette + scatolina + alb

def ingombro_display():
    return scatola(DISPLAY["x"] - 17.7, DISPLAY["x"] + 17.7, -16.8, 16.8, H - PARETE - 4.2, H - PARETE - 0.2)
def ingombro_tasto():
    t = TASTO; return cil(14.0, H - 22, H, t["x"], 0) + cil(18.0, H, H + 1.6, t["x"], 0) + cil(14.6, H + 1.6, H + 4, t["x"], 0)
def ingombro_schede():
    """ESP32-S3 SuperMini, due DRV8833, HX711, cicalino: dietro, sotto i motori."""
    return (scatola(-48, -25.5, -9, 9, 44, 49) + scatola(-48, -29.5, -17, -1, 52, 58) + scatola(-48, -29.5, 1, 17, 52, 58)
            + scatola(-48, -27, -10.5, 10.5, 61, 66) + cil_x(6.0, -48.6, -39, 0, 30))

PEZZI = {
    "1_telaio": telaio,
    "2_imbuto": imbuto,
    "3_cassetta_sx": lambda: metti(cassetta_locale(), -1), "4_ruota_sx": lambda: metti(ruota_locale(), -1), "5_coperchio_sx": lambda: metti(coperchio_locale(), -1),
    "6_cassetta_dx": lambda: metti(cassetta_locale(), 1), "7_ruota_dx": lambda: metti(ruota_locale(), 1), "8_coperchio_dx": lambda: metti(coperchio_locale(), 1),
    "9_bicchierino": bicchierino, "10_piatto_bilancia": piatto_bilancia,
}
COMPONENTI = {"motore_sx": lambda: motore(-1), "motore_dx": lambda: motore(1), "cella": ingombro_cella, "display": ingombro_display,
              "tasto": ingombro_tasto, "schede": ingombro_schede}

def genera(cartella):
    for d in ("stampa", "assieme", "componenti"):
        dd = os.path.join(cartella, d); os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd): os.remove(os.path.join(dd, f))
    solidi = {n: f() for n, f in PEZZI.items()}
    for n, m in solidi.items():
        mesh = a_mesh(m); mesh.export(os.path.join(cartella, "assieme", n + ".stl"))
        st = mesh.copy(); b = st.bounds
        st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
        st.export(os.path.join(cartella, "stampa", n + ".stl"))
    for n, f in COMPONENTI.items(): a_mesh(f()).export(os.path.join(cartella, "componenti", n + ".stl"))
    return solidi

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    solidi = genera(os.path.join(qui, "..", "v7", "stl"))
    for n, m in solidi.items():
        mesh = a_mesh(m); d = mesh.bounds[1] - mesh.bounds[0]
        print(f"{n:20s} {d[0]:6.1f} x {d[1]:6.1f} x {d[2]:5.1f} mm  {m.volume() / 1000:6.1f} cm3  pezzi: {len(m.decompose())}")
    tutto = a_mesh(sum(solidi.values(), Manifold()))
    d = tutto.bounds[1] - tutto.bounds[0]
    print(f"Ingombro totale (con il manico del bicchierino): {d[0]:.0f} x {d[1]:.0f} x {d[2]:.0f} mm")
    print(f"Senza manico: {2 * X_HALF:.0f} x {2 * Y_FIANCO:.0f} x {H:.0f} mm = {2 * X_HALF * 2 * Y_FIANCO * H / 1e6:.2f} litri")
