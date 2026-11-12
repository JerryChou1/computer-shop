"""Clean stylized Mac Studio-class compact workstation (197^3 mm rounded box)"""
import bpy, math, mathutils, sys, os
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0] if argv else "macstudio.glb"
SHOTDIR = os.environ.get("SHOT_OUT", ".")
S = 0.197  # footprint m
SH = 0.117 # height m (real Mac Studio 197x197x117)

def mat(name, col, met=0.0, rough=0.5, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m

def box(name, dims, loc, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        bv = o.modifiers.new("bv", 'BEVEL')
        bv.width, bv.segments = bevel, 4
        bpy.ops.object.modifier_apply(modifier="bv")
        bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    return o

def cyl(name, r, d, loc, rot=(0,0,0), material=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name
    if material: o.data.materials.append(material)
    return o

M_SLV   = mat("slv_body",   (0.62, 0.63, 0.64), 0.9, 0.35)   # silver anodized
M_SLV_D = mat("slv_dark",   (0.42, 0.43, 0.45), 0.9, 0.4)
M_VENT  = mat("vent_dark",  (0.05, 0.05, 0.055), 0.3, 0.6)
M_PORT  = mat("port_dark",  (0.02, 0.02, 0.022), 0.2, 0.7)
M_GOLD  = mat("port_gold",  (0.75, 0.62, 0.30), 1.0, 0.25)
M_LED   = mat("led",        (0.1, 0.1, 0.1), 0.0, 0.4, emit=(0.2, 0.9, 1.0), emit_str=2.0)
M_SD    = mat("sd_slot",    (0.02, 0.02, 0.02), 0.3, 0.6)

H = S/2.0
body = box("body", (S, S, SH), (0, 0, SH/2), M_SLV, bevel=0.014)

# recessed ventral airflow channel: dark slab around bottom 26 mm
vh = 0.026
for tag, (sx, sy, ang) in enumerate([
    (S, 0.004, 0), (S, 0.004, 1), (S, 0.004, 2), (S, 0.004, 3)]):
    rotz = [0, math.pi/2, 0, math.pi/2][tag]
    loc  = [(0,-H+0.001,vh/2),(0,H-0.001,vh/2),(-H+0.001,0,vh/2),(H-0.001,0,vh/2)][tag]
    # honeycomb-ish: dark inset panel + horizontal slat lines
    if tag in (0,1):
        panel = box(f"vent_{tag}", (S-0.03, 0.003, vh-0.004), (0, loc[1], vh/2), M_VENT)
    else:
        panel = box(f"vent_{tag}", (0.003, S-0.03, vh-0.004), (loc[0], 0, vh/2), M_VENT)
    for k in range(3):
        z = 0.006 + k*0.008
        if tag in (0,1):
            box(f"slat_{tag}_{k}", (S-0.032, 0.0035, 0.0018), (0, loc[1], z), M_SLV_D)
        else:
            box(f"slat_{tag}_{k}", (0.0035, S-0.032, 0.0018), (loc[0], 0, z), M_SLV_D)

# --- front face (+Y): 2x USB-C + SD + status LED ---
fy = H - 0.0005
for i, x in enumerate((-0.052, -0.030)):
    box(f"usbc_f_{i}", (0.0105, 0.003, 0.0048), (x, fy, 0.046), M_PORT)
    box(f"usbc_f_{i}m", (0.0075, 0.0035, 0.0016), (x, fy, 0.046), M_SLV_D)
box("sd_f", (0.028, 0.003, 0.0032), (0.030, fy, 0.046), M_SD)
cyl("led_f", 0.0022, 0.003, (0.060, fy, 0.046), rot=(math.pi/2,0,0), material=M_LED)

# --- back face (-Y): power + IO bank cut ---
by = -H + 0.0005
box("pwrecess", (0.052, 0.003, 0.030), (0.055, by, 0.036), M_PORT)
cyl("pwrpin", 0.009, 0.004, (0.055, by, 0.040), rot=(math.pi/2,0,0), material=M_SLV_D)
for i, x in enumerate((-0.070, -0.048, -0.026)):
    box(f"eth_{i}" if i==0 else f"usbb_{i}", (0.013, 0.003, 0.012), (x, by, 0.040), M_PORT)
    box(f"metal_{i}", (0.011, 0.0035, 0.010), (x, by, 0.040), M_SLV_D)
for i, x in enumerate((-0.006, 0.016, 0.028)):
    box(f"usbcs_{i}", (0.0105, 0.003, 0.0048), (x+0.06, by, 0.075), M_PORT)
# hdmi-esque
box("hdmi", (0.0155, 0.003, 0.0065), (-0.080, by, 0.075), M_PORT)

# --- top: flat with subtle ROG-qr? keep clean, small silver disc logo ---
cyl("topdisc", 0.018, 0.0012, (0, 0, SH+0.0002), material=M_SLV_D, verts=48)

# small feet
for x in (-H+0.02, H-0.02):
    for y in (-H+0.02, H-0.02):
        cyl(f"foot_{x}_{y}", 0.008, 0.004, (x, y, -0.002), material=M_VENT, verts=24)

# ---------- export ----------
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o, do_unlink=True)
# purge any stray unnamed/primitive-leftover objects that slipped naming
for o in list(bpy.data.objects):
    if o.type == 'MESH' and (o.name == "Cube" or o.name.startswith("Cube.")):
        print("PURGE stray", o.name, tuple(round(v,3) for v in o.dimensions))
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True,
                          export_apply=True, export_yup=True)
sz = os.path.getsize(OUT)//1024
print(f"GLB: {OUT} {sz} KB")

# ---------- review render ----------
import os
print("RENDER-SECTION objects:", len([o for o in bpy.data.objects if o.type=='MESH']))
cam_data = bpy.data.cameras.new("cam"); camo = bpy.data.objects.new("cam", cam_data)
sc = bpy.context.scene; sc.collection.objects.link(camo); sc.camera = camo
cam_data.lens = 85
# matte floor at z=-0.0041 for contact shadows
bpy.ops.mesh.primitive_plane_add(size=3, location=(0,0,-0.0041))
floor = bpy.context.object; floor.name = "floor"
M_FL = bpy.data.materials.new("fl"); M_FL.use_nodes = True
M_FL.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.015,0.015,0.017,1)
M_FL.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
floor.data.materials.append(M_FL)
target = mathutils.Vector((0, 0, SH*0.55))
shots = [(0.05, 1.05, 0.10), (-1.05, 0.10, 0.09), (0.52, 0.72, 0.30)]
for i, loc in enumerate(shots):
    camo.location = target + mathutils.Vector(loc)
    d = target - camo.location
    camo.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    print(f"cam{i} loc={tuple(round(v,3) for v in camo.location)} dist={d.length:.2f}")
    if i == 0:
        la = bpy.data.objects.new("key", bpy.data.lights.new("key",'AREA')); sc.collection.objects.link(la)
        la.data.energy, la.data.size = 45, 0.8
        la.location = target + mathutils.Vector((0.30, 0.40, 0.55)); la.rotation_euler = (target-la.location).to_track_quat('-Z','Y').to_euler()
        la.data.use_shadow = True
        lb = bpy.data.objects.new("fill", bpy.data.lights.new("fill",'AREA')); sc.collection.objects.link(lb)
        lb.data.energy, lb.data.size = 25, 1.0
        lb.location = target + mathutils.Vector((-0.5, 0.3, 0.2)); lb.rotation_euler = (target-lb.location).to_track_quat('-Z','Y').to_euler()
    sc.world = bpy.data.worlds.new("w") if sc.world is None else sc.world
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.011, 0.014, 1)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError: pass
    sc.view_settings.exposure = -0.3
    sc.render.resolution_x = 1000; sc.render.resolution_y = 800
    sc.render.filepath = os.path.join(SHOTDIR, f"mac_{i}.png")
    bpy.ops.render.render(write_still=True)
print("DONE")
