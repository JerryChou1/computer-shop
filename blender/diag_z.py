import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
import mathutils
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    nm = o.name.split(".")[-1] if "." in o.name else o.name
    if any(k in nm for k in ("pcie","finger","pcb","fan","shroud","astral","rtx")):
        bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        z = [v.z for v in bb]; y=[v.y for v in bb]; x=[v.x for v in bb]
        print(f"{nm[:28]:28s} z[{min(z):+.3f},{max(z):+.3f}] y[{min(y):+.3f},{max(y):+.3f}] x[{min(x):+.3f},{max(x):+.3f}]")
