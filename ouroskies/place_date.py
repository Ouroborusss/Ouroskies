# SPDX-License-Identifier: GPL-3.0-or-later

"""Place/date evaluation — civil UI → UTC → sun/moon aim → Sky Texture."""

from __future__ import annotations

from datetime import datetime, timezone

import bpy
from bpy.app.handlers import persistent

from . import aim, world
from .ephemeris_moon import moon_azimuth_elevation
from .ephemeris_sun import sun_azimuth_elevation
from .time_util import civil_to_utc, zoneinfo_for


def format_status(settings, when_utc: datetime) -> tuple[str, str]:
    place = f"{settings.latitude:.2f}°, {settings.longitude:.2f}°"
    local = when_utc.astimezone(zoneinfo_for(settings.timezone))
    when = local.strftime("%Y-%m-%d %H:%M")
    return place, when


def evaluate(scene: bpy.types.Scene) -> None:
    """Evaluate place/date aim into Sky Texture + status + moon cache props."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        return
    if settings.aim_mode != "PLACE_DATE":
        return

    try:
        when_utc = civil_to_utc(settings)
    except ValueError:
        settings.status_when = "Invalid date"
        return

    use_refraction = settings.aim_refraction == "APPARENT"
    sun_az_geo, sun_el_geo = sun_azimuth_elevation(
        settings.latitude,
        settings.longitude,
        when_utc,
        refraction=False,
    )
    sun_az_app, sun_el_app = sun_azimuth_elevation(
        settings.latitude,
        settings.longitude,
        when_utc,
        refraction=True,
    )
    if use_refraction:
        sun_az, sun_el = sun_az_app, sun_el_app
    else:
        sun_az, sun_el = sun_az_geo, sun_el_geo

    moon_az, moon_el, _dist = moon_azimuth_elevation(
        settings.latitude,
        settings.longitude,
        when_utc,
        settings.altitude,
        refraction=use_refraction,
    )

    settings.refraction_diverges = abs(sun_el_app - sun_el_geo) > 0.05

    settings.evaluated_sun_azimuth_deg = sun_az
    settings.evaluated_sun_elevation_deg = sun_el
    settings.moon_azimuth_deg = moon_az
    settings.moon_elevation_deg = moon_el
    settings.status_place, settings.status_when = format_status(settings, when_utc)

    from . import lamps, looks

    looks.sync_looks(scene)
    lamps.sync_lamps(scene)

    owned = world.find_ouroskies_world(scene)
    if owned is None:
        return
    sky = world.find_sky_node(owned)
    if sky is None:
        return
    elevation, rotation = aim.alt_az_degrees_to_sky_radians(sun_el, sun_az)
    sky.sun_elevation = elevation
    sky.sun_rotation = rotation


@persistent
def frame_change_handler(scene: bpy.types.Scene) -> None:
    evaluate(scene)


def register_handlers() -> None:
    if frame_change_handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(frame_change_handler)


def unregister_handlers() -> None:
    handlers = bpy.app.handlers.frame_change_post
    while frame_change_handler in handlers:
        handlers.remove(frame_change_handler)


def stop_handlers() -> None:
    """Alias used by World Detach — keep handler registered; evaluate no-ops when disabled."""
    pass
