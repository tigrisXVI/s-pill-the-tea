#!/usr/bin/env python3
"""Schede tecniche della Scatoletta Blistra v0.3, ricavate dai solidi veri (sezioni, pianta, tabelle)."""
import math, os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import PathPatch, Rectangle, FancyBboxPatch
from matplotlib.path import Path
import matplotlib.image as mpimg
import scatoletta_v3 as s

QUI = os.path.dirname(os.path.abspath(__file__)); RADICE = os.path.join(QUI, "..")
BLU, INK, GRIGIO, ARANCIO = "#13294B", "#16202E", "#536072", "#E8962A"
COL = {"1_base": "#C9D2DC", "2_fondo_a_rampa": "#6FA6CC", "3_piastra_pesata": "#F2A43A", "3b_tappini_x2": "#F2A43A", "4_mozzo": "#8C949E",
       "5_paletta_x29": "#EEEEEA", "6_scivolo_vaschetta": "#A9CBE6", "7_coperchio": "#2B3550", "8_sportello": "#3FB58C"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})
S = {n: f() for n, f in s.PEZZI.items()}
A4 = (11.69, 8.27)
PIEDE = "Scatoletta Blistra, prototipo v0.3. Misure in millimetri. Controllato solo al computer: da provare con una stampa."

def patch(polys, **kw):
    polys = [p for p in polys if len(p) >= 3]
    if not polys: return Rectangle((0, 0), 0, 0, visible=False)
    verts, codes = [], []
    for p in polys:
        p = list(map(tuple, p)); verts += p + [p[0]]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(p) - 1) + [Path.CLOSEPOLY]
    return PathPatch(Path(verts, codes), **kw)
def sezione_xz(m, angolo=0.0):
    r = m.rotate([0, 0, -angolo]).rotate([90, 0, 0])
    return [[(x, -y) for x, y in p] for p in r.slice(0.0).to_polygons()]
def pianta(m, z=None):
    cs = m.project() if z is None else m.slice(z)
    return [[(x, y) for x, y in p] for p in cs.to_polygons()]
def quota(ax, p1, p2, testo, off=0.0, vert=False, col=GRIGIO):
    (x1, y1), (x2, y2) = p1, p2
    ax.annotate("", xy=p1, xytext=p2, arrowprops=dict(arrowstyle="<|-|>", color=col, lw=0.7, shrinkA=0, shrinkB=0))
    if vert: ax.text(x1 + off, (y1 + y2) / 2, testo, rotation=90, va="center", ha="center", color=col, backgroundcolor="white", fontsize=7.5)
    else: ax.text((x1 + x2) / 2, y1 + off, testo, va="center", ha="center", color=col, backgroundcolor="white", fontsize=7.5)
def pagina(titolo, sotto=""):
    fig = plt.figure(figsize=A4)
    fig.text(0.04, 0.945, titolo, fontsize=16, weight="bold", color=BLU)
    fig.text(0.04, 0.915, sotto, fontsize=9, color=GRIGIO)
    fig.text(0.04, 0.025, PIEDE, fontsize=7, color=GRIGIO)
    return fig
def assi(fig, rect, lim):
    ax = fig.add_axes(rect); ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[2], lim[3]); return ax
def nota(ax, xy, xytext, testo):
    ax.annotate(testo, xy=xy, xytext=xytext, fontsize=7.5, color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.6), va="center")
def tabella(fig, rect, righe, larghezze, titolo=None, fs=8, alt=1.55):
    ax = fig.add_axes(rect); ax.axis("off")
    t = ax.table(cellText=righe[1:], colLabels=righe[0], colWidths=larghezze, loc="upper left", cellLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(fs); t.scale(1, alt)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("#D5DCE4"); cell.set_linewidth(0.6)
        if r == 0: cell.set_facecolor(BLU); cell.get_text().set_color("white"); cell.get_text().set_weight("bold")
    if titolo: ax.set_title(titolo, loc="left", fontsize=10, weight="bold", color=INK, pad=4)
    return ax
def testo(fig, x, y, righe, fs=8.5, inter=0.031, col=INK):
    for i, r in enumerate(righe):
        peso = "bold" if r.startswith("#") else "normal"
        fig.text(x, y - i * inter, r.lstrip("# "), fontsize=fs + (1 if peso == "bold" else 0), weight=peso, color=BLU if peso == "bold" else col)

def stima(nome, m):
    """Peso e tempo indicativi in PETG (densita' 1,27), con riempimento 15% sulle parti piene."""
    v = m.volume() / 1000
    k = 0.55 if v > 30 else 0.85
    q = {"5_paletta_x29": 29, "3b_tappini_x2": 1}.get(nome, 1)
    g = v * 1.27 * k * q
    return g, g / 13.0

def risultati_sim():
    righe = []
    for cart, nome in ((os.path.join(RADICE, "simulazioni", "risultati", "v0.3a"), "v0.3a"), (os.path.join(RADICE, "simulazioni", "risultati", "v0.3b"), "v0.3b")):
        for d in sorted(glob.glob(os.path.join(cart, "*/"))):
            es = [json.load(open(f)) for f in glob.glob(d + "esito_*.json")]
            if not es: continue
            pill = [p for e in es for p in e["pillole"] if p["ruolo"] == "dose"]
            righe.append((nome, os.path.basename(d.rstrip("/")), len(es), sum(e["dose_completa"] for e in es), sum(e["vicini_al_loro_posto"] for e in es),
                          len(pill), sum(p["ok"] for p in pill), es[0]["attrito"], es[0]["gioco"]))
    return righe

def genera(percorso):
    with PdfPages(percorso) as pdf:
        # ---------- 1. copertina e misure
        fig = pagina("Scatoletta Blistra v0.3: schede tecniche", "28 scomparti (4 dosi al giorno per 7 giorni) + 1 di riposo. Rampa fissa, palette che salgono, ripiano pesato e vibrante, scivolo.")
        img = mpimg.imread(os.path.join(RADICE, "docs", "immagini", "v3_aperta.png"))
        ax = fig.add_axes([0.03, 0.08, 0.55, 0.80]); ax.imshow(img); ax.axis("off")
        testo(fig, 0.61, 0.86, [
            "# Misure d'ingombro",
            f"Corpo: diametro {2 * s.R_EST:.1f} mm, altezza {s.Z_TOP:.1f} mm",
            f"Con la cerniera dello sportello: {s.Z_TOP + 5.5:.1f} mm",
            f"Con scivolo e vaschetta: profondo {s.R_EST + s.X2_SC + 2.5:.0f} mm",
            "",
            "# Come funziona",
            "1. Il fondo e' fermo: sale di 10 mm lungo il giro e pende",
            "   di 8 gradi verso il bordo.",
            "2. Il motore gira il mozzo; le 29 palette scorrono in su",
            "   e in giu' e appoggiano sul fondo.",
            "3. Ogni paletta spinge la dose su per la rampa fino al",
            "   ripiano, largo esattamente uno scomparto.",
            "4. Il ripiano e' una piastra su una cella di carico: pesa la",
            "   dose e la confronta con quella attesa.",
            "5. Aprendo lo sportello la gonna libera il varco; la piastra",
            "   vibra e le pillole scendono nella vaschetta.",
            "6. Ripesa: piastra vuota = dose erogata. Il carosello",
            "   gira solo a sportello chiuso.",
            "",
            "# Pillole previste",
            "Dalla minicompressa da 2 mm all'Augmentin 875 (22 mm)."], fs=8.5, inter=0.034)
        pdf.savefig(fig); plt.close(fig)

        # ---------- 2. sezione d'assieme quotata
        fig = pagina("Sezione d'assieme", "Taglio verticale lungo l'asse davanti-dietro, a riposo: lo scomparto di riposo e' sul ripiano. Lo sportello e lo scivolo sono a destra.")
        ax = assi(fig, [0.03, 0.07, 0.94, 0.82], (-100, 160, -12, 92))
        for n, m in S.items():
            if n == "5_paletta_x29": continue
            ax.add_patch(patch(sezione_xz(m), facecolor=COL[n], edgecolor=INK, lw=0.5))
        for j in range(s.N):
            ax.add_patch(patch(sezione_xz(s.paletta_a(0, j)), facecolor=COL["5_paletta_x29"], edgecolor=INK, lw=0.4))
        for e, c in ((s.ingombro_motore(), "#E9C46A"), (s.ingombro_cella(), "#B5838D"), (s.ingombro_vibro(), "#E76F51")):
            ax.add_patch(patch(sezione_xz(e), facecolor=c, edgecolor=INK, lw=0.4, alpha=0.75))
        ax.plot([0, 0], [-4, 70], color=GRIGIO, lw=0.5, ls="-.")
        quota(ax, (-s.R_EST, -7), (s.R_EST, -7), f"Ø {2 * s.R_EST:.1f}")
        quota(ax, (-92, 0), (-92, s.Z_TOP), f"{s.Z_TOP:.1f}", vert=True)
        quota(ax, (-86, 2.4), (-86, s.Z_APPOGGIO), f"{s.VANO:.0f} vano", vert=True, off=0)
        quota(ax, (s.R_EST + 4, s.Z_BASSO), (s.R_EST + 4, s.Z_RIPIANO), "alzata 10", vert=True)
        quota(ax, (s.R_EST, -2), (s.X2_SC + 2.5, -2), f"{s.X2_SC + 2.5 - s.R_EST:.0f}")
        nota(ax, (-8, 26), (-95, 76), "motore 28BYJ-48 (sotto il centro rialzato)")
        nota(ax, (45, 31), (10, 88), "cella di carico 100 g (sotto la piastra)")
        nota(ax, (s.VIBRO["r"], s.Z_RIPIANO - 0.5), (100, 74), "motorino vibrante 8x2 mm incollato sotto la piastra")
        nota(ax, (60, s.Z_RIPIANO + 3), (100, 66), "piastra pesata (ripiano)")
        nota(ax, (s.R_INT + 1, s.Z_RIPIANO + 6), (118, 50), "gonna dello sportello: chiude il varco")
        nota(ax, (95, s.z_scivolo(95) + 1), (118, 38), "scivolo a 40 gradi, si allarga")
        nota(ax, (125, s.z_scivolo(125) + 1), (125, 30), "vaschetta: 40 mm a 15 gradi")
        nota(ax, (s.HALL_ZERO[0], s.Z_DISCO), (-95, 82), "Hall + magnete 4x2 (posizione zero)")
        nota(ax, (-50, s.Z_SOTTO_COP - 2), (-95, 88), f"spazio per le pillole: {s.ARIA_SOPRA:.0f} mm sopra il ripiano al mozzo")
        pdf.savefig(fig); plt.close(fig)

        # ---------- 3. pianta
        fig = pagina("Pianta: scomparti, ripiano, varco", "Vista dall'alto senza coperchio. Il numero e' lo scomparto a riposo: 0 = riposo (sul ripiano), 1-4 lunedi', 5-8 martedi', ... 25-28 domenica.")
        ax = assi(fig, [0.02, 0.06, 0.62, 0.84], (-95, 150, -95, 95))
        for n in ("1_base", "2_fondo_a_rampa", "3_piastra_pesata", "6_scivolo_vaschetta", "4_mozzo"):
            ax.add_patch(patch(pianta(S[n]), facecolor=COL[n], edgecolor=INK, lw=0.4, alpha=0.95 if n != "1_base" else 1))
        for j in range(s.N):
            ax.add_patch(patch(pianta(s.paletta_a(0, j)), facecolor="#FFFFFF", edgecolor=INK, lw=0.4))
        giorni = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
        for k in range(s.N):
            a = math.radians(-k * s.PASSO); r = 70       # lo scomparto k arriva sul ripiano dopo k passi del carosello
            # a riposo lo scomparto k e' centrato a k*PASSO; il carosello gira in senso antiorario visto dall'alto
            lab = "0" if k == 0 else f"{k}"
            ax.text(r * math.cos(a), r * math.sin(a), lab, ha="center", va="center", fontsize=6.5, color=BLU, weight="bold")
            if k and (k - 1) % 4 == 0:
                ax.text(52 * math.cos(math.radians(-(k + 1.5) * s.PASSO)), 52 * math.sin(math.radians(-(k + 1.5) * s.PASSO)), giorni[(k - 1) // 4], ha="center", va="center", fontsize=6.5, color=GRIGIO)
        for a in (-s.RIPIANO, s.RIPIANO):
            ax.plot([s.R_DISCO * math.cos(math.radians(a)), s.R_FONDO * math.cos(math.radians(a))], [s.R_DISCO * math.sin(math.radians(a)), s.R_FONDO * math.sin(math.radians(a))], color=ARANCIO, lw=0.8, ls="--")
        nota(ax, (60, 0), (100, 60), f"ripiano: {2 * s.RIPIANO:.1f} gradi (uno scomparto)")
        nota(ax, (60 * math.cos(math.radians(-60)), 60 * math.sin(math.radians(-60))), (95, -80), f"salita: {s.SALITA:.0f} gradi prima del ripiano")
        nota(ax, (60 * math.cos(math.radians(35)), 60 * math.sin(math.radians(35))), (95, 85), f"discesa: {s.DISCESA:.0f} gradi dopo")
        ax.annotate("", xy=(45 * math.cos(math.radians(-100)), 45 * math.sin(math.radians(-100))), xytext=(45 * math.cos(math.radians(-140)), 45 * math.sin(math.radians(-140))),
                    arrowprops=dict(arrowstyle="->", color=BLU, lw=1.2, connectionstyle="arc3,rad=-0.3"))
        ax.text(-40, -50, "verso di rotazione", color=BLU, fontsize=7)
        larg = [2 * math.pi * r / s.N - s.SP_PALETTA for r in (s.R_DISCO, 40, 60, s.R_FONDO)]
        testo(fig, 0.66, 0.86, [
            "# Scomparti",
            f"29 spicchi da {s.PASSO:.2f} gradi",
            f"Larghezza libera: {larg[0]:.1f} mm al mozzo, {larg[1]:.1f} a 40 mm,",
            f"{larg[2]:.1f} a 60 mm, {larg[3]:.1f} al bordo",
            f"Lunghezza: da {s.R_DISCO:.1f} a {s.R_FONDO:.0f} mm dal centro",
            f"Altezza libera: {s.ARIA_SOPRA:.0f} mm al mozzo sul ripiano, di piu'",
            "verso il bordo (il fondo pende di 8 gradi)",
            "Un Augmentin (22 mm) sta disteso verso il bordo.",
            "",
            "# Varco e scivolo",
            f"Varco nella parete: {2 * s.VARCO:.1f} gradi, {2 * s.W_SC:.1f} mm",
            f"Scivolo: {s.L_SCIVOLO:.0f} mm a {s.SCIVOLO_GRADI:.0f} gradi, si allarga fino a",
            f"{2 * (s.W_SC + s.SVASO):.0f} mm; vaschetta {s.L_VASCA:.0f} mm a {s.PEND_VASCA:.0f} gradi",
            f"Fondo della vaschetta a {s.Z2_SC - 3:.1f} mm dal tavolo",
            "",
            "# Palette",
            f"29 palette da {s.SP_PALETTA} mm, flottanti in verticale",
            f"Luce massima sotto la paletta: 0,75 mm"], fs=8.5, inter=0.033)
        pdf.savefig(fig); plt.close(fig)

        # ---------- 4. pezzi da stampare
        fig = pagina("Pezzi da stampare", "File in stl_per_stampa, gia' orientati. Tempi e pesi indicativi (PETG, ugello 0,4, strato 0,2): controllali nello slicer.")
        info = {
            "1_base": ("1", "PETG bianco o grigio", "in piedi, aperta in alto", "no"),
            "2_fondo_a_rampa": ("1", "PETG per alimenti, bianco", "sotto sul piatto", "si', solo nella sede del motore"),
            "3_piastra_pesata": ("1", "PETG per alimenti, bianco", "coricata (inclinata di 8 gradi)", "si', sotto il piedino"),
            "3b_tappini_x2": ("2", "PETG per alimenti, bianco", "piatti", "no"),
            "4_mozzo": ("1", "PETG", "in piedi", "no"),
            "5_paletta_x29": ("29", "PETG per alimenti, bianco", "coricate, tutte su un piatto", "no"),
            "6_scivolo_vaschetta": ("1", "PETG per alimenti, colore chiaro", "in piedi sulla flangia", "si', sotto la vaschetta"),
            "7_coperchio": ("1", "PETG scuro e opaco", "capovolto (occhielli in alto)", "no"),
            "8_sportello": ("1", "PETG colorato", "capovolto (tetto sul piatto)", "si', sotto la gonna"),
        }
        righe = [["Pezzo", "Q.ta'", "Materiale", "Come metterlo sul piatto", "Supporti", "Peso ~", "Tempo ~"]]
        tg = th = 0
        for n, m in S.items():
            g, h = stima(n, m); tg += g; th += h
            q, mat, ori, sup = info[n]
            righe.append([n.replace("_", " "), q, mat, ori, sup, f"{g:.0f} g", f"{h:.1f} h"])
        righe.append(["Totale", "", "", "", "", f"{tg:.0f} g", f"{th:.0f} h"])
        tabella(fig, [0.04, 0.42, 0.92, 0.46], righe, [0.17, 0.05, 0.2, 0.22, 0.17, 0.07, 0.07], fs=8)
        testo(fig, 0.04, 0.34, [
            "# Impostazioni consigliate",
            "PETG: ugello 230-250 C, piatto 70-80 C, ventola 30-50%. Asciuga la bobina se e' aperta da settimane.",
            "Strato 0,2 mm (0,12 per le palette se escono imperfette), 3 perimetri, riempimento 15% gyroid.",
            "Le superfici toccate dalle pillole (fondo, piastra, palette, scivolo) vanno lisce: niente stiratura aggressiva, pulisci i filamenti.",
            "Primo prototipo: puoi stampare tutto in PLA di un colore; passa al PETG per alimenti quando il meccanismo funziona.",
            "PETG 'per alimenti' vuol dire filamento dichiarato idoneo al contatto con alimenti: la stampa FDM ha comunque microfessure, va pulita bene."], fs=8.5, inter=0.033)
        pdf.savefig(fig); plt.close(fig)

        # ---------- 5. sensori ed elettronica
        fig = pagina("Sensori ed elettronica da comprare", "Prezzi indicativi (negozi online, 2026), da verificare. Molti pezzi si vendono in confezioni da piu' unita'.")
        righe = [["Componente", "Q.ta'", "A cosa serve", "Dove va", "Prezzo ~"],
                 ["ESP32 DevKit V1 (38 pin, USB)", "1", "Cervello: orari, Wi-Fi, Blistra", "nel vano, sotto il fondo", "6-10 €"],
                 ["Motore passo-passo 28BYJ-48 5 V + scheda ULN2003", "1", "Gira il carosello", "sotto il centro del fondo", "3-5 €"],
                 ["Cella di carico a barretta 100 g (circa 47x12x6 mm)", "1", "Pesa la dose sul ripiano", "nel fondo, sotto la piastra", "3-6 €"],
                 ["Modulino HX711", "1", "Legge la cella di carico", "nel vano", "2-3 €"],
                 ["Motorino vibrante a moneta 8x2 mm, 3 V (tipo 0820)", "1 (+1 scorta)", "Fa vibrare la piastra", "incollato sotto la piastra", "1-2 €"],
                 ["MOSFET logico AO3400 (o 2N7000) + diodo 1N4148 + resistenza 100 Ω", "1 set", "Accende il motorino vibrante", "nel vano", "1 €"],
                 ["Sensore di Hall A3144 (uscita digitale open collector)", "2", "Posizione zero e sportello aperto", "sotto il mozzo; torretta accanto al varco", "1-2 €"],
                 ["Magnete al neodimio 4x2 mm e 6x3 mm", "1 + 1", "Per i due sensori di Hall", "nel mozzo; nell'ala dello sportello", "2 €"],
                 ["Cicalino passivo 5 V", "1", "Avvisa che e' ora", "nel vano, vicino alla griglia", "1 €"],
                 ["LED 5 mm + resistenza 220 Ω", "1", "Lampeggia all'ora della dose", "foro nella parete", "0,5 €"],
                 ["Pulsante 7 mm da pannello", "1", "Silenzio / verifica del carico", "foro nella parete", "1 €"],
                 ["Alimentatore USB 5 V 2 A + cavo micro-USB o USB-C", "1", "Alimentazione", "esterno", "6-8 €"],
                 ["Viti autofilettanti M3 x 8 / x 12, M2,5 per la cella; perno Ø2 x 24", "~16 + 1", "Montaggio, cerniera", "", "3 €"],
                 ["Cavetti Dupont, filo sottile, termorestringente", "", "Collegamenti", "", "3 €"]]
        tabella(fig, [0.04, 0.24, 0.92, 0.64], righe, [0.36, 0.08, 0.22, 0.24, 0.08], fs=7.6, alt=1.62)
        testo(fig, 0.04, 0.2, [
            "# Totale indicativo: 35-55 € di elettronica, piu' il filamento (circa 10-15 € a scatoletta).",
            "Rispetto alla v0.1 non serve piu' il sensore a infrarossi TCRT5000: la conferma arriva dal peso.",
            "Limite: una minicompressa da 2 mm pesa circa 10 mg, al limite di quello che una cella da 100 g riesce a distinguere."], fs=8.5, inter=0.033)
        pdf.savefig(fig); plt.close(fig)

        # ---------- 6. collegamenti
        fig = pagina("Schema dei collegamenti", "Piedini dell'ESP32 come in config.h. 5 V dall'USB per motore e sensori di Hall; 3,3 V per HX711 e motorino vibrante.")
        righe = [["Da", "A (ESP32)", "Note"],
                 ["ULN2003 IN1 / IN2 / IN3 / IN4", "GPIO 16 / 17 / 18 / 19", "ULN2003 alimentato a 5 V (VIN)"],
                 ["HX711 DT (DOUT) / SCK", "GPIO 21 / 22", "HX711 a 3,3 V; cella: rosso E+, nero E-, bianco A-, verde A+"],
                 ["Gate del MOSFET AO3400", "GPIO 13 (PWM)", "100 Ω in serie; motorino tra 3,3 V e drain; diodo in parallelo al motorino"],
                 ["Hall zero (uscita)", "GPIO 25", "A3144 alimentato a 5 V; l'uscita e' open collector: pull-up interno a 3,3 V (sicuro)"],
                 ["Hall sportello (uscita)", "GPIO 26", "come sopra (5 V, pull-up interno a 3,3 V)"],
                 ["Cicalino passivo (+)", "GPIO 27", "- a GND"],
                 ["LED (anodo, con 220 Ω)", "GPIO 23", "catodo a GND"],
                 ["Pulsante", "GPIO 32", "l'altro capo a GND; pull-up interno"]]
        tabella(fig, [0.04, 0.5, 0.92, 0.38], righe, [0.28, 0.2, 0.52], fs=8.2)
        ax = assi(fig, [0.04, 0.05, 0.92, 0.42], (0, 300, 0, 120))
        def blocco(x, y, w, h, t, c="#EEF2F7"):
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.5", fc=c, ec=INK, lw=0.8)); ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.5)
        blocco(125, 45, 50, 30, "ESP32\nDevKit", "#DCE7F5")
        for x, y, t in ((10, 95, "ULN2003\n+ 28BYJ-48"), (10, 55, "HX711\n+ cella 100 g"), (10, 15, "MOSFET\n+ motorino vibrante"),
                        (240, 95, "Hall zero"), (240, 70, "Hall sportello"), (240, 45, "Cicalino"), (240, 20, "LED + pulsante")):
            blocco(x, y, 50, 18, t)
            xa = 60 if x < 100 else 240; xb = 125 if x < 100 else 175
            ax.annotate("", xy=(xb, 60), xytext=(xa, y + 9), arrowprops=dict(arrowstyle="-", color=GRIGIO, lw=0.7))
        blocco(125, 5, 50, 16, "USB 5 V 2 A", "#FFF2D6")
        ax.annotate("", xy=(150, 45), xytext=(150, 21), arrowprops=dict(arrowstyle="-", color=ARANCIO, lw=1.2))
        pdf.savefig(fig); plt.close(fig)

        # ---------- 7. montaggio e taratura
        fig = pagina("Montaggio e prima accensione", "Prova a secco ogni passaggio prima di incollare o stringere le viti.")
        testo(fig, 0.04, 0.87, [
            "# Montaggio",
            "1. Base: monta LED, pulsante, cicalino e l'ESP32 con le schede nel vano; fai passare il cavo USB dalla feritoia dietro.",
            "2. Fondo, da sotto: avvita il motore 28BYJ-48 nella sua sede e la cella di carico sul rialzo (estremo fisso verso il centro).",
            "   Incolla il sensore di Hall 'zero' nella tasca sotto il mozzo; i fili scendono dal foro.",
            "3. Piastra: incolla il motorino vibrante nella sua tasca sotto la piastra; avvita la piastra all'estremo libero della cella (M2,5)",
            "   e chiudi le svasature con i tappini. La piastra non deve toccare il fondo: deve muoversi un poco quando la premi.",
            "4. Appoggia il fondo sulle 4 colonnine e avvitalo (M3 x 12).",
            "5. Mozzo: incolla il magnete 4x2 nel foro sotto; infila il mozzo sull'albero (con lo scomparto 0 sopra il ripiano).",
            "6. Infila le 29 palette nelle guide del mozzo: devono scendere da sole fino al fondo. Se si bloccano, carta vetrata fine.",
            "7. Scivolo: avvitalo da dentro con 4 viti M3 attraverso la flangia; la lingua deve stare nel varco senza gradini.",
            "8. Coperchio: appoggialo nella sede (il dente nella tacca). Sportello: incolla il magnete 6x3 nell'ala, monta il perno Ø2.",
            "   Incolla il sensore di Hall dello sportello nella torretta accanto al varco.",
            "",
            "# Prima accensione (monitor seriale a 115200)",
            "z  cerca lo zero: lo scomparto 0 deve finire centrato sul ripiano. Se no, cambia PASSI_DOPO_ZERO in config.h.",
            "t  tara con il ripiano vuoto.      c7.5  taratura con una moneta da 1 euro (7,5 g) sul ripiano.      s  controlla il peso.",
            "v  prova la vibrazione: metti qualche pillola sul ripiano e apri lo sportello, devono scendere nella vaschetta.",
            "a  avanza di uno scomparto: le palette devono salire e scendere senza fermarsi.",
            "",
            "# Ogni settimana",
            "Togli il coperchio, riempi gli scomparti come dice Blistra (Ricarica guidata), richiudi e tieni premuto il pulsante:",
            "la scatoletta pesa gli scomparti uno a uno (circa 2 minuti) e in Blistra vedi quali sono giusti e quali da controllare.",
            "",
            "# Sicurezza",
            "Il carosello non gira mai a sportello aperto. Prototipo non certificato: non sostituisce il controllo di chi assiste la persona."], fs=8.5, inter=0.031)
        pdf.savefig(fig); plt.close(fig)

        # ---------- 8. simulazioni
        fig = pagina("Risultati delle simulazioni", "Blender / Bullet. Ogni simulazione: una dose dal fondo dello scomparto fino alla vaschetta, con pillole a caso negli scomparti vicini.")
        rr = risultati_sim()
        righe = [["Serie", "Prova", "Simulazioni", "Dosi arrivate intere", "Vicini rimasti al posto", "Pillole della dose", "...in vaschetta", "Attrito", "Gioco palette"]]
        for r in rr: righe.append([r[0], r[1].replace("_", " "), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), f"{r[7]:.2f}", f"{r[8]:.2f} mm"])
        tabella(fig, [0.04, 0.55, 0.92, 0.33], righe, [0.06, 0.16, 0.09, 0.13, 0.13, 0.11, 0.1, 0.07, 0.1], fs=8)
        testo(fig, 0.04, 0.45, [
            "# Come leggere",
            "v0.3a: geometria della simulazione con mozzo da 14 mm e palette alte fino al coperchio (240 simulazioni).",
            "v0.3b: geometria di questo progetto: mozzo da 20 mm e palette della loro altezza vera.",
            "'Peggiore': attrito pillola-plastica 0,5 (pillole non rivestite o un po' umide) e palette stampate meno precise (0,5 mm).",
            "Pillole: minicompresse 2x2 e 3x2,5 mm, compresse 5 e 9 mm, Augmentin 22 x 10,5 x 7,5 mm (spessore stimato).",
            "",
            "# Cosa non dicono",
            "Attrito e vibrazione reali possono essere diversi: la prova vera e' il prototipo stampato.",
            "Senza vibrazione le pillole restano ferme sul ripiano: la vibrazione (50 Hz, circa 0,6 mm, 3 secondi) e' indispensabile.",
            "Le 2 dosi fallite (caso peggiore): una compressa da 9 mm ferma in fondo alla discesa, dietro l'Augmentin."], fs=8.5, inter=0.031)
        pdf.savefig(fig); plt.close(fig)

if __name__ == "__main__":
    out = os.path.join(RADICE, "docs", "schede_tecniche.pdf")
    genera(out); print("ok", out)
