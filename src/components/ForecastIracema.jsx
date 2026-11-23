import { useMemo } from "react";
import { useForecastData } from "../hooks/useForecastData";
import { directionLabel } from "../forecast/surfCheck.js";
import { SPOT_NAME } from "../forecast/config.js";

/**
 * Rating badge colors — same approach as SCENARIO_COLORS in EventosDetalle.
 *
 * Tailwind utility classes for each rating level:
 * - great = green (go!)
 * - good = blue (worth it)
 * - fair = yellow (maybe)
 */
const RATING_STYLES = {
  great: "bg-green-100 text-green-800 border-green-300",
  good:  "bg-blue-100 text-blue-800 border-blue-300",
  fair:  "bg-yellow-100 text-yellow-800 border-yellow-300",
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
      <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
        <h2 className="text-xl font-bold mb-2">
          Surf Forecast — {SPOT_NAME}
        </h2>
        <p className="text-sm text-gray-500">Loading forecast data...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
        <h2 className="text-xl font-bold mb-2">
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
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
      <h2 className="text-xl font-bold mb-2">
        Surf Forecast — {SPOT_NAME}
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        7-day forecast based on Open-Meteo swell data + Mucuripe tide table.
        Energy threshold: 400 J/m2. Tide window: 0.0m–1.5m.
      </p>

      {/* Summary banner */}
      {hasWindows ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="font-semibold text-blue-900">
            {surfWindows.length} surf window{surfWindows.length > 1 ? "s" : ""} this week
          </p>
          {bestWindow && (
            <p className="text-sm text-blue-700 mt-1">
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
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
          <p className="font-semibold text-gray-600">
            Flat week ahead — no surfable windows detected
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Energy stays below 400 J/m2 or tide/direction are unfavorable.
          </p>
        </div>
      )}

      {/* Windows table */}
      {hasWindows && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-600">
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
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 pr-3 font-medium">
                    {formatDate(win.start)}
                  </td>
                  <td className="py-2 pr-3">
                    {formatTime(win.start)}–{formatTime(win.end)}
                  </td>
                  <td className="py-2 pr-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-bold border ${RATING_STYLES[win.rating] || ""}`}
                    >
                      {win.rating.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2 pr-3">{win.energyAvg} J/m2</td>
                  <td className="py-2 pr-3">
                    {win.swellHeightAvg}m @ {win.swellPeriodAvg}s
                  </td>
                  <td className="py-2 pr-3">
                    {directionLabel(win.swellDirAvg)} ({win.swellDirAvg}°)
                  </td>
                  <td className="py-2 pr-3">{win.tideHeightAtPeak}m</td>
                  <td className="py-2 pr-3 text-xs text-gray-500">
                    {win.tidePhaseSummary}
                  </td>
                  <td className="py-2 text-xs text-red-600">
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
