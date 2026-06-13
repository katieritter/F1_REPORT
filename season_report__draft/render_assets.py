"""Regenerate all chart images for the season report.

Uses real 2025 data from data/season_2025_laps.parquet when present (build it
with `python -m src.season_etl --year 2025`), else falls back to the synthetic
season_data generator. Pit data uses the real pits parquet if present, else
synthetic stationary times derived from the (real or dummy) pit-in events.

    python season_report__draft/render_assets.py
Writes PNGs into season_report__draft/assets/.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import analysis, charts, season_data  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(exist_ok=True)
DATA = ROOT / "data"
LAPS_PARQUET = DATA / "season_2025_laps.parquet"
PITS_PARQUET = DATA / "season_2025_pits.parquet"


def main() -> None:
    if LAPS_PARQUET.exists():
        laps = pd.read_parquet(LAPS_PARQUET)
        print(f"[real 2025 data] {laps.shape}, {laps['Round'].nunique()} rounds")
    else:
        laps = season_data.get_season_laps()
        print("[synthetic data]")

    # Wet/drying races make tyre & strategy aggregates meaningless -> drop them
    # season-wide (see knowledge_base/wet-races-and-tyre-data.md).
    wet = analysis.wet_rounds(laps)
    dry = laps[~laps["Round"].isin(wet)] if wet else laps
    print("excluded wet rounds:", wet, "| dry rounds:", dry["Round"].nunique())

    q = analysis.add_fuel_correction_season(analysis.pick_quicklaps_season(dry))

    deg = analysis.team_degradation(q)
    charts.team_degradation_ranking(
        deg, ASSETS / "team_degradation.png", short_names=season_data.TEAM_SHORT)

    circ = analysis.circuit_degradation(q)  # q is already dry-only
    charts.circuit_degradation_heatmap(circ, ASSETS / "circuit_degradation.png")

    usage = analysis.compound_usage(dry)
    charts.compound_usage_bars(
        usage, ASSETS / "compound_usage.png", short_names=season_data.TEAM_SHORT)

    agg = analysis.strategy_aggression(dry)
    charts.strategy_aggression_quadrant(
        agg, ASSETS / "strategy_aggression.png", short_names=season_data.TEAM_SHORT)

    stops = analysis.stops_distribution(dry)
    charts.stops_distribution_bars(stops, ASSETS / "stops_distribution.png")

    if PITS_PARQUET.exists():
        pits = pd.read_parquet(PITS_PARQUET)   # real OpenF1 pit-lane durations
        print("[real pit data]")
    else:
        pits = season_data.get_pit_stops(dry)  # synthetic until OpenF1 reopens
        print("[synthetic pit data — OpenF1 locked]")
    charts.pit_performance(
        pits, ASSETS / "pit_performance.png", short_names=season_data.TEAM_SHORT)

    print(deg.assign(DegRate=deg["DegRate"].map("+{:.3f}".format)).to_string(index=False))
    print("\nCompound usage (% of laps):")
    print((usage * 100).round(1).to_string())
    print("\nStrategy aggression (avg stops, soft %):")
    print(agg.round(2).sort_values("AvgStops", ascending=False).to_string())
    print("\nCircuit degradation (most -> least punishing):")
    print(circ.round(3).to_string())
    print(f"\nRendered assets into {ASSETS}")


if __name__ == "__main__":
    main()
