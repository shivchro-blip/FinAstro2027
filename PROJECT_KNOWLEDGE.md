# FinAstro 2027: project knowledge base (gold and silver work)

This is the single place to start. It records every source, decision, method and finding from the gold and silver work of 19–21 Nov 2026, and the commands that rebuild every output. It was last updated 22 Nov 2026.

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

- **NYSE and USA foundation charts and the NYSE monthly solar-return technique are in scope** (24 Nov 2026). The user shared an astrologer's charts and forecast; reports call this material **Solar return**. The technique is reconstructed in `tools/nyse_charts.py` and is tested both the Solar return way (tropical) and ours (sidereal Lahiri). The user will keep sending updates; add them to the same tool and report.

- **Market prices and astrology only** (24 Nov 2026): news and fundamentals are not used or recorded. Explanations of market moves are astrological, and the market event log keeps prices, sky and conditions only.

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
| `tools/gold_deep_analysis.py [start] [end]` | Day-by-day gold analysis for a date range: rules with their 26-year records, transits, aspects, Model v1.0 and seasonality. A hand-written `..._notes.md` beside the output is rendered at the top |
| `tools/test_venus_visibility.py` | TA Section 18 Venus combust / rise rules on gold and silver 2000–2026, the January 2026 case and the next dates |
| `tools/big_move_analysis.py [threshold_pct]` | Gold's ±2% days 2000–2026: events within ±3 days, states and active gold rules vs a same-year expected count (Poisson, FDR) |
| `tools/big_move_forward.py [start] [end]` | Dates of the big-move leads from 22 Nov 2026 to 31 Dec 2027 with watch stretches (html, json, ics) |
| `tools/gold_outlook.py [start] [end]` | One timeline to end-2027: best-rule windows, volatility watch dates, Venus dates, month by month (html, json, ics) |
| `tools/fast_trigger_analysis.py [start] [end]` | Fast-planet triggers inside the watch windows (2000–2026 test with permutation check) and the narrowed forward days |
| `tools/gold_signal_table.py [start] [end]` | Simple gold table to end-2027: bullish / bearish / volatile, strength High / Moderate / Low, why |
| `tools/test_signal_table.py` | Backtest of the signal table's High / Moderate / Low (walk-forward 2013–2026, source rules only, in-sample) |
| `tools/metal_cfg.py` | `--metal silver` switch for big_move_analysis, big_move_forward, gold_outlook, fast_trigger_analysis, test_signal_table and gold_signal_table. Silver's big-move threshold is 3.5%, as rare as gold's 2%. Outputs are `silver_*` |
| `tools/market_events.py` | Detects every general-market rule event 2000–2026 (about 628 rules), takes about 30 min; writes the git-ignored cache `build/pdfref/backtest/market_events_2000-2026.json.gz` |
| `tools/backtest_market.py` | 26-year direction backtest of those rules on the S&P 500 and the Sensex, each in its own exchange time (16:00 ET; 15:30 IST); FDR; walk-forward; best rules' dates to end-2027 |
| `tools/market_summary.py` | Market findings page: robust big-move factors (q < 0.10, both halves, p < 0.01 without the 2008–09 and 2020 crashes) and their dates |
| `tools/calendar_rules_backtest.py` | Generates the original calendar's rule layer (`finastro/verdicts.py`; 2026 document catalogue B, configuration groups, sub-tables) for every year 2000–2026 and backtests it: SPX→S&P 500, NIFTY→Sensex, GC, SI; direction rules on direction, condition-only rules on big-day frequency. The cache in `build/pdfref/backtest/calendar_verdicts/` is git-ignored |
| `tools/market_signal_table.py` | Simple S&P 500 / Sensex bullish-bearish tables to end-2027. Rules qualify when p < 0.05 on one index and they beat the base in both halves on both indices. Strength High / Moderate / Low by p on the two indices; robust big-move factors are shown as Volatile |
| `tools/validate_external_model.py` | Check of an outside model's crash table and 2026–2029 roadmap: planet positions, its "signatures" on the S&P 500 1928–2026 (`spx_GSPC_daily_1928.csv`), and its windows against our tables and robust factors |
| `tools/day_report.py [YYYY-MM-DD]` | One day: positions, panchang, every active rule (gold, silver, general, calendar) with its 26-year record, our table signals, the watch windows and the actual moves. The latest report is published |
| `tools/sky_changes.py START END` | Every planetary change in a date range, in ET and IST: sign, nakshatra, pada and navamsa changes; tithi, karana (Bhadra) and yoga; aspects beginning and ending; exact degree aspects; rule starts and ends with their 26-year status; a daily position table |
| `tools/rule_tally.py [DATES]` | Net of active general-market rules with a good record per day, with a walk-forward test of the tally |
| `tools/trigger_study.py [--log DATE]` | Tests candidate fall and rise conditions day by day 2000–2026 on the S&P 500, Nasdaq, Sensex, gold and silver (same-day move, same-year base); checks Mars–Jupiter-with-a-node episodes on the S&P since 1928; keeps the market event log `build/pdfref/market_event_log.json` (big days with prices, sky and conditions) |
| `tools/nyse_charts.py` | NYSE (17 May 1792) and USA (4 Jul 1776, Sibly) natal charts, sidereal and tropical; transits to them; NYSE monthly solar returns (the Solar return tropical version and our sidereal one) with a 1928–2026 S&P backtest of the Solar return indications; the Solar return open forecasts |
| `tools/author_forecasts.py` | Scorecard of the Solar return forecasts (kept in its FORECASTS list), astronomy check of the transit statements, and 1928–2026 S&P tests of the degree-aspect rules (all days and each episode once) |
| `tools/dasha_transits.py [DATE]` | Vimshottari dashas of the USA and NYSE charts at all five levels (Maha, Antar, Pratyantar, Sookshma, Prana); the transit of each running lord; Pratyantar and Sookshma timelines with S&P moves; birth-time sensitivity; 1928–2026 S&P test of the lords |
| `tools/model_check_60d.py [END]` | Our tables' labels rebuilt for each of the last 60 days (gold, silver, S&P, Sensex), against the actual moves |
| `tools/combined_probability.py [END]` | Every layer joined into one probability per day (up today, up over 5 sessions, big day) by naive Bayes on log-odds; scored on the last 60 days and walk-forward 2013–2026. Caches `backtest/market_label_history.json.gz`; reads `backtest/{gold,silver}_label_history.json.gz` from `test_signal_table.py` |
| `tools/forward_daybyday.py [START] [END]` | Day-by-day forward page. For each day it shows:<br>• all transits and changes (from `sky_changes.py`)<br>• every active catalogue rule with its record, and the calendar-layer rows<br>• the four tables, watch windows, outlook, agreement and fast triggers, robust factors and Model v1.0<br>• USA/NYSE dashas (5 levels) and lord transits, gochara, Chandra and Tara bala<br>• the Solar return forecasts and rules, and the Mars–Jupiter–node lead<br>• combined probabilities |
| `tools/dasha_combinations.py [START] [END]` | Classical reading of the USA and NYSE dasha chains. Each Antar, Pratyantar, Sookshma and Prana lord is judged on:<br>• its relation to the parent lord (6/8, 2/12 vs kendra, trine, 3/11)<br>• natural friendship<br>• the houses it rules and its natal house<br>• its dignity<br>• its transit (house, malefics or Jupiter on its natal sign, transit dignity)<br>Tested on the S&P 1928–2026, and lists the coming combinations. `chain()` and `chain_score()` are used by `forward_daybyday.py` |
| `tools/solar_return_generate.py` | Generates the Solar return monthly NYSE charts (tropical 27°18' returns, New York) to Dec 2027.<br>• Readings use only the stated indications.<br>• Shows when the Solar return transit rules are active.<br>• Daily calls in the same style, calibrated on the 9 days Solar return called.<br>• Checked against Solar return's calls and against 1928–2026 |
| `tools/calendar_2026.py [START] [END]` | **The calendar** to 31 Dec 2026, one page. It shows:<br>• key dates and a calendar grid<br>• signal spans and the Solar return section<br>• each day in full: sky, the four markets, Solar return, every rule and calendar row with records, other analyses<br>• the track record and why the Sensex scored higher<br>• automatic verification checks<br>It uses `forward_daybyday.build()` and `solar_return_generate.py`, and replaces the forward day-by-day page |
| `tools/kartari_test.py` | Paap Kartari (B116 Mercury, B117 Jupiter; hemming as in config `valence.kartari`) and Shubh Kartari (exploratory). Shows when each occurs and tests it on the S&P and Sensex, 2000–2026: §6 method, both halves, big days, and a permutation check for B117 |
| `tools/kartari_jan2027.py` | B116 Mercury Paap Kartari in Jan 2027, S&P (ET) and Sensex (IST). Lists the windows and their sessions, describes every past window by B116's own conditions (Sun among the malefics, combustion, benefic aspect), and scores past windows matched to the January ones. Shown in the 2026 calendar's January 2027 section |
| `tools/doc_dec2026_check.py` | The 2026 document's December table checked: printed IST times against our ephemeris, presence in our calendar, and 2000–2026 S&P/Sensex records. It also tests the stated directions the calendar layer had not scored: Bhadra by the document's sec-142 tone rule, Moon–Mercury same D9, Rahu/Ketu nakshatra on Thursday, apogee/perigee, Mercury in Mula, Vargottam Mars, Mars ahead of Jupiter. Shown in the 2026 calendar |
| `tools/global_predictions.py` | Global Predictions, an outside forecast of the US market for 24 Nov – 5 Dec 2026. Keeps the calls (FORECASTS), checks the astronomy, scores the calls against the S&P (volatility windows against the trailing default rate), and tests the same configurations since 1928 (big days, sharp reversals, direction) through `author_forecasts.tests(conds)` |
| `tools/gold_tracker.py [--metal silver]` | Trackers: findings, rule status, best-rule dates, analysis log |
| `tools/build_year.py YEAR` | Astronomy layer for any year; 2000–2024 are git-ignored and rebuilt on demand |
| `tools/fetch_prices.py` | Downloads GC=F and SI=F (Yahoo; the host must be allowed) |
| `tools/refresh_all.py [--prices]` | Rebuilds everything in order, runs the tests, re-publishes `reports/` |
| `tools/publish_reports.py` | Copies the current HTML reports and calendar .ics files into `reports/` with an index |
| `tests/test_pdfref.py`, `tests/test_shadbala.py` | PDF-rule checks; Shadbala vs B.V. Raman's worked example |

## 5. Outputs (`build/pdfref/`; ready-to-open copies in `reports/`, start with `reports/index.html`)

| File | Content |
|---|---|
| `gold_2026-11-20_to_2027-12-31_ET.html` / `silver_…` | Every gold or silver rule's dated windows, each checked against the astronomy layer |
| `calendar_2027_NY_master.*` | NY 2027 calendar: all PDF rules plus the existing calendar |
| `gold_backtest_2000-11-20_to_2026-11-20_ET.html` (26 years), `…2021-11-20…` (5 years), `…2025-11-20…` (1 year); `silver_…` | Rule backtests |
| `source_rules_test_2000-2026_ET.html` | 26-year test of the Brihat Samhita, Timing Solutions and Silver guide rules |
| `venus_visibility_test_2000-2026_ET.html` | Venus combust / rise test 2000–2026 and the January 2026 gold crash |
| `gold_big_moves_2000-2026_ET.html` | Every ±2% gold day 2000–2026 with the sky ±3 days; which factors were over-represented |
| `gold_big_move_watch_2026-11-22_to_2027-12-31_ET.*` | Forward dates of the big-move leads, watch stretches, calendar (ics) |
| `gold_bs41_model_2026-11-20_to_2027-12-31_ET.*` | Model v1.0 daily readings, calendar (ics) and backtest |
| `gold_outlook_2026-11-22_to_2027-12-31_ET.*` | Combined outlook to end-2027, with the evidence for each item |
| `gold_fast_triggers_2026-11-22_to_2027-12-31_ET.*` | Watch windows narrowed to days with fast-planet triggers (html, json, ics) |
| `gold_signals_2026-11-22_to_2027-12-31_ET.html` | Simple bullish / bearish table with strength (scoring in the script's docstring) |
| `signal_table_test_2000-2026_ET.html` | Test of the signal table's strengths |
| `silver_big_moves_2000-2026_ET.html`, `silver_big_move_watch_*`, `silver_outlook_*`, `silver_fast_triggers_*`, `silver_signal_table_test_2000-2026_ET.html`, `silver_signals_*` | The same chain for silver |
| `market_summary_2000-2026_ET.html`, `market_backtest_2000-2026_ET.html`, `{spx,sensex}_big_moves_2000-2026_ET.html`, `{spx,sensex}_big_move_watch_*` | Stock-market work (S&P 500, BSE Sensex) |
| `market_signals_2026-11-23_to_2027-12-31_ET.html` | S&P 500 and Sensex signal tables |
| `external_model_check_ET.html` | Outside-model check (23 Nov 2026) |
| `nyse_usa_charts_ET.html` | NYSE / USA charts and the solar-return test. The shared chart image is kept in `Reference_materials/extracted/nyse_solar_return_charts_2026-10_2026-11.png` |
| `author_forecasts_ET.html` | The Solar return forecast scorecard and rule tests |
| `kartari_test_ET.html` | Paap and Shubh Kartari tested |
| `kartari_jan2027_ET.html` | Mercury Paap Kartari in Jan 2027, S&P and Sensex (also inside the 2026 calendar) |
| `global_predictions_ET.html` | Global Predictions calls, astronomy and tests |
| `solar_return_generated_ET.html` | Solar return generated by us: monthly charts, readings, transit rules, daily calls |
| `dasha_combinations_ET.html` | Dasha combinations: classical reading, S&P test, coming periods |
| `calendar_2026-11-24_to_2026-12-31_ET.html` | **The calendar to 31 Dec 2026**, the single current page |
| `daybyday_2026-11-01_to_2026-11-23_ET.html` | The same layers for 1–23 Nov, scored against the markets |
| `combined_probability_60d_ET.html` | All layers joined into daily probabilities, scored |
| `dasha_transits_ET.html`, `model_check_60d_ET.html` | Dashas with transits; the 60-day model check |
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

## 7. Findings (as of 22 Nov 2026)

The primary evidence is now the **26-year backtest (20 Nov 2000 – 20 Nov 2026)**. The 5-year and 1-year runs are kept as comparisons. Both trackers take rule status and "best rules" from the 26-year data.

**Rule sets as a whole:**

| Metal | 26 years | Chance | 5 years | Chance |
|---|---|---|---|---|
| Gold | 1,598 worked / 1,400 failed (53%) | 54% | 308 / 279 (52%) | 54% |
| Silver | 1,083 / 1,050 (51%) | 51% | 201 / 219 (48%) | 50% |

- No rule beats chance at p < 0.05 over 26 years.
- Silver's "Mars rising after combustion" is significantly *wrong*: 2 / 10, p = 0.03 for failing.
- The daily bullish-minus-bearish count carries no information: correlation with the next 5 days is −0.004 for gold and −0.024 for silver.

**Gold: the most consistent rules over 26 years** (the best-rule test: ≥15 decided, hit rate above base, and p < 0.10 or right in ≥70% of active years):

| Rule | 26 years | Rate vs base | p | Years right |
|---|---|---|---|---|
| TA S34 A9, Mars aspected by Saturn while Jupiter is retrograde | 14 / 17 | 82% vs 62% | 0.07 | 12 of 15 |
| U2 – Mercury with the Sun | 176 / 291 | 60% vs 57% | 0.115 | 20 of 26 |

There are no TA S34 A9 windows between now and 31 Dec 2027.

**Gold: the 5-year "best" rules faded over 26 years:**
- Combined Sun model: 509 / 939 (54% vs 53%).
- U2 – Venus: 75 / 134 (56% vs 56%).
- U2 – Jupiter: 65 / 104 (62% vs 57%, p = 0.17).

**Gold: did not hold up over 26 years:**
- Rise of Jupiter: 6 / 18.
- Venus in Jyeshtha with a benefic: 5 / 16.
- Mars in Pushya: 8 / 16.
- Sun in Libra with another malefic: 4 / 10.
- Sun enters Aquarius on a Friday: 1 / 5.
- U4 – Saturn on the Sun: 39 / 105 (37% vs 43%).
- New Moon bullish: 142 / 261 (54% vs 57%).

**Gold: open gap.** Bearish rules outnumbered bullish ones before only 1 of the 15 biggest 5-day falls of 2021–26. The January 2026 crash came with 6 bullish rules active and none bearish. Sun, Mercury, Venus and Mars were in Capricorn and Venus was combusting; no rule covers that configuration.

**Silver: the most consistent rules over 26 years:**

| Rule | 26 years | Rate vs base | p |
|---|---|---|---|
| TA S35 A1, retrograde Mercury or Jupiter | 78 / 126 | 62% vs 54% | 0.052 |
| TA S35 A17b, only Moon and Mercury alone in a sign | 49 / 80 | 61% vs 53% | 0.081 |

**Silver: the 5-year results that faded:**
- Venus–Mars or Sun–Mars in one sign: 74 / 144 (51% vs 54%) over 26 years, after 19 / 30 in 5 years.
- "Venus *alone* in Leo/Libra": 16 / 38 (42%), the same as the plain version (22 / 54).

**Silver: did not hold up over 26 years:**
- Saturn turns direct: 8 / 23.
- Jupiter turns direct: 9 / 21.
- Venus combust in the West: 5 / 13.
- Moon eclipse on Sunday: 2 / 11.
- Mars in Gemini with two other planets: 1 / 7.
- Mars rising: 2 / 10.

**Silver follows gold (5 years):** when gold moved against a silver rule, the rule failed 155 of 180 times. When gold moved its way, it worked 147 of 176.

**Moon and silver:**
- The rulership is sourced: TA p.32, Kindle Ch.15.
- No source applies the Sun-style rules to the Moon.
- The Silver guide's Moon rules showed no effect over 2000–2026, and new→full Moon holding did *worse* than full→new for both metals.

**Brihat Samhita, 26 years of the full backtest:**
- 42.14b (Sun in Aries or Capricorn with a malefic) is the best of the four: 20 / 36 (56% vs 45%, p = 0.13).
- 42.14a: 38 / 67, at chance.
- 42.6: 18 / 27 against a 70% base, no edge.
- 10.17: 2 / 3, a single passage. The current window runs to 7 Feb 2027.

**"Slow planets set the trend, fast planets the sudden moves"** (Kindle Ch.3 / Ch.6; TA p.59–60; KD p.82 / p.129), tested 2000–2026 in `speed_principle_test_2000-2026_ET.html`:
- **Not supported at daily-to-weekly horizons.** Fast-planet events (lunations, quarters, Mercury/Venus stations and ingresses, Sankrantis) were not followed by bigger or more sudden moves in gold or silver: all ratios ×0.95–1.10, none significant.
- **Slow-planet-only rules did not get the trend right more often:**

| Metal | Slow-planet-only rules | Fast-planet-only rules |
|---|---|---|
| Gold | 57% vs a 52% base, only 35 cases | 55% vs 53% |
| Silver | 46% vs 52% | 50% vs 51% |

- **The only hint ran the other way.** A sudden (more than 2σ) gold day followed within 3 days of a Jupiter/Saturn/Rahu sign change in 23% of cases, against 15% for all days (p ≈ 0.03, 77 events; silver 21% vs 15%, p ≈ 0.1). Jupiter/Saturn stations were calmer than normal (9% vs 15%). With 22 classes tested, treat this as a lead, not a rule.

**Gold's big days (±2% close to close), 2000–2026**, in `gold_big_moves_2000-2026_ET.html`:
- 476 big days (226 up, 250 down) out of 6,526. 239 factors were tested: events within ±3 days, states on the day, and active gold rules. Each one's expected count comes from the same years.
- **No factor survives the correction for multiple testing.** The lowest q is 0.36. Every lift below is a lead, not a rule. Big days come in bursts, so the separate episodes behind each count are shown.

| Factor | Lift | Count | Episodes | p |
|---|---|---|---|---|
| Sun–Uranus opposition | ×2.13 | 18 | 8 | 0.003 |
| Venus–Saturn conjunction | ×1.80 | 19 | 9 | 0.012 |
| Jupiter changes nakshatra | ×1.41 | 48 | 35 | 0.014 |
| Saturn combustion begins | ×1.86 | 17 | 11 | 0.013 |
| Rahu with Mars | ×1.44 | 39 | 15 | 0.018 |
| Mars in Capricorn | ×1.39 | 40 | 12 | 0.027 |
| Jupiter changes sign | ×1.53 | 23 | 18 | 0.034 |

- **Up moves:**
  - Mars–Pluto conjunction ×3.5 (8 days, mostly March 2020 and January 2026).
  - Mars in Capricorn, where Mars is exalted, ×1.86 (25 days, 62.5% of its big days up against 47.5% overall, p = 0.003, q = 0.36).
  - Jupiter in Capricorn ×1.55.
- **Down moves:**
  - Pluto stations retrograde ×2.2.
  - Venus–Saturn conjunction ×2.0.
  - Saturn combustion begins ×2.3 (11 against 4.8). Saturn leaving combustion shows nothing (×0.8).
  - Full Moon ×1.24 (73 against 59, p = 0.04).
- **Two bullish rules coincided with big falls, not big rises:** TA Mars in Pushya (25 of 40 big days down) and doc26 Sun in Libra with malefics (15 of 22 down).
- **Slow-planet changes** (Jupiter's nakshatra and sign changes, Saturn's combustion) repeat the speed-test hint: big days cluster around them, in both directions.
- **Uranus, Neptune and Pluto are not Vedic grahas.** Their lifts cannot become rules under the scope decision.
- **Out of sample: no edge.** The 23 leads picked on 2000–2013 (lift > 1, p < 0.05, at least 5 episodes) were measured again on 2013–2026. 14 stayed above 1, but together they gave 388 big days against 380 expected (×1.02, p = 0.34).
  - **Held in both halves:** Venus–Saturn conjunction, Saturn combustion begins, Jupiter's sign and nakshatra changes, Rahu with Mars, Mars in Capricorn, Jupiter in Capricorn, Mars in Pushya (down), Sun in Libra with malefics, Venus stations direct, full Moon (down).
  - **Faded:** the Sun–Uranus opposition (×2.9 → ×0.7) and Saturn leaving combustion.
- **Forward watch, 22 Nov 2026 – 31 Dec 2027** (`gold_big_move_watch_2026-11-22_to_2027-12-31_ET.html` / `.ics`, from `tools/big_move_forward.py`): the 19 full-sample leads, their 34 dated windows, and the weekday stretches with 3 or more leads, or 2 or more leads that held in both halves on Vedic grahas only:

| Dates | Leads | Lean |
|---|---|---|
| 21–27 Jan 2027 | Jupiter retrogrades back into Cancer/Ashlesha (24 Jan); full Moon 22 Jan | either |
| 22–25 Mar 2027 | Saturn combustion begins (23 Mar); full Moon 22 Mar | down |
| 22–28 Jun 2027 | Jupiter re-enters Leo/Magha (25 Jun) | up |
| 18 Oct 2027 | Full Moon (15 Oct); Sun in Libra with malefics | down |
| 27–31 Dec 2027 | Mars in Capricorn and with Rahu; the Rahu & Mars rule | up |

  Other single-lead windows:
  - Venus–Saturn conjunction 7 May 2027 (down).
  - Jupiter enters Virgo 26 Nov 2027.
  - Jupiter nakshatra changes 30 Aug and 4 Nov 2027.
  - Every full Moon (down lean).
  - Outer-planet events, for reference only: Sun–Uranus opposition 25 Nov 2026 and 30 Nov 2027; Neptune stations direct 12 Dec 2026 and 15 Dec 2027; Pluto stations retrograde 8 May 2027.

  These are dates to watch for volatility, not calls.

**Venus combust and rising (TA p.71 Section 18; silver S35 A15/B16; KD p.122/124), 2000–2026, and the January 2026 crash**, in `venus_visibility_test_2000-2026_ET.html`:
- **January 2026.** Venus rose in the West on Sat 31 Jan 2026 (1 Feb IST), in Capricorn/Dhanishta with the Sun and Mars. That is the rule's qualified case: Venus in Aries, Leo, Libra, Capricorn or Aquarius with the Sun, Mars, Saturn or Rahu, which TA says gives a "sharp upturn after a small dip".
  - Gold fell 10.8% on Fri 30 Jan and 1.95% on Mon 2 Feb. Silver fell 31% on 30 Jan.
  - Gold then rose 6.1% on 3 Feb and was 11.9% above the 30 Jan close 20 sessions later.
  - The fall came the session **before** the layer's rising date. Dates for the date-only kalamsha method can be a day or two out.
  - Read loosely, it matches the qualified rule: a fall at the rising, then a sharp recovery. But the dip was not small.
- **26-year record on the standard scoring:**

| Rule (TA says) | Gold | Silver | Longer horizon |
|---|---|---|---|
| Rises in West (Bearish) | 6/12, 50% vs 45%, at chance | 6/14, 43% vs 47%, at chance | Qualified rises gave dip-then-upturn in 2 of 6, against 1.8 expected. Silver had big days within ±3 days 14 times against 10.1 expected, and fell 2.7% on average in the 3 sessions before the date. |
| Combust in East (Bullish) | 12/16, 75% vs 57%, p = 0.11, average +3.3% | 10/15, 67% vs 51% | Gold 20 sessions 82% vs 58%, p = 0.10. The 2026 document's "Bearish for 15 days" is not supported. |
| Rises in East (Bullish for 2–3 months) | 9/12, 75% vs 58% | 9/14 | Gold 40 sessions 13/15, 87% vs 63%, p = 0.045. |
| Combust in West (Extreme Bullish) | 7/16, 44% vs 56%, did not hold up | 5/13 | — |

  None passes p < 0.05 on its stated horizon, and each rule has only about 16 events.
- **Next dates:**
  - Venus combust in East, 20 Jul – 7 Sep 2027 (Bullish).
  - Venus rises in West, 7 Sep 2027, in Leo with the Sun. This is the qualified case again: watch for a dip then an upturn.

**Outlook, 22 Nov 2026 – 31 Dec 2027**, in `gold_outlook_2026-11-22_to_2027-12-31_ET.html` / `.ics`: every tested item in one timeline.
- **Gold:**
  - U2 Mercury with the Sun (small bullish edge) is active on 81% of days in Dec 2026, 74% in Jan, 90% in Aug and 97% in Dec 2027. It is active on only about 13–17% of days in Mar, Sep and Oct 2027.
  - TA S34 A9 does not occur before 2028.
- **Silver:** retrograde Mercury or Jupiter (bullish, p ≈ 0.05) is active from mid-Dec 2026 to mid-Apr 2027, again from 10 Jun to 4 Jul 2027, and from 7 to 28 Oct 2027.
- **Venus:** combust in the East 20 Jul – 7 Sep 2027 (bullish lead). It rises in the West on 7 Sep 2027, in the qualified configuration seen on 31 Jan 2026 (no edge).
- **Volatility watch:**
  - 21–27 Jan, 22–25 Mar (down), 22–28 Jun (up), 18 Oct (down) and 27–31 Dec 2027 (up).
  - Single leads: Venus–Saturn conjunction 7 May (down); Jupiter's nakshatra and sign changes 30 Aug, 4 Nov and 26 Nov 2027.

**Narrowing the watch windows with fast planets**, in `gold_fast_triggers_2026-11-22_to_2027-12-31_ET.html`. This tests the idea that slow planets set the window and fast planets fire the move, conditionally.
- **Windows:** 2,498 historical window days (same definition as the forward watch). Big days were 9.5% of window days against 5.9% outside. This is partly circular, because the leads were picked on the same data.
- **Factors tested:** 44 fast factors on the day itself:
  - Moon relations: with, opposite or aspected by a slow planet; 12th, 2nd and 6/8 from Saturn; the malefic waning Moon; Moon changing sign.
  - Lunation days.
  - Mercury, Venus, Sun and Mars ingresses, stations and combustion, ±1 day.
  - KD's Sun–Mercury conjunction and Mercury manifestation.
- **Result: fast planets do not reliably narrow the windows.** 3 factors passed (lift > 1, p < 0.10, above 1 in both halves). With returns shuffled within each year, 2.0 pass on average (90th percentile 4), so 3 is what chance gives. None survives FDR.

| Factor | Lift | Count | p | Outside windows |
|---|---|---|---|---|
| Moon opposite the Sun (around full Moon) | ×1.49 | 28 / 18.8 | 0.03 | ×0.74 |
| Moon 6/8 from Saturn | ×1.31 | 54 / 41 | 0.03 | ×1.18 |
| Moon opposite Rahu (= with Ketu) | ×1.34 | 25 / 18.7 | 0.09 | — |

  - Moon opposite the Sun is the only one that works inside windows but not outside, which is the pattern the idea predicts.
  - None picks a direction.
  - KD's Sun–Mercury conjunction (×1.07) and Mercury manifestation (×1.40, p = 0.11) did not pass.
- **Narrowed days (best guesses inside the windows):**
  - 22 Jan 2027
  - 22–23 Mar
  - 19–20 Jul (start of Venus combust in East)
  - 30 Aug
  - 6–7 Sep (around Venus rising in the West)
  - 25–26 Nov

  The windows of 4–10 May, 22–28 Jun, 18 Oct, 1–7 Nov and 27–31 Dec 2027 have no tested trigger.

**Test of the signal table's High / Moderate / Low**, in `signal_table_test_2000-2026_ET.html`. The table's scoring was applied to every day of 2000–2026. Runs of days with the same signal and strength were scored like rules, against a same-year base.
- **Walk-forward** (watch leads and fast triggers re-picked on 2000–2013, scored on 2013–2026):

| Label | Right | By chance | Cases | p |
|---|---|---|---|---|
| Bullish High | 64% | 53% | 33 | 0.16 |
| Bullish Moderate | 58% | 54% | 69 | — |
| Bullish Low | 54% | 55% | 149 | — |
| Bullish High and Moderate together | 60% | 54% | 102 | 0.13 |
| Bearish Moderate | 48% | 44% | — | — |
| Bearish Low | 44% | 44% | — | — |

  Volatile runs held a ±2% day 11 times, against 10.4 expected.
- **Source rules only** (U2, Venus combust in East, Sun in a Saturn nakshatra with Mars): bullish High and Moderate together 38/57, 67% vs 56% (p = 0.058). Venus combust in East carries most of this.
- **Verdict:**
  - **Bullish:** the strength order holds in every run (High > Moderate > Low) and on unseen data, but the edge is small and not significant.
  - **Bullish Low:** this is U2 alone and is at chance.
  - **Bearish and Volatile:** these labels have no edge.
  - The table now shows each label's walk-forward record in its last column.

**Silver: the same chain** (big moves, watch, outlook, fast triggers, signal table and its test), using ±3.5% days. That threshold is as rare for silver (8.4% of days) as 2% is for gold.
- **Big moves:** 546 big days over 2000–2026. The top in-sample factors are Venus with the Sun (×1.25), Jupiter retrograde (×1.20), Rahu's vedha of Pushya (×1.27) and Jupiter in Gemini (×1.31). None survives FDR.
  - **Out of sample they fail:** only 3 of the 17 leads picked on 2000–2013 held on 2013–2026, and together they gave ×0.91. Silver's big-move leads have no value, which is weaker than gold's ×1.02.
- **Fast triggers:** 4,993 of 6,527 days fall inside silver's watch windows, because the long states make the windows broad. 3 of 44 fast factors passed, against 2.5 expected by chance. The three were Mercury stationing retrograde (×1.47), a last-quarter Moon (×1.25) and Venus changing nakshatra (×1.13).
- **Signal table test:**

| Run | Bullish High | Bullish Moderate | Bullish Low | Notes |
|---|---|---|---|---|
| Walk-forward 2013–2026 | 55% vs 52% | 55% vs 52% | 55% vs 52% | No strength order. Volatile runs held a ±3.5% day 8 times, against 13.7 expected. |
| Source rules only (retrograde Mercury/Jupiter +2, Moon–Mercury alone +1, Venus combust in East +1) | 29/44, 66% vs 53%, p = 0.065 | — | — | High and Moderate together 60% vs 54%, p = 0.075. |

  - For silver, the data-picked parts add nothing.
  - The useful part is retrograde Mercury or Jupiter: mid-Dec 2026 – mid-Apr 2027, 10 Jun – 2 Jul and 7–28 Oct 2027.
  - The silver table (`silver_signals_*`) shows these as High or Moderate bullish. Its past-record column shows the flat walk-forward result.

**Stock market: S&P 500 (^GSPC) and BSE Sensex (^BSESN), 20 Nov 2000 – 20 Nov 2026.** The user chose both markets on 23 Nov 2026. Prices come from `tools/fetch_prices.py`, with dates in each exchange's own time zone. Details are in `market_summary_2000-2026_ET.html`.

*Direction rules.* All computable general-market rules from TA, KD and the 2026 document were scored like the gold rules, 464 per market.
- **The rules do not call direction on either index.** Pooled hit rates are 51.2% vs 51.1% (S&P) and 50.9% vs 50.9% (Sensex). Only 9 rules per market reach p < 0.05, where luck alone would give about 18, and none passes FDR.
- **Walk-forward:** rules picked on 2000–2013 gave 62% vs 61% on 2013–2026 (S&P, 11 rules) and 58% vs 57% (Sensex, 15 rules).

*Big days (±2%; 7.5% of S&P sessions and 9.4% of Sensex sessions).* Several factors pass FDR here, unlike for gold.
- **Out of sample:** leads picked on 2000–2013 gave ×1.03 on 2013–2026 for the S&P (p = 0.13) and **×1.09 for the Sensex (p = 0.0008)**.
- **Robust factors** pass FDR, are above 1 in both halves, and still have p < 0.01 without the 2008–09 and 2020 crashes:

| Index | Factor | Lift | Without the crashes | q |
|---|---|---|---|---|
| S&P 500 | **Venus retrograde** | ×1.75 | ×1.92 | — |
| S&P 500 | Jupiter–Pluto 5/9 | ×1.56 | — | 0.002 |
| S&P 500 | Jupiter–Neptune opposition | ×1.63 | — | — |
| S&P 500 | Jupiter–Uranus 6/8 | ×1.42 | — | — |
| S&P 500 | Mercury–Saturn 2/12 | ×1.38 | — | — |
| Sensex | **Venus retrograde** | ×1.61 | ×1.68 | — |
| Sensex | Mars–Saturn conjunction | ×1.56 | — | — |
| Sensex | Mars with Saturn | ×1.51 | — | — |
| Sensex | Venus in Pisces | ×1.44 | — | — |
| Sensex | Mars–Uranus 5/9 | ×1.31 | — | — |

  - **Venus retrograde** is the one factor robust in both markets.
  - Mars with Jupiter and the Mars–Jupiter conjunction (S&P) were driven by March 2020 and drop out without it.
  - All these factors mark **volatility in both directions**: up share is 40–56% against 45–50% overall. Several are TA "Bullish" rules that actually mark big moves.
- **Dates to end-2027:**
  - **Venus retrograde does not occur before 2028.**
  - S&P: Mercury–Saturn 2/12 on 27 Jan – 23 Feb, 11 Mar – 5 Apr and 21 Apr – 6 May 2027. Jupiter–Neptune opposition and Jupiter–Pluto trine from 26 Nov 2027 (Jupiter in Virgo).
  - Sensex: Venus in Pisces 15 Apr – 9 May 2027. Mars–Uranus trine 4 Jul – 24 Aug and from 27 Dec 2027.

**The 2027 calendar's own rule layer (162 rules from the 2026 document), backtested 2000–2026**, in `calendar_rules_backtest_2000-2026_ET.html`.
- **Why this test:** only 76 of the 162 calendar rules have an equivalent in the PDF catalogue. Generating the layer per year (about 1 s each) tests all of them on the instruments the calendar names.
- **Pooled direction:** no edge anywhere.

| Market | Right | By chance |
|---|---|---|
| S&P 500 | 47.0% | 46.5% |
| Sensex | 45.5% | 46.7% |
| Gold | 54.9% | 54.8% |
| Silver | 49.9% | 51.7% |

- **Two rules held in both indices and in both halves** (bearish 5-session moves):

| Rule | S&P 500 | Sensex |
|---|---|---|
| **Three Saturdays in Shukla Paksha** (B101) | 41/73, 56% vs 39%, p = 0.002, q = 0.046 | 33/66, 50% vs 39%, p = 0.04 |
| **Shukla Shashti on Friday** (B100) | 41/77, 53% vs 41%, p = 0.02 | 40/76, 53% vs 42%, p = 0.045 |

  - 2027 dates for B101: 6 Feb, 5 Jun (Sensex) / 3 Jul (S&P), 30 Oct and 27 Nov (S&P).
  - 2027 dates for B100: 12 Feb, 9 Jul, 6 Aug (S&P) and 3 Dec.
- **Rules printed as strong that did not hold:**
  - "Ekadashi on Friday – High Bearish, reliability 90%+": 37% vs 40% (S&P) and 42% vs 42% (Sensex).
  - Pradosh (negative day): 39% vs 41% and 43% vs 42%.
  - Shani–Chandra dwidwadash: at chance.
- **Volatility:** Bhadra, Panchak, Pradosh, Amavasya/Purnima and the other condition-only rows bring no extra big days. For example, Bhadra episodes held a big day 183 times against 191 expected (S&P) and 248 against 234 (Sensex).
- **Gold and silver:** no calendar rule passes p < 0.05.

**S&P 500 / Sensex signal tables to end-2027**, in `market_signals_2026-11-23_to_2027-12-31_ET.html`. A rule qualifies when it reached p < 0.05 on one index and beat the base in both halves on both indices.
- **10 rules qualify:**

| Strength | Rules |
|---|---|
| High | Mars–Mercury Vedha (bullish); Shukla Shashti on Friday and Three Saturdays in Shukla Paksha (bearish, calendar) |
| Moderate | Mars–Saturn 4/10 (bullish); Moon–Rahu 6/8 (bullish); Mars–Saturn 2/12 (bearish); Mercury–Rahu conjunction (bearish) |
| Low | Venus–Uranus 7th (bearish); Venus–Rahu 6/8 (bullish); Mrigashira on Monday (bullish) |

- **Walk-forward check of the selection:** picked the same way on 2000–2013, these rules gave 61.8% vs 59.2% (S&P, p = 0.12) and 57.3% vs 56.4% (Sensex, p = 0.34) on 2013–2026. That is a small edge, not proven.

**Outside model check (two infographics, 23 Nov 2026)**, in `external_model_check_ET.html`.

| Part | Result |
|---|---|
| Astronomy | **Right.** 44 of 45 historical placements hold on the crash date or in the crash window; the one miss is Jupiter, which reached Capricorn on 30 Mar 2020, after the COVID low. 22 of 23 placements for 2026–2029 hold; Rahu enters Capricorn 25 Nov 2026 by the true node (5 Dec by our mean node). The India Mars-dasha sub-periods match. |
| "Core signatures" | **Do not predict crashes.** Jupiter weakness, Mars trigger and eclipse/stellium appear in every 12-month window since 1928, and the S&P did no worse with them. Saturn–node / Saturn in Pisces–Aries is the only hint: 6-month falls of 15%+ 19.6% vs 14.2% of the time (z = 2.3, with overlapping windows). |
| Forecast | **Agrees on timing of turbulence:** our robust volatility factors cluster in Feb–May 2027 and Jan–Jun 2028. **Not on direction:** our tables are mixed on the S&P and bullish-leaning on the Sensex in Aug–Dec 2027. They agree on silver strength in Dec 2026 – Jun 2027 and on gold in Aug 2027. |
| Nov 2026 "Act I" | Matches the moves (Nasdaq −18.1%, gold $3,515, silver $41.03), but it was drawn after the fact. |

**Day report, Mon 23 Nov 2026**, in `day_report_2026-11-23_ET.html`.
- **Sky:** Sun in Scorpio/Anuradha; Moon in Aries/Bharani (Shukla Chaturdashi, full Moon on 24 Nov); Mars, Jupiter and Ketu in Leo/Magha; Saturn retrograde in Pisces/Uttara Bhadrapada; Rahu at 0°38' Aquarius (enters Capricorn on 5 Dec); Venus just into Libra.
- **What we said:**
  - Gold: bearish, low strength (Sun in Anuradha, Mars aspecting the Sun). That label has no edge, 44% vs 44%.
  - S&P 500, Sensex and silver: no signal.
  - Volatility watch: gold's Sun–Uranus opposition and full-Moon window, 22–28 Nov.
- **What happened:** S&P +4.7%, Nasdaq +6.5%, gold +3.2%, silver +4.4%, Sensex −1.8%.
  - The gold call was wrong.
  - The volatility watch was right (a ±2% day).
  - 165 catalogue rules were active. Of those with a supported record, 8 bullish vs 1 bearish for the S&P (right) and 6 vs 3 for the Sensex (wrong), but that tally is not a tested signal.

**Day report, Tue 24 Nov 2026**, in `day_report_2026-11-24_ET.html`.
- **Sky:**
  - Full Moon in Taurus/Krittika (exalted Moon) at 09:53 ET; Krishna Pratipada by noon.
  - Sun–Uranus opposition exact on 25 Nov.
  - Otherwise the same as 23 Nov: Mars, Jupiter and Ketu in Leo/Magha; Saturn retrograde in Pisces; Rahu at 0°34' Aquarius.
- **What we said:**
  - Gold: bearish, low strength (no-edge label), and its volatility watch is on (full Moon, Sun–Uranus opposition).
  - S&P 500, Sensex and silver: no signal.
  - 136 catalogue rules are active. Those with a supported record lean bullish: S&P 5:1, Sensex 6:2 (not a tested signal).
  - Calendar: full Moon "top or bottom" for silver, which has no edge (14 big days against 18 expected); Kshay Tithi bullish for the S&P, at chance.

**What triggered the 20 Nov fall and the 23 Nov rise? (astrology only)** Sources: `trigger_study_2000-2026_ET.html`, `rule_tally_ET.html` and `market_event_log.json`.

| Day | Moves |
|---|---|
| Fri 20 Nov | S&P −3.7%, Nasdaq −5.3%, gold −4.6%, silver −7.4%, Sensex +1.1% |
| Mon 23 Nov | S&P +4.7%, Nasdaq +6.5%, gold +3.4%, silver +5.3%, Sensex −1.8% |

- **No day-level condition leans the way the market moved.** Each of the 20 conditions present on those days was tested on the same-day move, 2000–2026, in five markets.
  - "Ekadashi on Friday" (printed as 90%+ bearish): the S&P closed up on 64% of such days against 53%.
  - Bhadra, Moon with Saturn, Moon in Pisces and Panchak: at chance.
  - Venus debilitated and Mercury alone in a sign: slightly more big S&P falls (p ≈ 0.04 each, out of 100 tests).
  - Monday's conditions (Moon in Aries, Moon trine Jupiter and Mars, Venus in own sign, the days before the full Moon): no bullish lean.
- **The net tally of active rules with a good record was the same on both days: +5 for the S&P.** On Friday, Mercury alone in a sign and Jupiter with Ketu and the Moon (bearish) were outweighed by Moon contacts and Venus–Rahu 6/8. On Monday, Mercury alone and Venus–Rahu had ended.
  - Walk-forward (rules chosen on 2000–2013, scored on 2013–2026): the tally does not call the same-day move. A bearish net was right on the next 5 sessions 45% of the time against 40% (p = 0.02), a bullish net 61% against 60%.
- **The stand-out is the background: Mars, Jupiter and Ketu together** (Leo, since 12 Nov 2026).
  - The same triple ran from 10 Feb to 20 Mar 2020.
  - Mars–Jupiter with a node, S&P 1928–2026: 3 of 13 episodes had falls of 15%+ (1933, 2009, 2020), against 3.5% of random 29-session windows; 5 of 13 fell 8%+, against 11.8%.
  - In 2009 and 2020 the bottom came within 3 sessions of the episode ending. Ketu leaves on 5 Dec 2026, and Mars–Jupiter lasts until 24 Jan 2027.
  - It was picked after the fact: a lead, not a rule.
- **Reading:** the sky marked a turbulent period, with big moves both ways, but did not say which day would fall or rise.

**NYSE monthly solar returns** (an astrologer's technique, shared 24 Nov 2026), in `nyse_usa_charts_ET.html`.
- **The technique, reconstructed from the charts:**
  - The NYSE natal Sun is 27°18' Taurus **tropical** (Buttonwood Agreement, 17 May 1792, morning).
  - Each solar month starts when the tropical Sun reaches 27°18' of the next sign. The charts are cast for New York: 20 Oct 2026 12:28 EDT and 19 Nov 2026 10:10 EST, both Capricorn rising.
  - Solar return reads **tropical signs**: "debilitated ascendant lord Saturn" is Saturn in tropical Aries. In our sidereal Lahiri convention Saturn is in Pisces (not debilitated), the rising sign is Sagittarius, and Mars–Ketu fall in the 9th.
- **The Solar return claims:**
  - 20 Oct – 18 Nov: two bearish indications (debilitated ascendant lord, Mars with Ketu in the 8th). The S&P went 7,690 → 7,320 (−4.8%).
  - 19 Nov – 18 Dec: both persist, but Venus in the 10th moderates. Forecast: further weakness, but a smaller net decline than −4.8%.
- **98-year backtest (1,186 solar months, S&P 1928–2026), the Solar return version:**

| Indication | Months | S&P up | Average month vs other months |
|---|---|---|---|
| Debilitated ascendant lord | — | 68% (all months 60.5%) | +1.21% vs +0.60% |
| Mars with Ketu in the 8th | 8 | — | −0.08% vs +0.66% (inconclusive) |
| A malefic in the 8th | — | — | slightly *better* (t = +1.9) |
| Both bearish indications together | 27 | 70% | **+3.67%** vs +0.58% (t = +2.1, the wrong way) |
| Venus or Jupiter in the 10th | — | — | no moderating effect |

  - Sidereal version: nothing significant. Mars with Ketu in the 8th fell 5%+ in 3 of 11 months (27% vs 9.5%), but the sample is far too small to judge.
  - **Verdict:** the Solar return monthly indications do not hold up over 98 years. Their bearish pair has, if anything, come before better months.
- **Natal charts (sidereal):**
  - NYSE, 10:00 LMT: Cancer rising, Sun Taurus 6°, Saturn debilitated in Aries in the 10th.
  - USA, Sibly 17:10 LMT: Scorpio rising, Sun Gemini 22°, Moon Aquarius 6°.
- **Transits now:** Mars, Jupiter and Ketu in Leo fall in the USA's 10th house, with Mars and Jupiter opposite the USA Moon. Transit Rahu is in the NYSE's 8th house. These are descriptive; no rule has been tested.
- **Open forecast** (check on 19 Dec 2026): S&P net decline from 7,320 smaller than 4.8% over 19 Nov – 18 Dec.

**Solar return: transit method and forecasts** (shared 24 Nov 2026), in `author_forecasts_ET.html`. Its months start on the 18th or 19th (monthly NYSE solar returns), and it reads transits with degree aspects (square, sextile, conjunction).
- **Forecast scorecard, as of 23 Nov 2026:**

| Period | Solar return call | Result |
|---|---|---|
| 20 Oct – 18 Nov | Bearish | **Right** (−4.8%) |
| Week of 16 Nov | Lower Mon–Thu, Friday recovery | **4 of 5 days right** (Friday fell 3.7%) |
| Week of 23 Nov | Pressure Mon–Wed, Friday recovery | Monday +4.7%, the wrong way; rest open |
| 19 Nov – 18 Dec | Smaller decline than −4.8% | Open (−1.2% so far) |
| Oct 2026 – Oct 2027 | Weak to spring 2027, bottom Mar–May, strong second half | Open |

- **The Solar return transit statements, checked:**
  - Right:
    - Mars–Ketu conjunction (within 1° on 14–16 Nov 2026).
    - Sun square Mars–Ketu (exact about 19 Nov).
    - Jupiter–Venus sextile (within 1° 26–30 Nov).
    - Retrograde Mars square Uranus (exact 16–17 Feb 2027).
  - Wrong date: Mars turns retrograde on **10 Jan 2027**, not in February.
  - Tropical only: Mercury in Pisces in February. Sidereally, Mercury is in Pisces only 5–21 Apr 2027.
  - Close, not within 1°: Mars is 1.6° from Ketu (true node; 2.9° by the mean node) when it stations direct on 1 Apr 2027.
- **Solar return aspect rules on the S&P, 1928–2026:**
  - **Jupiter sextile Venus (Solar return bullish):** next 5 sessions up 63.6% of 198 episodes, against 55.8% (p = 0.03). It works, modestly; it is the best of the Solar return rules.
  - **Sun square Mars:** no direction, but more big days (67 vs 51, p = 0.016). That fits volatility, not a fall.
  - **At chance:** Mars–Ketu conjunction, Mars square Uranus, Mercury in Pisces (either zodiac).
  - **Mars retrograde:** *fewer* big days than usual.
- **The Solar return annual path against our S&P table:**

| Period | Solar return call | Our table (weekdays) |
|---|---|---|
| Nov 2026 – Feb 2027 | Weak | Bearish 34 vs bullish 10 |
| Mar – May 2027 | Bottom | Turns bullish 24 vs 6, plus 18 volatile days |
| Jun – Dec 2027 | Advance | Bullish 70 vs bearish 34 |

  - Independent agreement on the shape of the year, though our table's edge is small and unproven.
  - Also independent: **Mars, Jupiter and Ketu meet again in Cancer, 9 Mar – 26 Apr 2027.** That is our Mars–Jupiter-node lead, and in 2009 and 2020 the bottom came within 3 sessions of such an episode ending. This one ends on 26 Apr, inside the Solar return Mar–May bottom window.

**Our model over the last 60 days** (24 Sep – 23 Nov 2026), in `model_check_60d_ET.html`. Each table's label was rebuilt for every past day. A calendar-window fix was found and applied: "Three Saturdays in Shukla Paksha" is a whole-fortnight window, as it was backtested, not 5 sessions from its first day.

| Market | Window move | Bearish labels | Bullish labels |
|---|---|---|---|
| Gold | −15.3% | Next 5 sessions right 62% (low, 15 days) and 100% (moderate, 3 days) | Bullish low (U2) wrong: 14% over 5 sessions |
| Silver | −32.6% | Silver has no bearish rules | Bullish high (retrograde Mercury/Jupiter) wrong: 27% over 5 sessions, 15 days |
| S&P 500 | −6.1% | Bearish high (Three Saturdays) right 58% same day, 75% over 5 sessions (12 days) | Bullish low wrong: 20% / 14% |
| Sensex | +10.2% | Bearish high right 64% same day, 55% over 5 sessions | Bullish labels right 78–100% (17 days) |

- **Robust volatility factors:** no help here. Big days came on 2 of 30 factor days against 3 of 13 others (S&P), and 3 of 28 against 0 of 12 (Sensex).
- **Reading:** the bearish calls fitted the falls in gold and the S&P. The bullish metal calls failed in a falling market; that is the weak "low" label and silver's one-sided rules. Sixty days is a health check, not a test.

**USA and NYSE dashas** (Vimshottari, five levels; `dasha_transits_ET.html`)

- **USA** (Sibly 17:10 LMT; Moon Aquarius 6°26', end of Dhanishta). Running now:

| Level | Lord | Period | Transit of the lord |
|---|---|---|---|
| Mahadasha | Rahu | 2016–2034 | Aquarius 0°34' (4th house, on the natal Moon sign, aspected by Mars); enters Capricorn 5 Dec |
| Antardasha | Mercury | Jul 2024 – 17 Feb 2027 | Libra, 12th house |
| Pratyantar | Saturn | 23 Sep 2026 – 17 Feb 2027 | Retrograde in Pisces, 5th house; S&P −11% from its start to 20 Nov |
| Sookshma | Venus | 15 Nov – 9 Dec | Libra, own sign |

  Next: Rahu/Ketu from 17 Feb 2027; its Ketu Pratyantar runs to 12 Mar, then Venus.
- **NYSE** (10:00 LMT; Moon Pisces 28°48', Revati). Running now:

| Level | Lord | Period | Transit of the lord |
|---|---|---|---|
| Mahadasha | Mercury | 2016–2033 | — |
| Antardasha | Rahu | 22 May 2026 – 9 Dec 2028 | In the NYSE's 8th house, aspected by Mars |
| Pratyantar | Jupiter | 9 Oct 2026 – 10 Feb 2027 | With Mars and Ketu in Leo, the NYSE 2nd house, aspected by Rahu; S&P −11% since 9 Oct |
| Sookshma | Mercury | 15 Nov – 2 Dec | — |

  Next: Saturn Pratyantar from 10 Feb 2027.
- **Birth-time precision:** a birth-time error shifts the whole timeline, about 0.3–0.7 years per hour here.
  - The Mahadashas hold within ±3 hours.
  - The Antardashas need the hour.
  - Pratyantar, Sookshma and Prana need the minute, which neither chart has. Treat the smaller levels as illustrations.
- **S&P test, 1928–2026:** no dasha lord at any level (Antar, Pratyantar, Sookshma) shows an S&P effect in either chart (all |t| < 2). Benefic and malefic periods do not differ.

**All layers together as one probability** (`combined_probability_60d_ET.html`, user request 24 Nov 2026: "think like a pro Vedic astrologer").

- **Layers used:**
  - Our signal tables (all four markets).
  - Model v1.0 (gold).
  - Robust big-move factors (S&P, Sensex).
  - For the S&P, on both the USA and NYSE charts:
    - Dasha-lord condition (Antar + Pratyantar + Sookshma): dignity, house from the ascendant, combustion, Saturn/Mars/Jupiter influence, Shadbala.
    - Gochara of Jupiter, Saturn and Rahu from the natal Moon.
    - Chandra bala.
    - Tara bala.
  - The Solar return Jupiter sextile Venus (S&P).
- **Classical layers:** gochara, Chandra bala and Tara bala are classical practice that our sources do not state. They are included at the user's request and flagged.
- **Method:** naive Bayes on log-odds with 200-day shrinkage.

Results, as the share of calls right:

| Market | Last 60 days, all layers | 2013–2026, kept layers |
|---|---|---|
| S&P, 5 sessions | 64% of 25 calls (down calls 76% right in a market up only 31% of the time) | 55% |
| S&P, today | 48% | 55% |
| Sensex, today | 74% | 52% |
| Sensex, 5 sessions | 68% | 54% |
| Gold, 5 sessions | 55% of 11 calls (market up only 26% of the time) | 54% |
| Silver | No calls: the weights for its table's bullish labels are near zero | 51% |

- **What the 13-year walk-forward shows:**
  - All layers together score *worse* than the base rate on every market (skill −0.2% to −0.6%). That is noise adding up.
  - Layers kept because they helped on their own: +0.1% to +0.5% skill.
  - The probabilities stay within a few points of the base rate (about 47–62%).
- **Each Vedic layer on its own, 2013–2026:**
  - Only the NYSE dasha condition (+0.02%) and NYSE gochara (+0.18%) helped the 5-session forecast, and only by tiny margins.
  - USA dasha, USA gochara, Chandra bala and Tara bala did not help.
  - For big days, no Vedic layer helped, and the S&P model gave 19–20 Nov a big-day probability of only 2.7–3.2%.
- **Reading:** combined, our astrology gives probabilities that are honest but close to a coin with the market's natural upward lean. The good 60-day hit rates come mostly from bearish tables in falling markets.

**Day by day, 24 Nov – 31 Dec 2026** (`daybyday_2026-11-24_to_2026-12-31_ET.html`)

- **Active rules:** 131–171 catalogue rules are active each day, plus 4–22 calendar rows.
- **Key sky events (ET):**
  - Full Moon in Taurus, 24 Nov.
  - Sun–Uranus opposition, 25 Nov.
  - Mercury enters Scorpio, 2 Dec.
  - Rahu enters Capricorn and Ketu enters Cancer, 5 Dec. This ends Mars–Jupiter–Ketu in Leo, our crash lead, active 24 Nov – 5 Dec.
  - New Moon in Scorpio and Mercury–Uranus opposition, 8 Dec.
  - Saturn turns direct, 10 Dec.
  - Jupiter turns retrograde and Neptune turns direct, 12 Dec.
  - Mercury becomes combust, 13 Dec.
  - Sun enters Sagittarius, 15 Dec.
  - Mercury enters Sagittarius, 21 Dec.
  - Full Moon in Gemini, 23 Dec.
  - No eclipse.
- **Solar return rules:**
  - Jupiter sextile Venus (within 2°), 24 Nov – 1 Dec. Bullish over 5 sessions: 63.6% vs 55.8%, p 0.03.
  - Mars square Uranus, 27 Nov – 12 Dec. It showed no effect in its test.
- **Combined probabilities for the S&P (base: 57% up over 5 sessions):**
  - Over 5 sessions they range from 55% to 63%.
  - The highest, 62–63%, fall on 27 Nov and 2–4 Dec, when the table is Bullish Moderate.
  - Big-day probabilities are 2–6%. The model has no volatility-regime input.
- **Other markets:**
  - Gold's table is Bearish Low 24 Nov – 1 Dec, then Bullish Low (U2, Mercury with the Sun) from 2 Dec.
  - Silver is Bullish from 14 Dec.
  - Every probability stays within a few points of its base rate.

**The day-by-day set checked on 1–23 Nov 2026** (`daybyday_2026-11-01_to_2026-11-23_ET.html`; combined model fitted to 31 Oct only; 16 sessions)

**How the markets moved:**

| Market | Up days | Up over 5 sessions |
|---|---|---|
| S&P 500 | 6 of 16 | 3 of 12 |
| Sensex | 12 of 15 | 11 of 11 |
| Gold | 7 of 16 | 3 of 12 |
| Silver | 7 of 16 | 3 of 12 |

**All methods pooled, share of calls right:**

| Market | Same day | Next 5 sessions |
|---|---|---|
| All markets | 54% (171/319) | 49% (117/241) |
| S&P 500 | 51% | 48% |
| Sensex | 80% | 97% |
| Gold | 48% | 32% |
| Silver | 42% | 24% |

- **Why it splits this way:** our readings leaned bullish. Sensex rose, so they were right there; S&P, gold and silver fell, so they were wrong there.
- **Right on the S&P:** the bearish readings.
  - Mars–Jupiter–node lead: 88% same day, 100% over 5 sessions.
  - Solar return Sun square Mars: 83%.
  - Solar return day forecasts: 67% (4 of 6).
  - USA dasha condition: 70% / 71%.
  - NYSE gochara: 62% / 75%.
  - Solar return bearish month view: 62% / 75%.
- **Wrong on the S&P:**
  - Signal table: 29% / 18%.
  - Supported-rule tally: 40% / 25%.
  - Combined probability: 38% / 17%.
- **Gold and silver:**
  - Model v1.0 (gold): 46% / 18%.
  - Tara bala and Chandra bala: 33–55%.
- **Big days:** the model's average big-day probability was no higher on the 5 big S&P days (3.3% vs 3.9%).
- **Reading:** a few bearish signals hit in a falling month. Their success matches the market's down share, and some (the Solar return month view) were bearish on every day, so this is no evidence of skill. Over 16 sessions none of it is significant.

**Paap Kartari and Shubh Kartari** (`kartari_test_ET.html`, user question, 24 Nov 2026)

- **Gap found:** the 2026 document's B116 (Mercury in Paap Kartari, "negative event for financial markets") and B117 (Jupiter in Paap Kartari, no direction printed) were in the calendar layer as condition-only rows. So they were never scored, and the 2026 calendar did not show them. Both are now tested and shown.
- **Tested on the S&P and Sensex, 2000–2026:**

| Yoga | Tested as | S&P 500 | Sensex | Verdict |
|---|---|---|---|---|
| B116, Mercury in Paap Kartari (236 windows) | Bearish | 41% vs 39% (p 0.28) | 48% vs 41% (p 0.027); beat the base in both halves (50 vs 42, 45 vs 39) | Holds as bearish on the Sensex only |
| B117, Jupiter in Paap Kartari (42 windows) | Bearish (inferred from B116) | 48% vs 37% (p 0.12); only the first half (65 vs 46), not the second (30 vs 29) | 48% vs 42% (p 0.28) | Direction unproven |
| TA s31, Mercury in Paap Kartari (stricter definition, from the market backtest) | Bearish | 49% vs 39% (p 0.065) | At chance | Weak, S&P only |
| Shubh Kartari, Mercury and Jupiter (not in any source; exploratory) | Bullish | 33–50% vs 57–63% | 33–50% vs 57–63% | Fails; not used |

- **B116 details:** big days are normal. Its "more profound" case (Mercury combust, malefics other than the Sun) has only 12 windows, too few to judge.
- **B117 big days:**
  - Pooled, they run higher: 11.6% vs 7.5% (S&P) and 14.4% vs 9.4% (Sensex).
  - Only 14 and 18 of the 42 windows beat their year's rate.
  - Permutation p is 0.075 (S&P) and 0.052 (Sensex).
  - A lead at most.
- **Active now:** Jupiter in Paap Kartari (Ketu | Mars), 16 Nov 2026 – 31 Jan 2027.
- **Next:** Mercury in Paap Kartari (B116) 1–15 Jan 2027 (Sun | Pluto), 25 Jan and 18 Feb – 16 Mar 2027.
- **In the calendar:** shown in the 2026 calendar's key dates, read-first notes and each day's notes.

**24 Nov 2026: what we said and what happened** (`day_report_2026-11-24_ET.html`, closes; the BSE was shut for Guru Nanak Jayanti)

| Market | What we said | What happened |
|---|---|---|
| Gold | Bearish Low; big-move watch on (full Moon exact) | −2.64%, a big day. Both right |
| Silver | No signal | −5.65%, a big day by silver's 3.5% threshold. Not called |
| S&P 500 | No signal (combined model 58% up) | −0.50% (Nasdaq −1.48%). Model leaning wrong, by a hair |
| Sensex | — | Closed |

- **Solar return:** its day call ("down") was right, and so was our generated Solar return call ("bearish"). Its week of 23–27 Nov now stands at 1 of 2.
- **Global Predictions:** −0.50% after +4.73% is not a sharp reversal by our 1% definition. Its 24–27 Nov window is open; 11% of the 23 Nov rally has been given back.

**Global Predictions** (outside forecast, a WhatsApp forecaster, shared 24 Nov 2026; `global_predictions_ET.html` and the 2026 calendar). Western-style aspects, so the calls are tracked and scored but not added as rules. News in the messages is ignored.

- **The calls:**
  - 24–27 Nov: volatility and sharp reversals. Full Moon conjunct Uranus, challenged by Mars; Sun opposite Uranus.
  - 30 Nov – 5 Dec: Venus–Mercury optimism, then instability from the approaching Mars–Uranus square.
  - Overall: a rally followed by equally sharp selling.
- **Astronomy check:**

| Claim | Check |
|---|---|
| Full Moon conjunct Uranus | Right: Full Moon 24 Nov 09:54 ET, Moon–Uranus 1.4° |
| Challenged by Mars | Right: Mars 2.9° from a square to the Moon |
| Sun opposite Uranus | Right: exact 25 Nov 17:41 ET |
| Mars–Uranus square | Right: exact 4 Dec 14:28 ET |
| Venus–Mercury, 30 Nov – 5 Dec | Wrong: no aspect, the two are 24–28° apart |

- **The same configurations, 1928–2026:**
  - **Full Moon near Uranus:**
    - Sharp reversals (a 1%+ session after a 1%+ session the other way) ran at 14 against 6.5 expected (p 0.007).
    - All of the excess is in 1977–2026 (11 vs 3.5). 1928–1976 had 3 vs 3.1.
    - Big days were normal.
    - A lead, not a rule.
  - **Sun opposite Uranus:** reversals 23 vs 17 (p 0.10); big days normal.
  - **Mars square Uranus:** no effect.
  - **Venus conjunct Mercury:** more big days (109 vs 86, p 0.01) and no bullish tilt, though it does not occur in the window.
- **Scoring:**
  - A volatility window is right if it has a big day or a sharp reversal.
  - In the last 250 sessions, 15% of 3-session windows had one, so such calls are often right by default.
  - Scheduled: score the 24–27 Nov window on 28 Nov; score 30 Nov – 5 Dec and the overall scenario on 5 Dec.

**The 2026 document's December table, checked** (user request 24 Nov 2026; in the 2026 calendar's "Check against the 2026 document" section and on each December day)

- **Rows:** 30 printed rows (pp.292–293, IST). 26 carry computable times, and 24 agree with our ephemeris within 2 minutes.
- **Misprints, according to the document's own tables:**
  - The Saturn vedha change is printed at 11 Dec 20:54, but the document's Saturn table gives 05:02, Saturn's station (we compute 05:01, by the tropical speed, as the document does).
  - The November table's "Mercury and Venus both retrograde 24 Oct – 11 Dec" contradicts its own station tables (Mercury direct 13 Nov, Venus 14 Nov).
- **Printed only within Indian market hours:** Bhadra on 13, 20 and 26 Dec and the Moon–Mercury D9 windows outside 09:15–15:30 IST are omitted.
- **Mercury "alone" in Mula:** the Sun is also in Mula from 15 Dec. Tested without the "alone" condition.
- **Bhadra tone:** our implementation of the document's sec-142 rule matches its 2026 Bhadra table on 99 of 99 rows.
- **Day-level coverage (monthly fixture):** 26 of 30 rows are reproduced. The rule layer still blocks the two Saturn vedha rows, the Rahu vedh row and Vargottam Mars.
- **Stated directions, 2000–2026** (newly tested here, or quoted from the calendar backtest):
  - Only negative Bhadra holds, on the Sensex: 47% vs 42%, p 0.039, both halves. That is 1 of about 18 tests, so a chance pass is expected.
  - Everything else is at chance or the wrong way:
    - Ekadashi on Friday: 37% vs 40% (S&P).
    - Shukla Pratipada vriddhi.
    - Shani–Chandra dwidwadash.
    - Shatabhisha on Tuesday.
    - Vyatipata in Panchak.
    - Shukla Trayodashi on Tuesday.
    - Kshay Purnima.
    - Positive Bhadra.
    - Moon–Mercury D9.
    - Rahu/Ketu nakshatra on Thursday.
    - Apogee and perigee.
    - Mercury in Mula: 23% vs 39% (S&P), the wrong way.
    - Vargottam Mars.
    - Mars ahead of Jupiter.
- **This December:** the only nominal pass is the negative Bhadra on 29 Dec (13:25 IST – 00:55), a bearish lean for the Sensex.

**Mercury Paap Kartari in January 2027, S&P and Sensex** (`kartari_jan2027_ET.html`; merged into the 2026 calendar as its "January 2027" section; user request 24 Nov 2026)

- **S&P 500** (ET; New Year's Day 1 Jan and MLK Day 18 Jan are closed):

| Window | Hemmed by | Mercury | Sessions |
|---|---|---|---|
| 1 Jan 12:07 – 15 Jan 21:48 | Sun / Pluto | Sagittarius, combust, aspected by Jupiter | 10 sessions, 4–15 Jan, from the 31 Dec close |
| 25 Jan 03:01 – 22:51 | Sun / Rahu | Aspected by Jupiter | The 25 Jan session |

| Past windows (a bearish call is right when the S&P fell) | Windows | Right | Normal |
|---|---|---|---|
| All | 236 | 41% | 39% (p 0.28) |
| Like 1–15 Jan | 70 | 36% | 40% |
| Like 1–15 Jan, 7+ days | 28 | 43% | 38% (p 0.40) |
| Like 25 Jan | 32 | 42% | 41% |

  - **Verdict:** no edge on the S&P.
  - Our S&P table is bearish all January for its own reasons: Venus–Uranus opposition; Mercury–Rahu conjunction; the Mercury–Saturn 2/12 big-move factor from 27 Jan.
- **Sensex:** see below.

**Mercury Paap Kartari and the Sensex, January 2027**

- **Windows (IST):**
  - 1 Jan 22:37 – 16 Jan 08:18: Sun | Pluto. Mercury is in Sagittarius, combust, and aspected by Jupiter. It covers 10 Sensex sessions, 4–15 Jan, from the 1 Jan close.
  - 25 Jan 13:31 – 26 Jan 09:21: Sun | Rahu. Mercury is in Capricorn, not combust, and aspected by Jupiter. The 25 Jan session is the only one; 26 Jan is Republic Day and the BSE is closed.
- **What the record says** (236 Sensex windows since 2000; a bearish call is right when the Sensex fell more than 0.5% over the scored horizon):

| Group | Windows | Right | Normal | p |
|---|---|---|---|---|
| All | 236 | 48% | 41% | 0.027 |
| Sun is one of the malefics | 197 | 50% | 41% | 0.008 |
| No benefic aspect | 115 | 50% | 40% | 0.03 |
| A benefic aspects Mercury | 121 | 46% | 41% | 0.21 |
| Past windows like 1–15 Jan (Sun in the pair, combust, benefic aspect) | 70 | 42% | 41% | — |
| The same, 7+ days long | 28 | 43% | 38% | 0.37 |
| Past windows like 25 Jan | 32 | 63% | 43% | 0.019 |

  - **Benefic aspect:** it removes most of the edge, as B116 itself says ("very volatile and both side movement"). The data does not show extra volatility: big days per window are no higher.
  - **The 1–15 Jan window:** no reliable bearish tilt.
  - **The 25 Jan match:** picked after the fact from about 13 groups. Its average and median moves point in opposite directions. Not reliable.
  - **Separately:** our Sensex table is bearish all January (Venus–Uranus opposition; Mercury–Rahu conjunction, High on 11–18 and 26–27 Jan).

**The calendar, 24 Nov – 31 Dec 2026** (`calendar_2026-11-24_to_2026-12-31_ET.html`, user request 24 Nov 2026: one complete, verified page that replaces the earlier forward pages)

- **Holidays:**
  - BSE closed 24 Nov for Guru Nanak Jayanti (confirmed: no trades on 24 Nov IST; exchange holiday lists).
  - NYSE closed 26 Nov and 25 Dec, with early closes 27 Nov and 24 Dec.
  - COMEX has no settlement on 26 Nov or 25 Dec.
- **Verification:** 11 automatic checks, all passed:
  - days and holidays;
  - probability ranges;
  - labels equal the published tables;
  - no duplicate sky events;
  - positions recomputed within 1 arc-minute;
  - Solar return month starts at tropical 27°18';
  - a daily call for every session;
  - every rule shown with its record;
  - naming;
  - no dashas.
- **Why the Sensex scored higher than the S&P:**
  - The market table uses only rules that held on both indices, so its labels were identical on both: 16 of 16 sessions on 1–23 Nov, and 40 of 40 labelled days in the last 60 days.
  - The labels leaned bullish, and the two markets moved opposite ways: Sensex +10.2% and S&P −6.1% over 60 days; up 12 of 15 days and 6 of 16 days on 1–23 Nov.
  - Over 2013–2026 the S&P is no worse: 55% against 54% over 5 sessions.
  - The Sensex session ends before New York opens, and labels use astrology only, so there is no look-ahead.

**Solar return, generated by us** (`solar_return_generated_ET.html`, user request 24 Nov 2026)

- **Monthly charts:** our reconstruction reproduces both monthly charts Solar return shared.
  - 20 Oct gives "Bearish": debilitated Saturn and Mars–Ketu in the 8th.
  - 19 Nov gives "Weak, moderated": Venus in the 10th.
- **Daily calls:**
  - **The rule:** bearish aspects first (Sun square Mars, Mars–Ketu). Jupiter sextile Venus within 1° is bullish. Mars square Uranus alone is volatile. Any other day takes the month's reading.
  - **Fit:** it matches 8 of the 9 days Solar return called (16–27 Nov). Only Fri 20 Nov differs: Solar return said up.
  - **Caveat:** the ordering and the 1° orb were chosen to fit those 9 days.
- **Upcoming generated months:**
  - 19 Dec 2026 – 17 Jan 2027 (Libra rising) and 17 Jan – 16 Feb 2027: no stated indication.
  - 16 Feb – 18 May 2027: "Supported", with Jupiter or Venus in the 10th. This differs from Solar return's own view of a bottom in Mar–May, so Solar return reads more than it has shared with us (for example the Mars–Ketu transits and retrograde Mars).
  - Aug, Oct and Nov 2027: "Pressure", with malefics in the 8th.
- **Upcoming daily calls:**
  - Bearish 24–25 Nov.
  - Bullish 27 Nov (Jupiter–Venus exact).
  - Volatile 30 Nov – 11 Dec (Mars square Uranus).
  - Bearish 14–18 Dec (month reading).
  - No call from 21 Dec.
- **What the method is worth, 1928–2026:**
  - **Generated monthly readings, 1,186 months:** bearish-leaning months rose 63.3% of the time and supportive ones 57.0%, against 60.5% for all months. They do not call the month.
  - **The calibrated daily rule:**

| Call | Days | Right, same day | Right, next 5 sessions | Market base rate |
|---|---|---|---|---|
| Bearish | 9,485 | 47.0% | 42.9% | down 47.6% / 43.8% |
| Bullish | 2,429 | 53.4% | 56.8% | up 52.4% / 56.2% |

  - **Verdict:** at chance. We can reproduce what Solar return says, but the reproduced method has had no edge over 98 years.

**Decision, 24 Nov 2026: dashas parked.** The user ended the dasha work after these results; work continues with the Solar return method.
- The dasha reports (`dasha_transits_ET.html`, `dasha_combinations_ET.html`) stay as reference.
- The combined model no longer uses the USA/NYSE dasha layers. Gochara, Chandra bala, Tara bala and the Solar return Jupiter sextile Venus remain.
- The day-by-day pages no longer show or score dashas (`USE_DASHA = False`).
- On 1–23 Nov, all methods pooled without dashas: 53% right the same day (163/307), 48% over 5 sessions (112/235).

**Dasha combinations read classically** (user request, 24 Nov 2026: "Antardasha → Pratyantar → Sookshma → Prana compared with the charts"; `dasha_combinations_ET.html`)

- **Natal charts (sidereal, whole sign):**
  - **USA:** Scorpio rising. Sun, Venus, Mars and Jupiter are in the 8th (Gemini); Mercury and Rahu in the 9th; Saturn in the 11th; Moon in the 4th.
  - **NYSE:** Cancer rising. Sun and Mercury are in the 11th; Venus and Saturn in the 10th; Mars in the 2nd; Jupiter in the 4th; Moon and Ketu in the 9th.
- **Method:** BPHS dasha principles. Each lord scores +1 or −1 on nine factors, and the factors and thresholds were fixed in advance.
- **S&P test, 1928–2026:** 132 tests (2 charts × 4 levels × each factor, plus the combination and the daily chain).
  - **None holds:** none points the classical way, passes q < 0.10 and agrees in both halves.
  - **Direction is a coin toss:** 66 of 132 point the classical way.
  - **The strongest results (|t| ≈ 2.5) point against the classical reading.** For example, USA Prana lords ruling dusthanas ran −3.9% a year against +7.8%, but in neither half was it significant.
- **On 1–23 Nov:** the classical chain called "helps" through most of the fall.
  - USA chain right 50% of days the same day, 30% over 5 sessions.
  - NYSE chain right 43% / 17%.
- **Coming:**
  - USA: Saturn Pratyantar scores +3, "helps", which is the opposite of the −11% so far. Venus Sookshma −1 (to 9 Dec); Sun 0; Moon +2 (17–29 Dec).
  - NYSE: Mercury Sookshma −2, "hurts" (14 Nov – 2 Dec; S&P −8.6% so far); Ketu −1; Venus +6, "helps" (9–30 Dec).
  - Shown as illustrations: the test gives them no weight.

**Model v1.0 (Ch.41 + Shadbala + Ashtakavarga), 6,572 trading days:**
- The correlation of the scarcity index with the next 5 days is −0.002.
- The model leans bullish on 67% of days by construction.
- Use it as classical context, not as a timing tool.

## 8. Open items

- **External forecasts are tracked in `tools/author_forecasts.py`**: the week of 23–27 Nov (check 28 Nov), the solar month to 18 Dec (check 19 Dec), and the Oct 2026 – Oct 2027 path.
- **External forecast to check on 19 Dec 2026:** Solar return expects a smaller net S&P decline over 19 Nov – 18 Dec 2026 than the previous month's −4.8% (from 7,320).

- Brihat Samhita 41.12 has a translation ambiguity: Sastri reads "fetch good price and have great demand", another translation reads moderate prices and easy availability. Kept visible; V is not a stand-alone signal.
- A rule for a stellium on the Sun (the January 2026 gap) has no source yet.
- 26-year backtests are done (`*_backtest_2000-11-20_to_2026-11-20_ET.*`). The astronomy layers for 2000–2024 are git-ignored and rebuilt on demand, which takes about 10 s per year.

## 9. Rebuild

    python tools/refresh_all.py --prices      # fresh prices, then every report, backtest, model, tracker and test
    python tools/refresh_all.py               # same, using the prices already in the repo

Then add an entry to `build/pdfref/analysis_log.json` for any new analysis, and re-run `python tools/gold_tracker.py` and `python tools/gold_tracker.py --metal silver`.
