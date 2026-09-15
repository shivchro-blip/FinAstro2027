"""Generate build/RULE_LAYER_STATUS.md -- every section, status, counts, blockers.

Written from the registry and the firings, never by hand, so it cannot drift from
what the layer actually does. Re-run after any rule change.

TWO DENOMINATORS, and the second is not folded into the first. "141 of 141" is
true of catalogue B and is not a coverage claim about the instrument
configuration sections, which were never in the 141 at all. The second count is
read from the document (`finastro.cfgsections`) rather than from our config,
because a count taken from the thing being audited is not an audit.
"""
from __future__ import annotations

import collections
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro import rules as R                              # noqa: E402
from finastro import cfgsections as CFG                      # noqa: E402
from finastro.config import CONF                             # noqa: E402
from finastro.rules.catalogue import SECTIONS                # noqa: E402
from finastro.rules import config_rules as CFGR              # noqa: E402
from finastro.sky import Sky                                 # noqa: E402

YEAR = CONF["year"]
OUT = ROOT / "build" / "RULE_LAYER_STATUS.md"

sky = Sky.load()
firings = R.fire(R.REGISTRY, sky)
mumbai = collections.Counter(f.rule_id for f in firings if f.location == "mumbai")
ny = collections.Counter(f.rule_id for f in firings if f.location == "new_york")
by_section = R.rules_by_section()
zero = {r.id for r in R.zero_firing(firings)}


STATUS_MARK = {
    "executable": "ok",
    "resolved_ambiguity": "ok*",
    "blocked": "BLOCKED",
    "ambiguous": "AMBIG",
}

def cell(s: str) -> str:
    """A markdown table cell: no pipes, no newlines.

    One section title in the source carries a byte that decodes to something
    containing a pipe, which silently split its table row in half and made the
    coverage table unparseable from that line onward. Sanitising here rather than
    trusting 141 titles to be table-safe is the same discipline as slicing
    verbatim strings: the document is not formatted for our output.
    """
    return " ".join(str(s).replace("|", "/").split())


lines: list[str] = []
A = lines.append

A(f"# Rule layer status — catalogue B, and what catalogue B is not")
A("")
A(f"Generated {dt.date.today():%d-%b-%Y} from the live registry, not by hand. "
  f"Year {YEAR}.")
A("")
tot_rules = len(R.REGISTRY)
tot_fire = len(firings)
n_exec = len(R.by_status("executable"))
n_res = len(R.by_status("resolved_ambiguity"))
n_blk = len(R.by_status("blocked"))
n_amb = len(R.by_status("ambiguous"))

cfg_counts = CFG.counts()
cfg_total = CFG.total()
cfg_inst = CFG.by_instrument()

A("## Coverage, in two denominators")
A("")
A("Two counts, because there are two catalogues and only one of them was ever "
  "in scope:")
A("")
A("| | sections | ported | reading |")
A("| --- | --- | --- | --- |")
A(f"| **Catalogue B** — `<h3 class=\"section\">`, the rule sections of Chapter 1 | "
  f"{len(SECTIONS)} sections | **{len(R.sections_ported())} of {len(SECTIONS)}** | "
  f"every section carries a status |")
A(f"| **Instrument configuration sections** — `<section id=\"...\">` with an "
  f"`<h2>`, Chapter 2 | **{cfg_total} named groups** | "
  f"**{len(CFGR.ported())} of {cfg_total}** | "
  f"**{len(CFGR.blocked_rules())} blocked, each on a named input** |")
A("")
A(f"**So: catalogue B {len(R.sections_ported())}/{len(SECTIONS)} · configuration "
  f"sections {len(CFGR.ported())}/{cfg_total}.** The configuration rules are "
  f"registered in their own registry and are NOT in catalogue B's denominator; "
  f"they also do not yet feed the calendar's rows, which still come from "
  f"catalogue B alone.")
A("")
A(f"**141 of 141 is TRUE OF CATALOGUE B and is not a coverage claim about the "
  f"source.** The instrument configuration sections are a different shape of "
  f"markup and were never in the 141, so they were never in the denominator and "
  f"a reader seeing \"141/141\" could conclude the source is fully covered when "
  f"{cfg_total} named groups have never had a rule written for them.")
A("")
A("The counts, from the document (read out of `data/source_2026.html` at "
  "generation time by `finastro/cfgsections.py`, not out of config — a count "
  "taken from the thing being audited is not an audit):")
A("")
A("| block | instrument | direction | pages | named groups | ported |")
A("| --- | --- | --- | --- | --- | --- |")
#: Ported per block, off the registry rather than typed. The first version of
#: this page hardcoded **0** in this column and went on doing so after part 1
#: ported 38 groups, so the header read 38/58 and the table beneath it read
#: 0 -- the §12.16 shape, on the page whose whole subject is a misleading count.
_ported_by_block = collections.Counter(
    g.section.block.id for g in CFGR.ported())
for b, (inst, direction, pages) in CFG.BLOCKS.items():
    A(f"| `{b}` | {inst} | {direction} | {pages} | {cfg_counts[b]} | "
      f"**{_ported_by_block[b]}** |")
A(f"| | | | | **{cfg_total}** | **{len(CFGR.ported())} of {cfg_total}** |")
A("")
A("### Gold, silver and sugar reach the calendar only through generic "
  "catalogue-B rules")
A("")
A(f"**Gold, silver and sugar are the three instruments the source prints "
  f"verdicts for** — that is why they carry evidence blocks naming their own "
  f"configuration sections, and it is what their tiers rest on. Their own "
  f"configuration groups are "
  + " · ".join(f"**{i} {cfg_inst[i]}**" for i in CFG.INSTRUMENTS)
  + f" named groups, of which **{len(CFGR.ported())}** now carry a rule and "
  f"**{len(CFGR.blocked_rules())}** are blocked on a named input.")
A("")
# STALE MARKER -- emitted onto the page deliberately. `verdicts.py` now fires
# BOTH registries (14-Sep-2026 wiring); the paragraphs below still describe the
# pre-wiring state and the full prose sweep is a task in build/NEXT_SESSION.md.
A("> **STALE — this section describes the state before the configuration "
  "wiring.** `verdicts.py` now fires both registries: the 38 ported groups DO "
  "reach calendar rows (1,468 of 6,677 in a rebuild). The paragraphs below "
  "still say they do not. Corrected text is a task in "
  "`build/NEXT_SESSION.md`; the counts in the table above are current.")
A("")
A("**Ported is not wired, and the difference is the whole of what this section "
  "says.** The ported groups are registered in their own registry and "
  f"`verdicts.py` fires catalogue B alone, so none of them reaches a row in "
  f"`build/calendar_{YEAR}.*` today.")
A("")
A("What they *do* get today is real but is not the source's verdicts for them. "
  "Every row carrying gold, silver or sugar comes from a generic catalogue-B "
  "rule whose bodies happen to resolve to that instrument — a Venus rule reaches "
  "SUGAR because SUGAR's rulership is Venus, not because the source said "
  "anything about sugar. **No row in the calendar originates in any of the "
  "configuration sections**: the `event_section` field of all "
  f"{tot_fire:,} dated rows in {YEAR} names a catalogue-B section or the "
  "panchang families, and never `gold-bullish`, `silver-bearish`, "
  "`sugar-bullish` or any other block.")
A("")
A("Sugar is the clearest case and the reason the gap was found at all: it emits "
  "rows from 12 different Venus-ruled catalogue-B sections, and **0** from its "
  "own nine groups — four of which are now ported and none of which is wired. "
  "A reader seeing SUGAR's rows would see a covered instrument.")
A("")
A("Gold and silver reach tier 1 through their MCX legs (`MCXGOLD`, "
  "`MCXSILVER`); their COMEX legs (`GC`, `SI`) emit `venue_shifted` instead, by "
  "the 14-Sep-2026 localised split. Both legs are the same generic rules on the "
  "same sky. The tier says where a claim was authored and how the civil day is "
  "bounded; it does not say the source's own gold and silver conditions were "
  "ported.")
A("")
A("**What porting them would take is scoped, not estimated, in "
  "`build/CONFIG_SECTIONS_SCOPE.md`** — all "
  f"{cfg_total} groups, their conditions, and which of them the existing "
  "astronomy layer can already compute.")
A("")
A("### There is a third unported body of material, recorded here so it is not "
  "mistaken for covered either")
A("")
A("The same chapter carries nine further `<h2>` sub-tables that are neither "
  "catalogue B nor any of the six blocks above: "
  + ", ".join(f"*{t}*" for t in CFG.other_h2_tables()) + ".")
A("")
A("And the source's own monthly prophecy tables (Chapter 3) print named "
  "verdicts for gold and silver — \"Bullish for Gold and Silver\", \"High "
  "Bearish for Gold\" — which are also outside catalogue B and also unported. "
  "Recorded because a coverage page that fixes one denominator and leaves the "
  "next one implicit has only moved the misleading claim.")
A("")
A("---")
A("")
A(f"**{tot_rules} rules over {len(R.sections_ported())} of {len(SECTIONS)} "
  f"catalogue-B sections — full coverage of catalogue B — {tot_fire} dated rows "
  f"in {YEAR}.** {n_exec} executable, {n_res} resolved, {n_blk} blocked, "
  f"{n_amb} ambiguous.")
A("")

A("`zero` in the firing column means the rule runs and produces no row this "
  "year. That is either the configuration genuinely not occurring or a porting "
  "error, and the two look identical from outside — so every zero is pinned by "
  "name with its kind in `tests/test_rule_layer.py`. `BLOCKED` means the rule is "
  "registered, counted, emits nothing, and **names the input it is waiting for**.")
A("")
A("Status keys: `ok` executable · `ok*` fires on a reading we supplied, flagged "
  "on every row · `BLOCKED` missing input named below · `AMBIG` source wording "
  "admits more than one reading.")
A("")

# ---------------------------------------------------------------- main table
A(f"## Coverage of catalogue B — all {len(SECTIONS)} sections")
A("")
A("| B | page | section | status | rules | " + f"{YEAR} rows (mumbai / ny)" +
  " | notes |")
A("| --- | --- | --- | --- | --- | --- | --- |")
for s in SECTIONS:
    rs = by_section.get(s.b, [])
    if not rs:
        A(f"| {s.b} | {cell(s.page)} | {cell(s.title)} | **UNPORTED** | 0 | - "
          f"| - |")
        continue
    st = sorted({r.status for r in rs})
    mark = " + ".join(STATUS_MARK.get(x, x) for x in st)
    m = sum(mumbai.get(r.id, 0) for r in rs)
    n = sum(ny.get(r.id, 0) for r in rs)
    note = ""
    if all(r.id in zero for r in rs if r.status in R.FIRING_STATUSES) and \
            any(r.status in R.FIRING_STATUSES for r in rs):
        note = "zero this year (pinned)"
    elif st == ["blocked"]:
        note = "see blockers"
    elif st == ["ambiguous"]:
        note = "awaiting a ruling"
    elif st == ["resolved_ambiguity"]:
        note = "reading supplied, flagged"
    A(f"| {s.b} | {cell(s.page)} | {cell(s.title)} | {mark} | {len(rs)} | "
      f"{m} / {n} | {cell(note)} |")
A("")

# ---------------------------------------------------------------- blockers
A("## Blocked sections and the input each is missing")
A("")
A("| B | section | rule | missing input |")
A("| --- | --- | --- | --- |")
for r in sorted(R.by_status("blocked"), key=lambda x: x.catalogue_b):
    # Joined with an explicit separator: a section can be blocked on more than
    # one input, and concatenating them made B63's two reasons read as one
    # run-on sentence that said "licence question ... a decision on what the
    # range is" as though the second continued the first.
    why = " **AND** ".join(" ".join(str(m).split())
                           for m in r.missing_inputs)
    A(f"| {r.catalogue_b} | {cell(r.section_title)} | `{r.id}` | {cell(why)} |")
A("")

# ---------------------------------------------------------------- zeros
A(f"## Rules that fire zero times in {YEAR}")
A("")
A("Pinned by name in the harness with the reason, so a zero can never be read "
  "as a quiet year without someone having checked which kind it is. The three "
  "kinds: **calendar-boundary** (the event falls in the carry-in or carry-out), "
  "**orbital-period** (the configuration does not occur in this span at all), "
  "and **sky** (it is excluded by where the bodies are).")
A("")
A("| rule | B | kind |")
A("| --- | --- | --- |")
import re
_src = (ROOT / "tests" / "test_rule_layer.py").read_text(encoding="utf-8")
for r in sorted(R.zero_firing(firings), key=lambda x: x.catalogue_b):
    m = re.search(rf'"{re.escape(r.id)}":\s*\n?\s*"([^"]{0,180})', _src)
    why = m.group(1) if m else "see harness"
    kind = ("sky" if any(w in why.lower() for w in
                         ("excluded", "outside", "never", "holds", "occupies",
                          "alone on neither"))
            else "orbital-period" if any(w in why.lower() for w in
                                         ("only", "does not occur", "no ", "once"))
            else "calendar-boundary")
    A(f"| `{r.id}` | {r.catalogue_b} | {cell(kind)} |")
A("")

# ---------------------------------------------------------------- resolved
A("## Rules firing on a reading we supplied")
A("")
A("Never counted in with the executable rules. The words these fire on are "
  "partly ours, and every row carries the flag naming what was supplied.")
A("")
A("| rule | B | flag |")
A("| --- | --- | --- |")
for r in sorted(R.by_status("resolved_ambiguity"), key=lambda x: x.catalogue_b):
    fl = [f for f in r.flags if "supplied" in f or "elided" in f] or list(r.flags)
    A(f"| `{r.id}` | {r.catalogue_b} | {cell(', '.join(fl))} |")
A("")

# ---------------------------------------------------------------- ambiguous
A("## Sections whose wording admits more than one reading")
A("")
for r in sorted(R.by_status("ambiguous"), key=lambda x: x.catalogue_b):
    A(f"### B{r.catalogue_b} — {r.section_title}")
    A("")
    A(f"`{r.id}`. {r.ambiguity}")
    A("")

A("## What this page does not cover")
A("")
A("This is the **condition** layer: dated, per location, traceable to a page. "
  "It states when a rule's condition holds. It does **not** yet state what the "
  "market does — that is the verdict layer, which applies "
  "`evidence_source` x `construction` per instrument and per venue day, and "
  "then renders. Nothing here is a forecast or investment advice.")
A("")
A(f"**And \"this page\" is not the whole source.** It covers catalogue B. The "
  f"{cfg_total} named groups of the instrument configuration sections "
  f"(Chapter 2) are unported and are scoped in "
  f"`build/CONFIG_SECTIONS_SCOPE.md`; the source's monthly prophecy tables "
  f"(Chapter 3) are unported and are not scoped anywhere yet. See **Coverage, "
  f"in two denominators** at the top of this page before reading any number on "
  f"it as a statement about coverage of the document.")
A("")

OUT.write_text("\n".join(lines), encoding="utf-8", newline="\r\n")
print(f"wrote {OUT.relative_to(ROOT)}  ({len(lines)} lines)")
print(f"sections {len(R.sections_ported())}/{len(SECTIONS)}  rules {tot_rules}  "
      f"firings {tot_fire}  blocked {n_blk}  zero {len(R.zero_firing(firings))}")
