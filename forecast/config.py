"""
Configuration for the Praia de Iracema surf forecast module.

This file defines the surf spot, data sources, and surfability rules.
Unlike doc_swell/scripts/config.py (which configures the historical
analysis), this config is specific to real-time forecasting for a
single beach.
"""

# ---------------------------------------------------------------------------
# Spot definition
# ---------------------------------------------------------------------------
SPOT_NAME = "Praia de Iracema"
SPOT_LAT = -3.7217       # Iracema beach coordinates
SPOT_LON = -38.5133

# Open-Meteo uses a 28km grid, so we query the nearest offshore point
# (same point used in the historical ERA5 analysis)
OFFSHORE_LAT = -3.5
OFFSHORE_LON = -38.5

# ---------------------------------------------------------------------------
# Surfability rules for Iracema
#
# Iracema is a shallow beach break close to the swell source.
# Unlike open-ocean spots, it works with shorter-period trade-wind
# swell — what matters most is ENERGY, not period alone.
#
# Primary metric: wave energy E = (1/16) × ρ × g × Hs²
#
# MODEL CALIBRATION NOTE:
# SurfGuru runs WW3 with coastal-refined grids (1/16°, ~7km) that
# account for refraction/shoaling near the coast.  Open-Meteo uses
# DWD GWAM at 0.25° (28km) — a global offshore model that gives
# ~2x higher swell heights because it doesn't model coastal attenuation.
#
# Thresholds are scaled for Open-Meteo's offshore values:
#   SurfGuru 400 J → Open-Meteo ~800 J
#   SurfGuru 500 J → Open-Meteo ~1000 J
#   SurfGuru 800 J → Open-Meteo ~1600 J
#
# Direction: N through E — Iracema faces north but accepts ENE
# trade-wind swell that wraps around the headland.
#
# Tide: high tide drowns the sandbars.  Best at mid-to-low.
# ---------------------------------------------------------------------------
SWELL_DIR_RANGES = [(330.0, 360.0), (0.0, 90.0)]   # FROM convention, N to E
SWELL_HEIGHT_MIN = 0.6    # meters — below this, it's flat
SWELL_PERIOD_MIN = 4.0    # seconds — very low bar; energy is what matters
TIDE_MAX_HEIGHT = 1.5     # meters above chart datum — above this, too deep for waves to break
TIDE_ROCKS_WARNING = 0.6  # below this, rocks are exposed — experienced surfers only

# Wave energy threshold (J/m²) — scaled for Open-Meteo's offshore model
# E = (1/16) × 1025 × 9.81 × Hs²  (seawater density × gravity × height²)
ENERGY_SURFABLE = 800     # ~400 J on SurfGuru scale × 2 for offshore model

# Physical constants for energy calculation
RHO_SEAWATER = 1025       # kg/m³
G = 9.81                  # m/s²

# Rating thresholds — scaled for Open-Meteo (SurfGuru × 2)
RATING_THRESHOLDS = {
    "great": {"energy_min": 1600, "period_min": 8.0},
    "good":  {"energy_min": 1000, "period_min": 5.0},
    "fair":  {"energy_min": 800,  "period_min": 4.0},
}

# ---------------------------------------------------------------------------
# Tide reference
# ---------------------------------------------------------------------------
TIDE_STATION = "Porto de Mucuripe"
TIDE_TIMEZONE = "America/Fortaleza"   # UTC-3, no daylight saving

# ---------------------------------------------------------------------------
# Open-Meteo Marine API
#
# Free, no API key required.  Returns 7-day hourly swell forecast.
# Docs: https://open-meteo.com/en/docs/marine-weather-api
# ---------------------------------------------------------------------------
OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
FORECAST_DAYS = 7
