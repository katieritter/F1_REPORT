"""Render the draft report HTML + CSS to a print-ready PDF via headless Chromium
(Playwright). Chromium's print engine gives the best CSS @page / print fidelity
and needs no system libraries on Windows (unlike WeasyPrint's GTK/Pango deps).

Usage:
    python single_race_report_draft/build.py
Produces single_race_report_draft/report.pdf
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
HTML_IN = HERE / "report.html"
PDF_OUT = HERE / "report.pdf"


def build() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # file:// URL so relative CSS/asset paths resolve; wait for web fonts.
        page.goto(HTML_IN.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(PDF_OUT),
            prefer_css_page_size=True,  # honour @page size/margins from print.css
            print_background=True,      # render background colours/cards
        )
        browser.close()
    print(f"Wrote {PDF_OUT}")


if __name__ == "__main__":
    build()
