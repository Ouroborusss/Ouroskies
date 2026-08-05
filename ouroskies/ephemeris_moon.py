# SPDX-License-Identifier: GPL-3.0-or-later

"""Truncated Meeus lunar azimuth / altitude (topocentric, degrees).

Baseline for OuroSkies moon aim — Jean Meeus, *Astronomical Algorithms*
Ch. 47 (abbreviated series) + horizontal conversion. Good enough for disk
aim and eclipse timing at artistic fidelity; not observatory-grade.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

# Mean Earth radius / equatorial (km) and mean lunar radius (km).
_EARTH_RADIUS_KM = 6378.14
_MOON_RADIUS_KM = 1737.4


def _julian_day(when_utc: datetime) -> float:
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=timezone.utc)
    else:
        when_utc = when_utc.astimezone(timezone.utc)
    y, m = when_utc.year, when_utc.month
    day = (
        when_utc.day
        + (
            when_utc.hour
            + when_utc.minute / 60.0
            + when_utc.second / 3600.0
            + when_utc.microsecond / 3.6e9
        )
        / 24.0
    )
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    return (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (m + 1))
        + day
        + b
        - 1524.5
    )


def _delta_t_seconds(year: float) -> float:
    """Rough ΔT (TT − UT) in seconds — provisional polynomial."""
    # provisional: Espenak/Meeus-ish fit; fine for artistic moon aim.
    t = (year - 2000.0) / 100.0
    return 64.09 + 61.0 * t + 58.5 * t * t


def moon_azimuth_elevation(
    latitude_deg: float,
    longitude_deg: float,
    when_utc: datetime,
    observer_elevation_m: float = 0.0,
    *,
    refraction: bool,
) -> tuple[float, float, float]:
    """Return (azimuth_deg, elevation_deg, distance_km).

    Azimuth east from north. Elevation geometric or apparent per ``refraction``.
    """
    jd_ut = _julian_day(when_utc)
    year = when_utc.year + (when_utc.timetuple().tm_yday - 1) / 365.25
    jd_tt = jd_ut + _delta_t_seconds(year) / 86400.0
    t = (jd_tt - 2451545.0) / 36525.0

    # Mean arguments (degrees) — Meeus Ch. 47.
    lp = (218.3164477 + 481267.88123421 * t) % 360.0
    d = (297.8501921 + 445267.1114034 * t) % 360.0
    m = (357.5291092 + 35999.0502909 * t) % 360.0
    mp = (134.9633964 + 477198.8675055 * t) % 360.0
    f = (93.2720950 + 483202.0175233 * t) % 360.0

    def r(*angles_deg: float) -> list[float]:
        return [math.radians(a) for a in angles_deg]

    d_r, m_r, mp_r, f_r = r(d, m, mp, f)

    # Longitude periodic terms (abbreviated).
    sum_l = (
        6.288774 * math.sin(mp_r)
        + 1.274027 * math.sin(2 * d_r - mp_r)
        + 0.658314 * math.sin(2 * d_r)
        + 0.213618 * math.sin(2 * mp_r)
        - 0.185116 * math.sin(m_r)
        - 0.114332 * math.sin(2 * f_r)
        + 0.058793 * math.sin(2 * d_r - 2 * mp_r)
        + 0.057066 * math.sin(2 * d_r - m_r - mp_r)
        + 0.053322 * math.sin(2 * d_r + mp_r)
        + 0.045758 * math.sin(2 * d_r - m_r)
    )
    sum_b = (
        5.128122 * math.sin(f_r)
        + 0.280602 * math.sin(mp_r + f_r)
        + 0.277693 * math.sin(mp_r - f_r)
        + 0.173238 * math.sin(2 * d_r - f_r)
        + 0.055413 * math.sin(2 * d_r + f_r - mp_r)
        + 0.046272 * math.sin(2 * d_r - f_r - mp_r)
        + 0.032573 * math.sin(2 * d_r + f_r)
        + 0.017198 * math.sin(2 * mp_r + f_r)
    )
    sum_r = (
        -20905.355 * math.cos(mp_r)
        - 3699.111 * math.cos(2 * d_r - mp_r)
        - 2955.968 * math.cos(2 * d_r)
        - 569.925 * math.cos(2 * mp_r)
        + 48.888 * math.cos(m_r)
        - 3.149 * math.cos(2 * f_r)
        + 246.158 * math.cos(2 * d_r - 2 * mp_r)
        + 152.138 * math.cos(2 * d_r - m_r - mp_r)
        - 170.733 * math.cos(2 * d_r + mp_r)
        - 204.586 * math.cos(2 * d_r - m_r)
    )

    lon = math.radians((lp + sum_l) % 360.0)
    lat = math.radians(sum_b)
    distance = 385000.56 + sum_r  # km

    # Ecliptic obliquity (rough).
    eps = math.radians(23.439291 - 0.0130042 * t)
    # Equatorial.
    ra = math.atan2(
        math.sin(lon) * math.cos(eps) - math.tan(lat) * math.sin(eps),
        math.cos(lon),
    )
    dec = math.asin(
        math.sin(lat) * math.cos(eps) + math.cos(lat) * math.sin(eps) * math.sin(lon)
    )

    # Local sidereal (approx from UT).
    gmst = (
        280.46061837
        + 360.98564736629 * (jd_ut - 2451545.0)
        + 0.000387933 * t * t
    ) % 360.0
    lst = math.radians((gmst + longitude_deg) % 360.0)
    ha = lst - ra

    # Geocentric horizontal.
    lat_r = math.radians(latitude_deg)
    sin_alt = math.sin(lat_r) * math.sin(dec) + math.cos(lat_r) * math.cos(dec) * math.cos(
        ha
    )
    sin_alt = max(min(sin_alt, 1.0), -1.0)
    alt = math.asin(sin_alt)
    az = math.atan2(
        -math.sin(ha),
        math.tan(dec) * math.cos(lat_r) - math.sin(lat_r) * math.cos(ha),
    )
    az = (math.degrees(az) + 360.0) % 360.0
    elev = math.degrees(alt)

    # Topocentric parallax (horizontal parallax).
    hp = math.asin(_EARTH_RADIUS_KM / max(distance, _EARTH_RADIUS_KM + 1.0))
    elev -= math.degrees(hp) * math.cos(math.radians(elev))

    if refraction:
        from .ephemeris_sun import refraction_degrees

        elev += refraction_degrees(elev)

    return az, elev, distance


def moon_angular_radius_deg(distance_km: float) -> float:
    return math.degrees(math.asin(_MOON_RADIUS_KM / distance_km))
