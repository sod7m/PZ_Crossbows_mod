"""Build the final Project Zomboid back quiver without a Blender dependency.

The vanilla AmmoStrap skeleton/mesh is retained as a proven wearable harness,
but its UVs are remapped to leather.  A rigid low-poly quiver and visible bolt
tails are appended and weighted to the torso.  The script also writes an OBJ,
the game texture atlas, QA renders, and an inventory icon.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from parse_x_to_obj import parse_mesh


ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "PZCrossbows/Contents/mods/PZCrossbows/42/media"
REF = ROOT / "work/reference"
OUT = ROOT / "work/InWork/final"


def v3(value):
    return np.asarray(value, dtype=np.float64)


def unit(value):
    value = v3(value)
    length = np.linalg.norm(value)
    return value / length if length > 1e-10 else value


def cross(a, b):
    return np.cross(v3(a), v3(b))


def find_matching_brace(text, open_idx):
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unmatched brace")


def mesh_block(text, name):
    match = re.search(r"Mesh\s+" + re.escape(name) + r"\s*\{", text)
    if not match:
        raise ValueError(f"mesh {name!r} not found")
    opening = text.find("{", match.start())
    closing = find_matching_brace(text, opening)
    return match.start(), closing + 1, text[match.start() : closing + 1]


def parse_skin_weights(block):
    result = []
    for match in re.finditer(r"SkinWeights\s*\{", block):
        opening = block.find("{", match.start())
        closing = find_matching_brace(block, opening)
        body = block[opening + 1 : closing]
        bone_match = re.search(r'"([^"]+)"', body)
        if not bone_match:
            continue
        nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", body[bone_match.end() :])
        count = int(nums[0])
        indices = [int(x) for x in nums[1 : 1 + count]]
        weights = [float(x) for x in nums[1 + count : 1 + count * 2]]
        matrix = [float(x) for x in nums[1 + count * 2 : 1 + count * 2 + 16]]
        result.append({"bone": bone_match.group(1), "indices": indices, "weights": weights, "matrix": matrix})
    return result


class MeshBuilder:
    def __init__(self, verts=None, faces=None, uvs=None):
        self.verts = [v3(v) for v in (verts or [])]
        self.faces = [tuple(f) for f in (faces or [])]
        self.uvs = list(uvs or [])
        self.face_tags = ["leather"] * len(self.faces)

    def add_vertex(self, pos, uv):
        self.verts.append(v3(pos))
        self.uvs.append(tuple(uv))
        return len(self.verts) - 1

    def add_face(self, indices, tag="leather"):
        self.faces.append(tuple(indices))
        self.face_tags.append(tag)

    def basis(self, p0, p1):
        axis = unit(v3(p1) - v3(p0))
        depth_hint = v3((0, 1, 0))
        side = unit(cross(depth_hint, axis))
        depth = unit(cross(axis, side))
        return axis, side, depth

    def add_profile_tube(self, p0, p1, profiles, segments=14, cap_bottom=True, tag="leather"):
        p0, p1 = v3(p0), v3(p1)
        axis, side, depth = self.basis(p0, p1)
        rings = []
        for t, rx, ry in profiles:
            center = p0 + (p1 - p0) * t
            ring = []
            for i in range(segments + 1):
                angle = 2 * math.pi * i / segments
                pos = center + side * (math.cos(angle) * rx) + depth * (math.sin(angle) * ry)
                ring.append(self.add_vertex(pos, (i / segments, 0.02 + t * 0.68)))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for i in range(segments):
                self.add_face((r0[i], r0[i + 1], r1[i + 1]), tag)
                self.add_face((r0[i], r1[i + 1], r1[i]), tag)
        if cap_bottom:
            center = self.add_vertex(p0, (0.5, 0.36))
            for i in range(segments):
                self.add_face((center, rings[0][i + 1], rings[0][i]), tag)
        return axis, side, depth

    def add_elliptic_band(self, p0, p1, t0, t1, rx0, ry0, thickness=0.006, segments=14):
        profiles = [(0.0, rx0 + thickness, ry0 + thickness * 0.75), (1.0, rx0 + thickness, ry0 + thickness * 0.75)]
        a = v3(p0) + (v3(p1) - v3(p0)) * t0
        b = v3(p0) + (v3(p1) - v3(p0)) * t1
        self.add_profile_tube(a, b, profiles, segments, cap_bottom=False, tag="dark_leather")

    def add_annulus(self, center, axis, side, depth, outer, inner, segments=14):
        outer_ring, inner_ring = [], []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            c, s = math.cos(angle), math.sin(angle)
            outer_ring.append(self.add_vertex(center + side * c * outer[0] + depth * s * outer[1], (i / segments, 0.69)))
            inner_ring.append(self.add_vertex(center + side * c * inner[0] + depth * s * inner[1], (i / segments, 0.705)))
        for i in range(segments):
            self.add_face((outer_ring[i], outer_ring[i + 1], inner_ring[i + 1]), "dark_leather")
            self.add_face((outer_ring[i], inner_ring[i + 1], inner_ring[i]), "dark_leather")

    def add_cylinder(self, p0, p1, radius, uv_center, tag, segments=8):
        axis, side, depth = self.basis(p0, p1)
        rings = []
        du = 0.055
        for t, center in ((0, v3(p0)), (1, v3(p1))):
            ring = []
            for i in range(segments + 1):
                angle = 2 * math.pi * i / segments
                pos = center + side * math.cos(angle) * radius + depth * math.sin(angle) * radius
                ring.append(self.add_vertex(pos, (uv_center[0] + (i / segments - 0.5) * du, uv_center[1] + (t - 0.5) * 0.08)))
            rings.append(ring)
        for i in range(segments):
            self.add_face((rings[0][i], rings[0][i + 1], rings[1][i + 1]), tag)
            self.add_face((rings[0][i], rings[1][i + 1], rings[1][i]), tag)
        return axis, side, depth

    def add_fletching(self, start, end, axis, side, depth, scale=1.0):
        for radial in (side, depth, unit(side + depth)):
            radial = unit(radial)
            p0 = v3(start)
            p1 = p0 + (v3(end) - p0) * 0.28
            p2 = v3(end)
            p3 = p0 + (v3(end) - p0) * 0.60 + radial * (0.013 * scale)
            ids = [self.add_vertex(p, (0.625, 0.86 + j * 0.015)) for j, p in enumerate((p0, p1, p2, p3))]
            self.add_face((ids[0], ids[1], ids[3]), "fletch")
            self.add_face((ids[1], ids[2], ids[3]), "fletch")
            self.add_face((ids[3], ids[1], ids[0]), "fletch")
            self.add_face((ids[3], ids[2], ids[1]), "fletch")

    def add_box_between(self, p0, p1, width, thickness, uv_center=(0.875, 0.87), tag="stitch"):
        axis = unit(v3(p1) - v3(p0))
        side = unit(cross(v3((0, 1, 0)), axis))
        if np.linalg.norm(side) < 0.01:
            side = v3((1, 0, 0))
        depth = unit(cross(axis, side))
        corners = []
        for center in (v3(p0), v3(p1)):
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                corners.append(self.add_vertex(center + side * sx * width / 2 + depth * sy * thickness / 2, uv_center))
        for q in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.add_face((corners[q[0]], corners[q[1]], corners[q[2]]), tag)
            self.add_face((corners[q[0]], corners[q[2]], corners[q[3]]), tag)


def add_quiver(builder, back_depth):
    bottom = v3((0.105, back_depth + 0.025, 0.395))
    top = v3((-0.045, back_depth + 0.025, 0.815))
    profiles = [
        (0.00, 0.028, 0.024),
        (0.06, 0.043, 0.033),
        (0.20, 0.050, 0.037),
        (0.72, 0.056, 0.041),
        (0.92, 0.060, 0.044),
        (1.00, 0.069, 0.051),
    ]
    axis, side, depth = builder.add_profile_tube(bottom, top, profiles, segments=14, cap_bottom=True)
    builder.add_elliptic_band(bottom, top, 0.16, 0.195, 0.049, 0.037, 0.005)
    builder.add_elliptic_band(bottom, top, 0.71, 0.75, 0.056, 0.041, 0.005)
    builder.add_elliptic_band(bottom, top, 0.94, 0.995, 0.064, 0.047, 0.006)
    builder.add_annulus(top + axis * 0.001, axis, side, depth, (0.075, 0.057), (0.057, 0.039), 14)

    # A visible stitched seam along the outer edge of the leather body.
    seam_side = side
    for t in np.linspace(0.13, 0.84, 10):
        center = bottom + (top - bottom) * t + seam_side * 0.052
        builder.add_box_between(center - axis * 0.009, center + axis * 0.009, 0.0045, 0.0035)

    # Two short leather keepers visually connect the quiver to the harness.
    for t, target in ((0.30, v3((0.025, back_depth - 0.002, 0.545))), (0.72, v3((-0.015, back_depth - 0.002, 0.705)))):
        q = bottom + (top - bottom) * t - depth * 0.038
        builder.add_box_between(q, target, 0.027, 0.007, (0.32, 0.50), "dark_leather")

    # Crossbow bolts point down inside the quiver; only shafts, nocks and fins
    # are visible above the mouth.  This fixes the old upside-down arrowheads.
    offsets = [(-0.033, -0.010), (-0.012, 0.010), (0.010, -0.008), (0.031, 0.011), (-0.001, 0.023)]
    heights = [0.112, 0.138, 0.125, 0.105, 0.145]
    for i, ((sx, sy), height) in enumerate(zip(offsets, heights)):
        origin = top + side * sx + depth * sy - axis * 0.035
        spread = unit(axis + side * (sx * 0.30) + depth * (sy * 0.20))
        tail = origin + spread * (height + 0.035)
        baxis, bside, bdepth = builder.add_cylinder(origin, tail, 0.0031, (0.125, 0.875), "wood", 8)
        builder.add_fletching(tail - baxis * 0.052, tail - baxis * 0.006, baxis, bside, bdepth, 0.92 + i * 0.02)
        builder.add_cylinder(tail - baxis * 0.007, tail + baxis * 0.004, 0.0040, (0.375, 0.875), "metal", 7)


def compute_normals(verts, faces):
    normals = np.zeros((len(verts), 3), dtype=np.float64)
    verts_np = np.asarray(verts)
    for face in faces:
        for i in range(1, len(face) - 1):
            a, b, c = verts_np[face[0]], verts_np[face[i]], verts_np[face[i + 1]]
            n = np.cross(b - a, c - a)
            for idx in (face[0], face[i], face[i + 1]):
                normals[idx] += n
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths < 1e-10] = 1.0
    return normals / lengths[:, None]


def skin_text(blocks, original_count, total_count, anchor=114):
    result = []
    new_indices = list(range(original_count, total_count))
    for bone in blocks:
        indices = list(bone["indices"])
        weights = list(bone["weights"])
        if anchor in indices:
            anchor_weight = weights[indices.index(anchor)]
            indices.extend(new_indices)
            weights.extend([anchor_weight] * len(new_indices))
        idx_text = ",\n   ".join(str(x) for x in indices)
        weight_text = ",\n   ".join(f"{x:.6f}" for x in weights)
        matrix_text = ",".join(f"{x:.6f}" for x in bone["matrix"])
        result.append(
            "  SkinWeights {\n"
            f'   "{bone["bone"]}";\n'
            f"   {len(indices)};\n   {idx_text};\n   {weight_text};\n   {matrix_text};;\n  }}\n"
        )
    return result


def make_mesh_block(name, builder, skin_blocks):
    # Convert Blender-like coordinates (x, depth, height) back to PZ .X
    # coordinates (x, height, depth).
    verts = [(p[0], p[2], p[1]) for p in builder.verts]
    normals_b = compute_normals(builder.verts, builder.faces)
    normals = [(n[0], n[2], n[1]) for n in normals_b]
    lines = [f"Mesh {name} {{\n {len(verts)};\n"]
    for i, (x, y, z) in enumerate(verts):
        lines.append(f" {x:.6f};{y:.6f};{z:.6f};{',' if i + 1 < len(verts) else ';'}\n")
    lines.append(f" {len(builder.faces)};\n")
    for i, face in enumerate(builder.faces):
        lines.append(f" {len(face)};{','.join(str(x) for x in face)};{',' if i + 1 < len(builder.faces) else ';'}\n")
    lines.append(" MeshNormals {\n")
    lines.append(f"  {len(normals)};\n")
    for i, (x, y, z) in enumerate(normals):
        lines.append(f"  {x:.6f};{y:.6f};{z:.6f};{',' if i + 1 < len(normals) else ';'}\n")
    lines.append(f"  {len(builder.faces)};\n")
    for i, face in enumerate(builder.faces):
        lines.append(f"  {len(face)};{','.join(str(x) for x in face)};{',' if i + 1 < len(builder.faces) else ';'}\n")
    lines.append(" }\n MeshMaterialList {\n  1;\n")
    lines.append(f"  {len(builder.faces)};\n  {','.join('0' for _ in builder.faces)};\n  {{ _07_-_Defaultggg }}\n }}\n")
    lines.append(" MeshTextureCoords c1 {\n")
    lines.append(f"  {len(builder.uvs)};\n")
    for i, (u, v) in enumerate(builder.uvs):
        lines.append(f"  {u:.6f};{v:.6f};{',' if i + 1 < len(builder.uvs) else ';'}\n")
    lines.append(" }\n")
    lines.extend(skin_blocks)
    lines.append("}\n")
    return "".join(lines)


def build_gender(ref_path, mesh_name, destination, obj_destination):
    ref = parse_mesh(str(ref_path))
    # PZ -> convenient construction coordinates.
    ref_verts = [(x, z, y) for x, y, z in ref["verts"]]
    ref_uvs = [(u, 0.02 + v * 0.68) for u, v in ref["uvs"]]
    builder = MeshBuilder(ref_verts, ref["faces"], ref_uvs)
    original_count = len(builder.verts)
    back_depth = max(p[1] for p in builder.verts)
    add_quiver(builder, back_depth)

    text = ref_path.read_text(encoding="utf-8", errors="ignore")
    start, end, old_block = mesh_block(text, mesh_name)
    skins = parse_skin_weights(old_block)
    replacement = make_mesh_block(mesh_name, builder, skin_text(skins, original_count, len(builder.verts)))
    destination.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
    write_obj(builder, obj_destination)
    return builder


def write_obj(builder, path):
    with path.open("w", encoding="utf-8") as f:
        f.write("o BoltQuiver_Final\n")
        for p in builder.verts:
            f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        for u, v in builder.uvs:
            f.write(f"vt {u:.6f} {1-v:.6f}\n")
        normals = compute_normals(builder.verts, builder.faces)
        for n in normals:
            f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
        for face in builder.faces:
            f.write("f " + " ".join(f"{i+1}/{i+1}/{i+1}" for i in face) + "\n")


def build_texture(source, destination):
    source_img = Image.open(source).convert("RGB")
    leather = ImageOps.fit(source_img, (512, 384), method=Image.Resampling.LANCZOS)
    leather = ImageEnhance.Color(leather).enhance(0.82)
    leather = ImageEnhance.Contrast(leather).enhance(0.90)
    atlas = Image.new("RGB", (512, 512), (50, 28, 18))
    atlas.paste(leather, (0, 0))
    rng = np.random.default_rng(42)
    swatches = np.zeros((128, 512, 3), dtype=np.uint8)
    # wood, dark metal/nock, red fletching, tan stitch/dark interior
    colors = ((126, 82, 43), (72, 72, 68), (132, 45, 37), (191, 151, 93))
    for section, color in enumerate(colors):
        x0, x1 = section * 128, (section + 1) * 128
        noise = rng.normal(0, 5, (128, 128, 1))
        base = np.array(color, dtype=np.float32)[None, None, :] + noise
        if section == 0:
            base += (np.sin(np.arange(128)[None, :, None] * 0.19) * 8)
        swatches[:, x0:x1] = np.clip(base, 0, 255).astype(np.uint8)
    # Dark lower-right corner for the inside of the mouth where required.
    swatches[64:128, 448:512] = (43, 25, 18)
    atlas.paste(Image.fromarray(swatches, "RGB"), (0, 384))
    atlas = atlas.filter(ImageFilter.GaussianBlur(0.25))
    atlas.save(destination, optimize=True)


def look_at(camera, target):
    forward = unit(v3(target) - v3(camera))
    right = unit(cross(forward, v3((0, 0, 1))))
    up = unit(cross(right, forward))
    return np.stack((right, up, forward), axis=0)


def render_mesh(builder, texture, body, path, camera, target, scale, size=(900, 900), icon=False):
    width, height = size
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:] = (33, 36, 39) if not icon else (0, 0, 0)
    alpha = np.zeros((height, width), dtype=np.uint8)
    zbuf = np.full((height, width), np.inf)
    rot = look_at(camera, target)
    light = unit(v3((0.4, 0.8, 1.2)))
    tex = np.asarray(texture.convert("RGB"))

    def project(points):
        q = (points - v3(target)) @ rot.T
        x = width * 0.5 + q[:, 0] * scale
        y = height * 0.5 - q[:, 1] * scale
        return np.column_stack((x, y, q[:, 2]))

    def draw_object(verts, faces, uvs, body_color=None):
        verts = np.asarray(verts, dtype=np.float64)
        screen = project(verts)
        order = []
        for face in faces:
            for i in range(1, len(face) - 1):
                tri = (face[0], face[i], face[i + 1])
                order.append((float(np.mean(screen[list(tri), 2])), tri))
        order.sort(reverse=True)
        for _, tri in order:
            ids = list(tri)
            pts = screen[ids]
            minx = max(0, int(math.floor(np.min(pts[:, 0]))))
            maxx = min(width - 1, int(math.ceil(np.max(pts[:, 0]))))
            miny = max(0, int(math.floor(np.min(pts[:, 1]))))
            maxy = min(height - 1, int(math.ceil(np.max(pts[:, 1]))))
            if minx > maxx or miny > maxy:
                continue
            a, b, c = pts[:, :2]
            denom = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(denom) < 1e-8:
                continue
            xs, ys = np.meshgrid(np.arange(minx, maxx + 1), np.arange(miny, maxy + 1))
            w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / denom
            w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / denom
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-5) & (w1 >= -1e-5) & (w2 >= -1e-5)
            z = w0 * pts[0, 2] + w1 * pts[1, 2] + w2 * pts[2, 2]
            region_z = zbuf[miny : maxy + 1, minx : maxx + 1]
            mask = inside & (z < region_z)
            if not np.any(mask):
                continue
            normal = unit(cross(verts[ids[1]] - verts[ids[0]], verts[ids[2]] - verts[ids[0]]))
            shade = 0.45 + 0.55 * abs(float(np.dot(normal, light)))
            if body_color is not None:
                color = np.clip(v3(body_color) * shade, 0, 255).astype(np.uint8)
                region = canvas[miny : maxy + 1, minx : maxx + 1]
                region[mask] = color
            else:
                uv = np.asarray([uvs[i] for i in ids])
                uu = np.clip(w0 * uv[0, 0] + w1 * uv[1, 0] + w2 * uv[2, 0], 0, 1)
                vv = np.clip(w0 * uv[0, 1] + w1 * uv[1, 1] + w2 * uv[2, 1], 0, 1)
                tx = np.minimum(tex.shape[1] - 1, (uu * (tex.shape[1] - 1)).astype(int))
                ty = np.minimum(tex.shape[0] - 1, (vv * (tex.shape[0] - 1)).astype(int))
                sampled = np.clip(tex[ty, tx].astype(np.float32) * shade, 0, 255).astype(np.uint8)
                region = canvas[miny : maxy + 1, minx : maxx + 1]
                region[mask] = sampled[mask]
            region_z[mask] = z[mask]
            alpha[miny : maxy + 1, minx : maxx + 1][mask] = 255

    if body is not None:
        draw_object(body[0], body[1], None, (116, 119, 123))
    draw_object(builder.verts, builder.faces, builder.uvs)
    image = Image.fromarray(canvas, "RGB")
    if icon:
        rgba = image.convert("RGBA")
        rgba.putalpha(Image.fromarray(alpha, "L"))
        bbox = rgba.getbbox()
        if bbox:
            rgba = rgba.crop(bbox)
            rgba.thumbnail((116, 116), Image.Resampling.LANCZOS)
            final = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            final.alpha_composite(rgba, ((128 - rgba.width) // 2, (128 - rgba.height) // 2))
            final.save(path, optimize=True)
    else:
        image.save(path, optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--leather-source", required=True, type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    texture_path = MOD / "textures/Clothes/BoltQuiver.png"
    texture_path.parent.mkdir(parents=True, exist_ok=True)
    build_texture(args.leather_source, texture_path)

    skinned_dir = MOD / "models_x/Skinned/Clothes"
    skinned_dir.mkdir(parents=True, exist_ok=True)
    bob = build_gender(
        REF / "models/Bob_AmmoStrap.x",
        "Bob_AmmoStrap",
        skinned_dir / "Bob_BoltQuiver.X",
        OUT / "Bob_BoltQuiver.obj",
    )
    build_gender(
        REF / "models/Kate_AmmoStrap.x",
        "Kate_AmmoStrap",
        skinned_dir / "Kate_BoltQuiver.X",
        OUT / "Kate_BoltQuiver.obj",
    )
    body_mesh = parse_mesh(str(REF / "models/MaleBody.x"))
    body = ([(x, z, y) for x, y, z in body_mesh["verts"]], body_mesh["faces"])
    texture = Image.open(texture_path)
    render_mesh(bob, texture, body, OUT / "quiver_final_back.png", (0.0, 1.8, 0.66), (0.0, 0.08, 0.56), 720)
    render_mesh(bob, texture, body, OUT / "quiver_final_3q.png", (0.75, 1.55, 0.76), (0.0, 0.08, 0.57), 720)
    render_mesh(bob, texture, None, OUT / "quiver_final_close.png", (0.42, 1.25, 0.70), (0.0, 0.13, 0.63), 1180)
    icon_path = MOD / "textures/Item_BoltQuiver.png"
    render_mesh(bob, texture, None, icon_path, (0.55, 1.35, 0.73), (0.0, 0.13, 0.63), 190, size=(256, 256), icon=True)
    print(f"bob verts={len(bob.verts)} faces={len(bob.faces)}")
    print(texture_path)
    print(icon_path)


if __name__ == "__main__":
    main()
