import { useEffect, useState, useRef } from "react";
import Papa from "papaparse";

/**
 * Custom hook that loads the 3 Ceará swell CSV files once and shares
 * the parsed data across all components that call it.
 *
 * Usage:
 *   const { climatologia, resumoAnual, eventos, loading, error } = useCearaData();
 *
 * The `month` param defaults to "marco" (March). When full-year data
 * arrives, we'll add more folders under public/data/ceara/{month}/.
 * For now there is only one folder and all CSVs live at the root level.
 */

// Module-level cache — shared across all component instances.
// This means the CSVs are fetched only once per page load, even if
// 4 different components call useCearaData().
const cache = {
  climatologia: null,
  resumoAnual: null,
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
  const [climatologia, resumoAnual, eventos] = await Promise.all([
    parseCsv("/data/ceara/climatologia.csv"),
    parseCsv("/data/ceara/resumo_anual.csv"),
    parseCsv("/data/ceara/eventos.csv"),
  ]);

  cache.climatologia = climatologia;
  cache.resumoAnual = resumoAnual;
  cache.eventos = eventos;
  cache.loaded = true;

  return { climatologia, resumoAnual, eventos };
}

export function useCearaData() {
  const [data, setData] = useState({
    climatologia: cache.climatologia ?? [],
    resumoAnual: cache.resumoAnual ?? [],
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
        resumoAnual: cache.resumoAnual,
        eventos: cache.eventos,
      });
      setLoading(false);
      return;
    }

    // Reuse the same promise if another component already triggered the load
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
