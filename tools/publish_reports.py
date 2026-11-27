"""Copy the two kept calendars (and the 2027 calendar .ics) into reports/.

    python tools/publish_reports.py

The user asked (27 Nov 2026) to keep only two HTML pages:
  * calendar_2026-11-24_to_2026-12-31_ET.html  - the complete calendar to the end of 2026 (tools/calendar_2026.py)
  * calendar_2027_NY_master.html               - the 2027 calendar in New York time (tools/build_pdf_calendar.py)
The base 2027 master build/calendar_2027.html (finastro.render) also stays, as tests/test_rule_layer.py reads it.
Every other report HTML is still written by its tool into build/pdfref/ during a refresh (the tools also write the
JSON the calendar reads), but those pages are git-ignored and not published. tools/refresh_all.py runs this last.
"""
from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "reports"
B = ROOT / "build" / "pdfref"
ICS = ["calendar_2027_NY_master.ics"]


def main():
    DEST.mkdir(exist_ok=True)
    keep = sorted(B.glob("calendar_2026-*_ET.html"))[-1:] + [B / "calendar_2027_NY_master.html"] + [B / f for f in ICS]
    for p in keep:
        if p.exists():
            shutil.copy2(p, DEST / p.name)
    names = {p.name for p in keep} | {"README.md"}
    for p in list(DEST.glob("*.html")) + list(DEST.glob("*.ics")):     # nothing else is published
        if p.name not in names:
            p.unlink()
    (DEST / "README.md").write_text(
        "# reports/\n\nReady-to-open calendars:\n\n"
        "* `calendar_2026-11-24_to_2026-12-31_ET.html`: the complete calendar from now to 31 Dec 2026 (S&P 500, Sensex, gold, silver; every layer, track record and checks).\n"
        "* `calendar_2027_NY_master.html`: the 2027 calendar in New York time (and `.ics`).\n\n"
        "Published by `tools/publish_reports.py` (run at the end of `tools/refresh_all.py`); do not edit these copies.\n", encoding="utf-8")
    print(f"published {sum(1 for _ in DEST.iterdir())} files to reports/")


if __name__ == "__main__":
    main()
