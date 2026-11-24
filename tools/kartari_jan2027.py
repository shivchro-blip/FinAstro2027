"""Mercury in Paap Kartari (2026 document B116), the S&P 500 and the BSE Sensex in January 2027: the windows, every
past window, and the past windows most like January's. Each market in its own exchange time (S&P: ET; Sensex: IST).

    python tools/kartari_jan2027.py

B116 says: "negative event for financial markets"; "result will be different if aspect by benefic planets: very
volatile and both side movement"; "if Mercury is combust, the impact is more profound if the malefic planets are
other than Sun". Each past window (2000-2026) is described by those conditions: which malefics hem Mercury
(Sun among them or not), Mercury combust at the start (within 14°), a benefic (Jupiter or Venus) aspecting Mercury's
sign at the start (whole-sign drishti, config valence), plus its length and month. Scoring: section 6 via
tools/backtest_market.py (entry = last close before the start, in the exchange's time; windows of 3+ days to the last close
inside, otherwise 5 sessions; FLAT < 0.5%; base = same horizon in the same Nov-Nov year). Big days = |move| >= 2%.
The January windows are then matched to the past windows that share their conditions.
Writes build/pdfref/kartari_jan2027_ET.{html,json}; tools/calendar_2026.py shows it as its January 2027 section.
"""
from __future__ import annotations

import bisect
import datetime as dt
import html
import json
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402

K = load(ROOT / "tools" / "kartari_test.py", "kt_jan")
BM = K.BM
IST = ZoneInfo("Asia/Kolkata")
ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
ASPECT = {"Jupiter": (1, 5, 7, 9), "Venus": (1, 7)}
FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
HOLIDAYS = {"spx": {dt.date(2027, 1, 1): "New Year's Day (NYSE closed)", dt.date(2027, 1, 18): "Martin Luther King Jr. Day (NYSE closed)"},
            "sensex": {dt.date(2027, 1, 26): "Republic Day (BSE closed)"}}
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex"}


def conditions(t):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    u = t.astimezone(UTC)
    jd = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60)
    lon = {b: swe.calc_ut(jd, k, FL)[0][0] % 360 for b, k in (("Mercury", swe.MERCURY), ("Sun", swe.SUN), ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS))}
    ms = int(lon["Mercury"] // 30)
    comb = abs((lon["Mercury"] - lon["Sun"] + 180) % 360 - 180) <= 14
    ben = [b for b, hs in ASPECT.items() if (ms - int(lon[b] // 30)) % 12 + 1 in hs]
    return dict(sign=SIGNS[ms], combust=comb, benefic=ben)


def describe(spans, M, tz):
    rows = []
    for a, b, pair in spans:
        pair = " | ".join(pair)
        e = dict(start=a.isoformat(), end=b.isoformat(), day=None, tone="Bearish")
        s = M.score(e)
        c = conditions(a)
        i0 = bisect.bisect_left(M.D, M.session_day(a))
        i1 = bisect.bisect_right(M.D, M.session_day(b))
        inside = list(range(max(i0, 1), min(i1, len(M.D))))
        big = sum(abs(M.C[i] / M.C[i - 1] - 1) >= 0.02 for i in inside)
        worst = min((M.C[i] / M.C[i0 - 1] - 1) * 100 for i in inside) if inside and i0 >= 1 else None
        rows.append(dict(start=a, end=b, pair=pair, sun="Sun" in pair, days=round((b - a).total_seconds() / 86400, 1), month=a.astimezone(tz).month, **c,
                         score=s, sessions=len(inside), big=big, worst=None if worst is None else round(worst, 2)))
    return rows


def record(rows, M):
    agg = BM.aggregate([(dict(tone="Bearish"), r["score"]) for r in rows if r["score"]], M)
    rets = [r["score"]["ret"] for r in rows if r["score"]]
    agg["median_ret"] = round(statistics.median(rets), 2) if rets else None
    agg["windows"] = len(rows)
    agg["big_per_window"] = round(sum(r["big"] for r in rows) / len(rows), 2) if rows else None
    return agg


def analyse(mk, allsp):
    M = BM.Market(mk)
    tz, close = BM.MARKETS[mk]["tz"], BM.MARKETS[mk]["close"]
    hols = HOLIDAYS[mk]
    hist = [s for s in allsp if dt.datetime(2000, 11, 20, tzinfo=UTC) <= s[0] < dt.datetime(2026, 11, 21, tzinfo=UTC)]
    jan = [s for s in allsp if dt.datetime(2026, 12, 25, tzinfo=UTC) <= s[0] < dt.datetime(2027, 2, 1, tzinfo=UTC)]
    rows = describe(hist, M, tz)
    janrows = []
    for a, b, pair in jan:
        pair = " | ".join(pair)
        c = conditions(a)
        d0, d1 = M.session_day(a), M.session_day(b)
        eloc = b.astimezone(tz)
        last = eloc.date() if eloc.time() >= close else eloc.date() - dt.timedelta(days=1)    # last close inside the window
        sess, x = [], d0
        while x <= last:
            if x.weekday() < 5 and x not in hols:
                sess.append(x)
            x += dt.timedelta(days=1)
        entry = d0 - dt.timedelta(days=1)
        while entry.weekday() >= 5 or entry in hols or entry == dt.date(2026, 12, 25):
            entry -= dt.timedelta(days=1)
        hol = [f"{h:%a %d %b} {hols[h]}" for h in hols if d0 - dt.timedelta(days=1) <= h <= d1]
        janrows.append(dict(sessions=sess, holidays=hol, entry=entry, start=a, end=b, pair=pair, sun="Sun" in pair, days=round((b - a).total_seconds() / 86400, 1), **c,
                            start_local=a.astimezone(tz), end_local=b.astimezone(tz), tz=("ET" if mk == "spx" else "IST")))
    groups = {"All B116 windows": rows,
              "Sun is one of the hemming malefics": [r for r in rows if r["sun"]],
              "Sun not among them": [r for r in rows if not r["sun"]],
              "Mercury combust at the start": [r for r in rows if r["combust"]],
              "Mercury combust, malefics other than the Sun (B116's 'more profound')": [r for r in rows if r["combust"] and not r["sun"]],
              "A benefic aspects Mercury (B116: volatile, both sides)": [r for r in rows if r["benefic"]],
              "No benefic aspect": [r for r in rows if not r["benefic"]],
              "Windows of 7+ days": [r for r in rows if r["days"] >= 7],
              "Windows under 2 days": [r for r in rows if r["days"] < 2],
              "Starting in December or January": [r for r in rows if r["month"] in (12, 1)]}
    for j in janrows:
        like = [r for r in rows if r["sun"] == j["sun"] and r["combust"] == j["combust"] and bool(r["benefic"]) == bool(j["benefic"])]
        groups[f"Like {j['start_local']:%d %b}: Sun {'in' if j['sun'] else 'not in'} pair, Mercury {'combust' if j['combust'] else 'not combust'}, "
               f"{'benefic aspect' if j['benefic'] else 'no benefic aspect'}"] = like
        if j["days"] >= 3:
            groups[f"Like {j['start_local']:%d %b} and also 7+ days long"] = [r for r in like if r["days"] >= 7]
    recs = {k: record(v, M) for k, v in groups.items() if v}
    sigs = json.load(open(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json"))["tables"][mk]
    table = [dict(frm=str(x["frm"])[:10], to=str(x["to"])[:10], sig=x["sig"], st=x["st"], why="; ".join(x["why"])) for x in sigs
             if str(x["to"])[:10] >= "2027-01-01" and str(x["frm"])[:10] <= "2027-01-31"]
    past = [dict(start=r["start"].astimezone(tz).strftime("%d %b %Y"), end=r["end"].astimezone(tz).strftime("%d %b %Y"), pair=r["pair"], days=r["days"],
                 sign=r["sign"], combust=r["combust"], benefic=r["benefic"], ret=None if not r["score"] else round(r["score"]["ret"], 2),
                 n=None if not r["score"] else r["score"]["n"], big=r["big"], worst=r["worst"]) for r in rows]
    return dict(name=NAME[mk], jan=janrows, groups=recs, table=table, past=past)


def main():
    allsp = K.spans_all("Mercury", "malefic")
    res = dict(markets={mk: analyse(mk, allsp) for mk in ("spx", "sensex")})
    json.dump(res, open(OUT / "kartari_jan2027_ET.json", "w"), indent=1, default=str)
    (OUT / "kartari_jan2027_ET.html").write_text(page(res), encoding="utf-8")
    for mk, m in res["markets"].items():
        print("==", m["name"])
        for j in m["jan"]:
            print(f"  JAN {j['start_local']:%a %d %b %H:%M} -> {j['end_local']:%a %d %b %H:%M} {j['tz']} {j['pair']} {j['days']}d {j['sign']} combust {j['combust']} benefic {j['benefic']} "
                  f"entry {j['entry']} sessions {[str(x) for x in j['sessions']]} {j['holidays']}")
        for k, v in m["groups"].items():
            print(f"  {k[:90]:90s} {v['windows']:3d} right {v['worked']}/{v['worked'] + v['failed']} = {v['hit_rate']}% vs {v['base_rate']}% p {v['p_value']} avg {v['avg_dir_ret']} med {v['median_ret']} big/w {v['big_per_window']}")
        for t in m["table"]:
            print("  ", t["frm"], t["to"], t["sig"], t["st"], t["why"][:90])


def section(m, E):
    o = [f"<h2>{E(m['name'])}</h2><h3>The January windows</h3><div class='wrap'><table><thead><tr><th>Window ({m['jan'][0]['tz'] if m['jan'] else ''})</th><th>Hemmed by</th>"
         "<th>Length</th><th>Mercury</th><th>Benefic aspect</th><th>Sessions (entry = close of)</th></tr></thead><tbody>"]
    for j in m["jan"]:
        ss = j["sessions"]
        o.append(f"<tr><td>{j['start_local']:%a %d %b %Y %H:%M} → {j['end_local']:%a %d %b %H:%M}</td><td>{E(j['pair'])}</td><td class='n'>{j['days']} days</td>"
                 f"<td>{j['sign']}{', combust' if j['combust'] else ''}</td><td>{E(', '.join(j['benefic']) or 'none')}</td>"
                 f"<td>{len(ss)}: {ss[0]:%a %d %b}{' – ' + format(ss[-1], '%a %d %b') if len(ss) > 1 else ''} (entry {j['entry']:%a %d %b}){'; ' + E('; '.join(j['holidays'])) if j['holidays'] else ''}</td></tr>")
    o.append("</tbody></table></div><h3>Past windows, 2000–2026</h3><div class='wrap'><table><thead><tr><th>Group</th><th class='n'>Windows</th>"
             "<th class='n'>Bearish call right</th><th class='n'>Normal rate</th><th class='n'>p</th><th class='n'>Average move (bearish = +)</th><th class='n'>Median move</th><th class='n'>Big days per window</th></tr></thead><tbody>")
    for k, v in m["groups"].items():
        cls = "g" if v["hit_rate"] is not None and v["base_rate"] is not None and v["hit_rate"] > v["base_rate"] else "r"
        bold = k.startswith("Like")
        o.append(f"<tr><td>{'<b>' if bold else ''}{E(k)}{'</b>' if bold else ''}</td><td class='n'>{v['windows']}</td><td class='n {cls}'>{v['worked']}/{v['worked'] + v['failed']} = {v['hit_rate']}%</td>"
                 f"<td class='n'>{v['base_rate']}%</td><td class='n'>{v['p_value']}</td><td class='n'>{'' if v['avg_dir_ret'] is None else format(v['avg_dir_ret'], '+.2f')}%</td>"
                 f"<td class='n'>{v['median_ret']:+.2f}%</td><td class='n'>{v['big_per_window']}</td></tr>")
    o.append(f"</tbody></table></div><h3>Our {E(m['name'])} table in January 2027</h3><div class='wrap'><table><thead><tr><th>Dates</th><th>Signal</th><th>Why</th></tr></thead><tbody>")
    for t in m["table"]:
        o.append(f"<tr><td class='n'>{t['frm']} – {t['to']}</td><td class='{'r' if t['sig'] == 'Bearish' else 'g' if t['sig'] == 'Bullish' else ''}'>{t['sig']} {t['st']}</td><td class='s'>{E(t['why'])}</td></tr>")
    o.append("</tbody></table></div>")
    rows = ""
    for r in m["past"]:
        cls = "r" if r["ret"] is not None and r["ret"] < -0.5 else "g" if r["ret"] is not None and r["ret"] > 0.5 else ""
        rows += (f"<tr><td>{r['start']} – {r['end']}</td><td>{E(r['pair'])}</td><td class='n'>{r['days']}</td><td>{r['sign']}{', combust' if r['combust'] else ''}</td>"
                 f"<td>{E(', '.join(r['benefic']) or '–')}</td><td class='n {cls}'>{'' if r['ret'] is None else format(r['ret'], '+.2f') + '%'}</td><td class='n'>{r['n'] or ''}</td>"
                 f"<td class='n'>{r['big']}</td><td class='n'>{'' if r['worst'] is None else format(r['worst'], '+.2f') + '%'}</td></tr>")
    o.append(f"<details><summary>Every past window ({len(m['past'])})</summary><div class='wrap'><table><thead><tr><th>Window</th><th>Hemmed by</th><th class='n'>Days</th><th>Mercury</th>"
             f"<th>Benefic aspect</th><th class='n'>Move</th><th class='n'>Sessions</th><th class='n'>Big days</th><th class='n'>Worst point</th></tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "".join(o)


INTRO = ("2026 document B116: “negative event for financial markets”; with a benefic aspect, “very volatile and both side movement”; if Mercury is combust, "
         "“more profound” when the malefics are other than the Sun. Past windows 2000–2026 scored by the project's standard method; each market in its own exchange time. "
         "“Bearish call right” counts windows where the market fell more than 0.5% over the scored horizon; the normal rate is how often a move of the same length fell in the same year.")


def page(res):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--dn:#cf222e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1150px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} h3{font-size:15px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .g{color:var(--up);font-weight:600} .r{color:var(--dn);font-weight:600} summary{cursor:pointer}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Mercury Paap Kartari January</title><style>{css}</style></head><body>",
         "<h1>Mercury in Paap Kartari, January 2027: S&amp;P 500 and BSE Sensex</h1>", f"<p class='s'>{E(INTRO)}</p>"]
    for m in res["markets"].values():
        o.append(section(m, E))
    o.append("<p class='s'>Generated by tools/kartari_jan2027.py; also shown in the 2026 calendar. Market prices and astrology only.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
