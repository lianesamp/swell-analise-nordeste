# Architecture — Swell Analysis Northeast Brazil

This document maps the 3 analysis fronts, their data pipelines, frontend
components, and the key differences between them.  It exists so that any
future session (or contributor) can pick up context immediately.

---

## Overview

The project is a **React single-page app** (Vite + Tailwind CSS + Recharts)
backed by **Python data pipelines** that process ERA5 reanalysis data from
ECMWF.  There is no backend server — the pipelines produce CSV files that the
frontend loads statically from `public/data/`.

Three independent analysis fronts coexist in the same repo:

| Front | Name | Surf Spot | Data Span | Status |
|-------|------|-----------|-----------|--------|
| 1 | Live Forecast | Praia de Iracema, Fortaleza | 7-day forecast | Complete |
| 2 | March Swell Analysis | Jericoacoara (trip planning) | 1979–2025 (47 yrs), March only | Complete |
| 3 | Historical Patterns | Praia de Iracema, Fortaleza | Oct–May season, 2024–2025+ | In progress |

---

## Front 1 — Live Forecast (Praia de Iracema)

**Goal:** 7-day surf forecast for Iracema, combining offshore swell data with
wave transformation physics and local tide tables.

### Data Sources (fetched live)
- **Open-Meteo Marine API** — 7-day hourly swell forecast (height, period, direction)
- **Marinha do Brasil** — Mucuripe tide predictions (high/low events)
- **GEBCO bathymetry** — cached depth transect for wave transformation

### Surfability Rules (`src/forecast/rules.js`)
Iracema-specific domain knowledge:
- Wave energy threshold: ~400 J/m² (≈ Hs 0.80m after transformation)
- Tide window: surfable between ~0.6m and ~1.5m chart datum
- Direction: N/NE swell required (refraction favorable)
- Daylight only: 05:00–18:30

### Pipeline
No offline pipeline — everything is computed in the browser at runtime.

### Frontend
| Component | What it shows |
|-----------|---------------|
| `ForecastIracema` | Daily forecast cards with surf/flat verdict |
| `SwellTideChart` | Dual-axis time series: swell height + tide height |

### Key Files
```
src/forecast/
  config.js          — API URLs, coordinates, bathymetry cache
  rules.js           — Iracema surfability rules (energy, tide, direction)
  surfCheck.js       — Main forecast logic (fetch → transform → evaluate)
  tides.js           — Tide interpolation from high/low events
  waveTransform.js   — Shoaling + refraction model (dispersion relation)
src/hooks/useForecastData.js — Hook that runs surfCheck and caches result
```

---

## Front 2 — March Swell Analysis (Jericoacoara Trip)

**Goal:** Compare two March weeks (15–21 vs 22–28) across 47 years of data
to find the best window for a surf trip to Jericoacoara.

### Data Source
- **ERA5 reanalysis** (ECMWF) — 1979–2025, March only
- **WW3 hindcast** (NOAA ERDDAP) — 2018–2025, March only (cross-validation)

### Scenario Thresholds (Jericoacoara)

These thresholds were calibrated for **long-period North Atlantic ground swell**
reaching Jericoacoara.  ERA5 uses mean period (mpts), which is ~3–4s lower than
peak period — so the thresholds are lower than you'd see for peak-period data.

| Scenario | Period (ERA5 mean) | Height (Hs) |
|----------|-------------------|-------------|
| Any relevant | ≥ 7.5s | ≥ 0.0m |
| Surfable | ≥ 9.0s | ≥ 0.8m |
| Good | ≥ 9.0s | ≥ 1.0m |
| Strong | ≥ 9.0s | ≥ 1.2m |
| Very good | ≥ 9.0s | ≥ 1.5m |
| Exceptional | ≥ 9.0s | ≥ 2.0m |

### Pipeline (`doc_swell/scripts/`)
7-step pipeline, run via `cli.py`:

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `01_validar_era5.py` | Validate raw NetCDF files |
| 2 | `02_consolidar_era5.py` | Consolidate 47 .nc files → single CSV |
| 3 | `03_baixar_ww3.py` | Download WW3 data from ERDDAP |
| 4 | `04_detectar_eventos.py` | Group qualifying hours into events |
| 5 | `05_climatologia.py` | Probabilities, CIs, percentiles |
| 6 | `06_comparar_era5_ww3.py` | Cross-validate ERA5 vs WW3 |
| 7 | `07_relatorio.py` | Generate markdown report |

Configuration: `config.py` (thresholds, paths, variable mappings)
Validation: `models.py` (Pydantic models for all config values)

### Frontend
| Component | What it shows |
|-----------|---------------|
| `ProbabilidadeCenarios` | Probability comparison: week 3 vs week 4 |
| `GraficoProbabilidade` | Bar chart with Wilson CI error bars |
| `DireccionSwell` | N vs NE direction breakdown |
| `DistribucionEventos` | Height distribution histograms |
| `TimelineAnual` | Year-by-year event timeline |
| `JanelasSurfaveis` | Probability of continuous surf windows (3h, 6h, 12h, 24h) |
| `EventosDetalle` | Paginated table of all detected events |

Data hook: `useCearaData.js` → loads CSVs from `public/data/`

---

## Front 3 — Historical Patterns (Praia de Iracema)

**Goal:** Full swell season analysis for Iracema — which months bring the most
swell, return periods, trends, and what a typical season looks like.

### Data Source
- **ERA5 reanalysis** — swell season (Oct–May), year by year
- Currently: 2024–2025 (2 years).  Downloading backwards toward 2015.

### Scenario Thresholds (Iracema) — CALIBRATION PENDING

The season pipeline currently reuses the **Jericoacoara thresholds** from
Front 2 (Tp ≥ 9s for "surfable").  However, ground-truth testing against
confirmed surf days at Iracema (May 2025: days 1–6) showed that:

- **Period was 6.4–8.0s** on those days (never reached 9.0s)
- **Height was 0.97–1.17m** (above the 0.8m threshold)
- **Direction was NE** (35–66°, correct)
- **Zero hours** matched the current "surfable" threshold

**Root cause:** Iracema also works with shorter-period NE trade wind swell
(6–8s), not just long-period ground swell (9s+).  Additionally, wave energy
(E ∝ Hs² × Tp) may be a better discriminator than period alone for this spot.

**Plan:** Calibrate Iracema-specific thresholds using confirmed surf/no-surf
dates from the user's records:
- May 2025: days 1, 2, 3, 4, 6 (confirmed surf)
- Dec 2025: dates TBD (user has records)
- 2026 season: data not yet downloaded

This calibration will produce **separate scenario definitions** for
Iracema, keeping the Jericoacoara thresholds untouched.

### Pipeline (`doc_swell/scripts/season/`)
3-step pipeline, run via `season/cli.py`:

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `01_consolidar_season.py` | Consolidate year .nc files → single CSV |
| 2 | `02_detectar_eventos_season.py` | Detect swell events (all scenarios) |
| 3 | `03_climatologia_mensal.py` | Monthly climatology + heatmap summary |

Configuration: `season/config.py` (imports shared constants from parent
`config.py` via `importlib.util`, adds season-specific settings)

Download: `00_baixar_era5_historico.py` (1 CDS API request per year,
Oct–May months)

### Frontend
| Component | What it shows |
|-----------|---------------|
| `OverviewCards` | 4 summary stats: peak month, events/season, avg duration, height range |
| `SeasonalityChart` | Bar chart: monthly probability with Wilson CI error bars |
| `MonthlyHeatmap` | Year × month grid colored by intensity |
| `EventosSeason` | Paginated event table with scenario + month filters |

Data hook: `useHistoricalData.js` → loads CSVs from `public/data/historical/`

---

## Key Differences Between Fronts

### Jericoacoara vs Iracema

| Aspect | Jericoacoara (Front 2) | Iracema (Fronts 1 & 3) |
|--------|----------------------|----------------------|
| Swell type | Long-period N Atlantic ground swell | Ground swell + NE trade wind swell |
| Min period | ≥ 9.0s (ERA5 mean) | TBD — likely ≥ 6.5–7.0s |
| Energy matters? | Less critical (open beach break) | Critical (needs ~400 J/m² to break on sandbars) |
| Tide dependency | Low | High (surfable only 0.6–1.5m chart datum) |
| Bathymetry | Open, exposed | Sheltered, shallow sandbars |
| Calibration method | Literature + ERA5 vs WW3 comparison | Ground truth from confirmed surf sessions |

### Pipeline Differences

| Aspect | March pipeline | Season pipeline |
|--------|----------------|-----------------|
| Time window | 2 weeks (Mar 15–28) | 8 months (Oct–May) |
| Year range | 1979–2025 (47 years) | 2024–2025 (growing) |
| Granularity | Week comparison | Month-by-month climatology |
| Steps | 7 (includes WW3 cross-validation) | 3 (ERA5 only for now) |
| Config | `scripts/config.py` | `scripts/season/config.py` |
| CLI | `scripts/cli.py` | `scripts/season/cli.py` |

---

## Directory Structure

```
swell-analise-nordeste/
├── public/
│   └── data/
│       ├── *.csv                      # Front 2 output (March analysis)
│       └── historical/
│           ├── monthly_climatology.csv # Front 3 — monthly probabilities
│           ├── monthly_summary.csv     # Front 3 — year×month heatmap
│           └── eventos_season.csv      # Front 3 — individual events
├── src/
│   ├── App.jsx                        # Main layout (3 sections)
│   ├── components/
│   │   ├── BannerCeara.jsx            # Hub landing
│   │   ├── Navbar.jsx                 # Navigation
│   │   ├── ForecastIracema.jsx        # Front 1
│   │   ├── SwellTideChart.jsx         # Front 1
│   │   ├── ProbabilidadeCenarios.jsx  # Front 2
│   │   ├── GraficoProbabilidade.jsx   # Front 2
│   │   ├── DireccionSwell.jsx         # Front 2
│   │   ├── DistribucionEventos.jsx    # Front 2
│   │   ├── TimelineAnual.jsx          # Front 2
│   │   ├── JanelasSurfaveis.jsx       # Front 2
│   │   ├── EventosDetalle.jsx         # Front 2
│   │   ├── OverviewCards.jsx          # Front 3
│   │   ├── SeasonalityChart.jsx       # Front 3
│   │   ├── MonthlyHeatmap.jsx         # Front 3
│   │   └── EventosSeason.jsx          # Front 3
│   ├── forecast/                      # Front 1 — wave transform + rules
│   │   ├── config.js
│   │   ├── rules.js
│   │   ├── surfCheck.js
│   │   ├── tides.js
│   │   └── waveTransform.js
│   └── hooks/
│       ├── useCearaData.js            # Front 2 data
│       ├── useForecastData.js         # Front 1 data
│       └── useHistoricalData.js       # Front 3 data
└── doc_swell/
    ├── ERA5_CEARA_MARCO/              # Raw .nc files (March, 47 years)
    ├── data/
    │   ├── raw/
    │   │   ├── noaa/                  # WW3 raw data
    │   │   └── era5_historico/        # Season .nc files (year by year)
    │   ├── processed/                 # Consolidated CSVs
    │   └── climatology/              # Analysis output CSVs
    ├── output/                        # Reports, charts
    └── scripts/
        ├── config.py                  # March pipeline config (shared base)
        ├── models.py                  # Pydantic validation models
        ├── cli.py                     # March pipeline CLI (7 steps)
        ├── 01–07_*.py                 # March pipeline steps
        └── season/
            ├── config.py              # Season config (extends parent)
            ├── cli.py                 # Season pipeline CLI (3 steps)
            └── 01–03_*.py             # Season pipeline steps
```

---

## Pending / Next Steps

1. **Download 2026 ERA5 season data** — user is downloading year by year
2. **Calibrate Iracema-specific thresholds** — using confirmed surf dates
   (May 2025, Dec 2025, 2026 season) to find the optimal Hs, Tp, and energy
   thresholds.  Will likely add a new scenario set separate from Jeri's.
3. **Add energy (joules) as a detection criterion** — Iracema depends heavily
   on wave energy (E ∝ Hs² × Tp), not just height and period independently.
4. **Expand season year range** — download 2015–2023 to build a robust
   climatology (Wilson CIs will narrow with more years).
5. **Collect negative examples** — days when the user checked but there was
   no surf.  These are as important as positive examples for threshold
   calibration.
