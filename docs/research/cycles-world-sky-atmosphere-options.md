# Cycles World sky atmosphere options (Blender 5.2)

**Question:** What options does Blender 5.2 give for a Nishita-class World sky (Rayleigh/Mie-style scattering, ozone/dust/turbidity-style parameters, sun disk) — built-in Sky Texture vs custom nodes/OSL/scripts — and which path best supports live artistic overrides while staying primarily in the World shader?

**Scope:** Plan/spec research for OuroSkies. Cycles-first. No volumetric fog. No clouds. Secondary sun + moon as custom overlays. No addon implementation in this ticket.

**Doc versions:** Prefer Blender 5.2 LTS manual / API. Feature history noted where 4.x docs still describe older naming.

---

## Verdict

**Baseline on the built-in Sky Texture node in Multiple Scattering mode**, wired through a Background shader into the World Output Surface. That model is Blender’s current Nishita-class atmosphere (air / aerosols / ozone / altitude / sun elevation–rotation / Cycles sun disk). Live artistic overrides map cleanly to the node’s RNA properties (animatable / driverable from an N-panel), without leaving the World graph.

**Do not** rebuild Rayleigh/Mie atmosphere in pure nodes or OSL for the baseline — the built-in LUT path already owns that accuracy. **Do** extend the same World tree with Mix/Add of Background (or color-mix into one Background) for secondary sun disk, moon disk, stars, and eclipse-style occlusion. Drive place/date → primary sun (and moon) aim from Python; keep atmosphere knobs on the Sky Texture node.

Built-in Sky Texture alone **cannot** provide binary/second sun, moon disk, procedural stars, eclipse presentation, or place/date astronomy.

---

## Findings by option

### 1. Built-in Sky Texture node (World)

**Role.** Procedural sky for environment lighting; “typically used in combination with the World Output Node.”

Sources:
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- https://docs.blender.org/manual/en/5.2/render/lights/world.html (World surface = Background color + strength; sky model is a supported surface approach)

**World wiring.** World Surface accepts a Background shader (color + strength). Sky Texture Color → Background Color → World Output Surface is the documented pattern.

Sources:
- https://docs.blender.org/manual/en/5.2/render/lights/world.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/background.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/output/world.html

**Sky models in 5.2**

| `sky_type` (API) | Manual name | Notes |
|---|---|---|
| `MULTIPLE_SCATTERING` | Multiple Scattering | Most accurate; multiple atmospheric bounces. Based on Fernando García Liñán. **Preferred Nishita-class baseline.** |
| `SINGLE_SCATTERING` | Single Scattering | Improved Nishita 1993; single bounces. Manual: legacy, may be removed. Formerly labeled “Nishita” in 4.x. |
| `PREETHAM` | Preetham | 1999 analytic daylight. Legacy; will be removed. Turbidity + sun direction. |
| `HOSEK_WILKIE` | Hosek/Wilkie | 2012. Legacy; will be removed. Turbidity + ground albedo + sun direction. |

Sources:
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html
- https://developer.blender.org/docs/release_notes/5.0/rendering/ (PR#140480 Multiple Scattering)
- https://www.blender.org/download/releases/5-0/ (old Nishita → “Single Scattering”; Multiple Scattering new)

**Default in 5.2 source:** new Sky Texture nodes initialize to `SHD_SKY_MULTIPLE_SCATTERING` (not Preetham). API docs still list default `'PREETHAM'` — treat the **source init** as product reality for new nodes; verify in addon when creating nodes.

Source: `blender-5.2.0/source/blender/nodes/shader/nodes/node_shader_tex_sky.cc` (e.g. https://fossies.org/linux/blender/source/blender/nodes/shader/nodes/node_shader_tex_sky.cc)

**Parameter groups (which UI shows what)** — from node draw code in the same source file:

**Preetham:** `sun_direction`, `turbidity`

**Hosek/Wilkie:** `sun_direction`, `turbidity`, `ground_albedo`

**Single / Multiple Scattering:**

| Control | API property | Manual / API meaning |
|---|---|---|
| Sun Disc | `sun_disc` | Include sun in output. Manual: **Cycles Only**. |
| Sun Size | `sun_size` | Angular diameter (manual: degrees; API stores radians, default ≈ 0.545°). |
| Sun Intensity | `sun_intensity` | Multiplier for sun disc lighting `[0, 1000]`. |
| Sun Elevation | `sun_elevation` | Angle from horizon. |
| Sun Rotation | `sun_rotation` | Rotation around zenith. |
| Altitude | `altitude` | Height from sea level; API `[0, 100000]`, default `100.0`. |
| Air | `air_density` | Air molecules; `0` = none, `1` ≈ urban. `[0, 1000]`. |
| Aerosols | `aerosol_density` | Dust / pollution / water droplets (5.x rename of older “Dust”). `0` = none, `1` ≈ urban. |
| Ozone | `ozone_density` | Ozone; useful for bluer sky. `0` = none, `1` ≈ urban. |

Sources:
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html
- Node UI branching: `node_shader_tex_sky.cc` (5.2.0 package above)

**Naming migration (4.x → 5.x):** 4.5 manual still called the scattering model **Nishita** and the haze control **Dust**. 5.0+ renames model to Single/Multiple Scattering and Dust → **Aerosols** (`aerosol_density`). Turbidity remains only on Preetham/Hosek.

Sources:
- https://docs.blender.org/manual/en/4.5/render/shader_nodes/textures/sky.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html

**Sockets vs properties (live overrides).** Declared sockets are only **Vector** (in) and **Color** (out). Atmosphere and sun controls are **node RNA properties**, not graph sockets. They are live-tweakable in the UI, animatable, and driverable (standard Blender property drivers). For addon N-panel: set `ShaderNodeTexSky` properties from Python / custom properties / drivers.

Sources:
- Socket declare in `node_shader_tex_sky.cc` (`node_declare`: Vector in, Color out)
- https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html
- https://docs.blender.org/manual/en/5.2/animation/drivers/introduction.html

**Sun disk behavior (Cycles).** Kernel evaluates a **single** sun direction from `sun_elevation` / `sun_rotation`, optional disc with angular diameter, intensity, limb darkening (~0.6), and earth-intersection cutoff. Atmosphere LUT is sampled separately and **added**. There is no second sun or moon in this path.

Source: `blender-5.2.0/intern/cycles/kernel/svm/sky.h` — `sky_radiance_nishita` (https://fossies.org/linux/blender/intern/cycles/kernel/svm/sky.h)

**Intensity / strength coupling.**

1. `sun_intensity` — multiplies **sun disc** contribution only (kernel above).
2. Background **Strength** — scales the whole World emission (sky + disc in the Color feed).
3. Scene **Exposure** (Color Management) — scattering skies are “very bright by default (hence accurate)”; 5.2 manual points to Properties → Color Management → Exposure.

Sources:
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/background.html
- Kernel sun intensity multiply in `sky.h`

**Vector input caveat.** When Single/Multiple Scattering **and** `sun_disc` is on, the Vector input socket is **disabled** (node update). Disable sun disc (or use overlays) if custom vector sampling is required.

Source: `node_shader_update_sky` in `node_shader_tex_sky.cc`

**Multiple suns / moon.** Built-in model exposes one elevation/rotation pair and one disc. No moon, no multi-sun API. Confirmed by UI props + kernel single `sun_dir`.

**EEVEE (brief).** Official 5.0 release notes: Multiple Scattering sky is “beautiful out of the box, in both Cycles and EEVEE.” Sun Disc remains Cycles-oriented: manual marks Sun Disc “Cycles Only”; EEVEE node-support page still says Sky Texture “In Nishita mode, the Sun Disc property is not supported” (stale “Nishita” naming); GPU node draw shows “Sun disc not available in EEVEE.” Atmosphere without disc is the EEVEE-safe subset.

Sources:
- https://www.blender.org/download/releases/5-0/
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- https://docs.blender.org/manual/en/5.2/render/eevee/limitations/nodes_support.html
- `node_shader_tex_sky.cc` EEVEE warning label

**World volume.** Surface and Volume are mutually exclusive in practice: infinite-distance surface is fully occluded by World volume. World volume is a poor fit for atmosphere (docs recommend a finite volume object for fog/scattering). OuroSkies preference (no volumetric fog) aligns with **Surface-only** World.

Sources:
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/output/world.html
- https://docs.blender.org/manual/en/5.2/render/lights/world.html

**Altitude note.** 4.5 manual claimed a ~60 km model limit. 5.2 manual drops that sentence; API allows `[0, 100000]`. Spec should treat 5.2 API ranges as authoritative and re-check visually at extreme altitudes.

---

### 2. Pure shader-node overlays (no OSL)

**What nodes can do well in World:**

- Combine environment contributions with **Mix Shader** / **Add Shader** of **Background** closures, or Mix RGB / Math into a single Background Color.
- Build **custom disks** (moon, secondary sun) from view/generated direction vs a direction vector (dot product / angular size thresholds), then feed high-value Color into Background Strength or Add.
- Procedural **stars** via Noise / Voronoi on direction coordinates, masked above horizon.
- **Eclipse look:** mask or subtract primary sun contribution (built-in disc off + custom discs, or factor-based Mix) when moon and sun angular positions overlap — artistic, not astronomical simulation.

Sources (building blocks):
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/mix.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/add.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/background.html
- https://docs.blender.org/manual/en/5.2/render/lights/world.html (only Background-class emission for World surface)

**What pure nodes cannot replace:** Built-in Multiple/Single Scattering LUT (spectral multi-bounce air/aerosol/ozone). Reimplementing that in nodes is out of scope for a maintainable addon baseline.

**Fit for OuroSkies:** Overlays + artistic factors **yes**; atmosphere core **no**.

---

### 3. OSL (Script node)

**Capabilities.** Custom surface/volume/displacement shading via Script node when Open Shading Language is enabled. Closures include `background()` / `emission()` among others — enough in principle to author a custom sky.

Sources:
- https://docs.blender.org/manual/en/5.2/render/cycles/osl/index.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/utilities/script.html

**Hard limits for a portable Cycles-first addon:**

- Script node is **Cycles only**.
- OSL requires enabling OSL; **GPU unsupported unless OptiX**; further OptiX feature gaps (noise, `trace`, etc.).
- Generally slower than built-in nodes; production tip is to wrap Script nodes in node groups.

**Fit for OuroSkies:** Research/prototype alternate atmospheres only — **not** the baseline World sky path.

---

### 4. Python-generated / driven World node trees

**Capabilities.** Addon builds and maintains a World node tree: Sky Texture (Multiple Scattering) + overlay group(s); exposes N-panel → RNA props; computes place/date → `sun_elevation` / `sun_rotation` (and moon overlay direction); optional synced sun/moon lamps (out of this ticket’s atmosphere focus).

**World nodes always on:** Blender 5.0 removed “Use Nodes” for Worlds — Worlds always use nodes.

Source: https://developer.blender.org/docs/release_notes/5.0/rendering/

**Fit for OuroSkies:** This is the **integration layer** around option 1 + option 2, not a separate atmosphere model.

---

## What built-in Nishita-class alone cannot give OuroSkies

| Need | Built-in Sky Texture | Typical World extension |
|---|---|---|
| Primary sun disk | Yes (Cycles; Single/Multiple Scattering) | Optional custom disc if EEVEE parity or more control |
| Secondary / binary sun disk | No (single sun params + kernel) | Custom disk overlay; Python pose |
| Moon disk | No | Custom disk overlay; place/date aim |
| Procedural stars | No | Noise-based overlay |
| Eclipse look | No (no moon; one disc) | Overlap masking / artistic Mix |
| Place/date aim | No | Python → elevation/rotation (+ moon dir) |
| Air / aerosol / ozone live tweaks | Yes (RNA props) | N-panel → props / drivers |
| Turbidity-style haze | Via **Aerosols** (scattering models), not Turbidity | Prefer aerosols; Turbidity only on legacy Preetham/Hosek |
| Volumetric fog / clouds | Out of scope; World volume discouraged for atmosphere | Do not use World Volume for this |

---

## Recommendation for OuroSkies

1. **Atmosphere baseline:** One `ShaderNodeTexSky` with `sky_type = 'MULTIPLE_SCATTERING'` in the World Surface graph → Background → World Output.
2. **Artistic atmosphere overrides:** N-panel binds to `air_density`, `aerosol_density`, `ozone_density`, `altitude`, and optionally `sun_intensity` / `sun_size` / `sun_disc`. Prefer drivers or direct RNA writes over rebuilding scattering in nodes.
3. **Primary sun aim:** Python place/date → `sun_elevation` + `sun_rotation`. Keep built-in Cycles sun disc for primary when on Cycles; document EEVEE disc gap.
4. **Celestial overlays:** Same World tree — node group(s) for secondary sun, moon, stars; Mix/Add Background (or color composite). Eclipse = overlay logic, not Sky Texture.
5. **Avoid for baseline:** OSL atmosphere; Preetham/Hosek (legacy removal); Single Scattering unless needed for parity with older files; World Volume fog.
6. **Exposure workflow:** Document that Multiple/Single Scattering are physically bright; expect Color Management Exposure (and/or Background Strength) tuning — do not “fix” accuracy by crushing sky color in the node alone without a clear artistic Strength control.

**Rationale (tied to sources):** Multiple Scattering is documented as the most accurate built-in model and ships as the 5.0+ Nishita-class successor; parameters match OuroSkies dust/ozone/turbidity-style needs via air/aerosols/ozone; Cycles sun disc is first-class; World Surface + Background keeps the design in-shader; overlays cover product gaps the kernel deliberately does not (single sun).

---

## Open questions / caveats

1. **API default vs source init:** API text still says default `sky_type` `'PREETHAM'`; 5.2.0 source initializes Multiple Scattering. Addon must set `MULTIPLE_SCATTERING` explicitly when creating nodes.
2. **EEVEE docs lag:** Node-support page still says “Nishita mode” for sun disc; confirm wording against 5.2 UI and whether Multiple Scattering sun disc remains unsupported in EEVEE (source warning suggests yes).
3. **Altitude physical range:** 4.5 “60 km” note removed in 5.2 manual; API max 100000 — validate look at high altitude for aerial scenes.
4. **Sun disc + Vector:** Built-in disc disables Vector input — overlays that need custom coords on the Sky node itself must turn disc off and supply a custom primary disc, or leave Vector unused.
5. **Day-cycle wrapping:** Multiple Scattering path wraps elevation/rotation for animation (`sky_simplify_multiscatter_elevation_rotation` in source). Place/date drivers should understand that wrapping when animating across midnight/horizon.
6. **Legacy removal timeline:** Preetham, Hosek/Wilkie, and Single Scattering are marked legacy/may-or-will-be-removed — do not build OuroSkies features that depend on them.
7. **Strength vs Exposure vs sun_intensity:** Spec should define which control is “artist sky brightness,” which is “sun disk punch,” and which is “scene exposure,” to avoid fighting the physically bright LUT.

---

## Primary sources index

| Source | URL / path |
|---|---|
| Sky Texture (5.2 manual) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html |
| Sky Texture (4.5 manual, Nishita/Dust naming) | https://docs.blender.org/manual/en/4.5/render/shader_nodes/textures/sky.html |
| ShaderNodeTexSky API (5.2) | https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html |
| World Environment (5.2) | https://docs.blender.org/manual/en/5.2/render/lights/world.html |
| World Output (5.2) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/output/world.html |
| Background (5.2) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/background.html |
| Mix / Add Shader (5.2) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/mix.html — add.html |
| OSL (5.2) | https://docs.blender.org/manual/en/5.2/render/cycles/osl/index.html |
| Script Node (5.2) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/utilities/script.html |
| EEVEE node support (5.2) | https://docs.blender.org/manual/en/5.2/render/eevee/limitations/nodes_support.html |
| Drivers intro (5.2) | https://docs.blender.org/manual/en/5.2/animation/drivers/introduction.html |
| 5.0 rendering release notes | https://developer.blender.org/docs/release_notes/5.0/rendering/ |
| 5.0 product notes (sky / EEVEE) | https://www.blender.org/download/releases/5-0/ |
| PR#140480 (Multiple Scattering) | https://projects.blender.org/blender/blender/pulls/140480 |
| Node UI / init (5.2.0 source) | `source/blender/nodes/shader/nodes/node_shader_tex_sky.cc` |
| Cycles sun/sky kernel (5.2.0) | `intern/cycles/kernel/svm/sky.h` |
