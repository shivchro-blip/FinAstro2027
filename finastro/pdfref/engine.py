"""Condition engine for the reference-PDF rules.

Positions come from finastro.ephem (Swiss Ephemeris, Lahiri, mean node) --
the same calls the astronomy layer makes, so a sign or nakshatra boundary
found here is the same instant the 2027 astronomy layer records.

A condition is a predicate over a Snapshot (every body's position at one
instant). `spans(pred)` samples the predicate on a fixed grid and bisects
every change of value down to `RESOLUTION`, returning half-open windows
[start, end). A condition that can switch on and off inside one grid step
would be missed, so the grid is 1 hour: the fastest body (the Moon) moves
~0.55 deg in that time, far below any arc a rule here conditions on.
"""
from __future__ import annotations

import bisect
import datetime as dt
import functools
from dataclasses import dataclass, field

from .. import ephem as E

UTC = dt.timezone.utc
STEP = dt.timedelta(hours=1)
RESOLUTION = dt.timedelta(seconds=30)

#: Rahu/Ketu are the mean node (config `node: mean`); Herschel is Uranus.
BODIES = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
          "Rahu", "Ketu", "Uranus", "Neptune", "Pluto")
SOURCE_NAME = {"Uranus": "Herschel"}
SIGNS = E.SIGNS
NAKS = E.NAKSHATRAS
NAK_ARC = 360 / 27
PADA_ARC = NAK_ARC / 4
#: Abhijit, for the 28-name Sarvatobhadra wheel: 276deg40' - 280deg00', the
#: last pada of Uttara Ashadha. Measured on the 2026 document's own residency
#: tables: Abhijit begins at 276deg40' in all four (Sun, Mars, Mercury, Venus)
#: and Shravana begins at 280deg00' in the Sun, Mars and Venus tables; the
#: Mercury table alone ends Abhijit at 283deg20' (recorded as a conflict).
#: (An earlier build used 276deg40' - 280deg53'20", another convention.)
ABHIJIT = (276 + 40 / 60, 280.0)

#: TA p.144 (printed p.114) NORMAL SPEED OF PLANETS PER DAY, deg/day.
#: "SPEED LOWER THAN SPECIFIED IS CALLED SLOW OR MAND / SPEED HIGHER THAN
#: SPECIFIED IS CALLED FAST OR ATICHARI".
def _dms(d, m, s):
    return d + m / 60 + s / 3600


NORMAL_SPEED = {
    "Sun": _dms(0, 59, 10.68), "Moon": _dms(13, 20, 0),
    "Mars": _dms(0, 31, 26.46), "Mercury": _dms(1, 40, 0),
    "Jupiter": _dms(0, 4, 59.17), "Venus": _dms(1, 36, 0),
    "Saturn": _dms(0, 2, 0.4), "Rahu": _dms(0, 3, 11), "Ketu": _dms(0, 3, 11),
}


def name(body: str) -> str:
    return SOURCE_NAME.get(body, body)


@dataclass(frozen=True)
class P:
    """One body at one instant."""
    body: str
    lon: float
    speed: float          # deg/day, sidereal frame
    retro: bool           # of-date speed < 0 (stations as almanacs define them)
    lat: float

    @property
    def sign_i(self): return int(self.lon // 30)
    @property
    def sign(self): return SIGNS[self.sign_i]
    @property
    def deg(self): return self.lon % 30
    @property
    def nak_i(self): return int(self.lon // NAK_ARC)
    @property
    def nak(self): return NAKS[self.nak_i]
    @property
    def pada(self): return int((self.lon % NAK_ARC) // PADA_ARC) + 1
    @property
    def nav_i(self): return int(self.lon // (30 / 9)) % 12
    @property
    def nav(self): return SIGNS[self.nav_i]
    @property
    def vargottama(self): return self.nav_i == self.sign_i

    @property
    def nak28(self) -> str:
        if ABHIJIT[0] <= self.lon < ABHIJIT[1]:
            return "Abhijeet"
        return self.nak

    @property
    def fast(self) -> bool:
        """Atichari per TA p.144: |speed| above the printed normal speed."""
        n = NORMAL_SPEED.get(self.body)
        return n is not None and not self.retro and abs(self.speed) > n

    @property
    def slow(self) -> bool:
        n = NORMAL_SPEED.get(self.body)
        return n is not None and abs(self.speed) < n


class Snapshot(dict):
    """body -> P at one instant, plus derived panchang quantities."""

    def __init__(self, t: dt.datetime, data: dict):
        super().__init__(data)
        self.t = t

    @property
    def elong(self):
        return (self["Moon"].lon - self["Sun"].lon) % 360

    @property
    def tithi(self) -> int:          # 1..30
        return int(self.elong // 12) + 1

    @property
    def paksha(self) -> str:
        return "Shukla" if self.tithi <= 15 else "Krishna"

    @property
    def yoga(self) -> int:           # 1..27
        return int(((self["Moon"].lon + self["Sun"].lon) % 360) // NAK_ARC) + 1

    def sign_dist(self, a: str, b: str) -> int:
        """House of b counted from a, inclusive (same sign = 1)."""
        return (self[b].sign_i - self[a].sign_i) % 12 + 1

    def ahead(self, a: str, b: str) -> bool:
        """a is ahead of b in zodiacal order (shorter arc)."""
        return ((self[a].lon - self[b].lon) % 360) < 180

    def in_sign(self, sign: str, bodies=BODIES):
        return [b for b in bodies if self[b].sign == sign]


@functools.lru_cache(maxsize=200_000)
def snapshot(t: dt.datetime) -> Snapshot:
    E.init()
    out = {}
    for b in BODIES:
        p = E.position(t, b)
        retro = (p.speed_of_date if p.speed_of_date is not None else p.speed) < 0
        if b in ("Rahu", "Ketu"):
            retro = True          # TA p.73: "RAHU WHICH IS ALWAYS RETROGRADE"
        out[b] = P(b, p.lon, p.speed, retro, p.lat)
    return Snapshot(t, out)


@dataclass
class Window:
    start: dt.datetime
    end: dt.datetime
    value: object = True
    open_start: bool = False      # condition already held when the scan began
    open_end: bool = False        # still holding when the scan ended

    @property
    def days(self) -> float:
        return (self.end - self.start).total_seconds() / 86400


@dataclass
class Grid:
    start: dt.datetime
    end: dt.datetime
    times: list = field(default_factory=list)

    def __post_init__(self):
        t = self.start
        while t <= self.end:
            self.times.append(t)
            t += STEP

    def snaps(self):
        return [snapshot(t) for t in self.times]


def _refine(fn, lo: dt.datetime, hi: dt.datetime, v_lo) -> dt.datetime:
    while hi - lo > RESOLUTION:
        mid = lo + (hi - lo) / 2
        mid = mid.replace(microsecond=0)
        if fn(snapshot(mid)) == v_lo:
            lo = mid
        else:
            hi = mid
    return hi.replace(microsecond=0)


def value_windows(grid: Grid, fn) -> list[Window]:
    """Windows of constant fn(snapshot) value, boundaries refined."""
    out: list[Window] = []
    prev_t, prev_v = grid.times[0], fn(snapshot(grid.times[0]))
    cur_start, cur_open = prev_t, True
    for t in grid.times[1:]:
        v = fn(snapshot(t))
        if v != prev_v:
            edge = _refine(fn, prev_t, t, prev_v)
            out.append(Window(cur_start, edge, prev_v, open_start=cur_open))
            cur_start, cur_open = edge, False
        prev_t, prev_v = t, v
    out.append(Window(cur_start, grid.times[-1], prev_v, open_start=cur_open,
                      open_end=True))
    return out


def spans(grid: Grid, pred) -> list[Window]:
    """Windows where pred(snapshot) is truthy; value = the truthy value."""
    return [w for w in value_windows(grid, pred) if w.value]


def crossings(grid: Grid, fn) -> list[tuple[dt.datetime, object, object]]:
    """Instants where fn's value changes: (t, before, after)."""
    ws = value_windows(grid, fn)
    return [(ws[i].end, ws[i].value, ws[i + 1].value) for i in range(len(ws) - 1)]


def conjunction_instants(grid: Grid, a: str, b: str):
    """Exact longitudinal conjunctions a-b (either direction of overtaking)."""
    def d(s): return ((s[a].lon - s[b].lon + 180) % 360) - 180
    out = []
    ts = grid.times
    prev = d(snapshot(ts[0]))
    for t0, t1 in zip(ts, ts[1:]):
        cur = d(snapshot(t1))
        if (prev < 0) != (cur < 0) and abs(prev - cur) < 90:
            lo, hi, flo = t0, t1, prev < 0
            while hi - lo > RESOLUTION:
                mid = (lo + (hi - lo) / 2).replace(microsecond=0)
                if (d(snapshot(mid)) < 0) == flo:
                    lo = mid
                else:
                    hi = mid
            out.append((hi, "a_overtakes_b" if flo else "b_overtakes_a"))
        prev = cur
    return out


def utc(y, m, d, h=0, mi=0):
    return dt.datetime(y, m, d, h, mi, tzinfo=UTC)
