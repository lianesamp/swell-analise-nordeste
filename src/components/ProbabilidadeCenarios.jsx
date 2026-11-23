import { useMemo } from "react";
import { useCearaData } from "../hooks/useCearaData";

const SCENARIO_ORDER = [
  "any_relevant",
  "surfable",
  "good",
  "strong",
  "very_good",
  "exceptional",
];

const probColor = (p) => {
  if (p >= 0.8) return "bg-teal-100 text-teal-800";
  if (p >= 0.5) return "bg-cyan-100 text-cyan-800";
  if (p >= 0.2) return "bg-amber-100 text-amber-800";
  return "bg-rose-100 text-rose-800";
};

const ProbabilidadeCenarios = () => {
  const { climatologia, loading } = useCearaData();

  const scenarios = useMemo(() => {
    const rows = climatologia.filter((d) => d.scenario && d.week);
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

    return SCENARIO_ORDER
      .filter((k) => grouped[k])
      .map((k) => ({ key: k, ...grouped[k] }));
  }, [climatologia]);

  if (loading || scenarios.length === 0) return null;

  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-6 md:p-8 max-w-5xl mx-auto my-6">
      <h2 className="text-xl font-bold mb-2 tracking-tight text-slate-900">
        N/NE Swell Probability by Scenario
      </h2>
      <p className="text-sm text-slate-500 mb-4">
        Probability of at least one event per year (ERA5, 1979–2025, 47 years).
        CI = Wilson 95% confidence interval.
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200">
              <th className="text-left p-3 font-semibold text-xs uppercase tracking-wider text-slate-600">Scenario</th>
              <th className="text-center p-3 font-semibold text-xs uppercase tracking-wider text-slate-600">Tp min</th>
              <th className="text-center p-3 font-semibold text-xs uppercase tracking-wider text-slate-600">Hs min</th>
              <th className="text-center p-3 font-semibold text-xs uppercase tracking-wider text-slate-600">Mar 15–21</th>
              <th className="text-center p-3 font-semibold text-xs uppercase tracking-wider text-slate-400">95% CI</th>
              <th className="text-center p-3 font-semibold text-xs uppercase tracking-wider text-slate-600">Mar 22–28</th>
              <th className="text-center p-3 font-semibold text-xs uppercase tracking-wider text-slate-400">95% CI</th>
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
                  className={`border-b border-slate-100 hover:bg-cyan-50/30 transition-colors duration-150 ${isGood ? "ring-2 ring-cyan-400/50 ring-inset bg-cyan-50/30" : ""}`}
                >
                  <td className={`p-3 font-medium ${isGood ? "text-cyan-700" : "text-slate-800"}`}>
                    {sc.name}
                    {isGood && (
                      <span className="ml-2 text-xs bg-cyan-100 text-cyan-700 px-2 py-0.5 rounded-full">
                        reference
                      </span>
                    )}
                  </td>
                  <td className="text-center p-3 text-slate-600">
                    {sc.period}s
                  </td>
                  <td className="text-center p-3 text-slate-600">
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
                      <td className="text-center p-3 text-xs text-slate-400">
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
                      <td className="text-center p-3 text-xs text-slate-400">
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
