import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh
body = parse_mesh("E:/PZCrossbows/work/reference/models/MaleBody.x")
verts = [(ox, oz, oy) for (ox, oy, oz) in body["verts"]]
cand = [v for v in verts if 0.70 < v[2] < 0.95 and -0.05 < v[0] < 0.15]
cand.sort(key=lambda v: -v[1])
for v in cand[:15]:
    print(v)
