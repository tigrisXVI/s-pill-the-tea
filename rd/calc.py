import os
HERE = os.path.dirname(os.path.abspath(__file__))
import math, json, random, statistics as st
random.seed(7)
EMC='https://www.medicines.org.uk/emc/'
# name, shape, L, W, T, T_is_est, source
P=[
 ("Bisoprolol 1.25 mg","round",5.0,5.0,None,EMC+"medicine/43515/spc"),
 ("Bisoprolol 5 mg","round",7.0,7.0,None,EMC+"product/101896/smpc"),
 ("Levothyroxine 25 mcg","round",7.0,7.0,None,EMC+"product/100043/smpc"),
 ("Rivaroxaban 20 mg (A)","round",6.1,6.1,None,EMC+"product/15725/smpc"),
 ("Rivaroxaban 20 mg (B)","round",7.0,7.0,None,EMC+"product/15714/smpc"),
 ("Rivaroxaban 20 mg (C)","round",10.5,10.5,None,EMC+"product/15820/smpc"),
 ("Atorvastatin 40 mg (round)","round",8.5,8.5,None,EMC+"product/12904/smpc"),
 ("Atorvastatin 40 mg (round, 11)","round",11.0,11.0,None,EMC+"product/13505/smpc/print"),
 ("Atorvastatin 40 mg (oval)","oval",14.6,7.3,None,EMC+"product/14006/smpc"),
 ("Atorvastatin 40 mg (oval, 16.9)","oval",16.9,8.1,None,EMC+"product/4344/smpc"),
 ("Apixaban 5 mg","oval",10.0,5.4,4.0,EMC+"product/13690/smpc"),
 ("Co-amoxiclav 250/125 mg","oval",18.1,8.6,None,EMC+"product/11485/smpc"),
 ("Co-amoxiclav 500/125 mg","oval",21.0,10.0,None,EMC+"medicine/21728"),
 ("Metformin 1000 mg (film)","oval",19.0,10.0,None,EMC+"product/101269/smpc"),
 ("Metformin 1000 mg SR","oval",22.0,10.0,8.0,EMC+"medicine/108079/spc"),
 ("Metformin 1000 mg PR","oval",22.6,10.6,None,EMC+"product/102232/smpc"),
 ("Calcium/D3 chewable 17 mm","round",17.0,17.0,None,EMC+"medicine/24306"),
 ("Calcium/D3 chewable 18 mm","round",18.0,18.0,None,EMC+"medicine/40234/spc"),
 ("Placebo mini-tablet","round",2.3,2.3,None,"https://www.researchgate.net/publication/370187382"),
]
CAPS={"000":(26.14,9.91),"00":(23.30,8.53),"0":(21.7,7.65),"1":(19.4,6.91),"2":(18.0,6.35),"3":(15.9,5.82),"4":(14.3,5.31),"5":(11.1,4.91)}
for k,(L,d) in CAPS.items(): P.append((f"Hard capsule size {k}","capsule",L,d,d,"https://cache.erowid.org/archive/rhodium/pdf/gelcap.sizechart.pdf"))
def thick(shape,L,W,T):
    if T: return T,T,False
    if shape=="round": return 0.40*L,0.50*L,True   # biconvex t/d range (hypothesis)
    return 0.50*W,0.75*W,True                       # oval t/w range (hypothesis)
def vol(shape,L,W,t):
    if shape=="capsule": r=W/2; return math.pi*r*r*(L-2*r)+4/3*math.pi*r**3
    if shape=="round": return math.pi/4*L*L*t*0.85
    return math.pi/4*L*W*t*0.85
# openings (mm) from the v0.9 CAD
R_O,R_I,N=47.0,23.0,15
def comp_fits(L,W,t):
    # try orientations: (radial, tangential, axial)
    for a,b,c in [(L,W,t),(L,t,W),(W,L,t),(W,t,L),(t,L,W),(t,W,L)]:
        if a>24 or c>13: continue
        r_in=R_O-a
        w=min(2*math.pi*r_in/N-1.0, 14.8)
        if b<=w: return True
    return False
def passes(s, A, B):  # pill sorted dims s1<=s2<=s3 through rectangle A x B
    a,b=sorted((A,B)); return s[0]<=a and s[1]<=b
rows=[]
for name,shape,L,W,T,src in P:
    tlo,thi,est=thick(shape,L,W,T)
    res={}
    for tt in (tlo,thi):
        s=sorted((L,W,tt))
        r=dict(comp=comp_fits(L,W,tt), exit=passes(s,14,13), funnel=passes(s,13,18),
               roof=passes(s,7.2,10), tray_up=s[0]<=3.5 and s[1]<=10, chute=passes(s,4.2,12))
        for k,v in r.items(): res.setdefault(k,[]).append(v)
    top=all(res['roof'])and all(res['tray_up'])and all(res['chute'])
    top_any=any(a and b and c for a,b,c in zip(res['roof'],res['tray_up'],res['chute']))
    vl=vol(shape,L,W,(tlo+thi)/2)
    rows.append(dict(name=name,shape=shape,L=L,W=W,t=(round(tlo,1),round(thi,1)),t_est=est,vol=round(vl/1000,3),
      comp=all(res['comp']),exit=all(res['exit']),top="yes" if top else ("depends" if top_any else "no"),src=src))
for r in rows: print(f"{r['name']:34s} {r['shape']:7s} L{r['L']:5.1f} W{r['W']:5.1f} t{r['t']} est={r['t_est']} V={r['vol']}cm3 comp={r['comp']} exit={r['exit']} top={r['top']}")
n=len(rows); print('N',n,'exit ok',sum(r['exit'] for r in rows),'comp ok',sum(r['comp'] for r in rows),'top yes',sum(r['top']=='yes' for r in rows),'top depends',sum(r['top']=='depends' for r in rows))
json.dump(rows,open(os.path.join(HERE, 'pills.json'),'w'),indent=1)

# ---------- compartment capacity: example polypharmacy doses
pv={r['name']:r['vol'] for r in rows}
VC=4.26; PACK=(0.45,0.60)  # random packing fraction range (hypothesis)
doses={"Typical evening (5 meds)":["Metformin 1000 mg (film)","Atorvastatin 40 mg (oval)","Apixaban 5 mg","Bisoprolol 5 mg","Levothyroxine 25 mcg"],
       "Heavy (with chewable calcium)":["Metformin 1000 mg PR","Calcium/D3 chewable 18 mm","Co-amoxiclav 500/125 mg","Atorvastatin 40 mg (oval, 16.9)","Apixaban 5 mg"],
       "Light morning (3 small)":["Bisoprolol 1.25 mg","Levothyroxine 25 mcg","Rivaroxaban 20 mg (A)"]}
cap=[]
for k,lst in doses.items():
    v=sum(pv[x] for x in lst); cap.append((k,len(lst),round(v,2),round(v/(VC*PACK[1]),2),round(v/(VC*PACK[0]),2)))
print('capacity',cap)
# tray footprint (flat lying), inner 21.6 x 19.6
fp=lambda r:(math.pi/4*r['L']*r['W'] if r['shape']!='capsule' else r['L']*r['W']*0.95)
FP={r['name']:fp(r) for r in rows}
TRAY=21.6*19.6
tray=[(k,round(sum(FP[x] for x in lst)),round(sum(FP[x] for x in lst)/(TRAY*0.70),2)) for k,lst in doses.items()]
print('tray',tray, 'tray area',TRAY)

# ---------- Geneva drive mechanics
C=50.606; a=10.5215; Rw=49.5
def kin(phi):  # phi: crank angle from the line of centres (0 = deepest), radians
    x=C-a*math.cos(phi); y=a*math.sin(phi); r=math.hypot(x,y); th=math.atan2(y,x)
    # wheel angular velocity ratio dth/dphi
    ratio=(a*(a-C*math.cos(phi)))/(r*r)
    return r,ratio
alpha=math.pi/N  # half engagement on wheel side
phimax=math.pi/2-alpha  # crank half angle of engagement
ratios=[abs(kin(p)[1]) for p in [i/200*phimax for i in range(201)]]
print('geneva crank half-engagement deg',math.degrees(phimax),'max ratio',max(ratios),'dwell deg',360-2*math.degrees(phimax))
# motor torques (Pololu 100:1 6V): LP 0.74 kg.cm, HP 1.7 kg.cm ; generic 0.35 kg.cm
mot={"Generic N20 100:1 (0.35 kg·cm)":0.35*98.07,"Pololu LP 100:1 (0.74 kg·cm)":0.74*98.07,"Pololu HP 100:1 (1.7 kg·cm)":1.7*98.07}
eta=0.9
mech=[]
for k,T in mot.items():
    Td=T*24/10*eta
    Fpin=Td/a                 # worst case: force at full crank lever
    Ft=T/5.0                  # pinion pitch radius 5 mm
    Y=0.201                   # Lewis form factor Z=10 (20 deg full depth, table value)
    sig_tooth=Ft/(2.0*1.0*Y)
    d=3.0; Lb=1.3
    sig_pin=32*Fpin*Lb/(math.pi*d**3)
    Est=1810/(2*(1-0.38**2))
    p0=math.sqrt(Fpin*Est/(math.pi*1.5*2.0))
    mech.append((k,round(T),round(Td),round(Fpin,1),round(Ft,1),round(sig_tooth),round(sig_pin,1),round(p0)))
print('mech',mech)
# normal running torque estimate
m_w=0.0404; m_p=0.020; g=9.81; mu=0.3
Tw=mu*(m_p)*g*R_O + (m_p*g*0.035) + 0.3*(m_w+m_p)*g*3.0
print('wheel resist N.mm',round(Tw,1),'driver torque need',round(Tw*max(ratios),2),'motor torque need',round(Tw*max(ratios)/2.4/eta,2))
# ---------- tolerance stack: wiper gap at the bottom, Monte Carlo
def mc(n=200000):
    gaps=[];touch=0
    for _ in range(n):
        ring=47.3+random.gauss(-0.05,0.075)          # printed ring inner radius (holes print small: bias -0.05)
        tip=47.2+random.gauss(0,0.05)+random.gauss(0,0.03)   # blade length + seating
        hole=3.3+random.gauss(-0.08,0.05); axis=3.0+random.gauss(0,0.04)
        sag=max(0,hole-axis)                          # gravity: wheel hangs on axis
        gap=ring-(tip)-sag                            # gap at the bottom (exit side)
        gaps.append(gap); touch+= gap<0
    gaps.sort(); return round(st.mean(gaps),3),round(gaps[int(.01*n)],3),round(gaps[int(.99*n)],3),round(touch/n,3)
print('wiper gap bottom mean,p1,p99,P(touch)',mc())
def mc_gate(n=200000):
    t=0
    for _ in range(n):
        play=max(0,(1.55+random.gauss(-0.08,0.05))-(1.25+random.gauss(0,0.04)))  # hinge radial play
        g=0.6+random.gauss(0,0.1)+random.gauss(0,0.1)-random.uniform(0,play)    # gate gap
        t+= g<=0
    return round(t/n,4)
print('P(gate touches tray)',mc_gate())
# tilt from axis clearance
c=0.3; L=15.3
tilt=math.degrees(math.atan(2*c/L)); print('tilt deg',round(tilt,2),'axial shift at R49.5',round(49.5*math.tan(math.radians(tilt)),2))
# ---------- load cell / HX711
for vexc in (3.3,4.3):
    fs=1.0e-3*vexc  # 1 mV/V rated output (TAL220 value; TAL221 to confirm)
    perg=fs/100.0
    print('exc',vexc,'uV/g',round(perg*1e6,1),'noise mg rms (G128, 50 nV)',round(50e-9/perg*1000,2))
print('datasheet combined error 0.05%FS =',0.0005*100*1000,'mg; creep 0.05%FS/3min =',0.0005*100*1000,'mg at rated load')
# ---------- thermal
CTE=68e-6
print('PETG wheel radius growth 20->40C mm',round(47*CTE*20,3))
print('steel vs PETG foot mismatch 104 mm, -10..+50C mm',round(104*(68-12)*1e-6*60,3))
# ---------- humidity: desiccant vs air exchange (hypothesis)
Vair=0.12*0.11*0.20*0.5  # m3, half of envelope is air (hypothesis)
abs_h=23.0*0.6           # g/m3 at 25 C 60% RH
for ach in (0.05,0.5,2.0):
    water_day=Vair*abs_h*ach*24
    print('ACH',ach,'water in g/day',round(water_day,3),'days to load 2x2 g silica at 25%',round(2*2*0.25/water_day,1))
# ---------- material use / print time estimate
parts=json.load(open(os.path.join(HERE, 'rd_cad.json')))['parts']
tot=sum(p[1] for p in parts); print('PETG cm3',round(tot,1),'g',round(tot*1.27),'time h at 12 mm3/s',round(tot*1000/12/3600,1))
json.dump(dict(cap=cap,tray=tray,mech=mech),open(os.path.join(HERE, 'calc.json'),'w'))
