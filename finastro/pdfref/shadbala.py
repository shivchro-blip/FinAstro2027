"""Shadbala (sixfold planetary strength) and Ashtakavarga, per BPHS Ch.27 and Ch.66.

Primary source: Brihat Parasara Hora Sastra, tr. R. Santhanam,
Reference_materials/Others/BPHS/BPHS - 1 RSanthanam.pdf, Ch.27 (PDF pp.263-287).
Validation: B.V. Raman, "Graha and Bhava Balas", worked example (16 Oct 1918,
14:22:16 IST, 13N 77E35, Raman ayanamsa); every component is reproduced in
tests/test_shadbala.py with convention="raman".

Three conventions differ between BPHS and Raman and are selectable:
  * Drekkana bala: BPHS 27.6 "male, female and hermaphrodite planets ... first,
    second and third decanates"; Raman gives neuter the 2nd and female the 3rd.
  * Saptavargaja points: BPHS 27.2-4 gives 45/30/20/15/10/4/2 (moolatrikona,
    own, great friend, friend, neutral, enemy, great enemy); Raman uses
    45/30/22.5/15/7.5/3.75/1.875.
  * Cheshta bala of the Sun / Moon: BPHS 27.18 = the Sun's ayana bala / the
    Moon's paksha bala; Raman's example lists 0 for both.
convention="bphs" (default, used by the commodity model) or "raman".
Kendradi bala counts houses by sign from the lagna and ayana bala uses the
kranti (declination) of the planet's ecliptic degree, as Raman's example does.

Components (all in virupas; 60 virupas = 1 rupa):
  Sthana   uchcha + saptavargaja + ojayugma + kendradi + drekkana   (27.1-6)
  Dig      arc from the powerless cusp / 3                           (27.7)
  Kala     nathonnatha + paksha + tribhaga + abda/masa/dina/hora
           + ayana + yuddha                                          (27.8-17)
  Cheshta  Sun = ayana bala, Moon = paksha bala, others by
           cheshta kendra (seeghrochcha - (mean + true)/2) / 3
  Naisargika  60 x n/7                                               (27.14)
  Drik     (benefic aspects - malefic aspects) / 4, Parashari values
Required totals (27.32-33): Sun 390, Moon 360, Mars 300, Mercury 420,
Jupiter 390, Venus 330, Saturn 300.

Mean longitudes for cheshta bala: JPL approximate Keplerian elements
(Standish 1992, valid 1800-2050), tropical; seeghrochcha = mean Sun for
Mars/Jupiter/Saturn and the planet's heliocentric mean longitude for
Mercury/Venus. Raman's book uses Surya-Siddhanta epoch tables, so its cheshta
values differ from these by a few virupas.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field

import swisseph as swe

from .. import ephem as E

PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SWE_ID = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
          "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}
SIGN_LORD = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
DEEP_DEBIL = {"Sun": 190, "Moon": 213, "Mars": 118, "Mercury": 345, "Jupiter": 275, "Venus": 177, "Saturn": 20}
OWN = {"Sun": (4,), "Moon": (3,), "Mars": (0, 7), "Mercury": (2, 5), "Jupiter": (8, 11), "Venus": (1, 6), "Saturn": (9, 10)}
MOOLATRIKONA = {"Sun": (4, 0, 20), "Moon": (1, 3, 30), "Mars": (0, 0, 12), "Mercury": (5, 15, 20),
                "Jupiter": (8, 0, 10), "Venus": (6, 0, 15), "Saturn": (10, 0, 20)}
NATURAL = {  # BPHS: friends / enemies (rest neutral)
    "Sun": (("Moon", "Mars", "Jupiter"), ("Venus", "Saturn")),
    "Moon": (("Sun", "Mercury"), ()),
    "Mars": (("Sun", "Moon", "Jupiter"), ("Mercury",)),
    "Mercury": (("Sun", "Venus"), ("Moon",)),
    "Jupiter": (("Sun", "Moon", "Mars"), ("Mercury", "Venus")),
    "Venus": (("Mercury", "Saturn"), ("Sun", "Moon")),
    "Saturn": (("Mercury", "Venus"), ("Sun", "Moon", "Mars")),
}
POINTS = {"bphs": {"mt": 45, "own": 30, "gf": 20, "f": 15, "n": 10, "e": 4, "ge": 2},
          "raman": {"mt": 45, "own": 30, "gf": 22.5, "f": 15, "n": 7.5, "e": 3.75, "ge": 1.875}}
SEX = {"Sun": "m", "Mars": "m", "Jupiter": "m", "Moon": "f", "Venus": "f", "Mercury": "n", "Saturn": "n"}
DREKKANA_PART = {"bphs": {"m": 0, "f": 1, "n": 2}, "raman": {"m": 0, "n": 1, "f": 2}}
NAISARGIKA = {"Sun": 60.0, "Moon": 60 * 6 / 7, "Venus": 60 * 5 / 7, "Jupiter": 60 * 4 / 7, "Mercury": 60 * 3 / 7,
              "Mars": 60 * 2 / 7, "Saturn": 60 * 1 / 7}
REQUIRED = {"Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420, "Jupiter": 390, "Venus": 330, "Saturn": 300}
WEEKDAY_LORD = ("Saturn", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus")   # BPHS remainder 0..6 (1 = Sunday)
CHALDEAN = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")
#: JPL approximate elements (Standish 1992): mean longitude L0, rate (deg / Julian century from J2000).
MEAN_L = {"Mercury": (252.25032350, 149472.67411175), "Venus": (181.97909950, 58517.81538729),
          "EMB": (100.46457166, 35999.37244981), "Mars": (-4.55343205, 19140.30268499),
          "Jupiter": (34.39644051, 3034.74612775), "Saturn": (49.95424423, 1222.49362201)}


def norm(x):
    return x % 360.0


def arc(a, b):
    d = abs(norm(a - b))
    return 360 - d if d > 180 else d


def sign(lon):
    return int(norm(lon) // 30)


# ---------------------------------------------------------------- vargas
def varga_sign(lon, n):
    lon = norm(lon)
    s, d = int(lon // 30), lon % 30
    odd = s % 2 == 0                       # Aries = sign 1 = odd
    if n == 1:
        return s
    if n == 2:                             # Parashari hora: Leo (Sun) / Cancer (Moon)
        return (4 if d < 15 else 3) if odd else (3 if d < 15 else 4)
    if n == 3:
        return (s + 4 * int(d // 10)) % 12
    if n == 7:
        return ((s if odd else s + 6) + int(d // (30 / 7))) % 12
    if n == 9:
        return (s * 9 + int(d // (10 / 3))) % 12
    if n == 12:
        return (s + int(d // 2.5)) % 12
    if n == 30:                            # trimsamsa
        if odd:
            return 0 if d < 5 else 10 if d < 10 else 8 if d < 18 else 2 if d < 25 else 6
        return 1 if d < 5 else 5 if d < 12 else 11 if d < 20 else 9 if d < 25 else 7
    raise ValueError(n)


# ---------------------------------------------------------------- relationships
def compound(p, q, sid):
    """Compound (natural + temporal) relation of p towards q; temporal from the rasi chart."""
    f, e = NATURAL[p]
    nat = 1 if q in f else -1 if q in e else 0
    h = (sid[q] // 30 - sid[p] // 30) % 12 + 1
    tmp = 1 if h in (2, 3, 4, 10, 11, 12) else -1
    t = nat + tmp
    return {2: "gf", 1: "f", 0: "n", -1: "e", -2: "ge"}[t]


def drishti(d):
    """Parashari aspect value (virupas) for d = aspected - aspecting (0-360)."""
    d = norm(d)
    if d < 30 or d >= 300:
        return 0.0
    if d < 60:
        return (d - 30) / 2
    if d < 90:
        return d - 45
    if d < 120:
        return 30 + (120 - d) / 2
    if d < 150:
        return 150 - d
    if d < 180:
        return 2 * (d - 150)
    return (300 - d) / 2


SPECIAL = {"Mars": ((90, 120, 15), (210, 240, 15)), "Jupiter": ((120, 150, 30), (240, 270, 30)),
           "Saturn": ((60, 90, 45), (270, 300, 45))}


def aspect_value(aspecting, d):
    v = drishti(d)
    for lo, hi, add in SPECIAL.get(aspecting, ()):
        if lo <= norm(d) < hi:
            v += add
    return v


# ---------------------------------------------------------------- chart
@dataclass
class Chart:
    when: dt.datetime                    # UTC
    lat: float
    lon: float
    sid: dict = field(default_factory=dict)        # sidereal longitude
    trop: dict = field(default_factory=dict)       # tropical longitude
    lat_ecl: dict = field(default_factory=dict)
    speed: dict = field(default_factory=dict)
    decl: dict = field(default_factory=dict)
    asc: float = 0.0
    mc: float = 0.0
    cusps: tuple = ()
    sunrise: dt.datetime | None = None
    sunset: dt.datetime | None = None
    next_sunrise: dt.datetime | None = None
    lat_hours: float = 0.0              # local apparent time, hours after midnight
    local_date: dt.date | None = None   # civil date of the Vedic day (sunrise to sunrise)


def jd_of(t):
    t = t.astimezone(dt.timezone.utc)
    return swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 + t.second / 3600 + t.microsecond / 3.6e9)


def from_jd(j):
    y, m, d, h = swe.revjul(j)
    return dt.datetime(y, m, d, tzinfo=dt.timezone.utc) + dt.timedelta(hours=h)


def build_chart(when, lat, lon, ayanamsa=swe.SIDM_LAHIRI, tz=None):
    E.init()
    swe.set_sid_mode(ayanamsa)
    jd = jd_of(when)
    c = Chart(when.astimezone(dt.timezone.utc), lat, lon)
    for p in PLANETS:
        x, _ = swe.calc_ut(jd, SWE_ID[p], swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
        c.sid[p], c.lat_ecl[p], c.speed[p] = x[0], x[1], x[3]
        y, _ = swe.calc_ut(jd, SWE_ID[p], swe.FLG_SWIEPH | swe.FLG_SPEED)
        c.trop[p] = y[0]
        z, _ = swe.calc_ut(jd, SWE_ID[p], swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
        c.decl[p] = z[1]
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"O", swe.FLG_SIDEREAL)      # Porphyry = Sripati bhava madhyas
    c.asc, c.mc, c.cusps = ascmc[0], ascmc[1], tuple(cusps[:12])
    geo = (lon, lat, 0)
    rs = swe.rise_trans(jd - 1, swe.SUN, swe.CALC_RISE | swe.BIT_HINDU_RISING, geo)[1][0]
    while True:
        nxt = swe.rise_trans(rs + 0.01, swe.SUN, swe.CALC_RISE | swe.BIT_HINDU_RISING, geo)[1][0]
        if nxt > jd:
            break
        rs = nxt
    ss = swe.rise_trans(rs, swe.SUN, swe.CALC_SET | swe.BIT_HINDU_RISING, geo)[1][0]
    c.sunrise, c.sunset, c.next_sunrise = from_jd(rs), from_jd(ss), from_jd(nxt)
    ra = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0][0]
    lst = (swe.sidtime(jd) * 15 + lon) % 360
    ha = norm(lst - ra)                                  # 0 at local apparent noon
    c.lat_hours = (ha / 15 + 12) % 24
    tz = tz or dt.timezone(dt.timedelta(hours=lon / 15))
    c.local_date = c.sunrise.astimezone(tz).date() if not isinstance(tz, dt.timezone) or True else None
    return c


# ---------------------------------------------------------------- components
def benefic_flags(c):
    """BPHS 27.10-11 notes: Mercury malefic if conjunct a malefic; Moon malefic in the dark half."""
    elong = norm(c.sid["Moon"] - c.sid["Sun"])
    mer_mal = any(sign(c.sid["Mercury"]) == sign(c.sid[m]) for m in ("Sun", "Mars", "Saturn"))
    return {"Sun": False, "Mars": False, "Saturn": False, "Jupiter": True, "Venus": True,
            "Mercury": not mer_mal, "Moon": elong < 180}


def sthana(c, conv):
    pts = POINTS[conv]
    out = {}
    for p in PLANETS:
        lon = c.sid[p]
        uch = arc(lon, DEEP_DEBIL[p]) / 3
        sv = 0.0
        for n in (1, 2, 3, 7, 9, 12, 30):
            s = varga_sign(lon, n)
            mt = MOOLATRIKONA[p]
            if n == 1 and s == mt[0] and mt[1] <= lon % 30 < mt[2]:
                sv += pts["mt"]
            elif s in OWN[p]:
                sv += pts["own"]
            else:
                sv += pts[compound(p, SIGN_LORD[s], c.sid)]
        rs, ns = sign(lon), varga_sign(lon, 9)
        fem = p in ("Moon", "Venus")
        oja = 15 * ((rs % 2 == 1) == fem) + 15 * ((ns % 2 == 1) == fem)
        h = (sign(lon) - sign(c.asc)) % 12 + 1          # houses by sign from the lagna (Raman's worked example)
        ken = 60 if h in (1, 4, 7, 10) else 30 if h in (2, 5, 8, 11) else 15
        dre = 15 if int((lon % 30) // 10) == DREKKANA_PART[conv][SEX[p]] else 0
        out[p] = dict(uchcha=uch, saptavargaja=sv, ojayugma=oja, kendradi=ken, drekkana=dre,
                      total=uch + sv + oja + ken + dre)
    return out


def bhava_of(c, lon):
    """House (1-12) in the Sripati bhava chart: bhava i runs between the sandhis around cusp i."""
    cu = c.cusps
    for i in range(12):
        a, b, nx = cu[i - 1], cu[i], cu[(i + 1) % 12]
        s0 = norm(a + norm(b - a) / 2)
        s1 = norm(b + norm(nx - b) / 2)
        if norm(lon - s0) < norm(s1 - s0):
            return i + 1
    return 1


def dig(c):
    powerless = {"Sun": c.mc + 180, "Mars": c.mc + 180, "Jupiter": c.asc + 180, "Mercury": c.asc + 180,
                 "Moon": c.mc, "Venus": c.mc, "Saturn": c.asc}
    return {p: arc(c.sid[p], powerless[p]) / 3 for p in PLANETS}


def ahargana(d: dt.date):
    """BPHS 'abbreviated Ahargana' (Santhanam p.270-274): JDN of the civil date - 2380558."""
    jdn = int(swe.julday(d.year, d.month, d.day, 12.0))
    return jdn - 2380558


def kala(c, conv, sth, dg):
    ben = benefic_flags(c)
    out = {p: {} for p in PLANETS}
    t = c.lat_hours
    unnata = min(t, 24 - t)                 # hours from midnight
    day_val = unnata * 5                    # 60 at noon
    for p in PLANETS:
        out[p]["nathonnatha"] = 60.0 if p == "Mercury" else day_val if p in ("Sun", "Jupiter", "Venus") else 60 - day_val
    elong = arc(c.sid["Moon"], c.sid["Sun"])
    bv = elong / 3
    for p in PLANETS:
        if p == "Moon":
            out[p]["paksha"] = 2 * bv
        else:
            out[p]["paksha"] = bv if ben[p] else 60 - bv
    is_day = c.sunrise <= c.when < c.sunset
    if is_day:
        frac = (c.when - c.sunrise) / (c.sunset - c.sunrise)
        ruler = ("Mercury", "Sun", "Saturn")[min(int(frac * 3), 2)]
    else:
        frac = (c.when - c.sunset) / (c.next_sunrise - c.sunset)
        ruler = ("Moon", "Venus", "Mars")[min(int(frac * 3), 2)]
    for p in PLANETS:
        out[p]["tribhaga"] = 60.0 if p in ("Jupiter", ruler) else 0.0
    A = ahargana(c.local_date)
    abda = WEEKDAY_LORD[(3 * (A // 360) + 1) % 7]
    masa = WEEKDAY_LORD[(2 * (A // 30) + 1) % 7]
    dina = WEEKDAY_LORD[A % 7]
    hora_i = int((c.when - c.sunrise) / ((c.next_sunrise - c.sunrise) / 24))
    hora = CHALDEAN[(CHALDEAN.index(dina) + hora_i) % 7]
    for p in PLANETS:
        out[p]["abda"] = 15.0 if p == abda else 0.0
        out[p]["masa"] = 30.0 if p == masa else 0.0
        out[p]["dina"] = 45.0 if p == dina else 0.0
        out[p]["hora"] = 60.0 if p == hora else 0.0
    eps = swe.calc_ut(jd_of(c.when), swe.ECL_NUT)[0][0]
    for p in PLANETS:
        k = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(c.trop[p]))))   # kranti of the ecliptic degree
        if p == "Mercury":
            v = 23.45 + abs(k)
        elif p in ("Moon", "Saturn"):
            v = 23.45 - k
        else:
            v = 23.45 + k
        out[p]["ayana"] = v * 1.2793 * (2 if p == "Sun" else 1)
    out_y = {p: 0.0 for p in PLANETS}
    star = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    for i, a in enumerate(star):
        for b in star[i + 1:]:
            if arc(c.sid[a], c.sid[b]) < 1.0:
                win, lose = (a, b) if c.lat_ecl[a] > c.lat_ecl[b] else (b, a)
                def base(q):
                    return sth[q]["total"] + dg[q] + sum(v for k2, v in out[q].items())
                diff = abs(base(win) - base(lose))
                out_y[win] += diff
                out_y[lose] -= diff
    for p in PLANETS:
        out[p]["yuddha"] = out_y[p]
        out[p]["total"] = sum(v for k2, v in out[p].items())
    return out, dict(abda=abda, masa=masa, dina=dina, hora=hora, tribhaga=ruler, ahargana=A)


def mean_lon(name, jd):
    T = (jd - 2451545.0) / 36525
    L0, r = MEAN_L[name]
    return norm(L0 + r * T)


def cheshta(c, kl, conv="bphs"):
    jd = jd_of(c.when)
    sun_mean = norm(mean_lon("EMB", jd) + 180)
    # BPHS 27.18: Sun's cheshta = his ayana bala, Moon's = her paksha bala; Raman's example lists 0 for both
    out = {"Sun": kl["Sun"]["ayana"], "Moon": kl["Moon"]["paksha"]} if conv == "bphs" else {"Sun": 0.0, "Moon": 0.0}
    for p in ("Mars", "Jupiter", "Saturn"):
        k = arc(sun_mean, (mean_lon(p, jd) + c.trop[p]) / 2 if abs(mean_lon(p, jd) - c.trop[p]) < 180 else (mean_lon(p, jd) + c.trop[p] + 360) / 2)
        out[p] = k / 3
    for p in ("Mercury", "Venus"):
        seeg = mean_lon(p, jd)
        m, tr = sun_mean, c.trop[p]
        mid = (m + tr) / 2 if abs(m - tr) < 180 else (m + tr + 360) / 2
        out[p] = arc(seeg, mid) / 3
    return out


def drik(c):
    ben = benefic_flags(c)
    out = {}
    for p in PLANETS:
        tot = 0.0
        for q in PLANETS:
            if q == p:
                continue
            v = aspect_value(q, c.sid[p] - c.sid[q])
            tot += v if ben[q] else -v
        out[p] = tot / 4
    return out


def shadbala(c: Chart, convention="bphs"):
    sth = sthana(c, convention)
    dg = dig(c)
    kl, lords = kala(c, convention, sth, dg)
    ch = cheshta(c, kl, convention)
    dk = drik(c)
    res = {}
    for p in PLANETS:
        total = sth[p]["total"] + dg[p] + kl[p]["total"] + ch[p] + NAISARGIKA[p] + dk[p]
        res[p] = dict(sthana=sth[p], dig=dg[p], kala=kl[p], cheshta=ch[p], naisargika=NAISARGIKA[p], drik=dk[p],
                      total=total, rupas=total / 60, required=REQUIRED[p], ratio=total / REQUIRED[p])
    res["_lords"] = lords
    return res


def strength_class(ratio):
    return ("Very weak" if ratio < 0.75 else "Weak" if ratio < 0.90 else "Borderline" if ratio < 1.00 else
            "Strong" if ratio < 1.10 else "Very strong" if ratio < 1.25 else "Exceptionally strong")


# ---------------------------------------------------------------- Ashtakavarga (BPHS Ch.66)
BAV = {  # benefic places counted from each contributor (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Lagna)
    "Sun": ((1, 2, 4, 7, 8, 9, 10, 11), (3, 6, 10, 11), (1, 2, 4, 7, 8, 9, 10, 11), (3, 5, 6, 9, 10, 11, 12),
            (5, 6, 9, 11), (6, 7, 12), (1, 2, 4, 7, 8, 9, 10, 11), (3, 4, 6, 10, 11, 12)),
    "Moon": ((3, 6, 7, 8, 10, 11), (1, 3, 6, 7, 10, 11), (2, 3, 5, 6, 9, 10, 11), (1, 3, 4, 5, 7, 8, 10, 11),
             (1, 4, 7, 8, 10, 11, 12), (3, 4, 5, 7, 9, 10, 11), (3, 5, 6, 11), (3, 6, 10, 11)),
    "Mars": ((3, 5, 6, 10, 11), (3, 6, 11), (1, 2, 4, 7, 8, 10, 11), (3, 5, 6, 11), (6, 10, 11, 12),
             (6, 8, 11, 12), (1, 4, 7, 8, 9, 10, 11), (1, 3, 6, 10, 11)),
    "Mercury": ((5, 6, 9, 11, 12), (2, 4, 6, 8, 10, 11), (1, 2, 4, 7, 8, 9, 10, 11), (1, 3, 5, 6, 9, 10, 11, 12),
                (6, 8, 11, 12), (1, 2, 3, 4, 5, 8, 9, 11), (1, 2, 4, 7, 8, 9, 10, 11), (1, 2, 4, 6, 8, 10, 11)),
    "Jupiter": ((1, 2, 3, 4, 7, 8, 9, 10, 11), (2, 5, 7, 9, 11), (1, 2, 4, 7, 8, 10, 11), (1, 2, 4, 5, 6, 9, 10, 11),
                (1, 2, 3, 4, 7, 8, 10, 11), (2, 5, 6, 9, 10, 11), (3, 5, 6, 12), (1, 2, 4, 5, 6, 7, 9, 10, 11)),
    "Venus": ((8, 11, 12), (1, 2, 3, 4, 5, 8, 9, 11, 12), (3, 5, 6, 9, 11, 12), (3, 5, 6, 9, 11), (5, 8, 9, 10, 11),
              (1, 2, 3, 4, 5, 8, 9, 10, 11), (3, 4, 5, 8, 9, 10, 11), (1, 2, 3, 4, 5, 8, 9, 11)),
    "Saturn": ((1, 2, 4, 7, 8, 10, 11), (3, 6, 11), (3, 5, 6, 10, 11, 12), (6, 8, 9, 10, 11, 12), (5, 6, 11, 12),
               (6, 11, 12), (3, 5, 6, 11), (1, 3, 4, 6, 10, 11)),
}


def ashtakavarga(c: Chart):
    """Bhinna (per planet) and Sarva Ashtakavarga by sign (0 = Aries). SAV always totals 337."""
    contrib = [sign(c.sid[p]) for p in PLANETS] + [sign(c.asc)]
    bav = {}
    for p, rows in BAV.items():
        v = [0] * 12
        for src, places in zip(contrib, rows):
            for h in places:
                v[(src + h - 1) % 12] += 1
        bav[p] = v
    sav = [sum(bav[p][s] for p in BAV) for s in range(12)]
    return bav, sav
