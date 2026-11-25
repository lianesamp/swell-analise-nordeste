"""
Configuration for the Season Analysis Pipeline (Front 3).

This module reuses the shared constants from the March pipeline
(scenarios, directions, ERA5 variable mapping) and adds season-specific
settings: which months form the swell season, paths for season output
files, and the year range we have data for.

Why a separate config instead of extending the March one?
  - The March pipeline analyzes 2 specific weeks across 47 years.
  - The Season pipeline analyzes 9 months across 10+ years.
  - Different time granularity, different output files, different questions.
  - Keeping them separate avoids coupling: changes to one don't break the other.
"""

import os
import importlib.util

# ---------------------------------------------------------------------------
# Import shared constants from the March pipeline
#
# We use importlib to load the parent config explicitly by file path.
# Why not just `from config import ...`?  Because this file IS config.py,
# so Python would find itself instead of the parent's config.py.
#
# importlib.util.spec_from_file_location() loads a module from an absolute
# path, bypassing the normal import system.  This is a standard Python
# pattern for importing from a specific file when names collide.
#
# Alternative: rename this file to season_config.py.  We chose importlib
# to keep the naming consistent (every pipeline has config.py).
# ---------------------------------------------------------------------------
_PARENT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config.py",
)
_spec = importlib.util.spec_from_file_location("march_config", _PARENT_CONFIG_PATH)
assert _spec is not None and _spec.loader is not None
_march_cfg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_march_cfg)

# Re-export the constants we need from the March config
LAT: float = _march_cfg.LAT
LON: float = _march_cfg.LON
DIRECTIONS: dict = _march_cfg.DIRECTIONS
DEFAULT_DIRECTION: str = _march_cfg.DEFAULT_DIRECTION
SCENARIOS_ERA5: list[dict] = _march_cfg.SCENARIOS_ERA5
ERA5_VARS: dict = _march_cfg.ERA5_VARS
GAP_TOLERANCE_HOURS: int = _march_cfg.GAP_TOLERANCE_HOURS
HEIGHT_BINS: list[float] = _march_cfg.HEIGHT_BINS
HEIGHT_LABELS: list[str] = _march_cfg.HEIGHT_LABELS
WINDOW_DURATIONS: list[int] = _march_cfg.WINDOW_DURATIONS

# ---------------------------------------------------------------------------
# Season-specific settings
# ---------------------------------------------------------------------------

# Swell season months: September through May.
# June, July, August have essentially zero N/NE swell at Praia de Iracema
# because the ITCZ (Intertropical Convergence Zone) is too far north for
# North Atlantic swells to reach Ceara.
SEASON_MONTHS = [9, 10, 11, 12, 1, 2, 3, 4, 5]

# Human-readable month labels (Portuguese abbreviations for display)
MONTH_LABELS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

# Year range for the season analysis.
# We download starting from the most recent year backwards.
# This will grow as more years are downloaded.
SEASON_YEAR_START = 2025
SEASON_YEAR_END = 2025  # will become 2015 once all data is downloaded

# ---------------------------------------------------------------------------
# Paths
#
# __file__ = doc_swell/scripts/season/config.py
# dirname x1 = doc_swell/scripts/season/
# dirname x2 = doc_swell/scripts/
# dirname x3 = doc_swell/           <-- this is BASE_DIR
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "era5_historico")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CLIMATOLOGY_DIR = os.path.join(BASE_DIR, "data", "climatology")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Output file paths
SEASON_CSV = os.path.join(PROCESSED_DIR, "era5_season.csv")
SEASON_EVENTS_CSV = os.path.join(CLIMATOLOGY_DIR, "eventos_season.csv")
MONTHLY_CLIMATOLOGY_CSV = os.path.join(CLIMATOLOGY_DIR, "monthly_climatology.csv")
MONTHLY_SUMMARY_CSV = os.path.join(CLIMATOLOGY_DIR, "monthly_summary.csv")

# ---------------------------------------------------------------------------
# File naming convention
#
# Each year's season file: era5_swell_YYYY_season.nc
# Contains months Sep-May (9 months) of hourly data for a single grid point.
# ---------------------------------------------------------------------------
def season_filename(year: int) -> str:
    """Return the expected filename for a year's season data."""
    return f"era5_swell_{year}_season.nc"
