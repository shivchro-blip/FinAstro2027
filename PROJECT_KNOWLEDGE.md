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
| Added 27 Nov 2026: Tajika Neelakanthi (Hindi/Sanskrit, Chowkhamba; legacy-font text, 300 pp.) | `Others/Tajikneelkanthi.pdf`; OCR in `extracted/ocr/tajika_neelakanthi.txt` | Read 27 Nov 2026: `extracted/NEW_SOURCES_REVIEW_2026-11.md` (N1–N9, T-rules). Not implemented yet |
| Added 27 Nov 2026: Balabhadra's Hayanaratna, "The Jewel of Annual Astrology", ed. and tr. M. Gansten (Brill 2020, Sanskrit–English, 1044 pp.) | `Others/9789004433717-57015.pdf` | Read 27 Nov 2026: `NEW_SOURCES_REVIEW_2026-11.md` (N4, N5, T1–T11). Not implemented yet |
| Added 27 Nov 2026: Brihat Samhita of Varahamihira (scanned edition, 496 pp.) | `Others/b29353130.pdf` (N. Chidambaram Iyer's English translation, 1884) | Read 27 Nov 2026: `NEW_SOURCES_REVIEW_2026-11.md` (B1–B15). Not implemented yet |
| Not added (over GitHub's 100 MB limit): Dreyer, *Vedic Astrology* (463 MB) and BPHS in Hindi (125 MB) | user's PC only | BPHS is already here in two English translations (Santhanam, G.C. Sharma) |

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
| `tools/solar_return_engine.py` | Solar return in four models: A tropical and B sidereal monthly degree returns, C/D annual return ÷ 12. Natal: NYSE 10:10 LMT, with alternative birth times as sensitivity. Placidus and whole-sign houses, mean and true node. Applies an orb-weighted aspect rubric (the user's 24 Nov spec), tests it on the S&P 1928–2026 against an always-bullish baseline, verifies the given 2027 timestamps and casts charts to Dec 2027 |
| `tools/gold_jupiter_crash.py` | The user's gold-crash note (Jupiter–Saturn trine/aspect/conjunction, Jupiter with a node or Pluto, Jupiter hemmed, malefic Vedha on Jupiter). Checks each claimed year from its peak to the low within 12 months, measures how common each condition is on monthly gold since 1972 (`backtest/gold_monthly_1833.csv`, datasets/gold-prices), and lists active spans to end-2027 |
| `tools/gold_turns.py` | Gold's major peaks and bottoms (15% zigzag; monthly 1972–1999, daily 2000–2026): sidereal degrees of every body at each turn, station proximity, Jupiter–Saturn angle, Jupiter afflictions and Vedha. Tests which features recur at bottoms and peaks against all weeks, and gives watch windows for the current fall |
| `tools/jupiter_saturn_gold.py` | Jupiter–Saturn aspects in a 10° orb (degree-based; exact passes to the minute) for Nov 2026 – Dec 2030, verified against the user's list. Shows every past window since 1972 with gold's turns, classified by the nearest anchor (orb entry / exact / exit). Gives a plain bottom-or-top table, which also includes Jupiter and Saturn direct stations |
| `tools/new_sources_test.py` | Backtest of the rules from the three new books (BS Iyer, Tajika Nilakanthi, Hayanaratna): BS 42.6 with eclipses, Moon north/south, Mercury reappearance, nakshatra and lord rules, Tajika monthly and annual charts → `new_sources_test_ET.html` |
| `tools/new_sources_leftover.py` | The leftover new-source rules (B5, B6, B7, B9, B10, B11, B13, T4, T6, T10), Tajika five-dignity strength and ruler of the year, and the calendar layer read by `calendar_2026.py` → `new_sources_leftover_ET.{html,json}` |
| `tools/week_deep_dive.py [nov] [dec] [jan] [feb] [mar] [apr] [may] [jun] [jul] [--reuse-days]` | Every week of November and December 2026 and of January to July 2027 (December from the 2026 calendar, the others built with `forward_daybyday.build`; `--reuse-days` reuses the cached day data): every sky event as an event class backtested on 4 markets (next session, 5 sessions, big days; BH per week) with 4 automatic checks, plus each day's rules, labels, model, Solar return, Kartari, gold notes and new-source items → `deep_dive_*_ET.json`. November uses history to 31 Oct 2026 only, so no November event scores itself |
| `tools/november_review.py` | November 2026 review: every call of every layer scored against what the markets did (pass / fail at 0.5%, against chance for the same up/down mix; recount checked against `forward_daybyday.score`), where it failed (rules behind each label, spans, wrong calls, big days, deep-dive leans), and the tuning tests on the long records (clean walk-forward labels and model, label strengths, each table rule as a day call, big-day flags, volatility factors, 24 Sep – 27 Nov) → `november_review_2026-11_ET.json` with the recommendations the two calendars apply |
| `tools/bigday_clean_test.py` | Clean walk-forward test of the big-day volatility factors: the published choice (q < 0.10, lift > 1 in both halves, p < 0.01 without the 2008–09 crash) made on 20 Nov 2000 – 19 Nov 2013 only for each market, over every factor of `big_move_analysis.py`, then scored 20 Nov 2013 – 31 Oct 2026 (year-stratified expected big days, without Feb–May 2020, leave one year out, each factor). Also: the S&P's picks on the Sensex, looser choices, and a check that the same choice on 2000–2026 reproduces the published robust sets → `bigday_clean_test_ET.json` (read by `november_review.py` and both calendars) |
| `tools/month_outlook.py [2027-MM ...]` | A coming month after the November review (default: every 2027 month whose day data is built; January to July so far). Lists every kind of call — labels and the rules behind them, combined model, Model v1.0, Solar return and its transit rules, Paap Kartari B116/B117, big-day factors — with its best out-of-sample evidence. A table rule that the 2000–2013 choice picks is judged by its span record after 2013, with BH over the 22 tests. For B116 it tests the case that applies (with or without a benefic aspect) on direction and big days. Writes `<month>_<year>_outlook_ET.json`, and freezes the month's calls into `<month>_<year>_calls_ET.json`: rewritten until the day before the month starts (ET), never after. Replaced `january_2027_outlook.py` |
| `tools/deep_dive_render.py` | Renders the 2027 monthly deep dives (January, February) into `calendar_2027_NY_master.html` with a month index (called by `build_pdf_calendar.py`; `--html-only` re-renders from the JSON). Applies the November review's changes (Low labels as leans, model percentages uncoloured, Volatile labels marked by the clean big-day test) |
| `tools/gold_tracker.py [--metal silver]` | Trackers: findings, rule status, best-rule dates, analysis log |
| `tools/build_year.py YEAR` | Astronomy layer for any year; 2000–2024 are git-ignored and rebuilt on demand |
| `tools/fetch_prices.py` | Downloads GC=F and SI=F (Yahoo; the host must be allowed) |
| `tools/refresh_all.py [--prices]` | Rebuilds everything in order, runs the tests, re-publishes `reports/` |
| `tools/publish_reports.py` | Copies the two kept calendars (2026 to year end, 2027 NY master) and the calendar .ics files into `reports/`; removes any other HTML there |
| `tests/test_pdfref.py`, `tests/test_shadbala.py` | PDF-rule checks; Shadbala vs B.V. Raman's worked example |

## 5. Outputs (`build/pdfref/`; since 27 Nov 2026 only the two calendars are kept as HTML, in `reports/`; the other pages below are rebuilt locally by their tools but git-ignored)

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
| `jupiter_saturn_gold_ET.html` | Jupiter–Saturn aspects and gold: bottom or top, 2026–2030 |
| `gold_turns_ET.html` | Gold turns since 1972 and the bottom-watch windows |
| `gold_jupiter_crash_ET.html` | Gold crashes and Jupiter's afflictions, checked |
| `solar_return_engine_ET.html` | Solar return engine: models, rubric, sensitivity, tests, charts to Dec 2027 |
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

**Jupiter–Saturn aspects and gold, 2026–2030** (user list, 25 Nov 2026; `jupiter_saturn_gold_ET.html`; table also in the 2026 calendar's gold section)

- **Verification:** every date the user gave matches our ephemeris to the minute: the trine window 14 Feb – 30 Aug 2027 (exact 3 Apr 08:59 and 11 Jul 19:15) and the three opposition windows of 2028–2030 (exact 22 Dec 2029, 23 Apr 2030, 19 Nov 2030).
  - The degree-based trine differs from the earlier sign-based spans (25 Jan – 2 Jun and 26 Jun – 19 Oct 2027).
- **Past windows since 1972: gold's turns by the nearest point of the window:**

| Point of the window | Tops | Bottoms |
|---|---|---|
| Trine: orb exit | 4 (1973, 1974, Mar 2008, Jan 2026) | 1 |
| Trine: orb entry | 3 | 2 |
| Trine: exact passes | 4 | 4 |
| Opposition | 0 | 2 |

- **Stations within ±30 days:**
  - Jupiter direct: 8 bottoms vs 5 tops.
  - Saturn direct: 7 bottoms vs 1 top.
- **The plain table:**

| Date | Event | Reading |
|---|---|---|
| 11 Dec 2026 | Saturn direct | Bottom-leaning (weak) |
| 14 Feb 2027 | Trine enters orb | Either way |
| 3 Apr 2027 | Exact trine | Either way |
| 13 Apr 2027 | Jupiter direct | Bottom-leaning (weak) |
| 11 Jul 2027 | Exact trine | Either way |
| 30 Aug 2027 | Trine leaves orb | Top-leaning |
| Late 2027 – 2030 | Saturn and Jupiter direct stations | Bottom-leaning (weak) |
| 2028–2030 | Oppositions | Either way (1 bottom, 0 tops in history) |

- Small samples: leads, not rules.

**Gold's peaks and bottoms since 1972, and the current fall** (user request 25 Nov 2026; `gold_turns_ET.html`)

- **Turns:** a 15% zigzag gives 24 bottoms and 25 peaks since 1972. The current fall from the 24 Aug 2026 peak (4,698) is −25% to 20 Nov and not yet a confirmed bottom.
- **At bottoms, against all weeks:**

| Feature | Bottoms | All weeks | p |
|---|---|---|---|
| Jupiter–Saturn within 10° of trine, opposition or conjunction | 42% | 20% | 0.014 |
| Jupiter direct station within ±30 days | 33% | 15% | 0.02 |
| Saturn direct station within ±30 days | 29% | 16% | 0.08 |

- **At peaks:** the Jupiter–Saturn trine was at 36% vs 16% (p 0.012). The trine marks turns either way, not direction.
- **Multiple testing:** about 40 features were tested, so these are leads.
- **Watch windows for the current fall:**
  - **11 Nov 2026 – 10 Jan 2027.** Saturn stations direct on 11 Dec at Pisces 13.7°. Jupiter stations retrograde on 13 Dec at Leo 2.8°.
  - **14 Mar – 13 May 2027.** Jupiter stations direct on 13 Apr at Cancer 22.75° (Ashlesha), within 0.5° of Ketu, with Mars at Cancer 27.5° and Saturn trine within 1.4°.
  - The second window coincides with:
    - Solar return's Mar–May 2027 bottom.
    - The Mars–Jupiter–Ketu-in-Cancer lead (9 Mar – 26 Apr).
    - The end of malefic Vedha on Jupiter (9 Apr).

**Gold crashes and Jupiter's afflictions** (user note, 25 Nov 2026; `gold_jupiter_crash_ET.html`; sidereal Lahiri; monthly gold since 1972 and daily COMEX since 2000)

- **Crashes, from each year's high to the low within 12 months:**

| Year | Fall | Dates |
|---|---|---|
| 1974 | −24.5% | Dec 1974 → Dec 1975 |
| 1980 | −23.9% | Jan → May 1980 |
| 2008 | −29.7% | 18 Mar → 13 Nov |
| 2011 | −18.7% | 22 Aug 2011 → May 2012 |
| 2020 | −18.9% | 6 Aug 2020 → 8 Mar 2021 |
| 2022 | −20.2% | 8 Mar → 3 Nov |
| 2026 | −33.9% | 29 Jan → 20 Nov |

- **Positions:** mostly right, with sidereal corrections:
  - 1974: Jupiter in Aquarius trine Saturn in Gemini. ✓
  - 1980: Jupiter with Rahu in Leo. ✓ Saturn was in Virgo at the January peak and joined them in Leo from about March. Pluto was in Virgo.
  - 2008: Jupiter and Pluto in Sagittarius, trine Saturn in Leo, for the whole fall. ✓
  - 2011: at the August peak Saturn was in Virgo. The Aries–Libra opposition came only from 15 Nov 2011 (68% of the fall); Jupiter was hemmed throughout.
  - 2020: Jupiter with Ketu and Pluto. ✓
  - 2022: Jupiter entered Pisces on 13 Apr. Saturn aspected Jupiter for 54% of the fall and hemmed it for 49%. ✓
  - 2026: Jupiter was retrograde in Gemini at the January peak. The Cancer–Pisces trine held for 51% of the fall (from June); Jupiter–Ketu in Leo from 12 Nov.
- **Vedha:** malefic Vedha on Jupiter occurred in every fall (11–82% of the time). But it holds in 28% of all months because of the fast Sun and Mars.
- **How common, 1972–2026:**
  - "Jupiter afflicted" (any of the conditions) holds in 69% of months and at 6 of 8 crash peaks, so it does not single out crashes.
  - Jupiter–Saturn trine was at 3 of 8 peaks against 16% of months. Gold's next 6 months: +1.9% vs +5.9%, but 10%+ falls were *less* common (6.9% vs 10.9%).
  - Jupiter–Saturn conjunction and Jupiter with Pluto were followed by 10%+ falls more often: 21% and 20%, against 9%.
  - Small, overlapping samples: leads only.
- **When the current one ends:** Jupiter with Ketu in Leo ends on 5 Dec 2026. The pattern returns while Jupiter is back in Cancer:

| Condition | Dates |
|---|---|
| Jupiter with Ketu | 25 Jan – 25 Jun 2027 |
| Jupiter–Saturn trine | 25 Jan – 2 Jun and 26 Jun – 19 Oct 2027 |
| Malefic Vedha on Jupiter | 6 Dec 2026 – 9 Apr 2027 |
| All together | 25 Jan – 9 Apr 2027 |

  - Jupiter in Paap Kartari (B117) runs to 31 Jan 2027.

**Why the Solar return reading missed, month by month** (`solar_return_engine_ET.html` §6; 20 Nov 2025 – 24 Nov 2026; astrology and prices only)

- **Scoreboard:** 4 right (Nov 2025 Supported; Feb, Aug and Oct 2026 Bearish), 6 wrong (Mar, Apr, May, Jun, Jul and Sep 2026), 2 with no stated indication, 1 still open.
- **1. No edge to begin with.** Since 1928, months read "Bearish" rose 69.6% of the time and "Pressure" months 62.8%, against 60.5% for all months. The indications are not bearish in the data, so a run of misses in a rising year is what the record predicts.
- **2. Fragile readings.**
  - 12 of the 13 readings change under at least one plausible alternative: the exact natal degree (27°17′39″ vs 27°18′), the birth time (07:52 or 11:15), Placidus houses, or the sidereal zodiac.
  - Even the Oct 2026 success flips to "no indication" with the 10:10-LMT natal degree, a shift of 9 minutes. Only Jan 2026 is stable.
- **3. One snapshot for the whole month.** The reading comes from the start-of-month chart only, while the market path inside the month did the work:
  - Mar 2026: −2.8% in the first half, then +7.9%.
  - May 2026: +2.7%, then −2.5%.
  - The misses that count: Mar (+4.8%), Apr (+5.2%) and Jul (+3.4%).
  - May (+0.2%), Jun (+0.5%) and Sep (+0.5%) were near-flat. May is FLAT by the project's 0.5% rule.
- **4. The transit layer and our tables did not rescue it.**
  - Jupiter sextile Venus ran inside the missed Mar and Jul months.
  - Our S&P table leaned bullish in Jun and Jul but bearish in Mar and May, and was wrong there too.
- **What this means:** the problem is the method's foundation (indications with no record, house readings that depend on an unknown birth time), not a calculation error. Solar return's own published calls appear to add judgement that the stated indications do not capture.

**Solar return over the past year** (20 Nov 2025 – 24 Nov 2026, S&P closes; `solar_return_engine_ET.html` §5)

| Method | Right | Always-bullish baseline |
|---|---|---|
| Monthly stated-indication reading, the Solar return way (27°18′, which reproduces the shared charts) | 4 of 10 monthly calls | 8 of 12 months up |
| Rubric, model A | 3 of 6 | — |
| Rubric, model B | 1 of 5 | — |
| Rubric, model C | 3 of 6 | — |
| Rubric, model D | 2 of 6 | — |
| Daily calls, bearish (184 days): same day / next 5 sessions | 50% / 49% | 49% / 48% down |
| Daily calls, bullish (25 days): same day / next 5 sessions | 56% / 64% | 51% / 52% up |

- **Months the readings got wrong:** the "Bearish" Mar and Apr 2026 months rose 4.8% and 5.2%. The Oct 2026 bearish month was right (−4.8%).
- **Solar return's own published calls** cover only Oct–Nov 2026: the month right, the week of 16 Nov 4 of 5, the week of 23 Nov 1 of 2 so far.

**Solar return engine** (`solar_return_engine_ET.html`; built from the analysis the user pasted on 24 Nov 2026)

- **Natal check:** at 10:10 LMT the NYSE Sun is 27°17′39″ Taurus tropical and 6°20′11″ Lahiri, which confirms the pasted figures.
  - The pasted "Ascendant 19°51′ Aries" is impossible for 10:10 AM. It is Leo 11.6° (tropical, Placidus).
  - Over the disputed times (07:52–11:15) the ascendant runs from Cancer 13.9° to Leo 24.3°, while the boundaries move only −6 to +3 minutes.
- **The given 2027 timestamps:** all reproduced within 1 minute, for both the tropical and sidereal models.
- **Sensitivity:**
  - The house-based indications change in 32.6% of months between Placidus and whole sign, against 1.6% between the true and mean node.
  - Model A's natal degree (27°17′39″ vs the 27°18′ that reproduced the shared charts) moves each boundary by about 9 minutes. That flips the 19 Dec 2026 rising sign between Virgo and Libra.
- **Rubric test, 1186 months, S&P 1928–2026** (orb weights 4/3/2/1; Solar return's Sun□Mars, Mars☌Ketu, Mars□Uranus, Mercury in Pisces, plus the analysis's Saturn–Sun, Jupiter–Sun and Venus–Jupiter):

| Model | Calls right | Always bullish |
|---|---|---|
| A, tropical monthly | 44.6% | 60.9% |
| B, sidereal monthly | 46.7% | 59.1% |
| C, tropical annual ÷ 12 | 45.0% | 60.1% |
| D, sidereal annual ÷ 12 | 47.8% | 58.9% |

  - Every model is worse than calling every month up, in each half and since 2010.
  - D's bearish months averaged 0.14% against 0.84% for the others (t -1.85). Not significant.
  - Volatility scores do not mark more big days.
  - **Items on their own (model A):**
    - Saturn square Sun: fell 48.5% vs 39.5% (66 months), consistent across models but not significant after about 40 item tests.
    - Jupiter sextile Venus: 63.5% vs 60.5%.
    - The rest are at chance.
- **Charts now:** all four models call the 19 Nov chart bearish (net −2 to −5: Sun□Mars, Mars☌Ketu) and the December chart bullish (+1 to +3: Jupiter△Sun).
- **2027, model A:**

| Month | Rubric reading |
|---|---|
| Jan | Neutral |
| Feb | Bearish: Mars□Uranus and Mercury in Pisces |
| Mar | Bearish: Mars☌Ketu |
| Apr | Neutral |
| May | Bearish |
| Jun | Neutral |
| Jul | Bearish: Saturn□Sun |
| Aug, Sep | Neutral |
| Oct | Bullish |
| Nov | Neutral |
| Dec | Bullish |

  - This partly matches Solar return's own path (weak into spring, bottom Mar–May), but the rubric itself has no track record.
- **In the calendar:** shown in the 2026 calendar's Solar return section.

**Deep dives and updates, April to July 2027 (28 Nov 2026)** (`tools/week_deep_dive.py apr may jun jul`, `deep_dive_2027-0[4-7]-*_ET.json`; `tools/month_outlook.py`, `<month>_2027_outlook_ET.json`, `<month>_2027_calls_ET.json`; 2027 calendar → "Deep dive: April … July 2027")

- **Holidays.** Each was checked against the price files: no bar on any recent occurrence.
  - Ambedkar Jayanti, 14 Apr (BSE): fixed date.
  - Memorial Day, 31 May; Juneteenth, observed Friday 18 Jun; Independence Day, observed Monday 5 Jul (S&P, gold, silver). COMEX had a bar on 4 Jul 2025 only.
  - Lunar-calendar BSE holidays are still not assumed.
- **New event class.** Planets entering and leaving fast motion: the speed crossing its calibrated level, as `build_2027.py` emits `speed_crossing` records. The levels come from `config/conventions.yaml` `speed_classes`: Mercury 1.744909, Venus 1.223981, Mars 0.658287°/day.
  - Occurrences 2000–2026, each way: Mercury 67, Venus 16, Mars 13. At most once per synodic cycle; Mercury's peak speed misses its level in some cycles.
  - The time check reads the sidereal speed, which is the frame the levels are defined in. The tropical speed differs by about 7×10⁻⁵°/day, which near Venus's peak moves the crossing by hours. A first pass with the tropical speed failed July's Venus check; with the sidereal speed, all three such events in the months pass.
  - April, May, June and July were rerun with the class from the cached day data.
- **Paap Kartari windows to the end of 2027.** `kartari_test.py` previously listed windows only to 28 Feb 2027, so the later months' notes and updates were missing:
  - Mercury (B116): 19–28 Apr, 23–27 May, 11 Dec 2027 – 7 Jan 2028.
  - Jupiter (B117): 19 Apr – 3 Aug and 31 Aug – 17 Oct.
  - The day notes in every 2027 deep-dive file were refreshed. The rerun also took in the newest prices, so the B116/B117 p-values moved slightly (Sensex B116 0.0268 → 0.0265).
- **Deep dives.** Every week passes its 4 checks (20/20 per month) and every month's 8 independent recounts match. Nothing passes the Benjamini–Hochberg correction in any month, and no class changes the chance of a big day.

| Month | Tests | Nominal (by chance) | Calls with some support |
|---|---|---|---|
| April | 2,035 | 41 (about 102) | none |
| May | 2,064 | 44 (about 103) | Mercury Paap Kartari 23–27 May, no benefic aspect (Sensex: past windows of this case bearish 50% vs 40%, p 0.03) |
| June | 1,948 | 34 (about 97) | Three Saturdays in Shukla Paksha, Bearish 14–18 Jun, Sensex only (held after 2013 on the Sensex: 55% vs 39%, p 0.049) |
| July | 1,992 | 33 (about 100) | Three Saturdays in Shukla Paksha, Bearish High 9–15 Jul, S&P (held after 2013: 58% vs 37%, p 0.014) |

- **Everything else is a leaning:**
  - S&P/Sensex labels: April Bullish Moderate 12–16 Apr and Bullish High from 28 Apr (Mars–Mercury Vedha, Moon–Rahu 6/8), plus Volatile spans from in-sample factors (S&P Mercury–Saturn 2/12, Sensex Venus in Pisces). May bullish to 14 May. June S&P Bullish Moderate 7–11 Jun. July mixed.
  - Mercury Paap Kartari 19–28 Apr: Jupiter and Venus aspect Mercury, B116's "volatile" case, which was neither bearish nor more volatile in the past.
  - Jupiter Paap Kartari 19 Apr – 3 Aug: its bearish record faded after 2013.
  - Gold and silver mostly bullish labels; the combined model; Model v1.0.
  - Solar return: bearish 11 / bullish 11 sessions in April; bullish 11 / bearish 7 in May. Its Sun square Mars rule has had more big days since 1928 (67 vs 50.6, p 0.016), but the rule claims bearish, not volatile. Volatile 4 sessions in June; no call in July. All day calls are at chance.
  - No factor that passed the clean big-day test is active in any of the four months.
- **Main sky events:**
  - April: Mars direct 1 Apr; Jupiter–Saturn trine 3 Apr; Mercury combust and into fast motion 11 Apr; Jupiter direct 12 Apr; Sun into Aries 14 Apr; Jupiter opposite Rahu 19 Apr; Mars into Leo 26 Apr; Saturn rises 27 Apr.
  - May: Mercury rises 6 May; Pluto retrograde 8 May; Mercury leaves fast motion and Sun into Taurus 15 May.
  - June: Saturn into Aries 2 Jun; Mercury retrograde 10 Jun; Sun into Gemini 15 Jun; Jupiter into Leo 25 Jun.
  - July: Venus into fast motion and Mercury rises 1 Jul; Mercury direct and Mars into Virgo 4 Jul; Neptune retrograde 9 Jul; Jupiter–Saturn trine 11 Jul; Sun into Cancer 16 Jul; Venus combust 20 Jul.
- **Frozen calls and checks:**
  - Each month's calls are frozen (rewritten until the day before the month starts, never after).
  - The 2026 calendar now finds every frozen month and deep-dive month on its own and checks each frozen file: 26 of 26 checks pass.
  - The 2027 calendar's 2,211 rows are byte-identical.

**Deep dive and update, March 2027 (28 Nov 2026)** (`tools/week_deep_dive.py mar`, `deep_dive_2027-03-*_ET.json`; `tools/month_outlook.py 2027-03`, `march_2027_outlook_ET.json`, `march_2027_calls_ET.json`; 2027 calendar → "Deep dive: March 2027")

- **Setup:**
  - Good Friday, 26 Mar 2027, is closed on all four markets. None of the last six Good Fridays has a ^GSPC, ^BSESN, GC=F or SI=F bar. It is assumed for the BSE as well because its date is certain.
  - Holi is not assumed: its BSE date shifts by a day between calendars (2023 and 2026 show bars on the dates tried).
  - The Solar return months now cover each run's range.
- **Deep dive:** 1,950 tests over 5 weeks, **0 pass** the Benjamini–Hochberg correction. 40 are nominal (about 98 expected by chance) and no class changes the chance of a big day. Double checks: 20 of 20 pass; 8 of 8 independent recounts match.
  - Nominal examples, all at chance after correction: Venus–Rahu exact conjunction (S&P next session 5 up / 14 down); Mercury entering Aquarius (gold 10 up / 0 down); the Moon entering Purva Bhadrapada (silver 162 up / 95 down).
- **March's main sky events:**
  - Jupiter opposite Rahu 1 Mar.
  - Mercury direct 3 Mar.
  - Venus with Pluto 6 Mar.
  - New Moon 8 Mar.
  - Mars into Cancer 9 Mar.
  - Mercury opposite Mars 11 Mar.
  - Sun into Pisces 14 Mar.
  - Venus opposite Jupiter and with Rahu 16 Mar.
  - Venus opposite Mars 19 Mar.
  - Full Moon 22 Mar.
  - Saturn combust 23 Mar.
  - Sun with Neptune 24 Mar.
- **Update (calls and their evidence):**

| Call | March | What it is worth |
|---|---|---|
| S&P / Sensex labels | Bearish Moderate to 8 Mar (Mercury–Rahu); Bullish Low 9–11 Mar; Bullish High 12–19 Mar (Mars–Mercury Vedha, Moon–Rahu 6/8, Mrigashira on Monday) | Labels at chance out of sample. All four rules were picked on 2000–2013 and leaned the right way after 2013, but none significantly (best: Mars–Mercury Vedha on the Sensex, 75% vs 57%, p 0.08) |
| S&P Volatile | 22 Mar – 5 Apr | From Mercury–Saturn 2/12, which has only an in-sample record |
| Mercury in Paap Kartari (B116) | To 16 Mar ET (17 Mar IST); no benefic aspect | Sensex: some support (past windows of this case bearish 50% vs 40%, p 0.03). S&P: not bearish |
| Gold / silver labels | Gold Bullish Low 11–12, Bearish Moderate 22–23, Bearish Low 24–25 Mar; silver Bullish High 8–31 Mar | At chance |
| Combined model | S&P 9 down-lean sessions; Sensex 6 down, 6 up | No edge |
| Solar return | Bearish 16 sessions (Mars conjunct Ketu, "disruption"), Bullish 6; both solar months "Supported" | Day calls at chance since 1928. Mars conjunct Ketu: up over 5 sessions 50.0% vs 56.2% (p 0.33), big days 72 vs 70.8 |
| Big days | No factor that passed the clean test is active | – |

- **Frozen calls:** March's calls are in `march_2027_calls_ET.json`, rewritten until 28 Feb 2027 and never after. The 2026 calendar checks the frozen labels against the tables (31 days). The 2027 calendar's 2,211 rows are byte-identical.

**February 2027 after the November review (28 Nov 2026)** (`tools/month_outlook.py 2027-02`, `february_2027_outlook_ET.json`, `february_2027_calls_ET.json`; 2027 calendar → "Deep dive: February 2027" → Update)

- **New check of single table rules** (`november_review.py` → `picked_rules`):
  - Each of the 11 rules that the 2000–2013 choice picks is scored on its own span record after 2013, on both indices.
  - Only Three Saturdays in Shukla Paksha passes on both: S&P 58% vs 37% (p 0.014), Sensex 55% vs 39% (p 0.049). That is 2 passes in 22 tests where about 1.1 are expected by chance, so after correction it is not significant (q 0.30 and 0.54).
  - 16 of the 22 tests leaned the right way. Pooled, the picked rules did only slightly better than chance after 2013: S&P 347 right vs 326.6 expected (p 0.07), Sensex 344 vs 333.6 (p 0.39).
- **February's calls with some support:**
  - **Bearish 8–19 Feb (S&P and Sensex):** the label rests on Three Saturdays in Shukla Paksha, the best-supported table rule, though not proven. Shukla Shashthi on a Friday (12–18 Feb) was not picked on 2000–2013, so it has no clean test.
  - **Mercury in Paap Kartari (B116), 18 Feb – 16 Mar ET (Sensex 18 Feb – 17 Mar IST):** no benefic aspects Mercury, which B116 reads as a negative event. Past windows of this case were bearish on the Sensex (50% vs 40%, p 0.03) and had more big days (×1.24, p 0.02). That is a 2000–2026 record of a source rule, not a walk-forward test. On the S&P they were not bearish (41% vs 38%), though big days were ×1.25 (p 0.02).
- **Everything else is a leaning:**
  - S&P Volatile 1–5 Feb (Mercury–Saturn 2/12, in sample only).
  - Bullish Moderate 22 Feb (Moon–Rahu 6/8; at chance after 2013).
  - Bearish Moderate from 23 Feb (Mercury–Rahu; leaned the right way after 2013, not significant).
  - Gold Bullish Low 12–23 Feb; silver bullish all month.
  - The model: 14 down-lean sessions on each index.
  - Solar return: volatile 10 sessions (Mars square Uranus; since 1928 no extra big days, 52 vs 52.9) and bullish 3. Its transit rules (Mars retrograde, Mercury in Pisces) are at chance.
  - No clean big-day factor is active.
- **Tool and calendars:** `month_outlook.py` now builds January and February in the same way; the January outlook gained the per-rule clean test. The 2027 calendar shows an update block at the top of each month's deep dive. The 2026 calendar has a check for each frozen month (31 and 28 days). The 2027 rows are byte-identical.

**January 2027 after the November review (28 Nov 2026)** (`tools/january_2027_outlook.py`, since renamed `tools/month_outlook.py`, `january_2027_outlook_ET.json`, `january_2027_calls_ET.json`; 2027 calendar → "Deep dive: January 2027" → Update; 2026 calendar → "January 2027")

- **Result: no January call has a tested edge on any market.**

| Call | January | What it is worth |
|---|---|---|
| S&P / Sensex labels | Bearish all month: Low 1–8 Jan (Venus–Herschel 7th); High 11–18, 22, 26–27 Jan (plus Mercury–Rahu conjunction); Low 19–21, 25, 28–29 Jan | Clean label record: S&P 52.4% vs 52.5% chance, Sensex 50.5% vs 52.2%. Venus–Herschel 7th day by day: S&P 50.0% vs 45.4% (in sample); not picked when rules are chosen on 2000–2013. Mercury–Rahu: 41.4% vs 42.1% after 2013 |
| Gold labels | Bullish Low (Mercury with the Sun), 21 Dec – 8 Jan, 14–22 and 25–27 Jan | Gold labels out of sample 50.0% vs 50.1% |
| Silver labels | Bullish High 1–13 Jan and 25 Jan – 5 Feb, Moderate 14–22 Jan | 53.3% vs 51.9% |
| Combined model | Leans down on 13 S&P and 8 Sensex sessions; no gold or silver leans | No edge out of sample on any market |
| Model v1.0 (gold) | Bullish to strong bullish on most sessions | 53.8% vs 53.6% (2000–2026) |
| Solar return | No stated indication in either solar month (19 Dec – 17 Jan, 17 Jan – 16 Feb) | Day calls at chance since 1928 |
| Big days | No factor that passed the clean test is active; Mercury–Saturn 2/12 on 4 S&P days is in sample only | – |

- **Mercury in Paap Kartari (B116):** windows 1–15 Jan and 25 Jan (ET); in IST 1–16 Jan and 25–26 Jan.
  - As a bearish rule it holds on the Sensex in general (48% vs 41%, p 0.027; both halves above chance) but not on the S&P (41% vs 39%).
  - In January, Jupiter aspects Mercury in every window. B116 says a benefic aspect makes it "very volatile and both side movement".
  - Past windows with a benefic aspect were not bearish (Sensex 46% vs 41%, p 0.21).
  - Nor did they have more big days. Days of ±2% against each year's own rate: S&P 45 vs 60.7 (×0.74); Sensex 88 vs 78.3 (×1.12, p 0.15).
  - Oddly, the windows *without* a benefic aspect had more big days: S&P ×1.25 (p 0.02), Sensex ×1.24 (p 0.02). That split is post hoc; it was found by looking and has not been tested.
- **Jupiter in Paap Kartari (B117)**, to 31 Jan: its bearish record faded after 2013 (S&P 30% vs 29%). More big days in past windows (S&P 11.6% vs 7.5%) was not significant.
- **Frozen calls:** January's calls are saved in `january_2027_calls_ET.json`: labels, model, rules tally, calendar verdicts, Model v1.0, Solar return, the Mars–Jupiter–node lead, big-day factors and watch windows. `refresh_all` rewrites the file until 31 Dec 2026 and never from 1 Jan 2027. January can then be scored afterwards with the November scorer, on the calls as published.
- **Display:** the 2027 calendar's January section opens with the update (a call-by-call table). The 2026 calendar's January section opens with the summary and the B116 big-day table. A new verification check confirms the frozen labels equal the published tables (31 days). The 2027 calendar's 2,211 rows are byte-identical.

**Clean test of the big-day volatility factors (28 Nov 2026)** (`tools/bigday_clean_test.py`, `bigday_clean_test_ET.json`; 2026 calendar → November review → "Clean test of the big-day volatility factors")

- **Why:** the robust big-move factors (`market_summary.py`) behind the "volatility factor" notes, the tables' Volatile label and the model's big-move layer were chosen on all of 2000–2026, so their record after 2013 was partly in sample.
- **Method:**
  - Universe: every factor of `big_move_analysis.py` for the market (730 for the S&P and Sensex, 258 gold, 263 silver).
  - Choice made on 20 Nov 2000 – 19 Nov 2013 only, with the published criteria moved inside that period: q < 0.10 over all factors, lift > 1 in both halves (split 20 May 2007), and p < 0.01 without Sep 2008 – Jun 2009.
  - Score on 20 Nov 2013 – 31 Oct 2026: big days (±2%; silver 3.5%) on days with any picked factor, against the count expected from each year's own big-day rate (one-sided Poisson).
  - Check: the same choice on all of 2000–2026 reproduces the published robust sets exactly (6 factors each for the S&P and Sensex).

| Market | Chosen on 2000–2013 | Big days 2013–2026 | Without Feb–May 2020 | Verdict |
|---|---|---|---|---|
| S&P | Venus retrograde; Jupiter–Pluto 5/9 | 44 vs 31.0 (×1.42, p 0.016) | ×1.60 (p 0.002) | holds |
| Sensex | nothing | – | – | no clean test of its own factors |
| Sensex, with the S&P's two picks | Venus retrograde; Jupiter–Pluto 5/9 | 38 vs 25.4 (×1.50, p 0.011) | ×1.54 (p 0.013) | holds |
| Gold | Sun–Uranus opposition | 2 vs 2.9 (×0.68) | ×0.73 | does not hold |
| Silver | Sun in Aries | 22 vs 25.1 (×0.88) | ×0.85 | does not hold |

- **Each factor after 2013:**
  - S&P: Venus retrograde ×1.52 (p 0.04); Jupiter–Pluto 5/9 ×1.77 (p 0.002).
  - Sensex: Venus retrograde ×1.87 (p 0.007); Jupiter–Pluto 5/9 ×1.39 (p 0.08).
- **Caveats:**
  - The S&P result leans on 2025: April's sell-off came during Venus retrograde. Without 2025 it is ×1.25 (p 0.12); without any other single year it stays significant.
  - The Sensex cross-check survives dropping any one year (worst: without 2016, ×1.45, p 0.03).
  - Looser choices dilute the result to chance: q < 0.20 gives the S&P 3 factors at ×1.11; every lead with p < 0.05 gives 43 factors at ×0.99. The finding rests on these two factors.
  - The plain big-day rate on S&P factor days is 6.3% vs 5.1% on other days (p 0.22). The year-stratified count is the published method; the plain rate ignores which years were volatile.
- **Not clean (in sample only):**
  - S&P: Jupiter–Neptune 7th, Mercury–Saturn 2/12, Jupiter–Herschel 6/8.
  - Sensex: Mars–Saturn conjunction, Mars with Saturn, Venus in Pisces, Mars–Herschel 5/9.
  - The model's big-day chance, whose Sensex lift came through those factors.
- **Applied:**
  - The model's big-day chance is shown as untested for every market. This replaces "Sensex only" from the November review.
  - "Volatility factor" notes and Volatile labels say "passes a clean test" or "in sample only"; a Volatile label is grey unless its factor passed.
  - The 2027 deep-dive sections mark the S&P's Volatile days on 1–5 Feb 2027 (Mercury–Saturn 2/12) "in sample only".
  - No clean factor is active in December 2026. Next: Jupiter–Pluto 5/9 for the S&P on 28–31 Dec 2027; Venus retrograde in 2028.
  - The 2027 calendar's 2,211 rows are byte-identical.

**November 2026 review: pass / fail against the markets, and what changes (28 Nov 2026)** (`tools/november_review.py`, `november_review_2026-11_ET.json`, `tools/week_deep_dive.py nov`; 2026 calendar → "November review")

- **Method:**
  - Every call the calendar's layers made for 1–27 Nov (combined model fitted before 1 Nov) scored against the price files. A call **passes** when the market moved its way by 0.5% or more and **fails** when it moved the other way by 0.5% or more; smaller moves are too small to count.
  - "By chance" = what calls with the same up/down mix would score, from the up share of the same period (November; each Nov–Nov year on the long records). p-values are exact (Poisson-binomial); 5-session results on consecutive days use a 5× variance because they overlap.
  - Recount check: 33 of 33 layer counts equal `forward_daybyday.score`. Sensex 27 Nov uses the Yahoo quote close (83,339.26) because the daily bar had none.
- **November itself:** S&P −3.7% (7 up / 12 down sessions, 5 big days), Sensex +11.9% (14 / 4), gold −5.9%, silver −11.0% (8 big days each).

| Layer (that day) | S&P | Sensex | Gold | Silver |
|---|---|---|---|---|
| Table label | 4 ✓ 6 ✗ (40% vs 46% chance) | 8 ✓ 2 ✗ (80% vs 77%) | 5 ✓ 5 ✗ (50% vs 38%) | 4 ✓ 5 ✗ (44% vs 39%) |
| … Low labels | 2 ✓ 4 ✗ | 5 ✓ 1 ✗ | 4 ✓ 4 ✗ | – |
| Combined model, all layers | 4 ✓ 4 ✗ (only up calls) | 4 ✓ 1 ✗ | 1 ✓ 0 ✗ | no calls |
| Model v1.0 | – | – | 4 ✓ 9 ✗ (31% vs 35%) | – |
| Solar return generated day call | 7 ✓ 4 ✗ (64% vs 52%, p 0.55) | – | – | – |
| USA Tara bala | 2 ✓ 8 ✗ (20% vs 52%, p 0.06) | – | – | – |

  - All main layers together: **120 passed, 118 failed (50%), 118 too small; chance 50%.** By market: S&P 65/65 (50% vs 50%), Sensex 25/9 (74% vs 74%), gold 18/25 (42% vs 36%), silver 12/19 (39% vs 40%). Nothing passes p < 0.05.
  - The Sensex "worked" only because the calls were bullish and the Sensex rose; the same bullish calls failed on the falling S&P and metals.
- **Where it failed:**
  - **S&P labels came from one span rule.** Venus–Rahu 6/8 (Bullish, Low) labelled every day 5–22 Nov; over the span the S&P fell 10.1% and the Sensex rose 8.6%. Moon–Rahu 6/8 (4–7 Nov): S&P −2.5%, Sensex +5.3%. The table's records count each span once; as day-by-day calls these rules were never better than chance (Venus–Rahu S&P 56.0% vs 53.8%, p 0.27; Moon–Rahu 54.8% vs 54.6%, p 0.88; 2000–2026).
  - The model made only up calls on the S&P in a falling month, and almost no calls on gold and silver.
  - **Big days:** 23 across the four markets; the model flagged 3 (Sensex 2 of 2, gold 1 of 8, S&P 0 of 5, silver 0 of 8). Volatility-factor days held 2 of the S&P's 5 and both Sensex big days. Gold's watch windows caught 3 of 4 watch days (no long-run lift).
  - **Deep-dive leans** (nominal p < 0.05 on history to 31 Oct): 9 of 30 right (30% vs 39% by chance); silver 2 of 13.
- **November deep dive** (`deep_dive_2026-11-*_ET.json`, history to 31 Oct): 2,010 tests over 5 weeks, 0 pass BH, 41 nominal (about 100 expected). Checks 20/20; 10 of 10 independent recounts match (the recount takes the history end as an argument).
- **Long records (the tuning evidence):**
  - **Clean walk-forward labels, every day 2013–2026.** S&P/Sensex: rules picked on their 2000–2013 records only (both indices beat the base, p < 0.05 on one; 11 rules, 6 of them in today's table). Gold/silver: data-picked parts re-picked on 2000–2013.

| Market | Low | Moderate or High | All labels | Combined model (clean) |
|---|---|---|---|---|
| S&P | 46.8% vs 50.1% | 55.5% vs 53.9% (p 0.39) | 52.4% vs 52.5% | 50.7% vs 49.8% (p 0.58) |
| Sensex | 45.4% vs 50.2% (p 0.06) | 53.2% vs 53.3% | 50.5% vs 52.2% | 51.3% vs 51.6% (p 0.85) |
| Gold | 47.9% vs 49.6% | 54.9% vs 51.1% (p 0.17) | 50.0% vs 50.1% | 47.1% vs 49.8% |
| Silver | 53.9% vs 51.7% | 52.6% vs 52.2% | 53.3% vs 51.9% | 52.8% vs 50.6% |

  - With the table's own rules (chosen on all of 2000–2026) the S&P labels look good (53.5% vs 50.0%, p 0.0005; Moderate or High 53.9% vs 49.8%): that is the selection, not an edge.
  - The model's "kept layers" walk-forward (S&P 56.6% vs 52.1%, p 0.02) was a selection effect: those layers were chosen by how they scored on 2013–2026 itself. Chosen on 2000–2012 only, the S&P model scores 50.1% vs 51.6%.
  - Up calls look right more often only because markets rise more often (S&P up calls 57.3% vs 57.0% up share; down calls 43.5% vs 42.7%). Gold's down calls were worse than chance (38.0% vs 46.5%, p 0.01).
  - Model v1.0 (gold, 2000–2026): 53.8% vs 53.6% (p 0.87).
  - Each of the 10 S&P/Sensex table rules as a day call (2000–2026, in sample): 1 of 20 rule-and-market tests passes BH: Three Saturdays in Shukla Paksha on the Sensex (52.6% vs 44.7%, q 0.02).
  - **Big days**, walk-forward: the model's big-day flag works only for the Sensex (7.3% big on flagged days vs 3.1%, p < 0.0001); S&P 4.7% vs 5.3%, gold 3.9% vs 6.5%, silver never flags. The volatility factors alone: S&P 6.4% vs 4.2% (2013–2026, p 0.004) and 12.0% vs 8.9% (2000–2012); Sensex 7.3% vs 2.6% and 22.8% vs 13.2%. The factors were chosen on 2000–2026, so this is not a clean out-of-sample result.
  - Solar return day calls since 1928: Bullish 53.4% right vs 52.4% up days; Bearish 47.0% vs 47.6% down days: November's 7 of 11 was luck.
  - 24 Sep – 27 Nov: nothing passes p < 0.05 (S&P Moderate or High labels 9 of 13, Low 2 of 6).
- **Changes applied (both calendars unless noted):**
  - Low labels are shown grey, as a lean, not a day call.
  - The combined model's probabilities are no longer coloured as calls.
  - The big-day chance counts only for the Sensex; for the other markets it is shown as untested (2026 calendar). Superseded the same day by the clean big-day test (entry above): untested for every market.
  - Gold and silver big-move watch windows are marked "no proven lift" (2026 calendar).
  - "Read this first" and the track record now quote the clean walk-forward figures. The 2027 calendar's 2,211 rows are byte-identical.
- **Not changed:** no rule was added, removed or reversed; the published tables are unchanged.

**Deep dive, February 2027, week by week (27 Nov 2026)** (`tools/week_deep_dive.py feb`, `deep_dive_2027-02-*_ET.json`, `calendar_2027_NY_master.html` → "Deep dive: February 2027"; the page now has a month index)

- **Setup:**
  - Holiday added: 15 Feb (Presidents' Day) for US stocks and COMEX. Past Presidents' Days have no ^GSPC/GC=F/SI=F bar.
  - The BSE has no February holiday: Maha Shivaratri 2027 falls about 6–7 Mar, and Shivaji Jayanti (19 Feb) is a trading day in the past data.
- **New event kinds:**
  - Eclipses. The calendar marks a solar eclipse at its global first contact and a lunar eclipse at its penumbral first contact (`build_2027.py`), so the classes use the same instants. The first-pass check caught this: the maximum is 2–3 h later.
  - Venus overtaking Mercury in speed (signed speeds, as in `ephem.relative_speed_crossings`). 82 times in 26 years, once per Mercury synodic cycle; my first expected range was wrong.
- **Result:** 1,827 tests over 4 weeks, **0 pass** the Benjamini–Hochberg correction. 43 are nominal (about 91 expected by chance), and no class changes the chance of a big day. Nominal examples:
  - The solar eclipse start: S&P next session 22 up / 7 down.
  - Uranus stationing direct: Sensex 14 up / 2 down.
- **Double checks:** 16 of 16 pass, 8 of 8 independent recounts match, and Presidents' Day is verified in the day data.
- **What is left for February:**

| Market | Label | Basis and record |
|---|---|---|
| S&P | Volatile on 1–5 Feb | Mercury–Saturn 2/12 big-move factor |
| S&P and Sensex | **Bearish High on 8–19 Feb** | 2026 document: "Three Saturdays in Shukla Paksha" (S&P 56% vs 39%, p 0.002; Sensex 50% vs 39%) and "Shukla Shashthi on a Friday" (S&P 53% vs 41%, p 0.02; Sensex 53% vs 42%) |
| S&P and Sensex | Bullish Moderate on 22 Feb | Moon–Rahu 6/8 |
| S&P and Sensex | Bearish Moderate from 23 Feb | Mercury with Rahu again |
| Silver | Bullish (High to Low) | – |
| Gold | Bullish Low from 12 Feb | – |

- **Model and Solar return:**
  - The combined model has the S&P at 44–51% that day vs 54% normal for most of February (lowest 16 Feb).
  - Solar return: volatile (Mars square Uranus, exact 17 Feb) on 9–23 Feb, then Bullish (month reading "Supported") from 24 Feb.
- **February's main sky events:**
  - Solar eclipse 6 Feb.
  - Uranus direct 8 Feb.
  - Mercury retrograde 9 Feb.
  - Sun with Rahu 9 Feb.
  - Sun opposite Jupiter 10 Feb.
  - Sun into Aquarius 12 Feb.
  - Mars square Uranus 17 Feb.
  - Sun opposite Mars 19 Feb.
  - Penumbral lunar eclipse 20 Feb.
  - Mercury rises 23 Feb.

**Deep dive, January 2027, week by week (27 Nov 2026)** (`tools/week_deep_dive.py jan`, `deep_dive_2027-01-*_ET.json`, shown in `calendar_2027_NY_master.html` → "Deep dive: January 2027")

- **How it was built:**
  - The January day data comes from `forward_daybyday.build`, the same layers as the December days: the rules active with their records, the published table labels, the combined model, Solar return calls and the month reading.
  - Added on top: Paap Kartari spans (B116, B117), the gold–Jupiter note, gold turn-watch markers, and the new-source items (`new_sources_leftover.calendar_layer` now takes a date range).
  - January 2027 holidays were added to `forward_daybyday.CLOSED`. US stocks and COMEX are closed on 1 Jan (New Year's Day) and 18 Jan (MLK Day); past MLK and New Year days have no GC=F/SI=F bar. The BSE is closed on 26 Jan (Republic Day); its 2027 list is not out yet.
  - The 2027 page is re-rendered from its JSON by `build_pdf_calendar.py --html-only`, using `tools/deep_dive_render.py`. Its 2,211 existing rows are byte-identical.
- **New event kinds handled:**
  - The Sun at perihelion (2 Jan).
  - Mercury rising from combustion (17 Jan, kalamsha method).
  - The "neighbour change" kind: these are the starts and ends of Mercury's Paap Kartari windows, already covered by the B116 record.
- **Result:** 2,087 tests over 5 weeks, **0 pass** the Benjamini–Hochberg correction. 44 are nominal (about 104 expected by chance), and no class changes the chance of a big day.
- **Double checks:** 20 of 20 pass, 8 of 8 independent recounts match, and the holidays are verified in the day data.
- **What is left for January:**

| Market | Label | Basis and record |
|---|---|---|
| S&P and Sensex | **Bearish all month** (High on 11–18, 22 and 26–27 Jan) | Venus opposite Uranus (S&P 58% vs 37%, p 0.03; Sensex 46% vs 38%), plus from 9 Jan Mercury with Rahu in Capricorn (S&P 47% vs 35%; Sensex 57% vs 40%, p 0.03) |
| Silver | Bullish High or Moderate | Jupiter retrograde |
| Gold | Bullish Low | U2, at chance |

- **Model, Solar return and notes:**
  - The combined model is below normal for the S&P on most January sessions (47–52% vs 54%).
  - Solar return: "no stated indication" months, so no day calls.
  - B116 Mercury Paap Kartari runs 1–15 Jan and on 25 Jan (Sensex 48% vs 41%, p 0.027).
  - Jupiter enters Cancer on 24 Jan. The gold–Jupiter pattern (Jupiter–Saturn trine, Jupiter with Ketu) returns on 25 Jan.
  - Mars stations retrograde on 10 Jan.

**Cleanup of unused files (27 Nov 2026)**

- **Removed 19 files nobody reads any more:**
  - the 13 `.ics` calendar files of the removed reports (gold, silver, S&P and Sensex big-move watch; gold BS41 model; fast triggers; outlooks);
  - the past day-report JSONs for 23–26 Nov;
  - two partial planetary-change files duplicated by `sky_changes_2026-11-01_to_2026-11-23_ET.json` and `sky_changes_2026-11-24_to_2026-12-31_ET.json`. The 2026 document check gives the same result without them.
- **Kept:** every JSON the tables, model or calendar read, the 2027 calendar's `.ics` files, and all project records (`.md`).
- **Going forward:** `.gitignore` keeps these kinds of files out, and `reports/` now holds only the two calendars, the 2027 `.ics` and the README.

**Deep dive, week by week to 31 Dec 2026 (27 Nov 2026)** (`tools/week_deep_dive.py`, `deep_dive_2026-12-*_ET.json`, calendar "Deep dive")

- **Scope:** five weeks, 1–7, 8–14, 15–21, 22–28 and 29–31 Dec. Every sky event was tested; new event kinds were added:
  - planet-planet exact aspects, which the calendar stores under a different kind;
  - stations: Saturn direct 10 Dec; Neptune direct and Jupiter retrograde 12 Dec;
  - combustion by the project's kalamsha method: Mercury, IST day 14 Dec;
  - the Moon's perigee and apogee;
  - the yoga spelt "Variyana".
- **Result:** **2,083 tests, 0 pass** the Benjamini–Hochberg correction within their week. 36 are nominal (about 104 expected by chance), and no class changes the chance of a big day. The sky events of December carry no measurable direction.
- **Double checks:** 20 of 20 pass.
  - Every event time was re-derived from the ephemeris.
  - Occurrence counts were checked against the expected frequencies. My first ranges were wrong for yogas (374 in 26 years: one every 25.4 days) and Bhadra (2,579: 8 per lunar month); the counts were right.
  - One result per week was recounted from raw prices with separate code.
  - Every sky event was confirmed as classified.
  - Five sample nominal results were recomputed independently, and all match.
- **What is left for December (labels and model):**

| Market | Label | Basis and record |
|---|---|---|
| S&P and Sensex | Bullish Moderate on 2–4 Dec and 23–29 Dec | Moon–Rahu 6/8 (61% vs 59% and 58%) |
| Silver | Bullish High from 14 Dec | Jupiter retrograde from 12 Dec, retrograde Mercury or Jupiter. Walk-forward 55% vs 52%, p 0.40 |
| Gold | Bullish Low from 2 Dec | At chance |

- **Model and Solar return:** the combined model leans up for the S&P on most December sessions (56–60% vs 54%). Solar return points to volatility (Mars square Uranus) until about 12 Dec.

**Deep dive, 1–7 Dec 2026 (27 Nov 2026)** (`tools/week_deep_dive.py`, `deep_dive_2026-12-01_to_2026-12-07_ET.json`, shown in the 2026 calendar under "Deep dive" and in each day)

- **Events tested:** every sky event of the week, 59 event classes:
  - 26 exact aspects, including the Moon's;
  - Mercury–Rahu square, Mercury–Jupiter square, Mars–Uranus square (4 Dec 14:30 ET) and Mercury–Neptune trine;
  - sign and nakshatra entries: Mercury into Scorpio (2 Dec), the Sun into Jyeshtha (2 Dec), Rahu into Capricorn and Ketu into Cancer (5 Dec), Venus into Swati (5 Dec);
  - tithis, yogas, Bhadra and the last quarter (1 Dec).
- **Method:** each class was scored on every occurrence since 2000 on the S&P, Sensex, gold and silver, over the next session and 5 sessions, two-sided, with big days, Benjamini–Hochberg across 460 tests.
- **Result:** **0 pass**. 3 are nominal (about 23 expected by chance):
  - Moon enters Anuradha: S&P next session 42% up vs 54% (p 0.001, q 0.64). It falls on Mon 7 Dec 05:18 ET.
  - Moon enters Scorpio: S&P next session 46% vs 55%.
  - Yoga Shobhana: gold next session 46% vs 54%.
  - No event class changes the chance of a big day.
- **Labels and model for the week:**
  - S&P and Sensex Bullish Moderate on 2–4 Dec, from one rule (Moon–Rahu 6/8: S&P 61% vs 59%, Sensex 61% vs 58%).
  - Gold Bullish Low from 2 Dec (Mercury with the Sun, at chance in the walk-forward test).
  - The combined model has the S&P up 56–60% that day on 1–4 Dec (normal 54%).
  - Solar return: Mars square Uranus, so volatility all week.
- **How to read it:** a mild bullish lean for stocks early in the week, with nothing in the sky events themselves that has a measurable edge.

**Gold Bearish Low on Fri 27 Nov 2026: why it was wrong (27 Nov 2026)**

- **What happened:** gold settled at 3,668.5 on 27 Nov against 3,535.8 on 25 Nov, +3.75% (there was no settlement on Thanksgiving). Silver rose +9.0%.
- **Since the label began:**

| Day | Gold move | Bearish label |
|---|---|---|
| 23 Nov | +3.9% | wrong |
| 24 Nov | −2.5% | right |
| 25 Nov | −0.7% | right |
| 27 Nov | +3.75% | wrong |
| 20 → 27 Nov | +4.4% | wrong |

- **Cause:** the "Bearish Low" label for 23 Nov – 1 Dec had a single input: a hand-added phase (Sun in Anuradha, a Saturn nakshatra, with Mars aspecting the Sun) from the 22 Nov deep analysis.
  - That rests on the user note U3 (Sun in a Saturn or Rahu nakshatra = fall), which is at chance: 60 of 134 = 45% vs 43% since 2000, right in 10 of 26 years.
  - The "Bearish Low" label itself has no edge in the walk-forward test (44% right vs 44% base), and gold rose on average after it (+0.31%).
  - It had stayed in the table despite our own notes that its rules were at chance.
- **What the other layers said:**
  - The combined model put gold at 54.2% up for 27 Nov (base 52.7%), so it already leaned the other way.
  - Model v1.0 was neutral.
  - The big-move watch (Sun opposite Uranus, exact 25 Nov; full Moon, 24 Nov) was right that big days would come: +3.9%, −2.5% and +3.75%.
- **Fix:** the phase is removed from `tools/gold_signal_table.py`. Gold now shows "No signal" for 23 Nov – 1 Dec. The combined model and the 2026 calendar were rebuilt, and the calendar checks pass.
- **Next label:** from 2 Dec, Bullish Low (Mercury with the Sun, user note U2). That label is also at chance in the walk-forward test (54% vs 55%), so treat it as weak.
- **Lesson:** a daily label with no tested edge should not be shown as a direction. The model's probability and the big-move watch carry the information.

**HTML cleanup (27 Nov 2026)**

- **What was asked:** the user asked to keep only the now-to-year-end calendar and the 2027 calendar.
- **Removed:** 140 generated HTML pages from git:
  - the reports and their `build/pdfref/` sources, including the trackers, day reports, tests and reviews;
  - `PROJECT_KNOWLEDGE.html`;
  - the `Reference_materials/extracted/` pages;
  - `build/reference_*.html`.
- **Kept:**
  - `calendar_2026-11-24_to_2026-12-31_ET.html` and `calendar_2027_NY_master.html` (in `build/pdfref/` and `reports/`);
  - `build/calendar_2027.html` (tests read it);
  - the user's own HTML sources (Kindle chapters, `data/source_2026.html`, `slv-trade-plan.html`);
  - every MD, JSON and data file.
- **Going forward:**
  - `.gitignore` keeps any other generated page out of git.
  - `publish_reports.py` publishes only the two calendars and the .ics files.
  - `refresh_all.py` no longer renders the Markdown documents to HTML.
  - Any removed page can be rebuilt by running its tool, or restored from git history.

**Leftover new-source rules and calendar layer (27 Nov 2026)** (`new_sources_leftover_ET.html`, `tools/new_sources_leftover.py`)

- **Tested:**
  - B5 (Venus phases).
  - B7 (planetary war).
  - B9 (Kosha and Sammoha meetings).
  - B10 (BS 47 combinations).
  - B11 (eclipses).
  - B13 (the Sun with benefics or malefics).
  - B6 over 1928–2026.
  - T4 and T6 (ruler of the year, using the Tajika five-dignity strength implemented from Hayanaratna 2.5).
  - T10 (substance strength at the Aries ingress).
- **Result:** none holds after correction. Nominal only:
  - Eclipse in Libra or Sagittarius: gold down 11 of 15, p 0.02, q 0.22.
  - Eclipse in the lunar month Chaitra: gold down 6 of 7 and silver 8 of 8, from 9 eclipses, too few to correct. None falls before 2028.
- **Not testable:**
  - The Sun's strength at the Aries ingress, which is constant.
  - Saturn's nakshatras (5–9 windows each).
  - Horary rules N7 and N8.
- **Calendar:** the master calendar has a "New sources" section and a per-day line with every new-source item active (13 in 24 Nov – 31 Dec), each with its test result; none feeds the signals. It also shows:
  - Lord of the year 2026–27: Mercury (US) or Jupiter (India), watch list only.
  - NYSE ruler of the year: the Moon, strength 12.4, in house 1.
  - The NYSE monthly-chart readings.

**New sources backtest (27 Nov 2026)** (`new_sources_test_ET.html`, `tools/new_sources_test.py`)

- **Scope:** the user approved the suggested order. 73 daily and monthly results and 40 annual results were scored with the §6 method and Benjamini–Hochberg correction. **None passes, so nothing is added to the rule set or the calendar.**
- **BS 42.6 with an eclipse (B12):** worse, not better. Gold rose by mid-December in 6 of 14 eclipse years vs 22 of 39 other years (1972–2025). The 2026 eclipse is not a reason to expect a gain in mid-December to mid-January.
- **At chance:**
  - The Moon passing north or south of Mercury, Jupiter or Venus (B1).
  - Mercury's reappearance as volatility (B2).
  - The Mercury and Mars nakshatra rules (B3, B4).
  - The lord of the day and of the month (B8).
  - The Tajika monthly-chart rules on the NYSE (T7–T9; best: trade saham 57% vs 53%, q 0.24).
- **Watch list (annual, not significant after correction):**
  - Lord of the year: years ruled by the Moon, Mercury, Jupiter or Venus were up 76% vs 64% on the S&P 1929–2026 (p 0.047, right in both halves). With the weekday taken at Indian sunrise it is p 0.10.
  - Ascendant of the world in the 8th or 12th from the NYSE ascendant (N5): 41% of those years were down vs 22% (p 0.01), but they still averaged +6.7%.
- **Not testable or not tested:**
  - Mars never passed south of Rohini in 2000–2026.
  - The Saturn nakshatra rules have only 2–3 windows each since 2000.
  - T4 needs the Tajika fivefold strength.

**New sources review (27 Nov 2026)** (`Reference_materials/extracted/NEW_SOURCES_REVIEW_2026-11.md`)

- **Files:** Tajika Nilakanthi (300 pages, OCR'd in Sanskrit+Hindi), Hayanaratna (1,044 pages, Gansten's English) and Brihat Samhita (Iyer 1884, 496 pages). All pages were scanned and the matching passages read. Nothing is implemented yet; the user picks the rules to move.
- **World-level rules (new):**
  - Nilakanthi, Prashna Tantra, Prakirna 36–43 (pp.298–299): the Aries-ingress chart and the lunation-chart lords give the year's tone and dear or cheap grain (N1–N3).
  - The Aries-ingress ascendant counted from the natal ascendant (N4, also in Hayanaratna p.135).
  - The "ascendant of the world" in the 8th or 12th from a chart or town is a bad year (N5, Hayanaratna p.137).
- **Tajika annual and monthly chart rules (T1–T11):**
  - The return is sidereal (supports Model B).
  - Muntha, ruler of the year, sahams (wealth, trade, business), and the 2nd and 11th houses.
  - Monthly-chart navamsha rules for wealth and business (Hayanaratna 8.4).
  - These would apply to the NYSE annual and monthly charts.
- **Brihat Samhita chapters not covered before (B1–B11):**
  - The Moon passing north or south of Mercury, Jupiter and Venus: treasuries full or suffering (Ch.18).
  - Mercury's reappearance as price disruption (7.1).
  - Mars and Saturn in stated nakshatras.
  - The lord of the year, month or day (Ch.19).
  - Planetary war (Ch.17) and planetary meetings (Ch.20).
  - Ch.47 combinations (Saturn–Rahu: commodities scarce; Mars and Saturn retrograde in Cancer, Leo or Pisces).
  - Eclipse rules (eclipse in Chaitra: gold dealers suffer).
- **Correction found (B12):** both translations make 42.6 (store gold and silver with the Sun in Leo, sell in the 5th month) conditional on portents such as an eclipse; BS4 was tested without that condition. 2026 qualifies (lunar eclipse 28 Aug, Sun in sidereal Leo), so the sell window is 16 Dec 2026 – 14 Jan 2027. This is the first suggested retest.
- **Conflicts recorded:**
  - Gold's planet: the Sun (BS 16.4) or Mercury (Hayanaratna, Nilakanthi 72).
  - Silver's planet: Venus (BS 16.27, Hayanaratna) or the Moon.
  - Grain price with the Sun in Sagittarius, Capricorn or Aquarius: Nilakanthi and BS 40.14 disagree.

**26 Nov 2026: what we said and what happened** (Thanksgiving; only the Sensex traded)

| Market | What we said | What happened |
|---|---|---|
| Sensex | No signal (model 53.2% up vs 53.3% normal); calendar row "Mrigsira on Thursday: Bearish" | +0.46% (83,938 → 84,329). Up, but FLAT by the 0.5% rule. The bearish row was wrong in sign. |
| Gold | Bearish Low | No COMEX settlement. Electronic trading was +1.66% at 07:00 ET. Not scored; the 27 Nov settlement covers both days. |
| Silver | No signal | No settlement. Electronic trading was +4.29% at 07:00 ET. Not scored. |
| S&P 500 | (closed) | — |

- **Gold Bearish Low:** wrong again on the electronic price, as on 25 Nov (+1.57%).
- **Solar return and Global Predictions:** nothing to score, because the US was closed. Fri 27 Nov (early close) is Solar return's Bullish day and the last day of the Global Predictions window.

**Day report for Thu 26 Nov 2026** (`day_report_2026-11-26_ET.html`; made the evening before, ET)

- **Markets:** Thanksgiving. The S&P, gold and silver (COMEX) are closed. Only the BSE Sensex trades (09:15–15:30 IST = 22:45 Wed – 05:00 Thu ET).
- **Signals:**
  - Gold: Bearish Low (Sun in Anuradha, Mars aspects the Sun). No session to score.
  - Sensex, S&P and silver: no signal.
- **Combined model, Sensex:**

| Measure | Model | Normal |
|---|---|---|
| Up that day | 53.2% | 53.3% |
| Up over 5 sessions | 57.9% | 56.6% |
| Big day | 9.2% | 10.4% |

  - Supported rules for the Sensex: 6 bullish, 3 bearish. No call (under 2 points from the normal rate).
- **Active rules:** 140 catalogue rules, 14 of them with a supported record.
- **Calendar rows:**
  - Sensex: "Mrigsira on Thursday: Bearish" (the Moon is in Mrigashira for the whole Sensex session). Record 37% down vs 42% normal (p 0.84): at chance, leans the wrong way.
  - S&P (closed): "Chaturthi, Krishna paksha: Bearish" (43% vs 41%, p 0.32) and "Mrigsira on Thursday: Bearish" (47% vs 42%, p 0.19). Both are at chance.
- **Changes during the day (ET):**
  - 02:45: Tritiya begins.
  - 07:17: the Moon enters Ardra. Ardra is a Rahu nakshatra, and the 2026 document's "Rahu/Ketu nakshatra on Thursday: Positive" tests at chance.
  - 13:00–23:19: Bhadra. It starts after the Sensex close.
  - 23:19: Chaturthi begins.
  - Moon aspects: Jupiter sextile 00:30, Mars sextile 06:10, Neptune square 08:40, Saturn square 18:50.
  - 17:14: yoga Sadhya → Shubha.
- **Also on the day:**
  - Jupiter in Paap Kartari continues (Ketu | Mars).
  - Mars–Jupiter–Ketu lead active.
  - Model v1.0 gold: Neutral / mixed.
- **Solar return:** no day call, because the US is closed. Jupiter–Venus is at 59.3° (0.7° from exact), so the sextile is already within 1°. It is exact on about 28 Nov at 09:00 ET. The generated call for Fri 27 Nov is Bullish (Jupiter sextile Venus), which matches Solar return's Friday recovery call. From 30 Nov the call turns Volatile (Mars square Uranus).
- **Follow-up:** the Sensex actual move is scheduled for 26 Nov at 07:00 ET.

**25 Nov 2026: what we said and what happened** (closes)

| Market | What we said | What happened |
|---|---|---|
| Gold | Bearish Low; big-move watch on the Sun–Uranus opposition | +1.57%. Bearish call wrong; not a big day |
| Silver | No signal | +2.23% |
| S&P 500 | No signal (model 56% up) | −0.25% (Nasdaq −0.62%). FLAT by the 0.5% rule |
| Sensex | No signal | +1.82% |

- **Solar return:** its day call ("down") was right in sign but within the flat band. Its week of 23–27 Nov now stands at 2 of 3.
- **Global Predictions:** 24–25 Nov were −0.50% and −0.25%. Still no big day or sharp reversal; the window ends 27 Nov.

**Day report for Wed 25 Nov 2026** (`day_report_2026-11-25_ET.html`; made the evening before, ET)

- **Signals:**
  - Gold: Bearish Low (Sun in Anuradha, Mars aspects the Sun). Gold big-move watch on the Sun–Uranus opposition (exact 17:41 ET, after the close).
  - S&P, Sensex and silver: no signal.
- **Combined model, chance of a rise that day:**

| Market | Model | Normal |
|---|---|---|
| S&P | 56% | 54% |
| Sensex | 53% | 53% |
| Gold | 53% | 53% |
| Silver | 52% | 53% |

  - Big-day chance: S&P 3%, gold 11%.
- **Active rules:** 146 catalogue rules, 21 of them with a supported record.
- **S&P calendar row:** "Kshay Tithi, Krishna paksha: Bullish". Record 62% vs 59% (p 0.25), so at chance.
- **Also on the day:**
  - Moon perigee (16:01 ET).
  - Mercury enters Vishakha.
  - Jupiter in Paap Kartari continues (Ketu | Mars).
  - Mars–Jupiter–Ketu lead active.
- **Solar return:** its day call is "down". Jupiter sextile Venus is within 2° but not yet within 1°, so the generated call follows the month reading, bearish.
- **Global Predictions:** 24–27 Nov volatility window. History for Sun opposite Uranus: 23 sharp reversals vs 17 expected (p 0.10).
- **Follow-up:** actual moves scheduled for 25 Nov after the close.

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
