"""Regenerate all chart images for the draft report from dummy data.

Run after changing chart code or dummy data:
    python single_race_report_draft/render_assets.py
Writes PNGs into single_race_report_draft/assets/.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import analysis, charts, dummy_data  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(exist_ok=True)


def main() -> None:
    laps = dummy_data.get_laps()
    n = dummy_data.TOTAL_LAPS

    charts.strategy_gantt(laps, ASSETS / "strategy_gantt.png", total_laps=n)
    charts.degradation_curves(laps, ASSETS / "degradation_curves.png", total_laps=n)
    charts.compound_pace_box(laps, ASSETS / "compound_pace_box.png", total_laps=n)
    charts.undercut_gap(laps, ASSETS / "undercut_gap.png", ahead="HAM", behind="LEC")

    # Cadillac proxy spotlight — Sauber pairing (Bottas is the real-world bridge).
    proxy = ["BOT", "ZHO"]
    charts.pair_strategy(laps, proxy, ASSETS / "proxy_strategy.png", total_laps=n)
    charts.pair_pace(laps, proxy, ASSETS / "proxy_pace.png", total_laps=n)

    # Gap at key laps for the page-7 narrative.
    g = analysis.driver_gap(laps, "HAM", "LEC").set_index("LapNumber")["Gap"]
    for lap in (27, 28, 38, 39, 70):
        print(f"  L{lap}: LEC gap to HAM = {g.loc[lap]:+.1f}s")

    # Proxy-driver degradation slopes for the page-8/9 commentary.
    q = analysis.add_fuel_correction(analysis.pick_quicklaps(laps), n)
    import numpy as np
    for drv in proxy:
        d = q[q["Driver"] == drv]
        m, _ = np.polyfit(d["TyreLife"], d["FuelCorrectedSeconds"], 1)
        print(f"  {drv} degradation: +{m:.3f} s/lap ({len(d)} quicklaps)")

    # Print the degradation summary so the page-5 table can use real numbers.
    q = analysis.add_fuel_correction(analysis.pick_quicklaps(laps), n)
    summary = analysis.degradation_summary(q)
    print(summary.to_string(index=False,
          formatters={"DegRate": "{:+.3f}".format,
                      "PaceAt5": "{:.3f}".format,
                      "PaceAdvVsHard": "{:+.3f}".format}))
    print(f"\nRendered assets into {ASSETS}")


if __name__ == "__main__":
    main()
