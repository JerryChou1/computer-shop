import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/Users/jjmac_studio/Desktop/AI/computer-shop-site/assets/MacStudio_Studio_v1.glb")
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    sz = [round(max(c[k] for c in cs)-min(c[k] for c in cs),3) for k in range(3)]
    if max(sz) > 0.5:
        print("BIG", o.name, sz)
print("total meshes:", sum(1 for o in bpy.data.objects if o.type=='MESH'))
