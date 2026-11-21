"""Generate the astronomy layer for 2025 (Dec 2024 - Jan 2026) for the gold backtest.

Not a second engine. This is `build_2027.py` run with the year set to 2025
*before* `finastro.events` is imported, so the span constants, the total-day
series and every generator derive from the fixture year exactly as they derive
from 2027 in the normal build. Nothing is recomputed here and nothing is
transcribed: the only difference between the two runs is the year and the
output path.

It exists because the rule layer reads a GENERATED calendar and never the
ephemeris. To run the rules over late 2025 -- which the gold backtest
(tools/backtest_gold.py) needs -- 2025 has to be generated through the same path 2027 was.

TWO NAMES HOLD THE YEAR, and both have to be set. `config.py` binds
`YEAR = CONF["year"]` at import, and `events.py` imports that NAME rather than
re-reading the dict, so mutating `CONF["year"]` alone leaves `events.SPAN_START`
on 2027. The asserts below are not decoration: the first version of this file
set only the dict and generated a 2027 span under a 2025 filename, which is
exactly the class of silent wrong answer §12.16 is about.

    python tools/build_2025.py
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro import config as _config          # noqa: E402

_config.CONF["year"] = 2025
_config.YEAR = 2025

import build_2027 as B                          # noqa: E402

B.OUT_JSON = ROOT / "build" / "astronomy_2025.json"
B.OUT_SUMMARY = ROOT / "build" / "astronomy_2025_summary.txt"

if __name__ == "__main__":
    assert B.YEAR == 2025, B.YEAR
    assert B.SPAN_START.astimezone(B.IST).year == 2024, B.SPAN_START
    assert B.SPAN_END.astimezone(B.IST).year == 2026, B.SPAN_END
    raise SystemExit(B.main())
