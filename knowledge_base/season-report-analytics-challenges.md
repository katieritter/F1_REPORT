# Season Report Analytics Challenges and Interpretation Notes

This note records the main data-analysis problems encountered while building the
2025 season strategy and tyre report, the fixes used in the report pipeline, and
the cautious interpretation of the resulting team patterns.

The key principle is that the report is an analytical summary, not a causal model.
The charts are useful evidence, but strategy choices are driven by car pace,
starting position, traffic, safety cars, tyre allocation, circuit layout, race
incidents, and incomplete public data. The team explanations below should be read
as likely interpretations of the observed patterns, not definitive team intent.

## Data Sources Used

| Source | Used for | Main limitation |
|---|---|---|
| FastF1 race laps | Lap times, tyre compound, tyre age, team, driver, pit-in/out markers | `Stint` can overcount stops; wet/drying races distort degradation; compound labels are relative, not C1-C5 absolute compounds |
| OpenF1 `/pit` | Stationary pit-stop times via `stop_duration` | Some `stop_duration` rows are null; `pit_duration` is deprecated pit-lane time, not stationary time |
| Synthetic fallback data | Layout and chart development before real data exists | Never use for final analytical conclusions when real data is available |

## Challenge 1: Raw Lap Time Does Not Equal Tyre Degradation

Raw lap times get faster through a race because fuel burns off. If we fit lap time
against tyre age without correction, the slope mixes tyre wear with lower fuel
load. That can make a tyre appear stable or even improving when the car is simply
lighter.

The report handles this by adding `FuelCorrectedSeconds` in `src/analysis.py`,
using a simple per-lap fuel correction. It is an estimate, not a physical car
model, but it moves the analysis in the right direction: from raw pace toward
tyre-only pace loss.

Remaining caveat: a single correction cannot fully control for traffic, track
evolution, DRS trains, safety cars, driver lift-and-coast, or changing engine
modes. It is good enough for season-level ranking, but individual race conclusions
should still be checked visually.

## Challenge 2: Drying Circuits After Rain Break Degradation Analysis

Tyre degradation analysis assumes that, all else equal, an older tyre should make
the car slower. A drying circuit violates that assumption.

On a wet or drying track, lap times often improve rapidly through the race because
the racing line dries, standing water clears, track temperature changes, rubber is
laid down, and cars switch from wet or intermediate tyres to slicks. The track is
getting faster at the same time the tyres are getting older. The track-evolution
signal can be much larger than the tyre-wear signal.

That creates a misleading regression. If the fastest laps come late in the stint,
the fitted line can slope downward, implying "negative degradation". That does not
mean old tyres are faster. It usually means the track improved faster than the tyre
lost performance.

For 2025, the report excludes these wet-affected races from tyre-degradation and
strategy-pattern analysis:

| Round | Race | Why excluded |
|---:|---|---|
| 1 | Australia / Melbourne | Heavy wet and mixed conditions; very little representative dry running |
| 12 | Britain / Silverstone | Mostly wet/intermediate running and drying-track effects |
| 13 | Belgium / Spa-Francorchamps | Delayed/wet opening and drying transition to slicks |

This is why the report uses 21 dry rounds for tyre degradation, circuit severity,
compound usage, stop distribution, and strategy aggression. Pit-stop stationary
time is different: pit crew performance can use all 24 races because the question
is operational execution, not dry-tyre wear.

## Challenge 3: Low-Degradation Dry Circuits Can Also Produce Near-Zero Slopes

Some dry circuits have very low tyre degradation. In the current heatmap, Monza,
Baku, Las Vegas, Suzuka, and Lusail sit near the low-degradation end. At these
tracks the real tyre-wear signal is small, so normal track evolution, safety-car
periods, traffic, and lap filtering can push fitted slopes close to zero.

Monza is the best example. A `0.000` heatmap cell does not mean the tyres had no
physical wear. It means the model found no measurable positive degradation after
fuel correction and filtering. At a low-energy circuit, tyre wear might cost only
a few thousandths or hundredths per lap, while the racing line is also rubbering in
and grip is improving. If the tyre is losing roughly +0.01 s/lap but the track is
gaining roughly -0.01 s/lap, the fitted slope can look flat or slightly negative.
That is a track-evolution cancellation problem, not proof of zero wear.

The report treats slightly negative or near-zero values on dry low-degradation
circuits as "no measurable degradation," not as proof that tyres improve with age.
For the circuit heatmap, negative slopes are floored to zero after wet races are
excluded.

## Challenge 4: Cross-Race Normalisation Is Essential

Absolute lap times cannot be compared across circuits. A 90-second lap in Jeddah
and a 70-second lap in Austria are not measuring the same thing. The report avoids
global lap-time comparisons by fitting degradation within race/compound/team
groups and then aggregating slopes.

Quicklap filtering is also applied per round, not globally. A global 107% cutoff
would be wrong because each race has a different baseline lap time.

## Challenge 5: FastF1 `Stint` Is Not Reliable for Counting Stops

The obvious stop-count method is `number_of_stints - 1`. That is unsafe. FastF1 can
split late-race laps into phantom stints even when no tyre change happened. Canada
2025 was the clearest case: the `Stint` counter suggested many cars made 4-6 stops,
but tyre age continued rising through the phantom stints.

The report uses `analysis.stops_per_car()` instead. A stop is counted when either:

- `TyreLife` drops versus the previous lap, meaning a fresher set was fitted.
- `Compound` changes versus the previous lap, catching lap-2 edge cases where a car
  changed tyre but `TyreLife` stayed at 1.

This avoids both known failure modes:

- Phantom end-of-race stints that overcount stops.
- Early compound-change rows that undercount stops if tyre age does not drop.

## Challenge 6: 0-Stop Rows Are Usually DNFs, Not Strategy Choices

The raw stop-count output produced 0-stop rows. Most were cars that retired or
completed only a small fraction of the race. A 0-stop DNF is not a strategy choice,
so it should not be plotted beside real 1-stop, 2-stop, or 3-stop strategies.

The report now filters stop-distribution and strategy-aggression data to
representative car-races only: the car must complete at least 90% of race distance.
After this filter, the representative dry-race stop distribution is:

| Stops | Representative car-races |
|---:|---:|
| 1 | 201 |
| 2 | 152 |
| 3 | 25 |
| 4 | 3 |

This gives a corrected dry-race average of about 1.55 stops per representative car.
Stops of 4 or more are grouped as `4+` in the chart.

## Challenge 7: Pit Stop Timing Uses OpenF1, Not FastF1

The pit-crew performance chart needed stationary stop time, not the full time lost
in the pit lane. The important OpenF1 fields are:

| Field | Meaning | Used? |
|---|---|---|
| `stop_duration` | Stationary tyre-change time | Yes |
| `lane_duration` | Full time travelling through the pit lane | No, not for crew-performance ranking |
| `pit_duration` | Deprecated alias of pit-lane duration | No |

The first attempted ETL used `pit_duration`, which would have charted values around
20-28 seconds. That is pit-lane transit time, not stationary stop performance. The
fixed ETL uses `stop_duration` as `Stationary`.

The generated pit-stop dataset has 702 valid `stop_duration` rows across all 24
2025 races. Rows with null `stop_duration` are excluded. OpenF1 rate limits also
matter: the ETL has to throttle requests or retry after `429 Too Many Requests`.

The chart caps plotted points above 9 seconds for readability. The raw parquet data
is unchanged; only the plotted outlier position is capped so normal team-to-team
differences around 2-3 seconds are visible.

## Challenge 8: Pit Stops and Stop Counts Are Different Questions

The report has two separate "pit" concepts:

- Stop count: how many times a car changed tyres in a race. This comes from FastF1
  lap/tyre data and is filtered to dry representative car-races for strategy charts.
- Stationary stop time: how long the car was stopped in the box. This comes from
  OpenF1 `stop_duration` and includes all 24 races for the operations chart.

Combining these without care leads to confusion. A team can have many strategic
stops but still execute them quickly, or have few stops but poor stationary times.

## Team-Specific Interpretation

The team-by-team interpretation has been moved to
`knowledge_base/team-strategy-interpretation-2025.md`. Keeping it separate makes
this document the methodology/caveats reference and the team note the narrative
support reference.

## Circuit-Level Interpretation From The Heatmap

The circuit heatmap supports the strategy charts:

| Circuit type | Examples | Strategic implication |
|---|---|---|
| High degradation | Bahrain/Sakhir, Sao Paulo, Monaco, Barcelona, Mexico City, Budapest | More two-stop and occasional three-stop strategies become viable because the pace loss from old tyres is large enough to pay back the pit loss. |
| Low degradation | Monza, Baku, Las Vegas, Suzuka, Lusail | One-stop strategies become attractive because old tyres do not lose enough pace to justify extra pit loss. Track position matters more. |
| Missing cells | Some circuit-compound combinations | The compound was barely used or did not have enough representative tyre-age spread to fit a meaningful slope. Do not over-interpret blanks. |

## Practical Rules We Settled On

1. Use dry races only for tyre degradation and strategy pattern charts.
2. Use all races for pit-crew stationary stop timing.
3. Never count stops from FastF1 `Stint` alone.
4. Count tyre changes from `TyreLife` reset or `Compound` change.
5. Exclude DNFs/short races from stop-distribution and strategy-aggression charts.
6. Use OpenF1 `stop_duration` for stationary pit-stop time, not `pit_duration`.
7. Cap plotted pit-stop outliers for readability, but keep raw data unchanged.
8. Treat the team explanations as plausible interpretations, not causal proof.

## Related Documents

- `knowledge_base/wet-races-and-tyre-data.md`
- `knowledge_base/pit-stop-count-fastf1.md`
- `knowledge_base/team-strategy-interpretation-2025.md`
- `src/analysis.py`
- `src/season_etl.py`
- `season_report__draft/render_assets.py`
