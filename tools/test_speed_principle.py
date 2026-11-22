"""Test: "slow-moving planets set the trend; fast-moving planets set volatility and sudden moves".

    python tools/test_speed_principle.py

Sources of the idea: Kindle Ch.3 / Ch.6 ("the Moon for intraday, the slow planets
for the primary trend"); TA p.59-60 (Moon "very short term", Mercury "sudden
sentiment changer"); KD p.82 / p.129 (a planet's slow motion prolongs a move).

Part A - volatility / sudden moves (event study on the astronomy layer, independent
of any rule). For each event class, the size of gold's and silver's move after the
event (|1-day| and |5-day| from the close before the event) and the share of events
followed within 3 trading days by a "sudden" day (|daily move| > 2 standard
deviations of that year), compared with all days. Fast classes: new / full Moon,
Moon-quarter, Mercury and Venus stations and sign ingresses, Sun ingress. Slow
classes: Jupiter, Saturn and Rahu sign ingresses, Jupiter / Saturn / outer-planet
stations. Eclipses separately.

Part B - trend (direction over long windows). Pooled 26-year results of the gold /
silver rules (tools/backtest_gold.py) grouped by the speed of the planets the rule
names: slow (Jupiter, Saturn, Rahu, Ketu, outer planets only), fast (Moon, Mercury,
Venus, Sun only), mixed. If slow planets set the trend, slow-planet rules should
beat their base rate more than fast-planet rules.

Writes build/pdfref/speed_principle_test_2000-2026_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import html
import json
import math
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finastro.sky import parse  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
SLOW = {"Jupiter", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"}
FAST = {"Moon", "Mercury", "Venus", "Sun"}


def prices(m):
    rows = list(csv.DictReader(open(OUT / "backtest" / f"{m}_daily_2000.csv")))
    return [dt.date.fromisoformat(r["date"]) for r in rows], [float(r["close"]) for r in rows]


def classify(r):
    ec, b = r["event_class"], r["bodies"][0] if r["bodies"] else ""
    fam = r.get("rule_family", "")
    if ec == "lunation":
        return "New / full Moon (fast)" if fam.endswith(("new_moon", "full_moon")) else "Moon quarter (fast)"
    if ec == "station" and b in ("Mercury", "Venus"):
        return "Mercury / Venus station (fast)"
    if ec == "sign_ingress" and b in ("Mercury", "Venus"):
        return "Mercury / Venus sign ingress (fast)"
    if ec == "sign_ingress" and b == "Sun":
        return "Sun sign ingress / Sankranti (fast)"
    if ec == "sign_ingress" and b == "Mars":
        return "Mars sign ingress (medium)"
    if ec == "station" and b == "Mars":
        return "Mars station (medium)"
    if ec == "sign_ingress" and b in ("Jupiter", "Saturn", "Rahu"):
        return "Jupiter / Saturn / Rahu sign ingress (slow)"
    if ec == "station" and b in ("Jupiter", "Saturn"):
        return "Jupiter / Saturn station (slow)"
    if ec == "station" and b in ("Uranus", "Neptune", "Pluto"):
        return "Outer-planet station (slow)"
    if ec == "eclipse":
        return "Eclipse"
    return None


def events():
    out, seen = [], set()
    for y in range(2000, 2027):
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            c = classify(r)
            if not c:
                continue
            t = parse(r["time"]["t_start_utc"])
            k = (c, r["bodies"][0] if r["bodies"] else "", t.replace(second=0, minute=0))
            if k in seen:
                continue
            seen.add(k)
            out.append((t, c))
    return sorted(out)


def idx_before(D, t):
    x = t.astimezone(ET)
    day = x.date() + (dt.timedelta(days=1) if x.hour >= 17 else dt.timedelta(0))
    return bisect.bisect_left(D, day) - 1


def tstat(a, b):
    va, vb = statistics.pvariance(a), statistics.pvariance(b)
    return (statistics.fmean(a) - statistics.fmean(b)) / math.sqrt(va / len(a) + vb / len(b)) if len(a) > 2 else None


def part_a(metal, evs):
    D, C = prices(metal)
    r1 = [abs(C[i] / C[i - 1] - 1) * 100 for i in range(1, len(C))]
    # yearly 2-sigma threshold for "sudden" days
    by_y = collections.defaultdict(list)
    for i in range(1, len(C)):
        by_y[D[i].year].append((C[i] / C[i - 1] - 1) * 100)
    thr = {y: 2 * statistics.pstdev(v) for y, v in by_y.items()}
    sudden = [False] + [abs(C[i] / C[i - 1] - 1) * 100 > thr[D[i].year] for i in range(1, len(C))]
    base1 = r1
    base5 = [abs(C[i + 5] / C[i] - 1) * 100 for i in range(len(C) - 5)]
    base_s3 = [any(sudden[i + 1:i + 4]) for i in range(len(C) - 4)]
    res = {}
    groups = collections.defaultdict(list)
    for t, c in evs:
        i = idx_before(D, t)
        if i < 1 or i + 5 >= len(C) or D[i] < dt.date(2000, 9, 1):
            continue
        groups[c].append(i)
    for c, ix in sorted(groups.items()):
        a1 = [abs(C[i + 1] / C[i] - 1) * 100 for i in ix]
        a5 = [abs(C[i + 5] / C[i] - 1) * 100 for i in ix]
        s3 = [any(sudden[i + 1:i + 4]) for i in ix]
        res[c] = dict(n=len(ix), abs1=round(statistics.fmean(a1), 3), abs5=round(statistics.fmean(a5), 3),
                      ratio1=round(statistics.fmean(a1) / statistics.fmean(base1), 3), ratio5=round(statistics.fmean(a5) / statistics.fmean(base5), 3),
                      t1=round(tstat(a1, base1), 2), t5=round(tstat(a5, base5), 2),
                      sudden3=round(sum(s3) / len(s3) * 100, 1), sudden3_base=round(sum(base_s3) / len(base_s3) * 100, 1))
    res["_base"] = dict(abs1=round(statistics.fmean(base1), 3), abs5=round(statistics.fmean(base5), 3), sudden3=round(sum(base_s3) / len(base_s3) * 100, 1))
    return res


def speed_class(bodies):
    bs = {b for b in bodies if b}
    if not bs:
        return None
    if bs <= SLOW:
        return "slow planets only"
    if bs <= FAST:
        return "fast planets only"
    if bs <= SLOW | {"Mars"} and "Mars" in bs:
        return "Mars with slow planets"
    return "mixed / with Mars"


def part_b(metal):
    d = json.load(open(OUT / f"{metal}_backtest_2000-11-20_to_2026-11-20_ET.json"))
    g = collections.defaultdict(lambda: dict(w=0, f=0, base=[], rets=[], rules=set(), days=[]))
    for e in d["events"]:
        if e.get("component") or e.get("outcome") not in ("WORKED", "FAILED"):
            continue
        c = speed_class(e.get("bodies") or [])
        if not c:
            continue
        x = g[c]
        x["w" if e["outcome"] == "WORKED" else "f"] += 1
        x["rules"].add(e["rule_id"])
        x["days"].append(e.get("n_days", 0))
        x["rets"].append(e["ret"] if e["tone"] == "Bullish" else -e["ret"])
    base = {p["rule_id"]: p["base_rate"] for p in d["rules"] if p.get("base_rate") is not None}
    out = {}
    for c, x in g.items():
        dec = x["w"] + x["f"]
        bs = [base[r] for r in x["rules"] if r in base]
        out[c] = dict(decided=dec, worked=x["w"], hit=round(x["w"] / dec * 100, 1), rules=len(x["rules"]), base=round(statistics.fmean(bs), 1) if bs else None,
                      avg_dir_move=round(statistics.fmean(x["rets"]), 2), median_days=statistics.median(x["days"]))
    return out


def main():
    evs = events()
    res = {"A": {m: part_a(m, evs) for m in ("gold_GC_F", "silver_SI_F")}, "B": {m: part_b(m) for m in ("gold", "silver")}}
    json.dump(res, open(OUT / "speed_principle_test_2000-2026_ET.json", "w"), indent=1)
    write(res)
    for m, r in res["A"].items():
        print(m, r["_base"])
        for c, v in r.items():
            if c != "_base":
                print(f"   {c:42s} n={v['n']:4d} |1d| x{v['ratio1']:.2f} (t {v['t1']:+.1f})  |5d| x{v['ratio5']:.2f} (t {v['t5']:+.1f})  sudden<=3d {v['sudden3']}% vs {v['sudden3_base']}%")
    for m, r in res["B"].items():
        print(m, json.dumps(r))


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    def a_rows(r):
        rows = []
        for c, v in sorted(((c, v) for c, v in r.items() if c != "_base"), key=lambda kv: ("(fast)" not in kv[0], "(medium)" not in kv[0], kv[0])):
            cl = "bullish" if v["ratio5"] > 1.1 and v["t5"] >= 2 else "bearish" if v["ratio5"] < 0.9 and v["t5"] <= -2 else "mixed"
            rows.append(f"<tr class='{cl}'><td>{html.escape(c)}</td><td class='n'>{v['n']}</td><td class='n'>{v['abs1']:.2f}% (×{v['ratio1']:.2f}, t {v['t1']:+.1f})</td>"
                        f"<td class='n'>{v['abs5']:.2f}% (×{v['ratio5']:.2f}, t {v['t5']:+.1f})</td><td class='n'>{v['sudden3']}% vs {v['sudden3_base']}%</td></tr>")
        return "".join(rows)
    a_html = "".join(f"<h3>{m.split('_')[0].capitalize()} (all days: |1d| {r['_base']['abs1']:.2f}%, |5d| {r['_base']['abs5']:.2f}%, a sudden day within 3 days {r['_base']['sudden3']}%)</h3>"
                     f"<div class='wrap'><table><thead><tr><th>Event class</th><th>Events</th><th>Size of next-day move</th><th>Size of next-5-day move</th><th>Sudden (>2σ) day within 3 trading days</th></tr></thead><tbody>{a_rows(r)}</tbody></table></div>"
                     for m, r in res["A"].items())
    b_html = "".join(f"<h3>{m.capitalize()}</h3><div class='wrap'><table><thead><tr><th>Rules naming…</th><th>Rules</th><th>Decided occurrences</th><th>Hit rate</th><th>Avg base rate of those rules</th><th>Avg move in stated direction</th><th>Median length (trading days)</th></tr></thead><tbody>"
                     + "".join(f"<tr><td>{html.escape(c)}</td><td class='n'>{v['rules']}</td><td class='n'>{v['decided']}</td><td class='n'><b>{v['hit']}%</b></td><td class='n'>{v['base']}%</td><td class='n'>{v['avg_dir_move']:+.2f}%</td><td class='n'>{v['median_days']}</td></tr>" for c, v in sorted(r.items()))
                     + "</tbody></table></div>" for m, r in res["B"].items())
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Planet Speed Test</title><style>{css}</style></head><body>
<h1>"Slow planets set the trend, fast planets the sudden moves": test on gold and silver, 2000–2026</h1>
<p class="m">Idea as stated in Kindle Ch.3 / Ch.6 (Moon intraday, slow planets the primary trend), TA p.59–60 (Moon very short term; Mercury a sudden sentiment changer) and KD p.82 / p.129 (slow motion prolongs a move). COMEX GC=F and SI=F daily closes, Aug 2000 – Nov 2026; events from the astronomy layer (Swiss Ephemeris, Lahiri). {{VERDICT}}</p>
<h2>A. Do fast-planet events bring bigger or sudden moves?</h2>
<p class="m">Move size from the close before the event, against all days. ×1.00 = the same as any day. Green = significantly bigger (×1.10+, t ≥ 2); red = significantly smaller.</p>
{a_html}
<h2>B. Do slow-planet rules get the trend right more often?</h2>
<p class="m">26-year backtest results of the gold / silver rules, pooled by the speed of the planets each rule names. Long windows (median length) belong to the slow-planet rules by nature; the question is whether they beat their base rate.</p>
{b_html}
<p class="s">Generated by tools/test_speed_principle.py.</p></body></html>"""
    ra, rb = res["A"]["gold_GC_F"], res["B"]["gold"]
    fast = [v for c, v in ra.items() if "(fast)" in c]
    slow = [v for c, v in ra.items() if "(slow)" in c]
    sig_fast = [c for c, v in ra.items() if "(fast)" in c and v["ratio5"] > 1.1 and v["t5"] >= 2]
    verdict = (f"<b>Gold result:</b> after fast-planet events the next-5-day move averaged ×{statistics.fmean(v['ratio5'] for v in fast):.2f} of a normal 5-day move "
               f"(slow-planet events ×{statistics.fmean(v['ratio5'] for v in slow):.2f}); significantly bigger moves after: {', '.join(sig_fast) or 'none'}. "
               f"Slow-planet-only rules hit {rb.get('slow planets only', {}).get('hit', '–')}% (base {rb.get('slow planets only', {}).get('base', '–')}%), "
               f"fast-planet-only rules {rb.get('fast planets only', {}).get('hit', '–')}% (base {rb.get('fast planets only', {}).get('base', '–')}%).")
    (OUT / "speed_principle_test_2000-2026_ET.html").write_text(page.replace("{VERDICT}", verdict), encoding="utf-8")


if __name__ == "__main__":
    main()
