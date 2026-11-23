"""
Surf rules for Praia de Iracema.

This module encodes local knowledge about when Iracema is surfable.
It's the "domain logic" of the forecast — the part that makes this
project more than a generic data display.

The rules are specific to Iracema's geography:
- It's a shallow beach break facing north
- N through ENE swell reaches the beach; E swell wraps around the headland
- High tide drowns the sandbars — the sweet spot is roughly 0.6m–1.5m
- Below 0.6m rocks get exposed — only for experienced surfers
- The PRIMARY metric is wave energy (J/m2), not period alone
  (SurfGuru's energy chart shows ~400 J/m2 as the threshold for Iracema)

Tide phases matter:
- "draining" (secando): tide falling, sandbars becoming exposed = improving
- "low" (seca): maximum exposure, but rocks risk below 0.6m
- "filling" (enchendo): still good, but getting deeper = deteriorating
- "high" (preamar): too deep, waves don't break

Wave energy formula: E = (1/16) x rho x g x Hs^2
  - rho = seawater density = 1025 kg/m3
  - g = gravity = 9.81 m/s2
  - Hs = significant wave height (meters)
  - E is in Joules per square meter (J/m2)
"""

import config as cfg
from models import SwellHour


def wave_energy(height: float) -> float:
    """
    Calculate wave energy density in J/m2.

    E = (1/16) x rho x g x Hs^2

    This is the same metric SurfGuru displays on their energy chart.
    For Iracema, ~400 J/m2 is the threshold where waves start breaking.
    """
    return (1 / 16) * cfg.RHO_SEAWATER * cfg.G * height ** 2


def is_direction_valid(direction: float) -> bool:
    """
    Check if the swell direction falls within the accepted ranges.

    Iracema accepts swell from NNW (330) through North (0) to E (90).
    This wraps around 0 degrees, so we need multiple ranges.

    The FROM convention means direction = where the swell comes FROM.
    330 degrees = from the NNW, 76 degrees = from the ENE.
    """
    for range_start, range_end in cfg.SWELL_DIR_RANGES:
        if range_start <= direction <= range_end:
            return True
    return False


def is_surfable(swell: SwellHour, tide_height: float) -> bool:
    """
    Determine if conditions are surfable at Iracema.

    Three conditions must be met simultaneously:
    1. Swell direction is from N to E
    2. Wave energy >= 400 J/m2 (the key metric for Iracema)
    3. Tide is in the right range (0.6m–1.5m ideal; below 0.6m = rocks)

    Parameters
    ----------
    swell : SwellHour
        One hour of swell forecast.
    tide_height : float
        Estimated tide height at this hour (meters above chart datum).
    """
    if not is_direction_valid(swell.direction):
        return False
    if swell.height < cfg.SWELL_HEIGHT_MIN:
        return False
    if swell.period < cfg.SWELL_PERIOD_MIN:
        return False
    if wave_energy(swell.height) < cfg.ENERGY_SURFABLE:
        return False
    if tide_height > cfg.TIDE_MAX_HEIGHT:
        return False
    return True


def rate_conditions(swell: SwellHour, tide_height: float, tide_phase: str) -> str:
    """
    Rate the surf quality from "flat" to "great".

    The rating is primarily based on wave energy (J/m2), with
    tide height and phase as modifiers.

    Returns one of: "flat", "poor", "fair", "good", "great".

    "flat" and "poor" mean don't bother going.
    "fair" means possible but not ideal.
    "good" and "great" mean worth the trip.
    """
    if not is_surfable(swell, tide_height):
        energy = wave_energy(swell.height)
        if energy < cfg.ENERGY_SURFABLE:
            return "flat"
        return "poor"

    energy = wave_energy(swell.height)

    # Check thresholds from best to worst
    for rating in ("great", "good", "fair"):
        thresholds = cfg.RATING_THRESHOLDS[rating]
        if (energy >= thresholds["energy_min"]
                and swell.period >= thresholds["period_min"]):
            # Draining tide improves the rating one step
            # (sandbars becoming more exposed = better waves)
            if tide_phase == "draining" and rating != "great":
                better = {"fair": "good", "good": "great"}
                return better.get(rating, rating)
            return rating

    return "fair"  # met is_surfable but below all named thresholds


def get_warnings(tide_height: float, tide_phase: str) -> list[str]:
    """
    Generate safety warnings based on tide conditions.

    Returns a list of warning strings (empty if no warnings).
    """
    warnings: list[str] = []
    if tide_height < cfg.TIDE_ROCKS_WARNING:
        warnings.append("Rocks exposed! Careful with maneuvers")
    return warnings
