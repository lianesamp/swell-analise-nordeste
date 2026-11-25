"""
01_consolidar_season.py — Consolidate season ERA5 NetCDF files into a single CSV.

Reads all era5_swell_YYYY_season.nc files found in data/raw/era5_historico/
and produces a unified CSV with standardized column names.

Each NetCDF file contains 9 months of hourly data (Sep-May) for a single
grid point offshore Fortaleza.  The script:

  1. Scans the raw directory for season files
  2. Opens each one with xarray (the standard Python library for NetCDF)
  3. Extracts the 3 swell variables + timestamps
  4. Filters to season months only (safety check — the files should already
     contain only season months, but we verify)
  5. Concatenates all years into a single DataFrame
  6. Saves to CSV

Output: data/processed/era5_season.csv

This is the Season equivalent of the March pipeline's 02_consolidar_era5.py.
The key difference: March reads from ERA5_CEARA_MARCO/ (14-day windows),
while this reads from data/raw/era5_historico/ (9-month seasons).
"""

import os
import glob

import numpy as np
import xarray as xr
import pandas as pd

import config as cfg


def find_season_files() -> list[tuple[int, str]]:
    """
    Scan the raw directory for season NetCDF files.

    Returns a sorted list of (year, filepath) tuples.
    Looks for files matching the pattern era5_swell_YYYY_season.nc.
    """
    pattern = os.path.join(cfg.RAW_DIR, "era5_swell_*_season.nc")
    files = glob.glob(pattern)

    results: list[tuple[int, str]] = []
    for filepath in files:
        # Extract year from filename: era5_swell_2025_season.nc -> 2025
        basename = os.path.basename(filepath)
        parts = basename.replace(".nc", "").split("_")
        # parts = ["era5", "swell", "2025", "season"]
        try:
            year = int(parts[2])
            results.append((year, filepath))
        except (IndexError, ValueError):
            print(f"  WARNING: skipping unrecognized file: {basename}")

    return sorted(results, key=lambda x: x[0])


def load_season_file(year: int, filepath: str) -> pd.DataFrame:
    """
    Load a single year's season NetCDF and return a standardized DataFrame.

    Uses xarray to open the file — same approach as the March consolidation
    script.  xarray is a library built on top of NumPy and pandas specifically
    for working with labeled multi-dimensional arrays (like climate data in
    NetCDF format).  Think of it as "pandas for N-dimensional data".

    Alternative: netCDF4 library directly.  xarray is preferred because it
    handles coordinate alignment, time parsing, and dimension names
    automatically.
    """
    ds = xr.open_dataset(filepath, engine="netcdf4")

    # Identify time dimension (ERA5 files from CDS use "valid_time",
    # older files might use "time")
    time_dim = "valid_time" if "valid_time" in ds.dims or "valid_time" in ds.coords else "time"

    times = pd.DatetimeIndex(ds[time_dim].values)
    shts = ds[cfg.ERA5_VARS["height"]].values.flatten()
    mdts = ds[cfg.ERA5_VARS["direction"]].values.flatten()
    mpts = ds[cfg.ERA5_VARS["period"]].values.flatten()

    ds.close()

    # Wrap direction values > 360 or < 0 (floating-point artifacts from ERA5)
    mdts = np.where(mdts > 360.0, mdts - 360.0, mdts)
    mdts = np.where(mdts < 0.0, mdts + 360.0, mdts)

    df = pd.DataFrame({
        "time": times,
        "year": times.year,
        "month": times.month,
        "day": times.day,
        "hour": times.hour,
        "lat": cfg.LAT,
        "lon": cfg.LON,
        "swell_height": np.round(shts, 4),
        "swell_period": np.round(mpts, 4),
        "swell_direction": np.round(mdts, 2),
        "source": "ERA5",
    })

    # Filter to season months only (safety check)
    before = len(df)
    df = df[df["month"].isin(cfg.SEASON_MONTHS)].reset_index(drop=True)
    after = len(df)
    if before != after:
        print(f"    NOTE: filtered out {before - after} non-season rows")

    return df


def main() -> None:
    print("=" * 70)
    print("SEASON CONSOLIDATION — Ceara Swell (Front 3)")
    print(f"Raw directory: {cfg.RAW_DIR}")
    print(f"Season months: {cfg.SEASON_MONTHS}")
    print("=" * 70)
    print()

    # Find available files
    season_files = find_season_files()

    if not season_files:
        print("No season files found!")
        print(f"Expected files like: era5_swell_2025_season.nc in {cfg.RAW_DIR}")
        return

    print(f"Found {len(season_files)} season file(s):")
    for year, filepath in season_files:
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  {year}: {os.path.basename(filepath)} ({size_kb:.0f} KB)")
    print()

    # Load and concatenate all files
    all_dfs: list[pd.DataFrame] = []
    for year, filepath in season_files:
        df = load_season_file(year, filepath)
        all_dfs.append(df)
        print(f"  {year}: {len(df)} rows loaded "
              f"(months {sorted(df['month'].unique().tolist())})")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("time").reset_index(drop=True)

    print()
    print(f"Total rows: {len(combined)}")
    print(f"Years: {combined['year'].nunique()} ({combined['year'].min()}-{combined['year'].max()})")
    print(f"Time range: {combined['time'].min()} to {combined['time'].max()}")
    print()

    # Quick sanity checks
    print("Quick stats:")
    print(f"  Height  — min: {combined['swell_height'].min():.3f}, "
          f"max: {combined['swell_height'].max():.3f}, "
          f"mean: {combined['swell_height'].mean():.3f}")
    print(f"  Period  — min: {combined['swell_period'].min():.2f}, "
          f"max: {combined['swell_period'].max():.2f}, "
          f"mean: {combined['swell_period'].mean():.2f}")
    print(f"  Direction — min: {combined['swell_direction'].min():.1f}, "
          f"max: {combined['swell_direction'].max():.1f}")
    print(f"  NaN count: {combined.isna().sum().sum()}")
    print()

    # Rows per month
    print("Rows per month:")
    for month in cfg.SEASON_MONTHS:
        count = (combined["month"] == month).sum()
        label = cfg.MONTH_LABELS.get(month, str(month))
        print(f"  {label:>3}: {count:>6} rows")
    print()

    # Save
    os.makedirs(cfg.PROCESSED_DIR, exist_ok=True)
    combined.to_csv(cfg.SEASON_CSV, index=False)
    print(f"CSV saved to: {cfg.SEASON_CSV}")
    print(f"File size: {os.path.getsize(cfg.SEASON_CSV) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
