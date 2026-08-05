# Blender 5.2 Extension packaging & remote repos (OuroSkies)

**Question:** What is the Blender 5.2 Extension packaging shape for OuroSkies (`blender_manifest.toml`, `bl_info`/legacy coexistence, zip install, remote-repository install/update), and what must the build-ready spec require so shipping later is mechanical rather than rediscovered?

**Scope:** Plan/spec research only. Target Blender **5.2** on Windows (portable design). Standing preference: Extension system (remote-repo install/update) as primary packaging; zip offline install still works. Do not implement the addon.

---

## Verdict

**Ship OuroSkies as a Blender Extension add-on (`type = "add-on"`) with a root `blender_manifest.toml` (schema `1.0.0`), not as a legacy `bl_info` add-on.** Build the distributable with `blender --command extension build` into `{id}-{version}.zip`; validate with `extension validate`. Prefer **remote repository** (official [extensions.blender.org](https://extensions.blender.org/) *or* a self-hosted static `index.json`) so users get install + update; keep the same `.zip` usable via **Install from Disk** for offline (local repo — **no automatic updates**).

**`bl_info` is not part of the Extension packaging shape.** Official conversion guidance: put metadata in the manifest and **remove** `bl_info`. Legacy add-ons remain installable in 5.2 but are deprecated and cannot use the Extensions update path.

**For official-platform publishing:** add-on license must be **GNU GPL v3.0 or later** (`SPDX:GPL-3.0-or-later`); bundled add-on assets must be **Public Domain (CC0)**. Self-hosted repos are not bound by that platform rule, but the manifest still requires SPDX `license` entries, and Blender’s add-on guidelines remain best practice everywhere.

---

## Packaging shape

### What an Extension package is

An extension is a **`.zip` archive** containing a manifest plus type-specific files. For an add-on, the minimum is `blender_manifest.toml` + `__init__.py` (plus any other modules/wheels). Files may sit at the zip root **or** inside one top-level folder (common when exporting a VCS repo as ZIP).

Sources:

- https://docs.blender.org/manual/en/5.2/advanced/extensions/getting_started.html

Canonical layout (from the 5.2 manual):

```text
my_extension-0.0.1.zip
├─ __init__.py
├─ blender_manifest.toml
└─ (...)
```

### `blender_manifest.toml` (schema 1.0.0)

**Filename is mandatory:** `blender_manifest.toml`. Schema version for 5.2 remains **`1.0.0`** (developer schema docs + 5.2 manual).

#### Required fields

| Field | Rule (5.2 / schema 1.0.0) |
|---|---|
| `schema_version` | `"1.0.0"` |
| `id` | Unique extension id (stable; used by repos/API) |
| `version` | **Semantic versioning** (e.g. `"1.0.0"`) |
| `name` | Display name |
| `tagline` | One-line description; **≤64 chars**; **must not end with punctuation** |
| `maintainer` | Maintainer string (may include email) |
| `type` | `"add-on"` (or `"theme"`) |
| `blender_version_min` | At least `"4.2.0"`; OuroSkies should set **`"5.2.0"`** if that is the supported floor |
| `license` | List of SPDX ids with `SPDX:` prefix |

#### Optional fields (omit entirely if unused — empty `""` / `[]` are invalid)

| Field | Notes |
|---|---|
| `blender_version_max` | Exclusive upper bound (“does not support”); can also be set later on the platform |
| `website` | Docs / project / platform page |
| `copyright` | `"Year Name"` or `"Year-Year Name"`; required by some licenses |
| `tags` | From the official add-on tag list only (when validating against platform tags) |
| `platforms` | `windows-x64`, `windows-arm64`, `macos-x64`, `macos-arm64`, `linux-x64`; omit = all |
| `wheels` | Relative paths to `*.whl` (convention: `./wheels/...`; forward slashes) |
| `[permissions]` | `files`, `network`, `clipboard`, `camera`, `microphone` → short reason (≤64 chars, no trailing period) |
| `[build]` | `paths` **or** `paths_exclude_pattern` (gitignore-style); default excludes `__pycache__/`, `.git`, `*.zip` |

**Reserved:** do not author `[build.generated]` in source manifests (added by `--split-platforms` builds).

Sources:

- https://docs.blender.org/manual/en/5.2/advanced/extensions/getting_started.html
- https://developer.blender.org/docs/features/extensions/schema/1.0.0/

### Build / validate CLI (mechanical shipping)

```bash
blender --command extension validate
blender --command extension build
# optional, when bundling platform-specific wheels:
blender --command extension build --split-platforms
```

Default output zip name: `{id}-{version}.zip`. Validate also accepts an already-built zip.

Source: https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html

### Folder / wheels / permissions / tags / licenses

**Wheels**

- Place under `./wheels/` by convention.
- Bundle unmodified wheels from PyPI; include dependencies; filenames must match Python wheel binary-distribution naming.
- List paths in `wheels = [...]` with forward slashes.
- Binary wheels: download per target platform / Python ABI matching Blender’s bundled Python; use `--split-platforms` so each zip only carries its platforms’ wheels.
- Official add-on guidelines: **do not** runtime-install pip/wheels; bundle them or require the user to run external software.

Sources:

- https://docs.blender.org/manual/en/5.2/advanced/extensions/python_wheels.html
- https://developer.blender.org/docs/handbook/extensions/addon_guidelines/

**Permissions**

Declare only what OuroSkies actually needs, with a short reason. If `network` is declared, also respect `bpy.app.online_access` (and optionally `bpy.app.online_access_override` for better messaging).

Sources:

- https://docs.blender.org/manual/en/5.2/advanced/extensions/getting_started.html
- https://docs.blender.org/manual/en/5.2/advanced/extensions/addons.html

**Tags (add-ons)**

Platform-supported tags include (non-exhaustive relative to OuroSkies relevance): `Lighting`, `Render`, `Scene`, `Camera`, `3D View`, `Animation`, `Pipeline`, … Full list: https://docs.blender.org/manual/en/5.2/advanced/extensions/tags.html

**Licenses (official Extensions Platform)**

- Add-ons: **GPL-3.0 or later** required.
- Themes: GPL recommended; any GPL-compatible allowed.
- Assets used in add-ons: **Public Domain (CC0)** required.

Source: https://docs.blender.org/manual/en/5.2/advanced/extensions/licenses.html

### Code-shape requirements (not just the zip)

Beyond the manifest, Extension add-ons should:

1. **Remove `bl_info`** — metadata lives in the manifest.
2. Use **`__package__`** for `AddonPreferences.bl_idname` and preference lookups (never hard-code the module name). Runtime module path is `bl_ext.{repository_module_name}.{id}`.
3. Use **relative imports** inside the package (`from . import utils`).
4. Be **self-contained** (wheels / vendored modules in package namespace).
5. **Not write into the install directory** (System/read-only repos). Use:
   `bpy.utils.extension_path_user(__package__, path="", create=True)` for persistent user data (kept across upgrades; removed on uninstall).
6. Not manipulate other add-ons’ install/update/remove; not mutate global `sys.path` / module dict outside the package namespace.

Source: https://docs.blender.org/manual/en/5.2/advanced/extensions/addons.html  
Guidelines: https://developer.blender.org/docs/handbook/extensions/addon_guidelines/

---

## Remote repositories

### Two hosting models

| Model | What you host | How users get updates | Fit for OuroSkies |
|---|---|---|---|
| **Official platform** | Upload `.zip` to extensions.blender.org (Blender ID; moderation). Updates via platform API / CI | Blender’s default remote repo | Best if product can be GPL + pass guidelines |
| **Self-hosted static** | Directory of `.zip` files + generated `index.json` (optional `index.html`) on any static HTTP(S) or even `file://` | User adds remote repo URL → Refresh / Update | Best for private/commercial or pre-publish; primary path if not on platform yet |
| **Self-hosted dynamic** | Same listing API, but server filters by `?blender_version=&platform=` | Same as remote | Only needed for large multi-version catalogs; official docs recommend **static** for small/personal repos |

Sources:

- https://docs.blender.org/manual/en/5.2/advanced/extensions/creating_repository/static_repository.html
- https://docs.blender.org/manual/en/5.2/advanced/extensions/creating_repository/dynamic_repository.html
- https://docs.blender.org/manual/en/5.2/editors/preferences/extensions.html

### Authoring a static remote repo

```bash
# Place built packages in a directory, then:
blender --command extension server-generate --repo-dir=/path/to/packages
# optional browse page:
blender --command extension server-generate --repo-dir=/path/to/packages --html
```

Produces **`index.json`** listing all zips (Listing API **v1**). Optional `blender_repo.toml` can define a **blocklist**.

User adds remote: **Get Extensions → Repositories → [+] → Add Remote Repository**, URL = path to JSON, e.g.:

- Linux/macOS: `file:///path/to/packages/index.json`
- Windows: `file:///C:/path/to/packages/index.json`
- Production: `https://example.com/ouroskies-repo/index.json`

Listing API shape (`version`, `blocklist`, `data[]` with archive URL/hash/size + manifest fields): https://developer.blender.org/docs/features/extensions/api_listing/v1/

Example official listing endpoint: https://extensions.blender.org/api/v1/extensions/

### Install / update UX expectations

- Users **manually check** for updates (Refresh Remote), unless the remote repo has **Check for Updates on Startup** enabled (notification on status bar).
- Available repo version is treated as **latest**.
- **Update All** / per-extension update installs newer packages from the remote.
- Drag-and-drop install URLs for `.zip` may include query params (`repository`, `blender_version_min`, `platforms`, …); download URL must end in `.zip`.

CLI equivalents: `extension sync`, `extension update`, `extension install`, `extension repo-add --url …`.

Sources:

- https://docs.blender.org/manual/en/5.2/editors/preferences/extensions.html
- https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html

### Official platform publish / versioning flow

1. Build + **Install from Disk** smoke test.
2. Upload `.zip` (Blender ID); held for **moderation**, then published.
3. Later versions: bump semver in manifest, rebuild, upload again — or automate:

```bash
curl -X POST https://extensions.blender.org/api/v1/extensions/$EXTENSION/versions/upload/ \
  -H "Authorization:bearer $BLENDER_EXTENSIONS_TOKEN" \
  -F "version_file=@$FILENAME" \
  -F "release_notes=$RELEASE_NOTES"
```

Token from the extensions platform user profile. `$EXTENSION` = extension **id**.

Sources:

- https://docs.blender.org/manual/en/5.2/advanced/extensions/getting_started.html
- https://developer.blender.org/docs/features/extensions/ci_cd/

### Self-hosted update flow (mechanical)

1. Bump `version` in `blender_manifest.toml` (semver).
2. `extension validate` + `extension build` → new zip into the repo directory (keep or replace older zips per policy; static generate indexes what’s on disk).
3. Re-run `extension server-generate --repo-dir=…`.
4. Publish directory (HTTPS static hosting).
5. Clients: Refresh Remote → Update.

---

## Zip path (offline / Install from Disk)

- **Install from Disk** (Get Extensions or Add-ons UI) or drag-and-drop `.zip` into Blender.
- Installed into a **Local Repository**.
- Manual docs are explicit: **no updates will be available** for disk-installed packages (until/unless the same extension is obtained from a remote repo workflow — treat remote as the update channel).
- Still the recommended **pre-publish test** path (“as close to the final experience as possible”).
- CLI: `blender --command extension install-file -r <repo_id> <file.zip>`

Same zip artifact serves both offline install and remote-repo hosting; do not maintain a separate “legacy zip” shape for OuroSkies shipping.

Sources:

- https://docs.blender.org/manual/en/5.2/editors/preferences/extensions.html
- https://docs.blender.org/manual/en/5.2/editors/preferences/addons.html
- https://docs.blender.org/manual/en/5.2/advanced/extensions/addons.html

---

## `bl_info` coexistence

| Mode | Metadata | Status in 5.2 | Updates |
|---|---|---|---|
| **Extension add-on** | `blender_manifest.toml` only | **Primary / supported** | Via remote repository |
| **Legacy add-on** | `bl_info` in `__init__.py` | Still installable; **deprecated** since 4.2 | No Extensions platform update path |

Official conversion steps: create manifest → **remove `bl_info`** → `__package__` + relative imports → wheels for deps → test via Install from Disk.

**Spec implication for OuroSkies:** do **not** dual-ship `bl_info` + manifest as the supported product shape. One Extension package; no legacy packaging track unless a temporary internal-dev Script Directory workflow is needed (out of shipping scope).

Source: https://docs.blender.org/manual/en/5.2/advanced/extensions/addons.html

---

## Spec checklist (build-ready requirements)

The OuroSkies build-ready spec should mandate:

1. **Packaging type:** Blender Extension `type = "add-on"`; not legacy-only.
2. **Manifest file:** root `blender_manifest.toml` with `schema_version = "1.0.0"` and all required fields filled; no empty optionals.
3. **Stable `id`:** choose once (e.g. `ouroskies`); never rename casually (repos/API/CI keys off it).
4. **Semver `version`:** single source of truth in the manifest; release process bumps it before build.
5. **`blender_version_min`:** `"5.2.0"` (or documented wider range if intentionally supporting older 4.2+).
6. **`platforms`:** either omit (all) or explicitly list; Windows primary (`windows-x64`, and `windows-arm64` if claimed).
7. **License policy:** decide **official platform vs self-hosted**. If platform: `license = ["SPDX:GPL-3.0-or-later"]`, add-on assets CC0, pass add-on guidelines. If self-hosted only: still declare SPDX licenses in the manifest; document divergence.
8. **No `bl_info`** in shipped `__init__.py`.
9. **Namespace rules:** `AddonPreferences.bl_idname = __package__`; relative imports; no hard-coded package string.
10. **User data path:** use `bpy.utils.extension_path_user(__package__, …)`; never write into the extension install tree.
11. **Permissions:** declare `[permissions]` only for real needs; gate network on `bpy.app.online_access`.
12. **Dependencies:** pure-Python vendored **or** wheels under `./wheels/` listed in manifest; no runtime pip; use `--split-platforms` if binary wheels bloat the zip.
13. **Tags:** only from the official add-on tag list when targeting the platform / default validators.
14. **Build commands:** CI/release must run `extension validate` then `extension build` (document Blender 5.2 binary path on the build agent).
15. **Artifacts:** ship `{id}-{version}.zip` as the only installable unit.
16. **Offline path:** document Install from Disk / drag-drop; accept “no updates” for that path.
17. **Remote path (primary):** document either (A) extensions.blender.org upload + token CI, or (B) static repo: drop zips → `server-generate` → host `index.json` → user adds remote URL; optional `--html`.
18. **Update path:** bump semver → rebuild → publish to remote → users Refresh/Update (optionally Check for Updates on Startup).
19. **Smoke test gate:** Install from Disk on clean Blender 5.2 Windows before any remote publish.
20. **Guidelines compliance** (even if self-hosted): online_access, self-contained, no interfering with other add-ons, System-install safe — https://developer.blender.org/docs/handbook/extensions/addon_guidelines/

---

## Open questions

1. **Distribution channel:** publish on **extensions.blender.org** (implies GPL + moderation + CC0 assets) vs **self-hosted static repo only** (or both: GPL public channel + private staging repo)?
2. **Exact `id` / `name` / `tagline` / `maintainer` / `website` strings** for the manifest (product branding vs technical id).
3. **Will OuroSkies need wheels** (e.g. Skyfield/NumPy) or stay pure-Python? If wheels: pin Blender 5.2’s bundled CPython ABI and decide `--split-platforms` matrix.
4. **Permissions set:** files-only vs network (ephemeris download, update checks outside Blender’s repo sync, etc.).
5. **`blender_version_max`:** leave unset until a known break, or pin an exclusive ceiling intentionally?
6. **Repo policy for static hosting:** keep multiple historical zips in `index.json` vs only latest (static generate indexes all zips present).
7. **Access tokens:** will any OuroSkies remote require Authorization Bearer tokens (dynamic/private repos)?

---

## Primary sources

- How to Create Extensions (5.2): https://docs.blender.org/manual/en/5.2/advanced/extensions/getting_started.html
- Manifest schema 1.0.0: https://developer.blender.org/docs/features/extensions/schema/1.0.0/
- Extension add-ons / legacy conversion: https://docs.blender.org/manual/en/5.2/advanced/extensions/addons.html
- Get Extensions preferences (install/update/repos): https://docs.blender.org/manual/en/5.2/editors/preferences/extensions.html
- Add-ons preferences (Install from Disk / legacy): https://docs.blender.org/manual/en/5.2/editors/preferences/addons.html
- Static remote repository: https://docs.blender.org/manual/en/5.2/advanced/extensions/creating_repository/static_repository.html
- Dynamic remote repository: https://docs.blender.org/manual/en/5.2/advanced/extensions/creating_repository/dynamic_repository.html
- Listing API v1: https://developer.blender.org/docs/features/extensions/api_listing/v1/
- Extension CLI: https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html
- Licenses: https://docs.blender.org/manual/en/5.2/advanced/extensions/licenses.html
- Tags: https://docs.blender.org/manual/en/5.2/advanced/extensions/tags.html
- Python wheels: https://docs.blender.org/manual/en/5.2/advanced/extensions/python_wheels.html
- Add-on guidelines (extensions.blender.org): https://developer.blender.org/docs/handbook/extensions/addon_guidelines/
- Platform CI/CD upload API: https://developer.blender.org/docs/features/extensions/ci_cd/
