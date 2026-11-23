/**
 * Configuration for the Praia de Iracema surf forecast.
 *
 * Energy thresholds are calibrated to SurfGuru's scale (~400 J/m2 = surfable).
 * Open-Meteo gives offshore swell heights, and the wave transformation module
 * (waveTransform.js) converts them to nearshore values using shoaling +
 * refraction physics along a GEBCO bathymetry transect.
 *
 * This replaces the previous 2x empirical correction with actual physics.
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

// Wave energy threshold (J/m2) — calibrated to SurfGuru's nearshore scale
// The wave transformation module handles offshore → nearshore conversion
export const ENERGY_SURFABLE = 400;

// Physical constants
export const RHO_SEAWATER = 1025; // kg/m3
export const G = 9.81;            // m/s2

// Rating thresholds — energy (J/m2) + minimum period (SurfGuru scale)
export const RATING_THRESHOLDS = {
  great: { energyMin: 800, periodMin: 8.0 },
  good:  { energyMin: 500, periodMin: 5.0 },
  fair:  { energyMin: 400, periodMin: 4.0 },
};

// --- Wave transformation ---
// Breaking index: waves break when height > BREAKING_INDEX × depth
// 0.78 is the standard value from linear wave theory (McCowan, 1894)
export const BREAKING_INDEX = 0.78;

// --- Open-Meteo Marine API ---
export const OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine";
export const FORECAST_DAYS = 7;

// --- Tide reference ---
export const TIDE_STATION = "Porto de Mucuripe";
export const TIDE_TIMEZONE = "America/Fortaleza";
