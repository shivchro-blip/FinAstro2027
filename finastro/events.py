"""The canonical event record.

One event, one record, one place. Every renderer -- JSON, HTML, CSV -- reads
from here, so the same event cannot acquire two different times in two
different tables the way it did in the 2026 source.

The layers are kept strictly separate and are never merged into one field:

    identity   what the event is
    time       when it is, in UTC and in both display zones
    astronomy  measured quantities only
    panchang   the five limbs at the event instant
    location   which place the record was evaluated for, where that matters
    qa         how it was computed and how far it can be trusted

This module is Step 3 and is astronomy only. There is deliberately no field for
interpretation, market theme, verdict or confidence: those belong to Step 4 and
must not be able to leak in through this schema.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field, fields, replace
from typing import Any

from . import ephem, panchang as pn
from .config import CONF, YEAR
from .timezones import IST, stamp

UTC = dt.timezone.utc

# --------------------------------------------------------------------- span
# The generated span, carry-in and carry-out included, expressed in the primary
# zone because that is the zone the calendar is published in and converted to
# UTC once, here. It lives in the record layer rather than in the build script
# because the record layer needs it: a node's lord_relationship is anchored to
# a sign ingress that can sit in the carry-in, and the anchor search has to
# know how far back the carry-in reaches.
SPAN_START = dt.datetime(YEAR - 1, 12, 1, tzinfo=IST).astimezone(UTC)
SPAN_END = dt.datetime(YEAR + 1, 2, 1, tzinfo=IST).astimezone(UTC)


class _Unset:
    """Sentinel for an astronomy field that does not apply to this event class.

    Distinct from None. None means 'applies, and the value is deliberately
    null' -- a node's dignity, for instance, which config leaves unresolved.
    _UNSET means 'does not apply' and is dropped from the serialised record.
    """

    __slots__ = ()

    def __repr__(self) -> str:            # pragma: no cover - debug only
        return "UNSET"


UNSET: Any = _Unset()


#: Allowed values for EventRecord.kind.
KINDS = ("instant", "window", "civil_day")

#: Event classes whose value is a LOCATION PROPERTY rather than an instant in
#: the sky, and which therefore MUST carry a location.
#:
#: The distinction is the reason this constant exists instead of a comment. A
#: tithi or a yoga boundary is an angle between two longitudes reaching an exact
#: multiple: it happens once, everywhere at the same moment, and asking where it
#: was observed from is a category error. The Sun crossing a horizon is the
#: opposite -- it happens at one place, at a time no other place shares, and a
#: record of it without a location is not an under-specified Mumbai record. It
#: is not a record of anything. So the schema refuses it rather than defaulting
#: it, and `location=None` on one of these classes is a build error.
LOCATION_REQUIRED = ("sunrise", "sunset")

#: Allowed values for time precision, coarsest last.
PRECISIONS = ("exact", "minutes", "hours", "date_only")


# ------------------------------------------------------------------ identity

@dataclass(frozen=True)
class Identity:
    id: str
    event_class: str
    rule_family: str
    bodies: list[str]
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"bad kind {self.kind!r}")

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "event_class": self.event_class,
            "rule_family": self.rule_family,
            "bodies": list(self.bodies),
            "kind": self.kind,
        }


# ---------------------------------------------------------------------- time

@dataclass(frozen=True)
class TimeLayer:
    """UTC is the truth; the stamps are rendering.

    Both ends are stamped independently, never by adding a fixed offset to the
    start, so a window spanning the US DST switch shows two different Eastern
    offsets. Nothing here knows the 2027 switch dates.
    """

    t_start_utc: dt.datetime
    t_end_utc: dt.datetime | None
    precision: str
    #: Eclipse contact times. Global and local are held apart on purpose: an
    #: eclipse has one set of contacts for the Earth and a different set for
    #: any given observer, and merging them is how a document ends up quoting
    #: the wrong one. Empty for every other event class.
    contacts_global: dict | None = None
    contacts_local: dict | None = None

    def __post_init__(self) -> None:
        if self.precision not in PRECISIONS:
            raise ValueError(f"bad precision {self.precision!r}")
        for t in (self.t_start_utc, self.t_end_utc):
            if t is not None and t.tzinfo is None:
                raise ValueError("datetimes must be timezone-aware")

    def as_dict(self) -> dict:
        out = {
            "t_start_utc": _iso(self.t_start_utc),
            "t_end_utc": _iso(self.t_end_utc),
            "precision": self.precision,
            "start_stamp": stamp(self.t_start_utc).as_dict(),
            "end_stamp": (stamp(self.t_end_utc).as_dict()
                          if self.t_end_utc is not None else None),
        }
        if self.contacts_global is not None:
            out["contacts_global"] = stamp_map(self.contacts_global)
        if self.contacts_local is not None:
            out["contacts_local"] = stamp_map(self.contacts_local)
        return out


def stamp_map(d: dict) -> dict:
    """Dual-stamp every datetime in a flat dict, pass everything else through.

    Contact times get the same IST-primary / Eastern-secondary treatment as the
    record's own ends, and each is converted independently, so a contact on the
    far side of a DST switch carries its own Eastern offset.
    """
    return {k: (stamp(v).as_dict() if isinstance(v, dt.datetime) else v)
            for k, v in d.items()}


def _iso(t: dt.datetime | None) -> str | None:
    return None if t is None else t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------- astronomy

@dataclass(frozen=True)
class Astronomy:
    """Measured quantities. Populate only what applies to the event class;
    everything left UNSET is dropped from the record rather than emitted as a
    null, so an absent field means 'not applicable' and an explicit null means
    'applicable but unresolved'."""

    sign: Any = UNSET
    sign_from: Any = UNSET
    sign_to: Any = UNSET
    lon_sid: Any = UNSET
    nakshatra: Any = UNSET
    nakshatra_from: Any = UNSET
    nakshatra_to: Any = UNSET
    pada: Any = UNSET
    navamsa: Any = UNSET
    navamsa_from: Any = UNSET
    navamsa_to: Any = UNSET
    # The two panchang divisions the layer emits an ingress series for. They
    # are angles BETWEEN the Moon and the Sun rather than positions of a body,
    # so they get their own from/to pair exactly as the nakshatra does, and for
    # the same reason: writing a tithi into sign_from would make a record of one
    # division claim to be a record of another. The value held after the
    # crossing lives in the panchang layer, which the ingress generators
    # override from the crossing index rather than sampling at the cusp.
    tithi_from: Any = UNSET             # 1..30
    tithi_to: Any = UNSET
    tithi_name_from: Any = UNSET
    tithi_name_to: Any = UNSET
    paksha_from: Any = UNSET            # Shukla | Krishna
    paksha_to: Any = UNSET
    yoga_from: Any = UNSET              # 1..27
    yoga_to: Any = UNSET
    yoga_name_from: Any = UNSET
    yoga_name_to: Any = UNSET
    motion: Any = UNSET                 # "direct" | "retrograde" | "stationary"
    speed_deg_day: Any = UNSET
    #: Speed-class crossing records only. The calibrated Fast/Normal level this
    #: crossing is of, and the interval of levels that also reproduce the
    #: source's printed boundaries. Both are carried ON THE RECORD rather than
    #: left to config, so the calibration is auditable from the output alone:
    #: a reader can see which number was used AND how much freedom it had.
    speed_threshold: Any = UNSET
    speed_threshold_interval: Any = UNSET   # [lo, hi]
    speed_crossing_kind: Any = UNSET       # "threshold" | "station"
    speed_crossing_direction: Any = UNSET  # "into_fast" | "out_of_fast" | ...
    latitude: Any = UNSET
    declination: Any = UNSET
    elongation: Any = UNSET
    distance: Any = UNSET
    dignity: Any = UNSET                # RASHI dignity: list of states, or null
    trine: Any = UNSET                  # rashi moolatrikona, folded into dignity
    navamsa_dignity: Any = UNSET        # D9 dignity, read off `navamsa`
    navamsa_trine: Any = UNSET          # D9 moolatrikona
    vargottama: Any = UNSET             # D1 sign == D9 sign. NOT a dignity.
    deep_exaltation_deg: Any = UNSET    # informational; never decides a label
    lord_relationship: Any = UNSET      # nodes only, in place of a dignity
    eclipse_type: Any = UNSET
    magnitude: Any = UNSET

    def as_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)
                if not isinstance(getattr(self, f.name), _Unset)}


# ------------------------------------------------------------------ panchang

@dataclass(frozen=True)
class PanchangLayer:
    tithi: int
    tithi_name: str
    paksha: str
    moon_nakshatra: str
    yoga: str
    karana: str

    @classmethod
    def at(cls, when: dt.datetime) -> "PanchangLayer":
        p = pn.at(when)
        return cls(tithi=p.tithi_num, tithi_name=p.tithi_name, paksha=p.paksha,
                   moon_nakshatra=p.nakshatra, yoga=p.yoga, karana=p.karana)

    def as_dict(self) -> dict:
        return {
            "tithi": self.tithi,
            "tithi_name": self.tithi_name,
            "paksha": self.paksha,
            "moon_nakshatra": self.moon_nakshatra,
            "yoga": self.yoga,
            "karana": self.karana,
        }


# ------------------------------------------------------------------------ qa

ENGINE = "finastro/step3-astronomy"

#: A computed exact, B definition-sensitive, C depends on something unevidenced.
CERTAINTIES = tuple(CONF["labels"]["data_certainty"])

#: The two independent grounds a C record can be on. Required on every C record
#: and forbidden on any other, which is the invariant `QA` enforces: a bare C
#: would tell a reader that something is wrong without telling them WHICH thing,
#: and the remedies differ -- an undocumented rule is looked for on the page, an
#: unevidenced parameter is waited for in another year.
CERTAINTY_GROUNDS = tuple(CONF["labels"]["data_certainty_grounds"])

GROUND_UNDOCUMENTED = "undocumented_source_rule"
GROUND_UNEVIDENCED = "parameter_not_constrained_by_evidence"


@dataclass(frozen=True)
class QA:
    ephemeris: str
    ayanamsha: str
    ayanamsha_deg: float
    node: str
    data_certainty: str
    precision_days: int | None = None
    source_2026_equivalent: str | None = None
    flags: list[str] = field(default_factory=list)
    #: Which ground the C grade rests on. None for A and B, where there is no
    #: ground to name because nothing is missing.
    certainty_ground: str | None = None
    engine: str = ENGINE

    def __post_init__(self) -> None:
        if self.data_certainty not in CERTAINTIES:
            raise ValueError(f"bad certainty {self.data_certainty!r}")
        if self.data_certainty == "C":
            if self.certainty_ground not in CERTAINTY_GROUNDS:
                raise ValueError(
                    f"a C record must name its ground, one of "
                    f"{list(CERTAINTY_GROUNDS)}; got "
                    f"{self.certainty_ground!r}. The two grounds have "
                    "different remedies and a bare C hides which applies.")
        elif self.certainty_ground is not None:
            raise ValueError(
                f"certainty {self.data_certainty} carries a ground "
                f"({self.certainty_ground!r}); only C has one, because only C "
                "has something missing")

    def as_dict(self) -> dict:
        out = {
            "engine": self.engine,
            "ephemeris": self.ephemeris,
            "ayanamsha": self.ayanamsha,
            "ayanamsha_deg": self.ayanamsha_deg,
            "node": self.node,
            "data_certainty": self.data_certainty,
            "precision_days": self.precision_days,
            "source_2026_equivalent": self.source_2026_equivalent,
            "flags": list(self.flags),
        }
        # Dropped when absent, which is the same rule the astronomy layer's own
        # fields follow: a null key would be a field on every record saying
        # "this does not apply", and it would also have rewritten all 4163
        # pre-existing records to add a key none of them can have a value for.
        if self.certainty_ground is not None:
            out["certainty_ground"] = self.certainty_ground
        return out


def qa_for(when: dt.datetime, certainty: str, *,
           precision_days: int | None = None,
           source_2026_equivalent: str | None = None,
           certainty_ground: str | None = None,
           flags: list[str] | None = None) -> QA:
    """QA block with the backend, ayanamsha and node type actually in force.

    These are read from the engine at call time rather than copied from config,
    so a record can never claim a backend or an ayanamsha that was not the one
    used to compute it.
    """
    return QA(
        ephemeris=ephem.init(),
        ayanamsha=CONF["ayanamsha"],
        ayanamsha_deg=round(ephem.ayanamsha(when), 6),
        node=CONF["node"],
        data_certainty=certainty,
        certainty_ground=certainty_ground,
        precision_days=precision_days,
        source_2026_equivalent=source_2026_equivalent,
        flags=list(flags or []),
    )


# --------------------------------------------------------------- the record

@dataclass(frozen=True)
class EventRecord:
    identity: Identity
    time: TimeLayer
    astronomy: Astronomy
    panchang: PanchangLayer
    qa: QA
    location: str | None = None

    def __post_init__(self) -> None:
        if self.identity.event_class in LOCATION_REQUIRED and not self.location:
            raise ValueError(
                f"{self.identity.id}: {self.identity.event_class} is a "
                "location property and carries no location. There is no "
                "default venue: a rise or a set belongs to one horizon, and "
                "the primary location is not a fallback for an unstated one.")

    @property
    def id(self) -> str:
        return self.identity.id

    @property
    def t_start_utc(self) -> dt.datetime:
        return self.time.t_start_utc

    @property
    def event_class(self) -> str:
        return self.identity.event_class

    def as_dict(self) -> dict:
        """Stable key order: identity, then time, astronomy, panchang,
        location, qa. Ordering is fixed in code, never left to a dict's
        insertion order at the call site."""
        out = self.identity.as_dict()
        out["time"] = self.time.as_dict()
        out["astronomy"] = self.astronomy.as_dict()
        out["panchang"] = self.panchang.as_dict()
        out["location"] = self.location
        out["qa"] = self.qa.as_dict()
        return out

    def sort_key(self) -> tuple[str, str]:
        return (_iso(self.time.t_start_utc), self.identity.id)


# ----------------------------------------------------------------- id minting

def make_id(event_class: str, bodies: list[str], when: dt.datetime,
            suffix: str | None = None) -> str:
    """Deterministic, collision-resistant, and readable in a diff.

    Built from the event class, the bodies and the UTC instant to the second,
    so regenerating the year produces byte-identical ids and a real change
    shows up as a changed id rather than a silently reordered file.
    """
    parts = [event_class, "-".join(b.lower() for b in bodies),
             _iso(when).replace("-", "").replace(":", "")]
    if suffix:
        parts.append(suffix)
    return ":".join(parts)


def build(event_class: str, rule_family: str, bodies: list[str], kind: str,
          t_start: dt.datetime, astronomy: Astronomy, qa: QA, *,
          t_end: dt.datetime | None = None, precision: str = "exact",
          location: str | None = None,
          id_suffix: str | None = None,
          contacts_global: dict | None = None,
          contacts_local: dict | None = None,
          panchang_override: dict | None = None) -> EventRecord:
    """Assemble a record, stamping the panchang at the event instant.

    `panchang_override` is the panchang layer's version of `sign_override`, and
    exists for the same reason. A tithi or yoga ingress record's instant IS the
    cusp, bisected and then rounded to the second, so a panchang sampled at it
    lands on the far side of the boundary about half the time -- and a tithi
    ingress record that reported the tithi it had just left would be wrong in
    the one field the record exists to carry. The crossing index is
    authoritative; the sample is not.
    """
    panchang = PanchangLayer.at(t_start)
    if panchang_override:
        panchang = replace(panchang, **panchang_override)
    return EventRecord(
        identity=Identity(
            id=make_id(event_class, bodies, t_start, id_suffix),
            event_class=event_class, rule_family=rule_family,
            bodies=list(bodies), kind=kind),
        time=TimeLayer(t_start_utc=t_start, t_end_utc=t_end,
                       precision=precision,
                       contacts_global=contacts_global,
                       contacts_local=contacts_local),
        astronomy=astronomy,
        panchang=panchang,
        qa=qa,
        location=location,
    )


# ------------------------------------------------------ positional astronomy

#: Bodies with no Parashari rulership, so no dignity of any kind.
NO_DIGNITY = ("Uranus", "Neptune", "Pluto")


def positional(when: dt.datetime, body: str, *,
               sign_from: str | None = None,
               sign_to: str | None = None,
               sign_override: str | None = None,
               navamsa_from: str | None = None,
               navamsa_to: str | None = None,
               navamsa_override: str | None = None,
               extra_flags: list[str] | None = None):
    """Full positional astronomy for one body at one instant.

    Returns the Astronomy block and any QA flags the position itself raises, so
    a dignity that corrects a 2026 source omission is auditable on the record
    rather than silently different.

    `sign_override` exists for ingress records. The instant is the cusp itself,
    so a sampled position can land a few milliarcseconds on either side of it;
    the crossing indices are authoritative about which sign was entered. The
    override sets the sign AND the dignity computed from it together, because
    letting them disagree is how a record ends up saying Venus entered Libra
    while reporting Virgo's debilitation.

    `navamsa_override` is the same contract one chart down. `sign` and `dignity`
    always name the RASHI chart; `navamsa` and `navamsa_dignity` always name the
    D9. They are genuinely different answers: across the whole of 2026 Saturn's
    rashi sign is Pisces, which is no dignity at all, while its D9 sign runs
    Cancer to Scorpio and takes Libra (exalted) and Capricorn (own) on the way --
    and it is the D9 labels the source prints.

    Both overrides exist because of the same fact: a sign cusp is always also a
    navamsa cusp, so at either kind of ingress a sampled position can land on the
    far side of BOTH boundaries at once. An ingress caller therefore overrides
    both frames from its crossing index, not just the one it is a record of;
    otherwise `vargottama` -- the equality of the two -- is decided by which side
    of a milliarcsecond the sample fell on.

    `navamsa_dignity` is emitted only where `navamsa_to` says the record is a
    record of a D9 crossing. Overriding the navamsa sign on a rashi ingress fixes
    the frame; it does not make that record a D9 record.
    """
    p = ephem.position(when, body)
    sign = sign_override or p.sign
    navamsa = navamsa_override or p.navamsa
    flags = list(extra_flags or [])

    astro: dict[str, Any] = {
        "sign": sign,
        "lon_sid": round(p.lon, 6),
        "nakshatra": p.nakshatra,
        "pada": p.pada,
        "navamsa": navamsa,
        # Not a dignity, and deliberately not inside the dignity list: the
        # source prints "Cancer (Exalted, Vargottam)" -- both states at once.
        # Computed wherever both frames are known, which is every position,
        # because vargottama is a property of a position and not of a D9
        # boundary crossing.
        "vargottama": ephem.vargottama(sign, navamsa),
        "motion": "retrograde" if p.retrograde else "direct",
        "speed_deg_day": round(p.speed, 6),
        "latitude": round(p.lat, 6),
        "declination": round(ephem.declination(when, body), 6),
    }
    # The nodes are a computed point, not a body. Swiss Ephemeris returns the
    # Earth-Moon distance for them, which would read as the node's distance and
    # mean nothing, so it is omitted rather than emitted misleadingly.
    if body not in ephem.NODES:
        astro["distance"] = round(p.dist, 9)
    if sign_from is not None:
        astro["sign_from"] = sign_from
    if sign_to is not None:
        astro["sign_to"] = sign_to
    if navamsa_from is not None:
        astro["navamsa_from"] = navamsa_from
    if navamsa_to is not None:
        astro["navamsa_to"] = navamsa_to
    if body != "Sun":
        astro["elongation"] = round(ephem.separation(when, body, "Sun"), 6)

    if body in ephem.NODES:
        # Config sets dignity.nodes.dignity to null and asks for the source's
        # Relationship column instead. The Taurus/Scorpio versus
        # Gemini/Sagittarius exaltation dispute is left unresolved on purpose.
        astro["dignity"] = None
        # Period-constant: evaluated at the node's sign ingress and held for
        # the whole period, so every record inside one period prints the same
        # value. Null with a flag where the period opened before the span.
        rel, anchor = ephem.lord_relationship(when, body, SPAN_START, SPAN_END)
        astro["lord_relationship"] = rel
        if anchor is None:
            flags.append(ephem.NO_ANCHOR_FLAG)
    elif body not in NO_DIGNITY:
        states = ephem.dignity_states(body, sign)
        astro["dignity"] = states
        astro["trine"] = ephem.is_trine(body, sign)
        astro["deep_exaltation_deg"] = ephem.deep_exaltation_deg(body)
        if states and ephem.corrects_source_omission(body, sign):
            flags.append("dignity_corrects_source_omission")

    # The D9 dignity is emitted only on records that are records of the D9, and
    # under its own name. Same scheme, same table, different chart: the states
    # are read off `navamsa`, never off `sign`.
    if navamsa_to is not None:
        if body in ephem.NODES:
            # Config gives the nodes no dignity in any chart, not merely in the
            # rashi. The null is stated rather than left as an absent key.
            astro["navamsa_dignity"] = None
        elif body not in NO_DIGNITY:
            nav_states = ephem.dignity_states(body, navamsa)
            astro["navamsa_dignity"] = nav_states
            astro["navamsa_trine"] = ephem.is_trine(body, navamsa)
            # The one omission config records -- Saturn in Libra -- is a row in
            # the D9 table, so the check belongs in the D9 frame. Checked
            # against the rashi sign it could never fire: Saturn's rashi never
            # reaches Libra in either year.
            if nav_states and ephem.corrects_source_omission(body, navamsa):
                flags.append("navamsa_dignity_corrects_source_omission")

    return Astronomy(**astro), flags
