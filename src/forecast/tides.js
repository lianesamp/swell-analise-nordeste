/**
 * Tide data loading and interpolation for Porto de Mucuripe.
 *
 * JS port of forecast/tide_mucuripe.py.
 *
 * Loads the static tide table (high/low events) from a JSON file
 * served from public/data/, then provides two key functions:
 *
 * - interpolateTideHeight(time, tides) — estimate height at any moment
 * - getTidePhase(time, tides) — is the tide draining, low, filling, or high?
 *
 * Key concept: "Chart datum" is the reference level (roughly the lowest
 * astronomical tide). Heights are in meters above chart datum. So 0.0m
 * is very low water, 3.0m is a very high spring tide.
 */

/**
 * Fetch and parse the tide JSON from the public directory.
 *
 * Returns an array of { time: Date, height: number, type: "high"|"low" }
 * sorted by time.
 *
 * @returns {Promise<Array<{ time: Date, height: number, type: string }>>}
 */
export async function loadTides() {
  const response = await fetch("/data/tide_mucuripe_2026.json");
  if (!response.ok) {
    throw new Error(`Failed to load tide data: ${response.status}`);
  }

  const raw = await response.json();
  return raw.map((entry) => ({
    time: new Date(entry.time),
    height: entry.height,
    type: entry.type,
  }));
}

/**
 * Find the tide events that bracket a given time (one before, one after).
 *
 * This is a helper used by both interpolation and phase detection.
 *
 * @param {Date} time
 * @param {Array<{ time: Date, height: number, type: string }>} tides
 * @returns {{ before: object|null, after: object|null }}
 */
function findBracketingTides(time, tides) {
  let before = null;
  let after = null;

  for (const tide of tides) {
    if (tide.time <= time) {
      before = tide;
    } else if (after === null) {
      after = tide;
    }
  }

  return { before, after };
}

/**
 * Estimate tide height at an arbitrary time using linear interpolation.
 *
 * Real tides follow a sinusoidal curve, so linear interpolation between
 * high/low events is an approximation — but good enough for "is it too
 * high to surf?" checks. A proper model would use harmonic constituents.
 *
 * Compare with Laravel: this is like a simple lerp() helper.
 *
 * @param {Date} time - The moment to estimate
 * @param {Array<{ time: Date, height: number, type: string }>} tides
 * @returns {number} Height in meters above chart datum
 */
export function interpolateTideHeight(time, tides) {
  if (!tides.length) return 1.5; // fallback: assume mid-tide

  const { before, after } = findBracketingTides(time, tides);

  if (!before && after) return after.height;
  if (!after && before) return before.height;
  if (!before && !after) return 1.5;

  const totalMs = after.time - before.time;
  if (totalMs === 0) return before.height;

  const fraction = (time - before.time) / totalMs;
  return before.height + fraction * (after.height - before.height);
}

/**
 * Determine the tide phase at a given time.
 *
 * Returns one of:
 * - "draining" (secando) — falling from high toward low
 * - "low"     (seca)    — near a low tide event (within ~30 min)
 * - "filling" (enchendo) — rising from low toward high
 * - "high"    (preamar)  — near a high tide event (within ~30 min)
 * - "unknown"            — not enough data
 *
 * Why this matters for surfing:
 * - Draining = sandbars more exposed = waves break better
 * - Low = max exposure but rocks risk below 0.6m
 * - Filling = still OK but getting deeper
 * - High = too deep, waves don't break
 *
 * @param {Date} time
 * @param {Array<{ time: Date, height: number, type: string }>} tides
 * @returns {string}
 */
export function getTidePhase(time, tides) {
  if (!tides.length) return "unknown";

  const { before, after } = findBracketingTides(time, tides);

  if (!before || !after) return "unknown";

  // Close to an event? (~30 min)
  const minsSinceBefore = (time - before.time) / 60000;
  const minsUntilAfter = (after.time - time) / 60000;

  if (minsSinceBefore < 30) return before.type; // "high" or "low"
  if (minsUntilAfter < 30) return after.type;

  // Between events: check if falling or rising
  if (before.type === "high" && after.type === "low") return "draining";
  if (before.type === "low" && after.type === "high") return "filling";

  return "unknown";
}
