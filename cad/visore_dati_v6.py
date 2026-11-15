"""Scrive docs/modello-3d/modello_v6.js: i pezzi della v0.6 a due piani per il visore."""
import base64, json, os
import numpy as np
import scatoletta_v6 as s

Q = 0.01
qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "docs", "modello-3d", "modello_v6.js")
def dati(m):
    g = m.to_mesh()
    v = np.round(np.asarray(g.vert_properties)[:, :3] / Q).astype(np.int16); i = np.asarray(g.tri_verts)
    assert i.max() < 65536; return {"v": base64.b64encode(v.tobytes()).decode(), "i": base64.b64encode(i.astype(np.uint16).tobytes()).decode()}
pezzi = {n: dati(f()) for n, f in s.PEZZI.items() if n != "11_cofanetto"}
c = s.CERN_C
pezzi["11_cofanetto"] = dati(s.cofanetto().translate([-c["x"], 0, -c["z"]]))
for n, f in s.COMPONENTI.items(): pezzi[n] = dati(f())
PAR = dict(Q=Q, N=s.N, PASSO=s.PASSO, R_H=s.R_H, R_F=s.R_F, R_E=s.R_E, T=s.T, CONO=s.CONO, Z1=s.Z1, Z2=s.Z2, ZC=s.ZC, W=s.W, CORSA=s.CORSA,
           X_SC0=s.X_SC0, X_SC1=s.X_SC1, SC_ANG=s.SC_ANG, XG=s.NIC["x0"] - 0.3, CUP=s.CUP, COF_X=c["x"], COF_Z=c["z"], XF=s.XF, H_G=s.H_G,
           DISPLAY=s.DISPLAY, PARETE=s.PARETE)
open(out, "w").write("export const PAR=" + json.dumps(PAR) + ";\nexport const PEZZI=" + json.dumps(pezzi) + ";\n")
print("scritto", out, os.path.getsize(out) // 1024, "kB")
