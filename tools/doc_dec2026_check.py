"""The 2026 document's December table (Chapter 4, pp.292-293) checked against our computation and our calendar.

    python tools/doc_dec2026_check.py

For every printed December row:
  1. timing  - the printed IST time against our ephemeris (the astronomy layer's events; Moon-Mercury navamsa and
               stations computed here to the minute);
  2. calendar - whether the row reaches our 2026 calendar, and how (direction or "condition only");
  3. record  - its 2000-2026 S&P / Sensex record. Rows our backtests already score are quoted; rows with a market
               direction the calendar layer had not scored are tested here with the project's standard method
               (tools/backtest_market.py: day rules from that day's open over 5 sessions; windows of 3+ days to the last
               close inside; FLAT < 0.5%; base = same horizon, same Nov-Nov year):
                 Bhadra by the document's own tone rule (sec-142: karana parity x day/night opening at Mumbai,
                   Moon's loka sign; Overall Positive / Negative), Moon and Mercury in the same D9 during market hours
                   (Positive), Rahu or Ketu nakshatra on a Thursday (Positive), Apogee (Positive) and Perigee (Negative)
                   for the indices, Mercury in Mula (Negative), Vargottam Mars (Positive), Mars ahead of Jupiter in the
                   same sign (Positive).
Writes build/pdfref/doc_dec2026_check_ET.json; tools/calendar_2026.py shows it (a section and a line on each day).
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import json
import pathlib
import re
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402
from finastro import monthly2026 as MO  # noqa: E402

BM = load(ROOT / "tools" / "backtest_market.py", "bm_dec")
IST, ET, UTC = ZoneInfo("Asia/Kolkata"), ZoneInfo("America/New_York"), dt.timezone.utc
MUMBAI = (72 + 50 / 60, 18 + 58 / 60)
swe.set_sid_mode(swe.SIDM_LAHIRI)
FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAK = 360 / 27
RK_NAKS = {5, 14, 23, 0, 9, 18}            # Ardra, Swati, Shatabhisha (Rahu); Ashwini, Magha, Mula (Ketu)
SESSION = {"spx": (dt.time(9, 30), dt.time(16, 0), ET), "sensex": (dt.time(9, 15), dt.time(15, 30), IST)}
H0, H1 = dt.datetime(2000, 11, 1, tzinfo=UTC), dt.datetime(2026, 11, 21, tzinfo=UTC)


def jd(t):
    u = t.astimezone(UTC)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def lon(t, body):
    return swe.calc_ut(jd(t), body, FL)[0]


def elong(t):
    return (lon(t, swe.MOON)[0] - lon(t, swe.SUN)[0]) % 360


# ------------------------------------------------------------------ Bhadra with the document's tone rule
def sun_rise_set(day):
    j0 = swe.julday(day.year, day.month, day.day, 0) - 5.5 / 24
    r = swe.rise_trans(j0, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER, (MUMBAI[0], MUMBAI[1], 0))[1][0]
    s = swe.rise_trans(j0, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER, (MUMBAI[0], MUMBAI[1], 0))[1][0]

    def tt(x):
        y, m, d, h = swe.revjul(x)
        return (dt.datetime(y, m, d, tzinfo=UTC) + dt.timedelta(hours=h)).astimezone(IST)
    return tt(r), tt(s)


def crossing(t0, t1, target):
    """Time in (t0, t1] when the elongation crosses `target` degrees."""
    for _ in range(40):
        m = t0 + (t1 - t0) / 2
        if (elong(m) - target) % 360 < 180:
            t1 = m
        else:
            t0 = m
    return t1


def bhadras(a, b):
    out = []
    t = a
    step = dt.timedelta(hours=2)
    prev = int(elong(t) // 6) + 1
    opening = None
    while t < b:
        n = t + step
        k = int(elong(n) // 6) + 1
        if k != prev:
            ks = [(prev % 60) + 1 + i for i in range((k - prev) % 60)]
            for kk in ks:
                kk = (kk - 1) % 60 + 1
                c = crossing(t, n, (kk - 1) * 6)
                if kk in (8, 15, 22, 29, 36, 43, 50, 57):
                    opening = (c, kk)
                elif opening and kk == opening[1] % 60 + 1:
                    o, kn = opening
                    oi = o.astimezone(IST)
                    rise, sset = sun_rise_set(oi.date())
                    day_time = rise <= oi < sset
                    day_b = kn % 2 == 1
                    r1 = "Positive" if day_b != day_time else "Negative"
                    sign = SIGNS[int(lon(o, swe.MOON)[0] // 30)]
                    loka = "Swarg" if sign in ("Aries", "Taurus", "Gemini", "Scorpio") else "Patal" if sign in ("Virgo", "Libra", "Sagittarius", "Capricorn") else "Earth"
                    r2 = "Negative" if loka == "Earth" else "Positive"
                    overall = r1 if r1 == r2 else "Neutral"
                    out.append(dict(start=o, end=c, day_bhadra=day_b, day_time=day_time, r1=r1, sign=sign, loka=loka, r2=r2, overall=overall))
                    opening = None
            prev = k
        t = n
    return out


def doc_bhadra_table():
    s = (ROOT / "data" / "source_2026.html").read_text(encoding="utf-8")
    i = s.find('<section id="sec-142">')
    sec = s[i:s.find("</section>", i)]
    rows = []
    for r in re.findall(r"<tr>(.*?)</tr>", sec, flags=re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", r, flags=re.S)]
        if len(cells) == 12 and re.match(r"\d\d-\w\w\w-26", cells[0]):
            rows.append(dict(start=dt.datetime.strptime(cells[0] + " " + cells[1], "%d-%b-%y %H:%M").replace(tzinfo=IST), overall=cells[11], sign=cells[8]))
    return rows


# ------------------------------------------------------------------ hourly scan for the window rules
def scan(a, b, step=dt.timedelta(hours=1)):
    t = a
    rows = []
    while t < b:
        j = jd(t)
        p = {k: swe.calc_ut(j, v, FL)[0] for k, v in (("Moon", swe.MOON), ("Sun", swe.SUN), ("Mercury", swe.MERCURY), ("Mars", swe.MARS), ("Jupiter", swe.JUPITER))}
        rows.append((t, p))
        t += step
    return rows


def windows(sc, pred):
    out, cur = [], None
    for t, p in sc:
        on = pred(p)
        if on and cur is None:
            cur = t
        elif not on and cur is not None:
            out.append((cur, t))
            cur = None
    if cur is not None:
        out.append((cur, sc[-1][0]))
    return out


def apsides(sc):
    ev = []
    d = [(t, p["Moon"][2]) for t, p in sc]
    for i in range(1, len(d) - 1):
        if d[i][1] > d[i - 1][1] and d[i][1] >= d[i + 1][1]:
            ev.append(("Apogee", d[i][0]))
        if d[i][1] < d[i - 1][1] and d[i][1] <= d[i + 1][1]:
            ev.append(("Perigee", d[i][0]))
    return ev


# ------------------------------------------------------------------ session-day rules
def session_rule(mk, M, pred, weekday=None):
    s0, s1, tz = SESSION[mk]
    days = []
    for d in M.D:
        if not (BM.P0 <= d <= BM.P1) or (weekday is not None and d.weekday() != weekday):
            continue
        a = dt.datetime.combine(d, s0, tz)
        b = dt.datetime.combine(d, s1, tz)
        t, hit = a, False
        while t <= b:
            if pred(t):
                hit = True
                break
            t += dt.timedelta(minutes=15)
        if hit:
            days.append(d)
    return days


def same_d9(t):
    m, me = lon(t, swe.MOON)[0], lon(t, swe.MERCURY)[0]
    return int(m // (10 / 3)) % 12 == int(me // (10 / 3)) % 12


def rk_nak(t):
    return int(lon(t, swe.MOON)[0] // NAK) in RK_NAKS


# ------------------------------------------------------------------ timing of each printed row
def sky_events():
    ev = []
    for f in sorted(OUT.glob("sky_changes_2026-1*_ET.json")):
        for x in json.load(open(f))["events"]:
            ev.append((dt.datetime.fromisoformat(x["utc"]), x["kind"], x["text"]))
    return sorted(set(ev))


def first(ev, kind, text, after, before=None):
    for t, k, tx in ev:
        if k == kind and text in tx and t >= after and (before is None or t <= before):
            return t
    return None


def d9_windows(day):
    a = dt.datetime.combine(day, dt.time(9, 15), IST)
    b = dt.datetime.combine(day, dt.time(15, 30), IST)
    t, cur, out = a, None, []
    while t <= b:
        on = same_d9(t)
        if on and cur is None:
            cur = t
        if not on and cur is not None:
            out.append((cur, t))
            cur = None
        t += dt.timedelta(minutes=1)
    if cur is not None:
        out.append((cur, b))
    return out


def station(body, a, b):
    """Station by the TROPICAL (geocentric) speed, as the astronomy layer and the document time it; the sidereal speed
    includes the drift of the ayanamsa and moves a slow planet's station by about an hour."""
    def spd(t):
        return swe.calc_ut(jd(t), body, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3]
    t, prev = a, spd(a) < 0
    while t < b:
        n = t + dt.timedelta(minutes=10)
        r = spd(n) < 0
        if r != prev:
            lo, hi = t, n
            for _ in range(20):
                m = lo + (hi - lo) / 2
                if (spd(m) < 0) == prev:
                    lo = m
                else:
                    hi = m
            return hi
        t, prev = n, r
    return None


def ingress(fn, a, b, step=dt.timedelta(minutes=10)):
    """First time in a..b when fn(t) changes value."""
    t, v = a, fn(a)
    while t < b:
        n = t + step
        if fn(n) != v:
            lo, hi = t, n
            for _ in range(20):
                m = lo + (hi - lo) / 2
                if fn(m) == v:
                    lo = m
                else:
                    hi = m
            return hi
        t = n
    return None


def timing(bh):
    ev = sky_events()
    D = lambda d, h=0: dt.datetime(2026, 12, d, h, tzinfo=IST)  # noqa: E731
    out = {}
    out["Uttra Falguni Nakshtra|2026-12-02"] = (first(ev, "nakshatra change", "Moon enters Uttara Phalguni", D(1)), first(ev, "nakshatra change", "Moon enters Hasta", D(2)))
    out["Uttra Falguni Nakshtra|2026-12-29"] = (first(ev, "nakshatra change", "Moon enters Uttara Phalguni", D(28)), first(ev, "nakshatra change", "Moon enters Hasta", D(29)))
    for x in bh:
        si = x["start"].astimezone(IST)
        if si.year == 2026 and si.month == 12:
            out[f"Bhadra|{si.date()}"] = (x["start"], x["end"], x["overall"])
    out["Ekadashi on Friday|2026-12-04"] = (None, first(ev, "tithi", "Ekadashi → Dwadashi", D(4)))
    for d in (4, 15, 22, 28):
        w = d9_windows(dt.date(2026, 12, d))
        out[f"Moon Mercury in the same D9|2026-12-{d:02d}"] = (w[0][0], w[-1][1]) if w else (None, None)
    pr = (first(ev, "tithi", "Amavasya → Pratipada", D(8)), first(ev, "tithi", "Pratipada → Dwitiya", D(9)))
    out["Shukla Pratipada Vriddhi Tithi|2026-12-09"] = pr
    out["Apogee|2026-12-11"] = (first(ev, "apsis", "apogee", D(10)), None)
    out["Perigee|2026-12-24"] = (first(ev, "apsis", "perigee", D(23)), None)
    st = station(swe.SATURN, D(9), D(13))
    out["Saturn Vehda of Purva Shada|2026-10-09"] = (ingress(lambda t: int(lon(t, swe.SATURN)[0] // (360 / 108)), dt.datetime(2026, 10, 8, tzinfo=IST), dt.datetime(2026, 10, 11, tzinfo=IST)), st)
    out["Saturn Vehda of Hast|2026-12-11"] = (st, None)
    out["Shani Chandra Dwidwadash Yog along negative axis|2026-12-14"] = (first(ev, "sign change", "Moon enters Aquarius", D(14)), first(ev, "sign change", "Moon enters Pisces", D(16)))
    out["Shatbisha on Tuesday|2026-12-15"] = (first(ev, "nakshatra change", "Moon enters Shatabhisha", D(14)), None)
    out["Vyatipath Yog in Panchak|2026-12-17"] = (first(ev, "yoga", "→ Vyatipata", D(17)), first(ev, "yoga", "Vyatipata →", D(17)))
    out["Vargottam Mars|2026-12-19"] = (first(ev, "navamsa change", "Mars navamsa (D9) Cancer → Leo", D(18)), None)
    out["Mercury alone in Mool Nakshtra|2026-12-22"] = (first(ev, "nakshatra change", "Mercury enters Mula", D(21)), first(ev, "nakshatra change", "Mercury enters Purva Ashadha", D(22)))
    out["Shukla Trayodashi on Tuesday|2026-12-22"] = (None, first(ev, "tithi", "Trayodashi → Chaturdashi", D(22)))
    out["Shukla Purnima Kshay Tithi|2026-12-23"] = (first(ev, "tithi", "Chaturdashi → Purnima", D(22)), first(ev, "tithi", "Purnima → Pratipada", D(23)))
    out["Jupiter in Magha Nakshtra|2026-10-31"] = (ingress(lambda t: int(lon(t, swe.JUPITER)[0] // NAK), dt.datetime(2026, 10, 30, tzinfo=IST), dt.datetime(2026, 11, 2, tzinfo=IST)), None)
    out["Mars ahead of Jupiter in the same sign|2026-11-16"] = (ingress(lambda t: lon(t, swe.MARS)[0] > lon(t, swe.JUPITER)[0], dt.datetime(2026, 11, 14, tzinfo=IST), dt.datetime(2026, 11, 18, tzinfo=IST)), None)
    for d in (10, 24):
        a, b = D(d, 9) + dt.timedelta(minutes=15), D(d, 15) + dt.timedelta(minutes=30)
        out[f"Rahu/Ketu Nakshtra on Thursday|2026-12-{d}"] = (a if rk_nak(a) else None, b if rk_nak(b) else None)
    rs = {d: sun_rise_set(dt.date(2026, 12, d))[0] for d in (9, 10, 23, 24)}
    out["_sunrise"] = {str(d): v.strftime("%H:%M") for d, v in rs.items()}
    return out


# ------------------------------------------------------------------ scoring
def score(events, tone, mk):
    M = BM.Market(mk)
    rows = []
    for e in events:
        ev = dict(tone=tone, **e)
        s = M.score(ev)
        if s:
            rows.append((ev, s))
    return dict(all=BM.aggregate(rows, M), h1=BM.aggregate(rows, M, BM.P0, BM.SPLIT), h2=BM.aggregate(rows, M, BM.SPLIT, BM.P1), n=len(rows))


def rec_text(r):
    a = r["all"]
    dec = a["worked"] + a["failed"]
    if not dec:
        return "no decided cases"
    return f"{a['worked']}/{dec} ({a['hit_rate']}% vs {a['base_rate']}%), p {a['p_value']}"


def holds(r):
    a, h1, h2 = r["all"], r["h1"], r["h2"]
    return bool(a["p_value"] is not None and a["p_value"] < 0.05 and h1["hit_rate"] and h2["hit_rate"] and h1["hit_rate"] > h1["base_rate"] and h2["hit_rate"] > h2["base_rate"])


def main():
    print("scanning 2000-2026 ...")
    sc = scan(H0, H1)
    tests = {}

    def wtest(name, tone, wins):
        evs = [dict(start=a.isoformat(), end=b.isoformat(), day=None) for a, b in wins]
        tests[name] = dict(tone=tone, n=len(wins), spx=score(evs, tone, "spx"), sensex=score(evs, tone, "sensex"))
    wtest("Mercury in Mula", "Bearish", windows(sc, lambda p: 240 <= p["Mercury"][0] % 360 < 240 + NAK))
    wtest("Vargottam Mars", "Bullish", windows(sc, lambda p: int(p["Mars"][0] // 30) == int(p["Mars"][0] // (10 / 3)) % 12))
    wtest("Mars ahead of Jupiter in the same sign", "Bullish",
          windows(sc, lambda p: int(p["Mars"][0] // 30) == int(p["Jupiter"][0] // 30) and p["Mars"][0] % 30 > p["Jupiter"][0] % 30))
    aps = apsides(sc)
    for kind, tone in (("Apogee", "Bullish"), ("Perigee", "Bearish")):
        evs = [dict(start=t.isoformat(), end=None, day=None) for k, t in aps if k == kind]
        tests[kind] = dict(tone=tone, n=len(evs), spx=score(evs, tone, "spx"), sensex=score(evs, tone, "sensex"))
    print("Bhadra ...")
    bh = bhadras(H0, dt.datetime(2027, 1, 2, tzinfo=UTC))
    for tone_doc, tone in (("Positive", "Bullish"), ("Negative", "Bearish")):
        evs = [dict(start=x["start"].isoformat(), end=x["end"].isoformat(), day=None) for x in bh if x["overall"] == tone_doc and x["start"] < H1]
        tests[f"Bhadra, {tone_doc.lower()} by the document's rule"] = dict(tone=tone, n=len(evs), spx=score(evs, tone, "spx"), sensex=score(evs, tone, "sensex"))
    print("session rules ...")
    for name, pred, wd in (("Moon and Mercury in the same D9 (market hours)", same_d9, None), ("Rahu or Ketu nakshatra on Thursday (market hours)", rk_nak, 3)):
        out = dict(tone="Bullish")
        for mk in ("spx", "sensex"):
            M = BM.Market(mk)
            ds = session_rule(mk, M, pred, wd)
            out[mk] = score([dict(start=None, end=None, day=str(d)) for d in ds], "Bullish", mk)
            out["n_" + mk] = len(ds)
        out["n"] = out["n_spx"]
        tests[name] = out
    # validation of the Bhadra rule against the document's own 2026 table
    doc_bh = doc_bhadra_table()
    ours = {x["start"].astimezone(IST).replace(second=0, microsecond=0): x for x in bh if x["start"].year == 2026}
    agree = total = 0
    mism = []
    for r in doc_bh:
        near = min(ours.values(), key=lambda x: abs((x["start"] - r["start"]).total_seconds()))
        if abs((near["start"] - r["start"]).total_seconds()) < 3 * 3600:
            total += 1
            agree += near["overall"] == r["overall"]
            if near["overall"] != r["overall"]:
                mism.append(f"{r['start']:%d %b %H:%M}: document {r['overall']}, ours {near['overall']} ({near['sign']})")
    # December rows
    dec = [r for r in MO.blocks()[11].rows]
    tm = timing(bh)

    def fm(t):
        return None if t is None else dict(ist=t.astimezone(IST).strftime("%d %b %H:%M"), et=t.astimezone(ET).strftime("%d %b %H:%M"))
    timings = {k: ([fm(x) if isinstance(x, dt.datetime) else x for x in v] if k != "_sunrise" else v) for k, v in tm.items()}
    res = dict(tests=tests, timings=timings, bhadra_validation=dict(rows=len(doc_bh), matched=total, agree=agree, mismatches=mism),
               bhadra_dec=[dict(start=x["start"].astimezone(IST).strftime("%d %b %H:%M"), end=x["end"].astimezone(IST).strftime("%d %b %H:%M"),
                                kind="Day" if x["day_bhadra"] else "Night", opens="day" if x["day_time"] else "night", sign=x["sign"], loka=x["loka"], overall=x["overall"])
                           for x in bh if x["start"].astimezone(IST).date().month == 12 and x["start"].year == 2026],
               printed=[dict(event=r.event, start=str(r.start_date), start_time=r.raw_start_time, end=r.raw_end_date or (str(r.end_date) if r.end_date else ""),
                             end_time=r.raw_end_time, inference=r.inference, tone=r.tone) for r in dec])
    json.dump(res, open(OUT / "doc_dec2026_check_ET.json", "w"), indent=1, default=str)
    for k, v in tests.items():
        print(f"{k:55s} {v['tone']:7s} n {v['n']:5d} | S&P {rec_text(v['spx'])} {'HOLDS' if holds(v['spx']) else ''} | Sensex {rec_text(v['sensex'])} {'HOLDS' if holds(v['sensex']) else ''}")
    print("Bhadra rule vs document 2026 table:", agree, "of", total, "agree;", mism[:5])
    print(res["bhadra_dec"])


if __name__ == "__main__":
    main()
