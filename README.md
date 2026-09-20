# FinAstro 2027

A Vedic financial-astrology calendar for 2027, rebuilt from the structure of
*Parth Prophecies 2026* but computed rather than transcribed.

The 2026 source is a 437 KB single-file HTML with 233 tables. It is a serious
piece of work, but it carries the defects of a hand-maintained document. The same
event appears at two different times in two different tables: the 13-Jan-2026
Bhadra window opens at **02:00** in the Bhadra section (pp.120–124) and at
**3:59** in the January calendar (pg.270–271), with the same end time in both.
Recomputing it from the source's own stated rule — a Vishti karana is a 6°
step of Moon–Sun elongation — gives 02:00:06, so the section is right and the
calendar is 1h58m54s late. Alongside that: year typos (`17-Apr-25` inside a 2026
calendar), sheared table columns, a table of contents that disagrees with its own
headings, and one flagship claim — the Saturn–Neptune conjunction billed as the
event of the year — that is off by 12 hours 42 minutes.

This project's answer to all of that is a single rule: **nothing is typed twice.**
Every event is computed once into a canonical record, and the JSON, HTML and CSV
are all rendered from that record. Drift becomes structurally impossible.

## Status

Step 3 of the build, plus two late Step-3 extensions delivered during Step 4:
the **tithi and yoga boundary series** (`tithi_ingress`, `yoga_ingress`) and the
**sunrise and sunset series** (`sunrise`, `sunset`). The engine, its regression
harness, and the 2027 astronomy layer are in place. Interpretation is Step 4 and
has not started; the record schema in `finastro/events.py` has no field it could
occupy.

```
$ python3 tests/test_2026_regression.py
112/112 checks passed

$ python3 build_2027.py
4163 records -> build/astronomy_2027.json

$ python3 tests/test_2027_astronomy.py
123/123 checks passed

$ python3 tests/test_node_anchor_unit.py
12/12 checks passed

$ python3 tests/test_rule_layer.py
133/133 checks passed
```

The rule layer carries **171 rules over all 141 catalogue-B sections** — full
coverage of catalogue B: 132 executable, 5 resolved on a supplied reading, 33
blocked with the missing input named, and 1 ambiguous. 3,557 dated rows in the
generated year.

**Catalogue B is not the whole source, and the two numbers are now stated
together.** The instrument configuration sections — gold, silver and sugar, the
three instruments the source prints verdicts for — are a different shape of
markup (`<section id="...">` with an `<h2>`, not `<h3 class="section">`), so
they were never in the 141 and never in its denominator:

```
catalogue B                        141 / 141 sections
instrument configuration sections   38 /  58 named groups   (ported AND wired)
<h2> sub-tables                      3 /  10 sub-tables     (ported AND wired)
```

**38 of the 58 are ported and 20 are blocked, each on a named input**
(`build/CONFIG_PORT_REPORT.md`). **Ported is now wired**, since the 14-Sep-2026
change to `verdicts.py`: `build_verdicts()` fires all three registries, and
**1,468 of the calendar's 7,501 verdict rows originate in a configuration
section**, from 26 of the 38 ported groups. `config_instruments_for` routes a
group to the instrument its BLOCK heading names rather than through the
rulership table, so a *Gold — Bullish* group reaches gold because the source
filed it under gold.

**The third line landed 20-Sep-2026** and is the ten `<h2>` sub-tables of the
same chapter that belong to no instrument block — *Bhadra*, *Total Days in
Year*, *Rahu or Ketu Nakshtra on a Thursday* and seven more. Three are ported
and **824 rows** come from them; seven are registered and blocked with the
input each waits on named, two of those on the Moon's navamsa ingress series,
which the astronomy layer does not emit for the Moon at all. These sections
state no verdict about their own condition, so every sub-table row is
`condition_only` by construction and a guard refuses any rule that arrives
carrying one.

**Ten, and it was nine for five days.** Membership was a byte range from
`<section id="kshin-moon">` to `<section id="gold-bullish">` — where the
reading happened to start — and counting the *shape* over the whole document
found exactly one section outside it: Bhadra, `sec-142`, which the document's
own table of contents lists in the same run one row above Kshin Moon. The rule
is now positive and readable off the page: a configuration block's `<h2>`
states a direction (*Gold — Bullish Configuration*), a sub-table's does not.

The three registries stay separate anyway, and that separation is the point: a
configuration group must never reach `sections_ported()` and inflate 141/141. A
reader must not see 141/141 and conclude the source is covered.

**What the port did not change.** Gold, silver and sugar still also reach the
calendar through generic catalogue-B rules whose bodies happen to resolve to
those instruments — a Venus rule reaches SUGAR because SUGAR's rulership is
Venus, not because the source says anything about sugar. The wiring added the
source's own conditions beside those rows and removed none of them. **To tell
the two apart, read `event`, not `event_section`**: a configuration row's rule
id begins `cfg_<block>_`, while `event_section` carries the group's own printed
title and so never reads `gold-bullish` — which is why the check this page used
to offer still passes and its old conclusion is now wrong.

`build/CONFIG_SECTIONS_SCOPE.md` reports what porting the remaining groups would
take, per group, and `build/MONTHLY_2026_FIXTURE.md` measures what the layer
reproduces of the source's own finished output: **168 of 354 printed windows
(COVERAGE) and 168 of 175 claimed rows (PRECISION, conditional on a rule
existing and firing)**. Neither of those travels alone either.

**`build/RULE_LAYER_STATUS.md` is the one-page answer to "what does this calendar
actually cover"** — both denominators at the top, then every catalogue-B section
with its status, rule count, 2027 row count, and for each blocked section the
input it is waiting for. It is generated from the live registry and the document
itself, not written by hand. `build/STEP4_DECISIONS.md` §12 is the batch-by-batch
record of the arguments behind it, and §12.16 is the recurring failure mode the
build keeps producing.


## The calendar

Three rendered artifacts, all deterministic — rendering twice is byte-identical
for each:

```
build/calendar_2027.json   7,163 rows, the master
build/calendar_2027.csv    the same rows, flat
build/calendar_2027.html   self-contained, with search and filters
```

**7,906 rows over 365 distinct dates, and the split is load-bearing: 7,501
verdict rows and 405 base-track event rows**, told apart by `row_kind`. Of the
7,501, **5,209 come from catalogue B, 1,468 from the configuration groups and
824 from the sub-tables**; 3,414 carry a verdict text and 4,087 do not.

**Quote the split, not the total.** `records` meant "verdict rows" while there
were no others, and a consumer still reading it that way is now wrong by 405.
The verdict count itself has moved four times: 7,484 before the tier_4 scoping
removed 807 USDINR configuration rows that recorded no measurement; 5,209 before
the configuration wiring added 1,468; 6,677 before the first sub-table ports
added 81 on 20-Sep-2026; and 6,758 before Bhadra added **743** the same day,
which is the largest single rule in the build.

**Catalogue B has stayed at 5,209 across both of those ports, and that is the
check rather than a coincidence.** A port that moved it would be a port that had
reached into catalogue B's registry, which is the one thing three separate
denominators exist to prevent.

The verdict layer applies `evidence_source` × `construction` per instrument on
that instrument's **venue civil day**, and it *authors nothing*: verdict text is
the source's own words or it is null, there is no derived verdict, and
**confidence is `untested` on every row** — no code path can raise it. A
base-track row carries no instrument, no tier and no verdict at all — those keys
are absent rather than null.

The HTML carries the epistemic apparatus visibly rather than as a footnote:
certainty grades **and both C grounds**, claim tags, all 33 blocked sections with
the input each waits for, **both pairs of denominators beside the blocked list —
sections ported (catalogue B 141/141, configuration sections 38/58) and rows
reproduced against the source's own 2026 calendar (COVERAGE 168/354, PRECISION
168/175)**, the source
defects found, the known coverage gap, and the standing statement that this is a
speculative interpretive framework and not investment advice.

The build is deterministic: regenerating the year produces a byte-identical
file, so a real change shows up as a diff and nothing else does. Confirmed by
running the build twice and comparing:

```
sha256  757c53126bae410d5d594ee97a8694185b31d7b2a7eef72d6524b75bb22bdf2f  build/astronomy_2027.json
```

That hash is over the Moshier ephemeris. It will change when the Swiss Ephemeris
data files are used, which is the point of that cross-check and not a regression.

A Step 3 closing report — record counts, every derived convention with its pass
rate, every convention carried without source evidence, every source defect, and
the open questions — is in `build/STEP3_REPORT.md`.

## The two panchang boundary series

A tithi is a 12-degree step of the Moon-Sun elongation and a yoga a 360/27 step
of their sum, both bisected to the second -- the method the source states for
its own Bhadra windows, on a different multiple of the same angle. Eight of the
Bhadra section's sixteen January boundaries are also tithi boundaries, and the
series reproduces all eight within **25 seconds**.

The two are not equally frame-free, and the difference is carried on every
record rather than assumed:

| | Angle | Ayanamsha | Measured |
| --- | --- | --- | --- |
| Tithi | Moon **-** Sun | cancels | identical to the second under Lahiri, KP, Raman, Fagan-Bradley and tropical |
| Yoga | Moon **+** Sun | enters twice | Lahiri 64 s, KP 22 min, Fagan-Bradley 3h17m, Raman 5h24m against the source's own printed edges |

Read tropically the yoga edges do not merely shift: they land on different
yogas altogether (4, 21 and 22 in place of 17, 18 and 27). So the yoga series is
certainty A on the same footing as a sign ingress -- exact given a locked,
evidenced ayanamsha -- and not on the "the ayanamsha cancels" footing the tithi
series has.

Both were validated against the source before any rule was wired to them:

| Fixture | Result |
| --- | --- |
| Bhadra pp.120-124, the 8 coincident boundaries | within 25 s |
| 36 printed tithi edges (B65, B73, B74, B75, B76, B109) | 35 within 68 s, 1 source defect |
| Kshay / Vriddhi tables (B66-B69), 28 rows | 28/28, every tithi named correctly, no extra |
| Vyatipata on weekdays (B96), 9 rows | 9/9, no omission and no extra |
| Yoga edges in B96 and B56 | 14 within 64 s |
| Amavasya ghadi (B106), 4 rows | 4/4 within 2 min, 1 source defect |

## Sunrise and sunset are a location property

The third event class, and the only one that is not a fact about the sky. A
tithi boundary is an angle reaching an exact multiple of 12°: it happens once
and the whole Earth shares the instant, which is why those records carry no
location. The Sun meets **one horizon at one place**. A sunrise record without a
location is not an under-specified Mumbai record — it is not a record of
anything — so the schema refuses it:

```python
LOCATION_REQUIRED = ("sunrise", "sunset")   # finastro/events.py
```

Both venues are generated, 427 civil days each, and neither is a fallback for
the other. The source computes its own rise and set for Mumbai alone and says
so; that is a fact about the source, not a licence to let a New York reader
infer the other from an offset. There is no offset: the two sunrises are ~10½
hours apart and the gap moves all year.

**Certainty B, not A, and the record says why.** A rise depends on which part of
the disc touches the horizon, on refraction, and on the horizon's height. Every
record carries `rise_set_convention=disc_center_no_refraction`, `disc=center`,
`refraction=none` and the lat/lon/alt it was taken from.

The document prints exactly four Mumbai times, to the minute, inside the Bhadra
section's prose rather than in any table. The engine reproduces all four within
**4m43s** — and they do **not** decide the convention, which is measured rather
than waved at:

| Convention | Worst | Mean |
| --- | --- | --- |
| disc centre, no refraction (**used**) | 283 s | 194 s |
| disc centre, with refraction | 114 s | 80 s |
| upper limb, no refraction | 208 s | 127 s |
| upper limb, with refraction | 168 s | 59 s |

Every one has errors of both signs, so none is a fixed offset from the source's.
Four times printed to the minute cannot separate conventions whose spread is 4½
minutes. The convention used is the one the kalāṃśa calibration was fitted
under, because kalāṃśa is the gap between a planet's rise and the Sun's rise and
a gap measured between two different conventions is not a gap. A harness check
pins the two strings together so they cannot drift.

**One row of the document decides it independently, and is recorded as worth
exactly that.** B66 prints 23-Feb-26 Saptami as a Kshay tithi. That Saptami ends
24-Feb 07:02:37; Mumbai sunrise that morning is 07:05:07 without refraction and
07:02:29 with it. Without refraction the tithi holds no sunrise and is Kshay on
23-Feb — the printed row. With refraction it is not, and the next tithi is Kshay
on 24-Feb instead. An **eight-second** margin, pointing the same way as the
kalāṃśa calibration.

That row is also the answer to "how far does the B grade travel". Twenty-seven
of the 28 Kshay/Vriddhi rows, and all 25 Pradosh rows, are identical under all
four conventions. The definition-sensitivity is real and it attaches to the
*published time of a rise*, not to the rules conditioned on one.

**Emitting the series found a defect the old checks could not see.**
`panchang.sunrise` anchored its search at local noon and so returned the *next*
day's rise — a true instant under the wrong date. The 28-row Kshay/Vriddhi
reproduction could not catch it: it only counts sunrises inside a tithi, and a
set of instants shifted by a day covers the same interval. It took emitting them
as dated records. The search is now anchored at the venue's own civil midnight,
and two checks keep it there.

## The rule layer has two kinds of location-awareness, not one

A **weekday** rule has one sky-side condition and two calendars: "Anuradha on
Sunday" asks the same question of the sky at both venues and only the date
differs, so the weekday is applied after a span becomes a day at a venue.

A **sunrise** rule has two conditions. Whether a tithi is Kshay — whether any
sunrise falls inside it — is a different question in Mumbai and in New York, and
can come out yes in one and no in the other with no calendar involved. So
`Rule.per_location` calls the condition once per venue, and a rule declaring a
`horizon/` input is *required* to set it; the constructor raises otherwise.

The difference is not theoretical. Across the generated span, Mumbai has 10
bright-fortnight Kshay tithis and New York 11, with **none in common**: a Kshay
tithi is one whose ~21-hour span falls entirely between two consecutive
sunrises, so two venues half a world apart agreeing would be a coincidence.

## The conventions are derived, not assumed

Every convention in `config/conventions.yaml` was either confirmed by the project
owner or recovered empirically from the 2026 source. The interesting ones:

**Ayanamsha — Lahiri.** The source puts the Sun entering Capricorn at 14-Jan-2026
15:08 IST. Lahiri computes 15:07, KP computes 12:50, Raman computes the previous
day. The choice is not a matter of taste; it is measurable to the minute.

**Node — mean.** Rahu enters Capricorn at 05-Dec-2026 21:52 in the source. The
mean node gives 22:32; the true node gives 25-Nov, ten days earlier.

**Weekday rules — civil-day overlap.** Four competing conventions were tested by
reproducing 13 weekday-rule tables (75 dated rows):

| Convention | Rows reproduced |
| --- | --- |
| Tithi/nakshatra prevailing at sunrise | 51 / 75 |
| **Any overlap with the local civil day** | **74 / 75** |
| Sunrise-to-sunrise day | 73 / 75 |
| Market-session overlap only | 64 / 75 |

Confirmed independently by the source's own From/Till annotations, which land on
civil-day span boundaries to the minute.

Every weekday-conditioned per-date table in the document is now transcribed into
the harness — 12 families, 64 printed rows — and the convention reproduces
**63/63** of them. The 64th, `Anuradha on Sunday` 28-Jun-26, is a source defect:
the Moon is in Jyeshtha all that day, so no day convention could produce the row.
No rule family systematically fails.

The convention also emits **27 dates the source does not print**, spread across 8
of the 12 families and concentrated in the two Ashtami tables. These are left
exactly as they are: they are the source's omissions unless evidence says
otherwise, and neither duration nor prevailing-at-sunrise discriminates them from
the rows the source does print. The margin is recorded in
`weekday_rule.extras`, not tuned away.

**Combustion — classical kalāṃśa.** Three hypotheses were tested against all 23
combust/rise dates:

| Hypothesis | Verdict |
| --- | --- |
| Fixed ecliptic-elongation orbs | Rejected — Mercury's events span 10.0°–15.4° |
| Modern heliacal visibility (`swe.heliacal_ut`) | Rejected — Venus off by 9–10 days |
| Classical kalāṃśa | Confirmed |

Kalāṃśa is the gap between planet and Sun at the horizon, expressed in degrees of
time. Measured that way the source's dates give near-constant values per planet
(Jupiter 9.42 and 9.44; Saturn 12.84 and 12.63), each sitting a uniform ~2.3°
below the classical table — a rise/set convention offset, not a different method.
The thresholds are calibrated from the source so the output reproduces it rather
than approximating it.

**Total Days — `dd + mm == yy`.** Reproduces 12/12 with no extras. Arithmetic, so
certainty A.

**Dignity — witnessed for five of the seven planets, across two charts.** The
source labels dignity inline in its journey and navamsa tables, and every label it
prints was swept out of the file and checked against the config block: Mars,
Mercury, Venus and Jupiter have all four states labelled, Saturn only
`Capricorn (Own)`. Nothing outside the Parashari table is labelled anywhere, so the
source neither contradicts the scheme nor extends it.

The labels do not all come from the same chart, and that matters more than it
looks. Mars, Mercury and Venus are witnessed in **rashi (D1)** journey tables;
Jupiter and Saturn are witnessed in **navamsa (D9)** tables. The two frames give
different answers for the same planet at the same instant, so the block is a
single Parashari table assembled from two different readings of the sky:

| Planet | Frame | Section |
| --- | --- | --- |
| Mars | rashi (D1) | *Journey of Mars p.5* |
| Mercury | rashi (D1) | *Journey of Mercury p.8* |
| Venus | rashi (D1) | *Journey of Venus p.12-13* |
| Jupiter | navamsa (D9) | *Jupiter in Navmansh (D9) p.22* |
| Saturn | navamsa (D9) | *Saturn in Navmansh (D9) p.25* |

Saturn settles which frame the D9 tables are using. *Journey of Saturn p.23* says
"Saturn remains in Pisces throughout the year", and Pisces carries Saturn no
dignity at all — yet *Saturn in Navmansh (D9) p.25* prints `Capricorn (Own)`. Read
in the rashi frame that row would be blank. Jupiter agrees: its D9 table prints
`Sagittarius (Own, Trine)`, `Capricorn (Debilitated)` and `Pisces (Own)` while its
rashi sign is Cancer throughout, which would have printed `Exalted` for all three.
Four of the five D9 rows discriminate; the fifth is Jupiter's Cancer window, which
the source itself labels Vargottam, so rashi and navamsa agree there by
construction and it is evidence for neither.

So the engine emits dignity per chart and under a distinct name — `dignity` from
`sign`, `navamsa_dignity` from `navamsa` — and never collapses them into one
field. The one omission the config records, Saturn in Libra, is likewise a D9 row,
and is checked in the D9 frame: against the rashi sign it could never fire, because
Saturn's rashi sign never reaches Libra in either year.

Two absences are recorded rather than papered over. The Sun passes through all
twelve signs in *Sun Transgression (Sankranti) p.2* — Aries, Leo and Libra among
them — and carries **no dignity label anywhere in the document**; that table has no
dignity column at all. The Moon gets no journey or navamsa table, so it never had
the chance. Both are carried from Parashari and are untested by the source, which
`dignity.source_witness` now says in the config instead of leaving it to be assumed.

Saturn's D9 pass through Libra (*Saturn in Navmansh (D9) p.25*, 21-Mar-26 15:00 to
17-Apr-26 14:57) is printed bare while the same table labels `Capricorn (Own)`
twice — a real omission, which the engine corrects and flags rather than copies.

## Precision is measured, not asserted

`precision_days` in the config is the calibration scatter divided by the body's
daily rate of change. Mercury gets ±2 days because 13 calibration points span
1.66° at roughly 0.45°/day. Mars gets ±2 days because there are only two
calibration points. Jupiter gets ±1 because its two points agree to 0.02°.

Stations are checked to 5 minutes rather than 1, because at a station the
longitude is stationary to second order and a sub-arcsecond ephemeris difference
moves the clock time by minutes. The source's own slow-planet stations drift by
up to an hour for exactly this reason.

## Layout

```
config/conventions.yaml        every locked decision, with its evidence
finastro/config.py             loads the above
finastro/ephem.py              sidereal positions, ingresses, stations, eclipses
finastro/timezones.py          IST primary, Eastern secondary, DST via IANA
finastro/panchang.py           tithi/nakshatra/yoga/karana, sunrise/sunset,
                               the weekday-rule engine
finastro/combustion.py         kalāṃśa asta/udaya
finastro/events.py             the canonical record; layers kept separate
build_2027.py                  generates the 2027 astronomy layer
tools/build_2026.py            the same build, year set to 2026 -- the
                               fixture year
tools/gen_status.py            -> build/RULE_LAYER_STATUS.md
tools/cfg_port_report.py       -> build/CONFIG_PORT_REPORT.md
tools/gen_cfg_scope.py         -> build/CONFIG_SECTIONS_SCOPE.md
tools/monthly_match.py         the 2026 monthly-calendar fixture
tests/test_2026_regression.py  locks the conventions against the source
tests/test_2027_astronomy.py   sanity-checks the generated 2027 output
tests/test_node_anchor_unit.py the node-anchor branch the real span can't reach
build/astronomy_2027.json      4163 records, astronomy only
build/astronomy_2027_summary.txt  counts per class and the backend used
```

## Running it

```bash
pip install -r requirements.txt
python3 tests/test_2026_regression.py
```

### Ephemeris backend

The code prefers real Swiss Ephemeris data files and falls back to the built-in
Moshier ephemeris, reporting which it used. Moshier is accurate to well under an
arcsecond for the Sun, Moon and planets across 1900–2100, so every date and
minute produced so far is sound. For the production run, download the SE files
and point at them:

```bash
export SE_EPHE_PATH=/path/to/ephe
```

Then diff the output against the Moshier run. Given what the source document got
wrong, a final cross-check costs little and is worth doing.

## Time handling

IST (UTC+05:30, no DST) is primary. Eastern is resolved through the IANA zone
`America/New_York`, so the EDT/EST label and the −9:30 or −10:30 gap from IST are
always correct without hardcoding the 2027 switch dates of 14-Mar and 07-Nov.

Where the Eastern calendar date differs, both dates are shown and the record
carries `day_shift = -1`. Window starts and ends are converted independently, so
a window spanning a DST change correctly shows two different Eastern offsets.

Mumbai and New York are evaluated **separately** for sunrise- and weekday-
dependent rules, and emit their own rows. This is not cosmetic: across 13 rule
families in 2026 the two locations produce 103 and 119 qualifying dates with only
90 in common — and for the Kshay and Vriddhi families, which turn on where a
sunrise falls rather than on which day it lands, the two venues share no tithi
at all.

## Epistemics

Astronomy and interpretation are kept in separate layers of the record and never
merged into one field. Astronomical data carries a certainty grade (A computed
exact, B definition-sensitive, C dependent on an undocumented source rule);
interpretation carries a claim tag (Classical, Framework, Observed, Historical,
Verify) and a confidence that starts at `untested` and is only raised by a
pre-registered backtest.

The 2026 probability labels are preserved as `source_probability` — they are
what the source asserted, not a calibrated result, and are not treated as one.
The field is an annotation, not a computable column: 44 labels exist, 19 survive
a three-part transfer test, and they reach roughly 26 of thousands of 2027 rows,
so nothing filters, weights or aggregates on it. Where the source gave one rule
two different labels — which it does in every case where it repeats a rule text
verbatim — the set is emitted rather than a chosen value, flagged
`source_probability_disputed`. `source_probability` never feeds `confidence`.
See `source_probability` in `config/conventions.yaml` and
`build/STEP4_DECISIONS.md`.

Financial astrology is a speculative interpretive framework. Nothing this
project generates is investment advice.

## Known gaps

Carried in `open_questions` in the config: **speed-class thresholds** — resolved
for the inner planets, still open for the slow ones, see below — the 2–7 day lag
on the source's Mercury latitude rows, aspect orb policy, confirmation of
Purnimanta month reckoning, sector mapping, and sign-off on the label scheme.

**The speed-class thresholds calibrate for Mercury and not the others.** An
earlier report that no threshold exists was a **method artefact** and is retracted
in `build/STEP4_DECISIONS.md` §12.8: it read the speed *at* the printed boundary
dates instead of computing crossing instants, and near a speed maximum the whole
above-threshold window is only a few days wide, so the samples "overlapped"
whether or not a threshold existed. Done the kalāṃśā way — propose a threshold,
compute the crossings, score them against the printed dates — **Mercury's level
is 1.7449 deg/day**, cross-checked by six independent boundaries.

**Mars's 0.6583 and Venus's 1.2240 are single-point fits, not calibrations**, and
are recorded as such with `degrees_of_freedom: 0`. Each planet crosses its level
exactly **once** in 2026, so the fit solved one equation in one unknown and no
other printed row can falsify it — the "interval" is just the speed's change
across the ±1 day scoring window. A number that cannot fail is not evidence, so
their Vedha ports are withdrawn and the missing input is named as *a threshold
constrained by more than one crossing*. A later year supplying a second crossing
would make them testable. The series still emits their crossings, graded **C**,
with the reason on the record.

Jupiter and Saturn have **no** threshold, and the reason is a doctrine rather
than a failure: the source carries **B30 "Demoted and Shadow Speed of Saturn"
p.26**, which defines its interval by **longitude** (Saturn at 20°31′ of Pisces,
crossed retrograde on 27-Jul-2026 and direct again on 15-Mar-2027 — both
reproduced to the arcminute by the engine) and supplies no speed level. So those
two stay blocked with a **slow-planet speed doctrine** named as the missing
input.

**Vedha direction: 109/111 overall, and 52/52 within its honest domain.** The
rule — Fast/Atichari→Left, Normal→Front, Retrograde→Right — holds without
exception on **Mercury 45/45 and Jupiter 7/7**. Mars (21/21) and Venus (30/30)
also score perfectly but are **excluded from that figure**, because their classes
came from thresholds that fit by construction and so are not independent
confirmations. Only Saturn (B136) fails, at 6/8, and Saturn is unresolved. The
headline stays **correlation**; **the test that decides** is named in config — if
the slow-planet doctrine is ever settled and Saturn's class becomes computable,
its two rows become testable and the label moves to derivation.

**The speed-class series exists; the Vedha port is MERCURY ONLY.** The astronomy
layer emits `speed_crossing` records at each calibrated level, bisected to the
second, carrying the level *and* its feasible interval. Retrograde boundaries
stay `station` records: the two kinds come from **separate scans at their own
levels**, and a threshold crossing must clear a 0.2 deg/day dead band that no
retrograde loop reaches — so confusing a `Retrograde → Normal` transition with a
Fast/Normal boundary is structurally impossible rather than merely avoided.
Validated before any rule read it: Venus **+0.12 h**, Mars **+0.09 h**, Mercury 5
of 6 within 24 h.

**Mercury is ported because its threshold is overdetermined, and that — not its
row count — is what distinguishes it.** Mercury crosses its level **six** times in
2026, so six independent printed boundaries constrain one number, and it held.
Mars and Venus each cross **once**, so each calibration solved one equation in one
unknown: the feasible interval is just the speed's change across the ±1 day
scoring window, and no other row in the year can falsify it. **Zero degrees of
freedom.** Those thresholds are recorded as **single-point fits**, not
calibrations, with the ports withdrawn and the missing input named as *a threshold
constrained by more than one crossing*. They are kept so a later year supplying a
second crossing can test them rather than re-derive them. Their crossings are
still emitted, but graded **C** rather than B, with the reason on the record.

The port covers B122 and B133. Targets are a **transcription** (all 96 printed
rows resolve through the wheels) and an entry is refused when a 2027 residency's
computed class differs, with the reason on the row — Mercury 66/68 rows carry a
target.

**Atichari is a frame, not a synonym.** It is the **nakshatra-residency frame's**
label for the period the speed frame calls Fast: every Atichari row in
B132/B133/B134 opens and closes on a nakshatra ingress (Venus's eleven run to
12-Apr-26 14:22, when she leaves Revati) and none is bounded by a speed value. It
is recorded under `frame_findings` as **the same shape as the rashi/navamsa
dignity split**. Mars's two tables, once wrongly reported as contradicting each
other there, in fact **agree on 20 of 21 rows** — the single disagreement is the
boundary day itself.

**Shar is settled, and it is the ecliptic latitude and not the declination.**
B118 and B119 print North/South periods; the latitude sign reproduces B119's 27
printed 2026 ends **26 of 27** within 1.5 days, the declination sign reproduces
**0 of 27**, and B118's Mars prints one change where the latitude crosses once
(0.76 d) while the declination crosses 104 days away. Grade B, because latitude
has no ingress series and a boundary is known only to the gap between records —
negligible for the Moon, months for Pluto.

**Atichari is not a speed class name at all** — it is the nakshatra-residency
frame's label for the same period the speed frame calls **Fast**. Every Atichari
row in B132/B133/B134 opens and closes on a nakshatra ingress (Venus's eleven run
to 12-Apr-26 14:22, exactly when she leaves Revati), so the two tables are one
period described in two frames. Recorded under `frame_findings` beside the
rashi/navamsa dignity split, which is the same shape.

**B81 is labelled for the wrong planet, and the tables cannot show it.** "Saturn
and Mercury Both Retrograde" prints a 2026 window during which Saturn and Mercury
are never both retrograde — the printed row is **Venus's** retrograde window to
within four minutes, and the true Saturn∩Mercury window is the row B83 prints.
Because in 2026 both Venus's and Saturn's retrograde stretches happen to contain
Mercury's, the error is invisible without an independent computation. Ported as
the exact condition with the row flagged; nothing widened. Three further source
defects are recorded in §12.7 (B82's carry-in-only window, B114's unmatched
printed end, B115's narrower printed table).

Deliberately excluded: the rainfall formula (dropped), Sankranti muhurta
(deferred until the 15/30/45 division rule is available). The "Big Volatile" list
is flagged C — all 51 source dates carry a real configuration, but the list is
over-determined and the source's weighting is not recoverable, so reconstructions
are emitted as candidates and never as fact. It is ported as a **recorded
absence** with its C flag and `source_selection_rule` named as the missing input,
not reconstructed.
