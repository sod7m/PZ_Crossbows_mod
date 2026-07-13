import re
import json
import sys

def find_matching_brace(text, open_idx):
    depth = 0
    i = open_idx
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("no matching brace")


def parse_skin_weights_blocks(mesh_text):
    blocks = []
    for m in re.finditer(r"SkinWeights\s*\{", mesh_text):
        start = m.end()
        end = find_matching_brace(mesh_text, m.start())
        body = mesh_text[start:end]
        nm = re.search(r'"([^"]+)"', body)
        bone = nm.group(1)
        nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", body[nm.end():])
        n = int(nums[0])
        idxs = [int(x) for x in nums[1:1 + n]]
        weights = [float(x) for x in nums[1 + n:1 + n + n]]
        matrix = [float(x) for x in nums[1 + n + n:1 + n + n + 16]]
        blocks.append({"bone": bone, "indices": idxs, "weights": weights, "matrix": matrix})
    return blocks


def fmt(v):
    return f"{v:.6f}"


def build_skinweights_text(bone, indices, weights, matrix):
    idx_txt = ",\n   ".join(str(i) for i in indices)
    w_txt = ",\n   ".join(fmt(w) for w in weights)
    m_txt = ",".join(fmt(x) for x in matrix)
    return (
        "  SkinWeights {\n"
        f'   "{bone}";\n'
        f"   {len(indices)};\n"
        f"   {idx_txt};\n"
        f"   {w_txt};\n"
        f"   {m_txt};;\n"
        "  }\n"
    )


def build_mesh_block(mesh_name, verts_orig, faces, uvs, skin_blocks_text, material_name="_07_-_Defaultggg"):
    lines = []
    lines.append(f" Mesh {mesh_name} {{\n")
    lines.append(f"  {len(verts_orig)};\n")
    vlines = []
    for (x, y, z) in verts_orig:
        vlines.append(f"  {fmt(x)};{fmt(y)};{fmt(z)};,")
    vlines[-1] = vlines[-1][:-1] + ";"  # last vertex line ends with ; not ,
    lines.append("\n".join(vlines) + "\n")

    lines.append(f"  {len(faces)};\n")
    flines = []
    for f in faces:
        idxs = ",".join(str(i) for i in f)
        flines.append(f"  {len(f)};{idxs};,")
    flines[-1] = flines[-1][:-1] + ";"
    lines.append("\n".join(flines) + "\n")

    # MeshNormals: reuse same face structure, one (unit) normal per vertex,
    # approximated as the direction from the mesh centroid -- not perfectly
    # smooth-shaded but a valid unit vector, unlike raw vertex positions.
    cx = sum(v[0] for v in verts_orig) / len(verts_orig)
    cy = sum(v[1] for v in verts_orig) / len(verts_orig)
    cz = sum(v[2] for v in verts_orig) / len(verts_orig)
    lines.append("  MeshNormals {\n")
    lines.append(f"   {len(verts_orig)};\n")
    nlines = []
    for (x, y, z) in verts_orig:
        dx, dy, dz = x - cx, y - cy, z - cz
        length = (dx * dx + dy * dy + dz * dz) ** 0.5
        if length < 1e-6:
            dx, dy, dz, length = 0.0, 1.0, 0.0, 1.0
        nlines.append(f"   {fmt(dx/length)};{fmt(dy/length)};{fmt(dz/length)};,")
    nlines[-1] = nlines[-1][:-1] + ";"
    lines.append("\n".join(nlines) + "\n")
    lines.append(f"   {len(faces)};\n")
    nflines = []
    for f in faces:
        idxs = ",".join(str(i) for i in f)
        nflines.append(f"   {len(f)};{idxs};,")
    nflines[-1] = nflines[-1][:-1] + ";"
    lines.append("\n".join(nflines) + "\n")
    lines.append("  }\n")

    # MeshMaterialList: single material, all faces use it
    lines.append("  MeshMaterialList {\n")
    lines.append("   1;\n")
    lines.append(f"   {len(faces)};\n")
    mlines = ["   " + ",".join(["0"] * len(faces)) + ";"]
    lines.append("\n".join(mlines) + "\n")
    lines.append(f"   {{ {material_name} }}\n")
    lines.append("  }\n")

    lines.append("  MeshTextureCoords c1 {\n")
    lines.append(f"   {len(uvs)};\n")
    ulines = []
    for (u, v) in uvs:
        ulines.append(f"   {fmt(u)};{fmt(v)};,")
    ulines[-1] = ulines[-1][:-1] + ";"
    lines.append("\n".join(ulines) + "\n")
    lines.append("  }\n")

    for sb in skin_blocks_text:
        lines.append(sb)

    lines.append(" }\n")
    return "".join(lines)


def main():
    ref_x_path = sys.argv[1]
    mesh_json_path = sys.argv[2]
    out_path = sys.argv[3]
    mesh_name = sys.argv[4]  # e.g. "Bob_AmmoStrap" (must match the Frame name to replace)

    with open(ref_x_path, "r", encoding="utf-8", errors="ignore") as f:
        full_text = f.read()

    mesh_start_match = re.search(r"Mesh\s+" + re.escape(mesh_name) + r"\s*\{", full_text)
    mesh_open_brace = full_text.find("{", mesh_start_match.start())
    mesh_close_brace = find_matching_brace(full_text, mesh_open_brace)
    old_mesh_block = full_text[mesh_start_match.start():mesh_close_brace + 1]

    orig_skin_blocks = parse_skin_weights_blocks(old_mesh_block)
    print(f"parsed {len(orig_skin_blocks)} original skin weight blocks")

    with open(mesh_json_path) as f:
        data = json.load(f)

    n_strap = data["n_strap_verts"]
    verts_b = data["verts_blender"]
    faces = data["faces"]
    face_groups = data["face_groups"]

    # convert back to original x-file convention (y=height,z=depth)
    verts_orig = [(bx, bz, by) for (bx, by, bz) in verts_b]

    # UVs: original 154 strap verts keep their original UV (u, v*0.5); new verts
    # get a constant coordinate inside their material's flat-color swatch region.
    orig_uvs = re.search(r"MeshTextureCoords\s+\w*\s*\{", old_mesh_block)
    uv_nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+", old_mesh_block[orig_uvs.end():])
    uv_count = int(uv_nums[0])
    orig_uv_pairs = []
    for i in range(uv_count):
        u = float(uv_nums[1 + i * 2])
        v = float(uv_nums[2 + i * 2])
        orig_uv_pairs.append((u, v * 0.5))

    vertex_groups = data["vertex_groups"]
    swatch = {
        "leather": (0.25, 0.625),
        "wood": (0.75, 0.625),
        "tip": (0.25, 0.875),
        "fletch": (0.75, 0.875),
    }
    uvs = list(orig_uv_pairs)
    for g in vertex_groups[n_strap:]:
        uvs.append(swatch[g])

    # Skin weights: every new vertex (pouch/bands/connector/bolts) inherits the
    # EXACT bone-weight profile of whichever original strap vertex it sits
    # closest to. This guarantees the new geometry moves 1:1 with the strap
    # point it's visually attached to, using only proven, unmodified strap
    # bone matrices -- no borrowed/unrelated bone transform involved.
    strap_positions = verts_orig[:n_strap]

    def nearest_strap_index(p):
        best_i, best_d = 0, None
        for i, sp in enumerate(strap_positions):
            d = (p[0]-sp[0])**2 + (p[1]-sp[1])**2 + (p[2]-sp[2])**2
            if best_d is None or d < best_d:
                best_d, best_i = d, i
        return best_i

    nearest_map = {}  # new_vertex_index -> nearest strap vertex index
    for i in range(n_strap, len(verts_orig)):
        nearest_map[i] = nearest_strap_index(verts_orig[i])

    # per-bone: extend each original block's vertex/weight list with any new
    # vertex whose nearest strap neighbor belongs to that bone
    skin_texts = []
    for b in orig_skin_blocks:
        strap_idx_set = set(b["indices"])
        idx_to_weight = dict(zip(b["indices"], b["weights"]))
        new_indices = list(b["indices"])
        new_weights = list(b["weights"])
        for new_i, nearest_i in nearest_map.items():
            if nearest_i in strap_idx_set:
                new_indices.append(new_i)
                new_weights.append(idx_to_weight[nearest_i])
        skin_texts.append(build_skinweights_text(b["bone"], new_indices, new_weights, b["matrix"]))

    new_mesh_block = build_mesh_block(mesh_name, verts_orig, faces, uvs, skin_texts)

    new_full_text = full_text[:mesh_start_match.start()] + new_mesh_block + full_text[mesh_close_brace + 1:]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new_full_text)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
