"""Database compresse ampliato (batch 1 svolto in chat, 17/11/2026).
Spessore: DS quando il foglietto/SmPC lo dichiara; altrimenti HYP con rapporti ricalibrati sui casi DS."""
import os, json, math
from calc_pills_core import comp_fits, passes, vol
HERE=os.path.dirname(os.path.abspath(__file__))
EMC='https://www.medicines.org.uk/emc/'; MPA='https://docetp.mpa.se/LMF/'; CBG='https://www.geneesmiddeleninformatiebank.nl/smpc/'
# name, shape, L, W, T (None=HYP), source   shape: round | flat | chew | oval | capsule
P=[
 # --- spessore dichiarato (DS) ---
 ("Bisoprolol 3.75/7.5 mg (Bausch)","round",8.0,8.0,4.0,MPA+"Bisoprolol%20Bausch%20Health%20film-coated%20tablet%20ENG%20SmPC_09001bee827312ef.pdf"),
 ("Levothyroxine 13-100 mcg (Medithyrox)","round",6.5,6.5,3.5,MPA+"Medithyrox%20tablet%20SmPC_09001bee8140e6bf.pdf"),
 ("Apixaban 5 mg (emc 13690)","oval",10.0,5.4,4.0,EMC+"product/13690/smpc"),
 ("Apixaban 5 mg (Prepixan)","oval",10.0,5.4,4.4,CBG+"h133117_smpc_en.pdf"),
 ("Apixaban 5 mg (Teva, max)","oval",10.5,5.6,4.8,"https://assets.hpra.ie/products/Human/36093/Licence_PA0436-049-002_26052026144142.pdf"),
 ("Metformin 1000 mg (Glucophage)","oval",19.0,10.5,6.4,"https://spc.fimea.fi/indox/english/html/nam/humspc/2/23189272.pdf"),
 ("Metformin 1000 mg SR","oval",22.0,10.0,8.0,EMC+"medicine/108079/spc"),
 # --- solo lunghezza/larghezza dichiarate (spessore HYP) ---
 ("Bisoprolol 1.25 mg","round",5.0,5.0,None,MPA+"Bisoprolol%20Medical%20Valley%20tablet%20ENG%20SmPC_09001bee807a1750.pdf"),
 ("Bisoprolol 2.5 mg","round",7.0,7.0,None,MPA+"Cardovia%20film-coated%20tablet%20ENG%20SmPC_09001bee847e6373.pdf"),
 ("Bisoprolol 10 mg (round)","round",8.0,8.0,None,EMC+"product/14906/smpc"),
 ("Bisoprolol 10 mg (oval)","oval",9.0,7.0,None,EMC+"product/13705/smpc"),
 ("Levothyroxine 25-175 mcg (Striroxin)","round",7.0,7.0,None,MPA+"Striroxin%20tablet%20ENG%20SmPC_09001bee84511527.pdf"),
 ("Levothyroxine 100 mcg (Eltroxin old)","round",8.0,8.0,None,"https://pharmac.govt.nz/assets/Eltroxin-Tablet-Guide-for-HCPs-May-2024.pdf"),
 ("Levothyroxine 100 mcg (Eltroxin new, flat)","flat",6.5,6.5,None,"https://pharmac.govt.nz/assets/Eltroxin-Tablet-Guide-for-HCPs-May-2024.pdf"),
 ("Atorvastatin 10 mg (round)","round",6.0,6.0,None,MPA+"Lipistad%20film-coated%20tablet%20SmPC_09001bee807a59d0.pdf"),
 ("Atorvastatin 20 mg (round)","round",8.0,8.0,None,MPA+"Lipistad%20film-coated%20tablet%20SmPC_09001bee807a59d0.pdf"),
 ("Atorvastatin 40 mg (round)","round",10.0,10.0,None,MPA+"Lipistad%20film-coated%20tablet%20SmPC_09001bee807a59d0.pdf"),
 ("Atorvastatin 80 mg (round)","round",12.0,12.0,None,MPA+"Lipistad%20film-coated%20tablet%20SmPC_09001bee807a59d0.pdf"),
 ("Atorvastatin 10 mg (oval 8.1)","oval",8.1,5.1,None,EMC+"product/14003/smpc"),
 ("Atorvastatin 10 mg (oval 9.8)","oval",9.8,5.2,None,EMC+"product/13672/smpc"),
 ("Atorvastatin 20 mg (Teva)","oval",10.0,6.0,None,"https://assets.hpra.ie/products/Human/39414/Licence_PA1986-125-002_22122025152338.pdf"),
 ("Atorvastatin 30 mg","oval",12.4,6.4,None,EMC+"product/11753/smpc"),
 ("Atorvastatin 80 mg (12.3)","oval",12.3,6.5,None,EMC+"product/7051/smpc"),
 ("Atorvastatin 60 mg","oval",16.0,8.5,None,EMC+"product/14488/smpc"),
 ("Atorvastatin 40 mg (oval, 16.9)","oval",16.9,8.1,None,EMC+"product/4344/smpc"),
 ("Amlodipine 5 mg (Accord)","round",6.6,6.6,None,MPA+"Amlodipin%20Accord%20tablet%20ENG%20SmPC_09001bee807a28c5.pdf"),
 ("Amlodipine 10 mg (Accord)","round",8.5,8.5,None,MPA+"Amlodipin%20Accord%20tablet%20ENG%20SmPC_09001bee807a28c5.pdf"),
 ("Amlodipine 5 mg (Medical Valley)","round",8.83,8.83,None,MPA+"Amlodipin%20Medical%20Valley%20tablet%20ENG%20SmPC_09001bee807a28f3.pdf"),
 ("Amlodipine 10 mg (Medical Valley)","round",10.6,10.6,None,MPA+"Amlodipin%20Medical%20Valley%20tablet%20ENG%20SmPC_09001bee807a28f3.pdf"),
 ("Amlodipine 5/10 mg (Vitabalans)","round",9.0,9.0,None,MPA+"Amlodipine%20Vitabalans%20tablet%20ENG%20SmPC_09001bee807a2918.pdf"),
 ("Amlodipine/valsartan 5/160 mg","oval",13.5,7.0,None,MPA+"Amlodipin_Valsartan%20Teva%20film-coated%20tablet%20ENG%20SmPC_09001bee827efc52.pdf"),
 ("Ramipril 1.25-5 mg (oblong)","oval",8.0,4.0,None,EMC+"product/8064/smpc/print"),
 ("Ramipril 10 mg (oblong)","oval",7.0,4.5,None,EMC+"product/2757/smpc"),
 ("Ramipril 2.5-10 mg (round)","round",7.0,7.0,None,MPA+"Ramiliv%20tablet%20ENG%20SmPC_09001bee83e94ca1.pdf"),
 ("Pantoprazole 20 mg","oval",8.8,4.6,None,EMC+"product/14643/smpc"),
 ("Pantoprazole 40 mg","oval",11.9,6.2,None,MPA+"Pantoprazol%20Orion%20gastro-resistant%20tablet%20ENG%20SmPC_09001bee807a5af4.pdf"),
 ("Allopurinol 100 mg","round",8.0,8.0,None,MPA+"Allopurinol%20Accord%20tablet%20ENG%20SmPC_09001bee84da7190.pdf"),
 ("Allopurinol 300 mg","round",11.2,11.2,None,MPA+"Allopurinol%20Accord%20tablet%20ENG%20SmPC_09001bee84da7190.pdf"),
 ("Furosemide 500 mg (flat)","flat",13.0,13.0,None,"https://products.tevauk.com/media/download/39977"),
 ("Metformin 850 mg","oval",19.0,9.0,None,EMC+"product/10760/smpc"),
 ("Metformin 1000 mg (19x10)","oval",19.0,10.0,None,EMC+"product/101269/smpc"),
 ("Metformin 1000 mg (Accord)","oval",19.0,10.8,None,"https://fass.se/health/product/20200601000070/stock-status"),
 ("Metformin 1000 mg PR (21.1)","oval",21.1,10.1,None,EMC+"medicine/42623/spc"),
 ("Metformin 1000 mg PR (22.6)","oval",22.6,10.6,None,EMC+"product/102232/smpc"),
 ("Amoxicillin 500 mg","oval",16.5,8.0,None,EMC+"medicine/103426/spc"),
 ("Co-amoxiclav 500/125 mg","oval",20.2,9.8,None,"https://assets.hpra.ie/products/Human/30797/Licence_PA2315-001-001_23022023084313.pdf"),
 ("Co-amoxiclav 875/125 mg","oval",22.0,10.0,None,CBG+"h122310_smpc_en.pdf"),
 ("Calcium/Mg chewable 13 mm (flat)","flat",13.0,13.0,None,"https://fass.se/product/20200527000086/pl"),
 ("Calcium/D3 chewable 14 mm","chew",14.0,14.0,None,"https://fass.se/product/20010629000118/stock-status"),
 ("Calcium/D3 chewable 17 mm","chew",17.0,17.0,None,EMC+"medicine/24306"),
 ("Calcium 1 g chewable 18 mm","chew",18.0,18.0,None,"https://fass.se/health/product/19970425000139/stock-status"),
]
CAPS={"000":(26.14,9.91),"00":(23.30,8.53),"0":(21.7,7.65),"1":(19.4,6.91),"2":(18.0,6.35),"3":(15.9,5.82),"4":(14.3,5.31),"5":(11.1,4.91)}
for k,(L,d) in CAPS.items(): P.append((f"Hard capsule size {k}","capsule",L,d,d,"https://cache.erowid.org/archive/rhodium/pdf/gelcap.sizechart.pdf"))
# rapporti spessore ricalibrati sui casi DS (vedi tabella 'calibrazione')
RAT={"round":(0.45,0.56),"oval":(0.60,0.86),"flat":(0.30,0.40),"chew":(0.38,0.50)}
def thick(shape,L,W,T):
    if T: return T,T,False
    a,b=RAT[shape]; base=L if shape in("round","flat","chew") else W
    return a*base,b*base,True
rows=[]
for name,shape,L,W,T,src in P:
    tlo,thi,est=thick(shape,L,W,T); res={}
    for tt in (tlo,thi):
        s=sorted((L,W,tt))
        r=dict(comp=comp_fits(L,W,tt),exit=passes(s,14,13),roof=passes(s,7.2,10),tray_up=s[0]<=3.5 and s[1]<=10,chute=passes(s,4.2,12))
        for k,v in r.items(): res.setdefault(k,[]).append(v)
    top=all(res['roof'])and all(res['tray_up'])and all(res['chute'])
    top_any=any(a and b and c for a,b,c in zip(res['roof'],res['tray_up'],res['chute']))
    rows.append(dict(name=name,shape=shape,L=L,W=W,t=(round(tlo,1),round(thi,1)),t_ev="HYP" if est else "DS",
       vol_cm3=round(vol('capsule' if shape=='capsule' else ('round' if shape in('round','flat','chew') else 'oval'),L,W,(tlo+thi)/2)/1000,3),
       comp=all(res['comp']),comp_any=any(res['comp']),exit=all(res['exit']),exit_any=any(res['exit']),
       top="yes" if top else("depends" if top_any else "no"),src=src))
json.dump(rows,open(os.path.join(HERE,'pills_v2.json'),'w'),indent=1)
n=len(rows); f=lambda k:sum(r[k] for r in rows)
print('N',n,'DS thickness',sum(r['t_ev']=='DS' for r in rows),'| comp',f('comp'),'(any',f('comp_any'),') exit',f('exit'),'(any',f('exit_any'),') top yes',sum(r['top']=='yes' for r in rows),'depends',sum(r['top']=='depends' for r in rows))
for r in rows:
    if not r['exit'] or not r['comp']: print('  FAIL',r['name'],r['L'],r['W'],r['t'],'comp',r['comp'],r['comp_any'],'exit',r['exit'],r['exit_any'])
# calibrazione: rapporti misurati vs vecchia ipotesi
print('calib round t/d: 4.0/8=%.2f 3.5/6.5=%.2f (old 0.40-0.50)'%(4/8,3.5/6.5))
print('calib oval t/W: apix %.2f-%.2f, teva %.2f, glucophage %.2f, SR %.2f (old 0.50-0.75)'%(4/5.4,4.4/5.4,4.8/5.6,6.4/10.5,8/10))
