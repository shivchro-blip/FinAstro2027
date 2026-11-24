"""Astrology-only reading of a day: the net tally of active document rules with a good record, and
whether that tally has ever called the S&P 500 / Sensex direction (walk-forward).

    python tools/rule_tally.py [DATE ...]          # default: 2026-11-20 2026-11-23

Rules: the general-market catalogue rules (cached events of tools/market_events.py) scored in
market_backtest_2000-2026_ET.json. Instants count for the 5 sessions they were scored on, windows
while they last, day-rules on their day.
  * Tally of a day: bullish minus bearish active rules whose 26-year record is above base
    (status Strongest / Supported / Consistent) - what the planets "said".
  * Walk-forward test: rules qualify on 2000-2013 only (10+ decided, hit > base, p < 0.20); on each
    2013-2026 trading day the net of qualifying active rules is compared with that day's move and
    the next 5 sessions' move (up share by sign of the net, against the same years' up share).
Writes build/pdfref/rule_tally_ET.{html,json}. News is not used (project decision, 24 Nov 2026).
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import gzip
import html
import json
import math
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
MK = {"spx": ("S&P 500", "spx_GSPC_daily_2000.csv", ZoneInfo("America/New_York"), dt.time(16, 0)),
      "sensex": ("BSE Sensex", "sensex_BSESN_daily_2000.csv", ZoneInfo("Asia/Kolkata"), dt.time(15, 30))}
GOOD = ("Strongest", "Supported", "Consistent")
SPLIT, P1 = dt.date(2013, 11, 20), dt.date(2026, 11, 20)


def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


def binom_two_sided(k, n, p):
    if not n:
        return None
    z = (k - n * p) / (math.sqrt(n * p * (1 - p)) or 1)
    return round(math.erfc(abs(z) / math.sqrt(2)), 4)


def active_days(e, D, tz, close):
    """Trading-day indices on which an event counts."""
    def sday(t):
        x = dt.datetime.fromisoformat(t).astimezone(tz)
        return x.date() + (dt.timedelta(days=1) if x.time() >= close else dt.timedelta(0))
    if e["day"]:
        d = dt.date.fromisoformat(e["day"])
        i = bisect.bisect_left(D, d)
        return [i] if i < len(D) and D[i] == d else []
    s = sday(e["start"])
    i = bisect.bisect_left(D, s)
    if e["end"]:
        en = sday(e["end"])
        if (dt.datetime.fromisoformat(e["end"]) - dt.datetime.fromisoformat(e["start"])).days >= 3:
            j = bisect.bisect_left(D, en)
            return list(range(i, min(j, len(D))))
    return list(range(i, min(i + 5, len(D))))


def main():
    days = [dt.date.fromisoformat(x) for x in sys.argv[1:]] or [dt.date(2026, 11, 20), dt.date(2026, 11, 23)]
    mb = json.load(open(OUT / "market_backtest_2000-2026_ET.json"))
    with gzip.open(OUT / "backtest" / "market_events_2000-2026.json.gz", "rt", encoding="utf-8") as fh:
        events = [e for e in json.load(fh) if e["tone"] in ("Bullish", "Bearish")]
    # forward events (after 20 Nov 2026) for the requested days come from the catalogue directly
    fwd = forward_events(days) if max(days) > P1 else []
    res = dict(days={}, test={})
    for k, (name, f, tz, close) in MK.items():
        rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / f))]
        D = [r[0] for r in rows]
        C = [r[1] for r in rows]
        rec = {}
        for x in mb["rules"]:
            r = x[k]
            if r:
                rec[x["rule_id"]] = r
        def key(e):
            return e["rule_id"] if e["rule_id"] in rec else f"{e['rule_id']}::{e['tone']}"
        good = {rid for rid, r in rec.items() if r["status"] in GOOD}
        h1q = {rid for rid, r in rec.items() if r["h1"]["worked"] + r["h1"]["failed"] >= 10 and r["h1"]["hit_rate"] > r["h1"]["base_rate"] and (r["h1"]["p_value"] or 1) < 0.20}
        net_full = collections.Counter()
        net_h1 = collections.Counter()
        listing = collections.defaultdict(list)
        Dx = D + [d for d in days if d > D[-1]]
        for e in events + fwd:
            kk = key(e)
            sgn = 1 if e["tone"] == "Bullish" else -1
            for i in active_days(e, Dx, tz, close):
                if kk in good:
                    net_full[i] += sgn
                    if Dx[i] in days:
                        listing[Dx[i]].append((e["title"], e["tone"], rec[kk]["status"], f"{rec[kk]['worked']}/{rec[kk]['worked'] + rec[kk]['failed']} ({rec[kk]['hit_rate']}% vs {rec[kk]['base_rate']}%)"))
                if kk in h1q:
                    net_h1[i] += sgn
        for d in days:
            i = Dx.index(d) if d in Dx else None
            items = sorted(set(listing[d]))
            move = round((C[i] / C[i - 1] - 1) * 100, 2) if i is not None and i < len(C) else live_move(d, name)
            nb, nr = sum(1 for x in items if x[1] == "Bullish"), sum(1 for x in items if x[1] == "Bearish")
            res["days"].setdefault(str(d), {})[k] = dict(market=name, net=nb - nr,
                                                          bull=sum(1 for x in items if x[1] == "Bullish"), bear=sum(1 for x in items if x[1] == "Bearish"),
                                                          rules=items, move=move)
        # walk-forward test on 2013-2026
        out = {}
        for label, H in (("same day", 0), ("next 5 sessions", 5)):
            yr = collections.defaultdict(lambda: [0, 0])
            for i in range(1, len(C) - 6):
                if SPLIT <= D[i] <= P1:
                    yr[nov_year(D[i])][0] += 1
                    yr[nov_year(D[i])][1] += (C[i] > C[i - 1]) if H == 0 else (C[i + H - 1] > C[i - 1])
            for side in ("bullish net", "bearish net"):
                sel = [i for i in range(1, len(C) - 6) if SPLIT <= D[i] <= P1 and ((net_h1.get(i, 0) > 0) if side == "bullish net" else (net_h1.get(i, 0) < 0))]
                if H == 0:
                    ups = sum(C[i] > C[i - 1] for i in sel)
                else:
                    ups = sum(C[i + H - 1] > C[i - 1] for i in sel)
                exp = sum(yr[nov_year(D[i])][1] / yr[nov_year(D[i])][0] for i in sel) / max(len(sel), 1)
                hit = ups / len(sel) if side == "bullish net" else 1 - ups / len(sel)
                out[f"{label}, {side}"] = dict(n=len(sel), right=round(hit * 100, 1), base=round((exp if side == 'bullish net' else 1 - exp) * 100, 1),
                                               p=binom_two_sided(round(hit * len(sel)), len(sel), exp if side == "bullish net" else 1 - exp))
        res["test"][k] = dict(market=name, n_rules_h1=len(h1q), results=out)
    json.dump(res, open(OUT / "rule_tally_ET.json", "w"), indent=1, default=str)
    write(res)
    for d, v in res["days"].items():
        for k, x in v.items():
            print(d, x["market"], "net", x["net"], f"({x['bull']} bullish / {x['bear']} bearish)", "move", x["move"])
    for k, t in res["test"].items():
        print(t["market"], t["n_rules_h1"], t["results"])


def live_move(d, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location("dr", ROOT / "tools" / "day_report.py")
    dr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dr)
    for a in dr.actual(d):
        if a["market"] == name and "change" in a:
            return a["change"]
    return None


def forward_events(days):
    import importlib.util
    sys.path.insert(0, str(ROOT))
    from finastro.sky import Sky
    from finastro.pdfref.detect import Ctx
    from finastro.pdfref.engine import Grid, utc
    spec = importlib.util.spec_from_file_location("bt", ROOT / "tools" / "backtest_gold.py")
    B = importlib.util.module_from_spec(spec)
    sys.modules["bt"] = B
    spec.loader.exec_module(B)
    B.M.METAL = "general"
    B.M.EXCLUDE["general"] = set()
    B.M.EXTRA["general"] = []
    B.METAL = "general"
    et = ZoneInfo("America/New_York")
    B.P0 = dt.datetime.combine(P1 - dt.timedelta(days=10), dt.time(0), et)
    B.P1 = dt.datetime.combine(max(days) + dt.timedelta(days=1), dt.time(0), et)
    y = max(days).year
    grid = Grid(utc(y - 1, 6, 1), utc(y + 1, 6, 30))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{yy}.json"), yy) for yy in (y - 1, y, y + 1) if (ROOT / "build" / f"astronomy_{yy}.json").exists()]
    out = []
    for e in B.collect(ctxs):
        if e["tone"] in ("Bullish", "Bearish") and (e["start"].date() > P1 - dt.timedelta(days=8)):
            out.append(dict(rule_id=e["rule_id"], title=e["title"], tone=e["tone"], start=e["start"].isoformat(),
                            end=e["end"].isoformat() if e["end"] else None, day=e["day"].isoformat() if e["day"] else None))
    return out


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    drows = ""
    for d, v in res["days"].items():
        for k, x in v.items():
            lst = "<br>".join(f"{'▲' if t == 'Bullish' else '▼'} {html.escape(a)} – {s}, {r}" for a, t, s, r in x["rules"])
            cls = "bullish" if (x["net"] or 0) > 0 else "bearish" if (x["net"] or 0) < 0 else ""
            drows += (f"<tr class='{cls}'><td class='w'><b>{dt.date.fromisoformat(d):%a %d %b %Y}</b></td><td>{x['market']}</td><td class='n'><b>{x['net']:+d}</b> ({x['bull']} ▲ / {x['bear']} ▼)</td>"
                      f"<td class='n'>{'' if x['move'] is None else format(x['move'], '+.2f') + '%'}</td><td class='s'>{lst}</td></tr>")
    trows = ""
    for k, t in res["test"].items():
        for lab, r in t["results"].items():
            trows += f"<tr><td>{t['market']}</td><td>{lab}</td><td class='n'>{r['n']}</td><td class='n'><b>{r['right']}%</b></td><td class='n'>{r['base']}%</td><td class='n'>{r['p']}</td></tr>"
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rule Tally</title><style>{css}</style></head><body>
<h1>What the planets said: the net tally of document rules with a good record</h1>
<p class="m">Astrology and market prices only. For each day: the general-market rules (TA, KD, 2026 document) that were active and have a 26-year record above base on that index, bullish minus bearish.</p>
<div class="wrap"><table><thead><tr><th>Day</th><th>Index</th><th>Net tally</th><th>Move</th><th>Rules (record on this index)</th></tr></thead><tbody>{drows}</tbody></table></div>
<h2>Has the tally ever called direction? Walk-forward 2013–2026</h2>
<p class="m">Rules chosen on 2000–2013 only (10+ decided, above base, p &lt; 0.20); on each 2013–2026 day the net of those active rules, against the day's move and the next 5 sessions.</p>
<div class="wrap"><table><thead><tr><th>Index</th><th>Test</th><th>Days</th><th>Right</th><th>Base</th><th>p</th></tr></thead><tbody>{trows}</tbody></table></div>
<p class="s">Generated by tools/rule_tally.py.</p></body></html>"""
    (OUT / "rule_tally_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
