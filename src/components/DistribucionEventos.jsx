import { useMemo, useState } from "react";
import { useCearaData } from "../hooks/useCearaData";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from "recharts";

const SCENARIO_ORDER = [
  "any_relevant",
  "surfable",
  "good",
  "strong",
  "very_good",
];
// "exceptional" excluded — 0 events, no stats

const METRICS = [
  {
    key: "duration",
    title: "Duration (hours)",
    unit: "h",
    fields: { mean: "duration_mean", median: "duration_median", p90: "duration_p90", max: "duration_max" },
  },
  {
    key: "height",
    title: "Height Hs (m)",
    unit: "m",
    fields: { mean: "height_mean", median: "height_median", p90: "height_p90", max: "height_max" },
  },
  {
    key: "period",
    title: "Period Tp (s)",
    unit: "s",
    fields: { mean: "period_mean", median: "period_median", p90: "period_p90", max: "period_max" },
  },
];

const DistribucionEventos = () => {
  const { climatologia, loading } = useCearaData();
  const [activeWeek, setActiveWeek] = useState("week3");
  const [activeMetric, setActiveMetric] = useState("duration");

  const metric = METRICS.find((m) => m.key === activeMetric);

  const chartData = useMemo(() => {
    if (!metric) return [];

    const rows = climatologia.filter(
      (d) => d.scenario && d.week === activeWeek && d.total_events > 0
    );

    const byScenario = {};
    rows.forEach((r) => {
      byScenario[r.scenario] = r;
    });

    return SCENARIO_ORDER
      .filter((k) => byScenario[k])
      .map((k) => {
        const r = byScenario[k];
        return {
          label: r.scenario_label,
          mean: +Number(r[metric.fields.mean]).toFixed(2),
          median: +Number(r[metric.fields.median]).toFixed(2),
          p90: +Number(r[metric.fields.p90]).toFixed(2),
          max: +Number(r[metric.fields.max]).toFixed(2),
        };
      });
  }, [climatologia, activeWeek, activeMetric, metric]);

  if (loading || chartData.length === 0) return null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-lg p-3 text-sm text-white">
        <p className="font-semibold mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.dataKey} style={{ color: p.color }}>
            {p.name}: {p.value}{metric.unit}
          </p>
        ))}
      </div>
    );
  };

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Event Characteristics
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        When there is swell, what are the typical characteristics?
        Mean, median, 90th percentile, and maximum per scenario.
      </p>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-4">
        {/* Week toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveWeek("week3")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeWeek === "week3"
                ? "bg-cyan-600 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800"
            }`}
          >
            Mar 15–21
          </button>
          <button
            onClick={() => setActiveWeek("week4")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeWeek === "week4"
                ? "bg-amber-500 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800"
            }`}
          >
            Mar 22–28
          </button>
        </div>

        {/* Metric selector */}
        <div className="flex gap-2">
          {METRICS.map((m) => (
            <button
              key={m.key}
              onClick={() => setActiveMetric(m.key)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeMetric === m.key
                  ? "bg-slate-800 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800"
              }`}
            >
              {m.title}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11 }}
            angle={-15}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            label={{
              value: metric.title,
              angle: -90,
              position: "insideLeft",
              offset: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="mean" name="Mean" fill="#67e8f9" radius={[2, 2, 0, 0]} />
          <Bar dataKey="median" name="Median" fill="#5eead4" radius={[2, 2, 0, 0]} />
          <Bar dataKey="p90" name="P90" fill="#fbbf24" radius={[2, 2, 0, 0]} />
          <Bar dataKey="max" name="Maximum" fill="#f97316" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs text-slate-400 mt-2 text-center">
        ERA5 1979–2025 — Statistics per scenario (excl. &quot;Exceptional&quot; = 0 events)
      </p>
    </section>
  );
};

export default DistribucionEventos;
