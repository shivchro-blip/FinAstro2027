"""A timeline view over the generated astronomy layer.

The rule layer conditions on states -- "Venus is combust", "Mars and Jupiter are
in the same sign", "Mercury and Saturn are both retrograde" -- but the astronomy
layer emits *transitions*: ingresses, stations, combust and rise instants. This
module turns one into the other, and it does so by **reading
build/astronomy_2027.json and nothing else**.

That restriction is the point. No rule may re-run an ingress search, re-derive a
station or ask the ephemeris for a longitude: every state below is reconstructed
from records `build_2027.py` already emitted, so a rule and the calendar can
never disagree about where a planet was. Where a state genuinely is not in the
astronomy layer -- a planet's speed class, a sunrise -- this module does not
supply it, and the rule that needs it is recorded as blocked rather than
approximated. The tithi and yoga spans were in that list until the astronomy
layer grew the two ingress classes they are built from; they are read here
exactly like a sign span, from the boundary records and from nothing else.

The one thing reconstructed rather than read is the *leading* value of a span:
the astronomy layer's first ingress for a body tells us what the body moved
*into*, and the state before it comes from the same record's `_from` field, or,
for a body with no ingress of that frame in the span at all, from the position
every record of that body already carries. Both are still the astronomy layer.
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import functools
import json
import pathlib
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from .config import CONF
from .timezones import UTC, civil_day_bounds

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASTRONOMY = ROOT / "build" / "astronomy_2027.json"

#: Frames the astronomy layer emits an ingress series for, and the record class
#: and field names each is carried under.
FRAMES = {
    "sign":      ("sign_ingress", "sign_from", "sign_to", "sign"),
    "nakshatra": ("nakshatra_ingress", "nakshatra_from", "nakshatra_to",
                  "nakshatra"),
    "navamsa":   ("navamsa_ingress", "navamsa_from", "navamsa_to", "navamsa"),
}

#: The two panchang divisions the astronomy layer emits an ingress series for,
#: and the astronomy fields each carries its from/to values under. Held apart
#: from FRAMES because these are not positions of a body: a tithi is the
#: Moon-Sun elongation and a yoga their sum, so neither is keyed on a body and
#: neither has a from/to pair in the position frames above.
_PANCHANG_DIVISIONS = {
    "tithi": ("tithi_ingress", ("tithi", "tithi_name", "paksha")),
    "yoga": ("yoga_ingress", ("yoga", "yoga_name")),
}

#: Bodies whose motion never changes in the span, and so produce no station
#: record to read it from. The nodes are retrograde by construction under
#: config's `node: mean`; the luminaries never retrograde at all.
FIXED_MOTION = {"Sun": "direct", "Moon": "direct",
                "Rahu": "retrograde", "Ketu": "retrograde"}


def parse(ts: str) -> dt.datetime:
    return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


@dataclass(frozen=True)
class Span:
    """A state that holds continuously over [start, end).

    `open_start` / `open_end` mark a span the generated period cut rather than
    the sky: the state was already running when the carry-in began, or is still
    running when the carry-out ends. A rule must not read such a boundary as an
    event -- that is exactly the year-boundary truncation the 2026 source made.
    """

    start: dt.datetime
    end: dt.datetime
    value: object
    open_start: bool = False
    open_end: bool = False

    def overlaps(self, lo: dt.datetime, hi: dt.datetime) -> bool:
        if self.start == self.end:      # an instant: the day that contains it
            return lo <= self.start < hi
        return self.start < hi and lo < self.end

    def clipped(self, lo: dt.datetime, hi: dt.datetime) -> "Span | None":
        if not self.overlaps(lo, hi):
            return None
        return Span(max(self.start, lo), min(self.end, hi), self.value,
                    self.open_start or self.start < lo,
                    self.open_end or self.end > hi)


def _merge_adjacent(spans: list[Span]) -> list[Span]:
    """Join consecutive spans carrying the same value.

    A body can leave a sign and re-enter it after a station; those are two
    crossings and stay two records, but as a *state* the sign held throughout
    only if the two spans touch. They do not touch across a retrograde loop
    (the body was elsewhere in between), so nothing is merged that should not be.
    """
    out: list[Span] = []
    for s in spans:
        if out and out[-1].value == s.value and out[-1].end == s.start:
            prev = out.pop()
            out.append(Span(prev.start, s.end, s.value,
                            prev.open_start, s.open_end))
        else:
            out.append(s)
    return out


def flag(rec: dict, key: str) -> str | None:
    """The value of a `key=value` QA flag on a record, or None.

    The astronomy layer carries a handful of measured quantities this way --
    `direction=East`, `kalamsha=11.52`, `station=R` -- rather than as schema
    fields. Reading them here keeps the rule layer inside the emitted record.
    """
    for f in rec["qa"]["flags"]:
        if f.startswith(key + "="):
            return f.split("=", 1)[1]
    return None


_flag = flag        # internal alias, used below before `flag` reads naturally


class Sky:
    """Every state the rule layer is allowed to condition on."""

    def __init__(self, doc: dict) -> None:
        self.meta = doc["meta"]
        self.records = doc["records"]
        self.span_start = parse(self.meta["span_start_utc"])
        self.span_end = parse(self.meta["span_end_utc"])
        self.by_class: dict[str, list[dict]] = collections.defaultdict(list)
        for r in self.records:
            self.by_class[r["event_class"]].append(r)

    # ------------------------------------------------------------- loading
    @classmethod
    def load(cls, path: pathlib.Path = ASTRONOMY) -> "Sky":
        if not path.exists():
            raise SystemExit(f"{path} missing -- run python build_2027.py first")
        with path.open(encoding="utf-8") as fh:
            return cls(json.load(fh))

    # -------------------------------------------------------------- spans
    @functools.lru_cache(maxsize=None)
    def spans(self, body: str, frame: str) -> tuple[Span, ...]:
        """Contiguous spans of `body`'s position in `frame`, over the whole span.

        Built from the ingress series alone. The value is the position held
        during the span, so consecutive ingresses bound it and the record's own
        `_from` field supplies the state before the first one.
        """
        event_class, f_from, f_to, at = FRAMES[frame]
        ing = sorted((r for r in self.by_class[event_class]
                      if r["bodies"] and r["bodies"][0] == body),
                     key=lambda r: r["time"]["t_start_utc"])
        if not ing:
            # No crossing in the span: the body held one position throughout,
            # and every record it has already carries that position.
            any_rec = next((r for r in self.records
                            if r["bodies"] and r["bodies"][0] == body), None)
            if any_rec is None:
                return ()
            return (Span(self.span_start, self.span_end,
                         any_rec["astronomy"][at], True, True),)

        out = [Span(self.span_start, parse(ing[0]["time"]["t_start_utc"]),
                    ing[0]["astronomy"][f_from], open_start=True)]
        for k, r in enumerate(ing):
            start = parse(r["time"]["t_start_utc"])
            if k + 1 < len(ing):
                end, open_end = parse(ing[k + 1]["time"]["t_start_utc"]), False
            else:
                end, open_end = self.span_end, True
            out.append(Span(start, end, r["astronomy"][f_to], open_end=open_end))
        return tuple(_merge_adjacent(out))

    @functools.lru_cache(maxsize=None)
    def panchang_spans(self, division: str) -> tuple[Span, ...]:
        """Contiguous tithi or yoga spans, built from the boundary series alone.

        `division` is "tithi" or "yoga". The value is a dict carrying the number
        and the name held during the span, plus the fortnight for a tithi --
        read off the ingress record's own `_to` fields and never sampled,
        because the record's instant IS the cusp.

        These are the two series whose absence blocked eighteen catalogue-B
        sections in batch 3. Nothing here computes: a tithi's start and end are
        two consecutive `tithi_ingress` records, exactly as a sign's are two
        consecutive `sign_ingress` records.
        """
        cls, fields = _PANCHANG_DIVISIONS[division]
        ing = sorted(self.by_class[cls],
                     key=lambda r: r["time"]["t_start_utc"])
        if not ing:
            return ()

        def value(rec: dict, side: str) -> dict:
            return {k: rec["astronomy"][f"{k}_{side}"] for k in fields}

        out = [Span(self.span_start, parse(ing[0]["time"]["t_start_utc"]),
                    value(ing[0], "from"), open_start=True)]
        for k, r in enumerate(ing):
            start = parse(r["time"]["t_start_utc"])
            if k + 1 < len(ing):
                end, open_end = parse(ing[k + 1]["time"]["t_start_utc"]), False
            else:
                end, open_end = self.span_end, True
            out.append(Span(start, end, value(r, "to"), open_end=open_end))
        # Deliberately not merged. Two consecutive spans of one division cannot
        # carry the same value -- a boundary is where the value changes -- so a
        # merge here could only paper over a duplicate record.
        return tuple(out)

    def tithi_spans(self) -> tuple[Span, ...]:
        """Every tithi in the span, bounded. The value carries `tithi` (1-30),
        `tithi_name` and `paksha`."""
        return self.panchang_spans("tithi")

    def yoga_spans(self) -> tuple[Span, ...]:
        """Every yoga in the span, bounded. The value carries `yoga` (1-27) and
        `yoga_name`."""
        return self.panchang_spans("yoga")

    @functools.lru_cache(maxsize=None)
    def motion_spans(self, body: str) -> tuple[Span, ...]:
        """`direct` / `retrograde` spans, bounded by the station records.

        The station instant is the boundary: the body is retrograde from an R
        station to the next D station. Bodies config gives no station -- the
        luminaries and the mean nodes -- carry one span of fixed motion, which
        is a statement about the configuration and not a gap.
        """
        if body in FIXED_MOTION:
            return (Span(self.span_start, self.span_end, FIXED_MOTION[body],
                         True, True),)
        st = sorted((r for r in self.by_class["station"]
                     if r["bodies"][0] == body),
                    key=lambda r: r["time"]["t_start_utc"])
        after = {"motion/station_R": "retrograde", "motion/station_D": "direct"}
        if not st:
            return (Span(self.span_start, self.span_end, "direct", True, True),)
        lead = "direct" if after[st[0]["rule_family"]] == "retrograde" \
            else "retrograde"
        out = [Span(self.span_start, parse(st[0]["time"]["t_start_utc"]), lead,
                    open_start=True)]
        for k, r in enumerate(st):
            start = parse(r["time"]["t_start_utc"])
            if k + 1 < len(st):
                end, open_end = parse(st[k + 1]["time"]["t_start_utc"]), False
            else:
                end, open_end = self.span_end, True
            out.append(Span(start, end, after[r["rule_family"]],
                            open_end=open_end))
        return tuple(_merge_adjacent(out))

    @functools.lru_cache(maxsize=None)
    def combust_spans(self, body: str) -> tuple[Span, ...]:
        """Asta-to-udaya windows, paired off the combust and rise records.

        The window runs from the combust record's civil day to the rise
        record's civil day, exclusive of the rise day. That is the source's own
        convention and not a choice made here: its Duration column reads 33 for
        Mercury combust 02-Jan-26 and rise 04-Feb-26, which is the difference of
        the two dates.

        The value is the direction the source prints -- East or West -- read off
        the combust record's own `direction=` flag.
        """
        evs = sorted((r for r in self.by_class["combustion"]
                      if r["bodies"][0] == body),
                     key=lambda r: r["time"]["t_start_utc"])
        out: list[Span] = []
        open_at: dt.datetime | None = None
        direction: str | None = None
        if evs and evs[0]["rule_family"] == "visibility/rise":
            open_at = self.span_start          # already combust at carry-in
        for r in evs:
            t = parse(r["time"]["t_start_utc"])
            if r["rule_family"] == "visibility/combust":
                open_at, direction = t, _flag(r, "direction")
            elif open_at is not None:
                out.append(Span(open_at, t, direction,
                                open_start=(open_at == self.span_start)))
                open_at, direction = None, None
        if open_at is not None:
            out.append(Span(open_at, self.span_end, direction, open_end=True))
        return tuple(out)

    # ------------------------------------------------------------- horizon
    # A sunrise is not a state and not a transition between states: it is a
    # LOCATION PROPERTY, one instant per venue per civil day. Every accessor
    # below therefore takes `loc_key` and none of them has a default.
    #
    # That is what keeps `Sky` location-blind in the sense the rule layer needs.
    # Location-blind never meant "knows no location"; it meant "supplies none".
    # A condition function that asks for a sunrise must say whose, and a
    # condition function that does not ask never receives one -- so no rule can
    # acquire one venue's horizon by omission, which is the failure mode
    # `weekday_rule.evaluate_per_location` exists to prevent.

    #: The two horizon classes and nothing else. Named so a typo in a caller is
    #: a KeyError here rather than a silently empty list of instants.
    HORIZON_CLASSES = ("sunrise", "sunset")

    @functools.lru_cache(maxsize=None)
    def horizon_instants(self, event_class: str,
                         loc_key: str) -> tuple[dt.datetime, ...]:
        """Every `sunrise` or `sunset` instant emitted for `loc_key`, ascending.

        Read off the records' own `location` field. A record of either class
        with no location is a build error in `events.py` and cannot reach this
        file; if one ever does, it is rejected here rather than silently
        counted under whichever venue asked first.
        """
        if event_class not in self.HORIZON_CLASSES:
            raise KeyError(f"{event_class!r} is not a horizon class; "
                           f"expected one of {self.HORIZON_CLASSES}")
        if not loc_key:
            raise ValueError(
                f"{event_class} needs a location: it is a property of one "
                "horizon, and there is no default venue")
        if loc_key not in CONF["locations"]:
            raise KeyError(f"unknown location {loc_key!r}")
        out = []
        for r in self.by_class[event_class]:
            if r["location"] is None:
                raise ValueError(f"{r['id']}: {event_class} record carries no "
                                 "location")
            if r["location"] == loc_key:
                out.append(parse(r["time"]["t_start_utc"]))
        return tuple(sorted(out))

    def sunrises(self, loc_key: str) -> tuple[dt.datetime, ...]:
        """Every sunrise emitted for `loc_key`. The argument is required."""
        return self.horizon_instants("sunrise", loc_key)

    def sunsets(self, loc_key: str) -> tuple[dt.datetime, ...]:
        """Every sunset emitted for `loc_key`. The argument is required."""
        return self.horizon_instants("sunset", loc_key)

    def horizon_crossings_within(self, event_class: str, loc_key: str,
                                 span: "Span") -> tuple[dt.datetime, ...]:
        """The `loc_key` crossings falling inside [span.start, span.end).

        This is the whole of what Kshay and Vriddhi need: a tithi is Kshay when
        the count is zero and Vriddhi when it is two. A span the generated
        period cut is the caller's problem, not this function's -- an open end
        would under-count, and the rules that use it skip such spans rather
        than measure them.
        """
        xs = self.horizon_instants(event_class, loc_key)
        lo = bisect.bisect_left(xs, span.start)
        hi = bisect.bisect_left(xs, span.end)
        return xs[lo:hi]


    # ------------------------------------------------------------ instants
    def aspect_instants(self, event_class: str, a: str, b: str) -> list[dict]:
        """Exact conjunction or opposition records for an unordered pair."""
        want = {a, b}
        return sorted((r for r in self.by_class[event_class]
                       if set(r["bodies"]) == want),
                      key=lambda r: r["time"]["t_start_utc"])

    def class_records(self, event_class: str, family: str | None = None,
                      body: str | None = None) -> list[dict]:
        out = list(self.by_class[event_class])
        if family is not None:
            out = [r for r in out if r["rule_family"] == family]
        if body is not None:
            out = [r for r in out if body in r["bodies"]]
        return sorted(out, key=lambda r: r["time"]["t_start_utc"])

    # --------------------------------------------------------- combinators
    def value_at(self, body: str, frame: str, t: dt.datetime):
        spans = self.spans(body, frame)
        starts = [s.start for s in spans]
        i = bisect.bisect_right(starts, t) - 1
        return spans[i].value if 0 <= i < len(spans) else None


# ------------------------------------------------------------- span algebra

def intersect(a, b, value=None) -> list[Span]:
    """Every interval where a span from each list is simultaneously in force.

    `value` may be a callable taking the two values, in which case a pair whose
    result is None is dropped. That is how "same sign" is expressed: the value
    function returns the sign when the two agree and None when they do not.
    """
    out = []
    for x in a:
        for y in b:
            lo, hi = max(x.start, y.start), min(x.end, y.end)
            if lo >= hi:
                continue
            if callable(value):
                v = value(x.value, y.value)
            elif value is not None:
                v = value
            else:
                v = (x.value, y.value)
            if v is None:
                continue
            out.append(Span(lo, hi, v,
                            (x.open_start and x.start >= y.start)
                            or (y.open_start and y.start >= x.start),
                            (x.open_end and x.end <= y.end)
                            or (y.open_end and y.end <= x.end)))
    return _merge_adjacent(sorted(out, key=lambda s: s.start))


def where(spans, predicate) -> list[Span]:
    """The spans whose value satisfies `predicate`."""
    return [s for s in spans if predicate(s.value)]


def same(v1, v2):
    """Value function for `intersect`: the shared value, or None."""
    return v1 if v1 == v2 else None


# ------------------------------------------------------------- civil days

def civil_days(span: Span, loc_key: str, year: int) -> list[dt.date]:
    """Every civil day of `year` at `loc_key` that the span touches.

    This is `weekday_rule.convention: civil_day_overlap` -- the convention
    chosen in Step 3 by reproducing 13 source tables under four competing
    readings, where overlap scored 74/75 against 51 for prevailing-at-sunrise.
    It is applied here unchanged, per location, because the same evidence
    governs both layers.
    """
    tz = ZoneInfo(CONF["locations"][loc_key]["tz"])
    out = []
    day = span.start.astimezone(tz).date()
    last = span.end.astimezone(tz).date()
    while day <= last:
        lo, hi = civil_day_bounds(day, tz)
        if span.overlaps(lo, hi) and day.year == year:
            out.append(day)
        day += dt.timedelta(days=1)
    return out


def weekdays_in_span(span: Span, weekday: int, loc_key: str) -> list[dt.date]:
    """Every civil date inside `span` at `loc_key` falling on `weekday`.

    Monday=0, the same convention `Rule.weekdays` uses.

    This is calendar arithmetic and nothing else. It reads no record, asks no
    ephemeris and computes no position: given two instants and a venue, it says
    which of that venue's dates the interval covers and which of those are the
    named weekday. `civil_days` above already does the first half, per
    `weekday_rule.convention: civil_day_overlap`; this adds the second and is
    kept beside it for that reason.

    It exists because "Three Saturday in Shukla Paksh" COUNTS a weekday inside
    a window rather than requiring the firing day to be one, and `Rule.weekdays`
    can only express the requirement. A count is not a filter, and the rule
    layer had no way to say so -- which is a rule-layer limit and was never a
    third missing event class. Handling it here rather than on `Sky` is the
    point: `Sky` answers questions about the sky, and which dates a venue's
    calendar holds is not one of them.
    """
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday {weekday} outside Monday=0..Sunday=6")
    tz = ZoneInfo(CONF["locations"][loc_key]["tz"])
    out = []
    day = span.start.astimezone(tz).date()
    last = span.end.astimezone(tz).date()
    while day <= last:
        lo, hi = civil_day_bounds(day, tz)
        if span.overlaps(lo, hi) and day.weekday() == weekday:
            out.append(day)
        day += dt.timedelta(days=1)
    return out


def civil_day_span(first: dt.date, last: dt.date, loc_key: str) -> Span:
    """The UTC interval covering civil days `first` through `last` at `loc_key`.

    The inverse of `civil_days`, and beside it for the same reason: a rule that
    has picked out dates at a venue needs to hand `fire` a span, and building
    one means knowing that venue's midnights. Calendar arithmetic, no record and
    no ephemeris -- and kept here rather than in a rule module so no rule has to
    import a timezone to say what it means.
    """
    tz = ZoneInfo(CONF["locations"][loc_key]["tz"])
    lo, _ = civil_day_bounds(first, tz)
    _, hi = civil_day_bounds(last, tz)
    return Span(lo, hi, None)
