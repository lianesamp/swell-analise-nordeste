import { useEffect, useState, useRef } from "react";
import { fetchSwell, runSurfCheck } from "../forecast/surfCheck.js";
import { loadTides } from "../forecast/tides.js";
import { loadBathymetry, transformWaves } from "../forecast/waveTransform.js";

/**
 * Custom hook that fetches the 7-day surf forecast for Praia de Iracema.
 *
 * Follows the same pattern as useCearaData:
 * - Module-level cache so data is fetched once per page load
 * - Shared promise so multiple components don't duplicate requests
 * - Cleanup ref to prevent state updates on unmounted components
 *
 * Data pipeline:
 * 1. Fetch offshore swell from Open-Meteo API
 * 2. Load bathymetry transect (static JSON, GEBCO data)
 * 3. Load tide table (static JSON, Marinha do Brasil)
 * 4. Transform offshore → nearshore using shoaling + refraction physics
 * 5. Run surf rules on the nearshore (transformed) data
 *
 * Both offshore and nearshore swell data are returned so the chart
 * can display both lines for comparison.
 *
 * Usage:
 *   const { offshoreData, swellData, tideData, surfWindows, loading, error } = useForecastData();
 */

// Module-level cache — same approach as useCearaData
const cache = {
  offshoreData: null,
  swellData: null,
  tideData: null,
  surfWindows: null,
  loaded: false,
  promise: null,
};

async function loadAll() {
  // Fetch swell, tides, and bathymetry in parallel (3 independent requests)
  const [offshoreData, tideData, bathymetry] = await Promise.all([
    fetchSwell(),
    loadTides(),
    loadBathymetry(),
  ]);

  // Transform offshore → nearshore using wave physics (pure computation)
  const swellData = transformWaves(offshoreData, bathymetry);

  // Run the surf check rules on the nearshore data
  const surfWindows = runSurfCheck(swellData, tideData);

  cache.offshoreData = offshoreData;
  cache.swellData = swellData;
  cache.tideData = tideData;
  cache.surfWindows = surfWindows;
  cache.loaded = true;

  return { offshoreData, swellData, tideData, surfWindows };
}

export function useForecastData() {
  const [data, setData] = useState({
    offshoreData: cache.offshoreData ?? [],
    swellData: cache.swellData ?? [],
    tideData: cache.tideData ?? [],
    surfWindows: cache.surfWindows ?? [],
  });
  const [loading, setLoading] = useState(!cache.loaded);
  const [error, setError] = useState(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;

    if (cache.loaded) {
      setData({
        offshoreData: cache.offshoreData,
        swellData: cache.swellData,
        tideData: cache.tideData,
        surfWindows: cache.surfWindows,
      });
      setLoading(false);
      return;
    }

    // Reuse promise if another component already triggered the load
    if (!cache.promise) {
      cache.promise = loadAll();
    }

    cache.promise
      .then((result) => {
        if (mounted.current) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted.current) {
          setError(err);
          setLoading(false);
        }
      });

    return () => {
      mounted.current = false;
    };
  }, []);

  return { ...data, loading, error };
}
