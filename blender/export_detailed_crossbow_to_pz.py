"""Export the detailed Blender crossbow as PZ-ready empty and drawn models.

The original game's CrossBow UVs stay untouched.  New detail meshes are
collapsed into small, appropriate colour regions of the existing crossbow
texture atlas, so the PZ model definition can still use one texture.
"""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


ROOT = Path(r"E:\PZCrossbows")
DETAIL_SOURCE = ROOT / "blender" / "CrossBow_Detailed.fbx"
ORIGINALS = ROOT / "blender" / "original_game_assets"
TARGET = ROOT / "PZCrossbows" / "Contents" / "mods" / "PZCrossbows" / "42" / "media" / "models_x" / "weapons" / "firearm"

# UV centres in the original CrossBow texture: lower-left is walnut, upper-left
# is blackened iron, and the centre/right area is cool steel grey.
ATLAS_CENTRES = {
    "M_Walnut": (0.14, 0.16),
    "M_Wood_Inlay": (0.18, 0.26),
    "M_Leather": (0.12, 0.78),
    "M_Blackened_Iron": (0.18, 0.84),
    "M_Antique_Bronze": (0.18, 0.30),
    "M_Waxed_Cord": (0.14, 0.38),
    "M_Bolt_Steel": (0.62, 0.50),
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_mesh(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    return [obj for obj in bpy.context.scene.objects if obj not in before and obj.type == "MESH"]


def remap_detail_uvs(objects):
    for obj in objects:
        uv_layer = obj.data.uv_layers.active
        if uv_layer is None:
            uv_layer = obj.data.uv_layers.new(name="UVMap")
        material_name = obj.active_material.name if obj.active_material else "M_Blackened_Iron"
        centre_u, centre_v = ATLAS_CENTRES.get(material_name, ATLAS_CENTRES["M_Blackened_Iron"])
        # Retain a tiny amount of variation from the source UVs while forcing
        # each material into its correct atlas swatch.
        for loop in uv_layer.data:
            loop.uv.x = centre_u + (loop.uv.x - 0.5) * 0.035
            loop.uv.y = centre_v + (loop.uv.y - 0.5) * 0.035


def export_model(filename, original_filename, remove_loaded_bolt):
    # The working PZ mesh is the active object.  Joining new vertices into it
    # retains its root rotation, unit scale and node layout exactly, instead of
    # exporting a hierarchy of independent objects PZ cannot attach correctly.
    reset_scene()
    base_meshes = import_mesh(ORIGINALS / original_filename)
    if len(base_meshes) != 1:
        raise RuntimeError(f"Expected one working base mesh in {original_filename}")
    base = base_meshes[0]
    detail_meshes = import_mesh(DETAIL_SOURCE)
    for obj in list(detail_meshes):
        if obj.name.startswith("PZC_CrossBow_Base"):
            bpy.data.objects.remove(obj, do_unlink=True)
            detail_meshes.remove(obj)
    if remove_loaded_bolt:
        for obj in list(detail_meshes):
            if obj.name.startswith(("Loaded_Bolt_", "Bolt_Fletching_")):
                bpy.data.objects.remove(obj, do_unlink=True)
                detail_meshes.remove(obj)
    remap_detail_uvs(detail_meshes)
    bpy.ops.object.select_all(action="DESELECT")
    base.select_set(True)
    for obj in detail_meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    base.name = "PZC_CrossBowDrawn" if "Drawn" in filename else "PZC_CrossBow"
    # The PZ renderer recognises the original PZC_* material slots (0-7).
    # New Blender-only slots were being treated as wood in-game, so fold each
    # detail component into the matching original slot before export.
    slot_by_name = {material.name: index for index, material in enumerate(base.data.materials) if material}
    slot_remap = {
        "M_Wood_Inlay": "PZC_wood2",
        "M_Leather": "PZC_grip",
        "M_Waxed_Cord": "PZC_cord",
        "M_Antique_Bronze": "PZC_metal",
        "M_Blackened_Iron": "PZC_metal",
        "M_Bolt_Steel": "PZC_steel",
    }
    for polygon in base.data.polygons:
        source = base.data.materials[polygon.material_index]
        target_name = slot_remap.get(source.name if source else "")
        if target_name and target_name in slot_by_name:
            polygon.material_index = slot_by_name[target_name]
    for index in range(len(base.data.materials) - 1, -1, -1):
        material = base.data.materials[index]
        if material and material.name.startswith("M_"):
            base.data.materials.pop(index=index)
    # PZ uses this mesh's local Y axis as the weapon's longitudinal axis.
    # Flip only the visible geometry so the opposite face points upward while
    # retaining the original object's transform and all model attachments.
    base.data.transform(Matrix.Rotation(math.pi, 4, "Y"))
    bpy.ops.export_scene.fbx(
        filepath=str(TARGET / filename),
        use_selection=False,
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )


export_model("CrossBow.fbx", "CrossBow.fbx", remove_loaded_bolt=True)
export_model("CrossBowDrawn.fbx", "CrossBowDrawn.fbx", remove_loaded_bolt=False)
print("Exported PZ CrossBow.fbx and CrossBowDrawn.fbx")
