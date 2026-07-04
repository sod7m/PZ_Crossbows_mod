"""Render original 32x32 item icons from our own models (transparent bg).

Renders each item at 256x256 with alpha then downscales to 32x32.
Run: blender --background --python render_icons.py -- <models_dir> <weapon_tex_dir> <out_icons_dir>
"""
import bmesh
import bpy
import math
import sys
from mathutils import Vector
from pathlib import Path

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODELS = Path(argv[0])
WTEX = Path(argv[1])
OUT = Path(argv[2])
OUT.mkdir(parents=True, exist_ok=True)
TMP = OUT / "_tmp256.png"

# icon name, kind, source-fbx (or None), texture png (or None)
ITEMS = [
    ("CrossBow", "xbow", "CrossBow.fbx", "CrossBow.png"),
    ("CrossBowDrawn", "xbow", "CrossBowDrawn.fbx", "CrossBow.png"),
    ("ImprovedCrossBow", "xbow", "ImprovedCrossBow.fbx", "CrossBow.png"),
    ("ImprovedCrossBowDrawn", "xbow", "ImprovedCrossBowDrawn.fbx", "CrossBow.png"),
    ("CompoundCrossBow", "xbow", "CompoundCrossBow.fbx", "CompoundCrossBow.png"),
    ("CompoundCrossBowDrawn", "xbow", "CompoundCrossBowDrawn.fbx", "CompoundCrossBow.png"),
    ("HandCrossBow", "xbow", "HandCrossBow.fbx", "HandCrossBow.png"),
    ("HandCrossBowDrawn", "xbow", "HandCrossBowDrawn.fbx", "HandCrossBow.png"),
    ("WoodBolt", "bolt", "WoodBolt.fbx", "WoodBolt.png"),
    ("ShortWoodBolt", "bolt", "ShortWoodBolt.fbx", "WoodBolt.png"),
    ("BrokenWoodBolt", "bolt", "WoodBoltBroken.fbx", "WoodBolt.png"),
    ("ShortBrokenWoodBolt", "bolt", "WoodBoltBroken.fbx", "WoodBolt.png"),
    ("WoodBoltShaft", "shaft", None, None),
    ("ShortWoodBoltShaft", "shaft_short", None, None),
    ("StoneBoltHead", "stone", None, None),
]


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for b in list(c):
            if b.users == 0 and b.name not in ("Render Result", "Viewer Node"):
                try:
                    c.remove(b)
                except Exception:
                    pass


def bounds(o):
    p = [o.matrix_world @ v.co for v in o.data.vertices]
    return (Vector((min(x.x for x in p), min(x.y for x in p), min(x.z for x in p))),
            Vector((max(x.x for x in p), max(x.y for x in p), max(x.z for x in p))))


def join_sel():
    objs = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def tex_material(name, tex_png):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.65
    if tex_png:
        img = bpy.data.images.load(str(WTEX / tex_png), check_existing=True)
        tn = m.node_tree.nodes.new("ShaderNodeTexImage")
        tn.image = img
        m.node_tree.links.new(tn.outputs["Color"], b.inputs["Base Color"])
    return m


def flat_material(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.8
    return m


def make_object(kind, fbx, tex):
    if fbx:
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.fbx(filepath=str(MODELS / fbx))
        objs = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        o = join_sel()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        mat = tex_material("icm", tex)
        o.data.materials.clear()
        o.data.materials.append(mat)
        return o
    # procedural component icons
    if kind in ("shaft", "shaft_short"):
        length = 1.0 if kind == "shaft" else 0.62
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.03, depth=length)
        o = bpy.context.object
        o.rotation_euler = (0, math.radians(90), 0)
        bpy.ops.object.transform_apply(rotation=True)
        o.data.materials.append(flat_material("shaft", (0.44, 0.25, 0.11)))
        for p in o.data.polygons:
            p.use_smooth = True
        return o
    if kind == "stone":
        # flattened knapped triangular head
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in [
            (0.5, 0, 0), (-0.5, 0.28, 0.05), (-0.5, -0.28, 0.05),
            (-0.5, 0.28, -0.05), (-0.5, -0.28, -0.05), (-0.62, 0, 0)]]
        bm.faces.new([v[0], v[1], v[2]])
        bm.faces.new([v[0], v[4], v[3]])
        bm.faces.new([v[1], v[5], v[2]])
        bm.faces.new([v[3], v[5], v[4]])
        bm.faces.new([v[0], v[3], v[1]])
        bm.faces.new([v[0], v[2], v[4]])
        bm.faces.new([v[1], v[3], v[5]])
        bm.faces.new([v[2], v[5], v[4]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new("stone")
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("stone", me)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(flat_material("stone", (0.40, 0.40, 0.43)))
        return o


def render_icon(name, kind, fbx, tex):
    clear()
    o = make_object(kind, fbx, tex)
    # normalize + centre
    mn, mx = bounds(o)
    sz = mx - mn
    m = max(sz)
    o.scale = (1 / m,) * 3
    bpy.ops.object.transform_apply(scale=True)
    mn, mx = bounds(o)
    o.location -= (mn + mx) * 0.5
    # long thin items look better on a diagonal
    if kind in ("bolt", "shaft", "shaft_short", "stone"):
        o.rotation_euler = (math.radians(18), math.radians(8), math.radians(38))
        bpy.ops.object.transform_apply(rotation=True)
        mn, mx = bounds(o)
        o.location -= (mn + mx) * 0.5
    # camera + light
    for ob in [x for x in bpy.context.scene.objects if x.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(ob, do_unlink=True)
    mn, mx = bounds(o)
    span = mx - mn
    if kind == "xbow":
        d = Vector((0.75, -1.0, 0.65)).normalized()
        osc = max(span.x, span.z) * 1.06
    else:
        d = Vector((0.15, -1.0, 0.32)).normalized()
        osc = max(span) * 1.08
    loc = d * 8
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.rotation_euler = (-loc).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = osc
    bpy.context.scene.camera = cam
    bpy.ops.object.light_add(type="SUN", location=(3, -4, 6))
    L = bpy.context.object
    L.data.energy = 4.0
    L.rotation_euler = (math.radians(50), math.radians(12), math.radians(35))
    bpy.ops.object.light_add(type="SUN")
    L2 = bpy.context.object
    L2.data.energy = 1.3
    L2.rotation_euler = (math.radians(-40), 0, math.radians(-120))
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except Exception:
        pass
    try:
        sc.eevee.taa_render_samples = 64
    except Exception:
        pass
    sc.view_settings.view_transform = "Standard"
    # soft ambient fill so shadowed sides aren't pure black
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.62, 0.68, 1)
    bg.inputs["Strength"].default_value = 0.55
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x = 256
    sc.render.resolution_y = 256
    sc.render.filepath = str(TMP)
    bpy.ops.render.render(write_still=True)
    # downscale 256 -> 32
    im = bpy.data.images.load(str(TMP))
    im.scale(32, 32)
    im.filepath_raw = str(OUT / f"Item_{name}.png")
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    print("icon", name)


def main():
    only = argv[3:] if len(argv) > 3 else []
    for name, kind, fbx, tex in ITEMS:
        if only and name not in only:
            continue
        render_icon(name, kind, fbx, tex)
    if TMP.exists():
        TMP.unlink()
    print("ALL DONE")


if __name__ == "__main__":
    main()
