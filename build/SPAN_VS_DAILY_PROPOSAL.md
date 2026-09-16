# Span vs daily — what a row without an instant should emit

**Report. THE COLLAPSE IS NOT IMPLEMENTED.** What *has* landed in `finastro/`
since this was first written is the two things §5 said had to be settled before
anyone implements it — the half-open end convention (§5.1) and the civil-year
clip field (§5.2) — plus the re-derivation of §1's cause figures. The row count
is unchanged at **7,082**: `clipped_start` / `clipped_end` are two new fields on
rows that already existed, and every suite passes (215 · 120 · 135 · 12 · 17).
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

### The four cause figures, re-derived — **and one of this report's own was wrong**

*Rewritten 15-Sep-2026 after the measurement was disputed. What this section
said first — that the recorded `249 / 147 / 45 / 12 firings, 662 rows` do not
reproduce, and that the build measures `331 / 282 / 105 / 11` — was half right.
The finding stood; one of the four replacement figures did not.*

**`282` is not a carry-in figure at all.** Brute-forcing every (population ×
grouping key) pair over this build, 282 has exactly one source: distinct
`(venue, date)` pairs among the **471 `date_only` ephemeris rows**. It is a
second measurement of the **first** cause written into the **second** cause's
slot — the same class of defect as the recorded table it was correcting.

Re-derived, as **catalogue-B firings** = distinct `(rule, location, civil day)`,
which is what `rules.base.fire` emits:

| cause | firings | rows | spans | rules |
| --- | ---: | ---: | ---: | ---: |
| `date_only` — ephemeris | **331** | 431 | 18 | 8 |
| carry-in cut | **142** | 151 | 7 | 4 |
| `civil_day_span` (b101) | **105** | 255 | 17 | 1 |
| anchored | **11** | 12 | 12 | 11 |

**Nothing moved because the population moved.** The same rule families counted
against the pre-wiring, pre-base-track **5,209-row** build (`e00024a`) give the
same figures — 431 rows / 331 firings for the ephemeris windows, 255 / 105 for
`b101`, 398 rows for the four carry-in rules. The base track added 31 event rows
and 5 eclipse rows to the no-instant population and the configuration wiring
added 9: **45 rows of 894, none of them catalogue B.** Every difference between
the two recorded sets is a unit or a derivation defect, not a population effect.

The four, diagnosed:

* **`45` is the Mumbai half of `105`.** `b101` is `per_location`: 45 firings at
  Mumbai, 60 at New York, over 7 windows. The recorded figure counted one venue.
* **`12` counted ROWS where its three neighbours counted FIRINGS** — the
  recorded table's own column header says so. 12 rows, 11 firings, 11 rules:
  `b014` emits a SUGAR row and tier_4's USDINR row from one firing. **Both
  numbers are right about different things and neither moved.** That is the one
  that appeared to go down while the total went up.
* **`282`** — above. Replaced by **142**.
* **`249`, `147` and `662`** are diagnosed as nothing. They reproduce against no
  slicing of this build or of the one before it. They and the
  `no_instant_reason` field were **born in the same commit** (`846c780`),
  measured against a transient pre-`DateStamp` render that was never committed,
  and **no generator for them exists**. They are WITHDRAWN, not corrected:
  `render._time_fields`, `timezones.DateStamp` and `conventions.yaml` now carry
  the re-derived figures, and `tests/test_rule_layer.py` recomputes the census
  off the artifact.

**The rule this leaves: a figure without a generator is not a measurement.** Both
withdrawn sets were written by hand into prose, and both passed every check this
build had, because no check read them.

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
| **Rows** | 7,082 → **6,287** (−795, −11.2%) |
| **Empty-day figures** | unchanged — 0 of any kind, 105 with no event |
| **Cost** | a rendering change. No new ephemeris work and no new computation: every collapsed row's endpoints are already on every daily row it replaces |
| **§5 blockers** | **5.1 and 5.2 are settled and landed** — `timezones.SpanDates` / `span_dates()` and `sky.year_clip` → `clipped_start` / `clipped_end` on all 7,082 rows, both pinned by checks. **5.3 (the HTML date filter) is still open** and belongs to whoever implements the collapse |
| **Re-derived** | §1's cause figures, after `282` was found to be the first cause measured on a second key. Catalogue-B firings: **331 / 142 / 105 / 11** |
| **Explicitly deferred** | Model B, the 5,024 timed span rows over 1,527 spans. A −61% change to the headline, and it falsifies the empty-day statement published today |
| **Explicitly refused** | emitting both shapes under `row_kind`. If both are wanted, a second discriminator, landed on all 7,082 existing rows **first** |

**Written by hand. Not a `tools/` page** — this is a written record like
`STEP4_DECISIONS.md` and `NEXT_SESSION.md`, and has no generator.
