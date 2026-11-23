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
    <div className="min-h-screen bg-gray-50">
      <Navbar />

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
    </div>
  );
}

export default App;
