import { useEffect, useState, useRef } from "react";
import { fetchSwell, runSurfCheck } from "../forecast/surfCheck.js";
import { loadTides } from "../forecast/tides.js";

/**
 * Custom hook that fetches the 7-day surf forecast for Praia de Iracema.
 *
 * Follows the same pattern as useCearaData:
 * - Module-level cache so data is fetched once per page load
 * - Shared promise so multiple components don't duplicate requests
 * - Cleanup ref to prevent state updates on unmounted components
 *
 * Unlike useCearaData (which loads static CSVs), this hook calls
 * the Open-Meteo Marine API for live swell data. The tide data is
 * still a static JSON file.
 *
 * Usage:
 *   const { swellData, tideData, surfWindows, loading, error } = useForecastData();
 *
 * New concept — "hook composition":
 *   Each hook manages its own data source independently. Components
 *   can use one or both hooks without them interfering. This is like
 *   having separate Service classes in Laravel that don't depend on
 *   each other.
 */

// Module-level cache — same approach as useCearaData
const cache = {
  swellData: null,
  tideData: null,
  surfWindows: null,
  loaded: false,
  promise: null,
};

async function loadAll() {
  // Fetch swell and tides in parallel (independent requests)
  const [swellData, tideData] = await Promise.all([
    fetchSwell(),
    loadTides(),
  ]);

  // Run the surf check rules (pure computation, no I/O)
  const surfWindows = runSurfCheck(swellData, tideData);

  cache.swellData = swellData;
  cache.tideData = tideData;
  cache.surfWindows = surfWindows;
  cache.loaded = true;

  return { swellData, tideData, surfWindows };
}

export function useForecastData() {
  const [data, setData] = useState({
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
