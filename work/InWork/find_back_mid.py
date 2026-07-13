import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh

ref = parse_mesh("E:/PZCrossbows/work/reference/models/Bob_AmmoStrap.x")
strap_verts = [(ox, oz, oy) for (ox, oy, oz) in ref["verts"]]

# most-rearward point (max Y = deepest on the back)
max_y_idx = max(range(len(strap_verts)), key=lambda i: strap_verts[i][1])
print("max-Y (most rearward, mid-back) vertex:", strap_verts[max_y_idx])

# print a handful of the top-Y vertices to see the spread
sv = sorted(strap_verts, key=lambda v: -v[1])[:10]
for v in sv:
    print(v)
