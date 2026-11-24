"""Which planetary conditions go with falls and which with rises, tested day by day, plus a running
log of big market days for learning.

    python tools/trigger_study.py                  # test the candidate triggers, rebuild the log page
    python tools/trigger_study.py --log 2026-11-20 "news text" "url"   # add / update one day in the log

Candidates are the conditions present on the days logged so far (first: Fri 20 Nov 2026, a fall,
and Mon 23 Nov 2026, a rise). Each is tested on every trading day 20 Nov 2000 - 20 Nov 2026 for
the S&P 500, Nasdaq, BSE Sensex, COMEX gold and silver, on the SAME day's close-to-close move
(the sky at the middle of each market's session): share of up days against the same years' share
(binomial p), and big down / big up days against the number expected from the same years (Poisson).
Big = 2% (silver 3.5%). With ~20 conditions x 5 markets about 5 results will reach p < 0.05 by luck.
Writes build/pdfref/trigger_study_2000-2026_ET.{html,json} and build/pdfref/market_event_log.json.
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
sys.path.insert(0, str(ROOT))

from finastro.pdfref.engine import snapshot  # noqa: E402

OUT = ROOT / "build" / "pdfref"
LOG = OUT / "market_event_log.json"
ET, IST = ZoneInfo("America/New_York"), ZoneInfo("Asia/Kolkata")
P0, P1 = dt.date(2000, 11, 20), dt.date(2026, 11, 20)
MARKETS = {  # name: (price file, session-midpoint time, zone, big-day threshold %)
    "S&P 500": ("spx_GSPC_daily_2000.csv", dt.time(12, 45), ET, 2.0),
    "Nasdaq": ("nasdaq_IXIC_daily_2000.csv", dt.time(12, 45), ET, 2.0),
    "BSE Sensex": ("sensex_BSESN_daily_2000.csv", dt.time(12, 20), IST, 2.0),
    "Gold": ("gold_GC_F_daily_2000.csv", dt.time(12, 0), ET, 2.0),
    "Silver": ("silver_SI_F_daily_2000.csv", dt.time(12, 0), ET, 3.5),
}
G9 = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
PANCHAK = ("Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati")


def hdist(s, a, b):
    return (s[b].sign_i - s[a].sign_i) % 12 + 1


def karana_vishti(s):
    """Vishti (Bhadra) karana: half-tithis 8, 15, 22, 29, 36, 43, 50, 57 of the 60 (6° steps of elongation)."""
    k = int(((s["Moon"].lon - s["Sun"].lon) % 360) // 6) + 1
    return k in (8, 15, 22, 29, 36, 43, 50, 57)


CANDIDATES = {
    # present on Fri 20 Nov 2026 (fall)
    "Ekadashi on a Friday (2026 doc: 'High Bearish, 90%+')": ("fall", lambda s, d: s.tithi in (11, 26) and d.weekday() == 4),
    "Ekadashi (any weekday)": ("fall", lambda s, d: s.tithi in (11, 26)),
    "Bhadra (Vishti karana) at mid-session": ("fall", lambda s, d: karana_vishti(s)),
    "Moon with Saturn (same sign)": ("fall", lambda s, d: s["Moon"].sign_i == s["Saturn"].sign_i),
    "Moon in Pisces": ("fall", lambda s, d: s["Moon"].sign == "Pisces"),
    "Panchak (Moon in Dhanishta 3rd pada to Revati)": ("fall", lambda s, d: s["Moon"].nak in PANCHAK or (s["Moon"].nak == "Dhanishta" and s["Moon"].pada >= 3)),
    "Venus debilitated (Virgo)": ("fall", lambda s, d: s["Venus"].sign == "Virgo"),
    "Venus opposite Saturn (7th)": ("fall", lambda s, d: hdist(s, "Venus", "Saturn") == 7),
    "Venus in the last 2° of a sign": ("fall", lambda s, d: s["Venus"].lon % 30 >= 28),
    "Mercury alone in a sign (TA/KD bearish)": ("fall", lambda s, d: all(s[p].sign_i != s["Mercury"].sign_i for p in G9 if p != "Mercury")),
    "Saturn retrograde": ("both", lambda s, d: s["Saturn"].retro),
    "Mars, Jupiter and Ketu together (Leo)": ("both", lambda s, d: s["Mars"].sign_i == s["Jupiter"].sign_i == s["Ketu"].sign_i),
    # present on Mon 23 Nov 2026 (rise)
    "Moon in Aries": ("rise", lambda s, d: s["Moon"].sign == "Aries"),
    "Moon trine Jupiter (5th / 9th)": ("rise", lambda s, d: hdist(s, "Jupiter", "Moon") in (5, 9)),
    "Moon trine Mars (5th / 9th)": ("rise", lambda s, d: hdist(s, "Mars", "Moon") in (5, 9)),
    "Shukla Chaturdashi / Purnima (last two tithis before full Moon)": ("rise", lambda s, d: s.tithi in (14, 15)),
    "Venus in own sign (Taurus / Libra)": ("rise", lambda s, d: s["Venus"].sign in ("Taurus", "Libra")),
    "Mercury and Venus together": ("rise", lambda s, d: s["Mercury"].sign_i == s["Venus"].sign_i),
    "Moon opposite Mercury (7th)": ("rise", lambda s, d: hdist(s, "Mercury", "Moon") == 7),
    "Monday with a waxing Moon": ("rise", lambda s, d: d.weekday() == 0 and s.tithi <= 15),
}


def binom_two_sided(k, n, p):
    if not n:
        return None
    m, sd = n * p, math.sqrt(n * p * (1 - p)) or 1
    z = (k - m) / sd
    return math.erfc(abs(z) / math.sqrt(2))


def poisson_sf(k, lam):
    if k <= 0:
        return 1.0
    if lam > 300:
        return 0.5 * math.erfc((k - 0.5 - lam) / math.sqrt(lam) / math.sqrt(2))
    term = math.exp(-lam)
    cdf = term
    for i in range(1, k):
        term *= lam / i
        cdf += term
    return max(0.0, 1 - cdf)


def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


def market_days(name):
    f, t, tz, th = MARKETS[name]
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / f))]
    out = []
    for (d0, c0), (d1, c1) in zip(rows, rows[1:]):
        if P0 <= d1 <= P1:
            s = snapshot(dt.datetime.combine(d1, t, tz).astimezone(dt.timezone.utc))
            out.append(dict(d=d1, r=(c1 / c0 - 1) * 100, flags={k: bool(f_(s, d1)) for k, (_, f_) in CANDIDATES.items()}))
    return out, th


def study():
    res = {}
    for name in MARKETS:
        days, th = market_days(name)
        yr = {}
        for x in days:
            y = yr.setdefault(nov_year(x["d"]), dict(n=0, up=0, bd=0, bu=0))
            y["n"] += 1
            y["up"] += x["r"] > 0
            y["bd"] += x["r"] <= -th
            y["bu"] += x["r"] >= th
        res[name] = {}
        for k in CANDIDATES:
            sel = [x for x in days if x["flags"][k]]
            if not sel:
                continue
            e_up = sum(yr[nov_year(x["d"])]["up"] / yr[nov_year(x["d"])]["n"] for x in sel)
            e_bd = sum(yr[nov_year(x["d"])]["bd"] / yr[nov_year(x["d"])]["n"] for x in sel)
            e_bu = sum(yr[nov_year(x["d"])]["bu"] / yr[nov_year(x["d"])]["n"] for x in sel)
            up = sum(x["r"] > 0 for x in sel)
            bd = sum(x["r"] <= -th for x in sel)
            bu = sum(x["r"] >= th for x in sel)
            res[name][k] = dict(n=len(sel), mean=round(sum(x["r"] for x in sel) / len(sel), 3), up=round(up / len(sel) * 100, 1), exp_up=round(e_up / len(sel) * 100, 1),
                                p_up=round(binom_two_sided(up, len(sel), e_up / len(sel)), 4), bd=bd, exp_bd=round(e_bd, 1), p_bd=round(poisson_sf(bd, e_bd), 4),
                                bu=bu, exp_bu=round(e_bu, 1), p_bu=round(poisson_sf(bu, e_bu), 4))
    return res


def mars_jupiter_node():
    """Every Mars-Jupiter conjunction (same sign) with Rahu or Ketu in the same sign, S&P 500 1928-2026."""
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv")) if r["date"] <= str(P1)]
    D = [r[0] for r in rows]
    C = [r[1] for r in rows]
    eps, cur = [], None
    for i, d in enumerate(D):
        s = snapshot(dt.datetime(d.year, d.month, d.day, 17, tzinfo=dt.timezone.utc))
        node = "Ketu" if s["Ketu"].sign_i == s["Mars"].sign_i else "Rahu" if s["Rahu"].sign_i == s["Mars"].sign_i else None
        on = s["Mars"].sign_i == s["Jupiter"].sign_i and node
        if on and cur and cur["node"] == node and i - cur["j"] <= 3:
            cur["j"] = i
        elif on:
            cur = dict(node=node, sign=s["Mars"].sign, i=i, j=i)
            eps.append(cur)
    out = []
    for e in eps:
        i, j = e["i"], e["j"]
        out.append(dict(node=e["node"], sign=e["sign"], start=str(D[i]), end=str(D[j]), sessions=j - i + 1, ret=round((C[j] / C[i - 1] - 1) * 100, 1),
                        worst=round((min(C[i:j + 1]) / C[i - 1] - 1) * 100, 1), after63=round((C[min(j + 63, len(C) - 1)] / C[j] - 1) * 100, 1) if j + 1 < len(C) else None))
    L = 29
    wr = [(min(C[i:i + L + 1]) / C[i - 1] - 1) * 100 for i in range(1, len(C) - L, 3)]
    base = dict(sessions=L, worst15=round(sum(x <= -15 for x in wr) / len(wr) * 100, 1), worst8=round(sum(x <= -8 for x in wr) / len(wr) * 100, 1))
    return out, base


def sky_flags(day, name):
    f, t, tz, th = MARKETS[name]
    s = snapshot(dt.datetime.combine(day, t, tz).astimezone(dt.timezone.utc))
    return [k for k, (_, f_) in CANDIDATES.items() if f_(s, day)]


def moves(day):
    """Close-to-close moves; days not yet in the price files come from Yahoo (tools/day_report.py actual())."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("dr", ROOT / "tools" / "day_report.py")
    dr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dr)
    live = {a["market"].split(" (")[0]: a["change"] for a in dr.actual(day) if "change" in a}
    out = {k: v for k, v in live.items()}
    for name, (f, t, tz, th) in MARKETS.items():
        rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / f))]
        prev = [x for x in rows if x[0] < day]
        cur = [x for x in rows if x[0] == day]
        if prev and cur and name not in out:
            out[name] = round((cur[0][1] / prev[-1][1] - 1) * 100, 2)
    return out


def capture(day, news="", url=""):
    log = json.load(open(LOG)) if LOG.exists() else {"entries": []}
    s = snapshot(dt.datetime.combine(day, dt.time(12, 45), ET).astimezone(dt.timezone.utc))
    entry = dict(date=str(day), weekday=day.strftime("%A"), moves=moves(day), news=news, sources=[u for u in url.split() if u],
                 sky={p: f"{s[p].sign} {s[p].lon % 30:.1f}° {s[p].nak}{' R' if s[p].retro and p not in ('Rahu', 'Ketu') else ''}" for p in G9},
                 tithi=s.tithi, flags={name: sky_flags(day, name) for name in MARKETS})
    log["entries"] = [e for e in log["entries"] if e["date"] != str(day)] + [entry]
    log["entries"].sort(key=lambda e: e["date"])
    json.dump(log, open(LOG, "w"), indent=1)
    return entry


def main():
    if "--log" in sys.argv:
        i = sys.argv.index("--log")
        day = dt.date.fromisoformat(sys.argv[i + 1])
        news = sys.argv[i + 2] if len(sys.argv) > i + 2 else ""
        url = sys.argv[i + 3] if len(sys.argv) > i + 3 else ""
        e = capture(day, news, url)
        print(json.dumps(e, indent=1))
        return
    res = study()
    log = json.load(open(LOG)) if LOG.exists() else {"entries": []}
    mjn, base = mars_jupiter_node()
    json.dump(dict(results=res, log=log, mars_jupiter_node=mjn, mjn_base=base), open(OUT / "trigger_study_2000-2026_ET.json", "w"), indent=1)
    write(res, log, mjn, base)
    for k, (side, _) in CANDIDATES.items():
        print(f"[{side}] {k}")
        for name in MARKETS:
            r = res[name].get(k)
            if r:
                print(f"     {name:10s} n {r['n']:4d} mean {r['mean']:+.3f}% up {r['up']}% vs {r['exp_up']}% p {r['p_up']}  bigdown {r['bd']}/{r['exp_bd']} p {r['p_bd']}  bigup {r['bu']}/{r['exp_bu']} p {r['p_bu']}")


def write(res, log, mjn, base):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    names = list(MARKETS)

    def cell(r):
        if not r:
            return "<td>–</td>"
        lean = r["up"] - r["exp_up"]
        sig = r["p_up"] < 0.05
        cls = ("bullish" if lean > 0 else "bearish") if sig else ""
        extra = []
        if r["p_bd"] < 0.05:
            extra.append(f"big falls {r['bd']} vs {r['exp_bd']}")
        if r["p_bu"] < 0.05:
            extra.append(f"big rises {r['bu']} vs {r['exp_bu']}")
        return (f"<td class='n {cls}'><b>{r['up']}%</b> up vs {r['exp_up']}% (p {r['p_up']})<br><span class='s'>n {r['n']}, mean {r['mean']:+.2f}%"
                f"{'; ' + '; '.join(extra) if extra else ''}</span></td>")
    rows = "".join(f"<tr><td><b>{html.escape(k)}</b><div class='s'>present on the {'fall day (Fri 20 Nov)' if side == 'fall' else 'rise day (Mon 23 Nov)' if side == 'rise' else 'both days'}</div></td>"
                   f"{''.join(cell(res[n].get(k)) for n in names)}</tr>" for k, (side, _) in CANDIDATES.items())
    mjrows = "".join(f"<tr class='{'bearish' if e['worst'] <= -8 else ''}'><td>{e['start']}</td><td>{e['end']}</td><td>{e['node']}</td><td>{e['sign']}</td><td class='n'>{e['sessions']}</td>"
                     f"<td class='n'>{e['ret']:+.1f}%</td><td class='n'><b>{e['worst']:+.1f}%</b></td><td class='n'>{'' if e['after63'] is None else format(e['after63'], '+.1f') + '%'}</td></tr>" for e in mjn)
    lrows = ""
    for e in log["entries"]:
        mv = "; ".join(f"{k} {v:+.2f}%" for k, v in e["moves"].items())
        sky = "; ".join(f"{p} {v}" for p, v in e["sky"].items())
        src = " ".join(f"<a href='{html.escape(u)}'>source</a>" for u in e.get("sources", []))
        lrows += (f"<tr><td class='w'><b>{e['weekday']} {e['date']}</b></td><td class='s'>{html.escape(mv)}</td><td class='s'>{html.escape(e['news'])} {src}</td>"
                  f"<td class='s'>{html.escape(sky)}; tithi {e['tithi']}</td><td class='s'>{html.escape('; '.join(e['flags'].get('S&P 500', [])))}</td></tr>")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Trigger Study</title><style>{css} a{{color:inherit}}</style></head><body>
<h1>Fall and rise triggers: the conditions of 20 and 23 Nov 2026, tested day by day 2000–2026</h1>
<p class="m">Every condition that was present on the fall day (Fri 20 Nov: S&amp;P −3.7%, Nasdaq −5.3%, gold −4.6%, silver −7.4%) or the rise day (Mon 23 Nov: S&amp;P +4.7%, Nasdaq +6.5%, gold +3.4%, silver +5.3%),
checked on every trading day of the last 26 years: how often the market closed up on days with the condition, against how often it closed up in the same years (coloured where p &lt; 0.05), and whether big falls or rises (±2%; silver ±3.5%) were more common.
About 5 of the 100 cells will reach p &lt; 0.05 by luck alone.</p>
<div class="wrap"><table><thead><tr><th>Condition</th>{''.join(f'<th>{n}</th>' for n in names)}</tr></thead><tbody>{rows}</tbody></table></div>
<h2>The one condition that stands out: Mars and Jupiter together with a node (S&amp;P 500, 1928–2026)</h2>
<p class="m">Mars, Jupiter and Ketu have shared a sign since 12 Nov 2026; the same triple ran from 10 Feb to 20 Mar 2020 (COVID crash). Every episode of Mars and Jupiter together with Rahu or Ketu since 1928:
{sum(1 for e in mjn if e['worst'] <= -15)} of {len(mjn)} had a fall of 15% or more inside it, against {base['worst15']}% of random {base['sessions']}-session windows; {sum(1 for e in mjn if e['worst'] <= -8)} of {len(mjn)} fell 8% or more, against {base['worst8']}%.
<b>This condition was picked after seeing the crash, and the episodes differ in length</b>, so treat it as a lead to track, not a tested rule. In 2009 and 2020 the market bottomed within three sessions of the episode ending; this one loses Ketu on 5 Dec 2026 (Mars and Jupiter stay together until Jupiter returns to Cancer on 24 Jan 2027).</p>
<div class="wrap"><table><thead><tr><th>Start</th><th>End</th><th>Node</th><th>Sign</th><th>Sessions</th><th>S&amp;P during</th><th>Worst point</th><th>Next 63 sessions</th></tr></thead><tbody>{mjrows}</tbody></table></div>
<h2>Market event log (for learning)</h2>
<p class="s">Big days with the news that moved them, the sky and the candidate conditions present (S&amp;P session). Add a day with <code>python tools/trigger_study.py --log YYYY-MM-DD "news" "url"</code>.</p>
<div class="wrap"><table><thead><tr><th>Day</th><th>Moves</th><th>News</th><th>Sky (12:45 ET)</th><th>Candidate conditions present</th></tr></thead><tbody>{lrows}</tbody></table></div>
<p class="s">Generated by tools/trigger_study.py.</p></body></html>"""
    (OUT / "trigger_study_2000-2026_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
