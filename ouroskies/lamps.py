# SPDX-License-Identifier: GPL-3.0-or-later

"""Optional synced Sun / Moon lamps — Add/Remove, aim, strength, EEVEE helpers."""

from __future__ import annotations

import math

import bpy
from mathutils import Euler, Vector

from . import defaults, looks


LAMP_KIND_SUN = "sun"
LAMP_KIND_MOON = "moon"


def _alt_az_to_direction(altitude_deg: float, azimuth_deg: float) -> Vector:
    """Unit vector toward the body in +Y-north / +Z-up frame."""
    alt = math.radians(altitude_deg)
    az = math.radians(azimuth_deg)
    return Vector(
        (
            math.cos(alt) * math.sin(az),
            math.cos(alt) * math.cos(az),
            math.sin(alt),
        )
    ).normalized()


def _current_sun_alt_az(settings) -> tuple[float, float]:
    if settings.aim_mode == "PLACE_DATE":
        return (
            float(settings.evaluated_sun_elevation_deg),
            float(settings.evaluated_sun_azimuth_deg),
        )
    return float(settings.sun_elevation_deg), float(settings.sun_azimuth_deg)


def _current_moon_alt_az(settings) -> tuple[float, float]:
    return float(settings.moon_elevation_deg), float(settings.moon_azimuth_deg)


def _is_owned_lamp(obj: bpy.types.Object, kind: str) -> bool:
    if obj is None or obj.type != "LIGHT":
        return False
    return bool(obj.get(defaults.LAMP_OWNED_KEY)) and obj.get(defaults.LAMP_KIND_KEY) == kind


def find_lamp_object(scene: bpy.types.Scene, kind: str) -> bpy.types.Object | None:
    name = settings_lamp_name(scene, kind)
    obj = bpy.data.objects.get(name)
    if obj is not None and _is_owned_lamp(obj, kind):
        return obj
    for candidate in bpy.data.objects:
        if _is_owned_lamp(candidate, kind):
            return candidate
    return None


def settings_lamp_name(scene: bpy.types.Scene, kind: str) -> str:
    settings = scene.ouroskies
    if kind == LAMP_KIND_SUN:
        return settings.sun_lamp_name or defaults.SUN_LAMP_NAME
    return settings.moon_lamp_name or defaults.MOON_LAMP_NAME


def _apply_sun_extraction(world: bpy.types.World | None, enabled_sun_lamp: bool) -> None:
    if world is None:
        return
    if hasattr(world, "sun_threshold"):
        # Prefer addon lamp as direct sun; avoid EEVEE double-sun extraction.
        world.sun_threshold = 0.0 if enabled_sun_lamp else defaults.WORLD_SUN_THRESHOLD_DEFAULT


def add_lamp(scene: bpy.types.Scene, kind: str) -> bpy.types.Object:
    existing = find_lamp_object(scene, kind)
    if existing is not None:
        sync_lamps(scene)
        return existing

    name = defaults.SUN_LAMP_NAME if kind == LAMP_KIND_SUN else defaults.MOON_LAMP_NAME
    light = bpy.data.lights.new(name=name, type="SUN")
    light.energy = (
        defaults.SUN_LAMP_ENERGY if kind == LAMP_KIND_SUN else defaults.MOON_LAMP_ENERGY
    )
    light.angle = defaults.SUN_LAMP_ANGLE_RAD

    obj = bpy.data.objects.new(name, light)
    obj[defaults.LAMP_OWNED_KEY] = True
    obj[defaults.LAMP_KIND_KEY] = kind
    scene.collection.objects.link(obj)

    settings = scene.ouroskies
    if kind == LAMP_KIND_SUN:
        settings.sun_lamp_name = obj.name
        settings.has_sun_lamp = True
    else:
        settings.moon_lamp_name = obj.name
        settings.has_moon_lamp = True

    sync_lamps(scene)
    return obj


def remove_lamp(scene: bpy.types.Scene, kind: str) -> bool:
    obj = find_lamp_object(scene, kind)
    settings = scene.ouroskies
    if obj is None:
        if kind == LAMP_KIND_SUN:
            settings.has_sun_lamp = False
            settings.sun_lamp_name = ""
        else:
            settings.has_moon_lamp = False
            settings.moon_lamp_name = ""
        _apply_sun_extraction(
            scene.world if scene.ouroskies.is_enabled else None,
            find_lamp_object(scene, LAMP_KIND_SUN) is not None,
        )
        return False

    light = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if light is not None and light.users == 0:
        bpy.data.lights.remove(light)

    if kind == LAMP_KIND_SUN:
        settings.has_sun_lamp = False
        settings.sun_lamp_name = ""
    else:
        settings.has_moon_lamp = False
        settings.moon_lamp_name = ""

    owned_world = None
    from . import world as world_mod

    if settings.is_enabled:
        owned_world = world_mod.find_ouroskies_world(scene)
    _apply_sun_extraction(owned_world, find_lamp_object(scene, LAMP_KIND_SUN) is not None)
    return True


def remove_all_owned_lamps(scene: bpy.types.Scene) -> None:
    """Detach cleanup — only objects tagged as OuroSkies-owned."""
    remove_lamp(scene, LAMP_KIND_SUN)
    remove_lamp(scene, LAMP_KIND_MOON)


def sync_lamps(scene: bpy.types.Scene) -> None:
    """Aim and tint owned lamps from current sky aim + Looks WB / PA energies."""
    settings = scene.ouroskies
    wb = looks.kelvin_to_rgb(settings.white_balance_kelvin)

    sun_obj = find_lamp_object(scene, LAMP_KIND_SUN)
    settings.has_sun_lamp = sun_obj is not None
    if sun_obj is not None:
        alt, az = _current_sun_alt_az(settings)
        _aim_sun_object(sun_obj, alt, az)
        sun_obj.data.color = wb
        # Sun Punch remaps later; for now PA / base energy.
        sun_obj.data.energy = settings.sun_lamp_energy

    moon_obj = find_lamp_object(scene, LAMP_KIND_MOON)
    settings.has_moon_lamp = moon_obj is not None
    if moon_obj is not None:
        alt, az = _current_moon_alt_az(settings)
        _aim_sun_object(moon_obj, alt, az)
        moon_obj.data.color = wb
        moon_obj.data.energy = settings.moon_lamp_energy

    owned_world = None
    if settings.is_enabled:
        from . import world as world_mod

        owned_world = world_mod.find_ouroskies_world(scene)
    _apply_sun_extraction(owned_world, sun_obj is not None)


def _aim_sun_object(obj: bpy.types.Object, altitude_deg: float, azimuth_deg: float) -> None:
    direction = _alt_az_to_direction(altitude_deg, azimuth_deg)
    # Place lamp along the sky direction; illuminate toward the origin (-Z local).
    obj.location = direction * defaults.LAMP_DISTANCE
    elev = math.radians(altitude_deg)
    az = math.radians(azimuth_deg)
    obj.rotation_euler = Euler((elev - math.pi / 2.0, 0.0, -az), "XYZ")


def apply_pa_lamp_energies(scene: bpy.types.Scene) -> None:
    settings = scene.ouroskies
    settings.sun_lamp_energy = defaults.PA_SUN_LAMP_ENERGY
    settings.moon_lamp_energy = defaults.PA_MOON_LAMP_ENERGY
    sync_lamps(scene)
