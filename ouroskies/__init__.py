# SPDX-License-Identifier: GPL-3.0-or-later

"""OuroSkies — Blender Extension entry point."""

from __future__ import annotations

from . import ops, props, ui


def register() -> None:
    props.register()
    ops.register()
    ui.register()


def unregister() -> None:
    ui.unregister()
    ops.unregister()
    props.unregister()
