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
from .rules import subtables as SUBR
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
.win{font-size:11px;color:var(--ven);font-weight:600}
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
  // Both lists are built from VERDICT rows. An event row has neither field,
  // and `undefined` sorting into a dropdown as a blank option is exactly how
  // one population starts looking like a member of the other.
  const vr=rows.filter(r=>r.row_kind==='verdict');
  const insts=[...new Set(vr.map(r=>r.instrument))].sort();
  const tiers=[...new Set(vr.map(r=>r.tier).filter(Boolean))].sort();
  const si=document.getElementById('inst'), st=document.getElementById('tier');
  insts.forEach(v=>si.add(new Option(v,v)));
  tiers.forEach(v=>st.add(new Option(v,v)));
}
function render(){
  const q=document.getElementById('q').value.toLowerCase();
  const from=document.getElementById('from').value;
  const to=document.getElementById('to').value;
  const kind=document.getElementById('kind').value;
  const inst=document.getElementById('inst').value;
  const tier=document.getElementById('tier').value;
  const onlyV=document.getElementById('onlyv').checked;
  const body=document.getElementById('rows');
  let n=0, html='';
  for(const r of rows){
    if(kind && r.row_kind!==kind) continue;
    // An instrument or tier filter is a question only a verdict row can answer,
    // so it hides every event row rather than matching `undefined` against ''.
    if(inst && (r.row_kind!=='verdict' || r.instrument!==inst)) continue;
    if(tier && (r.row_kind!=='verdict' || r.tier!==tier)) continue;
    if(onlyV && !r.vedic_interpretation) continue;
    // AN OVERLAP TEST, NOT A COMPARISON AGAINST THE SORT KEY. A window row
    // carries one sort date -- the first day it holds -- so `iso<from` would
    // drop a window running 06-Feb -> 20-Feb from a "from 10-Feb" view although
    // it is live on every day the reader asked about. `iso_date_end` equals
    // `iso_date` on a day row, so the two shapes take the same branch rather
    // than the filter growing a case. SPAN_VS_DAILY_PROPOSAL.md section 5.3.
    if(from && r.iso_date_end<from) continue;
    if(to && r.iso_date>to) continue;
    if(q){
      // `||''` on every optional field: an event row has no instrument and no
      // interpretation, and 'undefined' in the haystack makes that word a
      // search term that matches 405 rows.
      const hay=(r.event+' '+r.row_kind+' '+(r.instrument||'')+' '
        +(r.event_section||'')+' '+(r.record_id||'')+' '
        +(r.bodies||[]).join(' ')+' '
        +(r.vedic_interpretation||'')+' '+(r.flags||[]).join(' ')).toLowerCase();
      if(!hay.includes(q)) continue;
    }
    n++;
    const ev = r.row_kind==='event';
    const shift=(!ev && r.day_shift)
      ? '<span class="shift">'+esc(r.day_shift_marker)+' '+esc(r.date_et)+'</span>'
      : esc(r.date_et);
    // A row with no instant prints WHY, in place of the time it does not have.
    // `no instant` alone would read as a gap in the build; `date_only` says the
    // ephemeris never resolved it to a moment, `period_cut` that the boundary
    // is the generated span's, `anchored` that the date was chosen here, and
    // `named_contacts` that there are several times and the row names them.
    const noTime = r.time_ist? null
      : '<span class="null">'+esc(r.no_instant_reason||'no instant')+'</span>';
    const tIST = r.time_ist? esc(r.time_ist) : noTime;
    const tET  = r.time_et? esc(r.time_et)+' <span class="mut">'
                            +esc(r.et_offset)+'</span>' : noTime;
    // An eclipse names its contacts. The record carries begin, maximum, end and
    // both totality contacts; one unlabelled time would be choosing among them.
    const contacts=(r.contacts||[]).map(c=>
      '<div class="mut flag">'+esc(c.contact.replace('_',' '))+': '
      +esc(c.date_ist)+' '+esc(c.time_ist)+'</div>').join('');
    // A WINDOW ROW SAYS SO IN THE DATE CELL, not only in a field. It stands
    // for `days_in_view` civil days, and `last_held` is the last day the
    // condition HOLDS -- never the calendar date of `t_end_utc`, which is the
    // exclusive instant it ceases and lands one day later on every window whose
    // end falls on a venue midnight.
    const win = r.row_span==='window';
    const dateCell = win
      ? esc(r.first_held)+' <span class="mut">&rarr;</span> '+esc(r.last_held)
        +'<div class="mut flag">'+r.days_in_view+' days in view'
        +(r.open_start?' &middot; running at the carry-in':'')
        +(r.open_end?' &middot; still running at the period end':'')
        +(r.clipped_start?' &middot; starts before '+CAL_YEAR:'')
        +(r.clipped_end?' &middot; ends after '+CAL_YEAR:'')+'</div>'
      : esc(r.date_ist);
    html+='<tr>'
      +'<td class="mut flag">'+esc(r.row_kind)
        +(win? '<div class="win">window</div>':'')+'</td>'
      +'<td>'+dateCell+'</td>'
      +'<td>'+tIST+'</td>'
      +'<td>'+tET+'</td>'
      +'<td>'+shift+'</td>'
      // An event row has no instrument, no theme, no tier and no verdict, and
      // the cells say so rather than sitting empty. An empty cell reads as a
      // missing value; "the sky" reads as the answer it is.
      +'<td>'+(ev? '<span class="null">the sky</span>'
               : '<b>'+esc(r.instrument)+'</b><div class="mut flag">'
                 +esc(r.venue)+'</div>')+'</td>'
      +'<td>'+esc(r.event)+'<div class="mut flag">'+esc(r.event_section)+'</div>'
      +contacts+'</td>'
      +'<td>'+(ev? '<span class="null">not a claim</span>'
               : (r.vedic_interpretation? esc(r.vedic_interpretation)
                  : '<span class="null">no inference printed</span>'))+'</td>'
      +'<td class="mut">'+(ev? esc(r.bodies? r.bodies.join(' ') : '')
                            : esc(r.financial_theme))+'</td>'
      +'<td>'+(ev? '<span class="mut flag">certainty '+esc(r.data_certainty)
                   +'</span>'
               : '<span class="tier t-'+esc(r.tier)+'">'+esc(r.tier||'none')
                 +'</span><div class="mut flag">'+esc(r.confidence)+' &middot; '
                 +esc(r.claim_tag||'no claim')+'</div>')+'</td>'
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
  ['q','from','to','kind','inst','tier'].forEach(id=>
    document.getElementById(id).addEventListener('input',render));
  document.getElementById('onlyv').addEventListener('change',render);
  document.getElementById('reset').addEventListener('click',()=>{
    ['q','from','to'].forEach(id=>document.getElementById(id).value='');
    ['kind','inst','tier'].forEach(id=>document.getElementById(id).value='');
    document.getElementById('onlyv').checked=false; render();});
  render();
});
"""


def write_html(rows: list[dict], verdicts) -> pathlib.Path:
    # COUNTED OVER VERDICT ROWS ONLY, and `.get` is deliberately not used: an
    # event row has no `tier` key at all, so counting over every row raises a
    # KeyError here rather than quietly tallying 405 `None`s into a tier
    # histogram. That exception is the discriminator working -- it is what
    # stopped the base track being absorbed the first time this file met it.
    vrows = [r for r in rows if r["row_kind"] == "verdict"]
    erows = [r for r in rows if r["row_kind"] == "event"]
    tiers = collections.Counter(str(r["tier"]) for r in vrows)
    insts = collections.Counter(r["instrument"] for r in vrows)
    classes = collections.Counter(r["event_class"] for r in erows)
    blocked = sorted(by_status("blocked"), key=lambda r: r.catalogue_b)
    resolved = sorted(by_status("resolved_ambiguity"), key=lambda r: r.catalogue_b)
    ambiguous = sorted(by_status("ambiguous"), key=lambda r: r.catalogue_b)
    # The three empty-day figures, computed here from the SAME rows the table
    # below renders rather than quoted from the JSON. They differ only in which
    # rows they count, and the gap between the first two is the whole point.
    from .render import _days_without, covered_days
    # THE TWO SHAPES, counted here off the rows this page renders rather than
    # read from meta -- the same argument the cfg panel's row counts make, and
    # for the same reason: a figure quoted from a file the page did not read
    # goes on looking right after the page stops agreeing with it.
    wrows = [r for r in rows if r["row_span"] == "window"]
    n_windows = len(wrows)
    window_days = sum(len(covered_days(r)) for r in wrows)
    daily_equiv = sum(len(covered_days(r)) for r in rows)
    empty_event_days = _days_without(rows, "event")
    empty_any_days = _days_without(rows)
    empty_verdict_days = _days_without(
        rows, predicate=lambda r: bool(r.get("vedic_interpretation")))
    grounds = CONF["labels"]["data_certainty_grounds"]
    uncov = CONF["verdict_coverage"]["unported_configuration_sections"]
    cfg_counts = CFG.counts()
    cfg_total = CFG.total()

    # THE FILTER'S TWO KEYS, built here so the browser never parses a date.
    # `iso_date_end` is the LAST day the row holds, which on a day row is the
    # same day -- so the overlap test in `render()` has one branch and not two,
    # and a day row cannot take a window's path by accident.
    js_rows = []
    for r in rows:
        d = dict(r)
        days = covered_days(r)
        d["iso_date"] = days[0].strftime("%Y-%m-%d")
        d["iso_date_end"] = days[-1].strftime("%Y-%m-%d")
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
    # TWO POPULATIONS, NAMED. `len(rows)` alone would read as a verdict count,
    # which is what it was until the base track arrived and is what it stopped
    # being on the same day.
    A(f'<div class="sub">{len(rows):,} rows &mdash; '
      f'<b>{len(vrows):,} verdict rows</b> over {len(insts)} instruments and '
      f'<b>{len(erows):,} astronomy event rows</b>, which carry no instrument, '
      f'no tier and no verdict &middot; '
      # THE SECOND SPLIT, on the same line as the first and for the same
      # reason. This number was 8,916 until 21-Sep-2026 and every row was one
      # civil day; a reader meeting 8,121 with no second split would read it as
      # the same kind of number one row smaller.
      f'{n_windows:,} of them are <b>windows</b> standing for '
      f'{window_days:,} civil days, so the daily-row equivalent is '
      f'{daily_equiv:,} &middot; '
      f'{sum(1 for r in vrows if r["vedic_interpretation"]):,} verdict rows '
      f'carry an interpretation, '
      f'{sum(1 for r in vrows if not r["vedic_interpretation"]):,} carry none '
      f'&middot; confidence <code>untested</code> on every verdict row</div>')
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

    A("<h2>Two kinds of row, and why the counts are split</h2>"
      "<p>Every row carries <code>row_kind</code>. A <b>verdict</b> row is one "
      "rule, one instrument, one venue civil day; an <b>event</b> row is one "
      "astronomy record rendered as itself &mdash; the <b>base track</b>. An "
      "event row has no instrument, no tier, no claim tag and no verdict, and "
      "not because they were left empty: the object it is built from has "
      "nowhere to put them.</p>"
      f"<p>{len(vrows):,} verdict rows, {len(erows):,} event rows, "
      f"{len(rows):,} together &mdash; and that last number is the one to be "
      "careful with. Until the base track arrived every count in this file "
      "was a verdict count, so <code>no_rule</code> would have absorbed 405 "
      "rows and gone on looking like the figure it used to be. Every count in "
      "the JSON <code>meta</code> is therefore keyed by row kind first.</p>"
      "<p>The base track is the ten core event classes &mdash; sign ingress, "
      "lunation, conjunction, opposition, apsis, combustion, station, speed "
      "crossing, eclipse, total day. Not the panchang ingresses (tithi, "
      "nakshatra, yoga, navamsa: four to six a day, and already carried on "
      "every row that falls in them) and not sunrise or sunset (a location "
      "property, an input to the rules that use it).</p><ul>")
    for c, n in sorted(classes.items(), key=lambda x: -x[1]):
        A(f"<li><code>{_e(c)}</code> &mdash; {n:,}</li>")
    A("</ul>")

    # ------------------------------------------- the second discriminator
    # A SEPARATE FIELD AND A SEPARATE SECTION. `row_kind` answers verdict vs
    # sky; this answers window vs day, and the two axes are independent -- an
    # event row can be a window and most verdict rows are not.
    rs = CONF["row_kinds"]["row_span"]
    A(f"<h2>Two SHAPES of row, and why {daily_equiv - len(rows):,} rows are "
      f"not here</h2>"
      f"<p>Every row also carries <code>row_span</code>. A <b>day</b> row "
      f"stands for one civil day at one venue. A <b>window</b> row stands for "
      f"an interval, and prints the first and last civil day the condition "
      f"holds instead of a single date. There are <b>{n_windows:,} window "
      f"rows</b> and they cover <b>{window_days:,} civil days</b>, which is "
      f"why {len(rows):,} rows here are {daily_equiv:,} rows under the shape "
      f"this calendar had until 21-Sep-2026.</p>"
      f"<p><b>Only rows with no instant at either end were collapsed.</b> A "
      f"combust window the ephemeris emits as two dates, a window built from "
      f"civil-day boundaries, and a state already running when the generated "
      f"period began &mdash; those printed the same pair of endpoints on every "
      f"day they covered, and the days differed in nothing else. That is "
      f"measured rather than assumed: the renderer refuses to fold a group "
      f"whose rows disagree on any field but the date.</p>"
      f"<p><b>What was deliberately not collapsed.</b> An "
      f"<code>anchored</code> row's date was chosen <i>here</i>, because the "
      f"body never crossed its frame &mdash; giving it the year would read as "
      f"a state somebody observed, and nothing observed it. An eclipse has "
      f"<i>several</i> instants, not none. And every span carrying a clock "
      f"time is still one row per day: its start is a real moment, and "
      f"collapsing it would discard a per-day statement a reader may be "
      f"using.</p>"
      f"<p><b>A window's end is the last day it <i>holds</i>.</b> A span is "
      f"half-open, so the instant it ceases lands in a day the condition no "
      f"longer holds &mdash; one day later, on every window whose end falls on "
      f"a venue midnight. Both are in the file, under names that cannot be "
      f"confused: <code>last_held</code> is the day, <code>t_end_utc</code> is "
      f"the instant. Neither a duration nor an end date is asserted where the "
      f"period cut the span or the year clipped it; <code>open_start</code>, "
      f"<code>open_end</code>, <code>clipped_start</code> and "
      f"<code>clipped_end</code> say which ends are real, and the date cell "
      f"repeats it in words.</p>"
      f"<p><span class=mut>The date filter above is an <b>overlap</b> test for "
      f"this reason: a window running 06-Feb to 20-Feb appears for any day in "
      f"that range, not only for its first. The three empty-day figures below "
      f"are unmoved by the collapse for the same reason &mdash; a window "
      f"counts on every day it covers.</span></p>")
    A(f"<p><span class=mut>{_e(rs['no_count_changed_meaning'].strip())}"
      f"</span></p>")
    # ------------------------------------------------ absence, stated on the page
    # 105 is a FACT ABOUT THE YEAR and it is invisible in the default view, so
    # it goes on the panel rather than waiting to be discovered by a reader who
    # already knows to filter. The second paragraph is the one that earns the
    # section: the calendar read whole is never empty, and that is `tier_4`
    # talking, not the sky.
    A(f"<h2>The {empty_event_days} days of {YEAR} on which nothing happened"
      f"</h2>"
      f"<p><b>{empty_event_days} of {YEAR}'s 365 days carry no astronomical "
      f"event.</b> Not a gap in the build &mdash; a measurement. Nothing in the "
      f"ten core classes the base track covers falls on any of them, and the "
      f"{len(erows):,} event rows land on the other "
      f"{365 - empty_event_days}.</p>"
      f"<p><b>You will not see those days by scrolling.</b> "
      f"{empty_any_days} days carry no row <i>of any kind</i>, and that zero is "
      f"not a second measurement agreeing with the first &mdash; it is "
      f"<code>tier_4</code>. A catalogue-B firing emits a verdict-null "
      f"<code>USDINR</code> row whether or not the rulership table has anything "
      f"to say about USDINR, and those blanket all 365 days. So the unfiltered "
      f"calendar <b>cannot be empty on any day</b>, and it cannot report "
      f"absence at all.</p>"
      f"<p>Set the row-kind control to <b>astronomy events only</b> and the "
      f"{empty_event_days} days appear as the gaps they are. That is the second "
      f"use of <code>row_kind</code>, and the argument for adding it did not "
      f"anticipate this one: <b>absence is reportable on the base track and "
      f"only through the discriminator.</b></p>"
      f"<p><span class=mut>A third figure, for completeness and because it is "
      f"the one that sounds worst and means least: {empty_verdict_days} days "
      f"carry no row with a verdict text on it. The argument that produced the "
      f"base track was made with a figure of 32 empty days, which was never "
      f"measured against this build. It is not one number and it is not "
      f"32.</span></p>")

    A("<h2>When a row prints a date and no time</h2>"
      "<p>A row carries a clock time only when its start is a moment something "
      "crossed. When it is not, the row prints <b>why</b> instead:</p><ul>"
      "<li><code>date_only</code> &mdash; the ephemeris never resolved it to a "
      "moment. Combust and rise windows are horizon measurements emitted as "
      "dates; so is a total day.</li>"
      "<li><code>period_cut</code> &mdash; the boundary is where the generated "
      "span was cut, not where the sky changed. The state was already running "
      "at the carry-in.</li>"
      "<li><code>anchored</code> &mdash; the date was chosen here, because the "
      "thing the row reports is that a body did <i>not</i> cross.</li>"
      "<li><code>named_contacts</code> &mdash; there are several times and the "
      "row names them. Eclipses carry first contact and maximum.</li></ul>"
      f"<p><span class=mut>{sum(1 for r in rows if not r['time_ist']):,} of "
      f"{len(rows):,} rows. Until 15-Sep-2026 all of them printed "
      "<code>00:00 IST</code> with a previous-Eastern-day afternoon beside it, "
      "because the renderer was handed one stamp type and that type always had "
      "a time on it.</span></p>")

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

    # ----------------------------------------------- coverage, three denominators
    # Placed immediately after the blocked list and before anything else, because
    # the whole point of this block is that a reader must not be able to see the
    # catalogue-B number and conclude the source is covered. It is not a
    # footnote: it sits inside the same panel as the blockers, where a reader
    # asking "what is missing" is already looking.
    #
    # The third row landed 20-Sep-2026 with the sub-table registry. Two rows
    # here while the build fires three registries would understate the source
    # by a whole catalogue -- and the table would have gone on being CORRECT
    # about the two it did list, which is the failure this panel exists to stop.
    n_ported = len(SECTIONS)
    A(f"<h2>Coverage &mdash; three denominators, and only one of them "
      f"is 141</h2>")
    A(f"<table><thead><tr><th>catalogue</th><th>shape in the source</th>"
      f"<th>sections</th><th>ported</th></tr></thead><tbody>"
      f"<tr><td><b>Catalogue B</b> &mdash; the Chapter-1 rule sections</td>"
      f"<td><code>&lt;h3 class=\"section\"&gt;</code></td>"
      f"<td>{n_ported} sections</td>"
      f"<td><b>{n_ported}/{n_ported}</b></td></tr>"
      f"<tr><td><b>Instrument configuration sections</b> &mdash; Chapter 1, "
      f"Sr.No 149-154</td>"
      f"<td><code>&lt;section id=\"...\"&gt;</code> with <code>&lt;h2&gt;</code>"
      f" and named groups</td>"
      f"<td><b>{cfg_total} named groups</b></td>"
      f"<td><b>{len(CFGR.ported())}/{cfg_total}</b></td></tr>"
      f"<tr><td><b><code>&lt;h2&gt;</code> sub-tables</b> &mdash; Chapter 1, "
      f"Sr.No 139-148, "
      f"belonging to no instrument block</td>"
      f"<td><code>&lt;section id=\"...\"&gt;</code> with <code>&lt;h2&gt;</code>"
      f" and none</td>"
      f"<td><b>{len(SUBR.SUBTABLE_REGISTRY)} sub-tables</b></td>"
      f"<td><b>{len(SUBR.ported())}/{len(SUBR.SUBTABLE_REGISTRY)}</b></td>"
      f"</tr>"
      f"</tbody></table>")
    cfg_ported = len(CFGR.ported())
    cfg_blocked = len(CFGR.blocked_rules())
    # OFF THE ROWS THIS PAGE IS RENDERING, not off a registry count. A panel
    # that described the wiring from the registry would say the same thing
    # whether or not anything downstream read it -- which is exactly how the
    # sentence this replaces stayed wrong after the wiring landed.
    verdict_rows = [r for r in rows if r.get("row_kind") == "verdict"]
    cfg_row_list = [r for r in verdict_rows if r["event"].startswith("cfg_")]
    cfg_calendar_rows = len(cfg_row_list)
    cfg_rules_in_calendar = len({r["event"] for r in cfg_row_list})
    per_block = {}
    for r in CFGR.CONFIG_REGISTRY:
        k = r.section.block.id
        per_block.setdefault(k, [0, 0])[0 if r.status != "blocked" else 1] += 1
    sub_calendar_rows = sum(1 for r in verdict_rows
                            if str(r.get("event", "")).startswith("sub_"))
    A(f"<p><b>Catalogue B is {n_ported}/{n_ported}. The configuration sections "
      f"are {cfg_ported}/{cfg_total} ported, {cfg_blocked} blocked. The "
      f"sub-tables are {len(SUBR.ported())}/{len(SUBR.SUBTABLE_REGISTRY)} "
      f"ported, {len(SUBR.blocked())} blocked.</b> Neither of the last two "
      f"sets was ever in the first's denominator &mdash; different shapes of "
      f"markup, counted separately &mdash; so <b>nothing on this page "
      f"should be read as \"the source is covered\"</b>. The counts come from "
      f"the document itself, not from this build's own config. The three "
      f"registries stay separate on purpose &mdash; neither a configuration "
      f"group nor a sub-table may reach catalogue B's denominator and inflate "
      f"{n_ported}/{n_ported} &mdash; but <b>all three are fired</b>, and of "
      f"the {len(verdict_rows):,} verdict rows below "
      f"<b>{cfg_calendar_rows:,} come from the configuration groups and "
      f"{sub_calendar_rows:,} from the sub-tables</b>.</p>")
    # A SECOND PAIR OF DENOMINATORS, AND IT IS NOT THE ONE ABOVE. The table
    # above counts SECTIONS PORTED. This counts ROWS REPRODUCED against the
    # source's own finished 2026 calendar, and the two are routinely confused
    # because both are called coverage. The figures come from conventions.yaml
    # rather than from this file, and carry the date they were read: the
    # fixture harness deliberately does not freeze them.
    td = CONF["verdict_coverage"]["two_denominators"]
    cov_n, cov_d = td["coverage"]["rate"]
    pre_n, pre_d = td["precision"]["rate"]
    A(f"<h2>A different pair of denominators &mdash; how much of the source's "
      f"own calendar this layer reproduces</h2>")
    A(f"<p>The table above counts <b>sections ported</b>. This counts <b>rows "
      f"reproduced</b>, against the source's own finished "
      f"{td['fixture_year']} monthly calendar "
      f"(<code>{_e(td['fixture'])}</code>). <b>Neither number below may be "
      f"quoted without the other.</b></p>")
    A(f"<table><thead><tr><th></th><th>rate</th><th>what it answers</th>"
      f"</tr></thead><tbody>"
      f"<tr><td><b>COVERAGE</b></td>"
      f"<td><b>{cov_n} of {cov_d}</b> ({round(cov_n * 100 / cov_d)}%)</td>"
      f"<td>of everything the source printed, how much the layer "
      f"reproduces</td></tr>"
      f"<tr><td><b>PRECISION</b>, conditional on a rule existing and firing"
      f"</td>"
      f"<td><b>{pre_n} of {pre_d}</b> ({round(pre_n * 100 / pre_d)}%)</td>"
      f"<td>of the rows some rule claims, how many land</td></tr>"
      f"</tbody></table>")
    A(f"<p><b>State the relationship, not just the pair.</b> "
      f"{round(pre_n * 100 / pre_d)}% would read as 100% for a layer with one "
      f"perfect rule and nothing else, so it is not a quality score; it "
      f"answers \"when we do claim a row, do we get it right\". And "
      f"{round(cov_n * 100 / cov_d)}% is not a failure score either &mdash; "
      f"131 of the 188 misses at the baseline were rows no rule was ever "
      f"written for.</p>")
    A(f"<p class=mut>Measured by <code>{_e(td['generator'])}</code> and read "
      f"here on {td['recorded']:%d-%b-%Y}. <b>A dated record, not a live "
      f"count:</b> this page renders {YEAR} and the fixture measures "
      f"{td['fixture_year']}, and the fixture harness pins the fixture and the "
      f"map but deliberately not the match result, which is the thing it "
      f"exists to measure.</p>")
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
      f"and their own configuration groups number "
      + " &middot; ".join(f"<b>{i} {CFG.by_instrument()[i]}</b>"
                          for i in CFG.INSTRUMENTS)
      + f", of which {cfg_ported} are ported and "
      f"<b>{cfg_rules_in_calendar} fire in {YEAR}</b>. <b>Those groups reach "
      f"this calendar directly</b>: {cfg_calendar_rows:,} of its "
      f"{len(rows):,} rows carry a configuration group as their rule, routed "
      f"to the instrument the source's own BLOCK heading names rather than "
      f"through the rulership table.</p>")
    # THE OLD TEST STILL PASSES AND ITS CONCLUSION IS NOW FALSE. This panel
    # used to offer `event_section` as the way to see that no row came from a
    # configuration group. It still never reads `gold-bullish` -- the field
    # carries the group's printed TITLE -- so a reader re-running the old test
    # gets the same answer and the opposite truth. Naming the field that does
    # work is the correction; deleting the old sentence silently is not.
    A(f"<p>What gold, silver and sugar got <i>before</i> that wiring is still "
      f"here and is still not the source's verdicts for them: a generic "
      f"catalogue-B rule reaches SUGAR because SUGAR's rulership is Venus, not "
      f"because the source says anything about sugar. The wiring added the "
      f"source's own conditions beside those rows and removed none of them. "
      f"<b>To tell the two apart, read <code>event</code>, not "
      f"<code>event_section</code></b>: a configuration row's rule id begins "
      f"<code>cfg_&lt;block&gt;_</code>. This panel used to say that "
      f"<code>event_section</code> never reads <code>gold-bullish</code>, and "
      f"it still never does &mdash; that field carries the group's own printed "
      f"title &mdash; so the old check passes and its old conclusion is "
      f"wrong.</p>")
    A(f"<p>There is a third unported body of material. The same chapter carries "
      f"{len(CFG.other_h2_tables())} further <code>&lt;h2&gt;</code> "
      f"sub-tables that are neither catalogue B nor any of the six blocks "
      f"above ("
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
    # The row-kind filter comes FIRST in the control strip, because every other
    # control below it means something different to the two populations: an
    # instrument filter hides every event row, a tier filter hides every event
    # row, and a reader who did not know there were two kinds would read that
    # as the calendar being empty.
    A('<select id=kind><option value="">both row kinds</option>'
      '<option value="verdict">verdict rows only</option>'
      '<option value="event">astronomy events only</option></select>')
    A('<select id=inst><option value="">all instruments</option></select>')
    A('<select id=tier><option value="">all tiers</option></select>')
    A('<label class=sub><input type=checkbox id=onlyv> only rows with a verdict'
      '</label>')
    A('<button id=reset>reset</button>')
    A('<span class=count id=count></span>')
    A("</div>")

    A("<table><thead><tr>"
      "<th>Kind</th>"
      "<th>Date (IST)</th><th>Time IST</th><th>Time ET</th><th>Date (ET)</th>"
      "<th>Instrument</th><th>Event</th><th>Vedic interpretation</th>"
      "<th>Financial-market theme</th><th>Tier / confidence</th>"
      "</tr></thead><tbody id=rows></tbody></table>")
    A("</div>")
    A(f"<script>const CAL_YEAR={YEAR};"
      f"const CAL_ROWS={json.dumps(js_rows, ensure_ascii=False)};"
      f"{JS}</script>")
    A("</body></html>")
    OUT_HTML.write_text("\n".join(P), encoding="utf-8", newline="\n")
    return OUT_HTML
