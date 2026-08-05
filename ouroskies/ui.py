# SPDX-License-Identifier: GPL-3.0-or-later

"""N-panel cockpit — Variant C: Sticky Now + Looks / Celestials / Eclipse / Setup."""

from __future__ import annotations

import bpy
from bpy.types import Panel


def _settings(context):
    return context.scene.ouroskies


class OUROSKIES_PT_now(Panel):
    """Sticky Now chrome — always the top panel in the OuroSkies category."""

    bl_label = "OuroSkies"
    bl_idname = "OUROSKIES_PT_now"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OuroSkies"
    bl_order = 0

    def draw_header(self, context):
        layout = self.layout
        settings = _settings(context)
        layout.label(text="On" if settings.is_enabled else "Off")

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)

        status = layout.row(align=True)
        status.label(
            text=settings.aim_mode.replace("_", "/").title(),
            icon="ORIENTATION_GIMBAL",
        )
        status.label(text=settings.status_place, icon="WORLD")
        status.label(text=settings.status_when, icon="TIME")

        layout.prop(settings, "aim_mode", text="Aim")
        layout.prop(settings, "aim_refraction", text="Refraction")
        if settings.aim_mode == "PLACE_DATE" and settings.refraction_diverges:
            layout.label(
                text="Apparent ≠ Geometric near horizon",
                icon="INFO",
            )

        if settings.aim_mode == "PLACE_DATE":
            row = layout.row(align=True)
            row.prop(settings, "year", text="")
            row.prop(settings, "month", text="")
            row.prop(settings, "day", text="")
            layout.prop(settings, "time_hours", text="Time (h)")

        row = layout.row(align=True)
        row.operator("ouroskies.physically_accurate", text="Physically Accurate")
        row = layout.row(align=True)
        row.operator("ouroskies.enable", text="Enable")
        row.operator("ouroskies.detach", text="Detach")


class OUROSKIES_PT_looks(Panel):
    bl_label = "Looks"
    bl_idname = "OUROSKIES_PT_looks"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OuroSkies"
    bl_order = 1
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)

        layout.label(text="Atmosphere")
        layout.prop(settings, "air")
        layout.prop(settings, "dust")
        layout.prop(settings, "ozone")
        layout.prop(settings, "altitude")
        layout.operator("ouroskies.reset_atmosphere", text="Reset Atmosphere")

        layout.separator()
        layout.label(text="Brightness")
        layout.prop(settings, "sky_strength")
        layout.prop(settings, "world_contribution")
        layout.prop(settings, "exposure")

        layout.separator()
        layout.label(text="White Balance")
        layout.prop(settings, "white_balance_kelvin", text="Kelvin")
        row = layout.row(align=True)
        row.operator("ouroskies.wb_preset", text="Daylight").preset = "DAYLIGHT"
        row.operator("ouroskies.wb_preset", text="Cloudy").preset = "CLOUDY"
        row = layout.row(align=True)
        row.operator("ouroskies.wb_preset", text="Shade").preset = "SHADE"
        row.operator("ouroskies.wb_preset", text="Warm").preset = "WARM"

        layout.separator()
        layout.label(text="Airglow")
        layout.prop(settings, "airglow_strength", text="Strength")
        layout.prop(settings, "airglow_tint", text="Tint")

        layout.separator()
        layout.label(text="Stars — later", icon="INFO")


class OUROSKIES_PT_celestials(Panel):
    bl_label = "Celestials"
    bl_idname = "OUROSKIES_PT_celestials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OuroSkies"
    bl_order = 2
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)

        layout.label(text="Primary sun (Manual aim)")
        col = layout.column(align=True)
        col.enabled = settings.aim_mode == "MANUAL"
        col.prop(settings, "sun_elevation_deg", text="Elevation")
        col.prop(settings, "sun_azimuth_deg", text="Azimuth")
        row = layout.row()
        row.enabled = settings.aim_mode == "MANUAL"
        row.operator("ouroskies.reset_sun_position", text="Reset Sun Position")
        if settings.aim_mode == "PLACE_DATE":
            layout.label(
                text=(
                    f"Place/Date sun  elev {settings.evaluated_sun_elevation_deg:.1f}°"
                    f"  az {settings.evaluated_sun_azimuth_deg:.1f}°"
                ),
                icon="INFO",
            )

        layout.separator()
        layout.label(text="Moon")
        layout.prop(settings, "moon_size_deg", text="Size")
        layout.label(
            text=(
                f"Moon elev {settings.moon_elevation_deg:.1f}°"
                f"  az {settings.moon_azimuth_deg:.1f}°"
            ),
            icon="INFO",
        )
        if settings.aim_mode == "MANUAL":
            layout.label(
                text="Manual: moon tracks opposite the sun",
                icon="INFO",
            )
        else:
            layout.label(
                text="Place/Date: real moon path (may be down at night)",
                icon="INFO",
            )

        layout.separator()
        layout.label(text="Secondary sun, Sun Punch — later", icon="INFO")


class OUROSKIES_PT_eclipse(Panel):
    bl_label = "Eclipse"
    bl_idname = "OUROSKIES_PT_eclipse"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OuroSkies"
    bl_order = 3
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Effects and artistic overlays — stub")
        layout.label(text="Controls land with later tickets", icon="INFO")


class OUROSKIES_PT_setup(Panel):
    bl_label = "Setup"
    bl_idname = "OUROSKIES_PT_setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OuroSkies"
    bl_order = 4

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)

        layout.label(text="Place")
        layout.prop(settings, "latitude")
        layout.prop(settings, "longitude")
        layout.prop(settings, "altitude")
        layout.prop(settings, "timezone")

        layout.separator()
        layout.label(text="Lamps")
        from . import lamps as lamps_mod

        sun_obj = lamps_mod.find_lamp_object(context.scene, lamps_mod.LAMP_KIND_SUN)
        moon_obj = lamps_mod.find_lamp_object(context.scene, lamps_mod.LAMP_KIND_MOON)

        row = layout.row(align=True)
        row.operator("ouroskies.add_sun_lamp", text="Add Sun Lamp")
        row.operator("ouroskies.remove_sun_lamp", text="Remove")
        if sun_obj is not None:
            layout.prop(settings, "sun_lamp_energy", text="Sun Strength")
            layout.label(text="Strength fades below the horizon", icon="INFO")
        row = layout.row(align=True)
        row.operator("ouroskies.add_moon_lamp", text="Add Moon Lamp")
        row.operator("ouroskies.remove_moon_lamp", text="Remove")
        if moon_obj is not None:
            layout.prop(settings, "moon_lamp_energy", text="Moon Strength")
            elev = settings.moon_elevation_deg
            if elev >= 0.0:
                note = (
                    f"Moon elev {elev:.1f}°  az {settings.moon_azimuth_deg:.1f}°"
                )
            else:
                note = f"Moon below horizon ({elev:.1f}°) — strength faded"
            layout.label(text=note, icon="INFO")

        layout.separator()
        layout.operator("ouroskies.rebuild_sky_graph", text="Rebuild Sky Graph")

        layout.separator()
        box = layout.box()
        box.label(text="EEVEE notes", icon="INFO")
        box.label(text="Sky Texture Sun Disc is Cycles-only")
        box.label(text="Use Add Sun Lamp for EEVEE daylight")
        box.label(text="No Cycles/EEVEE lighting parity claims")


CLASSES = (
    OUROSKIES_PT_now,
    OUROSKIES_PT_looks,
    OUROSKIES_PT_celestials,
    OUROSKIES_PT_eclipse,
    OUROSKIES_PT_setup,
)


def register() -> None:
    from .registry import register_classes

    register_classes(CLASSES)


def unregister() -> None:
    from .registry import unregister_classes

    unregister_classes(CLASSES)
