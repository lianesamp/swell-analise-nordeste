import { useEffect, useState } from "react";
import Papa from "papaparse";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from "recharts";

const SwellMensal = () => {
  const [dados, setDados] = useState([]);

  useEffect(() => {
    Papa.parse("/data/dados_swell_nordeste.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        const filtrados = result.data.filter(d => d.month && d.swell_period);

        const somaPorMes = {};
        const contagem = {};

        filtrados.forEach(({ month, swell_period }) => {
          if (!somaPorMes[month]) {
            somaPorMes[month] = 0;
            contagem[month] = 0;
          }
          somaPorMes[month] += swell_period;
          contagem[month] += 1;
        });

        const mediaPorMes = Object.keys(somaPorMes).map(m => ({
          month: parseInt(m),
          swell_period: (somaPorMes[m] / contagem[m]).toFixed(2)
        })).sort((a, b) => a.month - b.month);

        setDados(mediaPorMes);
      }
    });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Período Médio por Mês</h2>
      <BarChart width={700} height={300} data={dados}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="swell_period" name="Período Médio (s)" fill="#2b6cb0" />
      </BarChart>
    </div>
  );
};

export default SwellMensal;