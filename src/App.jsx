import Navbar from './components/Navbar';
import BannerCeara from './components/BannerCeara';
import ForecastIracema from './components/ForecastIracema';
import SwellTideChart from './components/SwellTideChart';
import ProbabilidadeCenarios from './components/ProbabilidadeCenarios';
import GraficoProbabilidade from './components/GraficoProbabilidade';
import DireccionSwell from './components/DireccionSwell';
import DistribucionEventos from './components/DistribucionEventos';
import TimelineAnual from './components/TimelineAnual';
import JanelasSurfaveis from './components/JanelasSurfaveis';
import EventosDetalle from './components/EventosDetalle';

function SectionHeader({ title, subtitle }) {
  return (
    <div className="max-w-5xl mx-auto px-4 pt-10 pb-4">
      <h2 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
      )}
      <div className="mt-3 h-px bg-gradient-to-r from-cyan-400/60 via-slate-200 to-transparent"></div>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-cyan-50/30 to-slate-50">
      <Navbar />

      <main className="pb-12">
        {/* Hub / Landing */}
        <div id="home">
          <BannerCeara />
        </div>

        {/* ── Front 1: Live Forecast ── */}
        <section id="forecast">
          <SectionHeader
            title="Live Forecast — Praia de Iracema"
            subtitle="7-day surf forecast using Open-Meteo data, wave transformation physics, and Mucuripe tide table."
          />
          <ForecastIracema />
          <SwellTideChart />
        </section>

        {/* ── Front 2: March Swell Analysis ── */}
        <section id="march-analysis">
          <SectionHeader
            title="March Swell Analysis — Jericoacoara Trip"
            subtitle="47 years of ERA5 reanalysis (1979-2025) comparing March weeks 15-21 vs 22-28 for N/NE swell probability."
          />
          <ProbabilidadeCenarios />
          <GraficoProbabilidade />
          <DireccionSwell />
          <DistribucionEventos />
          <TimelineAnual />
          <JanelasSurfaveis />
          <EventosDetalle />
        </section>

        {/* ── Front 3: Historical Patterns (Coming Soon) ── */}
        <section id="historical">
          <SectionHeader
            title="Historical Patterns — Fortaleza"
            subtitle="Long-term swell research using 10+ years of data. This section is under development."
          />
          <div className="max-w-5xl mx-auto px-4 my-6">
            <div className="bg-white/80 backdrop-blur-sm border border-amber-200/60 rounded-xl shadow-md p-8 text-center">
              <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-700 text-xs font-semibold uppercase tracking-wider rounded-full px-3 py-1 mb-4">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                Coming Soon
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Swell Pattern Research
              </h3>
              <p className="text-slate-600 max-w-2xl mx-auto leading-relaxed mb-4">
                We are working on acquiring at least 10 years of continuous swell data
                for Fortaleza to investigate seasonality, return periods, and long-term
                trends in N/NE swell arrivals. The data pipeline already exists — we
                need to source and process the full dataset.
              </p>
              <p className="text-sm text-slate-400">
                Data sources under evaluation: ERA5 (ECMWF), WaveWatch III (NOAA)
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-slate-900 text-slate-400 py-8 mt-12">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm">
            Swell Analysis — Northeast Brazil
          </p>
          <p className="text-xs mt-2 text-slate-500">
            Data: ERA5 (ECMWF) 1979-2025 · Forecast: Open-Meteo Marine API · Tides: Marinha do Brasil
          </p>
          <p className="text-xs mt-1 text-slate-500">
            Built with React, Recharts & Tailwind CSS
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
