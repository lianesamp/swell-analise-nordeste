import { useEffect, useState } from "react";
import Papa from "papaparse";
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
  ErrorBar,
} from "recharts";

const GraficoProbabilidade = () => {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    Papa.parse("/data/ceara/climatologia.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        const rows = result.data.filter((d) => d.scenario && d.week);

        const grouped = {};
        rows.forEach((row) => {
          if (!grouped[row.scenario]) {
            grouped[row.scenario] = {
              scenario: row.scenario,
              label: row.scenario_label,
            };
          }
          const prob = row.probability * 100;
          const ciLow = row.ci_low * 100;
          const ciHigh = row.ci_high * 100;

          if (row.week === "week3") {
            grouped[row.scenario].week3 = prob;
            grouped[row.scenario].week3_err = [prob - ciLow, ciHigh - prob];
          } else {
            grouped[row.scenario].week4 = prob;
            grouped[row.scenario].week4_err = [prob - ciLow, ciHigh - prob];
          }
        });

        const order = [
          "any_relevant",
          "surfable",
          "good",
          "strong",
          "very_good",
          "exceptional",
        ];
        const sorted = order
          .filter((k) => grouped[k])
          .map((k) => grouped[k]);

        setChartData(sorted);
      },
    });
  }, []);

  if (chartData.length === 0) return null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;
    return (
      <div className="bg-white p-3 border border-gray-200 rounded shadow text-sm">
        <p className="font-semibold mb-1">{label}</p>
        {payload.map((entry) => (
          <p key={entry.name} style={{ color: entry.color }}>
            {entry.name}: {entry.value.toFixed(1)}%
          </p>
        ))}
      </div>
    );
  };

  return (
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
      <h2 className="text-xl font-bold mb-2 text-gray-900">
        Probabilidade de Swell N/NE — Comparação por Semana
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Barras de erro mostram o intervalo de confiança de Wilson (95%).
      </p>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11 }}
            angle={-15}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            domain={[0, 110]}
            label={{
              value: "Probabilidade (%)",
              angle: -90,
              position: "insideLeft",
              offset: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine y={50} stroke="#9ca3af" strokeDasharray="3 3" />
          <Bar
            dataKey="week3"
            name="15–21 março"
            fill="#2563eb"
            radius={[4, 4, 0, 0]}
          >
            <ErrorBar
              dataKey="week3_err"
              width={4}
              strokeWidth={1.5}
              stroke="#1e40af"
            />
          </Bar>
          <Bar
            dataKey="week4"
            name="22–28 março"
            fill="#f97316"
            radius={[4, 4, 0, 0]}
          >
            <ErrorBar
              dataKey="week4_err"
              width={4}
              strokeWidth={1.5}
              stroke="#c2410c"
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
};

export default GraficoProbabilidade;
