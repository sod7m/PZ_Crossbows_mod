import bpy
import bmesh
import math
import mathutils
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh

REF_STRAP = "E:/PZCrossbows/work/reference/models/Bob_AmmoStrap.x"
REF_BODY = "E:/PZCrossbows/work/reference/models/MaleBody.x"
OUT_DIR = "E:/PZCrossbows/work/InWork"

bpy.ops.wm.read_factory_settings(use_empty=True)


def to_blender(verts):
    # original convention: x=left/right, y=height, z=depth(negative=front)
    # blender here: X=left/right, Y=depth(positive=behind), Z=height
    return [(ox, oz, oy) for (ox, oy, oz) in verts]


# ---- Body (scale/placement reference only) ----
body = parse_mesh(REF_BODY)
body_verts = to_blender(body["verts"])
body_faces = [tuple(f) for f in body["faces"]]
body_mesh = bpy.data.meshes.new("Body")
body_mesh.from_pydata(body_verts, [], body_faces)
body_mesh.update()
body_obj = bpy.data.objects.new("Body", body_mesh)
bpy.context.scene.collection.objects.link(body_obj)

bxs = [v[0] for v in body_verts]; bys = [v[1] for v in body_verts]; bzs = [v[2] for v in body_verts]
print(f"Body bbox X {min(bxs):.3f}..{max(bxs):.3f} Y {min(bys):.3f}..{max(bys):.3f} Z {min(bzs):.3f}..{max(bzs):.3f}")

# ---- Strap (real bandolier loop, mirrored to the back) ----
ref = parse_mesh(REF_STRAP)
strap_verts = to_blender(ref["verts"])
strap_faces = [tuple(f) for f in ref["faces"]]
strap_mesh = bpy.data.meshes.new("QuiverStrap")
strap_mesh.from_pydata(strap_verts, [], strap_faces)
strap_mesh.update()
strap_obj = bpy.data.objects.new("QuiverStrap", strap_mesh)
bpy.context.scene.collection.objects.link(strap_obj)

sxs = [v[0] for v in strap_verts]; sys_ = [v[1] for v in strap_verts]; szs = [v[2] for v in strap_verts]
print(f"Strap bbox X {min(sxs):.3f}..{max(sxs):.3f} Y {min(sys_):.3f}..{max(sys_):.3f} Z {min(szs):.3f}..{max(szs):.3f}")


# attach the quiver where the strap actually crosses the back (the most rearward
# point of the loop, roughly mid-torso), NOT at the shoulder/neck.
back_idx = max(range(len(strap_verts)), key=lambda i: strap_verts[i][1])
attach_point = mathutils.Vector(strap_verts[back_idx])
back_depth = max(sys_)
print("attach point (mid-back, on the strap):", attach_point)

# ---- Elongated quiver pouch, leaning up along the back, base at strap top ----
pouch_length = 0.24
r_bottom = 0.032
r_top = 0.042

pouch_base = attach_point + mathutils.Vector((0.02, 0.015, -0.01))  # right against the strap, mid-back
lean_x = math.radians(6)   # nearly straight up, hugging the spine/back
lean_y = math.radians(9)   # slight backward lean so it clears the back curve as it rises
axis_dir = mathutils.Vector((math.sin(lean_x), math.sin(lean_y), math.cos(lean_x) * math.cos(lean_y))).normalized()
pouch_top = pouch_base + axis_dir * pouch_length
print("pouch base", pouch_base, "top", pouch_top, "axis", axis_dir)

bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=r_bottom, radius2=r_top, depth=pouch_length)
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


def make_bolt(name, origin, direction, length, shaft_r):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=shaft_r, radius2=shaft_r, depth=length)
    tip_len = length * 0.16
    result = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=shaft_r * 1.4, radius2=0.0, depth=tip_len)
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


bolt_length = 0.15
offsets = [(-0.013, 0.0), (0.011, 0.007), (0.003, -0.011), (-0.002, 0.011)]
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


def flat_mat(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m


skin_mat = flat_mat("Skin", (0.68, 0.52, 0.42))
leather_mat = flat_mat("Leather", (0.28, 0.17, 0.095))
wood_mat = flat_mat("Wood", (0.45, 0.30, 0.15))
fletch_mat = flat_mat("Fletch", (0.85, 0.15, 0.12))

body_obj.data.materials.append(skin_mat)
strap_obj.data.materials.append(leather_mat)
pouch_obj.data.materials.append(leather_mat)
for b in bolt_objs:
    b.data.materials.append(wood_mat)
    b.data.materials.append(fletch_mat)
    n = len(b.data.polygons)
    for poly in b.data.polygons[max(0, n - 4):]:
        poly.material_index = 1

all_objs = [body_obj, strap_obj, pouch_obj] + bolt_objs
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


def add_camera(name, offset, target=None):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    tgt = target if target else mathutils.Vector((cx2, cy2, cz2))
    cam_pos = tgt + offset
    cam.location = cam_pos
    direction = tgt - cam_pos
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return cam


dist = size * 1.5
cams = {
    "full_back": add_camera("Cam1", mathutils.Vector((dist * 0.15, dist * 1.3, dist * 0.1))),
    "full_back_3q": add_camera("Cam2", mathutils.Vector((dist * 0.65, dist * 1.05, dist * 0.35))),
}
# closer view centered on the quiver itself, but still with body visible for context
quiver_center = (pouch_base + pouch_top) * 0.5
cams["quiver_closeup"] = add_camera("Cam3", mathutils.Vector((0.55, 0.75, 0.15)), target=quiver_center)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900

for name, cam in cams.items():
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT_DIR, f"quiver_v4_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "quiver_v4.blend"))
print("DONE")

# debug: verify pouch geometry actually sits where we intended
pverts = [pouch_obj.matrix_world @ v.co for v in pouch_obj.data.vertices]
pxs = [v.x for v in pverts]; pys = [v.y for v in pverts]; pzs = [v.z for v in pverts]
print("POUCH actual bbox X", min(pxs), max(pxs), "Y", min(pys), max(pys), "Z", min(pzs), max(pzs))
print("intended pouch_base", pouch_base, "pouch_top", pouch_top)
