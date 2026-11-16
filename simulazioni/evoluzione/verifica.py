"""Verifica finale, con piu' prove: quanto conta la larghezza dell'uscita, e il disegno di oggi contro il migliore trovato.
Stesse prove difficili per tutti (stesso seme). Scrive verifica.json e i grafici in PNG."""
import json, os, random, sys
from multiprocessing import Pool
import sim_scomparto as S

PROVE = int(sys.argv[1]) if len(sys.argv) > 1 else 40
qui = os.path.dirname(os.path.abspath(__file__))

def _valuta(args):
    g, seme = args
    import pybullet as p
    cid = p.connect(p.DIRECT); rng = random.Random(seme); ok = perse = 0
    for _ in range(PROVE):
        t, pe = S.prova(g, rng, cid); ok += t; perse += pe
    p.disconnect(cid)
    return dict(gen=g, succ=ok / PROVE, leak=perse / PROVE)

if __name__ == "__main__":
    evo = json.load(open(os.path.join(qui, "evoluzione.json")))
    best = evo["generazioni"][-1]["migliore"]["gen"]
    larghezze = [0.50, 0.60, 0.70, 0.80, 0.86, 0.95]
    casi = [dict(apre=a, alfa=60.0, w=0.0, T=1.0) for a in larghezze] + [best]
    with Pool(2) as pool: ris = pool.map(_valuta, [(g, 777) for g in casi])
    out = dict(prove=PROVE, larghezze=ris[:-1], migliore=ris[-1])
    json.dump(out, open(os.path.join(qui, "verifica.json"), "w"), indent=1)
    for r in ris: print(f"uscita {r['gen']['apre'] * 20:.1f} mm, T {r['gen']['T']:.2f} s: riuscite {r['succ']:.0%}, perdite {r['leak']:.0%}")
