"""The ten `<h2>` sub-tables, ported. Three of ten; seven blocked or out of scope.

The third registry. `SUBTABLE_REGISTRY` is neither `base.REGISTRY` (catalogue
B, 141 sections) nor `config_rules.CONFIG_REGISTRY` (the 58 configuration
groups), for the reason `subtable_catalogue`'s docstring gives: a denominator
that quietly changes meaning is the failure this build has shipped twice.

WHAT WAS VERIFIED BEFORE ANYTHING WAS WIRED
    All three ported rules were reported against their own section's printed
    rows FIRST, which is the Step-3 discipline and is what makes a firing
    count evidence rather than an assertion.

    * **Bhadra, pp.120-124** -- the section prints **99** windows and the
      karana series reproduces **99 of 99** on BOTH boundaries within **30
      seconds**, with **zero** series spans left unmatched to a printed row.
      The only one of the three with no residual in either direction. Its
      count is also the one this port corrected: every page naming "Bhadra's
      54 windows" was quoting the MONTHLY calendar, which prints 45 fewer than
      the section does -- the same relationship as Total Day's 12 against 11,
      one order of magnitude larger.

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
    None of the ten sections states one about its own condition, so
    `verdict_text` is None on every rule here and
    `subtable_catalogue.check_no_verdict` refuses a rule that arrives with
    one. The monthly calendar prints a tone against these rows -- 'Positive'
    against all 13 Thursday windows, 'Turning Date' against Total Day -- and
    that belongs to a different table in a different chapter. Importing it
    would be the B87 colon failure in a third costume.

    Bhadra is the case that shows this is a reading and not a formality. Its
    section DOES print Result 1, Result 2 and Overall -- Positive, Negative,
    Neutral -- but per WINDOW, derived by a procedure the section states, from
    Mumbai sunrise and sunset (graded B) and the Moon's sign. What it never
    states is a verdict about the condition *a Bhadra*, which is what
    `verdict_text` holds. Three verdict-looking columns, and none of them is
    this rule's verdict.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..panchang import VISHTI_KARANAS
from ..sky import Span, intersect, parse, record_precision, same
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


# ================================================================= 1. BHADRA
_s = S("sec-142")

#: The section's own printed windows, sliced from its first table. 99 rows,
#: each a start date, a start time, an end date and an end time. This is the
#: list the verification counted against, and it is held here so the count
#: comes from the DOCUMENT and not from the karana series, which is the code
#: under test -- section 12.16's point 1.
#:
#: NOT 54. That number is the MONTHLY calendar's, and it is what every page
#: naming "Bhadra's 54 windows" has been quoting. The section prints 99, and
#: the relationship is the one section 6.8 established and the Total Day port
#: found again: the section is the complete printing and the monthly calendar
#: is the incomplete secondary one. The gap here is 45 windows, the largest of
#: the three.
BHADRA_PRINTED = tuple((r[0], r[1], r[2], r[3]) for r in _s.tables[0].rows)

#: The section's SECOND table is its errata -- printed-vs-computed rows, ours,
#: and not part of the printing being reproduced. Counted apart so
#: `printed_rows` is never read as the number of windows.
BHADRA_ERRATA_ROWS = len(_s.tables[1].rows)


def _bhadra_windows():
    """The Vishti karana spans, read off the emitted karana series.

    A BHADRA IS A VISHTI KARANA -- the section's own first sentence says so --
    so the window is one karana's span, and the layer's `karana_spans()` gives
    it: two consecutive `karana_ingress` records, exactly as a tithi's span is
    two consecutive `tithi_ingress` records. Nothing here recomputes the sky,
    per the standing constraint that a rule reads the generated calendar.

    THE SELECTION IS THE DOCUMENT'S OWN, AND IT IS DERIVED RATHER THAN TYPED.
    The section states which karanas are Bhadras -- "the eight windows of each
    lunar month fall on karana numbers 8, 15, 22, 29, 36, 43, 50 and 57" --
    and `panchang.VISHTI_KARANAS` derives exactly those eight from the seven
    movable karana names. The derivation and the printed sentence are
    independent of one another, and they agree, which is what makes this a
    reading of the document rather than a fit to its rows.

    THE DERIVATION CORRECTED THE LAYER RATHER THAN THE OTHER WAY ROUND.
    `panchang.karana_name` named karana 57 *Shakuni*, because FIXED_KARANA's
    keys were 0-based while the lookup tried both conventions and took
    whichever answered. 57 is the EIGHTH Vishti of the lunation, so the layer
    named seven Vishtis per lunation where the source names eight, and printed
    Shakuni twice. It reached the artifact -- `karana` is on every panchang
    block -- and no check could see it: `test_bhadra_two_printings` carries
    its own local numbering and never calls the shared function. The source's
    own sentence is what contradicted it.
    """
    want = set(VISHTI_KARANAS)

    def fn(sky):
        return [s for s in sky.karana_spans() if s.value["karana"] in want]
    return fn


_rule(
    _s,
    id="sub_bhadra",
    rule_family="panchang/karana",
    condition_text="the eight windows of each lunar month fall on karana "
                   "numbers 8, 15, 22, 29, 36, 43, 50 and 57",
    condition_from="para",
    inputs=("panchang/karana",),
    notes="VERIFIED BEFORE WIRING, against this section's own first table, and "
          "the agreement is the strongest of the three sub-table ports: "
          f"**{len(BHADRA_PRINTED)} of {len(BHADRA_PRINTED)}** printed windows "
          "reproduce on BOTH boundaries within 30 seconds, and the check runs "
          "in both directions -- zero series spans are left unmatched to a "
          "printed row, so there is no over-firing to carry as a residual and "
          "none to tune away. The section prints to the minute, so a "
          "sub-30-second residual is its own rounding and not a disagreement "
          "about the sky. On the sixteen January boundaries specifically the "
          "worst is 25 s, which is the figure STEP3_REPORT section 6.8 "
          "recorded for the karana COMPUTATION and is now the figure for the "
          "emitted SERIES -- a different claim, and the one that was missing. "
          "THE COUNT THIS PORT CORRECTS: every page carrying 'Bhadra, 54 "
          "windows' was quoting the MONTHLY calendar. The section prints "
          f"{len(BHADRA_PRINTED)}, and the monthly calendar is the incomplete "
          "secondary printing -- the same relationship as Total Day's 12 "
          "against 11 and the one section 6.8 established. Frame-free: "
          "elongation is a difference of two longitudes, so the ayanamsha "
          "cancels and no ayanamsha choice can move one of these instants; "
          "graded A for that reason. NOT SCOPED TO ONE VENUE, unlike Total "
          "Day: a karana boundary is an instant of the Moon-Sun angle and "
          "belongs to no calendar, and the section says its own Day/Night "
          "parity 'never changes with timezone'. THE SECTION'S THREE VERDICT "
          "COLUMNS ARE NOT THIS RULE'S VERDICT, and that is a reading rather "
          "than an oversight: Result 1, Result 2 and Overall are per-WINDOW "
          "values the section DERIVES by a stated procedure -- Nature 1 needs "
          "Mumbai sunrise and sunset, which are graded B, and Nature 2 needs "
          "the Moon's sign at the opening instant. The section states no "
          "verdict about the condition 'a Bhadra', which is what `verdict_text` "
          "holds, so the rule carries none and `check_no_verdict` is satisfied "
          "by the document rather than by us. Porting the two axes is separate "
          "work and is named in the handoff. SOURCE DEFECT CARRIED, not fixed: "
          "the monthly calendar's 13-Jan cell reads 3:59 where the window "
          "opens at 02:00:06 and the section itself prints 02:00, so the "
          "SECTION is right and the January calendar is about 1h59m late -- "
          "the reverse of the Thursday table's row offset, and the reason "
          "neither printing may be trusted as ground truth without the other.",
)(_bhadra_windows())


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
#: The printed table's own rows, sliced from the section, so the verification
#: count comes from the DOCUMENT and not from the tithi series under test.
KSHIN_PRINTED = tuple(S("kshin-moon").tables[0].rows)

#: Krishna Ashtami is tithi 23 and Shukla Panchami tithi 5; "both days
#: included" makes the window every tithi from the START of 23 to the END of 5.
KSHIN_TITHIS = frozenset(range(23, 31)) | frozenset(range(1, 6))


def _kshin_moon(sky):
    """One span per run of consecutive tithis 23..30, 1..5, off the tithi
    boundary series alone (Sky.tithi_spans): no longitude is sampled."""
    out = []
    for sp in sky.tithi_spans():
        if sp.value["tithi"] not in KSHIN_TITHIS:
            continue
        if out and out[-1].end == sp.start:
            prev = out[-1]
            out[-1] = Span(prev.start, sp.end, prev.value,
                           prev.open_start, sp.open_end)
        else:
            out.append(Span(sp.start, sp.end,
                            {"from": "Krishna Ashtami", "till": "Shukla Panchami"},
                            sp.open_start, sp.open_end))
    return out


_rule(
    S("kshin-moon"),
    id="sub_kshin_malefic_moon",
    rule_family="panchang/tithi",
    condition_text="Moon is malefic from Krishna Ashtami till Shukla Panchmi",
    condition_from="para",
    inputs=("panchang/tithi",),
    notes="PORTED 18-Nov-2026 (registered blocked-on-scope until then: the "
          "section states its condition completely and the tithi series was "
          "always there). VERIFIED BEFORE WIRING against the section's own "
          f"table: {len(KSHIN_PRINTED)} of {len(KSHIN_PRINTED)} printed windows "
          "come back, both boundaries within 2 minutes -- start at the "
          "ingress of Krishna Ashtami (tithi 23), end at the end of Shukla "
          "Panchami (tithi 5). The last printed row is open ('Till year end'); "
          "this build prints that window whole.",
)(_kshin_moon)

#: The printed table's own rows, sliced from the section, so the verification
#: count comes from the DOCUMENT and not from the series under test.
MOON_MERCURY_PRINTED = tuple(S("moon-mercury-d9").tables[0].rows)

#: The three printed boundaries this port does NOT reach inside five minutes,
#: carried rather than tuned away. All three sit on a date the table splits
#: into two rows at a navamsa changeover -- 09-Oct and 16-Oct -- or beside one,
#: which is where a rounded printing shows most. The other 37 land inside five
#: minutes and the median is 1.2.
MOON_MERCURY_LOOSE_BOUNDARIES = (
    ("16-Oct-26", "14:06", 14.8),
    ("11-Jun-26", "11:33", 7.0),
    ("09-Oct-26", "14:04", 5.9),
)


def _same_navamsa(a: str, b: str):
    """Spans where two bodies occupy one navamsa, off the ingress series.

    Nothing here computes a longitude: `Sky.spans` builds each body's D9
    residency out of its own `navamsa_ingress` records, and `intersect` is the
    same helper the sign-level colocation rules use one chart up. The Moon's
    half of this became available on 21-Sep-2026 and is why the section is
    ported at all -- see build_2027.NAVAMSA_BODIES.
    """
    def fn(sky):
        return intersect(list(sky.spans(a, "navamsa")),
                         list(sky.spans(b, "navamsa")), same)
    return fn


_rule(
    S("moon-mercury-d9"),
    id="sub_moon_mercury_in_the_same_navamsh",
    rule_family="ingress/navamsa",
    condition_text=S("moon-mercury-d9").title,
    condition_from="h2",
    inputs=("ingress/navamsa",),
    notes="VERIFIED BEFORE WIRING, against this section's own table: "
          f"**{len(MOON_MERCURY_PRINTED)} of {len(MOON_MERCURY_PRINTED)}** "
          "printed windows come back, each on the navamsa its Navmansh (D9) "
          "cell names and each on the printed date, and every 'Prior to "
          "Market' and 'Till Market Closes' cell is on the correct side of "
          "the 09:15/15:30 session it refers to. Of the 40 boundaries the "
          "table states as clock times, 37 land within five minutes and the "
          "median offset is 1.2 minutes; the three that do not are carried in "
          "MOON_MERCURY_LOOSE_BOUNDARIES rather than fitted. "
          "THIS SECTION WAS BLOCKED FOR ITS WHOLE LIFE ON A FALSE PREMISE AND "
          "THEN ON A TRUE ONE. It was first carried as a cheap port needing "
          "no astronomy-layer change, on the ground that 'navamsa_ingress "
          "carries every Moon and Mercury navamsa crossing' -- it did not, "
          "0 Moon records against 162 Mercury -- and was then blocked on the "
          "Moon's absent D9 series, correctly, until 21-Sep-2026 supplied it. "
          "The count is the thing to hold on to: the 36 rows are the windows "
          "that reach the MARKET SESSION, and the series carries 139 shared "
          "navamsas over 2026. The section is a session table, not a "
          "complete one, which is the same relationship Bhadra's 99 rows have "
          "to the monthly calendar's 54.",
)(_same_navamsa("Moon", "Mercury"))

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

#: The printed table's own rows, sliced from the section.
MARS_MERCURY_PRINTED = tuple(S("mars-mercury").tables[0].rows)

#: Mars's whole-sign drishti: every planet aspects the 7th sign from itself,
#: and Mars also the 4th and 8th (Reference_materials Ch 0, "The Vedic way --
#: counted in whole signs", and Appendix B.2). House 1 is "with".
MARS_DRISHTI = {1: "With (same sign)", 4: "4th", 7: "7th", 8: "8th"}


def _mars_with_or_aspecting_mercury(sky):
    """Mercury in Mars's sign, or in the 4th, 7th or 8th sign counted forward
    from Mars. Whole signs, so no orb: the spans are the intersection of the
    two bodies' sign residencies off the sign_ingress series."""
    from ..ephem import SIGNS

    def house(mars, merc):
        h = (SIGNS.index(merc) - SIGNS.index(mars)) % 12 + 1
        if h not in MARS_DRISHTI:
            return None
        return {"aspect": MARS_DRISHTI[h], "mars_sign": mars, "mercury_sign": merc}
    return intersect(list(sky.spans("Mars", "sign")),
                     list(sky.spans("Mercury", "sign")), house)


_rule(
    S("mars-mercury"),
    id="sub_mars_with_or_aspecting_mercury",
    rule_family="aspect/drishti",
    condition_text=S("mars-mercury").title,
    condition_from="h2",
    inputs=("ingress/sign",),
    notes="PORTED 19-Nov-2026 (blocked on aspect_orb until then). The "
          "section's Aspect column prints '4th', a HOUSE aspect, and Vedic "
          "drishti is counted in whole signs with no orb -- Reference_materials "
          "Ch 0 and Appendix B.2 state it outright (Mars: 4th, 7th, 8th). "
          "VERIFIED against the section's own table: all 3 printed rows are "
          "Mercury 4th from Mars, starts within 11 minutes; its 01-Dec-26 is "
          "the 02-Dec 17:27 Mercury ingress (time exact, date mistyped) and "
          "its 'Till year end' is Mercury leaving Scorpio on 22-Dec. CARRIED, "
          "NOT TUNED AWAY: 2026 also has six 'with' (same-sign) windows the "
          "page does not print although its title names them; no 7th or 8th "
          "window occurred in 2026.",
)(_mars_with_or_aspecting_mercury)

#: The printed table's own rows, sliced from the section.
ECLIPSE_PRINTED = tuple(S("eclipse").tables[0].rows)

#: Lunar month named by the Sun's sidereal sign at the new moon that begins
#: it (amanta reckoning), in the section's own spelling ("Falgun", "Shravan").
MONTH_BY_SUN_SIGN = {"Pisces": "Chaitra", "Aries": "Vaishakh", "Taurus": "Jyeshtha",
                     "Gemini": "Ashadh", "Cancer": "Shravan", "Leo": "Bhadrapad",
                     "Virgo": "Ashwin", "Libra": "Kartik", "Scorpio": "Margashirsh",
                     "Sagittarius": "Paush", "Capricorn": "Magh", "Aquarius": "Falgun"}


def lunar_months(sky):
    """[(new_moon_start, next_new_moon, name)] -- amanta months off the
    lunation series, named by the Sun's sign at the opening new moon; a month
    whose next new moon finds the Sun in the same sign is Adhik."""
    nms = [parse(r["time"]["t_start_utc"])
           for r in sky.class_records("lunation", family="lunation/new_moon")]
    sun = list(sky.spans("Sun", "sign"))

    def sun_sign(t):
        return next(sp.value for sp in sun if sp.start <= t < sp.end)
    out = []
    for a, b in zip(nms, nms[1:]):
        name = MONTH_BY_SUN_SIGN[sun_sign(a)]
        if sun_sign(a) == sun_sign(b):
            name = "Adhik " + name
        out.append((a, b, name))
    return out


def _eclipses(sky):
    """Each eclipse's global first-to-last contact, with its lunar month.

    A SOLAR eclipse is named for the Amavasya it falls on and a LUNAR one for
    its Purnima -- under PURNIMANTA reckoning, which the section's own table
    settles: of its four eclipses the two lunar ones name the same month under
    either system, and the two solar ones (17-Feb-26 Falgun, 12-Aug-26
    Shravan) are purnimanta names; amanta would read Magh and Ashadh. So a
    solar eclipse takes the month the new moon OPENS (amanta), which is the
    purnimanta month that Amavasya closes, and a lunar eclipse the month
    containing its full moon, the same in both systems."""
    months = lunar_months(sky)
    out = []
    for r in sky.class_records("eclipse"):
        c = r["time"]["contacts_global"]
        mx = parse(c["max"]["utc"])
        solar = r["rule_family"] == "eclipse/solar"
        if solar:
            m = min(months, key=lambda m: abs((m[0] - mx).total_seconds()))
        else:
            m = next((m for m in months if m[0] <= mx < m[1]), None)
        out.append(Span(parse(r["time"]["t_start_utc"]), parse(r["time"]["t_end_utc"]),
                        {"eclipse": "Solar" if solar else "Lunar",
                         "type": r["astronomy"].get("eclipse_type"),
                         "month": m[2] if m else None,
                         "max_utc": c["max"]["utc"]}))
    return out


_rule(
    S("eclipse"),
    id="sub_eclipse",
    rule_family="eclipse",
    condition_text=S("eclipse").title,
    condition_from="h2",
    inputs=("eclipse", "lunation", "ingress/sign"),
    notes="PORTED 19-Nov-2026 (blocked on month_system until then). The "
          "section's own Month column settles the system: its two solar "
          "eclipses are named Falgun and Shravan, the PURNIMANTA months of "
          "those Amavasyas (amanta would read Magh and Ashadh); its two lunar "
          "eclipses name the same month either way. VERIFIED: 4 of 4 dates, "
          "kinds and months, and the start/end times are the global contacts.",
)(_eclipses)

#: This section's own rows. 19, of which FOURTEEN are Moon rows -- not the
#: thirteen `vargottama.source_witness.detail.Moon` records. The count is
#: sliced here so it cannot be mistyped again: 19 rows less Rahu, Mercury,
#: Venus and Jupiter's two leaves fourteen.
VARGOTTAM_PRINTED = tuple(S("vargottam").tables[0].rows)

#: Defects this port found in the section, carried and not silently corrected.
#:
#: * The Pad cell of the Venus row reads "2nd". The window it prints --
#:   16-Jul-26 19:08, reproduced to 36 seconds -- is Purva Phalguni pada 1,
#:   whose navamsa is Leo and therefore vargottama; pada 2's navamsa is Virgo
#:   and can never be. Config had pada 1 recorded already, from the other
#:   direction, so the cell and the config disagreed and nothing could see it.
#: * Mercury's and Venus's printed END times are 5h07m late and 2h01m early
#:   against the computed pada boundary. Mercury's lands inside the window and
#:   Venus's outside it, which is worth separating: `source_defects.note` says
#:   the fifteen non-defect rows all have end times "inside the window", and
#:   Venus's does not.
#: * Rahu's two boundaries are 35 and 42 minutes out, which is not a defect at
#:   all but the mean node's resolution: Rahu crosses one navamsa in 63 days,
#:   so a boundary to the minute is a precision the quantity does not have.
VARGOTTAM_SOURCE_DEFECTS = (
    "Venus / Purva Falguni: Pad cell reads 2nd; the printed window is pada 1",
    "Mercury / Revati 4th: printed end 30-Apr-26 1:46, computed 6:52 "
    "(inside the window)",
    "Venus / Purva Falguni: printed end 19-Jul-26 22:28, computed 20:27 "
    "(OUTSIDE the window)",
)

#: Windows the condition produces and the appendix does not print. The Sun's
#: is the one that matters: it is vargottama in Uttara Ashadha, WHICH THE SUN
#: LORDS, for six days in January 2026, which is this appendix's exact
#: condition -- and the appendix omits it. That is a fresh instance of
#: `source_findings.sun_never_labelled`, found on a new surface: the finding
#: was recorded off the Sun's dignity column and its D9 absence, and here the
#: Sun qualifies for a table it is simply left out of. Jupiter's is a carry-in
#: that opened on 05-Dec-25, which the appendix has a plain reason to omit.
VARGOTTAM_UNPRINTED = (
    "Sun / Uttara Ashadha padas 1-2, 11-Jan-26 08:36 to 17-Jan-26 21:39",
    "Jupiter / Punarvasu pada 3, opening 05-Dec-25 17:25 and running to "
    "04-Jan-26 18:45",
)


def _vargottama_in_own_nakshatra():
    """Vargottama windows in a nakshatra the body itself lords.

    Both halves are read off emitted series and neither is typed. Vargottama
    is `sign == navamsa` -- the config's own definition -- taken as the
    intersection of the body's rashi and D9 residencies, so the equality is
    evaluated on spans bounded by ingress records rather than on a sample.
    The lordship is B2's own printed nakshatra-lord table, through
    `names.nakshatra` so the document's spellings ("Shatbhisha", "Purva
    Falguni") reach the series' canonical ones and a missing bridge raises
    instead of quietly dropping a body.

    The appendix is a filter over the same boolean and not a separate state,
    exactly as config records: nothing here emits an "own-nakshatra
    vargottama" value.
    """
    own: dict[str, set[str]] = {}
    for nak, lord in _NAK_LORDS.items():
        own.setdefault(lord, set()).add(names.nakshatra(nak))

    def fn(sky):
        out = []
        for body, stars in own.items():
            varg = intersect(list(sky.spans(body, "sign")),
                             list(sky.spans(body, "navamsa")), same)
            mine = [s for s in sky.spans(body, "nakshatra")
                    if s.value in stars]
            out += [Span(s.start, s.end, {"body": body, "nakshatra": s.value},
                         s.open_start, s.open_end, s.precision)
                    for s in intersect(varg, mine, lambda _v, n: n)]
        return sorted(out, key=lambda s: s.start)
    return fn


_rule(
    S("vargottam"),
    id="sub_planet_vargottam_in_their_own_nakshatra",
    rule_family="ingress/navamsa",
    condition_text=S("vargottam").title,
    condition_from="h2",
    inputs=("ingress/navamsa", "ingress/nakshatra", "ingress/sign"),
    notes="VERIFIED BEFORE WIRING, against this section's own table: "
          f"**{len(VARGOTTAM_PRINTED)} of {len(VARGOTTAM_PRINTED)}** printed "
          "rows come back on the right body and the right nakshatra, and 12 "
          "of them on both boundaries within three minutes. FOURTEEN of the "
          "19 are Moon rows and every one of them is Rohini pada 2, which is "
          "the Moon's only vargottama-in-own-nakshatra arc -- Rohini's second "
          "quarter is the Taurus navamsa of Taurus. "
          "THE FOUR END-DATE TYPOS CAME BACK, AND ONLY THEY. "
          "`vargottama.source_defects` convicts four rows -- 28-Jan, 20-Apr, "
          "11-Jul and 01-Oct-2026 -- on an independent Swiss Ephemeris "
          "recomputation, and this series reaches the same four by a "
          "different route: each printed end is 24 hours plus one or two "
          "minutes past the computed one, while the two control rows that "
          "genuinely cross midnight (24-Feb, 28-Oct) come back clean. Two "
          "routes, one verdict. What the routes did NOT agree on is recorded "
          "in VARGOTTAM_SOURCE_DEFECTS and VARGOTTAM_UNPRINTED rather than "
          "reconciled away.",
)(_vargottama_in_own_nakshatra())

#: The printed table's own rows, sliced from the section.
PARIVARTAN_PRINTED = tuple(S("rashi-parivartan").tables[0].rows)


def _moon_parivartan(sky):
    """Moon in a sign owned by planet X while X is in Cancer, the Moon's own
    sign: a mutual exchange (parivartana -- "two planets occupying each other's
    signs", Reference_materials Ch 5). Lordship is the classical Vedic table
    (Ch 0's sign table, Appendix B), which is ephem.SIGN_LORDS; the nodes and
    the outer planets own no sign and cannot exchange."""
    from ..config import CONF
    # Sign -> lord off the config's own-sign lists, the same table ephem
    # derives SIGN_LORDS from; a rule module may not import the ephemeris.
    SIGN_LORDS = {sign: body for body, spec in CONF["dignity"]["signs"].items()
                  for sign in spec["own"]}
    moon = list(sky.spans("Moon", "sign"))
    out = []
    for x in ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        out += intersect(moon, list(sky.spans(x, "sign")),
                         lambda m, s, x=x: {"planet": x, "sign": m}
                         if s == "Cancer" and SIGN_LORDS[m] == x else None)
    return sorted(out, key=lambda sp: sp.start)


_rule(
    S("rashi-parivartan"),
    id="sub_moon_rashi_parivartan_yog",
    rule_family="residency/exchange",
    condition_text=S("rashi-parivartan").title,
    condition_from="h2",
    inputs=("ingress/sign",),
    notes="PORTED 19-Nov-2026 (blocked on sign_lordship until then: the "
          "lordship is now read from Reference_materials, Ch 0's sign table "
          "and Appendix B, which agree with the config's own-sign lists). "
          "VERIFIED against the section's own table: all 19 printed rows come "
          "back on planet and sign, 17 with both boundaries within 5 minutes. "
          "The other two disagree with the document itself: 02-Jun-26 starts "
          "when Jupiter enters Cancer, which B20 prints at 01:49 (this row "
          "01:33), and 18-Sep-26 ends when the Moon leaves Sagittarius at "
          "11:15 on 21-Sep (printed 21:44). CARRIED: five 2026 exchanges the "
          "page omits -- Sun twice, Venus twice, Mercury once.",
)(_moon_parivartan)


# ------------------------------------------------------------------ checks
if len(SUBTABLE_REGISTRY) != len(SUBTABLES):          # pragma: no cover
    raise SystemExit(
        f"{len(SUBTABLE_REGISTRY)} sub-table rules against "
        f"{len(SUBTABLES)} sections in the document. Every one of them "
        "carries a rule -- ported or blocked with its input named -- so the "
        "denominator is the document's and a section cannot go missing "
        "quietly, which is the whole reason this registry exists")


def ported() -> list[Rule]:
    return [r for r in SUBTABLE_REGISTRY if r.status in FIRING_STATUSES]


def blocked() -> list[Rule]:
    return [r for r in SUBTABLE_REGISTRY if r.status == STATUS_BLOCKED]
