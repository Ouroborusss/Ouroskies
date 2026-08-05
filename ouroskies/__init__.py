# SPDX-License-Identifier: GPL-3.0-or-later

"""OuroSkies — Blender Extension entry point."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from . import ops, place_date, props, ui


@persistent
def _load_post_resync(_dummy) -> None:
    from . import lamps

    lamps.resync_all_scenes()


def _deferred_resync() -> None:
    """One-shot timer — ``bpy.data`` is restricted inside ``register()``."""
    from . import lamps

    lamps.resync_all_scenes()
    return None


def register() -> None:
    props.register()
    ops.register()
    ui.register()
    place_date.register_handlers()
    if _load_post_resync not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_load_post_resync)
    # Do not touch bpy.data here — schedule after register returns.
    if not bpy.app.timers.is_registered(_deferred_resync):
        bpy.app.timers.register(_deferred_resync, first_interval=0.0)


def unregister() -> None:
    if bpy.app.timers.is_registered(_deferred_resync):
        bpy.app.timers.unregister(_deferred_resync)
    handlers = bpy.app.handlers.load_post
    while _load_post_resync in handlers:
        handlers.remove(_load_post_resync)
    place_date.unregister_handlers()
    ui.unregister()
    ops.unregister()
    props.unregister()
