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
import { ENERGY_SURFABLE } from "../forecast/config.js";

/**
 * The energy threshold (400 J/m2) corresponds to a minimum wave height.
 * Hs = sqrt(E * 16 / (rho * g))
 * At 400 J/m2 this is about 0.80m.
 */
const ENERGY_THRESHOLD_HEIGHT = Math.sqrt(
  (ENERGY_SURFABLE * 16) / (1025 * 9.81)
);

function shortDate(date) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return `${days[date.getDay()]} ${date.getDate()}`;
}

function fullDateTime(date) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const hh = String(date.getHours()).padStart(2, "0");
  return `${days[date.getDay()]} ${date.getDate()} ${hh}:00`;
}

/**
 * Custom tooltip showing both offshore and nearshore values.
 */
const ChartTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  return (
    <div className="bg-white border border-gray-200 rounded shadow-sm p-3 text-sm">
      <p className="font-medium">{fullDateTime(data.date)}</p>
      <p className="text-gray-400">
        Offshore: {data.offshoreHeight.toFixed(2)}m ({Math.round(data.offshoreEnergy)} J/m2)
      </p>
      <p className="text-blue-600">
        Nearshore: {data.swellHeight.toFixed(2)}m ({Math.round(data.energy)} J/m2)
      </p>
      <p className="text-gray-500 text-xs">
        Reduction: {data.offshoreHeight > 0
          ? Math.round((1 - data.swellHeight / data.offshoreHeight) * 100)
          : 0}%
      </p>
      <p className="text-cyan-600">
        Tide: {data.tideHeight.toFixed(2)}m
      </p>
    </div>
  );
};

const SwellTideChart = () => {
  const { offshoreData, swellData, tideData, loading, error } = useForecastData();

  // Build chart data with both offshore and nearshore values
  const chartData = useMemo(() => {
    if (!swellData.length) return [];

    return swellData
      .filter((_, i) => i % 3 === 0)
      .map((swell, idx) => {
        // Find matching offshore data point (same index after filtering)
        const offshoreIdx = idx * 3;
        const offshore = offshoreData[offshoreIdx] || swell;

        return {
          timeLabel: shortDate(swell.time),
          date: swell.time,
          offshoreHeight: offshore.height,
          offshoreEnergy: waveEnergy(offshore.height),
          swellHeight: swell.height,
          swellPeriod: swell.period,
          energy: waveEnergy(swell.height),
          tideHeight: interpolateTideHeight(swell.time, tideData),
        };
      });
  }, [offshoreData, swellData, tideData]);

  // X-axis ticks: one label per day
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
        Gray dashed: offshore swell (Open-Meteo raw).
        Blue: nearshore swell (after shoaling + refraction).
        Cyan: tide.
        Orange dashed: {ENERGY_SURFABLE} J/m2 threshold (~{ENERGY_THRESHOLD_HEIGHT.toFixed(2)}m).
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

          {/* Energy threshold reference line */}
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

          {/* Offshore swell — raw Open-Meteo data (gray dashed) */}
          <Line
            yAxisId="swell"
            type="monotone"
            dataKey="offshoreHeight"
            stroke="#9ca3af"
            strokeWidth={1.5}
            strokeDasharray="4 3"
            dot={false}
            name="Offshore (m)"
          />

          {/* Nearshore swell — after wave transformation (solid blue) */}
          <Line
            yAxisId="swell"
            type="monotone"
            dataKey="swellHeight"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            name="Nearshore (m)"
          />

          {/* Tide height */}
          <Line
            yAxisId="tide"
            type="monotone"
            dataKey="tideHeight"
            stroke="#06b6d4"
            strokeWidth={1.5}
            dot={false}
            name="Tide (m)"
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
};

export default SwellTideChart;
