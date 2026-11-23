import { useMemo } from "react";
import { useForecastData } from "../hooks/useForecastData";
import { directionLabel } from "../forecast/surfCheck.js";
import { SPOT_NAME } from "../forecast/config.js";

/**
 * Rating badge colors — ocean theme palette.
 *
 * Tailwind utility classes for each rating level:
 * - great = teal (go!)
 * - good = cyan (worth it)
 * - fair = amber (maybe)
 */
const RATING_STYLES = {
  great: "bg-teal-100 text-teal-800 border-teal-300",
  good:  "bg-cyan-100 text-cyan-800 border-cyan-300",
  fair:  "bg-amber-100 text-amber-800 border-amber-300",
};

/**
 * Format a Date to a readable string like "Mon 24/11".
 * @param {Date} date
 * @returns {string}
 */
function formatDate(date) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const day = days[date.getDay()];
  const dd = String(date.getDate()).padStart(2, "0");
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  return `${day} ${dd}/${mm}`;
}

/**
 * Format a Date to hours like "08:00".
 * @param {Date} date
 * @returns {string}
 */
function formatTime(date) {
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

const ForecastIracema = () => {
  const { surfWindows, loading, error } = useForecastData();

  // Group windows by date for display
  const windowsByDate = useMemo(() => {
    const grouped = {};
    for (const win of surfWindows) {
      const dateKey = formatDate(win.start);
      if (!grouped[dateKey]) grouped[dateKey] = [];
      grouped[dateKey].push(win);
    }
    return grouped;
  }, [surfWindows]);

  if (loading) {
    return (
      <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
        <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
          Surf Forecast — {SPOT_NAME}
        </h2>
        <p className="text-sm text-slate-500">Loading forecast data...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
        <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
          Surf Forecast — {SPOT_NAME}
        </h2>
        <p className="text-sm text-red-600">
          Failed to load forecast: {error.message}
        </p>
      </section>
    );
  }

  const hasWindows = surfWindows.length > 0;

  // Find the best window overall
  const ratingOrder = { great: 3, good: 2, fair: 1 };
  const bestWindow = hasWindows
    ? surfWindows.reduce((a, b) =>
        (ratingOrder[b.rating] || 0) > (ratingOrder[a.rating] || 0) ? b : a
      )
    : null;

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Surf Forecast — {SPOT_NAME}
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        7-day forecast based on Open-Meteo swell data + Mucuripe tide table.
        Energy threshold: 400 J/m2. Tide window: 0.0m–1.5m.
      </p>

      {/* Summary banner */}
      {hasWindows ? (
        <div className="bg-cyan-50/60 border border-cyan-200/60 rounded-xl p-4 mb-6">
          <p className="font-semibold text-cyan-900">
            {surfWindows.length} surf window{surfWindows.length > 1 ? "s" : ""} this week
          </p>
          {bestWindow && (
            <p className="text-sm text-cyan-700 mt-1">
              Best session: {formatDate(bestWindow.start)}{" "}
              {formatTime(bestWindow.start)}–{formatTime(bestWindow.end)}{" "}
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold border ${RATING_STYLES[bestWindow.rating]}`}>
                {bestWindow.rating.toUpperCase()}
              </span>
              {" "}({bestWindow.energyAvg} J/m2)
            </p>
          )}
        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
          <p className="font-semibold text-slate-600">
            Flat week ahead — no surfable windows detected
          </p>
          <p className="text-sm text-slate-500 mt-1">
            Energy stays below 400 J/m2 or tide/direction are unfavorable.
          </p>
        </div>
      )}

      {/* Windows table */}
      {hasWindows && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500 uppercase text-xs tracking-wider">
                <th className="py-2 pr-3">Date</th>
                <th className="py-2 pr-3">Time</th>
                <th className="py-2 pr-3">Rating</th>
                <th className="py-2 pr-3">Energy</th>
                <th className="py-2 pr-3">Swell</th>
                <th className="py-2 pr-3">Direction</th>
                <th className="py-2 pr-3">Tide</th>
                <th className="py-2 pr-3">Phase</th>
                <th className="py-2">Warnings</th>
              </tr>
            </thead>
            <tbody>
              {surfWindows.map((win, i) => (
                <tr
                  key={i}
                  className="border-b border-slate-100 hover:bg-cyan-50/40 transition-colors duration-150"
                >
                  <td className="py-2 pr-3 font-medium text-slate-800">
                    {formatDate(win.start)}
                  </td>
                  <td className="py-2 pr-3 text-slate-600">
                    {formatTime(win.start)}–{formatTime(win.end)}
                  </td>
                  <td className="py-2 pr-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-bold border ${RATING_STYLES[win.rating] || ""}`}
                    >
                      {win.rating.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2 pr-3 text-slate-600">{win.energyAvg} J/m2</td>
                  <td className="py-2 pr-3 text-slate-600">
                    {win.swellHeightAvg}m @ {win.swellPeriodAvg}s
                  </td>
                  <td className="py-2 pr-3 text-slate-600">
                    {directionLabel(win.swellDirAvg)} ({win.swellDirAvg}°)
                  </td>
                  <td className="py-2 pr-3 text-slate-600">{win.tideHeightAtPeak}m</td>
                  <td className="py-2 pr-3 text-xs text-slate-500">
                    {win.tidePhaseSummary}
                  </td>
                  <td className="py-2 text-xs text-amber-600">
                    {win.warnings.join("; ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
};

export default ForecastIracema;
