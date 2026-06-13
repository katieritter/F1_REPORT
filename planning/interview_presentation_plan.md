# F1 Interview Presentation — 10-Page Printed Handout Plan

## Overview

A single, cohesive printed document (10 pages max) to bring into the interview. It tells one story — a deep analysis of one well-chosen race — viewed through three lenses: strategy architecture, tyre degradation, and a tactical case study, plus a Cadillac-specific spotlight. Every page earns its place.

## Race Selection Criteria

Pick ONE race that has all of the following:
- Mixed strategies across the field (some one-stoppers, some two-stoppers)
- At least one clear undercut or overcut battle between two drivers
- Ideally a safety car, VSC, or weather event that forced reactive decisions
- All three dry compounds used (Soft, Medium, Hard)

**Strong candidates:** 2024 Hungarian GP, 2024 British GP (Silverstone), 2024 Spanish GP, or a 2025 race with strategic variety. Load 2–3 candidates in FastF1 and check stint diversity before committing.

---

## Page-by-Page Layout

### Page 1 — Title Page

- Your name and contact details
- Title: "Race Strategy & Tyre Performance Analysis"
- Subtitle: the specific race (e.g., "2024 Hungarian Grand Prix — Hungaroring")
- One headline finding in large text (e.g., "A two-stop strategy was 4.2 seconds faster than one-stop, but only 6 drivers chose it")
- FastF1 / Python / pandas / matplotlib listed subtly at the bottom as the toolchain
- Clean, minimal design — no clutter

### Pages 2–3 — Strategy Gantt Chart (The Hero Visual)

**Page 2: Full-page chart.**

Horizontal stacked bars, one row per driver (sorted by finishing position), each segment coloured by compound (Soft/Medium/Hard using official FastF1 colours). Width of each segment equals stint length in laps. Pit stops appear as the boundaries between segments.

This is the single most recognisable chart in F1 strategy analysis. It must be polished, legible, and beautiful.

**Page 3: Annotation page (facing the chart).**

Three to four concise bullet points calling out the key strategic stories visible in the Gantt:
- Which strategy won the race and why
- Where the field split between one-stop and two-stop (or other variations)
- Any drivers who ran an unusual or outlier strategy and how it played out
- Safety car or VSC impact on pit-stop clustering (if applicable)

Each bullet should be 2–3 sentences max. The tone is analyst briefing, not essay.

### Pages 4–5 — Tyre Degradation Analysis

**Page 4: Degradation curves chart.**

Two panels side by side:
- **Left panel — Raw lap times vs tyre life**, one line per compound (Soft, Medium, Hard), using quick-laps only (pit laps and outliers filtered out). This shows the "naive" view where lap times often decrease early in a stint due to fuel burn-off.
- **Right panel — Fuel-corrected lap times vs tyre life.** Same data but with the fuel-weight effect removed (approximately +0.033 s/lap added back per lap to isolate tyre-only degradation). The corrected curves should show a clearer upward slope.

Showing both side by side is the key — it demonstrates you understand that raw lap times are confounded by fuel load, and that correcting for it reveals the true degradation picture.

**Page 5: Degradation summary and compound comparison.**

A small table reporting:

| Compound | Deg Rate (s/lap) | Pace Advantage vs Hard (s) | Estimated Cliff Lap |
|----------|-------------------|----------------------------|---------------------|
| Soft     | +0.08             | -0.9                       | ~18 laps            |
| Medium   | +0.05             | -0.4                       | ~28 laps            |
| Hard     | +0.03             | baseline                   | none detected       |

*(Values are illustrative — fill from actual data.)*

Below the table, a compact violin or box plot showing lap-time distributions per compound. A short paragraph (3–4 sentences) interpreting what the numbers mean strategically: "The soft compound offered a 0.9-second pace advantage over the hard but degraded at nearly three times the rate, making it viable only for stints under 18 laps before the performance cliff. This explains why the majority of two-stop strategies used the soft for a short opening stint before switching to the medium."

### Pages 6–7 — Undercut / Overcut Case Study

**Page 6: Gap chart.**

Pick the most interesting driver battle from the race — two drivers fighting for position across a pit window. Plot the gap between them (in seconds) on the y-axis, lap number on the x-axis. Annotate with vertical lines and labels for each driver's pit-in and pit-out laps.

The chart should clearly show:
- The gap trend before the pit window (e.g., Driver A closing on Driver B)
- The moment the undercut/overcut is attempted
- Whether the position changed and by how much

Colour the two drivers using their official team colours.

**Page 7: Tactical narrative.**

A half-page written analysis (150–200 words max) explaining:
- What each driver's strategy team was trying to achieve
- Why the undercut worked (or didn't) at this specific circuit — relating back to the degradation data from pages 4–5
- The pit-loss time at this circuit and how it factors in
- What the alternative decision would have been and its likely outcome

This page proves you can connect data to narrative — the core communication skill of a strategy engineer.

### Pages 8–9 — Cadillac Team Spotlight

**Page 8: Cadillac strategy overview.**

If 2026 FastF1 data is available, show a mini strategy Gantt for Pérez and Bottas at their best 2026 race, with the field median strategy shown as a grey reference bar above. Annotate whether Cadillac mirrored the field consensus or diverged.

If 2026 data is not yet available in FastF1, use a 2024/2025 backmarker team (e.g., Sauber or Haas) as a structural proxy and include a note: "Methodology validated on [team]; ready to apply to Cadillac 2026 data as it becomes available."

Include a brief stint-pace comparison between the two Cadillac drivers (or proxy drivers): who managed tyres better, who was faster on fresh rubber, who maintained pace deeper into stints.

**Page 9: Cadillac context and trajectory.**

A short written section (half page) covering:
- Cadillac's 2026 season context: new 11th team, Pérez and Bottas, Ferrari PU customer, best results so far
- How their tyre strategy choices compare to the field — are they conservative, aggressive, or reactive?
- One specific insight from the data (e.g., "Pérez's degradation rate on mediums was comparable to the midfield average despite the car's lower overall pace, suggesting effective tyre management from the driver side")
- A forward-looking note: what data you would track across the season to monitor their progression

This page shows you've done your homework on the team and can think about a new entrant's challenges analytically.

### Page 10 — Methodology, Tools & Next Steps

**Top half: Technical summary.**

A clean, compact section listing:
- **Data source:** FastF1 3.x (MIT license), accessing F1 live-timing data for the selected race session
- **Fuel correction method:** Estimated fuel consumption of ~1.7 kg/lap, time effect of ~0.033 s/kg, applied as an additive correction to isolate tyre degradation from fuel burn-off
- **Filtering:** Quick-laps only (pit-in/out laps, formation lap, and laps beyond 107% threshold excluded via FastF1's built-in filtering)
- **Tools:** Python 3.10+, pandas, matplotlib, seaborn, NumPy, Jupyter Notebook

**Bottom half: What I would build next (given more time).**

Three to four short bullets signalling depth without requiring you to have built them:
- Monte Carlo race simulation: model thousands of strategy paths with randomised safety car events to compute optimal pit windows with confidence intervals
- Circuit classification model: cluster all circuits by degradation severity and pit-loss time to predict optimal strategy type before a race weekend
- Tyre cliff detection: fit piecewise regression to identify the exact lap where compound performance drops nonlinearly
- Live-session dashboard: a Streamlit or Plotly Dash app that ingests FastF1 data in near-real-time and visualises strategy options as the race unfolds

These show the interviewer where your thinking goes — without overpromising what's in the document.

---

## Production Notes

### Printing and Format
- Target: A4 or US Letter, landscape orientation for chart-heavy pages (2, 4, 6), portrait for text-heavy pages (3, 5, 7, 9, 10). Or use consistent landscape throughout for a presentation-deck feel.
- Export charts from matplotlib at 300 DPI minimum for print clarity.
- Use FastF1's dark theme (`color_scheme='fastf1'`) for the charts but consider whether dark backgrounds print well on paper. If printing on white paper, you may want to invert to a light theme or print on high-quality colour stock where the dark background reproduces cleanly.
- Bind or staple neatly. A simple black cover with the title page visible through a window, or a clean spiral bind, signals professionalism.

### Build Order
1. Load the candidate race in FastF1. Inspect stint diversity and confirm it meets the selection criteria.
2. Build the Strategy Gantt (pages 2–3). This is the highest-value visual.
3. Build the degradation curves and fuel correction (pages 4–5). This is the technical credibility piece.
4. Build the undercut/overcut gap chart (pages 6–7). Pick the battle after seeing the Gantt.
5. Build the Cadillac/proxy spotlight (pages 8–9).
6. Write the title page and methodology page last, once you know exactly what's in the document.

### Time Estimate
- Data exploration and race selection: 1–2 hours
- Strategy Gantt chart (polished): 2–3 hours
- Degradation analysis with fuel correction: 2–3 hours
- Undercut/overcut case study: 1–2 hours
- Cadillac spotlight: 1–2 hours
- Title page, methodology, annotations, print formatting: 2–3 hours
- **Total: roughly 10–15 hours of focused work**
