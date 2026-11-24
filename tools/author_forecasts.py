"""Solar return (the NYSE monthly solar-return astrologer the user follows): transit claims and forecasts, astronomy check,
1928-2026 S&P tests of the aspect rules, and a running scorecard of the forecasts (market prices and astrology only).

    python tools/author_forecasts.py

Method (shared by the user, 24 Nov 2026): NYSE monthly solar returns (months start on the 18th / 19th,
see tools/nyse_charts.py) plus planetary transits read with degree aspects (square, sextile, conjunction).
Aspects between two planets are the same in either zodiac; sign claims (Mercury in Pisces) are checked
in both. Tests on the S&P 500 1928-2026 (daily closes): for each condition, the same-day move and the next
5 sessions against the same years (up share, binomial p), and big days (|move| >= 2%) against the same years.
Forecasts live in FORECASTS below; each is scored from the price files, or Yahoo for days not yet in them.
Writes build/pdfref/author_forecasts_ET.{html,json}.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
import pathlib

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
FL_S = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
FL_T = swe.FLG_SWIEPH | swe.FLG_SPEED
swe.set_sid_mode(swe.SIDM_LAHIRI)
SG = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
B = {"Sun": swe.SUN, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Uranus": swe.URANUS, "Rahu": swe.MEAN_NODE}

# --------------------------------------------------------------------------- forecasts
# kind: "range" = net S&P move between two dates (last close before `start` to close on `end`) with an expected sign / bound;
#       "days"  = the listed sessions' sign; "path" = several checkpoints. Levels and dates are as given in Solar return.
FORECASTS = [
    dict(id="m2026-10", made="before 20 Oct 2026", period="NYSE solar month 20 Oct - 18 Nov 2026", text="Bearish: debilitated ascendant lord Saturn and Mars with Ketu in the 8th.",
         kind="range", start="2026-10-20", end="2026-11-18", expect="down"),
    dict(id="w2026-11-16", made="week of 16 Nov 2026", period="Mon 16 - Fri 20 Nov 2026", text="Lower Monday to Thursday, recovery on Friday.",
         kind="days", days={"2026-11-16": "down", "2026-11-17": "down", "2026-11-18": "down", "2026-11-19": "down", "2026-11-20": "up"}),
    dict(id="m2026-11", made="about 21 Nov 2026", period="NYSE solar month 19 Nov - 18 Dec 2026", text="Further weakness, but a smaller net decline than the previous month's -4.8% (from 7,320).",
         kind="range", start="2026-11-19", end="2026-12-18", expect="down_smaller", bound=-4.8),
    dict(id="w2026-11-23", made="about 22 Nov 2026", period="Mon 23 - Fri 27 Nov 2026", text="Pressure in the first half of the week (Mon-Wed); Friday recovery (Jupiter-Venus sextile); volatile, rebound toward the end.",
         kind="days", days={"2026-11-23": "down", "2026-11-24": "down", "2026-11-25": "down", "2026-11-27": "up"}),
    dict(id="y2026-27", made="early Nov 2026", period="Oct 2026 - Oct 2027", text="Weak from late 2026 through spring 2027, bottom around Mar-May 2027, recovery from May-June, strong second half with a sustained advance through Dec 2027.",
         kind="path", checkpoints=[("2026-11-01", "2027-03-01", "down", "weak late 2026 to Feb 2027"),
                                   ("2027-03-01", "2027-05-31", "low", "bottom around Mar-May 2027 (the year's low falls in this window)"),
                                   ("2027-06-01", "2027-12-31", "up", "advance from June through December 2027")]),
]


def prices():
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv"))]
    d = dict(rows)
    try:  # sessions after the file's last date
        import urllib.request
        from zoneinfo import ZoneInfo
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=3mo&interval=1d",
                                                                     headers={"User-Agent": "Mozilla/5.0"}), timeout=30))["chart"]["result"][0]
        for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
            day = dt.datetime.fromtimestamp(t, ZoneInfo("America/New_York")).date()
            if c and day not in d:
                d[day] = c
        today = dt.datetime.now(ZoneInfo("America/New_York"))
        if today.time() < dt.time(16, 15):          # an unfinished session is not a close
            d.pop(today.date(), None)
    except Exception:
        pass
    return dict(sorted(d.items()))


def score(f, P):
    D = list(P)
    last = D[-1]

    def close_before(day):
        prev = [x for x in D if x < day]
        return prev[-1] if prev else None
    if f["kind"] == "range":
        a, b = dt.date.fromisoformat(f["start"]), dt.date.fromisoformat(f["end"])
        i = close_before(a)
        if b > last:
            mv = (P[last] / P[i] - 1) * 100 if i else None
            return dict(status="open", detail=f"so far {P[i]:,.0f} → {P[last]:,.0f} ({mv:+.1f}%) to {last}")
        mv = (P[b] / P[i] - 1) * 100
        ok = mv < 0 if f["expect"] == "down" else (f["bound"] < mv < 0)
        return dict(status="right" if ok else "wrong", detail=f"{P[i]:,.0f} → {P[b]:,.0f} ({mv:+.1f}%)")
    if f["kind"] == "days":
        res, hits, n = [], 0, 0
        for day, exp in f["days"].items():
            d = dt.date.fromisoformat(day)
            if d not in P:
                res.append(f"{d:%a %d %b}: pending")
                continue
            i = close_before(d)
            mv = (P[d] / P[i] - 1) * 100
            ok = (mv < 0) == (exp == "down")
            hits += ok
            n += 1
            res.append(f"{d:%a %d %b}: said {exp}, {mv:+.2f}% {'✓' if ok else '✗'}")
        pending = n < len(f["days"])
        return dict(status=("open" if pending else "right" if hits == n else "partly right" if hits else "wrong") + f" ({hits}/{n})", detail="; ".join(res))
    if f["kind"] == "path":
        out = []
        for a, b, exp, label in f["checkpoints"]:
            a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
            if b > last:
                out.append(f"{label}: open")
                continue
            i = close_before(a)
            mv = (P[b] / P[i] - 1) * 100
            out.append(f"{label}: {mv:+.1f}%")
        return dict(status="open", detail="; ".join(out))


# --------------------------------------------------------------------------- astronomy check
def lonspd(d, body, sid=True):
    r = swe.calc_ut(swe.julday(d.year, d.month, d.day, 17), B[body], FL_S if sid else FL_T)[0]
    return r[0] % 360, r[3]


def sep(a, b):
    return abs((a - b + 180) % 360 - 180)


def astro_checks():
    out = []
    days = [dt.date(2026, 11, 1) + dt.timedelta(days=i) for i in range(0, 260)]
    # Mars stations
    prev = None
    stations = []
    for d in days:
        m, s = lonspd(d, "Mars")
        if prev is not None and (prev < 0) != (s < 0):
            ke_m = (lonspd(d, "Rahu")[0] + 180) % 360
            ke_t = (swe.calc_ut(swe.julday(d.year, d.month, d.day, 17), swe.TRUE_NODE, FL_S)[0][0] + 180) % 360
            stations.append((d, "retrograde" if s < 0 else "direct", m, sep(m, ke_m), sep(m, ke_t)))
        prev = s
    st_r = [x for x in stations if x[1] == "retrograde"]
    st_d = [x for x in stations if x[1] == "direct"]
    out.append(dict(claim="Mars is approaching Ketu (conjunction associated with disruption)", status="holds",
                    note="Mars and Ketu were within 1° in Leo about 14-16 Nov 2026 (0.8° on 16 Nov), then separated"))
    if st_r:
        d, _, m, *_ = st_r[0]
        out.append(dict(claim="Mars turns retrograde in February 2027", status="wrong (date)", note=f"Mars stations retrograde on {d:%d %b %Y} at {SG[int(m // 30)]} {m % 30:.1f}° (sidereal); it is retrograde through February"))
    sq = [d for d in days if abs(sep(lonspd(d, "Mars")[0], lonspd(d, "Uranus")[0]) - 90) < 0.5 and lonspd(d, "Mars")[1] < 0]
    out.append(dict(claim="Retrograde Mars squares Uranus (February 2027)", status="holds" if sq else "wrong",
                    note=f"exact square while Mars is retrograde: {sq[0]:%d} – {sq[-1]:%d %b %Y}" if sq else ""))
    pis_t = [d for d in days if SG[int(lonspd(d, "Mercury", False)[0] // 30)] == "Pisces"]
    pis_s = [d for d in days if SG[int(lonspd(d, "Mercury")[0] // 30)] == "Pisces"]
    out.append(dict(claim="Mercury enters debilitation (Pisces) in February 2027", status="tropical only",
                    note=f"tropical Pisces {pis_t[0]:%d %b} – {pis_t[-1]:%d %b %Y}; sidereal (our convention) Pisces only {pis_s[0]:%d %b} – {pis_s[-1]:%d %b %Y}"))
    if st_d:
        d, _, m, km, kt = st_d[0]
        out.append(dict(claim="In April 2027 retrograde Mars comes within 1° of Ketu before turning direct", status="close, not within 1°",
                        note=f"Mars stations direct on {d:%d %b %Y} at {SG[int(m // 30)]} {m % 30:.1f}°; distance to Ketu {kt:.1f}° (true node) / {km:.1f}° (mean node)"))
    sun_mk = [d for d in days if abs(sep(lonspd(d, "Sun")[0], lonspd(d, "Mars")[0]) - 90) < 2]
    out.append(dict(claim="Sun square the Mars-Ketu pair (week of 16-20 Nov 2026)", status="holds", note=f"Sun-Mars within 2° of a square {sun_mk[0]:%d} – {sun_mk[0] + dt.timedelta(days=6):%d %b}, exact about 19 Nov"))
    near = lambda d: abs(sep(lonspd(d, "Jupiter")[0], lonspd(d, "Venus")[0]) - 60) < 1      # noqa: E731
    d27 = dt.date(2026, 11, 27)
    a = b = d27
    while near(a - dt.timedelta(days=1)):
        a -= dt.timedelta(days=1)
    while near(b + dt.timedelta(days=1)):
        b += dt.timedelta(days=1)
    out.append(dict(claim="Jupiter-Venus sextile on Fri 27 Nov 2026", status="holds" if near(d27) else "wrong",
                    note=f"within 1°: {a:%d} – {b:%d %b}, exact about 28 Nov" if near(d27) else ""))
    out.append(dict(claim="(our note) Mars, Jupiter and Ketu together again in Cancer", status="holds",
                    note="9 Mar – 26 Apr 2027: our Mars-Jupiter-node lead (bottoms in 2009 and 2020 came within 3 sessions of such an episode ending); its end on 26 Apr falls inside the Solar return Mar-May bottom window"))
    return out


# --------------------------------------------------------------------------- aspect tests 1928-2026
def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


def tests():
    P = {d: c for d, c in prices().items() if d <= dt.date(2026, 11, 20)}
    D = list(P)
    C = [P[d] for d in D]
    conds = {
        "Sun square Mars (within 3°) – Solar return: bearish": lambda x: abs(sep(x["Sun"], x["Mars"]) - 90) < 3,
        "Sun square Mars with Mars-Ketu within 8° – Solar return: bearish": lambda x: abs(sep(x["Sun"], x["Mars"]) - 90) < 3 and sep(x["Mars"], x["Ketu"]) < 8,
        "Mars conjunct Ketu (within 5°) – Solar return: disruption": lambda x: sep(x["Mars"], x["Ketu"]) < 5,
        "Jupiter sextile Venus (within 2°) – Solar return: bullish": lambda x: abs(sep(x["Jupiter"], x["Venus"]) - 60) < 2,
        "Mars square Uranus (within 3°) – Solar return: volatility": lambda x: abs(sep(x["Mars"], x["Uranus"]) - 90) < 3,
        "Mars retrograde": lambda x: x["mars_spd"] < 0,
        "Mercury in Pisces, tropical – Solar return: unfavourable": lambda x: SG[int(x["mer_t"] // 30)] == "Pisces",
        "Mercury in Pisces, sidereal": lambda x: SG[int(x["Mercury"] // 30)] == "Pisces",
    }
    rows = []
    for i, d in enumerate(D):
        if i == 0 or i + 5 >= len(D):
            continue
        jd = swe.julday(d.year, d.month, d.day, 19)
        x = {b: swe.calc_ut(jd, k, FL_S)[0][0] % 360 for b, k in B.items()}
        x["Ketu"] = (x["Rahu"] + 180) % 360
        x["mars_spd"] = swe.calc_ut(jd, swe.MARS, FL_S)[0][3]
        x["mer_t"] = swe.calc_ut(jd, swe.MERCURY, FL_T)[0][0] % 360
        rows.append(dict(d=d, r=(C[i] / C[i - 1] - 1) * 100, r5=(C[i + 4] / C[i - 1] - 1) * 100, x=x))
    yr = {}
    for r in rows:
        y = yr.setdefault(nov_year(r["d"]), [0, 0, 0, 0])
        y[0] += 1
        y[1] += r["r"] > 0
        y[2] += r["r5"] > 0
        y[3] += abs(r["r"]) >= 2
    res = {}
    for k, f in conds.items():
        sel = [r for r in rows if f(r["x"])]
        if not sel:
            continue
        e1 = sum(yr[nov_year(r["d"])][1] / yr[nov_year(r["d"])][0] for r in sel)
        e5 = sum(yr[nov_year(r["d"])][2] / yr[nov_year(r["d"])][0] for r in sel)
        eb = sum(yr[nov_year(r["d"])][3] / yr[nov_year(r["d"])][0] for r in sel)
        u1, u5, bg = sum(r["r"] > 0 for r in sel), sum(r["r5"] > 0 for r in sel), sum(abs(r["r"]) >= 2 for r in sel)
        n = len(sel)

        def p2(k_, e):
            z = (k_ - e) / (math.sqrt(e * (1 - e / n)) or 1)
            return round(math.erfc(abs(z) / math.sqrt(2)), 4)
        # each episode once: S&P from the close before its first day to 5 sessions later
        idx = {r["d"]: j for j, r in enumerate(rows)}
        eps, last = [], None
        for r in sel:
            j = idx[r["d"]]
            if last is None or j - last > 1:
                eps.append(j)
            last = j
        eu = sum(rows[j]["r5"] > 0 for j in eps)
        ee = sum(yr[nov_year(rows[j]["d"])][2] / yr[nov_year(rows[j]["d"])][0] for j in eps)
        lam, kk = eb, bg
        term = math.exp(-lam) if lam < 700 else 0.0
        cdf = term
        for i_ in range(1, kk):
            term *= lam / i_
            cdf += term
        res[k] = dict(n=n, up1=round(u1 / n * 100, 1), exp1=round(e1 / n * 100, 1), p1=p2(u1, e1), up5=round(u5 / n * 100, 1), exp5=round(e5 / n * 100, 1), p5=p2(u5, e5),
                      big=bg, exp_big=round(eb, 1), p_big=round(max(0.0, 1 - cdf), 4), mean1=round(sum(r["r"] for r in sel) / n, 3),
                      eps=len(eps), eps_up5=round(eu / len(eps) * 100, 1), eps_exp5=round(ee / len(eps) * 100, 1),
                      eps_p=round(math.erfc(abs((eu - ee) / (math.sqrt(ee * (1 - ee / len(eps))) or 1)) / math.sqrt(2)), 4))
    return res


def main():
    P = prices()
    fc = [dict(f, score=score(f, P)) for f in FORECASTS]
    ac = astro_checks()
    ts = tests()
    out = dict(forecasts=fc, astronomy=ac, tests=ts, last_price=str(list(P)[-1]))
    json.dump(out, open(OUT / "author_forecasts_ET.json", "w"), indent=1, default=str)
    write(out)
    for f in fc:
        print(f["id"], f["score"])
    for a in ac:
        print(a["status"], "|", a["claim"], "|", a["note"])
    for k, r in ts.items():
        print(k, r)


def write(out):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    cls = {"right": "bullish", "wrong": "bearish"}
    frows = "".join(f"<tr class='{cls.get(f['score']['status'].split(' ')[0], 'mixed' if f['score']['status'].startswith('partly') else '')}'><td class='w'><b>{html.escape(f['period'])}</b><div class='s'>made {html.escape(f['made'])}</div></td>"
                    f"<td>{html.escape(f['text'])}</td><td><b>{html.escape(f['score']['status'])}</b></td><td class='s'>{html.escape(f['score']['detail'])}</td></tr>" for f in out["forecasts"])
    acls = {"holds": "bullish", "wrong": "bearish", "wrong (date)": "bearish"}
    arows = "".join(f"<tr class='{acls.get(a['status'], 'mixed')}'><td>{html.escape(a['claim'])}</td><td><b>{a['status']}</b></td><td class='s'>{html.escape(a['note'])}</td></tr>" for a in out["astronomy"])
    trows = "".join(f"<tr><td><b>{html.escape(k)}</b></td><td class='n'>{r['n']}</td><td class='n'>{r['up1']}% vs {r['exp1']}% (p {r['p1']})</td><td class='n'>{r['up5']}% vs {r['exp5']}% (p {r['p5']})</td>"
                    f"<td class='n'>{r['eps']} episodes: {r['eps_up5']}% vs {r['eps_exp5']}% (p {r['eps_p']})</td><td class='n'>{r['big']} vs {r['exp_big']} (p {r['p_big']})</td></tr>" for k, r in out["tests"].items())
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Solar Return Forecasts</title><style>{css}</style></head><body>
<h1>Solar return: forecasts, transit claims and aspect rules tested</h1>
<p class="m">Solar return is the NYSE monthly solar-return astrologer whose material the user shares. Method: NYSE monthly solar returns (months start on the 18th / 19th; tools/nyse_charts.py) plus transits read with degree aspects. Market prices and astrology only. S&amp;P prices to {out['last_price']}.</p>
<h2>Forecast scorecard</h2>
<div class="wrap"><table><thead><tr><th>Period</th><th>Forecast</th><th>Score</th><th>S&amp;P 500</th></tr></thead><tbody>{frows}</tbody></table></div>
<h2>Are the transit statements astronomically right? (sidereal Lahiri unless stated)</h2>
<div class="wrap"><table><thead><tr><th>Claim</th><th>Check</th><th>Detail</th></tr></thead><tbody>{arows}</tbody></table></div>
<h2>Solar return aspect rules on the S&amp;P 500, 1928–2026 (daily)</h2>
<p class="s">Same-day move and next 5 sessions: share up on days with the condition, against the same years; big days (±2%) against the same years. Consecutive days overlap, so the episode column (each run of days counted once) is the fair test of direction.</p>
<div class="wrap"><table><thead><tr><th>Condition</th><th>Days</th><th>Same day up</th><th>Next 5 sessions up (all days)</th><th>Each episode once: next 5 sessions up</th><th>Big days vs expected</th></tr></thead><tbody>{trows}</tbody></table></div>
<p class="s">Generated by tools/author_forecasts.py. New forecasts go into FORECASTS in the script.</p></body></html>"""
    (OUT / "author_forecasts_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
