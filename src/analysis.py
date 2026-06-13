"""Tyre-performance analysis helpers — quicklap filtering, fuel correction,
and per-compound degradation stats. Written against the FastF1 ``laps`` schema
so the same functions work on real data later.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Fuel-weight time effect: ~1.7 kg burned per lap x ~0.032 s/kg ≈ 0.055 s/lap.
# An industry estimate, not an exact figure — state this in the methodology.
FUEL_CORRECTION_S_PER_LAP = 0.055

DRY_COMPOUNDS = ("SOFT", "MEDIUM", "HARD")


def lap_seconds(laps: pd.DataFrame) -> pd.Series:
    """LapTime (timedelta) as float seconds."""
    return laps["LapTime"].dt.total_seconds()


def pick_quicklaps(laps: pd.DataFrame, threshold: float = 1.07) -> pd.DataFrame:
    """Drop in-/out-laps and lap 1, then keep laps within ``threshold`` of the
    fastest remaining lap (mirrors FastF1's quicklap filtering)."""
    s = lap_seconds(laps)
    mask = (laps["PitInTime"].isna() & laps["PitOutTime"].isna()
            & (laps["LapNumber"] > 1))
    q = laps[mask].assign(_s=s[mask])
    cutoff = q["_s"].min() * threshold
    return q[q["_s"] <= cutoff].drop(columns="_s")


def add_fuel_correction(laps: pd.DataFrame, total_laps: int,
                        s_per_lap: float = FUEL_CORRECTION_S_PER_LAP) -> pd.DataFrame:
    """Add ``LapTimeSeconds`` and ``FuelCorrectedSeconds`` columns.

    Correction normalises every lap to end-of-race (low) fuel by removing the
    fuel-weight benefit carried on earlier laps, isolating tyre degradation.
    """
    s = lap_seconds(laps)
    fuel_benefit = (total_laps - laps["LapNumber"]) * s_per_lap
    return laps.assign(LapTimeSeconds=s, FuelCorrectedSeconds=s - fuel_benefit)


def pit_laps(laps: pd.DataFrame, driver: str) -> list[int]:
    """Lap numbers on which ``driver`` pitted (the in-laps)."""
    d = laps[laps["Driver"] == driver]
    return d.loc[d["PitInTime"].notna(), "LapNumber"].tolist()


def driver_gap(laps: pd.DataFrame, ahead: str, behind: str) -> pd.DataFrame:
    """Per-lap on-track gap (seconds) between two drivers, from cumulative race
    time. ``Gap`` > 0 means ``behind`` trails ``ahead``; < 0 means it leads."""
    a = (laps[laps["Driver"] == ahead]
         .set_index("LapNumber")["Time"].dt.total_seconds())
    b = (laps[laps["Driver"] == behind]
         .set_index("LapNumber")["Time"].dt.total_seconds())
    common = a.index.intersection(b.index)
    return pd.DataFrame({"LapNumber": common,
                         "Gap": (b.loc[common] - a.loc[common]).values})


# ---------------------------------------------------------------------------
# Season-level helpers (cross-race). These apply per-race normalisation, which
# is essential: a global 107% cutoff or single total-laps would be wrong across
# circuits with different lap times and race lengths.
# ---------------------------------------------------------------------------

def pick_quicklaps_season(laps: pd.DataFrame, threshold: float = 1.07) -> pd.DataFrame:
    """Quicklap filtering normalised per round: drop in-/out-laps and lap 1, then
    keep laps within ``threshold`` of *that race's* fastest lap."""
    s = lap_seconds(laps)
    q = laps.assign(_s=s)
    q = q[q["PitInTime"].isna() & q["PitOutTime"].isna() & (q["LapNumber"] > 1)]
    race_min = q.groupby("Round")["_s"].transform("min")
    return q[q["_s"] <= race_min * threshold].drop(columns="_s")


def add_fuel_correction_season(laps: pd.DataFrame,
                               s_per_lap: float = FUEL_CORRECTION_S_PER_LAP) -> pd.DataFrame:
    """Fuel-correct using each race's own length (``RoundLaps`` column)."""
    s = lap_seconds(laps)
    fuel_benefit = (laps["RoundLaps"] - laps["LapNumber"]) * s_per_lap
    return laps.assign(LapTimeSeconds=s, FuelCorrectedSeconds=s - fuel_benefit)


def team_degradation(laps_corrected: pd.DataFrame, min_laps: int = 6) -> pd.DataFrame:
    """Season degradation rate (s/lap) per team. Fit a deg slope per
    (team, round, compound) then average — controlling for compound and circuit
    so the ranking reflects tyre management, not strategy/track mix. Sorted best
    (lowest deg) first."""
    recs = []
    for (team, _rnd, _comp), d in laps_corrected.groupby(["Team", "Round", "Compound"]):
        if len(d) < min_laps or d["TyreLife"].nunique() < 3:
            continue
        slope = np.polyfit(d["TyreLife"], d["FuelCorrectedSeconds"], 1)[0]
        recs.append((team, slope))
    df = pd.DataFrame(recs, columns=["Team", "Slope"])
    out = (df.groupby("Team")["Slope"].mean()
           .reset_index().rename(columns={"Slope": "DegRate"}))
    return out.sort_values("DegRate").reset_index(drop=True)


def stops_per_car(laps: pd.DataFrame) -> pd.DataFrame:
    """Real pit-stop count per car-race: a stop = ``TyreLife`` dropping between
    consecutive laps (a new set fitted). This deliberately ignores FastF1's
    ``Stint`` counter, which spuriously splits end-of-race laps into phantom
    single-lap stints at some races (e.g. 2025 Canada) and badly overcounts
    stops. See knowledge_base/pit-stop-count-fastf1.md."""
    d = laps.sort_values(["Round", "Driver", "LapNumber"]).copy()
    d["_stop"] = d.groupby(["Round", "Driver"])["TyreLife"].diff() < 0
    return (d.groupby(["Round", "Driver"])
            .agg(Stops=("_stop", "sum"), Circuit=("Circuit", "first"),
                 Team=("Team", "first")).reset_index())


def stops_distribution(laps: pd.DataFrame) -> pd.DataFrame:
    """Per circuit, the % of the field on each stop count (1-stop, 2-stop, ...).
    Rows ordered by 2-stop share descending (most multi-stop circuits first)."""
    spc = stops_per_car(laps)
    tab = spc.groupby(["Circuit", "Stops"]).size().unstack(fill_value=0)
    shares = tab.div(tab.sum(axis=1), axis=0) * 100
    sort_col = 2 if 2 in shares.columns else shares.columns.max()
    return shares.sort_values(sort_col, ascending=False)


def strategy_aggression(laps: pd.DataFrame) -> pd.DataFrame:
    """Per team: average pit stops per car-race (x) and soft-usage share % (y) —
    the two axes of a strategy-aggression quadrant."""
    avg_stops = stops_per_car(laps).groupby("Team")["Stops"].mean()
    usage = compound_usage(laps)
    return pd.DataFrame({"AvgStops": avg_stops,
                         "SoftShare": usage["SOFT"] * 100}).dropna()


def compound_usage(laps: pd.DataFrame) -> pd.DataFrame:
    """Per-team share of race laps run on each dry compound, across the season.
    Rows ordered most→least soft-heavy (aggressive→conservative)."""
    d = laps[laps["Compound"].isin(DRY_COMPOUNDS)]
    counts = (d.groupby(["Team", "Compound"]).size().unstack(fill_value=0)
              .reindex(columns=list(DRY_COMPOUNDS), fill_value=0))
    shares = counts.div(counts.sum(axis=1), axis=0)
    return shares.loc[shares["SOFT"].sort_values(ascending=False).index]


def wet_rounds(laps: pd.DataFrame, threshold: float = 0.25) -> list[int]:
    """Rounds where intermediate/wet tyres ran on >= ``threshold`` of laps.
    These distort tyre degradation (drying track) and should be excluded."""
    wet = laps.assign(_w=laps["Compound"].isin(["INTERMEDIATE", "WET"]))
    share = wet.groupby("Round")["_w"].mean()
    return share[share >= threshold].index.tolist()


def circuit_degradation(laps_corrected: pd.DataFrame, min_laps: int = 10,
                        exclude_rounds: list[int] | None = None) -> pd.DataFrame:
    """Degradation rate (s/lap) per circuit × dry compound, pooling all cars at
    each round. Returns a pivot (rows = circuits ordered most→least punishing,
    columns = SOFT/MEDIUM/HARD) for a track-classification heatmap.

    Wet-affected rounds are excluded (their drying tracks give meaningless,
    often negative slopes). Negative slopes elsewhere — track evolution on
    low-deg circuits — are floored to 0 ("no measurable degradation")."""
    d0 = laps_corrected
    if exclude_rounds:
        d0 = d0[~d0["Round"].isin(exclude_rounds)]
    recs = []
    for (circuit, comp), d in d0.groupby(["Circuit", "Compound"]):
        if comp not in DRY_COMPOUNDS or len(d) < min_laps or d["TyreLife"].nunique() < 4:
            continue
        slope = np.polyfit(d["TyreLife"], d["FuelCorrectedSeconds"], 1)[0]
        recs.append((circuit, comp, max(slope, 0.0)))
    mat = (pd.DataFrame(recs, columns=["Circuit", "Compound", "DegRate"])
           .pivot(index="Circuit", columns="Compound", values="DegRate")
           .reindex(columns=list(DRY_COMPOUNDS)))
    return mat.loc[mat.mean(axis=1).sort_values(ascending=False).index]


def degradation_summary(laps_corrected: pd.DataFrame,
                        compounds: tuple[str, ...] = DRY_COMPOUNDS) -> pd.DataFrame:
    """Per compound: linear degradation rate (s/lap), modelled pace at a common
    tyre age, pace advantage vs HARD, and quicklap sample size."""
    rows = []
    for c in compounds:
        d = laps_corrected[laps_corrected["Compound"] == c]
        if len(d) < 5:
            continue
        slope, intercept = np.polyfit(d["TyreLife"], d["FuelCorrectedSeconds"], 1)
        rows.append({
            "Compound": c,
            "DegRate": slope,
            "PaceAt5": slope * 5 + intercept,   # modelled pace at 5 laps of life
            "Samples": len(d),
        })
    df = pd.DataFrame(rows)
    hard_pace = df.loc[df["Compound"] == "HARD", "PaceAt5"]
    baseline = hard_pace.iloc[0] if len(hard_pace) else df["PaceAt5"].max()
    df["PaceAdvVsHard"] = df["PaceAt5"] - baseline
    return df
