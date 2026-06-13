# Wet Races and Why They Break Tyre-Degradation Analysis (2025)

## The short version
Tyre-degradation analysis assumes a simple thing: **as a tyre gets older, the car
gets slower**. We measure that by fuel-correcting the lap times and fitting a line
through lap time vs. tyre age — the slope is the degradation rate (seconds lost per
lap of tyre life).

In a **wet or drying race that assumption collapses**, and the maths returns
nonsense — often *negative* degradation, as if the tyres got faster the older they
got. They didn't. The track did.

## Why a drying track produces "negative degradation"
On a wet track that is drying out, lap times fall dramatically from one lap to the
next — not because of the tyres, but because:

- the racing line **rubbers in and dries**, so grip climbs steeply through the race;
- cars switch from full wets → intermediates → slicks as conditions improve;
- early laps are run behind the safety car or at reduced pace.

So the *fastest* laps of the race are usually the *last* ones, on the *oldest* tyres.
When we fit "lap time vs tyre age" to that, the line slopes **downward** — a negative
degradation rate. It is an artefact of the drying track, not a real tyre measurement.
The signal we want (tyre wear) is completely swamped by track evolution.

On top of that, the dry-tyre stints in these races are short, fragmented, and run in
unrepresentative conditions, so even the "dry" laps that exist are poor data for
degradation.

## The 2025 races affected
Of the 24 rounds, only **three** had meaningful wet running (measured as the share of
race laps on intermediate or wet tyres in our data):

| Round | Race | Wet/inter laps | Notes |
|------:|------|---------------:|-------|
| 1  | **Australian Grand Prix** (Melbourne) | **81%** | Heavily wet/mixed start-to-finish; almost no representative dry running. No soft-tyre laps at all. |
| 12 | **British Grand Prix** (Silverstone) | **74%** | Classic Silverstone mixed conditions; mostly inters/wets with a drying phase. |
| 13 | **Belgian Grand Prix** (Spa-Francorchamps) | **30%** | Delayed/wet opening, then a drying track onto slicks — a partial wet race. |

**Every other 2025 round was fully dry (0% wet laps)** and is safe for tyre-degradation
analysis.

These three are exactly the circuits that showed broken degradation numbers in the
season report's circuit heatmap — e.g. Melbourne and Silverstone returned large
*negative* slopes (cars "getting faster" on older tyres), which is the drying-track
artefact described above.

## A related, smaller issue: low-degradation dry circuits
Even some fully-dry races can show tiny or slightly-negative degradation — for example
Monza, Baku, Las Vegas and Abu Dhabi. Here the cause is different and less severe:

- these are **low-degradation circuits** where the real tyre wear is genuinely small;
- with such a faint signal, normal **track evolution** (grip improving through the
  race) and **safety-car/VSC** periods can tip a slope slightly negative;
- it means "no measurable degradation," not "negative degradation."

## Empty (NaN) cells in the heatmap
Some circuit × compound cells have no value at all. That happens when a compound was
**barely used** at that circuit (e.g. the soft run for only a handful of laps), leaving
too few points across too narrow a tyre-age range to fit a meaningful line.

## How we handle it in the report
1. **Exclude the wet-affected rounds** (Australia, Britain, Belgium) from circuit- and
   tyre-degradation analysis — their dry-tyre data is not representative.
2. **Require a minimum** number of dry green laps and a sufficient spread of tyre ages
   per circuit × compound cell; drop cells that don't meet it (rather than show noise).
3. Treat near-zero or slightly-negative slopes on low-deg circuits as **"no measurable
   degradation,"** not as a real negative rate.

## Takeaway
Wet races are great racing and terrible degradation data. For any season-wide tyre
analysis, the safe default is **dry races only** — in 2025 that means dropping the
Australian, British and Belgian Grands Prix before measuring degradation.
