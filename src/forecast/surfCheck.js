/**
 * Surf check orchestration — combines swell, tide and rules.
 *
 * JS port of forecast/surf_check.py.
 *
 * This is the "brain" that takes raw API data + tide events,
 * evaluates every hour with the Iracema rules, and groups
 * consecutive surfable hours into windows.
 *
 * Compare with Laravel: this is like a Service class — it
 * coordinates multiple data sources and returns a clean result.
 */

import {
  OFFSHORE_LAT,
  OFFSHORE_LON,
  FORECAST_DAYS,
  OPEN_METEO_MARINE_URL,
} from "./config.js";
import { isSurfable, rateConditions, waveEnergy, getWarnings } from "./rules.js";
import { interpolateTideHeight, getTidePhase } from "./tides.js";

/**
 * Fetch swell forecast from the Open-Meteo Marine API.
 *
 * Open-Meteo is free, no API key, supports CORS — so we can call
 * it directly from the browser with fetch(). This replaces the
 * Python version that used urllib.
 *
 * The API returns parallel arrays (one for time, one per variable),
 * which we zip into objects — same pattern as the Python version.
 *
 * @returns {Promise<Array<{ time: Date, height: number, direction: number, period: number }>>}
 */
export async function fetchSwell() {
  const params = new URLSearchParams({
    latitude: OFFSHORE_LAT,
    longitude: OFFSHORE_LON,
    hourly: "swell_wave_height,swell_wave_direction,swell_wave_period",
    forecast_days: FORECAST_DAYS,
    timezone: "America/Fortaleza",
  });

  const response = await fetch(`${OPEN_METEO_MARINE_URL}?${params}`);
  if (!response.ok) {
    throw new Error(`Open-Meteo API error: ${response.status}`);
  }

  const data = await response.json();
  const hourly = data.hourly || {};
  const times = hourly.time || [];
  const heights = hourly.swell_wave_height || [];
  const directions = hourly.swell_wave_direction || [];
  const periods = hourly.swell_wave_period || [];

  if (!times.length) {
    throw new Error("Open-Meteo returned empty forecast data");
  }

  // Zip parallel arrays into objects, skipping nulls
  const result = [];
  for (let i = 0; i < times.length; i++) {
    if (heights[i] == null || directions[i] == null || periods[i] == null) {
      continue;
    }
    result.push({
      time: new Date(times[i]),
      height: heights[i],
      direction: directions[i],
      period: periods[i],
    });
  }

  return result;
}

/**
 * Convert degrees to a compass label (N, NE, E, etc.).
 *
 * @param {number} degrees
 * @returns {string}
 */
export function directionLabel(degrees) {
  const labels = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
  ];
  const index = Math.round(degrees / 22.5) % 16;
  return labels[index];
}

/**
 * Run the full surf check: rate every hour and group into windows.
 *
 * This is the main function the hook calls. It takes raw data
 * (already fetched) and returns surf windows — keeping the
 * "fetch" and "process" steps separate for testability.
 *
 * @param {Array<{ time: Date, height: number, direction: number, period: number }>} swellData
 * @param {Array<{ time: Date, height: number, type: string }>} tideData
 * @returns {Array<object>} Surf windows
 */
export function runSurfCheck(swellData, tideData) {
  // Rate each hour
  const surfableHours = [];

  for (const swell of swellData) {
    const tideH = interpolateTideHeight(swell.time, tideData);
    const tidePhase = getTidePhase(swell.time, tideData);
    const warnings = getWarnings(tideH, tidePhase);
    const rating = rateConditions(swell, tideH, tidePhase);

    if (rating === "fair" || rating === "good" || rating === "great") {
      surfableHours.push({
        time: swell.time,
        swell,
        tideHeight: tideH,
        tidePhase,
        warnings,
        rating,
      });
    }
  }

  // Group consecutive surfable hours into windows
  return groupIntoWindows(surfableHours);
}

/**
 * Group consecutive surfable hours into windows.
 *
 * A 1-hour gap is tolerated (2h between timestamps) to avoid
 * splitting windows that have one marginal hour in the middle.
 * Same logic as the Python version and the historical event detection.
 *
 * @param {Array<object>} ratedHours
 * @returns {Array<object>} Surf windows
 */
function groupIntoWindows(ratedHours) {
  if (!ratedHours.length) return [];

  const windows = [];
  let currentGroup = [ratedHours[0]];

  for (let i = 1; i < ratedHours.length; i++) {
    const prevTime = currentGroup[currentGroup.length - 1].time;
    const gapHours = (ratedHours[i].time - prevTime) / 3600000;

    if (gapHours <= 2) {
      currentGroup.push(ratedHours[i]);
    } else {
      windows.push(groupToWindow(currentGroup));
      currentGroup = [ratedHours[i]];
    }
  }

  // Don't forget the last group
  windows.push(groupToWindow(currentGroup));
  return windows;
}

/**
 * Convert a group of consecutive rated hours into a surf window object.
 *
 * Uses circular mean for direction averaging (you can't just average
 * 350 and 10 degrees — that gives 180, which is wrong).
 *
 * @param {Array<object>} group
 * @returns {object} Surf window
 */
function groupToWindow(group) {
  const n = group.length;
  const avgHeight = group.reduce((s, h) => s + h.swell.height, 0) / n;
  const avgPeriod = group.reduce((s, h) => s + h.swell.period, 0) / n;
  const avgEnergy = group.reduce((s, h) => s + waveEnergy(h.swell.height), 0) / n;

  // Circular mean for direction
  const sinSum = group.reduce(
    (s, h) => s + Math.sin((h.swell.direction * Math.PI) / 180), 0
  );
  const cosSum = group.reduce(
    (s, h) => s + Math.cos((h.swell.direction * Math.PI) / 180), 0
  );
  const avgDir = (((Math.atan2(sinSum / n, cosSum / n) * 180) / Math.PI) + 360) % 360;

  // Best rating determines the window rating
  const ratingOrder = { great: 3, good: 2, fair: 1 };
  const best = group.reduce((a, b) =>
    (ratingOrder[b.rating] || 0) > (ratingOrder[a.rating] || 0) ? b : a
  );

  // Tide phases summary: "draining > LOW > filling"
  const phasesSeen = [];
  for (const h of group) {
    const phase = h.tidePhase || "unknown";
    if (!phasesSeen.length || phasesSeen[phasesSeen.length - 1] !== phase) {
      phasesSeen.push(phase);
    }
  }
  const phaseLabels = {
    draining: "draining",
    filling: "filling",
    low: "LOW",
    high: "HIGH",
    unknown: "?",
  };
  const phaseSummary = phasesSeen.map((p) => phaseLabels[p] || p).join(" > ");

  // Collect unique warnings
  const allWarnings = [];
  for (const h of group) {
    for (const w of h.warnings) {
      if (!allWarnings.includes(w)) {
        allWarnings.push(w);
      }
    }
  }

  // End time is 1 hour after the last hour in the group
  const endTime = new Date(group[group.length - 1].time.getTime() + 3600000);

  return {
    start: group[0].time,
    end: endTime,
    rating: best.rating,
    swellHeightAvg: Math.round(avgHeight * 100) / 100,
    swellPeriodAvg: Math.round(avgPeriod * 10) / 10,
    swellDirAvg: Math.round(avgDir),
    energyAvg: Math.round(avgEnergy),
    tideHeightAtPeak: Math.round(best.tideHeight * 100) / 100,
    tidePhaseSummary: phaseSummary,
    warnings: allWarnings,
  };
}
