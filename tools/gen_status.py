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
from finastro.rules import subtables as SUBR                 # noqa: E402
from finastro.sky import Sky                                 # noqa: E402
from finastro.verdicts import build_verdicts                 # noqa: E402

YEAR = CONF["year"]
OUT = ROOT / "build" / "RULE_LAYER_STATUS.md"

sky = Sky.load()
firings = R.fire(R.REGISTRY, sky)
mumbai = collections.Counter(f.rule_id for f in firings if f.location == "mumbai")
ny = collections.Counter(f.rule_id for f in firings if f.location == "new_york")
by_section = R.rules_by_section()
zero = {r.id for r in R.zero_firing(firings)}

# THE ROWS, not the firings, and from the renderer's own function rather than
# from build/calendar_YYYY.json. `firings` above is catalogue B alone -- it is
# what the section table is built from and it stays that way -- so every
# statement on this page about what reaches the CALENDAR is measured here
# instead. A page that described the wiring from a catalogue-B firing count
# could only ever describe the state before it.
_verdicts = build_verdicts(sky)
cfg_rows = [v for v in _verdicts if v.rule_id.startswith("cfg_")]
sub_rows = [v for v in _verdicts if v.rule_id.startswith("sub_")]
# CATALOGUE B BY EXCLUDING EVERY OTHER REGISTRY BY NAME, not by excluding the
# one that happened to exist. This read `not startswith("cfg_")` until
# 20-Sep-2026, when the sub-table registry landed and its rows were counted as
# catalogue B on this page -- a correct count of the wrong set, and the
# fourth place in the build where "not configuration" was standing in for
# "catalogue B". The prefixes are listed so a fourth registry has to be added
# here rather than being silently absorbed.
_OTHER_REGISTRY_PREFIXES = ("cfg_", "sub_")
cat_b_rows = [v for v in _verdicts
              if not v.rule_id.startswith(_OTHER_REGISTRY_PREFIXES)]
assert len(cat_b_rows) + len(cfg_rows) + len(sub_rows) == len(_verdicts)
cfg_rules_firing = len({v.rule_id for v in cfg_rows})
cfg_rows_by_instrument = collections.Counter(v.instrument for v in cfg_rows)
cfg_rows_by_block = collections.Counter(
    "-".join(v.rule_id.split("_")[1:3]) for v in cfg_rows)


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

A("## Coverage, in three denominators")
A("")
A("Three counts, because there are three catalogues in this document and "
  "only one of them was ever in scope:")
A("")
A("| | sections | ported | reading |")
A("| --- | --- | --- | --- |")
A(f"| **Catalogue B** — `<h3 class=\"section\">`, the rule sections of Chapter 1 | "
  f"{len(SECTIONS)} sections | **{len(R.sections_ported())} of {len(SECTIONS)}** | "
  f"every section carries a status |")
A(f"| **Instrument configuration sections** — `<section id=\"...\">` with an "
  f"`<h2>`, Chapter 1 Sr.No 149-154 | **{cfg_total} named groups** | "
  f"**{len(CFGR.ported())} of {cfg_total}** | "
  f"**{len(CFGR.blocked_rules())} blocked, each on a named input** |")
A(f"| **`<h2>` sub-tables** — `<section id=\"...\">` with an `<h2>` that "
  f"states no direction | **{len(SUBR.SUBTABLE_REGISTRY)} sub-tables** | "
  f"**{len(SUBR.ported())} of {len(SUBR.SUBTABLE_REGISTRY)}** | "
  f"**{len(SUBR.blocked())} blocked or out of scope, each on a named "
  f"input** |")
A("")
A(f"**So: catalogue B {len(R.sections_ported())}/{len(SECTIONS)} · "
  f"configuration sections {len(CFGR.ported())}/{cfg_total} · sub-tables "
  f"{len(SUBR.ported())}/{len(SUBR.SUBTABLE_REGISTRY)}.** THREE DENOMINATORS "
  f"OVER THREE SHAPES OF MARKUP, and none of them is in either of the "
  f"others. That separation is what keeps \"141 of 141\" honest: it is a "
  f"statement about `<h3 class=\"section\">` and about nothing else. All "
  f"three DO feed the calendar — `verdicts.py` fires all three registries — "
  f"and the {len(_verdicts):,} verdict rows split "
  f"**{len(cat_b_rows):,} catalogue B · {len(cfg_rows):,} configuration · "
  f"{len(sub_rows):,} sub-table**.")
A("")
A(f"**A row's registry is readable off its `event` field with no lookup**: "
  f"`cfg_<block>_` for a configuration group, `sub_` for a sub-table, and "
  f"`b<nn>` or a panchang family name for catalogue B. That convention is "
  f"asserted at registration rather than left to discipline, because the one "
  f"thing that would make all three of these numbers wrong at once is a rule "
  f"in the wrong registry.")
A("")
A(f"**141 of 141 is TRUE OF CATALOGUE B and is not a coverage claim about the "
  f"source.** The instrument configuration sections are a different shape of "
  f"markup and were never in the 141, so they were never in the denominator and "
  f"a reader seeing \"141/141\" could conclude the source is fully covered when "
  f"{cfg_total - len(CFGR.ported())} of those {cfg_total} named groups have "
  f"still never had a rule written for them.")
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
A("### Gold, silver and sugar now reach the calendar through their own "
  "configuration groups as well as through generic catalogue-B rules")
A("")
A(f"**Gold, silver and sugar are the three instruments the source prints "
  f"verdicts for** — that is why they carry evidence blocks naming their own "
  f"configuration sections, and it is what their tiers rest on. Their own "
  f"configuration groups are "
  + " · ".join(f"**{i} {cfg_inst[i]}**" for i in CFG.INSTRUMENTS)
  + f" named groups, of which **{len(CFGR.ported())}** now carry a rule and "
  f"**{len(CFGR.blocked_rules())}** are blocked on a named input. "
  f"**{cfg_rules_firing} of those {len(CFGR.ported())} fire in {YEAR}**, for "
  f"{len(cfg_rows):,} rows.")
A("")
A("**Ported IS wired, since the 14-Sep-2026 change to `verdicts.py`, and the "
  "distinction this section used to draw is the one thing about it that is now "
  f"out of date.** `build_verdicts()` fires both registries; "
  f"`config_instruments_for` routes a group to the instrument its BLOCK names "
  f"rather than through the rulership table, so a *Gold — Bullish* group "
  f"reaches gold because the source filed it under gold.")
A("")
A(f"**{len(cfg_rows):,} of {len(_verdicts):,} verdict rows in "
  f"`build/calendar_{YEAR}.*` originate in a configuration section**, from "
  f"{cfg_rules_firing} groups, split "
  + " · ".join(f"**{b} {c:,}**"
               for b, c in sorted(cfg_rows_by_block.items()))
  + ".")
A("")
# THE OLD TEST STILL PASSES AND ITS OLD CONCLUSION IS NOW FALSE, which is worth
# the sentence: this page used to say "the event_section field never reads
# `gold-bullish`", and it still never does -- event_section carries the group's
# own printed title. A reader re-running that test today gets the same answer
# and the opposite truth.
A("**How to tell one apart, because the old test no longer works.** This page "
  "used to say that no row originates in a configuration section and offered a "
  "check: the `event_section` field never reads `gold-bullish`. It still never "
  "does — `event_section` carries the group's own printed title, such as "
  "`Venus Alone in Leo or Libra — Bearish`, and never the block id. The test "
  "passes and its conclusion is now wrong. **The field that separates them is "
  "`event`**, whose rule id begins `cfg_<block>_` for a configuration row and "
  "`b<nn>` or a panchang family name for a catalogue-B one.")
A("")
A("What gold, silver and sugar got BEFORE the wiring is still in the file and "
  "is still not the source's verdicts for them: every generic catalogue-B rule "
  "whose bodies resolve to an instrument still emits there — a Venus rule "
  "reaches SUGAR because SUGAR's rulership is Venus, not because the source "
  "said anything about sugar. The wiring added the source's own conditions "
  "beside those rows; it removed none of them.")
A("")
A(f"Sugar is the clearest case and is the reason the gap was found at all: it "
  f"emits rows from 12 different Venus-ruled catalogue-B sections, and "
  f"**{cfg_rows_by_instrument['SUGAR']:,}** from its own nine groups — "
  f"{cfg_rows_by_instrument['SUGAR']:,} of its "
  f"{sum(1 for v in _verdicts if v.instrument == 'SUGAR'):,} rows. That figure "
  f"was **0** until the wiring, and a reader seeing SUGAR's rows then would "
  f"have seen a covered instrument.")
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
A("### The third body of material — registered since 20-Sep-2026, and two of "
  "it ported")
A("")
A(f"The same chapter carries {len(CFG.other_h2_tables())} further `<h2>` "
  "sub-tables that are neither catalogue B nor any of the six blocks above: "
  + ", ".join(f"*{t}*" for t in CFG.other_h2_tables()) + ".")
A("")
A(f"**This heading read \"There is a third UNPORTED body of material\" until "
  f"20-Sep-2026.** These nine now have a registry of their own and a "
  f"denominator of their own, at the top of this page: "
  f"{len(SUBR.ported())} of {len(SUBR.SUBTABLE_REGISTRY)} ported, "
  f"{len(SUBR.blocked())} registered and blocked with the input each waits "
  f"on NAMED. Registering the blocked seven rather than describing them in "
  f"prose is what makes \"blocked on what\" countable off the registry "
  f"instead of parsed out of a sentence.")
A("")
A("| sub-table | status | rule | blocked on |")
A("| --- | --- | --- | --- |")
_sub_ported = set(id(x) for x in SUBR.ported())
for _r in SUBR.SUBTABLE_REGISTRY:
    _st = "**ported**" if id(_r) in _sub_ported else "blocked"
    _mi = ", ".join(f"`{k}`" for k in _r.missing_inputs) or "—"
    A(f"| {_r.section.title} ({_r.section.page}) | {_st} | `{_r.id}` | "
      f"{_mi} |")
A("")
A("The two ported are the ones the layer could already compute AND whose "
  "printed tables they were reported against first: Total Day reproduces the "
  "section's own **12 of 12** dates with no extra, and the Thursday table "
  "**13 of 13** rows on three independent columns — date, nakshatra, and the "
  "five boundaries it states as clock times, all landing within 50 seconds. "
  "Both carry a NULL verdict, because none of the nine sections prints one "
  "and `subtable_catalogue.check_no_verdict` refuses a rule that arrives "
  "carrying one.")
A("")
A("**`moon_navamsa_series` blocks two of the seven and is the largest single "
  "gap named on this page.** The Moon crosses a navamsa every two hours and "
  "the astronomy layer emits no navamsa ingress for it — 0 records in both "
  "years, against 162 for Mercury — so *Moon Mercury in the Same Navamsh "
  "(D9)* (36 printed windows) and most of *Planet Vargottam in Their Own "
  "Nakshatra* sit behind a series that does not exist, and so does B71d. It "
  "is a new SERIES of roughly 1,450 records a year, not a rule, which is why "
  "it is filed with Bhadra rather than with the two above.")
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
A(f"**And \"this page\" is not the whole source.** It covers catalogue B. Of "
  f"the {cfg_total} named groups of the instrument configuration sections "
  f"(Chapter 1, Sr.No 149-154), **{len(CFGR.ported())} are ported and reach "
  f"the rows above** "
  f"and {cfg_total - len(CFGR.ported())} are blocked on a named input, per "
  f"group in `build/CONFIG_PORT_REPORT.md`; "
  f"`build/CONFIG_SECTIONS_SCOPE.md` is the scope survey as it stood BEFORE "
  f"that port and its ported column is a record of that date, not a live "
  f"count. The source's monthly prophecy tables "
  f"(Chapter 3) are unported and are not scoped anywhere yet. See **Coverage, "
  f"in two denominators** at the top of this page before reading any number on "
  f"it as a statement about coverage of the document.")
A("")

OUT.write_text("\n".join(lines), encoding="utf-8", newline="\r\n")
print(f"wrote {OUT.relative_to(ROOT)}  ({len(lines)} lines)")
print(f"sections {len(R.sections_ported())}/{len(SECTIONS)}  rules {tot_rules}  "
      f"firings {tot_fire}  blocked {n_blk}  zero {len(R.zero_firing(firings))}")
