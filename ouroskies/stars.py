# SPDX-License-Identifier: GPL-3.0-or-later

"""Procedural stars + togglable Milky band — World camera overlay (looks over catalog)."""

from __future__ import annotations

import math

import bpy

from . import defaults, world


def stars_daylight_fade(sun_elevation_deg: float) -> float:
    """1 at night, 0 in daylight. provisional: fade between STARS_FADE_LOW/HIGH."""
    low = defaults.STARS_FADE_LOW_DEG
    high = defaults.STARS_FADE_HIGH_DEG
    if sun_elevation_deg <= low:
        return 1.0
    if sun_elevation_deg >= high:
        return 0.0
    return 1.0 - (sun_elevation_deg - low) / (high - low)


def _current_sun_elevation_deg(settings) -> float:
    if settings.aim_mode == "PLACE_DATE":
        return float(settings.evaluated_sun_elevation_deg)
    from .aim import orbit_to_alt_az

    alt, _az = orbit_to_alt_az(
        float(settings.sun_elevation_deg),
        float(settings.sun_azimuth_deg),
    )
    return alt


def _set_value_output(node, value: float) -> None:
    if node is None or not node.outputs:
        return
    node.outputs[0].default_value = float(value)


def _set_combine_xyz(node, xyz: tuple[float, float, float]) -> None:
    for key, component in (("X", xyz[0]), ("Y", xyz[1]), ("Z", xyz[2])):
        socket = node.inputs.get(key)
        if socket is not None:
            socket.default_value = float(component)
            continue
        idx = {"X": 0, "Y": 1, "Z": 2}[key]
        if len(node.inputs) > idx:
            node.inputs[idx].default_value = float(component)


def _normalize3(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z) or 1.0
    return (x / length, y / length, z / length)


def sync_stars_to_world(settings, owned: bpy.types.World) -> None:
    """Push Density / Brightness / Milky into World uniforms."""
    if owned is None or owned.node_tree is None:
        return
    nodes = owned.node_tree.nodes

    density = max(0.0, float(settings.stars_density))
    brightness = max(0.0, float(settings.stars_brightness))
    if defaults.STARS_USE_DAYLIGHT_FADE:
        fade = stars_daylight_fade(_current_sun_elevation_deg(settings))
    else:
        fade = 1.0
    milky_on = bool(settings.stars_milky_band)

    scale = defaults.STARS_VORONOI_SCALE * max(0.05, density)
    _set_value_output(nodes.get(defaults.NODE_STAR_SCALE), scale)
    _set_value_output(
        nodes.get(defaults.NODE_STAR_SCALE_BRIGHT),
        scale * defaults.STARS_BRIGHT_SCALE_FRAC,
    )
    _set_value_output(nodes.get(defaults.NODE_STAR_BRIGHTNESS), brightness)
    _set_value_output(nodes.get(defaults.NODE_STAR_FADE), fade)
    _set_value_output(
        nodes.get(defaults.NODE_MILKY_STRENGTH),
        defaults.MILKY_STRENGTH * brightness if milky_on else 0.0,
    )


def sync_stars(scene: bpy.types.Scene) -> None:
    settings = scene.ouroskies
    if not settings.is_enabled:
        return
    owned = world.find_ouroskies_world(scene)
    if owned is None:
        return
    sync_stars_to_world(settings, owned)


def wire_stars_nodes(
    node_tree: bpy.types.NodeTree,
    light_path: bpy.types.ShaderNode,
    base_shader_socket,
) -> bpy.types.NodeSocket:
    """Add camera-only procedural stars + Milky band after airglow.

    Returns the combined shader socket for World Output.
    """
    nodes = node_tree.nodes
    links = node_tree.links

    # --- Shared view direction ---
    geo = nodes.new("ShaderNodeNewGeometry")
    geo.name = defaults.NODE_STAR_GEO
    geo.label = defaults.NODE_STAR_GEO
    geo.location = (-1100.0, -520.0)

    view = nodes.new("ShaderNodeVectorMath")
    view.name = defaults.NODE_STAR_VIEW
    view.label = defaults.NODE_STAR_VIEW
    view.location = (-920.0, -520.0)
    view.operation = "SCALE"
    if len(view.inputs) > 3:
        view.inputs[3].default_value = -1.0
    elif view.inputs.get("Scale") is not None:
        view.inputs["Scale"].default_value = -1.0

    norm = nodes.new("ShaderNodeVectorMath")
    norm.name = defaults.NODE_STAR_NORMALIZE
    norm.label = defaults.NODE_STAR_NORMALIZE
    norm.location = (-740.0, -520.0)
    norm.operation = "NORMALIZE"

    links.new(geo.outputs["Incoming"], view.inputs[0])
    links.new(view.outputs["Vector"], norm.inputs[0])

    # --- Horizon soft fade (before hard clip) ---
    sep = nodes.new("ShaderNodeSeparateXYZ")
    sep.name = defaults.NODE_STAR_HORIZON_SEP
    sep.label = defaults.NODE_STAR_HORIZON_SEP
    sep.location = (-560.0, -680.0)

    horizon = nodes.new("ShaderNodeMapRange")
    horizon.name = defaults.NODE_STAR_HORIZON
    horizon.label = defaults.NODE_STAR_HORIZON
    horizon.location = (-380.0, -680.0)
    horizon.clamp = True
    horizon.inputs["From Min"].default_value = defaults.STARS_HORIZON_ZERO_Z
    horizon.inputs["From Max"].default_value = defaults.STARS_HORIZON_FULL_Z
    horizon.inputs["To Min"].default_value = 0.0
    horizon.inputs["To Max"].default_value = 1.0

    links.new(norm.outputs["Vector"], sep.inputs["Vector"])
    links.new(sep.outputs["Z"], horizon.inputs["Value"])

    # --- Daylight fade + brightness uniforms ---
    fade = nodes.new("ShaderNodeValue")
    fade.name = defaults.NODE_STAR_FADE
    fade.label = defaults.NODE_STAR_FADE
    fade.location = (-380.0, -860.0)
    fade.outputs[0].default_value = 1.0

    bri = nodes.new("ShaderNodeValue")
    bri.name = defaults.NODE_STAR_BRIGHTNESS
    bri.label = defaults.NODE_STAR_BRIGHTNESS
    bri.location = (-380.0, -940.0)
    bri.outputs[0].default_value = defaults.STARS_BRIGHTNESS

    # --- Medium field (Voronoi) + sparse bright layer ---
    scale = nodes.new("ShaderNodeValue")
    scale.name = defaults.NODE_STAR_SCALE
    scale.label = defaults.NODE_STAR_SCALE
    scale.location = (-740.0, -360.0)
    scale.outputs[0].default_value = defaults.STARS_VORONOI_SCALE

    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.name = defaults.NODE_STAR_VORONOI
    voronoi.label = defaults.NODE_STAR_VORONOI
    voronoi.location = (-560.0, -360.0)
    voronoi.feature = "F1"
    voronoi.distance = "EUCLIDEAN"
    voronoi.voronoi_dimensions = "3D"

    inv = nodes.new("ShaderNodeMath")
    inv.name = defaults.NODE_STAR_INV
    inv.label = defaults.NODE_STAR_INV
    inv.location = (-380.0, -360.0)
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0

    power = nodes.new("ShaderNodeMath")
    power.name = defaults.NODE_STAR_POWER
    power.label = defaults.NODE_STAR_POWER
    power.location = (-200.0, -360.0)
    power.operation = "POWER"
    power.inputs[1].default_value = defaults.STARS_POWER

    scale_b = nodes.new("ShaderNodeValue")
    scale_b.name = defaults.NODE_STAR_SCALE_BRIGHT
    scale_b.label = defaults.NODE_STAR_SCALE_BRIGHT
    scale_b.location = (-740.0, -200.0)
    scale_b.outputs[0].default_value = (
        defaults.STARS_VORONOI_SCALE * defaults.STARS_BRIGHT_SCALE_FRAC
    )

    voronoi_b = nodes.new("ShaderNodeTexVoronoi")
    voronoi_b.name = defaults.NODE_STAR_VORONOI_BRIGHT
    voronoi_b.label = defaults.NODE_STAR_VORONOI_BRIGHT
    voronoi_b.location = (-560.0, -200.0)
    voronoi_b.feature = "F1"
    voronoi_b.distance = "EUCLIDEAN"
    voronoi_b.voronoi_dimensions = "3D"

    inv_b = nodes.new("ShaderNodeMath")
    inv_b.name = defaults.NODE_STAR_INV_BRIGHT
    inv_b.label = defaults.NODE_STAR_INV_BRIGHT
    inv_b.location = (-380.0, -200.0)
    inv_b.operation = "SUBTRACT"
    inv_b.inputs[0].default_value = 1.0

    power_b = nodes.new("ShaderNodeMath")
    power_b.name = defaults.NODE_STAR_POWER_BRIGHT
    power_b.label = defaults.NODE_STAR_POWER_BRIGHT
    power_b.location = (-200.0, -200.0)
    power_b.operation = "POWER"
    power_b.inputs[1].default_value = defaults.STARS_BRIGHT_POWER

    layers = nodes.new("ShaderNodeMath")
    layers.name = defaults.NODE_STAR_ADD
    layers.label = defaults.NODE_STAR_ADD
    layers.location = (-20.0, -280.0)
    layers.operation = "ADD"

    links.new(norm.outputs["Vector"], voronoi.inputs["Vector"])
    links.new(scale.outputs[0], voronoi.inputs["Scale"])
    links.new(voronoi.outputs["Distance"], inv.inputs[1])
    links.new(inv.outputs["Value"], power.inputs[0])

    links.new(norm.outputs["Vector"], voronoi_b.inputs["Vector"])
    links.new(scale_b.outputs[0], voronoi_b.inputs["Scale"])
    links.new(voronoi_b.outputs["Distance"], inv_b.inputs[1])
    links.new(inv_b.outputs["Value"], power_b.inputs[0])

    links.new(power.outputs["Value"], layers.inputs[0])
    links.new(power_b.outputs["Value"], layers.inputs[1])

    mul_h = nodes.new("ShaderNodeMath")
    mul_h.name = defaults.NODE_STAR_MUL_H
    mul_h.label = defaults.NODE_STAR_MUL_H
    mul_h.location = (160.0, -280.0)
    mul_h.operation = "MULTIPLY"

    mul_f = nodes.new("ShaderNodeMath")
    mul_f.name = defaults.NODE_STAR_MUL_F
    mul_f.label = defaults.NODE_STAR_MUL_F
    mul_f.location = (340.0, -280.0)
    mul_f.operation = "MULTIPLY"

    mul_b = nodes.new("ShaderNodeMath")
    mul_b.name = defaults.NODE_STAR_MUL_B
    mul_b.label = defaults.NODE_STAR_MUL_B
    mul_b.location = (520.0, -280.0)
    mul_b.operation = "MULTIPLY"

    cam_mul = nodes.new("ShaderNodeMath")
    cam_mul.name = defaults.NODE_STAR_CAM_MUL
    cam_mul.label = defaults.NODE_STAR_CAM_MUL
    cam_mul.location = (700.0, -280.0)
    cam_mul.operation = "MULTIPLY"

    color = nodes.new("ShaderNodeRGB")
    color.name = defaults.NODE_STAR_COLOR
    color.label = defaults.NODE_STAR_COLOR
    color.location = (520.0, -100.0)
    color.outputs[0].default_value = defaults.STARS_COLOR

    bg = nodes.new("ShaderNodeBackground")
    bg.name = defaults.NODE_STAR_BG
    bg.label = "Stars (look)"
    bg.location = (880.0, -200.0)

    add_stars = nodes.new("ShaderNodeAddShader")
    add_stars.name = defaults.NODE_STAR_ADD_SHADER
    add_stars.label = defaults.NODE_STAR_ADD_SHADER
    add_stars.location = (440.0, -40.0)

    links.new(layers.outputs["Value"], mul_h.inputs[0])
    links.new(horizon.outputs["Result"], mul_h.inputs[1])
    links.new(mul_h.outputs["Value"], mul_f.inputs[0])
    links.new(fade.outputs[0], mul_f.inputs[1])
    links.new(mul_f.outputs["Value"], mul_b.inputs[0])
    links.new(bri.outputs[0], mul_b.inputs[1])
    links.new(mul_b.outputs["Value"], cam_mul.inputs[0])
    links.new(light_path.outputs["Is Camera Ray"], cam_mul.inputs[1])
    links.new(color.outputs["Color"], bg.inputs["Color"])
    links.new(cam_mul.outputs["Value"], bg.inputs["Strength"])
    links.new(base_shader_socket, add_stars.inputs[0])
    links.new(bg.outputs["Background"], add_stars.inputs[1])

    # --- Milky band (structured glow — not a flat ribbon) ---
    milky_n = nodes.new("ShaderNodeCombineXYZ")
    milky_n.name = defaults.NODE_MILKY_NORMAL
    milky_n.label = defaults.NODE_MILKY_NORMAL
    milky_n.location = (-740.0, -1040.0)
    _set_combine_xyz(milky_n, _normalize3(defaults.MILKY_PLANE_NORMAL))

    milky_dot = nodes.new("ShaderNodeVectorMath")
    milky_dot.name = defaults.NODE_MILKY_DOT
    milky_dot.label = defaults.NODE_MILKY_DOT
    milky_dot.location = (-560.0, -1040.0)
    milky_dot.operation = "DOT_PRODUCT"

    milky_abs = nodes.new("ShaderNodeMath")
    milky_abs.name = defaults.NODE_MILKY_ABS
    milky_abs.label = defaults.NODE_MILKY_ABS
    milky_abs.location = (-380.0, -1040.0)
    milky_abs.operation = "ABSOLUTE"

    milky_map = nodes.new("ShaderNodeMapRange")
    milky_map.name = defaults.NODE_MILKY_MAP
    milky_map.label = defaults.NODE_MILKY_MAP
    milky_map.location = (-200.0, -1040.0)
    milky_map.clamp = True
    milky_map.inputs["From Min"].default_value = 0.0
    milky_map.inputs["From Max"].default_value = defaults.MILKY_HALF_WIDTH
    milky_map.inputs["To Min"].default_value = 1.0
    milky_map.inputs["To Max"].default_value = 0.0

    # Soft core: raise falloff so edges dissolve instead of a hard strip.
    milky_core = nodes.new("ShaderNodeMath")
    milky_core.name = defaults.NODE_MILKY_MAP + " Core"
    milky_core.label = "Milky Soft Core"
    milky_core.location = (-20.0, -1040.0)
    milky_core.operation = "POWER"
    milky_core.inputs[1].default_value = 1.65

    milky_noise = nodes.new("ShaderNodeTexNoise")
    milky_noise.name = defaults.NODE_MILKY_NOISE
    milky_noise.label = defaults.NODE_MILKY_NOISE
    milky_noise.location = (-200.0, -1200.0)
    milky_noise.noise_dimensions = "3D"
    milky_noise.inputs["Scale"].default_value = defaults.MILKY_NOISE_SCALE
    milky_noise.inputs["Detail"].default_value = 6.0
    milky_noise.inputs["Roughness"].default_value = 0.62

    milky_clump = nodes.new("ShaderNodeTexNoise")
    milky_clump.name = defaults.NODE_MILKY_CLUMP
    milky_clump.label = defaults.NODE_MILKY_CLUMP
    milky_clump.location = (-200.0, -1380.0)
    milky_clump.noise_dimensions = "3D"
    milky_clump.inputs["Scale"].default_value = defaults.MILKY_CLUMP_SCALE
    milky_clump.inputs["Detail"].default_value = 3.0
    milky_clump.inputs["Roughness"].default_value = 0.45

    # Dark lanes: push clump contrast (0.2 floor → bright cores / dark gaps).
    milky_clump_c = nodes.new("ShaderNodeMapRange")
    milky_clump_c.name = defaults.NODE_MILKY_CLUMP + " Contrast"
    milky_clump_c.label = "Milky Clump Contrast"
    milky_clump_c.location = (-20.0, -1380.0)
    milky_clump_c.clamp = True
    milky_clump_c.inputs["From Min"].default_value = 0.28
    milky_clump_c.inputs["From Max"].default_value = 0.78
    milky_clump_c.inputs["To Min"].default_value = 0.08
    milky_clump_c.inputs["To Max"].default_value = 1.0

    milky_dust = nodes.new("ShaderNodeTexVoronoi")
    milky_dust.name = defaults.NODE_MILKY_DUST
    milky_dust.label = defaults.NODE_MILKY_DUST
    milky_dust.location = (-200.0, -1560.0)
    milky_dust.feature = "F1"
    milky_dust.distance = "EUCLIDEAN"
    milky_dust.voronoi_dimensions = "3D"
    milky_dust.inputs["Scale"].default_value = defaults.MILKY_DUST_SCALE

    milky_dust_inv = nodes.new("ShaderNodeMath")
    milky_dust_inv.name = defaults.NODE_MILKY_DUST + " Inv"
    milky_dust_inv.label = "Milky Dust Inv"
    milky_dust_inv.location = (-20.0, -1560.0)
    milky_dust_inv.operation = "SUBTRACT"
    milky_dust_inv.inputs[0].default_value = 1.0

    milky_dust_pow = nodes.new("ShaderNodeMath")
    milky_dust_pow.name = defaults.NODE_MILKY_DUST + " Pow"
    milky_dust_pow.label = "Milky Dust Pow"
    milky_dust_pow.location = (160.0, -1560.0)
    milky_dust_pow.operation = "POWER"
    milky_dust_pow.inputs[1].default_value = 10.0

    # Structure = soft_core × (0.15 + 0.85×noise) × clump + 0.35×dust
    milky_struct = nodes.new("ShaderNodeMath")
    milky_struct.name = defaults.NODE_MILKY_MUL_N + " Struct"
    milky_struct.label = "Milky Struct Floor"
    milky_struct.location = (-20.0, -1200.0)
    milky_struct.operation = "MULTIPLY_ADD"
    milky_struct.inputs[1].default_value = 0.85
    milky_struct.inputs[2].default_value = 0.15

    milky_mul_n = nodes.new("ShaderNodeMath")
    milky_mul_n.name = defaults.NODE_MILKY_MUL_N
    milky_mul_n.label = defaults.NODE_MILKY_MUL_N
    milky_mul_n.location = (160.0, -1120.0)
    milky_mul_n.operation = "MULTIPLY"

    milky_mul_clump = nodes.new("ShaderNodeMath")
    milky_mul_clump.name = defaults.NODE_MILKY_MUL_N + " Clump"
    milky_mul_clump.label = "Milky × Clump"
    milky_mul_clump.location = (340.0, -1120.0)
    milky_mul_clump.operation = "MULTIPLY"

    milky_add_dust = nodes.new("ShaderNodeMath")
    milky_add_dust.name = defaults.NODE_MILKY_DUST + " Add"
    milky_add_dust.label = "Milky + Dust"
    milky_add_dust.location = (520.0, -1200.0)
    milky_add_dust.operation = "MULTIPLY_ADD"
    milky_add_dust.inputs[1].default_value = 0.45

    milky_str = nodes.new("ShaderNodeValue")
    milky_str.name = defaults.NODE_MILKY_STRENGTH
    milky_str.label = defaults.NODE_MILKY_STRENGTH
    milky_str.location = (340.0, -1340.0)
    milky_str.outputs[0].default_value = defaults.MILKY_STRENGTH

    milky_mul_s = nodes.new("ShaderNodeMath")
    milky_mul_s.name = defaults.NODE_MILKY_MUL_S
    milky_mul_s.label = defaults.NODE_MILKY_MUL_S
    milky_mul_s.location = (700.0, -1120.0)
    milky_mul_s.operation = "MULTIPLY"

    milky_mul_h = nodes.new("ShaderNodeMath")
    milky_mul_h.name = defaults.NODE_MILKY_MUL_H
    milky_mul_h.label = defaults.NODE_MILKY_MUL_H
    milky_mul_h.location = (880.0, -1120.0)
    milky_mul_h.operation = "MULTIPLY"

    milky_mul_f = nodes.new("ShaderNodeMath")
    milky_mul_f.name = defaults.NODE_MILKY_MUL_F
    milky_mul_f.label = defaults.NODE_MILKY_MUL_F
    milky_mul_f.location = (1060.0, -1120.0)
    milky_mul_f.operation = "MULTIPLY"

    milky_cam = nodes.new("ShaderNodeMath")
    milky_cam.name = defaults.NODE_MILKY_CAM_MUL
    milky_cam.label = defaults.NODE_MILKY_CAM_MUL
    milky_cam.location = (1240.0, -1120.0)
    milky_cam.operation = "MULTIPLY"

    milky_color = nodes.new("ShaderNodeRGB")
    milky_color.name = defaults.NODE_MILKY_COLOR
    milky_color.label = defaults.NODE_MILKY_COLOR
    milky_color.location = (880.0, -920.0)
    milky_color.outputs[0].default_value = defaults.MILKY_COLOR

    milky_cool = nodes.new("ShaderNodeRGB")
    milky_cool.name = defaults.NODE_MILKY_COLOR_COOL
    milky_cool.label = defaults.NODE_MILKY_COLOR_COOL
    milky_cool.location = (880.0, -800.0)
    milky_cool.outputs[0].default_value = defaults.MILKY_COLOR_COOL

    milky_cmix = nodes.new("ShaderNodeMix")
    milky_cmix.name = defaults.NODE_MILKY_COLOR_MIX
    milky_cmix.label = defaults.NODE_MILKY_COLOR_MIX
    milky_cmix.location = (1060.0, -880.0)
    milky_cmix.data_type = "RGBA"
    milky_cmix.blend_type = "MIX"

    milky_bg = nodes.new("ShaderNodeBackground")
    milky_bg.name = defaults.NODE_MILKY_BG
    milky_bg.label = "Milky Band (look)"
    milky_bg.location = (1420.0, -1000.0)

    milky_add = nodes.new("ShaderNodeAddShader")
    milky_add.name = defaults.NODE_MILKY_ADD
    milky_add.label = defaults.NODE_MILKY_ADD
    milky_add.location = (660.0, -40.0)

    links.new(norm.outputs["Vector"], milky_dot.inputs[0])
    links.new(milky_n.outputs["Vector"], milky_dot.inputs[1])
    links.new(milky_dot.outputs["Value"], milky_abs.inputs[0])
    links.new(milky_abs.outputs["Value"], milky_map.inputs["Value"])
    links.new(milky_map.outputs["Result"], milky_core.inputs[0])

    links.new(norm.outputs["Vector"], milky_noise.inputs["Vector"])
    links.new(norm.outputs["Vector"], milky_clump.inputs["Vector"])
    links.new(norm.outputs["Vector"], milky_dust.inputs["Vector"])
    links.new(milky_noise.outputs["Factor"], milky_struct.inputs[0])
    links.new(milky_clump.outputs["Factor"], milky_clump_c.inputs["Value"])
    links.new(milky_dust.outputs["Distance"], milky_dust_inv.inputs[1])
    links.new(milky_dust_inv.outputs["Value"], milky_dust_pow.inputs[0])

    links.new(milky_core.outputs["Value"], milky_mul_n.inputs[0])
    links.new(milky_struct.outputs["Value"], milky_mul_n.inputs[1])
    links.new(milky_mul_n.outputs["Value"], milky_mul_clump.inputs[0])
    links.new(milky_clump_c.outputs["Result"], milky_mul_clump.inputs[1])
    # multiply_add: dust * 0.45 + structured_band
    links.new(milky_dust_pow.outputs["Value"], milky_add_dust.inputs[0])
    links.new(milky_mul_clump.outputs["Value"], milky_add_dust.inputs[2])

    links.new(milky_add_dust.outputs["Value"], milky_mul_s.inputs[0])
    links.new(milky_str.outputs[0], milky_mul_s.inputs[1])
    links.new(milky_mul_s.outputs["Value"], milky_mul_h.inputs[0])
    links.new(horizon.outputs["Result"], milky_mul_h.inputs[1])
    links.new(milky_mul_h.outputs["Value"], milky_mul_f.inputs[0])
    links.new(fade.outputs[0], milky_mul_f.inputs[1])
    links.new(milky_mul_f.outputs["Value"], milky_cam.inputs[0])
    links.new(light_path.outputs["Is Camera Ray"], milky_cam.inputs[1])

    # Warm core → cool edges via clump factor.
    cmix_a = milky_cmix.inputs.get("A") or milky_cmix.inputs.get("A_Color") or milky_cmix.inputs[6]
    cmix_b = milky_cmix.inputs.get("B") or milky_cmix.inputs.get("B_Color") or milky_cmix.inputs[7]
    cmix_fac = milky_cmix.inputs.get("Factor") or milky_cmix.inputs[0]
    links.new(milky_clump_c.outputs["Result"], cmix_fac)
    links.new(milky_cool.outputs["Color"], cmix_a)
    links.new(milky_color.outputs["Color"], cmix_b)
    cmix_out = milky_cmix.outputs.get("Result_Color") or milky_cmix.outputs.get("Result")
    links.new(cmix_out, milky_bg.inputs["Color"])
    links.new(milky_cam.outputs["Value"], milky_bg.inputs["Strength"])
    links.new(add_stars.outputs["Shader"], milky_add.inputs[0])
    links.new(milky_bg.outputs["Background"], milky_add.inputs[1])

    return milky_add.outputs["Shader"]
