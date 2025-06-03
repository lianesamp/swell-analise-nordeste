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

const SwellMaxPeriodoPorAno = () => {
  const [dados, setDados] = useState([]);
  const [anoSelecionado, setAnoSelecionado] = useState(2018);

  useEffect(() => {
    Papa.parse("/data/dados_swell_nordeste.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        
        const filtrados = result.data.filter(
          d =>
            d.year &&
            d.month &&
            d.swell_period &&
            !isNaN(d.swell_period)
        );

        setDados(filtrados);
      },
    });
  }, []);

  
  const maxPorMes = {};
  dados
    .filter(d => d.year === anoSelecionado)
    .forEach(({ month, swell_period }) => {
      if (!maxPorMes[month] || swell_period > maxPorMes[month]) {
        maxPorMes[month] = swell_period;
      }
    });

  const dadosGrafico = Object.keys(maxPorMes)
    .map(m => ({
      month: parseInt(m),
      max_periodo: +maxPorMes[m].toFixed(2),
    }))
    .sort((a, b) => a.month - b.month);

 
  const nomeMes = (m) => {
    const nomes = [
      "Jan", "Fev", "Mar", "Abr", "Mai",
      "Jun", "Jul", "Ago", "Set", "Out",
      "Nov", "Dez",
    ];
    return nomes[m - 1] || m;
  };

 
  const anos = [];
  for (let y = 2014; y <= 2024; y++) anos.push(y);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">
        Maior Período de Swell por Mês - Ano {anoSelecionado}
      </h2>

      <div className="mb-4">
        <label htmlFor="ano" className="mr-2 font-semibold">
          Selecione o Ano:
        </label>
        <select
          id="ano"
          value={anoSelecionado}
          onChange={(e) => setAnoSelecionado(parseInt(e.target.value))}
          className="border border-gray-300 rounded p-1"
        >
          {anos.map((ano) => (
            <option key={ano} value={ano}>
              {ano}
            </option>
          ))}
        </select>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={dadosGrafico}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="month"
            tickFormatter={nomeMes}
            label={{ value: "Mês", position: "insideBottom", offset: -10 }}
            ticks={dadosGrafico.map((d) => d.month)}
          />
          <YAxis
            label={{
              value: "Período Máximo (s)",
              angle: -90,
              position: "insideLeft",
            }}
            domain={["dataMin - 1", "dataMax + 1"]}
          />
          <Tooltip formatter={(value) => `${value} s`} labelFormatter={nomeMes} />
          <Legend />
          <Line
            type="monotone"
            dataKey="max_periodo"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ r: 5 }}
            activeDot={{ r: 7 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SwellMaxPeriodoPorAno;
