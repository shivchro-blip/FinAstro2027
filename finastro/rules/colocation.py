"""Batch 2 -- the colocation families.

Twenty-one catalogue-B sections in which the condition is a *relation between
two or more bodies* rather than a property of one: exact conjunction and
opposition (B12, B17, B41, B42, B47, B48, B53, B54), shared residency in a sign
or a nakshatra (B16, B78, B84, B87, B90, B93, B112), and longitudinal ordering
inside a shared sign (B18, B19, B79, B80, B85, B86).

The first two groups are read straight off the astronomy layer: a conjunction is
a record, and shared residency is the intersection of two ingress-derived span
series, which `sky.intersect` already expresses. Neither needed anything new.

The third group did, and it is the batch's one real decision.

**Ordering, and the navamsa ladder.** "Venus Behind Jupiter in the Same Sign"
needs to know which of two bodies is further along the zodiac, and the astronomy
layer emits `lon_sid` only at the instants of other events -- so inside a
shared-sign window there is frequently no sampled longitude for either body.
`test_2027_astronomy.py` settles the same question by calling
`ephem.longitude()` directly, which the rule layer may not do: a rule that
reached the ephemeris could disagree with the calendar, which is the one failure
this layer is built to make impossible.

What the layer *does* carry continuously is each body's nakshatra and navamsa
ingress series. A nakshatra is 13 degrees 20 minutes and a navamsa is exactly a
quarter of it, so (nakshatra index, pada) is a monotone position ladder at 3
degrees 20 minutes resolution, recovered from two emitted series and one
definitional identity -- 1 nakshatra = 4 navamsas -- and no ephemeris call.

The ladder is **exact where it separates and silent where it does not.** Two
bodies in the same navamsa are within 3 degrees 20 minutes and their order is
simply not in the astronomy layer; those stretches carry `None` and fire
nothing. That is partial coverage with exact positives, not an approximation,
and the distinction only holds if the silence is visible -- so every ordering
rule declares `ordering_from_navamsa_ladder` and the harness pins the tied days
per pair. A tie that grows is a change in the sky or a bug, and either way it
must not pass as an absence of the configuration.

Mars/Jupiter is the cross-check that the ladder is right rather than merely
plausible: it resolves all three 2027 shared-sign windows as Mars ahead, which
is independently what `test_2027_astronomy.py` gets from three direct
`ephem.longitude()` samples per window. Two unrelated methods, same answer, and
the ladder needed no ephemeris.

**A verdict scoped by a colon.** B87's heading reads "Moon and Rahu in Same
Nakshtra - Bullish: Rahu in Shatbisha". It was first ported as one rule whose
verdict named the 2026 instance; that reading was wrong and the section is now
two rules. The colon restricts the verdict rather than annotating it, and the
document says so itself: B87 prints eight Moon-with-Rahu windows and Rahu is in
Shatabhisha at all eight, while B88 -- "Rahu in Dhanistha" -- prints the next
five of the same monthly series with Rahu in Dhanishta and no verdict at all.
One condition, partitioned by Rahu's nakshatra, Bullish on one part. So `b087`
carries the condition with the verdict withheld, and `b087s` carries the
condition with the proviso and the verdict, and fires zero times in 2027
because Rahu is never in Shatabhisha in it. Withholding rather than emitting is
B19's treatment reached by a different route: there the proviso cannot be
evaluated, here it can be and is not met.

**Per-row verdicts.** The six conjunction/opposition sections print one row per
partner body with that partner's own Result -- Neptune-Venus is "Bearish" while
Neptune-Saturn is blank -- so each row is ported as its own rule, with the
partner taken from the table's Planet column and the verdict from its Result
column. Neither is typed here. A blank Result is a section that states no
verdict for that pairing, and is carried as `verdict_text=None`.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..ephem import NAKSHATRAS, SIGNS
from ..sky import Span, intersect, parse, same
from . import names
from .base import blocked, rule
from .catalogue import B, split_proviso, split_statement

#: Nakshatra and sign order, as index lookups. Both come from the engine, so
#: the ladder below is ordered by the same vocabulary the records are in.
_NIDX = {n: i for i, n in enumerate(NAKSHATRAS)}
_SIDX = {s: i for i, s in enumerate(SIGNS)}

#: Declared by every rule whose condition is an ordering. Names the method and
#: therefore its limit: exact to 3 degrees 20 minutes, silent inside that.
ORDER_FLAG = "ordering_from_navamsa_ladder"

#: The residency bodies "alone in a sign" is judged against, per B16. The same
#: set `test_2027_astronomy.py` uses, so the two layers answer "alone" the same
#: way.
RESIDENCY_BODIES = ("Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn",
                    "Rahu", "Ketu", "Uranus", "Neptune", "Pluto")


# ------------------------------------------------------------ the ladder

def _pada(nakshatra: str, navamsa: str) -> int | None:
    """Which quarter of `nakshatra` the body is in, from its navamsa sign.

    Nakshatra *k* spans navamsas 4k..4k+3, and a navamsa's name is its index
    modulo twelve, so the pada is recoverable by subtraction. A result outside
    0..3 means the two series disagree about where the body is, which is a
    corrupt record rather than an unusual sky, and is surfaced as None.
    """
    p = (_SIDX[navamsa] - 4 * _NIDX[nakshatra]) % 12
    return p if p < 4 else None


def _rank(nakshatra: str, navamsa: str) -> int | None:
    p = _pada(nakshatra, navamsa)
    return None if p is None else _NIDX[nakshatra] * 4 + p


def _rank_spans(sky, body: str) -> list[Span]:
    """`body`'s position as a monotone rank, at navamsa resolution.

    Refuses a body whose navamsa series the astronomy layer does not carry.
    NO BODY IS IN THAT STATE ANY MORE. The Moon was, until 21-Sep-2026 -- it
    crosses a navamsa every 6.06 hours and no ingress series was emitted for
    it -- and the guard is kept because what it refuses is the fallback single
    span in `Sky.spans`, which would read as "one navamsa all year" and
    silently order every comparison wrongly instead of failing. A guard that
    has stopped firing is not a guard that has stopped being needed; it is the
    only thing standing between a dropped series and a plausible answer.
    """
    nav = sky.spans(body, "navamsa")
    if len(nav) < 2:
        raise ValueError(
            f"{body} has fewer than two navamsa spans in the astronomy "
            f"layer ({len(nav)}); its position cannot be ranked, and a rule "
            "needing its order is blocked rather than ranked on the fallback")
    return intersect(list(sky.spans(body, "nakshatra")), list(nav), _rank)


def _order_spans(sky, a: str, b: str) -> list[Span]:
    """Spans of `a`'s order relative to `b`, inside their shared sign.

    The value is "ahead", "behind", or None where the two share a navamsa and
    the astronomy layer therefore does not separate them. None spans are
    returned rather than dropped, so a caller can count what it cannot answer.
    """
    shared = intersect(list(sky.spans(a, "sign")), list(sky.spans(b, "sign")),
                       same)
    ra, rb = _rank_spans(sky, a), _rank_spans(sky, b)
    out: list[Span] = []
    for w in shared:
        clip_a = [s.clipped(w.start, w.end) for s in ra
                  if s.overlaps(w.start, w.end)]
        clip_b = [s.clipped(w.start, w.end) for s in rb
                  if s.overlaps(w.start, w.end)]
        for s in intersect(clip_a, clip_b,
                           lambda x, y: "ahead" if x > y
                           else "behind" if x < y else "tied"):
            out.append(Span(s.start, s.end,
                            None if s.value == "tied" else s.value,
                            s.open_start, s.open_end))
    return out


def tied_days(sky, a: str, b: str) -> float:
    """Days inside `a`/`b`'s shared-sign windows the ladder cannot order.

    Exposed because it is the number that has to be watched. Reported by the
    harness per pair rather than summed, since a tie is only interpretable
    against the window it sits in.
    """
    return sum((s.end - s.start).total_seconds() / 86400
               for s in _order_spans(sky, a, b) if s.value is None)


# ------------------------------------------------------------- conditions

def _aspect(event_class: str, a: str, b: str):
    """The exact instants of an unordered pair's conjunction or opposition."""
    def fn(sky):
        return [Span(parse(r["time"]["t_start_utc"]),
                     parse(r["time"]["t_start_utc"]),
                     {"sign": r["astronomy"]["sign"], "bodies": r["bodies"]})
                for r in sky.aspect_instants(event_class, a, b)]
    return fn


def _together(a: str, b: str, frame: str, value: str | None = None):
    """Spans where `a` and `b` share a position in `frame`.

    `value` restricts to one sign or star -- B112 is stated about Shravan
    alone, not about Venus and Mercury sharing any nakshatra.
    """
    def fn(sky):
        out = intersect(list(sky.spans(a, frame)), list(sky.spans(b, frame)),
                        same)
        if value is not None:
            out = [s for s in out if s.value == value]
        return out
    return fn


def _alone(a: str, b: str):
    """Spans where `a` and `b` share a sign no other residency body is in."""
    others = [x for x in RESIDENCY_BODIES if x not in (a, b)]

    def fn(sky):
        out = intersect(list(sky.spans(a, "sign")),
                        list(sky.spans(b, "sign")), same)
        for o in others:
            out = intersect(out, list(sky.spans(o, "sign")),
                            lambda shared, third:
                            shared if shared != third else None)
        return out
    return fn


def _in_nakshatra(body: str, *stars: str):
    """Spans where `body` occupies any one of `stars`.

    A one-name call is the restricted case (B89's Rohini half); a two-name call
    is the bare condition it was split from. Reading `Sky.spans` keeps every
    name a claim about the source's own vocabulary -- each is looked up through
    `names.nakshatra`, which raises rather than silently missing.
    """
    wanted = {names.nakshatra(s) for s in stars}

    def fn(sky):
        return [s for s in sky.spans(body, "nakshatra") if s.value in wanted]
    return fn


def _ordered(a: str, b: str, which: str):
    """Shared-sign spans where `a` is `which` ("ahead"/"behind") of `b`."""
    def fn(sky):
        return [s for s in _order_spans(sky, a, b) if s.value == which]
    return fn


def _middle(front: str, back: str, mid: str):
    """Spans where `front` leads `back` and `mid` sits between the two.

    Three ladder comparisons, all from the same two emitted series. A stretch
    where any of the three pairs shares a navamsa is not ordered and is not
    returned -- the same silence the pairwise rules have, and the reason B18
    carries `ORDER_FLAG` too.
    """
    def fn(sky):
        rf, rb, rm = (_rank_spans(sky, front), _rank_spans(sky, back),
                      _rank_spans(sky, mid))
        pair = intersect(rf, rb, lambda f, b: (f, b))
        out = []
        for s in intersect(pair, rm, lambda fb, m: (fb[0], fb[1], m)):
            f, b, m = s.value
            if f > m > b:
                out.append(Span(s.start, s.end,
                                {"front": front, "middle": mid, "back": back},
                                s.open_start, s.open_end))
        return out
    return fn


# ============================================================ conjunctions
# ------------------------------------------------------- B012  Mars/Mercury
# Verdict-free: a date-time-sign table and nothing else.
rule(
    id="b012_mars_mercury_conjunction",
    section=B(12),
    rule_family="aspect/conjunction",
    condition_text=B(12).title,
    condition_from="title",
    inputs=("aspect/conjunction",),
    flags=("section_states_no_verdict",),
)(_aspect("conjunction", "Mars", "Mercury"))


# ----------------------------------------------------- B017  Venus/Mercury
# The remark IS the verdict, and it is unusual in the document for having no
# condition beyond the section title: the conjunction itself is the turning day.
# The table's Status column (Direct / Contra-Directional) classifies the pair's
# motions, which the layer can supply, but the source never states a rule that
# turns on the class -- so it is left where the source put it rather than
# ported as a condition nobody wrote.
rule(
    id="b017_venus_mercury_conjunction",
    section=B(17),
    rule_family="aspect/conjunction",
    condition_text=B(17).title,
    condition_from="title",
    verdict_text=B(17).remarks[0],
    verdict_from="remark[0]",
    inputs=("aspect/conjunction",),
    flags=("status_column_not_ported",),
    notes="Status (Direct / Contra-Directional) is printed per row and no rule "
          "is stated over it; motion_spans could supply it if one ever is.",
)(_aspect("conjunction", "Venus", "Mercury"))


# ------------------------- B041/B042/B047/B048/B053/B054  the outer sections
#: Section -> (event class, the section's own body). The partner list is NOT
#: here: it is read from each table's Planet column below, so the document
#: decides which pairings the rule layer carries.
_OUTER_SECTIONS = (
    (41, "conjunction", "Herschel"),
    (42, "opposition", "Herschel"),
    (47, "conjunction", "Neptune"),
    (48, "opposition", "Neptune"),
    (53, "conjunction", "Pluto"),
    (54, "opposition", "Pluto"),
)

#: Rules built from the tables, one per printed row. Kept so the harness can
#: check the count against the document's own row count rather than a constant.
OUTER_PAIR_RULES: list[str] = []

for _b, _cls, _own in _OUTER_SECTIONS:
    _sec = B(_b)
    _own_engine = names.body(_own)
    for _i, _row in enumerate(_sec.tables[0].rows):
        _partner, _result = _row[0], _row[3]
        _pe = names.body(_partner)
        _rid = f"b{_b:03d}_{_own.lower()}_{_cls}_{_pe.lower()}"
        OUTER_PAIR_RULES.append(_rid)
        rule(
            id=_rid,
            section=_sec,
            rule_family=f"aspect/{_cls}",
            condition_text=_sec.title,
            condition_from="title",
            # The partner is the row's own first cell and the verdict its
            # fourth; a blank fourth cell is a pairing the section prints
            # without a result, carried as no verdict rather than as the
            # section's general one.
            verdict_text=_result or None,
            verdict_from=(f"table row {_i + 1} ({_partner}), Result column"
                          if _result else None),
            inputs=(f"aspect/{_cls}",),
            flags=(("verdict_is_per_partner_body",) if _result
                   else ("section_states_no_verdict_for_this_pairing",)),
            notes=f"{_own} with {_partner}, from the section's own Planet "
                  f"column."
                  + (f" The source names Uranus '{_own}' throughout; the "
                     f"engine body is {_own_engine}."
                     if _own == "Herschel" else ""),
        )(_aspect(_cls, _own_engine, _pe))


# ======================================================= shared residency
# --------------------------------------------- B016  Mercury/Venus alone
rule(
    id="b016_mercury_venus_alone_in_a_sign",
    section=B(16),
    rule_family="residency/alone_in_sign",
    condition_text=B(16).title,
    condition_from="title",
    inputs=("ingress/sign",),
    flags=("section_states_no_verdict",),
    notes="'Alone' is judged against the eleven residency bodies, the same set "
          "the astronomy suite uses. The Aspect column ('4th aspect of Mars') "
          "is an annotation on the window, not a second condition, and is not "
          "ported.",
)(_alone("Mercury", "Venus"))


# --------------------------------------------- B078  Venus/Jupiter same sign
rule(
    id="b078_venus_jupiter_same_sign",
    section=B(78),
    rule_family="residency/same_sign",
    condition_text=B(78).title,
    condition_from="title",
    inputs=("ingress/sign",),
    flags=("section_states_no_verdict",),
    notes="The bare shared-sign window. Its two verdicts are conditioned on "
          "the ordering and are B79 and B80.",
)(_together("Venus", "Jupiter", "sign"))


# --------------------------------------------- B084  Mars/Jupiter same sign
rule(
    id="b084_mars_jupiter_same_sign",
    section=B(84),
    rule_family="residency/same_sign",
    condition_text=B(84).title,
    condition_from="title",
    inputs=("ingress/sign",),
    flags=("section_states_no_verdict",),
)(_together("Mars", "Jupiter", "sign"))


# ------------------------------------------ B087  Moon/Rahu same nakshatra
# RE-READ, and the re-reading split the section. See the module docstring.
# "Bullish: Rahu in Shatbisha" is not a verdict with the 2026 instance stuck on
# the end. The colon SCOPES the verdict: the general rule is the shared
# nakshatra, and Bullish is asserted for the Shatabhisha case only. So the
# condition and the conditioned verdict are two rules, exactly as B78 is the
# bare Venus/Jupiter window and B79/B80 are its two conditioned verdicts.
_B87_COND, _B87_STATEMENT = split_statement(B(87).title)
_B87_VERDICT, _B87_PROVISO = split_proviso(_B87_STATEMENT)
assert _B87_PROVISO, "B87's colon is gone; re-read the split"

#: The star the proviso names, through the one spelling bridge. Going through
#: `names.nakshatra` keeps the restriction a claim about the SOURCE's own
#: vocabulary -- "Shatbisha" is a spelling the document uses -- and it raises
#: rather than silently missing if the map ever loses the entry.
_SHATABHISHA = names.nakshatra("Shatbisha")

rule(
    id="b087_moon_rahu_same_nakshatra",
    section=B(87),
    rule_family="residency/same_nakshatra",
    condition_text=_B87_COND,
    condition_from="title",
    inputs=("ingress/nakshatra",),
    flags=("verdict_conditioned_on_rahu_in_shatabhisha_not_met_in_2027",),
    notes="The condition fires; the verdict is withheld, because the section "
          "states Bullish only for the Rahu-in-Shatabhisha case and Rahu is "
          "never in Shatabhisha in 2027 -- Dhanishta to 10-Apr, Shravana to "
          "18-Dec, Uttara Ashadha after. Emitting the verdict on these rows "
          "would assert an outcome the source restricted. Same handling as "
          "B19, whose proviso is unevaluated rather than unmet; there the "
          "whole rule is blocked because the ordering has no statable outcome "
          "without it, and here the bare window is a rule the document itself "
          "prints -- B88 is this condition with Rahu in Dhanishta, printed "
          "with no verdict at all.",
)(_together("Moon", "Rahu", "nakshatra"))

# The verdict half, restricted to the case the section restricts it to. Zero
# firings in 2027 by construction, pinned by name in the harness with that
# reason, like b004 and b015r.
rule(
    id="b087s_moon_rahu_same_nakshatra_rahu_in_shatabhisha",
    section=B(87),
    rule_family="residency/same_nakshatra",
    condition_text=_B87_COND,
    condition_from="title",
    condition_proviso=_B87_PROVISO,
    verdict_text=_B87_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=("verdict_scoped_by_colon_in_title",),
    notes="The evidence that the colon is a condition and not a label is the "
          "document's own partition of the series. B87 prints eight "
          "Moon-with-Rahu windows, 21-Jan to 01-Aug-2026, and Rahu is in "
          "Shatabhisha at every one; B88 -- 'Rahu in Dhanistha' -- prints the "
          "next five, 27-Aug to 15-Dec-2026, with Rahu in Dhanishta at every "
          "one and no verdict printed. Same monthly conjunction series, split "
          "by which nakshatra Rahu occupies, Bullish on one half only. Where "
          "Rahu is in Shatabhisha this rule and the bare b087 both fire, which "
          "is the B78/B79/B80 shape and not a double count: one is the window, "
          "the other the window with its outcome.",
)(_together("Moon", "Rahu", "nakshatra", value=_SHATABHISHA))


# ------------------------------------------ B089  Mars in Rohini or Chitra
# OWED from section 12.3 and delivered here: the same colon-scoped shape as B87.
# "Bullish: Mars in Rohini" is not a verdict with the 2026 instance appended.
# The colon SCOPES the verdict: the condition is Mars in either nakshatra, and
# Bullish is asserted for the Rohini case alone. So the condition and the
# conditioned verdict are two rules, exactly as B87 splits.
#
# The evidence is the source's own partition, and it is the mirror image of
# B87's. B89 prints ONE window, 04-Jul-26 to 24-Jul-26, and Mars is in Rohini
# at it. Mars is also in Chitra in 2026 -- and the document prints no Bullish
# window there. So the two halves of the condition are not interchangeable on
# the page, which is what makes the colon a restriction rather than a label.
_B89_COND, _B89_STATEMENT = split_statement(B(89).title)
_B89_VERDICT, _B89_PROVISO = split_proviso(_B89_STATEMENT)
assert _B89_PROVISO, "B89's colon is gone; re-read the split"

_ROHINI = names.nakshatra("Rohini")
_CHITRA = names.nakshatra("Chitra")

rule(
    id="b089_mars_in_rohini_or_chitra",
    section=B(89),
    rule_family="residency/nakshatra",
    condition_text=_B89_COND,
    condition_from="title",
    inputs=("ingress/nakshatra",),
    flags=("verdict_conditioned_on_mars_in_rohini_not_met_in_2027",),
    notes="The condition fires; the verdict is withheld, because the section "
          "states Bullish only for the Mars-in-Rohini case and 2027 puts Mars "
          "in Chitra from 13-Aug to 03-Sep and never in Rohini. Emitting the "
          "verdict on the Chitra window would assert an outcome the source "
          "restricted. Same handling as B87: the bare window is a rule the "
          "document itself prints, and the conditioned verdict is a second "
          "rule that is correctly silent.",
)(_in_nakshatra("Mars", _ROHINI, _CHITRA))


# The verdict half, restricted to the case the section restricts it to. Zero
# firings in 2027 by construction, pinned by name in the harness with that
# reason, like b004, b015r and b087s.
rule(
    id="b089s_mars_in_rohini",
    section=B(89),
    rule_family="residency/nakshatra",
    condition_text=_B89_COND,
    condition_from="title",
    condition_proviso=_B89_PROVISO,
    verdict_text=_B89_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    flags=("verdict_scoped_by_colon_in_title",),
    notes="2027 puts Mars in Chitra 13-Aug to 03-Sep and never in Rohini, so "
          "this rule is silent while the bare b089 fires on the Chitra window "
          "-- the same shape as b087s, and the same reason to keep the count "
          "pinned rather than let a zero read as an absence.",
)(_in_nakshatra("Mars", _ROHINI))


# ------------------------------------------ B090  Venus/Mars same nakshatra
_B90_COND, _B90_VERDICT = split_statement(B(90).title)

rule(
    id="b090_venus_mars_same_nakshatra",
    section=B(90),
    rule_family="residency/same_nakshatra",
    condition_text=_B90_COND,
    condition_from="title",
    verdict_text=_B90_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
)(_together("Venus", "Mars", "nakshatra"))


# ---------------------------------------------- B093  Moon/Mars same sign
_B93_COND, _B93_VERDICT = split_statement(B(93).title)

rule(
    id="b093_moon_mars_same_sign",
    section=B(93),
    rule_family="residency/same_sign",
    condition_text=_B93_COND,
    condition_from="title",
    verdict_text=_B93_VERDICT,
    verdict_from="title",
    inputs=("ingress/sign",),
)(_together("Moon", "Mars", "sign"))


# ------------------------------------- B112  Venus/Mercury in Shravan only
_B112_COND, _B112_VERDICT = split_statement(B(112).title)

rule(
    id="b112_venus_mercury_together_in_shravana",
    section=B(112),
    rule_family="residency/same_nakshatra",
    condition_text=_B112_COND,
    condition_from="title",
    verdict_text=_B112_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra",),
    notes="Restricted to Shravana, which is what the section states; the "
          "general 'Venus and Mercury in the same nakshatra' is a rule the "
          "document does not make. Star name via the spelling map: the source "
          "writes 'Shravan'.",
)(_together("Venus", "Mercury", "nakshatra",
            value=names.nakshatra("Shravan")))


# =============================================================== ordering
# ------------------------------- B079/B080  Venus behind / ahead of Jupiter
_B79_COND, _B79_VERDICT = split_statement(B(79).title)
_B80_COND, _B80_VERDICT = split_statement(B(80).title)

rule(
    id="b079_venus_behind_jupiter_same_sign",
    section=B(79),
    rule_family="residency/order_in_sign",
    condition_text=_B79_COND,
    condition_from="title",
    verdict_text=_B79_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra", "ingress/navamsa", "ingress/sign"),
    flags=(ORDER_FLAG,),
    notes="Ordering at navamsa resolution. The 2027 window has a tied stretch "
          "around the pair's conjunction which fires neither this rule nor "
          "B80; the harness pins its length.",
)(_ordered("Venus", "Jupiter", "behind"))

rule(
    id="b080_venus_ahead_of_jupiter_same_sign",
    section=B(80),
    rule_family="residency/order_in_sign",
    condition_text=_B80_COND,
    condition_from="title",
    verdict_text=_B80_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra", "ingress/navamsa", "ingress/sign"),
    flags=(ORDER_FLAG,),
)(_ordered("Venus", "Jupiter", "ahead"))


# --------------------------------- B085/B086  Mars behind / ahead of Jupiter
_B85_COND, _B85_VERDICT = split_statement(B(85).title)
_B86_COND, _B86_VERDICT = split_statement(B(86).title)

rule(
    id="b085_mars_behind_jupiter_same_sign",
    section=B(85),
    rule_family="residency/order_in_sign",
    condition_text=_B85_COND,
    condition_from="title",
    verdict_text=_B85_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra", "ingress/navamsa", "ingress/sign"),
    flags=(ORDER_FLAG,),
)(_ordered("Mars", "Jupiter", "behind"))

rule(
    id="b086_mars_ahead_of_jupiter_same_sign",
    section=B(86),
    rule_family="residency/order_in_sign",
    condition_text=_B86_COND,
    condition_from="title",
    verdict_text=_B86_VERDICT,
    verdict_from="title",
    inputs=("ingress/nakshatra", "ingress/navamsa", "ingress/sign"),
    flags=(ORDER_FLAG,),
    notes="The ladder orders Mars ahead across all three 2027 shared-sign "
          "windows with no tied stretch, which is independently what "
          "test_2027_astronomy.py gets from direct longitude samples. The "
          "section's remark dates a crossing rather than the window and is "
          "b086x below.",
)(_ordered("Mars", "Jupiter", "ahead"))

# The remark is a SECOND rule in the same section, and a different shape: it is
# stated about the crossing instant plus eleven days, not about the ordering
# span. The crossing is the Mars-Jupiter conjunction, which the layer emits as
# a record -- there simply is not one in 2027, and the zero is pinned with that
# reason rather than folded into B086.
_B86R_COND, _B86R_VERDICT = split_statement(B(86).remarks[0])

rule(
    id="b086x_mars_crosses_jupiter_eleven_days",
    section=B(86),
    rule_family="aspect/conjunction",
    condition_text=_B86R_COND,
    condition_from="remark[0]",
    verdict_text=_B86R_VERDICT,
    verdict_from="remark[0]",
    inputs=("aspect/conjunction",),
    flags=("verdict_states_its_own_duration",),
    notes="'eleven days Bullish' dates the window from the crossing; the span "
          "emitted is the crossing instant and the eleven days stay in the "
          "verdict text, undated, exactly as the source leaves them. "
          "Extending the span by eleven days would author an end date the "
          "document never prints.",
)(_aspect("conjunction", "Mars", "Jupiter"))


# ------------------------------- B018  Sun ahead, Venus behind, Mercury mid
# The note states an outcome -- "market deliver big positive return" -- but
# states it in one comma-joined sentence with no dash, so `split_statement`
# returns the whole thing as the condition and no verdict. That is the right
# outcome of the project's own rule and it is left standing: the comma is not
# the document's statement separator anywhere else, and promoting it to one
# here would author a boundary in the single place it happened to be
# convenient. The consequence is that this rule UNDERSTATES its section -- the
# outcome is carried, inside `condition_text`, and reported as no verdict -- so
# the flag says exactly that rather than leaving the reader to notice.
_B18_COND, _B18_VERDICT = split_statement(B(18).notes[0])
assert _B18_VERDICT is None, "B18's note gained a dash; re-read the split"

rule(
    id="b018_sun_ahead_venus_behind_mercury_middle",
    section=B(18),
    rule_family="residency/order_in_sign",
    condition_text=_B18_COND,
    condition_from="note[0]",
    verdict_text=_B18_VERDICT,
    verdict_from="note[0]",
    inputs=("ingress/nakshatra", "ingress/navamsa"),
    flags=(ORDER_FLAG, "ordering_is_three_body",
           "outcome_stated_but_not_separable_no_dash"),
    notes="The note's outcome -- 'market deliver big positive return' -- is "
          "inside condition_text because the source joins it with a comma "
          "rather than its usual dash, and the comma is not promoted to a "
          "separator. This rule therefore reports no verdict while its section "
          "plainly states one. "
          "Three ladder comparisons rather than one, so the tied fraction is "
          "larger: about 9 per cent of the Sun/Venus/Mercury year is inside a "
          "shared navamsa for at least one of the three pairs and is not "
          "ordered. Those stretches sit at the configuration's own boundaries, "
          "where the bodies are closest, so the windows this fires are "
          "narrower than the source's and never wider.",
)(_middle("Sun", "Venus", "Mercury"))


# ------------------------------- B019  Venus ahead, Sun behind, Mercury mid
# BLOCKED, and not on the ordering -- the ladder handles that as well as it
# does B18. The blocker is the remark's own proviso: "provided there is a
# malefic aspect on Mercury". The astronomy layer emits conjunctions and
# oppositions as records but classifies no aspect as benefic or malefic, and
# the source never prints the classification either. A verdict stated under a
# proviso, fired without evaluating the proviso, would assert something the
# source conditioned -- so the ordering half is left uncomputed with the
# missing input named, rather than fired with the condition quietly dropped.
def _b19(sky):
    """B18's mirror ordering (Venus ahead, Sun behind, Mercury between),
    kept only where a malefic casts a drishti on Mercury's sign."""
    from . import valence as VAL
    order = _middle("Venus", "Sun", "Mercury")(sky)
    bodies = ["Mercury"] + [b for b in VAL.CLASSICAL if b != "Mercury"]

    def malefic_aspect(st, t):
        ms = st.at("Mercury", "sign", t)
        hits = sorted(f"{b} {VAL.ordinal(h)}" for b in VAL.CLASSICAL
                      if b != "Mercury" and st.valence(b, t) == "malefic"
                      and (h := VAL.aspects(b, st.at(b, "sign", t), ms)))
        return ", ".join(hits) or None
    asp = VAL.piecewise(sky, bodies, malefic_aspect)
    return intersect(order, asp, lambda o, a: {"malefic_aspect": a})


rule(
    id="b019_venus_ahead_sun_behind_mercury_middle",
    section=B(19),
    rule_family="residency/order_in_sign",
    condition_text=B(19).remarks[0],
    condition_from="remark[0]",
    inputs=("ingress/nakshatra", "ingress/navamsa", "ingress/sign",
            "panchang/tithi"),
    flags=(ORDER_FLAG, "ordering_is_three_body",
           "outcome_stated_but_not_separable_no_dash"),
    notes="PORTED 20-Nov-2026 (blocked on valence until then). The ordering is "
          "B18's ladder mirrored; the proviso 'a malefic aspect on Mercury' is "
          "a whole-sign drishti from a malefic (config `valence`). The verdict "
          "('it is Bearish') sits inside the remark, joined by a comma, as in "
          "B18, so it travels in condition_text and not as a separate field. "
          "The section's printed remarks describe Mercury's hemming and its "
          "aspects rather than stating dated windows the rule can be scored on.",
)(_b19)
