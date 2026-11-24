import bpy, os, sys, math, glob
from mathutils import Vector
qui = os.path.dirname(os.path.abspath(__file__)); src = os.path.join(qui, "..", "stl_assieme"); out = os.path.join(qui, "..")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 40; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 860
COL = {"1_base": (0.75, 0.76, 0.78), "2_fondo": (0.25, 0.55, 0.75), "3_piastra": (0.95, 0.6, 0.15), "3b_tappini": (0.95, 0.6, 0.15), "4_mozzo": (0.55, 0.57, 0.6), "5_paletta": (0.9, 0.9, 0.88), "6_scivolo": (0.6, 0.78, 0.92), "7_coperchio": (0.15, 0.2, 0.3), "8_sportello": (0.2, 0.65, 0.5)}
ALZA = {"1_base": 0, "6_scivolo": 0, "2_fondo": 45, "3_piastra": 75, "3b_tappini": 85, "5_paletta": 105, "4_mozzo": 120, "7_coperchio": 150, "8_sportello": 175}
ogg = {}
for f in sorted(glob.glob(os.path.join(src, "*.stl"))):
    bpy.ops.wm.stl_import(filepath=f)
    o = bpy.context.selected_objects[0]; o.scale = (0.001,) * 3; n = os.path.basename(f)[:-4]; o.name = n
    k = next(k for k in COL if n.startswith(k))
    m = bpy.data.materials.get(k) or bpy.data.materials.new(k)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*COL[k], 1); b.inputs["Roughness"].default_value = 0.45
    o.data.materials.append(m); ogg[n] = (o, k)
    for p in o.data.polygons: p.use_smooth = False
bpy.ops.mesh.primitive_plane_add(size=40); pm = bpy.data.materials.new("piano"); pm.use_nodes = True
pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.82, 1); bpy.context.object.data.materials.append(pm)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
for loc, e in (((0.3, -0.3, 0.5), 3.5), ((-0.3, 0.2, 0.4), 1.2)):
    bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object; L.data.energy = e; L.data.size = 0.4
    L.rotation_euler = (Vector((0, 0, 0.03)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 60
def guarda(pos, verso):
    cam.location = pos; cam.rotation_euler = (Vector(verso) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
def scatta(nome):
    sc.render.filepath = os.path.join(out, nome); bpy.ops.render.render(write_still=True)
import mathutils
H = mathutils.Vector((30.500 / 1000, 0, 59.048 / 1000))
def apri(gradi):
    o = next(o for o, k in ogg.values() if k == "8_sportello")
    R = mathutils.Matrix.Rotation(math.radians(-gradi), 4, "Y")
    o.rotation_euler = R.to_euler(); o.location = H - (R.to_3x3() @ H)
# 1) chiusa
guarda((0.34, -0.30, 0.24), (0.03, 0, 0.025)); scatta("v3_chiusa.png")
# 2) sportello aperto
apri(100); guarda((0.36, -0.20, 0.26), (0.06, 0, 0.03)); scatta("v3_aperta.png"); apri(0)
# 3) interno: senza coperchio e sportello
for n, (o, k) in ogg.items(): o.hide_render = k in ("7_coperchio", "8_sportello")
guarda((0.30, -0.20, 0.30), (0.03, 0, 0.03)); scatta("v3_interno.png")
# 4) esploso
for n, (o, k) in ogg.items(): o.hide_render = False; o.location.z = ALZA[k] / 1000
guarda((0.62, -0.48, 0.42), (0.02, 0, 0.11)); cam.data.lens = 50; scatta("v3_esploso.png")
for n, (o, k) in ogg.items(): o.location.z = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "spill_v3.blend"))
