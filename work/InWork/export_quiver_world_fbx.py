"""Export the final quiver OBJ as a centered, ground-ready static FBX."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OBJ = ROOT / "work/InWork/final/BoltQuiverWorld.obj"
TEXTURE = ROOT / "PZCrossbows/Contents/mods/PZCrossbows/42/media/textures/Clothes/BoltQuiver.png"
DESTINATION = ROOT / "PZCrossbows/Contents/mods/PZCrossbows/42/media/models_x/PZCrossbows/BoltQuiver.fbx"
PREVIEW = ROOT / "work/InWork/final/quiver_world_preview.png"


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(OBJ))
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
obj.name = "BoltQuiver"

# Rotate the cassette's front normal onto world +Z so the leather face and
# the row of bolts are readable from the isometric camera.  A small yaw keeps
# the silhouette from aligning with a tile edge.
panel_normal = Vector((0.0, -0.037, 0.032)).normalized()
obj.rotation_mode = "QUATERNION"
obj.rotation_quaternion = panel_normal.rotation_difference(Vector((0.0, 0.0, 1.0)))
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
obj.rotation_mode = "XYZ"
obj.rotation_euler.z = math.radians(28.0)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

corners = [obj.matrix_world @ v.co for v in obj.data.vertices]
min_x, max_x = min(v.x for v in corners), max(v.x for v in corners)
min_y, max_y = min(v.y for v in corners), max(v.y for v in corners)
min_z = min(v.z for v in corners)
obj.location = (-(min_x + max_x) * 0.5, -(min_y + max_y) * 0.5, -min_z + 0.006)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

material = bpy.data.materials.new("BoltQuiver")
material.use_nodes = True
image = bpy.data.images.load(str(TEXTURE))
tex = material.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = image
bsdf = material.node_tree.nodes.get("Principled BSDF")
material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
obj.data.materials.clear()
obj.data.materials.append(material)

DESTINATION.parent.mkdir(parents=True, exist_ok=True)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=str(DESTINATION),
    use_selection=True,
    object_types={"MESH"},
    apply_unit_scale=True,
    bake_space_transform=False,
    axis_forward="-Z",
    axis_up="Y",
    add_leaf_bones=False,
    path_mode="STRIP",
    embed_textures=False,
)
print(DESTINATION)
print("dimensions", tuple(round(v, 6) for v in obj.dimensions))

# Blender render of the exact static orientation exported above.
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, 0))
plane = bpy.context.object
ground = bpy.data.materials.new("Ground")
ground.diffuse_color = (0.075, 0.082, 0.090, 1)
plane.data.materials.append(ground)

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.025, 0.030, 0.035, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
bpy.context.scene.world = world

sun_data = bpy.data.lights.new("Sun", "AREA")
sun_data.energy = 650
sun_data.shape = "DISK"
sun_data.size = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.location = (1.8, 1.2, 2.5)
bpy.context.scene.collection.objects.link(sun)

camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location = (0.75, -0.95, 0.78)
direction = -camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 58
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
bpy.ops.render.render(write_still=True)
print(PREVIEW)
