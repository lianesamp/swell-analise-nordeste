
import Navbar from './components/Navbar';
import BannerCeara from './components/BannerCeara';
import ProbabilidadeCenarios from './components/ProbabilidadeCenarios';
import GraficoProbabilidade from './components/GraficoProbabilidade';
import TimelineAnual from './components/TimelineAnual';
import JanelasSurfaveis from './components/JanelasSurfaveis';


function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav>
        <Navbar/>
      </nav>
      <div id='home'>
        <BannerCeara/>
      </div>
      <div id='probabilidade'>
        <ProbabilidadeCenarios/>
      </div>
      <div id='grafico'>
        <GraficoProbabilidade/>
      </div>
      <div id='timeline'>
        <TimelineAnual/>
      </div>
      <div id='janelas'>
        <JanelasSurfaveis/>
      </div>
    </div>
  );
}

export default App;
