# OuroSkies

Physically grounded skies for Blender Worlds — atmosphere, suns, moon, stars, and timed eclipse looks, driven from an N-panel cockpit.

**Status:** Spec and research are in-repo; the Extension package is not implemented yet.  
**Blender:** 5.2+  
**License:** [GPL-3.0-or-later](LICENSE)  
**Maintainer:** [Ouroborusss](https://github.com/Ouroborusss)

## Install (when a build exists)

1. Download the Extension zip from Releases (or build with Blender’s `extension build`).
2. In Blender: **Edit → Preferences → Extensions → Install from Disk**.
3. Enable **OuroSkies**.

Offline Install from Disk does not receive remote updates. Packaging and remote-repo notes: [`docs/research/extension-packaging-and-remote-repos.md`](docs/research/extension-packaging-and-remote-repos.md).

## Documentation

| Doc | Role |
|---|---|
| [`docs/ouroskies-spec.md`](docs/ouroskies-spec.md) | Build-ready product specification |
| [`CONTEXT.md`](CONTEXT.md) | Domain glossary (ubiquitous language) |
| [`docs/research/`](docs/research/) | Background research (Cycles sky, aiming, EEVEE gaps, packaging, PA2 inspiration checklist) |
| [`docs/prototypes/`](docs/prototypes/) | N-panel IA and star-field look stubs |

## Scope (short)

**In:** Nishita-class Multiple Scattering World sky, place/date or Manual aim, secondary artist-posed sun, moon disk, procedural stars, optional synced lamps, eclipse looks.  
**Out:** Clouds, volumetric fog, planets, reverse-engineering paid addons.

See the [spec](docs/ouroskies-spec.md) for the full contract.

## Development

Extension package: [`ouroskies/`](ouroskies/) (`blender_manifest.toml` + `__init__.py`; Blender `id` = `ouroskies`). No `bl_info`.

Offline manifest checklist (no Blender required):

```bash
python3 tools/offline_validate_extension.py
```

On a Blender 5.2 machine, also run:

```bash
cd ouroskies && blender --command extension validate
```

Smoke-testing: Install from Disk or symlink the `ouroskies/` folder into the extensions path.
