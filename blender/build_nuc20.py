# ROG NUC 16 Edition 20 (20th anniversary black-gold mini PC) parametric model
# Real-world: ~198 x 117 x 280 mm upright 3L chassis. Units = meters.
import bpy, math, os, sys

OUT = sys.argv[-1] if len(sys.argv) > 1 else "assets/ROG_NUC_Edition20.glb"
W, D, H = 0.1895, 0.0565, 0.2825  # official ROG NUC 16 upright: 189.5 W x 56.5 D x 282.5 H mm

bpy.ops.wm.read_factory_settings(use_empty=True)
sc_ = bpy.context.scene

def mat(name, base, metallic=0.0, rough=0.5, emit=None, emit_str=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["Alpha"].default_value = alpha
    if trans > 0.0:
        for nm in ("Transmission Weight", "Transmission"):
            if nm in b.inputs: b.inputs[nm].default_value = trans; break
    if alpha < 1.0: m.blend_method = 'BLEND'
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m

M_BLACK   = mat("rog_black",      (0.018, 0.018, 0.020), 0.35, 0.45)
M_BLACK2  = mat("rog_black_matte",(0.010, 0.010, 0.012), 0.10, 0.70)
M_SLATL   = mat("slat_light",   (0.085, 0.087, 0.092), 0.7,  0.35)
M_GOLD    = mat("radiant_gold",   (0.820, 0.600, 0.230), 1.0,  0.22)
M_GOLD_L  = mat("gold_glow",      (0.820, 0.600, 0.230), 1.0,  0.25, emit=(1.0, 0.68, 0.25), emit_str=1.4)
M_GOLD_D  = mat("gold_dark",      (0.520, 0.380, 0.150), 1.0,  0.35)
M_SMOKE   = mat("smoke_lens",     (0.012, 0.012, 0.015), 0.25, 0.08)
M_RED     = mat("rog_red_led",    (0.55, 0.015, 0.015), 0.0, 0.3, emit=(0.8, 0.02, 0.02), emit_str=1.1)
M_EYE     = mat("rog_eye_white",  (1.0, 0.97, 0.82), 0.0, 0.2, emit=(1.0, 0.96, 0.78), emit_str=12.0)
M_HALO    = mat("eye_halo",       (1.0, 0.9, 0.66), 0.0, 0.4, emit=(1.0, 0.9, 0.66), emit_str=2.2, alpha=0.12)
M_INNER   = mat("inner_duct",     (0.020, 0.020, 0.022), 0.2, 0.6)
M_STEEL   = mat("steel",          (0.35, 0.35, 0.37), 1.0, 0.35)
M_USB     = mat("usb_slot",       (0.02, 0.02, 0.02), 0.8, 0.4)
M_USBBLUE = mat("usb_blue",       (0.05, 0.15, 0.60), 0.5, 0.4)
M_USBBLU2 = mat("usb_blue_core",  (0.02, 0.02, 0.02), 0.3, 0.5)

def box(name, dims, loc, material, bevel=0.0, alpha=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = o.data.name = name
    o.dimensions = dims
    if bevel > 0:
        v = o.modifiers.new("bev", 'BEVEL'); v.width = bevel; v.segments = 2
    o.data.materials.append(material)
    return o

def cyl(name, r, depth, loc, rot=(math.pi/2, 0, 0), material=M_BLACK, verts=32, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = o.data.name = name
    o.data.materials.append(material)
    if smooth: bpy.ops.object.shade_smooth()
    return o

def text3d(name, body, size, loc, material, extrude=0.0008, rot_top=False):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size
    cu.extrude = extrude; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu)
    sc_.collection.objects.link(ob); ob.location = loc
    if rot_top: ob.rotation_euler = (0, 0, math.pi)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    ob.data.materials.clear(); ob.data.materials.append(material)
    return ob


# ---- ROG Fearless Eye from official SVG contours ----
def add_rog_eye(tag, idxs, size, loc, material, axis='+y', extrude_ratio=0.06, mirror=False):
    import json, mathutils
    from mathutils.geometry import tessellate_polygon
    from mathutils import Vector as V
    polys = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rog_eye_polys.json")))
    # viewBox 375 -> map contours
    tris_out = []
    verts_out = []
    idx = 0
    for ci in idxs:
        poly = polys[ci]
        sgx = -1.0 if mirror else 1.0
        pts = [V((sgx*(p[0]-187.5)/375.0, -(p[1]-150.0)/375.0)) for p in poly]
        tris = tessellate_polygon([pts])
        if not tris: continue
        th = size*extrude_ratio
        base = len(verts_out)
        for pl in pts: verts_out.append((size*pl.x, size*pl.y, 0))
        for pl in pts: verts_out.append((size*pl.x, size*pl.y, th))
        n = len(pts)
        for a,b,c in tris:
            tris_out.append((base+a, base+b, base+c))
            tris_out.append((base+n+c, base+n+b, base+n+a))
        for i in range(n):
            j = (i+1) % n
            tris_out.append((base+i, base+j, base+n+j))
            tris_out.append((base+i, base+n+j, base+n+i))
    me = bpy.data.meshes.new(tag + "_me")
    me.from_pydata(verts_out, [], tris_out)
    import bmesh as _bm
    _b = _bm.new(); _b.from_mesh(me)
    _bm.ops.recalc_face_normals(_b, faces=_b.faces)
    _b.to_mesh(me); _b.free()
    me.update()
    ob = bpy.data.objects.new(tag, me)
    sc_.collection.objects.link(ob)
    ob.location = loc
    # center on origin of contour space already normalized around (0,0)
    if axis == '+y':   ob.rotation_euler = (math.pi/2, 0, 0)
    elif axis == '-y': ob.rotation_euler = (-math.pi/2, 0, 0)
    elif axis == '+x': ob.rotation_euler = (math.pi/2, 0, math.radians(90))
    elif axis == '-x': ob.rotation_euler = (math.pi/2, 0, math.radians(-90))
    ob.data.materials.append(material)
    return ob
EYE_IDXS = [8, 6, 7, 4, 9, 23, 24, 1, 5, 2, 3]

# ---------- 1. main chassis (chamfered top front edge) ----------
body = box("nuc_body", (W, D, H-0.014), (0, 0, (H-0.014)/2 + 0.012), M_BLACK, bevel=0.0045)
# big top-front chamfer like official (45deg cut across front top)
cut_top = box("cut_top", (W+0.02, 0.10, 0.10), (0, D/2+0.03, H-0.005), M_INNER)
cut_top.rotation_euler = (math.radians(-38), 0, 0)
mods = [m for m in body.modifiers if m.type == 'BEVEL']
mv = body.modifiers["bev"]; body.modifiers.remove(mv)
b = body.modifiers.new("bev", 'BEVEL'); b.width = 0.006; b.segments = 2
mm = body.modifiers.new("cham", 'BOOLEAN'); mm.object = cut_top; mm.operation = 'DIFFERENCE'
cut_top.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
new = ev.to_mesh().copy(); new.name = "nuc_body_cut"
body.modifiers.clear(); body.data = new
b2 = body.modifiers.new("bev2", 'BEVEL'); b2.width = 0.0015; b2.segments = 2

# ---------- 2. pedestal foot with intake slits ----------
foot = box("nuc_foot", (W+0.006, D+0.006, 0.012), (0, 0, 0.006), M_BLACK2, bevel=0.003)
for i in range(9):
    box(f"foot_slit{i}", (0.010, 0.003, 0.004), (-0.075 + i*0.019, D/2+0.004, 0.006), M_BLACK2)

# ---------- 2b. removable vertical stand (rear wedge, tapered) ----------
stand = box("nuc_stand", (0.030, 0.009, H-0.030), (-0.052, -D/2-0.006, 0.012 + (H-0.030)/2), M_BLACK2, bevel=0.0025)
cst = box("cut_stand", (0.06, 0.06, 0.16), (-0.052, -D/2-0.05, 0.02), M_INNER)
cst.rotation_euler = (math.radians(30), 0, 0)
cst.hide_render = True
m = stand.modifiers.new("taper", 'BOOLEAN'); m.object = cst; m.operation = 'DIFFERENCE'
dg2 = bpy.context.evaluated_depsgraph_get()
evs = stand.evaluated_get(dg2)
news = evs.to_mesh().copy(); news.name = "nuc_stand_cut"
stand.modifiers.clear(); stand.data = news
# ---------- 8b. diagonal hatch relief on narrow sides (paste-on, zero holes) ----------
for sx in (1, -1):
    yb0 = -0.020 if sx > 0 else 0.010   # -x side keeps its front strip clear for the IO column
    n = 5 if sx > 0 else 3
    for i in range(n):
        for a in (52, -52):
            sl2 = box(f"hslat_{sx}_{i}_{a}", (0.0012, 0.008, 0.028),
                      (sx * (W/2 + 0.0006), yb0 + i*0.010, 0.062), M_SLATL)
            sl2.rotation_euler = (math.radians(a), 0, 0)

# ---------- 11. top: diagonal slat relief + gold ROG lettering (paste-on, zero holes) ----------
ztp = H - 0.0140
for i in range(5):
    sl = box(f"tslat_{i}", (0.050, 0.0012, 0.03), (0.040, D/2 - 0.0006 + i*0.008, ztp), M_SLATL)
    sl.rotation_euler = (0, 0, math.radians(52))
text3d("rog_top_txt", "R O G", 0.020, (-0.082, D/2 + 0.0004, ztp - 0.006), M_GOLD, extrude=0.0002, rot_top=True)

box("stand_gold_line", (0.014, 0.0014, 0.0018), (-0.052, -D/2-0.0118, 0.150), M_GOLD)

# ---------- 3. smoked crystal-lens front panel ----------
panel = box("smoke_panel", (W-0.012, 0.0035, H-0.052), (0, D/2 - 0.0005, 0.012 + (H-0.052)/2 + 0.008), M_SMOKE, bevel=0.001)
# gold frame lines on panel edges (vertical thin lines)
box("gold_line_L", (0.0018, 0.0012, H-0.060), (-W/2+0.026, D/2+0.002, 0.012 + (H-0.052)/2 + 0.010), M_GOLD)
box("gold_line_R", (0.0018, 0.0012, H-0.060), ( W/2-0.026, D/2+0.002, 0.012 + (H-0.052)/2 + 0.010), M_GOLD)

# ---------- 4. inner duct + gold circuitry (seen through lens) ----------
duct = box("inner_duct", (W-0.045, 0.006, H-0.085), (0, D/2-0.014, 0.020 + (H-0.085)/2), M_INNER)
gz = 0.062
for i, (lz, lw) in enumerate([(0.230, 0.090), (0.212, 0.050), (0.118, 0.120), (0.096, 0.075)]):
    box(f"gold_trace{i}", (lw, 0.0012, 0.0022), (0.012 if i % 2 else -0.020, D/2+0.0016, lz), M_GOLD_L)
# >> chevron marks
for i in range(2):
    ch = box(f"chev{i}", (0.020, 0.0012, 0.0022), (0.048, D/2+0.0016, 0.084 - i*0.010), M_GOLD_L)
    ch.rotation_euler = (0, 0, math.radians(35))
box("gold_node0", (0.005, 0.0012, 0.005), (-0.062, D/2+0.0016, 0.150), M_GOLD_L)
box("gold_node1", (0.005, 0.0012, 0.005), (0.070, D/2+0.0016, 0.238), M_GOLD_L)
badge = box("gold_badge", (0.016, 0.0012, 0.016), (-0.062, D/2+0.0016, 0.224), M_GOLD_L)
# hex vent deco (dark hex + gold lattice hint)
hexb = cyl("hex_vent", 0.026, 0.0012, (-0.00, D/2+0.0014, 0.058), rot=(math.pi/2,0,0), material=M_BLACK2, verts=6, smooth=False)

# ---------- 5. glowing ROG Fearless Eye (official SVG contours) ----------
eyec_y = D/2 + 0.0020
plate = box("eye_plate", (0.105, 0.0016, 0.078), (-0.012, D/2+0.0008, 0.170), M_BLACK2, bevel=0.004)
text3d("emb_republic", "REPUBLIC OF GAMERS", 0.0042, (-0.0575, D/2+0.0026, 0.2035), M_GOLD)
add_rog_eye("eye_front_base", EYE_IDXS, 0.094, (-0.012, D/2+0.0016, 0.1665), M_GOLD, axis='+y', extrude_ratio=0.03, mirror=True)
add_rog_eye("eye_front_glow", EYE_IDXS, 0.108, (-0.015, D/2+0.0030, 0.1675), M_HALO, axis='+y', extrude_ratio=0.012, mirror=True)
add_rog_eye("eye_front", EYE_IDXS, 0.085, (-0.012, eyec_y+0.0012, 0.1690), M_EYE, axis='+y', extrude_ratio=0.06, mirror=True)

# ---------- 6. gold ROG + REPUBLIC OF GAMERS text (top-left of panel) ----------
text3d("nuc_rog", "R O G", 0.0155, (-0.050, D/2+0.003, 0.246), M_GOLD)
text3d("nuc_rog_sub", "REPUBLIC OF GAMERS", 0.0050, (-0.028, D/2+0.003, 0.229), M_GOLD)

# ---------- 7. red LED accents ----------
box("red_led_tr", (0.016, 0.0016, 0.0026), (0.058, D/2+0.0025, 0.244), M_RED)
box("red_led_bc", (0.040, 0.0016, 0.0026), (0.007, D/2+0.0025, 0.078), M_RED)


# ---------- 7b. official front-lower extras: 20 badge / red strip / motto / grille ----------
badge = box("b20_frame", (0.030, 0.0016, 0.030), (0.062, D/2+0.0012, 0.088), M_GOLD, bevel=0.002)
bp20 = box("b20_plate", (0.024, 0.0012, 0.024), (0.062, D/2+0.0022, 0.088), M_BLACK2)
text3d("b20_txt", "20", 0.0130, (0.0515, D/2+0.0040, 0.0795), M_GOLD)
box("red20_strip", (0.020, 0.0014, 0.0034), (0.020, D/2+0.0018, 0.0885), M_RED)
text3d("motto_txt", "ONCE ROG, FOREVER ROG", 0.0038, (-0.070, D/2+0.0022, 0.0585), M_GOLD_L)
for r in range(3):
    for cidx in range(9):
        box(f"fg_hole{r}_{cidx}", (0.0075, 0.0012, 0.0034), (-0.0735 + cidx*0.0185, D/2+0.0016, 0.0265 + r*0.0095), M_BLACK2)

# ---------- 8. right narrow side (56.5mm): official stack ----------
sx0 = W/2 + 0.0016
# top: gold Fearless Eye + red strip (per user ref photo)
add_rog_eye("eye_side_base", EYE_IDXS, 0.034, (W/2+0.0008, -0.001, 0.257), M_BLACK2, axis='+x', extrude_ratio=0.04, mirror=True)
side_eye = add_rog_eye("eye_side", EYE_IDXS, 0.030, (sx0, 0.0, 0.258), M_GOLD, axis='+x', extrude_ratio=0.09, mirror=True)
box("red_led_side", (0.0016, 0.020, 0.0026), (sx0, 0.0, 0.236), M_RED)
cyl("pwr_btn", 0.0058, 0.003, (sx0, 0.0, 0.220), rot=(0, math.pi/2, 0), material=M_GOLD, verts=28, smooth=False)
cyl("pwr_core", 0.0034, 0.004, (sx0+0.0005, 0.0, 0.220), rot=(0, math.pi/2, 0), material=M_RED, verts=24)
cyl("aud_jack", 0.0030, 0.0026, (sx0, 0.0, 0.204), rot=(0, math.pi/2, 0), material=M_USB, verts=20)
box("usbc", (0.0026, 0.0095, 0.0036), (sx0, 0.0, 0.190), M_USB)
for i in range(2):
    box(f"usba{i}", (0.003, 0.013, 0.0055), (sx0, 0.0, 0.172 - i*0.014), M_USBBLUE)
    box(f"usba_core{i}", (0.0034, 0.011, 0.0022), (sx0+0.0002, 0.0, 0.172 - i*0.014), M_USBBLU2)
text3d("nuc_side_20", "20", 0.0100, (sx0+0.0012, 0.0, 0.128), M_GOLD_L)
s20 = bpy.data.objects["nuc_side_20"]; s20.rotation_euler = (0, math.radians(90), math.radians(90))
text3d("nuc_side_txt", "FUTURE", 0.0060, (sx0+0.0012, 0.0, 0.098), M_GOLD)
side_txt = bpy.data.objects["nuc_side_txt"]; side_txt.rotation_euler = (0, math.radians(90), math.radians(90))


# ---------- 9. top face gold eye logo (flat) ----------
ztop = H - 0.0130
# mesh built in XY facing +z = naturally flat on the top face

# (top-face eye removed: official top has vents + openwork lettering only)

# ---------- 12. back panel: layered eye relief (dark patch + light thin slats), no float ----------
yb2 = -D/2
M_EYESHK = mat("eye_shade", (0.010, 0.010, 0.012), 0.4, 0.6)
M_SLATL  = mat("slat_light", (0.085, 0.087, 0.092), 0.7, 0.4)
# base clip solid (removed after)
eye_solid = add_rog_eye("back_eye_solid", EYE_IDXS, 0.13, (0.018, yb2 - 0.012, 0.175), M_INNER, axis='-y', extrude_ratio=0.25)
eye_solid.hide_render = True
# layer 1: dark eye patch slightly proud of wall
eye_patch = add_rog_eye("back_eye_patch", EYE_IDXS, 0.132, (0.018, yb2 - 0.0016, 0.175), M_EYESHK, axis='-y', extrude_ratio=0.012)
# layer 2: light thin slats clipped to eye, proud of patch
slat_a = math.radians(58)
snx, snz = math.sin(slat_a), math.cos(slat_a)
kept = 0
for k in range(-14, 15):
    cx, cz = 0.018 + k*0.0062*snx, 0.175 + k*0.0062*snz
    rib = box(f"eye_slat{k}", (0.15, 0.0012, 0.0032), (cx, yb2 - 0.0022, cz), M_SLATL)
    rib.rotation_euler = (0, slat_a, 0)
    mi = rib.modifiers.new("eyeclip", 'BOOLEAN'); mi.object = eye_solid; mi.operation = 'INTERSECT'; mi.solver = 'FLOAT'
    dgs = bpy.context.evaluated_depsgraph_get()
    ms = rib.evaluated_get(dgs).to_mesh().copy(); ms.name = rib.data.name + "_clip"
    rib.modifiers.clear(); rib.data = ms
    if len(rib.data.polygons) == 0:
        bpy.data.objects.remove(rib, do_unlink=True)
    else:
        kept += 1
print("eye slats kept:", kept)
# ROG openwork vent lettering on the back, below the eye
# ROG openwork vent lettering on the back, below the eye
text3d("vent_rog", "ROG", 0.022, (-0.008, yb2 + 0.001, 0.082), M_INNER, extrude=0.005)
_vent = bpy.data.objects["vent_rog"]; _vent.rotation_euler = (math.pi/2, 0, 0)
_mv = body.modifiers.new("rogvent", 'BOOLEAN'); _mv.object = _vent; _mv.operation = 'DIFFERENCE'
_vent.hide_render = True
dgv = bpy.context.evaluated_depsgraph_get()
evv = body.evaluated_get(dgv)
newv = evv.to_mesh().copy(); newv.name = "nuc_body_rogvent"
body.modifiers.clear(); body.data = newv


bpy.data.objects.remove(eye_solid, do_unlink=True)

# ---------- export ----------
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    nm = o.name
    if o.type == 'MESH' and (nm.startswith("tslat") or nm.startswith("rog_vent_txt") or nm.startswith("vent_rog") or nm.startswith("hatch_")):
        bpy.data.objects.remove(o, do_unlink=True)   # boolean cutters already applied -> not geometry
for o in list(bpy.data.objects):
    nm = o.name
    if o.type == 'MESH' and (nm.startswith("Cube") or nm.startswith("cut_")):
        print("PURGE", nm, tuple(round(v,3) for v in o.dimensions))
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True)
sz = os.path.getsize(OUT) // 1024
print("GLB:", OUT, sz, "KB")
import mathutils
mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
for o in bpy.data.objects:
    if o.type == 'MESH':
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            mn = mathutils.Vector(map(min, mn, w)); mx = mathutils.Vector(map(max, mx, w))
print("bbox(cm):", tuple(round(v*100,1) for v in (mx-mn)))


# ---------- render check shots ----------
SHOTDIR = os.environ.get("SHOT_OUT", "")
if SHOTDIR:
    center = (mn+mx)/2; diag = (mx-mn).length
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.exposure = -0.9
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.resolution_x, sc.render.resolution_y = 1200, 900
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.03, 0.04, 1)
    for i, (az, el) in enumerate([(-35, 12), (35, 15), (95, 18), (150, 55)]):
        camo = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(camo)
        r, p = math.radians(az), math.radians(el)
        d = mathutils.Vector((math.cos(p)*math.sin(r), math.cos(p)*math.cos(r), math.sin(p)))
        camo.location = center + d*diag*1.25
        fwd = (center - camo.location).normalized()
        up0 = mathutils.Vector((0, 0, 1.0))
        up = (up0 - up0.dot(fwd)*fwd).normalized()
        right = fwd.cross(up)
        camo.matrix_world = mathutils.Matrix((
            (right.x, up.x, -fwd.x, camo.location.x),
            (right.y, up.y, -fwd.y, camo.location.y),
            (right.z, up.z, -fwd.z, camo.location.z),
            (0.0, 0.0, 0.0, 1.0)))
        camo.data.lens = 60
        sc.camera = camo
        if i == 0:
            la = bpy.data.objects.new("key", bpy.data.lights.new("key",'AREA')); sc.collection.objects.link(la)
            la.data.energy, la.data.size = 80, 0.9
            la.location = center + mathutils.Vector((0.35, 0.55, 0.45))
            la.rotation_euler = (center-la.location).to_track_quat('-Z','Y').to_euler()
            lb = bpy.data.objects.new("fill", bpy.data.lights.new("fill",'AREA')); sc.collection.objects.link(lb)
            lb.data.energy, lb.data.size = 45, 1.2
            lb.location = center + mathutils.Vector((-0.55, 0.45, 0.1))
            lb.rotation_euler = (center-lb.location).to_track_quat('-Z','Y').to_euler()
            lr = bpy.data.objects.new("rim", bpy.data.lights.new("rim",'AREA')); sc.collection.objects.link(lr)
            lr.data.energy, lr.data.size = 70, 0.6
            lr.location = center + mathutils.Vector((-0.1, -0.6, 0.5))
            lr.rotation_euler = (center-lr.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath = os.path.join(SHOTDIR, f"nuc_{i}.png")
        bpy.ops.render.render(write_still=True)
print("DONE")
