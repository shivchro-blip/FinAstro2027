"""Render the 2027 calendar: JSON master, generated HTML, CSV.

The verdict layer produces one row per rule, instrument and venue civil day. This
turns those into a calendar a reader can use, in the display format the project
specified:

    Date - Time IST | Time ET (EDT/EST) | Event | Vedic interpretation |
    Financial-market theme | Confidence/risk label

Three things this module is careful about, because each is a place a calendar
quietly lies:

* **Tagged uncertainty.** Every row carries its axes pair, its derived tier, its
  claim tag, its confidence and its flags. A row rendered without those would read
  as a prediction rather than as a condition with a provenance.
* **The dual date.** When the Eastern civil date differs from the IST one the row
  shows both, with the marker, and the SHIFT IS ALWAYS ZERO OR MINUS ONE --
  Eastern is never ahead of IST. Window ends are converted independently, so a
  window spanning a DST change shows two different Eastern offsets.
* **The epistemic apparatus is visible, not buried.** The HTML carries the
  certainty grades and both C grounds, the claim tags, all 33 blocked sections
  with what each waits for, the source defects found, and the standing statement
  that this is a speculative interpretive framework and not investment advice.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import html
import json
import pathlib

from .config import CONF
from .timezones import ET, IST, SHIFT_MARK, stamp
from .verdicts import INSTRUMENTS, build_verdicts

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
YEAR = CONF["year"]

OUT_JSON = BUILD / "calendar_2027.json"
OUT_HTML = BUILD / "calendar_2027.html"
OUT_CSV = BUILD / "calendar_2027.csv"

#: Carried into every output and rendered at the top of the HTML. The project's
#: own framing, stated once rather than left to be inferred from the column
#: names.
DISCLAIMER = (
    "Financial astrology is a speculative interpretive framework. The dates and "
    "conditions in this calendar are computed from an ephemeris and ported from "
    "a 2026 source document; the interpretations are that source's claims, "
    "carried verbatim or absent. Nothing here is a forecast, a prediction, or "
    "investment advice, and no confidence has been raised above `untested` for "
    "any row.")


def _sector_of(instrument: str) -> str:
    return INSTRUMENTS[instrument]["label"]


def render_rows(verdicts) -> list[dict]:
    """One display row per verdict, in the specified column order."""
    rows = []
    for v in verdicts:
        st = stamp(v.start_utc) if v.start_utc else None
        rows.append({
            "date": v.civil_date.strftime("%d-%b-%Y"),
            "date_ist": st.ist_date if st else None,
            "date_et": st.et_date if st else None,
            "day_shift": st.day_shift if st else 0,
            "time_ist": f"{st.ist_time} IST" if st else None,
            "time_et": f"{st.et_time} {st.et_abbr}" if st else None,
            "et_offset": st.et_offset if st else None,
            "dual_date": bool(st and st.day_shift),
            "instrument": v.instrument,
            "instrument_label": _sector_of(v.instrument),
            "venue": v.venue,
            "event": v.rule_id,
            "event_section": v.provenance,
            "vedic_interpretation": v.verdict_text,
            "interpretation_basis": v.significance,
            "financial_theme": f"{_sector_of(v.instrument)} - {v.rule_id.split('_', 1)[-1].replace('_', ' ')}",
            "confidence": v.confidence,
            "claim_tag": v.claim_tag,
            "evidence_source": v.evidence_source,
            "construction": v.construction,
            "tier": v.tier,
            "source_probability": v.source_probability,
            "source_probability_disputed": v.source_probability_disputed,
            "crude_path": v.crude_path,
            "flags": v.flags,
        })
    return rows


# --------------------------------------------------------------------- JSON

def write_json(rows: list[dict], verdicts) -> pathlib.Path:
    counts = collections.Counter(r["instrument"] for r in rows)
    tiers = collections.Counter(r["tier"] for r in rows)
    doc = {
        "meta": {
            "year": YEAR,
            "generated_by": "finastro/render.py",
            "records": len(rows),
            "rows_with_verdict": sum(1 for r in rows
                                     if r["vedic_interpretation"]),
            "rows_without_verdict": sum(1 for r in rows
                                        if not r["vedic_interpretation"]),
            "by_instrument": dict(sorted(counts.items())),
            "by_tier": {str(k): v for k, v in sorted(tiers.items(),
                                                     key=lambda x: str(x[0]))},
            "confidence": dict(collections.Counter(r["confidence"]
                                                   for r in rows)),
            "timezones": {"primary": CONF["display"]["primary_tz"],
                          "secondary": CONF["display"]["secondary_tz"]},
            "source_astronomy": {
                "path": "build/astronomy_2027.json",
                "sha256": __import__("hashlib").sha256(
                    (BUILD / "astronomy_2027.json").read_bytes()
                ).hexdigest(),
            },
            "disclaimer": DISCLAIMER,
        },
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    return OUT_JSON


# ---------------------------------------------------------------------- CSV

CSV_COLS = ["date", "date_ist", "date_et", "day_shift", "time_ist", "time_et",
            "et_offset", "instrument", "instrument_label", "venue", "event",
            "event_section", "vedic_interpretation", "interpretation_basis",
            "financial_theme", "confidence", "claim_tag", "evidence_source",
            "construction", "tier", "source_probability",
            "source_probability_disputed", "crude_path", "flags"]


def write_csv(rows: list[dict]) -> pathlib.Path:
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = dict(r)
            out["source_probability"] = (
                "|".join(r["source_probability"])
                if r["source_probability"] else "")
            out["flags"] = "|".join(r["flags"])
            w.writerow(out)
    return OUT_CSV


def main() -> int:
    """Render all three artifacts and print the counts."""
    verdicts = build_verdicts()
    rows = render_rows(verdicts)
    j = write_json(rows, verdicts)
    c = write_csv(rows)
    from .html_calendar import write_html
    h = write_html(rows, verdicts)
    print(f"{len(rows)} rows -> {j.relative_to(ROOT)}")
    print(f"{len(rows)} rows -> {c.relative_to(ROOT)}")
    print(f"{len(rows)} rows -> {h.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

