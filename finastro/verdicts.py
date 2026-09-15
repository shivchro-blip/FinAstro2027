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
from .rules import CONFIG_REGISTRY, REGISTRY, firing_rules, fire
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
    #: The condition's other end. A verdict row has always been one rule on one
    #: civil day, so only `start_utc` was carried, and a row standing for a
    #: 220-day window looked exactly like a row standing for a 30-second ingress.
    end_utc: dt.datetime | None = None
    #: The generated period's cut, not the sky's. Carried onto the row because
    #: an open boundary is not an event and must not render as one.
    open_start: bool = False
    open_end: bool = False
    #: Whether the endpoints are instants at all. See `sky.Span.precision`.
    precision: str = "exact"

    @property
    def is_instant(self) -> bool:
        """True when start and end are the same computed moment."""
        return (self.precision == "exact" and not self.open_start
                and not self.open_end and self.start_utc == self.end_utc)

    @property
    def has_instant_start(self) -> bool:
        """Whether this row's start is a moment at which something crossed.

        The one question the renderer asks. False for a date-granular window,
        for a boundary the generated period cut, and for an anchor this build
        chose -- three different ways of not being an event, all three of which
        rendered as `00:00 IST` until 15-Sep-2026.
        """
        return self.precision == "exact" and not self.open_start

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
            "end_utc": (self.end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                        if self.end_utc else None),
            "open_start": self.open_start,
            "open_end": self.open_end,
            "precision": self.precision,
        }


#: The source's printed probability labels, and which rule each attaches to.
#:
#: `source_probability` is an ANNOTATION, not a computable column
#: (`not_a_confidence.no_derivation_in_either_direction`). It reaches only the
#: eleven `carried_families`, and where the source gave one rule two different
#: labels the family emits the SET and is flagged disputed
#: (`disputed_families.emit`). Nothing filters, weights or aggregates on it.
_CARRIED = CONF["source_probability"]["carried_families"]


#: rule id -> (labels, disputed), built once off the config's `rules` lists.
#:
#: THE ATTACHMENT IS BY RULE ID, AND ONLY BY RULE ID. It used to be by section
#: title -- `family` and `source_section` were matched as substrings of
#: `rule.section.title` -- and a section is not a rule. Three defects followed,
#: all of them silent:
#:
#: * every rule in "Venus Combust Rise Cycle p.14" took combust_venus's
#:   Reasonable, because combust_venus is listed before rise_venus and the title
#:   matched both. b015b_venus_rise_west was labelled Reasonable, and block 46's
#:   High -- rise_venus's only value -- reached NO row of the calendar;
#: * all three firing b041 Herschel partners took conj_venus_uranus's High,
#:   although block 23 is titled "Venus Herschel Conjunction" and labels the
#:   Venus partner alone. Two rules carried a judgement the source never made;
#: * cfg_silver_bearish_10_venus_rise_in_west, the one rule the old matcher
#:   reached by family+body rather than by title, held a label from a section it
#:   is not in.
#:
#: This is the family-read-two-ways bug in its third costume -- a key that
#: identifies a GROUP used to identify a MEMBER. Building the map eagerly is
#: part of the fix: a rule id claimed by two families fails on import rather
#: than silently taking whichever family the config happens to list first, which
#: is exactly how rise_venus lost its High to combust_venus.
def _label_index() -> dict[str, tuple[list | None, bool]]:
    index: dict[str, tuple[list | None, bool]] = {}
    for fam in _CARRIED:
        val = fam.get("value")
        labels = list(val) if isinstance(val, list) else ([val] if val else None)
        for rid in fam.get("rules") or ():
            if rid in index:
                raise ValueError(
                    f"source_probability: {rid} is claimed by two carried "
                    f"families; a rule carries at most one label")
            index[rid] = (labels, bool(fam.get("disputed")))
    return index


_LABEL_BY_RULE = _label_index()


def probability_for(rule) -> tuple[list | None, bool]:
    """(labels, disputed) for a rule, or (None, False) if it carries none.

    Read off `carried_families[].rules` by id. A rule with no label of its own
    gets none -- not its neighbour's, not its section's, not its family's.
    """
    return _LABEL_BY_RULE.get(rule.id, (None, False))


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
    if is_config_rule(rule):
        # The source printed this verdict under a named instrument's block, so
        # it is instrument-specific by the document's own arrangement rather
        # than by anything read here. Every configuration rule carries a
        # verdict -- `check_verdict` refuses a null one at registration -- so
        # this branch never reaches `condition_only`.
        return "instrument_specific"
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
    if is_config_rule(rule):
        return config_instruments_for(rule)
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


def is_config_rule(rule) -> bool:
    """True for one of the 58 instrument configuration groups.

    Read off `catalogue_b`, which a configuration group carries as None and a
    catalogue-B rule always carries as an int. Not a name test: an id prefix is
    a convention and this is an invariant the harness already asserts.
    """
    return rule.catalogue_b is None


def config_instruments_for(rule) -> list[str]:
    """The instruments a configuration group is addressed to.

    NOT through the rulership table, and that is the whole point of wiring these
    separately. A catalogue-B rule reaches an instrument because its BODIES
    resolve there -- a Venus rule reaches SUGAR because SUGAR's rulership is
    Venus, which is an inference this layer makes. A configuration group reaches
    gold because **the source printed it under "Gold - Bullish Configuration"**.
    The block says so; nothing is derived.

    So `cfg_gold_bullish_11_venus_in_rohini` reaches gold and not sugar, even
    though its body is Venus. Routing it through the rulership table would send
    the source's own gold statement to the wrong instrument and would be exactly
    the kind of inference `label_scheme_signoff` forbids.
    """
    return list(SECTOR_INSTRUMENTS.get(rule.section.block.instrument, []))


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
    # BOTH catalogues. Catalogue B's 141 sections and the 58 instrument
    # configuration groups are separate registries on purpose -- a group must
    # never reach `sections_ported()` and inflate "141 of 141" -- but they are
    # both the source's own conditions, and a calendar that fired one and not
    # the other was a calendar whose gold, silver and sugar rows came entirely
    # from generic rules whose bodies happened to resolve there.
    #
    # `fire()` serves both unchanged: a ConfigGroup carries `title`, `page`,
    # `heading` and `b = None`, which is every field `Rule` reads off a section.
    # Only the INSTRUMENT routing differs, and that is `config_instruments_for`.
    firings = fire(REGISTRY, sky) + fire(CONFIG_REGISTRY, sky)
    by_rule = {r.id: r for r in
               list(firing_rules()) + list(CONFIG_REGISTRY)}

    out: list[Verdict] = []
    for f in firings:
        rule = by_rule[f.rule_id]
        sig = significance_of(rule)
        labels, disputed = probability_for(rule)
        targets = instruments_for(rule)
        # tier_4 emits anyway, in its own words: "USDINR rows are still emitted
        # with verdict null, so the absence is VISIBLE in the output rather than
        # looking like a gap in the build." So USDINR joins every CATALOGUE-B
        # rule whose venue day it shares, and its rows can only ever be
        # verdict-null.
        #
        # CATALOGUE B ONLY, and the asymmetry is the point. A catalogue-B rule
        # is a general statement -- it names bodies, and `instruments_for` asks
        # the rulership table where those bodies land. USDINR is in the room for
        # that question and the answer is "no defensible rulership", so the null
        # row records a real absence: the rule was addressable to the whole
        # instrument set and did not reach this one.
        #
        # A configuration group was never addressable to USDINR. The source
        # printed it under "Gold -- Bullish Configuration"; the block names its
        # instrument and `config_instruments_for` reads that name rather than
        # resolving bodies. There is no question to which "USDINR: none" is the
        # answer, so the row records nothing -- it is noise wearing the shape of
        # visible absence, which is worse than silence because it reads as a
        # measured negative. The count this removes, and what the port is
        # worth once it is gone, are in build/CONFIG_PORT_REPORT.md under
        # "What the port is actually worth".
        if not is_config_rule(rule) and VENUE_OF["USDINR"] == f.location:
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
                flags=flags, detail=f.detail,
                start_utc=f.start_utc, end_utc=f.end_utc,
                open_start=f.open_start, open_end=f.open_end,
                precision=f.precision))
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
