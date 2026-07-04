"""Generate original crossbow texture atlases (256x256, 4 quadrants).

Quadrant layout matches generate_crossbows.py add_planar_uv():
  bottom-left  = wood      bottom-right = metal
  top-left     = grip      top-right    = steel tip
Run:  blender --background --python make_textures.py -- <textures_dir>
"""
import bpy
import sys
from pathlib import Path

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0]) if argv else Path(r"E:/PZCrossbows/PZCrossbows/Contents/mods/PZCrossbows/42/media/textures/weapons/firearm")
OUT.mkdir(parents=True, exist_ok=True)
N = 256
H = N // 2


def noise(x, y, seed):
    v = (x * 12.9898 + y * 78.233 + seed * 37.719)
    s = (v * 43758.5453) % 1.0
    return s


def build(name, wood, metal):
    px = [0.0] * (N * N * 4)

    def setpx(x, y, c):
        i = (y * N + x) * 4
        px[i] = min(max(c[0], 0), 1)
        px[i + 1] = min(max(c[1], 0), 1)
        px[i + 2] = min(max(c[2], 0), 1)
        px[i + 3] = 1.0

    for y in range(N):
        for x in range(N):
            left = x < H
            bottom = y < H
            if bottom and left:            # wood: horizontal grain
                base = wood
                grain = 0.78 + 0.22 * (0.5 + 0.5 * __import__("math").sin(y * 0.7 + noise(0, y, 3) * 2))
                streak = 1.0 - 0.10 * noise(x // 3, y, 7)
                c = [base[0] * grain * streak, base[1] * grain * streak, base[2] * grain * streak]
            elif bottom and not left:      # metal: subtle brushed
                base = metal
                b = 0.85 + 0.30 * noise(x, y // 4, 11)
                c = [base[0] * b, base[1] * b, base[2] * b]
            elif not bottom and left:      # grip: dark speckle
                base = (0.08, 0.07, 0.06)
                b = 0.7 + 0.5 * noise(x, y, 21)
                c = [base[0] * b, base[1] * b, base[2] * b]
            else:                          # steel tip: mid steel
                base = (0.42, 0.44, 0.47)
                b = 0.85 + 0.22 * noise(x, y, 31)
                c = [base[0] * b, base[1] * b, base[2] * b]
            setpx(x, y, c)

    img = bpy.data.images.new(name, width=N, height=N, alpha=True)
    img.pixels.foreach_set(px)
    img.filepath_raw = str(OUT / name)
    img.file_format = "PNG"
    img.save()
    print("wrote", OUT / name)


# All tiers share ONE identical palette so wood/metal look the same everywhere.
_WOOD = (0.50, 0.30, 0.15)
_METAL = (0.21, 0.22, 0.25)
build("CrossBow.png", wood=_WOOD, metal=_METAL)
build("HandCrossBow.png", wood=_WOOD, metal=_METAL)
build("CompoundCrossBow.png", wood=_WOOD, metal=_METAL)
print("DONE")
