"""Controlli geometrici della v0.5 (cofanetto)."""
import itertools
import scatoletta_v5 as s
P = {n: f() for n, f in s.PEZZI.items()}
fissi = ["1_base", "2_fondo_a_rampa", "3_piastra_pesata", "3b_tappini_x2", "6_scivolo", "7_coperchio", "8_sportello", "10_guscio", "11_cofanetto", "12_bicchierino"]
inter = lambda a, b: (a ^ b).volume()
ok = True
def male(*x):
    global ok; ok = False; print("   ", *x)
print("1) pezzi fermi tra loro")
for a, b in itertools.combinations(fissi, 2):
    if {a, b} == {"3_piastra_pesata", "3b_tappini_x2"}: continue
    v = inter(P[a], P[b])
    if v > 0.3: male(a, b, round(v, 1))
extra = {"motore": s.ingombro_motore(), "cella": s.ingombro_cella(), "motorino vibrante": s.ingombro_vibro(), "servo": s.ingombro_servo(),
         "display": s.ingombro_display(), "tasto": s.ingombro_tasto(), "luci": s.ingombro_luci(), "interruttore": s.ingombro_interruttore()}
print("2) componenti contro i pezzi e tra loro")
for en, e in extra.items():
    for n in fissi + ["4_mozzo"]:
        if en in ("cella", "motorino vibrante") and n == "3_piastra_pesata": continue
        v = inter(P[n], e)
        if v > 0.3: male(en, "contro", n, round(v, 1))
for a, b in itertools.combinations(extra, 2):
    v = inter(extra[a], extra[b])
    if v > 0.3: male(a, "contro", b, round(v, 1))
print("3) carosello in rotazione")
for k in range(12):
    th = k * s.PASSO / 12
    gir = [("mozzo", s.ruota(P["4_mozzo"], th))] + [("paletta", s.paletta_a(th, j)) for j in range(s.N)]
    for nf in ["1_base", "2_fondo_a_rampa", "3_piastra_pesata", "6_scivolo", "7_coperchio", "10_guscio"]:
        for ng, mg in gir:
            v = inter(P[nf], mg)
            if v > 0.2: male(nf, ng, round(v, 2))
print("4) sportello alzato dal servo, a cofanetto chiuso (0-%d gradi)" % s.APERTO)
for g in range(0, int(s.APERTO) + 1, 5):
    sp = s.sportello_aperto(g); lv = s.leva_a(s.gradi_servo(g))
    for n in ["1_base", "6_scivolo", "7_coperchio", "2_fondo_a_rampa", "10_guscio", "11_cofanetto"]:
        v = inter(sp, P[n])
        if v > 0.2: male("sportello a", g, "contro", n, round(v, 1))
        if n != "6_scivolo":
            v = inter(lv, P[n])
            if v > 0.2: male("leva a", g, "contro", n, round(v, 1))
    if inter(sp, extra["servo"]) > 0.2: male("sportello contro il servo a", g)
    if inter(lv, sp) > 1.0: male("leva dentro lo sportello a", g)
    if g and inter(s.leva_a(s.gradi_servo(g) + 2.5), sp) < 0.05: male("il perno non tocca la mensola a", g)
print("5) a", s.APERTO, "gradi il varco e' libero per le pillole:", end=" ")
passaggio = s.scatola(s.R_INT - 2, s.R_EST + 6, -s.W_SC, s.W_SC, s.Z_RIPIANO - 1, s.Z_RIPIANO + 12)
v = inter(s.sportello_aperto(s.APERTO), passaggio); print("si" if v < 0.05 else "NO (%.1f mm3)" % v)
if v >= 0.05: ok = False
print("6) cofanetto che si apre (0-105 gradi)")
for g in range(0, 106, 7):
    c = s.cofanetto_aperto(g)
    for n in ["10_guscio", "7_coperchio", "8_sportello"]:
        v = inter(c, P[n])
        if v > 0.2: male("cofanetto a", g, "contro", n, round(v, 1))
    if inter(c, extra["servo"]) > 0.2: male("cofanetto a", g, "contro il servo")
print("7) sportello alzato a mano fino a 100 gradi, a cofanetto aperto")
co = s.cofanetto_aperto(105)
for g in range(0, 101, 10):
    sp = s.sportello_aperto(g)
    for n in ["10_guscio", "1_base", "6_scivolo"]:
        v = inter(sp, P[n])
        if v > 0.2: male("sportello a mano a", g, "contro", n, round(v, 1))
    if inter(sp, co) > 0.2: male("sportello a mano a", g, "contro il cofanetto aperto")
print("8) il bicchierino si sfila in avanti")
for dx in range(0, 61, 4):
    b = P["12_bicchierino"].translate([dx, 0, 0])
    for n in ["10_guscio", "6_scivolo"]:
        v = inter(b, P[n])
        if v > 0.2: male("bicchierino spostato di", dx, "contro", n, round(v, 1))
print("9) lo scivolo finisce sopra l'interno del bicchierino:", end=" ")
b = s.BICCHIERE
dentro = b["x0"] + b["parete"] < s.X_FINE_SC - 1.0
print("si" if dentro else "NO")
if not dentro: ok = False
print("RISULTATO:", "nessuna interferenza" if ok else "DA CORREGGERE")
