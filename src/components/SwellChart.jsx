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

const SwellTendenciaAno = () => {
  const [dadosAno, setDadosAno] = useState([]);

  useEffect(() => {
    Papa.parse("/data/dados_swell_nordeste.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        const filtrados = result.data.filter(
          d => d.year && d.swell_period && !isNaN(d.swell_period)
        );

        const agrupados = {};
        filtrados.forEach(({ year, swell_period }) => {
          if (!agrupados[year]) {
            agrupados[year] = { total: 0, count: 0 };
          }
          agrupados[year].total += swell_period;
          agrupados[year].count += 1;
        });

        const resumo = Object.keys(agrupados).map((y) => ({
          year: parseInt(y),
          periodo_medio: +(agrupados[y].total / agrupados[y].count).toFixed(2),
        })).sort((a, b) => a.year - b.year);

        setDadosAno(resumo);
      }
    });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Tendência do Período Médio de Swell por Ano</h2>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={dadosAno} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="year"
            label={{ value: 'Ano', position: 'insideBottom', offset: -10 }}
            tickCount={dadosAno.length}
          />
          <YAxis
            label={{ value: 'Período Médio (s)', angle: -90, position: 'insideLeft' }}
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <Tooltip formatter={value => `${value} s`} />
          <Legend />
          <Line
            type="monotone"
            dataKey="periodo_medio"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SwellTendenciaAno;
