"""Shared by the Blender arrow models (blender_arrow3d*.py run it with exec): camera, light, render settings and the 100-angle loop.

A model script defines `scene`, `holder` (the parent of the whole model, turned for each frame), OUT, FRAMES and PIXELS, then runs this file.
"""
import math

from mathutils import Vector

import bpy

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
