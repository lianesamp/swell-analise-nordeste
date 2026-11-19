"""
03_baixar_ww3.py — Re-download WW3 swell data from NOAA ERDDAP.

Downloads swell peak data for March 15-28, 2018-2025
from the NOAA/NCEP WaveWatch III dataset via ERDDAP.

Point: -3.5, -38.5
Variables: shgt (height), sdir (direction), sper (period)

Output: data/processed/ww3_ceara_marco_2018_2025.csv
Expected: 2,688 rows (8 years × 14 days × 24 hours)
"""

import os
import io
import time
import pandas as pd

import config as cfg

# ERDDAP returns CSV directly — no need for special libraries
import urllib.request
import urllib.error
import ssl


def build_erddap_url(year: int) -> str:
    """Build ERDDAP CSV download URL for a single year's March 15-28."""
    start = f"{year}-03-15T00:00:00Z"
    end = f"{year}-03-28T23:00:00Z"

    # Use the NWW3_Global_Best dataset
    # Variables: Sper, Shgt, Sdir (swell peak)
    url = (
        f"{cfg.ERDDAP_BASE_URL}/griddap/{cfg.ERDDAP_DATASET}.csv?"
        f"Sper[({start}):1:({end})][({cfg.LAT}):1:({cfg.LAT})][({cfg.LON}):1:({cfg.LON})],"
        f"Shgt[({start}):1:({end})][({cfg.LAT}):1:({cfg.LAT})][({cfg.LON}):1:({cfg.LON})],"
        f"Sdir[({start}):1:({end})][({cfg.LAT}):1:({cfg.LAT})][({cfg.LON}):1:({cfg.LON})]"
    )
    return url


def download_year(year: int) -> pd.DataFrame:
    """Download a single year from ERDDAP and return a DataFrame."""
    url = build_erddap_url(year)
    print(f"  Downloading {year}...")

    try:
        # NOAA ERDDAP sometimes has SSL certificate issues
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(url, timeout=60, context=ctx)
        content = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"    HTTP Error {e.code}: {e.reason}")
        raise
    except Exception as e:
        print(f"    Error: {e}")
        raise

    # ERDDAP CSV has a header row and a units row — skip the units row
    lines = content.strip().split("\n")
    header = lines[0]
    data_lines = lines[2:]  # skip units row (line 1)

    csv_text = header + "\n" + "\n".join(data_lines)
    df = pd.read_csv(io.StringIO(csv_text))

    return df


def standardize_ww3(df: pd.DataFrame) -> pd.DataFrame:
    """Convert raw ERDDAP DataFrame to standardized format."""
    df = df.copy()

    # Parse time
    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    df["hour"] = df["time"].dt.hour

    # Rename to standardized columns
    result = pd.DataFrame({
        "time": df["time"],
        "year": df["year"],
        "month": df["month"],
        "day": df["day"],
        "hour": df["hour"],
        "lat": cfg.LAT,
        "lon": cfg.LON,
        "swell_height": df["Shgt"].round(4),
        "swell_period": df["Sper"].round(4),
        "swell_direction": df["Sdir"].round(2),
        "source": "WW3",
    })

    # March week classification
    result["march_week"] = result["day"].apply(
        lambda d: 3 if cfg.MARCH_WINDOWS["week3"]["start_day"] <= d <= cfg.MARCH_WINDOWS["week3"]["end_day"]
        else (4 if cfg.MARCH_WINDOWS["week4"]["start_day"] <= d <= cfg.MARCH_WINDOWS["week4"]["end_day"]
              else 0)
    )

    return result


def main():
    print("=" * 70)
    print("WW3 DOWNLOAD — NOAA ERDDAP")
    print(f"Dataset: {cfg.ERDDAP_DATASET}")
    print(f"Point: {cfg.LAT}, {cfg.LON}")
    print(f"Years: {cfg.WW3_YEAR_START}–{cfg.WW3_YEAR_END}")
    print("=" * 70)
    print()

    all_dfs = []
    failed_years = []

    for year in range(cfg.WW3_YEAR_START, cfg.WW3_YEAR_END + 1):
        try:
            raw_df = download_year(year)
            std_df = standardize_ww3(raw_df)
            all_dfs.append(std_df)
            print(f"    {year}: {len(std_df)} rows")
        except Exception as e:
            print(f"    {year}: FAILED — {e}")
            failed_years.append(year)

        time.sleep(1)  # be polite to the server

    if not all_dfs:
        print("\nNo data downloaded. Check your internet connection and ERDDAP availability.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("time").reset_index(drop=True)

    print()
    print(f"Total rows: {len(combined)}")
    print(f"Years downloaded: {combined['year'].nunique()}")
    if failed_years:
        print(f"Failed years: {failed_years}")
    print()

    # Quick stats
    print("Quick stats:")
    print(f"  Height — min: {combined['swell_height'].min():.3f}, "
          f"max: {combined['swell_height'].max():.3f}, "
          f"mean: {combined['swell_height'].mean():.3f}")
    print(f"  Period — min: {combined['swell_period'].min():.2f}, "
          f"max: {combined['swell_period'].max():.2f}, "
          f"mean: {combined['swell_period'].mean():.2f}")
    print(f"  Direction — min: {combined['swell_direction'].min():.1f}, "
          f"max: {combined['swell_direction'].max():.1f}")
    nan_count = combined.isna().sum().sum()
    print(f"  NaN count: {nan_count}")
    if nan_count > 0:
        print("  NaN per column:")
        for col in combined.columns:
            n = combined[col].isna().sum()
            if n > 0:
                print(f"    {col}: {n}")
    print()

    # Save
    os.makedirs(cfg.PROCESSED_DIR, exist_ok=True)

    # Also save raw copy
    os.makedirs(cfg.RAW_NOAA_DIR, exist_ok=True)
    raw_path = os.path.join(cfg.RAW_NOAA_DIR, "ww3_raw_2018_2025.csv")
    combined.to_csv(raw_path, index=False)
    print(f"Raw copy saved to: {raw_path}")

    combined.to_csv(cfg.WW3_CSV, index=False)
    print(f"Processed CSV saved to: {cfg.WW3_CSV}")
    print(f"File size: {os.path.getsize(cfg.WW3_CSV) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
