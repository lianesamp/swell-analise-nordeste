import { useEffect, useState } from "react";
import Papa from "papaparse";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

const WINDOWS = ["3h", "6h", "12h", "24h"];
const WINDOW_KEYS = [
  "prob_window_3h",
  "prob_window_6h",
  "prob_window_12h",
  "prob_window_24h",
];

const JanelasSurfaveis = () => {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    Papa.parse("/data/ceara/climatologia.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        const rows = result.data.filter(
          (d) => d.scenario === "good" && d.week
        );

        const w3 = rows.find((d) => d.week === "week3");
        const w4 = rows.find((d) => d.week === "week4");

        if (!w3 || !w4) return;

        const points = WINDOWS.map((label, i) => ({
          window: label,
          week3: +(w3[WINDOW_KEYS[i]] * 100).toFixed(1),
          week4: +(w4[WINDOW_KEYS[i]] * 100).toFixed(1),
        }));

        setChartData(points);
      },
    });
  }, []);

  if (chartData.length === 0) return null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <div className="bg-white p-3 border border-gray-200 rounded shadow text-sm">
        <p className="font-semibold mb-1">Janela {label}</p>
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
        Janelas Surfáveis — Cenário &quot;Good&quot;
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Probabilidade de encontrar ao menos uma janela contínua de swell N/NE
        com duração {"\u2265"} X horas (Tp {"\u2265"} 9s, Hs {"\u2265"} 1.0m).
      </p>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="window"
            label={{
              value: "Duração mínima",
              position: "insideBottom",
              offset: -10,
            }}
          />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            label={{
              value: "Probabilidade (%)",
              angle: -90,
              position: "insideLeft",
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend verticalAlign="top" />
          <Line
            type="monotone"
            dataKey="week3"
            name="15–21 março"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
          <Line
            type="monotone"
            dataKey="week4"
            name="22–28 março"
            stroke="#f97316"
            strokeWidth={2}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-400 mt-2 text-center">
        ERA5 1979–2025 — Cenário &quot;Good&quot; (Tp {"\u2265"} 9s, Hs{" "}
        {"\u2265"} 1.0m)
      </p>
    </section>
  );
};

export default JanelasSurfaveis;
