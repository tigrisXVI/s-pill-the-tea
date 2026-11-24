import sys, math, json
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cad'))
from spill_v8 import *
M = Modello('2m')
P = M.pezzi()
out = {}
rows = []
for n, m in P.items():
    v = m.volume() / 1000.0  # cm3
    bb = m.bounding_box()
    rows.append((n, round(v, 2), round(v * 1.27, 1), [round(bb[i+3]-bb[i], 1) for i in range(3)]))
rows.sort(key=lambda r: -r[1])
out['parts'] = rows
out['tot_cm3'] = round(sum(r[1] for r in rows), 1)
# compartment geometry
pitch = 360 / N
out['comp'] = dict(R_I=M.R_I, R_O=M.R_O, depth=PROF, w_inner=round(2*math.pi*M.R_I/N - SP_DIV, 2), w_outer=round(2*math.pi*M.R_O/N - SP_DIV, 2), exit_w=2*M.APRE, exit_depth=PROF)
ruota = M.ruota_locale()
# volume of one compartment: annulus sector minus dividers approx
area = math.pi*(M.R_O**2 - M.R_I**2)/N - SP_DIV*(M.R_O-M.R_I)
out['comp']['vol_cm3_gross'] = round(area*PROF/1000, 2)
out['geneva'] = dict(N=N, R_GEN=M.R_GEN, C=round(M.C_GEN,3), R_pin=round(M.R_MAN,3), pin_d=3.0, slot_w=3.6, R_LOCK=R_LOCK, Z_driver=Z_CROCE, Z_pinion=Z_PIGN_G, module=MOD)
out['refill'] = dict(roof_hole=(35.4-28.2, 10.0), tray_inner_x=round((RA['x1']-1.2)-(RA['x0']+1.2),2), tray_y=2*RA['hy'], chute_top_inner=(34.8-30.6, 19.2-7.2), chute_bottom=(10.8, PROF-3.2))
out['axis'] = dict(hole_r=3.3, axis_r=3.0, hub_len=PROF)
out['tray'] = M.PIATTO; out['cup'] = M.CUP
out['funnel_out'] = dict(y=13.0, x=2*(M.APRE+2.0))
out['H'] = round(M.H,1); out['X_HALF']=M.X_HALF; out['Y']=(M.Y_SX, M.Y_DX)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rd_cad.json'), 'w'), indent=1)
print(json.dumps(out, indent=1)[:3500])
