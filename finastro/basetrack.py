"""The base track: the sky's own events, rendered as calendar rows.

WHY THIS EXISTS, in the order the reasons were argued.

**Third and strongest: a calendar that cannot be empty cannot report absence.**
Until this module the calendar held verdict rows only, so a day with no row was
a day no rule fired -- and there was no way to tell that from a day nothing was
computed for. With the base track the empty days are *output*. Nothing the
astronomy layer tracks happened on them, and that is a measurement.

**Second: rejoinability.** Every row here carries the astronomy record's own
`id` and its `t_utc`, so a reader checking the calendar against the ephemeris
matches on a key rather than on an event name and a date.

**First: the sky is not a verdict, and the calendar showed only verdicts.** An
ingress is not a claim about gold. It carries no confidence, no tier and no
claim tag, and it is in the calendar because it happened.

THE DISCRIMINATOR CAME FIRST, AND THAT ORDERING IS THE POINT. `row_kind` was
added to every one of the 6,677 verdict rows in a separate commit, before a
single base-track row existed. Without it these 405 rows would have landed in a
file whose `records`, `by_tier` and `rows_without_verdict` counts all silently
changed denominator -- `no_rule` would have absorbed the base track, and every
meta figure would have gone on looking like the figure it used to be. That is
the stale-denominator failure this build has now recorded three times, and the
lesson from the first two is that the discriminator is a PRECONDITION for the
population it discriminates, never a follow-up.

**`BaseEvent` HAS NOWHERE TO PUT A VERDICT.** It is not a `Verdict` with the
interpretive fields left null: it has no `instrument`, no `tier`, no
`claim_tag`, no `construction`, no `verdict_text`, no `source_probability` and
no `confidence` field to set. A later renderer cannot give an ingress a market
opinion by forgetting a branch, because there is no attribute to assign. The
harness asserts the outcome as well, since a dict assembled downstream could
still add the key by hand.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .config import CONF
from .sky import Sky, parse

YEAR = CONF["year"]

_ROW_KINDS = CONF["row_kinds"]
_BASE = _ROW_KINDS["base_track"]

#: The ten core event classes, read from config rather than restated. The
#: panchang ingresses and the two horizon classes are excluded there, each with
#: its reason, so the scope of this track is a ruling on record and not a tuple
#: in a module.
CORE_CLASSES: tuple[str, ...] = tuple(_BASE["event_classes"])

#: Keys an event row must NOT carry. Asserted by the harness against the
#: RENDERED DICT, because `BaseEvent` already cannot hold them and the thing
#: left worth guarding is a dict assembled downstream.
FORBIDDEN_FIELDS = ("instrument", "instrument_label", "venue", "tier",
                    "claim_tag", "construction", "verdict_text",
                    "vedic_interpretation", "source_probability",
                    "source_probability_disputed", "confidence", "crude_path",
                    "interpretation_basis", "financial_theme")

#: An event row's `evidence_source`. `none` is the config's own value for "no
#: source verdict stands behind this", and it is the honest one here: none
#: does, because an ingress makes no claim. THE TIER IS NOT DERIVED FROM IT.
#: `tier_derivation` maps (none, null) to `no_rule`, and letting the base track
#: reach that mapping is exactly the absorption `row_kind` exists to prevent.
#: An event row's tier is null and is never computed.
EVIDENCE_SOURCE = "none"

#: Which contact of an eclipse a row names, and the key it is read from. A
#: solar record prints `begin`; a lunar record prints `penumbral_begin`,
#: because a lunar eclipse's first contact IS the penumbral one. Keyed per
#: family rather than taken as the earliest contact in the dict: picking by
#: time would quietly rename the contact the day a record carries a new one.
FIRST_CONTACT_KEY = {"eclipse/solar": "begin",
                     "eclipse/lunar": "penumbral_begin"}
MAX_CONTACT_KEY = "max"


@dataclass(frozen=True)
class BaseEvent:
    """One astronomy record, rendered as itself.

    Compare `verdicts.Verdict`, which is one rule, one instrument and one venue
    civil day. This is one record. It has no instrument because the sky has no
    instrument, and no tier because a tier grades how a VERDICT was built.
    """

    record_id: str
    event_class: str
    rule_family: str
    bodies: tuple[str, ...]
    kind: str                       # instant | window | civil_day
    civil_date: dt.date             # the IST civil date, off the record's stamp
    start_utc: dt.datetime
    end_utc: dt.datetime | None
    precision: str                  # exact | date_only, per sky.Span.precision
    #: The astronomy layer's own accuracy grade -- exact, minutes, hours,
    #: date_only. Kept beside `precision` because the two answer different
    #: questions: this one is HOW ACCURATE, that one is WHETHER AN INSTANT
    #: EXISTS AT ALL. A station good to the hour still has a moment; a combust
    #: window emitted as a date does not.
    record_precision: str
    label: str                      # display name, built from class and bodies
    astronomy: dict
    panchang: dict
    location: str | None
    data_certainty: str
    qa_flags: tuple[str, ...] = ()
    #: Eclipse rows only: (name, record_key, stamp) for first contact and for
    #: maximum. Empty for every other class.
    contacts: tuple = ()

    @property
    def is_instant(self) -> bool:
        return self.kind == "instant"

    #: Always False, and constants rather than fields on purpose. `open_start`
    #: and `open_end` mark a SPAN the generated period cut -- a state that was
    #: already running when the carry-in began. A record is not a state: it is
    #: the thing that happened, and it happened inside the span or it is not in
    #: the file. The renderer asks every row for these, so they are answered
    #: here rather than left for it to special-case by type.
    open_start = False
    open_end = False

    @property
    def has_instant_start(self) -> bool:
        """Whether this row may print ONE unlabelled clock time.

        The same question `Verdict.has_instant_start` answers, so the renderer
        has one branch and not two. False in two cases here:

        * `date_only` -- no instant exists;
        * an eclipse -- SEVERAL instants exist. The record carries begin,
          maximum, end and, for a central eclipse, the two totality contacts,
          every one of them fully stamped. A bare time on the row would be
          choosing one of five and not saying which, so the row names its
          contacts instead. That is the same rule as everywhere else in this
          build, pointing the other way: a row may not print a time it cannot
          identify.
        """
        return self.precision == "exact" and not self.contacts

    @property
    def no_instant_reason(self) -> str | None:
        """Why this row prints no single time, or None if it prints one."""
        if self.has_instant_start:
            return None
        return "named_contacts" if self.contacts else self.precision


# --------------------------------------------------------------- labelling

def _family_word(rule_family: str) -> str:
    """`lunation/full_moon` -> `Full Moon`."""
    return rule_family.split("/", 1)[-1].replace("_", " ").title()


def label_for(rec: dict) -> str:
    """A row's display name, built from the record and nothing else.

    NO INTERPRETATION ENTERS HERE. The label is the class, the bodies and where
    the record says they were: `Sun Mercury conjunction in Capricorn` is a
    restatement of the record, not a reading of it. An unhandled class raises
    rather than falling back to a generic string, so adding an eleventh class
    to the track is a decision somebody makes and not a row that appears.
    """
    cls, fam = rec["event_class"], rec["rule_family"]
    bodies = rec["bodies"]
    sign = (rec.get("astronomy") or {}).get("sign")
    joined = " ".join(bodies)

    if cls == "sign_ingress":
        return f"{joined} enters {sign}"
    if cls == "lunation":
        return _family_word(fam) + (f" in {sign}" if sign else "")
    if cls in ("conjunction", "opposition"):
        return f"{joined} {cls}" + (f" in {sign}" if sign else "")
    if cls == "apsis":
        return f"{joined} {_family_word(fam).lower()}"
    if cls == "station":
        # motion/station_D and motion/station_R, in the document's own words.
        turn = "direct" if fam.endswith("_D") else "retrograde"
        return f"{bodies[0]} turns {turn}" + (f" in {sign}" if sign else "")
    if cls == "combustion":
        # visibility/combust is asta, visibility/rise is udaya.
        return f"{bodies[0]} " + ("combust" if fam.endswith("combust")
                                  else "rises")
    if cls == "speed_crossing":
        # motion/fast_start, motion/fast_end
        return f"{bodies[0]} {_family_word(fam).lower()}"
    if cls == "eclipse":
        return ((rec.get("astronomy") or {}).get("eclipse_type")
                or f"{_family_word(fam)} eclipse")
    if cls == "total_day":
        return "Total Day"
    raise ValueError(
        f"no label form for event class {cls!r}. row_kinds.base_track names "
        "the ten classes this track renders; an eleventh is a decision, not a "
        "default")


# ------------------------------------------------------------------ contacts

def contacts_for(rec: dict) -> tuple:
    """(name, record_key, stamp) for an eclipse's first contact and maximum.

    RULED 15-Sep-2026. The record carries `contacts_global` fully stamped --
    three contacts for a penumbral lunar eclipse, five for a central solar one
    -- so a row emitting ONE UNLABELLED TIME has chosen one of several and not
    said which.

    What is emitted is first contact and maximum: the instant the event begins,
    and the instant the source's own eclipse material is stated about. The
    remaining contacts are neither dropped nor rendered. They stay on the
    record, which the row names by id.
    """
    cg = (rec.get("time") or {}).get("contacts_global") or {}
    fam = rec["rule_family"]
    first_key = FIRST_CONTACT_KEY.get(fam)
    if first_key is None:
        raise ValueError(
            f"eclipse record {rec['id']} has rule_family {fam!r}, which names "
            "no first contact. FIRST_CONTACT_KEY is per family on purpose: a "
            "lunar eclipse's first contact is penumbral and a solar one's is "
            "not, and taking the earliest key in the dict would silently "
            "rename the contact the day a record carries a new one")
    out = []
    for name, key in (("first_contact", first_key),
                      ("maximum", MAX_CONTACT_KEY)):
        stamp = cg.get(key)
        if stamp is None:
            raise ValueError(
                f"eclipse record {rec['id']} carries no {key!r} contact. "
                "row_kinds.eclipse_contacts requires both, and a missing one "
                "is a build error rather than a row with one time on it")
        out.append((name, key, stamp))
    return tuple(out)


# ------------------------------------------------------------------- build

def _ist_civil_date(rec: dict) -> dt.date | None:
    """The record's IST civil date, off its own start stamp.

    Read from the stamp the astronomy layer already computed rather than
    re-converted from the UTC instant here. Two conversions of one instant is
    two places for a timezone to be wrong.
    """
    st = (rec.get("time") or {}).get("start_stamp")
    if not st or not st.get("ist_date"):
        return None
    return dt.datetime.strptime(st["ist_date"], "%d-%b-%Y").date()


def build_base_events(sky: Sky | None = None,
                      year: int = YEAR) -> list[BaseEvent]:
    """Every core astronomy record whose IST civil date falls in `year`.

    The generated span runs 01-Dec-2026 -> 01-Feb-2028, so the carry-in and
    carry-out records are in the file and are not rendered: 472 core records
    exist, 405 fall in IST civil 2027. That is the same year convention every
    other layer uses, not a filter invented here.
    """
    sky = sky or Sky.load()
    out: list[BaseEvent] = []
    for rec in sky.records:
        if rec["event_class"] not in CORE_CLASSES:
            continue
        day = _ist_civil_date(rec)
        if day is None or day.year != year:
            continue
        t = rec["time"]
        out.append(BaseEvent(
            record_id=rec["id"],
            event_class=rec["event_class"],
            rule_family=rec["rule_family"],
            bodies=tuple(rec["bodies"]),
            kind=rec["kind"],
            civil_date=day,
            start_utc=parse(t["t_start_utc"]),
            end_utc=parse(t["t_end_utc"]) if t.get("t_end_utc") else None,
            precision=("date_only" if t["precision"] == "date_only"
                       else "exact"),
            record_precision=t["precision"],
            label=label_for(rec),
            astronomy=rec.get("astronomy") or {},
            panchang=rec.get("panchang") or {},
            location=rec.get("location"),
            data_certainty=rec["qa"]["data_certainty"],
            qa_flags=tuple(rec["qa"].get("flags") or ()),
            contacts=(contacts_for(rec) if rec["event_class"] == "eclipse"
                      else ()),
        ))
    out.sort(key=lambda e: (e.civil_date, e.start_utc, e.record_id))
    return out


def counts(events: list[BaseEvent]) -> dict:
    import collections
    return {
        "total": len(events),
        "by_event_class": dict(sorted(collections.Counter(
            e.event_class for e in events).items())),
        "by_precision": dict(sorted(collections.Counter(
            e.precision for e in events).items())),
        "by_data_certainty": dict(sorted(collections.Counter(
            e.data_certainty for e in events).items())),
    }
