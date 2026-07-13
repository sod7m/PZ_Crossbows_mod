"""Build a compact right-thigh crossbow-bolt pouch for Project Zomboid B42."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

from build_quiver_final import (
    MOD,
    OUT,
    REF,
    MeshBuilder,
    compute_normals,
    mesh_block,
    parse_mesh,
    render_mesh,
    unit,
    v3,
    write_obj,
)


def add_solid_thigh_band(builder, x, radius_y, radius_z, width=0.014, thickness=0.004, segments=16):
    """Closed elliptical band with inner faces, so backface culling cannot make it disappear."""
    rings = {key: [] for key in ("outer0", "outer1", "inner0", "inner1")}
    for i in range(segments + 1):
        angle = 2 * np.pi * i / segments
        c, s = float(np.cos(angle)), float(np.sin(angle))
        u = i / segments
        for key, px, ry, rz, v in (
            ("outer0", x - width / 2, radius_y, radius_z, 0.05),
            ("outer1", x + width / 2, radius_y, radius_z, 0.12),
            ("inner0", x - width / 2, radius_y - thickness, radius_z - thickness, 0.15),
            ("inner1", x + width / 2, radius_y - thickness, radius_z - thickness, 0.22),
        ):
            rings[key].append(builder.add_vertex((px, c * ry, s * rz), (u, v)))
    for i in range(segments):
        o0, o1 = rings["outer0"], rings["outer1"]
        n0, n1 = rings["inner0"], rings["inner1"]
        for face in (
            (o0[i], o0[i + 1], o1[i + 1]), (o0[i], o1[i + 1], o1[i]),
            (n0[i], n1[i + 1], n0[i + 1]), (n0[i], n1[i], n1[i + 1]),
            (o0[i], n0[i + 1], o0[i + 1]), (o0[i], n0[i], n0[i + 1]),
            (o1[i], o1[i + 1], n1[i + 1]), (o1[i], n1[i + 1], n1[i]),
        ):
            builder.add_face(face, "dark_leather")


def add_flat_carrier(builder, female=False):
    """A thin, gently curved leather cassette that follows the thigh surface."""
    pouch_y = -0.034 if female else -0.037
    pouch_z = 0.029 if female else 0.032
    normal = unit((0.0, pouch_y, pouch_z))
    tangent = unit((0.0, -normal[2], normal[1]))
    axis = v3((-1.0, 0.0, 0.0))
    upper_x, lower_x = 0.058, 0.184
    half_width = 0.034 if female else 0.037
    base_radius = 0.044 if female else 0.047
    thickness = 0.014
    rows = ((upper_x, 0.90), (upper_x + 0.007, 1.0), (lower_x - 0.007, 1.0), (lower_x, 0.88))
    columns = np.linspace(-half_width, half_width, 5)
    back, front = [], []
    for row_index, (x, width_scale) in enumerate(rows):
        back_row, front_row = [], []
        for col_index, raw_w in enumerate(columns):
            w = float(raw_w * width_scale)
            curve = -0.008 * (abs(raw_w) / half_width) ** 2
            inner = v3((x, 0, 0)) + normal * (base_radius + curve) + tangent * w
            outer = inner + normal * thickness
            uv = (0.08 + col_index * 0.21, 0.05 + row_index * 0.20)
            back_row.append(builder.add_vertex(inner, uv))
            front_row.append(builder.add_vertex(outer, uv))
        back.append(back_row)
        front.append(front_row)

    for r in range(len(rows) - 1):
        for c in range(len(columns) - 1):
            # Front faces point away from the leg; back faces point inward.
            builder.add_face((front[r][c], front[r][c + 1], front[r + 1][c + 1]), "leather")
            builder.add_face((front[r][c], front[r + 1][c + 1], front[r + 1][c]), "leather")
            builder.add_face((back[r][c], back[r + 1][c + 1], back[r][c + 1]), "dark_leather")
            builder.add_face((back[r][c], back[r + 1][c], back[r + 1][c + 1]), "dark_leather")
    for c in range(len(columns) - 1):
        builder.add_face((back[0][c], back[0][c + 1], front[0][c + 1]), "dark_leather")
        builder.add_face((back[0][c], front[0][c + 1], front[0][c]), "dark_leather")
        builder.add_face((back[-1][c], front[-1][c + 1], back[-1][c + 1]), "dark_leather")
        builder.add_face((back[-1][c], front[-1][c], front[-1][c + 1]), "dark_leather")
    for r in range(len(rows) - 1):
        for c in (0, len(columns) - 1):
            nr = r + 1
            if c == 0:
                builder.add_face((back[r][c], front[nr][c], back[nr][c]), "dark_leather")
                builder.add_face((back[r][c], front[r][c], front[nr][c]), "dark_leather")
            else:
                builder.add_face((back[r][c], back[nr][c], front[nr][c]), "dark_leather")
                builder.add_face((back[r][c], front[nr][c], front[r][c]), "dark_leather")

    # Raised top and bottom leather rails reinforce the flat cassette shape.
    for x in (upper_x + 0.006, lower_x - 0.006):
        left = v3((x, 0, 0)) + normal * (base_radius + thickness + 0.001) + tangent * (-half_width)
        right = v3((x, 0, 0)) + normal * (base_radius + thickness + 0.001) + tangent * half_width
        builder.add_box_between(left, right, 0.007, 0.004, (0.32, 0.50), "dark_leather")

    # Stitches on both vertical edges remain readable without transparent planes.
    for x in np.linspace(upper_x + 0.018, lower_x - 0.018, 5):
        for w in (-half_width + 0.003, half_width - 0.003):
            center = v3((x, 0, 0)) + normal * (base_radius + thickness + 0.002) + tangent * w
            builder.add_box_between(center - axis * 0.004, center + axis * 0.004, 0.0028, 0.0022)
    return normal, tangent, axis, upper_x, base_radius, thickness, half_width


def make_thigh_pouch(female=False, wearable=True):
    builder = MeshBuilder()
    thigh_y = 0.053 if female else 0.057
    thigh_z = 0.056 if female else 0.059
    normal, tangent, axis, upper_x, base_radius, thickness, half_width = add_flat_carrier(builder, female)

    for x in (0.105, 0.166):
        if wearable:
            add_solid_thigh_band(builder, x, thigh_y, thigh_z)
        else:
            # Relaxed strap tails lie in the carrier plane.  When the front
            # panel is turned face-up for the world model, these also lie flat.
            start = v3((x, 0, 0)) + normal * (base_radius + 0.003) + tangent * (half_width * 0.72)
            builder.add_box_between(start, start + tangent * 0.070, 0.014, 0.005, (0.32, 0.50), "dark_leather")

    # Four parallel bolts form one clear row across the carrier.
    for i, w in enumerate((-0.024, -0.008, 0.008, 0.024)):
        rail = normal * (base_radius + thickness + 0.004) + tangent * w
        inside = v3((0.118, rail[1], rail[2]))
        tail = v3((0.010, rail[1], rail[2]))
        baxis, bside, bdepth = builder.add_cylinder(inside, tail, 0.0018, (0.125, 0.875), "wood", 7)
        builder.add_cylinder(v3((0.080, rail[1], rail[2])), v3((0.070, rail[1], rail[2])), 0.0030, (0.32, 0.50), "dark_leather", 7)
        builder.add_fletching(tail - baxis * 0.023, tail - baxis * 0.003, baxis, bside, bdepth, 0.48 + i * 0.01)
        builder.add_cylinder(tail - baxis * 0.0035, tail + baxis * 0.002, 0.0025, (0.375, 0.875), "metal", 6)
    return builder


def static_mesh_block(name, builder, material_name):
    normals = compute_normals(builder.verts, builder.faces)
    lines = [f"Mesh {name} {{\n {len(builder.verts)};\n"]
    for i, p in enumerate(builder.verts):
        lines.append(f" {p[0]:.6f};{p[1]:.6f};{p[2]:.6f};{',' if i + 1 < len(builder.verts) else ';'}\n")
    lines.append(f" {len(builder.faces)};\n")
    for i, face in enumerate(builder.faces):
        lines.append(f" {len(face)};{','.join(str(x) for x in face)};{',' if i + 1 < len(builder.faces) else ';'}\n")
    lines.append(" MeshNormals {\n")
    lines.append(f"  {len(normals)};\n")
    for i, n in enumerate(normals):
        lines.append(f"  {n[0]:.6f};{n[1]:.6f};{n[2]:.6f};{',' if i + 1 < len(normals) else ';'}\n")
    lines.append(f"  {len(builder.faces)};\n")
    for i, face in enumerate(builder.faces):
        lines.append(f"  {len(face)};{','.join(str(x) for x in face)};{',' if i + 1 < len(builder.faces) else ';'}\n")
    lines.append(" }\n MeshMaterialList {\n  1;\n")
    lines.append(f"  {len(builder.faces)};\n  {','.join('0' for _ in builder.faces)};\n  {{ {material_name} }}\n }}\n")
    lines.append(" MeshTextureCoords c1 {\n")
    lines.append(f"  {len(builder.uvs)};\n")
    for i, (u, v) in enumerate(builder.uvs):
        lines.append(f"  {u:.6f};{v:.6f};{',' if i + 1 < len(builder.uvs) else ';'}\n")
    lines.append(" }\n}\n")
    return "".join(lines)


def write_static(template, template_mesh_name, builder, destination, new_mesh_name):
    text = template.read_text(encoding="utf-8", errors="ignore")
    start, end, _ = mesh_block(text, template_mesh_name)
    material = re.search(r"(?m)^Material\s+([^\s{]+)\s*\{", text).group(1)
    replacement = static_mesh_block(new_mesh_name, builder, material)
    text = text[:start] + replacement + text[end:]
    text = text.replace(f"Frame {template_mesh_name}", f"Frame {new_mesh_name}", 1)
    text = re.sub(r'(TextureFilename\s*\{\s*\n?\s*")[^"]+(";)', r'\1BoltQuiver.png\2', text, count=1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def frame_matrix(text, name):
    start = text.find("Frame " + name)
    matrix_start = text.find("FrameTransformMatrix", start)
    opening = text.find("{", matrix_start)
    closing = text.find(";;", opening)
    values = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text[opening + 1 : closing])]
    return np.asarray(values, dtype=np.float64).reshape(4, 4)


def thigh_world_matrix(skeleton_path):
    text = skeleton_path.read_text(encoding="utf-8", errors="ignore")
    return (
        frame_matrix(text, "Bip01_L_Thigh")
        @ frame_matrix(text, "Bip01_Pelvis")
        @ frame_matrix(text, "Bip01")
        @ frame_matrix(text, "Dummy01")
    )


def transformed_for_preview(builder, matrix):
    local = np.column_stack((np.asarray(builder.verts), np.ones(len(builder.verts))))
    world = local @ matrix
    # PZ original (x, height, depth) -> preview (x, depth, height).
    verts = world[:, [0, 2, 1]]
    return MeshBuilder(verts.tolist(), builder.faces, builder.uvs)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    static_dir = MOD / "models_x/Static/Clothes"
    bob = make_thigh_pouch(False)
    kate = make_thigh_pouch(True)
    world = make_thigh_pouch(False, wearable=False)
    write_static(
        REF / "models/Bob_Thigh_BodyArmour_L.x",
        "Bob_Thigh_BodyArmour_L",
        bob,
        static_dir / "Bob_BoltQuiverThigh.x",
        "Bob_BoltQuiverThigh",
    )
    write_static(
        REF / "models/Kate_Thigh_BodyArmour_L.x",
        "Kate_Thigh_BodyArmour_L",
        kate,
        static_dir / "Kate_BoltQuiverThigh.x",
        "Kate_BoltQuiverThigh",
    )
    write_obj(bob, OUT / "Bob_BoltQuiverThigh.obj")
    write_obj(kate, OUT / "Kate_BoltQuiverThigh.obj")
    write_obj(world, OUT / "BoltQuiverWorld.obj")

    body_mesh = parse_mesh(str(REF / "models/MaleBody.x"))
    body = ([(x, z, y) for x, y, z in body_mesh["verts"]], body_mesh["faces"])
    world_bob = transformed_for_preview(bob, thigh_world_matrix(REF / "models/Bob_AmmoStrap.x"))
    texture = Image.open(MOD / "textures/Clothes/BoltQuiver.png")
    render_mesh(
        world_bob,
        texture,
        body,
        OUT / "quiver_thigh_back_3q.png",
        (0.72, 1.45, 0.60),
        (0.04, 0.04, 0.47),
        760,
    )
    render_mesh(
        world_bob,
        texture,
        body,
        OUT / "quiver_thigh_front_3q.png",
        (0.72, -1.45, 0.58),
        (0.04, 0.00, 0.44),
        760,
    )
    render_mesh(
        world_bob,
        texture,
        None,
        OUT / "quiver_thigh_close.png",
        (0.46, 0.85, 0.45),
        (0.11, 0.02, 0.31),
        1900,
    )
    render_mesh(
        world_bob,
        texture,
        None,
        MOD / "textures/Item_BoltQuiver.png",
        (0.48, 0.86, 0.44),
        (0.11, 0.02, 0.31),
        360,
        size=(256, 256),
        icon=True,
    )
    print("Bob", len(bob.verts), len(bob.faces))
    print("Kate", len(kate.verts), len(kate.faces))


if __name__ == "__main__":
    main()
