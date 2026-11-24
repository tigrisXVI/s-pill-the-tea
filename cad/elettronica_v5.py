"""S-pill the tea v0.5: elettronica, viti, perni e cavi (solo ingombri, per i controlli, le immagini e il visore).

Le schede stanno nel vano sotto il fondo (alto 22 mm), appoggiate su biadesivo spesso. Le misure sono quelle
dei moduli piu' comuni; se il tuo e' diverso controlla che entri.

    python3 elettronica_v5.py      -> controlla che niente si tocchi e scrive stl/componenti
"""
import math, os
import spill_v5 as s
from spill_v5 import cil, cil_x, cil_y, scatola, ruota, sul_fronte, Manifold

Z0 = 2.4                      # pavimento del vano
PAD = 3.5                     # biadesivo spesso sotto le schede
ZP = Z0 + PAD                 # sotto delle schede
Z_FL = s.Z_DISCO - 2.4        # flangia del motore

def polare(r, gradi, z): return (r * math.cos(math.radians(gradi)), r * math.sin(math.radians(gradi)), z)

# ---------------------------------------------------------------- schede e componenti nel vano
def esp32():          # ESP32 DevKit 30 pin, senza pettini: i fili sono saldati. Presa USB verso il foro dietro
    return (scatola(-77.5, -26.0, -14.15, 14.15, ZP, ZP + 1.6) + scatola(-50.0, -26.0, -9.0, 9.0, ZP + 1.6, ZP + 4.7)
            + scatola(-78.5, -71.0, -3.8, 3.8, ZP + 1.6, ZP + 4.4))

def uln2003():        # scheda driver del motore, 35 x 32: chip, LED e connettore bianco
    x0, y0 = 9.0, -54.0
    return (scatola(x0, x0 + 35, y0, y0 + 32, ZP, ZP + 1.6) + scatola(x0 + 10, x0 + 30, y0 + 6, y0 + 26, ZP + 1.6, ZP + 6)
            + scatola(x0, x0 + 6, y0 + 9, y0 + 23, ZP + 1.6, ZP + 9.5))

def hx711():          # amplificatore della cella di carico, 34 x 21
    return scatola(26.0, 60.0, 16.0, 37.0, ZP, ZP + 1.6) + scatola(36.0, 46.0, 22.0, 31.0, ZP + 1.6, ZP + 3.2)

def mosfet():         # modulo MOSFET per il motorino vibrante, 20 x 15
    return scatola(50.0, 70.0, -15.0, 0.0, ZP, ZP + 1.6) + scatola(55.0, 65.0, -12.0, -3.0, ZP + 1.6, ZP + 6.0)

CICALINO = polare(71.0, 121.0, 0)
def cicalino():       # cicalino attivo 12 x 9,5, vicino alla griglia sul fianco
    return cil(6.0, Z0, Z0 + 9.5, CICALINO[0], CICALINO[1])

def hall_zero():      # sensore A3144 sotto il mozzo (posizione zero del carosello)
    hx, hy = s.HALL_ZERO
    return scatola(hx - 2.0, hx + 2.0, hy - 1.5, hy + 1.5, s.Z_DISCO - 1.5, s.Z_DISCO - 0.1)

def magnete_zero():   # magnete 4 x 2 nel mozzo: gira con il carosello
    hx, hy = s.HALL_ZERO
    return cil(2.0, s.Z_MOZZO0 + 0.1, s.Z_MOZZO0 + 2.1, hx, hy)

def hall_sportello(): # sensore A3144 nella torretta accanto al varco: sente se lo sportello e' chiuso
    return ruota(scatola(s.R_EST + 0.15, s.R_EST + 1.65, -2.0, 2.0, s.Z_TOP - 3.4, s.Z_TOP - 0.4), s.HALL_SP["ang"])

def magnete_sportello():   # magnete 6 x 3 nell'ala dello sportello (si muove con lo sportello)
    a = s.HALL_SP["ang"]; xm, ym = (s.R_EST + 0.8) * math.cos(math.radians(a)), (s.R_EST + 0.8) * math.sin(math.radians(a))
    return cil(3.0, s.Z_TOP + 0.2, s.Z_TOP + 3.2, xm, ym)

def motore():         # 28BYJ-48: corpo, alette, scatolina dei fili, albero
    x = s.MOTORE_X
    m = s.ingombro_motore()
    m += scatola(x - 3.5, x + 3.5, -17.5, 17.5, Z_FL - 0.8, Z_FL) + cil(3.5, Z_FL - 0.8, Z_FL, x, -17.5) + cil(3.5, Z_FL - 0.8, Z_FL, x, 17.5)
    m += scatola(x - 17.3, x - 10.0, -7.3, 7.3, Z_FL - 17.0, Z_FL - 0.8)
    return m

COMPONENTI = {   # nome: (forma, colore, nome da mostrare, a quale pezzo e' attaccato)
    "esp32": (esp32, "#24408e", "Scheda ESP32", "1_base"),
    "uln2003": (uln2003, "#2e7d4f", "Driver del motore (ULN2003)", "1_base"),
    "hx711": (hx711, "#3a8f5c", "Amplificatore della bilancia (HX711)", "1_base"),
    "mosfet": (mosfet, "#5a6b2e", "Modulo MOSFET del motorino vibrante", "1_base"),
    "cicalino": (cicalino, "#1b1d21", "Cicalino", "1_base"),
    "motore": (motore, "#b7bcc4", "Motore passo-passo 28BYJ-48", "2_fondo_a_rampa"),
    "cella": (s.ingombro_cella, "#d6dade", "Cella di carico da 100 g", "2_fondo_a_rampa"),
    "vibro": (s.ingombro_vibro, "#9aa1aa", "Motorino vibrante", "3_piastra_pesata"),
    "hall_zero": (hall_zero, "#15171a", "Sensori di Hall (2)", "2_fondo_a_rampa"),
    "hall_sportello": (hall_sportello, "#15171a", "Sensori di Hall (2)", "1_base"),
    "magnete_zero": (magnete_zero, "#8a8f98", "Magneti (2)", "4_mozzo"),
    "magnete_sportello": (magnete_sportello, "#8a8f98", "Magneti (2)", "8_sportello"),
    "interruttore": (s.ingombro_interruttore, "#202327", "Interruttore e presa USB-C", "10_guscio"),
    "luci": (s.ingombro_luci, "#f2f2ee", "Barra di 8 LED", "10_guscio"),
}

# ---------------------------------------------------------------- viti e perni
NUCLEO = False   # True nei controlli: il gambo e' grande come il nucleo del filetto (le autofilettanti tagliano il foro pilota)
def vite(p, asse, lung, testa_r, testa_h, svasata=False, d=3.0):
    """Vite con la testa che appoggia nel punto p e il gambo lungo 'lung' verso 'asse' (vettore unitario x/y/z con segno)."""
    x, y, z = p
    (ax, sg) = asse
    if svasata:
        t = Manifold.cylinder(testa_h, d / 2, testa_r, 32)          # cono: largo verso fuori
    else:
        t = Manifold.cylinder(testa_h, testa_r, testa_r, 32)
    rg = d * 0.39 if NUCLEO else d / 2 * 0.95
    g = Manifold.cylinder(lung - (testa_h if svasata else 0), rg, rg, 24)
    # costruita lungo +Z con la testa sotto (z da -testa_h a 0) e il gambo verso -Z, poi girata
    if svasata: v = t.translate([0, 0, -testa_h]) + g.translate([0, 0, -lung])
    else: v = t + g.translate([0, 0, -lung])
    if ax == "z": v = v if sg < 0 else v.rotate([180, 0, 0])
    if ax == "x": v = v.rotate([0, -90, 0]) if sg > 0 else v.rotate([0, 90, 0])
    if ax == "y": v = v.rotate([90, 0, 0]) if sg > 0 else v.rotate([-90, 0, 0])
    return v.translate([x, y, z])

def dado(p, h=2.4):
    x, y, z = p
    return Manifold.cylinder(h, 3.15, 3.15, 6).translate([x, y, z - h])

def viti():
    v = {}
    # fondo sulla base: 4 x M3x14, testa cilindrica, dall'alto
    v["fondo"] = sum((vite(polare(s.R_VITI, a, s.Z_APPOGGIO + 1.6), ("z", -1), 14, 2.75, 3.0) for a in s.ANGOLI_VITI), Manifold())
    # motore: 2 x M3x8 svasate a filo del disco + 2 dadi sotto le alette
    v["motore"] = sum((vite((s.MOTORE_X, y, s.Z_DISCO), ("z", -1), 8, 2.9, 1.7, svasata=True) + dado((s.MOTORE_X, y, Z_FL - 0.8))
                       for y in s.VITI_MOTORE_Y), Manifold())
    # cella, lato fisso: 2 x M3x8 da sotto il fondo
    v["cella_fissa"] = sum((vite((x, 0, s.Z_APPOGGIO + 0.2), ("z", 1), 8, 2.75, 3.0) for x in s.FORI_CELLA_FISSO), Manifold())
    # piastra sulla cella: 2 x M3x6 a testa bassa, sotto i tappini
    v["piastra"] = sum((vite((x, 0, s.z_fondo(0, x) - s.PROF_SVASO), ("z", -1), 6, 2.75, 2.0) for x in s.FORI_CELLA_LIBERO), Manifold())
    # scivolo sulla base: 4 x M3x10 da fuori
    v["scivolo"] = sum((vite((s.R_EST + 1.6, y, z), ("x", -1), 10, 2.75, 3.0) for y in (-s.Y_VITI_SC, s.Y_VITI_SC) for z in s.Z_VITI_SC), Manifold())
    # servo sulla culla: 2 x M2x8 (sono nel sacchetto del servo)
    sx, sz = s.SERVO["x"], s.SERVO["z"]
    v["servo"] = sum((vite((x, -27.4, sz), ("y", -1), 8, 1.9, 1.3, d=2.0) for x in (sx - 18.9, sx + 8.2)), Manifold())
    # presa USB-C sul fianco: 2 x M2x6 da fuori
    i = s.INTERRUTTORE
    v["usb"] = sum((vite((i["x_usb"] + dx, s.R_G, i["z"]), ("y", -1), 6, 1.9, 1.2, d=2.0) for dx in (-7.5, 7.5)), Manifold())
    return v

def vite_leva():      # vite della squadretta del servo: gira con la leva
    sx, sz = s.SERVO["x"], s.SERVO["z"]
    return vite((sx, -16.5, sz), ("y", -1), 4, 1.9, 1.2, d=2.0)

def perno_sportello():   # perno da 2 mm (un pezzo di filamento) della cerniera dello sportello
    c = s.CERN; return cil_y(0.95, -s.Y_SP + 0.3, s.Y_SP - 0.3, c["x"], c["z"])

def perno_cofanetto():
    c = s.CERN_C; return cil_y(0.95, -21.7, 21.7, c["x"], c["z"])

# ---------------------------------------------------------------- cavi
def _fronte(xl, a, b):
    """Un punto sulla fascia davanti (coordinate della fascia) -> coordinate vere."""
    t = math.radians(s.INCL)
    return (s.FX + xl * math.cos(t) - b * math.sin(t), a, s.FZ + xl * math.sin(t) + b * math.cos(t))

def _esp(x, lato, dz=0.0): return (x, lato * 15.6, ZP + 2.6 + dz)

FORO_D = lambda r, z: polare(r, -40, z)     # passaggio dei fili davanti a destra (verso display e servo)
FORO_S = lambda r, z: polare(r, 40, z)      # davanti a sinistra (tasto, luci, sensore dello sportello)
FORO_A = lambda r, z: polare(r, 75, z)      # fianco (interruttore)

CAVI = {   # nome: (colore, raggio del fascio, punti, componenti toccati alle estremita')
    "motore": ("#2f6fd0", 1.3, [(-25.8, 0, 18.5), (-27.5, -4, 15.5), (-22, -22, 15.0), (-2, -30, 15.0), (8.5, -38, ZP + 6.0)], ["motore", "uln2003"]),
    "uln2003": ("#d8a020", 1.2, [(11, -26, ZP + 5.0), (-5, -20, 13.0), (-32, -16, ZP + 3.4), _esp(-36, -1)], ["uln2003", "esp32"]),
    "cella": ("#c0392b", 1.0, [(41.0, 1.8, 27.4), (41.0, 1.8, 21.0), (41.0, 8, 16.0), (42.0, 15.0, ZP + 3.4)], ["cella", "hx711"]),
    "hx711": ("#8e44ad", 1.0, [(30.0, 17.0, ZP + 3.0), (10, 15, 12.0), (-20, 17, 12.0), _esp(-44, 1)], ["hx711", "esp32"]),
    "vibro": ("#e67e22", 0.45, [(s.VIBRO["r"] - 3.6, 0, s.z_fondo(0, 70.4) - 3.6), (70.3, 0, 30.5), (70.3, -6.5, 28.6), (41.5, -6.5, 28.6), (41.5, -6.5, 26.7),
                                       (41.0, -2.0, 26.7), (41.0, -2.0, 21.0), (50.5, -6.0, ZP + 3.6)], ["vibro", "mosfet", "cella"]),
    "mosfet": ("#16a085", 1.0, [(50.0, -10.0, ZP + 3.2), (20, -12, 11.0), (-15, -18, 11.0), _esp(-52, -1)], ["mosfet", "esp32"]),
    "hall_zero": ("#7f8c8d", 0.8, [(10.0, 0.0, s.Z_DISCO - 1.5), (10.0, 0.0, 21.5), (4.0, 18.0, 19.5), (-20.0, 19.0, 13.0), _esp(-58, 1)], ["hall_zero", "esp32"]),
    "cicalino": ("#2c3e50", 0.8, [(CICALINO[0], CICALINO[1], Z0 + 9.6), (-36.0, 50.0, 10.0), _esp(-50, 1)], ["cicalino", "esp32"]),
    "servo": ("#c0392b", 1.2, [(16.5, -34.0, 69.0), (16.5, -36.0, 72.5), (48.0, -60.0, 70.0), (66.0, -67.0, 46.0), FORO_D(90.0, 14.0), FORO_D(74.0, 13.5),
                               (50.0, -42.0, 21.5), (-17.0, -26.0, 21.5), (-36.0, -19.0, 12.0), _esp(-40, -1, 0.2)], ["servo", "esp32"]),
    "display": ("#2471a3", 1.2, [_fronte(-7.2, -28.0, -4.0), (118.0, -36.0, 62.0), (84.0, -66.0, 42.0), FORO_D(90.0, 17.5), FORO_D(74.0, 17.0),
                                 (52.0, -45.5, 22.2), (-15.0, -29.0, 21.8), (-40.0, -20.5, 14.0), _esp(-46, -1, 0.2)], ["display", "esp32"]),
    "tasto": ("#e74c3c", 1.0, [_fronte(-22.5, 28.0, -4.0), (110.0, 40.0, 62.0), (84.0, 64.0, 40.0), FORO_S(90.0, 15.0), FORO_S(74.0, 14.5),
                               (30.0, 40.0, 13.0), (-30.0, 22.0, 12.5), _esp(-70, 1, 0.2)], ["tasto", "esp32"]),
    "luci": ("#27ae60", 1.0, [_fronte(-4.2, 0.0, 19.5), (128.0, 0.0, 84.0), (100.0, 0.0, 72.0), (92.0, 40.0, 62.0), (86.0, 67.0, 44.0), FORO_S(90.0, 18.0), FORO_S(74.0, 18.0),
                              (34.0, 44.0, 16.0), (-20.0, 26.0, 16.5), (-48.0, 18.0, 11.5), _esp(-74, 1, 0.2)], ["luci", "esp32"]),
    "hall_sportello": ("#95a5a6", 0.8, [polare(s.R_EST + 0.9, s.HALL_SP["ang"], s.Z_TOP - 3.5), (lambda p: (p[0], p[1], s.Z_TOP - 4.3))(polare(s.R_EST + 0.9, s.HALL_SP["ang"] + 3.4, 0)),
                                        polare(s.R_EST + 3.0, 17.0, 48.0), polare(87.0, 24.0, 36.0), polare(89.0, 34.0, 20.0), FORO_S(90.0, 9.0), FORO_S(74.0, 9.0),
                                        (20.0, 40.0, 9.5), (-26.0, 20.0, 9.0), _esp(-30, 1)], ["hall_sportello", "esp32"]),
    "alimentazione": ("#1c1c1c", 1.2, [(78.5, 79.5, 26.0), (64.0, 79.5, 26.0)], ["interruttore"]),
    "interruttore": ("#b03a2e", 1.2, [(55.0, 72.0, 24.0), (40.0, 78.5, 15.0), FORO_A(84.3, 12.0), FORO_A(72.0, 11.5), (0.0, 50.0, 11.0), (-30.0, 22.0, 9.5), _esp(-56, 1, 0.2)], ["interruttore", "esp32"]),
}

def cavo(r, punti):
    m = Manifold()
    sfere = [Manifold.sphere(r, 16).translate(list(p)) for p in punti]
    for a, b in zip(sfere, sfere[1:]): m += Manifold.batch_hull([a, b])
    return m

# ---------------------------------------------------------------- controlli
if __name__ == "__main__":
    import itertools, trimesh
    NUCLEO = True
    P = {n: f() for n, f in s.PEZZI.items()}
    fissi = ["1_base", "2_fondo_a_rampa", "3_piastra_pesata", "3b_tappini_x2", "4_mozzo", "6_scivolo", "7_coperchio", "8_sportello", "9_leva_servo",
             "10_guscio", "11_cofanetto", "12_bicchierino"]
    P["9_leva_servo"] = s.leva_a(0)
    C = {n: f() for n, (f, *_ ) in COMPONENTI.items()}
    C.update({"servo": s.ingombro_servo(), "display": s.ingombro_display(), "tasto": s.ingombro_tasto()})
    V = viti(); V["leva"] = vite_leva(); V["perno_sportello"] = perno_sportello(); V["perno_cofanetto"] = perno_cofanetto()
    K = {n: cavo(r, pts) for n, (_, r, pts, _t) in CAVI.items()}
    ok = True
    def male(*x):
        global ok; ok = False; print("   ", *x)
    inter = lambda a, b: (a ^ b).volume()
    # cosa sta dentro cosa per progetto (sedi, fori)
    sede = {("vibro", "3_piastra_pesata"), ("cella", "3_piastra_pesata"), ("magnete_zero", "4_mozzo"), ("magnete_sportello", "8_sportello")}
    print("1) componenti contro i pezzi stampati e tra loro")
    for c, m in C.items():
        for n in fissi:
            if (c, n) in sede: continue
            v = inter(m, P[n])
            if v > 0.3: male(c, "contro", n, round(v, 1))
    for a, b in itertools.combinations(C, 2):
        v = inter(C[a], C[b])
        if v > 0.3: male(a, "contro", b, round(v, 1))
    print("2) viti e perni: entrano nei loro fori senza toccare altro")
    vite_in = {"fondo": ["1_base", "2_fondo_a_rampa"], "motore": ["2_fondo_a_rampa"], "cella_fissa": ["2_fondo_a_rampa"], "piastra": ["3_piastra_pesata"],
               "scivolo": ["1_base", "6_scivolo"], "servo": ["7_coperchio"], "usb": ["10_guscio"], "leva": ["9_leva_servo"],
               "perno_sportello": ["7_coperchio", "8_sportello"], "perno_cofanetto": ["10_guscio", "11_cofanetto"]}
    tocca_comp = {"motore": ["motore"], "cella_fissa": ["cella"], "piastra": ["cella"], "servo": ["servo"], "usb": ["interruttore"], "leva": ["servo"]}
    for vn, vm in V.items():
        for n in fissi:
            v = inter(vm, P[n])
            if v > (0.6 if n in vite_in[vn] else 0.05): male("viti", vn, "contro", n, round(v, 2))
        for c, m in C.items():
            if c in tocca_comp.get(vn, []): continue
            v = inter(vm, m)
            if v > 0.05: male("viti", vn, "contro", c, round(v, 2))
    print("3) cavi: passano dai fori e non toccano pezzi, schede o viti")
    for kn, km in K.items():
        for n in fissi:
            v = inter(km, P[n])
            if v > 0.2:
                pts = CAVI[kn][2]; seg = [i for i in range(len(pts) - 1) if inter(cavo(CAVI[kn][1], pts[i:i + 2]), P[n]) > 0.05]
                male("cavo", kn, "contro", n, round(v, 2), "tratti", seg)
        for c, m in C.items():
            if c in CAVI[kn][3]: continue
            v = inter(km, m)
            if v > 0.2:
                pts = CAVI[kn][2]; seg = [i for i in range(len(pts) - 1) if inter(cavo(CAVI[kn][1], pts[i:i + 2]), m) > 0.05]
                male("cavo", kn, "contro", c, round(v, 2), "tratti", seg)
        for vn, vm in V.items():
            v = inter(km, vm)
            if v > 0.05: male("cavo", kn, "contro le viti", vn, round(v, 2))
    print("4) parti che si muovono contro cavi e viti")
    for g in range(0, int(s.APERTO) + 1, 5):
        sp, lv = s.sportello_aperto(g), s.leva_a(s.gradi_servo(g))
        for kn, km in K.items():
            if inter(sp, km) > 0.05 or inter(lv, km) > 0.05: male("sportello/leva a", g, "contro il cavo", kn)
    for g in range(0, 106, 15):
        co = s.cofanetto_aperto(g)
        for kn, km in K.items():
            if inter(co, km) > 0.05: male("cofanetto a", g, "contro il cavo", kn)
    for k in range(6):
        th = k * s.PASSO / 6
        giro = s.ruota(P["4_mozzo"], th)
        for vn in ("motore", "fondo"):
            if inter(giro, V[vn]) > 0.01: male("mozzo che gira contro le viti", vn)
        for j in range(s.N):
            pa = s.paletta_a(th, j)
            for vn in ("motore", "fondo", "piastra"):
                if inter(pa, V[vn]) > 0.01: male("paletta contro le viti", vn); break
    print("TUTTO A POSTO" if ok else "CI SONO PROBLEMI")
    qui = os.path.dirname(os.path.abspath(__file__)); d = os.path.join(qui, "..", "stl", "componenti")
    os.makedirs(d, exist_ok=True)
    for n, m in list(C.items()) + [("viti_e_perni", sum(V.values(), Manifold()))]:
        s.a_mesh(m).export(os.path.join(d, n + ".stl"))
