import bpy
import bmesh
import math
import mathutils
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh

REF_X = "E:/PZCrossbows/work/reference/models/Bob_AmmoStrap.x"
OUT_DIR = "E:/PZCrossbows/work/InWork"

bpy.ops.wm.read_factory_settings(use_empty=True)

ref = parse_mesh(REF_X)

# ---- Strap: the REAL reference bandolier loop, mirrored from chest to back ----
# original convention: x = left/right, y = height, z = depth (negative = front)
# blender convention here: X = left/right, Y = depth (positive = behind body), Z = height
strap_verts = []
for (ox, oy, oz) in ref["verts"]:
    strap_verts.append((ox, oz, oy))  # mirror depth -> sits on the back instead of chest

strap_faces = [tuple(f) for f in ref["faces"]]

strap_mesh = bpy.data.meshes.new("QuiverStrap")
strap_mesh.from_pydata(strap_verts, [], strap_faces)
strap_mesh.update()
strap_obj = bpy.data.objects.new("QuiverStrap", strap_mesh)
bpy.context.scene.collection.objects.link(strap_obj)

xs = [v[0] for v in strap_verts]
ys = [v[1] for v in strap_verts]
zs = [v[2] for v in strap_verts]
print(f"Strap bbox X {min(xs):.4f}..{max(xs):.4f}  Y {min(ys):.4f}..{max(ys):.4f}  Z {min(zs):.4f}..{max(zs):.4f}")

# find the strap vertex with the greatest Z (highest point of the loop, near the
# shoulder) - that's where the quiver pouch will attach.
top_idx = max(range(len(strap_verts)), key=lambda i: strap_verts[i][2])
attach_point = mathutils.Vector(strap_verts[top_idx])
back_depth = max(ys)
print("attach point (top of loop):", attach_point)

# ---- Quiver pouch: an ELONGATED container (not a short wide cone), roughly
# vertical along the back, its base attached at the strap loop's top point ----
pouch_length = 0.55
r_bottom = 0.05
r_top = 0.065

pouch_base = attach_point + mathutils.Vector((0.01, back_depth * 0.35, -0.015))
# slight lean outward/up over the shoulder
lean_x = math.radians(10)
lean_y = math.radians(-14)
axis_dir = mathutils.Vector((math.sin(lean_x), math.sin(lean_y), math.cos(lean_x) * math.cos(lean_y))).normalized()
pouch_top = pouch_base + axis_dir * pouch_length

bm = bmesh.new()
bmesh.ops.create_cone(
    bm, cap_ends=True, cap_tris=False, segments=12,
    radius1=r_bottom, radius2=r_top, depth=pouch_length,
)
z_axis = mathutils.Vector((0, 0, 1))
quat = z_axis.rotation_difference(axis_dir)
for v in bm.verts:
    v.co = quat @ v.co
center = pouch_base + axis_dir * (pouch_length * 0.5)
for v in bm.verts:
    v.co += center
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
pouch_mesh = bpy.data.meshes.new("QuiverPouch")
bm.to_mesh(pouch_mesh)
bm.free()
pouch_obj = bpy.data.objects.new("QuiverPouch", pouch_mesh)
bpy.context.scene.collection.objects.link(pouch_obj)

print("pouch base", pouch_base, "pouch top", pouch_top)


# ---- Bolts poking out of the pouch opening ----
def make_bolt(name, origin, direction, length, shaft_r):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=shaft_r, radius2=shaft_r, depth=length,
    )
    tip_len = length * 0.16
    result = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=shaft_r * 1.4, radius2=0.0, depth=tip_len,
    )
    for v in result["verts"]:
        v.co.z += length / 2 + tip_len / 2

    fletch_len = length * 0.22
    fletch_h = shaft_r * 5.0
    base_z = -length / 2 + fletch_len / 2
    for ang in (0, math.pi / 2, math.pi, math.pi * 1.5):
        nx, ny = math.cos(ang), math.sin(ang)
        v0 = bm.verts.new((0, 0, base_z - fletch_len / 2))
        v1 = bm.verts.new((nx * fletch_h, ny * fletch_h, base_z))
        v2 = bm.verts.new((0, 0, base_z + fletch_len / 2))
        bm.faces.new((v0, v1, v2))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    z_axis = mathutils.Vector((0, 0, 1))
    dirn = mathutils.Vector(direction).normalized()
    q = z_axis.rotation_difference(dirn)
    obj.rotation_euler = q.to_euler()
    obj.location = origin
    return obj


bolt_length = 0.30
offsets = [(-0.02, 0.0), (0.016, 0.010), (0.005, -0.018), (-0.004, 0.018)]
perp1 = axis_dir.cross(mathutils.Vector((0, 0, 1)))
if perp1.length < 0.01:
    perp1 = mathutils.Vector((1, 0, 0))
perp1.normalize()
perp2 = axis_dir.cross(perp1).normalized()

bolt_objs = []
for i, (ox, oy) in enumerate(offsets):
    origin = pouch_top + perp1 * ox + perp2 * oy - axis_dir * (bolt_length * 0.30)
    b = make_bolt(f"Bolt{i}", origin, axis_dir, bolt_length, 0.008)
    bolt_objs.append(b)

# ---- materials ----
def flat_mat(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m

leather_mat = flat_mat("Leather", (0.28, 0.17, 0.095))
wood_mat = flat_mat("Wood", (0.45, 0.30, 0.15))
fletch_mat = flat_mat("Fletch", (0.85, 0.15, 0.12))

strap_obj.data.materials.append(leather_mat)
pouch_obj.data.materials.append(leather_mat)
for b in bolt_objs:
    b.data.materials.append(wood_mat)
    b.data.materials.append(fletch_mat)
    n = len(b.data.polygons)
    for poly in b.data.polygons[max(0, n - 4):]:
        poly.material_index = 1

# ---- camera framing on combined bbox ----
all_objs = [strap_obj, pouch_obj] + bolt_objs
allx, ally, allz = [], [], []
for o in all_objs:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        allx.append(w.x); ally.append(w.y); allz.append(w.z)
cx2 = (min(allx) + max(allx)) / 2
cy2 = (min(ally) + max(ally)) / 2
cz2 = (min(allz) + max(allz)) / 2
size = max(max(allx) - min(allx), max(ally) - min(ally), max(allz) - min(allz))
print("combined bbox center", cx2, cy2, cz2, "size", size)

sun = bpy.data.objects.new("Sun1", bpy.data.lights.new("Sun1", type='SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(55), 0, math.radians(35))
bpy.context.scene.collection.objects.link(sun)
sun2 = bpy.data.objects.new("Sun2", bpy.data.lights.new("Sun2", type='SUN'))
sun2.data.energy = 1.4
sun2.rotation_euler = (math.radians(110), 0, math.radians(210))
bpy.context.scene.collection.objects.link(sun2)

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.58, 1)
bpy.context.scene.world = world


def add_camera(name, offset):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam_pos = mathutils.Vector((cx2, cy2, cz2)) + offset
    cam.location = cam_pos
    direction = mathutils.Vector((cx2, cy2, cz2)) - cam_pos
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return cam


dist = size * 1.6
cams = {
    "back_3q": add_camera("Cam1", mathutils.Vector((dist * 0.55, dist * 0.95, dist * 0.35))),
    "back_flat": add_camera("Cam2", mathutils.Vector((0, dist * 1.3, 0))),
    "side": add_camera("Cam3", mathutils.Vector((dist * 1.3, 0, dist * 0.1))),
}

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900

for name, cam in cams.items():
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT_DIR, f"quiver_v3_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "quiver_v3.blend"))
print("DONE")
