"""Download COMEX gold (GC=F) and silver (SI=F), S&P 500 (^GSPC) and BSE Sensex (^BSESN) daily bars from Yahoo Finance.

    python tools/fetch_prices.py

Writes build/pdfref/backtest/{gold_GC_F,silver_SI_F}_daily.csv (1 Jan 2021 onward,
used by tools/backtest_gold.py) and *_daily_2000.csv (Aug 2000 onward, used by
tools/test_source_rules.py and tools/build_bs41_model.py). Dates are New York
trading dates; the last bar can be an intraday value if run during the session.
Needs the environment to allow query1.finance.yahoo.com (added to the FinAstro2027
environment on 20 Nov 2026; stooq.com blocks automated downloads).
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import time
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref" / "backtest"
NY = ZoneInfo("America/New_York")
SYMBOLS = {"gold_GC_F": "GC%3DF", "silver_SI_F": "SI%3DF"}
INDICES = {"spx_GSPC": ("%5EGSPC", "America/New_York"), "sensex_BSESN": ("%5EBSESN", "Asia/Kolkata")}   # dates in each exchange's own time zone


def fetch(sym, start, tz=NY):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={int(start.timestamp())}"
           f"&period2={int(time.time()) + 86400}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = json.load(urllib.request.urlopen(req, timeout=90))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    rows = []
    for t, o, h, lo, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if c is not None:
            rows.append((dt.datetime.fromtimestamp(t, tz).date().isoformat(), o, h, lo, c))
    dates = [x[0] for x in rows]
    assert len(dates) == len(set(dates)), "duplicate dates"
    return rows


def write(path, rows):
    with open(path, "w") as f:
        f.write("date,open,high,low,close\n")
        for x in rows:
            f.write(",".join(str(v) for v in x) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, sym in SYMBOLS.items():
        rows = fetch(sym, dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc))
        write(OUT / f"{name}_daily_2000.csv", rows)
        write(OUT / f"{name}_daily.csv", [x for x in rows if x[0] >= "2021-01-01"])
        print(name, len(rows), rows[0][0], "->", rows[-1][0], rows[-1][4])
    for name, (sym, tz) in INDICES.items():
        rows = fetch(sym, dt.datetime(1999, 1, 1, tzinfo=dt.timezone.utc), ZoneInfo(tz))
        write(OUT / f"{name}_daily_2000.csv", rows)
        print(name, len(rows), rows[0][0], "->", rows[-1][0], rows[-1][4])


if __name__ == "__main__":
    main()
