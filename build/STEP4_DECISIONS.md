# Step 4 — Decisions on Record

**FinAstro 2027, rule layer.** Written before any verdict rule is written.
This is the document Step 4's rule layer gets built against.

Everything below is **decided**. Nothing below is a verdict: no verdict rule
exists, no verdict is generated, and the record schema still has no field an
interpretation could occupy —
`tests/test_2027_astronomy.py::test_no_interpretation_leaked` asserts exactly
that, and the assertion is unchanged by anything here.

A decision recorded here with its evidence is cheaper than a decision
re-litigated in Step 4 from memory.

**This document is living, and Step 4 is in progress.** §1–§11 were written
before the rule layer existed and are the decisions it is built against; §12 is
appended to as batches land, each section date-stamped, newest last. A decisions
record that is stale is worse than one that grows. `build/STEP3_REPORT.md` is
the frozen one — it records a step that closed.

| | |
| --- | --- |
| Opened | 13-Sep-2026 |
| Last updated | 14-Sep-2026 — §12.8, batch 4 calibration retracted and replaced |
| Companion | `build/STEP3_REPORT.md` — the astronomy layer, closed and frozen |
| Config | `config/conventions.yaml`, sha256 `28b037710e9628f5e23354002ad0c84159ec50f43ae45e185fe7eeff19f1f1d2` |
| Build | `build/astronomy_2027.json`, sha256 `c3a45926eb0a97e9e429e37487f10fa004818828bb3d00d123840ebefd16365d` — **unmoved** |
| Harness | `test_2026_regression.py` 68/68 · `test_2027_astronomy.py` 87/87 · `test_node_anchor_unit.py` 12/12 · `test_rule_layer.py` 74/74 |
| Source | `data/source_2026.html`, 437578 bytes, md5 `5e098446d6dd13d3df8443528db5dd95` |
| Book | *The Celestial Ledger* Ch15, Ch16, Appendix B.5 — **not in the project tree**, read from `C:/Shiva/Horoscopes/FinAstro/FinAstro_Guide/raw/` |

**The build hash has not moved while the config hash has.** That is the expected
result and a standing check: every decision in this document is material the
engine does not read, so recording one cannot silently move a date. The build was
re-run after the config was written and compared — byte-identical.

---

## 1. What is decided here, and what is not

| Decided | Where |
| --- | --- |
| Which instruments may carry a verdict, and on what evidence | §2, §3 |
| The planet → instrument/sector map and its four witnesses | §4 |
| Crude oil's significator — **both**, neither primary | §5 |
| The seven source-vs-book sector disputes owed the same treatment | §6 |
| The civil day every instrument evaluates on | §7 |
| The source's probability labels: what transfers, and what it means | §8 |
| Claims made along the way that did not survive checking | §9 |
| What each rule batch decided, as it landed | §12 |

| Still open, and what it blocks | Status |
| --- | --- |
| `label_scheme_signoff` | **Blocks writing any verdict rule.** Owner decision, not a research question. |
| `speed_class_thresholds` (Atichari / Fast / Normal / Slow / Vakri) | Blocks the entire Vedha family, and excludes two labels in §8. Undocumented in the source. |
| `aspect_orbs` — graha drishti vs degree orbs | Blocks every aspect-based rule. The astronomy layer emits only exact contacts. |
| `sector_mapping` | **Reopened** by §5. Not blocking now — no instrument in scope maps to any of the seven. |
| `mercury_shar_lag`, `month_system_confirmation` | Not blocking. Each bounds specific claims. |

---

## 2. Per-instrument coverage

Eleven instruments. The tier is a **required, non-null field on every emitted
verdict** — not a comment and not inferable from the instrument, so no downstream
consumer can mistake a localized or derived verdict for a source-backed one. A
verdict record with no tier, or with a tier outside the four names, is a build
error and must fail the emit rather than be defaulted.

| Instrument | Venue | Civil day | Tier | Where its verdict comes from |
| --- | --- | --- | --- | --- |
| NIFTY | NSE | Mumbai | 1 source_backed | The source's general weekday/panchang/transit verdicts |
| BANKNIFTY | NSE | Mumbai | 1 source_backed | Same general verdicts. Its Jupiter sector path is tier 3 and does **not** upgrade |
| MCXGOLD | MCX | Mumbai | 1 source_backed | *Gold — Bullish/Bearish Configuration* pp.136-148, 17 named rule groups |
| GC | CME_Globex | **New York** | 1 source_backed | The same gold sections, evaluated on the venue day |
| MCXSILVER | MCX | Mumbai | 1 source_backed | *Silver — Bullish/Bearish* pp.149-167, 29 rule groups — the largest set in the document |
| SI | CME_Globex | **New York** | 1 source_backed | The same silver sections, venue day |
| SUGAR | physical_IN | Mumbai | 1 source_backed | *Sugar and Jaggery — Bullish/Bearish* pp.168-175, 9 rule groups |
| SPX | US_cash | New York | 2 localized | The **same** rule families as Indian equities, on the New York civil day |
| NDX | US_cash | New York | 2 localized | Same |
| CL | CME_Globex | New York | 3 book_derived | **Two significator paths, both emitted** — see §5 |
| USDINR | NSE_FX | Mumbai | 4 no_rule | Nothing. `verdict: null`, emitted anyway so the absence is visible |

**SUGAR's venue is deliberately unresolved.** The source gives sugar and jaggery
the same full configuration treatment it gives gold and silver, so the evidence
exists and the instrument is tier 1; but it names no exchange, and Indian
sugar/gur futures are not currently live. `venue_status:
unresolved_no_live_futures_contract`. The instrument was added rather than
dropped, because dropping it would have discarded 9 named rule groups of real
source evidence over a contract-listing question.

**USDINR is a decision, not a gap.** A currency pair is a ratio of two economies,
not a thing a significator maps to. Checked rather than assumed: none of
`book_ch15`, `book_ch16`, `book_appB` or the source's own sector map contains a
currency row; the nearest item in any of them is Appendix B's Mercury →
"trading/brokerage", which is about brokers. Rows are still emitted with a null
verdict so the absence shows in the output instead of looking like a build gap.

**Tier 2 is a change of day boundary, not a change of rule.** The source's rule
families here are transit and panchang rules: they reference no natal chart and
condition only on planetary position, tithi, nakshatra, yoga, karana and weekday,
all defined independently of any location's chart. The machinery already exists —
`weekday_rule.evaluate_per_location` is true, and the 2026 divergence is measured
at 103 Mumbai dates vs 119 New York, 90 shared. Anything requiring a natal chart
is **out** of tier 2: not the NYSE 1792 chart, not a US foundation chart, not a
re-derivation.

**The narrative layer does not localize at all.** The source's Salient Features
prose (pp.192-231) is natal, not transit: it is computed from a chart cast for
*"January 1, 2026, 0:00:00, 72E50'00, 18N58'00 — Mumbai, India"*, reasons in house
lords off that chart, and repeatedly invokes India's own natal chart (*"Venus is
Lagnesh in the natal chart of India"*). Tier 2's justification is exactly what
fails there, so that layer is flagged `india_chart_anchored` and does not extend
to SPX, NDX, GC, SI, CL or USDINR.

---

## 3. The four tiers, read as two axes

### 3.1 Why the split is needed

The four tier names answer two different questions at once:

- **evidence_source** — *where does the claim come from?* `source` (the 2026
  document) / `book` (*The Celestial Ledger*) / `none`.
- **construction** — *how is the verdict produced?* `printed` (the source states
  the verdict itself) / `derived` (a rulership is applied to a significator's
  condition) / `null`.

For ten of the eleven instruments the two axes move together and the tier name is
unambiguous. For one row they come apart, and that row is what makes the
distinction worth writing down.

### 3.2 The cross-tabulation

| Row | evidence_source | construction | Emitted tier | Instruments |
| --- | --- | --- | --- | --- |
| Gold / silver / sugar configuration sections | source | printed | 1 source_backed | MCXGOLD, GC, MCXSILVER, SI, SUGAR |
| General weekday / panchang / transit verdicts | source | printed | 1 source_backed | NIFTY, BANKNIFTY |
| The same families on the New York civil day | source | printed *(day boundary moved)* | 2 localized | SPX, NDX |
| **CL via Rahu** | **source** *(rulership only)* | **derived** | **1 source_backed** | CL |
| CL via Saturn | book | derived | 3 book_derived | CL |
| BANKNIFTY Jupiter sector overlay | source + book | derived | 3 book_derived *(if used at all)* | BANKNIFTY |
| USDINR | none | null | 4 no_rule | USDINR |

### 3.3 The row that forced it — objection on record, ruling stands

`tier_1.means` reads *"The 2026 source states the verdict itself. Nothing is
derived."* **The CL Rahu path does not meet that.** The source states the
**rulership** (Rahu → Crude oil); the verdict is still derived by applying it to
Rahu's condition, which is tier 3's definition.

It carries tier 1 because `verdict_coverage.precedence` ranks **evidence**, not
verdict **construction**. The consequence is stated rather than hidden: a consumer
filtering on `tier == source_backed` will pick up a CL row whose verdict no
section of the source prints. That is mitigated — not removed — by the flag
`rulership_source_stated_verdict_derived` carried on every CL_rahu row.

**The objection was raised so the tier's meaning stays honest, and the ruling
stands.** Under the two axes the row is simply `(source, derived)`, which is
unambiguous and needs no flag to be legible.

### 3.4 The pair is canonical in config; nothing emits it yet

**Superseded 13-Sep-2026.** The two axes were recorded here as a *reading* of the
existing decisions. They are now the model: `verdict_coverage.axes` defines
`evidence_source` and `construction` as **the** fields a rule is written against,
and `tier` is demoted to `verdict_coverage.tier_derivation` — a derived name over
the pair, retained because eleven instruments and three reports already speak in
tier names.

**This is config only and moves nothing.** No verdict record exists, so nothing
carries either field; `verdict_coverage` is read by no module — not
`build_2027.py`, not `finastro/`, not any suite — so the build hash cannot move
and did not. `test_no_interpretation_leaked` is untouched.

Two things the canonicalisation forced, both recorded rather than smoothed over:

- **The pair alone does not determine the tier.** `(source, printed)` appears
  twice in §3.2 with two different tiers — Indian equities at tier 1, SPX/NDX at
  tier 2. The derivation therefore takes a third input, `localized`, which is
  **not** a third axis: both axes are about the claim, `localized` is about where
  the claim is evaluated. It is already carried as
  `source_authored_for_indian_equities` and `authored_ist_evaluated_venue_day`;
  the config names it rather than resolving the ambiguity by quietly reassigning
  one of the two rows.
- **`evidence_source` has four values, not three.** §3.1 named three; §3.2's
  cross-tabulation then used `source + book` on the BANKNIFTY Jupiter overlay
  row. The cross-tabulation enumerates actual rows and governs, so the value set
  is widened to include `source_and_book`. Flattening it to `source` would have
  hidden a two-witness agreement; flattening it to `book` would have dropped the
  source's own map — the error §4.2 was raised against.

`rulership_source_stated_verdict_derived` is now redundant rather than
load-bearing: under the pair, CL_rahu is simply `(source, derived)`. The flag
stays on the row for consumers reading the tier name.

---

## 4. Rulership — the reconciled map

### 4.1 Four witnesses, all read in full

| Witness | What it is |
| --- | --- |
| `book_ch15` | *The Celestial Ledger* Ch15, Commodities — Gold, Silver & the Metals |
| `book_ch16` | Ch16, Sector & Stock Selection |
| `book_appB` | Appendix B.5, "the sector → planet map" |
| `source` | The map the 2026 source prints for its **own** verdicts (pp.210, 214-218), used throughout its monthly tables via "sectors ruled by X" |

The book is not in the project tree; its file paths are recorded in the config so
the provenance is checkable and the next reader does not search `config/` and
`data/` for it.

### 4.2 Two corrections that changed the table

**`ch15_silence_read_as_agreement` — corrected and applied.** The instruction that
built this table claimed *"Ch15 agrees with Ch16 and Appendix B across the sector
map — three-way agreement."* Ch15 is a **commodities** chapter. It takes part in
three-way agreement on exactly **three** mappings: Sun → gold, Mars → base metals
and defence, Saturn → oil. It says nothing whatever about IT, banking, autos, FMCG
or Rahu, and **silence is not agreement**. Every `witnesses` list now names only
sections that actually make the assignment, so Mercury → IT and Venus → autos are
recorded as **two-way**, not three-way. Consequence: two of the map's most-used
rows are weaker than the instruction assumed, and both are *also* contradicted by
the source (§6).

**`bphs_venus_silver` — unverified, kept as stated grounds.** The claim *"BPHS
gives Venus silver alongside the diamond; the Moon holds silver alongside the
pearl"* was cited from recall. BPHS is not in the project tree and was not read.
The claim may well be right — nothing here refutes it — but none of the four
sections this table was reconciled from witnesses it, so it must not be recorded
as a witnessed classical claim. It does not move the decision, which rests on a
structural argument instead (§4.4).

### 4.3 The map

`witnesses` lists only the sections that make the assignment.

| Planet | Primary | Witnesses | Claim tag |
| --- | --- | --- | --- |
| Sun | gold | ch15, ch16, appB, **source** | Classical |
| Moon | silver | ch15, appB | Classical |
| Mars | base metals, copper, defence | ch15, ch16, appB, source | Framework |
| Mercury | IT, telecom, media | ch16, appB *(two-way)* | Framework |
| Jupiter | banking, finance | ch16, appB, source | Framework |
| Venus | autos, luxury, entertainment, textiles | ch16, appB *(two-way)* | Framework |
| Saturn | oil, crude, PSU, mining, infrastructure, labour | ch15, ch16, appB *(**contradicted by the source**)* | Framework |
| Rahu | speculation, tech, crypto | ch16, appB, source | Framework |
| Ketu | pharma niches | ch16, appB | Framework |

Sun → gold is the only mapping with three-way book agreement **and** source
agreement, and `book_ch15` calls it one of just two pedigreed asset rulerships in
the whole book. The source's Rahu row is the widest of any planet and carries a
scope clause the book has no equivalent for: *"Rahu rules all the commodities of
any Nakshatra (Star) or Sign where it stays."*

### 4.4 Silver — Moon primary, Venus secondary only

**Not convention-following.** `book_ch15` *constructs* the gold-silver spread as
the Sun-Moon spread — *"The Sun-Moon separation of roughly 96.9 degrees is the
celestial analogue a practitioner would map onto the gold/silver ratio"* — so a
Venus-ruled silver collapses the chapter's own construction. That is a structural
argument, not a popularity one.

Recorded so the disagreement does not read as settled: **within these three
sections** the conflict is Classical (Moon) vs Framework (Venus), not Classical vs
Classical. The book files Venus under *"Framework — the extensions are modern
practitioner convention, not classical"*, and Appendix B.5 gives Venus no silver
at all. Venus may enter as a secondary modifier only, flagged
`silver_venus_secondary_modifier`, never as primary.

---

## 5. Crude oil — both significators, neither primary

**DECIDED 12-Sep-2026. `CRUDE = SATURN and RAHU`. Both paths are carried, both are
emitted, `primary` is `null` and must remain null in the output.**

This is not an oversight, not a deferral and not a failure to choose, and the
reasoning is recorded at length in the config so it cannot later be "tidied up" by
picking a winner.

### 5.1 The disagreement

| Witness | Says |
| --- | --- |
| `book_ch15` | Saturn — *"Iron, oil and crude, coal"*; significator table `Saturn \| Oil / iron` |
| `book_ch16` | Saturn (with Sun) — *"Oil, Energy, PSU, Heavy Industry"* |
| `book_appB` | Saturn — *"Oil, PSUs, mining, infrastructure, labour"* |
| `source` | **Rahu** — *"… Logistics, Crude oil, Pharmaceuticals …"*. Saturn's row in the same table carries *"Oil-seeds"* — an agricultural commodity, **not** crude |

### 5.2 Why it is not resolved

Neither witness refutes the other. The classical weight is with Saturn — that
which is extracted from underground, dark and heavy, of which mineral oil is the
paradigm case — and the book says so in three separate sections. But the source
says Rahu, **the source is what this project reproduces**, and Rahu-as-crude is
coherent on its own terms as the modern imported/speculative reading. The source's
map is not decorative: *"sectors ruled by X"* drives verdicts throughout its
monthly event tables, so it is the map the source's own verdicts run on.

Resolving by precedence would be resolving by fiat — the precedence rule ranks
**evidence for verdicts**, and applying it to a *rulership* dispute would silently
convert a question about the world into a question about filing order.

### 5.3 Why carrying both is cheap

It converts an unresolvable rulership dispute into a **testable divergence**,
which is the only way it can be settled in a project built to test astro-financial
signals empirically. **Deciding by fiat now would destroy the experiment to save
34 rows.**

| | |
| --- | --- |
| Saturn-conditioned 2027 events | 26 |
| Rahu-conditioned 2027 events | 8 |
| Union | 34 |
| **Intersection** | **0** |

Choosing Rahu alone would have shrunk CL's addressable population by roughly two
thirds; choosing Saturn alone would have discarded the source's own map.

### 5.4 The test this enables, and its limit

**Checked, not assumed, and it constrains the test.** The two sets are *disjoint*
in 2027 — no 2027 record carries both bodies — so every CL verdict comes from
exactly one path, and the two paths can never contradict each other on a single
event. The test is therefore a **population-level** comparison of hit rates, not a
per-event agreement count.

**Power caveat, recorded so the first year's numbers are not over-read:** 8
Rahu-conditioned events in a year is a small sample. One year cannot settle this;
several years of scored outcomes will be needed before the divergence means
anything.

Every CL verdict carries `crude_significator_contested` and names the other path
explicitly, so a consumer reading one path can never be unaware of the other.

---

## 6. `sector_mapping` — reopened, with seven items owed the same treatment

Closed at the coverage step; **reopened 12-Sep-2026 by the crude decision**. Ruling
that the source's own map is load-bearing enough to be emitted alongside the book
makes that map evidence **everywhere**, not only where it is convenient. A map that
outweighs three book sections on crude cannot be treated as decorative on autos,
pharma, FMCG or iron.

**Not blocking now:** no instrument currently in `instruments` maps to any of the
seven. The trigger point is *when an instrument mapping to that sector enters
`instruments`*.

**Treatment owed — the same shape CL just got:** both mappings carried, each with
its own tier, claim_tag and citation, neither marked primary, every affected
verdict flagged `<sector>_significator_contested` and cross-referenced to the
rival path, and the divergence recorded as the intended test rather than as a
defect.

| # | Item | Book | Source | Kind | Severity |
| --- | --- | --- | --- | --- | --- |
| 1 | IT / telecom | Mercury (ch16, appB — two-way) | **Rahu**; the source prints *no Mercury sector row at all* | omission + reassignment | high if scoped |
| 2 | Automobiles | Venus (ch16, appB — two-way) | **Saturn** (heavy commercial vehicles) **and Mars**; Venus gets no row | reassignment to two other planets | high if scoped |
| 3 | Pharma | ch16 Moon/Mars/Ketu — the chapter itself concedes *"assignment varies by scheme"*; appB Jupiter + Ketu | Mars *"Healthcare & Pharma"*, Rahu *"Pharmaceuticals"* | four-way, including book-internal | high if scoped |
| 4 | Iron & steel | ch15 double-assigns inside one chapter; ch16 resolves it to "Mars base metals, Saturn iron and coal" | keeps **both** and says so — *"the sector is ruled by Mars and Saturn both"* | the source declines the book's resolution | medium |
| 5 | FMCG | **flat contradiction between two book sections** — ch16 Venus, appB Moon | no FMCG row; invokes *"sectors ruled by Moon"* but never tabulates it | book-internal contradiction + source gap | medium |
| 6 | Gold (secondary) | Sun — the only three-way-plus-source agreement in the table | agrees, **but also puts Gold under Mars** | source-internal double assignment | **low but live** |
| 7 | Logistics | Saturn (appB extended row) | **Rahu** — the adjacent item on the same source row as crude | the identical Saturn-vs-Rahu split | low |

**Item 6 is live now and the other six are not** — GC and MCXGOLD are in scope. It
does not disturb them: gold reaches tier 1 through the source's own configuration
sections, not through any rulership, so no significator path is used and nothing
here is load-bearing yet. It becomes live the moment a gold verdict is derived
from rulership rather than read from a configuration section.

**Item 4 is the one where the source is the party refusing to resolve** — a dual
emit is what the source itself prescribes. **Item 7 should be settled by whatever
settles crude**; it is the same dispute on the adjacent item of the same row.

**Two near-misses are excluded, listed so the count of seven is auditable rather
than the result of a quiet trim:** Sun "renewables" vs Rahu "wind_power" (adjacent
rather than contradictory — no section denies the other), and Mercury
"money_flows_with_venus" vs Venus (the book states the sharing itself, so it is
not a disagreement).

---

## 7. The civil day is a property of the venue

**DECIDED 12-Sep-2026. Every instrument evaluates on the civil day of its venue's
location** — for instrument rules as well as market rules.

**Supersedes** the provisional rule that had GC and SI inheriting the Mumbai civil
day because their rules were authored in IST. **Authorship is not venue.**

**Reason.** The alternative has COMEX gold firing on a day the contract was not
trading. A verdict that cannot be acted on at its own venue is not a verdict about
that instrument. This is not a new convention: it is the dual-location evaluation
already in the build, re-keyed from rule type onto venue.

**Provenance is unchanged.** The gold and silver configuration sections keep their
IST authorship in `provenance`; nothing about the rule text, its page citation or
its authored timezone is re-stamped. Only the day boundary the rule is evaluated
against moves. Every affected verdict carries `authored_ist_evaluated_venue_day`.
Changed by this decision: **GC, SI, CL**.

### 7.1 The measured divergence — the number is large, and was asked for

No verdicts exist yet, so this is measured on the **addressable events**: the
upper bound on affected verdicts.

| Population | In scope | Land on a different calendar date | % |
| --- | ---: | ---: | ---: |
| Gold classes | 1277 | 536 | 42.0 |
| Silver classes | 1282 | 537 | 41.9 |
| CL classes | 34 | 19 | 55.9 |

**Direction is always −1, never +1.** IST is UTC+5:30 and ET is UTC−5/−4, so the
New York civil date is either the same day or one day *earlier*; it is never
later.

**This is not a defect and not a surprise.** A 9.5-to-10.5 hour offset moves any
event stamped before about 10:30 IST back a day, and the Moon ingresses that
dominate these populations are uniformly distributed across the clock, so a ~40%
shift rate is exactly what a uniform distribution predicts.

**What it means practically.** The *size* of the gold/silver population is nearly
unchanged (1276 vs 1276 — one event in, one out, both Moon sign ingresses on a New
Year boundary), but the *date* two in five of them carry changes. Anything joining
these verdicts to price data by date must key on the instrument's venue day, not
on a single global date column, or roughly two in five GC/SI rows will be joined
to the wrong session.

CL's shift rate is higher (19 of 34) purely because Saturn's 2027 events cluster
in the Indian morning; the population size is unchanged at 26 + 8 under either
day.

---

## 8. The label layer — `source_probability`

### 8.1 The headline finding

**The two "Mercury Venus Alone in Any Sign" blocks carry character-identical
prophecy text and different labels.** Block 26 (02-Jun to 08-Jun-2026, p.240) is
labelled **REASONABLE**; block 42 (26-Sep to 17-Oct-2026, p.259) is labelled
**HIGH**. Both print, character for character:

> *"Whenever Mercury Venus are alone in any sign without any other Planet(s),
> Markets are sluggish."*

Only the dates and the remarks differ. The rule does not.

**Verified independently** against `data/source_2026.html` by re-parsing all 50
prophecy blocks and grouping them by exact prophecy string — 50 blocks, 44
labelled, and the two blocks' prophecy strings compare equal. Locked by
`test_2026_regression.py::test_source_probability_labels`.

**And it is not the only case.** Three groups of blocks share character-identical
prophecy text, and **all three disagree with themselves**:

| Blocks | Rule text | Labels |
| --- | --- | --- |
| 17, 24, 31, 38, 48 | *"Sun Mercury Conjunction is a high vibration time and a Major Turning Date."* | Reasonable ×4, **Good** ×1 |
| 26, 42 | *"Whenever Mercury Venus are alone in any sign…"* | **Reasonable, High** |
| 34, 49 | *"Mercury Manifestation is a major Turning date."* | **Reasonable, Good** |

Every repeated rule text in the document is labelled inconsistently. There is no
counter-example.

**What it establishes:** the labels are **per-occurrence editorial judgements, not
properties of a rule.** Carrying one as a rule-level field asserts a stability the
source does not have. Every constraint in this section follows from that single
fact.

### 8.2 The transfer test

Three parts, all of which must hold; objective, and each computed rather than
judged by reading.

1. **Generic configuration.** The block's title names a configuration, not an
   instance. *"Venus Combust in the East"* transfers although its 2026 window is
   dated — the dates are that year's occurrence of a recurring rule. *"Jupiter
   Vargottam in Gemini"* and *"Rahu in Dhanistha"* do not: the sign or nakshatra
   binding **is** the configuration.
2. **Recurs in the span.** 01-Dec-2026 → 01-Feb-2028 IST, computed from
   `build/astronomy_2027.json`.
3. **Maps to a catalogue.** Catalogue **A** = the 20 emitted `rule_family` values
   in the build. Catalogue **B** = the **141** Chapter-1 rule sections of the
   source. A label mapping to neither is an orphan.

**RULED: catalogue B counts.** The 141 sections are the catalogue Step 4's rule
layer is being built from; excluding them because the astronomy layer has not
reached them yet would make the answer depend on **build order** rather than on
evidence. **Pass count is 19.** Under catalogue A alone it would have been 14, and
the five co-location labels (blocks 13, 26, 29, 42, 50) would have joined the
orphan list.

*Catalogue B is defined precisely so it stays checkable: every `h3.section`
element in the document (142) except the Table of Contents heading. Asserted by
the harness.*

### 8.3 The classification

44 labels, not 45 (§9). All 44 sit in prophecy blocks on lines 4335-4909 — the
monthly calendar carries none, and the 141-section rule catalogue carries none, so
there is **no per-rule probability to inherit except through these blocks.**

| Outcome | Count |
| --- | ---: |
| **Pass** | **19** |
| Fail — test 1, title names an instance | 12 |
| Fail — test 2, does not recur in the span | 12 |
| Fail — test 3, orphan | 1 |
| **Total** | **44** |

Three test-2 failures are worth naming, because each reads as a pass until it is
computed:

- **Mars Behind Jupiter in the Same Sign** (block 41, High). Three shared-sign
  windows exist in 2027, and **Mars is ahead in all three** — verified by
  longitude at the start, midpoint and end of each window. So the *behind* block
  fires zero times and the *ahead* block (50) fires three. The pair is decided by
  computation, not by reading.
- **Mercury Venus Conjunction in Contra-Directional Mode** (block 43, High). The
  rule is *direct Mercury crossing **retrograde** Venus*. Venus has **no station
  in the span**, so it is direct throughout; the two contra-directional
  conjunctions in 2027 (01-Jul, 11-Oct) have the opposite polarity — Mercury
  retrograde, Venus direct.
- **Exalted Mars if Atichari** (block 5) and **Reducing Speed of Mars** (block 45)
  fail on the open `speed_class_thresholds` question, not on the sky.

### 8.4 The eleven carried families

| Family | Keyed on | Blocks | Value |
| --- | --- | --- | --- |
| `aspect/conjunction` Sun-Mercury | family | 8, 17, 24, 31, 38, 48 | **[Reasonable, Good]** |
| `aspect/conjunction` Mercury-Venus · p.16 | family | 9, 14 | **[Reasonable, High]** |
| `aspect/conjunction` Venus-Uranus · p.34 | family | 23 | High |
| `visibility/combust` · p.14 | **body** = Venus | 2, 44 | Reasonable |
| `visibility/combust` · p.24 | **body** = Saturn | 18 | High |
| `visibility/combust` · p.20 | **body** = Jupiter | 32 | Good |
| `visibility/rise` · p.14 | **body** = Venus | 46 | High |
| Mercury Venus Alone in Any Sign p.16 | family *(catalogue B)* | 26, 42 | **[Reasonable, High]** |
| Rahu Mars Together in Any Sign | family *(B)* | 13 | Reasonable |
| Venus Jupiter in the Same Sign p.67 | family *(B)* | 29 | High |
| Mars Ahead of Jupiter in Same Sign p.69 | family *(B)* | 50 | High |

Note the asymmetry: the six Sun-Mercury labels pass through catalogue **A** only —
the source prints no Sun-Mercury pair table, and all eight of its pair tables were
read. The four co-location families pass through catalogue **B** only.

### 8.5 Disputed families emit the **set**, never a value

**Three of the eleven carried families disagree with themselves.** Where they do,
the emitted value is the set the source assigned, with the dispute flagged:

```yaml
source_probability: [Reasonable, Good]
source_probability_disputed: true
```

**Not min, not max, not mode, not first, not most-recent.** Picking one
manufactures an agreement the source never expressed. The set is honest and
trivially filterable; a single value would be a claim made on the source's behalf.

The alternative — attaching labels per occurrence instead — is incoherent here: a
2027 occurrence would have no occurrence to inherit from, and the whole premise of
the transfer is that the label attaches to a repeatable rule.

### 8.6 `visibility/combust` is keyed **per body**

At family level the combust family carries Venus Reasonable, Saturn High and
Jupiter Good — a three-way conflict. **Per body it is three families with one
value each and no conflict at all.** The source labels *a body's* combustion,
never "combustion"; keying at family level would be our aggregation, not the
source's claim. This ruling is what keeps combust out of the disputed list.

### 8.7 Blocks 10 and 20 are **not** split

Both are compound blocks: block 10 pairs Venus Rise (01-Feb-2026) with Mercury
Rise (04-Feb-2026); block 20 pairs the hemisphere turning with the Sun-Neptune
conjunction, two days apart.

**Splitting a block re-authors a source block into two blocks it did not write.**
The author labelled the *coincidence* of the two rises falling three days apart —
that pairing **is** the configuration judged, and halving it invents two
judgements out of one. Both are recorded as **test-1 failures**.

The halves are individually generic, and that is recorded because it is the
argument *for* splitting. It is not enough: a generic half is not evidence that
the author labelled the half.

**Consequence, left latent on purpose.** Because block 10 is not split,
`visibility/rise` Venus carries one label only (High, from block 46). The
Reasonable a split would have produced does not exist, so the rise-Venus conflict
stays **latent** and we do not create it ourselves. It is recorded so that anyone
who later argues for splitting knows exactly what splitting would cost.

*Block 20 was classified under test 2 in the pre-implementation report; the
no-split ruling moves it to test 1. It fails test 2 independently as well — the
hemisphere half is a tropical-equinox quantity the build does not emit — so the
ruling changes which test is named, not whether it is excluded.*

### 8.8 The scale collapses from six buckets to three

`labels.source_probability_map` defines six. **Three survive transfer: Reasonable,
Good, High.** Every `Low` (block 16), every `Very High` (blocks 12, 21) and the
single `Intense and High Reliable` (block 1) is excluded — the Low on test 1, the
rest on test 2.

**Both extremes of the scale are lost, and the reason is structural.** The
source's strongest claims all sit on once-in-decades configurations — a
Saturn-Neptune conjunction, a Saturn-Mars conjunction, a Mars-twelfth-to-Saturn
window. That is entirely coherent editorially (the rarest configuration is the
most newsworthy) and **useless for transfer** (the rarest configuration is the one
least likely to recur next year).

A consumer must not read "no Very High in 2027" as a claim about 2027. It is a
fact about which 2026 blocks survived a recurrence test.

### 8.9 Saturn-Neptune — the exclusion, on record

Written into the config verbatim, so it reads as a consequence of the rule and not
as an omission:

```yaml
exclusions:
  saturn_neptune_conjunction:
    label: "Intense and High Reliable"
    source_block: "Event of the Year -- 2026, Saturn Neptune Conjunction, pg. 211-213"
    excluded_by: transfer_test_2_recurrence
    reason: >
      The configuration does not recur in the generated span. Zero
      Saturn-Neptune conjunction records exist in build/astronomy_2027.json
      across 01-Dec-2026 -> 01-Feb-2028 IST; the pair's synodic period is
      ~36 years. The exclusion follows from the recurrence test alone and
      required no editorial judgement.
    note: >
      Independently, this is the block whose 2026 instant the source prints
      12h42m wrong (STEP3_REPORT section 6.1). The label was assigned to an
      event the source had mis-timed. That is not the ground of exclusion --
      test 2 excludes it on its own -- but it is recorded here because the
      source's single highest label sits on its single largest verified
      defect, and that bears on how much authority the label scheme is owed.
```

### 8.10 Four of the six unlabelled blocks are the eclipse blocks

Six of the 50 blocks carry no label: 11, 15, 35, 39 — **every eclipse block in the
document** — plus 37 and 47, the two mutual-Vedh blocks.

**Eclipses are impact tier T1**, the highest tier this config defines. A systematic
scheme would have labelled its own top-tier events first. That absence is itself
evidence that the labels are **editorial rather than systematic**, and it
corroborates the headline finding from the opposite direction: the headline shows
the labels moving where the rule does not; this shows them missing where the
impact is greatest. It belongs beside the disputed-family finding, not in a
footnote.

Consequence: `eclipse/solar` and `eclipse/lunar` inherit no `source_probability`
at all. Their verdicts carry the field **absent**, not null-because-unknown.

### 8.11 One orphan — recorded, no family invented

**Block 4, "Mars (Sagittarius) Tenth to Saturn", High.** It passes tests 1 and 2
outright: the source states it generically — *"Whenever Mars comes 10th to Saturn
in transit"* — and it recurs **18-Nov-2027 → 27-Dec-2027 (39 days)**, Mars in
Sagittarius, tenth from Saturn in Pisces, computed from the build.

It fails test 3 only for want of a family to attach to: no relative-house family
exists in catalogue A, and no Chapter-1 section states it. **Recorded as an
orphan; no rule family is created for it** — inventing one to receive a single
label would build the catalogue around the annotation instead of the other way
round. If a relative-house family is ever added, this is first in line.

### 8.12 Coverage — 26 rows, and that is the whole of it

| Source | Rows |
| --- | ---: |
| `aspect/conjunction` Sun-Mercury | 7 |
| `aspect/conjunction` Mercury-Venus | 3 |
| `aspect/conjunction` Venus-Uranus | 1 |
| `visibility/combust` Venus / Saturn / Jupiter | 1 / 1 / 1 |
| `visibility/rise` Venus | 1 |
| **Astronomy records** | **15** of 1569 = **0.96%** |
| Mercury-Venus alone in a sign | 5 windows |
| Rahu-Mars together (1 same-sign + 1 same-nakshatra) | 2 |
| Venus-Jupiter same sign | 1 |
| Mars ahead of Jupiter same sign | 3 |
| **Rule-layer firings** | **11** |
| **Combined** | **26** |

**Said plainly, as asked: this is a small minority, and small enough to question
the field.** 1569 is the most favourable denominator available. The Step-4 verdict
layer adds the weekday and panchang families and the 141-section catalogue — in
2026, 12 weekday families alone produced 103 Mumbai and 119 New York qualifying
dates — so the real denominator runs into the thousands and the populated share
lands **below 1%**.

A field populated on under 1% of rows cannot be filtered on, cannot be weighted
with, and cannot be aggregated. **Its honest use is narrow: provenance on ~26
specific rows, readable as "the source asserted a likelihood here", never as a
column anything downstream computes across.** Three of those rows carry a disputed
set rather than a value. That reasoning is written into the field's own
description inside the config, so no later reader mistakes sparsity for absence of
signal.

### 8.13 It is not a confidence, and nothing may make it one

`confidence` stays a separate field at `untested`, raised **only** by a
pre-registered backtest. **`source_probability` must not feed `confidence`, and
`confidence` must not be derived from `source_probability`** — in either
direction, by any rule, not as a default, not as a prior, not as a tie-break. A
label with no stated basis, no sample and no hit rate cannot raise a confidence,
and naming it confidence would import an authority the source never earned.

Nothing is emitted onto astronomy records: `emitted_on_astronomy_records: false`,
and `test_no_interpretation_leaked` still bans the name from the astronomy layer.

---

## 9. Corrections on record

Claims that did not survive checking. Recorded rather than silently repaired — the
provenance of a table is not only where its evidence came from, but also which
assertions about that evidence failed.

| # | Claim | Attributed to | Outcome |
| --- | --- | --- | --- |
| 1 | "Ch15 agrees with Ch16 and Appendix B — three-way agreement" | user prompt | **Corrected and applied.** Ch15 is a commodities chapter; it agrees on three mappings only. Mercury → IT and Venus → autos are two-way. |
| 2 | "BPHS gives Venus silver alongside the diamond" | user prompt | **Unverified.** BPHS is not in the tree and was not read. Kept as the *stated grounds* for the Venus rival, marked unverified; does not move the decision. |
| 3 | "There are 45 probability labels in the source" | user prompt | **Corrected to 44.** The likely 45th is a `div.summary` in the January calendar — narrative prose, no probability class, no block. Two further suspects are a `div.chapter-label` and a `div.subtitle`. |
| 4 | "Sun-Mercury Conjunction carries 4 labels" | user prompt | **Corrected to 6** — blocks 8, 17, 24, 31, 38, 48. |
| 5 | "the five catalogue-B-only families" | this project's pre-implementation report | **Corrected to four families carrying five labels.** Blocks 26 and 42 are two labels on one family — which is exactly why that family is disputed. The firing count of 11 is unaffected. |
| 6 | Block 20 classified as a test-2 failure | this project's pre-implementation report | **Reclassified to test 1** by the no-split ruling. It fails test 2 independently too; only the named test changes. |
| 7 | "two of the three identical-text groups disagree" | this project, drafted into the config this session | **Corrected to all three.** Caught by the new harness check on its first run, against the document. The finding is stronger than the wording claimed. |
| 8 | "B87's 'Bullish: Rahu in Shatbisha' names where Rahu happened to be in 2026; the condition is the shared nakshatra alone" | this project, batch 2 | **Corrected.** The colon restricts the verdict to a case. B87's eight windows are all Rahu-in-Shatabhisha and B88 prints the next five of the same series, Rahu in Dhanishta, with no verdict. §12.3. |
| 9 | "all eleven 2026 windows fall inside Rahu's Shatabhisha period" | user prompt | **Corrected to eight.** B87 prints eight windows, 21-Jan to 01-Aug-2026. The other five of the series are B88's and are the Dhanishta ones — which is the evidence, so the miscount understated the case rather than overstating it. |
| 10 | "In 2027 Rahu is in Dhanishta and Shravana" | user prompt | **Corrected to three nakshatras.** Dhanishta to 10-Apr-2027, Shravana to 18-Dec, **Uttara Ashadha** from 18-Dec to year end. Capricorn throughout, and Shatabhisha at no point — the conclusion is unaffected. |

Correction 7 is the reason the population counts are asserted exactly rather than
approximately: the harness found a wrong claim inside the config within one run of
that claim being written.

Two corrections carried from Step 3 remain relevant here: the Mars p.6 table is a
**rashi-frame** residency table and not a D9 ingress series (so it sits in
`rule_layer_pending`, not in any ingress class), and the Sun is never labelled for
dignity or vargottama anywhere in the source — an **editorial** absence, where the
state obtains and the source declined to print it, as against the **structural**
absences of Saturn and the outers, where the state never obtains.

---

## 10. Harness

| Suite | Before | Now | Added |
| --- | --- | --- | --- |
| `tests/test_2026_regression.py` | 55/55 | **68/68** | 13 checks — the label layer against the document |
| `tests/test_2027_astronomy.py` | 79/79 | **87/87** | 8 checks — the populated count against the build |
| `tests/test_node_anchor_unit.py` | 12/12 | **12/12** | — |
| `tests/test_rule_layer.py` | — | **74/74** | the whole suite — new with the rule layer, §12 |

**241 checks across four suites.** The fourth is the Step-4 suite and did not
exist when §1–§11 were written; it checks the rule layer against the document
and against the build, and never against itself. What it locks is in §12.

**What the new checks lock.** *Source side:* 50 blocks / 44 labels / 6 unlabelled;
every eclipse block unlabelled; the printed value distribution (High 20,
Reasonable 17, Good 3, Very High 2, Intense and High Reliable 1, Low 1); the
headline pair's identical text and differing labels; all three identical-text
groups disagreeing; catalogue B = 141 sections with zero labels inside it; and the
config's own counts re-checked against the document rather than against
themselves.

*Build side:* the **exact** populated count per family — 7, 3, 1, 1, 1, 1, 1 = 15
— all inside IST civil 2027; the four catalogue-B families firing exactly 5, 2, 1,
3 = 11; the combined 26; Mars ahead of Jupiter in all three shared-sign windows;
zero Saturn-Neptune conjunctions; and the field still absent from every record.

**Why exact and not a range.** A field populated on 26 rows drifts invisibly — 400
rows or zero would both look plausible in a spot check. If a later change moves
the number in either direction, the harness fails loudly.

---

## 11. What Step 4's rule layer gets built against

1. **Instruments and tiers are settled** (§2). Every verdict carries a tier, a
   claim_tag, a provenance and a flags list; a missing or unknown tier fails the
   emit.
2. **The civil day is the venue's** (§7), and roughly two in five GC/SI rows will
   carry a different date than they would have under the Mumbai day.
3. **Crude emits two paths, neither primary** (§5), and the divergence between
   them is the intended experiment, at population level and over several years.
4. **Seven sector disputes are queued** (§6), each owed the same dual treatment at
   the point its instrument enters scope.
5. **`source_probability` is an annotation on ~26 rows** (§8): disputed where the
   source disputed itself, keyed per body where the source labelled a body, and
   structurally incapable of raising a confidence.
6. **The rule catalogue is 141 source sections**, none of which carries a label of
   its own, plus the 12 `rule_layer_pending` items carried from Step 3.

**Still blocked on one owner decision:** `label_scheme_signoff`. No verdict rule
may be written until it lands.

**Nothing in this document generates a verdict.** Financial astrology is a
speculative interpretive framework; nothing this project produces is investment
advice.

---

## 12. The rule layer, batch by batch

Appended to as batches land. Each subsection is date-stamped and they read
oldest first, so the newest decision is the last one in the file. Nothing here
emits a verdict: `label_scheme_signoff` is still open and still blocks that.
What the batches produce is the **condition layer** — dated, per location,
every string traceable to a page.

Two counts, kept current: **87 rules over 59 of the 141 sections**, and **1635
firings** in calendar 2027 across both locations.

| Status | Rules | Emits rows? | What it means |
| --- | --- | --- | --- |
| `executable` | 60 | yes | The section's own words, computed off the astronomy layer |
| `blocked` | 25 | no | Well defined, but our layer does not carry an input it needs |
| `ambiguous` | 0 | no | The source's wording admits more than one reading, and none is picked |
| `resolved_ambiguity` | 2 | **yes** | Ambiguous, then ruled on — part of the words it fires on are ours |

**The blocked count is batch 3's story, not a backlog.** Twenty-two of the
twenty-five arrived with that batch, and nineteen of those name one of two
missing strings: sixteen the tithi boundary series, three the yoga series. One
event class added to the astronomy layer would unblock sixteen families at
once. See §12.4.

### 12.1 Batch 1 — visibility · recorded 13-Sep-2026

Seven sections: the five Combust Rise Cycles (B4, B9, B15, B22, B27) and the two
Mercury sections between them (B10, B11). Ten rules, three decisions.

**The family evaluates on the Mumbai civil day only, and says so on every row.**
Kalamsha is a horizon measurement at the primary location and the records are
`precision: date_only`, so there is no instant to convert; a New York date could
only be produced by picking one of the two New York days the Mumbai day
straddles. `locations` is narrowed and
`combust_evaluated_mumbai_horizon_date_only` travels on every firing. This does
not waive §7 — §7 is about weekday, tithi and nakshatra conditions, and this
family has none.

**Two sections are blocked on arithmetic, not on impression.** B10's dates
(10-Apr, 03-Aug, 14-Nov-2026) are not the East rise dates under any constant lag
(offsets 27, 13, 4 days) and not the greatest-elongation dates either (+6, +1,
−7); what is left is the speed crossing its one sentence describes, and
`speed_deg_day` is emitted only at other events' instants. B11 needs a greatest
elongation, which is an extremum of a series sampled nowhere near its turning
point. Both are registered, counted, and emit nothing, with the missing input
named.

**`resolved_ambiguity` became a status of its own.** B15 item c) prints "Purva"
and "Uttra" bare, and each is the first word of three nakshatras — nine readings
of the pair. It was registered `ambiguous`, reported, and ruled on as Falguni on
three independent pieces of evidence: a document-wide sweep finding exactly one
bare instance of each word against 90 and 98 qualified ones; a parallel rising
rule in the same document with the same list head and the pair written out as
Falguni; and the adjacent remark spelling "Uttra Bhadrapad" in full.

The ruling was **not** folded into `executable`, and that is the decision. A
resolved rule's dated rows are exactly as computable as any other rule's, which
is precisely why the fact that a word in its condition came from an editor has
to be carried where a reader trips over it. The dataclass enforces four things
on such a rule — the competing readings, the evidence, the readings the evidence
rejected, and a flag — and the flag is copied onto every firing, because a row
travels further than the registry does. `b015c` fires once in 2027, on Venus's
08-Sep rise in Uttara Phalguni; under either rejected reading that count is
zero, so the number is the ruling's own footprint and moves if it is revisited.

### 12.2 Batch 2 — colocation · recorded 13-Sep-2026

Twenty-one sections in which the condition is a relation between bodies:
conjunction and opposition (B12, B17, B41, B42, B47, B48, B53, B54), shared
residency (B16, B78, B84, B87, B90, B93, B112), and ordering inside a shared
sign (B18, B19, B79, B80, B85, B86). The first two groups needed nothing new.

**The navamsa ladder, and its 3°20′ resolution limit.** "Venus Behind Jupiter in
the Same Sign" needs to know which body is further along the zodiac, and the
astronomy layer emits `lon_sid` only at other events' instants — so inside a
shared-sign window there is frequently no sampled longitude for either body. The
rule layer may not call the ephemeris: a rule that reached it could disagree
with the calendar, which is the one failure this layer exists to make
impossible.

What the layer does carry continuously is each body's nakshatra and navamsa
ingress series. A nakshatra is 13°20′ and a navamsa is exactly a quarter of it,
so `(nakshatra index, pada)` is a **monotone position ladder at 3°20′
resolution**, recovered from two emitted series and one definitional identity —
1 nakshatra = 4 navamsas — and no ephemeris call.

**The blind spot, and why it is pinned rather than tolerated.** The ladder is
exact where it separates and silent where it does not. Two bodies inside the
same navamsa are within 3°20′ and their order is simply not in the astronomy
layer; those stretches carry `None` and fire nothing. That is partial coverage
with exact positives, not an approximation — but the distinction only holds if
the silence is visible. So every ordering rule declares
`ordering_from_navamsa_ladder`, and the harness pins the tied days **per pair**,
to one minute of a day:

| Pair | Tied days | Consequence |
| --- | --- | --- |
| Venus / Jupiter | **2.691 d** | 23 of 25 shared-sign days are ordered; the tie sits around the pair's conjunction and fires neither B79 nor B80 |
| Mars / Jupiter | **0.0 d** | all 83 shared-sign days ordered, all "ahead" |

A tie that grows is a change in the sky or a bug, and either way it must not
pass as an absence of the configuration. B18's three-body ordering has the
larger blind spot — about 9 per cent of the Sun/Venus/Mercury year is inside a
shared navamsa for at least one of its three pairs — and those stretches sit at
the configuration's own boundaries, so its windows are narrower than the
source's and never wider.

**Two independent checks, because a plausible method is not a validated one.**
Mars/Jupiter is cross-validated by two unrelated routes: the ladder resolves all
three 2027 shared-sign windows as Mars ahead, and `test_2027_astronomy.py` gets
the same answer from three direct `ephem.longitude()` samples per window. And
the ordering rules must close an **arithmetic identity** — ahead + behind + tied
must reconstruct the bare shared-sign window and never exceed it — which is
worth more than trusting three counts that each look plausible alone.

**Three smaller calls on record.** *Per-row verdicts:* the six outer sections
print one row per partner with that partner's own Result — Neptune-Venus is
"Bearish" while Neptune-Saturn is blank — so each row is generated as its own
rule from the table, and a blank Result is carried as no verdict rather than as
the section's general one. *B18's comma is not promoted to a separator:* its
note states an outcome joined by a comma rather than the document's usual dash,
so the outcome stays inside `condition_text` and the rule understates its own
section; the flag `outcome_stated_but_not_separable_no_dash` says exactly that.
*B19 is blocked on its proviso:* the ordering is as computable as B18's, but the
remark's verdict holds only "provided there is a malefic aspect on Mercury", and
the layer carries aspect records with no valence — so the condition is not fired
with the proviso quietly dropped.

**One method note that generalises.** The check that no rule module reaches the
ephemeris is an **AST parse**, not a text search. A grep flagged the prose in
`colocation.py` that *explains* why the ladder exists — the sentence naming
`ephem.longitude()` — as a breach of the rule it documents. A check whose false
positives are its own documentation is a check people learn to ignore.

### 12.3 B87 re-read — the colon is a condition · recorded 13-Sep-2026

**What changed.** B87's heading is "Moon and Rahu in Same Nakshtra — Bullish:
Rahu in Shatbisha". Batch 2 read the second half as naming the 2026 instance and
carried the whole string as the verdict, flagged
`verdict_text_names_the_2026_instance`. That reading was wrong. The colon
**scopes** the verdict: the general rule is the shared nakshatra, and Bullish is
asserted for the Shatabhisha case only. The two readings are not stylistic
variants — one emits "Bullish" on 28 dated 2027 rows and the other emits it on
none.

**The evidence is the document's own partition of the series**, and it is
stronger than the reading it settles.

| | B87 "…Bullish: Rahu in Shatbisha" | B88 "Rahu in Dhanistha" |
| --- | --- | --- |
| Windows printed | 8, 21-Jan → 01-Aug-2026 | 5, 27-Aug → 15-Dec-2026 |
| Rahu's nakshatra at each | **Shatabhisha**, all eight | **Dhanishta**, all five |
| What each window is | the Moon's transit of Shatabhisha, 306°40′ → 320°00′ | the Moon's transit of Dhanishta, 293°20′ → 306°40′ |
| Verdict printed | Bullish | **none** |

One monthly Moon-with-Rahu conjunction series, tabulated in two sections split
by which nakshatra Rahu occupies, with Bullish printed on one part and nothing
on the other. If the colon were a label the two sections would not differ that
way. Checked against the ephemeris on the source's own printed times — which the
same arithmetic shows to be **IST**, since read as UTC the entries miss the
nakshatra cusp by about 3°, which is 5h30m of Moon motion.

**What the section is now.** Two rules, which is the shape B78/B79/B80 already
had — a bare window plus its conditioned verdicts.

| Rule | Condition | Proviso | Verdict | 2027 |
| --- | --- | --- | --- | --- |
| `b087_moon_rahu_same_nakshatra` | Moon and Rahu in Same Nakshtra | — | **null** | 28 Mumbai days |
| `b087s_moon_rahu_same_nakshatra_rahu_in_shatabhisha` | the same | Rahu in Shatbisha | **Bullish** | **0**, pinned by name |

`verdict_text_names_the_2026_instance` is gone, replaced by
`verdict_conditioned_on_rahu_in_shatabhisha_not_met_in_2027` on the bare rule
and `verdict_scoped_by_colon_in_title` on the scoped one. The old flag called
the second half an artifact; the new one calls it a condition, which is what it
is.

Rahu is in Shatabhisha at no point in 2027 — Dhanishta to 10-Apr, Shravana to
18-Dec, Uttara Ashadha to year end, Capricorn throughout — so `b087s` fires zero
times, and the zero is pinned with that reason in `EXPECTED_ZERO_FIRING`
alongside `b004` and `b015r`. This is **B19's treatment reached by a different
route**: there the proviso cannot be evaluated, here it can be and is not met.
Either way the condition is what fires and the verdict is withheld.

**One schema change.** `Rule` gains `condition_proviso`, verbatim from the
source and checked as a substring of the document exactly as `condition_text`
is. It is a separate field rather than text glued onto the condition, because
the two are different strings on the page: concatenating them would have
produced an authored sentence that no substring check could see. A proviso with
no verdict to restrict is a construction error and raises.

**The re-scan.** Every ported section was re-read for the same shape — a colon,
comma or "if" that scopes a verdict to a case rather than labelling it. **Among
batches 1 and 2, B87 was the only one.** The sweep also ran over the unported
sections, and what it found is owed to the batches that will meet them:

| Section | Shape | 2027 |
| --- | --- | --- |
| **B89** "Mars in the Nakshtra of Rohini or Chitra — Bullish: **Mars in Rohini**" | the same colon shape, in a title. Its one printed window, 04-Jul-2026, is the Rohini one | Mars enters **Chitra** 13-Aug–03-Sep-2027 and **never Rohini** — condition fires, proviso not met, the same way round as B87. Must be split the same way |
| **B60** remark: "Amavasya on Tuesday — Bullish. Amavasya **if** Moon in Sagittarius or Pisces — Bearish" | two statements in one remark; `split_statement` takes the first dash, so the verdict half swallows the second rule entire | batch 3. Two rules; the second's proviso is computable from the Moon's sign |
| **B67** note: "…Tithi Kshay in Dark Fortnight of Asthami, **particularly on Tue, Sat or Sun** — Immediate Bullish" | the same double-statement shape, the second carrying a weekday proviso | batch 3 |
| **B116** note: "…Result will be different **if** aspect by benefic planets… **if** the malefic planets are other than Sun" | two provisos, both needing a benefic/malefic valence — **the same missing input that blocks B19** | later batch; likely blocked, not split |
| **B71** note: "Observation — D9 results, Sagittarius/Capricorn — Bullish, Aquarius — Bearish, Pisces — Dicey/Volatile" | a per-case verdict list in prose; "Observation" is a label, not a condition | later batch |
| **B118** "Shar — Mars, Mercury, Jupiter, Venus, Saturn, Herschel, Neptune" | the dash separates a **list**, not a verdict; `split_statement` misfires here | Vedha batch, already blocked on `speed_class_thresholds` |
| **B98** "Mool Nakshtra: Mercury in Mool Nakshtra — Bearish" | a colon **left** of the dash, heading the condition. **Not** this shape | no action |

Distinguished from all of these, and left alone: verdicts that segment their own
window in time — B22's "first nine days fall, then bullish till Rise", B92's
"1st 2 Days Bullish, Then Bearish", B99's "First 15 Days Bearish, Then Bullish",
B15 item a). Those are one verdict with an internal boundary the source states
in prose and never dates, already carried whole under
`verdict_segments_the_window`. A proviso restricts *whether* the verdict holds; a
segmentation describes *how* it unfolds once it does.

**What the harness gained** — four checks, 56 → 60:

- every `condition_proviso` is verbatim from the document, and exists only where
  there is a verdict for it to restrict;
- B87's and B88's thirteen windows are one Moon-Rahu series partitioned by
  Rahu's nakshatra — Rahu's position checked at every window, each window
  checked to be the Moon's transit of that nakshatra to better than 0.01°, and
  B88 checked to print no verdict at all;
- the bare rule withholds its verdict and carries the flag saying why; the
  scoped rule carries the proviso, the verdict, and the same condition text;
- exactly B87 and B89 scope a title verdict with a colon, and **no ported
  verdict still has a scoping colon inside it** — which is what a careless port
  of B89 would produce. The one exception is pinned by name: `b010`'s verdict
  begins "Note:", the document's own label on its paragraph, carried with the
  text because it is part of what the paragraph says.

The last of those is the re-scan kept as a check rather than as a finished
sweep, in the same spirit as the B15 elision sweep: a second instance of the
shape must be ruled on, not quietly absorbed into an existing reading.

**Nothing moved in the astronomy layer.** `build/astronomy_2027.json` is
byte-identical, the total firing count is unchanged at 1327 — `b087` fires the
same 28 Mumbai days it did before and `b087s` adds none — and what changed is
that 28 rows no longer carry a verdict the source did not state for them.

### 12.4 Batch 3 — the weekday and panchang families · recorded 13-Sep-2026

Thirty-one sections, the largest batch so far and the first in which most of
the work is a refusal. **Eleven fire, twenty do not**, and the line between
them is almost entirely one missing input.

| | Sections | Rules |
| --- | --- | --- |
| Fire | B55, B60, B61, B71, B72, B97, B102, B103, B104, B105, B110 | 14 |
| Blocked | B56, B62, B64-B69, B73-B76, B95, B96, B100, B101, B106, B108, B109, B111 | 22 |

#### The tithi is sampled but not bounded

Every record in the astronomy layer carries `panchang.tithi`, `tithi_name` and
`paksha`. All three are the value **at that record's instant**, and the layer
emits no tithi ingress event class. A tithi runs about 23 hours 40 minutes and
its boundaries fall where nothing else is happening, so they are not
recoverable from records sampled at other events.

That is not a technicality. "Ekadashi on Friday" is a question about which
Fridays an Ekadashi *touches*, and the source answers it to the minute —
`13-Feb-26, Till 14:26`. Nothing in the layer supplies that instant. Sixteen
sections turn on it:

> B64, B65, B66, B67, B68, B69, B73, B74, B75, B76, B95, B100, B101, B106,
> B108, B109

**They carry one shared string, not sixteen paraphrases of it**, and the
harness asserts that they do. The point is what the report can then promise: a
tithi ingress class added to Step 3 unblocks sixteen families at once, and a
reader can only see that if the reason is literally the same reason. The three
yoga sections (B56, B96, B108) are blocked the same way on the same absence in
the same panchang block. B108 needs both and names both, rather than being
filed under whichever was noticed first.

The remaining four blocks are one-offs, each with its own named input. B62
needs a first-crescent visibility computation — its Tithi column reads
Pratipada and Dwitiya, so the event is the *sighting* and not the conjunction,
and Step 3 already measured `swe.heliacal_ut` against the source's Venus rise
dates and found it 9-10 days out. B111 needs the lunar month system, which is
`month_system_confirmation`, still open. B55's remark needs sunrise and the
ghati. B71's note needs the Moon's navamsa series — the same absence that stops
the batch-2 ladder ranking the Moon.

#### What a bare nakshatra name means, established rather than assumed

Six sections state a condition as a nakshatra and a weekday with no body named:
"Anuradha on Sunday". Reading that as the **Moon's** nakshatra is the single
assumption the whole family rests on, so it was tested against the document
before anything was ported, by recomputing the 2026 sky.

| Section | Printed | Recomputed | Result |
| --- | --- | --- | --- |
| B71 Uttara Phalguni, 14 windows | 14 | 14 | every start date, end date and **both times to the minute** |
| B104 Mrigashira on Thursday | 6 | 6 | exact |
| B105 Uttara Ashadha on Monday | 4 | 4 | exact |

B71 is the strongest of the three: fourteen windows with both ends timed is
enough structure that a wrong body could not come close. B97 settles it from
the other direction — it is the one section of the six that says "Moon" aloud,
and it names the same star as B104 on a different weekday.

Two further things fall out of these reproductions. The source's printed times
are **IST**, which is the same arithmetic that fixed B87's; and the day
convention is the project's own `civil_day_overlap`, which Step 3 chose on 13
tables and which here reproduces two more without adjustment.

#### The source's own tables are incomplete, and by how much

Across the same six sections the condition occurs **23 times** in 2026. The
document prints **18 dates**: seventeen of those occurrences, and one on which
the condition does not hold at all.

| Section | Occurs | Printed | Omitted | Printed but never holds |
| --- | --- | --- | --- | --- |
| B72 Ashwini / Tuesday | 3 | 1 | 04-Aug, 29-Sep | — |
| B97 Mrigashira / Monday | 3 | 2 | 13-Jul | — |
| B102 Anuradha / Sunday | 2 | 2 | 03-May | **28-Jun** |
| B103 Shatabhisha / Tuesday | 5 | 3 | 17-Feb, 12-May | — |
| B104 Mrigashira / Thursday | 6 | 6 | — | — |
| B105 Uttara Ashadha / Monday | 4 | 4 | — | — |

On B102's 28-Jun-2026 Anuradha ended at **22:11 the previous evening** and the
Moon was in Jyeshtha all day. The date is in the table anyway.

Three explanations were tested and none survives. *Overlap length:* B104 prints
a window lasting 1.19 hours and B102 omits one lasting 16.83. *Market hours:*
B104's 01-Jan-2026 window opens at 22:50 and is printed, annotated "Off-Market"
by the source itself. *Weekday:* two Sundays with near-identical Anuradha
overlap are treated oppositely — 31-May printed, 03-May not.

So the conclusion is the plain one: **the tables are incomplete and the titles
are the rule.** These rules therefore fire on days the source did not print,
deliberately, and the harness pins all six omissions and the one spurious date
**by name** — "the source omits some" is an impression, "the source omits
04-Aug-2026" is a fact a reader can go and check.

That two of the six reproduce exactly is what makes the other four a finding
about the document rather than about the reading.

#### Panchak — the second resolved ambiguity

The document names Panchak thirteen times and defines it nowhere. Two
definitions are in ordinary currency: the Moon from Dhanishta's third pada
through the end of Revati, and the Moon in Aquarius or Pisces. They denote the
same 60-degree arc, but only under the same ayanamsha and the same
27-division, so they are two claims rather than one.

Ruled on as the two-sign reading, on three pieces of evidence. **All thirteen**
of the section's own 2026 windows come back with the printed start date, the
printed end date and both printed times to within two minutes. The arc is 60
degrees and the printed windows run four and a half to five days, which is the
word itself — *panchaka*, five. And the count is thirteen against thirteen,
none left over and none missing.

The five-nakshatra reading is recorded as **not rejected** — it names the same
arc — but not used, because it needs a navamsa boundary the Moon has no series
for. Filed `resolved_ambiguity` beside `b015c`, never counted in with the
executable rules, and `panchak_definition_supplied_not_printed` travels on
every one of its 74 rows. The thirteen-window reproduction is kept as a harness
check rather than as a sentence inside `resolution`: a ruling nobody re-runs
decays into an assertion.

#### One schema change — the weekday is a property of the venue's day

`Rule` gains `weekdays`, and `fire` applies it **after** a span has become a
day at a location.

It could not go anywhere else. A condition function receives a `Sky`, which is
location-blind by construction, so evaluating "on Sunday" inside one would
force a single calendar on both venues — exactly what
`weekday_rule.evaluate_per_location` forbids, and what §7 measured at 103
Mumbai dates against 119 New York. "Anuradha on Sunday" is one condition living
in two frames: the Moon's nakshatra is a fact about the sky, Sunday is a fact
about the calendar a venue keeps. The 2027 lunar eclipse of 21-Feb falls on
Sunday in Mumbai and Saturday in New York, and both rows are correct.

The weekday set is **read out of the rule's own condition text**, never typed —
`names.weekdays_in` — and the harness checks that each rule declares exactly
what its condition names. The nakshatra is read the same way. It also checks
that the filter does work rather than passing vacuously: 25 Mumbai rows survive
of 183 day-matches.

#### The B87 re-scan, continued — and it caught six more

§12.3 predicted that B60 and B67 would need handling in this batch. Both did,
and the sweep turned up a third shape §12.3 had not seen.

**The final dash.** Six titles join the two halves of one condition with a dash
and then add the verdict with a second: *"Kshay Tithi — Shukla Paksh (Bright
Fortnight) — Bearish"*. `split_statement` takes the first dash and returns
"Shukla Paksh (Bright Fortnight) — Bearish" as the verdict, filing half the
condition inside the outcome. **That is B87's colon in a different mark.** B66,
B67, B68, B69, B75 and B76 are ported on `split_final` instead, each flagged
`condition_split_at_final_dash`, and the harness pins the set at exactly six so
a seventh cannot arrive unexamined. None of the document's eight multi-dash
statements is in batches 1 or 2 — the earlier batches are clean.

**The full stop.** B60's remark is two whole rules in one paragraph: *"Amavasya
on Tuesday - Bullish. Amavasya if Moon in Sagittarius or Pisces - Bearish"*.
Split at the period into `b060t` and `b060s`. The period is accepted where
B18's comma was refused, and the difference is that a **test** can be put to
it: `split_sentences` splits only when every part it produces is itself one of
the document's own dash statements, and raises otherwise. It refuses B57's
note, which is what it should do. The section's own Day and Sign columns print
the two conditions, so the split is a reading of the section and not of one
sentence.

**The parenthetical gloss.** B72 states its verdict and then defines its
condition *after* it: *"Mangal Ashwini Yog — Bullish (Ashwini Nakshtra on
Tuesday)"*. The condition is taken from the parenthetical — the document's own
definition of its own term — rather than from the yoga's name, which nothing
could compute. Flagged
`condition_read_from_the_titles_parenthetical_gloss`.

#### Two smaller calls on record

**B61 carries a verdict that names no side.** "Usually markets tends to make
top or bottom near Full Moon" is the section's outcome and is carried whole,
tagged `Observed` by the mechanical marker test, which is right — the source is
hedging its own observation. It is flagged
`verdict_states_a_turn_not_a_direction`: a turning point without a direction is
a verdict the source stated, and resolving it into Bullish or Bearish would be
this layer inventing the half the author withheld.

**B101's weekday is counted, not required.** "Three Saturday in Shukla Paksh"
counts Saturdays inside a fortnight; it does not require the firing day to be
one. `weekdays` is deliberately left unset with
`weekday_is_counted_not_filtered`, because declaring it would describe a filter
the rule does not have.

#### Harness — 60 to 74

Fourteen checks, and the substantial ones recompute the **2026** sky directly,
which no rule may ever do. That is the point of putting them in the harness: a
rule reads the generated 2027 calendar and never the ephemeris, so the only way
to ask whether it *read the document right* is to set the document's own 2026
tables against an independent computation. The method is batch 2's ladder
cross-check and §12.3's B87 partition, applied a third time.

- B71's fourteen windows are the Moon's, both ends to the minute;
- Panchak's thirteen windows reproduce under the resolved definition;
- the six weekday sections differ from their own titles in exactly the pinned
  places — six omissions and one spurious date, listed by date;
- every weekday rule declares exactly the weekdays its condition text names,
  every weekday firing lands on a declared weekday of its **own** location's
  calendar, and the filter demonstrably removes most of what it matches;
- sixteen sections share one tithi-series string and three share one
  yoga-series string, with B108 in both;
- exactly six titles split differently at the first and final dash, all six are
  ported on the final-dash reading, and each carries the one-word verdict that
  dash separates.

**Nothing moved in the astronomy layer.** `build/astronomy_2027.json` is
byte-identical again. Firings rise from 1327 to 1635, all of it batch 3's own
308 rows.

#### What batch 4 inherits

Sections this batch deliberately left aside, because their condition is
orbital geometry or a curated list rather than a calendar: **B57** and **B58**
(Moon apogee and perigee, each with a stated distance threshold the layer *can*
evaluate — `distance` is emitted on every record), **B59** (perihelion and
aphelion), **B63** (Hemisphere, which needs a tropical solar longitude the
sidereal layer does not emit), and **B70** (Big Volatile, whose dates are
"sorted on multiple parameters" the document never states — a
`source_selection_rule` block).

Carried forward from §12.3: **B89** is still unported and still owed B87's
treatment — *"Mars in the Nakshtra of Rohini or Chitra — Bullish: Mars in
Rohini"*, where 2027 puts Mars in Chitra from 13-Aug to 03-Sep and never in
Rohini, so the condition fires and the proviso is not met, exactly as B87 does.
And **B116** remains the one section whose provisos need the benefic/malefic
valence that blocks B19.

### 12.5 The tithi and yoga boundary series — recorded 13-Sep-2026

Step-3 work arriving late. Two event classes were added to the **astronomy**
layer — `tithi_ingress` and `yoga_ingress` — in `finastro/` and
`build_2027.py`, under Step 3's discipline and not inside the rule layer. The
no-ephemeris-from-rules rule is untouched: `finastro/sky.py` gains
`tithi_spans()` and `yoga_spans()`, which read the emitted records the way
`spans()` reads a sign series, and the AST check that no rule module reaches
the ephemeris still passes.

#### What the two classes are, and why only one of them is frame-free

A tithi is a 12-degree step of the Moon–Sun elongation and a yoga a 360/27 step
of their **sum**, both bisected to the second. That is the method the Bhadra
section states for its own windows — a 6-degree step of the same angle —
applied to two other multiples of it.

The authorisation for this work said both classes were certainty A because "the
ayanamsha cancels, exactly as recorded for Bhadra". That is right for the tithi
and **wrong for the yoga**, and the difference is now carried on every record
rather than assumed away:

| | Angle | Ayanamsha | Measured |
| --- | --- | --- | --- |
| Tithi | Moon **−** Sun | subtracts from both, cancels | identical **to the second** under Lahiri, Krishnamurti, Raman, Fagan-Bradley and in the tropical frame — 374 boundaries, worst shift 0.000 s |
| Yoga | Moon **+** Sun | subtracts twice, cancels nothing | Lahiri **64 s**, Krishnamurti 22 min, Fagan-Bradley 3h17m, Raman 5h24m, against the source's own printed edges |

Read tropically the yoga edges do not shift — they name **different yogas**
(Saubhagya, Shobhana, Siddha, Sadhya in place of Vyatipata, Variyana,
Vaidhriti, Vishkambha). So the source's yoga is sidereal, and its ayanamsha is
measurable from these fourteen printed times alone, as sharply as the Sankranti
table measures it.

Both classes stay certainty A, on different grounds, and each record says
which: `frame_free_elongation_ayanamsha_cancels` on a tithi ingress,
`ayanamsha_dependent_sum_of_longitudes` on a yoga ingress. The yoga series is
exact **given** config's Lahiri, which is the standing a `sign_ingress` has
always had. The harness checks that no record carries both flags, because a
distinction nothing can violate is decoration.

#### Validated against the source before any rule was wired

| Fixture | Printed | Result |
| --- | --- | --- |
| Bhadra pp.120–124, the 8 boundaries that are also tithi boundaries | 16 rows, 8 coincident | all 8 within **25 s** — the agreement the Bhadra check records for the karana series |
| 36 tithi edges across B65, B73, B74, B75, B76, B109 | 36 | 35 within **68 s**; 1 is a source defect |
| Kshay / Vriddhi, B66–B69 | 28 rows | **28/28**, every tithi named correctly, no omission and no extra |
| B65 Ekadashi on Friday | 6 | **6/6**, no extra |
| B73 Ashtami on Tue/Sat | 9 | 7 reproduce; 2 are printed against Sunday |
| B74 Ashtami on Mon/Thu/Fri | 12 | **12/12**, 6 omitted occurrences |
| B95 Shukla Pratipada on Sat/Sun | 4 | **4/4** |
| B100 Shukla Shasthi on Friday | 1 | **1/1**, 2 omitted occurrences |
| B109 Shukla Trayodashi on Tue/Sat | 7 | **7/7** within 56 s, 1 omitted |
| B96 Vyatipata on Tue/Sat/Sun | 9 | **9/9**, no omission and no extra |
| B106 Amavasya ghadi | 4 | **4/4** within 2 min, 2 omitted; 1 source defect |
| B108 Shukla Ekadashi with Vyatipata / Vaidhriti | 1 | **1/1**, the only 2026 occurrence |
| B56 yoga in Panchak | 6 | 5 within a minute; 1 source defect |

Every printed time above is read out of `data/source_2026.html` through the
catalogue rather than transcribed, and all of it lives in
`tests/test_2026_regression.py`, which recomputes the 2026 sky directly. It has
to live there: a rule reads the generated 2027 calendar and never the
ephemeris, so a check placed in the rule harness could only compare the engine
with itself.

#### Three source defects, none of them a tolerance

**B76's 03-Jun-2026 cell.** The row reads "Till 23:31". Krishna Chaturthi that
month runs 03-Jun 21:21:45 → 04-Jun 23:30:59, so the printed time is the
correct **end** of the tithi to one second, set against the day the tithi
*started*. Thirty-five of the thirty-six printed edges agree within 68 s; this
one is 7755 s out against its own date and 1 s out against the next — the
13-Jan Bhadra shape exactly, a right value in a wrong cell, identified by the
value rather than by the cell.

**B106's third row.** It reads `28-Mar-25 *` at 08:27. The Amavasya satisfying
the condition in that lunation opens **18-Mar-26 08:25**. Wrong day, wrong
year, and asterisked by the document itself — the year-typo class README
already records at `17-Apr-25`, with a transposed day on top of it.

**B56's 06-Jun-2026 row.** It asks for Indra inside Panchak. Indra ends that
day at 10:04 and Panchak opens at 19:03 — and B55, the source's own Panchak
table, prints that window as starting **19:05**. The contradiction is between
two of the document's own pages, not between the document and this engine. The
competing reading — "in Panchak" as sharing a civil *day* — would recover the
row and cost one extra elsewhere, a single row of evidence either way; it is
recorded, not rejected. The instant reading is kept because every other
conjunction of conditions in this package intersects spans, and because §12.4
already ruled on this shape when B102's 28-Jun row named a day its own title
could not reach.

All three are in `source_defects` in `config/conventions.yaml`, each with its
verification method and the check that pins it.

#### What cleared, and what did not

§12.4 promised that one restored input would clear sixteen families. Eighteen
distinct sections carried one of the two shared strings (sixteen the tithi,
three the yoga, B108 both). **Twelve cleared. Six did not** — and that is the
part worth stating precisely, because "still blocked" must stop meaning "still
waiting for the same thing".

| | Sections | Count |
| --- | --- | --- |
| Now `executable` | B65, B73, B74, B75, B76, B95, B96, B100, B106, B108, B109 | 11 |
| Now `resolved_ambiguity` | B56 | 1 |
| Still `blocked`, on **sunrise** | B66, B67, B68, B69 | 4 |
| Still `blocked`, on **sunset** | B64 | 1 |
| Still `blocked`, on a **per-location weekday count** | B101 | 1 |

**B56 cleared onto a resolved ambiguity, not onto `executable`.** Its yoga half
is now available; its Panchak half is `b055`'s condition, and `b055` is a
resolved ambiguity because the document names Panchak thirteen times and
defines it nowhere. A rule cannot inherit the condition and shed the status. So
`b056` carries `panchak_definition_supplied_not_printed` on all 15 of its
Mumbai rows, and it cites the **same four strings** `b055` cites, from shared
constants — a second paraphrase of one ruling is how two rules come to rest on
two slightly different rulings.

**Kshay and Vriddhi needed more than a boundary, and the reproduction measures
how much more.** A tithi is Kshay when no sunrise falls inside it and Vriddhi
when two do. Both are statements about the tithi's boundaries *and* the day's,
and no arc, ayanamsha or bisection supplies the second half. Read against
Mumbai sunrise all four tables come back exactly — B66 9/9, B67 8/8, B68 6/6,
B69 5/5, every tithi named correctly, nothing omitted and nothing extra — which
is what licenses naming *sunrise alone* as the remaining input instead of
leaving the four under the old shared string. They clear the day a sunrise
series exists, and the 28-row reproduction is already in the harness waiting
for it.

**B101 is not an astronomy gap at all.** Its fortnight bounds are now exact:
the bright fortnight opening 11-Sep-2026 08:57 closes 26-Sep 22:19 and holds
Saturdays on the 12th, 19th and 26th, which is the 12-Sep-to-26-Sep the section
prints — and a second such fortnight, 10-Oct to 26-Oct, is omitted by the
source. What is missing is the ability to **count** those Saturdays at a named
venue from inside a condition function, and a condition function receives a
location-blind `Sky` by construction. Counting them there would force one
calendar on both venues, which `weekday_rule.evaluate_per_location` forbids and
which the whole of §12.4's weekday handling exists to prevent. The missing
input says so in those words, so that nobody reads it as a third event class.

#### Two findings about the source's tables, in §12.4's own terms

**B73 prints two rows its own title cannot reach.** "Ashtami on Tuesday /
Saturday" lists 11-Jan-26 and 10-May-26 against *Sunday*. Each is the day after
a Saturday Ashtami this rule does fire on — 10-Jan from 08:24 and 09-May from
14:03, both running past midnight into that Sunday. The section's Monday column
does not settle which day was meant: the Monday after a Saturday and the Monday
after the Sunday following it are the same Monday. Treated as §12.4 treats
B102's 28-Jun row — the title is the rule.

**The Chaturthi and Pratipada "extras" are not extras.** B75 prints 12 dates
and the rule emits 24 Mumbai days; B95 prints 4 and emits 7. A tithi runs about
23h40m and touches two civil days more often than one, and the source prints
one of them. That is a different fact from B74's six genuinely unprinted
occurrences or B100's two, and the notes say which is which per section rather
than reporting one undifferentiated count of extras.

#### Counts

The astronomy layer moves from **1569 to 2455 records**, purely additively:

| Class | Records |
| --- | --- |
| `tithi_ingress` | **433** |
| `yoga_ingress` | **453** |
| the 11 pre-existing classes | 1569, unchanged |

Verified rather than asserted: of the 1569 ids in the previous build, **0 are
missing and 0 have a changed field value**, and the only `meta` change is
`record_count`. The build is deterministic — two consecutive runs produce a
byte-identical file, `sha256
1d9d8f93eed6ef189a03e963d6457f863c5e3c1cb7afca3f819fff3fc0ab0190`.

The rule layer moves from 60 executable / 25 blocked / 2 resolved to **71
executable / 13 blocked / 3 resolved**, over the same 87 rules and 59 sections,
and firings rise from 1635 to **1934**. No rule stopped firing, and no new rule
fires zero times.

Harness: 2026 regression 68 → **91**, 2027 astronomy 87 → **104**, rule layer
74 → **77**. The new astronomy checks assert what a spot check cannot see — that
each series advances exactly one division per record across the whole span,
that no division runs past 30 hours (which is how a too-coarse scan step would
show itself), that every instant sits on an exact multiple of its arc to under
an arcsecond, and that the panchang layer carries the division **entered**
rather than the one sampled at the cusp. That last one is load-bearing: the
instant *is* the boundary and is rounded to the second, so without the override
about half of the 886 new records would name the division they had just left.

#### What batch 4 inherits from this

Unchanged from §12.4's list, plus one item that is now cheap: **a sunrise and
sunset series** would clear B64, B66, B67, B68 and B69 — five more sections —
and the reproduction that proves it is already written. It is a third event
class and was not authorised alongside these two, so it is recorded here rather
than taken.

### 12.6 The sunrise and sunset series — recorded 14-Sep-2026

The third event class, and the first that is not a fact about the sky. Added to
the **astronomy** layer as `sunrise` and `sunset`, under Step 3's discipline:
`finastro/panchang.py` supplies the crossings, `build_2027.py` emits the
records, `finastro/sky.py` reads them back, and no rule computes one. The AST
check that no rule module reaches the ephemeris is untouched and still passes.

#### Why this class needed a schema change and the other two did not

A tithi boundary is an angle reaching an exact multiple of twelve degrees. It
happens once, the whole Earth shares the instant, and asking where it was
observed from is a category error — which is why `tithi_ingress` records carry
no location and why adding one would be wrong rather than merely redundant.

A rise is the opposite. The Sun meets one horizon at one place, at a time no
other place shares. A record of a sunrise without a location is not an
under-specified Mumbai record; it is not a record of anything. So the schema
refuses it:

```python
LOCATION_REQUIRED = ("sunrise", "sunset")
```

`EventRecord.__post_init__` raises on a record of either class with no location,
and the harness both asserts it across the emitted file and *attempts the
refused construction* to confirm the guard bites rather than merely being
documented. Both venues are generated — 427 civil days each, one rise and one
set per venue per day, 1708 records — and neither is a fallback for the other.
The 2026 source computes its own rise and set for Mumbai alone and says so,
naming Mumbai "the reference place declared by this calendar"; that is a fact
about the source, not a licence to emit one venue and let a New York reader
infer the other. The two sunrises are about ten and a half hours apart and no
fixed offset recovers one from the other across a year.

`panchang.sunrise` and `panchang.sunset` already existed and already took a
location. They are used as they are. No location-free wrapper was added, and the
two now share one `_horizon_crossing`, so the convention is stated once rather
than twice.

#### A defect found by emitting the series, which the old check could not see

`panchang.sunrise` anchored its Swiss Ephemeris search at **local noon**, so it
returned the rise of the **following day**. A true instant filed under the wrong
date — the defect class this project exists to make impossible, sitting inside
this project.

It is worth recording exactly why nothing caught it. §12.5's Kshay/Vriddhi
reproduction — the 28-row check that licensed this whole batch — builds a list of
sunrise instants over a range and asks how many fall inside each tithi. A set of
sunrise instants shifted by one day covers the same interval and yields the same
counts. The check was correct, it passed, and it was *structurally incapable* of
seeing the bug. It took emitting the crossings as **dated records** to make the
date visible at all.

The search is now anchored at the venue's own civil midnight, which is the civil
day the rest of the layer is keyed on under
`weekday_rule.convention: civil_day_overlap`. Sunset values are unchanged by the
fix — a search from local noon and one from local midnight find the same evening.
Two cheap checks now exist so it cannot return: in the 2026 suite, every rise and
set falls on the day it was asked for at both venues; in the 2027 suite, at both
venues on all 427 days the Sun rises before it sets and the day length stays
inside its latitude's range (Mumbai 10.86–13.14h, New York 9.08–14.92h).

#### Certainty B, and where the B actually lands

The authorisation said B rather than A, and that is right: a rise depends on
which part of the disc touches the horizon, on whether refraction is applied, and
on the horizon's own height. Every record carries the convention it was computed
under — `rise_set_convention=disc_center_no_refraction`, `disc=center`,
`refraction=none`, and the lat/lon/alt of the horizon itself — so no reader has to
know which build produced the file to know what the time means.

The document prints **four** Mumbai times to the minute. They are not in a table;
they are inside the Bhadra section's prose, explaining why its reference place
matters: *"09-Jan (opens 07:06, before Mumbai sunrise 07:13), 27-Apr (opens
06:08, before sunrise 06:16), 28-Jul (opens 18:20, before sunset 19:16) and
29-Sep (opens 06:14, before sunrise 06:29)"*. They are read out of
`data/source_2026.html` by the harness rather than transcribed.

The engine reproduces all four within **4m43s**. That is the agreement claimed
and the only one claimed, because the four **do not decide the convention** — and
that is measured, not asserted:

| Convention | Worst error | Mean |
| --- | --- | --- |
| disc centre, no refraction (**pinned**) | 283 s | 194 s |
| disc centre, with refraction | 114 s | 80 s |
| upper limb, no refraction | 208 s | 127 s |
| upper limb, with refraction | 168 s | 59 s |

Every one has errors of **both signs** across the four rows, so none is a fixed
offset from the source's and no correction recovers one from another. Four times
printed to the minute cannot separate conventions whose spread is four and a half
minutes. The convention stays the one the kalāṃśa calibration was fitted under,
because kalāṃśa is the gap between a planet's rise and the Sun's rise and a gap
measured between two different conventions is not a gap — and a harness check now
pins `panchang.RISE_SET_CONVENTION` to `combustion.rise_set_flags` so the two
cannot drift apart.

**One row of the document decides it independently, and it is worth what one row
is worth.** B66 prints 23-Feb-26, Saptami, as a Kshay tithi. Shukla Saptami runs
23-Feb 09:09:45 to 24-Feb 07:02:37, and Mumbai sunrise on 24-Feb is 07:05:07
without refraction and 07:02:29 with it — one side of the tithi's end and then the
other. Read without refraction the Saptami holds no sunrise and is Kshay on
23-Feb, which is the printed row; read with refraction it is not Kshay at all and
the following Ashtami is, on 24-Feb. An **eight-second margin**, one row in
twenty-eight, pointing the same way as the kalāṃśa calibration. Corroboration,
recorded as corroboration and not as the ground.

The same measurement says where the grade lands. **Twenty-seven of the
twenty-eight** Kshay and Vriddhi rows are identical under all four conventions,
and all 25 Pradosh rows are. So the definition-sensitivity is real and it
attaches to the **published time of a rise**, not to the rules conditioned on one
— which is a more useful thing to say than either "B" or "it doesn't matter".

#### The rule layer grew a second kind of location-awareness

§12.4 established that a weekday is applied *after* a span becomes a day at a
venue, because `fn` receives a location-blind `Sky`. That handles "Anuradha on
Sunday": one sky-side condition, two calendars, and only the date differs.

Kshay is not that shape. Whether a tithi holds no sunrise is a **different
question at each venue**, and it can be yes in Mumbai and no in New York with no
calendar involved at all. `Rule.weekdays` cannot express it — by the time `fire`
applies a weekday, the span has already been chosen. So `Rule` gains
`per_location`, and where it is set `fire` calls `fn(sky, loc)` once per venue and
never once for both.

It is not the default, and one invariant is enforced rather than trusted: a rule
declaring a `horizon/` input **must** be `per_location`, or `__post_init__`
raises. A horizon rule evaluated once would compute one venue's answer and print
it against both — and the row would still carry a location field naming the venue
it was never evaluated at, which is worse than carrying no field. The harness
attempts that construction and confirms the refusal.

The divergence is not theoretical. Across the six per-location sections the two
venues produce different spans in every case, and for Kshay and Vriddhi they
share **no tithi at all**: Mumbai has 10 Kshay bright-fortnight tithis in the span
and New York 11, with none in common. A Kshay tithi is one whose ~21-hour span
falls entirely between two consecutive sunrises, so agreement between two venues
half a world apart would be a coincidence, not a rule.

`Sky` gains `sunrises(loc_key)`, `sunsets(loc_key)` and
`horizon_crossings_within(...)`. Every one requires the venue and none has a
default. Location-blind never meant "knows no location"; it meant **supplies
none**. A condition that asks for a sunrise must say whose, and one that does not
ask never receives one.

#### What cleared, and what did not

| Section | Before | After | On what |
| --- | --- | --- | --- |
| B66, B67, B68, B69 | blocked (sunrise) | **executable** | the sunrise series |
| B64 Pradosh | blocked (sunset) | **resolved_ambiguity** | the sunset series *and* a supplied definition |
| B101 | blocked (weekday count) | **executable** | a calendar helper, no event class |
| B55's 40-ghati remark | blocked (sunrise) | **ambiguous** | the input arrived; the reading did not |

**B66–B69 cleared exactly as promised, and the promise is what makes it a
clearance rather than a guess.** §12.5 named *sunrise alone* as the remaining
input on the strength of a 28-row reproduction that was already written and
already passing. That check is unchanged and still passes: B66 9/9, B67 8/8, B68
6/6, B69 5/5, every tithi named correctly, nothing omitted and nothing extra. The
rules now fire on the same statement the check makes.

Their rows carry `source_prints_the_opening_day_of_a_multi_day_tithi`. A Vriddhi
tithi is longer than a civil day *by definition* and so always touches two, while
the source prints one — the day the tithi opens, which its 28 rows do without
exception. That is the **B75/B95** shape, not the **B74/B100** shape, and the flag
says so on the row rather than leaving a reader to infer it from a count of
extras. The distinction §12.5 drew per section is kept per section as the count
grows.

**B64 did not clear onto `executable`, and that is this batch's main finding.**
The sunset series supplies its astronomy half. Its other half is a definition the
document does not print: *Pradosh* appears twenty-two times and is explained
nowhere — Panchak's situation, one section later in the same chapter. And here the
obvious reading is not even the right one. Against the section's own 24 printed
rows:

| Reading | Reproduces |
| --- | --- |
| **Sunset in Trayodashi; first of two; the tithi's end-day if none** | **23 / 24** |
| Sunset in Trayodashi, plainly | 22 / 24 |
| Pradosh kāla — the muhūrtas after sunset | 20 / 24 |
| Trayodashi prevailing at sunrise | 10 / 24 |

Each clause is decided by a row that refutes its alternative, not by preference:

* **Sunset, not the kāla.** Krishna Trayodashi runs 12-Jun-2026 19:37:09 to
  13-Jun 16:08:14, and Mumbai sunset on 12-Jun is 19:12:22 — so the tithi opens
  25 minutes *after* that sunset, inside the pradosh kāla on any reading of its
  length. A kāla reading dates the row 12-Jun. **The section prints 13-Jun.**
* **First of two.** Shukla Trayodashi runs 28-Apr-2026 18:52:22 to 29-Apr
  19:52:07 and Mumbai sunset falls inside it on both days, at 18:56:10 and
  18:56:29. The section prints 28-Apr and not 29-Apr. It is the only two-sunset
  Trayodashi in 2026, so the clause rests on the one row that can decide it.
* **The end-day when none.** The 12-Jun Trayodashi again, read the other way: the
  section prints the day it *closes*, not the day it opens. This clause alone
  moves the reproduction from 22/24 to 23/24.

The two divergences are **held apart, because a count of differences would report
them as one thing**:

* **01-Jan-2026 Shukla is an omitted occurrence.** Trayodashi runs 01:48:28 to
  22:22:45 and sunset falls at 18:08:43 inside it. A Pradosh under every reading;
  the section's table simply begins at 16-Jan. The B74/B100 shape.
* **24-Aug-2026 is a source defect, and the document convicts itself.** The
  section prints it; that Trayodashi does not open until 25-Aug 06:21:21, so
  24-Aug's sunset falls in Dwadashi and no reading of Pradosh can reach the date.
  **B68's own Vriddhi table prints the same tithi as 25-Aug-26 Trayodashi** — the
  day this rule fires. Two of the document's pages disagree by one day about one
  tithi, exactly as p.43 and p.44 disagree about the 06-Jun Panchak start. Both
  entries are in `source_defects` with their verification.

B64's verdict — the note, carried whole — states three further conditions turning
on Vriddhi and Kshay Pradosh days. B66–B69 now make those portable. They are
deliberately **not** split in the same change that unblocked them, and the pinned
colon-prefix note says so, because splitting a verdict and unblocking a section
are two decisions and mixing them hides both.

**B101 cleared by arithmetic, which is what §12.5 said it needed.** No third event
class, no widening of `Sky`. `sky.weekdays_in_span(span, weekday, loc_key)` sits
beside `civil_days`, reads no record and asks no ephemeris, and counts a weekday
inside a window at a venue. `civil_day_span` is its inverse, so a rule that has
picked dates can hand `fire` a span without importing a timezone. `weekdays` stays
unset with `weekday_is_counted_not_filtered`, and the rows show why it must: B101
fires on all seven weekdays.

The span runs **first counted Saturday to last**, and the section's single printed
row decides that. Its fortnight opens 11-Sep-2026 08:57 and closes 26-Sep 22:19;
the row prints 12-Sep-26 to 26-Sep-26. The Till cannot separate "the last
Saturday" from "the fortnight's close" — same date — but the From can, and it is
the Saturday and not the Pratipada. A second qualifying Mumbai fortnight, 10-Oct
to 24-Oct (Saturdays on the 10th, 17th and 24th, inside a fortnight running
10-Oct 21:20 to 26-Oct 09:41), is **omitted** by the source: the B74/B100 shape
again, not a two-day artefact. §12.5 named this fortnight by its *fortnight*
bounds, 10-Oct to 26-Oct; the emitted span is its *Saturday* bounds. Both are
true and they are different quantities.

New York holds **three** such fortnights in 2026 against Mumbai's two: the one
opening 16-May 16:01 New York time opens 17-May in Mumbai and loses its first
Saturday in the crossing. One count, two answers, no astronomy in the difference —
the clearest available demonstration that the count belongs to a venue and never
to the sky.

**B55's 40-ghati remark moved from `blocked` to `ambiguous`, and the move is a
finding rather than a tidy-up.** It was blocked because the layer emitted no
sunrise. The layer now emits one at both venues, so the missing input is gone and
what remains is a choice between two readings of the source's own word: a ghati as
a fixed 24 minutes (the sense B106 uses, correctly, because there it measures a
*duration*), or as a sixtieth of the actual sunrise-to-sunrise day, which in
Mumbai runs 23h58m–24h02m and in New York 23h46m–24h14m. Forty ghati in is 16h00m
under the first and up to nine minutes away under the second. The section prints
no table of 40-ghati Panchaks — its thirteen rows are the Panchak windows
themselves, which both readings date identically — so no row of the document can
choose, and choosing would be this layer's decision. Left filed as `blocked` it
would have gone on reporting an absence this batch removed.

#### Counts

The astronomy layer moves from **2455 to 4163 records**, purely additively:

| Class | Records |
| --- | --- |
| `sunrise` | **854** (427 Mumbai, 427 New York) |
| `sunset` | **854** (427 Mumbai, 427 New York) |
| the 13 pre-existing classes | 2455, unchanged |

**Zero changed pre-existing values, proven rather than asserted.** The 2455
records of the previous build were extracted from the new file, written back
through the build's own serialiser, and hashed:
`sha256 1d9d8f93eed6ef189a03e963d6457f863c5e3c1cb7afca3f819fff3fc0ab0190` — the
§12.5 hash, byte for byte. Not one id is missing, not one field value moved, and
the only `meta` change is `record_count`.

**Deterministic.** Two consecutive builds produce a byte-identical file,
`sha256 f0ac8a2c01dd4dccbd714ba836c20e18a4667ea3665a499ce8325caff7ce69b6`.

Certainty grades move from A 2383 / B 72 to **A 2383 / B 1780** — the whole
increase is the new class, which is the arithmetic consequence of grading it B.

The rule layer, over the same 87 rules and 59 sections:

| | Before | After |
| --- | --- | --- |
| `executable` | 71 | **76** |
| `resolved_ambiguity` | 3 | **4** |
| `ambiguous` | 0 | **1** |
| `blocked` | 13 | **6** |

Firings rise from 1934 to **2197**, and all 263 new rows are the six sections:
B64 25/25 (Mumbai/New York), B66 18/18, B67 16/12, B68 12/8, B69 12/12, B101
45/60. No rule stopped firing and no new rule fires zero times.

Harness: 2026 regression 91 → **112**, 2027 astronomy 104 → **123**, node anchor
12 → 12, rule layer 77 → **94**. The new checks assert what a spot check cannot
see: that every horizon record names a venue config declares and a convention the
code actually used; that each venue gets exactly one rise and one set per civil
day *in its own zone*, with no gap and no repeat, and that the record's stated
venue date agrees with its instant; that the schema refuses a location-free record
and the rule layer refuses a location-blind horizon rule; that every per-location
condition really does differ between venues; that every sunrise a Kshay rule
counted is a sunrise the file emits; and that all three of B64's ruled clauses are
exercised, so none is dead wording in a resolution.

#### What batch 4 inherits

Unchanged from §12.5's list, less the sunrise item, which is taken. What remains
blocked is six rules over six sections, and no two wait on the same thing:

| Section | Missing |
| --- | --- |
| B10 | a continuous Mercury-vs-Venus speed comparison |
| B11 | a greatest-elongation event class |
| B19 | a benefic/malefic valence (also blocks B116) |
| B62 | first-crescent visibility — `swe.heliacal_ut` rejected on evidence in Step 3 |
| B71's note | the Moon's navamsa ingress series |
| B111 | the lunar month system (Purnimanta confirmation is an open question) |

Plus B55's remark, now `ambiguous` rather than blocked, waiting on a ruling and
not on an input. And still carried from §12.3: **B89** is unported and owed B87's
treatment, and the Vedha family — batch 4's own subject — still depends on the
speed-class thresholds `open_questions` records.

### 12.7 Batch 4 — Shar, Speed and the Vedha family · recorded 14-Sep-2026

Batch 4's subject was the Vedha family, and the batch's first result is that
**the family is still blocked, for a reason established rather than assumed.**
The speed-class calibration was the gate, so it was run first and reported
before anything was ported on top of it.

#### The calibration fails, and it fails in a way no tolerance can rescue

> **SUPERSEDED — see §12.8.** The method below is wrong and its conclusion does
> not stand. It read the speed AT the printed boundary dates instead of
> computing crossing instants, which is the one thing the kalāṃśā calibration
> never did. Mercury, Venus and Mars DO calibrate on an absolute speed
> threshold. This subsection is kept, unedited, because a retracted finding
> that quietly disappears is worse than one that is left visible with its
> correction attached.

For each of the nine Speed-and-Vedh tables (B120-B127) and every Atichari row of
the twenty-one Nakshtra Vedh tables (B128-B141), the speed the astronomy layer
emits — `astronomy.speed_deg_day`, which is on every record — was read at every
printed interior boundary. A threshold separating Fast from Normal exists only if
those two sets of values do not overlap.

They overlap on every planet that has more than one boundary:

| Planet | boundaries entering Fast/Atichari | entering Normal |
| --- | --- | --- |
| Jupiter | 0.20622, 0.22088 | −0.00128, **0.20622**, **0.22088**, 0.00082 |
| Mercury | **1.71453** … **1.77558** (n=6) | 0.08423, −0.00433, 0.07411, −0.01759, 0.06880, −0.16937, **1.71453** … **1.77558** |
| Venus | 1.22398 | **1.22398**, 0.02045, −0.01006 |
| Saturn | 0.08693, 0.09178 | **0.09178**, **0.08693**, 0.00003, −0.00046 |
| Mars | 0.65965 | 0.65829 |

Jupiter's Fast boundaries fall *inside* the range its Normal boundaries span.
Venus has a single Fast boundary and it is the highest Normal boundary as well.
Mercury is decisive: **1.77558 enters Normal and 1.71453 enters Fast**, so the
Normal set strictly contains the Fast set. There is no cut.

**This is not a precision failure and must not be treated as one.** A scatters
that overlap cannot be separated by any value however wide the tolerance; the
`range / acceleration` figure the project uses for `precision_days` would print
32.0 days for Jupiter and 25.1 for Mercury, but printing a number there would
imply a threshold exists and is merely imprecise. It does not exist. Widening a
tolerance to absorb this is exactly the move that would manufacture a class
boundary the source does not have.

**What does survive the same test.** Retrograde/Direct is the sign of the same
emitted quantity and it reproduces the source's own periods, station for
station: Jupiter prints 11-Mar-26 and the engine puts the station at 11-Mar-26;
Saturn 27-Jul-26 against 27-Jul-26; Neptune 07-Jul-26 against 07-Jul-26; Pluto
06-May-26 against 06-May-26; Herschel 10-Sep-26 against 11-Sep-26. Mercury is
the documented outlier — its printed retrograde boundaries sit +6, +1, +6, −7,
+3 and +8 days from the computed stations, which is the 2–7 day lag
`mercury_shar_lag` already records and not a new defect.

So **two of the classes are recoverable and one is not.** A rule may condition
on retrograde-or-direct today. It may not condition on Fast-or-Normal, and that
is what blocks the Vedha family: both the Speed-and-Vedh tables and the Nakshtra
Vedh tables select the direction branch from the class the source printed, so a
port needs the class at an arbitrary 2027 instant. The family is registered
blocked on `speed_class_thresholds`, not approximated around it.

#### Atichari and Fast are one class under two names — verified, not inferred

> **REFINED — see §12.8.** The periods below are correct and the conclusion
> stands, but "two names for one class" is the weaker statement. §12.8 shows
> Atichari is the *nakshatra-residency frame's* label for the period the speed
> frame calls Fast, which is why every Atichari row begins and ends on a
> nakshatra ingress.

Settled by comparing the boundaries directly rather than by reading the words:

| Planet | "Fast" in the Speed-and-Vedh table | "Atichari" in the Nakshtra Vedh table |
| --- | --- | --- |
| Mars | … → 14-Aug-26 | … → 15-Aug-26 |
| Mercury | 28-Jan → 07-Feb | 28-Jan → 07-Feb |
| Mercury | 27-Apr → 31-May | 27-Apr → 31-May |
| Mercury | 12-Aug → 08-Sep | 12-Aug → 08-Sep |
| Venus | … → 13-Apr-26 | … → 12-Apr-26 |
| Jupiter | 19-Jun → 06-Aug | 18-Jun → 06-Aug |
| Saturn | 26-Jan → 30-May | 25-Jan → 30-May |

The periods are the same periods. Every difference is one day at a start
boundary, where one table names the last day of the old state and the other the
first day of the new — a convention, not a class. So this is a **vocabulary
finding**: one class, two names, and no second threshold to derive. That matters
because the alternative reading would have doubled the calibration problem.

#### Vedha direction is a correlation at 109/111, not a derivation

The proposed rule — Fast/Atichari → Left, Normal → Front, Retrograde → Right —
was checked against every directional row of all thirteen per-planet Nakshtra
Vedh tables. **109 of 111 agree. Two do not, and both are in B136**, Saturn's
own table, on rows whose Speed column reads Atichari while the filled cell is
Right: Uttara Bhadrapada from 25-Jan-26 and Revati from 17-May-26. B124,
Saturn's Speed-and-Vedh table, prints **Fast/Left** for 26-Jan to 30-May — the
same window. So the source contradicts itself about Saturn there, and the two
tables cannot be reconciled from the page.

**A single exception demotes a derivation to a correlation, and there are two.**
Any rule that reads a direction off a speed class is reading a regularity the
source does not keep, and must carry that on the row.

The direction cells are not an arithmetic wheel either. No constant offset
reproduces any table: within B132 alone the Front offset ranges over
8, 10, 12, 14, 16, 18, 20 and Left over 1, 3, 5, 7, 9, 11, 13 in the 28-name
scheme. What the tables *are* is a per-planet lookup — own-nakshatra → target —
with exactly two exceptions (again B136's Saturn rows). A lookup cannot be
evaluated on a nakshatra the source never printed, which is a second, independent
reason the Vedha family is not a formula to be ported. Both facts are recorded in
`config/conventions.yaml` under `vedha_direction`.

#### Shar is settled, and it is the latitude and not the declination

The remainder's first item turned out to be a convention that had never been
pinned. B118 prints North/South periods per planet and B119 prints the Moon's
27-row alternation. **Shar is the sign of the ecliptic latitude**, settled by
reproducing the source's own dates the way the ayanamsha and the node were:

* B118 Mars prints **one** change and the latitude has **one** crossing,
  25-Jul-26 05:44 against the printed 26-Jul-26 — 0.76 d, inside the table's
  date-only resolution;
* B118 Venus prints three interior ends and the latitude has three crossings at
  **0.54, 0.01 and 0.85 d**;
* B119's 27 printed ends are reproduced **26/27** by the latitude sign, worst
  1.98 d, at the 18-Jun-26 node crossing where the latitude is slowest.

The competing reading — declination sign — is **rejected on the source's own
numbers**: Mars's declination crosses on 12-Apr-26 while B118 prints South until
26-Jul-26, a **104-day** disagreement, and Saturn's crosses on 27-Mar-26 while
B118 prints South for the entire year. Against B119 it reproduces **0/27**, every
miss 1.5–3.7 d and all in the same direction — a different quantity's phase, not
a tolerance. The month's ~13.6-day alternation is the latitude period, not the
declination period, which is what makes the reading checkable at all.

**What it costs, on the record.** Latitude is emitted on every record but has no
ingress series, so a zero-crossing is known only to the gap between the two
records that straddle it. For the Moon that gap is 0.23 d median and 1.03 d
worst; for Mercury 1.8 d, Venus 2.7 d; but **Pluto has four records in the span
and its gap runs to 163 days**, so a Pluto Shar change is dated to within months.
Grade **B**, for exactly the reason a sunrise is B: the quantity is exact and the
instant is definition-sensitive. Every firing carries
`boundary_uncertain_to_the_record_gap`, and both rules emit **one row per
change**, which is what the sections tabulate — B118 prints 22 rows for seven
bodies across a year, not 250 days of a North period.

Ported: `b118_shar_direction` (12 changes in 2027) and
`b119_moon_shar_parivartan` (27). Both fire with `verdict_text = None`, because
neither section prints a market verdict and one is not invented for them.

#### The reference tables map to classes the layer already emits

Thirty-two catalogue-B sections are renderings of ingress series rather than
rules in their own right: ten "Journey of <planet>" (sign ingresses), seven
"<planet> Motion" (stations), seven "<planet> Constellation (Nakshtra)"
(nakshatra ingresses) and eight "<planet> in Navmansh (D9)" (navamsa ingresses).
Confirmed as a mapping — each carries a table whose columns are that class's own
facts — so porting them is confirmation and not re-derivation. Two exceptions
are recorded rather than smoothed: **B49 "Journey of Pluto" carries no table at
all**, and the Constellation tables head their nakshatra column "Constellation",
with B28 and B45 varying the remaining columns from their siblings.

#### Four source defects this batch found, none of them tolerances

Each was found by reproducing the section's own 2026 table from the engine and
each is recorded rather than absorbed. Three are of a kind the project has met
before; the first is not.

**B81 is labelled for the wrong planet.** "Saturn and Mercury Both Retrograde —
Bullish" prints one 2026 row, 03-Oct-26 12:47 to 14-Nov-26 05:59. Saturn and
Mercury are **never** both retrograde in that window: Saturn's retrograde does
not begin until 27-Jul-26 and Mercury's 03-Oct retrograde does not begin until
24-Oct, so the true Saturn∩Mercury window in 2026 is 24-Oct-26 12:42 to
13-Nov-26 21:24 — **503.9 hours** from the printed start. The printed row is
**Venus's** retrograde window to within four minutes: her R station is 03-Oct-26
12:43 and her D station 14-Nov-26 05:59. So B81's row is not a Saturn-Mercury
window at all. The corrected window is the row B83 prints, because in 2026 both
Venus's and Saturn's retrograde stretches happen to contain Mercury's — which is
exactly why the error would never show up as an anomaly in the tables and took an
independent computation to see. Ported as the exact condition with the row
flagged; nothing widened.

**B82 reproduces only from the carry-in.** Its 26-Feb-26 window sits at the end
of a Jupiter retrograde that began 11-Nov-2025, before the generated span. A
2026-only station scan cannot see it and reports no window at all. The batch
recomputes from mid-2025, which is what makes B82 checkable — 12:17 → 09:23
against a printed 12:19 → 09:01.

**B114's printed end matches nothing in the sky.** Mercury's first 2026 visit to
Purva Bhadrapada starts when the table says (−10 min), but the printed end
14-Mar-26 14:20 has Mercury at 316.41°, four days after it left the nakshatra and
with no ingress within five hours. Mercury's second 2026 visit, 01-Apr 20:12 to
13-Apr 14:22, is printed nowhere at all.

**B115's condition is narrower than its printed table.** The title states the
union — "Either Sun or Venus in Shatbhisha" — and the rule fires the union, which
in 2027 runs to 05-Mar 00:54. But both printed rows are **alone** sub-windows,
verified to within two minutes: the Venus row ends at the Sun's Shatabhisha
ingress and the Sun row begins at Venus's exit. The table's construction is
recorded on the row rather than adopted as the condition, because "alone" is not
a word the title uses.

#### What the remainder added

Ported in this batch, besides Shar: the apsides **B57/B58** (the condition is the
apogee or perigee itself, *not* the 406,000/360,000 km in the notes — the
section's own table is the evidence, printing 13 apogees of which only 3 clear
the stated threshold), **B59** perihelion and aphelion, **B77** Kaal Sarp Yog,
the retrograde pairs **B81/B82/B83**, and the residency singles **B88, B91, B92,
B94, B98, B99, B107, B113, B114, B115** and **B117**. **B89** is delivered with
B87's treatment, as owed from §12.3: the condition fires on Mars in Chitra
13-Aug to 03-Sep-2027 while the Rohini-scoped verdict stays silent, and both
counts are pinned by name so the silence cannot read as an absence.

**B70 Big Volatile is ported as a recorded absence.** The section's date cells
hold 51 dates and its entire statement of method is that they "have been sorted
on multiple parameters", with none named and no weights given. Four candidate discriminators were tested and rejected, and
all 51 dates carry at least one major configuration, which is what makes the list
over-determined: a rule fitted to those 51 dates would reproduce them and predict
nothing. So the rule is registered `blocked` with `source_selection_rule` as the
named missing input and **certainty C**, emits nothing, and its zero is pinned by
name. No candidate list is emitted — a reconstruction here would be this layer's
inference wearing the page's authority.

**B63 Hemisphere is blocked on two independent counts**, and the record keeps
them apart: the equinox it names is a **tropical** solar longitude, and no
ingress series gives one — the sidereal longitude plus the per-record
`ayanamsha_deg` reconstructs it only at the instants the layer happens to sample
the Sun, whose ingresses mark whole signs, nakshatras and navamsas. Measured
anyway, daily-sample interpolation reproduces the equinox to about 5 minutes and
a navamsa bracket to about 3.6 hours, both inside the source's own ±2/3 days, so
this is a licence question and not a numerical one. The second count is the
source's own words: "range of the Hemisphere" never names the range's centre and
"broken on both side" never says whether the range is prices or the six-day
window. Three competing readings are carried in `ambiguity` and none is chosen.
**B117** joins B19 on the benefic/malefic valence, which is the same missing
input and not a new one.

### 12.8 §12.7's calibration is RETRACTED and replaced · recorded 14-Sep-2026

§12.7 reported that no Fast/Normal speed threshold exists, and that the Vedha
families were therefore blocked. **Both halves were wrong**, and the error was in
the method, not in the source.

#### The methodological error

§12.7 read `speed_deg_day` **at** each printed boundary date and asked whether
the Fast and Normal *samples* separate. A printed boundary is a DAY, not an
instant. Near a speed maximum the entire above-threshold window can be a few days
wide — Mercury's February maximum is 1.773164 against a threshold near 1.745 — so
an arbitrary sample inside the boundary day lands on whichever side the sample
instant happens to fall, and the two sets "overlap" whether or not a clean
threshold exists. **Mercury was called decisive on exactly this artefact**, and
the artefacts are the same size as the effect.

The kalāṃśā calibration never did this: it proposed a threshold, computed the
instants the body **crosses** it, and scored those against the printed dates.
Redone that way, the result inverts.

Two smaller errors in the first attempt at the correction are also on record,
because each changed the answer: it scored each row's END date as well as its
START (so every boundary was counted twice and the fit demanded twelve dates
where there are six), and it treated a `Retrograde -> Normal` transition as a
Fast/Normal boundary — that transition is a **station**, and fitting it with a
speed threshold would let a bad threshold borrow the stations' credit.

#### The thresholds, recomputed

For each printed boundary, the method now computes the interval of threshold
values T that could place a **crossing** on that date (±1 day), restricted to the
correct branch: a rising crossing into a speed maximum for `Normal -> Fast`, a
falling crossing out of one for `Fast -> Normal`. A planet has a threshold iff
those intervals share a point.

| Planet | Threshold (interval) | Tolerance needed | `precision_days` |
| --- | --- | --- | --- |
| **Mercury** | **1.7449** (1.743780 – 1.746038) | ±1.1 d | 0.08 |
| **Venus** | **1.2240** (1.223368 – 1.224595) | ±1.0 d | 2.00 |
| **Mars** | **0.6583** (0.656927 – 0.659648) | ±1.0 d | 2.00 |
| Jupiter | **none** — boundaries 0.013750 apart | ~4.8 d | — |
| Saturn | **none** — boundaries 0.002594 apart | ±2.2 d, window 0.000125 wide | — |

The thresholds are **absolute and planet-specific**: Mercury's 1.7449 and Mars's
0.6583 are in the same units and differ by 2.6×. They are **not** fractions of
each planet's maximum — that was tested and rejected, because it forces each Fast
window's two crossings to be equidistant from the speed maximum and Mars's are
not (rising 39 days before its maximum, falling 98 days after).

**The tolerance each planet needs is part of the finding.** Mercury misses the
1.0-day scoring by 6 × 10⁻⁵ deg/day, i.e. by 1.8 days — so an earlier sweep at
±1.0 d was right to report "5/6" and wrong to conclude that no threshold exists.
Saturn is the mirror case: a T *does* exist at ±2.2 days, but the feasible window
is then 0.000125 wide, a sliver fitted to a 2.2-day rounding. That is not a
threshold, and widening the tolerance to reach it is the move §12.7 correctly
refused and this section refuses too, for the opposite conclusion.

#### Jupiter and Saturn: a slow-planet doctrine, not a failed threshold

Their two boundaries have no common threshold, and the reason is structural: for
Jupiter the Fast period is 39 days on the rising side and 8 days on the falling
side of its maximum, which no level can produce. The source carries a section for
exactly this — **B30, "Demoted and Shadow Speed of Saturn" p.26** — and reading
it settles what the slow planets are doing:

> "Saturn crosses 20'31" on 15th March 2027. Saturn will be called in Demoted or
> Shadow Speed from 11th Dec 2026 to 15th March 2027 when it crosses 20'31""

**B30 defines its interval by LONGITUDE, not by speed.** Verified against the
engine: Saturn is at 20.508963° of Pisces on 27-Jul-2026 and 20.507990° on
15-Mar-2027 — 20°31′ to the arcminute, as the table prints — and at 13.694991°
(13°42′, the Direct row's printed value) on 11-Dec-2026. So the doctrine exists
and is reproducible, but **it supplies a longitude band, not a speed level**, so
it does not give Jupiter or Saturn a threshold.

**Therefore Jupiter and Saturn stay blocked, and the missing input is named as a
slow-planet speed doctrine — not as a failed threshold.** That is a different
block with a different remedy: a threshold would need a better number, a doctrine
needs a rule the source has not stated.

#### Consequence 1 — Atichari and Fast: the earlier finding was too weak

§12.7 said the two are one class under two names, arguing from the printed date
ranges. That argument survives but was the weak form. With the threshold in hand
the strong form is available: the **Fast** periods in the Speed-and-Vedh tables
and the **Atichari** periods in the Nakshtra Vedh tables are the same physical
above-threshold windows of the same T. For Mercury all three Fast windows are the
three above-threshold windows, and each Atichari period is a nakshatra-residency
sub-window inside one.

One correction follows. **Atichari is not a speed class name at all.** Every
Atichari row in B132, B133 and B134 begins and ends on a **nakshatra ingress** —
Venus's eleven Atichari rows run 01-Jan→10-Jan→18-Jan→…→12-Apr, ending exactly
when Venus leaves Revati on 12-Apr-26 14:22, and Mars's fifteen Atichari rows end
on 15-Aug-26, the nakshatra boundary the table itself prints. So **Atichari is
the nakshatra-residency frame's label for the same period that the speed frame
calls Fast**: one period, two frames, and the vocabulary finding stands — but it
is a claim about two framings, not about two names for one class.

#### Consequence 2 — Vedha direction: the count is unchanged, the reason is not

The 109/111 count stands, but reporting it as a single number buried the fact
that matters. Broken out per planet:

| Planet | Table | Match | Mismatch |
| --- | --- | --- | --- |
| Mars | B132 | 21 | 0 |
| Mercury | B133 | 45 | 0 |
| Venus | B134 | 30 | 0 |
| Jupiter | B135 | 7 | 0 |
| **Saturn** | **B136** | **6** | **2** |

**The rule holds without exception on every planet whose speed class is defined,
and both exceptions are Saturn rows.** The hypothesis that the exceptions were a
consequence of applying the wrong speed class is therefore half right: they are
confined to the one planet that has no speed threshold, so a wrong class cannot
be ruled out as their cause — but they are not explained away either, and two
printed rows still contradict the rule. It remains a **correlation at 109/111**,
and the honest refinement is that the counterexamples are confined to the planet
that is anomalous twice over.

**What the two rows actually say**, re-derived from the 28-name wheel rather than
asserted:

| B136 row | Class | Cell | Target | Offset |
| --- | --- | --- | --- | --- |
| Uttara Bhadrapada | Atichari | Right | Ardra | +7 |
| Revati | Atichari | Right | Mrigashira | +5 |

The Normal rows of that same table both use offset +14 and the Retrograde rows
use +19 and +21 — so every class in B136 has a consistent offset **except
Atichari, whose two rows use different offsets and fill the Right cell when the
class→cell rule says Left**. That is the signature of a slow-planet anomaly
rather than of an isolated typo, which is consistent with B30 existing at all.

#### What is now unblocked, and what that port still needs

The Vedha families are **unblocked for Mercury, Venus and Mars** — their speed
class is computable at an arbitrary instant (`Retrograde` when speed < 0, `Fast`
when speed ≥ T, `Normal` otherwise). They are **still blocked for Jupiter and
Saturn** on the slow-planet doctrine.

**No Vedha family has been ported, because a second gap remains and it is not in
the rule layer.** The astronomy layer emits speed on every record but emits **no
crossing of a speed level**, so a rule cannot build Fast/Normal spans from it —
the same situation the tithi, yoga and sunrise series were in before §12.5 and
§12.6 added them. That is new Step-3 work. Porting a Vedha rule by sampling speed
at other events' instants, or by approximating the boundaries, is exactly what
§12.7 and this section both refuse.


