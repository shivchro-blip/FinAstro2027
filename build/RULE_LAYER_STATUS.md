# Rule layer status — catalogue B, and what catalogue B is not

Generated 18-Nov-2026 from the live registry, not by hand. Year 2027.

## Coverage, in three denominators

Three counts, because there are three catalogues in this document and only one of them was ever in scope:

| | sections | ported | reading |
| --- | --- | --- | --- |
| **Catalogue B** — `<h3 class="section">`, the rule sections of Chapter 1 | 141 sections | **141 of 141** | every section carries a status |
| **Instrument configuration sections** — `<section id="...">` with an `<h2>`, Chapter 1 Sr.No 149-154 | **58 named groups** | **38 of 58** | **20 blocked, each on a named input** |
| **`<h2>` sub-tables** — `<section id="...">` with an `<h2>` that states no direction | **10 sub-tables** | **5 of 10** | **5 blocked or out of scope, each on a named input** |

**So: catalogue B 141/141 · configuration sections 38/58 · sub-tables 5/10.** THREE DENOMINATORS OVER THREE SHAPES OF MARKUP, and none of them is in either of the others. That separation is what keeps "141 of 141" honest: it is a statement about `<h3 class="section">` and about nothing else. All three DO feed the calendar — `verdicts.py` fires all three registries — and the 8,517 verdict rows split **5,545 catalogue B · 1,468 configuration · 1,504 sub-table**.

**A row's registry is readable off its `event` field with no lookup**: `cfg_<block>_` for a configuration group, `sub_` for a sub-table, and `b<nn>` or a panchang family name for catalogue B. That convention is asserted at registration rather than left to discipline, because the one thing that would make all three of these numbers wrong at once is a rule in the wrong registry.

**141 of 141 is TRUE OF CATALOGUE B and is not a coverage claim about the source.** The instrument configuration sections are a different shape of markup and were never in the 141, so they were never in the denominator and a reader seeing "141/141" could conclude the source is fully covered when 20 of those 58 named groups have still never had a rule written for them.

The counts, from the document (read out of `data/source_2026.html` at generation time by `finastro/cfgsections.py`, not out of config — a count taken from the thing being audited is not an audit):

| block | instrument | direction | pages | named groups | ported |
| --- | --- | --- | --- | --- | --- |
| `gold-bullish` | gold | bullish | pp.136-144 | 13 | **7** |
| `gold-bearish` | gold | bearish | pp.145-148 | 6 | **4** |
| `silver-bullish` | silver | bullish | pp.149-161 | 20 | **15** |
| `silver-bearish` | silver | bearish | pp.162-167 | 10 | **8** |
| `sugar-bullish` | sugar | bullish | pp.168-173 | 7 | **3** |
| `sugar-bearish` | sugar | bearish | pp.174-175 | 2 | **1** |
| | | | | **58** | **38 of 58** |

### Gold, silver and sugar now reach the calendar through their own configuration groups as well as through generic catalogue-B rules

**Gold, silver and sugar are the three instruments the source prints verdicts for** — that is why they carry evidence blocks naming their own configuration sections, and it is what their tiers rest on. Their own configuration groups are **gold 19** · **silver 30** · **sugar 9** named groups, of which **38** now carry a rule and **20** are blocked on a named input. **26 of those 38 fire in 2027**, for 1,468 rows.

**Ported IS wired, since the 14-Sep-2026 change to `verdicts.py`, and the distinction this section used to draw is the one thing about it that is now out of date.** `build_verdicts()` fires both registries; `config_instruments_for` routes a group to the instrument its BLOCK names rather than through the rulership table, so a *Gold — Bullish* group reaches gold because the source filed it under gold.

**1,468 of 8,517 verdict rows in `build/calendar_2027.*` originate in a configuration section**, from 26 groups, split **gold-bearish 167** · **gold-bullish 61** · **silver-bearish 164** · **silver-bullish 923** · **sugar-bullish 153**.

**How to tell one apart, because the old test no longer works.** This page used to say that no row originates in a configuration section and offered a check: the `event_section` field never reads `gold-bullish`. It still never does — `event_section` carries the group's own printed title, such as `Venus Alone in Leo or Libra — Bearish`, and never the block id. The test passes and its conclusion is now wrong. **The field that separates them is `event`**, whose rule id begins `cfg_<block>_` for a configuration row and `b<nn>` or a panchang family name for a catalogue-B one.

What gold, silver and sugar got BEFORE the wiring is still in the file and is still not the source's verdicts for them: every generic catalogue-B rule whose bodies resolve to an instrument still emits there — a Venus rule reaches SUGAR because SUGAR's rulership is Venus, not because the source said anything about sugar. The wiring added the source's own conditions beside those rows; it removed none of them.

Sugar is the clearest case and is the reason the gap was found at all: it emits rows from 12 different Venus-ruled catalogue-B sections, and **153** from its own nine groups — 153 of its 552 rows. That figure was **0** until the wiring, and a reader seeing SUGAR's rows then would have seen a covered instrument.

Gold and silver reach tier 1 through their MCX legs (`MCXGOLD`, `MCXSILVER`); their COMEX legs (`GC`, `SI`) emit `venue_shifted` instead, by the 14-Sep-2026 localised split. Both legs are the same generic rules on the same sky. The tier says where a claim was authored and how the civil day is bounded; it does not say the source's own gold and silver conditions were ported.

**What porting them would take is scoped, not estimated, in `build/CONFIG_SECTIONS_SCOPE.md`** — all 58 groups, their conditions, and which of them the existing astronomy layer can already compute.

### The third body of material — registered since 20-Sep-2026, and two of it ported

The same chapter carries 10 further `<h2>` sub-tables that are neither catalogue B nor any of the six blocks above: *Bhadra -- verified against Swiss Ephemeris*, *Kshin (Malefic) Moon*, *Total Days in Year*, *Rahu or Ketu Nakshtra on a Thursday*, *Moon Mercury in the Same Navamsh (D9)*, *Rainfall Calculation*, *Mars With or Aspecting Mercury*, *Eclipse*, *Planet Vargottam in Their Own Nakshatra*, *Moon Rashi Parivartan Yog with Other Planets in D1*.

**This heading read "There is a third UNPORTED body of material" until 20-Sep-2026.** These nine now have a registry of their own and a denominator of their own, at the top of this page: 5 of 10 ported, 5 registered and blocked with the input each waits on NAMED. Registering the blocked seven rather than describing them in prose is what makes "blocked on what" countable off the registry instead of parsed out of a sentence.

| sub-table | status | rule | blocked on |
| --- | --- | --- | --- |
| Bhadra — verified against Swiss Ephemeris (pp. 120–124) | **ported** | `sub_bhadra` | — |
| Total Days in Year (p. 126) | **ported** | `sub_total_days_in_year` | — |
| Rahu or Ketu Nakshtra on a Thursday (p. 127) | **ported** | `sub_rahu_or_ketu_nakshatra_on_a_thursday` | — |
| Kshin (Malefic) Moon (p. 125) | blocked | `sub_kshin_malefic_moon` | `scope` |
| Moon Mercury in the Same Navamsh (D9) (pp. 128–129) | **ported** | `sub_moon_mercury_in_the_same_navamsh` | — |
| Rainfall Calculation (p. 130) | blocked | `sub_rainfall_calculation` | `no_dated_window` |
| Mars With or Aspecting Mercury (p. 131) | blocked | `sub_mars_with_or_aspecting_mercury` | `aspect_orb` |
| Eclipse (p. 132) | blocked | `sub_eclipse` | `month_system` |
| Planet Vargottam in Their Own Nakshatra (p. 133) | **ported** | `sub_planet_vargottam_in_their_own_nakshatra` | — |
| Moon Rashi Parivartan Yog with Other Planets in D1 (pp. 134–135) | blocked | `sub_moon_rashi_parivartan_yog` | `sign_lordship` |

The two ported are the ones the layer could already compute AND whose printed tables they were reported against first: Total Day reproduces the section's own **12 of 12** dates with no extra, and the Thursday table **13 of 13** rows on three independent columns — date, nakshatra, and the five boundaries it states as clock times, all landing within 50 seconds. Both carry a NULL verdict, because none of the nine sections prints one and `subtable_catalogue.check_no_verdict` refuses a rule that arrives carrying one.

**`moon_navamsa_series` was the largest single gap named on this page and it is closed.** It blocked two of the ten sub-tables — *Moon Mercury in the Same Navamsh (D9)*, 36 printed windows, and most of *Planet Vargottam in Their Own Nakshatra* — plus B71d, and it was a SERIES rather than a rule, which is why it was filed with Bhadra. The build emits it from 21-Sep-2026: **1,692 Moon records over the 2026 span and 1,684 over the 2027 one**, about a third again on top of 5,036 in each year. All three consumers are ported, each verified against its own printed rows first.

**The exclusion was ours and its stated ground was measurably wrong.** `build_2027.py` excluded the Moon from D9 because a Moon D9 series "would be noise rather than signal", on an interval this page carried as two hours and the reclassification that produced the exclusion put at under two. The measured mean is **6.06 hours** on the 2026 span and 6.08 on the 2027 one. And the noise reading is refuted by the series' own structure: **every ninth record IS a Moon sign ingress**, to the second — 188 of 1,692 in 2026, 187 of 1,684 in 2027, nothing missed in either — so a ninth of the "noise" was already being emitted under another name and graded A.

And the source's own monthly prophecy tables (Chapter 3) print named verdicts for gold and silver — "Bullish for Gold and Silver", "High Bearish for Gold" — which are also outside catalogue B and also unported. Recorded because a coverage page that fixes one denominator and leaves the next one implicit has only moved the misleading claim.

---

**172 rules over 141 of 141 catalogue-B sections — full coverage of catalogue B — 3692 dated rows in 2027.** 135 executable, 5 resolved, 31 blocked, 1 ambiguous.

`zero` in the firing column means the rule runs and produces no row this year. That is either the configuration genuinely not occurring or a porting error, and the two look identical from outside — so every zero is pinned by name with its kind in `tests/test_rule_layer.py`. `BLOCKED` means the rule is registered, counted, emits nothing, and **names the input it is waiting for**.

Status keys: `ok` executable · `ok*` fires on a reading we supplied, flagged on every row · `BLOCKED` missing input named below · `AMBIG` source wording admits more than one reading.

## Coverage of catalogue B — all 141 sections

| B | page | section | status | rules | 2027 rows (mumbai / ny) | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p.2 | Sun Transgression (Sankranti) | ok | 1 | 12 / 12 |  |
| 2 | pp.3-4 | Sun Nakshtra Journey and Relationship with Nakshtra Lord | ok | 1 | 27 / 27 |  |
| 3 | p.5 | Journey of Mars | ok | 1 | 7 / 7 |  |
| 4 | p.6 | Mars Combust Rise Cycle | ok | 1 | 0 / 0 | zero this year (pinned) |
| 5 | p.6 | Mars in Pisces Navmansh (D9) | BLOCKED | 1 | 0 / 0 | see blockers |
| 6 | p.7 | Vargottam Mars | BLOCKED | 1 | 0 / 0 | see blockers |
| 7 | p.8 | Journey of Mercury | ok | 1 | 16 / 16 |  |
| 8 | pp.8-9 | Mercury Motion | ok | 1 | 1 / 0 |  |
| 9 | p.10 | Mercury Combust Rise Cycle | ok | 1 | 144 / 0 |  |
| 10 | p.11 | Mercury Manifestation | ok | 1 | 3 / 0 |  |
| 11 | p.12 | Mercury - Furthest from Sun | BLOCKED | 1 | 0 / 0 | see blockers |
| 12 | p.12 | Mars Mercury Conjunction | ok | 1 | 0 / 0 | zero this year (pinned) |
| 13 | p.12-13 | Journey of Venus | ok | 1 | 15 / 15 |  |
| 14 | p.14 | Venus Motion | ok | 1 | 1 / 0 |  |
| 15 | p.14 | Venus Combust Rise Cycle | ok + ok* | 5 | 100 / 0 |  |
| 16 | p.16 | Mercury Venus Alone in Any Sign | ok | 1 | 43 / 43 |  |
| 17 | p.16 | Venus Mercury Conjunction | ok | 1 | 3 / 3 |  |
| 18 | p.17 | Sun Ahead, Venus Behind and Mercury in the Middle | ok | 1 | 117 / 117 |  |
| 19 | p.18 | Venus Ahead, Sun Behind and Mercury in the Middle | BLOCKED | 1 | 0 / 0 | see blockers |
| 20 | p.18-19 | Journey of Jupiter | ok | 1 | 3 / 3 |  |
| 21 | p.20 | Jupiter Motion | ok | 1 | 1 / 0 |  |
| 22 | p.20 | Jupiter Combust Rise Cycle | ok | 2 | 52 / 0 |  |
| 23 | p.21 | Jupiter Constellation (Nakshtra) | ok | 1 | 4 / 4 |  |
| 24 | p.22 | Jupiter in Navmansh (D9) | ok | 1 | 15 / 15 |  |
| 25 | p.23 | Journey of Saturn | ok | 1 | 2 / 2 |  |
| 26 | p.23 | Saturn Motion | ok | 1 | 1 / 0 |  |
| 27 | p.24 | Saturn Combust Rise Cycle | ok | 1 | 35 / 0 |  |
| 28 | p.24 | Saturn Constellation (Nakshtra) | ok | 1 | 3 / 3 |  |
| 29 | p.25 | Saturn in Navmansh (D9) | ok | 1 | 8 / 8 |  |
| 30 | p.26 | Demoted and Shadow Speed of Saturn | BLOCKED | 1 | 0 / 0 | see blockers |
| 31 | p.26 | Journey of Rahu | ok | 1 | 0 / 0 | zero this year (pinned) |
| 32 | p.27 | Rahu Constellation (Nakshtra) | ok | 1 | 2 / 2 |  |
| 33 | p.28 | Rahu in Navmansh (D9) | ok | 1 | 6 / 6 |  |
| 34 | p.28 | Journey of Ketu | ok | 1 | 0 / 0 | zero this year (pinned) |
| 35 | p.29 | Ketu Constellation (Nakshtra) | ok | 1 | 1 / 1 |  |
| 36 | p.30 | Ketu in Navmansh (D9) | ok | 1 | 6 / 6 |  |
| 37 | p.30 | Journey of Herschel | ok | 1 | 1 / 0 |  |
| 38 | p.31 | Herschel Motion | ok | 1 | 1 / 0 |  |
| 39 | p.32 | Herschel Constellation (Nakshtra) | ok | 1 | 1 / 1 |  |
| 40 | p.32 | Herschel in Navmansh (D9) | ok | 1 | 3 / 3 |  |
| 41 | p.34 | Herschel Conjunction with Other Planets | ok | 4 | 3 / 3 |  |
| 42 | p.34 | Herschel Opposition with Other Planets | ok | 2 | 2 / 2 |  |
| 43 | p.34 | Journey of Neptune | ok | 1 | 1 / 0 |  |
| 44 | p.35 | Neptune Motion | ok | 1 | 1 / 0 |  |
| 45 | p.36 | Neptune Constellation (Nakshtra) | ok | 1 | 1 / 0 |  |
| 46 | p.36 | Neptune in Navmansh (D9) | ok | 1 | 2 / 2 |  |
| 47 | p.37 | Neptune Conjunction with Other Planets | ok | 5 | 3 / 3 |  |
| 48 | p.37 | Neptune Opposition with Other Planets | ok | 3 | 3 / 3 |  |
| 49 | p.38 | Journey of Pluto | ok | 1 | 1 / 0 |  |
| 50 | p.38 | Pluto Motion | ok | 1 | 1 / 0 |  |
| 51 | p.39 | Pluto Constellation (Nakshtra) | ok | 1 | 0 / 0 | zero this year (pinned) |
| 52 | p.40 | Pluto in Navmansh (D9) | ok | 1 | 0 / 0 | zero this year (pinned) |
| 53 | p.41 | Pluto Conjunction with Other Planets (Except Moon) | ok | 4 | 4 / 4 |  |
| 54 | p.42 | Pluto Opposition with Other Planets (Except Moon) | ok | 5 | 3 / 3 |  |
| 55 | p.42 | Panchak | AMBIG + ok* | 2 | 74 / 76 |  |
| 56 | p.44 | Aindra, Vaidhrati and Vyatipat Yog in Panchak — Bullish | ok* | 1 | 15 / 15 | reading supplied, flagged |
| 57 | p.44 | Apogee Dates | ok | 2 | 14 / 15 |  |
| 58 | p.46 | Perigee Dates | ok | 1 | 13 / 13 |  |
| 59 | p.47 | Perihelion and Aphelion Dates | ok | 1 | 2 / 2 |  |
| 60 | p.48 | Amavasya (No Moon Day) | ok | 3 | 18 / 18 |  |
| 61 | p.49 | Purnima (Full Moon) | ok | 1 | 12 / 12 |  |
| 62 | p.50 | Chandra Darshan (New Moon) | BLOCKED | 1 | 0 / 0 | see blockers |
| 63 | p.51 | Hemisphere | BLOCKED | 1 | 0 / 0 | see blockers |
| 64 | pp.52-53 | Pradosh | ok* | 1 | 25 / 25 | reading supplied, flagged |
| 65 | p.54 | Ekadashi on Friday | ok | 1 | 8 / 4 |  |
| 66 | p.55 | Kshay Tithi — Shukla Paksh (Bright Fortnight) — Bearish | ok | 1 | 18 / 18 |  |
| 67 | p.56 | Kshay Tithi — Krishna Paksh (Dark Fortnight) — Bullish | ok | 1 | 16 / 12 |  |
| 68 | p.57 | Vriddhi Tithi — Shukla Paksh (Bright Fortnight) — Bullish | ok | 1 | 12 / 8 |  |
| 69 | p.58 | Vriddhi Tithi — Krishna Paksh (Dark Fortnight) — Bearish | ok | 1 | 12 / 12 |  |
| 70 | p.59 | Big Volatile — Major Turning Days | BLOCKED | 1 | 0 / 0 | see blockers |
| 71 | p.60 | Uttra Falguni Nakshtra During the Year | ok | 2 | 89 / 89 |  |
| 72 | p.61 | Mangal Ashwini Yog — Bullish (Ashwini Nakshtra on Tuesday) | ok | 1 | 3 / 3 |  |
| 73 | p.62 | Ashtami on Tuesday / Saturday — Bullish | ok | 1 | 18 / 13 |  |
| 74 | p.63 | Ashtami on Monday, Thursday and Friday — Bearish | ok | 1 | 18 / 19 |  |
| 75 | p.64 | Chaturthi — Shukla Paksh (Bright Fortnight) — Bullish | ok | 1 | 24 / 27 |  |
| 76 | p.65 | Chaturthi — Krishna Paksh (Dark Fortnight) — Bearish | ok | 1 | 24 / 24 |  |
| 77 | p.66 | Kaal Sarp Yog | ok | 1 | 0 / 0 | zero this year (pinned) |
| 78 | p.67 | Venus Jupiter in the Same Sign | ok | 1 | 25 / 25 |  |
| 79 | p.67 | Venus Behind Jupiter in the Same Sign — Bullish | ok | 1 | 9 / 9 |  |
| 80 | p.67 | Venus Ahead of Jupiter in the Same Sign — Bearish | ok | 1 | 14 / 15 |  |
| 81 | p.68 | Saturn and Mercury Both Retrograde — Bullish | ok | 1 | 22 / 22 |  |
| 82 | p.68 | Jupiter and Mercury Both Retrograde — Bullish | ok | 1 | 23 / 23 |  |
| 83 | p.68 | Mercury and Venus Both Retrograde — Temp Bounce | ok | 1 | 0 / 0 | zero this year (pinned) |
| 84 | p.69 | Mars Jupiter in the Same Sign | ok | 1 | 83 / 83 |  |
| 85 | p.69 | Mars Behind Jupiter in the Same Sign — Bearish | ok | 1 | 0 / 0 | zero this year (pinned) |
| 86 | p.69 | Mars Ahead of Jupiter in Same Sign — Bullish | ok | 2 | 83 / 83 |  |
| 87 | p.70 | Moon and Rahu in Same Nakshtra — Bullish: Rahu in Shatbisha | ok | 2 | 28 / 29 |  |
| 88 | p.71 | Rahu in Dhanistha | ok | 1 | 8 / 8 |  |
| 89 | p.72 | Mars in the Nakshtra of Rohini or Chitra — Bullish: Mars in Rohini | ok | 2 | 22 / 22 |  |
| 90 | p.72 | Venus Mars in the Same Nakshtra — Bullish | ok | 1 | 31 / 32 |  |
| 91 | p.73 | Sun in Uttra Shada / Ashwini / Chitra — Bullish | ok | 1 | 43 / 43 |  |
| 92 | p.73 | Sun in Kritika — 1st 2 Days Bullish, Then Bearish | ok | 1 | 14 / 15 |  |
| 93 | p.74 | Moon Mars Together in the Same Sign — Bullish | ok | 1 | 42 / 43 |  |
| 94 | p.75 | Shani Chandra Dwidwadash Yog — Bearish | ok* | 1 | 43 / 44 | reading supplied, flagged |
| 95 | p.77 | Shukla Pratipada on Saturday / Sunday — Three Days Bullish | ok | 1 | 7 / 8 |  |
| 96 | p.77 | Vyathipat Yog on Tuesday, Saturday and Sunday — Bullish | ok | 1 | 11 / 11 |  |
| 97 | p.78 | Moon in Mrigsira on Monday — Bullish | ok | 1 | 3 / 5 |  |
| 98 | p.79 | Mool Nakshtra: Mercury in Mool Nakshtra — Bearish | ok | 1 | 9 / 10 |  |
| 99 | p.79 | Jupiter in Magha, Purva Falguni, Uttra Falguni or Hasta — First 15 Days Bearish, Then Bullish | ok | 1 | 214 / 214 |  |
| 100 | p.80 | Shukla Shasthi on a Friday — Bearish | ok | 1 | 3 / 4 |  |
| 101 | p.80 | Three Saturday in Shukla Paksh — Bearish | ok | 1 | 45 / 60 |  |
| 102 | p.80 | Anuradha on Sunday — Bearish | ok | 1 | 6 / 6 |  |
| 103 | p.80 | Shatbhisha on Tuesday — Bearish | ok | 1 | 5 / 4 |  |
| 104 | p.82 | Mrigsira on Thursday — Bearish | ok | 1 | 2 / 3 |  |
| 105 | p.83 | Uttra Shada on Monday — Bearish | ok | 2 | 5 / 5 |  |
| 106 | p.84 | Amavasya Ghadi Lesser than Chaturdashi — Bearish | ok | 1 | 14 / 13 |  |
| 107 | p.85 | Venus Alone in Shravan Nakshtra — High Bullish | ok | 1 | 0 / 0 | zero this year (pinned) |
| 108 | p.85 | Shukla Ekadashi Vyatipath or Vaidhrati Yog — Bearish | ok | 1 | 2 / 3 |  |
| 109 | p.86 | Shukla Trayodashi on Tuesday or Saturday — Bearish | ok | 1 | 6 / 8 |  |
| 110 | p.87 | Moon Eclipse on Tuesday — Bullish | ok | 1 | 1 / 1 |  |
| 111 | p.87 | Moon Eclipse in Vaishak, Shravan or Ashwin Month — Bullish | BLOCKED | 1 | 0 / 0 | see blockers |
| 112 | p.88 | Venus Mercury Together in Shravan — Bearish 3/4 Days | ok | 1 | 0 / 0 | zero this year (pinned) |
| 113 | p.88 | Mars in Dhanistha — Immediate Bearish | ok | 1 | 0 / 0 | zero this year (pinned) |
| 114 | p.89 | Mercury in Purva Bhadrapada — First Bullish Then Bearish | ok | 1 | 9 / 10 |  |
| 115 | p.89 | Either Sun or Venus in Shatbhisha — Bullish | ok | 1 | 26 / 26 |  |
| 116 | p.90 | Mercury in Paap Kartari | BLOCKED | 1 | 0 / 0 | see blockers |
| 117 | p.91 | Jupiter in Paap Kartari | BLOCKED | 1 | 0 / 0 | see blockers |
| 118 | p.92 | Shar — Mars, Mercury, Jupiter, Venus, Saturn, Herschel, Neptune | ok | 1 | 12 / 12 |  |
| 119 | p.93 | Moon Shar Parivartan | ok | 1 | 27 / 27 |  |
| 120 | p.94 | Mars Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 121 | p.95 | Jupiter Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 122 | p.96 | Mercury Speed and Vedh | ok | 1 | 4 / 4 |  |
| 123 | p.97 | Venus Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 124 | p.98 | Saturn Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 125 | p.99 | Herschel Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 126 | p.100 | Neptune Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 127 | p.101 | Pluto Speed and Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 128 | p.102 | Chandra Rahu Vedh — Bullish | BLOCKED | 1 | 0 / 0 | see blockers |
| 129 | p.103 | Venus Vedh of Moon in 2026 — Bearish | BLOCKED | 1 | 0 / 0 | see blockers |
| 130 | p.104 | Mercury Vedh of Moon in 2026 — Bearish | BLOCKED | 1 | 0 / 0 | see blockers |
| 131 | pp.105-106 | Sun Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 132 | pp.107-108 | Mars Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 133 | pp.109-111 | Mercury Nakshtra Vedh | ok | 1 | 34 / 34 |  |
| 134 | pp.112-113 | Venus Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 135 | p.114 | Jupiter Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 136 | p.115 | Saturn Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 137 | p.116 | Rahu Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 138 | p.116 | Ketu Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 139 | p.117 | Herschel Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 140 | p.118 | Neptune Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |
| 141 | p.119 | Pluto Nakshtra Vedh | BLOCKED | 1 | 0 / 0 | see blockers |

## Blocked sections and the input each is missing

| B | section | rule | missing input |
| --- | --- | --- | --- |
| 5 | Mars in Pisces Navmansh (D9) | `b005_not_an_ingress_view` | Mars's rashi windows while its navamsa is Pisces -- a residency rule over a D9 position, not a D9 ingress series, and the layer emits no Mars D9 ingress table because the source prints none |
| 6 | Vargottam Mars | `b006_not_an_ingress_view` | Vargottam Mars -- needs the D1 and D9 signs to agree at an instant, and the config already notes the source prints no Mars D9 ingress table to bound it |
| 11 | Mercury - Furthest from Sun | `b011_mercury_furthest_from_sun` | a greatest-elongation event class. The astronomy layer emits elongation per record but never its extrema, and recovering a maximum from instants sampled at other events would be a scan, not a read |
| 19 | Venus Ahead, Sun Behind and Mercury in the Middle | `b019_venus_ahead_sun_behind_mercury_middle` | a benefic/malefic classification of the aspects on a body. The remark's verdict holds only 'provided there is a malefic aspect on Mercury'; the layer carries aspect records but no valence for them, and the source prints none either |
| 30 | Demoted and Shadow Speed of Saturn | `b030_demoted_shadow_speed_of_saturn` | a rule, not merely the interval. B30 states when Saturn is in Demoted or Shadow Speed -- from 11-Dec-2026 until it crosses back over 20 deg 31' of Pisces direct on 15-Mar-2027 -- and its two printed values are VERIFIED to the arcminute (the engine puts Saturn at 20.508963 deg on 27-Jul-2026 and 20.507990 deg on 15-Mar-2027, and at 13.694991 deg on 11-Dec-2026). What the section never states is what makes a planet Demoted or Shadow: it names the band and the two dates and no condition. So the interval can be reproduced and the rule that generates it in another year cannot |
| 62 | Chandra Darshan (New Moon) | `b062_chandra_darshan` | a first-crescent visibility computation. The section's Tithi column reads Pratipada or Dwitiya, so the event is the sighting and not the conjunction; Step 3 measured swe.heliacal_ut against the source's own Venus rise dates and found it 9-10 days out, so the one routine available was rejected on evidence rather than on principle |
| 63 | Hemisphere | `b063_hemisphere_range` | a tropical solar longitude, or the equinox instant the layer would have to emit for one to be read. The equinox is a TROPICAL solar longitude of 0 or 180 degrees and every longitude the astronomy layer carries is sidereal ('lon_sid'), which is a frame the equinox slides through by about 50 arc seconds a year. The same record carries qa.ayanamsha_deg, so `lon_sid + ayanamsha_deg` reconstructs the tropical longitude at the instants the layer happens to sample the Sun -- but the Sun's own ingress series only marks whole signs, nakshatras and navamsas, which bracket an equinox date to 3 degrees 20 minutes, and the only dense solar series in the file is the per-venue horizon records, whose existence depends on a location rising. Pinning the date from those means interpolating a longitude between two of one venue's sunsets, and the rule layer is not licensed to reconstruct a longitude: measured, the interpolation reproduces the true equinox to about 5 minutes and the navamsa bracket to about 3.6 hours, so this is a licence question and not a numerical one **AND** a decision on what the range is and what breaks it. The note says 'Calculate range of the Hemisphere +/- 2/3 days any side' and never says the centre; and it says 'Breakout/breakdown is medium term trade' and 'When range is broken on both side, 2nd break is very powerful' without saying whether the range is a range of PRICES or the six-day window in TIME that the sentence before it just built. The word 'range' appears in both senses in the same line |
| 70 | Big Volatile — Major Turning Days | `b070_big_volatile_major_turning_days` | the selection rule itself. The section states only that its dates "have been sorted on multiple parameters" and names none of them and no weighting; four candidate discriminators (lunation, station, sign ingress, inner-planet conjunction or slow-pair aspect) were tested and rejected, and all 51 dates carry at least one major configuration, so the list is over-determined and a fitted reconstruction would describe our fit rather than the source's rule |
| 111 | Moon Eclipse in Vaishak, Shravan or Ashwin Month — Bullish | `b111_lunar_eclipse_in_vaishakha_shravana_or_ashwin` | the lunar month system. Naming a month Vaishakha, Shravana or Ashwin requires knowing whether the source counts months amanta or purnimanta -- the two disagree by a fortnight and therefore about which month an eclipse falls in. `month_system_confirmation` is open in config/conventions.yaml and this is a section it bounds |
| 116 | Mercury in Paap Kartari | `b116_mercury_in_paap_kartari` | a benefic/malefic classification of the bodies. Paap Kartari is a hemming by malefics, and the section's own Planet-1/Planet-2 columns name the bodies that happen to hem Mercury in 2026 without ever stating what makes a body malefic. The same missing input blocks B19 and B117, and it is the third time it has been the binding constraint |
| 117 | Jupiter in Paap Kartari | `b117_jupiter_in_paap_kartari` | a benefic/malefic classification of the bodies. Paap Kartari is Jupiter hemmed between two malefics; the section's own Planet-1 and Planet-2 columns name the two for each printed row and never say what makes them malefic, and the astronomy layer carries each body's sign and nakshatra ingress but no valence for any of them. The identical absence blocks B19 in batch 2, whose verdict holds only 'provided there is a malefic aspect on Mercury' |
| 120 | Mars Speed and Vedh | `b120_mars_speed_and_vedh` | a threshold constrained by more than one crossing. Mars's speed crosses 0.658287 exactly ONCE in the whole of 2026, so the calibration solved one equation in one unknown: the feasible interval is just the speed's own change across the +/-1 day scoring window, and no other printed row in the year can falsify it. Zero degrees of freedom. The fit is therefore true by construction and carries no evidence, so the Vedha direction cannot be anchored to it. Mercury is the only inner planet whose level is overdetermined (six crossings); a later year supplying a second crossing for Mars would make this testable rather than re-derivable |
| 121 | Jupiter Speed and Vedh | `b121_jupiter_speed_and_vedh` | a slow-planet speed doctrine. Jupiter's Fast and Normal boundaries have no common speed level -- the two printed boundaries are 0.013750 (Jupiter) apart in threshold space. B30 'Demoted and Shadow Speed of Saturn' p.26 shows the slow planets answer to a different doctrine and defines its interval by LONGITUDE (Saturn at 20 deg 31' of Pisces, crossed retrograde 27-Jul-2026 and direct again 15-Mar-2027), supplying no speed level, so the class cannot be computed and the Vedha direction cannot be selected |
| 123 | Venus Speed and Vedh | `b123_venus_speed_and_vedh` | a threshold constrained by more than one crossing. Venus's speed crosses 1.223981 exactly ONCE in the whole of 2026, so the calibration solved one equation in one unknown: the feasible interval is just the speed's own change across the +/-1 day scoring window, and no other printed row in the year can falsify it. Zero degrees of freedom. The fit is therefore true by construction and carries no evidence, so the Vedha direction cannot be anchored to it. Mercury is the only inner planet whose level is overdetermined (six crossings); a later year supplying a second crossing for Venus would make this testable rather than re-derivable |
| 124 | Saturn Speed and Vedh | `b124_saturn_speed_and_vedh` | a slow-planet speed doctrine. Saturn's Fast and Normal boundaries have no common speed level -- the two printed boundaries are 0.013750 (0.002594) apart in threshold space. B30 'Demoted and Shadow Speed of Saturn' p.26 shows the slow planets answer to a different doctrine and defines its interval by LONGITUDE (Saturn at 20 deg 31' of Pisces, crossed retrograde 27-Jul-2026 and direct again 15-Mar-2027), supplying no speed level, so the class cannot be computed and the Vedha direction cannot be selected |
| 125 | Herschel Speed and Vedh | `b125_herschel_vedha_unreached` | a calibrated speed level for an outer planet. No outer planet has one -- the source prints no Fast/Normal boundaries for them at all -- and B30 shows the slow planets answer to a longitude doctrine instead, so there is no level to fit and no class to select a direction from |
| 126 | Neptune Speed and Vedh | `b126_neptune_vedha_unreached` | a calibrated speed level for an outer planet. No outer planet has one -- the source prints no Fast/Normal boundaries for them at all -- and B30 shows the slow planets answer to a longitude doctrine instead, so there is no level to fit and no class to select a direction from |
| 127 | Pluto Speed and Vedh | `b127_pluto_vedha_unreached` | a calibrated speed level for an outer planet. No outer planet has one -- the source prints no Fast/Normal boundaries for them at all -- and B30 shows the slow planets answer to a longitude doctrine instead, so there is no level to fit and no class to select a direction from |
| 128 | Chandra Rahu Vedh — Bullish | `b128_moon_rahu_vedha_unreached` | a speed level for the Moon. This table keys on the Moon's class and no threshold work has been done for the Moon at all -- it has no Fast/Normal table in the source |
| 129 | Venus Vedh of Moon in 2026 — Bearish | `b129_venus_vedha_unreached` | the same input that withdrew B123: Venus's level was fitted to a single crossing and carries no evidence, so the class this table keys on is unearned |
| 130 | Mercury Vedh of Moon in 2026 — Bearish | `b130_mercury_vedha_unreached` | scope rather than an input: this table's key (Mercury's class) IS calibrated and overdetermined, so the section is portable in principle and was not ported in this batch. Registered blocked rather than omitted so the gap is visible as scope and not mistaken for a missing input |
| 131 | Sun Nakshtra Vedh | `b131_sun_vedha_unreached` | a calibrated speed level for this body. The threshold calibration covered Mercury, Venus and Mars only; the Sun has no Fast/Normal table in the source and the nodes have none either, so no level exists to fit |
| 132 | Mars Nakshtra Vedh | `b132_mars_nakshatra_vedh` | a threshold constrained by more than one crossing. The class this table keys on is Mars's speed class, and Mars's level was fitted to a single crossing, so the class it computes is not evidence. Withdrawing the wheel lookup follows from withdrawing the threshold: the target is transcribed correctly (96 of 96 printed rows resolve through the wheels) but the KEY is unearned |
| 134 | Venus Nakshtra Vedh | `b134_venus_nakshatra_vedh` | a threshold constrained by more than one crossing. The class this table keys on is Venus's speed class, and Venus's level was fitted to a single crossing, so the class it computes is not evidence. Withdrawing the wheel lookup follows from withdrawing the threshold: the target is transcribed correctly (96 of 96 printed rows resolve through the wheels) but the KEY is unearned |
| 135 | Jupiter Nakshtra Vedh | `b135_jupiter_nakshatra_vedh` | a slow-planet speed doctrine. This table keys its target on Jupiter's speed class, and Jupiter has no speed level at all -- its two printed boundaries share no threshold. B30 shows the slow planets answer to a longitude doctrine instead and supplies no speed level, so the class cannot be computed |
| 136 | Saturn Nakshtra Vedh | `b136_saturn_nakshatra_vedh` | a slow-planet speed doctrine. This table keys its target on Saturn's speed class, and Saturn has no speed level at all -- its two printed boundaries share no threshold. B30 shows the slow planets answer to a longitude doctrine instead and supplies no speed level, so the class cannot be computed |
| 137 | Rahu Nakshtra Vedh | `b137_rahu_vedha_unreached` | a calibrated speed level for this body. The threshold calibration covered Mercury, Venus and Mars only; the Sun has no Fast/Normal table in the source and the nodes have none either, so no level exists to fit |
| 138 | Ketu Nakshtra Vedh | `b138_ketu_vedha_unreached` | a calibrated speed level for this body. The threshold calibration covered Mercury, Venus and Mars only; the Sun has no Fast/Normal table in the source and the nodes have none either, so no level exists to fit |
| 139 | Herschel Nakshtra Vedh | `b139_herschel_vedha_unreached` | a calibrated speed level for an outer planet. No outer planet has one -- the source prints no Fast/Normal boundaries for them at all -- and B30 shows the slow planets answer to a longitude doctrine instead, so there is no level to fit and no class to select a direction from |
| 140 | Neptune Nakshtra Vedh | `b140_neptune_vedha_unreached` | a calibrated speed level for an outer planet. No outer planet has one -- the source prints no Fast/Normal boundaries for them at all -- and B30 shows the slow planets answer to a longitude doctrine instead, so there is no level to fit and no class to select a direction from |
| 141 | Pluto Nakshtra Vedh | `b141_pluto_vedha_unreached` | a calibrated speed level for an outer planet. No outer planet has one -- the source prints no Fast/Normal boundaries for them at all -- and B30 shows the slow planets answer to a longitude doctrine instead, so there is no level to fit and no class to select a direction from |

## Rules that fire zero times in 2027

Pinned by name in the harness with the reason, so a zero can never be read as a quiet year without someone having checked which kind it is. The three kinds: **calendar-boundary** (the event falls in the carry-in or carry-out), **orbital-period** (the configuration does not occur in this span at all), and **sky** (it is excluded by where the bodies are).

| rule | B | kind |
| --- | --- | --- |
| `b004_mars_combust_cycle` | 4 | calendar-boundary |
| `b012_mars_mercury_conjunction` | 12 | calendar-boundary |
| `b015r_venus_rise_uttara_bhadrapada` | 15 | calendar-boundary |
| `b031_reference_view_rahu` | 31 | calendar-boundary |
| `b034_reference_view_ketu` | 34 | calendar-boundary |
| `b041_herschel_conjunction_mars` | 41 | calendar-boundary |
| `b047_neptune_conjunction_saturn` | 47 | calendar-boundary |
| `b047_neptune_conjunction_mars` | 47 | calendar-boundary |
| `b051_reference_view_pluto` | 51 | calendar-boundary |
| `b052_reference_view_pluto` | 52 | calendar-boundary |
| `b053_pluto_conjunction_mars` | 53 | calendar-boundary |
| `b054_pluto_opposition_jupiter` | 54 | calendar-boundary |
| `b054_pluto_opposition_mars` | 54 | calendar-boundary |
| `b077_kaal_sarp_yog` | 77 | calendar-boundary |
| `b083_mercury_venus_both_retrograde` | 83 | calendar-boundary |
| `b085_mars_behind_jupiter_same_sign` | 85 | calendar-boundary |
| `b086x_mars_crosses_jupiter_eleven_days` | 86 | calendar-boundary |
| `b087s_moon_rahu_same_nakshatra_rahu_in_shatabhisha` | 87 | calendar-boundary |
| `b089s_mars_in_rohini` | 89 | calendar-boundary |
| `b107_venus_alone_in_shravana` | 107 | calendar-boundary |
| `b112_venus_mercury_together_in_shravana` | 112 | calendar-boundary |
| `b113_mars_in_dhanishta` | 113 | calendar-boundary |

## Rules firing on a reading we supplied

Never counted in with the executable rules. The words these fire on are partly ours, and every row carries the flag naming what was supplied.

| rule | B | flag |
| --- | --- | --- |
| `b015c_venus_rise_star_list` | 15 | nakshatra_name_elided_in_source |
| `b055_panchak` | 55 | panchak_definition_supplied_not_printed |
| `b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak` | 56 | panchak_definition_supplied_not_printed |
| `b064_pradosh` | 64 | pradosh_definition_supplied_not_printed |
| `b094_shani_chandra_dwidwadash_yog` | 94 | dwidwadash_definition_supplied_not_printed |

## Sections whose wording admits more than one reading

### B55 — Panchak

`b055g_panchak_after_forty_ghati`. '40 Ghati' is a time of day, and the sunrise series now fixes the instant it is counted from. What it does not fix is the length of the ghati, and the two readings in currency are not the same statement. Under the FIXED reading a ghati is 24 minutes -- a sixtieth of 24 hours, which is the sense B106 uses, correctly, because there it measures a DURATION and 24 minutes is a sixtieth of a day however the day is bounded. Under the VARIABLE reading a ghati is a sixtieth of the actual sunrise-to-sunrise day, which in Mumbai runs 23h58m to 24h02m across the year and in New York 23h46m to 24h14m. Forty ghati in is 16h00m under the first and up to nine minutes away from it under the second. The section prints no table of 40-ghati Panchaks -- its thirteen rows are the Panchak windows themselves, which both readings date identically -- so the document offers no row that could choose between them, and picking one would be this layer's decision rather than a reading of the page.

## What this page does not cover

This is the **condition** layer: dated, per location, traceable to a page. It states when a rule's condition holds. It does **not** yet state what the market does — that is the verdict layer, which applies `evidence_source` x `construction` per instrument and per venue day, and then renders. Nothing here is a forecast or investment advice.

**And "this page" is not the whole source.** It covers catalogue B. Of the 58 named groups of the instrument configuration sections (Chapter 1, Sr.No 149-154), **38 are ported and reach the rows above** and 20 are blocked on a named input, per group in `build/CONFIG_PORT_REPORT.md`; `build/CONFIG_SECTIONS_SCOPE.md` is the scope survey as it stood BEFORE that port and its ported column is a record of that date, not a live count. The source's monthly prophecy tables (Chapter 3) are unported and are not scoped anywhere yet. See **Coverage, in two denominators** at the top of this page before reading any number on it as a statement about coverage of the document.
