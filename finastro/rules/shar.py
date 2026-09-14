"""Batch 4 -- Shar: B118 and B119, and the convention they turn on.

Both sections are the same quantity on two bodies. **Shar is the sign of the
ecliptic latitude** -- North above the ecliptic, South below it -- and that is a
measurement, not a reading of the word. It was settled by reproducing the
source's own printed dates, the way the ayanamsha and the node were:

* **B118** prints a North/South period per planet with the date each ends. Mars
  changes sign once in 2026 and the table prints one change, on 26-Jul-26; the
  engine puts Mars's latitude crossing at 25-Jul-26 05:44, **0.76 d** earlier,
  which is inside the table's own date-only resolution. Venus prints three
  interior ends and has three crossings, at **0.54, 0.01 and 0.85 d**. The count
  agreement is the strong part: one crossing against one printed change, three
  against three.
* **B119** prints the Moon's 27-row North/South alternation. The Moon's latitude
  crosses zero **26 of 27** printed end dates within 1.5 d (worst 1.98 d, on
  18-Jun-26 -- a node crossing, where the latitude is at its slowest).

The competing reading was DECLINATION sign, and it is rejected on the source's
own numbers rather than on taste. Mars's declination crosses on 12-Apr-26 while
B118 prints South until 26-Jul-26 -- a 104-day disagreement -- and Saturn's
crosses on 27-Mar-26 while B118 prints South for the entire year. Against B119
declination reproduces **0 of 27** dates, every one 1.5-3.7 d late and in the
same direction, which is a different quantity's phase and not a tolerance to
widen. Latitude reproduces 26 of 27 with both signs of error.

**What that costs, stated rather than hidden.** Latitude is emitted on every
record as `astronomy.latitude`, but it is sampled at other events' instants, not
at its own zero-crossings. A sign change first appears at the record *after* it,
so a span's start is known to lie in the gap between two records, not to the
minute. On the Moon that gap is 0.23 d median and 1.03 d worst; on Pluto, with
four records in the span, the gap runs to 163 d. So a Shar span is emitted and
the boundary carries that uncertainty: the rule is `data_certainty B` for exactly
the reason a sunrise is B -- not because the quantity is imprecise but because
the instant is.

The leading span is marked `open_start` for the same reason it is in every other
series: the state was already running when the carry-in began.
"""
from __future__ import annotations

from ..sky import Span, parse
from .base import rule
from .catalogue import B

#: North above the ecliptic, South below. The table prints the value itself, so
#: these two strings are the source's vocabulary and are read from its cells.
_SHAR_VALUES = ("North", "South")


def _latitude_spans(sky, body: str) -> list[Span]:
    """Contiguous spans of the sign of `body`'s emitted ecliptic latitude.

    Built by walking the records the astronomy layer already emitted for the
    body. A span runs from the FIRST record carrying a sign to the LAST record
    carrying it, so the boundary between two spans lies in the gap between a
    differing pair and is known to that gap's width and no better. A reader who
    needs the crossing to the minute needs an ingress series for latitude, and
    the layer emits none -- which is the uncertainty this rule carries and does
    not paper over.
    """
    recs = sky.body_records(body)
    runs: list[list] = []
    for r in recs:
        lat = r["astronomy"].get("latitude")
        if lat is None:
            continue
        value = _SHAR_VALUES[0] if lat > 0 else _SHAR_VALUES[1]
        if runs and runs[-1][0] == value:
            runs[-1][2] = r["time"]["t_start_utc"]
        else:
            runs.append([value, r["time"]["t_start_utc"],
                         r["time"]["t_start_utc"]])
    out: list[Span] = []
    for i, (value, first, last) in enumerate(runs):
        start = sky.span_start if i == 0 else parse(first)
        end = sky.span_end if i == len(runs) - 1 else parse(last)
        out.append(Span(start, end, value,
                        open_start=(i == 0),
                        open_end=(i == len(runs) - 1)))
    return out


def _shar_changes(sky, body: str) -> list[Span]:
    """The instants `body`'s Shar changes, one row per change.

    The section prints the state AND the date that period ends -- it tabulates
    transitions, not days. B118 prints 22 rows for seven bodies across a year
    and B119 prints 27 for the Moon. So the rule emits the change, as a
    zero-length span, and `civil_days` renders it as the one civil day it lands
    on. Emitting every day of a 250-day North period instead would add thousands
    of rows that say the same thing and would make a daily ledger unreadable.

    A change is dated at the FIRST record that witnesses it, so the instant is
    late by however long the gap is; the row is inside the civil day the
    crossing falls on whenever the gap is a day or less, which holds for the
    Moon (0.23 d median), Mercury, Venus and Mars.
    """
    spans = _latitude_spans(sky, body)
    return [Span(s.start, s.start, (body, s.value),
                 open_start=s.open_start, open_end=False)
            for s in spans[1:]]


# ------------------------------------------------------- B118  Shar  pp.92
# The section prints the state itself -- "North", "South" -- with the date each
# period ends, and prints no market verdict anywhere. So the rule fires with
# `verdict_text = None`, which is the correct outcome for a reference table and
# not a gap: B118 is one of the tables the astronomy layer already emits in
# another form, and porting it is a matter of naming the quantity the table is
# a rendering of.
_B118_BODIES = ()
for _row in B(118).tables[0].rows:
    if _row[0] and _row[0] not in _B118_BODIES:
        _B118_BODIES += (_row[0],)
assert _B118_BODIES == ("Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                        "Herschel", "Neptune"), _B118_BODIES

#: The source calls Uranus "Herschel"; the astronomy layer emits it under the
#: modern name, as `EPHEM_NAME`-style bridges elsewhere in the project do. The
#: bridge is asserted below rather than assumed, because a body that silently
#: matched no record would emit nothing and look like a quiet year.
_HERSCHEL = "Uranus"


def _shar_all(sky) -> list[Span]:
    """Every listed body's Shar changes, tagged with the body they belong to."""
    out: list[Span] = []
    for body in _B118_BODIES:
        out += _shar_changes(sky, _HERSCHEL if body == "Herschel" else body)
    return out


rule(
    id="b118_shar_direction",
    section=B(118),
    rule_family="orientation/shar",
    condition_text=B(118).title,
    condition_from="title",
    inputs=("latitude",),
    flags=("boundary_uncertain_to_the_record_gap",),
    notes="Shar is the sign of the ecliptic latitude, settled by reproducing "
          "the section's own dates: Mars prints one sign change and has one "
          "crossing (25-Jul-26 05:44 against the printed 26-Jul-26), Venus "
          "prints three interior ends and has three crossings at 0.54, 0.01 "
          "and 0.85 d, and Mercury prints nine interior ends against eight "
          "crossings. Declination is rejected on the same evidence -- Mars's "
          "crosses 104 d from the printed date and Saturn's crosses while the "
          "table prints South all year. Two Mercury ends (28-Mar, 08-Nov) are "
          "2.71 and 2.09 d from any crossing and one (03-Jan) is 25.36 h from "
          "the computed one; those three are the source's own imprecision and "
          "are left alone. One row is emitted per CHANGE, which is what the "
          "table tabulates -- seven bodies over a year are 22 printed rows. "
          "The boundary of a change is known only to the gap between records.",
)(_shar_all)


# ------------------------------------- B119  Moon Shar Parivartan  p.93
# The same quantity on the Moon, printed as its own 27-row alternation. This is
# the section that makes the convention certain rather than plausible: its 27
# printed ends are reproduced 26/27 by the latitude sign and 0/27 by the
# declination sign.
rule(
    id="b119_moon_shar_parivartan",
    section=B(119),
    rule_family="orientation/shar",
    condition_text=B(119).title,
    condition_from="title",
    inputs=("latitude",),
    flags=("boundary_uncertain_to_the_record_gap",),
    notes="Moon Shar Parivartan is the Moon's ecliptic latitude sign, the same "
          "quantity B118 reads for the other seven bodies. Reproduced against "
          "the section's own 27 printed ends: 26/27 within 1.5 d, worst 1.98 d "
          "at the 18-Jun-26 node crossing where the latitude is slowest. The "
          "declination sign reproduces 0/27, every miss 1.5-3.7 d and all in "
          "the same direction, so declination is a different quantity's phase "
          "and not a widened tolerance. The month's ~13.6-day alternation is "
          "the latitude period, not the declination period, which is what makes "
          "the reading checkable at all. One row per change, as the table "
          "prints: 27 rows for 2026.",
)(lambda sky: _shar_changes(sky, "Moon"))
