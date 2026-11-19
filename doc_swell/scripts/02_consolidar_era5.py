"""
02_consolidar_era5.py — Consolidate all ERA5 NetCDF files into a single CSV.

Reads the 47 annual NetCDF files (1979-2025) and produces a unified CSV
with standardized column names.

Output: data/processed/era5_ceara_marco_1979_2025.csv
Expected: ~15,792 rows (47 years × 336 hours)
"""

import os
import numpy as np
import xarray as xr
import pandas as pd

import config as cfg


def load_year(year: int) -> pd.DataFrame:
    """Load a single year's NetCDF and return a standardized DataFrame."""
    filepath = os.path.join(cfg.ERA5_NC_DIR, f"era5_swell_marco_{year}.nc")
    ds = xr.open_dataset(filepath, engine="netcdf4")

    # Identify time dimension
    time_dim = "valid_time" if "valid_time" in ds.dims or "valid_time" in ds.coords else "time"

    times = pd.DatetimeIndex(ds[time_dim].values)
    shts = ds[cfg.ERA5_VARS["height"]].values.flatten()
    mdts = ds[cfg.ERA5_VARS["direction"]].values.flatten()
    mpts = ds[cfg.ERA5_VARS["period"]].values.flatten()

    ds.close()

    # Wrap direction values > 360 (floating-point artifacts)
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

    # March week classification
    df["march_week"] = df["day"].apply(
        lambda d: 3 if cfg.MARCH_WINDOWS["week3"]["start_day"] <= d <= cfg.MARCH_WINDOWS["week3"]["end_day"]
        else (4 if cfg.MARCH_WINDOWS["week4"]["start_day"] <= d <= cfg.MARCH_WINDOWS["week4"]["end_day"]
              else 0)
    )

    return df


def main():
    print("=" * 70)
    print("ERA5 CONSOLIDATION — Ceará Swell Climatology")
    print(f"Years: {cfg.ERA5_YEAR_START}–{cfg.ERA5_YEAR_END}")
    print("=" * 70)
    print()

    all_dfs = []
    for year in range(cfg.ERA5_YEAR_START, cfg.ERA5_YEAR_END + 1):
        df = load_year(year)
        all_dfs.append(df)
        print(f"  {year}: {len(df)} rows loaded")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("time").reset_index(drop=True)

    print()
    print(f"Total rows: {len(combined)}")
    print(f"Years: {combined['year'].nunique()}")
    print(f"Time range: {combined['time'].min()} to {combined['time'].max()}")
    print()

    # Quick sanity checks
    print("Quick stats:")
    print(f"  Height — min: {combined['swell_height'].min():.3f}, "
          f"max: {combined['swell_height'].max():.3f}, "
          f"mean: {combined['swell_height'].mean():.3f}")
    print(f"  Period — min: {combined['swell_period'].min():.2f}, "
          f"max: {combined['swell_period'].max():.2f}, "
          f"mean: {combined['swell_period'].mean():.2f}")
    print(f"  Direction — min: {combined['swell_direction'].min():.1f}, "
          f"max: {combined['swell_direction'].max():.1f}")
    print(f"  NaN count: {combined.isna().sum().sum()}")
    print()

    # Save
    os.makedirs(cfg.PROCESSED_DIR, exist_ok=True)
    combined.to_csv(cfg.ERA5_CSV, index=False)
    print(f"CSV saved to: {cfg.ERA5_CSV}")
    print(f"File size: {os.path.getsize(cfg.ERA5_CSV) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
