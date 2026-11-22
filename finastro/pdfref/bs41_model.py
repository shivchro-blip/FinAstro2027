"""Financial Astrology Model v1.0 - Classical Combined Commodity Framework (gold).

Locked methodology: Reference_materials/extracted/FINANCIAL_ASTROLOGY_MODEL_v1.md.

Layer 1 - Brihat Samhita (tr. P.S. Sastri 1946), Ch.41 (PDF pp.327-331):
  41.2 / 41.7   gold belongs to Mesha and Makara (silver is assigned no sign ->
                silver = "Insufficient data", safeguard 7).
  41.9-10       Jupiter in 2,4,5,7,9,10,11 / Mercury in 2,5,8,10,11 from a sign
                increase its articles; Venus in 6,7 destroys them, elsewhere
                promotes; malefics in 3,6,10,11 are beneficial, elsewhere harmful.
  41.11         strong malefics in 1,2,4,5,7,8,9,12 -> articles "very costly and scarce".
  41.12         strong benefics in auspicious houses -> articles "thrive, fetch good
                price and have great demand" (translation ambiguity kept: another
                translation reads moderate prices / easy availability).
  41.13         a benefic aspect on the sign protects; a malefic aspect does the reverse.
Layer 2 - BPHS Shadbala (finastro/pdfref/shadbala.py, convention "bphs") for
  "strong"; Sarvashtakavarga of the sign; Parashari whole-sign aspects.
Layer 3 - two separate indices and a confidence grade.

Chart: New York (40.7128 N, 74.0060 W) at Hindu sunrise of each civil date,
sidereal Lahiri, geocentric. Houses are counted from the commodity's sign.

Planet roles (methodology section 4):
  benefics  Jupiter, Venus, Mercury when not in a sign with Sun/Mars/Saturn;
            the waxing Moon counts for aspects only (41.9-10 name no houses for it).
  malefics  Saturn, Mars, Sun, the waning Moon, and Mercury when afflicted
            (generic malefic rule of 41.10).
  Rahu / Ketu  reported (house from the sign) but not scored.

Scoring, per sign X (Aries, Capricorn), each component in [-1, +1]:
  Scarcity / price-pressure index S (41.10-11, 41.13):
    H_S  = sum over malefics of (+1 in 1,2,4,5,7,8,9,12; -1 in 3,6,10,11) / 3
    K_S  = same, each weighted by its Shadbala strength weight w, / (3 x 1.5)
    A_S  = (sum of malefic aspects on X x w - sum of benefic aspects x w) / 3
    AV_S = -(SAV(X) - 28) / 9          (support for the articles -> less scarcity)
  Demand / market-value index V (41.9-10, 41.12-13):
    H_V  = Jupiter (+1 in its houses), Mercury (+1 in its houses), Venus (-1 in 6/7, else +1), / 3
    K_V  = same weighted by w / (3 x 1.5)
    A_V  = -A_S
    AV_V = +(SAV(X) - 28) / 9
  index = 100 x (0.45 H + 0.25 K + 0.20 A + 0.10 AV), all clipped to [-1, 1];
  gold = mean of the Aries and Capricorn values.
  Strength weight w from Shadbala / BPHS requirement: <0.75 0; 0.75-0.89 0.25;
  0.90-0.99 0.5; 1.00-1.09 1.0; 1.10-1.24 1.25; >=1.25 1.5.
Price bias: from S (methodology table: +60 strong bullish ... -60 strong bearish).
Confidence: indicators H_S, K_S, A_S, AV_S and V (V counts as corroboration
because 41.12 also reads as price-supportive); agreeing = same sign as S
(|x| > 0.05). >=4 agreeing and none against: Very high; >=3: High; 2: Moderate;
otherwise Low; |S| < 15: Neutral.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import swisseph as swe

from . import shadbala as SB

NY = ZoneInfo("America/New_York")
NY_LAT, NY_LON = 40.7128, -74.0060
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
COMMODITY_SIGNS = {"gold": (0, 9)}            # BS 41.2 Mesha, 41.7 Makara; silver: none in Ch.41
MAL_HARM = {1, 2, 4, 5, 7, 8, 9, 12}           # 41.11
MAL_GOOD = {3, 6, 10, 11}                      # 41.10
JUP_GOOD = {2, 4, 5, 7, 9, 10, 11}             # 41.9
MER_GOOD = {2, 5, 8, 10, 11}                   # 41.9
VEN_BAD = {6, 7}                               # 41.10
ASPECT_HOUSES = {"Mars": (4, 7, 8), "Jupiter": (5, 7, 9), "Saturn": (3, 7, 10)}
W, WEIGHTS = (0.45, 0.25, 0.20, 0.10), ("placement", "strength", "aspects", "ashtakavarga")


def strength_weight(ratio):
    return 0 if ratio < 0.75 else 0.25 if ratio < 0.90 else 0.5 if ratio < 1.0 else 1.0 if ratio < 1.10 else 1.25 if ratio < 1.25 else 1.5


def clip(x):
    return max(-1.0, min(1.0, x))


def bias(s):
    return ("Strong bullish" if s >= 60 else "Bullish" if s >= 35 else "Mild bullish" if s >= 15 else
            "Neutral / mixed" if s > -15 else "Mild bearish" if s > -35 else "Bearish" if s > -60 else "Strong bearish")


def sunrise_chart(day: dt.date):
    noon = dt.datetime(day.year, day.month, day.day, 12, tzinfo=NY)
    c = SB.build_chart(noon, NY_LAT, NY_LON, tz=NY)
    c2 = SB.build_chart(c.sunrise + dt.timedelta(seconds=30), NY_LAT, NY_LON, tz=NY)
    c2.local_date = day
    return c2


def evaluate(day: dt.date, commodity="gold"):
    if commodity not in COMMODITY_SIGNS:
        return {"date": day.isoformat(), "commodity": commodity, "status": "Insufficient data",
                "reason": "Brihat Samhita Ch.41 assigns no sign to this commodity."}
    c = sunrise_chart(day)
    sb = SB.shadbala(c, "bphs")
    bav, sav = SB.ashtakavarga(c)
    ben = SB.benefic_flags(c)
    rahu = swe.calc_ut(SB.jd_of(c.when), swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    psign = {p: SB.sign(c.sid[p]) for p in SB.PLANETS}
    psign["Rahu"], psign["Ketu"] = SB.sign(rahu), SB.sign(rahu + 180)
    w = {p: strength_weight(sb[p]["ratio"]) for p in SB.PLANETS}
    malefics = ["Sun", "Mars", "Saturn"] + (["Moon"] if not ben["Moon"] else []) + (["Mercury"] if not ben["Mercury"] else [])
    benefics = ["Jupiter", "Venus"] + (["Mercury"] if ben["Mercury"] else [])
    per_sign = []
    for x in COMMODITY_SIGNS[commodity]:
        house = {p: (psign[p] - x) % 12 + 1 for p in psign}
        hs = ks = hv = kv = 0.0
        lines = []
        for m in malefics:
            e = 1 if house[m] in MAL_HARM else -1
            hs += e
            ks += e * w[m]
            lines.append(dict(planet=m, role="malefic", house=house[m], effect="harmful house (41.11: costly & scarce)" if e > 0 else "beneficial house (41.10)",
                              e=e, strength=SB.strength_class(sb[m]["ratio"]), ratio=round(sb[m]["ratio"], 3)))
        for b in benefics:
            if b == "Jupiter":
                e = 1 if house[b] in JUP_GOOD else 0
            elif b == "Mercury":
                e = 1 if house[b] in MER_GOOD else 0
            else:
                e = -1 if house[b] in VEN_BAD else 1
            hv += e
            kv += e * w[b]
            lines.append(dict(planet=b, role="benefic", house=house[b],
                              effect={1: "increases / promotes (41.9-10, 41.12)", 0: "no effect stated", -1: "destroys (41.10)"}[e],
                              e=e, strength=SB.strength_class(sb[b]["ratio"]), ratio=round(sb[b]["ratio"], 3)))
        asp_mal = asp_ben = 0.0
        asp = []
        for p in SB.PLANETS:
            h_from_p = (x - psign[p]) % 12 + 1
            if h_from_p == 1:
                continue
            if h_from_p in ASPECT_HOUSES.get(p, (7,)):
                if ben[p]:
                    asp_ben += w[p]
                else:
                    asp_mal += w[p]
                asp.append(f"{p} ({'benefic' if ben[p] else 'malefic'}, {SB.strength_class(sb[p]['ratio']).lower()}) aspects {SIGNS[x]} ({h_from_p}th from {p})")
        comp_s = (clip(hs / 3), clip(ks / 4.5), clip((asp_mal - asp_ben) / 3), clip(-(sav[x] - 28) / 9))
        comp_v = (clip(hv / 3), clip(kv / 4.5), clip((asp_ben - asp_mal) / 3), clip((sav[x] - 28) / 9))
        S = 100 * sum(a * b for a, b in zip(W, comp_s))
        V = 100 * sum(a * b for a, b in zip(W, comp_v))
        per_sign.append(dict(sign=SIGNS[x], S=round(S, 1), V=round(V, 1), comp_S=[round(v, 3) for v in comp_s], comp_V=[round(v, 3) for v in comp_v],
                             SAV=sav[x], planets=lines, aspects=asp, nodes={n: house[n] for n in ("Rahu", "Ketu")}))
    S = sum(d["S"] for d in per_sign) / len(per_sign)
    V = sum(d["V"] for d in per_sign) / len(per_sign)
    ind = {f"S-{WEIGHTS[i]}": sum(d["comp_S"][i] for d in per_sign) / len(per_sign) for i in range(4)}
    ind["demand/value index"] = V / 100
    sgn = 1 if S > 0 else -1
    agree = [k for k, v in ind.items() if abs(v) > 0.05 and (v > 0) == (sgn > 0)]
    against = [k for k, v in ind.items() if abs(v) > 0.05 and (v > 0) != (sgn > 0)]
    if abs(S) < 15:
        conf = "Neutral"
    elif len(agree) >= 4 and not against:
        conf = "Very high"
    elif len(agree) >= 3:
        conf = "High"
    elif len(agree) == 2:
        conf = "Moderate"
    else:
        conf = "Low"
    return dict(date=day.isoformat(), commodity=commodity, chart_time=c.when.astimezone(NY).isoformat(), S=round(S, 1), V=round(V, 1),
                bias=bias(S), confidence=conf, agree=agree, against=against, per_sign=per_sign,
                shadbala={p: dict(total=round(sb[p]["total"], 1), ratio=round(sb[p]["ratio"], 3), cls=SB.strength_class(sb[p]["ratio"])) for p in SB.PLANETS},
                positions={p: f"{SIGNS[psign[p]]} {c.sid[p] % 30:.1f}" if p in c.sid else SIGNS[psign[p]] for p in psign},
                benefic=ben)
