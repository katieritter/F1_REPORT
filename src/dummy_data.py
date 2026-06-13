"""Dummy F1 lap data that mirrors FastF1's ``session.laps`` schema.

The whole report is built against this during the draft phase so layout and
charts can be finalised before wiring in real data. Chart functions are written
to these exact column names/dtypes, so swapping in a real FastF1 loader later
(returning the same shape) requires no chart changes.

Schema (subset of FastF1 ``session.laps``):
    Driver (str, 3-letter code), DriverNumber (int), Team (str),
    LapNumber (int), Stint (int), Compound (str), TyreLife (int),
    FreshTyre (bool), LapTime (timedelta), Time (timedelta, cumulative),
    Position (int, final classification), PitInTime / PitOutTime (timedelta|NaT)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TOTAL_LAPS = 70
CIRCUIT = "Hungaroring"
EVENT = "2024 Hungarian Grand Prix"

# (code, number, team) — 2024 grid
_GRID = [
    ("VER", 1, "Red Bull Racing"), ("PER", 11, "Red Bull Racing"),
    ("NOR", 4, "McLaren"),         ("PIA", 81, "McLaren"),
    ("LEC", 16, "Ferrari"),        ("SAI", 55, "Ferrari"),
    ("HAM", 44, "Mercedes"),       ("RUS", 63, "Mercedes"),
    ("ALO", 14, "Aston Martin"),   ("STR", 18, "Aston Martin"),
    ("GAS", 10, "Alpine"),         ("OCO", 31, "Alpine"),
    ("ALB", 23, "Williams"),       ("SAR", 2, "Williams"),
    ("TSU", 22, "RB"),             ("RIC", 3, "RB"),
    ("HUL", 27, "Haas"),           ("MAG", 20, "Haas"),
    ("BOT", 77, "Kick Sauber"),    ("ZHO", 24, "Kick Sauber"),
]

# Final classification (finishing order), top to bottom.
_FINISH = ["PIA", "NOR", "HAM", "LEC", "VER", "RUS", "SAI", "PER", "ALO", "STR",
           "GAS", "OCO", "ALB", "TSU", "RIC", "HUL", "MAG", "SAR", "BOT", "ZHO"]

# Drivers who ran a two-stop (the rest one-stop) — a deliberate front-and-back mix.
_TWO_STOP = {"NOR", "VER", "SAI", "PER", "RIC", "ZHO"}

# Car pace deltas (seconds/lap) by team — Red Bull/McLaren quickest.
_TEAM_PACE = {
    "Red Bull Racing": 0.00, "McLaren": 0.05, "Ferrari": 0.20, "Mercedes": 0.25,
    "Aston Martin": 0.75, "Alpine": 1.05, "Williams": 1.10, "RB": 0.95,
    "Haas": 1.00, "Kick Sauber": 1.25,
}

_BASE_LAP = 80.0           # clean-air base lap (s)
_FUEL_PER_LAP = 0.055      # lap-time gained per lap as fuel burns off (s)
_COMPOUND_OFFSET = {"SOFT": -0.45, "MEDIUM": 0.0, "HARD": 0.35}
_DEG_RATE = {"SOFT": 0.090, "MEDIUM": 0.055, "HARD": 0.035}  # s per lap of tyre life
_PIT_LOSS = 20.0           # added to the in-lap (pit stop time loss, s)
_OUT_LAP = 1.8             # added to the out-lap (cold tyres, s)
_LAP1 = 3.0                # standing start penalty on lap 1


def _build_stints(rng: np.random.Generator, code: str) -> list[tuple[str, int]]:
    """Return [(compound, stint_length), ...] summing to TOTAL_LAPS."""
    if code in _TWO_STOP:
        compounds = _pick(rng, [
            ("SOFT", "MEDIUM", "HARD"), ("MEDIUM", "HARD", "SOFT"),
            ("SOFT", "MEDIUM", "MEDIUM"), ("MEDIUM", "MEDIUM", "HARD")])
        pit1 = int(rng.integers(14, 25))
        pit2 = pit1 + int(rng.integers(20, 30))
        pit2 = min(pit2, TOTAL_LAPS - 8)
        return [(compounds[0], pit1), (compounds[1], pit2 - pit1),
                (compounds[2], TOTAL_LAPS - pit2)]
    # one-stop
    compounds = _pick(rng, [("MEDIUM", "HARD"), ("SOFT", "HARD"), ("HARD", "MEDIUM")])
    pit1 = int(rng.integers(26, 41))
    return [(compounds[0], pit1), (compounds[1], TOTAL_LAPS - pit1)]


def _pick(rng: np.random.Generator, options: list):
    return options[int(rng.integers(0, len(options)))]


def get_laps(seed: int = 42) -> pd.DataFrame:
    """Generate the dummy laps DataFrame (FastF1 ``session.laps`` schema)."""
    rng = np.random.default_rng(seed)
    pos_by_code = {code: i + 1 for i, code in enumerate(_FINISH)}
    rows: list[dict] = []

    for code, number, team in _GRID:
        stints = _build_stints(rng, code)
        car = _TEAM_PACE[team] + float(rng.normal(0, 0.05))
        lap = 0
        cum = 0.0
        n_stints = len(stints)
        for stint_idx, (compound, length) in enumerate(stints, start=1):
            for life in range(1, length + 1):
                lap += 1
                is_out = stint_idx > 1 and life == 1
                is_in = stint_idx < n_stints and life == length
                lt = (_BASE_LAP + car
                      + (TOTAL_LAPS - lap) * _FUEL_PER_LAP
                      + _COMPOUND_OFFSET[compound]
                      + _DEG_RATE[compound] * life
                      + float(rng.normal(0, 0.15)))
                if lap == 1:
                    lt += _LAP1
                if is_out:
                    lt += _OUT_LAP
                if is_in:
                    lt += _PIT_LOSS
                cum += lt
                rows.append({
                    "Driver": code,
                    "DriverNumber": number,
                    "Team": team,
                    "LapNumber": lap,
                    "Stint": stint_idx,
                    "Compound": compound,
                    "TyreLife": life,
                    "FreshTyre": life == 1,
                    "LapTime": pd.to_timedelta(lt, unit="s"),
                    "Time": pd.to_timedelta(cum, unit="s"),
                    "Position": pos_by_code[code],
                    "PitInTime": pd.to_timedelta(cum, unit="s") if is_in else pd.NaT,
                    "PitOutTime": pd.to_timedelta(cum, unit="s") if is_out else pd.NaT,
                })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    laps = get_laps()
    print(laps.head(12).to_string())
    print(f"\n{len(laps)} laps · {laps.Driver.nunique()} drivers · "
          f"{(laps.groupby('Driver').Stint.max() == 3).sum()} two-stoppers")
