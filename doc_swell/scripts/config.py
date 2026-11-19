"""
Centralized configuration for the Ceará Swell Climatology Pipeline.

All thresholds, paths, variable mappings and parameters live here.
Nothing is hard-coded in the analysis scripts.
"""

import os

# ---------------------------------------------------------------------------
# Paths (relative to doc_swell/scripts/)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERA5_NC_DIR = os.path.join(BASE_DIR, "ERA5_CEARA_MARCO")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
GRAFICOS_DIR = os.path.join(OUTPUT_DIR, "graficos")

PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CLIMATOLOGY_DIR = os.path.join(DATA_DIR, "climatology")
RAW_NOAA_DIR = os.path.join(DATA_DIR, "raw", "noaa")

# Output file paths
ERA5_CSV = os.path.join(PROCESSED_DIR, "era5_ceara_marco_1979_2025.csv")
WW3_CSV = os.path.join(PROCESSED_DIR, "ww3_ceara_marco_2018_2025.csv")
ERA5_EVENTS_CSV = os.path.join(CLIMATOLOGY_DIR, "eventos_era5.csv")
WW3_EVENTS_CSV = os.path.join(CLIMATOLOGY_DIR, "eventos_ww3.csv")
CLIMATOLOGY_CSV = os.path.join(CLIMATOLOGY_DIR, "climatologia_resultados.csv")
QUALITY_REPORT = os.path.join(OUTPUT_DIR, "relatorio_qualidade.txt")
COMPARISON_REPORT = os.path.join(OUTPUT_DIR, "comparacao_era5_ww3.md")
FINAL_REPORT = os.path.join(OUTPUT_DIR, "RELATORIO_CLIMATOLOGIA.md")

# ---------------------------------------------------------------------------
# Geographic point
# ---------------------------------------------------------------------------
LAT = -3.5
LON = -38.5

# ---------------------------------------------------------------------------
# ERA5 year range
# ---------------------------------------------------------------------------
ERA5_YEAR_START = 1979
ERA5_YEAR_END = 2025

# WW3 year range
WW3_YEAR_START = 2018
WW3_YEAR_END = 2025

# ---------------------------------------------------------------------------
# Direction ranges — FROM convention (degrees)
#
# ERA5 mdts and WW3 sdir both use "direction FROM which waves come".
# N  = swell coming from the north
# NE = swell coming from the northeast
# ---------------------------------------------------------------------------
DIRECTIONS = {
    "N":    [(337.5, 360.0), (0.0, 22.5)],
    "NE":   [(22.5, 67.5)],
    "N/NE": [(337.5, 360.0), (0.0, 67.5)],
}

# Default direction filter for climatology
DEFAULT_DIRECTION = "N/NE"

# ---------------------------------------------------------------------------
# Surf scenario levels
#
# Each scenario defines minimum period (s) and minimum height (m).
# Direction filter is applied separately.
# ---------------------------------------------------------------------------
SCENARIOS = [
    {"name": "any_relevant",  "label": "Any relevant swell",  "period_min": 10, "height_min": 0.0},
    {"name": "surfable",      "label": "Surfable",             "period_min": 12, "height_min": 0.8},
    {"name": "good",          "label": "Good",                 "period_min": 12, "height_min": 1.0},
    {"name": "strong",        "label": "Strong",               "period_min": 12, "height_min": 1.2},
    {"name": "very_good",     "label": "Very good / strong",   "period_min": 12, "height_min": 1.5},
    {"name": "exceptional",   "label": "Exceptional",          "period_min": 12, "height_min": 2.0},
]

# ---------------------------------------------------------------------------
# Event detection
# ---------------------------------------------------------------------------
GAP_TOLERANCE_HOURS = 1   # max gap (hours) before splitting into two events

# ---------------------------------------------------------------------------
# March analysis windows
# ---------------------------------------------------------------------------
MARCH_WINDOWS = {
    "week3": {"start_day": 15, "end_day": 21, "label": "15–21 março"},
    "week4": {"start_day": 22, "end_day": 28, "label": "22–28 março"},
}

# ---------------------------------------------------------------------------
# ERA5 variable mapping
#
# shts = significant height of total swell (m)
# mdts = mean direction of total swell (degrees, FROM)
# mpts = mean period of total swell (s)
#
# These are swell-only variables, NOT combined wind+swell.
# ---------------------------------------------------------------------------
ERA5_VARS = {
    "height":    "shts",
    "direction": "mdts",
    "period":    "mpts",
}

# ---------------------------------------------------------------------------
# WW3 (NOAA ERDDAP) variable mapping
#
# shgt = swell peak significant height (m)
# sdir = swell peak direction (degrees, FROM)
# sper = swell peak period (s)
#
# NOTE: WW3 uses PEAK swell, ERA5 uses MEAN total swell.
# These are NOT physically identical. The comparison script
# (06_comparar_era5_ww3.py) documents and quantifies the differences.
# ---------------------------------------------------------------------------
WW3_VARS = {
    "height":    "shgt",
    "direction": "sdir",
    "period":    "sper",
}

# ---------------------------------------------------------------------------
# Standardized output column names
# ---------------------------------------------------------------------------
STD_COLUMNS = {
    "time":            "time",
    "year":            "year",
    "month":           "month",
    "day":             "day",
    "hour":            "hour",
    "lat":             "lat",
    "lon":             "lon",
    "swell_height":    "swell_height",
    "swell_period":    "swell_period",
    "swell_direction": "swell_direction",
    "source":          "source",
    "march_week":      "march_week",
}

# ---------------------------------------------------------------------------
# Height distribution bins (meters)
# ---------------------------------------------------------------------------
HEIGHT_BINS = [0.0, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, float("inf")]
HEIGHT_LABELS = ["<0.6", "0.6–0.8", "0.8–1.0", "1.0–1.2", "1.2–1.5", "1.5–2.0", "≥2.0"]

# ---------------------------------------------------------------------------
# Period distribution bins (seconds)
# ---------------------------------------------------------------------------
PERIOD_BINS = [0.0, 10.0, 12.0, 14.0, 16.0, float("inf")]
PERIOD_LABELS = ["<10", "10–12", "12–14", "14–16", "≥16"]

# ---------------------------------------------------------------------------
# Surfable window durations to test (hours)
# ---------------------------------------------------------------------------
WINDOW_DURATIONS = [3, 6, 12, 24]

# ---------------------------------------------------------------------------
# ERDDAP configuration for WW3 download
# ---------------------------------------------------------------------------
ERDDAP_BASE_URL = "https://coastwatch.pfeg.noaa.gov/erddap"
ERDDAP_DATASET = "NWW3_Global_Best"
