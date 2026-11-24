"""Pezzi dettagliati SOLO per il visore 3D (i controlli usano le scatole semplici di spill_v8).
Ogni pezzo e' diviso per materiale: il nome finisce con __<materiale del visore> (pcb, nero, ottone, metallo...).
Schede con chip, piedini e connettori; motorini N20 con riduttore e contatti; celle di carico con i fori e l'estensimetro;
viti con la filettatura vera (elica) e la testa Torx; magneti al neodimio."""
import math
from manifold3d import Manifold, CrossSection
from spill_v3 import cil, scatola, cil_x, cil_y
import spill_v8 as s8

def _star(r_out, r_in, n=6, seg=4):
    pts = []
    for k in range(n * seg * 2):
        a = math.pi * 2 * k / (n * seg * 2)
        r = r_out if (k // seg) % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return CrossSection([pts])

def vite(L, d=2.0, passo=0.4, testa=3.8, h_testa=1.3):
    """Vite lungo +Z con la testa in alto (z da 0 a h_testa) e il gambo sotto (fino a -L). Filetto: cerchio eccentrico ruotato."""
    giri = L / passo
    r = d / 2
    filetto = Manifold.extrude(CrossSection.circle(r * 0.78, 10).translate((r * 0.22, 0)), L, n_divisions=max(8, int(giri * 8)), twist_degrees=360 * giri)
    gambo = filetto.translate([0, 0, -L]) + cil(r * 0.62, -L, 0.01)
    t = cil(testa / 2, 0, h_testa) - Manifold.extrude(_star(testa * 0.24, testa * 0.15), 1.0).translate([0, 0, h_testa - 0.8])
    return gambo + t

def _posa(m, asse, pos):
    """La vite e' costruita lungo +Z (testa in alto); asse = direzione in cui guarda la testa."""
    if asse == "z": r = m
    elif asse == "-z": r = m.rotate([180, 0, 0])
    elif asse == "x": r = m.rotate([0, 90, 0])
    elif asse == "-x": r = m.rotate([0, -90, 0])
    elif asse == "y": r = m.rotate([-90, 0, 0])
    else: r = m.rotate([90, 0, 0])
    return r.translate(pos)

def _pins(x0, x1, y, z0, z1, n, lato=0.64):
    m = Manifold()
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        m += scatola(x - lato / 2, x + lato / 2, y - lato / 2, y + lato / 2, z0, z1)
    return m

def dettagli(M):
    D = {}
    n_vite = [0]
    def add(nome, mat, m):
        if nome == "viti": n_vite[0] += 1; nome = "viti_%d" % n_vite[0]     # una vite per pezzo: tante facce
        k = "d_" + nome + "__" + mat
        D[k] = D[k] + m if k in D else m
    z = M.Z_PIATTO - 1.0; xb = -M.X_HALF + s8.PARETE + 0.5; ze = z + s8.Z_ESP
    # ---- ESP32-S3 SuperMini (18 x 22,5), USB-C verso dietro, antenna davanti
    add("esp32", "nero", scatola(xb, xb + 18.0, -11.25, 11.25, ze, ze + 1.0))
    add("esp32", "nero", scatola(xb + 5.0, xb + 12.0, -3.5, 3.5, ze + 1.0, ze + 1.9))                     # chip ESP32-S3
    add("esp32", "metallo", scatola(xb - 0.8, xb + 6.5, -4.45, 4.45, ze + 1.0, ze + 4.2) - scatola(xb - 1, xb + 0.2, -3.6, 3.6, ze + 1.6, ze + 3.6))   # presa USB-C
    add("esp32", "ceramica", scatola(xb + 15.4, xb + 17.4, -3.0, 3.0, ze + 1.0, ze + 2.0))               # antenna ceramica
    add("esp32", "metallo", scatola(xb + 12.6, xb + 15.0, -6.5, -4.5, ze + 1.0, ze + 1.7))               # quarzo
    for yy in (-6.0, 6.0): add("esp32", "metallo", scatola(xb + 7.5, xb + 10.5, yy - 1.5, yy + 1.5, ze + 1.0, ze + 2.4))   # tasti BOOT e RESET
    for yy in (-10.0, 10.0):
        add("esp32", "nero", scatola(xb + 1.0, xb + 17.0, yy - 1.25, yy + 1.25, ze - 2.5, ze))           # strisce dei piedini
        add("esp32", "ottone", _pins(xb + 1.0, xb + 17.0, yy, ze - 6.0, ze + 1.4, 8))
    # ---- DRV8833 (18,5 x 16,5), sotto
    add("drv8833", "pcbBlu", scatola(xb, xb + 18.5, -8.25, 8.25, z, z + 1.2))
    add("drv8833", "nero", scatola(xb + 6.0, xb + 12.5, -2.2, 2.2, z + 1.2, z + 2.2))
    for xx in (xb + 3.0, xb + 15.0): add("drv8833", "arancio", scatola(xx - 1.0, xx + 1.0, 3.5, 6.5, z + 1.2, z + 2.6))   # condensatori
    for yy in (-7.0, 7.0): add("drv8833", "ottone", _pins(xb + 1.0, xb + 17.5, yy, z + 1.2, z + 3.6, 6))
    # ---- HX711 (24 x 16)
    hx = (-50.5, -26.5, -21.0, -5.0, 40.0)
    add("hx711", "pcb", scatola(hx[0], hx[1], hx[2], hx[3], hx[4], hx[4] + 1.2))
    add("hx711", "nero", scatola(-41.0, -31.0, -15.0, -11.0, hx[4] + 1.2, hx[4] + 2.8))
    for yy in (-15.6, -10.4): add("hx711", "metallo", _pins(-40.5, -31.5, yy, hx[4] + 1.2, hx[4] + 1.8, 8, 0.35))   # piedini del chip
    for xx in (-49.0, -28.0): add("hx711", "ottone", _pins(-20.0, -6.0, 0, 0, 0, 1) if False else Manifold())
    add("hx711", "ottone", _pins(hx[0] + 1.5, hx[0] + 2.5, -13.0, hx[4] + 1.2, hx[4] + 3.0, 1) + _pins(-30.0, -27.0, -13.0, hx[4] + 1.2, hx[4] + 3.0, 1))
    for k in range(4): add("hx711", "ottone", scatola(-28.2, -27.6, -19.0 + 3.6 * k, -18.4 + 3.6 * k, hx[4] + 1.2, hx[4] + 3.0))
    # ---- orologio DS3231 con la pila a bottone
    rt = (-51.3, -31.3, 6.0, 20.0, 28.0)
    add("rtc", "pcbBlu", scatola(rt[0], rt[1], rt[2], rt[3], rt[4], rt[4] + 1.2))
    add("rtc", "nero", scatola(-48.0, -40.0, 9.0, 16.0, rt[4] + 1.2, rt[4] + 2.6))
    add("rtc", "metallo", cil(5.0, rt[4] + 1.2, rt[4] + 4.0, -36.0, 13.0))                               # pila CR1220
    for k in range(4): add("rtc", "ottone", scatola(rt[0] + 1.0, rt[0] + 1.6, 8.0 + 2.54 * k, 8.6 + 2.54 * k, rt[4] + 1.2, rt[4] + 5.6))
    # ---- amplificatore MAX98357A
    za = M.Z_NICCHIA + s8.PARETE + 0.1
    add("amplificatore", "pcbBlu", scatola(26.0, 44.0, -9.0, 9.0, za, za + 1.2))
    add("amplificatore", "nero", scatola(33.5, 36.5, -1.5, 1.5, za + 1.2, za + 2.0))
    add("amplificatore", "arancio", scatola(39.0, 43.5, -5.0, 5.0, za + 1.2, za + 3.0))                 # morsetto dell'altoparlante
    add("amplificatore", "ottone", _pins(27.0, 43.0, -8.0, za + 1.2, za + 2.8, 7))
    # ---- motorini N20: riduttore (metallo), motore (ferro), tappo nero, contatti di ottone
    for i, a in enumerate(s8.ANG_MOT[M.k]):
        r = M.R_GP + s8.R_PIGNONE
        x, zc = r * math.cos(math.radians(a)), M.Z_A + r * math.sin(math.radians(a))
        s = -1 if i == 0 else 1; faccia = s * M.Y_PIGN - s * 1.3; L = s8.N20["lungo"]
        def tratto(d0, d1, la=s8.N20["lato_a"], lb=s8.N20["lato_b"]):
            ya, yb = sorted((faccia - s * d0, faccia - s * d1))
            return scatola(-lb / 2, lb / 2, ya, yb, -la / 2, la / 2).rotate([0, -a, 0]).translate([x, 0, zc])
        add("motore", "metallo", tratto(0, 9.0))
        add("motore", "ferro", (tratto(9.0, L - 3.5) ^ cil_y(6.0, -60, 60, x, zc)))
        add("motore", "nero", tratto(L - 3.5, L - 1.5, 9.0, 9.0))
        add("motore", "ottone", tratto(L - 1.5, L, 1.0, 6.0))
    # ---- celle di carico: barra di alluminio con i due fori uniti, estensimetro bianco, viti M2,5 filettate
    def cella(box, asse_lungo):
        x0, y0, z0, x1, y1, z1 = box
        m = scatola(x0, x1, y0, y1, z0, z1)
        if asse_lungo == "x":
            xm, ym, zm = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
            m -= cil_y(1.6, y0 - 1, y1 + 1, xm - 3, zm) + cil_y(1.6, y0 - 1, y1 + 1, xm + 3, zm) + scatola(xm - 3, xm + 3, y0 - 1, y1 + 1, zm - 0.9, zm + 0.9)
            gauge = scatola(xm - 3, xm + 3, ym - 3, ym + 3, z1, z1 + 0.8)
            viti = [(x0 + 4.0, ym), (x0 + 12.0, ym), (x1 - 12.0, ym), (x1 - 4.0, ym)]
        else:
            xm, ym, zm = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
            m -= cil_x(1.6, x0 - 1, x1 + 1, ym - 3, zm) + cil_x(1.6, x0 - 1, x1 + 1, ym + 3, zm) + scatola(x0 - 1, x1 + 1, ym - 3, ym + 3, zm - 0.9, zm + 0.9)
            gauge = scatola(xm - 3, xm + 3, ym - 3, ym + 3, z1, z1 + 0.8)
            viti = [(xm, y0 + 4.0), (xm, y0 + 12.0)]
        for vx, vy in viti: m -= cil(1.3, z0 - 1, z1 + 1, vx, vy)
        add("celle", "alluminio", m); add("celle", "ceramica", gauge)
        for vx, vy in viti: add("viti", "metallo", _posa(vite(z1 - z0 + 3.0, d=2.5, passo=0.45, testa=4.4, h_testa=1.6), "z", [vx, vy, z1]))
    cb = M.cella().bounding_box(); cella(cb, "x")
    ca = M.cella_alta().bounding_box(); cella(ca, "y")
    # ---- viti della croce di Malta (recuperate dagli hard disk): M2 lungo l'asse della ruota, la testa verso la ruota
    for i, a in enumerate(s8.ANG_CROCE[M.k]):
        cx, cz = M.C_GEN * math.cos(math.radians(a)), M.Z_A + M.C_GEN * math.sin(math.radians(a))
        s = -1 if i == 0 else 1
        ytesta = s * (M.Y0 - 1.6)
        add("viti", "metallo", _posa(vite(4.2, d=2.0, passo=0.4, testa=3.0, h_testa=1.0), "-y" if s < 0 else "y", [cx, ytesta, cz]))
    # ---- vite nella chiglia della vaschetta alta (fa da peso: la vaschetta torna dritta)
    # (la vaschetta gira nel visore: la vite e' disegnata ferma, a vaschetta dritta)
    ra = s8.RA
    add("viti", "metallo", _posa(vite(ra["x1"] - ra["x0"] - 4.5, d=2.0, passo=0.4, testa=3.0, h_testa=1.0), "x", [ra["x1"] - 2.0, 0, ra["zb"] - 3.4]))
    # ---- magneti al neodimio (recuperati): nichelati, con la meta' nord segnata
    if M.ruote == 2:
        for sd in (-1, 1):
            m = M.metti(cil(1.5, M.Z_COR[0], M.Z_COR[0] + 1.0, 0, -s8.R_MAGNETE), sd)
            add("magneti", "magnete", m)
    c = M.CUP
    add("magneti", "magnete", cil_x(3.0, c["x0"] - 0.6, c["x0"] + 0.9, 0, M.Z_CUP + 6.0))
    return D

# componenti semplici che nel visore vengono sostituiti dai dettagli
SOSTITUITI = ("schede", "hx711", "rtc", "amplificatore", "motore_1", "motore_2", "cella", "cella_alta", "viti_croce", "magneti_ruote")
