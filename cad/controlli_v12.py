"""Controlli della v1.2 (dalla v1.0): interferenze, croce di Malta, stepper e finecorsa, ricarica, cassette che si sfilano
(vite M2,5), percorso delle pillole, cavi, stampa, robustezza, stabilita'."""
import itertools, math, sys
import scatoletta_v12 as s12
import scatoletta_v10 as s10
from scatoletta_v3 import scatola, cil
import croce_check_v10 as croce_check            # usa s10.ANG_CROCE[M.k]: la v1.2 ci ha messo la sua chiave
import ricarica_check_v10 as ricarica_check
inter = lambda a, b: (a ^ b).volume()

def controlla(k="2m"):
    M = s12.Modello12(k); P = M.pezzi(); C = M.componenti()
    ok = True
    def male(*x):
        nonlocal ok; ok = False; print("   ", *x)
    print(f"===== {k}: {M.nome}")
    print("1) pezzi fermi tra loro")
    tocco = {("5_piattino", "6_staffa_cella")}
    for a, b in itertools.combinations(P, 2):
        v = inter(P[a], P[b])
        lam = "spazzole" in a + b and "cassetta" in a + b and a[-2:] == b[-2:]
        if v > (40.0 if lam else 1.5 if (a, b) in tocco or (b, a) in tocco else 0.3): male(a, b, round(v, 1))
    print("2) componenti")
    sede = {("cella", "6_staffa_cella"), ("cella", "1_guscio"), ("piastra_acciaio", "3_piede"), ("sensore_bicchiere", "3_piede"), ("interruttore", "1_guscio"),
            ("interruttore", "2_cappello"), ("assi_acciaio", "10_ruota_sx"), ("assi_acciaio", "10_ruota_dx"),
            ("motore_1", "2_cappello"), ("motore_2", "2_cappello"), ("viti_motori", "2_cappello"), ("finecorsa_sx", "2_cappello"), ("finecorsa_dx", "2_cappello"),
            ("dadi_cassette", "1_guscio"), ("viti_cassette", "1_guscio"), ("viti_cassette", "9_cassetta_sx"), ("viti_cassette", "9_cassetta_dx"),
            ("esp32", "1_guscio"), ("uln2003_1", "1_guscio"), ("uln2003_2", "1_guscio"), ("hx711", "1_guscio"), ("cicalino", "1_guscio"), ("servo", "1_guscio")}
    for c, m in C.items():
        for n in P:
            v = inter(m, P[n])
            lim = (25.0 if c == "assi_acciaio" else 3.0) if (c, n) in sede else (40.0 if c.startswith("motore") and c.endswith("croce") and n.startswith("10_") else 0.3)
            if v > lim: male(c, "contro", n, round(v, 1))
    ingrana = {("motore_1_pignone", "motore_1_croce"), ("motore_2_pignone", "motore_2_croce")}
    attacco = {("motore_1", "motore_1_pignone"), ("motore_2", "motore_2_pignone")}
    for a, b in itertools.combinations(C, 2):
        v = inter(C[a], C[b])
        lim = 1.0 if (a, b) in ingrana or (b, a) in ingrana else 0.3
        if v > lim: male(a, b, round(v, 1))
    print("3) le ruote girano")
    ruote = [n for n in P if n.startswith("10_")]
    gira = lambda m, g: m.translate([0, 0, -M.Z_A]).rotate([0, g, 0]).translate([0, 0, M.Z_A])
    for g in [i * s10.PASSO / 4 for i in range(9)]:
        for r in ruote:
            rr = gira(P[r], g)
            for n in P:
                if n == r or n.startswith("10_"): continue
                v = inter(rr, P[n])
                if v > (40.0 if "spazzole" in r and n == "9_cassetta" + r[-3:] else 0.3): male(r, "a", g, "gradi contro", n, round(v, 1))
    print("3b) croce di Malta: un giro dell'ingranaggio, uno scomparto; a riposo la ruota e' bloccata")
    ok &= croce_check.controlla(M, P, C, stampa=print)
    print("3c) stepper, pignone e finecorsa: un giro intero dell'ingranaggio della croce")
    fermi = {n: P[n] for n in P if n[:2] not in ("9_", "10")}
    fermi.update({c: C[c] for c in ("motore_1", "motore_2", "viti_motori", "viti_croce", "finecorsa_sx", "finecorsa_dx")})
    for i, lato in enumerate(("sx", "dx")):
        dx, dy = M.centro_croce(i); px, py = M.pos_pignone(i)
        d = math.hypot(px - dx, py - dy)
        print(f"   {lato}: pignone a {d:.2f} mm dalla croce (10 + 24 denti, modulo 1: 17,0 + 0,1 di gioco)")
        if abs(d - 17.1) > 0.01: male("pignone fuori posto", lato)
        premuto, peggio, dove, ingr = [], 0.0, "", 0.0
        for phi in range(0, 360, 4):
            cr = M.croci(phi)[i][0]; pg = M.pignoni(phi)[i][0]
            ingr = max(ingr, inter(cr, pg))
            if inter(cr, C["finecorsa_" + lato]) > 0.01: premuto.append(phi)
            for n, m in fermi.items():
                if n.startswith("finecorsa_" + lato): continue
                for nome_p, pz in (("croce", cr), ("pignone", pg)):
                    if n == "motore_" + str(i + 1) and nome_p == "pignone": continue   # l'albero e' dentro il pignone
                    v = inter(pz, m)
                    if v > peggio: peggio, dove = v, f"{nome_p} contro {n} a {phi} gradi"
        print(f"   {lato}: il perno preme il finecorsa da {min(premuto) if premuto else '-'} a {max(premuto) if premuto else '-'} gradi (la ruota e' bloccata fino a 102); "
              f"denti croce-pignone {ingr:.2f} mm3; urto massimo con il resto {peggio:.2f} mm3 {dove}")
        if not premuto or min(premuto) < 20 or max(premuto) > 100 or 0 in premuto: male("finecorsa", lato, "premuto fuori dal tratto di blocco")
        if peggio > 0.3: male("croce o pignone urtano", dove)
        if ingr > 1.0: male("denti croce-pignone si incastrano", round(ingr, 2))
    print("3d) ricarica dall'alto: lo sportellino inclina il fondo della canaletta fissa")
    ok &= ricarica_check.controlla(M, P, C, stampa=print)
    print("4) le cassette si sfilano di lato (vite M2,5 tolta)")
    for lato in ("sx", "dx"):
        sgn = -1 if lato == "sx" else 1
        nomi = [n for n in P if n.endswith("_" + lato) and n[:2] in ("9_", "10")]
        g0 = sum((P[n] for n in nomi), s10.Manifold())
        for dy in range(5, 101, 5):
            g2 = g0.translate([0, sgn * dy, 0])
            for n in P:
                if n[:2] in ("9_", "10"): continue
                v = inter(g2, P[n])
                if v > 0.3: male("cassetta", lato, "fuori di", dy, "contro", n, round(v, 1))
            for c in C:
                if c in ("gel_silice", "viti_cassette", "assi_acciaio"): continue   # la spina d'acciaio esce con la cassetta
                if inter(g2, C[c]) > 0.3: male("cassetta", lato, "fuori di", dy, "contro", c, round(inter(g2, C[c]), 1))
    print("4b) con la vite avvitata la cassetta non esce")
    for sd, n in ((-1, "sx"), (1, "dx")):
        v = inter(P["9_cassetta_" + n].translate([0, sd * 1.0, 0]), C["viti_cassette"])
        print(f"   {n}: spostata di 1 mm verso fuori, l'aletta tocca la testa della vite per {v:.1f} mm3")
        if v < 1.0: male("la vite non trattiene la cassetta", n)
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
        ya, yb = sorted((sgn * (M.Y0 + M.Z_TAS[0] + 0.5), sgn * (M.Y0 + M.Z_TAS[1] - 0.5)))
        tappo = scatola(-fin, fin, ya, yb, M.Z_A - M.R_O + 0.3, M.Z_A - M.R_O + 5)
        stati = [inter(gira(P[r], g), tappo) / tappo.volume() for g in (0, s10.PASSO / 2, s10.PASSO, 1.5 * s10.PASSO)]
        print(f"   {r}: uscita coperta al " + ", ".join(f"{v * 100:.0f}%" for v in stati) + "  (a 0, 1/2, 1, 1,5 passi)")
        if stati[0] < .9 or stati[2] > .25: male("uscita", r)
    ye = abs(M.Y_PIGN) + s10.PROF + 2.5; zb = M.Z_PIATTO + 8.0
    pend = math.degrees(math.atan2(M.Z_IMB0 - zb, ye - 6.5))
    print(f"   imbuto inclinato di {pend:.0f} gradi"); ok &= pend >= 40
    largh = 2 * (M.R_I + 5.2) * math.sin(math.radians(s10.PASSO / 2)) - s10.SP_DIV
    print(f"   scomparto largo {largh:.1f} mm dove la compressa grande e' larga 10,4"); ok &= largh >= 10.6
    print("8) cavi, alimentazione e Wi-Fi")
    nastro = M.nastro()
    for n in P:
        v = inter(nastro, P[n])
        if v > 0.05: male("nastro dei cavi contro", n, round(v, 2))
    for c2 in C:
        v = inter(nastro, C[c2])
        if v > 0.05: male("nastro dei cavi contro", c2, round(v, 2))
    for nome, col, r, pts, attacchi in M.cavi():
        t = M.tubo(pts, r)
        for n in P:
            v = inter(t, P[n]); lim = 1.5 if (n == "1_guscio" and nome == "sensore del bicchiere") else 0.05
            if v > lim: male("cavo", nome, "contro", n, round(v, 2))
        for c2 in C:
            v = inter(t, C[c2]); lim = 14.0 if c2 in attacchi else 0.05
            if v > lim: male("cavo", nome, "contro", c2, round(v, 2))
        for g in (20, 40, 60):
            if inter(t, M.piattino(g)) > 0.05: male("cavo", nome, "contro il piattino aperto a", g)
        for lato in ("sx", "dx"):
            sgn = -1 if lato == "sx" else 1
            g0 = sum((P[n] for n in P if n.endswith("_" + lato) and n[:2] in ("9_", "10")), s10.Manifold())
            for dy in (10, 40, 80):
                if inter(t, g0.translate([0, sgn * dy, 0])) > 0.05: male("cavo", nome, "contro la cassetta", lato, "che si sfila")
        for i in range(2):
            for phi in range(0, 360, 30):
                if inter(t, M.croci(phi)[i][0]) > 0.05: male("cavo", nome, "contro la croce che gira a", phi)
    ant = M.antenna().bounding_box()
    def dist(b):
        d = [max(0, b[i] - ant[i + 3], ant[i] - b[i + 3]) for i in range(3)]
        return math.sqrt(sum(x * x for x in d))
    metalli = [n for n in C if n.startswith(("motore", "cella", "piastra", "servo", "uln", "cicalino"))]
    dm = min((dist(C[n].bounding_box()), n) for n in metalli)
    print(f"   antenna Wi-Fi: il metallo piu' vicino e' {dm[1]} a {dm[0]:.0f} mm")
    if dm[0] < 10: male("antenna troppo vicina a", dm[1])
    print("   cavi:", ", ".join(c[0] for c in M.cavi()))
    print("9) le pillole piccole non si incastrano (pillola minuscola: 3 mm x 1,6 mm)")
    fessure = [("lamelle - anello", s10.G_LAMELLA), ("divisori - sportellini", 0.2), ("cassetta - bordo dell'imbuto", M.Z_A - M.R_CASS - (M.Z_IMB0 + 0.5)),
               ("bocca dell'imbuto - pareti del piattino", (zb - 1.6) - (M.Z_PIATTO + s10.H_PIATTO)), ("piattino - paratia dietro", 0.6)]
    for nome, g in fessure:
        ok9 = g <= 0.6 + 1e-6 or g >= 4.0
        print(f"   {nome}: {g:.1f} mm {'ok' if ok9 else 'TROPPO'}")
        if not ok9: male("fessura", nome, round(g, 2))
    print("10) stampa 3D: verso di stampa e sbalzi da sostenere")
    tot = 0
    for n, m in P.items():
        parti = {"9_cassetta": 2, "10_spazzole": 15, "10_sportellini": 14, "19_sportello": 2}   # come nella v1.0: lamelle e sportellini sono pezzi staccati
        if len(m.decompose()) != next((v for p, v in parti.items() if n.startswith(p)), 1): male(n, "pezzi staccati:", len(m.decompose()))
        verso, area, st = s10.stampa(s10.a_mesh(m))
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
    F = 50.0 + 4.5; E = 2000.0; PETG_STRATI = 15.0
    A, cx, cy, _, I = props(g.slice(M.Z_NICCHIA - 25).to_polygons())
    poly = np.vstack([np.asarray(q) for q in g.slice(M.Z_NICCHIA - 25).to_polygons()])
    cmax = max(abs(poly[:, 0].max() - cx), abs(poly[:, 0].min() - cx))
    Mf = F * (M.X_TASTO - cx); sig = Mf * cmax / I + F / A
    scr = 3.6 * E * (s10.PARETE / (2 * M.Y_DX)) ** 2
    print(f"   colonna sotto la nicchia: sezione {A:.0f} mm2, sforzo {sig:.1f} MPa (sicurezza x{PETG_STRATI / sig:.0f}), instabilita' della parete a {scr:.1f} MPa (x{scr / sig:.1f})")
    if PETG_STRATI / sig < 4 or scr / sig < 2: male("struttura troppo debole")
    print("7) stabilita'")
    rho = 1.24 * 0.6
    masse = [(m.volume() * rho / 1000, m) for n, m in P.items()]
    peso_comp = {"assi_acciaio": 7, "interruttore": 2, "cella": 12, "servo": 9, "display": 3, "esp32": 3, "hx711": 2, "uln2003_1": 7, "uln2003_2": 7,
                 "sensore_bicchiere": 1, "motore_1": 33, "motore_2": 33, "cicalino": 2, "finecorsa_sx": 1, "finecorsa_dx": 1, "viti_cassette": 1,
                 "dadi_cassette": 1, "viti_motori": 2, "viti_croce": 1, "motore_1_pignone": 1, "motore_2_pignone": 1, "motore_1_croce": 3, "motore_2_croce": 3,
                 "gel_silice": 4, "spina_usb": 5}
    for n, m in C.items():
        g = 7.85 * m.volume() / 1000 if n == "piastra_acciaio" else peso_comp.get(n, 10)
        masse.append((g, m))
    tot = sum(g for g, _ in masse)
    def cg(m):
        b = m.bounding_box(); return ((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2)
    cx = sum(g * cg(m)[0] for g, m in masse) / tot; cy = sum(g * cg(m)[1] for g, m in masse) / tot; cz = sum(g * cg(m)[2] for g, m in masse) / tot
    pd = M.PIEDE
    lato = math.degrees(math.atan2(pd["y"] - abs(cy), cz)); avanti = math.degrees(math.atan2(pd["x1"] - cx, cz)); dietro = math.degrees(math.atan2(cx - pd["x0"], cz))
    print(f"   peso circa {tot:.0f} g (piastra d'acciaio {7.85 * C['piastra_acciaio'].volume() / 1000:.0f} g), baricentro a {cz:.0f} mm d'altezza")
    print(f"   si ribalta di lato solo se inclinata di {lato:.1f} gradi, in avanti {avanti:.1f}, indietro {dietro:.1f} (servono almeno 40)")
    ok &= min(lato, avanti, dietro) >= 40
    x, y, z = M.misure()
    print(f"   misure: corpo {x:.1f} x {y:.1f} x {z:.1f} mm ({x * y * z / 1e6:.2f} litri), piede {pd['x1'] - pd['x0']:.0f} x {2 * pd['y']:.0f} mm")
    print("RISULTATO v1.2:", "tutto verde" if ok else "DA CORREGGERE")
    return ok

if __name__ == "__main__":
    sys.exit(0 if controlla() else 1)
