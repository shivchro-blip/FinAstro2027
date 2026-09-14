"""Batch 5 -- the Vedha family, ported for MERCURY ONLY.

One section is ported: **B133 Mercury Nakshtra Vedh**, with B122 (Mercury Speed
and Vedh) supplying the class it keys on. Everything else in this module is a
record of why it is not ported.

WHY MERCURY ALONE, and it is a structural reason and not a tolerance question.
Mercury's speed oscillates: over 2026 it crosses the calibrated level 1.744909
deg/day **six** times, so six independent printed boundaries constrain one
number. That is overdetermined, and it held. Mars and Venus each cross their
level exactly **once** in the year, so their calibrations solved one equation in
one unknown -- the feasible interval is just the speed's change across the +/-1
day scoring window, no other row in the year can falsify it, and the fit carries
no evidence. They are registered `blocked` with that as the named missing input.
See `build/STEP4_DECISIONS.md` section 12.10 for the arithmetic.

WHY JUPITER AND SATURN ARE NOT HERE EITHER, but for a different reason. They have
no level at all -- their two printed boundaries have no common threshold -- and
the source carries a dedicated doctrine for them instead: B30 "Demoted and Shadow
Speed of Saturn" p.26, which defines its interval by LONGITUDE (Saturn at
20 deg 31' of Pisces, crossed retrograde 27-Jul-2026 and direct again
15-Mar-2027) and supplies no speed level. So their missing input is a slow-planet
speed doctrine. B121/B124 (their speed tables) and B135/B136 (their vedha tables)
are registered `blocked` with that named.

THE DIRECTION RULE, and how much of it is ours. Fast/Atichari -> Left, Normal ->
Front, Retrograde -> Right. The honest domain-restricted figure is now **52 of
52** -- Mercury 45/45 and Jupiter 7/7, the two planets whose class does not rest
on a single-point fit. Mars 21/21 and Venus 30/30 are excluded from that figure
even though both score perfectly, because their classes were derived from
thresholds that fit by construction and so are not independent confirmations.
The overall label stays **correlation** while Saturn is unresolved. Carried as a
flag on every row rather than presented as law, because the rule is a regularity
of the tables and not a sentence the source states.

THE TARGETS ARE A TRANSCRIPTION. Each table's target column is a per-planet
lookup from the planet's OWN nakshatra to the vedha'd nakshatra, and no constant
offset reproduces any of them (within B132 the Left offset runs 1,3,5,7,9,11,13
in the 28-name scheme). So the wheels below are the source's own tables, dict
literals, with the section each came from. They are NOT derived, and a reader
should treat a change to one as a transcription edit requiring the same evidence
as any other verbatim string. The Mars and Venus wheels are kept even though
those ports are withdrawn, so that a later year supplying a second crossing can
be tested against them rather than re-transcribing them.

WHERE THE LOOKUP IS INCOMPLETE, THE RULE SAYS SO. A planet's table prints only
the nakshatras that planet occupied in 2026 -- Mars's covers 21 of them, Venus's
28, Mercury's 38. A 2027 residency in a key the table never printed has no
target, and those rows are emitted with `vedha_target = None` and a flag rather
than being filled in from another planet's wheel. That is a real gap in the
source and not one to paper over.
"""
from __future__ import annotations

import datetime as dt

from ..config import CONF
from ..sky import Span, parse
from .base import blocked, rule
from .catalogue import B

#: Direction carried by each class. The rule, as a mapping, so a row can name
#: the direction it used rather than leaving it implicit in the target.
DIRECTION = {"Atichari": "Left", "Fast": "Left", "Normal": "Front",
             "Retrograde": "Right"}

#: The class names a speed window can take in this layer, in the source's own
#: vocabulary. "Fast" and "Atichari" are the same class in two frames: the speed
#: table calls it Fast, the nakshatra table calls it Atichari.
FAST_NAMES = ("Fast", "Atichari")

# --------------------------------------------------------------- the wheels
# Transcribed from the source's own tables. Key: (own nakshatra, printed class)
# -> the nakshatra that planet vedhas, and which cell it came from.
#
# B132 Mars Nakshtra Vedh pp.107-108 -- 21 printed keys. NOT PORTED; kept as the
# transcription of record. See WITHDRAWN below.
#
# The class column of this table AGREES with the calibrated threshold on 20 of
# its 21 rows. The one disagreement is the row whose printed start is 15-Aug-26,
# the civil day on which the single crossing falls (15-Aug-26 00:05 IST), so the
# tables agree to a day and disagree only about which side of a boundary day a
# class belongs on. An earlier report in this project claimed all fifteen
# Atichari rows disagreed; that was wrong, and the per-row breakdown is in
# build/STEP4_DECISIONS.md section 12.10.
MARS_WHEEL = {
    ("Purva Ashadha", "Atichari"): "Uttara Bhadrapada",
    ("Uttara Ashadha", "Atichari"): "Purva Bhadrapada",
    ("Abhijeet", "Atichari"): "Shatabhisha",
    ("Shravana", "Atichari"): "Dhanishta",
    ("Dhanishta", "Atichari"): "Ashlesha",
    ("Shatabhisha", "Atichari"): "Pushya",
    ("Purva Bhadrapada", "Atichari"): "Punarvasu",
    ("Uttara Bhadrapada", "Atichari"): "Ardra",
    ("Revati", "Atichari"): "Mrigashira",
    ("Ashwini", "Atichari"): "Rohini",
    ("Bharani", "Atichari"): "Krittika",
    ("Krittika", "Atichari"): "Vishakha",
    ("Rohini", "Atichari"): "Swati",
    ("Mrigashira", "Atichari"): "Chitra",
    ("Ardra", "Atichari"): "Hasta",
    ("Ardra", "Normal"): "Purva Ashadha",
    ("Punarvasu", "Normal"): "Mula",
    ("Pushya", "Normal"): "Jyeshtha",
    ("Ashlesha", "Normal"): "Anuradha",
    ("Magha", "Normal"): "Bharani",
    ("Purva Phalguni", "Normal"): "Ashwini",
}

# B133 Mercury Nakshtra Vedh pp.109-111 -- 38 printed keys, the fullest in the
# document.
MERCURY_WHEEL = {
    ("Shravana", "Atichari"): "Dhanishta",
    ("Dhanishta", "Atichari"): "Ashlesha",
    ("Revati", "Atichari"): "Mrigashira",
    ("Ashwini", "Atichari"): "Rohini",
    ("Bharani", "Atichari"): "Krittika",
    ("Krittika", "Atichari"): "Vishakha",
    ("Rohini", "Atichari"): "Swati",
    ("Mrigashira", "Atichari"): "Chitra",
    ("Pushya", "Atichari"): "Purva Phalguni",
    ("Ashlesha", "Atichari"): "Magha",
    ("Magha", "Atichari"): "Shravana",
    ("Purva Phalguni", "Atichari"): "Abhijeet",
    ("Uttara Phalguni", "Atichari"): "Uttara Ashadha",
    ("Mula", "Normal"): "Punarvasu",
    ("Purva Ashadha", "Normal"): "Ardra",
    ("Uttara Ashadha", "Normal"): "Mrigashira",
    ("Abhijeet", "Normal"): "Rohini",
    ("Shravana", "Normal"): "Krittika",
    ("Dhanishta", "Normal"): "Ashlesha",
    ("Shatabhisha", "Normal"): "Swati",
    ("Purva Bhadrapada", "Normal"): "Chitra",
    ("Uttara Bhadrapada", "Normal"): "Hasta",
    ("Revati", "Normal"): "Uttara Phalguni",
    ("Ashwini", "Normal"): "Rohini",
    ("Bharani", "Normal"): "Krittika",
    ("Krittika", "Normal"): "Vishakha",
    ("Rohini", "Normal"): "Swati",
    ("Mrigashira", "Normal"): "Uttara Ashadha",
    ("Ardra", "Normal"): "Purva Ashadha",
    ("Punarvasu", "Normal"): "Mula",
    ("Pushya", "Normal"): "Jyeshtha",
    ("Ashlesha", "Normal"): "Anuradha",
    ("Magha", "Normal"): "Shravana",
    ("Purva Phalguni", "Normal"): "Abhijeet",
    ("Uttara Phalguni", "Normal"): "Revati",
    ("Hasta", "Normal"): "Uttara Bhadrapada",
    ("Chitra", "Normal"): "Purva Bhadrapada",
    ("Swati", "Normal"): "Shatabhisha",
    ("Vishakha", "Normal"): "Dhanishta",
    ("Anuradha", "Normal"): "Ashlesha",
    ("Jyeshtha", "Normal"): "Pushya",
    ("Punarvasu", "Retrograde"): "Purva Bhadrapada",
    ("Swati", "Retrograde"): "Rohini",
    ("Vishakha", "Retrograde"): "Krittika",
    ("Shatabhisha", "Retrograde"): "Abhijeet",
    ("Purva Bhadrapada", "Retrograde"): "Uttara Ashadha",
}

# B134 Venus Nakshtra Vedh pp.112-113 -- 28 printed keys.
VENUS_WHEEL = {
    ("Purva Ashadha", "Atichari"): "Uttara Bhadrapada",
    ("Uttara Ashadha", "Atichari"): "Purva Bhadrapada",
    ("Abhijeet", "Atichari"): "Shatabhisha",
    ("Shravana", "Atichari"): "Dhanishta",
    ("Dhanishta", "Atichari"): "Ashlesha",
    ("Shatabhisha", "Atichari"): "Pushya",
    ("Purva Bhadrapada", "Atichari"): "Punarvasu",
    ("Uttara Bhadrapada", "Atichari"): "Ardra",
    ("Revati", "Atichari"): "Mrigashira",
    ("Ashwini", "Atichari"): "Rohini",
    ("Bharani", "Atichari"): "Krittika",
    ("Bharani", "Normal"): "Magha",
    ("Krittika", "Normal"): "Shravana",
    ("Rohini", "Normal"): "Abhijeet",
    ("Mrigashira", "Normal"): "Uttara Ashadha",
    ("Ardra", "Normal"): "Purva Ashadha",
    ("Punarvasu", "Normal"): "Mula",
    ("Pushya", "Normal"): "Jyeshtha",
    ("Ashlesha", "Normal"): "Anuradha",
    ("Magha", "Normal"): "Bharani",
    ("Purva Phalguni", "Normal"): "Ashwini",
    ("Uttara Phalguni", "Normal"): "Revati",
    ("Hasta", "Normal"): "Uttara Bhadrapada",
    ("Chitra", "Normal"): "Purva Bhadrapada",
    ("Swati", "Normal"): "Shatabhisha",
    ("Vishakha", "Normal"): "Dhanishta",
    ("Chitra", "Retrograde"): "Mrigashira",
    ("Swati", "Retrograde"): "Rohini",
}

WHEELS = {"Mars": MARS_WHEEL, "Mercury": MERCURY_WHEEL, "Venus": VENUS_WHEEL}

#: The three calibrated planets, and the two sections each contributes. Only
#: Mercury is PORTED; Mars and Venus have their wheels transcribed here and their
#: ports withdrawn.
VEDHA_BODIES = ("Mars", "Mercury", "Venus")
PORTED_BODIES = ("Mercury",)
SPEED_TABLE = {"Mars": 120, "Mercury": 122, "Venus": 123}
NAK_TABLE = {"Mars": 132, "Mercury": 133, "Venus": 134}
NAK_TABLE_FOR = dict(NAK_TABLE)

#: The calibrated level for each body, read from config so the blocked reason can
#: be specific without a second copy of the number in prose.
CONF_THRESHOLD = {b: CONF["speed_classes"][b]["threshold"]
                  for b in VEDHA_BODIES}

#: Registered but deliberately unported. See the module docstring.
SLOW_BODIES = {"Jupiter": (121, 135), "Saturn": (124, 136)}


# ------------------------------------------------------------- the conditions

def _class_windows(sky, body: str):
    """Fast / Retrograde windows for `body`, read off the emitted series.

    Returns ``(fast, retro)``, each a list of (start, end). Both are built from
    `speed_crossing` records for Fast and `motion/station` records for
    Retrograde -- the astronomy layer's own output, so a rule here cannot
    disagree with the calendar about a planet's speed class.

    The two are kept separate rather than merged into one interval list because
    a Normal stretch is the GAP between them, and materialising gaps as spans
    would invent boundaries where the layer states none.
    """
    fast_recs = sky.class_records("speed_crossing")
    stations = sky.class_records("motion/station")
    fast, open_at = [], None
    for r in sorted(fast_recs, key=lambda x: x["time"]["t_start_utc"]):
        if body not in r["bodies"]:
            continue
        t = parse(r["time"]["t_start_utc"])
        if r["rule_family"] == "motion/fast_start":
            open_at = t
        elif r["rule_family"] == "motion/fast_end" and open_at is not None:
            fast.append((open_at, t))
            open_at = None
    if open_at is not None:
        fast.append((open_at, sky.span_end))
    retro, open_at = [], None
    for r in sorted(stations, key=lambda x: x["time"]["t_start_utc"]):
        if body not in r["bodies"]:
            continue
        t = parse(r["time"]["t_start_utc"])
        if r["rule_family"] == "motion/station_R":
            open_at = t
        elif r["rule_family"] == "motion/station_D" and open_at is not None:
            retro.append((open_at, t))
            open_at = None
    if open_at is not None:
        retro.append((open_at, sky.span_end))
    return fast, retro


def _class_at(fast, retro, t: dt.datetime) -> str:
    for a, b in retro:
        if a <= t < b:
            return "Retrograde"
    for a, b in fast:
        if a <= t < b:
            return "Atichari"
    return "Normal"


def _span_midpoint(s: Span) -> dt.datetime:
    return s.start + (s.end - s.start) / 2


# --------------------------------------------- B120/B122/B123  Speed and Vedh
def _speed_table(body: str):
    """One row per class change, carrying the class and its Vedha direction.

    The section tabulates the class AND the direction it implies, so this is the
    direction rule's own table and the place it is stated per planet.
    """
    def fn(sky):
        fast, retro = _class_windows(sky, body)
        out: list[Span] = []
        recs = sorted(
            [r for r in sky.class_records("speed_crossing")
             if body in r["bodies"]]
            + [r for r in sky.class_records("motion/station")
               if body in r["bodies"]],
            key=lambda x: x["time"]["t_start_utc"])
        for r in recs:
            t = parse(r["time"]["t_start_utc"])
            cls = _class_at(fast, retro, t)
            out.append(Span(t, t, {
                "class": cls,
                "direction": DIRECTION[cls],
                "at": r["time"]["start_stamp"]["ist_date"],
            }))
        return out
    return fn


# ------------------------------------- B132/B133/B134  Nakshtra Vedh
#: Plain dicts: (body, own nakshatra) -> the class the 2026 table printed for it.
#: A residency whose 2027 class differs has NO usable target, and the row says
#: so instead of borrowing another class's target.
PRINTED_CLASS = {
    body: {own: cls for (own, cls) in wheel}
    for body, wheel in WHEELS.items()
}


def _lookup(body: str, own: str, cls: str):
    """(target, note) for this residency, or (None, why not).

    A wheel entry is a row of the source's table, and a row belongs to the class
    its Speed column printed. Using an Atichari row's target for a residency the
    calibrated threshold calls Normal would be reading a cell the source did not
    fill for that case -- so the entry is refused rather than reused, and the
    refusal is reported.

    This matters in practice and is not defensive padding. Mars's table prints
    every one of its 21 rows with a class the calibrated threshold does NOT
    compute for that period (see the note on MARS_WHEEL), so most Mars rows land
    here; Mercury and Venus mostly agree, and their misses are the boundary
    days where a class flips.
    """
    wheel = WHEELS[body]
    target = wheel.get((own, cls))
    if target is not None:
        return target, None
    if cls in FAST_NAMES:
        target = wheel.get((own, "Atichari"))
        if target is not None:
            return target, None
    printed = PRINTED_CLASS[body].get(own)
    if printed is None:
        return None, "the_2026_table_never_printed_this_nakshatra"
    return None, (f"table_prints_{printed}_for_this_nakshatra_"
                  f"but_2027_class_is_{cls}")


def _nakshatra_vedha(body: str):
    """One row per residency, carrying the Vedha target for that residency.

    The target is a transcription of the section's own table, keyed on the
    planet's own nakshatra AND the class that residency is in. Where the table
    never printed the key -- or printed it under a different class -- the row
    carries no target and names the reason.

    ONE ROW PER RESIDENCY, not per day. The section tabulates residencies --
    B133 prints 45 rows for Mercury's 2026 -- so emitting every civil day of a
    thirteen-day residency would multiply its 45 rows by thirteen and say the
    same thing each time. The residency's start is emitted as a zero-length
    span, which `civil_days` resolves to the one day it lands on.
    """

    def fn(sky):
        fast, retro = _class_windows(sky, body)
        out: list[Span] = []
        for s in sky.spans(body, "nakshatra"):
            own = s.value
            cls = _class_at(fast, retro, _span_midpoint(s))
            target, why = _lookup(body, own, cls)
            out.append(Span(s.start, s.start, {
                "own_nakshatra": own,
                "class": cls,
                "direction": DIRECTION[cls],
                "vedha_target": target,
                "target_unavailable_because": why,
                "residency_ends_utc": s.end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "residency_open_end": s.open_end,
            }, open_start=s.open_start))
        return out
    return fn


# ------------------------------------------------------- PORTED: Mercury only
# The one planet whose threshold is overdetermined. Six crossings in 2026
# constrain one number, and it held.
for _body in PORTED_BODIES:
    rule(
        id=f"b{SPEED_TABLE[_body]:03d}_{_body.lower()}_speed_and_vedh",
        section=B(SPEED_TABLE[_body]),
        rule_family="vedha/speed_class",
        condition_text=B(SPEED_TABLE[_body]).title,
        condition_from="title",
        inputs=("motion/speed_crossing",),
        flags=("vedha_direction_is_a_correlation_52_of_52_in_honest_domain",
               "threshold_is_overdetermined_six_crossings_constrain_one_number"),
        notes=f"{_body}'s speed class over the span, with the Vedha direction "
              "the class carries. The class is read off the emitted "
              "speed_crossing and motion/station records, so this rule and the "
              "calendar cannot disagree about it. One row per class change, "
              "which is what the table tabulates: it prints date RANGES, and "
              "the ranges' edges are exactly these crossings. THIS IS THE ONLY "
              "PLANET THIS MODULE PORTS, because it is the only one whose "
              "threshold is overdetermined: Mercury crosses its level six times "
              "in 2026, so six independent printed boundaries constrain one "
              "number. Mars and Venus cross once each, so their calibrations "
              "solved one equation in one unknown and are not evidence.",
    )(_speed_table(_body))

    _b = NAK_TABLE[_body]
    rule(
        id=f"b{_b:03d}_{_body.lower()}_nakshatra_vedh",
        section=B(_b),
        rule_family="vedha/nakshatra",
        condition_text=B(_b).title,
        condition_from="title",
        inputs=("ingress/nakshatra", "motion/speed_crossing"),
        flags=("vedha_target_is_transcribed_from_the_2026_table",
               "vedha_direction_is_a_correlation_52_of_52_in_honest_domain",
               "threshold_is_overdetermined_six_crossings_constrain_one_number",
               "target_missing_where_the_2026_table_never_printed_the_key"),
        notes=f"{_body}'s nakshatra residencies with the nakshatra each one "
              "vedhas. The target comes from the section's own table, keyed on "
              "the residency's nakshatra and the class in force during it -- a "
              "lookup, not a formula, because no constant offset reproduces any "
              "table's cells (within B132 the Left offset runs "
              "1,3,5,7,9,11,13 in the 28-name scheme). A residency whose key the "
              "2026 table never printed carries vedha_target=None and names the "
              "reason rather than being filled in from another planet's wheel: "
              "the table covers 38 own-nakshatras, so a 2027 residency outside "
              "that set is a real gap in the source.",
    )(_nakshatra_vedha(_body))


# -------------------------------- Mars and Venus: WITHDRAWN, single-point fits
for _body, _sb in (("Mars", 120), ("Venus", 123)):
    _level = CONF_THRESHOLD[_body]
    blocked(
        id=f"b{_sb:03d}_{_body.lower()}_speed_and_vedh",
        section=B(_sb),
        rule_family="vedha/speed_class",
        condition_text=B(_sb).title,
        condition_from="title",
        inputs=("source_selection_rule",),
        missing_inputs=(
            f"a threshold constrained by more than one crossing. {_body}'s "
            f"speed crosses {_level} exactly ONCE in the whole of 2026, so the "
            "calibration solved one equation in one unknown: the feasible "
            "interval is just the speed's own change across the +/-1 day scoring "
            "window, and no other printed row in the year can falsify it. Zero "
            "degrees of freedom. The fit is therefore true by construction and "
            "carries no evidence, so the Vedha direction cannot be anchored to "
            "it. Mercury is the only inner planet whose level is overdetermined "
            "(six crossings); a later year supplying a second crossing for "
            f"{_body} would make this testable rather than re-derivable",
        ),
        flags=("withdrawn_single_point_fit_zero_degrees_of_freedom",
               "port_withdrawn_2026_09_14_not_a_tolerance_question"),
        notes=f"WITHDRAWN. {_body}'s threshold is recorded as a SINGLE-POINT FIT "
              "rather than as a calibration. It is not wrong -- it does "
              "reproduce the one printed boundary it was fitted to -- but it "
              "cannot be wrong either, and a number that cannot fail is not "
              "evidence. The wheel transcription is kept in this module so that "
              "a year supplying a second crossing can be tested against it "
              "rather than having to re-transcribe it.",
    )
    blocked(
        id=f"b{NAK_TABLE_FOR[_body]:03d}_{_body.lower()}_nakshatra_vedh",
        section=B(NAK_TABLE_FOR[_body]),
        rule_family="vedha/nakshatra",
        condition_text=B(NAK_TABLE_FOR[_body]).title,
        condition_from="title",
        inputs=("source_selection_rule",),
        missing_inputs=(
            f"a threshold constrained by more than one crossing. The class this "
            f"table keys on is {_body}'s speed class, and {_body}'s level was "
            "fitted to a single crossing, so the class it computes is not "
            "evidence. Withdrawing the wheel lookup follows from withdrawing the "
            "threshold: the target is transcribed correctly (96 of 96 printed "
            "rows resolve through the wheels) but the KEY is unearned",
        ),
        flags=("withdrawn_single_point_fit_zero_degrees_of_freedom",
               "port_withdrawn_2026_09_14_not_a_tolerance_question"),
        notes="The transcription itself is sound -- all 30 of Venus's and all 21 "
              "of Mars's printed rows resolve to their own target through the "
              "wheels kept above. What is withdrawn is the RIGHT TO KEY ON a "
              "class derived from a threshold that fit by construction.",
    )


# ------------------------------------------- Jupiter and Saturn: still blocked
for _body, (_sb, _nb) in SLOW_BODIES.items():
    blocked(
        id=f"b{_sb:03d}_{_body.lower()}_speed_and_vedh",
        section=B(_sb),
        rule_family="vedha/speed_class",
        condition_text=B(_sb).title,
        condition_from="title",
        inputs=("source_selection_rule",),
        missing_inputs=(
            f"a slow-planet speed doctrine. {_body}'s Fast and Normal "
            "boundaries have no common speed level -- the two printed "
            "boundaries are 0.013750 (" + ("Jupiter" if _body == "Jupiter"
                                            else "0.002594") + ") apart in "
            "threshold space. B30 'Demoted and Shadow Speed of Saturn' p.26 "
            "shows the slow planets answer to a different doctrine and defines "
            "its interval by LONGITUDE (Saturn at 20 deg 31' of Pisces, crossed "
            "retrograde 27-Jul-2026 and direct again 15-Mar-2027), supplying no "
            "speed level, so the class cannot be computed and the Vedha "
            "direction cannot be selected",
        ),
        flags=("blocked_on_slow_planet_speed_doctrine_not_on_a_failed_threshold",),
        notes="Registered for the same reason the calibration records it: the "
              "missing input is a doctrine, not a better number. 2027 also "
              "gives this body no calibrated threshold to read a class from, so "
              "a port would have to invent one.",
    )
    blocked(
        id=f"b{_nb:03d}_{_body.lower()}_nakshatra_vedh",
        section=B(_nb),
        rule_family="vedha/nakshatra",
        condition_text=B(_nb).title,
        condition_from="title",
        inputs=("source_selection_rule",),
        missing_inputs=(
            f"a slow-planet speed doctrine. This table keys its target on "
            f"{_body}'s speed class, and {_body} has no speed level at all -- "
            "its two printed boundaries share no threshold. B30 shows the slow "
            "planets answer to a longitude doctrine instead and supplies no "
            "speed level, so the class cannot be computed",
        ),
        flags=("blocked_on_slow_planet_speed_doctrine_not_on_a_failed_threshold",),
        notes="A separate block from the speed table's for the same section "
              "family, because a blocked threshold and a blocked key are two "
              "different gaps and collapsing them would hide one.",
    )
