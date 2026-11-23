"""Backtest the original calendar's own rule layer (the 2026 document's catalogue B, its
instrument configuration groups and sub-tables; finastro/verdicts.py) over 2000-2026.

    python tools/calendar_rules_backtest.py             # generate (cached) and score
    python tools/calendar_rules_backtest.py --gen 2015  # one year (used internally)

The calendar layer is generated for every civil year 2000-2026 from that year's astronomy
layer, exactly as build/calendar_2027.json is for 2027 (finastro.verdicts.build_verdicts with
the year set), and cached in build/pdfref/backtest/calendar_verdicts/ (git-ignored).
Instruments scored: SPX -> S&P 500; NIFTY -> BSE Sensex (the Nifty series on Yahoo starts in
2007; the Sensex is the 26-year Indian proxy); GC -> COMEX gold; SI -> COMEX silver.
NDX / BANKNIFTY / MCX duplicates, USDINR, SUGAR and CL are not scored (no 26-year series here).
Each rule's day rows are merged into episodes (consecutive venue days with the same verdict).
Directional verdicts (Bullish / Bearish wording) are scored as in PROJECT_KNOWLEDGE section 6:
entry = last close before the first day; episodes of 3+ days to the close of their last day,
shorter ones on the 5-session move; FLAT under 0.5%; same-year base; binomial p; BH q.
Rules the calendar prints with no direction (condition-only, turning points, volatility) are
scored on volatility instead: did a big day (±2%; silver ±3.5%) fall inside the episode, against
the chance of one in the same number of sessions that year (Poisson p, BH q).
Writes build/pdfref/calendar_rules_backtest_2000-2026_ET.{html,json}.
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import html
import importlib.util
import json
import math
import pathlib
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
CACHE = OUT / "backtest" / "calendar_verdicts"
YEARS = range(2000, 2027)
P0, P1 = dt.date(2000, 11, 20), dt.date(2026, 11, 20)
SPLIT = dt.date(2013, 11, 20)
INSTR = {"SPX": "spx", "NIFTY": "sensex", "GC": "gold", "SI": "silver"}
TH = {"spx": 2.0, "sensex": 2.0, "gold": 2.0, "silver": 3.5}


def gen(year):
    sys.path.insert(0, str(ROOT))
    import finastro.config as cfg
    cfg.CONF["year"] = year
    cfg.YEAR = year
    from finastro.sky import Sky
    from finastro.verdicts import build_verdicts
    v = build_verdicts(Sky.load(ROOT / "build" / f"astronomy_{year}.json"))
    rows = [dict(rule_id=x.rule_id, instrument=x.instrument, date=x.civil_date.isoformat(), verdict=x.verdict_text,
                 provenance=x.provenance, significance=x.significance) for x in v if x.instrument in INSTR]
    CACHE.mkdir(parents=True, exist_ok=True)
    with gzip.open(CACHE / f"{year}.json.gz", "wt", encoding="utf-8") as f:
        json.dump(rows, f)
    print(year, len(rows))


def tone(t):
    if not t:
        return None
    s = t.lower().replace("\n", ". ").split(". ")[0]          # the first sentence carries the call (e.g. Pradosh)
    if "then bearish" in s or "then bullish" in s or "dicey" in s:
        return "Mixed"
    bull = any(w in s for w in ("bullish", "optimism", "rise", "positive"))
    bear = any(w in s for w in ("bearish", "negative", "pessimism", "fall"))
    if bull and not bear:
        return "Bullish"
    if bear and not bull:
        return "Bearish"
    if "top or bottom" in s or "turning" in s or "volatil" in s:
        return "Volatile"
    return "Mixed"


def poisson_sf(k, lam):
    if k <= 0:
        return 1.0
    if lam > 300:
        return 0.5 * math.erfc((k - 0.5 - lam) / math.sqrt(lam) / math.sqrt(2))
    term = math.exp(-lam)
    cdf = term
    for i in range(1, k):
        term *= lam / i
        cdf += term
    return max(0.0, 1 - cdf)


def main():
    if "--gen" in sys.argv:
        gen(int(sys.argv[sys.argv.index("--gen") + 1]))
        return
    for y in YEARS:
        if not (CACHE / f"{y}.json.gz").exists():
            subprocess.run([sys.executable, __file__, "--gen", str(y)], cwd=ROOT, check=True)
    spec = importlib.util.spec_from_file_location("bm", ROOT / "tools" / "backtest_market.py")
    BM = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(BM)
    BM.MARKETS["gold"] = dict(name="COMEX gold", sym="GC=F", file="gold_GC_F_daily_2000.csv", tz=ZoneInfo("America/New_York"), close=dt.time(17, 0))
    BM.MARKETS["silver"] = dict(name="COMEX silver", sym="SI=F", file="silver_SI_F_daily_2000.csv", tz=ZoneInfo("America/New_York"), close=dt.time(17, 0))
    spec = importlib.util.spec_from_file_location("gt", ROOT / "tools" / "gold_tracker.py")
    T = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(T)

    rows = []
    for y in YEARS:
        with gzip.open(CACHE / f"{y}.json.gz", "rt", encoding="utf-8") as f:
            rows += json.load(f)
    # episodes per (rule, instrument, verdict)
    by = collections.defaultdict(list)
    meta = {}
    for r in rows:
        by[(r["rule_id"], r["instrument"], r["verdict"])].append(dt.date.fromisoformat(r["date"]))
        meta[r["rule_id"]] = r["provenance"]
    res = dict(markets={}, rules=[])
    per = {}
    for ins, key in INSTR.items():
        mk = BM.Market(key)
        idx = {d: i for i, d in enumerate(mk.D)}
        big = [abs(mk.C[i] / mk.C[i - 1] - 1) * 100 >= TH[key] if i else False for i in range(len(mk.D))]
        bigshare = {}
        for i, d in enumerate(mk.D):
            y = BM.nov_year(d)
            a = bigshare.setdefault(y, [0, 0])
            a[0] += big[i]
            a[1] += 1
        recs = {}
        for (rid, i_, verdict), days in by.items():
            if i_ != ins:
                continue
            days = sorted(set(days))
            eps, cur = [], None
            for d in days:
                if cur and (d - cur[1]).days <= 1:
                    cur[1] = d
                else:
                    cur = [d, d]
                    eps.append(cur)
            t = tone(verdict)
            k = rid if t else rid + "::condition"
            r = recs.setdefault(k, dict(rule_id=rid, key=k, provenance=meta[rid], verdict=verdict, tone=t or "Condition only", episodes=[]))
            for e in eps:
                if P0 <= e[0] < P1:
                    r["episodes"].append(e)
        out = {}
        for k, r in recs.items():
            if r["tone"] in ("Bullish", "Bearish"):
                pairs = []
                for d0, d1 in r["episodes"]:
                    e = dict(tone=r["tone"], day=d0.isoformat(), start=None, end=None)
                    if (d1 - d0).days >= 2:
                        e = dict(tone=r["tone"], day=None, start=dt.datetime.combine(d0, dt.time(0), mk.cfg["tz"]).isoformat(),
                                 end=dt.datetime.combine(d1, mk.cfg["close"], mk.cfg["tz"]).isoformat())
                    s = mk.score(e)
                    if s:
                        pairs.append((e, s))
                a = BM.aggregate(pairs, mk)
                a.update(h1=BM.aggregate(pairs, mk, P0, SPLIT), h2=BM.aggregate(pairs, mk, SPLIT, P1), n_episodes=len(r["episodes"]))
                a["status"] = T.status(dict(a, tone=r["tone"], verdict=a["verdict"]))
                a["best"] = T.is_best(a)
                for h in ("h1", "h2"):
                    a[h].pop("exp", None)
                out[k] = dict(r, kind="direction", **{x: a[x] for x in a if x != "exp"}, exp=a["exp"])
            else:
                obs = exp = 0.0
                n = 0
                for d0, d1 in r["episodes"]:
                    ii = [idx[d] for d in (d0 + dt.timedelta(days=j) for j in range((d1 - d0).days + 1)) if d in idx]
                    if not ii:
                        continue
                    y = BM.nov_year(mk.D[ii[0]])
                    p = bigshare[y][0] / bigshare[y][1]
                    obs += any(big[i] for i in ii)
                    exp += 1 - (1 - p) ** len(ii)
                    n += 1
                out[k] = dict(r, kind="volatility", n_episodes=n, big=int(obs), big_exp=round(exp, 1),
                              lift=round(obs / exp, 2) if exp else None, p_value=poisson_sf(int(obs), exp) if exp else None)
            out[k].pop("episodes", None)
        d_sel = [r for r in out.values() if r["kind"] == "direction" and r["worked"] + r["failed"] >= 10]
        for r, q in zip(d_sel, BM.bh([r["p_value"] for r in d_sel])):
            r["q_value"] = round(q, 3)
        v_sel = [r for r in out.values() if r["kind"] == "volatility" and r["p_value"] is not None and r["n_episodes"] >= 10]
        for r, q in zip(v_sel, BM.bh([r["p_value"] for r in v_sel])):
            r["q_value"] = round(q, 3)
        W = sum(r["worked"] for r in d_sel)
        N = sum(r["worked"] + r["failed"] for r in d_sel)
        E = sum(r["exp"] for r in d_sel)
        res["markets"][key] = dict(name=mk.cfg["name"], instrument=ins, n_direction=len(d_sel), n_volatility=len(v_sel),
                                   pooled=dict(worked=W, decided=N, hit=round(W / N * 100, 1) if N else None, base=round(E / N * 100, 1) if N else None,
                                               p=round(BM.binom_p(W, N, E / N), 4) if N else None),
                                   p05=sum(1 for r in d_sel if r["p_value"] < 0.05), q10=sum(1 for r in d_sel if r["q_value"] < 0.10),
                                   v_q10=sum(1 for r in v_sel if r["q_value"] < 0.10), best=sorted(r["key"] for r in d_sel if r["best"]))
        for r in out.values():
            r.pop("exp", None)
        per[key] = out
    for k in sorted({k for v in per.values() for k in v}):
        x = next(v[k] for v in per.values() if k in v)
        res["rules"].append(dict(key=k, rule_id=x["rule_id"], provenance=x["provenance"], verdict=x["verdict"], tone=x["tone"], kind=x["kind"],
                                 **{m: per[m].get(k) for m in per}))
    cal = json.load(open(ROOT / "build" / "calendar_2027.json", encoding="utf-8"))["rows"]
    good = {(x["key"], m) for x in res["rules"] for m in per if x.get(m) and x[m]["kind"] == "direction" and (x[m].get("q_value") or 1) < 0.10
            or (x.get(m) and x[m]["kind"] == "direction" and x[m]["p_value"] is not None and x[m]["p_value"] < 0.05
                and x[m]["h1"]["hit_rate"] is not None and x[m]["h1"]["hit_rate"] > x[m]["h1"]["base_rate"]
                and x[m]["h2"]["hit_rate"] is not None and x[m]["h2"]["hit_rate"] > x[m]["h2"]["base_rate"])}
    inv = {v: k for k, v in INSTR.items()}
    fwd = collections.defaultdict(set)
    for r in cal:
        if r["row_kind"] == "verdict" and (r["event"], INSTR.get(r["instrument"])) in good:
            fwd[(r["event"], r["instrument"])].add(dt.datetime.strptime(r["date"], "%d-%b-%Y").date())
    res["forward_2027"] = []
    for (rid, ins), ds in sorted(fwd.items()):
        ds = sorted(ds)
        eps, cur = [], None
        for d in ds:
            if cur and (d - cur[1]).days <= 1:
                cur[1] = d
            else:
                cur = [d, d]
                eps.append(cur)
        res["forward_2027"].append(dict(rule_id=rid, instrument=ins, market=res["markets"][INSTR[ins]]["name"], windows=[[str(a), str(b)] for a, b in eps]))
    del inv
    json.dump(res, open(OUT / "calendar_rules_backtest_2000-2026_ET.json", "w"), indent=1, default=str)
    write(res)
    for key, m in res["markets"].items():
        print(f"{m['name']} ({m['instrument']}): direction rules {m['n_direction']} pooled {m['pooled']} p<.05 {m['p05']} q<.10 {m['q10']}; volatility rules {m['n_volatility']} q<.10 {m['v_q10']}; best {m['best']}")
        top = sorted([r for r in per[key].values() if r["kind"] == "direction" and r["worked"] + r["failed"] >= 10], key=lambda r: r["p_value"])[:8]
        for r in top:
            print(f"   {r['worked']}/{r['worked'] + r['failed']} {r['hit_rate']}% vs {r['base_rate']}% p {r['p_value']} q {r.get('q_value')} h1 {r['h1']['hit_rate']}/{r['h1']['base_rate']} h2 {r['h2']['hit_rate']}/{r['h2']['base_rate']} {r['tone']} {r['rule_id']}")
        topv = sorted([r for r in per[key].values() if r["kind"] == "volatility" and r["p_value"] is not None and r["n_episodes"] >= 10], key=lambda r: r["p_value"])[:6]
        for r in topv:
            print(f"   VOL {r['big']}/{r['big_exp']} x{r['lift']} p {r['p_value']:.4f} q {r.get('q_value')} eps {r['n_episodes']} {r['key']}")


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    mk = list(res["markets"])

    def cell(r):
        if not r:
            return "<td class='s'>–</td>"
        if r["kind"] == "volatility":
            if not r.get("n_episodes"):
                return "<td class='s'>no episodes</td>"
            good = (r.get("q_value") or 1) < 0.10 and (r["lift"] or 0) > 1
            return (f"<td class='s {'bullish' if good else ''}'>big day in <b>{r['big']}</b> of {r['n_episodes']} episodes vs {r['big_exp']} expected "
                    f"(×{r['lift']}, p {r['p_value']:.3f}{'' if r.get('q_value') is None else ', q ' + str(r['q_value'])})</td>")
        dec = r["worked"] + r["failed"]
        if not dec:
            return "<td class='s'>no decided cases</td>"
        st = r["status"]
        cls = "bullish" if st in ("Strongest", "Supported", "Consistent") else "bearish" if st == "Did not hold up" else ""
        return (f"<td class='s {cls}'><b>{r['worked']}/{dec}</b> ({r['hit_rate']}% vs {r['base_rate']}%), p {r['p_value']}"
                f"{'' if r.get('q_value') is None else ', q ' + str(r['q_value'])}<br>2000–13 {r['h1']['hit_rate']}% vs {r['h1']['base_rate']}% · 2013–26 {r['h2']['hit_rate']}% vs {r['h2']['base_rate']}%"
                f"<br><i>{html.escape(st)}</i>{' · <b>best</b>' if r['best'] else ''}</td>")
    summ = "".join(f"<tr><td><b>{m['name']}</b> ({m['instrument']} rows)</td><td class='n'>{m['n_direction']}</td><td class='n'>{m['pooled']['hit']}% vs {m['pooled']['base']}% (p {m['pooled']['p']})</td>"
                   f"<td class='n'>{m['p05']}</td><td class='n'>{m['q10']}</td><td class='n'>{m['n_volatility']}</td><td class='n'>{m['v_q10']}</td><td class='s'>{html.escape(', '.join(m['best']) or '-')}</td></tr>"
                   for m in res["markets"].values())

    def key_p(x):
        ps = [x[m]["p_value"] for m in mk if x.get(m) and x[m].get("p_value") is not None]
        return min(ps) if ps else 1
    body = "".join(f"<tr><td><b>{html.escape(x['rule_id'])}</b><div class='s'>{html.escape(x['provenance'] or '')}</div></td><td class='s'>{html.escape((x['verdict'] or 'condition only (no verdict printed)')[:160])}</td>"
                   f"<td>{x['tone']}</td>{''.join(cell(x.get(m)) for m in mk)}</tr>" for x in sorted(res["rules"], key=key_p))
    frows = "".join(f"<tr><td><b>{html.escape(f['rule_id'])}</b></td><td>{f['market']}</td><td class='s'>{'; '.join(a if a == b else a + ' – ' + b for a, b in f['windows'])}</td></tr>"
                    for f in res.get("forward_2027", [])) or "<tr><td colspan='3'>none</td></tr>"
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Calendar Rules Backtest</title><style>{css}</style></head><body>
<h1>The 2027 calendar's own rules (2026 document: catalogue B, configuration groups, sub-tables), backtested 2000–2026</h1>
<p class="m">The calendar layer (finastro/verdicts.py) was generated for every year 2000–2026 exactly as for 2027 and scored on the instruments it names: SPX rows on the S&amp;P 500, NIFTY rows on the BSE Sensex (26-year proxy),
GC on COMEX gold, SI on COMEX silver. Rows with a printed direction are scored on direction (same method as every other backtest); rows printed with no direction — Bhadra, Panchak, Amavasya/Purnima, eclipses, turning dates and the like —
are scored on whether a big day (±2%, silver ±3.5%) fell inside the episode, against the chance of one over the same number of sessions in that year.</p>
<h2>Summary</h2>
<div class="wrap"><table><thead><tr><th>Market</th><th>Direction rules (10+ decided)</th><th>All their calls together</th><th>p &lt; 0.05</th><th>q &lt; 0.10</th><th>Volatility rules (10+ episodes)</th><th>q &lt; 0.10</th><th>“Best” by the tracker rule</th></tr></thead><tbody>{summ}</tbody></table></div>
<h2>2027 dates of the rules that held (p &lt; 0.05 and above base in both halves, or q &lt; 0.10)</h2>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Market</th><th>2027 windows (calendar_2027.json)</th></tr></thead><tbody>{frows}</tbody></table></div>
<h2>Every rule (sorted by its smallest p)</h2>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Calendar verdict</th><th>Scored as</th>{''.join(f'<th>{res["markets"][m]["name"]}</th>' for m in mk)}</tr></thead><tbody>{body}</tbody></table></div>
<p class="s">Generated by tools/calendar_rules_backtest.py.</p></body></html>"""
    (OUT / "calendar_rules_backtest_2000-2026_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
