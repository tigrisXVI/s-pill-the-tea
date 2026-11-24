"""Immagini della v0.5 con Blender: python3 rendi_v5.py (dopo spill_v5.py)."""
import bpy, bmesh, os, math, glob, mathutils
from mathutils import Vector, Matrix
qui = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(qui, "..", "stl", "assieme"); comp = os.path.join(qui, "..", "stl", "componenti"); out = os.path.join(qui, "..", "docs", "immagini")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 860
COL = {"10_guscio": (0.90, 0.90, 0.88), "11_cofanetto": (0.13, 0.40, 0.35), "12_bicchierino": (0.96, 0.96, 0.95),
       "1_base": (0.75, 0.76, 0.78), "2_fondo": (0.25, 0.55, 0.75), "3_piastra": (0.95, 0.6, 0.15), "3b_tappini": (0.95, 0.6, 0.15),
       "4_mozzo": (0.55, 0.57, 0.6), "5_paletta": (0.9, 0.9, 0.88), "6_scivolo": (0.6, 0.78, 0.9), "7_coperchio": (0.22, 0.27, 0.35),
       "8_sportello": (0.25, 0.7, 0.55), "9_leva": (0.95, 0.75, 0.2), "servo": (0.1, 0.25, 0.7), "display": (0.02, 0.02, 0.03),
       "tasto": (0.85, 0.16, 0.12), "luci": (0.95, 0.95, 0.6)}
ALZA = {"10_guscio": 0, "12_bicchierino": 0, "1_base": 0, "6_scivolo": 0, "display": 0, "tasto": 0, "luci": 0, "2_fondo": 120, "3_piastra": 150,
        "3b_tappini": 160, "5_paletta": 180, "4_mozzo": 195, "7_coperchio": 230, "8_sportello": 250, "9_leva": 240, "servo": 240, "11_cofanetto": 300}
ogg = {}
for f in sorted(glob.glob(os.path.join(src, "*.stl"))) + sorted(glob.glob(os.path.join(comp, "*.stl"))):
    bpy.ops.wm.stl_import(filepath=f)
    o = bpy.context.selected_objects[0]; o.scale = (0.001,) * 3; n = os.path.basename(f)[:-4]; o.name = n
    k = max((k for k in COL if n.startswith(k)), key=len)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(o.data); bm.free()
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(32))
    except Exception:
        try: bpy.ops.object.shade_auto_smooth(angle=math.radians(32))
        except Exception: pass
    m = bpy.data.materials.get(k) or bpy.data.materials.new(k)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*COL[k], 1)
    b.inputs["Roughness"].default_value = 0.15 if k == "display" else 0.4
    o.data.materials.append(m); ogg[n] = (o, k)
bpy.ops.mesh.primitive_plane_add(size=40); pm = bpy.data.materials.new("piano"); pm.use_nodes = True
pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.82, 0.82, 0.84, 1); bpy.context.object.data.materials.append(pm)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.4
for loc, e in (((0.4, -0.35, 0.6), 5.0), ((-0.3, 0.3, 0.5), 1.6), ((0.5, 0.4, 0.2), 1.2)):
    bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object; L.data.energy = e; L.data.size = 0.5
    L.rotation_euler = (Vector((0.03, 0, 0.04)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 55
def guarda(pos, verso):
    cam.location = pos; cam.rotation_euler = (Vector(verso) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
def scatta(nome):
    sc.render.filepath = os.path.join(out, nome); bpy.ops.render.render(write_still=True)
def gira(k, perno, gradi):
    for o, kk in ogg.values():
        if kk == k:
            R = Matrix.Rotation(math.radians(-gradi), 4, "Y"); o.rotation_euler = R.to_euler(); o.location = perno - (R.to_3x3() @ perno)
H = Vector((0.0305, 0, 0.059048)); S = Vector((0.0305, 0, 0.063048)); C = Vector((-0.0902, 0, 0.0996))
def sportello(gradi):
    t = math.radians(gradi); gira("8_sportello", H, gradi)
    gira("9_leva", S, gradi + math.degrees(math.asin(min(1, 4.0 * (1 - math.cos(t)) / 14.0))))
def nascondi(*ks):
    for o, k in ogg.values(): o.hide_render = k in ks
# 1) chiusa, da davanti
nascondi("luci")
guarda((0.46, -0.30, 0.30), (0.035, 0, 0.045)); scatta("v5_chiusa.png")
# 2) cofanetto aperto per ricaricare (coperchio interno tolto)
gira("11_cofanetto", C, 100); nascondi("luci", "7_coperchio", "8_sportello", "9_leva", "servo")
guarda((0.40, -0.26, 0.42), (0.01, 0, 0.04)); scatta("v5_ricarica.png")
# 3) dentro: senza guscio e cofanetto, sportello alzato dal servo
gira("11_cofanetto", C, 0); sportello(35); nascondi("luci", "10_guscio", "11_cofanetto")
guarda((0.40, -0.32, 0.30), (0.04, 0, 0.04)); scatta("v5_dentro.png"); sportello(0)
# 4) esploso
nascondi("luci")
for o, k in ogg.values(): o.location.z = ALZA[k] / 1000
guarda((0.75, -0.55, 0.55), (0.02, 0, 0.16)); cam.data.lens = 45; scatta("v5_esploso.png")
