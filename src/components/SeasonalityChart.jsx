import { useState, useMemo } from "react";
import { useHistoricalData } from "../hooks/useHistoricalData";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ErrorBar,
  Cell,
} from "recharts";

/**
 * Bar chart showing swell probability by month across the swell season.
 *
 * X-axis = months (Sep through May, in season order)
 * Y-axis = probability (%) that the month has at least one qualifying event
 * Error bars = Wilson 95% confidence interval
 *
 * A scenario toggle lets the user switch between "surfable", "good", "strong", etc.
 * This is the main "which month is best?" visualization for Front 3.
 */

const SEASON_ORDER = [10, 11, 12, 1, 2, 3, 4, 5];

const SCENARIOS = [
  { key: "surfable", label: "Surfable", desc: "Tp \u2265 9s, Hs \u2265 0.8m" },
  { key: "good", label: "Good", desc: "Tp \u2265 9s, Hs \u2265 1.0m" },
  { key: "strong", label: "Strong", desc: "Tp \u2265 9s, Hs \u2265 1.2m" },
  { key: "very_good", label: "Very good", desc: "Tp \u2265 9s, Hs \u2265 1.5m" },
];

// Color gradient: warmer months get warmer colors
const MONTH_COLORS = {
  10: "#f97316",  // Oct — orange (season start)
  11: "#ef4444",  // Nov — red
  12: "#dc2626",  // Dec — deep red (peak)
  1: "#b91c1c",   // Jan — dark red (peak)
  2: "#ef4444",   // Feb — red
  3: "#f97316",   // Mar — orange
  4: "#fb923c",   // Apr — light orange
  5: "#94a3b8",   // May — slate (season end)
};

const SeasonalityChart = () => {
  const { climatologia, loading } = useHistoricalData();
  const [activeScenario, setActiveScenario] = useState("surfable");

  const chartData = useMemo(() => {
    const rows = climatologia.filter(
      (d) => d.scenario === activeScenario && d.month
    );

    return SEASON_ORDER.map((month) => {
      const row = rows.find((r) => r.month === month);
      if (!row) return { month, month_label: "", prob: 0, errLow: 0, errHigh: 0 };

      const prob = row.probability * 100;
      const ciLow = row.ci_low * 100;
      const ciHigh = row.ci_high * 100;

      return {
        month,
        month_label: row.month_label,
        prob,
        err: [prob - ciLow, ciHigh - prob],
        total_events: row.total_events,
        events_per_year: row.mean_events_per_year,
        duration_mean: row.duration_mean,
        total_years: row.total_years,
        years_with_event: row.years_with_event,
      };
    });
  }, [climatologia, activeScenario]);

  if (loading || chartData.length === 0) return null;

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload[0]) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-lg p-3 text-sm text-white">
        <p className="font-semibold mb-1">{d.month_label}</p>
        <p>Probability: {d.prob.toFixed(0)}%</p>
        <p>Years with event: {d.years_with_event}/{d.total_years}</p>
        <p>Events/year: {d.events_per_year}</p>
        {d.duration_mean > 0 && <p>Avg duration: {d.duration_mean}h</p>}
      </div>
    );
  };

  const scenarioInfo = SCENARIOS.find((s) => s.key === activeScenario);

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Swell Seasonality — Monthly Probability
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Chance of at least one N/NE swell event per month.
        Error bars show Wilson 95% CI.
        Scenario: <strong>{scenarioInfo?.label}</strong> ({scenarioInfo?.desc}).
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {SCENARIOS.map((s) => (
          <button
            key={s.key}
            onClick={() => setActiveScenario(s.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeScenario === s.key
                ? "bg-cyan-600 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800"
            }`}
          >
            <span>{s.label}</span>
            <span className={`block text-[10px] font-normal mt-0.5 ${
              activeScenario === s.key ? "text-cyan-200" : "text-slate-400"
            }`}>
              {s.desc}
            </span>
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="month_label" tick={{ fontSize: 12 }} interval={0} />
          <YAxis
            domain={[0, 110]}
            label={{
              value: "Probability (%)",
              angle: -90,
              position: "insideLeft",
              offset: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={50} stroke="#94a3b8" strokeDasharray="3 3" />
          <Bar dataKey="prob" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={MONTH_COLORS[entry.month] || "#0891b2"} />
            ))}
            <ErrorBar
              dataKey="err"
              width={4}
              strokeWidth={1.5}
              stroke="#475569"
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs text-slate-400 mt-2 text-center">
        ERA5 swell season (Oct–May) — {Math.max(...chartData.map((d) => d.total_years || 0))} year(s) of data
      </p>
    </section>
  );
};

export default SeasonalityChart;
