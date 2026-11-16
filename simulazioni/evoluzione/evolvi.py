"""Progettazione evolutiva dello scomparto e dell'uscita.
Geni: apre (mezza larghezza dell'uscita, cm), alfa (angolo degli scivoli, gradi), w (quanto entrano gli scivoli, cm),
T (durata dello scatto della croce, s: piu' lento = motorino a tensione piu' bassa).
Fitness = riuscite - 2 x perdite - 0,6 x volume perso dagli scivoli - 0,05 x secondi in piu' oltre 1 s.
Ogni generazione usa le stesse 12 prove difficili per tutti (confronto giusto), diverse da una generazione all'altra.
Si salva dopo ogni generazione (evoluzione.json) e riparte da li'."""
import json, math, os, random, sys, time
from multiprocessing import Pool
import sim_scomparto as S

LIM = dict(apre=(0.40, 0.95), alfa=(20.0, 70.0), w=(0.0, 0.6), T=(0.6, 1.6))
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evoluzione.json")
PROVE, POP, FIGLI, GEN = 12, 6, 8, 14

def area_persa(g):
    h = g["w"] * math.tan(math.radians(g["alfa"]))
    tasca = (S.R_O ** 2 - S.R_I ** 2) / 2 * math.radians(S.PASSO)
    return min(1.0, 2 * 0.5 * g["w"] * min(h, S.R_O - S.R_I) / tasca)

def _valuta(args):
    g, seme = args
    import pybullet as p
    cid = p.connect(p.DIRECT); rng = random.Random(seme)
    ok = perse = 0
    for _ in range(PROVE):
        t, pe = S.prova(g, rng, cid); ok += t; perse += pe
    p.disconnect(cid)
    succ, leak = ok / PROVE, perse / PROVE
    fit = succ - 2 * leak - 0.6 * area_persa(g) - 0.05 * max(0, g["T"] - 1.0)
    return dict(gen=g, succ=succ, leak=leak, persa=area_persa(g), fit=fit)

def muta(g, rng, scala):
    n = {}
    for k, (a, b) in LIM.items():
        n[k] = min(b, max(a, g[k] + rng.gauss(0, scala * (b - a))))
    return n

def main(tempo_max):
    t0 = time.time()
    st = json.load(open(FILE)) if os.path.exists(FILE) else None
    rng = random.Random(1234)
    if st is None:
        base = dict(apre=0.7, alfa=60.0, w=0.0, T=1.0)                      # il disegno di oggi
        genitori = [base] + [{k: rng.uniform(*LIM[k]) for k in LIM} for _ in range(POP - 1)]
        st = dict(generazioni=[], genitori=genitori, base=None)
    with Pool(2) as pool:
        while len(st["generazioni"]) < GEN and time.time() - t0 < tempo_max:
            g_n = len(st["generazioni"]); rng = random.Random(1000 + g_n)
            scala = 0.25 * (0.85 ** g_n)
            figli = [muta(rng.choice(st["genitori"]), rng, scala) for _ in range(FIGLI)]
            tutti = st["genitori"] + figli
            ris = pool.map(_valuta, [(g, 5000 + g_n) for g in tutti])
            ris.sort(key=lambda r: -r["fit"])
            st["genitori"] = [r["gen"] for r in ris[:POP]]
            base = next((r for r in ris if r["gen"] == dict(apre=0.7, alfa=60.0, w=0.0, T=1.0)), None)
            st["generazioni"].append(dict(migliore=ris[0], media=sum(r["fit"] for r in ris) / len(ris), base=base, tutti=ris))
            json.dump(st, open(FILE, "w"), indent=1)
            m = ris[0]
            print(f"gen {g_n:2d}: migliore fit {m['fit']:.2f} (riuscite {m['succ']:.0%}, perdite {m['leak']:.0%}, volume perso {m['persa']:.0%}) "
                  f"apre {m['gen']['apre'] * 10:.1f} mm, scivoli {m['gen']['alfa']:.0f} gradi x {m['gen']['w'] * 10:.1f} mm, T {m['gen']['T']:.2f} s"
                  + (f" | disegno di oggi: fit {base['fit']:.2f} riuscite {base['succ']:.0%}" if base else ""), flush=True)
    print("generazioni fatte:", len(st["generazioni"]), "su", GEN)

if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 520)
