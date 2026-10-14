"""Blender script (run by export_arrow3d.py): lays a painted arrow picture (a cut-out PNG with transparency) flat on the ground and renders it
from N turn angles, with the same camera as the modelled arrows, so a picture look also points INTO the scene.

The picture is shown unlit (its own painted shading), pointing +Y, turning around the middle of the picture.
Called as:  blender --background --python blender_arrow3d_picture.py -- <out_dir> <frames> <pixels> <picture.png>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(HERE, "blender_arrow_parts.py"), encoding="utf-8").read(), "blender_arrow_parts.py", "exec"))

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, FRAMES, PIXELS, PICTURE = argv[0], int(argv[1]), int(argv[2]), argv[3]

LENGTH = 2.05          # the picture's longer side, in model units (the modelled arrows are about 2.1 long)

img = bpy.data.images.load(PICTURE)
w, h = img.size
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.02))
plane = bpy.context.active_object
k = LENGTH / max(w, h)
plane.scale = (w * k, h * k, 1.0)

mat = bpy.data.materials.new("picture")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Cubic"
emit = nt.nodes.new("ShaderNodeEmission")
clear = nt.nodes.new("ShaderNodeBsdfTransparent")
mix = nt.nodes.new("ShaderNodeMixShader")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
nt.links.new(clear.outputs["BSDF"], mix.inputs[1])
nt.links.new(emit.outputs["Emission"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
plane.data.materials.append(mat)

holder = bpy.data.objects.new("holder", None)
scene.collection.objects.link(holder)
plane.parent = holder

exec(compile(open(os.path.join(HERE, "blender_arrow_render.py"), encoding="utf-8").read(), "blender_arrow_render.py", "exec"))
