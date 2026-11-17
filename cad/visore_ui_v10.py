# Costruisce docs/modello-3d/v10.html: interfaccia nuova (raggi X, sezione, ingranaggi che girano,
# pezzi per gruppi con etichette al passaggio del mouse) sopra il motore del visore v1.0.
# Uso: python3 cad/visore_ui_v10.py cad/visore_v10/motore.js cad/visore_v10/come.html cad/visore_v10/pagina.html docs/modello-3d/v10.html
import sys, os

script, come, testa = (open(p).read() for p in sys.argv[1:4])

def via(vecchio, nuovo, n=1):
    global script
    assert script.count(vecchio) == n, (script.count(vecchio), vecchio[:80])
    script = script.replace(vecchio, nuovo)

# ---- testi nuovi (con ripiego sui vecchi)
UI = r"""
const UI = {
  en: { altre: 'Other versions', mNormale: 'Normal', mRaggi: 'X-ray', mSezione: 'Section', aFronte: 'Front', aLato: 'Side', aAlto: 'Top',
    vFronte: 'Front', vLato: 'Side', vDietro: 'Back', vSopra: 'Top', vReset: 'Reset',
    sUsa: 'Use it', sPezzi: 'Parts', sIngr: 'Gears', sInfo: 'Info', usaTit: 'Try a dose',
    contesto: 'Show the rest as see-through', cerca: 'Search a part (e.g. motor, sensor, gel)', nascondi: 'Hide', mostra: 'Show',
    ingTit: 'Geneva drive, working', sinistra: 'Left', destra: 'Right', entrambe: 'Both',
    lMotore: 'Pinion (motor)', lCroce: '24-tooth gear', lRuota: 'Wheel', lScomp: 'Compartment', velocita: 'Speed',
    ingGuscio: 'Show the outline of the case', play: '❚❚ Pause', pausa: '▶ Turn', passo: 'One compartment →',
    faseVa: 'Pin in a slot: the wheel moves', faseFerma: 'Locking disc: the wheel stays still',
    spiega: (zp, zc) => 'The N20 motor turns the ' + zp + '-tooth pinion, which turns the ' + zc + '-tooth gear. A steel pin on the gear enters one slot of the wheel for 156° of every turn and pushes it forward by exactly one compartment (24°). For the other 204° the round locking disc holds the wheel still, so it cannot slip even if someone pushes it.',
    nota: (zp, zc) => 'One turn of the gear = one compartment. The pinion turns ' + (zc / zp).toLocaleString('en-GB') + ' times for each turn of the gear. The pills are hidden in this view, and the dose simulation waits until you leave this tab.',
    sel: (g, k) => g + (k > 1 ? ' · ' + k + ' pieces' : '') },
  it: { altre: 'Altre versioni', mNormale: 'Normale', mRaggi: 'Raggi X', mSezione: 'Sezione', aFronte: 'Fronte', aLato: 'Lato', aAlto: 'Alto',
    vFronte: 'Davanti', vLato: 'Lato', vDietro: 'Dietro', vSopra: 'Sopra', vReset: 'Reset',
    sUsa: 'Usala', sPezzi: 'Pezzi', sIngr: 'Ingranaggi', sInfo: 'Info', usaTit: 'Prova una dose',
    contesto: 'Mostra il resto in trasparenza', cerca: 'Cerca un pezzo (es. motorino, sensore, gel)', nascondi: 'Nascondi', mostra: 'Mostra',
    ingTit: 'Croce di Malta in funzione', sinistra: 'Sinistra', destra: 'Destra', entrambe: 'Entrambe',
    lMotore: 'Pignone (motorino)', lCroce: 'Ingranaggio da 24', lRuota: 'Ruota', lScomp: 'Scomparto', velocita: 'Velocità',
    ingGuscio: 'Mostra il profilo del guscio', play: '❚❚ Pausa', pausa: '▶ Gira', passo: 'Uno scomparto →',
    faseVa: 'Il perno è nella fessura: la ruota avanza', faseFerma: 'Disco di blocco: la ruota sta ferma',
    spiega: (zp, zc) => 'Il motorino N20 gira il pignone da ' + zp + ' denti, che gira l\'ingranaggio da ' + zc + '. Sull\'ingranaggio c\'è un perno d\'acciaio: per 156° di ogni giro entra in una fessura della ruota e la spinge avanti di uno scomparto esatto (24°). Per gli altri 204° il disco di blocco tiene ferma la ruota, che non scivola neanche se qualcuno la spinge.',
    nota: (zp, zc) => 'Un giro dell\'ingranaggio = uno scomparto. Il pignone fa ' + (zc / zp).toLocaleString('it-IT') + ' giri per ogni giro dell\'ingranaggio. In questa vista le pillole sono nascoste, e la simulazione della dose aspetta finché non esci da questa scheda.',
    sel: (g, k) => g + (k > 1 ? ' · ' + k + ' pezzi' : '') } };
const t = k => (k in UI[LANG] ? UI[LANG][k] : TX[LANG][k]);"""
via("const t = k => TX[LANG][k];", UI)

# ---- taglio (sezione) su tutti i materiali
via("renderer.setPixelRatio(Math.min(devicePixelRatio, 2));\nrenderer.toneMapping",
    "renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.localClippingEnabled = true;\n"
    "const TAGLIO = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 1e5), CLIP = [TAGLIO];\n"
    "const conTaglio = m => { m.clippingPlanes = CLIP; m.clipShadows = true; m.premultipliedAlpha = true; return m; };   // premoltiplicato: i pezzi trasparenti non bucano lo sfondo della pagina\nrenderer.toneMapping")
via("const tp = tipo(n), m = new THREE.Mesh(morbida(GEO[n]), MAT[tp.mat]());",
    "const tp = tipo(n), m = new THREE.Mesh(morbida(GEO[n]), conTaglio(MAT[tp.mat]()));")
via("new THREE.MeshPhysicalMaterial({ map: tex, roughness: .35 })", "conTaglio(new THREE.MeshPhysicalMaterial({ map: tex, roughness: .35 }))")
via("new THREE.MeshPhysicalMaterial({ color: c.colore, roughness: .55, clearcoat: .2 })", "conTaglio(new THREE.MeshPhysicalMaterial({ color: c.colore, roughness: .55, clearcoat: .2 }))")
via("new THREE.MeshPhysicalMaterial({ color: c2 ? '#ffffff' : c1, vertexColors: !!c2, roughness: .38, clearcoat: .55, clearcoatRoughness: .25 })",
    "conTaglio(new THREE.MeshPhysicalMaterial({ color: c2 ? '#ffffff' : c1, vertexColors: !!c2, roughness: .38, clearcoat: .55, clearcoatRoughness: .25 }))")
via("new THREE.LineBasicMaterial({ color: '#7d8794', transparent: true, opacity: .35, depthWrite: false })",
    "conTaglio(new THREE.LineBasicMaterial({ color: '#7d8794', transparent: true, opacity: .35, depthWrite: false }))")

# ---- ingranaggi: la croce gira da sola e la ruota segue (solo la vista; la fisica aspetta)
via("const angoloCroce = (giro, segno) =>",
    "const ing = { on: false, play: true, th: 0, meta: null, vel: 60, lato: 0, guscio: true };\n"
    "const giroDaCroce = (th, segno) => { const k = Math.floor(th / 360), r = th - 360 * k, f = r < 102 ? 0 : r < 258 ? (r - 102) / 156 : 1; return -(k + f) * segno * PASSO; };\n"
    "const ingLato = i => ing.on && (ing.lato === 2 || ing.lato === i);\n"
    "const segnoCroce = i => P.CROCI['c_motore_' + (i + 1) + '_croce'].segno;\n"
    "const extraGiro = i => ingLato(i) ? giroDaCroce(ing.th, segnoCroce(i)) : 0;\n"
    "const angC = i => angoloCroce(lati[i].giro, segnoCroce(i)) + (ingLato(i) ? ing.th : 0);\n"
    "const angoloCroce = (giro, segno) =>")
via("  for (const L of lati) {\n    L.gira.rotation.y = L.giro * rad;",
    "  lati.forEach((L, i) => {\n    L.gira.rotation.y = (L.giro + extraGiro(i)) * rad;")
via("    L.gira.position.y = L.s * 38 * e; G['10_sportellini_' + L.nome].position.y = L.s * 30 * e;\n  }",
    "    L.gira.position.y = L.s * 38 * e; G['10_sportellini_' + L.nome].position.y = L.s * 30 * e;\n  });")
via("g.rotation.y = cr ? angoloCroce(lati[i].giro, cr.segno) * P.Z_CROCE / P.Z_PIGN_G * rad :",
    "g.rotation.y = cr ? angC(i) * P.Z_CROCE / P.Z_PIGN_G * rad :")
via("g.rotation.y = -angoloCroce(lati[i].giro, cr.segno) * rad;", "g.rotation.y = -angC(i) * rad;")
via("ferma = esploso > 0 || esplosoMeta > 0;", "ferma = esploso > 0 || esplosoMeta > 0 || ing.on;")
via("schermo.visible = !trasparente && !scelta && e < .02;", "schermo.visible = modo === 'normale' && !ing.on && !scelta && e < .02;")
via("cavi.visible = e < .02 || caviScelti; G['nastro_cavi'].visible = (e < .02 && !scelta) || (!!scelta && scelta.mesh.has(G['nastro_cavi']));",
    "cavi.visible = (e < .02 || caviScelti) && !ing.on && !nascosti.has('elec'); G['nastro_cavi'].visible = ((e < .02 && !scelta) || (!!scelta && scelta.mesh.has(G['nastro_cavi']))) && !ing.on && !nascosti.has('elec');")
via("new ResizeObserver(misura).observe(box); misura();",
    "new ResizeObserver(misura).observe(box); misura();\n"
    "const faro = new THREE.DirectionalLight(0xffffff, 0); scene.add(faro, faro.target);   // luce dalla camera: si vede bene anche dentro e dietro")
via("function misura() { const w = box.clientWidth, h = box.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }",
    "function misura() { const w = box.clientWidth, h = box.clientHeight, pa = document.querySelector('.pannello'), pw = innerWidth > 860 && pa ? pa.offsetWidth + 26 : 0;   // il modello sta al centro dello spazio libero, non sotto il pannello\n"
    "  renderer.setSize(w, h, false); camera.aspect = (w + pw) / h; if (pw) camera.setViewOffset(w + pw, h, pw, 0, w, h); else camera.clearViewOffset(); camera.updateProjectionMatrix(); }")

# ---- camera: viste, centro degli ingranaggi
via("let az = -0.62, el = 0.26, dist = 640, distMeta = null, azMeta = null;",
    "let az = -0.62, el = 0.26, dist = 640, distMeta = null, azMeta = null, elMeta = null;")
via("  if (scelta) { scatola.makeEmpty();", "  if (ing.on) cMeta.copy(ing.centro); else if (scelta) { scatola.makeEmpty();")
via("el += (.3 - el) * k; if (Math.abs(d) < .01) azMeta = null; }",
    "el += ((elMeta ?? .3) - el) * k; if (Math.abs(d) < .01 && Math.abs((elMeta ?? .3) - el) < .01) azMeta = elMeta = null; }")
via("if (punt.size === 1) { azMeta = null;", "if (punt.size === 1) { azMeta = elMeta = null;")

# ---- comandi vecchi tolti o cambiati
via("  premi($('dentro'), trasparente, t('dentroOn'), t('dentroOff')); premi($('mini'), conMini, t('miniOn'), t('miniOff'));",
    "  premi($('mini'), conMini, t('miniOn'), t('miniOff'));")
via("$('dentro').onclick = () => { trasparente = !trasparente; etichette(); };\n", "")
via("a.download = 'blistra-pill-box-v09.png'", "a.download = 'blistra-pill-box-v10.png'")
via("fa: () => { if (!trasparente) $('dentro').click(); } }", "fa: () => setModo('raggi') }")
via("fa: () => { if (scelta) scegli(null); if (trasparente) $('dentro').click(); if (esplosoMeta < .5) $('smonta').click(); } }",
    "fa: () => { if (scelta) scegli(null); setModo('normale'); if (esplosoMeta < .5) $('smonta').click(); } }")
via("document.querySelectorAll('.comandi button, .comandi input').forEach(",
    "document.querySelectorAll('.pannello button, .modi button, .modi input, .viste button').forEach(")
via("if (on) { if (scelta) scegli(null); if (esplosoMeta) $('smonta').click(); }",
    "if (on) { if (scelta) scegli(null); if (esplosoMeta) $('smonta').click(); apriScheda('usa'); }")

# ---- aspetto: modi, gruppi nascosti, scelta con contesto, passaggio del mouse, ingranaggi
i0 = script.index("function aspetto() {"); i1 = script.index("function scegli(")
script = script[:i0] + r"""const VELATI = new Set(['10_sportellini_sx', '10_sportellini_dx', '4_imbuto', '17_staffa_alta']), RUOTE = /^10_(ruota|spazzole|tappo)/;
const INGR = /^(10_ruota_|c_motore_\d_(pignone|croce)|d_motore|c_assi_acciaio)/;
const latoDi = n => /_sx$|c_motore_1/.test(n) ? 0 : /_dx$|c_motore_2/.test(n) ? 1 : -1;
let modo = 'normale', contesto = true, sopra = null; const nascosti = new Set();
function aspetto() {
  const ora = performance.now();
  for (const m of TUTTE) {
    const x = m.material, o = x.userData.o, n = m.userData.nome; let tr = o.tr, op = o.op, dw = o.dw, acceso = 0, vis = !nascosti.has(m.userData.gr);
    if (modo === 'raggi') { if (GUSCIO.has(n)) { tr = true; op = .05; dw = false; } else if (CASSE.has(n)) { tr = true; op = .14; dw = false; } else if (VELATI.has(n)) { tr = true; op = Math.min(op, .3); dw = false; } else if (RUOTE.test(n)) { tr = true; op = .42; dw = false; } }
    if (ing.on) {
      const l = latoDi(n), mio = INGR.test(n) && (l < 0 || ing.lato === 2 || l === ing.lato);
      if (mio) { vis = true; if (ing.lato === 2 && /^10_ruota/.test(n)) { tr = true; op = .45; dw = false; } }
      else vis = false;
    }
    if (scelta) {
      if (scelta.mesh.has(m)) { tr = o.tr; op = o.op; dw = o.dw; acceso = 1; vis = true; }
      else if (contesto && vis) { tr = true; op = Math.min(op, .06); dw = false; }
      else vis = false;
    } else if (sopra && sopra.mesh.has(m)) acceso = .55;
    m.visible = vis; if (x.transparent !== tr) { x.transparent = tr; x.needsUpdate = true; }   // senza needsUpdate three.js resta 'opaco' e il pezzo non diventa trasparente
    x.opacity = op; x.depthWrite = dw; m.castShadow = op > .5 && o.op > .5;
    if (x.emissive) { if (acceso) { x.emissive.copy(VERDE); x.emissiveIntensity = acceso * (.26 + .1 * Math.sin(ora / 300)); } else { x.emissive.copy(o.em); x.emissiveIntensity = o.ei; } }
  }
  for (const p of pillole) if (p.stato !== 'tolta') p.m.visible = !scelta && !ing.on;
  const bordi = (modo === 'raggi' && !scelta) || (ing.on && ing.guscio) || (!!scelta && !contesto);
  for (const [m, l] of PROFILI) { l.material.opacity = ing.on ? .12 : .35; l.visible = bordi && !(scelta && scelta.mesh.has(m)); l.position.copy(m.position); l.quaternion.copy(m.quaternion); }
  for (const L of lati) L.disco.visible = !scelta && !ing.on;
}
""" + script[i1:]

# scegli: scheda del pezzo nel pannello invece di scorrere la pagina
via("    if (!daTocco) box.scrollIntoView({ behavior: 'smooth', block: 'center' });\n  } else { distMeta = 640; $('didascalia').classList.remove('on'); }",
    "    $('scheda').hidden = false; $('schedaNome').textContent = scelta.nome; $('schedaGr').textContent = t('sel')(GRUPPI[scelta.gr][IT ? 0 : 1], scelta.mesh.size);\n"
    "    if (daTocco) apriScheda('pezzi', true);\n"
    "  } else { distMeta = 640; $('didascalia').classList.remove('on'); $('scheda').hidden = true; }")
via("  scelta = chiave && VOCI.has(chiave)", "  if (ing.on && chiave) apriScheda('pezzi', true);\n  scelta = chiave && VOCI.has(chiave)")

# elenco: ricerca e gruppi da nascondere
i0 = script.index("(function elenco() {"); i1 = script.index("const S2 = P.STAB")
script = script[:i0] + r"""for (const v of VOCI.values()) for (const m of v.mesh) m.userData.gr = v.gr;
function elenco() {
  const per = {}, q = $('cerca').value.trim().toLowerCase();
  for (const v of VOCI.values()) if (!q || v.nome.toLowerCase().includes(q) || GRUPPI[v.gr][IT ? 0 : 1].toLowerCase().includes(q)) (per[v.gr] = per[v.gr] || []).push(v);
  const esc = s => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  $('parti').innerHTML = Object.keys(GRUPPI).filter(g => per[g]).map(g => '<div class="gruppo-tit"><h3>' + GRUPPI[g][IT ? 0 : 1] + '</h3><button class="occhio" data-g="' + g + '" aria-pressed="' + !nascosti.has(g) + '">' + (nascosti.has(g) ? t('mostra') : t('nascondi')) + '</button></div><div class="chips">'
    + per[g].map(v => '<button aria-pressed="' + (scelta && scelta.chiave === v.chiave) + '" class="' + (nascosti.has(g) ? 'spento' : '') + '" data-k="' + esc(v.chiave) + '"><i style="background:#' + MAT[v.mat]().color.getHexString() + '"></i>' + esc(v.nome) + '</button>').join('') + '</div>').join('') || '<p>—</p>';
}
$('parti').onclick = ev => { const b = ev.target.closest('button'); if (!b) return; fermaTour();
  if (b.dataset.g) { const g = b.dataset.g; nascosti.has(g) ? nascosti.delete(g) : nascosti.add(g); elenco(); return; }
  scegli(b.dataset.k); elenco(); };
$('parti').onpointerover = ev => { const b = ev.target.closest('button[data-k]'); sopra = b ? VOCI.get(b.dataset.k) : null; };
$('parti').onpointerleave = () => { sopra = null; };
$('cerca').placeholder = t('cerca'); $('cerca').oninput = elenco;
$('contesto').onchange = ev => { contesto = ev.target.checked; };
$('tutto').textContent = t('tutto'); $('tutto').onclick = () => { scegli(null); elenco(); };
elenco();

// ---------------- schede del pannello
function apriScheda(k, piano = false) {
  document.querySelectorAll('.schede button').forEach(b => b.setAttribute('aria-selected', b.dataset.scheda === k));
  document.querySelectorAll('.corpo').forEach(c => { c.hidden = c.dataset.pagina !== k; });
  const vuole = k === 'ingr'; if (vuole !== ing.on) attivaIngranaggi(vuole);
  if (k === 'pezzi') elenco();
}
document.querySelectorAll('.schede button').forEach(b => b.onclick = () => { fermaTour(); apriScheda(b.dataset.scheda); });

// ---------------- modi di vista: normale, raggi X, sezione
const LATI_SIDE = new Set();
function setModo(m) {
  const prima = modo; modo = m;
  document.querySelectorAll('#modi button').forEach(b => b.setAttribute('aria-pressed', b.dataset.modo === m));
  $('pannelloSezione').hidden = m !== 'sezione';
  if ((m === 'sezione') !== (prima === 'sezione')) {   // nella sezione si vedono anche le facce interne
    for (const x of new Set([...TUTTE.map(o => o.material), ...pillole.map(p => p.m.material)])) { x.side = m === 'sezione' ? THREE.DoubleSide : (x.userData.o ? x.userData.o.side : THREE.FrontSide); x.needsUpdate = true; }
    if (m === 'sezione') { const a = ASSI[asse]; azMeta = a.az; elMeta = a.el; }
  }
}
for (const m of TUTTE) m.material.userData.o.side = m.material.side;
document.querySelectorAll('#modi button').forEach(b => b.onclick = () => { fermaTour(); setModo(b.dataset.modo); });
const ASSI = { x: { n: [-1, 0, 0], a: -60, b: 72, az: 0.12, el: .2 }, y: { n: [0, -1, 0], a: -62, b: 62, az: Math.PI / 2 - .1, el: .2 }, z: { n: [0, 0, -1], a: 0, b: 215, az: -0.4, el: 1.0 } };
let asse = 'x';
document.querySelectorAll('#assi button').forEach(b => b.onclick = () => { asse = b.dataset.asse; document.querySelectorAll('#assi button').forEach(c => c.setAttribute('aria-pressed', c === b)); azMeta = ASSI[asse].az; elMeta = ASSI[asse].el; });
function aggiornaTaglio() {
  if (modo !== 'sezione') { TAGLIO.constant = 1e5; return; }
  const a = ASSI[asse], v = $('taglio').value / 100; TAGLIO.normal.set(...a.n); TAGLIO.constant = a.a + (a.b - a.a) * v;
}

// ---------------- viste rapide
const VISTE = { fronte: [0, .18, 560], lato: [-Math.PI / 2, .2, 560], dietro: [Math.PI, .22, 600], sopra: [-.5, 1.3, 620], reset: [-.62, .26, 640] };
document.querySelectorAll('#viste button').forEach(b => b.onclick = () => { fermaTour(); const [a, e, d] = VISTE[b.dataset.vista];
  if (b.dataset.vista === 'reset') { if (scelta) scegli(null); setModo('normale'); esplosoMeta = 0; nascosti.clear(); elenco(); etichette(); }
  azMeta = a; elMeta = e; if (!ing.on) distMeta = d; });

// ---------------- ingranaggi in funzione
function attivaIngranaggi(on) {
  ing.on = on; ing.th = 0; ing.meta = null;
  if (on) { if (scelta) scegli(null); esplosoMeta = 0; etichette(); inquadraIngr(); }
  else { azMeta = -.62; elMeta = .26; distMeta = 640; }
}
function inquadraIngr() {
  const pv = i => new THREE.Vector3(...P.CROCI['c_motore_' + (i + 1) + '_croce'].pivot);
  ing.centro = ing.lato === 2 ? pv(0).add(pv(1)).multiplyScalar(.5).add(new THREE.Vector3(0, 0, -12)) : pv(ing.lato).add(new THREE.Vector3(-8, 0, -10));
  azMeta = ing.lato === 1 ? -Math.PI / 2 : Math.PI / 2; elMeta = ing.lato === 2 ? .35 : .12; distMeta = ing.lato === 2 ? 420 : 300;
}
document.querySelectorAll('#ingLato button').forEach(b => b.onclick = () => { ing.lato = +b.dataset.lato; document.querySelectorAll('#ingLato button').forEach(c => c.setAttribute('aria-pressed', c === b)); inquadraIngr(); });
const etiPlay = () => { $('ingPlay').textContent = ing.play ? t('play') : t('pausa'); $('ingPlay').setAttribute('aria-pressed', ing.play); };
$('ingPlay').onclick = () => { ing.play = !ing.play; ing.meta = null; etiPlay(); };
$('ingPasso').onclick = () => { ing.play = false; etiPlay(); ing.meta = (Math.floor(ing.th / 360 + 1e-6) + 1) * 360; };
$('ingVel').oninput = ev => { ing.vel = +ev.target.value; };
$('ingGuscio').onchange = ev => { ing.guscio = ev.target.checked; };
$('ingSpiega').textContent = t('spiega')(P.Z_PIGN_G, P.Z_CROCE); $('ingNota').textContent = t('nota')(P.Z_PIGN_G, P.Z_CROCE); $('ingPasso').textContent = t('passo'); etiPlay();
const dc = $('disco').getContext('2d'), stile = () => getComputedStyle(document.documentElement);
let ultimaLettura = 0;
function aggiornaIngr(dt) {
  if (!ing.on) return;
  if (ing.meta !== null) { ing.th = Math.min(ing.meta, ing.th + dt * Math.max(90, ing.vel * 1.5)); if (ing.th >= ing.meta) ing.meta = null; }
  else if (ing.play) ing.th += dt * ing.vel;
  const ora = performance.now(); if (ora - ultimaLettura < 70) return; ultimaLettura = ora;
  const i = ing.lato === 1 ? 1 : 0, c = angC(i), r = ((c % 360) + 360) % 360, va = r > 102 && r < 258, ruota = Math.abs(lati[i].giro + extraGiro(i));
  const f = x => Math.round(x).toLocaleString(NUM) + '°';
  $('lMotore').textContent = f((c * P.Z_CROCE / P.Z_PIGN_G) % 360); $('lCroce').textContent = f(r); $('lRuota').textContent = f(ruota % 360);
  $('lScomp').textContent = (Math.round(ruota / PASSO) % P.N) + ' / ' + P.N;
  $('fase').textContent = va ? t('faseVa') : t('faseFerma'); $('fase').className = va ? 'va' : 'ferma';
  const cs = stile(), A = cs.getPropertyValue('--accent').trim(), L = cs.getPropertyValue('--line').trim(), I = cs.getPropertyValue('--ink').trim();
  dc.clearRect(0, 0, 264, 264); dc.lineWidth = 22; dc.lineCap = 'butt';
  const arco = (a0, a1, col) => { dc.strokeStyle = col; dc.beginPath(); dc.arc(132, 132, 104, (a0 - 90) * rad, (a1 - 90) * rad); dc.stroke(); };
  arco(0, 360, L); arco(102, 258, A);
  dc.strokeStyle = I; dc.lineWidth = 6; dc.lineCap = 'round'; dc.beginPath(); dc.moveTo(132, 132); dc.lineTo(132 + 92 * Math.cos((r - 90) * rad), 132 + 92 * Math.sin((r - 90) * rad)); dc.stroke();
  dc.fillStyle = I; dc.beginPath(); dc.arc(132, 132, 9, 0, 7); dc.fill();
}

// ---------------- etichetta al passaggio del mouse
let ultimoSopra = 0;
cv.addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse' || punt.size) { $('etichetta').classList.remove('on'); return; }
  const ora = performance.now(); if (ora - ultimoSopra < 90) return; ultimoSopra = ora;
  const r = cv.getBoundingClientRect(); mouse.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1); raggio.setFromCamera(mouse, camera);
  const colpi = raggio.intersectObjects(TUTTE.filter(m => m.visible && m.parent && m.parent.visible !== false), false).filter(h => h.object.userData.voce && h.object.material.opacity > .2 && TAGLIO.distanceToPoint(h.point) >= 0);
  const v = colpi.length ? VOCI.get(colpi[0].object.userData.voce) : null; sopra = scelta ? null : v;
  const et = $('etichetta'); if (v) { et.textContent = v.nome; et.style.left = (e.clientX - box.parentElement.getBoundingClientRect().left) + 'px'; et.style.top = (e.clientY - box.parentElement.getBoundingClientRect().top) + 'px'; et.classList.add('on'); cv.style.cursor = 'pointer'; }
  else { et.classList.remove('on'); cv.style.cursor = ''; }
});
cv.addEventListener('pointerleave', () => { sopra = null; $('etichetta').classList.remove('on'); });
""" + script[i1:]

# il tocco ignora quello che il taglio ha tolto o che e' quasi invisibile
via("const colpi = raggio.intersectObjects(TUTTE.filter(m => m.visible && m.parent && m.parent.visible !== false), false).filter(h => h.object.userData.voce);",
    "const colpi = raggio.intersectObjects(TUTTE.filter(m => m.visible && m.parent && m.parent.visible !== false), false).filter(h => h.object.userData.voce && TAGLIO.distanceToPoint(h.point) >= 0 && (h.object.material.opacity > .2 || scelta));")

# ciclo: ingranaggi e taglio
via("  logica(dt); suoni();", "  faro.position.copy(camera.position); faro.target.position.copy(c); faro.intensity = ing.on || modo !== 'normale' || scelta ? 1.4 : .3;\n  logica(dt); suoni();")
via("  if (esploso > 0) resto = 0;   // smontata: la fisica si ferma",
    "  if (esploso > 0 || ing.on) resto = 0;   // smontata o ingranaggi: la fisica si ferma\n  aggiornaIngr(dt); aggiornaTaglio();")
via("window.__v8 = { scegli,", "window.__v8 = { setModo, apriScheda, ing, scegli,")

# testi dei comandi che prima stavano in elenco (tasto della lingua ecc. restano)
via("document.getElementById('lingua').onclick =",
    "document.getElementById('versioni').onchange = ev => { location.href = ev.target.value + (IT ? '?lang=it' : ''); };\ndocument.getElementById('lingua').onclick =")

out = testa.replace('{{COME}}', come).replace('{{SCRIPT}}', script)
open(sys.argv[4], 'w').write(out)
print('scritto', sys.argv[4], len(out))
