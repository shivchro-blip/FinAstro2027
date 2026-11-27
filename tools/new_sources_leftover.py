"""The rules from the three new books that tools/new_sources_test.py did not cover, plus the calendar layer.

    python tools/new_sources_leftover.py      # after tools/new_sources_test.py

Rules (Reference_materials/extracted/NEW_SOURCES_REVIEW_2026-11.md):
  B5   Venus disappearing / reappearing (10 deg from the Sun, 8 when retrograde) in the northern / southern path, the
       6th mandala; Venus in Swati (BS ch.9)
  B7   planetary war: Mercury defeated by Jupiter or Saturn, Mars defeated by Venus, Saturn defeated by Mercury (bearish);
       Saturn defeated by Venus (grain dear) (BS 17). Defeat = the planet with the lower (southern) latitude at the
       conjunction, within 1 degree of longitude (BS 17: the northern planet wins).
  B9   planetary meetings: Kosha (Saturn and Jupiter in one sign with another planet) and Sammoha (4-5 planets with
       Rahu or Ketu) are disastrous (BS 20.6-9)
  B10  BS 47: Saturn and Rahu in one sign (commodities scarce); Mars or Saturn retrograde in Cancer, Leo or Pisces;
       Saturn, Mars and Jupiter in mutual aspect; Sun in the last part of Taurus/Gemini/Scorpio/Leo with Jupiter and
       Mars; 5+ planets in one sign; Jupiter or Saturn entering a sign while retrograde
  B11  eclipses in sidereal Libra or Sagittarius (traders, merchants suffer); eclipses in the lunar month Chaitra (gold
       dealers suffer) (BS 5.40, 5.41, 5.74)
  B13  BS 40.11 Sun in Scorpio with malefics in the 6th and 7th from it: commodity prices fall; BS 40.14 / Nilakanthi 36:
       Sun in Sagittarius, Capricorn or Aquarius with benefics / malefics (the two sources disagree on the direction)
  B6   Saturn in Pushya, Magha, Dhanishta, Shatabhisha/P.Bhadrapada over the S&P 1928-2026 (more windows)
  T4   ruler of the year in the NYSE annual chart with the Tajika five-dignity strength (Hayanaratna 2.5, 5.8-5.11):
       good / evil year; strong Jupiter, Venus or Mercury as ruler = great gain of wealth; combust or retrograde ruler =
       loss; T6 Mercury as ruler in the 2nd or 11th aspected by benefics = gain from trade
  T10  "gain of the substance of a planet strong in the year, loss of a weak one" (Hayanaratna 1.5): gold = Mercury
       (Trailokyaprakasha) or Sun (BS 16.4); silver = Venus or Moon; strength in the Aries-ingress chart
Not tested, with the reason in the report: horary rules (N7, N8), crop directions (N9), annual dashas (T11).

Method as in new_sources_test.py (PROJECT_KNOWLEDGE section 6; annual rules against the other years; BH q over all).
Writes build/pdfref/new_sources_leftover_ET.{html,json}; the JSON's "calendar" block feeds tools/calendar_2026.py.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import html
import json
import pathlib
import statistics
import sys

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import backtest_market as BM  # noqa: E402
import new_sources_test as T  # noqa: E402

OUT = ROOT / "build" / "pdfref"
UTC, ET, IST = T.UTC, T.ET, T.IST
A, B = dt.datetime(2000, 11, 1, tzinfo=UTC), dt.datetime(2026, 11, 25, tzinfo=UTC)
NORTH = set(range(1, 10))          # Bharani .. Magha (Garga's northern path, Iyer p.62 note)
MIDDLE = set(range(10, 19))        # Purva Phalguni .. Mula
SOUTH = set(range(19, 27)) | {0}   # Purva Ashadha .. Ashwini
MANDALA6 = {22, 23, 24, 25, 26, 0}  # Dhanishta + 5
FRIENDS = ({"Sun", "Moon", "Mars", "Jupiter"}, {"Mercury", "Venus", "Saturn"})      # Tajikasara 73
HADDA = [[("Jupiter", 6), ("Venus", 6), ("Mercury", 8), ("Mars", 5), ("Saturn", 5)], [("Venus", 8), ("Mercury", 6), ("Jupiter", 8), ("Saturn", 5), ("Mars", 3)],
         [("Mercury", 6), ("Venus", 6), ("Jupiter", 5), ("Mars", 7), ("Saturn", 6)], [("Mars", 7), ("Venus", 6), ("Mercury", 6), ("Jupiter", 7), ("Saturn", 4)],
         [("Jupiter", 6), ("Venus", 5), ("Saturn", 7), ("Mercury", 6), ("Mars", 6)], [("Mercury", 7), ("Venus", 10), ("Jupiter", 4), ("Mars", 7), ("Saturn", 2)],
         [("Saturn", 6), ("Mercury", 8), ("Jupiter", 7), ("Venus", 7), ("Mars", 2)], [("Mars", 7), ("Venus", 4), ("Mercury", 8), ("Jupiter", 5), ("Saturn", 6)],
         [("Jupiter", 12), ("Venus", 5), ("Mercury", 4), ("Mars", 5), ("Saturn", 4)], [("Mercury", 7), ("Jupiter", 7), ("Venus", 8), ("Saturn", 4), ("Mars", 4)],
         [("Mercury", 7), ("Venus", 6), ("Jupiter", 7), ("Mars", 5), ("Saturn", 5)], [("Venus", 12), ("Jupiter", 4), ("Mercury", 3), ("Mars", 9), ("Saturn", 2)]]
DECAN = ["Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter"]             # Samjnatantra 1.30: from Mars / Sun / Venus in weekday order
WEEK = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
FALL_DEG = {"Sun": 190, "Moon": 213, "Mars": 118, "Mercury": 345, "Jupiter": 275, "Venus": 177, "Saturn": 20}
TRIP = {0: ("Sun", "Jupiter", "Saturn"), 1: ("Venus", "Moon", "Mars"), 2: ("Saturn", "Mercury", "Jupiter"), 3: ("Venus", "Mars", "Moon")}   # Samarasimha (Hayanaratna p.455): day, night, constant


# ------------------------------------------------------------------ Tajika strength (Hayanaratna 2.5)
def rel(p, owner):
    if p == owner:
        return "own"
    return "friend" if any(p in g and owner in g for g in FRIENDS) else "enemy"


def decan_lord(lon):
    s, k = int(lon // 30), int((lon % 30) // 10)
    seq = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun", "Moon"]
    first = {"Mars": 0, "Sun": 5, "Venus": 3}[["Mars", "Sun", "Venus"][k]]
    return seq[(first + s) % 7]


def hadda_lord(lon):
    s, d = int(lon // 30), lon % 30
    acc = 0
    for p, w in HADDA[s]:
        acc += w
        if d < acc:
            return p
    return HADDA[s][-1][0]


def tajika_strength(c, p):
    """Twenty-point strength (Paddhatibhusana 30-31 / Tajikasara 74-75 with Vamana's exaltation strength)."""
    lon = c["p"][p][0]
    W = {"own": 1.0, "friend": 0.5, "enemy": 0.25}
    dom = 30 * W[rel(p, T.LORD[int(lon // 30)])]
    had = 15 * W[rel(p, hadda_lord(lon))]
    dec = 10 * W[rel(p, decan_lord(lon))]
    nav = 5 * W[rel(p, T.LORD[T.navamsa_sign(lon)])]
    ucc = T.sep(lon, FALL_DEG[p]) / 9
    return round((dom + had + dec + nav + ucc) / 4, 2)


def ruler_of_year(c, nat, muntha_sign):
    day = T.house(c, "Sun") >= 7
    trip = TRIP[c["a"] % 4]
    tr = max((trip[0] if day else trip[1], trip[2]), key=lambda p: tajika_strength(c, p))
    cands = {T.LORD[nat["a"]]: "natal ascendant lord", T.LORD[c["a"]]: "annual ascendant lord", T.LORD[muntha_sign]: "muntha lord",
             tr: "triplicity lord", T.LORD[T.sgn(c, "Sun" if day else "Moon")]: ("Sun" if day else "Moon") + "-sign lord"}
    asp = [p for p in cands if T.tajika_aspects_sign(c, p, c["a"])]
    pool = asp or [T.LORD[c["a"]]]
    r = max(pool, key=lambda p: (tajika_strength(c, p), list(cands).count(p)))
    return r, cands.get(r, "annual ascendant lord"), tajika_strength(c, r), bool(asp)


# ------------------------------------------------------------------ daily-event detectors
def venus_phases(a, b):
    def g(y):
        el = T.sep(T.pos(y, "Venus", False)[0], T.pos(y, "Sun", False)[0])
        return el - (8 if T.pos(y, "Venus", False)[2] < 0 else 10)
    out, x, end = [], T.jd(a), T.jd(b)
    while x < end:
        y = x + 0.5
        if (g(x) < 0) != (g(y) < 0):
            c = T.solve(g, x, y)
            nk = int(T.pos(c, "Venus")[0] // (360 / 27))
            out.append((T.from_jd(c), "reappears" if g(y) >= 0 else "disappears", nk))
        x = y
    return out


def wars(a, b):
    pl = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    out = []
    for i, p in enumerate(pl):
        for q in pl[i + 1:]:
            f = lambda y, p=p, q=q: T.wrap(T.pos(y, p, False)[0] - T.pos(y, q, False)[0])
            x, end = T.jd(a), T.jd(b)
            while x < end:
                y = x + 0.5
                if (f(x) < 0) != (f(y) < 0) and abs(f(x)) < 10:
                    c = T.solve(f, x, y)
                    lp, lq = T.pos(c, p, False)[1], T.pos(c, q, False)[1]
                    if abs(lp - lq) < 1.0:                    # BS 17: within a degree
                        loser, winner = (p, q) if lp < lq else (q, p)
                        out.append((T.from_jd(c), winner, loser))
                x = y
    return sorted(out)


def sign_count_fn(y):
    s = collections.Counter(int(T.pos(y, b)[0] // 30) for b in T.SEVEN)
    r = int(T.node(y) // 30)
    return s, r, (r + 6) % 12


def meetings(a, b):
    def kosha(y):
        s = {b: int(T.pos(y, b)[0] // 30) for b in T.SEVEN}
        return s["Saturn"] == s["Jupiter"] and sum(v == s["Saturn"] for v in s.values()) >= 3
    def sammoha(y):
        cnt, r, k = sign_count_fn(y)
        return any(n >= 4 and sg in (r, k) for sg, n in cnt.items())
    def five(y):
        cnt, _, _ = sign_count_fn(y)
        return max(cnt.values()) >= 5
    return {"kosha": [(s, e) for s, e, v in T.spans(kosha, a, b, 0.5) if v],
            "sammoha": [(s, e) for s, e, v in T.spans(sammoha, a, b, 0.25) if v],
            "five": [(s, e) for s, e, v in T.spans(five, a, b, 0.25) if v]}


def b10_spans(a, b):
    def sat_rahu(y):
        return int(T.pos(y, "Saturn")[0] // 30) == int(T.node(y) // 30)
    def retro_cls(y):
        out = []
        for p in ("Mars", "Saturn"):
            lon, _, sp = T.pos(y, p)
            if sp < 0 and int(lon // 30) in (3, 4, 11):
                out.append(p)
        return tuple(out)
    def triple(y):
        c = {b: int(T.pos(y, b)[0] // 30) for b in ("Saturn", "Mars", "Jupiter")}
        def asp(p, q):
            d = (c[q] - c[p]) % 12 + 1
            return d == 1 or d in T.DRISHTI[p]
        ps = list(c)
        return all(asp(p, q) or asp(q, p) for i, p in enumerate(ps) for q in ps[i + 1:])
    def sun_end(y):
        lon = T.pos(y, "Sun")[0]
        s = int(lon // 30)
        if s not in (1, 2, 7, 4) or lon % 30 < 26 + 2 / 3:
            return False
        return int(T.pos(y, "Jupiter")[0] // 30) == s and int(T.pos(y, "Mars")[0] // 30) == s
    return {"satrahu": [(s, e) for s, e, v in T.spans(sat_rahu, a, b, 1) if v],
            "retro_any": [(s, e) for s, e, v in T.spans(lambda y: bool(retro_cls(y)), a, b, 0.5) if v],
            "retro_both": [(s, e) for s, e, v in T.spans(lambda y: len(retro_cls(y)) == 2, a, b, 0.5) if v],
            "triple": [(s, e) for s, e, v in T.spans(triple, a, b, 0.5) if v],
            "sun_end": [(s, e) for s, e, v in T.spans(sun_end, a, b, 0.25) if v]}


def retro_ingress(a, b):
    out = []
    for p in ("Jupiter", "Saturn"):
        f = lambda y, p=p: int(T.pos(y, p)[0] // 30)
        for s, e, v in T.spans(f, a, b, 1):
            sp = T.pos(T.jd(s), p)[2]
            if sp < 0 and s > a + dt.timedelta(days=2):
                out.append((s, p))
    return out


def eclipses(a, b):
    out = []
    for fn, kind in ((swe.lun_eclipse_when, "lunar"), (swe.sol_eclipse_when_glob, "solar")):
        x = T.jd(a)
        while x < T.jd(b):
            m = fn(x)[1][0]
            if m < T.jd(b):
                body = "Moon" if kind == "lunar" else "Sun"
                sg = int(T.pos(m, body)[0] // 30)
                nm = [t for t in T.lunations(T.from_jd(m) - dt.timedelta(days=32), T.from_jd(m) - dt.timedelta(hours=12))][-1:]
                month_sun = int(T.pos(T.jd(nm[0]), "Sun")[0] // 30) if nm else None
                if kind == "solar":
                    month_sun = int(T.pos(T.jd(nm[0]), "Sun")[0] // 30) if nm else None
                out.append((T.from_jd(m), kind, sg, month_sun))
            x = m + 20
    return sorted(out)


def sun_with(a, b):
    """Sun-sign conditions: BS 40.11 and BS 40.14 / Nilakanthi 36 (daily states, merged into windows)."""
    def st(y):
        t = T.from_jd(y)
        c = T.chart(t, T.NYC)
        ss = T.sgn(c, "Sun")
        if ss == 7:
            m6 = [m for m in ("Mars", "Saturn", "Rahu", "Ketu") if (T.sgn(c, m) - ss) % 12 == 5]
            m7 = [m for m in ("Mars", "Saturn", "Rahu", "Ketu") if (T.sgn(c, m) - ss) % 12 == 6]
            if m6 and m7:
                return "sco"
        if ss in (8, 9, 10):
            g, bd = T.influence(c, ss)
            g = [x for x in g if x != "Sun"]
            bd = [x for x in bd if x != "Sun"]
            if g and not bd:
                return "winter_ben"
            if bd and not g:
                return "winter_mal"
        return None
    return T.spans(st, a, b, 0.5)


# ------------------------------------------------------------------ tests
def daily_tests(MK, MK28):
    res = []
    vp = venus_phases(A, B)
    res.append(T.test("B5 Venus disappears or reappears in the northern path (Bharani-Magha): prosperity", "BS ch.9 (Iyer p.77)",
                      [T.ev(t, "Bullish") for t, k, n in vp if n in NORTH], MK))
    res.append(T.test("B5 Venus disappears or reappears in the southern path (P.Ashadha-Ashwini): misery", "BS ch.9",
                      [T.ev(t, "Bearish") for t, k, n in vp if n in SOUTH], MK))
    res.append(T.test("B5 Venus reappears in the 6th mandala (Dhanishta + 5): wealth and prosperity", "BS ch.9 (Iyer p.79)",
                      [T.ev(t, "Bullish") for t, k, n in vp if k == "reappears" and n in MANDALA6], MK))
    w = T.nak_windows("Venus", {"sw": ("Bearish", {"Swati"})}, A, B)
    res.append(T.test("B5 Venus in Swati: merchants lawless (bearish)", "BS ch.9 (Iyer p.80)", w["sw"], MK))
    wr = wars(A, B)
    bear = [T.ev(t, "Bearish") for t, wn, ls in wr if (ls, wn) in (("Mercury", "Jupiter"), ("Mercury", "Saturn"), ("Mars", "Venus"), ("Saturn", "Mercury"))]
    res.append(T.test("B7 planetary war: Mercury beaten by Jupiter/Saturn, Mars by Venus, Saturn by Mercury (bearish)", "BS 17.18-25", bear, MK))
    res.append(T.test("B7 planetary war: Saturn beaten by Venus, grain dear (commodities bullish)", "BS 17.25",
                      [T.ev(t, "Bullish") for t, wn, ls in wr if (ls, wn) == ("Saturn", "Venus")], MK, ("gold", "silver")))
    mt = meetings(A, B)
    res.append(T.test("B9 Kosha meeting (Saturn and Jupiter in one sign with another planet): disastrous", "BS 20.7-9", [T.ev(s, "Bearish", e) for s, e in mt["kosha"]], MK))
    res.append(T.test("B9 Sammoha meeting (4+ planets in one sign with Rahu or Ketu): disastrous", "BS 20.6-9", [T.ev(s, "Bearish", e) for s, e in mt["sammoha"]], MK))
    res.append(T.test("B10 five or more planets in one sign: famine", "BS 47 (Iyer p.228)", [T.ev(s, "Bearish", e) for s, e in mt["five"]], MK))
    bs = b10_spans(A, B)
    res.append(T.test("B10 Saturn and Rahu in one sign: commodities scarce (gold/silver bullish)", "BS 47 (Iyer p.229)", [T.ev(s, "Bullish", e) for s, e in bs["satrahu"]], MK, ("gold", "silver")))
    res.append(T.test("B10 Saturn and Rahu in one sign: drought and famine (stocks bearish)", "BS 47", [T.ev(s, "Bearish", e) for s, e in bs["satrahu"]], MK, ("spx", "sensex")))
    res.append(T.test("B10 Mars or Saturn retrograde in Cancer, Leo or Pisces: much suffering", "BS 47 (Iyer p.228)", [T.ev(s, "Bearish", e) for s, e in bs["retro_any"]], MK))
    res.append(T.test("B10 Mars and Saturn both retrograde in Cancer, Leo or Pisces", "BS 47", [T.ev(s, "Bearish", e) for s, e in bs["retro_both"]], MK))
    res.append(T.test("B10 Saturn, Mars and Jupiter in mutual aspect: hunger and weapons", "BS 47", [T.ev(s, "Bearish", e) for s, e in bs["triple"]], MK))
    res.append(T.test("B10 Sun at the end of Taurus/Gemini/Scorpio/Leo with Jupiter and Mars: famine", "BS 47", [T.ev(s, "Bearish", e) for s, e in bs["sun_end"]], MK))
    ri = retro_ingress(A, B)
    res.append(T.test("B10 Jupiter or Saturn enters a sign while retrograde: kings lose glory / famine", "BS 47", [T.ev(t, "Bearish") for t, p in ri], MK))
    ec = eclipses(A, B)
    res.append(T.test("B11 eclipse in sidereal Libra or Sagittarius: traders and merchants suffer", "BS 5.40-41", [T.ev(t, "Bearish") for t, k, sg, ms in ec if sg in (6, 8)], MK))
    res.append(T.test("B11 eclipse in the lunar month Chaitra: dealers in gold suffer", "BS 5.74 (Iyer p.54)", [T.ev(t, "Bearish") for t, k, sg, ms in ec if ms == 11], MK, ("gold", "silver")))
    sw = sun_with(A, B)
    res.append(T.test("B13 Sun in Scorpio with malefics in the 6th and 7th from it: commodity prices fall", "BS 40.11", [T.ev(s, "Bearish", e) for s, e, v in sw if v == "sco"], MK, ("gold", "silver")))
    res.append(T.test("B13 Sun in Sag/Cap/Aqu with benefics: prices moderate or rise (BS 40.14); Nilakanthi 36 says cheap", "BS 40.14 vs Nilakanthi 36",
                      [T.ev(s, "Bullish", e) for s, e, v in sw if v == "winter_ben"], MK, ("gold", "silver")))
    res.append(T.test("B13 Sun in Sag/Cap/Aqu with malefics: prices fall (BS 40.14); Nilakanthi 36 says dear", "BS 40.14 vs Nilakanthi 36",
                      [T.ev(s, "Bearish", e) for s, e, v in sw if v == "winter_mal"], MK, ("gold", "silver")))
    w = T.nak_windows("Saturn", {"Pushya": ("Bearish", {"Pushya"}), "Magha": ("Bearish", {"Magha"}), "Dhanishta": ("Bullish", {"Dhanishta"}),
                               "Shat": ("Bearish", {"Shatabhisha", "Purva Bhadrapada"})}, dt.datetime(1928, 11, 1, tzinfo=UTC), B)
    for lab, nm in (("Pushya", "B6 Saturn in Pushya: tradesmen suffer"), ("Magha", "B6 Saturn in Magha: merchants suffer"),
                    ("Dhanishta", "B6 Saturn in Dhanishta: treasury officers prosper"), ("Shat", "B6 Saturn in Shatabhisha or P.Bhadrapada: tradesmen suffer")):
        evs = w.get(lab, [])
        rec, rows = T.run(evs, MK28)
        rec["halves"] = [BM.aggregate(rows, MK28, MK28.p0, dt.date(1977, 11, 20))["hit_rate"], BM.aggregate(rows, MK28, dt.date(1977, 11, 20), MK28.p1)["hit_rate"]]
        res.append(dict(name=nm + " (S&P 1928-2026)", src="BS 10.6-17", by={"spx1928": rec}))
    counts = dict(venus=len(vp), wars=len(wr), kosha=len(mt["kosha"]), sammoha=len(mt["sammoha"]), five=len(mt["five"]), eclipses=len(ec),
                  wars_list=[f"{t:%Y-%m-%d} {wn} beats {ls}" for t, wn, ls in wr])
    return res, counts


def annual_tests():
    nat = T.nyse_natal()
    D, C = T.load_px("spx_GSPC_daily_1928.csv")
    ar = T.annual_returns(nat, dt.datetime(1927, 1, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC))
    rows = collections.defaultdict(list)
    for s, e in zip(ar, ar[1:]):
        if s.year < 1929:
            continue
        ret = T.year_ret(D, C, s, e, ET, dt.time(16, 0))
        c = T.chart(s, T.NYC)
        muntha = (nat["a"] + s.year - 1792) % 12
        r, role, stg, asp = ruler_of_year(c, nat, muntha)
        h = T.house(c, r)
        d = s.date().isoformat()
        why = f"{r} ({role}), strength {stg}, house {h}"
        good = r in T.benefics(c) and h in (1, 4, 7, 10, 5, 9, 11)
        bad = stg < 5 and h in (6, 8, 12)
        rows["T4 ruler of the year: benefic in an angle, trine or 11th = good year; weak in 6th/8th/12th = evil year"].append(("Bullish" if good else "Bearish" if bad else None, ret, d, why))
        mg = r in ("Sun", "Mars", "Saturn") and stg > 10 and h in (3, 6, 11)
        mb = r in ("Sun", "Mars", "Saturn") and h in (8, 12)
        rows["T4 malefic ruler of the year strong in the 3rd/6th/11th = good; ruler in the 8th/12th = no good"].append(("Bullish" if mg else "Bearish" if (mb or (h in (8, 12))) else None, ret, d, why))
        rows["T4 Jupiter, Venus or Mercury as ruler of the year with strength (>10): great gain of wealth"].append(("Bullish" if r in ("Jupiter", "Venus", "Mercury") and stg > 10 else None, ret, d, why))
        cr = T.combust(c, r) or (r not in ("Sun", "Moon") and c["p"][r][2] < 0)
        rows["T4 ruler of the year combust or retrograde: loss of wealth in every undertaking"].append(("Bearish" if cr else None, ret, d, why))
        t6 = r == "Mercury" and h in (2, 11) and T.influence(c, T.sgn(c, "Mercury"), T.tajika_aspects_sign, nodes=False)[0]
        rows["T6 Mercury as ruler of the year in the 2nd or 11th aspected by benefics: gain from trade"].append(("Bullish" if t6 else None, ret, d, why))
    # T10 substance strength in the Aries-ingress chart (location-free: dignities only)
    gm = {r["Date"]: float(r["Price"]) for r in csv.DictReader(open(T.BT / "gold_monthly_1833.csv"))}
    gd, gc = T.load_px("gold_GC_F_daily_2000.csv")
    sd, sc = T.load_px("silver_SI_F_daily_2000.csv")
    ing = T.sun_at(0.0, dt.datetime(1972, 1, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC))
    for s, e in zip(ing, ing[1:]):
        c = T.chart(s, T.NYC)
        d = s.date().isoformat()
        if s.year >= 2001:
            rg = T.year_ret(gd, gc, s, e, ET, dt.time(13, 30))
        else:
            k0, k1 = f"{s.year}-{s.month:02d}", f"{e.year}-{e.month:02d}"
            rg = (gm[k1] / gm[k0] - 1) * 100 if k0 in gm and k1 in gm else None
        rs = T.year_ret(sd, sc, s, e, ET, dt.time(13, 25)) if s.year >= 2001 else None
        for metal, p, ret in (("gold", "Mercury", rg), ("gold", "Sun", rg), ("silver", "Venus", rs), ("silver", "Moon", rs)):
            stg = tajika_strength(c, p)
            tone = "Bullish" if stg > 10 else "Bearish" if stg < 5 else None
            rows[f"T10 {metal}: {p} strong (>10) in the Aries-ingress chart = gain, weak (<5) = loss"].append((tone, ret, d, f"{p} {stg}"))
    out = []
    for name, rr in rows.items():
        mname = "Gold 1972-2026" if " gold:" in name else "Silver 2001-2026" if " silver:" in name else "S&P 500 (1929-2026)"
        out.append(dict(name=name, market=mname, cmp=T.annual_compare([(t, r, d) for t, r, d, _ in rr], "1999-04-01" if "Gold" in mname else "2013-11-20" if "Silver" in mname else "1977-11-20"),
                        years=[dict(start=d, tone=t, ret=round(r, 2) if r is not None else None, why=w) for t, r, d, w in rr]))
    return out


# ------------------------------------------------------------------ calendar layer, 24 Nov - 31 Dec 2026
def calendar_layer(verdicts, a=None, b=None):
    a = a or dt.datetime(2026, 11, 24, 5, tzinfo=UTC)
    b = b or dt.datetime(2027, 1, 1, 5, tzinfo=UTC)
    items = []

    def add(kind, start, end, text, rule):
        items.append(dict(kind=kind, start=start.astimezone(ET).isoformat(), end=(end or start).astimezone(ET).isoformat(), text=text, rule=rule,
                          verdict=verdicts.get(rule, "not tested")))
    for pl, t, n in T.moon_passes(a, b):
        add("instant", t, None, f"Moon passes {'north' if n else 'south'} of {pl}", "B1")
    for t, k in T.mercury_reappear(a, b):
        add("instant", t, None, f"Mercury reappears from the Sun ({k})", "B2")
    for t, k, n in venus_phases(a, b):
        add("instant", t, None, f"Venus {k} in {T.NAKS[n]} ({'northern' if n in NORTH else 'middle' if n in MIDDLE else 'southern'} path)", "B5")
    for t, wn, ls in wars(a, b):
        add("instant", t, None, f"Planetary war: {wn} beats {ls}", "B7")
    for planet, rule, sets in (("Mercury", "B3", {"bear": ("Bearish", {"Ashwini", "Shatabhisha", "Mula", "Revati"}), "bull": ("Bullish", {"Swati", "Bharani", "Rohini", "Krittika"})}),
                               ("Mars", "B4", {"bull": ("Bullish", {"Shravana", "Magha", "Punarvasu", "Hasta", "Mula", "Purva Bhadrapada", "Ashwini", "Vishakha", "Rohini"})}),
                               ("Venus", "B5s", {"sw": ("Bearish", {"Swati"})})):
        for lab, evs in T.nak_windows(planet, sets, a - dt.timedelta(days=40), b).items():
            for e in evs:
                s, en = dt.datetime.fromisoformat(e["start"]), dt.datetime.fromisoformat(e["end"])
                if en > a:
                    nk = T.NAKS[int(T.pos(T.jd(max(s, a) + dt.timedelta(hours=1)), planet)[0] // (360 / 27))]
                    add("span", max(s, a), min(en, b), f"{planet} in {nk} ({e['tone'].lower()} per BS)", rule)
    mt = meetings(a - dt.timedelta(days=60), b)
    for k, rule, txt in (("kosha", "B9k", "Kosha meeting"), ("sammoha", "B9s", "Sammoha meeting"), ("five", "B10f", "5+ planets in one sign")):
        for s, e in mt[k]:
            if e > a:
                add("span", max(s, a), min(e, b), txt, rule)
    bs = b10_spans(a - dt.timedelta(days=400), b)
    for k, rule, txt in (("satrahu", "B10sr", "Saturn and Rahu in one sign"), ("retro_any", "B10r", "Mars or Saturn retrograde in Cancer, Leo or Pisces"),
                         ("triple", "B10t", "Saturn, Mars and Jupiter in mutual aspect"), ("sun_end", "B10e", "Sun at the end of a sign with Jupiter and Mars")):
        for s, e in bs[k]:
            if e > a:
                add("span", max(s, a), min(e, b), txt, rule)
    for s, e, v in sun_with(a - dt.timedelta(days=40), b):
        if v and e > a:
            add("span", max(s, a), min(e, b), {"sco": "Sun in Scorpio with malefics in the 6th and 7th", "winter_ben": "Sun in Sag/Cap/Aqu with benefics",
                                               "winter_mal": "Sun in Sag/Cap/Aqu with malefics"}[v], {"sco": "B13s", "winter_ben": "B13b", "winter_mal": "B13m"}[v])
    nm = T.lunations(a - dt.timedelta(days=31), b + dt.timedelta(days=31))
    for s, e in zip(nm, nm[1:]):
        if e > a and s < b:
            for tz, mk in ((ET, "US"), (IST, "India")):
                add("span", max(s, a), min(e, b), f"Lord of the lunar month ({mk} time): {T.hindu_weekday(s, tz)}", "B8m")
    ch = T.chaitra_starts(dt.datetime(2026, 2, 15, tzinfo=UTC), dt.datetime(2026, 4, 30, tzinfo=UTC))[0]
    nat = T.nyse_natal()
    yr = T.annual_returns(nat, dt.datetime(2026, 1, 1, tzinfo=UTC), dt.datetime(2026, 12, 31, tzinfo=UTC))[0]
    c = T.chart(yr, T.NYC)
    r, role, stg, _ = ruler_of_year(c, nat, (nat["a"] + yr.year - 1792) % 12)
    year = dict(lord_of_year_us=T.hindu_weekday(ch, ET), lord_of_year_india=T.hindu_weekday(ch, IST), chaitra=ch.date().isoformat(),
                nyse_return=yr.astimezone(ET).strftime("%Y-%m-%d %H:%M ET"), ruler=r, ruler_role=role, ruler_strength=stg, ruler_house=T.house(c, r),
                muntha_house=((nat["a"] + yr.year - 1792) % 12 - c["a"]) % 12 + 1)
    mr = [t for t in T.monthly_returns(nat, a - dt.timedelta(days=31), b)]
    months = []
    for s in mr:
        cm = T.chart(s, T.NYC)
        months.append(dict(start=s.astimezone(ET).strftime("%Y-%m-%d %H:%M ET"), t8a=T.navamsa_rule(cm, 2), t8b=T.navamsa_rule(cm, 11),
                           sahams={k: T.saham_tone(cm, v) for k, v in T.sahams(cm).items()}, sun_house=T.house(cm, "Sun")))
    return dict(items=items, year=year, months=months)


VERDICTS = {
    "B1": "tested: at chance", "B2": "tested: no extra volatility", "B3": "tested: at chance", "B4": "tested: at chance",
    "B5": "tested (see report)", "B5s": "tested (see report)", "B7": "tested (see report)", "B9k": "tested (see report)", "B9s": "tested (see report)",
    "B10f": "tested (see report)", "B10sr": "tested (see report)", "B10r": "tested (see report)", "B10t": "tested (see report)", "B10e": "tested (see report)",
    "B13s": "tested (see report)", "B13b": "tested (see report)", "B13m": "tested (see report)", "B8m": "tested: at chance",
}
RULE_TEST = {"B5": "B5 Venus disappears or reappears in the northern path", "B5s": "B5 Venus in Swati", "B7": "B7 planetary war: Mercury beaten",
             "B9k": "B9 Kosha", "B9s": "B9 Sammoha", "B10f": "B10 five or more", "B10sr": "B10 Saturn and Rahu in one sign: drought",
             "B10r": "B10 Mars or Saturn retrograde", "B10t": "B10 Saturn, Mars and Jupiter", "B10e": "B10 Sun at the end",
             "B13s": "B13 Sun in Scorpio", "B13b": "B13 Sun in Sag/Cap/Aqu with benefics", "B13m": "B13 Sun in Sag/Cap/Aqu with malefics"}


def verdict_of(t):
    """One-line verdict of a test over its markets."""
    if t.get("vol"):
        return "no extra volatility"
    good = [k for k, r in t["by"].items() if r.get("q") is not None and r["q"] < 0.10 and r["hit_rate"] > r["base_rate"]]
    nom = [k for k, r in t["by"].items() if r.get("p_value") is not None and r["p_value"] < 0.05 and r["hit_rate"] is not None and r["hit_rate"] > r["base_rate"]]
    dec = sum(r["worked"] + r["failed"] for r in t["by"].values())
    if good:
        return "holds (q < 0.10): " + ", ".join(good)
    if dec < 10:
        return "too few cases"
    if nom:
        return "nominal p < 0.05 only (" + ", ".join(nom) + "), not significant after correction"
    return "at chance"


def main():
    MK = T.markets()
    MK28 = T.Mkt("spx1928", "S&P 500 (1928-)", "spx_GSPC_daily_1928.csv", ET, dt.time(16, 0), p0=dt.date(1928, 11, 20), p1=dt.date(2026, 11, 20))
    res = dict(made=dt.datetime.now(ET).strftime("%Y-%m-%d %H:%M ET"))
    print("daily")
    res["daily"], res["counts"] = daily_tests(MK, MK28)
    for k in ("spx", "sensex", "gold", "silver", "spx1928"):
        items = [(t, t["by"][k]) for t in res["daily"] if k in t["by"] and t["by"][k].get("p_value") is not None and (t["by"][k]["worked"] + t["by"][k]["failed"]) >= 10]
        for (t, r), q in zip(items, BM.bh([r["p_value"] for _, r in items]) if items else []):
            r["q"] = round(q, 4)
    print("annual")
    res["annual"] = annual_tests()
    items = [v for t in res["annual"] for v in t["cmp"].values() if v.get("p_value") is not None]
    for v, q in zip(items, BM.bh([v["p_value"] for v in items])):
        v["q"] = round(q, 4)
    for t in res["daily"]:
        t["verdict"] = verdict_of(t)
    vd = dict(VERDICTS)
    for key, prefix in RULE_TEST.items():
        m = [t for t in res["daily"] if t["name"].startswith(prefix)]
        if m:
            vd[key] = "tested: " + m[0]["verdict"]
    print("calendar")
    res["calendar"] = calendar_layer(vd)
    (OUT / "new_sources_leftover_ET.json").write_text(json.dumps(res, indent=1, default=str))
    write(res)
    for t in res["daily"]:
        print(t["name"][:95], "|", t["verdict"])
        for k, r in t["by"].items():
            print("   ", k, f"n={r['n']} w={r['worked']} f={r['failed']} hit={r['hit_rate']} base={r['base_rate']} avg={r['avg_dir_ret']} p={r['p_value']} q={r.get('q')} {r['verdict']} halves={r.get('halves')}")
    for t in res["annual"]:
        print(t["market"], "|", t["name"][:90], "|", t["cmp"])
    print(res["calendar"]["year"])
    print(res["counts"])


def write(res):
    k4 = ["spx", "sensex", "gold", "silver"]
    daily = [t for t in res["daily"] if "spx1928" not in t["by"]]
    sat = [t for t in res["daily"] if "spx1928" in t["by"]]
    ann = []
    for t in res["annual"]:
        c = t["cmp"]
        cs = "<br>".join((f"<b>{tone}</b>: {v['right']}/{v['n']} right; {v['note']}" if v.get("note") else
                          f"<b>{tone}</b>: {v['right']}/{v['n']} right = {v['hit']}% vs {v['base']}% in the other years; mean {v['mean']:+.1f}% vs {(v['mean_other'] or 0):+.1f}%; p {v['p_value']}, q {v.get('q')}; halves {' / '.join(v.get('halves', []))}") for tone, v in c.items()) or "no case"
        good = any(v.get("p_value") is not None and v.get("q", 1) < 0.10 and v["hit"] > v["base"] for v in c.values())
        yr = "".join(f"<tr><td>{y['start']}</td><td>{y['tone'] or '–'}</td><td class='n'>{y['ret'] if y['ret'] is not None else '–'}</td><td class='m'>{html.escape(str(y['why']))}</td></tr>" for y in t["years"])
        ann.append(f"<tr><td>{html.escape(t['name'])}</td><td>{t['market']}</td><td class='{'ok' if good else ''}'>{cs}<details><summary>years</summary><table>{yr}</table></details></td></tr>")
    hold = [t["name"] for t in res["daily"] if t["verdict"].startswith("holds")] + [t["name"] for t in res["annual"] if any(v.get("p_value") is not None and v.get("q", 1) < 0.10 and v["hit"] > v["base"] for v in t["cmp"].values())]
    nom = [f"{t['name']} — {t['verdict']}" for t in res["daily"] if t["verdict"].startswith("nominal")]
    anom = [f"{t['name']} ({t['market']}, {tone}): {v['right']}/{v['n']} = {v['hit']}% vs {v['base']}%, p {v['p_value']}, q {v.get('q')}" for t in res["annual"] for tone, v in t["cmp"].items() if v.get("p_value") is not None and v["p_value"] < 0.05 and v["hit"] > v["base"]]
    y = res["calendar"]["year"]
    cnt = res["counts"]
    verdict = (f"<b>Verdict: {'no leftover rule holds' if not hold else str(len(hold)) + ' rule(s) hold: ' + html.escape('; '.join(hold))}.</b> "
               f"{len(res['daily'])} daily or window rules and {len(res['annual'])} annual rules were scored, with Benjamini–Hochberg correction within this set. "
               + ("Nothing new is added to the signals; the calendar shows these rules as information, each with its test result."
                  if not hold else "")
               + "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in nom + anom) + "</ul>")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Leftover Rules Backtest</title><style>{T.CSS}</style></head><body>
<h1>The leftover rules from the three new books</h1>
<p class="m">Made {res['made']}. These are the rules <code>new_sources_test_ET.html</code> did not cover, tested with the same method (PROJECT_KNOWLEDGE §6): daily and window rules on the S&P 500, Sensex, gold and silver, 20 Nov 2000 – 20 Nov 2026; the Saturn nakshatra rules on the S&P 500 1928–2026; annual rules against the other years. Sidereal Lahiri, mean node. Green: q &lt; 0.10, or p &lt; 0.05 with the hit rate above the base.</p>
<div class="box">{verdict}</div>
<h2>Daily and window rules (B5, B7, B9, B10, B11, B13)</h2>
<p class="m">2000–2026 counts: {cnt['venus']} Venus disappearances or reappearances, {cnt['wars']} planetary wars within 1°, {cnt['kosha']} Kosha meetings, {cnt['sammoha']} Sammoha meetings, {cnt['five']} spans with 5+ planets in one sign, {cnt['eclipses']} eclipses. A planetary war is scored at the exact conjunction; the loser is the planet with the lower (southern) latitude (BS 17). B13 compares opposite readings: BS 40.14 says benefics with the Sun in Sagittarius, Capricorn or Aquarius make prices "moderate or rise", while Nilakanthi 36 says they make grain cheap. Gold and silver stand in for commodities, and this is our substitution: both texts speak of grain.</p>
{T.table(daily, k4)}
<details><summary>Planetary wars found</summary><p class="m">{html.escape('; '.join(cnt['wars_list']))}</p></details>
<h2>Saturn in the stated nakshatras, S&amp;P 500 1928–2026 (B6)</h2>
{T.table(sat, ['spx1928'])}
<h2>Annual rules: ruler of the year (T4, T6) and the substance rule (T10)</h2>
<p class="m">Tajika five-dignity strength (Hayanaratna 2.5): domicile, haddā, decan and navamsha points in the friend/enemy scheme (Paddhatibhūṣaṇa 30, Tājikasāra 74–75), with Tajika constant friends (Sun, Moon, Mars, Jupiter vs Mercury, Venus, Saturn), plus Vāmana's exaltation strength. The total is divided by 4: above 10 is strong, below 5 weak. The ruler of the year is the strongest of the five candidates that aspects the annual ascendant; if none does, the annual ascendant lord. T10 uses the Aries-ingress chart for the world year. Gold before 2001 uses monthly prices.</p>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Market</th><th>Result</th></tr></thead><tbody>{''.join(ann)}</tbody></table></div>
<h2>Not tested</h2><ul class="m"><li><b>N7, N8 (horary price and buy/sell questions):</b> they need the moment a question is asked. Using the market's opening chart instead would be our invention, not the source's (CLAUDE.md: no extrapolation).</li>
<li><b>N9 (crops by direction):</b> regional, with no market to score.</li><li><b>T11 (annual dashas):</b> dashas are parked (user, 24 Nov 2026).</li>
<li><b>B4 Mars south of Rohini:</b> Mars never passed Aldebaran south of its latitude in 2000–2026.</li></ul>
<h2>Now: the current year</h2>
<p>Lord of the year 2026–27 (Chaitra new moon {y['chaitra']}): <b>{y['lord_of_year_us']}</b> by US time, <b>{y['lord_of_year_india']}</b> by Indian time (watch list only). NYSE annual return {y['nyse_return']}: the ruler of the year is <b>{y['ruler']}</b> ({y['ruler_role']}), strength {y['ruler_strength']}, in house {y['ruler_house']}. The muntha is in house {y['muntha_house']}.</p>
</body></html>"""
    (OUT / "new_sources_leftover_ET.html").write_text(page)


if __name__ == "__main__":
    main()
