# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Jupyter Notebook-based data reports on F1 telemetry, focused on **race strategy** (pit stop windows, undercut/overcut analysis) and **tyre performance** (degradation, compound comparisons, stint lengths).

## Environment

- Python 3.14, managed via a `.venv` virtual environment at the project root.
- Activate before running anything: `.venv\Scripts\activate` (PowerShell) or `.venv/Scripts/activate` (bash).

## Common Commands

```powershell
# Install dependencies
pip install -r requirements.txt

# Launch Jupyter
jupyter lab

# Run a notebook non-interactively (re-execute all cells)
jupyter nbconvert --to notebook --execute notebooks/your_notebook.ipynb

# Run tests
python -m pytest

# Run a single test
python -m pytest tests/test_foo.py::test_bar
```

## Key Libraries

| Library | Role |
|---|---|
| `fastf1` | Primary data source — lap telemetry, tyre/pit data via the official F1 timing API |
| `pandas` | All tabular data manipulation — FastF1 returns DataFrames |
| `matplotlib` / `seaborn` | Static plots exported as 300 DPI images for the report |
| `numpy` | Numerical operations |
| `playwright` | Renders the HTML report to print-ready PDF via headless Chromium |

## Data Sources

See `planning/f1_data_overview.md` for full research. Summary:

**FastF1** is the only free source with per-lap tyre compound, `TyreLife`, `FreshTyre`, and `Stint` columns. It covers 2018–present. Always enable caching — a single session download can be 200–500 MB.

**OpenF1** (`openf1.org`) is the best complement for tyre work: a REST API with a dedicated `/stints` endpoint (compound, stint number, tyre age at start) and `/pit` endpoint. Covers 2023+, free, no auth. Has documented data-quality quirks (stint boundary overlaps, some mislabeled compounds in 2024) — cross-validate against FastF1 when accuracy matters.

**Jolpica-F1 / Kaggle (Ergast-derived)** cover pit-stop timing and lap times back to 1950 but have **no tyre compound data**. Useful only for historical results/pit-stop trends. Ergast itself shut down after 2024; use `api.jolpi.ca` as a drop-in replacement.

Key caveats:
- FastF1 `Compound` gives relative labels only (SOFT/MEDIUM/HARD), not absolute Pirelli C1–C5 compounds.
- No free source has compound data before 2018.
- Raw lap times improve through a stint as fuel burns off — fuel-correct before interpreting degradation slopes.

## FastF1 Data Model

FastF1 organises data by **Session** (a race weekend event + session type):

```python
import fastf1
fastf1.Cache.enable_cache('cache/')  # always enable to avoid re-fetching

session = fastf1.get_session(2024, 'Monza', 'R')  # year, event, session type
session.load()  # fetches laps, telemetry, weather, tyre data

laps = session.laps                  # DataFrame — one row per lap per driver
car_data = session.car_data['VER']   # high-freq telemetry (speed, throttle, brake, gear, DRS)
pos_data = session.pos_data['VER']   # GPS position data
```

Key columns for strategy/tyre work:

- `laps`: `Driver`, `LapTime`, `Stint`, `TyreLife`, `Compound`, `FreshTyre`, `PitInTime`, `PitOutTime`
- Filter to representative laps: `laps.pick_quicklaps()` (drops in/out laps and laps above 107% threshold)
- Use `fastf1.plotting.get_compound_color(compound, session=session)` for official Pirelli compound colours

## Report Pipeline

The final deliverable is a **print-ready PDF** (a 10-page interview handout — see `planning/interview_presentation_plan.md`). Reports are produced in three separated stages:

1. **Analysis** happens in `notebooks/` — load FastF1 data, compute strategy/tyre metrics, build charts.
2. **Charts** are exported as 300 DPI PNG/SVG into `report_draft/assets/` using the light matplotlib style in `src/theme.py`. These images are the handoff artifact between analysis and presentation — regenerate them as the analysis evolves.
3. **Presentation** is hand-built HTML + CSS in `report_draft/`, not notebook export. `styles/theme.css` holds the palette/typography template; `styles/print.css` controls page size, margins, and page breaks (`@page`, `page-break-*`). `build.py` renders HTML → PDF via headless Chromium (Playwright).

The report is being built page-by-page against **dummy data** (FastF1-schema DataFrames from `src/dummy_data.py`) to lock layout and feel before wiring in real data. Design language is **"pit-wall / engineering"** (locked): light/print-friendly, condensed display type (Chakra Petch), monospace data readouts (IBM Plex Mono), and tyre-compound colour coding — signals trackside-engineering domain fluency. Compound colours are FastF1-official and centralised in both `theme.css` and `src/theme.py`. Reusable components (`.statusbar`, `.readout`, `.tyre-strip`, `.chart-card`, `.footer`) live in `theme.css`.

Why HTML over notebook PDF export: `nbconvert` gives poor layout/page-break control. HTML+CSS gives full control over the printed page. Why Chromium over WeasyPrint: WeasyPrint needs native GTK/Pango libraries that are painful to install on Windows; Chromium bundles its own renderer and has stronger CSS print support.

## Architecture

```
F1_REPORT/
├── notebooks/       # one notebook per analysis topic — the data work
├── src/             # reusable helpers imported by notebooks
│   ├── theme.py     # light matplotlib style + compound/team colour constants
│   ├── dummy_data.py# FastF1-schema dummy data generators (draft phase)
│   └── charts.py    # chart functions (DataFrame → 300 DPI image)
├── report_draft/    # the draft report (dummy data) being built page-by-page
│   ├── assets/      # exported 300 DPI charts (the analysis → report handoff)
│   ├── report.html  # the 10-page layout
│   ├── styles/
│   │   ├── theme.css# palette, typography, reusable layout components
│   │   └── print.css# @page size/margins, page breaks
│   └── build.py     # Playwright: html + css → report.pdf
├── planning/        # research notes and project planning docs
├── knowledge_base/  # F1 domain reference material
├── cache/           # FastF1 local cache — never commit this
├── data/            # exported CSVs or processed datasets
└── requirements.txt
```

Notebooks import shared logic from `src/` to avoid duplication across reports. The `cache/` directory is in `.gitignore`.
