import { useEffect, useState, useRef } from "react";
import Papa from "papaparse";

/**
 * Custom hook that loads the 3 Front 3 (Historical) CSV files once
 * and shares the parsed data across all components that call it.
 *
 * Same module-level cache pattern as useCearaData — the CSVs are fetched
 * only once per page load, even if multiple components call this hook.
 *
 * Usage:
 *   const { climatologia, summary, eventos, loading, error } = useHistoricalData();
 *
 * Files loaded:
 *   - monthly_climatology.csv  — per-scenario, per-month probability & stats
 *   - monthly_summary.csv      — per-year, per-month event summary (heatmap data)
 *   - eventos_season.csv       — individual event records for all season months
 */

const cache = {
  climatologia: null,
  summary: null,
  eventos: null,
  loaded: false,
  promise: null,
};

function parseCsv(url) {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (result) => resolve(result.data),
      error: (err) => reject(err),
    });
  });
}

async function loadAll() {
  const [climatologia, summary, eventos] = await Promise.all([
    parseCsv("/data/historical/monthly_climatology.csv"),
    parseCsv("/data/historical/monthly_summary.csv"),
    parseCsv("/data/historical/eventos_season.csv"),
  ]);

  cache.climatologia = climatologia;
  cache.summary = summary;
  cache.eventos = eventos;
  cache.loaded = true;

  return { climatologia, summary, eventos };
}

export function useHistoricalData() {
  const [data, setData] = useState({
    climatologia: cache.climatologia ?? [],
    summary: cache.summary ?? [],
    eventos: cache.eventos ?? [],
  });
  const [loading, setLoading] = useState(!cache.loaded);
  const [error, setError] = useState(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;

    if (cache.loaded) {
      setData({
        climatologia: cache.climatologia,
        summary: cache.summary,
        eventos: cache.eventos,
      });
      setLoading(false);
      return;
    }

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
