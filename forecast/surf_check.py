"""
Surf check orchestration — combines swell, tide and rules.

This is the main "brain" of the forecast module.  It:
1. Fetches the 7-day swell forecast from Open-Meteo
2. Transforms offshore swell → nearshore using wave physics
3. Loads the tide table for the period
4. For each hour, evaluates surfability using rules.py
5. Groups consecutive surfable hours into "windows"
6. Returns a list of SurfWindow objects ready for display

This is similar to how doc_swell/scripts/04_detectar_eventos.py
groups consecutive hours into events, but instead of historical
detection it's forward-looking forecast.
"""

from datetime import datetime, timedelta

from models import SwellHour, SurfWindow, TideEvent
from fetch_swell import fetch_swell
from wave_transform import transform_waves
from tide_mucuripe import get_tides, interpolate_tide_height, get_tide_phase
from rules import is_surfable, rate_conditions, wave_energy, get_warnings


def _group_into_windows(
    rated_hours: list[dict],
) -> list[SurfWindow]:
    """
    Group consecutive surfable hours into windows.

    Similar to the event detection in 04_detectar_eventos.py:
    consecutive hours meeting the criteria are merged into a
    single window with averaged swell stats.

    A 1-hour gap is tolerated (same as GAP_TOLERANCE_HOURS in
    the historical pipeline) to avoid splitting windows that
    have one marginal hour in the middle.
    """
    if not rated_hours:
        return []

    windows: list[SurfWindow] = []
    current_group: list[dict] = [rated_hours[0]]

    for hour_data in rated_hours[1:]:
        prev_time = current_group[-1]["time"]
        gap = (hour_data["time"] - prev_time).total_seconds() / 3600

        if gap <= 2:  # allow 1-hour gap (2h between timestamps)
            current_group.append(hour_data)
        else:
            windows.append(_group_to_window(current_group))
            current_group = [hour_data]

    # Don't forget the last group
    windows.append(_group_to_window(current_group))

    return windows


def _group_to_window(group: list[dict]) -> SurfWindow:
    """Convert a group of consecutive rated hours into a SurfWindow."""
    n = len(group)
    avg_height = sum(h["swell"].height for h in group) / n
    avg_period = sum(h["swell"].period for h in group) / n
    avg_energy = sum(wave_energy(h["swell"].height) for h in group) / n

    # Circular mean for direction (can't just average 350° and 10°)
    import math
    sin_sum = sum(math.sin(math.radians(h["swell"].direction)) for h in group)
    cos_sum = sum(math.cos(math.radians(h["swell"].direction)) for h in group)
    avg_dir = math.degrees(math.atan2(sin_sum / n, cos_sum / n)) % 360

    # Best rating in the window determines the window rating
    rating_order = {"great": 3, "good": 2, "fair": 1}
    best = max(group, key=lambda h: rating_order.get(h["rating"], 0))

    # Tide at the best-rated hour
    tide_at_peak = best["tide_height"]

    # Summarize tide phases: show unique phases in order
    # e.g. "draining > low > filling"
    phases_seen: list[str] = []
    for h in group:
        phase = h.get("tide_phase", "unknown")
        if not phases_seen or phases_seen[-1] != phase:
            phases_seen.append(phase)
    phase_labels = {
        "draining": "draining",
        "filling": "filling",
        "low": "LOW",
        "high": "HIGH",
        "unknown": "?",
    }
    phase_summary = " > ".join(phase_labels.get(p, p) for p in phases_seen)

    # Collect unique warnings from all hours
    all_warnings: list[str] = []
    for h in group:
        for w in h.get("warnings", []):
            if w not in all_warnings:
                all_warnings.append(w)

    return SurfWindow(
        start=group[0]["time"],
        end=group[-1]["time"] + timedelta(hours=1),
        rating=best["rating"],
        swell_height_avg=round(avg_height, 2),
        swell_period_avg=round(avg_period, 1),
        swell_dir_avg=round(avg_dir, 0),
        energy_avg=round(avg_energy, 0),
        tide_height_at_peak=round(tide_at_peak, 2),
        tide_phase_summary=phase_summary,
        warnings=all_warnings,
    )


def direction_label(degrees: float) -> str:
    """Convert degrees to a compass label (N, NE, E, etc.)."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]


def run_surf_check() -> tuple[list[SwellHour], list[TideEvent], list[SurfWindow]]:
    """
    Run the full surf check pipeline.

    Returns
    -------
    swell_data : list[SwellHour]
        Raw swell forecast (for display/debugging).
    tide_data : list[TideEvent]
        Tide events in the forecast period.
    windows : list[SurfWindow]
        Surfable windows found, sorted by time.
    """
    # 1. Fetch offshore swell forecast
    offshore_data = fetch_swell()

    if not offshore_data:
        return [], [], []

    # 2. Transform offshore → nearshore using wave physics
    swell_data = transform_waves(offshore_data)

    # 3. Get tides for the forecast period
    start = swell_data[0].time
    end = swell_data[-1].time
    tide_data = get_tides(start, end)

    # 4. Rate each hour
    surfable_hours: list[dict] = []
    for swell in swell_data:
        tide_h = interpolate_tide_height(swell.time, tide_data)
        tide_phase = get_tide_phase(swell.time, tide_data)
        warnings = get_warnings(tide_h, tide_phase)
        rating = rate_conditions(swell, tide_h, tide_phase)

        if rating in ("fair", "good", "great"):
            surfable_hours.append({
                "time": swell.time,
                "swell": swell,
                "tide_height": tide_h,
                "tide_phase": tide_phase,
                "warnings": warnings,
                "rating": rating,
            })

    # 5. Group into windows
    windows = _group_into_windows(surfable_hours)

    return swell_data, tide_data, windows
