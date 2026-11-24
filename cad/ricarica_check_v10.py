"""Controllo della ricarica dall'alto v1.0 (canaletta stretta, due fondi): chiudendo lo sportellino, il dito abbassa il fondo
di quel lato abbastanza da far scivolare le pillole (almeno 40 gradi, attrito fino a 0,84) ma non tanto da toccare la cassetta;
a sportellini chiusi e aperti i fondi sono liberi (si pesa)."""
import spill_v10 as s8
inter = lambda a, b: (a ^ b).volume()

def inclinazione(M, s, theta, fondi):
    lid = M.sportello_alto(s, theta)
    for a in sorted(fondi, key=abs):
        if a * s <= 0 and inter(fondi[a], lid) < 0.02: return abs(a)
    return None

def controlla(M, P, C, stampa=print, minimo=38, massimo=46):
    ok = True
    fondi = {a: M.vaschetta_alta(a) for a in range(-56, 57, 2)}
    for s, lato in ((-1, "sinistro"), (1, "destro")):
        incl = [(th, inclinazione(M, s, th, fondi)) for th in (0, 5, 10, 15, 20, 25, 28, 30, 32, 34, 36, 38, 40, 45, 50, 60, 70, 80)]
        mx = max((a for _, a in incl if a is not None), default=0)
        stampa(f"   sportello {lato}: chiudendolo il fondo si abbassa fino a {mx} gradi (servono {minimo}-{massimo}); chiuso e aperto il fondo e' libero: "
               + ("si" if incl[0][1] == 0 and incl[-1][1] == 0 else "NO") + "   " + " ".join(f"{t}:{a}" for t, a in incl))
        if not (minimo <= mx <= massimo) or incl[0][1] != 0 or incl[-1][1] != 0 or any(a is None for _, a in incl): ok = False
    peggio, dove = 0.0, ""
    for a in range(-massimo, massimo + 1, 4):
        if a == 0: continue
        for k, v in list(P.items()) + [("c_" + k, v) for k, v in C.items()]:
            if k.startswith(("16_", "19_")): continue
            x = inter(fondi[a], v)
            if x > peggio: peggio, dove = x, f"{k} a {a} gradi"
    stampa(f"   fondi abbassati fino a {massimo} gradi: urto massimo con il resto {peggio:.2f} mm3 {dove}")
    if peggio > 0.05: ok = False
    for th in (45, 80):
        for s in (-1, 1):
            if inter(M.sportello_alto(s, th), P["2_cappello"]) > 0.05: ok = False; stampa("    sportello aperto contro il cappello")
    return ok

if __name__ == "__main__":
    M = s8.Modello("2m"); P = M.pezzi(); C = M.componenti()
    print("RISULTATO ricarica:", "ok" if controlla(M, P, C) else "DA CORREGGERE")
