"""
Scatoletta Blistra v0.3 - 29 scomparti (4 dosi al giorno x 7 giorni + riposo), Ø circa 172 mm.
Simulazione fisica (Blender / Bullet) di UNA dose, dall'inizio alla fine:
  1. le pillole sono nello scomparto bersaglio, in basso;
  2. il carosello lo porta sul ripiano (le palette spingono su per la rampa);
  3. lo sportello si apre, il carosello fa qualche piccola scossa avanti-indietro;
  4. controllo: ogni pillola della dose deve finire nella parte piu' bassa dello scivolo
     (la vaschetta), e nessuna pillola degli scomparti vicini deve uscire.

Uso:  python3 simula_scivolo.py CARTELLA   (variabili: SEME, ATTRITO, GIOCO, PENDENZA, SCIVOLO_GRADI, SCOSSE, CARICO)
Unita': millimetri, secondi.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Euler

_arg = [a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".py")]
OUT = _arg[0] if _arg else "."
os.makedirs(OUT, exist_ok=True)
SEME = int(os.environ.get("SEME", "1")); random.seed(SEME)

# ---------------------------------------------------------------- geometria
N = 29; PASSO = 360.0 / N                     # 12,41 gradi
R_MOZZO, R = 20.0, 80.0                       # v0.3: mozzo da 20 mm (29 guide per le palette), fondo fino a 80 mm
H = 10.0                                      # alzata della rampa
PEND = float(os.environ.get("PENDENZA", "8"))
TAN = math.tan(math.radians(PEND))
RIPIANO = PASSO / 2 + 0.8                     # il ripiano contiene esattamente uno scomparto
SALITA, DISCESA = 96.0, 48.0
SP_PAL = 1.2
GIOCO = float(os.environ.get("GIOCO", "0.25"))
PIATTO = 8.0                                  # aria tra ripiano (al mozzo) e coperchio piatto
MU = float(os.environ.get("ATTRITO", "0.35"))  # attrito pillola-plastica (Bullet moltiplica i due valori)
VARCO = PASSO / 2 - 0.4                       # mezzo angolo dell'apertura nel bordo
SOGLIA = 0.0                                  # lo scivolo parte subito dal bordo del ripiano (finestre dell'anello e parete tagliate in basso)
PIASTRA = PASSO / 2 - 0.7                     # mezzo angolo della piastra pesata e vibrante (dentro lo scomparto, le palette restano sul fondo fisso)
VIBRA_X = float(os.environ.get("VIBRA_X", "1.2"))   # componente verso lo scivolo, per mm di salita
VIBRA_HZ = float(os.environ.get("VIBRA_HZ", "50")); VIBRA_MM = float(os.environ.get("VIBRA_MM", "0.6")); T_VIBRA = float(os.environ.get("T_VIBRA", "3"))
ANG_SC = float(os.environ.get("SCIVOLO_GRADI", "40"))
SVASO = float(os.environ.get("SVASO", "10"))   # di quanto si allarga lo scivolo per lato, dal bordo alla vaschetta
L_SC = 26.0                                   # lunghezza dello scivolo inclinato
L_VASCA = 40.0                                # vaschetta in fondo allo scivolo
SCOSSE = int(os.environ.get("SCOSSE", "0"))
FPS, VEL = 300, 72.0

def quota(th):
    t = (th + 180.0) % 360.0 - 180.0
    m = lambda x: 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, x)))
    if -RIPIANO <= t <= RIPIANO: return H
    if -RIPIANO - SALITA < t < -RIPIANO: return H * m((t + RIPIANO + SALITA) / SALITA)
    if RIPIANO < t < RIPIANO + DISCESA: return H * m((RIPIANO + DISCESA - t) / DISCESA)
    return 0.0
extra = lambda r: TAN * (R - r)
z_fondo = lambda th, r: quota(th) + extra(r)
def quota_pal(th):
    d = math.degrees(math.asin(SP_PAL / 2 / R_MOZZO))
    return max(quota(th - d), quota(th), quota(th + d)) + GIOCO
Z_COP = H + extra(R_MOZZO) + PIATTO
X0_SC = R + 0.2; Z0_SC = H - 0.6
X1_SC = X0_SC + L_SC * math.cos(math.radians(ANG_SC)); Z1_SC = Z0_SC - L_SC * math.sin(math.radians(ANG_SC))
X2_SC = X1_SC + L_VASCA
PEND_VASCA = float(os.environ.get("PEND_VASCA", "15"))   # la vaschetta scende ancora un po' verso il bordino
Z2_SC = Z1_SC - L_VASCA * math.tan(math.radians(PEND_VASCA))
W_SC = R * math.sin(math.radians(VARCO))      # mezza larghezza dello scivolo

# ---------------------------------------------------------------- scena
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = FPS; sc.gravity = (0, 0, -9810.0)
bpy.ops.rigidbody.world_add(); rw = sc.rigidbody_world
rw.substeps_per_frame = 4; rw.solver_iterations = 30
rw.collection = bpy.data.collections.new("Fisica"); sc.collection.children.link(rw.collection)

def oggetto(nome, v, f):
    me = bpy.data.meshes.new(nome); me.from_pydata(v, [], f); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nome, me); sc.collection.objects.link(o); return o

def fisica(o, tipo, forma, massa=1.0, cin=False, mu=None):
    rw.collection.objects.link(o); rb = o.rigid_body
    rb.type = tipo; rb.collision_shape = forma; rb.friction = math.sqrt(MU) if mu is None else mu; rb.restitution = 0.05
    rb.use_margin = True; rb.collision_margin = 0.04
    if tipo == "ACTIVE": rb.mass = massa; rb.use_deactivation = False; rb.linear_damping = 0.05; rb.angular_damping = 0.1
    rb.kinematic = cin; return o

def anello(nome, r0, r1, z0f, z1f, a0=0.0, a1=360.0, seg=None):
    """Solido tra r0 e r1, fra gli angoli a0 e a1; z0f/z1f(theta, r) danno sotto e sopra."""
    seg = seg or max(4, int(abs(a1 - a0) * 2))
    chiuso = abs(a1 - a0) >= 360.0
    v, f = [], []
    n = seg if chiuso else seg + 1
    for i in range(n):
        t = a0 + (a1 - a0) * i / seg; c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
        v += [(r0 * c, r0 * s, z1f(t, r0)), (r1 * c, r1 * s, z1f(t, r1)), (r1 * c, r1 * s, z0f(t, r1)), (r0 * c, r0 * s, z0f(t, r0))]
    for i in range(seg if chiuso else seg):
        a, b = 4 * i, 4 * ((i + 1) % n)
        for k in range(4): f.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
    if not chiuso: f += [(0, 1, 2, 3), (4 * (n - 1) + 3, 4 * (n - 1) + 2, 4 * (n - 1) + 1, 4 * (n - 1))]
    return oggetto(nome, v, f)

def scatola(nome, x0, x1, y0, y1, z0, z1):
    v = [(x, y, z) for z in (z0, z1) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return oggetto(nome, v, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])

def prisma(nome, punti_xz, y0, y1):
    """Prisma con sezione nel piano XZ, esteso tra y0 e y1."""
    n = len(punti_xz); v = [(x, y0, z) for x, z in punti_xz] + [(x, y1, z) for x, z in punti_xz]
    f = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return oggetto(nome, v, f)

# fondo a rampa, fino al davanzale (oltre R continua a scendere con la stessa pendenza)
def z_fisso(t, r):   # sotto la piastra il fondo fisso e' ribassato: la piastra appoggia sulla cella di carico
    tt = (t + 180) % 360 - 180
    return z_fondo(t, r) - (2.5 if abs(tt) < PIASTRA + 0.3 else 0.0)
fisica(anello("Fondo", R_MOZZO - 1, R, lambda t, r: -4.0, z_fisso, seg=1440), "PASSIVE", "MESH")
piastra = fisica(anello("Piastra", R_MOZZO + 2, R - 0.1, lambda t, r: z_fondo(t, r) - 1.5, lambda t, r: z_fondo(t, r) + 0.02, -PIASTRA, PIASTRA, 24), "PASSIVE", "MESH", cin=True)
# parete fissa con l'apertura davanti, e coperchio piatto
fisica(anello("Parete", R, R + 3, lambda t, r: -4.0, lambda t, r: Z_COP, VARCO, 360 - VARCO), "PASSIVE", "MESH")
fisica(anello("Coperchio", 0.01, R + 3, lambda t, r: Z_COP, lambda t, r: Z_COP + 2), "PASSIVE", "MESH")
fisica(anello("Mozzo", 0.01, R_MOZZO, lambda t, r: -4.0, lambda t, r: Z_COP), "PASSIVE", "MESH")
# scivolo: fondo inclinato, vaschetta in fondo, bordino davanti, sponde ai lati
WE = W_SC + SVASO + 3
# due solidi convessi: la parte inclinata e la vaschetta (un solo poligono concavo dava una superficie sbagliata)
fisica(prisma("Scivolo", [(X0_SC - 0.2, Z0_SC), (X1_SC, Z1_SC), (X1_SC, Z1_SC - 3), (X0_SC - 0.2, Z0_SC - 3)], -WE, WE), "PASSIVE", "CONVEX_HULL")
fisica(prisma("Vaschetta", [(X1_SC - 0.5, Z1_SC), (X2_SC, Z2_SC), (X2_SC, Z2_SC - 3), (X1_SC - 0.5, Z1_SC - 3)], -WE, WE), "PASSIVE", "CONVEX_HULL")
fisica(scatola("Bordino", X2_SC, X2_SC + 2, -WE, WE, Z2_SC - 3, Z2_SC + 7), "PASSIVE", "MESH")
def y_sponda(x): return W_SC + SVASO * min(1.0, max(0.0, (x - R) / (X1_SC - R)))
for s in (1, -1):   # sponde che si allargano lungo lo scivolo, poi dritte lungo la vaschetta
    xs = [R + 0.1, X1_SC, X2_SC + 2]
    for xa, xb in zip(xs, xs[1:]):
        v = []
        for z in (Z2_SC - 3, Z_COP):
            v += [(xa, s * y_sponda(xa), z), (xb, s * y_sponda(xb), z), (xb, s * (y_sponda(xb) + 2.5), z), (xa, s * (y_sponda(xa) + 2.5), z)]
        fisica(oggetto("Sponda", v, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]), "PASSIVE", "CONVEX_HULL")
# sportello: chiude il varco finche' la dose non e' arrivata
sportello = fisica(scatola("Sportello", R + 0.05, R + 3.0, -W_SC - 0.5, W_SC + 0.5, Z0_SC - 2.0, Z_COP), "PASSIVE", "CONVEX_HULL", cin=True)   # a filo della parete

# palette
palette = []
for j in range(N):
    x0, x1, y = R_MOZZO + 0.3, R - 0.3, SP_PAL / 2
    zt = Z_COP - 0.6 - H                        # paletta reale: alta quanto basta per non toccare il coperchio sul ripiano
    v = [(x0, -y, extra(x0)), (x1, -y, extra(x1)), (x1, y, extra(x1)), (x0, y, extra(x0)), (x0, -y, zt), (x1, -y, zt), (x1, y, zt), (x0, y, zt)]
    p = fisica(oggetto(f"Paletta {j}", v, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]), "PASSIVE", "CONVEX_HULL", cin=True)
    palette.append(p)

# ---------------------------------------------------------------- pillole
def m_cil(r, h, seg=18):
    v = [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z) for z in (-h / 2, h / 2) for i in range(seg)]
    return v, [tuple(range(seg)), tuple(range(seg, 2 * seg))] + [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]

def m_caps(lung, larg, spess, seg=16, anelli=5):
    r = larg / 2; k_z = spess / larg; q = []
    for k in range(anelli + 1): a = math.pi / 2 * k / anelli; q.append((-lung / 2 + r - r * math.cos(a), r * math.sin(a)))
    for k in range(anelli + 1): a = math.pi / 2 * (1 - k / anelli); q.append((lung / 2 - r + r * math.cos(a), r * math.sin(a)))
    v, f = [], []
    for x, rr in q:
        for i in range(seg): v.append((x, max(rr, .05) * math.cos(2 * math.pi * i / seg), max(rr, .05) * math.sin(2 * math.pi * i / seg) * k_z))
    for k in range(len(q) - 1):
        for i in range(seg): f.append((k * seg + i, k * seg + (i + 1) % seg, (k + 1) * seg + (i + 1) % seg, (k + 1) * seg + i))
    f += [tuple(range(seg)), tuple(range((len(q) - 1) * seg, len(q) * seg))]
    return v, f

TIPI = {  # nome: (mesh, massa g, ingombro radiale per il posizionamento)
    "minicompressa 2x2":      (m_cil(1.0, 2.0), 0.010, 2),
    "minicompressa 3x2,5":    (m_cil(1.5, 2.5), 0.025, 3),
    "compressa 5x2,5":        (m_cil(2.5, 2.5), 0.07, 5),
    "compressa tonda 9x3,5":  (m_cil(4.5, 3.5), 0.33, 9),
    "Augmentin 22x10,5x7,5":  (m_caps(22.0, 10.5, 7.5), 1.20, 22),
}
PICCOLE = ["minicompressa 2x2", "minicompressa 3x2,5", "compressa 5x2,5", "compressa tonda 9x3,5"]

def carico(rnd):
    tipo = os.environ.get("CARICO", "misto")
    if tipo == "augmentin": return ["Augmentin 22x10,5x7,5"] * rnd.choice([1, 2])
    if tipo == "mini": return ["minicompressa 2x2"] * rnd.randint(1, 4) + ["minicompressa 3x2,5"] * rnd.randint(0, 3)
    return ["Augmentin 22x10,5x7,5"] * rnd.choice([0, 1, 1]) + [rnd.choice(PICCOLE) for _ in range(rnd.randint(1, 4))]

K = 14                                         # scomparto bersaglio
PARTENZA = -160.0                              # dove sta il bersaglio all'inizio (zona bassa)
PHI0 = PARTENZA - (K * PASSO + PASSO / 2)      # rotazione iniziale del carosello
pillole = []
def metti(scomparto, lista, ruolo):
    centro = scomparto * PASSO + PASSO / 2 + PHI0
    occupati = []
    for i, nome in enumerate(sorted(lista, key=lambda n: -TIPI[n][2])):
        (v, f), massa, ing = TIPI[nome]
        o = oggetto(f"{ruolo} {i}: {nome}", v, f)
        for tentativo in range(60):
            if ing >= 22: r = random.uniform(58, 66)
            elif ing >= 9: r = random.uniform(40, 72)
            else: r = random.uniform(26, 75)
            semi = math.degrees((PASSO / 2) * math.pi / 180) - math.degrees((ing / 2 if ing < 22 else 5.6) / r) - math.degrees(1.2 / r)
            th = centro + random.uniform(-max(0.2, semi), max(0.2, semi))
            if all(math.hypot(r - a, math.radians(th - b) * r) > (ing + c) / 2 + 1 for a, b, c in occupati): break
        livello = sum(1 for a, b, c in occupati if math.hypot(r - a, math.radians(th - b) * r) <= (ing + c) / 2 + 1)
        occupati.append((r, th, ing))
        zz = min(z_fondo(th, r) + 4.5 + 7 * livello, Z_COP - 5.5)     # mai sopra il coperchio
        o.location = (r * math.cos(math.radians(th)), r * math.sin(math.radians(th)), zz)
        o.rotation_euler = Euler((random.uniform(-.2, .2), random.uniform(-.2, .2), math.radians(th) + (0 if ing >= 22 else random.uniform(0, 6))))
        fisica(o, "ACTIVE", "CONVEX_HULL", massa=massa)
        pillole.append(dict(o=o, nome=nome, ruolo=ruolo))
metti(K, carico(random), "dose")
metti(K - 1, [random.choice(PICCOLE + ["Augmentin 22x10,5x7,5"]) for _ in range(random.randint(1, 3))], "vicino")
metti(K + 1, [random.choice(PICCOLE + ["Augmentin 22x10,5x7,5"]) for _ in range(random.randint(1, 3))], "vicino")

# ---------------------------------------------------------------- programma del motore
ASSESTA = int(0.7 * FPS)
T_GIRO = -PARTENZA / VEL                        # il bersaglio va da -160 a 0 gradi
F_ARRIVO = ASSESTA + int(T_GIRO * FPS)
F_APRE = F_ARRIVO + int(0.3 * FPS)
F_SCOSSE = F_APRE + int(0.35 * FPS)             # da qui la piastra vibra (e, se richiesto, il carosello scuote)
D_SCOSSE = int(T_VIBRA * FPS)
FINE = F_SCOSSE + D_SCOSSE + int(0.8 * FPS)
def phi(f):
    if f <= ASSESTA: return PHI0
    if f <= F_ARRIVO: return PHI0 + VEL * (f - ASSESTA) / FPS
    base = PHI0 - PARTENZA
    if SCOSSE and F_SCOSSE < f <= F_SCOSSE + D_SCOSSE:
        u = (f - F_SCOSSE) / D_SCOSSE
        return base + 3.0 * math.sin(2 * math.pi * 3 * u)
    return base
sc.frame_start, sc.frame_end = 1, FINE
rw.point_cache.frame_start, rw.point_cache.frame_end = 1, FINE
prima = None
for f in range(1, FINE + 1):
    p_ = phi(f)
    u = (f - F_SCOSSE) / FPS
    zp = VIBRA_MM * 0.5 * (1 - math.cos(2 * math.pi * VIBRA_HZ * u)) if 0 <= u <= T_VIBRA and VIBRA_MM > 0 else 0.0
    piastra.location = (zp * VIBRA_X, 0, zp); piastra.keyframe_insert("location", frame=f)
    su = min(1.0, max(0.0, (f - F_APRE) / (0.2 * FPS)))
    sportello.location = (0, 0, 40 * su); sportello.keyframe_insert("location", frame=f)
    if p_ == prima: continue
    prima = p_
    for j, p in enumerate(palette):
        th = p_ + j * PASSO
        p.rotation_euler = (0, 0, math.radians(th)); p.location = (0, 0, quota_pal(th))
        p.keyframe_insert("rotation_euler", frame=f); p.keyframe_insert("location", frame=f)

# ---------------------------------------------------------------- simulazione
def dove(o):
    x, y, z = o.matrix_world.translation
    return x, y, z
traccia = {id(p["o"]): [] for p in pillole}
for f in range(1, FINE + 1):
    sc.frame_set(f)
    if f % 25 == 0 or f == FINE:
        for p in pillole: traccia[id(p["o"])].append((f,) + tuple(round(c, 2) for c in dove(p["o"])))

# ---------------------------------------------------------------- verdetto
def nella_vasca(x, y, z): return x > X1_SC and abs(y) < W_SC + SVASO + 0.5 and z < Z1_SC + 12.0
def al_bordino(x, y, z): return x > X2_SC - 26.0 and nella_vasca(x, y, z)
res = []
for p in pillole:
    t = traccia[id(p["o"])]
    x, y, z = t[-1][1:]
    r = math.hypot(x, y); th = math.degrees(math.atan2(y, x))
    zmax = max(z_ for _, x_, y_, z_ in t if _ <= F_ARRIVO + 5)
    sul_ripiano = any(abs(math.degrees(math.atan2(y_, x_))) < RIPIANO + 1 and z_ > H - 1 for f_, x_, y_, z_ in t if F_ARRIVO - 5 <= f_ <= F_APRE)
    fermo = math.dist(t[-1][1:], t[-3][1:]) < 0.8
    persa = z < -8 or r < R_MOZZO - 1 or (r > R + 3.5 and not nella_vasca(x, y, z) and x < X0_SC - 2)
    if p["ruolo"] == "dose":
        ok = nella_vasca(x, y, z) and fermo
        motivo = "" if ok else ("ferma sul ripiano" if r < X0_SC + 1 else "ferma a meta' scivolo" if not nella_vasca(x, y, z) else "ancora in movimento")
    else:
        rel = (th - phi(FINE)) % 360.0; comp = int(rel // PASSO)
        ok = r <= R + 1 and not nella_vasca(x, y, z) and not persa
        motivo = "" if ok else ("uscita dallo scivolo" if r > R + 1 else "persa")
    res.append(dict(ruolo=p["ruolo"], pillola=p["nome"], ok=ok, in_fondo_al_bordino=al_bordino(x, y, z), motivo=motivo, arrivata_sul_ripiano=sul_ripiano, fine=[round(x, 1), round(y, 1), round(z, 1)]))
ok_dose = all(r["ok"] for r in res if r["ruolo"] == "dose")
ok_vicini = all(r["ok"] for r in res if r["ruolo"] == "vicino")
esito = dict(vibrazione=dict(hz=VIBRA_HZ, mm=VIBRA_MM, s=T_VIBRA), seme=SEME, attrito=MU, gioco=GIOCO, pendenza=PEND, scivolo_gradi=ANG_SC, scosse=SCOSSE, carico=os.environ.get("CARICO", "misto"),
             dose_completa=ok_dose, vicini_al_loro_posto=ok_vicini, pillole=res)
json.dump(esito, open(os.path.join(OUT, f"esito_{SEME}.json"), "w"), ensure_ascii=False, indent=1)
if "--salva" in sys.argv: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"sim_{SEME}.blend"))
print("ESITO", SEME, "dose", "OK" if ok_dose else "NO", "vicini", "OK" if ok_vicini else "NO", [(r["pillola"], r["motivo"]) for r in res if not r["ok"]])
if os.environ.get("DEBUG"):
    print("varco +-%.1f  ripiano +-%.1f  W_SC %.1f  X0 %.1f Z0 %.1f X1 %.1f Z1 %.1f" % (VARCO, RIPIANO, W_SC, X0_SC, Z0_SC, X1_SC, Z1_SC))
    for p in pillole:
        t = traccia[id(p["o"])]
        sel = [x for x in t if x[0] in (ASSESTA // 25 * 25, F_ARRIVO // 25 * 25, F_SCOSSE // 25 * 25, (F_SCOSSE + D_SCOSSE // 2) // 25 * 25, (F_SCOSSE + D_SCOSSE) // 25 * 25, FINE)]
        print(p["ruolo"], p["nome"])
        for f_, x, y, z in sel: print("   f%4d r %5.1f th %6.1f z %5.1f   rel %5.1f" % (f_, math.hypot(x, y), math.degrees(math.atan2(y, x)), z, (math.degrees(math.atan2(y, x)) - phi(f_)) % 360 / PASSO))
