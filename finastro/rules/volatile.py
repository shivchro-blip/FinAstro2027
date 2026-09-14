"""Batch 4 -- B70, ported as a recorded absence and deliberately not reconstructed.

The "Big Volatile - Major Turning Days" list is the one section in catalogue B
whose condition cannot be recovered, and the decision not to try is the whole
content of this module.

**Why it cannot be reconstructed.** The section prints a table whose date cells
hold 51 dates, and its entire statement of method is one remark: *"These dates
have been sorted on multiple parameters, applies to Stock Markets / Commodities /
Currencies"*. It names none of the parameters and gives no weights. Everything
the project could check was checked before registering this, and four candidate
discriminators were tested and rejected:

* the dates are not lunations -- they do not fall on the new or full Moon;
* they are not stations -- none coincides with a planet turning;
* they are not sign ingresses;
* they are not the inner-planet conjunctions or the slow-pair aspects.

All 51 dates DO carry at least one major configuration, which is exactly what
makes the list over-determined: with that many candidate parameters and no
stated weighting, a rule fitted to the 51 dates would reproduce them and predict
nothing. That is a description of the fitted set, not a recovery of the source's
rule, and emitting it as the source's list would launder an artefact of our own
fitting into a claim about the page.

**So what is emitted is the absence.** The rule is registered `blocked` with
`source_selection_rule` named as the missing input and `data_certainty C` -- the
grade the config's own vocabulary reserves for "depends on an undocumented source
rule". It is counted, it emits nothing, and its zero is pinned in the harness by
name with this reason, so it can never be read as a quiet year.

This is the same discipline the project applies everywhere else: a missing input
is named rather than approximated, and a reconstruction that would look like a
transcription is not emitted at all.
"""
from __future__ import annotations

from .base import blocked
from .catalogue import B
from ..events import GROUND_UNDOCUMENTED

#: The section's own statement of method, verbatim. This string is what makes
#: the rule unrecoverable, and it is carried as the condition because it is the
#: closest thing to a condition the section prints.
_B70_METHOD = B(70).remarks[0]

#: The one printed row that needed the source's own footnote.
_B70_TYPO = B(70).paras[0]

blocked(
    id="b070_big_volatile_major_turning_days",
    section=B(70),
    rule_family="calendar/curated_list",
    condition_text=B(70).title,
    condition_from="title",
    inputs=("source_selection_rule",),
    missing_inputs=(
        'the selection rule itself. The section states only that its dates '
        '"have been sorted on multiple parameters" and names none of them and '
        "no weighting; four candidate discriminators (lunation, station, sign "
        "ingress, inner-planet conjunction or slow-pair aspect) were tested and "
        "rejected, and all 51 dates carry at least one major configuration, so "
        "the list is over-determined and a fitted reconstruction would describe "
        "our fit rather than the source's rule",
    ),
    flags=("recorded_absence_not_reconstructed",),
    certainty_ground=GROUND_UNDOCUMENTED,
    notes="Ported as a recorded absence with the section's existing certainty C, "
          "deliberately not reconstructed. The table's date cells hold 51 dates. "
          "The section's method remark is carried verbatim as the condition, and "
          "its footnote -- one cell printed as 07-Aug-62 and footnoted as likely "
          "07-Aug-26 -- is carried as the record of the source's own typo. "
          "Nothing is emitted: a candidate list would be this layer's inference "
          "wearing the page's authority.",
)
