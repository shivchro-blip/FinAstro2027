"""Narrow the slow-planet watch windows to days, using fast-moving planets.

    python tools/fast_trigger_analysis.py [start] [end] [--metal silver]     # silver: ±3.5% days, silver_* inputs/outputs

Idea under test (Kindle Ch.3/Ch.6; TA p.59-60; KD p.82/p.129): slow planets set the
condition, fast planets (Moon, Mercury, Venus, Sun, and Mars as the medium mover) fire
the move. Step 1, 2000-2026: take every trading day inside a historical watch window
(the same definition as tools/big_move_forward.py: 3+ big-move leads at once, or one
lead that held in both halves on Vedic grahas only, full Moon excepted). For each fast
factor on the day itself, compare the number of +/-2% days with the number expected
from the same years' window days (Poisson p, Benjamini-Hochberg q), and repeat for
2000-2013 and 2013-2026. The same factor outside the windows is shown too, so a trigger
that only matters inside windows can be told apart from one that matters everywhere.
Step 2: for every day of the forward watch items (gold_outlook), list the fast factors
present and rank the days by the factors that passed (lift > 1 in both halves, p < 0.10).
Writes build/pdfref/gold_fast_triggers_{start}_to_{end}_ET.{html,json,ics}.
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import importlib.util
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "tools"))
import metal_cfg as MC  # noqa: E402
from finastro.sky import parse  # noqa: E402
from finastro.pdfref.detect import aspects  # noqa: E402
from finastro.pdfref.engine import snapshot  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
SPLIT = dt.date(2013, 11, 20)
SLOW = ("Saturn", "Rahu", "Jupiter", "Mars", "Sun")          # Moon opposite Rahu = Moon with Ketu, so Ketu is not listed separately


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def session_day(t):
    x = t.astimezone(ET)
    return x.date() + (dt.timedelta(days=1) if x.hour >= 17 else dt.timedelta(0))


def fast_events(years):
    """session date -> fast-planet event names (exact in that session)."""
    ev = collections.defaultdict(set)
    for y in years:
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            ec, b, fam = r["event_class"], r["bodies"], r.get("rule_family", "")
            if not b:
                continue
            p = b[0]
            nm = None
            if ec == "sign_ingress" and p in ("Moon", "Mercury", "Venus", "Sun", "Mars"):
                nm = f"{p} changes sign"
            elif ec == "nakshatra_ingress" and p in ("Sun", "Mars", "Venus"):
                nm = f"{p} changes nakshatra"
            elif ec == "station" and p in ("Mercury", "Venus", "Mars"):
                nm = f"{p} stations {'retrograde' if fam.endswith('_R') else 'direct'}"
            elif ec == "combustion" and p in ("Mercury", "Venus", "Mars"):
                nm = f"{p} {'combustion begins' if fam.endswith('combust') else 'leaves combustion'}"
            elif ec == "speed_overtake" and p == "Mercury":
                nm = "Mercury overtakes Venus in speed (Mercury manifestation, KD)"
            elif ec == "conjunction" and set(b[:2]) == {"Sun", "Mercury"}:
                nm = "Sun-Mercury exact conjunction (KD turning date)"
            elif ec == "conjunction" and set(b[:2]) == {"Mercury", "Venus"}:
                nm = "Mercury-Venus exact conjunction"
            elif ec == "conjunction" and set(b[:2]) == {"Sun", "Venus"}:
                nm = "Sun-Venus exact conjunction"
            elif ec == "conjunction" and "Mars" in b[:2] and set(b[:2]) & {"Sun", "Mercury", "Venus"}:
                nm = "Mars exact conjunction with Sun / Mercury / Venus"
            elif ec == "lunation":
                nm = "Lunation day: " + fam.split("/")[-1].replace("_", " ")
            elif ec == "apsis" and p == "Moon" and "perigee" in (fam + r.get("id", "")).lower():
                nm = "Moon at perigee"
            if nm:
                ev[session_day(parse(r["time"]["t_start_utc"]))].add(nm)
    return ev


def moon_states(day):
    s = snapshot(dt.datetime(day.year, day.month, day.day, 12, tzinfo=ET).astimezone(dt.timezone.utc))
    f = set()
    for p in SLOW:
        if s["Moon"].sign_i == s[p].sign_i:
            f.add(f"Moon with {p}" + (" (= Moon opposite Ketu)" if p == "Rahu" else ""))
        elif s.sign_dist("Moon", p) == 7:
            f.add(f"Moon opposite {p}" + (" (= Moon with Ketu)" if p == "Rahu" else ""))
    for p in ("Saturn", "Mars", "Jupiter"):                       # Rahu's only aspect is the 7th = "Moon opposite Rahu"
        if s["Moon"].sign_i != s[p].sign_i and aspects(s, p, "Moon"):
            f.add(f"Moon aspected by {p}")
    if s.sign_dist("Saturn", "Moon") == 12:
        f.add("Moon 12th from Saturn (Shani-Chandra dwidwadash, KD p.94)")
    if s.sign_dist("Saturn", "Moon") == 2:
        f.add("Moon 2nd from Saturn")
    if s.sign_dist("Moon", "Saturn") in (6, 8):
        f.add("Moon-Saturn 6/8 (shadashtak)")
    t = s.tithi
    if t >= 23 or t <= 1:
        f.add("Moon waning past Ashtami to Amavasya (malefic Moon)")
    if s["Mercury"].sign_i == s["Moon"].sign_i:
        f.add("Moon with Mercury")
    if s["Mercury"].retro:
        f.add("Mercury retrograde")
    if s["Venus"].retro:
        f.add("Venus retrograde")
    return f


def day_fast(day, ev):
    f = set(moon_states(day))
    for k in (-1, 0, 1):
        for nm in ev.get(day + dt.timedelta(days=k), ()):
            if nm == "Moon changes sign":
                if k == 0:
                    f.add(nm)
            else:
                f.add(nm + " (±1 day)")
    if any(("±1 day" in x) and not x.startswith("Lunation") for x in f):
        f.add("Any Mercury / Venus / Sun / Mars event (±1 day)")
    return f


def table(days, M, min_days=25):
    rows, _, _ = M.factor_table([dict(date=x["date"], ret=x["ret"], f=x["fast"]) for x in days], min_days)
    return {r["factor"]: r for r in rows}


def n_passed(win, M):
    t, t1, t2 = table(win, M), table([x for x in win if x["date"] < SPLIT], M, 12), table([x for x in win if x["date"] >= SPLIT], M, 12)
    return sum(1 for f, r in t.items() if r["lift"] and r["lift"] > 1 and r["p"] < 0.10 and (t1.get(f) or {}).get("lift", 0) and t1[f]["lift"] > 1
               and (t2.get(f) or {}).get("lift", 0) and t2[f]["lift"] > 1)


def permutation_check(win, M, n=100):
    """How many factors 'pass' when the day's returns are shuffled within each year (no link to the sky)."""
    import random
    rng = random.Random(7)
    by_y = collections.defaultdict(list)
    for x in win:
        by_y[x["date"].year].append(x)
    counts = []
    for _ in range(n):
        sh = []
        for v in by_y.values():
            rets = [x["ret"] for x in v]
            rng.shuffle(rets)
            sh += [dict(date=x["date"], ret=r, fast=x["fast"]) for x, r in zip(v, rets)]
        counts.append(n_passed(sh, M))
    counts.sort()
    return dict(n=n, mean=round(sum(counts) / n, 1), p90=counts[int(0.9 * n)], max=counts[-1])


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 22)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2027, 12, 31)
    M = load(ROOT / "tools" / "big_move_analysis.py", "bma")
    watch = json.load(open(OUT / f"{MC.METAL}_big_move_watch_{a}_to_{b}_ET.json"))
    lead = {L["factor"]: L for L in watch["leads"]}
    strong = {f for f, L in lead.items() if L["both_halves"] and not L["outer"] and f != "Event: full moon"}

    hist = M.build_days()
    ev = fast_events(range(2000, b.year + 2))
    win, out = [], []
    for x in hist:
        on = [f for f in x["f"] if f in lead]
        x["fast"] = day_fast(x["date"], ev)
        (win if (len(on) >= 3 or any(f in strong for f in on)) else out).append(x)
    full_in = table(win, M)
    h1 = table([x for x in win if x["date"] < SPLIT], M, 12)
    h2 = table([x for x in win if x["date"] >= SPLIT], M, 12)
    full_out = table(out, M)
    big_in = sum(abs(x["ret"]) >= MC.TH for x in win)
    big_out = sum(abs(x["ret"]) >= MC.TH for x in out)
    facs = []
    for f, r in full_in.items():
        o = full_out.get(f)
        r1, r2 = h1.get(f), h2.get(f)
        facs.append(dict(factor=f, days=r["days"], big=r["big"], exp=r["exp_big"], lift=r["lift"], p=r["p"], q=r["q"], episodes=r["episodes"],
                         up=r["up"], lift_up=r["lift_up"], p_up=r["p_up"], down=r["down"], lift_down=r["lift_down"], p_down=r["p_down"], up_share=r["up_share"],
                         lift_h1=r1["lift"] if r1 else None, lift_h2=r2["lift"] if r2 else None, lift_out=o["lift"] if o else None, p_out=o["p"] if o else None))
    for x in facs:
        x["passed"] = bool(x["lift"] and x["lift"] > 1 and x["p"] < 0.10 and (x["lift_h1"] or 0) > 1 and (x["lift_h2"] or 0) > 1)
        base_up = sum(1 for x in win if x["ret"] >= MC.TH) / max(big_in, 1) * 100
        us = x["up_share"] or 0
        x["lean"] = ("up" if us >= base_up + 10 and x["p_up"] < 0.10 else "down" if us <= base_up - 10 and x["p_down"] < 0.10 else "either")
    facs.sort(key=lambda x: x["p"])
    passed = {x["factor"]: x for x in facs if x["passed"]}
    perm = permutation_check(win, M)

    # forward: every day of the outlook's watch items (stretches, single leads, Venus dates +/-3 days)
    outl = json.load(open(OUT / f"{MC.METAL}_outlook_{a}_to_{b}_ET.json"))
    fwd_items = []
    for it in outl["items"]:
        if it["kind"] == "Best rule":
            continue
        f0, t0 = dt.date.fromisoformat(it["frm"]), dt.date.fromisoformat(it["to"])
        if it["kind"].startswith("Venus"):
            if "rises" in it["title"]:
                f0, t0 = f0 - dt.timedelta(days=3), f0 + dt.timedelta(days=3)
            else:
                f0, t0 = f0 - dt.timedelta(days=3), f0 + dt.timedelta(days=3)     # start of the combustion
        fwd_items.append(dict(item=it["title"], kind=it["kind"], lean=it["lean"], frm=f0, to=t0))
    days = []
    for it in fwd_items:
        d = it["frm"]
        while d <= it["to"]:
            if d.weekday() < 5:
                f = day_fast(d, ev)
                hit = sorted((p for p in f if p in passed), key=lambda p: -passed[p]["lift"])
                score = round(sum(passed[p]["lift"] - 1 for p in hit), 2)
                days.append(dict(date=d.isoformat(), item=it["item"], kind=it["kind"], window_lean=it["lean"], fast=sorted(f), triggers=hit, score=score,
                                 trigger_lean=[passed[p]["lean"] for p in hit]))
            d += dt.timedelta(days=1)
    # one best day (or tie) per item
    picks = []
    for it in fwd_items:
        ds = [x for x in days if x["item"] == it["item"] and it["frm"].isoformat() <= x["date"] <= it["to"].isoformat()]
        if not ds:
            continue
        top = max(x["score"] for x in ds)
        best = [x for x in ds if x["score"] == top and top > 0]
        picks.append(dict(item=it["item"], kind=it["kind"], window_lean=it["lean"], frm=it["frm"].isoformat(), to=it["to"].isoformat(),
                          best=[dict(date=x["date"], triggers=x["triggers"], score=x["score"]) for x in best]))
    res = dict(start=a.isoformat(), end=b.isoformat(), perm=perm, n_win=len(win), big_win=big_in, n_out=len(out), big_out=big_out, factors=facs,
               passed=list(passed), days=days, picks=picks)
    stem = f"{MC.METAL}_fast_triggers_{a}_to_{b}_ET"
    json.dump(res, open(OUT / f"{stem}.json", "w"), indent=1, default=str)
    (OUT / f"{stem}.html").write_text(page(res), encoding="utf-8")
    (OUT / f"{stem}.ics").write_text(ics(res), encoding="utf-8")
    print("permutation:", perm)
    print(f"window days {len(win)} ({big_in} big, {big_in / len(win) * 100:.1f}%), other days {len(out)} ({big_out} big, {big_out / len(out) * 100:.1f}%)")
    for x in facs[:22]:
        print(f"  {'*' if x['passed'] else ' '} x{x['lift']:.2f} {x['big']:3d}/{x['exp']:5.1f} p {x['p']:.3f} q {x['q']:.2f} h1 {x['lift_h1']} h2 {x['lift_h2']} out x{x['lift_out']} lean {x['lean']}  {x['factor']}")
    for p in picks:
        print(f"  {p['frm']}..{p['to']} {p['item'][:60]}: " + "; ".join(f"{b['date']} ({', '.join(b['triggers'])})" for b in p["best"]))


def page(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    frows = "".join(
        f"<tr class='{'bullish' if x['passed'] else ''}'><td>{html.escape(x['factor'])}</td><td class='n'>{x['days']}</td><td class='n'>{x['big']} / {x['exp']}</td><td class='n'><b>×{x['lift']:.2f}</b></td>"
        f"<td class='n'>{x['p']:.3f}</td><td class='n'>{x['q']:.2f}</td><td class='n'>{x['episodes']}</td><td class='n'>×{x['lift_h1']}</td><td class='n'>×{x['lift_h2']}</td>"
        f"<td class='n'>{'–' if x['lift_out'] is None else '×' + str(x['lift_out'])}</td><td class='n'>{x['up_share']}%</td><td>{'yes' if x['passed'] else ''}</td></tr>" for x in res["factors"])
    cls = {"up": "bullish", "down": "bearish"}

    def fmt(d):
        return dt.date.fromisoformat(d).strftime("%a %d %b %Y")
    prows = "".join(
        f"<tr class='{cls.get(p['window_lean'], 'mixed')}'><td class='w'>{fmt(p['frm'])} – {fmt(p['to'])}</td><td>{html.escape(p['item'])}</td><td>{p['window_lean']}</td>"
        f"<td class='w'><b>{'<br>'.join(fmt(b['date']) for b in p['best']) or 'no tested trigger in the window'}</b></td>"
        f"<td class='s'>{html.escape(' | '.join(', '.join(b['triggers']) for b in p['best'])) or '-'}</td></tr>" for p in res["picks"])
    drows = "".join(
        f"<tr class='{'bullish' if x['score'] > 0 else ''}'><td class='w'>{fmt(x['date'])}</td><td class='s'>{html.escape(x['item'])}</td><td class='n'>{x['score']}</td>"
        f"<td class='s'><b>{html.escape('; '.join(x['triggers']) or '-')}</b></td><td class='s'>{html.escape('; '.join(f for f in x['fast'] if f not in x['triggers']))}</td></tr>" for x in res["days"])
    n_pass = len(res["passed"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{MC.NAME} Fast Triggers</title><style>{css}</style></head><body>
<h1>{MC.NAME}: narrowing the watch windows with fast planets, {fmt(res['start'])} – {fmt(res['end'])}</h1>
<p class="m">Slow-planet conditions set the window; does a Moon, Mercury, Venus, Sun or Mars trigger pick the day? Tested on {MC.METAL} (±{MC.TH:g}% days) 2000–2026: <b>{res['n_win']}</b> trading days fell inside a watch window
({res['big_win']} big days, {res['big_win'] / res['n_win'] * 100:.1f}%) against {res['n_out']} days outside ({res['big_out']} big, {res['big_out'] / res['n_out'] * 100:.1f}%).
For each fast factor on the day, the big days inside windows are compared with the number expected from the same years' window days; it <b>passes</b> if lift &gt; 1 with p &lt; 0.10 and lift &gt; 1 in both 2000–2013 and 2013–2026.
<b>{n_pass}</b> of {len(res['factors'])} factors passed. With the returns shuffled within each year ({res['perm']['n']} times, so no link to the sky), {res['perm']['mean']} factors pass on average (90th percentile {res['perm']['p90']}, maximum {res['perm']['max']}); none survives the false-discovery-rate correction, so the narrowed dates are best guesses inside the windows, not calls.
The “outside” column shows the same factor's lift on days outside any window: a trigger that only works inside windows is what the slow-sets-fast-fires idea predicts.</p>
<h2>Narrowed dates</h2>
<div class="wrap"><table><thead><tr><th>Window</th><th>Why the window</th><th>Window lean</th><th>Best day(s) by tested triggers</th><th>Triggers that day</th></tr></thead><tbody>{prows}</tbody></table></div>
<h2>Fast factors inside the windows, 2000–2026</h2>
<div class="wrap"><table><thead><tr><th>Fast factor (on the day)</th><th>Window days</th><th>Big days / expected</th><th>Lift</th><th>p</th><th>q</th><th>Episodes</th><th>2000–13</th><th>2013–26</th><th>Outside windows</th><th>Up share</th><th>Passed</th></tr></thead><tbody>{frows}</tbody></table></div>
<h2>Every weekday in the forward windows</h2>
<div class="wrap"><table><thead><tr><th>Day</th><th>Window</th><th>Score</th><th>Tested triggers</th><th>Other fast factors</th></tr></thead><tbody>{drows}</tbody></table></div>
<p class="s">Generated by tools/fast_trigger_analysis.py. Windows: tools/big_move_forward.py and tools/gold_outlook.py (--metal {MC.METAL}).</p></body></html>"""


def ics(res):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def esc(t):
        return t.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//finastro2027//{MC.METAL} fast triggers//EN", "CALSCALE:GREGORIAN", f"X-WR-CALNAME:{MC.NAME} narrowed watch days"]
    for p in res["picks"]:
        for b in p["best"]:
            d = dt.date.fromisoformat(b["date"])
            lines += ["BEGIN:VEVENT", f"UID:fast-{MC.METAL}-{b['date']}-{abs(hash(p['item'])) % 10**6}@finastro2027", f"DTSTAMP:{now}", f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
                      f"DTEND;VALUE=DATE:{d + dt.timedelta(days=1):%Y%m%d}", f"SUMMARY:{esc(MC.NAME + ' watch day (' + p['window_lean'] + '): ' + ', '.join(b['triggers'])[:100])}",
                      f"DESCRIPTION:{esc('Window ' + p['frm'] + ' to ' + p['to'] + ': ' + p['item'] + '. Fast triggers tested inside windows 2000-2026; none passes FDR.')}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


if __name__ == "__main__":
    main()
