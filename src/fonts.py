"""Register the report's web fonts with matplotlib so chart typography matches
the HTML (Chakra Petch / IBM Plex Mono / IBM Plex Sans).

Fonts are downloaded once from the Google Fonts repo and cached in ``fonts/``.
If download fails (offline), charts fall back to matplotlib defaults gracefully.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import matplotlib.font_manager as fm

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "fonts"

_BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl"
_FONTS = {
    "IBMPlexMono-Regular.ttf":  f"{_BASE}/ibmplexmono/IBMPlexMono-Regular.ttf",
    "IBMPlexMono-SemiBold.ttf": f"{_BASE}/ibmplexmono/IBMPlexMono-SemiBold.ttf",
    "IBMPlexSans-Regular.ttf":  f"{_BASE}/ibmplexsans/IBMPlexSans-Regular.ttf",
    "ChakraPetch-Bold.ttf":     f"{_BASE}/chakrapetch/ChakraPetch-Bold.ttf",
}

_registered = False


def ensure_chart_fonts() -> set[str]:
    """Download (if needed), register, and return the set of available family names."""
    global _registered
    FONT_DIR.mkdir(exist_ok=True)
    for fname, url in _FONTS.items():
        fp = FONT_DIR / fname
        if not fp.exists():
            try:
                urllib.request.urlretrieve(url, fp)
            except Exception:
                continue  # offline / unavailable — skip, fall back later
        if not _registered:
            try:
                fm.fontManager.addfont(str(fp))
            except Exception:
                pass
    _registered = True
    return {f.name for f in fm.fontManager.ttflist}
