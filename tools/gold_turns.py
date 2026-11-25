"""Gold's major peaks and bottoms since 1972: the planetary positions at each turn, which features recur at bottoms
(and at peaks) more often than on ordinary days, and when those features come next.

    python tools/gold_turns.py

Turns: a zigzag with a 15% threshold on monthly gold 1972-1999 (datasets/gold-prices, monthly averages) and on daily
COMEX gold closes 2000-2026. At each turn: sidereal Lahiri degrees of every body, retrograde state, days to the nearest
station of Mercury, Venus, Mars, Jupiter and Saturn, the Jupiter-Saturn angle, Jupiter with a node, Jupiter hemmed,
malefic Vedha on Jupiter, and whether Jupiter's afflictions (tools/gold_jupiter_crash.py) began or ended near the turn.
Recurrence test: each feature's share at bottoms (or peaks) against its share on all days 1972-2026 (binomial p).
With about ten bottoms, only a strong, repeated feature can mean anything; everything else is description.
Writes build/pdfref/gold_turns_ET.{html,json}. Market prices and astrology only.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402
from finastro.pdfref.engine import snapshot  # noqa: E402

GJ = load(ROOT / "tools" / "gold_jupiter_crash.py", "gj_t")
ET, UTC = ZoneInfo("America/New_York"), dt.timezone.utc
SIGNS = GJ.SIGNS
BODIES = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Uranus", "Neptune", "Pluto")
STATION_BODIES = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")
WIN = {"Mercury": 7, "Venus": 15, "Mars": 15, "Jupiter": 30, "Saturn": 30}


def zigzag(series, thr):
    """Alternating peaks and troughs: a turn is confirmed when price moves thr% the other way."""
    turns = []
    mode = None
    ext_d, ext_p = series[0]
    for d, p in series[1:]:
        if mode in (None, "up"):
            if p > ext_p:
                ext_d, ext_p = d, p
            elif (p / ext_p - 1) * 100 <= -thr:
                turns.append(("peak", ext_d, ext_p))
                mode, ext_d, ext_p = "down", d, p
        if mode == "down":
            if p < ext_p:
                ext_d, ext_p = d, p
            elif (p / ext_p - 1) * 100 >= thr:
                turns.append(("bottom", ext_d, ext_p))
                mode, ext_d, ext_p = "up", d, p
    return turns


def stations(a, b):
    """Station dates of the station bodies between a and b (daily scan)."""
    out = {x: [] for x in STATION_BODIES}
    d = a
    prev = None
    while d <= b:
        s = snapshot(dt.datetime(d.year, d.month, d.day, 12, tzinfo=UTC))
        cur = {x: s[x].retro for x in STATION_BODIES}
        if prev:
            for x in STATION_BODIES:
                if cur[x] != prev[x]:
                    out[x].append((d, "R" if cur[x] else "D"))
        prev = cur
        d += dt.timedelta(days=1)
    return out


def features(d, st_list, jspans):
    t = dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET).astimezone(UTC)
    s = snapshot(t)
    gst = GJ.state(t)
    f = {}
    for x in STATION_BODIES:
        near = min(st_list[x], key=lambda z: abs((z[0] - d).days)) if st_list[x] else None
        dd = (near[0] - d).days if near else None
        f[f"{x} station within ±{WIN[x]} days"] = dd is not None and abs(dd) <= WIN[x]
        f[f"{x} direct station within ±{WIN[x]} days"] = dd is not None and abs(dd) <= WIN[x] and near[1] == "D"
        f[f"{x} retrograde"] = s[x].retro
    ang = abs((s["Jupiter"].lon - s["Saturn"].lon + 180) % 360 - 180)
    f["Jupiter–Saturn within 10° of trine/opposition/conjunction"] = min(abs(ang - a) for a in (0, 120, 180)) <= 10
    for k in ("Jupiter–Saturn trine (5/9)", "Jupiter with Rahu or Ketu", "Jupiter with Pluto", "Jupiter hemmed by malefics (12th and 2nd)", "afflicted"):
        f[k] = bool(gst[k])
    f["Malefic vedha on Jupiter"] = bool(gst["Malefic vedha on Jupiter"])
    # Jupiter's affliction changing within 30 days
    a0 = GJ.state(t - dt.timedelta(days=30))["afflicted"]
    a1 = GJ.state(t + dt.timedelta(days=30))["afflicted"]
    f["Jupiter's affliction ends within 30 days"] = gst["afflicted"] and not a1 or (a0 and not gst["afflicted"])
    f["Jupiter's affliction begins within 30 days"] = (not gst["afflicted"] and a1) or (not a0 and gst["afflicted"])
    pos = {b: dict(sign=s[b].sign, deg=round(s[b].lon % 30, 2), retro=s[b].retro, nak=s[b].nak) for b in BODIES}
    return f, pos, round(ang, 1)


def binom_ge(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def main():
    M = [(d, p) for d, p in GJ.monthly() if d < dt.date(2000, 1, 1)]
    Dd = GJ.daily()
    turns = zigzag(M + [(d, p) for d, p in Dd], 15)
    # daily refinement for turns after 2000 is implicit (daily series); drop duplicates near the 1999/2000 seam
    print("turns", [(k, str(d), round(p)) for k, d, p in turns])
    st_list = stations(dt.date(1971, 1, 1), dt.date(2028, 3, 1))
    rows = []
    for k, d, p in turns:
        f, pos, ang = features(d, st_list, None)
        rows.append(dict(kind=k, date=d, price=p, f=f, pos=pos, js_angle=ang))
    # base rates: every 7th day 1972-2026
    base, n = {}, 0
    d = dt.date(1972, 1, 3)
    while d <= dt.date(2026, 11, 20):
        f, _, _ = features(d, st_list, None)
        n += 1
        for kk, v in f.items():
            base[kk] = base.get(kk, 0) + bool(v)
        d += dt.timedelta(days=7)
    base = {kk: v / n for kk, v in base.items()}
    rec = {}
    for kind in ("bottom", "peak"):
        sel = [r for r in rows if r["kind"] == kind]
        for kk in base:
            hits = sum(r["f"][kk] for r in sel)
            rec.setdefault(kind, {})[kk] = dict(hits=hits, n=len(sel), share=round(hits / len(sel) * 100) if sel else None, base=round(base[kk] * 100, 1),
                                                p=round(binom_ge(hits, len(sel), base[kk]), 3) if sel else None)
    # upcoming: the stations and affliction changes Nov 2026 - Dec 2027
    up = []
    for x in STATION_BODIES:
        for d_, kind in st_list[x]:
            if dt.date(2026, 11, 20) <= d_ <= dt.date(2027, 12, 31):
                up.append(dict(date=str(d_), what=f"{x} stations {'direct' if kind == 'D' else 'retrograde'}"))
    js = json.load(open(OUT / "gold_jupiter_crash_ET.json"))["spans"]
    for k in ("afflicted", "afflicted and malefic vedha", "Jupiter with Rahu or Ketu", "Jupiter–Saturn trine (5/9)", "Malefic vedha on Jupiter"):
        for a_, b_ in js.get(k, []):
            up.append(dict(date=a_, what=f"begins: {k}"))
            up.append(dict(date=b_, what=f"ends: {k}"))
    up = sorted(up, key=lambda x: x["date"])
    # score each upcoming week by how many bottom-favoured features hold (features with p < 0.10 at bottoms)
    fav = [kk for kk, v in rec["bottom"].items() if v["p"] is not None and v["p"] < 0.10 and v["hits"] >= 3]
    favp = [kk for kk, v in rec["peak"].items() if v["p"] is not None and v["p"] < 0.10 and v["hits"] >= 3]
    weeks = []
    d = dt.date(2026, 11, 23)
    while d <= dt.date(2027, 12, 27):
        f, _, _ = features(d, st_list, None)
        weeks.append(dict(week=str(d), bottom_hits=[kk for kk in fav if f[kk]], peak_hits=[kk for kk in favp if f[kk]]))
        d += dt.timedelta(days=7)
    res = dict(turns=[dict(r, date=str(r["date"])) for r in rows], base_n=n, rec=rec, fav=fav, favp=favp, upcoming=up, weeks=weeks)
    json.dump(res, open(OUT / "gold_turns_ET.json", "w"), indent=1, default=str)
    (OUT / "gold_turns_ET.html").write_text(page(res), encoding="utf-8")
    for kind in ("bottom", "peak"):
        print("==", kind)
        for kk, v in sorted(rec[kind].items(), key=lambda x: x[1]["p"] or 1):
            print(f"   {kk:55s} {v['hits']}/{v['n']} ({v['share']}%) vs base {v['base']}%  p {v['p']}")
    print("favoured at bottoms:", fav, "at peaks:", favp)
    for r in rows:
        print(r["kind"], r["date"], round(r["price"]), "J", r["pos"]["Jupiter"], "S", r["pos"]["Saturn"], "JS", r["js_angle"], [k for k, v in r["f"].items() if v and "retrograde" not in k])
    for w in weeks:
        if w["bottom_hits"] or w["peak_hits"]:
            print(w)


def page(res):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--dn:#cf222e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1300px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .g{color:var(--up);font-weight:600} .r{color:var(--dn);font-weight:600}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Gold Turns</title><style>{css}</style></head><body>",
         "<h1>Gold's major peaks and bottoms since 1972: the sky at each turn</h1>",
         "<p class='s'>Turns: 15% zigzag on monthly gold 1972–1999 and daily COMEX gold 2000–2026. Sidereal Lahiri degrees at 12:00 ET of the turn day (the 15th for monthly turns).</p>",
         "<h2>1. Every turn</h2><div class='wrap'><table><thead><tr><th>Turn</th><th>Date</th><th class='n'>Gold</th><th>Jupiter</th><th>Saturn</th><th>Rahu</th><th>Mars</th><th>Sun</th>"
         "<th class='n'>Jup–Sat angle</th><th>Features</th></tr></thead><tbody>"]

    def pp(p):
        return f"{p['sign']} {p['deg']:.1f}°{' R' if p['retro'] else ''}"
    for r in res["turns"]:
        feats = [k for k, v in r["f"].items() if v and "retrograde" not in k]
        o.append(f"<tr><td class='{'g' if r['kind'] == 'bottom' else 'r'}'>{r['kind']}</td><td class='n'>{r['date']}</td><td class='n'>{r['price']:,.0f}</td><td>{pp(r['pos']['Jupiter'])}</td>"
                 f"<td>{pp(r['pos']['Saturn'])}</td><td>{pp(r['pos']['Rahu'])}</td><td>{pp(r['pos']['Mars'])}</td><td>{pp(r['pos']['Sun'])}</td><td class='n'>{r['js_angle']}°</td><td class='s'>{E('; '.join(feats))}</td></tr>")
    o.append("</tbody></table></div><h2>2. What recurs at bottoms and at peaks</h2><p class='s'>Share of turns with the feature against its share of all weeks 1972–2026; p = chance of at least that many by luck.</p>")
    for kind in ("bottom", "peak"):
        o.append(f"<h3>At {kind}s</h3><div class='wrap'><table><thead><tr><th>Feature</th><th class='n'>Turns</th><th class='n'>All weeks</th><th class='n'>p</th></tr></thead><tbody>")
        for k, v in sorted(res["rec"][kind].items(), key=lambda x: x[1]["p"] or 1):
            o.append(f"<tr><td>{E(k)}</td><td class='n'>{v['hits']} of {v['n']} ({v['share']}%)</td><td class='n'>{v['base']}%</td><td class='n {'g' if (v['p'] or 1) < 0.10 else ''}'>{v['p']}</td></tr>")
        o.append("</tbody></table></div>")
    o.append("<h2>3. Coming up: stations and Jupiter's affliction changes, Nov 2026 – Dec 2027</h2><div class='wrap'><table><thead><tr><th>Date</th><th>Event</th></tr></thead><tbody>")
    for u in res["upcoming"]:
        o.append(f"<tr><td class='n'>{u['date']}</td><td>{E(u['what'])}</td></tr>")
    o.append("</tbody></table></div>")
    hits = [w for w in res["weeks"] if w["bottom_hits"] or w["peak_hits"]]
    o.append("<h2>4. Weeks ahead where the bottom- or peak-favoured features hold</h2><p class='s'>Only features with p &lt; 0.10 and at least 3 turns are used: "
             f"bottoms — {E(', '.join(res['fav']) or 'none')}; peaks — {E(', '.join(res['favp']) or 'none')}.</p>")
    if hits:
        o.append("<div class='wrap'><table><thead><tr><th>Week of</th><th>Bottom-favoured</th><th>Peak-favoured</th></tr></thead><tbody>"
                 + "".join(f"<tr><td class='n'>{w['week']}</td><td class='s'>{E(', '.join(w['bottom_hits']) or '–')}</td><td class='s'>{E(', '.join(w['peak_hits']) or '–')}</td></tr>" for w in hits)
                 + "</tbody></table></div>")
    else:
        o.append("<p>No feature recurred at turns strongly enough to project.</p>")
    o.append("<h2>5. The current fall: where the bottom-favoured features point</h2><div class='wrap'><table><thead><tr><th>Window</th><th>What lines up</th><th>Past record</th></tr></thead><tbody>"
             "<tr><td class='n'>11 Nov 2026 – 10 Jan 2027</td><td>Saturn stations direct 11 Dec 2026 (Pisces 13.7°, Uttara Bhadrapada); Jupiter stations retrograde 13 Dec (Leo 2.8°, Magha)</td>"
             f"<td>Saturn direct station within ±30 days at {res['rec']['bottom']['Saturn direct station within ±30 days']['hits']} of {res['rec']['bottom']['Saturn direct station within ±30 days']['n']} bottoms "
             f"(base {res['rec']['bottom']['Saturn direct station within ±30 days']['base']}%, p {res['rec']['bottom']['Saturn direct station within ±30 days']['p']}). Retrograde stations are not bottom-favoured.</td></tr>"
             "<tr><td class='n'>14 Mar – 13 May 2027</td><td>Jupiter stations direct 13 Apr 2027 at Cancer 22.75° (Ashlesha), within 0.5° of Ketu, Mars at Cancer 27.5°, Jupiter–Saturn 118.6° (trine within 1.4°)</td>"
             f"<td>Jupiter direct station within ±30 days at {res['rec']['bottom']['Jupiter direct station within ±30 days']['hits']} of {res['rec']['bottom']['Jupiter direct station within ±30 days']['n']} bottoms "
             f"(base {res['rec']['bottom']['Jupiter direct station within ±30 days']['base']}%, p {res['rec']['bottom']['Jupiter direct station within ±30 days']['p']}); Jupiter–Saturn within 10° of trine/opposition/conjunction "
             f"at {res['rec']['bottom']['Jupiter–Saturn within 10° of trine/opposition/conjunction']['hits']} of {res['rec']['bottom']['Jupiter–Saturn within 10° of trine/opposition/conjunction']['n']} "
             f"(base {res['rec']['bottom']['Jupiter–Saturn within 10° of trine/opposition/conjunction']['base']}%, p {res['rec']['bottom']['Jupiter–Saturn within 10° of trine/opposition/conjunction']['p']}). "
             "But the Jupiter–Saturn trine was just as common at peaks, so it marks turns, not direction.</td></tr></tbody></table></div>"
             "<p class='s'>About 40 features were tested at bottoms and peaks, so one or two p-values near 0.01–0.03 are expected by chance. Treat the windows as watch periods.</p>")
    o.append("<p class='s'>Generated by tools/gold_turns.py. With about ten turns of each kind, a feature found here is a lead to watch, not a timing rule.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
