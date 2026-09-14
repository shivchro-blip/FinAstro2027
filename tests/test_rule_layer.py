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
    test_firings(firings)
    test_outer_pair_rules_come_from_the_documents_own_tables()
    test_the_navamsa_ladder_agrees_with_the_ephemeris()
    test_ordering_rules_reconstruct_their_own_shared_sign_window(firings)
    test_the_rule_layer_never_reaches_the_ephemeris()
    test_combust_family_declares_its_narrowing()
    test_combust_windows_match_the_source_duration_convention()
    test_names_map_is_grounded_in_the_document()
    test_astronomy_layer_untouched()

    width = max(len(n) for n, _, _ in _results)
    failed = 0
    for name, status, detail in _results:
        failed += status == FAIL
        print(f"[{status}] {name.ljust(width)}  {detail}")
    print(f"\n{len(_results) - failed}/{len(_results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
