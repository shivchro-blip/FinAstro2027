"""Backtest of the gold signal table's High / Moderate / Low strengths, 2000-2026.

    python tools/test_signal_table.py [--metal silver]

Silver source points: +2 retrograde Mercury or Jupiter, +1 Moon and Mercury alone in a sign
(both from the silver 26-year backtest windows), +1 Venus combust in East; big days are ±3.5%.

The scoring of tools/gold_signal_table.py is applied to every past trading day:
  bullish  +1 U2 Mercury in the Sun's sign           +2 Venus combust in East (TA S18)
           +1 watch window leaning up                 +1 fast-planet trigger day in an up window
  bearish  +1 watch window leaning down               +1 fast-planet trigger day in a down window
           +1 Sun in a Saturn nakshatra (Pushya, Anuradha, Uttara Bhadrapada) with Mars on
              the Sun (with or aspecting) - the general form of the Nov 2026 phase
Net > 0 bullish, < 0 bearish, 0 inside a window = volatile; strength 3+ High, 2 Moderate, 1 Low.
Consecutive weekdays with the same signal and strength form one episode (as the rows of
the table). Each episode is scored like a rule (PROJECT_KNOWLEDGE section 6): entry =
last close before the first day; 3+ sessions scored to the close of the last day, shorter
ones on the 5-session move; FLAT under 0.5%; base = same-horizon moves in the same Nov-Nov
year; one-sided binomial p. Volatile episodes are scored on whether a +/-2% day fell inside.

Two runs:
  in-sample 2000-2026  - the watch leads and fast triggers exactly as used for the table
                         (picked on 2000-2026, so this run flatters them);
  walk-forward 2013-26 - watch leads and fast triggers re-picked on 2000-2013 only, then
                         scored on 2013-2026, which they never saw. U2, Venus and the Saturn-
                         nakshatra rule are source rules and stay as they are.
Writes build/pdfref/signal_table_test_2000-2026_ET.{html,json}.
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import importlib.util
import json
import math
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "tools"))
import metal_cfg as MC  # noqa: E402
from finastro.pdfref.detect import aspects  # noqa: E402
from finastro.pdfref.engine import snapshot  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
SPLIT = dt.date(2013, 11, 20)
OUTER = ("Uranus", "Neptune", "Pluto")
SAT_NAK = ("Pushya", "Anuradha", "Uttara Bhadrapada")
FLAT = 0.5
STEM = OUT / ("signal_table_test_2000-2026_ET" if MC.METAL == "gold" else f"{MC.METAL}_signal_table_test_2000-2026_ET")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def binom_p(k, n, p):
    if not n:
        return None
    p = min(max(p, 1e-9), 1 - 1e-9)
    lg = math.lgamma
    return min(1.0, sum(math.exp(lg(n + 1) - lg(i + 1) - lg(n - i + 1) + i * math.log(p) + (n - i) * math.log(1 - p)) for i in range(k, n + 1)))


def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


def lead_set(rows, M, both=None):
    """factor -> dict(lean, strong) from big_move_analysis.leads(rows); `both` = factors that held in both halves (or None)."""
    out = {}
    for r, side in M.leads(rows):
        out.setdefault(r["factor"], set()).add(side)
    res = {}
    for f, sides in out.items():
        lean = "up" if "up" in sides and "down" not in sides else "down" if "down" in sides and "up" not in sides else "either"
        outer = any(p in f for p in OUTER)
        strong = not outer and f != "Event: full moon" and (both is None or f in both)
        res[f] = dict(lean=lean, strong=strong)
    return res


def classify(days, leads, fast_ok, use_source=True):
    for x in days:
        on = [f for f in x["f"] if f in leads]
        n_strong = sum(1 for f in on if leads[f]["strong"])
        in_win = len(on) >= 3 or n_strong >= 1
        up = sum(1 for f in on if leads[f]["lean"] == "up")
        dn = sum(1 for f in on if leads[f]["lean"] == "down")
        wlean = ("up" if up > dn else "down" if dn > up else "either") if in_win else None
        bull, bear = (x["src_bull"], x["src_bear"]) if use_source else (0, 0)
        vol = False
        if in_win:
            for k in (1, 1 if any(f in fast_ok for f in x["fast"]) else 0):
                if not k:
                    continue
                if wlean == "up":
                    bull += 1
                elif wlean == "down":
                    bear += 1
                else:
                    vol = True
        net = bull - bear
        x["sig"] = "Bullish" if net > 0 else "Bearish" if net < 0 else ("Volatile" if vol else None)
        x["st"] = None if x["sig"] is None else "High" if abs(net) >= 3 else "Moderate" if abs(net) == 2 else "Low"
    return days


def episodes(days):
    eps = []
    for i, x in enumerate(days):
        if x["sig"] is None:
            continue
        if eps and eps[-1]["sig"] == x["sig"] and eps[-1]["st"] == x["st"] and eps[-1]["last_i"] == i - 1:
            eps[-1]["last_i"] = i
        else:
            eps.append(dict(sig=x["sig"], st=x["st"], first_i=i, last_i=i))
    return eps


def evaluate(days, D, C, lo, hi):
    idx = {d: i for i, d in enumerate(D)}
    # base: P(up | |move| > FLAT) per year and horizon; big-day share per year
    base = collections.defaultdict(dict)
    bigshare = {}
    for y in range(lo.year - 1, hi.year + 1):
        ii = [i for i in range(1, len(D) - 60) if nov_year(D[i]) == y]
        if not ii:
            continue
        for n in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 40, 60):
            rs = [(C[i + n] / C[i] - 1) * 100 for i in ii]
            u, d_ = sum(r > FLAT for r in rs), sum(r < -FLAT for r in rs)
            base[y][n] = u / max(u + d_, 1)
        bigshare[y] = sum(abs(C[i] / C[i - 1] - 1) >= MC.TH / 100 for i in ii) / len(ii)
    sel = [x for x in days if lo <= x["date"] < hi]
    eps = episodes(sel)
    res = collections.defaultdict(lambda: dict(n=0, w=0, f=0, exp=0.0, rets=[], big=0, big_exp=0.0, days=0, d_w=0, d_f=0, d_exp=0.0))
    for e in eps:
        k = (e["sig"], e["st"])
        r = res[k]
        r["n"] += 1
        d0, d1 = sel[e["first_i"]]["date"], sel[e["last_i"]]["date"]
        a = idx[d0] - 1
        b = idx[d1]
        span = b - a
        if span < 3:
            b, span = a + 5, 5
        if b >= len(D):
            continue
        y = nov_year(d0)
        if e["sig"] == "Volatile":
            hit = any(abs(C[i] / C[i - 1] - 1) >= MC.TH / 100 for i in range(a + 1, idx[d1] + 1))
            nd = idx[d1] - a
            r["big"] += hit
            r["big_exp"] += 1 - (1 - bigshare.get(y, 0.07)) ** nd
            continue
        ret = (C[b] / C[a] - 1) * 100
        r["rets"].append(ret)
        if abs(ret) < FLAT:
            continue
        hz = min(base[y], key=lambda n: abs(n - span))
        pu = base[y][hz]
        p_dir = pu if e["sig"] == "Bullish" else 1 - pu
        r["exp"] += p_dir
        if (ret > 0) == (e["sig"] == "Bullish"):
            r["w"] += 1
        else:
            r["f"] += 1
    # daily view: next-5-session move from each signal day's prior close
    for x in sel:
        if x["sig"] in (None, "Volatile"):
            continue
        a = idx[x["date"]] - 1
        if a + 5 >= len(D):
            continue
        ret = (C[a + 5] / C[a] - 1) * 100
        r = res[(x["sig"], x["st"])]
        r["days"] += 1
        if abs(ret) < FLAT:
            continue
        pu = base[nov_year(x["date"])][5]
        r["d_exp"] += pu if x["sig"] == "Bullish" else 1 - pu
        if (ret > 0) == (x["sig"] == "Bullish"):
            r["d_w"] += 1
        else:
            r["d_f"] += 1
    out = []
    for sig in ("Bullish", "Bearish", "Volatile"):
        for st in ("High", "Moderate", "Low"):
            r = res.get((sig, st))
            if not r or not r["n"]:
                continue
            dec = r["w"] + r["f"]
            ddec = r["d_w"] + r["d_f"]
            row = dict(signal=sig, strength=st, episodes=r["n"], days=r["days"])
            if sig == "Volatile":
                row.update(big=r["big"], big_exp=round(r["big_exp"], 1))
            else:
                b = r["exp"] / dec if dec else None
                db = r["d_exp"] / ddec if ddec else None
                row.update(worked=r["w"], decided=dec, hit=round(r["w"] / dec * 100) if dec else None, base=round(b * 100) if b else None,
                           p=round(binom_p(r["w"], dec, b), 3) if dec else None, avg=round(sum(r["rets"]) / len(r["rets"]), 2) if r["rets"] else None,
                           d_hit=round(r["d_w"] / ddec * 100) if ddec else None, d_base=round(db * 100) if db else None)
            out.append(row)
    return out


def main():
    M = load(ROOT / "tools" / "big_move_analysis.py", "bma")
    F = load(ROOT / "tools" / "fast_trigger_analysis.py", "fta")
    V = load(ROOT / "tools" / "test_venus_visibility.py", "tvv")
    days = M.build_days()
    ev = F.fast_events(range(2000, 2028))
    venus = set()
    for e in V.events():
        if e["rule_id"] == "ta_s18_venus_combust_east" and e["end"]:
            d = e["start"].date()
            while d <= e["end"].date():
                venus.add(d)
                d += dt.timedelta(days=1)
    windows = collections.defaultdict(set)
    if MC.METAL == "silver":
        bt = json.load(open(OUT / "silver_backtest_2000-11-20_to_2026-11-20_ET.json"))
        for e in bt["events"]:
            if e["rule_id"] in ("ta_s35a01_retro_mercury_or_jupiter", "ta_s35a17b_moon_mercury_alone"):
                d0 = dt.datetime.fromisoformat(e["start"]).astimezone(ET).date() if e["start"] else dt.date.fromisoformat(e["day"][:10])
                d1 = dt.datetime.fromisoformat(e["end"]).astimezone(ET).date() if e["end"] else d0
                d = d0
                while d <= d1:
                    windows[e["rule_id"]].add(d)
                    d += dt.timedelta(days=1)
    for x in days:
        x["fast"] = F.day_fast(x["date"], ev)
        if MC.METAL == "gold":
            s = snapshot(dt.datetime(x["date"].year, x["date"].month, x["date"].day, 12, tzinfo=ET).astimezone(dt.timezone.utc))
            u2 = s["Mercury"].sign_i == s["Sun"].sign_i
            satnak = s["Sun"].nak in SAT_NAK and (s["Mars"].sign_i == s["Sun"].sign_i or aspects(s, "Mars", "Sun"))
            x["src_bull"] = int(u2) + 2 * (x["date"] in venus)
            x["src_bear"] = int(satnak)
        else:
            x["src_bull"] = 2 * (x["date"] in windows["ta_s35a01_retro_mercury_or_jupiter"]) + (x["date"] in windows["ta_s35a17b_moon_mercury_alone"]) + (x["date"] in venus)
            x["src_bear"] = 0
    D, C = V.prices(MC.METAL)

    # in-sample: the table's own leads and triggers
    watch = json.load(open(OUT / f"{MC.METAL}_big_move_watch_2026-11-22_to_2027-12-31_ET.json"))
    fast = json.load(open(OUT / f"{MC.METAL}_fast_triggers_2026-11-22_to_2027-12-31_ET.json"))
    leads_full = {L["factor"]: dict(lean=L["lean"], strong=L["both_halves"] and not L["outer"] and L["factor"] != "Event: full moon") for L in watch["leads"]}
    classify(days, leads_full, set(fast["passed"]))
    recent = [dict(date=str(x["date"]), sig=x["sig"], st=x["st"], ret=round(x["ret"], 3)) for x in days if x["date"] >= dt.date(2026, 8, 1)]
    ins = evaluate(days, D, C, dt.date(2000, 11, 20), dt.date(2026, 11, 20))
    ins_h2 = evaluate(days, D, C, SPLIT, dt.date(2026, 11, 20))
    share_full = collections.Counter((x["sig"], x["st"]) for x in days)

    # walk-forward: re-pick leads and triggers on 2000-2013 only
    h1 = [x for x in days if x["date"] < SPLIT]
    rows1, _, _ = M.factor_table(h1, 15)
    leads1 = lead_set(rows1, M)
    win1 = []
    for x in h1:
        on = [f for f in x["f"] if f in leads1]
        if len(on) >= 3 or any(leads1[f]["strong"] for f in on):
            win1.append(x)
    t1 = F.table(win1, M, 12)
    fast1 = {f for f, r in t1.items() if r["lift"] and r["lift"] > 1 and r["p"] < 0.10 and r["episodes"] >= 5}
    days_wf = [dict(x) for x in days]
    classify(days_wf, leads1, fast1)
    wf = evaluate(days_wf, D, C, SPLIT, dt.date(2026, 11, 20))
    # full daily label history (in-sample definitions and walk-forward re-pick) for tools/combined_probability.py
    with gzip.open(OUT / "backtest" / f"{MC.METAL}_label_history.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(dict(in_sample={str(x["date"]): [x["sig"], x["st"]] for x in days if x["sig"]},
                       walk_forward={str(x["date"]): [x["sig"], x["st"]] for x in days_wf if x["sig"]}), fh)
    # source rules only (no data-picked parts): U2, Venus, Saturn-nakshatra
    days_src = [dict(x) for x in days]
    classify(days_src, {}, set())
    src = evaluate(days_src, D, C, dt.date(2000, 11, 20), dt.date(2026, 11, 20))

    def pooled(rows):
        out = {}
        for sig in ("Bullish", "Bearish"):
            hm = [r for r in rows if r["signal"] == sig and r["strength"] in ("High", "Moderate") and r["decided"]]
            if not hm:
                continue
            w, n = sum(r["worked"] for r in hm), sum(r["decided"] for r in hm)
            b = sum(r["base"] / 100 * r["decided"] for r in hm) / n
            out[sig] = dict(worked=w, decided=n, hit=round(w / n * 100), base=round(b * 100), p=round(binom_p(w, n, b), 3))
        return out
    res = dict(recent=recent, pooled={k: pooled(v) for k, v in (("in_sample", ins), ("walk_forward", wf), ("source_only", src))}, in_sample=ins, in_sample_2013=ins_h2, walk_forward=wf, source_only=src, n_leads_h1=len(leads1), fast_h1=sorted(fast1),
               day_share={f"{k[0]} {k[1]}": v for k, v in share_full.items() if k[0]})
    json.dump(res, open(STEM.with_suffix(".json"), "w"), indent=1, default=str)
    write(res)
    for name in ("in_sample", "in_sample_2013", "walk_forward", "source_only"):
        print(name)
        for r in res[name]:
            if r["signal"] == "Volatile":
                print(f"   {r['signal']:8s} {r['strength']:8s} eps {r['episodes']:4d}  big inside {r['big']}/{r['big_exp']}")
            else:
                print(f"   {r['signal']:8s} {r['strength']:8s} eps {r['episodes']:4d}  {r['worked']}/{r['decided']} hit {r['hit']}% base {r['base']}% p {r['p']} avg {r['avg']}  daily {r['d_hit']}% vs {r['d_base']}% ({r['days']} d)")
    print("h1 leads", len(leads1), "fast h1", sorted(fast1))
    print("pooled High+Moderate", res["pooled"])


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]

    def tbl(rows):
        body = ""
        for r in rows:
            if r["signal"] == "Volatile":
                body += (f"<tr class='mixed'><td>{r['signal']}</td><td>{r['strength']}</td><td class='n'>{r['episodes']}</td><td colspan='4'>a ±{MC.TH:g}% day inside the episode: <b>{r['big']}</b> "
                         f"vs {r['big_exp']} expected from the same years</td><td></td></tr>")
                continue
            avg = "" if r["avg"] is None else f"{r['avg']:+.2f}%"
            good = r["hit"] is not None and r["base"] is not None and r["hit"] >= r["base"] + 10
            bad = r["hit"] is not None and r["base"] is not None and r["hit"] <= r["base"] - 10
            body += (f"<tr class='{'bullish' if good else 'bearish' if bad else ''}'><td>{r['signal']}</td><td><b>{r['strength']}</b></td><td class='n'>{r['episodes']}</td>"
                     f"<td class='n'><b>{r['worked']}/{r['decided']}</b></td><td class='n'><b>{r['hit']}%</b> vs {r['base']}%</td><td class='n'>{r['p']}</td>"
                     f"<td class='n'>{avg}</td><td class='n'>{r['d_hit']}% vs {r['d_base']}% ({r['days']} days)</td></tr>")
        return ("<div class='wrap'><table><thead><tr><th>Signal</th><th>Strength</th><th>Episodes</th><th>Worked / decided</th><th>Hit vs base</th><th>p</th><th>Average move</th>"
                f"<th>Daily view: next 5 sessions right vs base</th></tr></thead><tbody>{body}</tbody></table></div>")
    SRC_TEXT = ("Only U2 (+1 bullish), Venus combust in East (+2 bullish) and Sun in a Saturn nakshatra with Mars on the Sun (+1 bearish)." if MC.METAL == "gold" else
                "Only retrograde Mercury or Jupiter (+2 bullish), Moon and Mercury alone in a sign (+1) and Venus combust in East (+1).")

    def pool(p):
        return "; ".join(f"{k} {v['worked']}/{v['decided']} ({v['hit']}% vs {v['base']}%, p {v['p']})" for k, v in p.items()) or "-"
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Signal Table Test</title><style>{css}</style></head><body>
<h1>Does the {MC.METAL} signal table's High / Moderate / Low hold up? Backtest 2000–2026</h1>
<p class="m">The table's scoring (tools/gold_signal_table.py) applied to every past trading day; consecutive days with the same signal and strength form one episode, scored like a rule
(entry = last close before; 3+ sessions to the last close, otherwise 5 sessions; base = same horizon, same Nov–Nov year). If the strengths mean something, High should beat Moderate and Moderate should beat Low, and all should beat their base.</p>
<h2>1. Walk-forward, 2013–2026 (the honest test)</h2>
<p class="m">Watch leads ({res['n_leads_h1']}) and fast triggers ({', '.join(res['fast_h1']) or 'none'}) re-picked on 2000–2013 only, then scored on 2013–2026. U2, Venus combust in East and the Saturn-nakshatra rule are source rules and stay as they are.</p>
{tbl(res['walk_forward'])}
<p class="m">High and Moderate together: {pool(res['pooled']['walk_forward'])}</p>
<h2>2. Source rules only, 2000–2026 (no data-picked parts)</h2>
<p class="m">{SRC_TEXT}</p>
{tbl(res['source_only'])}
<p class="m">High and Moderate together: {pool(res['pooled']['source_only'])}</p>
<h2>3. In-sample, 2000–2026 (flattering)</h2>
<p class="m">The table exactly as built; its watch leads and fast triggers were picked on these same years, so this run overstates them.</p>
{tbl(res['in_sample'])}
<p class="m">High and Moderate together: {pool(res['pooled']['in_sample'])}</p>
<h2>3b. In-sample, 2013–2026 only</h2>
{tbl(res['in_sample_2013'])}
<p class="s">Generated by tools/test_signal_table.py. p values for episodes are one-sided binomial against the same-year base; the daily view counts overlapping days and is shown for reference only.</p></body></html>"""
    (STEM.with_suffix(".html")).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
