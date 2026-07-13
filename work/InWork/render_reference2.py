import bpy
import sys
import math
import mathutils

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
obj_path = argv[0]
out_path = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)

objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print("mesh objects:", [o.name for o in objs])
obj = objs[0]

bbox = [obj.matrix_world @ v.co for v in obj.data.vertices]
xs = [v.x for v in bbox]
ys = [v.y for v in bbox]
zs = [v.z for v in bbox]
cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
size = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), 0.05)
print("center", cx, cy, cz, "size", size)

sun = bpy.data.objects.new("Sun1", bpy.data.lights.new("Sun1", type='SUN'))
sun.data.energy = 3.0
bpy.context.scene.collection.objects.link(sun)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

dist = size * 3.5
cam_pos = mathutils.Vector((cx, cy - dist, cz + dist*0.4))
cam.location = cam_pos
target = mathutils.Vector((cx, cy, cz))
direction = target - cam_pos
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()
cam.data.clip_start = 0.001
cam.data.clip_end = 100

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("done", out_path)
