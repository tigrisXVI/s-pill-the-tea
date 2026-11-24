// Pillole della S-pill: si aggiungono negli scomparti, girano con il carosello e, quando lo sportello
// e' aperto, cadono con una fisica semplice: gravita', attrito, rimbalzi, pareti di piastra, scivolo e bicchierino.
// Le compresse sono trattate come dischi che strisciano (non rotolano): e' cosi' che si muovono le pillole vere
// su piani poco inclinati. Misure in mm, tempo in secondi.

const G = 9810;                     // gravita' in mm/s^2
const ATTRITO = 0.35, ATTRITO_VIBRA = 0.13, RIMBALZO = 0.25;

export const FORME = {
  grande:  { it: 'Compressa grande (tipo Augmentin)', en: 'Large tablet (Augmentin-like)', mg: 1150, colore: '#ffffff',
             geo: T => { const g = new T.CapsuleGeometry(5.2, 11.5, 6, 16); g.rotateZ(Math.PI / 2); g.scale(1, 1, 0.72); return g; }, h: 3.75, rl: 10.95, rw: 5.2 },
  capsula: { it: 'Capsula', en: 'Capsule', mg: 480, colore: '#e8505b',
             geo: T => { const g = new T.CapsuleGeometry(3.4, 12.6, 6, 16); g.rotateZ(Math.PI / 2); return g; }, h: 3.4, rl: 9.7, rw: 3.4 },
  tonda:   { it: 'Compressa tonda', en: 'Round tablet', mg: 250, colore: '#f4d35e',
             geo: T => { const g = new T.CylinderGeometry(4.5, 4.5, 3.5, 24); g.rotateX(Math.PI / 2); return g; }, h: 1.75, rl: 4.5, rw: 4.5 },
  piccola: { it: 'Compressa piccola', en: 'Small tablet', mg: 90, colore: '#ffffff',
             geo: T => { const g = new T.CylinderGeometry(2.5, 2.5, 2.5, 18); g.rotateX(Math.PI / 2); return g; }, h: 1.25, rl: 2.5, rw: 2.5 },
  mini:    { it: 'Minicompressa', en: 'Mini tablet', mg: 12, colore: '#7fb7e6',
             geo: T => { const g = new T.CylinderGeometry(1.2, 1.2, 2.2, 14); g.rotateX(Math.PI / 2); return g; }, h: 1.1, rl: 1.2, rw: 1.2 },
};

export function creaPillole(T, scena, PAR, zFondo) {
  const rad = Math.PI / 180, TAN = Math.tan(PAR.PENDENZA * rad), TAN_SC = Math.tan(40 * rad);
  const C = PAR.CUP, MEZZO = PAR.PASSO / 2 - 0.35;
  const geos = {}, lista = [];
  const geo = f => geos[f] || (geos[f] = FORME[f].geo(T));
  const v3 = () => new T.Vector3(), tmp = v3(), n = v3(), q = new T.Quaternion(), su = new T.Vector3(0, 0, 1), avanti = v3(), m4 = new T.Matrix4();
  const zSc = x => PAR.Z0_SC - Math.max(0, x - PAR.X0_SC) * TAN_SC;
  const ySponda = x => PAR.W_SC + PAR.SVASO * Math.min(1, Math.max(0, (x - PAR.X0_SC) / (PAR.X1_SC - PAR.X0_SC)));

  // ---- aggiungere e togliere
  function aggiungi(f, k, colore) {
    const F = FORME[f], gia = lista.filter(p => p.stato === 'scomparto' && p.k === k);
    // cerca un posto libero nello scomparto: lungo il raggio, il lato lungo in direzione radiale
    let posto = null;
    for (let t = 0; t < 400 && !posto; t++) {
      const r = PAR.R_DISCO + 2 + F.rl + Math.random() * (PAR.R_FONDO - PAR.R_DISCO - 4 - 2 * F.rl);
      const lim = Math.max(0, Math.asin(Math.min(1, (r * Math.sin(MEZZO * rad) - F.rw - 0.4) / r)) / rad);
      const da = (Math.random() * 2 - 1) * lim;
      const ok = gia.every(p => { const dx = r - p.r, dy = (da - p.da) * rad * r; return Math.abs(dx) > (F.rl + p.F.rl) * 0.95 || Math.abs(dy) > (F.rw + p.F.rw) * 0.95; });
      if (ok && r - F.rl > PAR.R_DISCO + 1) posto = { r, da };
    }
    if (!posto) return false;
    const m = new T.Mesh(geo(f), new T.MeshStandardMaterial({ color: colore || F.colore, roughness: .4 }));
    scena.add(m);
    lista.push({ m, f, F, k, ...posto, stato: 'scomparto', p: v3(), v: v3(), w: v3(), tocca: 0 });
    return true;
  }
  function togli(filtro) {
    for (let i = lista.length - 1; i >= 0; i--) if (filtro(lista[i])) { scena.remove(lista[i].m); lista[i].m.material.dispose(); lista.splice(i, 1); }
  }

  // ---- vincoli: pavimenti e pareti, con attrito e rimbalzo
  function contatto(p, nx, ny, nz, pen, mu, dt) {
    n.set(nx, ny, nz).normalize();
    if (n.z > 0.5) p.p.z += pen / n.z; else p.p.addScaledVector(n, pen);   // sui pavimenti si corregge solo in altezza: niente scivolamenti finti
    const vn = p.v.dot(n); let premuta = 0;
    if (vn < 0) { premuta = -vn; p.v.addScaledVector(n, -vn * (1 + (vn < -60 ? RIMBALZO : 0))); }   // rimbalza solo negli urti veri
    tmp.copy(p.v).addScaledVector(n, -p.v.dot(n));                     // velocita' lungo la superficie
    const vt = tmp.length(), freno = mu * premuta;                      // attrito di Coulomb: proporzionale alla spinta normale
    if (vt <= freno) p.v.sub(tmp); else p.v.addScaledVector(tmp, -freno / vt);
    p.tocca = 0.06; p.nx = n.x; p.ny = n.y; p.nz = n.z;
  }
  function parete(p, asse, limite, verso) {                             // verso +1: deve stare sotto il limite
    const val = p.p[asse];
    if (verso * (val - limite) > 0) { p.p[asse] = limite; if (verso * p.v[asse] > 0) p.v[asse] *= -RIMBALZO; }
  }
  function vincoli(p, s, dt) {
    const { x, y, z } = p.p, r = Math.hypot(x, y), F = p.F;
    if (x < PAR.X0_SC) {                                                  // piastra pesata (pende verso fuori di 8 gradi)
      const zf = PAR.Z_RIPIANO + TAN * (PAR.R_FONDO - Math.max(r, PAR.R_DISCO));
      if (z < zf + F.h) contatto(p, TAN * x / r, TAN * y / r, 1, (zf + F.h - z) * 0.99, s.vibra ? ATTRITO_VIBRA : ATTRITO, dt);
      const lim = Math.min(r * Math.sin(MEZZO * rad), PAR.W_SC + 0.3) - F.rw;   // palette ai lati, poi il varco nella parete
      parete(p, 'y', Math.max(0, lim), 1); parete(p, 'y', -Math.max(0, lim), -1);
      if (r < PAR.R_DISCO + F.rl) { p.p.x += 0.2; p.v.x = Math.max(0, p.v.x); }
      if (s.vibra) { p.v.x += (Math.random() - 0.3) * 900 * dt; p.v.y += (Math.random() - 0.5) * 900 * dt; p.v.z += Math.random() * 300 * dt; }
    } else if (x <= PAR.X_FINE_SC) {                                      // scivolo a 40 gradi, sponde che si allargano
      const zf = zSc(x);
      if (z < zf + F.h) contatto(p, TAN_SC, 0, 1, (zf + F.h - z) * Math.cos(40 * rad), ATTRITO, dt);
      const lim = ySponda(x) - F.rw; parete(p, 'y', lim, 1); parete(p, 'y', -lim, -1);
    }
    if (x > C.xm - F.rw) {                                                // bicchierino
      if (x < C.x0 && z < C.basso + F.h) {                                // sopra il muretto basso dietro
        if (z > C.basso - 2) contatto(p, 0, 0, 1, C.basso + F.h - z, ATTRITO, dt); else { p.p.x = C.x0 + F.rw; p.v.x = Math.abs(p.v.x) * RIMBALZO; }
      }
      if (x >= C.x0 - 0.01) {
        const pend = (C.zf - C.zb) / (C.x1 - C.x0), zf = C.zb + pend * (x - C.x0);
        if (z < zf + F.h) contatto(p, -pend, 0, 1, zf + F.h - z, ATTRITO, dt);
        parete(p, 'x', C.x1 - F.rw, 1); parete(p, 'y', C.y - F.rw, 1); parete(p, 'y', -C.y + F.rw, -1);
        if (p.p.z < C.basso + F.h) parete(p, 'x', C.x0 + F.rw, -1);
      }
    }
    if (p.p.z < F.h) { p.p.z = F.h; p.v.set(0, 0, 0); }
  }

  // urti tra pillole: dischi con raggio nel piano e mezzo spessore in altezza
  function urti() {
    const att = lista.filter(p => p.stato === 'fisica');
    for (let i = 0; i < att.length; i++) for (let j = i + 1; j < att.length; j++) {
      const a = att[i], b = att[j], R = (a.F.rl + a.F.rw + b.F.rl + b.F.rw) / 2, H = a.F.h + b.F.h;
      const dx = b.p.x - a.p.x, dy = b.p.y - a.p.y, dz = b.p.z - a.p.z;
      const d = Math.sqrt((dx * dx + dy * dy) / (R * R) + (dz * dz) / (H * H));
      if (d >= 1 || d === 0) continue;
      tmp.set(dx / (R * R), dy / (R * R), dz / (H * H)).normalize();
      const pen = (1 - d) * Math.min(R, H) * 0.5;
      a.p.addScaledVector(tmp, -pen); b.p.addScaledVector(tmp, pen);
      const vr = tmp.dot(n.copy(b.v).sub(a.v));
      if (vr < 0) { const j2 = -(1 + 0.2) * vr / 2; a.v.addScaledVector(tmp, -j2); b.v.addScaledVector(tmp, j2); }
    }
  }

  // ---- un fotogramma
  // s = { theta, sc, fermo, aperto, vibra, visibili }
  function aggiorna(s, dt) {
    // sportello aperto e carosello fermo: la dose sul ripiano passa alla fisica
    if (s.aperto > .9 && s.fermo && s.sc !== 0)
      lista.forEach(p => { if (p.stato === 'scomparto' && p.k === s.sc) { p.stato = 'fisica'; p.v.set(0, 0, 0); } });
    // sportello chiuso: quello che e' rimasto sulla piastra torna a girare con il carosello
    if (s.aperto < .05)
      lista.forEach(p => { if (p.stato === 'fisica' && p.p.x < PAR.X0_SC - 1 && p.v.length() < 30) {
        p.stato = 'scomparto'; p.k = s.sc; p.r = Math.hypot(p.p.x, p.p.y); p.da = Math.atan2(p.p.y, p.p.x) / rad - s.theta + p.k * PAR.PASSO; } });
    // nello scomparto: la pillola segue il carosello
    lista.forEach(p => {
      p.m.visible = s.visibili;
      if (p.stato !== 'scomparto') return;
      const a = -p.k * PAR.PASSO + p.da + s.theta;
      p.p.set(p.r * Math.cos(a * rad), p.r * Math.sin(a * rad), zFondo(a, p.r) + p.F.h);
      p.m.position.copy(p.p); p.m.rotation.set(0, 0, a * rad);
    });
    // fisica a piccoli passi
    const att = lista.filter(p => p.stato === 'fisica');
    if (att.length) {
      const passi = Math.ceil(dt / (1 / 600)), h = dt / passi;
      for (let i = 0; i < passi; i++) {
        for (const p of att) { p.v.z -= G * h; p.p.addScaledVector(p.v, h); p.tocca -= h; vincoli(p, s, h); }
        urti();
      }
      for (const p of att) {
        p.m.position.copy(p.p);
        if (p.tocca > 0) {                                                // appoggiata: piatta sulla superficie, il lato lungo nel verso del moto
          n.set(p.nx, p.ny, p.nz);
          tmp.copy(p.v).addScaledVector(n, -p.v.dot(n));
          if (tmp.lengthSq() > 25) avanti.copy(tmp).normalize(); else avanti.set(1, 0, 0).applyQuaternion(p.m.quaternion).addScaledVector(n, -0).normalize();
          const lato = v3().crossVectors(n, avanti).normalize(); avanti.crossVectors(lato, n);
          m4.makeBasis(avanti, lato, n); q.setFromRotationMatrix(m4);
          p.m.quaternion.slerp(q, 0.35); p.w.set(0, 0, 0);
        } else {                                                          // in volo: gira un po' su se stessa
          if (p.w.lengthSq() === 0) p.w.set(Math.random() - .5, Math.random() - .5, Math.random() - .5).multiplyScalar(14);
          q.setFromAxisAngle(tmp.copy(p.w).normalize(), p.w.length() * dt); p.m.quaternion.premultiply(q);
        }
      }
    }
  }

  // ---- cosa legge la bilancia e quante pillole sono arrivate
  function letture(s) {
    const suPiastra = p => p.stato === 'scomparto' ? p.k === s.sc : (p.p.x < PAR.X0_SC && Math.hypot(p.p.x, p.p.y) > PAR.R_DISCO && p.tocca > 0);
    const peso = s.sc === 0 ? 0 : lista.filter(suPiastra).reduce((t, p) => t + p.F.mg, 0);
    const prevista = lista.filter(p => p.k === s.sc && s.sc !== 0).reduce((t, p) => t + p.F.mg, 0);
    const nelBicchiere = lista.filter(p => p.stato === 'fisica' && p.p.x > PAR.X_FINE_SC).length;
    const inViaggio = lista.filter(p => p.stato === 'fisica' && p.p.x >= PAR.X0_SC && p.p.x <= PAR.X_FINE_SC).length;
    const sulRipiano = lista.filter(p => p.k === s.sc && (p.stato === 'scomparto' || p.p.x < PAR.X0_SC)).length;
    return { peso, prevista, nelBicchiere, inViaggio, sulRipiano };
  }

  return { lista, aggiungi, aggiorna, letture,
           svuotaBicchiere: () => togli(p => p.stato === 'fisica' && p.p.x > PAR.X_FINE_SC),
           svuotaTutto: () => togli(() => true) };
}
