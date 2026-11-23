import { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend,
} from "recharts";
import { useForecastData } from "../hooks/useForecastData";
import { waveEnergy } from "../forecast/rules.js";
import { interpolateTideHeight } from "../forecast/tides.js";
import { ENERGY_SURFABLE, SPOT_NAME } from "../forecast/config.js";

/**
 * The energy threshold (400 J/m2) corresponds to a minimum wave height.
 * We solve E = (1/16) * 1025 * 9.81 * Hs^2 for Hs:
 *   Hs = sqrt(E * 16 / (1025 * 9.81))
 * At 400 J/m2 this is about 0.80m.
 *
 * We'll draw this as a reference line on the swell height axis.
 */
const ENERGY_THRESHOLD_HEIGHT = Math.sqrt(
  (ENERGY_SURFABLE * 16) / (1025 * 9.81)
);

/**
 * Format a Date to "Mon 24" for the X axis.
 * @param {Date} date
 * @returns {string}
 */
function shortDate(date) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return `${days[date.getDay()]} ${date.getDate()}`;
}

/**
 * Format hours for tooltip: "Mon 24 08:00"
 * @param {Date} date
 * @returns {string}
 */
function fullDateTime(date) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const hh = String(date.getHours()).padStart(2, "0");
  return `${days[date.getDay()]} ${date.getDate()} ${hh}:00`;
}

/**
 * Custom tooltip for the chart.
 *
 * Recharts calls this component for each hover point.
 * The `payload` prop contains the data for that point.
 *
 * This is the same pattern used in GraficoProbabilidade and other
 * existing chart components — a function component that receives
 * { active, payload, label } props from Recharts.
 */
const ChartTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  return (
    <div className="bg-white border border-gray-200 rounded shadow-sm p-3 text-sm">
      <p className="font-medium">{fullDateTime(data.date)}</p>
      <p className="text-blue-600">
        Swell: {data.swellHeight.toFixed(2)}m @ {data.swellPeriod.toFixed(1)}s
      </p>
      <p className="text-blue-600">
        Energy: {Math.round(data.energy)} J/m2
      </p>
      <p className="text-cyan-600">
        Tide: {data.tideHeight.toFixed(2)}m
      </p>
    </div>
  );
};

const SwellTideChart = () => {
  const { swellData, tideData, loading, error } = useForecastData();

  // Transform raw data into chart-friendly format
  // We sample every 3 hours to avoid an overcrowded chart (168 hours = 56 points at 3h)
  const chartData = useMemo(() => {
    if (!swellData.length) return [];

    return swellData
      .filter((_, i) => i % 3 === 0)
      .map((swell) => ({
        // Recharts needs a string key for XAxis
        timeLabel: shortDate(swell.time),
        date: swell.time,
        swellHeight: swell.height,
        swellPeriod: swell.period,
        energy: waveEnergy(swell.height),
        tideHeight: interpolateTideHeight(swell.time, tideData),
      }));
  }, [swellData, tideData]);

  // X-axis ticks: show one label per day (every 8 data points at 3h sampling)
  const dayTicks = useMemo(() => {
    if (!chartData.length) return [];
    const ticks = [];
    let lastDay = -1;
    for (let i = 0; i < chartData.length; i++) {
      const day = chartData[i].date.getDate();
      if (day !== lastDay) {
        ticks.push(i);
        lastDay = day;
      }
    }
    return ticks;
  }, [chartData]);

  if (loading || error || !chartData.length) return null;

  return (
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
      <h2 className="text-xl font-bold mb-2">
        Swell &amp; Tide — 7 Days
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Blue line: swell height (m). Cyan line: tide height (m).
        Dashed line: energy threshold (~{ENERGY_THRESHOLD_HEIGHT.toFixed(2)}m = {ENERGY_SURFABLE} J/m2).
      </p>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="timeLabel"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
            ticks={dayTicks.map((i) => chartData[i]?.timeLabel)}
          />

          {/* Left Y axis: swell height */}
          <YAxis
            yAxisId="swell"
            tick={{ fontSize: 12 }}
            domain={[0, "auto"]}
            label={{
              value: "Swell (m)",
              angle: -90,
              position: "insideLeft",
              style: { fontSize: 11, fill: "#6b7280" },
            }}
          />

          {/* Right Y axis: tide height */}
          <YAxis
            yAxisId="tide"
            orientation="right"
            tick={{ fontSize: 12 }}
            domain={[0, "auto"]}
            label={{
              value: "Tide (m)",
              angle: 90,
              position: "insideRight",
              style: { fontSize: 11, fill: "#6b7280" },
            }}
          />

          <Tooltip content={<ChartTooltip />} />
          <Legend />

          {/* Energy threshold as a dashed reference line */}
          <ReferenceLine
            yAxisId="swell"
            y={ENERGY_THRESHOLD_HEIGHT}
            stroke="#f59e0b"
            strokeDasharray="6 4"
            label={{
              value: `${ENERGY_SURFABLE} J/m2`,
              position: "right",
              style: { fontSize: 10, fill: "#f59e0b" },
            }}
          />

          {/* Swell height line */}
          <Line
            yAxisId="swell"
            type="monotone"
            dataKey="swellHeight"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            name="Swell height (m)"
          />

          {/* Tide height line */}
          <Line
            yAxisId="tide"
            type="monotone"
            dataKey="tideHeight"
            stroke="#06b6d4"
            strokeWidth={1.5}
            dot={false}
            name="Tide height (m)"
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
};

export default SwellTideChart;
