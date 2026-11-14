"""Scrive docs/modello-3d/modello.js: le forme dei pezzi per il visore 3D nel browser."""
import base64, json, math, os, re
import numpy as np
import scatoletta_v4 as s

qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "docs", "modello-3d", "modello.js")
def dati(m):
    g = m.to_mesh()
    v = np.asarray(g.vert_properties, dtype=np.float32)[:, :3]; i = np.asarray(g.tri_verts, dtype=np.uint32)
    return {"v": base64.b64encode(v.tobytes()).decode(), "i": base64.b64encode(i.tobytes()).decode()}
vecchio = open(out).read()
PAR = json.loads(re.search(r"export const PAR=(\{.*?\});", vecchio, re.S).group(1))     # le misure della v0.3 restano
PAR.update(CERN_X=s.CERN["x"], CERN_Z=s.CERN["z"], SERVO_X=s.SERVO["x"], SERVO_Z=s.SERVO["z"], BRACCIO=s.SERVO["braccio"], APERTO=s.APERTO,
           ANG_CONS=s.ANG_CONS, CX=s.CX, CZ=s.CZ, DISPLAY=s.DISPLAY, TASTO=s.TASTO, LUCI=s.LUCI)
pezzi = {n: dati(f()) for n, f in s.PEZZI.items()}
# lo sportello e la leva sono salvati con il loro perno nell'origine: il visore li fa ruotare
pezzi["8_sportello"] = dati(s.sportello().translate([-s.CERN["x"], 0, -s.CERN["z"]]))
pezzi["9_leva_servo"] = dati(s.leva_servo().translate([-s.SERVO["x"], 0, -s.SERVO["z"]]))
for n, f in (("servo", s.ingombro_servo), ("display", s.ingombro_display), ("tasto", s.ingombro_tasto), ("luci", s.ingombro_luci)): pezzi[n] = dati(f())
open(out, "w").write("export const PAR=" + json.dumps(PAR) + ";\nexport const PEZZI=" + json.dumps(pezzi) + ";\n")
print("scritto", out, os.path.getsize(out) // 1024, "kB")
