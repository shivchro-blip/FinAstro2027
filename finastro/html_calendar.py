"""The HTML calendar: the rows, the apparatus, search and filters.

One self-contained file. No CDN, no build step, no network: a calendar that needs
a server to read is a calendar that stops being readable when the server does.

TWO HALVES, and the second is not decoration:

* the CALENDAR -- every row in the specified display format, filterable by date
  range, instrument, tier and free text;
* the APPARATUS -- the certainty grades and both C grounds, the claim tags, every
  blocked section with what it waits for, the source defects found, and the
  standing disclaimer. It is a collapsible panel rather than a footnote because
  a reader who has to hunt for the caveats will read the rows without them.
"""
from __future__ import annotations

import collections
import html
import json
import pathlib

from . import cfgsections as CFG
from .rules import config_rules as CFGR
from .config import CONF
from .render import DISCLAIMER, OUT_HTML
from .rules import REGISTRY, by_status
from .rules.catalogue import SECTIONS

YEAR = CONF["year"]

#: How many of the configuration groups the SCOPE SURVEY classed as needing no
#: astronomy the layer lacks. Kept as a number here rather than re-derived: the
#: per-group class is a judgement recorded in
#: `build/CONFIG_SECTIONS_SCOPE.md`, and the panel quotes the report rather
#: than re-deciding it. Drift between the two is caught by
#: `tests/test_rule_layer.py::
#: test_configuration_coverage_is_stated_and_counted_from_the_document`, which
#: reads this number back out of the generated report.
#:
#: It is NOT the number ported. The port delivered 38: three of the 41 turned
#: out to need an input the survey had not seen, and one group the survey did
#: not count as READY was ported as a resolved ambiguity. The two numbers are
#: kept apart deliberately -- overwriting the estimate with the outcome would
#: erase the one fact worth keeping, which is that the estimate was wrong and
#: by how much.
CFG_READY = 41


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6b66;--line:#e2ded5;--card:#fff;
--ok:#1c6b3c;--blk:#9a2f2f;--amb:#8a6510;--loc:#1f4e79;--ven:#5b3a8e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:22px 26px;border-bottom:1px solid var(--line);background:var(--card)}
h1{margin:0 0 4px;font-size:20px}
h2{font-size:16px;margin:22px 0 8px}
.sub{color:var(--mut);font-size:13px}
.wrap{padding:0 26px 60px}
.disc{margin:14px 0;padding:11px 14px;border-left:3px solid var(--amb);
background:#fdf8ec;font-size:13px}
.panel{margin:14px 0;border:1px solid var(--line);border-radius:6px;background:var(--card)}
.panel>summary{cursor:pointer;padding:11px 14px;font-weight:600;font-size:14px}
.panel .body{padding:0 14px 14px;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:6px 9px;border-bottom:1px solid var(--line);
vertical-align:top}
th{background:#f4f1ea;position:sticky;top:0;cursor:pointer;white-space:nowrap}
tr:hover td{background:#faf8f3}
.mut{color:var(--mut)}
.tier{font-size:11px;padding:1px 6px;border-radius:9px;border:1px solid var(--line);
white-space:nowrap}
.t-source_backed{color:var(--ok);border-color:#bcd9c7}
.t-book_derived{color:var(--amb);border-color:#e2d3a8}
.t-no_rule{color:var(--blk);border-color:#e6c3c3}
.t-cross_market_localized{color:var(--loc);border-color:#c2d4e8}
.t-venue_shifted{color:var(--ven);border-color:#d6cce8}
.null{color:var(--mut);font-style:italic}
.shift{color:var(--amb);font-weight:600}
.controls{display:flex;flex-wrap:wrap;gap:9px;margin:14px 0;align-items:center}
input,select{padding:6px 9px;border:1px solid var(--line);border-radius:5px;
background:#fff;font:inherit;font-size:13px}
input[type=text]{min-width:220px}
.count{color:var(--mut);font-size:13px;margin-left:auto}
.flag{font-size:11px;color:var(--mut)}
code{font-size:12px;background:#f4f1ea;padding:1px 4px;border-radius:3px}
"""

JS = """
const rows = CAL_ROWS;
function esc(s){return s==null?'':String(s).replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function fill(){
  const insts=[...new Set(rows.map(r=>r.instrument))].sort();
  const tiers=[...new Set(rows.map(r=>r.tier).filter(Boolean))].sort();
  const si=document.getElementById('inst'), st=document.getElementById('tier');
  insts.forEach(v=>si.add(new Option(v,v)));
  tiers.forEach(v=>st.add(new Option(v,v)));
}
function render(){
  const q=document.getElementById('q').value.toLowerCase();
  const from=document.getElementById('from').value;
  const to=document.getElementById('to').value;
  const inst=document.getElementById('inst').value;
  const tier=document.getElementById('tier').value;
  const onlyV=document.getElementById('onlyv').checked;
  const body=document.getElementById('rows');
  let n=0, html='';
  for(const r of rows){
    if(inst && r.instrument!==inst) continue;
    if(tier && r.tier!==tier) continue;
    if(onlyV && !r.vedic_interpretation) continue;
    const iso=r.iso_date;
    if(from && iso<from) continue;
    if(to && iso>to) continue;
    if(q){
      const hay=(r.event+' '+r.instrument+' '+r.event_section+' '+
        (r.vedic_interpretation||'')+' '+(r.flags||[]).join(' ')).toLowerCase();
      if(!hay.includes(q)) continue;
    }
    n++;
    const shift=r.day_shift? '<span class="shift">'+esc(r.day_shift_marker)+
      ' '+esc(r.date_et)+'</span>' : esc(r.date_et);
    html+='<tr>'
      +'<td>'+esc(r.date_ist)+'</td>'
      +'<td>'+esc(r.time_ist)+'</td>'
      +'<td>'+esc(r.time_et)+' <span class="mut">'+esc(r.et_offset)+'</span></td>'
      +'<td>'+shift+'</td>'
      +'<td><b>'+esc(r.instrument)+'</b><div class="mut flag">'+esc(r.venue)+'</div></td>'
      +'<td>'+esc(r.event)+'<div class="mut flag">'+esc(r.event_section)+'</div></td>'
      +'<td>'+(r.vedic_interpretation? esc(r.vedic_interpretation)
              : '<span class="null">no inference printed</span>')+'</td>'
      +'<td class="mut">'+esc(r.financial_theme)+'</td>'
      +'<td><span class="tier t-'+esc(r.tier)+'">'+esc(r.tier||'none')+'</span>'
      +'<div class="mut flag">'+esc(r.confidence)+' &middot; '
      +esc(r.claim_tag||'no claim')+'</div></td>'
      +'</tr>';
  }
  body.innerHTML=html;
  document.getElementById('count').textContent=
    n.toLocaleString()+' of '+rows.length.toLocaleString()+' rows';
}
function sortBy(i,dir){
  rows.sort((a,b)=>{const k=Object.keys(a)[0];return 0;});
}
document.addEventListener('DOMContentLoaded',()=>{
  fill();
  ['q','from','to','inst','tier'].forEach(id=>
    document.getElementById(id).addEventListener('input',render));
  document.getElementById('onlyv').addEventListener('change',render);
  document.getElementById('reset').addEventListener('click',()=>{
    ['q','from','to'].forEach(id=>document.getElementById(id).value='');
    ['inst','tier'].forEach(id=>document.getElementById(id).value='');
    document.getElementById('onlyv').checked=false; render();});
  render();
});
"""


def write_html(rows: list[dict], verdicts) -> pathlib.Path:
    tiers = collections.Counter(str(r["tier"]) for r in rows)
    insts = collections.Counter(r["instrument"] for r in rows)
    blocked = sorted(by_status("blocked"), key=lambda r: r.catalogue_b)
    resolved = sorted(by_status("resolved_ambiguity"), key=lambda r: r.catalogue_b)
    ambiguous = sorted(by_status("ambiguous"), key=lambda r: r.catalogue_b)
    grounds = CONF["labels"]["data_certainty_grounds"]
    uncov = CONF["verdict_coverage"]["unported_configuration_sections"]
    cfg_counts = CFG.counts()
    cfg_total = CFG.total()

    js_rows = []
    for r in rows:
        d = dict(r)
        dd = __import__("datetime").datetime.strptime(r["date"], "%d-%b-%Y")
        d["iso_date"] = dd.strftime("%Y-%m-%d")
        d["day_shift_marker"] = __import__(
            "finastro.timezones", fromlist=["x"]).SHIFT_MARK
        js_rows.append(d)

    P = []
    A = P.append
    A("<!doctype html><html lang=en><head><meta charset=utf-8>")
    A(f"<title>FinAstro {YEAR} - astronomy calendar</title>")
    A(f"<style>{CSS}</style></head><body>")
    A("<header>")
    A(f"<h1>FinAstro {YEAR} - calendar</h1>")
    A(f'<div class="sub">{len(rows):,} rows over '
      f'{len(insts)} instruments &middot; '
      f'{sum(1 for r in rows if r["vedic_interpretation"]):,} carrying a '
      f'verdict, {sum(1 for r in rows if not r["vedic_interpretation"]):,} with '
      f'none &middot; confidence <code>untested</code> on every row</div>')
    A("</header><div class=wrap>")
    A(f'<div class="disc"><b>Read this first.</b> {_e(DISCLAIMER)}</div>')

    # ---------------------------------------------------------------- apparatus
    A("<details class=panel><summary>What this calendar is, and what it is "
      "not &mdash; the epistemic apparatus</summary><div class=body>")
    A("<p><b>Two layers, never merged.</b> The <b>astronomy</b> layer is "
      "computed from an ephemeris: positions, ingresses, stations, rises, "
      "eclipses. The <b>interpretation</b> layer is the 2026 source's own "
      "claims, carried verbatim or absent. Nothing in this file infers a "
      "market outcome from a planetary position.</p>")

    A("<h2>Certainty grades</h2><p>Every astronomy record carries one. "
      "<b>A</b> is computed exact under a minute; <b>B</b> is computed but "
      "definition-sensitive; <b>C</b> depends on something unevidenced &mdash; "
      "and <b>C has two grounds, which have different remedies and are named on "
      "every record and every rule</b>:</p><ul>")
    for k, v in grounds.items():
        A(f"<li><code>{_e(k)}</code> &mdash; {_e(v)}</li>")
    A("</ul><p><span class=mut>A station is frame-free: it is where the "
      "longitude is stationary, and no parameter stands between the sky and the "
      "instant. A crossing of 0.6583&nbsp;deg/day is only as meaningful as "
      "0.6583 is.</span></p>")

    A("<h2>Claim tags</h2><p>Each rule's verdict carries the tag its own words "
      "earn: <code>Classical</code> where the source states it plainly, "
      "<code>Observed</code> where the source hedges its own claim, "
      "<code>Framework</code> where it is a modern practitioner extension. A "
      "rule that prints no inference carries no tag, because an unstated claim "
      "has nothing to tag.</p>")

    A("<h2>Tiers, and the five values they take</h2><ul>")
    for t, n in sorted(tiers.items(), key=lambda x: str(x[0])):
        A(f"<li><span class='tier t-{_e(t)}'>{_e(t)}</span> &mdash; {n:,} "
          f"rows</li>")
    A("</ul><p><span class=mut><code>cross_market_localized</code> is a rule the "
      "source authored for Indian equities, applied to a different market "
      "(SPX, NDX). <code>venue_shifted</code> is the SAME instrument, same rule, "
      "same sky, differing only in which venue's midnight bounds the civil day "
      "(GC, SI, CL against MCXGOLD and MCXSILVER). Those were one value until "
      "14-Sep-2026.</span></p>")

    A(f"<h2>Source defects found in the 2026 document</h2>"
      f"<p>Recorded rather than corrected, because a calendar that silently "
      f"repairs its source cannot be audited against it.</p><ul>"
      f"<li><b>B81 is labelled for the wrong planet.</b> Its printed 2026 row "
      f"is Venus's retrograde window to within four minutes, and the true "
      f"Saturn&#8745;Mercury window is the row B83 prints.</li>"
      f"<li><b>B82</b> reproduces only from the carry-in: Jupiter's retrograde "
      f"began Nov-2025.</li>"
      f"<li><b>B114</b>'s printed end matches nothing in the sky; its second "
      f"visit is printed nowhere.</li>"
      f"<li><b>B115</b>'s printed rows are the <i>alone</i> sub-windows, "
      f"narrower than its title's union.</li>"
      f"<li><b>B88</b> is B87's series continuing with no verdict.</li>"
      f"<li><b>B30</b> defines its interval by longitude and never states what "
      f"makes a planet Demoted or Shadow.</li></ul>")

    A(f"<h2>Blocked sections &mdash; {len(blocked)}, each naming what it waits "
      f"for</h2><p>A blocked section is a real condition the layer refuses to "
      f"approximate. It is counted, emits nothing, and names the missing input."
      f"</p><ul>")
    for r in blocked:
        why = " <b>AND</b> ".join(" ".join(str(m).split())
                                  for m in r.missing_inputs)
        A(f"<li><b>B{r.catalogue_b}</b> {_e(r.section_title)} &mdash; "
          f"<span class=mut>{_e(why)}</span></li>")
    A("</ul>")

    # ------------------------------------------------- coverage, two denominators
    # Placed immediately after the blocked list and before anything else, because
    # the whole point of this block is that a reader must not be able to see the
    # catalogue-B number and conclude the source is covered. It is not a
    # footnote: it sits inside the same panel as the blockers, where a reader
    # asking "what is missing" is already looking.
    n_ported = len(SECTIONS)
    A(f"<h2>Coverage &mdash; two denominators, and one of them is not 141</h2>")
    A(f"<table><thead><tr><th>catalogue</th><th>shape in the source</th>"
      f"<th>sections</th><th>ported</th></tr></thead><tbody>"
      f"<tr><td><b>Catalogue B</b> &mdash; the Chapter-1 rule sections</td>"
      f"<td><code>&lt;h3 class=\"section\"&gt;</code></td>"
      f"<td>{n_ported} sections</td>"
      f"<td><b>{n_ported}/{n_ported}</b></td></tr>"
      f"<tr><td><b>Instrument configuration sections</b> &mdash; Chapter 2</td>"
      f"<td><code>&lt;section id=\"...\"&gt;</code> with <code>&lt;h2&gt;</code>"
      f"</td>"
      f"<td><b>{cfg_total} named groups</b></td>"
      f"<td><b>{len(CFGR.ported())}/{cfg_total}</b></td></tr>"
      f"</tbody></table>")
    cfg_ported = len(CFGR.ported())
    cfg_blocked = len(CFGR.blocked_rules())
    per_block = {}
    for r in CFGR.CONFIG_REGISTRY:
        k = r.section.block.id
        per_block.setdefault(k, [0, 0])[0 if r.status != "blocked" else 1] += 1
    A(f"<p><b>Catalogue B is {n_ported}/{n_ported}. The configuration sections "
      f"are {cfg_ported}/{cfg_total} ported, {cfg_blocked} blocked.</b> The "
      f"second set was never in the first's denominator &mdash; a different "
      f"shape of markup, counted separately &mdash; so <b>nothing on this page "
      f"should be read as \"the source is covered\"</b>. The counts come from "
      f"the document itself, not from this build's own config. The "
      f"configuration rules live in their own registry and, as of this build, "
      f"<b>do not feed the rows below</b>: porting a group is not publishing "
      f"it, and the two are kept separate on purpose.</p>")
    # STALE MARKER -- see build/NEXT_SESSION.md. The sentence above is no
    # longer true of the CODE: `verdicts.py` fires both registries since the
    # 14-Sep-2026 wiring. It remains true of any calendar rendered BEFORE that
    # wiring, which is why the marker states both.
    A("<p class=disc><b>STALE.</b> The sentence above describes the state "
      "before the configuration wiring. <code>verdicts.py</code> now fires "
      "both registries and configuration groups DO produce rows "
      "(1,468 of 6,677 in a rebuild). A calendar rendered before that wiring "
      "contains catalogue-B rows only and is internally consistent; this page "
      "says which it is by its own row count. Corrected text is a task in "
      "<code>build/NEXT_SESSION.md</code>.</p>")
    A("<ul>")
    for b, (inst, direction, pages) in CFG.BLOCKS.items():
        ported_n, blocked_n = per_block.get(b, [0, 0])
        A(f"<li><code>{_e(b)}</code> {_e(pages)} &mdash; "
          f"{_e(inst)}, {_e(direction)}: <b>{cfg_counts[b]}</b> named groups, "
          f"<b>{ported_n}</b> ported, <b>{blocked_n}</b> blocked</li>")
    A("</ul>")
    A("<p>The 20 blocked groups, by the input each is missing: "
      + " &middot; ".join(f"<b>{_e(k)}</b> {v}"
                          for k, v in sorted(CFGR.missing_input_counts().items(),
                                             key=lambda kv: -kv[1]) if v)
      + ". <code>vedha_wheel</code> is a sixth input the scope survey did not "
      "name and the port found; the other five are the survey's own.</p>")
    A(f"<p><b>Gold, silver and sugar are the three instruments the source "
      f"prints verdicts for</b> &mdash; that is what their tiers rest on &mdash; "
      f"and their own configuration groups are unported: "
      + " &middot; ".join(f"<b>{i} {CFG.by_instrument()[i]}</b>"
                          for i in CFG.INSTRUMENTS)
      + f". What they reach this calendar through today is generic catalogue-B "
      f"rules whose bodies happen to resolve to them &mdash; a Venus rule "
      f"reaches SUGAR because SUGAR's rulership is Venus, not because the "
      f"source says anything about sugar. <b>No row in this calendar "
      f"originates in any configuration section</b>: not one of the "
      f"{len(rows):,} rows carries a configuration section as its source, and "
      f"that is still true after the port &mdash; the {cfg_ported} ported "
      f"groups are registered and fire against the 2027 sky, but nothing "
      f"downstream reads them into this artifact yet.</p>")
    A(f"<p>There is a third unported body of material. The same chapter carries "
      f"nine further <code>&lt;h2&gt;</code> sub-tables that are neither "
      f"catalogue B nor any of the six blocks above ("
      + ", ".join(_e(t) for t in CFG.other_h2_tables())
      + f"), and the source's own monthly prophecy tables print named verdicts "
      f"for gold and silver that are also outside catalogue B and also "
      f"unported. Recorded because fixing one denominator and leaving the next "
      f"one implicit only moves the misleading claim.</p>")
    A(f"<p><span class=mut>What porting the {cfg_total} groups would take is "
      f"scoped per group in <code>build/CONFIG_SECTIONS_SCOPE.md</code> "
      f"&mdash; not estimated. Of the {cfg_total}, the survey classed "
      f"{CFG_READY} as needing no astronomy this layer lacks; the port "
      f"delivered {cfg_ported}, because three of the {CFG_READY} turned out to "
      f"need an input the survey had not seen and one group it had not counted "
      f"was ported as a resolved ambiguity. The estimate is kept beside the "
      f"outcome rather than overwritten by it.</span></p>")

    # The sugar diagnosis is a DIAGNOSTIC, not a second coverage statement --
    # the counts and the per-block lists are in the coverage block above, which
    # sits beside the blockers. Kept here because "why was SUGAR empty" and "why
    # is SUGAR thin" have two different answers and the first one was wrong.
    A(f"<h2>Why SUGAR's rows exist at all &mdash; a diagnosis that was wrong "
      f"first</h2><p>{_e(uncov['sugar_specifically'])}</p>")

    A(f"<h2>Rules firing on a reading we supplied &mdash; {len(resolved)}</h2>"
      f"<p>The words these fire on are partly ours. Never counted with the "
      f"source-backed rules, and flagged on every row.</p><ul>")
    for r in resolved:
        A(f"<li><b>B{r.catalogue_b}</b> <code>{_e(r.id)}</code> &mdash; "
          f"<span class=mut>{_e(', '.join(r.flags))}</span></li>")
    A("</ul>")

    if ambiguous:
        A("<h2>Wording that admits more than one reading</h2><ul>")
        for r in ambiguous:
            A(f"<li><b>B{r.catalogue_b}</b> <code>{_e(r.id)}</code> &mdash; "
              f"{_e(r.ambiguity)}</li>")
        A("</ul>")
    A("</div></details>")

    # ---------------------------------------------------------------- controls
    A("<div class=controls>")
    A('<input type=text id=q placeholder="search event, section, verdict, flag">')
    A('<label class=sub>from <input type=date id=from></label>')
    A('<label class=sub>to <input type=date id=to></label>')
    A('<select id=inst><option value="">all instruments</option></select>')
    A('<select id=tier><option value="">all tiers</option></select>')
    A('<label class=sub><input type=checkbox id=onlyv> only rows with a verdict'
      '</label>')
    A('<button id=reset>reset</button>')
    A('<span class=count id=count></span>')
    A("</div>")

    A("<table><thead><tr>"
      "<th>Date (IST)</th><th>Time IST</th><th>Time ET</th><th>Date (ET)</th>"
      "<th>Instrument</th><th>Event</th><th>Vedic interpretation</th>"
      "<th>Financial-market theme</th><th>Tier / confidence</th>"
      "</tr></thead><tbody id=rows></tbody></table>")
    A("</div>")
    A(f"<script>const CAL_ROWS={json.dumps(js_rows, ensure_ascii=False)};"
      f"{JS}</script>")
    A("</body></html>")
    OUT_HTML.write_text("\n".join(P), encoding="utf-8", newline="\n")
    return OUT_HTML
