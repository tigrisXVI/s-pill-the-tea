#!/usr/bin/env python3
"""
Scatoletta Blistra v0.8 - la piu' compatta (prova), in due modelli da confrontare:

  "2m"  due ruote sottili (Ø ~10 cm), ognuna con il suo motorino N20     -> la piu' piccola
  "1m"  una ruota doppia (Ø ~13 cm), tasche sui due lati, un solo motorino -> un pezzo e un motore in meno

Uguale nei due modelli:
  - le ruote sono mosse da una CORONA DENTATA sul bordo: il pignone del motorino (in un angolo, dove la ruota
    tonda lascia spazio libero) ha l'asse parallelo a quello della ruota, cosi' la cassetta si sfila di lato
    e i denti si staccano da soli
  - lo scomparto che arriva in basso si svuota da solo nell'imbuto
  - sotto l'imbuto c'e' il PIATTINO PESATO (su una cella di carico da 100 g): si apre, con un micro servo,
    solo se il peso e' quello impostato nell'app
  - sotto ancora il bicchierino, come in una macchina del caffe': in una nicchia aperta, si prende e si appoggia.
    Un magnete nella base del bicchierino e un sensore di Hall dicono se e' al suo posto
  - un PIEDE largo e basso con dentro una piastra d'acciaio tiene la scatola in piedi (stabilita')
  - tasto tondo da 21 mm sul cappello colorato; il display e' davanti, in alto

Assi: X davanti, Y destra-sinistra (asse delle ruote), Z in alto. mm.
"""
import math, os
import trimesh
from manifold3d import Manifold, CrossSection
from scatoletta_v3 import cil, scatola, cil_x, cil_y, ruota, ccw, a_mesh
import scatoletta_v5 as v5

N = 15; PASSO = 360.0 / N
BAIONETTA = (90.0, 210.0, 330.0)
R_MAGNETE = 40.0   # magnete 3 x 1 mm nella corona, sotto lo scomparto chiuso: segna la posizione di riposo
ANG_FERMO = -55.0  # fermo della cassetta (gradi, davanti in basso): lo gira un micro servo, comandato dall'app
R_SPIG = 5.0     # raggio degli spigoli verticali del guscio
Z_ESP = 12.0     # l'ESP32 sta 12 mm sopra la scheda dei driver: antenna lontana dalla cella di carico
R_TOP = 14.0     # spigoli del tetto arrotondati (davanti e dietro), come una macchina del caffe'
L_TASCA = 24.0; PROF = 13.0; SP_DIV = 1.0; G = 0.3; PARETE = 1.2
PAR_CAS = 1.2    # pareti della cassetta: 3 passate da 0,4 mm
MOD = 1.0; Z_PIGNONE = 20; R_PIGNONE = Z_PIGNONE * MOD / 2   # modulo 1: denti abbastanza grossi per la stampa 3D; pignone da 20 denti, il motorino sta fuori dalle cassette
N20 = dict(lato_a=12.0, lato_b=10.0, lungo=24.3 + 1.5, albero=3.0)   # motoriduttore N20 (senza encoder) + contatti
ANG_MOT = {"2m": (62.0, 118.0), "1m": (135.0,)}   # motorino della ruota sinistra davanti in alto, della destra dietro in alto        # dove il pignone tocca la corona (gradi, da +X verso +Z): angolo dietro in alto

MODELLI = {
    "2m": dict(nome="Due ruote, due motorini", R_I=23.0, ruote=2, labbri=False),
    "1m": dict(nome="Una ruota doppia, un motorino", R_I=38.0, ruote=1, labbri=True),
}

def ingranaggio(Z, m, fase=0.0):
    """Sezione di una ruota dentata (denti trapezoidali, modulo m): primitivo Z*m/2, piede -1,25 m, testa +m."""
    R = Z * m / 2; rr, rt = R - 1.25 * m, R + m; p = 360.0 / Z
    hr, ht = p / 4 * 1.69, p / 4 * 0.45
    pts = []
    for k in range(Z):
        c = fase + k * p
        for a, r in ((c - hr, rr), (c - ht, rt), (c + ht, rt), (c + hr, rr)):
            pts.append((r * math.cos(math.radians(a)), r * math.sin(math.radians(a))))
    return CrossSection([ccw(pts)])

def settore(r0, r1, a0, a1, z0, z1, n=24):
    pts = [(r0 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r0 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r1 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r1 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Manifold.extrude(CrossSection([ccw(pts)]), z1 - z0).translate([0, 0, z0])

class Modello:
    def __init__(self, chiave):
        p = MODELLI[chiave]; self.k = chiave; self.nome = p["nome"]
        self.R_I = p["R_I"]; self.R_O = self.R_I + L_TASCA; self.ruote = p["ruote"]; self.labbri = p["labbri"]
        self.Z_CORONA = round(2 * (self.R_O + 1.6) / MOD); self.R_GP = self.Z_CORONA * MOD / 2   # corona dentata: denti e raggio primitivo
        self.R_GT = self.R_GP + MOD                      # punta dei denti
        self.R_AN_T = self.R_O + G; self.R_AN_G = self.R_GT + G   # dentro dell'anello: zona tasche / zona corona
        self.R_CASS = self.R_AN_G + PAR_CAS
        self.APRE = 6.0 if self.labbri else 7.0           # mezza larghezza dell'uscita in basso: lo scomparto chiuso la copre con 3 mm di margine per lato
        if self.ruote == 2:
            self.Z_COR = (0.0, 2.0); self.Z_TAS = (2.0, 2.0 + PROF)       # locale: corona dietro, tasche davanti
        else:
            self.Z_COR = (-1.2, 1.2); self.Z_TAS = (1.2, 1.2 + PROF)      # corona in mezzo, tasche sui due lati
        self.TH = self.Z_TAS[1]
        self.Z_COP = (self.TH + 0.3, self.TH + 1.8); self.Z_FL = (self.Z_COP[1], self.Z_COP[1] + 1.2)   # coperchio: plexiglass da 1,5 mm
        # in Y
        if self.ruote == 2:
            self.Y0 = 0.95 + 1.4 + 0.3                   # parete centrale con il canale dei cavi (|y|<0,95) + fondo della cassetta + gioco
            self.Y_PIGN = self.Y0 + sum(self.Z_COR) / 2
            self.Y_DX = -self.Y_PIGN + 1.3 + N20["lungo"] + PARETE + 0.4; self.Y_SX = -self.Y_DX
        else:
            self.Y0 = 0.0
            self.Y_PIGN = 0.0
            ycas = self.Z_FL[1]
            self.Y_SX, self.Y_DX = -(ycas + 0.4), 2.0 + N20["lungo"] + PARETE
        # in X e Z
        self.X_HALF = self.R_CASS + 0.4 + PARETE
        self.Z_PIEDE = 8.4                               # piede con dentro la zavorra d'acciaio (6 mm)
        self.CUP = dict(x0=-22.0, x1=24.0, y=17.0, alt=26.0, parete=2.0, r=6.0)
        self.Z_CUP = self.Z_PIEDE
        self.Z_NICCHIA = self.Z_CUP + self.CUP["alt"] + 12.0   # il piattino si apre sopra il bicchierino
        self.Z_PIATTO = self.Z_NICCHIA + 11.0                  # sopra il tetto della nicchia: cella, staffa, vaschetta
        self.Z_IMB0 = self.Z_PIATTO + 7.0 + (abs(self.Y_PIGN) + PROF + 4 - 6.5) * 1.0 + 4   # imbuto a ~45 gradi
        self.Z_A = self.Z_IMB0 + self.R_CASS + 1.1          # 0,6 mm tra cassetta e imbuto: le pillole non si incastrano
        self.Z_DISP = (self.Z_A + math.sqrt(max(0, (self.R_CASS + 1.4) ** 2 - (self.R_CASS - 3.8) ** 2)) + 0.5, 0)   # il display sta dove la ruota curva
        self.Z_DISP = (self.Z_DISP[0], self.Z_DISP[0] + 34.0)
        self.H = max(self.Z_A + self.R_CASS + 0.6, self.Z_A + self._z_motori(), self.Z_DISP[1]) + PARETE + 2.6
        self.Y_MID = min((self.Y_SX + self.Y_DX) / 2, self.Y_DX - R_SPIG - 0.3 - 17.7)   # il display non deve toccare gli spigoli arrotondati
        self.PIEDE = dict(x0=-self.X_HALF, x1=self.X_HALF + 14.0, y=50.0, h=self.Z_PIEDE)

    def _z_motori(self):
        r = self.R_GP + R_PIGNONE
        return max(r * math.sin(math.radians(a)) + 8.5 for a in ANG_MOT[self.k]) + 4.0

    # ---------------- ruota (locale, asse Z)
    def ruota_locale(self, faccia_offset=0.0):
        m = Manifold()
        z0, z1 = self.Z_COR
        m += Manifold.extrude(ingranaggio(self.Z_CORONA, MOD), z1 - z0).translate([0, 0, z0])   # corona dentata
        zs = [(self.Z_TAS[0], self.Z_TAS[1], 0.0)]
        if self.ruote == 1: zs.append((-self.Z_TAS[1], -self.Z_TAS[0], PASSO / 2))
        for a0, a1, off in zs:
            m += cil(self.R_I, a0 - 0.01, a1) - cil(self.R_I - 1.6, a0 - 1, a1 + 1) + cil(5.0, a0 - 0.01, a1)   # mozzo vuoto, leggero
            for k in range(4): m += ruota(scatola(4.5, self.R_I - 1.0, -0.8, 0.8, a0 - 0.01, a0 + 3.0), 45 + 90 * k)
            for k in range(N):
                a = -90.0 + off + PASSO / 2 + k * PASSO
                m += ruota(scatola(self.R_I - 0.5, self.R_O, -SP_DIV / 2, SP_DIV / 2, a0 - 0.01, a1), a)
            m += settore(self.R_I - 0.5, self.R_O, -90.0 + off - PASSO / 2, -90.0 + off + PASSO / 2, a0 - 0.01, a1)   # chiuso
            # scivoli ai lati di ogni divisorio, vicino al bordo: lo scomparto finisce largo quanto l'uscita
            # e le pillole (anche quelle minuscole) scivolano verso il centro, a 60 gradi
            ag = ((self.R_O * 2 * math.pi / N - SP_DIV) / 2 - self.APRE + 0.4 + SP_DIV / 2) / self.R_O
            for k in range(N):
                a = math.radians(-90.0 + off + PASSO / 2 + k * PASSO)
                pts = [(self.R_O * math.cos(a - ag), self.R_O * math.sin(a - ag)), (self.R_O * math.cos(a + ag), self.R_O * math.sin(a + ag)),
                       ((self.R_O - 5.0) * math.cos(a), (self.R_O - 5.0) * math.sin(a))]
                m += Manifold.extrude(CrossSection([ccw(pts)]), a1 - a0 + 0.01).translate([0, 0, a0 - 0.01])
            if self.ruote == 2:   # fossette dove scattano i dentini degli sportellini
                for k in range(N):
                    for sgn in (-1, 1):
                        m -= ruota(cil(0.6, a1 - 0.45, a1 + 1.0, self.R_O - 1.5, 0), -90.0 + PASSO / 2 + k * PASSO + sgn * 1.5)
            for k in range(N):   # fessura in punta a ogni divisorio per la lamella (PETG, si incastra e si puo' limare)
                m -= ruota(scatola(self.R_O - 2.0, self.R_O + 1.0, -0.42, 0.42, a0, a1 + 1.0), -90.0 + off + PASSO / 2 + k * PASSO)
            if self.labbri:                               # bordo con aperture larghe 12 mm: tra un'uscita e l'altra c'e' pieno
                lab = cil(self.R_O, a0 - 0.01, a1) - cil(self.R_O - 2.0, a0 - 1, a1 + 1)
                for k in range(1, N):
                    a = -90.0 + off + k * PASSO
                    lab -= ruota(scatola(self.R_O - 3, self.R_O + 1, -self.APRE, self.APRE, a0 - 1, a1 + 1), a)
                m += lab
        m -= cil(3.3, -50, 50)                            # foro per l'asse (gioco 0,3 mm per la stampa)
        if self.ruote == 2:
            m -= cil(1.55, self.Z_COR[0] - 0.01, self.Z_COR[0] + 1.05, R_MAGNETE * math.cos(math.radians(-90)), R_MAGNETE * math.sin(math.radians(-90)))   # magnete di riposo
            zm = (self.Z_TAS[0] + self.Z_TAS[1]) / 2
            for k in range(1, N):     # forellini da 1,2 mm dal mozzo (gel di silice) a ogni scomparto: passa l'aria, non le pillole
                m -= ruota(cil_x(0.6, self.R_I - 2.4, self.R_I + 0.6, 0, zm), -90.0 + k * PASSO)
        return m

    # ---------------- cassetta (locale)
    def spazzole_locale(self):
        """Lamelle di PETG (tutto un solo materiale) infilate in punta ai divisori: arrivano a 0,1 mm dall'anello fermo
        senza toccarlo, cosi' tra ruota e anello non passa niente ma la ruota gira libera. Se la stampa viene un po' grossa
        si limano; se viene corta si spingono fuori nella fessura (incastro a pressione)."""
        a0, a1 = self.Z_TAS
        m = Manifold()
        for k in range(N):
            m += ruota(scatola(self.R_O - 1.95, self.R_AN_T - 0.1, -0.38, 0.38, a0 + 0.2, a1 - 0.2), -90.0 + PASSO / 2 + k * PASSO)
        return m

    def cassetta_locale(self):
        lati = [1] if self.ruote == 2 else [1, -1]
        m = Manifold()
        zc0, zc1 = self.Z_COR
        if self.ruote == 2:
            m += cil(self.R_CASS, zc0 - 1.4, zc0 - 0.4)                                        # fondo
            m += cil(3.0, zc0 - 0.41, self.TH - 0.5)                                            # asse fisso
        m += cil(self.R_CASS, zc0 - (1.4 if self.ruote == 2 else 0.4), zc1 + 0.4) - cil(self.R_AN_G, zc0 - 1, zc1 + 1)   # anello della corona
        for s in lati:
            a0, a1 = (self.Z_TAS[0], self.Z_FL[0]) if s > 0 else (-self.Z_FL[0], -self.Z_TAS[0])
            m += cil(self.R_CASS, a0, a1) - cil(self.R_AN_T, a0 - 1, a1 + 1)                    # anello delle tasche
            fl = (self.Z_FL[0], self.Z_FL[1]) if s > 0 else (-self.Z_FL[1], -self.Z_FL[0])
            if self.ruote == 2:   # davanti la cassetta e' aperta: ogni scomparto ha il suo sportellino sulla ruota
                m += cil(self.R_CASS + 1.0, fl[0], fl[1]) - cil(self.R_AN_T + 0.2, fl[0] - 1, fl[1] + 1)
                m -= ruota(scatola(self.R_CASS - 0.7, self.R_CASS + 2, -2.2, 2.2, fl[0] - 0.01, fl[1] + 0.01), ANG_FERMO)   # tacca del fermo
            else:
                m += cil(self.R_CASS + 1.0, fl[0], fl[1]) - cil(self.R_AN_T - 3.0, fl[0] - 1, fl[1] + 1)
            m -= scatola(-self.APRE, self.APRE, -self.R_CASS - 2, -self.R_AN_T + 1, min(self.Z_TAS[0] * s, self.Z_TAS[1] * s), max(self.Z_TAS[0] * s, self.Z_TAS[1] * s))  # uscita in basso
        for a in ANG_MOT[self.k]:
            m -= ruota(scatola(self.R_AN_G - 2, self.R_CASS + 3, -7.5, 7.5, zc0 - 0.3, zc1 + 0.3), a)   # finestra per il pignone
            if self.ruote == 1:                                   # la cassetta esce verso -Y (locale +Z): il pignone passa in una scanalatura
                m -= ruota(scatola(self.R_GP - MOD - 0.6, self.R_CASS + 3, -7.5, 7.5, -self.Z_FL[1] - 1, zc1), a)
        return m

    def sportellini_locale(self):
        """Uno sportellino trasparente (PETG trasparente) per ogni scomparto: cerniera a perno vicino al mozzo,
        si chiude a scatto sui due divisori e ha una linguetta per aprirlo con il dito. Gira con la ruota."""
        z0 = self.TH + 0.05; z1 = z0 + 1.2; rh = self.R_I + 1.6
        m = Manifold()
        for k in range(1, N):
            c = -90.0 + k * PASSO
            p = settore(self.R_I + 2.6, self.R_O - 0.3, c - PASSO / 2 + 0.3, c + PASSO / 2 - 0.3, z0, z1)
            w = 2 * rh * math.sin(math.radians(PASSO / 2 - 1.2))
            p += ruota(cil_y(0.9, -w / 2, w / 2, rh, z0 + 0.95) - cil_y(0.45, -w, w, rh, z0 + 0.95), c)               # cerniera (perno da 0,8 mm, un pezzo di filo)
            p += ruota(scatola(self.R_O - 5.0, self.R_O - 1.5, -2.5, 2.5, z1 - 0.01, z1 + 1.2), c)                 # linguetta per il dito
            for sgn in (-1, 1):                                                                                   # dentini dello scatto, sopra gli scivoli dei divisori
                p += ruota(cil(0.5, z0 - 0.35, z0 + 0.01, self.R_O - 1.5, 0), c + sgn * (PASSO / 2 - 1.5))
            m += p
        return m

    def tappo_locale(self):
        """Tappo del mozzo: chiude la tasca del gel di silice (circa 2 g), ha 6 feritoie e una presa per toglierlo."""
        z0 = self.TH + 0.05
        m = cil(self.R_I - 0.4, z0, z0 + 1.2) + (cil(self.R_I - 1.75, self.TH - 2.0, z0 + 0.01) - cil(self.R_I - 2.9, self.TH - 3, z0 + 1))
        for k in range(6): m -= ruota(scatola(9.0, 16.0, -0.6, 0.6, z0 - 1, z0 + 2), 30 + 60 * k)
        return m + scatola(-7.0, 7.0, -1.2, 1.2, z0 + 1.19, z0 + 2.4)

    def silice_locale(self):
        return cil(19.5, self.Z_TAS[0] + 3.5, self.TH - 2.5) - cil(6.0, 0, 30)

    # ---------------- fermo della cassetta: camma girata da un micro servo (dall'app: "Sblocca le cassette")
    def _fermo_pos(self):
        rc = self.R_CASS + 7.0
        return rc, rc * math.cos(math.radians(ANG_FERMO)), rc * math.sin(math.radians(ANG_FERMO))

    def fermo_locale(self):
        rc, xc, yc = self._fermo_pos(); f0, f1 = self.Z_FL
        m = ruota(scatola(self.R_CASS - 0.4, rc, -1.5, 1.5, f0 + 0.1, f1 - 0.1), ANG_FERMO)          # dente che entra nella tacca della flangia
        return m + cil(2.6, f0 - 0.6, f1 - 0.1, xc, yc) - cil(1.0, f0 - 1, f0 + 0.3, xc, yc)          # mozzo che si incastra sull'albero del servo

    def _servo_fermo_locale(self, g=0.0):
        rc, xc, yc = self._fermo_pos(); z1 = self.Z_FL[0] - 0.65
        return ruota(scatola(rc - 5.0 - g, rc + 15.2 + g, -10.1 - g, 10.1 + g, z1 - 8.5 - g, z1 + g), ANG_FERMO)

    def _staffa_fermo_locale(self):
        rc, xc, yc = self._fermo_pos(); z1 = self.Z_FL[0] - 0.65
        return ruota(scatola(rc + 9.0, rc + 15.2, -10.1, 10.1, z1 - 0.01, self.Y_DX - PARETE - self.Y0 + 0.01), ANG_FERMO)   # attacca il servo al fianco, fuori dal giro del dente

    def fermo(self, s): return self.metti(self.fermo_locale(), s)
    def fermo_perno(self, s):
        rc, xc, yc = self._fermo_pos(); return [xc, s * (self.Y0 + self.Z_FL[0]), self.Z_A + yc]
    def servo_fermo(self, s): return self.metti(self._servo_fermo_locale(), s)

    def coperchio_locale(self, s=1):
        z0, z1 = self.Z_COP
        if self.ruote == 2:
            # disco di plexiglass con tre linguette (baionetta): si infila con le linguette nelle tacche e si gira di 30 gradi
            m = cil(self.R_AN_T - 0.15, z0, z1)
            for c in BAIONETTA: m += settore(self.R_AN_T - 0.5, self.R_AN_T + 1.5, c + 30 - 4.8, c + 30 + 4.8, z0, z1)
            m += cil(6.0, z1 - 0.01, self.Z_FL[1] + 3.0) - cil(2.0, self.Z_FL[1] + 1.0, self.Z_FL[1] + 3.5)   # pomello stampato, incollato: per girare il coperchio e sfilare la cassetta
            return m
        m = cil(self.R_AN_T - 0.15, z0, z1) + cil(self.R_AN_T - 3.2, z1 - 0.01, self.Z_FL[1] - 0.2)
        if self.ruote == 1: m += cil(3.0, -self.TH + 0.5, z0 + 0.01) if s > 0 else Manifold()    # l'asse sta sul coperchio di un lato
        if self.ruote == 1: m -= cil(3.3, z0 - 1, z1 + 5) if s < 0 else Manifold()
        return m if s > 0 else m.mirror([0, 0, 1])

    # ---------------- da locale a mondo
    def metti(self, m, lato):
        if self.ruote == 2:
            m = m.rotate([90, 0, 0]).translate([0, -self.Y0, self.Z_A])
            return m if lato < 0 else m.mirror([0, 1, 0])
        return m.rotate([90, 0, 0]).translate([0, 0, self.Z_A])

    # ---------------- motorini con pignone
    def motori(self):
        out = []
        for i, a in enumerate(ANG_MOT[self.k]):
            r = self.R_GP + R_PIGNONE
            x, z = r * math.cos(math.radians(a)), self.Z_A + r * math.sin(math.radians(a))
            if self.ruote == 2:
                s = -1 if i == 0 else 1                  # motore della ruota di sinistra / di destra
                yp = s * self.Y_PIGN
                faccia = yp - s * 1.3                     # faccia del riduttore, il corpo va verso l'altro lato
                y0, y1 = sorted((faccia, faccia - s * N20["lungo"]))
            else:
                yp = 0.0; faccia = 2.0; y0, y1 = 2.0, 2.0 + N20["lungo"]
            corpo = ruota(scatola(r - N20["lato_b"] / 2, r + N20["lato_b"] / 2, -N20["lato_a"] / 2, N20["lato_a"] / 2, 0, 1), 0)
            corpo = scatola(-N20["lato_b"] / 2, N20["lato_b"] / 2, y0, y1, -N20["lato_a"] / 2, N20["lato_a"] / 2).rotate([0, -a, 0]).translate([x, 0, z])
            out.append(corpo + cil_y(N20["albero"] / 2, min(yp - 0.9, faccia), max(yp + 0.9, faccia), x, z))
        return out

    def pignoni(self):
        """Pignoni da 26 denti, in fase con la corona; ritorna (pezzo, centro x, y, z)."""
        out = []
        pc, pp = 360.0 / self.Z_CORONA, 360.0 / Z_PIGNONE
        for i, a in enumerate(ANG_MOT[self.k]):
            s = -1 if i == 0 else 1; yp = s * self.Y_PIGN if self.ruote == 2 else 0.0
            r = self.R_GP + R_PIGNONE; cx, cz = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
            t = round(a / pc) * pc; px, pz = self.R_GP * math.cos(math.radians(t)), self.R_GP * math.sin(math.radians(t))
            beta = math.degrees(math.atan2(pz - cz, px - cx))
            sez = ingranaggio(Z_PIGNONE, MOD, beta + pp / 2)
            m = Manifold.extrude(sez, 2.0).translate([0, 0, -1.0]).transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
            m = (m + cil_y(3.5, -1.0, 1.0, 0, 0)) - cil_y(N20["albero"] / 2 + 0.05, -3, 3, 0, 0)
            out.append((m.translate([cx, yp, self.Z_A + cz]), cx, yp, self.Z_A + cz))
        return out

    def supporti_motori(self):
        m = Manifold()
        r = self.R_GP + R_PIGNONE
        for i, a in enumerate(ANG_MOT[self.k]):
            if self.ruote == 2:
                s = -1 if i == 0 else 1; y0, y1 = sorted((s * self.Y_PIGN - s * 3.0, s * self.Y_PIGN - s * 1.3 - s * (N20["lungo"] - 4.5)))
            else: y0, y1 = 4.0, 2.0 + N20["lungo"]
            fascia = scatola(r + N20["lato_b"] / 2, r + N20["lato_b"] / 2 + 1.6, y0, y1, -N20["lato_a"] / 2 - 1.6, N20["lato_a"] / 2 + 1.6)
            fascia += scatola(r - N20["lato_b"] / 2 - 0.01, r + N20["lato_b"] / 2 + 1.6, y0, y1, N20["lato_a"] / 2, N20["lato_a"] / 2 + 1.6)
            fascia += scatola(r - N20["lato_b"] / 2 - 0.01, r + N20["lato_b"] / 2 + 1.6, y0, y1, -N20["lato_a"] / 2 - 1.6, -N20["lato_a"] / 2)
            m += fascia.transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]).rotate([0, -a, 0]).translate([0, 0, self.Z_A])
        return m

    # ---------------- imbuto, piattino pesato, servo, cella
    def imbuto(self):
        ye = (abs(self.Y_PIGN) + PROF + 2.5) if self.ruote == 2 else min(self.Z_TAS[1] + 0.5, -self.Y_SX - PARETE - 1.9)
        larg = self.APRE + 2.0
        zb = self.Z_PIATTO + 7.0
        prof = [(6.5, zb - 1.6), (ye + 1.6, self.Z_IMB0 - 0.01), (ye + 1.6, self.Z_IMB0 + 0.5), (ye, self.Z_IMB0 + 0.5), (6.5, zb)]
        sez = Manifold.extrude(CrossSection([ccw(prof)]), 2 * larg).translate([0, 0, -larg]).transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])
        m = sez + sez.mirror([0, 1, 0])
        for x in (-larg - 1.6, larg): m += scatola(x, x + 1.6, -ye - 1.6, ye + 1.6, zb - 1.6, self.Z_IMB0 + 8.0) - cil_y(self.R_CASS + 0.6, -50, 50, 0, self.Z_A) \
                 - cil_y(self.R_CASS + 1.6, self.Y0 + self.Z_FL[0] - 0.6, 50, 0, self.Z_A) - cil_y(self.R_CASS + 1.6, -50, -(self.Y0 + self.Z_FL[0] - 0.6), 0, self.Z_A)
        yf = self.Y0 + self.Z_FL[0] - 0.6
        m -= cil_y(self.R_CASS + 1.6, yf, 50, 0, self.Z_A) + cil_y(self.R_CASS + 1.6, -50, -yf, 0, self.Z_A)   # spazio per la flangia della cassetta
        # paratia fissa dietro il piattino: a 0,6 mm dal suo bordo aperto, cosi' le pillole non scivolano via
        p = self.PIATTO
        m += scatola(p["x0"] - 1.8, p["x0"] - 0.6, -p["y"], p["y"], self.Z_PIATTO + 0.2, zb - 1.59) + scatola(p["x0"] - 1.8, -larg - 0.01, -p["y"], p["y"], zb - 1.6, zb)
        return m

    PIATTO = dict(x0=-11.0, x1=13.0, y=11.0)
    def lato_cerniera(self): return -1 if self.ruote == 2 else 1      # da che parte e' la cerniera della vaschetta

    def perno_piattino(self): return (self.PIATTO["x1"] + 0.6, self.Z_PIATTO + 0.6)

    def piattino(self, gradi=0.0):
        """Vaschetta pesata: il perno e' davanti (lo gira il micro servo), il bordo dietro e' aperto e scende:
        le pillole scivolano verso il fondo della nicchia e cadono nel bicchierino."""
        p = self.PIATTO; z = self.Z_PIATTO; xh, zh = self.perno_piattino()
        m = scatola(p["x0"], p["x1"], -p["y"], p["y"], z, z + 1.2)
        m += scatola(p["x1"] - 1.2, p["x1"], -p["y"], p["y"], z, z + 5)                                   # parete davanti
        for sy in (-1, 1): m += scatola(p["x0"], p["x1"], min(sy * p["y"], sy * (p["y"] - 1.2)), max(sy * p["y"], sy * (p["y"] - 1.2)), z, z + 5)   # pareti di lato
        m += cil_y(1.25, -p["y"] - 2.6, p["y"] + 2.6, xh, zh)                                            # perno (diametro 2,5 mm, stampato in verticale)
        if gradi: m = m.translate([-xh, 0, -zh]).rotate([0, -gradi, 0]).translate([xh, 0, zh])
        return m

    def staffa_cella(self):
        """Due spalle con il foro del perno, unite da una piastrina che sta sull'estremita' libera della cella."""
        p = self.PIATTO; z = self.Z_PIATTO; xh, zh = self.perno_piattino()
        m = scatola(xh - 2.6, xh + 1.3, -(p["y"] + 12.0), p["y"] + 2.6, z - 2.8, z - 1.6)
        for sy in (-1, 1):
            y0, y1 = sorted((sy * (p["y"] + 0.4), sy * (p["y"] + 2.6)))
            m += scatola(xh - 2.6, xh + 2.6, y0, y1, z - 2.8, zh + 2.6) - cil_y(1.55, y0 - 1, y1 + 1, xh, zh)   # foro con 0,3 mm di gioco
        return m

    def cella(self):
        p = self.PIATTO; z = self.Z_PIATTO; s = self.lato_cerniera()
        y = sorted((s * (p["y"] + 0.7), s * (p["y"] + 12.7)))
        return scatola(p["x1"] + 2.0 - 47.0, p["x1"] + 2.0, y[0], y[1], z - 8.8, z - 2.8)

    def servo(self):
        """Micro servo 3,7 g (20,2 x 8,5 x 20,2): la sua levetta spinge giu' il bordo davanti della vaschetta."""
        p = self.PIATTO; z = self.Z_PIATTO
        return scatola(p["x1"] + 2.0, p["x1"] + 10.5, -10.1, 10.1, z - 6.0, z + 14.2)

    # ---------------- bicchierino, sensore, piede, guscio
    def bicchierino(self):
        c = self.CUP; z = self.Z_CUP
        m = v5.rett_arrotondato(c["x0"], c["x1"], -c["y"], c["y"], c["r"], z, z + c["alt"])
        m -= v5.rett_arrotondato(c["x0"] + c["parete"], c["x1"] - c["parete"], -c["y"] + c["parete"], c["y"] - c["parete"], c["r"] - c["parete"], z + 2.2, z + c["alt"] + 1)
        lab = v5.rett_arrotondato(c["x0"] + c["parete"], c["x1"] - c["parete"], -c["y"] + c["parete"], c["y"] - c["parete"], c["r"] - c["parete"], z + c["alt"] - 1.6, z + c["alt"])
        lab -= v5.rett_arrotondato(c["x0"] + 4.5, c["x1"] - 4.5, -c["y"] + 4.5, c["y"] - 4.5, 3, z + c["alt"] - 2, z + c["alt"] + 1)
        m += lab
        sf = lambda x, zz: Manifold.sphere(4.4, 24).scale([1.0, 1.55, 1.0]).translate([x, 0, zz])
        giro = [(c["x1"] - 3, z + c["alt"] - 5), (c["x1"] + 12, z + c["alt"] - 3), (c["x1"] + 21, z + c["alt"] - 9), (c["x1"] + 22, z + 11), (c["x1"] + 15, z + 6), (c["x1"] - 3, z + 6)]
        for (xa, za), (xb, zb) in zip(giro, giro[1:]): m += Manifold.batch_hull([sf(xa, za), sf(xb, zb)])
        m -= v5.rett_arrotondato(c["x0"] + c["parete"], c["x1"] - c["parete"], -c["y"] + c["parete"], c["y"] - c["parete"], c["r"] - c["parete"], z + 2.2, z + c["alt"] - 1.6)
        m -= cil_x(3.1, c["x0"] - 1, c["x0"] + 1.6, 0, z + 6.0)                                 # magnete 6 x 1,5 nella parete dietro, in basso
        return m

    def piede(self):
        p = self.PIEDE
        # piede largo e basso, con i fianchi inclinati (come la base di una lampada)
        m = Manifold.batch_hull([v5.rett_arrotondato(p["x0"], p["x1"], -p["y"], p["y"], 18, 0, 1.0),
                                 v5.rett_arrotondato(p["x0"] + 4, p["x1"] - 4, -p["y"] + 4, p["y"] - 4, 14, p["h"] - 0.01, p["h"])])
        z = self.ZAVORRA; xc = (p["x0"] + p["x1"]) / 2
        m -= scatola(xc - z["lungo"] / 2 - 0.3, xc + z["lungo"] / 2 + 0.3, -z["largo"] / 2 - 0.3, z["largo"] / 2 + 0.3, -1, 1.2 + z["spess"] + 0.3)   # tasca aperta sotto: la piastra si incolla da sotto, poi i piedini di gomma
        return m

    ZAVORRA = dict(lungo=104.0, largo=76.0, spess=6.0)    # piastra di ferro 104 x 76 x 6 mm (~370 g)
    def _zavorra(self, g=0.0):
        z = self.ZAVORRA; xc = (self.PIEDE["x0"] + self.PIEDE["x1"]) / 2
        return scatola(xc - z["lungo"] / 2 - g, xc + z["lungo"] / 2 + g, -z["largo"] / 2 - g, z["largo"] / 2 + g, 1.2 - g, 1.2 + z["spess"] + g)

    def piastra_acciaio(self):
        return self._zavorra()

    def _profilo(self, g):
        """Vista di fianco: rettangolo con gli spigoli in alto arrotondati (raggio R_TOP), rientrato di g."""
        xc, zc, r = self.X_HALF - R_TOP, self.H - R_TOP, R_TOP - g
        return (scatola(-self.X_HALF + g, self.X_HALF - g, -200, 200, -10, zc)
                + Manifold.batch_hull([cil_y(r, -200, 200, -xc, zc), cil_y(r, -200, 200, xc, zc)]))

    @property
    def Z_TAGLIO(self): return round(self.Z_DISP[0] - 8.0)      # dove finisce il corpo scuro e comincia il cappello colorato

    def _zona_cappello(self):
        g0, g1 = PARETE + 0.3, PARETE + 1.9
        x0, x1, y0, y1 = -self.X_HALF, self.X_HALF, self.Y_SX, self.Y_DX
        bordino = (v5.rett_arrotondato(x0 + g0, x1 - g0, y0 + g0, y1 - g0, R_SPIG - g0, self.Z_TAGLIO - 3.0, self.Z_TAGLIO + 0.01)
                   - v5.rett_arrotondato(x0 + g1, x1 - g1, y0 + g1, y1 - g1, 1.0, self.Z_TAGLIO - 4, self.Z_TAGLIO + 1))
        return scatola(-200, 200, -200, 200, self.Z_TAGLIO, 400) + bordino

    def guscio(self): return self.corpo() - self._zona_cappello()
    def cappello(self): return self.corpo() ^ self._zona_cappello()

    def corpo(self):
        if getattr(self, "_corpo", None) is not None: return self._corpo
        x0, x1, y0, y1 = -self.X_HALF, self.X_HALF, self.Y_SX, self.Y_DX
        m = v5.rett_arrotondato(x0, x1, y0, y1, R_SPIG, self.Z_PIEDE, self.H) ^ self._profilo(0)
        m -= v5.rett_arrotondato(x0 + PARETE, x1 - PARETE, y0 + PARETE, y1 - PARETE, R_SPIG - PARETE, self.Z_PIEDE + PARETE, self.H) ^ self._profilo(PARETE)
        m += self._zona_cappello() - scatola(-200, 200, -200, 200, self.Z_TAGLIO, 400)    # bordino che centra il cappello
        g1 = PARETE + 1.9
        m += (v5.rett_arrotondato(x0 + PARETE - 0.1, x1 - PARETE + 0.1, y0 + PARETE - 0.1, y1 - PARETE + 0.1, R_SPIG - PARETE, self.Z_TAGLIO, self.Z_TAGLIO + 1.6)
              - v5.rett_arrotondato(x0 + g1, x1 - g1, y0 + g1, y1 - g1, 1.0, self.Z_TAGLIO - 1, self.Z_TAGLIO + 2))   # aggancia il bordino al cappello
        # righine orizzontali sul cappello
        z = self.Z_TAGLIO + 4.0
        while z + 1.0 < self.H - R_TOP:
            m -= (v5.rett_arrotondato(x0 - 1, x1 + 1, y0 - 1, y1 + 1, R_SPIG + 1, z, z + 1.0)
                  - v5.rett_arrotondato(x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, R_SPIG - 0.4, z - 1, z + 2))
            z += 2.4
        # nicchia aperta davanti e di lato (come una macchina del caffe')
        m -= scatola(self.CUP["x0"] - 0.6, x1 + 1, y0 - 1, y1 + 1, self.Z_PIEDE - 0.5, self.Z_NICCHIA)
        m += scatola(self.CUP["x0"] - 2.6, self.CUP["x0"] - 0.6, y0 + 0.01, y1 - 0.01, self.Z_PIEDE, self.Z_NICCHIA + 0.01)   # fondo della nicchia: a 0,6 mm dal bicchierino
        # scivolo a 45 gradi sopra il bicchierino: le pillole che sbattono sulla parete tornano dentro (6 mm sopra il bordo: il bicchierino si solleva e si sfila)
        za = self.Z_CUP + self.CUP["alt"] + 6.0; xa = self.CUP["x0"] - 0.6
        zn = self.Z_NICCHIA + 0.01      # lo scivolo sale a 45 gradi fino al tetto della nicchia: fa anche da squadretta che irrigidisce l'angolo
        scivolo = CrossSection([ccw([(xa - 0.01, za), (self.CUP["x0"] + 3.5, za), (self.CUP["x0"] + 3.5 + (zn - za), zn), (xa - 0.01, zn)])])
        m += Manifold.extrude(scivolo, 2 * self.CUP["y"]).translate([0, 0, -self.CUP["y"]]).transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
        # squadrette ai lati della nicchia (fuori dal bicchierino): l'angolo tra colonna e sbalzo non si piega
        sq = CrossSection([ccw([(xa - 0.01, self.Z_NICCHIA + 0.01), (xa + 16.0, self.Z_NICCHIA + 0.01), (xa - 0.01, self.Z_NICCHIA - 16.0)])])
        for yy in (y0 + 0.01, y1 - 1.6 - 0.01):
            m += Manifold.extrude(sq, 1.6).translate([0, 0, yy]).transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
        m += scatola(self.CUP["x0"] - 2.6, x1, y0 + 0.01, y1 - 0.01, self.Z_NICCHIA, self.Z_NICCHIA + PARETE) - scatola(-14, 16, -13, 13, self.Z_NICCHIA - 1, self.Z_NICCHIA + 3)   # tetto della nicchia, con il passaggio
        # sedi delle cassette
        if self.ruote == 2:
            for s in (-1, 1):
                ys = sorted((s * 1.0, s * 40))
                m -= cil_y(self.R_CASS + 0.4, ys[0], ys[1], 0, self.Z_A) - (scatola(-100, 100, -1.0, 1.0, 0, 300) if False else Manifold())
                ys2 = sorted((s * (self.Y0 + self.Z_FL[0] - 0.01), s * 40))
                m -= cil_y(self.R_CASS + 1.4, ys2[0], ys2[1], 0, self.Z_A)
            m += (scatola(-self.X_HALF + 1, self.X_HALF - 8.0, -0.95, 0.95, self.Z_IMB0 + 2.2, self.H - 1.0) ^ self._profilo(PARETE - 0.5)) - cil_y(6.0, -2, 2, 0, self.Z_A) \
                 - scatola(self.X_TASTO - 10.5, self.X_TASTO + 10.5, -2, 2, self.H - PARETE - 11.5, self.H) \
                 - scatola(self.X_TASTO - 13.6, self.X_TASTO + 13.6, -2, 2, self.H - PARETE - 2.0, self.H)
        else:
            m -= cil_y(self.R_CASS + 1.4, -40, self.Z_FL[1] + 0.4, 0, self.Z_A)
        # culle sotto le cassette (meta' di sotto), con il passaggio dell'uscita
        culla = cil_y(self.R_CASS + 2.8, y0 + PARETE - 0.01, y1 - PARETE + 0.01, 0, self.Z_A) - cil_y(self.R_CASS + 1.4, y0, y1, 0, self.Z_A) - scatola(-100, 100, -100, 100, self.Z_A - 8, 400)
        culla -= scatola(-self.APRE - 3.6, self.APRE + 3.6, -100, 100, 0, self.Z_A)   # la culla arriva fino all'imbuto: nessuna fessura dove una pillola si incastra
        m += culla
        for c in self.motori():
            b = c.bounding_box(); m -= scatola(b[0] - 1, b[3] + 1, b[1] - 1, b[4] + 1, b[2] - 1, b[5] + 1)
        cb = self.cella().bounding_box()
        m += scatola(cb[0], cb[0] + 15.0, cb[1], cb[4], self.Z_NICCHIA + PARETE - 0.01, cb[2])   # appoggio della cella (lato fisso)
        # display davanti in alto, luce, USB-C, griglia del cicalino
        m -= scatola(x1 - PARETE - 1, x1 + 1, self.Y_MID - 12, self.Y_MID + 12, self.Z_DISP[0] + 6, self.Z_DISP[1] - 6)
        m += self.supporti_motori()                                                            # fascette dei motorini, attaccate alla parete centrale
        m -= cil(self.R_TASTO + 0.4, self.H - 7, self.H + 1, self.X_TASTO, 0)                    # foro del tasto
        if self.ruote == 2:   # canale dei cavi dentro la parete centrale (fili da 0,5 mm in fila), aperto in basso e in alto
            m -= scatola(self.X_CANALE - 4, self.X_CANALE + 4, -0.5, 0.5, self.Z_IMB0, self.H - PARETE - 0.5)
            m -= scatola(self.X_CANALE - 4, self.X_CANALE + 4, -2, 2, self.Z_A + 38, self.H - PARETE - 0.5)
        # presa USB-C dietro, all'altezza della scheda ESP32
        zb = self.Z_PIATTO - 1.0 + Z_ESP
        m -= scatola(-self.X_HALF - 1, -self.X_HALF + PARETE + 1, -4.8, 4.8, zb + 0.4, zb + 4.6)
        # sensore di Hall nella parete dietro la nicchia, all'altezza del magnete del bicchierino
        m -= cil_x(2.4, self.CUP["x0"] - 3.1, self.CUP["x0"] - 1.2, 0, self.Z_CUP + 6.0)
        xa = x1 - PARETE
        m += cil_x(11.4, xa - 4.0, xa + 0.01, 0, self.Z_SUONO) - cil_x(10.25, xa - 5, xa + 1, 0, self.Z_SUONO)   # anello che tiene l'altoparlante
        for dy, dz in [(0, 0)] + [(5.5 * math.cos(math.radians(a)), 5.5 * math.sin(math.radians(a))) for a in range(0, 360, 60)]:
            m -= cil_x(1.1, xa - 1, x1 + 1, dy, self.Z_SUONO + dz)                                # griglia del suono
        if self.ruote == 2:
            zs = self.Z_A - R_MAGNETE
            for sy in (-1, 1):
                y0s, y1s = sorted((sy * 0.25, sy * 0.96)); y0g, y1g = sorted((sy * 0.7, sy * 0.96))
                m -= scatola(-1.6, 1.6, y0s, y1s, zs - 1.6, zs + 1.6)                                 # sede del sensore di Hall della ruota
                m -= scatola(self.X_CANALE + 3.0, 0.0, y0g, y1g, zs - 0.75, zs + 0.75)               # scanalatura per la striscia flessibile
            m -= scatola(self.X_CANALE + 2.5, self.X_CANALE + 4.5, -0.96, 0.96, zs - 0.75, zs + 0.75)   # entra nel canale dei cavi
            rc, xc, yc = self._fermo_pos()
            for sd in (-1, 1):
                m -= self.metti(self._servo_fermo_locale(0.3), sd)                                      # posto per il servo del fermo
                m -= self.metti(cil(7.9, self.Z_FL[0] - 0.7, self.Z_FL[1] + 0.4, xc, yc) + ruota(scatola(self.R_CASS - 1.0, rc, -2.2, 2.2, self.Z_FL[0] - 0.4, self.Z_FL[1] + 0.4), ANG_FERMO), sd)   # spazio per il dente che gira
                m += self.metti(self._staffa_fermo_locale(), sd)
        self._corpo = m
        return m

    X_TASTO = 0.0;  X_CANALE = -42.0; R_TASTO = 10.5      # tasto tondo da 21 mm sul tetto, davanti (dove la ruota curva e lascia spazio)
    def tasto(self):
        """Il tasto stampato: cupoletta che sporge 3 mm, bordino sotto il tetto che lo trattiene, perno che preme l'interruttore."""
        hr = self.H - PARETE
        m = cil(self.R_TASTO, hr - 1.6, self.H + 2.0, self.X_TASTO, 0)
        m += Manifold.sphere(self.R_TASTO, 48).scale([1, 1, 0.12]).translate([self.X_TASTO, 0, self.H + 2.0])
        m += cil(self.R_TASTO + 2.5, hr - 1.6, hr - 0.3, self.X_TASTO, 0) + cil(2.0, hr - 4.6, hr - 1.59, self.X_TASTO, 0)
        return m

    def interruttore(self):
        """Pulsantino 12 x 12 su una schedina 20 x 20, appoggiata sulla parete centrale."""
        hr = self.H - PARETE; x = self.X_TASTO
        return (scatola(x - 6, x + 6, -6, 6, hr - 9.9, hr - 6.4) + cil(1.75, hr - 6.4, hr - 4.9, x, 0)
                + scatola(x - 10, x + 10, -10, 10, hr - 11.5, hr - 9.9))

    def display(self):
        x1 = self.X_HALF
        return scatola(x1 - PARETE - 4.2, x1 - PARETE - 0.2, self.Y_MID - 17.7, self.Y_MID + 17.7, self.Z_DISP[0], self.Z_DISP[1] - 1.5)

    def schede(self):
        """Sotto: modulo DRV8833 (18,5 x 16,5, comanda tutti e due i motorini). Sopra: ESP32-S3 SuperMini (22,5 x 18),
        USB-C verso dietro e antenna verso il vuoto davanti."""
        z = self.Z_PIATTO - 1.0
        xb = -self.X_HALF + PARETE + 0.5
        return scatola(xb, xb + 18.5, -8.25, 8.25, z, z + 4) + scatola(xb, xb + 18.0, -11.25, 11.25, z + Z_ESP, z + Z_ESP + 4.5)

    def antenna(self):
        """Zona dell'antenna dell'ESP32 (ultimi 4 mm della scheda): niente metallo entro 10 mm."""
        z = self.Z_PIATTO - 1.0 + Z_ESP; xb = -self.X_HALF + PARETE + 0.5
        return scatola(xb + 14.0, xb + 18.0, -6, 6, z, z + 4.5)

    Z_SUONO = 68.0
    def altoparlante(self):
        """Altoparlante da 20 mm (8 ohm, 1 W) dietro la griglia davanti: suona e puo' dire "E' ora delle pillole"."""
        x1 = self.X_HALF - PARETE
        return cil_x(10.0, x1 - 4.5, x1 - 0.05, 0, self.Z_SUONO)

    def amplificatore(self):
        """Amplificatore I2S MAX98357A (18 x 18 mm), appoggiato sul tetto della nicchia."""
        z = self.Z_NICCHIA + PARETE + 0.1
        return scatola(26.0, 44.0, -9.0, 9.0, z, z + 3.0)

    # ---------------- cavi (fili siliconati da 0,5 mm, a mazzetti) e alimentazione
    def spina_usb(self):
        z = self.Z_PIATTO - 1.0 + Z_ESP + 2.5
        return scatola(-self.X_HALF - 17.0, -self.X_HALF - 0.3, -5.5, 5.5, z - 3.5, z + 3.5)

    def cavi(self):
        """Percorsi dei cavi: (nome, colore, raggio del mazzetto, punti, componenti a cui si attacca)."""
        H = self.H; zc = H - PARETE - 1.7                 # i cavi di sopra corrono sotto il tetto, sopra i motorini
        ze = self.Z_PIATTO - 1.0 + Z_ESP                  # fondo dell'ESP32
        zd = self.Z_PIATTO - 1.0                          # fondo della scheda dei driver
        xc = self.X_CANALE
        mot = lambda a: (lambda r: (r * math.cos(math.radians(a)), self.Z_A + r * math.sin(math.radians(a))))
        m1, m1e = mot(ANG_MOT[self.k][0])(self.R_GP + R_PIGNONE), mot(ANG_MOT[self.k][0])(self.R_GP + R_PIGNONE + 8.4)
        m2, m2e = mot(ANG_MOT[self.k][1])(self.R_GP + R_PIGNONE), mot(ANG_MOT[self.k][1])(self.R_GP + R_PIGNONE + 8.4)
        yw = self.Y_DX - PARETE - 2.6                   # i fili partono dai contatti del motorino (ultimi 4 mm, senza fascetta)
        m1, m2 = mot(ANG_MOT[self.k][0])(self.R_GP + R_PIGNONE + 5.9), mot(ANG_MOT[self.k][1])(self.R_GP + R_PIGNONE + 5.9)
        zf = self.Z_A + 50.0                            # i fili entrano nel canale da qui
        L = [
            ("motorino davanti", "#c0392b", 0.8, [(m1[0], yw, m1[1]), (m1e[0], yw, m1e[1]), (m1e[0], 16, zc), (xc + 1, 16, zc), (xc - 1.5, 0.9, zf)], ["motore_1"]),
            ("motorino dietro", "#c0392b", 0.8, [(m2[0], -yw, m2[1]), (m2e[0], -yw, m2e[1]), (m2e[0], -19.5, zc), (xc + 1, -19.5, zc), (xc - 2.5, -0.9, zf)], ["motore_2"]),
            ("display", "#2f6fd0", 1.0, [(48.8, 0, 192.4), (48.8, -14.6, 193.2), (40, -14.6, zc - 1.5), (xc + 1, -14.6, zc), (xc + 0.5, -0.9, zf)], ["display"]),
            ("tasto", "#e0b400", 0.8, [(-10.5, 6, self.H - PARETE - 10.7), (-14, 7.4, self.H - PARETE - 7), (xc + 1, 7.4, zc), (xc + 2.5, 0.9, zf)], ["interruttore"]),
            ("servo", "#e67e22", 0.9, [(19.2, 10.8, 53.0), (19.2, 17.5, 53.0), (-29.5, 17.5, 53.0), (-31.6, 5.0, zd + 2.0)], ["servo", "schede"]),
            ("amplificatore", "#8e44ad", 1.1, [(25.4, 6.0, 49.3), (20.0, 20.4, 50.6), (-29.0, 20.4, 51.0), (-31.8, 8.0, ze + 2.2)], ["amplificatore", "schede"]),
            ("altoparlante", "#7f8c8d", 0.7, [(46.6, 5.0, 60.0), (44.8, 5.0, 52.0), (42.5, 5.0, 51.4)], ["altoparlante", "amplificatore"]),
            ("cella di carico", "#16a085", 1.0, [(-32.6, -17.9, 51.6), (-34.6, -17.9, 51.0), (-34.6, -15.0, 46.0), (-33.0, -13.0, 43.6)], ["cella", "hx711"]),
            ("HX711 - ESP32", "#16a085", 0.8, [(-48.0, -10.0, 43.6), (-48.0, -10.0, 55.0), (-48.0, -11.9, ze + 0.8)], ["hx711", "schede"]),
            ("sensore del bicchiere", "#34495e", 0.8, [(self.CUP["x0"] - 3.8, 0, self.Z_CUP + 6.0), (-40.0, 0, self.Z_CUP + 12.0), (-40.0, 0, zd - 1.0)], ["sensore_bicchiere", "schede"]),
            ("servo del fermo sinistro", "#e67e22", 0.8, [(36.0, -14.5, 68.4), (33.0, -15.5, 58.0), (-29.0, -15.5, 58.0), (-31.6, -6.0, zd + 2.0)], ["servo_fermo_sx", "schede"]),
            ("servo del fermo destro", "#e67e22", 0.8, [(36.0, 14.5, 68.4), (33.0, 15.5, 58.0), (-29.0, 15.5, 58.0), (-31.6, 6.0, zd + 2.6)], ["servo_fermo_dx", "schede"]),
            ("orologio con pila (RTC)", "#9b59b6", 0.7, [(-41.0, 13.0, 34.6), (-41.0, 13.0, 50.0), (-45.0, 7.6, zd - 0.8)], ["rtc", "schede"]),
            ("alimentazione USB-C", "#1b1b1b", 1.75, [(-self.X_HALF - 17.0, 0, ze + 2.5), (-self.X_HALF - 32.0, 0, ze + 2.5), (-self.X_HALF - 44.0, 0, ze - 14.0), (-self.X_HALF - 50.0, 0, 1.75)], ["spina_usb"]),
        ]
        return L

    def nastro(self):
        """I fili di sopra scendono in fila dentro il canale della parete centrale fino all'ESP32 e ai driver."""
        ze = self.Z_PIATTO - 1.0 + Z_ESP
        return scatola(self.X_CANALE - 3.0, self.X_CANALE + 3.0, -0.4, 0.4, ze + 4.6, self.Z_A + 50.0)

    @staticmethod
    def tubo(punti, r):
        m = Manifold()
        sf = [Manifold.sphere(r, 16).translate(list(p)) for p in punti]
        for a, b in zip(sf, sf[1:]): m += Manifold.batch_hull([a, b])
        return m

    def sensore_bicchiere(self):
        """Sensore di Hall (DRV5032) nella parete dietro la nicchia: vede il magnete del bicchierino a 3-4 mm."""
        return cil_x(2.0, self.CUP["x0"] - 3.0, self.CUP["x0"] - 1.3, 0, self.Z_CUP + 6.0)

    # ---------------- tutto
    def pezzi(self):
        P = {"1_guscio": self.guscio(), "2_cappello": self.cappello(), "3_piede": self.piede(), "4_imbuto": self.imbuto(),
             "5_piattino": self.piattino(), "6_staffa_cella": self.staffa_cella(), "7_bicchierino": self.bicchierino(),
             "12_tasto": self.tasto()}
        if self.ruote == 2:
            for s, n in ((-1, "sx"), (1, "dx")):
                P["9_cassetta_" + n] = self.metti(self.cassetta_locale(), s)
                P["10_ruota_" + n] = self.metti(self.ruota_locale(), s)
                P["10_spazzole_" + n] = self.metti(self.spazzole_locale(), s)
                P["10_sportellini_" + n] = self.metti(self.sportellini_locale(), s)
                P["10_tappo_mozzo_" + n] = self.metti(self.tappo_locale(), s)
                P["13_fermo_" + n] = self.fermo(s)
        else:
            P["9_cassetta"] = self.metti(self.cassetta_locale(), 0)
            P["10_ruota_doppia"] = self.metti(self.ruota_locale(), 0)
            P["11_coperchio_sx"] = self.metti(self.coperchio_locale(1), 0)
            P["11_coperchio_dx"] = self.metti(self.coperchio_locale(-1), 0)
        return P

    def componenti(self):
        C = {"cella": self.cella(), "servo": self.servo(), "display": self.display(), "schede": self.schede(),
             "piastra_acciaio": self.piastra_acciaio(), "sensore_bicchiere": self.sensore_bicchiere(), "interruttore": self.interruttore(), "altoparlante": self.altoparlante(), "amplificatore": self.amplificatore(), "spina_usb": self.spina_usb()}
        if self.ruote == 2:
            zs = self.Z_A - R_MAGNETE
            C["sensori_ruote"] = scatola(-1.5, 1.5, 0.3, 0.95, zs - 1.5, zs + 1.5) + scatola(-1.5, 1.5, -0.95, -0.3, zs - 1.5, zs + 1.5)
            C["strisce_sensori"] = scatola(self.X_CANALE + 3.0, -1.5, 0.71, 0.95, zs - 0.7, zs + 0.7) + scatola(self.X_CANALE + 3.0, -1.5, -0.95, -0.71, zs - 0.7, zs + 0.7)
            C["magneti_ruote"] = sum((self.metti(cil(1.5, self.Z_COR[0], self.Z_COR[0] + 1.0, 0, -R_MAGNETE), sd) for sd in (-1, 1)), Manifold())
            C["rtc"] = scatola(-51.3, -31.3, 6.0, 20.0, 28.0, 34.0)
            C["hx711"] = scatola(-50.5, -26.5, -21.0, -5.0, 40.0, 43.0)       # modulo HX711 piccolo (24 x 16), nella camera dietro, vicino alla cella
            C["servo_fermo_sx"] = self.servo_fermo(-1); C["servo_fermo_dx"] = self.servo_fermo(1)
            C["gel_silice"] = sum((self.metti(self.silice_locale(), sd) for sd in (-1, 1)), Manifold())
        for i, m in enumerate(self.motori()): C["motore_" + str(i + 1)] = m
        for i, (m, *_c) in enumerate(self.pignoni()): C["motore_" + str(i + 1) + "_pignone"] = m
        return C

    def misure(self):
        return (2 * self.X_HALF, self.Y_DX - self.Y_SX, self.H)

VERSI = {"giu'": (0, 0, -1), "su": (0, 0, 1), "dietro": (-1, 0, 0), "davanti": (1, 0, 0), "sinistra": (0, -1, 0), "destra": (0, 1, 0)}
def stampa(mesh):
    """Sceglie il verso di stampa con meno sbalzi (facce che guardano in giu' oltre 45 gradi, non appoggiate al piano).
    Ritorna (nome del verso, area da sostenere in cm2, mesh ruotata e appoggiata a z=0)."""
    import numpy as np
    meglio = None
    for nome, d in VERSI.items():
        d = np.array(d, float)
        R = trimesh.geometry.align_vectors(d, [0, 0, -1])
        m = mesh.copy(); m.apply_transform(R); m.apply_translation([0, 0, -m.bounds[0][2]])
        n, c, a = m.face_normals, m.triangles_center, m.area_faces
        sbalzo = (n[:, 2] < -0.7071) & (c[:, 2] > 0.3)
        area = a[sbalzo].sum() / 100.0
        if meglio is None or area < meglio[1] - 0.05: meglio = (nome, area, m)
    return meglio

def genera(chiave, cartella):
    M = Modello(chiave); P = M.pezzi(); C = M.componenti()
    for d in ("stampa", "assieme", "componenti"):
        dd = os.path.join(cartella, d); os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd): os.remove(os.path.join(dd, f))
    for n, m in P.items():
        mesh = a_mesh(m); mesh.export(os.path.join(cartella, "assieme", n + ".stl"))
        verso, area, st = stampa(mesh); b = st.bounds; st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, 0]); st.export(os.path.join(cartella, "stampa", n + ".stl"))
    for n, m in C.items(): a_mesh(m).export(os.path.join(cartella, "componenti", n + ".stl"))
    return M, P, C

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    for k in ("2m",):
        M, P, C = genera(k, os.path.join(qui, "..", "v8", k, "stl"))
        x, y, z = M.misure()
        print(f"== {k}: {M.nome}: corpo {x:.0f} x {y:.0f} x {z:.0f} mm = {x * y * z / 1e6:.2f} litri; piede {M.PIEDE['x1'] - M.PIEDE['x0']:.0f} x {2 * M.PIEDE['y']:.0f}; ruota Ø {2 * M.R_CASS:.0f}")
        for n, m in P.items(): print(f"   {n:22s} pezzi {len(m.decompose())}  {m.volume() / 1000:6.1f} cm3")
