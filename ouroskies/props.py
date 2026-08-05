# SPDX-License-Identifier: GPL-3.0-or-later

"""Scene PropertyGroup — cockpit source of truth."""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from . import defaults


def _on_atmosphere_update(self, context) -> None:
    from . import world

    world.sync_atmosphere(context.scene)
    if self.aim_mode == "PLACE_DATE":
        from . import place_date

        place_date.evaluate(context.scene)


def _on_aim_update(self, context) -> None:
    from . import aim, looks

    aim.sync_aim(context.scene)
    looks.sync_looks(context.scene)


def _on_place_date_update(self, context) -> None:
    from . import looks, place_date

    place_date.evaluate(context.scene)
    looks.sync_looks(context.scene)


def _on_looks_update(self, context) -> None:
    from . import looks

    looks.sync_looks(context.scene)


class OuroSkiesSettings(PropertyGroup):
    """Per-scene OuroSkies settings. Scene props are source of truth."""

    is_enabled: BoolProperty(
        name="Enabled",
        description="OuroSkies World is active on this scene (set by Enable / Detach)",
        default=False,
    )

    previous_world_name: StringProperty(
        name="Previous World",
        description="Name of the World restored on Detach (pointer only; provisional if deleted while active)",
        default="",
        options={"HIDDEN"},
    )

    aim_mode: EnumProperty(
        name="Aim",
        description="How primary sun and moon direction are driven",
        items=(
            ("MANUAL", "Manual", "Artist sets elevation and azimuth"),
            ("PLACE_DATE", "Place/Date", "Driven by place, date, and time"),
        ),
        default="MANUAL",
        update=_on_aim_update,
    )

    aim_refraction: EnumProperty(
        name="Aim Refraction",
        description="Apparent lifts near the horizon for prettier sunrise/set; Geometric is true direction. Eclipse math always uses Geometric",
        items=(
            ("APPARENT", "Apparent", "Horizon lift for prettier sunrise/set (default)"),
            ("GEOMETRIC", "Geometric", "True geometric direction"),
        ),
        default="APPARENT",
        update=_on_place_date_update,
    )

    sun_elevation_deg: FloatProperty(
        name="Sun Elevation",
        description="Primary sun altitude above the horizon in degrees (Manual aim). +Z up",
        default=defaults.MANUAL_SUN_ELEVATION_DEG,
        soft_min=-90.0,
        soft_max=90.0,
        min=-90.0,
        max=90.0,
        update=_on_aim_update,
    )
    sun_azimuth_deg: FloatProperty(
        name="Sun Azimuth",
        description="Primary sun azimuth in degrees eastward from north (Manual aim). +Y north, +X east",
        default=defaults.MANUAL_SUN_AZIMUTH_DEG,
        soft_min=0.0,
        soft_max=360.0,
        min=-360.0,
        max=720.0,
        update=_on_aim_update,
    )

    # Place / date (civil UI). Canonical evaluation is UTC via zoneinfo.
    latitude: FloatProperty(
        name="Latitude",
        description="Observer latitude in degrees (north positive)",
        default=defaults.PLACE_LATITUDE,
        soft_min=-90.0,
        soft_max=90.0,
        min=-90.0,
        max=90.0,
        update=_on_place_date_update,
    )
    longitude: FloatProperty(
        name="Longitude",
        description="Observer longitude in degrees (east positive)",
        default=defaults.PLACE_LONGITUDE,
        soft_min=-180.0,
        soft_max=180.0,
        min=-180.0,
        max=180.0,
        update=_on_place_date_update,
    )
    timezone: StringProperty(
        name="Timezone",
        description="IANA timezone id for civil date/time (e.g. America/New_York, UTC)",
        default=defaults.PLACE_TIMEZONE,
        update=_on_place_date_update,
    )
    year: IntProperty(
        name="Year",
        description="Civil year in the chosen timezone (animatable)",
        default=defaults.PLACE_YEAR,
        min=1,
        max=9999,
        update=_on_place_date_update,
    )
    month: IntProperty(
        name="Month",
        description="Civil month 1–12 (animatable)",
        default=defaults.PLACE_MONTH,
        min=1,
        max=12,
        update=_on_place_date_update,
    )
    day: IntProperty(
        name="Day",
        description="Civil day of month (animatable)",
        default=defaults.PLACE_DAY,
        min=1,
        max=31,
        update=_on_place_date_update,
    )
    time_hours: FloatProperty(
        name="Time",
        description="Civil time of day in hours (0–24, animatable; supports fractional minutes)",
        default=defaults.PLACE_TIME_HOURS,
        soft_min=0.0,
        soft_max=24.0,
        min=-24.0,
        max=48.0,
        update=_on_place_date_update,
    )

    status_place: StringProperty(
        name="Place",
        description="Place readout",
        default="—",
    )
    status_when: StringProperty(
        name="When",
        description="Date/time readout",
        default="—",
    )
    refraction_diverges: BoolProperty(
        name="Refraction Divergence",
        description="Apparent and Geometric sun elevation differ near the horizon",
        default=False,
        options={"HIDDEN"},
    )

    evaluated_sun_elevation_deg: FloatProperty(
        name="Evaluated Sun Elevation",
        description="Last place/date sun elevation (degrees)",
        default=0.0,
        options={"HIDDEN"},
    )
    evaluated_sun_azimuth_deg: FloatProperty(
        name="Evaluated Sun Azimuth",
        description="Last place/date sun azimuth (degrees)",
        default=0.0,
        options={"HIDDEN"},
    )
    moon_elevation_deg: FloatProperty(
        name="Moon Elevation",
        description="Evaluated moon altitude (degrees) — disk overlay later",
        default=0.0,
        options={"HIDDEN"},
    )
    moon_azimuth_deg: FloatProperty(
        name="Moon Azimuth",
        description="Evaluated moon azimuth (degrees) — disk overlay later",
        default=0.0,
        options={"HIDDEN"},
    )

    # Atmosphere — soft UI 0–10; type-beyond OK. Defaults are provisional.
    # Altitude is also observer height for place/date (mirrored in Setup).
    air: FloatProperty(
        name="Air",
        description="Air molecules (Sky Texture air_density). Soft range 0–10",
        default=defaults.ATMOSPHERE["air"],
        soft_min=0.0,
        soft_max=10.0,
        min=0.0,
        max=1000.0,
        update=_on_atmosphere_update,
    )
    dust: FloatProperty(
        name="Dust",
        description="Haze / pollution / water droplets (Sky Texture aerosol_density / Aerosols)",
        default=defaults.ATMOSPHERE["dust"],
        soft_min=0.0,
        soft_max=10.0,
        min=0.0,
        max=1000.0,
        update=_on_atmosphere_update,
    )
    ozone: FloatProperty(
        name="Ozone",
        description="Ozone density (Sky Texture ozone_density)",
        default=defaults.ATMOSPHERE["ozone"],
        soft_min=0.0,
        soft_max=10.0,
        min=0.0,
        max=1000.0,
        update=_on_atmosphere_update,
    )
    altitude: FloatProperty(
        name="Altitude",
        description="Observer / Sky Texture altitude in meters (Looks + Setup)",
        default=defaults.ATMOSPHERE["altitude"],
        soft_min=0.0,
        soft_max=10000.0,
        min=0.0,
        max=100000.0,
        subtype="DISTANCE",
        update=_on_atmosphere_update,
    )

    sky_strength: FloatProperty(
        name="Sky Strength",
        description="Visible sky / backdrop energy (camera Background Strength)",
        default=defaults.SKY_STRENGTH,
        soft_min=0.0,
        soft_max=10.0,
        min=0.0,
        max=1000.0,
        update=_on_looks_update,
    )
    world_contribution: FloatProperty(
        name="World Contribution",
        description="How hard the World lights the scene (non-camera / GI Background Strength)",
        default=defaults.WORLD_CONTRIBUTION,
        soft_min=0.0,
        soft_max=10.0,
        min=0.0,
        max=1000.0,
        update=_on_looks_update,
    )
    exposure: FloatProperty(
        name="Exposure",
        description="Color Management Exposure convenience mirror — never driven by eclipse FX",
        default=defaults.EXPOSURE,
        soft_min=-10.0,
        soft_max=10.0,
        update=_on_looks_update,
    )
    white_balance_kelvin: FloatProperty(
        name="White Balance",
        description="Kelvin tint applied after scatter (sky + later lamps)",
        default=defaults.WB_DAYLIGHT_KELVIN,
        soft_min=2000.0,
        soft_max=10000.0,
        min=1000.0,
        max=40000.0,
        update=_on_looks_update,
    )
    airglow_strength: FloatProperty(
        name="Airglow",
        description="Soft night-sky fill strength (fades with daylight)",
        default=defaults.AIRGLOW_STRENGTH,
        soft_min=0.0,
        soft_max=1.0,
        min=0.0,
        max=10.0,
        update=_on_looks_update,
    )
    airglow_tint: FloatVectorProperty(
        name="Airglow Tint",
        description="Artistic airglow color (default cool green-grey)",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=defaults.AIRGLOW_TINT,
        update=_on_looks_update,
    )


CLASSES = (OuroSkiesSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ouroskies = PointerProperty(type=OuroSkiesSettings)


def unregister() -> None:
    del bpy.types.Scene.ouroskies
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
