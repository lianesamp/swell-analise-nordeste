"""
05_climatologia.py — Climatological analysis of swell events.

Computes per-scenario, per-week:
  - Annual occurrence probability with Wilson 95% CI
  - Event count, duration stats
  - Surfable window probability (>=3h, >=6h, >=12h, >=24h)
  - Height/period distributions and percentiles
  - Direction breakdown (N vs NE)
  - Annual summary table
  - Week comparison (McNemar)
  - Exploratory trend analysis

Output:
  - data/climatology/climatologia_resultados.csv
  - Console summary tables
"""

import os
import warnings
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

import config as cfg


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def wilson_ci(successes: int, trials: int, z: float = 1.96) -> tuple:
    """Wilson score interval for a binomial proportion."""
    if trials == 0:
        return (0.0, 0.0)
    p_hat = successes / trials
    denom = 1 + z**2 / trials
    center = (p_hat + z**2 / (2 * trials)) / denom
    spread = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * trials)) / trials) / denom
    lower = max(0, center - spread)
    upper = min(1, center + spread)
    return (round(lower, 4), round(upper, 4))


def direction_matches(direction: float, ranges: list) -> bool:
    for low, high in ranges:
        if low <= direction <= high:
            return True
    return False


def classify_direction(direction: float) -> str:
    for name in ["N", "NE"]:
        if direction_matches(direction, cfg.DIRECTIONS[name]):
            return name
    return "other"


# ---------------------------------------------------------------------------
# Event detection (per-week version)
# ---------------------------------------------------------------------------

def detect_events_in_window(
    df: pd.DataFrame,
    direction_key: str,
    period_min: float,
    height_min: float,
    gap_tolerance: int,
) -> list:
    """Detect events in a DataFrame. Returns list of event dicts."""
    df = df.copy().sort_values("time").reset_index(drop=True)
    dir_ranges = cfg.DIRECTIONS[direction_key]

    df["qualifies"] = (
        df["swell_direction"].apply(lambda d: direction_matches(d, dir_ranges))
        & (df["swell_period"] >= period_min)
        & (df["swell_height"] >= height_min)
    )

    if df["qualifies"].sum() == 0:
        return []

    events = []
    in_event = False
    event_rows = []
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

    result = []
    for ev_df in events:
        dir_classes = ev_df["swell_direction"].apply(classify_direction)
        dir_counts = dir_classes.value_counts()
        result.append({
            "duration_hours": len(ev_df),
            "max_height": ev_df["swell_height"].max(),
            "mean_height": ev_df["swell_height"].mean(),
            "max_period": ev_df["swell_period"].max(),
            "mean_period": ev_df["swell_period"].mean(),
            "dominant_direction": dir_counts.index[0] if len(dir_counts) > 0 else "unknown",
            "n_hours_N": int((dir_classes == "N").sum()),
            "n_hours_NE": int((dir_classes == "NE").sum()),
        })

    return result


# ---------------------------------------------------------------------------
# Main climatology analysis
# ---------------------------------------------------------------------------

def analyze_scenario(df: pd.DataFrame, scenario: dict, source: str) -> list:
    """Analyze one scenario across all weeks and years."""
    rows = []
    total_years = df["year"].nunique()
    all_years = sorted(df["year"].unique())

    for week_key, week_info in cfg.MARCH_WINDOWS.items():
        start_day = week_info["start_day"]
        end_day = week_info["end_day"]
        week_label = week_info["label"]

        # Per-year analysis
        yearly_had_event = {}
        yearly_max_duration = {}
        yearly_n_events = {}
        all_events_this_week = []

        for year in all_years:
            year_week_df = df[(df["year"] == year) & (df["day"] >= start_day) & (df["day"] <= end_day)]

            events = detect_events_in_window(
                year_week_df,
                cfg.DEFAULT_DIRECTION,
                scenario["period_min"],
                scenario["height_min"],
                cfg.GAP_TOLERANCE_HOURS,
            )

            yearly_had_event[year] = len(events) > 0
            yearly_n_events[year] = len(events)
            yearly_max_duration[year] = max((e["duration_hours"] for e in events), default=0)
            all_events_this_week.extend(events)

        # Occurrence probability
        years_with_event = sum(1 for v in yearly_had_event.values() if v)
        prob = years_with_event / total_years if total_years > 0 else 0
        ci_low, ci_high = wilson_ci(years_with_event, total_years)

        # Duration stats
        durations = [e["duration_hours"] for e in all_events_this_week]
        heights = [e["max_height"] for e in all_events_this_week]
        periods = [e["max_period"] for e in all_events_this_week]

        # Surfable window probabilities
        window_probs = {}
        for w in cfg.WINDOW_DURATIONS:
            years_with_window = sum(
                1 for y in all_years if yearly_max_duration.get(y, 0) >= w
            )
            window_probs[f"prob_window_{w}h"] = years_with_window / total_years if total_years > 0 else 0

        # Direction breakdown
        total_n_hours = sum(e.get("n_hours_N", 0) for e in all_events_this_week)
        total_ne_hours = sum(e.get("n_hours_NE", 0) for e in all_events_this_week)
        total_dir_hours = total_n_hours + total_ne_hours

        row = {
            "source": source,
            "scenario": scenario["name"],
            "scenario_label": scenario["label"],
            "period_min": scenario["period_min"],
            "height_min": scenario["height_min"],
            "week": week_key,
            "week_label": week_label,
            "total_years": total_years,
            "years_with_event": years_with_event,
            "probability": round(prob, 4),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "total_events": len(all_events_this_week),
            "mean_events_per_year": round(len(all_events_this_week) / total_years, 2) if total_years > 0 else 0,
        }

        # Duration stats
        if durations:
            row.update({
                "duration_mean": round(np.mean(durations), 1),
                "duration_median": round(np.median(durations), 1),
                "duration_max": max(durations),
                "duration_p75": round(np.percentile(durations, 75), 1),
                "duration_p90": round(np.percentile(durations, 90), 1),
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
                "height_median": round(np.median(heights), 3),
                "height_max": round(max(heights), 3),
                "height_p75": round(np.percentile(heights, 75), 3),
                "height_p90": round(np.percentile(heights, 90), 3),
                "height_p95": round(np.percentile(heights, 95), 3),
            })
        else:
            row.update({
                "height_mean": 0, "height_median": 0, "height_max": 0,
                "height_p75": 0, "height_p90": 0, "height_p95": 0,
            })

        # Period stats
        if periods:
            row.update({
                "period_mean": round(np.mean(periods), 2),
                "period_median": round(np.median(periods), 2),
                "period_max": round(max(periods), 2),
                "period_p75": round(np.percentile(periods, 75), 2),
                "period_p90": round(np.percentile(periods, 90), 2),
            })
        else:
            row.update({
                "period_mean": 0, "period_median": 0, "period_max": 0,
                "period_p75": 0, "period_p90": 0,
            })

        # Window probabilities
        row.update(window_probs)

        # Direction
        row["pct_N"] = round(100 * total_n_hours / total_dir_hours, 1) if total_dir_hours > 0 else 0
        row["pct_NE"] = round(100 * total_ne_hours / total_dir_hours, 1) if total_dir_hours > 0 else 0

        rows.append(row)

    return rows


def build_annual_summary(df: pd.DataFrame, scenario: dict) -> pd.DataFrame:
    """Build per-year summary for the main scenario."""
    all_years = sorted(df["year"].unique())
    rows = []

    for year in all_years:
        for week_key, week_info in cfg.MARCH_WINDOWS.items():
            start_day = week_info["start_day"]
            end_day = week_info["end_day"]

            year_week_df = df[(df["year"] == year) & (df["day"] >= start_day) & (df["day"] <= end_day)]

            events = detect_events_in_window(
                year_week_df,
                cfg.DEFAULT_DIRECTION,
                scenario["period_min"],
                scenario["height_min"],
                cfg.GAP_TOLERANCE_HOURS,
            )

            had_event = len(events) > 0
            n_events = len(events)
            max_height = max((e["max_height"] for e in events), default=0)
            max_period = max((e["max_period"] for e in events), default=0)
            max_duration = max((e["duration_hours"] for e in events), default=0)
            total_hours = sum(e["duration_hours"] for e in events)

            # Dominant direction
            total_n = sum(e.get("n_hours_N", 0) for e in events)
            total_ne = sum(e.get("n_hours_NE", 0) for e in events)
            dom_dir = "N" if total_n > total_ne else ("NE" if total_ne > total_n else "-")

            rows.append({
                "year": year,
                "week": week_key,
                "had_event": had_event,
                "n_events": n_events,
                "total_hours": total_hours,
                "max_height": round(max_height, 3),
                "max_period": round(max_period, 2),
                "max_duration": max_duration,
                "dominant_direction": dom_dir if had_event else "-",
            })

    return pd.DataFrame(rows)


def mcnemar_test(annual_summary: pd.DataFrame) -> dict:
    """McNemar test comparing week3 vs week4 (paired by year)."""
    w3 = annual_summary[annual_summary["week"] == "week3"].set_index("year")["had_event"]
    w4 = annual_summary[annual_summary["week"] == "week4"].set_index("year")["had_event"]

    common_years = w3.index.intersection(w4.index)
    w3 = w3.loc[common_years]
    w4 = w4.loc[common_years]

    # Contingency: (w3=yes,w4=no), (w3=no,w4=yes)
    b = int(((w3 == True) & (w4 == False)).sum())   # w3 yes, w4 no
    c = int(((w3 == False) & (w4 == True)).sum())    # w3 no, w4 yes

    n = b + c
    if n == 0:
        return {"b": b, "c": c, "n_discordant": n, "p_value": 1.0, "interpretation": "No discordant pairs"}

    # McNemar exact (binomial) for small samples
    p_value = scipy_stats.binom_test(b, n, 0.5) if hasattr(scipy_stats, 'binom_test') else 1.0
    # scipy >= 1.7 deprecated binom_test in favor of binomtest
    try:
        result = scipy_stats.binomtest(b, n, 0.5)
        p_value = result.pvalue
    except AttributeError:
        pass

    return {
        "b_w3_only": b,
        "c_w4_only": c,
        "n_discordant": n,
        "p_value": round(p_value, 4),
    }


def trend_test(annual_summary: pd.DataFrame, metric: str = "had_event") -> dict:
    """Simple Mann-Kendall-like trend test using Spearman correlation."""
    years = annual_summary.groupby("year")[metric].max()
    if len(years) < 10:
        return {"test": "insufficient_data"}

    x = np.arange(len(years))
    y = years.values.astype(float)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rho, p_value = scipy_stats.spearmanr(x, y)

    return {
        "metric": metric,
        "spearman_rho": round(rho, 4) if not np.isnan(rho) else 0,
        "p_value": round(p_value, 4) if not np.isnan(p_value) else 1.0,
        "n_years": len(years),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("CLIMATOLOGICAL ANALYSIS — Ceará Swell")
    print("=" * 70)
    print()

    if not os.path.exists(cfg.ERA5_CSV):
        print(f"ERA5 CSV not found: {cfg.ERA5_CSV}")
        print("Run 02_consolidar_era5.py first.")
        return

    df = pd.read_csv(cfg.ERA5_CSV, parse_dates=["time"])
    source = "ERA5"
    scenarios = cfg.SCENARIOS_ERA5

    print(f"Source: {source}")
    print(f"Total rows: {len(df)}")
    print(f"Years: {df['year'].min()}–{df['year'].max()} ({df['year'].nunique()} years)")
    print()

    # Run all scenarios
    all_results = []
    for scenario in scenarios:
        print(f"--- Scenario: {scenario['name']} ---")
        results = analyze_scenario(df, scenario, source)
        all_results.extend(results)

        for r in results:
            prob_pct = r["probability"] * 100
            ci_pct = (r["ci_low"] * 100, r["ci_high"] * 100)
            print(f"  {r['week_label']}: {r['years_with_event']}/{r['total_years']} = "
                  f"{prob_pct:.1f}% [{ci_pct[0]:.1f}%–{ci_pct[1]:.1f}%], "
                  f"{r['total_events']} events, "
                  f"dur: {r['duration_mean']:.1f}h avg / {r['duration_max']}h max")
        print()

    # Save results
    os.makedirs(cfg.CLIMATOLOGY_DIR, exist_ok=True)
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(cfg.CLIMATOLOGY_CSV, index=False)
    print(f"Results saved to: {cfg.CLIMATOLOGY_CSV}")
    print()

    # Annual summary for the "good" scenario
    print("=" * 70)
    print("ANNUAL SUMMARY — 'good' scenario (period >= 9.0s, Hs >= 1.0m)")
    print("=" * 70)
    good_scenario = next(s for s in scenarios if s["name"] == "good")
    annual = build_annual_summary(df, good_scenario)
    annual_path = os.path.join(cfg.CLIMATOLOGY_DIR, "resumo_anual_era5.csv")
    annual.to_csv(annual_path, index=False)
    print(f"Saved to: {annual_path}")
    print()

    # Print annual summary table
    for week_key in ["week3", "week4"]:
        week_data = annual[annual["week"] == week_key]
        week_label = cfg.MARCH_WINDOWS[week_key]["label"]
        n_with = week_data["had_event"].sum()
        n_total = len(week_data)
        print(f"  {week_label}: {n_with}/{n_total} years with event")
        for _, row in week_data.iterrows():
            if row["had_event"]:
                print(f"    {row['year']}: {row['n_events']} events, "
                      f"max Hs={row['max_height']:.2f}m, "
                      f"max Tp={row['max_period']:.1f}s, "
                      f"max dur={row['max_duration']}h, "
                      f"dir={row['dominant_direction']}")
        print()

    # McNemar test
    print("=" * 70)
    print("WEEK COMPARISON — McNemar test (paired by year)")
    print("=" * 70)
    mcnemar = mcnemar_test(annual)
    print(f"  Years with event only in week3: {mcnemar['b_w3_only']}")
    print(f"  Years with event only in week4: {mcnemar['c_w4_only']}")
    print(f"  Discordant pairs: {mcnemar['n_discordant']}")
    print(f"  p-value: {mcnemar['p_value']}")
    if mcnemar['p_value'] < 0.05:
        print("  -> Statistically significant difference between weeks")
    else:
        print("  -> No statistically significant difference between weeks")
    print()

    # Trend analysis
    print("=" * 70)
    print("TREND ANALYSIS (exploratory)")
    print("=" * 70)
    for metric in ["had_event", "total_hours", "max_height"]:
        trend = trend_test(annual, metric)
        if "test" in trend and trend["test"] == "insufficient_data":
            print(f"  {metric}: insufficient data for trend test")
        else:
            sig = "significant" if trend["p_value"] < 0.05 else "not significant"
            print(f"  {metric}: rho={trend['spearman_rho']}, p={trend['p_value']} ({sig})")
    print()

    # Surfable windows summary
    print("=" * 70)
    print("SURFABLE WINDOW PROBABILITIES")
    print("=" * 70)
    for scenario in scenarios:
        sc_results = [r for r in all_results if r["scenario"] == scenario["name"]]
        print(f"\n  {scenario['name']} (Tp >= {scenario['period_min']}s, Hs >= {scenario['height_min']}m):")
        for r in sc_results:
            windows = []
            for w in cfg.WINDOW_DURATIONS:
                p = r.get(f"prob_window_{w}h", 0)
                windows.append(f">={w}h: {100*p:.0f}%")
            print(f"    {r['week_label']}: {', '.join(windows)}")


if __name__ == "__main__":
    main()
