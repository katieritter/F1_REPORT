"""Chart functions for the report. Each takes a FastF1-schema ``laps`` DataFrame
and writes a 300 DPI image, styled via ``src/theme.py`` to match the HTML.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import analysis, theme


def strategy_gantt(laps: pd.DataFrame, save_path: str | Path,
                   total_laps: int | None = None) -> None:
    """Horizontal stacked-bar strategy chart: one row per driver (finishing
    order, P1 at top), each stint a bar coloured by tyre compound, width = laps.
    """
    theme.apply_light_theme()
    total_laps = total_laps or int(laps["LapNumber"].max())

    # Finishing order (P1 first).
    order = (laps.groupby("Driver")["Position"].first()
             .sort_values().index.tolist())

    fig, ax = plt.subplots(figsize=(11.0, 5.4))

    for i, drv in enumerate(order):
        d = laps[laps["Driver"] == drv].sort_values("LapNumber")
        for _, stint in d.groupby("Stint"):
            compound = stint["Compound"].iloc[0]
            start = stint["LapNumber"].min() - 1
            length = len(stint)
            ax.barh(i, length, left=start, height=0.62,
                    color=theme.compound_color(compound),
                    edgecolor=theme.PAGE_BG, linewidth=1.0, zorder=3)

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontfamily=theme.MONO_FONT, fontsize=8.5)
    ax.invert_yaxis()  # P1 at the top
    ax.set_xlim(0, total_laps)
    ax.set_xlabel("LAP", fontfamily=theme.MONO_FONT, fontsize=9,
                  labelpad=8, color=theme.INK_MUTED)
    ax.tick_params(axis="x", labelsize=8.5)
    for lbl in ax.get_xticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)

    ax.grid(axis="x", zorder=0)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.margins(y=0.01)

    fig.savefig(save_path)
    plt.close(fig)


def _deg_panel(ax, q, value_col, title):
    """Draw one degradation panel: light scatter + bold trend line per compound."""
    for compound in analysis.DRY_COMPOUNDS:
        d = q[q["Compound"] == compound]
        if len(d) < 5:
            continue
        col = theme.compound_color(compound)
        ax.scatter(d["TyreLife"], d[value_col], s=7, color=col, alpha=0.22, zorder=2)
        xs = np.linspace(d["TyreLife"].min(), d["TyreLife"].max(), 50)
        m, b = np.polyfit(d["TyreLife"], d[value_col], 1)
        ax.plot(xs, m * xs + b, color=col, lw=2.4, zorder=3, label=compound)
    ax.set_title(title, fontfamily=theme.MONO_FONT, fontsize=9.5,
                 color=theme.INK_MUTED, loc="left", pad=10)
    ax.set_xlabel("TYRE LIFE (laps)", fontfamily=theme.MONO_FONT, fontsize=8.5,
                  color=theme.INK_MUTED)
    for lbl in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)


def degradation_curves(laps: pd.DataFrame, save_path: str | Path,
                       total_laps: int) -> None:
    """Two panels: raw lap time vs tyre life (confounded by fuel burn-off) and
    fuel-corrected lap time vs tyre life (true degradation), per compound."""
    theme.apply_light_theme()
    q = analysis.add_fuel_correction(analysis.pick_quicklaps(laps), total_laps)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6))
    _deg_panel(ax1, q, "LapTimeSeconds", "RAW LAP TIME")
    _deg_panel(ax2, q, "FuelCorrectedSeconds", "FUEL-CORRECTED")
    ax1.set_ylabel("LAP TIME (s)", fontfamily=theme.MONO_FONT, fontsize=8.5,
                   color=theme.INK_MUTED)
    ax2.legend(loc="upper left", fontsize=8.5, title="COMPOUND")
    ax2.get_legend().get_title().set_fontsize(8)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


_STOP_COLORS = {1: "#a7c1d9", 2: "#ef8a2b", 3: "#c4271c"}


def stops_distribution_bars(shares: pd.DataFrame, save_path: str | Path) -> None:
    """Vertical stacked bars: % of the field on each stop count, per circuit,
    circuits ordered by 2-stop share (most multi-stop first)."""
    theme.apply_light_theme()
    circuits = list(shares.index)
    stop_counts = sorted(shares.columns)
    x = range(len(circuits))

    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    bottom = [0.0] * len(circuits)
    for s in stop_counts:
        vals = shares[s].values
        ax.bar(x, vals, bottom=bottom, color=_STOP_COLORS.get(s, "#888"),
               edgecolor=theme.PAGE_BG, linewidth=0.6, zorder=3,
               label=f"{s}-STOP")
        bottom = [a + b for a, b in zip(bottom, vals)]

    ax.set_xticks(list(x))
    ax.set_xticklabels(circuits, rotation=45, ha="right",
                       fontfamily=theme.MONO_FONT, fontsize=7)
    ax.set_ylim(0, 100)
    ax.set_ylabel("SHARE OF FIELD (%)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    for lbl in ax.get_yticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    ax.grid(axis="y", zorder=0)
    ax.grid(axis="x", visible=False)
    ax.margins(x=0.01)
    leg = ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01),
                    ncol=len(stop_counts), fontsize=8.5, handlelength=1.1)
    for t in leg.get_texts():
        t.set_fontfamily(theme.MONO_FONT)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def strategy_aggression_quadrant(df: pd.DataFrame, save_path: str | Path,
                                 short_names: dict[str, str] | None = None) -> None:
    """Scatter of teams by avg stops/race (x) vs soft usage % (y), split into
    quadrants by the field medians. Top-right = most aggressive."""
    theme.apply_light_theme()
    x = df["AvgStops"]
    y = df["SoftShare"]
    xm, ym = x.median(), y.median()

    fig, ax = plt.subplots(figsize=(7.8, 5.6))
    ax.axvline(xm, color=theme.HAIRLINE, lw=1.0, ls="--", zorder=1)
    ax.axhline(ym, color=theme.HAIRLINE, lw=1.0, ls="--", zorder=1)

    for team, row in df.iterrows():
        col = theme.team_color(team)
        ax.scatter(row["AvgStops"], row["SoftShare"], s=120, color=col,
                   edgecolor=theme.PAGE_BG, linewidth=1.2, zorder=3)
        ax.annotate((short_names or {}).get(team, team),
                    (row["AvgStops"], row["SoftShare"]),
                    xytext=(7, 0), textcoords="offset points", va="center",
                    fontsize=8, fontfamily=theme.MONO_FONT, color=theme.INK)

    # Quadrant corner labels.
    xlo, xhi = ax.get_xlim()
    ylo, yhi = ax.get_ylim()
    pad = 0.01
    corners = [
        (xhi, yhi, "FULL ATTACK", "right", "top"),
        (xlo, ylo, "CONSERVATIVE", "left", "bottom"),
        (xlo, yhi, "SOFT-LED", "left", "top"),
        (xhi, ylo, "FORCED STOPPERS", "right", "bottom"),
    ]
    for cx, cy, label, ha, va in corners:
        ax.text(cx - pad if ha == "right" else cx + pad,
                cy - pad if va == "top" else cy + pad,
                label, ha=ha, va=va, fontsize=7.5, fontfamily=theme.MONO_FONT,
                color=theme.INK_MUTED, alpha=0.8,
                transform=ax.transData)

    ax.set_xlabel("AVERAGE STOPS PER RACE", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    ax.set_ylabel("SOFT USAGE (% of laps)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    for lbl in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def compound_usage_bars(shares: pd.DataFrame, save_path: str | Path,
                        short_names: dict[str, str] | None = None) -> None:
    """Stacked horizontal bars of each team's share of race laps per compound.
    Teams ordered most→least soft-heavy (aggressive at the top)."""
    theme.apply_light_theme()
    teams = list(shares.index)
    labels = [(short_names or {}).get(t, t) for t in teams]
    compounds = [c for c in ("SOFT", "MEDIUM", "HARD") if c in shares.columns]

    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    y = range(len(teams))
    left = [0.0] * len(teams)
    for comp in compounds:
        vals = shares[comp].values * 100
        ax.barh(y, vals, left=left, color=theme.compound_color(comp),
                edgecolor=theme.PAGE_BG, linewidth=1.0, zorder=3, height=0.72,
                label=comp)
        for i, (v, l) in enumerate(zip(vals, left)):
            if v >= 9:
                ax.text(l + v / 2, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=7.5, fontfamily=theme.MONO_FONT,
                        color=theme.INK if comp in ("MEDIUM", "HARD") else "white")
        left = [a + b for a, b in zip(left, vals)]

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontfamily=theme.MONO_FONT, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("SHARE OF RACE LAPS (%)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    for lbl in ax.get_xticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    ax.grid(axis="x", zorder=0)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    leg = ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3,
                    fontsize=8.5, handlelength=1.1)
    for t in leg.get_texts():
        t.set_fontfamily(theme.MONO_FONT)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def circuit_degradation_heatmap(mat: pd.DataFrame, save_path: str | Path) -> None:
    """Heatmap of degradation rate per circuit × compound (track classification).
    Rows = circuits (most→least punishing), columns = compounds, cells = s/lap."""
    theme.apply_light_theme()
    circuits = list(mat.index)
    comps = list(mat.columns)
    data = mat.values

    fig, ax = plt.subplots(figsize=(4.8, 7.8))
    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#eeeeee")  # empty cells (compound barely used) shown neutral grey
    masked = np.ma.masked_invalid(data)
    im = ax.imshow(masked, aspect="auto", cmap=cmap)

    ax.set_xticks(range(len(comps)))
    ax.set_xticklabels(comps, fontfamily=theme.MONO_FONT, fontsize=8.5)
    ax.set_yticks(range(len(circuits)))
    ax.set_yticklabels(circuits, fontfamily=theme.MONO_FONT, fontsize=8)
    ax.tick_params(length=0)
    ax.xaxis.set_ticks_position("top")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)

    vmin, vmax = np.nanmin(data), np.nanmax(data)
    for i in range(len(circuits)):
        for j in range(len(comps)):
            v = data[i, j]
            if np.isnan(v):
                ax.text(j, i, "—", ha="center", va="center", fontsize=8,
                        fontfamily=theme.MONO_FONT, color=theme.INK_MUTED)
                continue
            norm = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.0
            ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=7,
                    fontfamily=theme.MONO_FONT,
                    color="white" if norm > 0.6 else theme.INK)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, orientation="vertical")
    cbar.ax.tick_params(labelsize=7, length=0)
    for lbl in cbar.ax.get_yticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
    cbar.outline.set_visible(False)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def pit_performance(stops: pd.DataFrame, save_path: str | Path,
                    short_names: dict[str, str] | None = None) -> None:
    """Horizontal box plot of pit-stop stationary times per team, ordered by
    median (fastest crew at top). Box width = consistency; long tail = fumbles."""
    theme.apply_light_theme()
    order = (stops.groupby("Team")["Stationary"].median()
             .sort_values().index.tolist())
    data = [stops.loc[stops["Team"] == t, "Stationary"].values for t in order]
    labels = [(short_names or {}).get(t, t) for t in order]

    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    positions = list(range(len(order), 0, -1))  # first (fastest) at top
    bp = ax.boxplot(data, vert=False, positions=positions, patch_artist=True,
                    widths=0.62, showfliers=True,
                    medianprops=dict(color=theme.INK, linewidth=1.6),
                    flierprops=dict(marker="o", markersize=3,
                                    markerfacecolor=theme.HAIRLINE,
                                    markeredgecolor=theme.HAIRLINE))
    for patch, t in zip(bp["boxes"], order):
        patch.set_facecolor(theme.team_color(t))
        patch.set_alpha(0.85)
        patch.set_edgecolor(theme.INK)

    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontfamily=theme.MONO_FONT, fontsize=9)
    ax.set_xlabel("PIT-STOP STATIONARY TIME (s)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    for lbl in ax.get_xticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    ax.grid(axis="x", zorder=0)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def team_degradation_ranking(deg_df: pd.DataFrame, save_path: str | Path,
                             short_names: dict[str, str] | None = None) -> None:
    """Horizontal bar ranking of teams by season degradation rate (s/lap),
    best (lowest, kindest to tyres) at the top. ``deg_df`` has Team, DegRate."""
    theme.apply_light_theme()
    d = deg_df.sort_values("DegRate", ascending=True).reset_index(drop=True)
    labels = [(short_names or {}).get(t, t) for t in d["Team"]]
    colors = [theme.team_color(t) for t in d["Team"]]

    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    y = range(len(d))
    ax.barh(y, d["DegRate"], color=colors, edgecolor=theme.PAGE_BG,
            linewidth=1.0, zorder=3, height=0.72)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontfamily=theme.MONO_FONT, fontsize=9)
    ax.invert_yaxis()  # best (lowest deg) at top

    for i, v in enumerate(d["DegRate"]):
        ax.text(v + d["DegRate"].max() * 0.012, i, f"+{v:.3f}",
                va="center", ha="left", fontsize=8.5, fontfamily=theme.MONO_FONT,
                color=theme.INK)

    ax.set_xlabel("DEGRADATION RATE (s/lap, fuel-corrected)",
                  fontfamily=theme.MONO_FONT, fontsize=8.5, color=theme.INK_MUTED)
    ax.set_xlim(0, d["DegRate"].max() * 1.16)
    for lbl in ax.get_xticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    ax.grid(axis="x", zorder=0)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def _driver_stints(laps: pd.DataFrame, drv: str) -> list[tuple[str, int]]:
    d = laps[laps["Driver"] == drv].sort_values("LapNumber")
    return [(s["Compound"].iloc[0], len(s)) for _, s in d.groupby("Stint")]


def pair_strategy(laps: pd.DataFrame, drivers: list[str], save_path: str | Path,
                  total_laps: int) -> None:
    """Mini strategy chart for two drivers plus a field-median one-stop reference."""
    theme.apply_light_theme()

    # Field-median one-stop reference (median first-stop lap among one-stoppers).
    one_stop = [d for d in laps["Driver"].unique()
                if laps[laps["Driver"] == d]["Stint"].max() == 2]
    pit_laps_first = [analysis.pit_laps(laps, d)[0] for d in one_stop
                      if analysis.pit_laps(laps, d)]
    med_pit = int(np.median(pit_laps_first))
    field = [("MEDIUM", med_pit), ("HARD", total_laps - med_pit)]

    rows = [("FIELD MED.", field, True)] + [(d, _driver_stints(laps, d), False)
                                            for d in drivers]

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for i, (label, stints, is_ref) in enumerate(rows):
        start = 0
        for compound, length in stints:
            ax.barh(i, length, left=start, height=0.6,
                    color=theme.compound_color(compound),
                    edgecolor=theme.PAGE_BG, linewidth=1.0,
                    alpha=0.4 if is_ref else 1.0, zorder=3)
            start += length

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontfamily=theme.MONO_FONT, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, total_laps)
    ax.set_xlabel("LAP", fontfamily=theme.MONO_FONT, fontsize=8.5, color=theme.INK_MUTED)
    for lbl in ax.get_xticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    ax.grid(axis="x", zorder=0)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def pair_pace(laps: pd.DataFrame, drivers: list[str], save_path: str | Path,
              total_laps: int) -> None:
    """Fuel-corrected pace vs tyre life for two drivers — a tyre-management
    comparison (flatter trend = better degradation control)."""
    theme.apply_light_theme()
    q = analysis.add_fuel_correction(analysis.pick_quicklaps(laps), total_laps)
    palette = [theme.ACCENT, theme.INK]

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for drv, col in zip(drivers, palette):
        d = q[q["Driver"] == drv]
        if len(d) < 5:
            continue
        ax.scatter(d["TyreLife"], d["FuelCorrectedSeconds"], s=9, color=col,
                   alpha=0.30, zorder=2)
        xs = np.linspace(d["TyreLife"].min(), d["TyreLife"].max(), 50)
        m, b = np.polyfit(d["TyreLife"], d["FuelCorrectedSeconds"], 1)
        ax.plot(xs, m * xs + b, color=col, lw=2.4, zorder=3,
                label=f"{drv}  (+{m:.3f} s/lap)")

    ax.set_xlabel("TYRE LIFE (laps)", fontfamily=theme.MONO_FONT, fontsize=8.5,
                  color=theme.INK_MUTED)
    ax.set_ylabel("FUEL-CORR. LAP TIME (s)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    for lbl in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    leg = ax.legend(loc="upper left", fontsize=8.5)
    for t in leg.get_texts():
        t.set_fontfamily(theme.MONO_FONT)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def undercut_gap(laps: pd.DataFrame, save_path: str | Path,
                 ahead: str, behind: str) -> None:
    """Gap (seconds) between two drivers across the race, with pit laps marked.
    ``ahead`` finished in front; the chart shows whether the undercut decided it.
    Positive gap = ``behind`` trails ``ahead``; crossing zero = a lead change.
    """
    theme.apply_light_theme()
    gap = analysis.driver_gap(laps, ahead, behind)
    team_a = laps.loc[laps["Driver"] == ahead, "Team"].iloc[0]
    team_b = laps.loc[laps["Driver"] == behind, "Team"].iloc[0]
    col_a = theme.team_color(team_a)
    col_b = theme.team_color(team_b)

    fig, ax = plt.subplots(figsize=(11.0, 4.8))

    x, y = gap["LapNumber"].values, gap["Gap"].values
    ax.fill_between(x, y, 0, where=(y >= 0), color=col_a, alpha=0.10, zorder=1)
    ax.fill_between(x, y, 0, where=(y < 0), color=col_b, alpha=0.10, zorder=1)
    ax.plot(x, y, color=theme.INK, lw=2.0, zorder=3)
    ax.axhline(0, color=theme.INK_MUTED, lw=1.0, ls="--", zorder=2)

    # Pit-stop markers, coloured by the pitting driver's team.
    for lap in analysis.pit_laps(laps, ahead):
        ax.axvline(lap, color=col_a, lw=1.6, zorder=2)
        ax.text(lap + 0.4, ax.get_ylim()[1], f"{ahead} PITS",
                rotation=90, va="top", ha="left", fontsize=8,
                fontfamily=theme.MONO_FONT, color=col_a)
    for lap in analysis.pit_laps(laps, behind):
        ax.axvline(lap, color=col_b, lw=1.6, zorder=2)
        ax.text(lap + 0.4, ax.get_ylim()[1], f"{behind} PITS",
                rotation=90, va="top", ha="left", fontsize=8,
                fontfamily=theme.MONO_FONT, color=col_b)

    ax.set_xlabel("LAP", fontfamily=theme.MONO_FONT, fontsize=9, color=theme.INK_MUTED)
    ax.set_ylabel(f"GAP TO {ahead} (s)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    ax.set_xlim(x.min(), x.max())
    for lbl in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)

    # Annotate which side means what.
    ax.text(0.012, 0.96, f"{behind} BEHIND", transform=ax.transAxes,
            fontsize=8, fontfamily=theme.MONO_FONT, color=col_a, va="top")
    ax.text(0.012, 0.04, f"{behind} AHEAD", transform=ax.transAxes,
            fontsize=8, fontfamily=theme.MONO_FONT, color=col_b, va="bottom")

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def compound_pace_box(laps: pd.DataFrame, save_path: str | Path,
                      total_laps: int) -> None:
    """Box plot of fuel-corrected quicklap times per compound."""
    theme.apply_light_theme()
    q = analysis.add_fuel_correction(analysis.pick_quicklaps(laps), total_laps)

    compounds = [c for c in analysis.DRY_COMPOUNDS
                 if (q["Compound"] == c).sum() >= 5]
    data = [q.loc[q["Compound"] == c, "FuelCorrectedSeconds"] for c in compounds]

    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    bp = ax.boxplot(data, patch_artist=True, widths=0.55,
                    medianprops=dict(color=theme.INK, linewidth=1.6),
                    flierprops=dict(marker="o", markersize=3,
                                    markerfacecolor=theme.HAIRLINE,
                                    markeredgecolor=theme.HAIRLINE))
    for patch, c in zip(bp["boxes"], compounds):
        patch.set_facecolor(theme.compound_color(c))
        patch.set_alpha(0.85)
        patch.set_edgecolor(theme.INK)
    ax.set_xticklabels(compounds, fontfamily=theme.MONO_FONT, fontsize=9)
    ax.set_ylabel("FUEL-CORRECTED LAP TIME (s)", fontfamily=theme.MONO_FONT,
                  fontsize=8.5, color=theme.INK_MUTED)
    for lbl in ax.get_yticklabels():
        lbl.set_fontfamily(theme.MONO_FONT)
        lbl.set_fontsize(8)
    ax.grid(axis="x", visible=False)

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
