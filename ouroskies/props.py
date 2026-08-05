# SPDX-License-Identifier: GPL-3.0-or-later

"""Scene PropertyGroup — cockpit source of truth."""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from . import defaults


def _on_atmosphere_update(self, context) -> None:
    from . import world

    world.sync_atmosphere(context.scene)


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
    )

    aim_refraction: EnumProperty(
        name="Aim Refraction",
        description="Apparent lifts near the horizon for prettier sunrise/set; Geometric is true direction. Eclipse math always uses Geometric",
        items=(
            ("APPARENT", "Apparent", "Horizon lift for prettier sunrise/set (default)"),
            ("GEOMETRIC", "Geometric", "True geometric direction"),
        ),
        default="APPARENT",
    )

    status_place: StringProperty(
        name="Place",
        description="Place readout (filled when Place/Date aiming lands)",
        default="—",
    )
    status_when: StringProperty(
        name="When",
        description="Date/time readout (filled when Place/Date aiming lands)",
        default="—",
    )

    # Atmosphere — soft UI 0–10; type-beyond OK. Defaults are provisional.
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
        description="Observer altitude in meters (Sky Texture altitude). Mirrored in Setup later",
        default=defaults.ATMOSPHERE["altitude"],
        soft_min=0.0,
        soft_max=10000.0,
        min=0.0,
        max=100000.0,
        subtype="DISTANCE",
        update=_on_atmosphere_update,
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
