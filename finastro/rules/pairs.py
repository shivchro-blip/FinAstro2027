"""The pairs batch -- the retrograde pairs and the nakshatra-residency singles.

Sixteen catalogue-B sections in two shapes.

**The retrograde pairs (B81, B82, B83).** "Saturn and Mercury Both Retrograde",
"Jupiter and Mercury Both Retrograde", "Mercury and Venus Both Retrograde" --
each a window in which two bodies are retrograde at the same instant. Nothing
new was needed for them: `Sky.motion_spans` already reconstructs retrograde
stretches from the station records, and "both retrograde" is the intersection
of two of those series, which `sky.intersect` expresses. The batch's work here
was **checking**, and the check found a defect in the source.

* B82 reproduces its printed row: 26-Feb-26 12:19 against a computed 12:17, and
  11-Mar-26 9:01 against a computed 09:23 -- a 24-minute start and a 22-minute
  end.
* B83 reproduces its printed row to within two minutes: 24-Oct-26 12:44 /
  13-Nov-26 21:25 against 12:42 / 21:24.
* **B81 does not, and the row it prints belongs to a different planet.**
  "Saturn and Mercury Both Retrograde" prints 03-Oct-26 12:47 to 14-Nov-26
  5:59. Saturn turns retrograde on 27-Jul-26 and direct on 11-Dec-26; Mercury
  turns retrograde on 24-Oct-26 at 12:42 and direct on 13-Nov-26 at 21:24. Their
  intersection is 24-Oct-26 12:42 to 13-Nov-26 21:24. The printed row is not
  that window and cannot be: **03-Oct-26 12:43 is VENUS's retrograde station and
  14-Nov-26 05:59 is Venus's direct station**, both within four minutes of the
  printed ends. The Saturn-Mercury
  row is Venus's retrograde window, so the section's own table is wrong on its
  face. Its condition is still exact and is ported; the row is recorded as the
  defect it is, and nothing was widened to meet it.

The 2026 coincidence that makes the defect easy to misread as a difference is
worth stating: Venus is retrograde from 03-Oct to 14-Nov and Saturn from
27-Jul to 11-Dec, so both fully contain Mercury's 24-Oct to 13-Nov retrograde.
Saturn-with-Mercury and Mercury-with-Venus are therefore the SAME 2026 window,
which is why B83's printed row is also B81's correct one.

**The nakshatra-residency singles (B88, B91, B92, B94, B98, B99, B107, B113,
B114, B115).** One body in one nakshatra, or -- B94 -- a named yoga between two
bodies. Every one was recomputed against the section's own 2026 table before it
was ported, and the reproductions are in each rule's notes. The reading that a
bare nakshatra name means the Moon is not used here and is not assumed: B71
already establishes it (its fourteen printed windows come back to the minute),
and every section in this batch names its body except B88, which is read from
the Moon-Rahu series it continues.

Three of these sections print a verdict that segments its own window -- B92
("1st 2 Days Bullish, Then Bearish"), B99 ("First 15 Days Bearish, Then
Bullish") and B114 ("First Bullish Then Bearish") -- and B91 prints the
segmentation one level down, in its table's Duration column. None is expressible
as two spans without authoring the boundary: `Span` and `Firing` carry one
window and the source never dates the turn. The treatment is batch 1's, applied
unchanged to b015a and b022w: the window is emitted whole and the segmentation
travels inside `verdict_text`, with `verdict_segments_the_window` on the rule.
Splitting the firing would author an end date for the first half that the page
does not print.

**A condition stated over several stars is one window, not several.** The day a
body crosses from one named star into the next belongs to both stars' spans, and
`sky._merge_adjacent` will not join them because their values differ. `_join_touching`
does, exactly as b055 joins Aquarius to Pisces for its two-sign Panchak -- so
B99's boundary day is one row and not two, and `Firing`'s one-row-per-rule,
location and day survives where the document states a disjunction.

**B107 and B115 turned on the word "alone", and the source defines it.** The
prophecy blocks print "Whenever Mercury Venus are alone in any sign without any
other Planet(s)" -- so "alone" is the absence of any other planet, which is the
same eleven-body set B16 was ported against. Two consequences the tables show
once the 2026 rows are checked against the ephemeris:

* **B107's single row is Venus's Shravana window cut where Mercury enters
  Shravana**, and it reproduces exactly: 21-Jan-26 2:50 (Venus's ingress) to
  23-Jan-26 10:25 (Mercury's). In 2027 the rule cannot fire at all, because
  Pluto occupies Shravana from 28-Dec-2026 to the end of the generated span and
  Venus's two 2027 visits are therefore never alone ones.
* **B115's two rows are the alone sub-windows**, not the union its title states:
  the Venus row ends where the Sun enters Shatabhisha, the Sun row starts where
  Venus leaves it and ends where Mars enters it -- all three to within two
  minutes. The title states the union and the rule fires the union; the table's
  narrower construction is recorded rather than adopted, because "alone" is not
  a word this section prints.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..ephem import SIGNS
from ..sky import Span, intersect, same
from . import names
from . import valence as VAL
from .base import blocked, resolved, rule
from .catalogue import B, split_statement
from .colocation import ORDER_FLAG, RESIDENCY_BODIES

#: Nakshatra and sign order, as index lookups off the engine's own tables.
#: Sign order, as an index lookup off the engine's own table, for the
#: twelfth-from-Saturn arithmetic of B94.
_SIDX = {s: i for i, s in enumerate(SIGNS)}

#: Carried by the sections whose verdict segments the window it is stated over.
#: The same flag b015a and b022w carry: the span is the whole window and the
#: split stays inside the verdict text, undated, because the source dates the
#: turn in words and never in time.
SEGMENTED_FLAG = "verdict_segments_the_window"


# ------------------------------------------------------------- conditions

def _both_retrograde(a: str, b: str):
    """Spans where `a` and `b` are retrograde at the same instant.

    Both halves come from the station records through `Sky.motion_spans`, which
    is why this needs no ephemeris and no new event class: "both retrograde" is
    the intersection of two emitted series.
    """
    def fn(sky):
        both = intersect(list(sky.motion_spans(a)), list(sky.motion_spans(b)),
                         same)
        return [s for s in both if s.value == "retrograde"]
    return fn


def _join_touching(spans) -> list[Span]:
    """Join spans that touch, collecting their values.

    `sky._merge_adjacent` joins only spans of EQUAL value, which is not what a
    multi-star window needs: two nakshatras are different values and one
    condition. It is the helper b055 carries for its two-sign Panchak, and it
    matters here for the same reason: without it the day a body crosses from one
    named star into the next is emitted twice, once under each star, and
    `Firing` means one row per rule, location and civil day.
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


def _in_nakshatra(body: str, stars: tuple[str, ...]):
    """Spans where `body` occupies one of `stars`, off its ingress series."""
    wanted = set(stars)

    def fn(sky):
        return _join_touching([s for s in sky.spans(body, "nakshatra")
                               if s.value in wanted])
    return fn


def _together_in_nakshatra(a: str, b: str, star: str):
    """Spans where `a` and `b` occupy the same one nakshatra, `star`.

    Batch 2's `_together` at one named star, which is what B88 is: B87's
    shared-nakshatra series restricted to the nakshatra Rahu is in.
    """
    def fn(sky):
        return intersect(list(sky.spans(a, "nakshatra")),
                         list(sky.spans(b, "nakshatra")),
                         lambda x, y: x if x == y == star else None)
    return fn


def _either(*conditions):
    """The union of several conditions' spans, touching spans merged.

    B115 is stated over two bodies -- "Either Sun or Venus in Shatbhisha" -- and
    the two halves are separate ingress series. Merging is only cosmetic here
    (the two 2027 visits do not touch) and is done anyway so a row is one
    window rather than two halves of one.
    """
    def fn(sky):
        merged: list[Span] = []
        for s in sorted((s for cond in conditions for s in cond(sky)),
                        key=lambda s: s.start):
            if merged and s.start <= merged[-1].end:
                prev = merged.pop()
                merged.append(Span(prev.start, max(prev.end, s.end), prev.value,
                                   prev.open_start, s.open_end))
            else:
                merged.append(s)
        return merged
    return fn


def _alone_in_nakshatra(body: str, star: str):
    """Spans where `body` is in `star` and no other residency body is.

    "Alone" is the source's own word and it has a definition on the page: the
    prophecy blocks gloss it as "alone in any sign without any other Planet(s)".
    The set judged against is batch 2's `RESIDENCY_BODIES`, imported rather than
    retyped so the two batches cannot come to answer "alone" differently -- and
    the source's own tables count Pluto as a Planet, B116's Planet-2 column
    naming it, so the outer bodies are not an editorial addition here.

    The Moon is not in the set, which is batch 2's decision and matters more
    here than it does for a sign: the Moon crosses a nakshatra in about a day,
    so counting it would break every window thirteen times a year.
    """
    others = [b for b in RESIDENCY_BODIES if b != body]

    def fn(sky):
        out: list[Span] = _in_nakshatra(body, (star,))(sky)
        for other in others:
            out = intersect(out, list(sky.spans(other, "nakshatra")),
                            lambda held, pos: held if pos != star else None)
        return out
    return fn


def _moon_twelfth_from_saturn():
    """Spans where the Moon's sign is the twelfth from Saturn's.

    Whole-sign, which is what the section's Sign column names, and counted
    Saturn-first: the twelfth from Saturn is the sign before his, so with Saturn
    in Pisces -- where he is throughout 2026 -- the condition is the Moon in
    Aquarius, which is what all thirteen printed rows carry.
    """
    def fn(sky):
        return intersect(
            list(sky.spans("Moon", "sign")), list(sky.spans("Saturn", "sign")),
            lambda moon, saturn:
            {"moon_sign": moon, "saturn_sign": saturn}
            if _SIDX[moon] == (_SIDX[saturn] - 1) % 12 else None)
    return fn


# ================================================= the three retrograde pairs
# ------------------------------------------------ B081  Saturn and Mercury
_B81_COND, _B81_VERDICT = split_statement(B(81).title)
assert "Saturn" in _B81_COND and "Mercury" in _B81_COND, _B81_COND

rule(
    id="b081_saturn_mercury_both_retrograde",
    section=B(81),
    rule_family="motion/both_retrograde",
    condition_text=_B81_COND,
    condition_from="title",
    verdict_text=_B81_VERDICT,
    verdict_from="title",
    inputs=("motion/station",),
    flags=("source_table_row_is_another_planets_retrograde_window",),
    notes="The condition is exact; the section's printed 2026 row is not the "
          "condition's window and is not looked to for the rule. Saturn is "
          "retrograde 27-Jul-26 to 11-Dec-26 and Mercury 24-Oct-26 12:42 to "
          "13-Nov-26 21:24, so the pair's 2026 window is 24-Oct-26 12:42 to "
          "13-Nov-26 21:24 -- which is what B83 prints, to within two minutes. "
          "B81's row, "
          "03-Oct-26 12:47 to 14-Nov-26 5:59, is "
          "VENUS's retrograde window: her station retrograde is 03-Oct-26 12:43 "
          "(four minutes before the printed start) and her station direct "
          "14-Nov-26 05:59 (the printed end exactly). Nothing was widened to "
          "meet the printed row. In 2027 the pair is retrograde together once, "
          "07-Oct to 28-Oct.",
)(_both_retrograde("Saturn", "Mercury"))


# ------------------------------------------------ B082  Jupiter and Mercury
_B82_COND, _B82_VERDICT = split_statement(B(82).title)
assert "Jupiter" in _B82_COND and "Mercury" in _B82_COND, _B82_COND

rule(
    id="b082_jupiter_mercury_both_retrograde",
    section=B(82),
    rule_family="motion/both_retrograde",
    condition_text=_B82_COND,
    condition_from="title",
    verdict_text=_B82_VERDICT,
    verdict_from="title",
    inputs=("motion/station",),
    flags=(),
    notes="Reproduces its printed 2026 row: 26-Feb-26 12:19 against a computed "
          "12:17 and 11-Mar-26 9:01 against a computed 09:23 -- 24 minutes at "
          "the start and 22 at the end, which is the widest miss in this batch "
          "and is stated as it is rather than rounded into agreement. Two "
          "windows in the generated span "
          "put the pair retrograde together; the second opens 24-Jan-2028, in "
          "the carry-out, and contributes no 2027 day.",
)(_both_retrograde("Jupiter", "Mercury"))


# -------------------------------------------------- B083  Mercury and Venus
_B83_COND, _B83_VERDICT = split_statement(B(83).title)
assert "Mercury" in _B83_COND and "Venus" in _B83_COND, _B83_COND

rule(
    id="b083_mercury_venus_both_retrograde",
    section=B(83),
    rule_family="motion/both_retrograde",
    condition_text=_B83_COND,
    condition_from="title",
    verdict_text=_B83_VERDICT,
    verdict_from="title",
    inputs=("motion/station",),
    flags=(),
    notes="Reproduces its printed 2026 row to within two minutes: 24-Oct-26 "
          "12:44 "
          "against 12:42 and 13-Nov-26 21:25 against 21:24. Zero in 2027, and "
          "the zero is an orbital-period one rather than a calendar boundary: "
          "Venus does not station at all in the generated span -- her previous "
          "retrograde is 03-Oct-26 to 14-Nov-26 and the next is in 2028 -- so "
          "the pair cannot be retrograde together anywhere in it. The verdict "
          "is the source's own word for a two-and-a-half-week bounce rather "
          "than a direction, and is carried as printed.",
)(_both_retrograde("Mercury", "Venus"))


# ============================================= the nakshatra-residency singles
# -------------------------------------- B088  Rahu in Dhanistha (no verdict)
# The continuation of B87's series, and the same condition under it: B87's
# eight printed windows are the Moon's transits of Shatabhisha with Rahu in
# Shatabhisha, and B88's five are the Moon's transits of Dhanishta with Rahu in
# Dhanishta. One Moon-Rahu conjunction series, partitioned by Rahu's nakshatra,
# verdict-free on this half. So the condition is b087's with the nakshatra
# restriction where b087s carries a proviso, and the verdict is none because
# the section prints none.
_DHANISHTA = names.nakshatra("Dhanistha")

rule(
    id="b088_moon_rahu_same_nakshatra_rahu_in_dhanishta",
    section=B(88),
    rule_family="residency/same_nakshatra",
    condition_text=B(88).title,
    condition_from="title",
    inputs=("ingress/nakshatra",),
    flags=("section_states_no_verdict", "condition_continues_the_b87_series"),
    notes="The title names only Rahu's nakshatra; the section's own five "
          "printed windows are what fixes the rest of the condition, and each "
          "of them is the Moon's transit of Dhanishta while Rahu is there -- "
          "the same series B87 tabulates, and the evidence "
          "`test_b87s_proviso_is_a_condition_the_document_itself_obeys` "
          "recomputes. All five reproduce in 2026, both ends within half a "
          "minute: 27-Aug 00:48/02:15, 23-Sep 09:09/10:35, 20-Oct 18:02/19:48, "
          "17-Nov 02:17/04:34, 14-Dec 09:12/11:53. Rahu is in Dhanishta until "
          "10-Apr-2027, so four windows fall in 2027 -- 10-Jan, 06-Feb, 05-Mar "
          "and 02-Apr -- and the fifth the series produces, 14-Dec-2026, is in "
          "the carry-in. No verdict is "
          "printed and none is carried: `verdict_text` is None, `claim_tag` "
          "None and `tier` None, which is the correct port of a section that "
          "states no market outcome.",
)(_together_in_nakshatra("Moon", "Rahu", _DHANISHTA))


# ---------------------------------------------------- B091  Sun in three stars
_B91_COND, _B91_VERDICT = split_statement(B(91).title)
_B91_STARS = names.nakshatras_in(_B91_COND)
assert "Sun" in _B91_COND and len(_B91_STARS) == 3, (_B91_COND, _B91_STARS)

rule(
    id="b091_sun_in_uttara_ashadha_ashwini_or_chitra",
    section=B(91),
    rule_family="residency/planet_nakshatra",
    condition_text=_B91_COND,
    condition_from="title",
    verdict_text=_B91_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=("table_duration_column_scopes_the_verdict",),
    notes="All three printed 2026 windows reproduce, both ends within 1.4 "
          "minutes: Sun in Uttara Ashadha 11-Jan 08:36/24-Jan 10:50 (printed "
          "08:37/10:51), in Ashwini 14-Apr 09:32/28-Apr 01:18 (printed "
          "09:33/01:18), in Chitra 11-Oct 02:20/24-Oct 12:50 (printed "
          "02:21/12:52). The star names are read out of the title through the "
          "spelling map, so 'Uttra Shada' is the engine's Uttara Ashadha. The "
          "table's Duration column scopes the verdict further than the title "
          "does -- '1st 5 days Bullish' against Uttra Shada, '1st 3 days "
          "Bullish' against Ashwini, '1st 5 days Bullish' against Chitra -- and "
          "each row names a different number of days, so there is no one "
          "verdict string to carry. The title's 'Bullish' is carried whole over "
          "the whole window and the Duration column is recorded here; the flag "
          "says the scoping exists. This is the b015a shape one level down: the "
          "segmentation is in the section's table rather than in its verdict, "
          "and a sub-window would have to be authored either way.",
)(_in_nakshatra("Sun", _B91_STARS))


# ------------------------------------------------------- B092  Sun in Kritika
_B92_COND, _B92_VERDICT = split_statement(B(92).title)
assert "Sun" in _B92_COND, _B92_COND

rule(
    id="b092_sun_in_krittika",
    section=B(92),
    rule_family="residency/planet_nakshatra",
    condition_text=_B92_COND,
    condition_from="title",
    verdict_text=_B92_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=(SEGMENTED_FLAG,),
    notes="Reproduces its printed 2026 row: 11-May-26 19:31 against 19:32 and "
          "25-May-26 15:37 against 15:38. The verdict segments the window it "
          "is stated over and is carried whole, undated, exactly as b015a "
          "carries 'fifteen days bearish, then bullish': the source says the "
          "first two days and never says at what instant they end, so the two "
          "days are not turned into a span. The same source's monthly block "
          "reads 'Sun alone from 11th-15th' against this window, which is a "
          "different and longer first segment than the title's two days; the "
          "title is the rule and the block is not ported here.",
)(_in_nakshatra("Sun", (names.nakshatra("Kritika"),)))


# -------------------------------- B094  Shani Chandra Dwidwadash Yog (resolved)
# The section names a yoga and defines it nowhere, and its own table cannot
# separate the two candidate definitions because Saturn is in Pisces throughout
# 2026. Both readings reproduce the thirteen printed rows in 2026; they come
# apart the moment Saturn changes sign. The reading used is the relation the
# name states, and it is a supplied one -- so this is `resolved_ambiguity` and
# not `executable`, and every row carries the flag that says so.
_B94_COND, _B94_VERDICT = split_statement(B(94).title)
assert "Shani" in _B94_COND and "Dwidwadash" in _B94_COND, _B94_COND

_DWIDWADASH_AMBIGUITY = (
    "The section names Shani Chandra Dwidwadash Yog and defines it nowhere. "
    "Its table's Sign column is the only statement of what the yoga is, and it "
    "prints one value -- Aquarius -- on all thirteen rows, so the table alone "
    "leaves two readings standing. On the FIXED-SIGN reading the yoga is the "
    "Moon in Aquarius, which is literally what every printed row carries. On "
    "the TWELFTH-FROM-SATURN reading it is the Moon in the sign twelfth from "
    "Saturn, which is what the name's own words say -- Shani Saturn, Chandra "
    "Moon, Dwidwadash twelfth -- and the note's 'Aquarius-Pisces axis' names "
    "the two signs that relation puts the pair in. The two readings coincide "
    "exactly while Saturn is in Pisces and diverge as soon as he is not: in "
    "2027 he leaves Pisces for Aries on 02-Jun and returns on 20-Oct, and the "
    "fixed-sign reading would go on firing on Aquarius windows in which the "
    "Moon is in the second from Saturn rather than the twelfth."
)

_DWIDWADASH_RESOLUTION = (
    "The reading is the twelfth-from-Saturn relation, counted Saturn-first and "
    "by whole sign. The name is the only definition the document offers, and "
    "its words are Saturn, Moon and twelfth.",

    "The printed table is consistent with it and cannot contradict it. Saturn "
    "is in Pisces for the whole of 2026 -- he enters Aries only on 02-Jun-2027 "
    "-- so the sign twelfth from Saturn is Aquarius all year, and the Moon's "
    "Aquarius windows reproduce all thirteen printed rows, both ends, to "
    "within 1.4 minutes: 21-Jan 01:35/23-Jan 08:33 against 01:37/08:34, "
    "06-Jun 19:03/09-Jun 03:36 against 19:05/03:37, 14-Dec 22:35/17-Dec 09:13 "
    "against 22:36/09:13, and so on down the table. Thirteen two-ended windows "
    "agreeing at both ends is not what a wrong reading reaches.",

    "The direction is decided by the same table. Read the other way round -- "
    "Saturn in the twelfth from the Moon, which with Saturn in Pisces would put "
    "the Moon in Aries -- the condition reproduces none of the thirteen rows: "
    "the Moon is in Aries on none of the printed dates."
)

_DWIDWADASH_REJECTED = (
    "The fixed-sign reading, the Moon in Aquarius. Not rejected as failing on "
    "the page -- it reproduces the same thirteen rows in 2026 -- but rejected "
    "as the rule, because it is a coincidence of Saturn's sign in that year. "
    "The document calls the condition a yoga between Saturn and the Moon and "
    "prints the pair as an axis; a fixed sign stops being a Saturn-Moon yoga "
    "the moment Saturn changes sign, which he does on 02-Jun-2027.",
    "Saturn in the twelfth from the Moon (the Moon in the second from Saturn). "
    "It reproduces none of the thirteen printed rows.",
    "The twelfth counted by degree rather than by whole sign -- a 30-degree "
    "arc ending at Saturn's longitude. The section's own Sign column names "
    "whole signs and one value, so there is nothing in the page that asks for "
    "a degree boundary, and it would cut the windows at instants no printed "
    "row carries.",
)

_DWIDWADASH_FLAG = "dwidwadash_definition_supplied_not_printed"

resolved(
    id="b094_shani_chandra_dwidwadash_yog",
    section=B(94),
    rule_family="residency/yoga",
    condition_text=_B94_COND,
    condition_from="title",
    verdict_text=_B94_VERDICT,
    verdict_from="title",
    inputs=("ingress/sign",),
    flags=(_DWIDWADASH_FLAG,),
    ambiguity=_DWIDWADASH_AMBIGUITY,
    resolution=_DWIDWADASH_RESOLUTION,
    rejected_readings=_DWIDWADASH_REJECTED,
    notes="The sign column's single value is the whole difficulty: a table "
          "that prints Aquarius thirteen times cannot distinguish a rule about "
          "Aquarius from a rule about the sign before Saturn in the one year "
          "Saturn is in Pisces. Both readings were computed against the table "
          "before this one was chosen, and the rejected ones are named above "
          "rather than discarded. The flag travels on every firing: the dates "
          "are the layer's, the definition they rest on is not on the page. "
          "The section's note adds that the impact is highest until the Moon "
          "reaches Saturn's degree; that is a quantity inside the window rather "
          "than a second condition and is not ported.",
)(_moon_twelfth_from_saturn())


# ------------------------------------------- B098  Mercury in Mool Nakshtra
# The title's colon heads the condition rather than scoping the verdict, which
# the harness pins by name, so `split_statement` gives the whole left half as
# the condition and a bare "Bearish" as the verdict.
_B98_COND, _B98_VERDICT = split_statement(B(98).title)
assert ":" in _B98_COND and "Mercury" in _B98_COND, _B98_COND

rule(
    id="b098_mercury_in_mula",
    section=B(98),
    rule_family="residency/planet_nakshatra",
    condition_text=_B98_COND,
    condition_from="title",
    verdict_text=_B98_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=(),
    notes="Both printed rows reproduce, and the two are different shapes. The "
          "first runs from the year's opening to Mercury's exit from Mula at "
          "07-Jan-26 00:02, computed 00:01 -- the table's 'Start of the year' "
          "cell is the carry-in, and the rule emits the carrying window rather "
          "than a date the year does not contain. The second is "
          "22-Dec-26 07:40 to 30-Dec-26 18:32, computed 07:39 and 18:31. Both "
          "rows' Motion column reads Direct, which the layer could supply, but "
          "no rule is stated over it and it is not ported as a condition.",
)(_in_nakshatra("Mercury", (names.nakshatra("Mool"),)))


# ------------- B099  Jupiter in Magha, Purva Falguni, Uttra Falguni or Hasta
_B99_COND, _B99_VERDICT = split_statement(B(99).title)
_B99_STARS = names.nakshatras_in(_B99_COND)
assert "Jupiter" in _B99_COND and len(_B99_STARS) == 4, (_B99_COND, _B99_STARS)

rule(
    id="b099_jupiter_in_magha_purva_phalguni_uttara_phalguni_or_hasta",
    section=B(99),
    rule_family="residency/planet_nakshatra",
    condition_text=_B99_COND,
    condition_from="title",
    verdict_text=_B99_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=(SEGMENTED_FLAG,),
    notes="Reproduces the start of its printed 2026 row exactly: Jupiter enters "
          "Magha at 31-Oct-26 12:02 and the table prints 31-Oct-26 12:02. The "
          "row's end is 'Till year end', which is where the 2026 table stops "
          "rather than where the condition does -- Jupiter is in Magha into "
          "2027 -- so the rule runs to the ingress and not to the calendar. It "
          "is a long window by this batch's standard: 214 Mumbai days in 2027, "
          "because Jupiter is in one of the four stars from the year's opening "
          "to 24-Jan, again from 25-Jun and continuously thereafter, reaching "
          "Uttara Phalguni on 04-Nov and Hasta only in 2028. The verdict "
          "segments the window -- the first fifteen days bearish, then bullish "
          "-- and is carried whole and undated, as b015a's is.",
)(_in_nakshatra("Jupiter", _B99_STARS))


# --------------------------------------- B107  Venus Alone in Shravan Nakshtra
_B107_COND, _B107_VERDICT = split_statement(B(107).title)
assert "Venus" in _B107_COND and "Alone" in _B107_COND, _B107_COND

rule(
    id="b107_venus_alone_in_shravana",
    section=B(107),
    rule_family="residency/alone_in_nakshatra",
    condition_text=_B107_COND,
    condition_from="title",
    verdict_text=_B107_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=("zero_2027_pluto_occupies_shravana",),
    notes="'Alone' is the source's own word and it has a definition on the "
          "page: the prophecy blocks gloss it as being 'alone in any sign "
          "without any other Planet(s)', and batch 2's eleven-body set is what "
          "B16 was ported against. The printed 2026 row reproduces under that "
          "reading exactly -- Venus enters Shravana at 21-Jan-26 02:50 and the "
          "window ends at 23-Jan-26 10:25, which is Mercury's ingress into "
          "Shravana to the second, and no other body of the eleven was in "
          "Shravana in between. Zero in 2027, and the zero is a fact about the "
          "sky rather than a porting failure: Venus visits Shravana twice "
          "(04-Mar to 16-Mar and 23-Dec to 03-Jan-2028) and is alone there on "
          "neither visit, because Pluto occupies Shravana from 28-Dec-2026 to "
          "the end of the generated span. The source counts Pluto as a planet "
          "-- B116's own Planet-2 column names it -- so it is not excluded from "
          "'alone' to make this rule fire. The section's 2026 row is itself a "
          "consequence of the same fact in the other direction: Pluto had not "
          "yet reached Shravana.",
)(_alone_in_nakshatra("Venus", names.nakshatra("Shravan")))


# --------------------------------------------------- B113  Mars in Dhanistha
_B113_COND, _B113_VERDICT = split_statement(B(113).title)
assert "Mars" in _B113_COND, _B113_COND

rule(
    id="b113_mars_in_dhanishta",
    section=B(113),
    rule_family="residency/planet_nakshatra",
    condition_text=_B113_COND,
    condition_from="title",
    verdict_text=_B113_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=(),
    notes="Reproduces its printed 2026 row: 15-Feb-26 00:38 against 00:37 and "
          "03-Mar-26 22:54 against 22:56. Zero in 2027, and the zero is a "
          "calendar-boundary one: Mars reaches Dhanishta again on "
          "25-Jan-2028, inside the layer's carry-out and outside calendar "
          "2027. The condition itself is exact and the rule is not idle for any "
          "other reason -- it fires on every one of the 17 days in 2026.",
)(_in_nakshatra("Mars", (names.nakshatra("Dhanistha"),)))


# -------------------------------------------- B114  Mercury in Purva Bhadrapada
_B114_COND, _B114_VERDICT = split_statement(B(114).title)
assert "Mercury" in _B114_COND, _B114_COND

rule(
    id="b114_mercury_in_purva_bhadrapada",
    section=B(114),
    rule_family="residency/planet_nakshatra",
    condition_text=_B114_COND,
    condition_from="title",
    verdict_text=_B114_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=(SEGMENTED_FLAG, "source_table_row_ends_outside_its_own_condition"),
    notes="The section's single printed 2026 row does not reproduce, and the "
          "finding is recorded rather than absorbed. Mercury is in Purva "
          "Bhadrapada twice in 2026 -- 15-Feb-26 21:33 to 10-Mar-26 07:55, and "
          "01-Apr-26 20:12 to 13-Apr-26 14:22, the second being the "
          "post-retrograde re-entry. The table prints one row, 15-Feb-26 21:43 "
          "to 14-Mar-26 14:20. Its start matches to ten minutes. Its end "
          "matches nothing: at 14-Mar-26 14:20 Mercury is in Shatabhisha at "
          "316.41 degrees, four days after it left Purva Bhadrapada, and no "
          "ingress of any body falls within five hours of the printed instant. "
          "The row's end is therefore the source's mistake and the rule fires "
          "the condition -- which puts nothing on paper for 14-Mar-2026 and "
          "puts the re-entry of 01-Apr to 13-Apr on it, which the table omits. "
          "The verdict segments the window and is carried whole and undated, as "
          "b015a's is.",
)(_in_nakshatra("Mercury", (names.nakshatra("Purva Bhadrapad"),)))


# ------------------------------------- B115  Either Sun or Venus in Shatbhisha
_B115_COND, _B115_VERDICT = split_statement(B(115).title)
assert "Sun" in _B115_COND and "Venus" in _B115_COND, _B115_COND

rule(
    id="b115_sun_or_venus_in_shatabhisha",
    section=B(115),
    rule_family="residency/planet_nakshatra",
    condition_text=_B115_COND,
    condition_from="title",
    verdict_text=_B115_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=("source_table_prints_alone_sub_windows",),
    notes="The condition is the union the title states -- either body in "
          "Shatabhisha, which is why the rule is not restricted to a single "
          "Planet column. The table's two rows are narrower than that union and "
          "the arithmetic says what they are: Venus enters Shatabhisha at "
          "11-Feb-26 08:52 and the Venus row ends 19-Feb-26 18:34, which is the "
          "Sun's ingress into Shatabhisha to the minute; the Sun row starts "
          "22-Feb-26 0:39, which is Venus's exit to two minutes, and ends "
          "03-Mar-26 22:56, which is Mars's ingress to two minutes. So each "
          "printed row is the window in which its named body is ALONE in "
          "Shatabhisha, and the union's remaining days -- 19-Feb to 22-Feb, "
          "when both are there, and 03-Mar to 05-Mar, when the Sun and Mars "
          "are -- are printed nowhere. The title does not say 'alone' and does "
          "not name Mars, so the rule fires the union and the table's "
          "construction is recorded here rather than adopted. In 2027 that is "
          "26 Mumbai days in two windows: 19-Feb to 05-Mar for the Sun and "
          "27-Mar to 07-Apr for Venus.",
)(_either(_in_nakshatra("Sun", (names.nakshatra("Shatbhisha"),)),
           _in_nakshatra("Venus", (names.nakshatra("Shatbhisha"),))))


# ------------------------------------------------- B117  Jupiter in Paap Kartari
# BLOCKED, on the same absence that blocks B19 in batch 2: a valence the source
# states and never defines. Paap Kartari is a planet hemmed between two
# malefics, and the section's own Planet-1 and Planet-2 columns name the
# flanking bodies rather than a classification -- Mars and Ketu on both of its
# 2026 rows. Naming the pair is not the rule; the rule is that both are
# malefic, and nothing on the page says which planets are.
rule(
    id="b117_jupiter_in_paap_kartari",
    section=B(117),
    rule_family="residency/hemmed_between_malefics",
    condition_text=B(117).title,
    condition_from="title",
    inputs=("order/neighbours", "ingress/sign", "panchang/tithi"),
    notes="PORTED 20-Nov-2026 (blocked on valence until then), on the same "
          "definition as B116: config `valence` and its `kartari` hemming rule, "
          "over the astronomy layer's `neighbour_change` series. VERIFIED: the "
          "printed 25-Aug to 12-Nov-26 window on Mars|Ketu reproduces (the page "
          "splits it at Jupiter's 31-Oct sign change). CARRIED: 13-29 Jul "
          "(Sun|Ketu) and a window from 16-Nov the printed table stops before. "
          "The section's remark -- the yog is ineffective while the Moon runs "
          "from Jupiter to Ketu -- is a defeater recorded and NOT applied: the "
          "layer has no Moon-planet crossing series, and the printed window "
          "does not apply it either (it runs unbroken through two lunar passes).",
)(lambda sky: VAL.paap_kartari(sky, "Jupiter"))
