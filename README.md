# Swell Análise Nordeste

Real-time surf forecast and 47-year climate analysis for Northeast Brazil's coastline, focused on Praia de Iracema (Fortaleza, Ceará).

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)
![Pydantic](https://img.shields.io/badge/Pydantic-2-E92063)

<!-- TODO: Replace with an actual screenshot of your dashboard -->
<!-- ![Dashboard screenshot](docs/screenshot.png) -->

---

## Features

- **7-day surf forecast** — fetches live swell data from the Open-Meteo Marine API and classifies conditions (flat, fair, good, great, epic) using energy-based thresholds
- **Wave transformation physics** — applies shoaling, refraction (Snell's law), and depth-limited breaking (McCowan's criterion) along a real GEBCO bathymetry transect
- **Tide integration** — overlays Brazilian Navy (Marinha do Brasil) tide predictions with phase detection (draining, low, filling, high)
- **47-year climate analysis** — processes ERA5 reanalysis data (1979–2025) to calculate swell event probabilities per week, with Wilson Score 95% confidence intervals
- **Interactive charts** — probability distributions, annual timelines, swell direction breakdowns, surfable window analysis, and sortable event history
- **Dual implementation** — the same forecast pipeline runs in both JavaScript (browser) and Python (CLI), sharing identical physics and rules
- **Python CLI** — terminal-based forecast with Rich-formatted tables (`python cli.py check`)

---

## Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI components and state management |
| **Vite 6** | Build tool and dev server |
| **Tailwind CSS 4** | Utility-first styling |
| **Recharts** | Line charts, bar charts, dual-axis charts, error bars |
| **PapaParse** | CSV parsing in the browser for historical datasets |

### Backend / Data Pipeline
| Technology | Purpose |
|---|---|
| **Python 3.12+** | Data processing and CLI |
| **Pydantic 2** | Data validation with type-safe models |
| **NumPy** | Numerical computation (wave physics, circular statistics) |
| **Pandas** | Historical data processing and aggregation |
| **Xarray + NetCDF4** | ERA5 climate reanalysis data handling |
| **SciPy** | Scientific computing |
| **Typer + Rich** | CLI framework with styled terminal output |

### External APIs & Data Sources
| Source | Data |
|---|---|
| **Open-Meteo Marine API** | Real-time 7-day wave forecast (height, period, direction) |
| **ERA5 / Copernicus CDS** | 47-year historical reanalysis (1979–2025) |
| **Marinha do Brasil** | Tide predictions for Porto de Mucuripe |
| **GEBCO** | Seafloor bathymetry for the offshore-to-shore transect |

---

## Architecture

```
Open-Meteo API ──► fetch_swell ──► wave_transform ──► rules ──► surf_check ──► UI
                                        │                          │
                 bathymetry.json ───────┘    tide_mucuripe.json ──┘

ERA5 (47 years) ──► Python pipeline ──► CSV exports ──► React (PapaParse) ──► Recharts
```

The forecast engine runs a physics-based pipeline:
1. **Fetch** — hourly swell data (height, period, direction) from the API
2. **Transform** — solve the dispersion relation (Newton-Raphson), apply shoaling and refraction along the bathymetry transect
3. **Classify** — calculate wave energy (E = ρgH²/16), apply tide modifiers, rate each hour
4. **Group** — merge consecutive surfable hours into windows with an overall rating

---

## How to Run

### Prerequisites
- Node.js 18+
- Python 3.12+

### Frontend (React dashboard)

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Production build
npm run build
```

### Python CLI (forecast in the terminal)

```bash
# Install dependencies
pip install -r doc_swell/requirements.txt

# 7-day surf forecast
python forecast/cli.py check

# Raw swell data table
python forecast/cli.py swell

# Tide table for the week
python forecast/cli.py tides
```

---

## Project Structure

```
src/
  components/       # 11 React components (forecast, charts, tables)
  forecast/         # JS forecast engine (config, rules, surfCheck, waveTransform, tides)
  hooks/            # useCearaData (CSV loader), useForecastData (live forecast)
  App.jsx           # Main layout

forecast/           # Python forecast engine (mirrors the JS version)
  cli.py            # Typer CLI with 3 commands
  models.py         # Pydantic validated data classes
  config.py         # Spot definition and energy thresholds
  surf_check.py     # Main orchestration
  rules.py          # Surfability rules (pure functions)
  wave_transform.py # Shoaling + refraction physics
  fetch_swell.py    # Open-Meteo API client
  tide_mucuripe.py  # Tide interpolation and phase detection

public/data/        # Static CSV/JSON files (climatologia, eventos, tides, bathymetry)
```

---

## What I Learned

- **Physical oceanography** — dispersion relation, shoaling/refraction coefficients, wave energy flux conservation, McCowan's breaking criterion
- **Climate data engineering** — working with ERA5 reanalysis via CDS API, NetCDF format, Xarray for multidimensional arrays
- **Statistical methods** — Wilson Score confidence intervals, circular statistics for directional data, Spearman correlation for trend analysis, pseudo-replication awareness
- **React patterns** — custom hooks with module-level caching, hook composition, controlled components, responsive chart configuration
- **Data validation** — Pydantic models with field/model validators (Python equivalent of Zod)
- **Dual-language architecture** — maintaining the same physics engine in both JavaScript and Python, understanding the tradeoffs
- **API integration** — working with Open-Meteo (free, CORS-enabled), understanding rate limits, caching strategies

---

## License

This project is for personal and educational use.
