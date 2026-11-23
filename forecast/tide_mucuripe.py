"""
Tide data for Porto de Mucuripe (Fortaleza, Ceará).

Loads the static tide table from a JSON file.  The data comes from the
Marinha do Brasil (Brazilian Navy) tide predictions for the Mucuripe
port station — the official reference for Fortaleza.

The JSON file contains high/low tide events with times and heights in
meters above chart datum.  Chart datum is roughly the lowest astronomical
tide — so 0.0m means the water is as low as it gets, and 3.0m means
a very high spring tide.

For now this is a static file covering Nov–Dec 2026.  Future versions
could scrape the data or use harmonic constants to predict any date.

Data source: https://mareagora.com.br/mare/ceara/porto-de-mucuripe-fortaleza
(based on Marinha do Brasil official predictions)
"""

import json
import os
from datetime import datetime

from models import TideEvent


# Path to the tide data JSON file
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_TIDE_FILE = os.path.join(_DATA_DIR, "tide_mucuripe_2026.json")


def load_all_tides() -> list[TideEvent]:
    """Load all tide events from the JSON file."""
    with open(_TIDE_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    return [
        TideEvent(
            time=datetime.fromisoformat(entry["time"]),
            height=entry["height"],
            type=entry["type"],
        )
        for entry in raw
    ]


def get_tides(start: datetime, end: datetime) -> list[TideEvent]:
    """
    Get tide events within a date range.

    Parameters
    ----------
    start, end : datetime
        The range to filter (inclusive on both sides).

    Returns
    -------
    list[TideEvent]
        Tide events sorted by time, within the range.
    """
    all_tides = load_all_tides()
    return [t for t in all_tides if start <= t.time <= end]


def interpolate_tide_height(time: datetime, tides: list[TideEvent]) -> float:
    """
    Estimate the tide height at an arbitrary time by linear interpolation.

    Tides follow a roughly sinusoidal pattern, so linear interpolation
    between adjacent high/low events is a simplification — but good
    enough for our "is it too high to surf?" check.  A proper tidal
    model would use harmonic constituents, but that's overkill here.

    Parameters
    ----------
    time : datetime
        The moment to estimate.
    tides : list[TideEvent]
        Sorted list of tide events (from get_tides or load_all_tides).

    Returns
    -------
    float
        Estimated height in meters above chart datum.
    """
    if not tides:
        return 1.5  # fallback: assume mid-tide if no data

    # Find the two tide events that bracket this time
    before = None
    after = None
    for tide in tides:
        if tide.time <= time:
            before = tide
        elif after is None:
            after = tide

    # Edge cases: time is before or after all tide data
    if before is None and after is not None:
        return after.height
    if after is None and before is not None:
        return before.height
    if before is None and after is None:
        return 1.5

    # Linear interpolation between the two bracketing events
    total_seconds = (after.time - before.time).total_seconds()
    if total_seconds == 0:
        return before.height

    fraction = (time - before.time).total_seconds() / total_seconds
    return before.height + fraction * (after.height - before.height)


def get_tide_phase(time: datetime, tides: list[TideEvent]) -> str:
    """
    Determine the tide phase at a given time.

    Returns one of:
    - "draining" (secando) — tide is falling from high toward low
    - "low"     (seca)    — near the low tide event (within ~30 min)
    - "filling" (enchendo) — tide is rising from low toward high
    - "high"    (preamar)  — near the high tide event (within ~30 min)
    - "unknown"            — not enough data

    This matters for surfing because the phase tells you if conditions
    are improving or deteriorating:
    - Draining = sandbar exposed more, waves start breaking better
    - Low = maximum exposure, but risk of rocks if too shallow
    - Filling = still good but getting deeper
    - High = too deep, waves don't break

    Parameters
    ----------
    time : datetime
        The moment to check.
    tides : list[TideEvent]
        Sorted list of tide events.
    """
    if not tides:
        return "unknown"

    # Find the bracketing events
    before = None
    after = None
    for tide in tides:
        if tide.time <= time:
            before = tide
        elif after is None:
            after = tide

    if before is None or after is None:
        return "unknown"

    # Close to an event? (~30 min)
    mins_since_before = (time - before.time).total_seconds() / 60
    mins_until_after = (after.time - time).total_seconds() / 60

    if mins_since_before < 30:
        return before.type   # "high" or "low"
    if mins_until_after < 30:
        return after.type

    # Between events: check if falling or rising
    if before.type == "high" and after.type == "low":
        return "draining"
    if before.type == "low" and after.type == "high":
        return "filling"

    return "unknown"
