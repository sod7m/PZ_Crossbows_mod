"""Original WoodBolt.png atlas: bottom = wood grain, top-left = feather, top-right = tip."""
import bpy, math, sys
from pathlib import Path
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(argv[0])
N = 128


def noise(x, y, s):
    return ((x * 12.9898 + y * 78.233 + s * 37.7) * 43758.5453) % 1.0


px = [0.0] * (N * N * 4)
for y in range(N):
    for x in range(N):
        if y < N // 2:                      # bottom half: wood
            g = 0.80 + 0.20 * (0.5 + 0.5 * math.sin(x * 0.6 + noise(x, 0, 3) * 2))
            c = (0.44 * g, 0.25 * g, 0.11 * g)
        elif x < N // 2:                    # top-left: feather (dark)
            g = 0.7 + 0.4 * noise(x, y, 9)
            c = (0.15 * g, 0.11 * g, 0.08 * g)
        else:                               # top-right: sharpened tip (darker wood)
            g = 0.8 + 0.3 * noise(x, y, 17)
            c = (0.32 * g, 0.20 * g, 0.09 * g)
        i = (y * N + x) * 4
        px[i], px[i + 1], px[i + 2], px[i + 3] = min(c[0], 1), min(c[1], 1), min(c[2], 1), 1.0

img = bpy.data.images.new("WoodBolt.png", width=N, height=N, alpha=True)
img.pixels.foreach_set(px)
img.filepath_raw = str(OUT / "WoodBolt.png")
img.file_format = "PNG"
img.save()
print("wrote", OUT / "WoodBolt.png")
