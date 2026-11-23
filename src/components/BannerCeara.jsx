const BannerCeara = () => {
  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-8 md:p-10 max-w-5xl mx-auto my-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-teal-400 to-amber-400"></div>

      <h1 className="text-3xl md:text-5xl font-extrabold mb-6 text-center tracking-tight text-slate-900">
        Swell Climatology — Ceará
      </h1>

      <p className="text-sm text-center text-slate-400 mb-8 font-medium tracking-wide uppercase">
        Praia de Iracema / Lido Manso — Fortaleza, Brazil
      </p>

      <p className="text-base md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-slate-600">
        This project analyzes <strong>47 years of historical swell data</strong> (1979–2025)
        to answer a practical question: what is the probability of finding favorable
        N/NE swell conditions for surfing in Ceará during March?
      </p>

      <p className="text-base md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-slate-600">
        The data comes from <strong>ERA5</strong> (ECMWF), a global reanalysis that reconstructs
        past climate by combining observations with numerical models. The offshore reference point
        is <strong> -3.5°, -38.5°</strong>, near Fortaleza. The analyzed variables are:
        significant total swell height, mean period, and direction.
      </p>

      <p className="text-base md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-slate-600">
        The analysis focuses on two March windows: <strong>15–21</strong> (week 3)
        and <strong>22–28</strong> (week 4), comparing the frequency, duration, and intensity
        of North and Northeast swells in each period.
      </p>

      <div className="bg-cyan-50/60 border border-cyan-200/60 rounded-xl p-4 max-w-4xl mx-auto mt-6">
        <p className="text-sm text-cyan-800">
          <strong>Important:</strong> The data is offshore — beach conditions depend on
          bathymetry, local wind, and tide. This is a climatological probability analysis,
          not a surf forecast.
        </p>
      </div>
    </section>
  );
};

export default BannerCeara;
