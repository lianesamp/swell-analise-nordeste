const BannerInicial = () => {
  return (
    <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-8 max-w-5xl mx-auto my-8">
      <h1 className=" md:text-4xl font-bold mb-6 text-center text-gray-900">
        Explorando o Swell no Nordeste do Brasil
      </h1>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        Este projeto nasceu da curiosidade em entender como o swell tem se comportado na região Nordeste do Brasil ao longo dos últimos 10 anos (2014-2024).
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        Para isso, foram utilizados dados de reanálise ERA5, uma base confiável do ECMWF, focando numa área costeira específica do Nordeste (latitudes -1° a -10° e longitudes -33° a -45°). Excluindo os meses de junho, julho e agosto, que historicamente têm pouca entrada de swell de Norte e Nordeste (os atuantes na região).
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        A análise começou no Google Colab, explorando e validando os dados, criando gráficos para entender as tendências, como o possível declínio no período de swell, e eventos marcantes como o swell histórico de março de 2018.
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700">
        Agora, todo esse trabalho está disponível nesta interface, que mostra de forma visual e interativa as variações de altura, período e direção do swell, com filtros para facilitar a navegação pelos dados.
      </p>

      <p className="text-md md:text-lg leading-relaxed mb-4 max-w-4xl mx-auto text-justify text-gray-700 font-semibold">
        Lembrando que este é um estudo exploratório, feito por curiosidade e paixão pelo mar e pelo surf. Pesquisas mais aprofundadas e técnicas são recomendadas para aplicações científicas ou profissionais.
      </p>

    </section>
  );
};

export default BannerInicial;
