"""
04_detectar_eventos.py — Detect swell events from processed CSV data.

An "event" is a continuous period where swell conditions meet specific
criteria (direction, period, height). Consecutive qualifying hours are
grouped into a single event, with a configurable gap tolerance.

For each event computes: start, end, duration, max/mean height,
max/mean period, mean direction, dominant direction class.

Runs all 6 scenario levels for each data source.

Output: data/climatology/eventos_era5.csv (and eventos_ww3.csv if available)
"""

import os
import numpy as np
import pandas as pd

import config as cfg


def direction_matches(direction: float, ranges: list) -> bool:
    """Check if a direction value falls within any of the specified ranges."""
    for low, high in ranges:
        if low <= direction <= high:
            return True
    return False


def classify_direction(direction: float) -> str:
    """Classify a direction into N, NE, or other."""
    for name in ["N", "NE"]:
        if direction_matches(direction, cfg.DIRECTIONS[name]):
            return name
    return "other"


def detect_events(
    df: pd.DataFrame,
    direction_key: str = "N/NE",
    period_min: float = 12.0,
    height_min: float = 1.0,
    gap_tolerance: int = 1,
) -> pd.DataFrame:
    """
    Detect swell events from hourly data.

    Parameters
    ----------
    df : DataFrame with columns: time, swell_height, swell_period, swell_direction, year, march_week
    direction_key : key into cfg.DIRECTIONS
    period_min : minimum period threshold (seconds)
    height_min : minimum height threshold (meters)
    gap_tolerance : max number of consecutive non-qualifying hours
                    before splitting into separate events

    Returns
    -------
    DataFrame with one row per event.
    """
    df = df.copy().sort_values("time").reset_index(drop=True)
    dir_ranges = cfg.DIRECTIONS[direction_key]

    # Mark qualifying hours
    df["qualifies"] = (
        df["swell_direction"].apply(lambda d: direction_matches(d, dir_ranges))
        & (df["swell_period"] >= period_min)
        & (df["swell_height"] >= height_min)
    )

    if df["qualifies"].sum() == 0:
        return pd.DataFrame()

    # Group consecutive qualifying hours into events
    # Allow gap_tolerance hours of non-qualifying data within an event
    events = []
    in_event = False
    event_start = None
    event_rows = []
    gap_count = 0

    for idx, row in df.iterrows():
        if row["qualifies"]:
            if not in_event:
                # Start new event
                in_event = True
                event_start = idx
                event_rows = [row]
                gap_count = 0
            else:
                event_rows.append(row)
                gap_count = 0
        else:
            if in_event:
                gap_count += 1
                if gap_count > gap_tolerance:
                    # End event
                    events.append(pd.DataFrame(event_rows))
                    in_event = False
                    event_rows = []
                    gap_count = 0
                else:
                    # Still within tolerance — don't add non-qualifying row to event stats
                    pass

    # Close final event if still open
    if in_event and event_rows:
        events.append(pd.DataFrame(event_rows))

    if not events:
        return pd.DataFrame()

    # Compute event statistics
    results = []
    for event_df in events:
        start_time = event_df["time"].iloc[0]
        end_time = event_df["time"].iloc[-1]
        duration = len(event_df)

        # Direction classification
        dir_classes = event_df["swell_direction"].apply(classify_direction)
        dir_counts = dir_classes.value_counts()
        dominant_dir = dir_counts.index[0] if len(dir_counts) > 0 else "unknown"

        results.append({
            "start_time": start_time,
            "end_time": end_time,
            "year": int(event_df["year"].iloc[0]),
            "march_week": int(event_df["march_week"].mode().iloc[0]) if len(event_df) > 0 else 0,
            "duration_hours": duration,
            "max_height": event_df["swell_height"].max(),
            "mean_height": round(event_df["swell_height"].mean(), 4),
            "max_period": event_df["swell_period"].max(),
            "mean_period": round(event_df["swell_period"].mean(), 4),
            "mean_direction": round(event_df["swell_direction"].mean(), 2),
            "dominant_direction": dominant_dir,
            "n_hours_N": int((dir_classes == "N").sum()),
            "n_hours_NE": int((dir_classes == "NE").sum()),
        })

    return pd.DataFrame(results)


def run_all_scenarios(df: pd.DataFrame, source_name: str, scenarios: list = None) -> pd.DataFrame:
    """Run event detection for all scenarios and return combined results."""
    if scenarios is None:
        scenarios = cfg.SCENARIOS
    all_events = []

    for scenario in scenarios:
        print(f"  Scenario: {scenario['name']} "
              f"(period >= {scenario['period_min']}s, height >= {scenario['height_min']}m)")

        events = detect_events(
            df,
            direction_key=cfg.DEFAULT_DIRECTION,
            period_min=scenario["period_min"],
            height_min=scenario["height_min"],
            gap_tolerance=cfg.GAP_TOLERANCE_HOURS,
        )

        if len(events) > 0:
            events["scenario"] = scenario["name"]
            events["source"] = source_name
            all_events.append(events)
            print(f"    -> {len(events)} events detected")
        else:
            print(f"    -> 0 events")

    if all_events:
        return pd.concat(all_events, ignore_index=True)
    return pd.DataFrame()


def main():
    print("=" * 70)
    print("EVENT DETECTION — Ceará Swell Climatology")
    print(f"Direction: {cfg.DEFAULT_DIRECTION}")
    print(f"Gap tolerance: {cfg.GAP_TOLERANCE_HOURS}h")
    print("=" * 70)
    print()

    os.makedirs(cfg.CLIMATOLOGY_DIR, exist_ok=True)

    # ERA5
    if os.path.exists(cfg.ERA5_CSV):
        print("--- ERA5 (using ERA5-calibrated thresholds) ---")
        era5_df = pd.read_csv(cfg.ERA5_CSV, parse_dates=["time"])
        era5_events = run_all_scenarios(era5_df, "ERA5", cfg.SCENARIOS_ERA5)

        if len(era5_events) > 0:
            era5_events.to_csv(cfg.ERA5_EVENTS_CSV, index=False)
            print(f"\nERA5 events saved to: {cfg.ERA5_EVENTS_CSV}")
            print(f"Total events across all scenarios: {len(era5_events)}")
        else:
            print("\nNo ERA5 events detected.")
        print()
    else:
        print(f"ERA5 CSV not found: {cfg.ERA5_CSV}")
        print("Run 02_consolidar_era5.py first.")
        print()

    # WW3
    if os.path.exists(cfg.WW3_CSV):
        print("--- WW3 (using WW3 peak-period thresholds) ---")
        ww3_df = pd.read_csv(cfg.WW3_CSV, parse_dates=["time"])
        ww3_events = run_all_scenarios(ww3_df, "WW3", cfg.SCENARIOS_WW3)

        if len(ww3_events) > 0:
            ww3_events.to_csv(cfg.WW3_EVENTS_CSV, index=False)
            print(f"\nWW3 events saved to: {cfg.WW3_EVENTS_CSV}")
            print(f"Total events across all scenarios: {len(ww3_events)}")
        else:
            print("\nNo WW3 events detected.")
        print()
    else:
        print(f"WW3 CSV not found: {cfg.WW3_CSV}")
        print("Run 03_baixar_ww3.py first (requires internet).")
        print()

    # Quick summary for ERA5
    if os.path.exists(cfg.ERA5_CSV) and os.path.exists(cfg.ERA5_EVENTS_CSV):
        events = pd.read_csv(cfg.ERA5_EVENTS_CSV)
        print("=" * 70)
        print("ERA5 EVENT SUMMARY")
        print("=" * 70)
        for scenario in cfg.SCENARIOS:
            sc_events = events[events["scenario"] == scenario["name"]]
            if len(sc_events) == 0:
                print(f"  {scenario['name']}: 0 events")
                continue
            years_with = sc_events["year"].nunique()
            total_years = cfg.ERA5_YEAR_END - cfg.ERA5_YEAR_START + 1
            print(f"  {scenario['name']}: {len(sc_events)} events, "
                  f"{years_with}/{total_years} years ({100*years_with/total_years:.1f}%), "
                  f"duration: {sc_events['duration_hours'].mean():.1f}h avg, "
                  f"{sc_events['duration_hours'].max()}h max")


if __name__ == "__main__":
    main()
