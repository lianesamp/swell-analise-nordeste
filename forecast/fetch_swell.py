"""
Fetch 7-day wave forecast from the Open-Meteo Marine API.

Open-Meteo is a free weather API that requires no API key for
non-commercial use.  It uses the DWD (German Weather Service) global
wave model at 28km resolution, updated twice daily.

We fetch TOTAL wave_height (swell + wind waves) because that's what
determines surf energy at Iracema.  The trade winds add significant
chop that contributes to breaking.  SurfGuru's "Total Energy" chart
(our calibration reference) also uses the combined total.

We use SWELL direction for the direction filter — it's the swell
from N/NE that reaches Iracema's north-facing beach.  Wind waves
come from ESE (trade winds) and don't indicate surfability.

Docs: https://open-meteo.com/en/docs/marine-weather-api
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

from models import SwellHour
import config as cfg


def fetch_swell(
    lat: float = cfg.OFFSHORE_LAT,
    lon: float = cfg.OFFSHORE_LON,
    forecast_days: int = cfg.FORECAST_DAYS,
) -> list[SwellHour]:
    """
    Fetch hourly swell forecast from Open-Meteo.

    Returns a list of SwellHour objects, one per hour, for the next
    `forecast_days` days.  Each SwellHour is Pydantic-validated.

    Parameters
    ----------
    lat, lon : float
        Offshore point to query.  Open-Meteo snaps to the nearest
        grid cell (28km resolution).
    forecast_days : int
        Number of days to forecast (1–16, default 7).

    Raises
    ------
    ConnectionError
        If the API is unreachable or returns an error.
    ValueError
        If the response data is malformed or fails validation.
    """
    # Build the query URL
    # The API accepts parameters as query strings, similar to ERDDAP
    params = (
        f"latitude={lat}"
        f"&longitude={lon}"
        f"&hourly=wave_height,wave_period,swell_wave_direction"
        f"&forecast_days={forecast_days}"
        f"&timezone=America/Fortaleza"
    )
    url = f"{cfg.OPEN_METEO_MARINE_URL}?{params}"

    # Make the HTTP request using stdlib urllib
    # (no `requests` library needed — keeping dependencies minimal)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to reach Open-Meteo API: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from Open-Meteo API: {e}") from e

    # Parse the response
    # Open-Meteo returns parallel arrays: one for times, one per variable
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    heights = hourly.get("wave_height", [])
    directions = hourly.get("swell_wave_direction", [])
    periods = hourly.get("wave_period", [])

    if not times:
        raise ValueError("Open-Meteo returned empty forecast data")

    # Zip the parallel arrays into validated SwellHour objects
    # This is where Pydantic catches any bad data from the API
    result: list[SwellHour] = []
    for i, time_str in enumerate(times):
        # Skip hours where any value is None (API sometimes returns nulls)
        if heights[i] is None or directions[i] is None or periods[i] is None:
            continue

        result.append(SwellHour(
            time=datetime.fromisoformat(time_str),
            height=heights[i],
            direction=directions[i],
            period=periods[i],
        ))

    return result
