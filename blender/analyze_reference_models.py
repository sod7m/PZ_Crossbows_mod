import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
REFERENCE_DIR = ROOT / "reference"
OUTPUT = ROOT / "reference_metrics.json"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_fbx(path):
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path))
    bpy.context.view_layer.update()


def object_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(c[i] for c in corners) for i in range(3)],
        "max": [max(c[i] for c in corners) for i in range(3)],
    }


def merge_bounds(bounds):
    mins = [min(bound["min"][i] for bound in bounds) for i in range(3)]
    maxs = [max(bound["max"][i] for bound in bounds) for i in range(3)]
    return {
        "min": mins,
        "max": maxs,
        "size": [maxs[i] - mins[i] for i in range(3)],
        "center": [(maxs[i] + mins[i]) / 2 for i in range(3)],
    }


def main():
    metrics = {}
    for path in sorted(REFERENCE_DIR.glob("*.fbx")):
        import_fbx(path)
        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        bounds = [object_bounds(obj) for obj in mesh_objects]
        metrics[path.name] = {
            "objects": [
                {
                    "name": obj.name,
                    "type": obj.type,
                    "location": list(obj.location),
                    "rotation_euler": list(obj.rotation_euler),
                    "scale": list(obj.scale),
                    "dimensions": list(obj.dimensions),
                    "bounds": object_bounds(obj),
                    "vertices": len(obj.data.vertices),
                    "polygons": len(obj.data.polygons),
                }
                for obj in mesh_objects
            ],
            "bounds": merge_bounds(bounds) if bounds else None,
        }
    OUTPUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
