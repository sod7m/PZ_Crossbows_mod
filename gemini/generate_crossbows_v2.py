"""Generate PERFECTLY SYMMETRIC original PZCrossbows weapon meshes.

This V2 script forces perfect axial symmetry by mirroring geometry across the 
central stock axis (X=0.5 in normalized space), regardless of reference skew.

Run:
  blender --background --python generate_crossbows_v2.py -- <out_dir>
"""
import bmesh
import bpy
import math
import sys
from mathutils import Vector, Matrix
from pathlib import Path

# Paths
ROOT = Path(r"E:/PZCrossbows/blender")
REF = ROOT / "reference"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else (Path(r"E:/PZCrossbows/gemini/models"))
OUT.mkdir(parents=True, exist_ok=True)

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

def mat(name, color):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = color
    return m

PARTS = []

def _finish(obj, material, smooth=True):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.clear()
    obj.data.materials.append(material)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    PARTS.append(obj)
    return obj

class Frame:
    def __init__(self, mn, size):
        self.mn = mn
        self.size = size
        # Force perfect center alignment for X
        self.center_x = (mn.x + mn.x + size.x) * 0.5

    def P(self, nx, ny, nz):
        # nx=0.5 is exactly center_x
        return Vector((
            self.mn.x + nx * self.size.x,
            self.mn.y + ny * self.size.y,
            self.mn.z + nz * self.size.z,
        ))

    def D(self, dx, dy, dz):
        return Vector((dx * self.size.x, dy * self.size.y, dz * self.size.z))

def box(fr, name, center, dims, material, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=fr.P(*center), rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = fr.D(*dims)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, material)

def swept_limb(fr, name, path_pts, cross, material):
    rings = []
    m = len(path_pts)
    for i, c in enumerate(path_pts):
        if i < m - 1: tangent = (path_pts[i + 1] - c)
        else: tangent = (c - path_pts[i - 1])
        tangent.normalize()
        up = Vector((0, 1, 0))
        side = tangent.cross(up).normalized()
        upv = side.cross(tangent).normalized()
        w, h = cross[min(i, len(cross)-1)]
        ww, hh = fr.size.x * w, min(fr.size) * h
        rings.append([c + side*ww*0.5 + upv*hh*0.5, c - side*ww*0.5 + upv*hh*0.5,
                      c - side*ww*0.5 - upv*hh*0.5, c + side*ww*0.5 - upv*hh*0.5])
    verts = [v for r in rings for v in r]
    faces = []
    for i in range(m - 1):
        a, b = i * 4, (i + 1) * 4
        for k in range(4):
            kn = (k + 1) % 4
            faces.append((a + k, a + kn, b + kn, b + k))
    faces.append((0, 1, 2, 3))
    last = (m - 1) * 4
    faces.append((last + 3, last + 2, last + 1, last))
    me = bpy.data.meshes.new(name + "M")
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    return _finish(o, material)

def build_weapon(style, drawn, fr):
    M = {
        "wood": mat("PZC_wood", (0.3, 0.15, 0.05, 1)),
        "metal": mat("PZC_metal", (0.05, 0.05, 0.06, 1)),
        "steel": mat("PZC_steel", (0.15, 0.15, 0.16, 1)),
        "cord": mat("PZC_cord", (0.7, 0.7, 0.6, 1))
    }
    
    # Stock (Central Axis)
    stock_w = 0.08 if style != "hand" else 0.06
    box(fr, "stock", (0.5, 0.45, 0.4), (stock_w, 0.2, 0.8), M["wood"])
    
    # Riser (Front Block)
    box(fr, "riser", (0.5, 0.42, 0.85), (0.15, 0.15, 0.1), M["metal"])
    
    # Limbs (Mirrored Symmetry)
    z_root, z_tip = 0.85, 0.92
    y_lvl = 0.42
    
    def get_limb_pts(side_sign):
        pts = []
        for i in range(6):
            t = i / 5.0
            nx = 0.5 + side_sign * (0.45 * t)
            nz = z_root + (z_tip - z_root) * t - (0.05 * math.sin(t * 3.14))
            pts.append(fr.P(nx, y_lvl, nz))
        return pts

    lw = [(0.08, 0.04)] * 6
    swept_limb(fr, "limbL", get_limb_pts(-1), lw, M["wood"])
    swept_limb(fr, "limbR", get_limb_pts(1), lw, M["wood"])
    
    # String
    nock_z = 0.55 if drawn else 0.88
    tipL, tipR = fr.P(0.05, y_lvl, z_tip), fr.P(0.95, y_lvl, z_tip)
    nock = fr.P(0.5, y_lvl, nock_z)
    
    for name, tip in [("strL", tipL), ("strR", tipR)]:
        d = nock - tip
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.005, depth=d.length, location=(tip+nock)*0.5)
        o = bpy.context.object; o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        _finish(o, M["cord"])

def export_one(fname, style, drawn):
    clear(); PARTS.clear()
    bpy.ops.import_scene.fbx(filepath=str(REF / fname))
    ref = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    ref_matrix = ref.matrix_world.copy()
    mn, mx, size = world_bounds(ref)
    clear()
    
    fr = Frame(mn, size)
    build_weapon(style, drawn, fr)
    
    # Join parts
    bpy.ops.object.select_all(action="DESELECT")
    for o in PARTS: o.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    new = bpy.context.view_layer.objects.active
    
    # Move to reference local space
    inv = ref_matrix.inverted()
    for v in new.data.vertices: v.co = inv @ v.co
    new.matrix_world = ref_matrix
    new.name = "PZC_" + fname.replace(".fbx", "")
    
    bpy.ops.export_scene.fbx(filepath=str(OUT / fname), use_selection=True, object_types={"MESH"}, 
                             add_leaf_bones=False, bake_space_transform=False, apply_unit_scale=True)
    print(f"Exported: {fname}")

def main():
    for fname, (style, drawn) in MODELS.items():
        export_one(fname, style, drawn)
    print("FINISHED MODELS V2")

if __name__ == "__main__":
    main()
