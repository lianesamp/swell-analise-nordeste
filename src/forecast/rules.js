/**
 * Surf rules for Praia de Iracema.
 *
 * JS port of forecast/rules.py — the domain logic that decides
 * whether conditions are surfable and how good they are.
 *
 * All functions are pure (no side effects, no API calls).
 * They take data in, return a result — easy to test.
 */

import {
  SWELL_DIR_RANGES,
  SWELL_HEIGHT_MIN,
  SWELL_PERIOD_MIN,
  TIDE_MAX_HEIGHT,
  TIDE_ROCKS_WARNING,
  ENERGY_SURFABLE,
  RHO_SEAWATER,
  G,
  RATING_THRESHOLDS,
} from "./config.js";

/**
 * Calculate wave energy density in J/m2.
 *
 * Formula: E = (1/16) * rho * g * Hs^2
 * Same metric SurfGuru displays on their energy chart.
 *
 * @param {number} height - Significant wave height in meters
 * @returns {number} Energy in J/m2
 */
export function waveEnergy(height) {
  return (1 / 16) * RHO_SEAWATER * G * height ** 2;
}

/**
 * Check if swell direction is valid for Iracema.
 *
 * Iracema accepts N (330-360) through E (0-90).
 * The "FROM" convention means 0 = from North, 90 = from East.
 *
 * @param {number} direction - Swell direction in degrees (FROM convention)
 * @returns {boolean}
 */
export function isDirectionValid(direction) {
  return SWELL_DIR_RANGES.some(
    ([start, end]) => direction >= start && direction <= end
  );
}

/**
 * Determine if conditions are surfable at Iracema.
 *
 * Three conditions must all be true:
 * 1. Direction from N to E
 * 2. Wave energy >= 400 J/m2
 * 3. Tide between 0.0m and 1.5m (below 0.6m = rocks warning)
 *
 * @param {{ height: number, direction: number, period: number }} swell
 * @param {number} tideHeight - Meters above chart datum
 * @returns {boolean}
 */
export function isSurfable(swell, tideHeight) {
  if (!isDirectionValid(swell.direction)) return false;
  if (swell.height < SWELL_HEIGHT_MIN) return false;
  if (swell.period < SWELL_PERIOD_MIN) return false;
  if (waveEnergy(swell.height) < ENERGY_SURFABLE) return false;
  if (tideHeight > TIDE_MAX_HEIGHT) return false;
  return true;
}

/**
 * Rate surf quality from "flat" to "great".
 *
 * Based on energy + period, with tide phase as a modifier:
 * - Draining tide boosts the rating one step (sandbars more exposed)
 *
 * @param {{ height: number, direction: number, period: number }} swell
 * @param {number} tideHeight
 * @param {string} tidePhase - "draining" | "low" | "filling" | "high" | "unknown"
 * @returns {"flat" | "poor" | "fair" | "good" | "great"}
 */
export function rateConditions(swell, tideHeight, tidePhase) {
  if (!isSurfable(swell, tideHeight)) {
    return waveEnergy(swell.height) < ENERGY_SURFABLE ? "flat" : "poor";
  }

  const energy = waveEnergy(swell.height);
  const upgrade = { fair: "good", good: "great" };

  for (const rating of ["great", "good", "fair"]) {
    const { energyMin, periodMin } = RATING_THRESHOLDS[rating];
    if (energy >= energyMin && swell.period >= periodMin) {
      // Draining tide improves rating one step
      if (tidePhase === "draining" && rating !== "great") {
        return upgrade[rating] || rating;
      }
      return rating;
    }
  }

  return "fair"; // met isSurfable but below named thresholds
}

/**
 * Generate safety warnings based on tide conditions.
 *
 * @param {number} tideHeight
 * @param {string} tidePhase
 * @returns {string[]}
 */
export function getWarnings(tideHeight, tidePhase) {
  const warnings = [];
  if (tideHeight < TIDE_ROCKS_WARNING) {
    warnings.push("Rocks exposed! Careful with maneuvers");
  }
  return warnings;
}
