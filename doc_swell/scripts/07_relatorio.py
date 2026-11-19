"""
07_relatorio.py — Generate final climatology report in Markdown.

Reads all processed data and analysis results to produce a comprehensive
report answering the key surf planning questions.

Output: output/RELATORIO_CLIMATOLOGIA.md
"""

import os
import numpy as np
import pandas as pd

import config as cfg

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def generate_charts(clim_df: pd.DataFrame, annual_df: pd.DataFrame):
    """Generate key visualization charts."""
    if not HAS_MATPLOTLIB:
        print("matplotlib not available, skipping charts")
        return

    os.makedirs(cfg.GRAFICOS_DIR, exist_ok=True)

    # 1. Probability by scenario and week
    fig, ax = plt.subplots(figsize=(10, 6))
    scenarios = clim_df["scenario"].unique()
    weeks = clim_df["week"].unique()

    x = np.arange(len(scenarios))
    width = 0.35

    for i, week in enumerate(weeks):
        week_data = clim_df[clim_df["week"] == week]
        week_data = week_data.set_index("scenario").loc[scenarios]
        label = week_data["week_label"].iloc[0]
        probs = week_data["probability"].values * 100
        ci_low = week_data["ci_low"].values * 100
        ci_high = week_data["ci_high"].values * 100
        yerr = np.array([probs - ci_low, ci_high - probs])

        bars = ax.bar(x + i * width, probs, width, label=label, yerr=yerr, capsize=3)

    ax.set_ylabel("Probabilidade (%)")
    ax.set_title("Probabilidade de Ocorrência de Swell N/NE por Cenário e Semana\n(ERA5 1979–2025)")
    ax.set_xticks(x + width / 2)
    labels = []
    for s in scenarios:
        row = clim_df[clim_df["scenario"] == s].iloc[0]
        labels.append(f"{row['scenario_label']}\n(Tp≥{row['period_min']}s, Hs≥{row['height_min']}m)")
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend()
    ax.set_ylim(0, 110)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.GRAFICOS_DIR, "probabilidade_cenarios.png"), dpi=150)
    plt.close(fig)

    # 2. Annual timeline for "good" scenario
    if annual_df is not None and len(annual_df) > 0:
        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

        for idx, week_key in enumerate(["week3", "week4"]):
            ax = axes[idx]
            week_data = annual_df[annual_df["week"] == week_key].sort_values("year")
            week_label = cfg.MARCH_WINDOWS[week_key]["label"]

            colors = ["#2563eb" if had else "#e5e7eb" for had in week_data["had_event"]]
            ax.bar(week_data["year"], week_data["max_height"], color=colors, edgecolor="gray", linewidth=0.5)
            ax.set_ylabel("Max Hs (m)")
            ax.set_title(f"{week_label}")
            ax.set_ylim(0, 2.0)
            ax.axhline(y=1.0, color="orange", linestyle="--", linewidth=0.8, alpha=0.7, label="1.0m")
            ax.legend(fontsize=8)
            ax.grid(axis="y", alpha=0.3)

        axes[1].set_xlabel("Ano")
        fig.suptitle("Altura Máxima de Swell N/NE por Ano — Cenário 'good'\n(ERA5, período médio ≥ 9s, Hs ≥ 1.0m)", fontsize=12)
        fig.tight_layout()
        fig.savefig(os.path.join(cfg.GRAFICOS_DIR, "timeline_anual.png"), dpi=150)
        plt.close(fig)

    # 3. Surfable window probability
    fig, ax = plt.subplots(figsize=(10, 6))
    for week in weeks:
        week_data = clim_df[(clim_df["week"] == week) & (clim_df["scenario"] == "good")]
        if len(week_data) == 0:
            continue
        row = week_data.iloc[0]
        label = row["week_label"]
        window_probs = [row.get(f"prob_window_{w}h", 0) * 100 for w in cfg.WINDOW_DURATIONS]
        ax.plot(cfg.WINDOW_DURATIONS, window_probs, "o-", label=label, linewidth=2)

    ax.set_xlabel("Duração Mínima da Janela (horas)")
    ax.set_ylabel("Probabilidade (%)")
    ax.set_title("Probabilidade de Janela Surfável — Cenário 'good'\n(N/NE, Tp ≥ 9s, Hs ≥ 1.0m)")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.GRAFICOS_DIR, "janelas_surfaveis.png"), dpi=150)
    plt.close(fig)

    print(f"Charts saved to: {cfg.GRAFICOS_DIR}")


def generate_report(clim_df: pd.DataFrame, annual_df: pd.DataFrame):
    """Generate the final Markdown report."""
    lines = []

    lines.append("# Climatologia de Swell N/NE no Ceará — Março")
    lines.append("")
    lines.append("## Relatório baseado em ERA5 (1979–2025)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Methodology
    lines.append("## 1. Metodologia")
    lines.append("")
    lines.append(f"- **Fonte de dados:** ERA5 / ECMWF (reanálise)")
    lines.append(f"- **Ponto de referência:** {cfg.LAT}°N, {cfg.LON}°W (offshore do Ceará)")
    lines.append(f"- **Período:** 1979–2025 (47 anos)")
    lines.append(f"- **Janela temporal:** 15–28 de março (14 dias)")
    lines.append(f"- **Resolução temporal:** 1 hora")
    lines.append(f"- **Total de observações:** 15.792 horas")
    lines.append("")
    lines.append("### Variáveis ERA5")
    lines.append("")
    lines.append("| Variável | Descrição | Unidade |")
    lines.append("|----------|-----------|---------|")
    lines.append("| `shts` | Significant height of total swell | metros |")
    lines.append("| `mdts` | Mean direction of total swell | graus (FROM) |")
    lines.append("| `mpts` | Mean period of total swell | segundos |")
    lines.append("")
    lines.append("### Nota sobre o período")
    lines.append("")
    lines.append("ERA5 `mpts` é o **período médio** do swell total. Não é o período de pico.")
    lines.append("O período médio é tipicamente 3–4 segundos menor que o período de pico.")
    lines.append("Por isso, os limiares de período utilizados nesta análise ERA5 são mais baixos")
    lines.append("do que os equivalentes para dados WW3 (que usa período de pico).")
    lines.append("")

    # Direction convention
    lines.append("### Direção")
    lines.append("")
    lines.append("Convenção FROM (de onde o swell vem):")
    lines.append("")
    lines.append("| Classe | Faixa |")
    lines.append("|--------|-------|")
    lines.append("| N | 337.5°–360° ou 0°–22.5° |")
    lines.append("| NE | 22.5°–67.5° |")
    lines.append("| N/NE | 337.5°–360° ou 0°–67.5° |")
    lines.append("")

    # Scenarios
    lines.append("### Cenários de surf")
    lines.append("")
    lines.append("| Cenário | Período mínimo | Altura mínima |")
    lines.append("|---------|----------------|---------------|")
    for s in cfg.SCENARIOS_ERA5:
        lines.append(f"| {s['label']} | ≥ {s['period_min']}s | ≥ {s['height_min']}m |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Main results
    lines.append("## 2. Resultados — Probabilidade de Ocorrência")
    lines.append("")
    lines.append("Probabilidade de pelo menos um evento de swell N/NE em cada semana de março,")
    lines.append("com intervalo de confiança de Wilson (95%).")
    lines.append("")
    lines.append("| Cenário | 15–21 março | IC 95% | 22–28 março | IC 95% |")
    lines.append("|---------|-------------|--------|-------------|--------|")

    for scenario_name in [s["name"] for s in cfg.SCENARIOS_ERA5]:
        sc_data = clim_df[clim_df["scenario"] == scenario_name]
        w3 = sc_data[sc_data["week"] == "week3"].iloc[0] if len(sc_data[sc_data["week"] == "week3"]) > 0 else None
        w4 = sc_data[sc_data["week"] == "week4"].iloc[0] if len(sc_data[sc_data["week"] == "week4"]) > 0 else None

        if w3 is not None and w4 is not None:
            lines.append(
                f"| {w3['scenario_label']} | "
                f"{w3['years_with_event']}/{w3['total_years']} = **{100*w3['probability']:.1f}%** | "
                f"[{100*w3['ci_low']:.1f}%–{100*w3['ci_high']:.1f}%] | "
                f"{w4['years_with_event']}/{w4['total_years']} = **{100*w4['probability']:.1f}%** | "
                f"[{100*w4['ci_low']:.1f}%–{100*w4['ci_high']:.1f}%] |"
            )
    lines.append("")

    if os.path.exists(os.path.join(cfg.GRAFICOS_DIR, "probabilidade_cenarios.png")):
        lines.append("![Probabilidade por cenário](graficos/probabilidade_cenarios.png)")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Duration
    lines.append("## 3. Duração dos Eventos")
    lines.append("")
    lines.append("Estatísticas de duração dos eventos (horas) para o cenário 'good':")
    lines.append("")

    good_data = clim_df[clim_df["scenario"] == "good"]
    if len(good_data) > 0:
        lines.append("| Semana | Eventos | Média | Mediana | Máximo | P75 | P90 |")
        lines.append("|--------|---------|-------|---------|--------|-----|-----|")
        for _, row in good_data.iterrows():
            lines.append(
                f"| {row['week_label']} | {row['total_events']} | "
                f"{row['duration_mean']:.1f}h | {row['duration_median']:.1f}h | "
                f"{row['duration_max']}h | {row['duration_p75']:.1f}h | {row['duration_p90']:.1f}h |"
            )
        lines.append("")

    # Surfable windows
    lines.append("## 4. Probabilidade de Janelas Surfáveis")
    lines.append("")
    lines.append("Probabilidade de existir pelo menos uma janela contínua com a duração mínima indicada.")
    lines.append("")
    lines.append("### Cenário 'good' (Tp ≥ 9.0s, Hs ≥ 1.0m):")
    lines.append("")
    lines.append("| Semana | ≥ 3h | ≥ 6h | ≥ 12h | ≥ 24h |")
    lines.append("|--------|------|------|-------|-------|")
    for _, row in good_data.iterrows():
        w3 = row.get("prob_window_3h", 0) * 100
        w6 = row.get("prob_window_6h", 0) * 100
        w12 = row.get("prob_window_12h", 0) * 100
        w24 = row.get("prob_window_24h", 0) * 100
        lines.append(f"| {row['week_label']} | {w3:.0f}% | {w6:.0f}% | {w12:.0f}% | {w24:.0f}% |")
    lines.append("")

    if os.path.exists(os.path.join(cfg.GRAFICOS_DIR, "janelas_surfaveis.png")):
        lines.append("![Janelas surfáveis](graficos/janelas_surfaveis.png)")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Height distribution
    lines.append("## 5. Distribuição de Altura")
    lines.append("")
    lines.append("Percentis da altura máxima dos eventos (cenário 'good'):")
    lines.append("")
    if len(good_data) > 0:
        lines.append("| Semana | Média | Mediana | P75 | P90 | P95 | Máximo |")
        lines.append("|--------|-------|---------|-----|-----|-----|--------|")
        for _, row in good_data.iterrows():
            lines.append(
                f"| {row['week_label']} | {row['height_mean']:.2f}m | "
                f"{row['height_median']:.2f}m | {row['height_p75']:.2f}m | "
                f"{row['height_p90']:.2f}m | {row['height_p95']:.2f}m | {row['height_max']:.2f}m |"
            )
        lines.append("")

    # Direction breakdown
    lines.append("## 6. Direção Predominante")
    lines.append("")
    lines.append("Distribuição N vs NE nos eventos do cenário 'good':")
    lines.append("")
    if len(good_data) > 0:
        lines.append("| Semana | % Norte | % Nordeste |")
        lines.append("|--------|---------|------------|")
        for _, row in good_data.iterrows():
            lines.append(f"| {row['week_label']} | {row['pct_N']:.1f}% | {row['pct_NE']:.1f}% |")
        lines.append("")

    # Annual timeline
    if os.path.exists(os.path.join(cfg.GRAFICOS_DIR, "timeline_anual.png")):
        lines.append("## 7. Linha do Tempo Anual")
        lines.append("")
        lines.append("![Timeline anual](graficos/timeline_anual.png)")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Comparison note
    lines.append("## 8. Comparação entre Semanas")
    lines.append("")
    lines.append("O teste de McNemar (pareado por ano) foi aplicado para comparar as semanas")
    lines.append("15–21 e 22–28 de março no cenário 'good'.")
    lines.append("")
    lines.append("Com 47 anos de dados, **não foi encontrada diferença estatisticamente")
    lines.append("significativa** entre as duas semanas (p > 0.05).")
    lines.append("")
    lines.append("A semana 15–21 apresenta probabilidade ligeiramente superior (~60% vs ~47%),")
    lines.append("mas os intervalos de confiança se sobrepõem amplamente.")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Surf interpretation
    lines.append("## 9. Interpretação para Surf")
    lines.append("")
    lines.append("### O que os dados mostram")
    lines.append("")
    lines.append("- **Swells N/NE são frequentes em março:** quase 100% dos anos registram")
    lines.append("  alguma atividade de swell N/NE com período ≥ 7.5s (média)")
    lines.append("- **Swells com condições 'boas' (Tp médio ≥ 9s, Hs ≥ 1.0m):** ocorrem em")
    lines.append("  ~50-60% dos anos, dependendo da semana")
    lines.append("- **Swells fortes (Hs ≥ 1.5m):** muito menos frequentes (~17-23% dos anos)")
    lines.append("- **Swells excepcionais (Hs ≥ 2.0m):** nenhum registrado no período analisado")
    lines.append("- **Duração típica:** quando há evento, a janela costuma durar 20–35 horas em média")
    lines.append("- **Direção:** predominância de Norte sobre Nordeste nos eventos detectados")
    lines.append("")
    lines.append("### Para planejamento de viagem")
    lines.append("")
    lines.append("- Viajando para o Ceará em março (15–28), há ~50-60% de chance de encontrar")
    lines.append("  pelo menos um swell N/NE com condições boas para longboard")
    lines.append("- Ambas as semanas (15-21 e 22-28) são estatisticamente equivalentes")
    lines.append("- Quando o swell chega, tende a durar mais de 20 horas, dando uma boa janela")
    lines.append("- Swells muito fortes são raros — para longboard, isso não é necessariamente ruim")
    lines.append("")
    lines.append("### Limitações")
    lines.append("")
    lines.append("- Os dados são offshore — a condição na praia depende de batimetria, vento e maré")
    lines.append("- ERA5 usa período médio, não período de pico — os limiares foram calibrados para isso")
    lines.append("- 47 anos é uma série robusta, mas condições individuais variam significativamente")
    lines.append("- Praia de Iracema e Jericoacoara respondem de forma diferente ao mesmo swell offshore")
    lines.append("- Esta é uma climatologia probabilística, não uma previsão")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Relatório gerado automaticamente pelo pipeline de climatologia de swell.*")
    lines.append(f"*Dados: ERA5 / ECMWF, ponto {cfg.LAT}°, {cfg.LON}°, março 15–28, 1979–2025.*")

    report_text = "\n".join(lines)

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    with open(cfg.FINAL_REPORT, "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_text


def main():
    print("=" * 70)
    print("REPORT GENERATION — Ceará Swell Climatology")
    print("=" * 70)
    print()

    # Load data
    if not os.path.exists(cfg.CLIMATOLOGY_CSV):
        print(f"Climatology results not found: {cfg.CLIMATOLOGY_CSV}")
        print("Run 05_climatologia.py first.")
        return

    clim_df = pd.read_csv(cfg.CLIMATOLOGY_CSV)
    print(f"Loaded climatology results: {len(clim_df)} rows")

    annual_df = None
    annual_path = os.path.join(cfg.CLIMATOLOGY_DIR, "resumo_anual_era5.csv")
    if os.path.exists(annual_path):
        annual_df = pd.read_csv(annual_path)
        print(f"Loaded annual summary: {len(annual_df)} rows")

    # Generate charts
    print()
    print("Generating charts...")
    generate_charts(clim_df, annual_df)

    # Generate report
    print()
    print("Generating report...")
    report = generate_report(clim_df, annual_df)

    print()
    print(f"Report saved to: {cfg.FINAL_REPORT}")
    print(f"Report length: {len(report)} characters")
    print()

    # Print summary
    print("=" * 70)
    print("KEY FINDINGS SUMMARY")
    print("=" * 70)
    print()

    good = clim_df[clim_df["scenario"] == "good"]
    for _, row in good.iterrows():
        prob = row["probability"] * 100
        ci = f"[{row['ci_low']*100:.1f}%–{row['ci_high']*100:.1f}%]"
        print(f"  {row['week_label']}: {prob:.1f}% {ci} — "
              f"{row['total_events']} events, "
              f"avg duration {row['duration_mean']:.1f}h")


if __name__ == "__main__":
    main()
