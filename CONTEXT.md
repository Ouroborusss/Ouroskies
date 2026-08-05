# OuroSkies

A Blender extension that builds physically grounded skies (atmosphere, suns, moon, stars) primarily through the World shader, with an N-panel cockpit and optional synced lamps.

## Language

**OuroSkies**:
The Blender extension (addon) this effort specifies.
_Avoid_: Physical Sky, Atmos Sky, the sky addon

**World sky**:
The Blender World shader graph that produces environment lighting and the visible sky dome.
_Avoid_: skybox, sky box, environment map (unless meaning an HDRI asset)

**Primary sun**:
The main solar disk in the World sky, whose direction is driven by place/date (or manual override).
_Avoid_: the sun (when binary mode is on), sun lamp (that's a lamp)

**Secondary sun**:
An artist-posed second sun disk in the World sky (binary look), parented to the primary via angular separation + orbit angle — not real binary orbital mechanics. World-shader overlay only (no second lamp / mesh). Size, strength, and color live under Celestials.
_Avoid_: binary star, companion star (astronomy sense); second sun lamp

**Moon disk**:
A textured mesh disk the extension aims with the moon (Manual antipode or place/date). Size lives under Celestials; optional moon lamp for fill. Not a World-shader overlay.
_Avoid_: moon (when meaning the lamp); World-node moon

**Sun lamp / Moon lamp**:
Optional Blender lights the extension creates and aims in sync with the World sky disks.
_Avoid_: sun, moon (when meaning the disk in the sky)

**Place/date**:
Latitude, longitude, and date/time (timezone or UTC) used to aim the primary sun and moon; evaluation canonicalizes to UTC. Freely changeable to any place/time; Python owns per-frame evaluation into the World sky and lamps. Stored on the Scene with other cockpit settings.
_Avoid_: GPS, ephemeris (implementation detail), location alone

**Azimuth / altitude**:
Horizontal angles for celestial aim — azimuth eastward from north, altitude from horizon — mapped into Blender with +Y north, +Z up (+X east).
_Avoid_: bearing (ambiguous), sun rotation (Sky Texture property, not the angle itself)

**Aim mode**:
Cockpit choice between Manual (default) and Place/Date for primary sun and moon direction. Secondary sun is always manual.
_Avoid_: automatic-only aiming

**Aim refraction**:
Cockpit toggle between Apparent (horizon lift for prettier sunrise/set) and Geometric (true direction). Default Apparent; eclipse math always uses Geometric. UI notes when the two diverge near the horizon.
_Avoid_: silent-only refraction, no-toggle refraction

**Airglow**:
A soft World-shader night-sky fill behind stars and the Milky band (no volumes); strength fades with daylight; default subtle cool/green-grey with an artistic tint control.
_Avoid_: volumetric fog, neon aurora (unless artist pushes tint)

**Milky band**:
An optional procedural soft glow in the night sky suggesting a galactic band — looks-only, not catalog-based; togglable in the cockpit.
_Avoid_: Milky Way survey, Gaia, star catalog

**Nishita-class**:
The accuracy bar: Blender’s Multiple Scattering Sky Texture lineage (air / aerosols / ozone) with known limits — not full path-traced atmosphere.
_Avoid_: physically perfect, photoreal guarantee, Preetham, Hosek/Wilkie (legacy)

**Physically Accurate preset**:
An overridable cockpit preset that sets sky / sun / moon energies toward real-world brightness targets, resets World Contribution to neutral, and resets White Balance to Daylight; diverging then re-applying restores those. Does not reset Air / Dust / Ozone / Altitude; does not drive Exposure.
_Avoid_: locked physical mode, photoreal guarantee

**White balance**:
A Looks control (Kelvin + presets) that tints the World sky and synced lamps after scatter; default Daylight ~6500K. Physically Accurate re-apply resets WB to Daylight.
_Avoid_: Ozone (scatter blue), Exposure (view brightness)

**World contribution**:
How hard the OuroSkies World lights the scene (materials / GI), separate from Sky Strength (visible backdrop) and Exposure (view). Physically Accurate re-apply resets it to a neutral default.
_Avoid_: Sky Strength, Exposure, Sun Punch

**Rebuild Sky Graph**:
A cockpit action that restores the canonical OuroSkies World node layout from current settings; hand node edits are unsupported.
_Avoid_: per-frame node rebuild

**OuroSkies World**:
A dedicated World datablock the extension creates and switches the scene to while active; on detach the scene returns to the previous World and the OuroSkies World is deleted.
_Avoid_: in-place overwrite of the user’s existing World (unsupported)

**Detach / Remove OuroSkies**:
Graceful teardown: switch scene back to the previous World, delete the OuroSkies World, stop handlers/drivers. Lamps are removed via an explicit remove control (pair to add), not left orphaned by default.
_Avoid_: silent uninstall with orphaned drivers; mass-deleting unmarked lights

**Dust**:
OuroSkies N-panel label for Sky Texture `aerosol_density` (haze / pollution / water droplets). End-user descriptions explain the binding.
_Avoid_: Aerosols (Blender RNA name — OK in tooltips), turbidity

**Distance Haze**:
Non-volume aerial perspective on scene meshes: a material node group that keeps surfaces opaque and blends toward a **baked** sky color (atmosphere + white balance EXR sequence, sampled by view direction) by camera distance. Cockpit **Haze** section owns bake/cache; Near/Far/Opacity live on the group. Not volumetric fog.
_Avoid_: Transparent mix for strength, live Sky Texture in every material, World Volume fog

**Eclipse look**:
A timed, arc-correct sun/moon overlap presentation: geometric disk occlusion always; optional artistic Eclipse Effects (corona, sky dim, sun-lamp dim, Bailey’s beads, diamond ring) that may be faked. Does not drive the Exposure convenience slider.
_Avoid_: astronomical eclipse simulation (full precision)
