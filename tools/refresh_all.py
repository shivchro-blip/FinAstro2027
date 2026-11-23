"""Rebuild every gold / silver analysis in dependency order.

    python tools/refresh_all.py              # rebuild from the price files in the repo
    python tools/refresh_all.py --prices     # first download fresh GC=F / SI=F closes (tools/fetch_prices.py)

Order: prices -> rule docs and NY calendar -> gold / silver reports -> 1- and
5-year backtests (gold, silver) -> source-rule test 2000-2026 -> Model v1.0 (BS41)
-> trackers -> Markdown -> HTML renders -> tests -> copies into reports/. The 2021-2024 astronomy layers
are rebuilt on demand by backtest_gold.py. See PROJECT_KNOWLEDGE.md.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
STEPS = [
    ["tools/build_pdf_calendar.py"],
    ["tools/validate_pdfref.py"],
    ["tools/pdfref_docs.py"],
    ["tools/build_metal_report.py", "gold"],
    ["tools/build_metal_report.py", "silver"],
    ["tools/backtest_gold.py"],
    ["tools/backtest_gold.py", "--years", "5"],
    ["tools/backtest_gold.py", "--metal", "silver"],
    ["tools/backtest_gold.py", "--metal", "silver", "--years", "5"],
    ["tools/backtest_gold.py", "--years", "26"],
    ["tools/backtest_gold.py", "--metal", "silver", "--years", "26"],
    ["tools/test_source_rules.py"],
    ["tools/test_speed_principle.py"],
    ["tools/test_venus_visibility.py"],
    ["tools/big_move_analysis.py"],
    ["tools/big_move_forward.py", "2026-11-22", "2027-12-31"],
    ["tools/build_bs41_model.py"],
    ["tools/gold_deep_analysis.py", "2026-11-22", "2026-12-31"],
    ["tools/gold_tracker.py"],
    ["tools/gold_tracker.py", "--metal", "silver"],
    ["tools/gold_outlook.py", "2026-11-22", "2027-12-31"],
    ["tools/fast_trigger_analysis.py", "2026-11-22", "2027-12-31"],
    ["tools/test_signal_table.py"],
    ["tools/gold_signal_table.py", "2026-11-22", "2027-12-31"],
    ["tools/big_move_analysis.py", "--metal", "silver"],
    ["tools/big_move_forward.py", "2026-11-22", "2027-12-31", "--metal", "silver"],
    ["tools/gold_outlook.py", "2026-11-22", "2027-12-31", "--metal", "silver"],
    ["tools/fast_trigger_analysis.py", "2026-11-22", "2027-12-31", "--metal", "silver"],
    ["tools/test_signal_table.py", "--metal", "silver"],
    ["tools/gold_signal_table.py", "2026-11-22", "2027-12-31", "--metal", "silver"],
    # stock market (S&P 500, BSE Sensex): market_events.py runs first only if its cache is missing (about 30 min)
    ["tools/backtest_market.py"],
    ["tools/big_move_analysis.py", "--metal", "spx"],
    ["tools/big_move_analysis.py", "--metal", "sensex"],
    ["tools/big_move_forward.py", "2026-11-22", "2027-12-31", "--metal", "spx"],
    ["tools/big_move_forward.py", "2026-11-22", "2027-12-31", "--metal", "sensex"],
    ["tools/market_summary.py"],
    ["tools/calendar_rules_backtest.py"],
    ["tools/market_signal_table.py"],
    ["tools/validate_external_model.py"],
    ["tools/md_to_html.py", "Reference_materials/extracted/OTHERS_FINANCIAL_REVIEW.md", "Others Financial Review"],
    ["tools/md_to_html.py", "Reference_materials/extracted/FINANCIAL_ASTROLOGY_MODEL_v1.md", "Financial Astrology Model v1"],
    ["tools/md_to_html.py", "PROJECT_KNOWLEDGE.md", "FinAstro Project Knowledge"],
]


def run(args):
    print(">>", " ".join(args), flush=True)
    r = subprocess.run([PY] + args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tail = r.stdout.strip().splitlines()[-2:]
    for line in tail:
        print("   ", line[:200])
    if r.returncode:
        print(r.stdout[-3000:])
        raise SystemExit(f"step failed: {' '.join(args)}")


def main():
    if "--prices" in sys.argv:
        run(["tools/fetch_prices.py"])
    for s in STEPS:
        if s == ["tools/backtest_market.py"] and not (ROOT / "build/pdfref/backtest/market_events_2000-2026.json.gz").exists():
            run(["tools/market_events.py"])
        run(s)
    run(["-m", "pytest", "-q", "tests/test_pdfref.py", "tests/test_shadbala.py"])
    run(["tools/publish_reports.py"])
    print("all steps done")


if __name__ == "__main__":
    main()
