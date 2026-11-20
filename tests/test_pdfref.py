"""Checks for the reference-PDF rule engine (finastro/pdfref).

Run:  python tests/test_pdfref.py    (needs build/astronomy_2026.json)

* the TA Vedha wheel is a consistent transcription and agrees with the 2026
  document's Vedha tables exactly where vedha.py says it does;
* the engine reproduces dated claims printed in the PDFs (KD p.94's 13
  Shani-Chandra windows to within 2 minutes; TA's Mercury-in-the-middle
  examples; KD's Saturn-Mars and Mercury-manifestation dates);
* every catalogue entry carries a page reference, a verdict and a method.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.pdfref import catalogue as C, vedha as V  # noqa: E402
from finastro.pdfref.engine import Grid, conjunction_instants, crossings, spans, utc  # noqa: E402
from finastro.rules.catalogue import B  # noqa: E402
from finastro.rules.vedha import WHEELS  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")
RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not ok else ""))


ALIAS = {"bharni": "Bharani", "kritika": "Krittika", "mrigshira": "Mrigashira", "mrigsira": "Mrigashira", "mrigsria": "Mrigashira",
         "purva falguni": "Purva Phalguni", "uttra falguni": "Uttara Phalguni", "mool": "Mula", "purva shada": "Purva Ashadha",
         "uttra shada": "Uttara Ashadha", "shravan": "Shravana", "sharvan": "Shravana", "dhanistha": "Dhanishta", "shatbisha": "Shatabhisha",
         "shatbhisha": "Shatabhisha", "purva bhadrapad": "Purva Bhadrapada", "purva bhadrpad": "Purva Bhadrapada",
         "uttra bhadrapad": "Uttara Bhadrapada", "uttra bhadrpad": "Uttara Bhadrapada", "hast": "Hasta", "vishaka": "Vishakha",
         "visaka": "Vishakha", "visahka": "Vishakha", "jyestha": "Jyeshtha"}


def n(x):
    x = x.strip()
    return ALIAS.get(x.lower(), x) if x else ""


def test_wheel():
    record("TA wheel has all 28 nakshatras (with Abhijit)", len(V.TA_WHEEL) == 28)
    record("TA wheel Front column is mutual", all(V.TA_WHEEL[V.TA_WHEEL[k][2]][2] == k for k in V.TA_WHEEL))
    members = all(t in V.TA_WHEEL[nk] for w in WHEELS.values() for (nk, _), t in w.items())
    record("Every 2026 wheel entry (vedha.py) is one of TA's three targets", members)
    bad = []
    tot = 0
    for b in range(131, 142):
        t = B(b).tables[0]
        h = list(t.headers)
        for row in t.rows:
            exp = V.cells_2026_labels(n(row[0]))
            for col in (V.F, V.L, V.R):
                for hh in h:
                    if hh.endswith(col):
                        v = n(row[h.index(hh)])
                        if v:
                            tot += 1
                            if v != exp[col]:
                                bad.append((b, n(row[0]), col, v, exp[col]))
    record("2026 B131-B141 cells agree with TA except the 10 listed exceptions",
           tot == 227 and sorted(bad) == sorted(V.EXCEPTIONS_2026), f"{tot} cells, {len(bad)} differ: {bad}")


def test_dates():
    g = Grid(utc(2025, 12, 1), utc(2027, 1, 31))
    kd94 = ["21-Jan-26 1:37", "17-Feb-26 9:06", "16-Mar-26 18:15", "13-Apr-26 3:45", "10-May-26 12:13", "06-Jun-26 19:05", "04-Jul-26 0:49",
            "31-Jul-26 6:39", "27-Aug-26 13:36", "23-Sep-26 21:57", "21-Oct-26 7:01", "17-Nov-26 15:31", "14-Dec-26 22:36"]
    ws = [w for w in spans(g, lambda s: s.sign_dist("Saturn", "Moon") == 12) if w.start.year == 2026]
    diffs = [abs((w.start - dt.datetime.strptime(a, "%d-%b-%y %H:%M").replace(tzinfo=IST)).total_seconds()) for w, a in zip(ws, kd94)]
    record("KD p.94 Shani-Chandra 2026: 13 windows, starts within 2 min", len(ws) == 13 and max(diffs) <= 120, f"{max(diffs)} s")
    cj = [t for t, _ in conjunction_instants(g, "Mars", "Saturn") if t.year == 2026]
    record("KD p.96 Saturn-Mars exact conjunction 20 Apr 2026 04:13 IST (+/-5 min)",
           abs((cj[0] - dt.datetime(2026, 4, 20, 4, 13, tzinfo=IST)).total_seconds()) <= 300)
    xs = [t.astimezone(IST).date() for t, a, b in crossings(g, lambda s: s["Mercury"].speed > s["Venus"].speed) if b and t.year == 2026]
    want = [dt.date(2026, 4, 10), dt.date(2026, 8, 3), dt.date(2026, 11, 14)]
    record("KD Mercury-manifestation dates 2026 within 1 day", all(any(abs((x - w).days) <= 1 for x in xs) for w in want))
    for y, kind, a, b in ((2017, "sun_ahead", dt.date(2017, 4, 20), dt.date(2017, 6, 22)), (2020, "venus_ahead", dt.date(2020, 1, 11), dt.date(2020, 2, 26)),
                          (2020, "sun_ahead", dt.date(2020, 7, 1), dt.date(2020, 8, 18))):
        gy = Grid(utc(y, 1, 1), utc(y + 1, 1, 1))
        ok = any(abs((w.start.astimezone(IST).date() - a).days) <= 1 and abs((w.end.astimezone(IST).date() - b).days) <= 1
                 for w in spans(gy, lambda s: C._mid(s) == kind))
        record(f"TA Mercury-in-middle {y} {kind} {a}..{b} within 1 day", ok)


def test_catalogue():
    ids = [r.id for r in C.RULES]
    record("Catalogue ids are unique", len(ids) == len(set(ids)), str([i for i in ids if ids.count(i) > 1][:5]))
    record("Every rule names a PDF page", all(any(("TA p." in x) or ("KD p." in x) or x.startswith("(no PDF") for x in r.refs) for r in C.RULES))
    record("Every rule has a verdict and a calculation method", all(r.verdict and r.calc for r in C.RULES))
    record("Every not-computable entry has a reason", all(x["reason"] for x in C.NOT_COMPUTABLE))


if __name__ == "__main__":
    test_wheel()
    test_dates()
    test_catalogue()
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    sys.exit(1 if bad else 0)
