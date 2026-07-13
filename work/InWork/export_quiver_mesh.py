import bpy
import bmesh
import math
import mathutils
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
ref_strap_path = argv[0]
gender_tag = argv[1]  # "bob" or "kate"
out_json = argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)


def to_blender(verts):
    return [(ox, oz, oy) for (ox, oy, oz) in verts]


def to_original(v):
    # inverse of to_blender: blender(x,y,z) -> original(x,y,z) with y=height,z=depth
    return (v[0], v[2], v[1])


ref = parse_mesh(ref_strap_path)
strap_verts_b = to_blender(ref["verts"])
strap_faces = [tuple(f) for f in ref["faces"]]

sxs = [v[0] for v in strap_verts_b]
sy_ = [v[1] for v in strap_verts_b]
szs = [v[2] for v in strap_verts_b]

back_idx = max(range(len(strap_verts_b)), key=lambda i: strap_verts_b[i][1])
attach_point = mathutils.Vector(strap_verts_b[back_idx]) + mathutils.Vector((0.0, 0.0, -0.13))  # lowered
print("attach point (mid-back):", attach_point)

pouch_length = 0.30
r_top = 0.040  # same as the base -- a fully closed, constant-width cylinder
pouch_base = attach_point + mathutils.Vector((0.0, 0.0, 0.0))  # flush, zero gap
lean_x = math.radians(3)
lean_y = math.radians(4)
axis_dir = mathutils.Vector((math.sin(lean_x), math.sin(lean_y), math.cos(lean_x) * math.cos(lean_y))).normalized()
pouch_top = pouch_base + axis_dir * pouch_length

# constant-width closed cylinder, full length -- no taper anywhere, so it
# fully encloses every bolt regardless of its offset from the centre
POUCH_PROFILE = [
    (0.00, 0.040),
    (1.00, r_top),
]


def build_pouch_verts_faces(vstart, segments=14):
    z_axis = mathutils.Vector((0, 0, 1))
    quat = z_axis.rotation_difference(axis_dir)
    center = pouch_base + axis_dir * (pouch_length * 0.5)

    rings = []
    for t, r in POUCH_PROFILE:
        z = (t - 0.5) * pouch_length
        ring = []
        for i in range(segments):
            ang = 2 * math.pi * i / segments
            local = mathutils.Vector((r * math.cos(ang), r * math.sin(ang), z))
            ring.append(quat @ local + center)
        rings.append(ring)

    verts = []
    for ring in rings:
        verts.extend(ring)
    bottom_center_idx = len(verts)
    verts.append(quat @ mathutils.Vector((0, 0, (POUCH_PROFILE[0][0] - 0.5) * pouch_length)) + center)
    top_center_idx = len(verts)
    verts.append(quat @ mathutils.Vector((0, 0, (POUCH_PROFILE[-1][0] - 0.5) * pouch_length)) + center)

    faces = []
    n_rings = len(rings)
    for r in range(n_rings - 1):
        base0 = r * segments
        base1 = (r + 1) * segments
        for i in range(segments):
            j = (i + 1) % segments
            a, b, c, d = base0 + i, base0 + j, base1 + j, base1 + i
            faces.append((a, b, c))
            faces.append((a, c, d))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((bottom_center_idx, j, i))
    top_base = (n_rings - 1) * segments
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((top_center_idx, top_base + i, top_base + j))

    verts = [tuple(v) for v in verts]
    faces = [tuple(vi + vstart for vi in f) for f in faces]
    return verts, faces


def build_torus_verts_faces(vstart, center, axis_dir, major_r, minor_r=0.006, major_seg=16, minor_seg=6):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_r, minor_radius=minor_r, location=(0, 0, 0),
                                      major_segments=major_seg, minor_segments=minor_seg)
    obj = bpy.context.active_object
    z_axis = mathutils.Vector((0, 0, 1))
    quat = z_axis.rotation_difference(axis_dir)
    obj.rotation_euler = quat.to_euler()
    obj.location = center
    bpy.context.view_layer.update()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    mat = obj.matrix_world
    verts = [tuple(mat @ v.co) for v in bm.verts]
    faces = [tuple(vi.index + vstart for vi in f.verts) for f in bm.faces]
    bm.free()
    bpy.data.objects.remove(obj, do_unlink=True)
    return verts, faces


def build_strap_box_verts_faces(vstart, p0, p1, width, thickness):
    axis = (p1 - p0)
    axis_n = axis.normalized()
    up = mathutils.Vector((0, 0, 1))
    side = axis_n.cross(up).normalized()
    if side.length < 0.01:
        side = mathutils.Vector((1, 0, 0))
    normal = axis_n.cross(side).normalized()
    hw, ht = width / 2, thickness / 2
    verts = []
    for t in (0.0, 1.0):
        c = p0 + axis * t
        for sw, sh in [(-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht)]:
            verts.append(tuple(c + side * sw + normal * sh))
    ring0 = [0, 1, 2, 3]
    ring1 = [4, 5, 6, 7]
    quads = []
    for i in range(4):
        a, b = ring0[i], ring0[(i + 1) % 4]
        c, d = ring1[(i + 1) % 4], ring1[i]
        quads.append((a, b, c, d))
    quads.append(tuple(reversed(ring0)))
    quads.append(tuple(ring1))
    faces = []
    for q in quads:
        faces.append((q[0], q[1], q[2]))
        faces.append((q[0], q[2], q[3]))
    faces = [tuple(vi + vstart for vi in f) for f in faces]
    return verts, faces


def build_bolt_verts_faces(vstart, origin, direction, length, shaft_r):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=shaft_r, radius2=shaft_r, depth=length)
    shaft_result = bmesh.ops.triangulate(bm, faces=list(bm.faces))
    shaft_face_set = set(shaft_result["faces"])

    tip_len = length * 0.22
    result = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=shaft_r * 1.6, radius2=0.0, depth=tip_len)
    for v in result["verts"]:
        v.co.z += length / 2 + tip_len / 2
    raw_tip_faces = [f for f in bm.faces if f not in shaft_face_set]
    tip_result = bmesh.ops.triangulate(bm, faces=raw_tip_faces)
    tip_face_set = set(tip_result["faces"])

    fletch_len = length * 0.22
    fletch_h = shaft_r * 2.2
    base_z = -length / 2 + fletch_len / 2
    fletch_face_set = set()
    for ang in (0, math.pi / 2, math.pi, math.pi * 1.5):
        nx, ny = math.cos(ang), math.sin(ang)
        v0 = bm.verts.new((0, 0, base_z - fletch_len / 2))
        v1 = bm.verts.new((nx * fletch_h, ny * fletch_h, base_z))
        v2 = bm.verts.new((0, 0, base_z + fletch_len / 2))
        fletch_face_set.add(bm.faces.new((v0, v1, v2)))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    z_axis = mathutils.Vector((0, 0, 1))
    dirn = mathutils.Vector(direction).normalized()
    quat = z_axis.rotation_difference(dirn)
    bm.verts.ensure_lookup_table()
    verts = [tuple(quat @ v.co + origin) for v in bm.verts]
    faces = []
    tip_faces = []
    fletch_faces = []
    vertex_group = ["wood"] * len(verts)
    for f in bm.faces:
        idx = tuple(vi.index + vstart for vi in f.verts)
        faces.append(idx)
        if f in fletch_face_set:
            fletch_faces.append(idx)
            for vi in f.verts:
                vertex_group[vi.index] = "fletch"
        elif f in tip_face_set:
            tip_faces.append(idx)
            for vi in f.verts:
                if vertex_group[vi.index] != "fletch":
                    vertex_group[vi.index] = "tip"
    bm.free()
    return verts, faces, tip_faces, fletch_faces, vertex_group


all_verts = list(strap_verts_b)
all_faces = list(strap_faces)
groups = ["strap"] * len(strap_verts_b)
face_groups = ["strap"] * len(strap_faces)

pv, pf = build_pouch_verts_faces(len(all_verts))
all_verts += pv
all_faces += pf
groups += ["leather"] * len(pv)
face_groups += ["leather"] * len(pf)

def profile_radius_at(t):
    for i in range(len(POUCH_PROFILE) - 1):
        t0, r0 = POUCH_PROFILE[i]
        t1, r1 = POUCH_PROFILE[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            return r0 + (r1 - r0) * f
    return POUCH_PROFILE[-1][1]


for t in (0.30, 0.88):
    band_center = pouch_base + axis_dir * (pouch_length * t)
    band_r = profile_radius_at(t) + 0.007
    bv, bf = build_torus_verts_faces(len(all_verts), band_center, axis_dir, band_r)
    all_verts += bv
    all_faces += bf
    groups += ["leather"] * len(bv)
    face_groups += ["leather"] * len(bf)

cv, cf = build_strap_box_verts_faces(len(all_verts), attach_point, pouch_base + axis_dir * (pouch_length * 0.30), 0.04, 0.018)
all_verts += cv
all_faces += cf
groups += ["leather"] * len(cv)
face_groups += ["leather"] * len(cf)

bolt_length = 0.19  # NOT increased, per explicit instruction
offsets = [(-0.0264, 0.0), (0.0222, 0.0144), (0.006, -0.0222), (-0.0042, 0.0222),
           (0.0162, -0.0102), (-0.0186, -0.012)]
perp1 = axis_dir.cross(mathutils.Vector((0, 0, 1)))
if perp1.length < 0.01:
    perp1 = mathutils.Vector((1, 0, 0))
perp1.normalize()
perp2 = axis_dir.cross(perp1).normalized()

for i, (ox, oy) in enumerate(offsets):
    # arrow's own total length = 100%; cylinder (pouch_length) = 75% of it,
    # so 75% of the bolt sits hidden inside the cylinder, 25% pokes out above.
    # build_bolt_verts_faces centres the bolt geometry ON `origin` (the cone is
    # built from -length/2 to +length/2), so `origin` must be the bolt's
    # MIDPOINT, not its bottom -- offset the bottom-of-bolt point by +length/2.
    # only the pointed tip (0.22 of the bolt's own length, matching the tip
    # cone built in build_bolt_verts_faces) should poke out above the
    # cylinder -- the shaft and fletching stay fully hidden inside it
    exposed_len = bolt_length * 0.22
    bolt_top = pouch_top + axis_dir * exposed_len
    bolt_bottom = bolt_top - axis_dir * bolt_length
    origin = bolt_bottom + perp1 * ox + perp2 * oy + axis_dir * (bolt_length * 0.5)
    bv, bf, tip_f, fletch_f, vgroup = build_bolt_verts_faces(len(all_verts), origin, axis_dir, bolt_length, 0.0055)
    all_verts += bv
    all_faces += bf
    groups += vgroup
    tip_set = set(tip_f)
    fletch_set = set(fletch_f)
    for f in bf:
        if f in fletch_set:
            face_groups.append("fletch")
        elif f in tip_set:
            face_groups.append("tip")
        else:
            face_groups.append("wood")

data = {
    "gender": gender_tag,
    "n_strap_verts": len(strap_verts_b),
    "verts_blender": all_verts,
    "faces": all_faces,
    "vertex_groups": groups,
    "face_groups": face_groups,
}
with open(out_json, "w") as f:
    json.dump(data, f)
print("wrote", out_json, "verts:", len(all_verts), "faces:", len(all_faces))
