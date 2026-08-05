# SPDX-License-Identifier: GPL-3.0-or-later

"""Cockpit operators — Enable / Detach / Rebuild / Reset Atmosphere."""

from __future__ import annotations

import bpy
from bpy.types import Operator

from . import world


class OUROSKIES_OT_enable(Operator):
    """Enable OuroSkies: dedicated World + Multiple Scattering sky graph."""

    bl_idname = "ouroskies.enable"
    bl_label = "Enable"
    bl_description = "Create the OuroSkies World and switch this scene to it"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        owned = world.enable(context.scene)
        self.report({"INFO"}, f"OuroSkies enabled ({owned.name})")
        return {"FINISHED"}


class OUROSKIES_OT_detach(Operator):
    """Detach OuroSkies and restore the previous World."""

    bl_idname = "ouroskies.detach"
    bl_label = "Detach"
    bl_description = "Restore the previous World and delete the OuroSkies World"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.ouroskies
        if not settings.is_enabled and world.find_ouroskies_world(context.scene) is None:
            self.report({"WARNING"}, "OuroSkies is not enabled")
            return {"CANCELLED"}
        world.detach(context.scene)
        self.report({"INFO"}, "OuroSkies detached")
        return {"FINISHED"}


class OUROSKIES_OT_rebuild_sky_graph(Operator):
    """Restore the canonical OuroSkies World node layout from Scene settings."""

    bl_idname = "ouroskies.rebuild_sky_graph"
    bl_label = "Rebuild Sky Graph"
    bl_description = "Rebuild the OuroSkies World nodes from current settings (hand edits unsupported)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not world.rebuild(context.scene):
            self.report({"WARNING"}, "Enable OuroSkies before rebuilding the sky graph")
            return {"CANCELLED"}
        self.report({"INFO"}, "OuroSkies sky graph rebuilt")
        return {"FINISHED"}


class OUROSKIES_OT_reset_atmosphere(Operator):
    """Restore provisional Air / Dust / Ozone / Altitude defaults."""

    bl_idname = "ouroskies.reset_atmosphere"
    bl_label = "Reset Atmosphere"
    bl_description = "Restore provisional atmosphere defaults and sync the Sky Texture"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        world.reset_atmosphere(context.scene)
        self.report({"INFO"}, "Atmosphere reset to provisional defaults")
        return {"FINISHED"}


class OUROSKIES_OT_reset_sun_position(Operator):
    """Restore provisional Manual sun elevation and azimuth."""

    bl_idname = "ouroskies.reset_sun_position"
    bl_label = "Reset Sun Position"
    bl_description = "Restore default Manual sun elevation and azimuth (15° / 90° east)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import aim

        aim.reset_manual_sun(context.scene)
        self.report({"INFO"}, "Manual sun position reset to provisional defaults")
        return {"FINISHED"}


class OUROSKIES_OT_physically_accurate(Operator):
    """Apply Physically Accurate brightness targets (filled by Looks ticket)."""

    bl_idname = "ouroskies.physically_accurate"
    bl_label = "Physically Accurate"
    bl_description = "Reset brightness toward real-world targets (not implemented yet)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.report(
            {"INFO"},
            "Physically Accurate is a stub — Looks presets come later",
        )
        return {"FINISHED"}


CLASSES = (
    OUROSKIES_OT_enable,
    OUROSKIES_OT_detach,
    OUROSKIES_OT_rebuild_sky_graph,
    OUROSKIES_OT_reset_atmosphere,
    OUROSKIES_OT_reset_sun_position,
    OUROSKIES_OT_physically_accurate,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
