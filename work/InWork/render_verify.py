import bpy
import mathutils
import math
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
obj_path = argv[0]
tex_path = argv[1]
out_path = argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)
obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]

mat = bpy.data.materials.new("M")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(tex_path)
mat.node_tree.links.new(bsdf.inputs["Base Color"], tex.outputs["Color"])
obj.data.materials.append(mat)

bbox = [obj.matrix_world @ v.co for v in obj.data.vertices]
xs = [v.x for v in bbox]; ys = [v.y for v in bbox]; zs = [v.z for v in bbox]
cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
size = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

sun = bpy.data.objects.new("Sun1", bpy.data.lights.new("Sun1", type='SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(55), 0, math.radians(35))
bpy.context.scene.collection.objects.link(sun)

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.58, 1)
bpy.context.scene.world = world

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
dist = size * 1.6
cam_pos = mathutils.Vector((cx, cy, cz)) + mathutils.Vector((dist*0.6, dist*1.0, dist*0.4))
cam.location = cam_pos
direction = mathutils.Vector((cx, cy, cz)) - cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("rendered", out_path)
