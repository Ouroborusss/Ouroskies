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
    """Push Density / Brightness / Milky amount + noise scale into World uniforms."""
    if owned is None or owned.node_tree is None:
        return
    nodes = owned.node_tree.nodes

    density = max(0.0, float(settings.stars_density))
    brightness = max(0.0, float(settings.stars_brightness))
    if defaults.STARS_USE_DAYLIGHT_FADE:
        fade = stars_daylight_fade(_current_sun_elevation_deg(settings))
    else:
        fade = 1.0
    milky = max(0.0, float(settings.stars_milky_band))
    noise_mul = max(0.05, float(settings.stars_milky_noise))

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
        defaults.MILKY_STRENGTH * brightness * milky,
    )
    _set_value_output(nodes.get(defaults.NODE_MILKY_SCALE), noise_mul)

    # Drive texture scales from the shared multiplier (base × slider).
    mist = nodes.get(defaults.NODE_MILKY_NOISE)
    lane = nodes.get(defaults.NODE_MILKY_LANE)
    clump = nodes.get(defaults.NODE_MILKY_CLUMP)
    dust = nodes.get(defaults.NODE_MILKY_DUST)
    if mist is not None:
        mist.inputs["Scale"].default_value = defaults.MILKY_NOISE_SCALE * noise_mul
    if lane is not None:
        lane.inputs["Scale"].default_value = defaults.MILKY_LANE_SCALE * noise_mul
    if clump is not None:
        clump.inputs["Scale"].default_value = defaults.MILKY_CLUMP_SCALE * noise_mul
    if dust is not None:
        dust.inputs["Scale"].default_value = defaults.MILKY_DUST_SCALE * noise_mul


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

    # --- Milky band look F: mist + dust lanes + fine sparkle (soft, no hard ribbon) ---
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

    # Soft core falloff (blur-ish) — band^1.4 keeps the limb soft.
    milky_soft = nodes.new("ShaderNodeMath")
    milky_soft.name = defaults.NODE_MILKY_MAP + " Soft"
    milky_soft.label = "Milky Soft Core"
    milky_soft.location = (-20.0, -1040.0)
    milky_soft.operation = "POWER"
    milky_soft.inputs[1].default_value = 1.4

    # Shared noise-scale multiplier (driven by Milky Noise slider).
    milky_scale = nodes.new("ShaderNodeValue")
    milky_scale.name = defaults.NODE_MILKY_SCALE
    milky_scale.label = defaults.NODE_MILKY_SCALE
    milky_scale.location = (-740.0, -1220.0)
    milky_scale.outputs[0].default_value = defaults.STARS_MILKY_NOISE

    mist = nodes.new("ShaderNodeTexNoise")
    mist.name = defaults.NODE_MILKY_NOISE
    mist.label = defaults.NODE_MILKY_NOISE
    mist.location = (-200.0, -1200.0)
    mist.noise_dimensions = "3D"
    mist.inputs["Scale"].default_value = defaults.MILKY_NOISE_SCALE
    mist.inputs["Detail"].default_value = 5.0
    mist.inputs["Roughness"].default_value = 0.58

    lane = nodes.new("ShaderNodeTexNoise")
    lane.name = defaults.NODE_MILKY_LANE
    lane.label = defaults.NODE_MILKY_LANE
    lane.location = (-200.0, -1380.0)
    lane.noise_dimensions = "3D"
    lane.inputs["Scale"].default_value = defaults.MILKY_LANE_SCALE
    lane.inputs["Detail"].default_value = 3.0
    lane.inputs["Roughness"].default_value = 0.45

    clump = nodes.new("ShaderNodeTexNoise")
    clump.name = defaults.NODE_MILKY_CLUMP
    clump.label = defaults.NODE_MILKY_CLUMP
    clump.location = (-200.0, -1560.0)
    clump.noise_dimensions = "3D"
    clump.inputs["Scale"].default_value = defaults.MILKY_CLUMP_SCALE
    clump.inputs["Detail"].default_value = 3.0
    clump.inputs["Roughness"].default_value = 0.5

    dust = nodes.new("ShaderNodeTexVoronoi")
    dust.name = defaults.NODE_MILKY_DUST
    dust.label = defaults.NODE_MILKY_DUST
    dust.location = (-200.0, -1740.0)
    dust.feature = "F1"
    dust.distance = "EUCLIDEAN"
    dust.voronoi_dimensions = "3D"
    dust.inputs["Scale"].default_value = defaults.MILKY_DUST_SCALE

    # Mist body: 0.35 + 0.65 * mist
    mist_body = nodes.new("ShaderNodeMath")
    mist_body.name = defaults.NODE_MILKY_NOISE + " Body"
    mist_body.label = "Milky Mist Body"
    mist_body.location = (-20.0, -1200.0)
    mist_body.operation = "MULTIPLY_ADD"
    mist_body.inputs[1].default_value = 0.65
    mist_body.inputs[2].default_value = 0.35

    # Lane: abs(noise-0.5)*2 → soft contrast, then (1 - lane_amt*(1-lane)*soft)
    lane_sub = nodes.new("ShaderNodeMath")
    lane_sub.name = defaults.NODE_MILKY_LANE + " Sub"
    lane_sub.label = "Lane Center"
    lane_sub.location = (-20.0, -1380.0)
    lane_sub.operation = "SUBTRACT"
    lane_sub.inputs[1].default_value = 0.5

    lane_abs = nodes.new("ShaderNodeMath")
    lane_abs.name = defaults.NODE_MILKY_LANE + " Abs"
    lane_abs.label = "Lane Abs"
    lane_abs.location = (160.0, -1380.0)
    lane_abs.operation = "ABSOLUTE"

    lane_wide = nodes.new("ShaderNodeMath")
    lane_wide.name = defaults.NODE_MILKY_LANE + " Wide"
    lane_wide.label = "Lane ×2"
    lane_wide.location = (340.0, -1380.0)
    lane_wide.operation = "MULTIPLY"
    lane_wide.inputs[1].default_value = 2.0

    lane_pow = nodes.new("ShaderNodeMath")
    lane_pow.name = defaults.NODE_MILKY_LANE + " Pow"
    lane_pow.label = "Lane Soft"
    lane_pow.location = (520.0, -1380.0)
    lane_pow.operation = "POWER"
    lane_pow.inputs[1].default_value = 1.35

    # dark = (1 - lane) * soft * lane_amt
    lane_inv = nodes.new("ShaderNodeMath")
    lane_inv.name = defaults.NODE_MILKY_LANE + " Inv"
    lane_inv.label = "Lane Inv"
    lane_inv.location = (700.0, -1380.0)
    lane_inv.operation = "SUBTRACT"
    lane_inv.inputs[0].default_value = 1.0

    lane_cut = nodes.new("ShaderNodeMath")
    lane_cut.name = defaults.NODE_MILKY_LANE + " Cut"
    lane_cut.label = "Lane Cut"
    lane_cut.location = (880.0, -1380.0)
    lane_cut.operation = "MULTIPLY"

    lane_amt = nodes.new("ShaderNodeMath")
    lane_amt.name = defaults.NODE_MILKY_LANE + " Amt"
    lane_amt.label = "Lane Amount"
    lane_amt.location = (1060.0, -1380.0)
    lane_amt.operation = "MULTIPLY"
    lane_amt.inputs[1].default_value = defaults.MILKY_LANE_AMOUNT

    lane_keep = nodes.new("ShaderNodeMath")
    lane_keep.name = defaults.NODE_MILKY_LANE + " Keep"
    lane_keep.label = "1 − Cut"
    lane_keep.location = (1240.0, -1380.0)
    lane_keep.operation = "SUBTRACT"
    lane_keep.inputs[0].default_value = 1.0

    # Clump: 0.4 + 0.6 * clump
    clump_body = nodes.new("ShaderNodeMath")
    clump_body.name = defaults.NODE_MILKY_CLUMP + " Body"
    clump_body.label = "Milky Clump Body"
    clump_body.location = (-20.0, -1560.0)
    clump_body.operation = "MULTIPLY_ADD"
    clump_body.inputs[1].default_value = 0.6
    clump_body.inputs[2].default_value = 0.4

    # Dust sparkle: (1 - voronoi)^10 * soft
    dust_inv = nodes.new("ShaderNodeMath")
    dust_inv.name = defaults.NODE_MILKY_DUST + " Inv"
    dust_inv.label = "Dust Inv"
    dust_inv.location = (-20.0, -1740.0)
    dust_inv.operation = "SUBTRACT"
    dust_inv.inputs[0].default_value = 1.0

    dust_pow = nodes.new("ShaderNodeMath")
    dust_pow.name = defaults.NODE_MILKY_DUST + " Pow"
    dust_pow.label = "Dust Pow"
    dust_pow.location = (160.0, -1740.0)
    dust_pow.operation = "POWER"
    dust_pow.inputs[1].default_value = 10.0

    # dens = soft * mist * lane_keep * clump + dust*0.35*soft
    dens_a = nodes.new("ShaderNodeMath")
    dens_a.name = "OuroSkies Milky Dens A"
    dens_a.label = "Soft × Mist"
    dens_a.location = (160.0, -1120.0)
    dens_a.operation = "MULTIPLY"

    dens_b = nodes.new("ShaderNodeMath")
    dens_b.name = "OuroSkies Milky Dens B"
    dens_b.label = "× Lane Keep"
    dens_b.location = (340.0, -1120.0)
    dens_b.operation = "MULTIPLY"

    dens_c = nodes.new("ShaderNodeMath")
    dens_c.name = "OuroSkies Milky Dens C"
    dens_c.label = "× Clump"
    dens_c.location = (520.0, -1120.0)
    dens_c.operation = "MULTIPLY"

    dust_add = nodes.new("ShaderNodeMath")
    dust_add.name = defaults.NODE_MILKY_DUST + " Add"
    dust_add.label = "Dens + Dust"
    dust_add.location = (700.0, -1200.0)
    dust_add.operation = "MULTIPLY_ADD"
    dust_add.inputs[1].default_value = 0.35

    milky_str = nodes.new("ShaderNodeValue")
    milky_str.name = defaults.NODE_MILKY_STRENGTH
    milky_str.label = defaults.NODE_MILKY_STRENGTH
    milky_str.location = (520.0, -1340.0)
    milky_str.outputs[0].default_value = defaults.MILKY_STRENGTH

    milky_mul_s = nodes.new("ShaderNodeMath")
    milky_mul_s.name = defaults.NODE_MILKY_MUL_S
    milky_mul_s.label = defaults.NODE_MILKY_MUL_S
    milky_mul_s.location = (880.0, -1120.0)
    milky_mul_s.operation = "MULTIPLY"

    milky_mul_h = nodes.new("ShaderNodeMath")
    milky_mul_h.name = defaults.NODE_MILKY_MUL_H
    milky_mul_h.label = defaults.NODE_MILKY_MUL_H
    milky_mul_h.location = (1060.0, -1120.0)
    milky_mul_h.operation = "MULTIPLY"

    milky_mul_f = nodes.new("ShaderNodeMath")
    milky_mul_f.name = defaults.NODE_MILKY_MUL_F
    milky_mul_f.label = defaults.NODE_MILKY_MUL_F
    milky_mul_f.location = (1240.0, -1120.0)
    milky_mul_f.operation = "MULTIPLY"

    milky_cam = nodes.new("ShaderNodeMath")
    milky_cam.name = defaults.NODE_MILKY_CAM_MUL
    milky_cam.label = defaults.NODE_MILKY_CAM_MUL
    milky_cam.location = (1420.0, -1120.0)
    milky_cam.operation = "MULTIPLY"

    milky_color = nodes.new("ShaderNodeRGB")
    milky_color.name = defaults.NODE_MILKY_COLOR
    milky_color.label = defaults.NODE_MILKY_COLOR
    milky_color.location = (1240.0, -920.0)
    milky_color.outputs[0].default_value = defaults.MILKY_COLOR

    milky_bg = nodes.new("ShaderNodeBackground")
    milky_bg.name = defaults.NODE_MILKY_BG
    milky_bg.label = "Milky Band (look)"
    milky_bg.location = (1600.0, -1000.0)

    milky_add = nodes.new("ShaderNodeAddShader")
    milky_add.name = defaults.NODE_MILKY_ADD
    milky_add.label = defaults.NODE_MILKY_ADD
    milky_add.location = (660.0, -40.0)

    links.new(norm.outputs["Vector"], milky_dot.inputs[0])
    links.new(milky_n.outputs["Vector"], milky_dot.inputs[1])
    links.new(milky_dot.outputs["Value"], milky_abs.inputs[0])
    links.new(milky_abs.outputs["Value"], milky_map.inputs["Value"])
    links.new(milky_map.outputs["Result"], milky_soft.inputs[0])

    links.new(norm.outputs["Vector"], mist.inputs["Vector"])
    links.new(norm.outputs["Vector"], lane.inputs["Vector"])
    links.new(norm.outputs["Vector"], clump.inputs["Vector"])
    links.new(norm.outputs["Vector"], dust.inputs["Vector"])

    links.new(mist.outputs["Factor"], mist_body.inputs[0])
    links.new(lane.outputs["Factor"], lane_sub.inputs[0])
    links.new(lane_sub.outputs["Value"], lane_abs.inputs[0])
    links.new(lane_abs.outputs["Value"], lane_wide.inputs[0])
    links.new(lane_wide.outputs["Value"], lane_pow.inputs[0])
    links.new(lane_pow.outputs["Value"], lane_inv.inputs[1])
    links.new(lane_inv.outputs["Value"], lane_cut.inputs[0])
    links.new(milky_soft.outputs["Value"], lane_cut.inputs[1])
    links.new(lane_cut.outputs["Value"], lane_amt.inputs[0])
    links.new(lane_amt.outputs["Value"], lane_keep.inputs[1])

    links.new(clump.outputs["Factor"], clump_body.inputs[0])
    links.new(dust.outputs["Distance"], dust_inv.inputs[1])
    links.new(dust_inv.outputs["Value"], dust_pow.inputs[0])

    links.new(milky_soft.outputs["Value"], dens_a.inputs[0])
    links.new(mist_body.outputs["Value"], dens_a.inputs[1])
    links.new(dens_a.outputs["Value"], dens_b.inputs[0])
    links.new(lane_keep.outputs["Value"], dens_b.inputs[1])
    links.new(dens_b.outputs["Value"], dens_c.inputs[0])
    links.new(clump_body.outputs["Value"], dens_c.inputs[1])
    # multiply_add: dust_pow * 0.35 + dens_c  — also gate dust by soft
    dust_gate = nodes.new("ShaderNodeMath")
    dust_gate.name = defaults.NODE_MILKY_DUST + " Gate"
    dust_gate.label = "Dust × Soft"
    dust_gate.location = (340.0, -1740.0)
    dust_gate.operation = "MULTIPLY"
    links.new(dust_pow.outputs["Value"], dust_gate.inputs[0])
    links.new(milky_soft.outputs["Value"], dust_gate.inputs[1])
    links.new(dust_gate.outputs["Value"], dust_add.inputs[0])
    links.new(dens_c.outputs["Value"], dust_add.inputs[2])

    links.new(dust_add.outputs["Value"], milky_mul_s.inputs[0])
    links.new(milky_str.outputs[0], milky_mul_s.inputs[1])
    links.new(milky_mul_s.outputs["Value"], milky_mul_h.inputs[0])
    links.new(horizon.outputs["Result"], milky_mul_h.inputs[1])
    links.new(milky_mul_h.outputs["Value"], milky_mul_f.inputs[0])
    links.new(fade.outputs[0], milky_mul_f.inputs[1])
    links.new(milky_mul_f.outputs["Value"], milky_cam.inputs[0])
    links.new(light_path.outputs["Is Camera Ray"], milky_cam.inputs[1])
    links.new(milky_color.outputs["Color"], milky_bg.inputs["Color"])
    links.new(milky_cam.outputs["Value"], milky_bg.inputs["Strength"])
    links.new(add_stars.outputs["Shader"], milky_add.inputs[0])
    links.new(milky_bg.outputs["Background"], milky_add.inputs[1])

    return milky_add.outputs["Shader"]
