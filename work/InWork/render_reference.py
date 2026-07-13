import bpy
import sys
import os
import math

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
obj_path = argv[0]
tex_path = argv[1]
out_path = argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.wm.obj_import(filepath=obj_path)
obj = bpy.context.selected_objects[0]
obj.name = "Reference"

# bounding box print
bbox = [obj.matrix_world @ v.co for v in obj.data.vertices]
xs = [v.x for v in bbox]
ys = [v.y for v in bbox]
zs = [v.z for v in bbox]
print(f"BBOX X: {min(xs):.4f} .. {max(xs):.4f}  (size {max(xs)-min(xs):.4f})")
print(f"BBOX Y: {min(ys):.4f} .. {max(ys):.4f}  (size {max(ys)-min(ys):.4f})")
print(f"BBOX Z: {min(zs):.4f} .. {max(zs):.4f}  (size {max(zs)-min(zs):.4f})")

mat = bpy.data.materials.new("RefMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load(tex_path)
mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
obj.data.materials.append(mat)

# lights
sun = bpy.data.objects.new("Sun1", bpy.data.lights.new("Sun1", type='SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
bpy.context.collection.objects.link(sun)

sun2 = bpy.data.objects.new("Sun2", bpy.data.lights.new("Sun2", type='SUN'))
sun2.data.energy = 1.5
sun2.rotation_euler = (math.radians(120), 0, math.radians(200))
bpy.context.collection.objects.link(sun2)

# camera - 3/4 view centered on bbox
cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
size = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), 0.3)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
dist = size * 4.0
cam.location = (cx + dist*0.7, cy - dist*0.9, cz + dist*0.5)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

# point camera at bbox center
direction = bpy.data.objects.new("empty", None)
direction.location = (cx, cy, cz)
bpy.context.collection.objects.link(direction)
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = direction
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.film_transparent = False
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.25, 1)
scene.world = world
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"rendered to {out_path}")
