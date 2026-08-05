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
        layout.label(text="Secondary sun, moon disk, Sun Punch — later", icon="INFO")


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
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = _settings(context)

        layout.label(text="Place")
        layout.prop(settings, "latitude")
        layout.prop(settings, "longitude")
        layout.prop(settings, "altitude")
        layout.prop(settings, "timezone")

        layout.separator()
        layout.operator("ouroskies.rebuild_sky_graph", text="Rebuild Sky Graph")
        layout.separator()
        layout.label(text="Lamps — later", icon="INFO")


CLASSES = (
    OUROSKIES_PT_now,
    OUROSKIES_PT_looks,
    OUROSKIES_PT_celestials,
    OUROSKIES_PT_eclipse,
    OUROSKIES_PT_setup,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
