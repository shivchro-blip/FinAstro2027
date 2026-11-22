"""Which planetary conditions surround gold's big daily moves (|close-to-close| >= 2%), 2000-2026?

    python tools/big_move_analysis.py [threshold_pct]

For every COMEX gold (GC=F) trading day with a move of at least the threshold, the sky
within +/- 3 calendar days (events) and on the day (states) is compared with all trading
days. Factors:
  events within +/- 3 days (astronomy layer): new / full Moon, quarter Moons, solar and
    lunar eclipses, stations (per planet, direct / retrograde), sign ingresses (per
    planet), nakshatra ingresses (slow planets), combustion begins, conjunctions and
    oppositions (per pair);
  states on the day (12:00 ET): each planet retrograde; the Sun's nakshatra lord and
    sign; the Moon's paksha; Jupiter / Saturn / Rahu / Mars signs; each planet with or
    aspecting the Sun (whole-sign drishti); Mars-Saturn, Jupiter-Saturn, Saturn-Rahu,
    Mars-Rahu relations;
  every gold rule active on the day (26-year backtest events, instants counted +/- 3 days).
Big-move days cluster in volatile years, so each factor's EXPECTED count is stratified by
year: sum over years of (big days that year x share of that year's days with the factor).
Lift = observed / expected; p = Poisson upper tail; q = Benjamini-Hochberg over all
factors. Direction: share of up moves among big days with the factor vs all big days.
Writes build/pdfref/gold_big_moves_2000-2026_ET.{html,json}.
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
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import parse  # noqa: E402
from finastro.pdfref.detect import NAK_LORD, aspects  # noqa: E402
from finastro.pdfref.engine import snapshot  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
PL = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
RETRO = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")


def load_prices():
    rows = list(csv.DictReader(open(OUT / "backtest" / "gold_GC_F_daily_2000.csv")))
    D = [dt.date.fromisoformat(r["date"]) for r in rows]
    C = [float(r["close"]) for r in rows]
    return D, C


def load_events():
    ev = collections.defaultdict(set)          # ET date -> set of factor names
    seen = set()
    for y in range(2000, 2027):
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            ec, b = r["event_class"], r["bodies"]
            fam = r.get("rule_family", "")
            if not b:
                continue
            name = None
            if ec == "lunation":
                name = "Event: " + fam.split("/")[-1].replace("_", " ")
            elif ec == "eclipse":
                name = "Event: " + ("lunar" if fam.endswith("lunar") else "solar") + " eclipse"
            elif ec == "station" and b[0] != "Moon":
                name = f"Event: {b[0]} stations {'retrograde' if fam.endswith('_R') else 'direct'}"
            elif ec == "sign_ingress" and b[0] not in ("Moon",):
                name = f"Event: {b[0]} changes sign"
            elif ec == "nakshatra_ingress" and b[0] in ("Mars", "Jupiter", "Saturn", "Rahu"):
                name = f"Event: {b[0]} changes nakshatra"
            elif ec == "combustion":
                name = f"Event: {b[0]} combustion begins"
            elif ec in ("conjunction", "opposition") and len(b) > 1 and all(x in PL + ("Moon", "Uranus", "Neptune", "Pluto") for x in b) and "Moon" not in b:
                name = f"Event: {b[0]}-{b[1]} {ec}"
            if not name:
                continue
            t = parse(r["time"]["t_start_utc"])
            k = (name, t.replace(minute=0, second=0))
            if k in seen:
                continue
            seen.add(k)
            ev[t.astimezone(ET).date()].add(name)
    return ev


def states(day):
    s = snapshot(dt.datetime(day.year, day.month, day.day, 12, tzinfo=ET).astimezone(dt.timezone.utc))
    f = set()
    for p in RETRO:
        if s[p].retro:
            f.add(f"State: {p} retrograde")
    f.add(f"State: Sun in a {NAK_LORD[s['Sun'].nak_i]} nakshatra")
    f.add(f"State: Sun in {s['Sun'].sign}")
    f.add(f"State: Moon {s.paksha} paksha")
    for p in ("Jupiter", "Saturn", "Rahu", "Mars"):
        f.add(f"State: {p} in {s[p].sign}")
    for p in ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"):
        if s[p].sign_i == s["Sun"].sign_i:
            f.add(f"State: {p} with the Sun")
        elif p != "Ketu" and aspects(s, p, "Sun"):
            f.add(f"State: {p} aspects the Sun")
    for a, b in (("Mars", "Saturn"), ("Jupiter", "Saturn"), ("Saturn", "Rahu"), ("Mars", "Rahu"), ("Jupiter", "Rahu"), ("Mars", "Jupiter")):
        if s[a].sign_i == s[b].sign_i:
            f.add(f"State: {a} with {b}")
        elif aspects(s, a, b) or aspects(s, b, a):
            f.add(f"State: {a}-{b} in aspect")
    return f


def rule_days(D):
    d = json.load(open(OUT / "gold_backtest_2000-11-20_to_2026-11-20_ET.json"))
    act = collections.defaultdict(set)
    for e in d["events"]:
        if e.get("tone") not in ("Bullish", "Bearish", "Mixed"):
            continue
        s = dt.date.fromisoformat((e["day"] or e["start"])[:10])
        en = dt.date.fromisoformat(e["end"][:10]) if e.get("end") else None
        if en is None or (en - s).days < 1:
            s, en = s - dt.timedelta(days=3), s + dt.timedelta(days=3)
        nm = f"Rule: {e['title']} [{e['tone']}]"
        i = bisect.bisect_left(D, s)
        while i < len(D) and D[i] <= en:
            act[D[i]].add(nm)
            i += 1
    return act


def poisson_sf(k, lam):
    """P(X >= k) for X ~ Poisson(lam)."""
    if k <= 0:
        return 1.0
    term = math.exp(-lam)
    cdf = term
    for i in range(1, k):
        term *= lam / i
        cdf += term
    return max(0.0, 1 - cdf)


def bh(ps):
    n = len(ps)
    order = sorted(range(n), key=lambda i: ps[i])
    q = [0.0] * n
    prev = 1.0
    for rank, i in reversed(list(enumerate(order, 1))):
        prev = min(prev, ps[i] * n / rank)
        q[i] = prev
    return q


def main():
    D, C = load_prices()
    ev = load_events()
    rules = rule_days(D)
    days = []
    for i in range(1, len(D)):
        if D[i] < dt.date(2000, 11, 20) or D[i] > dt.date(2026, 11, 20):
            continue
        r = (C[i] / C[i - 1] - 1) * 100
        f = set(states(D[i]))
        for k in range(-3, 4):
            f |= ev.get(D[i] + dt.timedelta(days=k), set())
        f |= rules.get(D[i], set())
        days.append(dict(date=D[i], ret=r, f=f))
    big = [x for x in days if abs(x["ret"]) >= TH]
    up = [x for x in big if x["ret"] > 0]
    years = collections.defaultdict(list)
    for x in days:
        years[x["date"].year].append(x)
    allf = sorted(set().union(*(x["f"] for x in days)))
    share = {y: collections.Counter(f for x in v for f in x["f"]) for y, v in years.items()}
    nday = {y: len(v) for y, v in years.items()}
    def expected(sub, fac):
        cnt = collections.Counter(x["date"].year for x in sub)
        return sum(n * share[y][fac] / nday[y] for y, n in cnt.items())
    rows = []
    up_share_all = len(up) / len(big)
    for fac in allf:
        tot = sum(1 for x in days if fac in x["f"])
        if tot < 30:
            continue
        ob = [x for x in big if fac in x["f"]]
        ep, last = 0, None
        for x in ob:
            if last is None or (x["date"] - last).days > 10:
                ep += 1
            last = x["date"]
        o_up = sum(1 for x in ob if x["ret"] > 0)
        ex_b = expected(big, fac)
        ex_u = expected(up, fac)
        ex_d = expected([x for x in big if x["ret"] < 0], fac)
        rows.append(dict(factor=fac, episodes=ep, days=tot, share=round(tot / len(days) * 100, 1), big=len(ob), exp_big=round(ex_b, 1), lift=round(len(ob) / ex_b, 2) if ex_b else None,
                         p=poisson_sf(len(ob), ex_b), up=o_up, exp_up=round(ex_u, 1), lift_up=round(o_up / ex_u, 2) if ex_u else None, p_up=poisson_sf(o_up, ex_u),
                         down=len(ob) - o_up, exp_down=round(ex_d, 1), lift_down=round((len(ob) - o_up) / ex_d, 2) if ex_d else None, p_down=poisson_sf(len(ob) - o_up, ex_d),
                         up_share=round(o_up / len(ob) * 100, 1) if ob else None))
    for key in ("p", "p_up", "p_down"):
        qs = bh([r[key] for r in rows])
        for r, q in zip(rows, qs):
            r["q" + key[1:]] = q
    res = dict(threshold=TH, n_days=len(days), n_big=len(big), n_up=len(up), n_down=len(big) - len(up), up_share=round(up_share_all * 100, 1),
               factors=rows, big_days=[dict(date=x["date"].isoformat(), ret=round(x["ret"], 2), events=sorted(f for f in x["f"] if f.startswith("Event")),
                                            rules=sorted(f for f in x["f"] if f.startswith("Rule"))) for x in big])
    json.dump(res, open(OUT / "gold_big_moves_2000-2026_ET.json", "w"), indent=1, default=str)
    write(res)
    top = sorted(rows, key=lambda r: r["p"])[:25]
    print(f"{len(big)} big days ({len(up)} up, {len(big) - len(up)} down) of {len(days)}")
    for r in top:
        print(f"  lift {r['lift']:.2f}  {r['big']:3d}/{r['exp_big']:6.1f}  p {r['p']:.4f} q {r['q']:.3f}  up {r['up_share']}%  {r['factor']}")
    print("UP")
    for r in sorted(rows, key=lambda r: r["p_up"])[:12]:
        print(f"  lift {r['lift_up']:.2f}  {r['up']:3d}/{r['exp_up']:6.1f}  p {r['p_up']:.4f} q {r['q_up']:.3f}  {r['factor']}")
    print("DOWN")
    for r in sorted(rows, key=lambda r: r["p_down"])[:12]:
        print(f"  lift {r['lift_down']:.2f}  {r['down']:3d}/{r['exp_down']:6.1f}  p {r['p_down']:.4f} q {r['q_down']:.3f}  {r['factor']}")


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    rows = res["factors"]

    def table(key, lk, ok, ek, qk, title, n):
        sel = sorted([r for r in rows if r[lk] is not None], key=lambda r: r[key])[:n]
        body = "".join(
            f"<tr class='{'bullish' if r[qk] < 0.10 and r[lk] > 1 else 'mixed' if r[key] < 0.05 and r[lk] > 1 else ''}'><td>{html.escape(r['factor'])}</td><td class='n'>{r['share']}%</td>"
            f"<td class='n'>{r[ok]}</td><td class='n'>{r['episodes']}</td><td class='n'>{r[ek]}</td><td class='n'><b>×{r[lk]:.2f}</b></td><td class='n'>{r[key]:.4f}</td><td class='n'>{r[qk]:.3f}</td>"
            f"<td class='n'>{'' if r['up_share'] is None else str(r['up_share']) + '%'}</td></tr>" for r in sel)
        return (f"<h3>{title}</h3><div class='wrap'><table><thead><tr><th>Factor</th><th>Share of all days</th><th>Observed</th><th>Separate episodes (any big day, &gt;10 days apart)</th><th>Expected (same years)</th><th>Lift</th><th>p</th><th>q (FDR)</th><th>Up share among its big days</th></tr></thead>"
                f"<tbody>{body}</tbody></table></div>")
    sig = [r for r in rows if r["q"] < 0.10 and r["lift"] > 1]
    sig_u = [r for r in rows if r["q_up"] < 0.10 and r["lift_up"] > 1]
    sig_d = [r for r in rows if r["q_down"] < 0.10 and r["lift_down"] > 1]
    bd = "".join(f"<tr class='{'bullish' if x['ret'] > 0 else 'bearish'}'><td class='w'>{x['date']}</td><td class='n'><b>{x['ret']:+.2f}%</b></td><td class='s'>{html.escape('; '.join(e.replace('Event: ', '') for e in x['events']) or '-')}</td>"
                 f"<td class='s'>{html.escape('; '.join(r.replace('Rule: ', '') for r in x['rules'])[:600] or '-')}</td></tr>" for x in sorted(res["big_days"], key=lambda x: x["date"], reverse=True))
    def names(lst, lk):
        return "; ".join(f"{r['factor']} (×{r[lk]:.2f})" for r in sorted(lst, key=lambda r: -r[lk])) or "none"
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gold Big Moves</title><style>{css}</style></head><body>
<h1>Gold's big daily moves (±{res['threshold']:.0f}% or more), 2000–2026: what was in the sky ±3 days</h1>
<p class="m">COMEX GC=F, 20 Nov 2000 – 20 Nov 2026: <b>{res['n_big']}</b> days with a close-to-close move of {res['threshold']:.0f}% or more out of {res['n_days']} ({res['n_up']} up, {res['n_down']} down; {res['up_share']}% up).
For each factor, the number of big days on which it was present (events within ±3 calendar days; states on the day; gold rules active) is compared with the number <b>expected from the same years</b> (big moves cluster in volatile years, so a slow planet that happened to sit in one sign during 2008 or 2013 is not credited). Lift = observed ÷ expected; p = Poisson; q = false-discovery-rate correction over all {len(rows)} factors tested — only q &lt; 0.10 should be read as a finding. Big days come in bursts (e.g. March 2020, January 2026), so the episode column shows how many separate occasions stand behind each count; a lift carried by two or three episodes is weaker than the p-value suggests.</p>
<h2>Result</h2>
<ul class="m"><li><b>Any big move (q &lt; 0.10):</b> {html.escape(names(sig, 'lift'))}</li>
<li><b>Big up moves (q &lt; 0.10):</b> {html.escape(names(sig_u, 'lift_up'))}</li>
<li><b>Big down moves (q &lt; 0.10):</b> {html.escape(names(sig_d, 'lift_down'))}</li></ul>
<h2>Top factors</h2>
{table('p', 'lift', 'big', 'exp_big', 'q', 'Any big move (±)', 30)}
{table('p_up', 'lift_up', 'up', 'exp_up', 'q_up', 'Big UP moves', 20)}
{table('p_down', 'lift_down', 'down', 'exp_down', 'q_down', 'Big DOWN moves', 20)}
<h2>Every big day (newest first) with the events of ±3 days and the gold rules active</h2>
<div class="wrap"><table><thead><tr><th>Date</th><th>Move</th><th>Events within ±3 days</th><th>Gold rules active</th></tr></thead><tbody>{bd}</tbody></table></div>
<p class="s">Generated by tools/big_move_analysis.py.</p></body></html>"""
    (OUT / "gold_big_moves_2000-2026_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
