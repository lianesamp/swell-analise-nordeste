import { useState, useMemo } from "react";
import { useHistoricalData } from "../hooks/useHistoricalData";

/**
 * Paginated event table for the full swell season.
 *
 * Same pattern as EventosDetalle (Front 2) but adapted for season data:
 * - Month filter instead of week filter
 * - Shows month column instead of march_week
 *
 * Data source: eventos_season.csv
 */

const SCENARIO_LABELS = {
  any_relevant: "Any relevant",
  surfable: "Surfable",
  good: "Good",
  strong: "Strong",
  very_good: "Very good",
  exceptional: "Exceptional",
};

const SCENARIO_COLORS = {
  any_relevant: "bg-slate-100 text-slate-700",
  surfable: "bg-cyan-100 text-cyan-700",
  good: "bg-teal-100 text-teal-700",
  strong: "bg-amber-100 text-amber-700",
  very_good: "bg-orange-100 text-orange-700",
  exceptional: "bg-rose-100 text-rose-700",
};

const MONTH_LABELS = {
  1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May",
  9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
};

const EventosSeason = () => {
  const { eventos, loading } = useHistoricalData();

  const [scenarioFilter, setScenarioFilter] = useState("surfable");
  const [monthFilter, setMonthFilter] = useState("all");
  const [sortField, setSortField] = useState("start_time");
  const [sortAsc, setSortAsc] = useState(false);
  const [page, setPage] = useState(0);
  const perPage = 15;

  // Available months (from data)
  const availableMonths = useMemo(() => {
    const months = [...new Set(eventos.filter((d) => d.month).map((d) => d.month))];
    // Sort in season order
    const order = [9, 10, 11, 12, 1, 2, 3, 4, 5];
    return months.sort((a, b) => order.indexOf(a) - order.indexOf(b));
  }, [eventos]);

  const filtered = useMemo(() => {
    let rows = eventos.filter((d) => d.scenario && d.year);

    if (scenarioFilter !== "all") {
      rows = rows.filter((d) => d.scenario === scenarioFilter);
    }
    if (monthFilter !== "all") {
      rows = rows.filter((d) => d.month === Number(monthFilter));
    }

    rows.sort((a, b) => {
      const valA = a[sortField] ?? 0;
      const valB = b[sortField] ?? 0;
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });

    return rows;
  }, [eventos, scenarioFilter, monthFilter, sortField, sortAsc]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = filtered.slice(safePage * perPage, (safePage + 1) * perPage);

  if (loading) return null;

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
    setPage(0);
  };

  const sortIcon = (field) => {
    if (sortField !== field) return "";
    return sortAsc ? " \u2191" : " \u2193";
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "\u2014";
    const parts = dateStr.split(" ");
    if (parts.length < 2) return dateStr;
    const [, m, d] = parts[0].split("-");
    const hour = parts[1].substring(0, 5);
    return `${d}/${m} ${hour}`;
  };

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Season Events — Individual Records
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Each row is a continuous N/NE swell event detected during the swell season.
        Click headers to sort.
      </p>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1" htmlFor="season-scenario-filter">
            Scenario
          </label>
          <select
            id="season-scenario-filter"
            value={scenarioFilter}
            onChange={(e) => { setScenarioFilter(e.target.value); setPage(0); }}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400 outline-none transition-all duration-200"
          >
            <option value="all">All</option>
            {Object.entries(SCENARIO_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1" htmlFor="season-month-filter">
            Month
          </label>
          <select
            id="season-month-filter"
            value={monthFilter}
            onChange={(e) => { setMonthFilter(e.target.value); setPage(0); }}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400 outline-none transition-all duration-200"
          >
            <option value="all">All months</option>
            {availableMonths.map((m) => (
              <option key={m} value={m}>{MONTH_LABELS[m] || m}</option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <span className="text-sm text-slate-600">
            Showing <strong>{filtered.length}</strong> of {eventos.length} events
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200">
              {[
                { key: "year", label: "Year" },
                { key: "month", label: "Month" },
                { key: "start_time", label: "Start" },
                { key: "duration_hours", label: "Duration (h)" },
                { key: "max_height", label: "Hs max (m)" },
                { key: "max_period", label: "Tp max (s)" },
                { key: "dominant_direction", label: "Dir" },
                { key: "scenario", label: "Scenario" },
              ].map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="text-left p-2 font-semibold text-xs uppercase tracking-wider text-slate-600 cursor-pointer hover:bg-slate-100 select-none whitespace-nowrap transition-colors duration-150"
                >
                  {col.label}{sortIcon(col.key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-4 text-center text-slate-400">
                  No events found with these filters.
                </td>
              </tr>
            ) : (
              pageRows.map((ev, i) => (
                <tr
                  key={`${ev.start_time}-${ev.scenario}-${i}`}
                  className="border-b border-slate-100 hover:bg-cyan-50/40 transition-colors duration-150"
                >
                  <td className="p-2 font-medium text-slate-800">{ev.year}</td>
                  <td className="p-2 text-slate-600">{MONTH_LABELS[ev.month] || ev.month}</td>
                  <td className="p-2 whitespace-nowrap text-slate-600">{formatDate(ev.start_time)}</td>
                  <td className="p-2 text-right text-slate-600">{ev.duration_hours}</td>
                  <td className="p-2 text-right text-slate-600">{ev.max_height?.toFixed(2)}</td>
                  <td className="p-2 text-right text-slate-600">{ev.max_period?.toFixed(1)}</td>
                  <td className="p-2 text-slate-600">{ev.dominant_direction}</td>
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-4">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={safePage === 0}
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150"
          >
            Previous
          </button>
          <span className="text-sm text-slate-600">
            Page <strong>{safePage + 1}</strong> of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={safePage >= totalPages - 1}
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150"
          >
            Next
          </button>
        </div>
      )}

      <p className="text-xs text-slate-400 mt-3 text-center">
        ERA5 swell season (Sep–May) — N/NE direction filter
      </p>
    </section>
  );
};

export default EventosSeason;
