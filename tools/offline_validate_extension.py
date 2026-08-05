#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline checklist for ouroskies/blender_manifest.toml when Blender CLI is unavailable.

Mirrors required rules from Blender 5.2 Extension schema 1.0.0 / packaging research.
Exit 0 = pass. Not a substitute for ``blender --command extension validate``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    print("Python 3.11+ with tomllib required", file=sys.stderr)
    sys.exit(2)

REQUIRED = {
    "schema_version",
    "id",
    "version",
    "name",
    "tagline",
    "maintainer",
    "type",
    "blender_version_min",
    "license",
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
PUNCT_END = re.compile(r"[.!?]$")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    root = repo / "ouroskies"
    manifest_path = root / "blender_manifest.toml"
    init_path = root / "__init__.py"

    if not manifest_path.is_file():
        fail(f"missing {manifest_path}")
    if not init_path.is_file():
        fail(f"missing {init_path}")

    text = init_path.read_text(encoding="utf-8")
    if re.search(r"^bl_info\s*=", text, re.M):
        fail("__init__.py must not define bl_info")

    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    missing = REQUIRED - data.keys()
    if missing:
        fail(f"missing required fields: {sorted(missing)}")

    for key, value in data.items():
        if value == "" or value == []:
            fail(f"optional/required field must not be empty: {key}")

    if data["schema_version"] != "1.0.0":
        fail(f"schema_version must be 1.0.0, got {data['schema_version']!r}")
    if data["type"] != "add-on":
        fail(f"type must be add-on, got {data['type']!r}")
    if not SEMVER.match(str(data["version"])):
        fail(f"version must be semver X.Y.Z, got {data['version']!r}")
    tagline = data["tagline"]
    if len(tagline) > 64:
        fail(f"tagline > 64 chars ({len(tagline)})")
    if PUNCT_END.search(tagline):
        fail("tagline must not end with punctuation")
    licenses = data["license"]
    if not isinstance(licenses, list) or not all(
        isinstance(x, str) and x.startswith("SPDX:") for x in licenses
    ):
        fail("license must be a list of SPDX:… strings")
    if "SPDX:GPL-3.0-or-later" not in licenses:
        fail("expected SPDX:GPL-3.0-or-later")
    if data.get("id") != "ouroskies":
        fail(f"id must be ouroskies, got {data.get('id')!r}")
    if data.get("blender_version_min") != "5.2.0":
        fail(f"blender_version_min must be 5.2.0, got {data.get('blender_version_min')!r}")

    print("PASS: offline Extension checklist OK")
    print(f"  package: {root}")
    print(f"  id={data['id']} version={data['version']} blender_min={data['blender_version_min']}")
    print("  Reminder: run `blender --command extension validate` in this folder on a Blender 5.2 machine")


if __name__ == "__main__":
    main()
