"""Scrive docs/modello-3d/modello_v12.js: la v1.2 per il visore."""
import base64, json, os
import numpy as np
import scatoletta_v12 as s12, scatoletta_v10 as s

Q = 0.01
qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "docs", "modello-3d", "modello_v12.js")

def dati(m):
    g = m.to_mesh()
    v = np.asarray(g.vert_properties)[:, :3]; assert np.abs(v).max() / Q < 32000
    i = np.asarray(g.tri_verts); assert i.max() < 65536
    return {"v": base64.b64encode(np.round(v / Q).astype(np.int16).tobytes()).decode(), "i": base64.b64encode(i.astype(np.uint16).tobytes()).decode()}

# dai controlli (cad/controlli_v10.py): angolo a cui si ribalta, con e senza piastra; capacita' di uno scomparto
STAB = {"2m": dict(lato=41, avanti=46, dietro=41, tasca=4.3, peso=767, zavorra=372, cg=64)}   # cad/controlli_v12.py

tutto = {}
for k in ("2m",):
    M = s12.Modello12(k); P = M.pezzi(); C = M.componenti()
    P["5_piattino"] = M.piattino(0)
    pezzi = {}
    ric = {}
    if M.ruote == 2:   # ricarica dall'alto: vaschetta e sportellini girano attorno ai loro perni
        for sd, nn in ((-1, "sx"), (1, "dx")): P["16_fondo_" + nn] = P["16_fondo_" + nn].translate([0, -sd * s12.RA["yp"], -s12.RA["zp"]])
        for sd, nn in ((-1, "sx"), (1, "dx")): P["19_sportello_" + nn] = P["19_sportello_" + nn].translate([0, -sd * s12.RA["yh"], -s12.RA["zh"]])
        tab = [[0, 0], [5, 10], [10, 20], [15, 28], [20, 34], [25, 38], [28, 40], [30, 42], [34, 42], [35, 0], [80, 0]]   # da ricarica_check_v10.py
        ric = dict(zp=s12.RA["zp"], yp=s12.RA["yp"], yh=s12.RA["yh"], zh=s12.RA["zh"], fondi=True, tilt={"-1": tab, "1": tab})
    for n, m in P.items():
        if n.startswith("10_"): m = m.translate([0, 0, -M.Z_A])            # le ruote girano attorno al loro asse
        pezzi[n] = dati(m)
    piv = {}
    for i, (m, cx, cy, cz) in enumerate(M.pignoni()):
        C["motore_" + str(i + 1) + "_pignone"] = m.translate([-cx, -cy, -cz]); piv["c_motore_" + str(i + 1) + "_pignone"] = [cx, cy, cz]
    croci = {}
    if M.ruote == 2:
        import croce_check_v10 as croce_check
        for i, (m, cx, cy, cz) in enumerate(M.croci()):
            C["motore_" + str(i + 1) + "_croce"] = m.translate([-cx, -cy, -cz])
            croci["c_motore_" + str(i + 1) + "_croce"] = dict(pivot=[cx, cy, cz], segno=1 if croce_check.angolo_ruota(M, i, 360) > 0 else -1)
        for n, m in C.items(): pezzi["c_" + n] = dati(m)
    pezzi["nastro_cavi"] = dati(M.nastro())
    if M.ruote == 2:
        facce = [dict(lato=-1, y=-(M.Y0 + M.Z_TAS[0]), off=0.0), dict(lato=1, y=M.Y0 + M.Z_TAS[0], off=0.0)]
    else:
        facce = [dict(lato=-1, y=-M.Z_TAS[0], off=0.0), dict(lato=1, y=M.Z_TAS[0], off=s.PASSO / 2)]
    L, W, H = M.misure()
    tutto[k] = dict(PAR=dict(nome=M.nome, ruote=M.ruote, R_I=M.R_I, R_O=M.R_O, Z_A=M.Z_A, H=H, L=L, W=W, X_HALF=M.X_HALF, Y_SX=M.Y_SX, Y_DX=M.Y_DX,
                                Z_IMB0=M.Z_IMB0, Z_IMBB=M.Z_PIATTO + 8.0, Z_PIATTO=M.Z_PIATTO, PIATTO=M.PIATTO, PERNO=M.perno_piattino(), Z_CUP=M.Z_CUP, CUP=M.CUP,
                                Z_DISP=M.Z_DISP, Y_MID=M.Y_MID, PIEDE=M.PIEDE, PROF=s.PROF, facce=facce, STAB=STAB[k],
                                litri=round(L * W * H / 1e6, 2), ruota_d=round(2 * M.R_CASS),
                                Z_CORONA=M.Z_CORONA, Z_PIGNONE=s.Z_PIGNONE, PIGNONI=piv, CROCI=croci, RICARICA=ric, Z_PIGN_G=getattr(s, 'Z_PIGN_G', 10), Z_CROCE=getattr(s, 'Z_CROCE', 24), Y0=M.Y0, Z_TAS=M.Z_TAS, APRE=M.APRE,
                                CAVI=[dict(nome=n, colore=c, r=r, punti=p, attacchi=a) for n, c, r, p, a in M.cavi()],
                                FERMO={'sx': [0, 0, 0], 'dx': [0, 0, 0]}, TH=M.TH, MOD=s.MOD, R_AN_T=M.R_AN_T, R_GT=M.R_GT, R_CASS=M.R_CASS, Z_COR=M.Z_COR, Z_COP=M.Z_COP, SP_DIV=s.SP_DIV, N=s.N, STAMPA=[[n, *s.stampa(s.a_mesh(m))[:2]] for n, m in M.pezzi().items()]),
                    PEZZI=pezzi)
    print(k, "pezzi", len(pezzi))
open(out, "w").write("export const PASSO=" + json.dumps(s.PASSO) + ", Q=" + json.dumps(Q) + ";\nexport const MODELLI=" + json.dumps(tutto) + ";\n")
print("scritto", os.path.getsize(out) // 1024, "kB")
