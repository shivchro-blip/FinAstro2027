"""Batch 1 -- the visibility families.

Seven catalogue-B sections: the five Combust Rise Cycles (Mars p.6, Mercury
p.10, Venus p.14, Jupiter p.20, Saturn p.24) and the two Mercury sections that
sit between them, Manifestation p.11 and Furthest from Sun p.12.

This is the batch with the strongest ground under it. Combustion is the one
convention Step 3 validated against *all* 23 of the source's combust and rise
dates, rejecting fixed ecliptic orbs (Mercury's events span 10.0-15.4 degrees)
and `swe.heliacal_ut` (Venus off by 9-10 days) before confirming classical
kalamsha. The rules below add no astronomy to that: they turn the emitted
endpoints into the windows the source's own verdicts are stated over.

Two decisions the batch forced, both recorded rather than smoothed over.

**The family is evaluated on the Mumbai civil day only.** Kalamsha is measured
at the primary location's horizon, and the astronomy layer emits these events as
`location: mumbai` records at `precision: date_only`. There is no instant to
convert, so a New York civil date could only be produced by picking one of the
two New York days the Mumbai day straddles. That would be invention, not
localisation, so `locations` is narrowed and the reason travels on every rule as
`combust_evaluated_mumbai_horizon_date_only`. The general per-location rule is
not being waived -- it is a rule about weekday, tithi and nakshatra conditions,
and this family has none.

**Two sections are blocked, and the blocking was checked rather than assumed.**
See each rule for the arithmetic.

**One rule fires on a reading that is partly ours.** B15 item c) elides a
nakshatra's second word; the elision was reported as `ambiguous`, ruled on as
Falguni, and carries `status="resolved_ambiguity"` with the evidence, the
rejected readings, and `nakshatra_name_elided_in_source` on every row. It is
never counted in with the executable rules.
"""
from __future__ import annotations

from ..sky import Span, flag, parse
from . import names
from .base import blocked, resolved, rule
from .catalogue import B, lettered, split_statement

#: Kalamsha is a horizon measurement at the primary location and the records are
#: date_only, so these rules key on the Mumbai civil day and say so.
MUMBAI_ONLY = ("mumbai",)
HORIZON_FLAG = "combust_evaluated_mumbai_horizon_date_only"


def _combust(body: str, direction: str | None = None):
    """Asta-to-udaya windows, optionally only those combust in one direction."""
    def fn(sky):
        spans = list(sky.combust_spans(body))
        if direction is not None:
            spans = [s for s in spans if s.value == direction]
        return spans
    return fn


def _rise(body: str, direction: str | None = None,
          nakshatras: tuple[str, ...] | None = None):
    """The rise (udaya) day itself, optionally filtered.

    The nakshatra is the one the rise record already carries, so a rise-in-star
    rule reads the astronomy layer rather than re-deriving the planet's position
    on the day.
    """
    def fn(sky):
        out = []
        for r in sky.class_records("combustion", family="visibility/rise",
                                   body=body):
            d = flag(r, "direction")
            nak = r["astronomy"]["nakshatra"]
            if direction is not None and d != direction:
                continue
            if nakshatras is not None and nak not in nakshatras:
                continue
            out.append(Span(parse(r["time"]["t_start_utc"]),
                            parse(r["time"]["t_end_utc"]),
                            {"direction": d, "nakshatra": nak}))
        return out
    return fn


# ------------------------------------------------------- B004  Mars p.6
# The section prints a cycle table and nothing else: no remark, no note, no
# inference. The rule therefore fires with no verdict, which is the correct
# port of a section that states none.
rule(
    id="b004_mars_combust_cycle",
    section=B(4),
    rule_family="visibility/combust",
    condition_text=B(4).title,
    condition_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "section_states_no_verdict"),
    notes="Mars combusts about once in two years; a year with no window is the "
          "normal case and not a porting failure.",
)(_combust("Mars"))


# ---------------------------------------------------- B009  Mercury p.10
# Also verdict-free. Its Combustion Type column (Vimishra, Ghora, Sankshipta,
# Tikshna, Prakrita) is a classification the source never defines and the
# astronomy layer does not carry, so it is not ported as a condition; the
# window is, and the type is left where the source put it.
rule(
    id="b009_mercury_combust_cycle",
    section=B(9),
    rule_family="visibility/combust",
    condition_text=B(9).title,
    condition_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "section_states_no_verdict",
           "combustion_type_column_not_ported"),
    notes="Combustion Type is printed per row and never defined; porting it "
          "would require the undocumented rule that assigns it.",
)(_combust("Mercury"))


# ----------------------------------------------------- B010  Mercury p.11
# BLOCKED. The section prints three bare dates and one sentence that is the
# only thing resembling a definition. That sentence makes the date depend on a
# SPEED COMPARISON, which the astronomy layer cannot supply: `speed_deg_day` is
# emitted on every record, but only at the instants of other events, so the
# crossing where Mercury overtakes Venus is not recoverable from it.
#
# Checked before blocking, so this is a measurement and not a shrug. The 2026
# dates are 10-Apr, 03-Aug and 14-Nov.
#   - not the East rise dates (14-Mar, 21-Jul, 10-Nov): offsets 27, 13, 4 days
#   - not the greatest-elongation Behind dates (04-Apr, 02-Aug, 21-Nov):
#     offsets +6, +1, -7 days
# Neither offset is constant, so Manifestation is not either event under a lag,
# and the speed crossing the sentence describes is what is left.
blocked(
    id="b010_mercury_manifestation",
    section=B(10),
    rule_family="visibility/manifestation",
    condition_text=B(10).paras[0],
    condition_from="para[0]",
    verdict_text=B(10).notes[0],
    verdict_from="note[0]",
    inputs=("visibility/combust",),
    missing_inputs=(
        "a continuous Mercury-vs-Venus speed comparison. speed_deg_day is "
        "emitted only at event instants, so the date Mercury attains higher "
        "speed than Venus is not derivable from the astronomy layer",
    ),
    locations=MUMBAI_ONLY,
    notes="Ruled out by arithmetic before blocking: the 2026 dates are neither "
          "the East rise dates nor the greatest-elongation dates under any "
          "constant lag (offsets 27/13/4 and +6/+1/-7 respectively).",
)


# ----------------------------------------------------- B011  Mercury p.12
# BLOCKED. Greatest elongation. `elongation` is emitted on every record, but a
# maximum cannot be read off a series sampled at other events' instants -- the
# samples are irregular and none of them is near the turning point by
# construction. Finding it needs a scan, which is new ephemeris work.
blocked(
    id="b011_mercury_furthest_from_sun",
    section=B(11),
    rule_family="visibility/max_elongation",
    condition_text=B(11).title,
    condition_from="title",
    verdict_text=B(11).remarks[0],
    verdict_from="remark[0]",
    inputs=("aspect/conjunction",),
    missing_inputs=(
        "a greatest-elongation event class. The astronomy layer emits "
        "elongation per record but never its extrema, and recovering a maximum "
        "from instants sampled at other events would be a scan, not a read",
    ),
    notes="The Ahead/Behind column is the same quantity's sign and would come "
          "free with the event class; it is not separately missing.",
)


# ------------------------------------------------------- B015  Venus p.14
# The richest of the five. One cycle table, one remark, and a note carrying
# three lettered rules -- four statements in one section, ported as four rules
# plus the bare cycle.
_V = lettered(B(15).notes[0])
_VA_COND, _VA_VERDICT = split_statement(_V["a"])
_VB_COND, _VB_VERDICT = split_statement(_V["b"])
_VC_COND, _VC_VERDICT = split_statement(_V["c"])
_VR_COND, _VR_VERDICT = split_statement(B(15).remarks[0])

rule(
    id="b015_venus_combust_cycle",
    section=B(15),
    rule_family="visibility/combust",
    condition_text=B(15).title,
    condition_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "section_states_no_verdict"),
    notes="The cycle itself carries no verdict. The section's four verdicts are "
          "each conditioned on a direction or a nakshatra and are separate "
          "rules below.",
)(_combust("Venus"))

rule(
    id="b015a_venus_combust_east",
    section=B(15),
    rule_family="visibility/combust",
    condition_text=_VA_COND,
    condition_from="note[0] item a)",
    verdict_text=_VA_VERDICT,
    verdict_from="note[0] item a)",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "verdict_segments_the_window"),
    notes="The verdict segments its own window -- fifteen days bearish, then "
          "bullish -- and is carried whole. Splitting the firing into two would "
          "author a boundary the source states in prose but never dates.",
)(_combust("Venus", direction="East"))

rule(
    id="b015b_venus_rise_west",
    section=B(15),
    rule_family="visibility/rise",
    condition_text=_VB_COND,
    condition_from="note[0] item b)",
    verdict_text=_VB_VERDICT,
    verdict_from="note[0] item b)",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
)(_rise("Venus", direction="West"))

rule(
    id="b015r_venus_rise_uttara_bhadrapada",
    section=B(15),
    rule_family="visibility/rise",
    condition_text=_VR_COND,
    condition_from="remark[0]",
    verdict_text=_VR_VERDICT,
    verdict_from="remark[0]",
    inputs=("visibility/combust", "ingress/nakshatra"),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="Names its star in full where item c) elides it, which is itself the "
          "third piece of evidence in c)'s resolution below.",
)(_rise("Venus", nakshatras=("Uttara Bhadrapada",)))


# ------------------------------------------------ B015 item c)  RESOLVED
# The one reading in this batch that is partly ours. "Purva" and "Uttra" are
# printed bare, and each is the first word of three nakshatras -- Falguni,
# Shada and Bhadrapad in the source's spellings -- so the pair admits nine
# readings. It was registered `ambiguous` and reported; the ruling came back
# Falguni, on the three pieces of evidence carried in `resolution` below, and
# it is recorded as `resolved_ambiguity` rather than promoted to `executable`.
# The distinction is the whole point: the dates it produces are as computable
# as any other rule's, and the word they turn on was supplied by an editor.
#
#: The list as the source prints it, with the elision made good. The left-hand
#: column is what is on the page and the right-hand column is what we supplied;
#: a `None` is a name that needed nothing. Written this way so the reconstruction
#: is visible at the point of use instead of hidden inside a resolved string.
_VC_STARS = (
    ("Purva", "Purva Falguni"),          # supplied
    ("Uttra", "Uttra Falguni"),          # supplied
    ("Ardra", None),
    ("Bharni", None),
    ("Rohini", None),
)
#: Engine names, via the one spelling bridge. Going through `names.nakshatra`
#: rather than typing "Purva Phalguni" here keeps the reconstruction a claim
#: about the SOURCE's vocabulary -- it asserts the supplied string is one the
#: document itself uses 24 and 34 times -- and it raises if it is not.
_VC_NAKSHATRAS = tuple(names.nakshatra(supplied or printed)
                       for printed, supplied in _VC_STARS)

resolved(
    id="b015c_venus_rise_star_list",
    section=B(15),
    rule_family="visibility/rise",
    condition_text=_VC_COND,
    condition_from="note[0] item c)",
    verdict_text=_VC_VERDICT,
    verdict_from="note[0] item c)",
    inputs=("visibility/combust", "ingress/nakshatra"),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "nakshatra_name_elided_in_source"),
    ambiguity=(
        '"Purva" and "Uttra" are printed bare. Each is the first word of three '
        "nakshatras -- Purva/Uttra Falguni, Purva/Uttra Shada and Purva/Uttra "
        "Bhadrapad in the source's own spellings -- giving nine readings of the "
        "pair. Ardra, Bharani and Rohini in the same list are unambiguous."
    ),
    resolution=(
        "The source elides these names nowhere else, so no abbreviation "
        "convention can be appealed to in either direction. Swept over the "
        "whole document: 90 occurrences of Purva and 98 of Uttra, of which "
        "exactly one each is bare -- both in this item. The rest are qualified "
        "(Purva Falguni 24, Uttra Falguni 34, Purva Shada 23, Uttra Shada 28, "
        "Purva Bhadrapad 39, Uttra Bhadrapad 32; the Bhadrapad totals include "
        "the Bhadrapada and Bhadrpad variants the spelling map already carries).",

        "A parallel rule in the same document resolves it. \"Moon rise in "
        "Ardra, Purva Falguni, Uttra Falguni - Bullish and 2.5 days Bullish in "
        "Chitra\" is the same author, a rising rule, and the same list head -- "
        "Ardra plus the Purva/Uttra pair -- with the pair written out as "
        "Falguni; it is the only line in the document carrying both Ardra and "
        "Falguni. Item c) is that set with Falguni elided and Bharni and "
        "Rohini appended. Catalogue B's own \"Jupiter in Magha, Purva Falguni, "
        "Uttra Falguni or Hasta\" pairs them a third time.",

        "The adjacent remark writes \"Uttra Bhadrapad\" in full two lines "
        "below, which cuts one way only: where the author means Bhadrapada he "
        "writes Bhadrapada. It is evidence about his habit, not about what he "
        "meant here.",
    ),
    rejected_readings=(
        "Purva Shada / Uttra Shada (Purva Ashadha / Uttara Ashadha) -- no "
        "parallel anywhere pairs the two Shadas as a rising list head.",
        "Purva Bhadrapad / Uttra Bhadrapad (Purva Bhadrapada / Uttara "
        "Bhadrapada) -- rejected despite being the neighbouring remark's star, "
        "and because of it: that remark spells it out.",
        "The seven mixed readings of the pair (Falguni with Shada, Shada with "
        "Bhadrapad, and so on) -- the parallel rules pair Purva with Uttra of "
        "the SAME name every time they pair them at all.",
    ),
    notes="Fires once in 2027, on Venus's 08-Sep rise in Uttara Phalguni. That "
          "row rests on an editorial reconstruction and says so: the elision "
          "is the author's and the missing word is ours. Anything downstream "
          "that presents it as a plain reading of the page is wrong, and "
          "`nakshatra_name_elided_in_source` travels on the firing so it "
          "cannot be presented that way by accident.",
)(_rise("Venus", nakshatras=_VC_NAKSHATRAS))


# ----------------------------------------------------- B022  Jupiter p.20
_J_COND, _J_VERDICT = split_statement(B(22).remarks[0])

rule(
    id="b022_jupiter_combust_cycle",
    section=B(22),
    rule_family="visibility/combust",
    condition_text=B(22).title,
    condition_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "section_states_no_verdict"),
    notes="The section's only verdict is qualified on the West direction and is "
          "the rule below; the cycle itself states none.",
)(_combust("Jupiter"))

rule(
    id="b022w_jupiter_combust_west",
    section=B(22),
    rule_family="visibility/combust",
    condition_text=_J_COND,
    condition_from="remark[0]",
    verdict_text=_J_VERDICT,
    verdict_from="remark[0]",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "verdict_segments_the_window"),
)(_combust("Jupiter", direction="West"))


# ------------------------------------------------------ B027  Saturn p.24
# The one section of the five whose verdict is unqualified: it is stated about
# the combustion, not about a direction, so the cycle rule carries it directly.
# The verdict names a sector rather than an instrument -- "sectors ruled by
# Saturn" -- which is the source's own map at work and is where CL's contested
# significator will attach. Nothing is resolved here; the text is carried whole.
rule(
    id="b027_saturn_combust_cycle",
    section=B(27),
    rule_family="visibility/combust",
    condition_text=B(27).title,
    condition_from="title",
    verdict_text=B(27).remarks[0],
    verdict_from="remark[0]",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "verdict_names_a_sector_not_an_instrument"),
    notes="'sectors ruled by Saturn' is the source's own sector map, which "
          "rulership.conflicts.crude_saturn_vs_rahu records as contested for "
          "crude. The text is carried; no significator is resolved here.",
)(_combust("Saturn"))
