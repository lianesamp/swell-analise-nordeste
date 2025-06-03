# Análise do Swell no Nordeste do Brasil (2014-2024)

## Sobre o Projeto

Este projeto é uma análise exploratória sobre o comportamento do swell na região Nordeste do Brasil, com foco na costa próxima a Fortaleza. A iniciativa surgiu da minha curiosidade pessoal em entender se a entrada de swell tem diminuído ao longo dos últimos 10 anos, especialmente por sua importância para o surf e ecossistemas marinhos.

Os dados foram coletados da reanálise ERA5, uma base global de dados climáticos do ECMWF, utilizada frequentemente em estudos oceanográficos e meteorológicos.

---

## Área e Período Analisados

- **Área geográfica**: entre as latitudes -1° e -10°, e longitudes -33° a -45°, abrangendo a costa do Nordeste.
- **Período temporal**: 2014 a 2024, excluindo os meses de junho, julho e agosto, que historicamente têm baixa entrada de swell.
- **Frequência dos dados**: diária, às 12:00h.

---

## Metodologia

1. **Coleta de dados**  
   Os dados foram obtidos via API do CDS (Copernicus Data Store), focando nas variáveis:  
   - Altura significativa das ondas (swell + vento)  
   - Período médio do swell  
   - Direção média do swell  

2. **Análise exploratória no Google Colab**  
   - Validação dos dados (checagem de valores nulos, outliers)  
   - Cálculo de médias anuais e mensais para altura, período e direção do swell  
   - Identificação de eventos históricos, como o swell de março de 2018  
   - Geração de gráficos para visualização das tendências

3. **Desenvolvimento da interface React**  
   - Visualização interativa dos dados  
   - Filtros por ano para análise detalhada  
   - Representação clara das médias e máximos do swell

---

## Resultados e Observações

- Foi possível observar um possível declínio no período médio do swell ao longo da última década, o que pode impactar a frequência e qualidade das ondas para surf e demais atividades costeiras.
- O swell histórico de março de 2018 se destacou claramente nos dados mensais.
- A direção média do swell está concentrada entre 50° e 55°, indicando predominância do Nordeste.

---

## Uso e Exploração

- A interface está disponível para interação, permitindo navegar entre os anos e entender melhor os padrões de swell.
- O código está aberto para estudos, adaptações e aprimoramentos.

---

## Recomendações

Este estudo é exploratório e baseado em dados de reanálise. Para aplicações científicas ou operacionais, recomenda-se utilizar dados adicionais in situ e realizar análises mais robustas.

---
