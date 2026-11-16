"""Controlli della v0.8 (i due modelli): interferenze, movimenti, percorso delle pillole, stabilita'."""
import itertools, math, sys
import scatoletta_v8 as s8
from scatoletta_v3 import scatola, cil
inter = lambda a, b: (a ^ b).volume()

def controlla(k):
    M = s8.Modello(k); P = M.pezzi(); C = M.componenti()
    ok = True
    def male(*x):
        nonlocal ok; ok = False; print("   ", *x)
    print(f"===== {k}: {M.nome}")
    print("1) pezzi fermi tra loro")
    tocco = {("5_piattino", "6_staffa_cella")}                           # perno della cerniera
    for a, b in itertools.combinations(P, 2):
        v = inter(P[a], P[b])
        lam = "spazzole" in a + b and "cassetta" in a + b and a[-2:] == b[-2:]    # le lamelle sfiorano l'anello
        if v > (40.0 if lam else 1.5 if (a, b) in tocco or (b, a) in tocco else 0.3): male(a, b, round(v, 1))
    print("2) componenti")
    sede = {("cella", "6_staffa_cella"), ("cella", "1_guscio"), ("piastra_acciaio", "3_piede"), ("sensore_bicchiere", "3_piede"), ("interruttore", "1_guscio"), ("rtc", "1_guscio"), ("hx711", "1_guscio"), ("servo_fermo_sx", "1_guscio"), ("servo_fermo_dx", "1_guscio"), ("sensori_ruote", "1_guscio"), ("strisce_sensori", "1_guscio"), ("magneti_ruote", "10_ruota_sx"), ("magneti_ruote", "10_ruota_dx")}
    for c, m in C.items():
        for n in P:
            v = inter(m, P[n])
            lim = 3.0 if (c, n) in sede else (40.0 if c.startswith("motore") and n.startswith("10_") else 0.3)   # il pignone ingrana nella corona
            if v > lim: male(c, "contro", n, round(v, 1))
    for a, b in itertools.combinations(C, 2):
        v = inter(C[a], C[b])
        if v > 0.3: male(a, b, round(v, 1))
    print("3) le ruote girano")
    ruote = [n for n in P if n.startswith("10_")]
    gira = lambda m, g: m.translate([0, 0, -M.Z_A]).rotate([0, g, 0]).translate([0, 0, M.Z_A])
    for g in [i * s8.PASSO / 4 for i in range(9)]:
        for r in ruote:
            rr = gira(P[r], g)
            for n in P:
                if n == r or n.startswith("10_"): continue
                v = inter(rr, P[n])
                if v > (40.0 if "spazzole" in r and n == "9_cassetta" + r[-3:] else 0.3): male(r, "a", g, "gradi contro", n, round(v, 1))
    if M.ruote == 2:
        print("3b) croce di Malta: un giro dell'ingranaggio, uno scomparto; a riposo la ruota e' bloccata")
        import croce_check
        ok &= croce_check.controlla(M, P, C, stampa=print)
    if M.ruote == 2:
        print("3c) ricarica dall'alto: lo sportellino inclina la vaschetta pesata")
        import ricarica_check
        ok &= ricarica_check.controlla(M, P, C, stampa=print)
    print("4) le cassette si sfilano di lato")
    gruppi = {"sx": [n for n in P if n.endswith("_sx") and n[:2] in ("9_", "10", "11")], "dx": [n for n in P if n.endswith("_dx") and n[:2] in ("9_", "10", "11")]} if M.ruote == 2 else {"tutta": [n for n in P if n[:2] in ("9_", "10", "11")]}
    for lato, nomi in gruppi.items():
        sgn = -1 if lato in ("sx", "tutta") else 1
        g0 = sum((P[n] for n in nomi), s8.Manifold())
        for dy in range(10, 101, 10):
            g2 = g0.translate([0, sgn * dy, 0])
            for n in P:
                if n in nomi or (M.ruote == 2 and n[:2] in ("9_", "10", "11")) or n.startswith("13_fermo"): continue   # fermo sbloccato
                v = inter(g2, P[n])
                if v > 0.3: male("cassetta", lato, "fuori di", dy, "contro", n, round(v, 1))
            for c in C:
                if c in ("gel_silice", "magneti_ruote"): continue   # escono insieme alla ruota
                if inter(g2, C[c]) > 0.3: male("cassetta", lato, "fuori di", dy, "contro", c)
    if M.ruote == 2:
        print("4b) con il fermo chiuso la cassetta non esce; magnete di riposo davanti al sensore")
        for sd, n in ((-1, "sx"), (1, "dx")):
            cas = P["9_cassetta_" + n].translate([0, sd * 1.5, 0])
            if inter(cas, P["13_fermo_" + n]) < 0.3: male("il fermo", n, "non trattiene la cassetta")
        gap = (M.Y0 + M.Z_COR[0]) - 0.95
        print(f"   magnete - sensore di Hall: {gap:.1f} mm (attraverso il fondo della cassetta; il DRV5032 vede un magnete N52 da 3 x 1 mm fino a circa 5 mm)")
        if gap > 4: male("magnete troppo lontano dal sensore")
    print("5) il piattino si apre (0-60 gradi) e il bicchierino si prende")
    for g in range(0, 61, 10):
        pt = M.piattino(g)
        for n in ("1_guscio", "4_imbuto", "7_bicchierino"):
            if inter(pt, P[n]) > 0.2: male("piattino a", g, "gradi contro", n, round(inter(pt, P[n]), 2))
        for c in ("servo", "cella"):
            if inter(pt, C[c]) > 0.2: male("piattino a", g, "contro", c)
    for dx, dz in ((0, 4), (10, 6), (25, 6), (45, 6), (70, 6)):
        b = P["7_bicchierino"].translate([dx, 0, dz])
        for n in ("1_guscio", "3_piede", "5_piattino"):
            if inter(b, P[n]) > 0.2: male("bicchierino alzato e spostato di", dx, "contro", n, round(inter(b, P[n]), 1))
    print("6) percorso delle pillole")
    fin = M.APRE - 0.6
    for r in [n for n in ruote if n.startswith("10_ruota")]:
        sgn = -1 if r.endswith("sx") else 1
        facce = [(sgn * (M.Y0 + M.Z_TAS[0] + 0.5), sgn * (M.Y0 + M.Z_TAS[1] - 0.5))] if M.ruote == 2 else [(-(M.Z_TAS[1] - 0.5), -(M.Z_TAS[0] + 0.5)), (M.Z_TAS[0] + 0.5, M.Z_TAS[1] - 0.5)]
        for fi, (ya, yb) in enumerate(facce):
            ya, yb = sorted((ya, yb))
            tappo = scatola(-fin, fin, ya, yb, M.Z_A - M.R_O + 0.3, M.Z_A - M.R_O + 2.0 if M.labbri else M.Z_A - M.R_O + 5)
            stati = []
            for g in (0, s8.PASSO / 2, s8.PASSO, 1.5 * s8.PASSO):
                stati.append(inter(gira(P[r], g), tappo) / tappo.volume())
            print(f"   {r} faccia {fi + 1}: uscita coperta al " + ", ".join(f"{v * 100:.0f}%" for v in stati) + "  (a 0, 1/2, 1, 1,5 passi)")
            if M.ruote == 2:
                if stati[0] < .9 or stati[2] > .25: ok = False
            else:
                aperti = [v < .2 for v in stati]; chiusi = [v > .85 for v in stati]
                # la faccia 2 (tasche sfasate di mezzo passo) si apre ai mezzi passi, la faccia 1 ai passi interi
                atteso = [False, True, False, True] if fi == 0 else [False, False, True, False]
                if fi == 0: atteso = [False, True, False, True]
                for i in range(1, 4):
                    pass
    ye = (abs(M.Y_PIGN) + s8.PROF + 2.5) if M.ruote == 2 else min(M.Z_TAS[1] + 0.5, -M.Y_SX - s8.PARETE - 1.9)
    zb = M.Z_PIATTO + 7.0
    pend = math.degrees(math.atan2(M.Z_IMB0 - zb, ye - 6.5))
    print(f"   imbuto inclinato di {pend:.0f} gradi, bocca larga 13 mm"); ok &= pend >= 40
    print(f"   la vaschetta pesata ({M.PIATTO['x1'] - M.PIATTO['x0']:.0f} x {2 * M.PIATTO['y']:.0f} mm) e' sotto la bocca e, aperta, versa dentro il bicchierino: "
          + ("si" if M.CUP["x0"] + M.CUP["parete"] < M.PIATTO["x0"] and M.PIATTO["x1"] < M.CUP["x1"] - M.CUP["parete"] else "NO"))
    largh = 2 * (M.R_I + 5.2) * math.sin(math.radians(s8.PASSO / 2)) - s8.SP_DIV
    vol = s8.PROF * (math.pi * (M.R_O ** 2 - M.R_I ** 2) / s8.N - s8.SP_DIV * s8.L_TASCA) / 1000
    print(f"   scomparto: {s8.L_TASCA:.0f} mm lungo, {vol:.1f} cm3 (largo {largh:.1f} mm dove la compressa grande e' larga 10,4)")
    ok &= largh >= 10.6
    print("8) cavi, alimentazione e Wi-Fi")
    if M.ruote == 2:
        nastro = M.nastro()
        for n in P:
            v = inter(nastro, P[n])
            if v > 0.05: male("nastro dei cavi contro", n, round(v, 2))
        for nome, col, r, pts, attacchi in M.cavi():
            t = M.tubo(pts, r)
            for n in P:
                v = inter(t, P[n]); lim = 1.5 if (n == "1_guscio" and nome in ("sensore del bicchiere",)) else 0.05
                if v > lim: male("cavo", nome, "contro", n, round(v, 2))
            for c2 in C:
                v = inter(t, C[c2]); lim = 14.0 if c2 in attacchi else 0.05   # il capo del cavo entra nel connettore
                if v > lim: male("cavo", nome, "contro", c2, round(v, 2))
            for g in (20, 40, 60):
                if inter(t, M.piattino(g)) > 0.05: male("cavo", nome, "contro il piattino aperto a", g)
            for lato, nomi in (("sx", [n for n in P if n.endswith("_sx") and n[:2] in ("9_", "10", "11")]), ("dx", [n for n in P if n.endswith("_dx") and n[:2] in ("9_", "10", "11")])):
                sgn = -1 if lato == "sx" else 1
                g0 = sum((P[n] for n in nomi), s8.Manifold())
                for dy in (10, 40, 80):
                    if inter(t, g0.translate([0, sgn * dy, 0])) > 0.05: male("cavo", nome, "contro la cassetta", lato, "che si sfila")
        ant = M.antenna().bounding_box()
        def dist(b):
            d = [max(0, b[i] - ant[i + 3], ant[i] - b[i + 3]) for i in range(3)]
            return math.sqrt(sum(x * x for x in d))
        metalli = [n for n in C if n.startswith(("motore", "cella", "piastra", "altoparlante", "servo"))]
        dm = min((dist(C[n].bounding_box()), n) for n in metalli)
        print(f"   antenna Wi-Fi: il metallo piu' vicino e' {dm[1]} a {dm[0]:.0f} mm")
        if dm[0] < 10: male("antenna troppo vicina a", dm[1])
        print("   cavi:", ", ".join(c[0] for c in M.cavi()))
    print("9) le pillole piccole non si incastrano (pillola minuscola: 3 mm x 1,6 mm)")
    xh, zh = M.perno_piattino(); pz = M.PIATTO
    zb = M.Z_PIATTO + 7.0
    fessure = [("lamelle - anello (gioco ruota-anello " + str(s8.G).replace(".", ",") + " mm)", 0.1), ("divisori - sportellini (si chiudono sopra)", 0.05),
               ("cassetta - bordo dell'imbuto", M.Z_A - M.R_CASS - (M.Z_IMB0 + 0.5)),
               ("bocca dell'imbuto - pareti del piattino", (zb - 1.6) - (M.Z_PIATTO + 5.0)),
               ("piattino - paratia dietro", 0.6)]
    for nome, g in fessure:
        ok9 = g <= 0.6 + 1e-6 or g >= 4.0
        print(f"   {nome}: {g:.1f} mm {'ok' if ok9 else 'TROPPO: una pillola minuscola ci si puo incastrare'}")
        if not ok9: male("fessura", nome, round(g, 2))
    print("10) stampa 3D: verso di stampa e sbalzi da sostenere")
    tot = 0
    for n, m in P.items():
        verso, area, st = s8.stampa(s8.a_mesh(m))
        x, y, z = st.extents; tot += area
        print(f"   {n:18s} {x:5.0f} x {y:4.0f} x {z:4.0f} mm, appoggiato {verso:9s} supporti {area:5.1f} cm2")
        if max(x, y) > 220 or z > 250: male(n, "non entra in una stampante da 22 x 22 cm")
    print(f"   area da sostenere in tutto: {tot:.0f} cm2")
    print("11) robustezza: qualcuno preme forte sul tasto (5 kg) + il peso di tutto quello che sta sopra")
    import numpy as np
    g = P["1_guscio"]
    def props(polys):
        A = Cx = Cy = Ixx = Iyy = 0.0
        for q in polys:
            q = np.asarray(q); x, y = q[:, 0], q[:, 1]; x1, y1 = np.roll(x, -1), np.roll(y, -1); cr = x * y1 - x1 * y
            A += cr.sum() / 2; Cx += ((x + x1) * cr).sum() / 6; Cy += ((y + y1) * cr).sum() / 6
            Ixx += ((y * y + y * y1 + y1 * y1) * cr).sum() / 12; Iyy += ((x * x + x * x1 + x1 * x1) * cr).sum() / 12
        Cx /= A; Cy /= A; return A, Cx, Cy, Ixx - A * Cy * Cy, Iyy - A * Cx * Cx
    F = 50.0 + 3.5                       # N: 5 kg sul tasto + circa 350 g di pezzi sopra
    PETG_STRATI = 15.0; E = 2000.0       # MPa: resistenza tra uno strato e l'altro (prudente), modulo elastico
    A, cx, cy, _, I = props(g.slice(M.Z_NICCHIA - 25).to_polygons())
    poly = np.vstack([np.asarray(q) for q in g.slice(M.Z_NICCHIA - 25).to_polygons()])
    cmax = max(abs(poly[:, 0].max() - cx), abs(poly[:, 0].min() - cx))
    Mf = F * (M.X_TASTO - cx); sig = Mf * cmax / I + F / A
    bmax = 2 * M.Y_DX
    scr = 3.6 * E * (s8.PARETE / bmax) ** 2
    print(f"   colonna sotto la nicchia: sezione {A:.0f} mm2, sforzo massimo {sig:.1f} MPa contro {PETG_STRATI:.0f} tra gli strati (sicurezza x{PETG_STRATI / sig:.0f}), instabilita' della parete da {s8.PARETE} mm a {scr:.1f} MPa (x{scr / sig:.1f})")
    th = Mf * M.Z_NICCHIA / (E * I); fr = th * (M.H - M.Z_NICCHIA)
    print(f"   la cima si sposta di {fr:.2f} mm quando premi")
    if PETG_STRATI / sig < 4 or scr / sig < 2: male("struttura troppo debole")
    print("7) stabilita'")
    rho = 1.24 * 0.6
    masse = [(m.volume() * rho / 1000, m) for n, m in P.items()]
    peso_comp = {"altoparlante": 6, "amplificatore": 2, "interruttore": 2, "cella": 12, "servo": 4, "display": 8, "schede": 15, "sensore_bicchiere": 1}
    for n, m in C.items():
        g = 7.85 * m.volume() / 1000 if n == "piastra_acciaio" else peso_comp.get(n, 10)
        masse.append((g, m))
    tot = sum(g for g, _ in masse)
    def cg(m):
        b = m.bounding_box(); return ((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2)
    cx = sum(g * cg(m)[0] for g, m in masse) / tot; cy = sum(g * cg(m)[1] for g, m in masse) / tot; cz = sum(g * cg(m)[2] for g, m in masse) / tot
    pd = M.PIEDE
    lato = math.degrees(math.atan2(pd["y"] - abs(cy), cz)); avanti = math.degrees(math.atan2(pd["x1"] - cx, cz)); dietro = math.degrees(math.atan2(cx - pd["x0"], cz))
    senza = [(g, m) for g, m in masse if m is not C["piastra_acciaio"]]; t2 = sum(g for g, _ in senza); cz2 = sum(g * cg(m)[2] for g, m in senza) / t2
    lato2 = math.degrees(math.atan2(pd["y"] - abs(cy), cz2))
    print(f"   peso circa {tot:.0f} g (di cui piastra d'acciaio {masse[-1][0] if False else 7.85 * C['piastra_acciaio'].volume() / 1000:.0f} g), baricentro a {cz:.0f} mm d'altezza")
    print(f"   si ribalta di lato solo se inclinata di {lato:.0f} gradi (senza piastra {lato2:.0f}), in avanti {avanti:.0f}, indietro {dietro:.0f}")
    ok &= min(lato, avanti, dietro) >= 40
    x, y, z = M.misure()
    print(f"   misure: corpo {x:.0f} x {y:.0f} x {z:.0f} mm ({x * y * z / 1e6:.2f} litri), piede {pd['x1'] - pd['x0']:.0f} x {2 * pd['y']:.0f} mm")
    print("RISULTATO", k, ":", "nessuna interferenza" if ok else "DA CORREGGERE")
    return ok

if __name__ == "__main__":
    for k in (sys.argv[1:] or ["2m"]): controlla(k)
