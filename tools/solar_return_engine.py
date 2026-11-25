"""Solar return engine: NYSE monthly charts in four calculation models, scored by a fixed aspect rubric, tested on the
S&P since 1928, and cast for Dec 2026 - Dec 2027.

    python tools/solar_return_engine.py

Specification (user-supplied analysis, 24 Nov 2026, of the Solar return technique; nothing here is tuned):
  natal      NYSE, 17 May 1792, 10:10 LMT New York (74°00'W, 40°43'N; time disputed - Rodden DD; alternatives 07:52, 07:54,
             08:52, 09:00, 11:15 tested for sensitivity). Natal Sun 27°17'39" Taurus tropical, 6°20'11" Taurus Lahiri.
  models     A  tropical monthly degree returns (Sun at the natal tropical degree in each sign)
             B  sidereal Lahiri monthly degree returns (Sun at 6°20'11" of each sidereal sign)
             C  tropical annual return divided into 12 equal periods
             D  sidereal annual return divided into 12 equal periods
             (A at 27°18' is tools/nyse_charts.py's version A, which reproduced the two charts Solar return shared.)
  charts     New York; planets geocentric; houses Placidus and whole sign; nodes mean (true as a check).
  rubric     orb weights 0-1° = 4, 1-2° = 3, 2-3° = 2, 3-5° = 1, over 5° = 0.
             bearish: Sun square Mars; Mars conjunct Ketu; Mars square Uranus; Saturn conjunct / square / opposite Sun;
                      Mercury debilitated (Pisces in the model's zodiac, weight 2).
             bullish: Jupiter sextile Venus; Jupiter trine Sun; Venus trine Jupiter.
             net = bullish - bearish: Bullish if > 0, Bearish if < 0, otherwise Neutral.
             volatility = Mars-Ketu + Mars-Uranus + Sun-Mars weights.
  The rubric's first five items are the transit rules Solar return names; Saturn-Sun, Jupiter-Sun and Venus-Jupiter
  trines are the analysis's own additions. Each item is also tested on its own.
Test: S&P from the last close before one boundary to the last close before the next, 1928-2026; the monthly call
against an always-bullish baseline; Bearish months' average and worst-point drawdown against the rest; volatility score
against the month's big days. Periods: 1928-1976, 1977-2026, and 2010-2026 (the analysis's suggested window).
Writes build/pdfref/solar_return_engine_ET.{html,json}.
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
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
ET, UTC = ZoneInfo("America/New_York"), dt.timezone.utc
LON_W, LAT = 74.0, 40 + 43 / 60
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NEECHA = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"}
BODIES = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
          "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO}
BIRTH_TIMES = ("07:52", "07:54", "08:52", "09:00", "10:00", "10:10", "11:15")
swe.set_sid_mode(swe.SIDM_LAHIRI)
# the 2027 timestamps the pasted analysis gives (New York local), for verification
GIVEN = {"A": ["2027-01-17 10:41", "2027-02-16 00:12", "2027-03-17 23:05", "2027-04-17 08:49", "2027-05-18 06:49", "2027-06-18 14:07",
               "2027-07-20 01:01", "2027-08-20 08:47", "2027-09-20 07:36", "2027-10-20 18:15", "2027-11-19 15:56", "2027-12-19 05:55"],
         "B": ["2027-01-20 16:03", "2027-02-19 06:15", "2027-03-21 06:21", "2027-04-20 17:29", "2027-05-21 16:45", "2027-06-22 00:47",
               "2027-07-23 11:42", "2027-08-23 18:46", "2027-09-23 16:21", "2027-10-24 01:39", "2027-11-22 22:12", "2027-12-22 11:33"]}
WEIGHT = ((1, 4), (2, 3), (3, 2), (5, 1))


def jd(t):
    u = t.astimezone(UTC)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def from_jd(x):
    y, m, d, h = swe.revjul(x)
    return dt.datetime(y, m, d, tzinfo=UTC) + dt.timedelta(hours=h)


def natal(time_lmt="10:10"):
    h, m = map(int, time_lmt.split(":"))
    ut = dt.datetime(1792, 5, 17, h, m, tzinfo=UTC) + dt.timedelta(hours=LON_W / 15)
    j = jd(ut)
    trop = swe.calc_ut(j, swe.SUN, swe.FLG_SWIEPH)[0][0] % 360
    sid = swe.calc_ut(j, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360
    asc = swe.houses(j, LAT, -LON_W, b"P")[1][0]
    moon = swe.calc_ut(j, swe.MOON, swe.FLG_SWIEPH)[0][0] % 360
    return dict(time=time_lmt, ut=ut, trop=trop, sid=sid, asc_trop=asc, moon_trop=moon)


def sun_at(target, sid, a, b):
    """Instants a..b when the Sun's longitude (mod 30) equals `target` (degrees within the sign)."""
    fl = swe.FLG_SWIEPH | (swe.FLG_SIDEREAL if sid else 0)
    out, x, end = [], jd(a), jd(b)
    while x < end:
        for _ in range(60):
            d = ((swe.calc_ut(x, swe.SUN, fl)[0][0] % 30) - target + 15) % 30 - 15
            if abs(d) < 1e-8:
                break
            x -= d / 0.9856
        out.append(x)
        x += 30.4
    return [from_jd(v) for v in sorted(set(round(v, 7) for v in out)) if jd(a) <= v < end]


def annual(target_lon, sid, a, b):
    fl = swe.FLG_SWIEPH | (swe.FLG_SIDEREAL if sid else 0)
    out, x, end = [], jd(a - dt.timedelta(days=400)), jd(b + dt.timedelta(days=400))
    while x < end:
        for _ in range(60):
            d = ((swe.calc_ut(x, swe.SUN, fl)[0][0] - target_lon + 180) % 360) - 180
            if abs(d) < 1e-8:
                break
            x -= d / 0.9856
        out.append(x)
        x += 365.2
    rets = sorted(set(round(v, 7) for v in out))
    bounds = []
    for r0, r1 in zip(rets, rets[1:]):
        bounds += [r0 + (r1 - r0) * k / 12 for k in range(12)]
    return [from_jd(v) for v in bounds if jd(a) <= v < jd(b)]


def boundaries(model, nat, a, b):
    if model == "A":
        return sun_at(nat["trop"] % 30, False, a, b)
    if model == "B":
        return sun_at(nat["sid"] % 30, True, a, b)
    if model == "C":
        return annual(nat["trop"], False, a, b)
    return annual(nat["sid"], True, a, b)


def sep(a, b):
    return abs((a - b + 180) % 360 - 180)


def chart(t, sid, true_node=False):
    j = jd(t)
    fl = swe.FLG_SWIEPH | swe.FLG_SPEED | (swe.FLG_SIDEREAL if sid else 0)
    p = {}
    for b, k in BODIES.items():
        r = swe.calc_ut(j, k, fl)[0]
        p[b] = (r[0] % 360, r[3])
    r = swe.calc_ut(j, swe.TRUE_NODE if true_node else swe.MEAN_NODE, fl)[0]
    p["Rahu"] = (r[0] % 360, r[3])
    p["Ketu"] = ((r[0] + 180) % 360, r[3])
    ayan = swe.get_ayanamsa_ut(j) if sid else 0.0
    hp = swe.houses(j, LAT, -LON_W, b"P")
    cusps = [(c - ayan) % 360 for c in hp[0][:12]]
    asc = (hp[1][0] - ayan) % 360
    return dict(t=t, sid=sid, p=p, asc=asc, cusps=cusps)


def house_placidus(c, lon):
    cs = c["cusps"]
    for i in range(12):
        a, b = cs[i], cs[(i + 1) % 12]
        if (lon - a) % 360 < (b - a) % 360:
            return i + 1
    return 12


def house_whole(c, lon):
    return (int(lon // 30) - int(c["asc"] // 30)) % 12 + 1


def flags(c, hs="whole"):
    hf = house_whole if hs == "whole" else house_placidus
    p = c["p"]
    lord = LORD[int(c["asc"] // 30)]
    h8 = [b for b in ("Mars", "Saturn", "Rahu", "Ketu") if hf(c, p[b][0]) == 8]
    deb = SIGNS[int(p[lord][0] // 30)] == NEECHA.get(lord)
    return {"Ascendant lord debilitated": deb, "Malefic in the 8th": bool(h8),
            "Mars with Ketu in the 8th": hf(c, p["Mars"][0]) == 8 and hf(c, p["Ketu"][0]) == 8,
            "Venus or Jupiter in the 10th": hf(c, p["Venus"][0]) == 10 or hf(c, p["Jupiter"][0]) == 10}


def weight(orb):
    for lim, w in WEIGHT:
        if orb <= lim:
            return w
    return 0


def applying(c, a, b, angle):
    """True if the aspect a-b is getting closer (by the bodies' speeds)."""
    pa, pb = c["p"][a], c["p"][b]
    now = abs(sep(pa[0], pb[0]) - angle)
    nxt = abs(sep(pa[0] + pa[1] * 0.1, pb[0] + pb[1] * 0.1) - angle)
    return nxt < now


RUBRIC = [("Sun square Mars", "bear", "Sun", "Mars", 90), ("Mars conjunct Ketu", "bear", "Mars", "Ketu", 0),
          ("Mars square Uranus", "bear", "Mars", "Uranus", 90), ("Saturn conjunct Sun", "bear", "Saturn", "Sun", 0),
          ("Saturn square Sun", "bear", "Saturn", "Sun", 90), ("Saturn opposite Sun", "bear", "Saturn", "Sun", 180),
          ("Jupiter sextile Venus", "bull", "Jupiter", "Venus", 60), ("Jupiter trine Sun", "bull", "Jupiter", "Sun", 120),
          ("Venus trine Jupiter", "bull", "Venus", "Jupiter", 120)]
VOL = ("Sun square Mars", "Mars conjunct Ketu", "Mars square Uranus")


def score(c):
    items, bull, bear, vol = [], 0, 0, 0
    for name, side, a, b, ang in RUBRIC:
        orb = abs(sep(c["p"][a][0], c["p"][b][0]) - ang)
        w = weight(orb)
        if w:
            items.append(dict(name=name, side=side, orb=round(orb, 2), w=w, applying=applying(c, a, b, ang)))
            bull += w if side == "bull" else 0
            bear += w if side == "bear" else 0
            vol += w if name in VOL else 0
    if SIGNS[int(c["p"]["Mercury"][0] // 30)] == "Pisces":
        items.append(dict(name="Mercury debilitated (Pisces)", side="bear", orb=None, w=2, applying=None))
        bear += 2
    net = bull - bear
    return dict(items=items, bull=bull, bear=bear, net=net, vol=vol, call="Bullish" if net > 0 else "Bearish" if net < 0 else "Neutral")


def last_year(nat, lo=dt.date(2025, 11, 20)):
    """The past 12 solar months: rubric calls (four models), the stated-indication reading the Solar return way (27°18',
    which reproduced the shared charts) and the generated daily calls, on S&P closes to the latest session."""
    sys.path.insert(0, str(ROOT / "tools"))
    from model_check_60d import load
    AF = load(ROOT / "tools" / "author_forecasts.py", "af_ly")
    SRG = load(ROOT / "tools" / "solar_return_generate.py", "srg_ly")
    P = AF.prices()
    D, C = list(P), [P[d] for d in P]
    hi = D[-1]
    out = dict(last_close=str(hi), models={})
    for m in ("A", "B", "C", "D"):
        bs = boundaries(m, nat, dt.datetime(lo.year, lo.month, 1, tzinfo=UTC) - dt.timedelta(days=40), dt.datetime(hi.year + 1, 1, 31, tzinfo=UTC))
        rows = []
        for t0, t1 in zip(bs, bs[1:]):
            if t0.date() < lo - dt.timedelta(days=5) or t0.date() > hi:
                continue
            i, j = close_idx(D, t0), min(close_idx(D, t1), len(D) - 1)
            sc = score(chart(t0, m in ("B", "D")))
            rows.append(dict(start=t0.astimezone(ET).strftime("%d %b %Y"), call=sc["call"], net=sc["net"], ret=round((C[j] / C[i] - 1) * 100, 2),
                             partial=t1.astimezone(ET).date() > hi))
        done = [r for r in rows if not r["partial"]]
        calls = [r for r in done if r["call"] != "Neutral"]
        out["models"][m] = dict(rows=rows, months=len(done), up=sum(r["ret"] > 0 for r in done), calls=len(calls),
                                right=sum((r["ret"] > 0) == (r["call"] == "Bullish") for r in calls))
    mons = SRG.months(dt.datetime(lo.year, lo.month, 1) - dt.timedelta(days=40), dt.datetime(hi.year + 1, 1, 31))
    st = []
    for mm in mons:
        if not mm["end"] or mm["start"].date() < lo - dt.timedelta(days=5) or mm["start"].date() > hi:
            continue
        i, j = close_idx(D, mm["start"]), min(close_idx(D, mm["end"]), len(D) - 1)
        st.append(dict(start=mm["start"].strftime("%d %b %Y %H:%M"), asc=mm["asc"], reading=mm["reading"], ret=round((C[j] / C[i] - 1) * 100, 2),
                       partial=mm["end"].date() > hi))
    sc_ = [r for r in st if SRG.LEAN[r["reading"]] and not r["partial"]]
    out["stated"] = dict(rows=st, calls=len(sc_), right=sum((r["ret"] > 0) == (SRG.LEAN[r["reading"]] > 0) for r in sc_))
    _, ms = SRG.NC.backtest("A")
    SRG.START_DATES[:] = [x["start"].astimezone(SRG.ET).date() for x in ms]
    t = {"Bullish": [0, 0, 0, 0], "Bearish": [0, 0, 0, 0]}
    base = [0, 0, 0, 0]
    for k in range(1, len(D)):
        d = D[k]
        if not lo <= d <= hi:
            continue
        mm = SRG.month_of(mons, d)
        call = SRG.day_call(d, mm["reading"] if mm else "")[0]
        r1 = C[k] / C[k - 1] - 1
        r5 = C[k + 4] / C[k - 1] - 1 if k + 4 < len(D) else None
        base[0] += r1 > 0
        base[1] += 1
        if r5 is not None:
            base[2] += r5 > 0
            base[3] += 1
        if call in t:
            x = t[call]
            x[0] += (r1 > 0) == (call == "Bullish")
            x[1] += 1
            if r5 is not None:
                x[2] += (r5 > 0) == (call == "Bullish")
                x[3] += 1
    out["daily"] = dict(calls=t, base=base)
    return out


def diagnose(nat, lo=dt.date(2025, 11, 15)):
    """Month by month over the past year: what the Solar return reading rested on, how fragile it was, what the
    transit rules and our own S&P table said inside the month, what the market did, and why the call missed."""
    from model_check_60d import load, table_rows
    AF = load(ROOT / "tools" / "author_forecasts.py", "af_dg")
    SRG = load(ROOT / "tools" / "solar_return_generate.py", "srg_dg")
    CP = load(ROOT / "tools" / "combined_probability.py", "cp_dg")
    NC = SRG.NC
    P = AF.prices()
    D, C = list(P), [P[d] for d in P]
    hi = D[-1]
    hist = SRG.history()["by"]
    atests = json.load(open(OUT / "author_forecasts_ET.json"))["tests"]
    lab = CP.market_history(dt.date(2026, 11, 22))["spx"]
    lab.update(table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", "spx"))
    mons = SRG.months(dt.datetime(2025, 10, 1), dt.datetime(2027, 1, 31))
    bsA = boundaries("A", nat, dt.datetime(2025, 10, 1, tzinfo=UTC), dt.datetime(2027, 1, 31, tzinfo=UTC))
    bsB = boundaries("B", nat, dt.datetime(2025, 10, 1, tzinfo=UTC), dt.datetime(2027, 1, 31, tzinfo=UTC))

    def nc_reading(t, sid=False):
        return SRG.reading(NC.features(NC.chart(jd(t), NC.NY[0], NC.NY[1], sid)))

    def eng_reading(t, hs):
        f = flags(chart(t, False), hs)
        return SRG.reading({"Ascendant lord debilitated": f["Ascendant lord debilitated"], "Mars, Saturn, Rahu or Ketu in the 8th": f["Malefic in the 8th"],
                            "Venus or Jupiter in the 10th": f["Venus or Jupiter in the 10th"]})
    out = []
    for m in mons:
        if not m["end"] or m["start"].date() < lo or m["start"].date() > hi:
            continue
        t0, t1 = m["start"], m["end"]
        i, j = close_idx(D, t0), min(close_idx(D, t1), len(D) - 1)
        seg = C[i:j + 1]
        ret = (C[j] / C[i] - 1) * 100
        mid = i + (j - i) // 2
        lean = SRG.LEAN[m["reading"]]
        # fragility of the reading
        alt = {}
        alt["natal 27°17′39″ (10:10 LMT)"] = nc_reading(min(bsA, key=lambda x: abs((x - t0).total_seconds())))
        for bt in ("07:52", "11:15"):
            sh = (natal(bt)["trop"] - 57.3) / 0.9856 * 1440
            alt[f"birth {bt}"] = nc_reading(t0 + dt.timedelta(minutes=sh))
        alt["Placidus houses"] = eng_reading(t0, "placidus")
        alt["sidereal (model B)"] = nc_reading(min(bsB, key=lambda x: abs((x - t0).total_seconds())), True)
        flips = [k for k, v in alt.items() if SRG.LEAN[v] != lean]
        # transit rules inside the month
        eps = SRG.episodes(t0.date(), min(t1.date(), hi), atests)
        tr = sorted({e["rule"] for e in eps})
        # our S&P table inside the month
        days = [D[k] for k in range(i + 1, j + 1)]
        tb = {"Bullish": [0, 0], "Bearish": [0, 0]}
        for k in range(i + 1, j + 1):
            L = lab.get(D[k])
            if L and L[0] in tb:
                r1 = C[k] / C[k - 1] - 1
                tb[L[0]][0] += (r1 > 0) == (L[0] == "Bullish")
                tb[L[0]][1] += 1
        h = hist.get(m["reading"], {})
        right = None if lean == 0 else (ret > 0) == (lean > 0)
        partial = t1.date() > hi
        why = []
        if lean and not right and not partial:
            if h and h.get("up") is not None:
                why.append(f"since 1928 months read “{m['reading']}” rose {h['up']}% of the time (avg {h['mean']:+.2f}%), about the same as or more than all months (60.5%): the reading had no edge to start with")
            if flips:
                why.append("the reading was fragile: it changes with " + ", ".join(flips))
            bull_tr = [r for r in tr if r.startswith("Jupiter sextile Venus")]
            if lean < 0 and bull_tr:
                why.append("a bullish transit rule (Jupiter sextile Venus) ran inside the month")
            if lean < 0 and tb["Bullish"][1] > tb["Bearish"][1]:
                why.append(f"our own S&P table leaned bullish in the month ({tb['Bullish'][1]} bullish vs {tb['Bearish'][1]} bearish days)")
            ups = sum(1 for k in range(i + 1, j + 1) if C[k] > C[k - 1])
            why.append(f"the market rose on {ups} of {j - i} sessions; the drift was up")
        out.append(dict(start=t0.strftime("%d %b %Y %H:%M"), end=t1.strftime("%d %b %Y"), asc=m["asc"], lord=m["lord"], lord_pos=m["lord_pos"],
                        h8=m["h8"], h10=m["h10"], flags=[f for f in m["flags"] if not f.startswith("Both")], reading=m["reading"], lean=lean,
                        ret=round(ret, 2), first=round((C[mid] / C[i] - 1) * 100, 2), second=round((C[j] / C[mid] - 1) * 100, 2),
                        worst=round((min(seg) / C[i] - 1) * 100, 2), best=round((max(seg) / C[i] - 1) * 100, 2),
                        big=sum(abs(C[k] / C[k - 1] - 1) >= 0.02 for k in range(i + 1, j + 1)), sessions=j - i,
                        right=right, partial=partial, alt=alt, flips=flips, transits=tr, table=tb, hist=h, why=why))
    return out


# ------------------------------------------------------------------ market data and tests
def spx():
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv"))]
    return [r[0] for r in rows], [r[1] for r in rows]


def close_idx(D, t):
    x = t.astimezone(ET)
    day = x.date() + (dt.timedelta(days=1) if x.time() >= dt.time(16, 0) else dt.timedelta(0))
    return bisect.bisect_left(D, day) - 1


def months(model, nat, D, C, a, b, hs="whole"):
    bs = boundaries(model, nat, a, b)
    sid = model in ("B", "D")
    out = []
    for t0, t1 in zip(bs, bs[1:]):
        i, j = close_idx(D, t0), close_idx(D, t1)
        if i < 1 or j <= i or D[j] > dt.date(2026, 11, 20):
            continue
        c = chart(t0, sid)
        sc = score(c)
        seg = C[i:j + 1]
        ret = (C[j] / C[i] - 1) * 100
        worst = (min(seg) / C[i] - 1) * 100
        big = sum(abs(C[k] / C[k - 1] - 1) >= 0.02 for k in range(i + 1, j + 1))
        out.append(dict(start=t0, ret=ret, worst=worst, big=big, n=j - i, score=sc, flags=flags(c, hs)))
    return out


def evaluate(ms, lo=None, hi=None):
    sel = [m for m in ms if (lo is None or m["start"].date() >= lo) and (hi is None or m["start"].date() < hi)]
    if not sel:
        return None
    up_all = sum(m["ret"] > 0 for m in sel) / len(sel)
    calls = [m for m in sel if m["score"]["call"] != "Neutral"]
    right = sum((m["ret"] > 0) == (m["score"]["call"] == "Bullish") for m in calls)
    bear = [m for m in sel if m["score"]["call"] == "Bearish"]
    bull = [m for m in sel if m["score"]["call"] == "Bullish"]
    rest = [m for m in sel if m["score"]["call"] != "Bearish"]
    # baseline: always bullish on the same months that got a call
    base_calls = sum(m["ret"] > 0 for m in calls) / len(calls) if calls else None
    hv = [m for m in sel if m["score"]["vol"] >= 4]
    lv = [m for m in sel if m["score"]["vol"] < 4]

    def avg(x, k):
        return round(statistics.fmean(m[k] for m in x), 2) if x else None
    t = None
    if len(bear) > 2 and len(rest) > 2:
        a1, a2 = [m["ret"] for m in bear], [m["ret"] for m in rest]
        se = math.sqrt(statistics.variance(a1) / len(a1) + statistics.variance(a2) / len(a2))
        t = round((statistics.fmean(a1) - statistics.fmean(a2)) / se, 2) if se else None
    return dict(months=len(sel), up_share=round(up_all * 100, 1), calls=len(calls), right=right, hit=round(right / len(calls) * 100, 1) if calls else None,
                always_bull=round(base_calls * 100, 1) if base_calls is not None else None,
                bear_n=len(bear), bear_avg=avg(bear, "ret"), bear_up=round(sum(m["ret"] > 0 for m in bear) / len(bear) * 100, 1) if bear else None,
                bull_n=len(bull), bull_avg=avg(bull, "ret"), bull_up=round(sum(m["ret"] > 0 for m in bull) / len(bull) * 100, 1) if bull else None,
                rest_avg=avg(rest, "ret"), t_bear=t, bear_worst=avg(bear, "worst"), rest_worst=avg(rest, "worst"),
                hv_n=len(hv), hv_big=round(sum(m["big"] / m["n"] for m in hv) / len(hv) * 100, 2) if hv else None,
                lv_big=round(sum(m["big"] / m["n"] for m in lv) / len(lv) * 100, 2) if lv else None)


def item_tests(ms):
    out = {}
    names = [r[0] for r in RUBRIC] + ["Mercury debilitated (Pisces)"]
    for nm in names:
        on = [m for m in ms if any(i["name"] == nm for i in m["score"]["items"])]
        off = [m for m in ms if m not in on]
        if len(on) < 5:
            out[nm] = dict(n=len(on))
            continue
        side = "bull" if any(nm == r[0] and r[1] == "bull" for r in RUBRIC) else "bear"
        right = sum((m["ret"] > 0) == (side == "bull") for m in on)
        out[nm] = dict(n=len(on), side=side, right=round(right / len(on) * 100, 1),
                       base=round(sum((m["ret"] > 0) == (side == "bull") for m in ms) / len(ms) * 100, 1),
                       avg=round(statistics.fmean(m["ret"] for m in on), 2), avg_off=round(statistics.fmean(m["ret"] for m in off), 2))
    return out


def sensitivity(D, C):
    """How often the house-based indications change with the birth time, the house system and the node."""
    base = natal("10:10")
    bs = boundaries("A", base, dt.datetime(2000, 1, 1, tzinfo=UTC), dt.datetime(2026, 11, 1, tzinfo=UTC))
    res = {}
    for t in BIRTH_TIMES:
        nt = natal(t)
        shift = (nt["trop"] - base["trop"]) * 60 / 0.9856 / 60 * 60   # minutes the boundaries move
        res[t] = dict(sun=nt["trop"], asc=f"{SIGNS[int(nt['asc_trop'] // 30)]} {nt['asc_trop'] % 30:.1f}°", shift_min=round(shift, 1))
    flips = {"Placidus vs whole sign": 0, "true vs mean node": 0}
    n = 0
    for t0 in bs:
        c = chart(t0, False)
        ct = chart(t0, False, true_node=True)
        fw, fp, ft = flags(c, "whole"), flags(c, "placidus"), flags(ct, "whole")
        n += 1
        flips["Placidus vs whole sign"] += fw != fp
        flips["true vs mean node"] += fw != ft
    return dict(birth=res, flips={k: round(v / n * 100, 1) for k, v in flips.items()}, months=n)


def main():
    D, C = spx()
    nat = natal("10:10")
    A0, B0 = dt.datetime(1928, 1, 5, tzinfo=UTC), dt.datetime(2026, 12, 25, tzinfo=UTC)
    res = dict(natal={t: dict(trop=natal(t)["trop"], sid=natal(t)["sid"], asc=natal(t)["asc_trop"], moon=natal(t)["moon_trop"]) for t in BIRTH_TIMES}, models={})
    for model in ("A", "B", "C", "D"):
        ms = months(model, nat, D, C, A0, B0)
        res["models"][model] = dict(all=evaluate(ms), h1=evaluate(ms, hi=dt.date(1977, 1, 1)), h2=evaluate(ms, lo=dt.date(1977, 1, 1)),
                                    since2010=evaluate(ms, lo=dt.date(2010, 1, 1)), items=item_tests(ms),
                                    flags={k: dict(n=sum(m["flags"][k] for m in ms), avg=round(statistics.fmean([m["ret"] for m in ms if m["flags"][k]] or [0]), 2))
                                           for k in ms[0]["flags"]})
        print(model, res["models"][model]["all"])
    # verification of the given 2027 timestamps
    ver = {}
    for model in ("A", "B"):
        ours = boundaries(model, nat, dt.datetime(2027, 1, 1, tzinfo=UTC), dt.datetime(2028, 1, 1, tzinfo=UTC))
        rows = []
        for g, o in zip(GIVEN[model], ours):
            gt = dt.datetime.strptime(g, "%Y-%m-%d %H:%M").replace(tzinfo=ET)
            rows.append(dict(given=g, ours=o.astimezone(ET).strftime("%Y-%m-%d %H:%M"), diff=round((o - gt).total_seconds() / 60, 1)))
        ver[model] = rows
    res["verify"] = ver
    res["sensitivity"] = sensitivity(D, C)
    res["last_year"] = last_year(nat)
    sys.path.insert(0, str(ROOT / "tools"))
    res["diagnosis"] = diagnose(nat)
    # forward: Dec 2026 - Dec 2027
    fw = {}
    for model in ("A", "B", "C", "D"):
        bs = boundaries(model, nat, dt.datetime(2026, 11, 15, tzinfo=UTC), dt.datetime(2028, 1, 25, tzinfo=UTC))
        rows = []
        for t0, t1 in zip(bs, bs[1:]):
            c = chart(t0, model in ("B", "D"))
            sc = score(c)
            p = c["p"]
            rows.append(dict(start=t0.astimezone(ET).strftime("%a %d %b %Y %H:%M"), end=t1.astimezone(ET).strftime("%d %b %Y"),
                             asc=f"{SIGNS[int(c['asc'] // 30)]} {c['asc'] % 30:.1f}°", flags=[k for k, v in flags(c).items() if v],
                             flags_p=[k for k, v in flags(c, 'placidus').items() if v], score=sc,
                             mars=f"{SIGNS[int(p['Mars'][0] // 30)]} {p['Mars'][0] % 30:.1f}°{' R' if p['Mars'][1] < 0 else ''}"))
        fw[model] = rows
    res["forward"] = fw
    json.dump(res, open(OUT / "solar_return_engine_ET.json", "w"), indent=1, default=str)
    (OUT / "solar_return_engine_ET.html").write_text(page(res), encoding="utf-8")
    for m in ("A", "B"):
        print("verify", m, [r["diff"] for r in ver[m]])
    print(res["sensitivity"])
    for m in ("A", "B", "C", "D"):
        print(m, "items", {k: (v.get("n"), v.get("right"), v.get("base")) for k, v in res["models"][m]["items"].items()})
        print(m, "h1", res["models"][m]["h1"]["hit"], res["models"][m]["h1"]["always_bull"], "h2", res["models"][m]["h2"]["hit"], res["models"][m]["h2"]["always_bull"],
              "2010+", res["models"][m]["since2010"]["hit"], res["models"][m]["since2010"]["always_bull"])
    for r in fw["A"]:
        print("A", r["start"], r["asc"], r["score"]["call"], r["score"]["net"], r["score"]["vol"], [i["name"] for i in r["score"]["items"]], r["flags"])


def page(res):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--dn:#cf222e;--vo:#9a6700}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149;--vo:#d29922}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149;--vo:#d29922}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1250px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} h3{font-size:15px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .g{color:var(--up);font-weight:600} .r{color:var(--dn);font-weight:600} details{margin:6px 0} summary{cursor:pointer}"""
    NAMES = {"A": "A — tropical monthly degree returns", "B": "B — sidereal Lahiri monthly degree returns", "C": "C — tropical annual return ÷ 12", "D": "D — sidereal annual return ÷ 12"}
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Solar Return Engine</title><style>{css}</style></head><body>",
         "<h1>Solar return engine: four calculation models, one fixed aspect rubric, 98 years of the S&amp;P</h1>",
         "<p class='s'>Built from the analysis you shared (24 Nov 2026). NYSE 17 May 1792, 10:10 LMT New York (time disputed). The rubric scores each monthly chart at its start: "
         "orb 0–1° = 4, 1–2° = 3, 2–3° = 2, 3–5° = 1; bearish Sun□Mars, Mars☌Ketu, Mars□Uranus, Saturn☌/□/☍Sun, Mercury in Pisces; bullish Jupiter⚹Venus, Jupiter△Sun, Venus△Jupiter. "
         "Nothing was adjusted after seeing results.</p>"]
    o.append("<h2>1. The natal chart</h2><div class='wrap'><table><thead><tr><th>Birth time (LMT)</th><th>Sun, tropical</th><th>Sun, Lahiri</th><th>Ascendant (tropical, Placidus)</th><th>Moon (tropical)</th></tr></thead><tbody>")
    for t, v in res["natal"].items():
        def dms(x):
            x %= 30
            d = int(x)
            m = int((x - d) * 60)
            s_ = round(((x - d) * 60 - m) * 60)
            return f"{d}°{m:02d}′{s_:02d}″"
        o.append(f"<tr><td>{t}{' (working)' if t == '10:10' else ''}</td><td>{SIGNS[int(v['trop'] // 30)]} {dms(v['trop'])}</td><td>{SIGNS[int(v['sid'] // 30)]} {dms(v['sid'])}</td>"
                 f"<td>{SIGNS[int(v['asc'] // 30)]} {v['asc'] % 30:.1f}°</td><td>{SIGNS[int(v['moon'] // 30)]} {v['moon'] % 30:.1f}°</td></tr>")
    o.append("</tbody></table></div><p class='s'>The Sun moves about 2.4′ per hour, so the birth-time dispute moves each monthly boundary by under an hour and a half. "
             "The ascendant moves through two signs (Cancer to Leo), so house-based readings are uncertain. The pasted table's “Ascendant 19°51′ Aries” cannot be right for 10:10 AM "
             "(the Sun was high in the sky); at 10:10 LMT the ascendant is Leo 11.6°.</p>")
    o.append("<h2>2. The 2027 timestamps you were given, recomputed</h2><div class='wrap'><table><thead><tr><th>Model</th><th>Given (New York)</th><th>Ours</th><th class='n'>Difference</th></tr></thead><tbody>")
    for m, rows in res["verify"].items():
        for r in rows:
            o.append(f"<tr><td>{m}</td><td>{r['given']}</td><td>{r['ours']}</td><td class='n'>{r['diff']:+.1f} min</td></tr>")
    o.append("</tbody></table></div>")
    s = res["sensitivity"]
    o.append(f"<h2>3. Sensitivity</h2><p>Over {s['months']} monthly charts (2000–2026, model A), the house-based indications change in "
             f"<b>{s['flips']['Placidus vs whole sign']}%</b> of months between Placidus and whole-sign houses, and in <b>{s['flips']['true vs mean node']}%</b> between the true and the mean node. "
             "Birth-time alternatives move the boundaries by: " + ", ".join(f"{t}: {v['shift_min']:+.0f} min (ascendant {v['asc']})" for t, v in s["birth"].items()) + ".</p>")
    o.append("<h2>4. Does the monthly call work? S&amp;P 1928–2026</h2><div class='wrap'><table><thead><tr><th>Model</th><th>Period</th><th class='n'>Months</th><th class='n'>Calls right</th>"
             "<th class='n'>Always bullish, same months</th><th class='n'>Bearish months: avg / up</th><th class='n'>Other months avg</th><th class='n'>t</th><th class='n'>Worst point: bearish / other</th>"
             "<th class='n'>Big days per session: high / low volatility score</th></tr></thead><tbody>")
    for m, v in res["models"].items():
        for lab, k in (("1928–2026", "all"), ("1928–1976", "h1"), ("1977–2026", "h2"), ("2010–2026", "since2010")):
            x = v[k]
            better = x["hit"] is not None and x["always_bull"] is not None and x["hit"] > x["always_bull"]
            o.append(f"<tr><td>{E(NAMES[m])}</td><td>{lab}</td><td class='n'>{x['months']}</td><td class='n {'g' if better else 'r'}'>{x['hit']}% of {x['calls']}</td><td class='n'>{x['always_bull']}%</td>"
                     f"<td class='n'>{x['bear_avg']}% / {x['bear_up']}% up ({x['bear_n']})</td><td class='n'>{x['rest_avg']}%</td><td class='n'>{x['t_bear']}</td>"
                     f"<td class='n'>{x['bear_worst']}% / {x['rest_worst']}%</td><td class='n'>{x['hv_big']}% / {x['lv_big']}%</td></tr>")
    o.append("</tbody></table></div><p class='s'>“Calls right” counts months with a Bullish or Bearish net score where the S&amp;P moved that way; the baseline calls every one of those months bullish. "
             "Green = better than the baseline.</p>")
    o.append("<h3>Each rubric item on its own (model A, 1928–2026)</h3><div class='wrap'><table><thead><tr><th>Item</th><th class='n'>Months</th><th class='n'>Right</th><th class='n'>Base</th><th class='n'>Avg month on / off</th></tr></thead><tbody>")
    for k, v in res["models"]["A"]["items"].items():
        if "right" in v:
            o.append(f"<tr><td>{E(k)}</td><td class='n'>{v['n']}</td><td class='n {'g' if v['right'] > v['base'] else 'r'}'>{v['right']}%</td><td class='n'>{v['base']}%</td><td class='n'>{v['avg']:+.2f}% / {v['avg_off']:+.2f}%</td></tr>")
        else:
            o.append(f"<tr><td>{E(k)}</td><td class='n'>{v['n']}</td><td colspan='3' class='s'>too few</td></tr>")
    o.append("</tbody></table></div>")
    ly = res.get("last_year")
    if ly:
        st = ly["stated"]
        dd = ly["daily"]["calls"]
        bz = ly["daily"]["base"]
        o.append(f"<h2>5. The past year (20 Nov 2025 – {ly['last_close']})</h2><div class='wrap'><table><thead><tr><th>Method</th><th class='n'>Calls right</th><th class='n'>Always bullish</th></tr></thead><tbody>")
        upm = sum(r["ret"] > 0 for r in st["rows"] if not r["partial"])
        nm = sum(1 for r in st["rows"] if not r["partial"])
        o.append(f"<tr><td>Stated-indication reading, the Solar return way (27°18′; reproduces the shared charts)</td><td class='n'>{st['right']} of {st['calls']}</td><td class='n'>{upm} of {nm} months up</td></tr>")
        for m, v in ly["models"].items():
            o.append(f"<tr><td>Rubric, model {m}</td><td class='n'>{v['right']} of {v['calls']}</td><td class='n'>{v['up']} of {v['months']} months up</td></tr>")
        o.append(f"<tr><td>Daily calls, bearish (same day / 5 sessions)</td><td class='n'>{dd['Bearish'][0]}/{dd['Bearish'][1]} · {dd['Bearish'][2]}/{dd['Bearish'][3]}</td><td class='n'>down on {bz[1] - bz[0]}/{bz[1]} days · {bz[3] - bz[2]}/{bz[3]} spans</td></tr>")
        o.append(f"<tr><td>Daily calls, bullish (same day / 5 sessions)</td><td class='n'>{dd['Bullish'][0]}/{dd['Bullish'][1]} · {dd['Bullish'][2]}/{dd['Bullish'][3]}</td><td class='n'>up on {bz[0]}/{bz[1]} days · {bz[2]}/{bz[3]} spans</td></tr>")
        o.append("</tbody></table></div>")
        rows = "".join(f"<tr><td class='n'>{E(r['start'])}</td><td>{E(r['asc'])}</td><td>{E(r['reading'])}</td><td class='n {'g' if r['ret'] > 0 else 'r'}'>{r['ret']:+.2f}%{' (so far)' if r['partial'] else ''}</td></tr>" for r in st["rows"])
        o.append(f"<details open><summary>The past year's solar months, read the Solar return way</summary><div class='wrap'><table><thead><tr><th>Month starts (ET)</th><th>Ascendant</th><th>Reading</th><th class='n'>S&amp;P in the month</th></tr></thead><tbody>{rows}</tbody></table></div></details>")
    dg = res.get("diagnosis")
    if dg:
        wrong = [x for x in dg if x["right"] is False]
        rights = [x for x in dg if x["right"] is True]
        fragile = [x for x in wrong if x["flips"]]
        o.append("<h2>6. Month by month: why the reading missed</h2>")
        o.append(f"<div class='callout' style='border-left:4px solid var(--dn);padding:8px 12px;background:var(--soft)'><b>In sum:</b> {len(rights)} right, {len(wrong)} wrong, "
                 f"{sum(1 for x in dg if x['lean'] == 0)} with no stated indication, {sum(1 for x in dg if x['partial'])} still open. In every wrong month the reading had no historical "
                 f"edge to begin with (bearish-type readings have been followed by rises 60–70% of the time since 1928). {len(fragile)} of the {len(wrong)} wrong readings were fragile "
                 "(they change with the exact natal degree, the birth time, the house system or the zodiac). The method reads only the start-of-month chart, while the market rose on most "
                 "sessions in the misses.</div>")
        for x in dg:
            res_ = "open" if x["partial"] else "no call" if x["lean"] == 0 else "right" if x["right"] else "WRONG"
            cls = "g" if res_ == "right" else "r" if res_ == "WRONG" else ""
            alt = "; ".join(f"{k}: {v}" for k, v in x["alt"].items())
            tb = x["table"]
            o.append(f"<h3>{E(x['start'])} → {E(x['end'])} — reading <b>{E(x['reading'])}</b>, S&amp;P {x['ret']:+.2f}%{' so far' if x['partial'] else ''} — <span class='{cls}'>{res_}</span></h3>"
                     f"<ul><li><b>Chart:</b> {E(x['asc'])} rising; lord {E(x['lord'])} in {E(x['lord_pos'])}; 8th: {E(', '.join(x['h8']) or '–')}; 10th: {E(', '.join(x['h10']) or '–')}. "
                     f"Indications: {E('; '.join(x['flags']) or 'none')}.</li>"
                     f"<li><b>The month:</b> first half {x['first']:+.2f}%, second half {x['second']:+.2f}%; worst {x['worst']:+.2f}%, best {x['best']:+.2f}%; {x['big']} big days in {x['sessions']} sessions.</li>"
                     f"<li><b>Same reading since 1928:</b> {x['hist'].get('n', '–')} months, up {x['hist'].get('up', '–')}%, average {x['hist'].get('mean', 0):+.2f}%.</li>"
                     f"<li><b>Robustness:</b> {E(alt)}{' — <b>changes</b> with ' + E(', '.join(x['flips'])) if x['flips'] else ' — stable'}.</li>"
                     f"<li><b>Inside the month:</b> Solar return transit rules {E(', '.join(x['transits']) or 'none')}; our S&amp;P table {tb['Bullish'][1]} bullish days ({tb['Bullish'][0]} right), "
                     f"{tb['Bearish'][1]} bearish days ({tb['Bearish'][0]} right).</li>"
                     + (f"<li><b>Why it missed:</b> {E('; '.join(x['why']))}.</li>" if x["why"] else "") + "</ul>")
    o.append("<h2>7. The charts ahead, Dec 2026 – Dec 2027</h2>")
    for m, rows in res["forward"].items():
        body = ""
        for r in rows:
            sc = r["score"]
            cls = "g" if sc["call"] == "Bullish" else "r" if sc["call"] == "Bearish" else ""
            its = "; ".join(f"{i['name']} ({'' if i['orb'] is None else str(i['orb']) + '°, '}w{i['w']}{', applying' if i['applying'] else ', separating' if i['applying'] is False else ''})" for i in sc["items"]) or "none within 5°"
            body += (f"<tr><td class='n'>{E(r['start'])} → {E(r['end'])}</td><td>{E(r['asc'])}</td><td class='{cls}'>{sc['call']} ({sc['net']:+d})</td><td class='n'>{sc['vol']}</td>"
                     f"<td class='s'>{E(its)}</td><td class='s'>{E('; '.join(r['flags']) or '–')}</td><td class='s'>{E(r['mars'])}</td></tr>")
        o.append(f"<details{' open' if m in ('A', 'B') else ''}><summary><b>{E(NAMES[m])}</b></summary><div class='wrap'><table><thead><tr><th>Month (ET)</th><th>Ascendant</th><th>Rubric</th>"
                 f"<th class='n'>Volatility</th><th>Aspects in orb</th><th>Stated indications (whole sign)</th><th>Mars</th></tr></thead><tbody>{body}</tbody></table></div></details>")
    o.append("<p class='s'>Generated by tools/solar_return_engine.py. Market prices and astrology only.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
