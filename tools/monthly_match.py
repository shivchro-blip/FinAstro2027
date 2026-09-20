"""Run the rule layer over 2026 and compare it with the source's own Chapter 4.

THIS MEASURES THE CALENDAR AS IT STANDS, and what it stands on has changed.
`verdicts.py` fires BOTH registries since the 14-Sep-2026 wiring, so `run_rules`
below fires both too: firing a registry here that the calendar does not read
would measure something nobody ships. A row the source prints that only a
configuration group states is now reproducible, and two of them are -- `Rahu
Mars in the same sign` and `Rahu Mars in the same Nakshatra`, the 166 -> 168
that the port moved.

(This docstring read "THE BASELINE RUN ... verdicts.py fires catalogue B alone
-- the 38 configuration groups are not wired into the calendar" for two days
after the code below stopped doing that. The `config_not_wired` outcome in
`classify` is what remains of it: it now fires only when a configuration target
exists and is BLOCKED, and it produces zero windows in this build. Kept under
its old name rather than renamed silently, because the name is in the recorded
fixture output.)

    python tools/monthly_match.py            # summary to stdout
    python tools/monthly_match.py --json OUT # plus the full per-row result

Nothing here tunes anything. No tolerance is widened to improve a number; the
+/-1-day column exists because a civil-day boundary is a real ambiguity in the
source's own presentation, and it is reported BESIDE the exact column rather
than in place of it.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro import monthly2026 as MO           # noqa: E402
from finastro import monthlymap as MM            # noqa: E402
from finastro.rules import (REGISTRY, CONFIG_REGISTRY,   # noqa: E402
                            SUBTABLE_REGISTRY,
                            FIRING_STATUSES, fire, firing_rules)
from finastro.sky import Sky                     # noqa: E402

ASTRONOMY_2026 = ROOT / "build" / "astronomy_2026.json"
FIXTURE_YEAR = MO.YEAR

#: The source computes its own rise, set and civil day for MUMBAI and says so.
#: Every comparison below is against the Mumbai column for that reason; the New
#: York firings are counted only where the report says so.
VENUE = "mumbai"

RULES = {r.id: r for r in REGISTRY}
CONFIG = {g.id: g for g in CONFIG_REGISTRY}
SUBS = {r.id: r for r in SUBTABLE_REGISTRY}

#: Every rule this build has, by id, whichever registry it lives in. ONE index
#: rather than three names chained with `or` at each use site.
#:
#: The three names above stay, because "which registry is this in" is a real
#: question this file asks -- line 137's `cfg_targets` needs it. What they are
#: not is the way to ask "is this a rule at all". `mapped_rules` asked it as
#: `t in RULES or t in CONFIG`, written when there were two registries, and
#: after the third arrived it silently dropped every `sub_` rule out of the
#: mapped set: all three sub-table ports were reported under "rules no source
#: row maps to" while the map named them. STEP4_DECISIONS section 12.16's
#: eighth instance, on a line that section's own ninth instance did not reach.
ALL_RULES = {**RULES, **CONFIG, **SUBS}
assert len(ALL_RULES) == len(RULES) + len(CONFIG) + len(SUBS), (
    "a rule id is in two registries at once; the three denominators only stay "
    "three if the ids do")


# ------------------------------------------------------------------ direction
#: Words by which either side states a direction. Applied to the source's
#: inference text and to our verbatim verdict text by the same function, so
#: neither side is read more generously than the other.
_UP = ("bullish", "positive", "uptrend", "bounce", "up trend")
_DOWN = ("bearish", "negative", "fall", "downtrend")


def direction(text):
    """`up`, `down`, `both`, or None where the text states no direction."""
    if not text:
        return None
    low = text.lower()
    up = any(w in low for w in _UP)
    down = any(w in low for w in _DOWN)
    if up and down:
        return "both"
    if up:
        return "up"
    if down:
        return "down"
    return None


#: Inference texts that defer rather than state. The document's own words.
_DEFERS = ("explained separately",)
#: Inference texts that name a scope narrower than "the market".
_SCOPED = ("sector", "ruled by", "gold", "silver", "metal", "banking",
           "nifty", "off-market", "geo-politics")


def source_kind(inference: str) -> str:
    low = inference.lower()
    if any(w in low for w in _DEFERS):
        return "defers"
    if direction(inference) is None:
        return "no_direction"
    if any(w in low for w in _SCOPED):
        return "scoped"
    return "plain"


# --------------------------------------------------------------------- firing
def run_rules():
    """Every (rule, venue, civil day) the firing rules produce for 2026."""
    sky = Sky.load(ASTRONOMY_2026)
    if sky.meta["year"] != FIXTURE_YEAR:
        raise SystemExit(
            f"{ASTRONOMY_2026.name} carries year {sky.meta['year']}, not "
            f"{FIXTURE_YEAR} -- run tools/build_2026.py")
    # ALL THREE registries, because `verdicts.py` fires all three. The
    # fixture measures what the CALENDAR contains; firing a registry here
    # that the calendar does not read would measure something nobody ships,
    # and NOT firing one the calendar does read measures a coverage gap that
    # has already been closed -- which is what this call did for the first
    # hour of the sub-table port, reporting 168 of 354 against a build that
    # reproduces 170.
    firings = fire(list(firing_rules()) + list(CONFIG_REGISTRY)
                   + list(SUBTABLE_REGISTRY), sky, year=FIXTURE_YEAR)
    by_rule = collections.defaultdict(lambda: collections.defaultdict(set))
    for f in firings:
        by_rule[f.rule_id][f.location].add(f.civil_date)
    return sky, firings, by_rule


# ---------------------------------------------------------------- the compare
def classify(row, by_rule) -> dict:
    """One fixture row against the rules that claim it."""
    kind, targets, note = MM.MAP[row.event]
    # A configuration target is a FIRING target now that the calendar reads it.
    # Before the wiring it was counted apart, as `config_not_wired`, because a
    # ported group that reached no row was a wiring gap and not a rule gap --
    # and keeping the two separate is what makes this diff mean anything.
    _all = {**RULES, **CONFIG, **SUBS}
    firing_targets = [t for t in targets
                      if t in _all and _all[t].status in FIRING_STATUSES]
    silent_targets = [t for t in targets
                      if t in _all and _all[t].status not in FIRING_STATUSES]
    cfg_targets = [t for t in targets if t in CONFIG]

    days = set()
    for t in firing_targets:
        days |= by_rule.get(t, {}).get(VENUE, set())

    start, end = row.start_date, row.end_date
    on_start = bool(start and start in days)
    within_one = bool(start and any(abs((d - start).days) <= 1 for d in days))
    if start and end:
        in_window = any(start <= d <= end for d in days)
    else:
        in_window = on_start

    # Why nothing was produced, in the document's terms and ours.
    if firing_targets and (on_start or in_window):
        outcome = "reproduced"
    elif firing_targets and days:
        outcome = "fires_elsewhere"          # the rule runs, not on this window
    elif firing_targets:
        outcome = "rule_never_fires"
    elif silent_targets:
        outcome = "rule_blocked"
    elif cfg_targets:
        outcome = "config_not_wired"
    elif kind == MM.SERIES_NO_RULE:
        outcome = "series_no_rule"
    elif kind == MM.SUBTABLE:
        # Registered and blocked on a named input, which is a different fact
        # from nobody having looked at it -- the same distinction `rule_blocked`
        # draws for catalogue B. Kept under its old name because the name is in
        # the recorded fixture output.
        outcome = "subtable_unported"
    else:
        outcome = "no_section"

    return {
        "event": row.event,
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
        "months": row.months,
        "inference": row.inferences[0],
        "inferences": row.inferences,
        "tone": row.tones[0],
        "kind": kind,
        "targets": targets,
        "firing_targets": firing_targets,
        "silent_targets": silent_targets,
        "note": note,
        "outcome": outcome,
        "on_start": on_start,
        "within_one": within_one,
        "in_window": in_window,
        "our_days_near": sorted(
            d.isoformat() for d in days
            if start and abs((d - start).days) <= 7),
    }


def verdict_compare(results) -> dict:
    """Where both sides state something, do they agree?"""
    out = collections.Counter()
    detail = []
    for r in results:
        if r["outcome"] != "reproduced":
            continue
        ours = None
        for t in r["firing_targets"]:
            # Three registries. A KeyError here used to mean a typo in
            # the map; since 20-Sep-2026 it would mean a registry this
            # function does not know about, which is worth the crash.
            rr = ALL_RULES[t]
            if rr.verdict_text:
                ours = rr.verdict_text
                break
        theirs = r["inference"]
        d_ours, d_theirs = direction(ours), direction(theirs)
        kind = source_kind(theirs)
        if d_ours is None and d_theirs is None:
            key = "neither states a direction"
        elif d_ours is None:
            key = "source states, we print none"
        elif d_theirs is None:
            key = ("we state, source defers" if kind == "defers"
                   else "we state, source states none")
        elif d_ours == d_theirs:
            key = ("agree, source narrows the scope" if kind == "scoped"
                   else "agree")
        elif "both" in (d_ours, d_theirs):
            # "Positive, but during a major negative transit" is not the
            # opposite of "Bullish" -- it is the same direction with a
            # qualification the other side does not carry. Counting it as a
            # disagreement would overstate the conflict; counting it as
            # agreement would hide the qualification. It gets its own row.
            key = ("one side qualifies with both directions "
                   f"({'source' if d_theirs == 'both' else 'ours'})")
        else:
            key = "disagree"
        out[key] += 1
        if key == "disagree" or key.startswith(("agree, source narrows",
                                                "one side qualifies")):
            detail.append({"event": r["event"], "start": r["start"],
                           "ours": ours, "theirs": theirs,
                           "d_ours": d_ours, "d_theirs": d_theirs,
                           "key": key})
    return {"counts": dict(out.most_common()), "detail": detail}


def source_self_consistency() -> dict:
    """The document's Chapter-1 verdict against its own Chapter-4 inference.

    Our verdict text is carried VERBATIM out of the catalogue-B section, so
    where it and a monthly row differ, the two sides of the disagreement are
    both the document's. This measures that directly, per event name, over
    every PRINTED row rather than over the folded windows -- a row reprinted
    with the same inference in two months is two printings of one claim, and
    both are counted here because the question is how the chapter behaves.
    """
    out = {}
    for row in MO.printed_rows():
        kind, targets, _note = MM.MAP[row.event]
        if kind != MM.B:
            continue
        ours = next((ALL_RULES[t].verdict_text
                     for t in targets if t in ALL_RULES
                     and ALL_RULES[t].verdict_text), None)
        d_ours, d_theirs = direction(ours), direction(row.inference)
        if d_ours is None or d_theirs is None or "both" in (d_ours, d_theirs):
            continue
        rec = out.setdefault(row.event, {
            "rule_verdict": ours, "rule_direction": d_ours,
            "agree": 0, "contradict": 0, "contradicting_dates": []})
        if d_ours == d_theirs:
            rec["agree"] += 1
        else:
            rec["contradict"] += 1
            rec["contradicting_dates"].append(
                f"{row.start_date} ({row.month_name[:3]}): {row.inference}")
    contradicting = {k: v for k, v in out.items() if v["contradict"]}
    return {
        "event_names_compared": len(out),
        "event_names_with_a_contradicting_row": len(contradicting),
        "printed_rows_agreeing": sum(v["agree"] for v in out.values()),
        "printed_rows_contradicting": sum(v["contradict"] for v in out.values()),
        "detail": contradicting,
    }


def extras(results, by_rule) -> dict:
    """Days we emit that the source's chapter does not print for that rule."""
    claimed = collections.defaultdict(set)
    for r in results:
        if not r["start"]:
            continue
        start = dt.date.fromisoformat(r["start"])
        end = dt.date.fromisoformat(r["end"]) if r["end"] else start
        for t in r["firing_targets"]:
            d = start
            while d <= end:
                claimed[t].add(d)
                d += dt.timedelta(days=1)

    mapped_rules = {t for _k, ts, _n in MM.MAP.values() for t in ts
                    if t in ALL_RULES}
    per_rule = collections.Counter()
    per_rule_runs = collections.Counter()
    per_family = collections.Counter()
    per_family_runs = collections.Counter()
    per_weekday = collections.Counter()
    per_month = collections.Counter()
    total = 0
    total_runs = 0
    for rid in sorted(mapped_rules):
        ours = by_rule.get(rid, {}).get(VENUE, set())
        extra = sorted(d for d in ours if d not in claimed.get(rid, set()))
        if not extra:
            continue
        # A day count answers "how many rows do we emit"; a RUN count answers
        # "how many events do we claim". They differ by an order of magnitude
        # for a state that holds for weeks -- a combust window is one event to
        # the source and forty rows to the rule layer -- so both are reported
        # and neither is called the number.
        runs = 1 + sum(1 for a, b in zip(extra, extra[1:])
                       if (b - a).days > 1)
        per_rule[rid] = len(extra)
        per_rule_runs[rid] = runs
        fam = ALL_RULES[rid].rule_family
        per_family[fam] += len(extra)
        per_family_runs[fam] += runs
        total += len(extra)
        total_runs += runs
        for d in extra:
            per_weekday[d.strftime("%a")] += 1
            per_month[d.strftime("%b")] += 1

    unmapped_rules = sorted(
        rid for rid in by_rule
        if rid not in mapped_rules and by_rule[rid].get(VENUE))
    views = [r for r in unmapped_rules
             if ALL_RULES[r].rule_family.startswith("reference/")]
    conditions = [r for r in unmapped_rules if r not in set(views)]
    return {
        "total_extra_days_on_mapped_rules": total,
        "total_extra_runs_on_mapped_rules": total_runs,
        "per_rule": dict(per_rule.most_common()),
        "per_rule_runs": dict(per_rule_runs.most_common()),
        "per_family": dict(per_family.most_common()),
        "per_family_runs": dict(per_family_runs.most_common()),
        "per_weekday": dict(per_weekday.most_common()),
        "per_month": dict(per_month.most_common()),
        "rules_no_source_row_maps_to": len(unmapped_rules),
        "their_mumbai_days": sum(
            len(by_rule[r][VENUE]) for r in unmapped_rules),
        "of_those_reference_views": len(views),
        "of_those_conditions": len(conditions),
        "condition_rules_no_source_row_maps_to": conditions,
        "condition_rule_families": dict(collections.Counter(
            ALL_RULES[r].rule_family for r in conditions)
            .most_common()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    names = list(MO.event_names())
    missing = MM.unmapped(names)
    stale = MM.unknown(names)
    if missing or stale:
        raise SystemExit(f"map out of step with the document: "
                         f"{len(missing)} unmapped, {len(stale)} stale")

    sky, firings, by_rule = run_rules()
    rows = MO.fixture_rows()
    results = [classify(r, by_rule) for r in rows]

    outcomes = collections.Counter(r["outcome"] for r in results)
    by_kind = collections.Counter(r["kind"] for r in results)

    # By event NAME rather than by window: 54 Bhadra windows are one gap.
    per_name_outcome = {}
    for r in results:
        cur = per_name_outcome.get(r["event"])
        if cur is None or (cur != "reproduced" and r["outcome"] == "reproduced"):
            per_name_outcome[r["event"]] = r["outcome"]
    name_outcomes = collections.Counter(per_name_outcome.values())

    payload = {
        "fixture": MO.counts(),
        "astronomy": {"path": str(ASTRONOMY_2026.relative_to(ROOT)),
                      "records": sky.meta["record_count"],
                      "year": sky.meta["year"]},
        "rule_layer": {
            # All three registries, each named for what it is. The last key
            # read `config_groups_registered_not_wired` until 20-Sep-2026 --
            # six days after `verdicts.py` started firing that registry. The
            # VALUE was right throughout and the NAME asserted the opposite
            # of what the build did, which is the shape STEP4_DECISIONS
            # section 12.16 is about, in a JSON key.
            "catalogue_b_rules": len(REGISTRY),
            "config_groups": len(CONFIG_REGISTRY),
            "subtable_rules": len(SUBTABLE_REGISTRY),
            "firing_rules": len(firing_rules()),
            "firings_2026_both_venues": len(firings),
            "firings_2026_mumbai": sum(
                1 for f in firings if f.location == VENUE),
        },
        "assignment_kinds": MM.kinds(),
        "windows_by_kind": dict(by_kind.most_common()),
        "outcomes_by_window": dict(outcomes.most_common()),
        "outcomes_by_event_name": dict(name_outcomes.most_common()),
        "date_precision": {
            "on_printed_start_date": sum(1 for r in results if r["on_start"]),
            "within_one_day_of_start": sum(
                1 for r in results if r["within_one"]),
            "somewhere_in_the_printed_window": sum(
                1 for r in results if r["in_window"]),
        },
        "verdicts": verdict_compare(results),
        "source_self_consistency": source_self_consistency(),
        "extras": extras(results, by_rule),
        "rows": results,
    }

    f = payload["fixture"]
    print(f"fixture         {f['printed_rows']} printed rows -> "
          f"{f['distinct_windows']} windows, {f['distinct_event_names']} names")
    print(f"astronomy       {payload['astronomy']['records']} records "
          f"({payload['astronomy']['year']})")
    print(f"rule layer      {payload['rule_layer']['firing_rules']} firing "
          f"rules, {payload['rule_layer']['firings_2026_mumbai']} Mumbai "
          f"firings in 2026\n")
    print("windows by outcome")
    for k, v in payload["outcomes_by_window"].items():
        print(f"  {k:<22} {v:>4}")
    print("\nevent names by outcome")
    for k, v in payload["outcomes_by_event_name"].items():
        print(f"  {k:<22} {v:>4}")
    print("\ndate precision (of the distinct windows)")
    for k, v in payload["date_precision"].items():
        print(f"  {k:<34} {v:>4}")
    print("\nverdicts, where both sides produced something")
    for k, v in payload["verdicts"]["counts"].items():
        print(f"  {k:<36} {v:>4}")
    sc = payload["source_self_consistency"]
    print(f"\nthe document against itself: {sc['printed_rows_agreeing']} "
          f"printed rows agree with their own section's verdict, "
          f"{sc['printed_rows_contradicting']} contradict it "
          f"({sc['event_names_with_a_contradicting_row']} of "
          f"{sc['event_names_compared']} event names)")
    for name, d in sc["detail"].items():
        print(f"  {name[:44]:<44} rule says {d['rule_direction']}: "
              f"{d['agree']} agree / {d['contradict']} contradict")

    ex = payload["extras"]
    print(f"\nextra days on mapped rules: "
          f"{ex['total_extra_days_on_mapped_rules']} "
          f"({ex['total_extra_runs_on_mapped_rules']} runs)")
    for k, v in list(ex["per_family"].items())[:12]:
        print(f"  {k:<30} {v:>5} days  {ex['per_family_runs'][k]:>4} runs")
    print(f"weekday spread: {ex['per_weekday']}")
    print(f"rules no source row maps to: {ex['rules_no_source_row_maps_to']} "
          f"({ex['their_mumbai_days']} Mumbai days) -- "
          f"{ex['of_those_reference_views']} reference views, "
          f"{ex['of_those_conditions']} conditions")
    for k, v in ex["condition_rule_families"].items():
        print(f"    {k:<30} {v:>3}")

    if args.json:
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nfull result -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
