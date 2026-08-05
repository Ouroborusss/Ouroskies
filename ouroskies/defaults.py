# SPDX-License-Identifier: GPL-3.0-or-later

"""Provisional numeric defaults — marked until research tickets harden them.

Convention: values live here with ``# provisional:`` rationale; Scene props use
these as ``default=``. Research may replace numbers without renaming keys.
"""

from __future__ import annotations

# provisional: Blender 5.2 ShaderNodeTexSky Multiple Scattering factory defaults
# (urban-ish 1.0 densities, 100 m altitude). Reset Atmosphere restores these.
ATMOSPHERE = {
    "air": 1.0,
    "dust": 1.0,
    "ozone": 1.0,
    "altitude": 100.0,
}

WORLD_NAME = "OuroSkies"
WORLD_OWNED_KEY = "ouroskies_owned"
NODE_SKY = "OuroSkies Sky"
NODE_BACKGROUND = "OuroSkies Background"
NODE_OUTPUT = "OuroSkies Output"
