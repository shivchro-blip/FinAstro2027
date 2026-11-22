"""Deep gold analysis for a date range: every gold rule, transit and aspect, day by day.

    python tools/gold_deep_analysis.py                       # 22 Nov - 31 Dec 2026
    python tools/gold_deep_analysis.py 2026-11-22 2026-12-31

Combines, for each day of the range (US Eastern):
  * every gold rule window (the gold report's rule set, tools/backtest_gold.py collect()),
    each weighted by its 26-year record (build/pdfref/gold_backtest_2000-11-20_to_2026-11-20_ET.json):
    tier A = Strongest / Supported / Consistent, B = at chance / inconclusive / too few,
    C = did not hold up;
  * transits from the astronomy layer (sign and nakshatra ingresses, stations,
    conjunctions, oppositions, combustion, lunations, eclipses);
  * whole-sign aspects between the planets (project drishti) that begin or end, with
    the aspects on the Sun (gold's significator in the user's notes) in full;
  * Financial Astrology Model v1.0 (Brihat Samhita Ch.41, Shadbala, Ashtakavarga);
  * gold's own record over the same calendar stretch in 2000-2025 (seasonality).
Writes build/pdfref/gold_deep_<start>_to_<end>_ET.{html,json}; a hand-written analysis in
build/pdfref/gold_deep_<start>_to_<end>_ET_notes.md, if present, is rendered at the top.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import html
import importlib.util
import json
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky, parse  # noqa: E402
from finastro.pdfref.detect import Ctx, aspects  # noqa: E402
from finastro.pdfref.engine import Grid, name, snapshot, spans, utc  # noqa: E402
from finastro.pdfref import bs41_model as BM  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
PLANETS = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
KEEP = {"sign_ingress", "nakshatra_ingress", "station", "conjunction", "opposition", "combustion", "lunation", "eclipse", "speed_crossing"}
SLOWISH = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto")


def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def et(t, fmt="%a %d %b %H:%M"):
    x = t.astimezone(ET)
    return f"{x:{fmt}} {x.tzname()}"


def tier(st):
    if st in ("Strongest", "Supported", "Consistent"):
        return "A"
    if st == "Did not hold up":
        return "C"
    return "B"


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 22)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2026, 12, 31)
    P0 = dt.datetime.combine(a, dt.time(0), ET)
    P1 = dt.datetime.combine(b + dt.timedelta(days=1), dt.time(0), ET)
    B = load(ROOT / "tools" / "backtest_gold.py", "bt")
    T = load(ROOT / "tools" / "gold_tracker.py", "gt")
    B.configure_metal("gold")
    B.P0, B.P1 = P0, P1
    grid = Grid(utc(a.year - 1, 6, 1), utc(b.year + 1, 6, 30))
    years = sorted({a.year, b.year, b.year + 1})
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in years if (ROOT / "build" / f"astronomy_{y}.json").exists()]
    evs = B.collect(ctxs)
    d26 = json.load(open(OUT / "gold_backtest_2000-11-20_to_2026-11-20_ET.json"))
    r26 = {p["rule_id"]: p for p in d26["rules"]}
    for p in r26.values():
        p["status"] = T.status(p)
    for e in evs:
        p = r26.get(e["rule_id"])
        e["status"] = p["status"] if p else "not in backtest"
        e["tier"] = tier(e["status"])
        e["rec26"] = f"{p['worked']}/{p['worked'] + p['failed']} ({p['hit_rate']}% vs {p['base_rate']}%)" if p and p["worked"] + p["failed"] else "-"
        s = e["start"] if e["day"] is None else dt.datetime.combine(e["day"], dt.time(6), ET)
        e["s"], e["e"] = s, e["end"] or s + dt.timedelta(days=5)

    # transits
    recs = []
    for y in years:
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            if r["event_class"] not in KEEP or not r["bodies"]:
                continue
            if r["event_class"] in ("sign_ingress", "nakshatra_ingress") and r["bodies"][0] == "Moon":
                continue
            t = parse(r["time"]["t_start_utc"])
            if not (P0 <= t < P1):
                continue
            recs.append((t, r))
    seen, trans = set(), []
    for t, r in sorted(recs, key=lambda x: x[0]):
        k = (r["event_class"], tuple(r["bodies"]), t.replace(second=0))
        if k in seen:
            continue
        seen.add(k)
        ast = r.get("astronomy", {})
        ec, bd = r["event_class"], r["bodies"]
        if ec == "sign_ingress":
            txt = f"{name(bd[0])} enters {ast.get('sign_to', ast.get('sign'))} ({ast.get('nakshatra')})"
        elif ec == "nakshatra_ingress":
            txt = f"{name(bd[0])} enters {ast.get('nakshatra')} ({ast.get('sign')})"
        elif ec == "station":
            txt = f"{name(bd[0])} stations {'retrograde' if r['rule_family'].endswith('_R') else 'direct'} at {ast.get('sign')} {ast.get('lon_sid', 0) % 30:.1f} deg ({ast.get('nakshatra')})"
        elif ec == "lunation":
            txt = f"{r['rule_family'].split('/')[-1].replace('_', ' ').title()} in {ast.get('sign')} ({ast.get('nakshatra')})"
        elif ec == "combustion":
            txt = f"{name(bd[0])} combust (date-level, Mumbai kalamsha)"
        elif ec == "eclipse":
            txt = f"{'Lunar' if r['rule_family'].endswith('lunar') else 'Solar'} eclipse in {ast.get('sign')} ({ast.get('nakshatra')})"
        else:
            txt = f"{name(bd[0])} {ec.replace('_', ' ')} {name(bd[1]) if len(bd) > 1 else ''} in {ast.get('sign', '')}".strip()
        trans.append(dict(t=t, cls=ec, text=txt, bodies=bd))

    # whole-sign aspects (project drishti) beginning or ending in the range
    asp = []
    for i, p in enumerate(PLANETS):
        for q in PLANETS:
            if q == p or (p == "Ketu"):
                continue
            def rel(s, p=p, q=q):
                if s[p].sign_i == s[q].sign_i:
                    return "with" if PLANETS.index(p) < PLANETS.index(q) else False
                return f"aspects ({s.sign_dist(p, q)}th)" if aspects(s, p, q) else False
            for w in spans(grid, rel):
                if w.end < P0 or w.start >= P1:
                    continue
                asp.append(dict(a=p, b=q, kind=w.value, start=w.start, end=w.end, open_start=w.start < P0, open_end=w.end >= P1))
    asp.sort(key=lambda x: x["start"])

    # daily table
    days = []
    d = a
    model = {}
    while d <= b:
        t = dt.datetime.combine(d, dt.time(12), ET)
        act = [e for e in evs if e["tone"] in ("Bullish", "Bearish") and e["s"] <= t + dt.timedelta(hours=12) and e["e"] >= t - dt.timedelta(hours=12)]
        uniq = {}
        for e in act:
            uniq.setdefault((e["rule_id"], e["tone"]), e)
        act = list(uniq.values())
        cnt = collections.Counter((e["tier"], e["tone"]) for e in act)
        m = BM.evaluate(d)
        model[d.isoformat()] = m
        s = snapshot(t.astimezone(dt.timezone.utc).replace(second=0, microsecond=0))
        sun_c = [f"{x} with Sun" for x in ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu") if s[x].sign_i == s["Sun"].sign_i] + \
                [f"{x} aspects Sun" for x in ("Moon", "Mars", "Jupiter", "Saturn", "Rahu") if s[x].sign_i != s["Sun"].sign_i and aspects(s, x, "Sun")]
        today_tr = [x["text"] for x in trans if x["t"].astimezone(ET).date() == d]
        days.append(dict(date=d, A_bull=cnt[("A", "Bullish")], A_bear=cnt[("A", "Bearish")], B_bull=cnt[("B", "Bullish")], B_bear=cnt[("B", "Bearish")],
                         C_bull=cnt[("C", "Bullish")], C_bear=cnt[("C", "Bearish")], rules=sorted(act, key=lambda e: (e["tier"], e["tone"])),
                         S=m["S"], V=m["V"], bias=m["bias"], conf=m["confidence"], sun=f"{s['Sun'].sign} {s['Sun'].deg:.1f} {s['Sun'].nak}",
                         moon=f"{s['Moon'].sign} {s['Moon'].nak} ({s.paksha}, tithi {s.tithi})", sun_contacts=sun_c, transits=today_tr,
                         retro=[x for x in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn") if s[x].retro]))
        d += dt.timedelta(days=1)

    # seasonality: gold over the same calendar stretch, 2000-2025
    rows = list(csv.DictReader(open(OUT / "backtest" / "gold_GC_F_daily_2000.csv")))
    D = [dt.date.fromisoformat(r["date"]) for r in rows]
    C = [float(r["close"]) for r in rows]
    seas = []
    for y in range(2000, a.year):
        s0, s1 = a.replace(year=y), b.replace(year=y)
        i0 = max(i for i, x in enumerate(D) if x < s0) if any(x < s0 for x in D) else None
        i1 = max(i for i, x in enumerate(D) if x <= s1)
        if i0 is not None and D[i0] >= dt.date(y, 1, 1) - dt.timedelta(days=365):
            seas.append((y, round((C[i1] / C[i0] - 1) * 100, 2)))
    last_i = len(D) - 1

    write(a, b, evs, trans, asp, days, seas, D[last_i], C[last_i], d26)


def cls(t):
    return "bullish" if t == "Bullish" else "bearish" if t == "Bearish" else "mixed"


def write(a, b, evs, trans, asp, days, seas, last_d, last_c, d26):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    stem = f"gold_deep_{a.isoformat()}_to_{b.isoformat()}_ET"
    # rule windows table
    rw = sorted([e for e in evs if e["tone"] in ("Bullish", "Bearish", "Mixed")], key=lambda e: e["s"])
    rule_rows = "".join(
        f"<tr class='{cls(e['tone'])}'><td class='w'>{html.escape(et(e['s']))}{' (running)' if e['s'] < dt.datetime.combine(a, dt.time(0), ET) else ''}</td>"
        f"<td class='w'>{html.escape(et(e['end'])) if e['end'] else '(instant)'}</td><td><b>{html.escape(e['title'])}</b><div class='s'>{html.escape('; '.join(f'{k}: {v}' for k, v in e['facts'].items())[:220])}</div></td>"
        f"<td><span class='tag {cls(e['tone'])}'>{e['tone']}</span></td><td class='n'>{html.escape(e['rec26'])}</td><td>{html.escape(e['status'])} <b>[{e['tier']}]</b></td></tr>" for e in rw)
    tr_rows = "".join(f"<tr><td class='w'>{html.escape(et(x['t']))}</td><td>{html.escape(x['cls'].replace('_', ' '))}</td><td>{html.escape(x['text'])}</td></tr>" for x in trans)
    asp_rows = "".join(
        f"<tr{' class=bullish' if x['b'] == 'Sun' and x['a'] in ('Jupiter', 'Venus', 'Mercury') else ' class=bearish' if x['b'] == 'Sun' and x['a'] in ('Saturn', 'Rahu', 'Mars') else ''}>"
        f"<td class='w'>{'(before) ' if x['open_start'] else ''}{html.escape(et(x['start'], '%a %d %b %Y'))}</td><td class='w'>{html.escape(et(x['end'], '%a %d %b %Y'))}{' (after)' if x['open_end'] else ''}</td>"
        f"<td><b>{x['a']}</b> {html.escape(x['kind'])} <b>{x['b']}</b></td></tr>" for x in asp)
    def drow(d):
        a_net = d["A_bull"] - d["A_bear"]
        c_ = "bullish" if a_net > 0 else "bearish" if a_net < 0 else "mixed"
        rl = "".join(f"<li class='s'>[{e['tier']}] <b>{html.escape(e['title'])}</b> ({e['tone']}; 26 yr {html.escape(e['rec26'])})</li>" for e in d["rules"])
        return (f"<tr class='{c_}'><td class='w'><b>{d['date']:%a %d %b}</b></td><td class='n'>{d['A_bull']} : {d['A_bear']}</td><td class='n'>{d['B_bull']} : {d['B_bear']}</td><td class='n'>{d['C_bull']} : {d['C_bear']}</td>"
                f"<td class='n'>{d['S']:+.0f} / {d['V']:+.0f}<div class='s'>{html.escape(d['bias'])}</div></td><td class='s'>Sun {html.escape(d['sun'])}; {html.escape(', '.join(d['sun_contacts']) or 'no contacts')}<br>Moon {html.escape(d['moon'])}"
                f"{'<br>Retrograde: ' + ', '.join(d['retro']) if d['retro'] else ''}</td><td class='s'>{html.escape('; '.join(d['transits']))}</td><td><details><summary>{len(d['rules'])} rules</summary><ul>{rl}</ul></details></td></tr>")
    daily = "".join(drow(d) for d in days)
    sv = [r for _, r in seas]
    sea_rows = " · ".join(f"{y}: {r:+.1f}%" for y, r in seas)
    t26 = d26["totals"]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gold Deep Analysis</title><style>{css}</style></head><body>
<h1>Gold deep analysis, {a:%d %b %Y} – {b:%d %b %Y} (US Eastern)</h1>
<p class="m">Every gold rule in the project (TA, KD, 2026 document, your Sun notes U1–U4, Brihat Samhita), every transit and whole-sign aspect, and Model v1.0, day by day.
Each rule carries its <b>26-year record</b> (2000–2026; whole rule set {t26['WORKED']} worked / {t26['FAILED']} failed, no rule significant at p &lt; 0.05):
<b>tier A</b> = most consistent (Strongest / Supported / Consistent), <b>B</b> = at chance or too few to judge, <b>C</b> = did not hold up. Last gold close: {last_c:,.1f} ({last_d:%d %b %Y}).</p>
<h2>Gold's own record over this calendar stretch (2000–2025)</h2>
<p class="m">Close before {a:%d %b} to the last close on or before {b:%d %b}, each year: average {statistics.fmean(sv):+.2f}%, median {statistics.median(sv):+.2f}%, up in {sum(r > 0 for r in sv)} of {len(sv)} years. {sea_rows}</p>
{{SUMMARY}}
<h2>Day by day</h2>
<p class="m">Rules active that day (bullish : bearish) by tier; Model v1.0 scarcity / demand index and bias; the Sun (gold's significator in your notes), the Moon, retrograde planets and that day's transits.</p>
<div class="wrap"><table><thead><tr><th>Date</th><th>Tier A</th><th>Tier B</th><th>Tier C</th><th>Model v1.0 S / V</th><th>Sky</th><th>Transits that day</th><th>Rules</th></tr></thead><tbody>{daily}</tbody></table></div>
<h2>Every gold rule window in the period</h2>
<div class="wrap"><table><thead><tr><th>From (ET)</th><th>To (ET)</th><th>Rule</th><th>Effect</th><th>26-year record</th><th>26-year status [tier]</th></tr></thead><tbody>{rule_rows}</tbody></table></div>
<h2>Transits</h2>
<div class="wrap"><table><thead><tr><th>When (ET)</th><th>Kind</th><th>Event</th></tr></thead><tbody>{tr_rows}</tbody></table></div>
<h2>Whole-sign aspects and conjunctions in force</h2>
<p class="m">Project drishti: every planet 7th; Mars 4/8, Jupiter 5/9, Saturn 3/10; Rahu 7th; "with" = same sign. Rows on the Sun are coloured by your notes (green: Jupiter/Venus/Mercury; red: Saturn/Rahu/Mars).</p>
<div class="wrap"><table><thead><tr><th>From</th><th>To</th><th>Aspect</th></tr></thead><tbody>{asp_rows}</tbody></table></div>
<p class="s">Generated by tools/gold_deep_analysis.py. Rules: tools/backtest_gold.py collect(); records: build/pdfref/gold_backtest_2000-11-20_to_2026-11-20_ET.json; Model v1.0: finastro/pdfref/bs41_model.py.</p>
</body></html>"""
    notes = OUT / f"{stem}_notes.md"
    summary = ""
    if notes.exists():                      # hand-written analysis for this range, rendered into the page
        M2 = load(ROOT / "tools" / "md_to_html.py", "mdh")
        full = M2.render(notes.read_text(encoding="utf-8"), "notes")
        summary = full.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    page = page.replace("{SUMMARY}", summary)
    (OUT / f"{stem}.html").write_text(page, encoding="utf-8")
    def ser(x):
        if isinstance(x, (dt.datetime, dt.date)):
            return x.isoformat()
        return str(x)
    json.dump(dict(period=[a.isoformat(), b.isoformat()], last_close=[last_d.isoformat(), last_c], seasonality=seas,
                   days=[{k: v for k, v in d.items() if k != "rules"} | {"rules": [dict(rule_id=e["rule_id"], title=e["title"], tone=e["tone"], tier=e["tier"], rec26=e["rec26"]) for e in d["rules"]]} for d in days],
                   rule_windows=[dict(rule_id=e["rule_id"], title=e["title"], tone=e["tone"], start=e["s"], end=e["end"], tier=e["tier"], status=e["status"], rec26=e["rec26"], facts=e["facts"]) for e in rw],
                   transits=trans, aspects=asp), open(OUT / f"{stem}.json", "w"), indent=1, default=ser)
    print(stem, len(days), "days", len(rw), "rule windows", len(trans), "transits", len(asp), "aspects")


if __name__ == "__main__":
    main()
