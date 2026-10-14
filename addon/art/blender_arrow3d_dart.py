"""Blender script (run by export_arrow3d.py, not by hand): renders the BiZNav arrow as a 3D object from N angles.

The arrow is a gold dart lying flat on the ground (pointing north, +Y) with a raised ridge and a dark outline plate under it,
the same colours as the flat arrow (export_arrow.py). The camera looks at it from the south, tilted down, so the arrow is seen in
perspective like TomTom's "crazy arrow". Frame k is the arrow turned counter-clockwise (seen from above) by k * 360 / N degrees,
which is what the addon's turn angle means, so frame 0 points up on screen.

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

GOLD = (1.0, 0.80, 0.18, 1.0)       # the flat arrow's gold
GOLD_LIGHT = (1.0, 0.89, 0.47, 1.0)
OUTLINE = (0.094, 0.055, 0.016, 1.0)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---- the dart: outline in the ground plane (x east, y north), tip at +Y ----
TIP, RIGHT, NOTCH, LEFT = (0.0, 1.0), (0.78, -0.82), (0.0, -0.42), (-0.78, -0.82)


def make_mesh(name, scale, height, ridge, z0):
    """A dart prism: flat bottom at z0, the top rising to a ridge along the middle line."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()

    def v(p, z):
        return bm.verts.new((p[0] * scale, p[1] * scale, z))

    bt = [v(p, z0) for p in (TIP, RIGHT, NOTCH, LEFT)]
    # the top: wing tips and tip low, the middle line (tip -> notch) raised
    tt = v(TIP, z0 + height * 0.55)
    tr = v(RIGHT, z0 + height * 0.35)
    tn = v(NOTCH, z0 + height * 0.9)
    tl = v(LEFT, z0 + height * 0.35)
    mid = v((0.0, 0.18), z0 + height + ridge)
    # sides
    for i in range(4):
        a, b = bt[i], bt[(i + 1) % 4]
        top = (tt, tr, tn, tl)
        bm.faces.new((a, b, top[(i + 1) % 4], top[i]))
    # bottom
    bm.faces.new(list(reversed(bt)))
    # top surface: two triangles each side of the ridge
    bm.faces.new((tt, tr, mid))
    bm.faces.new((tr, tn, mid))
    bm.faces.new((tn, tl, mid))
    bm.faces.new((tl, tt, mid))
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def material(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


arrow = make_mesh("arrow", 1.0, 0.22, 0.12, 0.0)
plate = make_mesh("outline", 1.14, 0.10, 0.0, -0.06)
arrow.data.materials.append(material("gold", GOLD, 0.55, 0.32))
plate.data.materials.append(material("outline", OUTLINE, 0.0, 0.7))
for ob in (arrow, plate):
    bev = ob.modifiers.new("bevel", "BEVEL")
    bev.width = 0.025
    bev.segments = 2
    for poly in ob.data.polygons:
        poly.use_smooth = False
holder = bpy.data.objects.new("holder", None)
scene.collection.objects.link(holder)
arrow.parent = holder
plate.parent = holder

# ---- camera: south of the arrow, looking at it from about 52 degrees above the ground ----
cam_data = bpy.data.cameras.new("cam")
cam_data.type = "PERSP"
cam_data.lens = 70
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
elev = math.radians(52)
dist = 6.0
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
