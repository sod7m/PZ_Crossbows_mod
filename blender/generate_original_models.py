import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "newModels"
OUT_DIR.mkdir(exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def setup_materials():
    return {
        "dark_wood": material("PZC dark stained wood", (0.22, 0.12, 0.055, 1.0)),
        "pale_wood": material("PZC pale carved wood", (0.48, 0.31, 0.16, 1.0)),
        "metal": material("PZC dull blackened metal", (0.06, 0.065, 0.07, 1.0)),
        "cord": material("PZC waxed cord", (0.015, 0.012, 0.01, 1.0)),
        "bone": material("PZC stone bone point", (0.58, 0.55, 0.48, 1.0)),
        "wrap": material("PZC cloth wrap", (0.28, 0.24, 0.18, 1.0)),
    }


def cube(name, loc, scale, mat=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    bevel = obj.modifiers.new("small softened edges", "BEVEL")
    bevel.width = min(scale) * 0.10
    bevel.segments = 1
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def cylinder_between(name, p1, p2, radius, mat=None, vertices=10):
    p1 = Vector(p1)
    p2 = Vector(p2)
    mid = (p1 + p2) * 0.5
    direction = p2 - p1
    length = direction.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    if mat:
        obj.data.materials.append(mat)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def cone_between(name, p1, p2, r1, r2, mat=None, vertices=12):
    p1 = Vector(p1)
    p2 = Vector(p2)
    mid = (p1 + p2) * 0.5
    direction = p2 - p1
    length = direction.length
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    if mat:
        obj.data.materials.append(mat)
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def pulley(name, loc, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.010, major_segments=18, minor_segments=6, location=loc, rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def fin(name, loc, scale, mat, side=1):
    return cube(name, loc, scale, mat, rot=(0, 0, side * math.radians(22)))


def create_bolt(name, short=False, broken=False, mats=None):
    length = 0.62 if short else 0.92
    if broken:
        cylinder_between(name + " splinter A", (0, -length * 0.20, 0), (0.03, length * 0.16, 0.02), 0.012, mats["pale_wood"], 8)
        cylinder_between(name + " splinter B", (-0.035, -length * 0.08, -0.01), (-0.02, length * 0.30, 0.015), 0.009, mats["pale_wood"], 7)
        cone_between(name + " chipped point", (0.03, length * 0.16, 0.02), (0.09, length * 0.25, 0.02), 0.025, 0.0, mats["bone"], 8)
        cube(name + " torn wrap", (0.0, -length * 0.18, 0.0), (0.055, 0.060, 0.020), mats["wrap"], rot=(0.2, 0.0, 0.8))
        return
    cylinder_between(name + " shaft", (0, -length * 0.45, 0), (0, length * 0.36, 0), 0.012 if short else 0.014, mats["pale_wood"], 10)
    cone_between(name + " stone head", (0, length * 0.36, 0), (0, length * 0.48, 0), 0.035 if not short else 0.028, 0.0, mats["bone"], 12)
    base_y = -length * 0.38
    fin(name + " fletch left", (-0.028, base_y, 0.0), (0.006, 0.115 if not short else 0.085, 0.036), mats["wrap"], 1)
    fin(name + " fletch right", (0.028, base_y, 0.0), (0.006, 0.115 if not short else 0.085, 0.036), mats["wrap"], -1)
    fin(name + " fletch top", (0.0, base_y, 0.030), (0.036, 0.115 if not short else 0.085, 0.006), mats["wrap"], 0)


def create_crossbow(name, style, drawn=False, mats=None):
    is_hand = style == "hand"
    is_compound = style == "compound"
    is_improved = style == "improved"

    stock_len = 0.62 if is_hand else 1.05
    body_mat = mats["dark_wood"] if not is_improved else mats["pale_wood"]
    front_y = stock_len * 0.32
    back_y = -stock_len * 0.42

    cube(name + " angular stock", (0, -0.12 if not is_hand else -0.03, -0.02), (0.12 if not is_hand else 0.095, stock_len, 0.070), body_mat)
    cube(name + " top rail", (0, 0.02 if not is_hand else 0.05, 0.055), (0.060 if not is_hand else 0.045, stock_len * 0.86, 0.035), mats["metal"])
    cube(name + " trigger guard", (0, back_y + 0.12, -0.090), (0.085, 0.020, 0.105), mats["metal"], rot=(0.25, 0, 0))
    cube(name + " grip", (0, back_y + 0.03, -0.135), (0.075, 0.135, 0.095), body_mat, rot=(math.radians(-14), 0, 0))

    if is_hand:
        cube(name + " stub foregrip", (0, front_y - 0.10, -0.075), (0.070, 0.075, 0.085), body_mat)
    else:
        cube(name + " shoulder notch", (0, back_y - 0.06, -0.015), (0.150, 0.080, 0.090), body_mat)

    span = 0.66 if is_hand else (1.18 if is_compound else 0.98)
    limb_z = 0.030 if not is_hand else 0.040
    limb_mat = mats["metal"] if is_compound else body_mat
    cube(name + " left swept limb", (-span * 0.24, front_y, limb_z), (span * 0.52, 0.035, 0.040), limb_mat, rot=(0, 0, math.radians(10)))
    cube(name + " right swept limb", (span * 0.24, front_y, limb_z), (span * 0.52, 0.035, 0.040), limb_mat, rot=(0, 0, math.radians(-10)))
    cube(name + " center limb block", (0, front_y, limb_z), (0.115, 0.060, 0.065), mats["metal"])

    if is_compound:
        pulley(name + " left pulley", (-span * 0.52, front_y + 0.02, limb_z), mats["metal"])
        pulley(name + " right pulley", (span * 0.52, front_y + 0.02, limb_z), mats["metal"])
        cylinder_between(name + " compound cable lower", (-span * 0.52, front_y + 0.02, limb_z - 0.02), (span * 0.52, front_y + 0.02, limb_z - 0.02), 0.004, mats["cord"], 6)
        cylinder_between(name + " compound cable upper", (-span * 0.46, front_y + 0.04, limb_z + 0.035), (span * 0.46, front_y + 0.04, limb_z + 0.035), 0.004, mats["cord"], 6)
    else:
        string_y = back_y + 0.18 if drawn else front_y - 0.06
        cylinder_between(name + " bow string left", (-span * 0.49, front_y + 0.01, limb_z), (0, string_y, limb_z + 0.005), 0.0045, mats["cord"], 6)
        cylinder_between(name + " bow string right", (span * 0.49, front_y + 0.01, limb_z), (0, string_y, limb_z + 0.005), 0.0045, mats["cord"], 6)

    if drawn:
        bolt_len = 0.46 if is_hand else 0.74
        cylinder_between(name + " loaded bolt shaft", (0, -0.16 if not is_hand else -0.05, 0.090), (0, bolt_len * 0.55, 0.090), 0.009, mats["pale_wood"], 8)
        cone_between(name + " loaded bolt head", (0, bolt_len * 0.55, 0.090), (0, bolt_len * 0.67, 0.090), 0.026, 0.0, mats["bone"], 10)
        cube(name + " cocked latch", (0, -0.23 if not is_hand else -0.12, 0.072), (0.070, 0.035, 0.035), mats["metal"])
    else:
        cube(name + " empty latch", (0, -0.03 if not is_hand else 0.01, 0.070), (0.060, 0.025, 0.025), mats["metal"])

    if is_improved:
        cube(name + " side brace left", (-0.055, 0.03, 0.015), (0.018, stock_len * 0.66, 0.030), mats["metal"])
        cube(name + " side brace right", (0.055, 0.03, 0.015), (0.018, stock_len * 0.66, 0.030), mats["metal"])
    if style == "crude":
        cube(name + " raw binding front", (0, front_y - 0.04, 0.075), (0.150, 0.026, 0.022), mats["wrap"])
        cube(name + " raw binding rear", (0, -0.19, 0.066), (0.120, 0.024, 0.020), mats["wrap"])


def convert_modifiers():
    bpy.ops.object.select_all(action="SELECT")
    for obj in list(bpy.context.selected_objects):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.convert(target="MESH")
        except RuntimeError:
            pass


def export_model(filename):
    convert_modifiers()
    bpy.ops.object.select_all(action="SELECT")
    out = OUT_DIR / filename
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


def make_file(filename, builder):
    clear_scene()
    mats = setup_materials()
    builder(mats)
    export_model(filename)


def main():
    jobs = {
        "CrossBow.fbx": lambda m: create_crossbow("PZC crude", "crude", False, m),
        "CrossBowDrawn.fbx": lambda m: create_crossbow("PZC crude drawn", "crude", True, m),
        "ImprovedCrossBow.fbx": lambda m: create_crossbow("PZC improved", "improved", False, m),
        "ImprovedCrossBowDrawn.fbx": lambda m: create_crossbow("PZC improved drawn", "improved", True, m),
        "CompoundCrossBow.fbx": lambda m: create_crossbow("PZC compound", "compound", False, m),
        "CompoundCrossBowDrawn.fbx": lambda m: create_crossbow("PZC compound drawn", "compound", True, m),
        "HandCrossBow.fbx": lambda m: create_crossbow("PZC hand", "hand", False, m),
        "HandCrossBowDrawn.fbx": lambda m: create_crossbow("PZC hand drawn", "hand", True, m),
        "WoodBolt.fbx": lambda m: create_bolt("PZC wood bolt", False, False, m),
        "ShortWoodBolt.fbx": lambda m: create_bolt("PZC short bolt", True, False, m),
        "WoodBoltBroken.fbx": lambda m: create_bolt("PZC broken bolt", False, True, m),
    }
    for filename, builder in jobs.items():
        make_file(filename, builder)


if __name__ == "__main__":
    main()
