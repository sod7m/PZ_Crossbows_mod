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

# ---- Build the "strap" mesh from the reference loop, mirrored to the back ----
# original convention: x = left/right, y = height, z = depth (negative = front)
# blender convention here: X = left/right, Y = depth (positive = behind body), Z = height
strap_verts = []
for (ox, oy, oz) in ref["verts"]:
    bx = ox
    by = oz  # NOT negated -> flips the loop from front-hugging to back-hugging
    bz = oy
    strap_verts.append((bx, by, bz))

strap_faces = [tuple(f) for f in ref["faces"]]

strap_mesh = bpy.data.meshes.new("QuiverStrap")
strap_mesh.from_pydata(strap_verts, [], strap_faces)
strap_mesh.update()
strap_obj = bpy.data.objects.new("QuiverStrap", strap_mesh)
bpy.context.scene.collection.objects.link(strap_obj)

# bounding box of strap (world = local here, object has identity transform)
xs = [v[0] for v in strap_verts]
ys = [v[1] for v in strap_verts]
zs = [v[2] for v in strap_verts]
print(f"Strap bbox X {min(xs):.4f}..{max(xs):.4f}  Y {min(ys):.4f}..{max(ys):.4f}  Z {min(zs):.4f}..{max(zs):.4f}")

cx = (min(xs) + max(xs)) / 2
cz_top = max(zs)
cz_bot = min(zs)
cy_back = max(ys)  # deepest point on the back

# ---- Pouch: tapered cylinder over the right shoulder blade, angled ----
bm = bmesh.new()
pouch_radius_top = 0.075
pouch_radius_bottom = 0.045
pouch_length = 0.34

result = bmesh.ops.create_cone(
    bm,
    cap_ends=True,
    cap_tris=False,
    segments=10,
    radius1=pouch_radius_bottom,
    radius2=pouch_radius_top,
    depth=pouch_length,
)

# orient: cone's local axis is Z by default (create_cone builds along Z). We want it
# angled diagonally across the back, bottom near the opposite hip strap, top over the
# shoulder, tip open at the top.
angle_from_vertical = math.radians(22)
rot = mathutils.Matrix.Rotation(angle_from_vertical, 4, mathutils.Vector((1, 0, 0)))
rot2 = mathutils.Matrix.Rotation(math.radians(8), 4, mathutils.Vector((0, 0, 1)))
for v in bm.verts:
    v.co = (rot2 @ rot) @ v.co

pouch_center = mathutils.Vector((cx + 0.05, cy_back * 0.55, cz_top - 0.02))
for v in bm.verts:
    v.co += pouch_center

pouch_mesh = bpy.data.meshes.new("QuiverPouch")
bm.to_mesh(pouch_mesh)
bm.free()
pouch_obj = bpy.data.objects.new("QuiverPouch", pouch_mesh)
bpy.context.scene.collection.objects.link(pouch_obj)

pxs = [ (pouch_center + mathutils.Vector((0,0,0))) ]
pouch_top_center = pouch_center + (rot2 @ rot) @ mathutils.Vector((0, 0, pouch_length/2))
pouch_bottom_center = pouch_center + (rot2 @ rot) @ mathutils.Vector((0, 0, -pouch_length/2))
print("pouch top center", pouch_top_center, "bottom center", pouch_bottom_center)

# ---- Bolts poking out of the pouch opening (simple shaft + tip + fletching) ----
def make_bolt(name, origin, direction, length, shaft_r):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=shaft_r, radius2=shaft_r, depth=length,
    )
    # tip cone at the +Z end
    tip_len = length * 0.18
    result = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=shaft_r*1.3, radius2=0.0, depth=tip_len,
    )
    for v in result["verts"]:
        v.co.z += length/2 + tip_len/2

    # simple flat fletching fins near the base (two crossed thin quads)
    fletch_len = length * 0.16
    fletch_h = shaft_r * 3.2
    base_z = -length/2 + fletch_len/2
    for ang in (0, math.pi/2):
        fverts = []
        for (dx, dz) in [(-fletch_len/2, 0), (fletch_len/2, 0), (fletch_len/2, fletch_h), (-fletch_len/2, fletch_h)]:
            x = math.cos(ang) * 0.0 + dx * math.cos(ang)
            y = dx * math.sin(ang)
            fverts.append(bm.verts.new((x, y, base_z + dz)))
        bm.faces.new(fverts)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # orient along `direction`, then move to origin
    z_axis = mathutils.Vector((0, 0, 1))
    dirn = mathutils.Vector(direction).normalized()
    quat = z_axis.rotation_difference(dirn)
    obj.rotation_euler = quat.to_euler()
    obj.location = origin
    return obj

pouch_axis = ((rot2 @ rot) @ mathutils.Vector((0, 0, 1))).normalized()
bolt_length = 0.30
bolt_objs = []
offsets = [(-0.018, -0.01), (0.0, 0.012), (0.02, -0.006), (0.006, -0.024)]
for i, (ox, oy) in enumerate(offsets):
    perp1 = pouch_axis.cross(mathutils.Vector((0,0,1))).normalized()
    if perp1.length < 0.01:
        perp1 = mathutils.Vector((1,0,0))
    perp2 = pouch_axis.cross(perp1).normalized()
    origin = pouch_top_center + perp1 * ox + perp2 * oy - pouch_axis * (bolt_length*0.32)
    b = make_bolt(f"Bolt{i}", origin, pouch_axis, bolt_length, 0.007)
    bolt_objs.append(b)

# ---- materials (flat colors for a quick shape-approval render) ----
def flat_mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    return m

leather_mat = flat_mat("Leather", (0.30, 0.18, 0.10))
wood_mat = flat_mat("Wood", (0.42, 0.28, 0.14))
fletch_mat = flat_mat("Fletch", (0.75, 0.72, 0.60))

strap_obj.data.materials.append(leather_mat)
pouch_obj.data.materials.append(leather_mat)
for b in bolt_objs:
    b.data.materials.append(wood_mat)

# ---- combine bbox for camera framing ----
all_objs = [strap_obj, pouch_obj] + bolt_objs
allx, ally, allz = [], [], []
for o in all_objs:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        allx.append(w.x); ally.append(w.y); allz.append(w.z)
cx2 = (min(allx)+max(allx))/2
cy2 = (min(ally)+max(ally))/2
cz2 = (min(allz)+max(allz))/2
size = max(max(allx)-min(allx), max(ally)-min(ally), max(allz)-min(allz))
print("combined bbox center", cx2, cy2, cz2, "size", size)

sun = bpy.data.objects.new("Sun1", bpy.data.lights.new("Sun1", type='SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(55), 0, math.radians(35))
bpy.context.scene.collection.objects.link(sun)
sun2 = bpy.data.objects.new("Sun2", bpy.data.lights.new("Sun2", type='SUN'))
sun2.data.energy = 1.2
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

dist = size * 2.6
cams = {
    "back_3q": add_camera("Cam1", mathutils.Vector((dist*0.7, dist*1.1, dist*0.5))),
    "back_flat": add_camera("Cam2", mathutils.Vector((0, dist*1.4, dist*0.1))),
    "side": add_camera("Cam3", mathutils.Vector((dist*1.4, 0, dist*0.2))),
}

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900

for name, cam in cams.items():
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT_DIR, f"quiver_v1_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "quiver_v1.blend"))
print("DONE")
