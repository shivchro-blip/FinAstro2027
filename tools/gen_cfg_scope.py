"""Generate build/CONFIG_SECTIONS_SCOPE.md -- what porting the configuration
sections would take, per group, so the work can be scoped instead of guessed at.

The group list and the counts come from the document (`finastro.cfgsections`).
The CLASS of each group's condition is assigned here, by hand, one group at a
time, with the evidence for the call in the `why` column -- because the
classification is a judgement about the source's words and a generated guess
would be exactly the kind of plausible-looking answer this project keeps
catching. What IS generated is the accounting: which groups fall in which class,
how many per instrument, and which classes the existing astronomy layer can
already serve.

NOTHING HERE PORTS ANYTHING. This is a report.
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.cfgsections import BLOCKS, groups, total, by_instrument  # noqa: E402

OUT = ROOT / "build" / "CONFIG_SECTIONS_SCOPE.md"

# ---------------------------------------------------------------------------
# Class codes. The question a class answers: can this group's CONDITION be
# computed from the astronomy layer as it stands?
#
#   READY      yes -- the primitive is emitted and already used by a
#              catalogue-B rule of the same shape.
#   VALENCE    no -- needs a benefic/malefic classification of the bodies,
#              which the source never states. The binding constraint on B19,
#              B116 and B117 today.
#   VISIBILITY no -- needs a first-sighting / darshan computation that Step 3
#              tested and rejected. `swe.heliacal_ut` was 9-10 days out against
#              the source's own Venus rise dates.
#   LUNARNAV   was considered and has NO members here. The Moon's navamsa
#              ingress series (which blocks B71's remark and stops the navamsa
#              ladder ranking the Moon) does not bind any configuration group:
#              the two Moon groups are the darshan sighting, and "Moon Joins
#              Combust Mercury" needs only the Moon's POSITION at the combustion
#              instants, which the nakshatra series carries. Recorded because a
#              near-miss that is silently dropped looks like an oversight later.
#   MONTHSYS   no -- needs the lunar month system confirmed amanta vs
#              purnimanta. `month_system_confirmation` is open in config and
#              this is the second section it bounds.
#   ASPECTORB  yes in principle -- the aspect machinery exists and is validated
#              against B41/B42/B47's printed rows; the ORB the source uses for
#              "aspected by" is not stated, and `aspect_orbs` is open. Portable
#              the moment that is ruled on, not before.
#   NOTABLED   no condition to port -- the source prints a title and no dated
#              window, so there is nothing to register a rule for. Not a
#              missing input; a missing table.
#
# A group may carry more than one class; the report shows the most binding.
# Same input is what makes a batch a batch.
CLASS_CODES = {
    "READY": "computable from the astronomy layer today",
    "VALENCE": "needs a benefic/malefic classification (unstated in the source)",
    "VISIBILITY": "needs a first-sighting computation the layer rejected on evidence",
    "MONTHSYS": "needs the lunar month system confirmed",
    "ASPECTORB": "needs the aspect orb ruled on (`aspect_orbs` is open)",
    "NOTABLED": "the source prints no dated window -- nothing to port",
}

# ---------------------------------------------------------------------------
# block -> [(title regex, class, why)]. Matched in order; first match wins.
R = {
    # ------------------------------------------------------------ GOLD BULLISH
    "gold-bullish": [
        (r"^When Mars Passes Through Taurus$", "READY",
         "a sign residency plus the `vargottama` field the layer already puts on "
         "every positional record (config `vargottam.engine_field`)"),
        (r"^When Sun in Libra Aspected by Other Malefics$", "VALENCE",
         "the window is Mars's aspect to the Sun and the aspect layer has it; "
         "which aspects count as MALEFIC is what is unstated -- the same absence "
         "that blocks B19, B116 and B117"),
        (r"^Rahu Mars Together in Any Sign$", "READY",
         "`residency/same_sign`, already ported for B84/B93 and the B41/B47 "
         "conjunction families"),
        (r"^Jupiter Enters Gemini$", "READY",
         "read as the sign residency it is: the source's own row is dated "
         "05-Dec-25 to 02-Jun-26, which is a window in Gemini and not the "
         "ingress instant"),
        (r"^When Malefic Planets Do Vedh of", "VALENCE",
         "a 20-row vedha table; the vedha wheel exists (`vedha/nakshatra`) but "
         "the row SELECTION is 'malefic planets', so the valence is binding"),
        (r"^If Mars is Aspected by Saturn and Jupiter is Retrograde$", "READY",
         "a two-body aspect plus the `motion` field on every record; both exist "
         "and both are already used by catalogue-B rules"),
        (r"^Sun on Bharni, Kritika, Punarvasu or Pushya and Not Aspected by Benefic",
         "VALENCE",
         "explicitly negated on a BENEFIC aspect, and the note adds 'more "
         "bullish if aspected by malefic'. Both directions need the valence"),
        (r"^Moonrise on Monday or Friday", "VISIBILITY",
         "a two-row Friday/Monday table with no sign or star -- the SIGHTING "
         "class, the one B62 is blocked on, not the Moon's daily rise"),
        (r"^Moonrise in Libra", "VISIBILITY",
         "same sighting class; carries Sign and Nakshatra columns, so the "
         "sighting falls on a day the Moon is in Libra and Swati"),
        (r"^Sun Moon on the Same Degree", "READY",
         "the layer emits per-record longitudes and the lunation series, so the "
         "instant the two agree is readable rather than scanned for"),
        (r"^Venus in Rohini Nakshtra$", "READY",
         "`residency/planet_nakshatra`, the shape B89 and B113 already use"),
        (r"^Mars in Pushya Nakshtra$", "READY", "same as above, different body"),
        (r"^Aquarius Sun's Transgression, if Happens on a Friday$", "READY",
         "the Sankranti series is ported as B1 and carries the weekday on every "
         "record"),
    ],
    # ------------------------------------------------------------ GOLD BEARISH
    "gold-bearish": [
        (r"^Rise of Jupiter in Any Sign", "READY",
         "`visibility/rise` from the combustion class, with its `direction` "
         "flag -- the same primitive B15's rise rules use"),
        (r"^Saturn or Mercury in Gemini", "READY",
         "a sign residency; the printed row names Mercury, and the rule is the "
         "same shape either way"),
        (r"^Vedh by Benefics of Punarvasu", "VALENCE",
         "a 12-row vedha table selected on BENEFICS -- the mirror of the "
         "bullish block's malefic table, and the same missing input"),
        (r"^Mercury Rise in West$", "READY",
         "`visibility/rise` filtered on `direction == west`; exactly what "
         "`b015b_venus_rise_west` already does for Venus"),
        (r"^Moon Darshan on Saturday$", "VISIBILITY",
         "darshan is the sighting; B62 is the same computation and is blocked"),
        (r"^Venus in Punarvasu Nakshtra$", "READY",
         "`residency/planet_nakshatra`"),
    ],
    # ---------------------------------------------------------- SILVER BULLISH
    "silver-bullish": [
        (r"^Turning Dates . Shukla Shashti", "READY",
         "Shukla Shashti is tithi 6 of the bright fortnight and `tithi_ingress` "
         "is emitted; the impact window to Purnima is a span between two tithis"),
        (r"^Retrograde Mercury or Jupiter Increases Volatility", "READY",
         "`motion` plus the station series; `motion/both_retrograde` is already "
         "ported for B81-B83"),
        (r"^Sun in Pushya or Dhanistha Without Benefic Planet", "VALENCE",
         "negated on a BENEFIC presence -- valence again"),
        (r"^Mars Itself in Aquarius", "NOTABLED",
         "the source prints no dated window; its own note says the condition is "
         "'noted alongside Rahu-Mars conjunction in Aquarius below', which is "
         "gold-bullish's table and not a condition of its own"),
        (r"^Venus Mars Together$", "READY", "`residency/same_sign`, ported"),
        (r"^Sun Mars Together$", "READY", "same"),
        (r"^Rahu Mars Together in Any Sign", "READY",
         "same, and the starred sub-window is a nakshatra residency the layer "
         "carries"),
        (r"^Moon Darshan on Friday/Saturday", "VISIBILITY", "the sighting class"),
        (r"^Sun and Moon Together on Sankranti", "READY",
         "the Sankranti series plus the lunation series; both emitted"),
        (r"^Mercury or Jupiter Do Vedh of Venus$", "READY",
         "the vedha wheel is ported for B133 and the 96 printed rows resolve "
         "through it; both bodies' classes are calibrated and overdetermined"),
        (r"^Mercury Combust and Retrograde Does Mutual Vedh with Moon$", "READY",
         "a combustion span, the retrograde sense, and the Moon's nakshatra -- "
         "all three emitted; the Moon needs no speed class here, only its "
         "position, which the nakshatra series gives"),
        (r"^Venus Combust in West", "READY",
         "`combust_spans` filtered on the west direction, ported as B15"),
        (r"^Whenever Jupiter or Mercury Turns Direct", "READY",
         "the station series is emitted and reproduces the source's own "
         "directions"),
        (r"^Shukla Paksh of 16 Days or Krishna Paksh of 14 Days", "READY",
         "the tithi ingress series gives both pakshas' lengths directly"),
        (r"^Only Sun Mercury or Moon Mercury Alone in Any Sign", "READY",
         "`residency/alone_in_sign`, already ported as B16"),
        (r"^Mercury Jupiter Both Retrograde$", "READY",
         "`motion/both_retrograde`, ported"),
        (r"^Retrograde Mercury Once Goes Combust", "READY",
         "the combustion spans carry direction and the records carry `motion`"),
        (r"^Sun Eclipse in Falgun or Jyestha on Tuesday$", "MONTHSYS",
         "the eclipse series carries the date and weekday, but NAMING the month "
         "Falgun requires knowing whether the source counts amanta or "
         "purnimanta -- `month_system_confirmation` is open and this is the "
         "second section it bounds after B111"),
        (r"^Mars Rising", "READY",
         "`visibility/rise`; Mars's rise records exist in the combustion class"),
        (r"^Saturn and Neptune Conjunction$", "READY",
         "the conjunction series is emitted and ported as B41/B47; the note's "
         "3'20\" recovery is a stated end condition"),
    ],
    # ---------------------------------------------------------- SILVER BEARISH
    "silver-bearish": [
        (r"^Venus Alone in Leo or Libra", "READY",
         "`residency/alone_in_sign`, ported; the 'except 4th-6th Oct (Moon in "
         "Libra)' parenthetical is the same condition read in the negative and "
         "the Moon's Libra residency is emitted"),
        (r"^Mercury Alone in Aries or Virgo", "READY", "same"),
        (r"^Mars in the 4th Pad of Ashlesha", "READY",
         "the pada is on every record (`astronomy.pada`), and Ashlesha's 4th "
         "pada is a 3d20' arc of the nakshatra series"),
        (r"^Mars Vargottam in Cancer$", "READY",
         "the `vargottama` field plus a sign check"),
        (r"^Amavsya on Monday$", "READY",
         "`lunation/new_moon` is ported as B60 and the weekday is on the record"),
        (r"^Mercury Venus or Moon Venus Mutual Vedh$", "READY",
         "the vedha wheel, ported; 14 printed rows"),
        (r"^Moon Eclipse on Sunday", "READY",
         "`eclipse/lunar` is ported as B110 and carries the weekday"),
        (r"^Saturn Direct from Retrograde", "READY",
         "the station series is emitted and carries `motion`"),
        (r"^Sun in Virgo, Libra or Pisces With or Aspected by Benefics",
         "ASPECTORB",
         "the sign residency is READY; the 'or aspected by benefics' branch "
         "needs both the valence AND the orb, and the aspect machinery is "
         "validated only against exact-ish printed rows. Most binding is the orb"),
        (r"^Venus Rise in West$", "READY",
         "`visibility/rise` with `direction == west`, exactly B15's rule"),
    ],
    # ----------------------------------------------------------- SUGAR BULLISH
    "sugar-bullish": [
        (r"^Jupiter in Cancer$", "READY",
         "a sign residency with its own printed window (02-Jun-26 to 31-Oct-26)"),
        (r"^Eclipse in the Month of Falgun$", "MONTHSYS",
         "the eclipse date is emitted; the MONTH NAME is the open question"),
        (r"^If Any Malefic Planet Does the Vedh of", "VALENCE",
         "21 printed rows selected on malefic planets -- valence, and this is "
         "the family that appears in three of the four blocks"),
        (r"^Moon Joins Combust Mercury in West$", "READY",
         "the combust span with its direction flag plus the Moon's position at "
         "the same instant; both emitted"),
        (r"^Retrograde Mercury If Goes Combust in Cancer$", "READY",
         "combustion spans, `motion`, and a sign check"),
        (r"^When Herschel Is with Any Malefic Planet in Any Sign", "VALENCE",
         "'with any malefic planet' is the valence, and its own table names "
         "'Kshin Chandra' -- the waning Moon -- as one of them, so it also needs "
         "the Kshin definition the source never states"),
        (r"^Margshirsh Krishna Panchami Is on a Thursday", "MONTHSYS",
         "naming Margshirsh is the month system; Panchami and the weekday are "
         "both emitted"),
    ],
    # ----------------------------------------------------------- SUGAR BEARISH
    "sugar-bearish": [
        (r"^Jupiter in Hast or Shravan Nakshtra", "READY",
         "`residency/planet_nakshatra`; the printed row is Mars in Dhanistha, "
         "the same shape"),
        (r"^If Any Malefic Planet Does the Vedh of", "VALENCE",
         "the bearish half of the same 12-row table -- one input, one batch, "
         "with the bullish half"),
    ],
}

READY_NOTE = (
    "**READY does not mean ported, and it does not mean free.** Every group here "
    "still needs its own transcribed table, its own per-row fidelity check "
    "against the printed dates, and its own verdict text sliced verbatim or "
    "left null -- which is what the catalogue-B batches cost. The class answers "
    "one narrow question: does the CONDITION need astronomy this layer does not "
    "emit? For these, it does not."
)

INPUT_NOTE = (
    "**Five distinct missing inputs cover every blocking group** -- not "
    "fifty-eight. That is the scoping result: this is five decisions and one "
    "transcription batch, not an open-ended port. Two of the five "
    "(`aspect_orbs`, `month_system_confirmation`) are already open questions in "
    "config and are owed an answer for catalogue-B sections regardless of "
    "whether gold, silver or sugar are ever ported."
)


def classify(block: str) -> list[tuple[str, str, str]]:
    out = []
    for title, _body in groups(block):
        for pat, code, why in R[block]:
            if re.search(pat, title):
                out.append((title, code, why))
                break
        else:
            out.append((title, "UNCLASSIFIED",
                        "no class assigned -- fix the table"))
    return out


def main() -> None:
    rows = {b: classify(b) for b in BLOCKS}
    per_class: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    per_inst: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for b, rs in rows.items():
        inst, direction, _pages = BLOCKS[b]
        for _t, code, _w in rs:
            per_class[code][inst] += 1
            per_inst[inst][code] += 1

    n = total()
    ready_n = sum(per_class["READY"].values())
    blocked_n = n - ready_n
    L: list[str] = []
    A = L.append
    A("# What porting the instrument configuration sections would take")
    A("")
    A("**Status: this is the scope, reported BEFORE the work, and the port has "
      "since happened.** The `ported` column below reads 0 throughout because "
      "that is what it was when the survey was taken; **38 of the 58 groups are "
      "ported today and reach the calendar's rows**, per group in "
      "`build/CONFIG_PORT_REPORT.md`, which is the live page. This one is kept "
      "as the record of what the work was estimated to take, so the estimate can "
      "be read against what it cost -- see 'Where the port disagreed with the "
      "scope survey' there. "
      "Generated from `data/source_2026.html` by `finastro/cfgsections.py`; the "
      "per-group classes are assigned in `tools/gen_cfg_scope.py` with the "
      "evidence for each call in the same row, so a disagreement is checkable "
      "against the source rather than against this summary.")
    A("")
    A(f"## The counts, from the document")
    A("")
    A("Catalogue B is `<h3 class=\"section\">` and there are 141 of those. These "
      "are a different shape -- `<section id=\"...\">` with an `<h2>` -- so they "
      "were never in the 141 and the rule layer's \"141 of 141\" says nothing "
      "about them.")
    A("")
    A("| block | instrument | direction | pages | named groups | ported |")
    A("| --- | --- | --- | --- | --- | --- |")
    for b, (inst, direction, pages) in BLOCKS.items():
        A(f"| `{b}` | {inst} | {direction} | {pages} | "
          f"{len(rows[b])} | **0** |")
    A(f"| | | | **total** | **{n}** | **0 of {n}** |")
    A("")
    A("Per instrument: " + " · ".join(
        f"**{i} {by_instrument()[i]}**" for i in ("gold", "silver", "sugar"))
      + ".")
    A("")
    A("**This count disagrees with config and the document wins.** "
      "`verdict_coverage.tier_1.evidence` states 17 named groups for gold and 29 "
      "for silver, \"the largest configuration set in the document\". The "
      "document carries **19** and **30**: gold's groups are `<h3>` headings "
      "(13 + 6) rather than `config-title` divs, and the tier-1 note appears to "
      "have counted a subset. The undercount is recorded rather than quietly "
      "corrected in place, because a coverage number nobody can re-derive is "
      "the defect this page exists to fix.")
    A("")
    A(f"## The class of every one of the {n} groups")
    A("")
    for code, meaning in CLASS_CODES.items():
        A(f"* `{code}` — {meaning}")
    A("")
    A("| instrument | " + " | ".join(CLASS_CODES) + " | total |")
    A("| --- | " + " | ".join("---" for _ in CLASS_CODES) + " | --- |")
    for inst in ("gold", "silver", "sugar"):
        cells = " | ".join(str(per_inst[inst][c] or "") for c in CLASS_CODES)
        A(f"| **{inst}** | {cells} | **{by_instrument()[inst]}** |")
    A("| **all** | " + " | ".join(
        f"**{sum(per_class[c].values())}**" if sum(per_class[c].values())
        else "" for c in CLASS_CODES) + f" | **{n}** |")
    A("")
    A("### Reading the table")
    A("")
    A(f"* **{ready_n} of {n}** need no new astronomy at all. Their conditions "
      f"are sign and nakshatra residencies, aspect pairs, "
      f"combustion spans and `direction` flags, retrograde and station states, "
      f"tithi and paksha boundaries, eclipses, rises, and the `vargottama` and "
      f"`pada` fields -- every one of which the layer already emits and a "
      f"catalogue-B rule of the same shape already consumes.")
    A("* The remaining "
      f"**{blocked_n}** groups behind "
      f"**five** distinct missing inputs:")
    A("")
    A("| missing input | groups | where it already bites |")
    A("| --- | --- | --- |")
    A(f"| benefic/malefic valence | "
      f"**{sum(per_class['VALENCE'].values())}** | B19, B116, B117 -- the third "
      f"time this has been the binding constraint |")
    A(f"| first-sighting (darshan) computation | "
      f"**{sum(per_class['VISIBILITY'].values())}** | B62, and `swe.heliacal_ut` "
      f"was 9-10 days out against the source's own Venus rise dates |")
    A(f"| the source prints no dated window | "
      f"**{sum(per_class['NOTABLED'].values())}** | nothing -- this is a missing "
      f"TABLE, not a missing input; there is no condition to register |")
    A(f"| lunar month system (amanta vs purnimanta) | "
      f"**{sum(per_class['MONTHSYS'].values())}** | B111, and "
      f"`month_system_confirmation` is open in config |")
    A(f"| aspect orb | **{sum(per_class['ASPECTORB'].values())}** | "
      f"`aspect_orbs` is open; the aspect machinery itself is validated |")
    A("")
    A(INPUT_NOTE)
    A("")
    A(READY_NOTE)
    A("")
    A("## Is the verdict text separable the way catalogue B's was?")
    A("")
    A("**Yes, and it is the same operation, with one difference that matters.**")
    A("")
    A("Catalogue B's port sliced each section's verdict out of the source's own "
      "words and carried it verbatim or as `None`, which is the scheme "
      "`label_scheme_signoff` closed on. These blocks are the same shape: each "
      "group is a heading followed by a dated table, and the direction is in the "
      "heading itself -- \"Bullish\", \"Bearish\", \"Good Fall\", \"Short Term "
      "Bounce\", \"High Bullish\". So the verdict is separable for the same "
      "reason and by the same method.")
    A("")
    A("The difference is that **the block's `<h2>` and the group's heading are "
      "two halves of one verdict statement.** *Silver -- Bullish Configuration* "
      "is not a title only; it is the claim. *Moon Darshan on Friday/Saturday* "
      "carries no direction on its own. A porter who slices only the group "
      "heading will produce rows with no verdict and think the source was "
      "silent, exactly as `family` matched only one of its two readings and "
      "attached five of eleven families.")
    A("")
    A("Three further properties are worth knowing before the work is scoped:")
    A("")
    A("* **Direction is not always on the heading.** *Mars in the 4th Pad of "
      "Ashlesha* reads \"Good Fall\"; *Mercury Combust and Retrograde Does "
      "Mutual Vedh with Moon* reads nothing at all and inherits the block's. The "
      "heading is not a reliable field.")
    A("* **Impact windows are stated in prose, not in the table.** \"Maximum "
      "impact may remain for a fortnight\", \"Impact may be seen for 1 or 2 "
      "days\", \"Bullish for sugar and jaggery for the next three months\". "
      "Catalogue B handled this as a `remarks` string; the same field carries "
      "them.")
    A("* **One heading is a marked-up fragment.** Sugar-bearish's second group "
      "closes with the source's own `*Moon aspects to be added` -- an admitted "
      "incompleteness, which `tier_1.evidence` already carries forward as-is. "
      "It must be carried, not completed by us.")
    A("")
    A("## What is NOT in the 58")
    A("")
    _cfgsec = __import__("finastro.cfgsections", fromlist=["x"])
    A("Reported so the count is not read as the whole of the unported "
      "configuration material. The same chapter carries "
      f"**{len(_cfgsec.other_h2_tables())} further `<h2>` sub-tables** that "
      "are neither catalogue B nor one of these six blocks:")
    A("")
    for t in _cfgsec.other_h2_tables():
        A(f"* {t}")
    A("")
    A("*Kshin (Malefic) Moon* is load-bearing rather than incidental: "
      "sugar-bullish's malefic table names *Kshin Chandra* as one of its "
      "malefics, so the valence question and the Kshin definition are the same "
      "question asked twice.")
    A("")
    A("## Per group")
    A("")
    for b, (inst, direction, pages) in BLOCKS.items():
        A(f"### `{b}` — {inst}, {direction}, {pages} "
          f"({len(rows[b])} groups)")
        A("")
        A("| # | group (as the document heads it) | class | why that class |")
        A("| --- | --- | --- | --- |")
        for i, (title, code, why) in enumerate(rows[b], 1):
            t = title.replace("|", "/")
            A(f"| {i} | {t} | `{code}` | {why} |")
        A("")
    A("## Provenance")
    A("")
    A("Group titles and counts: `finastro/cfgsections.py`, read from "
      "`data/source_2026.html` at generation time. Classes and their grounds: "
      "`tools/gen_cfg_scope.py`. Neither infers a verdict and neither ports a "
      "rule. Nothing on this page is a forecast or investment advice.")
    A("")

    OUT.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(L)} lines, {n} groups)")
    for code in CLASS_CODES:
        print(f"  {code:<11} {sum(per_class[code].values()):>3}")
    unclassified = [t for rs in rows.values() for t, c, _ in rs
                    if c == "UNCLASSIFIED"]
    if unclassified:
        print("UNCLASSIFIED:", unclassified)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
