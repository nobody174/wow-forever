"""Shared by the Blender arrow models (run with exec before the model): the empty scene and small mesh helpers.

Defines `scene`, `to_obj`, `prism`, `material`, `paint`. Lengths are in model units, the arrow lies on the ground pointing +Y.
"""
import math

import bmesh
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

OUTLINE = (0.035, 0.02, 0.008, 1.0)


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


def paint(ob, mat, bevel=0.0, segments=2, smooth=False):
    ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("bevel", "BEVEL")
        bev.width = bevel
        bev.segments = segments
    for poly in ob.data.polygons:
        poly.use_smooth = smooth
    return ob
