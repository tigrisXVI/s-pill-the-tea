"""Scrive docs/modello-3d/modello_v8.js: i due modelli della v0.8 ("2m" e "1m") per il visore."""
import base64, json, os
import numpy as np
import scatoletta_v8 as s

Q = 0.01
qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "docs", "modello-3d", "modello_v8.js")

def dati(m):
    g = m.to_mesh()
    v = np.asarray(g.vert_properties)[:, :3]; assert np.abs(v).max() / Q < 32000
    i = np.asarray(g.tri_verts); assert i.max() < 65536
    return {"v": base64.b64encode(np.round(v / Q).astype(np.int16).tobytes()).decode(), "i": base64.b64encode(i.astype(np.uint16).tobytes()).decode()}

# dai controlli (cad/controlli_v8.py): angolo a cui si ribalta, con e senza piastra; capacita' di uno scomparto
STAB = {"2m": dict(lato=47, lato_senza=26, avanti=53, dietro=50, tasca=4.3, peso=643, zavorra=370, cg=47)}

tutto = {}
for k in ("2m",):
    M = s.Modello(k); P = M.pezzi(); C = M.componenti()
    P["5_piattino"] = M.piattino(0)
    pezzi = {}
    for n, m in P.items():
        if n.startswith("10_"): m = m.translate([0, 0, -M.Z_A])            # le ruote girano attorno al loro asse
        pezzi[n] = dati(m)
    for n, m in C.items(): pezzi["c_" + n] = dati(m)
    if M.ruote == 2:
        facce = [dict(lato=-1, y=-(M.Y0 + M.Z_TAS[0]), off=0.0), dict(lato=1, y=M.Y0 + M.Z_TAS[0], off=0.0)]
    else:
        facce = [dict(lato=-1, y=-M.Z_TAS[0], off=0.0), dict(lato=1, y=M.Z_TAS[0], off=s.PASSO / 2)]
    L, W, H = M.misure()
    tutto[k] = dict(PAR=dict(nome=s.MODELLI[k]["nome"], ruote=M.ruote, R_I=M.R_I, R_O=M.R_O, Z_A=M.Z_A, H=H, L=L, W=W, X_HALF=M.X_HALF, Y_SX=M.Y_SX, Y_DX=M.Y_DX,
                                Z_IMB0=M.Z_IMB0, Z_IMBB=M.Z_PIATTO + 7.0, Z_PIATTO=M.Z_PIATTO, PIATTO=M.PIATTO, CERNIERA=M.lato_cerniera(), Z_CUP=M.Z_CUP, CUP=M.CUP,
                                Z_DISP=M.Z_DISP, Y_MID=M.Y_MID, PIEDE=M.PIEDE, PROF=s.PROF, facce=facce, STAB=STAB[k],
                                litri=round(L * W * H / 1e6, 2), ruota_d=round(2 * M.R_CASS)),
                    PEZZI=pezzi)
    print(k, "pezzi", len(pezzi))
open(out, "w").write("export const PASSO=" + json.dumps(s.PASSO) + ", Q=" + json.dumps(Q) + ";\nexport const MODELLI=" + json.dumps(tutto) + ";\n")
print("scritto", os.path.getsize(out) // 1024, "kB")
