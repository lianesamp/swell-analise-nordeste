import { useEffect, useState } from "react";
import Papa from "papaparse";

const probColor = (p) => {
  if (p >= 0.8) return "bg-green-100 text-green-800";
  if (p >= 0.5) return "bg-yellow-100 text-yellow-800";
  if (p >= 0.2) return "bg-orange-100 text-orange-800";
  return "bg-red-100 text-red-800";
};

const ProbabilidadeCenarios = () => {
  const [scenarios, setScenarios] = useState([]);

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
              name: row.scenario_label,
              period: row.period_min,
              height: row.height_min,
            };
          }
          grouped[row.scenario][row.week] = row;
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
          .map((k) => ({ key: k, ...grouped[k] }));

        setScenarios(sorted);
      },
    });
  }, []);

  if (scenarios.length === 0) return null;

  return (
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 max-w-5xl mx-auto my-8">
      <h2 className="text-xl font-bold mb-2 text-gray-900">
        Probabilidade de Swell N/NE por Cenário
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Probabilidade de pelo menos um evento por ano (ERA5, 1979–2025, 47 anos).
        IC = intervalo de confiança de Wilson 95%.
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left p-3 font-semibold">Cenário</th>
              <th className="text-center p-3 font-semibold">Tp min</th>
              <th className="text-center p-3 font-semibold">Hs min</th>
              <th className="text-center p-3 font-semibold">15–21 março</th>
              <th className="text-center p-3 font-semibold text-gray-400">IC 95%</th>
              <th className="text-center p-3 font-semibold">22–28 março</th>
              <th className="text-center p-3 font-semibold text-gray-400">IC 95%</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((sc) => {
              const w3 = sc.week3;
              const w4 = sc.week4;
              const isGood = sc.key === "good";

              return (
                <tr
                  key={sc.key}
                  className={`border-b border-gray-100 ${isGood ? "ring-2 ring-blue-300 ring-inset" : ""}`}
                >
                  <td className={`p-3 font-medium ${isGood ? "text-blue-700" : "text-gray-800"}`}>
                    {sc.name}
                    {isGood && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
                        referência
                      </span>
                    )}
                  </td>
                  <td className="text-center p-3 text-gray-600">
                    {sc.period}s
                  </td>
                  <td className="text-center p-3 text-gray-600">
                    {sc.height > 0 ? `${sc.height}m` : "—"}
                  </td>

                  {w3 ? (
                    <>
                      <td className={`text-center p-3 font-bold rounded ${probColor(w3.probability)}`}>
                        {(w3.probability * 100).toFixed(1)}%
                        <span className="block text-xs font-normal opacity-70">
                          {w3.years_with_event}/{w3.total_years}
                        </span>
                      </td>
                      <td className="text-center p-3 text-xs text-gray-400">
                        {(w3.ci_low * 100).toFixed(0)}–{(w3.ci_high * 100).toFixed(0)}%
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="text-center p-3">—</td>
                      <td className="text-center p-3">—</td>
                    </>
                  )}

                  {w4 ? (
                    <>
                      <td className={`text-center p-3 font-bold rounded ${probColor(w4.probability)}`}>
                        {(w4.probability * 100).toFixed(1)}%
                        <span className="block text-xs font-normal opacity-70">
                          {w4.years_with_event}/{w4.total_years}
                        </span>
                      </td>
                      <td className="text-center p-3 text-xs text-gray-400">
                        {(w4.ci_low * 100).toFixed(0)}–{(w4.ci_high * 100).toFixed(0)}%
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="text-center p-3">—</td>
                      <td className="text-center p-3">—</td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default ProbabilidadeCenarios;
