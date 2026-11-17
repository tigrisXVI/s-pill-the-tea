"""Esporta la v1.0 per l'analisi ingegneristica e per la stampa:
STL (pezzi orientati per la stampa e assieme), STEP (pezzi e assieme con i nomi),
3MF (piatti di stampa pronti da aprire nello slicer e assieme colorato) e parametri di stampa."""
import os, sys, json, math, time
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scatoletta_v10 import Modello, genera, stampa, a_mesh, VERSI

QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, '..', 'v10')

from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.TDataStd import TDataStd_Name
from OCP.Interface import Interface_Static
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

def solido(mesh):
    """Mesh -> solido B-rep sfaccettato; le facce complanari vengono unite (file piu' leggero, facce piane vere)."""
    sew = BRepBuilderAPI_Sewing(1e-4)
    mesh = mesh.copy(); mesh.merge_vertices(); mesh.update_faces(mesh.nondegenerate_faces(height=1e-6)); mesh.remove_unreferenced_vertices()
    V = mesh.vertices
    for f in mesh.faces:
        p = BRepBuilderAPI_MakePolygon(*[gp_Pnt(*map(float, V[i])) for i in f], True)
        if not p.IsDone(): continue
        fc = BRepBuilderAPI_MakeFace(p.Wire(), True)
        if fc.IsDone(): sew.Add(fc.Face())
    sew.Perform(); sh = sew.SewedShape()
    ms = BRepBuilderAPI_MakeSolid()
    ex = TopExp_Explorer(sh, TopAbs_SHELL)
    while ex.More(): ms.Add(TopoDS.Shell(ex.Current())); ex.Next()
    s = ms.Solid() if ms.IsDone() else sh
    u = ShapeUpgrade_UnifySameDomain(s, True, True, False); u.Build()
    return u.Shape()

def scrivi_step(shape, nome, file):
    Interface_Static.SetCVal_s("write.step.schema", "AP214")
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    Interface_Static.SetCVal_s("write.step.product.name", nome)
    w = STEPControl_Writer(); w.Transfer(shape, STEPControl_AsIs); w.Write(file)

COLORI = {'1_guscio': (0.17, 0.2, 0.24), '2_cappello': (0.12, 0.44, 0.36), '3_piede': (0.17, 0.2, 0.24), '7_bicchierino': (0.95, 0.95, 0.93),
          '5_piattino': (0.93, 0.55, 0.2), '10_sportellini': (0.8, 0.9, 0.95), '19_sportello': (0.95, 0.95, 0.95)}
def colore(n):
    for k, c in COLORI.items():
        if n.startswith(k): return c
    return (0.93, 0.93, 0.9)

def main():
    t0 = time.time()
    solo_step = '--step' in sys.argv          # BLISTRA_SEG=64 python3 esporta_v10.py --step : STEP piu' leggeri
    if solo_step:
        import tempfile; tmp = tempfile.mkdtemp(); genera('2m', tmp); base = tmp
    else:
        genera('2m', os.path.join(OUT, 'stl')); base = os.path.join(OUT, 'stl')
    stl_st = os.path.join(base, 'stampa'); stl_as = os.path.join(base, 'assieme')
    for d in ('step', 'step/pezzi', '3mf'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, 'step', 'pezzi')): os.remove(os.path.join(OUT, 'step', 'pezzi', f))
    # ---- STEP dei pezzi (orientati come nell'assieme, coordinate del CAD in mm)
    shapes = {}
    for f in sorted(os.listdir(stl_as)):
        n = f[:-4]; m = trimesh.load(os.path.join(stl_as, f), force='mesh')
        s = solido(m); shapes[n] = s
        scrivi_step(s, n, os.path.join(OUT, 'step', 'pezzi', n + '.step'))
    for f in sorted(os.listdir(stl_st)):                 # croci e pignoni esistono solo in 'stampa'
        n = f[:-4]
        if n not in shapes and (n.startswith('14_') or n.startswith('15_')):
            s = solido(trimesh.load(os.path.join(stl_st, f), force='mesh')); shapes[n] = s
            scrivi_step(s, n, os.path.join(OUT, 'step', 'pezzi', n + '.step'))
    # ---- STEP dell'assieme con nomi e colori (pezzi stampati + componenti)
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    tutti = dict((n, s) for n, s in shapes.items() if not (n.startswith('14_') or n.startswith('15_')))
    for f in sorted(os.listdir(os.path.join(base, 'componenti'))):
        if f.startswith('viti'): continue          # viti filettate: solo nelle STL, nello STEP pesano troppo
        n = 'componente_' + f[:-4]; tutti[n] = solido(trimesh.load(os.path.join(base, 'componenti', f), force='mesh'))
    for n, s in tutti.items():
        lab = st.AddShape(s, False); TDataStd_Name.Set_s(lab, TCollection_ExtendedString(n))
        r, g, b = colore(n) if not n.startswith('componente_') else (0.3, 0.3, 0.32)
        ct.SetColor(lab, Quantity_Color(r, g, b, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    w = STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True)
    w.Transfer(doc, STEPControl_AsIs); w.Write(os.path.join(OUT, 'step', 'blistra_v10_assieme.step'))
    if solo_step: print('STEP fatti in', round(time.time() - t0), 's'); return
    # ---- 3MF: assieme colorato
    sc = trimesh.Scene()
    for f in sorted(os.listdir(stl_as)):
        m = trimesh.load(os.path.join(stl_as, f), force='mesh'); c = colore(f[:-4])
        m.visual.face_colors = [int(255 * c[0]), int(255 * c[1]), int(255 * c[2]), 255]
        sc.add_geometry(m, node_name=f[:-4], geom_name=f[:-4])
    with open(os.path.join(OUT, '3mf', 'blistra_v10_assieme.3mf'), 'wb') as fh: fh.write(trimesh.exchange.threemf.export_3MF(sc))
    # ---- 3MF: piatti di stampa (letto 250 x 210 mm, 10 mm tra i pezzi), pezzi gia' orientati
    BED = (250.0, 210.0); GAP = 10.0
    pezzi = sorted(((f[:-4], trimesh.load(os.path.join(stl_st, f), force='mesh')) for f in os.listdir(stl_st)), key=lambda x: -x[1].extents[1])
    piatti = []; cur = []; x = y = riga = 0.0
    for n, m in pezzi:
        w_, h_ = m.extents[0], m.extents[1]
        if x + w_ > BED[0]: x = 0.0; y += riga + GAP; riga = 0.0
        if y + h_ > BED[1] and cur: piatti.append(cur); cur = []; x = y = riga = 0.0
        cur.append((n, m, x, y)); x += w_ + GAP; riga = max(riga, h_)
    if cur: piatti.append(cur)
    elenco_piatti = []
    for i, pl in enumerate(piatti, 1):
        sc = trimesh.Scene()
        for n, m, x, y in pl:
            mm = m.copy(); b = mm.bounds; mm.apply_translation([x - b[0][0], y - b[0][1], -b[0][2]]); sc.add_geometry(mm, node_name=n, geom_name=n)
        fn = f'piatto_{i}.3mf'
        with open(os.path.join(OUT, '3mf', fn), 'wb') as fh: fh.write(trimesh.exchange.threemf.export_3MF(sc))
        elenco_piatti.append((fn, [n for n, *_ in pl]))
    # ---- parametri di stampa per pezzo
    def regole(n):
        fine = any(n.startswith(k) for k in ('10_', '5_', '4_', '7_', '16_', '18_', '19_'))
        mecc = any(n.startswith(k) for k in ('14_', '15_', '13_', '6_', '17_'))
        piede = n.startswith('3_'); guscio = n.startswith(('1_', '2_'))
        nota = ('ugello in acciaio, superfici lisce, lavare prima dell\'uso (I-8)' if fine else ('ingranaggio: piano, denti nel piano XY; PETG con almeno 45 MPa nel piano (I-14)' if mecc else ''))
        if n.startswith('10_ruota'): nota += '; foro centrale stampato a 5,8 mm: ALESARLO a 6,0 H7 (alesatore a mano) prima di montare la ruota (I-2)'
        if n.startswith('9_cassetta'): nota = 'foro della torretta 6,0 mm: la spina d\'acciaio 6 x 16 entra a pressione (se balla, una goccia di colla epossidica) (I-2)'
        if n.startswith('14_'): nota += '; foro del perno 3,0 mm: spina d\'acciaio 3 x 4 a pressione (I-3)'
        if n.startswith('10_sportellini'): nota += '; cerniere con filo d\'acciaio da 0,8 mm (graffetta) (I-6)'
        if guscio: nota = 'PETG va bene in casa; se la scatoletta puo\' stare al sole o in auto, stampare guscio e cappello in ASA o PC (stampante chiusa) (I-10)'
        if piede: nota = 'solo regge la piastra d\'acciaio: 2 pareti e 15% bastano (I-11)'
        return dict(layer_mm=0.12 if fine else (0.16 if mecc else 0.2), pareti=2 if piede else (3 if not mecc else 4),
                    riempimento='15% gyroid' if piede else ('100%' if mecc else '25% gyroid'),
                    contatto_pillole=fine, filamento='PETG naturale' if fine else ('PETG, oppure ASA o PC' if guscio else 'PETG'), nota=nota)
    rows = []
    for f in sorted(os.listdir(stl_st)):
        n = f[:-4]; m = trimesh.load(os.path.join(stl_st, f), force='mesh')
        verso, area, _ = stampa(m)
        r = dict(pezzo=n, volume_cm3=float(round(m.volume / 1000, 2)), massa_g_petg=float(round(m.volume / 1000 * 1.27, 1)),
                 ingombro_mm=[float(round(v, 1)) for v in m.extents], supporti_cm2=float(round(area, 2)), **regole(n))
        r['tempo_stimato_min'] = int(m.volume / 12.0 / 60 * (1.6 if r['layer_mm'] < 0.2 else 1.3))   # stima: 12 mm3/s + fattore spostamenti
        rows.append(r)
    par = dict(versione='v1.0', modello='2m (due ruote)', stampante=dict(tipo='FDM a filo, piano almeno 250 x 210 mm', ugello_mm=0.4, ugello_materiale='acciaio inox o temprato per i pezzi a contatto con le pillole'),
               materiale=dict(nome='PETG', requisito='scheda tecnica con almeno 45 MPa di trazione nel piano XY (I-14): le schede trovate vanno da 31,9 a 68,4 MPa', densita_g_cm3=1.27, ugello_C='230-250', piano_C='70-80', ventola='30-50%', essiccazione='65 C per 6-8 h se il filo ha preso umidita\''),
               regole_generali=['nessun gioco funzionale sotto 0,3 mm nel piano e sotto 2 strati in verticale (rapporto R&D, sezione 7); unica eccezione voluta: 0,2 mm tra divisori e sportellini (I-6)',
                                'compensazione dei fori XY dal campione di prova T2', 'smusso 0,4 mm sul primo strato dei pezzi che scorrono',
                                'perni caricati: in acciaio, non stampati in verticale',
                                'pezzi a contatto con le pillole: PETG naturale (senza colore), strati da 0,12, ugello d\'acciaio (I-8)'],
               ferramenta=[dict(cosa='spina cilindrica d\'acciaio 6 x 16 mm (ISO 2338)', quanti=2, dove='assi delle ruote (I-2)'),
                           dict(cosa='alesatore a mano 6 mm H7', quanti=1, dove='foro delle ruote (I-2)'),
                           dict(cosa='spina d\'acciaio 3 x 4 mm, o chiodo da 3 mm tagliato', quanti=2, dove='perni delle croci di Malta (I-3)'),
                           dict(cosa='filo d\'acciaio da 0,8 mm (graffette)', quanti='circa 50 cm', dove='cerniere degli sportellini (I-6)'),
                           dict(cosa='modulo AHT20 (umidita\' e temperatura, I2C)', quanti=1, dove='sotto il tetto, davanti a sinistra (I-9)')],
               pezzi=rows, piatti=elenco_piatti,
               totale=dict(volume_cm3=float(round(sum(r['volume_cm3'] for r in rows), 1)), massa_g=int(round(sum(r['massa_g_petg'] for r in rows))), tempo_stimato_h=round(sum(r['tempo_stimato_min'] for r in rows) / 60, 1)))
    json.dump(par, open(os.path.join(OUT, 'parametri_stampa.json'), 'w'), indent=1, ensure_ascii=False)
    print('fatto in', round(time.time() - t0), 's;', len(shapes), 'STEP;', len(piatti), 'piatti;', par['totale'])

if __name__ == '__main__':
    main()
