import { useState, useMemo } from "react";
import { useCearaData } from "../hooks/useCearaData";

const SCENARIO_LABELS = {
  any_relevant: "Any relevant",
  surfable: "Surfable",
  good: "Good",
  strong: "Strong",
  very_good: "Very good",
  exceptional: "Exceptional",
};

const SCENARIO_COLORS = {
  any_relevant: "bg-gray-100 text-gray-700",
  surfable: "bg-blue-100 text-blue-700",
  good: "bg-green-100 text-green-700",
  strong: "bg-yellow-100 text-yellow-700",
  very_good: "bg-orange-100 text-orange-700",
  exceptional: "bg-red-100 text-red-700",
};

const EventosDetalle = () => {
  const { eventos, loading } = useCearaData();

  // Filter state — these are "controlled" inputs.
  // React state drives the <select> value; onChange updates the state.
  const [scenarioFilter, setScenarioFilter] = useState("good");
  const [weekFilter, setWeekFilter] = useState("all");
  const [sortField, setSortField] = useState("year");
  const [sortAsc, setSortAsc] = useState(false);

  const filtered = useMemo(() => {
    let rows = eventos.filter((d) => d.scenario && d.year);

    if (scenarioFilter !== "all") {
      rows = rows.filter((d) => d.scenario === scenarioFilter);
    }
    if (weekFilter !== "all") {
      const weekNum = weekFilter === "week3" ? 3 : 4;
      rows = rows.filter((d) => d.march_week === weekNum);
    }

    rows.sort((a, b) => {
      const valA = a[sortField] ?? 0;
      const valB = b[sortField] ?? 0;
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });

    return rows;
  }, [eventos, scenarioFilter, weekFilter, sortField, sortAsc]);

  if (loading) return null;

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortIcon = (field) => {
    if (sortField !== field) return "";
    return sortAsc ? " ↑" : " ↓";
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    // "2005-03-16 03:00:00" → "16/03 03h"
    const parts = dateStr.split(" ");
    if (parts.length < 2) return dateStr;
    const [y, m, d] = parts[0].split("-");
    const hour = parts[1].substring(0, 5);
    return `${d}/${m} ${hour}`;
  };

  return (
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
      <h2 className="text-xl font-bold mb-2 text-gray-900">
        Eventos Individuais
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Cada linha é um evento contínuo de swell N/NE detectado no período.
        Clique nos cabeçalhos para ordenar.
      </p>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1" htmlFor="scenario-filter">
            Cenário
          </label>
          <select
            id="scenario-filter"
            value={scenarioFilter}
            onChange={(e) => setScenarioFilter(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
          >
            <option value="all">Todos</option>
            {Object.entries(SCENARIO_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1" htmlFor="week-filter">
            Semana
          </label>
          <select
            id="week-filter"
            value={weekFilter}
            onChange={(e) => setWeekFilter(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
          >
            <option value="all">Ambas</option>
            <option value="week3">15–21 março</option>
            <option value="week4">22–28 março</option>
          </select>
        </div>

        <div className="flex items-end">
          <span className="text-sm text-gray-600">
            Mostrando <strong>{filtered.length}</strong> de {eventos.length} eventos
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {[
                { key: "year", label: "Ano" },
                { key: "start_time", label: "Início" },
                { key: "duration_hours", label: "Duração (h)" },
                { key: "max_height", label: "Hs max (m)" },
                { key: "max_period", label: "Tp max (s)" },
                { key: "dominant_direction", label: "Dir" },
                { key: "scenario", label: "Cenário" },
              ].map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="text-left p-2 font-semibold cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap"
                >
                  {col.label}{sortIcon(col.key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-4 text-center text-gray-400">
                  Nenhum evento encontrado com esses filtros.
                </td>
              </tr>
            ) : (
              filtered.map((ev, i) => (
                <tr
                  key={`${ev.start_time}-${ev.scenario}-${i}`}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="p-2 font-medium">{ev.year}</td>
                  <td className="p-2 whitespace-nowrap">{formatDate(ev.start_time)}</td>
                  <td className="p-2 text-right">{ev.duration_hours}</td>
                  <td className="p-2 text-right">{ev.max_height?.toFixed(2)}</td>
                  <td className="p-2 text-right">{ev.max_period?.toFixed(1)}</td>
                  <td className="p-2">{ev.dominant_direction}</td>
                  <td className="p-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SCENARIO_COLORS[ev.scenario] ?? ""}`}>
                      {SCENARIO_LABELS[ev.scenario] ?? ev.scenario}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400 mt-3 text-center">
        ERA5 1979–2025 — Março semanas 3 e 4
      </p>
    </section>
  );
};

export default EventosDetalle;
