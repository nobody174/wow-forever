"""Export the Road to Forever logo (addon/art/logo.svg) to the addon's TGA files.

ADDON_PLAN.md 12.1: media/logo64.tga (minimap icon) and media/logo128.tga
(main window portrait), 32-bit with alpha, transparent outside the circle,
power-of-two sizes (WoW needs power-of-two texture dimensions).

Tools: resvg (true SVG rasterizer, via the `resvg_py` package) renders the
SVG; Pillow writes the TGA. On this machine both are installed for
Python 3.12 (`py -3.12 -m pip install resvg_py pillow`), so run it with:

    py -3.12 addon/art/export_logo.py

Each size is rendered at 4x and downscaled with Lanczos, which gives cleaner
anti-aliased edges at 64 px than rendering at 64 px directly. The script
then re-reads both files and checks the TGA header (uncompressed true-color,
32 bits per pixel, 8 alpha bits), the size, and that the corners are fully
transparent and the centre is opaque. Exit code 0 = both files are good.
A 20 px preview PNG (the minimap size) can be written with --preview DIR.
"""
import io
import os
import struct
import sys

import resvg_py
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(HERE, "logo.svg")
MEDIA = os.path.normpath(os.path.join(HERE, "..", "RoadToForever", "media"))
SIZES = (64, 128)
SUPERSAMPLE = 4


def render(size):
    png = resvg_py.svg_to_bytes(svg_path=SVG, width=size * SUPERSAMPLE, height=size * SUPERSAMPLE)
    img = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    return img.resize((size, size), Image.LANCZOS)


def check_tga(path, size):
    """Parse the 18-byte TGA header ourselves, so the check doesn't just trust Pillow."""
    with open(path, "rb") as f:
        header = f.read(18)
    id_len, cmap_type, img_type = header[0], header[1], header[2]
    width, height = struct.unpack("<HH", header[12:16])
    bpp, descriptor = header[16], header[17]
    problems = []
    if img_type != 2 or cmap_type != 0:
        problems.append("not an uncompressed true-color TGA (type %d, colormap %d)" % (img_type, cmap_type))
    if (width, height) != (size, size):
        problems.append("size %dx%d, expected %dx%d" % (width, height, size, size))
    if bpp != 32 or (descriptor & 0x0F) != 8:
        problems.append("%d bpp with %d alpha bits, expected 32 / 8" % (bpp, descriptor & 0x0F))
    if size & (size - 1):
        problems.append("size is not a power of two")
    img = Image.open(path)
    if img.mode != "RGBA":
        problems.append("Pillow reads mode %s, expected RGBA" % img.mode)
    else:
        for corner in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
            if img.getpixel(corner)[3] != 0:
                problems.append("corner %s is not transparent" % (corner,))
        if img.getpixel((size // 2, size // 2))[3] != 255:
            problems.append("centre is not opaque")
    return id_len, problems


def main():
    os.makedirs(MEDIA, exist_ok=True)
    failed = False
    for size in SIZES:
        path = os.path.join(MEDIA, "logo%d.tga" % size)
        render(size).save(path, format="TGA")  # Pillow: uncompressed unless compression= is given
        _, problems = check_tga(path, size)
        status = "OK" if not problems else "FAIL: " + "; ".join(problems)
        print("%s  %d bytes  %s" % (os.path.relpath(path, os.path.join(HERE, "..", "..")), os.path.getsize(path), status))
        failed = failed or bool(problems)
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(out, exist_ok=True)
        for px in (18, 20, 64, 128):
            render(px).save(os.path.join(out, "logo_preview_%d.png" % px))
        # 20 px blown up 8x (nearest), to judge what the minimap really shows.
        render(20).resize((160, 160), Image.NEAREST).save(os.path.join(out, "logo_preview_20_x8.png"))
        print("previews written to", out)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
