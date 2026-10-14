"""Blender script (run by export_arrow3d.py): the "Needle" pointer, a compass needle: a long diamond, red at the pointing end, cream behind.

Our own design, lying on the ground pointing +Y, a gold cap in the middle and a dark outline plate under it.
Called as:  blender --background --python blender_arrow3d_needle.py -- <out_dir> <frames> <pixels>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(HERE, "blender_arrow_parts.py"), encoding="utf-8").read(), "blender_arrow_parts.py", "exec"))

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, FRAMES, PIXELS = argv[0], int(argv[1]), int(argv[2])

RED = (0.78, 0.07, 0.07, 1.0)
RED_LIGHT = (0.95, 0.22, 0.16, 1.0)
CREAM = (0.95, 0.91, 0.78, 1.0)
CREAM_DARK = (0.76, 0.70, 0.54, 1.0)
GOLD = (1.0, 0.80, 0.18, 1.0)
W = 0.34
parts = []
# the pointing half (y > 0): two facets, left darker than right, so the needle has a ridge down the middle
parts.append(paint(prism("n_r", [(0.0, 1.12), (W, 0.0), (0.0, 0.0)], 0.0, 0.12), material("red", RED_LIGHT, 0.2, 0.4), bevel=0.012))
parts.append(paint(prism("n_l", [(0.0, 1.12), (0.0, 0.0), (-W, 0.0)], 0.0, 0.12), material("red2", RED, 0.2, 0.4), bevel=0.012))
parts.append(paint(prism("s_r", [(0.0, 0.0), (W, 0.0), (0.0, -1.0)], 0.0, 0.12), material("cream", CREAM, 0.1, 0.5), bevel=0.012))
parts.append(paint(prism("s_l", [(0.0, 0.0), (0.0, -1.0), (-W, 0.0)], 0.0, 0.12), material("cream2", CREAM_DARK, 0.1, 0.5), bevel=0.012))
# the gold cap on the pivot
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=0.1, location=(0, 0, 0.15))
cap = bpy.context.active_object
parts.append(paint(cap, material("gold", GOLD, 0.7, 0.3), smooth=True))
plate = prism("plate", [(0.0, 1.26), (W + 0.12, 0.0), (0.0, -1.14), (-W - 0.12, 0.0)], -0.07, -0.01)
parts.append(paint(plate, material("outline", OUTLINE, 0.0, 0.7)))

holder = bpy.data.objects.new("holder", None)
scene.collection.objects.link(holder)
for ob in parts:
    ob.parent = holder
    ob.location = (ob.location.x, ob.location.y - 0.06, ob.location.z)

exec(compile(open(os.path.join(HERE, "blender_arrow_render.py"), encoding="utf-8").read(), "blender_arrow_render.py", "exec"))
