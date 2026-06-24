import math
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path(__file__).resolve().parent
OUT_EMPTY = ROOT / "newModels" / "HandCrossBow.fbx"
OUT_DRAWN = ROOT / "newModels" / "HandCrossBowDrawn.fbx"
FIT_OFFSET = Vector((0.0, -0.18, 0.65))
TEXTURE_OUT = (
    ROOT.parent
    / "PZCrossbows"
    / "Contents"
    / "mods"
    / "PZCrossbows"
    / "42"
    / "media"
    / "textures"
    / "weapons"
    / "firearm"
    / "HandCrossBow.png"
)


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    return m


def cube(name, loc, scale, material, rot=(0, 0, 0)):
    loc = tuple(Vector(loc) + FIT_OFFSET)
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("soft bevel", "BEVEL")
    bevel.width = min(scale) * 0.08
    bevel.segments = 1
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def cyl_between(name, p1, p2, radius, material, vertices=10):
    p1 = Vector(p1) + FIT_OFFSET
    p2 = Vector(p2) + FIT_OFFSET
    mid = (p1 + p2) * 0.5
    direction = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def join_model(mesh_name):
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = mesh_name
    obj.data.name = mesh_name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def write_hand_texture():
    TEXTURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    width = 128
    height = 128
    image = bpy.data.images.new("HandCrossBow_Texture", width=width, height=height, alpha=True)
    pixels = [0.0] * (width * height * 4)

    def fill_rect(x0, y0, x1, y1, color):
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * width + x) * 4
                grain = 1.0
                if color[3] > 0.0 and color[0] > color[2]:
                    grain = 0.88 + ((x * 7 + y * 3) % 17) / 100.0
                pixels[i : i + 4] = [
                    min(color[0] * grain, 1.0),
                    min(color[1] * grain, 1.0),
                    min(color[2] * grain, 1.0),
                    color[3],
                ]

    fill_rect(0, 64, 64, 128, (0.43, 0.23, 0.10, 1.0))   # wood
    fill_rect(64, 64, 128, 128, (0.045, 0.048, 0.050, 1.0)) # dark metal
    fill_rect(0, 0, 64, 64, (0.012, 0.012, 0.012, 1.0))     # cord
    fill_rect(64, 0, 128, 64, (0.60, 0.57, 0.48, 1.0))      # bolt point
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEXTURE_OUT)
    image.file_format = "PNG"
    image.save()


def assign_atlas_uv(obj):
    uv_layer = obj.data.uv_layers.new(name="UVMap") if not obj.data.uv_layers else obj.data.uv_layers.active
    blocks = {
        "PZC visible wood": ((0.08, 0.58), (0.42, 0.92)),
        "PZC dark metal": ((0.58, 0.58), (0.92, 0.92)),
        "PZC cord": ((0.08, 0.08), (0.42, 0.42)),
        "PZC point": ((0.58, 0.08), (0.92, 0.42)),
    }
    corners = [(0, 0), (1, 0), (1, 1), (0, 1)]

    for poly in obj.data.polygons:
        mat_name = obj.material_slots[poly.material_index].material.name
        (u0, v0), (u1, v1) = blocks.get(mat_name, blocks["PZC visible wood"])
        for n, loop_index in enumerate(poly.loop_indices):
            cu, cv = corners[n % 4]
            uv_layer.data[loop_index].uv = (u0 if cu == 0 else u1, v0 if cv == 0 else v1)


def match_reference_transform(obj, mesh_name, rotation):
    target = Matrix.LocRotScale(
        Vector((0.0, 0.0, 0.0)),
        Euler(rotation, "XYZ"),
        Vector((0.0001, 0.0001, 0.0001)),
    )
    inv = target.inverted()

    # Keep the visible world-space shape, but store it under the same object
    # transform style as the working B42 reference FBX.
    for vert in obj.data.vertices:
        world = obj.matrix_world @ vert.co
        vert.co = inv @ world

    obj.name = mesh_name
    obj.data.name = mesh_name
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = rotation
    obj.scale = (0.0001, 0.0001, 0.0001)
    return obj


def cone_between(name, p1, p2, radius1, radius2, material, vertices=10):
    p1 = Vector(p1) + FIT_OFFSET
    p2 = Vector(p2) + FIT_OFFSET
    mid = (p1 + p2) * 0.5
    direction = p2 - p1
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=direction.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def build_hand_crossbow(out_path, drawn=False):
    clear()
    wood = mat("PZC visible wood", (0.52, 0.28, 0.10, 1))
    dark = mat("PZC dark metal", (0.035, 0.04, 0.045, 1))
    cord = mat("PZC cord", (0.01, 0.01, 0.01, 1))
    point = mat("PZC point", (0.55, 0.52, 0.44, 1))

    # Old hand-crossbow space:
    # X = limb width, Z = front/back length, Y = thickness/depth.
    # Bounds are roughly x -4.47..4.47, y -2.97..4.13, z -1.06..10.15.
    cube("stock main", (0.0, -1.28, 5.35), (1.08, 0.92, 6.85), wood)
    cube("top rail", (0.0, -2.04, 5.95), (0.46, 0.34, 5.95), dark)
    cube("rear cap", (0.0, -1.22, 2.05), (1.32, 1.05, 1.10), dark)
    cube("rear wood block", (0.0, -1.10, 2.55), (1.10, 0.92, 1.20), wood)
    cube("front block", (0.0, -1.30, 8.55), (1.80, 0.96, 0.95), dark)
    cube("front wood insert", (0.0, -1.12, 8.25), (1.20, 0.76, 0.80), wood)

    # Grip and trigger below the stock.
    cube("pistol grip", (0.0, 0.82, 2.90), (0.86, 1.35, 1.80), wood, rot=(math.radians(-10), 0, 0))
    cube("grip butt", (0.0, 1.34, 2.05), (1.02, 0.36, 0.70), dark)
    cube("grip neck", (0.0, 0.12, 3.65), (0.92, 0.72, 1.35), wood, rot=(math.radians(-4), 0, 0))
    cube("trigger housing", (0.0, -0.15, 3.98), (1.18, 0.54, 1.18), dark)
    cube("trigger guard", (0.0, 0.24, 3.72), (1.10, 0.34, 0.96), dark)
    cube("trigger", (0.0, 0.58, 3.45), (0.26, 0.22, 0.62), dark, rot=(math.radians(18), 0, 0))

    # Bow limbs near the old front area.
    cube("left limb root", (-1.35, -1.30, 8.80), (2.20, 0.46, 0.48), dark, rot=(0, 0, math.radians(-4)))
    cube("right limb root", (1.35, -1.30, 8.80), (2.20, 0.46, 0.48), dark, rot=(0, 0, math.radians(4)))
    cube("left limb tip", (-3.25, -1.30, 8.68), (2.05, 0.40, 0.42), dark, rot=(0, 0, math.radians(-9)))
    cube("right limb tip", (3.25, -1.30, 8.68), (2.05, 0.40, 0.42), dark, rot=(0, 0, math.radians(9)))
    string_z = 6.30 if drawn else 7.05
    cyl_between("string left", (-4.18, -1.32, 8.55), (0.0, -1.62, string_z), 0.065, cord, 6)
    cyl_between("string right", (4.18, -1.32, 8.55), (0.0, -1.62, string_z), 0.065, cord, 6)

    # Simple sight/post details, all within old extents.
    cube("front sight", (0.0, -2.14, 9.35), (0.34, 0.28, 0.62), dark)
    cube("rear sight", (0.0, -2.12, 4.05), (0.44, 0.26, 0.36), dark)
    cube("side plate left", (-0.68, -1.54, 5.75), (0.18, 0.22, 4.35), dark)
    cube("side plate right", (0.68, -1.54, 5.75), (0.18, 0.22, 4.35), dark)
    if drawn:
        cyl_between("loaded short bolt", (0.0, -2.25, 3.75), (0.0, -2.25, 9.20), 0.085, wood, 8)
        cone_between("loaded short bolt head", (0.0, -2.25, 9.20), (0.0, -2.25, 9.90), 0.20, 0.0, point, 10)

    mesh_name = "Plane.009" if drawn else "Plane.001"
    rotation = (0.000003, math.radians(5.0), math.radians(90.0)) if drawn else (0.0, 0.0, math.radians(90.0))
    obj = join_model(mesh_name)
    assign_atlas_uv(obj)
    match_reference_transform(obj, mesh_name, rotation)
    write_hand_texture()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(out_path),
        use_selection=True,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_space_transform=False,
        apply_unit_scale=True,
        path_mode="AUTO",
    )
    print(f"exported {out_path}")


if __name__ == "__main__":
    build_hand_crossbow(OUT_EMPTY, drawn=False)
    build_hand_crossbow(OUT_DRAWN, drawn=True)
