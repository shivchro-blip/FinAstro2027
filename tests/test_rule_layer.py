"""Harness for the Step-4 rule layer.

These checks exist because a ported rule can fail in four ways that all look
like success from the outside:

* it can carry a condition or a verdict that is **not** what the source says --
  so every one is checked as a literal substring of data/source_2026.html;
* it can be **silently unattached** -- so every rule is checked to name a real
  catalogue-B section, and the catalogue is checked to be 141 sections;
* it can **never fire** and look like a rule that simply had a quiet year -- so
  the zero-firing set is pinned by name with its reason;
* it can **invent** -- so a rule with no printed verdict is checked to carry
  none, and the astronomy layer is re-checked to have taken no interpretation.

Run:  python tests/test_rule_layer.py      (after python build_2027.py)
"""
from __future__ import annotations

import ast
import collections
import datetime as dt
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from finastro import ephem                             # noqa: E402
from finastro import rules as R                        # noqa: E402
from finastro.config import CONF                       # noqa: E402
from finastro.ephem import NAKSHATRAS, SIGNS           # noqa: E402
from finastro.rules import (catalogue, colocation, names,  # noqa: E402
                            panchang_rules)
from finastro.rules import base as rules_base  # noqa: E402
from finastro.rules import config_catalogue, config_rules  # noqa: E402
from finastro.sky import Sky, civil_day_span, civil_days               # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_TEXT = (ROOT / "data" / "source_2026.html").read_text(encoding="utf-8")

Y = CONF["year"]
PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, PASS if ok else FAIL, detail))


def _flat(text: str) -> str:
    """Whitespace- and entity-insensitive view of a string or of the document.

    The catalogue decodes entities and collapses runs of spaces, so a literal
    `in` against the raw file fails for a string that spans a tag boundary.
    Flattening both sides keeps the check a substring test rather than
    weakening it to a fuzzy match.
    """
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text)))


SOURCE_FLAT = _flat(SOURCE_TEXT)

# -------------------------------------------------------------------------
# Rules whose 2027 firing count is deliberately zero, each with the reason the
# zero was checked to. A rule that stops firing for a DIFFERENT reason, or a new
# rule that never fires, fails here rather than passing unnoticed.
EXPECTED_ZERO_FIRING = {
    "b004_mars_combust_cycle":
        "Mars combusts about once in two years; its only window in the "
        "generated span opens 18-Jan-2028, outside calendar 2027",
    "b015r_venus_rise_uttara_bhadrapada":
        "Venus's single 2027 rise is 08-Sep in Uttara Phalguni, not Uttara "
        "Bhadrapada",

    # ---- batch 2. Three distinct kinds of zero, and the kind matters: an
    # aspect that happens in the carry-out is a calendar-boundary zero, an
    # aspect absent from the whole span is an orbital-period zero, and an
    # ordering that never occurs is a fact about the year.
    "b012_mars_mercury_conjunction":
        "both Mars-Mercury conjunctions in the generated span fall in the "
        "carry-out, 09-Jan and 27-Jan-2028, outside calendar 2027",
    "b053_pluto_conjunction_mars":
        "the single Mars-Pluto conjunction in the span is 11-Jan-2028, in the "
        "carry-out",
    "b041_herschel_conjunction_mars":
        "no Mars-Uranus conjunction occurs anywhere in the generated span",
    "b047_neptune_conjunction_mars":
        "no Mars-Neptune conjunction occurs anywhere in the generated span",
    "b047_neptune_conjunction_saturn":
        "no Saturn-Neptune conjunction occurs in the span at all -- the same "
        "absence that excludes the source's single highest label, per "
        "STEP4_DECISIONS section 8.9",
    "b054_pluto_opposition_jupiter":
        "no Jupiter-Pluto opposition occurs anywhere in the generated span",
    "b054_pluto_opposition_mars":
        "no Mars-Pluto opposition occurs anywhere in the generated span",
    "b085_mars_behind_jupiter_same_sign":
        "Mars is ahead of Jupiter throughout all three 2027 shared-sign "
        "windows with no tied stretch, so the 'behind' rule is correctly "
        "silent and b086 carries all 83 days",
    "b086x_mars_crosses_jupiter_eleven_days":
        "Mars and Jupiter share a sign three times in 2027 but never reach "
        "conjunction; the span carries no Mars-Jupiter conjunction record",
    "b087s_moon_rahu_same_nakshatra_rahu_in_shatabhisha":
        "the section states Bullish for the Rahu-in-Shatabhisha case only, and "
        "Rahu is never in Shatabhisha in 2027 -- Dhanishta to 10-Apr-2027, "
        "Shravana to 18-Dec, Uttara Ashadha after. The condition fires 28 "
        "times as b087 with the verdict withheld",
    "b112_venus_mercury_together_in_shravana":
        "Venus and Mercury share a nakshatra twelve times in 2027 and none of "
        "them is Shravana",

    # ---- batch 5, the pairs. Three zeros and three different kinds, which is
    # why they are pinned together: one is the orbital period, one is the
    # calendar boundary, and one is a fact about the sky that the section's own
    # 2026 row happens to sit on the other side of.
    "b083_mercury_venus_both_retrograde":
        "Venus does not station anywhere in the generated span -- her previous "
        "retrograde is 03-Oct-26 to 14-Nov-26 and the next is in 2028 -- so "
        "Mercury and Venus cannot be retrograde together in it. An "
        "orbital-period zero, the B041 shape",
    "b107_venus_alone_in_shravana":
        "Venus visits Shravana twice in 2027, 04-Mar to 16-Mar and 23-Dec to "
        "03-Jan-2028, and is alone there on neither visit: Pluto occupies "
        "Shravana from 28-Dec-2026 to the end of the generated span, and the "
        "source counts Pluto as a planet -- B116's own Planet-2 column names "
        "it. The section's 2026 row is that same fact read the other way round, "
        "Pluto not having reached Shravana yet",
    "b113_mars_in_dhanishta":
        "Mars reaches Dhanishta again on 25-Jan-2028, inside the carry-out and "
        "outside calendar 2027. A calendar-boundary zero, the B012 and B053 "
        "shape, and the rule fires on all 17 days of its 2026 window",

    # ---- batch 4c, B89's scoped verdict, the b087s shape exactly. The section
    # states Bullish for the Mars-in-Rohini case only, and 2027 puts Mars in
    # Chitra from 13-Aug to 03-Sep and never in Rohini, so the condition fires
    # 22 times on the Chitra window with the verdict withheld while this rule
    # stays silent. Its zero is a fact about the year, not a missing input.
    "b089s_mars_in_rohini":
        "the section states Bullish for the Mars-in-Rohini case only, and 2027 "
        "puts Mars in Chitra from 13-Aug to 03-Sep and never in Rohini. The "
        "bare condition fires 22 times with the verdict withheld (B087's "
        "handling), so the zero here is a fact about the year and not a "
        "blocked input",

    # ---- batch 6, the reference views. Four sections whose body moves too
    # slowly to cross the frame inside the span: each has exactly ONE crossing,
    # in DECEMBER 2026, so their 2027 tables carry no crossing rows at all. An
    # orbital-period zero, the b041/b083 shape -- and what separates it from a
    # porting error is that each still emits its carried-in row, so the zeros
    # are on CROSSINGS and the sections are not silent.
    "b031_reference_view_rahu":
        "Rahu's only sign ingress in the span is 05-Dec-2026 (into Capricorn), "
        "before calendar 2027. The section's 2027 content is the carried-in "
        "state alone",
    "b034_reference_view_ketu":
        "Ketu moves with Rahu; its only sign ingress in the span is also "
        "05-Dec-2026. The same orbital-period zero as B031",
    "b051_reference_view_pluto":
        "Pluto's only nakshatra ingress in the span is 28-Dec-2026 -- four "
        "records in the whole span, one crossing, none in 2027",
    "b052_reference_view_pluto":
        "Pluto's only navamsa ingress in the span is also 28-Dec-2026. The same "
        "orbital-period zero as B051",

    # ---- batch 4b, the apsides. One zero, and it is a fact about the SKY that
    # no reading of the section can get round: Kaal Sarp Yog needs every body
    # between Rahu and Ketu, and Saturn holds Pisces, outside Rahu's six-sign
    # arc, for the whole span.
    "b077_kaal_sarp_yog":
        "Rahu holds Capricorn and Ketu Cancer from 05-Dec-2026 to the end of "
        "the generated span, so the six-sign arc is Capricorn..Gemini, and "
        "Saturn is in Pisces throughout it -- outside the arc -- with the Moon "
        "outside it for most of every month. The zero is structural: one body "
        "holding one wrong sign, not a configuration that had a quiet year. It "
        "was checked at BOTH readings of 'between Rahu and Ketu' and the "
        "degree reading finds no enclosed instant either, so the zero is not an "
        "artefact of reading the enclosure at sign resolution. The source's own "
        "printed window is a 2026 one and is not checkable against the layer, "
        "which opens 2026-11-30",
}

#: Days inside a pair's shared-sign windows that the navamsa ladder cannot
#: order, per pair. Pinned because this is the number that measures the
#: method's blind spot, and a blind spot that grows must not read as an absence
#: of the configuration. Tolerance is one minute of a day.
EXPECTED_TIED_DAYS = {
    ("Venus", "Jupiter"): 2.691,
    ("Mars", "Jupiter"): 0.0,
}

#: Exact firing counts, Mumbai. Exact and not a range, for the same reason the
#: astronomy suite pins its populated counts: a family that quietly doubled or
#: halved would look plausible in a spot check.
EXPECTED_FIRINGS_MUMBAI = {
    "b009_mercury_combust_cycle": 144,
    "b015_venus_combust_cycle": 49,
    "b015a_venus_combust_east": 49,
    "b015b_venus_rise_west": 1,
    "b022_jupiter_combust_cycle": 26,
    "b022w_jupiter_combust_west": 26,
    "b027_saturn_combust_cycle": 35,
    # Resolved, not executable. Venus rises once in 2027, 08-Sep, in Uttara
    # Phalguni -- which is in c)'s list only under the Falguni reading. Under
    # either rejected reading this count is 0, so the number is the ruling's
    # footprint and moves if the ruling is ever revisited.
    "b015c_venus_rise_star_list": 1,

    # ------------------------------------------------------------- batch 2
    # Exact instants: one civil day each, except where the pair repeats.
    "b017_venus_mercury_conjunction": 3,
    "b041_herschel_conjunction_venus": 1,
    "b041_herschel_conjunction_mercury": 1,
    "b041_herschel_conjunction_sun": 1,
    "b042_herschel_opposition_sun": 1,
    "b042_herschel_opposition_mercury": 1,
    "b047_neptune_conjunction_venus": 1,
    "b047_neptune_conjunction_sun": 1,
    "b047_neptune_conjunction_mercury": 1,
    "b048_neptune_opposition_venus": 1,
    "b048_neptune_opposition_mercury": 1,
    "b048_neptune_opposition_sun": 1,
    "b053_pluto_conjunction_venus": 2,
    "b053_pluto_conjunction_mercury": 1,
    "b053_pluto_conjunction_sun": 1,
    "b054_pluto_opposition_venus": 1,
    "b054_pluto_opposition_sun": 1,
    "b054_pluto_opposition_mercury": 1,
    # Residency windows, in civil days touched.
    "b016_mercury_venus_alone_in_a_sign": 43,
    "b078_venus_jupiter_same_sign": 25,
    "b084_mars_jupiter_same_sign": 83,
    "b087_moon_rahu_same_nakshatra": 28,
    "b090_venus_mars_same_nakshatra": 31,
    "b093_moon_mars_same_sign": 42,
    # Ordering. b079 + b080 + the tied stretch must reconstruct b078, and
    # b086 must equal b084 exactly, both checked below as relations rather
    # than trusted as three independent constants.
    "b079_venus_behind_jupiter_same_sign": 9,
    "b080_venus_ahead_of_jupiter_same_sign": 14,
    "b086_mars_ahead_of_jupiter_same_sign": 83,
    "b018_sun_ahead_venus_behind_mercury_middle": 117,

    # ------------------------------------------------------------- batch 3
    # The lunar calendar. Counts are days touched, so a one-instant event is
    # one day and a window is as many days as it overlaps.
    "b060_amavasya": 13,
    "b061_purnima": 12,
    "b060t_amavasya_on_tuesday": 2,
    "b060s_amavasya_moon_in_sagittarius_or_pisces": 3,
    "b110_lunar_eclipse_on_tuesday": 1,
    # Moon windows. b055 is thirteen Panchaks of four and a half to five days;
    # b071 is thirteen two-day visits to one nakshatra.
    "b055_panchak": 74,
    "b071_moon_in_uttara_phalguni": 25,
    # The Moon's nakshatra on a named weekday. The Moon visits a nakshatra
    # about thirteen times a year and each visit touches two civil days, so
    # roughly 26/7 = 3.7 land on any one weekday; two to six is that spread.
    "b072_ashwini_on_tuesday": 3,
    "b097_moon_in_mrigashira_on_monday": 3,
    "b102_anuradha_on_sunday": 6,
    "b103_shatabhisha_on_tuesday": 5,
    "b104_mrigashira_on_thursday": 2,
    "b105_uttara_ashadha_on_monday": 3,

    # ------------------------- the tithi and yoga series, added after batch 3
    # Days touched, on the same convention as everything above. A tithi runs
    # about 23h40m, so it touches two civil days more often than one, and a
    # family occurring twelve or thirteen times a year shows about twice that
    # here. The weekday filter cuts it back to roughly a seventh per weekday
    # named.
    "b065_ekadashi_on_friday": 8,
    "b073_ashtami_on_tuesday_saturday": 18,
    "b074_ashtami_on_monday_thursday_friday": 18,
    "b075_chaturthi_shukla_paksha": 24,
    "b076_chaturthi_krishna_paksha": 24,
    "b095_shukla_pratipada_on_saturday_or_sunday": 7,
    "b096_vyatipata_yoga_on_tuesday_saturday_or_sunday": 11,
    "b100_shukla_shasthi_on_friday": 3,
    "b106_amavasya_ghadi_lesser_than_chaturdashi": 14,
    "b108_shukla_ekadashi_with_vyatipata_or_vaidhriti": 2,
    "b109_shukla_trayodashi_on_tuesday_or_saturday": 6,
    # Resolved, not executable: the Panchak half of its condition is b055's
    # supplied definition, so this count moves if that ruling is revisited.
    "b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak": 15,

    # ------------------------------ the horizon series and the weekday count
    # Six sections that batch 3 left blocked, and the counts say which kind of
    # thing each is. B64 fires once per Trayodashi and a Trayodashi is one
    # tithi per fortnight, so 25 is two per lunar month across a calendar year
    # -- and it is 25 rather than 50 because Pradosh is an INSTANT in this
    # rule, the sunset the tithi holds, so `civil_days` resolves it to one day
    # and not to every day the tithi touches.
    #
    # The Kshay and Vriddhi counts are days touched, like every tithi family
    # above. A Vriddhi tithi is longer than a civil day by definition and so
    # always touches two; a Kshay tithi holds no sunrise and so lies between
    # two of them, touching one day or two. That is why 12 rows of Vriddhi are
    # six occurrences while 18 of Kshay are more.
    #
    # B101 is 15 days per qualifying fortnight -- the first counted Saturday to
    # the last, inclusive, which is exactly the range its one printed row
    # gives -- and three such fortnights fall in Mumbai's 2027.
    "b064_pradosh": 25,
    "b066_kshay_tithi_shukla_paksha": 18,
    "b067_kshay_tithi_krishna_paksha": 16,
    "b068_vriddhi_tithi_shukla_paksha": 12,
    "b069_vriddhi_tithi_krishna_paksha": 12,
    "b101_three_saturdays_in_shukla_paksha": 45,

    # ------------------------------------------------------------- batch 4a
    # Shar, B118 and B119. ONE ROW PER CHANGE, which is what the sections
    # tabulate -- B118 prints 22 rows for seven bodies across a year and B119
    # prints 27 for the Moon -- so these counts are changes, not days touched,
    # and are the only counts in this table that are not. B118's twelve are the
    # sign changes of seven bodies in 2027: Jupiter, Saturn and Neptune hold one
    # sign all year; Uranus is absent from B118's list in 2026 and is listed as
    # Herschel, whose records the layer carries as Uranus.
    "b118_shar_direction": 12,
    "b119_moon_shar_parivartan": 27,

    # ------------------------------------------------------------- batch 4b
    # The apsides. An apsis is an INSTANT and not a window, so each record
    # resolves to one civil day per venue and these counts are occurrences,
    # not days touched: 13 apogees and 13 perigees fall in calendar 2027.
    # `b058` is 13 at both venues because a perigee near midnight may land on
    # the same date either side; `b057` is 13 in Mumbai and 14 in New York for
    # the same reason, which is why only the Mumbai column is pinned here.
    "b057_moon_apogee": 13,
    # The one apogee of 2027 at which Amavasya is the tithi in force, 07-Jan.
    # Every one of the five ordinary readings of "together" selects it.
    "b057a_apogee_with_amavasya": 1,
    "b058_moon_perigee": 13,
    # B59: 03-Jan-2027 perihelion and 05-Jul-2027 aphelion, one row each.
    "b059_perihelion_and_aphelion": 2,
    # Not here: `b077_kaal_sarp_yog` is executable and fires ZERO times, so its
    # zero is pinned by name in EXPECTED_ZERO_FIRING. That zero was checked at
    # BOTH readings of "between Rahu and Ketu" -- the ported six-sign reading
    # and the degree reading -- which
    # test_kaal_sarp_yog_is_empty_under_both_its_readings re-derives.

    # ------------------------------------------------------------- batch 5
    # The pairs. Two retrograde pairs and ten nakshatra-residency singles, in
    # days touched like everything above.
    #
    # `b081` is 22 days and `b082` 23, both from a single window per pair in
    # 2027 -- and neither is checked against its section's 2026 row here,
    # because B81's row is a defect: it prints VENUS's retrograde window. That
    # finding is recomputed from the ephemeris by
    # test_the_retrograde_pairs_reproduce_what_reproduces below.
    "b081_saturn_mercury_both_retrograde": 22,
    "b082_jupiter_mercury_both_retrograde": 23,
    # B88 is the Dhanishta half of B87's Moon-Rahu series: four windows in
    # 2027, and the series' fifth falls in the carry-in.
    "b088_moon_rahu_same_nakshatra_rahu_in_dhanishta": 8,
    # B91 is three Sun windows -- Uttara Ashadha, Ashwini and Chitra -- and
    # B92 one, so 43 against 14 is the shape of the two sections and not a
    # rounding.
    "b091_sun_in_uttara_ashadha_ashwini_or_chitra": 43,
    "b092_sun_in_krittika": 14,
    # Resolved, not executable: the yoga's definition is supplied, and its
    # footprint in 2027 is the Aquarius windows to 02-Jun and from 20-Oct plus
    # the Pisces ones in between, which is what the ruling buys.
    "b094_shani_chandra_dwidwadash_yog": 43,
    # B98 is Mercury's one 2027 visit to Mula, in December; B114's is its one
    # visit to Purva Bhadrapada, in March and April.
    "b098_mercury_in_mula": 9,
    "b114_mercury_in_purva_bhadrapada": 9,
    # B99 is the batch's long rule: Jupiter holds one of its four stars from
    # the year's opening to 24-Jan, again from 25-Jun, and continuously after
    # that -- 214 of 365 days, one row per day because the star-to-star
    # boundary days are joined. Hasta is not reached in 2027 at all.
    "b099_jupiter_in_magha_purva_phalguni_uttara_phalguni_or_hasta": 214,
    # B115 is the union its title states: the Sun's Shatabhisha window and
    # Venus's, which do not touch.
    "b115_sun_or_venus_in_shatabhisha": 26,
    # Not here: `b083`, `b107` and `b113` are executable and fire ZERO times,
    # each for a different reason, and all three are pinned by name in
    # EXPECTED_ZERO_FIRING above. `b117` is blocked.

    # ------------------------------------------------------------- batch 4c
    # B89, the colon-scoped pair owed from section 12.3 and delivered here. The
    # bare rule fires on the Chitra window 13-Aug to 03-Sep-2027 -- 22 civil
    # days across both venues -- and the Rohini-restricted verdict half is
    # silent, pinned by name in EXPECTED_ZERO_FIRING rather than left to read
    # as a quiet year.
    "b089_mars_in_rohini_or_chitra": 22,

    # ------------------------------------------------------------- batch 5
    # The Vedha family, MERCURY ONLY. Mercury is the one inner planet whose
    # threshold is overdetermined -- six crossings in 2026 constrain one number
    # -- so it is the only one whose class is evidence. Mars and Venus each
    # cross once, so their calibrations solved one equation in one unknown and
    # their ports are withdrawn; they are pinned in EXPECTED_ZERO_FIRING as
    # BLOCKED, not as zero-firing executables.
    #
    # The speed table is ONE ROW PER CLASS CHANGE and the nakshatra table ONE
    # ROW PER RESIDENCY, which is what each tabulates. A residency straddling
    # local midnight appears in both venue columns, which is this project's
    # convention everywhere and not a double count.
    "b122_mercury_speed_and_vedh": 4,
    "b133_mercury_nakshatra_vedh": 34,

    # ------------------------------------------------------------- batch 6
    # The 32 reference tables, each a view of an ingress series the astronomy
    # layer already emits. Counts are ROWS EMITTED, and the leading 1 everywhere
    # is the carried-in row the source's own tables open with ("Start of the
    # year"); a body that never crosses the frame inside the span would
    # otherwise render blank. The four at zero are pinned below.
    "b001_reference_view_sun": 12,
    "b003_reference_view_mars": 7,
    "b007_reference_view_mercury": 16,
    "b008_reference_view_mercury": 1,
    "b013_reference_view_venus": 15,
    "b014_reference_view_venus": 1,
    "b020_reference_view_jupiter": 3,
    "b021_reference_view_jupiter": 1,
    "b023_reference_view_jupiter": 4,
    "b024_reference_view_jupiter": 15,
    "b025_reference_view_saturn": 2,
    "b026_reference_view_saturn": 1,
    "b028_reference_view_saturn": 3,
    "b029_reference_view_saturn": 8,
    "b032_reference_view_rahu": 2,
    "b033_reference_view_rahu": 6,
    "b035_reference_view_ketu": 1,
    "b036_reference_view_ketu": 6,
    "b037_reference_view_herschel": 1,
    "b038_reference_view_herschel": 1,
    "b039_reference_view_herschel": 1,
    "b040_reference_view_herschel": 3,
    "b043_reference_view_neptune": 1,
    "b044_reference_view_neptune": 1,
    "b045_reference_view_neptune": 1,
    "b046_reference_view_neptune": 2,
    "b049_reference_view_pluto": 1,
    "b050_reference_view_pluto": 1,

    # B2: the Sun's nakshatra residencies, one row each, with the lord sliced
    # from this section's own table. 27 in Mumbai -- the Sun visits every
    # nakshatra once a year, so the count equals the 27-nakshatra scheme.
    "b002_sun_nakshatra_journey": 27,
}


# ---------------------------------------------------------- 1. the catalogue
def test_catalogue() -> None:
    conf_b = CONF["source_probability"]["transfer_test"]["catalogues"]["B"]
    record("Catalogue B is 141 sections and agrees with the config",
           len(catalogue.SECTIONS) == catalogue.CATALOGUE_B_SIZE
           == conf_b["count"] == 141,
           f"{len(catalogue.SECTIONS)} sections")

    record("Every section is numbered 1..141 with no gap and no repeat",
           [s.b for s in catalogue.SECTIONS] == list(range(1, 142)))

    bad = [s.b for s in catalogue.SECTIONS if _flat(s.title) not in SOURCE_FLAT]
    record("Every section title appears verbatim in the source document",
           not bad, str(bad))

    # The chapter bound matters: unbounded, the last section swallows the
    # monthly calendars. 87 tables under one heading is that bug's signature.
    worst = max(catalogue.SECTIONS, key=lambda s: len(s.tables))
    record("No section has run past its own end into the next chapter",
           len(worst.tables) <= 2,
           f"largest section is B{worst.b} with {len(worst.tables)} table(s)")


# ------------------------------------------------------- 2. rule provenance
def test_every_rule_is_traceable() -> None:
    reg = R.REGISTRY
    record("Rule ids are unique",
           len({r.id for r in reg}) == len(reg), f"{len(reg)} rules")

    record("Every rule names a catalogue-B section in range",
           all(1 <= r.catalogue_b <= 141 for r in reg))

    record("Every rule carries a family, a section title and a page",
           all(r.rule_family and r.section_title and r.section_page
               for r in reg))

    bad = [r.id for r in reg if _flat(r.condition_text) not in SOURCE_FLAT]
    record("Every condition text is verbatim from the source document",
           not bad, str(bad))

    bad = [r.id for r in reg
           if r.verdict_text and _flat(r.verdict_text) not in SOURCE_FLAT]
    record("Every verdict text is verbatim from the source document",
           not bad, str(bad))

    bad = [r.id for r in reg if r.verdict_text and not r.verdict_from]
    record("Every verdict names the element it was read out of",
           not bad, str(bad))

    # A proviso is a second string off the page, so it is checked the same way
    # the condition is. Gluing it onto condition_text would have made the pair
    # an authored sentence and this check unable to see it.
    bad = [r.id for r in reg
           if r.condition_proviso
           and _flat(r.condition_proviso) not in SOURCE_FLAT]
    record("Every proviso is verbatim from the source document",
           not bad, str(bad))

    bad = [r.id for r in reg if r.condition_proviso and not r.verdict_text]
    record("A proviso exists only where there is a verdict for it to restrict",
           not bad, str(bad))

    # C has two grounds with different remedies -- a missing rule and an
    # unevidenced parameter -- so a bare C would hide which applies. An
    # undocumented rule sends a reader to the page; an unevidenced parameter
    # sends them to another year, and there is nothing on the page to find.
    grounds = tuple(CONF["labels"]["data_certainty_grounds"])
    bare = [r.id for r in reg
            if r.data_certainty == "C" and r.certainty_ground not in grounds]
    record("Every C rule names which ground it sits on", not bare,
           str(bare) or f"{sum(1 for r in reg if r.data_certainty == 'C')} "
           f"C rules, grounds {list(grounds)}")
    stray = [r.id for r in reg
             if r.data_certainty != "C" and r.certainty_ground is not None]
    record("Only a C rule carries a ground", not stray,
           str(stray) or "A and B have nothing missing to name")


# ------------------------------------------------------------ 3. the axes
def test_axes_and_tier_derivation() -> None:
    vc = CONF["verdict_coverage"]
    record("verdict_coverage names the two axes as canonical",
           vc["axes"]["canonical"] is True
           and vc["axes"]["fields"] == ["evidence_source", "construction"],
           vc["status"])

    record("tier is recorded as derived, not as the model",
           vc["tier_derivation"]["status"] == "derived_convenience_mapping"
           and vc["emit"]["tier_is_derived"] is True)

    ok_src = set(vc["emit"]["evidence_source_values"])
    ok_con = set(vc["emit"]["construction_values"])
    bad = [r.id for r in R.REGISTRY
           if r.evidence_source not in ok_src or r.construction not in ok_con]
    record("Every rule's axis pair is inside the declared value sets",
           not bad, str(bad))

    # The config table and the code must agree, or the tier means two things.
    table = {}
    for row in vc["tier_derivation"]["rules"]:
        table[(row["evidence_source"], row["construction"],
               row.get("localized"))] = row["tier"]
    bad = []
    for r in R.REGISTRY:
        key = (r.evidence_source, r.construction)
        want = table.get(key + (False,), table.get(key + (None,), "<unmapped>"))
        if want != r.tier:
            bad.append((r.id, r.tier, want))
    record("Every rule's tier is what the config's derivation table gives",
           not bad, str(bad))

    pairs = collections.Counter((r.evidence_source, r.construction)
                                for r in R.REGISTRY)
    record("Condition-only sections emit the (source, null) pair and no tier",
           pairs[("source", None)] > 0
           and all(r.tier is None for r in R.REGISTRY
                   if r.construction is None),
           f"{pairs[('source', None)]} rules")


# ------------------------------------------------------------ 4. labels
def test_labels_are_from_the_config_vocabulary() -> None:
    tags = set(CONF["labels"]["claim_tag"])
    grades = set(CONF["labels"]["data_certainty"])

    bad = [r.id for r in R.REGISTRY
           if r.claim_tag is not None and r.claim_tag not in tags]
    record("Every claim_tag is one of the config's five", not bad, str(bad))

    bad = [r.id for r in R.REGISTRY if r.data_certainty not in grades]
    record("Every data_certainty is A, B or C", not bad, str(bad))

    bad = [r.id for r in R.REGISTRY
           if (r.claim_tag is None) != (r.verdict_text is None)]
    record("A claim_tag exists exactly where a verdict does", not bad, str(bad))

    record("No rule carries a confidence or a source_probability",
           not any(hasattr(r, "confidence") or hasattr(r, "source_probability")
                   for r in R.REGISTRY),
           "confidence stays untested and is raised only by a backtest")


# ------------------------------------------ 4b. the label attaches per RULE
#: Every rule that carries a source label, the labels it carries, and the number
#: of verdict rows behind it. PINNED PER RULE, and that is the whole point of
#: the check: the label used to attach by SECTION TITLE, and a per-family or
#: per-total count passes either way. The broken build carried 536 rows to this
#: one's 533 -- three rows apart on a 6,677-row calendar -- so only this table
#: separates a correct attachment from one that labelled a rule's neighbours.
#:
#: Read against build_verdicts(), not against the registry: the defect was in
#: what reached a ROW, and b015r_venus_rise_uttara_bhadrapada carries the label
#: while firing zero times, so a registry-level check would not see the rows at
#: all.
SOURCE_PROBABILITY_ROWS = {
    "b015_venus_combust_cycle":                 (("Reasonable",), 98),
    "b015a_venus_combust_east":                 (("Reasonable",), 98),
    # The two that name the defect. Both are rise rules sitting in
    # combust_venus's section, and both used to read Reasonable.
    "b015b_venus_rise_west":                    (("High",), 2),
    "b015c_venus_rise_star_list":               (("High",), 2),
    "b016_mercury_venus_alone_in_a_sign":       (("Reasonable", "High"), 86),
    "b017_venus_mercury_conjunction":           (("Reasonable", "High"), 6),
    "b022_jupiter_combust_cycle":               (("Good",), 26),
    "b022w_jupiter_combust_west":               (("Good",), 26),
    "b027_saturn_combust_cycle":                (("High",), 35),
    # One Herschel partner, not three. Block 23 labels the Venus one.
    "b041_herschel_conjunction_venus":          (("High",), 1),
    "b078_venus_jupiter_same_sign":             (("High",), 50),
    "b086_mars_ahead_of_jupiter_same_sign":     (("High",), 83),
    "cfg_gold_bullish_03_rahu_mars_same_sign":  (("Reasonable",), 10),
    "cfg_silver_bullish_07_rahu_mars_same_sign": (("Reasonable",), 10),
}

#: Rules that share a section with a labelled rule and carry NO label. This is
#: the negative half and it is the half that bites: on the broken build every
#: one of these was labelled, because its section-mate was.
SECTION_MATES_WITHOUT_A_LABEL = [
    "b041_herschel_conjunction_sun",
    "b041_herschel_conjunction_mercury",
    "b041_herschel_conjunction_mars",
    "b086x_mars_crosses_jupiter_eleven_days",
]


def test_source_probability_attaches_per_rule_and_not_per_section() -> None:
    from finastro.verdicts import build_verdicts, probability_for

    conf = CONF["source_probability"]
    known = {r.id for r in R.REGISTRY} | {r.id for r in config_rules.CONFIG_REGISTRY}

    claimed: dict[str, str] = {}
    duplicated, unknown = [], []
    for fam in conf["carried_families"]:
        for rid in fam.get("rules") or ():
            if rid in claimed:
                duplicated.append(f"{rid} in {claimed[rid]} and {fam['id']}")
            claimed[rid] = fam["id"]
            if rid not in known:
                unknown.append(rid)
        for rid in (fam.get("rules_declined") or {}):
            if rid not in known:
                unknown.append(rid)

    record("Every rule id the label config names is a registered rule",
           not unknown, str(unknown))
    record("No rule id is claimed by two carried families",
           not duplicated, str(duplicated))

    # A family may legitimately reach no rule -- conj_sun_mercury is catalogue A
    # only -- but it has to SAY so rather than simply carry an empty list.
    silent = [fam["id"] for fam in conf["carried_families"]
              if not fam.get("rules") and not fam.get("rules_empty_is_correct")]
    record("A family that attaches to no rule records why", not silent, str(silent))

    verdicts = build_verdicts()
    got: dict[str, tuple] = {}
    for v in verdicts:
        if not v.source_probability:
            continue
        prev = got.get(v.rule_id)
        got[v.rule_id] = (tuple(v.source_probability),
                          (prev[1] if prev else 0) + 1)

    drift = ["; ".join(f"{k} {got.get(k)} != {want}"
                       for k, want in SOURCE_PROBABILITY_ROWS.items()
                       if got.get(k) != want)]
    drift += [f"unexpected {k} {v}" for k, v in got.items()
              if k not in SOURCE_PROBABILITY_ROWS]
    record("Each labelled rule carries exactly the labels and the row count "
           "pinned above -- per RULE, which a per-section attachment fails",
           got == SOURCE_PROBABILITY_ROWS,
           f"{len(got)} rules, {sum(n for _, n in got.values())} rows. "
           + " ".join(x for x in drift if x))

    by_id = {r.id: r for r in R.REGISTRY}
    by_id.update({r.id: r for r in config_rules.CONFIG_REGISTRY})
    leaked = [rid for rid in SECTION_MATES_WITHOUT_A_LABEL
              if probability_for(by_id[rid])[0] is not None]
    record("A rule sharing a section with a labelled rule carries no label",
           not leaked, str(leaked))

    # The section-mates are only evidence if they really do share the section.
    labelled_titles = {by_id[o].section.title for o in SOURCE_PROBABILITY_ROWS}
    stray = [rid for rid in SECTION_MATES_WITHOUT_A_LABEL
             if by_id[rid].section.title not in labelled_titles]
    record("...and each of those rules really is in a labelled rule's section",
           not stray, str(stray))

    # Carried but silent: b015r is one of rise_venus's three rules and fires
    # zero times in 2027, so it reaches no row. The attachment is a property of
    # the RULE and has to hold whether or not the sky obliges -- which is also
    # why the pinned table above cannot be the only check.
    labels, _ = probability_for(by_id["b015r_venus_rise_uttara_bhadrapada"])
    record("A labelled rule that fires zero times still carries its label",
           labels == ["High"]
           and not any(v.rule_id == "b015r_venus_rise_uttara_bhadrapada"
                       for v in verdicts),
           f"b015r carries {labels} behind 0 rows")

    disputed = {rid for rid, (labs, _) in SOURCE_PROBABILITY_ROWS.items()
                if len(labs) > 1}
    record("A disputed family emits the SET and flags it, and no other row is "
           "flagged disputed",
           {v.rule_id for v in verdicts if v.source_probability_disputed} == disputed,
           str(sorted(disputed)))


# ---------------------------------------------------- 5. blocked / ambiguous
def test_blocked_and_ambiguous(firings: list) -> None:
    fired = {f.rule_id for f in firings}

    blocked = R.by_status(R.STATUS_BLOCKED)
    record("Every blocked rule names the input it is missing",
           all(r.missing_inputs for r in blocked),
           f"{len(blocked)} blocked")
    record("No blocked rule emits a firing",
           not any(r.id in fired for r in blocked))

    amb = R.by_status(R.STATUS_AMBIGUOUS)
    record("Every ambiguous rule states the competing readings",
           all(r.ambiguity for r in amb), f"{len(amb)} ambiguous")
    record("No ambiguous rule emits a firing",
           not any(r.id in fired for r in amb),
           "an unresolved reading must not silently pick one")


def test_resolved_ambiguities_are_marked_as_reconstructions(firings: list):
    """A resolved rule's rows must be impossible to mistake for the page.

    It fires like any other rule, which is exactly the risk: nothing about a
    dated row says that a word in its condition was supplied by an editor
    unless the row itself carries it. So four things are checked -- the readings
    it was chosen against, the evidence that chose it, the readings the evidence
    rejected, and the flag, on the rule AND on every firing it produces.
    """
    res = R.resolved_ambiguities()
    record("Resolved rules are reported apart from the executable ones",
           not (set(res) & set(R.executable())),
           f"{len(res)} resolved, {len(R.executable())} executable")

    record("Every resolved rule states the readings it resolved",
           all(r.ambiguity for r in res), str([r.id for r in res
                                               if not r.ambiguity]))
    record("Every resolved rule carries the evidence that resolved it",
           all(len(r.resolution) >= 1 for r in res),
           str([(r.id, len(r.resolution)) for r in res]))
    record("Every resolved rule names the readings it rejected",
           all(r.rejected_readings for r in res),
           str([(r.id, len(r.rejected_readings)) for r in res]))

    # The flag has to reach the row, not just the registry. A row travels
    # further than the registry does.
    by_id = {r.id: r for r in res}
    bad = [f.rule_id for f in firings
           if f.rule_id in by_id
           and set(by_id[f.rule_id].flags) - set(f.flags)]
    record("Every firing of a resolved rule carries its rule's flags",
           not bad, str(sorted(set(bad))))

    elided = [r.id for r in res
              if "nakshatra_name_elided_in_source" in r.flags]
    rows = [f for f in firings if f.rule_id in set(elided)]
    record("Every row resting on a supplied nakshatra name says so",
           bool(rows) and all("nakshatra_name_elided_in_source" in f.flags
                              for f in rows),
           f"{len(rows)} row(s): "
           + ", ".join(f"{f.rule_id} {f.civil_date:%d-%b-%Y}" for f in rows))

    # And the evidence must be checkable: every quotation inside it that is
    # presented as the document's words has to be the document's words.
    quoted = [
        "Moon rise in Ardra, Purva Falguni, Uttra Falguni - Bullish and 2.5 "
        "days Bullish in Chitra",
        "Jupiter in Magha, Purva Falguni, Uttra Falguni or Hasta",
        "Uttra Bhadrapad",
    ]
    missing = [q for q in quoted if _flat(q) not in SOURCE_FLAT]
    record("Every passage quoted in a resolution is verbatim from the source",
           not missing, str(missing))


def test_the_elision_occurs_exactly_once_in_the_document():
    """`Purva` and `Uttra` are bare in B15(c) and nowhere else. Locked.

    This is the sweep the ruling rests on, kept as a check rather than as a
    number in a comment. If a later batch meets a second bare instance -- in
    catalogue B or anywhere else in the document -- it must be ruled on the same
    way and not quietly absorbed into an existing reading, and this fails until
    it is.
    """
    qualifiers = ("Shada", "Bhadrapad", "Bhadrapada", "Bhadrpad", "Falguni")
    bare = []
    for m in re.finditer(r"\b(Purva|Uttra)\b[ \n]*([A-Za-z]*)", SOURCE_FLAT):
        if m.group(2) not in qualifiers:
            bare.append((m.group(1), m.start()))

    record("Purva and Uttra are printed bare exactly twice in the document",
           len(bare) == 2 and {w for w, _ in bare} == {"Purva", "Uttra"},
           f"{len(bare)} bare: {[w for w, _ in bare]}")

    # Both must be inside B15, the section that was ruled on. The check is by
    # containment rather than by offset, so it survives a reflow of the file.
    b15 = catalogue.B(15)
    item_c = next((n for n in b15.notes if "Purva, Uttra" in n), "")
    record("Both bare instances are in the B15 item that was ruled on",
           bool(item_c) and item_c.count("Purva") == item_c.count("Uttra") == 1
           and len(bare) == 2,
           item_c[:60] + "..." if item_c else "B15 item c) not found")

    # The two supplied spellings must be ones the document itself uses, which
    # is what makes the reconstruction a claim about its vocabulary.
    for spelling, n in (("Purva Falguni", 24), ("Uttra Falguni", 34)):
        record(f"The supplied spelling {spelling!r} is the document's own",
               len(re.findall(spelling, SOURCE_FLAT)) == n,
               f"{len(re.findall(spelling, SOURCE_FLAT))} occurrences, "
               f"expected {n}")


def test_b87s_proviso_is_a_condition_the_document_itself_obeys():
    """B87's colon scopes its verdict. Checked against the sky, not asserted.

    The heading is "Moon and Rahu in Same Nakshtra - Bullish: Rahu in
    Shatbisha", and the whole of the split turns on whether the second half
    names a *case* or merely the 2026 instance. The document answers it: B87
    tabulates eight Moon-with-Rahu windows and B88 -- "Rahu in Dhanistha" --
    tabulates the next five of the same monthly series with no verdict at all.
    If the two tables are one series partitioned by which nakshatra Rahu
    occupies, the colon is a condition and Bullish belongs to one part of it.

    Three things are checked, on the source's own printed times:

    * Rahu is in Shatabhisha at every B87 window and in Dhanishta at every B88
      window -- so the partition is by Rahu's nakshatra and nothing else;
    * each window is exactly the Moon's transit of that nakshatra, entry to
      exit, to better than a hundredth of a degree -- so both sections state
      the same condition and only the heading differs;
    * B88 prints no verdict, while B87 prints one.

    The times are IST, which the third bullet's arithmetic establishes rather
    than assumes: read as UTC the entries miss the cusp by about three degrees,
    which is 5h30m of Moon motion.
    """
    ephem.init()
    ist = dt.timedelta(hours=5, minutes=30)
    arc = 360 / 27

    def utc(date_cell: str, time_cell: str) -> dt.datetime:
        h, m = time_cell.split(":")
        return dt.datetime.strptime(date_cell, "%d-%b-%y").replace(
            hour=int(h), minute=int(m), tzinfo=dt.timezone.utc) - ist

    cases = (("B87", catalogue.B(87), "Shatabhisha"),
             ("B88", catalogue.B(88), "Dhanishta"))

    bad, windows = [], 0
    for label, sec, star in cases:
        lo = NAKSHATRAS.index(star) * arc
        for row in sec.tables[0].rows:
            windows += 1
            start, end = utc(row[0], row[1]), utc(row[2], row[3])
            if ephem.position(start, "Rahu").nakshatra != star:
                bad.append(f"{label} {row[0]} Rahu not in {star}")
            # The Moon sits ON the cusp at both ends, where the nakshatra NAME
            # flips either side of rounding -- so the check is the longitude
            # against the boundary, which is the quantity actually claimed.
            for when, want, edge in ((start, lo, "entry"),
                                     (end, lo + arc, "exit")):
                got = ephem.position(when, "Moon").lon
                if abs((got - want + 180) % 360 - 180) > 0.01:
                    bad.append(f"{label} {row[0]} Moon {edge} {got:.4f} "
                               f"!= {want:.4f}")

    record("B87's and B88's windows are one Moon-Rahu series partitioned by "
           "Rahu's nakshatra, so the colon names a case", not bad,
           str(bad) or f"{windows} windows: 8 with Rahu in Shatabhisha, 5 in "
           "Dhanishta, each the Moon's transit of that nakshatra")

    record("B88 states no verdict for the Dhanishta half of the same series",
           catalogue.split_statement(catalogue.B(88).title)[1] is None
           and not catalogue.B(88).remarks and not catalogue.B(88).notes,
           repr(catalogue.B(88).title))

    by_id = {r.id: r for r in R.REGISTRY}
    bare, scoped = (by_id["b087_moon_rahu_same_nakshatra"],
                    by_id["b087s_moon_rahu_same_nakshatra_rahu_in_shatabhisha"])
    record("The bare condition fires with the verdict withheld and says why",
           bare.verdict_text is None and bare.claim_tag is None
           and bare.tier is None
           and "verdict_conditioned_on_rahu_in_shatabhisha_not_met_in_2027"
           in bare.flags,
           f"verdict={bare.verdict_text!r} flags={list(bare.flags)}")
    record("The scoped rule carries the proviso and the verdict it restricts",
           scoped.condition_proviso == "Rahu in Shatbisha"
           and scoped.verdict_text == "Bullish"
           and scoped.condition_text == bare.condition_text,
           f"{scoped.condition_text!r} + {scoped.condition_proviso!r} "
           f"-> {scoped.verdict_text!r}")


def test_no_ported_verdict_swallows_a_scoping_colon():
    """The re-scan, kept as a check rather than as a finished sweep.

    Exactly two catalogue-B headings put a colon inside the verdict half: B87
    and B89, "Mars in the Nakshtra of Rohini or Chitra - Bullish: Mars in
    Rohini". Both are the same shape. B89 is not ported yet and must be split
    the way B87 was when it is -- and in 2027 it will land the same way round,
    since Mars enters Chitra on 13-Aug and never enters Rohini, so the
    condition fires and the proviso is not met.

    B98's title carries a colon too and is NOT this shape: "Mool Nakshtra:
    Mercury in Mool Nakshtra - Bearish" heads the condition with it, left of
    the dash, so the verdict half is bare.

    Two locks. The set of colon-in-verdict sections may not grow unnoticed, and
    no rule may carry a verdict with a colon still in it -- which is what a
    careless port of B89 would produce.
    """
    hits = {s.b for s in catalogue.SECTIONS
            if (catalogue.split_statement(s.title)[1] or "").find(":") >= 0}
    record("Exactly B87 and B89 scope a title verdict with a colon",
           hits == {87, 89}, f"sections {sorted(hits)}")

    b98 = catalogue.split_statement(catalogue.B(98).title)
    record("B98's colon heads its condition and is not a verdict scope",
           ":" in b98[0] and b98[1] == "Bearish", str(b98))

    # A colon in a verdict read out of a TITLE is the shape above and must
    # have been split. A colon in one read out of body text is a different
    # animal -- the document labels its own paragraphs, "Note: Usually at these
    # dates markets either change the trend..." -- and the label is carried
    # with the text because it is part of what the paragraph says. Each such
    # rule is pinned by name, so a new one is looked at rather than absorbed.
    label_prefix = {
        "b010_mercury_manifestation":
            "'Note:' labels the paragraph; the colon prefixes the statement "
            "rather than restricting it to a case",
        "b064_pradosh":
            "the verdict is a whole note of three sentences, each using a "
            "colon to introduce a clause inside itself ('Tithi Vriddhi on "
            "Pradosh Day: in Dark Fortnight intensity rises'). The rule now "
            "fires, and the note is still carried whole: its further "
            "sentences are separate rules about Vriddhi and Kshay Pradosh "
            "days, which B66-B69 now make portable, and splitting them in the "
            "same change that unblocked them would mix two decisions",
        "b063_hemisphere_range":
            "the same shape as b010: 'Rule:' is the document's own label for "
            "the second half of the note, not a case the verdict is restricted "
            "to. Dropping the label is the tempting port and it is wrong -- the "
            "flattened document reads 'medium term trade. Rule: When range is "
            "broken on both side', so a join that silently drops the two words "
            "carries a string the source does not print",
    }
    bad = [r.id for r in R.REGISTRY
           if r.verdict_text and ":" in r.verdict_text
           and (r.verdict_from == "title" or r.id not in label_prefix)]
    record("No ported verdict still has a scoping colon inside it",
           not bad,
           str(bad) or f"{len(label_prefix)} label-prefix colon(s) pinned: "
           + ", ".join(sorted(label_prefix)))


# ------------------------------------- 5b. batch 3, the lunar calendar
# These checks recompute the 2026 sky directly, which no rule may do. That is
# the point: the rule layer reads the generated 2027 calendar and never the
# ephemeris, so the only way to ask whether it READ THE DOCUMENT RIGHT is to
# put the document's own 2026 tables against an independent computation. The
# same method validated the navamsa ladder in batch 2 and B87's proviso.
#
# One sampling pass, reused by every check below. Two hours is well inside the
# Moon's slowest crossing, and every detected change is bisected to the second,
# so the grid costs nothing in accuracy.
_MOON_EDGE_CACHE: dict[float, list] = {}

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def _moon_edges(arc: float) -> list:
    """Instants at which the Moon changes its `arc`-degree division, 2026."""
    if arc in _MOON_EDGE_CACHE:
        return _MOON_EDGE_CACHE[arc]
    ephem.init()
    n, step = int(round(360 / arc)), dt.timedelta(hours=2)
    t = dt.datetime(2025, 12, 20, tzinfo=dt.timezone.utc)
    end = dt.datetime(2027, 1, 15, tzinfo=dt.timezone.utc)
    out, prev = [], None
    while t <= end:
        i = int(ephem.longitude(t, "Moon") // arc) % n
        if prev is not None and i != prev[1]:
            lo, hi, target = prev[0], t, i * arc
            for _ in range(40):
                mid = lo + (hi - lo) / 2
                if ((ephem.longitude(mid, "Moon") - target + 180) % 360) - 180 < 0:
                    lo = mid
                else:
                    hi = mid
            out.append((lo + (hi - lo) / 2, i))
        prev = (t, i)
        t += step
    _MOON_EDGE_CACHE[arc] = out
    return out


def _moon_windows(arc: float, indices: set) -> list:
    """(start, end) in IST for each run of the Moon through `indices`."""
    edges = _moon_edges(arc)
    runs, open_at = [], None
    for (t, i), (t_next, i_next) in zip(edges, edges[1:] + [(None, None)]):
        if i in indices and open_at is None:
            open_at = t
        if open_at is not None and (i_next is None or i_next not in indices):
            runs.append((open_at.astimezone(IST),
                         (t_next or t).astimezone(IST)))
            open_at = None
    return runs


def _printed_dates(section) -> set:
    return {dt.datetime.strptime(r[0].replace(" *", ""), "%d-%b-%y").date()
            for r in section.tables[0].rows}


def _time_off(when, printed: str) -> int:
    h, m = printed.split(":")
    return abs((when.hour * 60 + when.minute) - (int(h) * 60 + int(m)))


def test_the_moon_is_what_a_bare_nakshatra_name_means() -> None:
    """B71's fourteen 2026 windows, recomputed. The reading rests on this.

    Six sections of batch 3 condition on a nakshatra without naming a body.
    Reading that as the MOON is the one assumption the family stands on, and
    B71 is where the document tests it for us: it prints fourteen windows with
    both ends timed, which is enough structure that a wrong body could not come
    close.
    """
    arc = 360 / 27
    idx = NAKSHATRAS.index(names.nakshatra("Uttra Falguni"))
    wins = {w[0].date(): w for w in _moon_windows(arc, {idx})}
    rows = catalogue.B(71).tables[0].rows
    bad = []
    for row in rows:
        start = dt.datetime.strptime(row[0], "%d-%b-%y").date()
        got = wins.get(start)
        if got is None:
            bad.append(f"{row[0]}: no window starts that day")
            continue
        if got[1].strftime("%d-%b-%y") != row[3]:
            bad.append(f"{row[0]}: ends {got[1]:%d-%b-%y}, printed {row[3]}")
        for when, printed in ((got[0], row[1]), (got[1], row[4])):
            if _time_off(when, printed) > 2:
                bad.append(f"{row[0]}: {when:%H:%M} vs printed {printed}")
    record("B71's fourteen Uttara Phalguni windows are the MOON's, both ends "
           "to the minute", not bad and len(rows) == 14,
           str(bad) or f"{len(rows)} windows; every start date, end date and "
           "both times within two minutes")


def test_panchak_is_the_moon_in_aquarius_or_pisces() -> None:
    """The resolved definition, against the thirteen windows that resolved it.

    b055 fires on a definition the document never prints, and the whole of the
    ruling is that the section's own table comes back. Keeping that as a check
    rather than as a sentence inside `resolution` is what stops a ruling from
    becoming an assertion the moment nobody re-runs it.
    """
    idx = {SIGNS.index(s) for s in panchang_rules.PANCHAK_SIGNS}
    wins = {w[0].date(): w for w in _moon_windows(30.0, idx)}
    rows = catalogue.B(55).tables[0].rows
    bad = []
    for row in rows:
        start = dt.datetime.strptime(row[0], "%d-%b-%y").date()
        got = wins.get(start)
        if got is None:
            bad.append(f"{row[0]}: no Panchak starts that day")
            continue
        if got[1].strftime("%d-%b-%y") != row[2]:
            bad.append(f"{row[0]}: ends {got[1]:%d-%b-%y}, printed {row[2]}")
        for when, printed in ((got[0], row[1]), (got[1], row[3])):
            if _time_off(when, printed) > 2:
                bad.append(f"{row[0]}: {when:%H:%M} vs printed {printed}")
    record("Panchak read as the Moon in Aquarius or Pisces reproduces all "
           "thirteen of the section's own 2026 windows",
           not bad and len(rows) == 13,
           str(bad) or "13 windows, both dates and both times within two "
           "minutes; the definition is printed nowhere in the document")


#: The six Moon-nakshatra-on-weekday sections against the 2026 sky, pinned BY
#: DATE rather than by count: "the source omits some" is an impression and
#: "the source omits 04-Aug-2026" is a fact someone can go and check.
EXPECTED_2026_TABLE_GAPS = {
    72: (["04-Aug", "29-Sep"], []),
    97: (["13-Jul"], []),
    102: (["03-May"], ["28-Jun"]),
    103: (["12-May", "17-Feb"], []),
    104: ([], []),
    105: ([], []),
}


def test_the_weekday_family_against_the_sources_own_2026_tables() -> None:
    """Where the document's tables and its own titles disagree, and by how much.

    The condition occurs 23 times in 2026. The document prints 18 dates: 17 of
    those occurrences, and one -- B102's 28-Jun-2026 -- on which the condition
    does not hold at all, Anuradha having ended at 22:11 the previous evening.
    Six occurrences are not listed.

    None of the six omissions is explained by how long the window lasts (B104
    prints 1.19 hours and B102 omits 16.83), by market hours, or by the
    weekday. So the tables are incomplete and the titles are the rule -- and
    these rules therefore fire on days the source did not print, on purpose.
    """
    arc = 360 / 27
    bad, occurrences, printed_total = [], 0, 0
    for b, (want_omitted, want_spurious) in EXPECTED_2026_TABLE_GAPS.items():
        # Read from the WHOLE title, not from its condition half: B72 puts
        # both halves of its condition in the parenthetical that follows the
        # verdict, and the other five put them before it.
        title = catalogue.B(b).title
        star = names.nakshatras_in(title)[0]
        day = names.weekdays_in(title)[0]
        got = set()
        for start, end in _moon_windows(arc, {NAKSHATRAS.index(star)}):
            d = start.date()
            while d <= end.date():
                if d.weekday() == day and d.year == 2026:
                    got.add(d)
                d += dt.timedelta(days=1)
        printed = _printed_dates(catalogue.B(b))
        occurrences += len(got)
        printed_total += len(printed)
        omitted = sorted(d.strftime("%d-%b") for d in got - printed)
        spurious = sorted(d.strftime("%d-%b") for d in printed - got)
        if omitted != sorted(want_omitted) or spurious != sorted(want_spurious):
            bad.append(f"B{b}: omitted {omitted} (want {sorted(want_omitted)}), "
                       f"spurious {spurious} (want {sorted(want_spurious)})")
    record("The 2026 tables of the six weekday sections differ from their own "
           "titles in exactly the pinned places", not bad,
           str(bad) or f"{occurrences} occurrences, {printed_total} printed, "
           "6 omitted, and 1 printed date on which the condition never holds")

    record("Two of the six reproduce exactly, which is what makes the other "
           "four a finding about the document rather than about the reading",
           EXPECTED_2026_TABLE_GAPS[104] == ([], [])
           and EXPECTED_2026_TABLE_GAPS[105] == ([], []),
           "B104's six Mrigashira-on-Thursday dates and B105's four Uttara "
           "Ashadha-on-Monday dates, exact under civil_day_overlap")


def test_weekday_conditions_are_read_from_the_title_and_applied_per_location(
        firings: list) -> None:
    """The weekday half: declared from the document, applied at the venue."""
    weekday_rules = [r for r in R.REGISTRY if r.weekdays]
    # Against the rule's own condition_text, not against the section title.
    # b060t's weekday is stated in a remark and b072's in a parenthetical, and
    # the claim worth checking is that the weekday is named in the very text
    # the rule carries as its condition.
    mismatched = [(r.id, r.weekdays, names.weekdays_in(r.condition_text))
                  for r in weekday_rules
                  if set(r.weekdays) != set(names.weekdays_in(r.condition_text))]
    record("Every weekday rule declares exactly the weekdays named in its own "
           "condition text", not mismatched,
           str(mismatched) or f"{len(weekday_rules)} weekday rules")

    by_id = {r.id: r for r in weekday_rules}
    bad = [(f.rule_id, f.location, f.civil_date.strftime("%d-%b-%Y %a"))
           for f in firings if f.rule_id in by_id
           and f.civil_date.weekday() not in by_id[f.rule_id].weekdays]
    record("Every weekday firing lands on a declared weekday of ITS OWN "
           "location's calendar", not bad, str(bad[:4]))

    # And the filter must be doing work, or the check above is vacuous.
    sky = Sky.load()
    unfiltered = sum(len(civil_days(sp, "mumbai", Y))
                     for r in weekday_rules if r.fn is not None
                     for sp in r.fn(sky))
    kept = len([f for f in firings
                if f.rule_id in by_id and f.location == "mumbai"])
    record("The weekday filter removes most of what its condition matches",
           0 < kept < unfiltered / 3,
           f"{kept} Mumbai rows kept of {unfiltered} day-matches before the "
           "weekday is applied")


#: The eighteen sections that carried one of batch 3's two shared missing-input
#: strings, and what each became once the tithi and yoga ingress classes
#: arrived. Pinned as a partition rather than as a count, because the
#: interesting number is not how many cleared but which did not and why: a
#: section that quietly moved between these three sets would otherwise read as
#: an unchanged total.
PANCHANG_SERIES_SECTIONS = {
    # Cleared by the tithi and yoga series alone: it was the whole of what each
    # was missing. Then cleared by the sunrise series: B66-B69, whose second
    # half is a day boundary and not an angle. Then B101, cleared by a calendar
    # helper and not by an event class at all.
    "executable": {65, 66, 67, 68, 69, 73, 74, 75, 76, 95, 96, 100, 101, 106,
                   108, 109},
    # Cleared onto a reading that is partly ours, and for two different
    # reasons. B56's yoga half is now available and its Panchak half is b055's
    # supplied definition, so it inherits that status. B64's astronomy half is
    # supplied by the sunset series and its definition is not: the document
    # names Pradosh twenty-two times and defines it nowhere, and the plain
    # reading reproduces 22 of its 24 rows against the ruled reading's 23.
    # Neither is ever counted with the executable.
    "resolved_ambiguity": {56, 64},
    # Nothing. All eighteen sections that shared batch 3's two missing-input
    # strings now fire, which is the claim this check exists to keep honest: it
    # is a partition and not a count, so a section that slid between these sets
    # cannot hide inside an unchanged total.
    "blocked": set(),
}


def test_the_tithi_and_yoga_series_cleared_what_batch_three_said_they_would(
        firings) -> None:
    """Batch 3 promised one restored input would clear sixteen families.

    It cleared twelve of the eighteen sections that named the two strings, and
    the six that remain are the point of this check. Each is blocked on
    something the tithi series was never going to supply, named separately, so
    that "still blocked" cannot go on meaning "still waiting for the same
    thing".
    """
    by_section = {}
    for b in set().union(*PANCHANG_SERIES_SECTIONS.values()):
        by_section[b] = {r.status for r in R.REGISTRY if r.catalogue_b == b}

    for want, sections in PANCHANG_SERIES_SECTIONS.items():
        wrong = sorted(b for b in sections if want not in by_section[b])
        record(f"The {len(sections)} sections expected to be {want} are",
               not wrong, f"sections {sorted(sections)}"
               + (f"; wrong: {wrong}" if wrong else ""))

    # A missing-input string that no longer describes a missing input is worse
    # than no string: it goes on reporting an absence the layer has filled, and
    # nothing downstream can tell the difference. Batch 3's five strings named
    # the tithi series, the yoga series, sunrise, sunset and a per-location
    # weekday count; all five are supplied, so no surviving string may claim
    # any of them is absent.
    sky = Sky.load()
    stale = re.compile(
        r"emits no (tithi|yoga) ingress|no (tithi|yoga) ingress|"
        r"emits no sunrise|emits no sunset|no sunrise( series)? (is|and)")
    claiming = [r.id for r in R.REGISTRY
                for m in r.missing_inputs if stale.search(m)]
    record("No rule still names an absence this batch filled -- tithi, yoga, "
           "sunrise, sunset or a per-location weekday count",
           not claiming,
           f"in the file: {len(sky.by_class['tithi_ingress'])} tithi, "
           f"{len(sky.by_class['yoga_ingress'])} yoga, "
           f"{len(sky.by_class['sunrise'])} sunrise and "
           f"{len(sky.by_class['sunset'])} sunset records"
           + (f"; stale: {claiming}" if claiming else ""))

    # B55's remark moved from `blocked` to `ambiguous` rather than clearing,
    # and that distinction is the one this check exists to keep: the sunrise it
    # was blocked on now exists, and what is left is which of two ghati
    # definitions the source means, which no event class supplies.
    b55g = next(r for r in R.REGISTRY
                if r.id == "b055g_panchak_after_forty_ghati")
    record("B55's 40-ghati remark is ambiguous and no longer blocked: the "
           "input arrived, the reading did not",
           b55g.status == R.STATUS_AMBIGUOUS and not b55g.missing_inputs
           and "ghati" in b55g.ambiguity,
           f"status {b55g.status}, {len(b55g.missing_inputs)} missing inputs")

    fired = {f.rule_id for f in firings}
    record("No blocked rule emits a row",
           not [r.id for r in R.by_status(R.STATUS_BLOCKED) if r.id in fired],
           f"{len(R.by_status(R.STATUS_BLOCKED))} blocked rules")


def test_the_panchang_rules_read_the_layer_and_not_the_ephemeris() -> None:
    """The new conditions are spans off the emitted series, like every other.

    The whole value of the two new classes is that a tithi rule and the
    calendar cannot disagree, and that holds only while the rules read
    `Sky.tithi_spans()` and never recompute an elongation. The AST check that
    covers the other modules covers these too; this one asserts the positive --
    that every span a panchang rule fires on is bounded by records in the file.
    """
    sky = Sky.load()
    edges = {r["time"]["t_start_utc"] for r in sky.by_class["tithi_ingress"]}
    edges |= {r["time"]["t_start_utc"] for r in sky.by_class["yoga_ingress"]}
    edges |= {sky.meta["span_start_utc"], sky.meta["span_end_utc"]}

    panchang_ids = {"b065_ekadashi_on_friday",
                    "b073_ashtami_on_tuesday_saturday",
                    "b074_ashtami_on_monday_thursday_friday",
                    "b075_chaturthi_shukla_paksha",
                    "b076_chaturthi_krishna_paksha",
                    "b095_shukla_pratipada_on_saturday_or_sunday",
                    "b096_vyatipata_yoga_on_tuesday_saturday_or_sunday",
                    "b100_shukla_shasthi_on_friday",
                    "b106_amavasya_ghadi_lesser_than_chaturdashi",
                    "b109_shukla_trayodashi_on_tuesday_or_saturday"}
    bad = []
    for r in R.REGISTRY:
        if r.id not in panchang_ids or r.fn is None:
            continue
        for sp in r.fn(sky):
            for end in (sp.start, sp.end):
                if end.strftime("%Y-%m-%dT%H:%M:%SZ") not in edges:
                    bad.append((r.id, str(end)))
    record("Every span the tithi and yoga rules fire on is bounded by emitted "
           "ingress records, never by a recomputed angle", not bad,
           f"{len(panchang_ids)} rules checked, {len(bad)} span ends not found "
           f"in the astronomy layer" + (f" e.g. {bad[:2]}" if bad else ""))


def test_the_final_dash_titles_would_have_lost_their_condition() -> None:
    """Six titles where a first-dash split files half the condition as verdict.

    "Kshay Tithi - Shukla Paksh (Bright Fortnight) - Bearish" is one condition
    in two segments plus a verdict, and `split_statement` hands back "Shukla
    Paksh (Bright Fortnight) - Bearish" as the outcome. That is B87's colon in
    a different mark, found by re-scanning for it; this pins the six sections
    it affects so a seventh cannot arrive unexamined.
    """
    want = {66, 67, 68, 69, 75, 76}
    got = {sec.b for sec in catalogue.SECTIONS
           if catalogue.split_statement(sec.title)[1] is not None
           and catalogue.split_statement(sec.title)[1]
           != catalogue.split_final(sec.title)[1]}
    record("Exactly six titles split differently at the first and final dash",
           got == want, f"sections {sorted(got)}")

    by_b = {r.catalogue_b: r for r in R.REGISTRY
            if "condition_split_at_final_dash" in r.flags}
    record("All six are ported on the final-dash reading and carry the flag",
           set(by_b) == want, f"flagged {sorted(by_b)}")

    bad = [r.id for r in by_b.values()
           if r.verdict_text not in ("Bullish", "Bearish")]
    record("Each of the six carries the one-word verdict the final dash "
           "separates", not bad,
           str(bad) or ", ".join(f"B{b} {r.verdict_text}"
                                 for b, r in sorted(by_b.items())))


# ------------------------------------------------------------ 6. firings
def test_shar_is_the_latitude_sign_and_not_the_declination():
    """B118/B119's convention, re-derived from the engine every run.

    Shar was settled as the ecliptic LATITUDE sign by reproducing the source's
    own printed 2026 dates, and the competing reading -- declination sign -- was
    rejected on those same dates. Both halves are re-run here rather than
    asserted in prose, because the rejection is what licenses the rule and a
    rejection nothing recomputes is a claim that decays into a fact.
    """
    from finastro.timezones import IST

    def crossings(fn, lo, hi, step_h=3):
        step = dt.timedelta(hours=step_h)
        out, t = [], lo
        prev = fn(t)
        while t < hi:
            nxt = t + step
            cur = fn(nxt)
            if (prev < 0) != (cur < 0):
                a, b = t, nxt
                for _ in range(40):
                    m = a + (b - a) / 2
                    if (fn(a) < 0) != (fn(m) < 0):
                        b = m
                    else:
                        a = m
                out.append(a + (b - a) / 2)
            prev, t = cur, nxt
        return out

    lo = dt.datetime(2026, 1, 1, tzinfo=IST)
    hi = dt.datetime(2027, 1, 1, tzinfo=IST)

    # B119's 27 printed end dates, read out of the source.
    ends = []
    for r in catalogue.B(119).tables[0].rows:
        for e in (r[2], r[5]):
            if e and not e.lower().startswith("till"):
                try:
                    ends.append(dt.datetime.strptime(e, "%d-%b-%y")
                                .replace(tzinfo=IST))
                except ValueError:
                    pass
    ends = sorted(set(ends))
    record("B119 prints 27 Shar periods for 2026", len(ends) == 27,
           f"{len(ends)} ends")

    def near(xs, tol=1.5):
        return sum(1 for t in xs
                   if min(abs((t - e).total_seconds()) for e in ends)
                   <= tol * 86400)

    lat = crossings(lambda t: ephem.position(t, "Moon").lat, lo, hi)
    dec = crossings(lambda t: ephem.declination(t, "Moon"), lo, hi)
    lat_ok, dec_ok = near(lat), near(dec)
    record("The Moon's LATITUDE sign reproduces B119's printed ends",
           len(lat) == 27 and lat_ok >= 26,
           f"{lat_ok}/{len(lat)} within 1.5 d")
    record("The Moon's DECLINATION sign does not reproduce B119",
           dec_ok == 0,
           f"{dec_ok}/{len(dec)} within 1.5 d -- the rejected reading, "
           "systematically late, which is a different quantity's phase")

    # B118: Mars prints one change and must have one crossing near it.
    rows = catalogue.B(118).tables[0].rows
    mars_ends = [r[2] for r in rows if r[0] == "Mars"]
    mx = crossings(lambda t: ephem.position(t, "Mars").lat, lo, hi)
    mx_dec = crossings(lambda t: ephem.declination(t, "Mars"), lo, hi)
    printed = dt.datetime.strptime("26-Jul-26", "%d-%b-%y").replace(tzinfo=IST)
    record("Mars prints one Shar change, and its latitude has one crossing",
           len(mx) == 1 and abs((mx[0] - printed).total_seconds()) < 2 * 86400,
           f"{len(mx)} crossing(s), nearest {mx[0]:%d-%b-%y %H:%M} vs printed "
           f"{printed:%d-%b-%y}")
    record("Mars's declination crossing is NOT the printed Shar change",
           len(mx_dec) == 1
           and abs((mx_dec[0] - printed).total_seconds()) > 30 * 86400,
           f"{mx_dec[0]:%d-%b-%y} is "
           f"{abs((mx_dec[0] - printed).days)} d from the printed date")
    bodies, seen = [], set()
    for r in rows:
        if r[0] and r[0] not in seen:
            seen.add(r[0])
            bodies.append(r[0])
    record("B118 lists seven bodies and B119 the Moon",
           tuple(bodies) == ("Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                             "Herschel", "Neptune"),
           f"{len(bodies)} distinct bodies in the source's own order: "
           f"{', '.join(bodies)}")


# ------------------------------------------------------- 6b. batch 4b apsides
def test_the_apsis_rules_fire_on_emitted_apsides_and_not_on_a_threshold():
    """B57/B58's reading, re-derived from the source's own table every run.

    The section states a distance threshold and its table does not obey it, so
    the rule conditions on the extremum instead. That is a reading of the page
    and it is checked here rather than asserted in prose: the printed
    distances are counted against the threshold the same page states, and the
    firing spans are checked to be the emitted `apsis` records and nothing
    else. A later change that quietly reinstated the threshold would fail the
    first check; one that recomputed its own distance would fail the second.
    """
    sky = Sky.load()
    AU_KM = 149597870.7

    # --- the printed distances against the threshold the same note states ---
    for b, threshold, clears in ((57, 406000.0, lambda km: km > 406000.0),
                                 (58, 360000.0, lambda km: km < 360000.0)):
        note = catalogue.B(b).notes[0]
        rows = catalogue.B(b).tables[0].rows
        printed = [float(r[2].replace(",", "")) for r in rows]
        obeying = [km for km in printed if clears(km)]
        record(f"B{b}: the printed table does not obey the threshold its own "
               f"note states, so the threshold is not the condition",
               len(printed) == len(rows) and len(obeying) < len(rows) / 2,
               f"{len(obeying)}/{len(rows)} rows obey "
               f"{threshold:.0f} km; printed range "
               f"{min(printed):.0f}..{max(printed):.0f}")
        record(f"B{b}: the threshold is stated verbatim in the section's note",
               f"{threshold:.0f}" in note.replace(",", ""),
               f"note: {note[:64]}...")

    # --- every span is an instant at an apsis record the file emits ---
    by_family = {}
    for fam in ("orbit/apogee", "orbit/perigee", "orbit/perihelion",
                "orbit/aphelion"):
        by_family[fam] = {r["time"]["t_start_utc"]
                          for r in sky.class_records("apsis", family=fam)}
    want = {"b057_moon_apogee": ("orbit/apogee",),
            "b058_moon_perigee": ("orbit/perigee",),
            "b059_perihelion_and_aphelion": ("orbit/perihelion",
                                             "orbit/aphelion")}
    firings = R.fire(R.REGISTRY, sky)
    bad, spans = [], 0
    for rid, fams in want.items():
        r = next(x for x in R.REGISTRY if x.id == rid)
        emitted = set().union(*(by_family[f] for f in fams))
        kinds = {f.split("/")[1] for f in fams}
        for sp in r.fn(sky):
            spans += 1
            if sp.start != sp.end:
                bad.append((rid, "not an instant", str(sp.start)))
            if sp.start.strftime("%Y-%m-%dT%H:%M:%SZ") not in emitted:
                bad.append((rid, "not an emitted apsis", str(sp.start)))
            if sp.value["apsis"] not in kinds:
                bad.append((rid, "wrong apsis kind", sp.value["apsis"]))
    record("Every apogee, perigee, perihelion and aphelion span is an instant "
           "at an apsis record the file emits", bool(spans) and not bad,
           f"{spans} spans, {len(bad)} inconsistent"
           + (f" e.g. {bad[:2]}" if bad else ""))

    # --- the detail's own distance agrees with the record it came from ---
    mismatched = []
    for rid in want:
        r = next(x for x in R.REGISTRY if x.id == rid)
        for sp in r.fn(sky):
            rec = next(x for x in sky.class_records("apsis")
                       if x["time"]["t_start_utc"] == sp.value["utc"])
            km = rec["astronomy"]["distance"] * AU_KM
            if abs(sp.value["distance_km"] - round(km)) > 1:
                mismatched.append((rid, sp.value["distance_km"], round(km)))
    record("Every apsis row's own distance is the record's, in both units",
           not mismatched, str(mismatched[:3]))

    # --- the shared 2026 rows: the source's date, to the half hour ---
    checks = (("orbit/apogee", "11-Dec-2026", "12:15", 406420),
              ("orbit/perigee", "24-Dec-2026", "13:59", 356652))
    for fam, date, hhmm, km in checks:
        recs = [x for x in sky.class_records("apsis", family=fam)
                if x["time"]["start_stamp"]["ist_date"] == date]
        if len(recs) != 1:
            record(f"B{fam.split('/')[1]}: the source's one 2026 row has a "
                   f"single record", False, f"{len(recs)} records on {date}")
            continue
        st = recs[0]["time"]["start_stamp"]
        got = recs[0]["astronomy"]["distance"] * AU_KM
        mins = abs((dt.datetime.strptime(st["ist_time"], "%H:%M")
                    - dt.datetime.strptime(hhmm, "%H:%M")).total_seconds()) / 60
        record(f"B{fam.split('/')[1]}: the source's one 2026 row is "
               f"reproduced on its date",
               st["ist_date"] == date and mins <= 30 and abs(got - km) <= 30,
               f"printed {date} {hhmm} {km} km, computed {st['ist_date']} "
               f"{st['ist_time']} {got:.0f} km ({mins:.0f} min, "
               f"{got - km:+.0f} km)")

    # --- B57's Amavasya: "together" is the tithi in force at the instant ---
    r57a = next(x for x in R.REGISTRY if x.id == "b057a_apogee_with_amavasya")
    bad = []
    for sp in r57a.fn(sky):
        inside = [t for t in sky.tithi_spans()
                  if t.start <= sp.start < t.end
                  and t.value["tithi_name"] == "Amavasya"]
        if not inside:
            bad.append((str(sp.start), "not in an emitted Amavasya span"))
        elif inside[0].value["tithi"] != sp.value["tithi"]:
            bad.append((str(sp.start), "tithi number disagrees"))
    record("Every 'Apogee and Amavasya together' row sits inside an Amavasya "
           "span the layer emits, and names that tithi", not bad,
           str(bad) or "1 row, 07-Jan-2027")

    # --- B59's two rows, in the year the calendar is built for ---
    b59 = {f.civil_date.strftime("%d-%b-%Y")
           for f in firings if f.rule_id == "b059_perihelion_and_aphelion"
           and f.location == "mumbai"}
    record("B59 fires on both events of its table -- one perihelion and one "
           "aphelion in the generated calendar year",
           len(b59) == 2 and {"03-Jan-2027", "05-Jul-2027"} == b59,
           f"{sorted(b59)}")


def test_kaal_sarp_yog_is_empty_under_both_its_readings():
    """B77's zero, measured hourly, and checked at the reading NOT ported.

    Two things could make this zero a lie and both are checked. The first is
    that the rule never fired because the layer's Rahu sign spans are
    period-truncated at both ends -- so the test iterates the rule's OWN
    windows and evaluates the condition at every instant across them, which
    turns the empty result into a measurement of the sky. The second is that
    "between Rahu and Ketu" was read at the coarser of two resolutions and the
    finer one would have found dates -- so the degree reading is recomputed
    here against the ephemeris. The rule layer must not ask it; this check may,
    because what it establishes is that the ported reading is not a choice
    between disagreeing answers.
    """
    sky = Sky.load()
    from finastro.rules import apsides

    # --- the windows the rule actually iterates ---
    windows = apsides.rahu_sign_windows(sky)
    record("B77's windows are Rahu's sign records and not the period-truncated "
           "spans, so the rule's zero is not an artefact of the file's edges",
           bool(windows)
           and windows[0].start == dt.datetime(2026, 12, 5, 17, 2, 10,
                                               tzinfo=dt.timezone.utc),
           f"{len(windows)} window(s): "
           + "; ".join(f"{w.value} {w.start:%d-%b-%Y} .. {w.end:%d-%b-%Y}"
                       for w in windows))

    # --- the condition, at every hour of every window ---
    step = dt.timedelta(hours=1)
    checked, held = 0, []
    for w in windows:
        t = w.start
        while t <= w.end:
            checked += 1
            if apsides.kaal_sarp_condition_holds(sky, t):
                held.append(t)
            t += step
    record("B77's condition holds at no instant of any window, so the zero is "
           "a fact about the sky and not a skipped span",
           checked > 8000 and not held,
           f"{checked} instants tested at 1-hour steps across "
           f"{len(windows)} window(s); {len(held)} held"
           + (f", first {held[0]:%d-%b-%Y}" if held else ""))

    # The exclusion named: which bodies are outside the arc, and why that is
    # permanent for this window rather than a near miss.
    w = windows[-1]
    allowed = apsides._forward_semicircle(w.value)
    placed = {b: sky.value_at(b, "sign", w.start) for b in apsides.KSY_BODIES}
    outside = [b for b, x in placed.items() if x not in allowed]
    record("The exclusion is named: the Sun and Moon are two of the nine bodies "
           "the sentence names and they pass through the other six signs "
           "continually, so no window bounded by one Rahu sign can ever hold",
           {"Sun", "Moon"} <= set(outside),
           f"at {w.start:%d-%b-%Y} Rahu in {w.value} -> arc {sorted(allowed)}; "
           f"outside {outside}")

    # --- reading 2, NOT ported: strictly between the node longitudes. ---
    def strictly_between(when):
        rahu = ephem.longitude(when, "Rahu")
        return [b for b in apsides.KSY_BODIES
                if not 0 < (ephem.longitude(when, b) - rahu) % 360 < 180]

    UTC = dt.timezone.utc
    t, end, open_at, deg_windows = sky.span_start, sky.span_end, None, []
    while t < end:
        if not strictly_between(t):
            if open_at is None:
                open_at = t
        elif open_at is not None:
            deg_windows.append((open_at, t))
            open_at = None
        t += dt.timedelta(minutes=30)
    if open_at is not None:
        deg_windows.append((open_at, end))
    record("B77's DEGREE reading also finds no instant in the generated span "
           "where every named body is enclosed, so the ported reading is not "
           "one of two disagreeing answers", not deg_windows,
           f"{len(deg_windows)} window(s) wholly enclosed; "
           f"{len(apsides.KSY_BODIES)} bodies checked per instant")

    # The closest the span comes, named: Rahu's widest semicircle in longitude.
    probe = dt.datetime(2027, 12, 18, tzinfo=UTC)
    out = strictly_between(probe)
    record("B77: at Rahu's own 2027 sign boundary the degree reading still "
           "names bodies in the far half, so its zero is arithmetic too",
           bool(out),
           f"2027-12-18 at Rahu {ephem.longitude(probe, 'Rahu'):.2f} deg -- "
           "outside " + ", ".join(
               f"{b} at "
               f"{(ephem.longitude(probe, b) - ephem.longitude(probe, 'Rahu')) % 360:.1f} deg"
               f" from Rahu" for b in out))

    # --- rule status: executable, verdict-free, for a reason on the page ---
    r77 = next(x for x in R.REGISTRY if x.id == "b077_kaal_sarp_yog")
    record("B77 is executable and states no verdict, because its own note says "
           "Kaal Sarp Yog is neither bullish nor bearish",
           r77.status == R.STATUS_EXECUTABLE and r77.verdict_text is None
           and "neither Bullish or Bearish" in catalogue.B(77).notes[0],
           f"status={r77.status}, verdict={r77.verdict_text!r}")

    # --- the source's printed 2026 row: outside the span, and not the
    #     condition's window either ---
    from finastro.timezones import IST
    row = catalogue.B(77).tables[0].rows[0]
    printed_start = dt.datetime.strptime(f"{row[0]} {row[1]}",
                                         "%d-%b-%y %H:%M").replace(tzinfo=IST)
    printed_end = dt.datetime.strptime(f"{row[2]} {row[3]}",
                                       "%d-%b-%y %H:%M").replace(tzinfo=IST)
    record("The source prints ONE Kaal Sarp window and it is 2026, outside the "
           "generated span, so the layer cannot check it",
           printed_start.year == 2026
           and printed_start.astimezone(UTC) < sky.span_start,
           f"printed {printed_start:%d-%b-%Y %H:%M} .. {printed_end:%d-%b-%Y} "
           f"({(printed_end - printed_start).days} d) against a span opening "
           f"{sky.span_start:%d-%b-%Y}")
    for label, when in (("start", printed_start), ("end", printed_end)):
        out = strictly_between(when)
        record(f"B77: the source's printed window {label} does not satisfy the "
               f"condition printed above it", bool(out),
               f"{when:%d-%b-%Y %H:%M}: outside " + ", ".join(
                   f"{b} at "
                   f"{(ephem.longitude(when, b) - ephem.longitude(when, 'Rahu')) % 360:.1f} deg"
                   f" from Rahu" for b in out))


def test_hemisphere_is_blocked_on_the_equinox_and_says_so():
    """B63's two independent blockers, both carried on the rule.

    The section needs a tropical solar longitude the layer does not emit as a
    series, AND its own words admit more than one reading of what its range is.
    The first is a gap in this layer and the second is a property of the page,
    and they are different findings: merging them into one `blocked` string is
    how the second gets lost. This checks that both are on the record and that
    no date is emitted.
    """
    r = next(x for x in R.REGISTRY if x.id == "b063_hemisphere_range")
    record("B63 is registered blocked, not silently ported",
           r.status == R.STATUS_BLOCKED, f"status={r.status}")
    record("B63 names the missing tropical solar longitude and the undecided "
           "reading as two separate missing inputs",
           len(r.missing_inputs) == 2
           and "tropical" in r.missing_inputs[0]
           and "range" in r.missing_inputs[1],
           f"{len(r.missing_inputs)} missing inputs")
    record("B63 states the competing readings it is not choosing between",
           all(k in r.ambiguity for k in
               ("centre", "Prices", "broken on both side")),
           f"{len(r.ambiguity)} chars of readings")
    record("B63 emits no firing",
           not any(f.rule_id == r.id for f in R.fire(R.REGISTRY, Sky.load())),
           "a blocked rule that emitted would be a port by accident")

    # The condition and the verdict are two slices off the same note. The
    # condition is one of its sentences; the verdict is the other sentence
    # joined to the line under it, and BOTH the source's own "Rule:" label and
    # the single joining space are what the flattened document has -- dropping
    # the label, which is tempting because it reads like a prefix and carries a
    # colon, is what this check exists to catch.
    lines = [ln.strip() for ln in catalogue.B(63).notes[0].split("\n")]
    sents = [s.strip() for s in lines[1].split(". ")]
    want_verdict = sents[1] + " " + lines[2]
    record("B63's condition is the note's own sentence and its verdict the two "
           "that follow it, neither retyped",
           r.condition_text == sents[0]
           and r.verdict_text == want_verdict,
           f"cond={r.condition_text!r}; verdict={r.verdict_text!r}")


def test_firings(firings: list) -> None:
    record(f"Every firing lands in calendar {Y}",
           all(f.civil_date.year == Y for f in firings),
           f"{len(firings)} firings")

    locs = {f.location for f in firings}
    record("Firings are emitted per location, never on a merged date column",
           locs <= set(R.LOCATIONS), str(sorted(locs)))

    counts = R.counts_by_rule(firings)
    got = {rid: c["mumbai"] for rid, c in counts.items() if c["mumbai"]}
    record("Mumbai firing counts are exactly as pinned",
           got == EXPECTED_FIRINGS_MUMBAI,
           str(sorted((k, v) for k, v in got.items()
                      if EXPECTED_FIRINGS_MUMBAI.get(k) != v)) or "all match")

    zero = {r.id for r in R.zero_firing(firings)}
    record("The zero-firing set is exactly the rules checked to be zero",
           zero == set(EXPECTED_ZERO_FIRING),
           str(sorted(zero ^ set(EXPECTED_ZERO_FIRING))) or "as expected")


def test_combust_family_declares_its_narrowing() -> None:
    # Firing statuses, not just executable: a resolved rule emits rows and so
    # owes the same declaration. Narrowing this filter to `executable` is how
    # b015c would have slipped the check the moment it started firing.
    fam = [r for r in R.REGISTRY
           if r.rule_family.startswith("visibility/")
           and r.status in R.FIRING_STATUSES]
    record("The combust family evaluates on the Mumbai day and says why",
           all(r.locations == ("mumbai",)
               and "combust_evaluated_mumbai_horizon_date_only" in r.flags
               for r in fam),
           f"{len(fam)} visibility rules; kalamsha is a primary-location "
           "horizon measurement at date_only precision")


def test_combust_windows_match_the_source_duration_convention() -> None:
    """A window must run combust-day to rise-day, exclusive of the rise day.

    That is the source's own Duration column -- 33 days for Mercury combust
    02-Jan-26 and rise 04-Feb-26 -- and it is what makes the window's day count
    reproducible rather than a choice.
    """
    sky = Sky.load()
    bad = []
    for body in ("Mercury", "Venus", "Jupiter", "Saturn", "Mars"):
        evs = sky.class_records("combustion", body=body)
        spans = {s.start: s for s in sky.combust_spans(body)}
        for i in range(len(evs) - 1):
            c, rise = evs[i], evs[i + 1]
            if c["rule_family"] != "visibility/combust" \
                    or rise["rule_family"] != "visibility/rise":
                continue
            span = next((s for t, s in spans.items()
                         if t.strftime("%Y-%m-%dT%H:%M:%SZ")
                         == c["time"]["t_start_utc"]), None)
            if span is None or span.end.strftime("%Y-%m-%dT%H:%M:%SZ") \
                    != rise["time"]["t_start_utc"]:
                bad.append((body, c["id"]))
    record("Every combust window ends on its own rise record", not bad,
           str(bad))


# ------------------------------------------- 7. nothing leaked in either way
def test_outer_pair_rules_come_from_the_documents_own_tables() -> None:
    """One rule per printed row, and the partner list is never typed by hand.

    The six outer conjunction/opposition sections print a Planet column and a
    Result column, and the Result differs per partner -- so the rules must be
    generated from the rows. If someone later types a pair list, this fails:
    the count stops matching the document's own row count.
    """
    rows = sum(len(catalogue.B(b).tables[0].rows)
               for b in (41, 42, 47, 48, 53, 54))
    record("Outer pair rules number exactly the rows the sections print",
           len(colocation.OUTER_PAIR_RULES) == rows == 23,
           f"{len(colocation.OUTER_PAIR_RULES)} rules from {rows} printed rows")

    # A blank Result is a pairing the section prints without an outcome. It
    # must carry no verdict -- not the section's general one, which does not
    # exist, and not an invented one.
    by_id = {r.id: r for r in R.REGISTRY}
    bad = []
    for b in (41, 42, 47, 48, 53, 54):
        sec = catalogue.B(b)
        for i, row in enumerate(sec.tables[0].rows):
            rid = next((x for x in colocation.OUTER_PAIR_RULES
                        if x.startswith(f"b{b:03d}_")
                        and x.endswith(names.body(row[0]).lower())), None)
            if rid is None or rid not in by_id:
                bad.append((b, i, row[0], "no rule"))
                continue
            want = row[3] or None
            if by_id[rid].verdict_text != want:
                bad.append((b, i, row[0], by_id[rid].verdict_text, want))
    record("Every outer pair's verdict is its own row's Result cell, blank "
           "included", not bad, str(bad))


def test_the_navamsa_ladder_agrees_with_the_ephemeris() -> None:
    """The ordering method, checked against the one it is not allowed to use.

    `test_2027_astronomy.py` resolves Mars-vs-Jupiter ordering with three
    direct `ephem.longitude()` samples per shared-sign window and gets "ahead"
    in all three. The ladder reads two emitted ingress series and one
    definitional identity and must get the same answer. Two unrelated methods
    agreeing is what makes the ladder a reading rather than a guess; if they
    ever diverge, the ladder is wrong and every ordering rule is suspect.
    """
    sky = Sky.load()
    spans = colocation._order_spans(sky, "Mars", "Jupiter")
    record("The ladder orders Mars ahead of Jupiter in all three shared-sign "
           "windows, as the ephemeris independently does",
           len(spans) == 3 and all(s.value == "ahead" for s in spans),
           f"{len(spans)} windows: {[s.value for s in spans]}")

    bad = []
    for (a, b), want in EXPECTED_TIED_DAYS.items():
        got = colocation.tied_days(sky, a, b)
        if abs(got - want) > 1 / 1440:
            bad.append((a, b, round(got, 4), want))
    record("The ladder's unordered stretches are exactly as long as pinned",
           not bad,
           str(bad) or ", ".join(f"{a}/{b} {w}d"
                                 for (a, b), w in EXPECTED_TIED_DAYS.items()))


def test_ordering_rules_reconstruct_their_own_shared_sign_window(firings):
    """behind + ahead + tied must account for the whole window, and no more.

    This is the check that makes the ladder's silence auditable. If an ordering
    rule ever fired on a day outside its pair's shared-sign window, or the two
    directions started overlapping, the totals would stop adding up -- and
    without this they would still look like three plausible numbers.
    """
    counts = R.counts_by_rule(firings)

    def n(rid: str) -> int:
        return counts.get(rid, {}).get("mumbai", 0)

    # Mars/Jupiter has no tied stretch, so the identity is exact.
    record("Mars ahead + behind accounts for every Mars/Jupiter shared-sign "
           "day, with nothing unordered",
           n("b086_mars_ahead_of_jupiter_same_sign")
           + n("b085_mars_behind_jupiter_same_sign")
           == n("b084_mars_jupiter_same_sign"),
           f"{n('b086_mars_ahead_of_jupiter_same_sign')} ahead + "
           f"{n('b085_mars_behind_jupiter_same_sign')} behind = "
           f"{n('b084_mars_jupiter_same_sign')} shared")

    # Venus/Jupiter has one, so the two directions must fall SHORT of the
    # window, and by no more than the tied stretch can touch.
    shared = n("b078_venus_jupiter_same_sign")
    ordered = (n("b079_venus_behind_jupiter_same_sign")
               + n("b080_venus_ahead_of_jupiter_same_sign"))
    record("Venus/Jupiter's ordered days fall short of its shared-sign days by "
           "exactly the tied stretch, and never exceed them",
           ordered < shared and shared - ordered <= 4,
           f"{ordered} ordered of {shared} shared; "
           f"{shared - ordered} day(s) unordered, "
           f"{EXPECTED_TIED_DAYS[('Venus', 'Jupiter')]}d tied")

    # And the flag has to be on every ordering row, for the same reason the
    # elision flag has to be on b015c's.
    ids = {r.id for r in R.REGISTRY
           if colocation.ORDER_FLAG in r.flags}
    bad = [f.rule_id for f in firings
           if f.rule_id in ids and colocation.ORDER_FLAG not in f.flags]
    record("Every ordering row declares that its order came from the ladder",
           not bad, f"{len(ids)} ordering rules, {len(bad)} undeclared rows")


def test_the_rule_layer_never_reaches_the_ephemeris() -> None:
    """No rule module may import or call the ephemeris. Checked as text.

    `base.py` states this as a design rule and `Sky` enforces it by being the
    only thing a condition receives -- but a module could still import `ephem`
    directly, and batch 2 is where the temptation first appears: the ordering
    rules want a longitude and the astronomy suite gets one by asking. The
    navamsa ladder exists so they do not have to, and this keeps it that way.
    """
    # Parsed, not grepped. This module and colocation.py both DISCUSS
    # ephem.longitude in prose -- a text search flags the explanation of the
    # rule as a breach of it.
    allowed = {"NAKSHATRAS", "SIGNS"}          # name tables, not computation
    banned_modules = {"ephem", "swisseph", "swe"}
    offenders = []
    for path in sorted((ROOT / "finastro" / "rules").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        bound: set[str] = set()                # local names for a banned module
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[-1]
                if mod in banned_modules:
                    taken = {a.name for a in node.names}
                    if not taken <= allowed:
                        offenders.append(
                            f"{path.name}:{node.lineno} imports "
                            f"{sorted(taken - allowed)} from {mod}")
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[-1] in banned_modules:
                        bound.add(a.asname or a.name.split(".")[-1])
                        offenders.append(f"{path.name}:{node.lineno} imports "
                                         f"module {a.name}")
            elif isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute) and isinstance(
                        fn.value, ast.Name) and fn.value.id in bound:
                    offenders.append(f"{path.name}:{node.lineno} calls "
                                     f"{fn.value.id}.{fn.attr}")
    record("No rule module imports or calls the ephemeris", not offenders,
           str(offenders) or "only the NAKSHATRAS/SIGNS name tables are taken "
           "from ephem, and the navamsa ladder needs nothing else")


def test_names_map_is_grounded_in_the_document() -> None:
    missing = [s for s in names.NAKSHATRA_SPELLINGS if s not in SOURCE_TEXT]
    record("Every source spelling in the name map occurs in the document",
           not missing, str(missing))
    record("The name map reaches all 27 engine nakshatras",
           set(names.NAKSHATRA_SPELLINGS.values()) == set(NAKSHATRAS),
           f"{len(names.NAKSHATRA_SPELLINGS)} spellings -> 27 names")


def test_astronomy_layer_untouched() -> None:
    """The rule layer must add nothing to the astronomy layer.

    `test_2027_astronomy.py::test_no_interpretation_leaked` bans the Step-4
    vocabulary from a record. This checks the other direction: that importing
    and running the rule layer did not write into the file it reads.
    """
    sky = Sky.load()
    banned = {"verdict", "verdict_text", "rule_id", "claim_tag", "tier",
              "evidence_source", "construction", "confidence"}
    found = set()
    for rec in sky.records:
        found |= banned & set(rec)
        for layer in ("astronomy", "panchang", "qa"):
            found |= banned & set(rec[layer])
    record("The astronomy layer carries no rule-layer field", not found,
           str(sorted(found)))


def test_configuration_coverage_is_stated_and_counted_from_the_document():
    """The 141/141 claim cannot be published alone again.

    Three things have to hold together, and each has failed at least once:

    * the count of the instrument configuration groups must come from the
      DOCUMENT, not from our own config -- a count taken from the thing being
      audited cannot fail, which is how "141 of 141" read as a coverage claim
      about the source for a day;
    * the document's count and config's count must agree, because config's
      read 17 and 29 for gold and silver against the document's 19 and 30 for
      as long as nobody re-derived them;
    * neither of those numbers may be reported on the status page or in the
      apparatus panel without the other, so this checks that both pages state
      BOTH denominators rather than trusting a hand edit to have kept them.

    A change to the source document that adds or removes a configuration group
    fails here, which is the point: the number is pinned to the document rather
    than to a memory of it.
    """
    from finastro import cfgsections as CFG

    cfg = CONF["verdict_coverage"]["unported_configuration_sections"]
    doc_counts = CFG.counts()
    doc_total = CFG.total()

    # 1. config and the document agree, group for group.
    mismatches = {b: (doc_counts[b], cfg["blocks"].get(b, {}).get("named_groups"))
                  for b in doc_counts
                  if doc_counts[b] != cfg["blocks"].get(b, {}).get("named_groups")}
    record("Config's configuration-group counts match the document's",
           not mismatches, str(mismatches))
    record("Config states the number the document counts, 58",
           cfg.get("total_named_groups") == doc_total
           and cfg.get("ported") + cfg.get("blocked") == doc_total,
           f"config says {cfg.get('total_named_groups')} groups, "
           f"{cfg.get('ported')} ported + {cfg.get('blocked')} blocked; "
           f"document says {doc_total}")
    per_inst = CFG.by_instrument()
    record("Config's per-instrument split matches the document's",
           cfg.get("per_instrument") == per_inst,
           f"config {cfg.get('per_instrument')} vs document {per_inst}")

    # 2. The two catalogues stay apart. This read "nothing is ported" until the
    #    configuration port landed; what it checks now is the invariant that
    #    made the port safe -- a configuration group is NOT a catalogue-B
    #    section, and the count that says "141 of 141" must stay unreachable
    #    from one.
    cfg_ids = set(CFG.BLOCKS)
    named = sorted(r.id for r in R.REGISTRY
                   if any(b in (r.section_title or "") for b in cfg_ids)
                   or any(b in str(r.section_title) for b in ("Configuration",)))
    record("No catalogue-B rule names a configuration section", not named,
           str(named[:5]))
    record("The configuration rules are in their own registry, not REGISTRY",
           not ({id(r) for r in config_rules.CONFIG_REGISTRY}
                & {id(r) for r in R.REGISTRY}),
           "a configuration rule reached the catalogue-B registry")
    record("A configuration group carries no catalogue-B number",
           all(r.catalogue_b is None for r in config_rules.CONFIG_REGISTRY),
           "a group was given a `b`, which would inflate sections_ported()")
    record("Catalogue B's denominator is unchanged by the port",
           len(R.sections_ported()) == len(catalogue.SECTIONS) == 141,
           f"{len(R.sections_ported())} of {len(catalogue.SECTIONS)}")
    record("Config states the ported and blocked counts the registry holds",
           cfg.get("ported") == len(config_rules.ported())
           and cfg.get("blocked") == len(config_rules.blocked_rules()),
           f"config {cfg.get('ported')}/{cfg.get('blocked')} vs registry "
           f"{len(config_rules.ported())}/{len(config_rules.blocked_rules())}")
    record("Config's per-input blocked counts match the registry's",
           dict(cfg.get("blocked_by_input") or {})
           == {k: v for k, v in config_rules.missing_input_counts().items()
               if v},
           f"config {cfg.get('blocked_by_input')} vs registry "
           f"{config_rules.missing_input_counts()}")

    # 3. Both denominators are on the face of both pages.
    status = (ROOT / "build" / "RULE_LAYER_STATUS.md")
    if status.exists():
        text = status.read_text(encoding="utf-8")
        head = text[:6000]
        n_cfg = len(config_rules.ported())
        record("The status page states the configuration denominator",
               f"{n_cfg} of {doc_total}" in head
               or f"{n_cfg}/{doc_total}" in head,
               f"no '{n_cfg} of {doc_total}' in the first 6000 chars")
        record("The status page states the catalogue-B denominator",
               "141 of 141" in head,
               "no '141 of 141' in the first 6000 chars")
        record("The status page says 141/141 is not a source-coverage claim",
               "TRUE OF CATALOGUE B" in text,
               "the caveat is not on the page")
        record("The status page names gold, silver and sugar as the affected "
               "instruments",
               all(i in text[:6000] for i in CFG.INSTRUMENTS),
               "an instrument is unnamed where the gap is stated")
    html_path = ROOT / "build" / "calendar_2027.html"
    if html_path.exists():
        h = html_path.read_text(encoding="utf-8")
        n_cfg = len(config_rules.ported())
        record("The HTML apparatus states the configuration denominator",
               f"{n_cfg}/{doc_total}" in h,
               f"no '{n_cfg}/{doc_total}' in the artifact")
        record("The HTML apparatus places it beside the blocked list",
               h.find(f"{n_cfg}/{doc_total}") > h.find("Blocked sections"),
               "the coverage statement precedes the blocked list")

    # 4. The panel quotes the scope report's READY count. Quoting a number that
    #    lives in two places is how a number drifts, so the panel's copy is read
    #    back against the report's own line rather than trusted.
    scope = ROOT / "build" / "CONFIG_SECTIONS_SCOPE.md"
    if scope.exists():
        from finastro.html_calendar import CFG_READY
        m = re.search(r"\*\*(\d+) of \d+\*\* need no new astronomy", 
                      scope.read_text(encoding="utf-8"))
        record("The apparatus panel's READY count matches the scope report",
               m is not None and int(m.group(1)) == CFG_READY,
               f"report says {m.group(1) if m else 'nothing'}, panel says "
               f"{CFG_READY}")


def test_a_horizon_rule_is_never_evaluated_once_for_both_venues() -> None:
    """The invariant that makes a per-location condition worth having.

    A rise or a set belongs to one horizon. A rule that conditions on one and
    is evaluated once would compute a single answer from a single venue's sky
    and print it against both -- and the row would still carry a location field
    naming the venue it was never evaluated at, which is worse than no field at
    all. `Rule.__post_init__` refuses that combination; this asserts it holds
    across the registry and that the refusal actually bites.
    """
    horizon_rules = [r for r in R.REGISTRY
                     if any(i.startswith("horizon/") for i in r.inputs)]
    bad = [r.id for r in horizon_rules if not r.per_location]
    record("Every rule conditioned on a rise or a set is evaluated per venue",
           bool(horizon_rules) and not bad,
           f"{len(horizon_rules)} horizon rules: "
           + ", ".join(sorted(r.id for r in horizon_rules)))

    # And the guard is a guard, not a comment: constructing the forbidden
    # combination has to fail.
    try:
        rules_base.Rule(
            id="probe", section=catalogue.B(64), rule_family="panchang/tithi",
            condition_text="probe", condition_from="title",
            inputs=("horizon/sunrise",), fn=lambda sky: [])
        ok, detail = False, "a location-blind horizon rule was ACCEPTED"
    except ValueError as exc:
        ok, detail = True, str(exc).split(":", 1)[-1].strip()[:96]
    record("A horizon rule that is not per_location is refused", ok, detail)

    graded = {r.id: r.data_certainty for r in horizon_rules}
    record("Every horizon rule carries certainty B, the weakest of its inputs",
           set(graded.values()) == {"B"}, str(sorted(set(graded.values()))))


def test_the_per_location_conditions_actually_differ_by_venue(firings) -> None:
    """The condition differs between venues, not merely the date it lands on.

    This is the whole reason `per_location` exists beside `weekdays`, and it is
    easy to state and easy to leave unchecked. A weekday rule has one sky-side
    span and two calendars. These have two spans.

    Checked where the difference is visible: the SPANS, before any calendar
    touches them. Were the Mumbai and New York span sets equal, `per_location`
    would be an expensive way of doing what `weekdays` already does.
    """
    sky = Sky.load()
    per_loc = [r for r in R.REGISTRY if r.per_location and r.fn is not None]
    record("Six sections are evaluated per venue", len(per_loc) == 6,
           ", ".join(sorted(r.id for r in per_loc)))

    same, differ = [], []
    for r in per_loc:
        m = {(s.start, s.end) for s in r.fn(sky, "mumbai")}
        n = {(s.start, s.end) for s in r.fn(sky, "new_york")}
        (same if m == n else differ).append(r.id)
    record("Every per-location condition gives a different answer at the two "
           "venues, so the flag is doing work", not same,
           f"{len(differ)} differ, {len(same)} identical"
           + (f": {same}" if same else ""))

    for rid in sorted(r.id for r in per_loc):
        days = {loc: {f.civil_date for f in firings
                      if f.rule_id == rid and f.location == loc}
                for loc in R.LOCATIONS}
        record(f"{rid}: the two venues do not produce the same dates",
               days["mumbai"] != days["new_york"],
               f"mumbai {len(days['mumbai'])}, new_york "
               f"{len(days['new_york'])}, shared "
               f"{len(days['mumbai'] & days['new_york'])}")


def test_the_kshay_and_vriddhi_rows_rest_on_emitted_sunrises() -> None:
    """A sunrise the rule counted must be a sunrise the file emitted.

    The positive form of the no-ephemeris rule, applied to the third series the
    way `test_the_panchang_rules_read_the_layer_and_not_the_ephemeris` applies
    it to the first two. Every span these rules fire on is a tithi bounded by
    two `tithi_ingress` records, and the count that selected it is a count of
    `sunrise` records at that venue -- so a reader can re-derive the row from
    the file alone, without the engine and without a horizon routine.
    """
    sky = Sky.load()
    edges = {r["time"]["t_start_utc"] for r in sky.by_class["tithi_ingress"]}
    kv = {"b066_kshay_tithi_shukla_paksha": 0,
          "b067_kshay_tithi_krishna_paksha": 0,
          "b068_vriddhi_tithi_shukla_paksha": 2,
          "b069_vriddhi_tithi_krishna_paksha": 2}
    bad_edges, bad_counts = [], []
    for rid, want in kv.items():
        r = next(x for x in R.REGISTRY if x.id == rid)
        for loc in R.LOCATIONS:
            rises = sky.sunrises(loc)
            for sp in r.fn(sky, loc):
                for end in (sp.start, sp.end):
                    if end.strftime("%Y-%m-%dT%H:%M:%SZ") not in edges:
                        bad_edges.append((rid, str(end)))
                n = sum(1 for t in rises if sp.start <= t < sp.end)
                if (want == 0 and n != 0) or (want == 2 and n < 2):
                    bad_counts.append((rid, loc, str(sp.start), n))
                if sp.value["sunrises_inside"] != n:
                    bad_counts.append((rid, loc, "detail disagrees", n))
    record("Every Kshay and Vriddhi span is bounded by two emitted tithi "
           "ingress records", not bad_edges, f"{len(bad_edges)} unbounded ends")
    record("Every Kshay span holds no emitted sunrise and every Vriddhi span "
           "holds two, at the venue it was evaluated for", not bad_counts,
           f"{len(bad_counts)} miscounted"
           + (f" e.g. {bad_counts[:2]}" if bad_counts else ""))


def test_pradosh_sits_on_an_emitted_sunset_or_says_why_not() -> None:
    """Each Pradosh row names the clause that dated it, and the clause is true.

    B64 is a resolved ambiguity with three clauses, and the status is only
    worth having if a reader can see which clause a row rests on. Every span
    carries `pradosh_clause`, and every row whose clause names a sunset has to
    land on one the file emits for that venue.
    """
    sky = Sky.load()
    r = next(x for x in R.REGISTRY if x.id == "b064_pradosh")
    seen, bad = collections.Counter(), []
    for loc in R.LOCATIONS:
        sets = set(sky.sunsets(loc))
        for sp in r.fn(sky, loc):
            clause = sp.value["pradosh_clause"]
            seen[clause] += 1
            on_sunset = sp.start in sets
            if clause.startswith("no_sunset"):
                if on_sunset or sp.value["sunsets_inside"]:
                    bad.append((loc, clause, str(sp.start)))
            elif not on_sunset:
                bad.append((loc, clause, str(sp.start)))
    record("Every Pradosh row lands on a sunset the file emits for its own "
           "venue, or names the clause that put it elsewhere", not bad,
           f"{len(bad)} inconsistent; clauses used: {dict(seen)}")
    record("All three ruled clauses are exercised, so none is dead wording in "
           "the resolution", len(seen) == 3, str(dict(seen)))


def test_b101_counts_three_of_the_weekday_it_names(firings) -> None:
    """The count is real, the dates are that weekday, and the span is theirs.

    B101 is the one section cleared by arithmetic rather than by an event
    class, so what is checked is the arithmetic: the detail says which dates
    were counted, they are all the weekday the title names, there are three of
    them, and the emitted span runs from the first to the last.
    """
    sky = Sky.load()
    r = next(x for x in R.REGISTRY
             if x.id == "b101_three_saturdays_in_shukla_paksha")
    bad, spans = [], 0
    for loc in R.LOCATIONS:
        for sp in r.fn(sky, loc):
            spans += 1
            dates = [dt.datetime.strptime(x, "%d-%b-%Y").date()
                     for x in sp.value["dates"]]
            if len(dates) != 3 or sp.value["count"] != 3:
                bad.append((loc, "count", sp.value["count"]))
            if any(x.strftime("%A") != sp.value["counted_weekday"]
                   for x in dates):
                bad.append((loc, "weekday", sp.value["dates"]))
            window = civil_day_span(dates[0], dates[-1], loc)
            if (sp.start, sp.end) != (window.start, window.end):
                bad.append((loc, "span", str(sp.start)))
    record("Every B101 span counts exactly three Saturdays and runs from the "
           "first to the last", bool(spans) and not bad,
           f"{spans} spans across both venues, {len(bad)} inconsistent"
           + (f" e.g. {bad[:2]}" if bad else ""))

    # `weekdays` stays unset on purpose, and the rows show why: the firing days
    # are every day of the counted range, not only the Saturdays.
    days = {f.civil_date.strftime("%a") for f in firings if f.rule_id == r.id}
    record("B101 fires on every weekday, because its Saturday is counted "
           "inside a window and not required of the firing day",
           len(days) == 7 and not r.weekdays,
           f"weekdays fired on {sorted(days)}; Rule.weekdays={r.weekdays}")


# --------------------------------------- 5c. batch 5, the retrograde pairs
# These recompute 2026 directly, which no rule may do and the harness may: the
# only way to ask whether a rule READ ITS PAGE RIGHT is to put the page against
# an independent computation. B87's proviso and the navamsa ladder are checked
# the same way.
def _retrograde_windows(body: str, lo, hi) -> list:
    """(start, end) UTC stretches where `body`'s longitude speed is negative.

    The carry-in matters: Jupiter is already retrograde when this range opens,
    so his first station inside it is a D and the window must be opened from the
    range's own start. `Sky.motion_spans` reconstructs the same leading state
    from the record's `_from` field; this is the ephemeris-side equivalent.
    """
    out = []
    open_at = lo if ephem.position(lo, body).retrograde else None
    for when, kind in ephem.stations(body, lo, hi):
        if kind == "R":
            open_at = when
        elif open_at is not None:
            out.append((open_at, when))
            open_at = None
    if open_at is not None:
        out.append((open_at, hi))
    return out


def _pair_windows(a: str, b: str, lo, hi) -> list:
    return [(max(a0, b0), min(a1, b1))
            for a0, a1 in _retrograde_windows(a, lo, hi)
            for b0, b1 in _retrograde_windows(b, lo, hi)
            if max(a0, b0) < min(a1, b1)]


def test_the_retrograde_pairs_reproduce_what_reproduces() -> None:
    """B82 and B83 come back; B81's printed row is another planet's.

    "Saturn and Mercury Both Retrograde" prints a 2026 row during which Saturn
    and Mercury are never both retrograde. It is Venus's retrograde window to
    within four minutes, and the Saturn-Mercury window is the row B83 prints.
    All four stations are recomputed here rather than trusted, because the
    claim is a defect in the source and a defect asserted without arithmetic is
    an opinion.
    """
    ephem.init()
    ist = dt.timedelta(hours=5, minutes=30)

    def when(cell_date: str, cell_time: str):
        h, m = cell_time.split(":")
        return dt.datetime.strptime(cell_date, "%d-%b-%y").replace(
            hour=int(h), minute=int(m), tzinfo=dt.timezone.utc) - ist

    lo = dt.datetime(2025, 12, 1, tzinfo=dt.timezone.utc)
    hi = dt.datetime(2026, 12, 31, tzinfo=dt.timezone.utc)

    bad = []
    for b, a, c in ((82, "Jupiter", "Mercury"), (83, "Mercury", "Venus")):
        row = catalogue.B(b).tables[0].rows[0]
        ps, pe = when(row[0], row[1]), when(row[2], row[3])
        wins = _pair_windows(a, c, lo, hi)
        near = [w for w in wins if abs((w[0] - ps).total_seconds()) < 1800]
        if len(near) != 1 or abs((near[0][1] - pe).total_seconds()) > 1800:
            bad.append(f"B{b}: printed {row[0]} {row[1]} -> {row[2]} {row[3]}, "
                       f"computed {wins}")
    record("B82 and B83 reproduce their printed 2026 rows to within half an "
           "hour", not bad, str(bad) or "2 rows, both ends")

    row = catalogue.B(81).tables[0].rows[0]
    ps, pe = when(row[0], row[1]), when(row[2], row[3])
    sm = _pair_windows("Saturn", "Mercury", lo, hi)
    gap = min(abs((w[0] - ps).total_seconds()) / 3600.0 for w in sm)
    record("B81's printed 2026 row is not the Saturn-Mercury window",
           gap > 60, f"nearest computed start is {gap:.1f} h away; that "
           f"window is {sm[0][0]:%d-%b %H:%M} to {sm[0][1]:%d-%b %H:%M}")

    ven = _retrograde_windows("Venus", lo, hi)
    record("B81's printed 2026 row is Venus's retrograde window, not the "
           "pair's",
           len(ven) == 1
           and abs((ven[0][0] - ps).total_seconds()) <= 600
           and abs((ven[0][1] - pe).total_seconds()) <= 600,
           f"Venus retrograde {ven[0][0]:%d-%b %H:%M} to "
           f"{ven[0][1]:%d-%b %H:%M} against printed {row[0]} {row[1]} to "
           f"{row[2]} {row[3]}")

    row83 = catalogue.B(83).tables[0].rows[0]
    qs, qe = when(row83[0], row83[1]), when(row83[2], row83[3])
    record("The Saturn-Mercury window is the row B83 prints",
           any(abs((w[0] - qs).total_seconds()) <= 180
               and abs((w[1] - qe).total_seconds()) <= 180 for w in sm),
           f"Saturn+Mercury {sm[0][0]:%d-%b %H:%M} to {sm[0][1]:%d-%b %H:%M} "
           f"against B83's {row83[0]} {row83[1]} to {row83[2]} {row83[3]}")


def test_the_pairs_zeroes_are_each_the_kind_they_claim(firings: list) -> None:
    """Three zeros, three reasons, each one checkable in the layer.

    A zero that is pinned in a table and never re-derived decays into an
    impression. B83's is the orbital period, B113's the calendar boundary and
    B107's the sky -- and the third is the one worth checking, because that
    rule looks idle and is in fact a statement about Pluto.
    """
    sky = Sky.load()
    by_id = {r.id: r for r in R.REGISTRY}
    fired = {f.rule_id for f in firings}

    venus_retro = [s for s in sky.motion_spans("Venus")
                   if s.value == "retrograde"]
    record("B83 is silent because Venus does not station in the span at all",
           not venus_retro
           and "b083_mercury_venus_both_retrograde" not in fired,
           f"{len(venus_retro)} Venus retrograde span(s) in the layer")

    dhan = [s for s in sky.spans("Mars", "nakshatra") if s.value == "Dhanishta"]
    record("B113 is silent because Mars's next Dhanishta window is in 2028",
           len(dhan) == 1 and dhan[0].start.year == 2028
           and "b113_mars_in_dhanishta" not in fired,
           f"Mars in Dhanishta {dhan[0].start:%d-%b-%Y} to "
           f"{dhan[0].end:%d-%b-%Y}")

    shr = [s for s in sky.spans("Venus", "nakshatra") if s.value == "Shravana"]
    pluto = [s for s in sky.spans("Pluto", "nakshatra")
             if s.value == "Shravana"]
    alone = by_id["b107_venus_alone_in_shravana"].fn(sky)
    record("B107 is silent because Pluto holds Shravana across both of Venus's "
           "2027 visits, though Venus does visit it twice",
           len(shr) == 2 and not alone
           and all(any(p.start <= s.start < p.end for p in pluto) for s in shr),
           f"Venus in Shravana {len(shr)} time(s), {len(alone)} alone "
           f"window(s); Pluto's Shravana span "
           + (f"{pluto[0].start:%d-%b-%Y} to {pluto[0].end:%d-%b-%Y}"
              if pluto else "absent"))


def test_both_halves_of_a_configuration_verdict_are_carried() -> None:
    """THE CHECK THE PORT WAS REQUIRED TO HAVE BEFORE IT STARTED.

    A configuration verdict is stated in two elements -- the block's `<h2>`
    carries the direction, the group heading carries the condition -- and a
    port that sliced only the group heading would have produced a null verdict
    for every group whose heading states no direction. That failure renders as
    a blank cell, not as an error, which is what makes it the same shape as
    `family` matching one of its two readings and attaching five of eleven.

    Four things are asserted, and the third is the counterfactual: it runs the
    naive slice and shows how many verdicts it would have lost, so the number
    the check is protecting is on the record rather than implied.
    """
    reg = config_rules.CONFIG_REGISTRY
    nulls = [r.id for r in reg if r.verdict_text is None]
    record("Every configuration rule carries a verdict", not nulls,
           f"{len(nulls)} null: {nulls[:4]}")

    unattributed = [r.id for r in reg if r.verdict_text and not r.verdict_from]
    record("Every configuration verdict names where it was sliced from",
           not unattributed, str(unattributed[:4]))

    # The counterfactual. `split_statement` on the group title alone is exactly
    # what a catalogue-B-shaped port would have done.
    naive_null = [g.key for g in config_catalogue.GROUPS
                  if catalogue.split_statement(g.title)[1] is None]
    held = {r.section.key: r for r in reg}
    recovered = [k for k in naive_null if held[k].verdict_text is not None]
    record("Every verdict the naive slice would have lost is recovered",
           len(naive_null) > 0 and len(recovered) == len(naive_null),
           f"{len(naive_null)} group headings yield nothing after their own "
           f"dash; {len(recovered)} of them still carry a verdict")
    #  Where the recovered verdicts came from. Most are the block's `<h2>`; a
    #  few are a slice of the group heading at a marker that is not a dash
    #  ("... Is Bullish (short-term bounce)", "... Increases Volatility ..."),
    #  which the naive split would have missed just as completely.
    where = collections.Counter(held[k].verdict_from for k in naive_null)
    record("No recovered verdict is unattributed", None not in where,
           f"recovered from {dict(where)}")
    from_block = [r.section.key for r in reg if r.verdict_from == "block_h2"]
    record("The block heading is what most of them were recovered from",
           where.get("block_h2", 0) >= 0.8 * len(naive_null)
           and len(from_block) >= where.get("block_h2", 0),
           f"{where.get('block_h2', 0)} of {len(naive_null)} from the block "
           f"heading; {len(from_block)} rules take the block's word overall")

    # And the split is not a fudge: a verdict taken from the block heading must
    # be a substring of that heading, one taken from the title a substring of
    # the title.
    misattributed = [
        r.id for r in reg
        if (r.verdict_from == "block_h2"
            and r.verdict_text not in r.section.block.h2)
        or (r.verdict_from == "title" and r.verdict_text not in r.section.title)]
    record("Each configuration verdict is in the element it claims",
           not misattributed, str(misattributed[:4]))


def test_the_silent_verdict_check_actually_bites() -> None:
    """A guard nobody has seen fail is a guard nobody has tested.

    Three refusals, each a way the same elision could reach the registry: a
    null verdict under a directional block, a verdict that is not in the
    document, and a verdict with no attribution. All three must raise
    `SilentVerdict` rather than pass, or the check above is decoration.
    """
    g = config_catalogue.G("silver-bullish", 5)          # "Venus Mars Together"

    def refuses(verdict, src) -> bool:
        try:
            config_catalogue.check_verdict("probe", g, verdict, src)
        except config_catalogue.SilentVerdict:
            return True
        return False

    record("The probe group's block does state a direction",
           g.block.is_directional, f"{g.block.h2!r} is not directional")
    record("A null verdict under a directional block is refused",
           refuses(None, "block_h2"), "it was accepted")
    record("A verdict that is not in the document is refused",
           refuses("Strongly Bullish For Silver", "block_h2"),
           "a typed verdict was accepted")
    record("A verdict with no attribution is refused",
           refuses("Bullish", None), "an unattributed verdict was accepted")
    record("A verdict that IS in the block heading is accepted",
           not refuses(g.block.verdict, "block_h2"),
           "the check rejects a correct verdict")


def test_configuration_text_is_a_substring_of_the_document() -> None:
    """Verbatim or absent, the rule catalogue B is held to.

    Every condition and every verdict on a configuration rule is checked as a
    literal substring of `data/source_2026.html`, flattened the way the
    catalogue-B check flattens it. A string that is not in the document is a
    string somebody typed.
    """
    doc = _flat(SOURCE_TEXT)
    bad_cond = [r.id for r in config_rules.CONFIG_REGISTRY
                if _flat(r.condition_text) not in doc]
    bad_verd = [r.id for r in config_rules.CONFIG_REGISTRY
                if r.verdict_text and _flat(r.verdict_text) not in doc]
    record("Every configuration condition is in the document", not bad_cond,
           str(bad_cond[:4]))
    record("Every configuration verdict is in the document", not bad_verd,
           str(bad_verd[:4]))


def test_every_configuration_group_is_registered_once() -> None:
    """58 groups, 58 rules, and the document decides the 58.

    The count comes from `cfgsections` reading the source, not from a list
    here, so a group added to or removed from the document fails this rather
    than silently changing the coverage claim.
    """
    from finastro import cfgsections as CFG

    reg = config_rules.CONFIG_REGISTRY
    keys = [r.section.key for r in reg]
    record("Every configuration group is registered exactly once",
           len(keys) == len(set(keys)) == CFG.total() == 58,
           f"{len(keys)} rules, {len(set(keys))} distinct, "
           f"{CFG.total()} groups in the document")
    record("Every blocked configuration rule names an input from the closed set",
           all(r.missing_inputs
               and all(k in config_rules.MISSING_INPUTS
                       for k in r.missing_inputs)
               for r in config_rules.blocked_rules()),
           "a blocked rule names no input, or one outside MISSING_INPUTS")
    survey = set(config_rules.SURVEY_INPUTS)
    beyond = sorted({k for r in config_rules.blocked_rules()
                     for k in r.missing_inputs if k not in survey})
    record("Inputs beyond the scope survey's five are named as such",
           beyond == ["vedha_wheel"],
           f"blocked on {beyond} outside the survey's five")


def test_configuration_zero_firings_are_each_the_kind_they_claim(
        cfg_firings) -> None:
    """A ported rule that never fires is either a quiet year or a broken port.

    Twelve of the 38 produce no 2027 row. Each is pinned by name with the
    reason, so a thirteenth appearing -- or one of these starting to fire --
    fails here instead of being read as normal.
    """
    expected = {
        "cfg_gold_bullish_01_mars_through_taurus":
            "Mars is never in Taurus in 2027",
        "cfg_gold_bullish_04_jupiter_in_gemini":
            "Jupiter is never in Gemini in 2027",
        "cfg_gold_bullish_12_mars_in_pushya":
            "Mars never occupies Pushya in 2027",
        "cfg_silver_bullish_09_sun_moon_together_on_sankranti":
            "no 2027 Sankranti finds the Moon already in the sign entered",
        "cfg_silver_bullish_11_mercury_combust_retrograde_vedh_moon":
            "five residencies have no printed Retrograde key, one targets "
            "Abhijeet which the 27-division does not emit, and the one fully "
            "computable residency did not coincide with the Moon in Rohini",
        "cfg_silver_bullish_12_venus_combust_in_west":
            "Venus has one combustion in the span and it is East",
        "cfg_silver_bullish_19_mars_rising":
            "Mars has no visibility/rise record in the span",
        "cfg_silver_bullish_20_saturn_neptune_conjunction":
            "the pair is scanned and has no exact conjunction in the span",
        "cfg_silver_bearish_04_mars_vargottam_in_cancer":
            "Mars holds Cancer with the navamsa in Pisces throughout",
        "cfg_sugar_bullish_04_moon_joins_combust_mercury_in_west":
            "three West combustions, and the Moon's Mercury-sharing window "
            "falls just outside each",
        "cfg_sugar_bullish_05_retrograde_mercury_combust_in_cancer":
            "Mercury holds Cancer 30-Jul to 14-Aug and is direct throughout",
        "cfg_sugar_bearish_01_jupiter_or_mars_in_three_stars":
            "Jupiter reaches neither Hasta nor Shravana; Mars enters Dhanishta "
            "on 25-Jan-2028, in the carry-out",
    }
    zero = {r.id for r in config_rules.zero_firing(cfg_firings)}
    record("The configuration zero-firing set is exactly the pinned one",
           zero == set(expected),
           f"unexpected {sorted(zero - set(expected))[:3]} / "
           f"now firing {sorted(set(expected) - zero)[:3]}")


def test_configuration_rules_obey_the_frame_rules_catalogue_b_obeys(
        cfg_firings) -> None:
    """The invariants that make a row readable, applied to the second registry.

    Nothing here is new doctrine. It is the catalogue-B harness's own checks
    run against the configuration rules, because an invariant enforced on one
    registry and not the other is an invariant with a hole in it.
    """
    reg = config_rules.CONFIG_REGISTRY
    horizon = [r.id for r in reg
               if any(i.startswith("horizon/") for i in r.inputs)
               and not r.per_location]
    record("No configuration rule takes a horizon without being per-location",
           not horizon, str(horizon[:3]))

    bad_days = [f.rule_id for f in cfg_firings if f.civil_date.year != Y]
    record("Every configuration firing lands in the generated year",
           not bad_days, str(sorted(set(bad_days))[:3]))

    allowed = {r.id: r.locations for r in reg}
    wrong_venue = [f.rule_id for f in cfg_firings
                   if f.location not in allowed[f.rule_id]]
    record("No configuration firing carries a venue its rule excludes",
           not wrong_venue, str(sorted(set(wrong_venue))[:3]))

    weekday_rules = {r.id: r.weekdays for r in reg if r.weekdays}
    off = [f.rule_id for f in cfg_firings
           if f.rule_id in weekday_rules
           and f.civil_date.weekday() not in weekday_rules[f.rule_id]]
    record("Every weekday-conditioned configuration firing is on that weekday",
           not off, str(sorted(set(off))[:3]))

    resolved = [r for r in reg if r.status == "resolved_ambiguity"]
    record("Every resolved configuration rule carries its rejected readings",
           all(r.ambiguity and r.resolution and r.rejected_readings and r.flags
               for r in resolved),
           f"{len(resolved)} resolved rules")


# ------------------------------------------- 20. row kinds and the base track
#: The rendered calendar, read back from disk. These checks are aimed at the
#: ARTIFACT and not at the code that produced it, which is the one shape of
#: check that has caught every silent defect this build has recorded: a
#: per-family count, a per-total count and a spot check all passed on the
#: section-level label bug, and only a per-rule census of the emitted file saw
#: it. The same reasoning applies here with more force, because a base-track row
#: absorbed into `no_rule` would leave every count in the file looking normal.
CALENDAR_JSON = ROOT / "build" / "calendar_2027.json"


def _calendar() -> dict:
    return json.loads(CALENDAR_JSON.read_text(encoding="utf-8"))


def test_row_kind_is_on_every_row_and_the_base_track_carries_no_verdict():
    """`row_kind` is required, and an event row cannot acquire a verdict.

    THE DISCRIMINATOR IS A PRECONDITION, NOT A FOLLOW-UP. It was added to all
    6,677 verdict rows before the first base-track row existed, because a
    calendar that gained 405 rows without one would have had `records`,
    `by_tier.no_rule` and `rows_without_verdict` all change denominator while
    still looking like the figures they had been.
    """
    from finastro import basetrack

    doc = _calendar()
    rows = doc["rows"]
    kinds = {v["id"] for v in CONF["row_kinds"]["values"]}

    missing = [i for i, r in enumerate(rows) if not r.get("row_kind")]
    record("Every calendar row carries a non-null row_kind",
           not missing, f"{len(rows)} rows, {len(missing)} without")

    outside = sorted({r["row_kind"] for r in rows} - kinds)
    record("Every row_kind is one the config names",
           not outside,
           f"config {sorted(kinds)}, rows "
           f"{sorted({r['row_kind'] for r in rows})}")

    ev = [r for r in rows if r["row_kind"] == "event"]
    vr = [r for r in rows if r["row_kind"] == "verdict"]
    record("The two populations are the sizes the config states",
           len(ev) == CONF["row_kinds"]["base_track"]["count"]
           and len(ev) + len(vr) == len(rows),
           f"{len(vr)} verdict + {len(ev)} event = {len(rows)}")

    # THE NEGATIVE HALF, and the half that bites. `BaseEvent` has no attribute
    # to hold any of these, so the only way one could appear is a dict written
    # by hand downstream -- which is exactly what a renderer is.
    leaked = sorted({k for r in ev for k in r
                     if k in basetrack.FORBIDDEN_FIELDS})
    record("No event row carries an instrument, a tier or a verdict -- "
           "not null, ABSENT",
           not leaked,
           f"forbidden keys present: {leaked}" if leaked
           else f"{len(basetrack.FORBIDDEN_FIELDS)} keys checked on "
                f"{len(ev)} rows")

    record("Every event row's evidence_source is `none`",
           all(r.get("evidence_source") == "none" for r in ev),
           str(sorted({r.get("evidence_source") for r in ev})))

    # The absorption this was built to prevent, stated as a number. An event
    # row that gained a derived tier would get `no_rule` -- tier_derivation
    # maps (none, null) there -- and 405 rows would vanish into 3,285.
    no_rule = sum(1 for r in vr if r["tier"] == "no_rule")
    record("`no_rule` counts verdict rows only, and did not grow by 405",
           no_rule == doc["meta"]["verdict_rows"]["by_tier"].get("no_rule"),
           f"no_rule {no_rule} over {len(vr)} verdict rows; the base track's "
           f"{len(ev)} are not in it")

    # Every event row names the record it came from, which is the whole of the
    # rejoinability claim: a reader matches on a key, not on name and date.
    astro = {r["id"] for r in json.loads(
        (ROOT / "build" / "astronomy_2027.json").read_text(
            encoding="utf-8"))["records"]}
    orphan = [r["record_id"] for r in ev if r["record_id"] not in astro]
    record("Every event row names a record that exists in the astronomy layer",
           not orphan, f"{len(ev)} rows, {len(orphan)} unmatched")

    classes = set(CONF["row_kinds"]["base_track"]["event_classes"])
    record("The base track carries the ten core classes and no others",
           {r["event_class"] for r in ev} <= classes,
           str(sorted({r["event_class"] for r in ev})))

    excluded = set()
    for group in CONF["row_kinds"]["base_track"]["excluded"].values():
        excluded |= set(group["classes"])
    record("No panchang ingress and no sunrise or sunset reached a row",
           not ({r["event_class"] for r in ev} & excluded),
           f"excluded: {sorted(excluded)}")


def test_a_row_without_an_instant_carries_no_clock_time():
    """STRUCTURAL, and checked against the artifact anyway.

    `timezones.DateStamp` has no time attribute, so the renderer cannot print
    one on a row without an instant -- it raises AttributeError instead. This
    check exists because the guarantee lives in one function and the file
    outlives it.

    The negative half is the one that matters: not only "no row without an
    instant has a time" but "every row WITH a time has an instant", so a later
    renderer cannot restore the old behaviour by stamping everything again.
    """
    doc = _calendar()
    rows = doc["rows"]
    reasons = set(CONF["row_kinds"]["time_fields"]["instant_precision"]
                  ["no_instant_reason"]["values"])

    timed = [r for r in rows if r["time_ist"]]
    untimed = [r for r in rows if not r["time_ist"]]

    bad = [r for r in untimed if r["time_et"] or r["et_offset"]
           or r["date_et"] or r["day_shift"]]
    record("A row with no IST time has no ET time, offset, ET date or day shift",
           not bad,
           f"{len(untimed)} untimed rows, {len(bad)} with a stray Eastern field")

    unexplained = [r["event"] for r in untimed if not r["no_instant_reason"]]
    record("Every row without a clock time says WHY",
           not unexplained,
           f"reasons present: "
           f"{sorted({r['no_instant_reason'] for r in untimed})}")

    outside = sorted({r["no_instant_reason"] for r in untimed} - reasons)
    record("Every no_instant_reason is one the config names",
           not outside, f"config: {sorted(reasons)}")

    stray = [r["event"] for r in timed if r["no_instant_reason"]]
    record("No row carries BOTH a clock time and a reason for having none",
           not stray, f"{len(timed)} timed rows, {len(stray)} contradictory")

    # The population this was built for, pinned by MEASUREMENT rather than by a
    # rule about the printed string. 662 verdict rows had no instant; one row --
    # b102 on 03-Oct-2027, a nakshatra ingress at 00:00:21 IST -- prints
    # `00:00 IST` and IS an instant, and no rule phrased over the display string
    # could have separated them.
    midnight = [r for r in timed if r["time_ist"] == "00:00 IST"]
    # Its instant is on `t_start_utc`, not `t_utc`: b102 conditions on a
    # nakshatra SPAN, and the span's start is the ingress. The twenty-one
    # seconds are what make it an event and not a midnight.
    record("Exactly one row still prints 00:00 IST, and it is a real instant",
           len(midnight) == 1
           and (midnight[0]["t_utc"] or midnight[0]["t_start_utc"])
           == "2027-10-03T18:30:21Z",
           f"{len(midnight)} rows: "
           f"{[(r['event'], r['t_utc'] or r['t_start_utc']) for r in midnight]}")

    both = [r["event"] for r in rows if r["t_utc"] and r["t_start_utc"]]
    neither = [r["event"] for r in rows
               if not r["t_utc"] and not r["t_start_utc"]]
    record("Every row carries either t_utc or t_start_utc, never both and "
           "never neither",
           not both and not neither,
           f"{sum(1 for r in rows if r['t_utc'])} instant rows, "
           f"{sum(1 for r in rows if r['t_start_utc'])} span rows")

    eclipses = [r for r in rows if r.get("event_class") == "eclipse"]
    record("Every eclipse row names its contacts and prints no bare time",
           bool(eclipses) and all(
               not r["time_ist"]
               and r["no_instant_reason"] == "named_contacts"
               and [c["contact"] for c in r["contacts"]]
               == ["first_contact", "maximum"]
               for r in eclipses),
           f"{len(eclipses)} eclipse rows, each naming first contact and "
           f"maximum")


def test_every_meta_count_is_split_by_row_kind():
    """No bare count in `meta` except the grand total, which names its split.

    `records` was 6,677 and meant verdict rows because there were no others. It
    is 7,082 now. A consumer reading it as a verdict count would be wrong by 405
    and would have no way to find out.
    """
    doc = _calendar()
    meta, rows = doc["meta"], doc["rows"]

    record("meta.records is the total over BOTH kinds, with the split beside it",
           meta["records"] == len(rows)
           and sum(meta["records_by_row_kind"].values()) == meta["records"],
           f"{meta['records']} = {meta['records_by_row_kind']}")

    vr = [r for r in rows if r["row_kind"] == "verdict"]
    ev = [r for r in rows if r["row_kind"] == "event"]
    record("meta.verdict_rows counts verdict rows and nothing else",
           meta["verdict_rows"]["total"] == len(vr)
           and sum(meta["verdict_rows"]["by_instrument"].values()) == len(vr)
           and sum(meta["verdict_rows"]["by_tier"].values()) == len(vr),
           f"{meta['verdict_rows']['total']} rows, by_instrument and by_tier "
           f"both summing to it")

    record("meta.event_rows counts event rows and states that it has no tier",
           meta["event_rows"]["total"] == len(ev)
           and meta["event_rows"]["by_tier"] is None
           and sum(meta["event_rows"]["by_event_class"].values()) == len(ev),
           f"{meta['event_rows']['total']} rows over "
           f"{len(meta['event_rows']['by_event_class'])} event classes")

    t = meta["time"]
    record("meta.time accounts for every row, timed and untimed",
           t["rows_with_a_clock_time"] + t["rows_without"] == len(rows)
           and sum(t["by_no_instant_reason"].values()) == t["rows_without"],
           f"{t['rows_with_a_clock_time']} timed + {t['rows_without']} untimed "
           f"= {len(rows)}; reasons {t['by_no_instant_reason']}")

    # The empty-day figure, MEASURED rather than asserted, and not the number
    # the base-track argument assumed: 105 days carry no event row and zero
    # carry no row at all, because tier_4's verdict-null USDINR rows blanket
    # every day of the year. Absence is reportable through `row_kind` and only
    # through it.
    cfgd = CONF["row_kinds"]["base_track"]["empty_days_are_output_not_gaps"]
    have_ev = {r["date"] for r in ev}
    day, last, n = dt.date(Y, 1, 1), dt.date(Y, 12, 31), 0
    while day <= last:
        n += day.strftime("%d-%b-%Y") not in have_ev
        day += dt.timedelta(days=1)
    record("The empty-day figures in config are the ones the build produces",
           n == cfgd["days_with_no_event_row"]
           and meta["days"]["days_with_no_row_of_any_kind"]
           == cfgd["days_with_no_row_of_any_kind"],
           f"{n} days carry no event row; "
           f"{meta['days']['days_with_no_row_of_any_kind']} carry no row at all")


def main() -> int:
    sky = Sky.load()
    firings = R.fire(R.REGISTRY, sky)
    print(f"rules: {len(R.REGISTRY)}   "
          f"sections touched: {len(R.sections_ported())}/141   "
          f"firings: {len(firings)}\n"
          + "   ".join(f"{s}: {len(R.by_status(s))}"
                       for s in R.base.STATUSES) + "\n")

    test_catalogue()
    test_every_rule_is_traceable()
    test_axes_and_tier_derivation()
    test_labels_are_from_the_config_vocabulary()
    test_source_probability_attaches_per_rule_and_not_per_section()
    test_blocked_and_ambiguous(firings)
    test_resolved_ambiguities_are_marked_as_reconstructions(firings)
    test_the_elision_occurs_exactly_once_in_the_document()
    test_the_moon_is_what_a_bare_nakshatra_name_means()
    test_panchak_is_the_moon_in_aquarius_or_pisces()
    test_the_weekday_family_against_the_sources_own_2026_tables()
    test_weekday_conditions_are_read_from_the_title_and_applied_per_location(
        firings)
    test_the_tithi_and_yoga_series_cleared_what_batch_three_said_they_would(firings)
    test_the_panchang_rules_read_the_layer_and_not_the_ephemeris()
    test_a_horizon_rule_is_never_evaluated_once_for_both_venues()
    test_the_per_location_conditions_actually_differ_by_venue(firings)
    test_the_kshay_and_vriddhi_rows_rest_on_emitted_sunrises()
    test_pradosh_sits_on_an_emitted_sunset_or_says_why_not()
    test_b101_counts_three_of_the_weekday_it_names(firings)
    test_the_final_dash_titles_would_have_lost_their_condition()
    test_b87s_proviso_is_a_condition_the_document_itself_obeys()
    test_no_ported_verdict_swallows_a_scoping_colon()
    test_shar_is_the_latitude_sign_and_not_the_declination()
    test_the_apsis_rules_fire_on_emitted_apsides_and_not_on_a_threshold()
    test_kaal_sarp_yog_is_empty_under_both_its_readings()
    test_hemisphere_is_blocked_on_the_equinox_and_says_so()
    test_the_retrograde_pairs_reproduce_what_reproduces()
    test_the_pairs_zeroes_are_each_the_kind_they_claim(firings)
    test_firings(firings)
    test_outer_pair_rules_come_from_the_documents_own_tables()
    test_the_navamsa_ladder_agrees_with_the_ephemeris()
    test_ordering_rules_reconstruct_their_own_shared_sign_window(firings)
    test_the_rule_layer_never_reaches_the_ephemeris()
    test_combust_family_declares_its_narrowing()
    test_combust_windows_match_the_source_duration_convention()
    test_names_map_is_grounded_in_the_document()
    test_astronomy_layer_untouched()
    test_configuration_coverage_is_stated_and_counted_from_the_document()

    # The configuration port. Fired into its own list: the two
    # registries are separate everywhere else and mixing them here
    # would be the one place the separation could quietly fail.
    cfg_firings = R.fire(config_rules.CONFIG_REGISTRY, sky)
    test_both_halves_of_a_configuration_verdict_are_carried()
    test_the_silent_verdict_check_actually_bites()
    test_configuration_text_is_a_substring_of_the_document()
    test_every_configuration_group_is_registered_once()
    test_configuration_zero_firings_are_each_the_kind_they_claim(
        cfg_firings)
    test_configuration_rules_obey_the_frame_rules_catalogue_b_obeys(
        cfg_firings)

    # The rendered calendar, checked as an ARTIFACT. Last because it needs
    # build/calendar_2027.json on disk: run `python build_2027.py` first, or
    # these read whatever the previous render left behind, which is its own
    # kind of stale denominator.
    if CALENDAR_JSON.exists():
        test_row_kind_is_on_every_row_and_the_base_track_carries_no_verdict()
        test_a_row_without_an_instant_carries_no_clock_time()
        test_every_meta_count_is_split_by_row_kind()
    else:
        record("The rendered calendar is on disk to be checked", False,
               f"{CALENDAR_JSON} missing; run python build_2027.py")

    width = max(len(n) for n, _, _ in _results)
    failed = 0
    for name, status, detail in _results:
        failed += status == FAIL
        print(f"[{status}] {name.ljust(width)}  {detail}")
    print(f"\n{len(_results) - failed}/{len(_results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
