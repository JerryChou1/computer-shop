import bpy, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
print("== emissive meshes near fan0 ==")
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(c.x for c in cs)/8; cy = sum(c.y for c in cs)/8; cz = sum(c.z for c in cs)/8
    for slot in o.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'PRINCIPLED' and n.inputs['Emission Strength'].default_value > 0.2:
                print(f"OBJ {o.name:40s} c=({cx:.3f},{cy:.3f},{cz:.3f}) mat={m.name} str={n.inputs['Emission Strength'].default_value}")
                break
