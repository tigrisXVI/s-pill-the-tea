"""Controllo della croce di Malta: un giro intero dell'ingranaggio fa avanzare la ruota di uno scomparto, senza urti."""
import math, spill_v8 as s8
inter = lambda a, b: (a ^ b).volume()

def angolo_ruota(M, i, phi):
    """Rotazione della ruota (gradi, nel piano della ruota) quando l'ingranaggio della croce e' girato di phi dal riposo."""
    a = s8.ANG_CROCE[M.k][i]; D = (M.C_GEN * math.cos(math.radians(a)), M.C_GEN * math.sin(math.radians(a)))
    ing = 90.0 - 180.0 / s8.N                       # mezzo angolo di presa
    phi_c = max(180 - ing, min(180 + ing, phi))     # fuori dalla presa la ruota sta ferma
    u = math.radians(a + phi_c); P = (D[0] + M.R_MAN * math.cos(u), D[1] + M.R_MAN * math.sin(u))
    u0 = math.radians(a + 180 - ing); P0 = (D[0] + M.R_MAN * math.cos(u0), D[1] + M.R_MAN * math.sin(u0))
    return math.degrees(math.atan2(P[1], P[0]) - math.atan2(P0[1], P0[0]))

def controlla(M, P, C, passi=(0, 60, 102, 120, 150, 180, 210, 240, 258, 300, 360), stampa=print):
    ok = True
    gira = lambda m, g: m.translate([0, 0, -M.Z_A]).rotate([0, g, 0]).translate([0, 0, M.Z_A])
    for i, lato in enumerate(("sx", "dx")):
        ruota = P["10_ruota_" + lato]; cas = P["9_cassetta_" + lato]
        peggio = 0.0
        for phi in passi:
            dr = M.croci(phi)[i][0]; th = angolo_ruota(M, i, phi)
            v = inter(dr, gira(ruota, -th)); v2 = inter(dr, cas); peggio = max(peggio, v, v2)
            if v > 0.3 or v2 > 0.3:
                ok = False; stampa(f"    croce {lato} a {phi} gradi: urta la ruota ({v:.1f} mm3) o la cassetta ({v2:.1f} mm3)")
        stampa(f"   croce {lato}: un giro dell'ingranaggio = {abs(angolo_ruota(M, i, 360)):.1f} gradi di ruota (uno scomparto = {s8.PASSO:.0f}); urto massimo {peggio:.2f} mm3")
        if abs(abs(angolo_ruota(M, i, 360)) - s8.PASSO) > 0.2: ok = False
        dr = M.croci(0)[i][0]                          # a riposo: se qualcuno spinge la ruota, il disco di blocco la ferma
        blocco = min(inter(dr, gira(ruota, g)) for g in (-3, 3))
        stampa(f"   croce {lato} a riposo: se si prova a girare la ruota di 3 gradi il disco di blocco la ferma ({blocco:.1f} mm3 di contatto)")
        if blocco < 1.0: ok = False
    return ok

if __name__ == "__main__":
    M = s8.Modello("2m"); P = M.pezzi(); C = M.componenti()
    print("RISULTATO croce:", "ok" if controlla(M, P, C, passi=range(0, 361, 6)) else "DA CORREGGERE")
