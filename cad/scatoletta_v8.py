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
R_SPIG = 5.0     # raggio degli spigoli verticali del guscio
R_TOP = 14.0     # spigoli del tetto arrotondati (davanti e dietro), come una macchina del caffe'
L_TASCA = 24.0; PROF = 13.0; SP_DIV = 1.0; G = 0.4; PARETE = 2.0
MOD = 0.8; Z_PIGNONE = 26; R_PIGNONE = Z_PIGNONE * MOD / 2   # pignone grande (26 denti): cosi' il motorino sta fuori dalle cassette
N20 = dict(lato_a=12.0, lato_b=10.0, lungo=24.3 + 1.5, albero=3.0)   # motoriduttore N20 (senza encoder) + contatti
ANG_MOT = {"2m": (118.0, 140.0), "1m": (135.0,)}        # dove il pignone tocca la corona (gradi, da +X verso +Z): angolo dietro in alto

MODELLI = {
    "2m": dict(nome="Due ruote, due motorini", R_I=23.0, ruote=2, labbri=False),
    "1m": dict(nome="Una ruota doppia, un motorino", R_I=38.0, ruote=1, labbri=True),
}

def settore(r0, r1, a0, a1, z0, z1, n=24):
    pts = [(r0 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r0 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r1 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r1 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Manifold.extrude(CrossSection([ccw(pts)]), z1 - z0).translate([0, 0, z0])

class Modello:
    def __init__(self, chiave):
        p = MODELLI[chiave]; self.k = chiave; self.nome = p["nome"]
        self.R_I = p["R_I"]; self.R_O = self.R_I + L_TASCA; self.ruote = p["ruote"]; self.labbri = p["labbri"]
        self.R_GP = self.R_O + 2.4                       # raggio primitivo della corona
        self.R_GT = self.R_GP + MOD                      # punta dei denti
        self.R_AN_T = self.R_O + G; self.R_AN_G = self.R_GT + G   # dentro dell'anello: zona tasche / zona corona
        self.R_CASS = self.R_AN_G + 1.6
        self.APRE = 6.0 if self.labbri else 9.0           # mezza larghezza dell'uscita in basso
        if self.ruote == 2:
            self.Z_COR = (0.0, 2.4); self.Z_TAS = (2.4, 2.4 + PROF)       # locale: corona dietro, tasche davanti
        else:
            self.Z_COR = (-1.2, 1.2); self.Z_TAS = (1.2, 1.2 + PROF)      # corona in mezzo, tasche sui due lati
        self.TH = self.Z_TAS[1]
        self.Z_COP = (self.TH + 0.2, self.TH + 1.8); self.Z_FL = (self.Z_COP[1], self.Z_COP[1] + 1.6)
        # in Y
        if self.ruote == 2:
            self.Y0 = 1.0 + 2.0                          # parete centrale (|y|<1) + fondo della cassetta
            self.Y_PIGN = self.Y0 + sum(self.Z_COR) / 2
            self.Y_DX = -self.Y_PIGN + 2.0 + N20["lungo"] + PARETE + 0.4; self.Y_SX = -self.Y_DX
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
        self.Z_A = self.Z_IMB0 + self.R_CASS + 1.5 + 0.6
        self.Z_DISP = (self.Z_A + math.sqrt(max(0, (self.R_CASS + 1.9) ** 2 - (self.R_CASS - 3.8) ** 2)) + 0.5, 0)   # il display sta dove la ruota curva
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
        m += cil(self.R_GT, z0, z1)                       # corona (i denti sono disegnati come anello pieno)
        zs = [(self.Z_TAS[0], self.Z_TAS[1], 0.0)]
        if self.ruote == 1: zs.append((-self.Z_TAS[1], -self.Z_TAS[0], PASSO / 2))
        for a0, a1, off in zs:
            m += cil(self.R_I, a0 - 0.01, a1) - cil(self.R_I - 1.6, a0 - 1, a1 + 1) + cil(5.0, a0 - 0.01, a1)   # mozzo vuoto, leggero
            for k in range(4): m += ruota(scatola(4.5, self.R_I - 1.0, -0.8, 0.8, a0 - 0.01, a0 + 3.0), 45 + 90 * k)
            for k in range(N):
                a = -90.0 + off + PASSO / 2 + k * PASSO
                m += ruota(scatola(self.R_I - 0.5, self.R_O, -SP_DIV / 2, SP_DIV / 2, a0 - 0.01, a1), a)
            m += settore(self.R_I - 0.5, self.R_O, -90.0 + off - PASSO / 2, -90.0 + off + PASSO / 2, a0 - 0.01, a1)   # chiuso
            if self.labbri:                               # bordo con aperture larghe 12 mm: tra un'uscita e l'altra c'e' pieno
                lab = cil(self.R_O, a0 - 0.01, a1) - cil(self.R_O - 2.0, a0 - 1, a1 + 1)
                for k in range(1, N):
                    a = -90.0 + off + k * PASSO
                    lab -= ruota(scatola(self.R_O - 3, self.R_O + 1, -self.APRE, self.APRE, a0 - 1, a1 + 1), a)
                m += lab
        m -= cil(3.2, -50, 50)                            # foro per l'asse
        return m

    # ---------------- cassetta (locale)
    def cassetta_locale(self):
        lati = [1] if self.ruote == 2 else [1, -1]
        m = Manifold()
        zc0, zc1 = self.Z_COR
        if self.ruote == 2:
            m += cil(self.R_CASS, zc0 - 2.0, zc0 - 0.4)                                        # fondo
            m += cil(3.0, zc0 - 0.41, self.TH - 0.5)                                            # asse fisso
        m += cil(self.R_CASS, zc0 - (2.0 if self.ruote == 2 else 0.4), zc1 + 0.4) - cil(self.R_AN_G, zc0 - 1, zc1 + 1)   # anello della corona
        for s in lati:
            a0, a1 = (self.Z_TAS[0], self.Z_FL[0]) if s > 0 else (-self.Z_FL[0], -self.Z_TAS[0])
            m += cil(self.R_CASS, a0, a1) - cil(self.R_AN_T, a0 - 1, a1 + 1)                    # anello delle tasche
            fl = (self.Z_FL[0], self.Z_FL[1]) if s > 0 else (-self.Z_FL[1], -self.Z_FL[0])
            m += cil(self.R_CASS + 1.5, fl[0], fl[1]) - cil(self.R_AN_T - 3.0, fl[0] - 1, fl[1] + 1)
            m -= scatola(-self.APRE, self.APRE, -self.R_CASS - 2, -self.R_AN_T + 1, min(self.Z_TAS[0] * s, self.Z_TAS[1] * s), max(self.Z_TAS[0] * s, self.Z_TAS[1] * s))  # uscita in basso
        for a in ANG_MOT[self.k]:
            m -= ruota(scatola(self.R_AN_G - 2, self.R_CASS + 3, -7.5, 7.5, zc0 - 0.3, zc1 + 0.3), a)   # finestra per il pignone
            if self.ruote == 1:                                   # la cassetta esce verso -Y (locale +Z): il pignone passa in una scanalatura
                m -= ruota(scatola(self.R_GP - MOD - 0.6, self.R_CASS + 3, -7.5, 7.5, -self.Z_FL[1] - 1, zc1), a)
        return m

    def coperchio_locale(self, s=1):
        z0, z1 = self.Z_COP
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
                faccia = yp - s * 2.0                     # faccia del riduttore, il corpo va verso l'altro lato
                y0, y1 = sorted((faccia, faccia - s * N20["lungo"]))
            else:
                yp = 0.0; faccia = 2.0; y0, y1 = 2.0, 2.0 + N20["lungo"]
            corpo = ruota(scatola(r - N20["lato_b"] / 2, r + N20["lato_b"] / 2, -N20["lato_a"] / 2, N20["lato_a"] / 2, 0, 1), 0)
            corpo = scatola(-N20["lato_b"] / 2, N20["lato_b"] / 2, y0, y1, -N20["lato_a"] / 2, N20["lato_a"] / 2).rotate([0, -a, 0]).translate([x, 0, z])
            pign = cil_y(R_PIGNONE + MOD, yp - 1.3, yp + 1.3, x, z) + cil_y(N20["albero"] / 2, min(yp, faccia), max(yp, faccia), x, z)
            out.append(corpo + pign)
        return out

    def supporti_motori(self):
        m = Manifold()
        r = self.R_GP + R_PIGNONE
        for i, a in enumerate(ANG_MOT[self.k]):
            if self.ruote == 2:
                s = -1 if i == 0 else 1; y0, y1 = sorted((s * self.Y_PIGN - s * 4.0, s * self.Y_PIGN - s * 2.0 - s * N20["lungo"]))
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
        for x in (-larg - 1.6, larg): m += scatola(x, x + 1.6, -ye - 1.6, ye + 1.6, zb - 1.6, self.Z_IMB0 + 0.5)
        return m

    PIATTO = dict(x0=-11.0, x1=13.0, y=11.0)
    def lato_cerniera(self): return -1 if self.ruote == 2 else 1      # da che parte e' la cerniera della vaschetta

    def piattino(self, gradi=0.0):
        """Vaschetta pesata: si apre ruotando attorno a un bordo laterale (cerniera sulla staffa della cella)."""
        p = self.PIATTO; z = self.Z_PIATTO; s = self.lato_cerniera(); yh = s * (p["y"] + 1.0)
        m = scatola(p["x0"], p["x1"], -p["y"], p["y"], z, z + 1.2)
        m += scatola(p["x0"], p["x0"] + 1.2, -p["y"], p["y"], z, z + 5) + scatola(p["x1"] - 1.2, p["x1"], -p["y"], p["y"], z, z + 5)
        m += scatola(p["x0"], p["x1"], min(s * p["y"], s * (p["y"] - 1.2)), max(s * p["y"], s * (p["y"] - 1.2)), z, z + 5)
        m += cil_x(1.6, p["x0"] + 1.3, p["x1"] - 1.3, yh, z + 0.6)
        if gradi: m = m.translate([0, -yh, -(z + 0.6)]).rotate([s * gradi, 0, 0]).translate([0, yh, z + 0.6])
        return m

    def staffa_cella(self):
        p = self.PIATTO; z = self.Z_PIATTO; s = self.lato_cerniera(); yh = s * (p["y"] + 1.0)
        yc = sorted((s * (p["y"] - 0.5), s * (p["y"] + 12.0)))
        m = scatola(p["x0"] - 2.0, p["x1"] + 2.0, yc[0], yc[1], z - 2.8, z - 1.6) ^ scatola(-100, 100, min(yh, s * 30), max(yh, s * 30), -100, 400)
        for x0 in (p["x0"] - 2.0, p["x1"] + 0.4):
            m += scatola(x0, x0 + 1.6, min(yh - 2, yh + 2), max(yh - 2, yh + 2), z - 2.8, z + 2.4) - cil_x(1.65, x0 - 1, x0 + 3, yh, z + 0.6)
        return m

    def cella(self):
        p = self.PIATTO; z = self.Z_PIATTO; s = self.lato_cerniera()
        y = sorted((s * (p["y"] + 0.9), s * (p["y"] + 12.9)))
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
        m -= cil(3.1, z - 1, z + 1.6, 0, 0)                                                     # magnete 6 x 1,5 nella base
        return m

    def piede(self):
        p = self.PIEDE
        # piede largo e basso, con i fianchi inclinati (come la base di una lampada)
        m = Manifold.batch_hull([v5.rett_arrotondato(p["x0"], p["x1"], -p["y"], p["y"], 18, 0, 1.0),
                                 v5.rett_arrotondato(p["x0"] + 4, p["x1"] - 4, -p["y"] + 4, p["y"] - 4, 14, p["h"] - 0.01, p["h"])])
        m -= self._zavorra(0.3)                                                                 # tasca chiusa per la zavorra (si inserisce in pausa di stampa)
        m -= cil(3.0, 0.3, p["h"] + 1, 0, 0)                                                    # sensore di Hall sotto il bicchierino
        return m

    ZAVORRA = dict(lungo=104.0, largo=76.0, spess=6.0)    # piastra di ferro 104 x 76 x 6 mm, foro da 8 mm (~370 g)
    def _zavorra(self, g=0.0):
        z = self.ZAVORRA; xc = (self.PIEDE["x0"] + self.PIEDE["x1"]) / 2
        return scatola(xc - z["lungo"] / 2 - g, xc + z["lungo"] / 2 + g, -z["largo"] / 2 - g, z["largo"] / 2 + g, 1.2 - g, 1.2 + z["spess"] + g)

    def piastra_acciaio(self):
        return self._zavorra() - cil(4.0, 0, 9, 0, 0)

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
        m -= scatola(self.CUP["x0"] - 3, x1 + 1, y0 - 1, y1 + 1, self.Z_PIEDE - 0.5, self.Z_NICCHIA)
        m += scatola(self.CUP["x0"] - 5, self.CUP["x0"] - 3, y0 + 0.01, y1 - 0.01, self.Z_PIEDE, self.Z_NICCHIA + 0.01)   # fondo della nicchia
        m += scatola(self.CUP["x0"] - 5, x1, y0 + 0.01, y1 - 0.01, self.Z_NICCHIA, self.Z_NICCHIA + PARETE) - scatola(-14, 16, -13, 13, self.Z_NICCHIA - 1, self.Z_NICCHIA + 3)   # tetto della nicchia, con il passaggio
        # sedi delle cassette
        if self.ruote == 2:
            for s in (-1, 1):
                ys = sorted((s * 1.0, s * 40))
                m -= cil_y(self.R_CASS + 0.4, ys[0], ys[1], 0, self.Z_A) - (scatola(-100, 100, -1.0, 1.0, 0, 300) if False else Manifold())
                ys2 = sorted((s * (self.Y0 + self.Z_FL[0] - 0.01), s * 40))
                m -= cil_y(self.R_CASS + 1.9, ys2[0], ys2[1], 0, self.Z_A)
            m += (scatola(-self.X_HALF + 1, self.X_HALF - 8.0, -1.0, 1.0, self.Z_IMB0 + 2.2, self.H - 1.0) ^ self._profilo(PARETE - 0.5)) - cil_y(6.0, -2, 2, 0, self.Z_A) \
                 - scatola(self.X_TASTO - 10.5, self.X_TASTO + 10.5, -2, 2, self.H - PARETE - 11.5, self.H) \
                 - scatola(self.X_TASTO - 13.6, self.X_TASTO + 13.6, -2, 2, self.H - PARETE - 2.0, self.H)
        else:
            m -= cil_y(self.R_CASS + 1.9, -40, self.Z_FL[1] + 0.4, 0, self.Z_A)
        # culle sotto le cassette (meta' di sotto), con il passaggio dell'uscita
        culla = cil_y(self.R_CASS + 3.5, y0 + PARETE - 0.01, y1 - PARETE + 0.01, 0, self.Z_A) - cil_y(self.R_CASS + 1.9, y0, y1, 0, self.Z_A) - scatola(-100, 100, -100, 100, self.Z_A - 8, 400)
        culla -= scatola(-self.APRE - 5.0, self.APRE + 5.0, -100, 100, 0, self.Z_A)
        m += culla
        for c in self.motori():
            b = c.bounding_box(); m -= scatola(b[0] - 1, b[3] + 1, b[1] - 1, b[4] + 1, b[2] - 1, b[5] + 1)
        cb = self.cella().bounding_box()
        m += scatola(cb[0], cb[0] + 15.0, cb[1], cb[4], self.Z_NICCHIA + PARETE - 0.01, cb[2])   # appoggio della cella (lato fisso)
        # display davanti in alto, luce, USB-C, griglia del cicalino
        m -= scatola(x1 - PARETE - 1, x1 + 1, self.Y_MID - 12, self.Y_MID + 12, self.Z_DISP[0] + 6, self.Z_DISP[1] - 6)
        m -= scatola(-self.X_HALF - 1, -self.X_HALF + PARETE + 1, -4.5, 4.5, self.Z_NICCHIA + 4, self.Z_NICCHIA + 8)
        m -= cil(self.R_TASTO + 0.4, self.H - 7, self.H + 1, self.X_TASTO, 0)                    # foro del tasto
        self._corpo = m
        return m

    X_TASTO = 30.0; R_TASTO = 10.5      # tasto tondo da 21 mm sul tetto, davanti (dove la ruota curva e lascia spazio)
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
        """ESP32-S3 SuperMini, DRV8833, HX711, cicalino: dietro, sopra il tetto della nicchia."""
        z = self.Z_PIATTO - 1.0
        xb = -self.X_HALF + PARETE + 0.5
        return scatola(xb, xb + 18.0, -11.25, 11.25, z, z + 4.5) + scatola(xb, xb + 18.5, -8, 8, z + 5, z + 9) + cil(6.0, z + 9.5, z + 15, xb + 7, 0)

    def sensore_bicchiere(self):
        return cil(2.0, 0.6, 2.2, 0, 0)

    # ---------------- tutto
    def pezzi(self):
        P = {"1_guscio": self.guscio(), "2_cappello": self.cappello(), "3_piede": self.piede(), "4_imbuto": self.imbuto(),
             "5_piattino": self.piattino(), "6_staffa_cella": self.staffa_cella(), "7_bicchierino": self.bicchierino(),
             "8_supporti_motori": self.supporti_motori(), "12_tasto": self.tasto()}
        if self.ruote == 2:
            for s, n in ((-1, "sx"), (1, "dx")):
                P["9_cassetta_" + n] = self.metti(self.cassetta_locale(), s)
                P["10_ruota_" + n] = self.metti(self.ruota_locale(), s)
                P["11_coperchio_" + n] = self.metti(self.coperchio_locale(), s)
        else:
            P["9_cassetta"] = self.metti(self.cassetta_locale(), 0)
            P["10_ruota_doppia"] = self.metti(self.ruota_locale(), 0)
            P["11_coperchio_sx"] = self.metti(self.coperchio_locale(1), 0)
            P["11_coperchio_dx"] = self.metti(self.coperchio_locale(-1), 0)
        return P

    def componenti(self):
        C = {"cella": self.cella(), "servo": self.servo(), "display": self.display(), "schede": self.schede(),
             "piastra_acciaio": self.piastra_acciaio(), "sensore_bicchiere": self.sensore_bicchiere(), "interruttore": self.interruttore()}
        for i, m in enumerate(self.motori()): C["motore_" + str(i + 1)] = m
        return C

    def misure(self):
        return (2 * self.X_HALF, self.Y_DX - self.Y_SX, self.H)

def genera(chiave, cartella):
    M = Modello(chiave); P = M.pezzi(); C = M.componenti()
    for d in ("stampa", "assieme", "componenti"):
        dd = os.path.join(cartella, d); os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd): os.remove(os.path.join(dd, f))
    for n, m in P.items():
        mesh = a_mesh(m); mesh.export(os.path.join(cartella, "assieme", n + ".stl"))
        st = mesh.copy(); b = st.bounds; st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]]); st.export(os.path.join(cartella, "stampa", n + ".stl"))
    for n, m in C.items(): a_mesh(m).export(os.path.join(cartella, "componenti", n + ".stl"))
    return M, P, C

if __name__ == "__main__":
    qui = os.path.dirname(os.path.abspath(__file__))
    for k in ("2m",):
        M, P, C = genera(k, os.path.join(qui, "..", "v8", k, "stl"))
        x, y, z = M.misure()
        print(f"== {k}: {M.nome}: corpo {x:.0f} x {y:.0f} x {z:.0f} mm = {x * y * z / 1e6:.2f} litri; piede {M.PIEDE['x1'] - M.PIEDE['x0']:.0f} x {2 * M.PIEDE['y']:.0f}; ruota Ø {2 * M.R_CASS:.0f}")
        for n, m in P.items(): print(f"   {n:22s} pezzi {len(m.decompose())}  {m.volume() / 1000:6.1f} cm3")
