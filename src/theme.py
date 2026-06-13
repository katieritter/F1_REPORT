"""Shared visual theme for charts — keeps matplotlib output consistent with
the report's "pit-wall" HTML/CSS template (single_race_report_draft/styles/theme.css).

Call ``apply_light_theme()`` before plotting. Use ``compound_color()`` for tyre
compounds (FastF1-official) and ``TEAM_COLORS`` for driver comparisons.
"""
from __future__ import annotations

import matplotlib as mpl

from . import fonts

# --- Tyre compound colours (must match theme.css :root variables) ---
COMPOUND_COLORS: dict[str, str] = {
    "SOFT":   "#da291c",
    "MEDIUM": "#ffd12e",
    "HARD":   "#b4b4b4",
    "INTERMEDIATE": "#43b02a",
    "WET":    "#0067ad",
}

# --- Team colours (2024 grid) for driver comparisons ---
TEAM_COLORS: dict[str, str] = {
    "Red Bull Racing": "#3671C6",
    "McLaren":         "#FF8000",
    "Ferrari":         "#E8002D",
    "Mercedes":        "#27F4D2",
    "Aston Martin":    "#229971",
    "Alpine":          "#0093CC",
    "Williams":        "#64C4FF",
    "RB":              "#6692FF",
    "Haas":            "#B6BABD",
    "Kick Sauber":     "#52E252",
}

# --- Document palette echoed for chart elements ---
INK = "#0e1216"
INK_MUTED = "#5d6873"
HAIRLINE = "#c7ccd4"
ACCENT = "#e10600"
PAGE_BG = "#ffffff"

EXPORT_DPI = 300

# Resolved at apply time (with generic fallbacks if web fonts unavailable).
SANS_FONT = "DejaVu Sans"
MONO_FONT = "monospace"
DISPLAY_FONT = "DejaVu Sans"


def apply_light_theme() -> None:
    """Apply the light, print-friendly matplotlib rcParams + register fonts."""
    global SANS_FONT, MONO_FONT, DISPLAY_FONT
    available = fonts.ensure_chart_fonts()
    if "IBM Plex Sans" in available:
        SANS_FONT = "IBM Plex Sans"
    if "IBM Plex Mono" in available:
        MONO_FONT = "IBM Plex Mono"
    if "Chakra Petch" in available:
        DISPLAY_FONT = "Chakra Petch"

    mpl.rcParams.update({
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "savefig.facecolor": PAGE_BG,
        "savefig.dpi": EXPORT_DPI,
        "savefig.bbox": "tight",

        "font.family": "sans-serif",
        "font.sans-serif": [SANS_FONT, "Segoe UI", "Arial", "DejaVu Sans"],
        "font.size": 10,

        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,

        "axes.edgecolor": HAIRLINE,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": HAIRLINE,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.7,

        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    })


def compound_color(compound: str) -> str:
    """Return the official colour for a tyre compound, defaulting to grey."""
    return COMPOUND_COLORS.get(str(compound).upper(), "#999999")


def team_color(team: str) -> str:
    """Return a team's colour, defaulting to muted ink."""
    return TEAM_COLORS.get(team, INK_MUTED)
