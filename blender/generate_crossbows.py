"""Generate original PZCrossbows weapon meshes.

Builds brand-new crossbow geometry (not derived from the reference meshes) inside
each reference model's world bounding box, then writes it into the imported
reference object's LOCAL space and re-exports with the reference's own transform.
That guarantees the mod's models.txt (scale / attachment offsets / rotation) keeps
placing the weapon identically in the player's hands.

Run:
  blender --background --python generate_crossbows.py -- <out_dir> [--flipcfg key=zY ...]
"""
import bmesh
import bpy
import math
import sys
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(r"E:/PZCrossbows/blender")
REF = ROOT / "reference"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else (ROOT / "newModels")
OUT.mkdir(parents=True, exist_ok=True)

# style, drawn
MODELS = {
    "CrossBow.fbx": ("crude", False),
    "CrossBowDrawn.fbx": ("crude", True),
    "ImprovedCrossBow.fbx": ("improved", False),
    "ImprovedCrossBowDrawn.fbx": ("improved", True),
    "CompoundCrossBow.fbx": ("compound", False),
    "CompoundCrossBowDrawn.fbx": ("compound", True),
    "HandCrossBow.fbx": ("hand", False),
    "HandCrossBowDrawn.fbx": ("hand", True),
}

# ---------------------------------------------------------------- scene utils
def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def world_bounds(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx, mx - mn


def limb_front_sign(obj):
    """Return +1 if the bow limbs (widest |x|) sit toward +z in world space."""
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    cx = sum(p.x for p in pts) / len(pts)
    cz = sum(p.z for p in pts) / len(pts)
    ranked = sorted(pts, key=lambda p: -abs(p.x - cx))
    wide = ranked[: max(4, len(pts) // 12)]
    mz = sum(p.z for p in wide) / len(wide)
    return 1.0 if mz >= cz else -1.0

# ---------------------------------------------------------------- materials
def mat(name, color):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = color
    return m


def materials():
    return {
        "wood": mat("PZC_wood", (0.33, 0.18, 0.075, 1)),
        "wood2": mat("PZC_wood2", (0.46, 0.27, 0.12, 1)),
        "metal": mat("PZC_metal", (0.05, 0.055, 0.062, 1)),
        "steel": mat("PZC_steel", (0.17, 0.18, 0.2, 1)),
        "grip": mat("PZC_grip", (0.02, 0.02, 0.02, 1)),
        "cord": mat("PZC_cord", (0.62, 0.58, 0.48, 1)),
        "bolt": mat("PZC_bolt", (0.5, 0.31, 0.13, 1)),
        "tip": mat("PZC_tip", (0.55, 0.56, 0.58, 1)),
    }

PARTS = []  # (object, material)

def _finish(obj, material, smooth=True, bevel=0.0):
    obj.data.materials.clear()
    obj.data.materials.append(material)
    if bevel > 0:
        b = obj.modifiers.new("bvl", "BEVEL")
        b.width = bevel
        b.segments = 2
        b.harden_normals = True
        obj.modifiers.new("wn", "WEIGHTED_NORMAL")
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    PARTS.append((obj, material))
    return obj

# ---- normalized-space builders (nx,ny,nz in [0,1]) mapped later to bbox -----
class Frame:
    """Maps normalized design coords to world bbox coords, with axis flips."""
    def __init__(self, mn, size, flip_z, flip_y):
        self.mn = mn
        self.size = size
        self.fz = flip_z
        self.fy = flip_y

    def P(self, nx, ny, nz):
        if self.fz:
            nz = 1 - nz
        if self.fy:
            ny = 1 - ny
        return Vector((
            self.mn.x + nx * self.size.x,
            self.mn.y + ny * self.size.y,
            self.mn.z + nz * self.size.z,
        ))

    def D(self, dx, dy, dz):
        return Vector((dx * self.size.x, dy * self.size.y, dz * self.size.z))


def box(fr, name, center, dims, material, rot=(0, 0, 0), bevel=0.18):
    bpy.ops.mesh.primitive_cube_add(size=1, location=fr.P(*center), rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = fr.D(*dims)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, material, bevel=min(fr.D(*dims)) * bevel)


def rod(fr, name, a, b, radius_frac, material, verts=12, taper=1.0):
    p1 = fr.P(*a)
    p2 = fr.P(*b)
    d = p2 - p1
    r = min(fr.size) * radius_frac
    if taper == 1.0:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length,
                                             location=(p1 + p2) * 0.5)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r * taper,
                                        depth=d.length, location=(p1 + p2) * 0.5)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return _finish(o, material)


def disc(fr, name, center, radius_frac, thick_frac, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=min(fr.size) * radius_frac,
                                        depth=fr.size.x * thick_frac,
                                        location=fr.P(*center),
                                        rotation=(0, math.pi / 2, 0))
    o = bpy.context.object
    o.name = name
    return _finish(o, material)


def profile(fr, name, pts_zy, half_w, material, bevel=0.03):
    """Extrude a side silhouette (list of (nz,ny)) across x width -> tiller."""
    verts = []
    for side in (-0.5, 0.5):
        for (nz, ny) in pts_zy:
            verts.append(fr.P(0.5 + half_w * side * 2, ny, nz))
    n = len(pts_zy)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    me = bpy.data.meshes.new(name + "M")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return _finish(o, material, bevel=min(fr.size) * bevel)


def swept_limb(fr, name, path_pts, cross, material, twist=0.0):
    """Loft a rectangular cross-section (cross=(w_frac,h_frac) sequence) along a
    world-space path of Vectors. Produces a smooth recurve limb."""
    rings = []
    m = len(path_pts)
    for i, c in enumerate(path_pts):
        if i < m - 1:
            tangent = (path_pts[i + 1] - c)
        else:
            tangent = (c - path_pts[i - 1])
        tangent.normalize()
        up = Vector((0, 1, 0))
        side = tangent.cross(up)
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        upv = side.cross(tangent).normalized()
        w, h = cross[min(i, len(cross) - 1)]
        ww = fr.size.x * w
        hh = min(fr.size) * h
        ring = [c + side * (ww * 0.5) + upv * (hh * 0.5),
                c - side * (ww * 0.5) + upv * (hh * 0.5),
                c - side * (ww * 0.5) - upv * (hh * 0.5),
                c + side * (ww * 0.5) - upv * (hh * 0.5)]
        rings.append(ring)
    verts = []
    for ring in rings:
        verts.extend(ring)
    faces = []
    for i in range(m - 1):
        a = i * 4
        b = (i + 1) * 4
        for k in range(4):
            kn = (k + 1) % 4
            faces.append((a + k, a + kn, b + kn, b + k))
    faces.append((0, 1, 2, 3))
    last = (m - 1) * 4
    faces.append((last + 3, last + 2, last + 1, last))
    me = bpy.data.meshes.new(name + "M")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return _finish(o, material, bevel=min(fr.size) * 0.006)


def arc_tube(fr, name, center, radius_frac, thick_frac, a0, a1, plane, material, seg=16):
    """A partial torus (guard / stirrup). plane 'zy' spins in z-y; 'xz' in x-z."""
    cx = fr.P(*center)
    R = min(fr.size) * radius_frac
    r = min(fr.size) * thick_frac
    path = []
    cross = []
    for i in range(seg + 1):
        t = a0 + (a1 - a0) * i / seg
        if plane == "zy":
            path.append(cx + Vector((0, math.sin(t) * R, math.cos(t) * R)))
        else:  # xz
            path.append(cx + Vector((math.cos(t) * R, 0, math.sin(t) * R)))
        cross.append((r / fr.size.x, r / min(fr.size)))
    return swept_limb(fr, name, path, cross, material)


# ---------------------------------------------------------------- limb helper
def recurve_path(fr, x_out, z_root, z_tip, y, curl):
    """Build one limb path from center root to outer tip with a recurve curl."""
    steps = 7
    pts = []
    for i in range(steps + 1):
        t = i / steps
        nx = 0.5 + (x_out - 0.5) * t
        # gentle recurve: limb bellies rearward mid-span, tips flick forward
        belly = math.sin(t * math.pi) * 0.06
        nz = z_root + (z_tip - z_root) * t - belly + curl * (t ** 4)
        ny = y - math.sin(t * math.pi) * 0.010
        pts.append(fr.P(nx, ny, nz))
    return pts

# ================================================================ crossbows
def build(style, drawn, fr):
    M = materials()
    wood, wood2, metal, steel, grip, cord, bolt, tip = (
        M["wood"], M["wood2"], M["metal"], M["steel"], M["grip"], M["cord"], M["bolt"], M["tip"])

    if style == "hand":
        build_hand(fr, drawn, M)
        return
    if style == "compound":
        build_compound(fr, drawn, M)
        return

    improved = style == "improved"
    limb_mat = wood2
    # --- tiller / stock silhouette (nz along length, ny vertical; y=0 top) ---
    if improved:
        # tactical / angular tiller
        sil = [
            (0.01, 0.34), (0.12, 0.28), (0.30, 0.30), (0.52, 0.32),
            (0.74, 0.34), (0.92, 0.35), (0.95, 0.40),
            (0.95, 0.50), (0.74, 0.52), (0.54, 0.54),
            (0.42, 0.62), (0.30, 0.70), (0.22, 0.64), (0.10, 0.56), (0.01, 0.50),
        ]
        hw = 0.058
    else:
        # classic carved wooden stock with comb, wrist, grip swell
        sil = [
            (0.01, 0.36), (0.10, 0.27), (0.30, 0.33), (0.52, 0.34),
            (0.72, 0.36), (0.90, 0.37), (0.93, 0.41),
            (0.93, 0.52), (0.72, 0.54), (0.54, 0.56),
            (0.40, 0.64), (0.30, 0.71), (0.23, 0.66), (0.10, 0.58), (0.01, 0.52),
        ]
        hw = 0.062
    profile(fr, "stock", sil, hw, wood)
    # butt plate
    box(fr, "buttplate", (0.5, 0.44, 0.03), (0.10, 0.22, 0.03), wood2, bevel=0.25)
    # flight rail on top of fore-end
    box(fr, "rail", (0.5, 0.33, 0.66), (0.05, 0.05, 0.60), wood2, bevel=0.2)
    box(fr, "rail_groove", (0.5, 0.305, 0.66), (0.018, 0.04, 0.60), metal, bevel=0.2)
    # riser block that holds the bow
    box(fr, "riser", (0.5, 0.40, 0.90), (0.14, 0.16, 0.10), metal, bevel=0.18)
    # trigger guard + trigger
    arc_tube(fr, "guard", (0.5, 0.66, 0.30), 0.05, 0.010, math.radians(20), math.radians(200), "zy", metal)
    box(fr, "trigger", (0.5, 0.60, 0.30), (0.02, 0.07, 0.02), steel, bevel=0.2)
    # grip wrap
    box(fr, "grip", (0.5, 0.66, 0.20), (0.06, 0.16, 0.11), grip, rot=(math.radians(12), 0, 0), bevel=0.22)
    # foot stirrup at front
    arc_tube(fr, "stirrup", (0.5, 0.52, 0.965), 0.10, 0.012, math.radians(-70), math.radians(70), "xz", metal)

    # --- recurve limbs ---
    z_root, z_tip = 0.90, 0.92
    curl = 0.03
    lw = [(0.10, 0.05)] * 3 + [(0.07, 0.04), (0.055, 0.035), (0.04, 0.03), (0.03, 0.025), (0.022, 0.02)]
    left = recurve_path(fr, 0.02, z_root, z_tip, 0.42, curl)
    right = recurve_path(fr, 0.98, z_root, z_tip, 0.42, curl)
    swept_limb(fr, "limbL", left, lw, limb_mat)
    swept_limb(fr, "limbR", right, lw, limb_mat)
    if improved:
        # metal reinforcement strips
        swept_limb(fr, "limbLm", recurve_path(fr, 0.06, z_root, z_tip, 0.38, curl),
                   [(0.05, 0.015)] * len(lw), metal)
        swept_limb(fr, "limbRm", recurve_path(fr, 0.94, z_root, z_tip, 0.38, curl),
                   [(0.05, 0.015)] * len(lw), metal)
    tipL = left[-1]
    tipR = right[-1]
    nock_z = 0.60 if drawn else 0.90
    nock = fr.P(0.5, 0.43, nock_z)
    make_string(fr, tipL, tipR, nock, cord)
    if drawn:
        loaded_bolt(fr, M)
        box(fr, "latch", (0.5, 0.40, 0.58), (0.05, 0.05, 0.04), steel, bevel=0.2)


def build_compound(fr, drawn, M):
    wood, wood2, metal, steel, grip, cord = M["wood"], M["wood2"], M["metal"], M["steel"], M["grip"], M["cord"]
    sil = [
        (0.02, 0.40), (0.05, 0.30), (0.30, 0.33), (0.42, 0.38),
        (0.66, 0.40), (0.88, 0.42), (0.92, 0.38), (0.92, 0.55),
        (0.68, 0.57), (0.52, 0.63), (0.30, 0.70), (0.18, 0.66),
        (0.10, 0.58), (0.03, 0.54),
    ]
    profile(fr, "cstock", sil, 0.045, metal)
    box(fr, "buttplate", (0.5, 0.44, 0.03), (0.09, 0.20, 0.03), grip, bevel=0.25)
    box(fr, "rail", (0.5, 0.33, 0.64), (0.05, 0.05, 0.62), metal, bevel=0.2)
    box(fr, "rail_groove", (0.5, 0.305, 0.64), (0.018, 0.04, 0.62), steel, bevel=0.2)
    box(fr, "scope_rail", (0.5, 0.24, 0.50), (0.05, 0.05, 0.30), steel, bevel=0.15)
    box(fr, "riser", (0.5, 0.42, 0.88), (0.16, 0.18, 0.12), metal, bevel=0.15)
    arc_tube(fr, "guard", (0.5, 0.66, 0.30), 0.05, 0.010, math.radians(20), math.radians(200), "zy", metal)
    box(fr, "trigger", (0.5, 0.60, 0.30), (0.02, 0.07, 0.02), steel, bevel=0.2)
    box(fr, "grip", (0.5, 0.66, 0.20), (0.06, 0.16, 0.11), grip, rot=(math.radians(12), 0, 0), bevel=0.22)
    # short stiff compound limbs (nearly straight, angled outward)
    z_root, z_tip = 0.88, 0.82
    lw = [(0.10, 0.055)] * 2 + [(0.09, 0.05), (0.08, 0.045), (0.07, 0.04), (0.06, 0.035)]
    left = [fr.P(0.5 + (0.12 - 0.5) * (i / 5), 0.42, z_root + (z_tip - z_root) * (i / 5)) for i in range(6)]
    right = [fr.P(0.5 + (0.88 - 0.5) * (i / 5), 0.42, z_root + (z_tip - z_root) * (i / 5)) for i in range(6)]
    swept_limb(fr, "climbL", left, lw, metal)
    swept_limb(fr, "climbR", right, lw, metal)
    # eccentric cam wheels at limb tips
    disc(fr, "camL", (0.11, 0.42, 0.80), 0.085, 0.07, steel)
    disc(fr, "camR", (0.89, 0.42, 0.80), 0.085, 0.07, steel)
    disc(fr, "camLh", (0.11, 0.42, 0.80), 0.030, 0.09, metal)
    disc(fr, "camRh", (0.89, 0.42, 0.80), 0.030, 0.09, metal)
    # cables + string through cams
    nock_z = 0.56 if drawn else 0.84
    nock = fr.P(0.5, 0.43, nock_z)
    tipL = fr.P(0.11, 0.42, 0.85)
    tipR = fr.P(0.89, 0.42, 0.85)
    make_string(fr, tipL, tipR, nock, cord, r=0.006)
    rod(fr, "cableA", (0.11, 0.40, 0.76), (0.89, 0.44, 0.84), 0.005, cord, verts=6)
    rod(fr, "cableB", (0.11, 0.44, 0.84), (0.89, 0.40, 0.76), 0.005, cord, verts=6)
    if drawn:
        loaded_bolt(fr, M)
        box(fr, "latch", (0.5, 0.40, 0.56), (0.05, 0.05, 0.04), steel, bevel=0.2)


def build_hand(fr, drawn, M):
    wood, wood2, metal, steel, grip, cord = M["wood"], M["wood2"], M["metal"], M["steel"], M["grip"], M["cord"]
    # compact body (spans nearly the full length so it fills the reference box)
    box(fr, "hbody", (0.5, 0.46, 0.50), (0.14, 0.36, 0.90), wood, bevel=0.14)
    box(fr, "hrail", (0.5, 0.28, 0.60), (0.05, 0.07, 0.74), wood2, bevel=0.18)
    box(fr, "hgroove", (0.5, 0.25, 0.60), (0.02, 0.05, 0.74), metal, bevel=0.2)
    box(fr, "hriser", (0.5, 0.44, 0.92), (0.13, 0.16, 0.10), metal, bevel=0.15)
    # magazine box (repeating hand crossbow look)
    box(fr, "hmag", (0.5, 0.20, 0.40), (0.16, 0.18, 0.20), metal, bevel=0.12)
    # pistol grip
    box(fr, "hgrip", (0.5, 0.76, 0.20), (0.11, 0.34, 0.16), grip, rot=(math.radians(18), 0, 0), bevel=0.2)
    arc_tube(fr, "hguard", (0.5, 0.66, 0.34), 0.06, 0.012, math.radians(20), math.radians(200), "zy", metal)
    box(fr, "htrigger", (0.5, 0.60, 0.34), (0.03, 0.08, 0.03), steel, bevel=0.2)
    # short recurve limbs
    z_root, z_tip = 0.90, 0.92
    curl = 0.03
    lw = [(0.12, 0.06)] * 2 + [(0.09, 0.05), (0.06, 0.04), (0.04, 0.03), (0.03, 0.025)]
    left = recurve_path(fr, 0.04, z_root, z_tip, 0.44, curl)
    right = recurve_path(fr, 0.96, z_root, z_tip, 0.44, curl)
    swept_limb(fr, "hlimbL", left, lw, wood2)
    swept_limb(fr, "hlimbR", right, lw, wood2)
    nock_z = 0.58 if drawn else 0.90
    nock = fr.P(0.5, 0.45, nock_z)
    make_string(fr, left[-1], right[-1], nock, cord, r=0.008)
    if drawn:
        loaded_bolt(fr, M, hand=True)


def make_string(fr, tipL, tipR, nock, cord, r=0.006):
    for name, a in (("stringL", tipL), ("stringR", tipR)):
        d = nock - a
        rr = min(fr.size) * r
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=rr, depth=d.length,
                                            location=(a + nock) * 0.5)
        o = bpy.context.object
        o.name = name
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        _finish(o, cord)


def loaded_bolt(fr, M, hand=False):
    z0, z1 = (0.50, 0.90) if not hand else (0.46, 0.82)
    y = 0.30 if not hand else 0.27
    rod(fr, "boltshaft", (0.5, y, z0), (0.5, y, z1), 0.012, M["bolt"], verts=8)
    rod(fr, "bolthead", (0.5, y, z1), (0.5, y, min(z1 + 0.06, 0.97)), 0.03, M["tip"], verts=10, taper=0.02)
    box(fr, "fletch", (0.5, y, max(z0 - 0.03, 0.05)), (0.10, 0.02, 0.03), grip_or(M), bevel=0.1)


def grip_or(M):
    return M["grip"]

# ---------------------------------------------------------------- assemble
def combine_and_remap(obj, frame_ignored):
    bpy.ops.object.select_all(action="DESELECT")
    objs = [o for (o, _m) in PARTS]
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


def export_one(fname, style, drawn, turn, bounds_file, offset=(0.0, 0.0, 0.0)):
    clear()
    PARTS.clear()
    # Build bbox comes from bounds_file: for a *Drawn* variant this is the
    # matching un-drawn file, so the drawn body lands in the exact same world
    # box -> no shift in the player's hands when a bolt is loaded.
    bpy.ops.import_scene.fbx(filepath=str(REF / bounds_file))
    bref = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    mn, mx, size = world_bounds(bref)
    clear()
    # The actual target file supplies the object transform we export with.
    bpy.ops.import_scene.fbx(filepath=str(REF / fname))
    ref = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    ref_matrix = ref.matrix_world.copy()
    fr = Frame(mn, size, False, False)
    build(style, drawn, fr)
    new = combine_and_remap(ref, fr)
    # thicken toward the reference's Y extent so the weapon is not paper-thin
    yc = (mn.y + mx.y) * 0.5
    ys = [v.co.y for v in new.data.vertices]
    cur = max(ys) - min(ys)
    if cur > 1e-9:
        f = min(1.7, (size.y * 0.82) / cur)
        for v in new.data.vertices:
            v.co.y = yc + (v.co.y - yc) * f
    # optional placement nudge in the common world-clean frame
    #   x = span (left/right),  y = thin (up = -y),  z = length (forward = +z)
    # applied equally to drawn+undrawn of a tier so they stay synced
    if any(offset):
        dx, dy, dz = offset
        for v in new.data.vertices:
            v.co.x += dx * size.x
            v.co.y += dy * size.y
            v.co.z += dz * size.z
    # match reference front/back: rotate 180 deg about Y through bbox centre
    # (a true rotation, not a mirror, so handedness and bbox fit are preserved)
    if turn:
        cx = (mn.x + mx.x) * 0.5
        cz = (mn.z + mx.z) * 0.5
        for v in new.data.vertices:
            v.co = Vector((2 * cx - v.co.x, v.co.y, 2 * cz - v.co.z))
    # transform new geometry (currently world coords) into ref local space
    inv = ref_matrix.inverted()
    for v in new.data.vertices:
        v.co = inv @ v.co
    new.matrix_world = ref_matrix
    new.name = "PZC_" + fname.replace(".fbx", "")
    # UV: simple planar box per material handled at texture stage; add basic UV
    add_planar_uv(new)
    bpy.ops.object.select_all(action="DESELECT")
    new.select_set(True)
    bpy.context.view_layer.objects.active = new
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / fname),
        use_selection=True,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_space_transform=False,
        apply_unit_scale=True,
        path_mode="AUTO",
    )
    # validate
    exp = re_measure(OUT / fname)
    print(f"[{fname}] target size={[round(a,4) for a in size]} exported={exp}")


def re_measure(path):
    tmp = bpy.data.scenes.new("m")
    old = bpy.context.window.scene
    bpy.context.window.scene = tmp
    bpy.ops.import_scene.fbx(filepath=str(path))
    o = [x for x in tmp.objects if x.type == "MESH"][0]
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    bpy.context.window.scene = old
    bpy.data.scenes.remove(tmp)
    return [round(a, 4) for a in (mx - mn)]


def add_planar_uv(obj):
    me = obj.data
    uv = me.uv_layers.new(name="UV")
    pts = [v.co for v in me.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    sz = mx - mn
    def region(name):
        n = name.lower()
        if "metal" in n or "steel" in n:
            return (0.52, 0.02, 0.98, 0.48)
        if "grip" in n:
            return (0.02, 0.52, 0.48, 0.98)
        if "tip" in n:
            return (0.52, 0.52, 0.98, 0.98)
        return (0.02, 0.02, 0.48, 0.48)  # wood, wood2, bolt, cord
    for poly in me.polygons:
        m = me.materials[poly.material_index] if poly.material_index < len(me.materials) else None
        u0, v0, u1, v1 = region(m.name if m else "wood")
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            fu = (co.z - mn.z) / sz.z if sz.z else 0.5
            fv = (co.x - mn.x) / sz.x if sz.x else 0.5
            uv.data[li].uv = (u0 + (u1 - u0) * fu, v0 + (v1 - v0) * fv)


def main():
    # In-game testing showed every tier holds correctly with NO 180 turn.
    TURN = {"crude": False, "improved": False, "compound": False, "hand": False}
    # Drawn variants build inside their un-drawn sibling's box so the body does
    # not jump when a bolt is loaded.
    BOUNDS_OF = {
        "CrossBowDrawn.fbx": "CrossBow.fbx",
        "ImprovedCrossBowDrawn.fbx": "ImprovedCrossBow.fbx",
        "CompoundCrossBowDrawn.fbx": "CompoundCrossBow.fbx",
        "HandCrossBowDrawn.fbx": "HandCrossBow.fbx",
    }
    # placement nudges in the common world-clean frame (fractions of bbox size):
    #   x = span (- = left),  y = thin (- = up),  z = length (+ = forward toward bow)
    # NOTE from in-game testing: up = +y (positive), forward = +z (positive).
    OFFSET = {
        "crude": (0.0, 0.12, 0.55),       # well forward + slight lift onto hand
        "improved": (0.0, 0.12, 0.55),
        "compound": (0.0, 0.16, 0.0),     # lift onto hand (left shift reverted; tracer fixed in models.txt)
    }
    # the hand crossbow is already perfect in-game -> leave it untouched
    skip = {"HandCrossBow.fbx", "HandCrossBowDrawn.fbx"}
    only = [a for a in argv[1:] if a.endswith(".fbx")]
    for fname, (style, drawn) in MODELS.items():
        if fname in skip:
            continue
        if only and fname not in only:
            continue
        export_one(fname, style, drawn, TURN[style],
                   BOUNDS_OF.get(fname, fname), OFFSET.get(style, (0.0, 0.0, 0.0)))
    print("ALL DONE")


if __name__ == "__main__":
    main()
