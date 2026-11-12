import bpy, mathutils, os
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/Users/jjmac_studio/Desktop/AI/computer-shop-site/assets/MacStudio_Studio_v1.glb")
# world bbox
mn = [1e9]*3; mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for k,v in enumerate((w.x,w.y,w.z)):
            mn[k]=min(mn[k],v); mx[k]=max(mx[k],v)
print("WORLD bbox:", [round(v,3) for v in mn], [round(v,3) for v in mx])
c = Vector(((mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2))
sc = bpy.context.scene
camo = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(camo); sc.camera=camo
camo.data.lens=50
camo.location = c + Vector((0.30, -0.42, 0.22))
d = c - camo.location
camo.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
la = bpy.data.objects.new("key", bpy.data.lights.new("key",'AREA')); sc.collection.objects.link(la)
la.data.energy=50; la.data.size=0.8
la.location = c + Vector((0.3,0.4,0.6)); la.rotation_euler=(c-la.location).to_track_quat('-Z','Y').to_euler()
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes=True
sc.world.node_tree.nodes["Background"].inputs[0].default_value=(0.02,0.02,0.025,1)
sc.render.engine='BLENDER_EEVEE'; sc.view_settings.view_transform='AgX'; sc.view_settings.exposure=-0.4
sc.render.resolution_x=1000; sc.render.resolution_y=800
sc.render.filepath="/Users/jjmac_studio/Desktop/AI/computer-shop-site/shots/mac_glb_reimport.png"
bpy.ops.render.render(write_still=True)
print("REIMPORT-DONE")
