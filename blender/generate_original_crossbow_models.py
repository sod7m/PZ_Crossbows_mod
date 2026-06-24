import json
import math
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path(__file__).resolve().parent
METRICS = ROOT / "reference_metrics.json"
OUT_DIR = ROOT / "newModels"
MOD_TEXTURE_DIR = (
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
)

CROSSBOW_FILES = {
    "CrossBow.fbx": ("crude", False),
    "CrossBowDrawn.fbx": ("crude", True),
    "ImprovedCrossBow.fbx": ("improved", False),
    "ImprovedCrossBowDrawn.fbx": ("improved", True),
    "CompoundCrossBow.fbx": ("compound", False),
    "CompoundCrossBowDrawn.fbx": ("compound", True),
    "HandCrossBow.fbx": ("hand", False),
    "HandCrossBowDrawn.fbx": ("hand", True),
}

CRUDE_REFERENCE_ROTATION = Euler((-math.pi / 2, 0.0, 0.0), "XYZ")
CRUDE_REFERENCE_SCALE = (0.0001, 0.0001, 0.0001)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def setup_materials(compound=False):
    return {
        "wood": material("PZC sealed walnut", (0.36, 0.20, 0.08, 1.0)),
        "pale": material("PZC carved maple", (0.58, 0.36, 0.16, 1.0)),
        "metal": material("PZC blued steel", (0.025, 0.028, 0.032, 1.0)),
        "rubber": material("PZC dark grip wrap", (0.012, 0.011, 0.010, 1.0)),
        "cord": material("PZC waxed string", (0.006, 0.005, 0.004, 1.0)),
        "bolt": material("PZC loaded wood bolt", (0.50, 0.31, 0.13, 1.0)),
        "tip": material("PZC stone point", (0.62, 0.60, 0.52, 1.0)),
    }


def write_texture_atlas(filename, compound=False):
    MOD_TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    image = bpy.data.images.new(filename, width=128, height=128, alpha=True)
    pixels = [0.0] * (128 * 128 * 4)

    def fill(x0, y0, x1, y1, color, grain=False):
        for y in range(y0, y1):
            for x in range(x0, x1):
                shade = 1.0
                if grain:
                    shade = 0.82 + ((x * 7 + y * 13) % 23) / 100.0
                i = (y * 128 + x) * 4
                pixels[i : i + 4] = [
                    min(color[0] * shade, 1.0),
                    min(color[1] * shade, 1.0),
                    min(color[2] * shade, 1.0),
                    color[3],
                ]

    wood = (0.44, 0.23, 0.085, 1.0) if not compound else (0.27, 0.18, 0.09, 1.0)
    metal = (0.030, 0.034, 0.038, 1.0) if not compound else (0.014, 0.018, 0.025, 1.0)
    fill(0, 64, 64, 128, wood, True)
    fill(64, 64, 128, 128, metal, False)
    fill(0, 0, 64, 64, (0.008, 0.007, 0.006, 1.0), False)
    fill(64, 0, 128, 64, (0.62, 0.59, 0.50, 1.0), False)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(MOD_TEXTURE_DIR / filename)
    image.file_format = "PNG"
    image.save()


def pt(bounds, x, y, z):
    mn = Vector(bounds["min"])
    size = Vector(bounds["size"])
    return Vector((mn.x + size.x * x, mn.y + size.y * y, mn.z + size.z * z))


def dims(bounds, x, y, z):
    size = Vector(bounds["size"])
    return (size.x * x, size.y * y, size.z * z)


def cube(name, loc, scale, mat, rot=(0, 0, 0), bevel_factor=0.16):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("softened bevels", "BEVEL")
    bevel.width = max(min(scale) * bevel_factor, min(scale) * 0.02)
    bevel.segments = 2
    bevel.harden_normals = True
    normal = obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    normal.keep_sharp = True
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cylinder_between(name, p1, p2, radius, mat, vertices=12):
    p1 = Vector(p1)
    p2 = Vector(p2)
    direction = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=direction.length,
        location=(p1 + p2) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cone_between(name, p1, p2, r1, r2, mat, vertices=14):
    p1 = Vector(p1)
    p2 = Vector(p2)
    direction = p2 - p1
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=r1,
        radius2=r2,
        depth=direction.length,
        location=(p1 + p2) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def torus(name, loc, major_radius, minor_radius, mat):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=24,
        minor_segments=8,
        location=loc,
        rotation=(math.pi / 2, 0, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def profile_prism(name, points, half_width, mat, bevel_width):
    verts = []
    for side in (-1, 1):
        for point in points:
            verts.append((point.x + half_width * side, point.y, point.z))

    count = len(points)
    faces = []
    faces.append(tuple(range(count - 1, -1, -1)))
    faces.append(tuple(range(count, count * 2)))
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, nxt + count, index + count))

    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("carved bevel", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 3
    bevel.harden_normals = True
    normal = obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    normal.keep_sharp = True
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def create_loaded_bolt(bounds, mats, hand=False, z_shift=0.0):
    y = 0.24
    z0 = 0.40 if not hand else 0.34
    z1 = 0.78 if not hand else 0.72
    z0 = min(z0 + z_shift, 0.92)
    z1 = min(z1 + z_shift, 0.96)
    radius = min(Vector(bounds["size"])) * (0.012 if not hand else 0.010)
    cylinder_between("loaded bolt shaft", pt(bounds, 0.5, y, z0), pt(bounds, 0.5, y, z1), radius, mats["bolt"], 10)
    cone_between("loaded stone head", pt(bounds, 0.5, y, z1), pt(bounds, 0.5, y, min(z1 + 0.08, 0.96)), radius * 2.3, 0, mats["tip"], 12)
    cube("loaded fletching", pt(bounds, 0.5, y, max(z0 - 0.04, 0.08)), dims(bounds, 0.09, 0.030, 0.025), mats["rubber"])


def create_crossbow(bounds, style, drawn, mats):
    hand = style == "hand"
    compound = style == "compound"
    improved = style == "improved"
    crude = style == "crude"
    wood = mats["wood"]
    limb_mat = mats["metal"] if compound else wood
    min_dim = min(Vector(bounds["size"]))

    if hand:
        cube("compact main body", pt(bounds, 0.5, 0.46, 0.46), dims(bounds, 0.16, 0.38, 0.56), wood)
        cube("short top rail", pt(bounds, 0.5, 0.27, 0.50), dims(bounds, 0.08, 0.12, 0.70), mats["metal"])
        cube("angled pistol grip", pt(bounds, 0.5, 0.78, 0.26), dims(bounds, 0.14, 0.30, 0.26), mats["rubber"], rot=(math.radians(-12), 0, 0))
        cube("four bolt feed box", pt(bounds, 0.5, 0.22, 0.33), dims(bounds, 0.23, 0.18, 0.18), mats["metal"])
        cube("trigger loop", pt(bounds, 0.5, 0.64, 0.36), dims(bounds, 0.20, 0.10, 0.10), mats["metal"])
        cube("front limb block", pt(bounds, 0.5, 0.42, 0.78), dims(bounds, 0.18, 0.16, 0.10), mats["metal"])
        cube("left short limb", pt(bounds, 0.26, 0.42, 0.80), dims(bounds, 0.45, 0.09, 0.07), limb_mat, rot=(0, 0, math.radians(-7)))
        cube("right short limb", pt(bounds, 0.74, 0.42, 0.80), dims(bounds, 0.45, 0.09, 0.07), limb_mat, rot=(0, 0, math.radians(7)))
        string_y = 0.62 if drawn else 0.45
        cylinder_between("left bow string", pt(bounds, 0.04, 0.43, 0.80), pt(bounds, 0.5, string_y, 0.70), min_dim * 0.010, mats["cord"], 6)
        cylinder_between("right bow string", pt(bounds, 0.96, 0.43, 0.80), pt(bounds, 0.5, string_y, 0.70), min_dim * 0.010, mats["cord"], 6)
        if drawn:
            create_loaded_bolt(bounds, mats, True)
        return

    forward_shift = {
        "crude": 0.10,
        "improved": 0.18,
        "compound": 0.12,
    }.get(style, 0.12)

    def fz(z):
        if improved or crude:
            return z + forward_shift
        return min(z + forward_shift, 0.97)

    def p(x, y, z):
        return pt(bounds, x, y, fz(z))

    if improved or crude:
        size = Vector(bounds["size"])
        if improved:
            body_points = [
                p(0.5, 0.55, 0.16),
                p(0.5, 0.67, 0.25),
                p(0.5, 0.61, 0.43),
                p(0.5, 0.49, 0.57),
                p(0.5, 0.43, 0.82),
                p(0.5, 0.34, 0.91),
                p(0.5, 0.24, 0.86),
                p(0.5, 0.24, 0.56),
                p(0.5, 0.31, 0.36),
                p(0.5, 0.38, 0.18),
            ]
            half_width = size.x * 0.060
            bevel_width = min(size.x, size.y, size.z) * 0.035
        else:
            body_points = [
                p(0.5, 0.56, 0.18),
                p(0.5, 0.67, 0.28),
                p(0.5, 0.58, 0.44),
                p(0.5, 0.48, 0.58),
                p(0.5, 0.42, 0.82),
                p(0.5, 0.34, 0.90),
                p(0.5, 0.27, 0.84),
                p(0.5, 0.28, 0.56),
                p(0.5, 0.35, 0.36),
                p(0.5, 0.42, 0.20),
            ]
            half_width = size.x * 0.050
            bevel_width = min(size.x, size.y, size.z) * 0.028
        profile_prism(
            "one piece improved stock" if improved else "one piece crude stock",
            body_points,
            half_width,
            wood,
            bevel_width,
        )
        rail_mat = mats["metal"] if improved else wood
        cylinder_between("rounded top rail", p(0.5, 0.22, 0.42), p(0.5, 0.22, 0.90), min_dim * (0.030 if improved else 0.026), rail_mat, 12)
        cylinder_between("lower tension rail", p(0.5, 0.54, 0.43), p(0.5, 0.54, 0.80), min_dim * (0.025 if improved else 0.022), rail_mat, 12)
        if improved:
            cylinder_between("left cheek rail", p(0.39, 0.34, 0.40), p(0.39, 0.34, 0.83), min_dim * 0.023, mats["metal"], 10)
            cylinder_between("right cheek rail", p(0.61, 0.34, 0.40), p(0.61, 0.34, 0.83), min_dim * 0.023, mats["metal"], 10)
            cube("front reinforced nose", p(0.5, 0.39, 0.91), dims(bounds, 0.165, 0.14, 0.12), mats["metal"], bevel_factor=0.12)
        else:
            cube("cloth front wrap", p(0.5, 0.39, 0.82), dims(bounds, 0.145, 0.095, 0.095), mats["rubber"], bevel_factor=0.12)
            cube("wood nose block", p(0.5, 0.40, 0.91), dims(bounds, 0.130, 0.105, 0.105), wood, bevel_factor=0.12)
        cube("wrapped rear grip", p(0.5, 0.72, 0.24), dims(bounds, 0.105, 0.18, 0.16), mats["rubber"], rot=(math.radians(-12), 0, 0), bevel_factor=0.14)

        limb_z = 0.88 if improved else 0.86
        cylinder_between("left improved limb", p(0.04, 0.42, limb_z), p(0.50, 0.42, 0.82), min_dim * (0.045 if improved else 0.040), wood, 12)
        cylinder_between("right improved limb", p(0.96, 0.42, limb_z), p(0.50, 0.42, 0.82), min_dim * (0.045 if improved else 0.040), wood, 12)
        if improved:
            cylinder_between("left metal limb strip", p(0.08, 0.37, limb_z), p(0.50, 0.37, 0.83), min_dim * 0.020, mats["metal"], 10)
            cylinder_between("right metal limb strip", p(0.92, 0.37, limb_z), p(0.50, 0.37, 0.83), min_dim * 0.020, mats["metal"], 10)

        string_y = 0.68 if drawn else 0.45
        cylinder_between("left bow string", p(0.03, 0.43, limb_z), p(0.5, string_y, 0.72), min_dim * 0.006, mats["cord"], 6)
        cylinder_between("right bow string", p(0.97, 0.43, limb_z), p(0.5, string_y, 0.72), min_dim * 0.006, mats["cord"], 6)
        if drawn:
            create_loaded_bolt(bounds, mats, False, forward_shift)
            cube("cocked latch", p(0.5, 0.48, 0.50), dims(bounds, 0.075, 0.065, 0.045), mats["metal"], bevel_factor=0.12)
        else:
            cube("empty latch", p(0.5, 0.37, 0.50), dims(bounds, 0.065, 0.055, 0.040), mats["metal"], bevel_factor=0.12)
        return

    cube("slim carved stock", p(0.5, 0.43, 0.40), dims(bounds, 0.070, 0.18, 0.45), wood, bevel_factor=0.11)
    cube("flat shoulder plate", p(0.5, 0.47, 0.17), dims(bounds, 0.16, 0.16, 0.060), wood, bevel_factor=0.10)
    cube("top guide rail", p(0.5, 0.27, 0.50), dims(bounds, 0.040, 0.065, 0.62), mats["metal"], bevel_factor=0.10)
    cube("small trigger guard", p(0.5, 0.60, 0.37), dims(bounds, 0.11, 0.075, 0.055), mats["metal"], bevel_factor=0.10)
    cube("wrapped grip", p(0.5, 0.71, 0.28), dims(bounds, 0.075, 0.19, 0.14), mats["rubber"], rot=(math.radians(-13), 0, 0), bevel_factor=0.10)
    cube("front block", p(0.5, 0.41, 0.76), dims(bounds, 0.10, 0.095, 0.075), mats["metal"], bevel_factor=0.10)

    if crude:
        cube("cloth front wrap", p(0.5, 0.30, 0.67), dims(bounds, 0.15, 0.060, 0.050), mats["rubber"], bevel_factor=0.10)
        cube("cloth rear wrap", p(0.5, 0.33, 0.35), dims(bounds, 0.12, 0.060, 0.045), mats["rubber"], bevel_factor=0.10)
    limb_z = 0.76 if compound else 0.78
    limb_y = 0.050
    limb_h = 0.040
    outer_limb_y = 0.045
    outer_limb_h = 0.035
    inner_limb_x = 0.30
    outer_limb_x = 0.23
    cube("left limb inner", p(0.32, 0.43, limb_z), dims(bounds, inner_limb_x, limb_y, limb_h), limb_mat, rot=(0, 0, math.radians(-5)), bevel_factor=0.09)
    cube("right limb inner", p(0.68, 0.43, limb_z), dims(bounds, inner_limb_x, limb_y, limb_h), limb_mat, rot=(0, 0, math.radians(5)), bevel_factor=0.09)
    cube("left limb outer", p(0.13, 0.42, limb_z), dims(bounds, outer_limb_x, outer_limb_y, outer_limb_h), limb_mat, rot=(0, 0, math.radians(8)), bevel_factor=0.09)
    cube("right limb outer", p(0.87, 0.42, limb_z), dims(bounds, outer_limb_x, outer_limb_y, outer_limb_h), limb_mat, rot=(0, 0, math.radians(-8)), bevel_factor=0.09)

    if compound:
        pulley_r = Vector(bounds["size"]).x * 0.035
        torus("left cam wheel", p(0.105, 0.43, 0.77), pulley_r, pulley_r * 0.14, mats["metal"])
        torus("right cam wheel", p(0.895, 0.43, 0.77), pulley_r, pulley_r * 0.14, mats["metal"])
        cylinder_between("front compound cable", p(0.105, 0.43, 0.75), p(0.895, 0.43, 0.75), min_dim * 0.006, mats["cord"], 6)
        cylinder_between("rear compound cable", p(0.16, 0.49, 0.81), p(0.84, 0.49, 0.81), min_dim * 0.006, mats["cord"], 6)
        cube("scope dovetail", p(0.5, 0.17, 0.50), dims(bounds, 0.075, 0.040, 0.26), mats["metal"], bevel_factor=0.08)
    else:
        string_y = 0.68 if drawn else 0.44
        string_anchor = limb_z
        string_mid_z = 0.65
        cylinder_between("left bow string", p(0.03, 0.43, string_anchor), p(0.5, string_y, string_mid_z), min_dim * 0.006, mats["cord"], 6)
        cylinder_between("right bow string", p(0.97, 0.43, string_anchor), p(0.5, string_y, string_mid_z), min_dim * 0.006, mats["cord"], 6)

    if drawn:
        create_loaded_bolt(bounds, mats, False, forward_shift)
        cube("cocked latch", p(0.5, 0.49, 0.47), dims(bounds, 0.070, 0.060, 0.045), mats["metal"], bevel_factor=0.10)
    else:
        cube("empty latch", p(0.5, 0.37, 0.47), dims(bounds, 0.060, 0.050, 0.040), mats["metal"], bevel_factor=0.10)


def convert_and_join():
    bpy.ops.object.select_all(action="SELECT")
    for obj in list(bpy.context.selected_objects):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.convert(target="MESH")
        except RuntimeError:
            pass
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = "PZC_OriginalCrossbow"
    obj.data.name = "PZC_OriginalCrossbowMesh"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_atlas_uv(obj)
    return obj


def atlas_region(material_name):
    name = material_name.lower()
    if "steel" in name:
        return (0.56, 0.56, 0.94, 0.94)
    if "grip" in name or "string" in name:
        return (0.06, 0.06, 0.44, 0.44)
    if "stone" in name:
        return (0.56, 0.06, 0.94, 0.44)
    return (0.06, 0.56, 0.44, 0.94)


def normalized(value, low, size):
    if abs(size) < 1e-12:
        return 0.5
    return max(0.0, min(1.0, (value - low) / size))


def assign_atlas_uv(obj):
    mesh = obj.data
    uv_layer = mesh.uv_layers.new(name="PZC_Atlas")
    mn, _mx, size = mesh_bounds(obj)

    for poly in mesh.polygons:
        mat = mesh.materials[poly.material_index] if poly.material_index < len(mesh.materials) else None
        region = atlas_region(mat.name if mat else "")
        u0, v0, u1, v1 = region
        for loop_index in poly.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            co = obj.matrix_world @ vertex.co
            u = u0 + (u1 - u0) * normalized(co.z, mn.z, size.z)
            v = v0 + (v1 - v0) * normalized(co.x, mn.x, size.x)
            uv_layer.data[loop_index].uv = (u, v)


def mesh_bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    mins = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maxs = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return mins, maxs, maxs - mins


def fit_mesh_to_bounds(obj, bounds):
    target_min = Vector(bounds["min"])
    target_size = Vector(bounds["size"])
    source_min, _source_max, source_size = mesh_bounds(obj)
    for vertex in obj.data.vertices:
        co = vertex.co.copy()
        ratios = []
        for i in range(3):
            if abs(source_size[i]) < 1e-12:
                ratios.append(0.5)
            else:
                ratios.append((co[i] - source_min[i]) / source_size[i])
        vertex.co = Vector((
            target_min.x + ratios[0] * target_size.x,
            target_min.y + ratios[1] * target_size.y,
            target_min.z + ratios[2] * target_size.z,
        ))
    bpy.context.view_layer.update()


def move_mesh_world(obj, offset):
    matrix_inv = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world_co = obj.matrix_world @ vertex.co
        vertex.co = matrix_inv @ (world_co + offset)
    bpy.context.view_layer.update()


def rotate_mesh_world(obj, angle, axis):
    mins, maxs, _size = mesh_bounds(obj)
    center = (mins + maxs) * 0.5
    rotation = Matrix.Rotation(angle, 4, axis)
    matrix_inv = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world_co = obj.matrix_world @ vertex.co
        vertex.co = matrix_inv @ (center + rotation @ (world_co - center))
    bpy.context.view_layer.update()


def apply_reference_transform(obj, rotation, scale):
    old_world = obj.matrix_world.copy()
    target = Matrix.LocRotScale(obj.location.copy(), rotation, scale)
    target_inv = target.inverted()
    for vertex in obj.data.vertices:
        world_co = old_world @ vertex.co
        vertex.co = target_inv @ world_co
    obj.rotation_euler = rotation
    obj.scale = scale
    bpy.context.view_layer.update()


def export_model(filename, bounds, style, drawn):
    clear_scene()
    mats = setup_materials(style == "compound")
    create_crossbow(bounds, style, drawn, mats)
    obj = convert_and_join()
    if style == "hand":
        fit_mesh_to_bounds(obj, bounds)
    elif style == "improved":
        move_mesh_world(obj, Vector((0.0, Vector(bounds["size"]).y * 0.33, Vector(bounds["size"]).z * 0.32)))
    elif style == "compound":
        move_mesh_world(obj, Vector((0.0, Vector(bounds["size"]).y * 0.35, 0.0)))
    elif style == "crude":
        apply_reference_transform(obj, CRUDE_REFERENCE_ROTATION, CRUDE_REFERENCE_SCALE)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    OUT_DIR.mkdir(exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(OUT_DIR / filename),
        use_selection=True,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_space_transform=False,
        apply_unit_scale=True,
        path_mode="AUTO",
    )
    print(f"exported {filename}")


def render_preview():
    files = sorted(CROSSBOW_FILES)
    clear_scene()
    for idx, filename in enumerate(files):
        bpy.ops.import_scene.fbx(filepath=str(OUT_DIR / filename))
        imported = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
        if not imported:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in imported:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = imported[0]
        if len(imported) > 1:
            bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        mn, _mx, size = mesh_bounds(obj)
        max_size = max(size.x, size.y, size.z)
        if max_size > 0:
            obj.scale = (1.0 / max_size, 1.0 / max_size, 1.0 / max_size)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mn, mx, _size = mesh_bounds(obj)
        center = (mn + mx) * 0.5
        obj.location -= center
        obj.location.x += (idx % 4) * 1.45
        obj.location.z += (idx // 4) * 1.25
        obj.name = filename.removesuffix(".fbx")
    bpy.ops.object.light_add(type="AREA", location=(2.2, -5.0, 3.0))
    bpy.context.object.data.energy = 700
    bpy.context.object.data.size = 5.0
    bpy.ops.object.camera_add(location=(2.1, -7.5, 1.3), rotation=(math.radians(80), 0, 0))
    bpy.context.object.data.type = "ORTHO"
    bpy.context.object.data.ortho_scale = 5.0
    bpy.context.scene.camera = bpy.context.object
    bpy.context.scene.world.color = (0.025, 0.025, 0.028)
    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 900
    bpy.context.scene.render.filepath = str(OUT_DIR / "newModels_preview.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_DIR / "newModels_overview.blend"))
    bpy.ops.render.render(write_still=True)


def main():
    write_texture_atlas("CrossBow.png", compound=False)
    write_texture_atlas("CompoundCrossBow.png", compound=True)
    write_texture_atlas("HandCrossBow.png", compound=False)
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    for filename, (style, drawn) in CROSSBOW_FILES.items():
        bounds_filename = {
            "CrossBowDrawn.fbx": "CrossBow.fbx",
            "ImprovedCrossBowDrawn.fbx": "ImprovedCrossBow.fbx",
            "CompoundCrossBowDrawn.fbx": "CompoundCrossBow.fbx",
        }.get(filename, filename)
        export_model(filename, metrics[bounds_filename]["bounds"], style, drawn)
    render_preview()


if __name__ == "__main__":
    main()
