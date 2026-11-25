"""
03_climatologia_mensal.py — Monthly climatological analysis of swell events.

This is the Season equivalent of the March pipeline's 05_climatologia.py.
Instead of analyzing two weeks, it analyzes each month of the swell season
and answers the core Front 3 questions:

  1. Which months bring the most swell? (seasonality)
  2. How often does good swell arrive? (probability per month)
  3. What does a typical swell event look like? (duration, height, direction)

Statistical approach:
  - Wilson Score confidence interval for binomial proportions.
    Why Wilson instead of the normal approximation (p +/- z*sqrt(p(1-p)/n))?
    Wilson is more accurate with small sample sizes (like 1 year of data)
    and never produces impossible intervals below 0% or above 100%.
    As more years are added, both methods converge.

Outputs:
  - data/climatology/monthly_climatology.csv  — per-scenario, per-month stats
  - data/climatology/monthly_summary.csv      — per-year, per-month event summary
"""

import os

import numpy as np
import pandas as pd

import config as cfg


# ---------------------------------------------------------------------------
# Statistical helpers (same as March pipeline)
# ---------------------------------------------------------------------------

def wilson_ci(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """
    Wilson score interval for a binomial proportion.

    Given "successes out of trials", returns (lower, upper) bounds for
    the true probability at 95% confidence.

    Example: 3 events in 5 years -> p = 0.6, Wilson CI = (0.23, 0.88)
    With more data (30 events in 50 years), the CI narrows.
    """
    if trials == 0:
        return (0.0, 0.0)
    p_hat = successes / trials
    denom = 1 + z**2 / trials
    center = (p_hat + z**2 / (2 * trials)) / denom
    spread = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * trials)) / trials) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (round(lower, 4), round(upper, 4))


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
# Event detection within a single month-year block
# ---------------------------------------------------------------------------

def detect_events_in_block(
    df: pd.DataFrame,
    direction_key: str,
    period_min: float,
    height_min: float,
    gap_tolerance: int,
) -> list[dict]:
    """
    Detect events within a block of hourly data (e.g. one month of one year).
    Returns a list of event dicts with statistics.

    Same algorithm as 02_detectar_eventos_season.py but returns dicts
    instead of a DataFrame, for easier aggregation.
    """
    df = df.copy().sort_values("time").reset_index(drop=True)
    dir_ranges = cfg.DIRECTIONS[direction_key]

    df["qualifies"] = (
        df["swell_direction"].apply(lambda d: direction_matches(d, dir_ranges))
        & (df["swell_period"] >= period_min)
        & (df["swell_height"] >= height_min)
    )

    if df["qualifies"].sum() == 0:
        return []

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

    if in_event and event_rows:
        events.append(pd.DataFrame(event_rows))

    results: list[dict] = []
    for ev_df in events:
        dir_classes = ev_df["swell_direction"].apply(classify_direction)
        dir_counts = dir_classes.value_counts()
        results.append({
            "duration_hours": len(ev_df),
            "max_height": float(ev_df["swell_height"].max()),
            "mean_height": float(ev_df["swell_height"].mean()),
            "max_period": float(ev_df["swell_period"].max()),
            "mean_period": float(ev_df["swell_period"].mean()),
            "dominant_direction": dir_counts.index[0] if len(dir_counts) > 0 else "unknown",
            "n_hours_N": int((dir_classes == "N").sum()),
            "n_hours_NE": int((dir_classes == "NE").sum()),
        })

    return results


# ---------------------------------------------------------------------------
# Monthly climatology analysis
# ---------------------------------------------------------------------------

def analyze_month_scenario(
    df: pd.DataFrame,
    month: int,
    scenario: dict,
) -> dict:
    """
    Analyze one scenario for one month across all available years.

    For each year, checks whether that month had at least one qualifying
    event. The fraction of years with events gives the probability.

    Returns a dict with all statistics for this month+scenario combination.
    """
    all_years = sorted(df["year"].unique())
    total_years = len(all_years)

    yearly_had_event: dict[int, bool] = {}
    yearly_max_duration: dict[int, int] = {}
    yearly_n_events: dict[int, int] = {}
    all_events: list[dict] = []

    for year in all_years:
        month_df = df[(df["year"] == year) & (df["month"] == month)]

        if len(month_df) == 0:
            # This year might not have this month's data yet
            continue

        events = detect_events_in_block(
            month_df,
            cfg.DEFAULT_DIRECTION,
            scenario["period_min"],
            scenario["height_min"],
            cfg.GAP_TOLERANCE_HOURS,
        )

        yearly_had_event[year] = len(events) > 0
        yearly_n_events[year] = len(events)
        yearly_max_duration[year] = max((e["duration_hours"] for e in events), default=0)
        all_events.extend(events)

    # Only count years that actually have data for this month
    years_with_data = len(yearly_had_event)
    if years_with_data == 0:
        return {}

    years_with_event = sum(1 for v in yearly_had_event.values() if v)
    prob = years_with_event / years_with_data
    ci_low, ci_high = wilson_ci(years_with_event, years_with_data)

    # Duration stats
    durations = [e["duration_hours"] for e in all_events]
    heights = [e["max_height"] for e in all_events]
    periods = [e["max_period"] for e in all_events]

    # Surfable window probabilities
    window_probs: dict[str, float] = {}
    for w in cfg.WINDOW_DURATIONS:
        years_with_window = sum(
            1 for y in yearly_max_duration
            if yearly_max_duration[y] >= w
        )
        window_probs[f"prob_window_{w}h"] = (
            years_with_window / years_with_data if years_with_data > 0 else 0.0
        )

    # Direction breakdown
    total_n_hours = sum(e.get("n_hours_N", 0) for e in all_events)
    total_ne_hours = sum(e.get("n_hours_NE", 0) for e in all_events)
    total_dir_hours = total_n_hours + total_ne_hours

    month_label = cfg.MONTH_LABELS.get(month, str(month))

    row: dict = {
        "scenario": scenario["name"],
        "scenario_label": scenario["label"],
        "period_min": scenario["period_min"],
        "height_min": scenario["height_min"],
        "month": month,
        "month_label": month_label,
        "total_years": years_with_data,
        "years_with_event": years_with_event,
        "probability": round(prob, 4),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "total_events": len(all_events),
        "mean_events_per_year": round(len(all_events) / years_with_data, 2),
    }

    # Duration stats
    if durations:
        row.update({
            "duration_mean": round(np.mean(durations), 1),
            "duration_median": round(float(np.median(durations)), 1),
            "duration_max": max(durations),
            "duration_p75": round(float(np.percentile(durations, 75)), 1),
            "duration_p90": round(float(np.percentile(durations, 90)), 1),
        })
    else:
        row.update({
            "duration_mean": 0, "duration_median": 0, "duration_max": 0,
            "duration_p75": 0, "duration_p90": 0,
        })

    # Height stats
    if heights:
        row.update({
            "height_mean": round(np.mean(heights), 3),
            "height_median": round(float(np.median(heights)), 3),
            "height_max": round(max(heights), 3),
            "height_p75": round(float(np.percentile(heights, 75)), 3),
            "height_p90": round(float(np.percentile(heights, 90)), 3),
        })
    else:
        row.update({
            "height_mean": 0, "height_median": 0, "height_max": 0,
            "height_p75": 0, "height_p90": 0,
        })

    # Period stats
    if periods:
        row.update({
            "period_mean": round(np.mean(periods), 2),
            "period_median": round(float(np.median(periods)), 2),
            "period_max": round(max(periods), 2),
        })
    else:
        row.update({
            "period_mean": 0, "period_median": 0, "period_max": 0,
        })

    # Window probabilities
    row.update(window_probs)

    # Direction
    row["pct_N"] = round(100 * total_n_hours / total_dir_hours, 1) if total_dir_hours > 0 else 0.0
    row["pct_NE"] = round(100 * total_ne_hours / total_dir_hours, 1) if total_dir_hours > 0 else 0.0

    return row


def build_monthly_summary(df: pd.DataFrame, scenario: dict) -> pd.DataFrame:
    """
    Build a per-year, per-month summary table for one scenario.

    This is the data behind the "Monthly Heatmap" component:
    rows = years, columns = months, cells = event intensity.
    """
    all_years = sorted(df["year"].unique())
    rows: list[dict] = []

    for year in all_years:
        for month in cfg.SEASON_MONTHS:
            month_df = df[(df["year"] == year) & (df["month"] == month)]

            if len(month_df) == 0:
                continue

            events = detect_events_in_block(
                month_df,
                cfg.DEFAULT_DIRECTION,
                scenario["period_min"],
                scenario["height_min"],
                cfg.GAP_TOLERANCE_HOURS,
            )

            had_event = len(events) > 0
            n_events = len(events)
            max_height = max((e["max_height"] for e in events), default=0.0)
            max_period = max((e["max_period"] for e in events), default=0.0)
            max_duration = max((e["duration_hours"] for e in events), default=0)
            total_hours = sum(e["duration_hours"] for e in events)

            # Dominant direction
            total_n = sum(e.get("n_hours_N", 0) for e in events)
            total_ne = sum(e.get("n_hours_NE", 0) for e in events)
            dom_dir = "N" if total_n > total_ne else ("NE" if total_ne > total_n else "-")

            rows.append({
                "year": year,
                "month": month,
                "month_label": cfg.MONTH_LABELS.get(month, str(month)),
                "had_event": had_event,
                "n_events": n_events,
                "total_hours": total_hours,
                "max_height": round(max_height, 3),
                "max_period": round(max_period, 2),
                "max_duration": max_duration,
                "dominant_direction": dom_dir if had_event else "-",
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("MONTHLY CLIMATOLOGY — Ceara Swell (Front 3)")
    print("=" * 70)
    print()

    if not os.path.exists(cfg.SEASON_CSV):
        print(f"Season CSV not found: {cfg.SEASON_CSV}")
        print("Run 01_consolidar_season.py first.")
        return

    df = pd.read_csv(cfg.SEASON_CSV, parse_dates=["time"])
    scenarios = cfg.SCENARIOS_ERA5

    print(f"Loaded {len(df)} rows")
    print(f"Years: {df['year'].min()}-{df['year'].max()} "
          f"({df['year'].nunique()} years)")
    print()

    # --- Monthly climatology for all scenarios ---
    all_results: list[dict] = []

    for scenario in scenarios:
        print(f"--- Scenario: {scenario['name']} ---")

        for month in cfg.SEASON_MONTHS:
            result = analyze_month_scenario(df, month, scenario)
            if result:
                all_results.append(result)
                label = cfg.MONTH_LABELS.get(month, str(month))
                prob_pct = result["probability"] * 100
                ci_pct = (result["ci_low"] * 100, result["ci_high"] * 100)
                print(f"  {label:>3}: {result['years_with_event']}/{result['total_years']} = "
                      f"{prob_pct:.0f}% [{ci_pct[0]:.0f}%-{ci_pct[1]:.0f}%], "
                      f"{result['total_events']} events, "
                      f"dur: {result['duration_mean']:.1f}h avg")
        print()

    # Save climatology results
    os.makedirs(cfg.CLIMATOLOGY_DIR, exist_ok=True)
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df.to_csv(cfg.MONTHLY_CLIMATOLOGY_CSV, index=False)
        print(f"Climatology saved to: {cfg.MONTHLY_CLIMATOLOGY_CSV}")
    else:
        print("No results to save.")

    # --- Monthly summary (for heatmap) ---
    print()
    print("=" * 70)
    print("MONTHLY SUMMARY — 'surfable' scenario")
    print("(period >= 9.0s, Hs >= 0.8m, direction N/NE)")
    print("=" * 70)

    surfable_scenario = next(s for s in scenarios if s["name"] == "surfable")
    summary = build_monthly_summary(df, surfable_scenario)

    if len(summary) > 0:
        summary.to_csv(cfg.MONTHLY_SUMMARY_CSV, index=False)
        print(f"Summary saved to: {cfg.MONTHLY_SUMMARY_CSV}")
        print()

        # Print the heatmap-style table
        for year in sorted(summary["year"].unique()):
            year_data = summary[summary["year"] == year]
            cells: list[str] = []
            for month in cfg.SEASON_MONTHS:
                month_row = year_data[year_data["month"] == month]
                if len(month_row) == 0:
                    cells.append("  -  ")
                elif month_row.iloc[0]["had_event"]:
                    n = month_row.iloc[0]["n_events"]
                    h = month_row.iloc[0]["max_height"]
                    cells.append(f"{n}e/{h:.1f}m")
                else:
                    cells.append("  0  ")

            month_headers = [cfg.MONTH_LABELS.get(m, str(m)) for m in cfg.SEASON_MONTHS]
            if year == sorted(summary["year"].unique())[0]:
                print(f"      {'  '.join(f'{h:>8}' for h in month_headers)}")
            print(f"  {year}  {'  '.join(f'{c:>8}' for c in cells)}")
    else:
        print("  No data for summary.")


if __name__ == "__main__":
    main()
