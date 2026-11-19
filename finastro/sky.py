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
    # The karana, added 20-Sep-2026 with the Bhadra port. It is the same angle
    # as the tithi at half the arc, so it needs no new span machinery at all --
    # one entry here, and `karana_spans()` is `panchang_spans("karana")`.
    "karana": ("karana_ingress", ("karana", "karana_name")),
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

    `precision` says whether the ENDPOINTS ARE INSTANTS AT ALL, which is a
    different question from how accurate they are. The astronomy layer's own
    `time.precision` (exact / minutes / hours / date_only) is about ACCURACY and
    stays on the record; this field is about EXISTENCE, and the renderer reads
    it to decide whether a row may carry a clock time:

    * `exact` -- both endpoints are computed instants;
    * `date_only` -- the endpoints are civil-day boundaries, because what
      produced the span was date-granular: a combust or rise record the
      ephemeris emits as a date, or a window built by `civil_day_span`;
    * `anchored` -- the endpoint is a date THIS BUILD CHOSE. The reference-table
      carried-in rows are the only case.

    Together with `open_start` this separates the four ways a span can begin at
    a midnight. Three of them are not events, and before 15-Sep-2026 all four
    rendered as `00:00 IST` beside a previous-Eastern-day afternoon.
    """

    start: dt.datetime
    end: dt.datetime
    value: object
    open_start: bool = False
    open_end: bool = False
    precision: str = "exact"

    def overlaps(self, lo: dt.datetime, hi: dt.datetime) -> bool:
        if self.start == self.end:      # an instant: the day that contains it
            return lo <= self.start < hi
        return self.start < hi and lo < self.end

    def clipped(self, lo: dt.datetime, hi: dt.datetime) -> "Span | None":
        if not self.overlaps(lo, hi):
            return None
        return Span(max(self.start, lo), min(self.end, hi), self.value,
                    self.open_start or self.start < lo,
                    self.open_end or self.end > hi,
                    self.precision)


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
                            prev.open_start, s.open_end,
                            _weaker(prev.precision, s.precision)))
        else:
            out.append(s)
    return out


#: Least-instant-bearing first. Combining two spans can only lose the property
#: of having an instant, never gain it, so the weaker of the two wins.
_PRECISION_ORDER = ("anchored", "date_only", "exact")


def _weaker(*precisions: str) -> str:
    """The least instant-bearing of the precisions given.

    An unknown value raises rather than defaulting: a precision nobody chose is
    exactly the shape of the tier bug -- `tier_derivation.unmapped_is_an_error`
    exists for the same reason -- and defaulting it to `exact` would hand a row
    a clock time on the strength of a typo.
    """
    for p in precisions:
        if p not in _PRECISION_ORDER:
            raise ValueError(f"unknown span precision {p!r}; "
                             f"expected one of {_PRECISION_ORDER}")
    return min(precisions, key=_PRECISION_ORDER.index)


def record_precision(rec: dict) -> str:
    """A record's `Span.precision`, from its own `time.precision`.

    The astronomy layer grades accuracy in four steps -- exact, minutes, hours,
    date_only -- and only the last of them means NO INSTANT EXISTS. `minutes`
    and `hours` are instants with an error bar, and an error bar is not a reason
    to withhold the time; `date_only` is a date the ephemeris never resolved to
    a moment, and rendering one as a clock time invents the moment.
    """
    return "date_only" if rec["time"]["precision"] == "date_only" else "exact"


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

    def karana_spans(self) -> tuple[Span, ...]:
        """Every karana in the span, bounded. The value carries `karana`
        (1-60) and `karana_name`.

        A BHADRA IS ONE OF THESE, and nothing here knows that. The window the
        source prints is a Vishti karana's span, start to end, and it is two
        consecutive `karana_ingress` records exactly as a tithi's is two
        consecutive `tithi_ingress` records. The selection of WHICH karanas
        are Bhadras belongs to the rule, which reads the source's own eight
        numbers -- not to this layer, which takes no interpretation.
        """
        return self.panchang_spans("karana")

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

        THE WINDOW HAS NO INSTANT. Kalamsha is a horizon measurement and the
        records are emitted at `precision: date_only`, so both endpoints are IST
        midnights -- 18:30Z -- and not moments anything crossed. That precision
        is carried onto the span rather than left on the record, because by the
        time the renderer sees a row the record is three layers behind it, and
        for a year these windows rendered as `00:00 IST`.
        """
        evs = sorted((r for r in self.by_class["combustion"]
                      if r["bodies"][0] == body),
                     key=lambda r: r["time"]["t_start_utc"])
        out: list[Span] = []
        open_at: dt.datetime | None = None
        direction: str | None = None
        prec: str = "exact"
        if evs and evs[0]["rule_family"] == "visibility/rise":
            open_at = self.span_start          # already combust at carry-in
            prec = record_precision(evs[0])
        for r in evs:
            t = parse(r["time"]["t_start_utc"])
            if r["rule_family"] == "visibility/combust":
                open_at, direction = t, _flag(r, "direction")
                prec = record_precision(r)
            elif open_at is not None:
                out.append(Span(open_at, t, direction,
                                open_start=(open_at == self.span_start),
                                precision=_weaker(prec, record_precision(r))))
                open_at, direction, prec = None, None, "exact"
        if open_at is not None:
            out.append(Span(open_at, self.span_end, direction, open_end=True,
                            precision=prec))
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

    # ---------------------------------------------------------- lunar months
    #: Lunar month named by the Sun's sidereal sign at the new moon that opens
    #: it, in the 2026 document's own spelling ("Falgun", "Shravan").
    MONTH_BY_SUN_SIGN = {
        "Pisces": "Chaitra", "Aries": "Vaishakh", "Taurus": "Jyeshtha",
        "Gemini": "Ashadh", "Cancer": "Shravan", "Leo": "Bhadrapad",
        "Virgo": "Ashwin", "Libra": "Kartik", "Scorpio": "Margashirsh",
        "Sagittarius": "Paush", "Capricorn": "Magh", "Aquarius": "Falgun"}

    @functools.lru_cache(maxsize=None)
    def lunar_months(self) -> tuple:
        """((new_moon, next_new_moon, name), ...) -- AMANTA months off the
        lunation series, named by the Sun's sign at the opening new moon. A
        month whose closing new moon finds the Sun in the same sign is Adhik
        (2026's Adhik Jyeshtha comes out of this)."""
        nms = [parse(r["time"]["t_start_utc"])
               for r in self.class_records("lunation", family="lunation/new_moon")]
        sun = self.spans("Sun", "sign")

        def sign_at(t):
            return next(sp.value for sp in sun if sp.start <= t < sp.end)
        out = []
        for a, b in zip(nms, nms[1:]):
            name = self.MONTH_BY_SUN_SIGN[sign_at(a)]
            out.append((a, b, ("Adhik " + name) if sign_at(a) == sign_at(b) else name))
        return tuple(out)

    def purnimanta_month(self, t) -> str | None:
        """The PURNIMANTA month holding instant `t`: the 2026 document's system,
        settled by its own eclipse labels (solar 17-Feb-26 Falgun, 12-Aug-26
        Shravan -- amanta would read Magh and Ashadh). Shukla paksha carries
        the amanta month's name; Krishna paksha, after the full moon, already
        belongs to the next month."""
        months = self.lunar_months()
        fms = [parse(r["time"]["t_start_utc"])
               for r in self.class_records("lunation", family="lunation/full_moon")]
        for k, (a, b, name) in enumerate(months):
            if a <= t < b:
                fm = next((f for f in fms if a <= f < b), None)
                if fm is not None and t >= fm:
                    return months[k + 1][2] if k + 1 < len(months) else None
                return name
        return None

    def eclipse_month(self, rec: dict) -> str | None:
        """Purnimanta month of an eclipse, by the lunation it sits on: a solar
        eclipse is named for its Amavasya (the month that new moon CLOSES, which
        is the amanta month it opens) and a lunar one for its Purnima (the same
        name in both systems). Read off the eclipse's maximum."""
        mx = parse(rec["time"]["contacts_global"]["max"]["utc"])
        months = self.lunar_months()
        if rec["rule_family"] == "eclipse/solar":
            m = min(months, key=lambda m: abs((m[0] - mx).total_seconds()))
            return m[2]
        return next((m[2] for m in months if m[0] <= mx < m[1]), None)

    def class_records(self, event_class: str, family: str | None = None,
                      body: str | None = None) -> list[dict]:
        out = list(self.by_class[event_class])
        if family is not None:
            out = [r for r in out if r["rule_family"] == family]
        if body is not None:
            out = [r for r in out if body in r["bodies"]]
        return sorted(out, key=lambda r: r["time"]["t_start_utc"])

    @functools.lru_cache(maxsize=None)
    def body_records(self, body: str) -> tuple[dict, ...]:
        """Every record of `body`, in time order, whatever its event class.

        No rule needs an ingress to satisfy a condition on a CONTINUOUS
        quantity -- Shar is the sign of the ecliptic latitude, which the
        astronomy layer samples on every record a body has rather than at a
        boundary it emits. Walking those records is therefore still reading the
        astronomy layer and nothing else: the samples are the emitted ones, and
        no condition may ask for a longitude or a latitude of its own.
        """
        return tuple(sorted((r for r in self.records
                             if r["bodies"] and r["bodies"][0] == body),
                            key=lambda r: r["time"]["t_start_utc"]))

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
                            or (y.open_end and y.end <= x.end),
                            _weaker(x.precision, y.precision)))
    return _merge_adjacent(sorted(out, key=lambda s: s.start))


def where(spans, predicate) -> list[Span]:
    """The spans whose value satisfies `predicate`."""
    return [s for s in spans if predicate(s.value)]


def same(v1, v2):
    """Value function for `intersect`: the shared value, or None."""
    return v1 if v1 == v2 else None


# ------------------------------------------------------------- civil days

def days_touched(span: Span, loc_key: str) -> list[dt.date]:
    """Every civil day at `loc_key` the span touches, WITH NO YEAR CLIP.

    `civil_days` below is this list filtered to one year, and the two are kept
    as one definition because the DIFFERENCE between them is a fact the calendar
    has to report: see `year_clip`.

    The half-open interval is what makes the last entry right. A span ending at
    `2027-02-20T18:30:00Z` -- 21-Feb 00:00 IST -- does not overlap 21-Feb at
    Mumbai, because `Span.overlaps` tests `lo < end` and `lo == end` there. The
    last day is 20-Feb, which is also the last day a row exists for.
    """
    tz = ZoneInfo(CONF["locations"][loc_key]["tz"])
    out = []
    day = span.start.astimezone(tz).date()
    last = span.end.astimezone(tz).date()
    while day <= last:
        lo, hi = civil_day_bounds(day, tz)
        if span.overlaps(lo, hi):
            out.append(day)
        day += dt.timedelta(days=1)
    return out


def civil_days(span: Span, loc_key: str, year: int) -> list[dt.date]:
    """Every civil day of `year` at `loc_key` that the span touches.

    This is `weekday_rule.convention: civil_day_overlap` -- the convention
    chosen in Step 3 by reproducing 13 source tables under four competing
    readings, where overlap scored 74/75 against 51 for prevailing-at-sunrise.
    It is applied here unchanged, per location, because the same evidence
    governs both layers.

    The `year` filter is a SECOND cut, and not the one `Span.open_start` /
    `open_end` describe. Those mark where `Sky.span_start` ended the generated
    period; this one drops days that fall outside the calendar year. A span can
    have a real, measured boundary and still be clipped here -- `year_clip`
    is the field that says so.
    """
    return [d for d in days_touched(span, loc_key) if d.year == year]


def year_clip(span: Span, loc_key: str, year: int) -> tuple[bool, bool]:
    """Whether `civil_days` dropped days off the start / end of this span.

    THE DISTINCTION `open_start` / `open_end` DO NOT MAKE, and one a daily
    render never needed. Under a daily render the out-of-year days simply have
    no rows and nothing is claimed about them. A collapsed row asserts an
    extent, and then the two cuts have to be told apart:

    * `open_start` true -- the condition was ALREADY RUNNING when the generated
      period began. There is no boundary; `Sky.span_start` is where we started
      looking.
    * `clipped_start` true with `open_start` false -- the boundary is REAL and
      MEASURED, and it falls outside the year. `b009_mercury_combust_cycle`
      starts `2026-12-13T18:30:00Z`: Mercury genuinely went combust that day,
      and the calendar's first row for it is 01-Jan-2027.

    A collapsed row that prints the true boundary starts before the file does;
    one that prints the first day in view asserts a boundary the sky did not
    supply. Emitting one of the two and choosing silently is the wrong-answer-
    that-renders-plausibly shape, so both are emitted and this flag says which
    is which.
    """
    touched = days_touched(span, loc_key)
    in_view = [d for d in touched if d.year == year]
    if not in_view:
        return False, False
    return touched[0] < in_view[0], touched[-1] > in_view[-1]


def last_day_held(span: Span, loc_key: str, year: int) -> dt.date | None:
    """The last civil day of `year` at `loc_key` the condition holds. Inclusive.

    THE DISPLAYED END OF A WINDOW, and the counterpart of `Span.end`, which is
    the exclusive instant the condition ceases. `timezones.span_dates` is what a
    renderer calls; this is where the date comes from. See `SpanDates` for why
    the two representations are given different types rather than a convention.
    """
    days = civil_days(span, loc_key, year)
    return days[-1] if days else None


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
    # `date_only` because the endpoints ARE the venue's midnights. Nothing
    # crossed at either of them; they are where the calendar turns over. A row
    # built from this span has a date and no instant, and the renderer is what
    # has to know that.
    return Span(lo, hi, None, precision="date_only")
