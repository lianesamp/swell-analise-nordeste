/**
 * 1D Wave Transformation Model — Shoaling + Refraction.
 *
 * Converts offshore swell data (from Open-Meteo's 28km grid) into
 * nearshore estimates at Praia de Iracema using linear wave theory.
 *
 * The physics:
 * As waves travel from deep water toward shore, two things happen:
 *
 * 1. SHOALING — the seafloor forces waves to slow down. Because energy
 *    flux must be conserved (energy in = energy out), the wave height
 *    changes. In most cases, waves get taller as they approach shore.
 *    Formula: Ks = sqrt(cg_offshore / cg_local)
 *
 * 2. REFRACTION — because waves slow down in shallow water, the part
 *    of the wave front in shallower water falls behind. This bends
 *    the wave toward shore (like light through a lens). The bending
 *    spreads or focuses energy, changing the wave height.
 *    Formula: Kr = sqrt(cos(angle_offshore) / cos(angle_local))
 *    Direction change: Snell's law — sin(a)/c = constant
 *
 * 3. BREAKING — waves can't be taller than ~78% of the water depth.
 *    When they exceed this, they break and lose energy.
 *
 * Result: H_nearshore = min(H_offshore × Ks × Kr, 0.78 × depth)
 *
 * Compare with Laravel/backend:
 * This is like a "transformer" or "middleware" that sits between the
 * raw API data and the business rules — it doesn't change the data
 * format, just adjusts the values to be more accurate.
 *
 * All functions are pure (no side effects). The only "hard" math is
 * the dispersion relation solver (Newton-Raphson iteration).
 */

import { G, BREAKING_INDEX } from "./config.js";

/**
 * Solve the wave dispersion relation for wave number k.
 *
 * The dispersion relation links wave period, wavelength, and water depth:
 *   omega^2 = g × k × tanh(k × h)
 *
 * where:
 *   omega = 2π / T (angular frequency)
 *   k = 2π / L (wave number, inverse of wavelength)
 *   h = water depth
 *   g = gravity
 *
 * This equation can't be solved algebraically for k — you have to
 * iterate. We use Newton-Raphson, which converges in 5-10 steps.
 *
 * New concept — Newton-Raphson method:
 * An iterative algorithm for finding roots of f(x) = 0.
 * Start with a guess x0, then repeatedly compute:
 *   x_next = x - f(x) / f'(x)
 * Each step gets closer to the root. It's the standard numerical
 * method for this kind of problem in oceanography.
 *
 * @param {number} period - Wave period in seconds
 * @param {number} depth - Water depth in meters (positive)
 * @returns {number} Wave number k in radians per meter
 */
export function solveDispersion(period, depth) {
  const omega = (2 * Math.PI) / period;
  const omega2 = omega * omega;

  // Deep water approximation as initial guess: k0 = omega^2 / g
  let k = omega2 / G;

  // Newton-Raphson iteration
  for (let i = 0; i < 20; i++) {
    const tanhKh = Math.tanh(k * depth);
    const f = omega2 - G * k * tanhKh;
    // Derivative: f'(k) = -g × (tanh(kh) + kh × sech^2(kh))
    // sech^2(x) = 1 - tanh^2(x)
    const sech2 = 1 - tanhKh * tanhKh;
    const fPrime = -G * (tanhKh + k * depth * sech2);

    if (Math.abs(fPrime) < 1e-15) break; // avoid division by zero

    const kNext = k - f / fPrime;
    if (Math.abs(kNext - k) < 1e-10) break; // converged
    k = kNext;
  }

  return Math.max(k, 1e-10); // safety: never return zero
}

/**
 * Calculate wave phase velocity (celerity) at a given depth.
 *
 * c = omega / k = wavelength / period
 *
 * In deep water: c ≈ gT / (2π) — depends only on period
 * In shallow water: c ≈ sqrt(g × h) — depends only on depth
 *
 * @param {number} period - Wave period in seconds
 * @param {number} depth - Water depth in meters
 * @returns {number} Phase velocity in m/s
 */
export function phaseVelocity(period, depth) {
  const omega = (2 * Math.PI) / period;
  const k = solveDispersion(period, depth);
  return omega / k;
}

/**
 * Calculate wave group velocity at a given depth.
 *
 * Group velocity is the speed at which wave ENERGY propagates.
 * It's different from phase velocity (the speed of individual crests).
 *
 * cg = (c / 2) × (1 + 2kh / sinh(2kh))
 *
 * In deep water: cg = c/2 (energy moves at half the crest speed)
 * In shallow water: cg = c (energy moves with the crests)
 *
 * This is the key quantity for shoaling: energy flux = E × cg = constant
 *
 * @param {number} period - Wave period in seconds
 * @param {number} depth - Water depth in meters
 * @returns {number} Group velocity in m/s
 */
export function groupVelocity(period, depth) {
  const k = solveDispersion(period, depth);
  const omega = (2 * Math.PI) / period;
  const c = omega / k;
  const kh = k * depth;

  // n = cg/c = 0.5 × (1 + 2kh / sinh(2kh))
  const sinh2kh = Math.sinh(2 * kh);
  const n = sinh2kh > 1e-10
    ? 0.5 * (1 + (2 * kh) / sinh2kh)
    : 1.0; // very shallow water limit: n → 1

  return n * c;
}

/**
 * Transform a single wave from offshore to nearshore along a transect.
 *
 * Walks step by step through the bathymetry profile, applying shoaling
 * and refraction at each depth change. If the wave exceeds the breaking
 * limit at any point, it breaks and energy is lost.
 *
 * This is the main function — it combines all the physics.
 *
 * @param {number} height - Offshore significant wave height (meters)
 * @param {number} period - Wave period (seconds)
 * @param {number} direction - Wave direction FROM, in degrees (0=N, 90=E)
 * @param {Array<{depth: number}>} transect - Depth profile, offshore to nearshore
 * @returns {{ height: number, direction: number }} Transformed nearshore values
 */
export function transformWave(height, period, direction, transect) {
  if (!transect.length || transect.length < 2) {
    return { height, direction };
  }

  // Convert direction to angle relative to shore-normal
  // Iracema faces north, so shore-normal is ~0° (from north)
  // Wave angle = how far off shore-normal the wave is coming from
  // A wave from 0° (N) hits Iracema head-on (angle = 0)
  // A wave from 45° (NE) arrives at 45° angle
  const shoreNormal = 0; // degrees — Iracema faces due north
  let angleRad = ((direction - shoreNormal) * Math.PI) / 180;

  let H = height;
  let prevDepth = transect[0].depth;

  for (let i = 1; i < transect.length; i++) {
    const currDepth = transect[i].depth;

    // Skip if depth is very shallow (< 0.5m) or we've already broken
    if (currDepth < 0.5 || H <= 0) break;

    // Phase velocities at previous and current depths
    const cPrev = phaseVelocity(period, prevDepth);
    const cCurr = phaseVelocity(period, currDepth);

    // --- Refraction (Snell's law) ---
    // sin(angle) / c = constant along a wave ray
    const sinAnglePrev = Math.sin(angleRad);
    const sinAngleCurr = sinAnglePrev * (cCurr / cPrev);

    // Check for total internal reflection (wave can't propagate)
    if (Math.abs(sinAngleCurr) >= 1) break;

    const angleCurrRad = Math.asin(sinAngleCurr);

    // Refraction coefficient: Kr = sqrt(cos(prev) / cos(curr))
    const cosAnglePrev = Math.cos(angleRad);
    const cosAngleCurr = Math.cos(angleCurrRad);

    let Kr = 1;
    if (cosAngleCurr > 1e-10 && cosAnglePrev > 1e-10) {
      Kr = Math.sqrt(cosAnglePrev / cosAngleCurr);
    }

    // --- Shoaling coefficient ---
    const cgPrev = groupVelocity(period, prevDepth);
    const cgCurr = groupVelocity(period, currDepth);

    let Ks = 1;
    if (cgCurr > 1e-10) {
      Ks = Math.sqrt(cgPrev / cgCurr);
    }

    // Apply transformation
    H = H * Ks * Kr;

    // --- Depth-limited breaking ---
    const maxH = BREAKING_INDEX * currDepth;
    if (H > maxH) {
      H = maxH; // wave breaks, height is capped
    }

    // Update state for next step
    angleRad = angleCurrRad;
    prevDepth = currDepth;
  }

  // Convert angle back to compass direction
  const nearshoreDir = (shoreNormal + (angleRad * 180) / Math.PI + 360) % 360;

  return {
    height: Math.max(H, 0),
    direction: nearshoreDir,
  };
}

/**
 * Load the bathymetry transect from the static JSON file.
 *
 * @returns {Promise<Array<{depth: number, distanceKm: number, lat: number, lon: number}>>}
 */
export async function loadBathymetry() {
  const response = await fetch("/data/bathymetry_iracema.json");
  if (!response.ok) {
    throw new Error(`Failed to load bathymetry: ${response.status}`);
  }
  const data = await response.json();
  return data.transect;
}

/**
 * Transform an array of offshore swell hours to nearshore values.
 *
 * This is the function the hook calls — it takes the raw Open-Meteo
 * data and returns corrected nearshore values.
 *
 * The input/output shape is identical (same fields), so the rest of
 * the pipeline doesn't need to change. Only the height and direction
 * values are modified.
 *
 * @param {Array<{time: Date, height: number, direction: number, period: number}>} swellData
 * @param {Array<{depth: number}>} transect
 * @returns {Array<{time: Date, height: number, direction: number, period: number}>}
 */
export function transformWaves(swellData, transect) {
  return swellData.map((swell) => {
    const { height: nearshoreH, direction: nearshoreDir } = transformWave(
      swell.height,
      swell.period,
      swell.direction,
      transect
    );

    return {
      ...swell,
      height: Math.round(nearshoreH * 100) / 100,
      direction: Math.round(nearshoreDir * 10) / 10,
      // period doesn't change through shoaling/refraction
    };
  });
}
