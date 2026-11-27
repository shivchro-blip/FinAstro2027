# New sources review: Tajika Neelakanthi, Hayanaratna, Brihat Samhita (Iyer 1884)

Made 27 Nov 2026. It covers the three PDFs added to `Reference_materials/Others/` on 27 Nov 2026 (PR #58). All three are Vedic, so they are in scope.

Every rule below is listed as the source states it, with a page reference. Nothing here is implemented or tested yet. The user picks which rules move into the project, and each one then gets the §6 backtest before it is used.

## 1. The three files and how they were read

| File | What it is | Pages | How it was read |
|---|---|---|---|
| `Tajikneelkanthi.pdf` | Nilakantha, *Tajika Nilakanthi*, with Hindi commentary (Chowkhamba). Three parts: Samjna Tantra (definitions), Varsha Tantra (annual charts) and Prashna Tantra (horary). | 300 | The PDF text uses a legacy Akruti font, so all 300 pages were OCR'd with Tesseract Sanskrit+Hindi (good quality). Every page was scanned for price, trade, metal, crop, ingress and world-year words, and every match was read. The Prashna Tantra special-questions and miscellaneous chapters (pp.255–300) were read in full. The house-by-house horary chapters (pp.217–255) were checked and are horary only. The OCR text is saved in `extracted/ocr/tajika_neelakanthi.txt`. |
| `9789004433717-57015.pdf` | Balabhadra, *Hayanaratna: The Jewel of Annual Astrology*, Sanskrit–English, ed. and tr. Martin Gansten (Brill 2020) | 1,044 | Clean English text. Read from the full chapter map, then every page was scanned for price, trade, gold, silver, grain, world, country and ingress words, and the matches were read in context. Sections 1.5–1.7, 4.1–4.6, 5.1–5.11, 6.3, 6.12 and 8.1–8.5 were read in full. |
| `b29353130.pdf` | Varahamihira, *Brihat Samhita*, English translation by N. Chidambaram Iyer (Madura 1884) | 496 | OCR text layer (fair). Every page was scanned for gold, silver, price, cheap, dear, merchant, trade, commodity and metal (226 sentences). The planet chapters 3–20 and chapters 40–42 and 47 were read in full. Part II (portents, gems, omens, house building) has no computable price rules. |

**How they relate:**
- Hayanaratna quotes Nilakantha's *Varsha Tantra* ("Varṣatantra") throughout. The annual-chart rules of the two Tajika books are therefore largely the same text, and are listed once (Section 4).
- The Iyer *Brihat Samhita* is the same work as the Sastri 1946 translation already in the project. It is used here to find chapters the earlier review did not cover, and to check readings.

## 2. Already in the project (not repeated)

- Brihat Samhita 42.14a/b, 10.17 and 42.6 (`bs_rules.py`, BS1–BS4). Ch.41.9–13 is Model v1.0.
- Checked in Swiss Ephemeris for B12: the 2026 eclipses are lunar 3 Mar (Sun in sidereal Aquarius), solar 12 Aug (Cancer) and lunar **28 Aug (Leo, 10.7°)**. The Sun enters sidereal Sagittarius on 16 Dec 2026 at 04:55 UT and Capricorn on 14 Jan 2027 at 15:40 UT.
- The TA/KD catalogue (734 rules) already has these events, so the new sources add only a verdict:
  - Saturn–Rahu conjunction (TA: bearish to 2°, then bullish).
  - Mercury rises east/west.
  - Venus rises east/west, plus a TA nakshatra list for Venus rising.
  - Mars in Rohini (bullish).
  - Lunar and solar eclipses by weekday, month and nakshatra.
  - KD "Shar" (each planet's own latitude).
- Weekday and Muhurta rules from TA/KD.

## 3. Rules for the world or market as a whole (directly stated)

These are the most relevant. They describe the year, prices or prosperity for everyone, not for one person.

| ID | Rule as stated | Source | Market use | Computable? |
|---|---|---|---|---|
| **N1** | The lords of the ascendant at the full-moon and new-moon moments, the lord of the Moon's sign, and the lord of the ascendant at the Sun's Aries ingress: if joined or aspected by benefics, "that year brings much happiness to the world"; if afflicted by malefics, disease and fear from the king. | Tajika Nilakanthi, Prashna Tantra, Prakirna 38 (p.298) | General year tone, from the Aries-ingress and lunation charts cast for New York and for Mumbai | Yes |
| **N2** | At the Aries ingress, the 7th lord from the ingress ascendant in an angle and in itthasala (applying aspect) with a malefic or the waning Moon, or joined or aspected by malefics: disease that year and "grain becomes dear". | Nilakanthi, Prakirna 39 (p.298) | Price-rise year (grain); general bearish tone | Yes |
| **N3** | The Aries-ingress ascendant lord, if a benefic, exalted or in its own sign or in an angle, aspected by benefics and strong: festivals, happiness, abundant crops and prosperity in the world. If a malefic and afflicted: fear from the king, hardship and all grain dear. | Nilakanthi, Prakirna 40 (p.299) | General year tone | Yes |
| **N4** | Count the house where the Aries-ingress ascendant falls from the natal ascendant. With benefics: 1st body, **2nd gain of wealth**, 3rd family growth, 4th friends and home, 5th children, 6th enemies (*Nilakanthi*: fear of enemies; Hayanaratna: defeat by enemies), 7th spouse, **8th fear of death or illness**, **9th dharma and wealth**, **10th wealth and position**, **11th every gain**, **12th sorrow and poverty**. With malefics it is reversed. | Nilakanthi, Prakirna 41–43 (p.299); the same rule in Hayanaratna 1.7, from *Prasnavaisnava* 13.73–75 (pp.135–137) | NYSE: houses counted from the NYSE natal ascendant. BSE: from its foundation chart (none in the project yet) | Yes (needs a foundation chart) |
| **N5** | "The Yavanas call the ascendant at the Aries ingress the *ascendant of the world*." If it falls in the 8th or 12th from a person's natal or annual ascendant, that year is not auspicious. If it falls in the 8th or 12th from **the sign of a town**, that town suffers damage. | Hayanaratna 1.7, quoting *Yantradhikara* (p.137) | NYSE natal or annual ascendant; also New York's or Mumbai's sign, if a source gives one | Yes (the town's sign needs a source) |
| **N6** | Sun in Aries, Taurus or Gemini with or aspected by benefics: summer grain will not be easy to get. Sun in Sagittarius, Capricorn or Aquarius with benefics: grain **cheap** (*samargha*); with malefics: **dear** (*mahargha*). | Nilakanthi, Prakirna 36 (p.298) | Grain prices only. **It conflicts with Brihat Samhita 40.13–14 (Iyer p.188):** "price moderate or will rise" with benefics, and "fluctuate or fall" with malefics. | Yes |
| N7 | Horary price question: a strong query ascendant with its own lord or benefics, and benefics in the angles, means all grain cheap. A weak ascendant with malefics in the angles means all dear. | Nilakanthi, Prakirna 37 (p.298) | Horary: needs the moment a question is asked. Using a fixed chart time instead (for example the daily open) would be our own choice, not the source's. | Only with a chosen chart time |
| N8 | Horary buy or sell: the ascendant lord is the buyer and the 11th lord is the seller. If the ascendant is stronger than the 11th, buying profits. If the 11th is strong, selling profits. | Nilakanthi, Prashna Tantra, special questions 183–185 (p.289) | Horary, as N7 | Only with a chosen chart time |
| N9 | Crop yield by direction: benefics in an angle mean good crops in that direction. Saturn with malefics means famine; the Sun means grain loss and fear from the king; Mars means grain loss and fire. | Nilakanthi 186–191 (pp.289–290) | Regional and horary; no market use | – |

## 4. Tajika annual and monthly chart rules (Hayanaratna and Nilakanthi Varsha Tantra)

These are written for a person's annual return (*varsha pravesha*) and monthly return. The Solar return method already treats the NYSE as a native, with an annual and monthly chart for its foundation chart, so these rules can be read the same way. That is still an application the Tajika sources do not make themselves, so each one is labelled.

| ID | Rule as stated | Source | Use |
|---|---|---|---|
| **T1** | The annual return is the moment the Sun regains its **sidereal** natal longitude. The monthly return is the Sun reaching the same degree in each following sidereal sign. Lunisolar and tropical years are rejected. | Hayanaratna 1.6 and 8.1–8.3 (pp.111–127, 885–923) | A source for the method choice: supports **Model B (sidereal monthly)** in `solar_return_engine.py` over Model A (tropical) |
| T2 | Calendar at the annual return: Monday, Wednesday, Thursday and Friday are excellent; Tuesday, Sunday and Saturday "bring loss and fear to the year". Nakshatras: Ashvini, Mrigashira, Hasta, Pushya, Punarvasu, Svati and Revati are auspicious. Bharani, Magha, Chitra, Vishakha, Shatabhisha, Dhanishta and Ashlesha are "much condemned". The remaining nakshatras are middling. Nanda/Bhadra/Jaya/Purna tithis are good, except tithis 1 and 12; Rikta tithis are not. | Hayanaratna 1.7, from *Trailokyaprakasha* 193–197 (p.129) | NYSE annual return (once a year) |
| T3 | Muntha: the natal ascendant advanced one sign per year. In the annual chart: 9th, 10th or 11th gives authority; 1st, 2nd, 3rd or 5th gives "wealth by enterprise"; 4th, 6th, 7th, 8th or 12th is not wanted, and the 7th, 8th and 12th bring loss of wealth. Muntha with benefics or its own lord is good, with malefics bad. Muntha in the "mouth" of Rahu (degrees Rahu has yet to cover) gives wealth; in its "tail" (7th from it) loss. | Hayanaratna 5.1–5.5 (pp.423–449); Nilakanthi Muntha chapter (pp.146–153) | NYSE annual chart |
| T4 | Ruler of the year: of five candidates (lords of the natal ascendant, the annual ascendant and the Muntha; the triplicity lord; and the lord of the Sun's sign by day or the Moon's by night), the strongest one aspecting the annual ascendant. A strong benefic ruler in an angle, trine or the 11th gives a good year; a weak one in the 6th, 8th or 12th an evil year. Combust or retrograde in both charts: "loss of wealth in every undertaking". **A strong Jupiter as ruler: great gain of wealth; Venus or Mercury the same.** | Hayanaratna 5.8–5.11 (pp.457–521, 583); Nilakanthi (pp.137–145) | NYSE annual chart |
| T5 | 2nd house (gold, silver, grains, buying and selling). Jupiter as 2nd lord in the 2nd in the annual chart, applying to the ascendant lord: gain all year; separating (isarapha) from a malefic: loss. A mutthashila (applying aspect) between the 2nd lord and the ascendant lord: easy gain. A corrupt 2nd lord and wealth-giver: loss. | Hayanaratna 6.3 (pp.581–597); Nilakanthi 2nd-house verses (pp.65, 166) | NYSE annual chart |
| T6 | 11th house (gains, buying). A strong 11th lord in itthasala with the ascendant lord or the ruler of the year: wealth. The ruler of the year in the 11th with benefics: gain from business. **Mercury as ruler of the year in the 2nd or 11th, aspected by benefics: gain from trade.** | Hayanaratna 6.12 (pp.721–729); Nilakanthi 11th house v.1–2 (p.188) | NYSE annual chart |
| T7 | Sahams (sensitive points), all used as "with benefics and their ruler: gain; with malefics: loss". Wealth saham: 2nd cusp − 2nd lord + ascendant. Trade (*vanijya*) saham: Moon − Mercury + ascendant. Business (*vyapara*) saham: Mars − Mercury + ascendant. Fortune saham: by day ascendant + Moon − Sun, at night reversed; "when Fortune is strong there is the means to wealth". | Hayanaratna 4.1–4.6 (pp.355–421); Nilakanthi saham verses 16 and 20 (pp.112, 114) | NYSE annual chart (and monthly) |
| **T8** | **Monthly chart:** the ruler of the month is chosen like the ruler of the year, from the monthly chart. Navamsha rule: if the navamsha lord of the ascendant lord is friendly (by aspect or conjunction) with the navamsha lord of the **2nd house, "riches in the house"**; inimical, fallen or combust means loss of wealth. The same with the 11th means "gain through business". The rulers of the ascendant, month and year in the 6th, 8th or 12th with malefics mean a bad month; strong in an angle, trine or the 11th mean gain. | Hayanaratna 8.4 (pp.923–935), from *Varsha Tantra* 18.3–13, Vamana and *Tajikasara* 362–363 | NYSE monthly charts: the same frame as the Solar return method, with many more samples than the annual rules |
| T9 | Planets in the houses of the monthly chart: for example, the Sun in its own, exaltation or friend's sign in the 2nd gives acquisition of wealth, elsewhere in the 2nd loss of wealth. The Sun in the 11th gives gain; in the 12th loss. The Moon in the 2nd aspected by benefics gives property. | Hayanaratna 8.5–8.6 (pp.937–949, *Jirnatajika*) | NYSE monthly charts |
| T10 | Substance rule: "there will be gain of the substance of a planet that is strong in the year and loss of the substance of a planet that is weak". Silver belongs to Venus and the Moon; **gold to Mercury**, gold with gems to Jupiter. | Hayanaratna 1.5 (pp.107–109), from *Trailokyaprakasha* 26–33 | Gold and silver strength from the annual chart. **Conflict:** Brihat Samhita 16.4 gives gold to the Sun, and Nilakanthi Samjna 69 and 72 give gold to both the Sun and Mercury (pp.72–73). |
| T11 | Annual dashas (Mudda and others) and their results. | Hayanaratna ch.7; Nilakanthi (pp.127–133, 192–201) | Personal. Dashas are parked (user, 24 Nov), so not proposed. |

## 5. Brihat Samhita (Iyer 1884): price and prosperity rules not yet in the project

PDF page numbers are those of `b29353130.pdf`.

| ID | Rule as stated | Ch. (PDF p.) | Market use | Overlap |
|---|---|---|---|---|
| **B1** | The Moon passing **north** of a planet at conjunction brings prosperity. North of Mercury: "the royal treasuries will be full". North of Jupiter: "mankind in general will be happy". North of Venus: "treasuries … will flourish". Passing **south**: the same things suffer. | 18.1–6 (pp.126–127) | General, about once a month for each planet. Computable from the latitudes of the Moon and the planet. | New (KD "Shar" uses a planet's own latitude, not the Moon relative to it) |
| **B2** | Mercury "never reappears after his conjunction with the Sun without … paralysing trade by abnormally enhancing or lowering the price". | 7.1 (p.62) | Volatility around Mercury's heliacal rising (14° from the Sun, 12° when retrograde) | The event is in the catalogue (TA Mercury rises east/west); BS adds a **volatile** verdict |
| B3 | Mercury cutting through Ashvini, Shatabhisha, Mula or Revati: "tradesmen … will suffer". Mercury's *Prakrita* course (through Svati, Bharani, Rohini, Krittika): health, rain, crops and prosperity. | 7.6, 7.9 (pp.63–64) | General | New |
| B4 | Mars passing through Shravana, Magha, Punarvasu, Hasta, Mula, Purva Bhadrapada, Ashvini, Vishakha or Rohini: "prosperity in the land". Mars passing **south of Rohini**: "prices will rise". | 6.13, 6.11 (p.62) | General. **Mars is in Magha now.** | Partly (TA: Mars in Rohini, bullish) |
| B5 | Venus reappearing (heliacal rising, 10° from the Sun) in a northern path: prosperity. In the 6th mandala (the six nakshatras from Dhanishta): "wealth and prosperity in the land". Venus in Svati: "merchants … will become wicked and lawless". | Ch.9 (pp.77–80) | General | Partly (TA lists different nakshatras for Venus rising) |
| B6 | Saturn in Pushya: tradesmen suffer. In Magha: "store houses and merchants will suffer". In Dhanishta: "treasury officers will prosper". In Shatabhisha or Purva Bhadrapada: tradesmen suffer. | 10.6, 10.7, 10.16, 10.17 (pp.84–85) | General; slow (Saturn about 1 year per nakshatra) | New. Saturn in Uttara Bhadrapada (gold) is already BS3. |
| B7 | Planetary war (two planets within a degree): the defeated planet's significations suffer. Mercury defeated by Jupiter or Saturn: "rich men … will suffer". Saturn defeated by Venus: "the price of food grains will rise". Mars defeated by Venus: store-houses suffer. Saturn defeated by Mercury: tradesmen suffer. | 17.7–25 (pp.118–121) | General. Computable if "defeat" is taken as the planet south in latitude (BS 17). | New |
| **B8** | **Lord of the year, month or day.** Jupiter: "there will be an increase of wealth". Saturn: "wealth will disappear". Mercury: towns flourish and "rulers will exchange rare and valuable gifts". Mars: fires and robbers. The lord of the year is the weekday lord of the Chaitra new moon (Iyer's note). | 19.1–22 (pp.128–131) | Year and month by weekday lord; day = weekday (Thursday vs the others; Saturday is a closed day) | Partly (TA has weekday-plus-tithi rules, not the weekday alone) |
| B9 | Planetary meetings in one sign. *Kosha* (Saturn and Jupiter plus another planet) and *Sammoha* (4–5 planets with Rahu or Ketu) are disastrous. *Samagama* (bright, undisturbed) brings prosperity. | 20.5–9 (pp.131–133) | General | New |
| B10 | Saturn and Rahu meeting: "commodity would become scarce" (prices up). Mars and Saturn retrograde in Cancer, Leo or Pisces: much suffering and grain destroyed. Saturn, Mars and Jupiter in mutual aspect: hunger and weapons. Two to four planets meeting: deaths and famine. Jupiter entering a sign while retrograde or fast: kings lose glory. Saturn turning retrograde or fast after a long direct course and entering a sign: famine. | 47 (pp.228–229) | General. **Saturn is retrograde in Pisces now**, until 11 Dec. | Saturn–Rahu is in the catalogue with a different verdict; the rest is new |
| B11 | Eclipses. In Libra: "the trading classes" suffer. In Sagittarius: "merchants … will perish". In the lunar month of **Chaitra: "dealers in gold" suffer**. In the 2nd section of the sky: merchants suffer. At midheaven: the price of food grains falls. | 5.29, 5.30, 5.40, 5.41, 5.74 (pp.46–54) | General; gold (Chaitra) | Partly (the TA eclipse rules use other months and nakshatras) |
| **B12** | **Correction to BS4 (42.6):** both translations make 42.3–12 conditional on portents seen on the new- or full-moon day or at the Sun's ingress. Sastri: "(observing the above portents)"; Iyer: "If the phenomena should occur when the Sun is in Simha …". The project implemented 42.6 without that condition. The only computable portent is an **eclipse**. | 42.1–6 (Iyer pp.190–191; Sastri pp.331–333) | Retest BS4 using only years with an eclipse while the Sun is in sidereal Leo. **2026 qualifies** (lunar eclipse of 28 Aug 2026). The "sell in the 5th month" window is then Sun in Sagittarius, about 16 Dec 2026 – 14 Jan 2027. | Refines BS4 |
| B13 | Sun in Scorpio with malefics in the 6th and 7th from it: "crops will thrive and the price of commodities will fall". Sun in Sagittarius, Capricorn or Aquarius with benefics: price "moderate or will rise"; with malefics at harvest: prices "fluctuate or fall". | 40.11, 40.14 (pp.188) | Commodity prices (crops) | Similar to 42.14b, but not limited to gold's signs |
| B14 | Planet rulerships: the Sun presides over gold (16.4). Venus over "silver mines … rich men … merchants" (16.27–29). | 16 (pp.112–115) | The first classical **Venus–silver** link in the project's sources (see T10) | Recorded only: no rule follows from it by itself |
| B15 | 41.6: Scorpio represents "metals". 41.12 (Iyer): with strong benefics "prices will be moderate and the articles … had easily". | 41 (pp.189–190) | 41.12 confirms the second reading listed under Open items. 41.6 is **not** treated as a gold or silver sign: the source says "metals" only, and silver has no sign. | Notes only |

## 6. Suggested order for moving rules into the project

1. **B12 (BS4 retest with an eclipse in the Leo month).** It corrects a rule already used. It is cheap to test, and it bears on the sell window opening 16 Dec 2026.
2. **B1 (Moon north or south of Mercury, Jupiter and Venus)** and **B2 (Mercury's reappearance as volatility).** Daily events with many samples; the full §6 backtest applies directly.
3. **B4, B6 and B8:** planet-in-nakshatra and lord-of-day/month rules (general, many samples).
4. **T8 and T9 (monthly-chart rules)** on the NYSE monthly returns: Model B frame, about 300 months since 2000, more since 1928.
5. **N1–N5, T2–T7:** annual rules. Only one sample a year (about 98 since 1928 for the S&P), so expect wide error bars.
6. Not proposed:
   - Horary rules (N7, N8, and the house-by-house questions in Nilakanthi pp.217–255): they need a chart-time choice the source does not make.
   - Crop-direction rules (N9).
   - Mudda dashas (T11): dashas are parked.
   - Colour and portent rules from Brihat Samhita Part II: not computable.

## 7. Conflicts to keep visible

- **The metal for gold:**
  - Brihat Samhita 16.4 and Nilakanthi Samjna 69 give it to the Sun.
  - Hayanaratna (*Trailokyaprakasha*) and Nilakanthi Samjna 72 give it to Mercury.
  - The project's current convention (Sun → gold, from the Kindle Ch.15 note) stays until the user decides.
- **The metal for silver:** the Moon (Kindle Ch.15), Venus and the Moon (Hayanaratna), and Venus for silver mines (Brihat Samhita 16.27).
- **Grain prices with the Sun in Sagittarius, Capricorn or Aquarius:** Nilakanthi says benefics make grain cheap and malefics dear. Brihat Samhita says benefics make it moderate or rising, and malefics make it fluctuate or fall.
- **The ascendant lord joined with the 2nd lord:**
  - *Varsha Tantra* (and Tejahsimha's applying-aspect version): good for wealth.
  - Vamana: "no happiness from wealth".
  - Hayanaratna 6.3 (p.583) records both views.
