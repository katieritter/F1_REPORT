# Counting Pit Stops in FastF1 — Don't Trust the Stint Counter

## The short version
The obvious way to count a driver's pit stops is *number of stints − 1* using
FastF1's `Stint` column. **That overcounts**, sometimes wildly, because FastF1
occasionally splits the closing laps of a race into **phantom single-lap stints**
that don't correspond to any real tyre change.

The fix: count a stop only when the tyre is actually changed — i.e. when
**`TyreLife` drops between consecutive laps** (a fresh set resets the age to ~1)
or when the **compound changes** between consecutive laps. The compound-change
check catches lap-2 edge cases where a car changes tyre but `TyreLife` remains 1.

## The smoking gun: 2025 Canadian Grand Prix (Montreal)
Counting by the stint counter, most of the field appeared to make **4–6 pit stops**
in a dry race that is normally a 1–2 stopper. Verstappen's stints looked like this:

| Stint | Laps | Compound | TyreLife at start | Real? |
|------:|------|----------|------------------:|-------|
| 1 | 1–12  | MEDIUM | 4  | yes (start) |
| 2 | 13–37 | HARD   | 1  | **real stop** (lap 12) |
| 3 | 38–67 | HARD   | 1  | **real stop** (lap 37) |
| 4 | 68    | HARD   | 31 | phantom |
| 5 | 69    | HARD   | 32 | phantom |
| 6 | 70    | HARD   | 33 | phantom |

Stints 4–6 are single laps at the very end where the **tyre age keeps climbing
(31 → 32 → 33)** instead of resetting. That is the *same* hard tyre getting older —
not three extra pit stops. So Verstappen made **2 stops**, not 5.

## The fix and its effect
Counting real tyre changes (`TyreLife` resets) instead of the stint counter:

| | Stint-counter (wrong) | TyreLife-reset (correct) |
|---|---|---|
| **Montreal field** | mostly 4–6 stops | 9 cars 1-stop, 9 cars 2-stop, 2 cars 3-stop |

That is a completely normal Canadian GP.

## How widespread is it?
Across the 2025 season, **55 of 476 driver-races (~12%)** were overcounted by the
stint-counter method — Canada was the worst, but the glitch appears in small
amounts at many races (usually 1–3 phantom end-of-race stints). Left unfixed it
inflates every stops-per-race and strategy-aggression number.

## What we do in the report
- `analysis.stops_per_car()` counts a stop as a lap where `TyreLife` falls below the
  previous lap or the compound changes. The stops-per-race chart and the
  strategy-aggression quadrant exclude DNFs/short races by requiring at least 90%
  race distance, so 0-stop retirements are not shown as strategy choices. The
  corrected season average is **~1.55 stops per representative car** (dry races).
- The slides note this explicitly so the method is transparent.

## Related
- Wet races are excluded entirely from tyre/strategy analysis — see
  `wet-races-and-tyre-data.md`. (Their stint/pit data is even messier.)

## Takeaway
FastF1's `Stint` and `PitInTime` fields can both fire on non-stops at the end of a
race. For an accurate pit-stop count, **detect the tyre change itself**
(`TyreLife` reset or compound change), not the stint number.
