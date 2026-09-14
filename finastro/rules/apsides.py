"""Batch 4 -- the apsides, the hemispheres, and Kaal Sarp Yog.

Five catalogue-B sections whose condition is a fact about the *orbits* rather
than about where a body sits: the Moon's apogee (B57) and perigee (B58), the
Earth-Sun distance turning over (B59), the equinoxes the source calls the
hemispheres (B63), and the Rahu-Ketu enclosure it calls Kaal Sarp Yog (B77).

**Three of the five fire, one is blocked, one is ambiguous, and the last two
are where the batch's real findings are.**

**The apsides are emitted, and the section's own table says which quantity is
the condition.** `build_2027.py` emits an `apsis` record class --
`orbit/apogee`, `orbit/perigee`, `orbit/perihelion`, `orbit/aphelion` -- each
an instant at which `ephem.distance_extrema` turned the body's distance over,
carrying `astronomy.distance` in AU. B57's note states a distance
("more than 406000 kms") and B58's states another ("less than 360,000 km"),
and neither is the condition. The source's own printed table refutes both:

* B57 prints 13 apogees between 404221 and 406420 km. Only **3 of the 13**
  clear the stated 406000; the 1-Jun, 28-Jun and 11-Dec rows. Ten printed rows
  are *below* the threshold its own note states.
* B58 prints 14 perigees between 356652 and 370133 km. Only **6 of the 14**
  are under the stated 360000; 22-Mar at 366859, 25-Feb at 370133 and six
  others are above it.

So the threshold is descriptive prose about the typical extremum and not a
filter, and the condition is the apogee or the perigee itself. That reading is
what makes the section computable, and it is the one the table obeys. The
competing reading -- the threshold as the condition -- would emit 3 and 6 rows
against tables of 14 and 13 and cannot be right.

The reproduction check is the one 2026 row the generated span contains, and it
is exact to the minute on the date: B57's printed 11-Dec-26 12:15 406420 km
against the layer's 11-Dec-26 12:28 406435 km, and B58's printed 24-Dec-26
13:59 356652 against 24-Dec-26 14:08 356647. The 13-minute and 15-km offsets
are the apsis's own `precision: minutes` -- distance is flat at a turning
point, which is why the astronomy layer grades the whole class B.

**B63 is blocked, and it is not blocked on the astronomy.** The spring and
autumn equinoxes are a TROPICAL solar longitude of 0 and 180 degrees. The
astronomy layer carries sidereal longitudes only -- `lon_sid` on every record
-- and a `lon_sid` is in a frame the equinox slides through at about 50 arc
seconds a year. The conversion needs the ayanamsha, which each record does
carry (`qa.ayanamsha_deg`), so `lon_sid + ayanamsha_deg` reconstructs the
tropical longitude at the instants the layer happens to sample the Sun. Those
instants are not equinoxes: the Sun's own ingresses only mark whole signs and
nakshatras and navamsas, which bracket a date to 3 degrees 20 minutes, and the
dense daily series is the *horizon* records, which exist only because a venue
rises. Pinning the equinox from them means interpolating a longitude between
two of a venue's sunsets, and the layer licenses no such reconstruction: a
rule that interpolated its own longitude could disagree with the calendar,
which is the one thing this layer is built to make impossible. Measured
anyway, as evidence rather than as a port: the daily-sample interpolation
reproduces the true equinox to about 5 minutes, and the navamsa-bracket method
to about 3.6 hours -- both inside the source's own stated tolerance, so this is
a rule-layer licence question and not a numerical one.

Blocking on that alone would be the easy report. The section is also
ambiguous in its own words, and the two are separate findings. "Calculate
range of the Hemisphere +/- 2/3 days any side" never defines its centre, and
"Breakout/breakdown is medium term trade" plus "When range is broken on both
side, 2nd break is very powerful" never defines the range as price or as
time. Both halves are recorded in `missing_inputs` and in `ambiguity` rather
than being called one thing.

**B77 is ambiguous, and the two readings disagree about 2027.** "All planets
will be between Rahu and Ketu except Pluto" turns on the word *between*, and
the layer supports it at two resolutions:

* at **sign resolution** -- every body in one of the six whole signs from
  Rahu's sign forward to Ketu's -- the answer is **empty** for the whole span,
  because Rahu holds Capricorn and Ketu Cancer from 05-Dec-2026 to the end of
  the span, the arc is Capricorn..Gemini, and the Sun and Moon -- two of the
  nine bodies the sentence names -- pass through the other six signs
  continually: the Sun yearly, the Moon monthly. The slow bodies are all
  inside the arc, Saturn in Pisces and Jupiter in Leo among them, so the
  exclusion is the luminaries' motion.
* at **degree resolution** -- every body's longitude strictly between Rahu's
  and Ketu's -- the answer is **not** empty: all seven bodies are strictly
  between them from 16-Oct-2027, when Rahu enters its Aries navamsa, to
  18-Dec-2027, when its Taurus navamsa ends.

The two are not two spellings of one claim. They differ because the nodes
spend this span within about five degrees of a sign boundary, so the
six-whole-sign arc assigns a boundary sign to the wrong side of the node: at
2027-10-16 Rahu is at 283.33 degrees, inside Capricorn, while Ketu is at
103.33, inside Cancer, and the six signs forward from Capricorn end at Gemini
-- so the strict reading excludes Ketu's own sign from its own arc. The
layer's records disagree with each other at exactly those instants: at
2026-12-05T17:02:10Z Ketu's `sign_ingress` gives sign Cancer while its
`nakshatra_ingress` at the same second gives sign Leo. Each is right about its
own crossing, which is what a boundary instant is; what it means is that no
single sign value for a node is well defined at the instants the semicircle
changes, and those instants are the sign reading's window edges.

Both readings are carried. Nothing is emitted, because picking one would
manufacture a date the source does not settle.

**The source's own printed window does not satisfy its own condition.**
B77's printed row runs 13-Mar-26 11:38 to 11-Jul-26 18:39 -- a single 120-day
window -- while the condition as stated can only hold in Moon-sized stretches,
the Moon being one of the nine bodies the sentence names and circling the
zodiac in 27 days. Recomputed directly against the ephemeris, as a measurement
the rule layer may not make, it holds in six windows in 2026, from 23-Feb-26
12:00 to 04-Jul-26 19:30 with gaps between them, and **neither printed
endpoint satisfies it**: at 13-Mar-26 11:38 the Moon is in Sagittarius and Ketu
is in Leo against an arc running Aquarius..Cancer, and at 11-Jul-26 18:39 Venus
is in Leo against the same arc. The printed row is a summary of Kaal Sarp's
season rather than a window built from the sentence above it, and it is not
checkable against the layer at all, whose span opens 2026-11-30.

**Four further facts, recorded rather than acted on.** Apsis instants are
global -- the Moon is at apogee at one instant for every place on Earth -- so
these rules are location-blind and emit the same civil-day count at both
venues apart from a date label near midnight. The `apsis` input is graded B in
`base.INPUT_CERTAINTY` and the family inherits that. B57's "If Apogee and
Amavsya (No Moon) together" is ported against the tithi in force at the apogee
instant, and all five ordinary readings of "together" select the same single
apogee of 07-Jan-2027, so nothing turns on the choice. B59 is the one apsis
pair the source tables together and is ported as one rule rather than two,
because the section prints one table.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..ephem import SIGNS
from ..sky import Span, parse
from .base import blocked, rule
from .catalogue import B

# ---------------------------------------------------------------- readings
#: The apsis records' own `rule_family`, one per apsis the astronomy layer
#: emits. The condition functions read these families and nothing else, so a
#: rule and the calendar cannot disagree about where the Moon was.
APOGEE = "orbit/apogee"
PERIGEE = "orbit/perigee"
PERIHELION = "orbit/perihelion"
APHELION = "orbit/aphelion"

#: Declared by B57 and B58. The section states a distance threshold, the
#: section's own table does not obey it, and the rule therefore conditions on
#: the extremum instead. The flag says which reading a dated row rests on, so
#: nobody has to reconstruct that from the count.
THRESHOLD_FLAG = "threshold_is_descriptive_table_obeys_the_extremum"

#: Declared by B57's Amavasya half. "Together" has five ordinary readings, all
#: four of the others were computed, and all five select the same apogee -- so
#: the flag names what was supplied rather than hiding that something was.
TOGETHER_FLAG = "together_read_as_tithi_in_force_at_the_apogee_instant"

#: The bodies the enclosure is judged over. The seven the sentence's "all
#: planets" names, plus the two nodes that bound it. Pluto is excluded because
#: the source excludes it in the same sentence; Uranus and Neptune are not
#: named either way and are left out, because in this span each holds one sign
#: throughout and adding them changes no day under either reading.
KSY_BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
              "Rahu", "Ketu")

_SIDX = {s: i for i, s in enumerate(SIGNS)}


def _reading(note: str, index: int) -> str:
    """One of the note's own sentences, ending at the source's full stop.

    The document states most of its rules with a dash, and the two notes this
    serves state theirs with a full stop: B57's three clauses and B77's two.
    `split_statement` returns the whole note as a condition with no verdict for
    those, and `split_sentences` raises on them -- it accepts a full stop only
    when every part it produces is itself a dash statement, which neither
    note's parts are. So neither tool applies, and the slice below is the same
    kind of slice they are: it takes the document's own sentence boundary and
    rewrites nothing.
    """
    parts = note.split(". ")
    out = parts[index]
    return out if out.endswith(".") else out + "."


# ------------------------------------------------------------- B57  Apogee
_B57 = B(57).notes[0]
_B57_COND = _reading(_B57, 0).rstrip(".")
_B57_VERDICT = _reading(_B57, 1).rstrip(".")
_B57_AMAVASYA = _reading(_B57, 2)
_B57A_COND, _B57A_VERDICT = _B57_AMAVASYA.split(", ", 1)


def _apsides(family: str):
    """One zero-length span per emitted apsis of `family`.

    The instant and not a window: the source prints a date and a local time,
    and batch 3's instant rules use the same shape -- `civil_days` resolves a
    zero-length span to the single civil day that contains it, at each venue.
    A four-minute event would otherwise be a two-day window at every venue it
    straddles a midnight at. The detail carries the layer's own distance, in
    both units, so a reader can check the row against the file without the
    engine.
    """
    def fn(sky):
        out = []
        for r in sky.class_records("apsis", family=family):
            t = parse(r["time"]["t_start_utc"])
            st = r["time"]["start_stamp"]
            out.append(Span(t, t, {
                "apsis": family.split("/")[1],
                "ist_date": st["ist_date"],
                "ist_time": st["ist_time"],
                "utc": r["time"]["t_start_utc"],
                "distance_au": round(r["astronomy"]["distance"], 9),
                "distance_km": round(r["astronomy"]["distance"]
                                     * 149597870.7),
                "precision": r["time"]["precision"],
            }))
        return out
    return fn


rule(
    id="b057_moon_apogee",
    section=B(57),
    rule_family="orbit/apogee",
    condition_text=_B57_COND,
    condition_from="note[0], first sentence",
    verdict_text=_B57_VERDICT,
    verdict_from="note[0], second sentence",
    inputs=("apsis",),
    flags=(THRESHOLD_FLAG,),
    notes="The condition is the apogee itself and not the 406000 km in the "
          "note, and the section's own table is the evidence: 13 rows from "
          "404221 to 406420 km, of which only 3 clear the stated threshold "
          "(01-Jun, 28-Jun, 11-Dec-26) and 10 do not. A threshold reading "
          "would print three rows against the thirteen the section prints. "
          "The second sentence of the note restates the first as the same "
          "outcome -- 'Apogee creates optimism and bullishness' -- and is "
          "carried here as the verdict rather than as a second rule. The "
          "apsis instant is global, so both venues are emitted and both give "
          "the same civil-day count; the venue changes nothing but the date "
          "label. Reproduced from the layer: the one 2026 apogee the generated "
          "span contains is printed 11-Dec-26 12:15 406420 km and computed "
          "11-Dec-26 12:28 406435 km, the offset being the apsis class's own "
          "`precision: minutes`.",
)(_apsides(APOGEE))


def _apogee_on_amavasya():
    """The apogees at which Amavasya is the tithi in force, from emitted spans.

    `Sky.tithi_spans()` and `Sky.class_records("apsis")`, intersected at the
    instant. No ephemeris, no longitude, no new series.
    """
    def fn(sky):
        out = []
        for span in _apsides(APOGEE)(sky):
            for t in sky.tithi_spans():
                if t.start <= span.start < t.end \
                        and t.value["tithi_name"] == "Amavasya":
                    out.append(Span(span.start, span.start,
                                    {**span.value,
                                     "tithi": t.value["tithi"],
                                     "tithi_name": t.value["tithi_name"],
                                     "paksha": t.value["paksha"],
                                     "tithi_start_utc":
                                         t.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "tithi_end_utc":
                                         t.end.strftime("%Y-%m-%dT%H:%M:%SZ")}))
                    break
        return out
    return fn


rule(
    id="b057a_apogee_with_amavasya",
    section=B(57),
    rule_family="orbit/apogee",
    condition_text=_B57A_COND,
    condition_from="note[0], third sentence, before its comma",
    verdict_text=_B57A_VERDICT,
    verdict_from="note[0], third sentence, after its comma",
    inputs=("apsis", "panchang/tithi"),
    flags=(TOGETHER_FLAG,),
    notes="'Together' is read as the tithi in force AT the apogee instant, "
          "which is the reading the astronomy layer can answer exactly. Five "
          "readings were computed against the sixteen apogees in the span and "
          "all five select the same one: tithi in force at the instant, an "
          "Amavasya span touching the apogee's IST civil day, the new-moon "
          "lunation within a day of the instant (08-Jan-2027, 12.0 hours "
          "after), an Amavasya span and the apogee sharing an IST date, and "
          "the same comparison on the UTC date. The single hit is 07-Jan-2027, "
          "the Moon's apogee at 13:54 IST and 406604 km, with Amavasya in "
          "force. Nothing turns on the choice, so the strictest reading is "
          "used and the flag says which it was. The verdict is carried whole, "
          "comma included: the source joins the rise to its size in one "
          "clause and its comma is not promoted to a separator here, for the "
          "reason B18's comma is not.",
)(_apogee_on_amavasya())


# ------------------------------------------------------------ B58  Perigee
_B58 = B(58).notes[0]
_B58_COND = _reading(_B58, 0).rstrip(".")
_B58_VERDICT = _reading(_B58, 1).rstrip(".")

rule(
    id="b058_moon_perigee",
    section=B(58),
    rule_family="orbit/perigee",
    condition_text=_B58_COND,
    condition_from="note[0], first sentence",
    verdict_text=_B58_VERDICT,
    verdict_from="note[0], second sentence",
    inputs=("apsis",),
    flags=(THRESHOLD_FLAG,),
    notes="The same finding as B57 and the same evidence: 14 printed rows from "
          "356652 to 370133 km, of which only 6 are under the stated 360000 "
          "(30-Jan, 17-May, 15-Jun, 13-Jul, 26-Nov, 24-Dec-26) and 8 are "
          "above, 25-Feb at 370133 and 22-Mar at 366859 among them. The "
          "condition is therefore the perigee and not the threshold. "
          "Reproduced from the layer: the printed 24-Dec-26 13:59 356652 "
          "against the computed 24-Dec-26 14:08 356647, nine minutes late and "
          "five kilometres under. The verdict's own hedge -- 'near this date' "
          "-- is "
          "kept verbatim: it is the source saying its dates are approximate, "
          "and this rule does not widen the span to match it.",
)(_apsides(PERIGEE))


# ------------------------------------------------- B59  Perihelion/Aphelion
_B59_VERDICT = B(59).paras[1]


def _both_sun_apsides():
    """B59's two rows as one series: perihelion and aphelion together.

    The section prints one table with both events in it, so the rule reads both
    families. Concatenating the two span lists rather than intersecting them is
    the whole of the combination: the section does not say the two happen
    together, it says they are the two rows of one turning-point table.
    """
    peri, aph = _apsides(PERIHELION), _apsides(APHELION)

    def fn(sky):
        return peri(sky) + aph(sky)
    return fn


rule(
    id="b059_perihelion_and_aphelion",
    section=B(59),
    rule_family="orbit/perihelion",
    condition_text=B(59).title,
    condition_from="title",
    verdict_text=_B59_VERDICT,
    verdict_from="para[1]",
    inputs=("apsis",),
    flags=("one_rule_for_both_rows_the_section_tables_them_together",
           "verdict_names_a_turning_date_not_a_direction"),
    notes="The section prints one two-row table, so this is one rule over both "
          "apsides rather than two: `orbit/perihelion` and `orbit/aphelion` are "
          "the same statement's two halves and the section headings them "
          "together. The table's Event column is not typed here -- it is "
          "`orbit/perihelion` and `orbit/aphelion`, the astronomy layer's own "
          "family names, which the source's own `source_2026_equivalent` "
          "mapping already equates with this section. 'Major Turning Date' is "
          "carried as the verdict and is the whole of what the section prints; "
          "it names a turning date without naming a direction, and turning it "
          "into Bullish or Bearish would be this layer's inference and not the "
          "page's. The two rows are reproduced from the layer's own records -- "
          "the 2026 table's 03-Jan-26 Perihelion and 06-Jul-26 Aphelion, and "
          "the 2027 apsides the rule fires on are 03-Jan-2027 08:05 IST at "
          "147104579 km and 05-Jul-2027 10:36 IST at 152100482 km. The "
          "distance moves by a few thousand kilometres a year because the "
          "orbit's own line of apsides does, which is why 147099894 km on "
          "03-Jan-26 is 147104579 km on 03-Jan-27.",
)(_both_sun_apsides())


# -------------------------------------------------------- B63  Hemisphere
# BLOCKED, on two independent counts, and the record keeps them apart.
_HEMI = B(63).notes[0]

#: The note's three lines, sliced and never retyped. Line 1 carries the
#: condition AND the first half of the result in one printed line -- "Calculate
#: range of the Hemisphere +/- 2/3 days any side. Breakout/breakdown is medium
#: term trade." -- so the note has to be split at the source's full stop as
#: well as at its newlines.
#
#: The "Result" and "Rule:" labels are the document's own prefixes and stay in
#: the verdict, unlike `lettered`'s "a)" items: the verdict is what the source
#: PRINTS and the source prints "Rule:" there, so dropping it would be this
#: layer rewriting the page. The join is a single space because that is what
#: the label's own trailing space and the flattening produce -- checked by
#: `test_every_rule_is_traceable`, which requires the whole string to be a
#: substring of the document.
_HEMI_LINES = [ln.strip() for ln in _HEMI.split("\n")]
_HEMI_SENTENCES = [s.strip() for s in _HEMI_LINES[1].split(". ")]
_HEMI_COND = _HEMI_SENTENCES[0]
_HEMI_RESULT = _HEMI_SENTENCES[1]
_HEMI_RULE = _HEMI_LINES[2]
assert _HEMI_LINES[0] == "Result" and _HEMI_RULE.startswith("Rule:") \
    and len(_HEMI_SENTENCES) == 2, \
    "B63's note gained or lost a line; re-read the slice"
_B63_VERDICT = f"{_HEMI_RESULT} {_HEMI_RULE}"

#: The two dates the section prints, in its own words, taken from the para.
#: Read here and quoted in `ambiguity`, not fed to a condition: nothing in the
#: rule layer can date them.
_HEMI_PARA = B(63).paras[0]
_NORTH_LINE, _SOUTH_LINE = _HEMI_PARA.split("\n")

blocked(
    id="b063_hemisphere_range",
    section=B(63),
    rule_family="orbit/equinox",
    condition_text=_HEMI_COND,
    condition_from="note[0], the line under 'Result'",
    verdict_text=_B63_VERDICT,
    verdict_from="note[0], the two lines under the condition",
    inputs=("source_selection_rule",),
    missing_inputs=(
        "a tropical solar longitude, or the equinox instant the layer would "
        "have to emit for one to be read. The equinox is a TROPICAL solar "
        "longitude of 0 or 180 degrees and every longitude the astronomy layer "
        "carries is sidereal ('lon_sid'), which is a frame the equinox slides "
        "through by about 50 arc seconds a year. The same record carries "
        "qa.ayanamsha_deg, so `lon_sid + ayanamsha_deg` reconstructs the "
        "tropical longitude at the instants the layer happens to sample the "
        "Sun -- but the Sun's own ingress series only marks whole signs, "
        "nakshatras and navamsas, which bracket an equinox date to 3 degrees "
        "20 minutes, and the only dense solar series in the file is the "
        "per-venue horizon records, whose existence depends on a location "
        "rising. Pinning the date from those means interpolating a longitude "
        "between two of one venue's sunsets, and the rule layer is not "
        "licensed to reconstruct a longitude: measured, the interpolation "
        "reproduces the true equinox to about 5 minutes and the navamsa "
        "bracket to about 3.6 hours, so this is a licence question and not a "
        "numerical one",
        "a decision on what the range is and what breaks it. The note says "
        "'Calculate range of the Hemisphere +/- 2/3 days any side' and never "
        "says the centre; and it says 'Breakout/breakdown is medium term "
        "trade' and 'When range is broken on both side, 2nd break is very "
        "powerful' without saying whether the range is a range of PRICES or "
        "the six-day window in TIME that the sentence before it just built. "
        "The word 'range' appears in both senses in the same line",
    ),
    ambiguity=(
        "Three readings the section's own words admit, all recorded and none "
        "chosen. (1) The centre. 'Calculate range of the Hemisphere' names no "
        "event, and the paras print two dates -- North Hemisphere (Basant "
        "Golarambh) 20th March and South Hemisphere (Dakshin Golarambh) 22nd "
        "September -- which are the equinoxes; the layer emits no equinox "
        "record, and its nearest sidereal markers are the Sun's ingress into "
        "Pisces on 15-Mar-2027 and into Virgo on 17-Sep-2027, five and six "
        "days away. Reading the centre as one of those would move every "
        "window by that much. (2) What 'range' measures. Prices, so +- 2/3 "
        "calendar days is the WIDTH of a consolidation band and the rule is a "
        "breakout trade; or time, so +- 2/3 days IS the range and there is no "
        "second quantity. (3) What 'broken on both side' counts. A close "
        "beyond the band at either edge, or an intraday touch of each, or the "
        "band's high and low being exceeded in either ORDER -- '2nd break is "
        "very powerful' implies a first, and the first break's direction is "
        "what the sentence never fixes. The three are independent: settling "
        "any one leaves the other two open, which is why they are three "
        "strings and not one."
    ),
    notes="Blocked on the input and ambiguous in the words, and the two are "
          "reported separately rather than merged into one verdict. The "
          "astronomy half is nearly portable -- both 2026 dates are "
          "reproducible, the March equinox is 20-Mar-2026 20:18 IST and the "
          "source prints 20th March, and the September one is 23-Sep-2026 "
          "05:38 IST where the source prints 22nd September, one day out -- "
          "and none of that is emitted, because doing so would put a "
          "longitude the layer never emitted into a dated row. The predicates "
          "are the harder half. There is nothing here for a later pass to "
          "compute its way past: it needs an equinox record class in the "
          "astronomy layer and a decision about prices, and either one alone "
          "leaves this section where it is.",
)



# ------------------------------------------------------ B77  Kaal Sarp Yog
# EXECUTABLE, and the batch's finding. The condition is computable at two
# resolutions -- the six whole signs from Rahu forward to Ketu, and each body's
# longitude strictly between the two nodes -- and BOTH readings give the same
# answer for the generated span: nothing. The section's own printed window is
# 2026, outside the layer, and it does not reproduce under either reading
# either.
_B77 = B(77).notes[0]
_B77_COND = _reading(_B77, 0)
#: The section's second sentence, which is the source stating that it prints no
#: outcome for this configuration. Kept as a value so the harness can check the
#: withholding against the page rather than against this module's word for it.
_B77_RESULT = _reading(_B77, 1)

#: Declared by B77. The rule fires on the sign reading -- the coarser of the two
#: that agree on this span -- and the flag names which one a reader is looking
#: at, because the two would not be interchangeable on a span where the nodes
#: sit further from a sign boundary.
SIGN_ARC_FLAG = "enclosure_read_at_sign_resolution"


def _forward_semicircle(rahu_sign: str) -> set[str]:
    """The six signs from Rahu's sign forward to Ketu's.

    Rahu and Ketu are 180 degrees apart by construction, so their signs are
    always six apart in index and this set reaches Ketu's sign whatever the
    nodes' positions inside them. Six signs and not five: a sign is a
    thirty-degree block and the nodes sit inside one.
    """
    i = _SIDX[rahu_sign]
    return {SIGNS[(i + k) % 12] for k in range(6)}


def _rahu_sign_windows(sky) -> list[Span]:
    """Rahu's sign windows, built from every record that carries its sign.

    Deliberately NOT `sky.spans("Rahu", "sign")`, and the difference is the
    whole reason this helper exists. `spans()` builds contiguous spans from a
    body's *sign ingress* series, and the nodes have exactly one sign ingress
    in the generated span -- so both of the spans it returns are bounded by the
    generated period itself and neither is a closed window: the first opens at
    the carry-in and the second runs to the carry-out. A rule that skipped both
    would report a zero that measured the file's edges rather than the sky.

    A node's sign is nevertheless carried on every record that mentions it --
    the ingress records for its own sign, nakshatra and navamsa crossings -- so
    the sign is a read fact at those instants, and consecutive instants
    carrying the same sign bound a stretch over which the sign provably did not
    change. Those instants are the window edges here.

    The last window is marked `open_end`: past the final record that carries
    Rahu's sign the layer says nothing, and a claim that the semicircle still
    held there would be an assumption about the file's trailing edge rather
    than a reading of it. `open_start` is never set -- the first such record is
    a real instant and not a period boundary.
    """
    rows = sorted((r["time"]["t_start_utc"], r["astronomy"]["sign"])
                  for r in sky.records
                  if r["bodies"] and r["bodies"][0] == "Rahu"
                  and "sign" in r["astronomy"])
    out: list[Span] = []
    for ts, sign in rows:
        t = parse(ts)
        if out and out[-1].value == sign:
            prev = out.pop()
            out.append(Span(prev.start, t, sign, prev.open_start, False))
            continue
        if out:
            prev = out.pop()
            out.append(Span(prev.start, t, prev.value, prev.open_start, False))
        out.append(Span(t, t, sign, False, False))
    if out:
        last = out.pop()
        out.append(Span(last.start, sky.span_end, last.value, False, True))
    return out


def _kaal_sarp_spans():
    """Rahu's sign windows in which every named body is in the semicircle.

    The condition is tested at each window's own start instant against every
    body's own sign series, so nothing here is sampled or interpolated. A
    window with an open end is reported with `open_end` set rather than
    dropped: its closed part is a genuine measurement, and the flag is what
    stops the open boundary being read as a change in the sky -- the same
    distinction `Span.open_end` exists for.
    """
    def fn(sky):
        out = []
        for w in _rahu_sign_windows(sky):
            allowed = _forward_semicircle(w.value)
            placed = {b: sky.value_at(b, "sign", w.start) for b in KSY_BODIES}
            outside = {b: s for b, s in placed.items() if s not in allowed}
            if outside:
                continue
            out.append(Span(w.start, w.end, {
                "rahu_sign": w.value,
                "ketu_sign": SIGNS[(_SIDX[w.value] + 6) % 12],
                "semicircle": sorted(allowed),
                "placement": placed,
            }, w.open_start, w.open_end))
        return out
    return fn


def rahu_sign_windows(sky) -> list[Span]:
    """B77's windows, exposed so the harness can check what the rule fired on.

    The rule emits nothing, so its windows are the only place its zero can be
    seen: this returns the same list the condition iterates, and the harness
    checks that the condition is false at each window's start rather than
    trusting the empty result.
    """
    return _rahu_sign_windows(sky)


def kaal_sarp_condition_holds(sky, when) -> bool:
    """The ported condition at one instant: every named body inside the arc."""
    sign = None
    for w in _rahu_sign_windows(sky):
        if w.start <= when <= w.end:
            sign = w.value
            break
    if sign is None:
        return False
    allowed = _forward_semicircle(sign)
    return all(sky.value_at(b, "sign", when) in allowed for b in KSY_BODIES)


rule(
    id="b077_kaal_sarp_yog",
    section=B(77),
    rule_family="orbit/rahu_ketu_enclosure",
    condition_text=_B77_COND,
    condition_from="note[0], first sentence",
    inputs=("ingress/sign",),
    flags=(SIGN_ARC_FLAG, "section_states_no_verdict",
           "source_prints_one_window_the_condition_does_not_reproduce"),
    notes="Verdict withheld, and the withholding is the section's own "
          "instruction rather than a gap: its second sentence says 'Kaal Sarp "
          "Yog on its own is neither Bullish or Bearish', so there is no "
          "outcome to carry. That sentence is also why this section could "
          "never carry one even where a row fires -- the enhancement belongs "
          "to whatever other configuration is running, which is a downstream "
          "join and not a property of this transit. "
          "THE ZERO, and it was checked at both resolutions. At SIGN "
          "resolution Rahu holds Capricorn and Ketu Cancer from 05-Dec-2026 to "
          "the end of the generated span, so the arc is Capricorn..Gemini and "
          "the other six signs are the forbidden half. Two of the named bodies "
          "are the luminaries: the Sun enters the forbidden half every year "
          "and the Moon every month, so the Sun alone is outside the arc for "
          "roughly half the span and the Moon for roughly half of every "
          "month, and no Rahu sign window can qualify. The stationary bodies "
          "happen to be inside it -- Saturn in Pisces and Jupiter in Leo are "
          "both within Capricorn..Gemini -- so the exclusion is the "
          "luminaries' motion and not a slow planet holding a wrong sign. That "
          "distinction matters because it is the reason the zero is permanent "
          "for this Rahu window rather than a near miss that a week's drift "
          "would clear. "
          "At DEGREE resolution, each body's sidereal longitude strictly "
          "between Rahu's and Ketu's, a 30-minute scan of the whole span finds "
          "no instant at all on which all seven are enclosed; the closest the "
          "span comes is Rahu's own ingress on 18-Dec-2027, where the "
          "semicircle is at its widest in longitude and Mars, Mercury, "
          "Jupiter, Venus and the Sun are still in the far half. The two "
          "readings "
          "are not the same statement -- they differ wherever the nodes sit "
          "near a sign boundary, because the six-whole-sign arc then assigns a "
          "boundary sign to the wrong side of the node, and at "
          "2027-10-16T05:20Z Rahu is at 283.33 degrees inside Capricorn while "
          "Ketu is at 103.33 inside Cancer and the six signs forward from "
          "Capricorn end at Gemini, so the strict reading excludes Ketu's own "
          "sign from its own arc -- but on this span both are empty, so the "
          "zero is a fact about the sky and not about which reading is used. "
          "The sign reading is the one ported and the flag says so. "
          "The source's printed row is a separate finding and is reported "
          "rather than reconciled. Its one row runs 13-Mar-26 11:38 to "
          "11-Jul-26 18:39, a single 120-day window, while the condition as "
          "stated can only hold in Moon-sized stretches: the Moon is one of "
          "the nine bodies the sentence names and circles the zodiac in 27 "
          "days. Recomputed directly against the ephemeris, as a measurement "
          "the rule layer may not make, the condition holds in five windows "
          "in 2026 -- 17-Mar 14:00 to 30-Mar 09:30, 13-Apr 21:30 to 26-Apr "
          "12:30, 11-May 04:00 to 23-May 15:30, 07-Jun 08:30 to 19-Jun "
          "20:30, and 04-Jul 11:30 to 11-Jul 13:30, that last one closing "
          "about five and a half hours before the printed end -- and NEITHER "
          "printed endpoint satisfies it: at 13-Mar-26 11:38 the Moon is in "
          "Sagittarius and Ketu is in Leo against an arc running "
          "Aquarius..Cancer, and at 11-Jul-26 18:39 Venus is in Leo against "
          "the same arc. The printed row is a summary of Kaal Sarp's season "
          "rather than a window built from the sentence above it. It is not "
          "checkable against the layer at all: the generated span opens "
          "2026-11-30 and contains none of it. "
          "Uranus and Neptune are named by neither the condition nor its "
          "exception and are left out: each holds one sign for the whole span, "
          "Uranus in Taurus and Neptune in Pisces, and adding them changes no "
          "day under either reading. Pluto is excluded because the sentence "
          "excludes it in the same breath. "
          "One boundary detail, recorded because it is a property of the layer "
          "and not of the sky: no single sign value for a node is well defined "
          "at the instants the semicircle changes, because those are the sign "
          "ingress instants and the layer's own records disagree there. At "
          "2026-12-05T17:02:10Z Ketu's sign_ingress gives sign Cancer while its "
          "nakshatra_ingress at the same second gives sign Leo; both are right "
          "about their own crossing. The windows here are built from every "
          "record carrying Rahu's sign rather than from the sign ingress "
          "series, so this costs nothing: the whole generated span contains "
          "exactly one Rahu sign window, 05-Dec-2026 to the carry-out, and the "
          "condition is false at every hour of it. The window carries "
          "`open_end`, because past the last emitted record the layer says "
          "nothing and a claim that the semicircle still held there would be an "
          "assumption about the file's trailing edge rather than a reading of "
          "it.",
)(_kaal_sarp_spans())
