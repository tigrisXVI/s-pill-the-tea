"""Controlli geometrici della v0.7 a due ruote."""
import itertools, math
import spill_v7 as s
P = {n: f() for n, f in s.PEZZI.items()}
C = {n: f() for n, f in s.COMPONENTI.items()}
inter = lambda a, b: (a ^ b).volume()
ok = True
def male(*x):
    global ok; ok = False; print("   ", *x)

def gira(m, lato, gradi):
    """Ruota un pezzo della cassetta attorno all'asse delle ruote."""
    return m.translate([0, 0, -s.Z_A]).rotate([0, gradi, 0]).translate([0, 0, s.Z_A])

print("1) pezzi fermi tra loro")
for a, b in itertools.combinations(P, 2):
    v = inter(P[a], P[b])
    if v > 0.3: male(a, b, round(v, 1))
print("2) componenti contro i pezzi e tra loro")
sede = {("motore_sx", "4_ruota_sx"), ("motore_dx", "7_ruota_dx"), ("cella", "10_piatto_bilancia"), ("cella", "1_telaio")}
for c, m in C.items():
    for n in P:
        v = inter(m, P[n])
        if v > (40 if (c, n) in sede else 0.3): male(c, "contro", n, round(v, 1))
for a, b in itertools.combinations(C, 2):
    v = inter(C[a], C[b])
    if v > 0.3: male(a, b, round(v, 1))
print("3) le ruote girano dentro le cassette")
for k in range(13):
    g = k * s.PASSO / 6
    for lato, nr, nc, nk, nm in ((-1, "4_ruota_sx", "3_cassetta_sx", "5_coperchio_sx", "motore_sx"), (1, "7_ruota_dx", "6_cassetta_dx", "8_coperchio_dx", "motore_dx")):
        r = gira(P[nr], lato, g)
        for n in (nc, nk, "1_telaio", "2_imbuto"):
            v = inter(r, P[n])
            if v > 0.2: male("ruota", nr, "a", round(g, 1), "gradi contro", n, round(v, 2))
print("4) le cassette si sfilano di lato (con ruota e coperchio dentro)")
for lato, nomi in ((-1, ("3_cassetta_sx", "4_ruota_sx", "5_coperchio_sx")), (1, ("6_cassetta_dx", "7_ruota_dx", "8_coperchio_dx"))):
    gruppo = sum((P[n] for n in nomi), s.Manifold())
    for dy in range(10, 101, 10):
        g2 = gruppo.translate([0, lato * dy, 0])
        for n in ("1_telaio", "2_imbuto", "9_bicchierino"):
            v = inter(g2, P[n])
            if v > 0.3: male("cassetta", "sinistra" if lato < 0 else "destra", "fuori di", dy, "mm contro", n, round(v, 1))
        m = C["motore_sx" if lato < 0 else "motore_dx"]
        if inter(g2, m) > 0.3: male("cassetta contro il suo motore a", dy, "mm")
print("5) il bicchierino si sfila in avanti")
for dx in range(0, 71, 5):
    b = P["9_bicchierino"].translate([dx, 0, 0])
    for n in ("1_telaio", "2_imbuto", "10_piatto_bilancia"):
        v = inter(b, P[n])
        if v > 0.3: male("bicchierino spostato di", dx, "contro", n, round(v, 1))
print("6) percorso delle pillole")
# a riposo l'uscita e' coperta dallo scomparto chiuso
fin = s.scatola(-s.USCITA + 0.5, s.USCITA - 0.5, -60, 60, s.Z_A - s.R_CASS - 0.2, s.Z_A - s.R_O - 0.2)
for lato, nr in ((-1, "4_ruota_sx"), (1, "7_ruota_dx")):
    ys = sorted((lato * (s.Y_RUOTA + s.FONDO + 0.5), lato * (s.Y_RUOTA + s.H_RUOTA - 0.5)))
    tappo = s.scatola(-s.USCITA + 0.5, s.USCITA - 0.5, ys[0], ys[1], s.Z_A - s.R_O + 0.5, s.Z_A - s.R_O + 6)
    v0 = inter(P[nr], tappo) / tappo.volume()
    v1 = inter(gira(P[nr], lato, s.PASSO), tappo) / tappo.volume()
    print(f"   ruota {'sinistra' if lato < 0 else 'destra'}: sopra l'uscita a riposo e' pieno al {v0 * 100:.0f}%, dopo un passo al {v1 * 100:.0f}% (scomparto aperto)")
    if v0 < 0.9 or v1 > 0.25: ok = False
# pendenza dell'imbuto e bocca sopra il bicchierino
ye = s.Y_IMB
pend = math.degrees(math.atan2(s.Z_IMB0 - s.Z_IMB1, ye - s.Y_BOCCA))
print(f"   imbuto inclinato di {pend:.0f} gradi (serve almeno 40)"); ok &= pend >= 40
c = s.CUP
dentro = (-s.Y_BOCCA > -c["y"] + c["parete"] + 2) and (-(s.USCITA + 3) > c["x0"] + c["parete"] + 1) and (s.USCITA + 3 < c["x1"] - c["parete"] - 1)
print("   la bocca dell'imbuto e' dentro il bicchierino:", "si" if dentro else "NO"); ok &= dentro
print(f"   la bocca e' a {s.Z_IMB1:.1f} mm, il bordo del bicchierino a {s.Z_CUP + c['alt']:.1f}:", "sopra" if s.Z_IMB1 > s.Z_CUP + c["alt"] else "NO"); ok &= s.Z_IMB1 > s.Z_CUP + c["alt"]
# la compressa grande (22 x 10,4 x 7,5) entra in uno scomparto
largh_dentro = 2 * (s.R_I + 5.2) * math.sin(math.radians(s.PASSO / 2)) - s.SP_DIV
largh_fuori = 2 * s.R_O * math.sin(math.radians(s.PASSO / 2)) - s.SP_DIV
print(f"   scomparto: lungo {s.R_O - s.R_I:.0f} mm, largo {largh_dentro:.1f} mm dove la compressa grande e' gia' larga 10,4 e {largh_fuori:.1f} mm fuori, profondo {s.PROF:.0f} mm")
ok &= largh_dentro >= 10.6
print("RISULTATO:", "nessuna interferenza" if ok else "DA CORREGGERE")
