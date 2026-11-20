"""Detector building blocks shared by the rule catalogue.

A detector takes a Ctx and returns Hits. Hits carry the instant(s), the
bodies involved (for the planetary-condition text) and any computed facts.
"""
from __future__ import annotations

import bisect
import datetime as dt
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from ..config import CONF
from .engine import (BODIES, Grid, NORMAL_SPEED, SIGNS, conjunction_instants,
                     crossings, snapshot, spans, utc, value_windows, Window)

NY = ZoneInfo("America/New_York")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")
#: Grahas used for "alone", "together", hemming. The Moon is excluded (it
#: passes every sign in ~2.5 days; neither PDF says it breaks "alone"), and
#: so are the outers, which the PDFs name explicitly when they mean them.
POOL = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
DRISHTI = CONF["valence"]["drishti"] if "drishti" in CONF.get("valence", {}) else None
TITHI_NAMES = ("Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
               "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi")
YOGA_NAMES = ("Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
              "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
              "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
              "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
              "Shukla", "Brahma", "Indra", "Vaidhriti")
VYATIPATA, VAIDHRITI, INDRA = 17, 27, 26
NAK_LORD = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
            "Saturn", "Mercury") * 3
DAY_LORDS = {0: ("Moon",), 1: ("Mars",), 2: ("Mercury", "Rahu"),
             3: ("Jupiter", "Ketu"), 4: ("Venus",), 5: ("Saturn",), 6: ("Sun",)}


def tithi_label(n: int) -> str:
    if n == 15:
        return "Purnima"
    if n == 30:
        return "Amavasya"
    return ("Shukla " if n < 15 else "Krishna ") + TITHI_NAMES[(n - 1) % 15]


def aspects(s, src: str, dst: str) -> bool:
    """Whole-sign graha drishti of src onto dst (project convention)."""
    d = CONF["valence"]["drishti"]
    if src in ("Uranus", "Neptune", "Pluto"):
        return False
    houses = {"Mars": d["Mars"], "Jupiter": d["Jupiter"],
              "Saturn": d["Saturn"]}.get(src, d["nodes"] if src in ("Rahu", "Ketu") else d["all"])
    return s.sign_dist(src, dst) in houses


@dataclass
class Hit:
    start: dt.datetime
    end: dt.datetime | None = None          # None -> instant
    bodies: tuple = ()
    facts: dict = field(default_factory=dict)
    day: dt.date | None = None              # day-granular hit (NY civil day)
    open_start: bool = False
    open_end: bool = False


@dataclass
class Ctx:
    grid: Grid
    sky: object
    year: int
    loc: str = "new_york"       # whose sunrise fixes the Hindu day for daily rules

    def __post_init__(self):
        self.tz = NY if self.loc == "new_york" else ZoneInfo("Asia/Kolkata")
        self.sunrises = list(self.sky.sunrises(self.loc))
        self.sunsets = list(self.sky.sunsets(self.loc))

    def ny_days(self):
        d = dt.date(self.year, 1, 1)
        while d.year == self.year:
            yield d
            d += dt.timedelta(days=1)

    def sunrise(self, day: dt.date):
        lo = dt.datetime(day.year, day.month, day.day, tzinfo=self.tz).astimezone(dt.timezone.utc)
        i = bisect.bisect_left(self.sunrises, lo)
        return self.sunrises[i]

    def sunset(self, day: dt.date):
        lo = dt.datetime(day.year, day.month, day.day, tzinfo=self.tz).astimezone(dt.timezone.utc)
        i = bisect.bisect_left(self.sunsets, lo)
        return self.sunsets[i]


# ------------------------------------------------------------ factories
def windows(pred, bodies=(), facts=None):
    """Hits for every window where pred(snapshot) is truthy."""
    def run(ctx):
        out = []
        for w in spans(ctx.grid, pred):
            f = dict(facts(snapshot(w.start + (w.end - w.start) / 2), w) if facts else {})
            if not isinstance(w.value, bool):
                f.setdefault("value", w.value)
            b = bodies(w.value) if callable(bodies) else bodies
            out.append(Hit(w.start, w.end, tuple(b), f, open_start=w.open_start,
                           open_end=w.open_end))
        return out
    return run


def entries(pred, bodies=(), effect_days=None, facts=None):
    """Instant hits where pred turns true (window starts), optional effect window."""
    def run(ctx):
        out = []
        for w in spans(ctx.grid, pred):
            if w.open_start:
                continue
            f = dict(facts(snapshot(w.start), w) if facts else {})
            f["condition_ends_utc"] = w.end
            if effect_days:
                f["effect_window_days"] = effect_days
            b = bodies(w.value) if callable(bodies) else bodies
            out.append(Hit(w.start, w.start + dt.timedelta(days=effect_days) if effect_days else None,
                           tuple(b), f))
        return out
    return run


def daily(pred, bodies=()):
    """Day hits: pred(snapshot_at_NY_sunrise, weekday_index, day, ctx)."""
    def run(ctx):
        out = []
        for d in ctx.ny_days():
            sr = ctx.sunrise(d)
            s = snapshot(sr.replace(microsecond=0))
            r = pred(s, d.weekday(), d, ctx)
            if r:
                out.append(Hit(sr, None, tuple(bodies), r if isinstance(r, dict) else {},
                               day=d))
        return out
    return run


def conjunctions(a, b, same_sign=False):
    def run(ctx):
        out = []
        for t, how in conjunction_instants(ctx.grid, a, b):
            s = snapshot(t)
            out.append(Hit(t, None, (a, b), {"overtaking": f"{a} overtakes {b}" if how == "a_overtakes_b" else f"{b} overtakes {a}"}))
        return out
    return run


def sign_rel(a, b, houses, ordered=False):
    """b in one of `houses` counted from a (inclusive). Unordered also tests a from b."""
    hs = set(houses)

    def pred(s):
        d = s.sign_dist(a, b)
        if ordered:
            return d in hs
        return d in hs or s.sign_dist(b, a) in hs
    return pred


def both_direct(s, *bodies):
    return all((not s[b].retro) or b in ("Rahu", "Ketu") for b in bodies)
