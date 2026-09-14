"""Unit test for the node-anchor fallback branch, which the real span cannot reach.

`lord_relationship` returns `(None, None)` when the node's sign-period opened
before the span did, and a record built in that condition carries a null
`lord_relationship` plus the `no_anchor_ingress_in_span` flag. Under the
shipped span that branch is dead: SPAN_START is 01-Dec-2026 IST and the mean
node changes sign on 05-Dec-2026, so every node record in the generated year
anchors. The build-output harness checks the branch over an empty set, which is
not coverage -- a refactor that reintroduced an instant-evaluated fallback
would leave every check green.

So this file drives the branch directly, with a synthetic span floor placed
AFTER the 05-Dec-2026 ingress. It is deliberately separate from
tests/test_2027_astronomy.py: that harness asserts things about
build/astronomy_2027.json and needs the build to have run, while this one tests
a code path no build output can contain.

Run:  python tests/test_node_anchor_unit.py      (no build required)
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from finastro import ephem, events as ev            # noqa: E402
from finastro.events import SPAN_START, SPAN_END    # noqa: E402
from finastro.timezones import IST, UTC             # noqa: E402

PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, PASS if ok else FAIL, detail))


#: The mean node's sign ingress that the shipped span anchors on. The synthetic
#: floor sits after it, so the node's current sign-period opens outside the
#: synthetic span and no anchor exists -- the same shape as a period that began
#: before the real carry-in.
REAL_ANCHOR = dt.datetime(2026, 12, 5, tzinfo=IST).astimezone(UTC)

#: Floor placed a month past that ingress. The mean node changes sign roughly
#: every 18.6 months, so there is no ingress between this floor and the probe
#: instant -- the emptiness is structural, not a coincidence of one ephemeris.
SYNTH_START = dt.datetime(2027, 1, 1, tzinfo=IST).astimezone(UTC)
SYNTH_END = SPAN_END

#: Probed right after the synthetic floor, so the answer cannot depend on a
#: later ingress drifting across the boundary under a backend swap.
WHEN = dt.datetime(2027, 1, 2, 12, 0, tzinfo=IST).astimezone(UTC)


def test_no_anchor_returns_null_pair() -> None:
    for node in ephem.NODES:
        rel, anchor = ephem.lord_relationship(WHEN, node, SYNTH_START, SYNTH_END)
        record(f"{node}: lord_relationship is (None, None) with no anchor in span",
               (rel, anchor) == (None, None), f"got {(rel, anchor)!r}")
        record(f"{node}: node_anchor itself finds nothing in the synthetic span",
               ephem.node_anchor(WHEN, node, SYNTH_START, SYNTH_END) is None, "")


def test_positive_control() -> None:
    """The same instant under the real span must resolve, or the test proves nothing.

    Without this, a `lord_relationship` broken into always returning None would
    pass the branch test above.
    """
    for node in ephem.NODES:
        rel, anchor = ephem.lord_relationship(WHEN, node, SPAN_START, SPAN_END)
        ok = rel is not None and anchor is not None
        record(f"{node}: same instant under the real span does anchor", ok,
               f"{rel} at {anchor.astimezone(IST):%d-%b-%Y %H:%M} IST" if ok
               else f"got {(rel, anchor)!r}")
        if ok:
            record(f"{node}: real-span anchor is the 05-Dec-2026 ingress",
                   anchor.astimezone(IST).date() == REAL_ANCHOR.astimezone(IST).date(),
                   f"{anchor.astimezone(IST):%d-%b-%Y %H:%M} IST")


def test_record_built_with_no_anchor_is_null_and_flagged() -> None:
    """A record assembled while the span floor sits after the ingress.

    `events.positional` reads the span from module scope, so the floor is moved
    on the module for the duration of the call and restored afterwards. That is
    the only way to reach the branch: the constant is imported by the build
    script precisely so both layers cannot disagree about it.
    """
    saved = ev.SPAN_START
    try:
        ev.SPAN_START = SYNTH_START
        astro, flags = ev.positional(WHEN, "Rahu")
        rec = ev.build("sign_ingress", "node_journey", ["Rahu"], "instant",
                       WHEN, astro,
                       ev.qa_for(WHEN, "B", flags=flags)).as_dict()
    finally:
        ev.SPAN_START = saved

    record("record carries lord_relationship = null",
           rec["astronomy"]["lord_relationship"] is None,
           repr(rec["astronomy"]["lord_relationship"]))
    record(f"record carries the {ephem.NO_ANCHOR_FLAG} flag",
           ephem.NO_ANCHOR_FLAG in rec["qa"]["flags"],
           f"flags: {rec['qa']['flags']}")
    # The node still has no dignity: the null above is the Relationship column
    # being unrecoverable, not dignity leaking in to fill the hole.
    record("record still carries dignity = null for a node",
           rec["astronomy"]["dignity"] is None,
           repr(rec["astronomy"]["dignity"]))


def test_real_span_record_is_not_flagged() -> None:
    """Control for the record layer, mirroring the positive control above."""
    astro, flags = ev.positional(WHEN, "Rahu")
    record("under the real span the same record is neither null nor flagged",
           astro.lord_relationship is not None
           and ephem.NO_ANCHOR_FLAG not in flags,
           f"{astro.lord_relationship!r}, flags: {flags}")


def main() -> int:
    print(f"ephemeris backend: {ephem.init()}")
    print(f"synthetic span floor: {SYNTH_START.astimezone(IST):%d-%b-%Y %H:%M} IST"
          f"  (real: {SPAN_START.astimezone(IST):%d-%b-%Y %H:%M} IST)\n")
    test_no_anchor_returns_null_pair()
    test_positive_control()
    test_record_built_with_no_anchor_is_null_and_flagged()
    test_real_span_record_is_not_flagged()

    width = max(len(n) for n, _, _ in _results)
    failed = 0
    for name, status, detail in _results:
        failed += status == FAIL
        print(f"[{status}] {name.ljust(width)}  {detail}")
    print(f"\n{len(_results) - failed}/{len(_results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
