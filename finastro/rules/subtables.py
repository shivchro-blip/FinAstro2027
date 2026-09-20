"""The nine `<h2>` sub-tables, ported. Two of nine; seven blocked or out of scope.

The third registry. `SUBTABLE_REGISTRY` is neither `base.REGISTRY` (catalogue
B, 141 sections) nor `config_rules.CONFIG_REGISTRY` (the 58 configuration
groups), for the reason `subtable_catalogue`'s docstring gives: a denominator
that quietly changes meaning is the failure this build has shipped twice.

WHAT WAS VERIFIED BEFORE ANYTHING WAS WIRED
    Both ported rules were reported against their own section's printed rows
    FIRST, which is the Step-3 discipline and is what makes a firing count
    evidence rather than an assertion.

    * **Total Days in Year, p.126** -- the section prints **12** dates in a
      six-row, two-column table. `panchang.total_days(2026)` reproduces all
      **12 of 12**, with no date it does not print. The source's own monthly
      calendar prints only **11** of them, omitting 22-Apr-26; the section is
      the complete printing and the monthly calendar is the incomplete
      secondary one, which is the SAME relationship STEP3_REPORT section 6.8
      established for Bhadra, in the same direction.

    * **Rahu or Ketu Nakshtra on a Thursday, p.127** -- **13 of 13** printed
      rows reproduce, and the agreement is on THREE independent columns and
      not only the date:
        - every one of the 13 dates is a Thursday and is reproduced;
        - every one of the 13 NAKSHATRA cells is reproduced. That column is
          what makes the reading the document's own rather than ours: the
          six nakshatras it names resolve through B2's own lord table to
          exactly Rahu and Ketu, so the condition is read off the source and
          not fitted to its dates;
        - of the five boundaries the table states as clock times rather than
          as market open or close, all five land within **50 seconds** of the
          computed crossing.

    The residuals are recorded rather than tuned away, and the largest of
    them is a CONVENTION difference and not a disagreement about the sky:
    the section tabulates market SESSIONS and this layer dates by civil day,
    so the Thursday rule fires on 21 Mumbai civil days where the section
    prints 13, and 16 of the 21 overlap the session the section is about.
    See `THURSDAY_OUTSIDE_SESSION`, `THURSDAY_UNPRINTED` and
    `THURSDAY_ROW_OFFSET` below, each with its own count.

WHY THESE RULES CARRY NO VERDICT
    None of the nine sections prints one, so `verdict_text` is None on every
    rule here and `subtable_catalogue.check_no_verdict` refuses a rule that
    arrives with one. The monthly calendar prints a tone against these rows
    -- 'Positive' against all 13 Thursday windows, 'Turning Date' against
    Total Day -- and that belongs to a different table in a different
    chapter. Importing it would be the B87 colon failure in a third costume.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..sky import Span, parse, record_precision
from . import names
from .base import FIRING_STATUSES, Rule, STATUS_BLOCKED
from .visibility import MUMBAI_ONLY
from .ref_tables import _NAK_LORDS
from .subtable_catalogue import S, SUBTABLES, check_no_verdict

# --------------------------------------------------------------- the registry
#: Separate from both other registries and deliberately so: these are not
#: catalogue-B sections and not configuration groups, and neither
#: `rules.sections_ported()` nor the 58 may be able to see them.
SUBTABLE_REGISTRY: list[Rule] = []
_SEEN: set[str] = set()

#: The blocking vocabulary, closed, so "blocked on what" is countable off the
#: registry rather than parsed out of prose -- the same rule
#: `config_rules.MISSING_INPUTS` is held to.
MISSING_INPUTS = {
    "moon_navamsa_series":
        "the Moon's navamsa ingress series. The Moon crosses a navamsa every "
        "two hours and the astronomy layer emits NONE for it: "
        "build/astronomy_2026.json and build/astronomy_2027.json carry "
        "navamsa_ingress for eleven bodies and 0 records for the Moon. This "
        "is the same absence that blocks B71d and that stops the navamsa "
        "ladder ranking the Moon in batch 2, and it is a new SERIES rather "
        "than a rule -- about 1,450 records a year, in both years",
    "sign_lordship":
        "a sign lordship table. A Rashi Parivartan is a mutual exchange -- "
        "the Moon in a planet's own sign while that planet is in the Moon's "
        "-- so it cannot be evaluated without knowing which planet owns which "
        "sign. The layer carries a NAKSHATRA lord table, sliced from B2's own "
        "printed table, and no sign lord table at all; the source prints none "
        "either, so this is an input the document withholds and not one we "
        "declined to derive",
    "aspect_orb":
        "the aspect doctrine -- graha drishti or a degree orb. This section's "
        "own Aspect column reads '4th' on all three of its rows, which is a "
        "house aspect and not a conjunction or an opposition; the layer emits "
        "aspect/conjunction and aspect/opposition and no other angle. "
        "`aspect_orbs` in config, the same open question that blocks "
        "gold-bullish#6",
    "month_system":
        "the lunar month system, amanta or purnimanta. The eclipses "
        "themselves are emitted and carry the weekday and both nakshatras, so "
        "every column of this table is reproducible EXCEPT its Month column, "
        "which reads Falgun and Shravan. `month_system_confirmation` in "
        "config, and B111",
    "no_dated_window":
        "nothing to port: the section is an arithmetic forecast for a Samvat "
        "year and prints no dated window, so there is no condition to "
        "register a reproduction against",
    "scope":
        "scope rather than an input. The section states its own condition "
        "completely and the layer already emits what it needs, so it is "
        "portable in principle and was not ported in this batch. Registered "
        "blocked rather than omitted so the gap is visible as SCOPE and is "
        "not mistaken for something the document withholds -- the ruling B130 "
        "is registered under",
}


def _register(r: Rule, sub) -> Rule:
    """Register one sub-table rule, after the checks that make it one."""
    check_no_verdict(r.id, sub, r.verdict_text, r.verdict_from)
    if not r.id.startswith("sub_"):
        raise ValueError(
            f"{r.id}: a sub-table rule id begins `sub_`, so a row's registry "
            "is readable off its rule id with no lookup -- the field that "
            "separates a configuration row from a catalogue-B one is `event`, "
            "and this keeps that true for three registries")
    if r.id in _SEEN:
        raise ValueError(f"duplicate sub-table rule id {r.id}")
    if not sub.carries(r.condition_text):
        raise ValueError(
            f"{r.id}: condition {r.condition_text!r} is not a substring of "
            f"{sub.key}; a condition is sliced from the document, never typed")
    if r.status == STATUS_BLOCKED:
        unknown = [k for k in r.missing_inputs if k not in MISSING_INPUTS]
        if unknown:
            raise ValueError(
                f"{r.id}: blocked on {unknown}, not in MISSING_INPUTS")
    _SEEN.add(r.id)
    SUBTABLE_REGISTRY.append(r)
    return r


def _rule(sub, **kw):
    def wrap(fn):
        _register(Rule(section=sub, fn=fn, **kw), sub)
        return fn
    return wrap


def _blocked(sub, **kw) -> Rule:
    return _register(Rule(section=sub, status=STATUS_BLOCKED, **kw), sub)


# ============================================================ 2. TOTAL DAYS
_s = S("total-days")

#: The section's own printed dates, sliced out of its six-row, two-column
#: table rather than retyped. This is the list the verification counted
#: against, and it is held here so the count comes from the DOCUMENT and not
#: from `panchang.total_days`, which is the code under test.
TOTAL_DAY_PRINTED = tuple(cell for row in _s.tables[0].rows for cell in row)


def _total_days():
    """The astronomy layer's `total_day` records, as CIVIL-DAY spans.

    The condition is the source's own arithmetic -- dd + mm == yy -- and no
    ephemeris is consulted, which is why `calendar/total_day` is graded A.
    The rule reads the emitted series and never `panchang.total_days`, per
    the standing constraint that a rule reads the generated calendar and
    never recomputes the sky.

    THE SPAN HAS NO INSTANT, AND SAYING SO IS THE POINT. A Total Day is a
    property of the DATE -- the day number plus the month number equalling
    the year -- and nothing crosses anything at any moment of it. The record
    is emitted `kind: civil_day`, `precision: date_only`, so both of its
    endpoints are IST midnights at 18:30Z and neither is a time.

    The first version of this function built `Span(t, t, ...)` off the start
    stamp and left `precision` at its "exact" default, and the renderer duly
    printed **00:00 IST on 60 rows** -- the identical defect section 12.17
    records for the combust windows, reproduced here about eighteen hours
    after that section was read. It was caught by
    `test_a_row_without_an_instant_carries_no_clock_time`, which exists
    because of the first occurrence, on the artifact rather than in review.
    """
    def fn(sky):
        out = []
        for r in sky.class_records("total_day"):
            out.append(Span(parse(r["time"]["t_start_utc"]),
                            parse(r["time"]["t_end_utc"]),
                            {"id": r["id"]},
                            precision=record_precision(r)))
        return out
    return fn


_rule(
    _s,
    id="sub_total_days_in_year",
    rule_family="calendar/total_day",
    condition_text=_s.title,
    condition_from="h2",
    inputs=("calendar/total_day",),
    locations=MUMBAI_ONLY,
    notes="MUMBAI ONLY, AND THE REASON IS THE CONDITION ITSELF AND NOT A "
          "HORIZON. A Total Day is `dd + mm == yy` -- arithmetic on a printed "
          "civil DATE, with no instant and no body. The record is emitted "
          "kind: civil_day at IST midnight, so under civil_day_overlap it "
          "straddles the previous EASTERN day, and 26-Jan-2027 IST is "
          "25-Jan-2027 in New York. Emitting the New York row would date the "
          "condition to 25-Jan, where 25 + 1 is 26 and the source's own "
          "arithmetic DOES NOT HOLD: the row would assert, in the venue's own "
          "calendar, something false. Every other date-only rule is scoped "
          "this way for a measurement reason -- the Mumbai horizon; this one "
          "is scoped because the condition is a fact about a calendar and "
          "this build carries one calendar per venue. Measured: both venues "
          "gave 84 rows over 24 distinct dates, 12 of which the arithmetic "
          "fails on. VERIFIED BEFORE WIRING, against this section's own table: it "
          f"prints {len(TOTAL_DAY_PRINTED)} dates and "
          "`panchang.total_days(2026)` reproduces 12 of 12 with no extra. "
          "The emitted series carries 12 records in each of 2026 and 2027, "
          "and they reached the base track without any rule reading them, "
          "which is STEP4_DECISIONS section 12.16's THIRD shape -- code that "
          "exists, was verified, and was never connected. The source's "
          "monthly calendar prints 11 of the 12, omitting 22-Apr-26; the "
          "section is the complete printing, exactly as section 6.8 found for "
          "Bhadra. The monthly calendar also prints 'Turning Date' against "
          "these rows and this section prints no verdict, so the rule carries "
          "none: the tone belongs to the other table.",
)(_total_days())


# =============================================== 3. RAHU OR KETU ON THURSDAY
_s = S("rahu-ketu-thu")

#: The nakshatras whose lord is a node, resolved through B2's OWN printed
#: lord table. Not a typed list: `_NAK_LORDS` is sliced from the document, so
#: the six names below are the document's answer to "which nakshatra is a
#: Rahu or Ketu nakshatra" and not ours. This is what makes the reading a
#: reading rather than a fit to the 13 dates -- section 12.10's ruling is
#: that a parameter fitted to the rows it must reproduce carries no evidence.
NODE_NAKSHATRAS = tuple(sorted(
    names.nakshatra(n) for n, lord in _NAK_LORDS.items()
    if lord in ("Rahu", "Ketu")))

#: The section's own Nakshatra column, bridged to the layer's spelling. The
#: independent expected CONTENT the verification counted against -- section
#: 12.16's point 1: a check whose expected value comes from the code under
#: test cannot fail.
THURSDAY_PRINTED = tuple(
    (row[0], names.nakshatra(row[3])) for row in _s.tables[0].rows)

#: THE SECTION IS A TABLE OF MARKET SESSIONS AND THIS LAYER DATES BY CIVIL
#: DAY, and that difference is the whole of this rule's over-firing. The
#: section's own Start Time and End Time columns read 'Prior to Market hours'
#: and 'Till Market closes'; the rule layer's standing convention is
#: `weekday_rule.convention: civil_day_overlap`, under which a span touching
#: any part of a Thursday fires on it. Measured, over 2026 Mumbai:
#:
#:     printed by the section               13
#:     fired under civil-day overlap        21
#:     of which overlap the 9:15-15:30 session  16
#:
#: So the 8 extras split in two, and the two halves are different findings:
#:
#: * `THURSDAY_OUTSIDE_SESSION` -- 5 Thursdays on which the Moon holds a node
#:   nakshatra at some point in the civil day but at no point while the
#:   market is open. The section could not print these and is not wrong to
#:   omit them. They are the measured cost of the convention difference, and
#:   the layer does not narrow them away, because 9:15 and 15:30 are NOT
#:   printed in this section -- it names the session in words and never its
#:   hours. Supplying them would be a reading we supplied, which this build
#:   carries as `ok*` with a flag on every row, and it would be supplied to
#:   make a residual disappear, which section 12.16 files under remediation.
#:
#: * `THURSDAY_UNPRINTED` -- 3 Thursdays that DO overlap the session and that
#:   the section still does not print. All three are Mula, and Mula IS
#:   printed on 10-Dec-26, so the nakshatra is not excluded; 12-Mar-26 runs
#:   the full session, so no duration filter explains them either. Narrowing
#:   the rule to exclude exactly these three would be a fit to three rows
#:   with nothing left to falsify it -- section 12.10's zero-degrees-of-
#:   freedom ruling -- so the residual is carried and not tuned away.
THURSDAY_UNPRINTED = ("2026-02-12", "2026-03-12", "2026-11-12")
THURSDAY_OUTSIDE_SESSION = ("2026-04-09", "2026-05-14", "2026-07-16",
                            "2026-11-19", "2026-11-26")

#: A source defect this port found, carried and not silently fixed. The
#: section's End Time column has rows 6 and 7 interchanged: it prints 14:57
#: against 25-Jun-26 and 'Till Market closes' against 09-Jul-26, while the
#: computed crossings are the other way round -- 25-Jun runs to the close and
#: 09-Jul ends at 14:56:23. The section's own note says so ("source table has
#: an apparent one-row date/nakshatra offset in the original"), and the
#: source's MONTHLY calendar is the third witness: it prints 09-Jul ending
#: 14:57 and 25-Jun running to 15:30, agreeing with the sky. So here the
#: SECTION is the defective printing and the monthly calendar is right, which
#: is the exact reverse of the Bhadra defect of section 6.8 -- and the reason
#: neither printing may be trusted as ground truth without the other.
THURSDAY_ROW_OFFSET = ("2026-06-25", "2026-07-09")


def _moon_in_node_nakshatra():
    """Moon nakshatra spans whose nakshatra's lord is Rahu or Ketu.

    The weekday half is NOT applied here. It is `Rule.weekdays`, which
    `fire()` applies after the span has been resolved to a civil day at a
    location -- the only point at which a weekday exists. Doing it inside the
    condition would force one calendar on both venues, which is what batch
    3's per-location split forbids.
    """
    want = set(NODE_NAKSHATRAS)

    def fn(sky):
        return [s for s in sky.spans("Moon", "nakshatra") if s.value in want]
    return fn


_rule(
    _s,
    id="sub_rahu_or_ketu_nakshatra_on_a_thursday",
    rule_family="ingress/nakshatra",
    condition_text=_s.title,
    condition_from="h2",
    inputs=("ingress/nakshatra", "weekday"),
    weekdays=(3,),
    notes="VERIFIED BEFORE WIRING, on three independent columns of this "
          "section's own table: 13 of 13 dates, 13 of 13 NAKSHATRA cells, and "
          "all five of the boundaries it states as clock times within 50 s of "
          "the computed crossing. The nakshatra column is the one that "
          "matters: its six names resolve through B2's own printed lord table "
          "to exactly Rahu and Ketu, so 'Rahu or Ketu Nakshtra' is read off "
          "the document rather than fitted to its dates. Two residuals are "
          "carried and not tuned away -- THURSDAY_UNPRINTED, three further "
          "Thursdays the section omits, and THURSDAY_ROW_OFFSET, the "
          "interchanged end times the section's own note flags and the "
          "monthly calendar contradicts. The section prints no verdict; the "
          "monthly calendar's 'Positive' belongs to that table and not to "
          "this rule. FIRING COUNT, STATED WITH ITS CONVENTION: 13 printed, "
          "21 fired on 2026 Mumbai civil days, 16 of those overlapping the "
          "market session the section actually tabulates. The gap is "
          "civil_day_overlap against a session table and not a disagreement "
          "about the sky -- see THURSDAY_OUTSIDE_SESSION.",
)(_moon_in_node_nakshatra())


# ================================================== THE SEVEN NOT PORTED HERE
_blocked(
    S("kshin-moon"),
    id="sub_kshin_malefic_moon",
    rule_family="panchang/tithi",
    condition_text="Moon is malefic from Krishna Ashtami till Shukla Panchmi",
    condition_from="para",
    inputs=("panchang/tithi",),
    missing_inputs=("scope",),
    notes="NOT blocked on anything the document withholds, and recorded that "
          "way deliberately. This section STATES its own condition completely "
          "-- 'Moon is malefic from Krishna Ashtami till Shukla Panchmi (both "
          "days included)' -- and the tithi series that bounds both ends is "
          "emitted and graded A. It is 13 printed windows and is portable "
          "today. It was not in the three ports this batch was asked for, and "
          "registering it blocked-on-scope rather than leaving it out is the "
          "B130 ruling: a gap that is OURS is visible as ours, and is not "
          "mistaken for a missing input.",
)

_blocked(
    S("moon-mercury-d9"),
    id="sub_moon_mercury_in_the_same_navamsh",
    rule_family="ingress/navamsa",
    condition_text=S("moon-mercury-d9").title,
    condition_from="h2",
    missing_inputs=("moon_navamsa_series",),
    notes="36 printed windows, and the largest of the sub-tables. It was "
          "carried on the handoff as a CHEAP port needing no astronomy-layer "
          "change, on the ground that 'navamsa_ingress carries every Moon and "
          "Mercury navamsa crossing'. It does not: the artifact holds 162 "
          "Mercury navamsa records and 0 Moon ones, in both years. Mercury's "
          "half is ready and the Moon's half is a new series -- the same one "
          "B71d is blocked on -- so this is a port of Bhadra's kind and not "
          "of Total Day's. Found by reading the artifact before the code, "
          "which is what the standing instruction is for.",
)

_blocked(
    S("rainfall"),
    id="sub_rainfall_calculation",
    rule_family="calendar/samvat",
    condition_text=S("rainfall").title,
    condition_from="h2",
    missing_inputs=("no_dated_window",),
    notes="An arithmetic forecast over the Samvat year -- residual number, "
          "multiply, add five, divide by seven -- resolving to one verdict "
          "for the whole year and no dated window. There is no condition here "
          "to register a reproduction against, which is the same reading "
          "silver-bullish#4 is blocked under.",
)

_blocked(
    S("mars-mercury"),
    id="sub_mars_with_or_aspecting_mercury",
    rule_family="aspect/drishti",
    condition_text=S("mars-mercury").title,
    condition_from="h2",
    missing_inputs=("aspect_orb",),
    notes="All three printed rows carry '4th' in their own Aspect column, "
          "which is a house aspect. The layer emits conjunction and "
          "opposition and no other angle, so the WITH half is computable and "
          "the ASPECTING half is not, and half a disjunction is not this "
          "section -- the ruling silver-bullish#10 is blocked under.",
)

_blocked(
    S("eclipse"),
    id="sub_eclipse",
    rule_family="eclipse",
    condition_text=S("eclipse").title,
    condition_from="h2",
    missing_inputs=("month_system",),
    notes="Every column of this table is reproducible except one. The four "
          "eclipses are emitted, and the records carry the weekday and both "
          "nakshatras the table prints. Its Month column reads Falgun and "
          "Shravan, and naming a lunar month needs the amanta/purnimanta "
          "question settled -- `month_system_confirmation`, the same input "
          "that blocks B111 and cfg_silver_bullish_18.",
)

_blocked(
    S("vargottam"),
    id="sub_planet_vargottam_in_their_own_nakshatra",
    rule_family="ingress/navamsa",
    condition_text=S("vargottam").title,
    condition_from="h2",
    missing_inputs=("moon_navamsa_series",),
    notes="Vargottam is the D1 and D9 signs agreeing at an instant, which "
          "needs both frames for the body named. Thirteen of the nineteen "
          "printed rows are MOON rows, and the Moon has no navamsa ingress "
          "series at all, so the majority of this table sits behind the same "
          "absence that blocks the D9 section above. The non-Moon rows sit "
          "behind B6's blocker, which is the same shape one body along.",
)

_blocked(
    S("rashi-parivartan"),
    id="sub_moon_rashi_parivartan_yog",
    rule_family="residency/exchange",
    condition_text=S("rashi-parivartan").title,
    condition_from="h2",
    missing_inputs=("sign_lordship",),
    notes="A parivartan is a mutual exchange of signs, so it cannot be "
          "evaluated without knowing which planet owns which sign. The layer "
          "carries a nakshatra lord table sliced from B2's own printed table "
          "and no sign lord table; the source prints none either. The Moon's "
          "and both partners' sign ingresses ARE emitted, so this is one "
          "table away rather than one series away -- and the table would be "
          "ours, which is the distinction that keeps it blocked.",
)


# ------------------------------------------------------------------ checks
if len(SUBTABLE_REGISTRY) != len(SUBTABLES):          # pragma: no cover
    raise SystemExit(
        f"{len(SUBTABLE_REGISTRY)} sub-table rules against "
        f"{len(SUBTABLES)} sections in the document. Every one of the nine "
        "carries a rule -- ported or blocked with its input named -- so the "
        "denominator is the document's and a section cannot go missing "
        "quietly, which is the whole reason this registry exists")


def ported() -> list[Rule]:
    return [r for r in SUBTABLE_REGISTRY if r.status in FIRING_STATUSES]


def blocked() -> list[Rule]:
    return [r for r in SUBTABLE_REGISTRY if r.status == STATUS_BLOCKED]
