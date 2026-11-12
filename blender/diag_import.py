import bpy, sys, os, mathutils
argv = sys.argv[sys.argv.index("--")+1:]
glb = argv[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.data.objects if o.type=='MESH']
print("IMPORTED MESHES:", len(meshes))
cs = [o.matrix_world @ __import__('mathutils').Vector(c) for m in meshes for c in m.bound_box]
for o in meshes[:50]:
    matname = o.material_slots[0].material.name if o.material_slots else None
    print(f"  {o.name[:40]:42s} {o.dimensions.x:.4f}x{o.dimensions.y:.4f}x{o.dimensions.z:.4f} mat={matname}")
bpy.ops.object.select_all(action='DESELECT')
