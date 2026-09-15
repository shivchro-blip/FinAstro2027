"""The 2026 monthly-calendar fixture, pinned.

What is pinned here is the FIXTURE and the MAP -- both derived from the
document -- and never the match result. The match result is what the fixture
measures and it is expected to move: wiring the configuration port changes it
on purpose, and a test that froze it would have to be edited every time the
thing it measures improves, which makes it a record of edits rather than a
check.

Two properties are worth a harness of their own:

* the denominators come out of `data/source_2026.html` unchanged. A silent
  re-parse that dropped rows would move a reproduction rate without moving
  anything visible -- the §12.16 shape exactly.
* `monthlymap.py` and the document agree in BOTH directions, and every rule id
  the map names exists. A stale entry is as much a defect as a missing one.

Run:  python tests/test_monthly_fixture.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from finastro import monthly2026 as MO       # noqa: E402
from finastro import monthlymap as MM        # noqa: E402
from finastro.rules import REGISTRY, CONFIG_REGISTRY   # noqa: E402

PASS, FAIL = "PASS", "FAIL"
_results: list = []


def record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, PASS if ok else FAIL, detail))


#: Read off the document on 14-Sep-2026. Every one of these is a count of
#: something the source prints, not of something we emit.
EXPECTED = {
    "printed_rows": 407,
    "distinct_windows": 354,
    "carry_over_copies": 53,
    "reprinted_windows": 34,
    "distinct_event_names": 147,
    "windows_with_varying_inference": 2,
    "instants": 136,
    "spans": 218,
}


def test_denominators():
    got = MO.counts()
    for key, want in EXPECTED.items():
        record(f"fixture: {key} == {want}", got[key] == want,
               f"got {got[key]}")


def test_twelve_blocks_each_with_rows():
    blocks = MO.blocks()
    record("fixture: twelve month blocks", len(blocks) == 12,
           str(len(blocks)))
    empty = [b.name for b in blocks if not b.rows]
    record("fixture: no month block is empty", not empty, str(empty))
    # A blank table and a month with nothing in it are the same bytes -- the
    # first instance in §12.16. Each block also carries the source's own
    # summary line, so an empty one would be visible here too.
    no_summary = [b.name for b in blocks if not b.summary]
    record("fixture: every block carries its summary line", not no_summary,
           str(no_summary))


def test_map_agrees_with_the_document_both_ways():
    names = list(MO.event_names())
    missing = MM.unmapped(names)
    stale = MM.unknown(names)
    record("map: every printed event name is assigned", not missing,
           f"{len(missing)}: {missing[:3]}")
    record("map: no assignment the document does not print", not stale,
           f"{len(stale)}: {stale[:3]}")
    record("map: 147 assignments", len(MM.MAP) == 147, str(len(MM.MAP)))


def test_every_target_exists():
    ids = {r.id for r in REGISTRY} | {g.id for g in CONFIG_REGISTRY}
    bad = [(name, t) for name, (kind, targets, _n) in MM.MAP.items()
           if kind in (MM.B, MM.CFG) for t in targets if t not in ids]
    record("map: every rule id it names is registered", not bad, str(bad[:3]))

    # A `CFG` assignment must name a CONFIGURATION group and a `B` assignment a
    # catalogue-B rule. Crossing the two would make a wiring gap look like a
    # rule gap, which is the one distinction this fixture exists to keep.
    cfg_ids = {g.id for g in CONFIG_REGISTRY}
    b_ids = {r.id for r in REGISTRY}
    crossed = [
        (name, t)
        for name, (kind, targets, _n) in MM.MAP.items() for t in targets
        if (kind == MM.CFG and t not in cfg_ids)
        or (kind == MM.B and t not in b_ids)]
    record("map: B and CFG targets are not crossed", not crossed,
           str(crossed[:3]))


def test_unassigned_names_carry_a_reason():
    silent = [name for name, (kind, targets, note) in MM.MAP.items()
              if kind in (MM.NO_SECTION, MM.SERIES_NO_RULE, MM.SUBTABLE)
              and not note.strip()]
    record("map: every unclaimed name states why", not silent,
           str(silent[:3]))


def main() -> int:
    for fn in (test_denominators, test_twelve_blocks_each_with_rows,
               test_map_agrees_with_the_document_both_ways,
               test_every_target_exists,
               test_unassigned_names_carry_a_reason):
        fn()
    width = max(len(n) for n, _s, _d in _results)
    for name, status, detail in _results:
        line = f"{status}  {name.ljust(width)}"
        print(line if status == PASS else f"{line}   {detail}")
    failed = sum(1 for _n, s, _d in _results if s == FAIL)
    print(f"\n{len(_results) - failed}/{len(_results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
