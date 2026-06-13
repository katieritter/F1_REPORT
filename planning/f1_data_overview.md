Free F1 Datasets for Tire-Focused Data Science Reports in Python
TL;DR
FastF1 is your single most important resource — it is the only free source that exposes per-lap tire compound, tire age (TyreLife), stint number, and a "fresh tire" flag for 2018–present, all as pandas DataFrames ready for matplotlib/seaborn/plotly. Build your tire-strategy portfolio on it.
Pair FastF1 with OpenF1 (dedicated `/stints` and `/pit` REST endpoints, 2023+, free, no auth) for a second tire-rich source, and use Jolpica-F1 (the community successor to the now-defunct Ergast API) plus the Kaggle "Formula 1 World Championship 1950–2024" CSV dump for historical results, pit-stop timing, and lap times back to 1950 — but note those last two have no tire-compound data.
Highest-impact tire charts to build: stint/strategy Gantt bars, lap-time-vs-tire-age degradation curves per compound, compound pace box/violin plots, and undercut/overcut pit-window analysis — all demonstrated in FastF1's own example gallery.
Key Findings
Tire-specific data (compound, tire age, stint, fresh-tire flag) is realistically only available free from FastF1 and OpenF1, both of which draw on F1's official live-timing feed and cover 2018+ and 2023+ respectively.
The classic historical sources — Ergast (shut down after 2024), its successor Jolpica-F1, and the Kaggle/Ergast CSV dump — contain pit-stop timing and lap times but zero tire-compound information.
All sources are free and suitable for portfolio/practice use, but each is unofficial and carries non-commercial-leaning terms; none is affiliated with Formula 1.
Details
1. FastF1 (Python library) — the core tool
What it is. FastF1 is an open-source Python package (`pip install fastf1`, also `conda install -c conda-forge fastf1`) for accessing and analyzing F1 timing data and telemetry. It is MIT-licensed, authored by Philipp Schaefer (theOehrly), and returns all data as extended pandas DataFrames with F1-specific helper methods. The current release is FastF1 3.8.3, and the library requires Python 3.10 or higher.
Data it provides:
Lap timing — lap times, sector times (Sector1/2/3Time), speed-trap speeds, pit-in/pit-out times, lap number, position.
Tire data — `Compound`, `TyreLife`, `FreshTyre`, `Stint` (see below).
Car telemetry — Speed, Throttle, Brake, nGear, RPM, DRS, plus X/Y/Z position data, sampled roughly every 240 ms.
Weather — air temp, track temp, humidity, wind speed/direction, pressure, rainfall.
Session results — grid, finish position, status, points, Q1/Q2/Q3 times.
Schedule / event info and circuit corner/marshal data.
Tire-specific columns on `session.laps`:
`Compound` (str): event-specific name — SOFT, MEDIUM, HARD, INTERMEDIATE, WET, plus TEST_UNKNOWN/UNKNOWN. Note: the underlying C1–C5 compounds are NOT differentiated; you only get the relative soft/medium/hard label for that weekend.
`TyreLife` (float): laps driven on the current tire set (includes laps from other sessions for used sets).
`FreshTyre` (bool): True if the tire had TyreLife=0 at stint start (i.e., a new tire).
`Stint` (int): stint counter per driver.
`PitInTime` / `PitOutTime`: timestamps for pit laps.
Data availability. Timing, telemetry, tire and weather data are available from 2018 onwards, usually 30–120 minutes after a session ends. Schedule and results go back to 1950 via the Ergast/Jolpica backend (lap-time data through that backend is limited to 1996–present). Seasons before 2018 cannot load lap/telemetry/tire data.
Caching. Caching should almost always be enabled to speed scripts and avoid rate limits. Call `fastf1.Cache.enable_cache('path/to/folder')` right after import. FastF1 enforces roughly 4 requests/second and uses the Ergast/Jolpica backend (200–500 requests/hour) — caching prevents re-downloads (a single session can be ~200–500 MB).
Install + quickstart code:
```python
import fastf1
fastf1.Cache.enable_cache('cache')                  # enable caching first

session = fastf1.get_session(2023, 'Monaco', 'R')   # year, GP, session
session.load()                                      # timing/telemetry/weather

laps = session.laps
# Tire columns: Driver, Stint, Compound, TyreLife, FreshTyre, LapTime, LapNumber
```
Tire-strategy example (from FastF1's official gallery): group laps by driver/stint/compound to get stint lengths, then draw a horizontal stacked bar (Gantt) chart of strategies, coloring each bar with `fastf1.plotting.get_compound_color(compound, session=session)`:
```python
stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
stints = stints.groupby(["Driver", "Stint", "Compound"]).count().reset_index()
stints = stints.rename(columns={"LapNumber": "StintLength"})
```
Tire-degradation example: filter representative laps with `.pick_quicklaps()` (drops in/out and slow laps below the 107% threshold), group by compound, and plot LapTime against TyreLife to get degradation curves. FastF1's plotting module integrates with matplotlib and provides official team/compound colors and a dark "fastf1" style via `fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')`.
Licensing/terms. FastF1 is MIT-licensed (free for portfolio use). The underlying data comes from F1's live-timing API plus Ergast/Jolpica; FastF1 is unofficial and not associated with Formula 1, and Ergast terms apply to that portion. Rich tire data: the best free option.
2. Ergast API / Jolpica-F1 API
Ergast status. The Ergast Developer API was an experimental, non-commercial historical motor-racing web service covering F1 from 1950. Maintainer Chris Newell confirmed its end directly in the Ergast FAQ: "The API and website will be shutdown after the 2024 season. Cheers, Chris" — citing that "the API has become technically harder to maintain following a[n] upgrade of the server plus I'm frequently unavailable on race weekends... There have never been any legal issues." It is no longer updated for 2025+.
Jolpica-F1 — the successor. Jolpica-F1 is an open-source, community-maintained, Ergast-compatible replacement API (Apache 2.0 license). To migrate, replace `ergast.com/api/f1/` with `api.jolpi.ca/ergast/f1/`. It covers 1950–present, requires no authentication, and is free.
Endpoints (all under `/ergast/f1/`): circuits, constructors, constructorStandings, drivers, driverStandings, laps (`/{season}/{round}/laps/`), pitstops (`/{season}/{round}/pitstops/`), qualifying, races, results, seasons, sprint, status. Query params: `limit` (default 30, max 100) and `offset` for pagination. Responses are JSON (XML no longer supported).
Rate limits. Per the Jolpica `rate_limits.md`: a burst limit of 4 requests per second and a sustained limit of 500 requests per hour for unauthenticated access (the project's original launch announcement set 200/hour and was later raised). HTTP 429 is returned when exceeded; the docs recommend caching and efficient filtered queries (e.g. `2024/12/laps.json?limit=100&offset=0`).
Tire relevance. Like Ergast, Jolpica provides pit-stop data (stop number, lap, local time, duration) and lap times (lap-by-lap position and time) but NO tire-compound data. Lap data is available from 1996; pit-stop data from 2012. Useful for historical pit-stop counts/timing and lap-time trends, not compound analysis.
Python access. Plain `requests`/`urllib` against the REST endpoints, or via FastF1's `fastf1.ergast` module (which now points at Jolpica) returning pandas DataFrames.
3. Kaggle F1 datasets
"Formula 1 World Championship (1950–2024)" by Rohan Rao (rohanrao / vopani) — the most popular F1 Kaggle dataset, a direct CSV dump of the Ergast database. License: CC0 Public Domain on Kaggle (note: the upstream Ergast data itself is CC BY-NC-SA 3.0, so the attribution/non-commercial spirit is worth respecting).
14 CSV files: circuits, constructor_results, constructor_standings, constructors, driver_standings, drivers, lap_times, pit_stops, qualifying, races, results, seasons, sprint_results, status.
Key tire-relevant schemas (verbatim from the Ergast schema the CSVs mirror):
`pit_stops.csv`: raceId, driverId, stop, lap, time, duration, milliseconds (note `time` is the clock time of day, `duration`/`milliseconds` are the stop length).
`lap_times.csv`: raceId, driverId, lap, position, time, milliseconds.
No tire-compound data. This dataset has no compound, stint, or tire-age field anywhere — Ergast never captured tire data (Ergast users explicitly requested "tyres_fitted/tyres_removed" fields and were told it is unavailable). It's excellent for results, standings, pit-stop timing and lap times back to 1950, but you must combine it with FastF1/OpenF1 for any compound work.
Download via Python:
```python
import kagglehub
path = kagglehub.dataset_download("rohanrao/formula-1-world-championship-1950-2020")
print("Files at:", path)
```
or CLI: `kaggle datasets download -d rohanrao/formula-1-world-championship-1950-2020 --unzip` (both require a `kaggle.json` API token in `~/.kaggle/`).
Other Kaggle datasets:
`jtrotman/formula-1-race-data` — an Ergast CSV dump kept current: per its description, "The data to 2024 is downloaded from http://ergast.com/mrd/... From 2025 the data is refreshed after each Grand Prix weekend using the new Ergast compatible API provided by api.jolpi.ca", currently covering race data from 1950 to 2026 (Round 5, Canada). Best choice if you want the Ergast schema with up-to-date seasons.
`aadigupta1601/f1-strategy-dataset-pit-stop-prediction` — lap-level data that does include Stint, TyreLife and Normalized_TyreLife columns (built from FastF1; CC BY-SA 4.0). A ready-made tire dataset if you want CSVs instead of calling FastF1.
4. Other free F1 data sources
OpenF1 (openf1.org) — an open-source REST/MQTT/WebSocket API, the best complement to FastF1 for tire work. Free historical data from 2023 onwards, no authentication; JSON or CSV (`csv=true`). Live data needs a paid sponsor tier (€9.90/month). Per openf1.org, "the free tier allows 3 req/s and 30 req/min... Project supporters receive double that capacity." License CC BY-NC-SA 4.0; unofficial/non-commercial.
`/stints` endpoint returns: `compound`, `driver_number`, `lap_start`, `lap_end`, `stint_number`, `tyre_age_at_start`, plus meeting/session keys. This is explicit per-stint tire data.
`/pit` endpoint: pit lane timing and `pit_duration` (filterable, e.g. `pit_duration<31`).
Also: car telemetry (~3.7 Hz), laps, intervals, position, weather, race control, team radio (18 endpoints total).
Example: `https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3`
Python:
```python
from urllib.request import urlopen
import json, pandas as pd
url = "https://api.openf1.org/v1/stints?session_key=9165"
df = pd.DataFrame(json.loads(urlopen(url).read().decode("utf-8")))
```
Caveat: there are documented data-quality issues where a stint's `lap_end` equals the next stint's `lap_start` (e.g., 2024 Hungarian GP), and some compounds were mislabeled in certain 2024 races.
GitHub / other: `TracingInsights/RaceData` (auto-updated Ergast-style CSVs), `RaceOptiData` (paid Ergast-format dumps continuing past 2024), and the `f1dataR` R package (wraps both Jolpica and FastF1). The official F1 live-timing SignalR feed is the ultimate upstream source but is unofficial to consume and is what FastF1/OpenF1 already wrap, so there is little reason to use it directly.
5. Tire-specific analysis & chart ideas
Using FastF1 (primary) or OpenF1 `/stints`:
Stint/strategy Gantt chart — horizontal stacked bars per driver, segments colored by compound, width = stint length. The flagship "cool chart."
Tire-degradation curves — median LapTime vs. TyreLife per compound (line chart); fit a linear/polynomial slope to quantify seconds-lost-per-lap by compound.
Lap-time vs. tire-age scatter — colored by compound, with regression lines; great for seaborn `lmplot`/`regplot`.
Compound pace comparison — box/violin plots of quicklap times grouped by compound.
Pit-stop window / undercut–overcut analysis — plot the gap between two drivers across the pit cycle; an undercut is pitting earlier for fresh-tire pace (works on high-deg tracks), an overcut is staying out on warm tires (works on low-deg tracks like Monaco). A typical pit stop costs ~20–25 seconds of track-position time (outliers reach ~30s at long pit lanes like Imola, under 20s at COTA); the actual stationary stop can be astonishingly fast — McLaren set the F1 world record of 1.80 seconds for Lando Norris at the 2023 Qatar Grand Prix.
Compound usage distribution — stacked bars of laps per compound by team.
Fuel-corrected degradation — note that raw lap times often fall through a stint as fuel burns off and tires warm up, so true degradation requires correcting for the fuel effect; this is a strong "shows sophistication" addition for an interview.
Recommendations
Start with FastF1 today. Install it, enable caching, and reproduce the official tire-strategy Gantt and degradation examples on a recent race with varied strategies (e.g., a 2024/2025 GP such as Hungary, or any one-vs-two-stop race). This alone covers compounds, stints, tire age and degradation — the user's core focus.
Add OpenF1 `/stints` + `/pit` as a second, REST-based pipeline to show you can work with raw JSON APIs and pandas, not just a wrapper library. Build a small Plotly/Streamlit dashboard from it.
Use Kaggle (rohanrao or jtrotman) + Jolpica for a historical breadth piece — e.g., pit-stop duration trends or lap-time evolution across decades — while being explicit that these lack compound data.
Build one polished "signature" report: a single race deep-dive combining a strategy Gantt, per-compound degradation curves, an undercut/overcut gap chart, and a fuel-corrected pace comparison, styled with FastF1's official team/compound colors. For an internship focused on reporting and race analytics, this directly mirrors the deliverables a strategy/trackside team produces.
Benchmarks that change the plan: if you need pre-2018 tire analysis, no free source exists — pivot to results/pit-timing analysis with Kaggle/Jolpica instead. If you need live race data, you must pay for OpenF1's sponsor tier or record the live-timing stream via FastF1's built-in recorder. If you hit HTTP 429 errors, your caching is misconfigured — fix that before scaling up requests.
Caveats
FastF1 and OpenF1 tire data only go back to 2018 and 2023 respectively; nothing free has compound data before 2018 (FastF1's lap data via the Ergast/Jolpica backend reaches 1996, but without compounds).
FastF1's `Compound` gives only the relative SOFT/MEDIUM/HARD label, not the absolute C1–C5 compound used that weekend (you can cross-reference Pirelli's published per-race allocation if you need the exact C-number).
Ergast is dead (no 2025+ data); rely on Jolpica or an updated Kaggle dump (jtrotman) for current seasons.
Kaggle (rohanrao) and Jolpica/Ergast have NO tire-compound data — a common misconception worth stating explicitly in any report you publish.
All these sources are unofficial and not affiliated with Formula 1; F1 trademarks belong to Formula One Licensing B.V. Treat everything as for personal/educational/portfolio use, respect rate limits, and observe the non-commercial terms (CC BY-NC-SA on OpenF1; CC BY-NC-SA 3.0 on upstream Ergast data despite Kaggle's CC0 tag).
OpenF1 has documented per-stint data-quality quirks; validate against FastF1 when accuracy matters.