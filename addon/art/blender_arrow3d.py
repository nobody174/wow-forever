"""Blender script (run by export_arrow3d.py, not by hand): renders the BiZNav arrow as a 3D object from N angles.

The model is a real arrow, the kind you shoot (no bow): a wooden shaft, a gold broadhead with a raised ridge, and feather
vanes (two flat, one upright) at the nock end, lying flat on the ground (pointing north, +Y) with a dark outline plate under it so
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

GOLD = (1.0, 0.80, 0.18, 1.0)       # the broadhead: the flat arrow's gold
WOOD = (0.66, 0.43, 0.17, 1.0)
CRIMSON = (0.60, 0.05, 0.05, 1.0)
CREAM = (0.97, 0.93, 0.80, 1.0)
OUTLINE = (0.035, 0.02, 0.008, 1.0)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Lengths in model units (tip at +Y). The whole arrow is shifted down a little so its middle sits on the turning point.
SHAFT_R = 0.085
SHAFT_Y0, SHAFT_Y1 = -0.90, 0.62
HEAD = [(0.0, 1.12), (0.19, 0.64), (0.12, 0.42), (0.0, 0.52), (-0.12, 0.42), (-0.19, 0.64)]   # a barbed broadhead
VANE = [(0.05, -0.50), (0.05, -0.84), (0.25, -1.00), (0.25, -0.66)]                            # right flat vane (mirror for left)
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


def paint(ob, mat, bevel=0.0):
    ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("bevel", "BEVEL")
        bev.width = bevel
        bev.segments = 2
    for poly in ob.data.polygons:
        poly.use_smooth = False
    return ob


parts = []
mirror = lambda pts: [(-x, y) for x, y in pts]
# shaft: a round rod along +Y
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=SHAFT_R, depth=SHAFT_Y1 - SHAFT_Y0)
shaft = bpy.context.active_object
shaft.rotation_euler = (math.radians(90), 0, 0)
shaft.location = (0, (SHAFT_Y0 + SHAFT_Y1) / 2, SHAFT_R)
bpy.ops.object.shade_smooth()
parts.append(paint(shaft, material("wood", WOOD, 0.0, 0.55)))
# the broadhead: a thin blade plus a ridge down its middle
blade = prism("blade", HEAD, 0.0, 0.06)
parts.append(paint(blade, material("gold", GOLD, 0.6, 0.30), 0.012))
ridge = prism("ridge", [(0.0, 1.12), (0.05, 0.62), (0.0, 0.52), (-0.05, 0.62)], 0.0, 0.13)
parts.append(paint(ridge, material("gold2", GOLD, 0.6, 0.30), 0.01))
# fletching: two flat vanes (crimson and cream) and one upright crimson fin
parts.append(paint(prism("vane_r", VANE, SHAFT_R - 0.02, SHAFT_R + 0.025), material("cream", CREAM, 0.0, 0.8)))
parts.append(paint(prism("vane_l", mirror(VANE), SHAFT_R - 0.02, SHAFT_R + 0.025), material("crimson", CRIMSON, 0.0, 0.8)))
fin = bmesh.new()
fv = [fin.verts.new(p) for p in ((0.0, -0.50, 0.10), (0.0, -0.84, 0.10), (0.0, -1.00, 0.30), (0.0, -0.66, 0.30))]
fin.faces.new(fv)
fin_ob = to_obj("fin", fin)
solid = fin_ob.modifiers.new("solid", "SOLIDIFY")
solid.thickness = 0.05
parts.append(paint(fin_ob, material("crimson2", CRIMSON, 0.0, 0.8)))
# the nock: a small dark knob at the tail
bpy.ops.mesh.primitive_uv_sphere_add(radius=SHAFT_R * 1.15, location=(0, SHAFT_Y0 - 0.02, SHAFT_R))
nock = bpy.context.active_object
bpy.ops.object.shade_smooth()
parts.append(paint(nock, material("nock", OUTLINE, 0.0, 0.7)))
# the dark outline plate under everything (so it reads on any ground): shaft strip, blade and vanes, slightly larger
plate_parts = [
    prism("o_shaft", [(-0.14, SHAFT_Y0 - 0.06), (0.14, SHAFT_Y0 - 0.06), (0.14, SHAFT_Y1 + 0.02), (-0.14, SHAFT_Y1 + 0.02)], -0.07, -0.01),
    prism("o_head", [(0.0, 1.24), (0.29, 0.64), (0.2, 0.34), (0.0, 0.46), (-0.2, 0.34), (-0.29, 0.64)], -0.07, -0.01),
    prism("o_vane_r", [(0.0, -0.44), (0.0, -0.90), (0.33, -1.10), (0.33, -0.60)], -0.07, -0.01),
    prism("o_vane_l", [(0.0, -0.44), (0.0, -0.90), (-0.33, -1.10), (-0.33, -0.60)], -0.07, -0.01),
]
outline_mat = material("outline", OUTLINE, 0.0, 0.7)
for po in plate_parts:
    parts.append(paint(po, outline_mat))

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
