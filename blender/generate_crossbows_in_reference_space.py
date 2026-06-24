import math
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "newModels"
TEXTURE_DIR = (
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
FORWARD_SHIFT = 0.0


SPECS = {
    "CrossBow.fbx": {
        "mesh": "Plane.006",
        "texture": "CrossBow.png",
        "rotation": (-math.pi / 2, 0.0, 0.0),
        "scale": (0.0001, 0.0001, 0.0001),
        "min": (-9.6045188904, -2.6333463192, -15.5598411560),
        "max": (9.5829858780, 2.4640772343, 6.2386994362),
        "style": "crude",
        "drawn": False,
    },
    "CrossBowDrawn.fbx": {
        "mesh": "Plane.006",
        "texture": "CrossBow.png",
        "rotation": (-math.pi / 2, 0.0, 0.0),
        "scale": (0.0001, 0.0001, 0.0001),
        "min": (-9.4361839294, -2.6333463192, -15.5738477707),
        "max": (9.4361848831, 2.4640772343, 6.2386994362),
        "style": "crude",
        "drawn": True,
    },
    "ImprovedCrossBow.fbx": {
        "mesh": "ImprovedCrossbow",
        "texture": "CrossBow.png",
        "rotation": (-0.000001, -math.pi, 0.0),
        "scale": (0.0001, 0.0001, 0.0001),
        "min": (-0.0024951173, -0.0007794180, -0.0038452158),
        "max": (0.0024951173, 0.0006866439, 0.0016259779),
        "style": "improved",
        "drawn": False,
    },
    "ImprovedCrossBowDrawn.fbx": {
        "mesh": "ICDrawn",
        "texture": "CrossBow.png",
        "rotation": (-0.000001, -math.pi, 0.0),
        "scale": (0.0001, 0.0001, 0.0001),
        "min": (-0.0024536136, -0.0007855215, -0.0039013682),
        "max": (0.0024536136, 0.0006805405, 0.0016479505),
        "style": "improved",
        "drawn": True,
    },
    "CompoundCrossBow.fbx": {
        "mesh": "CompoundCrossbow",
        "texture": "CompoundCrossBow.png",
        "rotation": (-math.pi, 0.0, 0.0),
        "scale": (0.0001, 0.0001, 0.0001),
        "min": (-0.0020825195, -0.0007006842, -0.0017175294),
        "max": (0.0020825195, 0.0003457644, 0.0041650389),
        "style": "compound",
        "drawn": False,
    },
    "CompoundCrossBowDrawn.fbx": {
        "mesh": "CompoundCrossbowDrawn",
        "texture": "CompoundCrossBow.png",
        "rotation": (0.0, -math.pi, 0.0),
        "scale": (0.0001, 0.0001, 0.0001),
        "min": (-0.0018286133, -0.0007006839, -0.0041406252),
        "max": (0.0018286136, 0.0003457651, 0.0017382818),
        "style": "compound",
        "drawn": True,
    },
}


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_mat(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def materials():
    return {
        "wood": make_mat("PZC wood", (0.42, 0.22, 0.08, 1.0)),
        "lightwood": make_mat("PZC light wood", (0.55, 0.34, 0.14, 1.0)),
        "metal": make_mat("PZC dark metal", (0.035, 0.038, 0.042, 1.0)),
        "cord": make_mat("PZC cord", (0.01, 0.01, 0.01, 1.0)),
        "point": make_mat("PZC point", (0.60, 0.57, 0.48, 1.0)),
    }


def write_atlas(filename, compound=False):
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    width = 128
    height = 128
    image = bpy.data.images.new(filename, width=width, height=height, alpha=True)
    pixels = [0.0] * (width * height * 4)

    def fill_rect(x0, y0, x1, y1, color, grain=False):
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * width + x) * 4
                g = 1.0
                if grain:
                    g = 0.87 + ((x * 5 + y * 11) % 19) / 100.0
                pixels[i : i + 4] = [
                    min(color[0] * g, 1.0),
                    min(color[1] * g, 1.0),
                    min(color[2] * g, 1.0),
                    color[3],
                ]

    wood = (0.50, 0.28, 0.10, 1.0) if not compound else (0.38, 0.23, 0.10, 1.0)
    metal = (0.020, 0.024, 0.028, 1.0) if not compound else (0.010, 0.014, 0.020, 1.0)
    fill_rect(0, 64, 64, 128, wood, True)
    fill_rect(64, 64, 128, 128, metal, False)
    fill_rect(0, 0, 64, 64, (0.010, 0.010, 0.010, 1.0), False)
    fill_rect(64, 0, 128, 64, (0.60, 0.57, 0.48, 1.0), False)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEXTURE_DIR / filename)
    image.file_format = "PNG"
    image.save()


def point(mins, dims, x, y, z):
    return Vector((mins.x + dims.x * x, mins.y + dims.y * y, mins.z + dims.z * z))


def cube(name, loc, scale, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("soft bevel", "BEVEL")
    bevel.width = min(scale) * 0.26
    bevel.segments = 4
    bevel.harden_normals = True
    normals = obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    normals.keep_sharp = True
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cyl_between(name, p1, p2, radius, mat, vertices=16):
    p1 = Vector(p1)
    p2 = Vector(p2)
    mid = (p1 + p2) * 0.5
    direction = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cone_between(name, p1, p2, radius1, radius2, mat, vertices=16):
    p1 = Vector(p1)
    p2 = Vector(p2)
    mid = (p1 + p2) * 0.5
    direction = p2 - p1
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=direction.length, location=mid)
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
        major_segments=28,
        minor_segments=8,
        location=loc,
        rotation=(math.pi / 2, 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def build_crossbow(spec):
    mats = materials()
    mins = Vector(spec["min"])
    maxs = Vector(spec["max"])
    dims = maxs - mins
    style = spec["style"]
    drawn = spec["drawn"]
    wood = mats["lightwood"] if style == "improved" else mats["wood"]
    limb_mat = mats["metal"] if style == "compound" else wood

    cx = 0.5
    cy = 0.44
    rear_z = 0.18
    front_z = 0.82
    if style == "compound":
        rear_z = 0.16
        front_z = 0.84

    body_loc = point(mins, dims, cx, cy, 0.46)
    body_scale = (dims.x * 0.10, dims.y * 0.42, dims.z * 0.62)
    cube("stock body", body_loc, body_scale, wood)

    rail_loc = point(mins, dims, cx, 0.18, 0.50)
    cube("top rail", rail_loc, (dims.x * 0.052, dims.y * 0.18, dims.z * 0.66), mats["metal"])

    cube("rear cap", point(mins, dims, cx, cy, rear_z), (dims.x * 0.18, dims.y * 0.48, dims.z * 0.10), mats["metal"])
    cube("front block", point(mins, dims, cx, cy, front_z), (dims.x * 0.16, dims.y * 0.50, dims.z * 0.10), mats["metal"])
    cube("grip neck", point(mins, dims, cx, 0.72, 0.30), (dims.x * 0.10, dims.y * 0.34, dims.z * 0.16), wood, rot=(math.radians(-8), 0.0, 0.0))
    cube("pistol grip", point(mins, dims, cx, 0.82, 0.22), (dims.x * 0.12, dims.y * 0.45, dims.z * 0.18), wood, rot=(math.radians(-14), 0.0, 0.0))
    cube("trigger housing", point(mins, dims, cx, 0.65, 0.35), (dims.x * 0.14, dims.y * 0.25, dims.z * 0.10), mats["metal"])
    cube("trigger", point(mins, dims, cx, 0.82, 0.34), (dims.x * 0.035, dims.y * 0.12, dims.z * 0.07), mats["metal"], rot=(math.radians(18), 0.0, 0.0))

    if style == "improved":
        cube("left side brace", point(mins, dims, 0.40, 0.29, 0.52), (dims.x * 0.035, dims.y * 0.12, dims.z * 0.54), mats["metal"])
        cube("right side brace", point(mins, dims, 0.60, 0.29, 0.52), (dims.x * 0.035, dims.y * 0.12, dims.z * 0.54), mats["metal"])
        cube("raised cheek piece", point(mins, dims, cx, 0.62, 0.22), (dims.x * 0.20, dims.y * 0.22, dims.z * 0.10), wood)
        cube("black rear plate", point(mins, dims, cx, 0.20, 0.24), (dims.x * 0.24, dims.y * 0.16, dims.z * 0.045), mats["metal"])
        cube("black nose plate", point(mins, dims, cx, 0.18, 0.88), (dims.x * 0.24, dims.y * 0.16, dims.z * 0.045), mats["metal"])
    elif style == "crude":
        cube("front wrap", point(mins, dims, cx, 0.20, 0.76), (dims.x * 0.22, dims.y * 0.12, dims.z * 0.05), mats["metal"])
        cube("rear wrap", point(mins, dims, cx, 0.22, 0.32), (dims.x * 0.18, dims.y * 0.12, dims.z * 0.05), mats["metal"])
        cube("dark top spine", point(mins, dims, cx, 0.13, 0.56), (dims.x * 0.075, dims.y * 0.12, dims.z * 0.50), mats["metal"])
        cube("side binding left", point(mins, dims, 0.39, 0.30, 0.52), (dims.x * 0.025, dims.y * 0.16, dims.z * 0.46), mats["metal"])
        cube("side binding right", point(mins, dims, 0.61, 0.30, 0.52), (dims.x * 0.025, dims.y * 0.16, dims.z * 0.46), mats["metal"])

    limb_z = 0.82 if style != "compound" else 0.78
    cube("left limb inner", point(mins, dims, 0.33, cy, limb_z), (dims.x * 0.32, dims.y * 0.18, dims.z * 0.055), limb_mat, rot=(0.0, 0.0, math.radians(-5)))
    cube("right limb inner", point(mins, dims, 0.67, cy, limb_z), (dims.x * 0.32, dims.y * 0.18, dims.z * 0.055), limb_mat, rot=(0.0, 0.0, math.radians(5)))
    cube("left limb outer", point(mins, dims, 0.18, cy, limb_z - 0.01), (dims.x * 0.28, dims.y * 0.15, dims.z * 0.045), limb_mat, rot=(0.0, 0.0, math.radians(-10)))
    cube("right limb outer", point(mins, dims, 0.82, cy, limb_z - 0.01), (dims.x * 0.28, dims.y * 0.15, dims.z * 0.045), limb_mat, rot=(0.0, 0.0, math.radians(10)))

    left_tip = point(mins, dims, 0.055 if style != "compound" else 0.08, cy, limb_z - 0.02)
    right_tip = point(mins, dims, 0.945 if style != "compound" else 0.92, cy, limb_z - 0.02)
    latch_z = 0.54 if drawn else 0.72
    latch = point(mins, dims, cx, 0.28, latch_z)
    cord_radius = min(dims.x, dims.y, dims.z) * 0.010
    cyl_between("string left", left_tip, latch, cord_radius, mats["cord"], 6)
    cyl_between("string right", right_tip, latch, cord_radius, mats["cord"], 6)

    if style == "compound":
        pulley_radius = min(dims.x, dims.z) * 0.045
        torus("left pulley", left_tip, pulley_radius, pulley_radius * 0.18, mats["metal"])
        torus("right pulley", right_tip, pulley_radius, pulley_radius * 0.18, mats["metal"])
        cyl_between("compound cable upper", point(mins, dims, 0.11, 0.36, 0.86), point(mins, dims, 0.89, 0.36, 0.86), cord_radius, mats["cord"], 6)
        cyl_between("compound cable lower", point(mins, dims, 0.11, 0.52, 0.73), point(mins, dims, 0.89, 0.52, 0.73), cord_radius, mats["cord"], 6)
        cube("compound center black rail", point(mins, dims, cx, 0.15, 0.55), (dims.x * 0.080, dims.y * 0.15, dims.z * 0.56), mats["metal"])
        cube("compound wood grip panel", point(mins, dims, cx, 0.62, 0.34), (dims.x * 0.18, dims.y * 0.24, dims.z * 0.14), wood)
        cube("compound front clamp", point(mins, dims, cx, 0.19, 0.81), (dims.x * 0.25, dims.y * 0.18, dims.z * 0.06), mats["metal"])
    else:
        cube("left limb dark tip", point(mins, dims, 0.08, cy, limb_z - 0.02), (dims.x * 0.11, dims.y * 0.16, dims.z * 0.050), mats["metal"])
        cube("right limb dark tip", point(mins, dims, 0.92, cy, limb_z - 0.02), (dims.x * 0.11, dims.y * 0.16, dims.z * 0.050), mats["metal"])

    cube("front sight", point(mins, dims, cx, 0.12, 0.90), (dims.x * 0.045, dims.y * 0.12, dims.z * 0.055), mats["metal"])
    cube("rear sight", point(mins, dims, cx, 0.12, 0.42), (dims.x * 0.060, dims.y * 0.11, dims.z * 0.040), mats["metal"])

    if drawn:
        bolt_y = 0.08
        cyl_between("loaded bolt shaft", point(mins, dims, cx, bolt_y, 0.30), point(mins, dims, cx, bolt_y, 0.88), min(dims.x, dims.y, dims.z) * 0.020, wood, 8)
        cone_between("loaded bolt head", point(mins, dims, cx, bolt_y, 0.88), point(mins, dims, cx, bolt_y, 0.97), min(dims.x, dims.y, dims.z) * 0.050, 0.0, mats["point"], 10)

    dz = dims.z * FORWARD_SHIFT
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.location.z += dz


def convert_and_join(mesh_name):
    bpy.ops.object.select_all(action="SELECT")
    for obj in list(bpy.context.selected_objects):
        bpy.context.view_layer.objects.active = obj
        if obj.type == "MESH":
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
    obj.name = mesh_name
    obj.data.name = mesh_name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def assign_atlas_uv(obj):
    uv_layer = obj.data.uv_layers.new(name="UVMap") if not obj.data.uv_layers else obj.data.uv_layers.active
    blocks = {
        "PZC wood": ((0.08, 0.58), (0.42, 0.92)),
        "PZC light wood": ((0.08, 0.58), (0.42, 0.92)),
        "PZC dark metal": ((0.58, 0.58), (0.92, 0.92)),
        "PZC cord": ((0.08, 0.08), (0.42, 0.42)),
        "PZC point": ((0.58, 0.08), (0.92, 0.42)),
    }
    corners = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for poly in obj.data.polygons:
        mat = obj.material_slots[poly.material_index].material
        (u0, v0), (u1, v1) = blocks.get(mat.name, blocks["PZC wood"])
        for n, loop_index in enumerate(poly.loop_indices):
            cu, cv = corners[n % 4]
            uv_layer.data[loop_index].uv = (u0 if cu == 0 else u1, v0 if cv == 0 else v1)


def fit_to_reference_bounds(obj, spec):
    target_min = Vector(spec["min"])
    target_max = Vector(spec["max"])
    target_dim = target_max - target_min
    coords = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    current_min = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
    current_max = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
    current_dim = current_max - current_min

    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        ratios = []
        for axis in range(3):
            dim = current_dim[axis]
            ratios.append(0.5 if abs(dim) < 1e-12 else (world[axis] - current_min[axis]) / dim)
        fitted = Vector((
            target_min.x + ratios[0] * target_dim.x,
            target_min.y + ratios[1] * target_dim.y,
            target_min.z + ratios[2] * target_dim.z,
        ))
        vertex.co = fitted


def match_reference_transform(obj, spec):
    target = Matrix.LocRotScale(
        Vector((0.0, 0.0, 0.0)),
        Euler(spec["rotation"], "XYZ"),
        Vector(spec["scale"]),
    )
    inv = target.inverted()
    for vert in obj.data.vertices:
        world = obj.matrix_world @ vert.co
        vert.co = inv @ world
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = spec["rotation"]
    obj.scale = spec["scale"]
    return obj


def export_fbx(name, spec):
    out = OUT_DIR / name
    obj = convert_and_join(spec["mesh"])
    assign_atlas_uv(obj)
    fit_to_reference_bounds(obj, spec)
    match_reference_transform(obj, spec)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(out),
        use_selection=True,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_space_transform=False,
        apply_unit_scale=True,
        path_mode="AUTO",
    )
    print(f"exported {out}")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    write_atlas("CrossBow.png", compound=False)
    write_atlas("CompoundCrossBow.png", compound=True)
    for name, spec in SPECS.items():
        clear()
        build_crossbow(spec)
        export_fbx(name, spec)


if __name__ == "__main__":
    main()
