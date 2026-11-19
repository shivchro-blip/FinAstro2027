"""Combustion (asta) and reappearance (udaya) by classical kalamsha.

Three hypotheses were tested against all 23 combust/rise dates in the 2026
source:

    fixed ecliptic-elongation orbs   REJECTED - Mercury's 13 events span
                                     10.0deg to 15.4deg, Venus 4.6deg to 14.1deg
    SE heliacal_ut visibility        REJECTED - Venus off by 9-10 days,
                                     Mars by 13
    classical kalamsha               CONFIRMED

Kalamsha is the gap between the planet's rise and the Sun's rise (morning
visibility) or between the planet's set and the Sun's set (evening), expressed
in degrees of time at 15 degrees per hour. Measured that way the source dates
give near-constant values per planet:

    Jupiter  9.42 / 9.44        Saturn  12.84 / 12.63      Mars  15.48
    Venus    6.97 / 6.80 direct, 5.74 / 5.16 retrograde
    Mercury  10.81 - 12.47 across all thirteen events

Each sits a uniform ~2.3deg below the classical table (Mercury 14/12, Venus
10/8, Mars 17, Jupiter 11, Saturn 15), which is a rise/set convention offset
rather than a different method. The thresholds in config are calibrated from
the source so the 2027 output reproduces its behaviour rather than approximating
it.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import swisseph as swe

from . import ephem
from .config import CONF, PRIMARY
from .timezones import UTC

_C = CONF["combustion"]
_RS_FLAGS = swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION


def _rise_or_set(day: dt.date, body: str, rising: bool, loc: dict) -> float:
    jd0 = swe.julday(day.year, day.month, day.day) - 0.5 - loc["lon"] / 360.0
    flag = swe.CALC_RISE if rising else swe.CALC_SET
    # The ephemeris flag goes in `flags`, never OR'd into `rsmi`: FLG_SWIEPH
    # is 2, which is CALC_SET, so under the Swiss Ephemeris files a "rise"
    # silently became a set. Under Moshier (4 = CALC_MTRANSIT, ignored beside
    # CALC_RISE/SET) it happened to work, which is how it went unseen.
    res = swe.rise_trans(jd0, ephem.body_id(body), flag | _RS_FLAGS,
                         (loc["lon"], loc["lat"], loc["alt"]), 0, 0,
                         ephem.backend_flag())
    return res[1][0]


def kalamsha(day: dt.date, body: str, morning: bool,
             loc: dict | None = None) -> float:
    """Time-degree gap between planet and Sun at the horizon.

    morning=True  -> planet rises before the Sun (eastern / morning visibility)
    morning=False -> planet sets after the Sun (western / evening visibility)
    """
    ephem.init()
    loc = loc or PRIMARY
    if morning:
        planet = _rise_or_set(day, body, True, loc)
        sun = _rise_or_set(day, "Sun", True, loc)
        raw = (sun - planet) * 360.0
    else:
        planet = _rise_or_set(day, body, False, loc)
        sun = _rise_or_set(day, "Sun", False, loc)
        raw = (planet - sun) * 360.0
    # Rise and set instants are found independently, so the pair can straddle a
    # day boundary and produce a 360-degree artefact. Wrap to the short arc.
    return ((raw + 180) % 360) - 180


def threshold(body: str, retrograde: bool) -> float:
    key = "retrograde" if retrograde else "direct"
    return _C["thresholds_deg"][body.lower()][key]


def precision_days(body: str) -> int:
    """Measured day-resolution limit for this body, from calibration scatter."""
    return _C["precision_days"][body.lower()]


def certainty_of(body: str) -> str:
    return _C["certainty"][body.lower()]


def is_morning_star(when: dt.datetime, body: str) -> bool:
    """Planet behind the Sun in longitude rises first: eastern, morning."""
    return ephem.separation(when, body, "Sun") < 0


@dataclass(frozen=True)
class CombustionEvent:
    instant: dt.datetime      # UTC, resolved to the day
    body: str
    kind: str                 # "combust" | "rise"
    direction: str            # "East" | "West"
    kalamsha: float
    retrograde: bool
    certainty: str            # A, or B where calibration scatter is wide
    precision_days: int       # reported date is good to +/- this many days


#: Beyond this elongation a planet is unambiguously visible, and the horizon
#: geometry stops being meaningful. Guards against artefacts near opposition.
_MAX_ELONGATION = 60.0


def _state(day: dt.date, body: str) -> tuple[bool, bool, float]:
    """(is_combust, retrograde, kalamsha) for a given civil day."""
    noon = dt.datetime(day.year, day.month, day.day, 12, tzinfo=UTC)
    sep = ephem.separation(noon, body, "Sun")
    retro = ephem.position(noon, body).retrograde
    if abs(sep) > _MAX_ELONGATION:
        return False, retro, float("nan")
    k = kalamsha(day, body, morning=sep < 0)
    return k < threshold(body, retro), retro, k


def find_events(body: str, start: dt.date, end: dt.date) -> list[CombustionEvent]:
    """Transitions of the combust flag, resolved to the nearer civil day.

    The threshold is crossed somewhere between two consecutive days. The day
    whose kalamsha sits closer to the threshold is reported, which is what the
    2026 source does.
    """
    out = []
    certainty = certainty_of(body)
    prec = precision_days(body)
    day = start
    prev_state, _, prev_k = _state(day, body)
    prev_day = day
    day += dt.timedelta(days=1)
    while day <= end:
        cur, retro, k = _state(day, body)
        if cur != prev_state:
            thr = threshold(body, retro)
            chosen, chosen_k = (
                (prev_day, prev_k)
                if abs(prev_k - thr) <= abs(k - thr) else (day, k)
            )
            noon = dt.datetime(chosen.year, chosen.month, chosen.day, 12,
                               tzinfo=UTC)
            out.append(CombustionEvent(
                instant=noon,
                body=body,
                kind="combust" if cur else "rise",
                direction="East" if is_morning_star(noon, body) else "West",
                kalamsha=round(chosen_k, 2),
                retrograde=retro,
                certainty=certainty,
                precision_days=prec,
            ))
            prev_state = cur
        prev_day, prev_k = day, k
        day += dt.timedelta(days=1)
    return out
