"""NYSE and USA foundation charts, and a backtest of the NYSE monthly solar-return technique.

    python tools/nyse_charts.py

Source of the technique (shared by the user, 24 Nov 2026): an astrologer's monthly "NYSE solar return"
charts (book: "Investing in Stock Market with Vedic Astrology", Vol. II). Each solar month starts when
the Sun returns to the NYSE's natal Sun degree in the next sign; the chart is cast for New York.
Reconstruction from the shared charts: the natal Sun is 27°18' Taurus TROPICAL (Buttonwood Agreement,
17 May 1792, morning, New York), the returns fall when the tropical Sun is at 27°18' of each sign
(20 Oct and 19 Nov 2026 confirmed), and Solar return reads tropical signs and houses (Capricorn rising,
Saturn "debilitated" in Aries). Our convention is sidereal Lahiri, under which Saturn is in Pisces.
Both versions are tested:
  A  Solar return's: returns at tropical 27°18' of each sign, tropical whole-sign houses from the New York ascendant;
  B  ours:     returns at the natal sidereal Sun degree (Lahiri) of each sign, sidereal whole-sign houses.
Features read in each monthly chart (the indications Solar return states): ascendant lord debilitated;
Mars with Ketu in the 8th; any of Mars / Saturn / Rahu / Ketu in the 8th; Sun in the 10th; Venus or
Jupiter in the 10th; both bearish indications together. Outcome: S&P 500 from the last close before one
return to the last close before the next, 1928-2026 (about 1,190 months), against all months.
Also: the NYSE and USA (4 Jul 1776, 17:10 LMT Philadelphia, the Sibly time) natal charts, transits to them
now, the next returns, and the Solar return open forecast for 19 Nov - 18 Dec 2026.
Writes build/pdfref/nyse_usa_charts_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import csv
import datetime as dt
import html
import json
import math
import pathlib
import statistics

import swisseph as swe
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
ET = ZoneInfo("America/New_York")
NY = (40.7069, -74.0113)
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NEECHA = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"}
BODIES = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
          "Rahu": swe.MEAN_NODE, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO}
NAKS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
swe.set_sid_mode(swe.SIDM_LAHIRI)
NATAL_NYSE = dt.datetime(1792, 5, 17, 10, 0) + dt.timedelta(hours=4, minutes=56)      # 10:00 LMT New York, as UT
NATAL_USA = dt.datetime(1776, 7, 4, 17, 10) + dt.timedelta(hours=5, minutes=1)         # 17:10 LMT Philadelphia (Sibly), as UT
PHILA = (39.9526, -75.1652)


def jd(t):
    return swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 + t.second / 3600)


def from_jd(x):
    y, m, d, h = swe.revjul(x)
    return dt.datetime(y, m, d, tzinfo=dt.timezone.utc) + dt.timedelta(hours=h)


def lon(x, body, sid):
    return swe.calc_ut(x, BODIES[body], swe.FLG_SWIEPH | (swe.FLG_SIDEREAL if sid else 0))[0]


def chart(x, lat, lng, sid):
    pos = {}
    for b in BODIES:
        r = lon(x, b, sid)
        pos[b] = dict(lon=r[0] % 360, retro=r[3] < 0)
    pos["Ketu"] = dict(lon=(pos["Rahu"]["lon"] + 180) % 360, retro=True)
    asc = swe.houses(x, lat, lng, b"W")[1][0]
    if sid:
        asc = (asc - swe.get_ayanamsa_ut(x)) % 360
    a_i = int(asc // 30)
    for b, p in pos.items():
        p["sign"] = SIGNS[int(p["lon"] // 30)]
        p["house"] = (int(p["lon"] // 30) - a_i) % 12 + 1
        p["deg"] = p["lon"] % 30
        p["nak"] = NAKS[int(((p["lon"] if sid else (p["lon"] - swe.get_ayanamsa_ut(x)) % 360)) // (360 / 27))]
    return dict(asc=asc, asc_sign=SIGNS[a_i], lagna_lord=LORD[a_i], pos=pos)


def returns(start, end, target, sid):
    """Moments when the Sun is at `target` degrees within a sign (tropical or sidereal), start..end."""
    out = []
    x = jd(start)
    end_jd = jd(end)
    while x < end_jd:
        for _ in range(60):
            d = ((lon(x, "Sun", sid)[0] % 30) - target + 15) % 30 - 15
            if abs(d) < 1e-7:
                break
            x -= d / 0.9856
        out.append(x)
        x += 30.4
    return sorted(set(round(v, 6) for v in out))


def features(c):
    p = c["pos"]
    h8 = [b for b in ("Mars", "Saturn", "Rahu", "Ketu") if p[b]["house"] == 8]
    f = {
        "Ascendant lord debilitated": p[c["lagna_lord"]]["sign"] == NEECHA.get(c["lagna_lord"]),
        "Mars with Ketu in the 8th": p["Mars"]["house"] == 8 and p["Ketu"]["house"] == 8,
        "Mars, Saturn, Rahu or Ketu in the 8th": bool(h8),
        "Sun in the 10th": p["Sun"]["house"] == 10,
        "Venus or Jupiter in the 10th": p["Venus"]["house"] == 10 or p["Jupiter"]["house"] == 10,
    }
    f["Both bearish indications (debilitated ascendant lord and a malefic in the 8th)"] = f["Ascendant lord debilitated"] and f["Mars, Saturn, Rahu or Ketu in the 8th"]
    return f


def spx():
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv"))]
    return [r[0] for r in rows], [r[1] for r in rows]


def close_before(D, C, t):
    x = t.astimezone(ET)
    day = x.date() + (dt.timedelta(days=1) if x.time() >= dt.time(16, 0) else dt.timedelta(0))
    i = bisect.bisect_left(D, day) - 1
    return i


def binom_two_sided(k, n, p):
    z = (k - n * p) / (math.sqrt(n * p * (1 - p)) or 1)
    return math.erfc(abs(z) / math.sqrt(2))


def backtest(version):
    sid = version == "B"
    natal_sid = lon(jd(NATAL_NYSE), "Sun", True)[0] % 30
    target = 27.3 if not sid else natal_sid
    D, C = spx()
    R = returns(dt.datetime(1928, 1, 5), dt.datetime(2026, 12, 25), target, sid)
    months = []
    for a, b in zip(R, R[1:]):
        ta, tb = from_jd(a), from_jd(b)
        i, j = close_before(D, C, ta), close_before(D, C, tb)
        if i < 0 or j <= i or D[j] > dt.date(2026, 11, 20) or tb.date() > dt.date(2026, 11, 21):
            continue
        c = chart(a, NY[0], NY[1], sid)
        months.append(dict(start=ta, ret=(C[j] / C[i] - 1) * 100, f=features(c), asc=c["asc_sign"]))
    allr = [m["ret"] for m in months]
    up_all = sum(r > 0 for r in allr) / len(allr)
    res = dict(n=len(months), up_all=round(up_all * 100, 1), mean_all=round(statistics.mean(allr), 2), target=round(target, 3), features={})
    for k in months[0]["f"]:
        on = [m["ret"] for m in months if m["f"][k]]
        off = [m["ret"] for m in months if not m["f"][k]]
        if not on:
            res["features"][k] = dict(n=0)
            continue
        se = math.sqrt(statistics.pvariance(on) / len(on) + statistics.pvariance(off) / len(off)) if len(on) > 1 else 1
        t = (statistics.mean(on) - statistics.mean(off)) / se if se else 0
        res["features"][k] = dict(n=len(on), up=round(sum(r > 0 for r in on) / len(on) * 100, 1), mean=round(statistics.mean(on), 2),
                                  mean_off=round(statistics.mean(off), 2), p_up=round(binom_two_sided(sum(r > 0 for r in on), len(on), up_all), 4),
                                  t=round(t, 2), fall5=round(sum(r <= -5 for r in on) / len(on) * 100, 1),
                                  fall5_all=round(sum(r <= -5 for r in allr) / len(allr) * 100, 1))
    return res, months


def describe(c, sid):
    rows = []
    for b in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"):
        p = c["pos"][b]
        rows.append(dict(body=b, sign=p["sign"], deg=f"{int(p['deg'])}°{int((p['deg'] % 1) * 60):02d}'", house=p["house"], nak=p["nak"],
                         retro=p["retro"] and b not in ("Rahu", "Ketu"), neecha=NEECHA.get(b) == p["sign"]))
    a = c["asc"] % 30
    return dict(asc=f"{c['asc_sign']} {int(a)}°{int((a % 1) * 60):02d}'", lagna_lord=c["lagna_lord"], rows=rows)


def main():
    out = dict(versions={}, charts={}, transits={})
    for v in ("A", "B"):
        res, months = backtest(v)
        out["versions"][v] = res
        print(v, res["n"], "months; up", res["up_all"], "% mean", res["mean_all"])
        for k, r in res["features"].items():
            print(f"   {k}: {r}")
    # natal charts
    for name, t, loc in (("NYSE (17 May 1792, 10:00 LMT, New York)", NATAL_NYSE, NY), ("USA (4 Jul 1776, 17:10 LMT, Philadelphia - Sibly)", NATAL_USA, PHILA)):
        x = jd(t)
        out["charts"][name] = dict(tropical=describe(chart(x, loc[0], loc[1], False), False), sidereal=describe(chart(x, loc[0], loc[1], True), True))
    # this month's and the next returns (Solar return's version and ours)
    rets = {}
    for v, sid in (("A", False), ("B", True)):
        target = 27.3 if not sid else lon(jd(NATAL_NYSE), "Sun", True)[0] % 30
        lst = []
        for x in returns(dt.datetime(2026, 10, 1), dt.datetime(2027, 12, 31), target, sid):
            c = chart(x, NY[0], NY[1], sid)
            f = features(c)
            lst.append(dict(start=from_jd(x).astimezone(ET).strftime("%a %d %b %Y %H:%M %Z"), chart=describe(c, sid), flags=[k for k, on in f.items() if on]))
        rets[v] = lst
    out["returns"] = rets
    # transits now (24 Nov 2026, 12:00 ET, sidereal) over the natal charts
    now = jd(dt.datetime(2026, 11, 24, 17, 0))
    tr = chart(now, NY[0], NY[1], True)["pos"]
    for name, t, loc in (("NYSE", NATAL_NYSE, NY), ("USA", NATAL_USA, PHILA)):
        n = chart(jd(t), loc[0], loc[1], True)
        hits = []
        for tb in ("Saturn", "Jupiter", "Rahu", "Ketu", "Mars"):
            for nb in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
                d = abs((tr[tb]["lon"] - n["pos"][nb]["lon"] + 180) % 360 - 180)
                if d <= 5:
                    hits.append(f"transit {tb} within {d:.1f}° of natal {nb}")
                elif abs(d - 180) <= 5:
                    hits.append(f"transit {tb} opposite natal {nb} ({abs(d - 180):.1f}°)")
            h = (int(tr[tb]["lon"] // 30) - int(n["asc"] // 30)) % 12 + 1
            hits.append(f"transit {tb} in natal house {h}")
        out["transits"][name] = hits
    out["forecast"] = dict(source="astrologer's NYSE solar return, shared 24 Nov 2026", month="19 Nov - 18 Dec 2026", start_level=7320,
                           text="Further weakness, but a smaller net monthly decline than the preceding month (-4.8%)", status="open; check on 19 Dec 2026")
    json.dump(out, open(OUT / "nyse_usa_charts_ET.json", "w"), indent=1, default=str)
    write(out)
    for k, v in out["transits"].items():
        print(k, v)
    print(json.dumps(out["returns"]["A"][:3], indent=1)[:1500])


def write(out):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]

    def ftable(res):
        body = ""
        for k, r in res["features"].items():
            if not r.get("n"):
                body += f"<tr><td>{html.escape(k)}</td><td colspan='5'>never</td></tr>"
                continue
            cls = "bearish" if r["mean"] < r["mean_off"] and abs(r["t"]) >= 2 else "bullish" if r["mean"] > r["mean_off"] and abs(r["t"]) >= 2 else ""
            body += (f"<tr class='{cls}'><td>{html.escape(k)}</td><td class='n'>{r['n']}</td><td class='n'><b>{r['up']}%</b> vs {res['up_all']}% (p {r['p_up']})</td>"
                     f"<td class='n'>{r['mean']:+.2f}% vs {r['mean_off']:+.2f}% (t {r['t']})</td><td class='n'>{r['fall5']}% vs {r['fall5_all']}%</td></tr>")
        return (f"<div class='wrap'><table><thead><tr><th>Indication in the monthly chart</th><th>Months</th><th>S&amp;P up</th><th>Average month vs other months</th><th>Months falling 5%+</th></tr></thead>"
                f"<tbody>{body}</tbody></table></div>")

    def ctable(c):
        body = "".join(f"<tr><td><b>{r['body']}</b></td><td>{r['sign']} {r['deg']}</td><td class='n'>{r['house']}</td><td>{r['nak']}</td><td>{'R' if r['retro'] else ''}{' debilitated' if r['neecha'] else ''}</td></tr>" for r in c["rows"])
        return f"<p class='s'>Ascendant {c['asc']} (lord {c['lagna_lord']})</p><div class='wrap'><table><thead><tr><th>Planet</th><th>Position</th><th>House</th><th>Nakshatra</th><th></th></tr></thead><tbody>{body}</tbody></table></div>"
    natal = "".join(f"<h3>{html.escape(k)}</h3><div style='display:grid;grid-template-columns:1fr 1fr;gap:16px'><div><b>Sidereal (Lahiri) – our convention</b>{ctable(v['sidereal'])}</div><div><b>Tropical</b>{ctable(v['tropical'])}</div></div>"
                    for k, v in out["charts"].items())
    rrows = ""
    for v, lst in out["returns"].items():
        for r in lst[:6]:
            p = {x["body"]: x for x in r["chart"]["rows"]}
            rrows += (f"<tr><td>{'A (Solar return, tropical)' if v == 'A' else 'B (ours, sidereal)'}</td><td class='w'>{r['start']}</td><td>{r['chart']['asc']} (lord {r['chart']['lagna_lord']})</td>"
                      f"<td class='s'>8th: {', '.join(b for b in p if p[b]['house'] == 8) or '-'}; 10th: {', '.join(b for b in p if p[b]['house'] == 10) or '-'}</td><td class='s'>{html.escape('; '.join(r['flags']) or 'none')}</td></tr>")
    trows = "".join(f"<tr><td><b>{k}</b></td><td class='s'>{html.escape('; '.join(v))}</td></tr>" for k, v in out["transits"].items())
    A, B = out["versions"]["A"], out["versions"]["B"]
    fc = out["forecast"]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NYSE and USA Charts</title><style>{css}</style></head><body>
<h1>NYSE and USA foundation charts, and the NYSE monthly solar-return technique tested on 98 years of the S&amp;P 500</h1>
<p class="m">Technique (shared 24 Nov 2026; book "Investing in Stock Market with Vedic Astrology", Vol. II): a new NYSE chart each solar month, cast for New York when the Sun returns to the NYSE natal Sun degree in the next sign.
From the shared charts: the natal Sun is 27°18' Taurus <b>tropical</b>, the returns fall when the tropical Sun is at 27°18' of each sign (20 Oct and 19 Nov 2026 confirmed), and the readings use tropical signs —
Capricorn rising and Saturn "debilitated" in Aries. In our sidereal Lahiri convention Saturn is in Pisces (not debilitated), the rising sign is Sagittarius and Mars–Ketu fall in the 9th, so the two readings differ.</p>
<h2>Backtest: does the monthly chart call the S&amp;P month? ({A['n']} months, 1928–2026)</h2>
<h3>A. The Solar return version (tropical returns and houses)</h3>{ftable(A)}
<h3>B. Our convention (sidereal Lahiri returns at the natal sidereal Sun, {B['target']}°, sidereal houses)</h3>{ftable(B)}
<p class="s">Green / red: average month differs from the other months with |t| ≥ 2. All months together: up {A['up_all']}% of the time, average {A['mean_all']:+.2f}%.</p>
<h2>The Solar return open forecast</h2>
<p class="m">{html.escape(fc['month'])}: “{html.escape(fc['text'])}”, from 7,320. Status: {html.escape(fc['status'])}.</p>
<h2>This month's and the next return charts</h2>
<div class="wrap"><table><thead><tr><th>Version</th><th>Return (ET)</th><th>Ascendant</th><th>8th and 10th houses</th><th>Indications present</th></tr></thead><tbody>{rrows}</tbody></table></div>
<h2>Natal charts</h2>{natal}
<p class="s">NYSE: Buttonwood Agreement, 17 May 1792, New York; the time is not recorded – 10:00 LMT gives the 27°18' tropical Sun of the shared charts (the Sun moves only 0.04° an hour, so the time matters only for the ascendant).
USA: 4 July 1776, 17:10 LMT, Philadelphia (the widely used Sibly chart); other times are in use, so its ascendant is uncertain.</p>
<h2>Transits now (24 Nov 2026, sidereal) over the natal charts</h2>
<div class="wrap"><table><tbody>{trows}</tbody></table></div>
<p class="s">Generated by tools/nyse_charts.py. Market prices and astrology only.</p></body></html>"""
    (OUT / "nyse_usa_charts_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
