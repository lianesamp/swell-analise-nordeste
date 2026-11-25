import { useMemo } from "react";
import { useHistoricalData } from "../hooks/useHistoricalData";

/**
 * Monthly Heatmap — a grid showing swell activity by year and month.
 *
 * Rows = years (sorted descending, most recent on top)
 * Columns = months (Sep through May, in season order)
 * Cell color = intensity based on number of events and max height
 *
 * This is NOT a Recharts chart — it's a plain HTML table with Tailwind
 * background colors, because Recharts doesn't have a built-in heatmap.
 * A table is simpler, more accessible, and easier to customize than
 * a custom SVG chart for this grid layout.
 *
 * Data source: monthly_summary.csv (one row per year-month combination)
 * filtered by the "surfable" scenario (from the pipeline).
 */

const SEASON_ORDER = [10, 11, 12, 1, 2, 3, 4, 5];

const MONTH_LABELS = {
  1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May",
  10: "Oct", 11: "Nov", 12: "Dec",
};

/**
 * Map event count + max height to a color intensity.
 * Uses Tailwind-style color classes for consistency.
 */
function getCellStyle(row) {
  if (!row || !row.had_event) {
    return { bg: "bg-slate-50", text: "text-slate-300", label: "-" };
  }

  const h = row.max_height;
  const n = row.n_events;

  if (h >= 1.5) {
    return { bg: "bg-red-100", text: "text-red-800", label: `${n}e / ${h.toFixed(1)}m` };
  }
  if (h >= 1.2) {
    return { bg: "bg-orange-100", text: "text-orange-800", label: `${n}e / ${h.toFixed(1)}m` };
  }
  if (h >= 1.0) {
    return { bg: "bg-amber-100", text: "text-amber-800", label: `${n}e / ${h.toFixed(1)}m` };
  }
  return { bg: "bg-cyan-50", text: "text-cyan-700", label: `${n}e / ${h.toFixed(1)}m` };
}

const MonthlyHeatmap = () => {
  const { summary, loading } = useHistoricalData();

  const { years, grid } = useMemo(() => {
    const validRows = summary.filter((d) => d.year && d.month);
    const yearSet = [...new Set(validRows.map((d) => d.year))].sort((a, b) => b - a);

    // Build a lookup: grid[year][month] = row
    const lookup = {};
    validRows.forEach((row) => {
      if (!lookup[row.year]) lookup[row.year] = {};
      lookup[row.year][row.month] = row;
    });

    return { years: yearSet, grid: lookup };
  }, [summary]);

  if (loading || years.length === 0) return null;

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Monthly Heatmap — Events by Year
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Scenario &quot;surfable&quot; (mean Tp &ge; 9s, Hs &ge; 0.8m, direction N/NE).
        Cell shows event count and max wave height.
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr>
              <th className="text-left text-slate-500 font-semibold py-2 px-2 w-16">Year</th>
              {SEASON_ORDER.map((m) => (
                <th key={m} className="text-center text-slate-500 font-semibold py-2 px-1">
                  {MONTH_LABELS[m]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year} className="border-t border-slate-100">
                <td className="font-medium text-slate-700 py-1.5 px-2">{year}</td>
                {SEASON_ORDER.map((month) => {
                  const row = grid[year]?.[month];
                  const hadEvent = row?.had_event === true || row?.had_event === "True";
                  const cell = getCellStyle(hadEvent ? row : null);
                  return (
                    <td
                      key={month}
                      className={`text-center py-1.5 px-1 rounded ${cell.bg} ${cell.text} font-medium`}
                      title={
                        hadEvent
                          ? `${year} ${MONTH_LABELS[month]}: ${row.n_events} events, max ${row.max_height}m, ${row.total_hours}h total`
                          : `${year} ${MONTH_LABELS[month]}: no events`
                      }
                    >
                      {hadEvent ? cell.label : "-"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 mt-4 text-xs text-slate-500">
        <span className="font-medium">Intensity:</span>
        <span className="inline-flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-slate-50 border border-slate-200"></span> No event
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-cyan-50"></span> &lt; 1.0m
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-amber-100"></span> 1.0–1.2m
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-orange-100"></span> 1.2–1.5m
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-red-100"></span> &ge; 1.5m
        </span>
      </div>
    </section>
  );
};

export default MonthlyHeatmap;
