"""The instrument configuration blocks, ported -- gold, silver, sugar.

Fifty-eight named groups under six `<section id>` blocks. The scope survey in
`build/CONFIG_SECTIONS_SCOPE.md` classed 41 of them as needing no astronomy the
layer does not already emit; **38 are ported here and 20 are registered blocked
with the input each is missing named.** The three that moved from READY to
blocked under the work are reported in `notes` on their own rules, because a
scope estimate that turns out wrong is worth more stated than quietly absorbed.

THE ONE STRUCTURAL THING THIS PORT DOES DIFFERENTLY FROM CATALOGUE B
    A catalogue-B rule's verdict is sliced out of its own section. A
    configuration rule's verdict is sliced out of **two elements**: the block's
    `<h2>` states the direction, and the group's heading states the condition
    and sometimes sharpens the direction. *Silver -- Bullish Configuration* +
    *Venus Mars Together* is one statement in two halves, and a port that reads
    only the second produces a row with no verdict and no error.

    So `config_catalogue.check_verdict` runs at REGISTRATION, on every rule in
    this module, before any of them can fire. A rule under a directional block
    that carries a null verdict raises `SilentVerdict` and the import fails.
    The check was written before the first rule below, not after, because this
    defect's whole character is that it renders as a blank rather than as an
    error.

WHAT A CONFIGURATION RULE MAY NOT DO
    Everything `base.Rule` already forbids, unchanged: it may not compute, may
    not approximate, may not pick a civil day, and may not set a tier by hand.
    Two more, specific to here:

    * **It may not be counted as a catalogue-B section.** These rules live in
      `CONFIG_REGISTRY` and never in `REGISTRY`, and `ConfigGroup.b` is None,
      so `rules.sections_ported()` cannot be inflated by them.
    * **It may not type a word the document prints.** Every condition and every
      verdict below is a SLICE of the group heading, the block heading or the
      group body, and `_register` refuses anything that is not a substring of
      one of the three.

WHERE THE PORT DISAGREED WITH THE SCOPE SURVEY
    Three groups the survey called READY are blocked here, on evidence found
    while porting them:

    * `gold-bullish#6` *If Mars is Aspected by Saturn...* -- the survey called
      the aspect "already used by catalogue-B rules". The layer emits
      `aspect/conjunction` and `aspect/opposition` and nothing else, and the
      section's own printed row is Saturn in Pisces aspecting Mars in
      Sagittarius, which is the tenth-house graha drishti and neither of those.
      Blocked on `aspect_orbs`, the open config question whose text is exactly
      "graha drishti vs degree orbs" -- so still one of the five.
    * `silver-bullish#10` *Mercury or Jupiter Do Vedh of Venus* and
      `silver-bearish#6` *Mercury Venus or Moon Venus Mutual Vedh* -- both need
      a per-planet Vedha wheel that is not ported. Mercury's is (B133);
      Jupiter's has no speed doctrine at all (B135) and Venus's was withdrawn
      on a single-point fit (B134). That is a **sixth** missing input, not one
      of the survey's five, and it is reported as such rather than folded into
      the nearest existing one.

    One group moved the other way. `silver-bullish#11` *Mercury Combust and
    Retrograde Does Mutual Vedh with Moon* looked like it needed the Moon's own
    wheel, and does not: both of its printed rows resolve out of Mercury's
    wheel alone. It is ported as a `resolved_ambiguity` with that evidence.

Financial astrology is a speculative interpretive framework. Nothing here is
investment advice.
"""
from __future__ import annotations

from ..sky import Span, _weaker, intersect, parse, same, weekdays_in_span
from . import names
from .base import (FIRING_STATUSES, Firing, Rule, STATUS_BLOCKED,
                   STATUS_RESOLVED)
from .catalogue import split_final, split_statement
from .colocation import RESIDENCY_BODIES, _alone, _pada, _together
from .config_catalogue import G, GROUPS, assert_no_silent_verdicts, check_verdict
from .pairs import _both_retrograde
from .panchang_rules import _tithi_named
from .vedha import DIRECTION as VEDHA_DIRECTION, WHEELS
from .visibility import HORIZON_FLAG, MUMBAI_ONLY, _combust, _rise

# --------------------------------------------------------------- the registry
#: Separate from `base.REGISTRY` and deliberately so: these are not catalogue-B
#: sections and `rules.sections_ported()` must not be able to see them.
CONFIG_REGISTRY: list[Rule] = []
_SEEN: set[str] = set()

#: The five missing inputs the scope survey named, plus the sixth this port
#: found. Every blocked rule below cites one of these by key, so "blocked on
#: what" is a closed vocabulary and the per-input counts are countable off the
#: registry rather than parsed out of prose.
MISSING_INPUTS = {
    "valence": "a benefic/malefic classification of the bodies -- the source "
               "selects rows on 'malefic' or 'benefic' and never defines "
               "either. The same absence blocks B19, B116 and B117",
    "darshan": "a first-sighting (darshan / moonrise-as-sighting) computation. "
               "B62 is the same computation and is blocked; swe.heliacal_ut "
               "ran 9-10 days out against the source's own Venus rise dates",
    "no_dated_window": "nothing to port: the source prints a title and no "
                       "dated window, so there is no condition to register a "
                       "reproduction against",
    "month_system": "the lunar month system, amanta or purnimanta. The event "
                    "itself is emitted; NAMING its month is what is open. "
                    "`month_system_confirmation` in config, and B111",
    "aspect_orb": "the aspect doctrine -- graha drishti or a degree orb. "
                  "`aspect_orbs` in config. The layer emits conjunction and "
                  "opposition only, so a 3rd/10th-house aspect has no series",
    "vedha_wheel": "a per-planet Nakshtra Vedh wheel for the planet the group "
                   "names. Mercury's is ported (B133); Jupiter's has no speed "
                   "doctrine (B135) and Venus's was withdrawn on a "
                   "single-point fit (B134). NOT one of the five inputs the "
                   "scope survey named -- and NOT an input the document "
                   "withholds either. It is the downstream cost of a decision "
                   "WE made: STEP4_DECISIONS section 12.10 withdrew the Mars "
                   "and Venus wheels because each threshold was fitted to ONE "
                   "crossing and so could not fail. Both groups blocked here "
                   "would be portable today under the withdrawn thresholds -- "
                   "every one of silver-bearish#6's thirteen printed rows "
                   "resolves exactly through B134's Venus wheel -- so this "
                   "row states what that decision cost, and a year supplying "
                   "a second crossing is what lifts it",
}

#: The five the survey named, kept apart from the sixth so the report can say
#: which blocked groups the survey predicted and which it did not.
SURVEY_INPUTS = ("valence", "darshan", "no_dated_window", "month_system",
                 "aspect_orb")


def _register(r: Rule, group) -> Rule:
    """Register one configuration rule, after the checks that make it one.

    The verdict check is the load-bearing one and runs FIRST, so a rule that
    lost half its verdict statement never reaches the registry at all.
    """
    check_verdict(r.id, group, r.verdict_text, r.verdict_from)
    if r.id in _SEEN:
        raise ValueError(f"duplicate configuration rule id {r.id}")
    if not group.carries(r.condition_text):
        raise ValueError(
            f"{r.id}: condition {r.condition_text!r} is not a substring of "
            f"{group.key} or of its block heading; a condition is sliced from "
            "the document, never typed")
    if r.status == STATUS_BLOCKED:
        unknown = [k for k in r.missing_inputs if k not in MISSING_INPUTS]
        if unknown:
            raise ValueError(
                f"{r.id}: blocked on {unknown}, not in MISSING_INPUTS; the "
                "blocking vocabulary is closed so the per-input counts can be "
                "taken off the registry rather than read out of prose")
    _SEEN.add(r.id)
    CONFIG_REGISTRY.append(r)
    return r


def _rule(group, **kw):
    """Decorate a condition function into a registered configuration rule."""
    def wrap(fn):
        _register(Rule(section=group, fn=fn, **kw), group)
        return fn
    return wrap


def _resolved(group, **kw):
    """As `_rule`, for a reading we ruled on. `Rule` enforces what it carries."""
    def wrap(fn):
        _register(Rule(section=group, status=STATUS_RESOLVED, fn=fn, **kw),
                  group)
        return fn
    return wrap


def _blocked(group, **kw) -> Rule:
    return _register(Rule(section=group, status=STATUS_BLOCKED, **kw), group)


# ------------------------------------------------------------ slicing helpers
# Nothing below types a word the document prints. Each helper cuts the group's
# own heading at a marker the heading itself contains, so the result is a
# substring and `_register` can prove it.

def _at(text: str, marker: str) -> str:
    """The half of `text` before `marker`, marker excluded."""
    return text[:text.index(marker)].strip()


def _from(text: str, marker: str) -> str:
    """`text` from `marker` onward, marker INCLUDED.

    Used where the verdict begins with a word the heading runs on from --
    "Retrograde Mercury or Jupiter *Increases Volatility and Prices May Rise*"
    -- so the verdict keeps the word that makes it one.
    """
    return text[text.index(marker):].strip()


# ----------------------------------------------------------------- conditions
# Every one is built from series the astronomy layer already emits, and most
# are a catalogue-B helper called with different arguments.

def _join(spans: list[Span]) -> list[Span]:
    """Join spans that touch, collecting their values.

    `panchang_rules._join` and `pairs._join_touching` are the same function;
    this is the third caller and for the same reason they give -- a body
    crossing from one named sign or star into the next is ONE window, and
    emitting it twice would break `Firing`'s one row per rule, location and day.
    """
    out: list[Span] = []
    for s in sorted(spans, key=lambda x: x.start):
        if out and out[-1].end == s.start:
            prev = out.pop()
            vals = prev.value if isinstance(prev.value, tuple) else (prev.value,)
            out.append(Span(prev.start, s.end, vals + (s.value,),
                            prev.open_start, s.open_end))
        else:
            out.append(s)
    return out


def _union(*conditions):
    """The union of several conditions' spans, overlapping ones merged.

    `pairs._either`, needed here for the same reason: several of these groups
    state a disjunction over bodies -- "Saturn or Mercury in Gemini",
    "Retrograde Mercury or Jupiter" -- and the union is one window.
    """
    def fn(sky):
        merged: list[Span] = []
        for s in sorted((s for c in conditions for s in c(sky)),
                        key=lambda s: s.start):
            if merged and s.start <= merged[-1].end:
                prev = merged.pop()
                longer = s.end >= prev.end
                merged.append(Span(prev.start, max(prev.end, s.end), prev.value,
                                   prev.open_start,
                                   s.open_end if longer else prev.open_end))
            else:
                merged.append(s)
        return merged
    return fn


def _sign(body: str, *signs: str):
    """Spans where `body` occupies one of `signs`, touching spans joined."""
    wanted = {names.sign(s) for s in signs}

    def fn(sky):
        return _join([s for s in sky.spans(body, "sign") if s.value in wanted])
    return fn


def _star(body: str, *stars: str):
    """Spans where `body` occupies one of `stars`, touching spans joined."""
    wanted = {names.nakshatra(s) for s in stars}

    def fn(sky):
        return _join([s for s in sky.spans(body, "nakshatra")
                      if s.value in wanted])
    return fn


def _alone_in_sign(body: str, *signs: str):
    """Spans where `body` holds one of `signs` and no other residency body does.

    `colocation._alone` judges a PAIR alone together; this is the one-body case
    the silver-bearish groups state. The set judged against is batch 2's
    `RESIDENCY_BODIES`, imported rather than retyped, so "alone" cannot come to
    mean two different things in two modules. The Moon is not in that set --
    see the note on `cfg_silver_bearish_01`, where this group's own exception
    line disagrees with that and the disagreement is carried, not resolved.
    """
    wanted = {names.sign(s) for s in signs}
    others = [b for b in RESIDENCY_BODIES if b != body]

    def fn(sky):
        out = [s for s in sky.spans(body, "sign") if s.value in wanted]
        for o in others:
            out = intersect(out, list(sky.spans(o, "sign")),
                            lambda held, third: held if held != third else None)
        return _join(out)
    return fn


def _vargottama(body: str, *signs: str):
    """Spans where `body`'s sign and navamsa agree, optionally in `signs`.

    Vargottama IS that agreement -- `vargottam.engine_field` on every record is
    exactly `sign == navamsa` -- so it is the intersection of two emitted
    ingress series and needs no new quantity.
    """
    wanted = {names.sign(s) for s in signs} if signs else None

    def fn(sky):
        return intersect(list(sky.spans(body, "sign")),
                         list(sky.spans(body, "navamsa")),
                         lambda sg, nv: sg if sg == nv and (
                             wanted is None or sg in wanted) else None)
    return fn


def _pad(body: str, star: str, pad: int):
    """Spans where `body` is in the `pad`-th quarter of `star`, 1-based.

    The quarter comes from `colocation._pada`, which recovers it from the
    navamsa the record already carries. `pad` is 1-based because the source
    counts "the 4th Pad"; `_pada` is 0-based, and the conversion is here, once.
    """
    want = names.nakshatra(star)

    def fn(sky):
        return intersect(
            [s for s in sky.spans(body, "nakshatra") if s.value == want],
            list(sky.spans(body, "navamsa")),
            lambda nak, nav: {"nakshatra": nak, "navamsa": nav, "pada": pad}
            if _pada(nak, nav) == pad - 1 else None)
    return fn


def _instants(event_class: str, family: str | None = None,
              body: str | None = None, keep=None):
    """One zero-length span per matching record; `civil_days` does the rest."""
    def fn(sky):
        out = []
        for r in sky.class_records(event_class, family=family, body=body):
            if keep is not None and not keep(r):
                continue
            t = parse(r["time"]["t_start_utc"])
            out.append(Span(t, t, {"id": r["id"],
                                   "sign": r["astronomy"]["sign"],
                                   "nakshatra": r["astronomy"]["nakshatra"]}))
        return out
    return fn


def _sankranti(sign: str):
    """The Sun's ingress instants into `sign` -- that sign's Sankranti."""
    want = names.sign(sign)
    return _instants("sign_ingress", "ingress/sign", "Sun",
                     keep=lambda r: r["astronomy"]["sign_to"] == want)


def _sankranti_with_moon_in_the_same_sign():
    """Sankranti instants at which the Moon already holds the sign entered.

    One instant and two emitted series: the Sun's sign ingress, and the Moon's
    sign at that instant, which `Sky.value_at` reads off the Moon's own ingress
    series without sampling anything.
    """
    def fn(sky):
        out = []
        for r in sky.class_records("sign_ingress", "ingress/sign", "Sun"):
            t = parse(r["time"]["t_start_utc"])
            entered = r["astronomy"]["sign_to"]
            if sky.value_at("Moon", "sign", t) == entered:
                out.append(Span(t, t, {"sign": entered, "id": r["id"]}))
        return out
    return fn


def _retrograde(*bodies: str):
    """The union of the named bodies' retrograde windows."""
    def one(body):
        def fn(sky):
            return [s for s in sky.motion_spans(body)
                    if s.value == "retrograde"]
        return fn
    return _union(*(one(b) for b in bodies))


def _turns_direct(*bodies: str):
    """The station-direct instants of the named bodies."""
    def fn(sky):
        out = []
        for b in bodies:
            for r in sky.class_records("station", "motion/station_D", b):
                t = parse(r["time"]["t_start_utc"])
                out.append(Span(t, t, {"body": b, "id": r["id"]}))
        return sorted(out, key=lambda s: s.start)
    return fn


def _goes_combust_while_retrograde(body: str, instant: bool = True,
                                   signs: tuple[str, ...] = ()):
    """Combustion beginning inside a retrograde window.

    Two groups state this at two granularities: silver-bullish prints DATES
    ("Retrograde Mercury Once Goes Combust") and sugar-bullish prints a WINDOW
    ("Retrograde Mercury If Goes Combust in Cancer"). Both are the same
    intersection; `instant` chooses which of the two the row is.
    """
    wanted = {names.sign(s) for s in signs} if signs else None

    def fn(sky):
        retro = [s for s in sky.motion_spans(body) if s.value == "retrograde"]
        out: list[Span] = []
        for c in sky.combust_spans(body):
            for r in retro:
                if not (r.start <= c.start < r.end):
                    continue
                # The combust window's own precision travels onto every span
                # built from it. `combust_spans` is date_only -- kalamsha is a
                # horizon measurement and the record carries a date, not a
                # moment -- while the retrograde stretch it is intersected with
                # is exact, so `_weaker` picks the one that governs. Without
                # this the three rows of cfg_silver_bullish_17 printed
                # `00:00 IST` for a combustion the ephemeris never timed.
                if instant:
                    if wanted is not None and \
                            sky.value_at(body, "sign", c.start) not in wanted:
                        continue
                    out.append(Span(c.start, c.start, {"direction": c.value},
                                    precision=c.precision))
                    continue
                lo, hi = max(c.start, r.start), min(c.end, r.end)
                prec = _weaker(c.precision, r.precision)
                if wanted is None:
                    if lo < hi:
                        out.append(Span(lo, hi, {"direction": c.value},
                                        precision=prec))
                    continue
                for sg in sky.spans(body, "sign"):
                    if sg.value not in wanted:
                        continue
                    a, b = max(lo, sg.start), min(hi, sg.end)
                    if a < b:
                        out.append(Span(a, b, {"direction": c.value,
                                               "sign": sg.value},
                                       precision=_weaker(prec, sg.precision)))
        return sorted(out, key=lambda s: s.start)
    return fn


def _moon_joins_combust(body: str, direction: str):
    """Spans where the Moon holds the sign of a body combust in `direction`.

    "Joins" is read as the shared sign, and the source's own two rows decide
    that: both run a shade under and a shade over two days, which is a Moon
    sign transit and not a nakshatra (about one day) or a conjunction (an
    instant).
    """
    def fn(sky):
        return intersect(
            list(_combust(body, direction=direction)(sky)),
            intersect(list(sky.spans("Moon", "sign")),
                      list(sky.spans(body, "sign")), same),
            lambda d, sg: {"direction": d, "sign": sg})
    return fn


def _conjunction(a: str, b: str):
    """The exact conjunction instants of an unordered pair."""
    def fn(sky):
        return [Span(parse(r["time"]["t_start_utc"]),
                     parse(r["time"]["t_start_utc"]),
                     {"sign": r["astronomy"]["sign"], "bodies": r["bodies"]})
                for r in sky.aspect_instants("conjunction", a, b)]
    return fn


def _fortnights(sky, paksha: str) -> list[Span]:
    """Whole fortnights of one paksha, off the tithi boundary series alone.

    `panchang_rules._shukla_fortnights` generalised to either fortnight: a run
    of tithi spans carrying the paksha, required to open at Pratipada and close
    at that fortnight's last tithi, and dropped entirely if the generated
    period cut either end -- a fortnight missing some of its days cannot be
    asked how many days it holds, and answering anyway is how a count silently
    becomes an undercount.
    """
    last = {"Shukla": "Purnima", "Krishna": "Amavasya"}[paksha]
    out, run = [], []
    for s in list(sky.tithi_spans()) + [None]:
        if s is not None and s.value["paksha"] == paksha:
            run.append(s)
            continue
        if run:
            first, final = run[0], run[-1]
            if (not first.open_start and not final.open_end
                    and first.value["tithi_name"] == "Pratipada"
                    and final.value["tithi_name"] == last):
                out.append(Span(first.start, final.end,
                                {"paksha": paksha, "tithis": len(run)}))
            run = []
    return out


def _paksha_of_n_days(*wanted):
    """Fortnights holding exactly `n` civil days at the venue.

    Per location, and it has to be: a fortnight's LENGTH IN DAYS is a property
    of the calendar the venue keeps, not of the sky. The count is
    `civil_day_overlap` applied to the fortnight -- how many of the venue's
    dates the interval touches -- assembled out of `weekdays_in_span`, which is
    the same arithmetic B101 counts its Saturdays with and reads no record.
    """
    def fn(sky, loc: str):
        out = []
        for paksha, n in wanted:
            for f in _fortnights(sky, paksha):
                days = sum(len(weekdays_in_span(f, w, loc)) for w in range(7))
                if days == n:
                    out.append(Span(f.start, f.end,
                                    {**f.value, "civil_days": days}))
        return sorted(out, key=lambda s: s.start)
    return fn


def mercury_vedh_moon_residencies(sky) -> list[dict]:
    """Every Mercury residency inside a combust-and-retrograde window, with
    what happened to it: a target, or the reason there was none.

    Reported, and not folded into the condition, because a rule that finds no
    day has THREE different reasons available and they are not the same fact:

    * the wheel's target for that residency is **Abhijeet**, the 28th
      nakshatra, which `nakshatra_scheme: 27` does not emit at all -- so the
      Moon can never be found in it and the row is BLOCKED, not absent;
    * the 2026 table never printed that (nakshatra, Retrograde) key, so there
      is no target to look for -- the gap `vedha._lookup` already refuses to
      paper over with another class's cell;
    * the target exists and is emitted, and the Moon simply was not there.

    Collapsing the three into one empty list is the same quiet blank this whole
    module is built to prevent, one level down, so the walk is exposed.
    """
    wheel = WHEELS["Mercury"]
    base = intersect(
        list(sky.combust_spans("Mercury")),
        [s for s in sky.motion_spans("Mercury") if s.value == "retrograde"],
        lambda d, _m: {"direction": d, "class": "Retrograde"})
    rows = []
    for s in base:
        for own in sky.spans("Mercury", "nakshatra"):
            lo, hi = max(s.start, own.start), min(s.end, own.end)
            if lo >= hi:
                continue
            target = wheel.get((own.value, "Retrograde"))
            if target is None:
                why = "the_2026_table_never_printed_this_nakshatra_retrograde"
            elif target == names.ABHIJIT:
                why = "target_is_abhijit_which_the_27_division_does_not_emit"
            else:
                why = None
            rows.append({"start": lo, "end": hi, "direction": s.value["direction"],
                         "mercury_nakshatra": own.value,
                         "vedha_target": target,
                         "target_unavailable_because": why})
    return sorted(rows, key=lambda r: r["start"])


def _mercury_vedh_of_moon_combust_retrograde():
    """Mercury combust AND retrograde, with the Moon in the star he vedhas.

    The target comes from B133's wheel, keyed on Mercury's own nakshatra and
    the Retrograde class the group's own title supplies -- so no speed
    threshold is consulted here at all, which is why this group is portable
    while the two Vedha groups beside it are not.

    Residencies with no usable target emit nothing and are reported by
    `mercury_vedh_moon_residencies` rather than dropped in silence.
    """
    def fn(sky):
        out: list[Span] = []
        for row in mercury_vedh_moon_residencies(sky):
            if row["target_unavailable_because"] is not None:
                continue
            for moon in sky.spans("Moon", "nakshatra"):
                if moon.value != row["vedha_target"]:
                    continue
                a, b = max(row["start"], moon.start), min(row["end"], moon.end)
                if a < b:
                    out.append(Span(a, b, {
                        "direction": row["direction"],
                        "class": "Retrograde",
                        "mercury_nakshatra": row["mercury_nakshatra"],
                        "vedha_target": row["vedha_target"],
                        "vedha_direction": VEDHA_DIRECTION["Retrograde"],
                        "moon_nakshatra": moon.value}))
        return sorted(out, key=lambda s: s.start)
    return fn


# =========================================================== GOLD -- BULLISH
_g = G("gold-bullish", 1)
_rule(
    _g,
    id="cfg_gold_bullish_01_mars_through_taurus",
    rule_family="residency/planet_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="The group's only prose is a vargottam sub-window -- "
          f"{_g.paras[0]!r} -- and its table is empty. The CONDITION the "
          "heading states is the Taurus residency, which is what is ported; "
          "the vargottam stretch inside it is recorded here rather than "
          "silently made the condition, because the heading says Passes "
          "Through and not Vargottam.",
)(_sign("Mars", "Taurus"))

_g = G("gold-bullish", 2)
_blocked(
    _g,
    id="cfg_gold_bullish_02_sun_libra_aspected_by_malefics",
    rule_family="residency/planet_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("valence",),
    notes="The Sun's Libra residency and Mars's aspect to it are both emitted; "
          "WHICH aspects count as malefic is what the source never states. Its "
          "single printed row is Mars's 4th aspect, 17-Oct-26 to 12-Nov-26.",
)

_g = G("gold-bullish", 3)
_rule(
    _g,
    id="cfg_gold_bullish_03_rahu_mars_same_sign",
    rule_family="residency/same_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="`residency/same_sign`, the shape B84/B93 already use. The printed "
          "2026 row is Aquarius, 23-Feb-26 to 01-Apr-26.",
)(_together("Rahu", "Mars", "sign"))

_g = G("gold-bullish", 4)
_rule(
    _g,
    id="cfg_gold_bullish_04_jupiter_in_gemini",
    rule_family="residency/planet_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="Read as the residency the source's own row is, not as the ingress "
          "instant the heading's verb suggests: the printed row runs 05-Dec-25 "
          "17:35 to 02-Jun-26 01:49, which is a window in Gemini.",
)(_sign("Jupiter", "Gemini"))

_g = G("gold-bullish", 5)
_blocked(
    _g,
    id="cfg_gold_bullish_05_malefic_vedh_of_four_stars",
    rule_family="vedha/nakshatra",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("valence",),
    notes="Twenty printed rows. A vedha wheel exists for the planets that have "
          "one, but the ROW SELECTION is 'malefic planets', so the valence "
          "binds before the wheel does. The heading's own "
          f"{split_statement(_g.title)[1]!r} is an intensifier on the block's "
          "direction and is carried here rather than as a second verdict.",
)

_g = G("gold-bullish", 6)
_blocked(
    _g,
    id="cfg_gold_bullish_06_mars_aspected_by_saturn",
    rule_family="aspect/graha_drishti",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("aspect_orb",),
    notes="SCOPE SURVEY SAID READY; IT IS NOT. The survey read this as 'a "
          "two-body aspect plus the motion field, both already used by "
          "catalogue-B rules'. The motion half is right and the aspect half is "
          "not: the layer emits `aspect/conjunction` and `aspect/opposition` "
          "and no other angle, and this group's own printed row is Saturn in "
          "Pisces with Mars in Sagittarius -- the tenth-house graha drishti, "
          "which is neither. Blocked on `aspect_orbs`, the open config "
          "question whose text is 'graha drishti vs degree orbs', so it is "
          "still one of the five and not a sixth.",
)

_g = G("gold-bullish", 7)
_blocked(
    _g,
    id="cfg_gold_bullish_07_sun_four_stars_not_aspected_by_benefic",
    rule_family="residency/planet_nakshatra",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("valence",),
    notes="Negated on a BENEFIC aspect and intensified on a malefic one, so "
          "the valence is needed in both directions before either branch can "
          "fire. The Sun's four nakshatra residencies are emitted and are not "
          "the missing half.",
)

_g = G("gold-bullish", 8)
_blocked(
    _g,
    id="cfg_gold_bullish_08_moonrise_monday_or_friday",
    rule_family="visibility/darshan",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    missing_inputs=("darshan",),
    notes="Two printed rows, 20-Mar-26 and 12-Oct-26, with no sign and no "
          "star. A moonrise on every Monday and Friday of the year would be "
          "104 rows, so this is the SIGHTING and not the daily rise -- the "
          "computation B62 is blocked on.",
)

_g = G("gold-bullish", 9)
_blocked(
    _g,
    id="cfg_gold_bullish_09_moonrise_in_libra",
    rule_family="visibility/darshan",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    missing_inputs=("darshan",),
    notes="The same sighting class; its Sign and Nakshatra columns say the "
          "sighting falls on a day the Moon is in Libra and Swati, which is a "
          "filter on the sighting and not a substitute for it.",
)

_g = G("gold-bullish", 10)
_rule(
    _g,
    id="cfg_gold_bullish_10_sun_moon_same_degree",
    rule_family="lunation/new_moon",
    condition_text=_at(_g.title, " Is "),
    condition_from="title",
    verdict_text=_from(_g.title, "Bullish"),
    verdict_from="title",
    inputs=("lunation",),
    notes="The Sun and Moon on the same degree IS the new moon, and the "
          "group's twelve printed rows are the twelve 2026 new moons with "
          "their longitudes. Ported off the lunation series rather than by "
          "scanning longitudes, so the rule and the calendar cannot disagree.",
)(_instants("lunation", "lunation/new_moon"))

_g = G("gold-bullish", 11)
_rule(
    _g,
    id="cfg_gold_bullish_11_venus_in_rohini",
    rule_family="residency/planet_nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/nakshatra",),
    notes="Printed window 27-Apr-26 21:05 to 08-May-26 21:48.",
)(_star("Venus", "Rohini"))

_g = G("gold-bullish", 12)
_rule(
    _g,
    id="cfg_gold_bullish_12_mars_in_pushya",
    rule_family="residency/planet_nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/nakshatra",),
    notes="Printed window 24-Sep-26 05:40 to 17-Oct-26 12:46.",
)(_star("Mars", "Pushya"))

_g = G("gold-bullish", 13)
_rule(
    _g,
    id="cfg_gold_bullish_13_aquarius_sankranti_on_friday",
    rule_family="calendar/sankranti",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign", "weekday"),
    weekdays=names.weekdays_in(_g.title),
    notes="The Sankranti series is B1's and carries the weekday on every "
          "record; the Friday half is applied by `fire` after the instant has "
          "been resolved to a day AT A VENUE, which is the only point at which "
          "a weekday exists. The printed 2026 row is 13-Feb-26, a Friday.",
)(_sankranti("Aquarius"))


# =========================================================== GOLD -- BEARISH
_g = G("gold-bearish", 1)
_rule(
    _g,
    id="cfg_gold_bearish_01_jupiter_rise",
    rule_family="visibility/rise",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="`visibility/rise` from the combustion class, the primitive B15's "
          "rise rules use. Kalamsha is a horizon measurement at the primary "
          "location and the records are date_only, so this keys on the Mumbai "
          "civil day and says so rather than rendering a venue it was never "
          "evaluated at.",
)(_rise("Jupiter"))

_g = G("gold-bearish", 2)
_rule(
    _g,
    id="cfg_gold_bearish_02_saturn_or_mercury_in_gemini",
    rule_family="residency/planet_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("ingress/sign",),
    notes="The heading states a disjunction and the rule fires the union; the "
          "printed row names only Mercury, which is the disjunct that occurs "
          "in 2026 and not a narrowing of the condition.",
)(_union(_sign("Saturn", "Gemini"), _sign("Mercury", "Gemini")))

_g = G("gold-bearish", 3)
_blocked(
    _g,
    id="cfg_gold_bearish_03_benefic_vedh_of_four_stars",
    rule_family="vedha/nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("valence",),
    notes="The mirror of gold-bullish#5: eleven printed rows selected on "
          "BENEFICS. One missing input, two groups, and they are one batch "
          "once it is supplied.",
)

_g = G("gold-bearish", 4)
_rule(
    _g,
    id="cfg_gold_bearish_04_mercury_rise_in_west",
    rule_family="visibility/rise",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="Exactly what `b015b_venus_rise_west` does, with Mercury's rise "
          "records. Three printed 2026 rows.",
)(_rise("Mercury", direction="West"))

_g = G("gold-bearish", 5)
_blocked(
    _g,
    id="cfg_gold_bearish_05_moon_darshan_on_saturday",
    rule_family="visibility/darshan",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("darshan",),
    notes="Darshan is the sighting, which is B62's computation and is blocked "
          "on the same evidence.",
)

_g = G("gold-bearish", 6)
_rule(
    _g,
    id="cfg_gold_bearish_06_venus_in_punarvasu",
    rule_family="residency/planet_nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/nakshatra",),
    notes="Printed window 31-May-26 05:47 to 11-Jun-26 14:07.",
)(_star("Venus", "Punarvasu"))


# ========================================================= SILVER -- BULLISH
_g = G("silver-bullish", 1)
_SB1_RIGHT = split_statement(_g.title)[1]
_rule(
    _g,
    id="cfg_silver_bullish_01_shukla_shashti_turning_dates",
    rule_family="panchang/tithi",
    condition_text=_at(_SB1_RIGHT, " ("),
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("panchang/tithi",),
    notes="The heading's dash does NOT separate a verdict here -- its right "
          f"half is {_SB1_RIGHT!r}, which is the condition and its impact "
          "window. Taking that half as the verdict is the B87 colon failure "
          "wearing a dash, so the verdict is the block's own word and the "
          f"impact window is carried here: {_from(_SB1_RIGHT, '(')!r}.",
)(_tithi_named(*names.tithis_in(_at(_SB1_RIGHT, " (")), paksha="Shukla"))

_g = G("silver-bullish", 2)
_rule(
    _g,
    id="cfg_silver_bullish_02_retrograde_mercury_or_jupiter",
    rule_family="motion/retrograde",
    condition_text=_at(_g.title, " Increases "),
    condition_from="title",
    verdict_text=_from(_g.title, "Increases "),
    verdict_from="title",
    inputs=("motion/station",),
    notes="The heading runs condition into verdict without a dash, so the cut "
          "is at the verb the verdict starts with. Five printed rows, two "
          "Jupiter and three Mercury.",
)(_retrograde("Mercury", "Jupiter"))

_g = G("silver-bullish", 3)
_blocked(
    _g,
    id="cfg_silver_bullish_03_sun_pushya_or_dhanistha_without_benefic",
    rule_family="residency/planet_nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("valence",),
    notes="Negated on a BENEFIC presence. The Sun's two nakshatra residencies "
          "are emitted; the selection is not.",
)

_g = G("silver-bullish", 4)
_blocked(
    _g,
    id="cfg_silver_bullish_04_mars_itself_in_aquarius",
    rule_family="residency/planet_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    missing_inputs=("no_dated_window",),
    notes="This is a missing TABLE, not a missing input: the source's own note "
          f"is {_g.notes[0]!r}. The residency is perfectly computable; what "
          "there is none of is a printed window to check a port against, and "
          "registering a rule with nothing to reproduce would be the one kind "
          "of coverage this project refuses.",
)

_g = G("silver-bullish", 5)
_rule(
    _g,
    id="cfg_silver_bullish_05_venus_mars_same_sign",
    rule_family="residency/same_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="Three printed 2026 rows: Sagittarius, Capricorn, Aquarius.",
)(_together("Venus", "Mars", "sign"))

_g = G("silver-bullish", 6)
_rule(
    _g,
    id="cfg_silver_bullish_06_sun_mars_same_sign",
    rule_family="residency/same_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="Five printed 2026 rows.",
)(_together("Sun", "Mars", "sign"))

_g = G("silver-bullish", 7)
_rule(
    _g,
    id="cfg_silver_bullish_07_rahu_mars_same_sign",
    rule_family="residency/same_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="The heading's right half, "
          f"{split_statement(_g.title)[1]!r}, is an intensifier on the block's "
          "direction and not a second verdict, so it is carried here and the "
          "verdict stays the block's word. The same condition as "
          "gold-bullish#3, stated for a different instrument.",
)(_together("Rahu", "Mars", "sign"))

_g = G("silver-bullish", 8)
_blocked(
    _g,
    id="cfg_silver_bullish_08_moon_darshan_friday_saturday",
    rule_family="visibility/darshan",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    missing_inputs=("darshan",),
    notes=f"Four printed rows. The group's own impact note is {_g.notes[0]!r}.",
)

_g = G("silver-bullish", 9)
_rule(
    _g,
    id="cfg_silver_bullish_09_sun_moon_together_on_sankranti",
    rule_family="calendar/sankranti",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="One instant and two emitted series: the Sun's sign ingress, and the "
          "Moon's sign at that instant read off her own ingress series. The "
          f"group's impact note is {_g.notes[0]!r} -- carried here and not as "
          "the verdict, because a duration is not a direction.",
)(_sankranti_with_moon_in_the_same_sign())

_g = G("silver-bullish", 10)
_blocked(
    _g,
    id="cfg_silver_bullish_10_mercury_or_jupiter_vedh_of_venus",
    rule_family="vedha/nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("vedha_wheel",),
    flags=("printed_rows_are_venus_as_the_vedher_not_the_vedhed",),
    notes="SCOPE SURVEY SAID READY; IT IS NOT, and the table says something "
          "different again from the heading. The heading's condition is a "
          "disjunction and JUPITER's half has no wheel: B135 is blocked on the "
          "slow-planet speed doctrine, so only Mercury's half is computable "
          "and half a disjunction is not this group. Separately, the two "
          "printed rows are VENUS rows -- Venus in Purva Bhadrapad vedhing "
          "Punarvasu, 22-Feb-26 00:39 to 04-Mar-26 17:11 -- which is a row of "
          "gold-bearish#3's benefic table with Venus as the VEDHER, not Venus "
          "being vedhed by anyone. Both facts are recorded; neither is "
          "reconciled by us.",
)

_g = G("silver-bullish", 11)
_resolved(
    _g,
    id="cfg_silver_bullish_11_mercury_combust_retrograde_vedh_moon",
    rule_family="vedha/nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("visibility/combust", "motion/station", "ingress/nakshatra"),
    locations=MUMBAI_ONLY,
    ambiguity="'Mutual Vedh with Moon' admits two readings. (a) BOTH bodies "
              "vedh each other, which needs the Moon's own Nakshtra Vedh wheel "
              "as well as Mercury's. (b) The Moon occupies the nakshatra "
              "MERCURY vedhs, 'mutual' naming the relation rather than "
              "requiring a second lookup.",
    resolution=(
        "The group's own two rows resolve entirely out of Mercury's wheel "
        "under reading (b) and need nothing else: Mercury in Punarvasu "
        "Retrograde vedhs Purva Bhadrapada, which is the printed Moon "
        "nakshatra of the 05-Jul-26 row; Mercury in Vishakha Retrograde vedhs "
        "Krittika, which is the printed Moon nakshatra of the 27-Oct-26 row. "
        "Two of two.",
        "The class the wheel is keyed on is supplied by the group's own title "
        "-- 'Retrograde' -- so no speed threshold is consulted, which is why "
        "this group is portable where silver-bullish#10 and silver-bearish#6 "
        "are not.",
        "The document prints no Vedha wheel for the Moon anywhere, in any "
        "chapter. Reading (a) would require a table the source does not have, "
        "so it cannot be the reading its own rows obey.",
    ),
    rejected_readings=(
        "(a) mutual = both bodies vedh each other, needing a Moon wheel. "
        "Rejected because no Moon wheel is printed and because both printed "
        "rows are already accounted for without one.",
    ),
    flags=("mutual_read_as_moon_in_mercurys_vedha_target", HORIZON_FLAG,
           "vedha_target_may_be_abhijit_which_the_layer_does_not_emit"),
    notes="The wheel entry used is a transcription of B133's own table and not "
          "a derivation; a change to it is a transcription edit. Mumbai only, "
          "because the combustion half is date_only at the primary horizon. "
          "IT FIRES ZERO TIMES IN 2027 AND THE ZERO HAS THREE CAUSES, which "
          "`mercury_vedh_moon_residencies` separates rather than collapsing: "
          "Mercury has eight combust-and-retrograde residencies in the "
          "generated span; five of them (Dhanishta, Ardra, Mrigashira, Chitra, "
          "Shravana) are keys the 2026 table never printed under Retrograde, "
          "so there is no target; one (Shatabhisha, 12-17 Feb-2027) has the "
          "target ABHIJEET, the 28th nakshatra, which `nakshatra_scheme: 27` "
          "does not emit -- the Moon can never be found in it, so that "
          "residency is blocked rather than absent; and one (Swati, 9-15 "
          "Oct-2027, target Rohini) is fully computable and the Moon was not "
          "in Rohini during it. Only the last is a statement about the sky.",
)(_mercury_vedh_of_moon_combust_retrograde())

_g = G("silver-bullish", 12)
_rule(
    _g,
    id="cfg_silver_bullish_12_venus_combust_in_west",
    rule_family="visibility/combust",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="The verdict states its own end -- 'Till It Rises in East' -- which "
          "is the combust span's far end, so the window and the verdict agree "
          "and nothing is segmented.",
)(_combust("Venus", direction="West"))

_g = G("silver-bullish", 13)
_rule(
    _g,
    id="cfg_silver_bullish_13_jupiter_or_mercury_turns_direct",
    rule_family="motion/station",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("motion/station",),
    notes="Four printed rows, one Jupiter and three Mercury, and the station "
          "series reproduces the source's own directions.",
)(_turns_direct("Jupiter", "Mercury"))

_g = G("silver-bullish", 14)
_rule(
    _g,
    id="cfg_silver_bullish_14_paksha_of_16_or_14_days",
    rule_family="panchang/paksha_length",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("panchang/tithi",),
    per_location=True,
    notes="Per location and necessarily: the LENGTH of a fortnight in days is "
          "a fact about the calendar a venue keeps, not about the sky, and a "
          "16-day Shukla Paksh in Mumbai need not be one in New York. The "
          "count is civil_day_overlap applied to the fortnight. Six printed "
          "2026 rows, four Krishna and two Shukla.",
)(_paksha_of_n_days(("Shukla", 16), ("Krishna", 14)))

_g = G("silver-bullish", 15)
_rule(
    _g,
    id="cfg_silver_bullish_15_sun_or_moon_with_mercury_alone",
    rule_family="residency/alone_in_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("ingress/sign",),
    flags=("alone_judged_against_b16_residency_bodies",),
    notes="'Alone' is the source's own word with the source's own gloss -- the "
          "prophecy blocks read 'alone in any sign without any other "
          "Planet(s)' -- and is judged against batch 2's RESIDENCY_BODIES, "
          "imported rather than retyped. That set excludes the Moon, so the "
          "Moon-Mercury disjunct asks only that no OTHER residency body shares "
          "the sign. All seven printed 2026 rows are Sun-Mercury.",
)(_union(_alone("Sun", "Mercury"), _alone("Moon", "Mercury")))

_g = G("silver-bullish", 16)
_rule(
    _g,
    id="cfg_silver_bullish_16_mercury_jupiter_both_retrograde",
    rule_family="motion/both_retrograde",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("motion/station",),
    notes="The same condition B82 states, ported here for silver. B82 "
          "reproduces its printed row to 24 minutes at the start and 22 at the "
          "end; this group prints the same 2026 window, 26-Feb-26 12:19 to "
          "11-Mar-26 09:01.",
)(_both_retrograde("Mercury", "Jupiter"))

_g = G("silver-bullish", 17)
_rule(
    _g,
    id="cfg_silver_bullish_17_retrograde_mercury_goes_combust",
    rule_family="visibility/combust",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("visibility/combust", "motion/station"),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="The group prints DATES, not windows -- 01-Mar, 03-Jul and 28-Oct-26 "
          "-- so the row is the instant combustion begins inside a retrograde "
          "stretch, not the stretch.",
)(_goes_combust_while_retrograde("Mercury", instant=True))

def _eclipses_in_months(family, months):
    """Eclipses whose purnimanta month (Sky.eclipse_month) is listed."""
    wanted = set(months)

    def fn(sky):
        out = []
        for r in sky.class_records("eclipse", family=family):
            m = sky.eclipse_month(r)
            if m in wanted:
                t = parse(r["time"]["t_start_utc"])
                out.append(Span(t, t, {"id": r["id"], "month": m}))
        return out
    return fn


def _margshirsh_krishna_panchami(sky):
    """Krishna Panchami (tithi 20) spans in the purnimanta month Margashirsh,
    judged at the tithi's midpoint."""
    out = []
    for sp in sky.tithi_spans():
        if sp.value["tithi"] != 20:
            continue
        mid = sp.start + (sp.end - sp.start) / 2
        if sky.purnimanta_month(mid) == "Margashirsh":
            out.append(Span(sp.start, sp.end, {"tithi": "Krishna Panchami",
                                               "month": "Margashirsh"},
                            sp.open_start, sp.open_end))
    return out


_g = G("silver-bullish", 18)
_rule(
    _g,
    id="cfg_silver_bullish_18_sun_eclipse_in_falgun_or_jyestha",
    rule_family="eclipse/solar",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("eclipse", "lunation", "ingress/sign", "weekday"),
    weekdays=names.weekdays_in(_g.title),
    notes="PORTED 19-Nov-2026 on the purnimanta month (Sky.eclipse_month). "
          "Its own printed row, 17-Feb-26 Falgun Tuesday, is a SOLAR eclipse "
          "named by the purnimanta system -- amanta would call it Magh -- so "
          "this group is itself evidence for the ruling, and it reproduces.",
)(_eclipses_in_months("eclipse/solar", ("Falgun", "Jyeshtha")))

_g = G("silver-bullish", 19)
_rule(
    _g,
    id="cfg_silver_bullish_19_mars_rising",
    rule_family="visibility/rise",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="Mars has one combustion in the generated span and no rise record "
          "inside it, so this rule is expected to fire zero times in 2027. "
          "That is a statement about the sky and not about the port, and it is "
          "surfaced by `zero_firing` rather than hidden.",
)(_rise("Mars"))

_g = G("silver-bullish", 20)
_rule(
    _g,
    id="cfg_silver_bullish_20_saturn_neptune_conjunction",
    rule_family="aspect/conjunction",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("aspect/conjunction",),
    notes="Saturn and Neptune are both in config's `conjunctions.bodies`, so "
          "the pair IS scanned and a zero count is a fact about 2027 rather "
          "than an unemitted series. The group's own end condition is "
          f"{_g.notes[0]!r}, a recovery in longitude the layer emits no series "
          "for, carried as text rather than fired as a second window.",
)(_conjunction("Saturn", "Neptune"))


# ========================================================= SILVER -- BEARISH
_g = G("silver-bearish", 1)
_rule(
    _g,
    id="cfg_silver_bearish_01_venus_alone_in_leo_or_libra",
    rule_family="residency/alone_in_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("ingress/sign",),
    flags=("alone_judged_against_b16_residency_bodies",
           "source_exception_names_the_moon_our_alone_set_does_not"),
    notes="THE SOURCE AND OUR 'ALONE' DISAGREE HERE, and the disagreement is "
          f"carried rather than settled. The group's exception is {_g.notes[0]!r} "
          "-- so the source counts the Moon as breaking Venus's solitude. "
          "Batch 2's RESIDENCY_BODIES excludes the Moon, because a Moon in the "
          "set would break every alone-window thirteen times a year, and "
          "changing the set for one rule would make two modules answer 'alone' "
          "differently, which is what pairs.py refused. The rule therefore "
          "fires the wider window and the narrower one the source prints is "
          "recorded here.",
)(_alone_in_sign("Venus", "Leo", "Libra"))

_g = G("silver-bearish", 2)
_rule(
    _g,
    id="cfg_silver_bearish_02_mercury_alone_in_aries_or_virgo",
    rule_family="residency/alone_in_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("ingress/sign",),
    flags=("alone_judged_against_b16_residency_bodies",),
    notes="One printed 2026 row, Virgo 07-Sep-26 13:35 to 17-Sep-26 07:54.",
)(_alone_in_sign("Mercury", "Aries", "Virgo"))

_g = G("silver-bearish", 3)
_rule(
    _g,
    id="cfg_silver_bearish_03_mars_in_fourth_pad_of_ashlesha",
    rule_family="residency/pada",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("ingress/nakshatra", "ingress/navamsa"),
    notes="The pada is recovered from the navamsa the record already carries, "
          "by `colocation._pada`; it is not a longitude computed here. The "
          "printed row is 05-Nov-26 19:50 to 12-Nov-26 20:22.",
)(_pad("Mars", "Ashlesha", 4))

_g = G("silver-bearish", 4)
_rule(
    _g,
    id="cfg_silver_bearish_04_mars_vargottam_in_cancer",
    rule_family="residency/vargottama",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign", "ingress/navamsa"),
    notes="Vargottama is the agreement of sign and navamsa, which is what "
          "`vargottam.engine_field` is on every record, so this is the "
          "intersection of two emitted ingress series and no new quantity. "
          "Printed window 18-Sep-26 16:36 to 24-Sep-26 05:40.",
)(_vargottama("Mars", "Cancer"))

_g = G("silver-bearish", 5)
_rule(
    _g,
    id="cfg_silver_bearish_05_amavasya_on_monday",
    rule_family="lunation/new_moon",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("lunation", "weekday"),
    weekdays=names.weekdays_in(_g.title),
    notes="`lunation/new_moon` is ported as B60 and the weekday half is "
          "applied per location by `fire`. Two printed 2026 rows.",
)(_instants("lunation", "lunation/new_moon"))

_g = G("silver-bearish", 6)
_blocked(
    _g,
    id="cfg_silver_bearish_06_mercury_or_moon_venus_mutual_vedh",
    rule_family="vedha/nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("vedha_wheel",),
    notes="SCOPE SURVEY SAID READY; IT IS NOT. Every one of the thirteen "
          "printed rows is a VENUS row -- Venus in Dhanistha vedhing Ashlesha, "
          "Venus in Chitra vedhing Purva Bhadrapada, and so on -- and each "
          "resolves exactly through B134's Venus wheel. B134 is withdrawn: "
          "Venus's speed level was fitted to a single 2026 crossing, so the "
          "CLASS the wheel is keyed on carries no evidence. The transcription "
          "is right and the key is unearned, which is the ruling B134 itself "
          "records.",
)

_g = G("silver-bearish", 7)
_rule(
    _g,
    id="cfg_silver_bearish_07_moon_eclipse_on_sunday",
    rule_family="eclipse/lunar",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("eclipse", "weekday"),
    weekdays=names.weekdays_in(_g.title),
    notes="`eclipse/lunar` is ported as B110 and carries the weekday. The "
          "verdict dates its own effect fifteen days out and is carried as the "
          "source states it, undated: emitting a second window fifteen days "
          "later would be authoring a row the page does not print. The group's "
          "single printed row is dated 07-Sep-25, outside the source's own "
          "year.",
)(_instants("eclipse", "eclipse/lunar"))

_g = G("silver-bearish", 8)
_rule(
    _g,
    id="cfg_silver_bearish_08_saturn_direct_from_retrograde",
    rule_family="motion/station",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    inputs=("motion/station",),
    notes="The printed row heads its column 'Retrograde Date' and gives "
          "11-Dec-26, which is Saturn's station DIRECT and not his station "
          "retrograde (27-Jul-26); the heading and the date agree and the "
          "column label does not. The condition is ported as the heading "
          "states it.",
)(_turns_direct("Saturn"))

_g = G("silver-bearish", 9)
_blocked(
    _g,
    id="cfg_silver_bearish_09_sun_three_signs_with_or_aspected_by_benefics",
    rule_family="aspect/graha_drishti",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    missing_inputs=("aspect_orb", "valence"),
    notes="The residency half is computable and the 'with' branch would need "
          "only the valence; the 'aspected by' branch needs the orb as well, "
          "and the orb is the more binding of the two because the aspect "
          "machinery is validated only against exact-ish printed rows. Both "
          "printed rows are 'With', not 'Aspected'.",
)

_g = G("silver-bearish", 10)
_rule(
    _g,
    id="cfg_silver_bearish_10_venus_rise_in_west",
    rule_family="visibility/rise",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("visibility/combust",),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="The same condition `b015b_venus_rise_west` fires, stated here for "
          "silver and bearish where B15 states it for gold.",
)(_rise("Venus", direction="West"))


# ========================================================== SUGAR -- BULLISH
_g = G("sugar-bullish", 1)
_rule(
    _g,
    id="cfg_sugar_bullish_01_jupiter_in_cancer",
    rule_family="residency/planet_sign",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/sign",),
    notes="Printed window 02-Jun-26 01:49 to 31-Oct-26 12:02, which is a "
          "residency and not an ingress.",
)(_sign("Jupiter", "Cancer"))

_g = G("sugar-bullish", 2)
_rule(
    _g,
    id="cfg_sugar_bullish_02_eclipse_in_falgun",
    rule_family="eclipse/any",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("eclipse", "lunation", "ingress/sign"),
    flags=("solar_falgun_eclipse_not_printed_in_2026",),
    notes=f"PORTED 19-Nov-2026 on the purnimanta month. The group's impact note "
          f"is {_g.notes[0]!r}. CARRIED, NOT TUNED AWAY: it prints only "
          "03-Mar-26 (lunar, Falgun under either system) and not 17-Feb-26, the "
          "solar eclipse silver-bullish#18 prints as Falgun on the same "
          "purnimanta reckoning. The document disagrees with itself here; this "
          "rule follows the system the other three sources settle and so fires "
          "on both.",
)(_eclipses_in_months(None, ("Falgun",)))

_g = G("sugar-bullish", 3)
_blocked(
    _g,
    id="cfg_sugar_bullish_03_malefic_vedh_of_four_stars",
    rule_family="vedha/nakshatra",
    condition_text=split_final(_g.title)[0],
    condition_from="title",
    verdict_text=split_final(_g.title)[1],
    verdict_from="title",
    missing_inputs=("valence",),
    notes="Twenty-one printed rows selected on malefic planets. Split at the "
          "heading's LAST dash and not its first: the middle segment ('if More "
          "than One Nakshtra Vedh at the Same Time') is part of the condition, "
          "and taking the first dash would put half the condition inside the "
          "verdict.",
)

_g = G("sugar-bullish", 4)
_rule(
    _g,
    id="cfg_sugar_bullish_04_moon_joins_combust_mercury_in_west",
    rule_family="visibility/combust",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("visibility/combust", "ingress/sign"),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG, "joins_read_as_the_shared_sign"),
    notes="'Joins' is read as the shared SIGN, and the group's own rows decide "
          "it: 12-Jul-26 19:08 to 14-Jul-26 18:50 is 1.99 days and 07-Nov-26 "
          "17:36 to 10-Nov-26 02:50 is 2.38, which is a Moon sign transit. A "
          "nakshatra would be about a day and a conjunction an instant.",
)(_moon_joins_combust("Mercury", "West"))

_g = G("sugar-bullish", 5)
_rule(
    _g,
    id="cfg_sugar_bullish_05_retrograde_mercury_combust_in_cancer",
    rule_family="visibility/combust",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("visibility/combust", "motion/station", "ingress/sign"),
    locations=MUMBAI_ONLY,
    flags=(HORIZON_FLAG,),
    notes="The same intersection silver-bullish#17 states, narrowed to Cancer "
          "and emitted as the WINDOW the group prints (03-Jul-26 05:00 to "
          "07-Jul-26 10:37) rather than as the instant.",
)(_goes_combust_while_retrograde("Mercury", instant=False, signs=("Cancer",)))

_g = G("sugar-bullish", 6)
_blocked(
    _g,
    id="cfg_sugar_bullish_06_herschel_with_any_malefic",
    rule_family="residency/same_sign",
    condition_text=split_statement(_g.title)[0],
    condition_from="title",
    verdict_text=split_statement(_g.title)[1],
    verdict_from="title",
    missing_inputs=("valence",),
    notes="Blocked twice over by one absence. 'With any malefic planet' needs "
          "the valence, and this group's own table names 'Kshin Chandra' -- "
          "the waning Moon -- as one of its malefics, which needs the Kshin "
          "definition the source states nowhere. The Kshin (Malefic) Moon "
          "sub-table in the same chapter is unported for the same reason, so "
          "the valence question and the Kshin question are one question asked "
          "twice.",
)

_g = G("sugar-bullish", 7)
_rule(
    _g,
    id="cfg_sugar_bullish_07_margshirsh_krishna_panchami",
    rule_family="panchang/tithi",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("panchang/tithi", "lunation", "ingress/sign", "weekday"),
    weekdays=names.weekdays_in(_g.title),
    notes="PORTED 19-Nov-2026: Krishna Panchami (tithi 20) in the purnimanta "
          "month Margashirsh, i.e. the Krishna fortnight after Kartik Purnima. "
          "The printed 28-Nov-26 is that tithi's sunrise day (amanta would put "
          "it near 28-Dec), which supports purnimanta; 28-Nov is a Saturday, so "
          "the row lists the tithi and not a qualifying weekday, and the "
          "weekday half is applied as the title states it.",
)(_margshirsh_krishna_panchami)


# ========================================================== SUGAR -- BEARISH
_g = G("sugar-bearish", 1)
_rule(
    _g,
    id="cfg_sugar_bearish_01_jupiter_or_mars_in_three_stars",
    rule_family="residency/planet_nakshatra",
    condition_text=_g.title,
    condition_from="title",
    verdict_text=_g.block.verdict,
    verdict_from="block_h2",
    inputs=("ingress/nakshatra",),
    notes="A three-way disjunction; the rule fires the union. The printed row "
          "is the Mars-in-Dhanistha disjunct, 15-Feb-26 to 03-Mar-26.",
)(_union(_star("Jupiter", "Hast", "Shravan"), _star("Mars", "Dhanistha")))

_g = G("sugar-bearish", 2)
_blocked(
    _g,
    id="cfg_sugar_bearish_02_malefic_vedh_of_four_stars",
    rule_family="vedha/nakshatra",
    condition_text=split_final(_g.title)[0],
    condition_from="title",
    verdict_text=split_final(_g.title)[1],
    verdict_from="title",
    missing_inputs=("valence",),
    flags=("source_states_its_own_incompleteness",),
    notes="The bearish half of sugar-bullish#3's table -- one input, one "
          "batch, with the bullish half. The group closes with the source's "
          f"own {_g.notes[0]!r}, an admitted incompleteness carried forward as "
          "it stands and not completed by us.",
)

del _g


# ------------------------------------------------------------------ the sweep
# Registration already checks every rule one at a time. This runs the same
# check over the finished registry, so the guarantee does not rest on
# `_register` surviving an edit to this file -- and it runs at IMPORT, so a
# regression is an ImportError and never a blank cell in a report.
CHECKED = assert_no_silent_verdicts(CONFIG_REGISTRY)

if len(CONFIG_REGISTRY) != len(GROUPS):                 # pragma: no cover
    raise SystemExit(
        f"{len(CONFIG_REGISTRY)} configuration rules registered against "
        f"{len(GROUPS)} groups in the document; every group is registered, "
        "ported or blocked, so the two counts must agree")


# ----------------------------------------------------------------- accessors
def by_status(status: str) -> list[Rule]:
    return [r for r in CONFIG_REGISTRY if r.status == status]


def ported() -> list[Rule]:
    """Configuration rules that can produce a dated row."""
    return [r for r in CONFIG_REGISTRY if r.status in FIRING_STATUSES]


def blocked_rules() -> list[Rule]:
    return by_status(STATUS_BLOCKED)


def by_group() -> dict[str, Rule]:
    return {r.section.key: r for r in CONFIG_REGISTRY}


def missing_input_counts() -> dict[str, int]:
    """How many groups each named input blocks, counted off the registry so
    the number and the rules cannot drift apart."""
    out = {k: 0 for k in MISSING_INPUTS}
    for r in blocked_rules():
        for k in r.missing_inputs:
            out[k] += 1
    return out


def zero_firing(firings: list[Firing]) -> list[Rule]:
    """Ported rules that never fire in the generated year. Surfaced, not
    tolerated: correct and broken look identical from outside until checked."""
    fired = {f.rule_id for f in firings}
    return [r for r in ported() if r.id not in fired]
