/**
 * Configuration for the Praia de Iracema surf forecast.
 *
 * This is the JS port of forecast/config.py — same constants,
 * same comments, just different syntax.
 *
 * IMPORTANT — Model calibration note:
 * The original 400 J/m2 threshold was calibrated against SurfGuru,
 * which runs WaveWatch III with coastal-refined grids (1/16 degree).
 * Open-Meteo uses DWD GWAM at 0.25 degree (28km) — an offshore
 * global model that gives ~2x higher swell heights because it doesn't
 * account for coastal attenuation (refraction, shoaling, bathymetry).
 *
 * To compensate, all energy thresholds are doubled:
 *   SurfGuru 400 J → Open-Meteo ~800 J
 *   SurfGuru 500 J → Open-Meteo ~1000 J
 *   SurfGuru 800 J → Open-Meteo ~1600 J
 *
 * This is an approximation — the 2x factor may vary with swell
 * direction and period. Cross-reference with SurfGuru over a few
 * sessions to refine.
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
// Doubled from SurfGuru's 400 J to compensate for Open-Meteo's offshore model
export const ENERGY_SURFABLE = 800;

// Physical constants
export const RHO_SEAWATER = 1025; // kg/m3
export const G = 9.81;            // m/s2

// Rating thresholds — energy (J/m2) + minimum period
// Doubled from SurfGuru scale (400/500/800) to Open-Meteo scale (800/1000/1600)
export const RATING_THRESHOLDS = {
  great: { energyMin: 1600, periodMin: 8.0 },
  good:  { energyMin: 1000, periodMin: 5.0 },
  fair:  { energyMin: 800,  periodMin: 4.0 },
};

// --- Open-Meteo Marine API ---
export const OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine";
export const FORECAST_DAYS = 7;

// --- Tide reference ---
export const TIDE_STATION = "Porto de Mucuripe";
export const TIDE_TIMEZONE = "America/Fortaleza";
