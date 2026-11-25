"""
00_baixar_era5_historico.py — Download ERA5 swell data for the swell season.

Downloads one NetCDF file per year containing only the swell-season months
(Sep-May) for a single grid point offshore Fortaleza.  This is more
efficient than downloading all 12 months individually:

  - 1 API request per year instead of 12 (saves CDS quota)
  - Excludes Jun-Aug (zero N/NE swell) so files are ~500 KB instead of ~800 KB
  - Produces the exact format the season pipeline expects

The CDS API accepts multiple months in a single request, so we pass
["01","02","03","04","05","09","10","11","12"] and get one merged file.

Designed to be run repeatedly: skips years that already exist and stops
gracefully when the CDS API daily quota is exceeded.

Usage:
    python 00_baixar_era5_historico.py 2023        # download 2023 only
    python 00_baixar_era5_historico.py 2023 2015    # download 2023 down to 2015
    python 00_baixar_era5_historico.py              # download 2025 down to 2015 (default)

Output: data/raw/era5_historico/era5_swell_YYYY_season.nc
"""

import os
import sys
import time

import cdsapi

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw", "era5_historico")

# Same offshore point used in the March analysis and live forecast
LAT = -3.5
LON = -38.5
AREA = [LAT, LON, LAT, LON]  # [North, West, South, East]

VARIABLES = [
    "significant_height_of_total_swell",
    "mean_direction_of_total_swell",
    "mean_period_of_total_swell",
]

# Swell season months only (Jun, Jul, Aug excluded — no N/NE swell)
SEASON_MONTHS = ["01", "02", "03", "04", "05", "09", "10", "11", "12"]

# CDS ignores invalid days (e.g. Feb 31), so we can always request 1-31
DAYS = [f"{d:02d}" for d in range(1, 32)]

HOURS = [f"{h:02d}:00" for h in range(24)]

# Default year range (most recent first = most useful for analysis)
DEFAULT_YEAR_START = 2025
DEFAULT_YEAR_END = 2015

# Seconds to wait between requests (be gentle on the API)
SLEEP_BETWEEN = 5

# Minimum file size in bytes to consider a download complete.
# A season file (9 months, single point, hourly) is ~480-520 KB.
MIN_FILE_SIZE = 100_000


# ---------------------------------------------------------------------------
# Download logic
# ---------------------------------------------------------------------------
def is_quota_error(error_msg: str) -> bool:
    """Check if the error is a CDS API quota/cost limit."""
    msg = str(error_msg).lower()
    return "403" in msg or "cost limit" in msg or "forbidden" in msg


def download_season(client: cdsapi.Client, year: int) -> bool:
    """
    Download one year's swell-season data as a single file.

    Returns True if successful or skipped, False if quota was hit.

    The CDS API merges all requested months into one NetCDF file
    automatically.  So requesting months [01,02,...,05,09,...,12]
    produces a single file with ~6500 hourly timestamps.
    """
    filename = f"era5_swell_{year}_season.nc"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > MIN_FILE_SIZE:
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  {year}: already exists ({size_kb:.0f} KB). Skipping.")
        return True

    print(f"  {year}: downloading 9 season months...", end=" ", flush=True)

    request = {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": str(year),
        "month": SEASON_MONTHS,
        "day": DAYS,
        "time": HOURS,
        "area": AREA,
        "format": "netcdf",
    }

    try:
        client.retrieve("reanalysis-era5-single-levels", request, filepath)
        size_kb = os.path.getsize(filepath) / 1024
        print(f"OK ({size_kb:.0f} KB)")
        return True

    except Exception as err:
        # Remove incomplete file
        if os.path.exists(filepath):
            os.remove(filepath)

        if is_quota_error(err):
            print("QUOTA EXCEEDED")
            return False

        # Other error — log and continue to next year
        print(f"ERROR: {err}")
        log_path = os.path.join(OUTPUT_DIR, "errors.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{year}: {err}\n")
        return True  # True = keep going (not a quota issue)


def main() -> None:
    # Parse arguments
    args = sys.argv[1:]

    if len(args) == 0:
        year_from = DEFAULT_YEAR_START
        year_to = DEFAULT_YEAR_END
    elif len(args) == 1:
        year_from = int(args[0])
        year_to = year_from  # single year
    elif len(args) == 2:
        year_from = int(args[0])
        year_to = int(args[1])
    else:
        print("Usage: python 00_baixar_era5_historico.py [year_start] [year_end]")
        print("  year_start: most recent year (default: 2025)")
        print("  year_end:   oldest year (default: 2015)")
        print()
        print("Examples:")
        print("  python 00_baixar_era5_historico.py 2023        # 2023 only")
        print("  python 00_baixar_era5_historico.py 2023 2015    # 2023 down to 2015")
        print("  python 00_baixar_era5_historico.py              # 2025 down to 2015")
        sys.exit(1)

    # Ensure descending order (most recent first)
    if year_from < year_to:
        year_from, year_to = year_to, year_from

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("ERA5 Season Download — Ceara Swell (Front 3)")
    print(f"Point: {LAT}, {LON}")
    print(f"Years: {year_from} down to {year_to}")
    print(f"Months: {', '.join(SEASON_MONTHS)} (swell season only)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Variables: height, direction, period (total swell)")
    print(f"Sleep between requests: {SLEEP_BETWEEN}s")
    print()

    client = cdsapi.Client()

    total_years_done = 0
    for year in range(year_from, year_to - 1, -1):
        completed = download_season(client, year)
        if not completed:
            print()
            print("=" * 60)
            print("STOPPED — CDS API daily quota exceeded.")
            print(f"Completed {total_years_done} year(s) in this session.")
            print()
            print("Resume tomorrow with the same command:")
            print(f"  python {os.path.basename(__file__)} {year} {year_to}")
            print("(already downloaded files will be skipped)")
            print("=" * 60)
            sys.exit(0)

        total_years_done += 1
        time.sleep(SLEEP_BETWEEN)

    print()
    print("=" * 60)
    print("ALL DOWNLOADS COMPLETE")
    print(f"Years: {year_from} to {year_to} ({total_years_done} years)")
    print(f"Files: {OUTPUT_DIR}")
    print()
    print("Next step: run the season pipeline")
    print("  cd doc_swell/scripts/season")
    print("  python cli.py run")
    print("=" * 60)


if __name__ == "__main__":
    main()
