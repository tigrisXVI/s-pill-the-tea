"""Simulazione fisica (pybullet) di uno scomparto della ruota che arriva sull'uscita.

Unita': centimetri, grammi, secondi. La ruota sta in piedi (asse lungo Y), l'uscita e' in basso.
Pezzi simulati:
  - anello fermo della cassetta (raggio interno R_AN_T) con l'uscita larga 2*APRE in basso
  - parete dietro e sportellini davanti (piani)
  - ruota: mozzo, divisori e due scivoli in ogni scomparto vicino all'anello (angolo 'alfa', larghezza 'w')
    mossa da un giunto con il profilo della croce di Malta (avanza di 24 gradi)
  - pillole vere: compresse grandi, medie, piccole, minuscole e capsule, messe a caso
Una prova: si riempie lo scomparto che sta per arrivare sull'uscita (e quello dopo), la ruota avanza di uno scomparto,
si aspetta 1,5 s. Riuscita = tutte le pillole della dose sono uscite. Perdita = e' uscita una pillola dello scomparto dopo.
"""
import math, random
import pybullet as p

N = 15; PASSO = 360.0 / N
R_I, R_O, G, PROF, SP_DIV = 2.3, 4.7, 0.03, 1.3, 0.1        # cm (come il modello CAD)
R_AN = R_O + G
PILLOLE = {   # nome: (forma, raggio, lunghezza/altezza) in cm
    "grande": ("disco", 0.52, 0.45), "media": ("disco", 0.40, 0.35), "piccola": ("disco", 0.30, 0.30),
    "minuscola": ("disco", 0.15, 0.16), "capsula": ("capsula", 0.30, 1.20),
}

def _box(he, pos, ang_y=0.0):
    return dict(he=he, pos=pos, orn=p.getQuaternionFromEuler([0, ang_y, 0]))

def ruota_pezzi(alfa, w):
    """Divisori, mozzo e scivoli nel riferimento della ruota (x, z nel piano della ruota, y = profondita')."""
    pezzi = []
    yc = PROF / 2
    for k in range(N):
        d = math.radians(-90 + PASSO / 2 + k * PASSO)          # divisorio
        rm = (R_I + R_O) / 2
        pezzi.append(_box([(R_O - R_I) / 2, PROF / 2, SP_DIV / 2], [rm * math.cos(d), yc, rm * math.sin(d)], -d))
    for k in range(24):                                          # mozzo (poligono)
        a = math.radians(k * 15)
        pezzi.append(_box([R_I * math.sin(math.radians(7.6)), PROF / 2, 0.08], [(R_I - 0.08) * math.cos(a), yc, (R_I - 0.08) * math.sin(a)], -(a + math.pi / 2)))
    if w > 0.02:                                                 # scivoli: dal divisorio verso il centro dello scomparto
        for k in range(N):
            c = -90 + k * PASSO
            for sgn in (-1, 1):
                dv = math.radians(c + sgn * (PASSO / 2 - 0.6))   # vicino al divisorio
                # punto sul bordo (raggio R_O) spostato verso il centro di w, e punto sul divisorio piu' in basso di h
                h = w * math.tan(math.radians(alfa))
                pa = (R_O * math.cos(dv), R_O * math.sin(dv))
                t = (-math.sin(dv) * -sgn, math.cos(dv) * -sgn)       # tangente verso il centro dello scomparto
                pb = (pa[0] + t[0] * w, pa[1] + t[1] * w)              # sul bordo, verso il centro
                rr = R_O - h
                pc = (rr * math.cos(dv), rr * math.sin(dv))            # sul divisorio, piu' dentro
                mx, mz = (pb[0] + pc[0]) / 2, (pb[1] + pc[1]) / 2
                L = math.hypot(pb[0] - pc[0], pb[1] - pc[1])
                ang = math.atan2(pb[1] - pc[1], pb[0] - pc[0])
                pezzi.append(_box([L / 2, PROF / 2, 0.05], [mx, yc, mz], -ang))
    return pezzi

def anello_pezzi(apre):
    pezzi = []
    n = 90
    for k in range(n):
        a0, a1 = 360 * k / n, 360 * (k + 1) / n
        am = math.radians((a0 + a1) / 2)
        x, z = (R_AN + 0.1) * math.cos(am), (R_AN + 0.1) * math.sin(am)
        if z < 0 and abs(x) < apre + 0.15: continue              # l'uscita
        L = 2 * (R_AN + 0.1) * math.sin(math.radians((a1 - a0) / 2)) + 0.02
        pezzi.append(_box([L / 2, PROF / 2 + 0.2, 0.1], [x, PROF / 2, z], -(am + math.pi / 2)))
    pezzi.append(_box([6, 0.1, 6], [0, -0.1, 0]))                 # parete dietro
    pezzi.append(_box([6, 0.1, 6], [0, PROF + 0.1, 0]))           # sportellini davanti
    return pezzi

def _compound(pezzi):
    return p.createCollisionShapeArray([p.GEOM_BOX] * len(pezzi), halfExtents=[q["he"] for q in pezzi],
                                       collisionFramePositions=[q["pos"] for q in pezzi], collisionFrameOrientations=[q["orn"] for q in pezzi])

def profilo_croce(t, T):
    """Angolo della ruota (0..1 di uno scomparto) con la croce di Malta: parte e arriva dolce."""
    if t <= 0: return 0.0
    if t >= T: return 1.0
    phi = math.radians(102 + 156 * t / T)                         # l'ingranaggio gira a velocita' costante
    C, r = 1.0 / math.cos(math.pi / N), math.tan(math.pi / N)    # in unita' del raggio della croce
    def ang(f): return math.atan2(r * math.sin(f), C - r * math.cos(f))
    a0, a1 = ang(math.radians(102)), ang(math.radians(258))
    return (ang(phi) - a0) / (a1 - a0)

def prova(gen, rng, cid, n_dose=None, vedi=False, difficile=True):
    """Una prova. gen = dict(apre, alfa, w). Ritorna (tutte_uscite, perdita)."""
    p.resetSimulation(physicsClientId=cid)
    p.setGravity(0, 0, -981, physicsClientId=cid)
    p.setPhysicsEngineParameter(fixedTimeStep=1 / 1000., numSolverIterations=30, physicsClientId=cid)
    for q in anello_pezzi(gen["apre"]):                            # pezzi fermi: un corpo statico per ogni lastrina
        b = p.createMultiBody(0, p.createCollisionShape(p.GEOM_BOX, halfExtents=q["he"], physicsClientId=cid), basePosition=q["pos"], baseOrientation=q["orn"], physicsClientId=cid)
        p.changeDynamics(b, -1, lateralFriction=0.35, restitution=0.2, physicsClientId=cid)
    # ruota: un link che gira (giunto) e tutte le lastrine attaccate a lui con giunti fissi
    pz = ruota_pezzi(gen["alfa"], gen["w"])
    shapes = [p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.05], physicsClientId=cid)] + [p.createCollisionShape(p.GEOM_BOX, halfExtents=q["he"], physicsClientId=cid) for q in pz]
    n = len(shapes)
    ruota = p.createMultiBody(0, -1, basePosition=[0, 0, 0], linkMasses=[50] + [1] * (n - 1), linkCollisionShapeIndices=shapes, linkVisualShapeIndices=[-1] * n,
                              linkPositions=[[0, 0, 0]] + [q["pos"] for q in pz], linkOrientations=[[0, 0, 0, 1]] + [q["orn"] for q in pz],
                              linkInertialFramePositions=[[0, 0, 0]] * n, linkInertialFrameOrientations=[[0, 0, 0, 1]] * n,
                              linkParentIndices=[0] + [1] * (n - 1), linkJointTypes=[p.JOINT_REVOLUTE] + [p.JOINT_FIXED] * (n - 1),
                              linkJointAxis=[[0, -1, 0]] + [[0, 0, 1]] * (n - 1), physicsClientId=cid)
    for j in range(n): p.changeDynamics(ruota, j, lateralFriction=0.35, restitution=0.2, physicsClientId=cid)
    a0 = -PASSO                                                    # lo scomparto della dose parte a -114 gradi, il prossimo a -138
    p.resetJointState(ruota, 0, math.radians(a0), physicsClientId=cid)
    def tieni(a): p.setJointMotorControl2(ruota, 0, p.POSITION_CONTROL, targetPosition=math.radians(a), force=1e7, positionGain=0.3, velocityGain=1, physicsClientId=cid)
    # pillole: nello scomparto della dose (a -114 gradi) e in quello dopo (-138)
    tipi = list(PILLOLE)
    pills = []
    def metti(c, n, gruppo):
        messe = []
        for _ in range(n):
            tipo = rng.choice(tipi); forma, r, L = PILLOLE[tipo]
            for _t in range(40):
                ang = math.radians(c + rng.uniform(-PASSO / 2 + 3, PASSO / 2 - 3)); rad = rng.uniform(R_I + 0.7, R_O - 0.7)
                pos = [rad * math.cos(ang), rng.uniform(0.35, PROF - 0.35), rad * math.sin(ang)]
                if all(math.dist(pos, q) > 1.25 for q in messe): break
            messe.append(pos)
            if forma == "disco": s = p.createCollisionShape(p.GEOM_CYLINDER, radius=r, height=L, physicsClientId=cid); vol = math.pi * r * r * L
            else: s = p.createCollisionShape(p.GEOM_CAPSULE, radius=r, height=L - 2 * r, physicsClientId=cid); vol = math.pi * r * r * (L - 2 * r) + 4 / 3 * math.pi * r ** 3
            orn = p.getQuaternionFromEuler([rng.uniform(0, 6.3), rng.uniform(0, 6.3), rng.uniform(0, 6.3)])
            b = p.createMultiBody(1.2 * vol, s, basePosition=pos, baseOrientation=orn, physicsClientId=cid)
            p.changeDynamics(b, -1, lateralFriction=attrito, restitution=0.2, rollingFriction=0.0005, ccdSweptSphereRadius=0.05, physicsClientId=cid)
            pills.append((b, gruppo))
    attrito = rng.uniform(0.3, 0.7) if difficile else 0.35          # compresse lisce o appiccicose (umidita')
    nd = n_dose if n_dose else (rng.randint(2, 8) if difficile else rng.randint(1, 6))
    metti(-90 - PASSO, nd, "dose"); metti(-90 - 2 * PASSO, 3, "dopo")
    tieni(a0)
    for _ in range(300): p.stepSimulation(physicsClientId=cid)   # si appoggiano
    T = gen.get("T", 1.0)
    for i in range(int(T * 1000) + 800):
        tieni(a0 + PASSO * profilo_croce(i / 1000, T))
        p.stepSimulation(physicsClientId=cid)
    fuori = lambda b: p.getBasePositionAndOrientation(b, physicsClientId=cid)[0][2] < -(R_AN + 0.25)
    tutte = all(fuori(b) for b, g in pills if g == "dose")
    perdita = any(fuori(b) for b, g in pills if g == "dopo")
    return tutte, perdita

def valuta(gen, n=16, seme=0, cid=None):
    rng = random.Random(seme)
    cid = cid if cid is not None else p.connect(p.DIRECT)
    ok = perse = 0
    for _ in range(n):
        t, pe = prova(gen, rng, cid)
        ok += t; perse += pe
    return ok / n, perse / n

if __name__ == "__main__":
    import time
    t0 = time.time()
    print("disegno attuale (APRE 7 mm, niente scivoli):", valuta(dict(apre=0.7, alfa=60, w=0.0), n=12), f"{time.time() - t0:.1f} s")
