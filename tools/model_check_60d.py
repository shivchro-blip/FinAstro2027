"""Our model over the last 60 days: what each signal table would have said every day, against what happened.

    python tools/model_check_60d.py [END_DATE]        # default: today (US Eastern); window = 60 calendar days

Labels are produced exactly as the published tables produce them:
  * gold / silver: the signal-table scoring (tools/test_signal_table.py, in-sample definitions) for days
    up to 20 Nov 2026, and the published tables (gold_signals_*, silver_signals_*) from 22 Nov;
  * S&P 500 / Sensex: the market table's ten qualifying rules (tools/market_signal_table.py) rebuilt from the
    cached rule events and the 2026 calendar layer, and the published table from 23 Nov;
  * volatility: the robust big-move factors (market_summary) for the indices.
Each day: the label, the day's move and the next 5 sessions. Summary per label: days, share right (same day,
next 5 sessions), average move; big days on volatility days against other days.
Writes build/pdfref/model_check_60d_ET.{html,json}. Market prices and astrology only.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import gzip
import importlib.util
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
ET, IST = ZoneInfo("America/New_York"), ZoneInfo("Asia/Kolkata")
PRICE = {"gold": "gold_GC_F_daily_2000.csv", "silver": "silver_SI_F_daily_2000.csv", "spx": "spx_GSPC_daily_2000.csv", "sensex": "sensex_BSESN_daily_2000.csv"}
NAME = {"gold": "Gold", "silver": "Silver", "spx": "S&P 500", "sensex": "BSE Sensex"}
LIVE = {"gold": "Gold (GC=F)", "silver": "Silver (SI=F)", "spx": "S&P 500", "sensex": "BSE Sensex"}
BIG = {"gold": 2.0, "silver": 3.5, "spx": 2.0, "sensex": 2.0}
PTS = {"High": 3, "Moderate": 2, "Low": 1}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def prices(k, end):
    rows = {dt.date.fromisoformat(r["date"]): float(r["close"]) for r in csv.DictReader(open(OUT / "backtest" / PRICE[k]))}
    last = max(rows)
    if end > last:
        dr = load(ROOT / "tools" / "day_report.py", "dr")
        d = last + dt.timedelta(days=1)
        while d <= end:
            if d.weekday() < 5:
                for a in dr.actual(d):
                    if a["market"] == LIVE[k] and "change" in a and a.get("prev") == str(max(rows)):
                        rows[d] = a["close"]
            d += dt.timedelta(days=1)
    return dict(sorted(rows.items()))


def table_rows(path, key=None):
    j = json.load(open(path))
    rows = j["tables"][key] if key else j
    out = {}
    for r in rows:
        a, b = dt.date.fromisoformat(str(r["frm"])[:10]), dt.date.fromisoformat(str(r["to"])[:10])
        d = a
        while d <= b:
            out[d] = (r["sig"], r["st"])
            d += dt.timedelta(days=1)
    return out


def market_labels(a, b):
    """S&P / Sensex labels from the market table's qualifying rules, rebuilt for past days."""
    MS = load(ROOT / "tools" / "market_signal_table.py", "mst")
    mb = json.load(open(OUT / "market_backtest_2000-2026_ET.json"))
    cb = json.load(open(OUT / "calendar_rules_backtest_2000-2026_ET.json"))
    rules = {}
    for x in mb["rules"]:
        s, n = x["spx"], x["sensex"]
        if MS.held(s) and MS.held(n) and min(s["p_value"], n["p_value"]) < 0.05:
            rules[x["rule_id"]] = dict(title=x["title"], tone=x["tone"], st=MS.strength(s["p_value"], n["p_value"]))
    for x in cb["rules"]:
        s, n = x.get("spx"), x.get("sensex")
        if s and n and s["kind"] == "direction" and MS.held(s) and MS.held(n) and min(s["p_value"], n["p_value"]) < 0.05:
            rules[x["rule_id"]] = dict(title=x["provenance"].split(" p.")[0].split(" — ")[0], tone=x["tone"], st=MS.strength(s["p_value"], n["p_value"]))
    calls = collections.defaultdict(list)
    with gzip.open(OUT / "backtest" / "market_events_2000-2026.json.gz", "rt", encoding="utf-8") as fh:
        for e in json.load(fh):
            k = e["rule_id"] if e["rule_id"] in rules else f"{e['rule_id']}::{e['tone']}"
            if k not in rules or e["tone"] not in ("Bullish", "Bearish"):
                continue
            s = dt.datetime.fromisoformat(e["start"]).astimezone(ET).date() if not e["day"] else dt.date.fromisoformat(e["day"])
            en = dt.datetime.fromisoformat(e["end"]).astimezone(ET).date() if e["end"] else s
            if en < a - dt.timedelta(days=10) or s > b:
                continue
            days = MS.sessions_from(s) if (en - s).days < 2 else [s + dt.timedelta(days=i) for i in range((en - s).days + 1)]
            for d in days:
                calls[d].append(k)
    with gzip.open(OUT / "backtest" / "calendar_verdicts" / f"{b.year}.json.gz", "rt", encoding="utf-8") as fh:
        cal = json.load(fh)
    cal_calls = {"spx": collections.defaultdict(list), "sensex": collections.defaultdict(list)}
    rowdays = collections.defaultdict(set)
    for r in cal:
        mk = {"SPX": "spx", "NIFTY": "sensex"}.get(r["instrument"])
        if mk and r["rule_id"] in rules:
            rowdays[(mk, r["rule_id"])].add(dt.date.fromisoformat(r["date"]))
    for (mk, rid), ds in rowdays.items():                      # consecutive row days = one window, as in the backtest
        ds = sorted(ds)
        eps, cur = [], None
        for d in ds:
            if cur and (d - cur[1]).days <= 1:
                cur[1] = d
            else:
                cur = [d, d]
                eps.append(cur)
        for d0, d1 in eps:
            if (d1 - d0).days >= 2:
                days = [d0 + dt.timedelta(days=i) for i in range((d1 - d0).days + 1)]
            else:
                start = d0 + dt.timedelta(days=(7 - d0.weekday()) % 7) if d0.weekday() >= 5 else d0
                days = MS.sessions_from(start)
            for d in days:
                cal_calls[mk][d].append(rid)
    out = {}
    for mk in ("spx", "sensex"):
        lab = {}
        d = a
        while d <= b:
            ids = list(dict.fromkeys(calls.get(d, []) + cal_calls[mk].get(d, [])))
            net = sum(PTS[rules[i]["st"]] * (1 if rules[i]["tone"] == "Bullish" else -1) for i in ids)
            if net:
                lab[d] = ("Bullish" if net > 0 else "Bearish", "High" if abs(net) >= 3 else "Moderate" if abs(net) == 2 else "Low")
            d += dt.timedelta(days=1)
        out[mk] = lab
    return out


def robust_vol(a, b):
    V = load(ROOT / "tools" / "validate_external_model.py", "vem")
    out = {}
    for mk, fs in V.ROBUST.items():
        s = set()
        d = a
        while d <= b:
            if any(f(d) for f in fs.values()):
                s.add(d)
            d += dt.timedelta(days=1)
        out[mk] = s
    return out


def main():
    end = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(ET).date()
    start = end - dt.timedelta(days=60)
    labels = {}
    for mk, f in (("gold", "signal_table_test_2000-2026_ET.json"), ("silver", "silver_signal_table_test_2000-2026_ET.json")):
        lab = {dt.date.fromisoformat(r["date"]): (r["sig"], r["st"]) for r in json.load(open(OUT / f))["recent"] if r["sig"]}
        lab.update(table_rows(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json"))
        labels[mk] = lab
    ml = market_labels(start, min(end, dt.date(2026, 11, 22)))
    for mk in ("spx", "sensex"):
        lab = ml[mk]
        lab.update(table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", mk))
        labels[mk] = lab
    vol = robust_vol(start, end)
    res = dict(start=str(start), end=str(end), markets={})
    for mk in ("gold", "silver", "spx", "sensex"):
        P = prices(mk, end)
        D = list(P)
        rows = []
        for i, d in enumerate(D):
            if not (start <= d <= end) or i == 0:
                continue
            r1 = (P[d] / P[D[i - 1]] - 1) * 100
            r5 = (P[D[i + 4]] / P[D[i - 1]] - 1) * 100 if i + 4 < len(D) else None
            sig, st = labels[mk].get(d, (None, None))
            rows.append(dict(date=str(d), sig=sig or "No signal", st=st or "", r1=round(r1, 2), r5=None if r5 is None else round(r5, 2),
                             vol=d in vol.get(mk, set()), big=abs(r1) >= BIG[mk]))
        summ = {}
        for key in sorted({(r["sig"], r["st"]) for r in rows}):
            sel = [r for r in rows if (r["sig"], r["st"]) == key]
            dirn = 1 if key[0] == "Bullish" else -1 if key[0] == "Bearish" else 0
            s5 = [r for r in sel if r["r5"] is not None]
            summ[" ".join(x for x in key if x)] = dict(days=len(sel), avg1=round(sum(r["r1"] for r in sel) / len(sel), 2),
                                                       right1=round(sum((r["r1"] > 0) == (dirn > 0) for r in sel) / len(sel) * 100) if dirn else None,
                                                       right5=round(sum((r["r5"] > 0) == (dirn > 0) for r in s5) / len(s5) * 100) if dirn and s5 else None,
                                                       up1=round(sum(r["r1"] > 0 for r in sel) / len(sel) * 100))
        vd = [r for r in rows if r["vol"]]
        nv = [r for r in rows if not r["vol"]]
        res["markets"][mk] = dict(name=NAME[mk], rows=rows, summary=summ, up_share=round(sum(r["r1"] > 0 for r in rows) / len(rows) * 100),
                                  move=round((P[D[-1]] / P[[d for d in D if d < start][-1]] - 1) * 100, 1),
                                  vol=dict(days=len(vd), big=sum(r["big"] for r in vd), other_days=len(nv), other_big=sum(r["big"] for r in nv)))
    json.dump(res, open(OUT / "model_check_60d_ET.json", "w"), indent=1, default=str)
    write(res)
    for mk, m in res["markets"].items():
        print(m["name"], "move", m["move"], "% up days", m["up_share"], "vol", m["vol"])
        for k, v in m["summary"].items():
            print("   ", k, v)


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    blocks, srows = "", ""
    for mk, m in res["markets"].items():
        for k, v in m["summary"].items():
            srows += (f"<tr><td>{m['name']}</td><td><b>{k}</b></td><td class='n'>{v['days']}</td><td class='n'>{'' if v['right1'] is None else str(v['right1']) + '%'}</td>"
                      f"<td class='n'>{'' if v['right5'] is None else str(v['right5']) + '%'}</td><td class='n'>{v['avg1']:+.2f}%</td><td class='n'>{v['up1']}%</td></tr>")
        cls = {"Bullish": "bullish", "Bearish": "bearish", "Volatile": "mixed"}
        rows = "".join(f"<tr class='{cls.get(r['sig'], '')}'><td class='w'>{dt.date.fromisoformat(r['date']):%a %d %b}</td><td>{r['sig']} {r['st']}</td>"
                       f"<td class='n'><b>{r['r1']:+.2f}%</b></td><td class='n'>{'' if r['r5'] is None else format(r['r5'], '+.2f') + '%'}</td><td>{'volatility factor' if r['vol'] else ''}{' · big day' if r['big'] else ''}</td></tr>"
                       for r in reversed(m["rows"]))
        v = m["vol"]
        blocks += (f"<details><summary><b>{m['name']}</b>: {m['move']:+.1f}% over the window; big days {v['big']} of {v['days']} volatility-factor days vs {v['other_big']} of {v['other_days']} other days</summary>"
                   f"<div class='wrap'><table><thead><tr><th>Day</th><th>Our label</th><th>Day's move</th><th>Next 5 sessions</th><th></th></tr></thead><tbody>{rows}</tbody></table></div></details>")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Model Check 60 Days</title><style>{css}</style></head><body>
<h1>Our model over the last 60 days ({dt.date.fromisoformat(res['start']):%d %b} – {dt.date.fromisoformat(res['end']):%d %b %Y})</h1>
<p class="m">Every label our signal tables give, rebuilt for each past day exactly as the tables build it, against what the market did that day and over the next 5 sessions. Sixty days is a short sample: read it as a health check, not as a new test.</p>
<div class="wrap"><table><thead><tr><th>Market</th><th>Label</th><th>Days</th><th>Right, same day</th><th>Right, next 5 sessions</th><th>Average day</th><th>Up days</th></tr></thead><tbody>{srows}</tbody></table></div>
<h2>Day by day</h2>{blocks}
<p class="s">Generated by tools/model_check_60d.py. Market prices and astrology only.</p></body></html>"""
    (OUT / "model_check_60d_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
