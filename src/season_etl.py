"""Real-data season loader — fetches a full F1 season from FastF1 (laps) and
OpenF1 (pit-lane durations) and returns the **same shapes** as the synthetic
``src/season_data.py``, so the charts/analysis read it unchanged.

Outputs are cached as parquet in ``data/`` to avoid re-downloading.

    python -m src.season_etl --year 2025            # build + cache laps (+ pits if available)
    python -m src.season_etl --year 2025 --refresh  # force re-fetch

OpenF1 note: during a *live* F1 session, OpenF1 restricts all access (including
past data) to authenticated users — ``fetch_season_pits`` then fails cleanly and
the laps parquet is still written. Retry pits once the live session has ended.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import fastf1
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
DATA = ROOT / "data"

# FastF1 2025 team strings -> keys used in theme.TEAM_COLORS / season_data.TEAM_SHORT.
TEAM_MAP = {
    "Haas F1 Team": "Haas",
    "Racing Bulls": "RB",
    # Identity for the rest (Red Bull Racing, McLaren, Ferrari, Mercedes,
    # Aston Martin, Alpine, Williams, Kick Sauber) — handled by .get(name, name).
}

# Columns the report's contract requires (must match season_data.get_season_laps()).
LAP_COLUMNS = [
    "Round", "Event", "Circuit", "RoundLaps", "Driver", "DriverNumber", "Team",
    "LapNumber", "Stint", "Compound", "TyreLife", "FreshTyre",
    "LapTime", "Time", "PitInTime", "PitOutTime",
]


def _norm_team(name: str) -> str:
    return TEAM_MAP.get(name, name)


def load_round_laps(year: int, rnd: int, event_name: str, circuit: str) -> pd.DataFrame:
    """Load one Race session's laps and shape them to the contract."""
    session = fastf1.get_session(year, rnd, "R")
    session.load(laps=True, telemetry=False, weather=False, messages=False)
    laps = session.laps.copy()
    laps["Round"] = rnd
    laps["Event"] = event_name
    laps["Circuit"] = circuit
    laps["RoundLaps"] = int(laps["LapNumber"].max())
    laps["Team"] = laps["Team"].map(_norm_team)
    # Keep only contract columns; drop laps with no compound/tyre age (unusable
    # for tyre analysis, e.g. anomalies) so downstream polyfits stay clean.
    laps = laps[[c for c in LAP_COLUMNS if c in laps.columns]]
    return laps.dropna(subset=["Compound", "TyreLife"])


def build_season_laps(year: int, rounds: list[int] | None = None) -> pd.DataFrame:
    """Fetch every Race in the season (or a subset) and concatenate to one frame."""
    CACHE.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE))
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    if rounds is not None:
        schedule = schedule[schedule["RoundNumber"].isin(rounds)]

    frames = []
    for _, ev in schedule.iterrows():
        rnd = int(ev["RoundNumber"])
        try:
            frames.append(load_round_laps(year, rnd, ev["EventName"], ev["Location"]))
            print(f"  R{rnd:>2} {ev['EventName']}: ok")
        except Exception as e:  # a missing/failed round shouldn't kill the season
            print(f"  R{rnd:>2} {ev['EventName']}: SKIPPED ({type(e).__name__}: {e})")
    return pd.concat(frames, ignore_index=True)


def fetch_season_pits(year: int) -> pd.DataFrame:
    """Pit-lane durations per stop from OpenF1, shaped to the pit contract
    (Team, Round, Driver, Stationary). Raises if OpenF1 access is restricted."""
    import requests

    UA = {"User-Agent": "f1-report/0.1"}

    def get(path: str, **params):
        r = requests.get(f"https://api.openf1.org/v1/{path}", params=params,
                         headers=UA, timeout=30)
        if r.status_code == 401:
            raise PermissionError(
                "OpenF1 access restricted (likely a live session in progress). "
                "Retry once the live session has ended, or use an API key.")
        r.raise_for_status()
        return r.json()

    sessions = get("sessions", year=year, session_name="Race")
    rows = []
    for s in sessions:
        sk = s["session_key"]
        drivers = {d["driver_number"]: _norm_team(d.get("team_name", ""))
                   for d in get("drivers", session_key=sk)}
        acro = {d["driver_number"]: d.get("name_acronym") for d in get("drivers", session_key=sk)}
        for p in get("pit", session_key=sk):
            if p.get("pit_duration") is None:
                continue
            rows.append({
                "Team": drivers.get(p["driver_number"], ""),
                "Round": s.get("meeting_key"),  # mapped to RoundNumber below if needed
                "Driver": acro.get(p["driver_number"]),
                "Stationary": p["pit_duration"],
            })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--rounds", type=int, nargs="*", default=None)
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    laps_path = DATA / f"season_{args.year}_laps.parquet"
    pits_path = DATA / f"season_{args.year}_pits.parquet"

    if args.refresh or not laps_path.exists():
        print(f"Building {args.year} laps from FastF1...")
        laps = build_season_laps(args.year, args.rounds)
        laps.to_parquet(laps_path)
        print(f"Wrote {laps_path}: {laps.shape}, {laps['Round'].nunique()} rounds")
    else:
        print(f"Laps cache exists: {laps_path}")

    if args.refresh or not pits_path.exists():
        try:
            print(f"Fetching {args.year} pit durations from OpenF1...")
            pits = fetch_season_pits(args.year)
            pits.to_parquet(pits_path)
            print(f"Wrote {pits_path}: {pits.shape}")
        except Exception as e:
            print(f"Pit fetch unavailable ({e}). Laps still cached; retry pits later.")


if __name__ == "__main__":
    main()
