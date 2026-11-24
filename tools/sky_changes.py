"""Every planetary change between two dates (US Eastern), with times in ET and IST.

    python tools/sky_changes.py START END        # dates inclusive, e.g. 2026-11-20 2026-11-23

Lists, in time order:
  * astronomy-layer events (exact): sign, nakshatra and navamsa ingresses, tithi / karana (Vishti =
    Bhadra) / yoga changes, lunations, eclipses, stations, combustion and rising, conjunctions and
    oppositions, speed crossings, apsides;
  * pada changes of every body (computed on a 10-minute grid);
  * whole-sign aspects that begin or end (project drishti: all planets 7th, Mars 4/8, Jupiter 5/9,
    Saturn 3/10, Rahu 7th; conjunction = same sign; Ketu by conjunction only);
  * exact degree aspects perfected (0, 60, 90, 120, 180 degrees, sidereal longitudes; informational);
  * catalogue rules (gold, silver and general-market sets) that start or end, with their 26-year status;
plus a daily position table (sign, degree, nakshatra-pada, navamsa, speed, motion at 00:00 and 23:59 ET).
Writes build/pdfref/sky_changes_<start>_to_<end>_ET.{html,json}.
"""
from __future__ import annotations

import datetime as dt
import html
import importlib.util
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import parse  # noqa: E402
from finastro.pdfref.detect import aspects  # noqa: E402
from finastro.pdfref.engine import snapshot  # noqa: E402

ET = ZoneInfo("America/New_York")
IST = ZoneInfo("Asia/Kolkata")
OUT = ROOT / "build" / "pdfref"
G9 = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
ALL = G9 + ("Uranus", "Neptune", "Pluto")
STEP = dt.timedelta(minutes=10)
EXACT = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine", 180: "opposition"}


def stamp(t):
    e, i = t.astimezone(ET), t.astimezone(IST)
    return f"{e:%a %d %b %H:%M} {e.tzname()}", f"{i:%a %d %b %H:%M} IST"


def layer_events(a, b):
    out = []
    for y in sorted({a.year, b.year}):
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            ec, fam, bod = r["event_class"], r.get("rule_family", ""), r["bodies"]
            if ec in ("sunrise", "sunset", "total_day") or not bod:
                continue
            t = parse(r["time"]["t_start_utc"])
            if not (a <= t < b):
                continue
            x = r.get("astronomy", {})
            p = bod[0]
            pos = f"{x.get('sign', '')} {x.get('lon_sid', 0) % 30:.2f}°" if x.get("lon_sid") is not None else ""
            if ec == "sign_ingress":
                txt, kind = f"{p} enters {x.get('sign_to')} (from {x.get('sign_from')})", "sign change"
            elif ec == "nakshatra_ingress":
                txt, kind = f"{p} enters {x.get('nakshatra_to')} nakshatra (from {x.get('nakshatra_from')}) in {x.get('sign')}", "nakshatra change"
            elif ec == "navamsa_ingress":
                txt, kind = f"{p} navamsa (D9) {x.get('navamsa_from')} → {x.get('navamsa_to')}", "navamsa change"
            elif ec == "tithi_ingress":
                txt, kind = f"Tithi {x.get('tithi_name_from')} → {x.get('tithi_name_to')} ({x.get('paksha_to')} paksha)", "tithi"
            elif ec == "karana_ingress":
                to, fr = x.get("karana_name_to"), x.get("karana_name_from")
                txt = f"Karana {fr} → {to}" + (" — Bhadra (Vishti) begins" if to == "Vishti" else " — Bhadra (Vishti) ends" if fr == "Vishti" else "")
                kind = "karana"
            elif ec == "yoga_ingress":
                txt, kind = f"Yoga {x.get('yoga_name_from')} → {x.get('yoga_name_to')}", "yoga"
            elif ec == "lunation":
                txt, kind = f"{fam.split('/')[-1].replace('_', ' ').title()} in {x.get('sign')} / {x.get('nakshatra')}", "lunation"
            elif ec == "station":
                txt, kind = f"{p} stations {'retrograde' if fam.endswith('_R') else 'direct'}", "station"
            elif ec == "combustion":
                txt, kind = f"{p} {'becomes combust' if fam.endswith('combust') else 'rises from combustion'}", "combustion"
            elif ec in ("conjunction", "opposition"):
                txt, kind = f"{bod[0]}–{bod[1]} exact {ec}", "exact aspect"
            elif ec == "eclipse":
                txt, kind = f"{'Solar' if 'solar' in fam else 'Lunar'} eclipse", "eclipse"
            else:
                txt, kind = f"{ec.replace('_', ' ')}: {', '.join(bod)} ({fam})", ec.replace("_", " ")
            out.append(dict(t=t, kind=kind, text=txt, pos=pos, exact=True))
    return out


def grid(a, b):
    t, out = a, []
    while t <= b:
        out.append((t, snapshot(t)))
        t += STEP
    return out


def relations(s):
    rel = set()
    for i, p in enumerate(G9):
        for q in G9[i + 1:]:
            if {p, q} == {"Rahu", "Ketu"}:
                continue
            if s[p].sign_i == s[q].sign_i:
                rel.add((p, q, "together in " + s[p].sign))
                continue
            for x, y in ((p, q), (q, p)):
                if x == "Ketu":
                    continue
                if aspects(s, x, y):
                    h = (s[y].sign_i - s[x].sign_i) % 12 + 1
                    rel.add((x, y, f"{x} aspects {y} ({h}{'rd' if h == 3 else 'th'} house)"))
    return rel


def computed_events(G):
    out = []
    for (t0, s0), (t1, s1) in zip(G, G[1:]):
        for p in ALL:
            if s0[p].pada != s1[p].pada or s0[p].nak != s1[p].nak:
                if s0[p].nak == s1[p].nak or p in ("Uranus", "Neptune", "Pluto"):
                    out.append(dict(t=t1, kind="pada change", text=f"{p} {s1[p].nak} pada {s0[p].pada} → {s1[p].pada}", pos=f"{s1[p].sign} {s1[p].lon % 30:.2f}°", exact=False))
            if s0[p].retro != s1[p].retro and p not in ("Rahu", "Ketu"):
                out.append(dict(t=t1, kind="station", text=f"{p} turns {'retrograde' if s1[p].retro else 'direct'}", pos=f"{s1[p].sign} {s1[p].lon % 30:.2f}°", exact=False))
        r0, r1 = relations(s0), relations(s1)
        for x in sorted(r1 - r0):
            out.append(dict(t=t1, kind="aspect begins", text=x[2], pos="", exact=False))
        for x in sorted(r0 - r1):
            out.append(dict(t=t1, kind="aspect ends", text=x[2] + " — ends", pos="", exact=False))
        for i, p in enumerate(ALL):
            for q in ALL[i + 1:]:
                if {p, q} == {"Rahu", "Ketu"}:
                    continue
                d0 = (s0[q].lon - s0[p].lon) % 360
                d1 = (s1[q].lon - s1[p].lon) % 360
                for ang, name in EXACT.items():
                    for target in {ang, (360 - ang) % 360}:
                        a0 = (d0 - target + 180) % 360 - 180
                        a1 = (d1 - target + 180) % 360 - 180
                        if a0 * a1 < 0 and abs(a0 - a1) < 30:
                            out.append(dict(t=t1, kind="exact degree aspect", text=f"{p}–{q} exact {name} ({ang}°)",
                                            pos=f"{p} {s1[p].sign} {s1[p].lon % 30:.2f}°, {q} {s1[q].sign} {s1[q].lon % 30:.2f}°", exact=False))
    return out


def rule_changes(a, b):
    spec = importlib.util.spec_from_file_location("bt", ROOT / "tools" / "backtest_gold.py")
    B = importlib.util.module_from_spec(spec)
    sys.modules["bt"] = B
    spec.loader.exec_module(B)
    from finastro.sky import Sky
    from finastro.pdfref.detect import Ctx
    from finastro.pdfref.engine import Grid, utc
    T = importlib.util.module_from_spec(importlib.util.spec_from_file_location("gt", ROOT / "tools" / "gold_tracker.py"))
    T.__spec__.loader.exec_module(T)
    status = {}
    for metal in ("gold", "silver"):
        for r in json.load(open(OUT / f"{metal}_backtest_2000-11-20_to_2026-11-20_ET.json"))["rules"]:
            status[(metal, r["rule_id"])] = T.status(r)
    for x in json.load(open(OUT / "market_backtest_2000-2026_ET.json"))["rules"]:
        st = [f"{k}: {x[k]['status']}" for k in ("spx", "sensex") if x[k]]
        status[("general", x["rule_id"].split("::")[0])] = "; ".join(st)
    grid_ = Grid(utc(a.year - 1, 6, 1), utc(b.year + 1, 6, 30))
    ctxs = [Ctx(grid_, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in (a.year - 1, a.year, a.year + 1) if (ROOT / "build" / f"astronomy_{y}.json").exists()]
    out = []
    for metal in ("gold", "silver", "general"):
        if metal == "general":
            B.M.METAL = "general"
            B.M.EXCLUDE["general"] = set()
            B.M.EXTRA["general"] = []
            B.METAL = "general"
        else:
            B.configure_metal(metal)
        B.P0, B.P1 = a - dt.timedelta(days=1), b + dt.timedelta(days=1)
        for e in B.collect(ctxs):
            if e["tone"] not in ("Bullish", "Bearish") or e["day"] is not None:          # Mixed / Neutral rules are not scored
                continue
            st = status.get((metal, e["rule_id"]), "")
            if a <= e["start"] < b:
                out.append(dict(t=e["start"], kind=f"rule starts ({metal})", text=f"{e['title']} — {e['tone']}", pos=st, exact=True))
            if e["end"] and a <= e["end"] < b and (e["end"] - e["start"]).total_seconds() > 3600:
                out.append(dict(t=e["end"], kind=f"rule ends ({metal})", text=f"{e['title']} — {e['tone']}", pos=st, exact=True))
    seen, uniq = set(), []
    for x in out:
        k = (x["kind"], x["text"], x["t"].replace(second=0, microsecond=0))
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq


def daily(G, a_day, b_day):
    rows = []
    d = a_day
    while d <= b_day:
        t0 = dt.datetime.combine(d, dt.time(0), ET)
        t1 = dt.datetime.combine(d, dt.time(23, 59), ET)
        s0, s1 = snapshot(t0.astimezone(dt.timezone.utc)), snapshot(t1.astimezone(dt.timezone.utc))
        for p in ALL:
            b0, b1 = s0[p], s1[p]
            rows.append(dict(day=str(d), planet=p, start=f"{b0.sign} {b0.lon % 30:.2f}°", end=f"{b1.sign} {b1.lon % 30:.2f}°",
                             moved=round(((b1.lon - b0.lon + 180) % 360) - 180, 3), nak=f"{b0.nak} {b0.pada}" + ("" if (b0.nak, b0.pada) == (b1.nak, b1.pada) else f" → {b1.nak} {b1.pada}"),
                             nav=b0.nav + ("" if b0.nav == b1.nav else f" → {b1.nav}"), retro="R" if b1.retro and p not in ("Rahu", "Ketu") else ""))
        d += dt.timedelta(days=1)
    return rows


def main():
    a_day = dt.date.fromisoformat(sys.argv[1])
    b_day = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else a_day
    a = dt.datetime.combine(a_day, dt.time(0), ET).astimezone(dt.timezone.utc)
    b = dt.datetime.combine(b_day + dt.timedelta(days=1), dt.time(0), ET).astimezone(dt.timezone.utc)
    G = grid(a, b)
    ev = layer_events(a, b)
    have = {(x["text"].split(" (")[0]) for x in ev}
    comp = [x for x in computed_events(G) if not (x["kind"] == "station" and any("stations" in h for h in have))]
    # drop computed exact conjunction/opposition already given exactly by the layer
    layer_pairs = {x["text"] for x in ev if x["kind"] == "exact aspect"}
    comp = [x for x in comp if not (x["kind"] == "exact degree aspect" and any(x["text"].startswith(lp.split(" exact")[0]) for lp in layer_pairs))]
    rules = rule_changes(a, b)
    allev, seen = [], set()
    for x in sorted(ev + comp + rules, key=lambda x: (x["t"], x["kind"])):   # the astronomy layers of adjacent years overlap
        k = (x["kind"], x["text"], x["t"].replace(second=0, microsecond=0))
        if k not in seen:
            seen.add(k)
            allev.append(x)
    for x in allev:
        x["et"], x["ist"] = stamp(x["t"])
    rows = daily(G, a_day, b_day)
    res = dict(start=str(a_day), end=str(b_day), events=[{k: v for k, v in x.items() if k != "t"} | {"utc": x["t"].isoformat()} for x in allev], daily=rows)
    stem = f"sky_changes_{a_day}_to_{b_day}_ET"
    json.dump(res, open(OUT / f"{stem}.json", "w"), indent=1, default=str)
    (OUT / f"{stem}.html").write_text(page(res, allev, rows), encoding="utf-8")
    import collections
    print(stem, len(allev), collections.Counter(x["kind"] for x in allev))
    for x in allev:
        if x["kind"] not in ("pada change", "navamsa change") or not x["text"].startswith("Moon"):
            print(f"  {x['et']:24s} | {x['ist']:22s} | {x['kind']:22s} | {x['text']} {('| ' + x['pos']) if x['pos'] else ''}")


def page(res, allev, rows):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    cls = {"sign change": "bullish", "nakshatra change": "mixed", "station": "bearish", "lunation": "bearish", "eclipse": "bearish", "exact aspect": "mixed", "exact degree aspect": "mixed"}
    erows = "".join(f"<tr class='{cls.get(x['kind'], '')}'><td class='w'>{x['et']}</td><td class='w s'>{x['ist']}</td><td>{x['kind']}{'' if x['exact'] else ' <span class=s>(±10 min)</span>'}</td>"
                    f"<td><b>{html.escape(x['text'])}</b></td><td class='s'>{html.escape(x['pos'])}</td></tr>" for x in allev)
    drows = "".join(f"<tr><td class='w'>{r['day']}</td><td><b>{r['planet']}</b></td><td class='n'>{r['start']}</td><td class='n'>{r['end']}</td><td class='n'>{r['moved']:+.3f}°</td>"
                    f"<td>{r['nak']}</td><td>{r['nav']}</td><td>{r['retro']}</td></tr>" for r in rows)
    a, b = res["start"], res["end"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sky Changes {a}</title><style>{css}</style></head><body>
<h1>Every planetary change, {dt.date.fromisoformat(a):%a %d %b} – {dt.date.fromisoformat(b):%a %d %b %Y} (US Eastern, IST alongside)</h1>
<p class="m">Sidereal Lahiri, mean node, whole-sign drishti. Exact times come from the astronomy layer; pada changes, aspect starts / ends and exact degree aspects are found on a 10-minute grid.
Rule starts / ends are the catalogue's gold, silver and general-market rules with their 26-year status.</p>
<h2>Timeline</h2>
<div class="wrap"><table><thead><tr><th>US Eastern</th><th>IST</th><th>Kind</th><th>Change</th><th>Position / status</th></tr></thead><tbody>{erows}</tbody></table></div>
<h2>Daily positions (00:00 and 23:59 ET)</h2>
<div class="wrap"><table><thead><tr><th>Day</th><th>Planet</th><th>00:00</th><th>23:59</th><th>Moved</th><th>Nakshatra, pada</th><th>Navamsa</th><th>Motion</th></tr></thead><tbody>{drows}</tbody></table></div>
<p class="s">Generated by tools/sky_changes.py.</p></body></html>"""


if __name__ == "__main__":
    main()
