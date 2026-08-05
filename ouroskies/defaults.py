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

# provisional: ~Blender default elevation (~15°); azimuth 90° east so
# sunrise-toward-+X checks are one click away (sun_rotation = -az pending verify).
MANUAL_SUN_ELEVATION_DEG = 15.0
MANUAL_SUN_AZIMUTH_DEG = 90.0

# provisional: NYC-ish defaults for place/date smoke tests.
PLACE_LATITUDE = 40.7128
PLACE_LONGITUDE = -74.0060
PLACE_TIMEZONE = "America/New_York"
PLACE_YEAR = 2026
PLACE_MONTH = 8
PLACE_DAY = 4
PLACE_TIME_HOURS = 12.0

# provisional: photography-ish Kelvin presets; Daylight locked ~6500K.
WB_DAYLIGHT_KELVIN = 6500.0
WB_CLOUDY_KELVIN = 7500.0
WB_SHADE_KELVIN = 8000.0
WB_WARM_KELVIN = 4500.0

# provisional: unity strengths as neutral; PA restores these (lamps later).
SKY_STRENGTH = 1.0
WORLD_CONTRIBUTION = 1.0
PA_SKY_STRENGTH = 1.0
PA_WORLD_CONTRIBUTION = 1.0

# provisional: modest cool green-grey night fill; fades -6°…+6° sun elev.
AIRGLOW_STRENGTH = 0.03
AIRGLOW_TINT = (0.55, 0.65, 0.60, 1.0)
AIRGLOW_FADE_LOW_DEG = -6.0
AIRGLOW_FADE_HIGH_DEG = 6.0

EXPOSURE = 0.0

# provisional: lamp energies / angle; PA sets these when lamps exist.
SUN_LAMP_NAME = "OuroSkies Sun Lamp"
MOON_LAMP_NAME = "OuroSkies Moon Lamp"
LAMP_OWNED_KEY = "ouroskies_owned_lamp"
LAMP_KIND_KEY = "ouroskies_lamp_kind"
LAMP_DISTANCE = 1000.0
SUN_LAMP_ENERGY = 4.0
MOON_LAMP_ENERGY = 0.05
PA_SUN_LAMP_ENERGY = 4.0
PA_MOON_LAMP_ENERGY = 0.05
SUN_LAMP_ANGLE_RAD = 0.00918043  # ~0.526° — near solar angular diameter
WORLD_SUN_THRESHOLD_DEFAULT = 10.0

WORLD_NAME = "OuroSkies"
WORLD_OWNED_KEY = "ouroskies_owned"
NODE_SKY = "OuroSkies Sky"
NODE_WB_MIX = "OuroSkies WB Mix"
NODE_WB_COLOR = "OuroSkies WB Color"
NODE_BG_CAMERA = "OuroSkies BG Camera"
NODE_BG_LIGHT = "OuroSkies BG Light"
NODE_LIGHT_PATH = "OuroSkies Light Path"
NODE_MIX_CAMERA = "OuroSkies Mix Camera"
NODE_AIRGLOW_COLOR = "OuroSkies Airglow Color"
NODE_BG_AIRGLOW = "OuroSkies BG Airglow"
NODE_ADD_AIRGLOW = "OuroSkies Add Airglow"
NODE_OUTPUT = "OuroSkies Output"
# Back-compat alias used by older comments
NODE_BACKGROUND = NODE_BG_CAMERA
