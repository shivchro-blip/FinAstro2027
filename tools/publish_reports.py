"""Copy the current gold / silver reports into reports/ and write reports/index.html.

    python tools/publish_reports.py

reports/ is the place to open the finished HTML (and calendar .ics) files without
rebuilding anything. tools/refresh_all.py runs this as its last step, so the
folder always holds the latest versions. Sources stay where they are built
(build/pdfref/, Reference_materials/extracted/, PROJECT_KNOWLEDGE.html).
"""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import shutil
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "reports"
B = "build/pdfref/"
X = "Reference_materials/extracted/"
SECTIONS = [
    ("Start here", [
        (B + "gold_signals_2026-11-22_to_2027-12-31_ET.html", "Gold bullish / bearish days to end-2027", "One simple table: dates, signal, strength (High / Moderate / Low), why, and each label's past record."),
        (B + "signal_table_test_2000-2026_ET.html", "Test of the table's High / Moderate / Low", "The table's scoring backtested 2000-2026: walk-forward, source rules only, in-sample."),
        (B + "silver_signals_2026-11-22_to_2027-12-31_ET.html", "Silver bullish / bearish days to end-2027", "The same simple table for silver, with each label's past record."),
        (B + "silver_signal_table_test_2000-2026_ET.html", "Test of the silver table's High / Moderate / Low", "Walk-forward, source rules only, in-sample."),
        ("PROJECT_KNOWLEDGE.html", "Project knowledge base", "Sources, user decisions, conventions, code map, every finding, rebuild commands."),
        (B + "GOLD_TRACKER.html", "Gold tracker", "Recent findings, every gold rule's 1 / 5 / 26-year record and status, best-rule dates to end-2027, analysis log."),
        (B + "SILVER_TRACKER.html", "Silver tracker", "The same for silver."),
        (B + "gold_outlook_2026-11-22_to_2027-12-31_ET.html", "Outlook to end-2027 (gold & silver)", "Everything tested in one timeline: best-rule windows, volatility watch dates, Venus dates, month by month, each with its 2000-2026 evidence."),
        (B + "gold_fast_triggers_2026-11-22_to_2027-12-31_ET.html", "Outlook narrowed with fast planets", "Moon / Mercury / Venus / Sun / Mars triggers tested inside the watch windows 2000-2026, and the best day in each forward window."),
        (B + "gold_fast_triggers_2026-11-22_to_2027-12-31_ET.ics", "Narrowed watch days (.ics)", "One entry per narrowed day."),
        (B + "silver_outlook_2026-11-22_to_2027-12-31_ET.html", "Silver outlook to end-2027", "Silver's best-rule windows, ±3.5% volatility watch, Venus dates, month by month."),
        (B + "silver_fast_triggers_2026-11-22_to_2027-12-31_ET.html", "Silver outlook narrowed with fast planets", "Fast-planet triggers tested inside silver's watch windows 2000-2026."),
        (B + "gold_outlook_2026-11-22_to_2027-12-31_ET.ics", "Outlook to end-2027 (.ics)", "The same timeline as calendar entries."),
    ]),
    ("Calendars and rule reports, 20 Nov 2026 - 31 Dec 2027 (US Eastern)", [
        (B + "gold_2026-11-20_to_2027-12-31_ET.html", "Gold report", "Every rule that names gold (TA, KD, 2026 document, your Sun notes, Brihat Samhita) with dated windows."),
        (B + "silver_2026-11-20_to_2027-12-31_ET.html", "Silver report", "Every rule that names silver."),
        (B + "calendar_2027_NY_master.html", "NY master calendar 2027", "All PDF rules plus the existing calendar, New York time with IST alongside."),
        (B + "calendar_2027_NY_master.ics", "NY master calendar 2027 (.ics)", "Import into Google / Apple / Outlook calendar."),
        (B + "gold_bs41_model_2026-11-20_to_2027-12-31_ET.html", "Gold Model v1.0 (Brihat Samhita Ch.41)", "Daily scarcity and demand/value indices with Shadbala and Ashtakavarga; backtest 2000-2026 on the same page."),
        (B + "gold_bs41_model_2026-11-20_to_2027-12-31_ET.ics", "Gold Model v1.0 (.ics)", "One calendar entry per change of bias class, with the planetary reasoning."),
        (B + "gold_big_move_watch_2026-11-22_to_2027-12-31_ET.html", "Gold big-move watch, 22 Nov 2026 - 31 Dec 2027", "Dates when the factors over-represented on gold's +/-2% days (2000-2026) recur: leads, windows, watch stretches. Watch dates, not calls."),
        (B + "gold_big_move_watch_2026-11-22_to_2027-12-31_ET.ics", "Gold big-move watch (.ics)", "One calendar entry per watch stretch."),
        (B + "gold_deep_2026-11-22_to_2026-12-31_ET.html", "Gold deep analysis, 22 Nov - 31 Dec 2026", "Every gold rule (with its 26-year record), transit and whole-sign aspect, day by day, with the written analysis and key dates."),
    ]),
    ("Backtests (COMEX closes)", [
        (B + "gold_backtest_2000-11-20_to_2026-11-20_ET.html", "Gold, 26 years (2000-2026)", "Primary evidence: per-rule scorecard, p-values, 5-year blocks, failure causes, biggest moves."),
        (B + "gold_backtest_2021-11-20_to_2026-11-20_ET.html", "Gold, 5 years (2021-2026)", ""),
        (B + "gold_backtest_2025-11-20_to_2026-11-20_ET.html", "Gold, 1 year (2025-2026)", ""),
        (B + "silver_backtest_2000-11-20_to_2026-11-20_ET.html", "Silver, 26 years (2000-2026)", "Includes the check of silver against gold's move."),
        (B + "silver_backtest_2021-11-20_to_2026-11-20_ET.html", "Silver, 5 years (2021-2026)", ""),
        (B + "silver_backtest_2025-11-20_to_2026-11-20_ET.html", "Silver, 1 year (2025-2026)", ""),
        (B + "source_rules_test_2000-2026_ET.html", "New-document rules test (2000-2026)", "Brihat Samhita 42.6 / 42.14 / 10.17, lunation half-cycles, the Silver guide's Moon conditions."),
        (B + "gold_big_moves_2000-2026_ET.html", "Gold's +/-2% days (2000-2026)", "Every big gold day with the sky +/-3 days, and which planetary factors were over-represented (same-year expected counts, FDR)."),
        (B + "silver_big_moves_2000-2026_ET.html", "Silver's +/-3.5% days (2000-2026)", "Every big silver day with the sky +/-3 days; over-represented factors and the out-of-sample check."),
        (B + "silver_big_move_watch_2026-11-22_to_2027-12-31_ET.html", "Silver big-move watch to end-2027", "Dates when silver's big-move leads recur."),
        (B + "venus_visibility_test_2000-2026_ET.html", "Venus combust / rising test (2000-2026) and the Jan 2026 crash", "TA Section 18 Venus rules on gold and silver; Venus rose in the West on 31 Jan 2026, the session after gold's -10.8% day."),
        (B + "speed_principle_test_2000-2026_ET.html", "Slow vs fast planets test (2000-2026)", "Do fast-planet events bring bigger / sudden moves, and do slow-planet rules get the trend right more often?"),
    ]),
    ("Stock market: S&P 500 and BSE Sensex, 2000-2026", [
        (B + "market_signals_2026-11-23_to_2027-12-31_ET.html", "S&P 500 and Sensex bullish / bearish days to end-2027", "Two simple tables: dates, signal, strength, why, and each rule's 26-year record on both indices."),
        (B + "model_check_60d_ET.html", "Our model over the last 60 days", "Every label of the gold, silver, S&P and Sensex tables rebuilt for each past day, against the actual moves."),
        (B + "dasha_transits_ET.html", "USA and NYSE dashas (five levels) with transits", "Maha / Antar / Pratyantar / Sookshma / Prana now, the transits of each dasha lord, Pratyantar and Sookshma timelines with S&P moves, and a 1928-2026 test of the lords."),
        (B + "author_forecasts_ET.html", "NYSE solar-return author: forecast scorecard and his rules tested", "Every forecast he made, scored against the S&P; his transit statements checked; his aspect rules tested 1928-2026."),
        (B + "nyse_usa_charts_ET.html", "NYSE and USA charts; NYSE monthly solar-return technique tested", "NYSE (1792) and USA (1776) natal charts, transits now, monthly solar-return charts (author's tropical and our sidereal) and a 98-year S&P backtest of the technique."),
        (B + "rule_tally_ET.html", "What the planets said on 20 and 23 Nov (rule tally)", "Net of active rules with a good record per day, and a walk-forward test of the tally."),
        (B + "trigger_study_2000-2026_ET.html", "Fall / rise triggers and the market event log", "The conditions of 20 and 23 Nov 2026 tested day by day 2000-2026 on five markets; Mars-Jupiter-node episodes since 1928; a running log of big days with prices and sky."),
        (B + "market_summary_2000-2026_ET.html", "Market findings (start here)", "Direction rules vs big days for both indices, the robust factors and their dates to end-2027."),
        (B + "calendar_rules_backtest_2000-2026_ET.html", "The 2027 calendar's own rules, backtested 2000-2026", "All 162 calendar rules (2026 document: catalogue B, configuration groups, sub-tables) on the S&P 500, Sensex, gold and silver; 2027 dates of those that held."),
        (B + "market_backtest_2000-2026_ET.html", "Market rules backtest, 26 years", "Every computable general-market rule (TA, KD, 2026 document) scored on the S&P 500 and the Sensex; walk-forward; best rules' dates."),
        (B + "spx_big_moves_2000-2026_ET.html", "S&P 500 +/-2% days", "Every big S&P day with the sky +/-3 days; over-represented factors; out-of-sample check."),
        (B + "sensex_big_moves_2000-2026_ET.html", "Sensex +/-2% days", "The same for the BSE Sensex."),
        (B + "spx_big_move_watch_2026-11-22_to_2027-12-31_ET.html", "S&P 500 big-move watch to end-2027", "All lead windows (broad); the robust ones are in the findings page."),
        (B + "sensex_big_move_watch_2026-11-22_to_2027-12-31_ET.html", "Sensex big-move watch to end-2027", ""),
    ]),
    ("Checks of outside models", [
        (B + "external_model_check_ET.html", "Outside crash table and 2026-2029 roadmap vs ours (23 Nov 2026)", "Planet positions, the 'core recurring signatures' tested on the S&P 500 since 1928, and their 2026-2029 windows against our tables and robust factors."),
    ]),
    ("Source research and methodology", [
        (X + "OTHERS_FINANCIAL_REVIEW.html", "Review of Reference_materials/Others (45 files)", "Financial content of every document with page references; what was implemented and what was excluded."),
        (X + "FINANCIAL_ASTROLOGY_MODEL_v1.html", "Financial Astrology Model v1.0 - methodology", "Locked method for Brihat Samhita 41.9-13 with Shadbala and Ashtakavarga."),
        (X + "TA_Tech_Astro_Analysis_2020.html", "TA - Tech Astro Analysis (2020), page by page", "Extraction of the reference PDF (page images live in Reference_materials/extracted/img)."),
        (X + "KD_Parth_Prophecies_2026.html", "KD - Parth Prophecies deck (2026), page by page", "Extraction of the reference PDF."),
    ]),
]


def main():
    DEST.mkdir(exist_ok=True)
    for f in sorted((ROOT / B).glob("sky_changes_*_ET.html"))[-2:]:          # the latest planetary-change lists (tools/sky_changes.py)
        SECTIONS[0][1].insert(1, (B + f.name, f"Planetary changes {f.name[12:22]} to {f.name[26:36]}", "Every sign, nakshatra, pada, navamsa, tithi, karana, yoga, aspect and rule start / end, ET and IST."))
    days = sorted((ROOT / B).glob("day_report_*_ET.html"))
    if days:                                       # the most recent day report (tools/day_report.py)
        SECTIONS[0][1].insert(1, (B + days[-1].name, f"Day report {days[-1].name[11:21]}", "Planet positions, every active rule with its 26-year record, our signals and what markets did."))
    now = dt.datetime.now(ZoneInfo("America/New_York"))
    log = json.load(open(ROOT / B / "analysis_log.json"))["entries"]
    blocks = []
    for title, items in SECTIONS:
        rows = []
        for src, name, desc in items:
            p = ROOT / src
            if not p.exists():
                continue
            out = DEST / p.name
            if src.startswith(X) and p.name.startswith(("TA_", "KD_")):
                href = "../" + src                        # page images are relative to Reference_materials/extracted
            else:
                shutil.copy2(p, out)
                href = p.name
            mb = p.stat().st_size / 1048576
            when = dt.datetime.fromtimestamp(p.stat().st_mtime, ZoneInfo("America/New_York"))
            rows.append(f"<tr><td><a href='{html.escape(href)}'><b>{html.escape(name)}</b></a><div class='s'>{html.escape(p.name)}</div></td>"
                        f"<td>{html.escape(desc)}</td><td class='n'>{mb:.2f} MB</td><td class='w'>{when:%d %b %Y %H:%M %Z}</td></tr>")
        blocks.append(f"<h2>{html.escape(title)}</h2><div class='wrap'><table><thead><tr><th>Report</th><th>What it is</th><th>Size</th><th>Built</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    last = log[-1] if log else {}
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FinAstro Reports</title><style>{css} a{{color:inherit}}</style></head><body>
<h1>FinAstro 2027 - gold &amp; silver reports</h1>
<p class="m">Ready-to-open copies of every current report (published {now:%d %b %Y %H:%M %Z}). Open any file directly; nothing needs to be rebuilt.
To refresh them after a rule or data change run <code>python tools/refresh_all.py --prices</code>, which rebuilds everything and re-publishes this folder.
Latest analysis: <b>{html.escape(last.get('topic', ''))}</b> ({html.escape(last.get('date', ''))}) - {html.escape(last.get('result', ''))}</p>
{''.join(blocks)}
</body></html>"""
    (DEST / "index.html").write_text(page, encoding="utf-8")
    (DEST / "README.md").write_text(
        "# reports/\n\nReady-to-open copies of the current gold and silver reports. Start with `index.html`.\n\n"
        "Published by `tools/publish_reports.py` (run automatically at the end of `tools/refresh_all.py`); "
        "do not edit these copies - the sources are rebuilt in `build/pdfref/` and `Reference_materials/extracted/`.\n", encoding="utf-8")
    print(f"published {sum(1 for _ in DEST.iterdir())} files to reports/")


if __name__ == "__main__":
    main()
