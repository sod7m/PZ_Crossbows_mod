import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
NEW_DIR = ROOT / "newModels"
METRICS = json.loads((ROOT / "reference_metrics.json").read_text(encoding="utf-8"))
FILES = [
    "CompoundCrossBow.fbx",
    "CompoundCrossBowDrawn.fbx",
    "CrossBow.fbx",
    "CrossBowDrawn.fbx",
    "HandCrossBow.fbx",
    "HandCrossBowDrawn.fbx",
    "ImprovedCrossBow.fbx",
    "ImprovedCrossBowDrawn.fbx",
]


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_fbx(path):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path))
    bpy.context.view_layer.update()
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    mins = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maxs = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return mins, maxs, maxs - mins


def fit(obj, target):
    target_min = Vector(target["min"])
    target_size = Vector(target["size"])
    source_min, _source_max, source_size = bounds(obj)
    for vertex in obj.data.vertices:
        co = vertex.co.copy()
        ratios = []
        for axis in range(3):
            if abs(source_size[axis]) < 1e-12:
                ratios.append(0.5)
            else:
                ratios.append((co[axis] - source_min[axis]) / source_size[axis])
        vertex.co = Vector((
            target_min.x + ratios[0] * target_size.x,
            target_min.y + ratios[1] * target_size.y,
            target_min.z + ratios[2] * target_size.z,
        ))
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)


def export_fbx(path, obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_space_transform=False,
        apply_unit_scale=True,
        path_mode="AUTO",
    )


def main():
    for name in FILES:
        path = NEW_DIR / name
        obj = import_fbx(path)
        fit(obj, METRICS[name]["bounds"])
        export_fbx(path, obj)
        print(f"post-fitted {name}")


if __name__ == "__main__":
    main()
