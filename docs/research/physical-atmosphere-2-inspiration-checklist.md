# Physical Atmosphere² — inspiration checklist for OuroSkies

**Question:** From **public** marketing/docs/listings only (no reverse-engineering), what feature surface does Physical Atmosphere 2 advertise that is useful as an **inspiration checklist** for OuroSkies — and which items are already out of scope (clouds, volumes, etc.)?

**Scope:** Public vendor docs, release notes, and press summaries only. No addon install, no purchased archives, no private/customer-only content. OuroSkies tags use the standing product scope (Nishita-class World sky, suns/moon/stars, place/date, optional lamps, artistic eclipses, Extension packaging; **no** clouds / volumetric fog / planets / full lunar BRDF / real binary orbits).

---

## 1. Verdict

Physical Atmosphere² (PA2) publicly advertises a **full sky + volumetric environment** stack: spectral/multiple-scattering atmosphere, sun/moon/planets/stars, Earth vs Artistic aiming, camera-style exposure/white balance, tiered UI, and (as the heavy half) multi-layer volumetric clouds + live GFS weather — shipping as a **Blender 5.2+ Extension**.

For OuroSkies, the useful inspiration is mostly the **non-volume sky cockpit**: place/date vs manual aim, air/aerosol/ozone-style atmosphere knobs, moon+stars with Earth-time positions, exposure/WB, Add/Remove own World, and progressive UI depth. **Clouds, weather maps, planet ground/from-orbit rendering, volume god-rays, and planet ephemerides** are clearly advertised and are **out of scope**. SuperHive product-page copy was **not reachable** from this research environment (Cloudflare block); treat listing-only bullets as **Unknown** unless echoed on physicaladdons.com or press.

---

## 2. Source list (URLs used)

| Source | URL | Role |
|---|---|---|
| Vendor getting started (public) | https://www.physicaladdons.com/physical-atmosphere/getting-started/ | Product pitch, requirements, Extension install, Simple/Advanced/Scientific layouts, Add Atmosphere / own World |
| Vendor documentation (public, Advanced UI) | https://www.physicaladdons.com/physical-atmosphere/documentation/ | Feature surface by panel section |
| Vendor release notes (public) | https://www.physicaladdons.com/physical-atmosphere/release-notes/ | 2.5.2 launch bullets + later public changelog feature blurbs |
| Vendor known issues (public) | https://www.physicaladdons.com/physical-atmosphere/known-issues/ | Platform caveats (not feature claims) |
| Vendor product root (redirect) | https://www.physicaladdons.com/physical-atmosphere/ | Redirects to getting started |
| CG Channel (press, cites Superhive) | https://www.cgchannel.com/2026/07/physical-atmosphere-2-generates-insanely-detailed-blender-skies/ | Secondary summary: spectral atmosphere, pollution, “stupidly advanced” knobs, space views, price/beta, Blender 5.2+ |
| Superhive listing | Purchase-only storefront referenced by vendor (“only available… on Superhive”) | **Not retrieved** here (HTTP 403 / Cloudflare). Listing-exclusive bullets remain **Unknown**. |

**Not used as PA2 feature truth:** Physical Starlight and Atmosphere (PSA) docs/listings — predecessor product; binary-sun / object-fog claims there are **not** assumed for PA2 unless PA2 pages repeat them.

---

## 3. Feature checklist

Tags: **Already covered** = in OuroSkies standing scope / language; **Consider** = undecided or good cockpit/UX inspiration still compatible with World-shader focus; **Out of scope** = conflicts with OuroSkies exclusions; **Unknown** = not stated on a reachable public PA2 page.

| Feature | Public source | OuroSkies tag |
|---|---|---|
| Physically based sky / atmosphere live in viewport | Getting started; Release notes 2.5.2 | Already covered |
| Multiple scattering (+ multiplier; optional Hillaire LUT MS) | Docs → Atmosphere; Release notes 2.6.x | Already covered (MS baseline); LUT A/B → Consider |
| Rayleigh scattering toggle | Docs → Atmosphere | Already covered (Nishita-class / Sky Texture lineage) |
| Aerosols: turbidity / haze; pollution / OPAC profiles | Docs → Atmosphere; Simple “Pollution”; CG Channel “pollution” | Already covered (Dust/aerosols); OPAC profiles → Consider |
| Ozone control (+ monthly value for place/date) | Docs → Atmosphere; CG Channel | Already covered; monthly auto value → Consider |
| Airglow (night sky glow) | Docs → Atmosphere | Consider |
| Atmospheric refraction (flattening sun, loom; pressure/temp) | Docs → Atmosphere; Release notes 2.6.1 prototype | Consider (map/spec already flags refraction undecided) |
| Sun disk / sun light driving the scene | Getting started (“sunlight”, “sun light”); Docs → Sun | Already covered (disk + optional lamp) |
| Sun spectrum: measured AM0 or blackbody Temperature (K) | Docs → Sun, Moon & Planets | Consider (color-temp / alien-sun look) |
| Moon with phase + “familiar face”; Earth or Artistic pose | Docs → Moon; Getting started | Already covered (moon disk / phase / place-date); “familiar face” BRDF depth → Out of scope if full lunar BRDF |
| Stars with brightness; true positions for place/date/time | Docs → Stars; Getting started | Already covered (procedural stars in scope); **catalog-true** positions vs procedural → Consider / Unknown implementation |
| Earth mode: place, date, time → sun, moon, planet, star positions | Release notes 2.5.2; Docs → Sky & Observer | Already covered for sun/moon; planets → Out of scope |
| Artistic mode: drag / angle sun & moon | Docs → Artistic; Getting started | Already covered (manual aim) |
| Observer lat / lon / altitude (km); city search; auto-detect location | Docs; Getting started; Extension Network permission | Already covered (place/date); search/auto-detect → Consider |
| UTC zone / DST; sunrise/sunset readout; set current time | Docs → Earth mode; Release notes 2.7.4 | Already covered (timezone/UTC); sunrise/sunset UI → Consider |
| Body scale (distance/radius) for dramatic oversized moons; Sun Energy Conservation | Docs → Sky & Observer | Consider (size already in scope); energy conservation knob → Consider |
| Motion paths / sun analemma / compass / constellation overlays | Docs → Overlay | Consider (viewport helpers); constellations if catalog → Consider |
| Exposure EV + photographic (aperture / shutter / ISO) + bias | Docs → Camera Settings; Release notes 2.5.2 | Consider (OuroSkies has Exposure convenience / Physically Accurate preset — photographic suite undecided) |
| White balance (K) presets named by scene | Docs; Release notes 2.6.0 | Consider |
| World Output (f-stops) separate from sky look | Docs → Camera Settings | Consider |
| Dedicated World on Add; Remove Atmosphere teardown | Getting started | Already covered (OuroSkies World / Detach) |
| N-panel + Properties → World; Add Atmosphere | Getting started | Already covered (cockpit) |
| Simple / Advanced / Scientific interface layouts | Getting started; Docs intro; CG Channel “stupidly advanced” | Consider (cockpit IA / progressive disclosure) |
| Ships as Blender **extension** for Blender **5.2+** | Getting started; Release notes 2.5.2 | Already covered (Extension packaging) |
| EEVEE + Cycles viewport / render mentions | Release notes (e.g. 2.7.x Cycles viewport; EEVEE path) | Already covered (Cycles-first, EEVEE appreciated) — **not** parity promise |
| Quality presets (Potato…NASA) + temporal/foveated sky pipeline | Docs → Rendering; Release notes 2.6.0 | Out of scope as custom GPU sky renderer; quality UX metaphor → Consider lightly |
| Volumetric clouds (L0/L1/L2 + rain); coverage/shape/shading | Getting started; Docs → Clouds; Release notes 2.5.2 | **Out of scope** |
| Live GFS weather → cloud coverage maps | Getting started; Docs → Cloud Maps; Release notes 2.5.2 | **Out of scope** |
| Cloud shadows on objects; object shadows in atmosphere (god-rays) | Release notes 2.5.2; Docs → Rendering | **Out of scope** (volume/atmosphere interaction) |
| Blend objects into atmosphere (haze compositing) | Docs → Camera; Release notes 2.5.2 / 2.6.0 disabled | **Out of scope** (volumetric fog / aerial perspective on meshes) |
| Planets Mercury–Neptune true or artistic | Docs → Planets; Release notes 2.5.2 | **Out of scope** |
| Ground / Earth planet surface, maps, Hapke, from-altitude / space views | Docs → Ground; Release notes 2.7.0; CG Channel space views | **Out of scope** (planets / ground system) |
| Binary / secondary sun | — | **Unknown** on PA2 public pages (PSA advertised binary sun; do not import) |
| Eclipses (solar/lunar looks) | — | **Unknown** (not mentioned on fetched PA2 pages); OuroSkies eclipse look remains own scope |
| Object / volumetric fog as named PA2 feature | CG Channel mentions “fog” among advanced knobs | **Unknown** as first-party PA2 control name; any volume fog → **Out of scope** |
| Superhive marketing bullets beyond vendor docs | Storefront blocked here | **Unknown** |

---

## 4. Gaps PA2 advertises that OuroSkies hasn’t decided yet

Candidates for fog discussion or future tickets (inspiration only — not commitments):

1. **Atmospheric refraction** toggle (apparent sun shape / loom vs geometric aim) — already flagged undecided in the wayfinder map; PA2 documents a physical pressure/temperature-driven suite.
2. **Tiered cockpit** (Simple vs Advanced vs Scientific) — progressive disclosure for atmosphere/celestials without shipping volume science.
3. **Photographic exposure** (f-stop / shutter / ISO) vs single EV / Physically Accurate preset.
4. **White balance** as a sky “develop” control separate from sun blackbody temperature.
5. **Aerosol profiles** (OPAC / pollution archetypes) vs a single Dust slider.
6. **Airglow** night fill.
7. **Place UX**: geocoding search, auto-detect location, sunrise/sunset readout, analemma / day motion-path overlays.
8. **Sun spectrum modes** (measured solar vs blackbody K) for stylized / alien primary (and secondary) suns — without claiming PSA-style binary orbits.
9. **Stars**: catalog-true Earth positions vs procedural + optional milky band (OuroSkies language already prefers procedural milky band).
10. **World contribution** control (PA2 “World Output f-stops”) distinct from sky look / Exposure.

Explicitly **not** gap candidates for OuroSkies: cloud layers, GFS weather, planet ground, planets, volume god-rays, object-in-atmosphere compositing.

---

## 5. Inspiration only

This note is an **inspiration checklist** from **public** PA2 materials. It is **not** a requirement to match PA2, not a license to copy implementation, and not permission to reverse-engineer the addon. Features absent from reachable public pages are marked **Unknown** — do not invent them. OuroSkies remains World-shader / Nishita-class scoped; PA2’s volumetric half is competitive context, not a backlog.

---

*Researched 2026-08-04. Primary evidence: physicaladdons.com PA2 getting started, documentation, release notes. Superhive listing not retrieved (Cloudflare).*
