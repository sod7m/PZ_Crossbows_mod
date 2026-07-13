import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_x_to_obj import parse_mesh

body = parse_mesh("E:/PZCrossbows/work/reference/models/MaleBody.x")
verts = [(ox, oz, oy) for (ox, oy, oz) in body["verts"]]

target = (0.10, 0.088, 0.745)
def d2(a,b): return sum((a[i]-b[i])**2 for i in range(3))
verts.sort(key=lambda v: d2(v, target))
for v in verts[:10]:
    print(v, "dist=", d2(v,target)**0.5)
