"""Draw the BiZNav waypoint arrow (addon/RoadToForever/media/arrow.tga).

A swept-back dart pointing up: dark outline, gold fill, a lighter left half and a darker right half so it
reads as a raised ridge at any angle. Drawn at 8x and scaled down (LANCZOS), so the edges stay sharp when the
game scales the arrow to Large. 128x128, uncompressed 32-bit TGA with alpha (same checks as export_logo.py).

Also writes media/upgrade.tga: the same dart, 32 px, white (tinted green / red in game) for the bag upgrade markers.

Usage (repo root):  python addon/art/export_arrow.py [--preview <dir>]
"""
import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, "..", "RoadToForever", "media")
SIZE = 128
SS = 8  # supersample



def check_tga(path, size):
    """Same checks as export_logo.py: uncompressed 32-bit, 8 alpha bits, power of two, clear corners, solid centre."""
    with open(path, "rb") as f:
        header = f.read(18)
    cmap_type, img_type = header[1], header[2]
    width, height = struct.unpack("<HH", header[12:16])
    bpp, descriptor = header[16], header[17]
    problems = []
    if img_type != 2 or cmap_type != 0:
        problems.append("not an uncompressed true-color TGA")
    if (width, height) != (size, size) or size & (size - 1):
        problems.append("size %dx%d" % (width, height))
    if bpp != 32 or (descriptor & 0x0F) != 8:
        problems.append("%d bpp / %d alpha bits" % (bpp, descriptor & 0x0F))
    img = Image.open(path)
    for corner in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        if img.getpixel(corner)[3] != 0:
            problems.append("corner %s is not transparent" % (corner,))
    if img.getpixel((size // 2, size // 2))[3] != 255:
        problems.append("centre is not opaque")
    return None, problems

# Shape in 0-1 units of the canvas: tip, right wing, tail notch, left wing.
TIP, RIGHT, NOTCH, LEFT = (0.5, 0.07), (0.86, 0.86), (0.5, 0.68), (0.14, 0.86)
OUTLINE = (24, 14, 4, 255)
LIGHT = (255, 226, 120, 255)   # left half (lit)
DARK = (214, 150, 20, 255)     # right half (shade)
EDGE = (255, 244, 200, 255)    # thin highlight along the left leading edge


def px(p, big):
    return (p[0] * big, p[1] * big)


def render(size=SIZE, light=LIGHT, dark=DARK, edge=EDGE):
    big = size * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    # Outline: the dart's mask grown by a few pixels, filled dark.
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).polygon([px(p, big) for p in (TIP, RIGHT, NOTCH, LEFT)], fill=255)
    grown = mask.filter(ImageFilter.MaxFilter(6 * SS + 1))
    img.paste(Image.new("RGBA", (big, big), OUTLINE), (0, 0), grown)
    d = ImageDraw.Draw(img)
    d.polygon([px(p, big) for p in (TIP, NOTCH, LEFT)], fill=light)
    d.polygon([px(p, big) for p in (TIP, RIGHT, NOTCH)], fill=dark)
    d.line([px(TIP, big), px(LEFT, big)], fill=edge, width=max(1, 2 * SS * size // SIZE))
    return img.resize((size, size), Image.LANCZOS)


# The small upgrade marker on bag icons: the same dart in white / light grey, so the game can
# tint it green (upgrade) or red (downgrade) with SetVertexColor.
UPGRADE_SIZE = 32
WHITE, GREY, BRIGHT = (255, 255, 255, 255), (200, 200, 200, 255), (255, 255, 255, 255)


def main():
    os.makedirs(MEDIA, exist_ok=True)
    path = os.path.join(MEDIA, "arrow.tga")
    render().save(path, format="TGA")
    _, problems = check_tga(path, SIZE)
    up = os.path.join(MEDIA, "upgrade.tga")
    render(UPGRADE_SIZE, WHITE, GREY, BRIGHT).save(up, format="TGA")
    _, p2 = check_tga(up, UPGRADE_SIZE)
    print("%s  %d bytes  %s" % (os.path.relpath(up, os.path.join(HERE, "..", "..")), os.path.getsize(up),
                                "OK" if not p2 else "FAIL: " + "; ".join(p2)))
    problems = problems + p2
    print("%s  %d bytes  %s" % (os.path.relpath(path, os.path.join(HERE, "..", "..")), os.path.getsize(path),
                                "OK" if not problems else "FAIL: " + "; ".join(problems)))
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(out, exist_ok=True)
        art = render()
        sheet = Image.new("RGBA", (SIZE * 4, SIZE), (40, 60, 40, 255))
        for i, angle in enumerate((0, 35, 140, 250)):
            sheet.alpha_composite(art.rotate(angle, resample=Image.BICUBIC), (i * SIZE, 0))
        sheet.save(os.path.join(out, "arrow_preview.png"))
        print("preview written to", out)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
