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

# provisional: Manual elevation is a ±180° orbit angle (0 = horizon toward Azimuth).
MANUAL_SUN_ELEVATION_DEG = 0.0
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
AIRGLOW_STRENGTH = 0.02
AIRGLOW_TINT = (0.55, 0.65, 0.60, 1.0)
AIRGLOW_FADE_LOW_DEG = -6.0
AIRGLOW_FADE_HIGH_DEG = 6.0

EXPOSURE = -3.0

# provisional: lamp energies / angle; PA sets these when lamps exist.
SUN_LAMP_NAME = "OuroSkies Sun Lamp"
MOON_LAMP_NAME = "OuroSkies Moon Lamp"
LAMP_OWNED_KEY = "ouroskies_owned_lamp"
LAMP_KIND_KEY = "ouroskies_lamp_kind"
LAMP_DISTANCE = 120.0
SUN_LAMP_ENERGY = 4.0
# provisional: visible night fill without matching daylight sun (was 0.05 — invisible).
MOON_LAMP_ENERGY = 0.4
PA_SUN_LAMP_ENERGY = 4.0
PA_MOON_LAMP_ENERGY = 0.4
SUN_LAMP_ANGLE_RAD = 0.00918043  # ~0.526° — near solar angular diameter
# Fade lamp energy across the horizon (degrees).
LAMP_HORIZON_FADE_DEG = 3.0
WORLD_SUN_THRESHOLD_DEFAULT = 10.0

# provisional: moon disk MUST sit inside default camera clip_end (100).
# Viewport View clip ≠ camera clip — 280 was invisible in Camera view.
MOON_DISK_NAME = "OuroSkies Moon Disk"
MOON_DISK_OWNED_KEY = "ouroskies_moon_disk"
MOON_DISK_DISTANCE = 50.0
MOON_ANGULAR_DIAMETER_DEG = 1.5
# provisional: compete with Multiple Scattering + Exposure −3 without crushing texture.
MOON_DISK_EMISSION = 15.0
MOON_DISK_IMAGE = "moon_disk.png"

# provisional: near Blender Multiple Scattering sun_size (~0.545°) and unity punch.
SUN_SIZE_DEG = 0.545
SUN_PUNCH = 1.0

# provisional: binary sun parented to primary — World look only (no lamp / mesh).
SECONDARY_SUN_ENABLED = False
SECONDARY_SUN_SEPARATION_DEG = 5.0
SECONDARY_SUN_ANGLE_DEG = 0.0
SECONDARY_SUN_SIZE_DEG = 0.545
SECONDARY_SUN_STRENGTH = 80.0
SECONDARY_SUN_COLOR = (1.0, 0.82, 0.55, 1.0)

# provisional: dense fine field (Density drives Voronoi scale); modest Brightness.
STARS_DENSITY = 6.0
STARS_BRIGHTNESS = 0.1
# Milky Band amount: 0 = off, 1 = recipe strength (see MILKY_STRENGTH).
STARS_MILKY_BAND = 1.0
# Voronoi scale at Density=1; bright layer uses a fraction of this.
STARS_VORONOI_SCALE = 95.0
STARS_BRIGHT_SCALE_FRAC = 0.22
STARS_POWER = 14.0
STARS_BRIGHT_POWER = 22.0
STARS_COLOR = (0.92, 0.90, 0.88, 1.0)
# Soft kill before horizon (view Z): full by ~7°, gone by ~1°.
STARS_HORIZON_FULL_Z = 0.12
STARS_HORIZON_ZERO_Z = 0.02
# No Python daylight fade — sky HDR + Exposure bury stars in daytime (ADD overlay).
STARS_USE_DAYLIGHT_FADE = False
STARS_FADE_LOW_DEG = -12.0
STARS_FADE_HIGH_DEG = 2.0
# Milky band look F — mist + dust lanes (prototype lean). Soft plane + noise.
MILKY_PLANE_NORMAL = (0.35, 0.72, 0.60)
MILKY_HALF_WIDTH = 0.18
MILKY_STRENGTH = 0.55
MILKY_COLOR = (0.82, 0.76, 0.70, 1.0)
# Base Noise scales at Milky Noise slider = 1.0
MILKY_NOISE_SCALE = 3.5
MILKY_LANE_SCALE = 8.4
MILKY_CLUMP_SCALE = 1.9
MILKY_DUST_SCALE = 48.0
MILKY_LANE_AMOUNT = 0.65
# User slider default (multiplies the base scales above).
STARS_MILKY_NOISE = 1.0

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
# Procedural stars + Milky band (camera-path overlay after airglow)
NODE_STAR_GEO = "OuroSkies Star Geo"
NODE_STAR_VIEW = "OuroSkies Star View"
NODE_STAR_NORMALIZE = "OuroSkies Star Norm"
NODE_STAR_VORONOI = "OuroSkies Star Voronoi"
NODE_STAR_VORONOI_BRIGHT = "OuroSkies Star Voronoi Bright"
NODE_STAR_SCALE = "OuroSkies Star Scale"
NODE_STAR_SCALE_BRIGHT = "OuroSkies Star Scale Bright"
NODE_STAR_POWER = "OuroSkies Star Power"
NODE_STAR_POWER_BRIGHT = "OuroSkies Star Power Bright"
NODE_STAR_INV = "OuroSkies Star Inv"
NODE_STAR_INV_BRIGHT = "OuroSkies Star Inv Bright"
NODE_STAR_ADD = "OuroSkies Star Layers"
NODE_STAR_HORIZON = "OuroSkies Star Horizon"
NODE_STAR_HORIZON_SEP = "OuroSkies Star Horizon Sep"
NODE_STAR_FADE = "OuroSkies Star Fade"
NODE_STAR_BRIGHTNESS = "OuroSkies Star Brightness"
NODE_STAR_MUL_H = "OuroSkies Star Mul H"
NODE_STAR_MUL_F = "OuroSkies Star Mul F"
NODE_STAR_MUL_B = "OuroSkies Star Mul B"
NODE_STAR_CAM_MUL = "OuroSkies Star Cam Mul"
NODE_STAR_COLOR = "OuroSkies Star Color"
NODE_STAR_BG = "OuroSkies Star BG"
NODE_STAR_ADD_SHADER = "OuroSkies Star Add"
NODE_MILKY_DOT = "OuroSkies Milky Dot"
NODE_MILKY_ABS = "OuroSkies Milky Abs"
NODE_MILKY_NORMAL = "OuroSkies Milky Normal"
NODE_MILKY_MAP = "OuroSkies Milky Map"
NODE_MILKY_NOISE = "OuroSkies Milky Noise"
NODE_MILKY_LANE = "OuroSkies Milky Lane"
NODE_MILKY_CLUMP = "OuroSkies Milky Clump"
NODE_MILKY_DUST = "OuroSkies Milky Dust"
NODE_MILKY_SCALE = "OuroSkies Milky Noise Scale"
NODE_MILKY_STRENGTH = "OuroSkies Milky Strength"
NODE_MILKY_MUL_S = "OuroSkies Milky Mul S"
NODE_MILKY_MUL_H = "OuroSkies Milky Mul H"
NODE_MILKY_MUL_F = "OuroSkies Milky Mul F"
NODE_MILKY_CAM_MUL = "OuroSkies Milky Cam Mul"
NODE_MILKY_COLOR = "OuroSkies Milky Color"
NODE_MILKY_BG = "OuroSkies Milky BG"
NODE_MILKY_ADD = "OuroSkies Milky Add"
# Binary (secondary) sun — camera-path World overlay
NODE_SEC_GEO = "OuroSkies Sec Geo"
NODE_SEC_VIEW = "OuroSkies Sec View"
NODE_SEC_DIR = "OuroSkies Sec Dir"
NODE_SEC_DOT = "OuroSkies Sec Dot"
NODE_SEC_ACOS = "OuroSkies Sec Acos"
NODE_SEC_RADIUS = "OuroSkies Sec Radius"
NODE_SEC_MAP = "OuroSkies Sec Map"
NODE_SEC_COLOR = "OuroSkies Sec Color"
NODE_SEC_STRENGTH = "OuroSkies Sec Strength"
NODE_SEC_MUL = "OuroSkies Sec Mul"
NODE_SEC_BG = "OuroSkies Sec BG"
NODE_SEC_ADD = "OuroSkies Sec Add"
NODE_SEC_CAM_MUL = "OuroSkies Sec Cam Mul"
# Back-compat alias used by older comments
NODE_BACKGROUND = NODE_BG_CAMERA
