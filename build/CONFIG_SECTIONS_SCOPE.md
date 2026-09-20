# What porting the instrument configuration sections would take

**Status: this is the scope, reported BEFORE the work, and the port has since happened.** The `ported` column below reads 0 throughout because that is what it was when the survey was taken; **38 of the 58 groups are ported today and reach the calendar's rows**, per group in `build/CONFIG_PORT_REPORT.md`, which is the live page. This one is kept as the record of what the work was estimated to take, so the estimate can be read against what it cost -- see 'Where the port disagreed with the scope survey' there. Generated from `data/source_2026.html` by `finastro/cfgsections.py`; the per-group classes are assigned in `tools/gen_cfg_scope.py` with the evidence for each call in the same row, so a disagreement is checkable against the source rather than against this summary.

## The counts, from the document

Catalogue B is `<h3 class="section">` and there are 141 of those. These are a different shape -- `<section id="...">` with an `<h2>` -- so they were never in the 141 and the rule layer's "141 of 141" says nothing about them.

| block | instrument | direction | pages | named groups | ported |
| --- | --- | --- | --- | --- | --- |
| `gold-bullish` | gold | bullish | pp.136-144 | 13 | **0** |
| `gold-bearish` | gold | bearish | pp.145-148 | 6 | **0** |
| `silver-bullish` | silver | bullish | pp.149-161 | 20 | **0** |
| `silver-bearish` | silver | bearish | pp.162-167 | 10 | **0** |
| `sugar-bullish` | sugar | bullish | pp.168-173 | 7 | **0** |
| `sugar-bearish` | sugar | bearish | pp.174-175 | 2 | **0** |
| | | | **total** | **58** | **0 of 58** |

Per instrument: **gold 19** · **silver 30** · **sugar 9**.

**This count disagrees with config and the document wins.** `verdict_coverage.tier_1.evidence` states 17 named groups for gold and 29 for silver, "the largest configuration set in the document". The document carries **19** and **30**: gold's groups are `<h3>` headings (13 + 6) rather than `config-title` divs, and the tier-1 note appears to have counted a subset. The undercount is recorded rather than quietly corrected in place, because a coverage number nobody can re-derive is the defect this page exists to fix.

## The class of every one of the 58 groups

* `READY` — computable from the astronomy layer today
* `VALENCE` — needs a benefic/malefic classification (unstated in the source)
* `VISIBILITY` — needs a first-sighting computation the layer rejected on evidence
* `MONTHSYS` — needs the lunar month system confirmed
* `ASPECTORB` — needs the aspect orb ruled on (`aspect_orbs` is open)
* `NOTABLED` — the source prints no dated window -- nothing to port

| instrument | READY | VALENCE | VISIBILITY | MONTHSYS | ASPECTORB | NOTABLED | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **gold** | 12 | 4 | 3 |  |  |  | **19** |
| **silver** | 25 | 1 | 1 | 1 | 1 | 1 | **30** |
| **sugar** | 4 | 3 |  | 2 |  |  | **9** |
| **all** | **41** | **8** | **4** | **3** | **1** | **1** | **58** |

### Reading the table

* **41 of 58** need no new astronomy at all. Their conditions are sign and nakshatra residencies, aspect pairs, combustion spans and `direction` flags, retrograde and station states, tithi and paksha boundaries, eclipses, rises, and the `vargottama` and `pada` fields -- every one of which the layer already emits and a catalogue-B rule of the same shape already consumes.
* The remaining **17** groups behind **five** distinct missing inputs:

| missing input | groups | where it already bites |
| --- | --- | --- |
| benefic/malefic valence | **8** | B19, B116, B117 -- the third time this has been the binding constraint |
| first-sighting (darshan) computation | **4** | B62, and `swe.heliacal_ut` was 9-10 days out against the source's own Venus rise dates |
| the source prints no dated window | **1** | nothing -- this is a missing TABLE, not a missing input; there is no condition to register |
| lunar month system (amanta vs purnimanta) | **3** | B111, and `month_system_confirmation` is open in config |
| aspect orb | **1** | `aspect_orbs` is open; the aspect machinery itself is validated |

**Five distinct missing inputs cover every blocking group** -- not fifty-eight. That is the scoping result: this is five decisions and one transcription batch, not an open-ended port. Two of the five (`aspect_orbs`, `month_system_confirmation`) are already open questions in config and are owed an answer for catalogue-B sections regardless of whether gold, silver or sugar are ever ported.

**READY does not mean ported, and it does not mean free.** Every group here still needs its own transcribed table, its own per-row fidelity check against the printed dates, and its own verdict text sliced verbatim or left null -- which is what the catalogue-B batches cost. The class answers one narrow question: does the CONDITION need astronomy this layer does not emit? For these, it does not.

## Is the verdict text separable the way catalogue B's was?

**Yes, and it is the same operation, with one difference that matters.**

Catalogue B's port sliced each section's verdict out of the source's own words and carried it verbatim or as `None`, which is the scheme `label_scheme_signoff` closed on. These blocks are the same shape: each group is a heading followed by a dated table, and the direction is in the heading itself -- "Bullish", "Bearish", "Good Fall", "Short Term Bounce", "High Bullish". So the verdict is separable for the same reason and by the same method.

The difference is that **the block's `<h2>` and the group's heading are two halves of one verdict statement.** *Silver -- Bullish Configuration* is not a title only; it is the claim. *Moon Darshan on Friday/Saturday* carries no direction on its own. A porter who slices only the group heading will produce rows with no verdict and think the source was silent, exactly as `family` matched only one of its two readings and attached five of eleven families.

Three further properties are worth knowing before the work is scoped:

* **Direction is not always on the heading.** *Mars in the 4th Pad of Ashlesha* reads "Good Fall"; *Mercury Combust and Retrograde Does Mutual Vedh with Moon* reads nothing at all and inherits the block's. The heading is not a reliable field.
* **Impact windows are stated in prose, not in the table.** "Maximum impact may remain for a fortnight", "Impact may be seen for 1 or 2 days", "Bullish for sugar and jaggery for the next three months". Catalogue B handled this as a `remarks` string; the same field carries them.
* **One heading is a marked-up fragment.** Sugar-bearish's second group closes with the source's own `*Moon aspects to be added` -- an admitted incompleteness, which `tier_1.evidence` already carries forward as-is. It must be carried, not completed by us.

## What is NOT in the 58

Reported so the count is not read as the whole of the unported configuration material. The same chapter carries **10 further `<h2>` sub-tables** that are neither catalogue B nor one of these six blocks:

* Bhadra -- verified against Swiss Ephemeris
* Kshin (Malefic) Moon
* Total Days in Year
* Rahu or Ketu Nakshtra on a Thursday
* Moon Mercury in the Same Navamsh (D9)
* Rainfall Calculation
* Mars With or Aspecting Mercury
* Eclipse
* Planet Vargottam in Their Own Nakshatra
* Moon Rashi Parivartan Yog with Other Planets in D1

*Kshin (Malefic) Moon* is load-bearing rather than incidental: sugar-bullish's malefic table names *Kshin Chandra* as one of its malefics, so the valence question and the Kshin definition are the same question asked twice.

## Per group

### `gold-bullish` — gold, bullish, pp.136-144 (13 groups)

| # | group (as the document heads it) | class | why that class |
| --- | --- | --- | --- |
| 1 | When Mars Passes Through Taurus | `READY` | a sign residency plus the `vargottama` field the layer already puts on every positional record (config `vargottam.engine_field`) |
| 2 | When Sun in Libra Aspected by Other Malefics | `VALENCE` | the window is Mars's aspect to the Sun and the aspect layer has it; which aspects count as MALEFIC is what is unstated -- the same absence that blocks B19, B116 and B117 |
| 3 | Rahu Mars Together in Any Sign | `READY` | `residency/same_sign`, already ported for B84/B93 and the B41/B47 conjunction families |
| 4 | Jupiter Enters Gemini | `READY` | read as the sign residency it is: the source's own row is dated 05-Dec-25 to 02-Jun-26, which is a window in Gemini and not the ingress instant |
| 5 | When Malefic Planets Do Vedh of Punarvasu, Pushya, Chitra and Dhanistha — more than one malefic is extreme bullish | `VALENCE` | a 20-row vedha table; the vedha wheel exists (`vedha/nakshatra`) but the row SELECTION is 'malefic planets', so the valence is binding |
| 6 | If Mars is Aspected by Saturn and Jupiter is Retrograde | `READY` | a two-body aspect plus the `motion` field on every record; both exist and both are already used by catalogue-B rules |
| 7 | Sun on Bharni, Kritika, Punarvasu or Pushya and Not Aspected by Benefic — more bullish if aspected by malefic | `VALENCE` | explicitly negated on a BENEFIC aspect, and the note adds 'more bullish if aspected by malefic'. Both directions need the valence |
| 8 | Moonrise on Monday or Friday — Bullish | `VISIBILITY` | a two-row Friday/Monday table with no sign or star -- the SIGHTING class, the one B62 is blocked on, not the Moon's daily rise |
| 9 | Moonrise in Libra — Bullish | `VISIBILITY` | same sighting class; carries Sign and Nakshatra columns, so the sighting falls on a day the Moon is in Libra and Swati |
| 10 | Sun Moon on the Same Degree Is Bullish (short-term bounce) | `READY` | the layer emits per-record longitudes and the lunation series, so the instant the two agree is readable rather than scanned for |
| 11 | Venus in Rohini Nakshtra | `READY` | `residency/planet_nakshatra`, the shape B89 and B113 already use |
| 12 | Mars in Pushya Nakshtra | `READY` | same as above, different body |
| 13 | Aquarius Sun's Transgression, if Happens on a Friday | `READY` | the Sankranti series is ported as B1 and carries the weekday on every record |

### `gold-bearish` — gold, bearish, pp.145-148 (6 groups)

| # | group (as the document heads it) | class | why that class |
| --- | --- | --- | --- |
| 1 | Rise of Jupiter in Any Sign — Bearish (short term) | `READY` | `visibility/rise` from the combustion class, with its `direction` flag -- the same primitive B15's rise rules use |
| 2 | Saturn or Mercury in Gemini — Bearish | `READY` | a sign residency; the printed row names Mercury, and the rule is the same shape either way |
| 3 | Vedh by Benefics of Punarvasu, Pushya, Chitra or Dhanistha | `VALENCE` | a 12-row vedha table selected on BENEFICS -- the mirror of the bullish block's malefic table, and the same missing input |
| 4 | Mercury Rise in West | `READY` | `visibility/rise` filtered on `direction == west`; exactly what `b015b_venus_rise_west` already does for Venus |
| 5 | Moon Darshan on Saturday | `VISIBILITY` | darshan is the sighting; B62 is the same computation and is blocked |
| 6 | Venus in Punarvasu Nakshtra | `READY` | `residency/planet_nakshatra` |

### `silver-bullish` — silver, bullish, pp.149-161 (20 groups)

| # | group (as the document heads it) | class | why that class |
| --- | --- | --- | --- |
| 1 | Turning Dates — Shukla Shashti (impact till Purnima / full moon) | `READY` | Shukla Shashti is tithi 6 of the bright fortnight and `tithi_ingress` is emitted; the impact window to Purnima is a span between two tithis |
| 2 | Retrograde Mercury or Jupiter Increases Volatility and Prices May Rise | `READY` | `motion` plus the station series; `motion/both_retrograde` is already ported for B81-B83 |
| 3 | Sun in Pushya or Dhanistha Without Benefic Planet | `VALENCE` | negated on a BENEFIC presence -- valence again |
| 4 | Mars Itself in Aquarius — Bullish for Silver | `NOTABLED` | the source prints no dated window; its own note says the condition is 'noted alongside Rahu-Mars conjunction in Aquarius below', which is gold-bullish's table and not a condition of its own |
| 5 | Venus Mars Together | `READY` | `residency/same_sign`, ported |
| 6 | Sun Mars Together | `READY` | same |
| 7 | Rahu Mars Together in Any Sign — more bullish when in the same Nakshatra | `READY` | same, and the starred sub-window is a nakshatra residency the layer carries |
| 8 | Moon Darshan on Friday/Saturday — Bullish | `VISIBILITY` | the sighting class |
| 9 | Sun and Moon Together on Sankranti Entering Time | `READY` | the Sankranti series plus the lunation series; both emitted |
| 10 | Mercury or Jupiter Do Vedh of Venus | `READY` | the vedha wheel is ported for B133 and the 96 printed rows resolve through it; both bodies' classes are calibrated and overdetermined |
| 11 | Mercury Combust and Retrograde Does Mutual Vedh with Moon | `READY` | a combustion span, the retrograde sense, and the Moon's nakshatra -- all three emitted; the Moon needs no speed class here, only its position, which the nakshatra series gives |
| 12 | Venus Combust in West — Bullish Till It Rises in East | `READY` | `combust_spans` filtered on the west direction, ported as B15 |
| 13 | Whenever Jupiter or Mercury Turns Direct from Retrograde — Short Term Bounce | `READY` | the station series is emitted and reproduces the source's own directions |
| 14 | Shukla Paksh of 16 Days or Krishna Paksh of 14 Days — Bullish | `READY` | the tithi ingress series gives both pakshas' lengths directly |
| 15 | Only Sun Mercury or Moon Mercury Alone in Any Sign — Bullish | `READY` | `residency/alone_in_sign`, already ported as B16 |
| 16 | Mercury Jupiter Both Retrograde | `READY` | `motion/both_retrograde`, ported |
| 17 | Retrograde Mercury Once Goes Combust — Short Term Uptrend | `READY` | the combustion spans carry direction and the records carry `motion` |
| 18 | Sun Eclipse in Falgun or Jyestha on Tuesday | `MONTHSYS` | the eclipse series carries the date and weekday, but NAMING the month Falgun requires knowing whether the source counts amanta or purnimanta -- `month_system_confirmation` is open and this is the second section it bounds after B111 |
| 19 | Mars Rising — Bullish in Short Term | `READY` | `visibility/rise`; Mars's rise records exist in the combustion class |
| 20 | Saturn and Neptune Conjunction | `READY` | the conjunction series is emitted and ported as B41/B47; the note's 3'20" recovery is a stated end condition |

### `silver-bearish` — silver, bearish, pp.162-167 (10 groups)

| # | group (as the document heads it) | class | why that class |
| --- | --- | --- | --- |
| 1 | Venus Alone in Leo or Libra — Bearish | `READY` | `residency/alone_in_sign`, ported; the 'except 4th-6th Oct (Moon in Libra)' parenthetical is the same condition read in the negative and the Moon's Libra residency is emitted |
| 2 | Mercury Alone in Aries or Virgo — Bearish | `READY` | same |
| 3 | Mars in the 4th Pad of Ashlesha — Good Fall | `READY` | the pada is on every record (`astronomy.pada`), and Ashlesha's 4th pada is a 3d20' arc of the nakshatra series |
| 4 | Mars Vargottam in Cancer | `READY` | the `vargottama` field plus a sign check |
| 5 | Amavsya on Monday | `READY` | `lunation/new_moon` is ported as B60 and the weekday is on the record |
| 6 | Mercury Venus or Moon Venus Mutual Vedh | `READY` | the vedha wheel, ported; 14 printed rows |
| 7 | Moon Eclipse on Sunday — Falls 15 Days Ahead | `READY` | `eclipse/lunar` is ported as B110 and carries the weekday |
| 8 | Saturn Direct from Retrograde — Bearish | `READY` | the station series is emitted and carries `motion` |
| 9 | Sun in Virgo, Libra or Pisces With or Aspected by Benefics | `ASPECTORB` | the sign residency is READY; the 'or aspected by benefics' branch needs both the valence AND the orb, and the aspect machinery is validated only against exact-ish printed rows. Most binding is the orb |
| 10 | Venus Rise in West | `READY` | `visibility/rise` with `direction == west`, exactly B15's rule |

### `sugar-bullish` — sugar, bullish, pp.168-173 (7 groups)

| # | group (as the document heads it) | class | why that class |
| --- | --- | --- | --- |
| 1 | Jupiter in Cancer | `READY` | a sign residency with its own printed window (02-Jun-26 to 31-Oct-26) |
| 2 | Eclipse in the Month of Falgun | `MONTHSYS` | the eclipse date is emitted; the MONTH NAME is the open question |
| 3 | If Any Malefic Planet Does the Vedh of Ashlesha, Magha, Jyestha or Uttra Bhadrapad — if More than One Nakshtra Vedh at the Same Time — High Bullish | `VALENCE` | 21 printed rows selected on malefic planets -- valence, and this is the family that appears in three of the four blocks |
| 4 | Moon Joins Combust Mercury in West | `READY` | the combust span with its direction flag plus the Moon's position at the same instant; both emitted |
| 5 | Retrograde Mercury If Goes Combust in Cancer | `READY` | combustion spans, `motion`, and a sign check |
| 6 | When Herschel Is with Any Malefic Planet in Any Sign — Bullish | `VALENCE` | 'with any malefic planet' is the valence, and its own table names 'Kshin Chandra' -- the waning Moon -- as one of them, so it also needs the Kshin definition the source never states |
| 7 | Margshirsh Krishna Panchami Is on a Thursday / Friday | `MONTHSYS` | naming Margshirsh is the month system; Panchami and the weekday are both emitted |

### `sugar-bearish` — sugar, bearish, pp.174-175 (2 groups)

| # | group (as the document heads it) | class | why that class |
| --- | --- | --- | --- |
| 1 | Jupiter in Hast or Shravan Nakshtra or Mars in Dhanistha | `READY` | `residency/planet_nakshatra`; the printed row is Mars in Dhanistha, the same shape |
| 2 | If Any Malefic Planet Does the Vedh of Ashlesha, Magha, Jyestha or Uttra Bhadrapad — if More than One Nakshtra Vedh at the Same Time — High Bearish | `VALENCE` | the bearish half of the same 12-row table -- one input, one batch, with the bullish half |

## Provenance

Group titles and counts: `finastro/cfgsections.py`, read from `data/source_2026.html` at generation time. Classes and their grounds: `tools/gen_cfg_scope.py`. Neither infers a verdict and neither ports a rule. Nothing on this page is a forecast or investment advice.
