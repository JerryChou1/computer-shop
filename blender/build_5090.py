# ROG Astral RTX 5090 — parametric hard-surface rebuild v1
# Orientation: X=length 358mm, Y=thickness 72mm (0=backplate, +Y fans up), Z=height 148mm
import bpy, math, mathutils, os, sys

OUT_GLB = sys.argv[-1] if len(sys.argv) > 1 else "5090_v1.glb"
SHOTDIR = os.environ.get("SHOT_OUT", "")  # if set, render 3 angles after build

L, H, T = 0.358, 0.148, 0.072     # card envelope
Z0, Z1 = 0.0, H                  # vertical
CX = 0.0

bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.collection

# ---------- material helpers ----------
def mat(name, color, metallic=0.0, rough=0.5, emit=None, emit_str=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m

M_SHROUD  = mat("shroud_black",  (0.028, 0.029, 0.033), 0.25, 0.42)
M_SILVER  = mat("silver",        (0.62, 0.63, 0.66),    1.0,  0.28)
M_GOLD    = mat("gold_accent",   (0.83, 0.62, 0.25),    1.0,  0.22)
M_DARKMET = mat("dark_metal",    (0.10, 0.10, 0.11),    1.0,  0.45)
M_FINS    = mat("alu_fins",      (0.52, 0.53, 0.55),    1.0,  0.40)
M_PCB     = mat("pcb_dark",      (0.018, 0.022, 0.020), 0.0,  0.55)
M_FINGER  = mat("pcie_gold",     (0.85, 0.60, 0.22),    1.0,  0.25)
M_BLACKPL = mat("black_plastic", (0.012, 0.012, 0.013), 0.0,  0.50)
M_FANBL   = mat("fan_blade",     (0.040, 0.042, 0.048), 0.1,  0.35)
M_LOGO    = mat("rog_logo",      (0.9, 0.9, 0.9),       0.0,  0.3, emit=(0.85, 0.9, 1.0), emit_str=4.0)
M_RING    = mat("fan_ring",      (0.7, 0.71, 0.74),     1.0,  0.25)

def box(name, dim, loc, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name
    o.dimensions = dim                      # world-size, per lesson learned
    o.data.materials.append(material)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL')
        md.width = bevel; md.segments = 2
    return o

def cyl(name, r, depth, loc, rot=(0,0,0), material=None, verts=64, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    for p in o.data.polygons: p.use_smooth = True
    if material: o.data.materials.append(material)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL'); md.width = bevel; md.segments = 2
    return o

def boolean(target, cutter, op='DIFFERENCE'):
    md = target.modifiers.new("bool", 'BOOLEAN')
    md.operation = op; md.object = cutter; md.solver = 'EXACT'

cutters = []
# ---------- 1. backplate ----------
bp = box("backplate", (L-0.008, 0.004, 0.134), (CX, 0.002, 0.075), M_DARKMET, bevel=0.002)
inset = box("bp_inset", (0.16, 0.002, 0.11), (0.06, -0.0005, 0.075), M_SHROUD)
boolean(bp, inset, 'UNION')      # subtle raised panel
logo_bp = box("bp_logo", (0.05, 0.003, 0.018), (-0.10, -0.002, 0.075), M_LOGO)

# ---------- 2. PCB + PCIe fingers ----------
pcb  = box("pcb", (L-0.012, 0.0035, 0.116), (CX, 0.008, 0.064), M_PCB)
finger = box("pcie_fingers", (0.118, 0.0045, 0.009), (-0.110, 0.008, 0.0045), M_FINGER)
notch_c = box("finger_notch", (0.003, 0.02, 0.004), (-0.056, 0.008, 0.004), M_PCB)
boolean(finger, notch_c)

# ---------- 3. heatsink fin stack ----------
fin = box("heatsink", (L-0.020, 0.034, 0.126), (CX, 0.029, 0.078), M_FINS)
for i in range(26):                   # fin grooves visible through openings
    g = box(f"fin_cut{i}", (L-0.018, 0.004, 0.128), (CX, 0.016 + i*0.0018*1.55, 0.078), M_PCB)
    cutters.append(g)

# ---------- 4. shroud ----------
sh = box("shroud", (L, T, H-0.004), (CX, T/2, H/2), M_SHROUD, bevel=0.004)
FANX = [-0.120, -0.040, 0.040, 0.120]
FANZ, FANR = 0.074, 0.052
for i, fx in enumerate(FANX):          # 4 fan openings through the top (must breach y=T=0.072)
    c = cyl(f"cut_fan{i}", FANR, 0.028, (fx, T-0.010, FANZ), rot=(math.pi/2, 0, 0), verts=96)
    cutters.append(c)
# end-window (shows fins + RGB bar) cut along X at far end
cend = cyl("cut_end", 0.030, 0.05, (L/2+0.01, T*0.5, 0.074), rot=(0, math.pi/2, 0), verts=64)
cutters.append(cend)
# bracket pocket at I/O end
poc = box("cut_brk", (0.010, T, 0.16), (-L/2-0.002, T/2, H/2), M_PCB)
cutters.append(poc)

# ---------- 5. fans ----------
for fi, fx in enumerate(FANX):
    fy = T - 0.018
    hub = cyl(f"hub{fi}", 0.0165, 0.018, (fx, fy, FANZ), rot=(math.pi/2,0,0), material=M_BLACKPL, verts=48)
    cap = cyl(f"hubcap{fi}", 0.009, 0.003, (fx, fy+0.0105, FANZ), rot=(math.pi/2,0,0), material=M_BLACKPL, verts=48)
    nblade = 11
    for b in range(nblade):
        ang = b * 2*math.pi/nblade + fi*0.31
        r = 0.0305
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        bl = bpy.context.object; bl.name = f"blade{fi}_{b}"
        piv = mathutils.Vector((fx, fy, FANZ))
        R_ang = mathutils.Matrix.Rotation(ang, 4, 'Y')
        T_r   = mathutils.Matrix.Translation((r, 0, 0))
        R_tw  = mathutils.Matrix.Rotation(math.radians(38), 4, 'X')
        S     = mathutils.Matrix.Diagonal((0.046, 0.0016, 0.021, 1.0))
        bl.matrix_world = mathutils.Matrix.Translation(piv) @ R_ang @ T_r @ R_tw @ S
        bl.data.materials.append(M_FANBL)
    ring = cyl(f"fring{fi}", FANR+0.002, 0.005, (fx, T-0.004, FANZ), rot=(math.pi/2,0,0), material=M_RING, verts=96)
    cinner = cyl(f"fring_in{fi}", FANR-0.004, 0.02, (fx, T-0.004, FANZ), rot=(math.pi/2,0,0), verts=96)
    boolean(ring, cinner)

# ---------- 6. accents ----------
# mirror strip on top-far edge
strip = box("top_strip", (0.13, 0.008, 0.016), (0.10, T-0.002, H-0.008), M_SILVER, bevel=0.002)
# gold front (I/O-side) corner accent
gold = box("gold_edge", (0.012, T-0.010, 0.130), (-L/2+0.014, T/2+0.004, H/2+0.004), M_GOLD, bevel=0.002)
# side ROG logo, emissive, near far end
logo_side = box("logo_side", (0.055, 0.002, 0.020), (0.150, T+0.0005, 0.105), M_LOGO)
# far-end white light bar visible through end window
bar = box("end_bar", (0.006, 0.052, 0.008), (L/2-0.020, T*0.5, 0.074), M_LOGO)

# ---------- 7. power connector (12V-2x6), top far-end ----------
pwr = box("pwr_12v2x6", (0.030, 0.016, 0.013), (L/2-0.052, T-0.004, H-0.020), M_BLACKPL, bevel=0.001)
pwr_pins = box("pwr_pins", (0.026, 0.010, 0.004), (L/2-0.052, T+0.0015, H-0.020), M_SILVER)

# ---------- 8. I/O bracket ----------
brk = box("io_bracket", (0.0035, T-0.012, H-0.002), (-L/2+0.001, T/2-0.004, H/2), M_SILVER, bevel=0.0008)
pz = 0.028
for i in range(4):                    # 4x DisplayPort
    p = box(f"dp{i}", (0.008, 0.018, 0.0115), (-L/2-0.001, T/2-0.004, pz + i*0.021), M_BLACKPL)
hd = box("hdmi", (0.008, 0.016, 0.010), (-L/2-0.001, T/2-0.004, pz + 4*0.021), M_BLACKPL)
for i in range(4):                    # vent slots on bracket
    v = box(f"vent{i}", (0.006, 0.020, 0.006), (-L/2-0.001, T/2-0.004, 0.118 + i*0.009), M_PCB)

# ---------- apply booleans ----------
for c in cutters:
    boolean(sh if c.name.startswith(("cut_fan", "cut_end", "cut_brk")) else fin, c)
dg = bpy.context.evaluated_depsgraph_get()
for ob in list(bpy.data.objects):
    if ob.type != 'MESH' or not any(md.type == 'BOOLEAN' for md in ob.modifiers):
        continue
    before = len(ob.data.vertices)
    ev = ob.evaluated_get(dg)
    tm = ev.to_mesh()
    new = tm.copy()
    new.name = ob.name + "_cut"
    ev.to_mesh_clear()
    while ob.modifiers:
        ob.modifiers.remove(ob.modifiers[0])
    if len(new.materials) == 0 and ob.data.materials:
        new.materials.append(ob.data.materials[0])
    old = ob.data
    ob.data = new
    ob.data.update()
    dg.update()
    print("BOOL", ob.name, "before:", before, "-> after:", len(new.vertices), "mats:", len(new.materials))

# sanity count
nm = sum(1 for o in bpy.data.objects if o.type=='MESH')
print("meshes:", nm)

# ---------- export GLB ----------
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("cut_", "fin_cut", "fring_in")):
        o.hide_render = True
        o.hide_set(True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_visible=True,
                          export_yup=True, export_apply=True)
sz = os.path.getsize(OUT_GLB)
print("GLB:", OUT_GLB, f"{sz/1024:.0f} KB")

# ---------- verification renders ----------
if SHOTDIR:
    import mathutils
    mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.hide_render:
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                mn2 = mathutils.Vector(map(min, mn, w)); mx2 = mathutils.Vector(map(max, mx, w))
                mn, mx = mn2, mx2
    center = (mn+mx)/2; diag = (mx-mn).length
    print("bbox(size cm):", tuple(round(v*100,1) for v in (mx-mn)))
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.10, 0.11, 0.13, 1)
    for i, (az, el) in enumerate([(-35, 62), (160, -55), (-55, -12)]):
        camo = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(camo)
        r, p = math.radians(az), math.radians(el)
        d = mathutils.Vector((math.cos(p)*math.cos(r), math.sin(p), math.cos(p)*math.sin(r)))
        camo.location = center + d*diag*1.25
        fwd = (center - camo.location).normalized()
        up0 = mathutils.Vector((0, 0, 1.0))
        up = (up0 - up0.dot(fwd)*fwd).normalized()
        right = fwd.cross(up)
        b = -fwd
        camo.matrix_world = mathutils.Matrix((
            (right.x, up.x, b.x, camo.location.x),
            (right.y, up.y, b.y, camo.location.y),
            (right.z, up.z, b.z, camo.location.z),
            (0.0, 0.0, 0.0, 1.0)))
        camo.data.lens = 50
        sc.camera = camo
        if i == 0:
            la = bpy.data.objects.new("key", bpy.data.lights.new("key",'AREA')); sc.collection.objects.link(la)
            la.data.energy, la.data.size = 500, 0.9
            la.location = center + mathutils.Vector((0.35, 0.5, 0.55))
            la.rotation_euler = (center-la.location).to_track_quat('-Z','Y').to_euler()
            lb = bpy.data.objects.new("fill", bpy.data.lights.new("fill",'AREA')); sc.collection.objects.link(lb)
            lb.data.energy, lb.data.size = 220, 1.2
            lb.location = center + mathutils.Vector((-0.5, -0.25, 0.3))
            lb.rotation_euler = (center-lb.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath = os.path.join(SHOTDIR, f"v1_{i}.png")
        bpy.ops.render.render(write_still=True)
        print("shot", sc.render.filepath)
print("DONE")
