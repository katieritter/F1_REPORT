# Season-Wide F1 Strategy & Tyre Report — Concept & Plan

## Overview

A companion to the single-race deep-dive (`interview_presentation_plan.md`): a
**season review seen through the strategy & tyre lens**, covering every team
across every round of a full season.

The differentiator is the lens. A generic championship recap — standings, race
winners, who-beat-who — is what everyone makes. The edge here is analysing the
*whole season as a tyre-management and strategy story*: who is kindest to their
tyres, who is aggressive on strategy, which circuits punish degradation, and
which teams execute in the pit lane.

This report reuses the existing **pit-wall design system** and **HTML → PDF
pipeline**. What changes is the **data scope** (all rounds, not one session) and
the **chart types** — aggregation, rankings, heatmaps and quadrants rather than
single-race time series.

---

## Key architectural difference: a season data pipeline (ETL)

The one-race report loads a single session. A season needs roughly
24 rounds × 20 drivers × 60 laps, which forces a different data approach:

- **Fetch all rounds once** via FastF1. Caching is essential — each session can
  be hundreds of MB, so a full season is a large, one-time download.
- **Build tidy aggregate tables** (per-lap, per-stint, per-pit-stop) and cache
  them as parquet in `data/`. Charts read these pre-built tables, not live
  FastF1. A new module (e.g. `src/season_etl.py`) handles this; it reuses
  `src/analysis.py` for quicklap filtering, fuel correction and degradation
  fits.
- **Cross-race normalisation is the hard part.** Lap times differ per circuit,
  so absolute seconds can't be compared across races — use *relative* pace
  (gap to each race's median) instead. Compounds are also *relative per
  weekend* (a "soft" is a different Pirelli C-compound from race to race), so
  cross-race compound comparisons need care, or a mapping to C-numbers via the
  published per-race allocation.

---

## Proposed sections & pages (~14–16 landscape pages)

### A · Season Overview (2 pp)

- **Title page** + a **season-at-a-glance readout**: rounds, total pit stops,
  safety-car / VSC count, wet races, compounds used.
- *(Optional orientation)* Constructor **points progression by round** — a line
  or bump chart. Kept light; it's context, not the focus.

### B · Tyre Performance — the core (4–5 pp)

- **Compound usage by team** — stacked bars of laps-per-compound share. Who runs
  aggressive (soft-heavy) vs conservative.
- **Tyre-degradation ranking by team** — season-aggregated fuel-corrected
  degradation rate; a bar ranking of the best tyre management.
- **Degradation by circuit (track classification)** — a heatmap of
  circuits × compound degradation severity, ranking tracks from high to low
  stress. (This is the "circuit classification" idea flagged as a next step in
  the one-race report.)
- **Stint-length trends** — average stint length per compound across the season.
- **Driver tyre management** — degradation controlling for the car; a ranking of
  the gentlest drivers on their tyres.

### C · Strategy Patterns (3–4 pp)

- **Stops-per-race distribution** — stacked bar per round showing the 1-/2-/3-stop
  split. How strategy varies by circuit.
- **Strategy-aggression quadrant** — scatter per team (average stops & soft usage
  vs divergence from the field): an aggressive ↔ conservative map.
- **Undercut / overcut success by circuit** — where the undercut actually worked,
  tying pit-loss and degradation together (bar or heatmap).
- **Safety car / VSC impact** — per-race SC/VSC count and how it reshuffled
  strategy; a season timeline.

### D · Operations (2 pp)

- **Pit-stop performance ranking** — median stationary time per team, with the
  distribution (box / violin). Pure operational excellence.
- **Pit-loss by circuit** — reference bar (e.g. Imola long, COTA short): the
  context that decides whether an undercut is even viable at a track.

### E · Synthesis (2–3 pp)

- **Season strategy scorecard / "awards"** — best strategy team, best tyre
  management, best pit crew, most aggressive — a summary panel.
- **Key takeaways** — a short narrative pulling the threads together.
- **Methodology & caveats** — FastF1 across all rounds, aggregation approach,
  fuel correction, the relative-compound caveat, cross-race normalisation, and
  known data-quality notes.

---

## New chart types to build (vs the one-race report)

| Chart | Used for |
|---|---|
| **Heatmap** | circuit × compound degradation (track classification) |
| **Ranking bar charts** | team degradation, pit times, driver degradation |
| **Quadrant scatter** | strategy aggression; quali-vs-race tyre limitation |
| **Bump / line** | standings or points by round |
| **Stacked bars** | compound usage, stop counts (extends existing stint grouping) |
| **Distribution / box** | pit times, stint lengths (reuses the `compound_pace_box` pattern) |
| **Small multiples** | mini strategy Gantts, one per circuit (facets `strategy_gantt`) |

---

## Reuse from the current (one-race) project

- **Pit-wall design system:** `report_draft/styles/theme.css`, `print.css` — unchanged.
- **Pipeline:** the Playwright `build.py` + `render_assets.py` pattern.
- **Modules:** `src/theme.py` (colours/fonts), `src/analysis.py` (fuel
  correction, quicklaps, degradation, gaps), `src/fonts.py`.
- **Dummy-data-first approach:** a multi-race synthetic generator (extending
  `src/dummy_data.py`) lets us lock the layout before the heavy real ETL.

---

## Suggested build sequence

1. Extend the dummy data to a synthetic **multi-race season** (for layout).
2. Build the new chart functions against the dummy season tables.
3. Lay out the pages (reusing the styles), render to PDF, iterate page-by-page.
4. Build `src/season_etl.py` to fetch real rounds → parquet, then swap
   dummy → real — a one-module swap, exactly as designed for the one-race report.

---

## Open decisions (to resolve before building)

- **Scope:** strict tyre/strategy lens (recommended — it's the differentiator)
  vs a broader season review.
- **Which season:** e.g. 2024 (complete; FastF1 tyre data exists 2018+).
- **Length:** target ~14–16 pages, landscape.
