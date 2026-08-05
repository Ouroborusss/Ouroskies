# SPDX-License-Identifier: GPL-3.0-or-later

"""Looks stack — Sky Strength, World Contribution, WB, Airglow, Exposure mirror."""

from __future__ import annotations

import math

import bpy

from . import defaults, world


def kelvin_to_rgb(kelvin: float) -> tuple[float, float, float]:
    """Approximate blackbody RGB (0–1) for white-balance tinting.

    Based on Tanner Helland's public-domain temperature→RGB fit.
    """
    temp = max(1000.0, min(float(kelvin), 40000.0)) / 100.0
    if temp <= 66.0:
        r = 255.0
        g = 99.4708025861 * math.log(temp) - 161.1195681661
    else:
        r = 329.698727446 * ((temp - 60.0) ** -0.1332047592)
        g = 288.1221695283 * ((temp - 60.0) ** -0.0755148492)
    if temp >= 66.0:
        b = 255.0
    elif temp <= 19.0:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(temp - 10.0) - 305.0447927307

    def _clamp01(channel: float) -> float:
        return max(0.0, min(channel, 255.0)) / 255.0

    return _clamp01(r), _clamp01(g), _clamp01(b)


def _current_sun_elevation_deg(settings) -> float:
    if settings.aim_mode == "PLACE_DATE":
        return float(settings.evaluated_sun_elevation_deg)
    return float(settings.sun_elevation_deg)


def airglow_daylight_fade(sun_elevation_deg: float) -> float:
    """1 at night, 0 in daylight. provisional: fade between -6° and +6°."""
    low = defaults.AIRGLOW_FADE_LOW_DEG
    high = defaults.AIRGLOW_FADE_HIGH_DEG
    if sun_elevation_deg <= low:
        return 1.0
    if sun_elevation_deg >= high:
        return 0.0
    return 1.0 - (sun_elevation_deg - low) / (high - low)


def find_node(node_tree: bpy.types.NodeTree, name: str):
    return node_tree.nodes.get(name)


def sync_looks_to_world(settings, owned: bpy.types.World) -> None:
    """Push Looks props into an OuroSkies World node tree (no Exposure)."""
    if owned is None or owned.node_tree is None:
        return
    nt = owned.node_tree

    wb = find_node(nt, defaults.NODE_WB_COLOR)
    if wb is not None:
        rgb = kelvin_to_rgb(settings.white_balance_kelvin)
        wb.outputs[0].default_value = (rgb[0], rgb[1], rgb[2], 1.0)

    bg_cam = find_node(nt, defaults.NODE_BG_CAMERA)
    if bg_cam is not None:
        bg_cam.inputs["Strength"].default_value = settings.sky_strength

    bg_light = find_node(nt, defaults.NODE_BG_LIGHT)
    if bg_light is not None:
        bg_light.inputs["Strength"].default_value = settings.world_contribution

    bg_glow = find_node(nt, defaults.NODE_BG_AIRGLOW)
    rgb_glow = find_node(nt, defaults.NODE_AIRGLOW_COLOR)
    if rgb_glow is not None:
        tint = settings.airglow_tint
        rgb_glow.outputs[0].default_value = (tint[0], tint[1], tint[2], 1.0)
    if bg_glow is not None:
        fade = airglow_daylight_fade(_current_sun_elevation_deg(settings))
        bg_glow.inputs["Strength"].default_value = settings.airglow_strength * fade


def sync_looks(scene: bpy.types.Scene) -> None:
    """Push Looks props into the OuroSkies World graph and Exposure mirror."""
    settings = scene.ouroskies
    scene.view_settings.exposure = settings.exposure

    if not settings.is_enabled:
        return
    owned = world.find_ouroskies_world(scene)
    sync_looks_to_world(settings, owned)


def physically_accurate(scene: bpy.types.Scene) -> None:
    """Apply Physically Accurate brightness + WB; do not touch Exposure or atmosphere."""
    settings = scene.ouroskies
    settings.sky_strength = defaults.PA_SKY_STRENGTH
    settings.world_contribution = defaults.PA_WORLD_CONTRIBUTION
    settings.white_balance_kelvin = defaults.WB_DAYLIGHT_KELVIN
    settings.airglow_strength = defaults.AIRGLOW_STRENGTH
    settings.airglow_tint = defaults.AIRGLOW_TINT
    sync_looks(scene)


def set_wb_preset(scene: bpy.types.Scene, preset: str) -> None:
    settings = scene.ouroskies
    kelvin = {
        "DAYLIGHT": defaults.WB_DAYLIGHT_KELVIN,
        "CLOUDY": defaults.WB_CLOUDY_KELVIN,
        "SHADE": defaults.WB_SHADE_KELVIN,
        "WARM": defaults.WB_WARM_KELVIN,
    }.get(preset, defaults.WB_DAYLIGHT_KELVIN)
    settings.white_balance_kelvin = kelvin
    sync_looks(scene)
