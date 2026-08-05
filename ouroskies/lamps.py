# SPDX-License-Identifier: GPL-3.0-or-later

"""Optional synced Sun / Moon lamps — Add/Remove, aim, strength, EEVEE helpers."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from . import defaults, looks


LAMP_KIND_SUN = "sun"
LAMP_KIND_MOON = "moon"


def _alt_az_to_direction(altitude_deg: float, azimuth_deg: float) -> Vector:
    from .aim import alt_az_to_direction

    return alt_az_to_direction(altitude_deg, azimuth_deg)


def _direction_from_sky(sky: bpy.types.ShaderNodeTexSky) -> Vector:
    """Match Cycles/EEVEE Nishita sun vector from Sky Texture RNA.

    ``spherical_to_direction(elev - π/2, rot - π/2)`` — same as Cycles ``sky.h``.
    """
    theta = float(sky.sun_elevation) - math.pi / 2.0
    phi = float(sky.sun_rotation) - math.pi / 2.0
    return Vector(
        (
            math.sin(theta) * math.cos(phi),
            math.sin(theta) * math.sin(phi),
            math.cos(theta),
        )
    ).normalized()


def _current_sun_alt_az(settings) -> tuple[float, float]:
    if settings.aim_mode == "PLACE_DATE":
        return (
            float(settings.evaluated_sun_elevation_deg),
            float(settings.evaluated_sun_azimuth_deg),
        )
    # Manual Elevation is a 360° orbit angle — fold to true alt/az for lamps/disk/UI.
    from .aim import orbit_to_alt_az

    return orbit_to_alt_az(float(settings.sun_elevation_deg), float(settings.sun_azimuth_deg))


def evaluate_moon_aim(settings) -> tuple[float, float]:
    """Moon alt/az for lamps + disk.

    Place/Date uses Meeus ephemeris. Manual places the moon 180° along the same
    elevation orbit so sun and moon rise/set on opposite horizons.
    """
    if settings.aim_mode == "MANUAL":
        from .aim import orbit_to_alt_az

        moon_orbit = float(settings.sun_elevation_deg) + 180.0
        moon_el, moon_az = orbit_to_alt_az(moon_orbit, float(settings.sun_azimuth_deg))
        if abs(settings.moon_azimuth_deg - moon_az) > 1e-6:
            settings.moon_azimuth_deg = moon_az
        if abs(settings.moon_elevation_deg - moon_el) > 1e-6:
            settings.moon_elevation_deg = moon_el
        return moon_el, moon_az
    return _refresh_moon_from_place(settings)


def _refresh_moon_from_place(settings) -> tuple[float, float]:
    """Moon from place/date ephemeris."""
    try:
        from .ephemeris_moon import moon_azimuth_elevation
        from .time_util import civil_to_utc

        when_utc = civil_to_utc(settings)
        use_refraction = settings.aim_refraction == "APPARENT"
        moon_az, moon_el, _dist = moon_azimuth_elevation(
            settings.latitude,
            settings.longitude,
            when_utc,
            settings.altitude,
            refraction=use_refraction,
        )
    except Exception:
        return float(settings.moon_elevation_deg), float(settings.moon_azimuth_deg)

    # Avoid RNA update recursion — write only when values change.
    if abs(settings.moon_azimuth_deg - moon_az) > 1e-6:
        settings.moon_azimuth_deg = moon_az
    if abs(settings.moon_elevation_deg - moon_el) > 1e-6:
        settings.moon_elevation_deg = moon_el
    return moon_el, moon_az


def _horizon_factor(altitude_deg: float) -> float:
    """1 above horizon, 0 below; smooth across ``LAMP_HORIZON_FADE_DEG``."""
    fade = defaults.LAMP_HORIZON_FADE_DEG
    if altitude_deg >= fade:
        return 1.0
    if altitude_deg <= -fade:
        return 0.0
    return 0.5 + 0.5 * (altitude_deg / fade)


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
    # Recover lamps created before tagging / after script reload by stable name.
    fallback = defaults.SUN_LAMP_NAME if kind == LAMP_KIND_SUN else defaults.MOON_LAMP_NAME
    for candidate in bpy.data.objects:
        if candidate.type != "LIGHT":
            continue
        if candidate.name == fallback or candidate.name.startswith(fallback + "."):
            _tag_lamp(candidate, kind)
            return candidate
    return None


def settings_lamp_name(scene: bpy.types.Scene, kind: str) -> str:
    settings = scene.ouroskies
    if kind == LAMP_KIND_SUN:
        return settings.sun_lamp_name or defaults.SUN_LAMP_NAME
    return settings.moon_lamp_name or defaults.MOON_LAMP_NAME


def _tag_lamp(obj: bpy.types.Object, kind: str) -> None:
    obj[defaults.LAMP_OWNED_KEY] = True
    obj[defaults.LAMP_KIND_KEY] = kind
    if obj.data is not None:
        obj.data[defaults.LAMP_OWNED_KEY] = True
        obj.data[defaults.LAMP_KIND_KEY] = kind


def _unique_light_name(base: str) -> str:
    if base not in bpy.data.lights:
        return base
    index = 1
    while f"{base}.{index:03d}" in bpy.data.lights:
        index += 1
    return f"{base}.{index:03d}"


def _unique_object_name(base: str) -> str:
    if base not in bpy.data.objects:
        return base
    index = 1
    while f"{base}.{index:03d}" in bpy.data.objects:
        index += 1
    return f"{base}.{index:03d}"


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

    base = defaults.SUN_LAMP_NAME if kind == LAMP_KIND_SUN else defaults.MOON_LAMP_NAME
    light_name = _unique_light_name(base)
    object_name = _unique_object_name(base)

    light = bpy.data.lights.new(name=light_name, type="SUN")
    light.energy = (
        defaults.SUN_LAMP_ENERGY if kind == LAMP_KIND_SUN else defaults.MOON_LAMP_ENERGY
    )
    light.angle = defaults.SUN_LAMP_ANGLE_RAD

    obj = bpy.data.objects.new(object_name, light)
    _tag_lamp(obj, kind)

    # Prefer the scene's collection; fall back to context scene collection.
    try:
        scene.collection.objects.link(obj)
    except RuntimeError:
        bpy.context.scene.collection.objects.link(obj)

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
    """Detach cleanup — owned lamps + moon disk."""
    remove_lamp(scene, LAMP_KIND_SUN)
    remove_lamp(scene, LAMP_KIND_MOON)
    from . import moon_disk

    moon_disk.remove_moon_disk(scene)


def sync_lamps(scene: bpy.types.Scene) -> None:
    """Aim and tint owned lamps from current sky aim + Looks WB / PA energies."""
    settings = scene.ouroskies
    wb = looks.kelvin_to_rgb(settings.white_balance_kelvin)

    sun_direction = None
    if settings.is_enabled:
        from . import world as world_mod

        owned = world_mod.find_ouroskies_world(scene)
        if owned is not None:
            sky = world_mod.find_sky_node(owned)
            if sky is not None:
                sun_direction = _direction_from_sky(sky)

    sun_obj = find_lamp_object(scene, LAMP_KIND_SUN)
    settings.has_sun_lamp = sun_obj is not None
    if sun_obj is not None:
        settings.sun_lamp_name = sun_obj.name
    if sun_obj is not None and sun_obj.data is not None:
        alt, az = _current_sun_alt_az(settings)
        direction = sun_direction if sun_direction is not None else _alt_az_to_direction(alt, az)
        _aim_sun_object(sun_obj, direction)
        sun_obj.data.color = wb
        factor = _horizon_factor(alt)
        sun_obj.data.energy = settings.sun_lamp_energy * factor
        # Keep the object visible; energy fade is enough below the horizon.
        sun_obj.hide_render = False
        sun_obj.hide_viewport = False

    moon_el, moon_az = evaluate_moon_aim(settings)
    moon_factor = _horizon_factor(moon_el)

    moon_obj = find_lamp_object(scene, LAMP_KIND_MOON)
    settings.has_moon_lamp = moon_obj is not None
    if moon_obj is not None:
        settings.moon_lamp_name = moon_obj.name
    if moon_obj is not None and moon_obj.data is not None:
        _aim_sun_object(moon_obj, _alt_az_to_direction(moon_el, moon_az))
        moon_obj.data.color = (
            wb[0] * 0.85,
            wb[1] * 0.92,
            min(1.0, wb[2] * 1.05),
        )
        moon_obj.data.energy = settings.moon_lamp_energy * moon_factor
        moon_obj.hide_render = False
        moon_obj.hide_viewport = False

    if settings.is_enabled:
        from . import moon_disk

        moon_disk.sync_moon_disk(
            scene,
            moon_el,
            moon_az,
            visible_factor=moon_factor,
        )

    owned_world = None
    if settings.is_enabled:
        from . import world as world_mod

        owned_world = world_mod.find_ouroskies_world(scene)
    _apply_sun_extraction(owned_world, sun_obj is not None)


def _aim_sun_object(obj: bpy.types.Object, direction: Vector) -> None:
    """Place the SUN light along ``direction``; emit toward the origin (-Z local)."""
    direction = direction.normalized()
    obj.rotation_mode = "QUATERNION"
    # Clear parenting so our transform is world-space.
    if obj.parent is not None:
        obj.parent = None
    obj.location = direction * defaults.LAMP_DISTANCE
    # Light travels opposite the toward-sun vector.
    obj.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
    obj.hide_viewport = False
    # Lamps light the scene; the moon disk is the visible celestial.
    if hasattr(obj, "visible_camera"):
        obj.visible_camera = False
    if hasattr(obj, "visible_shadow"):
        obj.visible_shadow = True


def resync_all_scenes() -> None:
    """Re-discover and aim lamps after register / script reload / file load.

    Safe to call from timers or handlers — no-ops while ``bpy.data`` is restricted
    (during ``register()``).
    """
    try:
        scenes = bpy.data.scenes
    except AttributeError:
        return
    for scene in scenes:
        if not hasattr(scene, "ouroskies"):
            continue
        try:
            sync_lamps(scene)
        except Exception:
            continue


def apply_pa_lamp_energies(scene: bpy.types.Scene) -> None:
    settings = scene.ouroskies
    settings.sun_lamp_energy = defaults.PA_SUN_LAMP_ENERGY
    settings.moon_lamp_energy = defaults.PA_MOON_LAMP_ENERGY
    sync_lamps(scene)
