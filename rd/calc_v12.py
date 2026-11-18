"""Calcoli ingegneristici e fisici della v1.2 (stessi metodi di calc.py per la v0.9, aggiornati ai pezzi veri).
Uscita: rd/calc_v12.json. Classi di evidenza: DS = scheda tecnica, CALC = calcolo, HYP = ipotesi, CAD = misura sul modello."""
import os, sys, math, json, random, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'cad'))
random.seed(12)
import scatoletta_v12 as s12, scatoletta_v10 as s10
M = s12.Modello12(); OUT = {}
g = 9.81

# ---------------- 1. CAD (dal modello e da v12/parametri_stampa.json)
par = json.load(open(os.path.join(HERE, '..', 'v12', 'parametri_stampa.json')))
L, W, H = M.misure()
OUT['cad'] = dict(L=round(L, 1), W=round(W, 1), H=round(H, 1), litri=round(L * W * H / 1e6, 2), piede=[M.PIEDE['x1'] - M.PIEDE['x0'], 2 * M.PIEDE['y']],
                  petg_cm3=par['totale']['volume_cm3'], petg_g=par['totale']['massa_g'], stampa_h=par['totale']['tempo_stimato_h'], pezzi=len(par['pezzi']),
                  croce=dict(C=round(M.C_GEN, 3), R_perno=round(M.R_MAN, 3), ang=s10.ANG_CROCE[s12.K]), pignone=[round(x, 2) for x in M.pos_pignone()], stepper=[round(x, 2) for x in M.pos_stepper()])

# ---------------- 2. pillole (database a 55 forme di pills_v2.json; scomparto e uscita come v1.0; ricarica: canaletta da 6,5 mm)
pills = json.load(open(os.path.join(HERE, 'pills_v2.json')))
RIC = (6.3, 12.0, 16.7)          # dimensioni massime che passano dalla ricarica dall'alto (rapporto v1.0: canaletta 6,5, sportello 6,7 x 23,9, scivolo)
def ricarica(r, t):
    s = sorted((r['L'], r['W'], t)); return s[0] <= RIC[0] and s[1] <= RIC[1] and s[2] <= RIC[2]
for r in pills: r['ric'] = all(ricarica(r, t) for t in r['t']); r['ric_any'] = any(ricarica(r, t) for t in r['t'])
OUT['pillole'] = dict(N=len(pills), scomparto=sum(r['comp'] for r in pills), uscita=sum(r['exit'] for r in pills),
                      ricarica=sum(r['ric'] for r in pills), ricarica_dipende=sum(r['ric_any'] and not r['ric'] for r in pills),
                      non_passano_uscita=[r['name'] for r in pills if not r['exit']])

# ---------------- 3. stepper 28BYJ-48 + ULN2003 (DS) -> croce di Malta
R_COIL, V, VCE = 50.0, 5.0, 0.9                      # ohm (DS), V USB, V Darlington a 100 mA (DS TI)
I_coil = (V - VCE) / R_COIL                           # A per bobina
k_I = I_coil / (V / R_COIL)                           # coppia ~ proporzionale alla corrente (sotto saturazione): ipotesi
T_pullin = 300e-3 * g * 1e-2 * 1e3                   # 300 gf.cm -> mN.m (DS)
T_self = 34.3                                         # mN.m self-positioning (DS)
T_use = T_pullin * k_I                                # coppia disponibile con la caduta dell'ULN2003
T_max = T_self * 1.5                                  # caso peggiore per i denti: coppia massima a bassa velocita' (HYP: 1,5 x self-positioning)
ratio = Z_C = 24 / 10; eta = 0.9
C, a = M.C_GEN, M.R_MAN
phimax = math.pi / 2 - math.pi / s10.N
def rapporto(phi):                                     # dtheta_ruota / dphi_croce, phi dalla linea dei centri
    x = C - a * math.cos(phi); y = a * math.sin(phi); return a * (a - C * math.cos(phi)) / (x * x + y * y)
rmax = max(abs(rapporto(i / 400 * phimax)) for i in range(401))
m_w, m_p, mu = 0.0404, 0.020, 0.3                     # kg ruota, kg pillole a pieno carico (HYP), attrito (come calc.py)
T_ruota = mu * m_p * g * M.R_O + m_p * g * 0.035 + 0.3 * (m_w + m_p) * g * 3.0   # N.mm (stesso modello di calc.py)
T_motore_serve = T_ruota * rmax / ratio / eta          # N.mm = mN.m al motore
# finecorsa: il perno spinge il pulsantino
F_fc = (0.160, 0.110, 0.210)                           # kgf nominale, min, max (DS 160 +-50 gf)
r_perno = M.R_MAN + 1.5
T_fc = [f * g * r_perno for f in F_fc]                 # N.mm sulla croce
T_fc_mot = [t / ratio / eta for t in T_fc]             # mN.m al motore (con attrito di strisciamento: x1,3 HYP)
T_fc_mot = [t * 1.3 for t in T_fc_mot]
# denti (Lewis) e perno, alla coppia massima del motore (lo stepper non ha corrente di spunto: la coppia e' limitata dal motore stesso)
Y_lewis = 0.201; b_dente = 2.0; m_mod = 1.0
def denti(Tm):
    Ft = Tm / 5.0; return Ft, Ft / (b_dente * m_mod * Y_lewis)
Ft_use, sig_use = denti(T_use); Ft_max, sig_max = denti(T_max)
Td_max = T_max * ratio * eta; F_perno = Td_max / a
sig_perno = 32 * F_perno * 1.3 / (math.pi * 3.0 ** 3)
# tempi
pps = (300, 500)                                        # passi interi al secondo (500 = pull-in DS); 2048 passi a giro (DS 1/64)
passi_giro = 2048 * 63.684 / 64
tempi = [round(ratio * passi_giro / p, 1) for p in pps]
OUT['motore'] = dict(I_bobina_mA=round(I_coil * 1000), coppia_pullin_mNm=round(T_pullin, 1), coppia_utile_mNm=round(T_use, 1), coppia_max_ipotesi_mNm=round(T_max, 1),
                     rapporto_croce_max=round(rmax, 3), coppia_ruota_Nmm=round(T_ruota, 2), coppia_motore_serve_mNm=round(T_motore_serve, 2),
                     margine=round(T_use / T_motore_serve), finecorsa_croce_Nmm=[round(t, 1) for t in T_fc], finecorsa_motore_mNm=[round(t, 1) for t in T_fc_mot],
                     finecorsa_quota=[round(t / T_use * 100) for t in T_fc_mot],
                     dente_uso=dict(Ft_N=round(Ft_use, 1), sigma_MPa=round(sig_use, 1)), dente_max=dict(Ft_N=round(Ft_max, 1), sigma_MPa=round(sig_max, 1)),
                     perno_max=dict(F_N=round(F_perno, 1), sigma_MPa=round(sig_perno, 1)), secondi_per_scomparto=dict(zip(map(str, pps), tempi)),
                     passi_per_scomparto=round(ratio * passi_giro), passi_ritorno_finecorsa=round(60 / 360 * ratio * passi_giro))

# ---------------- 4. finecorsa: corsa del pulsantino contro la spinta del perno (Monte Carlo)
def mc_finecorsa(n=200000):
    nonscatta = fine_corsa = 0; resto = []
    for _ in range(n):
        spinta = (M.R_MAN + 1.5) - s12.FC['punta']                     # 0,27 mm nominali (CAD)
        spinta += random.gauss(0, 0.10) + random.gauss(0, 0.05) + random.gauss(0, 0.04)   # tasca stampata, perno/croce, asse M2 (HYP)
        corsa = random.uniform(0.15, 0.45)                              # 0,25 +0,2/-0,1 (DS PTS645)
        scatta = 0.6 * corsa                                            # scatta a circa 60% della corsa (HYP)
        if spinta < scatta: nonscatta += 1
        if spinta > corsa: fine_corsa += 1; resto.append(spinta - corsa)
    return round(nonscatta / n, 3), round(fine_corsa / n, 3), round(st.mean(resto), 2) if resto else 0
p_no, p_fine, oltre = mc_finecorsa()
OUT['finecorsa'] = dict(spinta_nominale_mm=round((M.R_MAN + 1.5) - s12.FC['punta'], 2), P_non_scatta=p_no, P_a_fine_corsa=p_fine, oltre_medio_mm=oltre)

# ---------------- 5. ingranamento pignone - croce (asola della piastra: boss da 9 in foro da 10,4)
gioco_foro = (10.4 - 9.0) / 2
d_ass = math.radians(s12.A_PIGN)
CD0 = s12.D_PIGN
# lo stepper scorre verso -x nell'asola: se lo si spinge fino in fondo il boss tocca il bordo del foro
spost = (-gioco_foro, 0.0)
cd_fondo = math.hypot(CD0 * math.cos(d_ass) + spost[0], CD0 * math.sin(d_ass) + spost[1])
cd_min_lim = 17.0                                      # interasse teorico 10 + 24 denti modulo 1
OUT['ingranamento'] = dict(interasse_nominale=CD0, interasse_spinto_in_fondo=round(cd_fondo, 2), interferenza_mm=round(cd_min_lim - cd_fondo, 2),
                           con_foro_9_4=round(math.hypot(CD0 * math.cos(d_ass) - 0.2, CD0 * math.sin(d_ass)), 2))

# ---------------- 6. tolleranze lamelle - anello (v1.0: spina d'acciaio 6 m6, foro alesato 6 H7), Monte Carlo
def mc_lamelle(n=200000):
    gaps = []; tocca = 0
    for _ in range(n):
        anello = 47.3 + random.gauss(-0.05, 0.075)
        punta = 47.0 + random.gauss(0, 0.05) + random.gauss(0, 0.03)
        foro = 3.0 + random.uniform(0, 0.012) / 2; asse = 3.0 + random.uniform(0.002, 0.008) / 2   # H7 / m6, raggi
        g_ = anello - punta - max(0, foro - asse) - abs(random.gauss(0, 0.03))   # + eccentricita' della spina nella torretta (HYP)
        gaps.append(g_); tocca += g_ < 0
    gaps.sort(); return round(st.mean(gaps), 3), round(gaps[int(.01 * n)], 3), round(tocca / n, 4)
OUT['lamelle'] = dict(zip(('media_mm', 'p1_mm', 'P_tocca'), mc_lamelle()))

# ---------------- 7. bilancia (una cella da 100 g, 1 mV/V DS TAL220, HX711 guadagno 128)
OUT['bilancia'] = {}
for vexc in (3.3, 4.3):
    uvg = 1.0e-3 * vexc / 100 * 1e6
    OUT['bilancia'][str(vexc)] = dict(uV_per_g=round(uvg, 1), rumore_mg=round(0.05 / uvg * 1000, 2))
OUT['bilancia']['deriva_zero_mg_per_10C'] = round(0.0005 * 100 * 1000 / 1, 0)    # 0,05% FS / 10 C (HYP tipico): la tara si rifa' prima di ogni dose

# ---------------- 8. corrente e alimentazione (5 V USB)
corr = dict(esp32_wifi_picco=350, esp32_medio=100, stepper_in_moto=round(2 * I_coil * 1000), servo_in_moto=250, servo_bloccato=650, cicalino=30, oled=20, hx711=2, uln_led=4 * 3)
picco = corr['esp32_wifi_picco'] + corr['stepper_in_moto'] + corr['servo_bloccato'] + corr['cicalino'] + corr['oled']
picco_tutti = picco + corr['stepper_in_moto']
OUT['corrente_mA'] = dict(corr, picco_un_motore=picco, picco_due_motori=picco_tutti, riposo=corr['esp32_medio'] + corr['oled'] + corr['hx711'])
gpio = dict(stepper=8, servo=1, hx711=2, i2c_oled=2, cicalino=1, tasto=1, finecorsa=2, hall_bicchiere=1)
OUT['gpio'] = dict(gpio, totale=sum(gpio.values()), sicuri_supermini=12, generali_supermini=19)

# ---------------- 9. termica
P_mot = 2 * I_coil ** 2 * R_COIL; P_uln = 2 * I_coil * VCE
OUT['termica'] = dict(potenza_motore_W=round(P_mot, 2), potenza_uln_W=round(P_uln, 2), salita_motore_continua_K=40,
                      t_motore_continuo_C=25 + 40, PETG_Tg_C=80, PETG_HDT_C=70, secondi_al_giorno=round(4 * 2 * max(tempi)),
                      energia_giorno_J=round(4 * 2 * max(tempi) * P_mot, 0), crescita_ruota_20_40C_mm=round(47 * 68e-6 * 20, 3))

# ---------------- 10. umidita' (aria nel guscio)
Vair = L * W * H / 1e9 * 0.5; abs_h = 23.0 * 0.6
OUT['umidita'] = {str(ach): dict(acqua_g_giorno=round(Vair * abs_h * ach * 24, 3), giorni_4g_gel=round(2 * 2 * 0.25 / (Vair * abs_h * ach * 24), 1)) for ach in (0.05, 0.5, 2.0)}

# ---------------- 11. stabilita' (da controlli_v12.py) e spinte che la ribaltano
m_tot = 0.767; cz = 64.0; cy = 0.0
F_lato_cima = m_tot * g * (M.PIEDE['y'] - abs(cy)) / H
F_dietro_cima = m_tot * g * (0.4 - M.PIEDE['x0']) / H
OUT['stabilita'] = dict(angoli=dict(lato=41.1, avanti=46.4, dietro=40.8), peso_g=767, forza_in_cima_per_ribaltarla_di_lato_N=round(F_lato_cima, 2),
                        forza_in_cima_indietro_N=round(F_dietro_cima, 2), forza_tasto_N=50)

# ---------------- 12. aletta della cassetta (M2,5) e piastra dello stepper
F_estrazione = 5.0     # N: chi tira la cassetta con la vite avvitata (HYP)
t_al, w_al, l_al = 2.0, 7.0, 3.5      # mm: spessore, larghezza, sbalzo dall'anello alla vite
sig_al = 6 * F_estrazione * l_al / (w_al * t_al ** 2)
F_rad = Ft_max * math.tan(math.radians(20)); M_piastra = math.hypot(Ft_max, F_rad) * 8.0
OUT['strutture'] = dict(aletta_sigma_MPa=round(sig_al, 1), vite_M25_precarico_N=round(0.1e3 / (0.2 * 2.5), 0),
                        piastra_forza_denti_N=round(math.hypot(Ft_max, F_rad), 1), piastra_momento_Nmm=round(M_piastra, 0))

json.dump(OUT, open(os.path.join(HERE, 'calc_v12.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(OUT, indent=1, ensure_ascii=False))
