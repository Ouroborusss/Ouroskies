# SPDX-License-Identifier: GPL-3.0-or-later

"""Primary sun aim — altitude/azimuth → Sky Texture RNA (+Y north)."""

from __future__ import annotations

import math

import bpy

from . import world


def alt_az_degrees_to_sky_radians(altitude_deg: float, azimuth_deg: float) -> tuple[float, float]:
    """Map horizontal angles to Sky Texture props.

    Locked formula (pending Cycles sunrise → +X verify):
    ``sun_elevation = alt``, ``sun_rotation = -az`` (radians).
    Azimuth is eastward from north; +Y north, +X east, +Z up.
    """
    altitude_rad = math.radians(altitude_deg)
    azimuth_rad = math.radians(azimuth_deg)
    return altitude_rad, -azimuth_rad


def apply_manual_aim_to_sky(
    sky: bpy.types.ShaderNodeTexSky,
    settings: bpy.types.PropertyGroup,
) -> None:
    elevation, rotation = alt_az_degrees_to_sky_radians(
        settings.sun_elevation_deg,
        settings.sun_azimuth_deg,
    )
    sky.sun_elevation = elevation
    sky.sun_rotation = rotation


def sync_aim(scene: bpy.types.Scene) -> None:
    """Push aim onto the Sky Texture for the active Aim mode."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        return
    if settings.aim_mode == "PLACE_DATE":
        from . import place_date

        place_date.evaluate(scene)
        return
    owned = world.find_ouroskies_world(scene)
    if owned is None:
        return
    sky = world.find_sky_node(owned)
    if sky is None:
        return
    apply_manual_aim_to_sky(sky, settings)
