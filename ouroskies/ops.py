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
    """Apply Physically Accurate brightness targets and Daylight WB."""

    bl_idname = "ouroskies.physically_accurate"
    bl_label = "Physically Accurate"
    bl_description = (
        "Set Sky Strength, World Contribution, and White Balance to provisional "
        "physical targets; does not change Exposure or atmosphere"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import looks

        looks.physically_accurate(context.scene)
        self.report({"INFO"}, "Physically Accurate looks applied")
        return {"FINISHED"}


class OUROSKIES_OT_wb_preset(Operator):
    """Apply a White Balance Kelvin preset."""

    bl_idname = "ouroskies.wb_preset"
    bl_label = "WB Preset"
    bl_description = "Set White Balance Kelvin from a named preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.StringProperty(default="DAYLIGHT")

    def execute(self, context):
        from . import looks

        looks.set_wb_preset(context.scene, self.preset)
        self.report({"INFO"}, f"White Balance preset {self.preset.title()}")
        return {"FINISHED"}


class OUROSKIES_OT_add_sun_lamp(Operator):
    bl_idname = "ouroskies.add_sun_lamp"
    bl_label = "Add Sun Lamp"
    bl_description = "Create an OuroSkies-owned Sun lamp synced to primary sun aim"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import lamps

        try:
            obj = lamps.add_lamp(context.scene, lamps.LAMP_KIND_SUN)
        except Exception as exc:
            self.report({"ERROR"}, f"Add Sun Lamp failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Added {obj.name}")
        return {"FINISHED"}


class OUROSKIES_OT_remove_sun_lamp(Operator):
    bl_idname = "ouroskies.remove_sun_lamp"
    bl_label = "Remove Sun Lamp"
    bl_description = "Remove the OuroSkies-owned Sun lamp only"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import lamps

        if lamps.remove_lamp(context.scene, lamps.LAMP_KIND_SUN):
            self.report({"INFO"}, "Removed OuroSkies Sun Lamp")
        else:
            self.report({"WARNING"}, "No OuroSkies Sun Lamp to remove")
            return {"CANCELLED"}
        return {"FINISHED"}


class OUROSKIES_OT_add_moon_lamp(Operator):
    bl_idname = "ouroskies.add_moon_lamp"
    bl_label = "Add Moon Lamp"
    bl_description = "Create an OuroSkies-owned Moon lamp synced to moon aim"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import lamps

        try:
            obj = lamps.add_lamp(context.scene, lamps.LAMP_KIND_MOON)
        except Exception as exc:
            self.report({"ERROR"}, f"Add Moon Lamp failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Added {obj.name}")
        return {"FINISHED"}


class OUROSKIES_OT_remove_moon_lamp(Operator):
    bl_idname = "ouroskies.remove_moon_lamp"
    bl_label = "Remove Moon Lamp"
    bl_description = "Remove the OuroSkies-owned Moon lamp only"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import lamps

        if lamps.remove_lamp(context.scene, lamps.LAMP_KIND_MOON):
            self.report({"INFO"}, "Removed OuroSkies Moon Lamp")
        else:
            self.report({"WARNING"}, "No OuroSkies Moon Lamp to remove")
            return {"CANCELLED"}
        return {"FINISHED"}


CLASSES = (
    OUROSKIES_OT_enable,
    OUROSKIES_OT_detach,
    OUROSKIES_OT_rebuild_sky_graph,
    OUROSKIES_OT_reset_atmosphere,
    OUROSKIES_OT_reset_sun_position,
    OUROSKIES_OT_physically_accurate,
    OUROSKIES_OT_wb_preset,
    OUROSKIES_OT_add_sun_lamp,
    OUROSKIES_OT_remove_sun_lamp,
    OUROSKIES_OT_add_moon_lamp,
    OUROSKIES_OT_remove_moon_lamp,
)


def register() -> None:
    from .registry import register_classes

    register_classes(CLASSES)


def unregister() -> None:
    from .registry import unregister_classes

    unregister_classes(CLASSES)
