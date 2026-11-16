"""Controllo della ricarica dall'alto: chiudendo lo sportellino, il dito inclina la vaschetta pesata abbastanza
da far scivolare le pillole; a sportellini chiusi e aperti la vaschetta e' libera (si puo' pesare)."""
import scatoletta_v8 as s8
inter = lambda a, b: (a ^ b).volume()

def inclinazione(M, s, theta, vas):
    """Di quanti gradi il dito dello sportellino (lato s, aperto di theta) costringe a inclinare la vaschetta."""
    lid = M.sportello_alto(s, theta)
    for a in sorted(vas, key=abs):
        if a * s <= 0 and inter(vas[a], lid) < 0.02: return abs(a)
    return None

def controlla(M, P, C, stampa=print):
    ok = True
    vas = {a: M.vaschetta_alta(a) for a in range(-50, 51, 2)}
    for s, lato in ((-1, "sinistro"), (1, "destro")):
        incl = [(th, inclinazione(M, s, th, vas)) for th in (0, 5, 10, 15, 20, 30, 40, 60, 80)]
        mx = max((a for _, a in incl if a is not None), default=0)
        stampa(f"   sportello {lato}: chiudendolo la vaschetta si inclina fino a {mx} gradi; chiuso e aperto la vaschetta e' libera: "
               + ("si" if incl[0][1] == 0 and incl[-1][1] == 0 else "NO"))
        if mx < 28 or incl[0][1] != 0 or incl[-1][1] != 0 or any(a is None for _, a in incl): ok = False
    peggio = 0.0
    for a in (-40, -30, -20, -10, 10, 20, 30, 40):
        for k, v in list(P.items()) + [("c_" + k, v) for k, v in C.items()]:
            if k.startswith(("16_", "19_")): continue
            peggio = max(peggio, inter(vas[a], v))
    stampa(f"   vaschetta inclinata fino a 40 gradi: urto massimo con il resto {peggio:.2f} mm3")
    if peggio > 0.05: ok = False
    for th in (45, 80):
        for s in (-1, 1):
            if inter(M.sportello_alto(s, th), P["2_cappello"]) > 0.05: ok = False; stampa("    sportello aperto contro il cappello")
    return ok

if __name__ == "__main__":
    M = s8.Modello("2m"); P = M.pezzi(); C = M.componenti()
    print("RISULTATO ricarica:", "ok" if controlla(M, P, C) else "DA CORREGGERE")
