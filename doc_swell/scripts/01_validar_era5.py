"""
01_validar_era5.py — Validate all ERA5 NetCDF files (1979-2025).

Checks performed per file:
  - File exists and can be opened
  - Variables shts, mdts, mpts are present
  - 336 timestamps (14 days × 24 hours)
  - No duplicate timestamps
  - No temporal gaps (hourly continuity)
  - Latitude = -3.5, Longitude = -38.5
  - No NaN values
  - Direction in [0, 360]
  - Period > 0
  - Height >= 0

Outputs:
  - Console summary
  - output/relatorio_qualidade.txt
"""

import os
import sys
import numpy as np
import xarray as xr
import pandas as pd
from datetime import datetime

import config as cfg


def validate_year(year: int) -> dict:
    """Validate a single year's NetCDF file. Returns a dict with results."""
    filename = f"era5_swell_marco_{year}.nc"
    filepath = os.path.join(cfg.ERA5_NC_DIR, filename)
    result = {
        "year": year,
        "file": filename,
        "exists": False,
        "opens": False,
        "has_vars": False,
        "n_timestamps": 0,
        "expected_timestamps": 336,
        "duplicates": 0,
        "gaps": 0,
        "lat_ok": False,
        "lon_ok": False,
        "nan_shts": 0,
        "nan_mdts": 0,
        "nan_mpts": 0,
        "dir_out_of_range": 0,
        "period_invalid": 0,
        "height_negative": 0,
        "passed": False,
        "issues": [],
    }

    if not os.path.exists(filepath):
        result["issues"].append("File not found")
        return result
    result["exists"] = True

    try:
        ds = xr.open_dataset(filepath, engine="netcdf4")
    except Exception as e:
        result["issues"].append(f"Cannot open: {e}")
        return result
    result["opens"] = True

    # Check variables
    required_vars = [cfg.ERA5_VARS["height"], cfg.ERA5_VARS["direction"], cfg.ERA5_VARS["period"]]
    missing_vars = [v for v in required_vars if v not in ds.data_vars]
    if missing_vars:
        result["issues"].append(f"Missing variables: {missing_vars}")
        ds.close()
        return result
    result["has_vars"] = True

    # Identify time dimension
    time_dim = None
    for candidate in ["valid_time", "time"]:
        if candidate in ds.dims or candidate in ds.coords:
            time_dim = candidate
            break
    if time_dim is None:
        result["issues"].append("No time dimension found")
        ds.close()
        return result

    times = pd.DatetimeIndex(ds[time_dim].values)
    result["n_timestamps"] = len(times)

    if len(times) != 336:
        result["issues"].append(f"Expected 336 timestamps, got {len(times)}")

    # Duplicates
    result["duplicates"] = int(times.duplicated().sum())
    if result["duplicates"] > 0:
        result["issues"].append(f"{result['duplicates']} duplicate timestamps")

    # Gaps
    if len(times) > 1:
        diffs = np.diff(times.values) / np.timedelta64(1, "h")
        gaps = int(np.sum(diffs != 1.0))
        result["gaps"] = gaps
        if gaps > 0:
            result["issues"].append(f"{gaps} temporal gaps (non-1h intervals)")

    # Lat/Lon
    lat_vals = ds["latitude"].values.flatten()
    lon_vals = ds["longitude"].values.flatten()
    result["lat_ok"] = bool(np.all(np.isclose(lat_vals, cfg.LAT, atol=0.01)))
    result["lon_ok"] = bool(np.all(np.isclose(lon_vals, cfg.LON, atol=0.01)))
    if not result["lat_ok"]:
        result["issues"].append(f"Latitude mismatch: {lat_vals}")
    if not result["lon_ok"]:
        result["issues"].append(f"Longitude mismatch: {lon_vals}")

    # Extract data arrays
    shts = ds[cfg.ERA5_VARS["height"]].values.flatten()
    mdts = ds[cfg.ERA5_VARS["direction"]].values.flatten()
    mpts = ds[cfg.ERA5_VARS["period"]].values.flatten()

    # NaN checks
    result["nan_shts"] = int(np.isnan(shts).sum())
    result["nan_mdts"] = int(np.isnan(mdts).sum())
    result["nan_mpts"] = int(np.isnan(mpts).sum())
    total_nan = result["nan_shts"] + result["nan_mdts"] + result["nan_mpts"]
    if total_nan > 0:
        result["issues"].append(f"NaN values: shts={result['nan_shts']}, mdts={result['nan_mdts']}, mpts={result['nan_mpts']}")

    # Physical validity (only on non-NaN values)
    valid_dir = mdts[~np.isnan(mdts)]
    # Allow small floating-point overshoot (e.g., 360.0005)
    result["dir_out_of_range"] = int(np.sum((valid_dir < -0.01) | (valid_dir > 360.01)))
    if result["dir_out_of_range"] > 0:
        result["issues"].append(f"{result['dir_out_of_range']} direction values outside [0, 360]")

    valid_per = mpts[~np.isnan(mpts)]
    result["period_invalid"] = int(np.sum(valid_per <= 0))
    if result["period_invalid"] > 0:
        result["issues"].append(f"{result['period_invalid']} period values <= 0")

    valid_hgt = shts[~np.isnan(shts)]
    result["height_negative"] = int(np.sum(valid_hgt < 0))
    if result["height_negative"] > 0:
        result["issues"].append(f"{result['height_negative']} negative height values")

    ds.close()

    result["passed"] = len(result["issues"]) == 0
    return result


def main():
    print("=" * 70)
    print("ERA5 VALIDATION — Ceará Swell Climatology")
    print(f"Directory: {cfg.ERA5_NC_DIR}")
    print(f"Years: {cfg.ERA5_YEAR_START}–{cfg.ERA5_YEAR_END}")
    print("=" * 70)
    print()

    results = []
    for year in range(cfg.ERA5_YEAR_START, cfg.ERA5_YEAR_END + 1):
        r = validate_year(year)
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        icon = "OK" if r["passed"] else "!!"
        print(f"  [{icon}] {year}: {status}  (timestamps={r['n_timestamps']}, NaN={r['nan_shts']+r['nan_mdts']+r['nan_mpts']})")
        if not r["passed"]:
            for issue in r["issues"]:
                print(f"        -> {issue}")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    print()
    print("=" * 70)
    print(f"SUMMARY: {passed}/{total} years passed, {failed} failed")
    print("=" * 70)

    # Write report
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    report_path = cfg.QUALITY_REPORT
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("ERA5 Quality Report — Ceará Swell Climatology\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Directory: {cfg.ERA5_NC_DIR}\n")
        f.write(f"Years: {cfg.ERA5_YEAR_START}–{cfg.ERA5_YEAR_END}\n")
        f.write(f"Total files: {total}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")
        f.write("\n" + "=" * 70 + "\n\n")

        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            f.write(f"{r['year']} [{status}]\n")
            f.write(f"  File: {r['file']}\n")
            f.write(f"  Timestamps: {r['n_timestamps']}/{r['expected_timestamps']}\n")
            f.write(f"  Duplicates: {r['duplicates']}\n")
            f.write(f"  Gaps: {r['gaps']}\n")
            f.write(f"  Lat OK: {r['lat_ok']}, Lon OK: {r['lon_ok']}\n")
            f.write(f"  NaN — shts: {r['nan_shts']}, mdts: {r['nan_mdts']}, mpts: {r['nan_mpts']}\n")
            f.write(f"  Dir out of range: {r['dir_out_of_range']}\n")
            f.write(f"  Period invalid: {r['period_invalid']}\n")
            f.write(f"  Height negative: {r['height_negative']}\n")
            if r["issues"]:
                f.write(f"  Issues:\n")
                for issue in r["issues"]:
                    f.write(f"    - {issue}\n")
            f.write("\n")

    print(f"\nReport saved to: {report_path}")

    if failed > 0:
        print(f"\nWARNING: {failed} year(s) failed validation. Check the report.")
        sys.exit(1)
    else:
        print("\nAll files passed validation.")


if __name__ == "__main__":
    main()
