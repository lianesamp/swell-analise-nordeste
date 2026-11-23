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

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-cyan-50/30 to-slate-50">
      <Navbar />

      <main className="pb-12">
        <div id="home">
          <BannerCeara />
        </div>
        <div id="forecast">
          <ForecastIracema />
          <SwellTideChart />
        </div>
        <div id="probabilidade">
          <ProbabilidadeCenarios />
        </div>
        <div id="grafico">
          <GraficoProbabilidade />
        </div>
        <div id="direccion">
          <DireccionSwell />
        </div>
        <div id="distribucion">
          <DistribucionEventos />
        </div>
        <div id="timeline">
          <TimelineAnual />
        </div>
        <div id="janelas">
          <JanelasSurfaveis />
        </div>
        <div id="eventos">
          <EventosDetalle />
        </div>
      </main>

      <footer className="bg-slate-900 text-slate-400 py-8 mt-12">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm">
            Swell Ceara — Surf climatology for northeast Brazil
          </p>
          <p className="text-xs mt-2 text-slate-500">
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
