"""Generate the astronomy layer for any year (Dec of the year before - Jan of the year after).

    python tools/build_year.py 2023          -> build/astronomy_2023.json

The same path as tools/build_2026.py / build_2025.py: build_2027.py run with
the year set *before* finastro.events is imported (both names that hold the
year are set; see build_2026.py for why). Used by the multi-year gold
backtest (tools/backtest_gold.py), which builds a missing year on demand.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

YEAR = int(sys.argv[1])

from finastro import config as _config          # noqa: E402

_config.CONF["year"] = YEAR
_config.YEAR = YEAR

import build_2027 as B                          # noqa: E402

B.OUT_JSON = ROOT / "build" / f"astronomy_{YEAR}.json"
B.OUT_SUMMARY = ROOT / "build" / f"astronomy_{YEAR}_summary.txt"

if __name__ == "__main__":
    assert B.YEAR == YEAR, B.YEAR
    assert B.SPAN_START.astimezone(B.IST).year == YEAR - 1, B.SPAN_START
    assert B.SPAN_END.astimezone(B.IST).year == YEAR + 1, B.SPAN_END
    raise SystemExit(B.main())
