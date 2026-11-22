# Financial Astrology Model v1.0: Classical Combined Commodity Framework

Locked 21 Nov 2026 from the methodology the user supplied in the project chat. The code is in:

- `finastro/pdfref/bs41_model.py`: the model
- `finastro/pdfref/shadbala.py`: strengths
- `tools/build_bs41_model.py`: calendar and backtest

Outputs are in `build/pdfref/gold_bs41_model_2026-11-20_to_2027-12-31_ET.{html,json,csv,ics}` and `build/pdfref/gold_bs41_model_backtest_2000-2026_ET.json`.

## 1. Sources, in priority order

| Priority | Source | Used for |
|---|---|---|
| 1 | Brihat Samhita, tr. P.S. Sastri 1946, Ch.41 (PDF pp.327–331) | Commodity signs; house rules 41.9–13 |
| 2 | BPHS, tr. R. Santhanam, Ch.27 (PDF pp.263–287) | Shadbala, all six components; required totals 27.32–33 |
| 3 | BPHS Ch.66 (standard tables) | Bhinna and Sarva Ashtakavarga |
| 4 | Parashari whole-sign aspects | 7th for all planets; Mars 4/8, Jupiter 5/9, Saturn 3/10 |
| 5 | Other techniques | Not used |

**Validation.** The Shadbala code reproduces B.V. Raman's worked example (*Graha and Bhava Balas*: 16 Oct 1918, 14:22:16 IST, 13°N 77°35′E) in `tests/test_shadbala.py`:

- Every component is within 1 virupa.
- Totals are within 1.5 virupas, with two exceptions:
  - **Mercury**: within 5. Raman uses Surya Siddhanta epoch tables for mean motion.
  - **Mars**: within 10. The book prints Mars's dig bala as 64.30, above the 60-virupa maximum.
- BPHS's own abbreviated-Ahargana example (1 June 1984 → 65295; year Thursday, month Friday) is also reproduced.

## 2. Fixed calculation settings

| Setting | Standard |
|---|---|
| Zodiac / ayanamsa | Sidereal, Lahiri |
| Chart | Geocentric; New York 40.7128 N, 74.0060 W, at Hindu sunrise of each civil date (ET) |
| House reference | Counted from the commodity's sign (whole sign) |
| Strength | Sixfold Shadbala, BPHS conventions (convention `"bphs"`) |
| Support | Sarvashtakavarga of the commodity sign (0–56; every chart totals 337) |
| Nodes | Reported (house from the sign), not scored |
| Horizon | Daily; 1–2 weeks in the backtest (1, 5 and 10 trading days) |

## 3. Commodity signs (verified against the source)

- **Gold: Mesha (Aries) and Makara (Capricorn).** BS 41.2: Mesha presides over "… barley, herbs growing on land and gold". BS 41.7: Makara over "… sugar-cane, gold and black metal, i.e. iron".
- **Silver: none.** Ch.41 assigns no sign to silver, so per safeguard 7 silver shows **Insufficient data**. Brihat Samhita 42.6 (store gold and silver when the Sun is in Simha) is already a separate rule, `bs_42_06`.

## 4. Strength: Shadbala

The required totals, from BPHS 27.32–33, are below. The ratio is total ÷ requirement.

| Planet | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn |
|---|---|---|---|---|---|---|---|
| Virupas | 390 | **360** | 300 | 420 | 390 | 330 | 300 |

**Note:** the user's methodology listed the Moon at 6.17 rupas (370 virupas). BPHS 27.32–33 (Santhanam p.286) gives 360 (6.0 rupas), and 360 is used here.

Each ratio maps to a strength class and a weight:

| Ratio | Class | Weight w |
|---|---|---|
| < 0.75 | Very weak | 0 |
| 0.75–0.89 | Weak | 0.25 |
| 0.90–0.99 | Borderline | 0.5 |
| 1.00–1.09 | Strong | 1.0 |
| 1.10–1.24 | Very strong | 1.25 |
| ≥ 1.25 | Exceptionally strong | 1.5 |

**BPHS conventions used, where Raman's example differs:**

- **Drekkana bala:** male, female and neuter planets gain it in the 1st, 2nd and 3rd decanates respectively (BPHS 27.6). Raman gives neuter the 2nd and female the 3rd.
- **Saptavargaja points:** 45 / 30 / 20 / 15 / 10 / 4 / 2 (BPHS 27.2–4). Raman uses 45 / 30 / 22.5 / 15 / 7.5 / 3.75 / 1.875.
- **Cheshta bala of the Sun and Moon:** the Sun's ayana bala and the Moon's paksha bala (BPHS 27.18). Raman lists 0 for both.

Kendradi bala counts houses by sign from the lagna, and ayana bala uses the kranti (declination) of the ecliptic degree, both as in Raman's example. Mean longitudes for cheshta bala come from the JPL approximate elements.

## 5. Planet roles

| Benefics | Malefics |
|---|---|
| Jupiter, Venus; Mercury when not in a sign with Sun, Mars or Saturn (BPHS 27.10 note) | Saturn, Mars, Sun; afflicted Mercury |
| Waxing Moon: aspects only (41.9–10 give no house list for the Moon) | Waning Moon (generic malefic rule of 41.10) |

Rahu and Ketu: listed, not scored.

## 6. House rules, counted from the commodity sign (Brihat Samhita 41.9–13)

| Planet | Effect |
|---|---|
| Malefics | Houses 1, 2, 4, 5, 7, 8, 9, 12 are harmful (41.10). When the malefic is strong, its articles become "very costly and scarce" (41.11): **+1** to the scarcity score. Houses 3, 6, 10, 11 are beneficial: **−1**. |
| Jupiter | Houses 2, 4, 5, 7, 9, 10, 11 increase the articles: **+1** to the demand score (41.9, 41.12). Other houses: 0. |
| Mercury (benefic) | Houses 2, 5, 8, 10, 11: **+1**. Other houses: 0. |
| Venus | Houses 6 and 7 destroy the articles: **−1**. Other houses promote them: **+1**. |
| Aspects on the sign (41.13) | A benefic aspect protects, a malefic aspect does the reverse. Each is weighted by the aspecting planet's strength weight. A planet *in* the sign counts as house 1, not as an aspect. |

**Translation note (41.12).** Sastri reads "thrive, fetch good price and have great demand". The user's note cites another translation reading moderate prices and easy availability. This is why demand/value is kept as a separate index and never turned into a buy signal on its own.

## 7. Indices (research conventions, not classical formulas)

Each component lies in [−1, +1]. For each gold sign:

| Component | Weight | Scarcity / price pressure S | Demand / market value V |
|---|---|---|---|
| Placement H | 45% | Σ malefic house effects ÷ 3 | Σ benefic house effects ÷ 3 |
| Strength K | 25% | Σ (effect × w) ÷ 4.5 | Σ (effect × w) ÷ 4.5 |
| Aspects A | 20% | (malefic − benefic aspect weights) ÷ 3 | the negative of S's aspect component |
| Ashtakavarga AV | 10% | −(SAV − 28) ÷ 9 | +(SAV − 28) ÷ 9 |

- Index = 100 × the weighted sum. Gold = the average of the Aries and Capricorn readings.
- Drik bala sits inside Shadbala (the planet's own strength). The aspect component measures aspects *on the commodity sign*, so nothing is counted twice.

**Price bias** comes from S:

| S | Bias |
|---|---|
| +60 and above | Strong bullish |
| +35 to +59 | Bullish |
| +15 to +34 | Mild bullish |
| −14 to +14 | Neutral / mixed |
| −15 to −34 | Mild bearish |
| −35 to −59 | Bearish |
| −60 and below | Strong bearish |

**Confidence** counts five indicators: the four S components, plus V. V counts as corroboration because 41.12 also reads as price-supportive.

| Indicators agreeing with S's sign | Confidence |
|---|---|
| 4 or more, none against | Very high |
| 3 or more | High |
| 2 | Moderate |
| Fewer | Low |
| (any count) when \|S\| < 15 | Neutral |

Every calendar entry lists the agreeing and contradicting indicators. Market confirmation (price structure, volume, VWAP, invalidation level) is shown as a checklist; it is never computed into the score.

## 8. What the 2000–2026 backtest shows (COMEX gold, 6,572 trading days)

- **No predictive value found.** The correlation of S with the next 1 / 5 / 10 days is +0.001 / −0.002 / −0.011. For V it is −0.011 / −0.016 / −0.001.
- **The bias classes do not order the returns.** Average 5-day moves:

| Bias class | Days | Avg 5-day move |
|---|---|---|
| Strong bullish | 844 | +0.04% |
| Bullish | 1,790 | +0.33% |
| Neutral | 1,620 | +0.31% |
| All days | 6,572 | +0.24% |
| Strong bearish | 13 | −1.24% |

  The 13 strong-bearish days are far too few to judge.
- **Built-in bullish lean.** 41.11 makes 8 of 12 houses harmful for malefics. Three malefics placed at random therefore give an expected placement score of +1/3, and the model reads "mild bullish" or stronger on 67% of days. Bearish readings are rare: 8% of days, and 26 of the 407 forward days.
- **Use.** As locked, the model describes the classical supply / demand condition of gold's signs. It is not a timing tool. Read it as context alongside the rule calendar and market confirmation, as the methodology itself says.

## 9. Notes on the exaltation table image (21 Nov 2026)

- **Sign names are standard and match the code's deep-exaltation points:** Sun Aries 10°, Moon Taurus 3°, Mars Capricorn 28°, Mercury Virgo 15°, Jupiter Cancer 5°, Venus Pisces 27°, Saturn Libra 20°; debilitation is exactly opposite.
- **The glyphs in the image are wrong in several rows,** for example "♊ Capricorn" for Mars and "♌ Cancer" for Jupiter.
- **Rahu and Ketu exaltation (Taurus/Gemini vs Scorpio/Sagittarius) differs between schools.** The nodes are not part of Shadbala and are not scored here.
