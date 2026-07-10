"""Create UV-compatible texture fixes for Improved and Compound Crossbows."""

from pathlib import Path

import bpy


REPO = Path(__file__).resolve().parents[2]
TEXTURES = REPO / "PZCrossbows" / "Contents" / "mods" / "PZCrossbows" / "42" / "media" / "textures" / "weapons" / "firearm"


def make_fix(source_name, output_name):
    source = TEXTURES / source_name
    output = TEXTURES / output_name
    image = bpy.data.images.load(str(source), check_existing=False)
    pixels = list(image.pixels)
    for index in range(0, len(pixels), 4):
        red, green, blue = pixels[index:index + 3]
        luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722
        # Only lift the near-black material island.  Brown wood and grey steel
        # UV regions are preserved exactly as authored in the original atlas.
        if luminance < 0.18:
            shade = 0.18 + luminance * 0.35
            pixels[index:index + 3] = (shade * 0.93, shade * 0.98, shade)
    fixed = bpy.data.images.new(output.stem, width=image.size[0], height=image.size[1], alpha=True)
    fixed.pixels.foreach_set(pixels)
    fixed.filepath_raw = str(output)
    fixed.file_format = "PNG"
    fixed.save()
    bpy.data.images.remove(image)
    bpy.data.images.remove(fixed)
    print(f"Created {output}")


bpy.ops.wm.read_factory_settings(use_empty=True)
make_fix("CrossBow.png", "ImprovedCrossBow_Fixed.png")
make_fix("CompoundCrossBow.png", "CompoundCrossBow_Fixed.png")
