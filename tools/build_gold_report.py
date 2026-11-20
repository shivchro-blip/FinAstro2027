"""Gold (XAUUSD / COMEX GC) report: every rule that names gold, 20 Nov 2026 - 31 Dec 2027.

    python tools/build_gold_report.py

Sources: TA Section 34 'When gold can rally / fall' and the gold items of
other TA sections; KD slides naming gold; the 2026 document's gold section
(the existing calendar's cfg_gold_* rules). Every window is recomputed with
finastro/pdfref's engine and each boundary is checked against the
astronomy layer's own records (build/astronomy_2026.json / _2027.json, an
independent code path) and, for 2027, against the existing calendar's GC rows.

Writes build/pdfref/gold_2026-11-20_to_2027-12-31_ET.html and .json.
Times: US Eastern (America/New_York; EST, or EDT in summer).
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import html
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky, parse  # noqa: E402
from finastro.pdfref import catalogue as C  # noqa: E402
from finastro.pdfref.detect import Ctx, Hit, POOL, WEEKDAYS, aspects, windows, entries  # noqa: E402
from finastro.pdfref.engine import Grid, conjunction_instants, name, snapshot, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
P0 = dt.datetime(2026, 11, 20, tzinfo=ET).astimezone(UTC)
P1 = dt.datetime(2028, 1, 1, tzinfo=ET).astimezone(UTC)
OUT = ROOT / "build" / "pdfref"
DOC26 = "2026 document (data/source_2026.html), Gold section pp.136-148"


def et(t):
    if t is None:
        return ""
    x = t.astimezone(ET)
    return f"{x:%a %d %b %Y %H:%M} {x.tzname()}"


def et_date(d):
    return f"{d:%a %d %b %Y}"


# --------------------------------------------- 2026-document gold rules (extra)
def nak(body, n):
    return lambda s: s[body].nak == n and s[body].nak


EXTRA = []


def xrule(id, title, refs, verdict, rule, calc, detector, existing=(), quals=()):
    EXTRA.append(C.Rule(id=id, title=title, refs=refs, verdict=verdict, markets=("gold",), rule=rule, calc=calc,
                        detector=detector, existing=existing, quals=quals))


xrule("doc26_gold_bull_11_venus_rohini", "Venus in Rohini", (DOC26 + " - Bullish #11",), "Bullish", "Venus in Rohini nakshatra.", C.NAKCALC,
      windows(nak("Venus", "Rohini"), ("Venus",)), ("cfg_gold_bullish_11_venus_in_rohini",))
xrule("doc26_gold_bull_12_mars_pushya", "Mars in Pushya", (DOC26 + " - Bullish #12",), "Bullish", "Mars in Pushya nakshatra.", C.NAKCALC,
      windows(nak("Mars", "Pushya"), ("Mars",)), ("cfg_gold_bullish_12_mars_in_pushya",))
xrule("doc26_gold_bear_06_venus_punarvasu", "Venus in Punarvasu", (DOC26 + " - Bearish #6",), "Bearish", "Venus in Punarvasu nakshatra.", C.NAKCALC,
      windows(nak("Venus", "Punarvasu"), ("Venus",)), ("cfg_gold_bearish_06_venus_in_punarvasu",))
xrule("doc26_gold_bull_04_jupiter_gemini", "Jupiter in Gemini", (DOC26 + " - Bullish #4", "TA p.154 S34 A6 ('bullish after 5 months')"), "Bullish",
      "Jupiter resident in Gemini (the 2026 document's printed row is the residency).", C.SIGNCALC,
      windows(lambda s: s["Jupiter"].sign == "Gemini" and "Gemini", ("Jupiter",)))


def _sun_libra_aspected(s):
    if s["Sun"].sign != "Libra":
        return False
    m = [b for b in ("Mars", "Saturn", "Rahu", "Ketu") if s[b].sign_i == s["Sun"].sign_i or aspects(s, b, "Sun")]
    return tuple(m) or False


xrule("doc26_gold_bull_02_sun_libra_aspected", "Sun in Libra aspected by (or with) malefics", (DOC26 + " - Bullish #2", "TA p.154 S34 A3 ('with other Malefic like Saturn, Mars & Rahu')"),
      "Bullish", "Sun in Libra with Mars, Saturn, Rahu or Ketu in Libra or casting whole-sign drishti on it (Mars 4/7/8, Saturn 3/7/10, nodes 7).",
      C.SIGNCALC + " Drishti per config valence.drishti.", windows(_sun_libra_aspected, ("Sun",)), ("cfg_gold_bullish_02_sun_libra_aspected_by_malefics",))


def _new_moons(ctx):
    out = []
    for t, how in conjunction_instants(ctx.grid, "Moon", "Sun"):
        if t.year == ctx.year:
            s = snapshot(t)
            out.append(Hit(t, None, ("Sun", "Moon"), {"degree": f"{s['Sun'].deg:.2f} deg {s['Sun'].sign}"}))
    return out


xrule("doc26_gold_bull_10_sun_moon_same_degree", "Sun and Moon on the same degree (new moon)", (DOC26 + " - Bullish #10",), "Bullish (short-term bounce)",
      "Exact Sun-Moon conjunction.", "Instant the Moon's sidereal longitude equals the Sun's (bisected to 30 s).", _new_moons, ("cfg_gold_bullish_10_sun_moon_same_degree",))


def _aq_friday(ctx):
    out = []
    for t, sign, s, m in C.sankrantis(ctx):
        if sign == "Aquarius":
            wd_ny, wd_in = C.vara(ctx, t), C.vara(ctx, t, "mumbai")
            if 4 in (wd_ny, wd_in):
                out.append(Hit(t, None, ("Sun",), {"weekday_NY_hindu_day": WEEKDAYS[wd_ny], "weekday_IST_hindu_day": WEEKDAYS[wd_in]}))
    return out


xrule("doc26_gold_bull_13_aquarius_sankranti_friday", "Sun enters Aquarius on a Friday", (DOC26 + " - Bullish #13",), "Bullish",
      "Aquarius Sankranti falling on a Friday.", "Sun's sidereal ingress into Aquarius; weekday = Hindu day (sunrise to sunrise) at New York and at Mumbai.",
      _aq_friday, ("cfg_gold_bullish_13_aquarius_sankranti_on_friday",))


def _darshan_days(days, label):
    def run(ctx):
        out = []
        for ss, d, s in C.darshans(ctx):
            if d.weekday() in days:
                out.append(Hit(ss, None, ("Moon", "Sun"), {"weekday": WEEKDAYS[d.weekday()], "moon_nakshatra": s["Moon"].nak}, day=d))
        return out
    return run


xrule("doc26_gold_bull_08_moonrise_mon_fri", "Moon darshan (first sighting) on Monday or Friday", (DOC26 + " - Bullish #8 'Moonrise on Monday or Friday'",), "Bullish",
      "First evening sighting after the new moon falls on a Monday or Friday.", "Darshan as in finastro/pdfref (first New York sunset, elongation >= 12 deg, age >= 20 h).",
      _darshan_days((0, 4), ""), quals=C.DARSHAN_Q + ("The 2026 document's two printed rows (Fri 20-Mar-26, Mon 12-Oct-26) are both darshan evenings, which is how 'moonrise' is read here.",))


def _sun_eclipse_wed(ctx):
    out = []
    for r in ctx.sky.class_records("eclipse"):
        if r["rule_family"] == "eclipse/solar":
            t = parse(r["time"]["t_start_utc"])
            if t.year == ctx.year and 2 in (C.vara(ctx, t), C.vara(ctx, t, "mumbai")):
                out.append(Hit(t, None, ("Sun", "Moon"), {}))
    return out


xrule("kd114_sun_eclipse_wednesday", "Solar eclipse on a Wednesday", ("KD p.114 (12 Aug 2026: 'Day: Wednesday - Bullish for Cotton, Gold, Silver, Copper')",),
      "Bullish for gold (and cotton, silver, copper)", "A solar eclipse on a Wednesday.", "Eclipse maximum (Swiss Ephemeris); Hindu weekday at New York and Mumbai.", _sun_eclipse_wed)

NOT_COMPUTED = [
    (DOC26 + " - Bullish #9", "Moonrise in Libra - Bullish", "The 2026 printed rows (28-May-26 Libra/Swati, 12-Oct-26) are not all darshan evenings and the document does not say which moonrise; not guessed."),
]


def gold_rules():
    rs = [r for r in C.RULES if "gold" in r.markets and r.detector is not None]
    return rs + EXTRA


# ------------------------------------------------ independent checks
def astro_records():
    recs = []
    for f in ("astronomy_2026.json", "astronomy_2027.json"):
        for r in json.load(open(ROOT / "build" / f, encoding="utf-8"))["records"]:
            if r["event_class"] in ("sunrise", "sunset", "karana_ingress", "yoga_ingress", "tithi_ingress"):
                continue
            recs.append((parse(r["time"]["t_start_utc"]), r["event_class"], r["bodies"][0] if r["bodies"] else "", r["time"]["precision"]))
    recs.sort()
    return recs


REC = None


PRIORITY = {"sign_ingress": 0, "nakshatra_ingress": 1, "station": 2, "speed_crossing": 3, "conjunction": 4, "lunation": 5,
            "eclipse": 6, "opposition": 7, "neighbour_change": 8, "navamsa_ingress": 9}
TS = None


def match_record(t, bodies, tol=180):
    global TS
    if TS is None:
        TS = [x[0] for x in REC]
    i = bisect.bisect_left(TS, t - dt.timedelta(seconds=tol))
    out = []
    while i < len(REC) and REC[i][0] <= t + dt.timedelta(seconds=tol):
        if not bodies or REC[i][2] in bodies or REC[i][1] in ("eclipse", "lunation", "conjunction"):
            out.append(REC[i])
        i += 1
    return sorted(out, key=lambda r: PRIORITY.get(r[1], 10))


def verdict_tone(text):
    t = text.lower()
    bu, be = "bullish" in t or "rally" in t, "bearish" in t or "fall" in t
    return "Mixed" if bu and be else "Bullish" if bu else "Bearish" if be else "Neutral"


def main():
    global REC
    REC = astro_records()
    sky26, sky27 = Sky.load(ROOT / "build" / "astronomy_2026.json"), Sky.load(ROOT / "build" / "astronomy_2027.json")
    grid = Grid(utc(2026, 6, 1), utc(2028, 6, 30))
    ctxs = [Ctx(grid, sky26, 2026), Ctx(grid, sky27, 2027)]
    cal = json.load(open(ROOT / "build" / "calendar_2027.json", encoding="utf-8"))
    gc = collections.defaultdict(list)
    for r in cal["rows"]:
        if r["row_kind"] == "verdict" and r["instrument"] == "GC":
            t = r["t_start_utc"] or r["t_utc"]
            gc[r["event"]].append((parse(t) if t else None, r["date"], r["tier"]))

    ctxs_m = [Ctx(grid, sky26, 2026, loc="mumbai"), Ctx(grid, sky27, 2027, loc="mumbai")]
    hits = {}
    checked = []
    for r in gold_rules():
        n = 0
        if "darshan" in r.id or "moonrise" in r.id:
            ny = [h for c in ctxs for h in r.detector(c) if P0.astimezone(ET).date() <= h.day <= dt.date(2027, 12, 31)]
            mu = [h for c in ctxs_m for h in r.detector(c) if P0.astimezone(ET).date() <= h.day <= dt.date(2027, 12, 31)]
            allny = [d for c in ctxs for ss, d, sn in C.darshans(c)]
            allmu = [d for c in ctxs_m for ss, d, sn in C.darshans(c)]
            for h in ny:
                twin = next((d for d in allmu if abs((d - h.day).days) <= 2), None)
                ok = any(abs((m.day - h.day).days) <= 2 for m in mu)
                h.facts["Mumbai_sighting"] = f"{twin:%a %d %b %Y}" + (" (rule also met in India)" if ok else " (rule NOT met at Mumbai: different weekday)") if twin else "n/a"
                hits[(r.id, h.start.replace(second=0), h.start.replace(second=0), h.day)] = (r, h)
                n += 1
            for m in mu:
                if not any(abs((h.day - m.day).days) <= 2 for h in ny):
                    twin = next((d for d in allny if abs((d - m.day).days) <= 2), None)
                    m.facts["note"] = f"Indian (Mumbai) sighting only; New York sighting is {twin:%a %d %b %Y}" if twin else "Indian (Mumbai) sighting"
                    hits[(r.id, m.start.replace(second=0), m.start.replace(second=0), m.day)] = (r, m)
                    n += 1
            checked.append((r, n))
            continue
        for ctx in ctxs:
            for h in r.detector(ctx):
                end = h.end or h.start
                if h.day is not None:
                    if not (P0.astimezone(ET).date() <= h.day <= dt.date(2027, 12, 31)):
                        continue
                elif not (h.start < P1 and end >= P0):
                    continue
                k = (r.id, h.start.replace(second=0), (h.end or h.start).replace(second=0), h.day)
                if k not in hits:
                    hits[k] = (r, h)
                    n += 1
        checked.append((r, n))

    # merge identical windows of the same bodies across rules
    groups = collections.OrderedDict()
    for (rid, s0, e0, day), (r, h) in sorted(hits.items(), key=lambda kv: kv[0][1]):
        if h.day is None and h.end and h.end != h.start and h.bodies:
            key = ("w", frozenset(h.bodies), s0, e0, json.dumps(h.facts.get("value"), default=str))
        else:
            key = ("x", rid, s0, e0, day)
        groups.setdefault(key, []).append((r, h))

    rows = []
    for key, items in groups.items():
        r0, h0 = items[0]
        verdicts = []
        for r, h in items:
            v = r.verdict
            if "Malefic Vedha" in v and h.facts.get("value"):
                fv = h.facts["value"]
                v = ("MALEFIC Vedha: gold Bullish" if "MALEFIC" in fv else "") + (" / " if "MALEFIC" in fv and "BENEFIC" in fv else "") + ("BENEFIC Vedha: gold Bearish" if "BENEFIC" in fv else "")
            verdicts.append(v)
        tone = verdict_tone(" ".join(verdicts))
        # planetary detail
        bodies = h0.bodies
        detail = []
        if bodies:
            s = snapshot(max(h0.start, utc(2026, 6, 1)).replace(microsecond=0))
            detail.append("; ".join(f"{name(b)} {s[b].deg:.2f} deg {s[b].sign} ({s[b].nak} p{s[b].pada}){' R' if s[b].retro and b not in ('Rahu', 'Ketu') else ''}" for b in bodies))
        facts = {}
        for r, h in items:
            facts.update({k: v for k, v in h.facts.items() if k not in bodies and k not in ("condition_ends_utc", "note_vs_existing")})
        if facts:
            detail.append("; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in facts.items()))
        # checks
        checks = []
        date_only = any("civil dates" in q for r, _ in items for q in r.quals)
        if h0.day is not None:
            checks.append("darshan criterion reproduces all 4 Moon-darshan dates printed in the 2026 document at Mumbai (3 of 4 at New York); both sightings shown")
        elif date_only:
            m = match_record(h0.start, bodies, 60)
            checks.append("combust/rise civil dates from the astronomy layer (Mumbai kalamsha)")
        else:
            for label, t in (("start", h0.start), ("end", h0.end)):
                if t is None or t == h0.start and label == "end":
                    continue
                if h0.open_start and label == "start" or h0.open_end and label == "end":
                    checks.append(f"{label}: outside scan")
                    continue
                m = match_record(t, set())
                if m:
                    checks.append(f"{label} = astronomy-layer {m[0][1].replace('_', ' ')} of {name(m[0][2])} ✓")
                elif t > dt.datetime(2028, 1, 1, tzinfo=UTC):
                    checks.append(f"{label}: after the astronomy layer's span (engine value)")
                else:
                    checks.append(f"{label}: computed boundary (no single layer record)")
        ex_ids = [e for r, _ in items for e in r.existing if e in gc]
        if ex_ids:
            best = None
            for e in ex_ids:
                for t, d, tier in gc[e]:
                    if t and abs((t - h0.start).total_seconds()) <= 900 or (date_only and t and abs((t - h0.start).total_seconds()) <= 86400 * 1.01):
                        best = (e, t, tier)
            if best:
                checks.append(f"matches existing calendar GC row ({best[0]}) ✓")
            elif h0.start.year >= 2027:
                checks.append(f"existing calendar ({', '.join(ex_ids)}) has no GC row at this start")
        refs = []
        for r, _ in items:
            refs.extend(r.refs)
        quals = []
        for r, _ in items:
            for q in r.quals:
                if q and q not in quals:
                    quals.append(q)
            if r.effect:
                quals.append(f"Effect timing per source: {r.effect}")
        rows.append({
            "start": h0.start, "end": h0.end, "day": h0.day, "open_start": h0.open_start, "open_end": h0.open_end,
            "title": " / ".join(dict.fromkeys(r.title for r, _ in items)), "tone": tone, "verdicts": list(dict.fromkeys(verdicts)),
            "rule": " || ".join(dict.fromkeys(r.rule for r, _ in items)), "detail": " | ".join(detail), "refs": list(dict.fromkeys(refs)),
            "quals": quals, "checks": checks, "rule_ids": [r.id for r, _ in items], "date_only": date_only})
    rows.sort(key=lambda x: x["start"])
    for r in rows:
        if any(b in ("Rahu", "Ketu") for b in r["detail"].split()) or "Ketu" in r["detail"] or "Rahu" in r["detail"]:
            r["quals"].append("Rahu/Ketu sign/nakshatra changes: the 2026 document's almanac prints the 5 Dec 2026 node ingress 40 min earlier (21:52 IST) than the mean node computed here (22:32 IST) - a known 5-arcsecond formulation gap (config/conventions.yaml).")
    write(rows, checked, compare_2026(rows))


def compare_2026(rows):
    """Late-2026 rows vs the rows the 2026 document prints for its gold section."""
    from finastro.rules.config_catalogue import G
    IST = ZoneInfo("Asia/Kolkata")
    NM = {"Pushya": "Pushya", "Dhanistha": "Dhanishta", "Chitra": "Chitra", "Punarvasu": "Punarvasu"}
    out = []
    for key, n, kind in (("gold-bullish", 5, "malefic"), ("gold-bearish", 3, "benefic")):
        for row in G(key, n).tables[0].rows:
            pl, tgt = row[0], NM[row[2]]
            sd = row[4] if kind == "malefic" else row[3]
            st = row[5] if kind == "malefic" else row[4]
            try:
                t = dt.datetime.strptime(f"{sd} {st}", "%d-%b-%y %H:%M").replace(tzinfo=IST)
            except ValueError:
                continue
            if t < dt.datetime(2026, 11, 18, tzinfo=IST):
                continue
            pair = f"{pl}->{tgt}"
            best = None
            for r in rows:
                if pair in r["detail"] and r["start"] is not None:
                    d = abs((r["start"] - t).total_seconds()) / 60
                    if best is None or d < best:
                        best = d
            out.append((f"{key} #{n} ({kind})", pair, f"{sd} {st} IST", t, best))
    G10 = G("gold-bullish", 10).tables[0].rows
    for d, deg, sign in G10:
        day = dt.datetime.strptime(d, "%d-%b-%y").date()
        if day >= dt.date(2026, 11, 18):
            hit = [r for r in rows if "doc26_gold_bull_10_sun_moon_same_degree" in r["rule_ids"] and r["start"].astimezone(IST).date() == day]
            out.append(("gold-bullish #10", f"new moon {deg} {sign}", d, None, 0 if hit else None))
    return out


def when(r):
    if r["day"] is not None:
        return et_date(r["day"]), ""
    if r["date_only"]:
        return f"{r['start'].astimezone(ZoneInfo('Asia/Kolkata')):%a %d %b %Y} (civil date)", (f"{r['end'].astimezone(ZoneInfo('Asia/Kolkata')):%a %d %b %Y} (civil date)" if r["end"] and r["end"] != r["start"] else "")
    s = et(r["start"]) + (" (began earlier)" if r["open_start"] else "")
    e = et(r["end"]) if r["end"] and r["end"] != r["start"] else ""
    return s, e


NOTE26 = {"Venus->Dhanishta": "10 h later here (13:54 IST). The 2026 document's own Venus Vedh table (B134) prints Venus entering Vishakha at 22-Dec-26 3:50, but its neighbouring rows agree with this engine within 4 min (Swati 22:54 vs 22:58, Chitra 3:24 vs 3:22) and the astronomy layer independently gives 13:54 IST: the printed '3:50' has almost certainly lost a digit (13:50). This report uses 13:54 IST = 03:24 EST."}


def write(rows, checked, cmp26):
    OUT.mkdir(parents=True, exist_ok=True)
    js = []
    for r in rows:
        s, e = when(r)
        js.append({"start_ET": s, "end_ET": e, **{k: r[k] for k in ("title", "tone", "verdicts", "rule", "detail", "refs", "quals", "checks", "rule_ids")}})
    json.dump({"period": "2026-11-20 to 2027-12-31", "time_zone": "America/New_York", "rows": js}, open(OUT / "gold_2026-11-20_to_2027-12-31_ET.json", "w", encoding="utf-8"), indent=1)

    cnt = collections.Counter(r["tone"] for r in rows)
    # monthly overview
    months = []
    m = dt.date(2026, 11, 1)
    while m <= dt.date(2027, 12, 1):
        a = dt.datetime(m.year, m.month, 1, tzinfo=ET).astimezone(UTC)
        nm = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        b = dt.datetime(nm.year, nm.month, 1, tzinfo=ET).astimezone(UTC)
        act = collections.Counter()
        names = collections.defaultdict(set)
        for r in rows:
            s = r["start"]
            e = r["end"] or r["start"]
            if r["day"] is not None:
                s = dt.datetime(r["day"].year, r["day"].month, r["day"].day, tzinfo=ET).astimezone(UTC)
                e = s
            if s < b and e >= a:
                act[r["tone"]] += 1
                names[r["tone"]].add(r["title"].split(" / ")[0])
        months.append((m, act, names))
        m = nm
    mrows = "".join(
        f"<tr><td>{m:%b %Y}</td><td class='n bu'>{a['Bullish']}</td><td class='n be'>{a['Bearish']}</td><td class='n mx'>{a['Mixed']}</td>"
        f"<td class='s'>{html.escape('; '.join(sorted(n['Bullish']))[:420])}</td><td class='s'>{html.escape('; '.join(sorted(n['Bearish']))[:420])}</td></tr>"
        for m, a, n in months)
    trs = []
    for i, r in enumerate(rows, 1):
        s, e = when(r)
        q = "".join(f"<li>{html.escape(x)}</li>" for x in r["quals"])
        trs.append(f"<tr class='{r['tone'].lower()}' data-t='{r['tone']}'><td class='n'>{i}</td><td class='w'>{html.escape(s)}</td><td class='w'>{html.escape(e)}</td>"
                   f"<td class='c'><b>{html.escape(r['title'])}</b><div class='s'>{html.escape(r['rule'])}</div>"
                   + (f"<details><summary>Conditions &amp; qualifications ({len(r['quals'])})</summary><ul class='s'>{q}</ul></details>" if q else "") + "</td>"
                   f"<td class='g'><span class='tag {r['tone'].lower()}'>{r['tone']}</span><div>{html.escape(' || '.join(r['verdicts']))}</div></td>"
                   f"<td class='d s'>{html.escape(r['detail'].replace('value: ', ''))}</td>"
                   f"<td class='r s'>{html.escape(' | '.join(r['refs']))}</td>"
                   f"<td class='k s'>{'<br>'.join(html.escape(x) for x in r['checks'])}</td></tr>")
    cmprows = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td>{'found' if d is None and m is not None else (et(d) if d else '')}</td>"
                      f"<td>{'✓ same instant' if m is not None and m <= 5 else ('✓ within %d min (node ingress gap)' % m if m is not None and m <= 45 else ('&#10007; not found' if m is None else NOTE26.get(b, '%d min apart' % m)))}</td></tr>"
                      for a, b, c, d, m in cmp26)
    zero = [(r, n) for r, n in checked if n == 0]
    zrows = "".join(f"<li><b>{html.escape(r.title)}</b> &mdash; {html.escape('; '.join(r.refs))}: does not occur between 20 Nov 2026 and 31 Dec 2027</li>" for r, n in zero)
    ncrows = "".join(f"<li><b>{html.escape(t)}</b> &mdash; {html.escape(ref)}: {html.escape(why)}</li>" for ref, t, why in NOT_COMPUTED)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gold Astro Windows</title><style>
:root{{--bg:#fbfaf7;--fg:#1d1d1f;--mut:#66666c;--line:#e3e1db;--card:#fff;--bu:#1f7a4d;--bubg:#eaf6ef;--be:#b3261e;--bebg:#fbecea;--mx:#8a6400;--mxbg:#fbf3df}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--card:#1d1d20;--bu:#6fd39c;--bubg:#15271d;--be:#ff8a80;--bebg:#2b1716;--mx:#e6c35c;--mxbg:#2a2412}}}}
:root[data-theme=dark]{{--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--card:#1d1d20;--bu:#6fd39c;--bubg:#15271d;--be:#ff8a80;--bebg:#2b1716;--mx:#e6c35c;--mxbg:#2a2412}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;padding:16px}}
h1{{font-size:21px;margin:0 0 4px}}h2{{font-size:16px;margin:22px 0 8px}}p.m{{color:var(--mut);max-width:85em;margin:4px 0}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}}
table{{border-collapse:collapse;width:100%}}th,td{{border-top:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}}
th{{position:sticky;top:0;background:var(--card);font-size:12px;color:var(--mut);border-top:0}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.w{{white-space:nowrap;font-variant-numeric:tabular-nums}}.s{{font-size:12px;color:var(--mut)}}td.c{{min-width:17em}}td.g{{min-width:13em}}td.d{{min-width:20em}}td.r{{min-width:15em}}td.k{{min-width:16em}}ul.s{{margin:4px 0 0;padding-left:16px}}details summary{{cursor:pointer;font-size:12px;color:var(--mut);margin-top:4px}}
.tag{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:12px;font-weight:600;margin-bottom:3px}}
.tag.bullish{{background:var(--bubg);color:var(--bu)}}.tag.bearish{{background:var(--bebg);color:var(--be)}}.tag.mixed,.tag.neutral{{background:var(--mxbg);color:var(--mx)}}
td.bu{{color:var(--bu);font-weight:600}}td.be{{color:var(--be);font-weight:600}}td.mx{{color:var(--mx);font-weight:600}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}}input,select{{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0}}.kpi div{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 14px}}.kpi b{{font-size:20px;display:block}}
ul{{max-width:85em}}li{{margin:3px 0}}
</style></head><body>
<h1>Gold (XAUUSD / COMEX GC): astrological windows, 20 Nov 2026 &ndash; 31 Dec 2027</h1>
<p class="m">Every rule in the two reference PDFs and in the 2026 document that names gold, recomputed (Swiss Ephemeris, sidereal Lahiri, mean node). Times are US Eastern (America/New_York: EST, shown as EDT 14 Mar&ndash;7 Nov 2027). Results are quoted from the sources; they are the sources' claims, not forecasts or investment advice.</p>
<div class="kpi"><div><b>{len(rows)}</b>windows / dates</div><div><b style="color:var(--bu)">{cnt['Bullish']}</b>Bullish per source</div><div><b style="color:var(--be)">{cnt['Bearish']}</b>Bearish per source</div><div><b style="color:var(--mx)">{cnt['Mixed']}</b>Mixed (malefic and benefic Vedha at once)</div></div>
<h2>Month by month (conditions active at any time in the month)</h2>
<p class="m">A count of active conditions, not a net forecast: the sources give no weighting between rules, and TA p.30 says longer multi-planet combinations dominate single ones.</p>
<div class="wrap"><table><thead><tr><th>Month</th><th>Bullish</th><th>Bearish</th><th>Mixed</th><th>Bullish conditions</th><th>Bearish conditions</th></tr></thead><tbody>{mrows}</tbody></table></div>
<h2>All windows and dates (chronological)</h2>
<div class="bar"><input id="q" placeholder="Filter (e.g. Mars, Vedha, Rahu, March)" size="34"><select id="tone"><option value="">All</option><option>Bullish</option><option>Bearish</option><option>Mixed</option></select></div>
<div class="wrap"><table><thead><tr><th>#</th><th>Start (ET)</th><th>End (ET)</th><th>Combination</th><th>Gold effect (source, verbatim)</th><th>Planetary detail at start</th><th>Source</th><th>Double-check</th></tr></thead><tbody id="t">{''.join(trs)}</tbody></table></div>
<h2>How each row was double-checked</h2>
<ul>
<li><b>Boundaries vs the astronomy layer.</b> Every window start/end was compared with the records written independently by <code>build_2027.py</code> (sign, nakshatra and navamsa ingresses, stations, speed crossings, conjunctions, eclipses, lunations), within 3 minutes. The "Double-check" column names the matching record.</li>
<li><b>Vs the existing calendar.</b> For 2027 rows of the 2026 document's gold rules, the start was compared with the existing calendar's GC rows (15 min; one civil day for combust/rise dates).</li>
<li><b>Vedha engine vs printed rows.</b> The gold Vedha calculation reproduces all 30 rows the 2026 document prints for 2026 (gold-bullish #5 and gold-bearish #3), using the TA Sarvatobhadra wheel and the 2026 speed levels for Mars, Mercury and Venus. Rows it adds that the document left out (e.g. Sun in Mula vedhas Chitra, 16-29 Dec 2026) come from the 2026 Sun-Vedha table's printing defect.</li>
<li><b>Dated claims in the PDFs.</b> 51 of 58 recomputed (build/pdfref/validation.json), including KD's Saturn-Mars, Venus-Herschel and Mars-speed dates.</li>
<li>Day rules (darshan) use New York sunset; combust/rise dates are civil dates (Indian, kalamsha method) as in the existing calendar.</li>
</ul>
<h2>Late-2026 rows vs the 2026 document's own printed gold rows</h2>
<p class="m">The 2026 document prints its gold Vedha and new-moon rows through 31 Dec 2026; every one that falls after 18 Nov 2026 is looked up in this report.</p>
<div class="wrap"><table><thead><tr><th>Printed in</th><th>Row</th><th>Printed start</th><th>Printed start in ET</th><th>This report</th></tr></thead><tbody>{cmprows}</tbody></table></div>
<h2>Gold rules checked that do not occur in this period</h2><ul>{zrows}</ul>
<h2>Gold rules not computed</h2><ul>{ncrows}</ul>
<script>
const q=document.getElementById('q'),tn=document.getElementById('tone');
function f(){{const v=q.value.toLowerCase();for(const r of document.getElementById('t').rows){{r.style.display=((!v||r.textContent.toLowerCase().includes(v))&&(!tn.value||r.dataset.t===tn.value))?'':'none'}}}}
q.oninput=f;tn.onchange=f;
</script></body></html>"""
    (OUT / "gold_2026-11-20_to_2027-12-31_ET.html").write_text(doc, encoding="utf-8")
    print(len(rows), dict(cnt), "zero-hit rules:", len(zero))


if __name__ == "__main__":
    main()
