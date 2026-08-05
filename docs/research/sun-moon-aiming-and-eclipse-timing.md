# Sun / moon aiming and eclipse timing (OuroSkies)

**Question:** Which sun and moon position methods are appropriate for OuroSkies (believable arc, correct enough timing for eclipses, not observatory-grade), how do we map azimuth/altitude into Blender with **+Y = north, Z-up**, and what geometric condition defines an **eclipse look** trigger the addon can drive?

**Scope:** Plan/spec research only. Primary sun + moon from place/date; secondary sun artist-posed (out of ephemeris scope). Blender 5.2 Cycles Sky Texture Multiple Scattering for primary sun via `sun_elevation` / `sun_rotation`. Moon as custom overlay. Animatable date/time. No planets; not sub-arcsecond.

**Related (do not re-litigate):** `/home/ouro/ouroskies/docs/research/cycles-world-sky-atmosphere-options.md` — primary sun aim → Sky Texture props; one built-in sun; moon overlay; Multiple Scattering may wrap elevation/rotation for animation.

---

## Verdict

**Use a Meeus-class solar algorithm (NOAA SolCalc / Blender Sun Position lineage) plus Meeus Ch. 47 lunar position (or one JPL-backed library call for both)** — that accuracy class (~0.01° sun for daylight arcs; ~10″ geocentric lunar / better with JPL) is more than enough for believable arcs and eclipse *timing* at artistic look-trigger fidelity. **Do not** vendor NREL’s copyrighted `spa.c` into a Blender extension; SPA’s ±0.0003° is overkill and the official C redistribution is restricted. **Prefer a small pure-Python Meeus/NOAA-style module** (optionally Skyfield + DE421 later if eclipse path QA needs it) over Astropy for extension weight.

**Blender mapping (+Y north, Z-up):** set Sky Texture `sun_elevation` = altitude and drive `sun_rotation` from azimuth with an explicit signed convention validated against sunrise → +X east (see Frame mapping). Moon overlay uses the same horizontal angles → Cartesian direction.

**Eclipse look trigger (practical):** topocentric angular separation δ between Sun and Moon centers vs angular radii R☉, R☾:

| Look | Condition |
|---|---|
| Partial eclipse (disks overlap) | δ < R☉ + R☾ |
| Total (Moon covers Sun) | δ ≤ \|R☾ − R☉\| and R☾ ≥ R☉ |
| Annular (ring) | δ ≤ \|R☉ − R☾\| and R☉ > R☾ |

Drive the artistic occlusion from that predicate (and/or continuous overlap fraction); umbra/penumbra language is optional UI copy, not required geometry for the look.

---

## Solar position

### Accuracy bar for OuroSkies

Believable daytime arcs and eclipse timing at “look trigger” fidelity need roughly **arcminute-class** topocentric aim (Sun’s disk is ~32′ across; a few arcminutes of ephemeris error is invisible). Observatory / concentrator grades (±0.0003°) are out of scope.

### Algorithm families (primary sources)

| Method | Accuracy / validity | Complexity | Notes for an addon |
|---|---|---|---|
| **NOAA GML Solar Calculator** (Meeus-based low/medium formulas) | Sunrise/sunset ~1 min within ±72° lat (approx.); position formulas “very good” ~1800–2100; spreadsheets limited 1901–2099 | Low — pure trig + Julian day | Same lineage as **Blender Sun Position** addon. Good default for arcs + animation. NOAA: research/entertainment; atmospheric refraction approximations. |
| **PSA / PSA+** (Blanco-Muriel et al.) | Original: ~0.5′ for 1999–2015; PSA+: &lt;30″ envelope 2020–2050 | Very low | Sun-only; year-windowed. Fine for arcs, **not** a lunar/eclipse stack by itself. |
| **Grena 2012** (five algorithms) | Max error **0.19° → 0.0027°**, validity **2010–2110** | Low–medium | Sun-only; ENEA header freely disseminable (cite paper). Overkill at high end for OuroSkies. |
| **NREL SPA** (Reda & Andreas / Meeus high-precision procedure) | **±0.0003°**, years **−2000…6000** | High (many terms + ΔT) | Algorithm described in NREL/TP-560-34302; **official `spa.c` is noncommercial redistribution / commercial license**. Do not ship NREL C sources. Independent reimplementation of the *paper* is what pvlib-style projects do when they avoid the C license. Still overkill for OuroSkies. |

Sources:

- NOAA GML Solar Calculator & calculation details: https://gml.noaa.gov/grad/solcalc/index.html , https://gml.noaa.gov/grad/solcalc/calcdetails.html (equations from Meeus *Astronomical Algorithms*; Azimuth clockwise from north, elevation from horizon — also stated on https://gml.noaa.gov/grad/solcalc/azel.html )
- Blender Sun Position (NOAA/Meeus, public-domain NOAA data policy cited in source): https://extensions.blender.org/add-ons/sun-position/ ; implementation https://raw.githubusercontent.com/blender/blender-addons/main/sun_position/sun_calc.py
- PSA: Blanco-Muriel et al., “Computing the solar vector,” *Solar Energy* 70(5), 2001, https://doi.org/10.1016/S0038-092X(00)00156-0 ; PSA+: Blanco et al., *Solar Energy* 2021, https://doi.org/10.1016/j.solener.2020.11.048 ; updated code notes https://github.com/CST-Modelling-Tools/Updated-PSA-sun-position-algorithm
- Grena: R. Grena, “Five new algorithms…,” *Solar Energy* 86 (2012) 1323–1337, https://doi.org/10.1016/j.solener.2012.01.024 ; ENEA distribution http://www.solaritaly.enea.it/StrSunPosition/SunPositionEn.php
- NREL SPA report: Reda & Andreas, NREL/TP-560-34302 (rev. Jan 2008), https://docs.nrel.gov/docs/fy08osti/34302.pdf ; journal: *Solar Energy* 76(5) 2004; NLR SPA page (license: internal noncommercial; commercial via tech transfer): https://midcdmz.nrel.gov/spa/ (also mirrored as midcdmz.nlr.gov)

### Recommendation (sun)

**Baseline:** NOAA/Meeus-style topocentric **azimuth + elevation** (as in Blender’s Sun Position / NOAA SolCalc), UTC-based, optional refraction toggle for “look” vs geometric. **Optional upgrade path:** Grena mid-tier or a from-paper SPA reimplementation if a future ticket demands &lt;0.01° without shipping NREL C. PSA alone is acceptable for sun arcs but does not help moon/eclipses.

---

## Lunar position

### Accuracy bar

Moon disk aim and eclipse *timing* need the Moon’s topocentric direction and distance (for angular size). Meeus Ch. 47 (truncated ELP2000-82) quotes roughly **10″ in longitude and ~3–4″ in latitude**; that is ≪ the ~15–16′ lunar disk and is enough for correctly timed overlap windows at artistic fidelity. JPL DE ephemerides (via Skyfield/Astropy) are research-grade and unnecessary for the baseline unless QA against USNO/NASA eclipse catalogs is a hard requirement.

Sources:

- Jean Meeus, *Astronomical Algorithms*, 2nd ed. (Willmann-Bell, 1998), Ch. 47 (Moon), Ch. 54 (Eclipses) — bibliographic; ELP2000-82 basis: Chapront-Touzé & Chapront 1983
- Accuracy quotes echoed in primary-derived library docs, e.g. IDL `MOONPOS` (Landsman): http://astro.uni-tuebingen.de/software/idl/astrolib/astro/moonpos.html ; Starlink `sla_DMOON` notes (TT vs UT ~30″ lunar error if UT misused): https://starlink.eao.hawaii.edu/docs/sun67.htx/sun67ss49.html

### Practical pipeline

1. **Time:** compute in **TT** (or TDB≈TT) for lunar series; convert civil time → UTC → TT with ΔT (Meeus / IERS-style). Using UT as if it were TT biases the Moon by tens of arcseconds today (Starlink note above).
2. **Geocentric** apparent ecliptic/equatorial position + distance (Meeus 47).
3. **Topocentric:** parallax from observer lat/lon/elevation (Meeus Ch. 40 / standard geocentric→topocentric); then horizontal **altitude / azimuth** (same convention as Sun: az from north eastward).
4. **Angular radius:** R = arcsin(R_body / distance) or atan for small angles (JPL Horizons defines full-disk angular diameter from body radius and range — https://ssd.jpl.nasa.gov/horizons/manual.html#obsquan ).

### Recommendation (moon)

**Baseline:** pure-Python Meeus Ch. 47 + parallax + horizontal transform, same place/date stack as the Sun. **Optional:** Skyfield `earth + wgs84.latlon(...).at(t).observe(moon).apparent().altaz()` + `separation_from(sun)` for validation / “accurate mode” (MIT; needs NumPy + ephemeris `.bsp`).

Skyfield alt/az: azimuth east from geographic north — https://rhodesmill.org/skyfield/api-position.html (`altaz`).

---

## Blender frame mapping (+Y north, Z-up)

### Horizontal → Cartesian (overlays, moon, secondary aim helpers)

With **+Y = north**, **+Z = up**, right-handed (**+X = east**), and **azimuth measured eastward (clockwise on the ground) from north**, **altitude from horizon**:

```text
x = cos(alt) * sin(az)     # east
y = cos(alt) * cos(az)     # north
z = sin(alt)               # up
```

This matches Blender Sun Position’s `get_sun_vector` (after their internal φ = −az convention) for object placement:

Source: https://raw.githubusercontent.com/blender/blender-addons/main/sun_position/sun_calc.py (`get_sun_vector`, `get_sun_coordinates`; north default = +Y documented on older Sun Position manual pages and extension listing).

Skyfield documents the same geographic azimuth convention (0° N, 90° E) — https://rhodesmill.org/skyfield/api-position.html .

NOAA: “Azimuth is measured in degrees clockwise from north. Elevation is measured in degrees up from the horizon.” — https://gml.noaa.gov/grad/solcalc/azel.html

### Sky Texture `sun_elevation` / `sun_rotation`

**Manual / API**

- Manual (UI degrees): Sun Elevation = rotation from horizon; Sun Rotation = rotation around zenith.  
  https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- API stores **radians** (`sun_elevation` default `0.261799` ≈ 15°; `sun_rotation` default `0.0`).  
  https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html

**Cycles kernel (Multiple/Single Scattering path)** builds the sun direction as:

```text
sun_dir = spherical_to_direction(sun_elevation − π/2, sun_rotation − π/2)
```

with

```text
spherical_to_direction(θ, φ) = (sin θ · cos φ, sin θ · sin φ, cos θ)
```

Sources:

- https://raw.githubusercontent.com/blender/cycles/main/src/kernel/svm/sky.h (`sky_radiance_nishita`)
- https://raw.githubusercontent.com/blender/cycles/main/src/util/projection.h (`spherical_to_direction`)

Evaluating that mapping:

| Inputs | `sun_dir` | Scene meaning |
|---|---|---|
| elevation = 0, rotation = 0 | (0, 1, 0) | Horizon, **+Y (north)** |
| elevation = π/2 | (0, 0, 1) | Zenith, **+Z** |
| elevation = 0, rotation = +π/2 | (−1, 0, 0) | Horizon, **−X (west)** if +X is east |

So **`sun_elevation` = altitude** is correct for +Y-north / Z-up.

**`sun_rotation` vs navigational azimuth:** increasing `sun_rotation` moves the sun from +Y toward **−X** (west), i.e. the **opposite sense** of standard azimuth (clockwise from north toward east/+X). Therefore for standard az:

```text
sun_elevation = alt                    # radians in RNA
sun_rotation  = -az                    # or equivalently (2π − az) mod 2π
```

**Caveat — Blender Sun Position today sets both:**

```python
sky_node.sun_elevation = elevation
sky_node.sun_rotation = azimuth   # same signed az used for get_sun_vector
```

Source: `move_sun` in https://raw.githubusercontent.com/blender/blender-addons/main/sun_position/sun_calc.py

That matches elevation; the rotation sign may disagree with the Cycles SVM derivation above for “east = +X.” **OuroSkies should adopt the derivation (`sun_rotation = −az`) and verify with a known eastern sunrise** (morning Sun disk → +X). Do not assume Sun Position’s Nishita rotation sign without that check. Preetham/Hosek `sun_direction` vector from `get_sun_vector` already uses the east=+X Cartesian formula and is a good cross-check for overlays.

### Drivers / wrapping

Prior atmosphere research: Multiple Scattering animation may wrap elevation/rotation — drivers should use continuous unwrapped angles or shortest-path updates when keyframing timelapses (see `cycles-world-sky-atmosphere-options.md`).

`sun_size` default ≈ `0.009512` rad ≈ **0.545°** full angular diameter — in the real solar range (~0.53°); can be driven from ephemeris angular diameter for eclipse sizing. API: https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html

---

## Eclipse look trigger

### Physical picture (NASA)

A solar eclipse occurs when the Moon lies between Sun and observer and casts a shadow: **umbra** (Sun fully blocked), **penumbra** (partial), **antumbra** (annular ring when Moon’s apparent size is smaller). Solar eclipses only occur near new moon; orbital inclination keeps most new moons from lining up.

Source: https://science.nasa.gov/eclipses/geometry/

### Addon-scale geometry (topocentric disks)

For a **look** trigger (custom moon disk + Sky Texture sun disc / overlay), use **angular disk intersection** at the observer — not Besselian elements / shadow cones on Earth’s surface (those are for path-of-totality maps; USNO local circumstances API is a validation oracle, not runtime):

https://aa.usno.navy.mil/data/api (Solar Eclipse Calculator)

Let:

- δ = topocentric angular separation of Sun and Moon centers (great-circle / `acos` of unit-direction dot product, or Skyfield `separation_from`)
- R☉, R☾ = topocentric **angular radii** (half of Horizons-style angular diameter)

Then:

1. **No eclipse look:** δ ≥ R☉ + R☾ (disks disjoint).
2. **Partial:** δ < R☉ + R☾ and δ > \|R☉ − R☾\| (lenses overlap).
3. **Total (Moon larger):** δ ≤ R☾ − R☉ with R☾ ≥ R☉.
4. **Annular (Sun larger):** δ ≤ R☉ − R☾ with R☉ > R☾.

Optional continuous factor for shaders: approximate obscuration from circular-segment intersection area of two disks of radii R☉, R☾ separated by δ (standard geometry); or a cheaper smoothstep on (R☉ + R☾ − δ). Artistic faking of corona / exposure can sit on top of this predicate (in scope per wayfinder: look may be faked).

**Umbra vs penumbra at this fidelity:** treat “partial” ≈ penumbral disk overlap and “total/annular” ≈ umbral/antumbral *as seen on the solar disk*. That is enough to drive World overlays without modeling Earth’s shadow cones.

**Lunar eclipses** (Earth’s shadow on the Moon) are a different geometry (Meeus Ch. 54 / NASA lunar eclipse pages) and are out of the solar-eclipse look trigger above unless a later ticket adds them.

### Timing correctness

With Meeus-class Sun + Moon + topocentric reduction, contact times are correct to well under a minute for cinematic use; remaining error is dominated by ΔT, refraction near horizon, and (if omitted) light-time — all acceptable for non-observatory OuroSkies.

---

## Timezone / UTC for animatable timelines

1. **Canonical instant = UTC** (or UT1≈UTC for this accuracy). Store animation as UTC seconds / Julian Date, or as timezone-aware datetimes converted through UTC every evaluation.
2. **Civil UI:** IANA zone ids via Python `zoneinfo` (stdlib 3.9+; PEP 615) + optional `tzdata` wheel on platforms without system tzdb — https://docs.python.org/3/library/zoneinfo.html
3. **Do not** animate across DST with naive local + fixed offset: spring-forward gaps and fall-back folds break linear timelines. Prefer **UTC scrubbing** with local labels derived per frame, or fixed **UTC offset** mode for “timelapse without politics.”
4. **Fixed offset vs named zone:** named zones for “real place today”; fixed offset for historical/fictional control and reproducible files.
5. **ΔT:** apply when feeding lunar (and high-end solar) series that expect TT; NOAA low-precision sun formulas often take UT directly (SolCalc / Sun Position style). Document which path the addon uses.
6. NOAA itself warns that auto time zones / DST boundaries can be wrong for historical/future dates — https://gml.noaa.gov/grad/solcalc/index.html

---

## Library vs pure Python (Blender extension tradeoffs)

| Option | Pros | Cons | Fit |
|---|---|---|---|
| **Pure Python Meeus/NOAA-style** (sun + moon + δ + radii) | Tiny; no NumPy/ephemeris download; GPL-friendly self-contained; matches Sun Position mental model | Must implement/test yourself; lunar ~10″ class; ΔT table maintenance | **Recommended baseline** |
| **Skyfield** (MIT) + DE421/DE440s `.bsp` | Excellent altaz + `separation_from`; USNO-class agreement claimed (~0.00001″ vs Almanac on site); pure Python + NumPy | NumPy + jplephem + **~17+ MB ephemeris** download/cache; heavier extension | Optional “accurate / QA” mode |
| **Astropy** `get_body` / builtin or JPL | High quality; familiar in science | Large dependency graph; overkill for addon packaging | Prefer avoid for shipped extension |
| **Vendor NREL `spa.c`** | Extreme solar accuracy | **License blocks redistribution**; sun-only | **Do not** |
| **PyMeeus / similar** | Meeus already coded | Extra dependency; audit license & tests | Acceptable middle ground if maintained |

Skyfield: https://rhodesmill.org/skyfield/ ; PyPI license MIT https://pypi.org/project/skyfield/  
Astropy solar-system: https://docs.astropy.org/en/stable/coordinates/solarsystem.html (builtin ERFA vs JPL DE*)

**Verdict:** ship a **small pure-Python ephemeris module** for sun + moon aim + eclipse predicate; optionally detect/use Skyfield if the user installs it. Do not make Astropy or NREL SPA C a hard dependency.

---

## Open questions / caveats

1. **Confirm `sun_rotation` sign** against Cycles 5.2 sunrise → +X (see Frame mapping). Record the chosen formula in the addon spec once verified.
2. **Refraction:** NOAA/Sun Position optional refraction lifts apparent altitude near the horizon; geometric (unrefracted) positions are better for eclipse disk math; apparent may look nicer at sunrise/set. Spec should expose a toggle.
3. **ΔT source** for far future/past timelapses (polynomial vs IERS finals) — pick one and document error growth.
4. **Observer elevation** affects topocentric Moon strongly (parallax); wire optional elevation into the lunar path (Sun parallax is tiny).
5. **Sky Texture `sun_size` vs ephemeris diameter** during annular vs total — drive or leave artistic.
6. **Wrapping** of `sun_elevation` / `sun_rotation` under Multiple Scattering when animating long timelapses (prior research).
7. **Lunar eclipse / Earthshine** not covered by the solar disk-overlap trigger.
8. NOAA SolCalc pages note the service is **no longer actively maintained** — treat as algorithm reference, not a live dependency: https://gml.noaa.gov/grad/solcalc/index.html

---

## Sources (index)

- Meeus, J. *Astronomical Algorithms*, 2nd ed., Willmann-Bell, 1998 (Ch. 47 Moon; Ch. 54 Eclipses; solar chapters underlying NOAA/SPA).
- Reda, I. & Andreas, A. *Solar Position Algorithm for Solar Radiation Applications*, NREL/TP-560-34302, rev. 2008. https://docs.nrel.gov/docs/fy08osti/34302.pdf
- Blanco-Muriel et al., *Solar Energy* 70(5) 2001 (PSA). https://doi.org/10.1016/S0038-092X(00)00156-0
- Grena, R., *Solar Energy* 86 (2012) 1323–1337. https://doi.org/10.1016/j.solener.2012.01.024
- NOAA GML Solar Calculator. https://gml.noaa.gov/grad/solcalc/
- NASA eclipse geometry. https://science.nasa.gov/eclipses/geometry/
- USNO eclipse API. https://aa.usno.navy.mil/data/api
- JPL Horizons quantities (angular diameter). https://ssd.jpl.nasa.gov/horizons/manual.html#obsquan
- Blender 5.2 Sky Texture manual & API. https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html ; https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html
- Cycles `sky.h` / `projection.h`. https://github.com/blender/cycles (paths cited above)
- Blender Sun Position addon. https://extensions.blender.org/add-ons/sun-position/ ; `sun_calc.py` on blender-addons
- Skyfield docs / PyPI. https://rhodesmill.org/skyfield/ ; https://pypi.org/project/skyfield/
- Astropy solar system ephemerides. https://docs.astropy.org/en/stable/coordinates/solarsystem.html
- Python `zoneinfo`. https://docs.python.org/3/library/zoneinfo.html
