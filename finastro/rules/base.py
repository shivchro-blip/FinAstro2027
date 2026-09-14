"""The rule record, the registry, and how a rule becomes dated rows.

A rule is not a verdict. It is a **condition** taken from one catalogue-B
section, plus the verdict that section prints if it prints one, plus the
provenance needed to check both. Nothing here invents a market inference: a
rule whose section states none fires with `verdict_text = None`, and that is a
correct outcome rather than a gap to fill.

Four things this module refuses to do, each because the alternative was worse:

* **It does not compute.** A rule's `fn` receives a `Sky` -- the timeline view
  over `build/astronomy_2027.json` -- and returns spans. It cannot reach the
  ephemeris, so a rule and the calendar cannot disagree about the sky.
* **It does not approximate.** A rule whose condition needs an input the
  astronomy layer does not carry is registered with `status="blocked"` and the
  missing input named. It stays in the registry, is counted, and emits nothing.
* **It does not pick a civil day.** Every executable rule is evaluated against
  both locations and emits separate rows, because
  `weekday_rule.evaluate_per_location` is true and the 2026 divergence is 103
  Mumbai dates against 119 New York with 90 shared. Which row an instrument
  reads is settled downstream by `verdict_coverage.civil_day_by_venue`.
* **It does not set a tier by hand.** `tier` is derived from the axes, per
  `verdict_coverage.tier_derivation`, which is now the canonical model.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Callable, Iterable

from ..config import CONF
from ..sky import Sky, Span, civil_days
from .catalogue import Section

YEAR = CONF["year"]

#: The locations every rule is evaluated at. Both are emitted always; the venue
#: map in verdict_coverage.civil_day_by_venue decides which one an instrument
#: reads, and neither is a default for the other.
LOCATIONS = ("mumbai", "new_york")

STATUS_EXECUTABLE = "executable"

#: The condition is well defined but the astronomy layer does not carry an
#: input it needs. The rule is registered, counted and emits nothing; the
#: missing input is named so the gap is a fact rather than an impression.
STATUS_BLOCKED = "blocked"

#: The SOURCE's wording admits more than one reading, and picking one would
#: manufacture a decision. Distinct from `blocked`, which is about our layer:
#: an ambiguous rule might be perfectly computable once the reading is settled.
#: Registered, counted, emits nothing, and reported for a ruling.
STATUS_AMBIGUOUS = "ambiguous"

#: The source's wording was ambiguous and the reading has been RULED ON, with
#: the evidence for it on record. Not folded into `executable`, and
#: deliberately a status of its own: part of the words the rule fires on are
#: ours. A resolved rule must carry the competing readings it was chosen
#: against (`ambiguity`), the evidence that chose it (`resolution`), the
#: readings that evidence rejected (`rejected_readings`), and a flag naming
#: what was supplied -- and every firing carries that flag, so a dated row can
#: never be read as a plain transcription of the page.
STATUS_RESOLVED = "resolved_ambiguity"

STATUSES = (STATUS_EXECUTABLE, STATUS_BLOCKED, STATUS_AMBIGUOUS,
            STATUS_RESOLVED)

#: The statuses that produce dated rows. `blocked` and `ambiguous` are
#: registered and counted and emit nothing.
FIRING_STATUSES = (STATUS_EXECUTABLE, STATUS_RESOLVED)

# --------------------------------------------------------------- certainty
#: Certainty of each input a rule may declare, from `labels.data_certainty` and
#: the grades the astronomy layer already assigns its own records. A rule's
#: certainty is the WEAKEST of its inputs -- a rule is no more trustworthy than
#: the loosest quantity it conditions on.
INPUT_CERTAINTY = {
    # A -- computed exact, under a minute. Ingress instants and exact aspects.
    "ingress/sign": "A",
    "ingress/nakshatra": "A",
    "ingress/navamsa": "A",
    "aspect/conjunction": "A",
    "aspect/opposition": "A",
    "lunation": "A",
    "eclipse": "A",
    "calendar/total_day": "A",
    "panchang/tithi": "A",
    "panchang/yoga": "A",
    "panchang/karana": "A",
    "weekday": "A",
    # B -- computed but definition-sensitive, per config's own grading.
    # The horizon pair is the clearest case of what the grade means: a tithi
    # boundary is A because the twelve-degree step IS the definition, while a
    # rise depends on which part of the disc touches the horizon, on whether
    # refraction is applied and on the horizon's own height. Four conventions
    # swing a Mumbai sunrise by about four and a half minutes, so a rule
    # conditioned on one is no better than B however exactly it is computed.
    "horizon/sunrise": "B",
    "horizon/sunset": "B",
    "motion/station": "B",
    "visibility/combust": "B",
    "apsis": "B",
    # Shar -- B118 and B119. The quantity is exact; the INSTANT is not. The
    # astronomy layer emits latitude on every record but emits no ingress series
    # for it, so a zero-crossing is only known to lie in the gap between two
    # records. That is the same shape as a sunrise: computed exactly, and B
    # because the definition of the boundary is what is uncertain.
    "latitude": "B",
    # C -- depends on a source rule that was not recovered.
    "source_selection_rule": "C",
}
_ORDER = {"A": 0, "B": 1, "C": 2}


def certainty_of(inputs: Iterable[str]) -> str:
    grades = [INPUT_CERTAINTY[i] for i in inputs]
    if not grades:
        raise ValueError("a rule must declare at least one input")
    return max(grades, key=lambda g: _ORDER[g])


# -------------------------------------------------------------- claim tag
#: Wordings by which the source marks a statement as its own observation rather
#: than as a received rule. Applied to the VERBATIM verdict text, mechanically,
#: so the tag is a property of what the source wrote and not of who read it.
_OBSERVED_MARKERS = ("usually", "observation", "observed", "tends to",
                     "probable", "probability of", "may be seen",
                     "maybe seen", "expected to be")


def claim_tag_for(verdict_text: str | None) -> str | None:
    """`Observed` where the source hedges its own claim, else `Classical`.

    None where the section prints no verdict: an unstated claim has no tag, and
    defaulting one would assert a claim the source did not make.

    The test is mechanical and reads only the verbatim text, which is the point
    -- 141 sections tagged by hand would be 141 judgements no one could audit.
    A rule may override with `claim_tag=` and a stated reason.
    """
    if not verdict_text:
        return None
    low = verdict_text.lower()
    return "Observed" if any(m in low for m in _OBSERVED_MARKERS) \
        else "Classical"


# ------------------------------------------------------------------- rule

@dataclass(frozen=True)
class Rule:
    """One catalogue-B section, ported."""

    id: str
    section: Section
    rule_family: str
    condition_text: str                 #: verbatim, from the section
    condition_from: str                 #: which element it was read out of
    #: The extra case the section's verdict is restricted to, verbatim from the
    #: source, where the section states one. Kept as its own field and not
    #: glued onto `condition_text`, because the two are different strings on
    #: the page and the invariant that every condition is a substring of the
    #: document only survives if each is checked on its own. A proviso scopes a
    #: verdict, so a rule that states no verdict may not carry one.
    condition_proviso: str = ""
    inputs: tuple[str, ...] = ()
    verdict_text: str | None = None     #: verbatim, or None if none is printed
    verdict_from: str | None = None     #: "title" | "remark[0]" | "note[1]" ...
    evidence_source: str = "source"
    construction: str | None = None     #: set below, from the verdict
    claim_tag: str | None = None
    data_certainty: str | None = None
    status: str = STATUS_EXECUTABLE
    missing_inputs: tuple[str, ...] = ()
    ambiguity: str = ""                 #: the competing readings, both stated
    #: Why the ruling went the way it did -- one entry per independent piece of
    #: evidence, so a reader can re-check each separately instead of being
    #: handed a conclusion. Required on a resolved rule and forbidden without
    #: one: evidence with no ruling attached is a note, not a resolution.
    resolution: tuple[str, ...] = ()
    #: The readings the evidence ruled out, named. Kept because the value of a
    #: resolution is mostly in what it excluded, and that is the first thing
    #: lost when only the winner is recorded.
    rejected_readings: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    #: Civil weekdays the condition additionally requires, Monday=0. Empty
    #: means the condition is weekday-free.
    #:
    #: This is a field rather than part of `fn` because a weekday is a property
    #: of the civil day AT A LOCATION, and `fn` receives only a `Sky`, which is
    #: location-blind by construction. "Anuradha on Sunday" is one condition
    #: whose two halves live in different frames: the Moon's nakshatra is a
    #: fact about the sky, and Sunday is a fact about the calendar the venue
    #: keeps. Evaluating the second inside `fn` would force one calendar on
    #: both venues, which is exactly what `weekday_rule.evaluate_per_location`
    #: forbids -- and the 2027 lunar eclipse of 17-Aug is Tuesday in Mumbai and
    #: Tuesday in New York, while 21-Feb is Sunday in Mumbai and Saturday in
    #: New York.
    weekdays: tuple[int, ...] = ()
    #: True where the CONDITION ITSELF differs between venues, not merely the
    #: civil day it lands on. `fn` is then called once per location as
    #: `fn(sky, loc_key)` and sees only that venue's rows.
    #:
    #: This is a second, stronger thing than `weekdays`, and conflating them
    #: would lose the distinction that batch 3 spent its report making. A
    #: weekday rule has ONE sky-side condition and two calendars: "Anuradha on
    #: Sunday" asks the same question of the sky at both venues and only the
    #: answer's date differs. A sunrise rule has TWO conditions. Whether a
    #: tithi is Kshay -- whether any sunrise falls inside it -- is a different
    #: question in Mumbai and in New York, and can come out yes in one and no
    #: in the other with no calendar involved at all. `weekdays` cannot express
    #: that, because by the time `fire` applies a weekday the span has already
    #: been chosen.
    #:
    #: It is deliberately not the default. A location-blind `fn` is checked by
    #: the type system of its own signature: it cannot consult a venue, so it
    #: cannot quietly acquire one.
    per_location: bool = False
    notes: str = ""
    #: Locations this rule is evaluated at. Both by default. A rule narrows it
    #: only where the astronomy layer cannot support the other -- the combust
    #: family is date_only and measured at the primary location's horizon, so a
    #: venue-day rendering of it would be invention, not localisation.
    locations: tuple[str, ...] = LOCATIONS
    fn: Callable[[Sky], list[Span]] | None = None

    def __post_init__(self) -> None:
        # construction follows from whether the section PRINTS the verdict.
        # Nothing in catalogue B is derived: these are the source's own rules,
        # so the only two values reachable here are `printed` and null.
        if self.construction is None:
            object.__setattr__(
                self, "construction",
                "printed" if self.verdict_text else None)
        if self.claim_tag is None:
            object.__setattr__(self, "claim_tag",
                               claim_tag_for(self.verdict_text))
        if self.data_certainty is None and self.inputs:
            object.__setattr__(self, "data_certainty",
                               certainty_of(self.inputs))
        if self.status not in STATUSES:
            raise ValueError(f"{self.id}: bad status {self.status!r}")
        if self.status == STATUS_BLOCKED and not self.missing_inputs:
            raise ValueError(f"{self.id}: blocked without a named missing input")
        if self.status == STATUS_AMBIGUOUS and not self.ambiguity:
            raise ValueError(f"{self.id}: ambiguous without the readings stated")
        if self.status == STATUS_RESOLVED:
            # Each of the four is load-bearing. Without the readings the ruling
            # has no subject; without the evidence it is an assertion; without
            # the rejections the reader cannot see what was given up; without
            # the flag the firing looks like a transcription.
            if not self.ambiguity:
                raise ValueError(
                    f"{self.id}: resolved without the readings it resolved")
            if not self.resolution:
                raise ValueError(
                    f"{self.id}: resolved without the evidence that resolved it")
            if not self.rejected_readings:
                raise ValueError(
                    f"{self.id}: resolved without naming the readings rejected")
            if not self.flags:
                raise ValueError(
                    f"{self.id}: resolved without a flag naming what we supplied")
        if self.resolution and self.status != STATUS_RESOLVED:
            raise ValueError(
                f"{self.id}: carries resolution evidence but is "
                f"{self.status!r}; evidence with no ruling is a note")
        if any(w not in range(7) for w in self.weekdays):
            raise ValueError(f"{self.id}: weekdays outside Monday=0..Sunday=6")
        # A horizon input is a statement about one venue's sky. A rule that
        # declares one and is not evaluated per location would be computing a
        # single answer from a single horizon and printing it against both
        # venues -- which is `weekday_rule.evaluate_per_location` broken in the
        # one place it is hardest to notice, because the row would still carry
        # a location field naming the venue it was never evaluated at.
        horizon = [i for i in self.inputs if i.startswith("horizon/")]
        if horizon and not self.per_location:
            raise ValueError(
                f"{self.id}: declares {horizon} but is not per_location; a "
                "rise or a set belongs to one venue and cannot be evaluated "
                "once for both")
        if self.status in FIRING_STATUSES and self.fn is None:
            raise ValueError(f"{self.id}: {self.status} without a condition")
        if self.verdict_text is not None and self.verdict_from is None:
            raise ValueError(f"{self.id}: verdict without an attribution")
        if self.condition_proviso and self.verdict_text is None:
            raise ValueError(
                f"{self.id}: carries a proviso but states no verdict; "
                "a proviso restricts a verdict and has nothing to restrict")

    # ------------------------------------------------------------ metadata
    @property
    def section_title(self) -> str:
        return self.section.title

    @property
    def section_page(self) -> str:
        return self.section.page

    @property
    def catalogue_b(self) -> int:
        return self.section.b

    @property
    def tier(self) -> str | None:
        """Derived, never set by hand. See verdict_coverage.tier_derivation.

        A rule that prints no verdict has no tier: the tier names classify a
        VERDICT, and there is none to classify. That is not `no_rule`, which
        means no defensible rulership exists -- here the rule exists and fires.
        """
        if self.construction is None:
            return None
        if self.evidence_source == "source" and self.construction == "printed":
            return "source_backed"          # localized=false; tier_2 for NY
        raise ValueError(f"{self.id}: no tier rule for "
                         f"({self.evidence_source}, {self.construction})")

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_family": self.rule_family,
            "catalogue_b": self.catalogue_b,
            "section_title": self.section_title,
            "section_page": self.section_page,
            "section_heading": self.section.heading,
            "condition_text": self.condition_text,
            "condition_from": self.condition_from,
            "condition_proviso": self.condition_proviso,
            "verdict_text": self.verdict_text,
            "verdict_from": self.verdict_from,
            "evidence_source": self.evidence_source,
            "construction": self.construction,
            "tier": self.tier,
            "claim_tag": self.claim_tag,
            "data_certainty": self.data_certainty,
            "status": self.status,
            "missing_inputs": list(self.missing_inputs),
            "ambiguity": self.ambiguity,
            "resolution": list(self.resolution),
            "rejected_readings": list(self.rejected_readings),
            "inputs": list(self.inputs),
            "flags": list(self.flags),
            "weekdays": list(self.weekdays),
            "per_location": self.per_location,
            "locations": list(self.locations),
            "notes": self.notes,
        }


# ---------------------------------------------------------------- firings

@dataclass(frozen=True)
class Firing:
    """One rule, one location, one civil day."""

    rule_id: str
    location: str
    civil_date: dt.date
    start_utc: dt.datetime
    end_utc: dt.datetime
    detail: object = None
    open_start: bool = False
    open_end: bool = False
    #: Copied off the rule at fire time rather than left to a lookup. A row
    #: travels further than the registry does, and the flag that says a
    #: nakshatra name was supplied editorially is worth nothing if reading it
    #: requires already knowing to go and ask.
    flags: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "location": self.location,
            "civil_date": self.civil_date.strftime("%d-%b-%Y"),
            "flags": list(self.flags),
            "start_utc": self.start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_utc": self.end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "detail": self.detail,
            "open_start": self.open_start,
            "open_end": self.open_end,
        }


# --------------------------------------------------------------- registry

REGISTRY: list[Rule] = []
_SEEN: set[str] = set()


def register(rule_obj: Rule) -> Rule:
    if rule_obj.id in _SEEN:
        raise ValueError(f"duplicate rule id {rule_obj.id}")
    _SEEN.add(rule_obj.id)
    REGISTRY.append(rule_obj)
    return rule_obj


def rule(**kw):
    """Decorate a condition function into a registered executable rule."""
    def wrap(fn):
        register(Rule(fn=fn, **kw))
        return fn
    return wrap


def blocked(**kw) -> Rule:
    """Register a rule whose condition the astronomy layer cannot supply."""
    return register(Rule(status=STATUS_BLOCKED, **kw))


def ambiguous(**kw) -> Rule:
    """Register a rule whose SOURCE wording admits more than one reading."""
    return register(Rule(status=STATUS_AMBIGUOUS, **kw))


def resolved(**kw):
    """Decorate a condition into a rule whose reading was ruled on.

    Takes a condition function like `rule`, because a resolved rule fires; the
    difference is what it is required to carry, which `__post_init__` enforces.
    """
    def wrap(fn):
        register(Rule(status=STATUS_RESOLVED, fn=fn, **kw))
        return fn
    return wrap


# -------------------------------------------------------------- evaluation

def fire(rules: list[Rule], sky: Sky, year: int = YEAR) -> list[Firing]:
    """Every (rule, location, civil day) the executable rules produce.

    The span-to-day step is `weekday_rule.convention: civil_day_overlap`,
    applied per location and never collapsed to one date column.
    """
    out: list[Firing] = []
    for r in rules:
        if r.status not in FIRING_STATUSES:
            continue
        # A location-blind condition is evaluated ONCE and the same spans are
        # dated at both venues. A per-location condition is evaluated per
        # venue, because the spans themselves differ -- and it is never given
        # the chance to be evaluated once and reused, which is the whole
        # guarantee.
        shared = None if r.per_location else r.fn(sky)
        for loc in r.locations:
            spans = r.fn(sky, loc) if r.per_location else shared
            for span in spans:
                for day in civil_days(span, loc, year):
                    # The weekday half of a condition is applied HERE, after
                    # the span has been resolved to a day at this location,
                    # because that is the only point at which a weekday exists.
                    if r.weekdays and day.weekday() not in r.weekdays:
                        continue
                    out.append(Firing(r.id, loc, day, span.start, span.end,
                                      span.value, span.open_start,
                                      span.open_end, r.flags))
    out.sort(key=lambda f: (f.civil_date, f.rule_id, f.location))
    return out


def counts_by_rule(firings: list[Firing]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for f in firings:
        out.setdefault(f.rule_id, {loc: 0 for loc in LOCATIONS})[f.location] += 1
    return out
