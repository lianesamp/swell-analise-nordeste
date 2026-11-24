const sections = [
  {
    id: "forecast",
    title: "Live Forecast",
    location: "Praia de Iracema, Fortaleza",
    status: "Live",
    statusColor: "bg-emerald-500",
    description:
      "7-day surf forecast with wave transformation (shoaling + refraction), tide overlay, and surfability ratings. Updated in real time from Open-Meteo.",
  },
  {
    id: "march-analysis",
    title: "March Swell Analysis",
    location: "Jericoacoara trip planning",
    status: "Complete",
    statusColor: "bg-cyan-500",
    description:
      "47 years of ERA5 data (1979-2025) comparing two March windows (15-21 vs 22-28) to find the best week for N/NE swell probability, duration, and intensity.",
  },
  {
    id: "historical",
    title: "Historical Patterns",
    location: "Fortaleza, 10+ years",
    status: "Coming Soon",
    statusColor: "bg-amber-500",
    description:
      "Long-term pattern research: swell seasonality, return periods, and trend analysis using decade-scale data for Fortaleza.",
  },
];

const BannerCeara = () => {
  return (
    <section className="max-w-5xl mx-auto my-6 space-y-6 px-4">
      {/* Title */}
      <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-8 md:p-10 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-teal-400 to-amber-400"></div>

        <h1 className="text-3xl md:text-5xl font-extrabold mb-4 text-center tracking-tight text-slate-900">
          Swell Analysis — Northeast Brazil
        </h1>

        <p className="text-sm text-center text-slate-400 mb-6 font-medium tracking-wide uppercase">
          Surf climatology and forecasting for Ceara
        </p>

        <p className="text-base md:text-lg leading-relaxed max-w-4xl mx-auto text-slate-600 text-center">
          Three independent analyses exploring swell conditions on the
          northeast coast of Brazil — from real-time forecasts to multi-decade
          climate research.
        </p>
      </div>

      {/* Section cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {sections.map((section) => (
          <a
            key={section.id}
            href={`#${section.id}`}
            className="group bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-xl shadow-md shadow-slate-200/40 p-5 hover:shadow-lg hover:border-cyan-300/60 transition-all duration-200"
          >
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`inline-block w-2 h-2 rounded-full ${section.statusColor}`}
              ></span>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {section.status}
              </span>
            </div>

            <h2 className="text-lg font-bold text-slate-900 group-hover:text-cyan-700 transition-colors mb-1">
              {section.title}
            </h2>

            <p className="text-xs font-medium text-slate-400 mb-3">
              {section.location}
            </p>

            <p className="text-sm text-slate-600 leading-relaxed">
              {section.description}
            </p>
          </a>
        ))}
      </div>
    </section>
  );
};

export default BannerCeara;
