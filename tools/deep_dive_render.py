"""HTML sections for months of weekly deep dives (tools/week_deep_dive.py), used by tools/build_pdf_calendar.py to show
January and February 2027 in calendar_2027_NY_master.html. Self-contained: scoped CSS under .dd27, the page's colour variables.
"""
from __future__ import annotations

import datetime as dt
import glob
import html
import json
import pathlib

E = html.escape
MKS = (("spx", "S&P 500", "S&P"), ("sensex", "BSE Sensex", "Sensex"), ("gold", "Gold", "Gold"), ("silver", "Silver", "Silver"))
GOOD = ("Strongest", "Supported", "Consistent")
CSS = """<style>
.dd27{margin:14px 0 22px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.dd27 h2{font-size:18px;margin:0 0 6px}.dd27 h3{font-size:15px;margin:16px 0 6px}
.dd27 .call{border-left:4px solid var(--mix);padding:6px 10px;margin:8px 0;background:var(--bg)}
.dd27 table{border-collapse:collapse;width:100%;margin:6px 0}.dd27 th,.dd27 td{border:1px solid var(--line);padding:4px 6px;vertical-align:top;font-size:13px}
.dd27 th{background:var(--bg);text-align:left}.dd27 .s{font-size:12px;color:var(--mut)}.dd27 .wrap{overflow-x:auto}
.dd27 .up{color:var(--bull);font-weight:600}.dd27 .dn{color:var(--bear);font-weight:600}.dd27 .nav a{margin-right:10px}
.dd27 details{margin:4px 0}.dd27 summary{cursor:pointer}
</style>"""


TUNE = dict(on=False, note="", vol_ok=None)
SHORTN = {"spx": "S&P", "sensex": "Sensex"}


def set_tuning(out_dir):
    """The November 2026 review's changes (tools/november_review.py): Low labels are leans, the model's percentages are not coloured as calls."""
    f = pathlib.Path(out_dir) / "november_review_2026-11_ET.json"
    if not f.exists():
        return
    rec = {r["id"]: r for r in json.load(open(f)).get("recommendations", [])}
    if rec.get("labels", {}).get("applied") and rec.get("model", {}).get("applied"):
        TUNE.update(on=True, note=("After the November 2026 review (2026 calendar, section “November review”): Low labels are leans, not day calls, and the model's "
                                   "percentages are no longer coloured. Tested out of sample (2013–2026, everything chosen on earlier years), neither the labels nor the model "
                                   "beat chance on any market; treat both as leanings."))
    ok = rec.get("big_days", {}).get("vol_ok")
    if ok is not None and (pathlib.Path(out_dir) / "bigday_clean_test_ET.json").exists():
        TUNE["vol_ok"] = ok
        by = {}
        for mk, v in ok.items():
            for f_ in v:
                by.setdefault(f_, []).append(SHORTN.get(mk, mk))
        good = " and ".join(f"{f_} ({' and '.join(m)})" for f_, m in by.items()) or "no factor"
        TUNE["note"] += (f" Big days: in a clean test (factors chosen on 2000–2013 only) only {good} kept marking more big days after 2013; "
                         "a Volatile label from any other factor is marked “in sample only”.")


def load(pattern):
    return [json.load(open(f)) for f in sorted(glob.glob(str(pattern)))]


def _cell(st):
    h1, h5, bg = st["h1"], st["h5"], st["big"]
    if h1["up_pct"] is None:
        return "<td class='s'>–</td>"
    f1 = " ⚑" if (h1["p2"] or 1) < 0.05 else ""
    c5 = (" class='up'" if h5["up_pct"] > h5["base"] else " class='dn'") if (h5["p2"] or 1) < 0.05 else ""
    return (f"<td class='s'>next: {h1['up_pct']}% up vs {h1['base']}%{f1}<br><span{c5}>5 sessions: {h5['up_pct']}% vs {h5['base']}%</span>"
            f"<br>big day {bg['pct']}% (10% normal)</td>")


def day_events(dd, day):
    if not day["events"]:
        return "<p class='s'>No sky events today.</p>"
    rows = []
    for e in day["events"]:
        c = dd["classes"][e["key"]]
        rows.append(f"<tr><td class='s'>{E(e['et'])}<br>{E(e['ist'])}</td><td>{E(c['label'])}<div class='s'>{c['n_hist']} times since 2000</div></td>"
                    + "".join(_cell(c["stats"][k]) for k, _, _ in MKS) + "</tr>")
    return ("<div class='wrap'><table><thead><tr><th>ET / IST</th><th>Event</th>" + "".join(f"<th>{n}</th>" for _, _, n in MKS)
            + f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def day_row(day):
    lab = []
    for k, name, short in MKS:
        sg = day["signals"].get(name, {})
        pr = day["prob"].get(k)
        if day["closed"].get(k):
            lab.append(f"{short}: closed ({E(day['closed'][k])})")
        elif pr:
            sig = (sg.get("sig", "") + " " + sg.get("st", "")).strip()
            lean = pr["all"]["up1"] - pr["base"]["up1"]
            cls = "" if TUNE["on"] else " class='up'" if lean >= 2 else " class='dn'" if lean <= -2 else ""
            sig_h = f"<span style='color:var(--mut)'>{E(sig)} (lean)</span>" if TUNE["on"] and sg.get("st") == "Low" else E(sig)
            if TUNE["vol_ok"] is not None and sg.get("sig") == "Volatile":
                why = sg.get("why") if isinstance(sg.get("why"), str) else "; ".join(sg.get("why") or [])
                good = any(f in why for f in TUNE["vol_ok"].get(k, []))
                sig_h = E(sig) + (" (big-day factor passes a clean test)" if good else " <span style='color:var(--mut)'>(big-day factor in sample only)</span>")
            lab.append(f"{short}: {sig_h} · <span{cls}>{pr['all']['up1']:.0f}%</span> / {pr['all']['up5']:.0f}% (normal {pr['base']['up1']:.0f}% / {pr['base']['up5']:.0f}%)")
        else:
            lab.append(f"{short}: weekend")
    sup = []
    for k, _, short in MKS:
        c = day["rules"].get(k, {})
        sup.append(f"{short} {sum(v for s, v in c.items() if s in GOOD)} of {sum(c.values())}")
    notable = "; ".join(day["notable"].get("spx", [])[:2] + day["notable"].get("gold", [])[:1])
    sr = [x for x in (day.get("sr_call"), "; ".join(day["solar_return"]["rules"])) if x]
    return (f"<tr><td class='s'>{E(day['weekday'])} {E(day['date'][5:])}</td><td class='s'>{'<br>'.join(lab)}</td>"
            f"<td class='s'>{E(', '.join(sup))}<br>{E(notable)}</td><td class='s'>{E(' · '.join(sr) or 'month reading only')}</td>"
            f"<td class='s'>{E('; '.join(day.get('notes', [])[:4]))}</td><td class='s'>{E('; '.join(day['new_sources'][:3]))}</td></tr>")


def month_update_html(out_dir, key):
    """A coming month after the November review (tools/month_outlook.py): each kind of call, what it says, what it is worth."""
    y, m = map(int, key.split("-"))
    stem = f"{dt.date(y, m, 1):%B}".lower() + f"_{y}"
    f = pathlib.Path(out_dir) / f"{stem}_outlook_ET.json"
    if not f.exists():
        return ""
    o = json.load(open(f))
    v, fr, dd = o["verdicts"], o["frozen"], o["deep_dive"]
    rows = []
    for mk, name, _ in MKS:
        items = v[mk]["items"]
        for i, it in enumerate(items):
            mark = " class='up'" if it.get("level") in ("edge", "some") else ""
            rows.append("<tr>" + (f"<td rowspan='{len(items)}'><b>{E(name)}</b><div class='s'>{E(v[mk]['summary'])}</div></td>" if i == 0 else "")
                        + f"<td class='s'><b{mark}>{E(it['topic'])}</b>: {E(it['call'])}</td><td class='s'>{E(it['worth'])}</td></tr>")
    return (f"<div class='call'><b>Update ({E(o['made'][:10])}): {E(o['name'])} after the November review.</b> {E(o['headline'])} "
            "The week tables below are unchanged and read as leanings. "
            f"The sky-event deep dive: {dd['tests']} tests, {dd['significant']} pass the correction. "
            f"{E(o['name'].split()[0])}'s calls were frozen on {E(fr['frozen_at'])} ({E(fr['path'])}) so the month can be scored afterwards exactly as November was.</div>"
            "<div class='wrap'><table><thead><tr><th>Market</th><th>What the month's calls say</th><th>What they are worth</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></div><p class='s'>Green topic = some support (a clean test or a source rule's stated case); none is proven.</p>")


def section(dds, title=None, anchor="dd2027", css=True, extra=""):
    if not dds:
        return ""
    mon = dt.date.fromisoformat(dds[0]["start"])
    month = f"{mon:%B}"
    title = title or f"Deep dive: {mon:%B %Y}"
    n = sum(d["n_cells"] for d in dds)
    sig = sum(len(d["significant"]) for d in dds)
    nom = sum(len(d["nominal"]) for d in dds)
    big = sum(len(d["big_significant"]) for d in dds)
    chk = [c for d in dds for c in d["checks"]]
    ctx = dds[0].get("context", {})
    y = ctx.get("year", {})
    NM = {"spx": "S&P 500", "sensex": "Sensex", "gold": "gold", "silver": "silver"}
    hol = "; ".join(f"{dt.date.fromisoformat(k):%a %d %b} {name}: " + ", ".join(NM[m] for m, v in c.items() if v == name) + " closed"
                    for k, c in sorted(ctx.get("holidays", {}).items()) for name in dict.fromkeys(c.values())) or "none"
    mons = "".join(f"<li>{E(m['start'])}: navamsha 2nd-house rule {E(m['t8a'][0] or 'no call')}, 11th-house rule {E(m['t8b'][0] or 'no call')}; sahams "
                   + E(", ".join(f"{k} {v[0] or 'no call'}" for k, v in m["sahams"].items() if k != "Fortune")) + f"; Sun in house {m['sun_house']}</li>" for m in ctx.get("months", []))
    nav = "".join(f"<a href='#{anchor}-{d['start'][5:7]}{d['start'][8:]}'>{d['start'][8:]}–{d['end'][8:]} {mon:%b}</a>" for d in dds)
    o = [CSS if css else "", f"<section class='dd27' id='{anchor}'><h2>{E(title)}: every sky event backtested</h2><p class='nav s'>Weeks: {nav}</p>",
         f"<div class='call'><b>{n} tests over {len(dds)} weeks: {sig} pass the Benjamini–Hochberg correction</b> (within each week), and {nom} have a nominal p &lt; 0.05, "
         f"against about {round(n * 0.05)} expected by chance. Big days: {big} event classes pass. <b>" + ("The sky events of " + month + " carry no measurable direction or big-day signal." if not sig and not big else f"{sig + big} result(s) pass: see the week tables.") + "</b> "
         "Method: every event of each day (exact aspects, sign and nakshatra entries, stations, combustion and rising, eclipses, speed overtakes, the Sun's and Moon's apsides, tithi, yoga, Bhadra, lunations) is "
         "turned into its event class and scored on every occurrence from 20 Nov 2000 to 20 Nov 2026 on the S&amp;P 500, Sensex, gold and silver: next session and 5 sessions, "
         "two-sided, plus big days. The labels, the model and the rules with a supported record are built the same way as the December days of the 2026 calendar.<br>"
         f"<b>Double-checked:</b> {sum(c['ok'] for c in chk)} of {len(chk)} checks pass (event times re-derived from the ephemeris, occurrence counts against expected "
         "frequencies, one result per week recounted from raw prices with separate code, every sky event classified).<br>"
         f"<b>Holidays:</b> {E(hol)}. The BSE has not yet published its 2027 holiday list; only fixed holidays are assumed.<br>"
         + (f"<b>How far to trust the labels and the model:</b> {E(TUNE['note'])}<br>" if TUNE["on"] else "") +
         f"<b>The year:</b> lord of the year 2026–27 {E(y.get('lord_of_year_us', '?'))} (US time) or {E(y.get('lord_of_year_india', '?'))} (Indian time), watch list only. "
         f"NYSE ruler of the year {E(y.get('ruler', '?'))}, strength {y.get('ruler_strength', '?')}, house {y.get('ruler_house', '?')}. Both test at chance.</div>"]
    if extra:
        o.append(extra)
    if mons:
        o.append(f"<p class='s'><b>NYSE monthly charts (Tajika, Model B) in force during {month}, all at chance on the S&amp;P 1928–2026:</b></p><ul class='s'>{mons}</ul>")
    for dd in dds:
        a, b = dt.date.fromisoformat(dd["start"]), dt.date.fromisoformat(dd["end"])
        noms = "; ".join(f"{x['label']} ({x['market']}, {'next session' if x['horizon'] == 'h1' else '5 sessions'}: {x['up_pct']}% up vs {x['base']}%, p {x['p2']})" for x in dd["nominal"]) or "none"
        o.append(f"<h3 id='{anchor}-{a:%m%d}'>Week {a:%a %d %b} – {b:%a %d %b %Y}</h3>"
                 f"<p class='s'>{len(dd['classes'])} event classes, {dd['n_cells']} tests, {len(dd['significant'])} pass; nominal: {E(noms)}. "
                 f"Checks: {sum(c['ok'] for c in dd['checks'])}/{len(dd['checks'])}.</p>"
                 "<div class='wrap'><table><thead><tr><th>Day</th><th>Labels (table) and model: up that day / over 5 sessions vs normal</th>"
                 "<th>Catalogue rules active with a supported record</th><th>Solar return</th><th>Kartari and gold notes</th><th>New sources</th></tr></thead><tbody>"
                 + "".join(day_row(d) for d in dd["days"]) + "</tbody></table></div>")
        for d in dd["days"]:
            o.append(f"<details><summary>{E(d['weekday'])} {dt.date.fromisoformat(d['date']):%d %b}: every sky event backtested ({len(d['events'])})</summary>"
                     + day_events(dd, d)
                     + (f"<p class='s'>{E(d['sr_month'])}</p>" if d.get("sr_month") else "")
                     + (f"<p class='s'>Solar return forecasts: {E('; '.join(d['solar_return']['forecasts']))}</p>" if d["solar_return"].get("forecasts") else "")
                     + "</details>")
    o.append("<p class='s'>⚑ = next-session p &lt; 0.05; coloured 5-session figure = p &lt; 0.05 (up or down). Nothing in this section passes the multiple-testing correction. "
             "The model column is the combined model of the 2026 calendar (fitted to 23 Nov 2026); the labels are the published signal tables to the end of 2027."
             + (" Grey “(lean)” = a Low label." if TUNE["on"] else "") + "</p></section>")
    return "".join(o)


def all_months(pattern_dir):
    """Every 2027 month with deep dives, one section each (January keeps the anchor dd2027 that the 2026 calendar links to)."""
    import collections
    set_tuning(pattern_dir)
    by = collections.OrderedDict()
    for d in load(pathlib.Path(pattern_dir) / "deep_dive_2027-*_ET.json"):
        by.setdefault(d["start"][:7], []).append(d)
    if not by:
        return ""
    anchors = {k: ("dd2027" if k == "2027-01" else f"dd{k.replace('-', '')}") for k in by}
    index = " · ".join(f"<a href='#{anchors[k]}'>{dt.date.fromisoformat(k + '-01'):%B %Y}</a>" for k in by)
    out = [CSS, f"<p class='m'><b>Deep dives (every sky event backtested, week by week):</b> {index}</p>"]
    for k, dds in by.items():
        out.append(section(dds, anchor=anchors[k], css=False, extra=month_update_html(pattern_dir, k)))
    return "".join(out)
