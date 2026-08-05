# OuroSkies — build-ready specification

**Status:** Build-ready handoff for a later implementation effort.  
**Product:** OuroSkies — Blender 5.2 Extension  
**Maintainer:** Ouroborusss \<https://github.com/Ouroborusss\>  
**Map:** `.scratch/ouroskies-spec/map.md`  
**Glossary:** [`CONTEXT.md`](../CONTEXT.md)

This document is the destination artifact of the wayfinder planning map. It locks decisions so implementation can start cold. It does **not** ship the addon. Open numeric defaults and deferred fog are listed in §13.

---

## 1. Purpose & destination

OuroSkies produces a **Nishita-class World sky** (atmosphere, primary sun, secondary sun, moon disk, procedural stars) with place/date aiming (+Y = north), optional synced sun/moon lamps, animatable time for timelapses, and timed eclipse looks.

**Build-ready** means: scope, architecture, cockpit IA, and packaging are decided; remaining items are explicit fill-later slots (§13), not unresolved product forks.

**Plan-only boundary:** This effort does not implement or ship the Extension. Implementation is a separate later effort.

---

## 2. Glossary

Use [`CONTEXT.md`](../CONTEXT.md) as the ubiquitous language. Spec text prefers those terms (World sky, OuroSkies World, Aim mode, Aim refraction, Dust, Physically Accurate preset, World contribution, etc.).

---

## 3. Product scope

### In scope

- Multiple Scattering Sky Texture atmosphere (Air / Dust / Ozone / Altitude)
- Primary sun + secondary (artist-posed) sun; moon disk; procedural stars + togglable Milky band
- Place/date aiming and Manual aim; animatable time
- Apparent | Geometric refraction toggle; eclipse geometric disk occultation + artistic Effects
- Optional synced sun/moon lamps (Add/Remove)
- Looks: Sky Strength, World Contribution, Exposure, White Balance, Airglow
- Physically Accurate brightness preset + Reset Atmosphere
- N-panel cockpit (Variant C IA)
- Blender Extension packaging (zip + remote repo)

### Out of scope

- Clouds (any form)
- Volumetric fog / volume shaders for atmosphere
- Planets and full astronomy-suite features
- Real binary-star orbital mechanics
- Full lunar BRDF / research-grade path-traced atmosphere
- Reverse-engineering Physical Atmosphere 2 (or any paid addon)
- Implementing/shipping the addon in this planning effort

---

## 4. Target platform

| Item | Requirement |
|---|---|
| Blender | **5.2+** (`blender_version_min = "5.2.0"`) |
| Author platform | Windows (design portable) |
| Cycles | **First-class** |
| EEVEE | Supported where practical; **no parity claims** |

### EEVEE gaps (must document in UI/docs)

- Sky Texture **Sun Disc is Cycles-only** — EEVEE daylight needs a **synced Sun lamp**
- World is an internal probe / treated as indirect — overlays are look-first, weak as scene lights
- Prefer addon Sun lamp with World **Sun Extraction Threshold = 0** (avoid double-sun)
- Stars / bright World speckles: decorative on EEVEE, no lighting promise
- Remap Sun Punch → lamp Strength; Sun Size soft control → lamp Angle on EEVEE

Research: [`docs/research/eevee-parity-and-gaps.md`](research/eevee-parity-and-gaps.md)

---

## 5. Packaging

Ship as a Blender **Extension** (`type = "add-on"`), not legacy-only.

| Field | Value |
|---|---|
| `id` | `ouroskies` |
| `name` | `OuroSkies` |
| `tagline` | `Physically grounded skies for Blender Worlds` |
| `license` | `["SPDX:GPL-3.0-or-later"]` |
| `maintainer` | `Ouroborusss <https://github.com/Ouroborusss>` |
| `blender_version_min` | `5.2.0` |
| `website` | `https://github.com/Ouroborusss/Ouroskies` |
| Schema | `blender_manifest.toml`, `schema_version = "1.0.0"` |
| `bl_info` | **Do not ship** |

**Channels:** both —

1. **extensions.blender.org** when ready (implies GPL + CC0 add-on assets + moderation)
2. **Self-hosted static remote** for staging / early builds (`extension server-generate` → `index.json`)

**Build:** `extension validate` → `extension build` → `{id}-{version}.zip`.  
**Offline:** Install from Disk (no updates on that path).  
**Code shape:** `__package__`, relative imports, `extension_path_user` for user data; no writes into install tree.

Research: [`docs/research/extension-packaging-and-remote-repos.md`](research/extension-packaging-and-remote-repos.md)

---

## 6. Architecture

### Ownership

| Layer | Owns |
|---|---|
| **Scene PropertyGroup** | Source of truth for all cockpit settings |
| **Python** | Place/date evaluation (any place/time, animatable), aim writes, lamp Add/Remove + sync, authoring OuroSkies World, Rebuild Sky Graph, Detach |
| **World graph** | Multiple Scattering evaluation + overlay shading (disks, stars, Milky band, eclipse mixes, airglow). No astronomy math in nodes; no per-frame node rebuilds |

### World lifecycle

1. **Enable** — create a dedicated **OuroSkies World**, switch the scene to it, remember previous World  
2. **Rebuild Sky Graph** — restore canonical node layout from Scene settings (hand edits unsupported)  
3. **Detach** — switch back to previous World, **delete** OuroSkies World, stop handlers/drivers  

### Atmosphere baseline

- One `ShaderNodeTexSky` with `sky_type = 'MULTIPLE_SCATTERING'` → Background → World Output Surface  
- Live atmosphere knobs bind to RNA props (`air_density`, `aerosol_density`, `ozone_density`, `altitude`)  
- No OSL / pure-node atmosphere rebuild; no World Volume  
- Explicitly set `MULTIPLE_SCATTERING` when creating nodes (do not rely on API default text)

Research: [`docs/research/cycles-world-sky-atmosphere-options.md`](research/cycles-world-sky-atmosphere-options.md)

### Aiming math

- Pure-Python Meeus/NOAA-style sun + Meeus moon (topocentric); no NREL `spa.c`; Astropy not a hard dep  
- Blender +Y north, +Z up, +X east: overlay dir `(cos alt·sin az, cos alt·cos az, sin alt)`  
- Sky Texture: `sun_elevation = alt`, `sun_rotation = −az` (radians in RNA) — **verify** sunrise → +X on first Cycles check  
- Canonical timeline: **UTC**; civil UI via `zoneinfo`

Research: [`docs/research/sun-moon-aiming-and-eclipse-timing.md`](research/sun-moon-aiming-and-eclipse-timing.md)

---

## 7. Atmosphere & Looks

### Atmosphere (friendlier labels + end-user tooltips)

| Label | Binds to | Notes |
|---|---|---|
| Air | `air_density` | Soft UI 0–10, decimals; type-beyond OK |
| Dust | `aerosol_density` | Tooltip mentions Blender Aerosols |
| Ozone | `ozone_density` | Same range |
| Altitude | `altitude` | Meters; **mirrored** in Place (type) and Looks/Atmosphere (slide) |

### Brightness / grade

| Control | Job |
|---|---|
| **Sky Strength** | Visible sky / backdrop energy (Background Strength) |
| **World Contribution** | How hard the World lights the scene (materials / GI) |
| **Exposure** | Color Management convenience mirror — **never** driven by eclipse FX |
| **Sun Punch** | Cycles `sun_intensity`; EEVEE → synced Sun lamp Strength (**lives under Celestials**) |
| **White Balance** | Kelvin + presets after scatter; tints sky + synced lamps |
| **Airglow** | Soft night World fill (strength + artistic tint); daylight fade |

### Presets / actions

- **Physically Accurate** — sets Sky Strength + sun/moon lamp energies to real-world targets; resets **World Contribution** to neutral; resets **WB** to Daylight (~6500K); does **not** reset Air/Dust/Ozone/Altitude; does **not** drive Exposure  
- **Reset Atmosphere** — restores Air / Dust / Ozone / Altitude defaults  

### WB presets

Daylight (~6500K, default), Cloudy, Shade, Warm — exact K for non-Daylight in §13.

Always **Multiple Scattering** in-cockpit; legacy sky models / raw node edits = advanced only.

---

## 8. Celestials

### Aim

- **Aim mode** default: **Manual** (Place/Date optional)  
- **Aim refraction:** Apparent \| Geometric; default **Apparent**; **eclipse math always Geometric**; UI note when they diverge near the horizon  
- Secondary sun: always manual (artist-posed)

### Primary / secondary sun

- Sun Size for both under Celestials  
- Sun Punch under Celestials  
- Manual elev/az when Aim = Manual  

### Moon

- Disk in World shader; place/date or manual  
- During solar occultation: **dark silhouette** (new-moon face), not normal phase shading  
- Optional moon lamp for fill  

### Place/date

- Lat / lon / elevation (m) / date / time / timezone  
- Freely changeable; animatable for timelapses  
- Evaluation canonicalizes to UTC  

---

## 9. Stars

- Procedural medium field; looks over catalog accuracy  
- No twinkle by default  
- **Milky band** togglable; soft glow that **fades before the horizon** (no hard angled clip)  
- Daylight fade with sun elevation (curve in §13)  
- Density / Brightness knobs in Looks  

Prototype: [`docs/prototypes/procedural-star-field-looks.html`](prototypes/procedural-star-field-looks.html)

---

## 10. Eclipse

### Geometric (always when disks overlap)

- Topocentric δ vs R☉, R☾ from aiming research  
- Moon occults sun; dark silhouette during occultation  

### Eclipse Effects (optional artistic)

- Effects Strength, Corona, Sky Dim, Sun Lamp Dim  
- Bailey’s beads + diamond ring: **manual overlays available anytime**  
- Exposure convenience slider left alone  

Lunar eclipses (Earth shadow on moon): not in this spec’s eclipse path (§13).

---

## 11. Lamps

- Optional; paired **Add / Remove** for sun and moon lamps  
- When present, Python owns aim (and Strength when Physically Accurate / Sun Punch / eclipse lamp dim apply)  
- EEVEE: strongly recommend enabling sun lamp for daylight  
- Do not mass-delete unmarked lights  

---

## 12. N-panel IA (Variant C)

Prototype: [`docs/prototypes/npanel-cockpit-ia.html`](prototypes/npanel-cockpit-ia.html)?variant=C

1. **Sticky Now** — place/time readout, Aim (default Manual), Aim refraction, Physically Accurate, Enable, Detach  
2. **Looks** — Air, Dust, Ozone, Altitude, Sky Strength, World Contribution, Exposure, WB (+ presets), Airglow (+ tint), Reset Atmosphere, Stars (+ Milky band)  
3. **Celestials** — primary/secondary sizes, Sun Punch, manual elev/az, moon  
4. **Eclipse** — Effects On, Strength, Corona, Sky Dim, Sun Lamp Dim, beads, diamond ring  
5. **Setup** — lat/lon/elevation/timezone, Add/Remove lamps, Rebuild Graph  

End-user descriptions/tooltips on controls.

---

## 13. Open numeric defaults & deferred fog

Fill during implementation or a short follow-up; not product-scope forks:

- Kelvin numbers for Cloudy / Shade / Warm — provisional in `ouroskies/defaults.py` (7500 / 8000 / 4500; Daylight 6500)  
- Airglow default strength + default tint — provisional (`0.03`, cool green-grey)  
- Physically Accurate numeric targets (Sky Strength, lamp W·m⁻², World Contribution neutral) — Sky/WC provisional `1.0`; lamps later  
- Reset Atmosphere default values — provisional in `ouroskies/defaults.py` (Air/Dust/Ozone 1.0, Altitude 100 m)  
- Confirm `sun_rotation = −az` on Cycles 5.2 sunrise → +X  
- Previous-World snapshot strategy if user deletes it while active  
- Daylight star fade curve  
- Star Density/Brightness defaults; Milky band node recipe  
- Horizon / ground / non-volume aerial perspective (if any)  
- Filmic/AgX notes beyond Exposure convenience  
- Multi-World / linked-scene behavior  
- Performance budgets  
- Binary-sun default offsets  
- Lunar eclipses?  
- Bailey’s beads / diamond ring / corona shader recipes  
- Pollution/OPAC presets, place search, sunrise readout (optional inspiration)  
- Canonical GitHub repo URL: `https://github.com/Ouroborusss/Ouroskies` (set)  

---

## 14. Research & prototype index

| Asset | Role |
|---|---|
| [`docs/research/cycles-world-sky-atmosphere-options.md`](research/cycles-world-sky-atmosphere-options.md) | Sky Texture Multiple Scattering baseline |
| [`docs/research/sun-moon-aiming-and-eclipse-timing.md`](research/sun-moon-aiming-and-eclipse-timing.md) | Ephemeris + Blender frame + eclipse trigger |
| [`docs/research/extension-packaging-and-remote-repos.md`](research/extension-packaging-and-remote-repos.md) | Extension packaging checklist |
| [`docs/research/eevee-parity-and-gaps.md`](research/eevee-parity-and-gaps.md) | EEVEE gaps |
| [`docs/research/physical-atmosphere-2-inspiration-checklist.md`](research/physical-atmosphere-2-inspiration-checklist.md) | Public PA2 inspiration only |
| [`docs/prototypes/npanel-cockpit-ia.html`](prototypes/npanel-cockpit-ia.html) | N-panel IA (Variant C) |
| [`docs/prototypes/procedural-star-field-looks.html`](prototypes/procedural-star-field-looks.html) | Star / Milky band look target |

Wayfinder decisions: `.scratch/ouroskies-spec/issues/*.md` and [`map.md`](../.scratch/ouroskies-spec/map.md).
