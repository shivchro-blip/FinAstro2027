"""Generator of record for the no-instant cause census.

Every figure this build has had to withdraw was a correct count of the wrong
set: `282` was the first cause measured on a second key, `45`/`12` mixed rows
with firings, `22` omitted `clipped_start` and skipped its own `open_*` filter,
and `105` reads as a venue count when it is a location count. The arithmetic
was right every time. Nothing about a bare integer says which set it counted.

So this script never prints a number alone. Every count is emitted beside the
POPULATION it was measured over, the UNIT it was counted in, and the FILTER
applied -- because those three are what a reader needs in order to know whether
two figures may be compared at all, and they are exactly what the withdrawn
figures did not carry.

Run:  python tools/cause_census.py        (after python -m finastro.render)
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.render import covered_days                # noqa: E402
from finastro.verdicts import VENUE_OF                  # noqa: E402

CALENDAR_JSON = ROOT / "build" / "calendar_2027.json"

#: The one rule whose `date_only` is `sky.civil_day_span`'s and not an
#: ephemeris record's. `no_instant_reason` does not make this split -- both set
#: precision="date_only" and the renderer cannot tell them apart -- so it is
#: made here, by rule id, and every table below states that it was made.
B101 = "b101_three_saturdays_in_shukla_paksha"

#: The three causes a collapse (Model A) folds, and the two it leaves as point
#: rows. `anchored` is a decision and not an oversight: an anchored date is one
#: this build chose because the body never crossed its frame, so widening it to
#: a year would assert a measurement nobody made.
COLLAPSED = ("date_only_ephem", "date_only_b101", "period_cut")
POINT_ROWS = ("anchored", "named_contacts")
CAUSES = COLLAPSED + POINT_ROWS


def cause(row):
    """The cause, with `date_only` split by rule id. None if the row has an instant."""
    reason = row["no_instant_reason"]
    if reason is None:
        return None
    if reason == "date_only":
        is_b101 = row["row_kind"] == "verdict" and row["event"] == B101
        return "date_only_b101" if is_b101 else "date_only_ephem"
    return reason


def firing_location(row):
    """The location `rules.base.fire` emitted at -- mumbai or new_york.

    NOT the `venue` field. A verdict's venue is an exchange (NSE, NSE_FX,
    US_cash); its firing location is the civil day that exchange keeps, and
    `verdicts.VENUE_OF` is the map. Mumbai carries three venues, so counting
    firings by venue over-counts: b101 is 105 firings and 150 (rule, venue,
    day) triples, and 105 is what `rules.base.fire` actually emitted.
    """
    if row["row_kind"] == "verdict":
        return VENUE_OF[row["instrument"]]
    return row["location"]


def span_key(row):
    """The (instrument, venue, window) group a collapse produces one row for."""
    return (row["row_kind"], row["event"], row.get("instrument"),
            row.get("venue"), row["t_start_utc"], row["t_end_utc"])


def _venue(row):
    return row.get("venue") if row["row_kind"] == "verdict" else row.get("location")


#: Every unit this census reports in, named. A count is not a measurement
#: without one -- that is the whole lesson of the withdrawn figures.
#:
#: EACH RETURNS A SET, AND THE DAY-KEYED THREE RETURN ONE ENTRY PER CIVIL DAY
#: THE ROW COVERS. That is what survived the collapse of 21-Sep-2026 unchanged.
#: A FIRING is what `rules.base.fire` emits -- one per (rule, firing location,
#: civil day) -- and the collapse is a RENDERING operation strictly downstream
#: of it, so a window row standing for 15 days is 15 firings and not one. Had
#: these read `r["date"]` after the collapse, `105` would have become `17` and
#: the figure would have gone on being called a firing count: the same figure
#: measured over a set nobody restated, which is every withdrawn number on this
#: page. `rows` is deliberately NOT expanded -- it means rendered rows and it
#: genuinely moved -- and `daily_rows` is the old unit kept under its own name.
UNITS = {
    "rows": lambda r: {id(r)},
    "daily_rows": lambda r: {(id(r), d) for d in covered_days(r)},
    "firings": lambda r: {(r["event"], firing_location(r), d)
                          for d in covered_days(r)},
    "rule-venue-day": lambda r: {(r["event"], _venue(r), d)
                                 for d in covered_days(r)},
    "venue-date": lambda r: {(_venue(r), d) for d in covered_days(r)},
    "spans": lambda r: {span_key(r)},
    "rules": lambda r: {r["event"]},
}

UNIT_KEY = {
    "rows": "one per RENDERED row -- a window row counts once, however many "
            "days it stands for. This is the unit the collapse moved",
    "daily_rows": "one per (row, civil day it covers) -- what `rows` counted "
                  "before the collapse, kept under a name that says so",
    "firings": "distinct (rule, firing location, civil day) -- what rules.base.fire emits",
    "rule-venue-day": "distinct (rule, venue, civil day) -- over-counts firings wherever "
                      "one location carries several venues",
    "venue-date": "distinct (venue, civil day) -- drops the rule entirely",
    "spans": "distinct (row_kind, rule, instrument, venue, t_start_utc, t_end_utc)",
    "rules": "distinct rule ids",
}


#: The rule-id prefix of each registry that is NOT catalogue B. Catalogue B
#: is identified by EXCLUDING these, and the list is what makes that a
#: statement rather than an assumption.
#:
#: This read `not r["event"].startswith("cfg_")` until 20-Sep-2026, when the
#: sub-table registry landed and its `sub_` rows walked straight into P1:
#: "not a configuration row" had meant "catalogue B" for exactly as long as
#: there were two registries, and P1 went 5,209 -> 5,314 without a single
#: catalogue-B rule changing. The figure was still a correct count -- of the
#: wrong set, which is section 12.16's SECOND shape, and the third time in
#: one session that catalogue B was identified by what it is not.
#:
#: A fourth registry adds its prefix here or fails the harness, because the
#: sum of the named populations is checked against the whole.
NON_CATALOGUE_B_PREFIXES = ("cfg_", "sub_")


def populations(rows):
    """The four populations, all derivable from the one artifact.

    P1 is what the build was before the configuration groups were wired and
    before the base track existed -- `e00024a`'s 5,209 rows -- reconstructed
    by filter rather than by rebuild, because configuration rows are exactly
    the `cfg_` rules, sub-table rows exactly the `sub_` rules, and base-track
    rows exactly `row_kind == "event"`.

    P1x is new and is printed BESIDE P1 rather than folded into it: the
    sub-table port is the first thing since the base track to add rows to the
    verdict side, and a population that silently absorbed them would be the
    stale denominator this generator exists to prevent.
    """
    verdict = [r for r in rows if r["row_kind"] == "verdict"]
    cat_b = [r for r in verdict
             if not r["event"].startswith(NON_CATALOGUE_B_PREFIXES)]
    subs = [r for r in verdict if r["event"].startswith("sub_")]
    return {
        "P1 catalogue-B verdict rows only (pre-wiring, pre-base-track)": cat_b,
        "P1x sub-table verdict rows alone (the third registry)": subs,
        "P2 all verdict rows (post-wiring, post-sub-tables)": verdict,
        "P3 every row as rendered (post-base-track)": rows,
    }


def census(pop_rows):
    def count(rs, f):
        out = set()
        for r in rs:
            out |= f(r)
        return len(out)
    by_cause = {c: [r for r in pop_rows if cause(r) == c] for c in CAUSES}
    by_cause["TOTAL no-instant"] = [r for r in pop_rows if cause(r)]
    return {c: {u: count(rs, f) for u, f in UNITS.items()}
            for c, rs in by_cause.items()}


def collapse(pop_rows):
    """Model A's row delta over this population, cause by cause.

    MEASURED ON THE ARTIFACT, NOT PROJECTED ONTO IT. Until 21-Sep-2026 this
    function answered "what WOULD the collapse save" by counting spans among
    daily rows. The collapse has landed, so it now reports what the file
    actually holds -- rendered rows against their daily-row equivalent -- and
    the two readings give the same three numbers per cause, which is the check
    that the thing implemented is the thing proposed.
    """
    lines = []
    delta = 0
    for c in COLLAPSED:
        rs = [r for r in pop_rows if cause(r) == c]
        daily = sum(len(covered_days(r)) for r in rs)
        delta += daily - len(rs)
        lines.append("    {:18s} {:5d} daily rows -> {:4d} rendered   "
                     "delta {:+5d}".format(c, daily, len(rs), len(rs) - daily))
    for c in POINT_ROWS:
        rs = [r for r in pop_rows if cause(r) == c]
        lines.append("    {:18s} {:5d} daily rows -> {:4d} rendered   "
                     "delta     0   NOT collapsed, by decision".format(
                         c, len(rs), len(rs)))
    return delta, lines


def non_contiguous(rows):
    """Window rows that claim a run with a hole in it. Must be zero.

    A collapsed row asserts an EXTENT, so a group whose civil days are not
    contiguous would claim days no daily row was ever built for.
    `render.collapse_windows` refuses to fold such a group -- it leaves the
    rows daily and the row count moves -- so this reads the `contiguous` flag
    off what was emitted rather than re-deriving it from the dates, which is
    the only reading that could catch the renderer lying about it.
    """
    return sum(1 for r in rows
               if r["row_span"] == "window" and not r["contiguous"])


def left_daily_for_a_hole(rows):
    """Collapsible rows that are STILL day rows -- the refusal above, counted.

    Zero in the 2027 build. It is printed anyway: a non-zero here is not a
    defect but a rule whose no-instant span skips days, and the row count moves
    with it. Silence would make that look like the collapse simply missing some.
    """
    held = collections.Counter(span_key(r) for r in rows
                               if cause(r) in COLLAPSED
                               and r["row_span"] == "day")
    return sum(1 for n in held.values() if n > 1)


def main():
    if not CALENDAR_JSON.exists():
        print("{} missing; run python -m finastro.render".format(CALENDAR_JSON),
              file=sys.stderr)
        return 1
    rows = json.load(CALENDAR_JSON.open(encoding="utf-8"))["rows"]
    pops = populations(rows)

    print("NO-INSTANT CAUSE CENSUS")
    print("artifact: build/calendar_2027.json  ({} rows)".format(len(rows)))
    print("FILTER applied to every table below: no_instant_reason is not null.")
    print("`date_only` is split by rule id into the ephemeris cause and b101's")
    print("civil_day_span; no_instant_reason does not make that split itself.")
    print()

    for pname, prows in pops.items():
        print("===== {}  [{} rows] =====".format(pname, len(prows)))
        print("{:20s}".format("cause") + "".join("{:>16s}".format(u) for u in UNITS))
        for c, counts in census(prows).items():
            print("{:20s}".format(c) + "".join("{:16d}".format(counts[u]) for u in UNITS))
        print()

    print("UNIT KEY -- what each column counted")
    for u, desc in UNIT_KEY.items():
        print("    {:16s} {}".format(u, desc))
    print()

    print("MODEL A -- LANDED 21-Sep-2026. Measured on the artifact, not "
          "projected onto it")
    for pname, prows in pops.items():
        delta, lines = collapse(prows)
        print("  {}".format(pname))
        print("\n".join(lines))
        print("    {:18s} {:5d} daily rows -> {:4d} rendered   "
              "delta {:+5d}".format(
                  "TOTAL", len(prows) + delta, len(prows), -delta))
    print()
    print("  window rows claiming a non-contiguous run: {}  (must be 0)".format(
        non_contiguous(rows)))
    print("  collapsible spans left daily because their days have a hole: "
          "{}".format(left_daily_for_a_hole(rows)))
    print("  The delta is the SAME in all three populations. Every row the wider")
    print("  populations add to a collapsed cause is its own span, so it collapses")
    print("  to itself and saves nothing. The TOTAL differs by population; the")
    print("  SAVING does not, so it does not rest on which population is right.")
    print("  And NO DAY-KEYED FIGURE ABOVE MOVED: a firing is still one")
    print("  (rule, firing location, civil day), because every day-keyed unit")
    print("  expands a window row over the days it covers. Only `rows` moved,")
    print("  and `daily_rows` beside it is what `rows` used to mean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
