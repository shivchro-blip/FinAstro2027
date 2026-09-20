"""Panchang elements and weekday-rule evaluation.

The weekday convention here is not a guess. It was chosen by reproducing 13
weekday-rule tables from the 2026 source (75 dated rows) under four competing
conventions:

    tithi/nakshatra at sunrise   51/75
    civil-day overlap            74/75   <- selected
    sunrise-to-sunrise day       73/75
    market-session overlap       64/75

and confirmed by the source's own From/Till annotations, which coincide with
civil-day span boundaries to the minute.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import swisseph as swe

from . import ephem
from .config import CONF
from .timezones import UTC, civil_day_bounds

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima/Amavasya",
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

#: The seven MOVABLE karanas, in order. They repeat eight times over karana
#: numbers 2..57 -- 56 of the lunation's 60.
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
]

#: The four FIXED karanas, keyed by KARANA NUMBER 1..60 and not by index.
#: Kimstughna opens the lunation; Shakuni, Chatushpada and Naga close it.
#:
#: THE KEYS WERE 0-BASED AND THE LOOKUP TRIED BOTH CONVENTIONS, which named
#: karana 57 wrongly -- see `karana_name`.
FIXED_KARANA = {1: "Kimstughna", 58: "Shakuni", 59: "Chatushpada",
                60: "Naga"}


@dataclass(frozen=True)
class Panchang:
    tithi_num: int        # 1..30
    tithi_name: str
    paksha: str           # Shukla | Krishna
    nakshatra_num: int    # 1..27
    nakshatra: str
    yoga_num: int         # 1..27
    yoga: str
    karana_num: int       # 1..60
    karana: str
    moon_lon: float
    sun_lon: float


def tithi_name(num: int) -> str:
    """Name of tithi `num`, 1..30.

    The fifteen names repeat in each fortnight, and the fifteenth takes the
    name of the fortnight's own end: Purnima closing the bright half, Amavasya
    closing the dark one. One function, so a boundary record and a sampled
    panchang block cannot name the same tithi differently.
    """
    if num == 15:
        return "Purnima"
    if num == 30:
        return "Amavasya"
    return TITHI_NAMES[(num - 1) % 15]


def paksha_of(num: int) -> str:
    """Fortnight of tithi `num`. Tithis 1-15 are the bright half."""
    return "Shukla" if num <= 15 else "Krishna"


def karana_name(num: int) -> str:
    """Name of karana `num`, 1..60. One function, so a boundary record and a
    sampled panchang block cannot name the same karana differently.

    A CORRECTION, and it is the one that matters to Bhadra. This read:

        FIXED_KARANA.get(knum - 1) or FIXED_KARANA.get(knum) or <movable>

    against keys that were 0-based. The first lookup is the correct one and
    the second was a fallback in the other convention, so for `num = 57` --
    where the 0-based lookup correctly misses, because 57 is movable -- the
    fallback hit the 0-based key 57 and returned **Shakuni**. Karana 57 is the
    EIGHTH VISHTI of the lunation. The layer therefore named seven Vishtis per
    lunation instead of eight, and printed Shakuni twice.

    It reached the artifact: `karana` is on every panchang block. No check
    could see it -- `test_bhadra_two_printings` carries its own local
    numbering and never calls this, which is why a defect in the shared
    function survived a suite that verifies Bhadra to 25 seconds.

    The document states the eight explicitly ("the eight windows of each lunar
    month fall on karana numbers 8, 15, 22, 29, 36, 43, 50, 57"), so the
    source's own sentence contradicted the layer on the last of them.
    """
    if not 1 <= num <= 60:
        raise ValueError(f"karana number {num} is outside 1..60")
    return FIXED_KARANA.get(num) or KARANA_NAMES[(num - 2) % 7]


#: The karana numbers that are Vishti, DERIVED from the seven movable names
#: rather than typed. The source prints the same eight in its own prose -- "the
#: eight windows of each lunar month fall on karana numbers 8, 15, 22, 29, 36,
#: 43, 50, 57" -- so the derivation has an independent printed answer to agree
#: with, which a typed tuple copied off that sentence would not.
#: A Bhadra IS a Vishti karana; the two words name one thing.
VISHTI_KARANAS = tuple(n for n in range(1, 61) if karana_name(n) == "Vishti")


def at(when: dt.datetime) -> Panchang:
    moon = ephem.longitude(when, "Moon")
    sun = ephem.longitude(when, "Sun")
    elong = (moon - sun) % 360

    tnum = int(elong // 12) + 1
    paksha = paksha_of(tnum)
    tname = tithi_name(tnum)

    nnum = int(moon // (360 / 27)) + 1
    ynum = int(((moon + sun) % 360) // (360 / 27)) + 1
    knum = int(elong // 6) + 1

    return Panchang(tnum, tname, paksha, nnum, ephem.NAKSHATRAS[nnum - 1],
                    ynum, YOGA_NAMES[ynum - 1], knum, karana_name(knum),
                    moon, sun)


# ------------------------------------------------------- sunrise and sunset
# A rise or a set is a LOCATION PROPERTY. Unlike a tithi or a yoga boundary --
# an instant in the sky, the same everywhere -- the Sun crosses one horizon at
# one place, and there is no such thing as "the sunrise" without a place to
# take it from. Both functions therefore require `loc` and neither has a
# default: a caller with no location has not under-specified a Mumbai value, it
# has asked a question with no answer.
#
# The convention is the one Step 3's kalamsha work pinned, and it is named here
# once rather than spelled out twice, because the pair has to agree: kalamsha is
# the gap between a planet's rise and the Sun's rise, so a rise taken under one
# convention and a set under another would not be a gap at all. Config states
# the same string at `combustion.rise_set_flags` and the harness checks the two
# have not drifted apart.

#: Disc CENTRE on the true horizon, no refraction correction. The choice is
#: worth four to five minutes: upper-limb-with-refraction, the usual almanac
#: convention, puts the Sun up earlier. That is why it is carried on every
#: record rather than assumed -- and why the combustion thresholds calibrated
#: from the 2026 source sit a uniform ~2.3 degrees below the classical table.
#: That offset is a rise/set convention offset, and this is the convention it
#: is an offset from.
RISE_SET_CONVENTION = "disc_center_no_refraction"
RISE_SET_BITS = swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION


def _horizon_crossing(day: dt.date, loc: dict, calc: int) -> dt.datetime:
    """First crossing of `calc` after the start of `day` in `loc`'s own zone.

    The search is anchored at the venue's own civil midnight -- the same civil
    day the rest of the layer is keyed on, per
    `weekday_rule.convention: civil_day_overlap` -- and not at a local-noon or
    UT-midnight approximation of it. That is not a detail. Anchored at local
    noon, `sunrise(D)` returns the rise of D+1: a true instant filed under the
    wrong date, which is the one defect this project exists to make impossible.
    """
    ephem.init()
    lo, _ = civil_day_bounds(day, ZoneInfo(loc["tz"]))
    flags = ephem.backend_flag() | calc | RISE_SET_BITS
    res = swe.rise_trans(ephem.to_jd(lo), swe.SUN, flags,
                         (loc["lon"], loc["lat"], loc["alt"]), 0, 0)
    return ephem.from_jd(res[1][0])


def sunrise(day: dt.date, loc: dict) -> dt.datetime:
    """Sunrise of civil day `day` at `loc`, as a UTC instant."""
    return _horizon_crossing(day, loc, swe.CALC_RISE)


def sunset(day: dt.date, loc: dict) -> dt.datetime:
    """Sunset of civil day `day` at `loc`, as a UTC instant."""
    return _horizon_crossing(day, loc, swe.CALC_SET)


# ------------------------------------------------- weekday-rule evaluation

@dataclass(frozen=True)
class RuleHit:
    day: dt.date
    weekday: str
    start: dt.datetime | None   # UTC; None means the condition held at midnight
    end: dt.datetime | None
    location: str
    full_day: bool


def _refine(cond, before: dt.datetime, after: dt.datetime,
            iters: int = 24) -> dt.datetime:
    """Bisect a coarse-grid transition down to the second.

    The scan grid only tells us the condition changed somewhere inside one
    step. The source quotes From/Till times to the minute, so leaving the
    boundary on the grid would put every span up to a step out.
    """
    state = cond(before)
    lo, hi = before, after
    for _ in range(iters):
        mid = lo + (hi - lo) / 2
        if cond(mid) == state:
            lo = mid
        else:
            hi = mid
    edge = lo + (hi - lo) / 2
    if edge.microsecond >= 500_000:
        edge += dt.timedelta(seconds=1)
    return edge.replace(microsecond=0)


def _condition_spans(cond, lo: dt.datetime, hi: dt.datetime,
                     step: dt.timedelta):
    """Contiguous sub-intervals of [lo, hi) where cond(t) is true.

    Boundaries interior to the interval are refined to the second; boundaries
    that coincide with the interval edges are left as-is, since the condition
    continues outside the day.
    """
    spans, t, open_at, prev = [], lo, None, None
    while t < hi:
        now = cond(t)
        if now and open_at is None:
            open_at = lo if prev is None else _refine(cond, prev, t)
        elif not now and open_at is not None:
            spans.append((open_at, _refine(cond, prev, t)))
            open_at = None
        prev, t = t, t + step
    if open_at is not None:
        spans.append((open_at, hi))
    return spans


def evaluate_weekday_rule(cond, weekdays: set[int], year: int, loc_key: str,
                          step_minutes: int = 5) -> list[RuleHit]:
    """Find every local civil day of `year` falling on one of `weekdays`
    during which `cond` holds at any moment.

    cond takes a timezone-aware UTC datetime and returns bool.
    weekdays uses Python's Monday=0 convention, in the *local* zone.
    """
    loc = CONF["locations"][loc_key]
    tz = ZoneInfo(loc["tz"])
    step = dt.timedelta(minutes=step_minutes)
    hits = []
    day = dt.date(year, 1, 1)
    last = dt.date(year, 12, 31)
    while day <= last:
        if day.weekday() in weekdays:
            lo, hi = civil_day_bounds(day, tz)
            spans = _condition_spans(cond, lo, hi, step)
            if spans:
                start = spans[0][0]
                end = spans[-1][1]
                hits.append(RuleHit(
                    day=day, weekday=day.strftime("%a"),
                    start=None if start == lo else start,
                    end=None if end >= hi else end,
                    location=loc["label"],
                    full_day=(start == lo and end >= hi),
                ))
        day += dt.timedelta(days=1)
    return hits


# ------------------------------------------------------------ condition helpers

def tithi_is(*nums: int):
    """Match tithi numbers 1..30. Pass both paksha values for 'any Ashtami'."""
    wanted = set(nums)
    return lambda t: at(t).tithi_num in wanted


def nakshatra_is(*names: str):
    wanted = set(names)
    return lambda t: at(t).nakshatra in wanted


def yoga_is(*names: str):
    wanted = set(names)
    return lambda t: at(t).yoga in wanted


# ---------------------------------------------------------------- total days

def total_days(year: int) -> list[dt.date]:
    """Source rule, validated 12/12 against 2026: dd + mm equals the two-digit
    year. Arithmetic only, no ephemeris, certainty A."""
    yy = year % 100
    out = []
    for month in range(1, 13):
        dd = yy - month
        try:
            out.append(dt.date(year, month, dd))
        except ValueError:
            continue
    return out


# ------------------------------------------------- tithi and yoga boundaries
# The elements above are sampled AT an instant. These are the instants the
# elements change, which is a different quantity and the one a rule stated over
# a tithi or a yoga needs: "Ekadashi on Friday" is a question about which
# Fridays an Ekadashi touches, and only a boundary answers it.
#
# The method is the one the 2026 source states for its own Bhadra windows and
# the one Step 3 verified against them -- bisection on an exact multiple of the
# Moon-Sun angle -- applied to the 12-degree step that is a tithi and the
# 360/27 step that is a yoga instead of the 6-degree step that is a karana.


@dataclass(frozen=True)
class Boundary:
    """One panchang division ending and the next beginning."""

    instant: dt.datetime
    num_from: int
    num_to: int
    name_from: str
    name_to: str
    paksha_from: str | None = None      #: tithi only; a yoga has no fortnight
    paksha_to: str | None = None


def tithi_boundaries(start: dt.datetime, end: dt.datetime) -> list[Boundary]:
    """Every tithi boundary in [start, end), all 30 of them per lunation.

    Frame-free: elongation is a difference of two longitudes, so the ayanamsha
    cancels and no ayanamsha choice can move one of these instants.
    """
    out = []
    for inst, frm, to in ephem.tithi_ingresses(start, end):
        a, b = frm + 1, to + 1
        out.append(Boundary(inst, a, b, tithi_name(a), tithi_name(b),
                            paksha_of(a), paksha_of(b)))
    return out


def karana_boundaries(start: dt.datetime, end: dt.datetime) -> list[Boundary]:
    """Every karana boundary in [start, end), all 60 of them per lunation.

    THE SOURCE'S OWN METHOD, AT THE SOURCE'S OWN ARC. The Bhadra section says
    it outright -- "A Bhadra (Vishti karana) is a 6 degree step of Moon-Sun
    elongation" -- and this is the same bisection `tithi_boundaries` runs on
    12 degrees, which is why every second one of these instants IS a tithi
    boundary and why the tithi series already reproduced eight of the
    section's sixteen January boundaries to 25 seconds.

    Frame-free, for the tithi's reason: elongation is a DIFFERENCE of two
    longitudes, so the ayanamsha subtracts from both and cancels, and no
    ayanamsha choice can move one of these instants.
    """
    out = []
    for inst, frm, to in ephem.karana_ingresses(start, end):
        a, b = frm + 1, to + 1
        out.append(Boundary(inst, a, b, karana_name(a), karana_name(b)))
    return out


def yoga_boundaries(start: dt.datetime, end: dt.datetime) -> list[Boundary]:
    """Every yoga boundary in [start, end), 27 per turn of the sum.

    NOT frame-free, unlike the tithi: the yoga is the SUM of the two longitudes
    and the ayanamsha subtracts from both, so it enters twice instead of
    cancelling. These instants sit where config's Lahiri puts them.
    """
    out = []
    for inst, frm, to in ephem.yoga_ingresses(start, end):
        a, b = frm + 1, to + 1
        out.append(Boundary(inst, a, b, YOGA_NAMES[a - 1], YOGA_NAMES[b - 1]))
    return out
