# Step 3 — Closing Report

**FinAstro 2027, astronomy layer.** Written for review before any Step 4 decision.
Step 4 has not started.

This document records what is true as of the build below, including what is
weakly evidenced. A gap recorded here is cheaper than a gap discovered in Step 4.

| | |
| --- | --- |
| Report date | 12-Sep-2026 |
| Engine | `finastro/step3-astronomy` |
| Ephemeris backend | `moshier` (Swiss Ephemeris data files not yet used — see gap G-1) |
| Ayanamsha / node | LAHIRI / mean |
| Span generated | 01-Dec-2026 → 01-Feb-2028 IST (carry-in and carry-out, so no window is truncated at a year boundary) |
| Source document | `data/source_2026.html`, 437578 bytes, md5 `5e098446d6dd13d3df8443528db5dd95` |

---

## 1. Final record counts

1569 records, astronomy only. No interpretation field exists in the schema yet.

| event_class | records | of which carry a named 2026 source section |
| --- | ---: | ---: |
| sign_ingress | 250 | 63 |
| nakshatra_ingress | 562 | 45 |
| navamsa_ingress | 542 | 44 |
| lunation | 58 | 29 |
| apsis | 34 | 34 |
| conjunction | 33 | 13 |
| opposition | 27 | 13 |
| combustion | 22 | 22 |
| station | 22 | 20 |
| total_day | 12 | 12 |
| eclipse | 7 | 7 |
| **TOTAL** | **1569** | **302** |

Certainty grades: **A 1497, B 72.** B is stations (22), apsides (34) and the
definition-sensitive combust/rise events (16 of 22) — every grade B record is one
where the quantity is stationary to second order or depends on a rise/set
convention, never one where the arithmetic is doubtful.

The remaining **1267 records carry `source_section_not_printed_in_2026`**. That
flag now means one thing only: the 2026 document prints no section for that body
in that class. It does not mean "we could not look". Breakdown: nakshatra_ingress
517, navamsa_ingress 498, sign_ingress 187, lunation 29 (the quarter moons — the
source tracks only the syzygies), conjunction 20, opposition 14, station 2 (Mars,
which does not station in 2026, so the source had no occasion to print one).

**Changed this session:** 61 Mars `navamsa_ingress` records moved from "has a
source section" to this flag. See §7.1.

---

## 2. Build hash and determinism

```
sha256  c3a45926eb0a97e9e429e37487f10fa004818828bb3d00d123840ebefd16365d  build/astronomy_2027.json
sha256  166f0d04e50facb0fb6d18654db1ab1380d6dec46903d79b399b5d314a29142e  build/astronomy_2027_summary.txt
sha256  2ecb5e26fa3503e65255ca1979c36498ea6de97d67d8eef7c51df041ed33e629  config/conventions.yaml
```

The config hash has moved twice — for the `source_defects` block of §6.8 and for
the weekday coverage and extras blocks of §4.3 — while the build hash has **not**
moved at all. That is the expected result and a useful check: the
findings and defect blocks are documentation the engine does not read, so
recording them cannot silently move a date.

**Determinism confirmed empirically, not asserted:** `build_2027.py` was run twice
in succession and the two outputs compared with `cmp`. Byte-identical. Records are
sorted by `(t_start_utc, id)` and ids are checked for collisions at build time
(0 duplicates across 1569 records), so ordering cannot drift and a real change
shows up as a diff while nothing else does.

The hash is over Moshier output. It **will** change when the Swiss Ephemeris data
files are used (gap G-1); that diff is the point of the exercise, not a regression.

---

## 3. Test harness

| Suite | Result |
| --- | --- |
| `tests/test_2026_regression.py` | **55/55** — locks the conventions against the source (was 40/40: +7 for the Bhadra check of §6.8, +8 for the weekday transcription of §4.3) |
| `tests/test_2027_astronomy.py` | **79/79** — sanity-checks the generated 2027 output |
| `tests/test_node_anchor_unit.py` | **12/12** — the node-anchor branch the real span cannot reach |

`README.md` now quotes these figures and the build hash (G-8 closed).

---

## 4. Conventions empirically derived from the source

Each entry: what was adopted, the evidence in the source, and the pass rate.

### 4.1 Ayanamsha — Lahiri

**Evidence.** Source: Sun → Capricorn 14-Jan-2026 15:08 IST. Lahiri computes
15:07; KP computes 12:50; Raman computes the previous day.

**Pass rate.** 1/1 discriminating test, resolved to the minute. Two rivals
excluded by 2h18m and by a full day respectively.

**Residual.** A 1-minute gap remains and is not explained; it is inside the noise
between Lahiri variants. Certainty A.

### 4.2 Node — mean, not true

**Evidence.** Source: Rahu → Capricorn 05-Dec-2026 21:52 IST. Mean node computes
22:32; true node computes 25-Nov, ten days earlier.

**Pass rate.** 1/1 discriminating test. The rival is excluded by 10 days.

**Residual.** A 40-minute gap remains. Quantified rather than waved past: the mean
node moves 190.6″/day, so 40 minutes is **5.3 arcseconds** of node motion, against
a sign boundary 108000″ away. Nothing sign-level can turn on it, and all four node
Relationship values are unmoved. Certainty A.

### 4.3 Weekday rule — civil-day overlap

**Evidence.** Four conventions tested by reproducing 13 weekday-rule tables,
75 dated rows:

| Convention | Rows reproduced |
| --- | ---: |
| Tithi/nakshatra prevailing at sunrise | 51 / 75 |
| **Any overlap with the local civil day** | **74 / 75** |
| Sunrise-to-sunrise day | 73 / 75 |
| Market-session overlap only | 64 / 75 |

Independently corroborated by the source's own From/Till annotations, which land
on civil-day span boundaries: Mrigashira Thu 01-Jan "From 22:50" → computed 22:48
(1 min); Vyatipata 07-Apr "Till 16:17" → 16:16; Vyatipata 15-Feb "From 03:18" →
03:17.

**Pass rate in the locked harness — now complete (G-4 closed).** Every
weekday-conditioned per-date table in the document is transcribed and locked:
**12 families, 64 printed rows, 63/63 reproduced** after subtracting one row that
is a source defect (below), plus 3/3 span-boundary times within 1 minute.

| Family | Section | Printed | Reproduced | Extras |
| --- | --- | ---: | ---: | ---: |
| Ekadashi on Friday | p.54 | 6 | 6 | 0 |
| Mangal Ashwini Yog (Ashwini on Tuesday) | p.61 | 1 | 1 | 2 |
| Ashtami on Tuesday/Saturday/Sunday | p.62 | 9 | 9 | 12 |
| Ashtami on Monday, Thursday and Friday | p.63 | 12 | 12 | 6 |
| Shukla Pratipada on Saturday/Sunday | p.77 | 4 | 4 | 1 |
| Vyatipata on Tue/Sat/Sun | p.77 | 9 | 9 | 0 |
| Shukla Shasthi on a Friday | p.80 | 1 | 1 | 2 |
| Anuradha on Sunday | p.80 | 2 | 1 + 1 defect | 1 |
| Shatabhisha on Tuesday | p.80 | 3 | 3 | 2 |
| Mrigsira on Thursday | p.82 | 6 | 6 | 0 |
| Uttra Shada on Monday | p.83 | 4 | 4 | 0 |
| Shukla Trayodashi on Tuesday/Saturday | p.86 | 7 | 7 | 1 |
| **Total** | | **64** | **63 + 1 defect** | **27** |

**No rule family systematically fails.** Every family reproduces 100% of its
printed rows. The convention is not right for some rule types and wrong for
others — the question that would have changed Step 4 materially is answered, and
the answer is no.

**The one non-reproduced row is a source defect, not a convention failure.**
*Anuradha on Sunday p.80* prints 28-Jun-26. The Moon is in **Jyeshtha for the
whole of that day**; Anuradha runs 26-Jun-26 19:16 (Fri) → 27-Jun-26 22:11 (Sat)
and never touches a Sunday in that lunation. Asserted as absence across the entire
civil day at 10-minute resolution, so sunrise-at-dawn, civil-day overlap,
sunrise-to-sunrise and market-session **all** agree it is not a qualifying day. The
printed date is one day after the true one and the window closes at 22:11 the
evening before — the same off-by-one-day class as the p.133 appendix rows (§6.2).
Recorded in `source_defects` and asserted by its own harness check, so it is
subtracted from the denominator openly rather than tolerated silently.

**Five weekday-bearing tables are deliberately not fixtured**, each with its
reason recorded in `WEEKDAY_TABLES_NOT_FIXTURED`: *Moon Eclipse on Tuesday p.87*
(the condition is an eclipse, not a panchang predicate), *Moon in Mrigsira on
Monday p.78* (its two rows are one window's start and end, not qualifying
Mondays), *Three Saturday in Shukla Paksh p.80* (a date range, not a per-date
rule), *Shukla Ekadashi Vyatipath or Vaidhrati Yog p.85* and *Tithi lesser than
Chaturdashi p.84* (their Day columns are descriptive — no weekday conditions the
rule). None is a weekday rule in the sense under test.

**One source inconsistency surfaced by the transcription.** *Ashtami on Tuesday /
Saturday p.62* prints three **Sunday** rows (11-Jan, 10-May, 24-May) under a title
naming only Tuesday and Saturday, and its columns are sheared (5 headers, 4 values
per row). The weekday set in the fixture is read off the rows the source actually
prints rather than off its title, and the mismatch is recorded rather than
silently narrowed.

**Still weakly evidenced (G-5, still open).** The convention emits **27 dates the
source does not print**. Those are not tuned away — see §4.3a. Certainty B for the
family.

### 4.3a The 27 extras — G-5 is a pattern, not an isolated oddity

Grouped by family, in the table above. The distribution answers the question
directly:

- **They cluster by family, not by month.** 1–5 extras per month across the whole
  year, no part of the year favoured. So it is not a seasonal or
  ephemeris-boundary artefact.
- **Two-thirds are one rule type.** 18 of 27 are the two Ashtami tables.
- **Four families have zero extras and reproduce the source exactly** —
  Ekadashi/Friday, Mrigsira/Thursday, Vyatipata, Uttra Shada/Monday (25 rows,
  exact). Those four read as **exhaustive** lists; the other eight read as
  **selected** ones.

So the original Shatabhisha/Tuesday pair is **one instance of a pattern**, not an
isolated oddity. What the pattern is remains unknown: the source appears to print
a subset in eight of twelve families, and the selection criterion is not
recoverable from the document.

**Two candidate discriminators were tested and both rejected** (tested, not
applied — the convention was not adjusted):

| Hypothesis | Result |
| --- | --- |
| Extras are short — the condition only clips the civil day | **Rejected.** Extras do skew short (median 6.4h of condition inside the day vs 16.0h for printed rows; 13/27 extras under 6h vs 6/63 printed). But the distributions overlap: one *printed* row holds only 1.2h (Mrigsira Thu 01-Jan-26) and one *extra* holds 20.6h. No threshold separates them. |
| Extras are the ones not prevailing at sunrise | **Rejected decisively.** A sunrise filter would keep 15 of the 27 extras while discarding 48 of the 63 printed rows — consistent with the original sweep, where sunrise-at-dawn reproduced only 51/75. Sunrise fails as a secondary filter just as it failed as a primary rule. |

The margin is therefore known and bounded — 27 extras against 63 reproduced rows —
but unexplained. Step 4 must treat a weekday-rule hit that the source does not
print as *emitted but unconfirmed*, not as an error and not as a fact.

### 4.4 Combustion — classical kalāṃśa, thresholds calibrated from the source

**Evidence.** Three hypotheses tested against the source's combust/rise dates:
fixed ecliptic-elongation orbs **rejected** (Mercury's events spread 10.0°–15.4°);
`swe.heliacal_ut` modern visibility **rejected** (Venus off 9–10 days, Mars 13);
classical kalāṃśa **confirmed** — measured that way the source's dates give a
near-constant value per body (Jupiter 9.42 and 9.44, Saturn 12.84 and 12.63), each
sitting a uniform ≈2.3° below the classical table, i.e. a rise/set convention
offset rather than a different method.

**Pass rate.** 21/21 in-year rows, each within that body's own `precision_days`:
Mercury 13/13 (±2d), Venus 3/3 (±1d), Mars 1/1 (±2d), Jupiter 2/2 (±1d),
Saturn 2/2 (±1d).

**Weakly evidenced.** Mars rests on **2 calibration points** (15.48, 15.03) and
only **1** in-year assertion row — the weakest calibration in the config, held at
certainty B with a note to upgrade if more points appear. Config says "validated
against all 23 source combust/rise dates"; 23 counts the two rows whose combust
date falls in 2025 (Mars 06-Nov-25, Venus 12-Dec-25), which were used for
calibration but fall outside the assertion window — gap G-6.

**Precision is measured, not chosen.** `precision_days` = calibration scatter ÷
body's daily rate of change in kalāṃśa. Mercury ±2d = 1.66° spread at ≈0.45°/day.

### 4.5 Total Days — `dd + mm == yy`

**Evidence.** Pure arithmetic, no ephemeris. **Pass rate 12/12, zero extras.**
Certainty A. This is the only derived list that is fully closed.

### 4.6 Dignity — Parashari, and the frame it is read in

**Evidence.** Every parenthetical dignity word in the document was swept out and
checked. Five of seven planets are witnessed: Mars, Mercury, Venus, Jupiter (all
four states each) and Saturn (own only). Nothing outside the Parashari table is
labelled anywhere, so the source neither contradicts nor extends the scheme.

**The frames are not the same and the evidence says which is which.** Mars,
Mercury and Venus are witnessed in **rashi (D1)** journey tables; Jupiter and
Saturn in **navamsa (D9)** tables. Saturn settles it: its rashi sign is Pisces all
year (no dignity at all) while *Saturn in Navmansh (D9) p.25* prints
`Capricorn (Own)` — a row that would be blank in the rashi frame.

**Pass rate.** All 5 printed D9 dignity rows reproduce from the navamsa sign
(5/5). Read in the rashi frame only 1 of the 5 matches, and that one is Jupiter's
Cancer window which the source itself labels Vargottam — so 4 of 5 rows actively
discriminate and the fifth is evidence for neither, recorded as `undetermined_by`
rather than counted.

**Engine consequence.** Dignity is emitted per chart under distinct names —
`dignity` from `sign`, `navamsa_dignity` from `navamsa` — never collapsed.
223 records in the 2027 output are ones where the two frames actually differ,
0 mismatched.

### 4.7 Vargottama — D1 sign == D9 sign, a state beside dignity and not a dignity

**Evidence.** The source prints both at once — `Cancer (Exalted, Vargottam)` — so
they are simultaneous states, not alternatives. Witnessed across three surfaces:
the dedicated *Vargottam Mars p.7* (9 rows), inline in four D9 tables (6 rows),
and the *Planet Vargottam in Their Own Nakshatra p.133* appendix (19 rows, a
narrower filter over the same boolean, not a second rule).

**Pass rate.** 15/15 printed rows are D1 == D9 at their midpoint, and 15/15 print
that shared sign. 10 of the 15 discriminate against the immediately preceding
instant (the other 5 continue a prior window or open at year start, and are
recorded as non-discriminating rather than counted). 19/19 appendix rows are
vargottama, 19/19 also have the planet in a nakshatra it lords. Vargottama is a
minority state — 1031 of 7300 samples — so the row checks are not trivially true.

**Emitted on every positional record**, not only on D9 crossings: it is a property
of a position. 244 of 1569 records carry it true, across all 11 classes.

### 4.8 Node lord relationship — a period value, anchored at the node's ingress

**Evidence.** The nodes carry no dignity, so the source prints a Relationship
column instead. **Pass rate 4/4** values reproduce when anchored at the
05-Dec-2026 node ingress; anchoring at year-start or year-end each fails 2 of 4.
Certainty A for the rule, with the 5.3″ caveat of §4.2.

### 4.9 Conjunction universe — the Moon is excluded, by the source's own words

**Evidence.** Two headings state it: "Pluto Conjunction with Other Planets
(**Except Moon**) p.41" and "…Opposition… (Except Moon) p.42". All eight pair
tables were then read row by row and **none** carries a Moon row.

**Pass rate.** 8/8 tables honour an exclusion stated twice. 0 Moon records in the
conjunction or opposition class in the 2027 output.

### 4.10 Ingress geometry — the cusp is authoritative, not the sample

**Not from the source; forced by it.** A sign cusp is **always also a navamsa
cusp**, so at either kind of ingress a sampled position can land on the far side
of both boundaries at once, and `vargottama` — an equality between the two
frames — would be decided by which side of a milliarcsecond the sample fell on.
Both frames are therefore derived from the crossing index.

**Measured effect on the current 1569-record build** (792 ingress records):

| | records |
| --- | ---: |
| recorded rashi `sign` differs from the sampled value | **149** |
| recorded `navamsa` differs from the sampled value | 387 |
| both differ on the same record | 149 |
| `vargottama` differs from what sampling would have given | 43 |

The 149 rashi corrections are a **subset** of the 387 navamsa corrections, not
additional to them — because the two frames share cusps, every record whose sign
moves is also a record whose navamsa moves. An earlier expectation that the two
counts would add was formed before that was established; it was the expectation
that was wrong, not the fix.

**Pass rate:** 0 inconsistent records on both directional checks (sign_ingress
navamsa is the entered sign's first-or-last navamsa; navamsa_ingress sign is the
sign containing that navamsa arc), and 81/81 forward ingresses into a movable sign
are vargottama, as they must be.

---

## 5. Conventions carried from textbook or owner decision, with **no** source evidence

These are load-bearing and unwitnessed. Any Step 4 claim resting on one of them
must inherit that status.

| Convention | Status | Note |
| --- | --- | --- |
| **Sun's dignity** (own/trine Leo, exalted Aries, debilitated Libra) | Parashari, untested | The source labels the Sun nowhere. See §7.2. |
| **Moon's dignity** (own Cancer, exalted Taurus, debilitated Scorpio) | Parashari, untested | No journey or navamsa table for the Moon exists, so the source never had the chance. |
| **Saturn — Aquarius (own, trine) and Aries (debilitated)** | Parashari, untested | Never occupied in 2026. Saturn's `Capricorn (Own)` **is** witnessed. |
| `exaltation_degrees` (deep exaltation) | Textbook, informational only | Exposed as `deep_exaltation_deg`; **never** used to decide a label. Dignity is whole-sign, exactly as the source labels it. |
| Node dignity = `null`, use lord relationship | Deliberate non-decision | The Taurus/Scorpio vs Gemini/Sagittarius node-exaltation dispute is left unresolved on purpose. |
| `abhijit_span_deg` 276°40′–280°53′20″ and the 28-division | Textbook, untested | Reserved for Vedha tables; the 27-scheme used for transits **is** validated (Sun → Shravana 24-Jan-26 10:51 source vs 10:50 computed). |
| Vargottama via the Parashari navamsa mapping | Rule witnessed, mapping textbook | 15/15 printed rows reproduce, so the mapping is corroborated in effect. |
| Classical combustion thresholds | **Superseded** | Retained only as comments beside the calibrated values; the engine uses the calibrated numbers. |
| `penumbral_impact: low` | Framework/owner | Not a source claim. |
| `impact_tier` T1/T2/T3 | Framework/owner | Not a source claim. |
| `claim_tag` set and `confidence_default: untested` | Framework/owner | Step 4 machinery; nothing populates it yet. |
| Instruments, sessions, New York as secondary location | Owner | Mumbai **is** the source's own reference (NSE/BSE/MCX). |
| Moon excluded from the D9 series | Owner/task | Its navamsa changes roughly every 4 hours; a D9 series would be noise. |
| Station precision minutes (inner) / hours (outer) | Reasoned from geometry | Longitude is stationary to second order at a station. Not a source convention. |
| Apsis certainty B | Reasoned from geometry | Distance is flat around an apsis. |
| `big_volatile` | **Undocumented — certainty C** | All 51 source dates carry a real configuration, but the list is over-determined and the weighting is not recoverable. Emitted as flagged candidates, never as fact. |
| `sankranti_muhurta` | Deferred | The 15/30/45 division rule is not in the document. |
| `rainfall` | Dropped | Owner decision. |

---

## 6. Source defects found

Every defect below was verified this session against the document and against a
recomputation. Nothing here is carried on assertion.

### 6.1 Headline conjunction off by 12h42m — **verified**

The source bills *Saturn Neptune Conjunction* as the Event of the Year and prints
**20th February 2026 @ 09:40** (pp. 211–213, repeated at p.37 and in the February
events table).

**Corrected value: 20-Feb-2026 22:22 IST.** Delta **12h 42m 11s**.

Verification: exact sidereal conjunction solved by the engine; separation at the
source's instant is 0.0426° (2.6′), separation at the computed instant is 0.0°.
This is the defect that motivates the project rule *nothing is typed twice*.

### 6.2 Four appendix end dates one day late — **verified, with two controls**

*Planet Vargottam in Their Own Nakshatra p.133*, Moon/Rohini pada 2:

| Window start (printed) | End printed | End computed | Verdict |
| --- | --- | --- | --- |
| 28-Jan-26 15:00 | 29-Jan-26 20:33 | **28-Jan-26 20:30** | date typo |
| 20-Apr-26 09:59 | 21-Apr-26 15:20 | **20-Apr-26 15:20** | date typo |
| 11-Jul-26 16:28 | 12-Jul-26 21:50 | **11-Jul-26 21:48** | date typo |
| 01-Oct-26 11:39 | 02-Oct-26 17:15 | **01-Oct-26 17:15** | date typo |

Each printed end is 24 hours plus 0–2 minutes after the true end of the window.
The **times** are right; only the dates are wrong.

**Two control rows were checked alongside them** — the appendix's only other rows
whose window genuinely runs past midnight:

| Window start | End printed | End computed | Verdict |
| --- | --- | --- | --- |
| 24-Feb-26 20:46 | 25-Feb-26 02:24 | 25-Feb-26 02:23 | **correct as printed** |
| 28-Oct-26 18:55 | 29-Oct-26 00:20 | 29-Oct-26 00:18 | **correct as printed** |

The controls are what make this a defect claim rather than a convention claim. A
day-rollover or epoch convention we had not identified would have shifted these
two as well; it did not. The defect is editorial and confined to the four rows.
Nine of the thirteen Moon rows are clean, and all 15 non-Moon appendix rows have
end times inside their window.

**Verification:** independently recomputed against Swiss Ephemeris by the project
owner (four defects + both controls, all six confirmed), and independently
reproduced by the engine from the Rohini pada-2 boundary. The harness asserts the
times and not the printed dates (`4/4 reproduce as a date typo`; `19/19 appendix
rows vargottama, 4 using the corrected end date`).

### 6.3 Year typos — **verified**

Dates printed with the wrong year inside a 2026 calendar:

- `Vaidhrati` yog end **17-Apr-25** 7:23 → should be 17-Apr-26. Printed twice (the
  yog table and the April events table).
- `28-Mar-25` in *Tithi lesser than Chaturdashi p.84* → likely 28-Mar-26.
- `01-Jan-25` in *Nakshtra Vedh p.117* → likely 01-Jan-26.
- `17-Oct-25` in a Mercury with/aspected table whose window ends 16-Nov-26.
- `07-Sep-25` in *Moon Eclipse on Sunday*.

Two of these carry an editorial asterisk in the HTML itself ("* printed as
28-Mar-25 in source (likely 28-Mar-26)"), so the document is partly aware of its
own typos. Note that several other 2025 dates are **legitimate** carry-ins and not
defects — Mars combust 06-Nov-25, Venus combust 12-Dec-25, Jupiter → Gemini
05-Dec-25, Purva Shada 29-Dec-25.

### 6.4 Sheared table columns — **verified**

*Yog* table: the header declares five columns
`Yog | Start Date | Start Time | End Date | End Time`, and rows carry four:
`Vyatipath | 21-Jan-26 | 21-Jan-26 | 18:59`. The start **time** is missing and
every value after it reads one column to the left. Same shear in the Endra rows.

### 6.5 One printed row left unlabelled where the same table labels others

*Saturn in Navmansh (D9) p.25* prints a bare `Libra` for 21-Mar-26 15:00 →
17-Apr-26 14:57 while the same table labels `Capricorn (Own)` twice. Saturn is
**exalted** in Libra. This is a genuine omission — a slot the source opened and
left blank — so the engine emits the label and flags the record
`navamsa_dignity_corrects_source_omission` rather than copying the gap. Checked in
the D9 frame, because against the rashi sign it could never fire (Saturn's rashi
never reaches Libra in either year).

**Caveat — see gap G-3:** this correction path does **not** fire anywhere in the
2027 output. Saturn's D9 in the generated span runs Capricorn–Aquarius–Pisces–
Aries–Taurus–Sagittarius and never reaches Libra, so 0 records carry the flag. It
is exercised by the test suite only.

### 6.6 Labels printed inconsistently for a pair the source labels elsewhere

Evidence about the source's reliability, not about the scheme. The engine always
emits the full state set.

- Mars in Aries: `Own, Trine` (*Journey of Mars p.5*) vs bare `Own`
  (*Vargottam Mars p.7*).
- Venus in Libra: `Own, Trine` (*Journey of Venus p.12-13*) vs bare `Own`
  (*Venus Motion p.14*, *Venus Combust Rise Cycle p.14*).
- Mercury in Virgo: `Own, Trine, Exalted` (*Journey of Mercury p.8*) vs
  `Exalted, Trine` — Own dropped, order changed (*Mars With or Aspecting
  Mercury*).

### 6.7 One section heading spelled three ways

"Planet Vargottam in Their Own Nakshatra" (body) / "…in their own Nakshtra" (table
of contents) / "…in Own Nakshatra" (nav list). Recorded so a future sweep on one
spelling does not conclude the section is missing.

### 6.8 The same event printed at two different times — **verified and resolved**

The document prints its Bhadra (Vishti karana) windows twice and the two
printings disagree on one row:

| Printing | 13-Jan-2026 Bhadra |
| --- | --- |
| *Bhadra — verified against Swiss Ephemeris* pp.120–124 | 13-Jan-26 **02:00** → 15:18 |
| *JANUARY 2026 EVENTS* pg.270–271 | 13-Jan-26 **3:59** → 15:18 |

Same event, same end time, starts 1h58m54s apart.

**Resolved, not merely recorded.** The Bhadra section states its own method, so
the method was implemented rather than trusted: *"A Bhadra (Vishti karana) is a
6° step of Moon−Sun elongation, so the eight windows of each lunar month fall on
karana numbers 8, 15, 22, 29, 36, 43, 50 and 57. Boundaries were found by
bisection on the exact 6° multiples; all times are IST."* Karana *n* spans
[(n−1)·6, n·6) degrees, so 13-Jan-26 is karana 50, elongation 294°→300°.

**Computed: opens 13-Jan-2026 02:00:06 IST, closes 15:18:25 IST.**
**The section is correct. The monthly calendar's 3:59 is wrong, printed 1h58m54s
late.**

**All eight January windows, checked the same way:**

| Computed window | Karana | Section | Monthly calendar |
| --- | --- | --- | --- |
| 02-Jan 18:53 → 03-Jan 05:11 | 29 (Day) | agrees | **absent** |
| 05-Jan 20:54 → 06-Jan 08:02 | 36 (Night) | agrees | **absent** |
| 09-Jan 07:05 → 09-Jan 19:39 | 43 (Day) | agrees | agrees |
| 13-Jan 02:00 → 13-Jan 15:18 | 50 (Night) | agrees | **start wrong by 1h58m54s** |
| 16-Jan 22:22 → 17-Jan 11:16 | 57 (Day) | agrees | **absent** |
| 22-Jan 14:41 → 23-Jan 02:28 | 8 (Night) | agrees | agrees |
| 25-Jan 23:10 → 26-Jan 10:17 | 15 (Day) | agrees | **absent** |
| 29-Jan 03:17 → 29-Jan 13:55 | 22 (Night) | agrees | agrees |

Measured agreement: the section's "verified against Swiss Ephemeris" claim holds
— all **16** of its January boundaries land within **25 seconds** of the computed
value. The monthly calendar has **7 of its 8** boundaries within **79 seconds**;
the eighth is the 13-Jan start, off by 7134 seconds. It also omits four of the
eight windows entirely, so it is an incomplete secondary printing that is
otherwise right to the minute — a single bad row, not a systematic offset.

**Why this is a bad cell and not a different rule.** Three independent reasons:

1. The row's **end** time, 15:18, is correct in *both* printings and matches the
   computed 300° crossing. A different window definition would have moved both
   boundaries; only the start moved. This supplies, from the row's own other
   boundary, what the control rows supply for the appendix defect (§6.2).
2. **No boundary of any kind sits near 3:59.** The neighbouring tithi start is
   12-Jan 12:43, the Moon's nakshatra change 12-Jan 21:05, its sign change
   13-Jan 17:21. 3:59 corresponds to no rule in the neighbourhood.
3. **A timezone error cannot explain it.** The section's Day/Night column is read
   from karana parity — odd = Day Bhadra, even = Night Bhadra — which is a
   property of the tithi-half and not of daylight, so it never shifts with
   timezone. Computed parity reproduces the printed column **8/8**, which
   confirms the karana numbering is aligned, and the start times depend on
   exactly that numbering. One printing is simply wrong.

Note also that elongation is a **difference** of two longitudes, so the ayanamsha
cancels: this computation is identical in the sidereal and tropical frames and
cannot be moved by a frame choice.

**Recorded** in the new top-level `source_defects` block in
`config/conventions.yaml`, to the same standard as the Moon/Rohini rows, and
locked by `tests/test_2026_regression.py::test_bhadra_two_printings` (7 checks).

**Consequence for Step 4.** Bhadra is not an emitted event class in the astronomy
layer, so nothing in this build is affected. When Bhadra enters the rule layer it
must be computed from the karana rule and **must not** be read off the monthly
calendar. The precedence between the two printings is now settled before anything
depends on it.

---

## 7. Changes made this session

### 7.1 The Mars p.6 mapping was wrong and has been removed

`("navamsa_ingress", "Mars") → "Mars in Pisces Navmansh (D9) p.6"` claimed that
table as the 2026 equivalent of Mars's D9 ingress series. **It is not a D9 ingress
series.** Verified 6/6 against the engine: its Sign column is Mars's **rashi** sign
during the six windows in which Mars's **navamsa** is Pisces —

| Printed row | rashi at start / mid / end | navamsa at start / mid / end |
| --- | --- | --- |
| Capricorn (Exalted) 24-Jan → 29-Jan | Capricorn | Pisces |
| Aquarius 16-Mar → 20-Mar | Aquarius | Pisces |
| Pisces - Vargottam 07-May → 11-May | Pisces | Pisces |
| Taurus 30-Jun → 04-Jul | Taurus | Pisces |
| Gemini 28-Aug → 02-Sep | Gemini | Pisces |
| Cancer (Debilitated) 05-Nov → 12-Nov | Cancer | Pisces |

Its dignity labels are therefore **rashi-frame** labels: Mars is exalted in
Capricorn and debilitated in Cancer in the **rashi**, and holds neither dignity in
Pisces, which is the navamsa every one of those rows shares. Mapping it to a D9
class would have cited a rashi-frame table as the source equivalent for a D9
crossing — the exact frame confusion §4.6 exists to prevent.

**Done:** mapping removed from `build_2027.py`. The 61 Mars `navamsa_ingress`
records now carry `source_section_not_printed_in_2026`, which is the true
statement — **the source prints no Mars D9 ingress table**. The table is carried in
`rule_layer_pending` with its frame stated, so it is not lost.

The p.6 table's `Pisces - Vargottam` row remains valid vargottama evidence and is
unchanged in the config and the harness: there rashi == navamsa == Pisces, so no
frame question arises.

### 7.2 The Sun finding is now recorded once

It was two notes — "no dignity label anywhere" and "vargottama on 163 of 1460
samples, never labelled". They are **one editorial absence**, now recorded once
under `source_findings.sun_never_labelled` and cross-referenced from both the
dignity and vargottama blocks rather than duplicated.

**Evidence, dignity side.** The Sun occupies all twelve signs in *Sun Transgression
(Sankranti) p.2* — Aries (exalted), Leo (own + trine), Libra (debilitated) among
them — and that table has **no dignity column at all**, while every other journey
table carries dignity inline. The column was omitted for the Sun specifically.

**Evidence, vargottama side.** The Sun is vargottama on **163 of 1460** six-hourly
2026 samples, in eight windows: Sagittarius, Aquarius, Pisces, Taurus, Gemini, Leo,
Virgo, Scorpio. The Leo window (31-Aug-26 → 03-Sep-26) is vargottama **and** the
Sun's own sign simultaneously — precisely the pairing the source prints for other
bodies as `Cancer (Exalted, Vargottam)` — and it is not printed.

**Distinguished from the structural absences.** The Sun's absence is **editorial**:
the state obtains, the source could have printed it, and did not. Saturn and the
outers are a **structural** absence: the state never obtains, so there was nothing
to print. Verified: Saturn 0/1460 (rashi Pisces all year while D9 runs
Cancer→Scorpio, so they cannot coincide), Uranus 0/1460, Neptune 0/1460, Pluto
0/1460 — the last three despite each having its own D9 table. An editorial absence
is evidence about the source; a structural one is evidence about the sky.

**Engine consequence: none.** The Sun's dignity and vargottama are computed and
emitted normally. What the finding fixes is the **provenance** claim — the Sun's
rows are carried from the scheme and must never be counted as source-witnessed. It
is deliberately **not** filed under `dignity.source_omissions`, which is reserved
for a row the source printed and left blank (§6.5).

### 7.3 Bhadra defect resolved and recorded

The 13-Jan-2026 discrepancy of §6.8 was computed from the source's own stated
karana rule and settled in favour of the Bhadra section. A top-level
`source_defects` block now carries it; the appendix end-date defect stays at
`vargottama.source_defects`, with the two cross-referenced rather than merged, so
each defect sits beside the material it affects. Seven checks were added to
`tests/test_2026_regression.py` (40/40 → 47/47).

### 7.4 Control rows recorded alongside the defect

`vargottama.source_defects` now carries both control rows (§6.2), why they matter,
and the verification method and scope. A defect claimed without a control is a
convention difference waiting to be discovered later.

---

## 8. Open questions

### Blocking for Step 4 — a rule family cannot be built without an answer

| Question | What it blocks | Status |
| --- | --- | --- |
| `speed_class_thresholds` — Atichari / Fast / Normal / Slow / Vakri | The entire **Vedha** family: speed class drives Vedha direction. Also *Exalted Mars if Atichari*. | Undocumented in the source. No candidate rule yet. |
| `aspect_orbs` — graha drishti vs degree orbs | Every aspect-based interpretation rule. The astronomy layer emits only exact (0°/180°) contacts, so nothing downstream can currently ask "within orb". | Not started. |
| `sector_mapping` — book Appendix B vs the source's own lists | All sector attribution in Step 4. | Two candidate sources, not reconciled. |
| `label_scheme_signoff` | Publishing any interpretation. Owner decision, not a research question. | Awaiting owner. |

### Not blocking — Step 4 can proceed; these bound specific claims

| Question | Effect |
| --- | --- |
| `mercury_shar_lag` — source Mercury latitude rows lag computed by 2–7 days | Bounds Shar-based rules only. The lag is unexplained: neither a constant offset nor obviously an ayanamsha or node artefact. |
| `month_system_confirmation` — Purnimanta inferred from eclipse labelling | Inferred, not confirmed. Affects month-keyed rules and month labels, nothing in the astronomy layer. |
| `sankranti_muhurta` (deferred) | The 15/30/45 division rule is absent from the document. |
| `big_volatile` weighting (certainty C) | Reconstructions stay flagged candidates. |

---

## 9. `rule_layer_pending` — the full list for Step 4

Twelve items. These are Moon-planet and residency relationships the astronomy layer
deliberately does **not** emit as degree-exact events; they belong in the rule layer
at sign/nakshatra granularity.

1. **Mars in Pisces Navmansh (D9) p.6** — Mars's rashi windows while its navamsa is
   Pisces. **RASHI-frame dignity labels.** Source remark: "Mars transit from Pisces
   Navmansh (D9) is bearish unless there is some contrary event."
   *(Added this session — §7.1.)*
2. Moon Mars together in the same sign (p.74)
3. Moon and Rahu in the same nakshatra (p.70)
4. Shani Chandra Dwidwadash Yog (p.75)
5. Chandra Rahu Vedh (p.102)
6. Venus Vedh of Moon (p.103)
7. Mercury Vedh of Moon (p.104)
8. Moon Mercury in the same Navamsa
9. Sun Moon on the same degree
10. Moon in Mrigashira on Monday (p.78)
11. Moon Rashi Parivartan Yog with other planets in D1
12. Moonrise on Monday or Friday, Moonrise in Libra, Moon Darshan on Saturday

Items 5–7 depend on the **blocking** `speed_class_thresholds` question.

---

## 10. Known gaps in this layer

G-4, G-7 and G-8 are closed below and struck through — G-4 by transcribing the
remaining rows, which was work rather than wording. **G-3, G-5 and G-9 remain
open deliberately.** Each bounds how much the 2026 source actually validates, and
closing one would require new evidence, not a new sentence. G-5 in particular got
**wider** as a result of closing G-4: the extras are now known to be a pattern
across 8 of 12 rule families rather than a two-date curiosity. They are stated
here so Step 4 inherits them explicitly.

| # | Gap | Blocking? |
| --- | --- | --- |
| G-1 | The build uses the **Moshier** ephemeris. Swiss Ephemeris data files have not been used and no diff has been run. Moshier is sub-arcsecond for 1900–2100, so every date and minute is sound, but the cross-check is unperformed. | Not blocking Step 4. **Blocking publication.** |
| G-2 | `combustion` for **Mars** rests on 2 calibration points and 1 in-year assertion row. Certainty B. | Not blocking; bounds Mars combust/rise claims. |
| G-3 | The `*_corrects_source_omission` path fires on **0** records in the 2027 output (Saturn's D9 never reaches Libra in the span). Tested synthetically only. | Not blocking. Recorded so it is not mistaken for production-verified. |
| ~~G-4~~ | **CLOSED.** Every weekday-conditioned per-date table in the document is now transcribed and locked: **12 families, 64 printed rows**, against 5 families / 28 rows before. **63/63 reproduce** after subtracting one row shown to be a source defect. No family systematically fails. Five further weekday-bearing tables are excluded with a recorded reason each. See §4.3. | Closed. |
| G-5 | **Widened, not closed.** The convention emits **27 dates the source does not print**, across 8 of the 12 families — the original Shatabhisha/Tuesday pair is one instance of a pattern, not an oddity. Extras cluster by family (18 of 27 are the two Ashtami tables), not by month; four families have zero extras and reproduce exactly. Duration and prevailing-at-sunrise were both tested as discriminators and both rejected. The convention was **not** adjusted. See §4.3a. | Not blocking; the margin is now measured (27 against 63) but the selection criterion is unrecovered. |
| G-6 | Config says combustion is "validated against all 23 source combust/rise dates"; the harness asserts **21** (two combust dates fall in 2025, outside the scan window). Wording is imprecise. | Not blocking. Cosmetic but misleading. |
| ~~G-7~~ | **CLOSED.** The instance is the 13-Jan-2026 Bhadra row: 02:00 in the Bhadra section, 3:59 in the January calendar. Computed from the source's own karana rule — the section is right, the calendar is 1h58m54s late. All eight January windows checked, recorded in `source_defects`, locked by 7 harness checks. See §6.8. | Closed. |
| ~~G-8~~ | **CLOSED.** `README.md` now quotes 47/47, 79/79 and 12/12, carries the build hash, and states the 13-Jan Bhadra instance in place of the unevidenced sentence. | Closed. |
| G-9 | 1267 of 1569 records have no named source section. Expected — the source simply does not tabulate most bodies at nakshatra and navamsa granularity — but it means **81% of the output has no 2026 row to check against**, and the regression harness therefore constrains conventions, not coverage. | Not blocking. The single most important limit on how much the 2026 source validates. |

---

## 11. What Step 3 establishes

The astronomy layer is computed once into a canonical record; JSON, and later HTML
and CSV, render from that record, so drift between renderings is structurally
impossible. The build is deterministic and hashed. Every convention is either
witnessed in the source with a stated pass rate (§4) or declared unwitnessed (§5).
Defects in the source are corrected and flagged, never copied, and the corrections
are separated from convention differences by controls (§6.2).

Interpretation is Step 4. The record schema in `finastro/events.py` still has no
field it could occupy, and the harness asserts that no interpretation field has
leaked in.
