"""Generate original crossbow-bolt world models (WoodBolt / ShortWoodBolt /
WoodBoltBroken) fitted into each reference bolt's world box, written into the
reference object's local space so models.txt keeps placing them correctly.

Run: blender --background --python generate_bolts.py -- <out_dir>
"""
import bmesh
import bpy
import math
import sys
from mathutils import Vector
from pathlib import Path

ROOT = Path(r"E:/PZCrossbows/blender")
REF = ROOT / "reference"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else (ROOT / "newModels")
OUT.mkdir(parents=True, exist_ok=True)

MODELS = {
    "WoodBolt.fbx": "full",
    "ShortWoodBolt.fbx": "full",
    "WoodBoltBroken.fbx": "broken",
}
PARTS = []


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)


def world_bounds(obj):
    p = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = Vector((min(x.x for x in p), min(x.y for x in p), min(x.z for x in p)))
    mx = Vector((max(x.x for x in p), max(x.y for x in p), max(x.z for x in p)))
    return mn, mx, mx - mn


def mat(name, color):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = color
    return m


def _finish(o, material):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.clear()
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = True
    PARTS.append(o)
    return o


def cyl(p1, p2, r, material, verts=10):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length,
                                        location=(p1 + p2) * 0.5)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return _finish(o, material)


def cone(p1, p2, r1, r2, material, verts=10):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length,
                                    location=(p1 + p2) * 0.5)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return _finish(o, material)


def vane(center, dx, dy, dz, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=rot)
    o = bpy.context.object
    o.dimensions = (dx, dy, dz)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, material)


def build_bolt(mn, size, kind):
    wood = mat("BOLT_wood", (0.42, 0.24, 0.11, 1))
    tip = mat("BOLT_tip", (0.30, 0.19, 0.09, 1))     # sharpened, darker wood
    feather = mat("BOLT_feather", (0.14, 0.10, 0.07, 1))
    cy = mn.y + size.y * 0.5
    cz = mn.z + size.z * 0.5
    x0 = mn.x
    x1 = mn.x + size.x
    r = min(size.y, size.z) * 0.30
    if kind == "broken":
        # bent, snapped shaft: rises in Y; splintered break in the middle
        bx = x0 + size.x * 0.52          # break point along X
        y_top = mn.y + size.y * 0.86
        p_a = Vector((x0, cy, cz))
        p_b = Vector((bx, cy, cz))
        p_c = Vector((x1, y_top, cz))
        cyl(p_a, p_b, r, wood, 8)
        cone(p_b, (bx + size.x * 0.10, cy + size.y * 0.18, cz), r, r * 0.2, tip, 6)  # splinter
        cyl((bx + size.x * 0.06, cy + size.y * 0.10, cz), p_c, r, wood, 8)
        cone(p_c, (x1 + size.x * 0.02, y_top + size.y * 0.05, cz), r, r * 0.2, tip, 6)
        # a couple of fletch vanes near the low end
        vane((x0 + size.x * 0.10, cy, cz), size.x * 0.14, r * 0.4, r * 3.2, feather)
        return
    # full / short: shaft + sharpened point + nock + fletching
    point_len = size.x * 0.16
    fletch_len = size.x * 0.10
    cyl((x0 + fletch_len * 0.4, cy, cz), (x1 - point_len, cy, cz), r, wood, 10)
    cone((x1 - point_len, cy, cz), (x1, cy, cz), r * 1.05, 0.0, tip, 10)
    # nock collar
    cyl((x0 + fletch_len * 0.2, cy, cz), (x0 + fletch_len * 0.5, cy, cz), r * 1.25, wood, 8)
    # notch/nock end
    cyl((x0, cy, cz), (x0 + fletch_len * 0.2, cy, cz), r * 0.8, wood, 6)
    # two fletching vanes (vertical + horizontal)
    fx = x0 + fletch_len * 0.9
    vane((fx, cy, cz), size.x * 0.14, r * 0.35, r * 3.4, feather)
    vane((fx, cy, cz), size.x * 0.14, r * 3.4, r * 0.35, feather)


def combine():
    objs = list(PARTS)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.convert(target="MESH")
        except RuntimeError:
            pass
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def planar_uv(o):
    me = o.data
    uv = me.uv_layers.new(name="UV")
    vs = [v.co for v in me.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    sz = mx - mn

    def region(n):
        n = n.lower()
        if "feather" in n:
            return (0.02, 0.52, 0.48, 0.98)
        if "tip" in n:
            return (0.52, 0.52, 0.98, 0.98)
        return (0.02, 0.02, 0.98, 0.48)  # wood spans wide

    for poly in me.polygons:
        m = me.materials[poly.material_index] if poly.material_index < len(me.materials) else None
        u0, v0, u1, v1 = region(m.name if m else "wood")
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            fu = (co.x - mn.x) / sz.x if sz.x else 0.5
            fv = (co.y - mn.y) / sz.y if sz.y else 0.5
            uv.data[li].uv = (u0 + (u1 - u0) * fu, v0 + (v1 - v0) * fv)


def export_one(fname, kind):
    clear()
    PARTS.clear()
    bpy.ops.import_scene.fbx(filepath=str(REF / fname))
    ref = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    ref_matrix = ref.matrix_world.copy()
    mn, mx, size = world_bounds(ref)
    build_bolt(mn, size, kind)
    new = combine()
    inv = ref_matrix.inverted()
    for v in new.data.vertices:
        v.co = inv @ v.co
    new.matrix_world = ref_matrix
    new.name = "PZC_" + fname.replace(".fbx", "")
    planar_uv(new)
    bpy.ops.object.select_all(action="DESELECT")
    new.select_set(True)
    bpy.context.view_layer.objects.active = new
    bpy.ops.export_scene.fbx(filepath=str(OUT / fname), use_selection=True,
                             object_types={"MESH"}, add_leaf_bones=False,
                             bake_space_transform=False, apply_unit_scale=True, path_mode="AUTO")
    print(f"exported {fname} target={[round(a,3) for a in size]}")


def main():
    only = [a for a in argv[1:] if a.endswith(".fbx")]
    for fname, kind in MODELS.items():
        if only and fname not in only:
            continue
        export_one(fname, kind)
    print("ALL DONE")


if __name__ == "__main__":
    main()
