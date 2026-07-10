"""Build restrained, review-first detail candidates for the three crossbows."""

from pathlib import Path
import math
import shutil

import bpy


REPO = Path(__file__).resolve().parents[2]
BLENDER = REPO / "blender"
CRUDE_ATLAS = REPO / "PZCrossbows" / "Contents" / "mods" / "PZCrossbows" / "42" / "media" / "textures" / "weapons" / "firearm" / "CrossBow_Detailed.png"

DESIGNS = (
    ("improved_crossbow", "ImprovedCrossBow", "improved"),
    ("compound_crossbow", "CompoundCrossBow", "compound"),
    ("hand_crossbow", "HandCrossBow", "hand"),
)
UV = {
    "PZC_metal": (0.18, 0.84),
    "PZC_steel": (0.62, 0.50),
    "PZC_grip": (0.12, 0.78),
    "PZC_cord": (0.14, 0.38),
}


def box(vertices, faces, material_names, centre, size, material):
    cx, cy, cz = centre
    sx, sy, sz = (value * 0.5 for value in size)
    start = len(vertices)
    vertices.extend(((cx-sx,cy-sy,cz-sz),(cx+sx,cy-sy,cz-sz),(cx+sx,cy+sy,cz-sz),(cx-sx,cy+sy,cz-sz),(cx-sx,cy-sy,cz+sz),(cx+sx,cy-sy,cz+sz),(cx+sx,cy+sy,cz+sz),(cx-sx,cy+sy,cz+sz)))
    faces.extend(((start,start+3,start+2,start+1),(start+4,start+5,start+6,start+7),(start,start+1,start+5,start+4),(start+1,start+2,start+6,start+5),(start+2,start+3,start+7,start+6),(start+3,start,start+4,start+7)))
    material_names.extend((material,) * 6)


def cam(vertices, faces, material_names, centre, radius, depth, material, segments=8):
    cx, cy, cz = centre
    start = len(vertices)
    for y in (cy - depth * .5, cy + depth * .5):
        for i in range(segments):
            a = math.tau * i / segments
            vertices.append((cx + math.cos(a) * radius, y, cz + math.sin(a) * radius))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((start+i,start+j,start+segments+j,start+segments+i))
        material_names.append(material)
    faces.extend((tuple(start+i for i in range(segments)),tuple(start+segments+i for i in range(segments))))
    material_names.extend((material, material))


def build(base, style):
    points = [vertex.co for vertex in base.data.vertices]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    dx, dy, dz = (hi[i] - lo[i] for i in range(3))
    cx = (lo[0] + hi[0]) * .5
    cy = (lo[1] + hi[1]) * .5
    verts, faces, mats = [], [], []

    if style != "hand":
        # Improved and Compound have a 180° root rotation: their bow sits at
        # local Z minimum, while the stock runs toward local Z maximum.
        fy = lo[1] - dy * .015
        bow_z = lo[2] + dz * .095
        box(verts, faces, mats, (cx, fy, bow_z + dz*.055), (dx*.12, dy*.09, dz*.060), "PZC_steel")
        box(verts, faces, mats, (cx, fy, lo[2] + dz*.53), (dx*.09, dy*.060, dz*.045), "PZC_metal")
        for fraction in (.62, .70):
            box(verts, faces, mats, (cx, fy, lo[2] + dz*fraction), (dx*.12, dy*.045, dz*.010), "PZC_grip")
        if style == "improved":
            box(verts, faces, mats, (cx, fy, bow_z + dz*.115), (dx*.095, dy*.085, dz*.055), "PZC_metal")
        else:
            box(verts, faces, mats, (cx, fy, bow_z + dz*.12), (dx*.14, dy*.09, dz*.055), "PZC_steel")
    else:
        # Hand Crossbow has a Z-90 root rotation: local X is screen depth and
        # local Y spans the bow.  Keep every part flush to local X minimum.
        fx = lo[0] - dx * .014
        bow_z = hi[2] - dz * .095
        box(verts, faces, mats, (fx, cy, bow_z - dz*.055), (dx*.080, dy*.12, dz*.060), "PZC_steel")
        box(verts, faces, mats, (fx, cy, lo[2] + dz*.49), (dx*.060, dy*.09, dz*.050), "PZC_metal")
        for fraction in (.27, .36):
            box(verts, faces, mats, (fx, cy, lo[2] + dz*fraction), (dx*.045, dy*.12, dz*.012), "PZC_grip")

    mesh = bpy.data.meshes.new(f"{base.name}_ConservativeDetails")
    mesh.from_pydata(verts, [], faces)
    for material in base.data.materials:
        mesh.materials.append(material)
    indices = {m.name: i for i, m in enumerate(mesh.materials) if m}
    uv = mesh.uv_layers.new(name="UVMap")
    for polygon, name in zip(mesh.polygons, mats):
        polygon.material_index = indices[name]
        for loop in polygon.loop_indices:
            uv.data[loop].uv = UV[name]
    obj = bpy.data.objects.new(f"{base.name}_ConservativeDetails", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = base.matrix_world.copy()
    return obj


def candidate(folder_name, model, style, drawn):
    folder = BLENDER / folder_name
    filename = model + ("Drawn" if drawn else "")
    source = folder / "backup" / "game_current" / "models" / f"{filename}.fbx"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source))
    base = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
    detail = build(base, style)
    bpy.ops.object.select_all(action="DESELECT")
    base.select_set(True)
    detail.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    base.name = f"PZC_{filename}"
    out = folder / "work" / "models" / f"{filename}_candidate.fbx"
    bpy.ops.export_scene.fbx(filepath=str(out), use_selection=False, object_types={"MESH"}, add_leaf_bones=False, bake_anim=False)
    if not drawn:
        bpy.ops.wm.save_as_mainfile(filepath=str(folder / "work" / "models" / f"{filename}_candidate.blend"))


for folder, model, style in DESIGNS:
    candidate(folder, model, style, False)
    candidate(folder, model, style, True)
    shutil.copyfile(CRUDE_ATLAS, BLENDER / folder / "work" / "textures" / f"{model}_candidate.png")
    print(f"Candidate ready: {model}")
