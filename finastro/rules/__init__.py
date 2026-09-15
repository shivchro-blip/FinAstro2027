"""The rule layer -- the 141 Chapter-1 source sections, ported.

Importing this package registers every rule. The batch modules are imported in
the order the port was carried out, and each is a section type rather than a
convenience grouping:

    visibility      the five Combust Rise Cycles and the two Mercury sections
    colocation      conjunctions, oppositions, same-sign and same-nakshatra
    panchang_rules  weekday, tithi, yoga and the lunar-calendar families
    shar            B118 and B119 -- Shar, the ecliptic latitude sign
    apsides         the apsides, the hemispheres and Kaal Sarp Yog
    pairs           the retrograde pairs and the nakshatra-residency singles
    volatile        B70, recorded as an absence and deliberately not fitted
    vedha           Shar, Speed and Vedh, and the remaining reference tables

A rule states a **condition** and, where the section prints one, a **verdict**
carried verbatim. Nothing here generates a verdict of its own, and nothing here
raises a confidence: `label_scheme_signoff` is still open in
`config/conventions.yaml` and blocks the emission of a verdict record. What
this package produces is the condition layer that record will be built on --
dated, per location, and traceable to a page.

Financial astrology is a speculative interpretive framework. Nothing this
package produces is investment advice.
"""
from __future__ import annotations

import collections

from .base import (FIRING_STATUSES, Firing, LOCATIONS, REGISTRY, Rule,
                   STATUS_AMBIGUOUS, STATUS_BLOCKED, STATUS_EXECUTABLE,
                   STATUS_RESOLVED, counts_by_rule, fire)
from .catalogue import B, CATALOGUE_B_SIZE, SECTIONS, Section

from . import visibility          # noqa: F401  -- registers batch 1
from . import colocation          # noqa: F401  -- registers batch 2
from . import panchang_rules      # noqa: F401  -- registers batch 3
from . import shar                # noqa: F401  -- registers batch 4 (Shar)
from . import apsides             # noqa: F401  -- registers the apsides batch
from . import pairs               # noqa: F401  -- registers the pairs batch
from . import volatile            # noqa: F401  -- registers B70's recorded absence
from . import vedha               # noqa: F401  -- registers the Vedha family
from . import ref_tables          # noqa: F401  -- reference views + unreached sections

# The instrument configuration blocks (gold, silver, sugar). Imported so the
# port is live everywhere the rule layer is, and registered into its OWN
# registry: these are not catalogue-B sections and `sections_ported()` must
# not be able to see them.
from . import config_rules        # noqa: F401  -- registers the 58 config groups
from .config_rules import CONFIG_REGISTRY   # noqa: F401

BATCHES = ("visibility", "colocation", "panchang_rules", "shar", "apsides",
           "pairs", "volatile", "vedha", "ref_tables")

#: The configuration port, counted and reported separately from BATCHES
#: throughout. Catalogue B's denominator is 141 sections; this one's is 58
#: groups, and the two have never been the same number.
CONFIG_BATCH = "config_rules"


def by_status(status: str) -> list[Rule]:
    return [r for r in REGISTRY if r.status == status]


def executable() -> list[Rule]:
    return by_status(STATUS_EXECUTABLE)


def resolved_ambiguities() -> list[Rule]:
    """Rules that fire on a reading we supplied. Reported separately, always.

    They are never counted in with `executable()`. A resolved rule's dated rows
    are as computable as any other rule's, and that is exactly why the fact
    that a word in its condition came from us has to be carried where a reader
    trips over it rather than left to be discovered.
    """
    return by_status(STATUS_RESOLVED)


def firing_rules() -> list[Rule]:
    """Every rule that can produce a dated row, whatever the reading's origin."""
    return [r for r in REGISTRY if r.status in FIRING_STATUSES]


def sections_ported() -> set[int]:
    """Catalogue-B numbers touched by at least one rule, whatever its status."""
    return {r.catalogue_b for r in REGISTRY}


def sections_by_status() -> dict[str, set[int]]:
    out: dict[str, set[int]] = collections.defaultdict(set)
    for r in REGISTRY:
        out[r.status].add(r.catalogue_b)
    return dict(out)


def rules_by_section() -> dict[int, list[Rule]]:
    out: dict[int, list[Rule]] = collections.defaultdict(list)
    for r in REGISTRY:
        out[r.catalogue_b].append(r)
    return dict(out)


def zero_firing(firings: list[Firing]) -> list[Rule]:
    """Executable rules that never fire in the generated year.

    Surfaced rather than tolerated. A rule that never fires is either correct --
    the configuration genuinely does not occur in 2027 -- or a porting error,
    and the two look identical from the outside until someone checks.
    """
    fired = {f.rule_id for f in firings}
    return [r for r in firing_rules() if r.id not in fired]
