"""Surface-mounted, render-first detail candidates for Improved and Compound."""

from pathlib import Path
import math

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


REPO = Path(__file__).resolve().parents[2]
BLENDER = REPO / "blender"

DESIGNS = (
    ("improved_crossbow", "ImprovedCrossBow", "improved"),
    ("compound_crossbow", "CompoundCrossBow", "compound"),
)
UV = {
    "PZC_metal": (0.18, 0.84),
    "PZC_steel": (0.62, 0.50),
    "PZC_grip": (0.12, 0.78),
}


def add_box(vertices, faces, materials, centre, size, material):
    cx, cy, cz = centre
    sx, sy, sz = (value * .5 for value in size)
    start = len(vertices)
    vertices.extend(((cx-sx,cy-sy,cz-sz),(cx+sx,cy-sy,cz-sz),(cx+sx,cy+sy,cz-sz),(cx-sx,cy+sy,cz-sz),(cx-sx,cy-sy,cz+sz),(cx+sx,cy-sy,cz+sz),(cx+sx,cy+sy,cz+sz),(cx-sx,cy+sy,cz+sz)))
    faces.extend(((start,start+3,start+2,start+1),(start+4,start+5,start+6,start+7),(start,start+1,start+5,start+4),(start+1,start+2,start+6,start+5),(start+2,start+3,start+7,start+6),(start+3,start,start+4,start+7)))
    materials.extend((material,) * 6)


def add_cylinder_y(vertices, faces, materials, centre, radius, depth, material, segments=10):
    cx, cy, cz = centre
    start = len(vertices)
    for y in (cy-depth*.5, cy+depth*.5):
        for index in range(segments):
            angle = math.tau * index / segments
            vertices.append((cx+math.cos(angle)*radius,y,cz+math.sin(angle)*radius))
    for index in range(segments):
        nxt = (index+1) % segments
        faces.append((start+index,start+nxt,start+segments+nxt,start+segments+index))
        materials.append(material)
    faces.extend((tuple(start+i for i in range(segments)),tuple(start+segments+i for i in range(segments))))
    materials.extend((material,material))


def make_tree(mesh):
    vertices = [vertex.co.copy() for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    return BVHTree.FromPolygons(vertices, polygons)


def front_surface(tree, x, z, y_min, y_span):
    hit, _normal, _index, _distance = tree.ray_cast(Vector((x, y_min-y_span, z)), Vector((0,1,0)), y_span*3)
    return hit.y if hit else None


def surface_box(vertices, faces, materials, tree, x, z, size, y_min, y_span, material):
    y = front_surface(tree, x, z, y_min, y_span)
    if y is not None:
        add_box(vertices, faces, materials, (x, y-size[1]*.45, z), size, material)


def surface_rivet(vertices, faces, materials, tree, x, z, radius, depth, y_min, y_span, material):
    y = front_surface(tree, x, z, y_min, y_span)
    if y is not None:
        add_cylinder_y(vertices, faces, materials, (x, y-depth*.45, z), radius, depth, material)


def detail_object(base, style):
    points = [vertex.co for vertex in base.data.vertices]
    lo = [min(point[i] for point in points) for i in range(3)]
    hi = [max(point[i] for point in points) for i in range(3)]
    dx, dy, dz = (hi[i]-lo[i] for i in range(3))
    cx = (lo[0]+hi[0])*.5
    bow_z = lo[2]+dz*.095
    tree = make_tree(base.data)
    verts, faces, mats = [], [], []

    # Receiver faceplate and brass-like rivets: all surface-mounted.
    surface_box(verts,faces,mats,tree,cx,bow_z+dz*.070,(dx*.16,dy*.055,dz*.075),lo[1],dy,"PZC_steel")
    for offset in (-.045,.045):
        surface_rivet(verts,faces,mats,tree,cx+dx*offset,bow_z+dz*.070,dx*.010,dy*.040,lo[1],dy,"PZC_metal")
    # Two short leather bands on the stock, set exactly against its front face.
    for fraction in (.57,.68):
        z = lo[2]+dz*fraction
        surface_box(verts,faces,mats,tree,cx,z,(dx*.14,dy*.040,dz*.018),lo[1],dy,"PZC_grip")

    if style == "improved":
        # A compact raised sight base, deliberately shorter than the receiver.
        surface_box(verts,faces,mats,tree,cx,bow_z+dz*.145,(dx*.11,dy*.060,dz*.055),lo[1],dy,"PZC_metal")
        for z_fraction in (.25,.38):
            surface_rivet(verts,faces,mats,tree,cx,lo[2]+dz*z_fraction,dx*.011,dy*.040,lo[1],dy,"PZC_steel")
    else:
        # Compound: small cam covers fitted to the limb faces, not added beyond
        # the original limb width.
        for side in (-1,1):
            x = cx+side*dx*.365
            z = bow_z+dz*.012
            surface_rivet(verts,faces,mats,tree,x,z,dx*.026,dy*.060,lo[1],dy,"PZC_steel")
        surface_box(verts,faces,mats,tree,cx,bow_z+dz*.155,(dx*.14,dy*.065,dz*.060),lo[1],dy,"PZC_metal")

    mesh = bpy.data.meshes.new(f"{base.name}_RefinedDetailMesh")
    mesh.from_pydata(verts,[],faces)
    for material in base.data.materials:
        mesh.materials.append(material)
    indices = {material.name:index for index,material in enumerate(mesh.materials) if material}
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon,name in zip(mesh.polygons,mats):
        polygon.material_index = indices[name]
        for loop in polygon.loop_indices:
            uv_layer.data[loop].uv = UV[name]
    obj = bpy.data.objects.new(f"{base.name}_RefinedDetails",mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = base.matrix_world.copy()
    return obj


def compact_slots(base):
    first = {}
    for index, material in enumerate(base.data.materials):
        if material and material.name not in first:
            first[material.name] = index
    for polygon in base.data.polygons:
        material = base.data.materials[polygon.material_index]
        if material:
            polygon.material_index = first[material.name]
    for index in range(len(base.data.materials)-1,-1,-1):
        material = base.data.materials[index]
        if material and first[material.name] != index:
            base.data.materials.pop(index=index)


def build(folder_name, model, style, drawn):
    folder = BLENDER / folder_name
    name = model+("Drawn" if drawn else "")
    source = folder / "backup" / "game_current" / "models" / f"{name}.fbx"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source))
    base = next(obj for obj in bpy.context.scene.objects if obj.type=="MESH")
    detail = detail_object(base,style)
    bpy.ops.object.select_all(action="DESELECT")
    base.select_set(True);detail.select_set(True);bpy.context.view_layer.objects.active=base
    bpy.ops.object.join()
    # Softened edges make the low-poly stock and new plates less plastic.
    bevel = base.modifiers.new("Refined edge bevel","BEVEL")
    local_points = [vertex.co for vertex in base.data.vertices]
    local_span = max(max(point[i] for point in local_points) - min(point[i] for point in local_points) for i in range(3))
    bevel.width = local_span * .0035
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    compact_slots(base)
    base.data.transform(Matrix.Rotation(math.pi,4,"Z"))
    base.name = f"PZC_{name}"
    out = folder / "work" / "models" / f"{name}_refined_candidate.fbx"
    bpy.ops.export_scene.fbx(filepath=str(out),use_selection=False,object_types={"MESH"},add_leaf_bones=False,bake_anim=False)
    if not drawn:
        bpy.ops.wm.save_as_mainfile(filepath=str(folder / "work" / "models" / f"{name}_refined_candidate.blend"))


for folder,model,style in DESIGNS:
    build(folder,model,style,False)
    build(folder,model,style,True)
    print(f"Refined candidate ready: {model}")
