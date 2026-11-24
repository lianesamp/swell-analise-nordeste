"""
00_baixar_era5_historico.py — Download full-year ERA5 swell data, year by year.

Downloads monthly NetCDF files for a single grid point offshore Fortaleza.
Designed to be run repeatedly: skips files that already exist and stops
gracefully when the CDS API daily quota is exceeded.

Usage:
    python 00_baixar_era5_historico.py 2025        # download all 12 months of 2025
    python 00_baixar_era5_historico.py 2025 2016    # download 2025 down to 2016
    python 00_baixar_era5_historico.py              # download 2025 down to 2015 (default)

Each monthly file is ~65-70 KB (single grid point, 3 variables, hourly).
The CDS free tier allows ~10-20 requests per day. If quota is exceeded,
the script stops and tells you to resume tomorrow.
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

# CDS ignores invalid days (e.g. Feb 31), so we can always request 1-31
DAYS = [f"{d:02d}" for d in range(1, 32)]

HOURS = [f"{h:02d}:00" for h in range(24)]

# Default year range (most recent first = most useful for analysis)
DEFAULT_YEAR_START = 2025
DEFAULT_YEAR_END = 2015

# Seconds to wait between requests (be gentle on the API)
SLEEP_BETWEEN = 5

# Minimum file size in bytes to consider a download complete
MIN_FILE_SIZE = 10_000


# ---------------------------------------------------------------------------
# Download logic
# ---------------------------------------------------------------------------
def is_quota_error(error_msg: str) -> bool:
    """Check if the error is a CDS API quota/cost limit."""
    msg = str(error_msg).lower()
    return "403" in msg or "cost limit" in msg or "forbidden" in msg


def download_month(client: cdsapi.Client, year: int, month: int) -> bool:
    """
    Download one month of ERA5 data. Returns True if successful or skipped,
    False if quota was hit (caller should stop).
    Raises Exception for other errors.
    """
    month_str = f"{month:02d}"
    filename = f"era5_swell_{year}_{month_str}.nc"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > MIN_FILE_SIZE:
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  {year}-{month_str}: already exists ({size_kb:.0f} KB). Skipping.")
        return True

    print(f"  {year}-{month_str}: downloading...", end=" ", flush=True)

    request = {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": str(year),
        "month": month_str,
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

        # Other error — log and continue to next month
        print(f"ERROR: {err}")
        log_path = os.path.join(OUTPUT_DIR, "errors.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{year}-{month_str}: {err}\n")
        return True  # True = keep going (not a quota issue)


def download_year(client: cdsapi.Client, year: int) -> bool:
    """
    Download all 12 months of a year. Returns True if completed,
    False if quota was hit mid-year.
    """
    # Count how many months are already done
    existing = sum(
        1 for m in range(1, 13)
        if os.path.exists(os.path.join(OUTPUT_DIR, f"era5_swell_{year}_{m:02d}.nc"))
        and os.path.getsize(os.path.join(OUTPUT_DIR, f"era5_swell_{year}_{m:02d}.nc")) > MIN_FILE_SIZE
    )

    print(f"\n{'=' * 60}")
    print(f"YEAR {year}  ({existing}/12 months already downloaded)")
    print(f"{'=' * 60}")

    for month in range(1, 13):
        ok = download_month(client, year, month)
        if not ok:
            return False
        time.sleep(SLEEP_BETWEEN)

    # Verify completeness
    done = sum(
        1 for m in range(1, 13)
        if os.path.exists(os.path.join(OUTPUT_DIR, f"era5_swell_{year}_{m:02d}.nc"))
        and os.path.getsize(os.path.join(OUTPUT_DIR, f"era5_swell_{year}_{m:02d}.nc")) > MIN_FILE_SIZE
    )
    print(f"\n  Year {year}: {done}/12 months complete.")
    return True


def main():
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
        sys.exit(1)

    # Ensure descending order (most recent first)
    if year_from < year_to:
        year_from, year_to = year_to, year_from

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("ERA5 Historical Download — Ceara Swell")
    print(f"Point: {LAT}, {LON}")
    print(f"Years: {year_from} down to {year_to}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Variables: height, direction, period (total swell)")
    print(f"Sleep between requests: {SLEEP_BETWEEN}s")

    client = cdsapi.Client()

    total_years_done = 0
    for year in range(year_from, year_to - 1, -1):
        completed = download_year(client, year)
        if not completed:
            print()
            print("=" * 60)
            print("STOPPED — CDS API daily quota exceeded.")
            print(f"Completed {total_years_done} full year(s) in this session.")
            print()
            print("Resume tomorrow with the same command:")
            print(f"  python {os.path.basename(__file__)} {year} {year_to}")
            print("(already downloaded files will be skipped)")
            print("=" * 60)
            sys.exit(0)
        total_years_done += 1

    print()
    print("=" * 60)
    print("ALL DOWNLOADS COMPLETE")
    print(f"Years: {year_from} to {year_to} ({total_years_done} years)")
    print(f"Files: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
