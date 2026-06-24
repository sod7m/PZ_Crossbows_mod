from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
REF_DIR = ROOT / "reference"
NEW_DIR = ROOT / "newModels"


CROSSBOW_FILES = {
    "CrossBow.fbx",
    "CrossBowDrawn.fbx",
    "ImprovedCrossBow.fbx",
    "ImprovedCrossBowDrawn.fbx",
    "CompoundCrossBow.fbx",
    "CompoundCrossBowDrawn.fbx",
    "HandCrossBow.fbx",
    "HandCrossBowDrawn.fbx",
}

BOLT_FILES = {
    "WoodBolt.fbx",
    "ShortWoodBolt.fbx",
    "WoodBoltBroken.fbx",
}

GEOMETRY_SCALE = {
    "CompoundCrossBow.fbx": 0.78,
    "CompoundCrossBowDrawn.fbx": 0.78,
    "CrossBow.fbx": 0.66,
    "CrossBowDrawn.fbx": 0.66,
    "ImprovedCrossBow.fbx": 0.66,
    "ImprovedCrossBowDrawn.fbx": 0.66,
    "HandCrossBow.fbx": 0.72,
    "HandCrossBowDrawn.fbx": 0.72,
    "WoodBolt.fbx": 1.0,
    "ShortWoodBolt.fbx": 1.0,
    "WoodBoltBroken.fbx": 0.85,
}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_fbx(path):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh objects imported from {path}")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def bbox(obj):
    coords = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    mins = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
    maxs = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
    return mins, maxs, maxs - mins


def safe_ratio(value, min_value, dim):
    if abs(dim) < 1e-12:
        return 0.5
    return (value - min_value) / dim


def fit_object_to_reference(obj, ref_min, ref_dim, mode, filename):
    new_min, _new_max, new_dim = bbox(obj)
    ref_center = ref_min + ref_dim * 0.5
    shrink = GEOMETRY_SCALE.get(filename, 1.0)

    for vertex in obj.data.vertices:
        co = vertex.co.copy()

        if mode == "crossbow":
            rx = safe_ratio(co.x, new_min.x, new_dim.x)
            ry = safe_ratio(co.z, new_min.z, new_dim.z)
            rz = 1.0 - safe_ratio(co.y, new_min.y, new_dim.y)
        elif mode == "bolt":
            rx = safe_ratio(co.y, new_min.y, new_dim.y)
            ry = safe_ratio(co.x, new_min.x, new_dim.x)
            rz = safe_ratio(co.z, new_min.z, new_dim.z)
        else:
            raise ValueError(mode)

        fitted = Vector((
            ref_min.x + rx * ref_dim.x,
            ref_min.y + ry * ref_dim.y,
            ref_min.z + rz * ref_dim.z,
        ))
        fitted = ref_center + (fitted - ref_center) * shrink
        vertex.co = fitted

    obj.name = "PZC_Model"
    obj.data.name = "PZC_ModelMesh"
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)


def export_selected(path, obj):
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


def fit_file(filename, mode):
    ref_obj = import_fbx(REF_DIR / filename)
    ref_min, _ref_max, ref_dim = bbox(ref_obj)

    obj = import_fbx(NEW_DIR / filename)
    fit_object_to_reference(obj, ref_min, ref_dim, mode, filename)
    export_selected(NEW_DIR / filename, obj)
    print(f"fitted {filename} as {mode}")


def main():
    for filename in sorted(CROSSBOW_FILES):
        fit_file(filename, "crossbow")
    for filename in sorted(BOLT_FILES):
        fit_file(filename, "bolt")


if __name__ == "__main__":
    main()
