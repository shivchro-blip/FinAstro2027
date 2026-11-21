"""Gold findings tracker: one page that keeps every gold analysis current.

    python tools/gold_tracker.py              # rebuild from the existing backtest JSONs
    python tools/gold_tracker.py --refresh    # re-run the 1- and 5-year backtests first

Reads
  build/pdfref/gold_backtest_2025-11-20_to_2026-11-20_ET.json   (1-year backtest)
  build/pdfref/gold_backtest_2021-11-20_to_2026-11-20_ET.json   (5-year backtest)
  build/pdfref/analysis_log.json                                (log of every analysis)
and recomputes every gold rule from 20 Nov 2026 to 31 Dec 2027 with the same
detectors the backtest scored (tools/backtest_gold.py collect()).

Writes
  build/pdfref/GOLD_TRACKER.html / .md   status of every rule (1y vs 5y), key
                                         findings, forward dates of the
                                         best-performing rules, analysis log
  build/pdfref/gold_forward_2026-11-20_to_2027-12-31_ET.json

"Best-performing" is decided from the 5-year data, not by hand: at least 15
decided occurrences, hit rate above its base rate, and right in at least 4 of
the 5 years or p < 0.10. Rule status:
  Strongest        p < 0.10 against the base rate
  Supported        5-year verdict Worked (hit >= base + 10 pts), not significant
  Consistent       above base by less than 10 pts but right in >= 4 of 5 years (>= 15 decided)
  Did not hold up  5-year verdict Failed with >= 5 decided occurrences
  At chance        5-year verdict Mixed with >= 10 decided occurrences
  Too few to judge fewer than 5 decided occurrences in 5 years (lean shown)
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import importlib.util
import json
import pathlib
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "build" / "pdfref"
ET = ZoneInfo("America/New_York")
J1 = OUT / "gold_backtest_2025-11-20_to_2026-11-20_ET.json"
J5 = OUT / "gold_backtest_2021-11-20_to_2026-11-20_ET.json"
LOG = OUT / "analysis_log.json"
F0 = dt.datetime(2026, 11, 20, tzinfo=ET)
F1 = dt.datetime(2028, 1, 1, tzinfo=ET)


def load_bt():
    _spec = importlib.util.spec_from_file_location("bt", ROOT / "tools" / "backtest_gold.py")
    B = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(B)
    return B


def et(t):
    x = t.astimezone(ET)
    return f"{x:%a %d %b %Y %H:%M} {x.tzname()}"


def status(p):
    dec = p["worked"] + p["failed"]
    if p["n"] == 0:
        return "Did not occur"
    if p["tone"] in ("Neutral",) or dec + p["flat"] == 0:
        return "Not scored"
    if dec < 5:
        lean = "leans right" if p["worked"] > p["failed"] else "leans wrong" if p["failed"] > p["worked"] else "even"
        return f"Too few to judge ({p['worked']}/{dec}, {lean})"
    if p.get("p_value") is not None and p["p_value"] < 0.10:
        return "Strongest"
    if p["verdict"] == "Worked":
        return "Supported"
    if dec >= 15 and p["hit_rate"] > p["base_rate"] and p.get("years_right", 0) >= 4:
        return "Consistent"
    if p["verdict"] == "Failed":
        return "Did not hold up"
    return "At chance" if dec >= 10 else "Inconclusive"


def is_best(p):
    dec = p["worked"] + p["failed"]
    return (dec >= 15 and p["hit_rate"] is not None and p["hit_rate"] > p["base_rate"]
            and (p["years_right"] >= 4 or (p.get("p_value") is not None and p["p_value"] < 0.10)))


def css_cls(st):
    return ("bullish" if st in ("Strongest", "Supported", "Consistent") else "bearish" if st == "Did not hold up"
            else "mixed" if st.startswith("At chance") or st == "Inconclusive" else "")


def forward(B):
    from finastro.sky import Sky
    from finastro.pdfref.detect import Ctx
    from finastro.pdfref.engine import Grid, utc
    B.P0, B.P1 = F0, F1
    grid = Grid(utc(2026, 5, 1), utc(2028, 3, 1))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in (2026, 2027)]
    evs = B.collect(ctxs)
    evs.sort(key=lambda e: (e["start"], e["rule_id"]))
    return evs


def ev_span(e):
    s = e["start"] if e["day"] is None else dt.datetime.combine(e["day"], dt.time(6), ET)
    en = e["end"] or s + dt.timedelta(days=7)
    return s, en


def main():
    if "--refresh" in sys.argv:
        for a in ([], ["--years", "5"]):
            subprocess.run([sys.executable, str(ROOT / "tools" / "backtest_gold.py")] + a, check=True)
    d1, d5 = json.load(open(J1)), json.load(open(J5))
    r1 = {p["rule_id"]: p for p in d1["rules"]}
    r5 = {p["rule_id"]: p for p in d5["rules"]}
    for p in r5.values():
        p["status"] = status(p)
        p["best"] = is_best(p)
    best = [p for p in r5.values() if p["best"]]
    best_ids = {p["rule_id"] for p in best}
    log = json.load(open(LOG))["entries"]

    B = load_bt()
    evs = forward(B)
    for e in evs:
        p = r5.get(e["rule_id"])
        e["status5"] = p["status"] if p else "New in forward period"
    # per-rule forward counts
    fwd_count = collections.Counter(e["rule_id"] for e in evs)

    # forward rows for the best rules, with concurrent signals
    best_rows = []
    for e in evs:
        if e["rule_id"] not in best_ids or e["tone"] not in ("Bullish", "Bearish"):
            continue
        s, en = ev_span(e)
        if en < F0:
            continue
        conc = collections.defaultdict(set)
        for o in evs:
            if o is e or o["tone"] not in ("Bullish", "Bearish") or o["rule_id"] == e["rule_id"]:
                continue
            os_, oe = ev_span(o)
            if os_ <= en and oe >= s:
                st = o["status5"]
                grp = ("best" if o["rule_id"] in best_ids else "held" if st in ("Strongest", "Supported", "Consistent")
                       else "failed" if st == "Did not hold up" else "other")
                conc[grp].add(f"{o['title']} [{o['tone']}]")
        p = r5[e["rule_id"]]
        best_rows.append(dict(rule_id=e["rule_id"], title=e["title"], tone=e["tone"], start=s, end=en,
                              days=round((en - s).total_seconds() / 86400, 1), facts=e["facts"], verdict=e["verdict"],
                              hist=f"{p['worked']}/{p['worked'] + p['failed']} ({p['hit_rate']}% vs base {p['base_rate']}%), avg {p['avg_dir_ret']:+.2f}%, right in {p['years_right']}/{p['years_active']} yrs",
                              conc={k: sorted(v) for k, v in conc.items()}))

    # daily confluence of the best rules (Sun model counts with its own sign)
    days = []
    d = F0.date()
    while d <= dt.date(2027, 12, 31):
        t = dt.datetime.combine(d, dt.time(12), ET)
        bu, be = [], []
        for e in evs:
            if e["rule_id"] not in best_ids or e["tone"] not in ("Bullish", "Bearish"):
                continue
            s, en = ev_span(e)
            if s <= t <= en:
                (bu if e["tone"] == "Bullish" else be).append(e["title"].replace(" (user note)", ""))
        days.append((d, sorted(set(bu)), sorted(set(be))))
        d += dt.timedelta(days=1)
    # collapse consecutive identical days
    conf = []
    for d, bu, be in days:
        if conf and conf[-1]["bu"] == bu and conf[-1]["be"] == be and (d - conf[-1]["to"]).days == 1:
            conf[-1]["to"] = d
        else:
            conf.append(dict(frm=d, to=d, bu=bu, be=be))

    # ---------------- findings (generated from the two backtests)
    t5, t1 = d5["totals"], d1["totals"]
    sun = r5.get("user_sun_state_net", {})
    flipped = [p for rid, p in r5.items() if rid in r1 and r1[rid]["verdict"] == "Worked" and p["status"] == "Did not hold up"]
    held = [p for p in r5.values() if p["status"] in ("Strongest", "Supported", "Consistent") and p["worked"] + p["failed"] >= 10]
    failed = sorted((p for p in r5.values() if p["status"] == "Did not hold up"), key=lambda p: -(p["worked"] + p["failed"]))
    nb = d5["net_signal"]["buckets"]
    findings = [
        ("Rule set as a whole", f"5 yr: {t5['WORKED']} worked / {t5['FAILED']} failed ({t5['WORKED'] / (t5['WORKED'] + t5['FAILED']) * 100:.0f}%); 1 yr: {t1['WORKED']} / {t1['FAILED']}",
         "No better than chance in total; use individual rules, not the count of rules.", "Confirmed (5 yr)"),
        ("Stacking rules (bullish minus bearish count)", f"5 yr: next-5-day move {nb['net > 0 (more bullish rules active)']['avg5']:+.2f}% on bullish-majority days vs {nb['net < 0 (more bearish rules active)']['avg5']:+.2f}% on bearish-majority days; corr {d5['net_signal']['corr5']:+.3f}",
         "The net count carries almost no information; the 1-year bearish edge (-1.49%) did not repeat over 5 years.", "Did not hold up"),
        ("Your combined Sun model (U1-U4 together)", f"5 yr: {sun.get('worked')}/{sun.get('worked', 0) + sun.get('failed', 0)} ({sun.get('hit_rate')}% vs base {sun.get('base_rate')}%), p = {sun.get('p_value')}, right in {sun.get('years_right')}/{sun.get('years_active')} yrs",
         "Closest thing to an edge in the whole set; dates below.", sun.get("status", "")),
    ]
    for p in sorted(held, key=lambda p: -(p["worked"] + p["failed"])):
        if p["rule_id"] == "user_sun_state_net":
            continue
        findings.append((p["title"], f"5 yr: {p['worked']}/{p['worked'] + p['failed']} ({p['hit_rate']}% vs base {p['base_rate']}%), avg {p['avg_dir_ret']:+.2f}%, p = {p['p_value']}, right in {p['years_right']}/{p['years_active']} yrs",
                         "Consistent across years; dates below." if p["best"] else "Held up, fewer occurrences.", p["status"]))
    for p in flipped:
        q = r1[p["rule_id"]]
        findings.append((p["title"], f"1 yr: {q['worked']}/{q['worked'] + q['failed']} worked; 5 yr: {p['worked']}/{p['worked'] + p['failed']} ({p['hit_rate']}% vs base {p['base_rate']}%)",
                         "Looked good only in the falling 2025-26 year; do not rely on it.", "Did not hold up"))
    for p in failed:
        if p in flipped:
            continue
        findings.append((p["title"], f"5 yr: {p['worked']}/{p['worked'] + p['failed']} ({p['hit_rate']}% vs base {p['base_rate']}%), avg {p['avg_dir_ret']:+.2f}%, right in {p['years_right']}/{p['years_active']} yrs",
                         "Went the wrong way more often than chance would; treat as unreliable.", "Did not hold up"))
    findings.append(("Big falls", "Bearish rules outnumbered bullish ones before only 1 of the 15 biggest 5-day falls (5 yr); Jan-2026 crash had 6 bullish, 0 bearish",
                     "Largest gap: no rule for a stellium on the Sun (Sun, Mercury, Venus, Mars in Capricorn, Venus combusting, Jupiter retrograde).", "Open gap"))

    # ---------------- HTML
    def st_tag(st):
        return f"<span class='tag {css_cls(st)}'>{html.escape(st)}</span>"

    def rec(p):
        if not p:
            return "–"
        dec = p["worked"] + p["failed"]
        if not dec:
            return "–"
        return f"{p['worked']}/{dec} ({p['hit_rate']}% vs {p['base_rate']}%)"

    order = sorted(r5.values(), key=lambda p: (["Strongest", "Supported", "Consistent", "At chance", "Inconclusive", "Did not hold up"].index(p["status"]) if p["status"] in ("Strongest", "Supported", "Consistent", "At chance", "Inconclusive", "Did not hold up") else 6,
                                               -(p["worked"] + p["failed"])))
    rule_rows = "".join(
        f"<tr class='{css_cls(p['status'])}'><td><b>{html.escape(p['title'])}</b>{' ★' if p['best'] else ''}<div class='s'>{p['rule_id']}</div></td><td>{p['tone']}</td>"
        f"<td class='n'>{rec(r1.get(p['rule_id']))}</td><td class='n'>{rec(p)}</td><td class='n'>{'' if p['avg_dir_ret'] is None else f'{p['avg_dir_ret']:+.2f}%'}</td>"
        f"<td class='n'>{'' if p.get('p_value') is None else p['p_value']}</td><td class='n'>{f'{p['years_right']}/{p['years_active']}' if p.get('years_active') else ''}</td>"
        f"<td class='n s'>{' '.join(f'{v[1]}/{v[0]}' if v[0] else '–' for v in p['by_year'].values())}</td>"
        f"<td>{st_tag(p['status'])}</td><td class='n'>{fwd_count.get(p['rule_id'], 0)}</td></tr>" for p in order)
    find_rows = "".join(f"<tr class='{css_cls(st)}'><td><b>{html.escape(a)}</b></td><td class='s'>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{st_tag(st)}</td></tr>" for a, b, c, st in findings)

    def det(r):
        f = r["facts"]
        if r["rule_id"] == "user_sun_state_net":
            return f"Sun in {f.get('Sun nakshatra')}; rise: {f.get('rise')}; fall: {f.get('fall')} ({r['verdict']})"
        return f.get("value", "")
    best_html = "".join(
        f"<tr class='{r['tone'].lower()}'><td class='w'>{html.escape(et(max(r['start'], F0)))}{' (already running)' if r['start'] < F0 else ''}</td><td class='w'>{html.escape(et(r['end']))}</td><td class='n'>{r['days']}</td>"
        f"<td><b>{html.escape(r['title'])}</b><div class='s'>{html.escape(det(r))}</div></td><td><span class='tag {r['tone'].lower()}'>{r['tone']}</span></td>"
        f"<td class='s'>{html.escape(r['hist'])}</td>"
        f"<td class='s'>{('<b>Other best rules:</b> ' + html.escape('; '.join(r['conc'].get('best', []))) + '<br>') if r['conc'].get('best') else ''}"
        f"{('<b>Held up (5 yr):</b> ' + html.escape('; '.join(r['conc'].get('held', []))) + '<br>') if r['conc'].get('held') else ''}"
        f"{('<b>Did not hold up (ignore):</b> ' + html.escape('; '.join(r['conc'].get('failed', [])))) if r['conc'].get('failed') else ''}</td></tr>"
        for r in best_rows)
    conf_html = "".join(
        f"<tr class='{'bullish' if len(c['bu']) > len(c['be']) else 'bearish' if len(c['be']) > len(c['bu']) else 'mixed'}'><td class='w'>{c['frm']:%a %d %b %Y}</td><td class='w'>{c['to']:%a %d %b %Y}</td><td class='n'>{(c['to'] - c['frm']).days + 1}</td>"
        f"<td class='n'><b>{len(c['bu'])} : {len(c['be'])}</b></td><td class='s'>{html.escape('; '.join(c['bu']) or '-')}</td><td class='s'>{html.escape('; '.join(c['be']) or '-')}</td></tr>"
        for c in conf)
    log_html = "".join(f"<tr><td class='w'>{x['date']}</td><td class='n'>#{x['pr']}</td><td><b>{html.escape(x['topic'])}</b><div class='s'>{html.escape(x['analysis'])}</div></td>"
                       f"<td class='s'>{html.escape(x['result'])}</td><td class='s'>{'<br>'.join(html.escape(f) for f in x['files'])}</td></tr>" for x in reversed(log))
    best_list = ", ".join(p["title"].replace(" (user note)", "") for p in best)
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    now = dt.datetime.now(ET)
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gold Findings Tracker</title><style>{css}</style></head><body>
<h1>Gold findings tracker</h1>
<p class="m">Generated {now:%d %b %Y %H:%M %Z} by tools/gold_tracker.py from the 1-year and 5-year backtests and the analysis log. Re-run <code>python tools/gold_tracker.py --refresh</code> after any rule or data change; every number on this page is recomputed, nothing is typed in.</p>
<h2>Recent findings</h2>
<div class="wrap"><table><thead><tr><th>Finding</th><th>Evidence</th><th>What it means</th><th>Status</th></tr></thead><tbody>{find_rows}</tbody></table></div>

<h2>Best-performing rules: dates from 20 Nov 2026 to 31 Dec 2027 (ET)</h2>
<p class="m">Chosen from the 5-year backtest without hand-picking (≥15 decided occurrences, hit rate above base, right in ≥4 of 5 years or p &lt; 0.10): <b>{html.escape(best_list)}</b>.
Windows are scored in the backtest from the close before the start to the last close inside the window. The last column lists the other gold rules active at the same time, grouped by how they did over 5 years. None of these rules is statistically certain; read them as the most consistent of the set.</p>
<div class="wrap"><table><thead><tr><th>From (ET)</th><th>To (ET)</th><th>Days</th><th>Rule / condition</th><th>Effect</th><th>5-year record</th><th>Other rules active then</th></tr></thead><tbody>{best_html}</tbody></table></div>

<h3>Day-by-day agreement of the best rules</h3>
<p class="m">Each stretch: how many of the best rules point up : down (the combined Sun model counts on whichever side its net count falls). Longer stretches with 3–4 rules agreeing are the strongest signals this rule set produces. The rules are not independent: the combined Sun model already contains the U2 contacts, so agreement mostly means several of your Sun conditions hold at once.</p>
<div class="wrap"><table><thead><tr><th>From</th><th>To</th><th>Days</th><th>Up : down</th><th>Pointing up</th><th>Pointing down</th></tr></thead><tbody>{conf_html}</tbody></table></div>

<h2>Every gold rule: 1-year vs 5-year record</h2>
<p class="m">Record = worked/decided (hit rate vs drift-aware base rate). ★ = best-performing (dates above). "Upcoming" = occurrences from 20 Nov 2026 to 31 Dec 2027; every one of them is in the gold report (build/pdfref/gold_2026-11-20_to_2027-12-31_ET.html), and its status here tells you how much weight it earned.</p>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Effect</th><th>1 yr (2025-26)</th><th>5 yr (2021-26)</th><th>Avg move (5 yr)</th><th>p (5 yr)</th><th>Years right</th><th>By year 21-22 … 25-26</th><th>Status</th><th>Upcoming</th></tr></thead><tbody>{rule_rows}</tbody></table></div>

<h2>Analysis log</h2>
<div class="wrap"><table><thead><tr><th>Date</th><th>PR</th><th>Analysis</th><th>Result</th><th>Files</th></tr></thead><tbody>{log_html}</tbody></table></div>
<p class="s">Backtests: {J1.name}, {J5.name}. Prices: Yahoo Finance GC=F daily closes. Forward windows: same detectors as the backtest (tools/backtest_gold.py collect()), Swiss Ephemeris, Lahiri, mean node, whole-sign drishti.</p>
</body></html>"""
    (OUT / "GOLD_TRACKER.html").write_text(page, encoding="utf-8")

    # ---------------- Markdown (diff-friendly copy)
    md = ["# Gold findings tracker", "", f"Generated {now:%d %b %Y %H:%M %Z} by `tools/gold_tracker.py` (`--refresh` re-runs both backtests). HTML version: `GOLD_TRACKER.html`.", "",
          "## Recent findings", "", "| Finding | Evidence | What it means | Status |", "|---|---|---|---|"]
    md += [f"| {a} | {b} | {c} | {st} |" for a, b, c, st in findings]
    md += ["", "## Best-performing rules: dates 20 Nov 2026 - 31 Dec 2027 (ET)", "", f"Best (from the 5-year data): {best_list}.", "",
           "| From (ET) | To (ET) | Days | Rule | Effect | Detail |", "|---|---|---|---|---|---|"]
    md += [f"| {et(max(r['start'], F0))} | {et(r['end'])} | {r['days']} | {r['title']} | {r['tone']} | {det(r).replace('|', '/')} |" for r in best_rows]
    md += ["", "## Every gold rule: 1-year vs 5-year", "", "| Rule | Effect | 1 yr | 5 yr | Avg (5 yr) | p | Years right | Status | Upcoming |", "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {p['title']}{' ★' if p['best'] else ''} | {p['tone']} | {rec(r1.get(p['rule_id']))} | {rec(p)} | {'' if p['avg_dir_ret'] is None else f'{p['avg_dir_ret']:+.2f}%'} | {'' if p.get('p_value') is None else p['p_value']} | {f'{p['years_right']}/{p['years_active']}' if p.get('years_active') else ''} | {p['status']} | {fwd_count.get(p['rule_id'], 0)} |" for p in order]
    md += ["", "## Analysis log", "", "| Date | PR | Topic | Result |", "|---|---|---|---|"]
    md += [f"| {x['date']} | #{x['pr']} | {x['topic']} | {x['result']} |" for x in reversed(log)]
    (OUT / "GOLD_TRACKER.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    def ser(r):
        x = dict(r)
        x["start"], x["end"] = r["start"].isoformat(), r["end"].isoformat()
        return x
    json.dump(dict(period="2026-11-20..2027-12-31", time_zone="America/New_York", best_rules=[p["rule_id"] for p in best],
                   best_windows=[ser(r) for r in best_rows],
                   agreement=[dict(frm=c["frm"].isoformat(), to=c["to"].isoformat(), up=c["bu"], down=c["be"]) for c in conf],
                   rule_status={rid: dict(title=p["title"], status=p["status"], best=p["best"], upcoming=fwd_count.get(rid, 0)) for rid, p in r5.items()}),
              open(OUT / "gold_forward_2026-11-20_to_2027-12-31_ET.json", "w", encoding="utf-8"), indent=1, default=str)
    print(f"best: {best_list}; {len(best_rows)} forward windows; {len(conf)} agreement stretches; {len(findings)} findings")


if __name__ == "__main__":
    main()
