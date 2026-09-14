"""Batch 3 -- the weekday and panchang families.

Thirty-one catalogue-B sections whose condition is a fact about the *calendar*
rather than about a planet: which weekday it is (B72, B97, B102-B105, B110 and
the tithi-on-a-weekday sections), which tithi and fortnight (B64-B69, B73-B76,
B95, B100, B101, B106, B108, B109), which yoga (B56, B96, B108), and the lunar
month's own turning points (B55, B60, B61, B62, B71, B111).

Twenty-nine of the thirty-one fire, and the two that do not are worth more
than the twenty-nine: each names something the layer genuinely does not have.

The batch was written against an astronomy layer that emitted neither a tithi
boundary nor a sunrise, and twenty-two of these sections were blocked on that.
Three restorations cleared them, in three separate passes, and each pass is
recorded here rather than smoothed into a single "now it works":

**The tithi and yoga boundary series** cleared twelve sections. A tithi is
about 23 hours 40 minutes long and its boundaries fall where nothing else is
happening, so they were not recoverable from records sampled at other events;
`tithi_ingress` and `yoga_ingress` supply them, and `Sky.tithi_spans()` reads
them the way `Sky.spans()` reads a sign series.

**The sunrise and sunset series** cleared five more -- B64, B66, B67, B68, B69
-- and made a sixth ambiguous rather than blocked. Kshay and Vriddhi are
statements about a tithi's boundaries AND the day's: a tithi is Kshay when no
sunrise falls inside it and Vriddhi when two do, so the boundary series settled
exactly half of each. Pradosh is the same shape one horizon later.

**A calendar helper** cleared B101, which was never an astronomy gap at all.
"Three Saturday in Shukla Paksh" counts a weekday inside a window at a venue,
and `sky.weekdays_in_span` counts it -- arithmetic beside `civil_days`, reading
no record and asking no ephemeris.

What is left is B62, which needs a first-crescent visibility computation Step 3
tested and rejected on evidence, B71's navamsa half, B111's lunar month system,
and B55's remark, which is now ambiguous rather than blocked: the sunrise it
needed exists, and what remains is which of two ghati definitions the source
means.

**What does fire is the Moon's own position, and it is validated twice.** The
Moon's nakshatra and sign ingress series are emitted in full -- 422 nakshatra
spans and 188 sign spans -- so any condition of the form "the Moon is in X" is
exact. Two independent reproductions of the source's own tables establish that
this is what the document means by a bare nakshatra name:

* B71 tabulates fourteen Uttara Phalguni windows for 2026 and the Moon's
  ingress series reproduces **all fourteen**, start and end, to the minute;
* B104's six Mrigashira-on-Thursday dates and B105's four Uttara
  Ashadha-on-Monday dates come back **exactly**, under the project's own
  `civil_day_overlap` convention and no other.

**Where the source's own tables fall short, it is recorded rather than
smoothed.** Across the six Moon-nakshatra-on-weekday sections the condition
occurs **23 times** in 2026 and the document prints **18 dates** -- seventeen of
those occurrences, six omitted, and one date on which the condition does not
hold at all: B102's 28-Jun-2026, where Anuradha ended at 22:11 the previous
evening. The six omissions are not explained by
overlap length (B104 prints a 1.19-hour window and B102 omits a 16.83-hour
one), nor by market hours, nor by the weekday. The tables are incomplete; the
titles are the rule. The harness recomputes all six sections against the 2026
sky and pins the omissions and the spurious date by name, so the finding cannot
decay into an impression.

**Panchak is the one rule here whose words are partly ours.** The document
names Panchak thirteen times and defines it nowhere. Registered
`resolved_ambiguity`, ruled on against its own thirteen printed windows, and
never counted in with the executable rules.

**The weekday is applied per location, and cannot be applied anywhere else.**
"Anuradha on Sunday" is one condition in two frames: the Moon's nakshatra is a
fact about the sky, Sunday is a fact about the calendar a venue keeps. So the
conditions below return sky spans only, the weekday is declared on the rule,
and `fire` applies it once a span has become a day at a location. The lunar
eclipse of 21-Feb-2027 falls on Sunday in Mumbai and Saturday in New York, and
both rows are correct.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..sky import (Span, civil_day_span, intersect, parse, where,
                   weekdays_in_span)
from . import names
from .base import ambiguous, blocked, resolved, rule
from .catalogue import B, split_final, split_sentences, split_statement

# ------------------------------------------------------------ missing inputs
# One string is left of the five this module once carried. The other four named
# the tithi series, the yoga series, sunrise, sunset and a per-location weekday
# count, and every one of those is now supplied -- so they are deleted rather
# than kept with a qualifier. A missing-input string that no longer describes a
# missing input is worse than no string: it goes on reporting an absence that
# has been filled, and the harness checks for exactly that decay.
MOON_NAVAMSA = (
    "the Moon's navamsa ingress series. The Moon crosses a navamsa every two "
    "hours and the astronomy layer emits no navamsa ingress for it, which is "
    "the same absence that stops the navamsa ladder ranking the Moon in batch 2"
)

#: Panchak's two signs, and the whole of the resolved reading. A constant, so
#: the rule's condition and the harness's reproduction of the source's thirteen
#: windows are demonstrably the same statement.
PANCHAK_SIGNS = ("Aquarius", "Pisces")


# ------------------------------------------------------------- conditions

def _join(spans: list[Span]) -> list[Span]:
    """Join spans that touch, collecting their values.

    `sky._merge_adjacent` joins only spans of EQUAL value, which is not what a
    two-sign window needs: Aquarius and Pisces are different values and one
    Panchak.
    """
    out: list[Span] = []
    for s in sorted(spans, key=lambda x: x.start):
        if out and out[-1].end == s.start:
            prev = out.pop()
            vals = prev.value if isinstance(prev.value, tuple) else (prev.value,)
            out.append(Span(prev.start, s.end, vals + (s.value,),
                            prev.open_start, s.open_end))
        else:
            out.append(s)
    return out


def _moon_in(*stars: str):
    """Spans where the Moon occupies one of `stars`, off the ingress series."""
    wanted = set(stars)

    def fn(sky):
        return _join(where(sky.spans("Moon", "nakshatra"),
                           lambda v: v in wanted))
    return fn


def _moon_in_sign(*signs: str):
    """Spans where the Moon occupies one of `signs`, adjacent ones joined."""
    wanted = set(signs)

    def fn(sky):
        return _join(where(sky.spans("Moon", "sign"), lambda v: v in wanted))
    return fn


def _instants(event_class: str, family: str | None = None):
    """One zero-length span at each matching record's instant.

    The shape batch 2's `_aspect` uses: `civil_days` resolves an instant to the
    one civil day that contains it, per location.
    """
    def fn(sky):
        return [Span(parse(r["time"]["t_start_utc"]),
                     parse(r["time"]["t_start_utc"]),
                     {"id": r["id"], "flags": r["qa"]["flags"]})
                for r in sky.class_records(event_class, family=family)]
    return fn


def _tithi_named(*names: str, paksha: str | None = None):
    """Spans of the named tithis, off the boundary series.

    Nothing is joined: two consecutive tithi spans cannot carry the same name,
    so an adjacency here would be a duplicate record rather than one tithi.
    """
    wanted = set(names)

    def fn(sky):
        return [s for s in sky.tithi_spans()
                if s.value["tithi_name"] in wanted
                and (paksha is None or s.value["paksha"] == paksha)]
    return fn


def _yoga_named(*names: str):
    """Spans of the named yogas, off the boundary series."""
    wanted = set(names)

    def fn(sky):
        return [s for s in sky.yoga_spans() if s.value["yoga_name"] in wanted]
    return fn


def _tithi_with_yoga(tithis: tuple[str, ...], yogas: tuple[str, ...],
                     paksha: str | None = None):
    """Where a named tithi and a named yoga are in force at the same instant.

    Batch 2's `intersect`, unchanged. The two halves are separate series and
    are intersected as spans, which is what "Shukla Ekadashi Vyatipath Yog"
    says -- one instant carrying both -- rather than the weaker claim that the
    two merely share a civil day.
    """
    def fn(sky):
        return intersect(_tithi_named(*tithis, paksha=paksha)(sky),
                         _yoga_named(*yogas)(sky),
                         lambda t, y: {**t, **y})
    return fn


def _yoga_in_panchak(*yogas: str):
    """Where a named yoga is in force while the Moon is in Panchak.

    The Panchak half is `b055`'s own condition and inherits its status: the
    definition is supplied, not printed, so this rule is a resolved ambiguity
    and not an executable one.
    """
    def fn(sky):
        return intersect(_yoga_named(*yogas)(sky),
                         _moon_in_sign(*PANCHAK_SIGNS)(sky),
                         lambda y, sign: {**y, "moon_sign": sign})
    return fn


#: One ghadi is 24 minutes -- a sixtieth of the day. Definitional, no ephemeris.
GHADI_MINUTES = 24.0


def _amavasya_shorter_than_the_chaturdashi_before_it():
    """B106's condition, in the two tithis' own lengths.

    A length is the difference of two consecutive boundaries, so this needs the
    series and nothing else; the ghadi is a unit, not a measurement. A span the
    generated period cut is skipped rather than measured -- an open end is not
    a short tithi, and treating it as one is the year-boundary truncation the
    carry-in exists to avoid.
    """
    def fn(sky):
        spans = list(sky.tithi_spans())
        out = []
        for i, s in enumerate(spans):
            if i == 0 or s.value["tithi_name"] != "Amavasya":
                continue
            prev = spans[i - 1]
            if prev.value["tithi_name"] != "Chaturdashi":
                continue
            if s.open_start or s.open_end or prev.open_start or prev.open_end:
                continue
            amavasya = (s.end - s.start).total_seconds() / 60.0
            chaturdashi = (prev.end - prev.start).total_seconds() / 60.0
            if amavasya < chaturdashi:
                out.append(Span(s.start, s.end, {
                    **s.value,
                    "amavasya_ghadi": round(amavasya / GHADI_MINUTES, 2),
                    "chaturdashi_ghadi": round(chaturdashi / GHADI_MINUTES, 2),
                }))
        return out
    return fn


def _new_moon_with_moon_in(*signs: str):
    """New moons at which the Moon occupies one of `signs`.

    The sign comes from the Moon's own ingress series rather than from the
    lunation record's `sign` field. At a new moon the two agree by definition,
    and asking the series is what the remark actually says -- "if Moon in
    Sagittarius or Pisces" -- rather than what the conjunction record happens
    to carry.
    """
    wanted = set(signs)

    def fn(sky):
        out = []
        for r in sky.class_records("lunation", family="lunation/new_moon"):
            t = parse(r["time"]["t_start_utc"])
            sign = sky.value_at("Moon", "sign", t)
            if sign in wanted:
                out.append(Span(t, t, {"sign": sign, "id": r["id"]}))
        return out
    return fn



# ----------------------------------------------- conditions that need a venue
# Everything above returns spans from a location-blind `Sky`. The three below
# take a venue as well and are registered `per_location=True`, so `fire` calls
# them once per location and never once for both.
#
# The difference is not a refinement of the weekday handling; it is a second
# kind of thing. A weekday rule asks the sky ONE question and two calendars
# answer "which day was that": "Anuradha on Sunday" has the same sky-side span
# at both venues. These ask the sky a DIFFERENT question at each venue. Whether
# a tithi is Kshay -- whether any sunrise falls inside it -- can be yes in
# Mumbai and no in New York with no calendar involved at all, because the two
# horizons are met at different instants. `Rule.weekdays` cannot express that:
# by the time `fire` applies a weekday, the span has already been chosen.


def _tithi_by_sunrise_count(want: int, paksha: str):
    """Kshay (`want=0`) or Vriddhi (`want=2`) tithis of one fortnight, at a venue.

    A tithi is Kshay when no sunrise falls inside it and Vriddhi when two do.
    Both are statements about the tithi's boundaries AND the day's, which is
    exactly why the boundary series alone left B66-B69 blocked: the first half
    was in the layer and the second was not.

    A span the generated period cut is skipped rather than counted. An open end
    under-counts sunrises by construction, and here that would not merely
    shorten a window -- it would INVENT a Kshay tithi, one that looks empty of
    sunrises only because its far end was truncated.
    """
    def fn(sky, loc: str):
        out = []
        for s in sky.tithi_spans():
            if s.value["paksha"] != paksha or s.open_start or s.open_end:
                continue
            rises = sky.horizon_crossings_within("sunrise", loc, s)
            if (want == 0 and not rises) or (want == 2 and len(rises) >= 2):
                out.append(Span(s.start, s.end,
                                {**s.value, "sunrises_inside": len(rises)}))
        return out
    return fn


def _pradosh():
    """B64's condition: the Trayodashi that holds the twilight, at a venue.

    One instant per Trayodashi and never a window, because that is the shape
    the section's own table has -- a date and a fortnight, with no From/Till.
    The instant is the sunset the tithi holds, so `civil_days` resolves it to
    the single civil day that sunset falls in, exactly as it does for a
    lunation. The three clauses are `PRADOSH_RESOLUTION` written as code, and
    each is decided by a different row of the section's own 2026 table.
    """
    def fn(sky, loc: str):
        out = []
        for s in sky.tithi_spans():
            if s.value["tithi_name"] != "Trayodashi"                     or s.open_start or s.open_end:
                continue
            sets = sky.horizon_crossings_within("sunset", loc, s)
            if len(sets) == 1:
                instant, clause = sets[0], "sunset_inside_trayodashi"
            elif sets:
                # Two sunsets inside one Trayodashi -- the 28-Apr-2026 case.
                # The source prints the first of them and not both.
                instant, clause = sets[0], "first_of_two_sunsets"
            else:
                # No sunset inside it at all -- the 13-Jun-2026 case. The
                # source dates that Pradosh to the day the tithi ENDS.
                instant, clause = s.end, "no_sunset_inside_dated_to_tithi_end"
            out.append(Span(instant, instant,
                            {**s.value, "pradosh_clause": clause,
                             "sunsets_inside": len(sets)}))
        return out
    return fn


def _shukla_fortnights(sky):
    """Whole bright fortnights, off the tithi boundary series and nothing else.

    A bright fortnight is the run of tithi spans carrying `paksha == "Shukla"`:
    it opens where Pratipada opens and closes where Purnima closes, which is
    two `tithi_ingress` records exactly as a sign span is two `sign_ingress`
    records. A run the generated period cut at either end is dropped -- a
    fortnight missing some of its days cannot be asked how many Saturdays it
    holds, and answering anyway is how a count silently becomes an undercount.
    """
    out, run = [], []
    for s in list(sky.tithi_spans()) + [None]:
        if s is not None and s.value["paksha"] == "Shukla":
            run.append(s)
            continue
        if run:
            first, last = run[0], run[-1]
            if (not first.open_start and not last.open_end
                    and first.value["tithi_name"] == "Pratipada"
                    and last.value["tithi_name"] == "Purnima"):
                out.append(Span(first.start, last.end,
                                {"paksha": "Shukla", "tithis": len(run)}))
            run = []
    return out


def _n_weekdays_in_shukla_paksha(weekday: int, n: int):
    """B101's condition: bright fortnights holding at least `n` of one weekday.

    The span emitted runs from the FIRST such weekday to the LAST rather than
    across the whole fortnight, and the section's own single printed row is
    what decides that. Its fortnight opens 11-Sep-2026 08:57 and closes 26-Sep
    22:19; the row prints 12-Sep-26 to 26-Sep-26. The Till cannot tell the two
    readings apart -- the last Saturday and the fortnight's close are the same
    date -- but the From can, and it is the Saturday and not the Pratipada.

    The count is calendar arithmetic at a venue, done by `sky.weekdays_in_span`,
    which reads no record and asks no ephemeris. That is the whole of what B101
    was missing. It was never a third absent event class, and the fortnight
    bounds it needs have been in the layer since the tithi series arrived.
    """
    day_name = next(w for w, i in names.WEEKDAYS.items() if i == weekday)

    def fn(sky, loc: str):
        out = []
        for fortnight in _shukla_fortnights(sky):
            days = weekdays_in_span(fortnight, weekday, loc)
            if len(days) < n:
                continue
            window = civil_day_span(days[0], days[-1], loc)
            out.append(Span(window.start, window.end, {
                "paksha": "Shukla",
                "counted_weekday": day_name,
                "count": len(days),
                "dates": [x.strftime("%d-%b-%Y") for x in days],
                "fortnight_start_utc":
                    fortnight.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fortnight_end_utc":
                    fortnight.end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }))
        return out
    return fn


# =============================================================== B055 Panchak
# RESOLVED. The document names Panchak thirteen times -- this section's title
# and table, three rows of B56, and the monthly calendars -- and defines it in
# none of them. A rule cannot be written without supplying the definition, and
# supplying one silently is what `resolved_ambiguity` exists to prevent.
PANCHAK_AMBIGUITY = (
    "The source never defines Panchak. Two definitions are in ordinary "
    "currency and they are not the same statement: the FIVE-NAKSHATRA "
    "reading, the Moon from the third pada of Dhanishta through the end "
    "of Revati; and the TWO-SIGN reading, the Moon in Aquarius or Pisces. "
    "They denote the same arc -- Dhanishta's third pada begins at 300 "
    "degrees, which is the start of Aquarius -- but only under the same "
    "ayanamsha and the same 27-division, so they are two claims and not "
    "one. A third sense of the word, the five inauspicious acts, is not a "
    "market condition at all and no dated table could be built from it."
)

PANCHAK_RESOLUTION = (
    "The section's own thirteen windows decide it. Computed as the Moon in "
    "Aquarius or Pisces, all thirteen 2026 windows come back with the "
    "printed start date, the printed end date, and both printed times to "
    "within two minutes -- 21-Jan-26 01:37 against 01:35, 25-Jan-26 13:36 "
    "against 13:35, and so on down the table. Thirteen two-ended windows "
    "agreeing at both ends is not an agreement a wrong definition reaches.",

    "The arc is 60 degrees and the printed windows run four and a half to "
    "five days, which is the word itself: panchaka, five. A definition "
    "giving any other span length would print a different table.",

    "The count settles it independently of the times. Panchak recurs once "
    "per lunar month, so a calendar year holds thirteen; the section "
    "prints thirteen, and the two-sign reading produces thirteen in 2026 "
    "with none left over and none missing.",
)

PANCHAK_REJECTED = (
    "Panchak as the five inauspicious acts -- no dated window follows from "
    "it, and the section prints dated windows.",
    "The five-nakshatra reading stated in nakshatra terms -- not rejected "
    "as wrong, since it denotes the same arc, but not used: it needs "
    "Dhanishta's third pada, which is a navamsa boundary, and the Moon has "
    "no navamsa series in the layer. The sign series gives the identical "
    "arc from a series that is emitted.",
    "Any reading beginning at Dhanishta's start rather than its third pada "
    "-- it would run about 6.7 days and miss every printed end time.",
)

PANCHAK_FLAG = "panchak_definition_supplied_not_printed"

resolved(
    id="b055_panchak",
    section=B(55),
    rule_family="calendar/panchak",
    condition_text=B(55).title,
    condition_from="title",
    inputs=("ingress/sign",),
    flags=(PANCHAK_FLAG,),
    ambiguity=PANCHAK_AMBIGUITY,
    resolution=PANCHAK_RESOLUTION,
    rejected_readings=PANCHAK_REJECTED,
    notes="The two-sign reading is used because it is computable from an "
          "emitted series; the five-nakshatra reading names the same arc and "
          "is the same rule. The flag travels on every row: the dates are the "
          "layer's, the definition they rest on is not on the page.",
)(_moon_in_sign(*PANCHAK_SIGNS))

# The remark is a second rule and a different quantity: it turns on where in
# the day the window opens or closes, measured in ghatis from sunrise. No
# sunrise is emitted, so the ghati of an instant is not derivable -- and unlike
# the definition above, no printed table pins it: the Ghati column is filled on
# three rows of thirteen.
ambiguous(
    id="b055g_panchak_after_forty_ghati",
    section=B(55),
    rule_family="calendar/panchak",
    condition_text=B(55).remarks[0],
    condition_from="remark[0]",
    inputs=("ingress/sign",),
    ambiguity=(
        "'40 Ghati' is a time of day, and the sunrise series now fixes the "
        "instant it is counted from. What it does not fix is the length of "
        "the ghati, and the two readings in currency are not the same "
        "statement. Under the FIXED reading a ghati is 24 minutes -- a "
        "sixtieth of 24 hours, which is the sense B106 uses, correctly, "
        "because there it measures a DURATION and 24 minutes is a sixtieth "
        "of a day however the day is bounded. Under the VARIABLE reading a "
        "ghati is a sixtieth of the actual sunrise-to-sunrise day, which in "
        "Mumbai runs 23h58m to 24h02m across the year and in New York 23h46m "
        "to 24h14m. Forty ghati in is 16h00m under the first and up to nine "
        "minutes away from it under the second. The section prints no table "
        "of 40-ghati Panchaks -- its thirteen rows are the Panchak windows "
        "themselves, which both readings date identically -- so the document "
        "offers no row that could choose between them, and picking one would "
        "be this layer's decision rather than a reading of the page."
    ),
    flags=("outcome_stated_but_not_separable_no_dash",),
    notes="Reclassified from `blocked` to `ambiguous` by the sunrise series, "
          "and the change of status is the finding rather than an "
          "administrative tidy-up. It was blocked because the layer emitted no "
          "sunrise; the layer now emits one at both venues, so the missing "
          "input is gone and what is left is a choice between two readings of "
          "the source's own word. Filing that as `blocked` would have gone on "
          "reporting an absence this batch removed. The remark states its "
          "outcome in one comma-joined sentence with no dash, so it stays "
          "inside condition_text under the project's own separator rule and "
          "this rule reports no verdict either way.",
)


# ============================================================ B060 Amavasya
# Three rules. The title is the bare event; the remark packs two conditioned
# verdicts into one paragraph and is split at the full stop, which is accepted
# here because both halves come back as the document's own dash statements.
_B60_T, _B60_S = split_sentences(B(60).remarks[0])
_B60T_COND, _B60T_VERDICT = split_statement(_B60_T)
_B60S_COND, _B60S_VERDICT = split_statement(_B60_S)

rule(
    id="b060_amavasya",
    section=B(60),
    rule_family="lunation/new_moon",
    condition_text=B(60).title,
    condition_from="title",
    inputs=("lunation",),
    flags=("section_states_no_verdict",),
    notes="The bare no-moon day. Its two verdicts are conditioned -- on the "
          "weekday and on the Moon's sign -- and are the two rules below. The "
          "table's own Day and Sign columns are those two conditions printed, "
          "which is what makes the split a reading of the section rather than "
          "of one sentence.",
)(_instants("lunation", family="lunation/new_moon"))

rule(
    id="b060t_amavasya_on_tuesday",
    section=B(60),
    rule_family="lunation/new_moon",
    condition_text=_B60T_COND,
    condition_from="remark[0], first statement",
    verdict_text=_B60T_VERDICT,
    verdict_from="remark[0], first statement",
    inputs=("lunation", "weekday"),
    weekdays=(names.WEEKDAYS["Tuesday"],),
    notes="Tuesday is the venue's. A lunation falling near a date boundary is "
          "Tuesday at one venue and not the other, and both rows are emitted "
          "rather than one being chosen.",
)(_instants("lunation", family="lunation/new_moon"))

rule(
    id="b060s_amavasya_moon_in_sagittarius_or_pisces",
    section=B(60),
    rule_family="lunation/new_moon",
    condition_text=_B60S_COND,
    condition_from="remark[0], second statement",
    verdict_text=_B60S_VERDICT,
    verdict_from="remark[0], second statement",
    inputs=("lunation", "ingress/sign"),
    notes="The section's own Sign column prints this quantity for every "
          "amavasya it lists, which is the check on the reading: the remark "
          "names two of the twelve values that column takes.",
)(_new_moon_with_moon_in("Sagittarius", "Pisces"))


# ============================================================= B061 Purnima
# The remark IS the verdict and the title is the whole condition, which is
# B17's shape, so the remark is carried whole rather than split. Its "Usually"
# makes the claim Observed by the mechanical test, which is right: the source
# is hedging its own observation.
rule(
    id="b061_purnima",
    section=B(61),
    rule_family="lunation/full_moon",
    condition_text=B(61).title,
    condition_from="title",
    verdict_text=B(61).remarks[0],
    verdict_from="remark[0]",
    inputs=("lunation",),
    flags=("verdict_states_a_turn_not_a_direction",),
    notes="'top or bottom' names a turning point without naming a side. That "
          "is a verdict the source states and not one this layer may resolve "
          "into Bullish or Bearish; carried as printed.",
)(_instants("lunation", family="lunation/full_moon"))


# ====================================================== B062 Chandra Darshan
# BLOCKED. Not the new moon -- that is B60 -- but the first sighting of the
# crescent one or two days later, which the section's own Tithi column shows:
# Pratipada and Dwitiya, never Amavasya.
blocked(
    id="b062_chandra_darshan",
    section=B(62),
    rule_family="visibility/crescent",
    condition_text=B(62).title,
    condition_from="title",
    verdict_text=B(62).notes[0],
    verdict_from="note[0]",
    inputs=("lunation",),
    missing_inputs=(
        "a first-crescent visibility computation. The section's Tithi column "
        "reads Pratipada or Dwitiya, so the event is the sighting and not the "
        "conjunction; Step 3 measured swe.heliacal_ut against the source's own "
        "Venus rise dates and found it 9-10 days out, so the one routine "
        "available was rejected on evidence rather than on principle",
    ),
    notes="The note carries four separate rules, one of which -- 'Moon rise in "
          "Ardra, Purva Falguni, Uttra Falguni - Bullish and 2.5 days Bullish "
          "in Chitra' -- is the parallel that resolved B15 item c) in batch 1. "
          "All four wait on the same missing event.",
)


# ============================================================== B064 Pradosh
# RESOLVED, not executable. The sunset series clears the ASTRONOMY half of this
# section and does not clear the section, and the difference is the whole of
# what B64 turned out to be.
#
# The document names Pradosh twenty-two times and defines it nowhere -- the
# Panchak situation exactly, one section later in the same chapter. Supplying a
# definition silently is what `resolved_ambiguity` exists to prevent, and here
# the definition is not even the obvious one: the plain reading reproduces 22 of
# the section's 24 printed rows and the ruled reading reproduces 23, with the
# twenty-fourth a source defect the document contradicts on its own page.
PRADOSH_AMBIGUITY = (
    "The source never defines Pradosh. Every reading agrees it is about "
    "Trayodashi and the fall of night, and they disagree on three points "
    "that the section's own table can be put to. Which instant decides: "
    "sunset itself, or the pradosh kala -- the twilight muhurtas after it? "
    "Which day, when one Trayodashi holds TWO sunsets, as 28-Apr-2026 "
    "does? And which day when it holds NONE, as the Trayodashi of 12-Jun "
    "to 13-Jun-2026 does, opening after that evening's sunset and closing "
    "before the next? A table of 24 dated rows is not produced by 'the "
    "Trayodashi at sunset' alone: that reading emits 25 rows and misses two "
    "the source prints."
)

PRADOSH_RESOLUTION = (
    "The primary clause is sunset and not the pradosh kala, and one row "
    "separates them. Krishna Trayodashi runs 12-Jun-2026 19:37:09 to "
    "13-Jun 16:08:14 and Mumbai sunset on 12-Jun is 19:12:22, so the tithi "
    "opens 25 minutes AFTER that sunset -- inside the pradosh kala on any "
    "reading of its length. A kala reading therefore dates the row 12-Jun. "
    "The section prints 13-Jun. Sunset-primary survives the row that "
    "refutes the kala, and across the year the kala reading reproduces 20 "
    "of 24 against sunset's 22.",

    "Where one Trayodashi holds two sunsets, the source takes the first. "
    "Shukla Trayodashi runs 28-Apr-2026 18:52:22 to 29-Apr 19:52:07 and "
    "Mumbai sunset falls inside it on both days, at 18:56:10 and 18:56:29. "
    "The section prints 28-Apr and not 29-Apr, and this is the only "
    "two-sunset Trayodashi in 2026, so the clause is decided by the one "
    "row that can decide it.",

    "Where it holds none, the source takes the day the tithi ENDS. That is "
    "the 12-Jun-to-13-Jun Trayodashi again, read the other way round: the "
    "section prints 13-Jun, the day it closes, and not 12-Jun, the day it "
    "opens. Adding this clause alone moves the reproduction from 22 of 24 "
    "to 23 of 24.",

    "Under all three clauses together the section reproduces 23 of its 24 "
    "printed rows against Mumbai, exactly and in the right fortnight, with "
    "25 Trayodashis in the year and 25 Pradosh dates emitted -- one per "
    "Trayodashi, which is what the word means.",
)

PRADOSH_REJECTED = (
    "Pradosh kala -- Trayodashi overlapping the muhurtas after sunset "
    "rather than sunset itself. Refuted by 12-Jun-2026 and by three more "
    "rows: it reproduces 20 of 24.",
    "Trayodashi prevailing at SUNRISE. Reproduces 10 of 24 and is not a "
    "near miss -- it dates fourteen rows to the following day.",
    "Trayodashi touching the civil day at all, with no horizon instant in "
    "it. It cannot separate 28-Apr from 29-Apr, and it would emit both "
    "days of every Trayodashi, 44 rows against 24 printed.",
    "The last of two sunsets rather than the first -- 29-Apr-2026, which "
    "the section does not print.",
)

PRADOSH_FLAG = "pradosh_definition_supplied_not_printed"

resolved(
    id="b064_pradosh",
    section=B(64),
    rule_family="panchang/tithi",
    condition_text=B(64).title,
    condition_from="title",
    verdict_text=B(64).notes[0],
    verdict_from="note[0]",
    inputs=("panchang/tithi", "horizon/sunset"),
    per_location=True,
    flags=(PRADOSH_FLAG, "source_table_omits_2026_occurrences"),
    ambiguity=PRADOSH_AMBIGUITY,
    resolution=PRADOSH_RESOLUTION,
    rejected_readings=PRADOSH_REJECTED,
    notes="Two of the section's 25 Trayodashis diverge from the table and they "
          "are different findings, not one. 01-Jan-2026 Shukla is a Pradosh by "
          "every reading -- sunset 18:08:43 inside a Trayodashi running 01:48 "
          "to 22:22 -- and the section simply does not print it: an omitted "
          "occurrence, the B74 and B100 shape. 24-Aug-2026 Shukla is the "
          "opposite: the section prints a date its own condition cannot reach, "
          "because that Trayodashi does not open until 25-Aug 06:21:21 and "
          "24-Aug's sunset falls in Dwadashi. The document contradicts itself "
          "there rather than contradicting this engine -- B68's own Vriddhi "
          "table prints the same tithi as 25-Aug-26 Trayodashi, which is the "
          "day this rule fires. That is B56's shape, two of the document's "
          "pages disagreeing, and it is recorded in source_defects. The note "
          "carried as the verdict states three further conditions turning on "
          "Vriddhi and Kshay Pradosh days; B66-B69 now supply both, so those "
          "are portable sub-rules and are deliberately left to a later pass "
          "rather than split in the same change that unblocked them.",
)(_pradosh())


# ===================================================== B065 Ekadashi on Friday
rule(
    id="b065_ekadashi_on_friday",
    section=B(65),
    rule_family="panchang/tithi",
    condition_text=B(65).title,
    condition_from="title",
    verdict_text=B(65).remarks[0],
    verdict_from="remark[0]",
    inputs=("panchang/tithi", "weekday"),
    weekdays=(names.WEEKDAYS["Friday"],),
    notes="Reproduces its 2026 table exactly: all six dates, no extras, and "
          "every printed From/Till within 44 seconds of the computed boundary. "
          "The title says Ekadashi without a fortnight and the table carries "
          "both -- 24-Jul-26 is annotated 'Asadh Shukla Ekadashi' and "
          "10-Jul-26 'Kshay Tithi in Dark Fortnight' -- so the condition is "
          "the tithi name in either paksha, which is what the section's own "
          "rows show. The remark carries the source's reliability figure "
          "('90%+'), which is label-layer material per STEP4_DECISIONS "
          "section 8 and is neither read nor raised here.",
)(_tithi_named(*names.tithis_in(B(65).title)))


# ======================================== B066-B069  Kshay and Vriddhi Tithi
# Four sections, one shape, and one punctuation trap. Each title joins the two
# halves of its condition with a dash and then adds the verdict with a second
# -- "Kshay Tithi - Shukla Paksh (Bright Fortnight) - Bearish" -- so a
# first-dash split returns "Shukla Paksh (Bright Fortnight) - Bearish" as the
# verdict and loses half the condition inside it. That is B87's failure in a
# different mark, found by re-scanning for it; `split_final` is used instead.
_TITHI_SECTIONS = ((66, "kshay", 0, "Shukla"), (67, "kshay", 0, "Krishna"),
                   (68, "vriddhi", 2, "Shukla"), (69, "vriddhi", 2, "Krishna"))

#: The count of sunrises that defines each kind, read as the words do: Kshay is
#: a tithi the sun never rises in, Vriddhi one it rises in twice. Written as a
#: number in the table above rather than as an `if` here, so the four rules are
#: four instances of one statement and not four near-copies of it.
KSHAY_VRIDDHI_FLAG = "dated_by_sunrise_at_the_evaluating_location"

#: A tithi runs about 23h40m and a Vriddhi tithi is longer than a day by
#: definition, so both kinds routinely touch two civil days while the source
#: prints one -- the day the tithi opens, which its 28 rows do without
#: exception. That is the B75 and B95 shape and NOT the B74 and B100 shape, and
#: the two look identical in a count of extras. Flagged so they cannot be read
#: as the same finding.
KSHAY_VRIDDHI_SPAN_FLAG = "source_prints_the_opening_day_of_a_multi_day_tithi"

for _b, _kind, _rises, _paksha in _TITHI_SECTIONS:
    _cond, _verdict = split_final(B(_b).title)
    rule(
        id=f"b{_b:03d}_{_kind}_tithi_{_paksha.lower()}_paksha",
        section=B(_b),
        rule_family="panchang/tithi",
        condition_text=_cond,
        condition_from="title, split at the final dash",
        verdict_text=_verdict,
        verdict_from="title",
        inputs=("panchang/tithi", "horizon/sunrise"),
        per_location=True,
        flags=("condition_split_at_final_dash", KSHAY_VRIDDHI_FLAG,
               KSHAY_VRIDDHI_SPAN_FLAG),
        notes=f"{_kind.capitalize()} tithi in the {_paksha} fortnight, dated "
              "against sunrise at the evaluating venue. Reproduces its 2026 "
              "table exactly against Mumbai -- B66 9/9, B67 8/8, B68 6/6, "
              "B69 5/5, 28 rows between them, every tithi named correctly, "
              "nothing omitted and nothing extra -- and that reproduction was "
              "written and passing before the sunrise series existed, which is "
              "why batch 3 could name sunrise as the whole of what was missing "
              "instead of guessing at it. The condition is genuinely different "
              "at the two venues and not merely differently dated: a tithi can "
              "hold a Mumbai sunrise and no New York one, so the rule is "
              "evaluated per location rather than filtered after the fact. "
              "The middle segment of the title is the fortnight and is part of "
              "the condition; a first-dash split would have filed it under the "
              "verdict.",
    )(_tithi_by_sunrise_count(_rises, _paksha))


# ======================================================= B071 Uttara Phalguni
rule(
    id="b071_moon_in_uttara_phalguni",
    section=B(71),
    rule_family="residency/moon_nakshatra",
    condition_text=B(71).title,
    condition_from="title",
    inputs=("ingress/nakshatra",),
    flags=("section_states_no_verdict",),
    notes="Reproduces the section's own 2026 table exactly: fourteen windows, "
          "every start and end date, both times to the minute. That agreement "
          "is the evidence that a bare nakshatra name in this document means "
          "the MOON's nakshatra, which the rest of this batch rests on.",
)(_moon_in(names.nakshatra("Uttra Falguni")))

_B71_COND, _B71_VERDICT = split_statement(B(71).notes[0])

blocked(
    id="b071d_uttara_phalguni_by_navamsa",
    section=B(71),
    rule_family="residency/moon_nakshatra",
    condition_text=_B71_COND,
    condition_from="note[0]",
    verdict_text=_B71_VERDICT,
    verdict_from="note[0]",
    inputs=("ingress/nakshatra", "ingress/navamsa"),
    missing_inputs=(MOON_NAVAMSA,),
    notes="The note gives four outcomes by which navamsa the Moon occupies "
          "inside the window -- Sagittarius and Capricorn bullish, Aquarius "
          "bearish, Pisces volatile -- and the section's Navmansh column dates "
          "the changeovers to the minute. Each window crosses three or four "
          "navamsas in a day, which is exactly the resolution the layer does "
          "not carry for the Moon. The condition reads 'Observation' because "
          "that is the word before the note's first dash; the substance is in "
          "the verdict.",
)


# ===================================================== B072 Mangal Ashwini Yog
# The title names a yoga, states the verdict, and then defines the yoga in a
# parenthetical AFTER the verdict. The condition is taken from that
# parenthetical -- the document's own definition of its own term -- rather than
# from the name, which nothing could compute.
_B72_NAME, _B72_REST = split_statement(B(72).title)
_B72_VERDICT = _B72_REST.split("(")[0].strip()
_B72_COND = _B72_REST[_B72_REST.index("(") + 1:].rstrip(")").strip()

rule(
    id="b072_ashwini_on_tuesday",
    section=B(72),
    rule_family="residency/moon_nakshatra",
    condition_text=_B72_COND,
    condition_from="title, parenthetical gloss",
    verdict_text=_B72_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra", "weekday"),
    weekdays=(names.WEEKDAYS["Tuesday"],),
    flags=("condition_read_from_the_titles_parenthetical_gloss",
           "source_table_omits_2026_occurrences"),
    notes="'Mangal Ashwini Yog' is the name and 'Ashwini Nakshtra on Tuesday' "
          "is the definition, printed in the same title. Mangal is Tuesday's "
          "own lord, so name and gloss say the same thing twice. The 2026 "
          "table prints one of the three occurrences.",
)(_moon_in(names.nakshatra("Ashwini")))


# ================================== B073/B074  Ashtami on named weekdays
#: What each section's 2026 table does against its own title, recomputed and
#: stated as dates rather than as impressions -- the standard section 12.4 set
#: for the six Moon-nakshatra tables, applied to the two Ashtami tables.
_ASHTAMI_NOTES = {
    73: "Ashtami in either fortnight on the weekdays the title names. Seven of "
        "the nine printed rows come back exactly, with all four printed From "
        "times within 39 seconds. The other two -- 11-Jan-26 and 10-May-26 -- "
        "are printed against 'Sunday', which is not one of the two weekdays "
        "this section's own title names, and each is the day AFTER a Saturday "
        "Ashtami this rule does fire on: 10-Jan from 08:24 and 09-May from "
        "14:03, both running past midnight into that Sunday. The section's "
        "Monday column does not settle which day was meant, because the Monday "
        "after a Saturday and the Monday after the Sunday following it are the "
        "same Monday. Recorded as the title being the rule, which is section "
        "12.4's standing treatment of a printed date its own title cannot "
        "reach.",
    74: "Ashtami in either fortnight on Monday, Thursday or Friday. Reproduces "
        "all twelve printed dates, every printed From/Till within 45 seconds, "
        "and emits six the source does not print: 12-Mar, 09-Apr, 23-Apr, "
        "06-Aug, 18-Sep and 19-Oct-2026. The same finding as the six "
        "Moon-nakshatra sections -- the tables are incomplete and the titles "
        "are the rule.",
}
for _b in (73, 74):
    _cond, _verdict = split_statement(B(_b).title)
    _days = names.weekdays_in(B(_b).title)
    rule(
        id=f"b{_b:03d}_ashtami_on_"
           + "_".join(w.lower() for w, i in sorted(names.WEEKDAYS.items(),
                                                   key=lambda kv: kv[1])
                      if i in _days),
        section=B(_b),
        rule_family="panchang/tithi",
        condition_text=_cond,
        condition_from="title",
        verdict_text=_verdict,
        verdict_from="title",
        inputs=("panchang/tithi", "weekday"),
        weekdays=_days,
        flags=(("source_table_prints_days_outside_its_own_title",)
               if _b == 73 else ("source_table_omits_2026_occurrences",)),
        notes=_ASHTAMI_NOTES[_b],
    )(_tithi_named(*names.tithis_in(B(_b).title)))


# ================================== B075/B076  Chaturthi by fortnight
# The three-segment title shape of B66-B69, and `split_final` for that reason.
for _b in (75, 76):
    _cond, _verdict = split_final(B(_b).title)
    _paksha = "shukla" if "Shukla" in _cond else "krishna"
    rule(
        id=f"b{_b:03d}_chaturthi_{_paksha}_paksha",
        section=B(_b),
        rule_family="panchang/tithi",
        condition_text=_cond,
        condition_from="title, split at the final dash",
        verdict_text=_verdict,
        verdict_from="title",
        inputs=("panchang/tithi",),
        flags=("condition_split_at_final_dash",),
        notes="Reproduces every date the section prints -- B75 12/12, B76 "
              "13/13 -- with one cell disagreeing, which is recorded as a "
              "source defect rather than absorbed: B76's 03-Jun-2026 row is "
              "annotated 'Till 23:31', and Krishna Chaturthi that month runs "
              "03-Jun 21:21:45 to 04-Jun 23:30:59, so the printed time is the "
              "correct END of the tithi to one second, against the wrong date. "
              "The extra days this rule emits are not extra occurrences: a "
              "Chaturthi lasts about a day and touches two civil days, and the "
              "section prints one of them. The note conditions the result "
              "further on Vriddhi and Kshay tithis and on Tuesday; that half "
              "stays unported, because Vriddhi and Kshay need sunrise "
              "(B66-B69).",
    )(_tithi_named(*names.tithis_in(_cond),
                   paksha=names.paksha_in(_cond)))


# ============================================ B095 Shukla Pratipada on weekend
_B95_COND, _B95_VERDICT = split_statement(B(95).title)
rule(
    id="b095_shukla_pratipada_on_saturday_or_sunday",
    section=B(95),
    rule_family="panchang/tithi",
    condition_text=_B95_COND,
    condition_from="title",
    verdict_text=_B95_VERDICT,
    verdict_from="title",
    inputs=("panchang/tithi", "weekday"),
    weekdays=names.weekdays_in(B(95).title),
    notes="All four printed dates come back. The fifth day this rule emits, "
          "10-Oct-2026, is not a fifth occurrence: it is the Saturday half of "
          "the same Pratipada the source prints against Sunday 11-Oct, running "
          "10-Oct 21:20 to 11-Oct 21:31 and touching both named days. Both are "
          "non-trading days at both venues, and the section's remark says the "
          "impact lands on the following market day; that displacement is a "
          "second rule the source states in prose and never dates, and it is "
          "not ported.",
)(_tithi_named(*names.tithis_in(_B95_COND), paksha=names.paksha_in(_B95_COND)))


# ================================================ B096 Vyatipata on weekdays
_B96_COND, _B96_VERDICT = split_statement(B(96).title)
rule(
    id="b096_vyatipata_yoga_on_tuesday_saturday_or_sunday",
    section=B(96),
    rule_family="panchang/yoga",
    condition_text=_B96_COND,
    condition_from="title",
    verdict_text=_B96_VERDICT,
    verdict_from="title",
    inputs=("panchang/yoga", "weekday"),
    weekdays=names.weekdays_in(B(96).title),
    notes="The section's Remarks column prints the yoga's own start and end "
          "times -- 'From 20:01 onwards', 'Till 16:17' -- which is exactly the "
          "boundary series the layer now emits, and all nine come back within "
          "64 seconds. Those nine times are also what fixes the FRAME. A yoga "
          "is the SUM of the two longitudes, so the ayanamsha enters twice "
          "instead of cancelling: read under Krishnamurti these rows are 22 "
          "minutes out, under Fagan-Bradley 3h17m, under Raman 5h24m, and read "
          "tropically they do not shift but name different yogas altogether.",
)(_yoga_named(*names.yogas_in(_B96_COND)))


# ============================================= B097 Moon in Mrigashira, Monday
_B97_COND, _B97_VERDICT = split_statement(B(97).title)
rule(
    id="b097_moon_in_mrigashira_on_monday",
    section=B(97),
    rule_family="residency/moon_nakshatra",
    condition_text=_B97_COND,
    condition_from="title",
    verdict_text=_B97_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra", "weekday"),
    weekdays=(names.WEEKDAYS["Monday"],),
    flags=("source_table_omits_2026_occurrences",),
    notes="The one section of the six that names the Moon explicitly, which "
          "is why the other five are read the same way. Its 2026 table prints "
          "two of the three occurrences: 13-Jul-2026 holds Mrigashira until "
          "05:41 and is not listed.",
)(_moon_in(names.nakshatra("Mrigsira")))


# ================================================ B100 Shukla Shasthi on Friday
_B100_COND, _B100_VERDICT = split_statement(B(100).title)
rule(
    id="b100_shukla_shasthi_on_friday",
    section=B(100),
    rule_family="panchang/tithi",
    condition_text=_B100_COND,
    condition_from="title",
    verdict_text=_B100_VERDICT,
    verdict_from="title",
    inputs=("panchang/tithi", "weekday"),
    weekdays=names.weekdays_in(B(100).title),
    flags=("source_table_omits_2026_occurrences",),
    notes="The section prints one date, 19-Jun-2026, and the condition holds "
          "on three: 22-May-26 till 06:25 and 16-Oct-26 from 03:25 are not "
          "printed. Two separate occurrences, not two halves of one window, so "
          "these are omissions of the kind section 12.4 pins by name.",
)(_tithi_named(*names.tithis_in(_B100_COND),
               paksha=names.paksha_in(_B100_COND)))


# ======================================= B101 Three Saturdays in Shukla Paksh
_B101_COND, _B101_VERDICT = split_statement(B(101).title)

#: The number the title states, read from the title rather than typed: "Three
#: Saturday in Shukla Paksh". A bright fortnight spans about 14.8 days and so
#: touches at most three of any weekday, which the harness asserts -- so "at
#: least three" and "exactly three" cannot come apart, and the threshold
#: reading is used because that is what a count in a title is.
_B101_N = 3
_B101_WEEKDAY = names.weekdays_in(_B101_COND)[0]

rule(
    id="b101_three_saturdays_in_shukla_paksha",
    section=B(101),
    rule_family="panchang/tithi",
    condition_text=_B101_COND,
    condition_from="title",
    verdict_text=_B101_VERDICT,
    verdict_from="title",
    inputs=("panchang/tithi", "weekday"),
    per_location=True,
    flags=("weekday_is_counted_not_filtered",
           "span_runs_first_counted_weekday_to_last"),
    notes="Cleared by a rule-layer helper and not by a new event class, which "
          "is what batch 3 said it needed. Its fortnight bounds were already "
          "exact -- a bright fortnight is the opening of Pratipada to the "
          "close of Purnima, two tithi_ingress records -- and what was missing "
          "was the ability to COUNT a weekday inside one at a named venue. "
          "`sky.weekdays_in_span` does that: calendar arithmetic beside "
          "`civil_days`, reading no record and asking no ephemeris, so `Sky` "
          "is not widened and the no-ephemeris check is untouched. `weekdays` "
          "stays unset because Saturday here is counted inside a window, not "
          "required of the firing day; the rule is per_location because the "
          "count itself differs by venue, which is the same reason the "
          "weekday handling exists at all. The section prints one row, "
          "12-Sep-26 to 26-Sep-26, and a second qualifying fortnight in 2026 "
          "-- 10-Oct to 24-Oct -- is omitted by the source: an omitted "
          "occurrence of the B74 and B100 kind, not a two-day artefact.",
)(_n_weekdays_in_shukla_paksha(_B101_WEEKDAY, _B101_N))


# ============================ B102-B105  the Moon's nakshatra on a weekday
# Four sections of one shape, generated from their own titles: the nakshatra
# and the weekday are both read out of the heading, so neither is typed here
# and no rule can drift from the section it cites.
#
# The reading -- a bare nakshatra name is the MOON's nakshatra -- is not
# assumed. B104's six 2026 dates and B105's four come back exactly under
# `civil_day_overlap`, and B71's fourteen windows reproduce to the minute.
_MOON_WEEKDAY_NOTES = {
    102: "The 2026 table prints 28-Jun-2026, on which Anuradha ended at 22:11 "
         "the previous evening and the condition does not hold at all, and "
         "omits 03-May-2026, on which it holds for 16.8 hours. Recorded, not "
         "reconciled: the title is the rule.",
    103: "The 2026 table prints three of the five occurrences. The two omitted "
         "hold for 2.7 and 1.5 hours -- but B104 prints a 1.2-hour window, so "
         "brevity is not the source's criterion either.",
    104: "Reproduces its 2026 table exactly: all six dates, no extras.",
    105: "Reproduces its 2026 table exactly: all four dates. The remark adds "
         "that a vargottama Moon neutralises the result; vargottama needs the "
         "Moon's navamsa, which the layer does not carry, so the modifier is "
         "not ported and the rule fires unmodified.",
}
MOON_WEEKDAY_RULES: list[str] = []

for _b in (102, 103, 104, 105):
    _sec = B(_b)
    _cond, _verdict = split_statement(_sec.title)
    _stars = names.nakshatras_in(_cond)
    _days = names.weekdays_in(_cond)
    if len(_stars) != 1 or len(_days) != 1:
        raise SystemExit(f"B{_b}: expected one nakshatra and one weekday in "
                         f"{_cond!r}, read {_stars} and {_days}")
    _day = next(w for w, i in names.WEEKDAYS.items() if i == _days[0])
    _rid = f"b{_b:03d}_{_stars[0].lower().replace(' ', '_')}_on_{_day.lower()}"
    MOON_WEEKDAY_RULES.append(_rid)
    rule(
        id=_rid,
        section=_sec,
        rule_family="residency/moon_nakshatra",
        condition_text=_cond,
        condition_from="title",
        verdict_text=_verdict,
        verdict_from="title",
        inputs=("ingress/nakshatra", "weekday"),
        weekdays=_days,
        flags=(("source_table_omits_2026_occurrences",)
               if _b in (102, 103) else ()),
        notes=f"{_stars[0]} on {_day}, both read out of the title. "
              + _MOON_WEEKDAY_NOTES[_b],
    )(_moon_in(_stars[0]))


# =========================================== B106 Amavasya Ghadi vs Chaturdashi
_B106_COND, _B106_VERDICT = split_statement(B(106).title)
rule(
    id="b106_amavasya_ghadi_lesser_than_chaturdashi",
    section=B(106),
    rule_family="panchang/tithi",
    condition_text=_B106_COND,
    condition_from="title",
    verdict_text=_B106_VERDICT,
    verdict_from="title",
    inputs=("panchang/tithi",),
    flags=("source_table_omits_2026_occurrences",),
    notes="The second half of this section's old block dissolved with the "
          "first: a tithi's LENGTH is the difference of two consecutive "
          "boundaries, and the ghadi is a definitional unit of 24 minutes "
          "rather than a measurement. All four printed rows come back, each "
          "within two minutes of the printed start -- 18-Jan 00:04 against "
          "0:05, 16-Feb 17:34 against 17:35, 16-Apr 20:11 against 20:13 -- and "
          "the third row identifies itself the same way: its time 08:27 is the "
          "18-Mar-2026 Amavasya opening at 08:25, while its date cell reads "
          "'28-Mar-25 *', wrong in the day and in the year and asterisked by "
          "the document itself. Two further 2026 occurrences, 16-May and "
          "14-Jun, are not printed.",
)(_amavasya_shorter_than_the_chaturdashi_before_it())


# ==================================== B108 Shukla Ekadashi with Vyatipata etc.
_B108_COND, _B108_VERDICT = split_statement(B(108).title)
rule(
    id="b108_shukla_ekadashi_with_vyatipata_or_vaidhriti",
    section=B(108),
    rule_family="panchang/yoga",
    condition_text=_B108_COND,
    condition_from="title",
    verdict_text=_B108_VERDICT,
    verdict_from="title",
    inputs=("panchang/tithi", "panchang/yoga"),
    notes="Blocked twice over in batch 3, with both halves named rather than "
          "whichever was noticed first -- which is what makes this section the "
          "check on the pair: it clears only because both series arrived "
          "together. Its single printed row reproduces exactly. On 27-May-2026 "
          "Shukla Ekadashi and Vyatipata are in force together from 03:10 to "
          "06:22, and no other such coincidence occurs anywhere in 2026.",
)(_tithi_with_yoga(names.tithis_in(_B108_COND), names.yogas_in(_B108_COND),
                   paksha=names.paksha_in(_B108_COND)))


# ======================================= B109 Shukla Trayodashi on Tue or Sat
_B109_COND, _B109_VERDICT = split_statement(B(109).title)
rule(
    id="b109_shukla_trayodashi_on_tuesday_or_saturday",
    section=B(109),
    rule_family="panchang/tithi",
    condition_text=_B109_COND,
    condition_from="title",
    verdict_text=_B109_VERDICT,
    verdict_from="title",
    inputs=("panchang/tithi", "weekday"),
    weekdays=names.weekdays_in(B(109).title),
    flags=("source_table_omits_2026_occurrences",),
    notes="All seven printed rows come back, every Start and End within 56 "
          "seconds, including the one the section marks 'Whole day' -- "
          "27-Jun-2026, where Shukla Trayodashi covers that Saturday end to "
          "end. One occurrence is omitted: 28-Feb-2026, a Saturday, from "
          "20:43.",
)(_tithi_named(*names.tithis_in(_B109_COND),
               paksha=names.paksha_in(_B109_COND)))


# ============================================ B110 Moon eclipse on a Tuesday
_B110_COND, _B110_VERDICT = split_statement(B(110).title)
rule(
    id="b110_lunar_eclipse_on_tuesday",
    section=B(110),
    rule_family="eclipse/lunar",
    condition_text=_B110_COND,
    condition_from="title",
    verdict_text=_B110_VERDICT,
    verdict_from="title",
    inputs=("eclipse", "weekday"),
    weekdays=(names.WEEKDAYS["Tuesday"],),
    notes="The weekday is the venue's, and the difference is real in this "
          "family: the lunar eclipse of 21-Feb-2027 falls on Sunday in Mumbai "
          "and Saturday in New York. Neither is a Tuesday, so this rule is "
          "untouched by that one -- but the principle is why the weekday is "
          "declared on the rule and applied per location rather than folded "
          "into the condition.",
)(_instants("eclipse", family="eclipse/lunar"))


# ================================= B111 Moon eclipse in a named lunar month
_B111_COND, _B111_VERDICT = split_statement(B(111).title)
blocked(
    id="b111_lunar_eclipse_in_vaishakha_shravana_or_ashwin",
    section=B(111),
    rule_family="eclipse/lunar",
    condition_text=_B111_COND,
    condition_from="title",
    verdict_text=_B111_VERDICT,
    verdict_from="title",
    inputs=("eclipse", "source_selection_rule"),
    missing_inputs=(
        "the lunar month system. Naming a month Vaishakha, Shravana or Ashwin "
        "requires knowing whether the source counts months amanta or "
        "purnimanta -- the two disagree by a fortnight and therefore about "
        "which month an eclipse falls in. `month_system_confirmation` is open "
        "in config/conventions.yaml and this is a section it bounds",
    ),
    notes="The eclipse half is exact; the month half is a convention nobody "
          "has confirmed. Choosing amanta because it is commoner in western "
          "India would date this rule on a coin toss.",
)


# ============================== B056 Yoga in Panchak, last because it needs both
_B56_COND, _B56_VERDICT = split_statement(B(56).title)
resolved(
    id="b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak",
    section=B(56),
    rule_family="panchang/yoga",
    condition_text=_B56_COND,
    condition_from="title",
    verdict_text=_B56_VERDICT,
    verdict_from="title",
    inputs=("panchang/yoga", "ingress/sign"),
    flags=(PANCHAK_FLAG,),
    ambiguity=PANCHAK_AMBIGUITY,
    resolution=PANCHAK_RESOLUTION,
    rejected_readings=PANCHAK_REJECTED,
    notes="Batch 3 said the yoga series alone would unblock this section. That "
          "was right about the yoga and wrong about the status. The Panchak "
          "half is b055's condition and b055 is a resolved ambiguity -- part "
          "of the words it fires on are ours -- so this section inherits that "
          "status rather than arriving executable. It cites the same four "
          "strings b055 does, from the same constants, because a second "
          "paraphrase of one ruling is how two rules come to rest on two "
          "slightly different rulings. "
          "Five of the six printed rows reproduce within a minute, ends "
          "included: Vyatipata to 21-Jan-26 18:58 against 18:59; Indra to "
          "16-Apr 10:37 against 10:38; Vaidhriti 16-Apr 10:37 to 17-Apr 07:21 "
          "against 10:38 and 7:23, printed against '17-Apr-25', the document's "
          "recurring year typo; Vaidhriti to 07-Jun 10:01 against 10:02; and "
          "Vyatipata 17-Dec 13:21 to 18-Dec 12:19 against 13:22 and 12:19. "
          "The sixth is a source defect the document witnesses against itself. "
          "Its 'Endra 06-Jun-26, ending 10:05' row asks for Indra inside "
          "Panchak, and Indra ends that day at 10:04 while B55's own Panchak "
          "table opens the June window at 19:05 -- nine hours later, on the "
          "source's printed figures and not on ours. The two share a civil "
          "date and no instant. Reading 'in Panchak' as sharing a civil day "
          "instead would recover that row and cost an extra one, which is a "
          "single row of evidence either way; the instant reading is kept "
          "because every other conjunction of conditions in this package "
          "intersects spans, and because section 12.4 has already ruled on "
          "this exact shape once, when B102's 28-Jun-2026 row named a day its "
          "own title could not reach. The competing reading is recorded here "
          "rather than in `ambiguity`, which names the ruling this rule's rows "
          "actually rest on.",
)(_yoga_in_panchak(*names.yogas_in(_B56_COND)))
