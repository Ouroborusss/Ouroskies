# SPDX-License-Identifier: GPL-3.0-or-later

"""Idempotent bpy class register helpers (safe for reload / re-enable)."""

from __future__ import annotations

import bpy


def register_classes(classes) -> None:
    for cls in classes:
        # PropertyGroups are not exposed on bpy.types by class name; use is_registered.
        if getattr(cls, "is_registered", False):
            try:
                bpy.utils.unregister_class(cls)
            except (RuntimeError, ValueError):
                pass
        else:
            existing = getattr(bpy.types, cls.__name__, None)
            if existing is not None:
                try:
                    bpy.utils.unregister_class(existing)
                except (RuntimeError, ValueError):
                    pass
        bpy.utils.register_class(cls)


def unregister_classes(classes) -> None:
    for cls in reversed(tuple(classes)):
        if not getattr(cls, "is_registered", False):
            existing = getattr(bpy.types, cls.__name__, None)
            if existing is None:
                continue
            cls = existing
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
