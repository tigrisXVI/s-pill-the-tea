"""Controlli geometrici della v0.6 a due piani."""
import itertools
import scatoletta_v6 as s
P = {n: f() for n, f in s.PEZZI.items()}
C = {n: f() for n, f in s.COMPONENTI.items()}
inter = lambda a, b: (a ^ b).volume()
ok = True
def male(*x):
    global ok; ok = False; print("   ", *x)

fissi = ["1_base", "2_fondo_sotto", "4_fondo_sopra", "6_coperchio", "7_scivolo", "8_sportello_sotto", "9_sportello_sopra",
         "10_guscio", "11_cofanetto", "12_bicchierino", "13_piatto_bilancia", "14_appoggio_cella"]
print("1) pezzi fermi tra loro")
for a, b in itertools.combinations(fissi, 2):
    v = inter(P[a], P[b])
    if v > 0.3: male(a, b, round(v, 1))
print("2) componenti contro i pezzi e tra loro")
sede = {("cella", "13_piatto_bilancia"), ("cella", "14_appoggio_cella"), ("motore", "2_fondo_sotto"), ("motore", "3_carosello_sotto")}   # l'albero del motore entra nel mozzo
for c, m in C.items():
    for n in fissi + ["3_carosello_sotto", "5_carosello_sopra"]:
        v = inter(m, P[n])
        if v > (60.0 if (c, n) in sede else 0.3): male(c, "contro", n, round(v, 1))
for a, b in itertools.combinations(C, 2):
    v = inter(C[a], C[b])
    if v > 0.3: male(a, b, round(v, 1))
print("3) i due caroselli che girano")
for k in range(12):
    th = k * s.PASSO / 12
    cs, cp = s.ruota(P["3_carosello_sotto"], th), s.ruota(P["5_carosello_sopra"], th)
    for n in ["1_base", "2_fondo_sotto", "4_fondo_sopra", "6_coperchio", "7_scivolo", "8_sportello_sotto", "9_sportello_sopra"]:
        for nome, c in (("carosello di sotto", cs), ("carosello di sopra", cp)):
            v = inter(c, P[n])
            if v > 0.2: male(nome, "a", round(th, 1), "gradi contro", n, round(v, 2))
    v = inter(cs, cp)
    if v > 6.0: male("caroselli tra loro (oltre l'innesto)", round(v, 1))
print("4) sportelli che si aprono (0-100%)")
for k in range(0, 11):
    a = k / 10
    for piano, nome in ((0, "sotto"), (1, "sopra")):
        sp = s.sportello(piano, a)
        for n in ["1_base", "7_scivolo", "10_guscio", "2_fondo_sotto", "4_fondo_sopra"]:
            v = inter(sp, P[n])
            if v > 0.2: male("sportello di", nome, "al", int(a * 100), "% contro", n, round(v, 2))
        if inter(sp, C["servi"]) > 0.2: male("sportello di", nome, "contro i servi")
    if inter(s.sportello(0, a), s.sportello(1, 0)) > 0.1 or inter(s.sportello(1, a), s.sportello(0, 0)) > 0.1: male("sportelli tra loro al", a)
print("5) sportelli aperti: il varco e' libero")
for piano, zb in ((0, s.Z1), (1, s.Z2)):
    passo_libero = s.scatola(s.R_I - 1, s.R_E + 4, -s.W + 0.5, s.W - 0.5, zb - 0.5, zb + s.LUCE - 1)
    v = inter(s.sportello(piano, 1.0), passo_libero)
    print("   piano", "di sotto" if piano == 0 else "di sopra", "libero" if v < 0.05 else "CHIUSO (%.1f)" % v)
    if v >= 0.05: ok = False
print("6) cofanetto che si apre (0-115 gradi)")
for g in list(range(0, 106, 15)) + [115]:
    co = s.cofanetto_aperto(g)
    for n in ["10_guscio", "6_coperchio", "1_base"]:
        v = inter(co, P[n])
        if v > 0.2: male("cofanetto a", g, "contro", n, round(v, 1))
print("7) ricarica: coperchio e piano di sopra si sfilano in alto (a cofanetto aperto)")
co = s.cofanetto_aperto(115)
for dz in range(0, 81, 5):
    cop = P["6_coperchio"].translate([0, 0, dz])
    for n in ["1_base", "10_guscio", "5_carosello_sopra", "4_fondo_sopra"]:
        if dz and inter(cop, P[n]) > 0.2: male("coperchio alzato di", dz, "contro", n)
    if inter(cop, co) > 0.2: male("coperchio alzato di", dz, "contro il cofanetto aperto")
    sopra = (P["4_fondo_sopra"] + P["5_carosello_sopra"]).translate([0, 0, dz])
    for n in ["1_base", "10_guscio", "3_carosello_sotto", "7_scivolo", "9_sportello_sopra"]:
        v = inter(sopra, P[n])
        if v > (6.0 if n == "3_carosello_sotto" and dz < 6 else 0.2): male("piano di sopra alzato di", dz, "contro", n, round(v, 1))
    if inter(sopra, co) > 0.2: male("piano di sopra alzato di", dz, "contro il cofanetto aperto")
print("8) il bicchierino si sfila in avanti")
for dx in range(0, 61, 4):
    b = P["12_bicchierino"].translate([dx, 0, 0])
    for n in ["10_guscio", "7_scivolo", "13_piatto_bilancia"]:
        v = inter(b, P[n])
        if v > 0.2: male("bicchierino spostato di", dx, "contro", n, round(v, 1))
print("9) percorso delle pillole")
cu = s.CUP
fine = s.z_sc(s.X_SC1)
print("   lo scivolo finisce a %.1f mm, sopra il bordo basso del bicchierino (%.1f):" % (fine, cu["basso"]), "si" if fine > cu["basso"] + 2 else "NO")
if fine <= cu["basso"] + 2: ok = False
print("   e dentro il bicchierino (interno da x=%.1f):" % (cu["x0"] + cu["parete"]), "si" if s.X_SC1 > cu["x0"] + cu["parete"] + 2 else "NO")
# una compressa grande (spessa 7,5) sullo scivolo passa sotto il gradino del piano di sopra?
alto = s.z_sc(s.X_SC0) + 7.5 + 1.0
print("   sotto il gradino del piano di sopra (%.1f) passa una compressa spessa 7,5 mm (%.1f):" % (s.Z2 - 3.0, alto), "si" if alto < s.Z2 - 3.0 else "NO")
if alto >= s.Z2 - 3.0: ok = False
print("RISULTATO:", "nessuna interferenza" if ok else "DA CORREGGERE")
