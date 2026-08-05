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

# Common shorthand → IANA ids (ZoneInfo keys are case-sensitive).
_NAME_ALIASES = {
    "eastern": "America/New_York",
    "us/eastern": "America/New_York",
    "et": "America/New_York",
    "est": "America/New_York",
    "edt": "America/New_York",
    "central": "America/Chicago",
    "us/central": "America/Chicago",
    "ct": "America/Chicago",
    "cst": "America/Chicago",
    "cdt": "America/Chicago",
    "mountain": "America/Denver",
    "us/mountain": "America/Denver",
    "mt": "America/Denver",
    "mst": "America/Denver",
    "mdt": "America/Denver",
    "pacific": "America/Los_Angeles",
    "us/pacific": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "arizona": "America/Phoenix",
    "alaska": "America/Anchorage",
    "hawaii": "Pacific/Honolulu",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "auckland": "Pacific/Auckland",
}

_TZDATA_READY = False
_ZONE_INDEX: dict[str, str] | None = None
_LAST_ZONE_ERROR = ""


def last_timezone_error() -> str:
    return _LAST_ZONE_ERROR


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

    here = Path(__file__).resolve().parent
    paths: list[Path] = [here / "_vendor"]
    wheels_dir = here / "wheels"
    if wheels_dir.is_dir():
        paths.extend(sorted(wheels_dir.glob("tzdata-*.whl")))

    for path in paths:
        if not path.exists():
            continue
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)
        try:
            import tzdata  # noqa: F401

            _TZDATA_READY = True
            return
        except ImportError:
            continue
    _TZDATA_READY = True


def _zone_index() -> dict[str, str]:
    """lowercase IANA id → canonical key."""
    global _ZONE_INDEX
    if _ZONE_INDEX is not None:
        return _ZONE_INDEX
    _ensure_tzdata()
    from zoneinfo import available_timezones

    _ZONE_INDEX = {name.lower(): name for name in available_timezones()}
    return _ZONE_INDEX


def normalize_timezone_name(name: str) -> str:
    """Normalize user input toward an IANA id."""
    key = (name or "UTC").strip().replace("\\", "/").replace(" ", "_")
    while "__" in key:
        key = key.replace("__", "_")
    lower = key.lower()
    if lower in _UTC_ALIASES:
        return "UTC"
    if lower in _NAME_ALIASES:
        return _NAME_ALIASES[lower]
    index = _zone_index()
    if lower in index:
        return index[lower]
    return key


def zoneinfo_for(name: str):
    """Resolve an IANA id; UTC aliases and missing keys fall back to timezone.utc."""
    global _LAST_ZONE_ERROR
    key = normalize_timezone_name(name)
    if key.upper() == "UTC" or key.lower() in _UTC_ALIASES:
        _LAST_ZONE_ERROR = ""
        return timezone.utc

    _ensure_tzdata()
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        tz = ZoneInfo(key)
        _LAST_ZONE_ERROR = ""
        # Rewrite Scene prop to canonical casing when we can.
        return tz
    except ZoneInfoNotFoundError:
        _LAST_ZONE_ERROR = (
            f"Unknown timezone '{(name or '').strip()}' — use IANA ids like America/Chicago"
        )
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

    try:
        local = datetime(
            int(settings.year),
            int(settings.month),
            int(settings.day),
            hour,
            minute,
            second,
            tzinfo=tz,
        )
    except Exception:
        # DST spring-forward gap / invalid civil wall time — nudge forward an hour.
        local = datetime(
            int(settings.year),
            int(settings.month),
            int(settings.day),
            min(hour + 1, 23),
            minute,
            second,
            tzinfo=tz,
        )
    return local.astimezone(timezone.utc)
