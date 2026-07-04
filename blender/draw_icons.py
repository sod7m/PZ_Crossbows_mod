"""Hand-authored 32x32 pixel-art item icons for PZCrossbows.

Pure-Python (writes PNG directly, no Blender). Crisp 2D sprites in the PZ style:
flat palette, 1px dark outline, diagonal layout. Original artwork -- not traced
from the borrowed icons, just the same conventional game-icon style.

Run:  python draw_icons.py <out_dir>   (also writes _preview.png montage)
"""
import math
import struct
import sys
import zlib
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


def bez_pts(p0, p1, p2, n=48):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def line_pts(a, b):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 3 + 1
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def estroke(cv, pts, width, col, hi=None):
    """Draw an even-thickness stroke: at each centreline point fill a segment
    perpendicular to the tangent. Gives clean, uniform-width lines & curves."""
    r = (width - 1) / 2.0
    samples = max(3, int(width * 3))
    for i in range(len(pts)):
        if i < len(pts) - 1:
            tx, ty = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
        else:
            tx, ty = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        for j in range(samples + 1):
            t = -r + (2 * r) * (j / samples if samples else 0)
            plot(cv, int(round(pts[i][0] + nx * t)), int(round(pts[i][1] + ny * t)), col)
    if hi is not None:
        for p in pts:
            plot(cv, int(round(p[0])), int(round(p[1])), hi)


def arc_band(cv, cx, cy, rin, rout, a0, a1, col):
    """Fill an annulus sector -> a clean, even-width circular arc (crisp pixels
    by construction, unlike a bezier swept with a brush)."""
    for y in range(int(cy - rout - 1), int(cy + rout + 2)):
        for x in range(int(cx - rout - 1), int(cx + rout + 2)):
            d = math.hypot(x - cx, y - cy)
            if rin - 0.4 <= d <= rout + 0.4:
                a = math.atan2(y - cy, x - cx)
                if a0 <= a <= a1:
                    plot(cv, x, y, col)


def disc(cv, cx, cy, r, col):
    for y in range(int(cy - r), int(cy + r + 1)):
        for x in range(int(cx - r), int(cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                plot(cv, x, y, col)


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
def bolt(cv, x0, y0, x1, y1, head=True, fletch=True, broken=False):
    # even 2px wooden shaft with a 1px highlight run
    estroke(cv, line_pts((x0, y0), (x1, y1)), 2, WOOD, hi=WOOD_L)
    if head:
        # light stone point at the tip (x1,y1)
        dx = 1 if x1 >= x0 else -1
        dy = 1 if y1 >= y0 else -1
        plot(cv, x1, y1, STONE_L)
        plot(cv, x1 + dx, y1 - dy, STONE_L)
        plot(cv, x1 + dx, y1, STONE)
        plot(cv, x1, y1 - dy, STONE)
        plot(cv, x1 + 2 * dx, y1 - dy, STONE_L)
    if broken:
        # bright splintered break at the tip end
        plot(cv, x1, y1, FEA_L)
        plot(cv, x1 - 1, y1, WOOD_L)
        plot(cv, x1, y1 + 1, WOOD_L)
    if fletch:
        # fletching cluster at the back (x0,y0)
        for (ox, oy, c) in [(-1, 0, FEA), (0, -1, FEA_L), (0, 1, FEA_L),
                            (1, 0, FEA), (-1, 1, FEA_L), (1, -1, FEA), (0, 0, FEA_L)]:
            plot(cv, x0 + ox, y0 + oy, c)


def icon_WoodBolt():
    cv = blank(); bolt(cv, 9, 24, 25, 8); finalize(cv); return cv


def icon_ShortWoodBolt():
    cv = blank(); bolt(cv, 11, 22, 22, 11); finalize(cv); return cv


def icon_BrokenWoodBolt():
    cv = blank(); bolt(cv, 10, 24, 19, 15, head=False, broken=True); finalize(cv); return cv


def icon_ShortBrokenWoodBolt():
    cv = blank(); bolt(cv, 12, 22, 19, 15, head=False, broken=True); finalize(cv); return cv


def icon_WoodBoltShaft():
    cv = blank(); bolt(cv, 9, 24, 25, 8, head=False, fletch=True); finalize(cv); return cv


def icon_ShortWoodBoltShaft():
    cv = blank(); bolt(cv, 11, 22, 22, 11, head=False, fletch=True); finalize(cv); return cv


def _fill_tri(cv, A, B, C, col):
    xs = [A[0], B[0], C[0]]; ys = [A[1], B[1], C[1]]
    def sign(p, a, b):
        return (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            d1 = sign((x, y), A, B); d2 = sign((x, y), B, C); d3 = sign((x, y), C, A)
            neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            if not (neg and pos):
                plot(cv, x, y, col)


def icon_StoneBoltHead():
    cv = blank()
    # knapped flint head: pointed up-right, notched base at lower-left
    tip = (24, 8); b1 = (10, 15); b2 = (14, 22)
    _fill_tri(cv, tip, b1, b2, STONE)
    # darker lower edge, lighter central ridge
    line(cv, b1[0], b1[1], b2[0], b2[1], STONE_D, 1)
    line(cv, tip[0], tip[1], b2[0], b2[1], STONE_D, 1)
    line(cv, tip[0], tip[1], (b1[0] + b2[0]) // 2, (b1[1] + b2[1]) // 2, STONE_L, 1)
    plot(cv, tip[0] - 1, tip[1] + 1, STONE_L)
    # small knapped base notch
    plot(cv, 12, 19, None); plot(cv, 12, 18, STONE_D)
    finalize(cv)
    return cv


# --------------------------------------------------------------- crossbows
def crossbow(cv, pommel, front, bow_col, drawn=False, compound=False, hand=False):
    px, py = pommel; fx, fy = front
    # even-width wooden stock from the grey pommel up to the riser (front)
    estroke(cv, line_pts(pommel, front), 4 if not hand else 3, WOOD, hi=WOOD_L)
    # rounded metal pommel at the butt
    disc(cv, px, py, 1.8 if not hand else 1.5, MET_D)
    disc(cv, px, py, 0.8, MET)
    # bow: a clean circular arc centred on the riser, sweeping over the top-right
    R = 6.5 if hand else 10.0
    hw = 0.9 if hand else 1.1               # half-width of the metal band
    a0 = math.radians(-140); a1 = math.radians(42)
    arc_band(cv, fx, fy, R - hw, R + hw, a0, a1, bow_col)
    arc_band(cv, fx, fy, R + hw - 0.6, R + hw, a0, a1, MET_L)   # outer sheen
    UL = (int(round(fx + R * math.cos(a0))), int(round(fy + R * math.sin(a0))))
    LR = (int(round(fx + R * math.cos(a1))), int(round(fy + R * math.sin(a1))))
    # riser block where the stock meets the bow
    disc(cv, fx, fy, 1.4 if not hand else 1.1, MET_D)
    disc(cv, fx, fy, 0.6, MET)
    if compound:
        for T in (UL, LR):
            disc(cv, T[0], T[1], 1.9, MET_L)
            disc(cv, T[0], T[1], 0.7, MET_D)
    # string: chord between the tips, crossing the stock ( the classic X )
    if drawn:
        latch = (fx - 2, fy + 1)
        estroke(cv, line_pts(UL, latch), 1, STR)
        estroke(cv, line_pts(LR, latch), 1, STR)
        estroke(cv, line_pts(latch, (UL[0] + 2, fy - 2)), 1, WOOD_L)  # loaded bolt
        plot(cv, UL[0] + 2, fy - 2, STONE_L)
    else:
        estroke(cv, line_pts(UL, LR), 1, STR)


def icon_CrossBow(drawn=False):
    cv = blank(); crossbow(cv, (7, 25), (17, 13), MET, drawn=drawn); finalize(cv); return cv


def icon_ImprovedCrossBow(drawn=False):
    cv = blank()
    crossbow(cv, (7, 25), (17, 13), MET_L, drawn=drawn)
    # a small sight nub on the rail
    plot(cv, 14, 11, MET_D); plot(cv, 14, 10, MET)
    finalize(cv); return cv


def icon_CompoundCrossBow(drawn=False):
    cv = blank(); crossbow(cv, (7, 25), (17, 13), MET, drawn=drawn, compound=True)
    finalize(cv); return cv


def icon_HandCrossBow(drawn=False):
    cv = blank(); crossbow(cv, (11, 24), (18, 16), MET, drawn=drawn, hand=True)
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
    (OUT / "_preview.png").write_bytes(png)


order = list(ICONS.keys())
for nm, cv in ICONS.items():
    save(cv, nm)
preview(order)
print("wrote", len(ICONS), "icons +_preview to", OUT)
