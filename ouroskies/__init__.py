# SPDX-License-Identifier: GPL-3.0-or-later

"""OuroSkies — Blender Extension entry point.

Package layout stays flat until feature tickets introduce modules
(props, ui, world, aim, lamps). Prefer relative imports and ``__package__``
for preferences / user data paths when those land.
"""

from __future__ import annotations


def register() -> None:
    """Register operators, properties, and UI (filled by later tickets)."""


def unregister() -> None:
    """Unregister everything registered by :func:`register`."""
