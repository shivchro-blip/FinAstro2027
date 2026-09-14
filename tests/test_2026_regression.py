"""Regression harness: the engine must reproduce the 2026 source.

These are not unit tests of arithmetic. They lock in the three conventions that
were reverse-engineered from Parth Prophecies 2026, so that any future change to
ayanamsha, node type, thresholds or the weekday rule fails loudly instead of
silently shifting hundreds of dates.

Run:  python3 tests/test_2026_regression.py
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from finastro import combustion as cb          # noqa: E402
from finastro import ephem, panchang as pn     # noqa: E402
from finastro.config import CONF               # noqa: E402
from finastro.timezones import IST, UTC, civil_day_bounds  # noqa: E402

Y = 2026
PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, PASS if ok else FAIL, detail))


def ist(when: dt.datetime) -> str:
    return when.astimezone(IST).strftime("%d-%b-%y %H:%M")


def d(text: str) -> dt.date:
    return dt.datetime.strptime(text, "%d-%b-%y").date()


# ------------------------------------------------------------------ 1. ayanamsha
def test_ayanamsha_and_node():
    """Source ingress times discriminate between ayanamshas by hours."""
    a = dt.datetime(Y, 1, 1, tzinfo=UTC)
    b = dt.datetime(Y + 1, 1, 1, tzinfo=UTC)

    sun_cap = [x[0] for x in ephem.ingresses("Sun", a, b) if x[2] == 9]
    record("Sun -> Capricorn = 14-Jan 15:08 IST (source)",
           len(sun_cap) == 1 and ist(sun_cap[0]).startswith("14-Jan-26 15:0"),
           ist(sun_cap[0]) if sun_cap else "not found")

    mars_cap = [x[0] for x in ephem.ingresses("Mars", a, b) if x[2] == 9]
    record("Mars -> Capricorn = 16-Jan 04:29 IST (source)",
           len(mars_cap) == 1 and ist(mars_cap[0]).startswith("16-Jan-26 04:2"),
           ist(mars_cap[0]) if mars_cap else "not found")

    rahu = ephem.ingresses("Rahu", a, b)
    record("Rahu -> Capricorn in Dec (mean node, not true)",
           len(rahu) == 1 and ist(rahu[0][0]).startswith("05-Dec-26"),
           ist(rahu[0][0]) if rahu else "not found")

    shravana = [x[0] for x in
                ephem.ingresses("Sun", a, dt.datetime(Y, 2, 1, tzinfo=UTC), 360 / 27)
                if x[2] == 21]
    record("Sun -> Shravana = 24-Jan 10:51 IST (source, 27-nakshatra)",
           len(shravana) == 1 and ist(shravana[0]).startswith("24-Jan-26 10:5"),
           ist(shravana[0]) if shravana else "not found")


# ------------------------------------------------------------------ 2. stations
#: Verbatim from "Mercury Motion pp.8-9" of the source, times included.
SOURCE_MERCURY_STATIONS = [
    ("26-Feb-26 12:19", "R"), ("21-Mar-26 01:04", "D"),
    ("29-Jun-26 23:07", "R"), ("24-Jul-26 04:29", "D"),
    ("24-Oct-26 12:44", "R"), ("13-Nov-26 21:25", "D"),
]


def test_stations():
    a = dt.datetime(Y, 1, 1, tzinfo=UTC)
    b = dt.datetime(Y + 1, 1, 1, tzinfo=UTC)
    got = [(ist(t), k) for t, k in ephem.stations("Mercury", a, b)]
    record("Mercury: six stations, dates match source",
           [x[0][:9] for x in got] == [x[0][:9] for x in SOURCE_MERCURY_STATIONS],
           str([x[0] for x in got]))

    # A station is where speed passes through zero, so longitude is stationary
    # to second order and a sub-arcsecond ephemeris difference moves the clock
    # time by minutes. Five minutes is the honest agreement bar here, not a
    # concession -- the source's own slow-planet stations drift by up to an hour.
    deltas = [abs((dt.datetime.strptime(g, "%d-%b-%y %H:%M")
                   - dt.datetime.strptime(w, "%d-%b-%y %H:%M")).total_seconds()) / 60
              for (g, _), (w, _) in zip(got, SOURCE_MERCURY_STATIONS)]
    record("Mercury: station times within 5 minutes of source",
           max(deltas) <= 5, f"max delta {max(deltas):.0f} min")


# ---------------------------------------------------------------- 3. total days
SOURCE_TOTAL_DAYS = ["25-Jan-26", "24-Feb-26", "23-Mar-26", "22-Apr-26",
                     "21-May-26", "20-Jun-26", "19-Jul-26", "18-Aug-26",
                     "17-Sep-26", "16-Oct-26", "15-Nov-26", "14-Dec-26"]


def test_total_days():
    got = pn.total_days(Y)
    want = [d(x) for x in SOURCE_TOTAL_DAYS]
    record("Total Days: dd + mm == yy reproduces 12/12",
           got == want, f"{len(set(got) & set(want))}/12 matched")


# ---------------------------------------------------------------- 4. combustion
SOURCE_COMBUSTION = {
    "Mercury": [("02-Jan-26", "combust"), ("04-Feb-26", "rise"),
                ("01-Mar-26", "combust"), ("14-Mar-26", "rise"),
                ("01-May-26", "combust"), ("23-May-26", "rise"),
                ("03-Jul-26", "combust"), ("21-Jul-26", "rise"),
                ("18-Aug-26", "combust"), ("12-Sep-26", "rise"),
                ("28-Oct-26", "combust"), ("10-Nov-26", "rise"),
                ("14-Dec-26", "combust")],
    "Venus":   [("01-Feb-26", "rise"), ("15-Oct-26", "combust"),
                ("27-Oct-26", "rise")],
    "Mars":    [("10-Apr-26", "rise")],
    "Jupiter": [("16-Jul-26", "combust"), ("10-Aug-26", "rise")],
    "Saturn":  [("11-Mar-26", "combust"), ("15-Apr-26", "rise")],
}
#: Not arbitrary slack. Each body's calibration scatter divided by its daily
#: rate of change in kalamsha, recorded in config as precision_days.
TOLERANCE_DAYS = {b: cb.precision_days(b) for b in SOURCE_COMBUSTION}


def test_combustion():
    for body, expected in SOURCE_COMBUSTION.items():
        events = cb.find_events(body, dt.date(Y, 1, 1), dt.date(Y, 12, 31))
        found = {(e.instant.date(), e.kind) for e in events}
        hits, misses = 0, []
        for text, kind in expected:
            want = d(text)
            near = any(abs((fd - want).days) <= TOLERANCE_DAYS[body] and fk == kind
                       for fd, fk in found)
            hits += near
            if not near:
                misses.append(f"{text} {kind}")
        record(f"Combustion {body}: kalamsha reproduces source "
               f"(+/-{TOLERANCE_DAYS[body]}d)",
               hits == len(expected),
               f"{hits}/{len(expected)}" + (f" missed {misses}" if misses else ""))


# ------------------------------------------------------------- 5. weekday rule
SOURCE_WEEKDAY_RULES = {
    "Ekadashi on Friday": (
        pn.tithi_is(11, 26), {4},
        ["13-Feb-26", "27-Feb-26", "10-Jul-26", "24-Jul-26", "20-Nov-26",
         "04-Dec-26"]),
    "Mrigashira on Thursday": (
        pn.nakshatra_is("Mrigashira"), {3},
        ["01-Jan-26", "29-Jan-26", "26-Feb-26", "29-Oct-26", "26-Nov-26",
         "24-Dec-26"]),
    "Vyatipata on Tue/Sat/Sun": (
        pn.yoga_is("Vyatipata"), {1, 5, 6},
        ["20-Jan-26", "15-Feb-26", "07-Apr-26", "02-May-26", "21-Jun-26",
         "11-Aug-26", "06-Sep-26", "27-Oct-26", "22-Nov-26"]),
    "Shatabhisha on Tuesday": (
        pn.nakshatra_is("Shatabhisha"), {1},
        ["17-Mar-26", "14-Apr-26", "15-Dec-26"]),
    "Uttara Ashadha on Monday": (
        pn.nakshatra_is("Uttara Ashadha"), {0},
        ["19-Jan-26", "24-Aug-26", "21-Sep-26", "19-Oct-26"]),

    # ------------------------------------------------ transcribed to close G-4
    # The five families above were the original sample. The seven below are the
    # rest of the document's weekday-conditioned per-date tables, transcribed
    # row for row so the convention is locked against all of them and not a
    # third of them. Section titles quoted exactly as printed.

    # "Ashtami on Tuesday / Saturday - Bullish p.62".
    # The TITLE says Tuesday/Saturday; the table's own Day column also prints
    # two Sundays (11-Jan, 10-May). The weekday set here is read off the rows
    # the source actually prints, not off its title -- recorded as a source
    # inconsistency rather than silently narrowed.
    #
    # Two earlier claims in this comment were wrong and are corrected here.
    # The table is NOT sheared: it has five headers and five cells per row, and
    # every printed weekday matches the true weekday of its printed date. The
    # third column, headed "Monday", is data -- the following Monday the table's
    # note calls bullish -- and it is filled on the Saturday and Sunday rows
    # only. Both Sunday rows are the second civil day of a Saturday-Sunday
    # Ashtami run whose Saturday this fixture counts as an extra (10-Jan with
    # 11-Jan, 09-May with 10-May). {6} must stay in the weekday set below:
    # narrowing to the title's {1, 5} cannot emit a Sunday at all, so it loses
    # both printed Sunday rows outright and is refuted by them. See
    # weekday_rule.extras.p62_reread in config.
    "Ashtami on Tuesday/Saturday/Sunday (p.62)": (
        pn.tithi_is(8, 23), {1, 5, 6},
        ["11-Jan-26", "24-Feb-26", "10-May-26", "23-May-26", "21-Jul-26",
         "19-Sep-26", "03-Oct-26", "17-Nov-26", "01-Dec-26"]),

    # "Ashtami on Monday, Thursday and Friday - Bearish p.63".
    # Together with the row above these two tables cover Ashtami on six of the
    # seven weekdays -- every day but Wednesday.
    "Ashtami on Monday/Thursday/Friday (p.63)": (
        pn.tithi_is(8, 23), {0, 3, 4},
        ["26-Jan-26", "09-Feb-26", "26-Mar-26", "10-Apr-26", "24-Apr-26",
         "08-Jun-26", "22-Jun-26", "20-Aug-26", "04-Sep-26", "02-Nov-26",
         "17-Dec-26", "31-Dec-26"]),

    # "Shukla Pratipada on Saturday / Sunday - Three Days Bullish p.77"
    "Shukla Pratipada on Saturday/Sunday (p.77)": (
        pn.tithi_is(1), {5, 6},
        ["18-Apr-26", "17-May-26", "12-Sep-26", "11-Oct-26"]),

    # "Shukla Shasthi on a Friday - Bearish p.80"
    "Shukla Shasthi on Friday (p.80)": (
        pn.tithi_is(6), {4},
        ["19-Jun-26"]),

    # "Anuradha on Sunday - Bearish p.80"
    "Anuradha on Sunday (p.80)": (
        pn.nakshatra_is("Anuradha"), {6},
        ["31-May-26", "28-Jun-26"]),

    # "Shukla Trayodashi on Tuesday or Saturday - Bearish p.86"
    "Shukla Trayodashi on Tuesday/Saturday (p.86)": (
        pn.tithi_is(13), {1, 5},
        ["31-Jan-26", "31-Mar-26", "28-Apr-26", "27-Jun-26", "25-Aug-26",
         "24-Oct-26", "22-Dec-26"]),

    # "Mangal Ashwini Yog - Bullish (Ashwini Nakshtra on Tuesday) p.61"
    "Ashwini on Tuesday (p.61)": (
        pn.nakshatra_is("Ashwini"), {1},
        ["01-Sep-26"]),
}

#: Weekday-bearing tables deliberately NOT transcribed above, each with the
#: reason. Listed so "all weekday rules are locked" is a checkable claim rather
#: than an impression, and so a later reader does not think they were missed.
WEEKDAY_TABLES_NOT_FIXTURED = {
    "Moon Eclipse on Tuesday - Bullish p.87":
        "1 row (03-Mar-26). The condition is an eclipse, not a tithi, nakshatra "
        "or yoga, so it cannot be expressed as a panchang predicate and needs "
        "the eclipse class instead.",
    "Moon in Mrigsira on Monday - Bullish p.78":
        "2 rows, but they are the START and END of one window (18-May-26 11:33 "
        "Starts, 15-Jun-26 19:10 Ends), not qualifying Mondays. Different "
        "shape; already carried in config's rule_layer_pending.",
    "Three Saturday in Shukla Paksh - Bearish p.80":
        "1 row, a date RANGE (12-Sep-26 to 26-Sep-26) counting Saturdays "
        "within a paksha. Not a per-date qualifying rule.",
    "Shukla Ekadashi Vyatipath or Vaidhrati Yog - Bearish p.85":
        "1 row (27-May-26 Wednesday). The Day column is descriptive: no "
        "weekday conditions the rule, so it is not a weekday rule.",
    "Tithi lesser than Chaturdashi - Bearish p.84":
        "4 rows carrying a Weekday column, but the weekday is reported and not "
        "required. Also contains the 28-Mar-25 year typo.",
}


#: Printed rows that NO day convention can reproduce, because the condition does
#: not occur on the printed weekday at all. Not a convention failure and not
#: slack: each is asserted as a defect in its own right below, so the row cannot
#: quietly disappear from the count.
WEEKDAY_SOURCE_DEFECTS = {
    "Anuradha on Sunday (p.80)": {
        "28-Jun-26": "the Moon is in Jyeshtha for the whole of 28-Jun-26. "
                     "Anuradha runs 26-Jun-26 19:16 Fri to 27-Jun-26 22:11 Sat "
                     "and never touches a Sunday, so the qualifying day is "
                     "Saturday 27-Jun and the rule cannot fire at all. The "
                     "printed row is one day late -- the same off-by-one-day "
                     "class as the p.133 appendix rows.",
    },
}


def test_weekday_convention():
    total_want = total_hit = 0
    for name, (cond, days, expected) in SOURCE_WEEKDAY_RULES.items():
        hits = pn.evaluate_weekday_rule(cond, days, Y, "mumbai")
        got = {h.day for h in hits}
        defects = {d(x) for x in WEEKDAY_SOURCE_DEFECTS.get(name, {})}
        want = {d(x) for x in expected} - defects
        total_want += len(want)
        total_hit += len(want & got)
        record(f"Weekday rule '{name}'", want <= got,
               f"{len(want & got)}/{len(want)} source rows reproduced, "
               f"{len(got - want)} additional"
               + (f", {len(defects)} excluded as a source defect"
                  if defects else ""))
    record("Weekday convention: civil-day overlap covers the source",
           total_hit == total_want,
           f"{total_hit}/{total_want} printed rows across "
           f"{len(SOURCE_WEEKDAY_RULES)} weekday-conditioned families")


def test_weekday_source_defects():
    """Each excluded row is asserted as a defect, not merely skipped.

    The claim is stronger than "our convention misses it": the condition is
    absent for the entire printed day, so no day convention -- sunrise,
    civil-day, sunrise-to-sunrise or session -- could produce the row.
    """
    for name, rows in WEEKDAY_SOURCE_DEFECTS.items():
        cond, days, _ = SOURCE_WEEKDAY_RULES[name]
        for text in rows:
            day = d(text)
            lo, hi = civil_day_bounds(day, IST)
            step = dt.timedelta(minutes=10)
            when, holds = lo, False
            while when <= hi and not holds:
                holds = cond(when)
                when += step
            record(f"Source defect: {name} {text} cannot hold under ANY "
                   f"day convention", not holds,
                   "condition absent for the entire civil day, so sunrise, "
                   "civil-day and sunrise-to-sunrise all agree it is not a "
                   "qualifying day")


# ------------------------------------------------------------------ 6. spans
def test_source_span_times():
    """The source's From/Till annotations are civil-day span boundaries."""
    checks = [
        ("Mrigashira Thu 01-Jan From 22:50", pn.nakshatra_is("Mrigashira"),
         {3}, "01-Jan-26", "start", "22:50"),
        ("Vyatipata 07-Apr Till 16:17", pn.yoga_is("Vyatipata"),
         {1, 5, 6}, "07-Apr-26", "end", "16:17"),
        ("Vyatipata 15-Feb From 03:18", pn.yoga_is("Vyatipata"),
         {1, 5, 6}, "15-Feb-26", "start", "03:18"),
    ]
    TOL_MIN = 3
    for label, cond, days, day_text, which, want in checks:
        hits = [h for h in pn.evaluate_weekday_rule(cond, days, Y, "mumbai")
                if h.day == d(day_text)]
        if not hits:
            record(f"Span: {label}", False, "day not found")
            continue
        got = hits[0].start if which == "start" else hits[0].end
        if got is None:
            record(f"Span: {label}", False, "condition spans the whole day")
            continue
        local = got.astimezone(IST)
        want_dt = local.replace(hour=int(want[:2]), minute=int(want[3:]),
                                second=0, microsecond=0)
        delta = abs((local - want_dt).total_seconds()) / 60
        record(f"Span: {label}", delta <= TOL_MIN,
               f"computed {local.strftime('%H:%M')}, delta {delta:.0f} min")


# -------------------------------------------------------------- 7. New York
def test_new_york_divergence():
    """Separate NY evaluation must actually differ, or the second location is
    pointless. 2026 baseline across five rules."""
    diverged = 0
    for name, (cond, days, _) in SOURCE_WEEKDAY_RULES.items():
        mum = {h.day for h in pn.evaluate_weekday_rule(cond, days, Y, "mumbai")}
        nyc = {h.day for h in pn.evaluate_weekday_rule(cond, days, Y, "new_york")}
        diverged += len(mum ^ nyc)
    record("New York evaluated separately produces distinct dates",
           diverged > 0, f"{diverged} dates differ across 5 rules")


# ------------------------------------------------------- 8. dignity frame
#: Every dignity label the 2026 source prints in a Navmansh (D9) table, with the
#: window it prints it against. These are the rows that put Jupiter and Saturn
#: into the config dignity block, and they are read off the D9 sign, not the
#: rashi sign. Transcribed from the source exactly as printed:
#:
#:   Jupiter in Navmansh (D9) p.22
#:   Saturn in Navmansh (D9) p.25
#:
#: The point of the test is not that the scheme is Parashari -- that is asserted
#: elsewhere -- but that the FRAME is navamsa. If dignity is ever computed from
#: the rashi sign on a D9 record, four of these five rows break.
SOURCE_D9_DIGNITY_ROWS = [
    ("Jupiter", "Cancer",      ["exalted"],       "02-Jun-26 01:49", "18-Jun-26 20:59"),
    ("Jupiter", "Sagittarius", ["own", "trine"],  "19-Aug-26 03:13", "03-Sep-26 18:33"),
    ("Jupiter", "Capricorn",   ["debilitated"],   "03-Sep-26 18:33", "20-Sep-26 08:17"),
    ("Jupiter", "Pisces",      ["own"],           "08-Oct-26 18:32", "31-Oct-26 12:02"),
    ("Saturn",  "Capricorn",   ["own"],           "02-Jul-26 05:58", "27-Jul-26 01:27"),
]

#: The one row that cannot separate the frames. The source labels it Vargottam
#: itself: rashi and navamsa are the same sign there, so both frames answer
#: Exalted and the row is evidence for neither. Named here so it is visibly
#: excluded from the discriminating count rather than quietly inflating it.
VARGOTTAM_ROW = ("Jupiter", "Cancer")


def _at(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, "%d-%b-%y %H:%M").replace(tzinfo=IST)


def test_dignity_frame_is_navamsa():
    """The D9 labels reproduce from the navamsa sign and not from the rashi one.

    Read at the midpoint of each printed window, so the answer cannot come from
    a boundary instant landing either side of a cusp.
    """
    reproduced = rashi_would_match = 0
    discriminating = 0
    for body, sign, states, start, end in SOURCE_D9_DIGNITY_ROWS:
        a, z = _at(start), _at(end)
        p = ephem.position(a + (z - a) / 2, body)
        nav_ok = p.navamsa == sign and ephem.dignity_states(body, sign) == states
        rashi_states = ephem.dignity_states(body, p.sign)
        record(f"D9 {body} {sign} ({', '.join(states)}) reproduces from navamsa",
               nav_ok, f"navamsa={p.navamsa}, rashi={p.sign}")
        reproduced += nav_ok
        if rashi_states == states:
            rashi_would_match += 1
        else:
            discriminating += 1

    # Saturn is the decisive one: "Saturn remains in Pisces throughout the year"
    # (Journey of Saturn p.23), and Pisces carries Saturn no dignity at all, so
    # the rashi frame would have printed that row blank.
    sat = ephem.position(_at("14-Jul-26 00:00"), "Saturn")
    record("Saturn's rashi sign is Pisces while its D9 sign is Capricorn (Own)",
           sat.sign == "Pisces" and sat.navamsa == "Capricorn"
           and ephem.dignity_states("Saturn", "Pisces") == []
           and ephem.dignity_states("Saturn", "Capricorn") == ["own"],
           f"rashi={sat.sign}, navamsa={sat.navamsa}")

    record("All 5 printed D9 dignity rows reproduce from the navamsa sign",
           reproduced == len(SOURCE_D9_DIGNITY_ROWS),
           f"{reproduced}/{len(SOURCE_D9_DIGNITY_ROWS)}")
    record("The rashi frame reproduces only the Vargottam row, so the frames "
           "are distinguishable",
           rashi_would_match == 1 and discriminating == 4,
           f"{rashi_would_match}/5 match under rashi, {discriminating} rows "
           f"discriminate; the match is {VARGOTTAM_ROW[0]} in "
           f"{VARGOTTAM_ROW[1]}, labelled Vargottam by the source")


# ---------------------------------------------------------- 9. vargottama
#: Every row in the 2026 source that prints the word "Vargottam" against a sign,
#: across all three surfaces that carry one. Transcribed as printed.
#:
#:   Vargottam Mars p.7 (its own section, not a journey table)
#:   Mars in Pisces Navmansh (D9) p.6
#:   Jupiter in Navmansh (D9) p.22
#:   Rahu in Navmansh (D9) p.28 / Ketu in Navmansh (D9) p.30
#:
#: The word appears in no "Journey of X" rashi table anywhere in the document.
SOURCE_VARGOTTAMA_ROWS = [
    ("Mars", "Sagittarius", "11-Jan-26 21:11", "16-Jan-26 04:29", "Vargottam Mars p.7"),
    ("Mars", "Capricorn",   "16-Jan-26 04:29", "20-Jan-26 11:26", "Vargottam Mars p.7"),
    ("Mars", "Aquarius",    "12-Mar-26 10:00", "16-Mar-26 15:37", "Vargottam Mars p.7"),
    ("Mars", "Pisces",      "07-May-26 03:27", "11-May-26 12:39", "Vargottam Mars p.7"),
    ("Mars", "Aries",       "11-May-26 12:39", "15-May-26 22:17", "Vargottam Mars p.7"),
    ("Mars", "Taurus",      "09-Jul-26 17:25", "14-Jul-26 11:48", "Vargottam Mars p.7"),
    ("Mars", "Gemini",      "13-Sep-26 05:36", "18-Sep-26 16:36", "Vargottam Mars p.7"),
    ("Mars", "Cancer",      "18-Sep-26 16:36", "24-Sep-26 05:40", "Vargottam Mars p.7"),
    ("Mars", "Leo",         "19-Dec-26 10:21", "31-Dec-26 23:59", "Vargottam Mars p.7"),
    ("Mars", "Pisces",      "07-May-26 03:27", "11-May-26 12:39", "Mars in Pisces Navmansh D9 p.6"),
    ("Jupiter", "Gemini",   "01-Jan-26 00:01", "04-Jan-26 18:55", "Jupiter D9 p.22"),
    ("Jupiter", "Gemini",   "14-May-26 06:26", "02-Jun-26 01:49", "Jupiter D9 p.22"),
    ("Jupiter", "Cancer",   "02-Jun-26 01:49", "18-Jun-26 20:59", "Jupiter D9 p.22"),
    ("Rahu", "Aquarius",    "25-Jan-26 09:39", "29-Mar-26 07:11", "Rahu D9 p.28"),
    ("Ketu", "Leo",         "25-Jan-26 09:39", "29-Mar-26 07:11", "Ketu D9 p.30"),
]

#: "Planet Vargottam in Their Own Nakshatra" p.133. A narrower set, not a second
#: rule: vargottama AND the planet in a nakshatra it lords. Four rows carry an
#: end DATE one day late -- their end TIMES are right to within two minutes --
#: so the harness asserts the state at the START of every row and at the printed
#: midpoint only for the fifteen rows whose end is sound. Config records the four
#: under vargottama.source_defects.
APPENDIX_ROWS = [
    ("Moon", "Rohini",          "01-Jan-26 06:52", "01-Jan-26 12:10", True),
    ("Rahu", "Shatabhisha",     "25-Jan-26 09:39", "29-Mar-26 07:11", True),
    ("Moon", "Rohini",          "28-Jan-26 15:00", "29-Jan-26 20:33", False),
    ("Moon", "Rohini",          "24-Feb-26 20:46", "25-Feb-26 02:24", True),
    ("Moon", "Rohini",          "24-Mar-26 02:25", "24-Mar-26 07:57", True),
    ("Moon", "Rohini",          "20-Apr-26 09:59", "21-Apr-26 15:20", False),
    ("Mercury", "Revati",       "28-Apr-26 10:43", "30-Apr-26 01:46", True),
    ("Jupiter", "Punarvasu",    "14-May-26 06:26", "02-Jun-26 01:49", True),
    ("Moon", "Rohini",          "17-May-26 19:49", "18-May-26 01:03", True),
    ("Jupiter", "Punarvasu",    "02-Jun-26 01:49", "18-Jun-26 20:59", True),
    ("Moon", "Rohini",          "14-Jun-26 06:33", "14-Jun-26 11:49", True),
    ("Moon", "Rohini",          "11-Jul-26 16:28", "12-Jul-26 21:50", False),
    ("Venus", "Purva Phalguni", "16-Jul-26 19:08", "19-Jul-26 22:28", True),
    ("Moon", "Rohini",          "08-Aug-26 00:17", "08-Aug-26 05:50", True),
    ("Moon", "Rohini",          "04-Sep-26 06:09", "04-Sep-26 11:48", True),
    ("Moon", "Rohini",          "01-Oct-26 11:39", "02-Oct-26 17:15", False),
    ("Moon", "Rohini",          "28-Oct-26 18:55", "29-Oct-26 00:20", True),
    ("Moon", "Rohini",          "25-Nov-26 04:45", "25-Nov-26 10:03", True),
    ("Moon", "Rohini",          "22-Dec-26 16:08", "22-Dec-26 21:24", True),
]

#: Nakshatra lords, needed only to check the appendix's own-nakshatra filter.
#: Vimshottari order, repeating every nine nakshatras.
NAK_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
             "Jupiter", "Saturn", "Mercury"]

YEAR_START = dt.datetime(2026, 1, 1, tzinfo=IST)
YEAR_END = dt.datetime(2027, 1, 1, tzinfo=IST)


def _varg(when: dt.datetime, body: str) -> bool:
    p = ephem.position(when, body)
    return ephem.vargottama(p.sign, p.navamsa)


def test_vargottama_is_d1_equals_d9():
    """Every printed vargottama row reproduces as rashi sign == navamsa sign.

    Discriminating in the same way as the dignity frame test: a row supports the
    rule only if the rule is capable of being false there, so the harness also
    checks the state immediately OUTSIDE each window. A rule that fired
    everywhere would pass the inside check and fail the outside one.
    """
    inside = outside = matched_sign = 0
    cannot_discriminate = []
    # A row's opening boundary can only discriminate if vargottama was false on
    # the other side of it. Two kinds of row cannot: one that opens at the start
    # of the year, with nothing printed before it, and one that opens exactly
    # where the same planet's previous vargottama row closes. The second kind is
    # not a defect but the rule working -- leaving a dual sign's LAST navamsa and
    # entering a movable sign's FIRST keeps D1 == D9 across the cusp, which is
    # why Vargottam Mars p.7 runs Pisces straight into Aries at 11-May-26 12:39.
    contiguous = {(b, st) for b, _s, st, _e, _x in SOURCE_VARGOTTAMA_ROWS
                  for b2, _s2, _st2, e2, _x2 in SOURCE_VARGOTTAMA_ROWS
                  if b2 == b and e2 == st}
    for body, sign, start, end, _sec in SOURCE_VARGOTTAMA_ROWS:
        a, z = _at(start), _at(end)
        p = ephem.position(a + (z - a) / 2, body)
        ok = ephem.vargottama(p.sign, p.navamsa)
        inside += ok
        matched_sign += ok and p.sign == sign
        if start.startswith("01-Jan-26"):
            cannot_discriminate.append(f"{body} {sign} opens at year start")
            outside += 1
        elif (body, start) in contiguous:
            cannot_discriminate.append(
                f"{body} {sign} continues the previous window")
            outside += 1
        elif not _varg(a - dt.timedelta(minutes=2), body):
            outside += 1
    record("All 15 printed vargottama rows are D1 == D9 at their midpoint",
           inside == len(SOURCE_VARGOTTAMA_ROWS),
           f"{inside}/{len(SOURCE_VARGOTTAMA_ROWS)}")
    record("...and the sign each row prints is that shared sign",
           matched_sign == len(SOURCE_VARGOTTAMA_ROWS),
           f"{matched_sign}/{len(SOURCE_VARGOTTAMA_ROWS)}")
    record("Vargottama is false immediately before each window that can "
           "discriminate",
           outside == len(SOURCE_VARGOTTAMA_ROWS),
           f"{len(SOURCE_VARGOTTAMA_ROWS) - len(cannot_discriminate)}/"
           f"{len(SOURCE_VARGOTTAMA_ROWS)} discriminate; cannot: "
           + "; ".join(cannot_discriminate))


def test_vargottama_is_not_always_true():
    """Non-vacuity. If D1 == D9 were common the checks above would prove little.

    Sampled six-hourly across 2026 for the five planets the source shows in a
    vargottama state at all.
    """
    total = hits = 0
    per = {}
    for body in ("Mars", "Jupiter", "Moon", "Mercury", "Venus"):
        n = k = 0
        t = YEAR_START
        while t < YEAR_END:
            n += 1
            k += _varg(t, body)
            t += dt.timedelta(hours=6)
        per[body] = f"{k}/{n}"
        total += n
        hits += k
    record("Vargottama is a minority state, so the row checks discriminate",
           0 < hits < total / 4,
           f"{hits}/{total} samples true; "
           + ", ".join(f"{b} {v}" for b, v in per.items()))

    # Saturn is the strongest control: the source never prints it vargottama and
    # it never can be, because its rashi sign is Pisces for the whole year.
    t, sat = YEAR_START, 0
    while t < YEAR_END:
        sat += _varg(t, "Saturn")
        t += dt.timedelta(hours=6)
    record("Saturn is never vargottama in 2026, matching its absence from the "
           "source", sat == 0, f"{sat} of 1460 samples true")


def test_vargottama_appendix_own_nakshatra():
    """The p.133 appendix is vargottama intersected with own-nakshatra, not a
    second definition of vargottama."""
    varg = own = mid_n = 0
    for body, nak, start, end, end_sound in APPENDIX_ROWS:
        a, z = _at(start), _at(end)
        # Midpoints, as everywhere else -- but of the CORRECTED window. Four end
        # dates are a day late (config.vargottama.source_defects), and a midpoint
        # taken from the printed end would land outside the real window. The
        # correction is the documented defect, not a fitted adjustment: it is
        # the same minus-one-day for all four, and their end times are untouched.
        if not end_sound:
            z -= dt.timedelta(days=1)
            mid_n += 1
        p = ephem.position(a + (z - a) / 2, body)
        varg += ephem.vargottama(p.sign, p.navamsa)
        lord = NAK_LORDS[ephem.NAKSHATRAS.index(p.nakshatra) % 9]
        own += (p.nakshatra == nak and lord == body)
    record("All 19 appendix rows are vargottama at their midpoint",
           varg == len(APPENDIX_ROWS),
           f"{varg}/{len(APPENDIX_ROWS)}, {mid_n} using the corrected end date")
    record("All 19 appendix rows have the planet in a nakshatra it lords",
           own == len(APPENDIX_ROWS),
           f"{own}/{len(APPENDIX_ROWS)}; this is the appendix's extra filter, "
           f"not part of the vargottama rule")

    # The four rows config records as defective: end TIME right, end DATE a day
    # late. Asserted as a defect so a later fix to the transcription is caught.
    bad = [("Moon", "28-Jan-26 15:00", "29-Jan-26 20:33"),
           ("Moon", "20-Apr-26 09:59", "21-Apr-26 15:20"),
           ("Moon", "11-Jul-26 16:28", "12-Jul-26 21:50"),
           ("Moon", "01-Oct-26 11:39", "02-Oct-26 17:15")]
    confirmed = 0
    for body, start, printed_end in bad:
        a = t = _at(start)
        while t < a + dt.timedelta(hours=40):
            if not _varg(t, body):
                break
            t += dt.timedelta(minutes=1)
        pe = _at(printed_end)
        confirmed += abs((pe - dt.timedelta(days=1) - t).total_seconds()) <= 120
    record("4 appendix end dates are one day late with the time intact",
           confirmed == 4, f"{confirmed}/4 reproduce as a date typo")


def test_vargottama_is_not_a_dignity():
    """The source prints both at once -- Cancer (Exalted, Vargottam) -- so the
    engine must not have folded one into the other."""
    p = ephem.position(_at("10-Jun-26 00:00"), "Jupiter")
    record("Jupiter's Cancer window is exalted AND vargottam, both states",
           ephem.dignity_states("Jupiter", p.navamsa) == ["exalted"]
           and ephem.vargottama(p.sign, p.navamsa),
           f"D1={p.sign}, D9={p.navamsa}")
    record("vargottama never appears inside a dignity state list",
           all("vargottam" not in state
               for body in ephem.CONF["dignity"]["signs"]
               for sign in ephem.SIGNS
               for state in (ephem.dignity_states(body, sign) or [])), "")


# --------------------------------------------------------- 10. Bhadra (Vishti)
#: The 2026 document prints its Bhadra windows twice, and the two printings
#: disagree on one row. The dedicated section ("Bhadra -- verified against Swiss
#: Ephemeris" pp.120-124) states its own method, quoted:
#:
#:   "A Bhadra (Vishti karana) is a 6 degree step of Moon-Sun elongation, so the
#:    eight windows of each lunar month fall on karana numbers 8, 15, 22, 29, 36,
#:    43, 50 and 57. Boundaries were found by bisection on the exact 6 degree
#:    multiples; all times are IST."
#:
#: That method is implemented here rather than trusted, and both printings are
#: checked against it. Note that elongation is a DIFFERENCE of two longitudes,
#: so the ayanamsha cancels and this computation is identical in the sidereal and
#: tropical frames -- it cannot be moved by a frame choice.
VISHTI_KARANAS = (8, 15, 22, 29, 36, 43, 50, 57)

#: "Bhadra" pp.120-124, all eight January windows as printed.
SOURCE_BHADRA_SECTION = [
    ("02-Jan-26 18:54", "03-Jan-26 05:12"), ("05-Jan-26 20:54", "06-Jan-26 08:02"),
    ("09-Jan-26 07:06", "09-Jan-26 19:40"), ("13-Jan-26 02:00", "13-Jan-26 15:18"),
    ("16-Jan-26 22:22", "17-Jan-26 11:16"), ("22-Jan-26 14:41", "23-Jan-26 02:29"),
    ("25-Jan-26 23:11", "26-Jan-26 10:17"), ("29-Jan-26 03:17", "29-Jan-26 13:56"),
]
#: "JANUARY 2026 EVENTS" pg.270-271. Only four of the eight appear at all.
SOURCE_BHADRA_MONTHLY = [
    ("09-Jan-26 07:06", "09-Jan-26 19:39"), ("13-Jan-26 03:59", "13-Jan-26 15:18"),
    ("22-Jan-26 14:42", "23-Jan-26 02:29"), ("29-Jan-26 03:18", "29-Jan-26 13:57"),
]


def _elongation(when: dt.datetime) -> float:
    return (ephem.position(when, "Moon").lon
            - ephem.position(when, "Sun").lon) % 360.0


def _karana_index(when: dt.datetime) -> int:
    """1-60 within the lunation. Karana n spans [(n-1)*6, n*6) degrees."""
    return int(_elongation(when) // 6.0) + 1


def _bisect_elongation(target_deg: float, lo: dt.datetime,
                       hi: dt.datetime) -> dt.datetime:
    """The instant elongation crosses an exact 6-degree multiple."""
    def f(when: dt.datetime) -> float:
        return (_elongation(when) - target_deg + 180.0) % 360.0 - 180.0
    a, b = lo, hi
    for _ in range(60):
        m = a + (b - a) / 2
        if f(a) * f(m) <= 0:
            b = m
        else:
            a = m
    return a + (b - a) / 2


def _vishti_windows(start: dt.datetime, end: dt.datetime):
    """Every Vishti window opening in [start, end), by the stated method."""
    out, when = [], start
    step = dt.timedelta(minutes=20)
    previous = _karana_index(when)
    while when < end:
        when += step
        k = _karana_index(when)
        if k != previous and k in VISHTI_KARANAS:
            opened = _bisect_elongation((k - 1) * 6.0, when - step, when)
            walk = when
            while _karana_index(walk) == k:
                walk += step
            closed = _bisect_elongation(k * 6.0, walk - step, walk)
            out.append((k, opened, closed))
        previous = k
    return out


def test_bhadra_two_printings():
    """One row of the monthly calendar disagrees with the Bhadra section.

    The engine settles it: the section is right and the monthly table's
    13-Jan start is wrong by 1h59m. The row's END time is correct in both, which
    is what makes this a bad cell rather than a different window definition -- a
    rule change would have moved both boundaries, not one.
    """
    found = _vishti_windows(_at("01-Jan-26 00:00"), _at("01-Feb-26 00:00"))
    record("Bhadra: the stated method yields 8 January windows",
           len(found) == 8, f"{len(found)} windows, karanas "
           f"{[k for k, _, _ in found]}")

    # Karana parity is the section's own Day/Night column, and it is timezone
    # independent -- so agreement here proves the karana NUMBERING is aligned,
    # which is what the start times depend on.
    printed_parity = ["Day", "Night", "Day", "Night",
                      "Day", "Night", "Day", "Night"]
    computed_parity = ["Day" if k % 2 else "Night" for k, _, _ in found]
    record("Bhadra: karana parity reproduces the section's Day/Night column",
           computed_parity == printed_parity,
           f"{sum(a == b for a, b in zip(computed_parity, printed_parity))}/8; "
           f"parity is a property of the tithi-half, not of daylight, so no "
           f"timezone error can move it")

    # The section claims to be Swiss-Ephemeris verified. It is: all 16 of its
    # January boundaries land within half a minute of the stated method.
    section_worst = max(
        max(abs((o - _at(a)).total_seconds()), abs((z - _at(b)).total_seconds()))
        for (a, b), (_, o, z) in zip(SOURCE_BHADRA_SECTION, found))
    record("Bhadra section: all 16 boundaries within 30 seconds",
           section_worst <= 30, f"worst delta {section_worst:.0f}s across "
           f"{2 * len(SOURCE_BHADRA_SECTION)} boundaries")

    # The monthly calendar, boundary by boundary against the same computation.
    by_day = {o.astimezone(IST).strftime("%d-%b-%y"): (o, z)
              for _, o, z in found}
    close, outliers = 0, []
    for start_text, end_text in SOURCE_BHADRA_MONTHLY:
        o, z = by_day[start_text[:9]]
        for printed, computed, edge in ((start_text, o, "start"),
                                        (end_text, z, "end")):
            delta = (computed - _at(printed)).total_seconds()
            if abs(delta) <= 90:
                close += 1
            else:
                outliers.append(f"{printed} {edge} printed {-delta / 60:.0f} "
                                f"min late")
    record("Monthly calendar: 7 of its 8 Bhadra boundaries within 90 seconds",
           close == 7 and len(outliers) == 1,
           f"{close}/8 close; outlier: {'; '.join(outliers)}")

    thirteenth = by_day["13-Jan-26"]
    record("13-Jan-26 Bhadra opens at 02:00, the section's value not 3:59",
           ist(thirteenth[0]) == "13-Jan-26 02:00",
           f"computed {ist(thirteenth[0])} -> {ist(thirteenth[1])}; "
           f"section 02:00 -> 15:18; monthly 3:59 -> 15:18")

    record("The monthly row's END time is right, so only the start cell is bad",
           ist(thirteenth[1]) == "13-Jan-26 15:18",
           "a different window rule would have moved both boundaries")

    record("Monthly calendar omits 4 of the 8 January Bhadra windows",
           len(SOURCE_BHADRA_MONTHLY) == 4,
           "absent: 02-Jan, 05-Jan, 16-Jan, 25-Jan")


# ------------------------------------------------- 15. probability labels
#: The source's probability labels sit on the prophecy blocks of the
#: salient-features chapter and nowhere else. These checks lock what the labels
#: ARE, before any of them is carried into Step 4. They are the evidence behind
#: the top-level `source_probability` block of config/conventions.yaml, and the
#: last four check that block against the document rather than against itself.
SOURCE_HTML = pathlib.Path(__file__).resolve().parent.parent / "data" / "source_2026.html"

#: Label values as printed, counted off the document.
SOURCE_LABEL_COUNTS = {"HIGH": 20, "REASONABLE": 17, "GOOD": 3,
                       "VERY HIGH": 2, "INTENSE AND HIGH RELIABLE": 1, "LOW": 1}

#: The rule catalogue Step 4 is built from: every h3.section in the document
#: except the Table of Contents heading.
CATALOGUE_B_SECTIONS = 141


def _prophecy_blocks() -> list[dict]:
    """Every div.prophecy-block with its title, label and first prophecy line.

    Re-parsed from the HTML rather than read from the config, so that the
    config's counts are checked against the document and not against a copy of
    themselves.
    """
    lines = SOURCE_HTML.read_text(encoding="utf-8").split("\n")
    starts = [i for i, line in enumerate(lines)
              if '<div class="prophecy-block">' in line]
    blocks = []
    for k, i in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        seg = "\n".join(lines[i:end])

        def grab(pattern: str, text: str = seg):
            m = re.search(pattern, text, re.S)
            return re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else None

        label = grab(r'class="probability[^"]*">(.*?)</span>')
        if label:                          # "PROBABILITY - REASONABLE"
            label = re.sub(r"^PROBABILITY\W+", "", label).strip()
        blocks.append({"n": k + 1, "line": i + 1,
                       "title": grab(r'class="prophecy-title">(.*?)</div>'),
                       "label": label,
                       "text": grab(r'class="prophecy-text">(.*?)</p>')})
    return blocks


def test_source_probability_labels():
    blocks = _prophecy_blocks()
    labelled = [b for b in blocks if b["label"]]
    unlabelled = [b for b in blocks if not b["label"]]
    conf = CONF["source_probability"]

    record("Source carries 50 prophecy blocks, 44 labelled, 6 unlabelled",
           (len(blocks), len(labelled), len(unlabelled)) == (50, 44, 6),
           f"{len(blocks)} blocks, {len(labelled)} labelled")

    eclipse = [b["n"] for b in blocks if "Eclipse" in (b["title"] or "")]
    record("Every eclipse block is unlabelled, though eclipses are impact tier T1",
           len(eclipse) == 4 and all(b["label"] is None for b in blocks
                                     if b["n"] in eclipse),
           f"eclipse blocks {eclipse}, 4 of the 6 unlabelled")

    record("The other two unlabelled blocks are the mutual-Vedh pair",
           [b["n"] for b in unlabelled if b["n"] not in eclipse] == [37, 47],
           str([b["n"] for b in unlabelled]))

    counts = {}
    for b in labelled:
        counts[b["label"]] = counts.get(b["label"], 0) + 1
    record("Label values as printed: High 20, Reasonable 17, Good 3, "
           "Very High 2, Intense and High Reliable 1, Low 1",
           counts == SOURCE_LABEL_COUNTS, str(sorted(counts.items())))

    # ---------------------------------------------------- the headline finding
    b26, b42 = blocks[25], blocks[41]
    record("HEADLINE: blocks 26 and 42 print character-identical prophecy text",
           b26["text"] == b42["text"]
           and b26["title"] == b42["title"] == "Mercury Venus Alone in Any Sign",
           (b26["text"] or "")[:58] + "...")

    record("HEADLINE: and carry DIFFERENT labels -- Reasonable vs High",
           (b26["label"], b42["label"]) == ("REASONABLE", "HIGH"),
           f"block 26 {b26['label']}, block 42 {b42['label']}")

    groups = {}
    for b in labelled:
        groups.setdefault(b["text"], []).append(b)
    multi = [g for g in groups.values() if len(g) > 1]
    disagreeing = [g for g in multi if len({x["label"] for x in g}) > 1]
    record("All three identical-text groups disagree with themselves on the label",
           len(multi) == 3 and len(disagreeing) == 3,
           "; ".join(f"{[x['n'] for x in g]}={sorted({x['label'] for x in g})}"
                     for g in multi))

    # ------------------------------------------------- where the labels are not
    lines = SOURCE_HTML.read_text(encoding="utf-8").split("\n")
    sections = [i + 1 for i, line in enumerate(lines) if '<h3 class="section"' in line]
    labels_at = [i + 1 for i, line in enumerate(lines) if 'class="probability' in line]
    record("Catalogue B is 141 rule sections (142 h3.section minus the contents page)",
           len(sections) - 1 == CATALOGUE_B_SECTIONS
           == conf["transfer_test"]["catalogues"]["B"]["count"],
           f"{len(sections)} h3.section elements")

    record("Not one probability label falls inside the 141-section rule catalogue",
           len(labels_at) == 44 and min(labels_at) > max(sections),
           f"labels on lines {min(labels_at)}-{max(labels_at)}, "
           f"catalogue ends on line {max(sections)}")

    # -------------------------------------------- the config against the source
    cls = conf["classification"]
    record("config source_probability.classification matches the document",
           (cls["prophecy_blocks"], cls["labelled"], cls["unlabelled"]) == (50, 44, 6)
           and cls["passes"] + sum(cls["fail_by_test"].values()) == 44,
           f"{cls['passes']} pass + {sum(cls['fail_by_test'].values())} fail = 44")

    record("config lists the same six unlabelled blocks the document has",
           sorted(conf["unlabelled_blocks"]["blocks"])
           == sorted(b["n"] for b in unlabelled),
           str(sorted(conf["unlabelled_blocks"]["blocks"])))

    spell = {k.upper(): k for k in CONF["labels"]["source_probability_map"]}
    bad = []
    for fam in conf["carried_families"]:
        want = fam["value"] if isinstance(fam["value"], list) else [fam["value"]]
        got = sorted({spell[blocks[n - 1]["label"]] for n in fam["blocks"]})
        if got != sorted(want):
            bad.append(f"{fam['id']} config {want} vs source {got}")
    record("Every carried family's value set is the set the source actually prints",
           not bad, "; ".join(bad) or f"{len(conf['carried_families'])} families")

    disputed = [f["id"] for f in conf["carried_families"] if f.get("disputed")]
    record("Exactly three carried families are disputed, and the config names them",
           disputed == conf["disputed_families"]["ids"]
           and conf["disputed_families"]["count"] == 3,
           str(disputed))


# ------------------------------------ 11. the tithi and yoga boundary series
#: Added with the two panchang ingress classes. These checks recompute the 2026
#: sky directly, which is the only way to ask whether the series says what the
#: document says: the rule layer reads the generated 2027 calendar and never
#: the ephemeris, so a validation living there could only compare the engine
#: with itself.
#:
#: Every printed time below is read out of data/source_2026.html through the
#: catalogue rather than typed, so a section that changed under us fails here.

def _printed_tithi_times():
    """(section, date, printed time) for every tithi edge the document prints.

    Six sections annotate their rows with the tithi's own From/Till, in four
    different column layouts. Reading them rather than transcribing them is the
    discipline the rest of this file follows.
    """
    from finastro.rules.catalogue import B
    out = []
    for row in B(65).tables[0].rows:
        out.append((65, row[0], row[1]))
    for row in B(73).tables[0].rows:
        if row[4]:
            out.append((73, row[0], row[4]))
    for row in B(74).tables[0].rows:
        out.append((74, row[0], row[3].split(" - ")[0]))
    for row in B(109).tables[0].rows:
        if row[2] and row[2] != "Whole day":
            out.append((109, row[0], "From " + row[2]))
        if row[3]:
            out.append((109, row[0], "Till " + row[3]))
    for b in (75, 76):
        for row in B(b).tables[0].rows:
            for day, cell in ((row[0], row[2]), (row[3], row[5])):
                if cell.startswith(("From", "Till")):
                    out.append((b, day, cell))
    return out


def _nearest(bounds, when):
    return min(bounds, key=lambda x: abs((x.instant - when).total_seconds()))


def test_tithi_boundaries_against_the_bhadra_section():
    """The tithi series is the Bhadra method on twice the karana's arc.

    A Vishti karana is a 6-degree step and a tithi a 12-degree step of the same
    angle, so every second karana edge IS a tithi edge -- eight of the Bhadra
    section's sixteen January boundaries. Those eight are the one place the
    document states a tithi boundary and claims to have verified it against
    Swiss Ephemeris, which makes them the strongest fixture available.
    """
    bounds = pn.tithi_boundaries(_at("31-Dec-25 00:00").astimezone(UTC),
                                 _at("02-Feb-26 00:00").astimezone(UTC))
    printed = [t for a, b in SOURCE_BHADRA_SECTION for t in (a, b)]

    coincident, worst = 0, 0.0
    for text in printed:
        when = _at(text).astimezone(UTC)
        deg = ephem.elongation_angle(when)
        if min(deg % 12.0, 12.0 - deg % 12.0) > 0.5:
            continue                       # an odd multiple of 6: mid-tithi
        coincident += 1
        worst = max(worst, abs((_nearest(bounds, when).instant
                                - when).total_seconds()))
    record("Bhadra: 8 of its 16 boundaries are tithi boundaries, the rest "
           "mid-tithi", coincident == 8,
           f"{coincident} of 16 sit on an even multiple of 6 degrees, which is "
           f"what a 12-degree step is")
    record("Bhadra: all 8 reproduce from the tithi series within 25 seconds",
           worst <= 25, f"worst delta {worst:.0f}s -- the same agreement the "
           f"Bhadra check itself records for the karana series")


def test_the_tithi_is_frame_free_and_the_yoga_is_not():
    """The claim each class carries on every record, measured rather than said.

    A tithi is a DIFFERENCE of two longitudes, so the ayanamsha cancels; a yoga
    is their SUM, so it enters twice. That is arithmetic, but it decides
    whether the yoga series is a measurement or a convention -- so it is
    checked against the document, which turns out to name the ayanamsha as
    sharply as the Sankranti table does.
    """
    import swisseph as swe
    from finastro.rules.catalogue import B

    lo = _at("31-Dec-25 00:00").astimezone(UTC)
    hi = _at("02-Jan-27 00:00").astimezone(UTC)
    reference = [b.instant for b in pn.tithi_boundaries(lo, hi)]

    modes = {"LAHIRI": swe.SIDM_LAHIRI,
             "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
             "RAMAN": swe.SIDM_RAMAN,
             "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY}

    worst_tithi = 0.0
    for mode in modes.values():
        swe.set_sid_mode(mode)
        got = [i for i, _, _ in ephem.tithi_ingresses(lo, hi)]
        if len(got) != len(reference):
            worst_tithi = float("inf")
            break
        worst_tithi = max(worst_tithi,
                          max(abs((a - b).total_seconds())
                              for a, b in zip(reference, got)))
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    def tropical(when):
        return (ephem.longitude(when, "Moon", False)
                - ephem.longitude(when, "Sun", False)) % 360.0

    got = [i for i, _, _ in ephem.angle_ingresses(tropical, lo, hi,
                                                  ephem.ARC_TITHI)]
    worst_trop = max(abs((a - b).total_seconds())
                     for a, b in zip(reference, got))
    record("Tithi boundaries are identical under four ayanamshas and in the "
           "tropical frame", worst_tithi == 0.0 and worst_trop == 0.0,
           f"{len(reference)} boundaries, worst shift {worst_tithi:.3f}s "
           f"sidereal and {worst_trop:.3f}s tropical -- the ayanamsha cancels "
           f"out of a difference of longitudes")

    # The yoga, against the boundary times B96 and B56 print.
    # B96 writes its times as "From 20:01 onwards" and "Till 16:17", so the
    # clock is pulled out by pattern rather than by position.
    printed = [f"{row[0]} {re.search(r'[0-9]{1,2}:[0-9]{2}', row[2]).group()}"
               for row in B(96).tables[0].rows]
    printed += [f"{row[3]} {row[4]}" for row in B(56).tables[0].rows
                if row[4] and row[3].endswith("-26")]

    def yoga_worst():
        bounds = ephem.angle_ingresses(ephem.sum_angle, lo, hi, ephem.ARC_YOGA)
        worst = 0.0
        for text in printed:
            when = _at(text).astimezone(UTC)
            near = min(bounds, key=lambda x: abs((x[0] - when).total_seconds()))
            worst = max(worst, abs((near[0] - when).total_seconds()))
        return worst

    by_frame = {}
    for name, mode in modes.items():
        swe.set_sid_mode(mode)
        by_frame[name] = yoga_worst()
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    record(f"Yoga: the {len(printed)} boundary times B96 and B56 print come "
           f"back within 64 seconds under config's Lahiri",
           by_frame["LAHIRI"] <= 64,
           f"worst delta {by_frame['LAHIRI']:.0f}s across {len(printed)} "
           f"printed edges")
    record("Yoga: and no other ayanamsha comes within ten minutes, so the sum "
           "is frame-dependent and the frame is the source's",
           min(v for k, v in by_frame.items() if k != "LAHIRI") > 600,
           "; ".join(f"{k} {v / 60:.0f} min" for k, v in by_frame.items()
                     if k != "LAHIRI"))

    # Read tropically the sum does not merely shift: it names other yogas.
    def tropical_sum(when):
        return (ephem.longitude(when, "Moon", False)
                + ephem.longitude(when, "Sun", False)) % 360.0

    def yogas_at_printed(angle_fn):
        bounds = ephem.angle_ingresses(angle_fn, lo, hi, ephem.ARC_YOGA)
        out = set()
        for text in printed:
            when = _at(text).astimezone(UTC)
            near = min(bounds, key=lambda x: abs((x[0] - when).total_seconds()))
            if abs((near[0] - when).total_seconds()) < 36000:
                out.add(pn.YOGA_NAMES[near[2]])
        return out

    sid, trop = yogas_at_printed(ephem.sum_angle), yogas_at_printed(tropical_sum)
    record("Yoga: read tropically the printed edges land on different yogas "
           "entirely, not on shifted ones",
           bool(sid) and not (sid & trop),
           f"sidereal {sorted(sid)} against tropical {sorted(trop) or 'none'}")


def test_printed_tithi_times_reproduce():
    """Thirty-six printed tithi edges across six sections, to the second.

    One disagrees, and it is a source defect of the 13-Jan Bhadra kind -- a
    correct value in the wrong cell -- so it is pinned by name rather than
    absorbed into a tolerance.
    """
    lo = _at("20-Dec-25 00:00").astimezone(UTC)
    hi = _at("10-Jan-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)

    printed = _printed_tithi_times()
    deltas = []
    for sec, day, text in printed:
        when = _at(f"{day} {text.split()[-1]}").astimezone(UTC)
        deltas.append((sec, day, text,
                       (_nearest(bounds, when).instant - when).total_seconds()))
    close = [x for x in deltas if abs(x[3]) <= 90]
    outliers = [x for x in deltas if abs(x[3]) > 90]

    record(f"{len(printed)} printed tithi edges across B65, B73, B74, B75, B76 "
           f"and B109: all but one within 90 seconds",
           len(close) == len(printed) - 1 and len(outliers) == 1,
           f"{len(close)}/{len(printed)} close, worst of them "
           f"{max(abs(x[3]) for x in close):.0f}s")

    sec, day, text, delta = outliers[0]
    record("The one outlier is B76's 03-Jun-26 cell, about two hours out",
           (sec, day) == (76, "03-Jun-26"),
           f"B{sec} {day} {text}, printed {-delta / 60:.0f} min after the "
           f"nearest boundary")

    # ...and it is the 13-Jan Bhadra defect again: a right value, wrong cell.
    ends = [b for b in bounds
            if b.name_to == "Panchami" and b.paksha_to == "Krishna"
            and ist(b.instant).startswith("04-Jun-26")]
    record("B76's 23:31 is the correct END of that Chaturthi to one second, "
           "against the wrong date",
           len(ends) == 1 and ist(ends[0].instant) == "04-Jun-26 23:30",
           f"Krishna Chaturthi closes "
           f"{ends[0].instant.astimezone(IST):%d-%b-%y %H:%M:%S} and the row "
           f"prints 'Till 23:31' against 03-Jun-26" if ends else "not found")


def test_kshaya_and_vriddhi_tithis_reproduce_against_sunrise():
    """B66-B69, 28 rows, and the reason all four are still blocked.

    A tithi is Kshay when no sunrise falls inside it and Vriddhi when two do.
    Both are statements about the tithi's boundaries AND the day's, so the
    boundary series alone settles neither -- and read against Mumbai sunrise
    all four tables come back exactly, which is what makes 'sunrise' the whole
    of what is missing rather than a guess at it.
    """
    from finastro.rules.catalogue import B
    from finastro.rules import names as rule_names

    lo = _at("20-Dec-25 00:00").astimezone(UTC)
    hi = _at("10-Jan-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)
    spans = [(bounds[i].instant, bounds[i + 1].instant,
              bounds[i].name_to, bounds[i].paksha_to)
             for i in range(len(bounds) - 1)]

    mumbai = CONF["locations"]["mumbai"]
    rises, day = [], dt.date(2025, 12, 15)
    while day < dt.date(2027, 1, 15):
        rises.append(pn.sunrise(day, mumbai))
        day += dt.timedelta(days=1)

    #: section -> (sunrises the tithi must hold, fortnight)
    TABLES = {66: (0, "Shukla"), 67: (0, "Krishna"),
              68: (2, "Shukla"), 69: (2, "Krishna")}

    for sec, (want, paksha) in TABLES.items():
        printed = sorted((d(row[0]), rule_names.tithis_in(row[2])[0])
                         for row in B(sec).tables[0].rows)
        got = []
        for start, end, name, pk in spans:
            if pk != paksha or start.astimezone(IST).year != Y:
                continue
            n = sum(1 for r in rises if start <= r < end)
            if (want == 0 and n == 0) or (want == 2 and n >= 2):
                got.append((start.astimezone(IST).date(), name))
        kind = "Kshay" if want == 0 else "Vriddhi"
        record(f"B{sec} {kind} {paksha}: every printed row reproduces against "
               f"sunrise, dated by the day the tithi opens, with no extra",
               printed == sorted(got),
               f"printed {len(printed)}, computed {len(got)}, date and tithi "
               f"name agreeing on all of them: {printed == sorted(got)}")


def test_printed_tithi_and_yoga_tables_against_their_own_titles():
    """What each newly unblocked section's table does against its own title.

    Section 12.4 of STEP4_DECISIONS set the standard: the titles are the rule,
    the tables are incomplete, and an omission is recorded as a date rather
    than as an impression. These are the dates.
    """
    from finastro.rules.catalogue import B

    lo = _at("20-Dec-25 00:00").astimezone(UTC)
    hi = _at("10-Jan-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)
    spans = [(bounds[i].instant, bounds[i + 1].instant,
              bounds[i].name_to, bounds[i].paksha_to)
             for i in range(len(bounds) - 1)]

    def days(wanted, paksha, weekdays):
        out = set()
        for start, end, name, pk in spans:
            if name not in wanted or (paksha and pk != paksha):
                continue
            day = start.astimezone(IST).date()
            last = end.astimezone(IST).date()
            while day <= last:
                a, b = civil_day_bounds(day, IST)
                if start < b and a < end and day.year == Y \
                        and (weekdays is None or day.weekday() in weekdays):
                    out.add(day)
                day += dt.timedelta(days=1)
        return out

    TUE, FRI, SAT = 1, 4, 5

    got = days({"Ekadashi"}, None, {FRI})
    printed = {d(row[0]) for row in B(65).tables[0].rows}
    record("B65 Ekadashi on Friday: 6 printed, 6 computed, no omission and no "
           "extra", got == printed,
           f"printed {len(printed)}, computed {len(got)}")

    got = days({"Ashtami"}, None, {TUE, SAT})
    printed = {d(row[0]) for row in B(73).tables[0].rows}
    record("B73 Ashtami on Tue/Sat: the two rows it prints against 'Sunday' "
           "are outside its own title's weekday set",
           sorted(printed - got) == sorted([d("11-Jan-26"), d("10-May-26")]),
           f"printed and not reached: {sorted(printed - got)}; each is the day "
           f"after a Saturday Ashtami this condition does hold on")

    got = days({"Trayodashi"}, "Shukla", {TUE, SAT})
    printed = {d(row[0]) for row in B(109).tables[0].rows}
    record("B109 Shukla Trayodashi on Tue/Sat: all 7 printed rows reproduce, "
           "one occurrence omitted",
           printed <= got and sorted(got - printed) == [d("28-Feb-26")],
           f"omitted: {sorted(got - printed)}")

    got = days({"Shashthi"}, "Shukla", {FRI})
    printed = {d(row[0]) for row in B(100).tables[0].rows}
    record("B100 Shukla Shasthi on Friday: 1 printed of 3 occurrences",
           printed <= got
           and sorted(got - printed) == sorted([d("22-May-26"),
                                                d("16-Oct-26")]),
           f"omitted: {sorted(got - printed)}")

    got = days({"Pratipada"}, "Shukla", {SAT, 6})
    printed = {d(row[0]) for row in B(95).tables[0].rows}
    record("B95 Shukla Pratipada on Sat/Sun: all 4 printed dates reproduce",
           printed <= got, f"printed {len(printed)}, computed {len(got)} -- "
           f"the extra day is the Saturday half of the Pratipada printed "
           f"against Sunday 11-Oct-26")

    # The yoga side, and B108, which needed both series at once.
    ybounds = pn.yoga_boundaries(lo, hi)
    yspans = [(ybounds[i].instant, ybounds[i + 1].instant, ybounds[i].name_to)
              for i in range(len(ybounds) - 1)]
    # Civil-day overlap, not the opening day: two of the nine rows read "Till",
    # which is a window that opened the day before and closes on the printed
    # date. Testing for an opening would fail those two on the convention
    # rather than on the sky.
    vyatipata = set()
    for start, end, name in yspans:
        if name != "Vyatipata":
            continue
        day = start.astimezone(IST).date()
        last = end.astimezone(IST).date()
        while day <= last:
            a, b = civil_day_bounds(day, IST)
            if start < b and a < end and day.year == Y                     and day.weekday() in (TUE, SAT, 6):
                vyatipata.add(day)
            day += dt.timedelta(days=1)
    printed = {d(row[0]) for row in B(96).tables[0].rows}
    record("B96 Vyatipata on Tue/Sat/Sun: all 9 printed dates reproduce and "
           "the condition holds on no other", printed == vyatipata,
           f"printed {len(printed)}, computed {len(vyatipata)}, "
           f"omitted {sorted(printed - vyatipata)}, "
           f"extra {sorted(vyatipata - printed)}")

    hits = set()
    for ts, te, name, pk in spans:
        if name != "Ekadashi" or pk != "Shukla":
            continue
        for ys, ye, yn in yspans:
            if yn in ("Vyatipata", "Vaidhriti") and max(ts, ys) < min(te, ye) \
                    and max(ts, ys).astimezone(IST).year == Y:
                hits.add(max(ts, ys).astimezone(IST).date())
    printed = {d(row[0]) for row in B(108).tables[0].rows}
    record("B108 Shukla Ekadashi with Vyatipata or Vaidhriti: its one printed "
           "row is the only 2026 occurrence", hits == printed,
           f"computed {sorted(hits)}, printed {sorted(printed)} -- the section "
           f"blocked on BOTH series and clears only because both arrived")


def test_b106_ghadi_comparison_and_its_broken_date_cell():
    """B106 needs two tithi LENGTHS, which is two differences of boundaries.

    Its third row carries the document's recurring year typo and a wrong day
    besides, and the row's own TIME is what identifies it -- the same way the
    13-Jan Bhadra row's end time identified that one.
    """
    from finastro.rules.catalogue import B

    lo = _at("20-Dec-25 00:00").astimezone(UTC)
    hi = _at("10-Jan-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)
    spans = [(bounds[i].instant, bounds[i + 1].instant, bounds[i].name_to)
             for i in range(len(bounds) - 1)]

    hits = []
    for i, (start, end, name) in enumerate(spans):
        if i == 0 or name != "Amavasya":
            continue
        p_start, p_end, p_name = spans[i - 1]
        if p_name != "Chaturdashi":
            continue
        if (end - start) < (p_end - p_start) \
                and start.astimezone(IST).year == Y:
            hits.append(start)

    printed = [(row[0], row[1]) for row in B(106).tables[0].rows]
    record("B106: the condition holds 6 times in 2026 and the section prints 4",
           len(hits) == 6 and len(printed) == 4,
           f"computed {[ist(h) for h in hits]}")

    def minutes(text):
        hh, mm = text.split(":")
        return int(hh) * 60 + int(mm)

    worst = 0.0
    for _text, hhmm in printed:
        want = minutes(hhmm)
        best = min(abs(minutes(f"{h.astimezone(IST):%H:%M}") - want)
                   for h in hits)
        worst = max(worst, best)
    record("B106: all 4 printed start times land within 2 minutes of a "
           "computed Amavasya opening", worst <= 2, f"worst {worst:.0f} min")

    broken = [row for row in B(106).tables[0].rows if "-25" in row[0]]
    march = [h for h in hits if h.astimezone(IST).month == 3]
    record("B106's third row reads '28-Mar-25 *' while its 08:27 is the "
           "18-Mar-26 Amavasya opening at 08:25 -- wrong day, wrong year, and "
           "asterisked by the document itself",
           len(broken) == 1 and len(march) == 1
           and ist(march[0]).startswith("18-Mar-26 08:2"),
           f"printed {broken[0][0]!r} {broken[0][1]}, computed "
           f"{ist(march[0]) if march else 'none'}")


# ------------------------------------------- the sunrise and sunset series
# The 2026 document prints no rise or set table, and it does print four Mumbai
# times to the minute -- inside the Bhadra section's prose, where it explains
# why its reference place matters. Those four are the only direct evidence the
# document offers about this series, and they are read out of the file below
# rather than transcribed, as every other printed time in this suite is.

#: The prose sentence the four times live in, matched rather than quoted whole,
#: so a change to the surrounding wording fails loudly instead of silently
#: matching nothing.
_HORIZON_PROSE = re.compile(
    r"(\d{2}-[A-Z][a-z]{2}) \(opens \d{2}:\d{2}, before (?:Mumbai )?"
    r"(sunrise|sunset) (\d{2}:\d{2})")

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def _printed_horizon_times() -> list[tuple[dt.date, str, str]]:
    """(date, "sunrise"|"sunset", "HH:MM") for each time the prose prints."""
    text = SOURCE_HTML.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    out = []
    for day_month, kind, hhmm in _HORIZON_PROSE.findall(text):
        dd, mon = day_month.split("-")
        out.append((dt.date(Y, _MONTHS[mon], int(dd)), kind, hhmm))
    return out


def _conventions() -> dict:
    """The four rise/set conventions, as Swiss Ephemeris bit sets.

    Compared rather than argued about, and the comparison deliberately does not
    pick a winner: the size of the spread between them is why the series is
    graded B.
    """
    import swisseph as swe
    return {
        "disc_center_no_refraction":
            swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION,
        "disc_center_with_refraction": swe.BIT_DISC_CENTER,
        "upper_limb_no_refraction": swe.BIT_NO_REFRACTION,
        "upper_limb_with_refraction": 0,
    }


def _crossing(day: dt.date, loc: dict, rising: bool, bits: int) -> dt.datetime:
    """One rise or set under an arbitrary convention, for the comparison only.

    A deliberate near-duplicate of `panchang._horizon_crossing`, differing in
    the one argument the engine does not expose: the convention. The engine
    offers no such parameter on purpose -- a convention that can be passed in is
    a convention a caller can vary, and the point of pinning it is that no
    caller may. So the alternatives are constructed here, in the harness that
    exists to measure them, and nowhere else.
    """
    import swisseph as swe
    from zoneinfo import ZoneInfo
    ephem.init()
    lo, _ = civil_day_bounds(day, ZoneInfo(loc["tz"]))
    calc = swe.CALC_RISE if rising else swe.CALC_SET
    res = swe.rise_trans(ephem.to_jd(lo), swe.SUN,
                         ephem.backend_flag() | calc | bits,
                         (loc["lon"], loc["lat"], loc["alt"]), 0, 0)
    return ephem.from_jd(res[1][0])


def test_sunrise_and_sunset_against_the_four_printed_mumbai_times():
    """The only four rise/set times the 2026 document prints, and what they show.

    They come from the Bhadra section's own explanation of why its reference
    place matters: four 2026 windows open close enough to a horizon crossing
    that a fixed 06:00-18:00 clock would classify them differently from true
    Mumbai sunrise and sunset, so the document had to state the real times.

    Two separate things are checked, and only the first is a pass/fail about
    this engine. It reproduces all four within five minutes, and that is the
    agreement the series claims.

    The four do NOT establish the convention, and the second check records that
    as a measurement rather than leaving it as an impression. Times printed to
    the minute cannot separate conventions whose spread is about four and a
    half minutes, and under every one of them the errors come in both signs --
    so there is no offset to recover either. The convention therefore stays the
    one the kalamsha calibration pinned, that being the one place in this
    project where a rise/set convention was fitted to the source's own data.
    """
    printed = _printed_horizon_times()
    mumbai = CONF["locations"]["mumbai"]
    record("The four Mumbai rise/set times are read out of the document",
           len(printed) == 4,
           f"{len(printed)} found: "
           + ", ".join(f"{a:%d-%b} {b} {c}" for a, b, c in printed))
    if len(printed) != 4:
        return

    errs = {}
    for name, bits in _conventions().items():
        deltas = []
        for day, kind, hhmm in printed:
            got = _crossing(day, mumbai, kind == "sunrise", bits).astimezone(IST)
            want = got.replace(hour=int(hhmm[:2]), minute=int(hhmm[3:]),
                               second=0, microsecond=0)
            deltas.append((got - want).total_seconds())
        errs[name] = deltas

    pinned = errs[pn.RISE_SET_CONVENTION]
    record("The engine reproduces all four printed Mumbai times within 5 "
           "minutes", max(abs(x) for x in pinned) <= 300,
           ", ".join(f"{a:%d-%b} {b} {c} {e:+.0f}s"
                     for (a, b, c), e in zip(printed, pinned)))

    record("The rise/set convention is stated once and shared with combustion",
           pn.RISE_SET_CONVENTION == CONF["combustion"]["rise_set_flags"],
           f"{pn.RISE_SET_CONVENTION} in both panchang and config")

    spread = {k: (max(abs(x) for x in v), sum(abs(x) for x in v) / len(v))
              for k, v in errs.items()}
    signs = {k: len({x > 0 for x in v}) for k, v in errs.items()}
    record("Four printed times do not discriminate between the rise/set "
           "conventions, which is why the series is graded B",
           all(s == 2 for s in signs.values())
           and min(w for w, _ in spread.values()) > 60,
           "; ".join(f"{k} worst {w:.0f}s mean {m:.0f}s"
                     for k, (w, m) in spread.items())
           + " -- each has errors of both signs, so none is a fixed offset "
             "from the source's")


def test_sunrise_and_sunset_land_in_their_own_civil_day():
    """The day a crossing is filed under is the day it happens at that venue.

    A regression guard with a defect behind it. `panchang.sunrise` anchored its
    search at local NOON, so it returned the rise of the FOLLOWING day: a true
    instant filed under the wrong date. Nothing then in this suite could see
    it, because the Kshay/Vriddhi reproduction only asks how many sunrises fall
    inside a tithi, and a set of sunrise instants shifted by a day covers the
    same interval and gives the same count. It took emitting the series as
    dated records to make the defect visible; this keeps it visible.
    """
    from zoneinfo import ZoneInfo
    for key in ("mumbai", "new_york"):
        loc = CONF["locations"][key]
        tz = ZoneInfo(loc["tz"])
        bad_rise, bad_set, inverted = [], [], []
        day = dt.date(Y, 1, 1)
        while day <= dt.date(Y, 12, 31):
            r, s = pn.sunrise(day, loc), pn.sunset(day, loc)
            if r.astimezone(tz).date() != day:
                bad_rise.append(day)
            if s.astimezone(tz).date() != day:
                bad_set.append(day)
            if not r < s:
                inverted.append(day)
            day += dt.timedelta(days=7)
        record(f"{key}: every sunrise and sunset falls on the day it is asked "
               "for, and the rise precedes the set",
               not bad_rise and not bad_set and not inverted,
               f"{len(bad_rise)} misdated rises, {len(bad_set)} misdated sets, "
               f"{len(inverted)} inverted, over 53 sampled days")


def test_the_convention_and_the_kshaya_vriddhi_rows():
    """Where the B grade reaches these rows and where it does not -- measured.

    A rise depends on disc, refraction and horizon height, which is why the
    series is graded B and why every record carries the convention it was
    computed under. The question this answers is how far that doubt travels
    into a rule conditioned on a sunrise, and the answer is not "not at all".

    Twenty-seven of the twenty-eight Kshay and Vriddhi rows are the same under
    all four conventions: a tithi boundary lands within four minutes of a
    sunrise rarely, and when it does not, the count of sunrises inside the tithi
    cannot change. One row is not.

    **B66's 23-Feb-2026 Saptami is decided by eight seconds.** Shukla Saptami
    runs 23-Feb 09:09:45 to 24-Feb 07:02:37. Mumbai sunrise on 24-Feb is
    07:05:07 with disc centre and no refraction and 07:02:29 with refraction
    applied -- one side of the tithi's end and then the other. Read without
    refraction the Saptami contains no sunrise and is Kshay, dated 23-Feb. Read
    with refraction it contains one, is not Kshay, and the following Ashtami is
    Kshay instead, dated 24-Feb.

    **The section prints 23-Feb-26, Saptami.** So this row is evidence about
    the convention, from a different chapter of the document and by a different
    mechanism than the kalamsha calibration, and it points the same way. It is
    one row decided by eight seconds and is recorded as exactly that -- thin,
    independent, and consistent with the choice already made, which is a
    different thing from a choice made on its strength.
    """
    from finastro.rules.catalogue import B
    from finastro.rules import names as rule_names

    lo = _at("20-Dec-25 00:00").astimezone(UTC)
    hi = _at("10-Jan-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)
    spans = [(bounds[i].instant, bounds[i + 1].instant,
              bounds[i].name_to, bounds[i].paksha_to)
             for i in range(len(bounds) - 1)]
    mumbai = CONF["locations"]["mumbai"]
    TABLES = {66: (0, "Shukla"), 67: (0, "Krishna"),
              68: (2, "Shukla"), 69: (2, "Krishna")}

    per_convention = {}
    for name, bits in _conventions().items():
        rises, day = [], dt.date(Y - 1, 12, 15)
        while day < dt.date(Y + 1, 1, 15):
            rises.append(_crossing(day, mumbai, True, bits))
            day += dt.timedelta(days=1)
        got = []
        for sec, (want, paksha) in sorted(TABLES.items()):
            for start, end, nm, pk in spans:
                if pk != paksha or start.astimezone(IST).year != Y:
                    continue
                n = sum(1 for r in rises if start <= r < end)
                if (want == 0 and n == 0) or (want == 2 and n >= 2):
                    got.append((sec, start.astimezone(IST).date(), nm))
        per_convention[name] = tuple(sorted(got))

    printed = tuple(sorted(
        (sec, d(row[0]), rule_names.tithis_in(row[2])[0])
        for sec in TABLES for row in B(sec).tables[0].rows))

    pinned = per_convention[pn.RISE_SET_CONVENTION]
    record("Under the pinned convention all four tables reproduce exactly, "
           "28 rows, every tithi named correctly",
           pinned == printed,
           f"{len(pinned)} computed against {len(printed)} printed")

    stable = set.intersection(*(set(v) for v in per_convention.values()))
    moving = sorted(set(printed) - stable)
    record("Twenty-seven of the twenty-eight rows are the same under all four "
           "conventions", len(stable & set(printed)) == 27 and len(moving) == 1,
           f"{len(stable & set(printed))} convention-independent, "
           f"{len(moving)} decided by the convention: {moving}")

    # The one row that moves, and the margin that moves it.
    saptami = next((a, b) for a, b, nm, pk in spans
                   if nm == "Saptami" and pk == "Shukla"
                   and a.astimezone(IST).date() == dt.date(Y, 2, 23))
    rise_24 = {k: _crossing(dt.date(Y, 2, 24), mumbai, True, v).astimezone(IST)
               for k, v in _conventions().items()}
    margin = (saptami[1].astimezone(IST)
              - rise_24["disc_center_with_refraction"]).total_seconds()
    agrees = {k for k, t in rise_24.items() if t.astimezone(UTC) >= saptami[1]}
    record("The one row the convention decides is B66's 23-Feb Saptami, by an "
           "eight-second margin, and the section's printed row agrees with the "
           "no-refraction reading",
           moving == [(66, dt.date(Y, 2, 23), "Saptami")]
           and agrees == {"disc_center_no_refraction",
                          "upper_limb_no_refraction"}
           and 0 < margin < 15,
           f"Saptami closes {saptami[1].astimezone(IST):%d-%b %H:%M:%S}; "
           + ", ".join(f"{k.replace('_', ' ')} {t:%H:%M:%S}"
                       for k, t in rise_24.items())
           + f"; the refracted rise precedes the tithi's end by {margin:.0f}s")


def test_pradosh_reproduces_against_mumbai_sunset():
    """B64, its 24 printed rows, and the three clauses its own table decides.

    The section never defines Pradosh -- the word appears twenty-two times in
    the document and is explained nowhere -- so the definition is supplied and
    the rule is a `resolved_ambiguity` rather than an executable one. What makes
    it a resolution and not a preference is that each clause is chosen by a row
    that refutes the alternative, and all three are checked here against the
    2026 sky directly.
    """
    from finastro.rules.catalogue import B

    lo = _at("20-Dec-25 00:00").astimezone(UTC)
    hi = _at("10-Jan-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)
    spans = [(bounds[i].instant, bounds[i + 1].instant,
              bounds[i].name_to, bounds[i].paksha_to)
             for i in range(len(bounds) - 1)]
    mumbai = CONF["locations"]["mumbai"]
    PAKSHA = {"Dark": "Krishna", "Bright": "Shukla"}
    printed = sorted((d(row[0]), PAKSHA[row[2]])
                     for row in B(64).tables[0].rows)

    def sets_inside(a, b):
        out, day = [], a.astimezone(IST).date()
        last = b.astimezone(IST).date()
        while day <= last:
            s = pn.sunset(day, mumbai)
            if a <= s < b:
                out.append((day, s))
            day += dt.timedelta(days=1)
        return out

    trayodashis = [(a, b, pk) for a, b, nm, pk in spans
                   if nm == "Trayodashi"
                   and (a.astimezone(IST).year == Y
                        or b.astimezone(IST).year == Y)]
    record("2026 holds 25 Trayodashis and the section prints 24 Pradosh dates",
           len(trayodashis) == 25 and len(printed) == 24,
           f"{len(trayodashis)} Trayodashis, {len(printed)} printed rows")

    ruled, plain, kala, at_sunrise = [], [], [], []
    two_sunsets, no_sunset = [], []
    for a, b, pk in trayodashis:
        inside = sets_inside(a, b)
        if len(inside) > 1:
            two_sunsets.append((a, b, [x for x, _ in inside]))
        if not inside:
            no_sunset.append((a, b))
        ruled.append((inside[0][0] if inside else b.astimezone(IST).date(), pk))
        plain += [(day, pk) for day, _ in inside]
        day, last = a.astimezone(IST).date(), b.astimezone(IST).date()
        took_kala = took_rise = False
        while day <= last:
            s = pn.sunset(day, mumbai)
            if not took_kala and s < b and a < s + dt.timedelta(minutes=144):
                kala.append((day, pk))
                took_kala = True
            if not took_rise and a <= pn.sunrise(day, mumbai) < b:
                at_sunrise.append((day, pk))
                took_rise = True
            day += dt.timedelta(days=1)

    def score(rows):
        return len({x for x in rows if x[0].year == Y} & set(printed))

    record("The ruled reading reproduces 23 of the 24 printed rows, more than "
           "any competing one",
           score(ruled) == 23 and score(ruled) > score(plain) > score(kala)
           and score(kala) > score(at_sunrise),
           f"ruled {score(ruled)}/24, sunset-only {score(plain)}/24, "
           f"pradosh kala {score(kala)}/24, at sunrise {score(at_sunrise)}/24")

    record("Exactly one 2026 Trayodashi holds two sunsets, and the section "
           "prints the first of them",
           len(two_sunsets) == 1
           and (two_sunsets[0][2][0], "Shukla") in printed
           and (two_sunsets[0][2][1], "Shukla") not in printed,
           "; ".join(f"{a.astimezone(IST):%d-%b %H:%M:%S} to "
                     f"{b.astimezone(IST):%d-%b %H:%M:%S} holds "
                     f"{[str(x) for x in days]}"
                     for a, b, days in two_sunsets))

    record("Exactly one 2026 Trayodashi holds no sunset at all, and the "
           "section dates it to the day the tithi ends",
           len(no_sunset) == 1
           and (no_sunset[0][1].astimezone(IST).date(), "Krishna") in printed
           and (no_sunset[0][0].astimezone(IST).date(), "Krishna")
           not in printed,
           "; ".join(f"{a.astimezone(IST):%d-%b %H:%M:%S} to "
                     f"{b.astimezone(IST):%d-%b %H:%M:%S}; the section prints "
                     f"{b.astimezone(IST):%d-%b}, not {a.astimezone(IST):%d-%b}"
                     for a, b in no_sunset))

    # The two divergences, held apart, and the separation is the point. A
    # single count of differences would report three, and there are two
    # findings: one occurrence the section does not print, and one tithi the
    # section and this engine date to different days. The 24-Aug row and the
    # 25-Aug row are ONE disagreement about ONE tithi, not an omission plus an
    # unreachable row, so the pair is taken out before the omissions are read.
    defect_pair = {(dt.date(Y, 8, 24), "Shukla"), (dt.date(Y, 8, 25), "Shukla")}
    omitted = sorted({x for x in ruled if x[0].year == Y}
                     - set(printed) - defect_pair)
    unreachable = sorted(set(printed) - set(ruled))
    record("Once the 24-Aug pair is set aside, the one occurrence the section "
           "omits is 01-Jan-2026 -- a Pradosh on every reading",
           omitted == [(dt.date(Y, 1, 1), "Shukla")], str(omitted))

    b68_trayodashi = [row[0] for row in B(68).tables[0].rows
                      if "Trayodashi" in row[2]]
    record("The one printed row the condition cannot reach is 24-Aug-2026, and "
           "the document's own B68 dates that tithi to 25-Aug",
           unreachable == [(dt.date(Y, 8, 24), "Shukla")]
           and "25-Aug-26" in b68_trayodashi,
           f"{unreachable}; B68 prints the same tithi as {b68_trayodashi}")


def test_three_saturdays_in_a_bright_fortnight_at_each_venue():
    """B101, its single printed row, and why the count belongs to a venue.

    The section prints one two-ended row, 12-Sep-26 to 26-Sep-26, and that row
    settles the span's shape on its own. The fortnight it names opens 11-Sep
    08:57 and closes 26-Sep 22:19, so the Till cannot separate "the last
    Saturday" from "the fortnight's close" -- they are the same date -- but the
    From can, and it is the Saturday and not the Pratipada.

    The venue half is the finding. Counted in Mumbai's calendar, 2026 holds two
    qualifying fortnights; counted in New York's it holds three, because the
    fortnight opening 16-May 16:01 New York time opens 17-May in Mumbai and
    loses its first Saturday in the crossing. One count, two answers, and no
    astronomy in the difference.
    """
    from zoneinfo import ZoneInfo
    from finastro.rules.catalogue import B

    lo = _at("01-Dec-25 00:00").astimezone(UTC)
    hi = _at("01-Feb-27 00:00").astimezone(UTC)
    bounds = pn.tithi_boundaries(lo, hi)
    spans = [(bounds[i].instant, bounds[i + 1].instant,
              bounds[i].name_to, bounds[i].paksha_to)
             for i in range(len(bounds) - 1)]

    fortnights, run = [], []
    for a, b, nm, pk in list(spans) + [(None, None, None, None)]:
        if pk == "Shukla":
            run.append((a, b, nm))
            continue
        if run:
            if run[0][2] == "Pratipada" and run[-1][2] == "Purnima":
                fortnights.append((run[0][0], run[-1][1]))
            run = []

    SATURDAY = 5
    found = {}
    for key in ("mumbai", "new_york"):
        tz = ZoneInfo(CONF["locations"][key]["tz"])
        hits = []
        for a, b in fortnights:
            day, last = a.astimezone(tz).date(), b.astimezone(tz).date()
            sats = []
            while day <= last:
                x, y = civil_day_bounds(day, tz)
                if a < y and x < b and day.weekday() == SATURDAY:
                    sats.append(day)
                day += dt.timedelta(days=1)
            if len(sats) >= 3:
                hits.append((a, b, sats))
        found[key] = hits
        record(f"No bright fortnight at {key} holds more than three Saturdays, "
               "so 'three' as a threshold and as an exact count agree",
               all(len(s) == 3 for _, _, s in hits),
               f"{len(hits)} qualifying fortnights, counts "
               f"{sorted({len(s) for _, _, s in hits})}")

    printed = [(d(r[0]), d(r[1])) for r in B(101).tables[0].rows]
    mumbai_2026 = [x for x in found["mumbai"] if x[2][0].year == Y]
    record("The section prints one row and Mumbai 2026 holds two qualifying "
           "fortnights", len(printed) == 1 and len(mumbai_2026) == 2,
           f"printed {[(str(x), str(y)) for x, y in printed]}, computed "
           f"{[(str(s[0]), str(s[-1])) for _, _, s in mumbai_2026]}")

    match = [x for x in mumbai_2026 if (x[2][0], x[2][-1]) == printed[0]]
    record("The printed row runs first Saturday to last, not the fortnight's "
           "own bounds", len(match) == 1,
           (f"fortnight {match[0][0].astimezone(IST):%d-%b %H:%M} to "
            f"{match[0][1].astimezone(IST):%d-%b %H:%M}; the row prints "
            f"{printed[0][0]:%d-%b} to {printed[0][1]:%d-%b}; Saturdays "
            f"{[str(x) for x in match[0][2]]}") if match else "no match")

    omitted = [x for x in mumbai_2026 if (x[2][0], x[2][-1]) != printed[0]]
    record("The second qualifying Mumbai fortnight is omitted by the source -- "
           "an omitted occurrence, not a two-day artefact", len(omitted) == 1,
           "; ".join(f"fortnight {a.astimezone(IST):%d-%b %H:%M} to "
                     f"{b.astimezone(IST):%d-%b %H:%M}, Saturdays "
                     f"{[str(x) for x in s]}" for a, b, s in omitted))

    ny_2026 = [x for x in found["new_york"] if x[2][0].year == Y]
    record("The count is genuinely per venue: Mumbai 2026 holds two and New "
           "York three", len(mumbai_2026) == 2 and len(ny_2026) == 3,
           f"mumbai {[str(s[0]) for _, _, s in mumbai_2026]}, "
           f"new_york {[str(s[0]) for _, _, s in ny_2026]}")


def main() -> int:
    print(f"ephemeris backend: {ephem.init()}\n")
    for fn in (test_ayanamsha_and_node, test_stations, test_total_days,
               test_combustion, test_weekday_convention, test_source_span_times,
               test_new_york_divergence, test_dignity_frame_is_navamsa,
               test_vargottama_is_d1_equals_d9,
               test_vargottama_is_not_always_true,
               test_vargottama_appendix_own_nakshatra,
               test_vargottama_is_not_a_dignity,
               test_bhadra_two_printings,
               test_tithi_boundaries_against_the_bhadra_section,
               test_the_tithi_is_frame_free_and_the_yoga_is_not,
               test_printed_tithi_times_reproduce,
               test_kshaya_and_vriddhi_tithis_reproduce_against_sunrise,
               test_sunrise_and_sunset_against_the_four_printed_mumbai_times,
               test_sunrise_and_sunset_land_in_their_own_civil_day,
               test_the_convention_and_the_kshaya_vriddhi_rows,
               test_pradosh_reproduces_against_mumbai_sunset,
               test_three_saturdays_in_a_bright_fortnight_at_each_venue,
               test_printed_tithi_and_yoga_tables_against_their_own_titles,
               test_b106_ghadi_comparison_and_its_broken_date_cell,
               test_weekday_source_defects,
               test_source_probability_labels):
        fn()
    width = max(len(n) for n, _, _ in _results)
    failed = 0
    for name, status, detail in _results:
        failed += status == FAIL
        print(f"[{status}] {name.ljust(width)}  {detail}")
    print(f"\n{len(_results) - failed}/{len(_results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
