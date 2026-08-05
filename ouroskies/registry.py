# SPDX-License-Identifier: GPL-3.0-or-later

"""Idempotent bpy class register helpers (safe for reload / re-enable)."""

from __future__ import annotations

import bpy


def register_classes(classes) -> None:
    for cls in classes:
        existing = getattr(bpy.types, cls.__name__, None)
        if existing is not None:
            try:
                bpy.utils.unregister_class(existing)
            except RuntimeError:
                pass
        bpy.utils.register_class(cls)


def unregister_classes(classes) -> None:
    for cls in reversed(tuple(classes)):
        existing = getattr(bpy.types, cls.__name__, None)
        if existing is None:
            continue
        try:
            bpy.utils.unregister_class(existing)
        except RuntimeError:
            pass
