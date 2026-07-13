import re
import sys

def parse_mesh(path, mesh_name_hint=None):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # find "Mesh <name> {" block start
    m = re.search(r"Mesh\s+(\w+)\s*\{", text)
    start = m.end()
    name = m.group(1)

    # vertex count + vertices
    rest = text[start:]
    nums_iter = re.finditer(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", rest)

    def read_floats(it, n):
        vals = []
        for _ in range(n):
            vals.append(float(next(it).group()))
        return vals

    it = nums_iter
    vcount = int(next(it).group())
    verts = []
    for _ in range(vcount):
        x, y, z = read_floats(it, 3)
        verts.append((x, y, z))

    fcount = int(next(it).group())
    faces = []
    for _ in range(fcount):
        n = int(next(it).group())
        idx = [int(next(it).group()) for _ in range(n)]
        faces.append(idx)

    # MeshNormals block
    mn = re.search(r"MeshNormals\s*\{", rest)
    normals = []
    nfaces = []
    if mn:
        nit = re.finditer(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", rest[mn.end():])
        ncount = int(next(nit).group())
        for _ in range(ncount):
            x, y, z = read_floats(nit, 3)
            normals.append((x, y, z))
        nfcount = int(next(nit).group())
        for _ in range(nfcount):
            n = int(next(nit).group())
            idx = [int(next(nit).group()) for _ in range(n)]
            nfaces.append(idx)

    # MeshTextureCoords block (first one only)
    mt = re.search(r"MeshTextureCoords\s+\w*\s*\{", rest)
    uvs = []
    if mt:
        uit = re.finditer(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", rest[mt.end():])
        ucount = int(next(uit).group())
        for _ in range(ucount):
            u, v = read_floats(uit, 2)
            uvs.append((u, v))

    return {
        "name": name,
        "verts": verts,
        "faces": faces,
        "normals": normals,
        "nfaces": nfaces,
        "uvs": uvs,
    }


def write_obj(mesh, path):
    with open(path, "w") as f:
        f.write(f"o {mesh['name']}\n")
        for (x, y, z) in mesh["verts"]:
            f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for (u, v) in mesh["uvs"]:
            f.write(f"vt {u:.6f} {1.0-v:.6f}\n")
        has_uv = len(mesh["uvs"]) == len(mesh["verts"])
        for face in mesh["faces"]:
            if has_uv:
                idx = " ".join(f"{i+1}/{i+1}" for i in face)
            else:
                idx = " ".join(str(i + 1) for i in face)
            f.write(f"f {idx}\n")


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    mesh = parse_mesh(src)
    print(f"parsed mesh '{mesh['name']}': {len(mesh['verts'])} verts, {len(mesh['faces'])} faces, {len(mesh['uvs'])} uvs")
    write_obj(mesh, dst)
    print(f"wrote {dst}")
