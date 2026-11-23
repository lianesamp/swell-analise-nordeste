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
} from "recharts";

const SCENARIO_ORDER = [
  "any_relevant",
  "surfable",
  "good",
  "strong",
  "very_good",
  "exceptional",
];

const DireccionSwell = () => {
  const { climatologia, loading } = useCearaData();
  const [activeWeek, setActiveWeek] = useState("week3");

  const chartData = useMemo(() => {
    const rows = climatologia.filter(
      (d) => d.scenario && d.week === activeWeek && d.pct_N != null
    );

    const byScenario = {};
    rows.forEach((r) => {
      byScenario[r.scenario] = r;
    });

    return SCENARIO_ORDER
      .filter((k) => byScenario[k] && byScenario[k].total_events > 0)
      .map((k) => {
        const r = byScenario[k];
        return {
          label: r.scenario_label,
          N: +r.pct_N.toFixed(1),
          NE: +r.pct_NE.toFixed(1),
        };
      });
  }, [climatologia, activeWeek]);

  if (loading || chartData.length === 0) return null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-lg p-3 text-sm text-white">
        <p className="font-semibold mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.dataKey} style={{ color: p.color }}>
            {p.name}: {p.value}%
          </p>
        ))}
      </div>
    );
  };

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Direção do Swell — Norte vs Nordeste
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Percentual de horas com swell vindo de Norte (337.5°–22.5°) vs
        Nordeste (22.5°–67.5°) por cenário.
      </p>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveWeek("week3")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            activeWeek === "week3"
              ? "bg-cyan-600 text-white shadow-sm"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800"
          }`}
        >
          15–21 março
        </button>
        <button
          onClick={() => setActiveWeek("week4")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            activeWeek === "week4"
              ? "bg-amber-500 text-white shadow-sm"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-800"
          }`}
        >
          22–28 março
        </button>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
          />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ fontSize: 12 }}
            width={90}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar
            dataKey="N"
            name="Norte (N)"
            stackId="dir"
            fill="#0891b2"
            radius={[0, 0, 0, 0]}
          />
          <Bar
            dataKey="NE"
            name="Nordeste (NE)"
            stackId="dir"
            fill="#14b8a6"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs text-slate-400 mt-2 text-center">
        ERA5 1979–2025 — Cenários com eventos registrados (excl. &quot;Exceptional&quot; = 0 eventos)
      </p>
    </section>
  );
};

export default DireccionSwell;
