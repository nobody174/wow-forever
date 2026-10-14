"""Blender script (run by export_arrow3d.py, not by hand): renders the BiZNav arrow as a 3D object from N angles.

The model is a real arrow, the kind you shoot (no bow): a wooden shaft, a chipped-stone head (like an old flint arrow) lashed on with sinew, and feather
vanes (two flat, one upright, each made of single barbs) at the nock end, lying flat on the ground (pointing north, +Y) with a dark outline plate under it so
it reads on any ground. The camera looks at it from the south, tilted down, so the arrow is seen in perspective like TomTom's
"crazy arrow". Frame k is the arrow turned counter-clockwise (seen from above) by k * 360 / N degrees, which is what the addon's
turn angle means, so frame 0 points up on screen. The size options (Small / Medium / Large) just scale the sprite in the game.

Called as:  blender --background --python blender_arrow3d.py -- <out_dir> <frames> <pixels>
Writes <out_dir>/f000.png .. fNNN.png, transparent background, <pixels> square.
"""
import math
import sys

import bpy
import bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
FRAMES = int(argv[1])
PIXELS = int(argv[2])

STONE = (0.27, 0.26, 0.24, 1.0)     # flint: dark grey-brown, dull
STONE_LIGHT = (0.44, 0.42, 0.38, 1.0)
LASH = (0.30, 0.19, 0.09, 1.0)      # the sinew wrapping that holds the head
WOOD = (0.56, 0.36, 0.14, 1.0)
CRIMSON = (0.60, 0.05, 0.05, 1.0)
CRIMSON_LIGHT = (0.74, 0.14, 0.10, 1.0)
CREAM = (0.97, 0.93, 0.80, 1.0)
CREAM_DARK = (0.84, 0.78, 0.60, 1.0)
OUTLINE = (0.035, 0.02, 0.008, 1.0)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Lengths in model units (tip at +Y). The whole arrow is shifted down a little so its middle sits on the turning point.
SHAFT_R = 0.085
SHAFT_Y0, SHAFT_Y1 = -0.90, 0.62
# a notched stone point: a triangle with a notch and a barb on each side
HEAD = [(0.0, 1.14), (0.15, 0.82), (0.19, 0.70), (0.10, 0.64), (0.17, 0.50), (0.0, 0.57),
        (-0.17, 0.50), (-0.10, 0.64), (-0.19, 0.70), (-0.15, 0.82)]
SHIFT = -0.04


def to_obj(name, bm):
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def prism(name, pts, z0, z1):
    """A flat polygon (x, y) extruded from z0 to z1."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    k = len(pts)
    for i in range(k):
        bm.faces.new((lo[i], lo[(i + 1) % k], hi[(i + 1) % k], hi[i]))
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    return to_obj(name, bm)


def material(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def paint(ob, mat, bevel=0.0, smooth=False):
    ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("bevel", "BEVEL")
        bev.width = bevel
        bev.segments = 1
    for poly in ob.data.polygons:
        poly.use_smooth = smooth
    return ob


def barb(name, x0, y0, x1, y1, width):
    """One feather barb: a thin slanted strip from (x0, y0) on the spine to (x1, y1) at the outer tip."""
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln * width / 2, dx / ln * width / 2
    pts = [(x0 + nx, y0 + ny), (x1 + nx * 0.6, y1 + ny * 0.6), (x1 - nx * 0.6, y1 - ny * 0.6), (x0 - nx, y0 - ny)]
    return pts


parts = []
mats = {
    "wood": material("wood", WOOD, 0.0, 0.55),
    "stone": material("stone", STONE, 0.0, 0.92),
    "stone2": material("stone2", STONE_LIGHT, 0.0, 0.85),
    "lash": material("lash", LASH, 0.0, 0.8),
    "cream": material("cream", CREAM, 0.0, 0.85),
    "cream2": material("cream2", CREAM_DARK, 0.0, 0.85),
    "crimson": material("crimson", CRIMSON, 0.0, 0.85),
    "crimson2": material("crimson2", CRIMSON_LIGHT, 0.0, 0.85),
    "nock": material("nock", OUTLINE, 0.0, 0.7),
    "outline": material("outline", OUTLINE, 0.0, 0.7),
}
# shaft: a round rod along +Y
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=SHAFT_R, depth=SHAFT_Y1 - SHAFT_Y0)
shaft = bpy.context.active_object
shaft.rotation_euler = (math.radians(90), 0, 0)
shaft.location = (0, (SHAFT_Y0 + SHAFT_Y1) / 2, SHAFT_R)
bpy.ops.object.shade_smooth()
parts.append(paint(shaft, mats["wood"], smooth=True))
# the stone point: a faceted blade (flat shaded, no smoothing: it should look knapped) with a lighter raised ridge
blade = prism("blade", HEAD, 0.0, 0.07)
parts.append(paint(blade, mats["stone"], 0.012))
ridge = prism("ridge", [(0.0, 1.14), (0.06, 0.78), (0.03, 0.58), (-0.03, 0.58), (-0.06, 0.78)], 0.0, 0.14)
parts.append(paint(ridge, mats["stone2"], 0.015))
for i, (x, y, r) in enumerate([(0.09, 0.9, 0.05), (-0.1, 0.8, 0.045), (0.12, 0.7, 0.04), (-0.12, 0.66, 0.04)]):
    # small flake scars on the faces
    flake = prism("flake%d" % i, [(x - r, y - r), (x + r, y - r * 0.4), (x + r * 0.5, y + r), (x - r, y + r * 0.6)], 0.0, 0.085)
    parts.append(paint(flake, mats["stone2"] if i % 2 else mats["stone"], 0.006))
# the sinew lashing: three turns around the shaft just behind the head
for i, y in enumerate((0.47, 0.53, 0.59)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=SHAFT_R * 1.35, depth=0.045)
    ring = bpy.context.active_object
    ring.rotation_euler = (math.radians(90), 0, 0)
    ring.location = (0, y, SHAFT_R)
    parts.append(paint(ring, mats["lash"]))

# fletching: each vane is a row of single barbs fanning out from the spine, so the edge is feathery
N_BARBS = 9
Y_FRONT, Y_BACK = -0.52, -0.92
for side, (m_a, m_b) in ((1, ("cream", "cream2")), (-1, ("crimson", "crimson2"))):
    for i in range(N_BARBS):
        t = i / (N_BARBS - 1)
        y0 = Y_FRONT + (Y_BACK - Y_FRONT) * t
        reach = 0.13 + 0.12 * t + (0.02 if i % 2 else 0.0)        # longer toward the tail, uneven like real feathers
        pts = barb("b", side * 0.04, y0, side * (0.04 + reach), y0 - 0.12 - 0.05 * t, 0.075)
        ob = prism("vane%d_%d" % (side, i), pts, SHAFT_R - 0.015, SHAFT_R + 0.02)
        parts.append(paint(ob, mats[m_a if i % 2 == 0 else m_b]))
# the upright fin (crimson): the same barbs in the vertical plane
for i in range(N_BARBS - 2):
    t = i / (N_BARBS - 3)
    y0 = Y_FRONT + (Y_BACK - Y_FRONT) * t
    reach = 0.12 + 0.12 * t
    pts = barb("b", 0.0, y0, reach, y0 - 0.12 - 0.05 * t, 0.075)
    ob = prism("fin%d" % i, pts, -0.015, 0.015)
    ob.rotation_euler = (0.0, math.radians(-90), 0.0)
    ob.location = (0.0, 0.0, SHAFT_R + 0.02)
    parts.append(paint(ob, mats["crimson"] if i % 2 == 0 else mats["crimson2"]))
# the nock: a small dark knob at the tail
bpy.ops.mesh.primitive_uv_sphere_add(radius=SHAFT_R * 1.15, location=(0, SHAFT_Y0 - 0.02, SHAFT_R))
nock = bpy.context.active_object
bpy.ops.object.shade_smooth()
parts.append(paint(nock, mats["nock"], smooth=True))
# the dark outline plate under everything (so it reads on any ground): shaft strip, point and vanes, slightly larger
plate_parts = [
    prism("o_shaft", [(-0.14, SHAFT_Y0 - 0.06), (0.14, SHAFT_Y0 - 0.06), (0.14, SHAFT_Y1 + 0.02), (-0.14, SHAFT_Y1 + 0.02)], -0.07, -0.01),
    prism("o_head", [(0.0, 1.26), (0.2, 0.84), (0.27, 0.68), (0.2, 0.40), (0.0, 0.50), (-0.2, 0.40), (-0.27, 0.68), (-0.2, 0.84)],
          -0.07, -0.01),
    prism("o_vane_r", [(0.0, -0.46), (0.0, -0.90), (0.33, -1.08), (0.33, -0.62)], -0.07, -0.01),
    prism("o_vane_l", [(0.0, -0.46), (0.0, -0.90), (-0.33, -1.08), (-0.33, -0.62)], -0.07, -0.01),
]
for po in plate_parts:
    parts.append(paint(po, mats["outline"]))

holder = bpy.data.objects.new("holder", None)
scene.collection.objects.link(holder)
for ob in parts:
    ob.parent = holder
    ob.location = (ob.location.x, ob.location.y + SHIFT, ob.location.z)

# ---- camera: south of the arrow, looking at it from about 52 degrees above the ground ----
cam_data = bpy.data.cameras.new("cam")
cam_data.type = "PERSP"
cam_data.lens = 70
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
elev = math.radians(52)
dist = 5.3
cam.location = (0.0, -dist * math.cos(elev), dist * math.sin(elev))
direction = Vector((0, 0, 0.0)) - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# ---- light ----
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 4.5
sun_ob = bpy.data.objects.new("sun", sun)
sun_ob.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
scene.collection.objects.link(sun_ob)
fill = bpy.data.lights.new("fill", "SUN")
fill.energy = 1.2
fill_ob = bpy.data.objects.new("fill", fill)
fill_ob.rotation_euler = (math.radians(70), 0, math.radians(150))
scene.collection.objects.link(fill_ob)
world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.52, 0.45, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world

# ---- render settings ----
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.film_transparent = True
scene.render.resolution_x = PIXELS
scene.render.resolution_y = PIXELS
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"

for k in range(FRAMES):
    holder.rotation_euler = (0.0, 0.0, math.radians(360.0 * k / FRAMES))
    scene.render.filepath = "%s/f%03d.png" % (OUT, k)
    bpy.ops.render.render(write_still=True)
print("rendered", FRAMES, "frames to", OUT)
