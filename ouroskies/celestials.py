# SPDX-License-Identifier: GPL-3.0-or-later

"""Celestials polish — Sun Size / Punch + World-shader binary sun."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from . import defaults, world


def secondary_direction(
    primary: Vector,
    separation_deg: float,
    angle_deg: float,
) -> Vector:
    """Direction of the binary sun parented to ``primary``.

    ``separation_deg`` is angular distance from the primary on the sky.
    ``angle_deg`` is position angle around the primary: 0° toward world +Z
    (zenith-ish), increasing toward east (+X when primary is south).
    """
    p = primary.normalized()
    up = Vector((0.0, 0.0, 1.0))
    east = p.cross(up)
    if east.length_squared < 1e-12:
        east = p.cross(Vector((0.0, 1.0, 0.0)))
    east.normalize()
    toward_zenith = east.cross(p).normalized()

    theta = math.radians(angle_deg)
    offset = (math.cos(theta) * toward_zenith + math.sin(theta) * east).normalized()
    sigma = math.radians(separation_deg)
    return (math.cos(sigma) * p + math.sin(sigma) * offset).normalized()


def _primary_direction(settings) -> Vector:
    from .aim import alt_az_to_direction, orbit_to_alt_az

    if settings.aim_mode == "MANUAL":
        return alt_az_to_direction(
            float(settings.sun_elevation_deg),
            float(settings.sun_azimuth_deg),
        )
    return alt_az_to_direction(
        float(settings.evaluated_sun_elevation_deg),
        float(settings.evaluated_sun_azimuth_deg),
    )


def apply_sun_size_punch_to_sky(
    sky: bpy.types.ShaderNodeTexSky,
    settings,
) -> None:
    """Push primary Sun Size / Punch onto Sky Texture RNA."""
    sky.sun_size = math.radians(max(0.01, float(settings.sun_size_deg)))
    sky.sun_intensity = max(0.0, float(settings.sun_punch))
    if hasattr(sky, "sun_disc"):
        sky.sun_disc = True


def _set_combine_xyz(node, direction: Vector) -> None:
    # Prefer named sockets — Combine XYZ is X/Y/Z (not a Vector in).
    for key, component in (("X", direction.x), ("Y", direction.y), ("Z", direction.z)):
        socket = node.inputs.get(key)
        if socket is not None:
            socket.default_value = float(component)
            continue
        # Fallback by index if names differ.
        idx = {"X": 0, "Y": 1, "Z": 2}[key]
        if len(node.inputs) > idx:
            node.inputs[idx].default_value = float(component)


def _set_value_output(node, value: float) -> None:
    """ShaderNodeValue stores its constant on the output socket (no inputs)."""
    if node is None or not node.outputs:
        return
    node.outputs[0].default_value = float(value)


def _mix_color_sockets(mix: bpy.types.Node):
    """Return (factor, a, b, result) Color/Float sockets for ShaderNodeMix RGBA.

    Mix keeps hidden float/vector/color variants; name lookup can hit the wrong
    (empty/hidden) socket. Prefer enabled RGBA sockets.
    """
    factor = None
    a = b = result = None
    for socket in mix.inputs:
        if getattr(socket, "enabled", True) is False:
            continue
        name = socket.name
        if name in {"Factor", "Fac"} and socket.type == "VALUE":
            factor = socket
        elif name == "A" and socket.type in {"RGBA", "VECTOR", "VALUE"}:
            if a is None or socket.type == "RGBA":
                a = socket
        elif name == "B" and socket.type in {"RGBA", "VECTOR", "VALUE"}:
            if b is None or socket.type == "RGBA":
                b = socket
    for socket in mix.outputs:
        if getattr(socket, "enabled", True) is False:
            continue
        if socket.name in {"Result", "Result_Color"} and socket.type in {
            "RGBA",
            "VECTOR",
            "VALUE",
        }:
            if result is None or socket.type == "RGBA":
                result = socket
    # Hard indices from Blender Mix Color layout if discovery failed.
    if factor is None and len(mix.inputs) > 0:
        factor = mix.inputs[0]
    if a is None and len(mix.inputs) > 6:
        a = mix.inputs[6]
    if b is None and len(mix.inputs) > 7:
        b = mix.inputs[7]
    if result is None and len(mix.outputs) > 2:
        result = mix.outputs[2]
    return factor, a, b, result


def sync_binary_sun_to_world(settings, owned: bpy.types.World) -> None:
    """Update binary-sun overlay uniforms (direction, radius, color, strength)."""
    if owned is None or owned.node_tree is None:
        return
    nt = owned.node_tree
    nodes = nt.nodes

    dir_node = nodes.get(defaults.NODE_SEC_DIR)
    color_node = nodes.get(defaults.NODE_SEC_COLOR)
    radius_node = nodes.get(defaults.NODE_SEC_RADIUS)
    strength_node = nodes.get(defaults.NODE_SEC_STRENGTH)
    if dir_node is None or color_node is None:
        return

    enabled = bool(settings.secondary_sun_enabled)
    primary = _primary_direction(settings)
    secondary = secondary_direction(
        primary,
        float(settings.secondary_sun_separation_deg),
        float(settings.secondary_sun_angle_deg),
    )
    _set_combine_xyz(dir_node, secondary)

    tint = settings.secondary_sun_color
    if color_node.outputs:
        color_node.outputs[0].default_value = (tint[0], tint[1], tint[2], 1.0)

    # Half-angle radius in radians for the disk falloff.
    half = math.radians(max(0.01, float(settings.secondary_sun_size_deg)) * 0.5)
    _set_value_output(radius_node, half)

    strength = float(settings.secondary_sun_strength) if enabled else 0.0
    _set_value_output(strength_node, max(0.0, strength))


def sync_celestials(scene: bpy.types.Scene) -> None:
    """Push Sun Size / Punch + binary sun into the active OuroSkies World."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        return
    owned = world.find_ouroskies_world(scene)
    if owned is None:
        return
    sky = world.find_sky_node(owned)
    if sky is not None:
        apply_sun_size_punch_to_sky(sky, settings)
    sync_binary_sun_to_world(settings, owned)


def wire_binary_sun_nodes(
    node_tree: bpy.types.NodeTree,
    wb_color_socket,
    bg_cam: bpy.types.ShaderNode,
) -> None:
    """Insert camera-path binary sun disk between WB result and BG Camera Color.

    View ray = −Incoming; soft disk from angular radius. Contribution =
    ``color * soft_fac * strength``, added onto the sky (look-first; GI path
    stays WB-only).
    """
    nodes = node_tree.nodes
    links = node_tree.links

    geo = nodes.new("ShaderNodeNewGeometry")
    geo.name = defaults.NODE_SEC_GEO
    geo.label = defaults.NODE_SEC_GEO
    geo.location = (-900.0, 380.0)

    view = nodes.new("ShaderNodeVectorMath")
    view.name = defaults.NODE_SEC_VIEW
    view.label = defaults.NODE_SEC_VIEW
    view.location = (-720.0, 380.0)
    view.operation = "SCALE"
    if len(view.inputs) > 3:
        view.inputs[3].default_value = -1.0
    elif view.inputs.get("Scale") is not None:
        view.inputs["Scale"].default_value = -1.0

    direction = nodes.new("ShaderNodeCombineXYZ")
    direction.name = defaults.NODE_SEC_DIR
    direction.label = defaults.NODE_SEC_DIR
    direction.location = (-720.0, 540.0)

    dot = nodes.new("ShaderNodeVectorMath")
    dot.name = defaults.NODE_SEC_DOT
    dot.label = defaults.NODE_SEC_DOT
    dot.location = (-540.0, 420.0)
    dot.operation = "DOT_PRODUCT"

    acos = nodes.new("ShaderNodeMath")
    acos.name = defaults.NODE_SEC_ACOS
    acos.label = defaults.NODE_SEC_ACOS
    acos.location = (-360.0, 420.0)
    acos.operation = "ARCCOSINE"

    clamp_dot = nodes.new("ShaderNodeClamp")
    clamp_dot.name = defaults.NODE_SEC_DOT + " Clamp"
    clamp_dot.label = "Sec Dot Clamp"
    clamp_dot.location = (-450.0, 420.0)
    clamp_dot.inputs["Min"].default_value = -1.0
    clamp_dot.inputs["Max"].default_value = 1.0

    radius = nodes.new("ShaderNodeValue")
    radius.name = defaults.NODE_SEC_RADIUS
    radius.label = defaults.NODE_SEC_RADIUS
    radius.location = (-360.0, 540.0)
    radius.outputs[0].default_value = math.radians(defaults.SECONDARY_SUN_SIZE_DEG * 0.5)

    # Soft disk: angle 0→radius maps to fac 1→0
    disk_map = nodes.new("ShaderNodeMapRange")
    disk_map.name = defaults.NODE_SEC_MAP
    disk_map.label = defaults.NODE_SEC_MAP
    disk_map.location = (-180.0, 420.0)
    disk_map.clamp = True
    disk_map.inputs["From Min"].default_value = 0.0
    disk_map.inputs["To Min"].default_value = 1.0
    disk_map.inputs["To Max"].default_value = 0.0

    color = nodes.new("ShaderNodeRGB")
    color.name = defaults.NODE_SEC_COLOR
    color.label = defaults.NODE_SEC_COLOR
    color.location = (-180.0, 620.0)
    color.outputs[0].default_value = defaults.SECONDARY_SUN_COLOR

    strength = nodes.new("ShaderNodeValue")
    strength.name = defaults.NODE_SEC_STRENGTH
    strength.label = defaults.NODE_SEC_STRENGTH
    strength.location = (-180.0, 260.0)
    strength.outputs[0].default_value = 0.0

    fac_strength = nodes.new("ShaderNodeMath")
    fac_strength.name = defaults.NODE_SEC_MUL
    fac_strength.label = "Sec Fac×Strength"
    fac_strength.location = (20.0, 360.0)
    fac_strength.operation = "MULTIPLY"

    # color_rgb * (fac * strength) via Vector Math SCALE
    scaled = nodes.new("ShaderNodeVectorMath")
    scaled.name = defaults.NODE_SEC_MUL + " Scale"
    scaled.label = "Sec Color×Scale"
    scaled.location = (200.0, 480.0)
    scaled.operation = "SCALE"

    add = nodes.new("ShaderNodeMix")
    add.name = defaults.NODE_SEC_ADD
    add.label = defaults.NODE_SEC_ADD
    add.location = (-240.0, 160.0)
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    factor_sock, a_sock, b_sock, result_sock = _mix_color_sockets(add)
    if factor_sock is not None:
        factor_sock.default_value = 1.0

    links.new(geo.outputs["Incoming"], view.inputs[0])
    links.new(view.outputs["Vector"], dot.inputs[0])
    links.new(direction.outputs["Vector"], dot.inputs[1])
    links.new(dot.outputs["Value"], clamp_dot.inputs["Value"])
    links.new(clamp_dot.outputs["Result"], acos.inputs[0])
    links.new(acos.outputs["Value"], disk_map.inputs["Value"])
    links.new(radius.outputs[0], disk_map.inputs["From Max"])
    links.new(disk_map.outputs["Result"], fac_strength.inputs[0])
    links.new(strength.outputs[0], fac_strength.inputs[1])
    links.new(color.outputs["Color"], scaled.inputs[0])
    if len(scaled.inputs) > 3:
        links.new(fac_strength.outputs["Value"], scaled.inputs[3])
    elif scaled.inputs.get("Scale") is not None:
        links.new(fac_strength.outputs["Value"], scaled.inputs["Scale"])
    if a_sock is not None:
        links.new(wb_color_socket, a_sock)
    if b_sock is not None:
        links.new(scaled.outputs["Vector"], b_sock)
    if result_sock is not None:
        links.new(result_sock, bg_cam.inputs["Color"])
