"""Build a polished, stylised version of the mod's crude crossbow.

Run with Blender 5.1+ in background mode.  The source mesh remains intact;
all detail is separate, named geometry so it can be tuned or removed easily.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


WORKSPACE = Path(__file__).resolve().parents[1]
SOURCE = WORKSPACE / "backup" / "original_before_detailed" / "CrossBow.fbx"
BLEND_OUT = WORKSPACE / "work" / "models" / "CrossBow_Detailed.blend"
FBX_OUT = WORKSPACE / "work" / "models" / "CrossBow_Detailed.fbx"
PREVIEW_OUT = WORKSPACE / "work" / "textures" / "CrossBow_Detailed_preview.png"


def material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    return mat


WALNUT = WOOD_LIGHT = LEATHER = IRON = BRONZE = CORD = STEEL = None


def create_materials():
    """Create materials after Blender's factory reset has cleared its data."""
    global WALNUT, WOOD_LIGHT, LEATHER, IRON, BRONZE, CORD, STEEL
    WALNUT = material("M_Walnut", (0.16, 0.045, 0.014), 0.0, 0.34)
    WOOD_LIGHT = material("M_Wood_Inlay", (0.45, 0.15, 0.035), 0.0, 0.38)
    LEATHER = material("M_Leather", (0.055, 0.018, 0.008), 0.0, 0.58)
    IRON = material("M_Blackened_Iron", (0.035, 0.045, 0.05), 0.78, 0.24)
    BRONZE = material("M_Antique_Bronze", (0.33, 0.12, 0.025), 0.75, 0.25)
    CORD = material("M_Waxed_Cord", (0.18, 0.11, 0.045), 0.0, 0.7)
    STEEL = material("M_Bolt_Steel", (0.12, 0.15, 0.17), 0.92, 0.18)


def move_to_detail_collection(obj):
    details = bpy.data.collections.get("DETAILS")
    if not details:
        details = bpy.data.collections.new("DETAILS")
        bpy.context.scene.collection.children.link(details)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    details.objects.link(obj)
    return obj


def add_bevel(obj, width=0.08, segments=3):
    modifier = obj.modifiers.new("Soft edges", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"


def cube(name, location, dimensions, mat, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        add_bevel(obj, bevel)
    return move_to_detail_collection(obj)


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    add_bevel(obj, min(radius * 0.25, 0.05), 2)
    return move_to_detail_collection(obj)


def torus(name, location, major_radius, minor_radius, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=32,
        minor_segments=8,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return move_to_detail_collection(obj)


def cone(name, location, radius1, radius2, depth, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=16,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return move_to_detail_collection(obj)


def curve(name, points, radius, mat):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 3
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.data.collections["DETAILS"].objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def point_camera(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


# Reset, import the in-game mesh, and use it as the retained low-poly core.
bpy.ops.wm.read_factory_settings(use_empty=True)
create_materials()
bpy.ops.import_scene.fbx(filepath=str(SOURCE))
base_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
for obj in base_meshes:
    obj.name = "PZC_CrossBow_Base"
    obj.data.materials.clear()
    obj.data.materials.append(WALNUT)
    obj["source"] = "Original PZCrossbows CrossBow.fbx"
    obj["role"] = "Preserved game mesh beneath the high-detail additions"

# The front of the in-game mesh faces negative Y.  Build all ornamental layers
# just in front of it, keeping the original silhouette readable.
# Reinforced central rail and carved stock panels.
cube("Rail_BlackenedIron", (0, -1.95, 7.0), (0.72, 0.22, 16.2), IRON, 0.05)
cube("Rail_Bronze_Inlay", (0, -2.08, 7.5), (0.18, 0.055, 13.4), BRONZE, 0.025)
cube("Stock_Cheek_Panel", (0, -1.88, 1.3), (1.46, 0.18, 5.7), WOOD_LIGHT, 0.16)
cube("Stock_Grip_Panel", (0, -2.02, -0.7), (0.72, 0.10, 3.2), LEATHER, 0.12)

# Leather straps around the stock; the torus rings make the binding read from
# every angle rather than as flat painted bands.
for z in (8.7, 9.25, 12.2, 12.75):
    torus(f"Leather_Binding_{z}", (0, 0, z), 0.88, 0.11, LEATHER)

# Bronze pins and a decorative central boss.
for z in (2.2, 4.6, 10.4):
    cylinder(f"Stock_Pin_{z}", (0, -2.16, z), 0.20, 0.12, BRONZE, rotation=(math.pi / 2, 0, 0))
torus("Central_Bronze_Boss", (0, -2.18, 11.65), 0.44, 0.12, BRONZE, rotation=(math.pi / 2, 0, 0))

# A metal riser, recurved limb reinforcements, and plated limb tips.
cube("Forged_Riser", (0, -1.92, 14.75), (2.25, 0.62, 1.8), IRON, 0.14)
cube("Riser_Faceplate", (0, -2.27, 14.75), (1.44, 0.08, 1.12), BRONZE, 0.07)
for side in (-1, 1):
    sx = float(side)
    curve(
        f"Reinforced_Limb_{'L' if side < 0 else 'R'}",
        [(0.8 * sx, -2.06, 14.8), (4.0 * sx, -2.16, 14.65), (7.7 * sx, -2.1, 15.75), (9.15 * sx, -1.98, 16.45)],
        0.19,
        IRON,
    )
    curve(
        f"Limb_Bronze_Filigree_{'L' if side < 0 else 'R'}",
        [(1.2 * sx, -2.29, 14.75), (4.15 * sx, -2.31, 14.75), (7.45 * sx, -2.24, 15.7)],
        0.055,
        BRONZE,
    )
    cube(f"Limb_Tip_Cap_{'L' if side < 0 else 'R'}", (9.02 * sx, -1.96, 16.35), (0.62, 0.55, 0.92), IRON, 0.08)
    cylinder(
        f"Limb_Rivet_{'L' if side < 0 else 'R'}",
        (6.5 * sx, -2.30, 15.45),
        0.14,
        0.10,
        BRONZE,
        rotation=(math.pi / 2, 0, 0),
    )

# A proper loaded bolt: a wooden shaft seated in the rail, a steel head, and
# fletching near the stock.  Its Z axis follows the original game's rail.
cylinder("Loaded_Bolt_Shaft", (0, -2.18, 14.7), 0.115, 8.4, WOOD_LIGHT, vertices=12)
cone("Loaded_Bolt_Head", (0, -2.18, 19.25), 0.38, 0.0, 1.35, STEEL)
for x in (-0.34, 0.34):
    fin = cube(f"Bolt_Fletching_{'L' if x < 0 else 'R'}", (x, -2.18, 10.85), (0.42, 0.06, 1.15), LEATHER, 0.03)
    fin.rotation_euler.y = 0.20 if x < 0 else -0.20

# String, braided retention cord, and a readable trigger mechanism.
curve("Bow_String", [(-9.05, -2.12, 16.35), (0, -2.34, 13.65), (9.05, -2.12, 16.35)], 0.055, CORD)
curve("Retention_Cord", [(-1.0, -2.13, 15.2), (0, -2.40, 14.2), (1.0, -2.13, 15.2)], 0.075, CORD)
cube("Trigger_Housing", (0, -2.04, 5.45), (1.18, 0.34, 1.45), IRON, 0.1)
torus("Trigger_Guard", (0, -2.08, 4.65), 0.57, 0.075, BRONZE, rotation=(math.pi / 2, 0, 0))
curve("Trigger", [(0, -2.23, 5.22), (0.23, -2.36, 4.72), (0.05, -2.30, 4.28)], 0.085, BRONZE)

# Small engraved chevrons on the lower stock for a crafted, stylised finish.
for index, z in enumerate((0.0, 0.72, 1.44)):
    curve(f"Stock_Engraving_{index}", [(-0.32, -2.135, z + 0.14), (0, -2.15, z - 0.12), (0.32, -2.135, z + 0.14)], 0.026, BRONZE)

# Bring the detail pass close to the original front surface.  This keeps the
# forged limb curves as reinforcement plates rather than reading as a second,
# disconnected bow.
for obj in bpy.data.collections["DETAILS"].objects:
    obj.location.y += 0.45
    if obj.name.startswith(("Reinforced_Limb", "Limb_Bronze", "Limb_Tip", "Limb_Rivet", "Bow_String")):
        obj.location.y += 1.3

# Give all detail meshes useful metadata for future art passes.
for obj in bpy.data.collections["DETAILS"].objects:
    obj["role"] = "Stylised high-detail crossbow component"

# Presentation camera/lights stay in the blend file but are excluded from FBX.
presentation = bpy.data.collections.new("PRESENTATION")
bpy.context.scene.collection.children.link(presentation)

def add_light(location, energy, size):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    for collection in list(light.users_collection):
        collection.objects.unlink(light)
    presentation.objects.link(light)
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    point_camera(light, (0, 0, 8))


add_light((10, -13, 22), 1100, 12)
add_light((-15, -5, 11), 850, 10)
add_light((0, 9, 10), 650, 9)
bpy.ops.object.camera_add(location=(28, -36, 24))
camera = bpy.context.object
for collection in list(camera.users_collection):
    collection.objects.unlink(camera)
presentation.objects.link(camera)
camera.data.lens = 52
point_camera(camera, (0, 0, 8))
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW_OUT)
scene.world = bpy.data.worlds.new("Studio World")
scene.world.color = (0.025, 0.025, 0.025)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
# Blender's FBX exporter only accepts mesh objects in 5.1.  Preserve editable
# curves in the .blend, then convert a temporary export scene representation.
for obj in list(bpy.context.scene.objects):
    if obj.type == "CURVE":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
bpy.ops.export_scene.fbx(
    filepath=str(FBX_OUT),
    use_selection=False,
    object_types={"MESH"},
    add_leaf_bones=False,
    bake_anim=False,
    path_mode="AUTO",
)
bpy.ops.render.render(write_still=True)
print(f"Created {BLEND_OUT}")
print(f"Created {FBX_OUT}")
print(f"Created {PREVIEW_OUT}")
