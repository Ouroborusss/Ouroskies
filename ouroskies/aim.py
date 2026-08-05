# SPDX-License-Identifier: GPL-3.0-or-later

"""Primary sun aim — altitude/azimuth → Sky Texture RNA (+Y north)."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from . import world


def alt_az_to_direction(altitude_deg: float, azimuth_deg: float) -> Vector:
    """Unit vector toward a body. Altitude may be a full 360° orbit angle."""
    alt = math.radians(altitude_deg)
    az = math.radians(azimuth_deg)
    return Vector(
        (
            math.cos(alt) * math.sin(az),
            math.cos(alt) * math.cos(az),
            math.sin(alt),
        )
    ).normalized()


def orbit_to_alt_az(orbit_deg: float, path_azimuth_deg: float) -> tuple[float, float]:
    """Fold a 360° elevation orbit into horizon altitude + compass azimuth.

    Orbit 0° = horizon toward ``path_azimuth``, 90° = zenith, 180° = opposite
    horizon, 270° = nadir. Used so Manual Elevation can loop continuously.
    """
    direction = alt_az_to_direction(orbit_deg, path_azimuth_deg)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, direction.z))))
    az = math.degrees(math.atan2(direction.x, direction.y)) % 360.0
    return alt, az


def alt_az_degrees_to_sky_radians(altitude_deg: float, azimuth_deg: float) -> tuple[float, float]:
    """Map horizontal angles to Sky Texture props.

    Locked formula (pending Cycles sunrise → +X verify):
    ``sun_elevation = alt``, ``sun_rotation = -az`` (radians).
    Azimuth is eastward from north; +Y north, +X east, +Z up.
    """
    # Sky Texture expects true altitude, not a wrapped orbit angle.
    alt, az = orbit_to_alt_az(altitude_deg, azimuth_deg)
    return math.radians(alt), -math.radians(az)


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


def reset_manual_sun(scene: bpy.types.Scene) -> None:
    """Restore provisional Manual sun elev/az and sync if Aim is Manual."""
    from . import defaults

    settings = scene.ouroskies
    settings.sun_elevation_deg = defaults.MANUAL_SUN_ELEVATION_DEG
    settings.sun_azimuth_deg = defaults.MANUAL_SUN_AZIMUTH_DEG
    sync_aim(scene)


def sync_aim(scene: bpy.types.Scene) -> None:
    """Push aim onto the Sky Texture for the active Aim mode."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        from . import lamps

        lamps.sync_lamps(scene)
        return
    if settings.aim_mode == "PLACE_DATE":
        from . import place_date

        place_date.evaluate(scene)
        return
    owned = world.find_ouroskies_world(scene)
    if owned is not None:
        sky = world.find_sky_node(owned)
        if sky is not None:
            apply_manual_aim_to_sky(sky, settings)
    from . import lamps

    lamps.sync_lamps(scene)
