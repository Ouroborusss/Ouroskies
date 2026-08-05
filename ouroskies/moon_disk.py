# SPDX-License-Identifier: GPL-3.0-or-later

"""Visible moon disk — textured plane aimed with moon alt/az."""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

from . import defaults


def _assets_dir() -> Path:
    return Path(__file__).resolve().parent / "assets"


def _moon_image() -> bpy.types.Image:
    name = defaults.MOON_DISK_IMAGE
    path = _assets_dir() / name
    existing = bpy.data.images.get(name)
    if existing is not None:
        # Drop stale packed/high-res copies so pulls pick up the new plate.
        if tuple(existing.size) != (1080, 1080) or existing.filepath != str(path):
            bpy.data.images.remove(existing)
            existing = None
        else:
            try:
                existing.reload()
            except Exception:
                pass
            return existing
    image = bpy.data.images.load(str(path), check_existing=True)
    image.name = name
    image.alpha_mode = "STRAIGHT"
    return image


def find_moon_disk(scene: bpy.types.Scene) -> bpy.types.Object | None:
    settings = scene.ouroskies
    name = settings.moon_disk_name or defaults.MOON_DISK_NAME
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.get(defaults.MOON_DISK_OWNED_KEY):
        return obj
    for candidate in bpy.data.objects:
        if candidate.get(defaults.MOON_DISK_OWNED_KEY):
            return candidate
    fallback = defaults.MOON_DISK_NAME
    for candidate in bpy.data.objects:
        if candidate.name == fallback or candidate.name.startswith(fallback + "."):
            candidate[defaults.MOON_DISK_OWNED_KEY] = True
            return candidate
    return None


def _ensure_material() -> bpy.types.Material:
    mat_name = "OuroSkies Moon Disk"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    # CLIP avoids EEVEE hashed-transparency holes against the World background.
    mat.blend_method = "CLIP"
    if hasattr(mat, "alpha_threshold"):
        mat.alpha_threshold = 0.2
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"
    mat.use_backface_culling = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (200, 0)
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.location = (0, -120)
    emission = nt.nodes.new("ShaderNodeEmission")
    emission.location = (0, 80)
    emission.inputs["Strength"].default_value = defaults.MOON_DISK_EMISSION
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-280, 40)
    tex.image = _moon_image()
    tex.interpolation = "Cubic"
    tex.extension = "CLIP"
    nt.links.new(tex.outputs["Color"], emission.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emission.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def ensure_moon_disk(scene: bpy.types.Scene) -> bpy.types.Object:
    existing = find_moon_disk(scene)
    if existing is not None:
        return existing

    mesh = bpy.data.meshes.new(defaults.MOON_DISK_NAME)
    # Unit circle in XY; +Z faces the camera/origin after aim.
    verts = [(0.0, 0.0, 0.0)]
    edges = []
    faces = []
    segments = 96
    for i in range(segments):
        a = (i / segments) * math.tau
        verts.append((math.cos(a), math.sin(a), 0.0))
    for i in range(segments):
        faces.append((0, 1 + i, 1 + ((i + 1) % segments)))
    mesh.from_pydata(verts, edges, faces)
    # Simple planar UVs.
    mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data
    # after from_pydata, loops exist
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            co = mesh.vertices[vi].co
            uv[li].uv = (co.x * 0.5 + 0.5, co.y * 0.5 + 0.5)
    mesh.update()

    obj = bpy.data.objects.new(defaults.MOON_DISK_NAME, mesh)
    obj[defaults.MOON_DISK_OWNED_KEY] = True
    mat = _ensure_material()
    if mesh.materials:
        mesh.materials[0] = mat
    else:
        mesh.materials.append(mat)

    try:
        scene.collection.objects.link(obj)
    except RuntimeError:
        bpy.context.scene.collection.objects.link(obj)

    scene.ouroskies.moon_disk_name = obj.name
    scene.ouroskies.has_moon_disk = True
    return obj


def remove_moon_disk(scene: bpy.types.Scene) -> None:
    obj = find_moon_disk(scene)
    settings = scene.ouroskies
    if obj is None:
        settings.has_moon_disk = False
        settings.moon_disk_name = ""
        return
    mesh = obj.data
    mats = list(mesh.materials) if mesh is not None else []
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh is not None and mesh.users == 0:
        bpy.data.meshes.remove(mesh)
    for mat in mats:
        if mat is not None and mat.users == 0:
            bpy.data.materials.remove(mat)
    settings.has_moon_disk = False
    settings.moon_disk_name = ""


def sync_moon_disk(
    scene: bpy.types.Scene,
    direction: Vector,
    *,
    visible_factor: float,
) -> None:
    """Aim / scale the moon disk from the same toward-moon vector as the lamp."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        return

    obj = ensure_moon_disk(scene)
    settings.has_moon_disk = True
    settings.moon_disk_name = obj.name

    direction = direction.normalized()
    distance = defaults.MOON_DISK_DISTANCE
    angular = math.radians(max(0.05, float(settings.moon_size_deg)))
    radius = distance * math.tan(angular * 0.5)

    obj.rotation_mode = "QUATERNION"
    if obj.parent is not None:
        obj.parent = None
    obj.location = direction * distance
    # Plane +Z toward origin so the textured face is seen from the scene.
    obj.rotation_quaternion = (-direction).to_track_quat("Z", "Y")
    obj.scale = (radius, radius, radius)

    hide = visible_factor <= 0.001
    obj.hide_render = hide
    obj.hide_viewport = hide
    if hasattr(obj, "visible_camera"):
        obj.visible_camera = not hide
    if hasattr(obj, "visible_shadow"):
        obj.visible_shadow = False
    if hasattr(obj, "visible_volume_scatter"):
        obj.visible_volume_scatter = False

    # Rebuild material if an older HASHED version is still attached.
    if obj.data is not None:
        mat = _ensure_material()
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    # Dim emission near the horizon.
    if obj.data is not None and obj.data.materials:
        mat = obj.data.materials[0]
        if mat is not None and mat.node_tree is not None:
            emission = None
            for node in mat.node_tree.nodes:
                if node.type == "EMISSION":
                    emission = node
                    break
            if emission is not None:
                emission.inputs["Strength"].default_value = (
                    defaults.MOON_DISK_EMISSION * max(visible_factor, 0.0)
                )
