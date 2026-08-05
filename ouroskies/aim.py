# SPDX-License-Identifier: GPL-3.0-or-later

"""Primary sun aim — altitude/azimuth → Sky Texture RNA (+Y north)."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from . import world


def alt_az_to_direction(altitude_deg: float, azimuth_deg: float) -> Vector:
    """Unit vector toward a body. Altitude may be a ±180° orbit angle."""
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
    """Fold a ±180° elevation orbit into horizon altitude + compass azimuth.

    Orbit 0° = horizon toward ``path_azimuth``, +90° = zenith, ±180° = opposite
    horizon, −90° = nadir.
    """
    direction = alt_az_to_direction(orbit_deg, path_azimuth_deg)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, direction.z))))
    # Near zenith/nadir atan2 is unstable — keep the path azimuth.
    if abs(abs(alt) - 90.0) < 0.05:
        az = float(path_azimuth_deg) % 360.0
    else:
        az = math.degrees(math.atan2(direction.x, direction.y)) % 360.0
    return alt, az


def direction_to_sky_radians(direction: Vector) -> tuple[float, float]:
    """Inverse map a toward-sun vector → (sun_elevation, sun_rotation).

    Empirically matches the visible Nishita sun disc to our +Y-north lamps when
    ``sun_rotation = +azimuth`` (not ``-azimuth``). Mirrored Y without this sign.
    """
    d = direction.normalized()
    elev = math.asin(max(-1.0, min(1.0, d.z)))
    ce = math.cos(elev)
    if abs(ce) < 1e-8:
        rot = 0.0
    else:
        # x = ce * sin(az), y = ce * cos(az)  →  rot = +azimuth
        rot = math.atan2(d.x / ce, d.y / ce)
    return elev, rot


def alt_az_degrees_to_sky_radians(altitude_deg: float, azimuth_deg: float) -> tuple[float, float]:
    """Map Manual/Place angles to Sky Texture props via the shared direction."""
    direction = alt_az_to_direction(altitude_deg, azimuth_deg)
    return direction_to_sky_radians(direction)


def apply_direction_to_sky(sky: bpy.types.ShaderNodeTexSky, direction: Vector) -> None:
    """Write Nishita sun aim from a world-space toward-sun unit vector."""
    elev, rot = direction_to_sky_radians(direction)
    sky.sun_elevation = elev
    sky.sun_rotation = rot
    if hasattr(sky, "sun_disc"):
        sky.sun_disc = True
    # Avoid leftover mapping offsets flipping the disc.
    sky.texture_mapping.rotation = (0.0, 0.0, 0.0)
    sky.texture_mapping.translation = (0.0, 0.0, 0.0)


def apply_manual_aim_to_sky(
    sky: bpy.types.ShaderNodeTexSky,
    settings: bpy.types.PropertyGroup,
) -> None:
    direction = alt_az_to_direction(
        settings.sun_elevation_deg,
        settings.sun_azimuth_deg,
    )
    apply_direction_to_sky(sky, direction)


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
