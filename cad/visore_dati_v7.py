"""Scrive docs/modello-3d/modello_v7.js: i pezzi della v0.7 a due ruote per il visore."""
import base64, json, os
import numpy as np
import scatoletta_v7 as s

Q = 0.01
qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "docs", "modello-3d", "modello_v7.js")
def dati(m):
    g = m.to_mesh()
    v = np.round(np.asarray(g.vert_properties)[:, :3] / Q).astype(np.int16); i = np.asarray(g.tri_verts)
    assert i.max() < 65536; return {"v": base64.b64encode(v.tobytes()).decode(), "i": base64.b64encode(i.astype(np.uint16).tobytes()).decode()}
pezzi = {}
for n, f in s.PEZZI.items():
    m = f()
    if "ruota" in n: m = m.translate([0, 0, -s.Z_A])          # le ruote girano attorno al loro asse
    pezzi[n] = dati(m)
for n, f in s.COMPONENTI.items(): pezzi[n] = dati(f())
PAR = dict(Q=Q, N=s.N, PASSO=s.PASSO, R_I=s.R_I, R_O=s.R_O, ANG_CHIUSO=s.ANG_CHIUSO, Z_A=s.Z_A, Y_RUOTA=s.Y_RUOTA, FONDO=s.FONDO, PROF=s.PROF,
           Z_IMB0=s.Z_IMB0, Z_IMB1=s.Z_IMB1, Y_BOCCA=s.Y_BOCCA, Y_IMB=s.Y_IMB, Z_CUP=s.Z_CUP, CUP=s.CUP, H=s.H, X_HALF=s.X_HALF, Y_FIANCO=s.Y_FIANCO,
           DISPLAY=s.DISPLAY, TASTO=s.TASTO)
open(out, "w").write("export const PAR=" + json.dumps(PAR) + ";\nexport const PEZZI=" + json.dumps(pezzi) + ";\n")
print("scritto", os.path.getsize(out) // 1024, "kB")
