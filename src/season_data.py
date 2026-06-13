"""Dummy multi-race season data mirroring a season-long FastF1 ``laps`` dataset.

Generates a full 2025-style season (all rounds concatenated) so the season
report's aggregate charts can be built before the real FastF1 ETL exists.
Same contract idea as ``src/dummy_data.py``: a real season loader can later
return the same columns and the charts won't change.

Schema adds ``Round``, ``Event``, ``Circuit`` and ``RoundLaps`` to the per-lap
columns so cross-race normalisation (per-race quicklaps, per-race fuel
correction) is possible.

NOTE: drivers/teams are an illustrative 2025-style grid; all numbers are synthetic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEASON = 2025

# (name, laps, base_lap_s, deg_mult, pit_loss_s) — illustrative circuit params.
CIRCUITS = [
    ("Australia", 58, 80.0, 1.00, 20.0), ("China", 56, 95.0, 1.10, 22.0),
    ("Japan", 53, 91.0, 1.15, 23.0),     ("Bahrain", 57, 95.0, 1.20, 22.0),
    ("Saudi Arabia", 50, 90.0, 0.90, 19.0), ("Miami", 57, 89.0, 1.05, 20.0),
    ("Imola", 63, 78.0, 0.95, 28.0),     ("Monaco", 78, 73.0, 0.80, 21.0),
    ("Canada", 70, 75.0, 0.90, 19.0),    ("Spain", 66, 78.0, 1.15, 21.0),
    ("Austria", 71, 67.0, 1.05, 20.0),   ("Britain", 52, 88.0, 1.15, 20.0),
    ("Belgium", 44, 105.0, 1.10, 19.0),  ("Hungary", 70, 78.0, 1.00, 21.0),
    ("Netherlands", 72, 72.0, 1.10, 21.0), ("Italy", 53, 82.0, 0.95, 25.0),
    ("Azerbaijan", 51, 103.0, 0.85, 19.0), ("Singapore", 62, 95.0, 0.90, 28.0),
    ("United States", 56, 96.0, 1.10, 21.0), ("Mexico", 71, 78.0, 0.90, 22.0),
    ("Brazil", 71, 71.0, 1.05, 21.0),    ("Las Vegas", 50, 95.0, 0.85, 20.0),
    ("Qatar", 57, 84.0, 1.25, 25.0),     ("Abu Dhabi", 58, 87.0, 1.00, 22.0),
]

# Illustrative 2025 grid: (code, number, team). Team names match theme.TEAM_COLORS.
GRID = [
    ("VER", 1, "Red Bull Racing"), ("TSU", 22, "Red Bull Racing"),
    ("NOR", 4, "McLaren"),         ("PIA", 81, "McLaren"),
    ("LEC", 16, "Ferrari"),        ("HAM", 44, "Ferrari"),
    ("RUS", 63, "Mercedes"),       ("ANT", 12, "Mercedes"),
    ("ALO", 14, "Aston Martin"),   ("STR", 18, "Aston Martin"),
    ("GAS", 10, "Alpine"),         ("COL", 43, "Alpine"),
    ("ALB", 23, "Williams"),       ("SAI", 55, "Williams"),
    ("HAD", 6, "RB"),              ("LAW", 30, "RB"),
    ("HUL", 27, "Kick Sauber"),    ("BOR", 5, "Kick Sauber"),
    ("OCO", 31, "Haas"),           ("BEA", 87, "Haas"),
]

# Car pace delta (s/lap) by team.
TEAM_PACE = {
    "McLaren": 0.00, "Ferrari": 0.15, "Mercedes": 0.18, "Red Bull Racing": 0.20,
    "Williams": 0.75, "RB": 0.80, "Aston Martin": 0.85, "Haas": 0.90,
    "Alpine": 0.95, "Kick Sauber": 1.05,
}

# Tyre-management factor (multiplies degradation). <1 = kinder to tyres.
TEAM_DEG = {
    "McLaren": 0.90, "Mercedes": 0.92, "Williams": 0.98, "Ferrari": 1.00,
    "RB": 1.02, "Red Bull Racing": 1.05, "Alpine": 1.08, "Aston Martin": 1.10,
    "Haas": 1.12, "Kick Sauber": 1.15,
}

# Pit-crew baseline stationary time (s) per team — best (fastest) to worst.
TEAM_PIT = {
    "Red Bull Racing": 2.35, "McLaren": 2.42, "Ferrari": 2.52, "Mercedes": 2.55,
    "RB": 2.62, "Williams": 2.70, "Aston Martin": 2.74, "Alpine": 2.80,
    "Haas": 2.85, "Kick Sauber": 2.92,
}

# Strategy aggression (0 conservative .. 1 aggressive): biases stop count and
# soft-compound usage, so compound-usage and strategy charts show real spread.
TEAM_AGG = {
    "Red Bull Racing": 0.70, "Ferrari": 0.62, "McLaren": 0.55, "RB": 0.55,
    "Alpine": 0.50, "Mercedes": 0.45, "Aston Martin": 0.40, "Haas": 0.35,
    "Williams": 0.30, "Kick Sauber": 0.25,
}

# Short labels for charts.
TEAM_SHORT = {
    "Red Bull Racing": "Red Bull", "McLaren": "McLaren", "Ferrari": "Ferrari",
    "Mercedes": "Mercedes", "Aston Martin": "Aston Martin", "Alpine": "Alpine",
    "Williams": "Williams", "RB": "Racing Bulls", "Haas": "Haas",
    "Kick Sauber": "Sauber",
}

_COMPOUND_OFFSET = {"SOFT": -0.45, "MEDIUM": 0.0, "HARD": 0.35}
_COMPOUND_DEG = {"SOFT": 0.090, "MEDIUM": 0.055, "HARD": 0.035}
_FUEL_PER_LAP = 0.055


def _wpick(rng, options, weights):
    w = np.asarray(weights, dtype=float)
    return options[int(rng.choice(len(options), p=w / w.sum()))]


def _stints(rng, laps, two_stop, agg):
    """Pick compounds (weighted toward soft for aggressive teams) and stint lengths."""
    if two_stop:
        opts = [("SOFT", "MEDIUM", "HARD"), ("MEDIUM", "HARD", "SOFT"),
                ("SOFT", "MEDIUM", "MEDIUM"), ("MEDIUM", "MEDIUM", "HARD")]
    else:
        opts = [("SOFT", "HARD"), ("MEDIUM", "HARD"), ("HARD", "MEDIUM")]
    weights = [1.0 + agg * 1.8 * o.count("SOFT") + (1 - agg) * 1.4 * o.count("HARD")
               for o in opts]
    comps = _wpick(rng, opts, weights)

    if len(comps) == 3:
        p1 = int(laps * rng.uniform(0.20, 0.34))
        p2 = min(p1 + int(laps * rng.uniform(0.30, 0.42)), laps - 6)
        return [(comps[0], p1), (comps[1], p2 - p1), (comps[2], laps - p2)]
    p1 = int(laps * rng.uniform(0.38, 0.58))
    return [(comps[0], p1), (comps[1], laps - p1)]


def _race_rows(rng, rnd, circ):
    name, laps, base, degm, pit_loss = circ
    rows = []
    base_two_stop = min(0.85, max(0.05, (degm - 0.80) * 1.1))
    for code, num, team in GRID:
        car = TEAM_PACE[team] + float(rng.normal(0, 0.05))
        tdeg = TEAM_DEG[team]
        agg = TEAM_AGG[team]
        two_stop_prob = min(0.92, max(0.03, base_two_stop + (agg - 0.5) * 0.5))
        stints = _stints(rng, laps, rng.random() < two_stop_prob, agg)
        lap, cum, ns = 0, 0.0, len(stints)
        for si, (comp, length) in enumerate(stints, start=1):
            for life in range(1, length + 1):
                lap += 1
                is_out = si > 1 and life == 1
                is_in = si < ns and life == length
                lt = (base + car + (laps - lap) * _FUEL_PER_LAP
                      + _COMPOUND_OFFSET[comp]
                      + _COMPOUND_DEG[comp] * tdeg * degm * life
                      + float(rng.normal(0, 0.15)))
                if lap == 1:
                    lt += 3.0
                if is_out:
                    lt += 1.8
                if is_in:
                    lt += pit_loss
                cum += lt
                rows.append({
                    "Round": rnd, "Event": name, "Circuit": name, "RoundLaps": laps,
                    "Driver": code, "DriverNumber": num, "Team": team,
                    "LapNumber": lap, "Stint": si, "Compound": comp,
                    "TyreLife": life, "FreshTyre": life == 1,
                    "LapTime": pd.to_timedelta(lt, unit="s"),
                    "Time": pd.to_timedelta(cum, unit="s"),
                    "PitInTime": pd.to_timedelta(cum, unit="s") if is_in else pd.NaT,
                    "PitOutTime": pd.to_timedelta(cum, unit="s") if is_out else pd.NaT,
                })
    return rows


def get_season_laps(seed: int = 7) -> pd.DataFrame:
    """Generate the full synthetic season as one concatenated laps DataFrame."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for rnd, circ in enumerate(CIRCUITS, start=1):
        rows.extend(_race_rows(rng, rnd, circ))
    return pd.DataFrame(rows)


def get_pit_stops(laps: pd.DataFrame, seed: int = 11) -> pd.DataFrame:
    """Per-stop stationary times derived from the laps' pit-in events. Each team
    has a baseline crew pace; ~5% of stops are botched (a slow tail)."""
    rng = np.random.default_rng(seed)
    pit = laps[laps["PitInTime"].notna()]
    rows = []
    for team, rnd, drv in zip(pit["Team"], pit["Round"], pit["Driver"]):
        t = TEAM_PIT[team] + abs(float(rng.normal(0, 0.18)))
        if rng.random() < 0.05:
            t += float(rng.uniform(1.2, 3.0))  # botched stop
        rows.append({"Team": team, "Round": rnd, "Driver": drv, "Stationary": t})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    laps = get_season_laps()
    print(f"{len(laps)} laps · {laps.Round.nunique()} rounds · "
          f"{laps.Driver.nunique()} drivers · {laps.Team.nunique()} teams")
