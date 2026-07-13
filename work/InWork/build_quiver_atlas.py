from PIL import Image

orig = Image.open("E:/PZCrossbows/work/reference/textures/AmmoStrap_Shells.png").convert("RGB")
W, H = 128, 256
atlas = Image.new("RGB", (W, H), (0, 0, 0))
atlas.paste(orig.resize((W, 128)), (0, 0))

leather = (156, 84, 36)
wood = (140, 96, 52)
tip = (150, 150, 155)
fletch = (188, 60, 45)

for x in range(0, 64):
    for y in range(128, 192):
        atlas.putpixel((x, y), leather)
for x in range(64, 128):
    for y in range(128, 192):
        atlas.putpixel((x, y), wood)
for x in range(0, 64):
    for y in range(192, 256):
        atlas.putpixel((x, y), tip)
for x in range(64, 128):
    for y in range(192, 256):
        atlas.putpixel((x, y), fletch)

atlas.save("E:/PZCrossbows/work/InWork/BoltQuiver_atlas.png")
print("saved atlas", atlas.size)
