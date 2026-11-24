"""Controlli geometrici della v0.3: interferenze tra pezzi fermi, carosello in rotazione, sportello in apertura."""
import math, itertools
import spill_v3 as s
P = {n: f() for n, f in s.PEZZI.items()}
fissi = ["1_base", "2_fondo_a_rampa", "3_piastra_pesata", "3b_tappini_x2", "6_scivolo_vaschetta", "7_coperchio", "8_sportello"]
inter = lambda a, b: (a ^ b).volume()
probl = []
print("1) pezzi fermi tra loro (mm3 sovrapposti)")
for a, b in itertools.combinations(fissi, 2):
    if {a, b} == {"3_piastra_pesata", "3b_tappini_x2"}: continue
    v = inter(P[a], P[b])
    if v > 0.3: probl.append((a, b, round(v, 1))); print("   ", a, b, round(v, 1))
extra = {"motore": s.ingombro_motore(), "cella": s.ingombro_cella(), "motorino vibrante": s.ingombro_vibro()}
for en, e in extra.items():
    for n in fissi + ["4_mozzo"]:
        if en == "cella" and n == "3_piastra_pesata": continue
        if en == "motorino vibrante" and n == "3_piastra_pesata": continue
        v = inter(P[n], e)
        if v > 0.3: probl.append((en, n, round(v, 1))); print("   ", en, "contro", n, round(v, 1))
# la piastra non deve toccare il fondo (deve poter pesare e vibrare)
print("2) la piastra libera dal fondo:", "si" if inter(P["3_piastra_pesata"].translate([0, 0, -0.3]), P["2_fondo_a_rampa"]) < 0.05 and inter(P["3_piastra_pesata"].translate([0.3, 0, 0]), P["2_fondo_a_rampa"]) < 0.05 else "NO")
print("3) carosello in rotazione (1 passo in 48 posizioni)")
peg = {}
for k in range(48):
    th = k * s.PASSO / 48
    gir = [("mozzo", s.ruota(P["4_mozzo"], th))] + [("paletta", s.paletta_a(th, j)) for j in range(s.N)]
    for nf in fissi:
        for ng, mg in gir:
            v = inter(P[nf], mg)
            if v > 0.2: peg[(nf, ng)] = max(peg.get((nf, ng), 0), round(v, 2))
    for j in range(1, s.N + 1):
        v = inter(gir[0][1], gir[j][1])
        if v > 0.2: peg[("paletta", "mozzo")] = max(peg.get(("paletta", "mozzo"), 0), round(v, 2))
print("   ", peg or "nessuna interferenza")
print("4) sportello che si apre (0-110 gradi)")
pe = {}
for g in range(0, 111, 5):
    sp = s.sportello_aperto(g)
    for n in ["1_base", "6_scivolo_vaschetta", "7_coperchio", "2_fondo_a_rampa"]:
        v = inter(sp, P[n])
        if v > 0.2: pe.setdefault(n, []).append((g, round(v, 1)))
print("   ", pe or "si apre senza toccare niente")
mx = 0
for k in range(2880):
    a = k * 0.125; d = math.degrees(math.asin(s.SP_PALETTA / 2 / s.R_DISCO))
    mx = max(mx, max(s.quota_giro(a - d), s.quota_giro(a), s.quota_giro(a + d)) + 0.2 - s.quota_giro(a))
print("5) luce massima sotto la paletta: %.2f mm" % mx)
print("6) larghezza di uno scomparto: al mozzo %.1f mm, a 60 mm %.1f mm, al bordo %.1f mm" % tuple(2 * math.pi * r / s.N - s.SP_PALETTA for r in (s.R_DISCO, 60, s.R_FONDO)))
