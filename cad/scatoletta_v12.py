#!/usr/bin/env python3
"""
Scatoletta Blistra v1.2 (dalla v1.0, modello "2m"), adattata ai pezzi che ci sono davvero:

  - 2 stepper 28BYJ-48 con 2 driver ULN2003 al posto dei motorini N20 e del DRV8833.
    Le due croci di Malta stanno a 126 gradi (dietro in alto) per tutte e due le ruote. Il pignone da 10 denti
    sta a 17,1 mm dal centro della croce, nella direzione 60 gradi; il centro dello stepper e' a 8 mm dal pignone,
    nella direzione 135 gradi. Faccia dello stepper a |y| 11,5, retro a 30,5; piastra di supporto a |y| 9,3-11,5
    con due viti M3 nelle alette. Pignone con mozzo da 9 mm e foro a doppio D (albero da 5 con piatti a 3).
  - lo ZERO di ogni ruota: un pulsantino 6 x 6 x 7 usato come finecorsa, premuto dal perno d'acciaio della croce
    quando l'ingranaggio e' a 60 gradi dal riposo (dentro il tratto in cui la ruota e' bloccata)
  - microservo SG90 da 9 g per il piattino pesato; display OLED 0,96" I2C; cicalino da 12 mm; ESP32-S3 SuperMini;
    una sola cella di carico (100 g) con HX711
  - via: orologio RTC, altoparlante e amplificatore, sensore di umidita' AHT20, seconda cella di carico.
    La canaletta della ricarica dall'alto e' fissa, incollata su due appoggi del guscio
  - cassette fissate con una vite M2,5: aletta sulla flangia, dado incastrato in un blocchetto del guscio,
    tacca nel fianco per far passare l'aletta e il cacciavite (al posto dei fermi col servo)
  - guscio piu' largo (Y_DX = 32,1) e 10 mm piu' alto (H = 217,6): la ricarica dall'alto sale di 10 mm,
    le pareti della canaletta scendono di 10 mm
  - nella camera dietro: i due ULN2003 in verticale contro la parete dietro, a sinistra, uno sopra l'altro;
    HX711 ed ESP32 a destra, presa USB-C all'altezza dell'ESP32; il nastro dei cavi parte da z 81

Assi: X davanti, Y destra-sinistra (asse delle ruote), Z in alto. mm.
"""
import math, os
from manifold3d import Manifold, CrossSection
import scatoletta_v10 as s10
import scatoletta_v5 as v5
from scatoletta_v3 import cil, scatola, cil_x, cil_y, ruota, ccw, a_mesh
from scatoletta_v10 import (N, PASSO, PARETE, R_SPIG, R_TOP, MOD, Z_PIGN_G, Z_CROCE, R_LOCK, D_ASSE, Z_TORRE,
                            G_FERMO, ANG_FERMO, ingranaggio, stampa, VERSI)

# il modello v1.2 si registra nelle tabelle della v1.0 con una chiave sua (la v1.0 non cambia)
K = "2m-v1.2"
s10.MODELLI[K] = dict(nome="Due ruote, due stepper 28BYJ-48 (v1.2)", R_I=23.0, ruote=2, labbri=False)
s10.ANG_CROCE[K] = (126.0, 126.0)           # le due croci di Malta, dietro in alto
s10.ANG_MOT[K] = (110.0, 110.0)             # (serve solo al costruttore della v1.0; i motori veri sono sotto)

D_PIGN, A_PIGN = 17.1, 60.0                 # pignone: distanza e direzione dal centro della croce
D_MOT, A_MOT = 8.0, 135.0                   # centro del corpo dello stepper: distanza e direzione dal pignone
STEP = dict(r=14.0, faccia=11.5, retro=30.5, alette=35.0, foro=4.2, albero=5.0, piatti=3.0, l_albero=10.0, boss=9.0, h_boss=1.5)
PIASTRA_Y = (9.3, 11.5)                     # piastra di supporto dello stepper (|y|)
HUB = dict(d=9.0, y0=5.6, y1=9.7, collo=7.0)   # mozzo del pignone: sopra il perno della croce, sotto la piastra
FC = dict(phi=60.0, punta=11.75, lato=6.0, corpo=3.5, stelo=3.5, d_stelo=3.5, yc=5.2)   # finecorsa 6 x 6 x 7
SG90 = dict(x0=18.0, sp=12.2, lungo=22.5, alto=22.7, alette=32.0, z_al=15.6, sp_al=2.5)
OLED = dict(largo=27.3, alto=27.8, sp=4.0)
ESP = dict(x0=-49.9, lungo=22.5, y0=11.5, largo=18.0, z=60.0)          # ESP32-S3 SuperMini, orizzontale, USB-C dietro
ULN = dict(y0=-30.0, largo=32.0, z=((9.8, 44.8), (45.3, 80.3)), x_pcb=-49.4, sp=15.0)   # 2 x ULN2003 (35 x 32 x 15)
HX = dict(y0=11.0, largo=16.0, z0=18.0, alto=24.0)                       # HX711 in verticale contro la parete dietro
Z_NASTRO = 81.0
VITE_C = dict(rv=5.0, d=2.5, foro=2.8, testa=4.5, h_testa=1.7, lungo=8.0, dado=5.0, h_dado=2.0)   # M2,5 x 8 della cassetta
Z_SUONO = 68.0
RA = dict(s10.RA); [RA.__setitem__(k, RA[k] + 10.0) for k in ("zb", "zt", "zp", "zh")]     # ricarica: tutto 10 mm piu' su
GIU_CANALETTA = 10.0

def esagono(af, z0, z1, x, y):
    r = af / math.sqrt(3)
    pts = [(x + r * math.cos(math.radians(30 + 60 * k)), y + r * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    return Manifold.extrude(CrossSection([ccw(pts)]), z1 - z0).translate([0, 0, z0])

def doppio_d(r, piatti, z0, z1, x, y):
    return cil(r, z0, z1, x, y) ^ scatola(x - piatti / 2, x + piatti / 2, y - r - 1, y + r + 1, z0 - 1, z1 + 1)


class Modello12(s10.Modello):
    def __init__(self, chiave="2m"):
        super().__init__(K)
        self.nome = s10.MODELLI[K]["nome"]
        self.Y_DX = 32.1; self.Y_SX = -self.Y_DX
        self.H = self.H + 10.0
        self.Y_MID = 0.0
        self.Z_DISP = (self.Z_DISP[0], self.Z_DISP[0] + OLED["alto"])
        self.PIEDE = dict(self.PIEDE, x0=-self.X_HALF - 3.0, y=56.0)    # piede piu' lungo dietro (3 mm) e piu' largo (2 mm): gli stepper stanno in alto dietro

    # ---------------- quote utili (coordinate locali della ruota: x = X, y = Z - Z_A, z = |Y| - Y0)
    def zl(self, ay): return ay - self.Y0
    def centro_croce(self, i=0):
        a = math.radians(s10.ANG_CROCE[K][i]); return self.C_GEN * math.cos(a), self.C_GEN * math.sin(a)
    def pos_pignone(self, i=0):
        dx, dy = self.centro_croce(i); return dx + D_PIGN * math.cos(math.radians(A_PIGN)), dy + D_PIGN * math.sin(math.radians(A_PIGN))
    def pos_stepper(self, i=0):
        px, py = self.pos_pignone(i); return px + D_MOT * math.cos(math.radians(A_MOT)), py + D_MOT * math.sin(math.radians(A_MOT))
    def alette_stepper(self, i=0):
        cx, cy = self.pos_stepper(i); a = math.radians(A_MOT + 90.0); h = STEP["alette"] / 2   # le alette stanno di traverso all'albero
        return [(cx + h * math.cos(a), cy + h * math.sin(a)), (cx - h * math.cos(a), cy - h * math.sin(a))]

    # ---------------- ruota: niente piu' magnete (lo zero lo trova il finecorsa)
    def ruota_locale(self, faccia_offset=0.0):
        m = super().ruota_locale(faccia_offset)
        return m + cil(1.56, self.Z_COR[0], self.Z_COR[0] + 1.06, 0, -s10.R_MAGNETE)   # tappa la sede del vecchio magnete

    # ---------------- cassetta: aletta con il foro della vite M2,5
    def cassetta_locale(self):
        m = super().cassetta_locale()
        rv = self.R_CASS + VITE_C["rv"]; f0, f1 = self.Z_FL
        al = scatola(self.R_CASS + 0.3, rv + 3.5, -3.5, 3.5, f0 - 0.8, f1) - cil(VITE_C["foro"] / 2, f0 - 2, f1 + 1, rv, 0)
        return m + ruota(al, ANG_FERMO)

    def _blocchetto_locale(self):
        """Blocchetto del guscio sotto l'aletta: dado M2,5 incastrato (si infila da fuori), foro della vite."""
        rv = self.R_CASS + VITE_C["rv"]; zt = self.Z_FL[0] - 0.95
        b = scatola(self.R_CASS + 1.5, rv + 5.0, -6.0, 6.0, zt - 7.15, zt)
        return ruota(b, ANG_FERMO)

    def _vuoti_vite_locale(self):
        rv = self.R_CASS + VITE_C["rv"]; zt = self.Z_FL[0] - 0.95; zd = zt - 4.65
        v = cil(VITE_C["foro"] / 2, zt - 8, zt + 0.1, rv, 0)                                        # foro della vite
        v += esagono(VITE_C["dado"] + 0.3, zd, zd + VITE_C["h_dado"] + 0.3, rv, 0)                 # sede del dado
        v += scatola(rv, rv + 8.0, -(VITE_C["dado"] + 0.3) / 2, (VITE_C["dado"] + 0.3) / 2, zd, zd + VITE_C["h_dado"] + 0.3)   # il dado entra da fuori
        v += scatola(self.R_CASS + 0.1, rv + 4.0, -4.0, 4.0, zt + 0.0, 45.0)                       # tacca: passano l'aletta e il cacciavite
        return ruota(v, ANG_FERMO)

    def viti_cassette(self):
        rv = self.R_CASS + VITE_C["rv"]; f1 = self.Z_FL[1]
        v = cil(VITE_C["d"] / 2, f1 - VITE_C["lungo"], f1, rv, 0) + cil(VITE_C["testa"] / 2, f1, f1 + VITE_C["h_testa"], rv, 0)
        return sum((self.metti(ruota(v, ANG_FERMO), sd) for sd in (-1, 1)), Manifold())

    def dadi_cassette(self):
        rv = self.R_CASS + VITE_C["rv"]; zd = self.Z_FL[0] - 0.95 - 4.65 + 0.15
        d = esagono(VITE_C["dado"], zd, zd + VITE_C["h_dado"], rv, 0) - cil(VITE_C["d"] / 2, zd - 1, zd + 3, rv, 0)
        return sum((self.metti(ruota(d, ANG_FERMO), sd) for sd in (-1, 1)), Manifold())

    # ---------------- croce di Malta, pignone e stepper
    def croce_driver_locale(self, i, phi=0.0):
        a = s10.ANG_CROCE[K][i]; dx, dy = self.centro_croce(i); px, py = self.pos_pignone(i)
        bgp = math.degrees(math.atan2(py - dy, px - dx))
        g = Manifold.extrude(ingranaggio(Z_CROCE, MOD, bgp + 180.0 / Z_CROCE + phi), 2.0).translate([dx, dy, -2.3])
        u = a + phi
        lock = cil(R_LOCK, -0.31, 1.85, dx, dy) - cil(self.R_GEN + 0.5, 0, 2.1, dx + self.C_GEN * math.cos(math.radians(u)), dy + self.C_GEN * math.sin(math.radians(u)))
        m = g + lock
        m -= cil(1.5, -2.4, 0.0, dx + self.R_MAN * math.cos(math.radians(u)), dy + self.R_MAN * math.sin(math.radians(u)))
        return m - cil(1.1, -3, 3, dx, dy)

    def pignone_locale(self, i, phi=0.0):
        px, py = self.pos_pignone(i); dx, dy = self.centro_croce(i)
        bpg = math.degrees(math.atan2(dy - py, dx - px))
        m = Manifold.extrude(ingranaggio(Z_PIGN_G, MOD, bpg - phi * Z_CROCE / Z_PIGN_G), 2.0).translate([px, py, -2.3])
        m += cil(HUB["collo"] / 2, -0.31, self.zl(HUB["y0"]) + 0.01, px, py)                       # collo: il perno della croce gli passa accanto
        m += cil(HUB["d"] / 2, self.zl(HUB["y0"]), self.zl(HUB["y1"]), px, py)                      # mozzo
        return m - doppio_d(STEP["albero"] / 2 + 0.05, STEP["piatti"] + 0.1, -3, 10, px, py)

    def pignoni(self, phi=0.0):
        out = []
        for i in range(2):
            s = -1 if i == 0 else 1; px, py = self.pos_pignone(i)
            out.append((self.metti(self.pignone_locale(i, phi), s), px, s * self.Y_PIGN, self.Z_A + py))
        return out

    def stepper_locale(self, i):
        cx, cy = self.pos_stepper(i); px, py = self.pos_pignone(i); zl = self.zl
        m = cil(STEP["r"], zl(STEP["faccia"]), zl(STEP["retro"]), cx, cy)
        (e1x, e1y), (e2x, e2y) = self.alette_stepper(i)
        al = Manifold.batch_hull([cil(3.5, zl(STEP["faccia"]), zl(STEP["faccia"] + 1.0), e1x, e1y), cil(3.5, zl(STEP["faccia"]), zl(STEP["faccia"] + 1.0), e2x, e2y)])
        al -= cil(STEP["foro"] / 2, 0, 40, e1x, e1y) + cil(STEP["foro"] / 2, 0, 40, e2x, e2y)
        m += al
        cop = ruota(scatola(10.0, 17.2, -7.3, 7.3, zl(STEP["faccia"] + 1.0), zl(STEP["retro"] - 0.5)), A_MOT).translate([cx, cy, 0])   # copricavi blu
        m += cop
        m += cil(STEP["boss"] / 2, zl(STEP["faccia"] - STEP["h_boss"]), zl(STEP["faccia"]) + 0.01, px, py)
        m += doppio_d(STEP["albero"] / 2, STEP["piatti"], zl(STEP["faccia"] - STEP["l_albero"]), zl(STEP["faccia"] - STEP["h_boss"]) + 0.01, px, py)
        return m

    def motori(self):
        return [self.metti(self.stepper_locale(i), -1 if i == 0 else 1) for i in range(2)]

    def viti_motori(self):
        m = Manifold(); zl = self.zl
        for i in range(2):
            v = Manifold()
            for ex, ey in self.alette_stepper(i):
                v += cil(1.25, zl(6.5), zl(STEP["faccia"] + 1.0), ex, ey) + cil(2.75, zl(STEP["faccia"] + 1.0), zl(STEP["faccia"] + 3.0), ex, ey)   # M3 x 6
            m += self.metti(v, -1 if i == 0 else 1)
        return m

    def _piastra_locale(self, i):
        """Piastra di supporto dello stepper (parte del cappello): appesa al tetto e alla parete dietro."""
        cx, cy = self.pos_stepper(i); px, py = self.pos_pignone(i); zl = self.zl
        z0, z1 = zl(PIASTRA_Y[0]), zl(PIASTRA_Y[1])
        (e1x, e1y), (e2x, e2y) = self.alette_stepper(i)
        p = Manifold.batch_hull([cil(15.0, z0, z1, cx, cy), cil(4.0, z0, z1, e1x, e1y), cil(4.0, z0, z1, e2x, e2y)])
        p += scatola(-25.0, -15.0, cy, self.H - self.Z_A - 0.6, z0, z1)                     # braccio fino al tetto
        p += scatola(-self.X_HALF + 0.5, cx - 8.0, 45.5, 53.0, z0, z1)                       # braccio fino alla parete dietro
        for ex, ey in ((e1x, e1y), (e2x, e2y)): p += cil(3.0, zl(7.0), z0 + 0.01, ex, ey)  # rinforzi per le viti
        p -= cil(self.R_CASS + 1.8, -5, 30)
        return p

    def _vuoti_piastra_locale(self, i):
        px, py = self.pos_pignone(i); zl = self.zl
        v = cil(5.2, zl(PIASTRA_Y[0]) - 0.5, zl(PIASTRA_Y[1]) + 0.5, px, py)                  # passa il mozzo, entra il boss
        v += scatola(px, px + 30.0, py - 5.2, py + 5.2, zl(PIASTRA_Y[0]) - 0.5, zl(PIASTRA_Y[1]) + 0.5)   # asola aperta davanti: lo stepper (col pignone) entra di lato, scorrendo indietro di 4 mm
        for ex, ey in self.alette_stepper(i): v += cil(1.3, zl(6.9), zl(PIASTRA_Y[1]) + 0.5, ex, ey)   # fori da 2,6 per le viti M3
        return v

    # ---------------- finecorsa (zero della ruota)
    def _fc_frame(self, m, i):
        dx, dy = self.centro_croce(i)
        return ruota(m, s10.ANG_CROCE[K][i] + FC["phi"]).translate([dx, dy, 0])

    def finecorsa_locale(self, i):
        zc = self.zl(FC["yc"]); h = FC["lato"] / 2; zl = self.zl
        c0 = FC["punta"] + FC["stelo"]
        m = cil_x(FC["d_stelo"] / 2, FC["punta"], c0 + 0.01, 0, zc) + scatola(c0, c0 + FC["corpo"], -h, h, zc - h, zc + h)
        return self._fc_frame(m, i)

    def _supporto_fc_locale(self, i):
        zl = self.zl
        return self._fc_frame(scatola(14.9, 22.0, -4.6, 4.6, zl(0.9), zl(9.0)), i)

    def _vuoti_fc_locale(self, i):
        zc = self.zl(FC["yc"]); h = FC["lato"] / 2 + 0.2; zl = self.zl
        c0 = FC["punta"] + FC["stelo"]
        v = scatola(c0 - 0.2, c0 + FC["corpo"] + 1.15, -h, h, zc - h, zc + h) + cil_x(2.0, 11.0, c0 + 0.1, 0, zc)
        v += scatola(c0 + FC["corpo"] - 0.4, c0 + FC["corpo"] + 1.15, -6.0, 0.0, zc - 0.8, zc + 0.8)   # canalino del cavo, esce in alto
        return self._fc_frame(v, i)

    def finecorsa(self, i): return self.metti(self.finecorsa_locale(i), -1 if i == 0 else 1)

    def punto_fc(self, i, xp, yp, ay):
        """Punto nel riferimento del finecorsa (xp radiale dalla croce, yp di traverso, |y|) -> mondo."""
        dx, dy = self.centro_croce(i); a = math.radians(s10.ANG_CROCE[K][i] + FC["phi"]); s = -1 if i == 0 else 1
        x = dx + xp * math.cos(a) - yp * math.sin(a); z = dy + xp * math.sin(a) + yp * math.cos(a)
        return (x, s * ay, self.Z_A + z)

    # ---------------- ricarica dall'alto: 10 mm piu' su, canaletta fissa
    def fondo(self, sd, a=0.0): return super().fondo(sd, a).translate([0, 0, 10.0])

    def staffa_alta(self):
        """Canaletta fissa: niente cella, sta incollata su due appoggi del guscio. Pareti 10 mm piu' lunghe verso il basso."""
        x0, x1, w, hy, zb, zt, yp, zp, yi = RA["x0"], RA["x1"], RA["w"], RA["hy"], RA["zb"], RA["zt"], RA["yp"], RA["zp"], RA["yi"]
        m = scatola(x0, x0 + w, -hy, hy, zb - GIU_CANALETTA, zt) + scatola(x1 - w, x1, -hy, hy, zb - GIU_CANALETTA, zt)
        m += scatola(x0, x1, -0.8, 0.8, zb, zt) + scatola(x0, x1, -yi + 0.2, yi - 0.2, zb, zb + 1.0)
        for sd in (-1, 1):
            ya = sorted((sd * (yp - 1.0), sd * hy))
            m += scatola(x0, x0 + w, ya[0], ya[1], zp - 1.2, zb + 0.01) + scatola(x1 - w, x1, ya[0], ya[1], zp - 1.2, zb + 0.01)
            yf = sorted((sd * yi, sd * (yi + 1.0)))
            m += scatola(x0, x0 + w + 0.6, yf[0], yf[1], zb + 1.01, zb + 1.4) + scatola(x1 - w - 0.6, x1, yf[0], yf[1], zb + 1.01, zb + 1.4)
            m -= cil_x(0.45, x0 - 1, x1 + 1, sd * yp, zp)
            ys = sorted((sd * 16.5, sd * 23.5))
            m += scatola(x1 + 0.2, 46.0, ys[0], ys[1], 208.5, 210.1)                         # appoggi (si incollano sul guscio)
        m += scatola(x1 + 0.2, x1 + 1.6, -23.5, 23.5, 209.0, zt)                              # piastra davanti
        for yc in (-20.0, 0.0, 20.0): m += scatola(x1 - 0.01, x1 + 0.21, yc - 2.6, yc + 2.6, 209.0, zt)
        return m

    def sportello_alto(self, s, theta=0.0):
        yh, zh = s * RA["yh"], RA["zh"]
        y0, y1 = sorted((s * (RA["yi"] + 0.2), s * (RA["yh"] - 0.8)))
        m = scatola(RA["x0"] + 0.9, RA["x1"] - 0.9, y0, y1, self.H - PARETE + 0.05, self.H - 0.05) + cil_x(0.8, RA["x0"] + 0.9, RA["x1"] - 0.9, yh, zh)
        m += scatola(31.6, 35.7, *sorted((s * (RA["yi"] + 0.6), s * (RA["yi"] + 2.6))), self.H - 0.06, self.H + 1.2)
        yd = sorted((yh - s * 0.1 - 0.5, yh - s * 0.1 + 0.5))
        m += scatola(33.0, 34.2, yd[0], yd[1], zh - RA["rho"], zh)
        if theta: m = m.translate([0, -yh, -zh]).rotate([-s * theta, 0, 0]).translate([0, yh, zh])
        return m

    def scivolo_alto(self, s):
        davanti = Manifold.extrude(CrossSection([ccw([(34.4, 175.0), (37.9, 178.5), (37.9, 179.5), (34.4, 176.0)])]), 14.0).translate([0, 0, 6.0])
        davanti = davanti.transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
        davanti += scatola(34.4, 37.9, 19.99, self.Y_DX - PARETE + 0.01, 178.0, 179.5) - cil_y(self.R_CASS + 1.6, 19, 40, 0, self.Z_A)   # braccio fino al fianco (piu' lontano)
        davanti += scatola(29.6, 37.9, 5.55, 6.3, 178.6, 181.2)
        return davanti if s > 0 else davanti.mirror([0, 1, 0])

    # ---------------- servo SG90, display, cicalino, schede
    def servo(self):
        z = self.Z_PIATTO - 6.0; x0, x1 = SG90["x0"], SG90["x0"] + SG90["sp"]; h = SG90["lungo"] / 2
        m = scatola(x0, x1, -h, h, z, z + SG90["alto"])
        za = z + SG90["z_al"]; m += scatola(x0, x1, -SG90["alette"] / 2, SG90["alette"] / 2, za, za + SG90["sp_al"])
        return m + cil(2.4, z + SG90["alto"] - 0.01, z + SG90["alto"] + 4.0, (x0 + x1) / 2, -h + 5.6)   # albero con la levetta

    def _colonnine_servo(self):
        za = self.Z_PIATTO - 6.0 + SG90["z_al"]; m = Manifold()
        for sy in (-1, 1):
            ys = sorted((sy * (SG90["lungo"] / 2 + 0.35), sy * SG90["alette"] / 2))
            m += scatola(24.0, SG90["x0"] + SG90["sp"], ys[0], ys[1], self.Z_NICCHIA + PARETE - 0.01, za - 0.05)
        return m

    def display(self):
        x1 = self.X_HALF; h = OLED["largo"] / 2
        return scatola(x1 - PARETE - 0.2 - OLED["sp"], x1 - PARETE - 0.2, self.Y_MID - h, self.Y_MID + h, self.Z_DISP[0], self.Z_DISP[0] + OLED["alto"])

    def cicalino(self):
        x1 = self.X_HALF - PARETE
        return cil_x(6.0, x1 - 9.5, x1 - 0.05, 0, Z_SUONO)

    def esp32(self):
        e = ESP; x1 = e["x0"] + e["lungo"]; z = e["z"]; y1 = e["y0"] + e["largo"]; yc = (e["y0"] + y1) / 2
        m = scatola(e["x0"], x1, e["y0"], y1, z, z + 1.0) + scatola(e["x0"] + 3.0, x1 - 1.0, e["y0"] + 1.0, y1 - 1.0, z + 1.0, z + 1.8)
        return m + scatola(e["x0"] - 0.4, e["x0"] + 7.4, yc - 4.5, yc + 4.5, z + 1.0, z + 4.2)   # presa USB-C

    def antenna(self):
        e = ESP; x1 = e["x0"] + e["lungo"]
        return scatola(x1 - 4.0, x1, e["y0"], e["y0"] + e["largo"], e["z"], e["z"] + 1.8)

    def uln2003(self, k):
        u = ULN; z0, z1 = u["z"][k]; y1 = u["y0"] + u["largo"]; xp = u["x_pcb"]
        return scatola(xp, xp + 1.6, u["y0"], y1, z0, z1) + scatola(xp + 1.6, xp + u["sp"] - 2.0, u["y0"] + 1.5, y1 - 1.5, z0 + 1.0, z1 - 1.0)

    def hx711(self):
        h = HX; xp = ULN["x_pcb"]; y1 = h["y0"] + h["largo"]
        return scatola(xp, xp + 1.6, h["y0"], y1, h["z0"], h["z0"] + h["alto"]) + scatola(xp + 1.6, xp + 3.0, h["y0"] + 1.0, y1 - 1.0, h["z0"] + 1.0, h["z0"] + h["alto"] - 1.0)

    def _guide_schede(self):
        """Costole con la scanalatura per le schede verticali contro la parete dietro, binari per l'ESP32."""
        xw = -self.X_HALF + PARETE - 0.01; xp = ULN["x_pcb"]; zf = self.Z_PIEDE + PARETE - 0.01
        m = Manifold(); v = Manifold()
        y0, y1 = ULN["y0"], ULN["y0"] + ULN["largo"]
        for ya, yb, sa, sb in ((self.Y_SX + PARETE - 0.01, y0 + 1.2, y0 - 0.2, y0 + 1.3), (y1 - 1.4, y1 + 1.2, y1 - 1.5, y1 + 0.2)):
            m += scatola(xw, xp + 2.8, ya, yb, zf, ULN["z"][1][1] + 0.2)
            v += scatola(xp - 0.2, xp + 1.8, sa, sb, ULN["z"][0][0] - 0.1, 200)   # la scheda di sopra appoggia su quella di sotto
        h0, h1 = HX["y0"], HX["y0"] + HX["largo"]
        for ya, yb, sa, sb in ((h0 - 1.2, h0 + 0.8, h0 - 0.2, h0 + 0.9), (h1 - 0.8, h1 + 1.2, h1 - 0.9, h1 + 0.2)):
            m += scatola(xw, xp + 2.8, ya, yb, zf, HX["z0"] + HX["alto"] + 0.5)
            v += scatola(xp - 0.2, xp + 1.8, sa, sb, HX["z0"] - 0.1, 200)
        e = ESP; z = e["z"]
        m += scatola(xw, -36.0, e["y0"] - 1.6, e["y0"] + 0.6, z - 3.0, z + 2.5)               # binario di sinistra
        m += scatola(xw, -30.0, e["y0"] + e["largo"] - 0.6, self.Y_DX - PARETE + 0.01, z - 3.0, z + 2.5)   # binario di destra (sul fianco)
        v += scatola(xw - 1, -29.0, e["y0"] - 0.2, e["y0"] + e["largo"] + 0.2, z - 0.1, z + 1.1)   # scanalatura per la scheda
        return m - v

    def spina_usb(self):
        yc = ESP["y0"] + ESP["largo"] / 2; z = ESP["z"] + 2.6
        return scatola(-self.X_HALF - 17.0, -self.X_HALF - 0.3, yc - 5.5, yc + 5.5, z - 3.5, z + 3.5)

    def interruttore(self):
        return super().interruttore()

    # ---------------- guscio (copia della v1.0 con le modifiche)
    def corpo(self):
        if getattr(self, "_corpo", None) is not None: return self._corpo
        x0, x1, y0, y1 = -self.X_HALF, self.X_HALF, self.Y_SX, self.Y_DX
        m = v5.rett_arrotondato(x0, x1, y0, y1, R_SPIG, self.Z_PIEDE, self.H) ^ self._profilo(0)
        m -= v5.rett_arrotondato(x0 + PARETE, x1 - PARETE, y0 + PARETE, y1 - PARETE, R_SPIG - PARETE, self.Z_PIEDE + PARETE, self.H) ^ self._profilo(PARETE)
        m += self._zona_cappello() - scatola(-200, 200, -200, 200, self.Z_TAGLIO, 400)
        g1 = PARETE + 1.9
        m += (v5.rett_arrotondato(x0 + PARETE - 0.1, x1 - PARETE + 0.1, y0 + PARETE - 0.1, y1 - PARETE + 0.1, R_SPIG - PARETE, self.Z_TAGLIO, self.Z_TAGLIO + 1.6)
              - v5.rett_arrotondato(x0 + g1, x1 - g1, y0 + g1, y1 - g1, 1.0, self.Z_TAGLIO - 1, self.Z_TAGLIO + 2))
        z = self.Z_TAGLIO + 4.0
        while z + 1.0 < self.H - R_TOP:
            m -= (v5.rett_arrotondato(x0 - 1, x1 + 1, y0 - 1, y1 + 1, R_SPIG + 1, z, z + 1.0)
                  - v5.rett_arrotondato(x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, R_SPIG - 0.4, z - 1, z + 2))
            z += 2.4
        # nicchia del bicchierino
        m -= scatola(self.CUP["x0"] - 0.6, x1 + 1, y0 - 1, y1 + 1, self.Z_PIEDE - 0.5, self.Z_NICCHIA)
        m += scatola(self.CUP["x0"] - 2.6, self.CUP["x0"] - 0.6, y0 + 0.01, y1 - 0.01, self.Z_PIEDE, self.Z_NICCHIA + 0.01)
        za = self.Z_CUP + self.CUP["alt"] + 6.0; xa = self.CUP["x0"] - 0.6; zn = self.Z_NICCHIA + 0.01
        sc = CrossSection([ccw([(xa - 0.01, za), (self.CUP["x0"] + 3.5, za), (self.CUP["x0"] + 3.5 + (zn - za), zn), (xa - 0.01, zn)])])
        m += Manifold.extrude(sc, 2 * self.CUP["y"]).translate([0, 0, -self.CUP["y"]]).transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
        sq = CrossSection([ccw([(xa - 0.01, self.Z_NICCHIA + 0.01), (xa + 16.0, self.Z_NICCHIA + 0.01), (xa - 0.01, self.Z_NICCHIA - 16.0)])])
        for yy in (y0 + 0.01, y1 - 1.6 - 0.01):
            m += Manifold.extrude(sq, 1.6).translate([0, 0, yy]).transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])
        m += scatola(self.CUP["x0"] - 2.6, x1, y0 + 0.01, y1 - 0.01, self.Z_NICCHIA, self.Z_NICCHIA + PARETE) - scatola(self.PIATTO["x0"] - 3, self.PIATTO["x1"] + 3, -self.PIATTO["y"] - 2, self.PIATTO["y"] + 2, self.Z_NICCHIA - 1, self.Z_NICCHIA + 3)
        # sedi delle cassette e parete centrale
        for s in (-1, 1):
            m -= cil_y(self.R_CASS + 0.4, *sorted((s * 1.0, s * 40)), 0, self.Z_A)
            m -= cil_y(self.R_CASS + 1.4, *sorted((s * (self.Y0 + self.Z_FL[0] - 0.01), s * 40)), 0, self.Z_A)
        m += (scatola(-self.X_HALF + 1, self.X_HALF - 8.0, -0.95, 0.95, self.Z_IMB0 + 2.2, self.H - 1.0) ^ self._profilo(PARETE - 0.5)) - cil_y(6.0, -2, 2, 0, self.Z_A) \
             - scatola(self.X_TASTO - 10.5, self.X_TASTO + 10.5, -2, 2, self.H - PARETE - 11.5, self.H) \
             - scatola(self.X_TASTO - 13.6, self.X_TASTO + 13.6, -2, 2, self.H - PARETE - 2.0, self.H)
        culla = cil_y(self.R_CASS + 2.8, y0 + PARETE - 0.01, y1 - PARETE + 0.01, 0, self.Z_A) - cil_y(self.R_CASS + 1.4, y0, y1, 0, self.Z_A) - scatola(-100, 100, -100, 100, self.Z_A - 8, 400)
        culla -= scatola(-self.APRE - 3.6, self.APRE + 3.6, -100, 100, 0, self.Z_A)
        m += culla
        # appoggio della cella della dose, display, tasto
        cb = self.cella().bounding_box()
        m += scatola(cb[0], cb[0] + 15.0, cb[1], cb[4], self.Z_NICCHIA + PARETE - 0.01, cb[2])
        m -= scatola(x1 - PARETE - 1, x1 + 1, self.Y_MID - 11.5, self.Y_MID + 11.5, self.Z_DISP[0] + 8.0, self.Z_DISP[0] + 20.0)   # finestra dell'OLED 0,96"
        m -= cil(self.R_TASTO + 0.4, self.H - 7, self.H + 1, self.X_TASTO, 0)
        # cicalino da 12 mm dietro la griglia davanti
        xa = x1 - PARETE
        m += cil_x(7.0, xa - 4.0, xa + 0.01, 0, Z_SUONO) - cil_x(6.15, xa - 5, xa + 1, 0, Z_SUONO)
        for dy, dz in [(0, 0)] + [(3.5 * math.cos(math.radians(a)), 3.5 * math.sin(math.radians(a))) for a in range(0, 360, 60)]:
            m -= cil_x(0.9, xa - 1, x1 + 1, dy, Z_SUONO + dz)
        # sensore di Hall del bicchierino
        m -= cil_x(2.4, self.CUP["x0"] - 3.1, self.CUP["x0"] - 1.2, 0, self.Z_CUP + 6.0)
        # ricarica dall'alto: fori degli sportellini, parete centrale tagliata, appoggi della canaletta fissa
        for sd in (-1, 1):
            m -= scatola(RA["x0"] + 0.7, RA["x1"] - 0.7, *sorted((sd * (RA["yi"] - 0.3), sd * 24.5)), self.H - PARETE - 1.0, self.H + 1)
            m += scatola(37.9, 46.0, *sorted((sd * 16.5, sd * (self.Y_DX - PARETE + 0.01))), 196.5, 208.5)
        m -= scatola(27.6, self.X_HALF - 1.0, -1.2, 1.2, 186.0, self.H - PARETE + 0.01)
        m += scatola(cb[3] - 4.5, cb[3] - 0.5, cb[1] + 0.5, cb[4] - 0.5, self.Z_NICCHIA + PARETE - 0.01, cb[2] - G_FERMO)
        # nuovi: piastre degli stepper, supporti dei finecorsa, blocchetti delle viti delle cassette, colonnine del servo, guide delle schede
        for i, sd in ((0, -1), (1, 1)):
            m += self.metti(self._piastra_locale(i), sd)
            m += self.metti(self._supporto_fc_locale(i), sd)
            m += self.metti(self._blocchetto_locale(), sd)
        m += self._colonnine_servo()
        m += self._guide_schede()
        # canale dei cavi nella parete centrale
        m -= scatola(self.X_CANALE - 4, self.X_CANALE + 4, -0.5, 0.5, self.Z_IMB0, self.H - PARETE - 0.5)
        m -= scatola(self.X_CANALE - 4, self.X_CANALE + 4, -2, 2, self.Z_A + 38, self.H - PARETE - 0.5)
        for i, sd in ((0, -1), (1, 1)):
            m -= self.metti(self._vuoti_piastra_locale(i) + self._vuoti_fc_locale(i) + self._vuoti_vite_locale(), sd)
        # presa USB-C dietro, all'altezza dell'ESP32
        yc = ESP["y0"] + ESP["largo"] / 2; zu = ESP["z"] + 1.0 + 1.6
        m -= scatola(-self.X_HALF - 1, -self.X_HALF + PARETE + 1, yc - 4.8, yc + 4.8, zu - 2.1, zu + 2.1)
        self._corpo = m
        return m

    # ---------------- cavi
    def cavi(self):
        """(nome, colore, raggio del mazzetto, punti, componenti a cui si attacca)"""
        xc = self.X_CANALE; zn = Z_NASTRO + 1.0
        L = []
        for i, sd, n in ((0, -1, "sinistro"), (1, 1, "destro")):
            cx, cy = self.pos_stepper(i); a = math.radians(A_MOT)
            ux, uz = cx + 16.2 * math.cos(a), self.Z_A + cy + 16.2 * math.sin(a)
            L.append(("stepper " + n, "#c0392b", 0.9, [(ux, sd * 21.0, uz), (xc - 0.3, sd * 21.0, uz + 1.2), (xc - 0.3, sd * 1.2, uz + 1.2), (xc, sd * 0.9, self.Z_A + 64.0)], ["motore_" + str(i + 1)]))
            p0 = self.punto_fc(i, FC["punta"] + FC["stelo"] + FC["corpo"] + 0.35, -1.0, FC["yc"])
            p1 = self.punto_fc(i, FC["punta"] + FC["stelo"] + FC["corpo"] + 0.35, -6.9, FC["yc"])
            L.append(("finecorsa " + n, "#e0b400", 0.7, [p0, p1, (p1[0], p1[1], p1[2] + 1.6), (xc - 0.5, sd * 1.3, p1[2] + 2.6), (xc, sd * 0.9, p1[2] + 5.0)], ["finecorsa_" + ("sx" if i == 0 else "dx")]))
        zd = self.Z_DISP[0] + OLED["alto"]
        L.append(("display", "#2f6fd0", 0.8, [(46.7, 0, zd - 1.4), (44.5, 0, zd + 2.1), (28.5, -1.9, zd + 3.2), (-8.0, -1.9, zd + 3.2), (-12.0, -1.9, 203.0), (xc + 1.0, -1.9, 203.0), (xc, -0.9, 195.0)], ["display"]))
        hr = self.H - PARETE
        L.append(("tasto", "#e0b400", 0.8, [(-10.4, 6.0, hr - 10.7), (-14.0, 6.0, hr - 9.2), (xc + 1.0, 6.0, hr - 9.2), (xc, 1.3, hr - 9.2), (xc, 0.9, hr - 18.0)], ["interruttore"]))
        # camera dietro
        L.append(("stepper sinistro - ULN2003 di sotto", "#c0392b", 0.9, [(xc, 0, zn + 0.5), (-34.0, -4.0, zn + 0.5), (-34.0, -8.0, 47.0), (-35.9, -12.0, 41.5)], ["uln2003_1"]))
        L.append(("stepper destro - ULN2003 di sopra", "#c0392b", 0.9, [(xc, 0, zn + 0.5), (-38.0, -6.0, zn + 0.3), (-35.9, -12.0, 76.5)], ["uln2003_2"]))
        L.append(("nastro - ESP32 (display, tasto, finecorsa)", "#2f6fd0", 0.8, [(xc + 1.0, 0.5, zn + 0.6), (-36.0, 6.0, 75.0), (-33.0, 12.0, ESP["z"] + 2.5)], ["esp32"]))
        L.append(("ULN2003 di sotto - ESP32", "#8e44ad", 0.8, [(-35.9, -2.0, 25.0), (-33.5, 4.0, 35.0), (-33.5, 8.0, 57.0), (-31.0, 12.0, ESP["z"] - 0.4)], ["uln2003_1", "esp32"]))
        L.append(("ULN2003 di sopra - ESP32", "#8e44ad", 0.8, [(-35.9, -2.0, 60.0), (-33.5, 5.0, 61.5), (-31.0, ESP["y0"] + 0.2, ESP["z"] + 1.0)], ["uln2003_2", "esp32"]))
        cb = self.cella().bounding_box()
        L.append(("cella di carico - HX711", "#16a085", 1.0, [(cb[0] - 0.4, -18.7, 51.6), (-32.5, -18.7, 51.6), (-32.5, -10.0, 45.0), (-32.5, 6.0, 32.0), (-46.0, 14.0, 30.0)], ["cella", "hx711"]))
        L.append(("HX711 - ESP32", "#16a085", 0.8, [(-46.0, 20.0, HX["z0"] + HX["alto"] - 0.5), (-45.5, 20.0, 50.0), (-45.5, 20.0, ESP["z"] - 0.6)], ["hx711", "esp32"]))
        L.append(("servo SG90", "#e67e22", 0.9, [(20.5, 11.6, 53.5), (20.5, 17.5, 53.5), (-27.0, 17.5, 53.5), (-29.0, 17.5, ESP["z"] - 0.4)], ["servo", "esp32"]))
        L.append(("cicalino", "#7f8c8d", 0.7, [(41.6, 3.5, Z_SUONO - 1.5), (36.0, 17.0, 57.0), (-27.0, 17.0, 57.0), (-29.3, 19.0, ESP["z"] - 0.3)], ["cicalino", "esp32"]))
        L.append(("sensore del bicchiere", "#34495e", 0.8, [(self.CUP["x0"] - 3.8, 0, self.Z_CUP + 6.0), (-33.0, 4.0, self.Z_CUP + 6.0), (-33.0, 7.0, 50.0), (-31.5, 11.5, ESP["z"] - 0.3)], ["sensore_bicchiere", "esp32"]))
        yc = ESP["y0"] + ESP["largo"] / 2; zu = ESP["z"] + 2.6
        L.append(("alimentazione USB-C", "#1b1b1b", 1.75, [(-self.X_HALF - 17.0, yc, zu), (-self.X_HALF - 32.0, yc, zu), (-self.X_HALF - 44.0, yc, zu - 14.0), (-self.X_HALF - 50.0, yc, 1.75)], ["spina_usb"]))
        return L

    def nastro(self):
        return scatola(self.X_CANALE - 3.0, self.X_CANALE + 3.0, -0.4, 0.4, Z_NASTRO, self.Z_A + 72.0)

    # ---------------- tutto
    def pezzi(self):
        P = super().pezzi()
        for n in ("13_fermo_sx", "13_fermo_dx"): P.pop(n, None)
        return P

    def componenti(self):
        C = {"cella": self.cella(), "servo": self.servo(), "display": self.display(), "esp32": self.esp32(), "hx711": self.hx711(),
             "uln2003_1": self.uln2003(0), "uln2003_2": self.uln2003(1), "piastra_acciaio": self.piastra_acciaio(),
             "sensore_bicchiere": self.sensore_bicchiere(), "interruttore": self.interruttore(), "cicalino": self.cicalino(), "spina_usb": self.spina_usb(),
             "gel_silice": sum((self.metti(self.silice_locale(), sd) for sd in (-1, 1)), Manifold()),
             "finecorsa_sx": self.finecorsa(0), "finecorsa_dx": self.finecorsa(1),
             "viti_cassette": self.viti_cassette(), "dadi_cassette": self.dadi_cassette(), "viti_motori": self.viti_motori()}
        for i, m in enumerate(self.motori()): C["motore_" + str(i + 1)] = m
        for i, (m, *_c) in enumerate(self.pignoni()): C["motore_" + str(i + 1) + "_pignone"] = m
        for i, (m, *_c) in enumerate(self.croci()): C["motore_" + str(i + 1) + "_croce"] = m
        C["viti_croce"] = self.viti_croce()
        C["assi_acciaio"] = sum((self.metti(cil(D_ASSE / 2 - 0.01, self.Z_COR[0] - 2.3, Z_TORRE + 10.0), sd) for sd in (-1, 1)), Manifold())
        return C


Modello = Modello12

def genera(chiave, cartella):
    M = Modello12(chiave); P = M.pezzi(); C = M.componenti()
    for d in ("stampa", "assieme", "componenti"):
        dd = os.path.join(cartella, d); os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd): os.remove(os.path.join(dd, f))
    def su_piano(mesh, nome):
        verso, area, st = stampa(mesh); b = st.bounds; st.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, 0])
        st.export(os.path.join(cartella, "stampa", nome + ".stl"))
    for n, m in P.items():
        mesh = a_mesh(m); mesh.export(os.path.join(cartella, "assieme", n + ".stl")); su_piano(mesh, n)
    for n, m in C.items(): a_mesh(m).export(os.path.join(cartella, "componenti", n + ".stl"))
    for i, lato in enumerate(("sx", "dx")):
        su_piano(a_mesh(M.croci(perno=False)[i][0]), "14_croce_" + lato)
        su_piano(a_mesh(M.pignoni()[i][0]), "15_pignone_" + lato)
    return M, P, C

if __name__ == "__main__":
    import zipfile
    qui = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(qui, "..", "v12")
    M, P, C = genera("2m", os.path.join(out, "stl"))
    x, y, z = M.misure()
    print(f"== {M.nome}: corpo {x:.1f} x {y:.1f} x {z:.1f} mm = {x * y * z / 1e6:.2f} litri; piede {M.PIEDE['x1'] - M.PIEDE['x0']:.0f} x {2 * M.PIEDE['y']:.0f}")
    for n, m in P.items(): print(f"   {n:22s} pezzi {len(m.decompose())}  {m.volume() / 1000:6.1f} cm3")
    st = os.path.join(out, "stl", "stampa")
    with zipfile.ZipFile(os.path.join(out, "blistra_v12_stampa.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(st)): z.write(os.path.join(st, f), os.path.join("blistra_v12_stampa", f))
    print("zip:", os.path.join(out, "blistra_v12_stampa.zip"))
