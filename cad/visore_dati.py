"""Scrive docs/modello-3d/modello.js: le forme dei pezzi per il visore 3D nel browser."""
import base64, json, math, os, re
import numpy as np
import spill_v5 as s

qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "docs", "modello-3d", "modello.js")
Q = 0.01
def dati(m):
    g = m.to_mesh()
    # 16 bit: coordinate in centesimi di mm (errore < 0,005 mm) e indici < 65536 -> file grande la metà
    v = np.round(np.asarray(g.vert_properties)[:, :3] / Q).astype(np.int16); i = np.asarray(g.tri_verts)
    assert i.max() < 65536; i = i.astype(np.uint16)
    return {"v": base64.b64encode(v.tobytes()).decode(), "i": base64.b64encode(i.tobytes()).decode()}
vecchio = open(out).read()
PAR = json.loads(re.search(r"export const PAR=(\{.*?\});", vecchio, re.S).group(1))     # le misure della v0.3 restano
PAR.update(Q=Q, CERN_X=s.CERN["x"], CERN_Z=s.CERN["z"], SERVO_X=s.SERVO["x"], SERVO_Z=s.SERVO["z"], BRACCIO=s.SERVO["braccio"], APERTO=s.APERTO,
           ANG_CONS=0, CX=s.FX, CZ=s.FZ, INCL=s.INCL, DISPLAY=s.DISPLAY, TASTO=s.TASTO, LUCI=s.LUCI, X_FINE_SC=s.X_FINE_SC,
           CUP_X=(s.BICCHIERE["x0"] + s.BICCHIERE["x1"]) / 2, CUP_Z=(s.BICCHIERE["fondo_dietro"] + s.BICCHIERE["fondo_davanti"]) / 2, COF_X=s.CERN_C["x"], COF_Z=s.CERN_C["z"],
           CUP=dict(xm=s.BICCHIERE["x0"], x0=s.BICCHIERE["x0"] + s.BICCHIERE["parete"], x1=s.BICCHIERE["x1"] - s.BICCHIERE["parete"],
                    y=s.BICCHIERE["y"] - s.BICCHIERE["parete"], zb=s.BICCHIERE["fondo_dietro"], zf=s.BICCHIERE["fondo_davanti"], basso=s.BICCHIERE["basso"]))
pezzi = {n: dati(f()) for n, f in s.PEZZI.items()}
# lo sportello e la leva sono salvati con il loro perno nell'origine: il visore li fa ruotare
pezzi["8_sportello"] = dati(s.sportello().translate([-s.CERN["x"], 0, -s.CERN["z"]]))
pezzi["9_leva_servo"] = dati(s.leva_servo().translate([-s.SERVO["x"], 0, -s.SERVO["z"]]))
pezzi["11_cofanetto"] = dati(s.cofanetto().translate([-s.CERN_C["x"], 0, -s.CERN_C["z"]]))
for n, f in (("servo", s.ingombro_servo), ("display", s.ingombro_display), ("tasto", s.ingombro_tasto)): pezzi[n] = dati(f())
# elettronica, viti, perni e cavi: ognuno con il pezzo a cui e' attaccato (per lo smontaggio e i movimenti)
import elettronica_v5 as e
EN = {"esp32": "ESP32 board", "uln2003": "Motor driver (ULN2003)", "hx711": "Scale amplifier (HX711)", "mosfet": "MOSFET module for the vibration motor",
      "cicalino": "Buzzer", "motore": "Stepper motor 28BYJ-48", "cella": "100 g load cell", "vibro": "Vibration motor", "hall_zero": "Hall sensors (2)",
      "hall_sportello": "Hall sensors (2)", "magnete_zero": "Magnets (2)", "magnete_sportello": "Magnets (2)", "interruttore": "Switch and USB-C socket", "luci": "Bar of 8 LEDs"}
elettronica = []
def metti(nome, solido, colore, it, en, gruppo, perno=None):
    pezzi[nome] = dati(solido.translate([-perno[0], 0, -perno[1]]) if perno else solido)
    elettronica.append(dict(id=nome, colore=colore, it=it, en=en, gruppo=gruppo))
pernoSp, pernoLv, pernoCo = (s.CERN["x"], s.CERN["z"]), (s.SERVO["x"], s.SERVO["z"]), (s.CERN_C["x"], s.CERN_C["z"])
for n, (f, col, it, gr) in e.COMPONENTI.items():
    if n == "luci": continue                                          # la barra di luci e' gia' disegnata sulla fascia
    metti(n, f(), col, it, EN[n], gr, pernoSp if gr == "8_sportello" else None)
metti("luci_led", s.ingombro_luci(), "#f2f2ee", "Barra di 8 LED", EN["luci"], "10_guscio")
V = e.viti(); ACC = "#8e949c"
metti("viti_fondo", V["fondo"] + V["motore"] + V["cella_fissa"], ACC, "Viti, dadi e perni", "Screws, nuts and pins", "2_fondo_a_rampa")
metti("viti_piastra", V["piastra"], ACC, "Viti, dadi e perni", "Screws, nuts and pins", "3_piastra_pesata")
metti("viti_base", V["scivolo"] + V["usb"], ACC, "Viti, dadi e perni", "Screws, nuts and pins", "1_base")
metti("viti_servo", V["servo"], ACC, "Viti, dadi e perni", "Screws, nuts and pins", "servo")
metti("vite_leva", e.vite_leva(), ACC, "Viti, dadi e perni", "Screws, nuts and pins", "9_leva_servo", pernoLv)
metti("perno_sportello", e.perno_sportello(), "#d9d4c7", "Viti, dadi e perni", "Screws, nuts and pins", "8_sportello", pernoSp)
metti("perno_cofanetto", e.perno_cofanetto(), "#d9d4c7", "Viti, dadi e perni", "Screws, nuts and pins", "11_cofanetto", pernoCo)
cavi = [dict(id=n, colore=c, r=r, punti=[[round(v, 2) for v in p] for p in pts]) for n, (c, r, pts, _) in e.CAVI.items()]
open(out, "w").write("export const PAR=" + json.dumps(PAR) + ";\nexport const PEZZI=" + json.dumps(pezzi) + ";\nexport const ELETTRONICA=" + json.dumps(elettronica)
                     + ";\nexport const CAVI=" + json.dumps(cavi) + ";\n")
print("scritto", out, os.path.getsize(out) // 1024, "kB")
