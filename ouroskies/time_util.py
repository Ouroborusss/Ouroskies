# SPDX-License-Identifier: GPL-3.0-or-later

"""Civil date/time helpers (no Blender deps beyond Scene settings duck-typing)."""

from __future__ import annotations

from datetime import datetime, timezone


def zoneinfo_for(name: str):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


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
