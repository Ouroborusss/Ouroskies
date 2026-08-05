# SPDX-License-Identifier: GPL-3.0-or-later

"""OuroSkies — Blender Extension entry point."""

from __future__ import annotations

from . import ops, place_date, props, ui


def register() -> None:
    props.register()
    ops.register()
    ui.register()
    place_date.register_handlers()
    from . import lamps

    lamps.resync_all_scenes()


def unregister() -> None:
    place_date.unregister_handlers()
    ui.unregister()
    ops.unregister()
    props.unregister()
