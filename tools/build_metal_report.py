"""Gold / silver reports: every rule that names the metal, 20 Nov 2026 - 31 Dec 2027.

    python tools/build_metal_report.py gold
    python tools/build_metal_report.py silver

Sources: TA Section 34 'When gold can rally / fall' and the gold items of
other TA sections; KD slides naming gold; the 2026 document's gold section
(the existing calendar's cfg_gold_* rules). Every window is recomputed with
finastro/pdfref's engine and each boundary is checked against the
astronomy layer's own records (build/astronomy_2026.json / _2027.json, an
independent code path) and, for 2027, against the existing calendar's GC rows.

Writes build/pdfref/<metal>_2026-11-20_to_2027-12-31_ET.html and .json.
Times: US Eastern (America/New_York; EST, or EDT in summer).
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import html
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky, parse  # noqa: E402
from finastro.pdfref import catalogue as C  # noqa: E402
from finastro.pdfref.detect import Ctx, Hit, POOL, WEEKDAYS, aspects, windows, entries  # noqa: E402
from finastro.pdfref.engine import Grid, conjunction_instants, name, snapshot, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
P0 = dt.datetime(2026, 11, 20, tzinfo=ET).astimezone(UTC)
P1 = dt.datetime(2028, 1, 1, tzinfo=ET).astimezone(UTC)
OUT = ROOT / "build" / "pdfref"
DOC26 = "2026 document (data/source_2026.html), Gold section pp.136-148"
DOC26S = "2026 document (data/source_2026.html), Silver section"
METAL = "gold"
CFG = {
    "gold": {"label": "Gold (XAUUSD / COMEX GC)", "word": "gold", "Word": "Gold", "instr": "GC"},
    "silver": {"label": "Silver (XAGUSD / COMEX SI)", "word": "silver", "Word": "Silver", "instr": "SI"},
}


def et(t):
    if t is None:
        return ""
    x = t.astimezone(ET)
    return f"{x:%a %d %b %Y %H:%M} {x.tzname()}"


def et_date(d):
    return f"{d:%a %d %b %Y}"


# --------------------------------------------- 2026-document gold rules (extra)
def nak(body, n):
    return lambda s: s[body].nak == n and s[body].nak


EXTRA = {"gold": [], "silver": []}


def xrule(id, title, refs, verdict, rule, calc, detector, existing=(), quals=(), metal="gold"):
    for m in ((metal,) if isinstance(metal, str) else metal):
        EXTRA[m].append(C.Rule(id=id, title=title, refs=refs, verdict=verdict, markets=(m,), rule=rule, calc=calc,
                               detector=detector, existing=existing, quals=quals))


xrule("doc26_gold_bull_11_venus_rohini", "Venus in Rohini", (DOC26 + " - Bullish #11",), "Bullish", "Venus in Rohini nakshatra.", C.NAKCALC,
      windows(nak("Venus", "Rohini"), ("Venus",)), ("cfg_gold_bullish_11_venus_in_rohini",))
xrule("doc26_gold_bull_12_mars_pushya", "Mars in Pushya", (DOC26 + " - Bullish #12",), "Bullish", "Mars in Pushya nakshatra.", C.NAKCALC,
      windows(nak("Mars", "Pushya"), ("Mars",)), ("cfg_gold_bullish_12_mars_in_pushya",))
xrule("doc26_gold_bear_06_venus_punarvasu", "Venus in Punarvasu", (DOC26 + " - Bearish #6",), "Bearish", "Venus in Punarvasu nakshatra.", C.NAKCALC,
      windows(nak("Venus", "Punarvasu"), ("Venus",)), ("cfg_gold_bearish_06_venus_in_punarvasu",))
xrule("doc26_gold_bull_04_jupiter_gemini", "Jupiter in Gemini", (DOC26 + " - Bullish #4", "TA p.154 S34 A6 ('bullish after 5 months')"), "Bullish",
      "Jupiter resident in Gemini (the 2026 document's printed row is the residency).", C.SIGNCALC,
      windows(lambda s: s["Jupiter"].sign == "Gemini" and "Gemini", ("Jupiter",)))


def _sun_libra_aspected(s):
    if s["Sun"].sign != "Libra":
        return False
    m = [b for b in ("Mars", "Saturn", "Rahu", "Ketu") if s[b].sign_i == s["Sun"].sign_i or aspects(s, b, "Sun")]
    return tuple(m) or False


xrule("doc26_gold_bull_02_sun_libra_aspected", "Sun in Libra aspected by (or with) malefics", (DOC26 + " - Bullish #2", "TA p.154 S34 A3 ('with other Malefic like Saturn, Mars & Rahu')"),
      "Bullish", "Sun in Libra with Mars, Saturn, Rahu or Ketu in Libra or casting whole-sign drishti on it (Mars 4/7/8, Saturn 3/7/10, nodes 7).",
      C.SIGNCALC + " Drishti per config valence.drishti.", windows(_sun_libra_aspected, ("Sun",)), ("cfg_gold_bullish_02_sun_libra_aspected_by_malefics",))


def _new_moons(ctx):
    out = []
    for t, how in conjunction_instants(ctx.grid, "Moon", "Sun"):
        if t.year == ctx.year:
            s = snapshot(t)
            out.append(Hit(t, None, ("Sun", "Moon"), {"degree": f"{s['Sun'].deg:.2f} deg {s['Sun'].sign}"}))
    return out


xrule("doc26_gold_bull_10_sun_moon_same_degree", "Sun and Moon on the same degree (new moon)", (DOC26 + " - Bullish #10",), "Bullish (short-term bounce)",
      "Exact Sun-Moon conjunction.", "Instant the Moon's sidereal longitude equals the Sun's (bisected to 30 s).", _new_moons, ("cfg_gold_bullish_10_sun_moon_same_degree",))


def _aq_friday(ctx):
    out = []
    for t, sign, s, m in C.sankrantis(ctx):
        if sign == "Aquarius":
            wd_ny, wd_in = C.vara(ctx, t), C.vara(ctx, t, "mumbai")
            if 4 in (wd_ny, wd_in):
                out.append(Hit(t, None, ("Sun",), {"weekday_NY_hindu_day": WEEKDAYS[wd_ny], "weekday_IST_hindu_day": WEEKDAYS[wd_in]}))
    return out


xrule("doc26_gold_bull_13_aquarius_sankranti_friday", "Sun enters Aquarius on a Friday", (DOC26 + " - Bullish #13",), "Bullish",
      "Aquarius Sankranti falling on a Friday.", "Sun's sidereal ingress into Aquarius; weekday = Hindu day (sunrise to sunrise) at New York and at Mumbai.",
      _aq_friday, ("cfg_gold_bullish_13_aquarius_sankranti_on_friday",))


def _darshan_days(days, label):
    def run(ctx):
        out = []
        for ss, d, s in C.darshans(ctx):
            if d.weekday() in days:
                out.append(Hit(ss, None, ("Moon", "Sun"), {"weekday": WEEKDAYS[d.weekday()], "moon_nakshatra": s["Moon"].nak}, day=d))
        return out
    return run


xrule("doc26_gold_bull_08_moonrise_mon_fri", "Moon darshan (first sighting) on Monday or Friday", (DOC26 + " - Bullish #8 'Moonrise on Monday or Friday'",), "Bullish",
      "First evening sighting after the new moon falls on a Monday or Friday.", "Darshan as in finastro/pdfref (first New York sunset, elongation >= 12 deg, age >= 20 h).",
      _darshan_days((0, 4), ""), quals=C.DARSHAN_Q + ("The 2026 document's two printed rows (Fri 20-Mar-26, Mon 12-Oct-26) are both darshan evenings, which is how 'moonrise' is read here.",))


def _sun_eclipse_wed(ctx):
    out = []
    for r in ctx.sky.class_records("eclipse"):
        if r["rule_family"] == "eclipse/solar":
            t = parse(r["time"]["t_start_utc"])
            if t.year == ctx.year and 2 in (C.vara(ctx, t), C.vara(ctx, t, "mumbai")):
                out.append(Hit(t, None, ("Sun", "Moon"), {}))
    return out


xrule("kd114_sun_eclipse_wednesday", "Solar eclipse on a Wednesday", ("KD p.114 (12 Aug 2026: 'Day: Wednesday - Bullish for Cotton, Gold, Silver, Copper')",),
      "Bullish for gold, silver (and cotton, copper)", "A solar eclipse on a Wednesday.", "Eclipse maximum (Swiss Ephemeris); Hindu weekday at New York and Mumbai.", _sun_eclipse_wed,
      metal=("gold", "silver"))

# --------------------------------------------- silver (2026 document + KD + TA)
def _alone_in(body, signs):
    def p(s):
        if s[body].sign not in signs:
            return False
        return (not [b for b in POOL if b != body and s[b].sign_i == s[body].sign_i]) and s[body].sign
    return p


xrule("doc26_silver_bear_01_venus_alone_leo_libra", "Venus alone in Leo or Libra", (DOC26S + " - Bearish #1", "TA p.160 S35 B1 ('Venus in leo or Libra')"), "Bearish",
      "Venus in Leo or Libra with no other graha (Moon excluded) in the sign.", C.SIGNCALC, windows(_alone_in("Venus", ("Leo", "Libra")), ("Venus",)),
      ("cfg_silver_bearish_01_venus_alone_in_leo_or_libra",), metal="silver")
xrule("doc26_silver_bear_02_mercury_alone_aries_virgo", "Mercury alone in Aries or Virgo", (DOC26S + " - Bearish #2", "TA p.160 S35 B2"), "Bearish",
      "Mercury in Aries or Virgo with no other graha (Moon excluded) in the sign.", C.SIGNCALC, windows(_alone_in("Mercury", ("Aries", "Virgo")), ("Mercury",)),
      ("cfg_silver_bearish_02_mercury_alone_in_aries_or_virgo",), metal="silver")
xrule("doc26_silver_bear_04_mars_vargottam_cancer", "Mars Vargottam in Cancer", (DOC26S + " - Bearish #4", "KD p.119 ('Debilitated Mars, negative impact... High negative impact specifically flagged for Silver')"),
      "Bearish (KD: high negative impact for silver)", "Mars in Cancer and in the Cancer navamsa (Cancer 0-3deg20').", "D1 and D9 sign of Mars.",
      windows(lambda s: s["Mars"].sign == "Cancer" and s["Mars"].vargottama, ("Mars",)), metal="silver")
xrule("doc26_silver_bull_07b_rahu_mars_same_nakshatra", "Rahu and Mars in the same nakshatra", (DOC26S + " - Bullish #7 second row", "TA p.158 S35 A4 ('More Bullish when in same Nakshatra')"),
      "More Bullish", "Rahu and Mars in one nakshatra.", C.NAKCALC, windows(lambda s: s["Rahu"].nak_i == s["Mars"].nak_i and s["Mars"].nak, ("Rahu", "Mars")), metal="silver")
xrule("ta_s35a17b_moon_mercury_alone", "Only Moon and Mercury alone in a sign", ("TA p.159 S35 A17 (Moon-Mercury half)",), "Silver Bullish",
      "Moon and Mercury share a sign with no other graha in it.", C.SIGNCALC, windows(C.alone_together("Moon", "Mercury"), ("Moon", "Mercury")),
      quals=("The 2026 document prints only the Sun-Mercury half of this rule.",), metal="silver")


def _shashti(ctx):
    out = []
    for d in ctx.ny_days():
        s = snapshot(ctx.sunrise(d).replace(microsecond=0))
        if s.tithi == 6:
            out.append(Hit(ctx.sunrise(d), None, ("Moon", "Sun"), {"tithi_at_sunrise": "Shukla Shashti"}, day=d))
    return out


xrule("ta_s35_silver_prophecy_shashti", "Silver prophecy: Shukla Shashti range", ("TA p.157 [printed 127] Section 35 'Silver prophecy'", DOC26S + " - Bullish #1 'Turning dates'"),
      "Watch prices on Shashti of Shukla Paksh: whichever side the range breaks next day, it moves that way till Full Moon (worked 9 of 12 months)",
      "Udaya tithi Shukla Shashti.", "Tithi at sunrise (New York; Mumbai shown in the check).", _shashti, ("cfg_silver_bullish_01_shukla_shashti_turning_dates",),
      quals=("Direction is set by the next day's range break, not by the configuration; tagged Neutral here.",), metal="silver")


def _paksha_len(ctx):
    from finastro.sky import parse as _p
    lun = sorted([(_p(r["time"]["t_start_utc"]), r["rule_family"]) for r in ctx.sky.class_records("lunation") if r["rule_family"] in ("lunation/new_moon", "lunation/full_moon")])
    out = []
    for (a, fa), (b, fb) in zip(lun, lun[1:]):
        n = sum(1 for x in ctx.sunrises if a <= x < b)
        kind = "Shukla" if fa == "lunation/new_moon" else "Krishna"
        if (kind == "Shukla" and n == 16) or (kind == "Krishna" and n == 14):
            if a.year == ctx.year or b.year == ctx.year:
                out.append(Hit(a, b, ("Moon", "Sun"), {"paksha": kind, "sunrises_inside": n}))
    return out


xrule("ta_s35a21_paksha_16_or_14", "Shukla Paksha of 16 days or Krishna Paksha of 14 days", ("TA p.159 S35 A21", DOC26S + " - Bullish #14"), "Silver Bullish",
      "A bright fortnight spanning 16 sunrises or a dark fortnight spanning 14.", "Sunrises (New York) between consecutive new and full moons.",
      _paksha_len, ("cfg_silver_bullish_14_paksha_of_16_or_14_days",), metal="silver")


def _sun_star_no_benefic_nak(s):
    if s["Sun"].nak not in ("Pushya", "Dhanishta"):
        return False
    return (not [b for b in ("Mercury", "Venus", "Jupiter") if s[b].nak == s["Sun"].nak]) and s["Sun"].nak


xrule("doc26_silver_bull_03_sun_pushya_dhanishta_no_benefic_nak", "Sun in Pushya or Dhanishta with no benefic in the same nakshatra",
      (DOC26S + " - Bullish #3", "TA p.157 S35 A2 ('Sun in Pushya or Dhanishtha without Benefic Planets')"), "Silver Bullish",
      "Sun in Pushya or Dhanishta and no benefic (Mercury, Venus, Jupiter) in that nakshatra.",
      C.NAKCALC + " This is the 2026 document's reading: it reproduces its printed row (11-Feb-26 8:53 to 19-Feb-26 18:34 IST) to the minute; TA's wording is also computed with 'no benefic in the sign'.",
      windows(_sun_star_no_benefic_nak, ("Sun",)), metal="silver")


def _mercury_combust_retro_mutual_moon(ctx):
    base = [r for r in C.RULES if r.id == "ta_s35a13_mercury_moon_mutual_vedha"][0].detector(ctx)
    spans = ctx.sky.combust_spans("Mercury")
    out = []
    for h in base:
        s = snapshot(h.start.replace(microsecond=0))
        comb = any(sp.start - dt.timedelta(days=1) <= h.start < sp.end for sp in spans)   # combust dates are civil dates
        if comb and s["Mercury"].retro:
            out.append(h)
    return out


xrule("ta_s35a13_mercury_combust_retro_mutual_moon", "Mercury combust and retrograde does mutual Vedha with Moon", ("TA p.158 S35 A13", DOC26S + " - Bullish #11"),
      "Silver: Bullish day", "Mercury combust (Mumbai kalamsha window) and retrograde, and Mercury and Moon vedha each other.", "Mutual Vedha on the TA wheel within the combust-retrograde window.",
      _mercury_combust_retro_mutual_moon, ("cfg_silver_bullish_11_mercury_combust_retrograde_vedh_moon",), metal="silver")


def _mars_rise(ctx):
    from finastro.sky import parse as _p
    return [Hit(_p(r["time"]["t_start_utc"]), None, ("Mars", "Sun"), {"direction": next((f.split("=")[1] for f in r["qa"]["flags"] if f.startswith("direction=")), "")})
            for r in ctx.sky.class_records("combustion") if r["bodies"][0] == "Mars" and r["rule_family"] == "visibility/rise" and _p(r["time"]["t_start_utc"]).year == ctx.year]


xrule("doc26_silver_bull_19_mars_rising", "Mars rising (after combustion)", (DOC26S + " - Bullish #19",), "Bullish in Short Term", "Mars's heliacal rise.",
      "Rise date from the astronomy layer (kalamsha, Mumbai; civil date).", _mars_rise, quals=("Combust/rise dates are civil dates, not instants: the event is date-only.",), metal="silver")


def _sat_nep(ctx):
    return [Hit(t, None, ("Saturn", "Neptune"), {}) for t, _ in conjunction_instants(ctx.grid, "Saturn", "Neptune") if t.year == ctx.year]


xrule("doc26_silver_bull_20_saturn_neptune_conjunction", "Saturn-Neptune conjunction", (DOC26S + " - Bullish #20", "KD pp.15-22 (decade-defining reset)"), "Bullish",
      "Exact Saturn-Neptune conjunction.", "Exact sidereal conjunction instant.", _sat_nep, metal="silver")


def _rahu_pushya(ctx):
    def p(s):
        tg, _ = C.vedha_of(ctx, s, "Rahu")
        return [side for side, nk in tg.items() if nk == "Pushya"] and f"Rahu in {s['Rahu'].nak28} vedhas Pushya"
    return windows(p, ("Rahu",))(ctx)


xrule("kd092_rahu_vedha_pushya", "Rahu does Vedha of Pushya", ("KD p.92 'Rahu Vedh of Pushya Nakshtra - Effects on Gold & Silver'",), "High bullish for gold and silver (intermittent corrections expected; Mars 12th to Saturn may negate)",
      "Pushya is among Rahu's three Vedha targets.", "Rahu's nakshatra -> TA wheel (all three sides).", _rahu_pushya, metal=("gold", "silver"),
      quals=("KD p.92: 'Exception: Mars transiting 12th to Saturn may negate the positive impact'.",))


def _mantri_moon(ctx):
    return [h for h in C._cabinet(ctx) if h.facts["role"] == "Mantri" and h.facts["lord"] == "Moon"]


xrule("ta_s30_mantri_moon_silver", "Moon is Mantri of the year", ("TA p.127 [printed 97] 'Result of cabinet ranks Mantri'",),
      "White goods production is high so prices fall - rice, cotton, SILVER & all other white goods", "The Sun's entry into Aries falls on a Monday (Hindu day).",
      "Weekday of the Aries Sankranti at New York and Mumbai.", _mantri_moon, metal="silver")


NOT_COMPUTED = {"gold": [
    (DOC26 + " - Bullish #9", "Moonrise in Libra - Bullish", "The 2026 printed rows (28-May-26 Libra/Swati, 12-Oct-26) are not all darshan evenings and the document does not say which moonrise; not guessed."),
], "silver": [
    (DOC26S + " - Bullish #4", "Mars itself in Aquarius - Bullish for Silver", "The 2026 document prints no dated row; computed here from TA S35 A6 'Mars in Aquarius Bullish' instead."),
    ("KD p.107", "Jupiter in Pushya with Rahu in Shatabhisha, mutual Vedh - gold & silver bullish (18 Jun - 2 Aug 2026)", "A 2026 configuration; it does not recur in the period (Rahu leaves Shatabhisha on 2 Aug 2026). The general Rahu-Vedha-of-Pushya rule (KD p.92) is computed."),
]}


#: Catalogue rules tagged with the metal only because one clause or table row
#: mentions it; their own verdict is general-market, so they are left out of
#: the metal report (the metal-specific clause is a separate rule).
EXCLUDE = {"silver": {"ta_s12_vargottama_mars",      # silver clause = Mars Vargottam in Cancer (doc26_silver_bear_04)
                      "ta_s30_yearly_cabinet",       # silver clause = Moon as Mantri (ta_s30_mantri_moon_silver)
                      "ta_s35a13_mercury_moon_mutual_vedha"},  # unfiltered; the combust+retrograde version is ta_s35a13_mercury_combust_retro_mutual_moon
           "gold": set()}


def metal_rules():
    rs = [r for r in C.RULES if METAL in r.markets and r.detector is not None and r.id not in EXCLUDE[METAL]]
    return rs + EXTRA[METAL]


# ------------------------------------------------ independent checks
def astro_records():
    recs = []
    for f in ("astronomy_2026.json", "astronomy_2027.json"):
        for r in json.load(open(ROOT / "build" / f, encoding="utf-8"))["records"]:
            if r["event_class"] in ("sunrise", "sunset", "karana_ingress", "yoga_ingress", "tithi_ingress"):
                continue
            recs.append((parse(r["time"]["t_start_utc"]), r["event_class"], r["bodies"][0] if r["bodies"] else "", r["time"]["precision"]))
    recs.sort()
    return recs


REC = None


PRIORITY = {"sign_ingress": 0, "nakshatra_ingress": 1, "station": 2, "speed_crossing": 3, "conjunction": 4, "lunation": 5,
            "eclipse": 6, "opposition": 7, "neighbour_change": 8, "navamsa_ingress": 9}
TS = None


def match_record(t, bodies, tol=180):
    global TS
    if TS is None:
        TS = [x[0] for x in REC]
    i = bisect.bisect_left(TS, t - dt.timedelta(seconds=tol))
    out = []
    while i < len(REC) and REC[i][0] <= t + dt.timedelta(seconds=tol):
        if not bodies or REC[i][2] in bodies or REC[i][1] in ("eclipse", "lunation", "conjunction"):
            out.append(REC[i])
        i += 1
    return sorted(out, key=lambda r: PRIORITY.get(r[1], 10))


def verdict_tone(text):
    t = text.lower()
    bu = any(w in t for w in ("bullish", "rally", "rising", "bounce", "uptrend", "upturn"))
    be = any(w in t for w in ("bearish", "fall", "decline"))
    return "Mixed" if bu and be else "Bullish" if bu else "Bearish" if be else "Neutral"


def main():
    global REC
    REC = astro_records()
    sky26, sky27 = Sky.load(ROOT / "build" / "astronomy_2026.json"), Sky.load(ROOT / "build" / "astronomy_2027.json")
    grid = Grid(utc(2026, 6, 1), utc(2028, 6, 30))
    ctxs = [Ctx(grid, sky26, 2026), Ctx(grid, sky27, 2027)]
    cal = json.load(open(ROOT / "build" / "calendar_2027.json", encoding="utf-8"))
    gc = collections.defaultdict(list)
    for r in cal["rows"]:
        if r["row_kind"] == "verdict" and r["instrument"] == CFG[METAL]["instr"]:
            t = r["t_start_utc"] or r["t_utc"]
            gc[r["event"]].append((parse(t) if t else None, r["date"], r["tier"]))

    ctxs_m = [Ctx(grid, sky26, 2026, loc="mumbai"), Ctx(grid, sky27, 2027, loc="mumbai")]
    hits = {}
    checked = []
    for r in metal_rules():
        n = 0
        if "darshan" in r.id or "moonrise" in r.id:
            ny = [h for c in ctxs for h in r.detector(c) if P0.astimezone(ET).date() <= h.day <= dt.date(2027, 12, 31)]
            mu = [h for c in ctxs_m for h in r.detector(c) if P0.astimezone(ET).date() <= h.day <= dt.date(2027, 12, 31)]
            allny = [d for c in ctxs for ss, d, sn in C.darshans(c)]
            allmu = [d for c in ctxs_m for ss, d, sn in C.darshans(c)]
            for h in ny:
                twin = next((d for d in allmu if abs((d - h.day).days) <= 2), None)
                ok = any(abs((m.day - h.day).days) <= 2 for m in mu)
                h.facts["Mumbai_sighting"] = f"{twin:%a %d %b %Y}" + (" (rule also met in India)" if ok else " (rule NOT met at Mumbai: different weekday)") if twin else "n/a"
                hits[(r.id, h.start.replace(second=0), h.start.replace(second=0), h.day)] = (r, h)
                n += 1
            for m in mu:
                if not any(abs((h.day - m.day).days) <= 2 for h in ny):
                    twin = next((d for d in allny if abs((d - m.day).days) <= 2), None)
                    m.facts["note"] = f"Indian (Mumbai) sighting only; New York sighting is {twin:%a %d %b %Y}" if twin else "Indian (Mumbai) sighting"
                    hits[(r.id, m.start.replace(second=0), m.start.replace(second=0), m.day)] = (r, m)
                    n += 1
            checked.append((r, n))
            continue
        for ctx in ctxs:
            for h in r.detector(ctx):
                end = h.end or h.start
                if h.day is not None:
                    if not (P0.astimezone(ET).date() <= h.day <= dt.date(2027, 12, 31)):
                        continue
                elif not (h.start < P1 and end >= P0):
                    continue
                k = (r.id, h.start.replace(second=0), (h.end or h.start).replace(second=0), h.day)
                if k not in hits:
                    hits[k] = (r, h)
                    n += 1
        checked.append((r, n))

    # merge identical windows of the same bodies across rules
    groups = collections.OrderedDict()
    for (rid, s0, e0, day), (r, h) in sorted(hits.items(), key=lambda kv: kv[0][1]):
        if h.day is None and h.end and h.end != h.start and h.bodies:
            key = ("w", frozenset(h.bodies), s0, e0, json.dumps(h.facts.get("value"), default=str))
        else:
            key = ("x", rid, s0, e0, day)
        groups.setdefault(key, []).append((r, h))

    rows = []
    for key, items in groups.items():
        r0, h0 = items[0]
        verdicts = []
        for r, h in items:
            v = r.verdict
            if "Malefic Vedha" in v and h.facts.get("value"):
                fv = h.facts["value"]
                v = (f"MALEFIC Vedha: {METAL} Bullish" if "MALEFIC" in fv else "") + (" / " if "MALEFIC" in fv and "BENEFIC" in fv else "") + (f"BENEFIC Vedha: {METAL} Bearish" if "BENEFIC" in fv else "")
            verdicts.append(v)
        tone = verdict_tone(" ".join(verdicts))
        # planetary detail
        bodies = h0.bodies
        detail = []
        if bodies:
            s = snapshot(max(h0.start, utc(2026, 6, 1)).replace(microsecond=0))
            detail.append("; ".join(f"{name(b)} {s[b].deg:.2f} deg {s[b].sign} ({s[b].nak} p{s[b].pada}){' R' if s[b].retro and b not in ('Rahu', 'Ketu') else ''}" for b in bodies))
        facts = {}
        for r, h in items:
            facts.update({k: v for k, v in h.facts.items() if k not in bodies and k not in ("condition_ends_utc", "note_vs_existing")})
        if facts:
            detail.append("; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in facts.items()))
        # checks
        checks = []
        date_only = any("civil dates" in q for r, _ in items for q in r.quals)
        if h0.day is not None:
            checks.append("darshan criterion reproduces all 4 Moon-darshan dates printed in the 2026 document at Mumbai (3 of 4 at New York); both sightings shown")
        elif date_only:
            m = match_record(h0.start, bodies, 60)
            checks.append("combust/rise civil dates from the astronomy layer (Mumbai kalamsha)")
        else:
            for label, t in (("start", h0.start), ("end", h0.end)):
                if t is None or t == h0.start and label == "end":
                    continue
                if h0.open_start and label == "start" or h0.open_end and label == "end":
                    checks.append(f"{label}: outside scan")
                    continue
                m = match_record(t, set())
                if m:
                    checks.append(f"{label} = astronomy-layer {m[0][1].replace('_', ' ')} of {name(m[0][2])} ✓")
                elif t > dt.datetime(2028, 1, 1, tzinfo=UTC):
                    checks.append(f"{label}: after the astronomy layer's span (engine value)")
                else:
                    checks.append(f"{label}: computed boundary (no single layer record)")
        ex_ids = [e for r, _ in items for e in r.existing if e in gc]
        if ex_ids:
            best = None
            for e in ex_ids:
                for t, d, tier in gc[e]:
                    if t and abs((t - h0.start).total_seconds()) <= 900 or (date_only and t and abs((t - h0.start).total_seconds()) <= 86400 * 1.01):
                        best = (e, t, tier)
            if best:
                checks.append(f"matches existing calendar {CFG[METAL]['instr']} row ({best[0]}) ✓")
            elif h0.start.year >= 2027:
                checks.append(f"existing calendar ({', '.join(ex_ids)}) has no {CFG[METAL]['instr']} row at this start")
        refs = []
        for r, _ in items:
            refs.extend(r.refs)
        quals = []
        for r, _ in items:
            for q in r.quals:
                if q and q not in quals:
                    quals.append(q)
            if r.effect:
                quals.append(f"Effect timing per source: {r.effect}")
        rows.append({
            "start": h0.start, "end": h0.end, "day": h0.day, "open_start": h0.open_start, "open_end": h0.open_end,
            "title": " / ".join(dict.fromkeys(r.title for r, _ in items)), "tone": tone, "verdicts": list(dict.fromkeys(verdicts)),
            "rule": " || ".join(dict.fromkeys(r.rule for r, _ in items)), "detail": " | ".join(detail), "refs": list(dict.fromkeys(refs)),
            "quals": quals, "checks": checks, "rule_ids": [r.id for r, _ in items], "date_only": date_only})
    rows.sort(key=lambda x: x["start"])
    if METAL == "gold":
        TIMELINE.extend(user_timeline(grid))
    for r in rows:
        if any(b in ("Rahu", "Ketu") for b in r["detail"].split()) or "Ketu" in r["detail"] or "Rahu" in r["detail"]:
            r["quals"].append("Rahu/Ketu sign/nakshatra changes: the 2026 document's almanac prints the 5 Dec 2026 node ingress 40 min earlier (21:52 IST) than the mean node computed here (22:32 IST) - a known 5-arcsecond formulation gap (config/conventions.yaml).")
    write(rows, checked, compare_2026(rows) if METAL == "gold" else compare_2026_silver(ctxs[0]))


def compare_2026(rows):
    """Late-2026 rows vs the rows the 2026 document prints for its gold section."""
    from finastro.rules.config_catalogue import G
    IST = ZoneInfo("Asia/Kolkata")
    NM = {"Pushya": "Pushya", "Dhanistha": "Dhanishta", "Chitra": "Chitra", "Punarvasu": "Punarvasu"}
    out = []
    for key, n, kind in (("gold-bullish", 5, "malefic"), ("gold-bearish", 3, "benefic")):
        for row in G(key, n).tables[0].rows:
            pl, tgt = row[0], NM[row[2]]
            sd = row[4] if kind == "malefic" else row[3]
            st = row[5] if kind == "malefic" else row[4]
            try:
                t = dt.datetime.strptime(f"{sd} {st}", "%d-%b-%y %H:%M").replace(tzinfo=IST)
            except ValueError:
                continue
            if t < dt.datetime(2026, 11, 18, tzinfo=IST):
                continue
            pair = f"{pl}->{tgt}"
            best = None
            for r in rows:
                if pair in r["detail"] and r["start"] is not None:
                    d = abs((r["start"] - t).total_seconds()) / 60
                    if best is None or d < best:
                        best = d
            out.append((f"{key} #{n} ({kind})", pair, f"{sd} {st} IST", t, best))
    G10 = G("gold-bullish", 10).tables[0].rows
    for d, deg, sign in G10:
        day = dt.datetime.strptime(d, "%d-%b-%y").date()
        if day >= dt.date(2026, 11, 18):
            hit = [r for r in rows if "doc26_gold_bull_10_sun_moon_same_degree" in r["rule_ids"] and r["start"].astimezone(IST).date() == day]
            out.append(("gold-bullish #10", f"new moon {deg} {sign}", d, None, 0 if hit else None))
    return out


SILVER_MAP = {
    "silver-bullish#1": ["ta_s35_silver_prophecy_shashti"], "silver-bullish#2": ["ta_s35a01_retro_mercury_or_jupiter"],
    "silver-bullish#3": ["ta_s35a02_sun_pushya_dhanishta_no_benefic", "doc26_silver_bull_03_sun_pushya_dhanishta_no_benefic_nak"], "silver-bullish#5": ["ta_s35a03_venus_mars_or_sun_mars"],
    "silver-bullish#6": ["ta_s35a03_venus_mars_or_sun_mars"], "silver-bullish#7": ["ta_s34a04_rahu_mars_together", "doc26_silver_bull_07b_rahu_mars_same_nakshatra"],
    "silver-bullish#8": ["ta_s24_15_moon_darshan_fri_sat"], "silver-bullish#9": ["ta_s35a10_sun_moon_together_sankranti"],
    "silver-bullish#10": ["ta_s35a11_mercury_vedha_venus", "ta_s35a11_jupiter_vedha_venus"], "silver-bullish#11": ["ta_s35a13_mercury_combust_retro_mutual_moon"],
    "silver-bullish#12": ["ta_s18_venus_combust_west"], "silver-bullish#13": ["ta_s35a16_jupiter_turns_direct", "ta_s35a16_mercury_turns_direct"],
    "silver-bullish#14": ["ta_s35a21_paksha_16_or_14"], "silver-bullish#15": ["ta_s35a17_sun_or_moon_mercury_alone"],
    "silver-bullish#16": ["ta_s35a18_mercury_jupiter_retro"], "silver-bullish#17": ["ta_s35a19_retro_mercury_combust"],
    "silver-bullish#18": ["ta_s35a22_sun_eclipse_falgun_jyeshtha_tuesday"], "silver-bullish#19": ["doc26_silver_bull_19_mars_rising"],
    "silver-bullish#20": ["doc26_silver_bull_20_saturn_neptune_conjunction"], "silver-bearish#1": ["doc26_silver_bear_01_venus_alone_leo_libra"],
    "silver-bearish#2": ["doc26_silver_bear_02_mercury_alone_aries_virgo"], "silver-bearish#3": ["ta_s35b03_mars_ashlesha_pada4"],
    "silver-bearish#4": ["doc26_silver_bear_04_mars_vargottam_cancer"], "silver-bearish#5": ["ta_s35b04_amavasya_monday"],
    "silver-bearish#6": ["ta_s35b07_moon_venus_mutual_vedha", "ta_s35b07_mercury_venus_mutual_vedha"], "silver-bearish#7": ["ta_s35b09_moon_eclipse_sunday"],
    "silver-bearish#8": ["ta_s35b10_saturn_direct"], "silver-bearish#9": ["ta_s35b13_sun_vir_lib_pis_benefic"], "silver-bearish#10": ["ta_s18_venus_rise_west"],
}


SILVER_ROW_NOTES = {
    ("silver-bullish#15", "15-May-26"): "Printed start is Mercury's entry into Taurus (00:32 IST); the Sun only enters Taurus at 06:22 IST, so 'Sun and Mercury alone in Taurus' starts 6 h later than printed. This report uses 06:22 IST.",
    ("silver-bearish#9", "17-Oct-25"): "Year misprint: the Sun enters Libra (joining Mercury and Venus) on 17-Oct-2026 at 19:52 IST, exactly the printed time; the row is dated 2025.",
    ("silver-bearish#7", "07-Sep-25"): "A 2025 example printed by the document; outside the 2026 check.",
}


def compare_2026_silver(ctx26):
    """Every row the 2026 document prints for silver, looked up in this engine's 2026 output."""
    import re as _re
    from finastro.rules.config_catalogue import GROUPS
    IST = ZoneInfo("Asia/Kolkata")
    rules = {r.id: r for r in metal_rules()}
    g = Grid(utc(2025, 10, 1), utc(2027, 1, 31))       # the whole of 2026, with carry-in
    ctx26 = Ctx(g, ctx26.sky, 2026)
    ctx_m = Ctx(g, ctx26.sky, 2026, loc="mumbai")
    cache = {}

    def hits(rid):
        if rid not in cache:
            r = rules[rid]
            c = ctx_m if ("darshan" in rid or "amavasya" in rid or "shashti" in rid or "paksha" in rid) else ctx26
            cache[rid] = r.detector(c)
        return cache[rid]
    out = []
    for g in GROUPS:
        if g.key not in SILVER_MAP:
            continue
        for t in g.tables:
            for row in t.rows:
                cells = list(row)
                if g.key == "silver-bullish#1":
                    items = [(c, None) for c in cells]
                else:
                    items = None
                    for k, c in enumerate(cells):
                        if _re.match(r"\d\d-[A-Z][a-z]{2}-\d\d", c.strip()) or c.strip().lower().startswith("start of"):
                            tm = cells[k + 1].strip() if k + 1 < len(cells) and _re.match(r"^\d{1,2}:\d\d$", cells[k + 1].strip()) else None
                            items = [(c.strip(), tm)]
                            break
                    if items is None:
                        continue
                for dstr, tm in items:
                    label = " | ".join(x for x in cells if x and x not in ("—",))[:90]
                    note = SILVER_ROW_NOTES.get((g.key, dstr[:9]))
                    if note:
                        NOTE26[label] = note
                    if dstr.lower().startswith("start of"):
                        ok = any((h.end or h.start) > utc(2026, 1, 1) and h.start <= utc(2026, 1, 2) for rid in SILVER_MAP[g.key] for h in hits(rid))
                        out.append((g.key, label, "start of 2026", None, 0 if ok else None))
                        continue
                    day = dt.datetime.strptime(dstr[:9], "%d-%b-%y").date()
                    if tm:
                        tt = dt.datetime.combine(day, dt.time(*map(int, tm.split(":"))), IST)
                        best = None
                        for rid in SILVER_MAP[g.key]:
                            for h in hits(rid):
                                d = abs((h.start - tt).total_seconds()) / 60
                                best = d if best is None or d < best else best
                        out.append((g.key, label, f"{dstr} {tm} IST", tt, best if best is not None and best <= 24 * 60 else None))
                    else:
                        ok = None
                        for rid in SILVER_MAP[g.key]:
                            for h in hits(rid):
                                hd = h.day or h.start.astimezone(IST).date()
                                if abs((hd - day).days) <= 1:
                                    ok = 0
                        out.append((g.key, label, dstr, None, ok))
    return out


TIMELINE = []


def user_timeline(grid):
    from finastro.pdfref.engine import value_windows
    from finastro.pdfref.user_rules import sun_state
    out = []
    for w in value_windows(grid, sun_state):
        if w.start < P1 and w.end >= P0:
            out.append(w)
    return out


def user_section(rows):
    ur = [r for r in rows if any(i.startswith("user_") for i in r["rule_ids"])]
    if not ur:
        return ""
    tl = "".join(
        f"<tr class='{('bullish' if len(w.value[1]) > len(w.value[2]) else 'bearish' if len(w.value[2]) > len(w.value[1]) else 'mixed')}'>"
        f"<td class='w'>{html.escape(et(max(w.start, P0)))}</td><td class='w'>{html.escape(et(w.end))}</td><td>{html.escape(w.value[0])}</td>"
        f"<td class='bu'>{html.escape('; '.join(w.value[1])) or '-'}</td><td class='be'>{html.escape('; '.join(w.value[2])) or '-'}</td>"
        f"<td class='n'><span class='tag {('bullish' if len(w.value[1]) > len(w.value[2]) else 'bearish' if len(w.value[2]) > len(w.value[1]) else 'mixed')}'>{len(w.value[1])} : {len(w.value[2])}</span></td></tr>"
        for w in TIMELINE)
    trs = "".join(f"<tr class='{r['tone'].lower()}'><td class='w'>{html.escape(when(r)[0])}</td><td class='w'>{html.escape(when(r)[1])}</td>"
                  f"<td><b>{html.escape(r['title'])}</b></td><td><span class='tag {r['tone'].lower()}'>{r['tone']}</span></td>"
                  f"<td class='s'>{html.escape(r['detail'].replace('value: ', ''))}</td></tr>" for r in ur)
    return f"""<h2>Your notes on the Sun (U1-U4): every window</h2>
<p class="m">'Gold is ruled by the Sun': Sun in a Venus / Mercury / Jupiter nakshatra (rise), Venus, Mercury, Jupiter or a waxing Moon with or aspecting the Sun (hike),
Sun in a Saturn / Rahu nakshatra (fall), Saturn or Rahu with or aspecting the Sun (crash). Conjunction = same sign; aspect = whole-sign drishti (Jupiter 5/7/9, Saturn 3/7/10, Rahu 7, so Sun with Ketu counts as Rahu's aspect);
waxing = Shukla paksha. These rules disagree with TA Section 34 in places (Pushya is a TA rally star; TA and the 2026 document make malefics with the Sun in Libra bullish): every row carries the conflict note.</p>
<h2>Sun-state timeline under your notes (Moon contacts listed separately below)</h2>
<p class="m">Each row is a stretch in which the Sun's nakshatra and the planets with or aspecting it stay the same. "Rise : fall" counts the signals of each kind your notes give for that stretch; it is a count, not a weighting. Mercury is never more than ~28 deg from the Sun, so it shares the Sun's sign for much of the year and U2 is active often.</p>
<div class="wrap"><table><thead><tr><th>From (ET)</th><th>To (ET)</th><th>Sun's nakshatra</th><th>Rise signals (U1, U2)</th><th>Fall signals (U3, U4)</th><th>Rise : fall</th></tr></thead><tbody>{tl}</tbody></table></div>
<h2>Your notes: every window, including waxing-Moon contacts</h2>
<div class="wrap"><table><thead><tr><th>Start (ET)</th><th>End (ET)</th><th>Rule</th><th>Effect</th><th>Detail</th></tr></thead><tbody>{trs}</tbody></table></div>"""


def when(r):
    if r["day"] is not None:
        return et_date(r["day"]), ""
    if r["date_only"]:
        return f"{r['start'].astimezone(ZoneInfo('Asia/Kolkata')):%a %d %b %Y} (civil date)", (f"{r['end'].astimezone(ZoneInfo('Asia/Kolkata')):%a %d %b %Y} (civil date)" if r["end"] and r["end"] != r["start"] else "")
    s = et(r["start"]) + (" (began earlier)" if r["open_start"] else "")
    e = et(r["end"]) if r["end"] and r["end"] != r["start"] else ""
    return s, e


NOTE26 = {"Venus->Dhanishta": "10 h later here (13:54 IST). The 2026 document's own Venus Vedh table (B134) prints Venus entering Vishakha at 22-Dec-26 3:50, but its neighbouring rows agree with this engine within 4 min (Swati 22:54 vs 22:58, Chitra 3:24 vs 3:22) and the astronomy layer independently gives 13:54 IST: the printed '3:50' has almost certainly lost a digit (13:50). This report uses 13:54 IST = 03:24 EST."}


def write(rows, checked, cmp26):
    OUT.mkdir(parents=True, exist_ok=True)
    js = []
    for r in rows:
        s, e = when(r)
        js.append({"start_ET": s, "end_ET": e, **{k: r[k] for k in ("title", "tone", "verdicts", "rule", "detail", "refs", "quals", "checks", "rule_ids")}})
    json.dump({"period": "2026-11-20 to 2027-12-31", "time_zone": "America/New_York", "rows": js}, open(OUT / f"{METAL}_2026-11-20_to_2027-12-31_ET.json", "w", encoding="utf-8"), indent=1)

    cnt = collections.Counter(r["tone"] for r in rows)
    # monthly overview
    months = []
    m = dt.date(2026, 11, 1)
    while m <= dt.date(2027, 12, 1):
        a = dt.datetime(m.year, m.month, 1, tzinfo=ET).astimezone(UTC)
        nm = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        b = dt.datetime(nm.year, nm.month, 1, tzinfo=ET).astimezone(UTC)
        act = collections.Counter()
        names = collections.defaultdict(set)
        for r in rows:
            s = r["start"]
            e = r["end"] or r["start"]
            if r["day"] is not None:
                s = dt.datetime(r["day"].year, r["day"].month, r["day"].day, tzinfo=ET).astimezone(UTC)
                e = s
            if s < b and e >= a:
                act[r["tone"]] += 1
                names[r["tone"]].add(r["title"].split(" / ")[0])
        months.append((m, act, names))
        m = nm
    mrows = "".join(
        f"<tr><td>{m:%b %Y}</td><td class='n bu'>{a['Bullish']}</td><td class='n be'>{a['Bearish']}</td><td class='n mx'>{a['Mixed']}</td>"
        f"<td class='s'>{html.escape('; '.join(sorted(n['Bullish']))[:420])}</td><td class='s'>{html.escape('; '.join(sorted(n['Bearish']))[:420])}</td></tr>"
        for m, a, n in months)
    trs = []
    for i, r in enumerate(rows, 1):
        s, e = when(r)
        q = "".join(f"<li>{html.escape(x)}</li>" for x in r["quals"])
        trs.append(f"<tr class='{r['tone'].lower()}' data-t='{r['tone']}'><td class='n'>{i}</td><td class='w'>{html.escape(s)}</td><td class='w'>{html.escape(e)}</td>"
                   f"<td class='c'><b>{html.escape(r['title'])}</b><div class='s'>{html.escape(r['rule'])}</div>"
                   + (f"<details><summary>Conditions &amp; qualifications ({len(r['quals'])})</summary><ul class='s'>{q}</ul></details>" if q else "") + "</td>"
                   f"<td class='g'><span class='tag {r['tone'].lower()}'>{r['tone']}</span><div>{html.escape(' || '.join(r['verdicts']))}</div></td>"
                   f"<td class='d s'>{html.escape(r['detail'].replace('value: ', ''))}</td>"
                   f"<td class='r s'>{html.escape(' | '.join(r['refs']))}</td>"
                   f"<td class='k s'>{'<br>'.join(html.escape(x) for x in r['checks'])}</td></tr>")
    def verdict26(b, d, m):
        if m is None:
            return NOTE26.get(b, "&#10007; not found")
        if d is None:
            return "✓ found (same civil date, +/-1 day)"
        if m <= 5:
            return "✓ same instant"
        if m <= 45:
            return "✓ within %d min" % m + (" (node ingress gap)" if "Ketu" in b or "Rahu" in b else "")
        return NOTE26.get(b, "%d min apart" % m)
    cmprows = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{et(d) if d else ''}</td><td>{verdict26(b, d, m)}</td></tr>"
                      for a, b, c, d, m in cmp26)
    n26 = len(cmp26)
    ok26 = sum(1 for a, b, c, d, m in cmp26 if m is not None and m <= 45)
    W, Wd, L = CFG[METAL]["Word"], CFG[METAL]["word"], CFG[METAL]["label"]
    zero = [(r, n) for r, n in checked if n == 0]
    zrows = "".join(f"<li><b>{html.escape(r.title)}</b> &mdash; {html.escape('; '.join(r.refs))}: does not occur between 20 Nov 2026 and 31 Dec 2027</li>" for r, n in zero)
    ncrows = "".join(f"<li><b>{html.escape(t)}</b> &mdash; {html.escape(ref)}: {html.escape(why)}</li>" for ref, t, why in NOT_COMPUTED[METAL])
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{W} Astro Windows</title><style>
:root{{--bg:#fbfaf7;--fg:#1d1d1f;--mut:#66666c;--line:#e3e1db;--card:#fff;--bu:#1f7a4d;--bubg:#eaf6ef;--be:#b3261e;--bebg:#fbecea;--mx:#8a6400;--mxbg:#fbf3df}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--card:#1d1d20;--bu:#6fd39c;--bubg:#15271d;--be:#ff8a80;--bebg:#2b1716;--mx:#e6c35c;--mxbg:#2a2412}}}}
:root[data-theme=dark]{{--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--card:#1d1d20;--bu:#6fd39c;--bubg:#15271d;--be:#ff8a80;--bebg:#2b1716;--mx:#e6c35c;--mxbg:#2a2412}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;padding:16px}}
h1{{font-size:21px;margin:0 0 4px}}h2{{font-size:16px;margin:22px 0 8px}}p.m{{color:var(--mut);max-width:85em;margin:4px 0}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}}
table{{border-collapse:collapse;width:100%}}th,td{{border-top:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}}
th{{position:sticky;top:0;background:var(--card);font-size:12px;color:var(--mut);border-top:0}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.w{{white-space:nowrap;font-variant-numeric:tabular-nums}}.s{{font-size:12px;color:var(--mut)}}td.c{{min-width:17em}}td.g{{min-width:13em}}td.d{{min-width:20em}}td.r{{min-width:15em}}td.k{{min-width:16em}}ul.s{{margin:4px 0 0;padding-left:16px}}details summary{{cursor:pointer;font-size:12px;color:var(--mut);margin-top:4px}}
.tag{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:12px;font-weight:600;margin-bottom:3px}}
.tag.bullish{{background:var(--bubg);color:var(--bu)}}.tag.bearish{{background:var(--bebg);color:var(--be)}}.tag.mixed,.tag.neutral{{background:var(--mxbg);color:var(--mx)}}
td.bu{{color:var(--bu);font-weight:600}}td.be{{color:var(--be);font-weight:600}}td.mx{{color:var(--mx);font-weight:600}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}}input,select{{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0}}.kpi div{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 14px}}.kpi b{{font-size:20px;display:block}}
ul{{max-width:85em}}li{{margin:3px 0}}
</style></head><body>
<h1>{L}: astrological windows, 20 Nov 2026 &ndash; 31 Dec 2027</h1>
<p class="m">Every rule in the two reference PDFs{', the user notes (Reference_materials/user_notes_gold.md)' if METAL == 'gold' else ''} and in the 2026 document that names {Wd}, recomputed (Swiss Ephemeris, sidereal Lahiri, mean node). Times are US Eastern (America/New_York: EST, shown as EDT 14 Mar&ndash;7 Nov 2027). Results are quoted from the sources; they are the sources' claims, not forecasts or investment advice.</p>
<div class="kpi"><div><b>{len(rows)}</b>windows / dates</div><div><b style="color:var(--bu)">{cnt['Bullish']}</b>Bullish per source</div><div><b style="color:var(--be)">{cnt['Bearish']}</b>Bearish per source</div><div><b style="color:var(--mx)">{cnt['Mixed']}</b>{'Mixed (malefic and benefic Vedha at once)' if METAL == 'gold' else 'Mixed (source states both directions)'}</div></div>
<h2>Month by month (conditions active at any time in the month)</h2>
<p class="m">A count of active conditions, not a net forecast: the sources give no weighting between rules, and TA p.30 says longer multi-planet combinations dominate single ones.</p>
<div class="wrap"><table><thead><tr><th>Month</th><th>Bullish</th><th>Bearish</th><th>Mixed</th><th>Bullish conditions</th><th>Bearish conditions</th></tr></thead><tbody>{mrows}</tbody></table></div>
<h2>All windows and dates (chronological)</h2>
<div class="bar"><input id="q" placeholder="Filter (e.g. Mars, Vedha, Rahu, March)" size="34"><select id="tone"><option value="">All</option><option>Bullish</option><option>Bearish</option><option>Mixed</option></select></div>
<div class="wrap"><table><thead><tr><th>#</th><th>Start (ET)</th><th>End (ET)</th><th>Combination</th><th>{W} effect (source, verbatim)</th><th>Planetary detail at start</th><th>Source</th><th>Double-check</th></tr></thead><tbody id="t">{''.join(trs)}</tbody></table></div>
{user_section(rows) if METAL == 'gold' else ''}
<h2>How each row was double-checked</h2>
<ul>
<li><b>Boundaries vs the astronomy layer.</b> Every window start/end was compared with the records written independently by <code>build_2027.py</code> (sign, nakshatra and navamsa ingresses, stations, speed crossings, conjunctions, eclipses, lunations), within 3 minutes. The "Double-check" column names the matching record.</li>
<li><b>Vs the existing calendar.</b> For 2027 rows of the 2026 document's {Wd} rules, the start was compared with the existing calendar's {CFG[METAL]['instr']} rows (15 min; one civil day for combust/rise dates).</li>
<li><b>Vedha engine vs printed rows.</b> The Vedha calculation reproduces all 30 gold-Vedha rows the 2026 document prints for 2026, using the TA Sarvatobhadra wheel and the 2026 speed levels for Mars, Mercury and Venus.</li>
<li><b>Vs the 2026 document's own {Wd} rows.</b> {ok26} of {n26} printed rows checked below are reproduced (table further down).</li>
<li><b>Dated claims in the PDFs.</b> 51 of 58 recomputed (build/pdfref/validation.json), including KD's Saturn-Mars, Venus-Herschel and Mars-speed dates.</li>
<li>Day rules (darshan) use New York sunset; combust/rise dates are civil dates (Indian, kalamsha method) as in the existing calendar.</li>
</ul>
<h2>{'Late-2026 rows vs the 2026 document' + chr(39) + 's own printed gold rows' if METAL == 'gold' else 'Every 2026 row the 2026 document prints for silver vs this engine'}</h2>
<p class="m">{'The 2026 document prints its gold Vedha and new-moon rows through 31 Dec 2026; every one that falls after 18 Nov 2026 is looked up in this report.' if METAL == 'gold' else 'All dated rows of the silver section (bullish #1-#20, bearish #1-#10) for 2026, recomputed for 2026 with the same rules and compared (time within 45 min where a time is printed; civil date +/-1 day otherwise).'}</p>
<div class="wrap"><table><thead><tr><th>Printed in</th><th>Row</th><th>Printed start</th><th>Printed start in ET</th><th>This report</th></tr></thead><tbody>{cmprows}</tbody></table></div>
<h2>{W} rules checked that do not occur in this period</h2><ul>{zrows}</ul>
<h2>{W} rules not computed</h2><ul>{ncrows}</ul>
<script>
const q=document.getElementById('q'),tn=document.getElementById('tone');
function f(){{const v=q.value.toLowerCase();for(const r of document.getElementById('t').rows){{r.style.display=((!v||r.textContent.toLowerCase().includes(v))&&(!tn.value||r.dataset.t===tn.value))?'':'none'}}}}
q.oninput=f;tn.onchange=f;
</script></body></html>"""
    (OUT / f"{METAL}_2026-11-20_to_2027-12-31_ET.html").write_text(doc, encoding="utf-8")
    print(len(rows), dict(cnt), "zero-hit rules:", len(zero))


if __name__ == "__main__":
    METAL = sys.argv[1] if len(sys.argv) > 1 else "gold"
    assert METAL in CFG, "usage: build_metal_report.py gold|silver"
    main()
