# F1 Race Strategy & Tyre Performance — Notebook Portfolio Plan

## Purpose

This portfolio is designed for an interview targeting a **race strategy / tyre performance** role. It demonstrates the ability to ingest, clean, model, and visualise Formula 1 timing and tyre data at a level that mirrors real strategy-desk deliverables. The work centres on the 2026 Cadillac F1 Team (Pérez & Bottas, Ferrari PU) as the narrative thread, supported by historical and cross-team analysis.

## Data Sources

| Source | Coverage | Tyre Data? | Access Method |
|--------|----------|------------|---------------|
| **FastF1** (primary) | 2018–present, lap/telemetry/weather | Yes — Compound, TyreLife, FreshTyre, Stint | `pip install fastf1`, pandas DataFrames |
| **OpenF1** | 2023–present, REST/JSON | Yes — `/stints` (compound, tyre_age_at_start) and `/pit` | `requests` / `urllib`, free, no auth |
| **Jolpica-F1** | 1950–present (Ergast successor) | No compound data; pit-stop timing from 2012, lap times from 1996 | REST API at `api.jolpi.ca/ergast/f1/` |
| **Kaggle — rohanrao** | 1950–2024, 14 CSVs | No compound data | `kagglehub` or CLI download |
| **Kaggle — jtrotman** | 1950–2026 (auto-updated) | No compound data | Same Ergast schema, current seasons |
| **Kaggle — aadigupta1601** | Lap-level with Stint/TyreLife | Yes (derived from FastF1) | CSV download, CC BY-SA 4.0 |

### Key Caveats

- FastF1's `Compound` field gives the relative label (SOFT/MEDIUM/HARD) not the absolute C1–C5. Cross-reference Pirelli's published allocation per race if the absolute compound matters.
- OpenF1 has documented data-quality issues: stint `lap_end` sometimes equals the next stint's `lap_start`, and some 2024 compounds were mislabelled. Validate against FastF1 where accuracy is critical.
- 2026 is a major regulation change. Historical tyre data (2018–2025) should be contextualised as "previous-era" when comparing to 2026 results.
- All sources are unofficial and non-commercial. Respect rate limits (FastF1 ~4 req/s; Jolpica 500 req/hr; OpenF1 free tier 3 req/s, 30 req/min). Always enable FastF1 caching.

---

## Notebook 1 — Race Strategy Decoded: Stint Architecture & Decision Windows

**Goal:** Demonstrate fluency with the core deliverable of a strategy desk — reading a race through its stint structure and pit-window decisions.

### 1.1 Strategy Gantt Chart (Hero Visual)

Select a recent race with high strategic variability (e.g., 2024 Hungarian GP or a 2025 race with mixed one/two-stop splits). Build horizontal stacked bars per driver, one segment per stint, coloured by compound using `fastf1.plotting.get_compound_color()`. Width equals stint length in laps. Sort drivers by finishing position.

This is the single most recognisable chart in F1 strategy analysis. It must be polished.

**Data:** `session.laps` → group by Driver, Stint, Compound → count LapNumber as StintLength.

### 1.2 Optimal vs Actual Pit Windows

For the same race, compute the "crossover lap" — the point where the cumulative time lost to tyre degradation on old rubber exceeds the pit-stop time penalty (~22–25 seconds, circuit-dependent). Overlay where each driver actually pitted against where the model says was optimal.

**Method:**
- Extract fuel-corrected degradation rate per compound from the race data (see Notebook 2 methodology).
- Model cumulative time loss as `deg_rate × (tyre_age - baseline_age)` per lap.
- The crossover lap is where this cumulative loss equals pit-loss time.
- Annotate: drivers who pitted early (undercut attempt), late (overcut / track-position play), or on the model's optimum.

### 1.3 Undercut / Overcut Gap Analysis

Pick a specific on-track battle (two drivers fighting for position across a pit window). Plot the gap between them lap by lap, annotating pit-in and pit-out laps for each. Show how the gap inverts (or doesn't) through the pit cycle.

Label whether the undercut or overcut succeeded and quantify the net gain/loss in seconds. An undercut works best on high-degradation circuits; an overcut works on circuits like Monaco where track position dominates.

### 1.4 One-Stop vs Two-Stop Strategy Model

For a race where both strategies were viable, model the total elapsed race time under each:
- One-stop: long first stint on hards, short second stint on mediums (or vice versa).
- Two-stop: three shorter stints, heavier use of softs.

Vary the pit-stop lap(s) across a range and plot total race time as a function of pit lap. Show the sensitivity: how many laps of "window" does the optimal one-stop have before two-stop becomes faster?

### 1.5 Cadillac Strategy Panel

If FastF1 supports 2026 sessions, pull Pérez and Bottas stint data for their best race results so far. Even at P16–P19, analyse:
- Was their compound sequence aligned with the field or different?
- Did the timing of their stops suggest reactive decisions (pitting under VSC/SC) or planned calls?
- Were their stints the right length given their degradation profile?

The question "did the wall make the right calls given the car's pace?" is exactly what a strategy role evaluates.

**Fallback:** If 2026 data is unavailable in FastF1, build this panel using a 2024/2025 backmarker team (Haas or Sauber) as a structural proxy, and note it's ready to swap in Cadillac data.

---

## Notebook 2 — Tyre Degradation Modelling: From Raw Laps to Predictive Curves

**Goal:** Show technical depth — the ability to clean noisy lap data, correct for confounding variables, and extract the degradation metrics that strategy engineers actually use.

### 2.1 Raw Degradation Curves

Plot LapTime vs TyreLife per compound for a selected race. Use `session.laps.pick_quicklaps()` to filter pit-in/pit-out laps and outliers (>107% of best lap). Separate panels or colour-coded lines for Soft, Medium, Hard.

This is the baseline visual that every subsequent analysis improves upon.

### 2.2 Fuel-Corrected Degradation

Raw lap times typically *decrease* through the early laps of a stint because the car is burning fuel and getting lighter (~1.6–1.8 kg per lap, worth roughly 0.03 seconds per lap per kilogram). This masks the true tyre degradation.

**Method:**
- Estimate fuel load per lap: `fuel_load(lap) = start_fuel - (fuel_rate × lap_number)`. Start fuel ≈ 110 kg for a full race; fuel rate ≈ total_fuel / total_laps.
- Estimate fuel-time effect: approximately 0.03–0.035 s/lap/kg (circuit-dependent; use 0.033 as default).
- Corrected lap time = raw lap time + (fuel_burned × fuel_time_effect). This *adds back* the time the driver "gained" from being lighter, isolating the tyre-only trend.
- Plot corrected degradation curves alongside raw curves. The corrected version should show a clearer upward slope.

Including this step is a strong signal of analytical sophistication. Most portfolio projects skip it.

### 2.3 Linear and Polynomial Degradation Fit

Fit a linear model to the fuel-corrected lap time vs tyre life for each compound. The slope is the **degradation rate** in seconds per lap — the single most important number in tyre strategy.

Report:
- Soft deg rate (e.g., +0.08 s/lap)
- Medium deg rate (e.g., +0.05 s/lap)
- Hard deg rate (e.g., +0.03 s/lap)

Also fit a quadratic to test for nonlinearity (the "tyre cliff" effect). If the quadratic term is significant, the compound has a cliff — performance falls off sharply after a certain age.

### 2.4 Compound Pace Box / Violin Plots

Distribution of representative lap times per compound across all drivers. Use seaborn violin plots to show not just the median but the spread. High variance on softs late in a stint (when filtered by TyreLife > 15) tells the story of inconsistent grip.

### 2.5 Degradation by Team Tier

Group teams into tiers (top 3, midfield, backmarkers including Cadillac) and compute average degradation rate per compound per tier.

**Hypothesis:** Backmarkers may suffer worse degradation because lower downforce means more sliding, which overheats tyres. Or they may show less degradation because their lower cornering speeds put less energy into the rubber. Quantify which effect dominates.

### 2.6 Track Temperature Correlation

Use FastF1's weather data (TrackTemp per lap) to regress degradation rate against track surface temperature. High track temp should correlate with higher degradation. Plot the regression with confidence intervals. This connects tyre science to environmental factors — a level of analysis strategy teams perform routinely.

---

## Notebook 3 — Cadillac Deep Dive: The New Entrant Under the Microscope

**Goal:** Tailored analysis of the Cadillac F1 Team that shows you can extract meaningful insights even from a backmarker, and contextualise a new entrant's trajectory.

### 3.1 Cadillac's Tyre Strategy Choices vs the Field

For every 2026 race completed (Australia, China, Japan, Miami, Canada, and any subsequent rounds), show Cadillac's compound sequence alongside the field consensus. Visualise as a mini strategy Gantt per race with Cadillac highlighted and the modal field strategy shown as a reference band.

Questions to answer:
- Is Cadillac copying the midfield consensus or choosing independently?
- Are they conservative (longer stints, fewer stops) or aggressive?
- Do they appear to be reacting to on-track events (SC/VSC) or executing a pre-race plan?

### 3.2 Pérez vs Bottas Head-to-Head

Stint-by-stint pace comparison between the two Cadillac drivers. Normalise by compound and tyre age to make the comparison fair.

Metrics:
- Average lap time per stint (fuel-corrected if possible)
- Degradation rate per stint
- Consistency (standard deviation of lap times within a stint)
- Tyre life management — who maintains pace deeper into a stint?

Both are experienced drivers. Pérez is historically strong on tyre management (his long stints at Racing Point/Red Bull were legendary). Bottas is typically faster in clean air but harder on rubber. Does this pattern hold at Cadillac?

### 3.3 Benchmark Against Historical New Entrants

Using Kaggle/Jolpica data (no compound data, but lap times and results), pull the debut-season gap-to-leader for:
- Haas (2016) — the most successful modern new entrant
- Manor/Marussia — struggled for years
- Caterham — never competitive
- HRT — worst-case reference

Chart each team's average gap to the race winner (as a percentage) over their first 8–10 races. Where does Cadillac 2026 sit on this convergence curve? If Cadillac's gap is shrinking faster than Manor's did, that's a positive trajectory story.

### 3.4 Ferrari Power Unit Customer Comparison

In 2026, Ferrari supplies power units to Cadillac and Haas (and runs their own works team). If 2026 data is available, compare:
- Straight-line speed (speed trap data from FastF1) — should be similar across all three if it's PU-limited.
- Tyre degradation rate — differences here isolate the chassis/aero effect.
- Race pace delta to the works Ferrari team — how much of the gap is PU and how much is chassis?

### 3.5 Operational Maturity: Pit-Stop Duration Trends

New teams almost always have slow pit stops early in their first season. Using pit-stop duration data (FastF1 `PitInTime`/`PitOutTime` or Jolpica `/pitstops`), chart Cadillac's average pit-stop time race over race.

Overlay the grid average and the best team's average for context. A downward trend demonstrates operational learning. If they've had any pit-lane errors (unsafe releases, slow stops), annotate those.

---

## Notebook 4 — Circuit DNA: How Track Characteristics Shape Tyre Strategy

**Goal:** Demonstrate the ability to think across a full season, not just one race — understanding that strategy is fundamentally shaped by circuit properties.

### 4.1 Circuit Classification by Tyre Severity

Using 2023–2025 data (three seasons for robustness), compute per-circuit averages:
- Average degradation rate (from the Notebook 2 methodology)
- Average pit-loss time (pit-out lap time minus a normal lap time)
- Number of pit stops in the optimal strategy (mode across the field)

Create a 2D scatter plot: x-axis = average degradation rate, y-axis = pit-loss time. Draw quadrant lines:
- **High deg + Low pit loss** → multi-stop races (e.g., Bahrain, Silverstone)
- **Low deg + High pit loss** → one-stop races (e.g., Monaco, Singapore)
- **High deg + High pit loss** → strategic dilemma races (e.g., Spa)
- **Low deg + Low pit loss** → flexible strategy (e.g., COTA)

Label each point with the circuit name. This is a genuine strategic planning tool.

### 4.2 Compound Allocation vs Actual Usage Heatmap

Pirelli allocates specific C1–C5 compounds per race (the SOFT/MEDIUM/HARD labels are relative). Map which absolute compounds go to which circuits across 2023–2025, then overlay actual usage rates from FastF1 stint data.

Visualise as a heatmap: rows = circuits (sorted by tyre severity), columns = compound (C1–C5), cell colour = percentage of total race laps run on that compound. Do teams avoid the softest available compound at high-deg circuits?

### 4.3 Weather-Induced Strategy Pivots

Find 2–3 races with mid-race weather changes (rain starting during a dry race, or drying conditions after rain). Visualise the strategy chaos:
- A timeline showing when each driver pitted and what compound they switched to.
- Cluster analysis: which teams reacted within 1–2 laps of the weather change vs waited 5+ laps?
- Outcome analysis: did early reactors gain or lose positions vs late reactors?

This is one of the highest-value analyses for a strategy role — reactive decision-making under uncertainty is the core of the job.

### 4.4 Sector-Level Tyre Stress Analysis

Using FastF1's sector times (Sector1Time, Sector2Time, Sector3Time), compute degradation by sector:
- For each sector, plot sector time vs tyre life.
- Identify which sectors show the steepest degradation (high-energy corner sequences that overheat tyres).
- Compare across circuits to identify "tyre-killer" sector archetypes.

This level of granularity shows you understand that degradation isn't uniform around a lap — it's driven by specific corner combinations. Strategy teams use this to set tyre management targets by sector.

---

## Notebook 5 — Predictive Strategy Engine: A Monte Carlo Pit Window Simulator

**Goal:** The "wow factor" piece. Move from descriptive analysis to a predictive model that mirrors what strategy teams build internally.

### 5.1 Monte Carlo Race Simulation

Given inputs:
- Starting grid position
- Compound-specific degradation curves (from Notebook 2)
- Pit-loss time for the circuit
- Available compound sets

Simulate thousands of possible strategy paths. For each simulation:
1. Choose a strategy (compound sequence and pit lap for each stop).
2. Compute lap times using the degradation model: `lap_time = base_pace + deg_rate × tyre_age + random_noise`.
3. Track positions based on cumulative elapsed time and simulate overtaking probability (e.g., if a faster car is behind a slower car by less than DRS-activation delta).
4. Record the finishing position.

**Output:** For each possible strategy, show the distribution of finishing positions. Report the optimal strategy (highest expected finishing position) and its sensitivity to assumptions.

### 5.2 Safety Car Sensitivity Analysis

Inject random Safety Car events into the simulation:
- Use historical SC probability (~30–40% of races have at least one SC).
- SC duration: sample from historical distribution (typically 3–6 laps).
- SC timing: uniform random across the race.

Show how the optimal pit lap shifts when SC probability is varied from 0% to 50%. Under high SC probability, strategies that haven't pitted yet gain a "free" stop — this is why teams sometimes delay pitting when the race is chaotic.

Quantify: "Under a no-SC scenario the optimal pit lap is lap 28; with a 40% SC probability the expected-value-optimal strategy shifts to lap 32 (waiting for a potential free stop)."

### 5.3 Tyre Cliff Detection

Some compounds exhibit a "cliff" — a sudden, nonlinear drop in performance after a certain number of laps. This is distinct from linear degradation and is much harder to manage.

**Method:**
- Using fuel-corrected lap times from FastF1, fit a piecewise linear model (two segments with a breakpoint) to LapTime vs TyreLife for each compound.
- If the second segment's slope is significantly steeper than the first (e.g., > 2× the first segment's slope), declare a cliff at the breakpoint lap.
- Show concrete examples: races where drivers stayed out past the cliff and lost multiple seconds per lap.

### 5.4 Interactive Dashboard (Bonus)

Wrap the race simulator in a lightweight interactive interface using `ipywidgets` inside the Jupyter notebook:
- Dropdown: select circuit (auto-populates pit-loss time and degradation profiles).
- Sliders: adjust SC probability, degradation rate multiplier, fuel correction factor.
- Button: "Run Simulation" → generates strategy recommendation with confidence intervals.

Alternatively, build a standalone Plotly Dash or Streamlit app if the interviewer wants to see deployment skills.

---

## Visual & Technical Standards

### Styling
- Use `fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')` for all matplotlib figures. The dark theme with official F1 colours looks professional and domain-specific.
- Use `fastf1.plotting.get_compound_color(compound, session=session)` for all compound-coloured elements.
- Use `fastf1.plotting.get_team_color(team, session=session)` for team-coloured elements.
- Plotly for interactive charts; matplotlib/seaborn for static publication-quality figures.

### Notebook Structure
Every notebook should follow this format:
1. **Executive Summary** (Markdown cell) — one paragraph: what question is asked, what the key finding is, and what the strategic implication is. Strategy people read the summary first.
2. **Setup** — imports, cache configuration, data loading.
3. **Analysis sections** — each with a Markdown header explaining the "why" before the code, not just the "what."
4. **Key Findings** (Markdown cell at the end) — bullet points summarising actionable insights.
5. **Data Quality Notes** — where relevant, flag known issues (OpenF1 stint boundaries, compound label limitations, missing sessions).

### Export
- Save key charts as standalone PNGs at 300 DPI for a portfolio site or PDF compilation.
- Consider rendering a final HTML export of each notebook (via `jupyter nbconvert`) for easy sharing.

---

## Execution Order & Priority

| Priority | Notebook | Reason |
|----------|----------|--------|
| 1 | **Notebook 1** — Strategy Decoded | Most visually impactful; directly demonstrates the core hiring skill. Start here. |
| 2 | **Notebook 2** — Degradation Modelling | Provides the analytical foundation that Notebooks 4 and 5 depend on. |
| 3 | **Notebook 3** — Cadillac Deep Dive | Shows tailored research and narrative ability; ties the portfolio to a specific team. |
| 4 | **Notebook 5** — Monte Carlo Simulator | The technical differentiator; most candidates won't have this. |
| 5 | **Notebook 4** — Circuit DNA | Breadth piece; lower priority but rounds out the portfolio. |

## FastF1 Quick-Start Reference

```python
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Always enable cache first
fastf1.Cache.enable_cache('cache')

# Setup plotting
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')

# Load a session
session = fastf1.get_session(2024, 'Hungary', 'R')
session.load()

# Get laps with tyre data
laps = session.laps  # Columns include: Compound, TyreLife, FreshTyre, Stint

# Filter to representative laps
quick_laps = laps.pick_quicklaps()

# Get stint summary
stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
stints = stints.groupby(["Driver", "Stint", "Compound"]).count().reset_index()
stints = stints.rename(columns={"LapNumber": "StintLength"})
```

## Cadillac 2026 Context

- **Drivers:** Sergio Pérez (#11) and Valtteri Bottas (#77)
- **Power Unit:** Ferrari (customer; own GM PU planned for 2029)
- **Team Principal:** Graeme Lowdon
- **Base:** Silverstone (UK), with facilities in Fishers, Indiana and Charlotte, North Carolina
- **2026 Season Status (through ~Round 7):** No points scored; best finishes around P13 (Bottas) to P16 (Pérez). Double-car finishes achieved at China and Miami. Reliability has been solid — Pérez finished every race through Japan. One inter-team collision in China (racing incident). No cars into Q2 in qualifying yet.
- **Strategic Narrative:** Cadillac is data-poor compared to rivals — even historical data carries less weight due to the 2026 regulation overhaul. Analysing their strategy decisions and tyre management progression across their debut season is a compelling and original portfolio angle.
