"""Sidereal ephemeris wrapper.

Everything astronomical in this project goes through here so that the ayanamsha,
node type and ephemeris backend are set in exactly one place.
"""
from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass

import swisseph as swe

from .config import CONF

UTC = dt.timezone.utc

SIDM = {
    "LAHIRI": swe.SIDM_LAHIRI,
    "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
    "RAMAN": swe.SIDM_RAMAN,
    "TRUE_CITRA": swe.SIDM_TRUE_CITRA,
}

BODIES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

_NAK_ARC = 360.0 / 27.0
_PADA_ARC = _NAK_ARC / 4.0

_INITIALISED = False


def init() -> str:
    """Configure Swiss Ephemeris. Returns the backend actually in use."""
    global _INITIALISED, _BACKEND
    if _INITIALISED:
        return _BACKEND
    swe.set_sid_mode(SIDM[CONF["ayanamsha"]])
    path = os.environ.get(CONF["ephemeris"]["se_ephe_path_env"])
    _BACKEND = "moshier"
    if path and os.path.isdir(path):
        swe.set_ephe_path(path)
        try:
            swe.calc_ut(swe.julday(2027, 1, 1), swe.SUN, swe.FLG_SWIEPH)
            _BACKEND = "swisseph_files"
        except swe.Error:
            pass
    _INITIALISED = True
    return _BACKEND


def backend_flag() -> int:
    return swe.FLG_SWIEPH if init() == "swisseph_files" else swe.FLG_MOSEPH


def node_body() -> int:
    return swe.MEAN_NODE if CONF["node"] == "mean" else swe.TRUE_NODE


def body_id(name: str) -> int:
    if name in ("Rahu", "Ketu"):
        return node_body()
    return BODIES[name]


# --------------------------------------------------------------- time helpers

def to_jd(when: dt.datetime) -> float:
    """UTC datetime -> Julian Day (UT)."""
    if when.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    u = when.astimezone(UTC)
    return swe.julday(u.year, u.month, u.day,
                      u.hour + u.minute / 60 + u.second / 3600 + u.microsecond / 3.6e9)


def from_jd(jd: float) -> dt.datetime:
    """Julian Day (UT) -> UTC datetime, rounded to the second."""
    y, m, d, h = swe.revjul(jd)
    base = dt.datetime(y, m, d, tzinfo=UTC)
    return (base + dt.timedelta(hours=h)).replace(microsecond=0) \
        if h % 1 == 0 else _round_second(base + dt.timedelta(hours=h))


def _round_second(t: dt.datetime) -> dt.datetime:
    if t.microsecond >= 500_000:
        t += dt.timedelta(seconds=1)
    return t.replace(microsecond=0)


# ------------------------------------------------------------------ positions

@dataclass(frozen=True)
class Position:
    lon: float           # sidereal ecliptic longitude, degrees
    lat: float           # ecliptic latitude, degrees
    dist: float          # AU
    speed: float         # degrees per day in longitude
    body: str

    @property
    def sign_index(self) -> int:
        return int(self.lon // 30)

    @property
    def sign(self) -> str:
        return SIGNS[self.sign_index]

    @property
    def deg_in_sign(self) -> float:
        return self.lon % 30

    @property
    def nakshatra_index(self) -> int:
        return int(self.lon // _NAK_ARC)

    @property
    def nakshatra(self) -> str:
        return NAKSHATRAS[self.nakshatra_index]

    @property
    def pada(self) -> int:
        return int((self.lon % _NAK_ARC) // _PADA_ARC) + 1

    @property
    def navamsa_index(self) -> int:
        return int(self.lon // (30 / 9)) % 12

    @property
    def navamsa(self) -> str:
        return SIGNS[self.navamsa_index]

    @property
    def retrograde(self) -> bool:
        return self.speed < 0


def position(when: dt.datetime, body: str, sidereal: bool = True) -> Position:
    jd = to_jd(when)
    flags = backend_flag() | swe.FLG_SPEED | (swe.FLG_SIDEREAL if sidereal else 0)
    if body == "Ketu":
        vals = swe.calc_ut(jd, node_body(), flags)[0]
        return Position((vals[0] + 180) % 360, -vals[1], vals[2], vals[3], "Ketu")
    vals = swe.calc_ut(jd, body_id(body), flags)[0]
    return Position(vals[0] % 360, vals[1], vals[2], vals[3], body)


def longitude(when: dt.datetime, body: str, sidereal: bool = True) -> float:
    return position(when, body, sidereal).lon


def ayanamsha(when: dt.datetime) -> float:
    init()
    return swe.get_ayanamsa_ut(to_jd(when))


# ------------------------------------------------------------- root finding

def _bisect(fn, lo: dt.datetime, hi: dt.datetime, iters: int = 60) -> dt.datetime:
    f_lo = fn(lo) < 0
    for _ in range(iters):
        mid = lo + (hi - lo) / 2
        if (fn(mid) < 0) == f_lo:
            lo = mid
        else:
            hi = mid
    return _round_second(lo + (hi - lo) / 2)


def find_crossings(fn, start: dt.datetime, end: dt.datetime,
                   step: dt.timedelta, max_jump: float = 90.0):
    """Yield instants where a signed, wrapped function crosses zero."""
    t = start
    prev = fn(t)
    while t < end:
        nxt = t + step
        cur = fn(nxt)
        if (prev < 0) != (cur < 0) and abs(prev - cur) < max_jump:
            yield _bisect(fn, t, nxt)
        t, prev = nxt, cur


def _wrap(x: float) -> float:
    return ((x + 180) % 360) - 180


_SCAN_STEP = {"Moon": dt.timedelta(minutes=30)}


def scan_step(body: str, arc: float) -> dt.timedelta:
    """Step small enough that no arc can be skipped between samples."""
    if body in _SCAN_STEP:
        return min(_SCAN_STEP[body], dt.timedelta(hours=arc / 15.0))
    return dt.timedelta(hours=min(6.0, arc * 4))


def ingresses(body: str, start: dt.datetime, end: dt.datetime, arc: float = 30.0):
    """Sign (arc=30), nakshatra (arc=360/27) or navamsa (arc=30/9) changes.

    Returns (instant, from_index, to_index). Handles retrograde re-entry, so a
    planet that stations back across a cusp produces one record per crossing.
    """
    step = scan_step(body, arc)
    n = int(round(360 / arc))
    out = []
    t = start
    prev_idx = int(longitude(t, body) // arc)
    while t < end:
        nxt = min(t + step, end)
        idx = int(longitude(nxt, body) // arc)
        if idx != prev_idx:
            forward = (idx - prev_idx) % n == 1
            boundary = ((idx if forward else prev_idx) * arc) % 360
            inst = _bisect(lambda x: _wrap(longitude(x, body) - boundary), t, nxt)
            out.append((inst, prev_idx, idx))
            prev_idx = idx
        t = nxt
    return out


# ------------------------------------------------------------- vargottama
# D1 == D9. Not a dignity and never folded into one: the 2026 source prints it
# ALONGSIDE a dignity -- "Cancer (Exalted, Vargottam)" -- not instead of one.
#
# The two frames have to be read off the same longitude or the answer is noise.
# At an ingress the sampled position sits a few milliarcseconds either side of
# the cusp, so the helpers below derive the other frame from the crossing index
# instead of from a sample. A sign cusp is always also a navamsa cusp (30 is a
# whole multiple of 30/9), which is exactly why a sampled navamsa at a sign
# ingress can land in the previous sign's last navamsa.


def vargottama(sign: str, navamsa: str) -> bool:
    """True where the rashi and navamsa signs are the same."""
    return sign == navamsa


def sign_of_navamsa_index(idx: int) -> str:
    """Rashi sign containing global navamsa arc `idx` (0-107). Exact: each sign
    is nine whole navamsas, so the arc index determines the sign outright and no
    position needs to be sampled."""
    return SIGNS[(idx // 9) % 12]


def navamsa_at_sign_cusp(idx: int, forward: bool) -> str:
    """Navamsa occupied on the entered side of sign cusp `idx` (0-11).

    Entering forward the body is in the sign's FIRST navamsa; arriving backwards
    across the far cusp it is in the sign's LAST. Movable signs begin with their
    own navamsa, which is why a forward ingress into Aries, Cancer, Libra or
    Capricorn is vargottama from the instant of the cusp -- the 2026 source's
    Vargottam Mars row for Aries starts at exactly the Aries ingress.
    """
    return SIGNS[(idx * 9 + (0 if forward else 8)) % 12]


def stations(body: str, start: dt.datetime, end: dt.datetime):
    """Yield (instant, 'R'|'D') where longitudinal speed changes sign."""
    step = dt.timedelta(hours=6)
    out = []
    t = start
    prev = position(t, body).speed
    while t < end:
        nxt = min(t + step, end)
        cur = position(nxt, body).speed
        if (prev < 0) != (cur < 0):
            inst = _bisect(lambda x: position(x, body).speed, t, nxt)
            out.append((inst, "R" if prev > 0 else "D"))
        t, prev = nxt, cur
    return out


def separation(when: dt.datetime, a: str, b: str, sidereal: bool = True) -> float:
    """Signed longitudinal separation a - b, wrapped to (-180, 180]."""
    return _wrap(longitude(when, a, sidereal) - longitude(when, b, sidereal))


# --------------------------------------------------- panchang angle crossings
# A tithi is a 12-degree step of the Moon-Sun elongation and a yoga a 360/27
# step of their SUM. Both angles increase monotonically -- the Moon outruns the
# Sun at every point of its orbit, and both bodies always move direct in
# longitude -- so neither series can re-enter a division the way a planet does
# at a station, and the crossing search below has no retrograde case to handle.
#
# The two are NOT equally frame-free, and the difference is the whole reason
# they are separate functions rather than one parameterised by an arc:
#
#   elongation  Moon - Sun.  The ayanamsha subtracts from both and cancels.
#               A tithi boundary is the same instant in the sidereal and the
#               tropical frames, and no ayanamsha choice can move it. This is
#               the property the 2026 Bhadra section relies on when it says its
#               6-degree karana steps are "verified against Swiss Ephemeris".
#
#   sum         Moon + Sun.  The ayanamsha subtracts TWICE and cancels nothing.
#               A yoga boundary sits at sum_tropical - 2*ayanamsha, so a
#               different ayanamsha moves it by twice that difference divided by
#               the sum's rate -- about 3 hours between Lahiri and KP. The yoga
#               series is therefore exactly as ayanamsha-dependent as a sign
#               ingress is, and rests on the same evidence: config's Lahiri,
#               chosen in Step 3 because it alone reproduces the source.

ARC_TITHI = 12.0
ARC_YOGA = 360.0 / 27.0

#: Step for the two panchang angle scans. The shortest tithi is about 19h50m
#: (elongation rate peaks near 14.4 deg/day) and the shortest yoga about 19h30m,
#: so a 2-hour step cannot skip a division.
PANCHANG_STEP = dt.timedelta(hours=2)


def elongation_angle(when: dt.datetime) -> float:
    """Moon - Sun, 0..360. Frame-free: the ayanamsha cancels."""
    return (longitude(when, "Moon") - longitude(when, "Sun")) % 360.0


def sum_angle(when: dt.datetime) -> float:
    """Moon + Sun, 0..360, in the SIDEREAL frame config names.

    Not frame-free. See the note above: the ayanamsha enters twice.
    """
    return (longitude(when, "Moon") + longitude(when, "Sun")) % 360.0


def angle_ingresses(angle_fn, start: dt.datetime, end: dt.datetime, arc: float,
                    step: dt.timedelta = PANCHANG_STEP):
    """Crossings of exact multiples of `arc` by a monotonically rising angle.

    Returns (instant, from_index, to_index), the same shape `ingresses` returns,
    so the two series can be consumed by one caller. The boundary is bisected to
    the second exactly as a sign cusp is -- this is the method the 2026 Bhadra
    section states for its own windows, applied to a different multiple of the
    same angle.
    """
    n = int(round(360.0 / arc))
    out = []
    t = start
    prev_idx = int(angle_fn(t) // arc)
    while t < end:
        nxt = min(t + step, end)
        idx = int(angle_fn(nxt) // arc)
        if idx != prev_idx:
            # Monotone by construction, so a changed index is always a forward
            # crossing into `idx` and the boundary is `idx`'s own lower edge.
            boundary = (idx * arc) % 360.0
            inst = _bisect(lambda x: _wrap(angle_fn(x) - boundary), t, nxt)
            out.append((inst, prev_idx, idx))
            prev_idx = idx
        t = nxt
    return out


def tithi_ingresses(start: dt.datetime, end: dt.datetime):
    """Every tithi boundary in [start, end). 30 per lunation."""
    return angle_ingresses(elongation_angle, start, end, ARC_TITHI)


def yoga_ingresses(start: dt.datetime, end: dt.datetime):
    """Every yoga boundary in [start, end). 27 per 360 degrees of the sum."""
    return angle_ingresses(sum_angle, start, end, ARC_YOGA)


def aspect_exact(a: str, b: str, angle: float,
                 start: dt.datetime, end: dt.datetime):
    """Instants where a and b are exactly `angle` degrees apart."""
    step = dt.timedelta(hours=12)
    fn = lambda t: _wrap(separation(t, a, b) - angle)
    return list(find_crossings(fn, start, end, step))


# ------------------------------------------------------------------ eclipses

def solar_eclipses(start: dt.datetime, end: dt.datetime):
    init()
    out, jd, jd_end = [], to_jd(start), to_jd(end)
    while True:
        res = swe.sol_eclipse_when_glob(jd, backend_flag())
        peak = res[1][0]
        if peak > jd_end:
            return out
        kind = res[0]
        label = ("Total" if kind & swe.ECL_TOTAL else
                 "Annular" if kind & swe.ECL_ANNULAR else
                 "Hybrid" if kind & swe.ECL_ANNULAR_TOTAL else "Partial")
        out.append({"type": f"{label} solar", "max": from_jd(peak),
                    "begin": from_jd(res[1][2]) if res[1][2] else None,
                    "end": from_jd(res[1][3]) if res[1][3] else None})
        jd = peak + 1


def lunar_eclipses(start: dt.datetime, end: dt.datetime):
    init()
    out, jd, jd_end = [], to_jd(start), to_jd(end)
    while True:
        res = swe.lun_eclipse_when(jd, backend_flag())
        peak = res[1][0]
        if peak > jd_end:
            return out
        kind = res[0]
        label = ("Total" if kind & swe.ECL_TOTAL else
                 "Partial" if kind & swe.ECL_PARTIAL else "Penumbral")
        out.append({"type": f"{label} lunar", "max": from_jd(peak),
                    "penumbral": bool(label == "Penumbral")})
        jd = peak + 1


# ------------------------------------------------------------- declination

def declination(when: dt.datetime, body: str) -> float:
    """Apparent equatorial declination in degrees.

    Declination is independent of the ayanamsha, so this deliberately does not
    pass FLG_SIDEREAL: the sidereal flag rotates ecliptic longitude only.
    """
    jd = to_jd(when)
    flags = backend_flag() | swe.FLG_SPEED | swe.FLG_EQUATORIAL
    if body == "Ketu":
        vals = swe.calc_ut(jd, node_body(), flags)[0]
        return -vals[1]
    return swe.calc_ut(jd, body_id(body), flags)[0][1]


# ---------------------------------------------------------------- dignity
# Whole-sign Parashari dignity, driven entirely by config/conventions.yaml.
# Deliberately NOT degree-gated: the 2026 source labels Mercury in Virgo as
# Own + Trine + Exalted across the whole sign and never splits it at the
# exaltation degree, the moolatrikona span, or the own-sign remainder.

_DIG = CONF["dignity"]

#: Sign -> ruling planet, derived from the own-sign lists in config so the
#: rulership scheme lives in exactly one place.
SIGN_LORDS = {
    sign: body
    for body, spec in _DIG["signs"].items()
    for sign in spec["own"]
}

#: Sign-count distance -> the source's own relationship vocabulary.
SIGN_DISTANCE_ASPECTS = [
    "Conjunct", "Semi-Sextile", "Sextile", "Square",
    "Trine", "Quincunx", "Opposition",
]

NODES = ("Rahu", "Ketu")


def dignity_states(body: str, sign: str):
    """Applicable dignity states for a body in a sign, as a list.

    A sign can be own and trine and exalted at once (Mercury in Virgo), so the
    answer is a list, never a single value. Nodes return None: config sets
    dignity.nodes.dignity to null and the Taurus/Scorpio versus
    Gemini/Sagittarius exaltation dispute is left unresolved, not silently
    decided. Outer planets have no Parashari rulership and also return None.
    """
    if body in NODES:
        return None
    spec = _DIG["signs"].get(body)
    if spec is None:
        return None
    states = []
    if sign in spec["own"]:
        states.append("own")
    if sign in spec["trine"]:
        states.append("trine")
    if sign == spec["exalted"]:
        states.append("exalted")
    if sign == spec["debilitated"]:
        states.append("debilitated")
    return states


def is_trine(body: str, sign: str):
    """Moolatrikona flag, exposed separately as well as inside the state list."""
    if body in NODES or body not in _DIG["signs"]:
        return None
    return sign in _DIG["signs"][body]["trine"]


def deep_exaltation_deg(body: str):
    """Degree of deepest exaltation. Informational only, never used to decide a
    dignity label, which is whole-sign."""
    return _DIG["exaltation_degrees"].get(body)


def corrects_source_omission(body: str, sign: str) -> bool:
    """True where the 2026 source left a dignity unlabelled that its own scheme
    implies, e.g. Saturn in Libra. We emit the dignity and flag the divergence
    so the correction is auditable instead of silent."""
    return any(body in note and sign in note
               for note in _DIG.get("source_omissions", []))


def sign_distance_aspect(sign_a: str, sign_b: str) -> str:
    """Angular relation between two signs, in the source's vocabulary."""
    d = abs(SIGNS.index(sign_a) - SIGNS.index(sign_b)) % 12
    return SIGN_DISTANCE_ASPECTS[min(d, 12 - d)]


#: Emitted alongside a null lord_relationship when the node's sign-period began
#: before the generated span, so no anchoring ingress can be found. We never
#: fall back to instant evaluation: that would print a different value for two
#: records of the same period.
NO_ANCHOR_FLAG = "no_anchor_ingress_in_span"

#: Node sign ingresses are the same list for every record in a span, so they
#: are scanned once per (node, span) and held.
_NODE_INGRESS_CACHE: dict = {}


def node_sign_ingresses(node: str, span_start: dt.datetime,
                        span_end: dt.datetime):
    """(instant, sign) for each of a node's sign changes inside the span.

    The sign is taken from the ingress's own destination index, never
    recomputed from the longitude at the instant. A retrograde node enters a
    sign at that sign's upper cusp, where the bisected longitude sits within
    an epsilon of the boundary and can round into the sign it just left.
    """
    key = (node, span_start, span_end)
    if key not in _NODE_INGRESS_CACHE:
        _NODE_INGRESS_CACHE[key] = [
            (inst, SIGNS[to])
            for inst, _frm, to in ingresses(node, span_start, span_end, 30.0)
        ]
    return _NODE_INGRESS_CACHE[key]


def node_anchor(when: dt.datetime, node: str, span_start: dt.datetime,
                span_end: dt.datetime):
    """The node's most recent sign ingress at or before `when`, or None.

    The search runs back into the carry-in. None means the current sign-period
    opened before the span did, and the period's value is not recoverable from
    inside it.
    """
    prior = [(t, sign) for t, sign in node_sign_ingresses(node, span_start, span_end)
             if t <= when]
    return prior[-1] if prior else None


def lord_relationship(when: dt.datetime, node: str, span_start: dt.datetime,
                      span_end: dt.datetime):
    """(relationship, anchor) for a node, in the source's Relationship column.

    PERIOD-CONSTANT, not instant-evaluated. The 2026 source prints exactly one
    Relationship value per node sign-period, so the pair is evaluated once at
    the instant the node entered its sign and held for the whole period. Two
    of the four source pairs have a luminary as dispositor and would otherwise
    vary within the period -- Ketu in Cancer spans 26 days over which the Moon
    crosses every sign, and the printed Square holds for only the first ~36
    hours of it, which is the ingress instant.

    See config/conventions.yaml: node_lord_relationship.
    """
    anchor = node_anchor(when, node, span_start, span_end)
    if anchor is None:
        return None, None
    inst, node_sign = anchor
    lord = SIGN_LORDS[node_sign]
    return sign_distance_aspect(node_sign, position(inst, lord).sign), inst


# --------------------------------------------------------------- lunations

#: Elongation of the Moon from the Sun, in degrees, for each lunar phase.
LUNATION_ANGLES = {
    "new_moon": 0.0,
    "first_quarter": 90.0,
    "full_moon": 180.0,
    "last_quarter": 270.0,
}


def lunations(start: dt.datetime, end: dt.datetime):
    """New moon, both quarters and full moon, sorted by time.

    The Moon-Sun elongation is a difference of longitudes, so the ayanamsha
    cancels and the instants are identical sidereal or tropical.
    """
    out = []
    step = dt.timedelta(hours=6)
    for phase, angle in LUNATION_ANGLES.items():
        fn = lambda t, a=angle: _wrap(separation(t, "Moon", "Sun") - a)
        out += [(t, phase) for t in find_crossings(fn, start, end, step)]
    return sorted(out)


# ----------------------------------------------------------------- apsides

def distance_extrema(body: str, start: dt.datetime, end: dt.datetime,
                     step: dt.timedelta, delta: dt.timedelta):
    """Yield (instant, 'min'|'max') where the body's distance turns over.

    Found as a sign change in a symmetric numerical derivative of the distance,
    then bisected on that derivative. Like a station this is a stationary
    point, so the distance is flat near the root and the instant is the loosely
    determined quantity. Callers set precision accordingly.
    """
    def deriv(t: dt.datetime) -> float:
        return position(t + delta, body).dist - position(t - delta, body).dist

    out = []
    t = start
    prev = deriv(t)
    while t < end:
        nxt = min(t + step, end)
        cur = deriv(nxt)
        if (prev < 0) != (cur < 0):
            out.append((_bisect(deriv, t, nxt), "max" if prev > 0 else "min"))
        t, prev = nxt, cur
    return out


def moon_apsides(start: dt.datetime, end: dt.datetime):
    """(instant, 'perigee'|'apogee') for the Moon."""
    return [(t, "perigee" if k == "min" else "apogee")
            for t, k in distance_extrema("Moon", start, end,
                                         dt.timedelta(hours=12),
                                         dt.timedelta(hours=1))]


def sun_apsides(start: dt.datetime, end: dt.datetime):
    """(instant, 'perihelion'|'aphelion') for the Sun, i.e. the Earth-Sun
    distance turning over."""
    return [(t, "perihelion" if k == "min" else "aphelion")
            for t, k in distance_extrema("Sun", start, end,
                                         dt.timedelta(days=1),
                                         dt.timedelta(hours=12))]


# ------------------------------------------------------- eclipses, detailed

def _jd_or_none(jd: float):
    return from_jd(jd) if jd else None


def _geopos(loc: dict):
    return (loc["lon"], loc["lat"], loc["alt"])


#: A local search returns the next eclipse VISIBLE from the position, which may
#: be a different eclipse entirely. Accept it as the same event only if its
#: maximum falls within this many days of the global maximum.
_SAME_ECLIPSE_DAYS = 1.0


def solar_eclipses_detailed(start: dt.datetime, end: dt.datetime, loc: dict):
    """Global contact times, magnitude, and local circumstances at `loc`.

    Global and local are kept in separate sub-dicts. An eclipse has one set of
    contact times for the Earth and a different set for any given observer, and
    merging the two is how a document ends up quoting the wrong one.
    """
    init()
    flag = backend_flag()
    out, jd, jd_end = [], to_jd(start), to_jd(end)
    while True:
        kind, tret = swe.sol_eclipse_when_glob(jd, flag)[:2]
        peak = tret[0]
        if peak > jd_end:
            return out
        label = ("Total" if kind & swe.ECL_TOTAL else
                 "Annular" if kind & swe.ECL_ANNULAR else
                 "Hybrid" if kind & swe.ECL_ANNULAR_TOTAL else "Partial")
        where = swe.sol_eclipse_where(peak, flag)
        central = where[1] if len(where) > 1 else None
        attr = where[2] if len(where) > 2 else None
        out.append({
            "type": f"{label} solar",
            "central": bool(kind & swe.ECL_CENTRAL),
            "global": {
                "max": from_jd(peak),
                "begin": _jd_or_none(tret[2]),
                "end": _jd_or_none(tret[3]),
                "totality_begin": _jd_or_none(tret[4]),
                "totality_end": _jd_or_none(tret[5]),
                "greatest_lon": round(central[0], 4) if central else None,
                "greatest_lat": round(central[1], 4) if central else None,
            },
            "local": _solar_local(peak, loc, flag),
            "magnitude": round(attr[8], 4) if attr else None,
        })
        jd = peak + 1


def _solar_local(peak_jd: float, loc: dict, flag: int) -> dict:
    """Circumstances of the eclipse peaking at `peak_jd` as seen from `loc`."""
    res = swe.sol_eclipse_when_loc(peak_jd - 2, _geopos(loc), flag)
    kind, tret, attr = res[0], res[1], res[2]
    if not kind or abs(tret[0] - peak_jd) > _SAME_ECLIPSE_DAYS:
        return {"visible": False}
    return {
        "visible": True,
        "max": from_jd(tret[0]),
        "first_contact": _jd_or_none(tret[1]),
        "second_contact": _jd_or_none(tret[2]),
        "third_contact": _jd_or_none(tret[3]),
        "fourth_contact": _jd_or_none(tret[4]),
        "magnitude": round(attr[8], 4),
        "obscuration": round(attr[2], 4),
        "sun_altitude": round(attr[6], 2),
    }


def lunar_eclipses_detailed(start: dt.datetime, end: dt.datetime, loc: dict):
    """Global contact times, umbral and penumbral magnitude, local visibility."""
    init()
    flag = backend_flag()
    out, jd, jd_end = [], to_jd(start), to_jd(end)
    while True:
        kind, tret = swe.lun_eclipse_when(jd, flag)[:2]
        peak = tret[0]
        if peak > jd_end:
            return out
        label = ("Total" if kind & swe.ECL_TOTAL else
                 "Partial" if kind & swe.ECL_PARTIAL else "Penumbral")
        attr = swe.lun_eclipse_how(peak, _geopos(loc), flag)[1]
        out.append({
            "type": f"{label} lunar",
            "penumbral": label == "Penumbral",
            "global": {
                "max": from_jd(peak),
                "penumbral_begin": _jd_or_none(tret[6]),
                "penumbral_end": _jd_or_none(tret[7]),
                "partial_begin": _jd_or_none(tret[2]),
                "partial_end": _jd_or_none(tret[3]),
                "totality_begin": _jd_or_none(tret[4]),
                "totality_end": _jd_or_none(tret[5]),
            },
            "local": _lunar_local(peak, loc, flag, attr),
            "magnitude": round(attr[1] if label == "Penumbral" else attr[0], 4),
            "umbral_magnitude": round(attr[0], 4),
            "penumbral_magnitude": round(attr[1], 4),
        })
        jd = peak + 1


def _lunar_local(peak_jd: float, loc: dict, flag: int, attr) -> dict:
    """A lunar eclipse is visible wherever the Moon is above the horizon, so
    local circumstances reduce to the Moon's altitude at maximum and the
    rise/set times that clip the visible portion."""
    res = swe.lun_eclipse_when_loc(peak_jd - 2, _geopos(loc), flag)
    kind, tret = res[0], res[1]
    if not kind or abs(tret[0] - peak_jd) > _SAME_ECLIPSE_DAYS:
        return {"visible": False, "moon_altitude_at_max": round(attr[6], 2)}
    return {
        "visible": True,
        "max": from_jd(tret[0]),
        "moonrise": _jd_or_none(tret[8]),
        "moonset": _jd_or_none(tret[9]),
        "moon_altitude_at_max": round(attr[6], 2),
    }
