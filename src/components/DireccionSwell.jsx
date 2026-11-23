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
      <div className="bg-white p-3 border border-gray-200 rounded shadow text-sm">
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
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
      <h2 className="text-xl font-bold mb-2 text-gray-900">
        Direção do Swell — Norte vs Nordeste
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Percentual de horas com swell vindo de Norte (337.5°–22.5°) vs
        Nordeste (22.5°–67.5°) por cenário.
      </p>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveWeek("week3")}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            activeWeek === "week3"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          15–21 março
        </button>
        <button
          onClick={() => setActiveWeek("week4")}
          className={`px-4 py-2 rounded text-sm font-medium transition ${
            activeWeek === "week4"
              ? "bg-orange-500 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
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
          <CartesianGrid strokeDasharray="3 3" />
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
            fill="#2563eb"
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

      <p className="text-xs text-gray-400 mt-2 text-center">
        ERA5 1979–2025 — Cenários com eventos registrados (excl. &quot;Exceptional&quot; = 0 eventos)
      </p>
    </section>
  );
};

export default DireccionSwell;
