# SPDX-License-Identifier: GPL-3.0-or-later

"""Civil date/time helpers (no Blender deps beyond Scene settings duck-typing)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Fixed-offset UTC — always available (Windows Blender has no system tzdb).
_UTC_ALIASES = frozenset(
    {
        "utc",
        "uct",
        "gmt",
        "zulu",
        "universal",
        "etc/utc",
        "etc/uct",
        "etc/gmt",
        "etc/zulu",
        "etc/universal",
    }
)

_TZDATA_READY = False


def _ensure_tzdata() -> None:
    """Make bundled tzdata importable when the OS has no IANA database."""
    global _TZDATA_READY
    if _TZDATA_READY:
        return
    try:
        import tzdata  # noqa: F401

        _TZDATA_READY = True
        return
    except ImportError:
        pass

    wheels = Path(__file__).resolve().parent / "wheels"
    if wheels.is_dir():
        for wheel in sorted(wheels.glob("tzdata-*.whl")):
            path = str(wheel)
            if path not in sys.path:
                sys.path.insert(0, path)
            try:
                import tzdata  # noqa: F401

                _TZDATA_READY = True
                return
            except ImportError:
                continue
    _TZDATA_READY = True


def zoneinfo_for(name: str):
    """Resolve an IANA id; UTC aliases and missing keys fall back to timezone.utc."""
    key = (name or "UTC").strip()
    if key.lower() in _UTC_ALIASES:
        return timezone.utc

    _ensure_tzdata()
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        return ZoneInfo(key)
    except ZoneInfoNotFoundError:
        return timezone.utc


def civil_to_utc(settings) -> datetime:
    """Convert Scene civil date/time + IANA timezone to UTC."""
    hours = float(settings.time_hours) % 24.0
    hour = int(hours)
    minutes_f = (hours - hour) * 60.0
    minute = int(minutes_f)
    second = int(round((minutes_f - minute) * 60.0))
    if second >= 60:
        second = 59
    tz = zoneinfo_for(settings.timezone)
    local = datetime(
        int(settings.year),
        int(settings.month),
        int(settings.day),
        hour,
        minute,
        second,
        tzinfo=tz,
    )
    return local.astimezone(timezone.utc)
