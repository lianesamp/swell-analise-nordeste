import { useEffect, useState } from "react";
import Papa from "papaparse";

const SwellResumoAno = () => {
  const [resumo, setResumo] = useState([]);

  useEffect(() => {
    Papa.parse("/data/dados_swell_nordeste.csv", {
      download: true,
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        const filtrados = result.data.filter(d => d.year && d.swell_height && d.swell_direction);

        const agrupados = {};

        filtrados.forEach(({ year, swell_height, swell_direction }) => {
          if (!agrupados[year]) agrupados[year] = { total_height: 0, total_direction: 0, count: 0 };
          agrupados[year].total_height += swell_height;
          agrupados[year].total_direction += swell_direction;
          agrupados[year].count += 1;
        });

        const resumo = Object.keys(agrupados).map(y => ({
          year: parseInt(y),
          altura_media: (agrupados[y].total_height / agrupados[y].count).toFixed(2),
          direcao_media: (agrupados[y].total_direction / agrupados[y].count).toFixed(2)
        })).sort((a, b) => a.year - b.year);

        setResumo(resumo);
      }
    });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Altura e Direção Média por Ano</h2>
      <table className="w-full text-left border border-gray-200">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2">Ano</th>
            <th className="p-2">Altura Média (m)</th>
            <th className="p-2">Direção Média (°)</th>
          </tr>
        </thead>
        <tbody>
          {resumo.map(({ year, altura_media, direcao_media }) => (
            <tr key={year} className="border-t">
              <td className="p-2">{year}</td>
              <td className="p-2">{altura_media}</td>
              <td className="p-2">{direcao_media}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SwellResumoAno;