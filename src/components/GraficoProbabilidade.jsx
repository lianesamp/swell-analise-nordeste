import { useMemo } from "react";
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
  ErrorBar,
} from "recharts";

const SCENARIO_ORDER = [
  "any_relevant",
  "surfable",
  "good",
  "strong",
  "very_good",
  "exceptional",
];

const GraficoProbabilidade = () => {
  const { climatologia, loading } = useCearaData();

  const chartData = useMemo(() => {
    const rows = climatologia.filter((d) => d.scenario && d.week);

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

    return SCENARIO_ORDER
      .filter((k) => grouped[k])
      .map((k) => grouped[k]);
  }, [climatologia]);

  if (loading || chartData.length === 0) return null;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-lg p-3 text-sm text-white">
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
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        N/NE Swell Probability — Week Comparison
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Error bars show the Wilson confidence interval (95%).
      </p>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
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
            domain={[0, 110]}
            label={{
              value: "Probability (%)",
              angle: -90,
              position: "insideLeft",
              offset: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine y={50} stroke="#94a3b8" strokeDasharray="3 3" />
          <Bar
            dataKey="week3"
            name="Mar 15–21"
            fill="#0891b2"
            radius={[4, 4, 0, 0]}
          >
            <ErrorBar
              dataKey="week3_err"
              width={4}
              strokeWidth={1.5}
              stroke="#0e7490"
            />
          </Bar>
          <Bar
            dataKey="week4"
            name="Mar 22–28"
            fill="#f59e0b"
            radius={[4, 4, 0, 0]}
          >
            <ErrorBar
              dataKey="week4_err"
              width={4}
              strokeWidth={1.5}
              stroke="#b45309"
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
};

export default GraficoProbabilidade;
