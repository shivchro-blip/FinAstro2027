"""Detect every general-market rule event 20 Nov 2000 - 20 Nov 2026 (input to tools/backtest_market.py).

    python tools/market_events.py

Rules: every catalogue rule tagged "general" with a detector (TA / KD / the 2026 document;
about 628). Detection reuses tools/backtest_gold.py collect() in 5-year chunks, as the
gold 26-year run does. Writes build/pdfref/backtest/market_events_2000-2026.json.gz
(git-ignored cache; about half an hour to rebuild).
"""
from __future__ import annotations

import datetime as dt
import gzip
import importlib.util
import json
import pathlib
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky  # noqa: E402
from finastro.pdfref.detect import Ctx  # noqa: E402
from finastro.pdfref.engine import Grid, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
CACHE = ROOT / "build" / "pdfref" / "backtest" / "market_events_2000-2026.json.gz"


def main():
    spec = importlib.util.spec_from_file_location("bt", ROOT / "tools" / "backtest_gold.py")
    B = importlib.util.module_from_spec(spec)
    sys.modules["bt"] = B
    spec.loader.exec_module(B)
    B.M.METAL = "general"
    B.M.EXCLUDE["general"] = set()
    B.M.EXTRA["general"] = []
    B.METAL = "general"
    B.P0 = dt.datetime(2000, 11, 20, tzinfo=ET)
    B.P1 = dt.datetime(2026, 11, 21, tzinfo=ET)
    for y in range(1999, 2028):
        if not (ROOT / "build" / f"astronomy_{y}.json").exists():
            subprocess.run([sys.executable, "tools/build_year.py", str(y)], cwd=ROOT, check=True)
    out = []
    for c0 in range(2000, 2027, 5):
        t = time.time()
        lo = dt.datetime(c0, 11, 20, tzinfo=ET) if c0 > 2000 else B.P0
        hi = min(dt.datetime(c0 + 5, 11, 20, tzinfo=ET), B.P1)
        if lo >= B.P1:
            break
        grid = Grid(utc(c0 - 1, 6, 1), utc(min(c0 + 6, 2027), 6, 30))
        ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in range(c0, min(c0 + 7, 2028))
                if (ROOT / "build" / f"astronomy_{y}.json").exists()]
        ev = B.collect(ctxs, lo, hi)
        for e in ev:
            out.append(dict(rule_id=e["rule_id"], title=e["title"], refs=e["refs"], tone=e["tone"], verdict=e["verdict"],
                            start=e["start"].isoformat(), end=e["end"].isoformat() if e["end"] else None,
                            day=e["day"].isoformat() if e["day"] else None))
        print(f"chunk {c0}: {len(ev)} events, {time.time() - t:.0f}s", flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(CACHE, "wt", encoding="utf-8") as f:
        json.dump(out, f)
    print(f"{len(out)} events -> {CACHE}")


if __name__ == "__main__":
    main()
