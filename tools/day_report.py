"""Everything our work says about one day: planet positions, panchang, every rule active, its 26-year
record, the signal tables, the volatility watch, and (when the day has traded) what markets did.

    python tools/day_report.py [YYYY-MM-DD]        # default: today (US Eastern)

Active rules: every catalogue rule (gold set, silver set, general-market set) whose window covers the
day, plus instants of the previous four sessions (still inside their 5-session scoring horizon);
the calendar layer's rows for the day (SPX, NIFTY, GC, SI). Each comes with its 26-year record
(gold / silver backtests, market backtest, calendar-rules backtest) and the tracker's status.
Writes build/pdfref/day_report_<date>_ET.{html,json}.
"""
from __future__ import annotations

import datetime as dt
import gzip
import html
import importlib.util
import json
import pathlib
import subprocess
import sys
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky  # noqa: E402
from finastro.pdfref.detect import Ctx  # noqa: E402
from finastro.pdfref.engine import Grid, snapshot, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
PL = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto")
EXALT = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"}
DEBIL = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"}
OWN = {"Sun": ("Leo",), "Moon": ("Cancer",), "Mars": ("Aries", "Scorpio"), "Mercury": ("Gemini", "Virgo"), "Jupiter": ("Sagittarius", "Pisces"),
       "Venus": ("Taurus", "Libra"), "Saturn": ("Capricorn", "Aquarius")}
COMBUST = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
WEEKDAY_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
TICK = {"S&P 500": ("%5EGSPC", "America/New_York"), "Nasdaq": ("%5EIXIC", "America/New_York"), "BSE Sensex": ("%5EBSESN", "Asia/Kolkata"),
        "Gold (GC=F)": ("GC%3DF", "America/New_York"), "Silver (SI=F)": ("SI%3DF", "America/New_York")}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def positions(day):
    s = snapshot(dt.datetime(day.year, day.month, day.day, 12, tzinfo=ET).astimezone(dt.timezone.utc))
    rows = []
    for p in PL:
        b = s[p]
        dig = "exalted" if EXALT.get(p) == b.sign else "debilitated" if DEBIL.get(p) == b.sign else "own sign" if b.sign in OWN.get(p, ()) else ""
        sep = min((b.lon - s["Sun"].lon) % 360, (s["Sun"].lon - b.lon) % 360)
        comb = p in COMBUST and sep <= COMBUST[p]
        rows.append(dict(planet=p, sign=b.sign, deg=f"{int(b.lon % 30)}°{int((b.lon % 1) * 60):02d}'", nakshatra=f"{b.nak} {b.pada}",
                         retro=bool(b.retro) and p not in ("Rahu", "Ketu"), dignity=dig, combust=comb, speed=round(b.speed, 3)))
    together = {}
    for p in PL[:9]:
        together.setdefault(s[p].sign, []).append(p)
    pan = dict(weekday=day.strftime("%A"), day_lord=WEEKDAY_LORD[day.weekday()], tithi=s.tithi, paksha=s.paksha, moon_nakshatra=s["Moon"].nak,
               yoga=s.yoga if not callable(s.yoga) else s.yoga(), groups={k: v for k, v in together.items() if len(v) > 1})
    return rows, pan


def active_rules(day):
    """Catalogue events active on the day for the gold, silver and general-market rule sets."""
    B = load(ROOT / "tools" / "backtest_gold.py", "bt")
    out = []
    p0 = dt.datetime.combine(day - dt.timedelta(days=7), dt.time(0), ET)
    p1 = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(0), ET)
    grid = Grid(utc(day.year - 1, 6, 1), utc(day.year + 1, 6, 30))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in (day.year - 1, day.year, day.year + 1)
            if (ROOT / "build" / f"astronomy_{y}.json").exists()]
    d0 = dt.datetime.combine(day, dt.time(0), ET)
    d1 = d0 + dt.timedelta(days=1)
    for metal in ("gold", "silver", "general"):
        if metal == "general":
            B.M.METAL = "general"
            B.M.EXCLUDE["general"] = set()
            B.M.EXTRA["general"] = []
            B.METAL = "general"
        else:
            B.configure_metal(metal)
        B.P0, B.P1 = p0, p1
        for e in B.collect(ctxs):
            if e["tone"] not in ("Bullish", "Bearish", "Mixed", "Neutral"):
                continue
            if e["day"] is not None:
                ok, kind = e["day"] == day, "day rule"
            elif e["end"] and (e["end"] - e["start"]).days >= 1:
                ok, kind = e["start"] < d1 and e["end"] >= d0, "window"
            else:
                t = e["start"].astimezone(ET)
                ok, kind = (d0 - dt.timedelta(days=6) <= t < d1), ("instant today" if t >= d0 else f"instant {t:%d %b} (5-session horizon)")
            if ok:
                out.append(dict(set=metal, rule_id=e["rule_id"], title=e["title"], tone=e["tone"], refs="; ".join(e["refs"]), kind=kind,
                                start=e["start"].astimezone(ET).strftime("%d %b %H:%M") if e["start"] else str(e["day"]),
                                end=e["end"].astimezone(ET).strftime("%d %b %H:%M") if e["end"] else ""))
    seen, uniq = set(), []
    for x in out:
        k = (x["set"], x["rule_id"], x["tone"], x["start"])
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq


def records():
    T = load(ROOT / "tools" / "gold_tracker.py", "gt")
    rec = {}
    for metal in ("gold", "silver"):
        f = OUT / f"{metal}_backtest_2000-11-20_to_2026-11-20_ET.json"
        for r in json.load(open(f))["rules"]:
            dec = r["worked"] + r["failed"]
            rec[(metal, r["rule_id"])] = dict(text=f"{r['worked']}/{dec} ({r['hit_rate']}% vs {r['base_rate']}%), p {r.get('p_value')}" if dec else "no decided cases",
                                              status=T.status(r))
    mb = json.load(open(OUT / "market_backtest_2000-2026_ET.json"))
    for x in mb["rules"]:
        for k in ("spx", "sensex"):
            r = x[k]
            if r:
                rec[(k, x["rule_id"])] = dict(text=f"{r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%), p {r['p_value']}", status=r["status"])
    return rec


def calendar_rows(day):
    f = OUT / "backtest" / "calendar_verdicts" / f"{day.year}.json.gz"
    if not f.exists():
        subprocess.run([sys.executable, "tools/calendar_rules_backtest.py", "--gen", str(day.year)], cwd=ROOT, check=True)
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        rows = [r for r in json.load(fh) if r["date"] == day.isoformat()]
    cb = json.load(open(OUT / "calendar_rules_backtest_2000-2026_ET.json"))
    mk = {"SPX": "spx", "NIFTY": "sensex", "GC": "gold", "SI": "silver"}
    by = {}
    for x in cb["rules"]:
        for m in mk.values():
            r = x.get(m)
            if r:
                if r["kind"] == "direction" and r["worked"] + r["failed"]:
                    t = f"{r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%), p {r['p_value']}"
                elif r["kind"] == "volatility" and r.get("n_episodes"):
                    t = f"big day in {r['big']} of {r['n_episodes']} episodes vs {r['big_exp']} expected"
                else:
                    t = "–"
                by[(x["rule_id"], m)] = t
    out = []
    for r in rows:
        m = mk[r["instrument"]]
        out.append(dict(rule_id=r["rule_id"], market=m, verdict=r["verdict"] or "condition only", provenance=r["provenance"], record=by.get((r["rule_id"], m), "–")))
    return out


def table_signals(day):
    out = {}
    for name, f, key in (("Gold", "gold_signals_2026-11-22_to_2027-12-31_ET.json", None), ("Silver", "silver_signals_2026-11-22_to_2027-12-31_ET.json", None),
                         ("S&P 500", "market_signals_2026-11-23_to_2027-12-31_ET.json", "spx"), ("BSE Sensex", "market_signals_2026-11-23_to_2027-12-31_ET.json", "sensex")):
        p = OUT / f
        if not p.exists():
            continue
        j = json.load(open(p))
        rows = j["tables"][key] if key else j
        hit = [r for r in rows if str(r["frm"])[:10] <= day.isoformat() <= str(r["to"])[:10]]
        out[name] = [dict(sig=r["sig"], st=r["st"], why="; ".join(r["why"])) for r in hit] or [dict(sig="No signal", st="", why="no tested rule active")]
    watch = []
    for metal in ("gold", "silver", "spx", "sensex"):
        f = OUT / f"{metal}_big_move_watch_2026-11-22_to_2027-12-31_ET.json"
        if f.exists():
            for w in json.load(open(f))["windows"]:
                if w["frm"] <= day.isoformat() <= w["to"]:
                    watch.append(dict(market=metal, factor=w["factor"], exact=", ".join(w["exact"])))
    return out, watch


def actual(day):
    res = []
    for name, (sym, tz) in TICK.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=15d&interval=1d"
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30))["chart"]["result"][0]
            c = [(dt.datetime.fromtimestamp(t, ZoneInfo(tz)).date(), x) for t, x in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if x]
            m = r["meta"]
            last_t = dt.datetime.fromtimestamp(m["regularMarketTime"], ZoneInfo(tz)).date()
            if last_t == day and (not c or c[-1][0] != day):
                c.append((day, m["regularMarketPrice"]))
            prev = [x for x in c if x[0] < day]
            today = [x for x in c if x[0] == day]
            if prev and today:
                res.append(dict(market=name, prev=str(prev[-1][0]), prev_close=round(prev[-1][1], 2), close=round(today[0][1], 2),
                                change=round((today[0][1] / prev[-1][1] - 1) * 100, 2)))
        except Exception as ex:  # offline or blocked: leave it out
            res.append(dict(market=name, error=str(ex)[:80]))
    return res


def main():
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(ET).date()
    pos, pan = positions(day)
    act = active_rules(day)
    rec = records()
    for a in act:
        keys = [("gold", a["rule_id"]), ("silver", a["rule_id"])] if a["set"] in ("gold", "silver") else []
        a["record"] = {}
        if a["set"] in ("gold", "silver"):
            r = rec.get((a["set"], a["rule_id"]))
            a["record"][a["set"]] = r
        else:
            for k in ("spx", "sensex"):
                r = rec.get((k, a["rule_id"])) or rec.get((k, f"{a['rule_id']}::{a['tone']}"))
                a["record"][k] = r
        del keys
    cal = calendar_rows(day)
    sig, watch = table_signals(day)
    real = actual(day)
    res = dict(day=str(day), positions=pos, panchang=pan, rules=act, calendar=cal, signals=sig, watch=watch, actual=real)
    json.dump(res, open(OUT / f"day_report_{day}_ET.json", "w"), indent=1, default=str)
    write(res)
    print(pan)
    for p in pos:
        print(f"  {p['planet']:8s} {p['sign']:12s} {p['deg']:>7s} {p['nakshatra']:22s} {'R' if p['retro'] else ' '} {p['dignity']:12s} {'combust' if p['combust'] else ''}")
    print("signals:", sig)
    print("watch:", watch)
    print("actual:", real)
    good = [a for a in act if any(v and v["status"] in ("Strongest", "Supported", "Consistent") for v in a["record"].values())]
    print(f"{len(act)} catalogue rules active; {len(good)} with a supported 26-year record:")
    for a in good:
        print("   ", a["set"], a["tone"], a["title"], a["kind"], {k: (v['text'], v['status']) for k, v in a["record"].items() if v})
    print(f"{len(cal)} calendar rows")


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    day = dt.date.fromisoformat(res["day"])
    prow = "".join(f"<tr><td><b>{p['planet']}</b></td><td>{p['sign']}</td><td class='n'>{p['deg']}</td><td>{p['nakshatra']}</td><td>{'retrograde' if p['retro'] else ''}</td>"
                   f"<td>{p['dignity']}</td><td>{'combust' if p['combust'] else ''}</td></tr>" for p in res["positions"])
    pan = res["panchang"]
    groups = "; ".join(f"{k}: {', '.join(v)}" for k, v in pan["groups"].items()) or "none"

    def rtxt(a):
        return "<br>".join(f"{ {'gold': 'Gold', 'silver': 'Silver', 'spx': 'S&P', 'sensex': 'Sensex'}[k] }: {html.escape(v['text'])} – <i>{html.escape(v['status'])}</i>"
                           for k, v in a["record"].items() if v) or "–"

    def good(a):
        return any(v and v["status"] in ("Strongest", "Supported", "Consistent") for v in a["record"].values())
    rrows = "".join(f"<tr class='{('bullish' if a['tone'] == 'Bullish' else 'bearish' if a['tone'] == 'Bearish' else 'mixed') if good(a) else ''}'><td>{a['set']}</td><td><b>{html.escape(a['title'])}</b>"
                    f"<div class='s'>{html.escape(a['refs'])}</div></td><td>{a['tone']}</td><td class='s'>{a['kind']}<br>{a['start']}{' – ' + a['end'] if a['end'] else ''}</td><td class='s'>{rtxt(a)}</td></tr>"
                    for a in sorted(res["rules"], key=lambda a: (not good(a), a["set"], a["title"])))
    crow = "".join(f"<tr><td>{c['market']}</td><td><b>{html.escape(c['rule_id'])}</b><div class='s'>{html.escape(c['provenance'] or '')}</div></td><td class='s'>{html.escape(c['verdict'][:140])}</td>"
                   f"<td class='s'>{html.escape(c['record'])}</td></tr>" for c in res["calendar"])
    srow = "".join(f"<tr><td><b>{k}</b></td><td>{'<br>'.join(x['sig'] + ' ' + x['st'] for x in v)}</td><td class='s'>{html.escape(' | '.join(x['why'] for x in v))}</td></tr>" for k, v in res["signals"].items())
    wrow = "".join(f"<tr><td>{w['market']}</td><td>{html.escape(w['factor'])}</td><td class='s'>{w['exact'] or 'state / rule window'}</td></tr>" for w in res["watch"]) or "<tr><td colspan='3'>none</td></tr>"
    arow = "".join(f"<tr><td><b>{a['market']}</b></td><td class='n'>{a.get('prev', '')} {a.get('prev_close', '')}</td><td class='n'>{a.get('close', '')}</td>"
                   f"<td class='n'><b>{'' if 'change' not in a else format(a['change'], '+.2f') + '%'}</b></td></tr>" for a in res["actual"] if "error" not in a) or "<tr><td colspan='4'>not traded yet / prices unavailable</td></tr>"
    n_good = sum(1 for a in res["rules"] if good(a))
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Day Report {day}</title><style>{css}</style></head><body>
<h1>{day:%A %d %B %Y}: planets, rules and signals</h1>
<h2>What our published tables said</h2>
<div class="wrap"><table><thead><tr><th>Market</th><th>Signal</th><th>Why</th></tr></thead><tbody>{srow}</tbody></table></div>
<h3>Volatility watch windows covering the day</h3>
<div class="wrap"><table><thead><tr><th>Market</th><th>Factor</th><th>Exact</th></tr></thead><tbody>{wrow}</tbody></table></div>
<h2>What markets did</h2>
<div class="wrap"><table><thead><tr><th>Market</th><th>Previous close</th><th>This day</th><th>Change</th></tr></thead><tbody>{arow}</tbody></table></div>
<h2>Planet positions (12:00 ET, sidereal Lahiri, mean node)</h2>
<p class="m">{pan['weekday']} (day lord {pan['day_lord']}); tithi {pan['tithi']} ({pan['paksha']} paksha); Moon in {pan['moon_nakshatra']}; together in a sign: {html.escape(groups)}.</p>
<div class="wrap"><table><thead><tr><th>Planet</th><th>Sign</th><th>Degree</th><th>Nakshatra, pada</th><th>Motion</th><th>Dignity</th><th>Combust</th></tr></thead><tbody>{prow}</tbody></table></div>
<h2>Every catalogue rule active ({len(res['rules'])}; {n_good} with a supported 26-year record, coloured)</h2>
<div class="wrap"><table><thead><tr><th>Set</th><th>Rule</th><th>Says</th><th>When</th><th>26-year record</th></tr></thead><tbody>{rrows}</tbody></table></div>
<h2>Calendar layer rows for the day ({len(res['calendar'])})</h2>
<div class="wrap"><table><thead><tr><th>Market</th><th>Rule</th><th>Calendar verdict</th><th>26-year record</th></tr></thead><tbody>{crow}</tbody></table></div>
<p class="s">Generated by tools/day_report.py.</p></body></html>"""
    (OUT / f"day_report_{day}_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
