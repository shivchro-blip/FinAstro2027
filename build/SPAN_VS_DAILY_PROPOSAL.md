# Span vs daily — what a row without an instant should emit

> **LANDED 21-Sep-2026. Model A is implemented and §7 below is the record of
> what it produced.** Read §§1–6 as written — they are the argument, and the
> argument was made against the 15-Sep-2026 build of **7,082 rows**. The build
> has since grown to **8,916** through the configuration wiring, the base track,
> three sub-table ports, Bhadra and the Moon's navamsa series, so every TOTAL
> below is a figure of a file that no longer exists. **The saving is not**:
> −795, invariant, reproduced exactly on a build this report could not have
> seen. §7 states which of this report's figures survived and which did not.

**Report, as written 15-Sep-2026, when the collapse was NOT implemented.** What
had landed in `finastro/` by then was the two things §5 said had to be settled
before anyone implements it — the half-open end convention (§5.1) and the
civil-year clip field (§5.2) — plus the re-derivation of §1's cause figures. The
row count was unchanged at **7,082**: `clipped_start` / `clipped_end` are two new
fields on rows that already existed, and every suite passed (215 · 120 · 135 ·
12 · 17).
Written 15-Sep-2026, against `build/calendar_2027.json` as rendered at that date:
**7,082 rows — 6,677 verdict + 405 event.** Owed since `build/NEXT_SESSION.md`
TASK 4, deferred once, and unblocked by `no_instant_reason`: until that field
existed the 894 rows in question were one undifferentiated population and the
question could only be answered for all of them at once.

Every figure below is measured off the rendered artifact, not off the code that
produced it, and each is checkable by grouping the JSON.

---

## 1. The population, split by cause

A row without an instant is one of five things, and they are not interchangeable.
`no_instant_reason` names four; the fifth is a split inside `date_only` that the
field does not make, because `sky.civil_day_span` and a date-granular ephemeris
record both set `precision="date_only"` and the renderer cannot tell them apart.
**That split is made here by rule id and it is the one the rest of this report
turns on.**

| cause | rows | distinct spans | rules | verdict / event | config-sourced rows |
| --- | ---: | ---: | ---: | --- | ---: |
| `date_only` — ephemeris date-granular | 471 | 58 | 21 | 440 / 31 | 9 |
| `date_only` — `civil_day_span` (b101) | 255 | 17 | 1 | 255 / 0 | 0 |
| `period_cut` — carry-in cut | 151 | 7 | 4 | 151 / 0 | 0 |
| `anchored` — synthetic IST anchor | 12 | 12 | 11 | 12 / 0 | 0 |
| `named_contacts` — eclipse | 5 | 5 | 3 | 0 / 5 | 0 |
| **total** | **894** | **99** | | **858 / 36** | **9** |

"Distinct spans" is the count of `(row_kind, event, instrument, venue,
t_start_utc, t_end_utc)` groups. It is the row count a full collapse produces,
and it is exact rather than estimated because **every daily row already carries
its parent span's endpoints unchanged**. `Firing` is built as
`Firing(r.id, loc, day, span.start, span.end, ...)` — the span is copied whole
onto every day it covers, and only `civil_date` differs. Collapsing is therefore
a **pure rendering operation over rows that already exist**: group and drop. No
new computation, no new ephemeris call, nothing to re-derive.

Every one of the 99 groups is **contiguous** in civil dates — no gaps, no weekday
filter punching holes in a run. Checked, because had any group been
non-contiguous, a collapsed row asserting a start and an end would have claimed
days the daily rows did not.

### The two recorded sets, each attributed to the population it was measured over

*Rewritten 15-Sep-2026, third time. The first version said the recorded
`249 / 147 / 45 / 12 firings, 662 rows` "reproduce against no slicing of this
build" and replaced them with `331 / 282 / 105 / 11`. The second withdrew `282`.
Both versions argued about which set was right without stating what either had
counted, which is the same mistake one level up. Every figure below now carries
its **population**, its **unit** and its **filter**, and `tools/cause_census.py`
is the generator they previously lacked — recompute it, do not re-read this.*

**The decisive test first, because it removes the "the build moved" explanation
entirely.** The census at `846c780` — the commit whose own message records
`249 / 147 / 45 / 12` and `662` — can be run against that commit's **committed**
artifact rather than a reconstruction:

```
git show 846c780:build/calendar_2027.json
```

It is **identical to today's, in all three populations and all six units**:
`date_only` ephemeris 431 rows / 331 firings, `b101` 255 / 105, carry-in 151 /
142, anchored 12 / 11. Nothing in the structural population has moved since the
field was born. So no difference between the two recorded sets is a build effect
— and the earlier claim that the old set was "measured against a transient
pre-`DateStamp` render that was never committed" is **withdrawn too**. The render
it was measured against is in git, and the figures still do not come from it.

#### The three populations, all derivable from the one artifact

| | rows | what it is |
| --- | ---: | --- |
| **P1** | 5,209 | catalogue-B verdict rows — the build before the configuration wiring and before the base track (`e00024a`). Reconstructed by **filter**, not by rebuild: configuration rows are exactly the `cfg_` rules, base-track rows are exactly `row_kind == "event"` |
| **P2** | 6,677 | all verdict rows — post-wiring, pre-base-track |
| **P3** | 7,082 | every row as rendered — the artifact |

And a fourth that is **not a population of the artifact at all**, which is where
the old set comes from:

> **D — the display population.** Rows whose rendered `time_ist` string began
> `00:00`, measured at `dfb485b`, the last render before `DateStamp`. It is a
> property of the **output string**, not of any field.

#### The old set: measured over D, and D is biased to one location

| figure | population | unit | filter | reproduces |
| ---: | --- | --- | --- | --- |
| **662** | **D** at `dfb485b` (6,677 verdict rows) | rows | `time_ist` starts `00:00`, less `b102` | **yes, exactly** |
| **45** | **D** | firings — (rule, location, day) | `b101` only | **yes** |
| **12** | **D**, and every other population | **rows** | `anchored` only | **yes** |
| **249** | — | — | — | **no** |
| **147** | — | — | — | **no** |

`662` is real. D holds **663 rows across 28 events** at `dfb485b`; drop
`b102_anuradha_on_sunday`, whose 00:00:22 IST nakshatra ingress is a genuine
instant that renders as `00:00`, and it is **662 across 27** — which is what the
commit message says, word for word. It is a correct count of D.

**Why D is 196 rows smaller than the structural population, and why that matters
more than the number.** A row without an instant printed midnight **only when the
stand-in instant it was handed happened to be a Mumbai midnight.** Where it was
not, the row printed a plausible wrong time and D never saw it:

| | in D | structural (P2) | invisible to D | what the invisible rows printed |
| --- | ---: | ---: | ---: | --- |
| `date_only` ephemeris | 440 | 440 | 0 | — |
| `anchored` | 12 | 12 | 0 | — the anchor *is* IST midnight by construction |
| `b101` `civil_day_span` | 135 | 255 | **120** | `10:30 IST` / `09:30 IST` — `US_cash`'s New York midnights, two values because that window spans the US DST change |
| carry-in `period_cut` | 75 | 151 | **76** | `09:34 IST` (all 18 of `b079`), `00:13 IST`, `05:18 IST` |
| **total** | **662** | **858** | **196** | |

**D could not see its own worst cases.** The rows it missed are precisely the
ones whose fabricated time looked *real*: `09:34 IST` on a boundary the sky never
supplied is a worse artefact than `00:00 IST`, and a population defined as
"prints midnight" is structurally blind to it. All 18 of `b079`'s rows were
invisible for that reason.

So `45` is not "the Mumbai half of `105`" by an accident of counting. D contains
`b101`'s Mumbai rows **and no others**, because the New York half never printed
midnight. `45` is a complete and correct firing count **of D**.

`249` and `147` reproduce against nothing — not P1, P2, P3 or D; not at
`dfb485b`, `846c780`, `90b54e3` or today; not under rows, firings,
`(rule, venue, day)`, `(venue, date)`, spans or rules; and not under a
Mumbai-only or New York-only filter of any of those. The nearest real figures are
`date_only` ephemeris **440 rows / 340 firings** in D, and carry-in **75 rows /
75 firings** in D. Subset-sums over per-rule counts do hit 249 and 147, but only
as arithmetic coincidence across rule groupings no argument selects. **They stay
withdrawn.**

#### The new set: correct figures, two populations, quoted as one line

| figure | population | unit | filter | reproduces |
| ---: | --- | --- | --- | --- |
| **331** | **P1** | firings | `date_only` ephemeris | **yes** |
| **105** | P1, P2, P3 — invariant | firings | `b101` | **yes** |
| **11** | P1, P2, P3 — invariant | firings | `anchored` | **yes** |
| **858** | **P2** | **rows** | all no-instant | **yes** |
| **282** | **P3** | **(venue, date)** | **`date_only` ephemeris** | yes — **of the first cause, filed under the second** |

Every member is a correct count. The set is still not correct, because **`331` is
a P1 figure and `858` is a P2 figure** and they were written on one line as
though they described one thing. `858` is not the population `331` was drawn
from: the no-instant rows of P1 total **849**.

`282` is confirmed exactly as the second version diagnosed it — distinct
`(venue, date)` pairs among P3's 471 `date_only` ephemeris rows. It is the
**first** cause, on a **third** unit, in the **third** population, written into
the **second** cause's slot. Three axes wrong and the arithmetic right.

#### Which set is correct: **neither, as recorded.** This one is

Not an average, and not the newer because it is newer — the old set has three
members that reproduce and the new set has one filed under the wrong cause.
Stated with the three things a figure needs:

> **Population P1** — catalogue-B verdict rows, 5,209.
> **Unit: firings** — distinct `(rule, firing location, civil day)`, which is
> what `rules.base.fire` emits.
> **Filter: `no_instant_reason` is not null**, with `date_only` split by rule id.

| cause | firings | rows | spans | rules |
| --- | ---: | ---: | ---: | ---: |
| `date_only` — ephemeris | **331** | 431 | 18 | 8 |
| carry-in cut | **142** | 151 | 7 | 4 |
| `civil_day_span` (`b101`) | **105** | 255 | 17 | 1 |
| anchored | **11** | 12 | 12 | 11 |

**`142`, `105` and `11` are identical in P1, P2 and P3** — those causes are
catalogue-B only, so widening the population adds nothing to them. **Only `331`
is population-sensitive:** 331 in P1, 340 in P2, **371 in P3**, because the
configuration wiring and the base track both contribute `date_only` ephemeris
rows. A reader who wants the artifact's figure wants 371, and the two are not
interchangeable.

#### How each disputed figure moved — the classification

| pair | moved because | verdict |
| --- | --- | --- |
| 662 → 858 | the **population** changed, D → structural, and the 196-row difference decomposes exactly | **fine, and now said** |
| 45 → 105 | the **population** changed; D held Mumbai only | **fine, and now said** |
| 12 → 11 | the population is **fixed** — 12 rows and 11 firings in every population and every build. The **unit** changed mid-row | **defect** |
| 249 → 331 | `249` reproduces nowhere | **defect** |
| 147 → 282 | `147` reproduces nowhere, and `282` is a different cause on a different unit in a different population. Carry-in is **142** | **defect, twice** |

#### And a fifth instance, found while doing this

`105` is a **location** count. The natural misreading is the **venue** count, and
it exists and is **150**: `b101` fires on 45 Mumbai and 60 New York civil days,
but Mumbai carries three venues — `NSE` (90 rows), `NSE_FX` (45) and, at New
York, `US_cash` (120) — so `(rule, venue, day)` gives 150 where `rules.base.fire`
emits 105. The earlier note that `b101` runs "over two venues" was wrong about
the word: two **locations**, three venues. Nothing downstream used 150, so
nothing is corrected — but it is the same shape one more time, and
`cause_census.py` now prints both columns with the unit key spelled out beneath
them, so the two cannot be confused by a reader who has only the output.

**The rule this leaves: a figure without a generator is not a measurement, and a
figure without a population is not a claim.** Both recorded sets were written by
hand into prose, and both passed every check this build had, because no check
read them.

---

## 2. What each cause should emit

The structural requirement stands and constrains all five answers:

> **A row without an instant must be unable to emit a clock time.**
> `timezones.DateStamp` enforces it by having no `ist_time`, `et_time`,
> `et_abbr` or `et_offset` attribute at all; code in that branch that reaches
> for one raises `AttributeError` at build time. A collapsed row has **two**
> boundaries instead of one, so it needs **two** stamps, and the requirement is
> that neither may be a `DualStamp`.

### 2.1 `date_only`, ephemeris — 471 rows → 58. **Collapse.**

Combust and rise windows (`b009`, `b015`, `b015a/b/c`, `b022`, `b022w`, `b027`,
nine `cfg_*` rules) and `Total Day`. The ephemeris emits these as dates because
they are horizon measurements; there is no instant at either end and there will
not be one without a new scan.

**Emit:** one row per `(rule, instrument, venue, window)` carrying `date_start`
and `date_end` as two `DateStamp`s, `no_instant_reason: date_only`, and
`duration_days`.

**The source is the warrant, not our convenience.** The 2026 document prints this
exact class as one row with two boundaries and its own **Duration** column —
Mercury combust 02-Jan → rise 04-Feb, Duration 33. The daily render does not
disagree with the source about the sky; it disagrees about the shape of a row,
and the source's shape is the one it also prints a duration for.

**`Total Day` is a no-op.** Its 12 event rows are single civil days; start and end
are the same date and the collapse saves nothing. Stated because a rule that
"collapses spans" and silently turns a one-day event into a zero-length window
would be a regression nobody would see.

### 2.2 `civil_day_span` — 255 rows → 17. **Collapse. The clearest case of the five.**

One rule, `b101_three_saturdays_in_shukla_paksha`: seven windows, two venues,
15 civil days each, 17 `(instrument, venue, window)` groups.

**These are the rows with a real start and a real end that the current render
collapses to a fake midnight — fifteen times per window.** They are not
date-granular for want of an ephemeris scan. The window *is* a run of civil days
by construction — `sky.civil_day_span(days[0], days[-1], loc)`, first counted
Saturday to last counted Saturday at a named venue. Its endpoints are that
venue's midnights, which is exactly why `precision="date_only"` is set on it. And
then each of the 15 days re-prints those same two midnights as though that day
were the window.

```
today                        proposed
06-Feb-2027  date_only        06-Feb-2027 -> 20-Feb-2027   (15 days, NSE)
07-Feb-2027  date_only        counted Saturdays: 06, 13, 20 Feb
08-Feb-2027  date_only
   ... 12 more
20-Feb-2027  date_only
```

**Emit:** one row per `(instrument, venue, window)` with both civil dates, the
`count` and the `dates` list — **both of which are already on the span's `value`**
and are thrown away by the render today. The two flags the rows already carry,
`weekday_is_counted_not_filtered` and `span_runs_first_counted_weekday_to_last`,
are the window's definition and stop a reader taking the 15 days for 15 Saturdays.

**The source prints it this way.** `b101`'s single printed 2026 row is
**12-Sep-26 to 26-Sep-26** — one row, two boundaries — and the argument that
settled where the window starts (the first counted Saturday, not the Pratipada)
is already recorded in `panchang_rules._n_weekdays_in_shukla_paksha`. The daily
render is the only place in the chain that does not treat this as a window.

**One window carries information that fifteen fake midnights structurally cannot.**
The `US_cash` window opening 30-Oct-2027 has `t_start 04:00Z` and `t_end 05:00Z`:
it spans the US DST change, so its two ends sit at different Eastern offsets.
`timezones.window_line` already converts each end independently for exactly this
reason. A one-row window can show it. Fifteen rows each printing one midnight
cannot show it at all.

### 2.3 `period_cut` — 151 rows → 7. **Collapse, but the start is not a date the row may assert.**

Four rules (`b079`, `b084`, `b086`, `b099`), seven spans, **`open_start` on all
seven and `open_end` on three**. The condition was already running when the
generated period began; `sky.span_start` is where we started looking, not where
the sky changed.

**Emit:** one row, and **`date_start: null`** — not a `DateStamp`. A `DateStamp`
for a boundary that is not one would be the same invention `DateStamp` was built
to stop, one field along: the point of the type is that the renderer cannot print
what it does not have, and handing it the period's edge gives it something. What
the row may print is the **first civil day in view** — `first_day_in_view`,
explicitly a view property — beside `open_start: true`.

```
open start, closed end   ->  (running at 01-Jan-2027) -> 26-Feb-2027
open at both ends        ->  (running at 01-Jan-2027) -> (still running at 31-Dec-2027)
```

**`duration_days` must be absent on an open span.** A duration asserts two real
boundaries; three of the seven have neither. Emitting "364 days" for a state
whose start and end are both outside the file is the §12.16 shape in a new field,
and it is the one place in this proposal where a plausible number is available
for free.

### 2.4 `anchored` — 12 rows → 12. **Emit nothing different. Zero rows saved, and that is the right answer.**

Eleven reference-view rules, 12 rows, all on 01-Jan-2027, with
`t_start == t_end == 2027-01-01T00:00:00Z`, `interpretation_basis:
condition_only`, and no verdict.

They are already one row each and there is nothing to collapse. **The point worth
making is what must NOT happen to them.** The obvious move under a span model is
to give them the year — `01-Jan-2027 → 31-Dec-2027`, "this body did not cross its
frame all year". That would be **a measurement where there is none.** The anchored
date is a date *this build chose* because the body never crossed, which is why the
reason is a distinct value and why `the_remedies_differ` says an anchored endpoint
"cannot be remedied at all". A year-long window reads as a state that was observed
to hold. Nothing observed it.

Leave them as anchored point rows. **The 0 in the "saved" column for this cause is
a decision, not an oversight,** and it belongs in whatever config block a span
model gets, or someone collapses it later as tidying.

### 2.5 `named_contacts` — 5 rows → 5. Unchanged.

Five eclipse rows, each already one row naming first contact and maximum. Not a
span question: an eclipse has *several* instants, not none, and the contacts block
is how it says so. Listed only so the population adds up.

---

## 3. What the row count becomes

| model | rows | Δ | verdict | event |
| --- | ---: | ---: | ---: | ---: |
| **today** — one row per civil day | **7,082** | — | 6,677 | 405 |
| **A** — collapse the four no-instant causes | **6,287** | **−795 (−11.2%)** | 5,882 | 405 |
| **B** — A, plus collapse every *timed* span | **2,790** | **−4,292 (−60.6%)** | 2,421 | 369 |

### −795 does not rest on the disputed population, and that is measurable rather than asserted

*Re-derived 15-Sep-2026 by `tools/cause_census.py`, after §1's cause figures were
attributed. The objection was fair as stated — if §1's population was in dispute,
a saving computed over it was not actionable — and the answer is stronger than
"§3 never used those figures".*

**Model A's saving is identical in all three populations:**

| | rows | → | Δ |
| --- | ---: | ---: | ---: |
| **P1** catalogue-B verdict only | 5,209 | 4,414 | **−795** |
| **P2** all verdict rows | 6,677 | 5,882 | **−795** |
| **P3** every row — the artifact | 7,082 | **6,287** | **−795** |

Cause by cause it is the same three numbers in each: `date_only` ephemeris
**−413**, `b101` **−238**, carry-in **−144**. The totals differ by population;
the saving does not.

**Why, and it is not a coincidence.** Every row the wider populations add to a
collapsed cause is **its own span** and therefore collapses to itself. P3's
`date_only` ephemeris cause holds 471 rows over 58 spans where P1's holds 431
over 18 — 40 more rows and 40 more spans, saving nothing. Those 40 are the 9
configuration rows and the 31 base-track event rows, each a single-day
date-granular record. The saving comes only from rows that share a span with
another row, and every one of those is catalogue B.

So `−795` is safe against the one question §1 was disputing — it is invariant
under exactly the axis that moved. **The `6,287` is not**: it is `7,082 − 795`
and therefore a P3 figure, which is correct here because P3 is the artifact and
the headline is a property of the artifact. A reader wanting the same collapse
against catalogue B alone wants **4,414**, not 6,287.

**Also re-derived, and needed before any collapse row is written:** all **82**
groups the three collapsed causes form are **contiguous** in civil dates — 58 +
17 + 7, and the 99 in §1 is 82 plus the 17 point rows the model does not touch.
Had any group had a hole, a collapsed row asserting a start and an end would have
claimed days no daily row was ever built for.

**Model B is stated because the four causes are not the whole of the span problem,
and a proposal that did not say so would be reporting the smaller half as the
whole.** The 894 no-instant rows are 12.6% of the file. The other span population
— **5,024 rows carrying a clock time and a `t_start_utc`, over 1,527 distinct
spans** — has exactly the same daily-repetition shape and differs only in having a
real instant at its start. `b018_sun_ahead_venus_behind_mercury_middle` alone is
702 rows over a handful of windows; `b055_panchak` is 374.

**Recommendation: do A, and do not do B in the same change.** Two reasons, the
first substantive:

1. **In the no-instant population a daily row carries nothing its window does
   not.** All 15 rows of a `b101` window print the same two endpoints, the same
   `date_only`, and no clock time — there is no field in which day 7 differs from
   day 8. That is pure duplication. A *timed* span row's start is a real instant,
   and collapsing it discards a per-day statement a reader may be using; whether
   that statement is worth 3,497 rows is a genuine question and a different one.
2. **B moves the headline figure by 61% and changes what the calendar reports
   about absence** (§4). A −11% change and a −61% change do not deserve the same
   review.

**Do not "emit both and filter on `row_kind`"** — the third candidate in
`NEXT_SESSION.md` TASK 4. `row_kind` already means *verdict vs sky*, and giving it
a second axis (*window vs day*) makes `by_row_kind` a count over a cross product
no denominator in `meta` is keyed to. Emitting both is also 7,082 + 1,626 = 8,708
rows in which every existing figure silently changes population — the
stale-denominator failure a **fourth** time. If both shapes are wanted they need a
**second, separate discriminator** (`row_span: window | day`), and per the rule
`row_kinds` already states, **the discriminator lands first, on all 7,082 existing
rows, before a single collapsed row exists.**

---

## 4. What moves with the row count

**The headline figure is quoted in five places and they move together or not at
all.** This is TASK 2's lesson with a number attached: `141/141` and `0 of 58`
each reached four pages as a figure that was right and a page that was not.

| where | what it carries now |
| --- | --- |
| `build/calendar_2027.json` | `meta.records`, `meta.records_by_row_kind`, and every count under them |
| `build/calendar_2027.html` | the header sub-line, `7,082 rows — 6,677 verdict …` |
| `README.md` | `5,209 rows, the master` — **already stale**, see `NEXT_SESSION.md` TASK 2 |
| `build/RULE_LAYER_STATUS.md` | per-section 2027 row counts, generated by `tools/gen_status.py` |
| `build/MONTHLY_2026_FIXTURE.md` | 168 of 354 windows / 3,168 Mumbai firings — fixture-level, below |

### The empty-day figures, which were published today

| model | days with no row of any kind | days with no event row |
| --- | ---: | ---: |
| today | **0** | **105** |
| A | **0** | **105** |
| B | **19** | **105** |

**Model A changes neither, and that is a reason to prefer it.** `tier_4`'s
verdict-null `USDINR` rows still blanket all 365 days, the apparatus panel's new
statement stays true word for word, and the 105 is a property of the 405 event
rows, which A does not touch.

**Model B falsifies the statement published today.** Collapsing the timed spans
empties 19 days, so `days_with_no_row_of_any_kind` goes 0 → 19 and the panel's
sentence — *"the unfiltered calendar cannot be empty on any day"* — becomes false.
It would then be true for a different reason on 346 days and false on 19, which is
worse than either. Anyone attempting B rewrites that panel section in the same
commit.

### The 2026 fixture

`tools/monthly_match.py` matches **windows**, and the source prints windows. The
fixture's 413 extra Mumbai days include **251 from nine combust windows that are
nine runs, not 251 events** — the finding that opened this question. Collapsing
under A makes the layer's shape and the fixture's unit the same shape for that
class. **Expect the extras to fall and the window match not to move**, since a
window either matched or did not before the collapse. That is a prediction to
measure: do not report A as done until `monthly_match.py` has been re-run and both
numbers printed side by side.

---

## 5. Three things that must be decided before anyone implements A

Each is a place where a collapsed row would render plausibly and wrongly.

### 5.1 The end date is the last day it holds, not the end instant's date — **RULED AND PINNED**

*Settled 15-Sep-2026, before any collapse, and landed in code.
`conventions.yaml` → `row_kinds.time_fields.span_endpoints`.*

Spans are half-open. `b101`'s February Mumbai window has `t_end_utc =
2027-02-20T18:30:00Z`, which **is 21-Feb-2027 00:00 IST**. The last civil day the
condition holds is **20-Feb**. A collapsed row that stamps `t_end_utc` prints
21-Feb and is off by one — in the direction that makes each window one day
longer than the daily rows said it was. **Measured: 251 of the 1,626 span groups
in this build would move.**

**The ruling.** Both representations are emitted, under names that cannot be
confused:

| | what it is | where it comes from |
| --- | --- | --- |
| `t_end_utc` | the **instant the condition ceases**, EXCLUSIVE | the span |
| `last_held` | the **last civil day it holds**, inclusive | `sky.civil_days(...)[-1]` |

**And the confusion is made structural rather than conventional.**
`timezones.SpanDates` carries `first_held` / `last_held` and is built only by
`timezones.span_dates(days)`, which takes the civil **days** the rows were built
from and **raises `TypeError` on a `datetime`**. `datetime` is a `date` subclass,
so without that guard `span_dates([t_end_utc])` would render 21-Feb and nothing
would raise. This is the move `DateStamp` makes for clock times, one field along:
the renderer cannot print what it has no way to obtain.

`max(civil_date)` over the group is the same value — for **this** population.
`SpanDates` also carries `days_in_view = len(days)` and a `contiguous` flag,
because **179 of the timed span groups are not contiguous** (a weekday-filtered
rule's days have holes) and a window over one of those would claim days no row
was built for. All 99 no-instant groups are contiguous, so Model A is unaffected
— the flag exists before Model B does.

**Duration stays absent.** A duration asserts two real boundaries; an open span
has at most one, and a year-clipped span's other end is outside the file.

**Pinned by** `tests/test_rule_layer.py::test_a_spans_displayed_end_is_the_last_day_it_holds`,
which **fails both ways**: it fails if a displayed end is ever taken from
`t_end_utc`, and it fails equally if `span_dates` is "corrected" to agree with
`t_end_utc`, because it also asserts the two disagree on a counted set of 251
windows. Both failure modes were run and confirmed to bite before the check was
believed.

### 5.2 24 spans have a real endpoint outside the year — **FIELD LANDED; and the 22 was wrong too**

`open_start` / `open_end` mark **`sky.span_start`'s cut** — the generated period's
edge. They do **not** mark `fire()`'s second clip, `civil_days(span, loc, year)`,
which drops the days falling outside the calendar year. There is no field for that
clip, because under a daily render it needs none: the out-of-year days simply have
no rows.

Under a collapse it needs one.

**The `22` this section first reported does not survive its own definition.** 22
is the count of `clipped_end` groups **alone**: it leaves out the 10
`clipped_start` groups, and it does not apply the `open_*` filter the sentence
states, so 5 of its 22 are already marked `open_end`. Re-derived over the same
span unit — `(row_kind, event, instrument, venue, t_start_utc, t_end_utc)`,
1,626 groups:

| | |
| --- | ---: |
| `clipped_start` | 10 — of which `open_start` false: **7** |
| `clipped_end` | 22 — of which `open_end` false: **17** |
| **real endpoint outside 2027, `open_*` false** | **24** — 1 no-instant + 23 timed |

(18 under the rule-span unit `(row_kind, event, location, t_start, t_end)`, which
does not repeat a window per instrument.)

**The field is landed, on all 7,082 daily rows, before any collapse** —
`clipped_start` / `clipped_end`, computed once per (span, location) in
`rules.base.fire` by `sky.year_clip`, carried on `Firing` and `Verdict`, and
emitted by `render._time_fields`. The clearest case is
`b009_mercury_combust_cycle`:

```
t_start_utc 2026-12-13T18:30:00Z   open_start False   first row 01-Jan-2027
```

Mercury genuinely went combust on 13-Dec-2026, so `open_start: False` is correct —
the boundary is real and measured. But a collapsed row printing `13-Dec-2026 →
17-Jan-2027` starts before the file does, and one printing `01-Jan-2027 →
17-Jan-2027` asserts a boundary the sky did not supply.

**Decided: emit both.** The condition's true boundary stays on `t_start_utc` /
`t_end_utc`; the in-year extent is `SpanDates.first_held` / `last_held`; and
`clipped_*` says which of the two a reader is looking at. Neither is dropped and
neither is chosen silently.

**And `open_*` and `clipped_*` are genuinely independent, which is the whole
reason the pair was not enough.** `b009`'s carried-in window is `clipped_start`
**and not** `open_start` — Mercury genuinely went combust on 13-Dec-2026. The
three carry-in windows are **both**: the period cut them *and* the year clips
them. A single flag could express neither pair.

Ruled in `conventions.yaml` → `row_kinds.time_fields.year_clip`, whose census is
recomputed off the artifact figure by figure by
`tests/test_rule_layer.py::test_the_civil_year_clip_is_a_field_and_not_the_period_cut`
— which **prints what it read** rather than reporting a boolean.

### 5.3 The HTML date filter becomes an overlap test

`render()` compares `iso_date` against the from/to inputs. A collapsed row carries
one sort date, so a reader filtering *from 10-Feb-2027* would lose a window
running 06-Feb → 20-Feb that is live on every day they asked about. **The filter
has to test span overlap, not the sort key** — and the row-kind control's own
comment already records what happens when a control means something different to
two populations: a reader who does not know reads it as the calendar being empty.

---

## 6. Summary

| | |
| --- | --- |
| **Recommended** | Model A — collapse `date_only` (ephemeris), `civil_day_span` and `period_cut`; leave `anchored` and `named_contacts` as point rows |
| **Rows** | 7,082 → **6,287** (−795, −11.2%). The **−795 is invariant** across all three populations (P1 5,209 → 4,414, P2 6,677 → 5,882, P3 7,082 → 6,287); the **6,287 is a P3 figure** and the catalogue-B answer is 4,414 |
| **Empty-day figures** | unchanged — 0 of any kind, 105 with no event |
| **Cost** | a rendering change. No new ephemeris work and no new computation: every collapsed row's endpoints are already on every daily row it replaces |
| **§5 blockers** | **5.1 and 5.2 are settled and landed** — `timezones.SpanDates` / `span_dates()` and `sky.year_clip` → `clipped_start` / `clipped_end` on all 7,082 rows, both pinned by checks. **5.3 (the HTML date filter) is still open** and belongs to whoever implements the collapse |
| **Re-derived** | §1's cause figures, now **attributed to a population** rather than argued over. Neither recorded set is correct as recorded. The answer is **P1, firings, no-instant filter: 331 / 142 / 105 / 11**. `662`, `45` and `12` are correct counts of the pre-`DateStamp` **display** population D; `249` and `147` reproduce nowhere; `282` is the first cause on a third unit in the third population |
| **Generator** | `tools/cause_census.py` — the thing §1 said every figure needs and did not itself have. Prints population, unit and filter beside every count |
| **Explicitly deferred** | Model B, the 5,024 timed span rows over 1,527 spans. A −61% change to the headline, and it falsifies the empty-day statement published today |
| **Explicitly refused** | emitting both shapes under `row_kind`. If both are wanted, a second discriminator, landed on all 7,082 existing rows **first** |

**Written by hand. Not a `tools/` page** — this is a written record like
`STEP4_DECISIONS.md` and `NEXT_SESSION.md`, and the prose has no generator.

**Its figures now do.** `tools/cause_census.py` recomputes every count in §1 and
§3 off `build/calendar_2027.json`, in all three populations, with the unit and
filter printed beside each. That split is the point: the argument is hand-written
and stays hand-written, the numbers it argues over are regenerated. Two of this
report's own figures — `282` and the `22` of §5.2 — were right about a set nobody
had stated, and neither would have survived a page that printed its population.

---

## 7. What it actually produced — 21-Sep-2026

*Written after implementing Model A. Everything above is the argument as it
stood on 15-Sep-2026 and is left as written; this section is the outcome, and
it says which of the report's own figures survived contact with a build six
days and 1,834 rows later.*

### 7.1 The one figure that had to hold, and did

| | §3 predicted, at 7,082 rows | measured 21-Sep-2026, at 8,916 |
| --- | ---: | ---: |
| `date_only` ephemeris | **−413** | **−413** |
| `civil_day_span` (`b101`) | **−238** | **−238** |
| carry-in `period_cut` | **−144** | **−144** |
| **total** | **−795** | **−795** |

**Invariant in all three populations, again:** P1 5,539 → 4,744, P2 8,511 →
7,716, P3 8,916 → **8,121**, the same three numbers in each. §3's argument for
why — *every row the wider populations add to a collapsed cause is its own span
and collapses to itself* — is the same reason it survived the build GROWING, and
that was not a case §3 made. It is the stronger claim, and it is now measured
rather than reasoned: P3's ephemeris cause held 471 rows over 58 spans in the
15-Sep build and holds 507 over 94 today. Thirty-six more rows, thirty-six more
spans, nothing saved.

**`6,287` is withdrawn as a prediction of today's file and stands as a correct
P3 figure of the 15-Sep build.** It was always `7,082 − 795`, and §3 said so.
The P3 answer today is **8,121**; the catalogue-B answer is **4,744**.

### 7.2 What was emitted

118 window rows, standing for 913 civil days, over 8,121 rendered rows:

| cause | daily rows | window rows | Δ | collapsed? |
| --- | ---: | ---: | ---: | --- |
| `date_only` — ephemeris | 507 | 94 | −413 | yes |
| `date_only` — `civil_day_span` | 255 | 17 | −238 | yes |
| `period_cut` — carry-in | 151 | 7 | −144 | yes |
| `anchored` | 12 | 0 | 0 | **no, by decision** |
| `named_contacts` | 5 | 0 | 0 | **no, by decision** |
| timed spans | 7,986 | 0 | 0 | **no — Model B, refused** |

A window row carries `first_held`, `last_held`, `first_weekday`, `last_weekday`,
`days_in_view` and `contiguous`, all from `timezones.SpanDates`. **No duration
and no `date_start` / `date_end`**, per §5.1 — which is where §2.1's request for
`duration_days` and §2.3's for `date_start: null` both end up, and §7.5 says why.

### 7.3 §5.3, and the discriminator §3 demanded

* **§5.3 is closed.** The HTML date filter is an overlap test: a row is kept when
  `iso_date <= to` and `iso_date_end >= from`. Verified by driving the artifact's
  own `render()` under Node against a stub DOM — filtering to the single day
  **10-Feb-2027** now returns b101's **5** February windows where a comparison
  against the sort key returned **0**. `iso_date_end == iso_date` on a day row,
  so the two shapes take one branch.
* **`row_span` is the second discriminator §3 said this needs**, and it is on all
  8,121 rows rather than only on the 118. §3 refused "emit both shapes under
  `row_kind`" and named the remedy; this is that remedy, with the one difference
  that both shapes are not emitted — each row has exactly one.

### 7.4 No day-keyed figure moved, and that is the check

A firing is one `(rule, firing location, civil day)` and `rules.base.fire` emits
it upstream of any rendering, so the collapse may move **rendered rows and
nothing else**. `render.covered_days` is the one place the two shapes are
reconciled, and every day-keyed consumer reads it:

| | before | after |
| --- | ---: | ---: |
| catalogue-B firings — ephemeris / carry-in / `b101` / anchored | 331 / 142 / 105 / 11 | **331 / 142 / 105 / 11** |
| P1 firings, unfiltered | 2,802 | **2,802** |
| `b101` by firing location | 45 + 60 | **45 + 60** |
| `(rule, venue, day)` for `b101` | 150 | **150** |
| 282's cell — P3 ephemeris `(venue, date)` | 300 | **300** |
| days in year / no event row / no row at all / no verdict text | 365 / 105 / 0 / 2 | **365 / 105 / 0 / 2** |

**The empty-day figures are §4's case for Model A over Model B, and they held.**
`tier_4`'s verdict-null `USDINR` rows are timed and were never collapsible, so
the apparatus panel's published sentence — *the unfiltered calendar cannot be
empty on any day* — is still true word for word.

`tools/cause_census.py` gets there by expanding a window row over its covered
days in the `firings`, `rule-venue-day` and `venue-date` units. **`rows` is
deliberately not expanded** — it means rendered rows and it genuinely moved — and
the old unit is kept beside it under the name **`daily_rows`**, which is where
`431 / 151 / 255 / 12` now lives. Renaming the unit rather than restating the
figures is the whole of that correction: the four are the same measurement.

### 7.5 Three things this report asked for that the implementation did not do

1. **`duration_days` (§2.1).** Not emitted. §5.1 ruled duration out generally and
   is the later ruling; `SpanDates` carries `days_in_view` and no duration by
   design. Where all four of `open_start`, `open_end`, `clipped_start`,
   `clipped_end` are false, `days_in_view` **is** the source's Duration in days,
   and where they are not, no field says so.
2. **`date_start: null` on an open span (§2.3).** Not emitted, because it is no
   longer needed. `first_held` and `last_held` are VIEW properties by
   construction — `civil_days` applies the period cut and the year clip before
   `span_dates` sees a day — so neither asserts a boundary, and §5.2's later
   *emit both* ruling is what says which end is real. §2.3 was asking for a name
   that does not claim a measurement; `first_held` is that name.
3. **§4's fixture prediction was wrong, and not in the direction it worried
   about.** It predicted *the extras fall and the window match does not move*.
   Re-run after the collapse, `tools/monthly_match.py` is **identical**: 285
   windows reproduced, 622 extra days over 239 runs, `visibility/combust` 251
   days over 9 runs. The reason is that it measures the **2026 rule layer**, and
   the collapse is a rendering operation on the **2027 artifact**, downstream of
   every firing it reads. The window answer was already in its `runs` column —
   *9 runs, not 251 events* is the finding that opened this whole question, and
   it was being printed the entire time.

### 7.6 Two figures of this report's own, re-derived

* **§5.1's `251 of the 1,626 span groups`** — re-measured at **316 of 2,938**,
  the build having grown. 251 stays attached to the build it was measured over.
  The number that matters now is a different one: **108 of the 118 window rows
  are in that set**, so `last_held` finally has a reader and a build stamping
  `t_end_utc` would print 108 wrong dates.
* **`179 of the timed span groups are not contiguous`** (`conventions.yaml`,
  not this report) — **withdrawn.** Zero non-contiguous groups under four
  different span units, on the pre-collapse artifact as well as the collapsed
  one, so it is not a collapse effect. No check asserted it and nothing rested on
  it: the `contiguous` flag is justified by what it prevents, and
  `collapse_windows` refuses to fold a group with a hole whether or not one
  exists today.

### 7.7 Where the figures live now

`conventions.yaml → row_kinds.row_span` is the ruling and carries the census.
`tests/test_rule_layer.py::test_the_span_collapse_is_model_A_and_no_day_keyed_figure_moved`
recomputes every figure in §7.2 off the artifact and pins the negative half —
that `anchored`, `named_contacts` and every timed span are **still day rows** —
because a check that only asserted the row count fell would pass on a collapse
that folded the wrong rows. Suites **282 · 149 · 123 · 12 · 17**, from 268.
