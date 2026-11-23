/**
 * Configuration for the Praia de Iracema surf forecast.
 *
 * This is the JS port of forecast/config.py — same constants,
 * same comments, just different syntax.
 *
 * All the surfability thresholds here come from local knowledge:
 * years of surfing Iracema and cross-referencing with SurfGuru's
 * energy chart.
 */

// --- Spot definition ---
export const SPOT_NAME = "Praia de Iracema";
export const SPOT_LAT = -3.7217;
export const SPOT_LON = -38.5133;

// Open-Meteo uses a 28km grid — we query the nearest offshore point
export const OFFSHORE_LAT = -3.5;
export const OFFSHORE_LON = -38.5;

// --- Surfability rules ---
// Direction: N through E (FROM convention, wraps around 0)
export const SWELL_DIR_RANGES = [
  [330.0, 360.0],
  [0.0, 90.0],
];

export const SWELL_HEIGHT_MIN = 0.6;   // meters — below this, flat
export const SWELL_PERIOD_MIN = 4.0;   // seconds — low bar; energy is what matters
export const TIDE_MAX_HEIGHT = 1.5;    // above this, too deep
export const TIDE_ROCKS_WARNING = 0.6; // below this, rocks exposed

// Wave energy threshold (J/m2) — the key metric for Iracema
export const ENERGY_SURFABLE = 400;

// Physical constants
export const RHO_SEAWATER = 1025; // kg/m3
export const G = 9.81;            // m/s2

// Rating thresholds — energy (J/m2) + minimum period
export const RATING_THRESHOLDS = {
  great: { energyMin: 800, periodMin: 8.0 },
  good:  { energyMin: 500, periodMin: 5.0 },
  fair:  { energyMin: 400, periodMin: 4.0 },
};

// --- Open-Meteo Marine API ---
export const OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine";
export const FORECAST_DAYS = 7;

// --- Tide reference ---
export const TIDE_STATION = "Porto de Mucuripe";
export const TIDE_TIMEZONE = "America/Fortaleza";
