"""Add surface-aligned loaded bolts to Improved and Compound Drawn models."""

from pathlib import Path
import math

import bpy


REPO = Path(__file__).resolve().parents[2]
MODEL_TARGET = REPO / "PZCrossbows" / "Contents" / "mods" / "PZCrossbows" / "42" / "media" / "models_x" / "weapons" / "firearm"
WORK = REPO / "blender"


def cylinder_z(vertices, faces, materials, centre, radius, depth, material, segments=10):
    cx, cy, cz = centre
    start = len(vertices)
    for z in (cz-depth*.5, cz+depth*.5):
        for index in range(segments):
            angle=math.tau*index/segments
            vertices.append((cx+math.cos(angle)*radius,cy+math.sin(angle)*radius,z))
    for index in range(segments):
        nxt=(index+1)%segments
        faces.append((start+index,start+nxt,start+segments+nxt,start+segments+index))
        materials.append(material)
    faces.extend((tuple(start+i for i in range(segments)),tuple(start+segments+i for i in range(segments))))
    materials.extend((material,material))


def cone_z(vertices, faces, materials, centre, radius, depth, material, segments=10):
    cx,cy,cz=centre
    start=len(vertices)
    vertices.append((cx,cy,cz-depth*.5))
    for index in range(segments):
        angle=math.tau*index/segments
        vertices.append((cx+math.cos(angle)*radius,cy+math.sin(angle)*radius,cz+depth*.5))
    for index in range(segments):
        nxt=(index+1)%segments
        faces.append((start,start+1+nxt,start+1+index));materials.append(material)
    faces.append(tuple(start+1+i for i in range(segments)));materials.append(material)


def fletching(vertices, faces, materials, centre, size, material):
    cx,cy,cz=centre
    sx,sy,sz=size
    start=len(vertices)
    vertices.extend(((cx-sx,cy,cz-sz),(cx+sx,cy,cz-sz),(cx+sx,cy,cz+sz),(cx-sx,cy,cz+sz),(cx,cy-sy,cz-sz),(cx,cy-sy,cz+sz)))
    faces.extend(((start,start+1,start+2,start+3),(start,start+4,start+5,start+3)))
    materials.extend((material,material))


def add_bolt(path, work_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    base=next(obj for obj in bpy.context.scene.objects if obj.type=='MESH')
    points=[v.co for v in base.data.vertices]
    lo=[min(p[i] for p in points) for i in range(3)]
    hi=[max(p[i] for p in points) for i in range(3)]
    dx,dy,dz=(hi[i]-lo[i] for i in range(3))
    cx=(lo[0]+hi[0])*.5
    # The bow/muzzle is local Z minimum for both long crossbows.
    shaft_start=lo[2]+dz*.10
    shaft_end=lo[2]+dz*.70
    front_y=lo[1]-dy*.012
    shaft_material='PZC_wood' if any(m and m.name=='PZC_wood' for m in base.data.materials) else 'PZC_grip'
    verts=[];faces=[];mats=[]
    cylinder_z(verts,faces,mats,(cx,front_y,(shaft_start+shaft_end)*.5),dx*.012,shaft_end-shaft_start,shaft_material)
    cone_z(verts,faces,mats,(cx,front_y,shaft_start-dz*.035),dx*.038,dz*.075,'PZC_steel')
    fletching(verts,faces,mats,(cx,front_y,shaft_end-dz*.05),(dx*.025,dy*.05,dz*.050),'PZC_grip')
    mesh=bpy.data.meshes.new(f'{base.name}_LoadedBolt')
    mesh.from_pydata(verts,[],faces)
    for material in base.data.materials: mesh.materials.append(material)
    indices={m.name:i for i,m in enumerate(mesh.materials) if m}
    uv=mesh.uv_layers.new(name='UVMap')
    centres={'PZC_wood':(.5,.5),'PZC_grip':(.5,.5),'PZC_steel':(.62,.5)}
    for polygon,name in zip(mesh.polygons,mats):
        polygon.material_index=indices[name]
        for loop in polygon.loop_indices: uv.data[loop].uv=centres[name]
    bolt=bpy.data.objects.new(f'{base.name}_LoadedBolt',mesh)
    bpy.context.scene.collection.objects.link(bolt);bolt.matrix_world=base.matrix_world.copy()
    bpy.ops.object.select_all(action='DESELECT');base.select_set(True);bolt.select_set(True);bpy.context.view_layer.objects.active=base;bpy.ops.object.join()
    bpy.ops.export_scene.fbx(filepath=str(work_path),use_selection=False,object_types={'MESH'},add_leaf_bones=False,bake_anim=False)


for folder,model in (('improved_crossbow','ImprovedCrossBow'),('compound_crossbow','CompoundCrossBow')):
    game=MODEL_TARGET/f'{model}Drawn.fbx'
    candidate=WORK/folder/'work'/'models'/f'{model}Drawn_loaded_candidate.fbx'
    add_bolt(game,candidate)
    print(f'Loaded bolt candidate ready: {model}')
