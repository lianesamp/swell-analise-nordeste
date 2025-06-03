
import SwellChart from './components/SwellChart';
import SwellMensal from './components/SwellMensal';
import SwellMaxPeriodoPorAno from './components/SwellMaxPeriodoAnual';
import Navbar from './components/Navbar';
import BannerInicial from './components/BannerInicial';


function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav>
        <Navbar/>
      </nav>
      <div id='home'>
        <BannerInicial/>
      </div>
      <main className="flex justify-center" id='resumo'>
        <SwellChart />
      </main>
      <div className="flex justify-center " id='resumo-mensal'>
        <SwellMensal/>
      </div>
      <div className="flex justify-center" id='swell-ano'>
        <SwellMaxPeriodoPorAno/>
      </div>
    </div>
  );
}

export default App;
