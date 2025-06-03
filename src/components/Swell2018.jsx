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
  Cell,
  LabelList,
} from "recharts";

const meses = [
  "", "Jan", "Fev", "Mar", "Abr", "Mai",
  
  "Set", "Out", "Nov", "Dez"
];

const SwellPeriodo2018 = () => {
  const [dados2018, setDados2018] = useState([]);

  useEffect(() => {
    Papa.parse("/data/dados_swell_nordeste.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        
        const filtrados = result.data.filter(
          d => d.year === 2018 && d.swell_period && !isNaN(d.swell_period)
        );

        const agrupados = {};
        filtrados.forEach(({ month, swell_period }) => {
          if (!agrupados[month]) {
            agrupados[month] = { total: 0, count: 0 };
          }
          agrupados[month].total += swell_period;
          agrupados[month].count += 1;
        });

        const resumo = Object.keys(agrupados).map(m => ({
          month: parseInt(m),
          periodo_medio: (agrupados[m].total / agrupados[m].count).toFixed(2),
        }));

        setDados2018(resumo);
      }
    });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Período Médio do Swell - 2018</h2>
      <p className="mb-4">
        Destaque para <strong>março</strong>, mês do swell histórico, com período médio alto.
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={dados2018} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="month"
            tickFormatter={m => meses[m] || `Mês ${m}`} 
            label={{ value: "Mês", position: "insideBottom", offset: -10 }}
            domain={['dataMin', 'dataMax']}
          />
          <YAxis
            label={{ value: "Período (s)", angle: -90, position: "insideLeft" }}
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <Tooltip formatter={value => `${value} s`} labelFormatter={m => meses[m] || `Mês ${m}`} />
          <Bar dataKey="periodo_medio" >
            {
              dados2018.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.month === 3 ? "#f97316" : "#3b82f6"} // destaque em laranja no março
                />
              ))
            }
            <LabelList
              dataKey="periodo_medio"
              position="top"
              formatter={val => `${val}s`}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-4 text-sm text-gray-600">
        * Meses de junho, julho e agosto não possuem dados por serem meses de quase nenhuma entrada de swell.
      </p>
    </div>
  );
};

export default SwellPeriodo2018;
