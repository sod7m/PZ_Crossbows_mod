import bpy
import bmesh
import math
import mathutils
import os

OUT_DIR = "E:/PZCrossbows/work/InWork"
bpy.ops.wm.read_factory_settings(use_empty=True)

# Blender-space convention used here: X = left/right, Y = depth (positive = behind
# the body / away from viewer when looking at the back), Z = height (root ~ pelvis,
# matching the vanilla AmmoStrap_Shells chest-strap height range of Z 0.60-0.82).

HIP_L = mathutils.Vector((-0.085, 0.055, 0.04))     # strap anchor, lower-left hip, on the back
SHOULDER_R = mathutils.Vector((0.075, 0.050, 0.92))  # strap anchor, upper-right shoulder, on the back
POUCH_TOP = mathutils.Vector((0.135, 0.075, 1.16))   # quiver mouth, above the shoulder

def make_strap(p0, p1, width, thickness, name):
    axis = (p1 - p0)
    length = axis.length
    axis_n = axis.normalized()
    up = mathutils.Vector((0, 0, 1))
    side = axis_n.cross(up).normalized()
    if side.length < 0.01:
        side = mathutils.Vector((1, 0, 0))
    normal = axis_n.cross(side).normalized()

    bm = bmesh.new()
    hw = width / 2
    ht = thickness / 2
    verts = []
    for t in (0.0, 1.0):
        center = p0 + axis * t
        for sw, sh in [(-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht)]:
            verts.append(bm.verts.new(center + side * sw + normal * sh))
    # 4 side faces (a box, capped ends)
    ring0 = verts[0:4]
    ring1 = verts[4:8]
    for i in range(4):
        a, b = ring0[i], ring0[(i + 1) % 4]
        c, d = ring1[(i + 1) % 4], ring1[i]
        bm.faces.new((a, b, c, d))
    bm.faces.new(ring0[::-1])
    bm.faces.new(ring1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_pouch(p_bottom, p_top, r_bottom, r_top, name, segments=12):
    axis = p_top - p_bottom
    length = axis.length
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=r_bottom, radius2=r_top, depth=length,
    )
    z_axis = mathutils.Vector((0, 0, 1))
    quat = z_axis.rotation_difference(axis.normalized())
    for v in bm.verts:
        v.co = quat @ v.co
    center = p_bottom + axis * 0.5
    for v in bm.verts:
        v.co += center
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, quat, center


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
    fletch_verts_idx = []
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
    quat = z_axis.rotation_difference(dirn)
    obj.rotation_euler = quat.to_euler()
    obj.location = origin
    return obj


strap_obj = make_strap(HIP_L, SHOULDER_R, width=0.11, thickness=0.028, name="QuiverStrap")
pouch_obj, pouch_quat, pouch_center = make_pouch(SHOULDER_R, POUCH_TOP, r_bottom=0.05, r_top=0.075, name="QuiverPouch")

pouch_axis = (POUCH_TOP - SHOULDER_R).normalized()
mouth_center = POUCH_TOP
bolt_length = 0.34
offsets = [(-0.022, 0.0), (0.018, 0.012), (0.006, -0.020), (-0.005, 0.020)]
perp1 = pouch_axis.cross(mathutils.Vector((0, 0, 1)))
if perp1.length < 0.01:
    perp1 = mathutils.Vector((1, 0, 0))
perp1.normalize()
perp2 = pouch_axis.cross(perp1).normalized()

bolt_objs = []
for i, (ox, oy) in enumerate(offsets):
    origin = mouth_center + perp1 * ox + perp2 * oy - pouch_axis * (bolt_length * 0.30)
    b = make_bolt(f"Bolt{i}", origin, pouch_axis, bolt_length, 0.008)
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
    for poly in b.data.polygons:
        # fletching faces were added after the cones; identify by vertex count (triangles near base)
        pass

# assign fletch material to the last N faces (the 4 fletch triangles) of each bolt
for b in bolt_objs:
    n = len(b.data.polygons)
    for poly in b.data.polygons[max(0, n - 4):]:
        poly.material_index = 1

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


dist = size * 1.55
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
    scene.render.filepath = os.path.join(OUT_DIR, f"quiver_v2_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "quiver_v2.blend"))
print("DONE")
