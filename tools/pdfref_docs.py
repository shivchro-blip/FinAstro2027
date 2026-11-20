"""Write build/pdfref/REFERENCE_PDF_RULES.md and COMPLETION_REPORT.md.

    python tools/pdfref_docs.py      (after build_pdf_calendar.py and validate_pdfref.py)
"""
from __future__ import annotations

import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
cat = json.load(open(OUT / "rules_catalogue.json", encoding="utf-8"))
val = json.load(open(OUT / "validation.json", encoding="utf-8"))
cc = json.load(open(OUT / "existing_crosscheck.json", encoding="utf-8"))
master = json.load(open(OUT / "calendar_2027_NY_master.json", encoding="utf-8"))
moon = json.load(open(OUT / "calendar_2027_NY_moon_layer.json", encoding="utf-8"))
RULES = cat["rules"]

FILES = """## 1. The two files

**TA - "Tech Astro Analysis pages 1 to 265 all final new printout cq 10 2 2020.pdf"** (Parth Prophesies, 2020; 265 scanned pages, image-only, OCR'd at 150 dpi and every table read from the page image). Printed page = PDF page - 30 in the lesson part.
* pp.31-39: Sections 1-2 - sectors ruled by each planet and represented by each sign (silver: Moon, Jupiter, Cancer; gold: Sun (western), Mars, Aries, Leo, Capricorn).
* pp.18-30: market history 1992-2019 read astrologically (Herschel-Neptune 1992, Jupiter-Saturn 2000, 2008 crash factors, Mercury-Venus contra-directional periods, Saturn-Mars 2016/2018, Saturn-Ketu 2019) and seven "important quotes".
* pp.40-168: the lessons - Sections 3-37: Dwidwadash/Shadashtak sign tables, day & nakshatra lords, Mercury between Sun and Venus, Mercury combustion types, dignity tables, bullish/bearish nature of signs and of each planet's placement, Moon rise, Navamsh results, Venus combustion, strong bearish/bullish aspect combinations, Panchak, 113 "important observations", the full planet-pair relationship tables (Section 25), Sankranti (window, muhurta class, yearly majority), Bhadra, sectors, the yearly cabinet, Mercury Paap Kartari, the Sarvatobhadra Vedha wheel and its rules, normal planetary speeds, D9 conjunction tables, and the gold / silver / sugar / commercial-turning sections.
* pp.245-265: the 2020 forecast ("story of the year"), the technical corner (price rules), total days and Samvat rainfall.

**KD - "KD Final PPT PDF 2026.pdf"** ("Parth Prophecies - based on Argh Martand - 2026 - Tech Astro Analysis", 223 pages; image-only). pp.1-4: title and foreword. pp.5-22: 2016-2032 transit review (Herschel in Aries, Saturn-Neptune conjunction as a decade-defining reset). pp.23-35: how to use astro turning dates (method, risk control, high-probable turning events incl. hemisphere dates). pp.36-81: charts of past turning dates (Mercury retrograde, equinox "hemisphere" dates, Mercury manifestation) with index ranges 2020-2025. pp.82-128: the 2026 prophecies, each dated. pp.129-148: condensed rule slides (planetary motion, vedha & Sankranti, Sun/Moon/eclipse signals, Mars, Mercury/Venus, Saturn, Rahu/Ketu, weekday, tithi and yoga rules). pp.149-223: sector outperformance cycles, conflict checklist and 2026 month bias, technical learning, gold/macro essays.

A browsable page-by-page extraction of both files (page image, verified transcriptions, OCR text) is in `Reference_materials/extracted/`.

Both are by the same school and largely restate each other; KD often clarifies a misprint in TA (e.g. TA S24 #36, see conflicts) and supplies 2026 dates that this build used as a test of its own calculations.
"""

CONFLICTS = """## Conflicts and discrepancies (both values kept)

| # | Item | One source | Other source | Handling |
|---|---|---|---|---|
| 1 | Vedha direction doctrine | TA p.134: star planets vedha Left when direct, Right when retrograde (no Front); Sun/Moon/Rahu/Ketu all three sides | 2026 document tables: Atichari -> Left, Normal -> Front, Retrograde -> Right | 2026 doctrine used (95/95 of its printed targets fit), TA rule 1 used for Sun/Moon/Rahu/Ketu; every vedha event names the doctrine it used |
| 2 | Vedha wheel labels | TA columns "To South/Right", "To East/Left" | 2026 "Left"/"Right" equal TA's for Revati, Ashwini, Bharani, Krittika and are swapped for the other 24 | Same three targets as a set on every row; mapping recorded in vedha.py |
| 3 | 2026 Sun Nakshatra Vedh (B131) | 2026 rows Chitra..Mula: Right column shifted one row (Vishakha even vedhas itself) | TA wheel | TA value used; 7 cells listed as 2026 printing defects |
| 4 | 2026 Saturn Vedh (B136) | Atichari targets printed in the Right column | Target equals the Left (Atichari) cell | Treated as column misplacement |
| 5 | 2026 Herschel Vedh (B139) | Rohini Front = Uttara Ashadha | TA: Rohini Front = Abhijit | Both recorded (27- vs 28-nakshatra scheme) |
| 6 | Normal speed | TA p.144 (and KD p.123 uses it: Mars below normal 26 Oct 2026 - reproduced, 25 Oct) | 2026 document's speed classes: TA speeds reproduce 1/12 Mercury, 0/3 Venus, 0/2 Mars printed boundaries; TA's Venus normal speed (1d36m) exceeds Venus's maximum daily motion (~1d15m), so Venus is never Atichari under TA | TA speeds used for the PDF speed rules (fast/slow planet, Atichari Mars, Mars below normal). For Vedha sides the 2026 levels are used: they reproduce 29/30 of the 2026 document's printed gold-Vedha rows vs 25/30 with TA speeds |
| 7 | Malefic Moon | TA p.137: from Krishna Ekadashi to Shukla Panchami | 2026 document: Kshin Moon from Krishna Ashtami | Each layer keeps its own source's definition |
| 8 | Mercury Paap Kartari | TA p.128: planet ahead must be retrograde; grahas only | 2026 B116: no retrograde condition; Uranus/Pluto count as malefic | Both kept as separate rules; TA's 2011 example not reproduced |
| 9 | Moon-Mercury in D9 | TA p.147: "Temporary Bounce" | KD p.85/p.134: "Bullish" | Both quoted on the event |
| 10 | Margashirsh Krishna Panchami on Thu/Fri (sugar) | TA S36 B3: Bearish | 2026 config rule: Bullish | Both shown on the existing row |
| 11 | Venus combust in West | TA S18 and S35 A15: (extreme) Bullish | TA p.261 (2020 prophecy 1): Bearish | Both quoted |
| 12 | Venus combust in East | TA S18: Bullish | 2026 document b015a: Bearish fifteen days, then Bullish | Both on the existing row |
| 13 | Moon darshan weekdays | TA #56: Tue/Sat/Sun 15 days Bullish; TA #15: Fri/Sat Bullish | KD p.133: Thu/Fri/Sat/Sun Bullish; TA S34 B9: Saturday Bearish for gold | Weekdays marked by source |
| 14 | Mercury alone in a sign | KD p.138: Bearish | TA S35 A17: Sun-Mercury or Moon-Mercury alone Bullish (silver) | Different configurations; both listed |
| 15 | TA S24 #36 | "Mercury, Venus & Jupiter Bullish together - extreme Bearish" | KD p.138: "... retrograde together: High Bearish" | Read as retrograde (misprint in TA) |
| 16 | TA p.93 heading | Second "SUN WITH MARS" table, different results from p.88-89 | Position (between Sun-Neptune and Moon-Mercury) | Read as MOON WITH MARS |
| 17 | TA p.118 | Third row labelled "60 Muhurta" | Row text and p.119 results say 45 Muhurta | 45 used |
| 18 | TA S24 #110 vs p.261 | Venus rising in the three Uttaras, Ardra, Bharani, Rohini | p.261 adds "any Purva" | Wider list used, flagged |
| 19 | KD p.136 | Atichari Mars in Purva Bhadrapada Bearish | Mars in Purva Bhadrapada Bullish after 3-4 days | Both rules emitted |
| 20 | KD p.86 citation | "Principles of Financial Astrology Book, page 79, Point No 39" | TA's point 39 is the Sagittarius-Sankranti rule | Citation unverifiable from these files |
| 21 | KD p.83 vs p.130 | "When malefic planets TRANSIT a nakshatra" | "Malefic planets doing VEDH of any nakshatra" | Read as the vedha rule (p.130 states it fully) |
| 23 | User gold notes (U1-U4) vs TA S34 / 2026 document | User: Sun in Saturn/Rahu nakshatra -> gold falls; Saturn/Rahu with or aspecting the Sun -> crash; benefics with the Sun -> rise | TA S34 A10: Sun on Pushya (Saturn nakshatra) is a rally star and a malefic aspect makes it MORE bullish; TA S34 A3 and 2026 gold-bullish #2: Sun in Libra with/aspected by malefics bullish; TA S34 B1: benefic with Sun on Anuradha bearish | Both shown on every event; agreement where TA's stars are Venus/Jupiter nakshatras (Bharani, Punarvasu) |
| 24 | Abhijit span in the 2026 document's tables | Sun, Mars, Venus Nakshtra-Vedh tables: Shravana begins at 280deg00' | Mercury table (B133): Abhijit ends at 283deg20' | 276deg40'-280deg00' used (Abhijit always begins at 276deg40') |
| 22 | Dated claims not reproduced | see the validation table (Vargottam Mars in Cancer KD 13-18 Sep 2026 vs computed 18-24 Sep; TA 2020 Saturn-Mars 23 Mar vs computed 22 Mar 14:40 - same clock time, one day earlier; TA 2018 Mercury-middle as one window vs two; TA 2011 Paap Kartari) | | Both values printed |
"""


def status(r):
    if r["existing"]:
        ex = ", ".join(r["existing"])
        return f"annotates existing `{ex}`"
    if r["hits_2027"] is None:
        return "annotation only"
    if r["tier"] == "moon":
        return f"Moon layer ({r['hits_2027']} in 2027)"
    if r["hits_2027"] == 0:
        return "computed - does not occur in 2027"
    return f"new: {r['hits_2027']} in 2027"


def section_key(r):
    ref = r["refs"][0]
    if ref.startswith("TA p."):
        try:
            return (0, int(ref.split("p.")[1].split()[0].split("-")[0]))
        except ValueError:
            return (0, 999)
    return (1, int(ref.split("p.")[1].split()[0].split("/")[0].split("-")[0]) if "p." in ref else 999)


def rules_md():
    out = ["## 2. Complete rule list (as extracted and implemented)\n",
           "Grouped by first source page. **Status**: `new` = new calendar events; `annotates existing` = the 2026-document rule already in the calendar states the same condition, so its rows carry this text instead of a duplicate; `Moon layer` = Moon-only condition, in the separate Moon-layer files; `does not occur in 2027` = computed, no instance in the year.\n"]
    s25 = [r for r in RULES if r["id"].startswith("ta_s25_")]
    d9 = [r for r in RULES if r["id"].startswith("ta_d9_")]
    rest = sorted([r for r in RULES if not (r["id"].startswith("ta_s25_") or r["id"].startswith("ta_d9_"))], key=section_key)
    out.append("| Rule | Source | Result (verbatim) | Status |\n|---|---|---|---|")
    for r in rest:
        out.append(f"| {r['title']} | {'; '.join(r['refs'])} | {r['verdict'].replace('|', '/')} | {status(r)} |")
    out.append("\n### TA Section 25 - relationship of each pair (pp.88-115)\n")
    out.append("| Pair & relation | Result | Status |\n|---|---|---|")
    for r in s25:
        out.append(f"| {r['title']} (TA p.{r['refs'][0].split('p.')[1].split()[0]}) | {r['verdict']} | {status(r)} |")
    out.append("\n### TA pp.146-153 - Navamsh (D9) conjunction results\n")
    out.append("| Pair | Result | Status |\n|---|---|---|")
    for r in d9:
        out.append(f"| {r['title']} | {r['verdict']} | {status(r)} |")
    out.append("\n### Rules not computable (with reasons)\n\n| Source | Rule | Reason |\n|---|---|---|")
    for x in cat["not_computable"]:
        out.append(f"| {x['ref']} | {x['rule']} | {x['reason']} |")
    return "\n".join(out)


def bottom_notes():
    seen = collections.OrderedDict()
    for r in RULES:
        for q in r["quals"]:
            if ("bottom" in q.lower() or "NOTE" in q or "footer" in q.lower()) and q not in seen:
                seen[q] = r["refs"][0]
    out = ["## Bottom-of-table notes and how each was applied\n"]
    for q, ref in seen.items():
        out.append(f"* {q} -- carried on every event of the rules it governs (first: {ref}).")
    out.append("* TA p.41 (S4): 'IF BOTH PLANET DIRECT RESULT RELIABILITY VERY HIGH / IF ANY OF THEM RETRO OR COMBUST RESULT WILL BE CONTRA' -- every 2/12 and 6/8 event states the sign-pair class (S4/S5 tables) and whether both planets are direct.")
    out.append("* TA p.67 / p.68: 'RELIABILITY VERY LOW AS MOON ALONE DOES NOT DRIVE THE MARKETS' -- every Moon-only condition was moved to the separate Moon-layer files rather than the main calendar.")
    out.append("* TA pp.54-57 footer '(R) MEANS RETROGRADE' -- applied as an explicit retrograde test on each marked planet.")
    return "\n".join(out)


def validation_md():
    out = ["## Dates recalculated against the PDFs' own dated claims\n",
           f"{sum(v['agreement'] for v in val)} of {len(val)} dated claims reproduced (tolerances: minutes where the source prints a time, one day where it prints a date).\n",
           "| Result | Item | Source | Source says | Computed (IST) | Note |\n|---|---|---|---|---|---|"]
    for v in val:
        out.append(f"| {'OK' if v['agreement'] else '**DIFF**'} | {v['item']} | {v['source']} | {v['claim']} | {v['computed_IST']} | {v['note']} |")
    return "\n".join(out)


def crosscheck_md():
    out = ["## Independent recomputation of rules already in the calendar\n",
           "For every PDF rule that states an existing calendar rule's condition, this engine recomputed it and compared with the existing rows (instants: same start within 10 minutes; date-only combustion: same civil date; day rules: our Mumbai-sunrise days vs the existing Indian-venue days, our New York-sunrise days vs the existing US-venue days).\n",
           "| PDF rule | Existing rule | Agreement |\n|---|---|---|"]
    for k, v in cc.items():
        if v["method"].startswith("day"):
            a = f"Mumbai: {v['mumbai_common']}/{v['mumbai_ours']} of ours in existing ({v['mumbai_existing']} existing days); New York: {v['ny_common']}/{v['ny_ours']} (existing US days {v['ny_existing']})"
        else:
            a = f"{v['matched']}/{v['ours']} of our instants match ({v['existing_rows']} existing rows)"
        out.append(f"| {v['pdf_rule']} | {', '.join(v['existing'])} | {a} |")
    out.append("\nWhere ours is a subset of existing, the existing rule is broader (e.g. it also lists days a tithi merely touches, or several nakshatras under one rule). Where days differ by one, it is the day convention (sunrise vs sunset tithi, e.g. Pradosh is customarily the Trayodashi at sunset): the existing rows were kept and the difference is reported here, not re-emitted.")
    return "\n".join(out)


def main():
    head = "# Reference PDFs - extracted rules, validation and conflicts\n\nGenerated by `tools/pdfref_docs.py` from `finastro/pdfref/catalogue.py`, `build/pdfref/validation.json` and `build/pdfref/existing_crosscheck.json`.\n\n"
    (OUT / "REFERENCE_PDF_RULES.md").write_text(head + FILES + "\n" + rules_md() + "\n\n" + bottom_notes() + "\n\n" + CONFLICTS + "\n" + validation_md() + "\n\n" + crosscheck_md() + "\n", encoding="utf-8")

    m = master["meta"]["counts"]
    new = [e for e in master["events"] if e["source"] == "reference_pdfs"]
    fam = collections.Counter()
    for e in new:
        rid = e["rule_ids"][0]
        key = ("TA Section 25 relationships" if rid.startswith("ta_s25") else "TA D9 conjunctions" if rid.startswith("ta_d9") else
               "TA Sections 19-22 strong combinations" if rid.split("_")[1] in ("s19", "s20", "s21", "s22") else
               "Section 14 placement" if rid.startswith("ta_s14") else "Bhadra (S28)" if rid.startswith("ta_s28") else
               "Vedha (S32, gold/sugar/silver vedha)" if "vedha" in rid or rid.startswith("ta_s32") else
               "Gold / silver / sugar (S34-36)" if rid.split("_")[1][:3] in ("s34", "s35", "s36") else
               "KD rules" if rid.startswith("kd_") else "Other TA sections")
        fam[key] += 1
    exist_rules = sorted({e for r in RULES for e in r["existing"]})
    gold = sum(1 for e in new if "gold" in e["markets"])
    silver = sum(1 for e in new if "silver" in e["markets"])
    rep = f"""# Completion report - reference PDFs into the 2027 New York calendar

Generated by `tools/pdfref_docs.py`. Full detail: `build/pdfref/REFERENCE_PDF_RULES.md`.

## 1. Summary of both files
See section 1 of REFERENCE_PDF_RULES.md. TA (2020 book, 265 pp.) is the rule book; KD (2026 deck, 223 pages) restates its rules and applies them to dated 2026 events. Every page of both was OCR'd and every table and garbled slide was read from the page image (transcriptions kept in the build notes).

## 2. Complete list of extracted rules
{len(RULES)} catalogue entries in `finastro/pdfref/catalogue.py` (TA Sections 3-37 incl. the 294 Section-25 pair/relation cells and 61 D9 conjunction cells; KD pp.23-148), each with page reference, verbatim result, qualifications and calculation method; {len(cat['not_computable'])} further items recorded as not computable. Listed in REFERENCE_PDF_RULES.md section 2.

## 3. New events added
{m['new_events_major_yearly']} new events in `calendar_2027_NY_master.*` (New York time, IST alongside) and {m['new_events_moon_layer']} Moon-only events in `calendar_2027_NY_moon_layer.*` (separated because TA rates Moon-alone conditions as very low reliability). Of the new events, {gold} name gold and {silver} name silver as their market. By family:
""" + "\n".join(f"* {k}: {v}" for k, v in fam.most_common()) + f"""

## 4. Existing events updated
{m['existing_rows_carried']} existing calendar rows (`build/calendar_2027.json`, deduplicated across instruments) are carried into the master calendar unchanged; {m['existing_rows_with_pdf_text']} of them now carry the PDF's interpretation, page references and qualifications because a PDF rule states the same condition ({len(exist_rules)} existing rules: {', '.join(exist_rules)}). No existing row was deleted or altered in `build/calendar_2027.*`.

## 5. Dates recalculated or corrected
* {sum(v['agreement'] for v in val)}/{len(val)} dated claims in the PDFs reproduced by independent computation (table in REFERENCE_PDF_RULES.md): e.g. all 13 KD p.94 Shani-Chandra windows within 1.4 min; Saturn-Mars exact conjunction 20 Apr 2026 04:14 IST (KD 04:13); Mars into Ardra 22:34 (KD 22:35); every TA/KD Mercury-in-the-middle period; KD's Mercury-manifestation dates; KD's Mars-below-normal-speed date (confirming KD uses TA p.144's normal speed).
* Not reproduced (both values kept): KD Vargottam Mars in Cancer 13-18 Sep 2026 (computed 18-24 Sep: Mars enters Cancer on 18 Sep); TA Saturn-Mars in Capricorn from 23 Mar 2020 14:42 (computed 22 Mar 14:40 - same time, one day earlier); TA 2018 Mercury-middle as one window (computes as two); TA's 2011 Paap Kartari window; TA p.144 normal speeds do not reproduce the 2026 document's speed-class boundaries.
* 2026 document defects found via the TA Vedha wheel: a one-row shift in the Sun Nakshatra Vedh table's Right column (7 cells), two Saturn targets in the wrong column, one Herschel Front cell.
* Existing-calendar rules recomputed independently: see the cross-check table (instants match exactly for Shani-Chandra 14/14, Moon-Rahu 14/14, Moon-Mars 14/14, Venus-Mars nakshatra 5/5, combust/rise dates all, etc.).

## 6. Bottom-of-table explanations and how they were applied
See REFERENCE_PDF_RULES.md "Bottom-of-table notes". Each note is carried verbatim in the Conditions & qualifications field of every event it governs; the S4 direct/retro note is evaluated (both-direct check printed on every 2/12 and 6/8 event); the Moon-reliability note moved Moon-only rules to their own layer.

## 7. Conflicts or discrepancies found
22 items, tabulated in REFERENCE_PDF_RULES.md (Vedha direction doctrine; wheel labelling; normal speeds vs 2026 classes; malefic-Moon definitions; Paap Kartari definitions; Moon-Mercury D9; Margashirsh Krishna Panchami; Venus combust West/East; Moon darshan weekdays; TA misprints p.93, p.118, #36; unverifiable KD citation; dated claims not reproduced).

## 8. Rules that could not be computed
{len(cat['not_computable'])} items with reasons (price/RSI rules, behavioural maxims, reference tables, undefined conditions such as "all five Panchak bullish", ambiguous TA #93, the partly illegible Vedha-on-signs list, and KD's generic every-vedha sector rule which is continuous rather than dated). Interpretive choices that WERE made are flagged on the events: Moon darshan criterion (first New York sunset with elongation >= 12 deg and age >= 20 h); Mercury combustion type from its length; "Purnima less than 5 ghadi" read as Purnima remaining after sunrise; panchang read at New York sunrise.

## 9. Confirmation
Every new event in `calendar_2027_NY_master.json/.csv/.html/.ics` and the Moon layer carries: event title; date and time in New York local time (EST/EDT) with IST alongside; planetary condition (positions at start and end, computed facts); astrological rule; source interpretation (verbatim result); financial-market significance as the source states it, with the market (general / gold XAUUSD-GC / silver SI / sugar / sector) - never a forecast; conditions and qualifications including bottom-of-table notes; source reference (file, page, section, item); calculation method. Checked by `tests/test_pdfref.py` (catalogue fields) and by construction in `tools/build_pdf_calendar.py`.

Disclaimer: financial astrology is a speculative interpretive framework; the dates are computed, the interpretations are the sources' claims, and nothing here is investment advice.
"""
    (OUT / "COMPLETION_REPORT.md").write_text(rep, encoding="utf-8")
    print("written")


if __name__ == "__main__":
    main()
