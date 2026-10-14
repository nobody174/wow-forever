"""Turn picture arrows (AI-generated or painted, on a plain light background) into the game's flat arrow textures.

For each entry of LOOKS: the source picture in addon/art/sources/ is cut out (the light, colourless background that touches the border becomes
transparent, which also removes a soft shadow), centred on the middle of the arrow, padded and shrunk to SIZE x SIZE, and written as an
uncompressed 32-bit TGA to addon/RoadToForever/media/arrow_<key>.tga. The game turns these pictures like the flat dart (Nav.lua, STYLES
entries without a sprite sheet).

Usage (repo root):  python addon/art/make_image_looks.py [--preview <dir>]
A new look = a picture in addon/art/sources/, a line in LOOKS, a Nav.STYLES entry and a NAV_STYLE_<KEY> text in Locale.lua.
"""
import os
import sys
from collections import deque

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "sources")
MEDIA = os.path.join(HERE, "..", "RoadToForever", "media")
SIZE = 128
PAD = 0.06            # empty margin around the arrow, fraction of the picture

# key -> source file
LOOKS = {
    "gilded": "gilded.jpg",
    "plate": "plate.jpg",
    "slab": "slab.jpg",
}


def is_background(px):
    r, g, b = px
    return min(r, g, b) >= 140 and max(r, g, b) - min(r, g, b) <= 28


def cut_out(img):
    """RGBA image: the border-connected light colourless background is transparent."""
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()
    bg = [[False] * w for _ in range(h)]
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_background(px[x, y]) and not bg[y][x]:
                bg[y][x] = True
                dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_background(px[x, y]) and not bg[y][x]:
                bg[y][x] = True
                dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx] and is_background(px[nx, ny]):
                bg[ny][nx] = True
                dq.append((nx, ny))
    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            if bg[y][x]:
                mp[x, y] = 0
    # a one pixel erosion drops the light fringe, a small blur gives soft anti-aliased edges
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def centred(img):
    """Crop to the arrow, centre it on the middle of the arrow's box, pad, resize to SIZE x SIZE."""
    box = img.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    img = img.crop(box)
    side = int(max(img.size) * (1 + 2 * PAD))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    preview = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    os.makedirs(MEDIA, exist_ok=True)
    sheet = Image.new("RGBA", (SIZE * 2 * len(LOOKS), SIZE * 2), (40, 60, 80, 255))
    for i, (key, name) in enumerate(LOOKS.items()):
        out = centred(cut_out(Image.open(os.path.join(SOURCES, name))))
        path = os.path.join(MEDIA, "arrow_%s.tga" % key)
        out.save(path, format="TGA")
        print("%s  %d bytes" % (os.path.relpath(path, os.path.join(HERE, "..", "..")), os.path.getsize(path)))
        sheet.alpha_composite(out.resize((SIZE * 2, SIZE * 2), Image.LANCZOS), (i * SIZE * 2, 0))
    if preview:
        os.makedirs(preview, exist_ok=True)
        sheet.save(os.path.join(preview, "image_looks.png"))


if __name__ == "__main__":
    main()
