import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh

body = parse_mesh("E:/PZCrossbows/work/reference/models/MaleBody.x")
verts = [(ox, oz, oy) for (ox, oy, oz) in body["verts"]]  # to blender convention

# look for right-side, upper-back shoulder blade area
candidates = [v for v in verts if 0.65 < v[2] < 0.85 and v[1] > 0.03 and 0.05 < v[0] < 0.30]
print("num candidates:", len(candidates))
for v in sorted(candidates, key=lambda v: -v[1])[:20]:
    print(v)
