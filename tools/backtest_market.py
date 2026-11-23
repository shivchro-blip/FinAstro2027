"""26-year backtest of every general-market rule on the S&P 500 and the BSE Sensex, 2000-2026.

    python tools/market_events.py      # once: detect the events (cache, ~30 min)
    python tools/backtest_market.py

Rules: every catalogue rule tagged "general" (TA, KD, the 2026 document) with a detector.
Prices: S&P 500 (^GSPC, New York dates, close 16:00 ET) and BSE Sensex (^BSESN, Mumbai
dates, close 15:30 IST), build/pdfref/backtest/{spx_GSPC,sensex_BSESN}_daily_2000.csv.
Scoring as for gold (PROJECT_KNOWLEDGE section 6), in each exchange's own time:
  * entry = last close before the event (an event after the close counts from the next
    session; a day-rule counts from that day's open);
  * windows of 3+ calendar days spanning 2+ sessions: entry to the last close inside the
    window, clipped to the entry's Nov-Nov year; otherwise the 5-session move;
  * |move| < 0.5% FLAT; Bullish worked if up, Bearish if down;
  * base = share of same-length moves (> 0.5%) in the same Nov-Nov year that went the rule's
    way; one-sided binomial p; right in a year = more worked than failed that year;
  * Benjamini-Hochberg q over every rule with 10+ decided cases, per market;
  * status and "best" exactly as the gold tracker (tools/gold_tracker.py status / is_best);
  * walk-forward: rules that were best-looking on 2000-2013 (10+ decided, hit > base,
    p < 0.10) are re-scored on 2013-2026, which did not choose them.
Writes build/pdfref/market_backtest_2000-2026_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import gzip
import html
import importlib.util
import json
import math
import pathlib
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
CACHE = OUT / "backtest" / "market_events_2000-2026.json.gz"
P0, P1 = dt.date(2000, 11, 20), dt.date(2026, 11, 20)
SPLIT = dt.date(2013, 11, 20)
FLAT = 0.5
H = 5
MARKETS = {
    "spx": dict(name="S&P 500", sym="^GSPC", file="spx_GSPC_daily_2000.csv", tz=ZoneInfo("America/New_York"), close=dt.time(16, 0)),
    "sensex": dict(name="BSE Sensex", sym="^BSESN", file="sensex_BSESN_daily_2000.csv", tz=ZoneInfo("Asia/Kolkata"), close=dt.time(15, 30)),
}


def load_tracker():
    spec = importlib.util.spec_from_file_location("gt", ROOT / "tools" / "gold_tracker.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def binom_p(k, n, p):
    if not n:
        return None
    p = min(max(p, 1e-9), 1 - 1e-9)
    lg = math.lgamma
    return min(1.0, sum(math.exp(lg(n + 1) - lg(i + 1) - lg(n - i + 1) + i * math.log(p) + (n - i) * math.log(1 - p)) for i in range(k, n + 1)))


def bh(ps):
    n = len(ps)
    order = sorted(range(n), key=lambda i: ps[i])
    q = [1.0] * n
    prev = 1.0
    for rank, i in reversed(list(enumerate(order, 1))):
        prev = min(prev, ps[i] * n / rank)
        q[i] = prev
    return q


def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


class Market:
    def __init__(self, key):
        self.key, self.cfg = key, MARKETS[key]
        rows = list(csv.DictReader(open(OUT / "backtest" / self.cfg["file"])))
        self.D = [dt.date.fromisoformat(r["date"]) for r in rows]
        self.C = [float(r["close"]) for r in rows]
        self._base = {}
        self.yend = {}
        for i, d in enumerate(self.D):
            self.yend[nov_year(d)] = i                          # last index of each Nov-Nov year

    def session_day(self, t):
        x = t.astimezone(self.cfg["tz"])
        return x.date() + (dt.timedelta(days=1) if x.time() >= self.cfg["close"] else dt.timedelta(0))

    def base(self, y, n):
        """P(up | |move| > FLAT) over n-session moves starting in Nov-Nov year y."""
        k = (y, n)
        if k not in self._base:
            ii = [i for i in range(1, len(self.D) - n) if nov_year(self.D[i]) == y]
            rs = [(self.C[i + n] / self.C[i] - 1) * 100 for i in ii]
            u, d_ = sum(r > FLAT for r in rs), sum(r < -FLAT for r in rs)
            self._base[k] = u / max(u + d_, 1)
        return self._base[k]

    def score(self, e):
        if e["day"]:
            day = dt.date.fromisoformat(e["day"])
        else:
            day = self.session_day(dt.datetime.fromisoformat(e["start"]))
        a = bisect.bisect_left(self.D, day) - 1
        if a < 1 or self.D[a] < P0 - dt.timedelta(days=7) or day > P1:
            return None
        y = nov_year(self.D[a + 1] if a + 1 < len(self.D) else self.D[a])
        b = None
        if e["end"] and not e["day"]:
            s, en = dt.datetime.fromisoformat(e["start"]), dt.datetime.fromisoformat(e["end"])
            if (en - s).days >= 3:
                b = min(bisect.bisect_left(self.D, self.session_day(en)) - 1, self.yend.get(y, len(self.D) - 1))
                if b - a < 2:
                    b = None
        if b is None:
            b = a + H
        if b >= len(self.D) or self.D[b] > P1 + dt.timedelta(days=10):
            return None
        ret = (self.C[b] / self.C[a] - 1) * 100
        return dict(entry=self.D[a], n=b - a, ret=ret, year=y)


def aggregate(rows, mk, lo=P0, hi=P1):
    """rows: [(event, score)] of one rule -> record."""
    w = f = fl = 0
    exp = 0.0
    dir_rets = []
    yrs = collections.defaultdict(lambda: [0, 0])
    for e, s in rows:
        if not (lo <= s["entry"] < hi):
            continue
        bull = e["tone"] == "Bullish"
        dret = s["ret"] if bull else -s["ret"]
        dir_rets.append(dret)
        if abs(s["ret"]) < FLAT:
            fl += 1
            continue
        pu = mk.base(s["year"], s["n"])
        exp += pu if bull else 1 - pu
        yrs[s["year"]][0] += 1
        if dret > 0:
            w += 1
            yrs[s["year"]][1] += 1
        else:
            f += 1
    dec = w + f
    hit = round(w / dec * 100) if dec else None
    base = round(exp / dec * 100) if dec else None
    avg = round(sum(dir_rets) / len(dir_rets), 2) if dir_rets else None
    verdict = "Mixed"
    if dec and hit >= base + 10 and avg > 0:
        verdict = "Worked"
    elif dec and hit <= base - 10 and avg < 0:
        verdict = "Failed"
    return dict(worked=w, failed=f, flat=fl, hit_rate=hit, base_rate=base, exp=exp, avg_dir_ret=avg, verdict=verdict,
                p_value=round(binom_p(w, dec, exp / dec), 4) if dec else None,
                years_active=len(yrs), years_right=sum(1 for v in yrs.values() if v[1] * 2 > v[0]))


def forward(best_ids, a=dt.date(2026, 11, 22), b=dt.date(2027, 12, 31)):
    """Dates of the given rules (rule ids, ::tone allowed) from a to b, detected like the history."""
    import sys
    sys.path.insert(0, str(ROOT))
    from finastro.sky import Sky
    from finastro.pdfref.detect import Ctx
    from finastro.pdfref.engine import Grid, utc
    spec = importlib.util.spec_from_file_location("bt", ROOT / "tools" / "backtest_gold.py")
    B = importlib.util.module_from_spec(spec)
    sys.modules["bt"] = B
    spec.loader.exec_module(B)
    base_ids = {i.split("::")[0] for i in best_ids}
    B.M.METAL = "general"
    B.M.EXCLUDE["general"] = set()
    B.M.EXTRA["general"] = []
    B.METAL = "general"
    keep = [r for r in B.M.C.RULES if r.id in base_ids]
    B.M.metal_rules = lambda: keep
    et = ZoneInfo("America/New_York")
    B.P0 = dt.datetime.combine(a, dt.time(0), et)
    B.P1 = dt.datetime.combine(b + dt.timedelta(days=1), dt.time(0), et)
    grid = Grid(utc(a.year - 1, 6, 1), utc(b.year + 1, 6, 30))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in range(a.year, b.year + 2) if (ROOT / "build" / f"astronomy_{y}.json").exists()]
    out = []
    for e in B.collect(ctxs):
        k = e["rule_id"] if e["rule_id"] in best_ids else f"{e['rule_id']}::{e['tone']}"
        if k not in best_ids:
            continue
        s = e["day"] or e["start"].astimezone(et).date()
        en = e["end"].astimezone(et).date() if e["end"] else s
        out.append(dict(rule_id=k, title=e["title"], tone=e["tone"], frm=str(s), to=str(en)))
    return sorted(out, key=lambda x: (x["frm"], x["title"]))


def main():
    T = load_tracker()
    with gzip.open(CACHE, "rt", encoding="utf-8") as fh:
        events = json.load(fh)
    meta = {}
    for e in events:
        meta.setdefault(e["rule_id"], dict(rule_id=e["rule_id"], title=e["title"], refs=e["refs"], verdict_text=e["verdict"], tones=collections.Counter()))
        meta[e["rule_id"]]["tones"][e["tone"]] += 1
    res = dict(markets={}, rules=[])
    per = {}
    for key in MARKETS:
        mk = Market(key)
        by_rule = collections.defaultdict(list)
        for e in events:
            if e["tone"] not in ("Bullish", "Bearish"):
                continue
            s = mk.score(e)
            if s:
                by_rule[e["rule_id"]].append((e, s))
        recs = {}
        for rid, rows in by_rule.items():
            # a rule can carry both tones (e.g. vedha benefic/malefic): score each tone separately
            for tone in ("Bullish", "Bearish"):
                rr = [(e, s) for e, s in rows if e["tone"] == tone]
                if not rr:
                    continue
                k = rid if len({e["tone"] for e, _ in rows}) == 1 else f"{rid}::{tone}"
                r = aggregate(rr, mk)
                r.update(rule_id=k, title=meta[rid]["title"] + ("" if k == rid else f" [{tone}]"), refs=meta[rid]["refs"], tone=tone,
                         h1=aggregate(rr, mk, P0, SPLIT), h2=aggregate(rr, mk, SPLIT, P1))
                r["status"] = T.status(r)
                r["best"] = T.is_best(r)
                recs[k] = r
        sel = [r for r in recs.values() if r["worked"] + r["failed"] >= 10]
        for r, q in zip(sel, bh([r["p_value"] for r in sel])):
            r["q_value"] = round(q, 3)
        # walk-forward
        picked = [r for r in recs.values() if (r["h1"]["worked"] + r["h1"]["failed"]) >= 10 and r["h1"]["hit_rate"] > r["h1"]["base_rate"]
                  and r["h1"]["p_value"] is not None and r["h1"]["p_value"] < 0.10]
        W = sum(r["h2"]["worked"] for r in picked)
        N = sum(r["h2"]["worked"] + r["h2"]["failed"] for r in picked)
        E = sum(r["h2"]["exp"] for r in picked)
        wf = dict(n_rules=len(picked), held=sum(1 for r in picked if r["h2"]["hit_rate"] is not None and r["h2"]["hit_rate"] > r["h2"]["base_rate"]),
                  worked=W, decided=N, hit=round(W / N * 100) if N else None, base=round(E / N * 100) if N else None,
                  p=round(binom_p(W, N, E / N), 4) if N else None, rules=[dict(rule_id=r["rule_id"], title=r["title"], tone=r["tone"],
                                                                                h1=f"{r['h1']['worked']}/{r['h1']['worked'] + r['h1']['failed']} ({r['h1']['hit_rate']}% vs {r['h1']['base_rate']}%)",
                                                                                h2=f"{r['h2']['worked']}/{r['h2']['worked'] + r['h2']['failed']} ({r['h2']['hit_rate']}% vs {r['h2']['base_rate']}%)",
                                                                                held=r["h2"]["hit_rate"] is not None and r["h2"]["hit_rate"] > r["h2"]["base_rate"]) for r in picked])
        all_w = sum(r["worked"] for r in recs.values())
        all_n = sum(r["worked"] + r["failed"] for r in recs.values())
        all_e = sum(r["exp"] for r in recs.values())
        res["markets"][key] = dict(name=mk.cfg["name"], symbol=mk.cfg["sym"], n_rules=len(recs), n_scored=len(sel),
                                   pooled=dict(worked=all_w, decided=all_n, hit=round(all_w / all_n * 100, 1), base=round(all_e / all_n * 100, 1)),
                                   beat_base=sum(1 for r in sel if r["hit_rate"] > r["base_rate"]), p05=sum(1 for r in sel if r["p_value"] < 0.05),
                                   p10=sum(1 for r in sel if r["p_value"] < 0.10), q10=sum(1 for r in sel if r["q_value"] < 0.10),
                                   expected_p05=round(0.05 * len(sel), 1), walk_forward=wf,
                                   status=dict(collections.Counter(r["status"].split(" (")[0] for r in recs.values())), best=sorted(r["rule_id"] for r in recs.values() if r["best"]))
        per[key] = recs
    keys = sorted(set(per["spx"]) | set(per["sensex"]))
    for k in keys:
        a, b = per["spx"].get(k), per["sensex"].get(k)
        x = a or b
        for r in (a, b):
            if r:
                r.pop("exp", None)
                for h in ("h1", "h2"):
                    r[h].pop("exp", None)
        res["rules"].append(dict(rule_id=k, title=x["title"], refs=x["refs"], tone=x["tone"], spx=a, sensex=b,
                                 both_best=bool(a and b and a["best"] and b["best"])))
    best_ids = sorted({r["rule_id"] for k in per for r in per[k].values() if r["best"]})
    res["forward"] = forward(best_ids)
    for f in res["forward"]:
        f["best_in"] = [MARKETS[k]["name"] for k in per if f["rule_id"] in per[k] and per[k][f["rule_id"]]["best"]]
    json.dump(res, open(OUT / "market_backtest_2000-2026_ET.json", "w"), indent=1, default=str)
    write(res)
    for key, m in res["markets"].items():
        print(f"{m['name']}: {m['n_rules']} rules, {m['n_scored']} with 10+ decided; pooled {m['pooled']}; beat base {m['beat_base']}; p<.05 {m['p05']} (chance {m['expected_p05']}); q<.10 {m['q10']}")
        print("   walk-forward:", {k: v for k, v in m["walk_forward"].items() if k != "rules"})
        print("   status:", m["status"])
        top = sorted([r for r in per[key].values() if r["worked"] + r["failed"] >= 15], key=lambda r: r["p_value"])[:12]
        for r in top:
            print(f"     {r['worked']}/{r['worked'] + r['failed']} {r['hit_rate']}% vs {r['base_rate']}% p {r['p_value']} q {r.get('q_value')} yrs {r['years_right']}/{r['years_active']} "
                  f"h1 {r['h1']['hit_rate']}/{r['h1']['base_rate']} h2 {r['h2']['hit_rate']}/{r['h2']['base_rate']} {r['tone']} {r['title'][:70]}")
    print("best in both:", [r["title"] for r in res["rules"] if r["both_best"]])


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]

    def rec(r):
        if not r:
            return "<td class='s'>–</td>"
        dec = r["worked"] + r["failed"]
        if not dec:
            return "<td class='s'>no decided cases</td>"
        st = r["status"]
        cls = "bullish" if st in ("Strongest", "Supported", "Consistent") else "bearish" if st == "Did not hold up" else ""
        return (f"<td class='s {cls}'><b>{r['worked']}/{dec}</b> ({r['hit_rate']}% vs {r['base_rate']}%), p {r['p_value']}"
                f"{'' if r.get('q_value') is None else ', q ' + str(r['q_value'])}, avg {r['avg_dir_ret']:+.2f}%, right {r['years_right']}/{r['years_active']} yrs"
                f"<br>2000–13: {r['h1']['hit_rate']}% vs {r['h1']['base_rate']}% · 2013–26: {r['h2']['hit_rate']}% vs {r['h2']['base_rate']}%<br><i>{html.escape(st)}</i>{' · <b>best</b>' if r['best'] else ''}</td>")

    def mtable(key, n=30):
        rs = [x for x in res["rules"] if x[key] and x[key]["worked"] + x[key]["failed"] >= 15]
        rs.sort(key=lambda x: x[key]["p_value"])
        body = "".join(f"<tr><td><b>{html.escape(x['title'])}</b><div class='s'>{html.escape('; '.join(x['refs']))}</div></td><td>{x['tone']}</td>{rec(x[key])}"
                       f"{rec(x['sensex' if key == 'spx' else 'spx'])}</tr>" for x in rs[:n])
        other = "BSE Sensex" if key == "spx" else "S&P 500"
        return (f"<div class='wrap'><table><thead><tr><th>Rule</th><th>Says</th><th>{res['markets'][key]['name']} (sorted by p)</th><th>Same rule on {other}</th></tr></thead>"
                f"<tbody>{body}</tbody></table></div>")

    summ = ""
    for key, m in res["markets"].items():
        wf = m["walk_forward"]
        summ += (f"<tr><td><b>{m['name']}</b> ({m['symbol']})</td><td class='n'>{m['n_rules']}</td><td class='n'>{m['n_scored']}</td>"
                 f"<td class='n'>{m['pooled']['hit']}% vs {m['pooled']['base']}%</td><td class='n'>{m['beat_base']} of {m['n_scored']}</td>"
                 f"<td class='n'>{m['p05']} (chance ≈ {m['expected_p05']})</td><td class='n'>{m['q10']}</td><td class='n'>{len(m['best'])}</td>"
                 f"<td class='s'>{wf['n_rules']} rules picked on 2000–13; {wf['held']} stayed above base on 2013–26; together {wf['worked']}/{wf['decided']} ({wf['hit']}% vs {wf['base']}%, p {wf['p']})</td></tr>")
    both = [x for x in res["rules"] if x["both_best"]]
    brows = "".join(f"<tr><td><b>{html.escape(x['title'])}</b><div class='s'>{html.escape('; '.join(x['refs']))}</div></td><td>{x['tone']}</td>{rec(x['spx'])}{rec(x['sensex'])}</tr>" for x in both)
    wfrows = ""
    for key, m in res["markets"].items():
        for r in m["walk_forward"]["rules"]:
            wfrows += f"<tr class='{'bullish' if r['held'] else 'bearish'}'><td>{m['name']}</td><td>{html.escape(r['title'])}</td><td>{r['tone']}</td><td class='n'>{r['h1']}</td><td class='n'>{r['h2']}</td></tr>"
    frows = "".join(f"<tr class='{'bullish' if f['tone'] == 'Bullish' else 'bearish'}'><td class='w'>{f['frm']}{'' if f['to'] == f['frm'] else ' – ' + f['to']}</td><td>{html.escape(f['title'])}</td>"
                    f"<td>{f['tone']}</td><td>{', '.join(f['best_in'])}</td></tr>" for f in res.get("forward", [])) or "<tr><td colspan='4'>none</td></tr>"
    allrows = "".join(f"<tr><td>{html.escape(x['title'])}<div class='s'>{html.escape('; '.join(x['refs']))}</div></td><td>{x['tone']}</td>{rec(x['spx'])}{rec(x['sensex'])}</tr>"
                      for x in sorted(res["rules"], key=lambda x: x["title"]))
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Market Rules Backtest</title><style>{css}</style></head><body>
<h1>Stock-market rules from the documents, tested on 26 years of the S&amp;P 500 and the BSE Sensex (20 Nov 2000 – 20 Nov 2026)</h1>
<p class="m">Every general-market rule in TA, KD and the 2026 document that can be computed, scored like the gold rules: entry at the last close before the event in the exchange's own time,
windows to their last close, instants on 5 sessions, FLAT under 0.5%, each rule compared with how often the index went that way over the same horizon in the same Nov–Nov year (the base).
With several hundred rules tested, about 5% will show p &lt; 0.05 by luck alone, so the false-discovery-rate q and the walk-forward column are the honest guides.</p>
<h2>Summary</h2>
<div class="wrap"><table><thead><tr><th>Index</th><th>Rules with events</th><th>10+ decided</th><th>All rule calls together</th><th>Beat their base</th><th>p &lt; 0.05</th><th>q &lt; 0.10</th><th>“Best” (tracker rule)</th><th>Walk-forward</th></tr></thead><tbody>{summ}</tbody></table></div>
<h2>Rules that are “best” in both markets</h2>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Says</th><th>S&amp;P 500</th><th>BSE Sensex</th></tr></thead><tbody>{brows or "<tr><td colspan='4'>none</td></tr>"}</tbody></table></div>
<h2>S&amp;P 500: top 30 rules by p (15+ decided)</h2>
{mtable('spx')}
<h2>BSE Sensex: top 30 rules by p (15+ decided)</h2>
{mtable('sensex')}
<h2>Dates of the “best” rules, 22 Nov 2026 – 31 Dec 2027 (US Eastern dates)</h2>
<div class="wrap"><table><thead><tr><th>Dates</th><th>Rule</th><th>Says</th><th>Best in</th></tr></thead><tbody>{frows}</tbody></table></div>
<h2>Walk-forward detail (picked on 2000–2013, scored on 2013–2026)</h2>
<div class="wrap"><table><thead><tr><th>Index</th><th>Rule</th><th>Says</th><th>2000–2013</th><th>2013–2026</th></tr></thead><tbody>{wfrows}</tbody></table></div>
<h2>Every rule</h2>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Says</th><th>S&amp;P 500</th><th>BSE Sensex</th></tr></thead><tbody>{allrows}</tbody></table></div>
<p class="s">Generated by tools/backtest_market.py from the events of tools/market_events.py. Mixed / Neutral rules are not scored.</p></body></html>"""
    (OUT / "market_backtest_2000-2026_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
