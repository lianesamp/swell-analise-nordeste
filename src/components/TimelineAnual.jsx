import { useState } from "react";
import { useCearaData } from "../hooks/useCearaData";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Cell,
} from "recharts";

const TimelineAnual = () => {
  const { resumoAnual, loading } = useCearaData();
  const [activeWeek, setActiveWeek] = useState("week3");

  const data = resumoAnual.filter((d) => d.year && d.week);

  const weekData = data
    .filter((d) => d.week === activeWeek)
    .sort((a, b) => a.year - b.year);

  if (loading || weekData.length === 0) return null;

  const weekLabel =
    activeWeek === "week3" ? "15–21 março" : "22–28 março";

  const yearsWithEvent = weekData.filter((d) => d.had_event === true || d.had_event === "True").length;

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload[0]) return null;
    const d = payload[0].payload;
    const hadEvent = d.had_event === true || d.had_event === "True";
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-lg p-3 text-sm text-white">
        <p className="font-semibold">{d.year}</p>
        {hadEvent ? (
          <>
            <p>Eventos: {d.n_events}</p>
            <p>Max Hs: {d.max_height}m</p>
            <p>Max Tp: {d.max_period}s</p>
            <p>Max duração: {d.max_duration}h</p>
            <p>Direção: {d.dominant_direction}</p>
          </>
        ) : (
          <p className="text-slate-400">Sem evento detectado</p>
        )}
      </div>
    );
  };

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        Linha do Tempo — Swell N/NE por Ano
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Cenário &quot;good&quot; (Tp médio &ge; 9s, Hs &ge; 1.0m).
        Barras coloridas = anos com evento. Barras cinzas = sem evento.
        {" "}<strong>{yearsWithEvent}/{weekData.length}</strong> anos com evento.
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

      <ResponsiveContainer width="100%" height={350}>
        <BarChart
          data={weekData}
          margin={{ top: 10, right: 20, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 10 }}
            interval={4}
            label={{
              value: "Ano",
              position: "insideBottom",
              offset: -10,
            }}
          />
          <YAxis
            domain={[0, 2]}
            label={{
              value: "Max Hs (m)",
              angle: -90,
              position: "insideLeft",
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={1.0}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            label={{ value: "1.0m", position: "right", fontSize: 10 }}
          />
          <Bar dataKey="max_height" radius={[2, 2, 0, 0]}>
            {weekData.map((entry, index) => {
              const hadEvent =
                entry.had_event === true || entry.had_event === "True";
              return (
                <Cell
                  key={`cell-${index}`}
                  fill={
                    hadEvent
                      ? activeWeek === "week3"
                        ? "#0891b2"
                        : "#f59e0b"
                      : "#e2e8f0"
                  }
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs text-slate-400 mt-2 text-center">
        {weekLabel} — ERA5 1979–2025
      </p>
    </section>
  );
};

export default TimelineAnual;
