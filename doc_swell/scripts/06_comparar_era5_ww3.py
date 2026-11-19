"""
06_comparar_era5_ww3.py — Compare ERA5 and WW3 for the overlap period (2018-2025).

Requires both ERA5 and WW3 CSVs to be available.
If WW3 data is not yet downloaded, this script exits gracefully.

Computes:
  - Correlation between height, period, direction
  - Bias and RMSE
  - Event-level comparison
  - Charts (scatter plots, time series)

Output:
  - output/comparacao_era5_ww3.md
  - output/graficos/comparacao_*.png
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


def circular_mean(angles_deg: np.ndarray) -> float:
    """Compute circular mean of angles in degrees."""
    rad = np.deg2rad(angles_deg)
    mean_sin = np.mean(np.sin(rad))
    mean_cos = np.mean(np.cos(rad))
    return np.rad2deg(np.arctan2(mean_sin, mean_cos)) % 360


def circular_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute circular difference between two arrays of angles (degrees)."""
    diff = a - b
    diff = (diff + 180) % 360 - 180
    return diff


def compare_variables(era5: pd.DataFrame, ww3: pd.DataFrame) -> dict:
    """Compare matched hourly observations."""
    # Merge on time
    merged = pd.merge(era5, ww3, on="time", suffixes=("_era5", "_ww3"))

    if len(merged) == 0:
        return {"error": "No matching timestamps"}

    results = {"n_matched": len(merged)}

    for var in ["swell_height", "swell_period"]:
        e = merged[f"{var}_era5"].values
        w = merged[f"{var}_ww3"].values

        mask = ~(np.isnan(e) | np.isnan(w))
        e, w = e[mask], w[mask]

        if len(e) < 2:
            continue

        corr = np.corrcoef(e, w)[0, 1]
        bias = np.mean(e - w)
        rmse = np.sqrt(np.mean((e - w) ** 2))
        mae = np.mean(np.abs(e - w))

        results[f"{var}_corr"] = round(corr, 4)
        results[f"{var}_bias"] = round(bias, 4)
        results[f"{var}_rmse"] = round(rmse, 4)
        results[f"{var}_mae"] = round(mae, 4)
        results[f"{var}_era5_mean"] = round(np.mean(e), 4)
        results[f"{var}_ww3_mean"] = round(np.mean(w), 4)

    # Direction comparison (circular)
    e_dir = merged["swell_direction_era5"].values
    w_dir = merged["swell_direction_ww3"].values
    mask = ~(np.isnan(e_dir) | np.isnan(w_dir))
    e_dir, w_dir = e_dir[mask], w_dir[mask]

    if len(e_dir) > 0:
        circ_diffs = circular_diff(e_dir, w_dir)
        results["direction_mean_diff"] = round(np.mean(circ_diffs), 2)
        results["direction_mae"] = round(np.mean(np.abs(circ_diffs)), 2)
        results["direction_era5_circ_mean"] = round(circular_mean(e_dir), 2)
        results["direction_ww3_circ_mean"] = round(circular_mean(w_dir), 2)

    return results


def plot_scatter(merged: pd.DataFrame, var: str, label_era5: str, label_ww3: str, output_path: str):
    """Create scatter plot comparing ERA5 and WW3."""
    if not HAS_MATPLOTLIB:
        return

    e = merged[f"{var}_era5"].values
    w = merged[f"{var}_ww3"].values

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.scatter(w, e, alpha=0.3, s=10)
    lims = [min(e.min(), w.min()), max(e.max(), w.max())]
    ax.plot(lims, lims, "r--", linewidth=1, label="1:1 line")
    ax.set_xlabel(f"WW3 {label_ww3}")
    ax.set_ylabel(f"ERA5 {label_era5}")
    ax.set_title(f"ERA5 vs WW3 — {label_era5}")
    ax.legend()
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def generate_report(results: dict, output_path: str):
    """Generate comparison report in Markdown."""
    lines = [
        "# Comparação ERA5 × WW3 — Período de Sobreposição",
        "",
        "## Período: 2018–2025, Março 15–28",
        f"## Ponto: {cfg.LAT}°, {cfg.LON}°",
        "",
        "### Nota Metodológica Importante",
        "",
        "ERA5 utiliza **período médio do swell total** (`mpts`), enquanto WW3 utiliza",
        "**período de pico do swell** (`sper`). São variáveis fisicamente diferentes.",
        "O período de pico é tipicamente 3–4 segundos maior que o período médio.",
        "",
        "Portanto, **não se espera concordância perfeita nos valores absolutos de período**.",
        "A comparação foca em correlação e consistência relativa.",
        "",
    ]

    if "error" in results:
        lines.append(f"**Erro:** {results['error']}")
    else:
        lines.append(f"### Observações Pareadas: {results['n_matched']}")
        lines.append("")
        lines.append("### Altura (shts vs shgt)")
        lines.append("")
        for key in ["swell_height_corr", "swell_height_bias", "swell_height_rmse",
                     "swell_height_mae", "swell_height_era5_mean", "swell_height_ww3_mean"]:
            if key in results:
                label = key.replace("swell_height_", "").upper()
                lines.append(f"- {label}: {results[key]}")
        lines.append("")
        lines.append("### Período (mpts vs sper)")
        lines.append("")
        for key in ["swell_period_corr", "swell_period_bias", "swell_period_rmse",
                     "swell_period_mae", "swell_period_era5_mean", "swell_period_ww3_mean"]:
            if key in results:
                label = key.replace("swell_period_", "").upper()
                lines.append(f"- {label}: {results[key]}")
        lines.append("")
        lines.append("### Direção (mdts vs sdir)")
        lines.append("")
        for key in ["direction_mean_diff", "direction_mae",
                     "direction_era5_circ_mean", "direction_ww3_circ_mean"]:
            if key in results:
                label = key.replace("direction_", "").upper()
                lines.append(f"- {label}: {results[key]}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    print("=" * 70)
    print("ERA5 × WW3 COMPARISON")
    print("=" * 70)
    print()

    if not os.path.exists(cfg.ERA5_CSV):
        print(f"ERA5 CSV not found: {cfg.ERA5_CSV}")
        return

    if not os.path.exists(cfg.WW3_CSV):
        print(f"WW3 CSV not found: {cfg.WW3_CSV}")
        print("Run 03_baixar_ww3.py first (requires internet and ERDDAP access).")
        print()
        print("This script requires both datasets. Skipping comparison.")
        return

    era5 = pd.read_csv(cfg.ERA5_CSV, parse_dates=["time"])
    ww3 = pd.read_csv(cfg.WW3_CSV, parse_dates=["time"])

    # Filter ERA5 to overlap period
    overlap_years = sorted(set(era5["year"].unique()) & set(ww3["year"].unique()))
    print(f"Overlap years: {overlap_years}")

    era5_overlap = era5[era5["year"].isin(overlap_years)]
    ww3_overlap = ww3[ww3["year"].isin(overlap_years)]

    print(f"ERA5 rows in overlap: {len(era5_overlap)}")
    print(f"WW3 rows in overlap: {len(ww3_overlap)}")
    print()

    # Compare
    results = compare_variables(era5_overlap, ww3_overlap)

    if "error" in results:
        print(f"Error: {results['error']}")
        return

    print(f"Matched timestamps: {results['n_matched']}")
    print()

    for var_label, var_name in [("Height", "swell_height"), ("Period", "swell_period")]:
        print(f"{var_label}:")
        for metric in ["corr", "bias", "rmse", "mae", "era5_mean", "ww3_mean"]:
            key = f"{var_name}_{metric}"
            if key in results:
                print(f"  {metric}: {results[key]}")
        print()

    print("Direction:")
    for key in ["direction_mean_diff", "direction_mae", "direction_era5_circ_mean", "direction_ww3_circ_mean"]:
        if key in results:
            print(f"  {key}: {results[key]}")
    print()

    # Generate charts
    os.makedirs(cfg.GRAFICOS_DIR, exist_ok=True)
    merged = pd.merge(era5_overlap, ww3_overlap, on="time", suffixes=("_era5", "_ww3"))

    if HAS_MATPLOTLIB and len(merged) > 0:
        plot_scatter(merged, "swell_height", "Hs (m)", "Hs (m)",
                     os.path.join(cfg.GRAFICOS_DIR, "comparacao_altura.png"))
        plot_scatter(merged, "swell_period", "Tp mean (s)", "Tp peak (s)",
                     os.path.join(cfg.GRAFICOS_DIR, "comparacao_periodo.png"))
        print("Charts saved to output/graficos/")

    # Generate report
    generate_report(results, cfg.COMPARISON_REPORT)
    print(f"Report saved to: {cfg.COMPARISON_REPORT}")


if __name__ == "__main__":
    main()
