# Coverage audit: gold and silver

Every page of both PDFs (TA 265 pp., KD 223 pp.), the 2026 document's gold and
silver sections, the Kindle chapters in `Reference_materials/` and the user's
gold notes were searched for gold / silver / bullion / precious; each hit was
read and checked against what `tools/build_metal_report.py` computes.

## Gold

| Source | Items | Status |
|---|---|---|
| TA p.154-156 Section 34 'When gold can rally / fall' | A1-A12, B1-B10 | all computed (A1 via 'Mars retrograde', A8/B4 via the four-star Vedha rule, B5 via 'Mercury rises in West') |
| TA p.79 S24 #8 | Retrograde Mars entering Taurus or Libra (gold & silver) | computed |
| TA pp.32-39 Sections 1-2 | Gold under Sun (western) and Mars; signs Aries, Leo, Capricorn | reference tables (not dated rules) |
| 2026 document gold section | 13 bullish + 6 bearish groups | 18 computed; 'Moonrise in Libra' not computed (its own rows are not darshan evenings). All 62 printed 2026 rows: 55 reproduced, 7 explained (see the report) |
| KD p.92 | Rahu Vedh of Pushya - gold & silver | computed |
| KD p.107 | Jupiter in Pushya + Rahu in Shatabhisha, mutual Vedh (2026) | 2026-only configuration; does not recur |
| KD p.111, p.113 | Rahu in Dhanishta - bullion negative | added in this audit round for silver; in the gold report too (1 Aug 2026 - 10 Apr 2027) |
| KD p.114 | Solar eclipse on Wednesday - gold, silver, copper | computed (none in the period) |
| KD p.137/139 | Retrograde Mars entering Taurus or Libra - gold & silver | computed |
| KD p.13, 72, 79, 189-221 | Geopolitics, price charts, gold macro essays (gold/money, DXY, ratios) | no astronomical condition |
| Kindle Ch00/04/15, Conclusion | Sun rules gold (classical, symbolic); Indian physical-gold demand calendar | rulership noted; **added in this round**: Akshaya Tritiya, Dhanteras, Diwali as context rows (the book calls them non-astrological demand) |
| User notes (20 Nov 2026) | U1-U4 Sun rules | computed, with conflicts against TA S34 shown |

## Silver

| Source | Items | Status |
|---|---|---|
| TA p.157-161 Section 35 | Silver prophecy, A1-A22, B1-B16 | all computed |
| TA p.79 S24 #8, p.127 S30 | Retrograde Mars into Taurus/Libra; Moon as Mantri | computed |
| TA p.261 | Venus retrograde in Taurus - cotton, silver, sugar bullish | added; next occurrence 2028 |
| TA pp.32-39 Sections 1-2 | Silver under Moon and Jupiter; sign Cancer | reference tables |
| 2026 document silver section | 20 bullish + 10 bearish groups | all computed; 84 printed 2026 rows: 81 reproduced, 3 explained |
| KD p.92, p.111/113, p.114, p.119, p.137 | Rahu Vedh of Pushya; Rahu in Dhanishta; solar eclipse Wednesday; Vargottam Mars in Cancer; retro Mars into Taurus/Libra | computed |
| KD p.43-80, 201-202 | Price charts; gold/silver ratio | no astronomical condition |
| Kindle Ch00/04/15 | Moon rules silver (Venus secondary); symbolic | rulership noted |

## Found while auditing

- The 2026 document's Abhijit span is 276deg40'-280deg00' (Sun, Mars, Venus tables); the engine had used 276deg40'-280deg53'20". Corrected; the Mercury table's 283deg20' end is recorded as a conflict.
- Gold-bullish #13 (Aquarius Sankranti on Friday, 13-Feb-26): the document uses the civil date; the report uses the Hindu day (sunrise to sunrise), under which it was Thursday.
- Gold-bullish #7 rows (29-Apr and 11-May-26) include periods with Mercury beside the Sun, which TA's 'not aspected by benefic' excludes.
