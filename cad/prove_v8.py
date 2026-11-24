#!/usr/bin/env python3
"""Pezzi di prova della v0.8, da stampare PRIMA della scatola intera (poche ore invece di un giorno e mezzo).

  prova 1 - spicchio di ruota: un quarto di ruota con 3 scomparti, lamelle di PETG, sportellini, e il pezzo di cassetta
            con l'uscita e l'asse. Serve a vedere se le pillole minuscole passano tra ruota e anello, se lo scomparto
            dopo resta chiuso e quanta forza serve per girare con le lamelle.
  prova 3 - croce di Malta (v0.9): un pezzo di ruota con 4 fessure, l'ingranaggio con perno e disco di blocco, e una base
            con i due perni alla distanza giusta. Giri l'ingranaggio con un dito: a ogni giro la ruota deve avanzare
            di uno scomparto e, tra un giro e l'altro, non si deve poter girare a mano.
  prova 2 - piattino pesato: piattino, staffa e una base che tiene la cella di carico come nella scatola.
            Serve a vedere quanto e' precisa la bilancia con pillole vere (90 mg, 12 mg).
Le STL vanno in v8/2m/prove/, gia' girate nel verso di stampa giusto.
"""
import os, math
import spill_v8 as s8
from spill_v3 import cil, scatola

qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "v8", "2m", "prove"); os.makedirs(out, exist_ok=True)
for f in os.listdir(out): os.remove(os.path.join(out, f))
M = s8.Modello("2m")

def spicchio(m, loc=True):
    """Tiene solo un quarto della ruota attorno all'uscita (da -135 a -45 gradi) piu' il centro (asse e mozzo)."""
    taglio = s8.settore(0.0, 80.0, -135.0, -45.0, -30, 40) + cil(9.0, -30, 40)
    return m ^ taglio

pezzi = {
    "prova1_ruota": spicchio(M.ruota_locale()),
    "prova1_lamelle": spicchio(M.spazzole_locale()),
    "prova1_sportellini": spicchio(M.sportellini_locale()),
    "prova1_cassetta": spicchio(M.cassetta_locale()),
}
# prova 2: piattino e staffa come nella scatola, piu' una base che tiene l'estremita' fissa della cella
P = M.pezzi(); cb = M.cella().bounding_box()
base = scatola(cb[0] - 4, cb[0] + 15, cb[1] - 4, cb[4] + 4, cb[2] - 12, cb[2]) + scatola(cb[0] - 30, cb[0] + 50, cb[1] - 20, cb[4] + 25, cb[2] - 15, cb[2] - 12)
for dx in (4.0, 12.0): base -= cil(1.4, cb[2] - 20, cb[2] + 1, cb[0] + dx, (cb[1] + cb[4]) / 2)   # viti M2,5 della cella
pezzi["prova2_piattino"] = P["5_piattino"]
pezzi["prova2_staffa"] = P["6_staffa_cella"]
pezzi["prova2_base_cella"] = base

# prova 3: croce di Malta
a = s8.ANG_CROCE["2m"][0]; dx, dy = M.C_GEN * math.cos(math.radians(a)), M.C_GEN * math.sin(math.radians(a))
fetta = s8.settore(0.0, 80.0, a - 40, a + 40, -1, 3)
pezzi["prova3_croce_ruota"] = (M.croce_ruota_locale() ^ fetta) + cil(6.0, 0, 2) - cil(3.3, -1, 3)
pezzi["prova3_croce_ingranaggio"] = M.croce_driver_locale(0)
base = s8.settore(0.0, M.C_GEN + 16, a - 40, a + 40, -4.6, -2.6) + cil(8.0, -4.6, -2.6)
base += cil(3.0, -2.61, 2.5) + cil(4.5, -2.61, 0.0)                      # asse della ruota e rondella
base += cil(1.0, -2.61, 1.6, dx, dy) + cil(2.5, -2.61, -2.3, dx, dy)    # perno dell'ingranaggio e rondella
pezzi["prova3_croce_base"] = base

for n, m in pezzi.items():
    verso, area, st = s8.stampa(s8.a_mesh(m)); b = st.bounds
    st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, 0]); st.export(os.path.join(out, n + ".stl"))
    x, y, z = st.extents
    print(f"{n:22s} {x:4.0f} x {y:4.0f} x {z:4.0f} mm  {m.volume() / 1000:5.1f} cm3  appoggiato {verso}, supporti {area:.1f} cm2")
