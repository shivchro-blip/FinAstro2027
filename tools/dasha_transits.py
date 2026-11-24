"""Vimshottari dashas of the USA and NYSE charts, all five levels (Mahadasha > Antardasha > Pratyantar >
Sookshma > Prana), mapped against the transits of the dasha lords, plus a 1928-2026 S&P test of the lords.

    python tools/dasha_transits.py [YYYY-MM-DD]      # reference day, default today (US Eastern)

Charts (tools/nyse_charts.py): USA 4 Jul 1776 17:10 LMT Philadelphia (Sibly); NYSE 17 May 1792 10:00 LMT
New York (the time is not recorded). Sidereal Lahiri; Vimshottari from the natal Moon; 365.25-day years.
The dasha sequence is continuous across a nakshatra boundary, so a birth-time error shifts the dates
rather than changing everything: one hour moves the timeline by about 0.3-0.7 years here. The running
Mahadashas (USA Rahu, NYSE Mercury) hold within +/-3 hours, the Antardasha needs the hour, and the
Pratyantar, Sookshma and Prana need the minute - which neither chart has. A sensitivity table shows this.
Transit mapping: where each running dasha lord is now (sign, nakshatra, house from the natal ascendant and
Moon, retrograde, combust, dignity, conjunct a node / Mars / Saturn, whole-sign aspects from malefics).
S&P test 1928-2026: S&P daily returns during each lord's Antardasha / Pratyantar / Sookshma periods
against all days (mean daily return, t-statistic), and natural benefics against natural malefics.
Writes build/pdfref/dasha_transits_ET.{html,json}.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
swe.set_sid_mode(swe.SIDM_LAHIRI)
FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
YEARS = dict(Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16, Saturn=19, Mercury=17)
YEAR_DAYS = 365.25
LEVELS = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"]
NAKS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
BODY = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
EXALT = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra", "Rahu": "Taurus", "Ketu": "Scorpio"}
DEBIL = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries", "Rahu": "Scorpio", "Ketu": "Taurus"}
OWN = {"Sun": ("Leo",), "Moon": ("Cancer",), "Mars": ("Aries", "Scorpio"), "Mercury": ("Gemini", "Virgo"), "Jupiter": ("Sagittarius", "Pisces"),
       "Venus": ("Taurus", "Libra"), "Saturn": ("Capricorn", "Aquarius")}
BENEFIC = ("Jupiter", "Venus", "Mercury", "Moon")
MALEFIC = ("Saturn", "Mars", "Rahu", "Ketu", "Sun")
COMBUST = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
CHARTS = {
    "USA": dict(label="USA – 4 Jul 1776, 17:10 LMT, Philadelphia (Sibly)", ut=dt.datetime(1776, 7, 4, 22, 11, tzinfo=UTC), lat=39.9526, lon=-75.1652),
    "NYSE": dict(label="NYSE – 17 May 1792, 10:00 LMT, New York", ut=dt.datetime(1792, 5, 17, 14, 56, tzinfo=UTC), lat=40.7069, lon=-74.0113),
}


def jd(t):
    t = t.astimezone(UTC)
    return swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 + t.second / 3600)


def pos(t, body):
    if body == "Ketu":
        r = swe.calc_ut(jd(t), swe.MEAN_NODE, FL)[0]
        return (r[0] + 180) % 360, r[3]
    r = swe.calc_ut(jd(t), BODY[body], FL)[0]
    return r[0] % 360, r[3]


def asc(t, lat, lon):
    x = jd(t)
    return (swe.houses(x, lat, lon, b"W")[1][0] - swe.get_ayanamsa_ut(x)) % 360


# ------------------------------------------------------------------ dashas
def maha_start(moon, birth):
    span = 360 / 27
    ni = int(moon // span)
    frac = (moon % span) / span
    lord_i = ni % 9
    start = birth - dt.timedelta(days=frac * YEARS[LORDS[lord_i]] * YEAR_DAYS)
    return lord_i, start, ni, frac


def periods(lord_i, start, length_days, level, depth):
    """Yield (path, start, end) for the sub-periods of one period, `depth` levels down (level 1 = Antardasha)."""
    t = start
    for k in range(9):
        li = (lord_i + k) % 9
        L = length_days * YEARS[LORDS[li]] / 120
        e = t + dt.timedelta(days=L)
        yield (LORDS[li],), t, e, li, L
        t = e


def dasha_at(chart, when, levels=5):
    moon = pos(chart["ut"], "Moon")[0]
    li, t, *_ = maha_start(moon, chart["ut"])
    out = []
    # Mahadasha
    while True:
        L = YEARS[LORDS[li]] * YEAR_DAYS
        e = t + dt.timedelta(days=L)
        if e > when:
            break
        t, li = e, (li + 1) % 9
    out.append((LORDS[li], t, e))
    cur_li, cur_t, cur_L = li, t, L
    for lvl in range(1, levels):
        for path, s, e, sub_li, sub_L in periods(cur_li, cur_t, cur_L, lvl, 1):
            if s <= when < e:
                out.append((path[0], s, e))
                cur_li, cur_t, cur_L = sub_li, s, sub_L
                break
    return out


def sequence(chart, level, a, b):
    """All periods of `level` (1 = Antardasha, 2 = Pratyantar, 3 = Sookshma) overlapping a..b, with parents."""
    moon = pos(chart["ut"], "Moon")[0]
    li, t, *_ = maha_start(moon, chart["ut"])
    res = []

    def walk(lord_i, s, L, lvl, path):
        e = s + dt.timedelta(days=L)
        if e < a or s > b:
            return
        if lvl == level:
            res.append(("/".join(path), s, e))
            return
        for p, ss, ee, sli, sL in periods(lord_i, s, L, lvl + 1, 1):
            walk(sli, ss, sL, lvl + 1, path + [p[0]])
    while t < b:
        L = YEARS[LORDS[li]] * YEAR_DAYS
        walk(li, t, L, 0, [LORDS[li]])
        t += dt.timedelta(days=L)
        li = (li + 1) % 9
    return res


# ------------------------------------------------------------------ transits of the dasha lords
def transit_state(lord, chart, when):
    p, spd = pos(when, lord)
    sign = SIGNS[int(p // 30)]
    nat_asc = int(asc(chart["ut"], chart["lat"], chart["lon"]) // 30)
    nat_moon = int(pos(chart["ut"], "Moon")[0] // 30)
    sun = pos(when, "Sun")[0]
    others = {b: pos(when, b)[0] for b in ("Mars", "Saturn", "Rahu", "Ketu", "Jupiter")}
    notes = []
    if EXALT.get(lord) == sign:
        notes.append("exalted")
    if DEBIL.get(lord) == sign:
        notes.append("debilitated")
    if sign in OWN.get(lord, ()):
        notes.append("own sign")
    if spd < 0 and lord not in ("Rahu", "Ketu"):
        notes.append("retrograde")
    if lord in COMBUST and min((p - sun) % 360, (sun - p) % 360) <= COMBUST[lord]:
        notes.append("combust")
    for b, q in others.items():
        if b != lord and int(q // 30) == int(p // 30):
            notes.append(f"with {b}")
    si = int(p // 30)
    for b, q in (("Saturn", others["Saturn"]), ("Mars", others["Mars"]), ("Rahu", others["Rahu"])):
        if b == lord:
            continue
        h = (si - int(q // 30)) % 12 + 1
        asp = {"Saturn": (3, 7, 10), "Mars": (4, 7, 8), "Rahu": (7,)}[b]
        if h in asp:
            notes.append(f"aspected by {b}")
    return dict(lord=lord, sign=sign, deg=round(p % 30, 2), nak=NAKS[int(p // (360 / 27))], house_asc=(si - nat_asc) % 12 + 1, house_moon=(si - nat_moon) % 12 + 1, notes=notes)


# ------------------------------------------------------------------ S&P test
def spx():
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv")) if r["date"] <= "2026-11-20"]
    return [(rows[i][0], (rows[i][1] / rows[i - 1][1] - 1) * 100) for i in range(1, len(rows))]


def lord_test(chart, level, R):
    D = [r[0] for r in R]
    seq = sequence(chart, level, dt.datetime(1928, 1, 1, tzinfo=UTC), dt.datetime(2026, 11, 21, tzinfo=UTC))
    lab = {}
    j = 0
    for path, s, e in seq:
        lord = path.split("/")[-1]
        s_d, e_d = s.astimezone(ET).date(), e.astimezone(ET).date()
        while j < len(D) and D[j] < s_d:
            j += 1
        k = j
        while k < len(D) and D[k] < e_d:
            lab[k] = lord
            k += 1
    allr = [r[1] for r in R]
    mu, sd = statistics.mean(allr), statistics.pstdev(allr)
    res = {}
    for L in LORDS + ["benefic", "malefic"]:
        idx = [i for i, l in lab.items() if (l == L or (L == "benefic" and l in BENEFIC) or (L == "malefic" and l in MALEFIC))]
        if not idx:
            continue
        x = [R[i][1] for i in idx]
        m = statistics.mean(x)
        t = (m - mu) / (sd / math.sqrt(len(x)))
        res[L] = dict(days=len(x), mean=round(m, 4), up=round(sum(v > 0 for v in x) / len(x) * 100, 1), t=round(t, 2), ann=round(m * 252, 1))
    res["_all"] = dict(mean=round(mu, 4), up=round(sum(v > 0 for v in allr) / len(allr) * 100, 1), ann=round(mu * 252, 1))
    return res


def sensitivity(chart):
    rows = []
    for m in range(-180, 181, 30):
        t = chart["ut"] + dt.timedelta(minutes=m)
        moon = pos(t, "Moon")[0]
        d = dasha_at(dict(chart, ut=t), dt.datetime(2026, 11, 24, 17, tzinfo=UTC), 3)
        rows.append(dict(shift=m, moon=f"{SIGNS[int(moon // 30)]} {moon % 30:.2f}°", nak=NAKS[int(moon // (360 / 27))], now=" / ".join(x[0] for x in d)))
    return rows


def main():
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(ET).date()
    now = dt.datetime.combine(day, dt.time(12), ET)
    a, b = now - dt.timedelta(days=60), now + dt.timedelta(days=120)
    R = spx()
    res = dict(day=str(day), charts={})
    for key, ch in CHARTS.items():
        moon = pos(ch["ut"], "Moon")[0]
        li, start, ni, frac = maha_start(moon, ch["ut"])
        cur = dasha_at(ch, now, 5)
        lv = []
        for name, (lord, s, e) in zip(LEVELS, cur):
            lv.append(dict(level=name, lord=lord, start=s.astimezone(ET).strftime("%d %b %Y %H:%M"), end=e.astimezone(ET).strftime("%d %b %Y %H:%M"),
                           transit=transit_state(lord, ch, now)))
        maha = sequence(ch, 0, dt.datetime(1950, 1, 1, tzinfo=UTC), dt.datetime(2060, 1, 1, tzinfo=UTC))
        antar = sequence(ch, 1, now - dt.timedelta(days=2 * 365), now + dt.timedelta(days=4 * 365))
        prat = sequence(ch, 2, a, b)
        sook = sequence(ch, 3, a, b)
        # S&P move in each past Pratyantar / Sookshma inside the window
        rmap = dict(R)

        def move(s, e):
            xs = [r for d_, r in R if s.astimezone(ET).date() <= d_ < e.astimezone(ET).date()]
            return round((math.prod(1 + v / 100 for v in xs) - 1) * 100, 2) if xs else None
        del rmap
        res["charts"][key] = dict(
            label=ch["label"], moon=f"{SIGNS[int(moon // 30)]} {moon % 30:.2f}° ({NAKS[ni]}, {frac * 100:.1f}% through)",
            asc=SIGNS[int(asc(ch["ut"], ch["lat"], ch["lon"]) // 30)], levels=lv,
            maha=[dict(lord=p, start=s.strftime("%Y-%m-%d"), end=e.strftime("%Y-%m-%d")) for p, s, e in maha],
            antar=[dict(lord=p, start=s.strftime("%Y-%m-%d"), end=e.strftime("%Y-%m-%d")) for p, s, e in antar],
            pratyantar=[dict(lord=p, start=s.astimezone(ET).strftime("%Y-%m-%d"), end=e.astimezone(ET).strftime("%Y-%m-%d"), spx=move(s, e),
                             transit=transit_state(p.split("/")[-1], ch, max(s, a))) for p, s, e in prat],
            sookshma=[dict(lord=p, start=s.astimezone(ET).strftime("%Y-%m-%d %H:%M"), end=e.astimezone(ET).strftime("%Y-%m-%d %H:%M"), spx=move(s, e)) for p, s, e in sook],
            sensitivity=sensitivity(ch),
            test={lvl: lord_test(ch, n, R) for n, lvl in ((1, "Antardasha"), (2, "Pratyantar"), (3, "Sookshma"))})
    json.dump(res, open(OUT / "dasha_transits_ET.json", "w"), indent=1, default=str)
    write(res)
    for k, c in res["charts"].items():
        print(k, c["label"], c["moon"], "asc", c["asc"])
        for x in c["levels"]:
            print(f"   {x['level']:11s} {x['lord']:8s} {x['start']} → {x['end']} | transit {x['transit']['sign']} {x['transit']['deg']} {x['transit']['nak']} H{x['transit']['house_asc']} (Moon H{x['transit']['house_moon']}) {', '.join(x['transit']['notes'])}")
        for lvl, t in c["test"].items():
            print("  ", lvl, {L: (v["days"], v["ann"], v["t"]) for L, v in t.items() if L != "_all"}, "all", t["_all"]["ann"])
        print("   sensitivity", [(s["shift"], s["nak"], s["now"]) for s in c["sensitivity"]])


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    blocks = ""
    for k, c in res["charts"].items():
        lv = "".join(f"<tr><td><b>{x['level']}</b></td><td><b>{x['lord']}</b></td><td class='w'>{x['start']}</td><td class='w'>{x['end']}</td>"
                     f"<td>{x['transit']['sign']} {x['transit']['deg']}°, {x['transit']['nak']}</td><td class='n'>{x['transit']['house_asc']} / {x['transit']['house_moon']}</td>"
                     f"<td class='s'>{html.escape(', '.join(x['transit']['notes']) or '-')}</td></tr>" for x in c["levels"])
        pr = "".join(f"<tr class='{'bullish' if (p['spx'] or 0) > 0 else 'bearish' if (p['spx'] or 0) < 0 else ''}'><td class='w'>{p['start']} – {p['end']}</td><td><b>{p['lord']}</b></td>"
                     f"<td class='n'>{'' if p['spx'] is None else format(p['spx'], '+.2f') + '%'}</td><td class='s'>{p['transit']['sign']} {p['transit']['deg']}°, house {p['transit']['house_asc']} from the ascendant; {html.escape(', '.join(p['transit']['notes']) or '-')}</td></tr>"
                     for p in c["pratyantar"])
        sk = "".join(f"<tr class='{'bullish' if (p['spx'] or 0) > 0 else 'bearish' if (p['spx'] or 0) < 0 else ''}'><td class='w'>{p['start']} – {p['end']}</td><td>{p['lord']}</td>"
                     f"<td class='n'>{'' if p['spx'] is None else format(p['spx'], '+.2f') + '%'}</td></tr>" for p in c["sookshma"])
        an = "; ".join(f"{p['lord']} {p['start'][:7]} – {p['end'][:7]}" for p in c["antar"])
        mh = "; ".join(f"{p['lord']} {p['start'][:4]} – {p['end'][:4]}" for p in c["maha"])

        def ttable(t):
            body = "".join(f"<tr class='{'bullish' if v['t'] >= 2 else 'bearish' if v['t'] <= -2 else ''}'><td>{L}</td><td class='n'>{v['days']}</td><td class='n'>{v['ann']:+.1f}%</td><td class='n'>{v['up']}%</td><td class='n'>{v['t']}</td></tr>"
                           for L, v in t.items() if L != "_all")
            return (f"<table><thead><tr><th>Lord</th><th>Days</th><th>S&amp;P per year</th><th>Up days</th><th>t</th></tr></thead><tbody>{body}"
                    f"<tr><td><i>all days</i></td><td></td><td class='n'>{t['_all']['ann']:+.1f}%</td><td class='n'>{t['_all']['up']}%</td><td></td></tr></tbody></table>")
        tests = "".join(f"<div><b>{lvl}</b>{ttable(t)}</div>" for lvl, t in c["test"].items())
        sens = "".join(f"<tr><td class='n'>{s['shift']:+d} min</td><td>{s['moon']}</td><td>{s['nak']}</td><td>{s['now']}</td></tr>" for s in c["sensitivity"])
        blocks += f"""<h2>{html.escape(c['label'])}</h2>
<p class="m">Natal Moon {html.escape(c['moon'])}; ascendant {c['asc']}. Mahadashas: {html.escape(mh)}.</p>
<h3>Running now, all five levels, with the transit of each lord (house from the natal ascendant / natal Moon)</h3>
<div class="wrap"><table><thead><tr><th>Level</th><th>Lord</th><th>From</th><th>To</th><th>Lord's transit</th><th>House</th><th>Transit condition</th></tr></thead><tbody>{lv}</tbody></table></div>
<p class="s">Antardashas around now: {html.escape(an)}.</p>
<h3>Pratyantar dashas, last 60 days to next 120 days, with the S&amp;P move inside each (past ones)</h3>
<div class="wrap"><table><thead><tr><th>Period</th><th>Maha / Antar / Pratyantar</th><th>S&amp;P</th><th>Pratyantar lord's transit at its start (or at the window start)</th></tr></thead><tbody>{pr}</tbody></table></div>
<details><summary>Sookshma dashas in the same window</summary><div class="wrap"><table><thead><tr><th>Period (ET)</th><th>Maha / Antar / Pratyantar / Sookshma</th><th>S&amp;P</th></tr></thead><tbody>{sk}</tbody></table></div></details>
<h3>Do the dasha lords show in the S&amp;P, 1928–2026?</h3>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px">{tests}</div>
<p class="s">S&amp;P daily return during each lord's periods, as a yearly rate, against all days; |t| ≥ 2 coloured. With 9 lords × 3 levels × 2 charts, a couple of |t| ≥ 2 results are expected by chance.</p>
<h3>Birth-time sensitivity (the running Maha / Antar / Pratyantar on {res['day']})</h3>
<div class="wrap"><table><thead><tr><th>Birth time shift</th><th>Moon</th><th>Nakshatra</th><th>Dasha now</th></tr></thead><tbody>{sens}</tbody></table></div>"""
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dasha and Transits</title><style>{css}</style></head><body>
<h1>USA and NYSE: Vimshottari dashas (five levels) and the transits of the dasha lords, {res['day']}</h1>
<p class="m">Mahadasha → Antardasha → Pratyantar → Sookshma → Prana, from the natal Moon (sidereal Lahiri, 365.25-day years). A birth-time error shifts the whole dasha timeline (about 0.3–0.7 years per hour here): the Mahadashas hold within ±3 hours, the Antardasha needs the hour, and the Pratyantar, Sookshma and Prana need the minute, which neither chart has. Read the smaller levels as illustrations.</p>
{blocks}
<p class="s">Generated by tools/dasha_transits.py. Market prices and astrology only.</p></body></html>"""
    (OUT / "dasha_transits_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
