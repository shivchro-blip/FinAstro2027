"""One timeline of everything the tested work says about 22 Nov 2026 - 31 Dec 2027.

    python tools/gold_outlook.py [start] [end]

Collects, with each item's evidence:
  * best gold and silver rules' windows (gold_tracker.py forward files; 26-year records),
  * big-move watch stretches and single-lead windows (big_move_forward.py),
  * Venus combust / rising dates (test_venus_visibility.py; TA Section 18),
and writes a dated timeline, a month-by-month summary and a calendar:
build/pdfref/gold_outlook_{start}_to_{end}_ET.{html,json,ics}.
Run after the trackers, big_move_forward.py and test_venus_visibility.py.
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
ET = ZoneInfo("America/New_York")


def d_et(s):
    t = dt.datetime.fromisoformat(s)
    return (t if t.tzinfo else t.replace(tzinfo=ET)).astimezone(ET).date()


def items(a, b):
    out = []
    for metal in ("gold", "silver"):
        f = json.load(open(OUT / f"{metal}_forward_2026-11-20_to_2027-12-31_ET.json"))
        for w in f["best_windows"]:
            s, e = d_et(w["start"]), d_et(w["end"]) if w["end"] else d_et(w["start"])
            if e < a or s > b:
                continue
            strong = w["rule_id"] in ("ta_s35a01_retro_mercury_or_jupiter", "ta_s34a09_mars_aspected_saturn_jupiter_retro")
            out.append(dict(metal=metal, kind="Best rule", frm=max(s, a), to=min(e, b), title=w["title"], lean="up" if w["tone"] == "Bullish" else "down",
                            evidence=f"26 yrs: {w['hist']}", weight="lead (p ≈ 0.05–0.07)" if strong else "small edge"))
    wf = json.load(open(OUT / f"gold_big_move_watch_{a}_to_{b}_ET.json"))
    for s in wf["stretches"]:
        out.append(dict(metal="gold", kind="Volatility watch", frm=dt.date.fromisoformat(s["frm"]), to=dt.date.fromisoformat(s["to"]),
                        title="Big-move watch: " + "; ".join(x.split(": ", 1)[1] for x in s["leads"]), lean=s["lean"],
                        evidence=f"leads over-represented on ±2% days 2000–2026 (no FDR pass; out of sample ×{wf['split']['pooled_lift']})", weight="volatility only"))
    lead = {L["factor"]: L for L in wf["leads"]}
    for w in wf["windows"]:
        L = lead[w["factor"]]
        if L["outer"] or not L["both_halves"] or w["factor"] == "Event: full moon":
            continue
        f0, t0 = dt.date.fromisoformat(w["frm"]), dt.date.fromisoformat(w["to"])
        if any(x["kind"] == "Volatility watch" and x["frm"] <= t0 and f0 <= x["to"] for x in out):
            continue
        out.append(dict(metal="gold", kind="Volatility watch", frm=dt.date.fromisoformat(w["frm"]), to=dt.date.fromisoformat(w["to"]),
                        title="Single lead: " + w["factor"].split(": ", 1)[1], lean=L["lean"],
                        evidence=f"held in both halves; ±2% days {L['big_rate']}% when present vs {wf['base_big_rate']}% normally", weight="volatility only"))
    vv = json.load(open(OUT / "venus_visibility_test_2000-2026_ET.json"))
    rec = {r["rule_id"]: r for r in vv["rules"]}
    for f in vv["forward"]:
        s = d_et(f["start"])
        e = d_et(f["end"]) if f["end"] else s
        if e < a or s > b:
            continue
        g = rec[f["rule_id"]]["metals"]["gold"]
        if f["rule_id"] == "ta_s18_venus_combust_east":
            ev = f"gold {g['main']['worked']}/{g['main']['worked'] + g['main']['failed']} ({g['main']['hit']}% vs {g['main']['base']}%, p {g['main']['p']}); 20 sessions {g['f20']['hit']}% vs {g['f20']['base']}%"
            wt = "lead (p ≈ 0.10)"
        else:
            q = g.get("qualified", {})
            ev = (f"gold {g['main']['worked']}/{g['main']['worked'] + g['main']['failed']} ({g['main']['hit']}% vs {g['main']['base']}%), at chance; qualified dip-then-upturn {q.get('pattern')}/{q.get('n')} vs {q.get('expected')} expected. "
                  "Same configuration as 31 Jan 2026.")
            wt = "no edge – watch only"
        out.append(dict(metal="gold & silver", kind="Venus (TA S18)", frm=s, to=e,
                        title=f"{f['title']} – {f['sign']} / {f['nakshatra']}{' with ' + ', '.join(f['with_']) if f['with_'] else ''}{' (qualified: sharp upturn after a small dip)' if f['qualified'] else ''}",
                        lean="up" if f["tone"] == "Bullish" else "dip then up" if f["qualified"] else "down", evidence=ev, weight=wt))
    return sorted(out, key=lambda x: (x["frm"], x["kind"]))


def months(its, a, b):
    rows = []
    m = dt.date(a.year, a.month, 1)
    while m <= b:
        nxt = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        lo, hi = max(m, a), min(nxt - dt.timedelta(days=1), b)
        days = (hi - lo).days + 1

        def cover(pred):
            s = set()
            for x in its:
                if pred(x):
                    d = max(x["frm"], lo)
                    while d <= min(x["to"], hi):
                        s.add(d)
                        d += dt.timedelta(days=1)
            return round(len(s) / days * 100)
        rows.append(dict(month=m.strftime("%b %Y"), gold_up=cover(lambda x: x["metal"] == "gold" and x["kind"] == "Best rule"),
                         silver_up=cover(lambda x: x["metal"] == "silver" and x["kind"] == "Best rule"),
                         watch=[f"{x['frm']:%d %b}–{x['to']:%d %b} ({x['lean']})" for x in its if x["kind"] == "Volatility watch" and x["title"].startswith("Big") and lo <= x["frm"] <= hi],
                         singles=[f"{x['frm']:%d %b}: {x['title'].split(': ', 1)[1]} ({x['lean']})" for x in its if x["kind"] == "Volatility watch" and x["title"].startswith("Single") and lo <= x["frm"] <= hi],
                         venus=[f"{x['frm']:%d %b}: {x['title'].split(' – ')[0]}" for x in its if x["kind"].startswith("Venus") and x["frm"] <= hi and x["to"] >= lo]))
        m = nxt
    return rows


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 22)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2027, 12, 31)
    its = items(a, b)
    mon = months(its, a, b)
    stem = f"gold_outlook_{a}_to_{b}_ET"
    json.dump(dict(start=a.isoformat(), end=b.isoformat(), items=its, months=mon), open(OUT / f"{stem}.json", "w"), indent=1, default=str)
    (OUT / f"{stem}.html").write_text(page(a, b, its, mon), encoding="utf-8")
    (OUT / f"{stem}.ics").write_text(ics(its), encoding="utf-8")
    print(f"{len(its)} items")
    for r in mon:
        print(f"  {r['month']}: gold up-rule {r['gold_up']}%, silver up-rule {r['silver_up']}%, watch {r['watch']}, singles {r['singles']}, venus {r['venus']}")


def page(a, b, its, mon):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    cls = {"up": "bullish", "down": "bearish"}

    def span(x):
        return f"{x['frm']:%a %d %b %Y}" if x["frm"] == x["to"] else f"{x['frm']:%a %d %b %Y} – {x['to']:%a %d %b %Y}"
    trows = "".join(f"<tr class='{cls.get(x['lean'], 'mixed')}'><td class='w'>{span(x)}</td><td>{x['metal']}</td><td>{x['kind']}</td><td><b>{html.escape(x['title'])}</b></td>"
                    f"<td>{x['lean']}</td><td>{x['weight']}</td><td class='s'>{html.escape(x['evidence'])}</td></tr>" for x in its)
    mrows = "".join(f"<tr><td class='w'><b>{r['month']}</b></td><td class='n'>{r['gold_up']}%</td><td class='n'>{r['silver_up']}%</td><td class='s'>{html.escape('; '.join(r['watch']) or '-')}</td>"
                    f"<td class='s'>{html.escape('; '.join(r['singles']) or '-')}</td><td class='s'>{html.escape('; '.join(r['venus']) or '-')}</td></tr>" for r in mon)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gold Outlook 2027</title><style>{css}</style></head><body>
<h1>Gold &amp; silver outlook, {a:%d %b %Y} – {b:%d %b %Y} (US Eastern)</h1>
<p class="m">Everything the tested work says about this period, in one place, each item with its 2000–2026 evidence. <b>Nothing here passed a strict significance test</b>: the best items are leads at p ≈ 0.05–0.10, the rest are small edges or volatility watch dates. Use them as context alongside price, not as calls.</p>
<ul class="m">
<li><b>Gold's best rules:</b> U2 – Mercury with the Sun (bullish; 60% vs 57% by chance, right in 20 of 26 years) covers about half of the period. TA S34 A9 (Mars aspected by Saturn while Jupiter is retrograde, 14/17) does not occur before 2028.</li>
<li><b>Silver's best rules:</b> retrograde Mercury or Jupiter (bullish; 62% vs 54%, p ≈ 0.05) – mid-Dec 2026 to mid-Apr 2027, Jun–early Jul 2027 and Oct 2027; Moon and Mercury alone in a sign (short bullish windows).</li>
<li><b>Venus (TA Section 18):</b> combust in the East 20 Jul – 7 Sep 2027 (bullish; gold 12/16 since 2000); rises in the West 7 Sep 2027 in Leo with the Sun – the same qualified configuration as 31 Jan 2026 (“sharp upturn after a small dip”), which has no edge over 26 years.</li>
<li><b>Volatility watch:</b> 21–27 Jan, 22–25 Mar, 22–28 Jun, 18 Oct and 27–31 Dec 2027, plus single leads such as the Venus–Saturn conjunction on 7 May 2027.</li></ul>
<h2>Month by month</h2>
<div class="wrap"><table><thead><tr><th>Month</th><th>Gold: days under a best bullish rule</th><th>Silver: days under a best bullish rule</th><th>Volatility watch stretches</th><th>Single volatility leads</th><th>Venus</th></tr></thead><tbody>{mrows}</tbody></table></div>
<h2>Timeline</h2>
<div class="wrap"><table><thead><tr><th>Dates</th><th>Metal</th><th>Kind</th><th>Item</th><th>Lean</th><th>Weight</th><th>Evidence (2000–2026)</th></tr></thead><tbody>{trows}</tbody></table></div>
<p class="s">Sources: GOLD_TRACKER / SILVER_TRACKER forward files, gold_big_move_watch_*, venus_visibility_test_2000-2026_ET. Generated by tools/gold_outlook.py. The day-by-day view for 22 Nov – 31 Dec 2026 is in gold_deep_2026-11-22_to_2026-12-31_ET.html.</p></body></html>"""


def ics(its):
    def esc(t):
        return t.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//finastro2027//gold outlook//EN", "CALSCALE:GREGORIAN", "X-WR-CALNAME:Gold & silver outlook 2027"]
    seen = collections.Counter()
    for x in its:
        uid = f"outlook-{x['frm']}-{x['kind'][:4]}-{x['metal'][:3]}"
        seen[uid] += 1
        summary = x["metal"] + ": " + x["title"][:90] + " (" + x["lean"] + ")"
        lines += ["BEGIN:VEVENT", f"UID:{uid}-{seen[uid]}@finastro2027", f"DTSTAMP:{now}", f"DTSTART;VALUE=DATE:{x['frm']:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{x['to'] + dt.timedelta(days=1):%Y%m%d}", f"SUMMARY:{esc(summary)}",
                  f"DESCRIPTION:{esc(x['kind'] + ' - ' + x['weight'] + '. ' + x['evidence'])}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


if __name__ == "__main__":
    main()
