from mathutils import Vector

import bpy


PATHS = [
    ("ref CrossBow", "E:/PZCrossbows/blender/reference/CrossBow.fbx"),
    ("new CrossBow", "E:/PZCrossbows/blender/newModels/CrossBow.fbx"),
    ("mod CrossBow", "E:/PZCrossbows/PZCrossbows/Contents/mods/PZCrossbows/42/media/models_x/weapons/firearm/CrossBow.fbx"),
    ("ref Improved", "E:/PZCrossbows/blender/reference/ImprovedCrossBow.fbx"),
    ("new Improved", "E:/PZCrossbows/blender/newModels/ImprovedCrossBow.fbx"),
    ("ref Compound", "E:/PZCrossbows/blender/reference/CompoundCrossBow.fbx"),
    ("new Compound", "E:/PZCrossbows/blender/newModels/CompoundCrossBow.fbx"),
]


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def scene_bounds():
    points = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    mins = [min(point[i] for point in points) for i in range(3)]
    maxs = [max(point[i] for point in points) for i in range(3)]
    return {
        "min": mins,
        "max": maxs,
        "size": [maxs[i] - mins[i] for i in range(3)],
        "center": [(maxs[i] + mins[i]) / 2 for i in range(3)],
    }


def rounded(values):
    return [round(value, 8) for value in values]


for label, path in PATHS:
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    bpy.context.view_layer.update()
    print(f"\n{label}")
    for obj in [o for o in bpy.context.scene.objects if o.type == "MESH"][:3]:
        print(" obj", obj.name)
        print("   loc", rounded(obj.location))
        print("   rot", rounded(obj.rotation_euler))
        print("   scale", rounded(obj.scale))
        print("   dims", rounded(obj.dimensions))
    data = scene_bounds()
    print(" bounds size", rounded(data["size"]))
    print(" bounds center", rounded(data["center"]))
