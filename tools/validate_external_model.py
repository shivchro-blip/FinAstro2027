"""Check an outside model's crash table and 2026-2029 roadmap (two infographics shared by the user,
23 Nov 2026) against our ephemeris, our data and our model.

    python tools/validate_external_model.py

Part A  Planet positions: every placement the infographics state for the 11 historical crashes and
        for the 2026-2029 windows, checked with our Swiss Ephemeris setup (sidereal Lahiri, mean
        node, whole-sign). A claim holds if it is true on the reference date, "in window" if it is
        true on some day of the stated window, otherwise wrong.
Part B  Do the "core recurring signatures" predict crashes? Each signature is defined objectively
        and tested on the S&P 500 from 1928 to 2026 (daily closes, ^GSPC): how often it is present
        at all, how often on the crash dates, and what the S&P did in the following 6 months when it
        was present vs absent (monthly samples, two-proportion z-test).
Part C  Their 2026-2029 windows against our model: our signal tables (gold, silver, S&P 500,
        Sensex) and the robust big-move factors (market_summary), day by day, plus what prices
        have done so far.
Writes build/pdfref/external_model_check_ET.{html,json}.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import swisseph as swe  # noqa: E402
from finastro.pdfref.engine import snapshot  # noqa: E402

OUT = ROOT / "build" / "pdfref"
UTC = dt.timezone.utc
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
PL7 = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
_cache = {}


def S(d):
    if d not in _cache:
        _cache[d] = snapshot(dt.datetime(d.year, d.month, d.day, 16, tzinfo=UTC))
    return _cache[d]


def days(a, b):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


# ---------------------------------------------------------------- eclipses
def eclipses(y0=1925, y1=2030):
    out = []
    for kind, fn in (("solar", swe.sol_eclipse_when_glob), ("lunar", swe.lun_eclipse_when)):
        jd = swe.julday(y0, 1, 1)
        end = swe.julday(y1, 1, 1)
        while jd < end:
            res = fn(jd, swe.FLG_SWIEPH)
            t = res[1][0]
            y, m, d, h = swe.revjul(t)
            when = dt.datetime(y, m, d, tzinfo=UTC) + dt.timedelta(hours=h)
            out.append(dict(kind=kind, when=when, date=when.date(), sun=S(when.date())["Sun"].sign, moon=S(when.date())["Moon"].sign))
            jd = t + 20
    return sorted(out, key=lambda e: e["when"])


ECL = None


def eclipse_near(d, sign=None, kind=None, tol=2):
    for e in ECL:
        if abs((e["date"] - d).days) <= tol and (kind is None or e["kind"] == kind) and (sign is None or e["sun"] == sign):
            return e
    return None


# ---------------------------------------------------------------- predicates
def in_(p, sign):
    return lambda d: S(d)[p].sign == sign


def R(p):
    return lambda d: S(d)[p].retro


def with_(p, q):
    return lambda d: S(d)[p].sign_i == S(d)[q].sign_i


def opp(p, q):
    return lambda d: (S(d)[p].sign_i - S(d)[q].sign_i) % 12 == 6


def nak(p, name):
    return lambda d: S(d)[p].nak == name


def all_(*fs):
    return lambda d: all(f(d) for f in fs)


def any_(*fs):
    return lambda d: any(f(d) for f in fs)


def gandanta_aries(p):
    return lambda d: (S(d)[p].lon % 360) < 3.3334 or (S(d)[p].lon % 360) > 356.6666


def node_29():
    return lambda d: (S(d)["Rahu"].lon % 30) >= 28.0


def node_sandhi():
    return lambda d: (S(d)["Rahu"].lon % 30) >= 29.0 or (S(d)["Rahu"].lon % 30) <= 1.0


def combust(p, orb=11):
    return lambda d: min((S(d)[p].lon - S(d)["Sun"].lon) % 360, (S(d)["Sun"].lon - S(d)[p].lon) % 360) <= orb


def kala_sarpa():
    def f(d):
        s = S(d)
        r = s["Rahu"].lon
        side = [((s[p].lon - r) % 360) < 180 for p in PL7]
        return all(side) or not any(side)
    return f


def stellium(sign, n):
    return lambda d: sum(1 for p in PL7 + ("Rahu", "Ketu") if S(d)[p].sign == sign) >= n


def ecl(sign, kind="solar", date=None):
    return lambda d: eclipse_near(date or d, sign, kind, tol=1) is not None


NEECHA = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"}


def neecha(p):
    return in_(p, NEECHA[p])


def fixed(fn):
    """A claim about one dated event (an eclipse, a count): fn() -> (status, note)."""
    fn.fixed = True
    return fn


def ecl_claim(date, sign=None, kind="solar"):
    def fn():
        e = eclipse_near(date, None, kind, tol=1)
        if not e:
            return "wrong", f"no {kind} eclipse within a day of {date}"
        ok = sign is None or e["sun"] == sign
        return ("holds" if ok else "wrong"), f"{kind} eclipse {e['date']}, Sun in {e['sun']} (sidereal)"
    return fixed(fn)


def stell_claim(sign, n, a, b):
    def fn():
        best = max(((sum(1 for p in PL7 + ("Rahu", "Ketu") if S(d)[p].sign == sign), d) for d in days(a, b)), key=lambda z: z[0])
        st = "holds" if best[0] >= n else ("in window" if best[0] >= n - 1 else "wrong")
        return st, f"most bodies in {sign}: {best[0]} on {best[1]} (Sun..Saturn, Moon and nodes, sidereal)"
    return fixed(fn)


D = dt.date
CRASHES = [
    ("1929 Wall Street", D(1929, 10, 29), D(1929, 9, 3), D(1932, 7, 8), [
        ("Sun neecha (Libra)", neecha("Sun")), ("Venus neecha (Virgo)", neecha("Venus")), ("Mars and Ketu in Libra", all_(in_("Mars", "Libra"), in_("Ketu", "Libra"))),
        ("Saturn in Mula", nak("Saturn", "Mula")), ("1 Nov 1929 solar eclipse", ecl_claim(D(1929, 11, 1)))]),
    ("1937-38 recession", D(1937, 10, 19), D(1937, 3, 6), D(1938, 3, 31), [
        ("Saturn retrograde in Pisces", all_(in_("Saturn", "Pisces"), R("Saturn"))), ("Mars and Rahu in Scorpio", all_(in_("Mars", "Scorpio"), in_("Rahu", "Scorpio"))),
        ("Jupiter (in)to Capricorn", in_("Jupiter", "Capricorn"))]),
    ("1973-74 oil crisis", D(1973, 10, 17), D(1973, 1, 11), D(1974, 10, 3), [
        ("Saturn and Ketu in Ardra", all_(nak("Saturn", "Ardra"), nak("Ketu", "Ardra"))), ("Jupiter neecha", neecha("Jupiter")), ("Sun neecha", neecha("Sun")),
        ("Mars retrograde in Aries", all_(in_("Mars", "Aries"), R("Mars"))), ("Gemini solar eclipse (30 Jun 1973, ~7 min)", ecl_claim(D(1973, 6, 30), "Gemini"))]),
    ("1987 Black Monday", D(1987, 10, 19), D(1987, 8, 25), D(1987, 12, 4), [
        ("Jupiter retrograde at 0° Aries (gandanta)", all_(R("Jupiter"), gandanta_aries("Jupiter"))), ("Mars and Ketu in Virgo", all_(in_("Mars", "Virgo"), in_("Ketu", "Virgo"))),
        ("Mercury retrograde", R("Mercury")), ("Virgo solar eclipse 23 Sep 1987", ecl_claim(D(1987, 9, 23), "Virgo"))]),
    ("1990 Japan bubble", D(1990, 1, 2), D(1989, 12, 29), D(1992, 8, 18), [
        ("Rahu in Capricorn", in_("Rahu", "Capricorn")), ("Ketu and Jupiter in Cancer", all_(in_("Ketu", "Cancer"), in_("Jupiter", "Cancer"))),
        ("Saturn opposite Jupiter", opp("Saturn", "Jupiter")), ("Cancer solar eclipse 22 Jul 1990", ecl_claim(D(1990, 7, 22), "Cancer"))]),
    ("1997 Asian crisis", D(1997, 10, 27), D(1997, 7, 2), D(1998, 10, 8), [
        ("Jupiter retrograde neecha (Capricorn)", all_(neecha("Jupiter"), R("Jupiter"))), ("Saturn Pisces to Aries", any_(in_("Saturn", "Pisces"), in_("Saturn", "Aries"))),
        ("Nodes at 29°", node_29()), ("Mars opposite Saturn", opp("Mars", "Saturn"))]),
    ("2000-02 dot-com", D(2000, 4, 14), D(2000, 3, 10), D(2002, 10, 9), [
        ("Saturn neecha (Aries)", neecha("Saturn")), ("Jupiter in Ashwini", nak("Jupiter", "Ashwini")), ("Saturn and Rahu in Taurus", all_(in_("Saturn", "Taurus"), in_("Rahu", "Taurus"))),
        ("7-planet Aries stellium", stell_claim("Aries", 7, D(2000, 3, 10), D(2000, 6, 30)))]),
    ("2008 global crisis", D(2008, 9, 15), D(2007, 10, 9), D(2009, 3, 9), [
        ("Rahu Capricorn / Ketu Cancer", all_(in_("Rahu", "Capricorn"), in_("Ketu", "Cancer"))), ("Saturn and Sun in Leo", all_(in_("Saturn", "Leo"), in_("Sun", "Leo"))),
        ("Jupiter (in)to neecha (Capricorn)", neecha("Jupiter")), ("Cancer solar eclipse 1 Aug 2008", ecl_claim(D(2008, 8, 1), "Cancer"))]),
    ("2020 COVID crash", D(2020, 3, 16), D(2020, 2, 19), D(2020, 3, 23), [
        ("Saturn, Mars and Jupiter in Capricorn (Jupiter neecha) – true only from 30 Mar 2020, after the 23 Mar low", all_(in_("Saturn", "Capricorn"), in_("Mars", "Capricorn"), in_("Jupiter", "Capricorn"))),
        ("Rahu in Ardra", nak("Rahu", "Ardra")), ("Kala Sarpa", kala_sarpa()),
        ("6-planet Sagittarius solar eclipse (26 Dec 2019)", stell_claim("Sagittarius", 6, D(2019, 12, 25), D(2019, 12, 27)))]),
    ("2022 rates and crypto", D(2022, 6, 13), D(2022, 1, 3), D(2022, 10, 12), [
        ("Saturn retrograde in Capricorn", all_(in_("Saturn", "Capricorn"), R("Saturn"))), ("Mars and Rahu in Aries", all_(in_("Mars", "Aries"), in_("Rahu", "Aries"))),
        ("Kala Sarpa", kala_sarpa()),
        ("4 Aries-Libra eclipses in 2022", fixed(lambda: (lambda n: ("holds" if n >= 4 else "in window" if n == 3 else "wrong", f"{n} of the 2022 eclipses fall in sidereal Aries / Libra: " + ", ".join(f"{e['date']} {e['kind']} (Sun {e['sun']})" for e in ECL if e["date"].year == 2022)))(sum(1 for e in ECL if e["date"].year == 2022 and (e["sun"] in ("Aries", "Libra") or e["moon"] in ("Aries", "Libra"))))))]),
    ("2025 tariff shock", D(2025, 4, 7), D(2025, 2, 19), D(2025, 4, 8), [
        ("Saturn and Rahu in Pisces", all_(in_("Saturn", "Pisces"), in_("Rahu", "Pisces"))), ("Mars neecha (Cancer)", neecha("Mars")),
        ("Mercury and Venus retrograde", all_(R("Mercury"), R("Venus"))),
        ("6-planet Pisces solar eclipse (29 Mar 2025)", stell_claim("Pisces", 6, D(2025, 3, 28), D(2025, 3, 30)))]),
]

FORWARD = [
    ("Nov 2026 (Act I crack)", D(2026, 11, 1), D(2026, 12, 15), [
        ("Jupiter, Mars and Ketu in Magha", all_(nak("Jupiter", "Magha"), nak("Mars", "Magha"), nak("Ketu", "Magha"))),
        ("Jupiter, Mars and Ketu together in Leo", all_(in_("Jupiter", "Leo"), in_("Mars", "Leo"), in_("Ketu", "Leo"))),
        ("Nodes at 0° (sandhi)", node_sandhi()), ("Venus neecha (Virgo)", neecha("Venus")), ("Rahu enters Capricorn (in November)", fixed(lambda: ("in window", "mean node (our convention) enters Capricorn 5 Dec 2026; the true node enters about 25 Nov 2026")))]),
    ("Feb-Apr 2027 (Tremor)", D(2027, 2, 1), D(2027, 4, 30), [
        ("Mars retrograde neecha in Cancer with Ketu", all_(in_("Mars", "Cancer"), R("Mars"), in_("Ketu", "Cancer"))),
        ("Mercury retrograde in Capricorn", all_(in_("Mercury", "Capricorn"), R("Mercury"))),
        ("6 Feb 2027 solar eclipse in Capricorn", ecl_claim(D(2027, 2, 6), "Capricorn")),
        ("Jupiter exalted in Cancer (Feb-Jun)", in_("Jupiter", "Cancer"))]),
    ("Aug-Oct 2027 (Fracture)", D(2027, 8, 1), D(2027, 10, 31), [
        ("Saturn neecha in Aries", neecha("Saturn")), ("Saturn's 10th aspect on Rahu in Capricorn", all_(in_("Saturn", "Aries"), in_("Rahu", "Capricorn"))),
        ("Sun neecha (Libra)", neecha("Sun")), ("2 Aug 2027 total solar eclipse (on India's Moon sign, Cancer)", ecl_claim(D(2027, 8, 2), "Cancer"))]),
    ("Jan-May 2028 (Apex)", D(2028, 1, 1), D(2028, 5, 31), [
        ("Jupiter retrograde in Virgo", all_(in_("Jupiter", "Virgo"), R("Jupiter"))), ("Mars and Rahu in Capricorn", all_(in_("Mars", "Capricorn"), in_("Rahu", "Capricorn"))),
        ("Mars and Saturn in Aries", all_(in_("Mars", "Aries"), in_("Saturn", "Aries"))),
        ("26 Jan 2028 eclipse", ecl_claim(D(2028, 1, 26))), ("Node sandhi in January", fixed(lambda: ("wrong", "Rahu is near 8° Capricorn in January 2028 (mean and true node); no sign boundary")))]),
    ("Aug-Oct 2028 (Washout)", D(2028, 8, 1), D(2028, 10, 31), [
        ("Saturn retrograde neecha in Aries", all_(neecha("Saturn"), R("Saturn"))), ("Jupiter combust in Virgo", all_(in_("Jupiter", "Virgo"), combust("Jupiter"))),
        ("Ketu in Gemini", in_("Ketu", "Gemini")), ("22 Jul 2028 solar eclipse", ecl_claim(D(2028, 7, 22)))]),
    ("Mar 2029 onward", D(2029, 3, 1), D(2029, 4, 30), [("Jupiter in Libra", in_("Jupiter", "Libra"))]),
]


def check(claims, ref, a, b):
    out = []
    for label, f in claims:
        if getattr(f, "fixed", False):
            st, note = f()
            out.append(dict(claim=label, on_ref=None, in_window=st != "wrong", first=None, last=None, status=st, note=note))
            continue
        on = bool(f(ref)) if ref else None
        hit = [d for d in days(a, b) if f(d)]
        out.append(dict(claim=label, on_ref=on, in_window=bool(hit), first=str(hit[0]) if hit else None, last=str(hit[-1]) if hit else None,
                        status="holds" if on else ("in window" if hit else "wrong"), note=""))
    return out


def india_dasha():
    """Vimshottari from the 15 Aug 1947 00:00 IST Delhi chart (Moon)."""
    t = dt.datetime(1947, 8, 14, 18, 30, tzinfo=UTC)
    from finastro.pdfref.engine import snapshot as snap
    m = snap(t)["Moon"].lon % 360
    lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    years = dict(Ketu=7, Venus=20, Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16, Saturn=19, Mercury=17)
    span = 360 / 27
    ni = int(m // span)
    frac = (m % span) / span
    lord = lords[ni % 9]
    start = t - dt.timedelta(days=frac * years[lord] * 365.25)
    seq = []
    i = ni % 9
    s = start
    while s.year < 2040:
        L = lords[i % 9]
        e = s + dt.timedelta(days=years[L] * 365.25)
        seq.append((L, s.date(), e.date()))
        s, i = e, i + 1
    sub = []
    for L, a, b in seq:
        if L != "Mars":
            continue
        i0 = lords.index(L)
        x = dt.datetime.combine(a, dt.time(0))
        for j in range(9):
            Lj = lords[(i0 + j) % 9]
            e = x + dt.timedelta(days=years[L] * years[Lj] / 120 * 365.25)
            sub.append((f"Mars-{Lj}", str(x.date()), str(e.date())))
            x = e
    return dict(moon=f"{snap(t)['Moon'].sign} / {snap(t)['Moon'].nak}", seq=[(L, str(a), str(b)) for L, a, b in seq if b.year >= 2000], mars_sub=sub)


# ---------------------------------------------------------------- Part B
SIGS = {
    "Jupiter weak (neecha in Capricorn, retrograde or combust)": lambda d: neecha("Jupiter")(d) or R("Jupiter")(d) or combust("Jupiter")(d),
    "Mars trigger (Mars with or opposite Saturn / Rahu / Ketu, retrograde, or neecha)": lambda d: any(with_("Mars", q)(d) or opp("Mars", q)(d) for q in ("Saturn", "Rahu")) or R("Mars")(d) or neecha("Mars")(d),
    "Eclipse within ±15 days, or a 4-planet stellium": lambda d: eclipse_near(d, tol=15) is not None or any(stellium(s, 4)(d) for s in SIGNS),
    "Saturn with or opposite the nodes, or Saturn in Pisces / Aries": lambda d: with_("Saturn", "Rahu")(d) or opp("Saturn", "Rahu")(d) or in_("Saturn", "Pisces")(d) or in_("Saturn", "Aries")(d),
    "Rahu in Capricorn": in_("Rahu", "Capricorn"),
    "Kala Sarpa": kala_sarpa(),
}


def part_b():
    rows = list(csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv")))
    Dd = [dt.date.fromisoformat(r["date"]) for r in rows]
    C = [float(r["close"]) for r in rows]
    n = len([d for d in Dd if d <= D(2026, 11, 20)])
    Dd, C = Dd[:n], C[:n]
    runmax, dd = 0, []
    for c in C:
        runmax = max(runmax, c)
        dd.append(c / runmax - 1)
    H = 126
    res = {}
    sample = list(range(0, n - H, 21))                       # monthly samples, about 1,170
    pres = {k: [] for k in SIGS}
    for i in range(n):
        for k, f in SIGS.items():
            pres[k].append(f(Dd[i]))
    count = [sum(pres[k][i] for k in SIGS) for i in range(n)]
    for k in list(SIGS) + ["4 or more of the 6 at once"]:
        P = pres[k] if k in SIGS else [x >= 4 for x in count]
        share = sum(P) / n

        def stats(idx):
            fw = [(C[i + H] / C[i] - 1) for i in idx]
            mdd = [min(C[i:i + H + 1]) / C[i] - 1 for i in idx]
            return dict(n=len(idx), neg=sum(x < 0 for x in fw) / len(idx) if idx else None, avg=sum(fw) / len(idx) * 100 if idx else None,
                        dd15=sum(x <= -0.15 for x in mdd) / len(idx) if idx else None)
        on = [i for i in sample if P[i]]
        off = [i for i in sample if not P[i]]
        a, b = stats(on), stats(off)
        z = None
        if on and off:
            p1, p2 = a["dd15"], b["dd15"]
            pp = (p1 * len(on) + p2 * len(off)) / (len(on) + len(off))
            se = math.sqrt(pp * (1 - pp) * (1 / len(on) + 1 / len(off))) or 1
            z = (p1 - p2) / se
        res[k] = dict(share=round(share * 100, 1), on=a, off=b, z_dd15=round(z, 2) if z is not None else None,
                      crash_hits=sum(1 for c in CRASHES if (SIGS[k](c[1]) if k in SIGS else sum(f(c[1]) for f in SIGS.values()) >= 4)),
                      crash_window_hits=sum(1 for c in CRASHES if any((SIGS[k](d) if k in SIGS else sum(f(d) for f in SIGS.values()) >= 4) for d in days(c[2], min(c[3], c[2] + dt.timedelta(days=365))))))
        # chance that a random 12-month window contains the signature at least once
        wins = [i for i in range(0, n - 252, 21)]
        res[k]["random_window_share"] = round(sum(1 for i in wins if any(P[i:i + 252])) / len(wins) * 100, 1)
    bear = sum(1 for x in dd if x <= -0.2) / n
    return res, dict(n=n, start=str(Dd[0]), end=str(Dd[-1]), bear_share=round(bear * 100, 1))


# ---------------------------------------------------------------- Part C
def our_tables():
    def load_rows(path, key=None):
        j = json.load(open(path))
        return j
    out = {}
    g = OUT / "gold_signals_2026-11-22_to_2027-12-31_ET.html"
    out["note"] = str(g.name)
    return out


def window_view(sig_json_rows, a, b):
    """Count weekdays per (signal, strength) inside [a, b] from a list of rows with frm/to/sig/st."""
    c = {}
    for r in sig_json_rows:
        f0, t0 = r["frm"], r["to"]
        for d in days(max(f0, a), min(t0, b)):
            if d.weekday() < 5:
                k = f"{r['sig']} {r['st']}".strip()
                c[k] = c.get(k, 0) + 1
    return c


def load_signal_rows():
    rows = {}
    for k in ("gold", "silver"):
        rows[k] = [dict(frm=dt.date.fromisoformat(r["frm"]), to=dt.date.fromisoformat(r["to"]), sig=r["sig"], st=r["st"])
                   for r in json.load(open(OUT / f"{k}_signals_2026-11-22_to_2027-12-31_ET.json"))]
    m = json.load(open(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json"))
    for k in ("spx", "sensex"):
        rows[k] = [dict(frm=dt.date.fromisoformat(str(r["frm"])[:10]), to=dt.date.fromisoformat(str(r["to"])[:10]), sig=r["sig"], st=r["st"]) for r in m["tables"][k]]
    return rows


ROBUST = {  # whole-sign forms of the robust big-move factors (market_summary_2000-2026_ET.html)
    "spx": {"Venus retrograde": R("Venus"),
            "Jupiter-Pluto 5/9": lambda d: (S(d)["Jupiter"].sign_i - S(d)["Pluto"].sign_i) % 12 in (4, 8),
            "Jupiter-Neptune 7th": opp("Jupiter", "Neptune"),
            "Jupiter-Uranus 6/8": lambda d: (S(d)["Jupiter"].sign_i - S(d)["Uranus"].sign_i) % 12 in (5, 7),
            "Mercury-Saturn 2/12": lambda d: (S(d)["Mercury"].sign_i - S(d)["Saturn"].sign_i) % 12 in (1, 11)},
    "sensex": {"Venus retrograde": R("Venus"), "Mars-Saturn conjunction": with_("Mars", "Saturn"), "Venus in Pisces": in_("Venus", "Pisces"),
               "Mars-Uranus 5/9": lambda d: (S(d)["Mars"].sign_i - S(d)["Uranus"].sign_i) % 12 in (4, 8)},
}

STAGES = [
    ("Nov 2026 (Act I crack)", D(2026, 11, 23), D(2027, 1, 31), "Nasdaq -16 to -20%; gold margin-call floor $3,525-3,700; silver $41-45; Nifty choppy, FII outflows", "down"),
    ("Feb-Apr 2027 (Tremor) / Feb-Jun 2027 roadmap", D(2027, 2, 1), D(2027, 6, 30), "Tech -15 to -25%; gold and silver strong recovery rally; Indian markets outperform and rally", "mixed"),
    ("Aug-Oct 2027 (Fracture) / Aug-Dec 2027 roadmap", D(2027, 8, 1), D(2027, 12, 31), "AI bubble fractures (primary pop); gold surges to $4,650+; silver volatile; India sharp reversal, FII selling", "down"),
    ("Jan-May 2028 (Apex)", D(2028, 1, 1), D(2028, 5, 31), "AI -55 to -78%, S&P -35 to -50%; Nifty -20 to -35%; gold structural breakout", "down"),
    ("Aug-Oct 2028 (Washout)", D(2028, 8, 1), D(2028, 10, 31), "Secular bottom", "bottom"),
]


def main():
    global ECL
    ECL = eclipses()
    A = [dict(crash=c[0], ref=str(c[1]), window=f"{c[2]} – {c[3]}", claims=check(c[4], c[1], c[2], c[3])) for c in CRASHES]
    F = [dict(stage=s[0], window=f"{s[1]} – {s[2]}", claims=check(s[3], None, s[1], s[2])) for s in FORWARD]
    dasha = india_dasha()
    B, Bmeta = part_b()
    sig = load_signal_rows()
    gold = json.load(open(OUT / "gold_outlook_2026-11-22_to_2027-12-31_ET.json"))
    del gold
    stages = []
    for name, a, b, claim, lean in STAGES:
        row = dict(stage=name, window=f"{a} – {b}", claim=claim, lean=lean, ours={}, robust={})
        if a <= D(2027, 12, 31):
            for k in ("spx", "sensex", "gold", "silver"):
                row["ours"][k] = window_view(sig[k], a, min(b, D(2027, 12, 31)))
        for k, fs in ROBUST.items():
            act = {}
            for lab, f in fs.items():
                hit = [d for d in days(a, b) if f(d)]
                if hit:
                    act[lab] = f"{hit[0]} – {hit[-1]} ({len(hit)} days)"
            row["robust"][k] = act
        stages.append(row)
    real = []
    for name, f, since in (("Nasdaq", "nasdaq_IXIC_daily_2000.csv", D(2026, 6, 1)), ("S&P 500", "spx_GSPC_daily_2000.csv", D(2026, 6, 1)),
                           ("BSE Sensex", "sensex_BSESN_daily_2000.csv", D(2026, 6, 1)), ("Gold", "gold_GC_F_daily_2000.csv", D(2026, 6, 1)),
                           ("Silver", "silver_SI_F_daily_2000.csv", D(2026, 6, 1))):
        rr = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / f))]
        rr = [x for x in rr if since <= x[0] <= D(2026, 11, 20)]
        pk = max(rr, key=lambda z: z[1])
        low = min(rr[rr.index(pk):], key=lambda z: z[1])
        real.append(dict(name=name, peak=str(pk[0]), peak_close=round(pk[1], 2), low=str(low[0]), low_close=round(low[1], 2),
                         fall=round((low[1] / pk[1] - 1) * 100, 1), last=str(rr[-1][0]), last_close=round(rr[-1][1], 2)))
    res = dict(A=A, F=F, dasha=dasha, B=B, Bmeta=Bmeta, stages=stages, real=real,
               eclipses=[dict(kind=e["kind"], date=str(e["date"]), sun=e["sun"]) for e in ECL if e["date"].year >= 2026])
    json.dump(res, open(OUT / "external_model_check_ET.json", "w"), indent=1, default=str)
    write(res)
    tot = [c["status"] for x in A for c in x["claims"]]
    print("historical claims:", {s: tot.count(s) for s in set(tot)})
    for x in A:
        print(" ", x["crash"], [(c["claim"], c["status"]) for c in x["claims"]])
    totf = [c["status"] for x in F for c in x["claims"]]
    print("forward claims:", {s: totf.count(s) for s in set(totf)})
    for x in F:
        print(" ", x["stage"], [(c["claim"], c["status"], c["first"], c["last"]) for c in x["claims"]])
    print("dasha", dasha)
    print(Bmeta)
    for k, v in B.items():
        print(f"  {v['share']}% of days; crash dates {v['crash_hits']}/11, crash windows {v['crash_window_hits']}/11, random 12-month window {v['random_window_share']}%;"
              f" 6m dd>=15%: on {v['on']['dd15']:.3f} off {v['off']['dd15']:.3f} z {v['z_dd15']}; 6m ret on {v['on']['avg']:.1f}% off {v['off']['avg']:.1f}%  {k}")
    for s in stages:
        print(s["stage"], s["ours"], s["robust"])


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    mark = {"holds": "✓ holds", "in window": "≈ in window", "wrong": "✗ wrong"}
    cls = {"holds": "bullish", "in window": "mixed", "wrong": "bearish"}

    def claim_rows(items, key):
        out = ""
        for x in items:
            for i, c in enumerate(x["claims"]):
                when = c.get("note") or (f"{c['first']} – {c['last']}" if c["first"] else "never in window")
                out += (f"<tr class='{cls[c['status']]}'>{'<td rowspan=' + str(len(x['claims'])) + '><b>' + html.escape(x[key]) + '</b><div class=s>' + x.get('window', '') + '</div></td>' if i == 0 else ''}"
                        f"<td>{html.escape(c['claim'])}</td><td>{mark[c['status']]}</td><td class='s'>{when}</td></tr>")
        return out
    tot = [c["status"] for x in res["A"] for c in x["claims"]]
    totf = [c["status"] for x in res["F"] for c in x["claims"]]
    brows = "".join(f"<tr><td>{html.escape(k)}</td><td class='n'>{v['share']}%</td><td class='n'>{v['crash_hits']}/11</td><td class='n'>{v['crash_window_hits']}/11</td><td class='n'>{v['random_window_share']}%</td>"
                    f"<td class='n'>{v['on']['dd15'] * 100:.1f}% vs {v['off']['dd15'] * 100:.1f}% (z {v['z_dd15']})</td><td class='n'>{v['on']['avg']:+.1f}% vs {v['off']['avg']:+.1f}%</td></tr>" for k, v in res["B"].items())

    def fmt_counts(c):
        return "; ".join(f"{k}: {v}" for k, v in sorted(c.items(), key=lambda z: -z[1])) or "no signal days"
    srows = ""
    for s in res["stages"]:
        lab = {"spx": "S&P 500", "sensex": "Sensex", "gold": "Gold", "silver": "Silver"}
        ours = "<br>".join(f"<b>{lab[k]}</b>: {html.escape(fmt_counts(v))}" for k, v in s["ours"].items()) or "beyond our tables (end-2027)"
        rob = "<br>".join(f"<b>{'S&P 500' if k == 'spx' else 'Sensex'}</b>: {html.escape('; '.join(f'{a} {b}' for a, b in v.items()) or 'none')}" for k, v in s["robust"].items())
        srows += f"<tr><td><b>{html.escape(s['stage'])}</b></td><td class='s'>{html.escape(s['claim'])}</td><td class='s'>{ours}</td><td class='s'>{rob}</td></tr>"
    dasha = "; ".join(f"{L} {a[:7]} – {b[:7]}" for L, a, b in res["dasha"]["seq"])
    realrows = "".join(f"<tr><td><b>{r['name']}</b></td><td class='n'>{r['peak']} {r['peak_close']:,}</td><td class='n'>{r['low']} {r['low_close']:,}</td>"
                       f"<td class='n'><b>{r['fall']}%</b></td><td class='n'>{r['last_close']:,}</td></tr>" for r in res["real"])
    m = res["Bmeta"]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>External Model Check</title><style>{css}</style></head><body>
<h1>Checking an outside model's crash table and 2026–2029 roadmap against ours</h1>
<p class="m">Two infographics shared on 23 Nov 2026 ("Historical financial crashes &amp; Vedic planetary patterns 1929–2028" and "Cross-asset, gold, US debt &amp; India markets roadmap 2026–2029").
Positions are checked with our ephemeris (sidereal Lahiri, mean node, whole sign). The economic statements (US debt, Fed, DXY) are not astrological and are not checked here.</p>
<h2>Verdict</h2>
<div class="wrap"><table><thead><tr><th>Part of their model</th><th>Our check</th><th>Agreement</th></tr></thead><tbody>
<tr class="bullish"><td>Planet positions at the 11 historical crashes</td><td>{tot.count('holds')} of {len(tot)} hold on the crash date, {tot.count('in window')} somewhere in the crash window, {tot.count('wrong')} wrong (Jupiter only reached Capricorn on 30 Mar 2020, after the COVID low)</td><td>High: the astronomy is right</td></tr>
<tr class="bullish"><td>Planet positions and eclipses for 2026–2029, India dashas</td><td>{totf.count('holds') + totf.count('in window')} of {len(totf)} hold in the stated window; Rahu enters Capricorn 25 Nov 2026 by the true node (5 Dec by our mean node); "node sandhi" in Jan 2028 is wrong; Vimshottari periods match</td><td>High</td></tr>
<tr class="bearish"><td>"Core recurring signatures" (Jupiter weakness 10/11, Mars trigger 10/11, eclipse/stellium 9/11, Saturn–node / Pisces–Aries 8/11, Rahu in Capricorn)</td><td>The first three are present in every 12-month window since 1928, so they are bound to appear at every crash, and the S&amp;P did no worse when they were present. Only Saturn–node / Saturn in Pisces–Aries shows a hint (6-month falls of 15%+ 19.6% vs 14.2% of the time), and Rahu in Capricorn has only four episodes since 1928</td><td>Low: the signatures do not predict crashes</td></tr>
<tr class="mixed"><td>2026–2029 direction calls (AI crash stages, India reversal, gold to $4,650+)</td><td>Our direction tables (end-2027) are mixed on the S&amp;P and lean bullish on the Sensex in Aug–Dec 2027, against their bearish call; they agree on silver strength in Dec 2026 – Jun 2027 and on gold strength in Aug 2027; our direction rules have only a small, unproven edge</td><td>Partial</td></tr>
<tr class="bullish"><td>Timing of turbulence (Feb–Apr 2027 tremor, Jan–May 2028 apex)</td><td>Our robust big-move factors cluster in the same windows: Mercury–Saturn 2/12 Feb–May 2027 (S&amp;P); Jupiter–Pluto, Jupiter–Neptune, Mercury–Saturn and Venus retrograde across Jan–Jun 2028 (S&amp;P); Mars–Saturn conjunction Apr–May 2028 and Venus retrograde May–Jun 2028 (Sensex). They mark big moves in both directions and say nothing about the size of a fall</td><td>Good on timing, none on direction or size</td></tr>
<tr class="mixed"><td>Nov 2026 "Act I"</td><td>Nasdaq −18.1%, gold low $3,515, silver $41.03 by 20 Nov, which matches their numbers, but these had already happened when the chart was made; the Sensex was at a high on 20 Nov, against their "choppy, FII outflows"</td><td>Not a test (drawn after the fact)</td></tr>
</tbody></table></div>
<h2>A. Are the planet positions right?</h2>
<p class="m">Historical claims: {tot.count('holds')} hold on the crash date, {tot.count('in window')} hold somewhere in the crash window, {tot.count('wrong')} are wrong. 2026–2029 claims: {totf.count('holds') + totf.count('in window')} hold in the stated window, {totf.count('wrong')} are wrong.</p>
<div class="wrap"><table><thead><tr><th>Crash (reference date / window)</th><th>Claim</th><th>Our ephemeris</th><th>When true in the window</th></tr></thead><tbody>{claim_rows(res['A'], 'crash')}</tbody></table></div>
<h3>2026–2029 windows</h3>
<div class="wrap"><table><thead><tr><th>Stage</th><th>Claim</th><th>Our ephemeris</th><th>When true</th></tr></thead><tbody>{claim_rows(res['F'], 'stage')}</tbody></table></div>
<p class="s">India 1947 chart (15 Aug 1947 00:00 IST, Delhi), Moon {res['dasha']['moon']}; Vimshottari mahadashas from 2000: {dasha}.
Mars antardashas: {'; '.join(f"{L} {a[:7]} – {b[:7]}" for L, a, b in res['dasha']['mars_sub'])}. Their India dasha labels (Mars–Rahu Nov 2026–Jan 2027, Mars–Jupiter Feb–Jun 2027, Mars–Saturn 2028, Mars–Mercury from Mar 2029) match.</p>
<h2>B. Do the "core recurring signatures" predict crashes? S&amp;P 500, {m['start']} – {m['end']}</h2>
<p class="m">Each signature defined objectively and checked on every trading day. The infographic counts a signature as present at 8–11 of 11 crashes, but most of them are present on a large share of all days, and on almost every 12-month window; the test that matters is whether the S&amp;P did worse when they were present. The S&amp;P was 20% or more below its high on {m['bear_share']}% of days.</p>
<div class="wrap"><table><thead><tr><th>Signature (our definition)</th><th>Present on</th><th>On the 11 crash dates</th><th>Anywhere in the first year of the crash window</th><th>Chance a random 12-month window contains it</th><th>6-month fall of 15%+ when present vs absent</th><th>6-month S&amp;P return when present vs absent</th></tr></thead><tbody>{brows}</tbody></table></div>
<h2>So far: prices from June to 20 Nov 2026</h2>
<div class="wrap"><table><thead><tr><th>Market</th><th>High since June</th><th>Low after it</th><th>Fall</th><th>20 Nov 2026</th></tr></thead><tbody>{realrows}</tbody></table></div>
<p class="s">Their Nov 2026 numbers (Nasdaq −16 to −20%, gold floor $3,525–3,700, silver $41–45) sit right on these moves, so the infographic was most likely drawn after them: Act I is a description, not a test.</p>
<h2>C. Their 2026–2029 windows against our model</h2>
<p class="m">Our direction tables (S&amp;P 500, Sensex; weekdays per signal and strength) and the robust big-move factors (more ±2% days, either direction) active in each window.</p>
<div class="wrap"><table><thead><tr><th>Their stage</th><th>Their call</th><th>Our direction tables (weekdays)</th><th>Our robust volatility factors active</th></tr></thead><tbody>{srows}</tbody></table></div>
<p class="s">Generated by tools/validate_external_model.py.</p></body></html>"""
    (OUT / "external_model_check_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
