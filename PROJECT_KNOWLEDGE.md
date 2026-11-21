# FinAstro 2027: project knowledge base (gold and silver work)

This is the single place to start. It records every source, decision, method and finding from the gold and silver work of 19–21 Nov 2026, and the commands that rebuild every output. It was last updated 21 Nov 2026.

The work is logged entry by entry in `build/pdfref/analysis_log.json`, which is shown in both trackers. The 2027 calendar build from before this work is described in `README.md` and `build/NEXT_SESSION.md`.

## 1. Conventions (fixed for all gold/silver work)

| Item | Convention |
|---|---|
| Time zone | US Eastern (America/New_York, EST/EDT) in every report; IST only alongside in the NY master calendar |
| Zodiac | Sidereal, Lahiri ayanamsa (Swiss Ephemeris, `ephe/`), geocentric |
| Nodes | Mean node; Rahu and Ketu always retrograde |
| Aspects | Whole-sign graha drishti: every planet 7th; Mars 4/8, Jupiter 5/9, Saturn 3/10; Rahu 7th only; Ketu by conjunction only |
| "With / together" | The same sidereal sign |
| Hindu day | New York sunrise (Mumbai for Indian festival and darshan cross-checks) |
| Darshan | First sunset with elongation ≥ 12° and Moon age ≥ 20 h |
| Event detection | Hourly grid, boundaries bisected to 30 s; each boundary checked against the astronomy layer within 3 min |
| Prices | COMEX continuous front month from Yahoo Finance: gold GC=F, silver SI=F |

## 2. User decisions (respect these in future work)

1. **Implement rules only when a source states them.** The user declined extrapolations "without having the full picture", for example a Moon-based mirror of the gold Sun rules for silver.
2. **Bayer and the Western sources are excluded:** McWhirter, Williams, Weingarten, Timing Solutions, and the 'Moon and Silver' guide, which is built on the Timing Solutions / RBS lunar method. They are reviewed in `OTHERS_FINANCIAL_REVIEW.md` but not implemented.
3. **Vedic sources are implemented:** TA, KD, the 2026 document, the user's Sun notes U1–U4, and Brihat Samhita Ch.41–42 and 10.17.
4. **Brihat Samhita 41.9–13** is implemented through **Financial Astrology Model v1.0**, using the methodology the user supplied:
   - "costly and scarce" means scarcity price pressure (bullish);
   - "thrive, fetch good price" means the demand/value index;
   - "strong" means Shadbala at or above the BPHS requirement.
5. **Silver has no sign in Brihat Samhita Ch.41**, so the Model v1.0 reading for silver is "Insufficient data". Do not assume Cancer.
6. **Reports are tracked and kept up to date.** Every analysis gets an entry in `build/pdfref/analysis_log.json`. The user asks "Create PR and merge" when a round is done; work is developed on branch `claude/affectionate-goldberg-fhy3zb`.

## 3. Sources and where they live

| Source | Files | Status |
|---|---|---|
| TA: *Tech Astro Analysis* (2020, 265 pp.) | `Reference_materials/Tech Astro Analysis…pdf`; extraction in `Reference_materials/extracted/TA_*.html`, `TA_verified_transcriptions.md` | Every computable rule is in `finastro/pdfref/catalogue.py` |
| KD: *Parth Prophecies* deck 2026 (223 pp.) | `Reference_materials/KD Final PPT PDF 2026.pdf`; `extracted/KD_*.html` | In the catalogue |
| 2026 document (*Parth Prophecies 2026*) | `data/source_2026.html` | Configuration rules (`finastro/rules/`); gold/silver extras (`doc26_*`) in `tools/build_metal_report.py` |
| Kindle chapters (Ch.0–20) | `Reference_materials/Kindle_*.html` | Context. Ch.15: Sun → gold and Moon → silver are the only classical metal rulerships; Indian festival-demand dates (`kindle15_*`, not scored) |
| User's gold notes U1–U4 | `Reference_materials/user_notes_gold.md`, `finastro/pdfref/user_rules.py` | Implemented, with a conflict note on every row |
| `Reference_materials/Others` (45 files) | `extracted/OTHERS_FINANCIAL_REVIEW.md`; OCR of the 3 scanned books in `extracted/ocr/` | Only Brihat Samhita implemented (Section 5); BPHS used for Shadbala |
| Brihat Samhita, tr. P.S. Sastri 1946 | `Others/jyotish_brihat-samhita…pdf` | 42.14a/b, 10.17, 42.6 in `finastro/pdfref/bs_rules.py`; 41.9–13 in `finastro/pdfref/bs41_model.py` |
| BPHS, tr. R. Santhanam | `Others/BPHS/BPHS - 1 RSanthanam.pdf` Ch.27 | Shadbala in `finastro/pdfref/shadbala.py` |

Known data problems:
- `bayer_all_48_rules.docx`: Rules 25–48 are not Bayer's 1940 rules.
- Duplicate PDFs: BPHS volume 2 appears twice; two Sharad Joshi PDFs appear twice.
- The exaltation-table image has wrong glyphs; its sign names are correct.
- The Moon's Shadbala requirement is 360 virupas (BPHS 27.32), not 370.

## 4. Code map

| Path | What |
|---|---|
| `finastro/pdfref/engine.py`, `detect.py` | Ephemeris snapshot, grid, window/crossing detection, Hit/Ctx |
| `finastro/pdfref/catalogue.py` | All TA/KD rules, about 734 entries; imports `user_rules` and `bs_rules` at the end |
| `finastro/pdfref/vedha.py` | TA vedha wheel, 2026 label mapping, Atichari levels |
| `finastro/pdfref/user_rules.py` | U1–U4 (gold, Sun) |
| `finastro/pdfref/bs_rules.py` | Brihat Samhita 42.14a, 42.14b, 10.17, 42.6 |
| `finastro/pdfref/shadbala.py` | Shadbala (BPHS Ch.27) and Ashtakavarga (BPHS Ch.66); `convention="bphs"` or `"raman"` |
| `finastro/pdfref/bs41_model.py` | Financial Astrology Model v1.0 (gold) |
| `tools/build_metal_report.py gold\|silver` | Reports, 20 Nov 2026 – 31 Dec 2027 (ET) |
| `tools/build_pdf_calendar.py` | NY 2027 master calendar (json, csv, html, ics) and Moon layer |
| `tools/backtest_gold.py [--metal silver] [--years N]` | Rule backtests against COMEX closes |
| `tools/test_source_rules.py` | Tests of the 'Others' rules, 2000–2026 |
| `tools/build_bs41_model.py` | Model v1.0 calendar and 2000–2026 backtest |
| `tools/gold_tracker.py [--metal silver]` | Trackers: findings, rule status, best-rule dates, analysis log |
| `tools/build_year.py YEAR` | Astronomy layer for any year; 2021–2024 are git-ignored and rebuilt on demand |
| `tools/fetch_prices.py` | Downloads GC=F and SI=F (Yahoo; the host must be allowed) |
| `tools/refresh_all.py [--prices]` | Rebuilds everything in order and runs the tests |
| `tests/test_pdfref.py`, `tests/test_shadbala.py` | PDF-rule checks; Shadbala vs B.V. Raman's worked example |

## 5. Outputs (`build/pdfref/`)

| File | Content |
|---|---|
| `gold_2026-11-20_to_2027-12-31_ET.html` / `silver_…` | Every gold or silver rule's dated windows, each checked against the astronomy layer |
| `calendar_2027_NY_master.*` | NY 2027 calendar: all PDF rules plus the existing calendar |
| `gold_backtest_2021-11-20_to_2026-11-20_ET.html` (and `2025-11-20` for 1 year; `silver_…`) | Rule backtests |
| `source_rules_test_2000-2026_ET.html` | 26-year test of the Brihat Samhita, Timing Solutions and Silver guide rules |
| `gold_bs41_model_2026-11-20_to_2027-12-31_ET.*` | Model v1.0 daily readings, calendar (ics) and backtest |
| `GOLD_TRACKER.html`, `SILVER_TRACKER.html` | Current status of every rule, best-rule dates, analysis log |
| `REFERENCE_PDF_RULES.md`, `COMPLETION_REPORT.md`, `COVERAGE_AUDIT_GOLD_SILVER.md` | Rule lists and audits |

## 6. Backtest method (for comparing any new rule)

- **Entry** is the last close before the event. An event at or after 17:00 ET counts from the next session; a day-rule counts from that day's open.
- **Windows of 3 days or more** are scored from entry to the last close inside the window. **Instants** are scored on the 5-trading-day move.
- A move under ±0.5% is FLAT.
- **Hit rate** is worked ÷ (worked + failed).
- **Base rate** is the share of same-length moves in the same Nov–Nov year that went the rule's way. A rule gets no credit for riding the year's drift.
- **Verdicts:**
  - Worked: hit rate at least 10 points above base and the average move in the stated direction.
  - Failed: at least 10 points below base and the average move the wrong way.
  - Otherwise Mixed.
- For each rule the report also shows a one-sided binomial p-value and its result year by year.
- **Daily-factor tests** (2000–2026) score each COMEX session (18:00 → 17:00 ET) by the condition holding in at least half of its hours.

## 7. Findings (as of 21 Nov 2026)

**Rule sets as a whole (5 years, 20 Nov 2021 – 20 Nov 2026):**
- Gold: 308 worked / 279 failed (52%), against 54% expected by chance.
- Silver: 201 / 219 (48%), against 50%.
- No rule beats chance at p < 0.05.
- Adding up the bullish-minus-bearish count each day carries no information for gold. For silver it pointed the wrong way.

**Gold: most consistent rules (5-year data; dates in `GOLD_TRACKER.html`):**

| Rule | Worked / decided | Rate vs base | p | Years right |
|---|---|---|---|---|
| Combined Sun model U1–U4 | 105 / 179 | 59% vs 52% | 0.057 | 3 of 5 |
| U2 – Jupiter with / aspecting the Sun | 15 / 21 | 71% vs 61% | – | 4 of 5 |
| U2 – Venus with the Sun | 18 / 27 | 67% vs 57% | – | 4 of 5 |
| U2 – Mercury with the Sun | 36 / 55 | 65% vs 57% | – | 4 of 5 |

**Gold rules that did not hold up:**
- U4 – Saturn on the Sun: 6 / 20. It looked good only in the falling 2025–26 year.
- New Moon bullish: 21 / 48.
- Mercury rises in the West: 4 / 13.
- Sun on Anuradha with a benefic: 1 / 6.
- Sun in Libra with malefics: 2 / 6.
- Rise of Jupiter: 0 / 4.

**Gold, open gap:** bearish rules outnumbered bullish ones before only 1 of the 15 biggest 5-day falls. The January 2026 crash came with 6 bullish rules active and none bearish. Sun, Mercury, Venus and Mars were in Capricorn and Venus was combusting; no rule covers that configuration.

**Silver:**
- When gold moved against a silver rule, the rule failed 153 of 178 times. When gold moved its way, it worked 143 of 172. Silver rules mostly track gold.
- Best rule: Venus–Mars or Sun–Mars in one sign (19 / 30, 4 of 5 years).
- "Venus *alone* in Leo/Libra" worked 5 / 6, while "Venus in Leo/Libra" without "alone" worked 3 / 11.

**Moon and silver:**
- The rulership is sourced: TA p.32, Kindle Ch.15.
- No source applies the Sun-style rules to the Moon.
- The Silver guide's Moon rules showed no effect over 2000–2026, and new→full Moon holding did *worse* than full→new for both metals.

**Brihat Samhita (2000–2026):**
- 42.14a (lunation in Aries or Capricorn with a benefic) is a weak positive: 60% of 84 cases were followed by a rise.
- 42.6 (store gold and silver while the Sun is in Leo) shows no edge over drift.
- 10.17 (Saturn in Uttara Bhadrapada) has a single passage in the data; the current window runs to 7 Feb 2027.

**Model v1.0 (Ch.41 + Shadbala + Ashtakavarga), 6,572 trading days:**
- The correlation of the scarcity index with the next 5 days is −0.002.
- The model leans bullish on 67% of days by construction.
- Use it as classical context, not as a timing tool.

## 8. Open items

- Brihat Samhita 41.12 has a translation ambiguity: Sastri reads "fetch good price and have great demand", another translation reads moderate prices and easy availability. Kept visible; V is not a stand-alone signal.
- A rule for a stellium on the Sun (the January 2026 gap) has no source yet.
- Longer histories (2000–2026) exist for prices but not yet for the full rule backtest. Astronomy layers before 2021 would need `tools/build_year.py`.

## 9. Rebuild

    python tools/refresh_all.py --prices      # fresh prices, then every report, backtest, model, tracker and test
    python tools/refresh_all.py               # same, using the prices already in the repo

Then add an entry to `build/pdfref/analysis_log.json` for any new analysis, and re-run `python tools/gold_tracker.py` and `python tools/gold_tracker.py --metal silver`.
