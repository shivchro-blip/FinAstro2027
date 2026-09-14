"""The verdict layer: condition rows -> per-instrument verdict rows.

WHAT THIS DOES, and what it deliberately does not.

The condition layer emits ~3,500 dated rows saying WHEN a rule's condition holds,
per location. This layer turns each of those into a row per INSTRUMENT, on that
instrument's venue civil day, carrying the two canonical axes
(`evidence_source`, `construction`), the derived `tier`, a claim tag and a
confidence. It is the coverage model in `verdict_coverage` applied.

IT AUTHORS NO VERDICT. The rule layer's own module docstring says a verdict
record is blocked on `open_questions.label_scheme_signoff`, and that entry is
still open in the config. The instruction this layer was built against resolves
that question for this layer only, and in the most conservative direction
available: **verdict text is either ported verbatim from the source or absent.**
Nothing here infers Bullish or Bearish from a rulership. A row whose rule states
a condition and no inference carries `verdict_text = None`, which per
`verdict_coverage.axes.construction.null_is_a_value` is a real member of the value
set and not a gap.

Three consequences worth stating because they are visible in the counts:

* `construction` is `printed` for the 85 rules that print a verdict and `None`
  for the 86 that do not. There is no `derived` verdict anywhere, because a
  derived verdict would be one we authored.
* A printed verdict that the section itself SCOPES ("specifically in sectors
  ruled by Saturn") is carried verbatim but is NOT applied to instruments: the
  scope is prose, not a resolved instrument list, and turning it into one would
  be reading a sentence as a mapping. Rows carry a flag instead.
* Confidence is `untested` on every row. It is not derived from claim tag, from
  tier, from source_probability or from anything else, and no code path can raise
  it. That is `labels.confidence_default` and the one thing this layer must never
  become creative about.

`source_probability` is carried where the source printed a label, with disputed
families emitting the SET, per `source_probability.transfer_test`.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .config import CONF
from .rules import REGISTRY, firing_rules, fire
from .sky import Sky
from .timezones import civil_day_bounds

YEAR = CONF["year"]

#: The two canonical axes, read from config rather than restated.
_EV = CONF["verdict_coverage"]["emit"]["evidence_source_values"]
_CO = CONF["verdict_coverage"]["emit"]["construction_values"]
_TIERS = CONF["verdict_coverage"]["emit"]["tier_values"]
_CONFIDENCE_DEFAULT = CONF["labels"]["confidence_default"]

#: (evidence_source, construction, localized) -> tier. From
#: verdict_coverage.tier_derivation.rules, transcribed as a table because the
#: config states it as an ordered list of rules and this layer needs a lookup.
_TIER_RULES = CONF["verdict_coverage"]["tier_derivation"]["rules"]


def tier_for(evidence_source, construction, localized: bool):
    """The derived tier for an axes pair. Unmapped is an ERROR, not a default.

    `tier_derivation.unmapped_is_an_error` is explicit about this. Raising here
    is what stops a new rule shape from silently acquiring a tier nobody chose.
    """
    for r in _TIER_RULES:
        if r.get("evidence_source") != evidence_source:
            continue
        if r.get("construction", "MISSING") != construction:
            continue
        if "localized" in r and r["localized"] != localized:
            continue
        return r.get("tier")
    raise ValueError(
        f"no tier rule for ({evidence_source!r}, {construction!r}, "
        f"localized={localized}); verdict_coverage.tier_derivation says an "
        "unmapped pair is a build error, not a default")


#: Instruments whose venue civil day is Mumbai or New York, from config.
INSTRUMENTS = {i["code"]: i for i in CONF["instruments"]}
BY_VENUE = CONF["verdict_coverage"]["civil_day_by_venue"]["by_instrument"]
VENUE_OF = {code: loc for loc, codes in BY_VENUE.items() for code in codes}

#: The flag a verdict carries when the rule was authored against one civil day
#: and is evaluated against another.
AUTHORSHIP_FLAG = CONF["verdict_coverage"]["civil_day_by_venue"][
    "flag_on_every_affected_verdict"]
_AUTHORSHIP_INSTRUMENTS = set(
    CONF["verdict_coverage"]["civil_day_by_venue"]["changed_by_this_decision"])

#: Bodies each instrument's rulership resolves to, from the reconciled table.
#: `secondary` carries Venus for silver at secondary weight only (a settled
#: conflict) and both Crude paths are handled separately, not as a significator.
_SIG = CONF["rulership"]["table"]


def body_primary(bodies) -> set[str]:
    """The instruments a set of bodies governs, through the reconciled table."""
    out = set()
    for b in bodies:
        row = _SIG.get(b)
        if not row:
            continue
        out |= set(row.get("primary") or [])
        out |= set(row.get("also") or [])
    return out


#: Which instruments each resolvable sector maps to. Derived from the
#: instrument table: an instrument's sectors are named in its own definition
#: where config gives one, and the Indian equity indices are market-wide.
SECTOR_INSTRUMENTS = {
    "gold": ["MCXGOLD", "GC"],
    "silver": ["MCXSILVER", "SI"],
    # The rulership table spells it `sugar_and_soft_goods`, from book_ch15's
    # "sugar and soft/luxury goods". The first version looked for a plain
    # `sugar` key and so resolved Venus to nothing for this sector. It does not
    # rescue SUGAR's row count -- SUGAR reaches nothing because no catalogue-B
    # rule conditions on it, see config's unported_configuration_sections -- but
    # the alias is correct and belongs here.
    "sugar_and_soft_goods": ["SUGAR"],
    "sugar": ["SUGAR"],
    "indian_equities": ["NIFTY", "BANKNIFTY"],
}

#: A rule that names NO body is a panchang or calendar rule -- a weekday, a
#: tithi, a yoga, an eclipse, a total day. `tier_1.evidence.indian_equities`
#: defines that population exactly: "The source's general verdicts -- the
#: weekday/panchang/transit rule families ... These are market-wide verdicts,
#: NOT instrument-specific ones." `tier_2.rule_families` is "identical to
#: tier_1.indian_equities -- no additions, no substitutions", on the New York
#: civil day.
#:
#: So a general verdict reaches the two Indian indices, and reaches SPX and NDX
#: through tier_2 -- which the config defines as "the SAME rule families as
#: Indian equities, evaluated on the New York civil day ... no additions, no
#: substitutions", with `localized: True` rendering the tier name `localized`.
#: That is the row which proves the axes pair alone cannot reproduce the tier,
#: and it is why `localized` is tracked separately here.
#:
#: It is deliberately NOT extended to COMEX gold, sugar or FX: those
#: instruments carry their own configuration sections (Gold pp.136-148, Silver
#: pp.149-167, Sugar pp.168-175), and a general market verdict applied to a
#: specific contract would be this layer's inference.
#: `narrative_layer.do_not_extend_to` is the same prohibition about a different
#: layer.
GENERAL_MARKET_INSTRUMENTS = ("NIFTY", "BANKNIFTY", "SPX", "NDX")

#: The flag each instrument carries when the rule was authored against one civil
#: day and is evaluated against another. Config gives two, about two different
#: mismatches, and they are now the two VALUES of `localized` rather than one
#: boolean plus a flag.
#:
#:   cross_market   the claim crosses a MARKET boundary -- an Indian-equities
#:                  rule applied to a US index. SPX, NDX.
#:   venue_shifted  the same instrument, same rule, same sky; only the venue's
#:                  midnight moved. GC, SI, CL.
AUTHORSHIP_FLAGS = {
    "GC": "authored_ist_evaluated_venue_day",
    "SI": "authored_ist_evaluated_venue_day",
    "CL": "authored_ist_evaluated_venue_day",
    "SPX": "source_authored_for_indian_equities",
    "NDX": "source_authored_for_indian_equities",
}

#: Which `localized` value each authored-elsewhere instrument carries. Two
#: situations, two values, one tier name each -- so a reader never sees the word
#: `localized` and has to guess whether the instrument or the clock moved.
LOCALIZED_KIND = {
    "SPX": "cross_market",
    "NDX": "cross_market",
    "GC": "venue_shifted",
    "SI": "venue_shifted",
    "CL": "venue_shifted",
}

#: ONE CONFLICT IN THE CONFIG, resolved the way config says to resolve it.
#:
#: `verdict_coverage.tiers.tier_1.instruments` lists MCXGOLD, GC, MCXSILVER and
#: SI together as source_backed. But `axes.localized` defines the property as
#: "Is the rule evaluated on a civil day other than its authored one?", and
#: `civil_day_by_venue.changed_by_this_decision` names GC, SI and CL as exactly
#: the instruments whose day boundary MOVED in that decision -- their rules are
#: IST-authored and now evaluated on the New York civil day.
#:
#: The tier_1 list predates that decision; the axes block is dated after it and
#: `axes.localized.set_by` points at `civil_day_by_venue`. So GC and SI emit
#: tier `localized` and MCXGOLD and MCXSILVER emit `source_backed`, for the same
#: rule text on the same sky. That asymmetry is the decision showing through, not
#: a bug -- and it is the reason `tier_derivation.authority` says the pair wins:
#: "Where a tier name and the pair disagree, the pair is right and the tier name
#: is the lossy rendering." Reported in build/STEP4_DECISIONS.md section 12.13.


@dataclass
class Verdict:
    """One rule, one instrument, one venue civil day."""

    rule_id: str
    instrument: str
    venue: str
    civil_date: dt.date
    evidence_source: str
    construction: str | None
    tier: str | None
    claim_tag: str | None
    confidence: str
    verdict_text: str | None
    significance: str
    provenance: str
    source_probability: list | None = None
    source_probability_disputed: bool = False
    #: Which of Crude's two unresolved paths spoke, for CL rows only. None for
    #: every other instrument.
    crude_path: str | None = None
    flags: list = field(default_factory=list)
    detail: object = None
    start_utc: dt.datetime | None = None

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "instrument": self.instrument,
            "venue": self.venue,
            "civil_date": self.civil_date.strftime("%d-%b-%Y"),
            "evidence_source": self.evidence_source,
            "construction": self.construction,
            "tier": self.tier,
            "claim_tag": self.claim_tag,
            "confidence": self.confidence,
            "verdict_text": self.verdict_text,
            "significance": self.significance,
            "provenance": self.provenance,
            "source_probability": self.source_probability,
            "source_probability_disputed": self.source_probability_disputed,
            "crude_path": self.crude_path,
            "flags": list(self.flags),
            "detail": self.detail,
            "start_utc": (self.start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                          if self.start_utc else None),
        }


#: The source's printed probability labels, and which rule each attaches to.
#:
#: `source_probability` is an ANNOTATION, not a computable column
#: (`not_a_confidence.no_derivation_in_either_direction`). It reaches only the
#: eleven `carried_families`, and where the source gave one rule two different
#: labels the family emits the SET and is flagged disputed
#: (`disputed_families.emit`). Nothing filters, weights or aggregates on it.
_CARRIED = CONF["source_probability"]["carried_families"]


def probability_for(rule) -> tuple[list | None, bool]:
    """(labels, disputed) for a rule, or (None, False) if it carries none.

    A family attaches either by `rule_family` (optionally further keyed on the
    body) or by the source section it was read from. Both are read off the rule;
    nothing is re-derived from the label text.
    """
    for fam in _CARRIED:
        hit = False
        key = fam.get("family")
        if key:
            # `family` is READ TWO WAYS in the config and both are live: for the
            # aspect and visibility families it is the emitted `rule_family`
            # ("aspect/conjunction Sun-Mercury"), and for five others it is the
            # SOURCE SECTION as printed ("Mercury Venus Alone in Any Sign p.16",
            # "Mars Ahead of Jupiter in Same Sign p.69"). Matching only the
            # first silently dropped 5 of the 11 carried families, which is the
            # kind of miss the label census exists to prevent.
            if rule.rule_family == key:
                hit = True
            else:
                want = str(key).split(" p.")[0].strip().lower()
                hit = bool(want) and want in rule.section.title.lower()
            if hit and fam.get("body") is not None:
                hit = fam["body"] in (rule.condition_text or "") or \
                    fam["body"] in rule.section.heading
        if not hit and fam.get("source_section"):
            want = str(fam["source_section"]).split(" p.")[0].strip()
            hit = bool(want) and want.lower() in rule.section.title.lower()
        if hit:
            val = fam.get("value")
            labels = list(val) if isinstance(val, list) else ([val] if val else None)
            return labels, bool(fam.get("disputed"))
    return None, False


def significance_of(rule) -> str:
    """How a condition may be applied, which is NOT a verdict.

    `instrument_specific` means the source printed the verdict for a named
    instrument; `sector_scoped` means the printed verdict names a rulership in
    prose but no instrument; `market_wide` means the rule's own section is a
    general verdict over Indian equities; `condition_only` means no inference is
    printed at all.
    """
    if rule.verdict_text is None:
        return "condition_only"
    low = rule.verdict_text.lower()
    if any(w in low for w in ("sectors ruled by", "sector ruled by")):
        return "sector_scoped"
    return "market_wide"


def instruments_for(rule) -> list[str]:
    """Which instruments a rule's condition is addressable to.

    NOT all of them, and getting this wrong is what made the first run emit
    17,880 `no_rule` rows. A verdict row says "this condition is addressed to
    this instrument on this day"; a rule that conditions on Saturn has nothing to
    say about Nasdaq, and emitting a null row for it would bury the calendar in
    rows that are true of nothing.

    Two cases:

    * the rule names BODIES -- then the instruments are those the reconciled
      rulership resolves those bodies to, with Crude's two contested paths
      handled by their own entries rather than through the table;
    * the rule names NO bodies -- it is a panchang or calendar rule (weekday,
      tithi, yoga, eclipse, total-day) and it is a statement about the market
      day itself, so it is addressable to every instrument. This is the tier_1
      "indian_equities" family and tier_2, which the config describes as "ALL
      eleven classes".

    `condition_only` rules are NOT excluded by this: a rule that prints no
    inference still has an addressable set, and the row is how the calendar
    shows the condition.
    """
    bodies = _bodies_of(rule)
    if not bodies:
        # A general market verdict: the two Indian indices. See
        # GENERAL_MARKET_INSTRUMENTS for why this is not all eleven.
        return list(GENERAL_MARKET_INSTRUMENTS)
    out = set()
    for b in bodies:
        for key, path in CRUDE_PATHS.items():
            if b == path["significator"]:
                out.add(key)
        row = _SIG.get(b)
        if not row:
            continue
        for sector in (list(row.get("primary") or [])
                       + list(row.get("also") or [])):
            out |= set(SECTOR_INSTRUMENTS.get(sector, []))
    # A body whose rulership resolves to no instrument we carry (Mercury ->
    # IT/telecom, Mars -> base metals) leaves the set empty, and an empty set is
    # NOT the same as "market-wide": it means no instrument in this project
    # responds to that body. Emitting nothing is the correct outcome, and the
    # caller records the absence rather than widening it to all eleven.
    return sorted(out)


def _bodies_of(rule) -> list[str]:
    """The bodies a rule's condition is about.

    Read from the rule's declared `inputs` where they name a body, which is the
    field the rule layer already uses for this, falling back to the section's own
    text. Deliberately shallow: a rule whose bodies cannot be read is treated as
    market-wide rather than silently narrowed.
    """
    from .ephem import NAKSHATRAS, SIGNS
    found = []
    hay = " ".join([rule.condition_text or "", rule.section.title or ""])
    for b in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
              "Rahu", "Ketu", "Uranus", "Herschel", "Neptune", "Pluto"):
        if b in hay:
            found.append("Uranus" if b == "Herschel" else b)
    return found


#: Crude's two deliberately unresolved paths, from config. Each is its own
#: "instrument" key in the output so a consumer sees which significator spoke.
CRUDE_PATHS = {
    p["id"]: p
    for p in CONF["verdict_coverage"]["tiers"]["tier_3"]["derivations"]["CL"]["paths"]
}
CRUDE_FLAG = CONF["verdict_coverage"]["tiers"]["tier_3"]["derivations"]["CL"][
    "flag_on_every_cl_verdict"]


def verdict_for(rule, instrument: str, loc: str, path: str | None = None):
    """(evidence_source, construction, tier, claim_tag, verdict_text) for a row."""
    if instrument == "USDINR":
        # tier_4. No defensible rulership exists, so no verdict is produced --
        # and the row is emitted anyway so the absence is visible.
        return ("none", None, "no_rule", None, None)
    construction = "printed" if rule.verdict_text else None
    evidence = "source" if rule.verdict_text else "none"
    # `localized` is an EVALUATION property, not a third axis:
    # verdict_coverage.axes.localized.is_an_axis is False. It is no longer a
    # boolean but one of two situations, because folding them together put two
    # different facts under one word: a claim crossing a MARKET boundary
    # (cross_market) and the same instrument on a different venue's civil day
    # (venue_shifted).
    localized = LOCALIZED_KIND.get(instrument, False)
    tier = tier_for(evidence, construction, localized)
    return (evidence, construction, tier, rule.claim_tag, rule.verdict_text)


def build_verdicts(sky: Sky | None = None) -> list[Verdict]:
    sky = sky or Sky.load()
    firings = fire(REGISTRY, sky)
    by_rule = {r.id: r for r in firing_rules()}

    # The source's own printed labels, where a rule carries them. Read from the
    # rule, not re-derived: source_probability is an annotation, never a weight.
    labels = CONF.get("source_probability", {})
    fam_map = labels.get("families", {}) if isinstance(labels, dict) else {}

    out: list[Verdict] = []
    for f in firings:
        rule = by_rule[f.rule_id]
        sig = significance_of(rule)
        labels, disputed = probability_for(rule)
        targets = instruments_for(rule)
        # tier_4 emits anyway, in its own words: "USDINR rows are still emitted
        # with verdict null, so the absence is VISIBLE in the output rather than
        # looking like a gap in the build." So USDINR joins every rule whose
        # venue day it shares, and its rows can only ever be verdict-null.
        if VENUE_OF["USDINR"] == f.location:
            targets = list(targets) + ["USDINR"]
        for inst in targets:
            # Crude's two paths emit as `CL` with a `path` naming which
            # significator spoke, rather than as two instruments: they are two
            # readings of ONE contract, and putting them under one instrument is
            # what keeps `primary: null` honest. The path rides in `flags` and in
            # the detail so a consumer can always tell them apart.
            if inst in CRUDE_PATHS:
                ticker, path = "CL", inst
                loc_needed = "new_york"
            else:
                ticker, path = inst, None
                loc_needed = VENUE_OF[inst]
            if loc_needed != f.location:
                continue
            ev, co, tier, tag, text = verdict_for(rule, ticker, f.location, path)
            if path is not None:
                ev = CRUDE_PATHS[path]["axes"]["evidence_source"]
                co = CRUDE_PATHS[path]["axes"]["construction"]
                tier = tier_for(ev, co, LOCALIZED_KIND.get("CL", False))
                tag = CRUDE_PATHS[path]["claim_tag"]
            flags = list(dict.fromkeys(list(rule.flags) + list(f.flags)))
            if path is not None:
                flags.append(CRUDE_FLAG)
                flags.append(f"crude_path={path}")
                flags.append("crude_paths_are_disjoint_in_2027_no_per_event_comparison")
                flags.append("eight_rahu_events_cannot_settle_the_contest")
            if sig == "sector_scoped":
                flags.append("verdict_text_scopes_itself_to_a_rulership_in_prose")
            if ticker in AUTHORSHIP_FLAGS:
                flags.append(AUTHORSHIP_FLAGS[ticker])
            if ticker == "USDINR":
                flags.append("no_defensible_rulership")
            out.append(Verdict(
                rule_id=rule.id, instrument=ticker,
                venue=INSTRUMENTS[ticker]["venue"],
                civil_date=f.civil_date,
                evidence_source=ev, construction=co, tier=tier,
                claim_tag=tag, confidence=_CONFIDENCE_DEFAULT,
                verdict_text=text, significance=sig,
                provenance=rule.section.heading,
                source_probability=labels,
                source_probability_disputed=disputed,
                crude_path=path,
                flags=flags, detail=f.detail, start_utc=f.start_utc))
    out.sort(key=lambda v: (v.civil_date, v.instrument, v.rule_id))
    return out


def counts(verdicts: list[Verdict]) -> dict:
    import collections
    return {
        "total": len(verdicts),
        "by_instrument": dict(collections.Counter(
            v.instrument for v in verdicts)),
        "by_tier": dict(collections.Counter(
            v.tier for v in verdicts)),
        "with_verdict_text": sum(1 for v in verdicts if v.verdict_text),
        "with_null_verdict": sum(1 for v in verdicts if not v.verdict_text),
    }
