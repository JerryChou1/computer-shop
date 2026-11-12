# ROG Astral RTX 5090 — parametric rebuild v2, aligned to official refs
# Official: 357.6 x 149.3 x 76 mm, 3.8 slot, 3 front axial fans + reverse-flow tail fan on back
# Orientation: X=length, Y=thickness (y=0 backplate side, y=T front/fan side), Z=height
import bpy, math, mathutils, os, sys

OUT_GLB = sys.argv[-1] if len(sys.argv) > 1 else "5090_v2.glb"
SHOTDIR = os.environ.get("SHOT_OUT", "")

L, H, T = 0.3576, 0.1493, 0.076

bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, metallic=0.0, rough=0.5, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m

M_SHROUD  = mat("shroud_gunmetal", (0.045, 0.047, 0.052), 0.35, 0.38)
M_SILVER  = mat("chrome",           (0.72, 0.73, 0.76),   1.0,  0.12)
M_GOLDS   = mat("gold_screw",       (0.85, 0.63, 0.28),   1.0,  0.20)
M_DARKMET = mat("backplate",        (0.075, 0.077, 0.082),1.0,  0.35)
M_FINS    = mat("alu_fins",         (0.42, 0.43, 0.45),   1.0,  0.40)
M_PCB     = mat("pcb_dark",         (0.015, 0.018, 0.016),0.0,  0.55)
M_FINGER  = mat("pcie_gold",        (0.95, 0.72, 0.24),   1.0,  0.15)
M_BLACKPL = mat("black_plastic",    (0.012, 0.012, 0.013),0.0,  0.50)
M_FANBL   = mat("fan_blade",        (0.030, 0.032, 0.038),0.1,  0.32)
M_BAND    = mat("brand_band",       (0.030, 0.031, 0.034),0.2,  0.45)
M_RGB     = mat("rgb_bar",          (0.2, 0.2, 0.6),      0.0,  0.4, emit=(0.45, 0.3, 1.0), emit_str=1.4)
M_LOGO    = mat("rog_eyes",         (0.55, 0.56, 0.58),   0.9,  0.25, emit=(1.0, 1.0, 1.0), emit_str=0.35)
M_WHITE   = mat("white_print",      (0.9, 0.9, 0.9),      0.1,  0.4, emit=(0.9, 0.9, 0.9), emit_str=0.5)

def box(name, dim, loc, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name
    o.dimensions = dim
    o.data.materials.append(material)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL'); md.width = bevel; md.segments = 2
    return o

def cyl(name, r, depth, loc, rot=(0,0,0), material=None, verts=64, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    if material: o.data.materials.append(material)
    return o

TEXT_ROT = mathutils.Matrix.Rotation(math.pi, 4, mathutils.Vector((0, 1, 1)).normalized())

def text3d(name, body, size, loc, material, center=True, extrude=0.0016, rot_top=False):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'CENTER' if center else 'LEFT'
    cu.materials.append(material)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    rot = mathutils.Matrix.Rotation(math.pi, 4, 'Z') if rot_top else TEXT_ROT
    ob.matrix_world = mathutils.Matrix.Translation(mathutils.Vector(loc)) @ rot
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    me = ob.data
    me.name = name
    if len(me.materials) == 0:
        me.materials.append(material)
    print("TEXT", name, "verts:", len(me.vertices), "mats:", len(me.materials))
    return ob

def boolean(target, cutter, op='DIFFERENCE'):
    md = target.modifiers.new("bool", 'BOOLEAN')
    md.operation = op; md.object = cutter; md.solver = 'EXACT'

cut_sh, cut_bp, cut_fin = [], [], []

# ---------- dimensions ----------
FANX = [-0.112, 0.0, 0.112]      # 3 front fans
FANZ = 0.0738
FANR = 0.050                     # ~108mm ring, 3mm gap at 112mm pitch
RFX, RFZ, RFR = 0.145, FANZ, 0.034   # tail fan (back side)

# ---------- 1. backplate ----------
bp = box("backplate", (L-0.006, 0.004, H-0.014), (0, 0.002, H/2), M_DARKMET, bevel=0.0015)
rft = cyl("cut_bp_fan", RFR+0.006, 0.02, (RFX, 0.002, RFZ), rot=(math.pi/2,0,0), verts=96)
cut_bp.append(rft)

# ---------- 2. PCB + PCIe fingers ----------
pcb    = box("pcb", (L-0.014, 0.0035, H-0.030), (0, 0.008, (H-0.030)/2), M_PCB)
finger = box("pcie_fingers", (0.118, 0.007, 0.010), (0.105, 0.006, 0.005), M_FINGER)
notch  = box("finger_notch", (0.004, 0.02, 0.012), (0.072, 0.006, 0.005), M_PCB)
boolean(finger, notch)

# ---------- 3. heatsink fin stack ----------
fin = box("heatsink", (L-0.020, 0.040, H-0.026), (0, 0.032, H/2), M_FINS)
for i in range(42):
    g = box(f"fin_cut{i}", (0.0035, 0.06, H-0.020), (-0.168 + i*0.008, 0.032, H/2), M_PCB)
    cut_fin.append(g)

# ---------- 4. shroud ----------
sh = box("shroud", (L, T-0.006, H-0.002), (0, (T-0.006)/2, H/2), M_SHROUD, bevel=0.003)
for i, fx in enumerate(FANX):
    cut_sh.append(cyl(f"cut_fan{i}", FANR+0.004, 0.03, (fx, T-0.009, FANZ), rot=(math.pi/2,0,0), verts=96))
cut_sh.append(cyl("cut_end", 0.034, 0.05, (L/2+0.012, T/2, FANZ), rot=(0, math.pi/2, 0), verts=64))
cut_sh.append(box("cut_brk", (0.012, T, 0.17), (-L/2-0.004, T/2, H/2), M_PCB))
# reveal backplate: remove shroud material from rear face (perimeter frame stays)
cut_sh.append(box("cut_back", (L-0.012, 0.007, H-0.018), (0, 0.0015, H/2), M_PCB))
# tail fan recess
cut_sh.append(cyl("cut_tf", RFR+0.010, 0.030, (RFX, 0.012, RFZ), rot=(math.pi/2,0,0), verts=96, smooth=False))

# ---------- 5. front fans ----------
def fan_unit(tag, fx, fz, r, fy, nblade, hub_r, ring_thk=0.004):
    """fan facing +Y (ring sits at y=fy+blade offset); generic for front/back"""
    hub  = cyl(f"{tag}_hub", hub_r, 0.016, (fx, fy, fz), rot=(math.pi/2,0,0), material=M_BLACKPL, verts=48)
    cap  = cyl(f"{tag}_cap", hub_r*0.72, 0.003, (fx, fy+0.0088, fz), rot=(math.pi/2,0,0), material=M_BLACKPL, verts=48)
    dot  = cyl(f"{tag}_capdot", hub_r*0.30, 0.0045, (fx, fy+0.0092, fz), rot=(math.pi/2,0,0), material=M_LOGO, verts=32)
    piv = mathutils.Vector((fx, fy, fz))
    for b in range(nblade):
        ang = b * 2*math.pi/nblade
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
        bl = bpy.context.object; bl.name = f"{tag}_blade{b}"
        R_ang = mathutils.Matrix.Rotation(ang, 4, 'Y')
        T_r   = mathutils.Matrix.Translation((r*0.60, 0, 0))
        R_tw  = mathutils.Matrix.Rotation(math.radians(40), 4, 'X')
        S     = mathutils.Matrix.Diagonal((r*0.82, 0.0028, r*0.42, 1.0))
        bl.matrix_world = mathutils.Matrix.Translation(piv) @ R_ang @ T_r @ R_tw @ S
        bl.data.materials.append(M_FANBL)
    ring_out = cyl(f"{tag}_ring", r+ring_thk, 0.008, (fx, fy+0.010, fz), rot=(math.pi/2,0,0), material=M_SILVER, verts=96)
    ring_in  = cyl(f"{tag}_ring_in", r-0.002, 0.03, (fx, fy+0.010, fz), rot=(math.pi/2,0,0), verts=96, smooth=False)
    boolean(ring_out, ring_in)
    return ring_out

FRONT_Y = T - 0.020
for i, fx in enumerate(FANX):
    fan_unit(f"fan{i}", fx, FANZ, FANR, FRONT_Y, 11, 0.020)

# ---------- 5b. tail fan on BACK side (faces -Y) ----------
def tail_fan():
    hub = cyl("tf_hub", 0.013, 0.012, (RFX, 0.014, RFZ), rot=(math.pi/2,0,0), material=M_BLACKPL, verts=48)
    cap = cyl("tf_cap", 0.007, 0.003, (RFX, 0.0072, RFZ), rot=(math.pi/2,0,0), material=M_LOGO, verts=48)
    piv = mathutils.Vector((RFX, 0.013, RFZ))
    for b in range(9):
        ang = b * 2*math.pi/9
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0009, depth=1, vertices=8)  # placeholder removed below
        bpy.ops.object.delete()
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
        bl = bpy.context.object; bl.name = f"tf_blade{b}"
        R_ang = mathutils.Matrix.Rotation(ang, 4, 'Y')
        T_r   = mathutils.Matrix.Translation((RFR*0.55, 0, 0))
        R_tw  = mathutils.Matrix.Rotation(math.radians(45), 4, 'X')
        S     = mathutils.Matrix.Diagonal((RFR*0.72, 0.0016, RFR*0.40, 1.0))
        bl.matrix_world = mathutils.Matrix.Translation(piv) @ R_ang @ T_r @ R_tw @ S
        bl.data.materials.append(M_FANBL)
    ring = cyl("tf_ring", RFR+0.005, 0.006, (RFX, 0.001, RFZ), rot=(math.pi/2,0,0), material=M_SILVER, verts=80)
    rin  = cyl("tf_ring_in", RFR-0.002, 0.03, (RFX, 0.001, RFZ), rot=(math.pi/2,0,0), verts=80, smooth=False)
    boolean(ring, rin)
tail_fan()

# ---------- 6. front brand band + RGB bar (below PCB top edge) ----------
band   = box("brand_band", (L-0.014, 0.003, 0.018), (0, T-0.0055, H-0.008), M_BAND, bevel=0.001)
rtx    = text3d("print_rtx", "GEFORCE RTX\u2122", 0.0072, (-0.095, T-0.0038, H-0.0118), M_WHITE)
rogp   = box("rog_plate",  (0.086, 0.0025, 0.011), (0.098, T-0.0048, H-0.0085), M_SILVER)
rogtx  = text3d("rog_plate_tx", "REPUBLIC OF GAMERS", 0.0042, (0.098, T-0.0032, H-0.0085), M_BLACKPL, extrude=0.0006)
astral = text3d("print_astral", "ASTRAL", 0.009, (-0.095, 0.040, H-0.0020), M_SILVER, extrude=0.0012, rot_top=True)
rgbbar = box("rgb_bar",    (L-0.020, 0.004, 0.005), (0, T-0.0075, H-0.0015), M_RGB)

# gold accent screws on shroud front (cosmetic, official has mixed gold/silver)
for k, (sx, sz) in enumerate([(-0.168, 0.014), (0.168, 0.014), (-0.168, H-0.0135), (0.168, H-0.0135)]):
    sc = cyl(f"screw{k}", 0.0025, 0.0018, (sx, T-0.0026, sz), rot=(math.pi/2,0,0),
             material=(M_GOLDS if k % 3 == 0 else M_SILVER), verts=24, smooth=False)

# tail-end window inner light bar (visible through exhaust opening)
endbar = box("end_bar", (0.004, 0.048, 0.007), (L/2-0.016, T/2, FANZ), M_RGB)

# ---------- 7. power connectors on top edge, toward rear ----------
pw = box("pwr_main", (0.030, 0.017, 0.009), (0.118, 0.026, H-0.0015), M_SILVER, bevel=0.0015)
pwc = box("pwr_cav", (0.025, 0.012, 0.008), (0.118, 0.026, H+0.0015), M_BLACKPL)
hdr = box("aux_header", (0.008, 0.006, 0.007), (0.147, 0.026, H-0.002), M_BLACKPL)

# ---------- 8. dual-BIOS switch + I/O bracket ----------
bios = box("bios_sw", (0.012, 0.005, 0.007), (-0.163, T-0.006, H-0.030), M_BLACKPL)
bios_f = box("bios_frame", (0.015, 0.003, 0.009), (-0.163, T-0.0048, H-0.030), M_GOLDS)
brk = box("io_bracket", (0.0035, T-0.014, H+0.004), (-L/2+0.001, T/2-0.006, H/2), M_SILVER, bevel=0.0008)
pz = 0.030
for i in range(4):
    box(f"dp{i}", (0.008, 0.018, 0.0115), (-L/2-0.001, T/2-0.006, pz + i*0.022), M_BLACKPL)
box("hdmi", (0.008, 0.016, 0.010), (-L/2-0.001, T/2-0.006, pz + 4*0.022), M_BLACKPL)
for i in range(5):
    box(f"vent{i}", (0.006, 0.022, 0.006), (-L/2-0.001, T/2-0.006, 0.116 + i*0.0085), M_PCB)

# ---------- backplate subtle logo ----------
bplogo = box("bp_logo", (0.040, 0.0015, 0.012), (0.02, -0.0015, H/2), M_SILVER)

# ---------- 9. Astral diagonal cut lines (tactical facets) ----------
import mathutils as _mu
def groove(name, length, angle, loc, depth=0.0030, thick=0.0024):
    g = box(name, (length, depth, thick), loc, M_PCB)
    g.rotation_euler = (0, math.radians(angle), 0)
    return g
FR = 0.0690   # cutter center: straddles shroud front face (y=0.070)
G = [
    groove("gr1", 0.150, -28, (-0.148, FR, 0.1215)),
    groove("gr2", 0.100,  36, ( 0.150, FR, 0.1260)),
    groove("gr3", 0.062, -45, (-0.166, FR, 0.0300)),
    groove("gr4", 0.062,  45, (-0.058, FR, 0.0080)),
    groove("gr5", 0.062,  45, ( 0.058, FR, 0.0080)),
    groove("gr6", 0.100, -30, ( 0.132, FR, 0.0215)),
    groove("gr7", 0.080,  30, (-0.152, FR, 0.0738+0.0625+0.0025)),
    groove("gr8", 0.240,  -8, ( 0.010, FR, 0.0106)),
]
for g in G:
    cut_sh.append(g)

# bottom-edge exposure slot: reveals PCB edge + PCIe gold fingers (official shows PCB here)
cut_bot = box("cut_bot", (0.316, 0.090, 0.019), (0.015, 0.035, 0.0085), M_PCB)
cut_sh.append(cut_bot)

# ---------- apply booleans ----------
for c in cut_sh:  boolean(sh, c)
for c in cut_bp:  boolean(bp, c)
for c in cut_fin: boolean(fin, c)
dg = bpy.context.evaluated_depsgraph_get()
for ob in list(bpy.data.objects):
    if ob.type != 'MESH' or not any(md.type == 'BOOLEAN' for md in ob.modifiers):
        continue
    before = len(ob.data.vertices)
    ev = ob.evaluated_get(dg)
    new = ev.to_mesh().copy()
    new.name = ob.name + "_cut"
    ev.to_mesh_clear()
    while ob.modifiers: ob.modifiers.remove(ob.modifiers[0])
    if len(new.materials) == 0 and ob.data.materials:
        new.materials.append(ob.data.materials[0])
    ob.data = new
    ob.data.update()
    dg.update()
    print("BOOL", ob.name, "before:", before, "-> after:", len(new.vertices), "mats:", len(new.materials))

# ---------- hide cutters ----------
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.name.startswith(("cut_", "fin_cut", "gr1", "gr2", "gr3", "gr4", "gr5", "gr6", "gr7", "gr8")) or o.name.endswith("_ring_in") or o.name == "finger_notch"):
        o.hide_render = True
        o.hide_set(True)

bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_visible=True,
                          export_yup=True, export_apply=True)
print("GLB:", OUT_GLB, f"{os.path.getsize(OUT_GLB)/1024:.0f} KB")

# ---------- renders ----------
if SHOTDIR:
    mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.hide_render:
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                mn2 = mathutils.Vector(map(min, mn, w)); mx2 = mathutils.Vector(map(max, mx, w))
                mn, mx = mn2, mx2
    center = (mn+mx)/2; diag = (mx-mn).length
    print("bbox(cm):", tuple(round(v*100,1) for v in (mx-mn)))
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.exposure = -1.3
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.04, 0.045, 0.055, 1)
    for i, (az, el) in enumerate([(-40, 38), (140, 52), (-25, 8), (55, -22)]):
        camo = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(camo)
        r, p = math.radians(az), math.radians(el)
        # our model's "front" is +Y; azimuth measured from +Y axis toward +X
        d = mathutils.Vector((math.cos(p)*math.sin(r), math.cos(p)*math.cos(r), math.sin(p)))
        camo.location = center + d*diag*1.15
        fwd = (center - camo.location).normalized()
        up0 = mathutils.Vector((0, 0, 1.0))
        up = (up0 - up0.dot(fwd)*fwd).normalized()
        right = fwd.cross(up)
        camo.matrix_world = mathutils.Matrix((
            (right.x, up.x, -fwd.x, camo.location.x),
            (right.y, up.y, -fwd.y, camo.location.y),
            (right.z, up.z, -fwd.z, camo.location.z),
            (0.0, 0.0, 0.0, 1.0)))
        camo.data.lens = 50
        sc.camera = camo
        if i == 0:
            la = bpy.data.objects.new("key", bpy.data.lights.new("key",'AREA')); sc.collection.objects.link(la)
            la.data.energy, la.data.size = 55, 0.9
            la.location = center + mathutils.Vector((0.3, 0.55, 0.5))
            la.rotation_euler = (center-la.location).to_track_quat('-Z','Y').to_euler()
            lb = bpy.data.objects.new("fill", bpy.data.lights.new("fill",'AREA')); sc.collection.objects.link(lb)
            lb.data.energy, lb.data.size = 35, 1.2
            lb.location = center + mathutils.Vector((-0.55, 0.35, 0.15))
            lb.rotation_euler = (center-lb.location).to_track_quat('-Z','Y').to_euler()
            lr = bpy.data.objects.new("rim", bpy.data.lights.new("rim",'AREA')); sc.collection.objects.link(lr)
            lr.data.energy, lr.data.size = 60, 0.6
            lr.location = center + mathutils.Vector((0.1, -0.5, 0.55))
            lr.rotation_euler = (center-lr.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath = os.path.join(SHOTDIR, f"v2_{i}.png")
        bpy.ops.render.render(write_still=True)
print("DONE")
