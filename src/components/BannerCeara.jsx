const BannerCeara = () => {
  return (
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-8 max-w-5xl mx-auto my-8">
      <h1 className="text-2xl md:text-4xl font-bold mb-6 text-center text-gray-900">
        Climatologia de Swell no Ceará
      </h1>

      <p className="text-sm text-center text-gray-500 mb-6">
        Praia de Iracema / Lido Manso — Fortaleza
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        Este projeto analisa <strong>47 anos de dados históricos de swell</strong> (1979–2025)
        para responder uma pergunta prática: qual é a probabilidade de encontrar condições
        favoráveis de swell N/NE para surf no Ceará durante março?
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        Os dados vêm do <strong>ERA5</strong> (ECMWF), uma reanálise global que reconstrói o clima
        passado combinando observações com modelos numéricos. O ponto de referência offshore é
        <strong> -3.5°, -38.5°</strong>, próximo a Fortaleza. As variáveis analisadas são:
        altura significativa do swell total, período médio e direção.
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        A análise foca em duas janelas de março: <strong>15–21</strong> (semana 3)
        e <strong>22–28</strong> (semana 4), comparando a frequência, duração e intensidade
        dos swells de Norte e Nordeste em cada período.
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-4xl mx-auto mt-6">
        <p className="text-sm text-blue-800">
          <strong>Importante:</strong> Os dados são offshore — a condição na praia depende de
          batimetria, vento local e maré. Esta é uma análise probabilística climatológica,
          não uma previsão de surf.
        </p>
      </div>
    </section>
  );
};

export default BannerCeara;
