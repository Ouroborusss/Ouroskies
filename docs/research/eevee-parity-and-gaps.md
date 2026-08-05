# EEVEE parity and gaps for Nishita-class World sky + synced lamps (Blender 5.2)

**Question:** For a Nishita-class World sky plus synced sun/moon lamps, what works in **EEVEE** on Blender 5.2 versus **Cycles**, and what fidelity gaps must the OuroSkies spec explicitly document so EEVEE stays “appreciated” without promising Cycles parity?

**Scope:** Plan/spec research only. Locked baseline from prior work: Cycles first-class; Sky Texture `MULTIPLE_SCATTERING` → Background → World Output Surface; RNA air/aerosols/ozone; no World Volume; primary sun via Sky Texture sun disc on Cycles; moon / secondary sun / stars / eclipse as World overlays; optional addon-owned synced sun/moon lamps.

**Related (cite, do not re-litigate):**

- `/home/ouro/ouroskies/docs/research/cycles-world-sky-atmosphere-options.md` — atmosphere wiring, Multiple Scattering params, Cycles sun disc, overlay strategy
- `/home/ouro/ouroskies/docs/research/sun-moon-aiming-and-eclipse-timing.md` — place/date aim → elevation/rotation; eclipse look trigger geometry

**Doc versions:** Blender 5.2 LTS manual / API; 5.0 release notes for Multiple Scattering product claims; 5.2-release source for EEVEE UI/GPU path.

---

## Verdict

**EEVEE can render the Multiple Scattering / Single Scattering atmosphere look** (air, aerosols, ozone, altitude, sun elevation/rotation) through the same World Sky Texture → Background path, and Blender 5.0 marketed that sky as “beautiful out of the box, in both Cycles and EEVEE.” **It cannot match Cycles on primary sun behavior:** Sky Texture **Sun Disc is Cycles-only** (manual + EEVEE node-support + UI error label + GPU LUT path with no disc). On EEVEE, sharp sun lighting and shadows require a **real Sun light object** (addon-synced and/or World **Sun Extraction**), not the Sky Texture disc.

**OuroSkies should promise EEVEE:** atmosphere tint/look, aimed sky direction, camera-visible custom overlays (moon / second sun / stars) at “good enough” background fidelity, and **synced Sun/Moon lamps as the primary direct-light path**. **Do not promise:** Cycles-parity sun disc in the sky shader, World-as-direct lighting strength/precision, sharp environment-driven shadows from the sky alone, or identical lighting from bright World overlays. Document those as Cycles-first / EEVEE gaps so EEVEE remains appreciated without overselling.

---

## What works on EEVEE (practical subset)

### Atmosphere (Sky Texture Multiple / Single Scattering)

| Capability | EEVEE | Notes |
|---|---|---|
| `MULTIPLE_SCATTERING` / `SINGLE_SCATTERING` sky color | Yes | GPU path precomputes a LUT (`SKY_*_precompute_texture`) and samples it in `node_tex_sky_nishita` — same air/aerosol/ozone/altitude/elevation/rotation knobs as Cycles for the **sky dome**, without the disc. |
| Preetham / Hosek/Wilkie | Yes (legacy) | Not OuroSkies baseline; still GPU-supported analytic paths. |
| Aim via `sun_elevation` / `sun_rotation` | Yes | Same RNA props; Multiple Scattering wraps elevation/rotation in the GPU precompute path (see atmosphere research). |
| Air / aerosols / ozone / altitude | Yes | Same RNA; drives LUT bake. |
| Physically bright default | Yes | Manual: lower Color Management **Exposure**; same workflow as Cycles. |

Sources:

- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html
- https://www.blender.org/download/releases/5-0/ (“Beautiful out of the box, in both Cycles and EEVEE”)
- https://developer.blender.org/docs/release_notes/5.0/rendering/ (PR#140480 Multiple Scattering)
- 5.2 source: `source/blender/nodes/shader/nodes/node_shader_tex_sky.cc` (GPU LUT for Single/Multiple); `source/blender/gpu/shaders/material/gpu_shader_material_tex_sky.glsl` (`node_tex_sky_nishita` = LUT lookup only)

### World graph building blocks

| Capability | EEVEE | Notes |
|---|---|---|
| Background → World Output Surface | Yes | Only World surface shader class; shared with Cycles. |
| Mix / Add of Background (or color Mix into one Background) | Yes (not listed unsupported) | EEVEE node-support: “If something is not listed here, it is supported.” Use for moon / second sun / stars / eclipse masks. |
| Custom direction-based disks / stars in World | Camera background: yes in principle | Same node math as Cycles for **visible** sky. Lighting contribution is a different story (gaps table). |
| OSL / Script node atmosphere or overlays | No | Cycles-only (atmosphere research). |

Sources:

- https://docs.blender.org/manual/en/5.2/render/lights/world.html
- https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/background.html
- https://docs.blender.org/manual/en/5.2/render/eevee/limitations/nodes_support.html

### Lamps (when addon syncs them)

| Capability | EEVEE | Notes |
|---|---|---|
| Sun light: infinite parallel rays; rotation aims; location ignored | Yes | Same conceptual model as Cycles — ideal sync target for sky direction. |
| Sun **Angle** (angular diameter) | Yes | Softens sun shadows / specular; maps to artistic soft-sun / eclipse softness knobs. |
| Sun Strength in W/m² (with Normalize) | Yes | Manual clear-sky ~1000, moonlight ~0.001 — useful EEVEE defaults when World disc cannot light. |
| Point / Spot / Area for special cases | Partial | Usable; see gaps (no light node trees; Area Beam spread unsupported; Spot size ≠ cone softness). |
| EEVEE per-light Diffuse / Glossy / Transmission / Volume multipliers | Yes (EEVEE) | Artistic influence; values ≠ 1.0 break PBR — document if addon exposes them. |

Sources:

- https://docs.blender.org/manual/en/5.2/render/lights/light_object.html
- https://docs.blender.org/manual/en/5.2/render/eevee/light_settings.html

### EEVEE World helpers relevant to sky

| Capability | Role for OuroSkies |
|---|---|
| World Light Probe **Resolution** | Controls how finely environment lighting is stored; higher helps broad sky gradients, not tiny discs. |
| World **Sun** extraction (Threshold / Angle / Use Shadow) | Can peel intense World peaks into an internal sun light for better outdoor lighting — complementary to, or conflicting with, addon-owned synced lamps if both fight for “the” sun. |

Source: https://docs.blender.org/manual/en/5.2/render/eevee/world_settings.html

---

## Gaps table (must document — not Cycles parity)

| Topic | Cycles | EEVEE (5.2) | Spec implication |
|---|---|---|---|
| **Sky Texture Sun Disc** | Supported; lights scene as part of World; `sun_size` / `sun_intensity` | **Not supported.** Manual: “Sun Disc Cycles Only.” Node-support still says “In Nishita mode…” (stale name for Single/Multiple). UI: “Sun disc not available in EEVEE.” GPU shader never injects a disc (LUT only). Cycles kernel adds disc when angular diameter ≥ 0. | Treat built-in disc as **Cycles-only**. On EEVEE: disable reliance on disc for lighting; use synced Sun lamp and/or custom World disc for **camera** only. |
| **Primary sun as World lighting** | Disc + sky = direct environment emission | World contribution stored in an **internal Light Probe**; “less precise than Cycles.” World is treated as **indirect** lighting (Cycles: direct). | Do not claim World sky alone lights EEVEE scenes like Cycles. |
| **Sharp shadows from sky sun** | From sun disc sampling | Probe cannot reproduce intense directional sources with enough precision; needs **Sun light** or **Sun Extraction**. Historical EEVEE Nishita patch explicitly deferred disc because EEVEE would not cast sharp shadows from a huge Background spike. | EEVEE daylight shadows ⇒ synced Sun lamp (preferred) or document Sun Extraction as an alternate. |
| **`sun_intensity` / `sun_size` on Sky Texture** | Affect disc | UI still shows when `sun_disc` is on, but disc path is ineffective on EEVEE | Either hide/ignore on EEVEE or map those knobs to **lamp** Strength/Angle instead. |
| **Environment lighting precision** | Full path-traced World | Probe resolution + indirect classification; **Indirect Light** clamp/intensity also limit World | Document Exposure + probe resolution + clamp interaction; avoid “match Cycles HDR intensity” language. |
| **Custom World overlay disks (moon, 2nd sun)** as **visible** background | High dynamic range, sharp | Visible via Background mix — generally works | Promise camera-sky overlays; QA against Exposure. |
| **Same overlays as scene lighting** | Can contribute strongly if bright | Tiny bright features smear / lose punch in World probe; may **Sun-extract** unexpectedly or get crushed by indirect clamp / half-float limits | Spec: overlays are **look** first; lighting from overlays is best-effort / Cycles-stronger. Prefer lamps for moon fill if needed. |
| **Stars** | Speckles in World can light (noisy) | Worse: probe undersampling + firefly/clamp behavior | Stars = decorative World only on EEVEE; no lighting promise. |
| **Eclipse look** | Artistic Mix / mask of discs in World (+ optional lamps) | Same node logic for camera; lighting/occlusion of **scene** needs lamp Strength/visibility choreography | Document eclipse as World look + lamp dimming on EEVEE, not World-only occlusion of lighting. |
| **Light node trees** | Supported on lights | **Not supported** | Sync lamps via object RNA (color, strength, angle), not shader graphs. |
| **Area light Beam spread** | Supported | **Not supported** | Do not use Beam spread as an EEVEE moon soft-box control. |
| **Spot Size vs cone softness** | Size affects softness | Size does **not** change cone softness (EEVEE limitation) | Avoid Spot-based “soft moon” recipes that assume Cycles Spot behavior. |
| **Numerical precision** | Full float path | Shader tree float32; most EEVEE calc + output **half float**; Combined clamps negatives | Extreme Background Strength / tiny hot spots may not match Cycles. |
| **OSL overlays / custom skies** | Possible with caveats | Unavailable | Keep overlays pure nodes. |
| **World Volume atmosphere** | Poor fit anyway (locked out) | Volumetrics: single scattering; camera-rays only; etc. | Still out of scope; no EEVEE volume “cheat” for atmosphere. |

Sources:

- https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html (Sun Disc Cycles Only)
- https://docs.blender.org/manual/en/5.2/render/eevee/limitations/nodes_support.html (Sky Texture Sun Disc; Light Falloff; etc.)
- https://docs.blender.org/manual/en/5.2/render/eevee/world_settings.html (probe; indirect; sun extraction)
- https://docs.blender.org/manual/en/5.2/render/eevee/limitations/limitations.html (lights, shadows, half precision)
- https://docs.blender.org/manual/en/5.2/render/eevee/render_settings/light_paths.html (indirect clamp/intensity includes World)
- https://docs.blender.org/manual/en/5.2/render/eevee/light_settings.html (shadows; influence; no Custom Distance on Sun)
- https://archive.blender.org/developer/differential/0013/0013522/D13522.html (Nishita-in-EEVEE: disc deferred; LUT without sun; sharp shadows need lamp)
- 5.2 source UI warning + GPU `node_tex_sky_nishita` (no disc); Cycles `intern/cycles/kernel/svm/sky.h` (disc + `sun_intensity`)

---

## Lamp sync notes (EEVEE vs Cycles)

### Why synced lamps matter more on EEVEE

On **Cycles**, the Sky Texture sun disc can provide both the **visible** solar disk and a large share of **direct** sun lighting/shadows. On **EEVEE**, that disc path is missing, so an addon-owned **Sun light** aligned to the same elevation/rotation as the Sky Texture is not a nice-to-have — it is the practical way to get daylight direction, strength, and shadows.

Moon lighting is analogous: a dim **Sun** light (manual suggests ~0.001 W/m² moonlight) aimed with lunar azimuth/altitude from the aiming research gives believable fill; World moon disk alone will not light like Cycles.

### Sync mapping (engine-agnostic aim, engine-aware energy)

| Sky / astronomy quantity | Sky Texture (World) | Synced Sun lamp | EEVEE-specific note |
|---|---|---|---|
| Direction (alt/az → Blender +Y north) | `sun_elevation`, `sun_rotation` (primary); moon overlay dir | Object rotation so −Z (or light forward) matches direction; **location irrelevant** | Same aim math both engines. |
| Visible solar disk size | `sun_size` (Cycles disc) | Sun light **Angle** | On EEVEE, expose Angle as the soft-sun control; do not expect Sky `sun_size` to matter. |
| Sun punch | `sun_intensity` (Cycles disc) + Background Strength | Sun **Strength** (W/m²) + Exposure | EEVEE: drive lamp Strength; optionally leave Sky `sun_disc` off to avoid false expectations. |
| Moon disk look | World overlay | Optional; separate from light | Keep look in World; light via lamp if needed. |
| Moon fill | Overlay emission (weak on EEVEE) | Second Sun lamp, very low Strength | Prefer lamp on EEVEE. |
| Color temperature | Sky LUT | Light Temperature / Color | EEVEE: single color per light (no light nodes). |

### Sun Extraction vs addon Sun lamp

EEVEE World **Sun** panel (Threshold ≠ 0) extracts intense World energy into an **engine-managed** sun light for probe quality. That can help HDRI-like Worlds, but for OuroSkies:

- If the addon already owns a synced Sun lamp, **document interaction**: double sun (addon + extracted), mismatched angles, or fighting strengths.
- Spec options to pick one policy: (A) addon lamp only — recommend Threshold = 0; (B) extraction only — no addon sun; (C) hybrid with explicit precedence. **Recommend A** for predictable aim sync with place/date.

Source: https://docs.blender.org/manual/en/5.2/render/eevee/world_settings.html

### Shadow / softness expectations

EEVEE sun shadows use Virtual Shadow Mapping + Shadow Map Raytracing (not Cycles ray shadows). Softness comes from Sun **Angle** and EEVEE jitter/filter settings; large soft sources increase leak risk. Thin single-sided geometry leaks. Document “shadows will differ” without calling EEVEE broken.

Sources:

- https://docs.blender.org/manual/en/5.2/render/eevee/light_settings.html
- https://docs.blender.org/manual/en/5.2/render/eevee/limitations/limitations.html

### Secondary sun / Area / Spot

Secondary sun: second **Sun** lamp (parallel, infinite) matches the “second distant star” model better than Area. Area is fine for soft local fill but **Beam spread** is Cycles-only. Spot softness semantics differ — avoid Spot as the documented EEVEE path for celestial sync.

---

## What OuroSkies should promise vs Cycles-only

### Promise on EEVEE (supported / appreciated)

1. Multiple Scattering (or Single) **atmosphere look** with air / aerosols / ozone / altitude.
2. Place/date **aim** of sky sun direction (`sun_elevation` / `sun_rotation`) matching Cycles.
3. **Synced Sun lamp** (and optional Moon lamp) for direct light + shadows aligned to that aim.
4. World **overlays** for moon / second sun / stars / eclipse **as seen in the sky background**, with artistic Strength/Exposure tuning.
5. Explicit UI copy that EEVEE is supported with documented gaps — not a silent second-class engine.

### Document as Cycles-only or Cycles-stronger

1. Built-in Sky Texture **Sun Disc** contributing to lighting and a sharp visible solar disk from the sky node.
2. Parity of **World-only** outdoor lighting intensity and shadow quality without lamps.
3. Bright World overlays as reliable **scene lights** (moon fill, second sun illumination, star speck lighting).
4. OSL-based sky or overlay tricks.
5. Any claim of “identical to Cycles” for Exposure-normalized frames.

### Recommended EEVEE product shape

- World: Sky Texture `MULTIPLE_SCATTERING`, **`sun_disc` treated as irrelevant / off for EEVEE lighting**, optional **custom** primary sun disk overlay if a visible disc is required in-camera.
- Always-on or strongly recommended: **addon Sun lamp** synced to sky aim; optional Moon lamp.
- Overlays: camera-facing celestial decoration + eclipse masks.
- Do not auto-enable World Sun Extraction without documenting conflict with synced lamps.

---

## Spec documentation checklist

Use this as an EEVEE section checklist in the OuroSkies plan/spec (not implementation):

- [ ] **Engine matrix:** Cycles = full baseline; EEVEE = atmosphere + overlays + synced lamps; gaps listed.
- [ ] **Sun Disc:** Mark Cycles-only; cite manual + EEVEE node-support + UI warning; note stale “Nishita” wording means Single/Multiple Scattering.
- [ ] **EEVEE lighting path:** World → internal probe; World counted as **indirect**; precision ≠ Cycles.
- [ ] **Required EEVEE daylight path:** Synced **Sun** light for direction, Strength, Angle, shadows.
- [ ] **Optional Moon lamp:** Strength order-of-magnitude (~0.001 W/m²) from Blender light manual; aim from lunar ephemeris research.
- [ ] **Sun Extraction policy:** Prefer Threshold = 0 when addon owns the sun; document double-sun risk.
- [ ] **Sky `sun_intensity` / `sun_size`:** Cycles disc knobs; on EEVEE remap UX to lamp Strength/Angle or hide.
- [ ] **Custom overlays:** Supported for **visible** sky; not promised as EEVEE scene lights; stars decorative-only.
- [ ] **Eclipse:** World look + lamp dimming/visibility on EEVEE; not World-disc occlusion alone.
- [ ] **Light limitations to name:** No light node trees; Area Beam spread unsupported; Spot size ≠ softness; Sun has no Custom Distance.
- [ ] **Exposure:** Multiple/Single Scattering physically bright — Color Management Exposure (and/or Background Strength) required both engines; EEVEE indirect clamp can further tame World.
- [ ] **Probe resolution:** Mention World Light Probe Resolution as an EEVEE quality knob for sky lighting gradients.
- [ ] **Half-float / clamp:** Note possible highlight mismatch vs Cycles for extreme World values.
- [ ] **No World Volume** atmosphere (locked); EEVEE volume limits reinforce that choice.
- [ ] **Marketing language:** “Appreciated on EEVEE” / “Cycles-first fidelity” — never “parity.”
- [ ] **QA acceptance:** Side-by-side stills — atmosphere hue OK; sun disk + hard shadows may only match when EEVEE uses synced lamp; World-only EEVEE shot is allowed to look softer/dimmer.
- [ ] **Docs lag tracker:** File/follow upstream if node-support still says “Nishita mode” after Single/Multiple rename.

---

## Open questions

1. **Custom primary sun disk overlay on EEVEE:** Should the spec require a node-group disk (camera) whenever engine is EEVEE, or accept “no visible sun disk until user enables lamp-only / extraction”? Needs a product call; technically both work.
2. **Sun Extraction auto-tune:** Can Threshold be derived from Sky Texture brightness safely, or is it too scene-dependent to automate?
3. **Viewport vs final EEVEE:** Jittered soft shadows “aren’t visible by default in the viewport” (EEVEE light settings) — does the addon warn that viewport sun softness ≠ F12?
4. **Second sun extraction:** If two bright World disks exist, which direction does Sun Extraction pick? Spec should assume **unsafe** for binary-sun Worlds and prefer dual addon Sun lamps.
5. **Material Preview / LookDev:** Same EEVEE probe stack — confirm addon “EEVEE supported” includes Material Preview expectations.
6. **GPU LUT resolution (`GPU_SKY_WIDTH` / `HEIGHT`):** Exact texel density vs Cycles evaluation — confirm whether very high altitudes or sharp horizon features differ enough to mention in QA (source-defined constants; not re-specified here).
7. **Upstream doc fix:** Node-support “Nishita mode” string vs UI “Sun disc not available in EEVEE” for all Single/Multiple — track for 5.2.x/5.3 manual accuracy.

---

## Primary sources index

| Source | URL / path |
|---|---|
| Sky Texture (5.2) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/sky.html |
| ShaderNodeTexSky API (5.2) | https://docs.blender.org/api/5.2/bpy.types.ShaderNodeTexSky.html |
| World Environment (5.2) | https://docs.blender.org/manual/en/5.2/render/lights/world.html |
| Background shader (5.2) | https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/background.html |
| Light Objects (5.2) | https://docs.blender.org/manual/en/5.2/render/lights/light_object.html |
| EEVEE World Settings (probe / sun extraction) | https://docs.blender.org/manual/en/5.2/render/eevee/world_settings.html |
| EEVEE Supported Nodes | https://docs.blender.org/manual/en/5.2/render/eevee/limitations/nodes_support.html |
| EEVEE Limitations | https://docs.blender.org/manual/en/5.2/render/eevee/limitations/limitations.html |
| EEVEE Light Settings | https://docs.blender.org/manual/en/5.2/render/eevee/light_settings.html |
| EEVEE Light Paths (clamp / intensity) | https://docs.blender.org/manual/en/5.2/render/eevee/render_settings/light_paths.html |
| EEVEE Light Probes index | https://docs.blender.org/manual/en/5.2/render/eevee/light_probes/index.html |
| 5.0 Rendering release notes | https://developer.blender.org/docs/release_notes/5.0/rendering/ |
| 5.0 product notes (sky in Cycles + EEVEE) | https://www.blender.org/download/releases/5-0/ |
| D13522 EEVEE Nishita (disc deferred; LUT) | https://archive.blender.org/developer/differential/0013/0013522/D13522.html |
| Sky node UI / GPU (5.2-release) | `source/blender/nodes/shader/nodes/node_shader_tex_sky.cc` |
| GPU sky GLSL | `source/blender/gpu/shaders/material/gpu_shader_material_tex_sky.glsl` |
| Cycles sky SVM (sun disc) | `intern/cycles/kernel/svm/sky.h` |
| Prior: atmosphere options | `/home/ouro/ouroskies/docs/research/cycles-world-sky-atmosphere-options.md` |
| Prior: sun/moon aiming | `/home/ouro/ouroskies/docs/research/sun-moon-aiming-and-eclipse-timing.md` |
