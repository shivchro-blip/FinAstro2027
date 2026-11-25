"""Jupiter-Saturn aspects (10° orb) and gold: the windows Nov 2026 - Dec 2030 recomputed, every past window since 1972
with gold's turns inside it, and a plain table of which coming dates lean to a bottom or a top.

    python tools/jupiter_saturn_gold.py

Aspects by degree (geocentric apparent longitudes; the Jupiter-Saturn separation is the same in the tropical and the
Lahiri zodiac): conjunction 0°, trine 120°, opposition 180°, each with a 10° orb; exact passes found to the minute.
Gold: monthly averages 1972-1999 (datasets/gold-prices) and daily COMEX closes 2000-2026; major turns from
tools/gold_turns.py (15% zigzag). For each past window: gold's move from entry to exit, the moves before the first and
after the last exact pass, and the bottoms / peaks inside the window or within 30 days of it, placed in the applying
(before the first exact pass) or separating (after the last) phase. A coming date "leans" bottom or top only when past
turns in the same aspect and phase split at least 2 to 1 with three or more turns; otherwise "a turn, either way".
Writes build/pdfref/jupiter_saturn_gold_ET.{html,json}. Market prices and astrology only.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402

GJ = load(ROOT / "tools" / "gold_jupiter_crash.py", "gj_js")
ET, UTC = ZoneInfo("America/New_York"), dt.timezone.utc
ASPECTS = {"conjunction": 0, "trine": 120, "opposition": 180}
ORB = 10
GIVEN = {"trine": dict(enter="2027-02-14", exact=["2027-04-03 08:59", "2027-07-11 19:16"], leave="2027-08-30"),
         "opposition": [dict(enter="2028-12-27", exact=[], leave="2029-02-27"), dict(enter="2029-11-15", exact=["2029-12-22 02:02", "2030-04-23 21:57"], leave="2030-06-02"),
                        dict(enter="2030-10-14", exact=["2030-11-19 20:05"], leave="2030-12-23")]}


def sep(t):
    u = t.astimezone(UTC)
    j = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)
    a = swe.calc_ut(j, swe.JUPITER, swe.FLG_SWIEPH)[0][0]
    b = swe.calc_ut(j, swe.SATURN, swe.FLG_SWIEPH)[0][0]
    return abs((a - b + 180) % 360 - 180)


def jup_retro(t):
    u = t.astimezone(UTC)
    return swe.calc_ut(swe.julday(u.year, u.month, u.day, 12), swe.JUPITER, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3] < 0


def refine(f, a, b):
    """Root of f between a and b (f changes sign)."""
    fa = f(a)
    for _ in range(40):
        m = a + (b - a) / 2
        if (f(m) > 0) == (fa > 0):
            a, fa = m, f(m)
        else:
            b = m
    return a + (b - a) / 2


def windows(a, b):
    out = []
    for name, ang in ASPECTS.items():
        t = dt.datetime(a.year, a.month, a.day, 12, tzinfo=UTC)
        end = dt.datetime(b.year, b.month, b.day, 12, tzinfo=UTC)
        prev_in, prev_d = None, None
        cur = None
        while t <= end:
            dv = sep(t) - ang
            inside = abs(dv) <= ORB
            if inside and not prev_in:
                enter = refine(lambda x: abs(sep(x) - ang) - ORB, t - dt.timedelta(days=1), t) if prev_in is not None else t
                cur = dict(aspect=name, enter=enter, exact=[], min_orb=99)
            if inside:
                cur["min_orb"] = min(cur["min_orb"], abs(dv))
                if prev_d is not None and (dv > 0) != (prev_d > 0) and ang not in (0, 180):
                    cur["exact"].append(refine(lambda x: sep(x) - ang, t - dt.timedelta(days=1), t))
                if ang in (0, 180) and prev_d is not None:
                    # exact 0 / 180: separation turns around (minimum for 0, maximum for 180)
                    pass
            if not inside and prev_in:
                cur["leave"] = refine(lambda x: abs(sep(x) - ang) - ORB, t - dt.timedelta(days=1), t)
                out.append(cur)
                cur = None
            prev_in, prev_d = inside, dv
            t += dt.timedelta(days=1)
        if cur:
            cur["leave"] = None
            out.append(cur)
    # exact 0 and 180: closest approaches below 0.05°
    for w in out:
        if w["aspect"] in ("conjunction", "opposition") and w["min_orb"] < 0.5:
            ang = ASPECTS[w["aspect"]]
            t = w["enter"]
            stop = w["leave"] or t + dt.timedelta(days=400)
            last = None
            seq = []
            while t <= stop:
                seq.append((t, abs(sep(t) - ang)))
                t += dt.timedelta(hours=6)
            for i in range(1, len(seq) - 1):
                if seq[i][1] <= seq[i - 1][1] and seq[i][1] < seq[i + 1][1] and seq[i][1] < 0.05:
                    lo, hi = seq[i - 1][0], seq[i + 1][0]
                    for _ in range(60):
                        m1, m2 = lo + (hi - lo) / 3, lo + 2 * (hi - lo) / 3
                        if abs(sep(m1) - ang) < abs(sep(m2) - ang):
                            hi = m2
                        else:
                            lo = m1
                    w["exact"].append(lo + (hi - lo) / 2)
    return sorted(out, key=lambda w: w["enter"])


def series():
    M = [(d, p) for d, p in GJ.monthly() if d < dt.date(2000, 1, 1)]
    return M + GJ.daily()


def price_at(S, d, after=True):
    if after:
        for x, p in S:
            if x >= d:
                return x, p
    else:
        last = None
        for x, p in S:
            if x > d:
                break
            last = (x, p)
        return last
    return None


def main():
    S = series()
    turns = [(t["kind"], dt.date.fromisoformat(t["date"])) for t in json.load(open(OUT / "gold_turns_ET.json"))["turns"]]
    hist = [w for w in windows(dt.date(1971, 9, 1), dt.date(2026, 11, 20)) if w["enter"].date() >= dt.date(1972, 1, 1)]
    past = []
    for w in hist:
        e0, e1 = w["enter"].date(), (w["leave"] or w["enter"]).date()
        ex = [x.date() for x in w["exact"]]
        p0, p1 = price_at(S, e0), price_at(S, e1, after=False)
        mv = None if not (p0 and p1) or p1[0] <= p0[0] else round((p1[1] / p0[1] - 1) * 100, 1)
        inside = []
        anchors = [("enter", e0)] + [("exact", x) for x in ex] + [("leave", e1)]
        for k, d in turns:
            if e0 - dt.timedelta(days=30) <= d <= e1 + dt.timedelta(days=30):
                phase = "applying" if ex and d < ex[0] else "separating" if ex and d > ex[-1] else "between passes" if ex else "no exact pass"
                anc = min(anchors, key=lambda a: abs((a[1] - d).days))
                inside.append(dict(kind=k, date=str(d), phase=phase, anchor=anc[0], days_from_anchor=(d - anc[1]).days,
                                   jup_retro=jup_retro(dt.datetime(d.year, d.month, d.day, 12, tzinfo=UTC))))
        app = sep_ = None
        if ex:
            pa, pb = price_at(S, ex[0], after=False), price_at(S, ex[-1])
            if p0 and pa and pa[0] > p0[0]:
                app = round((pa[1] / p0[1] - 1) * 100, 1)
            if pb and p1 and p1[0] > pb[0]:
                sep_ = round((p1[1] / pb[1] - 1) * 100, 1)
        past.append(dict(aspect=w["aspect"], enter=str(e0), leave=str(e1), exact=[str(x) for x in ex], move=mv, applying_move=app, separating_move=sep_, turns=inside))
    # tendencies by aspect and phase
    tend = {}
    for p in past:
        for t in p["turns"]:
            k = (p["aspect"], t["phase"])
            tend.setdefault(k, {"bottom": 0, "peak": 0})
            tend[k][t["kind"]] += 1
    anc_t = {}
    for p in past:
        for t in p["turns"]:
            k = (p["aspect"], t["anchor"])
            anc_t.setdefault(k, {"bottom": 0, "peak": 0})
            anc_t[k][t["kind"]] += 1
    tend_all = {}
    for p in past:
        for t in p["turns"]:
            tend_all.setdefault(p["aspect"], {"bottom": 0, "peak": 0})
            tend_all[p["aspect"]][t["kind"]] += 1

    def lean(aspect, phase):
        c = anc_t.get((aspect, phase), {"bottom": 0, "peak": 0})
        n = c["bottom"] + c["peak"]
        if n >= 3 and c["bottom"] >= 2 * c["peak"]:
            return "bottom-leaning", c
        if n >= 3 and c["peak"] >= 2 * c["bottom"]:
            return "top-leaning", c
        return "a turn, either way", c
    fut = windows(dt.date(2026, 11, 25), dt.date(2030, 12, 31))
    # Jupiter / Saturn stations 2026-11 to 2030-12
    stations = []
    t = dt.datetime(2026, 11, 25, 12, tzinfo=UTC)
    prev = {}
    while t <= dt.datetime(2030, 12, 31, 12, tzinfo=UTC):
        j = swe.julday(t.year, t.month, t.day, 12)
        for b, k in (("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN)):
            r = swe.calc_ut(j, k, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3] < 0
            if b in prev and prev[b] != r:
                stations.append((t.date(), f"{b} turns {'retrograde' if r else 'direct'}"))
            prev[b] = r
        t += dt.timedelta(days=1)
    rows = []
    for w in fut:
        nm = w["aspect"]
        ex = w["exact"]
        l1, c1 = lean(nm, "enter")
        rows.append(dict(date=w["enter"].astimezone(ET).strftime("%d %b %Y"), event=f"Jupiter–Saturn {nm} enters 10° orb", lean=l1, basis=c1, phase="applying"))
        for i, x in enumerate(ex):
            l2, c2 = lean(nm, "exact")
            rows.append(dict(date=x.astimezone(ET).strftime("%d %b %Y %H:%M"), event=f"Exact {nm} ({ASPECTS[nm]}°){' — pass ' + str(i + 1) if len(ex) > 1 else ''}",
                             lean=l2, basis=c2, phase="exact"))
        if w["leave"]:
            l3, c3 = lean(nm, "leave")
            rows.append(dict(date=w["leave"].astimezone(ET).strftime("%d %b %Y"), event=f"Jupiter–Saturn {nm} leaves 10° orb", lean=l3, basis=c3, phase="separating"))
    gt = json.load(open(OUT / "gold_turns_ET.json"))["rec"]
    for d, what in stations:
        key = {"Jupiter turns direct": "Jupiter direct station within ±30 days", "Saturn turns direct": "Saturn direct station within ±30 days"}.get(what)
        if not key:
            continue
        b_, p_ = gt["bottom"][key], gt["peak"][key]
        rb, rp = b_["hits"] / b_["n"] / (b_["base"] / 100), p_["hits"] / p_["n"] / (p_["base"] / 100)
        lean_ = "bottom-leaning (weak)" if rb >= 1.5 and rb > 1.3 * rp else "a turn, either way"
        rows.append(dict(date=d.strftime("%d %b %Y"), event=what + " (±30 days)", lean=lean_, basis={"bottom": b_["hits"], "peak": p_["hits"]}, phase="station",
                         note=f"bottoms {b_['hits']}/{b_['n']} vs tops {p_['hits']}/{p_['n']}; normal {b_['base']}% of weeks"))
    rows.sort(key=lambda r: dt.datetime.strptime(r["date"][:11], "%d %b %Y"))
    # verification against the pasted dates
    ver = []
    tw = [w for w in fut if w["aspect"] == "trine"]
    if tw:
        w = tw[0]
        ver.append(dict(item="Trine enters orb", given=GIVEN["trine"]["enter"], ours=w["enter"].astimezone(ET).strftime("%Y-%m-%d")))
        for g, x in zip(GIVEN["trine"]["exact"], w["exact"]):
            ver.append(dict(item="Exact trine", given=g, ours=x.astimezone(ET).strftime("%Y-%m-%d %H:%M")))
        ver.append(dict(item="Trine leaves orb", given=GIVEN["trine"]["leave"], ours=w["leave"].astimezone(ET).strftime("%Y-%m-%d") if w["leave"] else "–"))
    for g, w in zip(GIVEN["opposition"], [w for w in fut if w["aspect"] == "opposition"]):
        ver.append(dict(item="Opposition enters orb", given=g["enter"], ours=w["enter"].astimezone(ET).strftime("%Y-%m-%d")))
        for gx, x in zip(g["exact"], w["exact"]):
            ver.append(dict(item="Exact opposition", given=gx, ours=x.astimezone(ET).strftime("%Y-%m-%d %H:%M")))
        ver.append(dict(item="Opposition leaves orb", given=g["leave"], ours=w["leave"].astimezone(ET).strftime("%Y-%m-%d") if w["leave"] else "–"))
    res = dict(rows=rows, past=past, anchors={f"{a}|{p}": v for (a, p), v in anc_t.items()}, tend={f"{a}|{p}": v for (a, p), v in tend.items()}, tend_all=tend_all, verify=ver,
               future=[dict(aspect=w["aspect"], enter=str(w["enter"].astimezone(ET)), exact=[str(x.astimezone(ET)) for x in w["exact"]], leave=str(w["leave"].astimezone(ET)) if w["leave"] else None) for w in fut])
    json.dump(res, open(OUT / "jupiter_saturn_gold_ET.json", "w"), indent=1, default=str)
    (OUT / "jupiter_saturn_gold_ET.html").write_text(page(res), encoding="utf-8")
    for v in ver:
        print(v)
    print("by anchor:", anc_t)
    print("by aspect:", tend_all)
    for p in past:
        print(p["aspect"], p["enter"], p["leave"], p["exact"], "move", p["move"], "app", p["applying_move"], "sep", p["separating_move"], [(t["kind"], t["date"], t["phase"]) for t in p["turns"]])
    for r in rows:
        print(r["date"], "|", r["event"], "|", r["lean"], r["basis"])


def page(res):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--upbg:#dafbe1;--dn:#cf222e;--dnbg:#ffebe9;--vo:#9a6700;--vobg:#fff8c5}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--upbg:#12261e;--dn:#f85149;--dnbg:#2d1215;--vo:#d29922;--vobg:#2e2410}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--upbg:#12261e;--dn:#f85149;--dnbg:#2d1215;--vo:#d29922;--vobg:#2e2410}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1150px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .chip{display:inline-block;padding:0 8px;border-radius:10px;font-weight:600;font-size:12.5px}
.b{color:var(--up);background:var(--upbg)} .t{color:var(--dn);background:var(--dnbg)} .e{color:var(--vo);background:var(--vobg)}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Jupiter Saturn Gold</title><style>{css}</style></head><body>",
         "<h1>Jupiter–Saturn and gold: which dates lean to a bottom or a top, Nov 2026 – Dec 2030</h1>",
         "<p class='s'>Read the table as watch dates. “Bottom-leaning” or “top-leaning” only where past gold turns in the same phase split at least 2 to 1 with three or more turns; "
         "otherwise “a turn, either way”. Based on gold since 1972; small samples.</p><h2>The table</h2><div class='wrap'><table><thead><tr><th>Date (New York)</th><th>Event</th>"
         "<th>Gold: likely</th><th>Past gold turns at this point</th></tr></thead><tbody>"]
    for r in res["rows"]:
        cls = "b" if r["lean"].startswith("bottom") else "t" if r["lean"].startswith("top") else "e"
        bz = r["basis"]
        o.append(f"<tr><td class='n'>{E(r['date'])}</td><td>{E(r['event'])}</td><td><span class='chip {cls}'>{E(r['lean'])}</span></td>"
                 f"<td class='s'>{bz.get('bottom', 0)} bottoms, {bz.get('peak', 0)} tops</td></tr>")
    o.append("</tbody></table></div><h2>Check of the dates you were given</h2><div class='wrap'><table><thead><tr><th>Item</th><th>Given</th><th>Ours</th></tr></thead><tbody>")
    for v in res["verify"]:
        o.append(f"<tr><td>{E(v['item'])}</td><td>{E(v['given'])}</td><td>{E(v['ours'])}</td></tr>")
    o.append("</tbody></table></div><h2>Every past Jupiter–Saturn window since 1972 and gold</h2><div class='wrap'><table><thead><tr><th>Aspect</th><th>Window</th><th>Exact</th>"
             "<th class='n'>Gold in window</th><th class='n'>Before first exact / after last</th><th>Gold turns (±30 days)</th></tr></thead><tbody>")
    for p in res["past"]:
        tt = "; ".join(f"{t['kind']} {t['date']} ({t['phase']})" for t in p["turns"]) or "none"
        o.append(f"<tr><td>{p['aspect']}</td><td class='n'>{p['enter']} – {p['leave']}</td><td class='s'>{', '.join(p['exact']) or '–'}</td><td class='n'>{'' if p['move'] is None else format(p['move'], '+.1f') + '%'}</td>"
                 f"<td class='n'>{'' if p['applying_move'] is None else format(p['applying_move'], '+.1f') + '%'} / {'' if p['separating_move'] is None else format(p['separating_move'], '+.1f') + '%'}</td><td class='s'>{E(tt)}</td></tr>")
    o.append("</tbody></table></div><p class='s'>Generated by tools/jupiter_saturn_gold.py. Jupiter direct stations: 8 of 24 past gold bottoms (and 5 of 25 tops) fell within 30 days of one; "
             "Saturn direct stations: 7 of 24 bottoms (gold_turns_ET.html).</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
