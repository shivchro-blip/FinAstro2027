"""Catalogue of rules read from the two reference PDFs.

Every entry names its page(s), quotes the source's result, carries the
source's bottom-of-table notes as qualifications, and says how the date is
computed. `existing` names calendar rules (finastro/rules, 2026 source) that
state the same condition: those are NOT re-emitted as new events -- the
builder annotates the existing event with this entry's source text and uses
our own recomputation only as a cross-check.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .detect import (DAY_LORDS, INDRA, NAK_LORD, POOL, VAIDHRITI, VYATIPATA,
                     WEEKDAYS, Hit, aspects, both_direct, conjunctions, daily,
                     entries, sign_rel, tithi_label, windows)
from .engine import NAKS, NORMAL_SPEED, SIGNS, name, snapshot
from . import vedha as V

TA = "TA"   # Tech Astro Analysis (2020) PDF
KD = "KD"   # KD Final PPT PDF 2026


@dataclass
class Rule:
    id: str
    title: str
    refs: tuple            # ("TA p.80 [printed 50] S24 #23", ...)
    verdict: str           # the source's result, verbatim where printed
    markets: tuple         # general / gold / silver / sugar / grains / sector:...
    rule: str              # the condition, stated
    calc: str              # how the date is computed
    detector: object = None
    quals: tuple = ()      # bottom notes, conditions, reliability statements
    tier: str = "major"    # major | moon (Moon-only, source says low reliability) | yearly
    existing: tuple = ()   # calendar rule ids stating the same condition
    effect: str = ""       # timing of the effect as the source states it


RULES: list[Rule] = []
NOT_COMPUTABLE: list[dict] = []


def rule(**kw):
    r = Rule(**kw)
    RULES.append(r)
    return r


def nc(ref, text, reason):
    NOT_COMPUTABLE.append({"ref": ref, "rule": text, "reason": reason})


H = "Uranus"   # the sources' Herschel
BEN = V.BENEFIC                 # TA p.137: Moon, Mercury, Jupiter, Venus
MAL = V.MALEFIC                 # TA p.137: Sun, Mars, Saturn, Rahu, Ketu
GRAHA_MAL = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
GRAHA_BEN = ("Mercury", "Jupiter", "Venus")
REL_NAME = {1: "conjunction (same sign)", 2: "2/12 (Dwidwadash)",
            3: "3/11 (Trikadash)", 4: "4/10 (Kendra)", 5: "5/9 (Trine)",
            6: "6/8 (Shadashtak)", 7: "7th (opposition)"}
PAIR_HOUSES = {1: (1,), 2: (2, 12), 3: (3, 11), 4: (4, 10), 5: (5, 9),
               6: (6, 8), 7: (7,)}

# TA p.41-44 (printed 11-14): sign-pair classes for 2/12 and 6/8 yogs.
DWI_BULL = {frozenset(p) for p in (("Aries", "Pisces"), ("Taurus", "Gemini"),
            ("Cancer", "Leo"), ("Virgo", "Libra"), ("Scorpio", "Sagittarius"),
            ("Capricorn", "Aquarius"))}
DWI_BEAR = {frozenset(p) for p in (("Libra", "Scorpio"), ("Sagittarius", "Capricorn"),
            ("Aquarius", "Pisces"), ("Aries", "Taurus"), ("Gemini", "Cancer"),
            ("Leo", "Virgo"))}
SHA_BULL = {frozenset(p) for p in (("Aries", "Scorpio"), ("Taurus", "Libra"),
            ("Gemini", "Capricorn"), ("Cancer", "Sagittarius"), ("Leo", "Pisces"),
            ("Virgo", "Aquarius"))}
SHA_BEAR = {frozenset(p) for p in (("Aries", "Virgo"), ("Taurus", "Sagittarius"),
            ("Gemini", "Scorpio"), ("Cancer", "Aquarius"), ("Leo", "Capricorn"),
            ("Libra", "Pisces"))}


def pair_class(sa: str, sb: str) -> str | None:
    k = frozenset((sa, sb))
    if k in DWI_BULL:
        return "TA S4 p.41: Auspicious-Bullish 2/12 sign pair"
    if k in DWI_BEAR:
        return "TA S4 p.42: Inauspicious-Bearish 2/12 sign pair"
    if k in SHA_BULL:
        return "TA S5 p.43: Auspicious-Bullish 6/8 sign pair"
    if k in SHA_BEAR:
        return "TA S5 p.44: Inauspicious-Bearish 6/8 sign pair"
    return None


def rel_facts(a, b):
    def f(s, w):
        out = {"signs": f"{name(a)} in {s[a].sign}, {name(b)} in {s[b].sign}",
               "motion": f"{name(a)} {'R' if s[a].retro else 'D'}, {name(b)} {'R' if s[b].retro else 'D'}",
               "both_direct": both_direct(s, a, b)}
        pc = pair_class(s[a].sign, s[b].sign)
        if pc:
            out["sign_pair_class"] = pc
        return out
    return f


# ======================================================================
# TA Section 25 (pp.88-115, printed 58-85): RELATIONSHIP EFFECT OF EACH PLANET
# WITH OTHER. Keys: 1 together, 7 seventh, 6 = 6/8, 5 = 5/9, 3 = 3/11,
# 2 = 2/12, 4 = 4/10. Text verbatim from the page images.
# ======================================================================
S25 = {
    ("Sun", "Moon", 88): {1: "Bullish if tithi happen to be Amavasya else Bearish", 7: "Volatile with Bearish tone", 6: "Bullish", 5: "Bearish", 3: "Bearish", 2: "Bearish", 4: "Flat & turns Bullish"},
    ("Sun", "Mars", 88): {1: "Mild Bearish", 7: "Sudden fall", 6: "High volatile both side", 5: "Good Bullish", 3: "Flat Market with mild volatility", 2: "Anyside dubious", 4: "Bearish"},
    ("Sun", "Jupiter", 89): {1: "Bearish", 7: "Bearish", 6: "Volatile", 5: "Depends on house they are placed", 3: "Flat after 2 way move", 2: "Flat", 4: "Bearish"},
    ("Sun", "Venus", 90): {1: "Bullish", 3: "Marginal moves", 2: "Depends upon house they are placed", 4: "Bullish (other yog not possible)"},
    ("Sun", "Saturn", 90): {1: "Bearish", 7: "Bearish", 6: "Both side ends with flat", 5: "Bullish", 3: "Volatile with flat end", 2: "Depend upon where they placed", 4: "Mild Bearish"},
    ("Sun", "Rahu", 91): {1: "Bearish", 7: "Bearish", 6: "Volatile", 5: "Bullish", 3: "flat after two way move", 2: "flat to Bullish", 4: "Check"},
    ("Sun", H, 92): {1: "Slow move to flat", 7: "Bearish", 6: "Bearish", 5: "Bullish", 3: "Bullish", 2: "Flat to positive", 4: "Bearish"},
    ("Sun", "Neptune", 92): {1: "Big high / lows do happen here", 7: "Big high / lows happen here", 6: "Positive than flat", 5: "Bullish", 3: "Mild both way move", 2: "Not much impact", 4: "Mild fall"},
    # p.93 prints the heading "SUN WITH MARS" a second time; it sits between
    # Sun-Neptune and Moon-Mercury, so it is read as MOON WITH MARS (see
    # REFERENCE_PDF_RULES.md, conflicts).
    ("Moon", "Mars", 93): {1: "Bullish", 7: "Bullish", 6: "Bearish", 5: "Bearish", 3: "Both side moves", 2: "Both side moves", 4: "After mild fall sudden big upmove"},
    ("Moon", "Mercury", 94): {1: "Small both side", 7: "Bearish", 6: "Bullish", 5: "Bullish", 3: "Bearish", 2: "Mild Bearish", 4: "Mild Bullish"},
    ("Moon", "Jupiter", 94): {1: "Bearish", 7: "Bearish", 6: "Bearish", 5: "Bearish", 3: "Bullish", 2: "Both side volatile", 4: "Bullish"},
    ("Moon", "Venus", 95): {1: "Bearish", 7: "Bearish", 6: "Bearish", 5: "First small fall than sudden upmove", 3: "Bearish", 2: "Mild fall than sudden spurt", 4: "If Venus Combust or Retrograde than Bearish else flat"},
    ("Moon", "Saturn", 96): {1: "Bullish", 7: "If Moon 5 deg behind / 10 deg above Bullish else flat", 6: "Bearish", 5: "Bearish start 12 deg ahead of Trine", 3: "Bullish", 2: "Bearish 12 deg ahead of Dwidwadash", 4: "Start with flat ends with Bullish"},
    ("Moon", "Rahu", 96): {1: "Bullish", 7: "Bullish", 6: "Bullish", 5: "Bullish", 3: "Bullish", 2: "Flat", 4: "Flat after volatile"},
    ("Moon", H, 97): {1: "Bullish", 7: "Both side volatile", 6: "Sudden spurt", 5: "Bullish", 3: "Bullish", 2: "Flat ends with fall", 4: "Bearish"},
    ("Moon", "Neptune", 97): {1: "Mild volatile ends flat", 7: "First fall than sudden spurt", 6: "First fall than sudden spurt", 5: "Good Bullish", 3: "Sudden Bullish", 2: "First bullish ends with fall", 4: "Very bullish"},
    ("Mars", "Mercury", 98): {1: "Bullish & extreme Bullish if Mercury(R) or Combust", 7: "Bullish", 6: "Flat but if Mercury(R) than Bullish", 5: "Bullish", 3: "Usually flat but Bullish sometime", 2: "Flat after 2 way moves", 4: "Bearish"},
    ("Mars", "Jupiter", 99): {1: "Bearish but Bullish if high speed", 7: "Bullish", 6: "6 - Flat, 8 - Bullish", 5: "Bearish", 3: "Very range bound", 2: "Too small range", 4: "4 - Bullish, 10 - Bearish"},
    ("Mars", "Venus", 99): {1: "1 side Bullish", 7: "Bearish", 6: "Bullish after sharp fall", 5: "Very volatile", 3: "Bullish", 2: "Range bound", 4: "After start with dip big spurt"},
    ("Mars", "Saturn", 100): {1: "Bullish & very Bullish if in Bullish Sign", 7: "Bullish", 6: "Range bound", 5: "Bullish", 3: "First fall than rally", 2: "Very Dubious very bad Bearish", 4: "Bullish"},
    ("Mars", "Rahu", 101): {1: "Bearish", 7: "Bearish", 6: "Small range", 5: "Good bounce", 3: "Both side volatile", 2: "Volatile ends flat", 4: "Bearish"},
    ("Mars", H, 101): {1: "Flat ends Bearish", 7: "Fall", 6: "Mild Bearish", 5: "Bullish", 3: "Bullish", 2: "Move both ways but Bullish", 4: "Bearish sometime heavy fall"},
    ("Mercury", "Jupiter", 102): {1: "Bullish", 7: "Bearish", 6: "Small range", 5: "Bearish", 3: "Bullish", 2: "Mild Bullish", 4: "Strong Bearish"},
    ("Mercury", "Venus", 103): {1: "Dealt in separate post", 2: "Sudden Bullish", 3: "Bullish but strong Bullish if Debilitated", 4: "Sudden fall"},
    ("Mercury", "Saturn", 103): {1: "High volatile after range bound", 7: "Bearish", 6: "Mild up move after range bound", 5: "Bullish", 3: "Very Bullish", 2: "Very mild Bullish", 4: "Bearish"},
    ("Mercury", "Rahu", 104): {1: "Bearish", 7: "No impact", 6: "If Mercury Combust Bullish else Bearish", 5: "Bullish", 3: "Bullish", 2: "Mild decline", 4: "Bearish"},
    ("Mercury", H, 104): {1: "Very good upmove if Direct else mild", 7: "Bearish if Direct & Bullish if Retro", 6: "No impact", 5: "Sudden big upmove", 3: "Simply superb Bullish", 2: "Bullish", 4: "Bearish"},
    ("Mercury", "Neptune", 105): {1: "Sudden big spurt", 7: "Simple fall", 6: "No impact", 5: "Bullish", 3: "Both side volatile", 2: "Flat", 4: "Bearish but Bullish if Retro"},
    ("Jupiter", "Venus", 106): {1: "Bullish but Bearish if anyone Retro", 7: "Bearish but Bullish if Retro", 6: "Very small movement", 5: "Bullish but Bearish if Retro", 3: "Bullish but Bearish if Retro", 2: "Mild Bullish", 4: "Bullish"},
    ("Jupiter", "Saturn", 106): {1: "Very Bullish if both Direct", 7: "Bearish", 6: "Bullish if both Planet Direct", 5: "Bearish & decline comes when Jupiter Direct", 3: "If Jupiter 4th Bearish & if Jupiter 10th than Bearish", 2: "Mild Bullish", 4: "Bullish"},
    ("Jupiter", "Rahu", 107): {1: "Bullish but its Bearish if Jupiter is Retrograde", 7: "Bearish but its Bullish if Retrograde", 6: "No impact", 5: "Very Bullish if Direct & not Combust", 3: "Big fall", 2: "Mild Bullish", 4: "Good Bullish"},
    ("Jupiter", H, 108): {1: "Very good Bullish", 7: "Good Bearish", 6: "Bullish if none of them Retro", 5: "Very Bullish", 3: "Both side market with negative bias", 2: "Mild Bullish", 4: "Mild Bearish but Bullish if Jupiter ahead"},
    ("Jupiter", "Neptune", 108): {1: "Very good Bullish", 7: "Good Bearish", 6: "Bullish if none of them is Retrograde", 5: "Very Bullish", 3: "Both side market with negative bias", 2: "Bullish", 4: "Bearish but Bullish if Jupiter is ahead"},
    ("Venus", "Saturn", 109): {1: "Bullish if Saturn not Retro or Combust", 7: "Bearish if Venus not Retro or Combust", 6: "Very small range", 5: "Bullish if both Planet Direct", 3: "Mild Bullish", 2: "Very small range", 4: "Bearish but Bullish if Saturn 4th to Venus"},
    ("Venus", "Rahu", 110): {1: "Good Bearish", 7: "Bearish if Venus is not Retro or Combust", 6: "Bullish", 5: "Bullish if Venus not atichari (very fast moving)", 3: "Mild Bullish", 2: "No impact", 4: "Big Bearish"},
    ("Venus", H, 110): {1: "Bullish if none of the 2 Retro else Bearish", 7: "Sudden Bearish", 6: "Very mild moves both side", 5: "Very good Bullish", 3: "Very mild moves both side", 2: "mild Bullish", 4: "Bearish"},
    ("Venus", "Neptune", 111): {1: "Bearish but Bullish if anyone retro", 7: "Bearish", 6: "Bullish", 5: "Bullish if both Planets Direct", 3: "Mild moves both side", 2: "Bearish", 4: "Bearish"},
    ("Saturn", H, 112): {1: "Good Bearish across all Markets", 7: "Bearish if none of Planet is Retro", 6: "Sudden spurt with limited potential", 5: "Very Bullish", 3: "Mild Bullish", 2: "Mild Bearish", 4: "Mild Bearish if none is Retro"},
    ("Saturn", "Neptune", 112): {1: "Extreme Bearish", 7: "Extreme Bullish if none is Retro", 6: "Bearish", 5: "Bullish", 3: "Mild Bullish", 2: "Mild moves result in fall Bearish", 4: "(printed incomplete) if both Planet Direct"},
    ("Saturn", "Rahu", 113): {1: "Bearish till distance 2 deg than Bullish", 7: "Bearish", 6: "Small moves both side", 5: "Bullish", 3: "Mild Bullish", 2: "Small fall best buying opportunity", 4: "Bearish"},
    ("Rahu", H, 114): {1: "Good Bearish", 7: "Bearish but small bounce in middle", 6: "Mild moves both side", 5: "Bullish", 3: "Mild Bullish", 2: "Mild Bearish", 4: "Good fall"},
    ("Rahu", "Neptune", 114): {1: "Very Bullish except if Neptune Retro or Combust", 7: "Bearish except Bullish if Neptune is Retro", 6: "Mild Bearish", 5: "Strong Bullish if Neptune Direct", 3: "Mild Bearish", 2: "Small moves both sides", 4: "Good fall"},
    (H, "Neptune", 115): {1: "Great falls & recession (like 1992)", 7: "Bearish", 6: "Mild Bearish if none is Retro", 5: "Strong Bullish", 3: "If Herschel Direct than Bullish", 2: "Sudden falls", 4: "Bearish"},
}
# Ketu: the section heads "RAHU / KETU"; a node pair is always 7th apart, so
# a relation to Rahu at k is a relation to Ketu at 8-k (k=1 <-> 7, 2/12 <->
# 6/8, 3/11 <-> 5/9, 4/10 <-> 4/10). Only Rahu is evaluated to avoid emitting
# the same window twice under two names; the facts name both nodes.

for (a, b, page), table in S25.items():
    moon = "Moon" in (a, b)
    for k, verdict in table.items():
        if k == 1 and verdict.startswith("Dealt in separate"):
            continue
        houses = PAIR_HOUSES[k]
        rule(id=f"ta_s25_{name(a).lower()}_{name(b).lower()}_{k}",
             title=f"{name(a)}-{name(b)} {REL_NAME[k]}",
             refs=(f"TA p.{page} [printed {page - 30}] Section 25 'Relationship effect of each planet with other' - {name(a).upper()} WITH {name(b).upper()}",),
             verdict=verdict, markets=("general",),
             rule=f"{name(a)} and {name(b)} are {REL_NAME[k]} to each other by whole sign.",
             calc="Whole-sign distance between the two sidereal (Lahiri) signs; window opens/closes at the sign ingress that changes the distance (1-hour scan, bisected to 30 s).",
             detector=windows(sign_rel(a, b, houses), (a, b), rel_facts(a, b)),
             quals=(("Rahu/Ketu: the section heads 'RAHU / KETU'; evaluated on Rahu, Ketu is always 7th from it." if "Rahu" in (a, b) else ""),
                    "Moon relationships: TA itself flags Moon-only conditions as low reliability ('RELIABILITY VERY LOW AS MOON ALONE DOES NOT DRIVE THE MARKETS', TA p.67/p.68)." if moon else ""),
             tier="moon" if moon else "major")

# ======================================================================
# TA Sections 3, 19-22: strong combinations (by whole sign).
# ======================================================================
rule(id="ta_s3_mars_12th_to_saturn", title="Mars 12th to Saturn (Mars-Saturn Dwidwadash Yog)",
     refs=("TA p.40 [printed 10] Section 3 'Saturn Moon / Mars Dwidwadash Yog'",
           "TA p.72 [printed 42] Section 19: Mars-Saturn Dwidwadash (2/12) 'Seen in Jan/Feb 16'",
           "TA p.100 [printed 70] S25 Mars with Saturn 2/12: 'Very Dubious very bad Bearish'",
           "KD p.27 'Transit Warning: Mars to Saturn Dwidwadash Yog'"),
     verdict="Bearish (TA S3: 'inauspicious & highly Bearish'; S25: 'Very Dubious very bad Bearish')",
     markets=("general",), rule="Mars occupies the 12th sign from Saturn.",
     calc="Sign of Mars = sign of Saturn - 1 (sidereal whole signs).",
     detector=windows(sign_rel("Saturn", "Mars", (12,), ordered=True), ("Mars", "Saturn"), rel_facts("Mars", "Saturn")),
     quals=("TA S3: 'Intensity always based on parameters laid out by larger Planets like Saturn, Hershel, Neptune, Jupiter & Rahu'.",
            "TA S4 note (p.41): IF BOTH PLANET DIRECT RESULT RELIABILITY VERY HIGH / IF ANY OF THEM RETRO OR COMBUST RESULT WILL BE CONTRA.",
            "TA p.257 (2020 example): highest impact when Mars and Saturn reach the same degree.",
            "KD p.27: Atichari Mars amplifies; Jupiter's 9th aspect on Rahu 'offers mitigating support'."))

rule(id="ta_s3_moon_12th_to_saturn", title="Moon 12th to Saturn (Shani Chandra Dwidwadash Yog)",
     refs=("TA p.40 [printed 10] Section 3", "TA p.245 (2020 table)", "KD p.94 (2026 table, 13 rows)"),
     verdict="Bearish", markets=("general",), rule="Moon occupies the 12th sign from Saturn.",
     calc="Sign of Moon = sign of Saturn - 1.", tier="major",
     detector=windows(sign_rel("Saturn", "Moon", (12,), ordered=True), ("Moon", "Saturn"), rel_facts("Moon", "Saturn")),
     existing=("b094_shani_chandra_dwidwadash_yog",),
     quals=("KD p.94 bottom note: 'HIGHEST IMPACT SEEN TILL MOON REACHES THE DEGREE OF SATURN'.",
            "KD p.94 bottom note (2026): axis Aquarius-Pisces 'INAUSPICIOUS, SO HIGH NEGATIVITY MAYBE SEEN' -- TA S4 classes Aquarius-Pisces as an Inauspicious-Bearish 2/12 pair."))

STRONG = [
    # (a, b, k, section, page, verdict, example)
    ("Mars", "Saturn", 3, 19, 72, "Strong Bearish", ""), ("Mars", "Saturn", 5, 19, 72, "Strong Bearish", ""),
    ("Mars", H, 6, 19, 72, "Strong Bearish", ""), ("Mars", "Neptune", 6, 19, 72, "Strong Bearish", ""),
    ("Mars", "Jupiter", 4, 19, 72, "Strong Bearish", ""), ("Mars", "Jupiter", 5, 19, 72, "Strong Bearish", ""),
    ("Mars", "Jupiter", 6, 19, 72, "Strong Bearish", ""), ("Mars", "Neptune", 5, 19, 72, "Strong Bearish", ""),
    ("Mars", "Rahu", 4, 19, 72, "Strong Bearish", ""), ("Sun", H, 4, 19, 72, "Strong Bearish", ""),
    ("Neptune", "Rahu", 4, 19, 72, "Strong Bearish", ""),
    (H, "Pluto", 6, 20, 73, "Very Strong Bearish", ""), (H, "Neptune", 1, 20, 73, "Very Strong Bearish - worst of all, like 1992", ""),
    ("Jupiter", "Saturn", 6, 21, 74, "Strong Bullish", "2012 rally from 4531 to 6100+"),
    ("Jupiter", H, 3, 21, 74, "Strong Bullish", ""), ("Jupiter", H, 6, 21, 74, "Strong Bullish", "2016 rally from 6826 to 8731"),
    ("Jupiter", "Neptune", 5, 21, 74, "Strong Bullish", "2013/14 rally from 5118 to 7780"),
    ("Jupiter", "Neptune", 6, 21, 74, "Strong Bullish", "Sept'16 is top example"),
    ("Jupiter", "Pluto", 3, 21, 74, "Strong Bullish", ""), ("Jupiter", "Pluto", 5, 21, 74, "Strong Bullish", "Seen from 6826 to 8731"),
    ("Jupiter", "Rahu", 5, 21, 74, "Strong Bullish", "2013/14 rally"), ("Jupiter", "Rahu", 6, 21, 74, "Strong Bullish", "2012 rally"),
    ("Mars", "Saturn", 1, 21, 75, "Strong Bullish", "Seen from 6826 to 8968"),
    ("Rahu", "Saturn", 5, 21, 75, "Strong Bullish", "Seen in 2017"), ("Rahu", H, 5, 21, 75, "Strong Bullish", "Seen from 6826 to 8297"),
    ("Rahu", "Neptune", 5, 21, 75, "Strong Bullish", "2016 rally from 6826 to 8731"),
    ("Rahu", "Neptune", 6, 21, 75, "Strong Bullish", "Oct15 bounce from 7540 to 8337"),
    ("Venus", "Saturn", 3, 22, 76, "Strong Bullish short term", ""), ("Venus", "Saturn", 5, 22, 76, "Strong Bullish short term", ""),
    ("Venus", H, 1, 22, 76, "Strong Bullish short term", ""), ("Venus", H, 5, 22, 76, "Strong Bullish short term", ""),
    ("Venus", "Rahu", 5, 22, 76, "Strong Bullish short term", ""), ("Mercury", "Saturn", 3, 22, 76, "Strong Bullish short term", ""),
    ("Mercury", "Saturn", 5, 22, 76, "Strong Bullish short term", ""), ("Mercury", H, 2, 22, 76, "Strong Bullish short term", ""),
    ("Mercury", "Rahu", 1, 22, 76, "Strong Bullish short term", ""), ("Mercury", "Rahu", 5, 22, 76, "Strong Bullish short term", ""),
]
SECTION_TITLE = {19: "STRONG BEARISH PERMUTATION & COMBINATION", 20: "VERY STRONG BEARISH",
                 21: "STRONG BULLISH PERMUTATION COMBINATION", 22: "STRONG BULLISH SHORT TERM YOGA'S"}
SECTION_NOTES = {
    19: (),
    20: ("TA p.73 bottom note: IMPACT STARTS WHILE PLANETS MOVE CLOSER TO THIS ASPECT; ONCE THEY MOVE AWAY FROM THOSE DEGREES IMPACT GETS OVER.",
         "TA p.73 bottom note: CONDITION - BOTH THE PLANETS SHOULD BE DIRECT FOR 100% OF RESULT EXCEPT RAHU WHICH IS ALWAYS RETROGRADE ONLY."),
    21: ("TA p.75 bottom note: BASED ON BOTH PLANETS EXCEPT RAHU DIRECT.",),
    22: ("TA p.76 bottom note: RELIABILITY OF ALL THESE IS SUBJECT TO NO MAJOR CONTRA EFFECT PLAYING & MOSTLY LIMITED TO SECTOR SPECIFIC.",),
}
for a, b, k, sec, page, verdict, ex in STRONG:
    rule(id=f"ta_s{sec}_{name(a).lower()}_{name(b).lower()}_{k}",
         title=f"{name(a)}-{name(b)} {REL_NAME[k]} ({SECTION_TITLE[sec].title()})",
         refs=(f"TA p.{page} [printed {page - 30}] Section {sec} '{SECTION_TITLE[sec]}'",),
         verdict=verdict + (f" (source example: {ex})" if ex else ""), markets=("general",),
         rule=f"{name(a)} and {name(b)} {REL_NAME[k]} by whole sign.",
         calc="Whole-sign distance (sidereal Lahiri); window bounded by the ingresses that make/break it.",
         detector=windows(sign_rel(a, b, PAIR_HOUSES[k]), (a, b), rel_facts(a, b)),
         quals=SECTION_NOTES[sec] + (("Section 20 entry 'Herschel Neptune Conjunction': read as both in one sign (the book uses 'together' for conjunction).",) if (a, b, k) == (H, "Neptune", 1) else ()))

rule(id="ta_s20_saturn_10th_aspect_on_jupiter", title="Saturn's 10th aspect on Jupiter",
     refs=("TA p.73 [printed 43] Section 20 'VERY STRONG BEARISH' #3",),
     verdict="Very Strong Bearish (example: 2015 fall accentuated after mid July; '25th May Aspect got over with higher Bottom of 7716')",
     markets=("general",), rule="Jupiter in the 10th sign from Saturn.",
     calc="Sign of Jupiter = sign of Saturn + 9.",
     detector=windows(sign_rel("Saturn", "Jupiter", (10,), ordered=True), ("Saturn", "Jupiter"), rel_facts("Saturn", "Jupiter")),
     quals=SECTION_NOTES[20])


# ======================================================================
# Helpers for placement rules
# ======================================================================
def nak_is(body, *naks):
    return lambda s: s[body].nak in naks and s[body].nak


def sign_is(body, *signs):
    return lambda s: s[body].sign in signs and s[body].sign


def together(*bodies):
    return lambda s: len({s[b].sign_i for b in bodies}) == 1 and s[bodies[0]].sign


def alone_together(*bodies):
    """bodies share a sign and no other POOL graha is in it."""
    def p(s):
        if len({s[b].sign_i for b in bodies}) != 1:
            return False
        others = [o for o in POOL if o not in bodies and s[o].sign_i == s[bodies[0]].sign_i]
        return (not others) and s[bodies[0]].sign
    return p


def all_retro(*bodies):
    return lambda s: all(s[b].retro for b in bodies)


def same_nak(*bodies):
    return lambda s: len({s[b].nak_i for b in bodies}) == 1 and s[bodies[0]].nak


def aspected_by_any(s, target, group):
    return [g for g in group if g != target and (s[g].sign_i == s[target].sign_i or aspects(s, g, target))]


def placed_facts(*bodies):
    def f(s, w):
        return {b: f"{s[b].sign} {s[b].deg:.2f} deg, {s[b].nak} pada {s[b].pada}, D9 {s[b].nav}, {'R' if s[b].retro else 'D'}" for b in bodies}
    return f


def R1(id, title, refs, verdict, markets, rule_text, pred, bodies, calc, quals=(), existing=(), effect="", tier="major", kind="window", effect_days=None):
    det = (windows(pred, bodies, placed_facts(*bodies)) if kind == "window"
           else entries(pred, bodies, effect_days, placed_facts(*bodies)))
    return rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets, rule=rule_text,
                calc=calc, detector=det, quals=quals, existing=existing, effect=effect, tier=tier)


NAKCALC = "Sidereal (Lahiri) nakshatra of the body, 27 x 13deg20'; window = the residency, boundaries bisected to 30 s."
SIGNCALC = "Sidereal (Lahiri) whole sign of the body; window bounded by its ingresses."
RETCALC = "Retrograde = of-date longitudinal speed < 0 (station instants as almanacs define them); Rahu/Ketu always retrograde (TA p.73)."
S24 = "TA Section 24 'Many important observations'"


def s24(n, page):
    return f"TA p.{page} [printed {page - 30}] Section 24 #{n}"


# ---------------- Section 9: Mercury in middle of Sun & Venus ----------------
def _mid(s):
    a = ((s["Sun"].lon - s["Venus"].lon + 180) % 360) - 180
    m = ((s["Mercury"].lon - s["Venus"].lon + 180) % 360) - 180
    if a > 0 and 0 < m < a:
        return "sun_ahead"
    if a < 0 and a < m < 0:
        return "venus_ahead"
    return None


rule(id="ta_s9_mercury_middle_sun_ahead", title="Mercury in middle of Sun (ahead) and Venus (behind)",
     refs=("TA p.49-50 [printed 19-20] Section 9 'Mercury in middle of Sun & Venus'", "TA p.25, p.262 (2014, 2020 examples)",
           "KD p.126/127 (4 & 14 Nov 2026: 'Sun ahead, Venus behind, Mercury in the middle')"),
     verdict="Markets deliver big returns (Bullish)", markets=("general",),
     rule="Sun ahead, Venus behind, and Mercury between them in zodiacal longitude.",
     calc="Signed arcs from Venus: Sun-Venus > 0 and 0 < Mercury-Venus < Sun-Venus. Validated against every dated example in TA/KD: 2014 (15 Feb-26 Apr; TA 'middle of February till end of April'), 2017 (20 Apr-21 Jun; 26 Aug-8 Oct), 2020 (1 Jul-17 Aug; TA '1st July to 18th August'), 2026 (from 4 Nov; KD 4 Nov).",
     detector=windows(lambda s: _mid(s) == "sun_ahead", ("Sun", "Mercury", "Venus"), placed_facts("Sun", "Mercury", "Venus")),
     quals=("TA p.49: 'In 2016 this yog got muted in February because Rahu was passing from Jupiter star in D9 charts'.",
            "TA p.50: in 2017 'got muted after 21st September due to Sun's 3rd aspect on Ketu till 29th September'.",
            "TA p.262: 'whether market will be continuous Bullish or rising in a flat mode will depend on many other events'."))
rule(id="ta_s9_mercury_middle_venus_ahead", title="Mercury in middle of Venus (ahead) and Sun (behind) - contra rule",
     refs=("TA p.50 [printed 20] Section 9 'CONTRA RULE'", "TA p.256 (2020: 11 Jan-26 Feb 2020)"),
     verdict="Bearish ('markets find it very tough to survive on the highs & frequent fall keep on happening')", markets=("general",),
     rule="Venus ahead, Sun behind, Mercury between them.",
     calc="Signed arcs from Venus: Sun-Venus < 0 and Sun-Venus < Mercury-Venus < 0. Validated: 2018 (21 Sep-15 Oct; TA 21.09-16.10.2018), 2020 (10 Jan-26 Feb; TA 11 Jan-26 Feb). TA's first 2018 example (18.02-21.03.2018) computes as 17 Feb-4 Mar and 20 Mar-1 Apr (Mercury passed Venus in between).",
     detector=windows(lambda s: _mid(s) == "venus_ahead", ("Sun", "Mercury", "Venus"), placed_facts("Sun", "Mercury", "Venus")),
     quals=("TA p.256 NOTE: whether markets will fall continuously or the fall will be flat depends on many other Planets & situations.",))

# ---------------- Section 31: Mercury Paap Kartari ----------------
def _pk(s):
    pool = ("Sun", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
    m = s["Mercury"].lon
    ahead = min(pool, key=lambda b: (s[b].lon - m) % 360)
    behind = min(pool, key=lambda b: (m - s[b].lon) % 360)
    if ahead in GRAHA_MAL and behind in GRAHA_MAL and s[ahead].retro:
        return f"{behind} behind, {ahead} ahead (retrograde)"
    return None


rule(id="ta_s31_mercury_paap_kartari", title="Mercury Paap Kartari Yog (TA definition)",
     refs=("TA p.128 [printed 98] Section 31 'Mercury Paap Kartari Yog'", "TA p.22 (2011 example)"),
     verdict="Bearish for Market in General & Banks in particular; USD & Dollar index strong", markets=("general", "sector:Banks", "USD"),
     rule="Mercury alone between two malefic planets AND the planet ahead of Mercury is retrograde.",
     calc="Nearest graha ahead and behind Mercury in longitude (Moon and outers excluded); both TA malefics (Sun, Mars, Saturn, Rahu, Ketu); the one ahead retrograde (Rahu/Ketu always).",
     detector=windows(_pk, ("Mercury",), placed_facts("Mercury")),
     existing=("b116_mercury_in_paap_kartari",),
     quals=("CONFLICT: the 2026 document's B116 has no 'planet ahead retrograde' condition and counts Uranus/Pluto as malefics; this TA definition is stricter. Both are kept: B116 rows stay as they are, this rule is listed separately.",
            "TA p.22 example (28 Oct 2011 - 2 Jan 2012) is NOT reproduced by this definition: it computes 6-26 Dec 2011 (Saturn behind, Rahu ahead), inside TA's window."))

# ---------------- Section 6: Day lord = Nakshatra lord ----------------
def _daylord(s, wd, d, ctx):
    lord = NAK_LORD[s["Moon"].nak_i]
    if lord in DAY_LORDS[wd]:
        return {"weekday": WEEKDAYS[wd], "moon_nakshatra_at_NY_sunrise": s["Moon"].nak, "lord": lord}


rule(id="ta_s6_day_lord_equals_nakshatra_lord", title="Day lord and Nakshatra lord the same",
     refs=("TA p.45 [printed 15] Section 6 'Days & their lords'",),
     verdict="Bullish day", markets=("general",),
     rule="The weekday's lord equals the lord of the Moon's nakshatra (Wednesday: Mercury & Rahu; Thursday: Jupiter, Ketu - as printed).",
     calc="Moon's nakshatra at New York sunrise of each civil day (Hindu day runs sunrise to sunrise); Vimshottari lords (TA p.47-48).",
     detector=daily(_daylord, ("Moon",)),
     quals=("Indian practice reads the nakshatra at the local (Indian) sunrise; this edition uses New York sunrise. Days near a nakshatra change can differ between the two.",))


# ---------------- Section 13: Bullish/Bearish nature of zodiac signs ----------------
# (sign, type, [(members, k, result, retro_required_members)])
#   members: list of (body, needs_retro) ; fires when >= k members are in the sign
def M(*spec):
    out = []
    for x in spec:
        if x.endswith("(R)"):
            out.append((x[:-3], True))
        else:
            out.append((x, False))
    return out


Hn = "Uranus"
S13 = [
    ("Aries", "Bullish", 54, [
        ("Sun or Mars present with Saturn & Rahu", "very Bullish", lambda s: any(s[b].sign == "Aries" for b in ("Sun", "Mars")) and s["Saturn"].sign == "Aries" and s["Rahu"].sign == "Aries"),
        ("Jupiter present with Venus or Mercury", "Bearish", lambda s: s["Jupiter"].sign == "Aries" and any(s[b].sign == "Aries" for b in ("Venus", "Mercury")))]),
    ("Taurus", "Very Bullish", 54, [
        ("Mars, Venus(R), Saturn, Rahu or Pluto there", "very Bullish", M("Mars", "Venus(R)", "Saturn", "Rahu", "Pluto"), 1),
        ("Direct Jupiter, Moon, Neptune or Ketu there", "Bearish", [("Jupiter", "D"), ("Moon", False), ("Neptune", False), ("Ketu", False)], 1)]),
    ("Gemini", "Bearish", 55, [
        ("Saturn(R), Mercury(R), Mars, Rahu, Sun any 2 together", "very Bullish", M("Saturn(R)", "Mercury(R)", "Mars", "Rahu", "Sun"), 2),
        ("Mercury, Jupiter, Venus, Neptune any 2 together", "very Bearish", M("Mercury", "Jupiter", "Venus", "Neptune"), 2)]),
    ("Cancer", "Bearish", 55, [
        ("Mars(R), Saturn(R), Mercury(R) with either Rahu/Herschel", "Bullish", lambda s: any(s[b].sign == "Cancer" and s[b].retro for b in ("Mars", "Saturn", "Mercury")) and any(s[b].sign == "Cancer" for b in ("Rahu", Hn))),
        ("Jupiter, Venus, Mercury & Neptune any 2 together", "very Bearish", M("Jupiter", "Venus", "Mercury", "Neptune"), 2)]),
    ("Leo", "Bullish", 55, [
        ("Venus(R), Sun, Saturn or Herschel any 2", "very Bullish", M("Venus(R)", "Sun", "Saturn", Hn), 2),
        ("Jupiter, Venus, Mercury, Neptune any 2", "Bearish", M("Jupiter", "Venus", "Mercury", "Neptune"), 2)]),
    ("Virgo", "Bearish", 56, [
        ("Saturn, Sun, Mars, Herschel, Rahu any 2", "extreme Bullish", M("Saturn", "Sun", "Mars", Hn, "Rahu"), 2),
        ("Jupiter, Venus, Ketu any 2", "extreme Bearish", M("Jupiter", "Venus", "Ketu"), 2)]),
    ("Libra", "Bearish", 56, [
        ("Saturn(R), Venus(R), Rahu or Mars any 2", "very Bullish", M("Saturn(R)", "Venus(R)", "Rahu", "Mars"), 2),
        ("Jupiter, Mercury, Moon any 2", "extreme Bearish", M("Jupiter", "Mercury", "Moon"), 2)]),
    ("Scorpio", "Bullish", 56, [
        ("Mars(R), Saturn(R), Rahu, Sun any 2", "historically Bullish (if Sun eclipse too happens - unprecedented Bullish)", M("Mars(R)", "Saturn(R)", "Rahu", "Sun"), 2),
        ("Jupiter, Mercury, Moon or Ketu any 2", "very Bearish", M("Jupiter", "Mercury", "Moon", "Ketu"), 2)]),
    ("Sagittarius", "Bearish", 56, [
        ("Jupiter(R), Venus(R), Saturn(R), Rahu or Sun any 2", "extreme Bullish", M("Jupiter(R)", "Venus(R)", "Saturn(R)", "Rahu", "Sun"), 2),
        ("Jupiter, Venus, Mercury, Moon any 2", "very Bearish", M("Jupiter", "Venus", "Mercury", "Moon"), 2)]),
    ("Capricorn", "1 sided Bullish", 57, [
        ("Mars(R), Saturn(R), Sun, Rahu, Herschel, Pluto any 2", "very very Bullish", M("Mars(R)", "Saturn(R)", "Sun", "Rahu", Hn, "Pluto"), 2),
        ("Mercury & Moon together", "little Bearish", M("Mercury", "Moon"), 2)]),
    ("Aquarius", "Bearish", 57, [
        ("Mars(R), Venus(R), Rahu, Sun any 2", "Bullish", M("Mars(R)", "Venus(R)", "Rahu", "Sun"), 2),
        ("Saturn, Jupiter, Mercury all 3 together", "extreme Bearish", M("Saturn", "Jupiter", "Mercury"), 3)]),
    ("Pisces", "Bearish", 57, [
        ("Jupiter(R), Saturn(R), Mars & Rahu any 2", "sudden Bullish", M("Jupiter(R)", "Saturn(R)", "Mars", "Rahu"), 2),
        ("Mercury, Moon, Neptune, Jupiter any 2", "extreme Bearish", M("Mercury", "Moon", "Neptune", "Jupiter"), 2)]),
]


def _members_pred(sign, members, k):
    def p(s):
        hit = []
        for b, need in members:
            if s[b].sign != sign:
                continue
            if need is True and not s[b].retro:
                continue
            if need == "D" and s[b].retro:
                continue
            hit.append(b)
        return len(hit) >= k and tuple(hit)
    return p


for sign, typ, page, combos in S13:
    for i, c in enumerate(combos):
        text, result = c[0], c[1]
        if callable(c[2]):
            pred, bodies, moon = c[2], (), False
        else:
            members, k = c[2], c[3]
            pred = _members_pred(sign, members, k)
            moon = any(b == "Moon" for b, _ in members)
        rule(id=f"ta_s13_{sign.lower()}_{i + 1}", title=f"{sign}: {text}",
             refs=(f"TA p.{page} [printed {page - 30}] Section 13 'Bullish Bearish nature of zodiac signs' - {sign} ({typ})",),
             verdict=result, markets=("general",),
             rule=f"In {sign} (sign type: {typ}): {text}.  (R) means retrograde.",
             calc=SIGNCALC + " 'Any 2' = at least two of the listed bodies in the sign at once, each meeting its (R) condition. " + RETCALC,
             detector=windows(pred, lambda v: v if isinstance(v, tuple) else (), None),
             tier="moon" if moon else "major",
             quals=("TA footer: (R) MEANS RETROGRADE.",) + (("Moon is one of the listed bodies: a combination that needs the Moon lasts ~2.5 days.",) if moon else ()))

# ---------------- Section 14: nature of planets, placement only ----------------
S14 = {
    "Sun": (58, "EXTREME BULLISH PLANET", ("Aries", "Taurus", "Scorpio", "Capricorn"), "very Bullish", ("Gemini", "Cancer", "Pisces"), "Bearish"),
    "Moon": (59, "VERY SHORT TERM BULLISH OR BEARISH", ("Aries", "Taurus", "Leo", "Libra", "Scorpio", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Cancer", "Virgo", "Sagittarius", "Pisces"), "Bearish"),
    "Mars": (59, "EXTREME BULLISH PLANET", ("Aries", "Taurus", "Scorpio", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Virgo", "Libra", "Pisces"), "Bearish"),
    "Mercury": (60, "SUDDEN SENTIMENT CHANGER, RULES MINDS", ("Aries", "Taurus", "Leo", "Libra", "Scorpio", "Aquarius"), "Bullish", (), ""),
    "Jupiter": (61, "MOSTLY BEARISH PLANET", ("Aries", "Leo", "Libra", "Scorpio", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Cancer", "Virgo", "Sagittarius", "Pisces"), "Bearish"),
    "Venus": (61, "EXTREME BULLISH PLANET", ("Aries", "Taurus", "Leo", "Libra", "Scorpio", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Cancer", "Virgo", "Sagittarius", "Pisces"), "Bearish"),
    "Saturn": (62, "UNSTABLE BULLISH OR BEARISH", ("Aries", "Leo", "Libra", "Scorpio", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Cancer", "Sagittarius", "Pisces"), "Bearish"),
    "Uranus": (64, "EXTREME BULLISH PLANET", ("Aries", "Taurus", "Scorpio", "Capricorn", "Aquarius"), "extreme Bullish", ("Gemini", "Virgo", "Libra", "Pisces"), "ordinary Bearish"),
    "Neptune": (65, "BEARISH PLANET", ("Aries", "Leo", "Libra", "Scorpio", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Cancer", "Virgo", "Sagittarius", "Pisces"), "Bearish"),
    "Pluto": (66, "BULLISH PLANETS", ("Aries", "Leo", "Libra", "Capricorn", "Aquarius"), "Bullish", ("Gemini", "Cancer", "Sagittarius", "Pisces"), "Bearish"),
}
S14_WITH = {   # body: (bullish companions, bullish note, bearish companions, bearish note)
    "Sun": (("Saturn", "Mars"), "With Saturn or Mars in Bullish signs - very Bullish", ("Jupiter", "Mercury", "Neptune"), "With Jupiter, Mercury, Neptune in Bearish signs - very Bearish"),
    "Moon": (("Mars", "Venus", "Saturn", "Rahu", "Uranus", "Pluto"), "With Mars, Venus, Saturn, Rahu, Herschel, Pluto - Bullish", ("Jupiter", "Neptune", "Mercury", "Ketu"), "With Jupiter, Neptune, Mercury, Ketu - Bearish"),
    "Mars": (("Saturn", "Rahu"), "With Saturn Rahu in Bullish signs - very Bullish", ("Jupiter", "Moon", "Neptune"), "With Jupiter, Moon, Neptune in Bearish signs - Bearish"),
    "Mercury": (("Sun", "Mars", "Saturn", "Rahu", "Pluto", "Uranus"), "With Sun, Mars, Saturn, Rahu, Pluto, Herschel - Bullish", ("Jupiter", "Neptune", "Moon", "Ketu"), "With Jupiter, Neptune, Moon, Ketu - Bearish"),
    "Jupiter": (("Sun", "Mars", "Venus", "Saturn", "Rahu"), "With Sun, Mars, Venus, Saturn, Rahu - Bullish", ("Mercury", "Neptune", "Ketu", "Moon"), "With Mercury, Neptune, Ketu, Moon - Bearish trend different in Direct & Retrograde"),
    "Venus": (("Sun", "Mars(R)", "Saturn(R)", "Rahu", "Uranus"), "With Sun, Mars(R), Saturn(R), Rahu, Herschel - high Bullish", ("Mercury", "Jupiter", "Moon", "Neptune"), "With Mercury, Jupiter, Moon, Neptune - Bearish"),
    "Saturn": (("Mars(R)", "Sun", "Rahu", "Venus", "Uranus"), "With Mars(R), Sun, Rahu, Venus, Herschel - very Bullish", ("Mercury", "Jupiter", "Moon", "Neptune"), "With Mercury, Jupiter, Moon, Neptune - ultra Bearish"),
    "Uranus": (("Saturn", "Rahu", "Sun"), "With Saturn, Rahu, Sun in Bullish Signs - great Bullish", ("Jupiter", "Moon", "Neptune"), "With Jupiter, Moon, Neptune in Bearish Signs - Bearish"),
    "Neptune": (("Sun", "Mars", "Venus", "Saturn", "Rahu"), "With Sun, Mars, Venus, Saturn & Rahu - Bullish", ("Mercury", "Jupiter", "Ketu", "Moon"), "With Mercury, Jupiter, Ketu, Moon - Bearish"),
    "Pluto": (("Mars(R)", "Sun", "Rahu", "Venus", "Uranus"), "With Mars(R), Sun, Rahu, Venus, Herschel - Bullish", ("Mercury", "Jupiter", "Moon", "Neptune"), "With Mercury, Jupiter, Moon, Neptune - Bearish"),
}
S14_EXTRA = {"Mercury": "Direct - mostly Bearish; Retrograde - mostly Bullish; with Venus - dealt separately",
             "Saturn": "more Bullish or Bearish as Direct/Retrograde is mirror image",
             "Neptune": "More Bullish as Retrograde; More Bearish as Direct; Scams & Bull/Bear syndicate ruled by it",
             "Pluto": "Very volatile @ time of changing direction"}
S14_NOTE = "TA p.66 bottom NOTE: THIS IS JUST PLACEMENT OF PLANET WHICH HAS VERY SMALL ROLE TO PLAY IN DECIDING BULLISH/BEARISH MARKETS SO SHOULD NOT BE TAKEN AS EXCLUSIVE RESULTS BASED ON IT."


def _s14_pred(body, bull, bear):
    def p(s):
        sg = s[body].sign
        if sg in bull:
            return f"{sg}: bullish sign"
        if sg in bear:
            return f"{sg}: bearish sign"
        return f"{sg}: sign not listed (neutral)"
    return p


for body, (page, label, bull, bv, bear, brv) in S14.items():
    rule(id=f"ta_s14_{name(body).lower()}_placement", title=f"{name(body)} sign placement ({label.title()})",
         refs=(f"TA p.{page} [printed {page - 30}] Section 14 'Nature of planets - purely only placement basis' - {name(body).upper()}",),
         verdict=f"{', '.join(bull)} - {bv}" + (f"; {', '.join(bear)} - {brv}" if bear else "") + (f"; {S14_EXTRA[body]}" if body in S14_EXTRA else ""),
         markets=("general",), rule=f"{name(body)}'s sign placement.",
         calc=SIGNCALC + " One event per residency; the verdict column states which list the sign is in.",
         detector=windows(_s14_pred(body, bull, bear), (body,), placed_facts(body)),
         quals=(S14_NOTE,), tier="moon" if body == "Moon" else "major")

    good, gnote, badc, bnote = S14_WITH[body]

    def _with(body=body, comp=good, need_sign=bull if "Bullish Signs" in gnote or "Bullish signs" in gnote else None):
        def p(s):
            hits = []
            for c in comp:
                rr = c.endswith("(R)")
                cb = c[:-3] if rr else c
                if cb == "Moon" and body != "Moon":
                    continue
                if s[cb].sign_i == s[body].sign_i and (not rr or s[cb].retro):
                    hits.append(cb)
            if need_sign and s[body].sign not in need_sign:
                return False
            return tuple(hits) if hits else False
        return p

    def _withbad(body=body, comp=badc, need_sign=bear if "Bearish Signs" in bnote or "Bearish signs" in bnote else None):
        def p(s):
            hits = [c for c in comp if s[c].sign_i == s[body].sign_i
                    and (c != "Moon" or body == "Moon")]
            if need_sign and s[body].sign not in need_sign:
                return False
            return tuple(hits) if hits else False
        return p

    for tag, pred, note in (("with_bullish", _with(), gnote), ("with_bearish", _withbad(), bnote)):
        moonish = body == "Moon"
        rule(id=f"ta_s14_{name(body).lower()}_{tag}", title=f"{name(body)} {note.split(' - ')[0].strip()}",
             refs=(f"TA p.{page} [printed {page - 30}] Section 14 - {name(body).upper()}",),
             verdict=note.split(" - ", 1)[1] if " - " in note else note, markets=("general",),
             rule=note, calc=SIGNCALC + " Companion = in the same sign. " + RETCALC,
             detector=windows(pred, (lambda v, body=body: (body,) + v), placed_facts(body)),
             quals=(S14_NOTE,) + (() if moonish or "Moon" not in note else ("A Moon companion is not evaluated in this row (it would add a ~2.5-day window every month); see the Moon layer.",)),
             tier="moon" if moonish else "major")


# ---------------- Section 24 and KD: placement / motion observations ----------------
def ent(id, title, refs, verdict, markets, text, pred, bodies, days=None, quals=(), existing=(), calc=None):
    return R1(id, title, refs, verdict, markets, text, pred, bodies,
              calc or (NAKCALC + (f" Effect window = entry + {days} days as the source states." if days else "")),
              quals=quals, existing=existing, kind="entry", effect_days=days,
              effect=f"{days} days from entry" if days else "")


def win(id, title, refs, verdict, markets, text, pred, bodies, calc=None, quals=(), existing=(), tier="major"):
    return R1(id, title, refs, verdict, markets, text, pred, bodies, calc or NAKCALC, quals=quals,
              existing=existing, tier=tier)


win("ta_s24_06_mars_retrograde", "Mars retrograde", (s24(6, 78), "TA p.154 S34 A1 (gold)", "KD p.137 #2"),
    "Bullish for its own sectors & commodities it rules; gold can rally (TA S34 A1)", ("sector:Mars (metals, chemicals)", "gold"),
    "Mars retrograde in any sign.", all_retro("Mars"), ("Mars",), RETCALC)
ent("ta_s24_07_mars_retro_cap_to_sag", "Retrograde Mars moves Capricorn->Sagittarius or Aries->Pisces", (s24(7, 79), "KD p.137 #3"),
    "High Bullish in grains", ("grains",), "Retrograde Mars re-enters Sagittarius from Capricorn or Pisces from Aries.",
    lambda s: s["Mars"].retro and s["Mars"].sign in ("Sagittarius", "Pisces") and s["Mars"].deg > 29.0 and s["Mars"].sign, ("Mars",),
    calc="Instant of Mars's retrograde ingress (Mars retrograde and at the end of Sagittarius/Pisces).")
ent("ta_s24_08_mars_retro_enters_taurus_libra", "Retrograde Mars entering Taurus or Libra", (s24(8, 79), "KD p.137 #4"),
    "High Bullish for Gold & Silver", ("gold", "silver"), "Mars, retrograde, enters Taurus or Libra.",
    lambda s: s["Mars"].retro and s["Mars"].sign in ("Taurus", "Libra") and s["Mars"].deg > 29.0 and s["Mars"].sign, ("Mars",),
    calc="Retrograde ingress instant into Taurus/Libra.")
win("ta_s24_09_retro_saturn_ashwini_bharani", "Retrograde Saturn on Ashwini or Bharani", (s24(9, 79), "KD p.142 #5"),
    "High Bullish in Commodities", ("commodities",), "Saturn retrograde in Ashwini or Bharani.",
    lambda s: s["Saturn"].retro and s["Saturn"].nak in ("Ashwini", "Bharani") and s["Saturn"].nak, ("Saturn",))
for n_, a_, b_, pg in ((10, "Magha", "Ashlesha", 79), (11, "Jyeshtha", "Anuradha", 79), (12, "Uttara Ashadha", "Purva Ashadha", 79)):
    ent(f"ta_s24_{n_:02d}_retro_saturn_{a_.split()[0].lower()}_to_{b_.split()[0].lower()}",
        f"Retrograde Saturn moves from {a_} into {b_}", (s24(n_, pg), f"KD p.142 #{ {10: 6, 11: 7, 12: 8}[n_] }"),
        "High Bullish for Markets" + (" (seen July - August 2016)" if n_ == 11 else ""), ("general",),
        f"Saturn, retrograde, re-enters {b_} from {a_}.",
        lambda s, b_=b_: s["Saturn"].retro and s["Saturn"].nak == b_ and (s["Saturn"].lon % (360 / 27)) > (360 / 27 - 0.05), ("Saturn",))


def _speed(group, faster):
    def p(s):
        hits = [b for b in group if b in NORMAL_SPEED and not s[b].retro and
                ((abs(s[b].speed) > NORMAL_SPEED[b]) if faster else (abs(s[b].speed) < NORMAL_SPEED[b]))]
        return tuple(hits) if hits else False
    return p


for b in ("Mercury", "Jupiter", "Venus"):
    win(f"ta_s24_13_{b.lower()}_fast", f"{b} (benefic) faster than normal speed", (s24(13, 79), "KD p.129", "TA p.144 normal speeds"),
        "Bullish", ("general",), f"{b} direct with daily motion above TA's normal speed ({NORMAL_SPEED[b]:.4f} deg/day).",
        lambda s, b=b: (not s[b].retro) and abs(s[b].speed) > NORMAL_SPEED[b], (b,),
        "Daily motion (sidereal) compared with TA p.144 'NORMAL SPEED OF PLANETS PER DAY'.")
for b in ("Mars", "Saturn"):
    win(f"ta_s24_14_{b.lower()}_fast", f"{b} (malefic) faster than normal speed", (s24(14, 79), "KD p.129", "TA p.144 normal speeds"),
        "Bearish", ("general",), f"{b} direct with daily motion above TA's normal speed ({NORMAL_SPEED[b]:.4f} deg/day).",
        lambda s, b=b: (not s[b].retro) and abs(s[b].speed) > NORMAL_SPEED[b], (b,),
        "Daily motion compared with TA p.144 normal speed.",
        quals=("Saturn's printed normal speed (0d2m0.4s = 0.0334 deg/day) is far below its mean motion (~0.0335-0.13 deg/day when direct), so direct Saturn is above it almost always; reported as computed.",) if b == "Saturn" else ())
win("kd_123_mars_below_normal_speed", "Mars speed below normal (Mand)", ("KD p.123 'Reducing the speed of Mars'", "TA p.144"),
    "Biggest rally in base metals expected ('Strong upside when Mars speed is below normal')", ("sector:Base metals",),
    "Mars direct or retrograde with |daily motion| below 0d31m26.46s.", lambda s: abs(s["Mars"].speed) < NORMAL_SPEED["Mars"], ("Mars",),
    "Daily motion vs TA p.144 normal speed. Cross-check: KD dates the 2026 onset 26 Oct 2026; this definition gives the 2026 crossing in the build log.")
win("ta_s24_23_venus_ahead_of_jupiter", "Venus ahead of Jupiter in same sign", (s24(23, 80), s24(48, 82), "KD p.141"),
    "Bearish", ("general",), "Venus and Jupiter in one sign, Venus ahead (greater longitude).",
    lambda s: s["Venus"].sign_i == s["Jupiter"].sign_i and s.ahead("Venus", "Jupiter") and s["Venus"].sign, ("Venus", "Jupiter"),
    SIGNCALC, existing=("b080_venus_ahead_of_jupiter_same_sign",))
win("ta_s24_47_venus_behind_jupiter", "Venus behind Jupiter in same sign", (s24(47, 82), "KD p.141"),
    "Bullish", ("general",), "Venus and Jupiter in one sign, Venus behind.",
    lambda s: s["Venus"].sign_i == s["Jupiter"].sign_i and s.ahead("Jupiter", "Venus") and s["Venus"].sign, ("Venus", "Jupiter"),
    SIGNCALC, existing=("b079_venus_behind_jupiter_same_sign",))


def _cross(a, b, days, verdict_ab):
    """a overtakes b (exact conjunction) while in one sign."""
    def run(ctx):
        out = []
        for h in conjunctions(a, b)(ctx):
            s = snapshot(h.start)
            if s[a].sign_i != s[b].sign_i:
                continue
            if h.facts["overtaking"].startswith(name(a)) or h.facts["overtaking"].startswith(a):
                h.end = h.start + dt.timedelta(days=days) if days else None
                h.facts.update(placed_facts(a, b)(s, None))
                out.append(h)
        return out
    return run


rule(id="ta_s24_40_mars_crosses_jupiter", title="Mars crosses Jupiter in same sign",
     refs=(s24(40, 81), "KD p.135 #3", "KD p.128 (2026: 'Market strength for 11 days when Mars ahead')"),
     verdict="11 days Bullish", markets=("general",), rule="Mars overtakes Jupiter (exact conjunction, Mars the faster) in one sign.",
     calc="Exact longitudinal conjunction Mars-Jupiter with Mars overtaking; effect window +11 days.", effect="11 days",
     detector=_cross("Mars", "Jupiter", 11, ""))
rule(id="ta_s24_24_jupiter_crosses_mars", title="Jupiter crosses Mars in same sign",
     refs=(s24(24, 80), s24(74, 84), "KD p.135 #2"), verdict="Bearish", markets=("general",),
     rule="Jupiter overtakes Mars (happens only while Mars is retrograde).",
     calc="Exact conjunction with Jupiter the one overtaking.", detector=_cross("Jupiter", "Mars", 0, ""))
win("ta_s24_25_mars_pisces_d9", "Mars in Pisces in D9 (Navamsh)", (s24(25, 80), "KD p.136"),
    "Bearish ('D9 placement signals weakness')", ("general",), "Mars's navamsa sign is Pisces.",
    lambda s: s["Mars"].nav == "Pisces", ("Mars",), "Navamsa = 9 divisions of 3deg20' per sign (Parashari).")
win("ta_s24_26_venus_in_pisces", "Venus in Pisces", (s24(26, 80), "KD p.141 'Venus alone in Pisces - Bearish'"),
    "Bearish", ("general",), "Venus in Pisces (KD adds 'alone').", sign_is("Venus", "Pisces"), ("Venus",), SIGNCALC,
    quals=("KD p.141 narrows to 'Venus alone in Pisces'; the alone flag is in the facts.",))
for n_, bodies_, verdict_, pg in ((29, ("Saturn", "Mars"), "Bullish", 80), (30, ("Saturn", "Mercury"), "Bullish", 81),
                                  (31, ("Saturn", "Venus"), "extreme Bullish", 81), (32, ("Saturn", "Venus", "Mars"), "extreme Bullish", 81),
                                  (33, ("Saturn", "Mars", "Mercury", "Jupiter"), "unprecedented Bullish", 81),
                                  (34, ("Saturn", "Mars", "Jupiter"), "Bullish", 81), (35, ("Jupiter", "Mercury"), "Bullish", 81),
                                  (36, ("Mercury", "Venus", "Jupiter"), "extreme Bearish", 81), (37, ("Mercury", "Venus"), "temporary bounce", 81)):
    ex = {29: ("cfg_none",), 30: ("b081_saturn_mercury_both_retrograde",), 35: ("cfg_silver_bullish_16_mercury_jupiter_both_retrograde",)}.get(n_, ())
    ex = tuple(e for e in ex if e != "cfg_none")
    q = ()
    if n_ == 36:
        q = ("TA prints '#36 Mercury, Venus & Jupiter Bullish together - extreme Bearish'; KD p.138 states the same rule as 'Mercury, Venus, and Jupiter retrograde together: High Bearish' and the list it sits in is all retrograde combinations, so 'Bullish' is read as a misprint for 'Retrograde'.",
             "TA S35 B5 (silver): 'Mercury, Jupiter & Venus all Retrograde in same Sign it's Bearish'.")
    win(f"ta_s24_{n_}_{'_'.join(b.lower() for b in bodies_)}_retro", f"{' & '.join(bodies_)} all retrograde together",
        (s24(n_, pg), "KD p.137/p.138"), verdict_, ("general",), f"{', '.join(bodies_)} simultaneously retrograde.",
        all_retro(*bodies_), bodies_, RETCALC, quals=q, existing=ex)
ent("ta_s24_41_saturn_enters_uttara_ashadha", "Saturn enters Uttara Ashadha", (s24(41, 81), "KD p.142 #1"),
    "Bullish start after 3 days", ("general",), "Saturn ingress into Uttara Ashadha.", nak_is("Saturn", "Uttara Ashadha"), ("Saturn",), days=3)
win("ta_s24_42_moon_ketu_same_sign", "Moon & Ketu in same sign", (s24(42, 82),), "Bullish", ("general",),
    "Moon and Ketu in one sign.", together("Moon", "Ketu"), ("Moon", "Ketu"), SIGNCALC, tier="moon")
win("ta_s24_43_moon_rahu_same_nakshatra", "Moon & Rahu in same nakshatra", (s24(43, 82), "KD p.133 #5"), "Bullish", ("general",),
    "Moon and Rahu in one nakshatra.", same_nak("Moon", "Rahu"), ("Moon", "Rahu"), existing=("b087_moon_rahu_same_nakshatra", "b088_moon_rahu_same_nakshatra_rahu_in_dhanishta"), tier="moon")
for n_, nk, pg, extra in ((44, "Rohini", 82, "KD p.136"), (50, "Chitra", 82, "KD p.136")):
    win(f"ta_s24_{n_}_mars_in_{nk.lower()}", f"Mars in {nk}", (s24(n_, pg), extra), "Bullish", ("general",),
        f"Mars in {nk}.", nak_is("Mars", nk), ("Mars",))
win("ta_s24_45_venus_mars_same_nakshatra", "Venus & Mars in same nakshatra", (s24(45, 82), "KD p.135 #7"), "Bullish", ("general",),
    "Venus and Mars in one nakshatra.", same_nak("Venus", "Mars"), ("Venus", "Mars"), existing=("b090_venus_mars_same_nakshatra",))
win("ta_s24_46_venus_mars_in_gemini", "Venus & Mars together in Gemini", (s24(46, 82), "KD p.135 #6", "TA S36 A18 (sugar)"),
    "high Bullish", ("general", "sugar"), "Venus and Mars both in Gemini.",
    lambda s: s["Venus"].sign == "Gemini" and s["Mars"].sign == "Gemini", ("Venus", "Mars"), SIGNCALC)
win("ta_s24_49_saturn_retro_in_vishakha", "Saturn retrograde in Vishakha", (s24(49, 82), "KD p.142 #2"), "Bullish 27 days", ("general",),
    "Saturn retrograde while in Vishakha.", lambda s: s["Saturn"].retro and s["Saturn"].nak == "Vishakha", ("Saturn",))
win("ta_s24_51_retro_mercury_conj_sun_mars_saturn", "Retrograde Mercury conjunct Sun, Mars or Saturn", (s24(51, 82), "KD p.138"),
    "Bullish", ("general",), "Mercury retrograde in the same sign as Sun, Mars or Saturn.",
    lambda s: s["Mercury"].retro and tuple(b for b in ("Sun", "Mars", "Saturn") if s[b].sign_i == s["Mercury"].sign_i) or False,
    ("Mercury",), SIGNCALC + " 'Conjunct' read as same sign (the book's usage for 'together'); exact conjunction instants are in the facts of the Sun-Mercury rule.")
for n_, nk, days, verdict_, pg, ex in ((52, "Uttara Ashadha", 5, "5 days Bullish", 82, "b091_sun_in_uttara_ashadha_ashwini_or_chitra"),
                                        (53, "Chitra", 5, "5 days Bullish", 82, "b091_sun_in_uttara_ashadha_ashwini_or_chitra"),
                                        (55, "Ashwini", 3, "3 days Bullish", 82, "b091_sun_in_uttara_ashadha_ashwini_or_chitra"),
                                        (73, "Krittika", 2, "2 days Bullish than Bearish", 84, "b092_sun_in_krittika")):
    ent(f"ta_s24_{n_}_sun_in_{nk.split()[0].lower()}", f"Sun enters {nk}", (s24(n_, pg), "KD p.132"), verdict_, ("general",),
        f"Sun ingress into {nk}.", nak_is("Sun", nk), ("Sun",), days=days, existing=(ex,))
win("ta_s24_54_moon_mars_together", "Moon & Mars together", (s24(54, 82),), "2.5 day Bullish", ("general",),
    "Moon and Mars in one sign.", together("Moon", "Mars"), ("Moon", "Mars"), SIGNCALC, existing=("b093_moon_mars_same_sign",), tier="moon")
win("ta_s24_69_atichari_mars_capricorn", "Atichari (very fast) Mars in Capricorn", (s24(69, 83), "KD p.135 #1"),
    "Bearish", ("general",), "Mars in Capricorn with daily motion above TA normal speed.",
    lambda s: s["Mars"].sign == "Capricorn" and s["Mars"].fast, ("Mars",), SIGNCALC + " Atichari = above TA p.144 normal speed.")
win("ta_s24_70_atichari_mars_pbh", "Atichari Mars in Purva Bhadrapada", (s24(70, 84), "KD p.88 (2026 window 20 Mar-06 Apr 2026)", "KD p.136"),
    "Bearish", ("general",), "Mars in Purva Bhadrapada with daily motion above TA normal speed.",
    lambda s: s["Mars"].nak == "Purva Bhadrapada" and s["Mars"].fast, ("Mars",), NAKCALC + " Atichari = above TA p.144 normal speed.",
    quals=("CONFLICT: KD p.136 also prints 'Mars in Purva Bhadrapad - Bullish after 3 to 4 days' (non-Atichari). Both are listed.",))
ent("kd_136_mars_in_pbh", "Mars enters Purva Bhadrapada", ("KD p.136",), "Bullish after 3 to 4 days ('Delayed positive impact')", ("general",),
    "Mars ingress into Purva Bhadrapada.", nak_is("Mars", "Purva Bhadrapada"), ("Mars",), days=4)
ent("kd_136_mars_in_vishakha", "Mars in Vishakha", ("KD p.136",), "Immediate (expect near-term upside)", ("general",),
    "Mars ingress into Vishakha.", nak_is("Mars", "Vishakha"), ("Mars",))
win("kd_087_mars_in_dhanishta", "Mars in Dhanishta", ("KD p.87", "KD p.136", "TA S36 B9 (sugar)"), "Immediate Bearish", ("general", "sugar"),
    "Mars in Dhanishta.", nak_is("Mars", "Dhanishta"), ("Mars",))
win("ta_s24_71_retro_saturn_combust", "Retrograde Saturn goes combust", (s24(71, 84), "KD p.142 #4"), "Bearish", ("general",),
    "Saturn retrograde within the Sun's combustion orb.", lambda s: False, ("Saturn",),
    "Saturn is combust only near its solar conjunction, when it is always direct; retrograde Saturn cannot be combust. Never fires (astronomical impossibility, recorded).")
win("ta_s24_72_sun_rahu_same_nakshatra", "Sun & Rahu in same nakshatra", (s24(72, 84), "KD p.131 #6"), "Bearish", ("general",),
    "Sun and Rahu in one nakshatra.", same_nak("Sun", "Rahu"), ("Sun", "Rahu"))
win("ta_s24_75_venus_in_mula", "Venus in Mula", (s24(75, 84), "KD p.141"), "Bullish", ("general",), "Venus in Mula.", nak_is("Venus", "Mula"), ("Venus",))
win("ta_s24_76_mercury_in_mula", "Mercury in Mula", (s24(76, 84), "KD p.138"), "Bearish", ("general",), "Mercury in Mula.", nak_is("Mercury", "Mula"), ("Mercury",))
win("ta_s24_77_sun_ketu_mars_same_nakshatra", "Sun, Ketu, Mars in same nakshatra", (s24(77, 84), "KD p.131 #4"), "high Bearish", ("general",),
    "Sun, Ketu and Mars in one nakshatra.", same_nak("Sun", "Ketu", "Mars"), ("Sun", "Ketu", "Mars"))
win("ta_s24_78_retro_mercury_in_jyeshtha", "Retrograde Mercury in Jyeshtha", (s24(78, 84), "KD p.138"), "Bearish", ("general",),
    "Mercury retrograde in Jyeshtha.", lambda s: s["Mercury"].retro and s["Mercury"].nak == "Jyeshtha", ("Mercury",))
for nk in ("Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta"):
    ent(f"ta_s24_79_jupiter_in_{nk.replace(' ', '_').lower()}", f"Jupiter enters {nk}", (s24(79, 84), "KD p.90"),
        "First 15 days Bearish than Bullish", ("general",), f"Jupiter ingress into {nk}.", nak_is("Jupiter", nk), ("Jupiter",), days=15)
ent("ta_s24_108_mars_3_days_after_direct", "Mars 3 days after getting direct", (s24(108, 86), "KD p.137 #9"), "Bearish ('Short-term downside bias around three days post-direct')",
    ("general",), "Mars direct station; effect window 3 days.", lambda s: not s["Mars"].retro, ("Mars",), days=3,
    calc="Mars direct-station instant (of-date speed crosses 0 upward); window +3 days.")
win("ta_s24_107_retro_mars_libra_not_combust", "Retrograde Mars in Libra (not combust)", (s24(107, 86), "KD p.137 #1"), "Very Bullish", ("general",),
    "Mars retrograde in Libra (retrograde Mars is opposite the Sun and cannot be combust).",
    lambda s: s["Mars"].retro and s["Mars"].sign == "Libra", ("Mars",), SIGNCALC)
win("kd_137_mars_retro_own_sign", "Mars retrograde in its own sign", ("KD p.137 #2",), "Bullish for its sectors", ("sector:Mars",),
    "Mars retrograde in Aries or Scorpio.", lambda s: s["Mars"].retro and s["Mars"].sign in ("Aries", "Scorpio"), ("Mars",), SIGNCALC)
win("kd_086_mars_at_28_deg", "Mars at 28 degrees in any sign", ("KD p.86 / p.135 #4 (cites 'Principles of Financial Astrology Book, page 79, Point No 39')",),
    "Can reverse or intensify trends", ("general",), "Mars between 28deg00' and 29deg00' of any sign.",
    lambda s: 28.0 <= s["Mars"].deg < 29.0 and s["Mars"].sign, ("Mars",), "Degree within sign from sidereal longitude.",
    quals=("KD's citation points to another book's point No 39; TA's own point 39 is the Sagittarius-Sankranti rule. The citation could not be verified from these two files.",))
win("kd_135_mars_saturn_aries_venus_joins", "Mars & Saturn in Aries, Venus joins", ("KD p.135 #5", "TA p.167 S37 #2"), "Bearish reversal", ("commodities", "general"),
    "Saturn and Mars together in Aries and Venus joins them.", lambda s: all(s[b].sign == "Aries" for b in ("Mars", "Saturn", "Venus")), ("Mars", "Saturn", "Venus"), SIGNCALC)
win("kd_142_saturn_in_uttara_bhadrapada", "Saturn in Uttara Bhadrapada", ("KD p.142 #3",), "High bullish", ("general",),
    "Saturn in Uttara Bhadrapada.", nak_is("Saturn", "Uttara Bhadrapada"), ("Saturn",))
win("kd_143_ketu_aquarius_under_10", "Ketu in Aquarius under 10 degrees", ("KD p.143 #2",), "High Bullish", ("general",),
    "Ketu in Aquarius 0-10 deg.", lambda s: s["Ketu"].sign == "Aquarius" and s["Ketu"].deg < 10, ("Ketu",), SIGNCALC)
win("kd_141_venus_alone_shravana", "Venus alone in Shravana", ("KD p.141",), "High Bullish", ("general",),
    "Venus in Shravana with no other graha in Shravana.", lambda s: s["Venus"].nak == "Shravana" and not [b for b in POOL if b != "Venus" and s[b].nak == "Shravana"], ("Venus",))
win("kd_141_venus_or_jupiter_alone_ubh", "Venus or Jupiter alone in Uttara Bhadrapada", ("KD p.141",), "Bearish ('Single benefic in Uttra Bhadrapad signals downside')", ("general",),
    "Venus or Jupiter in Uttara Bhadrapada with no other graha there.",
    lambda s: tuple(b for b in ("Venus", "Jupiter") if s[b].nak == "Uttara Bhadrapada" and not [o for o in POOL if o != b and s[o].nak == "Uttara Bhadrapada"]) or False, ())
win("kd_141_retro_venus_bullish_sign", "Retrograde Venus in a bullish sign", ("KD p.141",), "catalyst for big rally", ("general",),
    "Venus retrograde in a sign TA S13 types as Bullish (Aries, Taurus, Leo, Scorpio, Capricorn).",
    lambda s: s["Venus"].retro and s["Venus"].sign in ("Aries", "Taurus", "Leo", "Scorpio", "Capricorn") and s["Venus"].sign, ("Venus",), SIGNCALC,
    quals=("'Bullish sign' resolved with TA Section 13's sign types (KD gives no list).",))
win("kd_138_mercury_venus_shravana", "Mercury & Venus together in Shravana", ("KD p.138",), "Bearish for 3 to 4 days", ("general",),
    "Mercury and Venus both in Shravana.", lambda s: s["Mercury"].nak == "Shravana" and s["Venus"].nak == "Shravana", ("Mercury", "Venus"))
win("kd_138_mercury_in_pbh", "Mercury in Purva Bhadrapada", ("KD p.138",), "Bullish then Bearish", ("general",),
    "Mercury in Purva Bhadrapada.", nak_is("Mercury", "Purva Bhadrapada"), ("Mercury",))
win("kd_130_sun_mercury_revati", "Sun & Mercury together in Revati", ("KD p.130 #6",), "High Bullish", ("general",),
    "Sun and Mercury both in Revati.", lambda s: s["Sun"].nak == "Revati" and s["Mercury"].nak == "Revati", ("Sun", "Mercury"))
win("kd_131_sun_mars_rahu_venus_aries_scorpio", "Sun, Mars, Rahu, Venus together in Aries or Scorpio", ("KD p.131 #3", "TA S36 A19 (Aries only, sugar)"),
    "High Bullish", ("general", "sugar"), "Sun, Mars, Rahu (or Ketu, TA) and Venus all in Aries (KD adds Scorpio).",
    lambda s: s["Sun"].sign in ("Aries", "Scorpio") and all(s[b].sign == s["Sun"].sign for b in ("Mars", "Venus")) and (s["Rahu"].sign == s["Sun"].sign or s["Ketu"].sign == s["Sun"].sign), ("Sun", "Mars", "Venus", "Rahu"), SIGNCALC)
win("kd_089_mercury_venus_alone", "Mercury and Venus alone in a sign", ("KD p.89", "KD p.102", "KD p.121", "KD p.106"),
    "Bearish / sluggish markets, small dip ('High impact when both inner planets occupy a bearish sign')", ("general",),
    "Mercury and Venus share a sign and no other graha (Moon excluded) is in it.", alone_together("Mercury", "Venus"), ("Mercury", "Venus"), SIGNCALC,
    quals=("KD p.102 condition text: 'No other planets present in the same sign'. The Moon is not counted (it passes every ~2.5 days).",
           "KD p.121 (2026): conjunction in Virgo created Neech Bhang Yog -> 'probability of sharp turnaround after conjunction'."))
win("kd_138_mercury_alone", "Mercury alone in a sign", ("KD p.138",), "Bearish; stronger in bearish signs", ("general",),
    "Mercury with no other graha (Moon excluded) in its sign.",
    lambda s: not [b for b in POOL if b != "Mercury" and s[b].sign_i == s["Mercury"].sign_i] and s["Mercury"].sign, ("Mercury",), SIGNCALC,
    quals=("CONFLICT: TA S35 A17 (silver) 'Only Sun Mercury or Moon Mercury alone in any sign it's Bullish' -- a different configuration (Mercury paired), so not contradictory in condition, but opposite in tone.",))


# ---------------- TA Sections 34-37: gold, silver, sugar, turning ----------------
def S(sec, n, page, kind=""):
    return f"TA p.{page} [printed {page - 30}] Section {sec} {kind} #{n}"


GOLD = ("gold",)
SILV = ("silver",)
SUG = ("sugar",)
win("ta_s34a02_mars_in_taurus", "Mars passes from Taurus", (S(34, 2, 154, "A 'When gold can rally?'"),), "Gold can rally", GOLD,
    "Mars in Taurus.", sign_is("Mars", "Taurus"), ("Mars",), SIGNCALC)
win("ta_s34a03_sun_libra_with_malefic", "Sun in Libra with other malefic (Saturn, Mars, Rahu)", (S(34, 3, 154, "A"),), "Gold can rally", GOLD,
    "Sun in Libra with Saturn, Mars or Rahu in Libra.", lambda s: s["Sun"].sign == "Libra" and tuple(b for b in ("Saturn", "Mars", "Rahu") if s[b].sign == "Libra") or False,
    ("Sun",), SIGNCALC, existing=("cfg_gold_bullish_02_sun_libra_aspected_by_malefics",),
    quals=("The 2026 config rule reads 'aspected by' malefics; TA prints 'with other Malefic'. Both are reported.",))
win("ta_s34a04_rahu_mars_together", "Rahu & Mars together in any sign", (S(34, 4, 154, "A"), S(35, 4, 158, "A (silver)")), "Gold can rally; silver Bullish, more when same nakshatra", GOLD + SILV,
    "Rahu and Mars in one sign.", together("Rahu", "Mars"), ("Rahu", "Mars"), SIGNCALC,
    existing=("cfg_gold_bullish_03_rahu_mars_same_sign", "cfg_silver_bullish_07_rahu_mars_same_sign"))
for n_, sg in ((5, "Scorpio"), (6, "Gemini")):
    ent(f"ta_s34a0{n_}_jupiter_enters_{sg.lower()}", f"Jupiter enters {sg}", (S(34, n_, 154, "A"),) + ((S(35, 12, 158, "A (silver)"),) if sg == "Scorpio" else ()),
        "Gold Bullish after 5 months" + (" (2019 move); silver trend Bullish after 5 months" if sg == "Scorpio" else ""), GOLD + (SILV if sg == "Scorpio" else ()),
        f"Jupiter ingress into {sg}; effect from +5 months.", sign_is("Jupiter", sg), ("Jupiter",), calc=SIGNCALC + " Effect begins about 5 months (152 days) after the ingress.")
win("ta_s34a09_mars_aspected_saturn_jupiter_retro", "Mars aspected by Saturn while Jupiter retrograde", (S(34, 9, 155, "A"),), "Gold can rally", GOLD,
    "Saturn casts a drishti (3/7/10) on Mars and Jupiter is retrograde.", lambda s: aspects(s, "Saturn", "Mars") and s["Jupiter"].retro, ("Mars", "Saturn", "Jupiter"),
    "Whole-sign graha drishti (project convention: Saturn 3/7/10) + Jupiter retrograde.")


def _sun_star_unaspected(naks, benefic_bad=True):
    def p(s):
        if s["Sun"].nak not in naks:
            return False
        ben = aspected_by_any(s, "Sun", GRAHA_BEN)
        mal = aspected_by_any(s, "Sun", GRAHA_MAL[1:])
        if benefic_bad and ben:
            return False
        return f"{s['Sun'].nak}; malefic with/aspecting: {', '.join(mal) or 'none'}"
    return p


win("ta_s34a10_sun_bharani_krittika_punarvasu_pushya", "Sun on Bharani, Krittika, Punarvasu or Pushya, not aspected by benefic", (S(34, 10, 155, "A"),),
    "Gold can rally - More Bullish if aspected by malefic", GOLD, "Sun in one of the four nakshatras with no benefic (Mercury, Jupiter, Venus) with or aspecting it.",
    _sun_star_unaspected(("Bharani", "Krittika", "Punarvasu", "Pushya")), ("Sun",),
    NAKCALC + " Benefic contact = same sign or whole-sign drishti.")
win("ta_s34a11_saturn_jupiter_sagittarius", "Saturn with Jupiter in Sagittarius", (S(34, 11, 155, "A"),), "Gold can rally", GOLD,
    "Saturn and Jupiter both in Sagittarius.", lambda s: s["Saturn"].sign == "Sagittarius" == s["Jupiter"].sign, ("Saturn", "Jupiter"), SIGNCALC)
win("ta_s34a12_rahu_cancer_no_benefic", "Rahu in Cancer without any benefic", (S(34, 12, 155, "A"),), "Gold can rally", GOLD,
    "Rahu in Cancer, no benefic in Cancer.", lambda s: s["Rahu"].sign == "Cancer" and not [b for b in GRAHA_BEN if s[b].sign == "Cancer"], ("Rahu",), SIGNCALC)
win("ta_s34b01_sun_anuradha_benefic", "Sun on Anuradha with or aspected by benefic", (S(34, 1, 156, "B 'When gold can fall?'"),), "Gold can fall", GOLD,
    "Sun in Anuradha with a benefic in the sign or aspecting it.", lambda s: s["Sun"].nak == "Anuradha" and tuple(aspected_by_any(s, "Sun", GRAHA_BEN)) or False, ("Sun",), NAKCALC)
win("ta_s34b03_saturn_or_mercury_gemini", "Saturn or Mercury in Gemini", (S(34, 3, 156, "B"),), "Gold Bearish", GOLD,
    "Saturn or Mercury in Gemini.", lambda s: tuple(b for b in ("Saturn", "Mercury") if s[b].sign == "Gemini") or False, (), SIGNCALC,
    existing=("cfg_gold_bearish_02_saturn_or_mercury_in_gemini",))
win("ta_s34b06_jupiter_in_aries", "Jupiter in Aries", (S(34, 6, 156, "B"),), "Bearish in gold", GOLD, "Jupiter in Aries.", sign_is("Jupiter", "Aries"), ("Jupiter",), SIGNCALC)
win("ta_s34b07_venus_jyeshtha_benefic", "Venus in Jyeshtha with or aspected by benefic", (S(34, 7, 156, "B"),), "Gold Bearish", GOLD,
    "Venus in Jyeshtha with Mercury/Jupiter in its sign or aspecting it.", lambda s: s["Venus"].nak == "Jyeshtha" and tuple(aspected_by_any(s, "Venus", ("Mercury", "Jupiter"))) or False, ("Venus",), NAKCALC)
win("ta_s34b08_jupiter_sag_cap_aries_benefic", "Jupiter in Sagittarius, Capricorn or Aries alone, with benefic or aspected by benefic", (S(34, 8, 156, "B"),), "Gold Bearish", GOLD,
    "Jupiter in Sagittarius, Capricorn or Aries and either alone or with/aspected by a benefic (Mercury, Venus).",
    lambda s: s["Jupiter"].sign in ("Sagittarius", "Capricorn", "Aries") and s["Jupiter"].sign, ("Jupiter",), SIGNCALC,
    quals=("As printed, 'alone, with benefic or aspected by benefic' leaves only 'with/aspected by a malefic and no benefic' outside the rule; facts list the companions.",))
win("ta_s34b10_six_together", "Sun, Moon, Mars, Mercury, Jupiter & Venus together in any sign", (S(34, 10, 156, "B"),), "High Bearish in gold", GOLD,
    "All six in one sign.", together("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus"), ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus"), SIGNCALC)

win("ta_s35a03_venus_mars_or_sun_mars", "Venus-Mars or Sun-Mars together in any sign", (S(35, 3, 157, "A 'Bullish configurations - silver'"),), "Silver Bullish (July, August 2019)", SILV,
    "Venus with Mars, or Sun with Mars, in one sign.", lambda s: tuple(b for b in ("Venus", "Sun") if s[b].sign_i == s["Mars"].sign_i) or False, ("Mars",), SIGNCALC,
    existing=("cfg_silver_bullish_05_venus_mars_same_sign", "cfg_silver_bullish_06_sun_mars_same_sign"))
win("ta_s35a06_mars_in_aquarius", "Mars in Aquarius", (S(35, 6, 158, "A"),), "Silver Bullish", SILV, "Mars in Aquarius.", sign_is("Mars", "Aquarius"), ("Mars",), SIGNCALC)
win("ta_s35a07_venus_virgo_malefic", "Venus in Virgo with malefic", (S(35, 7, 158, "A"),), "Silver Bullish (August 2019)", SILV,
    "Venus in Virgo with a malefic in Virgo.", lambda s: s["Venus"].sign == "Virgo" and tuple(b for b in GRAHA_MAL if s[b].sign == "Virgo") or False, ("Venus",), SIGNCALC)
win("ta_s35a09_saturn_aquarius_aries", "Saturn in Aquarius or Aries", (S(35, 9, 158, "A"),), "Silver Bullish trend", SILV,
    "Saturn in Aquarius or Aries.", sign_is("Saturn", "Aquarius", "Aries"), ("Saturn",), SIGNCALC)
win("ta_s35a14_sun_leo_mars_or_jupiter_retro", "Sun in Leo with Mars or Jupiter retrograde", (S(35, 14, 159, "A"),), "Silver high Bullish", SILV,
    "Sun in Leo while Mars or Jupiter is retrograde.", lambda s: s["Sun"].sign == "Leo" and tuple(b for b in ("Mars", "Jupiter") if s[b].retro) or False, ("Sun",), SIGNCALC + " " + RETCALC)
win("ta_s35a20_sun_venus_alone_cancer", "Sun & Venus alone in Cancer", (S(35, 20, 159, "A"),), "Silver Bullish", SILV,
    "Sun and Venus in Cancer, no other graha there.", lambda s: s["Sun"].sign == "Cancer" and alone_together("Sun", "Venus")(s), ("Sun", "Venus"), SIGNCALC)
win("ta_s35b01_venus_leo_libra", "Venus in Leo or Libra", (S(35, 1, 160, "B 'Bearish configuration - silver'"),), "Silver Bearish", SILV,
    "Venus in Leo or Libra.", sign_is("Venus", "Leo", "Libra"), ("Venus",), SIGNCALC, existing=("cfg_silver_bearish_01_venus_alone_in_leo_or_libra",),
    quals=("The 2026 config rule adds 'alone'; TA does not.",))
win("ta_s35b02_mercury_aries_virgo", "Mercury in Aries or Virgo", (S(35, 2, 160, "B"),), "Silver Bearish", SILV,
    "Mercury in Aries or Virgo.", sign_is("Mercury", "Aries", "Virgo"), ("Mercury",), SIGNCALC, existing=("cfg_silver_bearish_02_mercury_alone_in_aries_or_virgo",))
win("ta_s35b03_mars_ashlesha_pada4", "Mars in 4th pada of Ashlesha", (S(35, 3, 160, "B"),), "Silver: good fall", SILV,
    "Mars in Ashlesha pada 4 (Cancer 26deg40'-30deg).", lambda s: s["Mars"].nak == "Ashlesha" and s["Mars"].pada == 4, ("Mars",), NAKCALC,
    existing=("cfg_silver_bearish_03_mars_in_fourth_pad_of_ashlesha",))
win("ta_s35b05_mer_jup_ven_retro_same_sign", "Mercury, Jupiter & Venus all retrograde in same sign", (S(35, 5, 160, "B"),), "Silver Bearish", SILV,
    "All three retrograde and in one sign.", lambda s: all_retro("Mercury", "Jupiter", "Venus")(s) and together("Mercury", "Jupiter", "Venus")(s), ("Mercury", "Jupiter", "Venus"), SIGNCALC)
win("ta_s35b06_jupiter_cap_saturn_scorpio", "Jupiter in Capricorn & Saturn in Scorpio", (S(35, 6, 160, "B"),), "Silver: huge fall comes", SILV,
    "Jupiter in Capricorn and Saturn in Scorpio.", lambda s: s["Jupiter"].sign == "Capricorn" and s["Saturn"].sign == "Scorpio", ("Jupiter", "Saturn"), SIGNCALC)
win("ta_s35b08_retro_mars_with_ketu", "Retrograde Mars with Ketu", (S(35, 8, 160, "B"), S(36, 4, 165, "B (sugar)")), "Silver huge Bearish; sugar 5 days Bearish then reversal", SILV + SUG,
    "Mars retrograde in the same sign as Ketu.", lambda s: s["Mars"].retro and s["Mars"].sign_i == s["Ketu"].sign_i, ("Mars", "Ketu"), SIGNCALC)
win("ta_s35b13_sun_vir_lib_pis_benefic", "Sun in Virgo, Libra or Pisces with or aspected by benefics", (S(35, 13, 161, "B"),), "Silver Bearish", SILV,
    "Sun in Virgo/Libra/Pisces with a benefic in its sign or aspecting it.",
    lambda s: s["Sun"].sign in ("Virgo", "Libra", "Pisces") and tuple(aspected_by_any(s, "Sun", GRAHA_BEN)) or False, ("Sun",), SIGNCALC,
    existing=("cfg_silver_bearish_09_sun_three_signs_with_or_aspected_by_benefics",))
win("ta_s35b14_mars_gemini_with_two", "Mars in Gemini with any 2 other planets", (S(35, 14, 161, "B"),), "Silver Bearish", SILV,
    "Mars in Gemini with at least two other grahas in Gemini.", lambda s: s["Mars"].sign == "Gemini" and len([b for b in POOL if b != "Mars" and s[b].sign == "Gemini"]) >= 2, ("Mars",), SIGNCALC)
win("ta_s35b15_mercury_venus_pisces", "Mercury & Venus both in Pisces", (S(35, 15, 161, "B"),), "Silver Bearish", SILV,
    "Mercury and Venus in Pisces.", lambda s: s["Mercury"].sign == "Pisces" == s["Venus"].sign, ("Mercury", "Venus"), SIGNCALC)
ent("ta_s35b11_rahu_enters_gemini", "Rahu enters Gemini", (S(35, 11, 161, "B"),), "Silver Bearish (March April 2019)", SILV,
    "Rahu ingress into Gemini.", sign_is("Rahu", "Gemini"), ("Rahu",), calc=SIGNCALC)
win("ta_s35a18_mercury_jupiter_retro", "Mercury & Jupiter both retrograde (even in different signs)", (S(35, 18, 159, "A"),), "Silver Bullish", SILV,
    "Both retrograde.", all_retro("Mercury", "Jupiter"), ("Mercury", "Jupiter"), RETCALC, existing=("cfg_silver_bullish_16_mercury_jupiter_both_retrograde",))
win("ta_s35a01_retro_mercury_or_jupiter", "Retrograde Mercury or Jupiter", (S(35, 1, 157, "A"),), "Silver: increases volatility & prices start rising", SILV,
    "Mercury or Jupiter retrograde.", lambda s: tuple(b for b in ("Mercury", "Jupiter") if s[b].retro) or False, (), RETCALC,
    existing=("cfg_silver_bullish_02_retrograde_mercury_or_jupiter",))
win("ta_s35a02_sun_pushya_dhanishta_no_benefic", "Sun in Pushya or Dhanishta without benefic planets", (S(35, 2, 157, "A"),), "Silver Bullish", SILV,
    "Sun in Pushya/Dhanishta with no benefic in its sign.", lambda s: s["Sun"].nak in ("Pushya", "Dhanishta") and not [b for b in GRAHA_BEN if s[b].sign_i == s["Sun"].sign_i] and s["Sun"].nak, ("Sun",), NAKCALC,
    existing=("cfg_silver_bullish_03_sun_pushya_or_dhanistha_without_benefic",))
win("ta_s35a17_sun_or_moon_mercury_alone", "Only Sun-Mercury or Moon-Mercury alone in a sign", (S(35, 17, 159, "A"),), "Silver Bullish", SILV,
    "Mercury shares a sign only with the Sun (or only with the Moon).", lambda s: alone_together("Sun", "Mercury")(s), ("Sun", "Mercury"), SIGNCALC,
    existing=("cfg_silver_bullish_15_sun_or_moon_with_mercury_alone",), quals=("Moon-Mercury variant belongs to the Moon layer (2.5-day windows).",))

win("ta_s36a01_jupiter_cancer_or_saturn_gemini", "Jupiter in Cancer or Saturn in Gemini", (S(36, 1, 162, "A 'Sugar & Jaggery - bullish'"),), "Sugar Bullish", SUG,
    "Jupiter in Cancer or Saturn in Gemini.", lambda s: ("Jupiter in Cancer" if s["Jupiter"].sign == "Cancer" else False) or ("Saturn in Gemini" if s["Saturn"].sign == "Gemini" else False), (), SIGNCALC,
    existing=("cfg_sugar_bullish_01_jupiter_in_cancer",))
win("ta_s36a02_jupiter_uttara_ashadha", "Jupiter passing Uttara Ashadha", (S(36, 2, 162, "A"),), "Sugar Bullish", SUG, "Jupiter in Uttara Ashadha.", nak_is("Jupiter", "Uttara Ashadha"), ("Jupiter",))
win("ta_s36a10_mars_ketu_virgo", "Mars & Ketu together in Virgo", (S(36, 10, 163, "A"),), "Sugar Bullish", SUG, "Mars and Ketu in Virgo.",
    lambda s: s["Mars"].sign == "Virgo" == s["Ketu"].sign, ("Mars", "Ketu"), SIGNCALC)
win("ta_s36a11_jup_retro_cancer_saturn_retro", "Jupiter retrograde in Cancer and Saturn also retrograde", (S(36, 11, 163, "A"),), "Sugar: huge Bullishness in that period", SUG,
    "Jupiter retrograde in Cancer while Saturn is retrograde (any sign).", lambda s: s["Jupiter"].retro and s["Jupiter"].sign == "Cancer" and s["Saturn"].retro, ("Jupiter", "Saturn"), SIGNCALC + " " + RETCALC)
win("ta_s36a13_herschel_with_malefic", "Herschel with any malefic planet in any sign", (S(36, 13, 163, "A"),), "Sugar Bullish", SUG,
    "Uranus in the same sign as Sun, Mars, Saturn, Rahu or Ketu.", lambda s: tuple(b for b in GRAHA_MAL if s[b].sign_i == s[H].sign_i) or False, (H,), SIGNCALC,
    existing=("cfg_sugar_bullish_06_herschel_with_any_malefic",))
win("ta_s36a14_combos", "Mercury, Jupiter & Saturn together in Virgo; or Jupiter & Rahu / Mars & Rahu together in Scorpio", (S(36, 14, 163, "A"),), "Sugar Bullish", SUG,
    "Any of the three combinations.", lambda s: (all(s[b].sign == "Virgo" for b in ("Mercury", "Jupiter", "Saturn")) and "Mer-Jup-Sat Virgo") or
    (s["Rahu"].sign == "Scorpio" and tuple(b for b in ("Jupiter", "Mars") if s[b].sign == "Scorpio")) or False, (), SIGNCALC)
win("ta_s36a15_combos", "Jupiter & Saturn in Pisces; Jupiter & Venus in Capricorn; Mars & Mercury in Aquarius; or only Saturn in Capricorn", (S(36, 15, 164, "A"),), "Sugar Bullish (all)", SUG,
    "Any of the four combinations.", lambda s: (s["Jupiter"].sign == "Pisces" == s["Saturn"].sign and "Jup-Sat Pisces") or (s["Jupiter"].sign == "Capricorn" == s["Venus"].sign and "Jup-Ven Capricorn")
    or (s["Mars"].sign == "Aquarius" == s["Mercury"].sign and "Mars-Mer Aquarius") or (s["Saturn"].sign == "Capricorn" and not [b for b in POOL if b != "Saturn" and s[b].sign == "Capricorn"] and "Saturn alone Capricorn") or False, (), SIGNCALC)
win("ta_s36a16_mars_mercury_jupiter_libra", "Mars (not combust), Mercury & Jupiter together in Libra", (S(36, 16, 164, "A"),), "Sugar Bullish", SUG, "All three in Libra.",
    together("Mars", "Mercury", "Jupiter"), ("Mars", "Mercury", "Jupiter"), SIGNCALC)
win("ta_s36a17_saturn_jupiter_or_rahu_taurus", "Saturn & Jupiter or Saturn & Rahu in Taurus", (S(36, 17, 164, "A"),), "Sugar Bullish", SUG, "Saturn in Taurus with Jupiter or Rahu.",
    lambda s: s["Saturn"].sign == "Taurus" and tuple(b for b in ("Jupiter", "Rahu") if s[b].sign == "Taurus") or False, ("Saturn",), SIGNCALC)
win("ta_s36b07_mercury_jupiter_aries", "Mercury & Jupiter together in Aries", (S(36, 7, 165, "B 'Sugar - bearish'"),), "Sugar Bearish", SUG, "Both in Aries.",
    lambda s: s["Mercury"].sign == "Aries" == s["Jupiter"].sign, ("Mercury", "Jupiter"), SIGNCALC)
win("ta_s36b08_mercury_leo_gemini_no_malefic", "Mercury in Leo or Gemini without any malefic planet or its aspect", (S(36, 8, 165, "B"),), "Sugar Bearish", SUG,
    "Mercury in Leo/Gemini with no malefic in its sign or aspecting it.", lambda s: s["Mercury"].sign in ("Leo", "Gemini") and not aspected_by_any(s, "Mercury", GRAHA_MAL) and s["Mercury"].sign, ("Mercury",), SIGNCALC)
win("ta_s36b09_jupiter_hasta_shravana", "Jupiter in Hasta or Shravana", (S(36, 9, 166, "B"),), "Sugar Bearish", SUG, "Jupiter in Hasta/Shravana.", nak_is("Jupiter", "Hasta", "Shravana"), ("Jupiter",))
win("ta_s36b04_mars_retro_virgo", "Mars retrograde in Virgo", (S(36, 4, 165, "B"),), "Sugar Bearish", SUG, "Mars retrograde in Virgo.", lambda s: s["Mars"].retro and s["Mars"].sign == "Virgo", ("Mars",), SIGNCALC)

win("ta_s37_01_sun_rahu_mercury_saturn_joins", "Sun, Rahu & Mercury together and Saturn enters the same sign", ("TA p.167 [printed 137] Section 37 'Biggest turning in commercial markets' #1", "KD p.131 #2"),
    "Trend becomes Bullish", ("commodities", "general"), "Sun, Rahu, Mercury and Saturn in one sign.", together("Sun", "Rahu", "Mercury", "Saturn"), ("Sun", "Rahu", "Mercury", "Saturn"), SIGNCALC)
win("ta_s37_03_direct_pluto_opp_retro_jupiter", "Direct Pluto opposite retrograde Jupiter", ("TA p.167 Section 37 #3",), "All agricultural commodities Bearish & all mining products Bullish (10 Aug 2013)",
    ("agri", "sector:Mining"), "Jupiter 7th from Pluto, Jupiter retrograde, Pluto direct.", lambda s: s.sign_dist("Pluto", "Jupiter") == 7 and s["Jupiter"].retro and not s["Pluto"].retro, ("Jupiter", "Pluto"), SIGNCALC + " " + RETCALC)
win("ta_s37_04_retro_pluto_opp_direct_jupiter", "Retrograde Pluto opposite direct Jupiter", ("TA p.167 Section 37 #4", "KD p.103 (2026: 'Jupiter Direct opposite Retrograde Pluto - agro up, mining down')"),
    "All agriculture products Bullish & mining products Bearish", ("agri", "sector:Mining"), "Jupiter 7th from Pluto, Pluto retrograde, Jupiter direct.",
    lambda s: s.sign_dist("Pluto", "Jupiter") == 7 and s["Pluto"].retro and not s["Jupiter"].retro, ("Jupiter", "Pluto"), SIGNCALC + " " + RETCALC)


def _mv_together(aspected):
    def p(s):
        if s["Mercury"].sign_i != s["Venus"].sign_i:
            return False
        mal = [b for b in GRAHA_MAL if aspects(s, b, "Mercury") and s[b].sign_i != s["Mercury"].sign_i]
        if aspected != bool(mal):
            return False
        return "aspected by " + ", ".join(mal) if mal else "no malefic aspect"
    return p


rule(id="ta_s37_05_mercury_venus_together", title="Venus & Mercury together in a sign (no malefic aspect)",
     refs=("TA p.167-168 Section 37 #5", "TA p.254-255 (story of 2020)", "KD p.138"),
     verdict="Bearish till the point of conjunction & Bullish thereafter", markets=("general", "commodities"),
     rule="Mercury and Venus in one sign, no malefic aspecting them.", calc=SIGNCALC + " Exact Mercury-Venus conjunction instant(s) inside the window are listed in the facts.",
     detector=windows(_mv_together(False), ("Mercury", "Venus"), placed_facts("Mercury", "Venus")),
     quals=("TA p.254: in Taurus, Gemini, Virgo, Libra & Pisces usually Bearish till conjunction, rising thereafter; in Cancer or Leo aspected by a malefic, tops out at conjunction and falls sharply.",
            "TA p.255 OBSERVATION: 'these two prophecies work irrespective of Mercury Venus Conjunction in any Sign'."))
rule(id="ta_s37_06_mercury_venus_together_malefic_aspect", title="Mercury & Venus together, aspected by a malefic",
     refs=("TA p.168 Section 37 #6", "KD p.138"), verdict="Bullish till the point of conjunction & Bearish thereafter (examples: Oct 1929 crash; 6 Aug 2015; 22 May 2020)",
     markets=("general", "commodities"), rule="Mercury and Venus in one sign with a TA malefic (Mars, Saturn, Rahu, Ketu; the Sun is always within 48 deg so its 7th aspect cannot fall there) casting drishti on that sign.",
     calc=SIGNCALC + " Malefic drishti by whole sign (Mars 4/7/8, Saturn 3/7/10, nodes 7).",
     detector=windows(_mv_together(True), ("Mercury", "Venus"), placed_facts("Mercury", "Venus")))


# ---------------- TA pp.146-153: Navamsh (D9) conjunction results ----------------
D9 = {
    "Sun": (146, {"Moon": "Bullish", "Mars": "Bullish", "Mercury": "Bullish", "Jupiter": "Bullish", "Venus": "Bullish", "Saturn": "Bearish", "Rahu": "Bearish", "Ketu": "Bearish", H: "Bullish", "Neptune": "Bearish", "Pluto": "Bullish"}),
    "Moon": (147, {"Mars": "Bullish", "Mercury": "Temporary Bounce", "Jupiter": "Bearish", "Venus": "Bearish", "Saturn": "Bullish", H: "Bullish", "Neptune": "Bearish", "Pluto": "Bullish", "Rahu": "Bullish", "Ketu": "Bearish"}),
    "Mars": (148, {"Mercury": "Bullish", "Jupiter": "Bullish", "Venus": "Bullish", "Saturn": "Bullish", "Rahu": "Bearish", H: "Sudden Rally", "Neptune": "Bearish", "Pluto": "Bullish"}),
    "Mercury": (149, {"Jupiter": "Bullish", "Venus": "Turning", "Saturn": "Bullish", "Rahu": "Bullish", "Ketu": "Bullish", H: "Sudden Rally", "Neptune": "Bearish", "Pluto": "Bullish"}),
    "Jupiter": (150, {"Venus": "Bullish", "Saturn": "Bullish", "Rahu": "Turning", "Ketu": "Bullish", H: "Bullish", "Neptune": "Bearish", "Pluto": "Bullish"}),
    "Venus": (151, {"Saturn": "Bullish", "Rahu": "Bearish", "Ketu": "Bullish", H: "Positive turning", "Neptune": "Bearish", "Pluto": "Bullish"}),
    "Saturn": (152, {"Rahu": "Positive turning", "Ketu": "Positive turning", H: "Bearish", "Neptune": "Bearish", "Pluto": "Bearish"}),
    "Rahu": (152, {H: "Bullish", "Neptune": "Bearish", "Pluto": "Bullish"}),
    H: (153, {"Neptune": "Biggest crash", "Pluto": "Bullish"}),
    "Neptune": (153, {"Pluto": "Bearish"}),
}
for a, (page, tab) in D9.items():
    for b, verdict in tab.items():
        ex = ()
        if {a, b} == {"Moon", "Mercury"}:
            ex = ("sub_moon_mercury_in_the_same_navamsh",)
        q = ()
        if a == "Sun" and b in ("Saturn", "Rahu", "Ketu"):
            q = ("KD p.131 #5: 'Sun with Saturn, Rahu, or Ketu in D9 - Bearish (occurs 25% annually)'.",)
        if {a, b} == {"Moon", "Mercury"}:
            q = ("CONFLICT: TA p.147 'Moon Mercury - Temporary Bounce'; KD p.85 and KD p.134 'Moon and Mercury conjunction in D9: Bullish'.",)
        rule(id=f"ta_d9_{name(a).lower()}_{name(b).lower()}", title=f"{name(a)}-{name(b)} conjunction in Navamsh (D9)",
             refs=(f"TA p.{page} [printed {page - 30}] 'Navamsh (D 9) conjunction results - {name(a).upper()}'",),
             verdict=verdict, markets=("general",), rule=f"{name(a)} and {name(b)} occupy the same navamsa sign.",
             calc="Navamsa sign of each body (Parashari D9, 3deg20' parts); window = both in one navamsa sign.",
             detector=windows(lambda s, a=a, b=b: s[a].nav_i == s[b].nav_i and s[a].nav, (a, b), placed_facts(a, b)),
             tier="moon" if "Moon" in (a, b) else "major", existing=ex, quals=q)

# ---------------- Vargottama ----------------
for b, verdict, refs in (("Jupiter", "Bullish (Vargottam Jupiter alone: TA p.258 '8th March to 18th March - Bullish'; KD p.101/p.104: positive for banking & finance)", ("TA p.53 [printed 23] Section 12 'Vargottam' (definition)", "TA p.258", "KD p.101", "KD p.104")),
                         ("Mars", "High Bullish, specifically sectors ruled by Mars (metals) when in Aries (TA p.263); debilitated Vargottam Mars in Cancer negative, esp. silver (KD p.119)", ("TA p.53 Section 12", "TA p.263", "KD p.119")),
                         ("Saturn", "Effect of a bearish conjunction 'may not be very steep' while Saturn is Vargottam (TA p.257)", ("TA p.53 Section 12", "TA p.256-257"))):
    win(f"ta_s12_vargottama_{b.lower()}", f"{b} Vargottam (same sign in D1 and D9)", refs, verdict,
        ("general", "silver") if b == "Mars" else ("general", "sector:Banking & Finance") if b == "Jupiter" else ("general",),
        f"{b}'s navamsa sign equals its rasi sign.", lambda s, b=b: s[b].vargottama and s[b].sign, (b,),
        "Vargottama = D9 sign equals D1 sign (first navamsa of movable, fifth of fixed, ninth of dual signs).",
        quals=("TA p.138: 'WHEN ANY PLANET IS VARGOTTAM ITS INTENSITY OF VEDHA IS HIGHEST'.",))

# ---------------- TA Section 16: Moon's navamsa (Moon layer) ----------------
NAV16 = {"Aries": "+", "Taurus": "+", "Gemini": "-", "Cancer": "+", "Leo": "+", "Virgo": "-", "Libra": "+", "Scorpio": "+",
         "Sagittarius": "-", "Capricorn": "+", "Aquarius": "+", "Pisces": "-"}
rule(id="ta_s16_moon_navamsa", title="Moon's Navamsh sign", refs=("TA p.68 [printed 38] Section 16 'Navamsh results'",),
     verdict="Aries+ Taurus+ Gemini- Cancer+ Leo+ Virgo- Libra+ Scorpio+ Sagittarius- Capricorn+ Aquarius+ Pisces-  (+ Bullish, - Bearish)",
     markets=("general",), rule="The Moon's D9 sign.", calc="Moon's navamsa (changes every ~6 h).",
     detector=windows(lambda s: f"{s['Moon'].nav} ({'Bullish' if NAV16[s['Moon'].nav] == '+' else 'Bearish'})", ("Moon",)),
     tier="moon", quals=("TA p.68 bottom: RELIABILITY VERY LOW AS MOON ALONE DON'T DRIVE THE MARKETS.",))

# ---------------- conjunction instants (turning dates) ----------------
def conj_rule(id, a, b, title, refs, verdict, markets, quals=(), existing=(), window_deg=None):
    def run(ctx):
        out = []
        for h in conjunctions(a, b)(ctx):
            s = snapshot(h.start)
            h.facts.update(placed_facts(a, b)(s, None))
            h.facts["motion"] = f"{name(a)} {'R' if s[a].retro else 'D'}, {name(b)} {'R' if s[b].retro else 'D'}"
            out.append(h)
        return out
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets,
         rule=f"Exact longitudinal conjunction of {name(a)} and {name(b)}.",
         calc="Instant where the sidereal longitudes are equal (sign change of the wrapped difference, bisected to 30 s).",
         detector=run, quals=quals, existing=existing)


conj_rule("kd_032_sun_mercury_conjunction", "Sun", "Mercury", "Sun-Mercury conjunction (major turning date)",
          ("TA p.89 [printed 59] S25 'Sun with Mercury'", "KD p.33", "KD p.100/108/117/126 (2026: 14 May, 13 Jul, 27 Aug, 4 Nov)"),
          "Major turning: 'any high low in 2 days +/- is major turning' (TA); 'Markets show high volatility; quick high or low may form' (KD)", ("general",),
          quals=("TA: 'they are never away from each other for more than 30 degree'.",))
conj_rule("kd_032_sun_neptune_conjunction", "Sun", "Neptune", "Sun-Neptune conjunction (high-probable turning event)",
          ("KD p.32", "TA p.92 S25 'Sun with Neptune - Together: Big high / lows do happen here'", "TA p.265 (2020: 8 March)"),
          "Big high / lows do happen here", ("general",))
conj_rule("kd_034_mercury_venus_conjunction", "Mercury", "Venus", "Mercury-Venus conjunction (turning event)",
          ("KD p.34", "TA p.149 (D9 'Mercury Venus - Turning')", "TA p.167-168 S37 #5/#6"), "Potential turning event; bearish-to-bullish (or reverse if malefic aspect) at the conjunction",
          ("general",), existing=("b017_venus_mercury_conjunction",))
conj_rule("ta_265_venus_neptune_conjunction", "Venus", "Neptune", "Venus-Neptune conjunction (major turning date)", ("TA p.265 'Major turning dates' a",), "Major turning date", ("general",))
conj_rule("ta_265_mercury_neptune_conjunction", "Mercury", "Neptune", "Mercury-Neptune conjunction (major turning date)", ("TA p.265 'Major turning dates' c",), "Major turning date", ("general",))

win("ta_258_venus_herschel_within_7", "Venus-Herschel conjunction within 7 degrees", ("TA p.258 'Venus Herschel conjunction'", "KD p.98 (2026: 24 April)"),
    "High effective; highest impact on sectors ruled by Venus & Herschel (KD: aluminium, aviation, high-speed vehicles, liquor), overall market Bullish", ("general", "sector:Aluminium, Aviation, Auto, Liquor"),
    "Venus within 7 deg of Uranus in longitude.", lambda s: abs(((s["Venus"].lon - s[H].lon + 180) % 360) - 180) <= 7, ("Venus", H),
    "Absolute longitudinal separation <= 7deg (TA: 'high effective when Venus & Herschel are within the range of 7 degree').")


# ======================================================================
# Sky-based rules: panchang days, eclipses, Sankranti, combustion.
# ======================================================================
from ..sky import parse as _parse  # noqa: E402


def vara(ctx, t, loc="new_york"):
    """Hindu weekday (sunrise to sunrise) of instant t at loc."""
    import bisect as _b
    sr = list(ctx.sky.sunrises(loc))
    i = _b.bisect_right(sr, t) - 1
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(CONF_TZ[loc])
    return sr[i].astimezone(tz).weekday()


CONF_TZ = {"new_york": "America/New_York", "mumbai": "Asia/Kolkata"}
PANCH_Q = ("Panchang read at New York sunrise (the Hindu day runs sunrise to sunrise). Indian almanacs read it at Indian sunrise, so a day near a tithi/nakshatra/yoga change can differ.",)
MONTHQ = "Lunar month: Purnimanta (Shukla paksha carries the amanta month's name, Krishna paksha the next one), the convention the 2026 document's own eclipse labels settle."


def day_rule(id, title, refs, verdict, markets, text, pred, quals=(), existing=(), tier="major", effect=""):
    def p(s, wd, d, ctx):
        r = pred(s, wd, d, ctx)
        if r:
            out = {"weekday": WEEKDAYS[wd], "tithi_at_NY_sunrise": tithi_label(s.tithi), "moon_nakshatra": s["Moon"].nak,
                   "yoga": YOGA[s.yoga - 1]}
            if isinstance(r, dict):
                out.update(r)
            return out
    return rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets, rule=text,
                calc="Tithi (12deg of Moon-Sun elongation), nakshatra and yoga at New York sunrise of each 2027 civil day; weekday of that day.",
                detector=daily(p, ("Moon",)), quals=PANCH_Q + tuple(quals), existing=existing, tier=tier, effect=effect)


from .detect import YOGA_NAMES as YOGA  # noqa: E402


def pmonth(ctx, t):
    return ctx.sky.purnimanta_month(t)


day_rule("ta_s24_19_ashtami_saturday", "Ashtami on Saturday", (s24(19, 80), s24(61, 83)), "Bullish", ("general",),
         "Udaya tithi Ashtami (either paksha) on a Saturday (#61 adds Tuesday).", lambda s, wd, d, c: s.tithi in (8, 23) and wd in (1, 5),
         existing=("b073_ashtami_on_tuesday_saturday",))
day_rule("ta_s24_20_shukla_navami_saturday", "Shukla Navami on Saturday", (s24(20, 80), s24(65, 83), "KD p.146"), "Bullish", ("general",),
         "Udaya tithi Shukla Navami on a Saturday.", lambda s, wd, d, c: s.tithi == 9 and wd == 5)
day_rule("ta_s24_18_ashwini_tuesday", "Ashwini nakshatra on Tuesday", (s24(18, 80), "KD p.144"), "Bullish", ("general",),
         "Moon in Ashwini at sunrise on a Tuesday.", lambda s, wd, d, c: s["Moon"].nak == "Ashwini" and wd == 1, existing=("b072_ashwini_on_tuesday",))
day_rule("ta_s24_05_ekadashi_friday", "Ekadashi on Friday", (s24(5, 78), "KD p.146"), "high Bearish", ("general",),
         "Udaya tithi Ekadashi on a Friday.", lambda s, wd, d, c: s.tithi in (11, 26) and wd == 4, existing=("b065_ekadashi_on_friday",))
day_rule("ta_s24_04_pradosh", "Pradosh (Trayodashi) day", (s24(4, 78), "KD p.146"), "Bearish", ("general",),
         "Udaya tithi Trayodashi in either paksha.", lambda s, wd, d, c: s.tithi in (13, 28), existing=("b064_pradosh",))
day_rule("ta_s24_01_chaturthi", "Sankashti (Krishna Chaturthi) / Vinayak (Shukla Chaturthi)", (s24(1, 78),), "Sankashti Bearish; Vinayak Chaturthi Bullish", ("general",),
         "Udaya tithi Chaturthi.", lambda s, wd, d, c: s.tithi in (4, 19) and {"verdict": "Bullish (Vinayak)" if s.tithi == 4 else "Bearish (Sankashti)"},
         existing=("b075_chaturthi_shukla_paksha", "b076_chaturthi_krishna_paksha"))
day_rule("ta_s24_27_ekadashi_vyatipata_vaidhriti", "Ekadashi with Vyatipata or Vaidhriti yoga", (s24(27, 80), s24(96, 85), "KD p.146"), "Bearish", ("general",),
         "Udaya tithi Ekadashi (either paksha; #96 says Shukla) and yoga Vyatipata or Vaidhriti at sunrise.",
         lambda s, wd, d, c: s.tithi in (11, 26) and s.yoga in (VYATIPATA, VAIDHRITI), existing=("b108_shukla_ekadashi_with_vyatipata_or_vaidhriti",))
day_rule("ta_s24_28_amavasya_sag_pisces", "Amavasya with Moon in Sagittarius or Pisces", (s24(28, 80), s24(91, 85), "KD p.145"), "Bearish", ("general",),
         "Udaya tithi Amavasya, Moon in Sagittarius or Pisces.", lambda s, wd, d, c: s.tithi == 30 and s["Moon"].sign in ("Sagittarius", "Pisces"),
         existing=("b060s_amavasya_moon_in_sagittarius_or_pisces",))
day_rule("ta_s24_58_amavasya_tuesday", "Amavasya on Tuesday", (s24(58, 83), "KD p.145"), "Bullish", ("general",), "Udaya tithi Amavasya on a Tuesday.",
         lambda s, wd, d, c: s.tithi == 30 and wd == 1, existing=("b060t_amavasya_on_tuesday",))
day_rule("ta_s35b04_amavasya_monday", "Amavasya on Monday", (S(35, 4, 160, "B (silver)"),), "Silver Bearish", SILV, "Udaya tithi Amavasya on a Monday.",
         lambda s, wd, d, c: s.tithi == 30 and wd == 0, existing=("cfg_silver_bearish_05_amavasya_on_monday",))
day_rule("ta_s24_59_shukla_pratipada_sat_sun", "Shukla Pratipada on Saturday or Sunday", (s24(59, 83),), "3 days Bullish", ("general",),
         "Udaya tithi Shukla Pratipada on Saturday or Sunday.", lambda s, wd, d, c: s.tithi == 1 and wd in (5, 6), existing=("b095_shukla_pratipada_on_saturday_or_sunday",), effect="3 days")
day_rule("ta_s24_60_vyatipata_sun_tue_sat", "Vyatipata yoga on Sunday, Tuesday or Saturday", (s24(60, 83), "KD p.148"), "Bullish", ("general",),
         "Yoga Vyatipata at sunrise on Sun/Tue/Sat.", lambda s, wd, d, c: s.yoga == VYATIPATA and wd in (6, 1, 5), existing=("b096_vyatipata_yoga_on_tuesday_saturday_or_sunday",))
day_rule("ta_s24_62_mrigashira_monday", "Mrigashira on Monday", (s24(62, 83),), "Bullish", ("general",), "Moon in Mrigashira at sunrise on a Monday.",
         lambda s, wd, d, c: s["Moon"].nak == "Mrigashira" and wd == 0, existing=("b097_moon_in_mrigashira_on_monday",))
day_rule("ta_s24_82_shukla_shashti_friday", "Shukla Shashti on Friday", (s24(82, 84),), "Bearish", ("general",), "Udaya tithi Shukla Shashti on a Friday.",
         lambda s, wd, d, c: s.tithi == 6 and wd == 4, existing=("b100_shukla_shasthi_on_friday",))
day_rule("ta_s24_84_ashtami_mon_thu_fri", "Ashtami on Monday, Thursday or Friday", (s24(84, 85),), "Bearish", ("general",), "Udaya tithi Ashtami on Mon/Thu/Fri.",
         lambda s, wd, d, c: s.tithi in (8, 23) and wd in (0, 3, 4), existing=("b074_ashtami_on_monday_thursday_friday",))
day_rule("ta_s24_86_anuradha_sunday", "Anuradha on Sunday", (s24(86, 85),), "Bearish", ("general",), "Moon in Anuradha at sunrise on a Sunday.",
         lambda s, wd, d, c: s["Moon"].nak == "Anuradha" and wd == 6, existing=("b102_anuradha_on_sunday",))
day_rule("ta_s24_87_vaidhriti_sunday", "Vaidhriti yoga on Sunday", (s24(87, 85),), "Bearish", ("general",), "Yoga Vaidhriti at sunrise on a Sunday.",
         lambda s, wd, d, c: s.yoga == VAIDHRITI and wd == 6)
day_rule("ta_s24_88_tuesday_shatabhisha", "Shatabhisha on Tuesday", (s24(88, 85), "KD p.144"), "Bearish", ("general",), "Moon in Shatabhisha at sunrise on a Tuesday.",
         lambda s, wd, d, c: s["Moon"].nak == "Shatabhisha" and wd == 1, existing=("b103_shatabhisha_on_tuesday",))
day_rule("ta_s24_89_thursday_mrigashira", "Mrigashira on Thursday", (s24(89, 85), "KD p.144"), "Bearish", ("general",), "Moon in Mrigashira at sunrise on a Thursday.",
         lambda s, wd, d, c: s["Moon"].nak == "Mrigashira" and wd == 3, existing=("b104_mrigashira_on_thursday",))
day_rule("ta_s24_90_uttara_ashadha_monday", "Uttara Ashadha on Monday", (s24(90, 85),), "Bearish", ("general",), "Moon in Uttara Ashadha at sunrise on a Monday.",
         lambda s, wd, d, c: s["Moon"].nak == "Uttara Ashadha" and wd == 0, existing=("b105n_uttara_ashadha_on_monday_moon_not_vargottama",))
day_rule("ta_s24_99_shukla_trayodashi_sat_tue", "Shukla Trayodashi on Saturday or Tuesday", (s24(99, 86), "KD p.146"), "Bearish", ("general",),
         "Udaya tithi Shukla Trayodashi on Sat/Tue.", lambda s, wd, d, c: s.tithi == 13 and wd in (5, 1), existing=("b109_shukla_trayodashi_on_tuesday_or_saturday",))
day_rule("ta_s24_38_chaitra_purnima_tuesday", "Full Moon of Chaitra on Tuesday", (s24(38, 81), "KD p.145"), "Bullish", ("general",),
         "Udaya tithi Purnima in Chaitra on a Tuesday.", lambda s, wd, d, c: s.tithi == 15 and wd == 1 and pmonth(c, s.t) == "Chaitra" and {"month": "Chaitra"}, quals=(MONTHQ,))
day_rule("ta_s24_67_vaisakh_purnima_tuesday", "Vaisakh Purnima on Tuesday", (s24(67, 83), "KD p.147"), "Very Bullish", ("general",),
         "Udaya tithi Purnima in Vaishakh on a Tuesday.", lambda s, wd, d, c: s.tithi == 15 and wd == 1 and pmonth(c, s.t) == "Vaishakh" and {"month": "Vaishakh"}, quals=(MONTHQ,))
day_rule("ta_s24_97_jyeshtha_shukla_panchami_sat", "Jyeshtha Shukla Panchami on Saturday", (s24(97, 86),), "Bearish", ("general",),
         "Udaya tithi Shukla Panchami in Jyeshtha on a Saturday.", lambda s, wd, d, c: s.tithi == 5 and wd == 5 and (pmonth(c, s.t) or "").endswith("Jyeshtha") and {"month": pmonth(c, s.t)}, quals=(MONTHQ,))
day_rule("ta_s24_98_ashadh_shukla_ekadashi_fri", "Ashadh Shukla Ekadashi on Friday", (s24(98, 86),), "Bearish", ("general",),
         "Udaya tithi Shukla Ekadashi in Ashadh on a Friday.", lambda s, wd, d, c: s.tithi == 11 and wd == 4 and (pmonth(c, s.t) or "").endswith("Ashadh") and {"month": pmonth(c, s.t)}, quals=(MONTHQ,))
day_rule("ta_s36b02_kartik_shukla_panchami_thu", "Kartik Shukla Panchami on Thursday", (S(36, 2, 165, "B (sugar)"),), "Sugar Bearish", SUG,
         "Udaya tithi Shukla Panchami in Kartik on a Thursday.", lambda s, wd, d, c: s.tithi == 5 and wd == 3 and (pmonth(c, s.t) or "").endswith("Kartik") and {"month": pmonth(c, s.t)}, quals=(MONTHQ,))
day_rule("ta_s36b03_margshirsh_krishna_panchami_thu_fri", "Margshirsh Krishna Panchami on Thursday/Friday", (S(36, 3, 165, "B (sugar)"),), "Sugar Bearish", SUG,
         "Udaya tithi Krishna Panchami in Margashirsh on Thu/Fri.", lambda s, wd, d, c: s.tithi == 20 and wd in (3, 4) and (pmonth(c, s.t) or "").endswith("Margashirsh") and {"month": pmonth(c, s.t)},
         quals=(MONTHQ, "CONFLICT: the 2026 document's config rule (cfg_sugar_bullish_07) prints the same condition as BULLISH; TA S36 B3 prints it as BEARISH. Both are shown."),
         existing=("cfg_sugar_bullish_07_margshirsh_krishna_panchami",))
day_rule("ta_s36b06_revati_paush_shukla_navami", "Revati nakshatra on Paush Shukla Navami", (S(36, 6, 165, "B (sugar)"),), "Sugar Bearish", SUG,
         "Moon in Revati on the day of Paush Shukla Navami.", lambda s, wd, d, c: s.tithi == 9 and s["Moon"].nak == "Revati" and (pmonth(c, s.t) or "").endswith("Paush"), quals=(MONTHQ,))


def _kshaya_tithis(ctx, which):
    out = []
    for sp in ctx.sky.tithi_spans():
        if sp.open_start or sp.open_end:
            continue
        if sp.start.year != ctx.year and sp.end.year != ctx.year:
            continue
        n = len(ctx.sky.horizon_crossings_within("sunrise", "new_york", sp))
        if n == 0 and sp.value["tithi"] in which:
            out.append(Hit(sp.start, sp.end, ("Moon", "Sun"), {"tithi": tithi_label(sp.value["tithi"]), "kshaya": "no New York sunrise inside the tithi"}))
    return out


rule(id="ta_s24_17_krishna_trayodashi_kshay", title="Trayodashi Kshay in dark fortnight", refs=(s24(17, 80), "KD p.146"), verdict="4 days Bullish",
     markets=("general",), rule="Krishna Trayodashi spans no sunrise (kshaya).", calc="Tithi spans (12deg elongation steps); kshaya = no New York sunrise between its start and end.",
     detector=lambda ctx: _kshaya_tithis(ctx, (28,)), quals=PANCH_Q, effect="4 days", existing=("b067_kshay_tithi_krishna_paksha",))
rule(id="ta_s24_85_shukla_trayodashi_kshay", title="Kshay of Shukla Trayodashi", refs=(s24(85, 85), "KD p.146"), verdict="3 days Bearish",
     markets=("general",), rule="Shukla Trayodashi spans no sunrise.", calc="As above.", detector=lambda ctx: _kshaya_tithis(ctx, (13,)), quals=PANCH_Q, effect="3 days",
     existing=("b066_kshay_tithi_shukla_paksha",))
rule(id="ta_s24_94_kshay_shukla_dashami_to_purnima", title="Tithi Kshay from Shukla Dashami till Purnima", refs=(s24(94, 85), "KD p.147"), verdict="high bearish",
     markets=("general",), rule="A kshaya tithi among Shukla Dashami..Purnima.", calc="Kshaya as above.", detector=lambda ctx: _kshaya_tithis(ctx, range(10, 16)), quals=PANCH_Q,
     existing=("b066_kshay_tithi_shukla_paksha",))
rule(id="kd_147_kshay_krishna_dashami_to_amavasya", title="Tithi Kshay from Krishna Dashami to Amavasya", refs=("KD p.147",), verdict="High Bullish",
     markets=("general",), rule="A kshaya tithi among Krishna Dashami..Amavasya.", calc="Kshaya as above.", detector=lambda ctx: _kshaya_tithis(ctx, range(25, 31)), quals=PANCH_Q,
     existing=("b067_kshay_tithi_krishna_paksha",))


def _purnima_short(ctx):
    out = []
    for sp in ctx.sky.tithi_spans():
        if sp.value["tithi"] != 15 or sp.open_start or sp.open_end:
            continue
        srs = ctx.sky.horizon_crossings_within("sunrise", "new_york", sp)
        if srs:
            rem = (sp.end - srs[-1]).total_seconds() / 3600
            if rem < 2.0 and sp.end.year == ctx.year:
                out.append(Hit(srs[-1], srs[-1] + dt.timedelta(days=2), ("Moon", "Sun"), {"purnima_after_sunrise_hours": round(rem, 2), "ghadi": round(rem * 2.5, 2)}))
    return out


rule(id="ta_s24_16_purnima_lt_5_ghadi", title="Purnima less than 5 ghadi", refs=(s24(16, 80), "KD p.145"), verdict="2 days Bullish", markets=("general",),
     rule="Purnima prevails for less than 5 ghadi (2 h) after sunrise on its day.",
     calc="Purnima tithi span; time from the last New York sunrise inside it to its end < 2 h (1 ghadi = 24 min, TA p.77). Effect window 2 days.",
     detector=_purnima_short, quals=PANCH_Q + ("'Less than 5 ghadi' read as the Purnima remaining after sunrise (the almanac's printed ghadi figure).",), effect="2 days")


# ---------------- eclipses ----------------
def eclipse_rule(id, title, refs, verdict, markets, kind, pred, quals=(), existing=()):
    def run(ctx):
        out = []
        for r in ctx.sky.class_records("eclipse"):
            if r["rule_family"] != f"eclipse/{kind}":
                continue
            t = _parse(r["time"]["t_start_utc"])
            if t.year != ctx.year:
                continue
            s = snapshot(t.replace(microsecond=0))
            info = {"weekday_NY": WEEKDAYS[vara(ctx, t)], "weekday_IST": WEEKDAYS[vara(ctx, t, "mumbai")],
                    "month": ctx.sky.eclipse_month(r), "moon_nakshatra": s["Moon"].nak, "sun_sign": s["Sun"].sign,
                    "moon_sign": s["Moon"].sign, "yoga": YOGA[s.yoga - 1], "type": next((f for f in r["qa"]["flags"] if f.startswith("type=")), "")}
            res = pred(info, s)
            if res:
                if isinstance(res, dict):
                    info.update(res)
                out.append(Hit(t, None, ("Sun", "Moon"), info))
        return out
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets,
         rule=title + ".", calc="Eclipse maximum from Swiss Ephemeris (global); weekday = Hindu day (sunrise-to-sunrise) at New York, IST weekday shown alongside; month " + MONTHQ,
         detector=run, quals=quals + ("An eclipse's visibility from New York is not required by either source.",), existing=existing)


def wd_any(info, *days, both=False):
    return info["weekday_NY"] in days or info["weekday_IST"] in days


eclipse_rule("ta_s24_57_moon_eclipse_monday", "Moon eclipse on Monday", (s24(57, 83), "KD p.133 #6"), "Bullish", ("general",), "lunar", lambda i, s: wd_any(i, "Monday"))
eclipse_rule("ta_s24_103_moon_eclipse_tuesday", "Moon eclipse on Tuesday", (s24(103, 86), "KD p.134"), "Bullish", ("general",), "lunar", lambda i, s: wd_any(i, "Tuesday"),
             existing=("b110_lunar_eclipse_on_tuesday",))
eclipse_rule("ta_s34a07_moon_eclipse_wednesday", "Moon eclipse on Wednesday", (S(34, 7, 154, "A (gold)"),), "Gold: instant Bullish", GOLD, "lunar", lambda i, s: wd_any(i, "Wednesday"))
eclipse_rule("ta_s35b09_moon_eclipse_sunday", "Moon eclipse on Sunday", (S(35, 9, 160, "B (silver)"),), "Silver: falls 15 days ahead", SILV, "lunar", lambda i, s: wd_any(i, "Sunday"),
             existing=("cfg_silver_bearish_07_moon_eclipse_on_sunday",))
eclipse_rule("ta_s24_104_moon_eclipse_vaishakh_shravan_ashvin", "Moon eclipse in Vaishakh, Shravan or Ashvin month", (s24(104, 86), "KD p.134"), "Bullish", ("general",), "lunar",
             lambda i, s: (i["month"] or "").split()[-1] in ("Vaishakh", "Shravan", "Ashwin"), existing=("b111_lunar_eclipse_in_vaishakha_shravana_or_ashwin",))
eclipse_rule("ta_s24_105_moon_eclipse_jyeshtha_paush", "Moon eclipse in Jyeshtha or Paush month", (s24(105, 86), "KD p.134"), "first Bearish than Bullish", ("general",), "lunar",
             lambda i, s: (i["month"] or "").split()[-1] in ("Jyeshtha", "Paush"))
eclipse_rule("ta_s24_106_moon_eclipse_margashirsh", "Moon eclipse in Margashirsh month", (s24(106, 86), "KD p.134"), "Bearish", ("general",), "lunar",
             lambda i, s: (i["month"] or "").split()[-1] == "Margashirsh")
eclipse_rule("ta_s24_64_moon_eclipse_paush_purnima", "Moon eclipse on Paush Purnima", (s24(64, 83),), "Big Bullish", ("general",), "lunar", lambda i, s: (i["month"] or "").split()[-1] == "Paush")
eclipse_rule("ta_s36a03_moon_eclipse_falgun", "Moon eclipse in the month of Falgun", (S(36, 3, 162, "A (sugar)"),), "Sugar Bullish", SUG, "lunar", lambda i, s: (i["month"] or "").split()[-1] == "Falgun")
eclipse_rule("ta_s36b10_moon_eclipse_vaishak_jyeshtha_kartik", "Moon eclipse in Vaishakh, Jyeshtha or Kartik", (S(36, 10, 166, "B (sugar)"),), "Sugar Bearish", SUG, "lunar",
             lambda i, s: (i["month"] or "").split()[-1] in ("Vaishakh", "Jyeshtha", "Kartik"))
eclipse_rule("ta_s24_102_sun_eclipse_nakshatras", "Sun eclipse in Rohini, Punarvasu, Purva Phalguni, Vishakha, Mula or Purva Ashadha", (s24(102, 86), "KD p.132"), "Bullish", ("general",), "solar",
             lambda i, s: i["moon_nakshatra"] in ("Rohini", "Punarvasu", "Purva Phalguni", "Vishakha", "Mula", "Purva Ashadha"))
eclipse_rule("ta_s24_100_vyatipata_on_sun_eclipse", "Vyatipata yoga on Sun eclipse", (s24(100, 86), "KD p.133 #1"), "Bullish", ("general",), "solar", lambda i, s: s.yoga == VYATIPATA)
eclipse_rule("ta_s24_68_shravan_amavasya_sun_eclipse", "Shravan Amavasya & Sun eclipse", (s24(68, 83), "KD p.132"), "Bullish", ("general",), "solar", lambda i, s: (i["month"] or "").split()[-1] == "Shravan")
eclipse_rule("ta_s36a04_sun_eclipse_sunday", "Sun eclipse on Sunday", (S(36, 4, 162, "A (sugar)"),), "Sugar Bullish", SUG, "solar", lambda i, s: wd_any(i, "Sunday"))
eclipse_rule("ta_s35a22_sun_eclipse_falgun_jyeshtha_tuesday", "Sun eclipse in Falgun or Jyeshtha on Tuesday", (S(35, 22, 159, "A (silver)"),), "Silver Bullish", SILV, "solar",
             lambda i, s: (i["month"] or "").split()[-1] in ("Falgun", "Jyeshtha") and wd_any(i, "Tuesday"))
eclipse_rule("ta_s13_scorpio_sun_eclipse", "Sun eclipse in Scorpio", ("TA p.56 [printed 26] Section 13 Scorpio: 'If Sun Eclipse too happen - unprecedented Bullish'",), "unprecedented Bullish (with Mars(R)/Saturn(R)/Rahu/Sun any 2 in Scorpio)", ("general",), "solar",
             lambda i, s: i["sun_sign"] == "Scorpio")


def _sun_then_moon(ctx):
    sol = [_parse(r["time"]["t_start_utc"]) for r in ctx.sky.class_records("eclipse") if r["rule_family"] == "eclipse/solar"]
    lun = [_parse(r["time"]["t_start_utc"]) for r in ctx.sky.class_records("eclipse") if r["rule_family"] == "eclipse/lunar"]
    out = []
    for a in sol:
        for b in lun:
            if dt.timedelta(days=10) < b - a < dt.timedelta(days=20) and (a.year == ctx.year or b.year == ctx.year):
                out.append(Hit(a, b, ("Sun", "Moon"), {"solar_max": a.isoformat(), "lunar_max": b.isoformat()}))
    return out


rule(id="kd_132_sun_eclipse_then_moon_eclipse", title="Sun eclipse followed by Moon eclipse within 15 days", refs=("KD p.132", "KD p.118"), verdict="Auspicious - positive market tone",
     markets=("general",), rule="A lunar eclipse about a fortnight after a solar eclipse.", calc="Pairs of eclipse maxima 10-20 days apart, solar first.", detector=_sun_then_moon)


# ---------------- Sankranti: TA Sections 26, 27, 30; S24 #39/#80/#95/#101 ----------------
M15 = ("Bharani", "Ardra", "Ashlesha", "Swati", "Jyeshtha", "Shatabhisha")
M45 = ("Rohini", "Punarvasu", "Uttara Phalguni", "Vishakha", "Uttara Ashadha", "Uttara Bhadrapada")
MUHURTA_RESULT = {15: "Grains, Fruits & Vegetables costly, inflation rises, Bullish in stock Market, excess or deficiency of Rains",
                  30: "Prices & inflation in small range, Markets neutral, medium rains",
                  45: "Excessive rains, supply exceed demand, negative Markets & low inflation"}
WINDOW_PART = {"Taurus": "first", "Cancer": "first", "Leo": "first", "Scorpio": "first", "Aquarius": "first",
               "Gemini": "last", "Virgo": "last", "Sagittarius": "last", "Capricorn": "last", "Pisces": "last",
               "Aries": "middle", "Libra": "middle"}
EFFECT_LEN = {"Cancer": "six months", "Libra": "six months", "Aries": "twelve months"}


def sankrantis(ctx):
    from .engine import crossings
    out = []
    for t, a, b in crossings(ctx.grid, lambda s: s["Sun"].sign):
        if t.year != ctx.year:
            continue
        s = snapshot(t)
        nk = s["Moon"].nak
        m = 15 if nk in M15 else 45 if nk in M45 else 30
        out.append((t, b, s, m))
    return out


def sank_rule(id, title, refs, verdict, markets, text, pred, quals=(), existing=(), extra=None):
    def run(ctx):
        hits = []
        for t, sign, s, m in sankrantis(ctx):
            info = {"sign_entered": sign, "moon_nakshatra_at_ingress": s["Moon"].nak, "muhurta": m,
                    "weekday_NY": WEEKDAYS[vara(ctx, t)], "weekday_IST": WEEKDAYS[vara(ctx, t, "mumbai")],
                    "sun_moon_same_sign": s["Moon"].sign == s["Sun"].sign}
            r = pred(info, s)
            if r:
                if isinstance(r, dict):
                    info.update(r)
                end = None
                if extra:
                    end = extra(t, sign)
                hits.append(Hit(t, end, ("Sun", "Moon"), info))
        return hits
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets, rule=text,
         calc="Sun's sidereal sign ingress (Sankranti), bisected to 30 s; Moon's nakshatra at that instant; weekday = Hindu day at New York (IST weekday alongside).",
         detector=run, quals=quals, existing=existing)


sank_rule("ta_s27_sankranti_muhurta", "Sankranti type by Moon's nakshatra (15 / 30 / 45 Muhurta)",
          ("TA p.118 [printed 88] Section 27", "TA p.119 [printed 89] results", s24(95, 85), s24(101, 86), "KD p.130 #4/#5"),
          "15 Muhurta: Bullish in stock market (KD: bullish in commodities); 30: neutral; 45: negative markets (KD: bearish in commodities)",
          ("general", "commodities", "grains"), "Moon's nakshatra at the Sun's ingress decides the Sankranti's muhurta class.",
          lambda i, s: {"result": MUHURTA_RESULT[i["muhurta"]]},
          quals=("TA p.118 prints the third row's label as '60 Muhurta' while its text and the results table (p.119) say 45 Muhurta; 45 is used.",
                 "TA p.120: if the majority of a year's Sankrantis are 45 Muhurta -> excess, people happy, markets negative; majority 15 Muhurta -> deficiency, markets positive."))
sank_rule("ta_s26_sankranti_effective_window", "Sankranti price-range window (Sun transgression)",
          ("TA p.116-117 [printed 86-87] Section 26 'Sankranti (Sun transgression)'",),
          "The price range made in the stated ten days decides the trend; effective for the stated period", ("general",),
          "Taurus, Cancer, Leo, Scorpio, Aquarius: first ten days decide; Gemini, Virgo, Sagittarius, Capricorn, Pisces: last ten days; Aries & Libra: middle ten days. Cancer & Libra effective six months, Aries twelve months, the rest only in the days mentioned.",
          lambda i, s: {"deciding_days": WINDOW_PART[i["sign_entered"]] + " ten days of the solar month", "effective": EFFECT_LEN.get(i["sign_entered"], "the deciding days only")},
          quals=("TA p.117 examples: Aries 23 Apr-5 May range effective till 13/14 Apr next year; Cancer 17-27 Jul till 14/15 Jan; Libra 27 Oct-7 Nov till 13/14 Apr.",))
sank_rule("ta_s24_39_sagittarius_sankranti_weekday", "Sagittarius Sankranti weekday", (s24(39, 81), s24(80, 84), "KD p.130 #3"),
          "Sunday, Tuesday or Saturday - Bullish; Friday - Bearish", ("general",), "Weekday of the Sun's ingress into Sagittarius.",
          lambda i, s: i["sign_entered"] == "Sagittarius" and (i["weekday_NY"] in ("Sunday", "Tuesday", "Saturday", "Friday") or i["weekday_IST"] in ("Sunday", "Tuesday", "Saturday", "Friday")))
sank_rule("ta_s35b12_cancer_sankranti_saturday", "Cancer Sankranti on Saturday", (S(35, 12, 161, "B (silver)"),), "Silver Bearish", SILV, "Sun enters Cancer on a Saturday.",
          lambda i, s: i["sign_entered"] == "Cancer" and "Saturday" in (i["weekday_NY"], i["weekday_IST"]))
sank_rule("ta_s36a07_libra_sankranti_tuesday", "Libra Sankranti on Tuesday", (S(36, 7, 163, "A (sugar)"),), "Sugar Bullish", SUG, "Sun enters Libra on a Tuesday.",
          lambda i, s: i["sign_entered"] == "Libra" and "Tuesday" in (i["weekday_NY"], i["weekday_IST"]))
sank_rule("ta_s35a10_sun_moon_together_sankranti", "Sun & Moon together at Sankranti entering time", (S(35, 10, 158, "A (silver)"),), "Silver Bullish", SILV,
          "Moon in the sign the Sun enters, at the ingress instant.", lambda i, s: i["sun_moon_same_sign"])


def _cabinet(ctx):
    """TA S30: the lords of the year's defining days."""
    LORD = {0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Sun"}
    hits = []
    # Chaitra Shukla Pratipada: first sunrise inside Shukla Pratipada of Chaitra.
    for sp in ctx.sky.tithi_spans():
        if sp.value["tithi"] == 1 and sp.start.year == ctx.year and ctx.sky.purnimanta_month(sp.start + dt.timedelta(hours=1)) == "Chaitra":
            for loc in ("new_york", "mumbai"):
                srs = ctx.sky.horizon_crossings_within("sunrise", loc, sp)
                day = vara(ctx, srs[0], loc) if srs else vara(ctx, sp.start, loc)
                hits.append(("King (Raja)", "Chaitra Shukla Pratipada", sp.start, loc, LORD[day], WEEKDAYS[day], bool(srs)))
            break
    roles = {"Aries": "Mantri", "Cancer": "Sasyesh (cultivation)", "Sagittarius": "Dhanyesh (foodgrains)", "Libra": "Rashesh (juicy products)",
             "Capricorn": "Nirshesh (metals & mining)", "Pisces": "Falesh (fruits & vegetables)", "Virgo": "Dhanesh (wealth)", "Leo": "Durgesh (defence)"}
    for t, sign, s, m in sankrantis(ctx):
        if sign in roles:
            for loc in ("new_york", "mumbai"):
                d = vara(ctx, t, loc)
                hits.append((roles[sign], f"Sun enters {sign}", t, loc, LORD[d], WEEKDAYS[d], True))
    from .engine import crossings
    for t, a, b in crossings(ctx.grid, lambda s: s["Sun"].nak):
        if b == "Ardra" and t.year == ctx.year:
            for loc in ("new_york", "mumbai"):
                d = vara(ctx, t, loc)
                hits.append(("Meghesh (rainfall)", "Sun enters Ardra", t, loc, LORD[d], WEEKDAYS[d], True))
    out = []
    KING = {"Sun": "Production of Grains, Vegetable & Fruits is less. End of the year is most deficient Phase",
            "Moon": "Excess of everything - still 7th & 8th month prices rise", "Mars": "Deficiency & prices move higher - unrest & chaos",
            "Mercury": "Business is good despite soft prices & sufficient availability of goods",
            "Jupiter": "Excess of everything & prices fall but if rains in Ashvin month than prices rise again",
            "Venus": "Excess & prices fall except Rice which rise big in last 6 months", "Saturn": "Less rainfall & price rise - specially Coal, Iron & Wool"}
    MANTRI = {"Sun": "Grains & Juicy products Bullish", "Moon": "White goods production is high so Prices fall like Rice, Cotton, Silver & all other White goods",
              "Mars": "Wheat & Milk products become very costly", "Mercury": "Everything available in plenty & cheap",
              "Jupiter": "Dry fruits, Fruits & Grains all available in excess with good rainfall", "Venus": "Similar like Jupiter", "Saturn": "Similar to Mars"}
    for role, basis, t, loc, lord, wd, ok in hits:
        res = (KING.get(lord) if role.startswith("King") else MANTRI.get(lord) if role == "Mantri"
               else "TA prints no result table for this rank (p.125 defines it only)")
        out.append(Hit(t, None, ("Sun",), {"role": role, "basis": basis, "location": loc, "weekday": wd, "lord": lord, "result": res,
                                           "pratipada_touches_sunrise": ok}))
    return out


rule(id="ta_s30_yearly_cabinet", title="Yearly cabinet (Samvat cabinet) of the Hindu year",
     refs=("TA p.125 [printed 95] Section 30", "TA p.126-127 [printed 96-97] results for King and Mantri", "TA S36 A5/A6 & B1 (sugar: King Sun/Mars; Rashesh Venus)"),
     verdict="King: per p.126 table; Mantri: per p.127 table (other ranks: no result table printed)", markets=("general", "grains", "silver", "commodities"),
     rule="Lord of the weekday of each defining day: King = Chaitra Shukla Pratipada; Mantri = Sun into Aries; etc.",
     calc="Weekday of the Hindu day (sunrise to sunrise) holding each defining instant, computed for both New York and Mumbai; Chaitra Shukla Pratipada = the Pratipada following the Chaitra new moon, weekday at the first sunrise inside it.",
     detector=_cabinet, tier="yearly",
     quals=("Indian almanacs fix the cabinet at Indian sunrise; the Mumbai row is the traditional one, the New York row is shown for this edition. If they differ, both are printed.",
            "TA S36 A5/A6: Sun as King -> sugar bullishness in Ashadh; Mars as King -> sugar bullish till Bhadrapada. S36 B1: Rashesh Venus -> sugar bearish."))

# ---------------- combustion & rise (TA S10/S17/S18; S24 #109/#110; S34/S35) ----------------
MERC_TYPES = ((35.0, "Prakrita (~40+ days)", "Bearish"), (26.25, "Vimishra (~30 days)", "Medium"), (20.25, "Sankshipta (~22.5 days)", "Bullish"),
              (16.5, "Tikshna (~18 days)", "Bullish"), (12.75, "Ghora (~15 days)", "Bullish"), (9.75, "Papa (~10.5 days)", "Bullish"), (0, "Yogantika (~9 days)", "Bullish"))


def combust_rule(id, title, refs, verdict, markets, body, pred, quals=(), existing=(), use="combust"):
    def run(ctx):
        out = []
        for sp in ctx.sky.combust_spans(body):
            if sp.open_start or sp.open_end:
                continue
            if sp.start.year != ctx.year and sp.end.year != ctx.year:
                continue
            days = (sp.end - sp.start).days
            mid = snapshot((sp.start + (sp.end - sp.start) / 2).replace(microsecond=0))
            s0 = snapshot(sp.start.replace(microsecond=0))
            s1 = snapshot(sp.end.replace(microsecond=0))
            rise_dir = next((_flag(r, "direction") for r in ctx.sky.class_records("combustion")
                             if r["bodies"][0] == body and r["rule_family"] == "visibility/rise" and _parse(r["time"]["t_start_utc"]) == sp.end), None)
            info = {"combust_direction": sp.value, "rise_direction": rise_dir, "days": days,
                    "retro_at_combust": s0[body].retro, "retro_mid": mid[body].retro, "sign_at_combust": s0[body].sign,
                    "sign_at_rise": s1[body].sign, "nakshatra_at_rise": s1[body].nak,
                    "with_at_rise": [b for b in ("Sun", "Mars", "Saturn", "Rahu") if b != body and s1[b].sign_i == s1[body].sign_i]}
            r = pred(info)
            if r:
                if isinstance(r, dict):
                    info.update(r)
                if use == "rise":
                    out.append(Hit(sp.end, None, (body, "Sun"), info))
                else:
                    out.append(Hit(sp.start, sp.end, (body, "Sun"), info))
        return out
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets, rule=title + ".",
         calc="Combustion (asta) and rise (udaya) dates from the astronomy layer's kalamsha method at Mumbai (date-granular; the 2026 document's convention); East/West as the layer records it.",
         detector=run, quals=quals + ("Combust/rise dates are civil dates, not instants: the event is date-only.",), existing=existing)


def _flag(rec, key):
    for f in rec["qa"]["flags"]:
        if f.startswith(key + "="):
            return f.split("=", 1)[1]


def _merc_type(i):
    for lo, nm, v in MERC_TYPES:
        if i["days"] >= lo:
            return {"combustion_type": nm, "type_result": v}


combust_rule("ta_s17_mercury_combustion_type", "Mercury combustion type (7 types)", ("TA p.69 [printed 39] Section 17", "TA p.51 [printed 21] Section 10 (2016 Prakruta example)", "TA p.26, p.29"),
             "Prakrita - Bearish; Vimishra - Medium; Sankshipta, Tikshna, Ghora, Papa, Yogantika - Bullish", ("general",), "Mercury", _merc_type,
             quals=("Type assigned from the combustion's length in days using midpoints between the printed nominal durations (40/30/22.5/18/15/10.5/9); TA p.26 calls Prakruta a 'speed of Mercury', so the type is a speed class and the length is its proxy.",
                    "TA p.70: If combustion Bullish but aspected by malefic - Bearish; if Bearish but aspected by benefic - Bullish.",
                    "TA p.70: If combust in direct motion: starts Bearish but Bullish after conjunction with Sun; if combust in retrogression it is Bullish.",
                    "TA p.70: Bullishness returns after speed of Mercury crosses speed of Venus (see 'Mercury Manifestation')."))
combust_rule("ta_s17_mercury_rise_west", "Mercury rises in West", ("TA p.70 Section 17", "TA S34 B5 (gold)"), "Changes the trend which has been going prior to it; gold Bearish",
             ("general", "gold"), "Mercury", lambda i: i["rise_direction"] == "West", use="rise", existing=("cfg_gold_bearish_04_mercury_rise_in_west",))
combust_rule("ta_s17_mercury_rise_east", "Mercury rises in East", ("TA p.70 Section 17",), "Small bounce immediately but very short term", ("general",), "Mercury",
             lambda i: i["rise_direction"] == "East", use="rise")
combust_rule("ta_s35a19_retro_mercury_combust", "Retrograde Mercury goes combust", (S(35, 19, 159, "A (silver)"), "TA p.70 'if Combust in Retrogression its Bullish'"),
             "Silver: short term uptrend; market Bullish", ("silver", "general"), "Mercury", lambda i: i["retro_mid"], existing=("cfg_silver_bullish_17_retrograde_mercury_goes_combust",))
combust_rule("ta_s36a20_retro_mercury_combust_cancer", "Retrograde Mercury goes combust in Cancer", (S(36, 20, 164, "A (sugar)"),), "Sugar Bullish", SUG, "Mercury",
             lambda i: i["retro_mid"] and i["sign_at_combust"] == "Cancer")
combust_rule("ta_s18_venus_combust_west", "Venus combust in West", ("TA p.71 [printed 41] Section 18", S(35, 15, 159, "A (silver)"), "KD p.122 (2026: 15-27 Oct)"),
             "Extreme Bullish (TA S18); silver Bullish till it rises in East", ("general", "silver"), "Venus", lambda i: i["combust_direction"] == "West",
             quals=("CONFLICT: TA p.261 (2020 prophecy 1): 'Venus getting Combust in West is Bearish'. Section 18 and S35 A15 say Bullish.",))
combust_rule("ta_s18_venus_combust_east", "Venus combust in East", ("TA p.71 Section 18",), "Bullish", ("general",), "Venus", lambda i: i["combust_direction"] == "East",
             existing=("b015a_venus_combust_east",), quals=("The 2026 document (b015a) prints Venus combust East as 'Bearish for Fifteen days, thereafter Bullish'; TA S18 prints 'Combust in East Bullish'.",))
combust_rule("ta_s18_venus_rise_east", "Venus rises in East", ("TA p.71 Section 18", "TA p.261 prophecy 3", "KD p.124"),
             "Bullish (in Aries, Taurus, Cancer, Libra, Scorpio, Capricorn, Aquarius - Bullish; with Sun, Mars, Saturn or Rahu - very Bullish; other signs minor Bullish; Bullish for 2 to 3 months)",
             ("general",), "Venus", lambda i: i["rise_direction"] == "East" and {"sign_class": "listed sign" if i["sign_at_rise"] in ("Aries", "Taurus", "Cancer", "Libra", "Scorpio", "Capricorn", "Aquarius") else "other sign (minor Bullish)"}, use="rise")
combust_rule("ta_s18_venus_rise_west", "Venus rises in West", ("TA p.71 Section 18", S(35, 16, 161, "B (silver)")),
             "Bearish; in Aries, Leo, Libra, Capricorn, Aquarius with Sun, Mars, Saturn or Rahu - sharp upturn after a small dip", ("general", "silver"), "Venus",
             lambda i: i["rise_direction"] == "West", use="rise", existing=("b015b_venus_rise_west", "cfg_silver_bearish_10_venus_rise_in_west"))
combust_rule("ta_s24_110_venus_rising_nakshatras", "Venus rising in Uttara Phalguni, Uttara Ashadha, Uttara Bhadrapada, Ardra, Bharani or Rohini",
             (s24(110, 87), "TA p.261 prophecy 2", "KD p.141"), "Bullish", ("general",), "Venus",
             lambda i: i["nakshatra_at_rise"] in ("Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Ardra", "Bharani", "Rohini", "Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada"),
             use="rise", existing=("b015c_venus_rise_star_list",),
             quals=("TA p.261 widens the list to 'any Uttara, any Purva, Aardra, Bharni & Rohini'; S24 #110 lists only the three Uttaras with Ardra, Bharani, Rohini.",))
combust_rule("ta_s24_109_jupiter_combust_west", "Jupiter getting combust in West", (s24(109, 87), "KD p.109-110 (2026: 16 Jul)"), "9 days fall than reversal (KD: first nine days weak then bullish)",
             ("general",), "Jupiter", lambda i: i["combust_direction"] == "West")
combust_rule("ta_s34b02_jupiter_rise", "Rise of Jupiter", (S(34, 2, 156, "B (gold)"),), "Gold Bearish", GOLD, "Jupiter", lambda i: True, use="rise", existing=("cfg_gold_bearish_01_jupiter_rise",))
combust_rule("kd_137_mars_combust_west_signs", "Mars combust in West in Aries, Scorpio, Capricorn or Aquarius", ("KD p.137 #10",), "High Bullish", ("general",), "Mars",
             lambda i: i["combust_direction"] == "West" and i["sign_at_combust"] in ("Aries", "Scorpio", "Capricorn", "Aquarius"))


# ---------------- Moon darshan (first sighting after Amavasya) ----------------
def darshans(ctx):
    """First New York sunset after each new moon with the Moon >= 12deg from
    the Sun (Shukla Dwitiya begun) and >= 20 h old. Our operational
    definition: neither PDF defines visibility."""
    out = []
    nms = [_parse(r["time"]["t_start_utc"]) for r in ctx.sky.class_records("lunation", family="lunation/new_moon")]
    for nm in nms:
        for ss in ctx.sunsets:
            if ss <= nm:
                continue
            s = snapshot(ss.replace(microsecond=0))
            if s.elong >= 12 and (ss - nm) >= dt.timedelta(hours=20):
                d = ss.astimezone(NYZ).date()
                if d.year == ctx.year:
                    out.append((ss, d, s))
                break
    return out


from zoneinfo import ZoneInfo as _ZI  # noqa: E402
NYZ = _ZI("America/New_York")
DARSHAN_Q = ("'Moon rise' / 'Moon darshan' read as the first evening sighting after Amavasya (Chandra Darshan). Operational criterion (not in either PDF): first New York sunset with elongation >= 12 deg and Moon age >= 20 h. Indian almanacs date the darshan for Indian sunset and can be a day earlier.",)


def darshan_rule(id, title, refs, verdict, markets, pred, quals=(), effect="", tier="major"):
    def run(ctx):
        out = []
        for ss, d, s in darshans(ctx):
            info = {"weekday": WEEKDAYS[d.weekday()], "moon_nakshatra": s["Moon"].nak, "tithi_at_sunset": tithi_label(s.tithi),
                    "elongation_deg": round(s.elong, 1)}
            r = pred(info, s)
            if r:
                if isinstance(r, dict):
                    info.update(r)
                out.append(Hit(ss, None, ("Moon", "Sun"), info, day=d))
        return out
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets, rule=title + ".",
         calc="Chandra Darshan evening (see qualification) and its weekday / the Moon's nakshatra then.", detector=run,
         quals=DARSHAN_Q + quals, effect=effect, tier=tier)


darshan_rule("ta_s15_moon_rise_after_amavasya", "Moon rise after Amavasya: weekday and tithi", ("TA p.67 [printed 37] Section 15 'Nature of Moon rise'",),
             "Pratipada: Sun/Tue/Fri/Sat - fortnight high Bullish; Mon/Wed/Thu - slight Bullish, sideways by Purnima. Dwitiya: Sun/Tue/Fri/Sat slight Bullish; Mon/Wed/Thu slight Bearish. Tritiya: Sun/Tue/Fri/Sat stable small movement; Mon/Wed/Thu one sided Bearish",
             ("general",), lambda i, s: {"result": {1: ("fortnight high Bullish", "slight Bullish, sideways by Purnima"), 2: ("slight Bullish", "slight Bearish"),
                                                   3: ("stable Market with small movement", "one sided Bearish")}.get(min(s.tithi, 3), ("", ""))[0 if i["weekday"] in ("Sunday", "Tuesday", "Friday", "Saturday") else 1]},
             quals=("TA p.67 bottom: RELIABILITY VERY LOW AS MOON ALONE DOES NOT DRIVE THE MARKETS.",))
darshan_rule("ta_s24_15_moon_darshan_fri_sat", "Moon darshan on Friday or Saturday", (s24(15, 79), S(35, 8, 158, "A (silver)"), "KD p.133 #2"), "Bullish (silver Bullish)", ("general", "silver"),
             lambda i, s: i["weekday"] in ("Friday", "Saturday"),
             quals=("CONFLICT: TA S34 B9 (gold) 'Moon darshan on Saturday is Bearish' (for gold).",))
darshan_rule("ta_s24_56_moon_darshan_tue_sat_sun", "Moon darshan on Tuesday, Saturday or Sunday", (s24(56, 83), "KD p.133 #2 (lists Thursday, Friday, Saturday, Sunday)"), "15 days Bullish", ("general",),
             lambda i, s: i["weekday"] in ("Tuesday", "Saturday", "Sunday", "Thursday", "Friday") and {"note": "KD-only weekday" if i["weekday"] in ("Thursday", "Friday") else "TA weekday"}, effect="15 days",
             quals=("CONFLICT: TA #56 lists Tuesday, Saturday, Sunday; KD p.133 lists Thursday, Friday, Saturday, Sunday. Days in only one list are marked.",))
darshan_rule("ta_s24_81_moon_darshan_wednesday", "Moon darshan on Wednesday", (s24(81, 84), "KD p.133 #2"), "Bearish", ("general",), lambda i, s: i["weekday"] == "Wednesday")
darshan_rule("ta_s34b09_moon_darshan_saturday_gold", "Moon darshan on Saturday (gold)", (S(34, 9, 156, "B (gold)"),), "Gold Bearish", GOLD, lambda i, s: i["weekday"] == "Saturday")
darshan_rule("ta_s24_21_moon_rise_ardra_pph", "Moon rise in Ardra, Purva Phalguni (or Uttara Phalguni / Chitra)", (s24(21, 80), s24(22, 80), s24(63, 83), s24(66, 83), "KD p.133 #3"),
             "Ardra / Purva Phalguni - Bullish; Chitra or Uttara Phalguni - 2.5 day Bullish", ("general",),
             lambda i, s: i["moon_nakshatra"] in ("Ardra", "Purva Phalguni", "Uttara Phalguni", "Chitra"))


def _chaitra_pratipada_wed(ctx):
    out = []
    for h in _cabinet(ctx):
        if h.facts["role"].startswith("King") and h.facts["weekday"] == "Wednesday":
            out.append(h)
    return out


rule(id="ta_s35a05_chaitra_shukla_pratipada_wednesday", title="Chaitra Shukla Pratipada on Wednesday", refs=(S(35, 5, 158, "A (silver)"),), verdict="Silver: short term Bullish",
     markets=SILV, rule="Hindu new year's day falls on a Wednesday.", calc="As the yearly cabinet's King row.", detector=_chaitra_pratipada_wed, tier="yearly")


# ---------------- Panchak (TA Section 23) ----------------
PANCHAK_START = 293 + 1 / 3      # Dhanishta pada 3 (Aquarius 0deg)
def _panchak(ctx):
    out = []
    for w in windows(lambda s: s["Moon"].lon >= PANCHAK_START, ("Moon",))(ctx):
        if w.open_start or w.open_end or w.start.year != ctx.year:
            continue
        def ghadi(t):
            sr = ctx.sunrise(t.astimezone(NYZ).date())
            if sr > t:
                sr = ctx.sunrise(t.astimezone(NYZ).date() - dt.timedelta(days=1))
            return round((t - sr).total_seconds() / 3600 * 2.5, 1)
        gs, ge = ghadi(w.start), ghadi(w.end)
        wd = vara(ctx, w.start)
        yogas = sorted({YOGA[snapshot(t).yoga - 1] for t in (w.start + dt.timedelta(hours=h) for h in range(0, int((w.end - w.start).total_seconds() // 3600) + 1, 3))} & {"Indra", "Vaidhriti", "Vyatipata"})
        res = []
        res.append(("Starts Mon/Wed/Fri - Bearish (#6)" if wd in (0, 2, 4) else "Starts Sun/Tue/Thu/Sat - Bullish (#7)"))
        if gs >= 50 and ge >= 50:
            res.append("Starts & ends >= 50 ghadi after sunrise - Bullish for one year (#3)")
        elif gs >= 45 and ge >= 45:
            res.append("Starts & ends >= 45 ghadi after sunrise - Bullish for the month (#4)")
        else:
            res.append("Starts & ends at other times - Bearish for that fortnight (#5)")
        if yogas:
            res.append(f"{'/'.join(yogas)} yoga on Panchak days - high Bullish (#8)")
        out.append(Hit(w.start, w.end, ("Moon",), {"start_weekday_NY": WEEKDAYS[wd], "start_ghadi_after_sunrise": gs, "end_ghadi_after_sunrise": ge,
                                                    "indra_vaidhriti_vyatipata_inside": yogas, "results": res}))
    return out


rule(id="ta_s23_panchak", title="Panchak (Moon in Dhanishta 3rd pada to Revati)", refs=("TA p.77 [printed 47] Section 23 'Panchak results'",),
     verdict="#6 starts Mon/Wed/Fri Bearish; #7 Sun/Tue/Thu/Sat Bullish; #3 starts & ends 50 ghadi after sunrise Bullish for one year; #4 45 ghadi Bullish for the month; #5 other times Bearish for that fortnight; #8 Indra, Vaidhrati or Vyatipat yog on Panchak days high Bullish",
     markets=("general",), rule="Moon from 0deg Aquarius (Dhanishta pada 3) to the end of Revati.",
     calc="Moon's sidereal longitude >= 293deg20'; ghadi counted from New York sunrise (1 day = 60 ghadi, 1 hour = 2.5 ghadi, TA p.77).",
     detector=_panchak, existing=("b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak",),
     quals=("TA p.77 bottom NOTE: 1, 3 & 8 ARE HIGH PROBABLE, THE REST DEPEND ON MANY OTHER FACTORS.",
            "Rules #1/#2 ('If all five Panchak Bullish/Bearish') are not computed: the book does not say what makes one Panchak day bullish."))


# ---------------- Bhadra (TA Section 28) ----------------
def _bhadra(ctx):
    out = []
    for sp in ctx.sky.karana_spans():
        if sp.value.get("karana_name") != "Vishti" or sp.open_start or sp.open_end or sp.start.year != ctx.year:
            continue
        s = snapshot(sp.start.replace(microsecond=0))
        sign = s["Moon"].sign
        loka = ("Prithvi (Earth) - negative & sentimental Bearish" if sign in ("Cancer", "Leo", "Aquarius", "Pisces") else
                "Swarga (heaven) - no effect here, beneficial" if sign in ("Aries", "Taurus", "Gemini", "Scorpio") else
                "Patal (hell) - no effect here, beneficial")
        t = s.tithi
        kind = "Day Bhadra" if t in (8, 15, 22, 29) else "Night Bhadra"
        # daytime share at New York
        day_sec, tot, x = 0, (sp.end - sp.start).total_seconds(), sp.start
        while x < sp.end:
            d = x.astimezone(NYZ).date()
            sr, ss = ctx.sunrise(d), ctx.sunset(d)
            if sr <= x < ss:
                day_sec += 600
            x += dt.timedelta(minutes=10)
        in_day = day_sec / tot >= 0.5
        eff = ("Negative" if (kind == "Day Bhadra") == in_day else "Positive")
        out.append(Hit(sp.start, sp.end, ("Moon",), {"tithi": tithi_label(t), "moon_sign_at_start": sign, "loka": loka, "type": kind,
                                                      "mostly_in_NY_daytime": in_day, "day_night_rule": f"{kind} in {'day' if in_day else 'night'} time - {eff}"}))
    return out


rule(id="ta_s28_bhadra", title="Bhadra (Vishti karana): loka and day/night effect", refs=("TA p.121-122 [printed 91-92] Section 28 'Bhadra & its effect' (Muhurta Chintamani)",),
     verdict="Earth (Cancer, Leo, Aquarius, Pisces) - negative & sentimental Bearish; heaven/hell - no effect, beneficial. Day Bhadra in day time / night Bhadra in night time - Negative; day Bhadra in night / night Bhadra in day - Positive",
     markets=("general",), rule="Each Vishti karana: Moon's sign at its start fixes the loka; Day Bhadra = Shukla 8/15, Krishna 7/14; Night Bhadra = Shukla 4/11, Krishna 3/10.",
     calc="Vishti karana spans from the astronomy layer (6deg elongation steps); Moon sign at the start; share of the window between New York sunrise and sunset (>= 50% = day time).",
     detector=_bhadra, existing=("sub_bhadra",), quals=("'Starts in' read as the Moon's sign at the Bhadra's start.", "Day/night judged at New York; Indian timing differs by ~10 h."))


# ---------------- Shar (latitude) KD p.129 ----------------
for b in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
    win(f"kd_129_shar_{b.lower()}", f"Shar (celestial latitude) of {b}", ("KD p.129 'Shar (Shadow) south of any planet - Bullish; north - Bearish'",),
        "South - Bullish; North - Bearish", ("general",), f"{b}'s ecliptic latitude south (negative) or north (positive).",
        lambda s, b=b: "South (Bullish)" if s[b].lat < 0 else "North (Bearish)", (b,), "Sign of the ecliptic latitude (Shara); windows bounded by the node crossings.",
        existing=("b118_shar_direction",), quals=("'Shar' is the Sanskrit shara (celestial latitude); the 2026 document's B118 'Shar' table is the same quantity and printed no verdict - KD supplies it.",))


def _count_sign(kind):
    BULL = ("Aries", "Taurus", "Leo", "Scorpio", "Capricorn")
    BEAR = ("Gemini", "Cancer", "Virgo", "Libra", "Sagittarius", "Aquarius", "Pisces")
    signs = BULL if kind == "bull" else BEAR
    def p(s):
        res = []
        for sg in signs:
            bs = [b for b in ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn") if s[b].sign == sg]
            if len(bs) >= 2:
                res.append(f"{sg}: {', '.join(bs)}")
        return "; ".join(res) or False
    return p


win("kd_129_two_planets_bullish_sign", "Two or more planets in a bullish sign", ("KD p.129", "KD p.82"), "Strong rally; slow-moving planets extend the rally duration", ("general",),
    "At least two of Sun..Saturn in one sign that TA S13 types Bullish.", _count_sign("bull"), (), SIGNCALC,
    quals=("Bullish/bearish sign = TA Section 13 type column (KD gives no list). Rahu/Ketu and the Moon not counted.",))
win("kd_129_two_planets_bearish_sign", "Two or more planets in a bearish sign", ("KD p.129",), "Market fall; if these planets have low speed the fall is larger", ("general",),
    "At least two of Sun..Saturn in one sign that TA S13 types Bearish.", _count_sign("bear"), (), SIGNCALC,
    quals=("Bullish/bearish sign = TA Section 13 type column. Fires most of the year by construction; listed for completeness.",))


# ---------------- Vedha (TA Section 32; S34-36; KD p.84/92-93/107/111/116/125/130) ----------------
_STATIONS: dict = {}


def _direct_stations(ctx, body):
    key = (id(ctx.grid), body)
    if key not in _STATIONS:
        from .engine import crossings
        _STATIONS[key] = [t for t, a, b in crossings(ctx.grid, lambda s: s[body].retro) if a and not b]
    return _STATIONS[key]


def vedha_of(ctx, s, body):
    """(targets dict side->nakshatra, doctrine) for body at snapshot s."""
    p = s[body]
    if body in ("Uranus", "Neptune", "Pluto"):
        cells = V.cells_2026_labels(p.nak28)
        side = V.R if p.retro else V.F
        return {side: cells[side]}, "Outer planet: Retrograde -> Right, otherwise Front (2026 B139-B141 tables)"
    lag = False
    if body in V.POST_STATION_LAG and not p.retro:
        for t in _direct_stations(ctx, body):
            if t <= s.t < t + dt.timedelta(days=V.POST_STATION_LAG[body]):
                lag = True
    return V.targets(body, p.nak28, p.retro, V.vedha_fast(body, p.speed, p.retro), lag)


def occupies(s, body, nak):
    return s[body].nak28 == nak or (nak == "Uttara Ashadha" and s[body].nak == nak)


def vedha_pair(by, to):
    def make(ctx):
        def p(s):
            tg, why = vedha_of(ctx, s, by)
            hit = [side for side, nk in tg.items() if s[to].nak28 == nk]
            return hit and f"{name(by)} in {s[by].nak28} vedhas {s[to].nak28} ({'/'.join(hit)} side) where {name(to)} is"
        return p
    return make


def vedha_rule(id, title, refs, verdict, markets, by, to, mutual=False, effect="", quals=(), tier="major"):
    def run(ctx):
        f1 = vedha_pair(by, to)(ctx)
        f2 = vedha_pair(to, by)(ctx)
        pred = (lambda s: (f1(s) and f2(s)) and f"{f1(s)}; {f2(s)}") if mutual else f1
        return windows(pred, (by, to), placed_facts(by, to))(ctx)
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets,
         rule=(f"{name(by)} and {name(to)} vedha each other (mutual)" if mutual else f"{name(by)} does Vedha to the nakshatra {name(to)} occupies") + " on the Sarvatobhadra wheel (TA pp.131-133).",
         calc="Each body's nakshatra (28-name scheme with Abhijit); vedha side per finastro/pdfref/vedha.py (TA p.134 rules + 2026 class doctrine, TA p.144 normal speeds); window while the target nakshatra is occupied.",
         detector=run, effect=effect, tier=tier,
         quals=("TA p.136: when 2 planets do Vedha of each other it is strong Vedha (impact high); Vedha by the Sun on Moon, Mars, Mercury, Jupiter, Venus or Saturn is weak; Moon below 8 deg or above 22 deg is weak.",
                "TA p.137 #5: when Vedha ends with Bearish implications it reverses the trend.",
                "Direction doctrine conflict between TA p.134 and the 2026 tables: see vedha.py and REFERENCE_PDF_RULES.md.") + tuple(quals))


VE = "TA p.140-141 [printed 110-111] Section 32 E 'Specific Vedha & their results'"
for by, to, verdict, mutual, eff in (("Sun", "Ketu", "Bearish", False, ""), ("Mars", "Rahu", "Bearish", False, ""), ("Venus", "Ketu", "Bearish", False, ""),
                                      ("Venus", "Rahu", "Bearish", False, ""), ("Venus", "Mercury", "Bearish", False, ""), ("Venus", "Uranus", "Bearish (mutual)", True, ""),
                                      ("Mercury", "Moon", "Bearish", False, ""), ("Jupiter", "Moon", "Bearish", False, ""), ("Venus", "Moon", "Bearish", False, ""),
                                      ("Mars", "Mercury", "Bullish", False, ""), ("Saturn", "Moon", "Bullish", False, ""), ("Jupiter", "Mars", "Bullish 13 days (mutual)", True, "13 days"),
                                      ("Saturn", "Mars", "Bullish 20 days (mutual)", True, "20 days"), ("Saturn", "Mars", "Bullish 10 days", False, "10 days"), ("Venus", "Jupiter", "Bullish", False, "")):
    vedha_rule(f"ta_s32e_{by.lower()}_{name(to).lower()}{'_mutual' if mutual else ''}", f"{name(by)}-{name(to)} {'mutual ' if mutual else ''}Vedha", (VE,), verdict,
               ("general",), by, to, mutual, eff, tier="moon" if "Moon" in (by, to) else "major")
vedha_rule("ta_s35a11_mercury_vedha_venus", "Mercury does Vedha of Venus", (S(35, 11, 158, "A (silver)"),), "Silver Bullish", SILV, "Mercury", "Venus")
vedha_rule("ta_s35a11_jupiter_vedha_venus", "Jupiter does Vedha of Venus", (S(35, 11, 158, "A (silver)"),), "Silver Bullish", SILV, "Jupiter", "Venus")
vedha_rule("ta_s35b07_mercury_venus_mutual_vedha", "Mercury-Venus mutual Vedha", (S(35, 7, 160, "B (silver)"),), "Silver Bearish", SILV, "Mercury", "Venus", mutual=True)
vedha_rule("ta_s35b07_moon_venus_mutual_vedha", "Moon-Venus mutual Vedha", (S(35, 7, 160, "B (silver)"),), "Silver Bearish", SILV, "Moon", "Venus", mutual=True, tier="moon")
vedha_rule("ta_s35a13_mercury_moon_mutual_vedha", "Mercury (combust & retrograde) mutual Vedha with Moon", (S(35, 13, 158, "A (silver)"),), "Silver: Bullish day", SILV, "Mercury", "Moon", mutual=True, tier="moon",
           quals=("The combust & retrograde condition on Mercury is reported in the facts, not filtered.",))


def nak_vedha_rule(id, title, refs, verdict_mal, verdict_ben, markets, naks):
    def run(ctx):
        def p(s):
            mal, ben = [], []
            for b in ("Sun", "Mars", "Saturn", "Rahu", "Ketu", "Mercury", "Jupiter", "Venus"):
                tg, _ = vedha_of(ctx, s, b)
                for side, nk in tg.items():
                    if nk in naks:
                        (mal if b in MAL else ben).append(f"{b}->{nk}")
            if not mal and not ben:
                return False
            tone = []
            if mal:
                tone.append(("MALEFIC vedha (" + ", ".join(mal) + ") - " + verdict_mal + (" - more than one malefic: stronger" if len(mal) > 1 else "")))
            if ben:
                tone.append(("BENEFIC vedha (" + ", ".join(ben) + ") - " + verdict_ben + (" - more than one benefic: stronger" if len(ben) > 1 else "")))
            return " | ".join(tone)
        return windows(p, (), None)(ctx)
    rule(id=id, title=title, refs=refs, verdict=f"Malefic Vedha: {verdict_mal}; Benefic Vedha: {verdict_ben}", markets=markets,
         rule=f"A malefic or benefic planet's Vedha falls on {', '.join(naks)}.",
         calc="Every graha's vedha targets (Moon excluded: it vedhas every target in turn within ~27 days) checked against the listed nakshatras; window while the set of vedhas is unchanged.",
         detector=run, quals=("TA p.137: Moon, Mercury, Jupiter & Venus benefic (their Vedha Bearish); Sun, Mars, Saturn, Rahu & Ketu malefic (their Vedha Bullish & reverses the trend).",))


nak_vedha_rule("ta_s34_gold_vedha_punarvasu_pushya_chitra_dhanishta", "Vedha of Punarvasu, Pushya, Chitra or Dhanishta (gold)",
               (S(34, 8, 154, "A (gold)"), S(34, 4, 156, "B (gold)"), "KD p.92 (2026: Rahu Vedh of Pushya - high bullish for gold & silver)"),
               "Gold Bullish (extreme if more than 1 malefic)", "Gold Bearish (high if more than 1 benefic)", GOLD, ("Punarvasu", "Pushya", "Chitra", "Dhanishta"))
nak_vedha_rule("ta_s36_sugar_vedha_ashlesha_magha_jyeshtha_ubh", "Vedha of Ashlesha, Magha, Jyeshtha or Uttara Bhadrapada (sugar)",
               (S(36, 9, 163, "A (sugar)"), S(36, 11, 166, "B (sugar)")), "Sugar Bullish (high if more than one)", "Sugar Bearish (high if more than one)", SUG,
               ("Ashlesha", "Magha", "Jyeshtha", "Uttara Bhadrapada"))


def _graha_vedha_table(body):
    def run(ctx):
        def p(s):
            tg, why = vedha_of(ctx, s, body)
            return f"{name(body)} in {s[body].nak28}: " + ", ".join(f"{side} {nk} (lord {NAK_LORD[NAKS.index(nk)] if nk in NAKS else 'Sun (Abhijit)'})" for side, nk in tg.items())
        return windows(p, (body,), None)(ctx)
    return run


for b, sec in (("Sun", 131), ("Rahu", 137), ("Ketu", 138)):
    rule(id=f"ta_s32_{b.lower()}_nakshatra_vedha", title=f"{b} Nakshatra Vedha (all three sides)", refs=("TA p.134 [printed 104] Section 32 A rule 1 'Sun, Moon, Rahu & Ketu do Vedha all 3 sides'", "TA pp.131-133 wheel", f"2026 document B{sec} (same table, 2026)", "KD p.84 / p.130 #1-#2 (sector rule)"),
         verdict="Malefic Vedha: good rally may appear in sectors ruled by the Nakshatra lord (KD p.130 #1); Vedha by malefic is Bullish and reverses the trend (TA p.137 #4)",
         markets=("general", "sector:nakshatra lord"), rule=f"{b}'s residency and the three nakshatras it vedhas.",
         calc=f"{b}'s nakshatra (28-name, Abhijit) -> TA wheel Front/Left/Right (2026 labels).", detector=_graha_vedha_table(b),
         existing=(), quals=(f"Unblocks the 2026 document's B{sec} for 2027: 217/227 of the 2026 printed cells equal the TA wheel; see vedha.py.",
                             "KD p.93 (2026): 'Rahu doing Vedh of Pushya, Swati and Abhijeet ... Abhijeet lord Sun: sectors ruled by Sun (NIFTY, Power) to outperform; Swati ruled by Rahu' ." if b == "Rahu" else ""))


# ---------------- remaining computable items ----------------
win("kd_134_mars_or_rahu_in_virgo", "Mars or Rahu in Virgo", ("KD p.134 #6",), "Bullish ('Placement in Virgo favors upward bias')", ("general",),
    "Mars or Rahu in Virgo.", lambda s: tuple(b for b in ("Mars", "Rahu") if s[b].sign == "Virgo") or False, (), SIGNCALC)


def station_rule(id, title, refs, verdict, markets, body, to, existing=(), days=None):
    def run(ctx):
        from .engine import crossings
        out = []
        for t, a, b in crossings(ctx.grid, lambda s: s[body].retro):
            if t.year != ctx.year:
                continue
            if (to == "D" and a and not b) or (to == "R" and b and not a):
                s = snapshot(t)
                out.append(Hit(t, t + dt.timedelta(days=days) if days else None, (body,), placed_facts(body)(s, None)))
        return out
    rule(id=id, title=title, refs=refs, verdict=verdict, markets=markets, rule=title + ".",
         calc="Station = zero of the of-date longitudinal speed (bisected to 30 s), as almanacs define it.", detector=run, existing=existing,
         effect=f"{days} days" if days else "")


for b in ("Jupiter", "Mercury"):
    station_rule(f"ta_s35a16_{b.lower()}_turns_direct", f"{b} turns direct from retrograde", (S(35, 16, 159, "A (silver)"),), "Silver: short term bounce", SILV, b, "D",
                 existing=("cfg_silver_bullish_13_jupiter_or_mercury_turns_direct",))
station_rule("ta_s35b10_saturn_direct", "Saturn direct from retrograde", (S(35, 10, 160, "B (silver)"),), "Silver Bearish (September 2019)", SILV, "Saturn", "D",
             existing=("cfg_silver_bearish_08_saturn_direct_from_retrograde",))
station_rule("kd_032_mercury_retrograde_station", "Mercury retrograde station (high-probable turning event)", ("KD p.32", "TA p.60 S14: 'Retrograde - mostly Bullish'"),
             "High-probable turning event (usually three times a year)", ("general",), "Mercury", "R")
station_rule("ta_s14_pluto_station", "Pluto changes direction", ("TA p.66 [printed 36] S14 Pluto: 'Very volatile @ time of changing direction'",), "Very volatile", ("general",), "Pluto", "R")
station_rule("ta_s14_pluto_station_d", "Pluto changes direction (direct)", ("TA p.66 S14 Pluto",), "Very volatile", ("general",), "Pluto", "D")


def _stambhi_mars(ctx):
    out = []
    for w in windows(lambda s: s["Mars"].sign, ("Mars",))(ctx):
        if w.end - w.start >= dt.timedelta(days=180) and (w.start.year == ctx.year or w.end.year == ctx.year):
            s = snapshot((w.start + (w.end - w.start) / 2).replace(microsecond=0))
            rahu_with = s["Rahu"].sign == w.facts.get("value", s["Mars"].sign)
            out.append(Hit(w.start, w.end, ("Mars",), {"sign": w.facts.get("value"), "days_in_sign": round((w.end - w.start).days), "rahu_in_same_sign": rahu_with,
                                                        "result": "with Rahu: S36 A12 very high Bullish (direct) / S36 B5 Bearish when it goes retrograde" if rahu_with else "no Rahu: S36 A12/B5 condition not met"}, open_start=w.open_start, open_end=w.open_end))
    return out


rule(id="ta_s36_stambhi_mars", title="Stationary (Stambhi) Mars: 6-7 months in one sign", refs=(S(36, 12, 163, "A (sugar)"), S(36, 5, 165, "B (sugar)")),
     verdict="Direct & Stambhi Mars with Rahu - very high Bullish; Stationery Mars with Rahu going retrograde - Bearish", markets=SUG,
     rule="Mars spends 6-7 months in one sign (TA: 'Mars when 6/7 months in the same Sign is called Stationery').",
     calc="Mars sign residencies of at least 180 days; Rahu in the same sign reported.", detector=_stambhi_mars)


def _paush_wednesdays(ctx):
    out = []
    for a, b, nm in ctx.sky.lunar_months():
        pass
    # Purnimanta Paush: from the full moon before amanta Paush's new moon... use day scan
    days = {}
    for d in ctx.ny_days():
        m = ctx.sky.purnimanta_month(ctx.sunrise(d))
        days.setdefault(m, []).append(d)
    for m, ds in days.items():
        if m and m.endswith("Paush"):
            weds = [d for d in ds if d.weekday() == 2]
            if len(weds) >= 5:
                out.append(Hit(ctx.sunrise(ds[0]), ctx.sunrise(ds[-1]), (), {"month": m, "wednesdays": [d.isoformat() for d in weds]}))
    return out


rule(id="ta_s36b06_five_wednesdays_paush", title="5 Wednesdays in the month of Paush", refs=(S(36, 6, 165, "B (sugar)"),), verdict="Sugar Bearish", markets=SUG,
     rule="The Purnimanta month Paush contains five Wednesdays.", calc="Count of Wednesdays among the civil days (New York sunrise) inside the month. " + MONTHQ,
     detector=_paush_wednesdays, tier="yearly")


def _vaisakh_adhik(ctx):
    return [Hit(a, b, (), {"month": nm}) for a, b, nm in ctx.sky.lunar_months() if nm == "Adhik Vaishakh" and (a.year == ctx.year or b.year == ctx.year)]


rule(id="ta_s36a08_vaisakh_adhik", title="Vaisakh is Adhik Mas", refs=(S(36, 8, 163, "A (sugar)"),), verdict="Sugar: buy before the crop starts", markets=SUG,
     rule="An intercalary (Adhik) Vaishakh month.", calc="Amanta months off the new moons; Adhik when the Sun does not change sign during the month.", detector=_vaisakh_adhik, tier="yearly")


def _sank_seq(ctx):
    out = []
    ss = sankrantis(ctx)
    for (t0, s0, _, m0), (t1, s1, _, m1) in zip(ss, ss[1:]):
        if m0 == 15 and m1 == 45 and vara(ctx, t1, "mumbai") == 5:
            out.append(Hit(t1, None, ("Sun",), {"previous": f"{s0} 15 Muhurta", "this": f"{s1} 45 Muhurta on Saturday (IST)"}))
    counts = {15: 0, 30: 0, 45: 0}
    for t, sg, s, m in ss:
        counts[m] += 1
    return out


rule(id="ta_s36a21_15_then_45_muhurta_saturday", title="15 Muhurta Sankranti followed by a 45 Muhurta Sankranti on Saturday", refs=(S(36, 21, 164, "A (sugar)"),),
     verdict="Sugar: high Bullish in 45 Mahurta Sankranti", markets=SUG, rule="Consecutive Sankrantis: 15 Muhurta, then 45 Muhurta falling on Saturday.",
     calc="Sankranti muhurta classes (TA S27) in sequence; weekday at Mumbai sunrise (the almanac convention) and New York.", detector=_sank_seq)


def _yearly_majority(ctx):
    ss = sankrantis(ctx)
    c = {15: 0, 30: 0, 45: 0}
    wd_hi = 0
    for t, sg, s, m in ss:
        c[m] += 1
        if vara(ctx, t, "mumbai") in (1, 5, 6):
            wd_hi += 1
    res = []
    if c[45] > len(ss) / 2:
        res.append("majority 45 Muhurta: excess of everything, people happy, Markets negative")
    if c[15] > len(ss) / 2:
        res.append("majority 15 Muhurta: deficiency, people not happy, Markets positive")
    res.append(("majority on Tue/Sat/Sun: inflation high, Markets positive" if wd_hi > len(ss) / 2 else
                "majority on Mon/Wed/Thu/Fri: inflation low, Markets negative" if wd_hi < len(ss) / 2 else "weekday split 6/6: no majority"))
    return [Hit(ss[0][0], ss[-1][0], ("Sun",), {"muhurta_counts": c, "sankrantis_on_tue_sat_sun_IST": wd_hi, "of": len(ss), "results": res})]


rule(id="ta_s27_yearly_majority", title="Year's Sankranti majority (muhurta and weekday)", refs=("TA p.120 [printed 90] Section 27",),
     verdict="Majority 45 Muhurta: markets negative; majority 15 Muhurta: markets positive; majority on Mon/Wed/Thu/Fri: inflation low, markets negative; on Tue/Sat/Sun: inflation high, markets positive",
     markets=("general",), rule="Tally of the year's twelve Sankrantis.", calc="Muhurta class per S27; weekday at Mumbai sunrise.", detector=_yearly_majority, tier="yearly")


def _moon_joins_combust_mercury(ctx):
    out = []
    for sp in ctx.sky.combust_spans("Mercury"):
        if sp.value != "West" or sp.open_start or sp.open_end:
            continue
        lo, hi = sp.start, sp.end
        for w in windows(lambda s: s["Moon"].sign_i == s["Mercury"].sign_i, ("Moon", "Mercury"))(ctx):
            if w.start < hi and lo < w.end and (w.start.year == ctx.year):
                out.append(Hit(max(w.start, lo), min(w.end, hi), ("Moon", "Mercury"), {"mercury_combust": "West"}))
    return out


rule(id="ta_s36a22_moon_joins_combust_mercury_west", title="Moon joins the combust Mercury in West", refs=(S(36, 22, 164, "A (sugar)"),), verdict="Sugar Bullish", markets=SUG,
     rule="Moon in Mercury's sign while Mercury is combust in the West.", calc="Combust window (Mumbai kalamsha, West) intersected with Moon-Mercury same-sign windows.",
     detector=_moon_joins_combust_mercury, tier="moon")


def _rahu_kaal_thursday(ctx):
    out = []
    for d in ctx.ny_days():
        if d.weekday() != 3:
            continue
        sr, ss = ctx.sunrise(d), ctx.sunset(d)
        part = (ss - sr) / 8
        a, b = sr + part * 5, sr + part * 6     # Thursday: 6th eighth of daylight
        lords = {NAK_LORD[snapshot(t.replace(microsecond=0)).__getitem__("Moon").nak_i] for t in (a, a + (b - a) / 2, b)}
        if lords & {"Rahu", "Ketu"}:
            s = snapshot(a.replace(microsecond=0))
            out.append(Hit(a, b, ("Moon",), {"rahu_kaal_NY": f"{a.astimezone(NYZ):%H:%M}-{b.astimezone(NYZ):%H:%M}", "moon_nakshatra": s["Moon"].nak}, day=d))
    return out


rule(id="kd_091_rahu_kaal_thursday_rahu_ketu_nakshatra", title="Thursday Rahu Kaal with a Rahu/Ketu nakshatra", refs=("KD p.91", "KD p.143 #1"),
     verdict="Bullish bias in that window ('use with technical and risk management, not sole decision factor')", markets=("general",),
     rule="On a Thursday, the Moon's nakshatra during Rahu Kaal is ruled by Rahu (Ardra, Swati, Shatabhisha) or Ketu (Ashwini, Magha, Mula).",
     calc="Rahu Kaal = 6th eighth of New York daylight on Thursday (sunrise-sunset from the astronomy layer); Moon's nakshatra sampled across the window.",
     detector=_rahu_kaal_thursday, existing=("sub_rahu_or_ketu_nakshatra_on_a_thursday",))

def _hemisphere(ctx):
    from .. import ephem as E
    from .engine import crossings
    out = []
    for t, a, b in crossings(ctx.grid, lambda s: int(E.position(s.t, "Sun", sidereal=False).lon // 180)):
        if t.year == ctx.year:
            out.append(Hit(t, None, ("Sun",), {"hemisphere": "North (March equinox, tropical Sun 0 deg)" if b == 0 else "South (September equinox, tropical Sun 180 deg)"}))
    return out


rule(id="kd_032_hemisphere_dates", title="Hemisphere date (equinox) - high-probable turning event", refs=("KD p.32", "KD pp.37-70 charts ('North Hemisphere' ~20-21 Mar, 'South Hemisphere' ~22-23 Sep)"),
     verdict="High-probable turning event (twice a year)", markets=("general",),
     rule="The Sun crosses the celestial equator (tropical 0 deg / 180 deg).",
     calc="Tropical (not sidereal) solar longitude crossing 0 or 180 deg; the KD charts date the North/South hemisphere events at the equinoxes.",
     detector=_hemisphere, quals=("KD p.31: identify the high or low price on the turning date and use it as the reference level; treat turning dates as signals within a broader strategy, not standalone predictors.",))


# ---------------- added after the silver coverage audit ----------------
win("ta_261_venus_retro_in_taurus", "Venus retrograde in Taurus", ("TA p.261 [printed 231] 2020 story #8 'PROPHECY - Venus getting Retrograde in the Sign of Taurus is high Bullish on Cotton, Silver & Sugar industries'",),
    "High Bullish on Cotton, Silver & Sugar industries", ("silver", "sugar", "sector:Cotton"), "Venus retrograde while in Taurus.",
    lambda s: s["Venus"].retro and s["Venus"].sign == "Taurus", ("Venus",), SIGNCALC + " " + RETCALC,
    quals=("TA p.260 (same page group): 'Retrograde Venus Bearish for five months thereafter Bullish' for the general market.",))
win("kd_111_rahu_in_dhanishta", "Rahu in Dhanishta (market and bullion risk)", ("KD p.111 'Rahu in Dhanistha: Market and Bullion Risk'", "KD p.113 'Rahu in Dhanistha: Negative for Markets and Bullion'"),
    "Market and bullion: negative outlook ('Rahu in Dhanistha, ruled by Mars (enemy), is bearish'; 'High probability of adverse moves')", ("gold", "silver", "general"),
    "Rahu in Dhanishta nakshatra.", nak_is("Rahu", "Dhanishta"), ("Rahu",), NAKCALC,
    quals=("KD prints the window as '2 August to year end' (2026); the configuration itself lasts until Rahu leaves Dhanishta, which is the window computed here.",
           "KD p.111: 'Rahu's vedh of Vishaka supports stability' for banking and finance; KD p.113: 'Jupiter trine may prevent' a general fall.",
           "KD p.111 bottom: 'Trading guidance: exercise extreme caution'."))
nc("TA pp.31-39 [printed 1-9] Sections 1-2", "Sectors ruled by each planet (silver: Moon, Jupiter; gold: Sun (western), Mars) and sectors represented by each sign (silver: Cancer; gold: Aries, Leo, Capricorn)",
   "Rulership tables, not dated rules. Recorded so the sector rule of KD p.84/p.130 (malefic Vedha of a nakshatra -> rally in its lord's sectors; benefic Vedha -> fall) could be applied to silver via the Moon and Jupiter nakshatras; not applied, at the user's direction, until confirmed.")


# ======================================================================
# Annotation-only entries: the condition is already a calendar rule and the
# PDF adds source text, not a new date.
# ======================================================================
for id_, title, refs, verdict, ex in (
    ("ta_s24_02_tithi_vruddhi_kshay_shukla", "Tithi Vruddhi / Kshay in Shukla Paksha", (s24(2, 78), "KD p.147"), "Vruddhi Bullish; Kshay Bearish", ("b068_vriddhi_tithi_shukla_paksha", "b066_kshay_tithi_shukla_paksha")),
    ("ta_s24_03_tithi_vruddhi_kshay_krishna", "Tithi Kshay / Vruddhi in Krishna Paksha", (s24(3, 78), "KD p.147"), "Kshay Bullish; Vruddhi Bearish", ("b067_kshay_tithi_krishna_paksha", "b069_vriddhi_tithi_krishna_paksha")),
    ("ta_s24_83_three_saturdays_shukla", "Three Saturdays in Shukla Paksha", (s24(83, 85), "KD p.148"), "Bearish", ("b101_three_saturdays_in_shukla_paksha",)),
    ("ta_s24_92_krishna_chaturdashi_longer", "Krishna paksha (Chaturdashi) 14 ghadi more than Amavasya", (s24(92, 85), "KD p.145"), "Bearish", ("b106_amavasya_ghadi_lesser_than_chaturdashi",)),
    ("ta_s24_08_panchak_yogas", "Indra, Vaidhriti or Vyatipata yoga on Panchak days", ("TA p.77 Section 23 #8",), "high Bullish", ("b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak",)),
    ("ta_s35_silver_prophecy_shukla_shashti", "Silver prophecy: range of Shukla Shashti", ("TA p.157 [printed 127] Section 35",), "Whatever side the range breaks next day, it moves that way till Full Moon (worked 9 of 12 months)", ("cfg_silver_bullish_01_shukla_shashti_turning_dates",)),
    ("ta_s35a21_paksha_16_14", "Shukla Paksha of 16 days or Krishna Paksha of 14 days", (S(35, 21, 159, "A (silver)"),), "Silver Bullish", ("cfg_silver_bullish_14_paksha_of_16_or_14_days",)),
    ("ta_s17_mercury_manifestation", "Mercury speed crosses Venus speed", ("TA p.70 Section 17 'Bullishness returns after speed of Mercury cross speed of Venus'", "KD p.99/112/127"), "Bullishness returns; major turning date", ("b010_mercury_manifestation",)),
    ("ta_s24_115_sun_venus_shatabhisha", "Sun or Venus in Shatabhisha", ("KD p.131 #1",), "Bullish", ("b115_sun_or_venus_in_shatabhisha",)),
    ("kd_057_apogee", "Apogee / perigee", ("(no PDF rule; 2026 document only)",), "-", ()),
):
    if not ex:
        continue
    rule(id=id_, title=title, refs=refs, verdict=verdict, markets=("general",), rule=title + ".",
         calc="Not recomputed here: the existing calendar rule computes this exact condition.", detector=None, existing=ex)

# ======================================================================
# Not computable / not a dated rule -- with reasons.
# ======================================================================
for ref, text, why in (
    ("TA pp.18-29", "Historical narratives 1992-2019 (Herschel-Neptune 1992, Jupiter-Saturn 2000, Rahu-Saturn 2002-03, 2008 crash factors, etc.)", "Worked examples, not rules for 2027; each named configuration that is a rule elsewhere in the book is implemented there. Used as validation where a date is given (Mercury-in-middle 2014/2017/2018/2020; Paap Kartari 2011)."),
    ("TA p.30 #1-#2", "'Tithi & Vaar play far vital role & can overtake any Planet'; 'No planet can play a solo game for very long'", "Weighting principles with no date; carried as a qualification in the report."),
    ("TA p.30 #3, #6; pp.247-251", "RSI and price rules (higher high/lower low, 3-year RSI extremes, 30-minute opening range, breakout purity 0.146%/0.236%, squares & cubes, rule of averages 0.0786)", "Need market price data; outside an astronomical calendar."),
    ("TA p.30 #4, #5, #7", "Behavioural trading maxims", "No astronomical condition."),
    ("TA pp.46-48, 52-53, 142-143, 145", "Reference tables (sign lords, nakshatra lords, exaltation/debilitation/moolatrikona and degrees, sign-nakshatra-pada map, tithi names)", "Definitions; used inside other rules (verified identical to the project's tables)."),
    ("TA p.77 [printed 47] S23 #1/#2", "If all five Panchak Bullish/Bearish -> entire month", "The book never says what makes one Panchak day Bullish or Bearish."),
    ("TA p.85 S24 #93", "Krishna Shashti smaller than Nakshatra duration - Bearish", "Ambiguous: which nakshatra's duration (the one current at sunrise, at the tithi's start, or the day's) is not stated; not guessed."),
    ("TA p.87 S24 #111-#113", "Tithi over-rules all planets; Neptune highest impact on speculation; Mercury lord of sentiment", "Principles; carried as qualifications."),
    ("TA p.70 S17", "Combustion result reversed by malefic/benefic aspect", "Carried as a qualification on every Mercury combustion event (the aspecting planets are named in the event facts)."),
    ("TA pp.138-139 S32 D", "Effect of Vedha on signs (sectors ruled by each sign costlier/cheaper)", "Only partly legible in the scan; the legible lines restate 'Bearish if Vedha by Benefic Planets' per sign with no sector names readable; vargottama-intensity line is carried as a qualification."),
    ("TA pp.123-124 S29", "Sectors and their rulers", "Mapping table; used to name sectors in the market-significance field."),
    ("TA pp.254-265", "Story of 2020 (dated 2020 events)", "2020-specific; used to validate the computations (Mercury middle 2020, Venus-Herschel, Saturn-Mars) and as source text for the rules they illustrate."),
    ("TA p.252-253", "Concept of Total Day; rainfall by Samvat year", "Already in the calendar (2026 document's Total Days and Rainfall tables)."),
    ("KD pp.23-34", "Methodology: how to track events, turning-date usage, risk controls, position sizing", "Guidance, no astronomical condition; quoted in the report's caution notes."),
    ("KD pp.5-22", "2016-2032 transit review: Herschel in Aries 2016, Saturn-Neptune conjunction as a decade-defining reset (effects 2-3 years before, peak at exact conjunction, smaller planets crossing Neptune over 30-45 days), 2026-27 shock events, 2030 new order", "Mundane narrative, not a dated market rule; the Saturn-Neptune relationship itself is computed under TA Section 25."),
    ("KD pp.36-81", "Charts of past turning dates (Mercury retrograde, hemisphere dates, Mercury manifestation) with index ranges 2020-2025", "Historical examples; they define 'hemisphere dates' as the equinoxes (North ~20-21 Mar, South ~22-23 Sep), which is implemented."),
    ("KD pp.149-163, 167-223", "Sector relative-strength cycles, technical learning (opening range, breakout purity, squares & cubes, total day, rule of averages, two-candle SMA, divergence), gold/macro essays", "Price and macro material, no astronomical condition (total day already in the calendar)."),
    ("KD p.164", "Conflict checklist: list positive and negative prophecies, check for contra prophecies, stay cautious while both are active", "Method; reflected in the 'Conditions & qualifications' field."),
    ("KD p.166", "Month bias (Jan/Feb/Oct highest volatility; Mar/Aug/Sep negative; Apr/May/Nov/Dec positive; Jun/Jul avoid fresh investment)", "Conclusion of the 2026 deck for 2026, not a rule that carries to 2027."),
    ("KD p.84 / p.130 #1-#2", "Malefic/benefic Vedh of any nakshatra -> rally/fall in sectors of the nakshatra lord", "Applies to every vedha of every planet at all times (always some nakshatra is vedha'd), so it is not a dated event; applied through the Sun/Rahu/Ketu nakshatra-vedha windows and the named gold/sugar nakshatras."),
    ("KD pp.95-128", "2026-dated prophecies", "2026 events; used to validate this engine's calculations (see the validation table); the underlying rules are implemented for 2027."),
    ("KD p.129", "Slow planets extend a rally / larger fall", "Carried as a qualification on the two-planets-in-a-sign windows (speeds in facts)."),
    ("KD p.143 #3", "Neptune: largest influence on speculation", "Principle."),
    ("KD p.115", "Mars in Ardra (ruled by Rahu) with Rahu in Dhanishta (ruled by Mars) - mutual rulership, ultra-volatile", "2026-specific nakshatra-lord exchange; the general rule (nakshatra parivartana) is not stated, so only the 2026 instance is recorded."),
):
    nc(ref, text, why)


# User-supplied gold rules (Reference_materials/user_notes_gold.md).
from . import user_rules  # noqa: E402,F401

# Brihat Samhita gold / silver price rules (Reference_materials/extracted/OTHERS_FINANCIAL_REVIEW.md).
from . import bs_rules  # noqa: E402,F401
