"""Create the single diffuse atlas Project Zomboid uses for the detailed FBX."""

from array import array
import math
from pathlib import Path

import bpy


OUT = Path(r"E:\PZCrossbows\PZCrossbows\Contents\mods\PZCrossbows\42\media\textures\weapons\firearm\CrossBow_Detailed.png")
SIZE = 512


def clamp(value):
    return max(0.0, min(1.0, value))


def write_pixel(pixels, x, y, color):
    index = (y * SIZE + x) * 4
    pixels[index:index + 4] = array("f", (*color, 1.0))


def wood(x, y):
    """Subtle walnut: strong stripes turn into visual noise at PZ camera scale."""
    shade = (math.sin(x * 0.018) + math.sin(y * 0.014) + math.sin((x + y) * 0.009)) * 0.006
    # PZ's in-game lighting is noticeably darker than Blender's material view,
    # so use a light, desaturated walnut rather than a near-black red-brown.
    return (clamp(0.36 + shade), clamp(0.275 + shade * 0.60), clamp(0.205 + shade * 0.45))


def iron(x, y):
    noise = math.sin(x * 0.91 + y * 0.37) * 0.025
    # Neutral grey matches the in-game prison bars; avoid a blue cast.
    return (0.18 + noise, 0.18 + noise, 0.18 + noise)


def bronze(x, y):
    noise = math.sin(x * 0.43 - y * 0.71) * 0.04
    return (0.45 + noise, 0.34 + noise * 0.40, 0.17 + noise * 0.18)


def leather(x, y):
    noise = math.sin(x * 0.31 + y * 0.29) * 0.022
    return (0.17 + noise, 0.10 + noise * 0.40, 0.06 + noise * 0.20)


def steel(x, y):
    line = math.sin(x * 0.28 + y * 0.04) * 0.05
    return (0.55 + line, 0.60 + line, 0.63 + line)


def swatch(pixels, centre_u, centre_v, half_size, painter):
    cx = round(centre_u * (SIZE - 1))
    cy = round(centre_v * (SIZE - 1))
    for y in range(max(0, cy - half_size), min(SIZE, cy + half_size)):
        for x in range(max(0, cx - half_size), min(SIZE, cx + half_size)):
            write_pixel(pixels, x, y, painter(x, y))


def mirrored_swatch(pixels, centre_u, centre_v, half_size, painter):
    """PZ's FBX path flips V compared with Blender; paint both valid rows."""
    swatch(pixels, centre_u, centre_v, half_size, painter)
    if abs(centre_v - 0.5) > 0.001:
        swatch(pixels, centre_u, 1.0 - centre_v, half_size, painter)


bpy.ops.wm.read_factory_settings(use_empty=True)
image = bpy.data.images.new("CrossBow_Detailed_Atlas", width=SIZE, height=SIZE, alpha=True)
pixels = array("f", [0.0]) * (SIZE * SIZE * 4)
for y in range(SIZE):
    for x in range(SIZE):
        write_pixel(pixels, x, y, wood(x, y))

# These locations exactly match ATLAS_CENTRES in export_detailed_crossbow_to_pz.py.
mirrored_swatch(pixels, 0.18, 0.84, 22, iron)
mirrored_swatch(pixels, 0.12, 0.78, 22, leather)
mirrored_swatch(pixels, 0.18, 0.30, 22, bronze)
mirrored_swatch(pixels, 0.14, 0.38, 18, leather)
mirrored_swatch(pixels, 0.62, 0.50, 24, steel)

image.pixels.foreach_set(pixels)
image.filepath_raw = str(OUT)
image.file_format = "PNG"
image.save()
print(f"Created {OUT}")
