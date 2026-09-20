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
| Last updated | 14-Sep-2026 — §12.9, batch 5 (speed-crossing series, Vedha port) |
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



### 12.9 Batch 5 — the speed-crossing series and the Vedha port · recorded 14-Sep-2026

> **PARTLY SUPERSEDED — see §12.10.** The speed-crossing series stands, and so
> does Mercury's port. **Mars's and Venus's ports are withdrawn**: each planet
> crosses its level exactly once in 2026, so those two calibrations solved one
> equation in one unknown and are single-point fits rather than calibrations. The
> 103/103 domain figure below is replaced by 52/52, and the claim here that all
> fifteen of Mars's Atichari rows disagree with the computed class is corrected
> there to 20 of 21 agreeing, the single disagreement being the boundary day.

The Step-3 series that §12.8 said was owed, and the port it unblocks.

#### The series, and the bug it makes structurally impossible

A new astronomy event class, ``speed_crossing``, emitted by ``build_2027.py`` from
``finastro/ephem.py`` under Step 3's discipline. Crossings are bisected to the
second like every other crossing in the layer. It carries, on **each record**:

* ``speed_threshold`` and ``speed_threshold_interval`` — the level used AND the
  interval of levels that also reproduce the source's printed boundaries, so the
  calibration is auditable from the output alone rather than from config;
* ``speed_crossing_kind`` (``threshold``) and ``speed_crossing_direction``
  (``into_fast`` / ``out_of_fast``);
* certainty **B** with the calibrated ``precision_days`` — Mercury 0.08, Venus
  2.00, Mars 2.00.

**Retrograde boundaries are stations, and that is now structural.** The second of
the two bugs §12.8 recorded was treating a ``Retrograde -> Normal`` transition as
a Fast/Normal boundary. It can no longer happen, for two independent reasons: the
two kinds are emitted from **separate scans at their own levels**, and the
station records stay in the existing ``station`` class rather than being
re-expressed as ``speed_crossing``. A threshold crossing must also clear a
**dead band** of 0.2 deg/day, which no retrograde loop on any body this series
covers reaches — so a loop arc dipping to a small positive maximum cannot be
interpolated into a spurious Fast boundary. The harness checks both properties,
including that no threshold crossing sits inside the dead band.

**Jupiter, Saturn and the outers emit no threshold records at all.** Their missing
input is a slow-planet speed doctrine, not a threshold, and a record for them
would be an invented level. B121 and B124 are registered ``blocked`` with that
named.

#### Validated against the printed boundaries before any rule read it

| Body | Printed Fast/Normal boundary | Crossing emitted | Offset |
| --- | --- | --- | --- |
| Venus | 13-Apr-26 | 13-Apr-26 00:07 | **+0.12 h** |
| Mars | 15-Aug-26 | 15-Aug-26 00:05 | **+0.09 h** |
| Mercury | 27-Apr-26 | 27-Apr-26 01:05 | +1.09 h |
| Mercury | 12-Aug-26 | 12-Aug-26 12:07 | +12.12 h |
| Mercury | 31-May-26 | 31-May-26 16:01 | +16.03 h |
| Mercury | 28-Jan-26 | 28-Jan-26 23:00 | +23.01 h |
| Mercury | 08-Feb-26 | 08-Feb-26 00:37 | +24.62 h |

The station series reproduces all six of Mercury's printed Retrograde boundaries
within **1.0 day** and Venus's two within **0.6 day**. Mercury's two February
Fast boundaries are ~1 day adrift at **every** level in its interval (24.62 h at
the midpoint, 22.9 h at the top of the interval, never below 23.0 h) — so that
residual is the source's own imprecision, not a calibration error, and it is
recorded rather than tuned away.

#### Determinism and blast radius

Rebuilding twice gives a byte-identical file. The build adds **7 records** to the
4163 and **changes none of them**: every pre-existing record was compared field by
field against the pre-batch backup and is identical. New artifact hash
``9ea5ff29d77689261bbe0a17596c805a148c5a431526765c1166886363625e73``.

#### The Vedha port: what it clears, and what it does not

Six sections ported: **B120, B122, B123** (Speed and Vedh) and **B132, B133,
B134** (Nakshtra Vedh), for Mercury, Venus and Mars. B121 and B124 stay blocked on
the slow-planet doctrine.

The direction rule is carried as a **flag** on every row, not as law, with both
numbers on record: **109/111 overall is the honest headline** because Saturn is
unresolved, and **103/103 within the domain where a speed class is defined** —
Mars 21/21, Mercury 45/45, Venus 30/30, Jupiter 7/7. Saturn's 6/8 is an
application of the rule *outside* its domain rather than a counterexample within
it, on a table whose two Atichari rows also disagree with each other. **The test
that decides** is named in config: if the slow-planet doctrine is ever settled and
Saturn's class becomes computable, Saturn's two rows become testable and the label
moves from correlation to derivation.

**The targets are a transcription, and the port says so.** Each table's target
column is a per-planet lookup on the planet's own nakshatra; no constant offset
reproduces any table (within B132 the Left offset runs 1,3,5,7,9,11,13 in the
28-name scheme). All **96 printed rows** resolve to their own target through the
wheels — Mars 21/21, Mercury 45/45, Venus 30/30.

**Where the source does not answer, the row says so instead of guessing.** A
wheel entry belongs to the class its own table printed, so an entry is refused
when the 2027 residency's computed class differs, with
``target_unavailable_because`` naming the mismatch. That is not defensive
padding: **Mars's table labels all fifteen of its Atichari rows for periods the
calibrated threshold calls Normal** — Mars runs 0.62–0.72 deg/day against a Fast
level of 0.6583 — so Mars's two tables do not agree about what Atichari means for
Mars, and reconciling them would mean choosing which of its own tables to
believe. Coverage after the refusal: Mercury **66 of 68** rows carry a target,
Mars 12 of 28, Venus 14 of 66.

#### Atichari is a frame finding, not a vocabulary one

Promoted out of the speed section into its own config block,
``frame_findings.atichari_is_a_residency_frame_label``. **Atichari is the
nakshatra-residency frame's label for the period the speed frame calls Fast** —
one period, two framings. The evidence is that every Atichari row in B132/B133/
B134 opens and closes on a **nakshatra ingress** (Venus's eleven run to
12-Apr-26 14:22, exactly when she leaves Revati), none is bounded by a speed
value, and the speed frame's calibrated crossings land on the same starts.

It is recorded as the **same shape as the rashi/navamsa dignity split** — the same
object carrying different labels in two frames, carried under distinct names
rather than collapsed — and filed where the next two-frame question will find it,
not buried under speed classes. The counter-evidence is recorded in the same
entry: Mars's fifteen Atichari rows show the two frames' labels do **not** reduce
to one another, which is precisely why it is a frame finding and not an equation.


### 12.10 Mars and Venus withdrawn: single-point fits are not calibrations · recorded 14-Sep-2026

§12.9 ported the Vedha family for Mercury, Venus and Mars and reported their
thresholds as calibrated. **Two of those three thresholds are not calibrations**,
and the ports that rested on them are withdrawn here. Mercury stands.

#### The structural reason

The calibration fits one number per planet to the printed Fast/Normal boundaries.
Whether that number is *evidence* depends on how many independent boundaries
constrain it:

| Planet | Crossings of its level in 2026 | Printed boundaries constraining it | Degrees of freedom |
| --- | --- | --- | --- |
| **Mercury** | **6** | 6 | overdetermined — it held |
| Venus | **1** | 1 | 0 |
| Mars | **1** | 1 | 0 |

Mars's speed runs monotonically from a single maximum (0.787915 on 01-Mar-26)
down to 0.116865 by year end, crossing 0.658287 **once**; Venus's crosses
1.223981 **once**, on its way down from 1.258240. So each calibration solved
**one equation in one unknown**. The "feasible interval" reported in §12.8 for
those two is not a measurement spread at all — it is just the speed's own change
across the ±1 day scoring window. No other printed row in the year can falsify
either number.

**A number that cannot fail is not evidence.** Both thresholds are recorded as
**single-point fits**, kept in config with `degrees_of_freedom: 0` and
`status: withdrawn_single_point_fit`, so that a later year supplying a second
crossing can *test* them rather than re-derive them. They are not "wrong"; they
are unfalsifiable, which for this project is a different and disqualifying thing.

Three independent measurements of the same structural fact agree, which is why
this is a withdrawal and not a judgement call:

| | Mercury | Mars | Venus |
| --- | --- | --- | --- |
| crossings in 2026 | **6** | 1 | 1 |
| wheel coverage under the port | **97%** | 43% | 21% |
| printed rows agreeing with the computed class | **45/45** | 20/21 | 30/30 |

#### Correcting §12.9's Mars claim

§12.9 stated that **all fifteen** of Mars's Atichari rows disagreed with the
computed class. That was wrong, and the corrected per-row breakdown is:

| Printed class | Rows | Agree with threshold | Disagree |
| --- | --- | --- | --- |
| Atichari | 15 | **15** | 0 |
| Normal | 6 | 5 | **1** |

Mars runs 0.766–0.788 deg/day through January (Purva Shada, Uttra Shada,
Abhijeet, Shravana) — **above** 0.658287, so the threshold calls those rows Fast
and the tables agree. It stays above the level until the August crossing, so every
one of the fifteen Atichari rows agrees.

**The single disagreement is the boundary row itself**: Ardra, printed `Normal`
from 15-Aug-26, where the crossing falls at 15-Aug-26 00:05 IST — the same civil
day. So the finding is **not** "Mars's tables contradict each other". It is the
much narrower: *Mars's two tables agree on 20 of 21 rows, and disagree only about
which side of a boundary day a class belongs on.*

#### What is withdrawn, and what stays

**Withdrawn** (now `blocked`, missing input *a threshold constrained by more than
one crossing*): `b120_mars_speed_and_vedh`, `b132_mars_nakshatra_vedh`,
`b123_venus_speed_and_vedh`, `b134_venus_nakshatra_vedh`. Four rules.

**Kept**: `b122_mercury_speed_and_vedh` and `b133_mercury_nakshatra_vedh`. Mercury
is the only planet whose threshold is overdetermined, and **that — not a larger
row count — is what distinguishes it**. Mercury's table also happens to be the
fullest (45 rows, 38 wheel keys), but Venus's 30 rows and Mars's 21 are ample;
what they lack is a *second crossing*, and no amount of rows substitutes for one.
The Mars and Venus **wheel transcriptions are kept in the module** even though
their ports are withdrawn, so a future year can test them without re-transcribing
them. All 96 printed rows still resolve to their own target through the wheels.

**The astronomy series still emits Mars's and Venus's crossings**, because a
crossing is a fact about the sky and deleting a measurement to punish a bad
inference would lose data. What changed is the **grade**: Mercury's records stay
certainty **B**, while Mars's and Venus's are now **C** — the grade this project
reserves for depending on an undocumented source rule — each carrying
`single_point_fit_zero_degrees_of_freedom`. The harness checks the grade per body
and that the reason travels on the record.

#### The honest domain-restricted Vedha figure is 52/52

§12.9 reported **103/103** within "the domain where a class is defined". That
counted Mars's 21/21 and Venus's 30/30, whose classes were derived from
single-point fits — so they were **not independent confirmations** of the
direction rule; they were guaranteed to fit. The honest figure counts only the
planets whose class does not rest on an unfalsifiable threshold:

| | Match | Mismatch |
| --- | --- | --- |
| Mercury | 45 | 0 |
| Jupiter | 7 | 0 |
| **Total** | **52** | **0** |

The **overall label remains correlation** while Saturn is unresolved, and the
superseded 103/103 is recorded in config rather than deleted, with the note that
it counted planets outside the honest domain.

One overdetermined calibration that survived six independent constraints is worth
more than three thresholds where two were guaranteed to fit.


### 12.11 Two grounds for C · recorded 14-Sep-2026

An earlier change graded Mars's and Venus's crossings **C** on the ground that C
is "depends on an undocumented source rule". **That was the wrong ground.** The
rule is documented and the method is sound; what is missing is evidence for a
*parameter*. Calling a single-point fit "an undocumented source rule" sends a
reader hunting for a page that does not exist.

So C now has **two independent grounds**, and the invariant is enforced in both
layers rather than left to convention:

| Ground | What is missing | Remedy |
| --- | --- | --- |
| `undocumented_source_rule` | the rule itself — B70's "sorted on multiple parameters", the Paap Kartari valence, Saturn's demotion | recover the rule |
| `parameter_not_constrained_by_evidence` | the method is sound; a fitted parameter has fewer constraints than free parameters — Mars's and Venus's Fast levels | a year supplying a second crossing |

**`events.QA` refuses a C without a ground, and refuses a ground on anything that
is not C.** `rules.base.Rule` carries the same pair of checks, so the rule layer
cannot state a bare C either. Both harnesses assert it across every record and
every rule. **Twenty-seven rules declare a ground: four on the parameter ground**
— Mars's and Venus's speed and nakshatra tables, the four withdrawn in §12.10 —
**and twenty-three on the undocumented one**, which is B70, B63, B111, B116, B30,
B5, B6, the four slow-planet Vedha tables, and the twelve Vedha sections no
calibration reaches.

The distinction is the whole point of the example that prompted it: **a station is
frame-free** — it is where the longitude is stationary, and no parameter stands
between the sky and the instant — while **a crossing of 0.6583 deg/day is only as
meaningful as 0.6583 is.** Same Grade letter, different defect, different remedy.

### 12.12 Batch 6: full coverage, and the status page · recorded 14-Sep-2026

The remaining 49 sections, and the one-page summary that answers coverage
without reading the config.

#### The reference tables: 32 sections, ported as views

"Journey of <planet>" (10), "<planet> Motion" (7), "<planet> Constellation
(Nakshtra)" (7) and "<planet> in Navmansh (D9)" (8) are **views of series the
astronomy layer already emits**. Each now fires one row per record of its series,
with `verdict_text = None`, which is correct for a reference table and not a gap:
they state where a body was and when it moved, and nothing about the market.

Three things had to be got right and each was found by the port failing:

* **The carried-in row.** Every one of these tables opens with a "Start of the
  year" row — the state before the first movement. Without it, a body that does
  not cross the frame inside the span renders as a **blank table**. That is not
  hypothetical: Uranus, Neptune and Pluto move too slowly, and the nodes barely
  move. The row is read from the layer (the first crossing's own `_from` field,
  or the nearest record's position where there is no crossing) and never from the
  engine.
* **The layer is right and the source is old about one name.** The document says
  "Herschel" throughout; the layer emits `Uranus`. A bridge carries the source's
  spelling, and its absence rendered four Herschel views blank — the same
  silent-failure shape as a body matching no record.
* **Four sections are genuinely quiet, not broken.** Rahu, Ketu, and Pluto's
  nakshatra and navamsa tables each have exactly **one** crossing in the whole
  span, in **December 2026**, before calendar 2027. Their 2027 content is the
  carried-in state alone. Pinned by name as orbital-period zeros, and the check
  that separates that from a porting error is that each still emits its row.

#### B2, and a lord table the document witnesses itself

B2 prints 28 rows — one per sidereal day of the Sun's circuit, closing on Purva
Shada — each carrying its nakshatra **and that nakshatra's lord**. So the
document is its own witness for the lord sequence, and the map is **sliced** from
those rows rather than recalled: nine lords cycling 3,3,3,3,3,3,3,3,3 over the 27
nakshatras. A recalled Vimshottari sequence would have been an unchecked
transcription.

The **Relationship** column is not rendered. It states an aspect between the Sun
and the nakshatra's lord — Conjunction, Sextile, Trine, Semi-Sextile, Opposition,
Own — and the source never says whether it measures the exact aspect or one under
an orb. Each row carries `relationship = None` with that reason rather than a
value computed from an unstated convention.

#### B5, B6 and B30

**B5 and B6 are blocked on the same absence**: the layer emits no Mars D9 ingress
series because the source prints no Mars D9 table, so a residency over a D9
position cannot be bounded. B5 was already recorded in config's
`rule_layer_pending`; both are now registered so the section has a status rather
than an omission — the more so because B5 and B6 sit between two Navmansh tables
and look like their neighbours.

**B30 "Demoted and Shadow Speed of Saturn" p.26 is blocked on a rule, not on its
interval.** Its two printed values are **verified to the arcminute**: the engine
puts Saturn at 20.508963° of Pisces on 27-Jul-2026 and 20.507990° on 15-Mar-2027,
both 20°31′ as the table prints, and at 13.694991° on 11-Dec-2026, the Direct
row's value. What the section never states is **what makes a planet Demoted or
Shadow**: it names the band and the two dates and no condition. So the interval is
reproducible for one year and the rule generating it in another cannot be stated.

#### The remaining Vedha sections, and one honest scope gap

B125–B127 and B131–B141 are the vedha tables for bodies with no calibrated level,
and B128 keys on the Moon. All are registered `blocked` with the input named. One
of them is a **scope** gap rather than an input gap and says so: **B130's key
(Mercury's class) is calibrated and overdetermined**, so the section is portable
in principle and was not ported in this batch. Registered blocked rather than
omitted, so the gap reads as scope and not as a missing input.

#### Full coverage

**141 of 141 sections now carry a status**: 171 rules, 132 executable, 5 resolved,
33 blocked, 1 ambiguous, 3,557 dated rows in 2027. `build/RULE_LAYER_STATUS.md`
is generated from the live registry, so it cannot drift from what the layer does.

**What remains to a calendar is two mechanical steps**, and this batch is what
makes them mechanical: the **verdict layer** applies `evidence_source` ×
`construction` per instrument on a venue's civil day, and then the render. Nothing
in the condition layer is a forecast or investment advice.

### 12.13 The verdict layer · recorded 14-Sep-2026

The condition layer emits ~3,500 dated rows saying WHEN a rule's condition holds,
per location. The verdict layer turns each into a row per INSTRUMENT on that
instrument's venue civil day, carrying the two canonical axes, the derived tier,
a claim tag and a confidence. `finastro/verdicts.py`.

#### It authors no verdict

The rule package's own docstring says a verdict record is blocked on
`open_questions.label_scheme_signoff`, and that entry is **still open** in config.
The instruction this layer was built against resolves that question for this layer
alone, and in the most conservative direction available: **verdict text is ported
verbatim from the source or absent.** Nothing here infers Bullish or Bearish from
a rulership.

So `construction` is `printed` for the rules that print a verdict and `None` for
those that do not, and **there is no `derived` verdict anywhere** — the only
`derived` rows are Crude's two configured paths. A rule that states a condition
and no inference carries `verdict_text = None`, which per
`axes.construction.null_is_a_value` is a real member of the value set.

**Confidence is `untested` on all 4,813 rows.** It is not derived from claim tag,
tier, source_probability or anything else, and no code path can raise it.

#### Scoping is the part that had to be got right

The first run emitted **17,880 `no_rule` rows** because it applied every rule to
every instrument. A verdict row says "this condition is addressed to this
instrument"; a rule conditioning on Saturn has nothing to say about Nasdaq, and a
null row for it is true of nothing. Three rules now decide the addressable set:

* a rule naming **bodies** reaches the instruments the reconciled rulership
  resolves those bodies to, with Crude's contested paths handled by their own
  entries;
* a rule naming **no body** is a panchang or calendar rule, and reaches
  `NIFTY`, `BANKNIFTY` (tier 1) and `SPX`, `NDX` (tier 2), whose config
  definition is "the SAME rule families as Indian equities, evaluated on the New
  York civil day — no additions, no substitutions". It is **not** extended to
  COMEX gold, sugar or FX: those carry their own configuration sections, and a
  general market verdict applied to a specific contract would be our inference;
* a body whose rulership resolves to no instrument we carry (Mercury → IT and
  telecom, Mars → base metals) leaves the set empty, and **empty is not
  market-wide**. Emitting nothing is the correct outcome.

`USDINR` is added to every rule whose venue day it shares, because tier_4 says
its rows are emitted anyway "so the absence is VISIBLE in the output rather than
looking like a gap in the build". Its 1,940 rows are all verdict-null.

#### One conflict in the config, resolved the way config says to resolve it

`tiers.tier_1.instruments` lists `MCXGOLD, GC, MCXSILVER, SI` together as
source_backed. But `axes.localized` defines the property as "is the rule
evaluated on a civil day other than its authored one?", and
`civil_day_by_venue.changed_by_this_decision` names **GC, SI and CL** as exactly
the instruments whose day boundary moved. So **GC and SI emit tier `localized`
while MCXGOLD and MCXSILVER emit `source_backed`, for the same rule text on the
same sky.** The tier list predates the civil-day decision; `axes.localized.set_by`
points at it, and `tier_derivation.authority` says the pair wins where the name
disagrees. The asymmetry is the decision showing through, and it is reported
rather than smoothed.

#### The divergence check passes

The config measured 42.0% (gold) and 41.9% (silver) of in-scope events falling on
a different calendar date at the two venues. Recomputed from the layer:

| Family | In scope | Different date | Measured | Config |
| --- | --- | --- | --- | --- |
| gold | 1489 | 631 | **42.4%** | 42.0% |
| silver | 1496 | 633 | **42.3%** | 41.9% |

That number is the one thing that catches a verdict layer evaluating on the wrong
civil day, which is why it is recomputed rather than quoted.

#### source_probability, and a projection the build outgrew

`source_probability` attaches through the eleven `carried_families`, and getting
it to attach at all required handling the fact that **`family` is read two ways in
the config and both are live**: for the aspect and visibility families it is the
emitted `rule_family`, and for five others it is the SOURCE SECTION as printed
("Mercury Venus Alone in Any Sign p.16"). Matching only the first silently
dropped 5 of the 11 families.

`config.source_probability.projected_population` says the label reaches "15
astronomy records and about 11 rule-layer firings". The layer has **14 rules
carrying labels, from 11 families, over 344 verdict rows**, and the raw rule
firings behind them are **501**. So the projection under-counts by roughly an
order of magnitude. Recorded rather than reconciled: the projection was made
before the rule layer was complete, it was never a constraint (nothing filters,
weights or aggregates on the label), and the disputed families do emit the SET —
`b016`, `b017` and `b078`'s peers carry two values each, flagged
`source_probability_disputed`.

### 12.14 The render · recorded 14-Sep-2026

Three artifacts, all deterministic: `build/calendar_2027.json` (5.2 MB,
the master), `build/calendar_2027.csv` (2.2 MB) and
`build/calendar_2027.html` (4.6 MB, self-contained). **5,209 rows over 365
distinct dates, 1,854 carrying a verdict and 3,355 without.** Rendering twice is
byte-identical for all three.

#### The display format

`Date — Time IST | Time ET (EDT/EST) | Event | Vedic interpretation |
Financial-market theme | Confidence/risk label`.

**The dual date** is shown whenever the Eastern civil date differs, with the
marker. It never inverts: the measured shift is 2,485 rows at 0 and **2,724 at
−1, never +1**, because IST is UTC+5:30 and Eastern is UTC−5/−4. Window ends are
converted independently, so a window crossing the March or November change shows
two different Eastern offsets: **EST −05:00 on 1,711 rows and EDT −04:00 on
3,498**, both resolved through the IANA database rather than hardcoded.

Two rendering bugs were found by checking the output rather than the code:

* **Flags were emitted twice.** `Firing.flags` is copied off the rule at fire
  time, so for most rules the rule's list and the firing's list are identical and
  the concatenation doubled every flag — 4,844 of 5,209 rows. A reader counting
  flags would have concluded there were twice as many caveats as there are.
* **The sector alias.** The rulership lookup asked for a `sugar` sector and the
  table spells it `sugar_and_soft_goods`, so Venus resolved to nothing and the
  body-scoping step excluded SUGAR from every rule. See §12.15.

#### The apparatus is visible, not buried

The HTML opens with the disclaimer and a collapsed panel carrying: the certainty
grades **and both C grounds**, the claim tags, the five tier values with what
`cross_market_localized` and `venue_shifted` mean, the seven source defects found
in the 2026 document, all 33 blocked sections **with the input each waits for**,
the known coverage gap, the five rules firing on a supplied reading with their
flags, and the ambiguous section's competing readings.

It is a collapsible panel rather than a footnote because a reader who has to hunt
for the caveats will read the rows without them. The file is **self-contained**:
one `<script>`, no CDN, no network. A calendar that needs a server to read stops
being readable when the server does.

#### Search and filters

Full-text over event, section, verdict and flags; a date range; instrument and
tier selects; and a "only rows with a verdict" toggle. All client-side, over the
embedded rows, with a live count.

### 12.15 SUGAR: the diagnosis was wrong first time · recorded 14-Sep-2026

SUGAR emitted zero rows. The first diagnosis blamed only the unported
configuration sections in §12.16. **That was wrong, and the corrected cause is
the sector alias.**

The rulership lookup asked for a `sugar` sector key. The table spells it
**`sugar_and_soft_goods`**, from book_ch15's "sugar and soft/luxury goods". So
Venus resolved to nothing for that sector and the body-scoping step — the fix that
stopped every rule reaching every instrument — excluded SUGAR from every rule.
Adding the alias restored it: **SUGAR emits 396 rows, 134 carrying a verdict and
262 null**, through Venus-ruled catalogue-B rules. That is the correct channel:
`rulership.disagreements.sugar.resolution` says "SUGAR is tier 1 and takes its
verdicts from the source's own configuration sections, so no rulership is needed
to reach it", and SUGAR's significator per ch15 is Venus.

**Both facts are now recorded and neither hides the other.** The unported blocks
in §12.16 remain a real gap and are the reason SUGAR's coverage is *thin*; the
alias was the reason it was *empty*. §12.16 scopes what porting them would take.

### 12.16 The recurring failure mode — recorded 14-Sep-2026

This is the most transferable thing the build has produced, and it does not belong
scattered across four `corrections_on_record` entries where a reader meets it once
and files it as a detail of the layer it happened in. **A wrong answer that renders
as a plausible correct one** is the shape the build keeps producing, ten times so
far -- the four below, the measured fifth, a sixth that is the FIX for the
third having the same shape as the third, a seventh in which **the CHECK was the
wrong thing, not the code it checked**, and -- added 20-Sep-2026, all three out of
the third registry -- an eighth in which **an enumeration written as a literal
stopped being one**, a ninth in which **the fixture built to detect the third shape
had the third shape**, and a tenth in which **a negative predicate used as a
positive identity went wrong in four places at once**. Every instance was silent:
no exception, no failing assertion, no log line. Each was found by a check aimed at
the OUTPUT rather than at the code that produced it, and in three of the four the
code was read, understood and believed before the output was looked at.

**Three of the ten were produced by work done to fix earlier ones** -- the sixth by
the fix for the third, the seventh by a check written to satisfy this section's own
discipline, and the eighth by that same check a second time. Remediation is not a
safe region of this build. It is where three of the ten instances came from, and
the sub-section below the seventh says why that follows rather than surprises.

**And the eighth, ninth and tenth arrived together, out of one change.** Adding a
third registry did not introduce three unrelated defects; it revealed three places
that had encoded "there are two of these" without recording that they had. That is
the through-line of all three, and it is why they are filed as consecutive
instances rather than in three different sections.

**This section now holds FOUR shapes, and they are not variants of one another.**
The ten instances above and their detectors are the FIRST. Three more were found
later, each because the first shape's remedies passed over it, and each carries its
own detector because none of the first shape's detectors reaches it:

| | the shape | where the defect sits | its detector |
| --- | --- | --- | --- |
| **1st** | **a wrong answer that renders as a plausible correct one** | the operation misfired; the result merely looked survivable | assert an expected count or content sourced from OUTSIDE the code under test |
| **2nd** | **a correct count of the wrong set** (16-Sep-2026) | the operation is right; the population, unit or filter under it is not | state the unit and the filter beside the count, so a figure cannot be read without its population |
| **3rd** | **code that exists, was verified, and was never connected** (20-Sep-2026) | nothing ran; there is no output at all | an end-to-end fixture against the source's own finished output |
| **4th** | **a check that passes by reimplementing the logic it verifies** (20-Sep-2026) | the code under test never ran; a second copy of it ran instead, and agreed with the document | a check must exercise the PRODUCTION PATH, not a parallel one |

Read in that order they are the four ways a build can be wrong while every check
it has is green: **the answer is wrong**, **the question is wrong**, **the answer
was never asked for**, and **the answer that was checked came from somewhere else**.
Each shape's own sub-section states why the preceding shapes' detectors miss it,
which is the part that makes them separate entries rather than four examples of one.

#### The four instances

**1. Blank reference views — two separate causes, one shape.** §12.12. The
reference tables ("Journey of &lt;planet&gt;", "&lt;planet&gt; Motion",
"&lt;planet&gt; Constellation", "&lt;planet&gt; in Navmansh") are ported as views
over series the astronomy layer already emits. Two things each independently made a
view render **empty**:

* **the carried-in row was missing.** Every one of those tables opens with a "Start
  of the year" row — the state before the first movement. Without it, a body that
  never crosses the frame inside the span has nothing to print, which is exactly
  Uranus, Neptune, Pluto and the nodes. A body with no crossings renders as **a
  quiet year**.
* **the Herschel bridge was missing.** The document says "Herschel" throughout; the
  layer emits `Uranus`. With no bridge carrying the source's spelling, four
  Herschel views rendered blank.

An empty table and a table for a body that genuinely did not move are the same
bytes. Nothing anywhere could tell them apart; only reading the artifact could.

**2. The null-key regression on 4,163 records.** `finastro/events.py`. The
`certainty_ground` field belongs to certainty C alone — only C has something
missing. Populating it unconditionally would have written a null key into **all
4,163 pre-existing records**: a field on every record saying "this does not apply",
which is not a value for any of them. The build would have been "correct" (every
record carries the key, the schema is uniform) and the artifact would have been
rewritten wholesale by a change that added 7 records.

**3. `family` is read two ways, dropping 5 of 11 families silently.**
§12.14, `source_probability.corrections_on_record.family_key_is_read_two_ways`. The
label attaches by matching `family` against the emitted `rule_family`. That is one
of the two live readings. For five of the eleven carried families, `family` is the
**source section as printed, page marker and all** — "Mercury Venus Alone in Any
Sign p.16". Matching only the first reading left `b016`, `b078`, `b086` and the
Rahu-Mars family attaching to nothing. The emitted label set was plausible-looking
and wrong.

**4. Flags emitted twice on 4,844 rows.** §12.14. `Firing.flags` is copied off the
rule at fire time, so for most rules the rule's list and the firing's list are
identical — and the render concatenated them. Every flag was doubled on **4,844 of
5,209 rows**. A reader counting caveats would have concluded there were twice as
many as there are. This one was found by **reading a rendered row**, not by reading
the render.

#### What caught each — and the check that did not

| instance | what caught it | the check that passed anyway |
| --- | --- | --- |
| blank reference views | **inspecting the artifact**: rendering the table and looking at it, for each of 32 sections | "did the rule fire" passed — the rule fired and emitted nothing |
| null-key regression | **byte-level comparison against a known-good tree**: the 2,455 prior records extracted, written back through the build's own serialiser, and hashed against §12.5's hash | "did the new field populate" passed — it populated on the 7 new records |
| `family` read two ways | **counting against an independent expected list**: this block's own declared eleven carried families, 11 vs the 5 that attached | **"did anything attach" PASSED on the broken version** |
| doubled flags | **inspecting the artifact**: reading what a row actually carried downstream | reading the code — which concatenates two lists and is correct on its face |

The third row is the one to keep. The check that was written —
*"did anything attach"* — **passed on the broken version.** Five families attached,
the result looked sparse rather than wrong, and a sparse result is what a
twelve-entry block with a few quiet families *should* look like. It took a count
against a list held somewhere else to make "five" fail, and the list had to already
exist.

#### The fifth instance, and the first one whose averted cost was MEASURED

**34 of 58.** Recorded here and not only in `build/CONFIG_PORT_REPORT.md`, because
it is the first time in this build that the size of an averted failure is a number
rather than a description. Every one of the four instances above was caught *after*
the fact — three before they reached an artifact, but all four after the wrong
thing had been built.

The configuration port's verdict is stated in **two** elements: the block's `<h2>`
carries the direction and the group heading carries the condition. *Silver —
Bullish Configuration* + *Venus Mars Together* is one statement in two halves.
Catalogue B's port sliced a verdict out of the section's own heading, and applying
that operation unchanged here slices only the group heading.

**34 of the 58 group headings state no direction after a dash of their own.** So
the catalogue-B slice, applied unchanged, would have produced **34 rules with
`verdict_text = None`**, and every one of them would have rendered as a **blank
cell** rather than as an error — a table with the right columns and nothing in the
verdict column, which is indistinguishable from a port whose sections genuinely
print no verdict. That is the `family` half-match in a new costume, and the fifth
instance of the shape.

The number is measurable because the counterfactual is runnable: the naive slice is
executed as a counterfactual in `tests/test_rule_layer.py`, against the same 58
headings, and its 34 nulls are counted. The actual port produced **36 verdicts from
the block `<h2>`, 22 from the group heading, and none null.**

**The guard was built before the port, not after, and is proven to refuse all three
of its cases.** `finastro/rules/config_catalogue.check_verdict` runs at
REGISTRATION — before any rule can fire — and raises `SilentVerdict` on a null
verdict under a directional block, on a verdict that is not a substring of the
document, and on a verdict with no attribution; the import dies rather than
reporting. The harness feeds it each of the three separately and asserts it refuses
each one, because **the standing problem in this section is guards nobody has seen
fail**: a guard that has never rejected anything is indistinguishable from a guard
that cannot.

Which is the generalisation of point 1 below, stated forward instead of backward.
The check that would have caught the `family` bug was "count against a list held
somewhere else". Here that list — the 58 headings, and which of them carry a
direction — was built first, and the failure it averted has a size.

#### The sixth instance — the same key, one level down — recorded 15-Sep-2026

**`source_probability` attached at SECTION level, not rule level.** Found by an
independent verification pass over `build/calendar_2027.json`, and it is instance
3 above wearing a third costume. The fix for instance 3 widened the match: where
`family` was not an emitted `rule_family`, it was matched as a **substring of the
rule's section title**. That made five missing families attach, which is what it
was for. It also made the SECTION the unit of attachment, and a section holds
several rules.

Three consequences, every one silent:

* `b015`, `b015a`, `b015b` and `b015c` all sit in *Venus Combust Rise Cycle p.14*,
  and all four carried `combust_venus`'s **Reasonable** — including the two that
  are *rise* rules. `combust_venus` is listed before `rise_venus` and both match
  the same title, so the first won. **Block 46's High, `rise_venus`'s only value,
  reached no row of the calendar at all.**
* All three firing `b041` Herschel partners carried `conj_venus_uranus`'s **High**.
  Block 23 is titled *Venus Herschel Conjunction*; the source labelled one partner
  and two rules got a judgement the document never made.
* `cfg_silver_bearish_10_venus_rise_in_west` — the one rule the old matcher reached
  by family+body rather than by title — held a High from a section it is not in.

**A key that identifies a GROUP used to identify a MEMBER.** That is the sentence
that covers instance 3 and this one together: `family` names a family, a section
title names a section, and neither names a rule. Widening a match is how a member
key becomes a group key, and once it has, nothing distinguishes *this is the rule
the source labelled* from *this is filed next to it*.

**What caught it, and what passed anyway.** The check that existed —
`test_source_probability_population` — asserts the projected 26 records and
firings **exactly**, in the spirit of point 1 above, and it passes on the broken
build: it counts the astronomy layer and the rule-layer firings, not what reached
a row. The populated row count also barely moves: **536 rows before, 533 after**,
three rows on a 6,677-row calendar, because the three misattributions very nearly
cancel the one label that reached nothing. A per-family count, a per-total count,
and a spot check of a Venus row all survive this bug.

Only a **per-rule census** separates them, which is why the pin added in
`tests/test_rule_layer.py::test_source_probability_attaches_per_rule_and_not_per_section`
is a table of *rule id → (labels, row count)* and not a total, and why it carries a
negative half: the section-mates that must carry **no** label. On the broken build
every one of those was labelled, because its neighbour was.

| instance | what caught it | the check that passed anyway |
| --- | --- | --- |
| label attached per section | **a per-rule census of the emitted artifact** | `test_source_probability_population` — exact counts, of the wrong unit; and the total, which moved by 3 |

**And the fix for instance 3 became instance 6, which is the part worth keeping.**
Both corrections are recorded, the second pointing at the first
(`source_probability.corrections_on_record.label_attached_at_section_level`). A
repair that widens a match to make missing things appear should be read as a
candidate for this section, not as the end of one.

The attachment is now an enumeration: `carried_families[].rules` lists rule ids,
`probability_for` is a dict lookup on `rule.id`, and a rule id claimed by two
families **raises on import** rather than taking whichever family is listed first.
That last clause is the guard built to be seen failing, per the standing rule
above — the silent first-match win is precisely how `rise_venus` lost its High.

#### The seventh instance -- the CHECK was what was wrong -- recorded 15-Sep-2026

**A harness check read test NAMES as figures and summed to the right total by
coincidence.** Recorded as its own instance because it is the first in which **the
code under test was correct and the CHECK was the defect**. Every instance above is
a wrong artifact that a check failed to catch; this one is a wrong check standing
over a right artifact, reporting a pass it had not established.

**What happened.** The test-3 recount against all three catalogues
(`catalogues.test_3_recount_against_all_three_catalogues`) states its arithmetic in
a prose line:

```
19 pass / 12 fail test 1 / 12 fail test 2 / 1 orphan = 44
```

The first version of the harness check pulled every digit out of that string to
verify the arithmetic closed over the 44 labelled prophecy blocks. It collected

```
[19, 12, 1, 12]
```

because **the `1` and the `2` in "fail test 1" and "fail test 2" are the test NAMES,
not counts**, and a regex cannot tell a name from a figure. It took the first `1` as
the third count, never reached the orphan count at all, and read `12` once instead
of twice. `19 + 12 + 1 + 12 = 44`, so the arithmetic closed and the check
**passed** -- on four numbers, three of them the wrong number and one of them a
label.

**Why it is its own instance.** The recount itself is sound: 19/12/12/1 before,
19/12/12/1 after, and the figures are the ones the classification carries. Nothing
downstream was wrong. Had the check been deleted, the build would have been in
exactly the state it was in with the check passing -- which is the definition of a
check that is not one.

| | the first six | the seventh |
| --- | --- | --- |
| what is wrong | the artifact | the check |
| what a passing check tells you | nothing -- it asks about occurrence | nothing -- it is reading the wrong input |
| the detector | assert an expected count or content from OUTSIDE the code under test | **print what the check actually read**, not whether it passed |

**What caught it.** Printing the list the scraper had built, beside the four numbers
it was supposed to have read. The pass/fail line said nothing: it read `[PASS]` both
before and after the fix, and the four figures are identical before and after, so no
re-run and no before/after comparison could have separated them. Only the
intermediate value could, and only because it was printed.

**The remedy is a schema change, not a stronger regex.** The prose line stays prose
and nothing parses it. The same two lines are now stated as **numbers**:

```yaml
arithmetic_before: "19 pass / 12 fail test 1 / 12 fail test 2 / 1 orphan = 44"
counts_before: {pass: 19, fail_test_1: 12, fail_test_2: 12, orphan: 1}
counts_after:  {pass: 19, fail_test_1: 12, fail_test_2: 12, orphan: 1}
labelled_blocks: 44
```

and the harness sums `before[k] for k in ("pass", "fail_test_1", "fail_test_2",
"orphan")` -- **four named keys, read by name, with a KeyError if one is missing.**
Point 2 of the generalisation below says a count taken from our own artefacts
describes our artefacts. This is one level under that: a count *parsed out of a
sentence about our artefacts* describes the sentence's punctuation.

| instance | what caught it | the check that passed anyway |
| --- | --- | --- |
| the check scraped test names as figures | **printing the intermediate value the check had read** | the check itself -- `[PASS]`, on `[19, 12, 1, 12]`, summing to the right total by coincidence |

**And it happened inside the file that documents the shape**, in the same session
that added the sixth instance to it. That is the part worth keeping, not the regex.
It is on record in the config as
`catalogues.test_3_recount_against_all_three_catalogues.the_first_check_read_test_names_as_figures`.

#### The two instances that remediation produced

**The sixth and the seventh both came out of work done to fix earlier ones,** and
they are the only two of the seven that did.

* **The sixth is the fix for the third.** `family` was matched too narrowly and five
  families attached to nothing; the repair widened the match to the rule's section
  title, which made them attach -- and made the SECTION the unit of attachment, so a
  label the source put on one rule spread to its section-mates.
* **The seventh is a check written to satisfy this section.** The discipline below
  says: *name the count you expect, say where that number came from, and check it.*
  The recount did name it, and the check written to enforce it read the count out of
  a prose sentence and passed on the wrong four numbers.

**Why that is structural rather than bad luck.** Remediation work carries two
properties the original work does not. It is done under the belief that the failure
mode is now understood, which is exactly the state in which the output goes unread.
And it is measured against the *symptom* of the thing it fixed -- "the five families
attach now", "the arithmetic closes now" -- so the fix is accepted the moment the
symptom clears, whether or not anything else moved with it.

The rule taken from both is already written into
`source_probability.corrections_on_record.label_attached_at_section_level`: **a
repair is a candidate for this section, not the end of one.** A fix that widens a
match, and a check written to pin a number this section asked for, get the same
treatment as a new emit -- name the count, say where it came from, and **print what
was read, not whether it passed.**

#### The shape, named

> **A wrong answer that renders as a plausible correct one.** Silence is not a
> signal. The failure mode is not "the code crashes" or "the number is obviously
> mad" — it is a result that is the right *shape*: a table with the right columns
> and no rows, a field present on every record, a label set that attaches to some
> families, a flag list that is longer than it should be. Each is indistinguishable
> from the truth **from inside the code that produced it, and from any check
> phrased as "did the thing happen at all".**

The generalisation that follows, and the reason this section exists:

1. **A check phrased as "did it happen" cannot catch this class.** "Did the rule
   fire", "did the field populate", "did anything attach" all pass on the broken
   version, because the broken version *does* the thing. The check has to assert an
   EXPECTED COUNT OR CONTENT that came from somewhere other than the code under
   test.
2. **A count taken from our own artefacts describes our artefacts.** This is the
   141/141 claim one level up: the coverage number was derived from our own config,
   so it could not fail, and it read as a coverage statement about the source for
   long enough to be published on two pages. The document is what the claim is
   about. `finastro/cfgsections.py` reads the count out of the source instead, and
   `CONFIG_SECTIONS_SCOPE.md` reports what is in it.
3. **The cheapest detector is the artifact, not the code.** Three of the four were
   found by looking at the OUTPUT: a rendered table, a rendered row, a hash over
   bytes. The code was read first in every case and was believed. Reading code
   tests the author's model; reading output tests the artifact, and the model is
   the thing that is wrong.
4. **Byte-level comparison against a known-good tree is the strongest of the
   three** because it cannot be satisfied by a plausible shape: either the bytes
   moved or they did not. §12.6 and §12.9 both used it, and it is why "changes none
   of them" is provable rather than asserted for the 4,163 records.

#### The discipline this argues for

Before believing any new emit: **name the count you expect, say where that number
came from, and check it.** If the only source for the expected number is the code
that produced the actual one, the check cannot fail and is not a check.

And -- added 15-Sep-2026, from the seventh instance -- before believing any new
**check**: **print what it actually read.** A check reports a boolean, and a boolean
is the one output of this build that carries no evidence of what produced it. The
scraper that read `[19, 12, 1, 12]` printed `[PASS]`, and so did the fix; only the
intermediate value told them apart. Which is
also why the pinned zero-firings, the 11 carried families, the 96 printed Vedha
rows, and the 58 configuration groups are all carried as **independent lists with
numbers attached** rather than as taste.

**It would be a mistake to read this section as a list of four mistakes.** Three of
the four were caught before they reached an artifact, by checks that exist because
the shape was already known. The transferable result is the shape, and the fact
that the check which passes on the broken version is always the one phrased as a
question about occurrence rather than about count.

#### The same shape, applied to the coverage claim itself · same date

The claim on `README.md` and `build/RULE_LAYER_STATUS.md` that the rule layer covers
"141 of 141 sections" was **true and misleading in exactly this way**. It was true
of catalogue B. The instrument configuration sections — `<section id="...">` with
an `<h2>`, not `<h3 class="section">` — were never in the 141 sections or the
141-section denominator, so the number could not fail, and it read as a statement
about coverage of the source. A reader seeing 141/141 and a calendar with gold,
silver and sugar rows on it had every reason to conclude the source's own gold,
silver and sugar material was in the build. **It is not: 0 of 58 named groups are
ported, and no row in the calendar originates in any configuration section.**

Two pages now carry both denominators, and the count is read from the document
rather than from config:

```
catalogue B                        141 / 141 sections
instrument configuration sections    0 /  58 named groups
```

> **Superseded by part 1, and left standing as written.** The configuration port
> took that second line to **38 / 58**, with 20 blocked on a named input. What is
> **not** superseded is the sentence that matters here: *no row in the calendar
> originates in any configuration section.* The 38 are registered in their own
> registry and `verdicts.py` still fires catalogue B alone, so a reader who reads
> "38 ported" as "38 in the calendar" makes the same mistake this section is
> about, one step further along. `build/RULE_LAYER_STATUS.md` and `README.md`
> carry the current pair; this block is the count as it stood when the audit was
> made.

The same audit found **two of the counts inside config had never been derived
either** — gold's groups read 17 and silver's 29 against the document's 19 and 30,
because gold carries its groups as `<h3>` headings and a reader reaching for
`config-title` finds none of them
(`source_probability.corrections_on_record.gold_and_silver_config_group_counts`).
Corrected, and the correction recorded rather than the number quietly replaced.

The scoping of the 58 is in `build/CONFIG_SECTIONS_SCOPE.md`: **41 of them need no
astronomy the layer lacks**, and the other 17 sit behind **five** distinct missing
inputs, two of which (`aspect_orbs`, `month_system_confirmation`) are already open
questions here and are owed an answer for catalogue-B sections regardless of
whether gold, silver and sugar are ever ported. That is the difference between a
gap that can be scoped and a gap that has to be guessed at, and it is the only kind
of coverage statement worth publishing.

**The calendar exists and renders. The coverage claim is now stated honestly, and
that mattered more than adding to it.**

#### A SECOND SHAPE: a correct count of the wrong set · recorded 16-Sep-2026

**This is not the quiet-blank family and must not be filed under it.** Everything
above is one shape — *a wrong answer that renders as a plausible correct one*. The
operation misfired and the result merely looked survivable. Here the operation
does not misfire. **The arithmetic is right every time.** The number is a true
statement about a set, and the set is not the one the sentence around it names.

> **A correct count of the wrong set.** A figure that is arithmetically sound,
> reproducible, and attached to the wrong population, unit or filter. It cannot
> be caught by recomputing it, because recomputing it gives the same answer —
> the defect is in the **domain**, not in the operation over the domain, and an
> integer carries no trace of its domain.

**Three instances in two turns**, all in the span-vs-daily work:

| | the figure | what it actually counted | what the sentence claimed |
| --- | --- | --- | --- |
| 1 | **`282`** | distinct `(venue, date)` pairs among the **471 `date_only` ephemeris** rows, in the 7,082-row population | the **carry-in** cause's firings. Carry-in is **142** |
| 2 | **`45` / `12`** | `45` = `b101` firings in a population holding its Mumbai rows only; `12` = anchored **rows** | both read as firings, in the same table as their neighbours. `b101` is **105** firings; anchored is 12 rows and **11** firings |
| 3 | **`22`** | `clipped_end` groups **alone**, with the `open_*` filter its own sentence states never applied | spans with a real endpoint outside 2027 and `open_*` false. That is **24** — it omits the 10 `clipped_start` groups, and 5 of its own 22 are already `open_end` |

Instance 1 is wrong in the **cause**, 2 in the **unit**, 3 in the **filter**.
Those are the three axes, one each, which is why the shape took three tries to
see: no two of them look alike at the point of failure.

**Two more, found while attributing the first three** — the shape does not stop
appearing once it is named:

* **`105` is a location count**, and the venue count exists and is **150**.
  `b101` fires on 45 Mumbai and 60 New York civil days, but Mumbai carries three
  venues, so `(rule, venue, day)` gives 150 where `rules.base.fire` emits 105.
  Nothing downstream used 150. It is recorded because the near-miss is the point.
* **`331 / 282 / 11` and `858 rows` were quoted as one line and are two
  populations.** `331` is catalogue-B only (5,209 rows); `858` is every verdict
  row (6,677). The no-instant rows of the population `331` was drawn from total
  **849**. Both figures are correct; the line is not.

#### Why every detector this section already had misses it

Each remedy above asks a question about **occurrence or content**: did the rule
fire, did the field populate, did the label attach, do the bytes match. §12.18
added *print what the check read*. **All of them pass here**, because the thing
that ran ran correctly and the value it printed is the value it computed.

The nearest neighbour is the **stale-denominator** failure that `row_kind` landed
first to prevent (§12.17), and this is its **mirror** — worth stating because the
remedy does not carry over. There, a figure is held fixed and the population moves
under it. Here the population was never fixed at all, so there is nothing for a
figure to go stale against. A discriminator landed before the change cannot help;
the figure has to carry its population **at the point it is written**.

And the sharpest form: **`662` was a correct count too.** It reproduces exactly
against the pre-`DateStamp` render at `dfb485b` — 663 rows less `b102` — and its
population was *rows whose rendered string began `00:00 IST`*. That population
misses 196 structurally instant-less rows, and misses them **non-randomly**: a row
printed midnight only where the stand-in instant it was handed happened to be a
Mumbai midnight, so the rows it could not see are precisely the ones whose
fabricated time looked *plausible* — `09:34 IST` for all 18 of `b079`, `10:30 IST`
for `b101`'s New York half. **A population defined on appearance is blind to
exactly the cases the appearance was hiding.**

#### The detector, named

> **State the unit and the filter beside the count, so a figure cannot be read
> without its population.**

Not a check that recomputes — that passes. Not "print what you read" — the figure
*is* what was read. The count must be **unpublishable in isolation**, the way the
two coverage denominators must travel together and for the same reason:
`166 of 354` and `166 of 173` are both correct and mean different things, and the
rule there is already *state the relationship, not just the pair*.

**Landed, not merely resolved:**

* **`tools/cause_census.py`** is the generator the proposal's §1 demanded and did
  not itself have. It prints every count in **three populations** side by side
  (catalogue-B 5,209 / all verdict 6,677 / all rows 7,082) and **six units**
  (rows, firings, `(rule, venue, day)`, `(venue, date)`, spans, rules), with a
  unit key spelled out beneath the tables and the filter stated in the header.
  A reader who has only the output cannot mistake 105 for 150, or 849 for 858.
* **`conventions.yaml → row_kinds.time_fields.year_clip.measured_2027`** carries
  instance 3's census as eight named keys rather than one number, and
  `test_the_civil_year_clip_is_a_field_and_not_the_period_cut` recomputes each
  and prints what it read.
* **The proposal's §1 is rewritten as an attribution table** — figure,
  population, unit, filter, reproduces — in place of an argument about which set
  is right. Under it, `249` and `147` are the only two members of either set that
  reproduce against nothing at all, and they stay withdrawn.

**What this cost, measured.** Nothing shipped wrong: all five figures were caught
inside the batch that produced them, and `−795` — the one number a reader would
have acted on — turns out to be **invariant across all three populations**, so the
collapse arithmetic never rested on the set under dispute. The cost was two full
turns of argument over which set was right, conducted by both sides without either
stating what it had counted. **That is the tell: a dispute about whether a figure
is correct, in which neither party has named the population, is not yet a dispute
about anything.**

#### A THIRD SHAPE: code that exists, was verified, and was never connected · recorded 20-Sep-2026

**This entry was owed from 15-Sep-2026 and deferred twice before it was written,
which is the shape it is about.** A documentation item that is understood, agreed
and never connected to the page it belongs on is the same failure as a module that
is written, tested and never called; the only difference is that nothing imports
prose. It is recorded here rather than noted as an aside because both prior
deferrals were invisible for exactly the reason below — nothing failed while it was
missing.

> **Code that exists, was verified, and was never connected.** A component that is
> present, correct, and covered by a passing check, which **nothing calls**.
> Invisible because every check on the component passes — the component *is*
> correct, and the correctness of a component says nothing whatever about whether
> anything reaches it.

**It is neither of the two shapes above, and the difference is where the defect
sits.** The first shape is an operation that misfired into a plausible-looking
result. The second is an operation that ran correctly over the wrong population,
unit or filter. This one is **an operation that never ran at all**. There is no
wrong output to read, no figure to attribute to a domain, and no byte that differs
from the byte that ought to have been there. The artifact is not misleading; it is
**silent** — and a silence is indistinguishable from the feature never having been
built.

#### The four instances

| | what exists, and what verified it | what it never reached | measured cost |
| --- | --- | --- | --- |
| **1. SUGAR's sector key** | the reconciled rulership table, which spells the sector `sugar_and_soft_goods` off book_ch15. The table was **right** | the lookup asked for `sugar`, so Venus resolved to nothing and the body-scoping step excluded SUGAR from every rule | SUGAR emitted **0** rows. With the alias: **396**, 134 carrying a verdict (§12.15) |
| **2. The configuration rules, ported and not wired** | 38 of 58 groups, verified against the document group by group, with `check_verdict` guarding registration and that guard proven to refuse all three of its cases | `verdicts.py` fired catalogue B alone, so no configuration rule reached a calendar row | **0** rows for the whole port until 14-Sep-2026. Now **1,468 of 6,677** |
| **3. The stale `0 of 58`** | the count in the registry, which was correct throughout | four pages that printed it, none of which read the registry | four published pages asserting the opposite of the build's own state |
| **4. Bhadra and Total Day** | `panchang.total_days` reproduces the source's `dd + mm == yy` **12/12** for 2026; the karana computation reproduces the Bhadra section's **16** January boundaries to within **25 seconds** (§6.8) | neither was ever given a rule | **65** of the source's own printed windows — Total Day **11**, Bhadra **54** — that the calendar does not reproduce |

Instance 3 shows that the shape is not about code. What was disconnected there was
a *number* from its *source*; the mechanism is identical and so is the silence.

#### Why every detector this section already had misses it

| the detector | why it passes |
| --- | --- |
| assert an expected count or content from outside the code under test | it asserts over an output. There is no output |
| read the artifact, not the code | the artifact is correct — it is a correct rendering of a build in which the thing was never called |
| byte-level comparison against a known-good tree | **the bytes are identical, and that identity IS the defect.** The strongest of the four detectors above is the most precisely inverted here |
| print what the check read | the check read what it was pointed at, and it was pointed at the component |
| state the unit and the filter beside the count | the second shape's remedy needs a count to attach them to |

Every remedy in this section presupposes that **something ran**. Four of the five
are questions about an output and the fifth is a question about a figure's domain.
A component nobody calls produces neither.

**And the component's own tests are the trap, not merely useless.** All four
instances carried passing checks *on the disconnected thing* the whole time:
`test_total_days` asserted 12/12 while zero rules read a `total_day` record,
`test_bhadra_two_printings` ran seven checks on a karana computation that no event
class emits, and the 38 configuration groups were verified group by group against
the source while reaching nothing. **A passing component test is positive evidence
that the component works and no evidence at all that it is reachable** — and it
reads, to anyone scanning a green suite, like coverage.

#### The detector, named

> **An end-to-end fixture against the source's own finished output.** Not against
> our records of it, and not against the component. The only check that can see an
> absence is one whose expected set was written down by somebody other than this
> build.

`build/MONTHLY_2026_FIXTURE.md` is that fixture — the source's own 2026 monthly
calendar, 354 printed windows over 147 event names — and it found instances **2 and
4**. It could find them because its denominator is the document's, so a window the
layer never attempts is a **miss** rather than an absence, and a miss is visible
where a silence is not. That is the same property that makes the two coverage
denominators travel together: **47% coverage is the number that can fall when
nothing is wired, and 96% precision is the number that cannot.**

#### A cheap structural detector, measured

The fixture is the general answer and it is not free — it needs the source's
finished output, transcribed and mapped. There is a narrower one available inside
the build, and it was **run rather than proposed**:

> **Every registered key that no registered consumer claims is a candidate
> instance.**

`finastro/rules/base.INPUT_CERTAINTY` grades 20 input classes. Cross-referenced
against the `inputs=` of all **171 catalogue-B rules and 58 configuration rules**,
exactly **two keys are declared by no rule**:

```
'calendar/total_day'  graded A
'panchang/karana'     graded A
```

**They are precisely the two cheap ports still owed.** A certainty grade is a
statement that a class has been assessed and is fit to condition a rule on; two of
them have sat in that table since Step 4 opened, graded **A**, claimed by nothing.
The grade is the registration this shape leaves behind, and it is checkable in a
dozen lines.

**Landed and falsified, not proposed.**
`tests/test_rule_layer.py::test_a_graded_input_class_that_no_rule_claims_is_named`
runs the cross-reference, **prints the whole census** — every graded class beside
the number of rules declaring it — and pins the unclaimed set against
`EXPECTED_UNCLAIMED_INPUT_GRADES`, which holds each key's reason and the port it
belongs to. The expected set is held in the harness and not derived from the
registry, because a set computed from the registry agrees with the registry by
construction and cannot fail. It was falsified three ways before it was believed:
a third unclaimed grade fails it, an *ungraded* declared input fails it, and a rule
that claims `calendar/total_day` — which is what wiring TASK 1a looks like — fails
it too. **That last one is the coupling worth having: the port cannot land without
this record moving with it,** which is the failure mode this whole sub-section is
about, turned into a check. +3, 228 → **231**.

**Its limit, stated because a detector nobody has seen fail is not a detector.** It
catches only disconnections that *registered* something. It does **not** catch
instance 1 — a misspelled key registers nothing — and it does **not** catch
instance 2, because the 38 configuration rules were fully registered in a registry
that `build_verdicts` did not call, so every key they declare is claimed. It is a
cheap second net under the fixture, not a substitute for it.

#### Two depths of disconnection, and only the artifact separates them

Instance 4 is one line in the table above and **two different failures**, which the
artifact distinguishes and the prose describing it does not:

| | Total Day | Bhadra |
| --- | --- | --- |
| computation | `panchang.total_days`, validated **12/12** | karana number and name, on every panchang record, verified to **25 s** |
| records in `build/astronomy_2027.json` | **12** `total_day` | **0** — the file carries 16 event classes and karana is not among them |
| rows in `build/calendar_2027.json` | **12**, as base-track event rows | **0** |
| verdict rows | **0** — no rule reads the class | **0** |
| of the source's printed windows | 0 of **11** | 0 of **54** |

**Total Day is connected to the artifact and not to the rule layer**: its records
reach a reader, and no rule conditions on them. **Bhadra is not connected to
anything** — the computation is verified and graded A, and there is no event class
for it, so nothing downstream could read it if it tried. Calling both "never
connected" is true and loses the fact that one is a rule away and the other is a
rule *and a series* away — which is exactly the difference the handoff's port list
draws between its 1b/1c and its 1d (`build/NEXT_SESSION.md`, TASK 1).

This distinction cost one query against each of the two generated files. **It was
not derivable from any page that describes them**, including the page that lists
the ports.

#### The discipline this argues for

Added to the two already standing — *name the count you expect and say where it
came from*, and *print what the check actually read*:

> **Before believing any verified component: name the thing that calls it, and
> check the call from the far end.** Not from the component — from the artifact the
> caller writes. If nothing can be named, the component is not done, however green
> its tests are.

And the corollary, because this is the fourth appearance and the second entry
deferred while it was true: **a verified-but-unconnected component is not a
half-finished feature, it is a zero-finished feature with a passing test.** Its
cost is not proportional to how much of it is built. Instance 2 was 38 fully
verified group ports at **0** rows, and the last step — one condition in
`build_verdicts` — was worth all 1,468.

#### The eighth instance — an enumeration written as a literal · recorded 20-Sep-2026

**The check written to satisfy this section's own third-shape discipline was itself
an instance of its second shape, and it kept passing while wrong.** This is the
third instance produced by remediation and the second in which the CHECK was the
defect rather than the code under it, so the pattern the seventh instance named
holds rather than repeats by accident.

`test_a_graded_input_class_that_no_rule_claims_is_named` cross-references
`rules.base.INPUT_CERTAINTY` against the `inputs=` of every registered rule and
names any graded class no rule claims. Written on **15-Sep-2026**, on a build with
**two** registries, it summed them **by name**:

```python
for rule in list(R.REGISTRY) + list(R.CONFIG_REGISTRY):     # the defect
```

On 20-Sep-2026 `sub_total_days_in_year` claimed `calendar/total_day` — which is
exactly what wiring TASK 1a looks like from this check's side, and the one
transition the check was explicitly falsified against before it was believed. **It
went on passing.** The rule that claimed the key sat in `SUBTABLE_REGISTRY`, a
registry the check could not see, so the census was a correct count over a
population two registries wide against a build three registries wide, and
`calendar/total_day` was still reported unclaimed after a rule claimed it.

| | what the check asserted | what was true |
| --- | --- | --- |
| registries walked | 2, by name | 3 |
| rules in the census | 229 | 231 |
| `calendar/total_day` | unclaimed, TASK 1a still owed | claimed by `sub_total_days_in_year`, ported and verified 12/12 |
| the check's own result | PASS | PASS |

**The lesson is narrower than "print what the check read", and that is why this is
its own entry.** The check *did* print what it read — the full census, every graded
class beside the number of rules declaring it — and the printed census was
internally consistent, because a rule the check cannot see also cannot appear in
its output. The discipline that would have caught this is about how the population
was *obtained*, not about how the result was reported:

> **An enumeration written as a literal stops being an enumeration the moment the
> thing it enumerates can grow. Discover, do not list.**

A literal list is a correct statement of a population *at the moment it is typed*,
and it carries no mechanism to notice it has stopped being one. It does not decay
into an error; it decays into a **smaller correct answer to a question nobody
re-asked**. `REGISTRY` and `CONFIG_REGISTRY` were the complete set when that line
was written, and the line was right for five days.

It now discovers:

```python
registries = [v for k, v in vars(R).items()
              if k.endswith("REGISTRY") and isinstance(v, list)]
```

with `len(registries) == 3` recorded **beside** the census rather than in place of
it. The distinction is the whole point: the count is a tripwire that must be
updated deliberately when a fourth registry lands, and the census is derived from
whatever is actually there. A literal used as a tripwire fails loudly when the
world moves; a literal used as an enumeration fails silently. **Same constant,
opposite properties, and which one it is depends entirely on whether anything
reads it.**

**Found only by running it against a build where the answer was known to have
changed.** No suite went red. The widening of 20-Sep-2026 shows the discipline
working the other way: `subtables.SUBTABLE_REGISTRY` is checked against
`subtable_catalogue.SUBTABLES`, a count the *document* produces, so a section
gaining a registry entry — or the document gaining a section — cannot pass quietly
in either direction. It duly failed the moment Bhadra joined: *9 sub-table rules
against 10 sections in the document.*

#### The ninth instance, and the sharpest this section holds — the fixture built to detect the third shape had the third shape · recorded 20-Sep-2026

**`build/MONTHLY_2026_FIXTURE.md` is named above as *the* detector for the third
shape.** It found instances 2 and 4 precisely because its denominator is the
document's, so a window the layer never attempts is a *miss* rather than an
absence. On 20-Sep-2026, with TASK 1a and 1b ported, verified against their own
sections' printed rows, registered, and wired into `verdicts.py`, the fixture was
re-run and reported:

```
168 of 354 windows      <-- the post-wire number, unchanged
```

The correct figure was **192**. The two ports contribute exactly **11 + 13 = 24**,
which is the whole of what the two sections print, and none of it was visible,
because **the instrument that measures coverage could not see the third registry**
— in two independent places:

| where | what it did | consequence |
| --- | --- | --- |
| `finastro/monthlymap.py` | classified *Total Days in Year* and *Rahu or Ketu Nakshtra on a Thursday* as `subtable_unported` | both events reported as gaps after they had been closed |
| `tools/monthly_match.py` | fired `REGISTRY` and `CONFIG_REGISTRY` | no `sub_` rule could fire, so no window could be claimed |

**This is the third shape occurring inside the fixture built to detect the third
shape, and it is the sharpest instance this section holds.** Every other instance
is a defect in the thing being measured. This one is a defect in the *measure* —
and it fails in the single direction that is indistinguishable from the defect the
measure exists to find. A port that was never wired and a port that was wired but
invisible to the fixture produce **the same number on the same page**: 168, with
the same 49 `subtable_unported` windows listed beneath it. Had the ports genuinely
not been connected, the fixture would have printed exactly this.

**The inversion, plainly.** The third shape's detector is "an end-to-end fixture
against the source's own finished output", and its power comes from the
denominator being the document's rather than ours. The *numerator* is still ours. A
fixture with the document's denominator and a stale numerator does not under-report
by a little — it reports the pre-port state as though it were the post-port state,
with full confidence and no gap anywhere in its own output.

Fixed in both places: `monthly_match` fires all three registries, and
`monthlymap`'s `SUBTABLE` outcome means what it always meant — a sub-table states
the event — with `subtable_unported` reserved for the ones still blocked. The
progression **166 → 168 → 192** is the record, and the middle number is the one
that stood while the ports were already live.

> **A detector's denominator being independent of the build does not make its
> numerator independent of the build.** Check the measure against a transition
> whose size is known in advance: the two ports were worth 11 and 13 printed
> windows before either was written, so a re-run that moved by anything other than
> 24 was answerable on the spot. **A coverage number that does not move when
> coverage moves is a failing check reporting PASS.**

#### The tenth instance — a negative predicate used as a positive identity · recorded 20-Sep-2026

**"Not a configuration rule" had been standing in for "a catalogue-B rule" in four
places, and the third registry made all four wrong at the same instant.** Not four
symptoms of one bug — four independent pieces of code, written at different times
by the same reasoning, each correct for exactly as long as the world held two
categories.

| | the predicate | what broke when a third registry existed |
| --- | --- | --- |
| `verdicts.is_config_rule` | `rule.section.catalogue_b is None` | a `SubTable` also carries `b = None`, so every sub-table rule was classified as a configuration rule |
| `tools/cause_census.py` | P1 as "all verdict rows that are not `cfg_`" | P1 went **5,209 → 5,314** with no catalogue-B rule changing — a population growing by rows belonging to neither of its two categories |
| `tools/gen_status.py` | the status page's row split, same predicate | 81 sub-table rows reported under catalogue B, inflating the one denominator this build maintains three registries to protect |
| `tools/monthly_match.py` | three rule lookups, same predicate | sub-table rules resolved as configuration rules inside the fixture's own attribution |

All four are now **positive** tests — `isinstance(rule.section, SubTable)`, or an
explicit `sub_` prefix — and P1 is back to **5,209** with its four census figures
back at **331 / 142 / 105 / 11**.

> **A negative predicate used as a positive identity survives exactly as long as
> there are two categories.** `not A` and `B` are the same set under a closed world
> of two, and nothing in the code records that the equivalence depends on the
> count. When a third category arrives, `not A` silently acquires it — and it
> acquires it in **every** place the shortcut was taken, simultaneously, with no
> single change to point at.

**Why this is worse than an ordinary wrong predicate.** A wrong predicate is wrong
from the day it is written and has a chance of being caught by the first test over
it. This one is *right* from the day it is written, is exercised correctly
thousands of times, and becomes wrong on a day nobody edited it. The defect's
commit is the commit that added the third registry — which changed none of the four
files.

**And the same reasoning was live in this build's membership rules until today,
which is how Bhadra stayed outside every registry.**
`cfgsections.other_h2_tables()` defined the sub-tables as "the `<h2>` sections that
are not the six instrument blocks", implemented as a byte range from
`<section id="kshin-moon">` to `<section id="gold-bullish">` — a negative identity
with a *document range* standing in for it. The range excluded `sec-142` for no
reason the document supports: Bhadra carries the identical markup, and the
document's own table of contents lists it one row above Kshin Moon, in the same
chapter, at Sr.No 139.

It is now the positive one: a configuration block's `<h2>` **states a direction**
(*Gold — Bullish Configuration*), a sub-table's does not, and
`cfgsections.is_config_heading()` is the single place that decides. That predicate
is the same fact `config_catalogue.check_verdict` and
`subtable_catalogue.check_no_verdict` already turn on — a block's heading carries
half of its section's verdict, a sub-table's carries none — so membership and the
verdict rule read one property and cannot disagree about a section. `BLOCKS` keeps
the instrument, direction and printed pages it alone carries, and is checked
against the six the predicate discovers rather than trusted as the list of them.
Denominator **9 → 10**.

#### A FOURTH SHAPE: a check that passes by reimplementing the logic it verifies · recorded 20-Sep-2026

**`panchang.karana_name` named karana 57 *Shakuni* for as long as the function
existed, and the suite that verifies Bhadra to 25 seconds could not have failed on
it.** Not "did not" — could not. `test_bhadra_two_printings` computes its own karana
index from the elongation, carries its own literal list of the eight Vishti numbers,
and never calls `karana_name`, `karana_boundaries` or anything else in the karana
half of `panchang.py`. It would have passed on *any* numbering error in the shared
function, including one that named every karana wrongly, because the shared function
is not on its path. **The defect was invisible for the same reason the test was
green**, and that identity is the whole entry.

> **A check that passes by reimplementing the logic it verifies.** The check is
> correct, its expected values come from the document, and it agrees with them — and
> the code the build actually ships never runs. What was verified is a second
> implementation that happens to live in the test file. The pass is real; it is a
> pass for the wrong program.

**It is none of the three shapes above, and the difference is what ran.** The first
shape is an operation that misfired into a plausible result. The second is an
operation that ran correctly over the wrong population. The third is an operation
that never ran at all and left silence. Here **an operation ran, produced the right
answer, agreed with the document — and was not the operation under test.** The
artifact was wrong throughout and the check standing over it was green, rigorous,
and pointed somewhere else.

**And it is NOT the eighth instance in a new coat**, which is the misfiling to guard
against. Both are about a check that quietly stopped covering what it was believed
to cover:

| | the eighth instance | this one |
| --- | --- | --- |
| what was a literal | the check's **enumeration** — `REGISTRY + CONFIG_REGISTRY`, a list of the populations to walk | the check's **logic** — a second karana engine, index, boundaries and names, all of it |
| when it became wrong | when the world grew a third registry, five days after it was typed | **never.** It was always a parallel path; it was never covering the shared one |
| the remedy | *discover, do not list* | *call the thing you are checking* |
| what a reader of the check sees | a correct census, internally consistent | a correct reproduction of the document, internally consistent |

The eighth was right when written and decayed. This one was never wrong and never
covered anything — which is worse in the one way that matters: **no change to the
build could have exposed it.** A registry count moves when a registry lands. A
parallel implementation stays in perfect agreement with the document forever, no
matter what the shared function does, because the two never meet.

##### The contributing cause, recorded separately: first-match-wins, one layer down

The defect itself was not the test. It was this, in `karana_name`:

```python
FIXED_KARANA.get(knum - 1) or FIXED_KARANA.get(knum) or <movable>
```

against a `FIXED_KARANA` whose keys were 0-based. The first lookup is the correct
one under those keys. The second is **the same question asked in the other
convention**, and `or` takes whichever answers. For `num = 57` — a movable karana,
where the 0-based lookup correctly misses — the fallback hit the 0-based key `57`
and returned **Shakuni**, which is karana 58's name.

> **A lookup that tries two conventions and takes whichever answers has decided
> nothing. It has guaranteed that nobody will ever find out which one is right.**

This is **the first-match-wins matcher again, one layer down.** §12.16's sixth
instance is the same move at the rule level — `family` matched against two readings
with the first hit winning, which is how `rise_venus` lost its High — and the remedy
recorded there was an enumeration that **raises on a rule claimed twice** rather
than taking the first. A key table is a smaller version of the same object, and this
one was left accepting both readings of its own keys. The fix is the same in kind:
the keys are the karana NUMBERS the document uses, and the lookup asks **once**.

```python
return FIXED_KARANA.get(num) or KARANA_NAMES[(num - 2) % 7]
```

`VISHTI_KARANAS` is now **derived** from the seven movable names rather than typed,
so the layer holds an answer the document's own prose — *"the eight windows of each
lunar month fall on karana numbers 8, 15, 22, 29, 36, 43, 50, 57"* — is able to
contradict. It did. That sentence is what found this; no check did.

##### The blast radius, measured rather than estimated

Every figure below was measured against the build of 20-Sep-2026, the counterfactual
column by re-introducing the defect in memory and re-running.

| what consumed the numbering | with the defect | as shipped |
| --- | --- | --- |
| `panchang.karana_name(57)` | `Shakuni` — printed twice a lunation, seven Vishtis where the source names eight | `Vishti` |
| `VISHTI_KARANAS`, derived from it | **7** numbers | **8** |
| `sub_bhadra`, whose selection is that set | **86 of the section's 99** printed windows; 13 never reproduced | **99 of 99** |
| its verdict rows, 2027 | **639** | **743** |
| total verdict rows | 7,397 | **7,501** |
| rows in the artifact | 7,802 | **7,906** |
| the 2026 monthly fixture | **239 of 354** windows, 3,334 Mumbai firings | **246 of 354**, 3,352 |
| `panchang.karana` on the astronomy records | **101 blocks in 2027 and 85 in 2026** read `Shakuni` over a Vishti karana | correct in both |

Two things are worth reading off that table rather than through it.

**The artifact carried it and the calendar did not.** `karana` is on every panchang
block of `build/astronomy_2027.json` and `build/astronomy_2026.json`, and 186 blocks
across the two years named a Vishti `Shakuni` — but no rendered calendar column
reads the panchang block, so `calendar_2027.{json,html,csv}` never printed the wrong
name at all. The visible cost was entirely in the SELECTION the name fed, not in the
name: **13 windows the source prints that the calendar would have omitted, with
nothing anywhere saying so.** A defect in a field nobody renders is not a harmless
defect; it is a defect that can only be found downstream of itself.

**Nothing published was measured over the wrong set.** Every Bhadra figure this
build carries — 99 of 99, 743 rows, 7,501, 246 of 354, the five clip-census figures
that moved by exactly 5, the 62 extra days on `panchang/karana` — was taken after
the fix, and both astronomy artifacts on disk carry the post-fix sha256 and name
karana 57 `Vishti`. The counterfactual column above exists only in memory. **No
published number is retracted by this entry**, which is the first question a reader
of §12.16 should ask and the one it does not usually get a clean answer to.

##### What the harness would have done, and what it now does

While the defect was live the five suites were green and would have stayed green.
`test_bhadra_two_printings` runs on its own numbering, and the Bhadra port's **99 of
99 was established before the wiring and pinned by nothing** — while the two ports
either side of it were pinned in
`test_the_subtable_ports_reproduce_their_own_printed_tables`. A verification that
lives only in a rule's `notes` is a verification that cannot fail.

**Four detectors are landed, not proposed, and every one was run against the defect
before it was believed.**

| the check | where | on the defect |
| --- | --- | --- |
| Bhadra's 99 printed windows reproduce on both boundaries within 30 s, **by firing the registered rule** | `test_the_subtable_ports_reproduce_their_own_printed_tables` | **FAIL** — 87 matched, 12 printed rows missed |
| karana 57 is derived as a Vishti, and its 12 windows in 2026 are printed windows | same | **FAIL** — `VISHTI_KARANAS` has 7 members and 0 windows on 57 |
| the test's own literal eight must equal `panchang.VISHTI_KARANAS`, every window it finds must be one `karana_name` also calls Vishti, and the four fixed karanas must sit on their own numbers | `test_bhadra_two_printings` | **FAIL**, all three clauses — while the seven original clauses of that same test still PASS |
| every **executable** sub-table rule is pinned against its own printed table, the set read off the registry | `test_every_ported_subtable_rule_is_pinned_against_its_printed_table` | **FAIL** on the build as it stood this morning, naming `sub_bhadra` as the unpinned one |

Suites: `test_rule_layer` **256 → 260**, `test_2026_regression` **120 → 123**.

The third row states the shape's remedy exactly. **The parallel implementation
stays** — it is a genuinely independent witness, and answering "which of the
source's two printings is right" with the layer's own code would answer it with the
layer. What changed is that it is **reconciled**: the local literal and the shared
function must agree, and every window the local walk finds must be one the shared
function also names Vishti. A parallel path is an asset; a parallel path that never
meets the production one is this section's fourth shape.

The fourth row generalises it past Bhadra, and it is the eighth instance's
discipline applied here: the executable set is **discovered** from
`SUBTABLE_REGISTRY` rather than listed, so the next port that lands with its
verification in prose fails a check instead of joining Bhadra in being verified once
and watched never.

**And one direction of the 99-of-99 check is no help at all, which is the detail to
keep.** The bidirectional form — no fired window left unmatched to a printed row —
**passed on the defect**: 87 fired, 87 matched, nothing over-firing. Under-firing is
invisible from our side of the comparison and visible only against the document's
denominator. That is the third shape's lesson arriving inside the fourth shape's
territory, and it is why `BHADRA_PRINTED` is sliced out of the section at import
rather than counted off the series.

##### The discipline this argues for

> **Name the function the check is supposed to cover, and make the check call it.**
> A test that recomputes is testing a reading of the document. A test that calls is
> testing the build. Both are worth having; only the second fails when the build
> breaks, and a suite of the first kind is a suite that would be green over any code
> at all.

**And the obvious question is the wrong one, which is worth stating because it was
asked first and measured.** "Did the suite execute this function" does not separate
the two cases. Every module-level function of the package was wrapped with a counter
and the five suites re-run: `panchang.karana_name` was executed **1,013,396 times**
by `test_2026_regression` alone, through `panchang.at` inside the weekday-condition
walk. **Execution coverage was total and assertion coverage was zero.** The function
ran a million times under a green suite and not one check ever looked at what it
returned. A coverage tool would have reported this file as covered on the day the
defect shipped.

So the questions are about the ASSERTION, not the execution:

1. **Where did the value this check compares against come from — the build, or a
   second implementation living in the test file?** That is the whole distinction.
   A check whose expected side is the document and whose actual side is also the
   test file has closed a loop that the build is outside of.
2. **Would it fail if the function it is named after were wrong?** For
   `test_bhadra_two_printings` on 19-Sep-2026 the answer was no — demonstrably, since
   the function *was* wrong and it did pass. `panchang.py`'s karana naming could have
   been deleted outright and the suite would have stayed at full marks.
3. **If a parallel implementation is wanted as an independent witness, what ties it
   to the shared one?** Not "does it agree with the document" — both do. The tie has
   to be an assertion that names both paths.

**The through-line with the seventh and eighth instances is that all three are
defects in CHECKS, and together they are a progression**: the seventh read the wrong
input, the eighth walked the wrong population, and this one ran the wrong program.
Each is invisible in the same way — the check reports `[PASS]`, and a boolean is the
one output of this build that carries no evidence of what produced it. §12.16 has
now spent three of its entries on the instruments rather than on the build, which is
its least comfortable result and the one most likely to transfer.



---

### 12.17 The base track, and the discriminator that had to come first · recorded 15-Sep-2026

The calendar held **verdict rows only**: one rule, one instrument, one venue civil
day, 6,677 of them. It now also holds the **base track** — 405 rows, one per core
astronomy record, the sky rendered as itself. Three arguments were made for it and
the third is the strongest.

1. *The sky is not a verdict, and the calendar showed only verdicts.* An ingress is
   not a claim about gold.
2. *Rejoinability.* Every base-track row carries the astronomy record's own `id`
   and its `t_utc`, so a reader checking the calendar against the ephemeris matches
   on a key rather than on an event name and a date.
3. **A calendar that cannot be empty cannot report absence.** A day with no row is
   a measurement — nothing the layer tracks happened — and without a base track
   there was no way to tell that from *nothing was computed*.

#### The discriminator is a precondition, and that is the whole shape of it

`row_kind` was specified and put on every one of the 6,677 existing rows **before a
single base-track row existed**. Not as tidiness. Without it the 405 rows land in a
file where `records` goes 6,677 → 7,082, `rows_without_verdict` absorbs 405 rows
that were never candidates for a verdict, and — worst — `by_tier.no_rule` acquires
them, because `tier_derivation` maps `(evidence_source: none, construction: null)`
to `no_rule` and an event row has exactly that pair. **3,285 would become 3,690 and
still be called `no_rule`.** Every meta figure in the file would have changed what
it meant while looking unchanged.

That is the stale-denominator failure for the **third** time in this build, after
the `family`-read-two-ways fix and the label-attached-per-section fix (§12.16, and
`source_probability.corrections_on_record`). The rule taken from those two is
written into `row_kinds` in the config: *a discriminator is a precondition for the
population it discriminates, never a follow-up.*

`BaseEvent` **has nowhere to put a verdict.** It is not a `Verdict` with the
interpretive fields nulled: it has no `instrument`, `tier`, `claim_tag`,
`construction`, `verdict_text`, `source_probability` or `confidence` attribute. The
harness checks the rendered dict anyway — a dataclass cannot stop a renderer adding
a key by hand — and `basetrack.FORBIDDEN_FIELDS` is that list. The first run of
`html_calendar.py` against the mixed rows raised `KeyError: 'tier'`, which is the
guarantee working: the file counted tiers over every row and there was no longer a
tier on every row.

#### What the empty-day argument turned out to measure

The argument was made with a figure of 32 empty days. **Measured against this build
it is not 32 and not one number but three:**

| measure | days of 2027 |
| --- | --- |
| carry no **event** row | **105** |
| carry no row **of any kind** | **0** |
| carry no row carrying a **verdict text** | 2 |

Zero, because `tier_4` emits a verdict-null `USDINR` row for every catalogue-B
firing and those blanket all 365 days. **The combined calendar is never empty.**
Absence is reportable on the base track and only through `row_kind` — filter to
`row_kind=event` and the 105 days appear; read the calendar whole and they do not.
That is a second use for the discriminator which the argument for it did not
anticipate, and it is recorded rather than folded into the original claim.

#### Eclipse rows name their contact

An eclipse record carries `contacts_global` fully stamped: begin, maximum, end, and
for a central eclipse both totality contacts — three for a penumbral lunar eclipse,
five for a solar one. A row emitting **one unlabelled time** was choosing one of
those and not saying which. Each of the five 2027 eclipse rows now names **first
contact and maximum**; the rest stay on the record, which the row names by id.
First contact is keyed per family and not taken as the earliest entry in the dict —
a solar eclipse's is `begin`, a lunar eclipse's is `penumbral_begin` — because
picking by time would silently rename the contact the day a record carries a new one.

#### The rows that printed a time that did not exist

Every row now carries `t_utc`, or `t_start_utc` and `t_end_utc` where the condition
holds over an interval. That is the rejoinability half. The other half is harder,
and it is the one the finding was actually about: **every row without an instant
printed `00:00 IST` beside a previous-Eastern-day afternoon, and not one of them
was an event at midnight.** Four causes, three of which were already marked in data
nobody was reading:

| cause | catalogue-B firings | rows | what the start actually is | was it marked? |
| --- | ---: | ---: | --- | --- |
| `date_only` astronomy records | **331** | 431 | the ephemeris emits a **date** — kalamsha is a horizon measurement | yes, `time.precision` |
| `civil_day_span()` | **105** | 255 | a venue's midnight. Calendar arithmetic | no |
| carry-in cut | **142** | 151 | `sky.span_start` — the **generated period's** edge | yes, `open_start` |
| synthetic anchor | **11** | 12 | `datetime(2027,1,1, tzinfo=IST)` — a date **this build chose** | only in `detail.anchor` |

Whole population on the rendered artifact, which is where it is checkable:
**894 rows over 99 spans** — 858 verdict and 36 event, 9 of them
configuration-sourced. `meta.time` publishes it.

**THE FIGURES IN THIS TABLE ARE NOT THE ONES IT WAS WRITTEN WITH, and the
correction is its own instance of the shape this section is about.** It read
*`249 / 45 / 147 / 12 firings`* over *662 rows across 27 rules*, and a later
report replaced three of those with *`331 / 282 / 105 / 11`*. Both sets were
withdrawn and the four above were re-derived. What the re-derivation found:

* **Nothing moved because the population moved.** The same rule families counted
  against the pre-wiring, pre-base-track 5,209-row build give the same figures.
  The base track and the configuration wiring together added 45 rows to the
  no-instant population, none of them catalogue B.
* **A unit travelled without its figure, twice.** `45` was the Mumbai half of
  `105` — `b101` is `per_location` and fires 45 times at Mumbai and 60 at New
  York. `12` counted **rows** where its three neighbours counted **firings**; 12
  rows and 11 firings are both correct and neither changed. The original table's
  own column header said "firings" for three columns and "12 rows" for the
  fourth, which is how far a mixed unit travels unnoticed.
* **`282` was the FIRST cause measured on a second key, filed under the SECOND.**
  It is the count of distinct `(venue, date)` pairs among the 471 `date_only`
  ephemeris rows. The correct carry-in figure is 142.
* **`249`, `147` and `662` are diagnosed as nothing.** They reproduce against no
  slicing of this build or of the one before it. They and `no_instant_reason`
  were born in the same commit, measured against a transient render that was
  never committed.

**And that is the lesson, which is not the one this section already carries: a
figure without a generator is not a measurement.** Both withdrawn sets were
written by hand into prose and neither was ever read by a check. The four above
are **keys** in `conventions.yaml` (`row_kinds.time_fields.the_four_causes_were_re_derived`)
and `tests/test_rule_layer.py` recomputes them off the artifact.

**The fix is structural rather than disciplinary, and it had to be.** There was no
way to write the renderer that did not print a clock time, because the object it
was handed had one: `stamp()` returns a `DualStamp` and a `DualStamp` always has
`ist_time`. So `timezones.DateStamp` was added — dates and weekdays, **no time
attribute at all** — and `_time_fields` hands a row one object or the other. Code in
the no-instant branch that reaches for a clock time raises `AttributeError` at build
time. A row without an instant is not discouraged from printing one; it cannot.

Each such row prints **why** instead, and the why is four values rather than a
boolean, because the remedies differ: `date_only` would need a new ephemeris scan,
`period_cut` a wider generated span, `anchored` cannot be remedied at all, and
`named_contacts` is not a shortage — the row has more times than one field can hold.

**And the display string was not the test.** `b102_anuradha_on_sunday` on
03-Oct-2027 is a nakshatra ingress at **00:00:21 IST** — a genuine instant that
happens to render as `00:00`. No rule phrased over the printed string could have
kept it while dropping the rows that have no instant at all, which is the same
lesson as the per-rule label census, in a different layer: *the artifact's surface
is not the thing to test; the property behind it is.* (The counts this paragraph
carried — 663 across 28 by display string, 662 across 27 structurally — are
withdrawn with the rest; the principle does not depend on them.)

---

### 12.18 Test 3 recounted against all three catalogues · recorded 15-Sep-2026

`b_counts_ruling` decided that catalogue B counts for transfer test 3, and gave
this reason: *excluding them because the astronomy layer has not reached them yet
would make the answer depend on BUILD ORDER rather than on evidence.* The 58
instrument configuration groups were ported after that ruling was written. Leaving
them out is the same dependence on the order we happened to do the work, so test 3
is now evaluated against **A, B and C**.

**The arithmetic does not move: 19 / 12 / 12 / 1 stays 19 / 12 / 12 / 1.** And that
is not the interesting part. Adding a catalogue can only turn a test-3 *failure*
into a pass, and the tests are **ordered** — a block failing test 1 or test 2 never
reaches test 3 — so 24 of the 25 failures cannot move under any catalogue. Only the
single orphan and the 19 passes were re-evaluated.

#### What actually changed: one pass acquired the ground it never had

All eleven carried families were re-tested against all three catalogues, not just
the disputed one. Ten pass exactly as recorded — seven through catalogue A
(`conj_sun_mercury`, `conj_mercury_venus`, `conj_venus_uranus`, `combust_venus`,
`combust_saturn`, `combust_jupiter`, `rise_venus`) and three through B
(`mercury_venus_alone`, `venus_jupiter_same_sign`, `mars_ahead_of_jupiter`).

**Block 13, `rahu_mars_together`, is the exception, and it was recorded as
catalogue B.** It is not in catalogue B: **zero of the 141 `h3.section` titles name
Rahu and Mars together.** It is not in catalogue A either — the astronomy layer
emits no conjunction or opposition record for a node, so no Rahu pair exists among
the 26 emitted families. **Under catalogues A and B alone, as this project's own
`catalogue` fields are written, the arithmetic is 18 / 12 / 12 / 2.**

So the recorded 19 was correct and the reason given for it was not. Catalogue C is
what makes it true: *Rahu Mars Together in Any Sign* is gold-bullish group 3 and
silver-bullish group 26, and the family's `rules` list has named
`cfg_gold_bullish_03` and `cfg_silver_bullish_07` since the per-rule attachment
landed. **The recount does not change the count; it supplies the count's missing
ground.** `catalogue` is corrected to `[C]` with `catalogue_was: [B]` beside it.

#### The orphan stays an orphan

Block 4, *Mars (Sagittarius) Tenth to Saturn*, fails test 3 under all three.

* **A** — no relative-house family among the 26 emitted `rule_family` values.
* **B** — no relative-house section among the 141. Zero titles match *tenth*,
  *twelfth*, *10th*, *12th*, *house* or *aspect*.
* **C** — exactly one candidate, and it is **declined**: gold-bullish group 6, *If
  Mars is Aspected by Saturn and Jupiter is Retrograde*. Mapping block 4 onto it
  takes three re-derivations — asserting the Parashari special aspect (Saturn
  aspects its 3rd, 7th and 10th) that the source states in neither place, dropping
  the group's Jupiter-retrograde conjunct, and reading a **one**-position condition
  as a **three**-position one. A narrower condition mapped onto a broader group and
  called the same family is the group-key-for-a-member-key error running backwards.

**And its twin settles it.** Block 12, *Mars Twelfth to Saturn*, carries VERY HIGH
and is the same shape. The twelfth is not a Saturn aspect position at all, so the
identity that would rescue block 4 leaves block 12 exactly where it is. A family
that receives one relative-house label and not its twin is not a family.
`do_not_create_a_family` stands.

#### Two things found while recounting

**Catalogue A's recorded size is stale: 20, measured 26.** It has no effect on the
recount — none of the six families added since is a relative-house or node
colocation family — and it is recorded anyway, because `catalogues.A.count` is a
figure about the *current build* that was written once and never re-derived. That
is the same shape as every other stale denominator in this file.

**And the first version of the harness check for this recount passed for the wrong
reason.** It pulled every digit out of `"19 pass / 12 fail test 1 / 12 fail test 2 /
1 orphan"`, collected `[19, 12, 1, 12]` — the `1` and `2` are the *test names* —
and summed to 44 anyway. Caught by printing what it had read rather than whether it
had passed. The figures are now stated as figures (`counts_before`,
`counts_after`), and the prose line is prose. **A check that passes for the wrong
reason is the subject of §12.16 happening inside the file that documents it**, and
it is recorded there as that section's **seventh instance** -- the first in which
the check, and not the code it checked, was the thing that was wrong.

#### `actual_figures_2026`'s 344 stays labelled stale

Re-measuring it means flipping `CONF["year"]` and rebuilding the whole layer against
2026. A stale number honestly labelled costs less than a year-flip at this point in
the work, and the label already says what it is: measured under the section-level
attachment, which is the defect §12.16's sixth instance records.


---

### 12.19 The two span blockers, settled before the collapse · recorded 15-Sep-2026

`build/SPAN_VS_DAILY_PROPOSAL.md` §5 named three things that had to be decided
before any collapse. Two of them are decided here and **landed on the daily rows**,
for the reason `row_kind` landed first: a discriminator added after a collapse
changes the population every earlier figure was measured over. The third — the
HTML date filter becoming an overlap test — belongs to whoever implements the
collapse, because it is a property of the collapsed view and of nothing that
exists yet.

#### A span's displayed end is the last day it holds

Spans are half-open, `[start, end)`. `b101`'s February Mumbai window ends at
`2027-02-20T18:30:00Z`, which **is 21-Feb-2027 00:00 IST**, and the last civil day
the condition holds is **20-Feb**. `sky.civil_days` already gets this right —
`Span.overlaps` tests `lo < end`, and `lo == end` on 21-Feb — so the daily render
has never been wrong about it. **A collapsed row that stamped `t_end_utc` would
be, on 251 of the 1,626 span groups in this build**, in the direction that makes
every window one day longer than the daily rows it replaces.

**Ruled: both representations are emitted, under names that cannot be confused.**
`t_end_utc` is the instant the condition ceases and is EXCLUSIVE; `last_held` is
the last civil day it holds and comes from `sky.civil_days(...)[-1]`.

**And the ruling is a type rather than a convention, which is the only reason to
trust it.** `timezones.SpanDates` is built only by `span_dates(days)`, which takes
the civil days the rows were built from and **raises `TypeError` on a
`datetime`**. `datetime` is a `date` subclass, so an unguarded list would have
accepted `[t_end_utc]`, rendered 21-Feb, and raised nothing. This is precisely
what `DateStamp` did for clock times one batch earlier, and the reason is the same:
a rule the renderer merely *follows* is a rule the next renderer can drop.

`SpanDates` also carries `days_in_view = len(days)` and a `contiguous` flag,
because **179 of the timed span groups are not contiguous** — a weekday-filtered
rule's days have holes — and a window over one of those would claim days no row
was ever built for. All 99 no-instant groups are contiguous, so Model A is
unaffected; the flag exists before Model B does, deliberately.

**The check was falsified both ways before it was believed**, per §12.18's lesson.
`test_a_spans_displayed_end_is_the_last_day_it_holds` fails if a displayed end is
taken from `t_end_utc` (the type raises), and fails equally if `span_dates` is
"corrected" to agree with `t_end_utc`, because it also asserts the two **disagree**
on a counted set of 251 windows. A check that asserted only the convention would
have passed on a build that had no convention at all.

#### `open_*` was standing in for a second cut it does not describe

`open_start` / `open_end` mark **`Sky.span_start`'s** edge: the condition was
already running when the generated period began, so there is no boundary. They do
**not** mark `fire()`'s second cut, `civil_days`' drop of days outside the calendar
year. A daily render needs no field for that — the out-of-year days simply have no
rows and nothing is claimed about them. **A collapsed row asserts an extent**, and
then one printing the true boundary starts before the file does while one printing
the first day in view asserts a boundary the sky did not supply.

**Ruled: `clipped_start` / `clipped_end`, on all 7,082 rows now.** Computed once
per (span, location) by `sky.year_clip`, carried on `Firing` and `Verdict`, emitted
by `render._time_fields`. The condition's true boundary stays on `t_start_utc` /
`t_end_utc`, the in-year extent is `SpanDates.first_held` / `last_held`, and the
flag says which a reader is looking at. Neither is dropped and neither is chosen
silently.

**The two cuts are independent, which is what a single flag could not express.**
`b009_mercury_combust_cycle`'s carried-in window is `clipped_start` and **not**
`open_start` — Mercury genuinely went combust on 13-Dec-2026, so the boundary is
real and measured, and the calendar's first row for it is 01-Jan-2027. The three
carry-in windows are **both**: the period cut them and the year clips them.

#### And the figure this was raised against was also wrong

The proposal reported **22** spans with a real endpoint outside 2027 and `open_*`
false, 1 no-instant and 21 timed. **22 is the count of `clipped_end` groups alone**
— it omits the 10 `clipped_start` groups and does not apply the `open_*` filter its
own sentence states, so 5 of its 22 are already marked `open_end`. Measured off the
field, over 1,626 span groups: `clipped_start` 10 (7 with `open_start` false),
`clipped_end` 22 (17 with `open_end` false), **24 spans with a real endpoint outside
the year — 1 no-instant and 23 timed**. 18 under the rule-span unit, which does not
repeat a window per instrument.

**That is the third figure in this batch to be a real count of the wrong set**,
after `282` and the `45`/`12` unit mix in §12.16. All three were arithmetic nobody
disputed over populations nobody stated. The census now lives in
`conventions.yaml → row_kinds.time_fields.year_clip.measured_2027` as eight named
keys, and `test_the_civil_year_clip_is_a_field_and_not_the_period_cut` recomputes
each one off the artifact and **prints what it read**.
