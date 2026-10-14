"""Blender script (run by export_arrow3d.py): the "Block" arrow, a thick rounded slab in an orange-gold with a lighter top face.

Our own design (a chunky signpost arrow lying on the ground, pointing +Y) with a dark outline plate under it.
Called as:  blender --background --python blender_arrow3d_block.py -- <out_dir> <frames> <pixels>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(HERE, "blender_arrow_parts.py"), encoding="utf-8").read(), "blender_arrow_parts.py", "exec"))

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, FRAMES, PIXELS = argv[0], int(argv[1]), int(argv[2])

SLAB = (0.93, 0.40, 0.04, 1.0)
TOP = (1.0, 0.64, 0.13, 1.0)
# arrow outline, tip at +Y; a stubby shaft and a wide head
ARROW = [(0.0, 1.12), (0.62, 0.34), (0.26, 0.34), (0.26, -0.98), (-0.26, -0.98), (-0.26, 0.34), (-0.62, 0.34)]
INNER = [(0.0, 0.92), (0.46, 0.30), (0.14, 0.30), (0.14, -0.82), (-0.14, -0.82), (-0.14, 0.30), (-0.46, 0.30)]
SHIFT = -0.07

parts = []
slab = prism("slab", ARROW, 0.0, 0.26)
parts.append(paint(slab, material("slab", SLAB, 0.15, 0.45), bevel=0.05, segments=3))
face = prism("face", INNER, 0.26, 0.31)
parts.append(paint(face, material("top", TOP, 0.15, 0.4), bevel=0.02, segments=2))
big = [(x * 1.12, y * 1.08) for x, y in ARROW]
plate = prism("plate", big, -0.07, -0.01)
parts.append(paint(plate, material("outline", OUTLINE, 0.0, 0.7)))

holder = bpy.data.objects.new("holder", None)
scene.collection.objects.link(holder)
for ob in parts:
    ob.parent = holder
    ob.location = (ob.location.x, ob.location.y + SHIFT, ob.location.z)

exec(compile(open(os.path.join(HERE, "blender_arrow_render.py"), encoding="utf-8").read(), "blender_arrow_render.py", "exec"))
