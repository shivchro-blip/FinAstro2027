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

**Model v1.0 (Ch.41 + Shadbala + Ashtakavarga), 6,572 trading days:**
- The correlation of the scarcity index with the next 5 days is −0.002.
- The model leans bullish on 67% of days by construction.
- Use it as classical context, not as a timing tool.

## 8. Open items

- Brihat Samhita 41.12 has a translation ambiguity: Sastri reads "fetch good price and have great demand", another translation reads moderate prices and easy availability. Kept visible; V is not a stand-alone signal.
- A rule for a stellium on the Sun (the January 2026 gap) has no source yet.
- 26-year backtests are done (`*_backtest_2000-11-20_to_2026-11-20_ET.*`). The astronomy layers for 2000–2024 are git-ignored and rebuilt on demand, which takes about 10 s per year.

## 9. Rebuild

    python tools/refresh_all.py --prices      # fresh prices, then every report, backtest, model, tracker and test
    python tools/refresh_all.py               # same, using the prices already in the repo

Then add an entry to `build/pdfref/analysis_log.json` for any new analysis, and re-run `python tools/gold_tracker.py` and `python tools/gold_tracker.py --metal silver`.
