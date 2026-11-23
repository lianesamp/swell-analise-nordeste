const BannerCeara = () => {
  return (
    <section className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-8 md:p-10 max-w-5xl mx-auto my-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-teal-400 to-amber-400"></div>

      <h1 className="text-3xl md:text-5xl font-extrabold mb-6 text-center tracking-tight text-slate-900">
        Climatologia de Swell no Ceará
      </h1>

      <p className="text-sm text-center text-slate-400 mb-8 font-medium tracking-wide uppercase">
        Praia de Iracema / Lido Manso — Fortaleza
      </p>

      <p className="text-base md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-slate-600">
        Este projeto analisa <strong>47 anos de dados históricos de swell</strong> (1979–2025)
        para responder uma pergunta prática: qual é a probabilidade de encontrar condições
        favoráveis de swell N/NE para surf no Ceará durante março?
      </p>

      <p className="text-base md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-slate-600">
        Os dados vêm do <strong>ERA5</strong> (ECMWF), uma reanálise global que reconstrói o clima
        passado combinando observações com modelos numéricos. O ponto de referência offshore é
        <strong> -3.5°, -38.5°</strong>, próximo a Fortaleza. As variáveis analisadas são:
        altura significativa do swell total, período médio e direção.
      </p>

      <p className="text-base md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-slate-600">
        A análise foca em duas janelas de março: <strong>15–21</strong> (semana 3)
        e <strong>22–28</strong> (semana 4), comparando a frequência, duração e intensidade
        dos swells de Norte e Nordeste em cada período.
      </p>

      <div className="bg-cyan-50/60 border border-cyan-200/60 rounded-xl p-4 max-w-4xl mx-auto mt-6">
        <p className="text-sm text-cyan-800">
          <strong>Importante:</strong> Os dados são offshore — a condição na praia depende de
          batimetria, vento local e maré. Esta é uma análise probabilística climatológica,
          não uma previsão de surf.
        </p>
      </div>
    </section>
  );
};

export default BannerCeara;
