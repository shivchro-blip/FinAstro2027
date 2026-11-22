# Gold findings tracker

Generated 22 Nov 2026 08:25 EST by `tools/gold_tracker.py` (`--refresh` re-runs both backtests). HTML version: `GOLD_TRACKER.html`.

## Recent findings

| Finding | Evidence | What it means | Status |
|---|---|---|---|
| Rule set as a whole | 5 yr: 308 worked / 279 failed (52%); 1 yr: 67 / 67 | No better than chance in total; use individual rules, not the count of rules. | Confirmed (5 yr) |
| Stacking rules (bullish minus bearish count) | 5 yr: next-5-day move +0.46% on bullish-majority days vs +0.06% on bearish-majority days; corr +0.049 | The net count carries almost no information; the 1-year bearish edge (-1.49%) did not repeat over 5 years. | Did not hold up |
| Rule set over 26 years (2000-2026) | 26 yr: 1598 worked / 1400 failed (53%) | No rule beat chance at p < 0.05 over 26 years. | Confirmed (26 yr) |
| Your combined Sun model (U1-U4 together) | 26 yr: 509/939 (54% vs base 53%), p = 0.242, right in 16/26 yrs | Closest thing to an edge in the 5-year data; at chance over 26 years. | At chance |
| U2 - Mercury with the Sun | 26 yr: 176/291 (60% vs base 57%), avg +0.62%, p = 0.115, right in 20/26 yrs | Consistent across years; dates below. | Consistent |
| Mars aspected by Saturn while Jupiter retrograde | 26 yr: 14/17 (82% vs base 62%), avg +2.97%, p = 0.07, right in 12/15 yrs | Consistent across years; dates below. | Strongest |
| Rise of Jupiter | 26 yr: 6/18 (33% vs base 44%), avg -0.62%, right in 6/18 yrs | Went the wrong way more often than chance would; treat as unreliable. | Did not hold up |
| Venus in Jyeshtha with or aspected by benefic | 26 yr: 5/16 (31% vs base 43%), avg -0.49%, right in 2/11 yrs | Went the wrong way more often than chance would; treat as unreliable. | Did not hold up |
| Mars in Pushya | 26 yr: 8/16 (50% vs base 61%), avg -0.84%, right in 8/16 yrs | Went the wrong way more often than chance would; treat as unreliable. | Did not hold up |
| Sun in Libra with other malefic (Saturn, Mars, Rahu) | 26 yr: 4/10 (40% vs base 58%), avg -1.26%, right in 4/10 yrs | Went the wrong way more often than chance would; treat as unreliable. | Did not hold up |
| Sun enters Aquarius on a Friday | 26 yr: 1/5 (20% vs base 56%), avg -1.56%, right in 1/5 yrs | Went the wrong way more often than chance would; treat as unreliable. | Did not hold up |
| Big falls | Bearish rules outnumbered bullish ones before only 1 of the 15 biggest 5-day falls (5 yr); Jan-2026 crash had 6 bullish, 0 bearish | Largest gap: no rule for a stellium on the Sun (Sun, Mercury, Venus, Mars in Capricorn, Venus combusting, Jupiter retrograde). | Open gap |
| New Moon -> full Moon hold (Timing Solutions / Silver guide; excluded source) | 2000-2026: new->full +0.23% per half-cycle vs full->new +0.68% (324 each) | Ran the opposite way to the claim in every 5-year block; Moon-based silver rules showed no effect. | Did not hold up |
| Brihat Samhita 42.14a: lunation in Aries/Capricorn with a benefic (implemented) | 2000-2026: 84 cases, gold up to the next lunation in 50 (60%), avg +0.89% | Weak positive, consistent with the source but not significant. | Weak positive |
| Brihat Samhita 10.17: Saturn in Uttara Bhadrapada afflicts gold (implemented) | 2000-2026: one passage, 3 windows: 2025-04-25 -> 2025-10-02 +17.3%; 2026-01-16 -> 2026-05-15 -0.7%; 2026-10-08 -> 2026-11-20 -15.4% | Current window runs to 7 Feb 2027; one passage in 26 years is anecdotal. | Too few to judge |
| Financial Astrology Model v1.0 (Brihat Samhita 41.9-13 + Shadbala + Ashtakavarga) | 6572 days 2000-2026: corr(scarcity index, next 5 days) -0.002; 'Strong bullish' days avg +0.04% vs +0.23% all days | No predictive value; structural bullish lean. Use as classical context only (gold_bs41_model_*.html). | Did not hold up |

## Best-performing rules: dates 20 Nov 2026 - 31 Dec 2027 (ET)

Best (from the 26 yr data): Mars aspected by Saturn while Jupiter retrograde, U2 - Mercury with the Sun.

| From (ET) | To (ET) | Days | Rule | Effect | Detail |
|---|---|---|---|---|---|
| Wed 02 Dec 2026 06:57 EST | Tue 15 Dec 2026 23:55 EST | 13.7 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Mon 21 Dec 2026 21:09 EST | Sat 09 Jan 2027 14:07 EST | 18.7 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Thu 14 Jan 2027 10:40 EST | Wed 27 Jan 2027 17:04 EST | 13.3 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Fri 12 Feb 2027 23:39 EST | Tue 23 Feb 2027 18:10 EST | 10.8 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Thu 11 Mar 2027 18:37 EST | Sun 14 Mar 2027 21:30 EDT | 3.1 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Mon 05 Apr 2027 06:46 EDT | Wed 14 Apr 2027 05:58 EDT | 9.0 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Wed 21 Apr 2027 22:42 EDT | Thu 06 May 2027 03:06 EDT | 14.2 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Sat 15 May 2027 02:50 EDT | Sun 23 May 2027 09:02 EDT | 8.3 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Tue 15 Jun 2027 09:26 EDT | Fri 16 Jul 2027 20:19 EDT | 31.5 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Fri 30 Jul 2027 09:01 EDT | Sat 14 Aug 2027 02:23 EDT | 14.7 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Tue 17 Aug 2027 04:44 EDT | Mon 30 Aug 2027 16:31 EDT | 13.5 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Fri 17 Sep 2027 04:40 EDT | Tue 21 Sep 2027 08:51 EDT | 4.2 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Sun 17 Oct 2027 16:39 EDT | Wed 20 Oct 2027 22:42 EDT | 3.3 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Fri 05 Nov 2027 07:41 EDT | Tue 16 Nov 2027 15:29 EST | 11.4 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Thu 25 Nov 2027 13:59 EST | Tue 14 Dec 2027 15:37 EST | 19.1 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |
| Thu 16 Dec 2027 06:09 EST | Sun 02 Jan 2028 10:25 EST | 17.2 | U2 - Mercury with the Sun | Bullish | Mercury conjunct (same sign) |

## Every gold rule: 1-year, 5-year and 26-year

| Rule | Effect | 1 yr | 5 yr | 26 yr | Avg (26 yr) | p (26 yr) | Years right (26 yr) | Status | Upcoming |
|---|---|---|---|---|---|---|---|---|---|
| Mars aspected by Saturn while Jupiter retrograde ★ | Bullish | 1/1 (100% vs 41%) | 2/2 (100% vs 50%) | 14/17 (82% vs 62%) p = 0.07; Worked | +2.97% | 0.07 | 12/15 | Strongest | 0 |
| U2 - Mercury with the Sun ★ | Bullish | 6/12 (50% vs 46%) | 36/55 (65% vs 57%) | 176/291 (60% vs 57%) p = 0.115; Mixed | +0.62% | 0.115 | 20/26 | Consistent | 16 |
| User Sun model: net rise vs fall signals | Bullish/Neutral/Bearish | 27/41 (66% vs 50%) | 105/179 (59% vs 52%) | 509/939 (54% vs 53%) p = 0.242; Mixed | +0.15% | 0.242 | 16/26 | At chance | 70 |
| U2 - waxing Moon with / aspecting the Sun | Bullish | 8/21 (38% vs 50%) | 54/103 (52% vs 56%) | 317/561 (57% vs 56%) p = 0.497; Mixed | +0.17% | 0.497 | 15/26 | At chance | 29 |
| Vedha of Punarvasu, Pushya, Chitra or Dhanishta (gold) | Mixed/Bullish/Bearish | 14/24 (58% vs 48%) | 58/98 (59% vs 55%) | 244/477 (51% vs 54%) p = 0.895; Mixed | +0.18% | 0.895 | 12/26 | At chance | 52 |
| Sun and Moon on the same degree (new moon) | Bullish | 3/10 (30% vs 50%) | 21/48 (44% vs 56%) | 142/261 (54% vs 57%) p = 0.774; Mixed | +0.12% | 0.774 | 14/26 | At chance | 14 |
| Sun in a Venus, Mercury or Jupiter nakshatra (user note) | Bullish | 3/8 (38% vs 45%) | 22/39 (56% vs 57%) | 114/205 (56% vs 56%) p = 0.592; Mixed | +0.36% | 0.592 | 13/26 | At chance | 11 |
| Sun in a Saturn or Rahu nakshatra (user note) | Bearish | 3/7 (43% vs 54%) | 9/25 (36% vs 43%) | 60/134 (45% vs 43%) p = 0.386; Mixed | -0.26% | 0.386 | 10/26 | At chance | 7 |
| U2 - Venus with / aspecting the Sun | Bullish | 5/7 (71% vs 46%) | 18/27 (67% vs 57%) | 75/134 (56% vs 56%) p = 0.566; Mixed | +0.54% | 0.566 | 14/26 | At chance | 8 |
| U4 - Saturn with / aspecting the Sun | Bearish | 3/4 (75% vs 59%) | 6/20 (30% vs 40%) | 39/105 (37% vs 43%) p = 0.894; Mixed | -1.46% | 0.894 | 5/26 | At chance | 6 |
| U2 - Jupiter with / aspecting the Sun | Bullish | 4/4 (100% vs 42%) | 15/21 (71% vs 61%) | 65/104 (62% vs 57%) p = 0.165; Mixed | +1.53% | 0.165 | 15/26 | At chance | 4 |
| Moon darshan (first sighting) on Monday or Friday | Bullish | 2/4 (50% vs 50%) | 7/16 (44% vs 57%) | 44/83 (53% vs 57%) p = 0.792; Mixed | +0.10% | 0.792 | 10/25 | At chance | 3 |
| Mercury rises in West | Bearish | 1/2 (50% vs 50%) | 4/13 (31% vs 43%) | 34/70 (49% vs 43%) p = 0.226; Mixed | -0.04% | 0.226 | 9/26 | At chance | 4 |
| New / full Moon in Aries or Capricorn with a benefic (Brihat Samhita 42.14) | Bullish | 2/4 (50% vs 50%) | 8/15 (53% vs 57%) | 38/67 (57% vs 57%) p = 0.562; Mixed | +0.56% | 0.562 | 15/26 | At chance | 2 |
| Sun on Bharani, Krittika, Punarvasu or Pushya, not aspected by benefic | Bullish | 0/2 (0% vs 50%) | 6/12 (50% vs 55%) | 30/61 (49% vs 55%) p = 0.843; Mixed | -0.09% | 0.843 | 11/25 | At chance | 4 |
| U4 - Rahu with / aspecting the Sun (incl. Sun with Ketu) | Bearish | 1/2 (50% vs 59%) | 4/11 (36% vs 40%) | 21/52 (40% vs 42%) p = 0.619; Mixed | -1.07% | 0.619 | 5/26 | At chance | 2 |
| Sun in Aries or Capricorn with or aspected by a malefic (Brihat Samhita 42.14) | Bearish | 1/2 (50% vs 55%) | 6/9 (67% vs 44%) | 20/36 (56% vs 45%) p = 0.133; Mixed | -0.76% | 0.133 | 10/24 | At chance | 1 |
| Moon darshan on Saturday (gold) | Bearish | 1/1 (100% vs 50%) | 4/7 (57% vs 43%) | 17/32 (53% vs 44%) p = 0.19; Mixed | +0.20% | 0.19 | 10/22 | At chance | 3 |
| Saturn or Mercury in Gemini | Bearish | 1/1 (100% vs 55%) | 2/3 (67% vs 48%) | 13/29 (45% vs 40%) p = 0.366; Mixed | -0.40% | 0.366 | 11/23 | At chance | 1 |
| Sun in Leo: store gold and silver, sell in the 5th month (Brihat Samhita 42.6) | Bullish | 1/2 (50% vs 36%) | 4/6 (67% vs 69%) | 18/27 (67% vs 70%) p = 0.708; Mixed | +5.91% | 0.708 | 17/26 | At chance | 2 |
| Sun on Anuradha with or aspected by benefic | Bearish | 0/2 (0% vs 50%) | 1/6 (17% vs 45%) | 10/26 (38% vs 44%) p = 0.772; Mixed | -0.66% | 0.772 | 6/19 | At chance | 3 |
| Venus in Rohini | Bullish | 0/1 (0% vs 45%) | 1/4 (25% vs 53%) | 14/26 (54% vs 56%) p = 0.664; Mixed | +0.80% | 0.664 | 11/23 | At chance | 1 |
| Sun in Libra aspected by (or with) malefics | Bullish | 0/1 (0% vs 41%) | 2/6 (33% vs 58%) | 13/23 (57% vs 59%) p = 0.679; Mixed | +0.24% | 0.679 | 7/17 | At chance | 1 |
| Venus in Punarvasu | Bearish | 1/1 (100% vs 55%) | 2/4 (50% vs 47%) | 7/19 (37% vs 45%) p = 0.828; Mixed | +0.09% | 0.828 | 7/19 | At chance | 1 |
| Mars passes from Taurus | Bullish | 0/1 (0% vs 41%) | 2/4 (50% vs 54%) | 7/14 (50% vs 60%) p = 0.846; Mixed | +0.17% | 0.846 | 6/13 | At chance | 0 |
| Rahu & Mars together in any sign | Bullish | 0/1 (0% vs 41%) | 0/3 (0% vs 54%) | 5/13 (38% vs 56%) p = 0.94; Mixed | +0.00% | 0.94 | 4/12 | At chance | 1 |
| Mars retrograde | Bullish | – | 2/2 (100% vs 71%) | 7/11 (64% vs 64%) p = 0.647; Mixed | +4.42% | 0.647 | 7/11 | At chance | 1 |
| Jupiter in Sagittarius, Capricorn or Aries alone, with benefic or aspected by benefic | Bearish | – | 1/2 (50% vs 35%) | 3/11 (27% vs 29%) p = 0.662; Mixed | -6.12% | 0.662 | 1/7 | At chance | 0 |
| Solar eclipse on a Wednesday | Bullish | – | 0/2 (0% vs 59%) | 6/9 (67% vs 59%) p = 0.453; Mixed | +0.65% | 0.453 | 6/9 | Inconclusive | 0 |
| Moon eclipse on Wednesday | Bullish | – | – | 4/8 (50% vs 52%) p = 0.685; Mixed | -0.02% | 0.685 | 4/8 | Inconclusive | 0 |
| Rise of Jupiter | Bearish | 0/1 (0% vs 50%) | 0/4 (0% vs 46%) | 6/18 (33% vs 44%) p = 0.881; Failed | -0.62% | 0.881 | 6/18 | Did not hold up | 1 |
| Venus in Jyeshtha with or aspected by benefic | Bearish | 0/1 (0% vs 55%) | 1/3 (33% vs 46%) | 5/16 (31% vs 43%) p = 0.888; Failed | -0.49% | 0.888 | 2/11 | Did not hold up | 1 |
| Mars in Pushya | Bullish | 0/1 (0% vs 41%) | 1/4 (25% vs 64%) | 8/16 (50% vs 61%) p = 0.873; Failed | -0.84% | 0.873 | 8/16 | Did not hold up | 0 |
| Sun in Libra with other malefic (Saturn, Mars, Rahu) | Bullish | – | 1/2 (50% vs 63%) | 4/10 (40% vs 58%) p = 0.926; Failed | -1.26% | 0.926 | 4/10 | Did not hold up | 0 |
| Sun enters Aquarius on a Friday | Bullish | – | – | 1/5 (20% vs 56%) p = 0.983; Failed | -1.56% | 0.983 | 1/5 | Did not hold up | 1 |
| Jupiter in Gemini | Bullish | 1/1 (100% vs 14%) | 2/2 (100% vs 56%) | 3/4 (75% vs 54%) p = 0.372; Worked | +10.69% | 0.372 | 3/4 | Too few to judge (3/4, leans right) | 0 |
| Rahu does Vedha of Pushya | Bullish | 1/1 (100% vs 14%) | 1/1 (100% vs 13%) | 3/4 (75% vs 60%) p = 0.481; Worked | +6.33% | 0.481 | 3/4 | Too few to judge (3/4, leans right) | 0 |
| Jupiter enters Scorpio | Bullish | – | – | 3/3 (100% vs 58%) p = 0.192; Worked | +2.90% | 0.192 | 3/3 | Too few to judge (3/3, leans right) | 0 |
| Saturn in Uttara Bhadrapada (Brihat Samhita 10.17) | Bearish | 2/2 (100% vs 64%) | 2/3 (67% vs 43%) | 2/3 (67% vs 43%) p = 0.397; Mixed | -0.37% | 0.397 | 1/2 | Too few to judge (2/3, leans right) | 1 |
| Retrograde Mars entering Taurus or Libra | Bullish | – | 0/1 (0% vs 47%) | 0/2 (0% vs 50%) p = 1.0; Failed | -1.77% | 1.0 | 0/2 | Too few to judge (0/2, leans wrong) | 0 |
| Jupiter enters Gemini | Bullish | 1/1 (100% vs 50%) | 2/2 (100% vs 59%) | 2/2 (100% vs 59%) p = 0.343; Worked | +0.87% | 0.343 | 2/2 | Too few to judge (2/2, leans right) | 0 |
| Saturn with Jupiter in Sagittarius | Bullish | – | – | 1/2 (50% vs 65%) p = 0.875; Mixed | +1.18% | 0.875 | 0/1 | Too few to judge (1/2, even) | 0 |
| Rahu in Cancer without any benefic | Bullish | – | – | 1/2 (50% vs 72%) p = 0.92; Mixed | +1.68% | 0.92 | 1/2 | Too few to judge (1/2, even) | 0 |
| Jupiter in Aries | Bearish | – | 0/1 (0% vs 17%) | 0/2 (0% vs 19%) p = 1.0; Failed | -9.36% | 1.0 | 0/2 | Too few to judge (0/2, leans wrong) | 0 |
| Rahu in Dhanishta (market and bullion risk) | Bearish | 1/1 (100% vs 68%) | 1/1 (100% vs 68%) | 2/2 (100% vs 58%) p = 0.34; Worked | +7.68% | 0.34 | 2/2 | Too few to judge (2/2, leans right) | 1 |
| Sun, Moon, Mars, Mercury, Jupiter & Venus together in any sign | Bearish | – | – | 0/1 (0% vs 36%) p = 1.0; Failed | -0.88% | 1.0 | 0/1 | Too few to judge (0/1, leans wrong) | 0 |
| Akshaya Tritiya (Indian gold-buying day) | Neutral | – | – | – |  |  |  | Not scored | 1 |
| Dhanteras (Indian festival gold buying) | Neutral | – | – | – |  |  |  | Not scored | 1 |
| Diwali / Lakshmi Puja (Indian festival gold buying) | Neutral | – | – | – |  |  |  | Not scored | 1 |

## Analysis log

| Date | PR | Topic | Result |
|---|---|---|---|
| 2026-11-22 | #15 | Gold ±2% days 2000-2026: which planetary factors surround them (±3 days) | No factor significant after FDR (lowest q 0.35). Leads: Sun-Uranus opposition x2.13, Venus-Saturn conjunction x1.80, Jupiter nakshatra change x1.41, Saturn combustion x1.57, Rahu with Mars x1.44. Up: Mars in Capricorn x1.86 (62.5% up, p 0.003), Mars-Pluto conjunction x3.5. Down: Pluto R station x2.2, full Moon x1.24. The bullish rules Mars in Pushya (TA) and Sun in Libra with malefics (doc26) coincided with big falls. |
| 2026-11-22 | #14 | Test: slow planets set the trend, fast planets the sudden moves | Not supported: fast-planet events brought no bigger or more sudden moves (ratios x0.95-1.10, none significant); slow-planet-only rules gold 57% vs 52% base (35 cases), silver 46% vs 52%. Opposite hint: sudden gold days within 3 days of Jupiter/Saturn/Rahu sign changes 23% vs 15% (p~0.03); Jupiter/Saturn stations calmer (9% vs 15%). |
| 2026-11-22 | #14 | Gold deep analysis, 22 Nov - 31 Dec 2026 | Three phases: 22 Nov - 2 Dec bearish lean (Sun in Anuradha, Mars on the Sun, benefic vedha, Saturn in Uttara Bhadrapada, Rahu in Dhanishta); 2-16 Dec neutral turning supportive (Mercury with the Sun, tier A; Saturn direct 10 Dec, Jupiter retrograde 13 Dec); 16-31 Dec mixed-supportive (Jupiter and Saturn both aspect the Sun, Mercury rejoins 22 Dec). Only U2-Mercury is tier A; seasonality +1.7% avg, up 16 of 26 years. |
| 2026-11-22 | #13 | reports/ folder with ready-to-open copies | reports/index.html lists 21 reports in four groups (start here, calendars and rule reports, backtests, source research). |
| 2026-11-22 | #13 | 26-year backtest, gold and silver (20 Nov 2000 - 20 Nov 2026) | Gold 1,598/1,400 (53%) vs 54% by chance; silver 1,083/1,050 (51%) vs 51%; no rule p<0.05. 5-year best rules faded (gold Sun model 54% vs 53%; silver Venus-Mars 51% vs 54%). Most consistent: gold TA S34 A9 Mars aspected by Saturn with Jupiter retrograde 14/17 (p=0.07), U2-Mercury 176/291 (20 of 26 years); silver TA S35 A1 retrograde Mercury or Jupiter 78/126 (p=0.052), A17b Moon-Mercury alone 49/80 (p=0.081). Silver 'Mars rising' significantly wrong (2/10). |
| 2026-11-21 | #13 | Project knowledge base and one-command refresh | Full refresh with fresh prices passed (7/7 tests); headline totals unchanged (gold 5 yr 308/279, silver 201/219). 20 Nov 2026 gold settlement 3,515.4. |
| 2026-11-21 | #13 | Financial Astrology Model v1.0 (Brihat Samhita Ch.41 + BPHS Shadbala + Ashtakavarga) for gold | Backtest 2000-2026 (6,572 days): correlation of the scarcity index with the next 5 days -0.002; 'Strong bullish' days averaged +0.04% over 5 days vs +0.24% for all days. Structural bullish skew (67% of days mild bullish or stronger). Forward: bearish stretches 16 Jun - 16 Jul 2027 (Mild bearish to Bearish); strongest bullish 1-8 Aug 2027, 23-30 Aug 2027, 16-27 Dec 2027. |
| 2026-11-21 | #13 | Brihat Samhita gold/silver rules implemented; Bayer and Western sources excluded | Forward dates: Saturn in Uttara Bhadrapada to 7 Feb 2027 (bearish); Sun with Rahu in Capricorn 14 Jan - 12 Feb 2027 (bearish); new Moon in Capricorn aspected by Jupiter 6 Feb 2027 and full Moon in Aries 13 Nov 2027 (bullish); store window 17 Aug 2027 - 14 Jan 2028. 5-year scores: all four 'Mixed' (too few occurrences to judge). |
| 2026-11-21 | #13 | Review of Reference_materials/Others (45 files) + test of their gold/silver rules | 8 documents have market content; only Brihat Samhita has classical gold/silver price rules. Moon->silver rulership is sourced, a Moon version of the user's Sun rules is not. Silver guide's Moon rules: no effect over 26 years; new->full Moon hold did WORSE than full->new for both metals. BS 42.14(a) weak positive for gold; BS 10.17 (Saturn in Uttara Bhadrapada, gold afflicted) active until 8 Feb 2027. bayer_all_48_rules.docx rules 25-48 do not match Bayer's 1940 text. |
| 2026-11-21 | #12 | Silver backtest, 1 and 5 years + silver tracker | 197 of 414 worked (48%) vs 50% by chance; net rule count pointed the wrong way; outcomes followed gold (failed 153/178 when gold moved against the rule). Best: Venus-Mars / Sun-Mars together (19/30, 4 of 5 years); 'Venus alone in Leo/Libra' 5/6 vs plain 'Venus in Leo/Libra' 3/11. |
| 2026-11-21 | #11 | Gold findings tracker + forward dates | See GOLD_TRACKER.html. |
| 2026-11-21 | #10 | Gold backtest, 5 years | 288 of 554 worked (52%) vs 54% by chance; best: combined Sun model 105/179 (p=0.057), U2-Jupiter, U2-Venus, U2-Mercury right in 4 of 5 years; U4-Saturn did not hold up (6/20). |
| 2026-11-20 | #9 | Gold backtest, 1 year | 61 of 124 decided occurrences worked (49%); bearish-majority days were followed by -1.49% over 5 days; the Jan-2026 crash was not flagged by any rule. |
| 2026-11-20 | #8 | Gold coverage audit | Gold coverage complete for computable rules. |
| 2026-11-20 | #7 | Silver coverage audit | Added Rahu in Dhanishta (bullion risk) and Venus retrograde in Taurus; Moon-based mirror of U1-U4 NOT implemented (no source backing). |
| 2026-11-20 | #6 | User gold notes (Sun rules U1-U4) | U1-U4 in the gold report with a Sun-state timeline; conflicts with TA S34 noted on each row. |
| 2026-11-20 | #5 | Gold & silver reports | Gold report ~205 rows, silver report 117 rows. |
| 2026-11-20 | #5 | Reference PDFs -> rules + NY calendar | ~730 rules in the catalogue; ~1,600 major events in the 2027 NY calendar; validation 51/58 against the 2026 printed rows. |
| 2026-11-19 | #1-4 | Rule layer (2026 document) | Rules print in the 2026 table layout; base layer for every later analysis. |
