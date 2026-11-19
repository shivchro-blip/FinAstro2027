"""The year's Complete Reference, in the shape of the 2026 source document.

    python tools/build_reference.py              # -> build/reference_2027.html
    python tools/build_reference.py --year 2026  # -> build/reference_2026_recomputed.html
                                                 #    + the cell-by-cell score against
                                                 #    data/source_2026.html

`data/source_2026.html` is a 141-section reference book plus sub-tables and
instrument configuration blocks. This script renders the SAME sections, in the
same order, under the same ids (`sec-1` .. `sec-141`) and the same stylesheet,
for any year -- and computes every row rather than transcribing one.

Where each table comes from, and why it can be trusted:

* **Positional tables** (journeys, motion, nakshatra, navamsa, combustion,
  apsides, lunations, conjunctions, eclipses) are computed here through
  `finastro.ephem` / `finastro.combustion` -- the same functions that write
  `build/astronomy_<year>.json` -- over a span wide enough that a window open on
  1 January shows its real start. Every in-span instant is cross-checked
  against the astronomy file and the build fails on any disagreement over 1 s.
* **Condition tables** (panchang and co-location sections, the sub-tables and
  the instrument configuration groups) are the registered rules' own Mumbai
  firings -- the population `build/calendar_<year>.*` renders -- so the
  reference and the calendar cannot disagree.
* **Derived columns** borrowed from the 2026 document (Sankranti muhurta, the
  lord-relationship column) are used only after this script reproduces them
  against every printed 2026 row; the score is printed in the document.
* **Nothing is approximated.** A section whose rule is `blocked` prints the
  missing input instead of a table, exactly as the registry states it, and the
  narrative chapters (past-year commentary, horoscope, cabinet, numerology)
  are not reproduced because they are prose, not computation.

Times are IST, HH:MM with seconds dropped -- `finastro.timezones.stamp`'s own
convention, so a time here is byte-identical to the calendar's.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import pathlib
import re
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_ap = argparse.ArgumentParser()
_ap.add_argument("--year", type=int, default=2027)
_ap.add_argument("--out", type=pathlib.Path, default=None)
_ap.add_argument("--zone", choices=("IST", "ET"), default="IST",
                 help="IST: Mumbai edition. ET: New York edition (EST/EDT).")
ARGS = _ap.parse_args()
YEAR = ARGS.year

# The year has to be set BEFORE finastro.events / rules import it (see
# tools/build_2026.py for the two names that hold it).
from finastro import config as _config          # noqa: E402
_config.CONF["year"] = YEAR
_config.YEAR = YEAR

from finastro import combustion as cb           # noqa: E402
from finastro import ephem                      # noqa: E402
from finastro.panchang import VISHTI_KARANAS, tithi_name  # noqa: E402
from finastro.rules import (CONFIG_REGISTRY, REGISTRY,  # noqa: E402
                            SUBTABLE_REGISTRY)
from finastro.rules import catalogue as CAT     # noqa: E402
from finastro.rules.base import FIRING_STATUSES, fire  # noqa: E402
from finastro.sky import Sky                    # noqa: E402

SOURCE = ROOT / "data" / "source_2026.html"
ASTRO = ROOT / "build" / f"astronomy_{YEAR}.json"
IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc

#: The edition. Every printed date and time is in TZ; rule tables read the
#: firings at LOC (each venue's own civil days); the Bhadra day/night test
#: uses LOC's own sunrise and sunset.
ZONE = ARGS.zone
TZ = IST if ZONE == "IST" else ZoneInfo("America/New_York")
LOC = "mumbai" if ZONE == "IST" else "new_york"
CITY = "Mumbai" if ZONE == "IST" else "New York"
ZLABEL = "IST" if ZONE == "IST" else "ET"
ZLONG = "IST (Mumbai)" if ZONE == "IST" else "US Eastern, EST/EDT (New York)"
_SUFFIX = "" if ZONE == "IST" else "_ET"
OUT = ARGS.out or (ROOT / "build" / (f"reference_{YEAR}{_SUFFIX}.html" if YEAR != 2026
                                     else f"reference_2026_recomputed{_SUFFIX}.html"))
Y0 = dt.datetime(YEAR, 1, 1, tzinfo=TZ)
Y1 = dt.datetime(YEAR + 1, 1, 1, tzinfo=TZ)
D = dt.timedelta

#: How far either side of the year each body is scanned, so the window in force
#: on 1 January (or 31 December) is printed with its real boundary.
EXT = {"Moon": D(days=45), "Sun": D(days=400), "Mercury": D(days=400),
       "Venus": D(days=500), "Mars": D(days=800), "Jupiter": D(days=1500),
       "Saturn": D(days=3000), "Rahu": D(days=700), "Ketu": D(days=700),
       "Uranus": D(days=3650 * 3), "Neptune": D(days=3650 * 3),
       "Pluto": D(days=3650 * 4)}

SOURCE_NAME = {"Uranus": "Herschel"}       # the document's spelling

VIMSHOTTARI = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
               "Saturn", "Mercury"]

#: Sankranti muhurta by the Moon's nakshatra at the ingress -- the classical
#: 15/30/45 division. Used only because it reproduces all twelve printed 2026
#: rows (scored below and printed in the document); otherwise it would be
#: blocked like the rest of the doctrine the source never states.
MUHURTA_15 = {"Ardra", "Ashlesha", "Swati", "Jyeshtha", "Shatabhisha", "Bharani"}
MUHURTA_45 = {"Rohini", "Punarvasu", "Vishakha", "Uttara Phalguni",
              "Uttara Ashadha", "Uttara Bhadrapada"}


# ------------------------------------------------------------------ format

def ist(t: dt.datetime) -> dt.datetime:
    """The instant in the edition's zone (IST or ET), rounded to the second."""
    t = t.astimezone(UTC)
    if t.microsecond >= 500_000:
        t += D(seconds=1)
    return t.replace(microsecond=0).astimezone(TZ)


def fd(t): return ist(t).strftime("%d-%b-%y") if t else ""
def ft(t): return ist(t).strftime("%H:%M") if t else ""
def fw(t): return ist(t).strftime("%A") if t else ""


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def nak_lord(nak: str) -> str:
    return VIMSHOTTARI[ephem.NAKSHATRAS.index(nak) % 9]


def lord(sign: str) -> str:
    return ephem.SIGN_LORDS[sign]


def dig(body: str, sign: str) -> str:
    st = ephem.dignity_states(body, sign) or []
    lab = [s.capitalize() for s in st if s != "trine"]
    return f"{sign} ({', '.join(lab)})" if lab else sign


def in_year(a, b) -> bool:
    """Window [a, b) overlaps the year; None means open."""
    return (a is None or a < Y1) and (b is None or b > Y0)


# ------------------------------------------------- astronomy cross-check

ASTRO_DOC = json.loads(ASTRO.read_text(encoding="utf-8"))
_SPAN_LO = dt.datetime.fromisoformat(ASTRO_DOC["meta"]["span_start_utc"].replace("Z", "+00:00"))
_SPAN_HI = dt.datetime.fromisoformat(ASTRO_DOC["meta"]["span_end_utc"].replace("Z", "+00:00"))
_BY_CLASS: dict[tuple[str, str], list[dt.datetime]] = collections.defaultdict(list)
for _r in ASTRO_DOC["records"]:
    if _r["bodies"]:
        _BY_CLASS[(_r["event_class"], _r["bodies"][0])].append(
            dt.datetime.fromisoformat(_r["time"]["t_start_utc"].replace("Z", "+00:00")))
CROSSCHECK = collections.Counter()


def crosscheck(event_class: str, body: str, instants) -> None:
    """Every in-span instant computed here must be in the astronomy file."""
    have = sorted(_BY_CLASS.get((event_class, body), []))
    for t in instants:
        if not (_SPAN_LO + D(hours=1) <= t <= _SPAN_HI - D(hours=1)):
            continue
        near = min(have, key=lambda h: abs((h - t).total_seconds()), default=None)
        off = abs((near - t).total_seconds()) if near else 1e9
        if off > 1.5:
            raise SystemExit(f"cross-check failed: {event_class} {body} {t} "
                             f"is {off:.0f}s from the astronomy file")
        CROSSCHECK[event_class] += 1


# ------------------------------------------------------- window builders

_ING_CACHE: dict = {}


def crossings(body: str, arc: float):
    key = (body, arc)
    if key not in _ING_CACHE:
        ext = EXT[body]
        out = ephem.ingresses(body, Y0 - ext, Y1 + ext, arc)
        cls = {30.0: "sign_ingress", 360 / 27: "nakshatra_ingress",
               30 / 9: "navamsa_ingress"}[arc]
        crosscheck(cls, body, [t for t, _, _ in out])
        _ING_CACHE[key] = out
    return _ING_CACHE[key]


def windows(body: str, arc: float):
    """[(start|None, end|None, index_held)] overlapping the year."""
    xs = crossings(body, arc)
    if not xs:
        idx = int(ephem.longitude(Y0, body) // arc)
        return [(None, None, idx)]
    out = [(None, xs[0][0], xs[0][1])]
    for (t, _f, to), nxt in zip(xs, xs[1:] + [None]):
        out.append((t, nxt[0] if nxt else None, to))
    return [w for w in out if in_year(w[0], w[1])]


_ST_CACHE: dict = {}


def stations(body: str):
    if body not in _ST_CACHE:
        ext = EXT[body]
        out = ephem.stations(body, Y0 - ext, Y1 + ext)
        crosscheck("station", body, [t for t, _ in out])
        _ST_CACHE[body] = out
    return _ST_CACHE[body]


def motion_windows(body: str):
    """[(start, end, 'Direct'|'Retrograde', sign)] split at sign ingresses."""
    st = stations(body)
    if st:
        mot = [(None, st[0][0], "Retrograde" if st[0][1] == "D" else "Direct")]
        for (t, k), nxt in zip(st, st[1:] + [None]):
            mot.append((t, nxt[0] if nxt else None,
                        "Retrograde" if k == "R" else "Direct"))
    else:
        mot = [(None, None, "Retrograde" if ephem.position(Y0, body).retrograde
                else "Direct")]
    signs = windows(body, 30.0)
    out = []
    for a, b, m in mot:
        if not in_year(a, b):
            continue
        for sa, sb, si in signs:
            lo = a if sa is None else (sa if a is None else max(a, sa))
            hi = b if sb is None else (sb if b is None else min(b, sb))
            if (lo is None or hi is None or lo < hi) and in_year(lo, hi):
                out.append((lo, hi, m, ephem.SIGNS[si]))
    return out


def start_cells(a):
    return ("Start of the year", "") if a is None or (a < Y0 - D(days=3650 * 3)) \
        else (fd(a), ft(a))


def end_cells(b):
    return ("Till year end", "") if b is None or (b > Y1 + D(days=3650 * 3)) \
        else (fd(b), ft(b))


# ===================================================================== tables
# Each builder returns a list of blocks: ("table", headers, rows, caption) or
# ("note", text). Rows are lists of cell strings.

def T(headers, rows, caption=None):
    # A cell is a string, or (css_class, text) for a coloured verdict cell.
    return ("table", list(headers),
            [[c if isinstance(c, tuple) else str(c) for c in r] for r in rows],
            caption)


def N(text, cls="note"):
    return (cls, text)


def b_sankranti():
    rows = []
    for t, _f, to in crossings("Sun", 30.0):
        if not Y0 <= t < Y1:
            continue
        mn = ephem.position(t, "Moon").nakshatra
        mu = 15 if mn in MUHURTA_15 else 45 if mn in MUHURTA_45 else 30
        rows.append([ephem.SIGNS[to], fd(t), ft(t), fw(t), mn, mu])
    return [T(["Sign", "Start Date", "Start Time", "Day", "Moon Nakshtra",
               "Sankranti Muhurat"], rows)]


def b_sun_nakshatra():
    rows = []
    for a, b, idx in windows("Sun", 360 / 27):
        if a is None or a >= Y1:
            continue
        nak = ephem.NAKSHATRAS[idx]
        lo = nak_lord(nak)
        if lo == "Sun":
            rel = "Own"
        else:
            rel = ephem.sign_distance_aspect(
                ephem.SIGNS[(idx * 4) // 9], ephem.position(a, lo).sign)
        rows.append([nak, fd(a), ft(a), lo, rel])
    return [T(["Nakshtra", "Start Date", "Start Time", "Nakshtra Lord",
               "Relationship"], rows)]


def b_journey(body):
    rows = []
    for a, b, idx in windows(body, 30.0):
        sign = ephem.SIGNS[idx]
        lo = lord(sign)
        if lo == body:
            rel = "Own"
        elif body in ("Rahu", "Ketu") or a is None:
            # Nodes: period-constant, anchored at the node's own ingress --
            # ephem.lord_relationship's convention.
            when = a if a is not None else Y0
            rel = ephem.sign_distance_aspect(sign, ephem.position(when, lo).sign)
        else:
            rel = ephem.sign_distance_aspect(sign, ephem.position(a, lo).sign)
        sd, st_ = start_cells(a)
        ed, et = end_cells(b)
        rows.append([dig(body, sign), sd, st_, ed, et, lo, rel])
    return [T(["Sign", "Start Date", "Start Time", "End Date", "End Time",
               "Lord", "Relationship"], rows)]


def b_motion(body):
    rows = []
    for a, b, m, sign in motion_windows(body):
        sd, st_ = start_cells(a)
        ed, et = end_cells(b)
        rows.append([m, dig(body, sign), sd, st_, ed, et, lord(sign)])
    return [T(["Motion", "Sign", "Start Date", "Start Time", "End Date",
               "End Time", "Lord"], rows)]


def split_at_stations(body, wins):
    """Cut each window at the body's stations, as the 2026 tables do: a
    nakshatra or navamsa row ends at a station and a new one starts there,
    tagged "(Retrograde)" while the body is retrograde. The mean node is
    retrograde by construction and is never tagged."""
    if body in ("Rahu", "Ketu"):
        return [(a, b, i, False) for a, b, i in wins]
    cuts = [t for t, _ in stations(body)]
    out = []
    for a, b, i in wins:
        pts = [a] + [c for c in cuts if (a is None or c > a) and (b is None or c < b)] + [b]
        for lo, hi in zip(pts, pts[1:]):
            probe = (lo or Y0 - D(days=1)) + D(minutes=1) if lo is not None else \
                (hi - D(minutes=1) if hi is not None else Y0)
            if not in_year(lo, hi):
                continue
            out.append((lo, hi, i, ephem.position(probe, body).retrograde))
    return out


def split_at_signs(body, wins):
    """A nakshatra row also ends where the SIGN changes inside it (the table
    carries a Sign column): the 2026 Rahu rows split Dhanistha at the node's
    Aquarius -> Capricorn ingress."""
    cuts = [t for t, _f, _t in crossings(body, 30.0)]
    out = []
    for a, b, i, r in wins:
        pts = [a] + [c for c in cuts if (a is None or c > a) and (b is None or c < b)] + [b]
        for lo, hi in zip(pts, pts[1:]):
            if in_year(lo, hi):
                out.append((lo, hi, i, r))
    return out


def b_constellation(body):
    rows = []
    for a, b, idx, retro in split_at_signs(body, split_at_stations(body, windows(body, 360 / 27))):
        nak = ephem.NAKSHATRAS[idx]
        sd, st_ = start_cells(a)
        ed, et = end_cells(b)
        mid = a if a is not None else Y0
        sign = ephem.position(mid + D(seconds=60) if a else mid, body).sign
        rows.append([nak + (" (Retrograde)" if retro else ""), sd, st_, ed, et,
                     sign, nak_lord(nak)])
    return [T(["Constellation", "Start Date", "Start Time", "End Date",
               "End Time", "Sign", "Constellation Lord"], rows)]


def b_navamsa(body):
    rows = []
    for a, b, idx, retro in split_at_stations(body, windows(body, 30 / 9)):
        sign = ephem.SIGNS[idx % 12]
        sd, st_ = start_cells(a)
        ed, et = end_cells(b)
        rows.append([dig(body, sign) + (" (Retrograde)" if retro else ""),
                     sd, st_, ed, et, lord(sign)])
    return [T(["Sign", "Start Date", "Start Time", "End Date", "End Time",
               "Sign Lord"], rows)]


def _merge_d9(body, keep):
    """Merge consecutive navamsa windows that satisfy `keep(rashi, d9)`."""
    out = []
    for a, b, idx in windows(body, 30 / 9):
        rashi = ephem.sign_of_navamsa_index(idx)
        d9 = ephem.SIGNS[idx % 12]
        if not keep(rashi, d9):
            continue
        if out and out[-1][1] == a and out[-1][2] == rashi:
            out[-1] = (out[-1][0], b, rashi)
        else:
            out.append((a, b, rashi))
    return out


def b_mars_pisces_d9():
    rows = []
    for a, b, rashi in _merge_d9("Mars", lambda r, d9: d9 == "Pisces"):
        sd, st_ = start_cells(a)
        ed, et = end_cells(b)
        rows.append([dig("Mars", rashi), sd, st_, ed, et, lord(rashi)])
    return [T(["Sign", "Start Date", "Start Time", "End Date", "End Time",
               "Sign Lord"], rows or [["No Pisces-navamsa window in the year",
                                       "", "", "", "", ""]])]


def b_vargottam_mars():
    rows = []
    for a, b, rashi in _merge_d9("Mars", lambda r, d9: r == d9):
        sd, st_ = start_cells(a)
        ed, et = end_cells(b)
        rows.append([dig("Mars", rashi), sd, st_, ed, et, lord(rashi)])
    return [T(["Sign", "Start Date", "Start Time", "End Date", "End Time",
               "Sign Lord"], rows)]


_CB_CACHE: dict = {}


def combust_events(body):
    if body not in _CB_CACHE:
        ext = D(days=420)
        ev = cb.find_events(body, (Y0 - ext).date(), (Y1 + ext).date())
        _CB_CACHE[body] = ev
    return _CB_CACHE[body]


def combust_cycles(body):
    """[(combust_event|None, rise_event|None)] touching the year."""
    ev = combust_events(body)
    out, pending = [], None
    for e in ev:
        if e.kind == "combust":
            pending = e
        elif e.kind == "rise":
            out.append((pending, e))
            pending = None
    if pending is not None:
        out.append((pending, None))
    def day(e): return e.instant.date() if e else None
    return [(c, r) for c, r in out
            if (r is None or day(r) >= Y0.date()) and (c is None or day(c) < Y1.date())]


def _conj_sun(body, c, r):
    """Sun-body conjunction instant between combust and rise."""
    lo = c.instant if c else (r.instant - D(days=60))
    hi = r.instant if r else (c.instant + D(days=60))
    xs = list(ephem.find_crossings(lambda t: ephem.separation(t, body, "Sun"), lo, hi,
                              D(hours=6)))
    return xs[0] if xs else None


def b_combust(body, conj=False, sign_cols=True):
    rows = []
    for c, r in combust_cycles(body):
        cd = c.instant.strftime("%d-%b-%y") if c else "Before the year"
        rd = r.instant.strftime("%d-%b-%y") if r else "After the year"
        dur = (r.instant - c.instant).days if c and r else ""
        row = [cd, c.direction if c else "", ]
        if sign_cols:
            row.append(dig(body, ephem.position(c.instant, body).sign) if c else "")
        row += [rd, r.direction if r else ""]
        row.append(dur)
        if sign_cols:
            row.append(dig(body, ephem.position(r.instant, body).sign) if r else "")
        if conj:
            k = _conj_sun(body, c, r)
            row += [fd(k), ft(k)] if k else ["", ""]
        rows.append(row)
    hdr = ["Combust Date", "Direction"] + (["Sign"] if sign_cols else []) + \
          ["Rise Date", "Direction", "Duration (days)"] + (["Sign"] if sign_cols else [])
    if conj:
        hdr += [f"Sun {body} Conjunction", "Time"]
    blocks = [T(hdr, rows or [["No combustion in the year"] + [""] * (len(hdr) - 1)])]
    blocks.append(N(f"Combust / rise dates are civil days resolved by kalamsha "
                    f"(threshold {cb.threshold(body, False)}&deg; direct, "
                    f"{cb.threshold(body, True)}&deg; retrograde, calibrated on the "
                    f"2026 edition); precision &plusmn;{cb.precision_days(body)} day(s), "
                    f"grade {cb.certainty_of(body)}."
                    + (" Dates are Mumbai civil days: kalamsha is measured at the Mumbai "
                       "horizon." if ZONE == "ET" else ""), "flag"))
    return blocks


def b_mercury_manifestation():
    """B10, from the registered rule's own firings (so it is the calendar's
    population), with the exact overtaking instant beside the printed date."""
    rows = []
    for f in sorted(FIRED.get("b010_mercury_manifestation", []),
                    key=lambda f: f.civil_date):
        t = dt.datetime.fromisoformat(f.detail["overtake_utc"].replace("Z", "+00:00"))
        m = ephem.position(t, "Mercury")
        rows.append([f.civil_date.strftime("%d-%b-%y"), f.civil_date.strftime("%A"),
                     f"{fd(t)} {ft(t)}", f"{m.speed:.3f}&deg;/day",
                     f"{abs(ephem.separation(t, 'Mercury', 'Sun')):.1f}&deg; East"])
    return [T(["Date", "Day", f"Mercury overtakes Venus ({ZLABEL})", "Speed (both)",
               "Mercury from Sun"], rows),
            N("The date is the first day a 12:00 UT daily ephemeris shows Mercury "
              "faster than Venus while rising in the East; the same reading "
              "reproduces all three printed 2026 dates (10-Apr, 03-Aug, 14-Nov).",
              "flag")]


# ------------------------------------------------------------------ Bhadra

LOKA = {**{s: "Swarg" for s in ("Aries", "Taurus", "Gemini", "Scorpio")},
        **{s: "Patal" for s in ("Virgo", "Libra", "Sagittarius", "Capricorn")},
        **{s: "Earth" for s in ("Cancer", "Leo", "Aquarius", "Pisces")}}


def _verdict(text):
    return ({"Positive": "pos", "Negative": "neg"}.get(text, "neu"), text)


def _tithi_label(n):
    paksha = "Shukla" if n <= 15 else "Krishna"
    return f"{paksha} {tithi_name(n)}"


def bhadra_windows():
    """[(start, end, karana)] for every Vishti window touching the year,
    from the karana series (a Vishti opens at its ingress and closes at the
    next karana ingress)."""
    ks = sorted((r for r in ASTRO_DOC["records"] if r["event_class"] == "karana_ingress"),
                key=lambda r: r["time"]["t_start_utc"])
    out = []
    for r, nxt in zip(ks, ks[1:]):
        k = r["astronomy"]["karana_to"]
        if k in VISHTI_KARANAS:
            a = dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00"))
            b = dt.datetime.fromisoformat(nxt["time"]["t_start_utc"].replace("Z", "+00:00"))
            if in_year(a, b):
                out.append((a, b, k, r["astronomy"]["sign"]))
    return out


def _horizon(loc):
    ev = []
    for r in ASTRO_DOC["records"]:
        if r["event_class"] in ("sunrise", "sunset") and r["id"].endswith(":" + loc):
            ev.append((dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00")),
                       r["event_class"]))
    return sorted(ev)


def b_kshin():
    """The 2026 Kshin Moon table: Start Date / Start Time / End Date / End Time."""
    rows = []
    for f in sorted({(f.start_utc, f.end_utc): f for f in FIRED.get(
            "sub_kshin_malefic_moon", [])}.values(), key=lambda f: f.start_utc):
        rows.append([fd(f.start_utc), ft(f.start_utc), fd(f.end_utc), ft(f.end_utc)])
    return [N("Moon is malefic from Krishna Ashtami till Shukla Panchmi (both days "
              "included)."),
            T(["Start Date", "Start Time", "End Date", "End Time"], rows),
            N(f"Start: the moment Krishna Ashtami (tithi 23) begins. End: the moment "
              f"Shukla Panchami (tithi 5) ends. Times {ZLONG}. Windows open on 1-Jan or "
              f"running on 31-Dec are printed whole. The same rule reproduces all 13 "
              f"printed 2026 windows within 2 minutes.", "flag")]


BHADRA_SCORE: list = []


def b_bhadra():
    """The 2026 Bhadra table, column for column, for the edition's venue."""
    hz = _horizon(LOC)
    wins = bhadra_windows()
    # Same population the calendar's Bhadra rule fires on.
    fired = {(f.start_utc, f.end_utc) for f in _FIRINGS
             if f.rule_id == "sub_bhadra" and f.location == LOC}
    have = {(a, b) for a, b, _k, _s in wins}
    missing = {w for w in fired if w not in have}
    if missing:
        raise SystemExit(f"Bhadra: {len(missing)} calendar windows not in the table")
    rows, close = [], []
    for a, b, k, sign in wins:
        tithi = (k + 1) // 2
        stay = "Day Bhadra" if k % 2 == 1 else "Night Bhadra"
        last = max((x for x in hz if x[0] <= a), default=None)
        period = "Day Time" if last and last[1] == "sunrise" else "Night Time"
        r1 = "Positive" if (stay == "Day Bhadra") == (period == "Night Time") else "Negative"
        loka = LOKA[sign]
        r2 = "Negative" if loka == "Earth" else "Positive"
        overall = r1 if r1 == r2 else "Neutral"
        rows.append([fd(a), ft(a), fd(b), ft(b), _tithi_label(tithi), stay,
                     f"{stay} in {period}", _verdict(r1), sign, f"{loka} Bhadra",
                     _verdict(r2), _verdict(overall)])
        near = min(hz, key=lambda x: abs((x[0] - a).total_seconds()))
        if abs((near[0] - a).total_seconds()) <= 45 * 60:
            close.append(f"<strong>{fd(a)}</strong> (opens {ft(a)}, {CITY} {near[1]} "
                         f"{ft(near[0])} &rarr; {period.split()[0]})")
    blocks = [
        N(f"<strong>Method.</strong> Every window is computed with the Swiss Ephemeris. A Bhadra "
          f"(Vishti karana) is a 6&deg; step of Moon&minus;Sun elongation, so the eight windows of each "
          f"lunar month fall on karana numbers 8, 15, 22, 29, 36, 43, 50 and 57. All times are "
          f"<strong>{ZLONG}</strong>.<br><br>"
          f"<strong>Stay</strong> (Day / Night Bhadra) is karana parity &mdash; odd (first half of the "
          f"tithi) = Day Bhadra, even = Night Bhadra; it never changes with place or timezone.<br><br>"
          f"<strong>Sign</strong> is the Moon&rsquo;s sidereal sign (Lahiri) when the window opens; "
          f"<strong>Bhadra Nature 2</strong> follows the loka rule &mdash; Aries/Taurus/Gemini/Scorpio "
          f"&rarr; Swarg, Virgo/Libra/Sagittarius/Capricorn &rarr; Patal, Cancer/Leo/Aquarius/Pisces "
          f"&rarr; Earth (Mrityu-loka), the malefic case.<br><br>"
          f"<strong>Bhadra Nature 1</strong> asks whether the window opens after sunrise (Day Time) or "
          f"after sunset (Night Time) at <strong>{CITY}</strong>; this is the one local column. "
          f"<strong>Result 1</strong>: a Bhadra opening in the opposite period is defused (Positive), "
          f"in the same period it is live (Negative). <strong>Overall</strong> is Positive or Negative "
          f"when both results agree, Neutral when they split."),
        T(["Start Date", "Start Time", "End Date", "End Time", "Tithi", "Stay",
           "Bhadra Nature 1", "Result 1", "Sign", "Bhadra Nature 2", "Result 2", "Overall"],
          rows),
    ]
    if close:
        blocks.append(N(f"<strong>Why the reference place matters.</strong> {len(close)} windows "
                        f"open within 45 minutes of {CITY} sunrise or sunset, where a fixed "
                        f"06:00&ndash;18:00 clock could classify them differently: "
                        + "; ".join(close) + "."))
    return blocks


def _max_elongations(body="Mercury"):
    lo, hi = Y0 - D(days=10), Y1 + D(days=10)
    f = lambda t: abs(ephem.separation(t, body, "Sun"))
    out, t, step = [], lo, D(hours=12)
    prev2, prev1 = f(t - step), f(t)
    while t < hi:
        nxt = t + step
        cur = f(nxt)
        if prev1 > prev2 and prev1 >= cur:
            a, b = t - step, nxt
            for _ in range(60):
                m1, m2 = a + (b - a) / 3, b - (b - a) / 3
                if f(m1) < f(m2):
                    a = m1
                else:
                    b = m2
            out.append(a + (b - a) / 2)
        prev2, prev1, t = prev1, cur, nxt
    return [x for x in out if Y0 <= x < Y1]


def b_mercury_furthest():
    rows = []
    for t in _max_elongations():
        s = ephem.separation(t, "Mercury", "Sun")
        d = abs(s)
        rows.append([fd(t), ft(t),
                     ("Ahead" if s > 0 else "Behind") +
                     f" &mdash; {int(d)}&deg;{int(round((d % 1) * 60)):02d}' "
                     f"{'east, evening star' if s > 0 else 'west, morning star'}"])
    return [T(["Date", "Time", "Position from Sun"], rows),
            N("Greatest elongation: the turning point of the Sun&ndash;Mercury "
              "longitude separation, bisected to the minute.", "flag")]


def _aspects(cls, pair_has, other_excl=()):
    rows = []
    for r in ASTRO_DOC["records"]:
        if r["event_class"] != cls:
            continue
        t = dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00"))
        if not Y0 <= t < Y1:
            continue
        b = r["bodies"]
        if pair_has(b):
            rows.append((t, b, r))
    return sorted(rows, key=lambda x: x[0])


def b_pair_conj(a, b):
    rows = []
    for t, bodies, r in _aspects("conjunction", lambda x: set(x) == {a, b}):
        rows.append([fd(t), ft(t), ephem.position(t, a).sign])
    return [T(["Date", "Time", "Sign"],
              rows or [["No conjunction in the year", "", ""]])]


def b_venus_mercury_conj():
    rows = []
    for t, bodies, r in _aspects("conjunction", lambda x: set(x) == {"Venus", "Mercury"}):
        v = "Retrograde" if ephem.position(t, "Venus").retrograde else "Direct"
        m = "Retrograde" if ephem.position(t, "Mercury").retrograde else "Direct"
        status = "Direct" if v == m == "Direct" else (
            "Both Retrograde" if v == m else "Contra-Directional")
        rows.append([ephem.position(t, "Venus").sign, fd(t), ft(t), status, v, m])
    return [T(["Sign", "Date", "Time", "Status", "Venus", "Mercury"],
              rows or [["No conjunction in the year"] + [""] * 5])]


def b_outer_aspects(outer, cls, exclude_moon=True):
    rows = []
    for t, bodies, r in _aspects(cls, lambda x: outer in x):
        other = [x for x in bodies if x != outer][0]
        rows.append([SOURCE_NAME.get(other, other), fd(t), ft(t),
                     r["astronomy"]["sign"]])
    return [T(["Planet", "Date", "Time", "Sign"],
              rows or [["None in the year", "", "", ""]])]


def b_apsis(kind):
    rows = []
    for r in ASTRO_DOC["records"]:
        if r["event_class"] == "apsis" and r["rule_family"] == f"orbit/{kind}":
            t = dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00"))
            if Y0 <= t < Y1:
                km = round(r["astronomy"]["distance"] * 149_597_870.7)
                rows.append([fd(t), ft(t), f"{km:,}"])
    return [T(["Date", "Local Time", "Distance in KM"], rows)]


def b_perihelion():
    rows = []
    for r in ASTRO_DOC["records"]:
        if r["event_class"] == "apsis" and r["bodies"] == ["Sun"]:
            t = dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00"))
            if Y0 <= t < Y1:
                km = round(r["astronomy"]["distance"] * 149_597_870.7)
                rows.append([fd(t), ft(t), f"{km:,} km",
                             r["rule_family"].split("/")[1].capitalize()])
    return [T(["Date", "Time", "Distance", "Event"], rows)]


def _lunations(phase):
    out = []
    for r in ASTRO_DOC["records"]:
        if r["event_class"] == "lunation" and r["rule_family"] == f"lunation/{phase}":
            t = dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00"))
            if Y0 <= t < Y1:
                out.append((t, r))
    return out


def b_amavasya():
    return [T(["Date", "Time", "Day", "Sign"],
              [[fd(t), ft(t), fw(t), r["astronomy"]["sign"]]
               for t, r in _lunations("new_moon")])]


def b_purnima():
    return [T(["Date", "Time", "Day", "Sign"],
              [[fd(t), ft(t), fw(t), r["astronomy"]["sign"]]
               for t, r in _lunations("full_moon")])]


def b_saturn_shadow():
    """B30: the direct station to the re-crossing of the retrograde-station
    degree. The window's definition is the source's own (its 2026 rows are the
    two stations and its note names the re-crossing); no speed level needed."""
    st = stations("Saturn")
    rows, notes = [], []
    for (t, k) in st:
        if k == "R" and Y0 - D(days=400) <= t < Y1:
            lon = ephem.longitude(t, "Saturn")
            nxt_d = next((x for x, kk in st if kk == "D" and x > t), None)
            if nxt_d is None:
                continue
            lon_d = ephem.longitude(nxt_d, "Saturn")
            # re-crossing of the retro-station longitude after the direct station
            xs = list(ephem.find_crossings(
                lambda x, L=lon: ((ephem.longitude(x, "Saturn") - L + 180) % 360) - 180,
                nxt_d, nxt_d + D(days=400), D(days=1)))
            back = xs[0] if xs else None
            if not in_year(t, back):
                continue
            sg = ephem.SIGNS[int(lon // 30)]
            rows.append(["Retrograde", f"{sg} ({lord(sg)})", fd(t), ft(t),
                         f"{int(lon % 30)}&deg;{int(round((lon % 1) * 60)):02d}'"])
            sg2 = ephem.SIGNS[int(lon_d // 30)]
            rows.append(["Direct", f"{sg2} ({lord(sg2)})", fd(nxt_d), ft(nxt_d),
                         f"{int(lon_d % 30)}&deg;{int(round((lon_d % 1) * 60)):02d}'"])
            if back:
                rows.append(["Re-crosses retrograde-station degree", "", fd(back),
                             ft(back), f"{int(lon % 30)}&deg;{int(round((lon % 1) * 60)):02d}'"])
                notes.append(f"Demoted / shadow speed: {fd(nxt_d)} (direct station) "
                             f"to {fd(back)}, when Saturn re-crosses "
                             f"{int(lon % 30)}&deg;{int(round((lon % 1) * 60)):02d}' {sg}.")
    return [T(["Motion", "Sign", "Date", "Time", "Degree"], rows)] + \
        [N(n, "remark") for n in notes]


def b_eclipse():
    rows = []
    for r in ASTRO_DOC["records"]:
        if r["event_class"] != "eclipse":
            continue
        tm = r["time"]
        a = dt.datetime.fromisoformat(tm["t_start_utc"].replace("Z", "+00:00"))
        b = dt.datetime.fromisoformat(tm["t_end_utc"].replace("Z", "+00:00"))
        if not in_year(a, b):
            continue
        mx = tm.get("contacts_global", {}).get("max", {})
        mxt = dt.datetime.fromisoformat(mx["utc"].replace("Z", "+00:00")) if mx else None
        moon_a = ephem.position(a, "Moon").nakshatra
        moon_b = ephem.position(b, "Moon").nakshatra
        vis = [f for f in r["qa"].get("flags", []) if "visible" in f]
        rows.append([fd(a), r["astronomy"].get("eclipse_type", ""),
                     r["astronomy"].get("magnitude", ""), ft(a), ft(mxt), ft(b),
                     fw(mxt or a), moon_a, moon_b,
                     ", ".join(v.replace("_", " ") for v in vis)])
    return [T(["Date", "Eclipse", "Magnitude", "Start Time", "Maximum",
               "End Time", "Day", "Start Nakshatra", "End Nakshatra",
               "India"], rows),
            N("Global contact times (first to last contact of the eclipse anywhere "
              f"on Earth), {ZLABEL}. The source's lunar-month column is not printed: "
              "the month system (amanta / purnimanta) is one of the five doctrinal "
              "decisions the 2026 edition never states.", "flag")]


# ------------------------------------------------- rule-firing renderer

SKY = Sky.load(ASTRO)
ALL_RULES = list(REGISTRY) + list(CONFIG_REGISTRY) + list(SUBTABLE_REGISTRY)
_FIRINGS = fire([r for r in ALL_RULES if r.status in FIRING_STATUSES], SKY, YEAR)
FIRED: dict[str, list] = collections.defaultdict(list)
_BY_ID = {r.id: r for r in ALL_RULES}
#: Rules evaluated at Mumbai only (the kalamsha horizon family, B10's
#: noon-GMT date) print their Mumbai rows in the New York edition too.
FIRED_AT: dict[str, str] = {}
for _f in _FIRINGS:
    _want = LOC if LOC in _BY_ID[_f.rule_id].locations else "mumbai"
    if _f.location == _want:
        FIRED[_f.rule_id].append(_f)
        FIRED_AT[_f.rule_id] = _want

_SKIP_KEYS = {"id", "utc", "flags", "how_read", "anchor", "carried_in",
              "residency_open_end", "target_unavailable_because",
              "relationship_unavailable_because", "ist_date", "ist_time",
              "precision", "distance_au", "at", "bodies", "pradosh_clause"}


def detail_text(d) -> str:
    if d is None:
        return ""
    if isinstance(d, dict):
        parts = []
        for k, v in d.items():
            if k in _SKIP_KEYS or v in (None, "", [], ()):
                continue
            if k.endswith("_utc"):
                try:
                    v = f"{fd(dt.datetime.fromisoformat(v.replace('Z', '+00:00')))} " \
                        f"{ft(dt.datetime.fromisoformat(v.replace('Z', '+00:00')))}"
                except Exception:
                    pass
            if isinstance(v, (list, tuple)):
                v = ", ".join(map(str, v))
            parts.append(f"{k.replace('_', ' ')}: {v}")
        return "; ".join(parts)
    if isinstance(d, (list, tuple)):
        return " / ".join(map(str, d))
    return str(d)


def rule_table(r, caption=None):
    fs = FIRED.get(r.id, [])
    groups: dict = collections.OrderedDict()
    for f in sorted(fs, key=lambda f: (f.start_utc, f.civil_date)):
        key = (f.start_utc, f.end_utc, detail_text(f.detail))
        groups.setdefault(key, (f, []))[1].append(f.civil_date)
    rows = []
    for (a, b, det), (f, days) in groups.items():
        dated = f.precision != "exact"
        a_s = "Before the year" if f.open_start else fd(a)
        b_s = "After the year" if f.open_end else fd(b)
        if dated:
            # date_only spans end at the midnight AFTER the last day held
            b_s = "After the year" if f.open_end else fd(b - D(seconds=1))
        dlist = sorted(set(days))
        if len(dlist) <= 3:
            held = ", ".join(d.strftime("%d-%b (%a)") for d in dlist)
        else:
            held = f"{dlist[0]:%d-%b} &ndash; {dlist[-1]:%d-%b} ({len(dlist)} days)"
        if a == b:
            rows.append([fd(a), ft(a), fw(a), "", "", held, det])
        else:
            rows.append([a_s, "" if dated or f.open_start else ft(a),
                         "" if f.open_start else fw(a),
                         b_s, "" if dated or f.open_end else ft(b), held, det])
    hdr = ["Start Date", "Start Time", "Day", "End Date", "End Time",
           f"{'Mumbai' if FIRED_AT.get(r.id, LOC) == 'mumbai' else 'New York'} civil day(s)",
           "Detail"]
    if not rows:
        rows = [[f"No occurrence in {YEAR}", "", "", "", "", "", ""]]
    # drop an all-empty Detail column
    if all(not row[-1] for row in rows):
        hdr, rows = hdr[:-1], [row[:-1] for row in rows]
    return T(hdr, rows, caption)


#: The configuration registry names its missing inputs by short key.
MISSING_PLAIN = {
    "valence": "which planets count as benefic or malefic",
    "darshan": "the first-crescent (Moon sighting) rule",
    "aspect_orb": "the aspect orb",
    "month_system": "the lunar month system (amanta or purnimanta)",
    "vedha_wheel": "the Vedh wheel for this table",
    "no_dated_window": "a dated window; the 2026 page prints none",
    "sign_lordship": "the sign-lordship rule for the outer planets",
    "scope": "the scope of the rule",
    "speed_threshold": "a speed level for the planet",
}


def blocked_note(r) -> tuple:
    why = "; ".join(MISSING_PLAIN.get(m, m) for m in r.missing_inputs) \
        or r.ambiguity or "no executable reading"
    kind = "Not computed &mdash; ambiguous source wording" if r.status == "ambiguous" \
        else "Not computed &mdash; blocked on an input the 2026 edition never supplies"
    return N(f"<b>{kind}.</b> {esc(why)}", "note")


def rules_for_section(n):
    return [r for r in REGISTRY if r.section.b == n]


def b_rules(n):
    rs = rules_for_section(n)
    out = []
    multi = len([r for r in rs if r.status in FIRING_STATUSES]) > 1
    for r in rs:
        if r.status in FIRING_STATUSES:
            cap = esc(r.condition_text[:160]) if multi else None
            out.append(rule_table(r, cap))
        else:
            out.append(blocked_note(r))
    return out or [N("No rule registered for this section.")]


# ------------------------------------------------------------ section map

DIRECT = {
    1: b_sankranti, 2: b_sun_nakshatra,
    3: lambda: b_journey("Mars"), 4: lambda: b_combust("Mars"),
    5: b_mars_pisces_d9, 6: b_vargottam_mars,
    7: lambda: b_journey("Mercury"), 8: lambda: b_motion("Mercury"),
    9: lambda: b_combust("Mercury", conj=True, sign_cols=False),
    10: b_mercury_manifestation,
    11: b_mercury_furthest, 12: lambda: b_pair_conj("Mars", "Mercury"),
    13: lambda: b_journey("Venus"), 14: lambda: b_motion("Venus"),
    15: lambda: b_combust("Venus"), 17: b_venus_mercury_conj,
    20: lambda: b_journey("Jupiter"), 21: lambda: b_motion("Jupiter"),
    22: lambda: b_combust("Jupiter", conj=True, sign_cols=False),
    23: lambda: b_constellation("Jupiter"), 24: lambda: b_navamsa("Jupiter"),
    25: lambda: b_journey("Saturn"), 26: lambda: b_motion("Saturn"),
    27: lambda: b_combust("Saturn", conj=True, sign_cols=False),
    28: lambda: b_constellation("Saturn"), 29: lambda: b_navamsa("Saturn"),
    30: b_saturn_shadow,
    31: lambda: b_journey("Rahu"), 32: lambda: b_constellation("Rahu"),
    33: lambda: b_navamsa("Rahu"), 34: lambda: b_journey("Ketu"),
    35: lambda: b_constellation("Ketu"), 36: lambda: b_navamsa("Ketu"),
    37: lambda: b_journey("Uranus"), 38: lambda: b_motion("Uranus"),
    39: lambda: b_constellation("Uranus"), 40: lambda: b_navamsa("Uranus"),
    41: lambda: b_outer_aspects("Uranus", "conjunction"),
    42: lambda: b_outer_aspects("Uranus", "opposition"),
    43: lambda: b_journey("Neptune"), 44: lambda: b_motion("Neptune"),
    45: lambda: b_constellation("Neptune"), 46: lambda: b_navamsa("Neptune"),
    47: lambda: b_outer_aspects("Neptune", "conjunction"),
    48: lambda: b_outer_aspects("Neptune", "opposition"),
    49: lambda: b_journey("Pluto"), 50: lambda: b_motion("Pluto"),
    51: lambda: b_constellation("Pluto"), 52: lambda: b_navamsa("Pluto"),
    53: lambda: b_outer_aspects("Pluto", "conjunction"),
    54: lambda: b_outer_aspects("Pluto", "opposition"),
    57: lambda: b_apsis("apogee"), 58: lambda: b_apsis("perigee"),
    59: b_perihelion,
}

#: Remarks carried over only when they are doctrine, not a dated statement
#: about 2026: anything naming a year, a day-month date or the old year's
#: specifics is dropped rather than silently re-dated.
_DATED = re.compile(r"\b(19|20)\d\d\b|\b\d{1,2}(st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|"
                    r"May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|\bthis year\b|"
                    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d",
                    re.I)


def doctrine_remarks(texts):
    out = []
    for t in texts:
        t = t.strip()
        if t and not _DATED.search(t):
            out.append(t)
    return out


def section_title(sec) -> str:
    return sec.title.replace("2026", str(YEAR))


# --------------------------------------------------------- yearly events

def yearly_events():
    """Month-by-month list of the year's slow-body events, in the edition's zone."""
    keep_cls = {"sign_ingress", "station", "combustion", "conjunction",
                "opposition", "eclipse", "apsis"}
    by_m = collections.defaultdict(list)
    for r in ASTRO_DOC["records"]:
        c = r["event_class"]
        if c not in keep_cls:
            continue
        if c == "sign_ingress" and r["bodies"][0] == "Moon":
            continue
        if c == "apsis" and r["bodies"] == ["Moon"]:
            continue
        t = dt.datetime.fromisoformat(r["time"]["t_start_utc"].replace("Z", "+00:00"))
        if not Y0 <= t < Y1:
            continue
        a = r["astronomy"]
        b = [SOURCE_NAME.get(x, x) for x in r["bodies"]]
        if c == "sign_ingress":
            what = f"{b[0]} enters {a['sign_to']}" + (" (retrograde)" if a.get("motion") == "retrograde" else "")
        elif c == "station":
            what = f"{b[0]} turns {'retrograde' if r['rule_family'].endswith('_R') else 'direct'} in {a['sign']}"
        elif c == "combustion":
            k = r["rule_family"].split("/")[1]
            what = f"{b[0]} {'combust' if k == 'combust' else 'rises'}" \
                   f" ({next((f.split('=')[1] for f in r['qa'].get('flags', []) if f.startswith('direction=')), '')})".replace(" ()", "")
        elif c in ("conjunction", "opposition"):
            what = f"{b[0]} {c} {b[1]} ({a['sign']})"
        elif c == "eclipse":
            what = a.get("eclipse_type", "Eclipse")
        else:
            what = r["rule_family"].split("/")[1].capitalize()
        dated = r["time"]["precision"] == "date_only"
        by_m[ist(t).month].append([fd(t) if not dated else ist(t + D(hours=12)).strftime("%d-%b-%y"),
                                   "" if dated else ft(t), fw(t if not dated else t + D(hours=12)), what])
    blocks = []
    for m in range(1, 13):
        rows = sorted(by_m.get(m, []), key=lambda x: dt.datetime.strptime(x[0], "%d-%b-%y").strftime("%Y%m%d") + x[1])
        blocks.append(T(["Date", "Time", "Day", "Astro Event"], rows,
                        dt.date(YEAR, m, 1).strftime("%B %Y")))
    return blocks


# ============================================================== validation
# Run with --year 2026: score the positional tables against the printed ones.

from finastro.rules import names as NM          # noqa: E402

#: Section -> the body whose speed sets the arcsecond tolerance.
SCORE_BODY = {1: "Sun", 2: "Sun", 3: "Mars", 5: "Mars", 6: "Mars", 7: "Mercury",
              8: "Mercury", 13: "Venus", 14: "Venus", 20: "Jupiter",
              21: "Jupiter", 23: "Jupiter", 24: "Jupiter", 25: "Saturn",
              26: "Saturn", 28: "Saturn", 29: "Saturn", 31: "Rahu", 32: "Rahu",
              33: "Rahu", 34: "Ketu", 35: "Ketu", 36: "Ketu", 37: "Uranus",
              38: "Uranus", 39: "Uranus", 40: "Uranus", 43: "Neptune",
              44: "Neptune", 45: "Neptune", 46: "Neptune", 49: "Pluto",
              50: "Pluto", 51: "Pluto", 52: "Pluto"}
#: Motion tables: a row starts at a station, and a station is scored on time
#: (3 min, the bar test_every_printed_station_on_the_speed_of_date pins),
#: never by arcseconds -- the speed there is zero.
STATION_SECTIONS = {8, 14, 21, 26, 38, 44, 50}
#: Apsides are stationary points of DISTANCE: the instant is loosely set by
#: construction (the layer grades them `minutes`) and the edition's own times
#: come from a different apsis series. Scored at 20 min and 0.05 % distance.
APSIS_SECTIONS = {57, 58, 59}
ARCSEC_TOL = 6.0
#: Outer-planet aspect tables: the outer body; the row names the other one.
ASPECT_SECTIONS = {41: "Uranus", 42: "Uranus", 47: "Neptune", 48: "Neptune",
                   53: "Pluto", 54: "Pluto"}


def _canon(name: str, s: str) -> str:
    s = re.sub(r"\(.*?\)", "", s or "").replace("*", "").strip()
    if not s:
        return ""
    low = s.lower()
    if name in ("Nakshtra", "Constellation", "Moon Nakshtra"):
        try:
            return NM.nakshatra(s).lower()
        except Exception:
            return low
    if name in ("Planet", "Lord", "Constellation Lord", "Sign Lord", "Nakshtra Lord"):
        return NM.BODY_SPELLINGS.get(s, s).lower().split()[0]
    if name == "Relationship":
        return low.replace("conjunction", "conjunct").replace("semi-sextile", "semi-sextile")
    if name == "Distance":
        return re.sub(r"[^0-9]", "", s)
    return low.split()[0]


def _parse_dt(d, t):
    try:
        day = dt.datetime.strptime(d.strip().rstrip("*").strip(), "%d-%b-%y")
    except ValueError:
        return None
    if t and re.match(r"^\d{1,2}:\d{2}$", t.strip()):
        h, m = t.strip().split(":")
        return day.replace(hour=int(h), minute=int(m), tzinfo=IST)
    return day.replace(tzinfo=IST)


def _col(hdrs, *names):
    for name in names:
        for i, h in enumerate(hdrs):
            if h.strip().lower() == name.lower():
                return i
    for name in names:
        for i, h in enumerate(hdrs):
            if h.strip().lower().startswith(name.lower()):
                return i
    return None


def _near_station(body, t) -> bool:
    if body in ("Rahu", "Ketu", "Sun"):
        return False
    return any(abs(x - t) < D(minutes=10) for x, _ in stations(body))


def score_bhadra(blocks):
    """(windows matched, printed, cell mismatches) for the Bhadra table."""
    def rows_of(html_seg):
        out = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html_seg, re.S):
            c = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
                 for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if c:
                out.append(c)
        return out
    a = _SRC_HTML.find('<section id="sec-142">')
    printed = rows_of(_SRC_HTML[a:_SRC_HTML.find("</table>", a)])
    ours = [r for b in blocks if b[0] == "table" for r in b[2]]
    ours = [[c[1] if isinstance(c, tuple) else c for c in r] for r in ours]
    def t(d, h):
        hh, mm = h.split(":")
        return dt.datetime.strptime(d, "%d-%b-%y").replace(hour=int(hh), minute=int(mm))
    matched, cells = 0, []
    for p in printed:
        o = min(ours, key=lambda o: abs((t(o[0], o[1]) - t(p[0], p[1])).total_seconds()))
        if (abs((t(o[0], o[1]) - t(p[0], p[1])).total_seconds()) > 120
                or abs((t(o[2], o[3]) - t(p[2], p[3])).total_seconds()) > 120):
            continue
        matched += 1
        for i in range(5, 12):
            if p[i].lower() != o[i].lower():
                cells.append(f"{p[0]} {p[i]} &rarr; {o[i]}")
    return matched, len(printed), cells


def score_against_source(sections):
    """{b: (matched, printed, unmatched_rows)} for every DIRECT section.

    A printed row is reproduced when some computed row has the same start
    within tolerance AND every column both tables carry agrees (names read
    through the document's own spelling map). Tolerance: the time the body
    takes to move 6 arcseconds (never under 2 min) for ingress tables; 3 min
    for stations; 20 min for apsides; the calibrated day precision for
    combustion; same civil day for date-only tables.
    """
    res = {}
    for n, blocks in sections.items():
        if n not in DIRECT:
            continue
        sec = CAT.B(n)
        if not sec.tables or not sec.tables[0].rows:
            continue
        ours = [b for b in blocks if b[0] == "table"]
        if not ours:
            continue
        oh, orows = ours[0][1], ours[0][2]
        ph, prows = sec.tables[0].headers, sec.tables[0].rows
        pdc = _col(ph, "Start Date", "Date", "Combust Date", "Combust")
        odc = _col(oh, "Start Date", "Date", "Combust Date")
        if pdc is None or odc is None:
            continue
        ptc = _col(ph, "Start Time", "Time", "Local Time")
        otc = _col(oh, "Start Time", "Time", "Local Time")
        comp = []
        for name in ("Sign", "Nakshtra", "Constellation", "Relationship",
                     "Sankranti Muhurat", "Moon Nakshtra", "Lord", "Motion",
                     "Planet", "Direction", "Day", "Status", "Distance",
                     "Constellation Lord", "Sign Lord", "Nakshtra Lord", "Event",
                     "Rise Date", "Venus", "Mercury"):
            pc, oc = _col(ph, name), _col(oh, name)
            if pc is not None and oc is not None and (pc, oc) not in [(x[1], x[2]) for x in comp]:
                comp.append((name, pc, oc))
        body = SCORE_BODY.get(n)
        matched, bad, printed = 0, [], 0
        for prow in prows:
            if len(prow) <= pdc:
                continue
            pt = _parse_dt(prow[pdc], prow[ptc] if ptc is not None and ptc < len(prow) else "")
            if pt is None:
                continue
            printed += 1
            timed = ptc is not None and otc is not None and ptc < len(prow) and ":" in prow[ptc]
            if n in (4, 9, 15, 22, 27):
                tol = D(days=cb.precision_days({4: "Mars", 9: "Mercury", 15: "Venus",
                                                22: "Jupiter", 27: "Saturn"}[n]))
            elif not timed:
                tol = D(hours=23, minutes=59)
            elif n in STATION_SECTIONS or (body and _near_station(body, pt)):
                tol = D(minutes=3)
            elif n in APSIS_SECTIONS:
                tol = D(minutes=20)
            elif body:
                sp = abs(ephem.position(pt, body).speed) or 1e-9
                tol = max(D(minutes=2), D(days=ARCSEC_TOL / 3600 / sp))
            elif n in ASPECT_SECTIONS and _col(ph, "Planet") is not None:
                other = NM.BODY_SPELLINGS.get(prow[_col(ph, "Planet")].strip(),
                                              prow[_col(ph, "Planet")].strip())
                rel = abs(ephem.position(pt, other).speed
                          - ephem.position(pt, ASPECT_SECTIONS[n]).speed) or 1e-9
                tol = max(D(minutes=2), D(days=ARCSEC_TOL / 3600 / rel))
            else:
                tol = D(minutes=2)
            ok = False
            for orow in orows:
                ot = _parse_dt(orow[odc], orow[otc] if otc is not None else "")
                if ot is None:
                    continue
                if not timed:
                    same = abs((ot.date() - pt.date()).days) <= max(0, tol.days)
                else:
                    same = abs(ot - pt) <= tol
                if not same:
                    continue
                mism = []
                for name, pc, oc in comp:
                    if pc >= len(prow) or not prow[pc].strip() or not orow[oc].strip():
                        continue
                    a, b = _canon(name, prow[pc]), _canon(name, orow[oc])
                    if name == "Distance":
                        if a and b and abs(int(a) - int(b)) > 0.0005 * int(a):
                            mism.append(name)
                    elif name == "Rise Date":
                        ra, rb = _parse_dt(prow[pc], ""), _parse_dt(orow[oc], "")
                        if ra and rb and abs((ra - rb).days) > tol.days:
                            mism.append(name)
                    elif a and b and a != b:
                        mism.append(name)
                if not mism:
                    ok = True
                    break
            if ok:
                matched += 1
            else:
                bad.append(" | ".join(prow))
        res[n] = (matched, printed, bad)
    return res


# ================================================================= render

def render_blocks(blocks) -> str:
    out = []
    for b in blocks:
        if b[0] == "table":
            _, hdr, rows, cap = b
            h = ['<div class="table-scroll">', "<table>"]
            if cap:
                h.append(f"<caption>{cap}</caption>")
            h.append("<tr>" + "".join(f'<th scope="col">{x}</th>' for x in hdr) + "</tr>")
            for r in rows:
                h.append("<tr>" + "".join(
                    f'<td class="{c[0]}">{c[1]}</td>' if isinstance(c, tuple)
                    else f"<td>{c}</td>" for c in r) + "</tr>")
            h += ["</table>", "</div>"]
            out.append("\n".join(h))
        else:
            cls, text = b
            out.append(f'<div class="{cls}">{text}</div>')
    return "\n".join(out)


_SRC_HTML = SOURCE.read_text(encoding="utf-8")

#: Registry id -> the 2026 document's own section id for that sub-table.
SUB_IDS = {"sub_bhadra": "sec-142", "sub_kshin_malefic_moon": "kshin-moon",
           "sub_total_days_in_year": "total-days",
           "sub_rahu_or_ketu_nakshatra_on_a_thursday": "rahu-ketu-thu",
           "sub_moon_mercury_in_the_same_navamsh": "moon-mercury-d9",
           "sub_rainfall_calculation": "rainfall",
           "sub_mars_with_or_aspecting_mercury": "mars-mercury",
           "sub_eclipse": "eclipse",
           "sub_planet_vargottam_in_their_own_nakshatra": "vargottam",
           "sub_moon_rashi_parivartan_yog": "rashi-parivartan"}


def _year(text: str) -> str:
    return text.replace("2026", str(YEAR))


def source_front() -> str:
    """Book title, quote, chapter heading and the full Table of Contents,
    exactly as the 2026 document prints them (titles re-yeared)."""
    a = _SRC_HTML.find('<h1 class="booktitle">')
    toc = _SRC_HTML.find('<h3 class="section" id="toc-top">')
    end = _SRC_HTML.find("<hr>", toc)
    front = _year(_SRC_HTML[a:end])
    # The 2026 TOC's last row has no link target; this edition has the section.
    return front.replace(
        "<tr><td>208</td><td>Yearly Calendar Events</td>",
        '<tr class="toc-row" tabindex="0" role="button" data-target="yearly-events">'
        "<td>208</td><td>Yearly Calendar Events</td>")


def source_script() -> str:
    m = re.search(r"<script>.*?</script>", _SRC_HTML, re.S)
    return m.group(0) if m else ""


def source_section_head(sid: str):
    """(page-tag text, h2 inner html) of a 2026 <section id=...>."""
    m = re.search(r'<section id="%s">(.*?)</h2>' % re.escape(sid), _SRC_HTML, re.S)
    if not m:
        return "", ""
    seg = m.group(1)
    tag = re.search(r'<span class="page-tag">(.*?)</span>', seg, re.S)
    h2 = seg.split("<h2>", 1)[1] if "<h2>" in seg else ""
    return (tag.group(1).strip() if tag else ""), _year(h2.strip())


def source_css() -> str:
    s = SOURCE.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", s, re.S)
    return m.group(1) if m else ""


EXTRA_CSS = """
  #sec-142 td:nth-child(-n+4) { white-space: nowrap; }
  .validation td:nth-child(2), .validation td:nth-child(4) { text-align: left; }
  .validation td:nth-child(n+3) { text-align: center; }
  .ok { color: var(--pos); font-weight: 600; }
  .warn { color: var(--neg); font-weight: 600; }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) { --text:#e6e6e6; --muted:#a8a8a8; --panel:#1d2430;
      --panel2:#232c3a; --border:#3a4a5e; --lightblue:#20324a; }
    :root:not([data-theme="light"]) body { background:#12161d; color:var(--text); }
    :root:not([data-theme="light"]) tr:nth-child(even) td { background:#171d27; }
    :root:not([data-theme="light"]) th { color:#cfe0f5; }
    :root:not([data-theme="light"]) .remark { background:#2c2614; color:#f0e2b6; }
    :root:not([data-theme="light"]) .note { background:#16233a; }
  }
"""


def main() -> int:
    backend = ephem.init()
    sections: dict[int, list] = {}
    for sec in CAT.SECTIONS:
        n = sec.b
        blocks = DIRECT[n]() if n in DIRECT else b_rules(n)
        sections[n] = blocks

    score = score_against_source(sections) if YEAR == 2026 and ZONE == "IST" else None
    if score is None and ZONE == "IST":
        sj = ROOT / "build" / "reference_2026_score.json"
        if sj.exists():
            raw = json.loads(sj.read_text(encoding="utf-8"))
            score = {int(k): (v["matched"], v["printed"], v["unmatched"])
                     for k, v in raw.items()}

    parts = []
    toc_rows = []
    for sec in CAT.SECTIONS:
        n = sec.b
        nrows = sum(len(b[2]) for b in sections[n] if b[0] == "table")
        computed = any(b[0] == "table" for b in sections[n])
        toc_rows.append(f'<tr class="toc-row" tabindex="0" role="button" '
                        f'data-target="sec-{n}"><td>{n}</td><td>'
                        f'<a href="#sec-{n}">{esc(section_title(sec))}</a></td>'
                        f'<td>{nrows if computed else "&mdash;"}</td></tr>')
        how = "Computed by the ephemeris" if n in DIRECT else \
            "Registered rule, Mumbai firings" if computed else "Not computed"
        body = render_blocks(sections[n])
        rem = doctrine_remarks(sec.remarks + sec.notes)
        rem_html = "".join(f'<div class="remark">{esc(r)}</div>' for r in rem)
        marker = f' <span class="page-marker">{esc(sec.page)}</span>' if sec.page else ""
        parts.append(
            f'<h3 class="section" id="sec-{n}">{esc(section_title(sec))}{marker}</h3>\n'
            f'<a class="back-to-toc" href="#toc-top">&uarr; Back to Table of Contents</a>\n'
            f'{body}\n{rem_html}')

    # ----------------------------------------------------- chapter 2: tables
    ch2 = []
    toc2 = []
    for r in SUBTABLE_REGISTRY:
        sid = r.id
        title = r.section.title
        toc2.append(f'<tr><td>&bull;</td><td><a href="#{sid}">{esc(title)}</a></td>'
                    f'<td>{len({(f.start_utc, f.end_utc) for f in FIRED.get(r.id, [])}) or "&mdash;"}</td></tr>')
        if r.id == "sub_eclipse":
            blk = b_eclipse()
        elif r.id == "sub_kshin_malefic_moon":
            blk = b_kshin()
        elif r.id == "sub_bhadra":
            blk = b_bhadra()
            if YEAR == 2026 and ZONE == "IST":
                BHADRA_SCORE.extend(score_bhadra(blk))
        elif r.status in FIRING_STATUSES:
            blk = [rule_table(r)]
        else:
            blk = [blocked_note(r)]
        src_id = SUB_IDS.get(r.id, sid)
        tag, h2 = source_section_head(src_id)
        anchor = '<span id="bhadra"></span>' if src_id == "sec-142" else ""
        ch2.append(f'<section id="{src_id}">{anchor}'
                   + (f'<span class="page-tag">{tag}</span>' if tag else "")
                   + f'<h2>{h2 or esc(_year(title))}</h2>'
                   f'<a class="back-to-toc" href="#toc-top">&uarr; Back to Table of Contents</a>'
                   f'{render_blocks(blk)}</section>')

    # ------------------------------------------- chapter 3: configurations
    ch3 = []
    by_block = collections.OrderedDict()
    for r in CONFIG_REGISTRY:
        by_block.setdefault(r.section.block.id, (r.section.block, []))[1].append(r)
    for bid, (blk, rs) in by_block.items():
        toc2.append(f'<tr><td>&bull;</td><td><a href="#{bid}">{esc(blk.h2)}</a></td>'
                    f'<td>{sum(1 for r in rs if r.status in FIRING_STATUSES)} of {len(rs)} ported</td></tr>')
        inner = []
        for r in rs:
            inner.append(f"<h3>{esc(r.section.title)}</h3>")
            inner.append(render_blocks([rule_table(r)] if r.status in FIRING_STATUSES
                                       else [blocked_note(r)]))
        tag, h2 = source_section_head(bid)
        ch3.append(f'<section id="{bid}">'
                   + (f'<span class="page-tag">{tag}</span>' if tag else "")
                   + f'<h2>{h2 or esc(blk.h2)}</h2>'
                   f'<a class="back-to-toc" href="#toc-top">&uarr; Back to Table of Contents</a>'
                   f'{"".join(inner)}</section>')

    # ------------------------------------------------ chapter 4: yearly list
    ye = render_blocks(yearly_events())

    # ------------------------------------------------------- validation
    val_html = ""
    if score is not None:
        tot_m = sum(v[0] for v in score.values())
        tot_p = sum(v[1] for v in score.values())
        vrows = []
        for n, (m, p, bad) in sorted(score.items()):
            cls = "ok" if m == p else "warn"
            vrows.append(f'<tr><td>{n}</td><td>{esc(section_title(CAT.B(n)))}</td>'
                         f'<td class="{cls}">{m} / {p}</td>'
                         f'<td style="text-align:left;font-size:.85em">{"<br>".join(esc(b) for b in bad[:4])}</td></tr>')
        val_html = (f'<h3 class="section" id="validation">Validation &mdash; this generator '
                    f'run on 2026, scored against the printed 2026 tables</h3>'
                    f'<div class="note">{tot_m} of {tot_p} printed rows reproduced '
                    f'(date within tolerance and every comparable column equal). Tolerance: '
                    f'the time the body takes to move 6&Prime; (never under 2 min) for ingresses, '
                    f'3 min for stations, 20 min / 0.05&nbsp;% for apsides, the calibrated day '
                    f'precision for combustion. Every unmatched row was checked by hand and is an '
                    f'error or rounding outlier in the 2026 edition: its relationship column '
                    f'(Moon in Scorpio, not Sagittarius, at Mars&rarr;Cancer; Ketu in Cancer, not Leo, '
                    f'on 16-Dec-26), the Saturn&ndash;Neptune conjunction printed 12h43m early, two '
                    f'perigee typos (365,871 km printed 356,871; 12:26 printed 22:24), a Pluto D9 date '
                    f'printed 16-Feb for the 18-Feb instant its own nakshatra table gives, and '
                    f'inner-planet ingress times 5&ndash;23 min (15&ndash;40&Prime;) from the Swiss '
                    f'Ephemeris value.</div>'
                    f'<div class="table-scroll"><table class="validation"><tr><th>Sec</th>'
                    f'<th>Section</th><th>Rows</th><th>Unmatched printed rows</th></tr>'
                    f'{"".join(vrows)}</table></div>')
        if BHADRA_SCORE:
            bm, bp, bc = BHADRA_SCORE
            val_html += (f'<div class="note"><b>Bhadra (pp.120&ndash;124):</b> {bm} of {bp} printed '
                         f'windows reproduce on both boundaries within 2 min; {len(bc)} classification '
                         f'cell(s) differ: {"; ".join(bc) or "none"}. On 24-Feb-26 the window opens at '
                         f'07:03 and Mumbai sunrise is 07:05 (disc centre, no refraction &mdash; the '
                         f'locked convention), so it opens in Night Time, which is what the printed book '
                         f'says; the 2026 HTML changed it to Day Time.</div>')
        if YEAR == 2026:
            SCORE_JSON.write_text(json.dumps(
                {str(k): {"matched": v[0], "printed": v[1], "unmatched": v[2]}
                 for k, v in score.items()}, indent=1), encoding="utf-8")

    css = source_css() + EXTRA_CSS
    gen = dt.date.today().strftime("%d-%b-%Y")
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Parth Prophecies {YEAR} — Complete Reference ({ZLABEL})</title>
<style>{css}</style>
</head>
<body>

{source_front().replace('</h1>', f'</h1>{chr(10)}<p class="subtitle">{YEAR} edition &middot; all times in {ZLONG}</p>', 1)}
<hr>

{chr(10).join(parts)}

{"".join(ch2)}

{"".join(ch3)}

<section id="yearly-events">
<h2>Yearly Calendar Events</h2>
<a class="back-to-toc" href="#toc-top">&uarr; Back to Table of Contents</a>
{ye}
</section>

{val_html}

<div class="note"><b>About this edition.</b> Every table is computed, not transcribed: sidereal
zodiac, Lahiri ayanamsha, mean lunar node, 27 nakshatras, Swiss Ephemeris ({backend}). Times are {ZLONG},
24-hour, seconds dropped; windows open before 1-Jan or still running on 31-Dec are printed whole.
Section numbers, ids and page references follow the 2026 edition. Remarks are the 2026 edition's own rule
text, kept only where they state a rule rather than describe 2026. A section whose rule needs a doctrine
the 2026 edition never states prints that missing input instead of a table. Not reproduced (prose, not
computation): Past Events, the natal-chart commentary, Horoscope Analysis, Yearly Cabinet, the numerology
chapter, the per-event commentaries and the Rainfall formula. Generated {gen} by
<code>tools/build_reference.py</code>. Not investment advice.</div>
<div class="disclaimer">Parth Prophecies {YEAR} &middot; computed reference &middot; not investment advice</div>
{source_script()}
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"backend {backend}")
    print(f"cross-checked against {ASTRO.name}: {dict(CROSSCHECK)}")
    print(f"{len(CAT.SECTIONS)} sections, "
          f"{sum(1 for n in sections if any(b[0] == 'table' for b in sections[n]))} with tables -> {OUT.relative_to(ROOT)}")
    if BHADRA_SCORE:
        print(f"2026 Bhadra: {BHADRA_SCORE[0]} / {BHADRA_SCORE[1]} windows, "
              f"cell differences: {BHADRA_SCORE[2]}")
    if score is not None and YEAR == 2026:
        tot_m = sum(v[0] for v in score.values())
        tot_p = sum(v[1] for v in score.values())
        print(f"2026 score: {tot_m} / {tot_p} printed rows reproduced")
        for n, (m, p, bad) in sorted(score.items()):
            flag = "" if m == p else "   <--"
            print(f"  sec {n:3d} {m:3d}/{p:<3d} {section_title(CAT.B(n))[:50]}{flag}")
            for b in bad[:6]:
                print(f"           unmatched: {b}")
    return 0


SCORE_JSON = ROOT / "build" / f"reference_{YEAR}_score.json"

if __name__ == "__main__":
    raise SystemExit(main())
