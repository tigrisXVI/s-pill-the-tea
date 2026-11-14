"""Controlli geometrici della v0.4: pezzi fermi, componenti nuovi, carosello in rotazione, sportello alzato dal servo."""
import math, itertools
import scatoletta_v4 as s
P = {n: f() for n, f in s.PEZZI.items()}
fissi = ["1_base", "2_fondo_a_rampa", "3_piastra_pesata", "3b_tappini_x2", "6_scivolo_vaschetta", "7_coperchio", "8_sportello"]
inter = lambda a, b: (a ^ b).volume()
ok = True
print("1) pezzi fermi tra loro (mm3 sovrapposti)")
for a, b in itertools.combinations(fissi, 2):
    if {a, b} == {"3_piastra_pesata", "3b_tappini_x2"}: continue
    v = inter(P[a], P[b])
    if v > 0.3: ok = False; print("   ", a, b, round(v, 1))
extra = {"motore": s.ingombro_motore(), "cella": s.ingombro_cella(), "motorino vibrante": s.ingombro_vibro(), "servo": s.ingombro_servo(),
         "display": s.ingombro_display(), "tasto": s.ingombro_tasto(), "barra di luci": s.ingombro_luci()}
print("2) componenti contro i pezzi stampati")
for en, e in extra.items():
    for n in fissi + ["4_mozzo"]:
        if en in ("cella", "motorino vibrante") and n == "3_piastra_pesata": continue
        v = inter(P[n], e)
        if v > 0.3: ok = False; print("   ", en, "contro", n, round(v, 1))
for a, b in itertools.combinations(["display", "tasto", "barra di luci"], 2):
    v = inter(extra[a], extra[b])
    if v > 0.3: ok = False; print("   ", a, "contro", b, round(v, 1))
print("3) carosello in rotazione (1 passo in 24 posizioni)")
for k in range(24):
    th = k * s.PASSO / 24
    gir = [("mozzo", s.ruota(P["4_mozzo"], th))] + [("paletta", s.paletta_a(th, j)) for j in range(s.N)]
    for nf in fissi:
        for ng, mg in gir:
            v = inter(P[nf], mg)
            if v > 0.2: ok = False; print("   ", nf, ng, round(v, 2))
print("4) sportello alzato dal servo (0-%d gradi) e a mano fino a 100" % s.APERTO)
for g in range(0, 101, 5):
    sp = s.sportello_aperto(g)
    for n in ["1_base", "6_scivolo_vaschetta", "7_coperchio", "2_fondo_a_rampa"]:
        v = inter(sp, P[n])
        if v > 0.2: ok = False; print("    sportello a", g, "contro", n, round(v, 1))
    v = inter(sp, extra["servo"])
    if v > 0.2: ok = False; print("    sportello a", g, "contro il servo", round(v, 1))
    if g <= s.APERTO:
        lv = s.leva_a(s.gradi_servo(g))
        for n in ["7_coperchio", "1_base"]:
            v = inter(lv, P[n])
            if v > 0.2: ok = False; print("    leva contro", n, "a", g, round(v, 1))
        v = inter(lv, sp)                        # deve sfiorarlo (il perno spinge), non entrarci
        if v > 1.0: ok = False; print("    leva dentro lo sportello a", g, round(v, 1))
        # il perno tocca davvero la mensola? spostato di 0,4 mm verso l'alto deve entrarci
        if inter(s.leva_a(s.gradi_servo(g) + 2.5), sp) < 0.05: ok = False; print("    il perno non tocca la mensola a", g)
print("5) la leva a riposo lascia chiudere lo sportello:", "si" if inter(s.leva_a(-3), P["8_sportello"]) < 0.05 else "NO")
print("RISULTATO:", "nessuna interferenza" if ok else "DA CORREGGERE")
