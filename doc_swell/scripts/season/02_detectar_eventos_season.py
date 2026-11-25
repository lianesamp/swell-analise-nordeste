"""
02_detectar_eventos_season.py — Detect swell events across the full season.

Reads the consolidated season CSV and finds continuous N/NE swell episodes
using the same algorithm as the March pipeline's 04_detectar_eventos.py.

Key difference from the March version:
  - March detects events within 14-day windows (week 3 and week 4).
  - Season detects events across 9 continuous months (Sep-May).
  - Events can span midnight, multiple days, or even cross month boundaries.

The algorithm is identical:
  1. For each hourly row, check if it "qualifies" (direction in N/NE range,
     period >= threshold, height >= threshold).
  2. Group consecutive qualifying hours into events.
  3. Allow a gap tolerance (default 1 hour) — if 1 non-qualifying hour sits
     between two qualifying hours, it's treated as one continuous event
     rather than two separate ones.

This avoids "pseudo-replication" (counting each hour as an independent
observation when they're really part of the same weather system).

Output: data/climatology/eventos_season.csv
"""

import os

import numpy as np
import pandas as pd

import config as cfg


# ---------------------------------------------------------------------------
# Reuse direction matching from the March pipeline
# ---------------------------------------------------------------------------

def direction_matches(direction: float, ranges: list[tuple[float, float]]) -> bool:
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


# ---------------------------------------------------------------------------
# Event detection (adapted for season-length data)
# ---------------------------------------------------------------------------

def detect_events(
    df: pd.DataFrame,
    direction_key: str,
    period_min: float,
    height_min: float,
    gap_tolerance: int,
) -> pd.DataFrame:
    """
    Detect swell events from hourly data.

    This is the same algorithm as 04_detectar_eventos.py's detect_events(),
    but adapted to include the month in event metadata (since events can
    happen in any month, not just March).

    Parameters
    ----------
    df : DataFrame with columns: time, swell_height, swell_period,
         swell_direction, year, month
    direction_key : key into cfg.DIRECTIONS (e.g. "N/NE")
    period_min : minimum period threshold (seconds)
    height_min : minimum height threshold (meters)
    gap_tolerance : max consecutive non-qualifying hours before splitting

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
    events: list[pd.DataFrame] = []
    in_event = False
    event_rows: list[pd.Series] = []
    gap_count = 0

    for _, row in df.iterrows():
        if row["qualifies"]:
            if not in_event:
                in_event = True
                event_rows = [row]
                gap_count = 0
            else:
                event_rows.append(row)
                gap_count = 0
        else:
            if in_event:
                gap_count += 1
                if gap_count > gap_tolerance:
                    events.append(pd.DataFrame(event_rows))
                    in_event = False
                    event_rows = []
                    gap_count = 0

    # Close final event if still open
    if in_event and event_rows:
        events.append(pd.DataFrame(event_rows))

    if not events:
        return pd.DataFrame()

    # Compute event statistics
    results: list[dict] = []
    for ev_df in events:
        start_time = ev_df["time"].iloc[0]
        end_time = ev_df["time"].iloc[-1]

        # Direction classification
        dir_classes = ev_df["swell_direction"].apply(classify_direction)
        dir_counts = dir_classes.value_counts()
        dominant_dir = dir_counts.index[0] if len(dir_counts) > 0 else "unknown"

        # Month of the event (use the start time's month)
        event_month = int(ev_df["month"].iloc[0])

        results.append({
            "start_time": start_time,
            "end_time": end_time,
            "year": int(ev_df["year"].iloc[0]),
            "month": event_month,
            "duration_hours": len(ev_df),
            "max_height": round(float(ev_df["swell_height"].max()), 4),
            "mean_height": round(float(ev_df["swell_height"].mean()), 4),
            "max_period": round(float(ev_df["swell_period"].max()), 4),
            "mean_period": round(float(ev_df["swell_period"].mean()), 4),
            "mean_direction": round(float(ev_df["swell_direction"].mean()), 2),
            "dominant_direction": dominant_dir,
            "n_hours_N": int((dir_classes == "N").sum()),
            "n_hours_NE": int((dir_classes == "NE").sum()),
        })

    return pd.DataFrame(results)


def run_all_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run event detection for all 6 scenario levels.

    Returns a combined DataFrame with a "scenario" column identifying
    which threshold level each event was detected at.
    """
    all_events: list[pd.DataFrame] = []

    for scenario in cfg.SCENARIOS_ERA5:
        print(f"  Scenario: {scenario['name']} "
              f"(period >= {scenario['period_min']}s, "
              f"height >= {scenario['height_min']}m)")

        events = detect_events(
            df,
            direction_key=cfg.DEFAULT_DIRECTION,
            period_min=scenario["period_min"],
            height_min=scenario["height_min"],
            gap_tolerance=cfg.GAP_TOLERANCE_HOURS,
        )

        if len(events) > 0:
            events["scenario"] = scenario["name"]
            all_events.append(events)
            print(f"    -> {len(events)} events detected")
        else:
            print(f"    -> 0 events")

    if all_events:
        return pd.concat(all_events, ignore_index=True)
    return pd.DataFrame()


def main() -> None:
    print("=" * 70)
    print("SEASON EVENT DETECTION — Ceara Swell (Front 3)")
    print(f"Direction: {cfg.DEFAULT_DIRECTION}")
    print(f"Gap tolerance: {cfg.GAP_TOLERANCE_HOURS}h")
    print("=" * 70)
    print()

    if not os.path.exists(cfg.SEASON_CSV):
        print(f"Season CSV not found: {cfg.SEASON_CSV}")
        print("Run 01_consolidar_season.py first.")
        return

    df = pd.read_csv(cfg.SEASON_CSV, parse_dates=["time"])

    print(f"Loaded {len(df)} rows")
    print(f"Years: {df['year'].min()}-{df['year'].max()} "
          f"({df['year'].nunique()} years)")
    print(f"Months: {sorted(df['month'].unique().tolist())}")
    print()

    # Run all scenarios
    all_events = run_all_scenarios(df)

    if len(all_events) == 0:
        print("\nNo events detected across any scenario.")
        return

    # Save
    os.makedirs(cfg.CLIMATOLOGY_DIR, exist_ok=True)
    all_events.to_csv(cfg.SEASON_EVENTS_CSV, index=False)
    print(f"\nEvents saved to: {cfg.SEASON_EVENTS_CSV}")
    print(f"Total events across all scenarios: {len(all_events)}")
    print()

    # Summary by scenario
    print("=" * 70)
    print("SUMMARY BY SCENARIO")
    print("=" * 70)
    for scenario in cfg.SCENARIOS_ERA5:
        sc_events = all_events[all_events["scenario"] == scenario["name"]]
        if len(sc_events) == 0:
            print(f"  {scenario['name']}: 0 events")
            continue
        print(f"  {scenario['name']}: {len(sc_events)} events, "
              f"duration: {sc_events['duration_hours'].mean():.1f}h avg / "
              f"{sc_events['duration_hours'].max()}h max, "
              f"height: {sc_events['max_height'].mean():.2f}m avg")

    # Summary by month (for the "surfable" scenario)
    print()
    print("=" * 70)
    print("EVENTS BY MONTH (surfable scenario)")
    print("=" * 70)
    surfable = all_events[all_events["scenario"] == "surfable"]
    if len(surfable) > 0:
        for month in cfg.SEASON_MONTHS:
            month_events = surfable[surfable["month"] == month]
            label = cfg.MONTH_LABELS.get(month, str(month))
            if len(month_events) > 0:
                print(f"  {label:>3}: {len(month_events)} events, "
                      f"avg duration {month_events['duration_hours'].mean():.1f}h, "
                      f"avg max height {month_events['max_height'].mean():.2f}m")
            else:
                print(f"  {label:>3}: 0 events")
    else:
        print("  No surfable events detected.")


if __name__ == "__main__":
    main()
