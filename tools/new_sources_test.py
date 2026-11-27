"""Backtest of the rules found in the three new sources (Reference_materials/extracted/NEW_SOURCES_REVIEW_2026-11.md).

    python tools/new_sources_test.py

Steps, in the order the user approved (27 Nov 2026):
  1. B12  Brihat Samhita 42.6 retested with its portent condition (eclipse while the Sun is in sidereal Leo).
  2. B1   Moon passing north / south of Mercury, Jupiter, Venus (BS 18.3-6).
     B2   Mercury's reappearance after conjunction = abnormal price swings (BS 7.1), scored as volatility.
  3. B3/B4/B6  Mercury, Mars, Saturn in the stated nakshatras (BS 7.6, 7.9, 6.13, 6.11, 10.6-17).
     B8   Lord of the day, month and year (BS 19).
  4. T8/T9  Tajika monthly-chart rules on the NYSE sidereal monthly returns (Hayanaratna 8.4-8.6), S&P 1928-2026.
  5. N1-N5, T2, T3, T5-T7  Annual rules: Aries-ingress and lunation charts (Tajika Nilakanthi, Prakirna 36-43;
     Hayanaratna 1.7) and the NYSE annual return (Hayanaratna 1.7, 4, 5, 6).

Method: PROJECT_KNOWLEDGE section 6 (tools/backtest_market.py) for daily and monthly rules: entry = last close
before the event, windows of 3+ days to the last close inside (clipped to the Nov-Nov year), instants on the
5-session move, |move| < 0.5% FLAT, base = same-length moves in the same Nov-Nov year, one-sided binomial p,
Benjamini-Hochberg q per market. Annual rules have one case a year, so they are compared with the other years
(up-rate and mean) instead of a same-year base. Sidereal Lahiri, mean node, whole-sign houses; Vedic (Parashari)
drishti for the Brihat Samhita / Nilakanthi rules, Tajika aspects (by sign) for the Tajika chart rules.
Writes build/pdfref/new_sources_test_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import collections
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
sys.path.insert(0, str(ROOT / "tools"))
import backtest_market as BM  # noqa: E402

OUT = ROOT / "build" / "pdfref"
BT = OUT / "backtest"
UTC = dt.timezone.utc
ET = ZoneInfo("America/New_York")
IST = ZoneInfo("Asia/Kolkata")
NYC = (40.7069, -74.0113)
MUM = (18.9300, 72.8330)
swe.set_sid_mode(swe.SIDM_LAHIRI)

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
NEECHA = {k: (v + 6) % 12 for k, v in EXALT.items()}
NAKS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
        "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
BODY = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN}
SEVEN = list(BODY)
COMBUST = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
ORB = {"Sun": 15, "Moon": 12, "Mars": 8, "Mercury": 7, "Jupiter": 9, "Venus": 7, "Saturn": 9}      # Tajika orbs of light (Hayanaratna 3.1)
DRISHTI = {"Mars": (4, 7, 8), "Jupiter": (5, 7, 9), "Saturn": (3, 7, 10)}
WD_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]                       # Python weekday 0 = Monday
GOOD_LORD = {"Moon", "Mercury", "Jupiter", "Venus"}                                                # BS 19: prosperity under these lords
FL = swe.FLG_SWIEPH | swe.FLG_SPEED


# ------------------------------------------------------------------ ephemeris
def jd(t):
    u = t.astimezone(UTC)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def from_jd(x):
    y, m, d, h = swe.revjul(x)
    return dt.datetime(y, m, d, tzinfo=UTC) + dt.timedelta(hours=h)


def pos(x, b, sid=True):
    r = swe.calc_ut(x, BODY[b] if b in BODY else b, FL | (swe.FLG_SIDEREAL if sid else 0))[0]
    return r[0] % 360, r[1], r[3]


def node(x):
    return swe.calc_ut(x, swe.MEAN_NODE, FL | swe.FLG_SIDEREAL)[0][0] % 360


def sep(a, b):
    return abs((a - b + 180) % 360 - 180)


def chart(t, place):
    x = jd(t)
    p = {b: pos(x, b) for b in SEVEN}
    r = node(x)
    p["Rahu"], p["Ketu"] = (r, 0, -0.05), ((r + 180) % 360, 0, -0.05)
    ay = swe.get_ayanamsa_ut(x)
    asc = (swe.houses(x, place[0], place[1], b"P")[1][0] - ay) % 360
    return dict(t=t, p=p, asc=asc, a=int(asc // 30))


def sgn(c, b):
    return int(c["p"][b][0] // 30)


def house(c, b):
    return (sgn(c, b) - c["a"]) % 12 + 1


def waxing(c):
    return (c["p"]["Moon"][0] - c["p"]["Sun"][0]) % 360 < 180


def benefics(c):
    return ["Jupiter", "Venus", "Mercury"] + (["Moon"] if waxing(c) else [])


def malefics(c, nodes=True):
    return ["Sun", "Mars", "Saturn"] + (["Rahu", "Ketu"] if nodes else []) + ([] if waxing(c) else ["Moon"])


def vedic_aspects_sign(c, b, s):
    """b joins or aspects sign s (whole-sign Parashari drishti; nodes by conjunction only)."""
    d = (s - sgn(c, b)) % 12 + 1
    if d == 1:
        return True
    if b in ("Rahu", "Ketu"):
        return False
    return d in DRISHTI.get(b, (7,))


def tajika_aspects_sign(c, b, s):
    """Tajika aspects are by sign: 1 (conjunction), 3, 4, 5, 7, 9, 10, 11 (Hayanaratna 2.1)."""
    return ((s - sgn(c, b)) % 12 + 1) in (1, 3, 4, 5, 7, 9, 10, 11)


def influence(c, s, rel=vedic_aspects_sign, nodes=True, extra_good=()):
    good = [b for b in set(benefics(c)) | set(extra_good) if rel(c, b, s)]
    bad = [b for b in malefics(c, nodes) if rel(c, b, s) and b not in extra_good]
    return good, bad


def combust(c, b):
    if b in ("Sun", "Rahu", "Ketu"):
        return False
    lim = COMBUST[b] - (2 if b in ("Mercury", "Venus") and c["p"][b][2] < 0 else 0)
    return sep(c["p"][b][0], c["p"]["Sun"][0]) < lim


def dignified(c, b):
    s = sgn(c, b)
    return LORD[s] == b or EXALT.get(b) == s


def weak(c, b):
    return NEECHA.get(b) == sgn(c, b) or combust(c, b)


def applying(c, a, b):
    """Tajika itthasala: an applying aspect (0/60/90/120/180) within the mean of the two orbs."""
    if a not in ORB or b not in ORB:
        return False
    pa, pb = c["p"][a], c["p"][b]
    lim = (ORB[a] + ORB[b]) / 2
    for ang in (0, 60, 90, 120, 180):
        now = abs(sep(pa[0], pb[0]) - ang)
        if now <= lim:
            nxt = abs(sep(pa[0] + pa[2] * 0.05, pb[0] + pb[2] * 0.05) - ang)
            if nxt < now:
                return True
    return False


def solve(f, x0, x1, it=50):
    """Root of a continuous f between x0 and x1 (sign change)."""
    f0 = f(x0)
    for _ in range(it):
        m = (x0 + x1) / 2
        fm = f(m)
        if (fm > 0) == (f0 > 0):
            x0, f0 = m, fm
        else:
            x1 = m
    return (x0 + x1) / 2


def wrap(v):
    return (v + 180) % 360 - 180


def spans(fn, a, b, step=0.25):
    """[(start_dt, end_dt, value)] of a categorical fn(jd) between datetimes a and b."""
    x, end = jd(a), jd(b)
    cur, st, out = fn(x), x, []
    while x < end:
        y = min(x + step, end)
        v = fn(y)
        if v != cur:
            lo, hi = x, y
            for _ in range(40):
                m = (lo + hi) / 2
                if fn(m) == cur:
                    lo = m
                else:
                    hi = m
            out.append((from_jd(st), from_jd(hi), cur))
            st, cur = hi, v
        x = y
    out.append((from_jd(st), from_jd(end), cur))
    return out


def lunations(a, b, which=0.0):
    """New (0) or full (180) moons between a and b."""
    out, x, end = [], jd(a), jd(b)
    f = lambda y: wrap(pos(y, "Moon", False)[0] - pos(y, "Sun", False)[0] - which)
    while x < end:
        y = x + 0.5
        if f(x) < 0 <= f(y) and abs(f(x)) < 30:
            out.append(from_jd(solve(f, x, y)))
        x = y
    return out


def sun_at(target, a, b):
    """Instants when the sidereal Sun reaches `target` longitude."""
    out, x, end = [], jd(a), jd(b)
    while x < end:
        for _ in range(60):
            d = wrap(pos(x, "Sun")[0] - target)
            if abs(d) < 1e-7:
                break
            x -= d / 0.9856
        out.append(x)
        x += 365.0
    return [from_jd(v) for v in sorted(set(round(v, 6) for v in out)) if jd(a) <= v < end]


def hindu_weekday(t, tz):
    """Weekday lord of the Hindu day (sunrise to sunrise, sunrise taken as 06:00 local)."""
    x = t.astimezone(tz)
    d = x.date() - (dt.timedelta(days=1) if x.time() < dt.time(6, 0) else dt.timedelta(0))
    return WD_LORD[d.weekday()]


# ------------------------------------------------------------------ markets
class Mkt(BM.Market):
    def __init__(self, key, name, file, tz, close, p0=BM.P0, p1=BM.P1):
        BM.MARKETS[key] = dict(name=name, sym="", file=file, tz=tz, close=close)
        super().__init__(key)
        self.p0, self.p1 = p0, p1

    def score(self, e):
        if e.get("day"):
            day = dt.date.fromisoformat(e["day"])
        else:
            day = self.session_day(dt.datetime.fromisoformat(e["start"]))
        a = bisect.bisect_left(self.D, day) - 1
        if a < 1 or self.D[a] < self.p0 - dt.timedelta(days=7) or day > self.p1:
            return None
        y = BM.nov_year(self.D[a + 1] if a + 1 < len(self.D) else self.D[a])
        b = None
        if e.get("end") and not e.get("day"):
            s, en = dt.datetime.fromisoformat(e["start"]), dt.datetime.fromisoformat(e["end"])
            if (en - s).days >= 3:
                b = bisect.bisect_left(self.D, self.session_day(en)) - 1
                if not e.get("noclip"):
                    b = min(b, self.yend.get(y, len(self.D) - 1))
                if b - a < 2:
                    b = None
        if b is None:
            b = a + e.get("h", BM.H)
        if b >= len(self.D) or self.D[b] > self.p1 + dt.timedelta(days=10):
            return None
        return dict(entry=self.D[a], n=b - a, ret=(self.C[b] / self.C[a] - 1) * 100, year=y)


def markets():
    return {
        "spx": Mkt("spx", "S&P 500", "spx_GSPC_daily_2000.csv", ET, dt.time(16, 0)),
        "sensex": Mkt("sensex", "BSE Sensex", "sensex_BSESN_daily_2000.csv", IST, dt.time(15, 30)),
        "gold": Mkt("gold", "Gold (COMEX)", "gold_GC_F_daily_2000.csv", ET, dt.time(13, 30)),
        "silver": Mkt("silver", "Silver (COMEX)", "silver_SI_F_daily_2000.csv", ET, dt.time(13, 25)),
    }


def ev(start, tone, end=None, **kw):
    e = dict(start=start.isoformat(), end=end.isoformat() if end else None, tone=tone, day=None)
    e.update(kw)
    return e


def run(events, mk, lo=None, hi=None):
    rows = [(e, s) for e in events if (s := mk.score(e))]
    return BM.aggregate(rows, mk, lo or mk.p0, hi or mk.p1), rows


def halves(rows, mk):
    return [BM.aggregate(rows, mk, mk.p0, BM.SPLIT)["hit_rate"], BM.aggregate(rows, mk, BM.SPLIT, mk.p1)["hit_rate"]]


def test(name, src, events, MK, mkts=("spx", "sensex", "gold", "silver")):
    out = dict(name=name, src=src, by={})
    for k in mkts:
        mk = MK[k]
        rec, rows = run(events, mk)
        rec["halves"] = halves(rows, mk)
        out["by"][k] = rec
    return out


def vol_test(name, src, times, MK, mkts=("spx", "sensex", "gold", "silver")):
    """Share of events whose 5-session |move| beats the median |5-session move| of that Nov-Nov year."""
    out = dict(name=name, src=src, by={}, vol=True)
    for k in mkts:
        mk = MK[k]
        med = {}
        big = tot = 0
        ratio = []
        for t in times:
            s = mk.score(dict(start=t.isoformat(), end=None, tone="Bullish", day=None))
            if not s or not (mk.p0 <= s["entry"] < mk.p1):
                continue
            y = s["year"]
            if y not in med:
                ii = [i for i in range(1, len(mk.D) - 5) if BM.nov_year(mk.D[i]) == y]
                med[y] = statistics.median(abs(mk.C[i + 5] / mk.C[i] - 1) * 100 for i in ii)
            tot += 1
            big += abs(s["ret"]) > med[y]
            ratio.append(abs(s["ret"]) / med[y] if med[y] else 1)
        out["by"][k] = dict(n=tot, big=big, share=round(big / tot * 100) if tot else None,
                            p_value=round(BM.binom_p(big, tot, 0.5), 4) if tot else None,
                            mean_ratio=round(statistics.fmean(ratio), 2) if ratio else None)
    return out


# ------------------------------------------------------------------ step 1: B12
def step1():
    """BS 42.6 with its portent: an eclipse while the Sun is in sidereal Leo; buy then, sell in the 5th solar month."""
    gm = {r["Date"]: float(r["Price"]) for r in csv.DictReader(open(BT / "gold_monthly_1833.csv"))}
    px = {}
    for m in ("gold", "silver"):
        rows = list(csv.DictReader(open(BT / f"{m}_SI_F_daily_2000.csv" if m == "silver" else BT / "gold_GC_F_daily_2000.csv")))
        px[m] = ([dt.date.fromisoformat(r["date"]) for r in rows], [float(r["close"]) for r in rows])

    def close_before(m, t):
        D, C = px[m]
        i = bisect.bisect_left(D, t.astimezone(ET).date()) - 1
        return (D[i], C[i]) if 0 <= i < len(D) and D[-1] >= t.astimezone(ET).date() else None

    ecl = []
    for fn, kind in ((swe.lun_eclipse_when, "lunar"), (swe.sol_eclipse_when_glob, "solar")):
        x = jd(dt.datetime(1971, 1, 1, tzinfo=UTC))
        while x < jd(dt.datetime(2026, 11, 1, tzinfo=UTC)):
            r = fn(x)
            m = r[1][0]
            ecl.append((from_jd(m), kind))
            x = m + 20
    years = []
    for y in range(1972, 2026):
        leo = sun_at(120.0, dt.datetime(y, 7, 1, tzinfo=UTC), dt.datetime(y, 10, 1, tzinfo=UTC))[0]
        vir = sun_at(150.0, leo, leo + dt.timedelta(days=40))[0]
        sag = sun_at(240.0, leo, leo + dt.timedelta(days=200))[0]
        cap = sun_at(270.0, leo, leo + dt.timedelta(days=230))[0]
        e = [(t, k) for t, k in ecl if leo <= t < vir]
        rec = dict(year=y, leo=leo.date().isoformat(), sag=sag.date().isoformat(), cap=cap.date().isoformat(),
                   eclipse=[f"{t.date().isoformat()} {k}" for t, k in e])
        buy_t = e[0][0] if e else leo
        for m in ("gold", "silver"):
            a, s5, s6 = close_before(m, buy_t), close_before(m, sag), close_before(m, cap)
            if a and s5 and s6:
                rec[m] = dict(buy=a[0].isoformat(), r5=round((s5[1] / a[1] - 1) * 100, 2), r6=round((s6[1] / a[1] - 1) * 100, 2))
            elif m == "gold" and y < 2000:
                bm = f"{buy_t.year}-{buy_t.month:02d}"
                s5m, s6m = f"{sag.year}-{sag.month:02d}", f"{cap.year}-{cap.month:02d}"
                if bm in gm and s5m in gm and s6m in gm:
                    rec[m] = dict(buy=bm + " (monthly)", r5=round((gm[s5m] / gm[bm] - 1) * 100, 2), r6=round((gm[s6m] / gm[bm] - 1) * 100, 2))
        years.append(rec)

    def summary(m, lo):
        a = [r for r in years if m in r and r["year"] >= lo]
        out = {}
        for lab, sel in (("eclipse years", [r for r in a if r["eclipse"]]), ("other years", [r for r in a if not r["eclipse"]]), ("all years", a)):
            r5 = [r[m]["r5"] for r in sel]
            r6 = [r[m]["r6"] for r in sel]
            out[lab] = dict(n=len(sel), up5=sum(v > 0 for v in r5), mean5=round(statistics.fmean(r5), 2) if r5 else None,
                            up6=sum(v > 0 for v in r6), mean6=round(statistics.fmean(r6), 2) if r6 else None)
        e, o = out["eclipse years"], out["other years"]
        out["p_up5"] = round(BM.binom_p(e["up5"], e["n"], o["up5"] / o["n"]), 3) if e["n"] and o["n"] else None
        return out
    return dict(years=years, gold_1972=summary("gold", 1972), gold_2000=summary("gold", 2000), silver_2000=summary("silver", 2000),
                y2026=dict(eclipse="2026-08-28 lunar (Sun 10.7 deg sidereal Leo)", sell_from="2026-12-16", sell_to="2027-01-14"))


# ------------------------------------------------------------------ step 2: B1, B2
def moon_passes(a, b):
    out = []
    for pl in ("Mercury", "Jupiter", "Venus"):
        f = lambda y, pl=pl: wrap(pos(y, "Moon", False)[0] - pos(y, pl, False)[0])
        x, end = jd(a), jd(b)
        while x < end:
            y = x + 0.25
            if f(x) < 0 <= f(y) and abs(f(x)) < 20:
                c = solve(f, x, y)
                north = pos(c, "Moon", False)[1] > pos(c, pl, False)[1]
                out.append((pl, from_jd(c), north))
            x = y
    return out


def mercury_reappear(a, b):
    def g(y):
        el = sep(pos(y, "Mercury", False)[0], pos(y, "Sun", False)[0])
        return el - (12 if pos(y, "Mercury", False)[2] < 0 else 14)
    out, x, end = [], jd(a), jd(b)
    while x < end:
        y = x + 0.5
        if g(x) < 0 <= g(y):
            c = solve(g, x, y)
            out.append((from_jd(c), "retrograde (morning)" if pos(c, "Mercury", False)[2] < 0 else "direct (evening)"))
        x = y
    return out


# ------------------------------------------------------------------ step 3: nakshatra and lord rules
def nak_windows(planet, sets, a, b):
    """sets: {label: (tone, {nakshatra names})} -> events for each contiguous stay."""
    idx = {lab: {NAKS.index(n) for n in names} for lab, (tone, names) in sets.items()}
    def fn(y):
        k = int(pos(y, planet)[0] // (360 / 27))
        for lab, s in idx.items():
            if k in s:
                return lab
        return None
    out = collections.defaultdict(list)
    for s, e, v in spans(fn, a, b, 0.5 if planet != "Saturn" else 2):
        if v:
            out[v].append(ev(s, sets[v][0], e))
    return out


def mars_south_rohini(a, b):
    out, x, end = [], jd(a), jd(b)
    # Aldebaran (Rohini's junction star): J2000 ecliptic longitude 69.789 deg, latitude -5.467 deg; precession 50.29"/yr
    star = lambda y: (((69.789 + (y - 2451545.0) / 365.25 * 50.29 / 3600) - swe.get_ayanamsa_ut(y)) % 360, -5.467)
    f = lambda y: wrap(pos(y, "Mars")[0] - star(y)[0])
    while x < end:
        y = x + 1
        if (f(x) < 0) != (f(y) < 0) and abs(f(x)) < 20:
            c = solve(f, x, y)
            out.append((from_jd(c), pos(c, "Mars")[1], star(c)[1]))
        x = y
    return [(t, ml, sl) for t, ml, sl in out]


def lord_events(MK):
    res = {}
    # lord of the day: each session's weekday (exchange date); day-rule, 1 session and 5 sessions
    for k in ("spx", "sensex", "gold", "silver"):
        mk = MK[k]
        evs1, evs5 = [], []
        for d in mk.D:
            if not (mk.p0 <= d < mk.p1):
                continue
            lord = WD_LORD[d.weekday()]
            tone = "Bullish" if lord in GOOD_LORD else "Bearish"
            evs1.append(dict(day=d.isoformat(), tone=tone, h=1, start=None, end=None, lord=lord))
            evs5.append(dict(day=d.isoformat(), tone=tone, start=None, end=None, lord=lord))
        res[k] = dict(day1=evs1, day5=evs5)
    return res


def lord_month_events(a, b, tz):
    nm = lunations(a, b)
    out = []
    for s, e in zip(nm, nm[1:]):
        lord = hindu_weekday(s, tz)
        out.append(ev(s, "Bullish" if lord in GOOD_LORD else "Bearish", e, lord=lord))
    return out


def chaitra_starts(a, b):
    """New moons with the Sun in sidereal Pisces (start of amanta Chaitra)."""
    return [t for t in lunations(a, b) if int(pos(jd(t), "Sun")[0] // 30) == 11]


# ------------------------------------------------------------------ NYSE charts (Tajika)
def nyse_natal():
    ut = dt.datetime(1792, 5, 17, 10, 10, tzinfo=UTC) + dt.timedelta(hours=74.0 / 15)
    c = chart(ut, NYC)
    return c


def monthly_returns(nat, a, b):
    tgt = nat["p"]["Sun"][0] % 30
    out, x, end = [], jd(a), jd(b)
    while x < end:
        for _ in range(60):
            d = ((pos(x, "Sun")[0] % 30) - tgt + 15) % 30 - 15
            if abs(d) < 1e-7:
                break
            x -= d / 0.9856
        out.append(x)
        x += 30.4
    return [from_jd(v) for v in sorted(set(round(v, 6) for v in out)) if jd(a) <= v < end]


def annual_returns(nat, a, b):
    return sun_at(nat["p"]["Sun"][0], a, b)


def navamsa_sign(lon):
    return int((lon % 360) // (10 / 3)) % 12


def friendly_config(c, A, B):
    """Configuration of friendship by sign distance (Romakatajika, Hayanaratna 2.4): 3/5/9/11 friend,
    1 (conjunction) good, 4/7/10 enemy, 2/6/8/12 none."""
    if A == B:
        return "friend"
    d = (sgn(c, B) - sgn(c, A)) % 12 + 1
    return "friend" if d in (1, 3, 5, 9, 11) else "enemy" if d in (4, 7, 10) else "none"


def navamsa_rule(c, house_no):
    asc_lord = LORD[c["a"]]
    A = LORD[navamsa_sign(c["p"][asc_lord][0])]
    B = LORD[navamsa_sign(c["asc"] + 30 * (house_no - 1))]
    cfg = friendly_config(c, A, B)
    fallen = weak(c, A) or weak(c, B)
    if cfg == "enemy" or (fallen and cfg != "friend"):
        return "Bearish", f"{A}/{B} {cfg}{', fallen or combust' if fallen else ''}"
    if cfg == "friend" and not fallen:
        return "Bullish", f"{A}/{B} friendly"
    return None, f"{A}/{B} {cfg}"


def sahams(c):
    p = {b: v[0] for b, v in c["p"].items()}
    asc = c["asc"]
    day = house(c, "Sun") >= 7

    def mk(minu, subt):
        v = (minu - subt + asc) % 360
        if not ((asc - subt) % 360 <= (minu - subt) % 360):
            v = (v + 30) % 360
        return v
    lord2 = LORD[(c["a"] + 1) % 12]
    return {"Fortune": mk(p["Moon"], p["Sun"]) if day else mk(p["Sun"], p["Moon"]),
            "Wealth": mk(asc + 30, p[lord2]),
            "Trade": mk(p["Moon"], p["Mercury"]),
            "Business": mk(p["Mars"], p["Mercury"])}


def saham_tone(c, lon):
    s = int(lon // 30)
    ruler = LORD[s]
    good, bad = influence(c, s, tajika_aspects_sign, nodes=False, extra_good=(ruler,))
    net = len(good) - len(bad)
    return ("Bullish" if net > 0 else "Bearish" if net < 0 else None), f"{SIGNS[s]} +{len(good)}/-{len(bad)}"


def tajika_monthly(MK1928):
    nat = nyse_natal()
    a, b = dt.datetime(1928, 11, 1, tzinfo=UTC), dt.datetime(2026, 11, 25, tzinfo=UTC)
    ar = annual_returns(nat, a - dt.timedelta(days=400), b)
    mr = monthly_returns(nat, a, b)
    rules = collections.defaultdict(list)
    for s, e in zip(mr, mr[1:]):
        c = chart(s, NYC)
        yr = [t for t in ar if t <= s + dt.timedelta(hours=1)][-1]
        ac = chart(yr, NYC)
        years = yr.year - 1792
        muntha = (nat["a"] + years) % 12
        tone, why = navamsa_rule(c, 2)
        if tone:
            rules["T8a navamsha: ascendant lord's navamsha lord with the 2nd house's (riches / loss of wealth)"].append(ev(s, tone, e, why=why, noclip=True))
        tone, why = navamsa_rule(c, 11)
        if tone:
            rules["T8b navamsha: ascendant lord's navamsha lord with the 11th house's (gain through business)"].append(ev(s, tone, e, why=why, noclip=True))
        # T8c: rulers of the month's ascendant, the year's ascendant and the muntha in 6/8/12 with malefics -> bad; strong in 1/4/5/7/9/10/11 -> good
        lords = {LORD[c["a"]], LORD[ac["a"]], LORD[muntha]}
        bad = [L for L in lords if house(c, L) in (6, 8, 12) and any(tajika_aspects_sign(c, m, sgn(c, L)) and m != L for m in ("Sun", "Mars", "Saturn"))]
        good = all(house(c, L) in (1, 4, 5, 7, 9, 10, 11) and not weak(c, L) for L in (LORD[c["a"]], LORD[ac["a"]]))
        if bad:
            rules["T8c rulers of the ascendant (month, year) or muntha in the 6th/8th/12th with malefics: bad month"].append(ev(s, "Bearish", e, why=",".join(bad), noclip=True))
        elif good:
            rules["T8c rulers of the month and year ascendants strong in an angle, trine or the 11th: good month"].append(ev(s, "Bullish", e, noclip=True))
        # T9: Sun and Moon in the houses of the monthly chart
        hs = house(c, "Sun")
        ss = sgn(c, "Sun")
        if hs == 2:
            ok = LORD[ss] in ("Sun", "Moon", "Mars", "Jupiter") or ss == 0
            rules["T9 Sun in the 2nd: own/exaltation/friend's sign = wealth, elsewhere = loss"].append(ev(s, "Bullish" if ok else "Bearish", e, noclip=True))
        if hs == 11:
            rules["T9 Sun in the 11th: gain"].append(ev(s, "Bullish", e, noclip=True))
        if hs == 12:
            rules["T9 Sun in the 12th: loss and punishment from the king"].append(ev(s, "Bearish", e, noclip=True))
        if house(c, "Moon") == 2 and influence(c, sgn(c, "Moon"), tajika_aspects_sign, nodes=False)[0]:
            rules["T9 Moon in the 2nd aspected by benefics: property"].append(ev(s, "Bullish", e, noclip=True))
        for nm, lon in sahams(c).items():
            tone, why = saham_tone(c, lon)
            if tone and nm in ("Wealth", "Trade", "Business"):
                rules[f"T7 (monthly) {nm} saham joined/aspected by benefics and its ruler vs malefics"].append(ev(s, tone, e, why=why, noclip=True))
    mk = MK1928
    res = []
    for name, evs in rules.items():
        rec, rows = run(evs, mk)
        rec["halves"] = [BM.aggregate(rows, mk, mk.p0, dt.date(1977, 11, 20))["hit_rate"], BM.aggregate(rows, mk, dt.date(1977, 11, 20), mk.p1)["hit_rate"]]
        rec["bull"] = sum(e["tone"] == "Bullish" for e in evs)
        rec["bear"] = len(evs) - rec["bull"]
        res.append(dict(name=name, by={"spx1928": rec}))
    return res, len(mr) - 1


# ------------------------------------------------------------------ step 5: annual rules
def year_ret(D, C, s, e, tz, close):
    def idx(t):
        x = t.astimezone(tz)
        d = x.date() + (dt.timedelta(days=1) if x.time() >= close else dt.timedelta(0))
        return bisect.bisect_left(D, d) - 1
    a, b = idx(s), idx(e)
    if a < 0 or b >= len(D) or b <= a or D[-1] < e.astimezone(tz).date():
        return None
    return (C[b] / C[a] - 1) * 100


def annual_compare(cases, split=None):
    """cases: [(tone or None, ret[, date])] -> rule years vs other years (and the same in each half if split)."""
    out = _annual_compare([c[:2] for c in cases])
    if split:
        for tone, v in out.items():
            hv = []
            for lo, hi in (("0000", split), (split, "9999")):
                part = _annual_compare([c[:2] for c in cases if lo <= c[2] < hi]).get(tone)
                hv.append(f"{part['right']}/{part['n']} vs {part['base']}%" if part else "–")
            v["halves"] = hv
    return out


def _annual_compare(cases):
    r = [(t, x) for t, x in cases if x is not None]
    out = {}
    for tone in ("Bullish", "Bearish"):
        sel = [x for t, x in r if t == tone]
        oth = [x for t, x in r if t != tone]
        if not sel:
            continue
        k = sum((x > 0) if tone == "Bullish" else (x < 0) for x in sel)
        if not oth:
            out[tone] = dict(n=len(sel), right=k, hit=round(k / len(sel) * 100), base=None, mean=round(statistics.fmean(sel), 2), mean_other=None,
                             p_value=None, note="no comparison years: the condition holds every year, so it cannot be tested")
            continue
        base = sum((x > 0) if tone == "Bullish" else (x < 0) for x in oth) / max(len(oth), 1)
        out[tone] = dict(n=len(sel), right=k, hit=round(k / len(sel) * 100), base=round(base * 100), mean=round(statistics.fmean(sel), 2),
                         mean_other=round(statistics.fmean(oth), 2) if oth else None, p_value=round(BM.binom_p(k, len(sel), base), 4))
    return out


def load_px(file):
    rows = list(csv.DictReader(open(BT / file)))
    return [dt.date.fromisoformat(r["date"]) for r in rows], [float(r["close"]) for r in rows]


def step5():
    nat = nyse_natal()
    spx = load_px("spx_GSPC_daily_1928.csv")
    sen = load_px("sensex_BSESN_daily_2000.csv")
    res = []
    rows_by = collections.defaultdict(list)
    for place, (D, C), tz, close, y0, mname in ((NYC, spx, ET, dt.time(16, 0), 1929, "S&P 500 (1929-2026)"), (MUM, sen, IST, dt.time(15, 30), 2000, "Sensex (2000-2026)")):
        ing = sun_at(0.0, dt.datetime(y0, 1, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC))
        fulls = lunations(dt.datetime(y0 - 1, 12, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC), 180.0)
        news = lunations(dt.datetime(y0 - 1, 12, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC), 0.0)
        ar = annual_returns(nat, dt.datetime(y0 - 2, 1, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC))
        for s, e in zip(ing, ing[1:]):
            ret = year_ret(D, C, s, e, tz, close)
            c = chart(s, place)
            # N1: lords of the ascendant at the last full and new moon before the ingress, the Moon's sign lord, the ingress ascendant lord
            score = 0
            parts = []
            for t, lab in (([f for f in fulls if f < s][-1], "full"), ([n for n in news if n < s][-1], "new"), (s, "ingress")):
                cc = chart(t, place)
                for L, nm in ((LORD[cc["a"]], f"{lab} asc lord"),) + (((LORD[sgn(cc, "Moon")], "Moon sign lord"),) if lab == "ingress" else ()):
                    g, bd = influence(cc, sgn(cc, L))
                    g = [x for x in g if x != L]
                    bd = [x for x in bd if x != L]
                    score += (1 if g else 0) - (1 if bd else 0)
                    parts.append(f"{nm} {L}: +{len(g)}/-{len(bd)}")
            rows_by[(mname, "N1 lunation and ingress ascendant lords with benefics / malefics")].append(("Bullish" if score > 0 else "Bearish" if score < 0 else None, ret, s.date().isoformat(), "; ".join(parts)))
            # N2: 7th lord in an angle, applying to a malefic or the waning Moon, or with/aspected by malefics -> disease, grain dear
            L7 = LORD[(c["a"] + 6) % 12]
            n2 = None
            if house(c, L7) in (1, 4, 7, 10):
                mal = [m for m in ("Sun", "Mars", "Saturn") if m != L7]
                app = any(applying(c, L7, m) for m in mal) or (not waxing(c) and L7 != "Moon" and applying(c, L7, "Moon"))
                g, bd = influence(c, sgn(c, L7))
                if app or [x for x in bd if x != L7]:
                    n2 = "Bearish"
            rows_by[(mname, "N2 7th lord of the ingress in an angle and afflicted: disease, grain dear")].append((n2, ret, s.date().isoformat(), L7))
            # N3: ingress ascendant lord benefic and dignified/angular with benefic aspect -> good; malefic and afflicted -> bad
            L = LORD[c["a"]]
            g, bd = influence(c, sgn(c, L))
            g, bd = [x for x in g if x != L], [x for x in bd if x != L]
            n3 = None
            if L in benefics(c) and (dignified(c, L) or house(c, L) in (1, 4, 7, 10)) and g and not weak(c, L):
                n3 = "Bullish"
            elif L in ("Sun", "Mars", "Saturn") and bd:
                n3 = "Bearish"
            rows_by[(mname, "N3 ingress ascendant lord: strong benefic = good year, afflicted malefic = bad year")].append((n3, ret, s.date().isoformat(), L))
            if place is NYC:
                # N4: house of the ingress ascendant counted from the NYSE natal ascendant
                h = (c["a"] - nat["a"]) % 12 + 1
                g, bd = influence(c, c["a"])
                dom = "good" if len(g) > len(bd) else "bad" if len(bd) > len(g) else None
                n4 = None
                if dom and h in (2, 9, 10, 11):
                    n4 = "Bullish" if dom == "good" else "Bearish"
                elif dom and h in (8, 12):
                    n4 = "Bearish" if dom == "good" else "Bullish"
                rows_by[(mname, "N4 ingress ascendant in the NYSE natal 2nd/9th/10th/11th (wealth) or 8th/12th (loss)")].append((n4, ret, s.date().isoformat(), f"house {h}, {dom}"))
                # N5: ascendant of the world in the 8th/12th from the NYSE natal or annual ascendant
                yr = [t for t in ar if t <= s][-1]
                ya = chart(yr, NYC)["a"]
                h1, h2 = h, (c["a"] - ya) % 12 + 1
                rows_by[(mname, "N5 ascendant of the world in the 8th/12th from the NYSE natal or annual ascendant: bad year")].append(("Bearish" if h1 in (8, 12) or h2 in (8, 12) else None, ret, s.date().isoformat(), f"natal {h1}, annual {h2}"))
            # B8 lord of the year: weekday of the Chaitra new moon
            chs = [t for t in chaitra_starts(s - dt.timedelta(days=45), s + dt.timedelta(days=20))]
            if chs:
                ch = chs[0]
                ch_next = chaitra_starts(ch + dt.timedelta(days=300), ch + dt.timedelta(days=420))
                if ch_next:
                    lord = hindu_weekday(ch, tz)
                    r2 = year_ret(D, C, ch, ch_next[0], tz, close)
                    rows_by[(mname, "B8 lord of the year (weekday of the Chaitra new moon, exchange time): Moon/Mercury/Jupiter/Venus good, Sun/Mars/Saturn bad")].append(("Bullish" if lord in GOOD_LORD else "Bearish", r2, ch.date().isoformat(), lord))
                    if place is NYC:
                        li = hindu_weekday(ch, IST)
                        rows_by[(mname, "B8 lord of the year, weekday taken at Indian sunrise (classical reckoning)")].append(("Bullish" if li in GOOD_LORD else "Bearish", r2, ch.date().isoformat(), li))
        if place is NYC:
            # NYSE annual return rules (T2, T3, T5, T6, T7)
            for s, e in zip(ar, ar[1:]):
                if s.year < y0:
                    continue
                ret = year_ret(D, C, s, e, tz, close)
                c = chart(s, NYC)
                wd = hindu_weekday(s, ET)
                rows_by[(mname, "T2 weekday of the NYSE annual return: Mon/Wed/Thu/Fri excellent, Tue/Sun/Sat loss")].append(("Bullish" if wd in GOOD_LORD else "Bearish", ret, s.date().isoformat(), wd))
                nk = NAKS[int(c["p"]["Moon"][0] // (360 / 27))]
                tone = "Bullish" if nk in ("Ashwini", "Mrigashira", "Hasta", "Pushya", "Punarvasu", "Swati", "Revati") else "Bearish" if nk in ("Bharani", "Magha", "Chitra", "Vishakha", "Shatabhisha", "Dhanishta", "Ashlesha") else None
                rows_by[(mname, "T2 Moon's nakshatra at the NYSE annual return: auspicious vs condemned")].append((tone, ret, s.date().isoformat(), nk))
                tith = int(((c["p"]["Moon"][0] - c["p"]["Sun"][0]) % 360) // 12) % 15 + 1
                tone = "Bearish" if tith in (1, 12, 4, 9, 14) else "Bullish"
                rows_by[(mname, "T2 tithi at the NYSE annual return: Nanda/Bhadra/Jaya/Purna (not 1, 12) good, Rikta bad")].append((tone, ret, s.date().isoformat(), tith))
                years = s.year - 1792
                mh = ((nat["a"] + years) % 12 - c["a"]) % 12 + 1
                rows_by[(mname, "T3 muntha in houses 1/2/3/5/9/10/11 (wealth, authority) vs 4/6/7/8/12")].append(("Bullish" if mh in (1, 2, 3, 5, 9, 10, 11) else "Bearish", ret, s.date().isoformat(), f"house {mh}"))
                s2 = (c["a"] + 1) % 12
                occ = [b for b in SEVEN + ["Rahu", "Ketu"] if sgn(c, b) == s2]
                ben = [b for b in occ if b in benefics(c)]
                mal = [b for b in occ if b in malefics(c)]
                rows_by[(mname, "T5 2nd house of the annual chart joined by benefics (gain) or only malefics (loss)")].append(("Bullish" if ben and not mal else "Bearish" if mal and not ben else None, ret, s.date().isoformat(), ",".join(occ)))
                rows_by[(mname, "T5 itthasala of the ascendant lord and the 2nd lord: easy gain")].append(("Bullish" if applying(c, LORD[c["a"]], LORD[s2]) else None, ret, s.date().isoformat(), ""))
                s11 = (c["a"] + 10) % 12
                o11 = [b for b in SEVEN if sgn(c, b) == s11 and not weak(c, b)]
                rows_by[(mname, "T6 planets in the 11th of the annual chart in strength: wealth")].append(("Bullish" if o11 else None, ret, s.date().isoformat(), ",".join(o11)))
                L1, L11 = LORD[c["a"]], LORD[s11]
                hl = (house(c, L1) == 11 and house(c, L11) == 11) or (house(c, L1) == 1 and house(c, L11) == 1) or (house(c, L1) == 11 and house(c, L11) == 1)
                rows_by[(mname, "T6 ascendant and 11th lords together in the 11th or 1st, or exchanged: gain (Hillaja)")].append(("Bullish" if hl else None, ret, s.date().isoformat(), ""))
                for nm, lon in sahams(c).items():
                    tone, why = saham_tone(c, lon)
                    rows_by[(mname, f"T7 (annual) {nm} saham joined/aspected by benefics and its ruler vs malefics")].append((tone, ret, s.date().isoformat(), why))
    for (mname, name), rows in rows_by.items():
        res.append(dict(name=name, market=mname, cmp=annual_compare([(t, r, d) for t, r, d, _ in rows], "1977-11-20" if mname.startswith("S&P") else "2013-11-20"), years=[dict(start=d, tone=t, ret=round(r, 2) if r is not None else None, why=w) for t, r, d, w in rows]))
    return res


# ------------------------------------------------------------------ main
def main():
    MK = markets()
    a, b = dt.datetime(2000, 11, 1, tzinfo=UTC), dt.datetime(2026, 11, 25, tzinfo=UTC)
    res = dict(made=dt.datetime.now(ET).strftime("%Y-%m-%d %H:%M ET"))
    print("step 1")
    res["step1"] = step1()
    print("step 2")
    mp = moon_passes(a, b)
    s2 = []
    for pl in ("Mercury", "Jupiter", "Venus"):
        evs = [ev(t, "Bullish" if n else "Bearish", None) for p, t, n in mp if p == pl]
        s2.append(test(f"B1 Moon passes north (bullish) / south (bearish) of {pl}", "BS 18.3-5 (Iyer p.127)", evs, MK))
    evs = [ev(t, "Bullish" if n else "Bearish", None) for p, t, n in mp]
    s2.append(test("B1 pooled: Moon passes north / south of Mercury, Jupiter or Venus", "BS 18.1-6", evs, MK))
    mr = mercury_reappear(a, b)
    s2.append(vol_test("B2 Mercury reappears from the Sun (14 deg, 12 deg when retrograde): abnormal price swings", "BS 7.1 (Iyer p.62)", [t for t, _ in mr], MK))
    res["step2"] = dict(tests=s2, n_moon=len(mp), n_merc=len(mr))
    print("step 3")
    s3 = []
    w = nak_windows("Mercury", {"bear": ("Bearish", {"Ashwini", "Shatabhisha", "Mula", "Revati"}), "bull": ("Bullish", {"Swati", "Bharani", "Rohini", "Krittika"})}, a, b)
    s3.append(test("B3 Mercury in Ashwini, Shatabhisha, Mula or Revati: tradesmen suffer (bearish)", "BS 7.6", w["bear"], MK))
    s3.append(test("B3 Mercury's Prakrita course (Swati, Bharani, Rohini, Krittika): prosperity (bullish)", "BS 7.9", w["bull"], MK))
    w = nak_windows("Mars", {"bull": ("Bullish", {"Shravana", "Magha", "Punarvasu", "Hasta", "Mula", "Purva Bhadrapada", "Ashwini", "Vishakha", "Rohini"})}, a, b)
    s3.append(test("B4 Mars in Shravana, Magha, Punarvasu, Hasta, Mula, P.Bhadrapada, Ashwini, Vishakha or Rohini: prosperity", "BS 6.13", w["bull"], MK))
    msr = mars_south_rohini(a, b)
    south = [(t, ml, sl) for t, ml, sl in msr if ml < sl]
    s3.append(test("B4 Mars passes south of Rohini (Aldebaran): prices rise (gold/silver bullish)", "BS 6.11", [ev(t, "Bullish") for t, _, _ in south], MK, ("gold", "silver")))
    w = nak_windows("Saturn", {"Pushya": ("Bearish", {"Pushya"}), "Magha": ("Bearish", {"Magha"}), "Dhanishta": ("Bullish", {"Dhanishta"}),
                               "Shat": ("Bearish", {"Shatabhisha", "Purva Bhadrapada"})}, dt.datetime(2000, 11, 1, tzinfo=UTC), b)
    for lab, nm in (("Pushya", "B6 Saturn in Pushya: tradesmen suffer"), ("Magha", "B6 Saturn in Magha: store-houses and merchants suffer"),
                    ("Dhanishta", "B6 Saturn in Dhanishta: treasury officers prosper"), ("Shat", "B6 Saturn in Shatabhisha or P.Bhadrapada: tradesmen suffer")):
        s3.append(test(nm, "BS 10.6-10.17", w.get(lab, []), MK))
    le = lord_events(MK)
    for h, lab in (("day1", "one session"), ("day5", "5 sessions")):
        out = dict(name=f"B8 lord of the day (Mon/Wed/Thu/Fri bullish, Tue bearish), {lab}", src="BS 19", by={})
        for k, mk in MK.items():
            rec, rows = run(le[k][h], mk)
            rec["halves"] = halves(rows, mk)
            out["by"][k] = rec
        s3.append(out)
    for k, tz in (("spx", ET), ("sensex", IST), ("gold", ET), ("silver", ET)):
        pass
    lm = {"ET": lord_month_events(a, b, ET), "IST": lord_month_events(a, b, IST)}
    out = dict(name="B8 lord of the month (weekday of the new moon): Moon/Mercury/Jupiter/Venus bullish, Sun/Mars/Saturn bearish", src="BS 19", by={})
    for k, mk in MK.items():
        rec, rows = run(lm["IST" if k == "sensex" else "ET"], mk)
        rec["halves"] = halves(rows, mk)
        out["by"][k] = rec
    s3.append(out)
    res["step3"] = dict(tests=s3, mars_rohini=[dict(t=t.isoformat(), mars_lat=round(ml, 2), star_lat=round(sl, 2)) for t, ml, sl in msr])
    print("step 4")
    MK28 = Mkt("spx1928", "S&P 500 (1928-)", "spx_GSPC_daily_1928.csv", ET, dt.time(16, 0), p0=dt.date(1928, 11, 20), p1=dt.date(2026, 11, 20))
    t4, nm = tajika_monthly(MK28)
    res["step4"] = dict(tests=t4, months=nm)
    print("step 5")
    res["step5"] = step5()
    # BH over every daily/monthly test with 10+ decided cases, per market
    allt = res["step2"]["tests"] + res["step3"]["tests"] + res["step4"]["tests"]
    for k in ("spx", "sensex", "gold", "silver", "spx1928"):
        items = [(t, t["by"][k]) for t in allt if not t.get("vol") and k in t["by"] and t["by"][k].get("p_value") is not None and (t["by"][k]["worked"] + t["by"][k]["failed"]) >= 10]
        qs = BM.bh([r["p_value"] for _, r in items]) if items else []
        for (t, r), q in zip(items, qs):
            r["q"] = round(q, 4)
    items = [v for t in res["step5"] for v in t["cmp"].values() if v.get("p_value") is not None]
    for v, q in zip(items, BM.bh([v["p_value"] for v in items])):
        v["q"] = round(q, 4)
    (OUT / "new_sources_test_ET.json").write_text(json.dumps(res, indent=1, default=str))
    write(res)
    summary(res)


def summary(res):
    s1 = res["step1"]
    print("B12 gold 1972:", s1["gold_1972"])
    print("B12 gold 2000:", s1["gold_2000"])
    print("B12 silver 2000:", s1["silver_2000"])
    for st in ("step2", "step3", "step4"):
        for t in res[st]["tests"]:
            print(t["name"][:90])
            for k, r in t["by"].items():
                if t.get("vol"):
                    print("   ", k, r)
                else:
                    print("   ", k, f"n={r['n']} w={r['worked']} f={r['failed']} hit={r['hit_rate']} base={r['base_rate']} avg={r['avg_dir_ret']} p={r['p_value']} q={r.get('q')} {r['verdict']} halves={r.get('halves')}")
    for t in res["step5"]:
        print(t["market"], "|", t["name"][:80], "|", t["cmp"])


# ------------------------------------------------------------------ page
CSS = """body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1180px;margin:0 auto;padding:16px;color:#1d1d1f;background:#fff;line-height:1.45}
h1{font-size:1.5em}h2{font-size:1.2em;margin-top:2em;border-bottom:1px solid #ddd}h3{font-size:1.02em;margin-top:1.4em}
table{border-collapse:collapse;font-size:.86em;margin:.5em 0}th,td{border:1px solid #ddd;padding:3px 7px;vertical-align:top}th{background:#f4f4f6}
td.n{text-align:right;white-space:nowrap}.wrap{overflow-x:auto}.m{color:#555;font-size:.92em}.ok{background:#e6f4ea}.bad{background:#fde8e8}
.box{background:#f7f7f9;border-left:4px solid #888;padding:.6em 1em;margin:1em 0}details{margin:.4em 0}
@media (prefers-color-scheme:dark){body{background:#111;color:#e6e6e6}th{background:#222}th,td{border-color:#333}.box{background:#1b1b1d}.ok{background:#16351f}.bad{background:#3a1818}.m{color:#aaa}}"""
MN = {"spx": "S&P 500", "sensex": "Sensex", "gold": "Gold", "silver": "Silver", "spx1928": "S&P 500 (1928-2026)"}


def cell(r):
    if r.get("hit_rate") is None:
        return "<td class='n'>–</td>"
    good = r["verdict"] == "Worked" or (r.get("p_value") is not None and r["p_value"] < 0.05 and r["hit_rate"] > r["base_rate"])
    bad = r["verdict"] == "Failed"
    cls = " ok" if good else " bad" if bad else ""
    q = f", q {r['q']}" if r.get("q") is not None else ""
    hv = f"<br><span class='m'>halves {r['halves'][0]}% / {r['halves'][1]}%</span>" if r.get("halves") else ""
    return (f"<td class='n{cls}'>{r['worked']}/{r['worked'] + r['failed']} = <b>{r['hit_rate']}%</b> vs {r['base_rate']}%"
            f"<br>avg {r['avg_dir_ret']:+.2f}%, p {r['p_value']}{q}<br>{r['verdict']}{hv}</td>")


def table(tests, keys):
    h = "".join(f"<th>{MN[k]}</th>" for k in keys)
    rows = []
    for t in tests:
        if t.get("vol"):
            cs = "".join(f"<td class='n{' ok' if (t['by'][k]['p_value'] or 1) < 0.05 else ''}'>{t['by'][k]['big']}/{t['by'][k]['n']} = <b>{t['by'][k]['share']}%</b> above the year's median |5-day move| (expected 50%)<br>mean ratio {t['by'][k]['mean_ratio']}, p {t['by'][k]['p_value']}</td>" for k in keys)
        else:
            cs = "".join(cell(t["by"][k]) if k in t["by"] else "<td class='n'>–</td>" for k in keys)
        rows.append(f"<tr><td>{html.escape(t['name'])}<br><span class='m'>{html.escape(t.get('src', ''))}</span></td>{cs}</tr>")
    return f"<div class='wrap'><table><thead><tr><th>Rule</th>{h}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def write(res):
    s1 = res["step1"]

    def s1row(lab, d):
        return "".join(f"<tr><td>{k}</td><td class='n'>{v['n']}</td><td class='n'>{v['up5']}/{v['n']}</td><td class='n'>{v['mean5']:+.2f}%</td><td class='n'>{v['up6']}/{v['n']}</td><td class='n'>{v['mean6']:+.2f}%</td></tr>"
                       for k, v in d.items() if isinstance(v, dict) and v.get("n"))
    s1t = "".join(f"<h3>{lab}</h3><div class='wrap'><table><thead><tr><th>Years</th><th>n</th><th>Up, sold as the 5th month starts (Sun into Sagittarius)</th><th>Avg</th><th>Up, sold as it ends (Sun into Capricorn)</th><th>Avg</th></tr></thead><tbody>{s1row(lab, d)}</tbody></table></div><p class='m'>p (eclipse years' up count vs the other years' up rate, sold mid-Dec): {d['p_up5']}</p>"
                  for lab, d in (("Gold 1972-2025 (monthly prices before 2000, daily after)", s1["gold_1972"]), ("Gold 2000-2025 (daily COMEX)", s1["gold_2000"]), ("Silver 2000-2025 (daily COMEX)", s1["silver_2000"])))
    yrs = "".join(f"<tr><td>{r['year']}</td><td>{', '.join(r['eclipse']) or '–'}</td><td class='n'>{r.get('gold', {}).get('r5', '–')}</td><td class='n'>{r.get('gold', {}).get('r6', '–')}</td><td class='n'>{r.get('silver', {}).get('r5', '–')}</td><td class='n'>{r.get('silver', {}).get('r6', '–')}</td></tr>" for r in s1["years"])
    k4 = ["spx", "sensex", "gold", "silver"]
    s5 = []
    for t in res["step5"]:
        c = t["cmp"]
        cs = "<br>".join((f"<b>{tone}</b>: {v['right']}/{v['n']} right; {v['note']}" if v.get("note") else
                          f"<b>{tone}</b>: {v['right']}/{v['n']} right = {v['hit']}% vs {v['base']}% in the other years; mean {v['mean']:+.1f}% vs {v['mean_other']:+.1f}%; p {v['p_value']}, q {v.get('q')}; halves {' / '.join(v.get('halves', []))}") for tone, v in c.items()) or "no case"
        good = any(v.get("p_value") is not None and v["p_value"] < 0.05 and v["hit"] > v["base"] for v in c.values())
        yr = "".join(f"<tr><td>{y['start']}</td><td>{y['tone'] or '–'}</td><td class='n'>{y['ret'] if y['ret'] is not None else '–'}</td><td class='m'>{html.escape(str(y['why']))}</td></tr>" for y in t["years"])
        s5.append(f"<tr><td>{html.escape(t['name'])}</td><td>{t['market']}</td><td class='{'ok' if good else ''}'>{cs}<details><summary>years</summary><table>{yr}</table></details></td></tr>")
    mr = "".join(f"<li>{x['t'][:10]}: Mars latitude {x['mars_lat']}°, Aldebaran {x['star_lat']}°{' (south)' if x['mars_lat'] < x['star_lat'] else ''}</li>" for x in res["step3"]["mars_rohini"])
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>New Sources Backtest</title><style>{CSS}</style></head><body>
<h1>New sources backtest: Brihat Samhita (Iyer), Tajika Nilakanthi, Hayanaratna</h1>
<p class="m">Made {res['made']}. The rules are from <code>NEW_SOURCES_REVIEW_2026-11.md</code>, tested in the order the user approved, using the method in PROJECT_KNOWLEDGE §6. Daily rules: S&P 500 and Sensex (each in its own exchange time) and COMEX gold and silver, 20 Nov 2000 – 20 Nov 2026. Monthly Tajika rules: S&P 500, 1928–2026. Annual rules: S&P 500 1929–2026 and Sensex 2000–2026. Sidereal Lahiri, mean node, whole-sign houses. Nothing was tuned; each rule is scored as stated. Green: the hit rate is above the base with p &lt; 0.05, or the verdict is Worked. Red: Failed. q is the Benjamini–Hochberg value per market over every daily and monthly test.</p>
<div class="box" id="verdict">VERDICT_PLACEHOLDER</div>
<h2>Step 1 · B12: Brihat Samhita 42.6 with its portent condition</h2>
<p class="m">Both translations make 42.6 conditional on portents seen at the new or full moon or at the Sun's ingress. The only portent that can be computed is an eclipse. Buy at the close before the first eclipse that falls while the Sun is in sidereal Leo; in other years, buy at the Leo ingress. Sell when the 5th solar month starts (Sun into Sagittarius) or ends (Sun into Capricorn).</p>
{s1t}
<details><summary>Year by year (gold and silver % move)</summary><div class="wrap"><table><thead><tr><th>Year</th><th>Eclipse with the Sun in Leo</th><th>Gold, sold mid-Dec</th><th>Gold, sold mid-Jan</th><th>Silver, sold mid-Dec</th><th>Silver, sold mid-Jan</th></tr></thead><tbody>{yrs}</tbody></table></div></details>
<p>2026: {s1['y2026']['eclipse']}. The condition holds, so the stated sell window is {s1['y2026']['sell_from']} to {s1['y2026']['sell_to']}.</p>
<h2>Step 2 · B1: Moon north or south of planets · B2: Mercury reappearing</h2>
<p class="m">{res['step2']['n_moon']} Moon conjunctions with Mercury, Jupiter and Venus; {res['step2']['n_merc']} reappearances of Mercury. B1 is scored on the 5-session move. B2 says "abnormally enhancing or lowering" prices, so it is scored as volatility: how often the 5-session move after the event is larger than the median 5-session move of that year.</p>
{table(res['step2']['tests'], k4)}
<h2>Step 3 · B3, B4, B6: planets in the stated nakshatras · B8: lord of the day, month and year</h2>
<p class="m">Nakshatra stays are windows, scored from the close before entry to the last close inside (clipped to the Nov–Nov year). Lord of the day: every session, by weekday (Mon/Wed/Thu/Fri bullish, Tue bearish; markets are shut on Sat/Sun), scored on that session and on 5 sessions. Lord of the month: the weekday lord of the Hindu day of each new moon (sunrise taken as 06:00 local), windowed to the next new moon. Mars passing Aldebaran (Rohini): <ul>{mr}</ul></p>
{table(res['step3']['tests'], k4)}
<h2>Step 4 · T7, T8, T9: Tajika monthly-chart rules on the NYSE sidereal monthly returns</h2>
<p class="m">{res['step4']['months']} monthly charts (Model B, cast for New York): each month runs from one return to the next, scored on the S&P 500 1928–2026, with halves 1928–77 and 1977–2026. Friendship between the navamsha lords is by sign distance (Romakatajika, Hayanaratna 2.4): 3/5/9/11 or the same sign is friendly, 4/7/10 inimical. Sahams use Tajika aspects with the one-sign correction.</p>
{table(res['step4']['tests'], ['spx1928'])}
<h2>Step 5 · Annual rules: Aries-ingress, lunation and NYSE annual-return charts</h2>
<p class="m">One case a year, compared with the other years. The S&P 500 Aries-ingress years are cast for New York and the Sensex years for Mumbai. The NYSE rules (N4, N5, T2–T7) are for the S&P only. T4 (ruler of the year) was not tested: it needs the Tajika fivefold strength, which has not been built yet.</p>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Market</th><th>Result</th></tr></thead><tbody>{''.join(s5)}</tbody></table></div>
</body></html>"""
    allt = res["step2"]["tests"] + res["step3"]["tests"] + res["step4"]["tests"]
    n_d = sum(len(t["by"]) for t in allt)
    sig = [(t["name"], k, r) for t in allt if not t.get("vol") for k, r in t["by"].items() if r.get("q") is not None and r["q"] < 0.10 and r["hit_rate"] > r["base_rate"]]
    watch = [(t["name"], k, r) for t in allt if not t.get("vol") for k, r in t["by"].items() if r.get("p_value") is not None and r["p_value"] < 0.05 and r["hit_rate"] > r["base_rate"]]
    ann = [(t["name"], t["market"], tone, v) for t in res["step5"] for tone, v in t["cmp"].items()]
    asig = [x for x in ann if x[3].get("q", 1) < 0.10 and x[3]["hit"] > x[3]["base"]]
    awatch = [x for x in ann if x[3].get("p_value") is not None and x[3]["p_value"] < 0.05 and x[3]["hit"] > x[3]["base"]]
    e1 = s1["gold_1972"]["eclipse years"]
    o1 = s1["gold_1972"]["other years"]
    li = "".join(f"<li>{html.escape(n)} ({MN[k]}): {r['worked']}/{r['worked'] + r['failed']} = {r['hit_rate']}% vs {r['base_rate']}%, p {r['p_value']}, q {r.get('q')}</li>" for n, k, r in watch)
    la = "".join(f"<li>{html.escape(n)} ({m}, {tone}): {v['right']}/{v['n']} = {v['hit']}% vs {v['base']}%, mean {v['mean']:+.1f}% vs {v['mean_other']:+.1f}%, p {v['p_value']}, q {v.get('q')}, halves {' / '.join(v.get('halves', []))}</li>" for n, m, tone, v in awatch)
    verdict = (f"<b>Verdict: no new rule holds up.</b> {n_d} daily and monthly results and {len(ann)} annual results were scored. "
               f"After the Benjamini–Hochberg correction, {len(sig) + len(asig)} pass (q &lt; 0.10). <b>Nothing is added to the rule set or the calendar.</b>"
               f"<ul><li><b>B12 (42.6 with an eclipse):</b> worse, not better. Gold rose by mid-December in {e1['up5']} of {e1['n']} eclipse years, against {o1['up5']} of {o1['n']} other years (1972–2025). So 2026's qualifying eclipse is not a reason to expect a mid-December to mid-January gain.</li>"
               f"<li><b>Nominal p &lt; 0.05 but not significant after correction (daily and monthly):</b><ul>{li or '<li>none</li>'}</ul></li>"
               f"<li><b>Nominal p &lt; 0.05 but not significant after correction (annual):</b><ul>{la or '<li>none</li>'}</ul>"
               f"The lord-of-the-year split (good lords Moon, Mercury, Jupiter, Venus) is right in both halves on the S&P. But it weakens to about p 0.10 when the weekday is taken at Indian sunrise, the classical reckoning (see the row below), so it depends on a convention and goes on a watch list only. N5 (ascendant of the world in the 8th or 12th) has more down years than usual, but the average of those years is still up, so it does not meet the §6 verdict.</li></ul>")
    page = page.replace("VERDICT_PLACEHOLDER", verdict)
    (OUT / "new_sources_test_ET.html").write_text(page)


if __name__ == "__main__":
    main()
