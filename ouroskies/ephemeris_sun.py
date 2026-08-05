# SPDX-License-Identifier: GPL-3.0-or-later

"""NOAA / Meeus-style solar azimuth and altitude (topocentric, degrees).

Algorithms follow the NOAA Solar Position Calculator lineage (Jean Meeus,
*Astronomical Algorithms*), public-domain NOAA calculation details:
https://gml.noaa.gov/grad/solcalc/calcdetails.html
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


def _julian_day(year: int, month: int, day: float) -> float:
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


def _julian_century(jd: float) -> float:
    return (jd - 2451545.0) / 36525.0


def _mean_longitude_sun(t: float) -> float:
    return (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0


def _mean_anomaly_sun(t: float) -> float:
    return 357.52911 + t * (35999.05029 - 0.0001537 * t)


def _eccentricity_earth(t: float) -> float:
    return 0.016708634 - t * (0.000042037 + 0.0000001267 * t)


def _equation_of_center(t: float) -> float:
    m = math.radians(_mean_anomaly_sun(t))
    return (
        math.sin(m) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2 * m) * (0.019993 - 0.000101 * t)
        + math.sin(3 * m) * 0.000289
    )


def _sun_apparent_longitude(t: float) -> float:
    true_long = _mean_longitude_sun(t) + _equation_of_center(t)
    omega = 125.04 - 1934.136 * t
    return true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))


def _obliquity_correction(t: float) -> float:
    seconds = 21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))
    e0 = 23.0 + (26.0 + seconds / 60.0) / 60.0
    omega = 125.04 - 1934.136 * t
    return e0 + 0.00256 * math.cos(math.radians(omega))


def _sun_declination(t: float) -> float:
    e = math.radians(_obliquity_correction(t))
    lamb = math.radians(_sun_apparent_longitude(t))
    return math.degrees(math.asin(math.sin(e) * math.sin(lamb)))


def _equation_of_time(t: float) -> float:
    epsilon = math.radians(_obliquity_correction(t))
    l0 = math.radians(_mean_longitude_sun(t))
    e = _eccentricity_earth(t)
    m = math.radians(_mean_anomaly_sun(t))
    y = math.tan(epsilon / 2.0) ** 2
    eq = (
        y * math.sin(2 * l0)
        - 2 * e * math.sin(m)
        + 4 * e * y * math.sin(m) * math.cos(2 * l0)
        - 0.5 * y * y * math.sin(4 * l0)
        - 1.25 * e * e * math.sin(2 * m)
    )
    return math.degrees(eq) * 4.0  # minutes


def refraction_degrees(elevation_deg: float) -> float:
    """Approximate atmospheric refraction (degrees), NOAA SolCalc style."""
    if elevation_deg > 85.0:
        return 0.0
    te = math.tan(math.radians(elevation_deg))
    if elevation_deg > 5.0:
        correction = 58.1 / te - 0.07 / (te**3) + 0.000086 / (te**5)
    elif elevation_deg > -0.575:
        s1 = -12.79 + elevation_deg * 0.711
        s2 = 103.4 + elevation_deg * s1
        s3 = -518.2 + elevation_deg * s2
        correction = 1735.0 + elevation_deg * s3
    else:
        correction = -20.774 / te
    return correction / 3600.0


def sun_azimuth_elevation(
    latitude_deg: float,
    longitude_deg: float,
    when_utc: datetime,
    *,
    refraction: bool,
) -> tuple[float, float]:
    """Return (azimuth_deg east-from-north, elevation_deg from horizon)."""
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=timezone.utc)
    else:
        when_utc = when_utc.astimezone(timezone.utc)

    year = when_utc.year
    month = when_utc.month
    day = when_utc.day
    utc_hours = (
        when_utc.hour
        + when_utc.minute / 60.0
        + when_utc.second / 3600.0
        + when_utc.microsecond / 3.6e9
    )

    lat = max(min(latitude_deg, 89.93), -89.93)
    lat_rad = math.radians(lat)
    # NOAA internal longitude sign (east positive in geographic → flip for calc)
    lon = -longitude_deg

    t = _julian_century(_julian_day(year, month, day + utc_hours / 24.0))
    solar_dec = math.radians(_sun_declination(t))
    eqtime = _equation_of_time(t)

    time_correction = eqtime - 4.0 * lon
    true_solar_time = (utc_hours * 60.0 + time_correction) % 1440.0
    hour_angle = true_solar_time / 4.0 - 180.0
    if hour_angle < -180.0:
        hour_angle += 360.0

    ha = math.radians(hour_angle)
    csz = math.sin(lat_rad) * math.sin(solar_dec) + math.cos(lat_rad) * math.cos(
        solar_dec
    ) * math.cos(ha)
    csz = max(min(csz, 1.0), -1.0)
    zenith = math.acos(csz)

    az_denom = math.cos(lat_rad) * math.sin(zenith)
    if abs(az_denom) > 0.001:
        az_arg = ((math.sin(lat_rad) * math.cos(zenith)) - math.sin(solar_dec)) / az_denom
        az_arg = max(min(az_arg, 1.0), -1.0)
        azimuth = math.pi - math.acos(az_arg)
        if hour_angle > 0.0:
            azimuth = -azimuth
    else:
        azimuth = math.pi if lat_rad > 0.0 else 0.0

    if azimuth < 0.0:
        azimuth += 2.0 * math.pi

    exoatm_elevation = 90.0 - math.degrees(zenith)
    if refraction:
        elevation = exoatm_elevation + refraction_degrees(exoatm_elevation)
    else:
        elevation = exoatm_elevation

    return math.degrees(azimuth) % 360.0, elevation
