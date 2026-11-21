# Review of `Reference_materials/Others`: financial content

Reviewed 21 Nov 2026. 45 files, about 11,000 pages. Each PDF's text was extracted with pdftotext. The three image-only scans had no text layer, so they were OCR'd with tesseract; the OCR text is saved in `Reference_materials/extracted/ocr/`. Every file was scanned page by page for market and price terms, and the financial passages were then read in full.

The new gold and silver rules found here were tested on COMEX closes from 2000 to 2026 with `tools/test_source_rules.py`. Results are in `build/pdfref/source_rules_test_2000-2026_ET.html`.

## 1. Bottom line

| Question | Answer |
|---|---|
| Documents with real market or price content | **8** of the 45: Brihat Samhita, the Silver guide (3 versions), Timing Solutions for Swing Traders, Bayer, McWhirter, Williams, Weingarten (*Investing by the Stars*) |
| Classical (Vedic) gold / silver price rules | **Brihat Samhita only**: Ch.41, Ch.42 and Ch.10 sl.17 (Section 3) |
| Moon → silver rulership | **Sourced.** TA p.32 (S1: "MOON: Silver …"), Kindle Ch.4 and Ch.15 (classical Sun → gold, Moon → silver), Weingarten p.24, Williams (PDF p.227) and Timing Solutions p.170 all state it. TA p.34 also gives silver to Jupiter. |
| Moon versions of your Sun rules ("Moon in a Venus nakshatra → silver up", etc.) | **Not found in any document.** No classical text has them. The Silver guide has *different* Moon rules (paksha, dignity, Rohini, aspects, tithis), and they are a modern compilation (Section 4). |
| Not financial | BPHS (both translations and the HTM), all KP books, *The Only Way to Learn Astrology*, the Llewellyn A–Z horoscope book, The Divine Codes 1–5. These cover natal and horary astrology: the 5th house as "speculation" in a birth chart is the only money content, and none of it times markets. |
| Duplicates | `BPHS - 2 RSanthanam.pdf` appears twice (root and `BPHS/`). The Sharad Joshi *Krishnamurthy padhdhati* and *Nakshatra light* PDFs each appear twice (the "(1)" copies are identical). |
| Data-quality warning | `bayer_all_48_rules.docx`: Rules 1–24 match Bayer's 1940 text, but **Rules 25–48 do not**. The docx says they were "reconstructed from secondary sources". The 1940 PDF in the same folder contains Bayer's real Rules 25–48 (plus 1A–11A for hides and 1B–1C for cotton/lard), and they are different rules. Use the PDF, not the docx, for Rules 25–48 (Section 5). |

## 2. Every file

Pages are PDF pages. "Fin." is the amount of market content: **H** = central, **M** = a section, **L** = passing mentions, **–** = none.

| File | Pages | Text | Fin. | What it is / financial content |
|---|---|---|---|---|
| jyotish_brihat-samhita_p-s-sastri-vol-1-2_full_1946_Important_For_Financial.pdf | 1107 | text (Sanskrit OCR garbled, English clean) | **H** | Varahamihira, tr. P.S. Sastri. Ch.40 crops and prices, **Ch.41 substances by sign (gold = Mesha, Makara)**, **Ch.42 fluctuation of prices (Sun-sign storage rules; lunations)**, Ch.10 Saturn by nakshatra (gold afflicted in Uttara Bhadrapada). Section 3. |
| Silver/Moon_Silver_Complete_Book.docx | – | docx | **H** | Modern guide *The Moon and Silver*: Moon rules for silver trading. Section 4. |
| Silver/Moon_Silver_Complete_Mastery_Guide.docx | – | docx | **H** | Same guide, alternate edit. |
| Silver/moon_silver_trading_guide.docx | – | docx | **H** | Same guide, long version. Its bibliography cites BPHS, March & McEvers, and Timing Solutions. |
| Silver/slv-trade-plan.html | – | html | M | One SLV swing-trade plan (2 Feb 2026). Technical only: entry $66.50–67, stop $64.50, targets $75/82/90. No astrology. |
| pdfcoffee.com-robert-lee-amp-peter-tryde-timing-solutions-…-2012.pdf | 241 | text | **H** | Lee & Tryde, *Timing Solutions for Swing Traders* (Wiley 2012). Chs 1–8 are technical analysis. **Ch.9 (p.169–) Financial Astrology**: new-Moon buy / full-Moon sell (RBS 2010 study), Moon rules silver, Moon–Mercury heliocentric 120° turns, astro stock screens. Section 4. |
| George-Bayer-Handbook-on-Trend-Determination-…pdf | 50 | text | **H** | Bayer 1940. Rules 1–48 for wheat, 1A–11A hides/stocks, 1B–1C cotton/lard. Western, tropical, mostly heliocentric Nautical Almanac quantities. No gold or silver. Section 5. |
| bayer_all_48_rules.docx | – | docx | M | Summary of Bayer: Rules 1–24 accurate, **25–48 not Bayer's** (Section 5). |
| pdfcoffee.com_astrology-and-stock-market-forecasting-mcwhirter.pdf | 109 | **scan → OCR** | **H** | McWhirter 1937. US business cycle from the North Node's sign (Leo high, Aquarius low, Scorpio normal), plus "secondary factors" (Saturn–Uranus etc.) and lunations on the NYSE chart. Stocks, tropical. No gold or silver rules. |
| pdfcoffee.com_david-williams-financial-astrology.pdf | 242 | **scan → OCR** | **H** | Williams 1982. Business and stock cycles (Jupiter–Saturn, sunspots, Kondratieff), McWhirter method, company charts. Silver: 31 / 15.36 / 9.26 / **5.58-year** price cycles (Shirk). Gold: peaks vs sunspot peaks. Sun → gold, Moon → silver (PDF p.227). No planetary timing rule for the metals. |
| pdfcoffee.com_investing-by-the-stars.pdf | 123 | **scan → OCR** | **H** | Weingarten 1996. Financial astrology overview, lunations and eclipses as turning points, money management. Gold/silver p.24: "Traditionally the sign Leo is said to rule gold, while Cancer rules silver. But does gold go up with Jupiter in Leo …? … the gold and silver markets don't fully agree." |
| Book_1969_Liewellyn_A To Z Horoscope Maker And Delineator.pdf | 798 | text | L | Western natal textbook. Speculation / 5th house; Moon rules "public commodities". No market timing. |
| pdfcoffee.com-marion-d-march-amp-joan-mcevers-the-only.pdf | 256 | text | L | *The Only Way to Learn about Horary and Electional Astrology*. 5th house = stocks and speculation in horary questions. No market timing. |
| Brihat Parasara Hora Sastra … Girish Chand Sharma Vol 1.pdf | 657 | text | – | BPHS natal. No market content. |
| BPHS/BPHS - 1 RSanthanam.pdf, BPHS - 2 RSanthanam.pdf (×2), BPHS/BPHS.HTM | 482 / 552 / – | text | – | BPHS (Santhanam). Charity items only; no prices. |
| Jyotish_KP_True astrology_S.P. Khullar.pdf | 310 | text | L | Natal KP. Lists commodities per sign (pp.37–62), copied from Brihat Samhita Ch.41. |
| Jyotish_Astrologics of kaalchakra_Baskaran.pdf | 427 | text | L | Natal: "gain through shares" for ascendants. |
| Jyotish_Applications of cuspal interlinks part 1 / 2_Baskaran | 287 / 299 | text | L | Natal KP: 5th / 11th cusp, "speculation on stocks" for a native. |
| Jyotish_KP_Kalamsa and cuspal interlinks_S.P. Khullar | 415 | text | L | Natal KP: speculation significations. |
| Other KP books (Chatterjee, Hariharan ×2, Naik, Astro IQ, Viswanath, KP year book 2010, KP reader 5, Sharad Joshi ×5, Prabhakar ×2, Khullar *Key to learn*, Anil Chawla) | 32–404 each | text | – | KP natal and horary. No market timing. |
| The Divine Codes Issues 1–4, magazine issue 5 | 45–108 each | text | – | Vedic astrology journal (Jaipur, 2015–18). Only market line: Issue 1 p.58, an author's 2015 forecast "Hike in rare metals and gold price can be seen as well", not a rule. |

## 3. Brihat Samhita: classical price rules (P.S. Sastri 1946)

Page numbers are PDF pages of the scanned volume.

| Ref | Rule (Sastri's English) | Gold / silver use | Tested (2000–2026) |
|---|---|---|---|
| **41.2** (p.327) | Mesha "presides over cloths, sheep's wool …, wheat, resin, barley, herbs … and **gold**." | Gold's sign 1 | used below |
| **41.7** (p.329) | Makara "presides over trees, shrubs, … sugar-cane, **gold** and black metal, i.e. iron." | Gold's sign 2 | used below |
| 41.9–10 (p.329) | Jupiter in the 4/10/2/11/7/9/5 house from a sign increases its objects. Mercury does the same from 2/11/10/5/8. Venus in 6/7 destroys, elsewhere promotes. Malefics in 3/6/10/11 are beneficial, elsewhere harmful. | Transits counted from Aries and Capricorn | **Not tested.** The direction is ambiguous for prices: "increase" means abundance, while 41.11 says malefics make the articles "very costly and scarce" (price **up**). Needs your reading first. |
| 41.11–13 (p.330) | Strong malefics in houses 1, 2, 4, 5, 7, 8, 9, 12 from a sign: its articles become "very costly and scarce". Strong benefics in auspicious houses: articles "thrive, fetch good price and have great demand". A benefic aspect protects. | same | Not tested (same ambiguity) |
| 42.1–2 (p.331) | Portents on new-Moon and full-Moon days and at Sankrantis foretell a change in prices. | general | – |
| **42.6** (p.332) | "If one stores up **gold**, gems, skins, armours, weapons, pearls and **silver** when the Sun is in Simha, and sells them in the 5th month, he will get profit and sustain loss otherwise." | Buy at the Sun's Leo ingress (mid-Aug), sell in the 5th solar month (Sun in Sagittarius, mid-Dec to mid-Jan) | **No edge.** Gold up in 14 of 25 years by mid-Dec, but 66% of all same-length holds rose (p = 0.90). Silver 14 of 25 (p = 0.55). Sold mid-Jan: gold 18/25, silver 17/25, about in line with drift. |
| 42.11 (p.333) | Sun in Makara or Kumbha: store metallic vessels and grains, sell after a month. | Not bullion | – |
| **42.14** (p.334) | "The Moon in conjunction with the Sun (New Moon) or in full disc and associated with and aspected by benefics promotes invariably the price of articles belonging to that particular Rasi occupied by her. Similarly, the Sun, conjoined with and aspected by malefics, destroys the price of the articles of that Rasi." | (a) New/full Moon in Aries or Capricorn with a benefic → gold up. (b) Sun in Aries or Capricorn with or aspected by a malefic → gold down. | (a) **Weak positive.** 84 such lunations: gold +0.89% to the next lunation, 50 of 84 up (60%). The 24 without a benefic: +0.03%. All half-cycles average about +0.46%. Not significant on its own. (b) **No.** 38 windows: down in 20 (53% vs 44% of all same-length windows) but average +0.80%. |
| **10.17** (p.144) | Saturn in Satabhishak and Purvabhadra: physicians, poets, traders … suffer; "so do those living on the banks of rivers, cart-wrights, women and **gold** when he is in Uttarabhadra." | Saturn in Uttara Bhadrapada → gold afflicted | Only one passage since 2000 (it recurs every ~29.5 years), split into 3 windows by retrogression: **28 Apr – 3 Oct 2025 gold +17%**, 20 Jan – 17 May 2026 −0.7%, **9 Oct 2026 – now −15%** (window ends **8 Feb 2027**). Falls in 2 of 3 windows; too few to judge. |
| 10.16 (p.143) | Saturn in Dhanishta: "prosperity on those that are engaged in usury". | finance (lenders) | – |
| 10.6 (p.141) | Saturn in Pushya: traders, gamblers suffer. | general market | – |
| 5 / 9 (p.82, p.134) | Mercury aspecting an eclipsed Sun or Moon: ghee, honey, oil "dear and rare". Venus in Visakha: "dread among the traders". | other commodities | – |
| 17 (p.211) | When Saturn is defeated by Venus in planetary war, "prices soar up". | general | – |

## 4. Moon and silver: the Silver guide and Timing Solutions

**What the Silver guide is.** The three docx files are one modern guide (no author or date). It cites the RBS 2010 "Sheer Lunacy" study and Mikula's soybean test (both from Timing Solutions p.170), BPHS, and March & McEvers. Its Vedic parts are standard Moon dignity, paksha, tithi and nakshatra lore; none of them come from a classical *market* text. Its main rules:

- Buy at the new Moon, sell at the full Moon. Shukla paksha is bullish, Krishna bearish (ch.1, ch.4; from TS p.170–171).
- Moon in Taurus (exalted) is strongest and Moon in Scorpio (debilitated) is worst (ch.2). Rohini is the "supreme nakshatra for silver", and Rohini, Hasta and Shravana (the Moon's own nakshatras) are favourable (ch.3).
- Rikta tithis (4, 9, 14) are days to avoid (ch.5).
- Jupiter conjunct or trine the Moon strengthens a signal. Saturn conjunct the Moon means wait. Mars conjunct or opposite the Moon means do not trade (ch.6).
- Void-of-course Moon, Chandrashtama, Ashtakavarga, Moon yogas, eclipse ±90-day projection, Moon–Mercury heliocentric cycle (ch.7–14).
- Personal-chart rules (Chandrashtama, natal yogas) cannot be tested against the market.

**Timing Solutions Ch.9 (Peter Tryde), pp.169–184.** It covers the new-Moon buy / full-Moon sell cycle (RBS: FTSE, DAX, HSI; Mikula: soybeans, 44 trades, 66% profitable). It states "In astrology, the Moon rules silver" and shows lunations on the SIL silver-miners ETF (Fig. 9.1). Other points: an accumulation half-cycle and a redistribution half-cycle; a stochastic filter (<20 at the new Moon, >80 at the full Moon); quarter Moons as turning points; Moon–Mercury heliocentric 120°/240°/360° as turning points (Fig. 9.3); and astro screens of stocks from their first-trade charts.

**Tested on silver, with gold as control, 2000–2026, about 6,500 trading days.** Days are scored by the Moon's state during the COMEX session.

| Rule (source) | Silver | Gold | Verdict |
|---|---|---|---|
| New → full Moon hold vs full → new (TS, SG) | +0.19% vs **+0.90%** per half-cycle (324 each) | +0.24% vs **+0.68%** | **Reversed.** Full → new did better in all five 5-year blocks for both metals (gold 2010–14 only marginally) (t = −1.4 / −1.6). |
| Shukla days bullish / Krishna bearish (SG ch.4) | Shukla avg +0.010%, Krishna +0.098% | +0.019% vs +0.071% | **Reversed** (t ≈ −1.8), consistent with the row above |
| Moon in Taurus (exalted) bullish | 51.2% up vs 52.8% base | 52.1% vs 52.5% | no effect |
| Moon in Scorpio (debilitated) bearish | 49.4% down vs 47.2% | 47.6% vs 47.5% | no effect |
| Moon in Rohini bullish | 55.1% up (p = 0.24) | 56.2% (p = 0.12) | slight, not significant; right in 3 of 5 blocks |
| Moon in Rohini, Hasta or Shravana | 53.2% (p = 0.42) | 51.3% | no effect |
| Jupiter conjunct or trine Moon bullish | 52.4% (p = 0.60) | 51.4% | no effect |
| Saturn conjunct Moon bearish | 46.1% down vs 47.2% | 47.7% | no effect |
| Rikta tithi = volatile / avoid | average move 1.38% vs 1.42% | 0.78% vs 0.80% | no effect |
| Mars conjunct or opposite Moon = volatile | 1.41% vs 1.42% | 0.79% vs 0.80% | no effect |

None of the Silver guide's Moon conditions moved silver differently from other days over 26 years. The one consistent pattern ran **against** the guide: the waning half of the month was the better half for both metals. With 22 tests, about one p < 0.05 would be expected by chance, and none occurred.

## 5. Bayer (1940): what is real and what is not

- The PDF in this folder holds Bayer's full rule set: Rules 1–48 (wheat), 1A–11A (hides; some also stocks) and 1B–1C (cotton, lard). They use Raphael's geocentric ephemeris (tropical) and Nautical Almanac heliocentric latitudes, radius vectors and right ascensions. They are calibrated on wheat, 1932–1940. **None concern gold or silver.**
- `bayer_all_48_rules.docx` Rules 1–24 match the book. **Rules 25–48 in the docx are not Bayer's.** For example:

| No. | In the 1940 book | In the docx |
|---|---|---|
| 25 | "The rule of 4-3/8, 8-3/4, 17-1/2 and 35" (price units) | "Declination of Mercury" |
| 32 | "Mercury's geocentric longitude 126°30' after the Sun" | "Mercury crossing Saturn & Jupiter heliocentric" |
| 39 | "Venus, variation per day of the heliocentric logarithm of its radius vector" | "Mars critical degrees 0/5/17/25" |
| 48 | "Jupiter in right ascension, differential of 1h 21m 45s" | "Five-fold horoscope" |

  The docx's "Rule 32 … confirmed in George Wollsten (1946)" and "Rule 39 … tested against SPX" are claims the 1940 book cannot support. The book's own hides rule 3A, "Mercury conjunctions to Saturn and Jupiter of 80 years ago", is the nearest real match to the docx's Rule 32.

## 6. What this means for the project

1. **Your Moon question.** The Moon → silver *rulership* is sourced. There is no source, classical or modern, for applying your Sun rules (nakshatra lords, benefic/malefic contacts) to the Moon. The Moon rules that do exist (Silver guide, Timing Solutions) were tested above and showed no edge on silver; the lunar half-cycle ran the opposite way. A "Moon model" for silver is therefore not supported by the sources or by the data.
2. **New classical gold rules worth tracking:**
   - **Brihat Samhita 42.14(a)**: new or full Moon in Aries or Capricorn with a benefic is gold-bullish. It is a weak positive (60% of 84 up), consistent with the source but not proven.
   - **Brihat Samhita 10.17**: Saturn in Uttara Bhadrapada is gold-negative. It is active now, until 8 Feb 2027. Only one passage exists in the data, so it is anecdotal.

   Neither is in the rule catalogue yet. Both can be added as sourced rules if you want.
3. **Brihat Samhita 41.9–13** (house positions from gold's signs) needs a decision on how "costly and scarce" and "increase" map to price direction before it can be tested.
4. **Bayer, McWhirter, Williams and Weingarten** are Western and tropical. Bayer is calibrated for wheat, McWhirter and Williams for US stocks and business, and Weingarten is a general overview. They hold nothing directly usable for gold or silver in the sidereal framework, apart from the cycle observations (silver 5.58 years; gold vs sunspots) and the lunation/eclipse turning-point idea that is already covered.
