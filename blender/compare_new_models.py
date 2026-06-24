import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
METRICS = json.loads((ROOT / "reference_metrics.json").read_text(encoding="utf-8"))
NEW_DIR = ROOT / "newModels"
OUTPUT = ROOT / "new_model_metrics.json"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_fbx(path):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path))
    bpy.context.view_layer.update()


def mesh_bounds():
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


def rel_delta(new, ref):
    return [0 if abs(ref[i]) < 1e-12 else (new[i] - ref[i]) / ref[i] for i in range(3)]


def main():
    report = {}
    for path in sorted(NEW_DIR.glob("*.fbx")):
        if path.name not in METRICS:
            continue
        import_fbx(path)
        new_bounds = mesh_bounds()
        ref_bounds = METRICS[path.name]["bounds"]
        report[path.name] = {
            "new": new_bounds,
            "reference": ref_bounds,
            "size_delta_ratio": rel_delta(new_bounds["size"], ref_bounds["size"]),
            "center_delta": [new_bounds["center"][i] - ref_bounds["center"][i] for i in range(3)],
        }
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for name, data in report.items():
        print(name)
        print("  size_delta_ratio", [round(v, 4) for v in data["size_delta_ratio"]])
        print("  center_delta", [round(v, 8) for v in data["center_delta"]])


if __name__ == "__main__":
    main()
