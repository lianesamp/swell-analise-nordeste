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
import OverviewCards from './components/OverviewCards';
import SeasonalityChart from './components/SeasonalityChart';
import MonthlyHeatmap from './components/MonthlyHeatmap';
import EventosSeason from './components/EventosSeason';

function SectionDivider() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="h-px bg-gradient-to-r from-transparent via-slate-300/60 to-transparent"></div>
    </div>
  );
}

function SectionHeader({ label, labelColor, title, subtitle }) {
  return (
    <div className="max-w-5xl mx-auto px-4 pt-6 pb-4">
      {label && (
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full mb-3 ${labelColor}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
          {label}
        </span>
      )}
      <h2 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-2 text-sm text-slate-500 max-w-3xl">{subtitle}</p>
      )}
      <div className="mt-4 h-px bg-gradient-to-r from-cyan-400/60 via-slate-200 to-transparent"></div>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-cyan-50/30 to-slate-50">
      <Navbar />

      <main className="pb-16">
        {/* Hub / Landing */}
        <div id="home">
          <BannerCeara />
        </div>

        <SectionDivider />

        {/* ── Front 1: Live Forecast ── */}
        <section id="forecast">
          <SectionHeader
            label="Live"
            labelColor="bg-emerald-100 text-emerald-700"
            title="Live Forecast — Praia de Iracema"
            subtitle="7-day surf forecast using Open-Meteo marine data, wave transformation physics (shoaling + refraction), and the Mucuripe tide table."
          />
          <ForecastIracema />
          <SwellTideChart />
        </section>

        <SectionDivider />

        {/* ── Front 2: March Swell Analysis ── */}
        <section id="march-analysis">
          <SectionHeader
            label="Complete"
            labelColor="bg-cyan-100 text-cyan-700"
            title="March Swell Analysis — Jericoacoara Trip"
            subtitle="47 years of ERA5 reanalysis (1979-2025) comparing two March windows to find the best week for N/NE swell probability, duration, and intensity."
          />
          <ProbabilidadeCenarios />
          <GraficoProbabilidade />
          <DireccionSwell />
          <DistribucionEventos />
          <TimelineAnual />
          <JanelasSurfaveis />
          <EventosDetalle />
        </section>

        <SectionDivider />

        {/* ── Front 3: Historical Patterns ── */}
        <section id="historical">
          <SectionHeader
            label="In Progress"
            labelColor="bg-amber-100 text-amber-700"
            title="Historical Patterns — Fortaleza"
            subtitle="Swell seasonality analysis using ERA5 reanalysis (Sep–May). Data is being acquired — statistics will sharpen as more years are added."
          />
          <OverviewCards />
          <SeasonalityChart />
          <MonthlyHeatmap />
          <EventosSeason />
        </section>
      </main>

      <footer className="bg-slate-900 text-slate-400 py-10">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm font-medium text-slate-300">
            Swell Analysis — Northeast Brazil
          </p>
          <p className="text-xs mt-3 text-slate-500">
            Data: ERA5 (ECMWF) 1979–2025 · Forecast: Open-Meteo Marine API · Tides: Marinha do Brasil
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
