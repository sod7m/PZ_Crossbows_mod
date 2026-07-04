"""Hand-authored perfectly-symmetric 32x32 pixel-art item icons for PZCrossbows.

Pure-Python (writes PNG directly, no Blender). Crisp 2D sprites in the PZ style:
flat palette, 1px dark outline, diagonal layout. Original artwork.
Perfect mathematical symmetry for stock-axis perpendicular bow limbs.

Run:  python draw_icons_v2.py <out_dir>
"""
import struct
import sys
import zlib
import math
from pathlib import Path

W = H = 32
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUT.mkdir(parents=True, exist_ok=True)

# palette (r,g,b)
WOOD = (150, 92, 42); WOOD_D = (96, 56, 26); WOOD_L = (188, 122, 66)
MET = (156, 159, 166); MET_D = (95, 98, 104); MET_L = (206, 209, 215)
STR = (233, 233, 237)
STONE = (150, 150, 156); STONE_L = (198, 198, 205); STONE_D = (98, 98, 106)
FEA = (70, 52, 40); FEA_L = (206, 206, 210)
OL = (24, 18, 14)  # outline


def blank():
    return [[None for _ in range(W)] for _ in range(H)]


def plot(cv, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        cv[y][x] = col


def line(cv, x0, y0, x1, y1, col, th=1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = th // 2
    while True:
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                plot(cv, x0 + ox, y0 + oy, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


def qbez(cv, p0, p1, p2, cold, col):
    pts = []
    for i in range(0, 33):
        t = i / 32.0
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    for j in range(len(pts) - 1):
        line(cv, pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], cold, th=3)
    for j in range(len(pts) - 1):
        line(cv, pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], col, th=1)


def disc(cv, cx, cy, r, col):
    for y in range(int(round(cy - r)), int(round(cy + r + 1))):
        for x in range(int(round(cx - r)), int(round(cx + r + 1))):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                plot(cv, x, y, col)


def get_symmetric_tips(pommel, front, limb_length):
    px, py = pommel
    fx, fy = front
    dx = fx - px
    dy = fy - py
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return front, front
    # Direction of stock
    ux = dx / length
    uy = dy / length
    # Perpendicular vector (pointing to the left and right of stock axis)
    perpx = -uy
    perpy = ux
    # Left and right tips
    UL = (fx + perpx * limb_length, fy + perpy * limb_length)
    LR = (fx - perpx * limb_length, fy - perpy * limb_length)
    return UL, LR


def finalize(cv):
    """Add the dark border, then centre the artwork in the 32x32 frame so every
    icon has uniform margins."""
    add_outline(cv)
    xs = [x for y in range(H) for x in range(W) if cv[y][x] is not None]
    ys = [y for y in range(H) for x in range(W) if cv[y][x] is not None]
    if not xs:
        return cv
    dx = (W - 1 - (min(xs) + max(xs))) // 2
    dy = (H - 1 - (min(ys) + max(ys))) // 2
    if dx or dy:
        new = blank()
        for y in range(H):
            for x in range(W):
                if cv[y][x] is not None and 0 <= x + dx < W and 0 <= y + dy < H:
                    new[y + dy][x + dx] = cv[y][x]
        for y in range(H):
            cv[y] = new[y]
    return cv


def add_outline(cv, col=OL):
    """Wrap the opaque silhouette with a 1px dark border (8-neighbour)."""
    edge = []
    for y in range(H):
        for x in range(W):
            if cv[y][x] is not None:
                continue
            near = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and cv[ny][nx] is not None and not _is_ol(cv[ny][nx]):
                        near = True
            if near:
                edge.append((x, y))
    for (x, y) in edge:
        cv[y][x] = col


def _is_ol(c):
    return c == OL


def save(cv, name):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            c = cv[y][x]
            if c is None:
                raw += bytes((0, 0, 0, 0))
            else:
                raw += bytes((c[0], c[1], c[2], 255))

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + chunk(b'IEND', b''))
    (OUT / f"Item_{name}.png").write_bytes(png)


# --------------------------------------------------------------- bolts
def bolt(cv, x0, y0, x1, y1, head=True, fletch=True):
    """A clean arrow: wood shaft, light-stone point at (x1,y1), fletching at (x0,y0)."""
    dx = x1 - x0; dy = y1 - y0
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    perpx, perpy = -uy, ux
    # wood shaft (2px, dark edge from outline)
    line(cv, x0, y0, x1, y1, WOOD_D, th=3)
    line(cv, x0, y0, x1, y1, WOOD, th=1)
    if head:
        # mount the same knapped stone head we generate for StoneBoltHead,
        # base sitting on the shaft tip, point extending forward
        stone_head(cv, x1 + ux * 6, y1 + uy * 6, ux, uy, length=6, halfw=3.0)
    if fletch:
        bx, by = x0 + ux * 2.4, y0 + uy * 2.4
        line(cv, x0, y0, bx + perpx * 2.4, by + perpy * 2.4, FEA_L, th=1)
        line(cv, x0, y0, bx - perpx * 2.4, by - perpy * 2.4, FEA_L, th=1)
        line(cv, x0 + ux * 1.3, y0 + uy * 1.3, bx + perpx * 2.0, by + perpy * 2.0, FEA, th=1)
        line(cv, x0 + ux * 1.3, y0 + uy * 1.3, bx - perpx * 2.0, by - perpy * 2.0, FEA, th=1)


def broken_bolt(cv, big=True):
    """Snapped bolt shown as two separated fragments (fletched half + pointed
    half) offset off-axis, with a small splinter in the gap -- like the reference."""
    A = (7, 25) if big else (10, 22)
    B = (25, 7) if big else (22, 10)
    dx = B[0] - A[0]; dy = B[1] - A[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    perpx, perpy = -uy, ux

    def pt(t, off):
        return (A[0] + dx * t + perpx * off, A[1] + dy * t + perpy * off)

    # lower fragment (fletched end), shifted to one side
    la = pt(0.02, 1.8); lb = pt(0.34, 1.8)
    line(cv, la[0], la[1], lb[0], lb[1], WOOD_D, th=3)
    line(cv, la[0], la[1], lb[0], lb[1], WOOD, th=1)
    plot(cv, lb[0] + ux, lb[1] + uy, FEA_L)              # splintered break
    line(cv, la[0], la[1], la[0] + perpx * 2.2, la[1] + perpy * 2.2, FEA_L, th=1)
    line(cv, la[0], la[1], la[0] - perpx * 2.2, la[1] - perpy * 2.2, FEA_L, th=1)
    line(cv, la[0] + ux, la[1] + uy, la[0] + ux + perpx * 1.8, la[1] + uy + perpy * 1.8, FEA, th=1)
    line(cv, la[0] + ux, la[1] + uy, la[0] + ux - perpx * 1.8, la[1] + uy - perpy * 1.8, FEA, th=1)

    # upper fragment (pointed end), shifted to the other side
    ua = pt(0.60, -1.8); ub = pt(0.97, -1.8)
    line(cv, ua[0], ua[1], ub[0], ub[1], WOOD_D, th=3)
    line(cv, ua[0], ua[1], ub[0], ub[1], WOOD, th=1)
    plot(cv, ua[0] - ux, ua[1] - uy, WOOD_L)             # splintered break
    tip = (ub[0] + ux * 3, ub[1] + uy * 3)
    b1 = (ub[0] - ux + perpx * 2, ub[1] - uy + perpy * 2)
    b2 = (ub[0] - ux - perpx * 2, ub[1] - uy - perpy * 2)
    _fill_tri(cv, tip, b1, b2, STONE_L)
    _fill_tri(cv, tip, (ub[0], ub[1]), b2, STONE)

    # tiny splinter chip in the gap
    m = pt(0.47, 0.3)
    plot(cv, m[0], m[1], WOOD); plot(cv, m[0] + ux, m[1] + uy, WOOD_D)


def icon_WoodBolt():
    cv = blank(); bolt(cv, 9, 23, 20, 12); finalize(cv); return cv


def icon_ShortWoodBolt():
    cv = blank(); bolt(cv, 11, 21, 18, 14); finalize(cv); return cv


def icon_BrokenWoodBolt():
    cv = blank(); broken_bolt(cv, big=True); finalize(cv); return cv


def icon_ShortBrokenWoodBolt():
    cv = blank(); broken_bolt(cv, big=False); finalize(cv); return cv


def icon_WoodBoltShaft():
    cv = blank(); bolt(cv, 8, 24, 24, 8, head=False, fletch=True); finalize(cv); return cv


def icon_ShortWoodBoltShaft():
    cv = blank(); bolt(cv, 10, 22, 22, 10, head=False, fletch=True); finalize(cv); return cv


def stone_head(cv, tx, ty, ux, uy, length=6, halfw=3.0):
    """Knapped flint head: point at (tx,ty) aimed along (ux,uy); base sits back
    along -u. Used both for the StoneBoltHead icon and mounted on bolts so they
    always match."""
    perpx, perpy = -uy, ux
    base = (tx - ux * length, ty - uy * length)
    b1 = (base[0] + perpx * halfw, base[1] + perpy * halfw)
    b2 = (base[0] - perpx * halfw, base[1] - perpy * halfw)
    _fill_tri(cv, (tx, ty), b1, b2, STONE)
    line(cv, b1[0], b1[1], b2[0], b2[1], STONE_D, 1)          # base edge (dark)
    line(cv, tx, ty, b2[0], b2[1], STONE_D, 1)                # one flank shaded
    line(cv, tx, ty, base[0], base[1], STONE_L, 1)            # central ridge
    plot(cv, int(round(tx - ux)), int(round(ty - uy)), STONE_L)


def _fill_tri(cv, A, B, C, col):
    xs = [A[0], B[0], C[0]]; ys = [A[1], B[1], C[1]]
    def sign(p, a, b):
        return (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
    for y in range(int(round(min(ys))), int(round(max(ys))) + 1):
        for x in range(int(round(min(xs))), int(round(max(xs))) + 1):
            d1 = sign((x, y), A, B); d2 = sign((x, y), B, C); d3 = sign((x, y), C, A)
            neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            if not (neg and pos):
                plot(cv, x, y, col)


def icon_StoneBoltHead():
    cv = blank()
    # the same knapped flint head, standalone and larger, pointing up-right
    stone_head(cv, 22, 9, 0.66, -0.75, length=12, halfw=5.5)
    finalize(cv)
    return cv


# --------------------------------------------------------------- crossbows
def crossbow(cv, pommel, front, bow_col, drawn=False, compound=False, hand=False, scope=False):
    px, py = pommel
    fx, fy = front
    
    # Stock direction vectors
    dx = fx - px
    dy = fy - py
    length = math.hypot(dx, dy)
    ux = dx / length if length > 0 else 1.0
    uy = dy / length if length > 0 else 0.0
    perpx = -uy
    perpy = ux
    
    # Draw stock under-stroke
    line(cv, px, py, fx, fy, OL, th=5 if not hand else 4)
    
    # Stock is wooden on every tier (compound = half-wood: wood stock + metal cams/bow)
    stock_col = WOOD
    stock_col_d = WOOD_D
    stock_col_l = WOOD_L
    
    line(cv, px, py, fx, fy, stock_col_d, th=3 if not hand else 2)
    line(cv, px, py, fx, fy, stock_col, th=1)
    line(cv, px - perpx, py - perpy, fx - perpx, fy - perpy, stock_col_l, th=1)
    
    # Buttstock cheek-rest (for long crossbows)
    if not hand:
        cx, cy = px + ux * 3.5, py + uy * 3.5
        disc(cv, cx, cy, 2.2, stock_col_d)
        disc(cv, cx, cy, 1.4, stock_col)
        disc(cv, cx - perpx, cy - perpy, 0.8, stock_col_l)
        
    # Trigger guard (small loop below the stock)
    tx, ty = px + ux * (length * 0.45), py + uy * (length * 0.45)
    disc(cv, tx + perpx * 1.5, ty + perpy * 1.5, 1.6, OL)
    disc(cv, tx + perpx * 1.5, ty + perpy * 1.5, 0.6, None)
    plot(cv, int(round(tx)), int(round(ty)), MET) # steel trigger
    
    # Pommel metal plate
    disc(cv, px, py, 1.8 if not hand else 1.2, OL)
    disc(cv, px, py, 1.0 if not hand else 0.6, MET)
    
    # Symmetric Bow limbs
    limb_len = 10 if not hand else 6
    if compound:
        limb_len = 8.5
    
    UL, LR = get_symmetric_tips(pommel, front, limb_len)
    
    # Forward-bend control point for curved limbs
    forward_bend = 4 if not hand else 2.5
    if compound:
        forward_bend = 1.5  # Compound has stiffer, flatter limbs
    ctrl = (front[0] + ux * forward_bend, front[1] + uy * forward_bend)
    
    # Draw bow limbs
    qbez(cv, UL, ctrl, LR, OL, bow_col)
    
    # Eccentric cams for compound crossbow
    if compound:
        disc(cv, UL[0], UL[1], 1.8, OL)
        disc(cv, UL[0], UL[1], 0.8, MET_L)
        disc(cv, LR[0], LR[1], 1.8, OL)
        disc(cv, LR[0], LR[1], 0.8, MET_L)
        
    # Riser block (meets stock and limbs)
    disc(cv, fx, fy, 1.8 if not hand else 1.2, OL)
    disc(cv, fx, fy, 1.0 if not hand else 0.6, MET)
    
    # Scope mount
    if scope:
        sx, sy = px + ux * (length * 0.65), py + uy * (length * 0.65)
        line(cv, sx - perpx * 1.8 - ux * 2, sy - perpy * 1.8 - uy * 2,
                 sx - perpx * 1.8 + ux * 2, sy - perpy * 1.8 + uy * 2, OL, th=3)
        line(cv, sx - perpx * 1.8 - ux * 2, sy - perpy * 1.8 - uy * 2,
                 sx - perpx * 1.8 + ux * 2, sy - perpy * 1.8 + uy * 2, MET_L, th=1)
        
    # String and loaded projectile
    if drawn:
        latch_pct = 0.52 if not hand else 0.48
        lx, ly = px + ux * (length * latch_pct), py + uy * (length * latch_pct)
        
        if compound:
            # Main shooting string
            line(cv, UL[0], UL[1], lx, ly, STR, th=1)
            line(cv, LR[0], LR[1], lx, ly, STR, th=1)
            # Secondary compound cables crossing below rail
            line(cv, UL[0], UL[1], lx - perpx * 1.5, ly - perpy * 1.5, MET_D, th=1)
            line(cv, LR[0], LR[1], lx + perpx * 1.5, ly + perpy * 1.5, MET_D, th=1)
        else:
            line(cv, UL[0], UL[1], lx, ly, STR, th=1)
            line(cv, LR[0], LR[1], lx, ly, STR, th=1)
            
        # Loaded bolt!
        bolt_len = 10 if not hand else 7
        bx0, by0 = lx, ly
        bx1, by1 = lx + ux * bolt_len, ly + uy * bolt_len
        line(cv, bx0, by0, bx1, by1, WOOD_D, th=3)
        line(cv, bx0, by0, bx1, by1, WOOD, th=1)
        # Stone point of bolt
        plot(cv, int(round(bx1)), int(round(by1)), STONE_L)
        plot(cv, int(round(bx1 + ux)), int(round(by1 + uy)), STONE_L)
        plot(cv, int(round(bx1 - perpx)), int(round(by1 - perpy)), STONE)
        # Fletchings
        plot(cv, int(round(bx0 + ux)), int(round(by0 + uy + perpy)), FEA_L)
        plot(cv, int(round(bx0 + ux)), int(round(by0 + uy - perpy)), FEA_L)
    else:
        line(cv, UL[0], UL[1], LR[0], LR[1], STR, th=1)


def icon_CrossBow(drawn=False):
    cv = blank(); crossbow(cv, (6, 26), (21, 11), MET, drawn=drawn); finalize(cv); return cv


def icon_ImprovedCrossBow(drawn=False):
    cv = blank()
    crossbow(cv, (6, 26), (21, 11), MET_L, drawn=drawn, scope=True)
    finalize(cv); return cv


def icon_CompoundCrossBow(drawn=False):
    cv = blank(); crossbow(cv, (6, 26), (21, 11), MET, drawn=drawn, compound=True, scope=True)
    finalize(cv); return cv


def icon_HandCrossBow(drawn=False):
    cv = blank(); crossbow(cv, (10, 23), (19, 14), MET, drawn=drawn, hand=True)
    finalize(cv); return cv


ICONS = {
    "CrossBow": icon_CrossBow(),
    "CrossBowDrawn": icon_CrossBow(True),
    "ImprovedCrossBow": icon_ImprovedCrossBow(),
    "ImprovedCrossBowDrawn": icon_ImprovedCrossBow(True),
    "CompoundCrossBow": icon_CompoundCrossBow(),
    "CompoundCrossBowDrawn": icon_CompoundCrossBow(True),
    "HandCrossBow": icon_HandCrossBow(),
    "HandCrossBowDrawn": icon_HandCrossBow(True),
    "WoodBolt": icon_WoodBolt(),
    "ShortWoodBolt": icon_ShortWoodBolt(),
    "BrokenWoodBolt": icon_BrokenWoodBolt(),
    "ShortBrokenWoodBolt": icon_ShortBrokenWoodBolt(),
    "WoodBoltShaft": icon_WoodBoltShaft(),
    "ShortWoodBoltShaft": icon_ShortWoodBoltShaft(),
    "StoneBoltHead": icon_StoneBoltHead(),
}


def preview(order):
    SC = 9; PAD = 6; COLS = 5
    rows = (len(order) + COLS - 1) // COLS
    PW = COLS * (W * SC) + (COLS + 1) * PAD
    PH = rows * (H * SC) + (rows + 1) * PAD
    buf = [[(40, 40, 46) for _ in range(PW)] for _ in range(PH)]
    for idx, nm in enumerate(order):
        cv = ICONS[nm]
        c = idx % COLS; r = idx // COLS
        ox = PAD + c * (W * SC + PAD); oy = PAD + r * (H * SC + PAD)
        for y in range(H):
            for x in range(W):
                col = cv[y][x]
                if col is None:
                    continue
                for sy in range(SC):
                    for sx in range(SC):
                        buf[oy + y * SC + sy][ox + x * SC + sx] = col
    raw = bytearray()
    for y in range(PH):
        raw.append(0)
        for x in range(PW):
            r_, g_, b_ = buf[y][x]
            raw += bytes((r_, g_, b_, 255))

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack(">IIBBBBB", PW, PH, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + chunk(b'IEND', b''))
    (OUT / "_preview_v2.png").write_bytes(png)


order = list(ICONS.keys())
for nm, cv in ICONS.items():
    save(cv, nm)
preview(order)
print("wrote", len(ICONS), "perfectly-symmetric icons +_preview_v2 to", OUT)
