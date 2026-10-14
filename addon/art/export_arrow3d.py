"""Build the 3D BiZNav arrows: addon/RoadToForever/media/arrow3d.tga (the stone arrow) and arrow3d_dart.tga (the gold dart), each a sprite
sheet of 100 frames of the arrow seen in perspective.

Blender (headless) renders the arrow model from 100 turn angles (blender_arrow3d.py, same gold as the flat arrow), then this script
downsamples each frame to 102 px and packs them 10 x 10 into one 1024 x 1024 uncompressed 32-bit TGA with alpha (a power of two, which the game
needs). Frame k = the arrow turned counter-clockwise by k * 3.6 degrees; the addon (Nav.lua) picks the frame from the turn angle:
column = k % 10, row = k // 10, texture coordinates (col * 102 / 1024, (col + 1) * 102 / 1024, row * 102 / 1024, (row + 1) * 102 / 1024).

Usage (repo root):  python addon/art/export_arrow3d.py [--style arrow|dart|block|needle|gilded|plate|slab|all] [--preview <dir>]   (default: all)
A new look = a new blender_arrow3d_<name>.py plus a line in STYLES (and in Nav.lua's Nav.STYLES).
Blender: set BLENDER to its blender.exe, or install it in the default place (C:/Program Files/Blender Foundation/Blender */) or on the PATH.
"""
import glob
import os
import shutil
import struct
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, "..", "RoadToForever", "media")
FRAMES, COLS, CELL, SHEET = 100, 10, 102, 1024
RENDER = CELL * 2          # rendered at 2x and scaled down: smooth edges
# style -> (Blender script, output file)
STYLES = {
    "arrow": ("blender_arrow3d.py", "arrow3d.tga"),
    "dart": ("blender_arrow3d_dart.py", "arrow3d_dart.tga"),
    "block": ("blender_arrow3d_block.py", "arrow3d_block.tga"),
    "needle": ("blender_arrow3d_needle.py", "arrow3d_needle.tga"),
    # painted pictures laid on the ground (addon/art/make_image_looks.py writes the cut-outs)
    "gilded": ("blender_arrow3d_picture.py", "arrow3d_gilded.tga", "gilded_cut.png"),
    "plate": ("blender_arrow3d_picture.py", "arrow3d_plate.tga", "plate_cut.png"),
    "slab": ("blender_arrow3d_picture.py", "arrow3d_slab.tga", "slab_cut.png"),
}


def find_blender():
    cand = os.environ.get("BLENDER")
    if cand and os.path.exists(cand):
        return cand
    for pattern in ("C:/Program Files/Blender Foundation/Blender */blender.exe",
                    "C:/Program Files (x86)/Blender Foundation/Blender */blender.exe"):
        found = sorted(glob.glob(pattern))
        if found:
            return found[-1]
    return shutil.which("blender")


def check_tga(path):
    with open(path, "rb") as f:
        header = f.read(18)
    width, height = struct.unpack("<HH", header[12:16])
    problems = []
    if header[2] != 2 or header[1] != 0:
        problems.append("not an uncompressed true-color TGA")
    if (width, height) != (SHEET, SHEET):
        problems.append("size %dx%d" % (width, height))
    if header[16] != 32 or (header[17] & 0x0F) != 8:
        problems.append("%d bpp / %d alpha bits" % (header[16], header[17] & 0x0F))
    img = Image.open(path)
    for k in (0, FRAMES - 1):
        cx, cy = (k % COLS) * CELL + CELL // 2, (k // COLS) * CELL + CELL // 2
        box = img.crop((cx - 40, cy - 40, cx + 40, cy + 40))
        if box.getchannel("A").getextrema()[1] != 255:
            problems.append("frame %d has no opaque pixels" % k)
    if img.getpixel((SHEET - 1, SHEET - 1))[3] != 0:
        problems.append("the unused corner is not transparent")
    return problems


def main():
    want = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else "all"
    bad = [style for style in (STYLES if want == "all" else [want]) if build_style(style)]
    sys.exit(1 if bad else 0)


def build_style(style):
    """Render and pack one style. Returns True when the sheet has problems."""
    blender = find_blender()
    if not blender:
        print("Blender not found: set BLENDER to blender.exe", file=sys.stderr)
        sys.exit(2)
    work = tempfile.mkdtemp(prefix="r2f_arrow3d_")
    try:
        script = os.path.join(HERE, STYLES[style][0])
        extra = [os.path.join(HERE, "sources", STYLES[style][2])] if len(STYLES[style]) > 2 else []
        subprocess.run([blender, "--background", "--python", script, "--", work, str(FRAMES), str(RENDER)] + extra, check=True,
                       stdout=subprocess.DEVNULL)
        sheet = Image.new("RGBA", (SHEET, SHEET), (0, 0, 0, 0))
        for k in range(FRAMES):
            frame = Image.open(os.path.join(work, "f%03d.png" % k)).convert("RGBA").resize((CELL, CELL), Image.LANCZOS)
            sheet.paste(frame, ((k % COLS) * CELL, (k // COLS) * CELL))
        os.makedirs(MEDIA, exist_ok=True)
        out = os.path.join(MEDIA, STYLES[style][1])
        sheet.save(out, format="TGA")
        problems = check_tga(out)
        print("%s  %d bytes  %s" % (os.path.relpath(out, os.path.join(HERE, "..", "..")), os.path.getsize(out),
                                    "OK" if not problems else "FAIL: " + "; ".join(problems)))
        if "--preview" in sys.argv:
            pdir = sys.argv[sys.argv.index("--preview") + 1]
            os.makedirs(pdir, exist_ok=True)
            bg = Image.new("RGBA", sheet.size, (40, 60, 80, 255))
            bg.alpha_composite(sheet)
            bg.save(os.path.join(pdir, "arrow3d_%s_sheet.png" % style))
            print("preview written to", pdir)
        return bool(problems)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
