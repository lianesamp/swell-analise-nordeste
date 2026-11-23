"""
1D Wave Transformation Model — Shoaling + Refraction.

Python port of src/forecast/waveTransform.js.

Converts offshore swell data (from Open-Meteo's 28km grid) into
nearshore estimates at Praia de Iracema using linear wave theory.

The physics (see waveTransform.js for detailed explanations):
1. Shoaling: Ks = sqrt(cg_offshore / cg_local)
2. Refraction: Kr = sqrt(cos(angle_offshore) / cos(angle_local))
3. Breaking: H_max = 0.78 × depth

All functions are pure (no side effects).
"""

import json
import math
import os

import config as cfg
from models import SwellHour

# Path to the bathymetry JSON (same data as public/data/ in the frontend)
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_BATHY_FILE = os.path.join(_DATA_DIR, "bathymetry_iracema.json")

BREAKING_INDEX = 0.78


def load_bathymetry() -> list[dict]:
    """Load the bathymetry transect from the JSON file."""
    with open(_BATHY_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["transect"]


def solve_dispersion(period: float, depth: float) -> float:
    """
    Solve the wave dispersion relation for wave number k.

    omega^2 = g × k × tanh(k × h)

    Uses Newton-Raphson iteration (5-10 steps to converge).

    Parameters
    ----------
    period : float
        Wave period in seconds.
    depth : float
        Water depth in meters (positive).

    Returns
    -------
    float
        Wave number k in radians per meter.
    """
    omega = (2 * math.pi) / period
    omega2 = omega ** 2

    # Deep water approximation as initial guess
    k = omega2 / cfg.G

    for _ in range(20):
        tanh_kh = math.tanh(k * depth)
        f = omega2 - cfg.G * k * tanh_kh
        # f'(k) = -g × (tanh(kh) + kh × sech^2(kh))
        sech2 = 1 - tanh_kh ** 2
        f_prime = -cfg.G * (tanh_kh + k * depth * sech2)

        if abs(f_prime) < 1e-15:
            break

        k_next = k - f / f_prime
        if abs(k_next - k) < 1e-10:
            break
        k = k_next

    return max(k, 1e-10)


def phase_velocity(period: float, depth: float) -> float:
    """Calculate wave phase velocity (celerity) at a given depth."""
    omega = (2 * math.pi) / period
    k = solve_dispersion(period, depth)
    return omega / k


def group_velocity(period: float, depth: float) -> float:
    """
    Calculate wave group velocity at a given depth.

    cg = (c / 2) × (1 + 2kh / sinh(2kh))
    """
    k = solve_dispersion(period, depth)
    omega = (2 * math.pi) / period
    c = omega / k
    kh = k * depth

    sinh_2kh = math.sinh(2 * kh)
    if sinh_2kh > 1e-10:
        n = 0.5 * (1 + (2 * kh) / sinh_2kh)
    else:
        n = 1.0  # very shallow water limit

    return n * c


def transform_wave(
    height: float,
    period: float,
    direction: float,
    transect: list[dict],
) -> tuple[float, float]:
    """
    Transform a single wave from offshore to nearshore along a transect.

    Parameters
    ----------
    height : float
        Offshore significant wave height (meters).
    period : float
        Wave period (seconds).
    direction : float
        Wave direction FROM, in degrees (0=N, 90=E).
    transect : list[dict]
        Depth profile from offshore to nearshore.

    Returns
    -------
    tuple[float, float]
        (nearshore_height, nearshore_direction)
    """
    if len(transect) < 2:
        return height, direction

    shore_normal = 0.0  # Iracema faces due north
    angle_rad = math.radians(direction - shore_normal)

    H = height
    prev_depth = transect[0]["depth"]

    for i in range(1, len(transect)):
        curr_depth = transect[i]["depth"]

        if curr_depth < 0.5 or H <= 0:
            break

        c_prev = phase_velocity(period, prev_depth)
        c_curr = phase_velocity(period, curr_depth)

        # Refraction — Snell's law
        sin_prev = math.sin(angle_rad)
        sin_curr = sin_prev * (c_curr / c_prev)

        if abs(sin_curr) >= 1:
            break  # total internal reflection

        angle_curr_rad = math.asin(sin_curr)

        cos_prev = math.cos(angle_rad)
        cos_curr = math.cos(angle_curr_rad)

        Kr = 1.0
        if cos_curr > 1e-10 and cos_prev > 1e-10:
            Kr = math.sqrt(cos_prev / cos_curr)

        # Shoaling
        cg_prev = group_velocity(period, prev_depth)
        cg_curr = group_velocity(period, curr_depth)

        Ks = 1.0
        if cg_curr > 1e-10:
            Ks = math.sqrt(cg_prev / cg_curr)

        H = H * Ks * Kr

        # Depth-limited breaking
        max_H = BREAKING_INDEX * curr_depth
        if H > max_H:
            H = max_H

        angle_rad = angle_curr_rad
        prev_depth = curr_depth

    nearshore_dir = (shore_normal + math.degrees(angle_rad)) % 360
    return max(H, 0.0), nearshore_dir


def transform_waves(
    swell_data: list[SwellHour],
    transect: list[dict] | None = None,
) -> list[SwellHour]:
    """
    Transform an array of offshore swell hours to nearshore values.

    Parameters
    ----------
    swell_data : list[SwellHour]
        Offshore swell from Open-Meteo.
    transect : list[dict], optional
        Bathymetry profile. If None, loads from file.

    Returns
    -------
    list[SwellHour]
        Transformed nearshore swell data (same shape).
    """
    if transect is None:
        transect = load_bathymetry()

    result = []
    for swell in swell_data:
        nearshore_h, nearshore_dir = transform_wave(
            swell.height, swell.period, swell.direction, transect
        )
        result.append(SwellHour(
            time=swell.time,
            height=round(nearshore_h, 2),
            direction=round(nearshore_dir, 1),
            period=swell.period,
        ))

    return result
