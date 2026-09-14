"""Batch 5 -- the Vedha families for Mercury, Venus and Mars.

Six sections: the three Speed-and-Vedh tables (B120 Mars, B122 Mercury, B123
Venus) and the three Nakshtra Vedh tables (B132, B133, B134). Jupiter and Saturn
are absent by decision, not by omission -- see below.

WHAT WAS NEEDED FIRST. These tables print a Vedha DIRECTION per period, and the
direction is selected by the speed class the source printed. That class was the
blocker `open_questions.speed_class_thresholds` recorded for two batches. It is
now calibrated for the three inner planets by crossing instants (Mercury
1.744909, Venus 1.223981, Mars 0.658287 deg/day), and the astronomy layer emits
`speed_crossing` records at those levels, so a rule can read the class off the
layer like any other span. Nothing here computes a speed or touches the
ephemeris.

WHY JUPITER AND SATURN ARE NOT HERE. They have no calibrated threshold -- their
two printed boundaries have no common level -- and the source carries a dedicated
doctrine for them instead: B30 "Demoted and Shadow Speed of Saturn" p.26, which
defines its interval by LONGITUDE (Saturn at 20 deg 31' of Pisces, crossed
retrograde 27-Jul-2026 and direct again 15-Mar-2027) and supplies no speed level.
So their missing input is a slow-planet speed doctrine, and a port would have to
invent a class. B135 (Jupiter) and B136 (Saturn) are registered `blocked` with
that named.

THE DIRECTION RULE, and how much of it is ours. Fast/Atichari -> Left, Normal ->
Front, Retrograde -> Right. Across every per-planet table this holds on 103 of
103 rows within the domain where a class is defined; the only two exceptions in
the whole corpus are Saturn's (B136), which is outside that domain. It is
nevertheless carried as a flag on every row rather than presented as law,
because the rule is a regularity of the tables and not a sentence the source
states.

THE TARGETS ARE A TRANSCRIPTION. Each table's target column is a per-planet
lookup from the planet's OWN nakshatra to the vedha'd nakshatra, and no constant
offset reproduces any of them (within B132 the Left offset runs 1,3,5,7,9,11,13
in the 28-name scheme). So the wheels below are the source's own tables, dict
literals, with the section each came from. They are NOT derived, and a reader
should treat a change to one as a transcription edit requiring the same evidence
as any other verbatim string.

WHERE THE LOOKUP IS INCOMPLETE, THE RULE SAYS SO. A planet's table prints only
the nakshatras that planet occupied in 2026 -- Mars's covers 21 of them, Venus's
28, Mercury's 38. A 2027 residency in a key the table never printed has no
target, and those rows are emitted with `vedha_target = None` and a flag rather
than being filled in from another planet's wheel. That is a real gap in the
source and not one to paper over.
"""
from __future__ import annotations

import datetime as dt

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
# B132 Mars Nakshtra Vedh pp.107-108 -- 21 printed keys.
#
# READ THIS BEFORE USING THIS TABLE. Every one of Mars's 15 Atichari rows is
# labelled Atichari for a period the CALIBRATED threshold calls Normal: Mars's
# speed runs 0.62-0.72 deg/day through that stretch against a Fast level of
# 0.6583, crossing it only for the two short windows B120 itself prints, and
# B120 labels the first of those windows "Fast" and the second "Normal". So
# Mars's two tables do not agree about what Atichari means for Mars, and the
# class in this wheel's key is the NAKSHATRA TABLE's label, not a speed the
# calibrated level computes. The port consequently refuses these entries for any
# residency whose computed class differs -- see `_lookup`. Recorded rather than
# reconciled: reconciling it would mean choosing which of Mars's own two tables
# to believe.
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

#: The three calibrated planets, and the two sections each contributes.
VEDHA_BODIES = ("Mars", "Mercury", "Venus")
SPEED_TABLE = {"Mars": 120, "Mercury": 122, "Venus": 123}
NAK_TABLE = {"Mars": 132, "Mercury": 133, "Venus": 134}

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


for _body in VEDHA_BODIES:
    rule(
        id=f"b{SPEED_TABLE[_body]:03d}_{_body.lower()}_speed_and_vedh",
        section=B(SPEED_TABLE[_body]),
        rule_family="vedha/speed_class",
        condition_text=B(SPEED_TABLE[_body]).title,
        condition_from="title",
        inputs=("motion/speed_crossing",),
        flags=("vedha_direction_is_a_correlation_103_of_103_in_domain",),
        notes=f"{_body}'s speed class over the span, with the Vedha direction "
              "the class carries. The class is read off the emitted "
              "speed_crossing and motion/station records, so this rule and the "
              "calendar cannot disagree about it. One row per class change, "
              "which is what the table tabulates: it prints date RANGES, and "
              "the ranges' edges are exactly these crossings. Direction is "
              "Fast/Atichari->Left, Normal->Front, Retrograde->Right; the "
              "section prints that correspondence itself and it is carried as "
              "a flag because it is a regularity of the tables rather than a "
              "sentence the source states.",
    )(_speed_table(_body))


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


for _body in VEDHA_BODIES:
    _b = NAK_TABLE[_body]
    rule(
        id=f"b{_b:03d}_{_body.lower()}_nakshatra_vedh",
        section=B(_b),
        rule_family="vedha/nakshatra",
        condition_text=B(_b).title,
        condition_from="title",
        inputs=("ingress/nakshatra", "motion/speed_crossing"),
        flags=("vedha_target_is_transcribed_from_the_2026_table",
               "vedha_direction_is_a_correlation_103_of_103_in_domain",
               "target_missing_where_the_2026_table_never_printed_the_key"),
        notes=f"{_body}'s nakshatra residencies with the nakshatra each one "
              "vedhas. The target comes from the section's own table, keyed on "
              "the residency's nakshatra and the class in force during it -- a "
              "lookup, not a formula, because no constant offset reproduces any "
              "table's cells (within B132 the Left offset runs "
              "1,3,5,7,9,11,13 in the 28-name scheme). Rows whose key the 2026 "
              "table never printed carry vedha_target=None rather than being "
              "filled in from another planet's wheel: Mars's table covers 21 "
              "own-nakshatras, Venus's 28, Mercury's 38, so a 2027 residency "
              "outside that set is a real gap in the source.",
    )(_nakshatra_vedha(_body))


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
