"""Build the New York (EST/EDT) 2027 calendar from the two reference PDFs.

    python tools/build_pdf_calendar.py

Reads build/astronomy_2027.json (sunrises, tithis, combustion, eclipses) and
build/calendar_2027.json (the existing calendar), evaluates every rule in
finastro/pdfref/catalogue.py, and writes build/pdfref/:

  calendar_2027_NY_master.json/.csv/.html/.ics  existing calendar rows (with the
                                                 PDF text attached where a PDF rule
                                                 states the same condition) + the
                                                 new PDF-derived events
  calendar_2027_NY_moon_layer.json/.csv/.ics     Moon-only conditions (the PDFs
                                                 rate them low reliability)
  rules_catalogue.json                           every rule, its refs and counts
  existing_crosscheck.json                       our recomputation vs the existing
                                                 calendar for each mapped rule

No existing file is modified and no existing row is dropped.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import html
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky, parse  # noqa: E402
from finastro.pdfref import catalogue as C  # noqa: E402
from finastro.pdfref.detect import Ctx  # noqa: E402
from finastro.pdfref.engine import Grid, name, snapshot, utc  # noqa: E402

OUT = ROOT / "build" / "pdfref"
NY = ZoneInfo("America/New_York")
IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc
YEAR = 2027
Y0 = dt.datetime(YEAR, 1, 1, tzinfo=NY).astimezone(UTC)
Y1 = dt.datetime(YEAR + 1, 1, 1, tzinfo=NY).astimezone(UTC)
ENGINE = ("Swiss Ephemeris (pyswisseph, sepl/semo 18 files), sidereal Lahiri ayanamsha, mean lunar node, "
          "whole-sign relationships; condition sampled hourly and every boundary bisected to 30 seconds; "
          "times shown in New York local time (EST/EDT by IANA America/New_York) with IST alongside.")
MARKET_LABEL = {"general": "General market (the sources write for Indian indices - NIFTY/Bank Nifty; no instrument named)",
                "gold": "Gold (XAUUSD / COMEX GC)", "silver": "Silver (COMEX SI)", "sugar": "Sugar & jaggery",
                "grains": "Grains", "commodities": "Commodities", "agri": "Agricultural commodities", "USD": "US Dollar / Dollar index"}


def ny(t: dt.datetime) -> str:
    x = t.astimezone(NY)
    return f"{x:%Y-%m-%d %H:%M} {x.tzname()}"


def ist(t: dt.datetime) -> str:
    return f"{t.astimezone(IST):%Y-%m-%d %H:%M} IST"


def describe(bodies, t):
    s = snapshot(t.replace(microsecond=0))
    out = []
    for b in bodies:
        p = s[b]
        sp = f", {abs(p.speed):.3f} deg/day" if b not in ("Rahu", "Ketu") else ""
        out.append(f"{name(b)} {p.deg:05.2f} deg {p.sign} ({p.nak} pada {p.pada}; D9 {p.nav}){' R' if p.retro and b not in ('Rahu', 'Ketu') else ''}{sp}")
    return "; ".join(out)


def fmt_facts(f):
    parts = []
    for k, v in f.items():
        if k in ("condition_ends_utc",):
            v = ny(v)
        if isinstance(v, dt.datetime):
            v = ny(v)
        parts.append(f"{k.replace('_', ' ')}: {v}")
    return "; ".join(parts)


def markets_text(ms):
    out = []
    for m in ms:
        if m.startswith("sector:"):
            out.append("Sector - " + m.split(":", 1)[1])
        else:
            out.append(MARKET_LABEL.get(m, m))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sky = Sky.load()
    ctx = Ctx(Grid(utc(2026, 6, 1), utc(2028, 6, 30)), sky, YEAR)
    cal = json.load(open(ROOT / "build" / "calendar_2027.json", encoding="utf-8"))
    cal_rows = [r for r in cal["rows"] if r["row_kind"] == "verdict" and r["tier"] != "no_rule"]
    cal_ids = {r["event"] for r in cal_rows}

    raw = []          # (rule, hit)
    counts = {}
    for r in C.RULES:
        if r.detector is None:
            counts[r.id] = None
            continue
        hits = r.detector(ctx)
        keep = []
        for h in hits:
            end = h.end or h.start
            if h.day is not None:
                if h.day.year != YEAR:
                    continue
            elif not (h.start < Y1 and end >= Y0):
                continue
            keep.append(h)
        counts[r.id] = len(keep)
        raw.extend((r, h) for h in keep)

    # ---------------- split: existing-mapped vs new; cross-check ----------------
    IN_VENUES, US_VENUES = ("NSE", "MCX", "NSE_FX", "physical_IN"), ("US_cash", "CME_Globex")
    ctx_in = Ctx(ctx.grid, sky, YEAR, loc="mumbai")
    crosscheck, annotations = {}, collections.defaultdict(list)
    new = []

    def rows_of(ids):
        return [x for x in cal_rows if x["event"] in ids]

    def inst(x):
        t = x["t_start_utc"] or x["t_utc"]
        return parse(t) if t else None

    for r in C.RULES:
        mapped = [e for e in r.existing if e in cal_ids]
        hits = [h for rr, h in raw if rr.id == r.id]
        if not mapped:
            new.extend((r, h) for h in hits)
            continue
        ex = rows_of(mapped)
        us_dates = {dt.datetime.strptime(x["date"], "%d-%b-%Y").date() for x in ex if x["venue"] in US_VENUES}
        in_dates = {dt.datetime.strptime(x["date"], "%d-%b-%Y").date() for x in ex if x["venue"] in IN_VENUES}
        ex_inst = sorted({inst(x) for x in ex if inst(x)})
        is_daily = any(h.day for h in hits)
        cc = {"pdf_rule": r.title, "existing": mapped, "method": None}
        if is_daily:
            mum = {h.day for h in r.detector(ctx_in) if h.day and h.day.year == YEAR}
            nyd = {h.day for h in hits}
            cc.update(method="day rule: our Mumbai-sunrise days vs existing Indian-venue days; our New York-sunrise days vs existing US-venue days",
                      mumbai_ours=len(mum), mumbai_existing=len(in_dates), mumbai_common=len(mum & in_dates),
                      mumbai_only_ours=sorted(d.isoformat() for d in mum - in_dates), mumbai_only_existing=sorted(d.isoformat() for d in in_dates - mum),
                      ny_ours=len(nyd), ny_existing=len(us_dates), ny_common=len(nyd & us_dates) if us_dates else None,
                      ny_only_ours=sorted(d.isoformat() for d in nyd - us_dates) if us_dates else "existing rule has no US-venue rows")
            for h in hits:
                if h.day in us_dates or (us_dates and h.day not in us_dates):
                    # The existing calendar already evaluates this rule for US
                    # venues: its rows stand; a different day here is a day-
                    # convention disagreement, reported in the cross-check only.
                    if h.day in us_dates:
                        for e in mapped:
                            annotations[e].append((r, h))
                else:
                    h.facts["note_vs_existing"] = (f"Same condition as existing rule {', '.join(mapped)}, which the existing calendar evaluates at "
                                                   f"{'Mumbai sunrise only' if not us_dates else 'US venues on other days'}; this is the New York-sunrise day.")
                    new.append((r, h))
        else:
            ours = sorted({h.start for h in hits})
            def near(t, pool, tol):
                return any(abs((t - p).total_seconds()) <= tol for p in pool)
            date_only = any("civil dates" in q for q in r.quals)
            tol = 86400 * 1.01 if date_only else 600
            common = [t for t in ours if near(t, ex_inst, tol)]
            cc.update(method="instants: our start instants vs existing rows' start instants (tolerance " + ("1 civil day (date-only)" if date_only else "10 min") + ")",
                      ours=len(ours), existing=len(ex_inst), matched=len(common),
                      only_ours=[t.isoformat() for t in ours if not near(t, ex_inst, tol)][:60],
                      only_existing=[t.isoformat() for t in ex_inst if not near(t, ours, tol)][:60])
            for h in hits:
                if near(h.start, ex_inst, tol):
                    for e in mapped:
                        annotations[e].append((r, h))
                else:
                    h.facts["note_vs_existing"] = f"Condition stated in the PDF differs from / is broader than existing rule {', '.join(mapped)}; this window is not one of its rows."
                    new.append((r, h))
        crosscheck[r.id] = cc

    # ---------------- merge identical windows across rules ----------------
    groups = collections.OrderedDict()
    for r, h in new:
        key = (frozenset(h.bodies) if h.bodies else r.id, h.start.replace(second=0), (h.end or h.start).replace(second=0), h.day,
               json.dumps(h.facts.get("value"), default=str) if not h.bodies else "")
        groups.setdefault(key, []).append((r, h))

    events = []
    for key, items in groups.items():
        r0, h0 = items[0]
        rules = []
        seen = set()
        for r, h in items:
            if r.id not in seen:
                rules.append((r, h))
                seen.add(r.id)
        tier = "major" if any(r.tier == "major" for r, _ in rules) else rules[0][0].tier
        start, end = h0.start, h0.end
        if h0.day is not None:
            when = {"kind": "day", "date_NY": h0.day.isoformat(), "start_NY": ny(start), "start_IST": ist(start)}
        elif end is None or end == start:
            when = {"kind": "instant", "start_NY": ny(start), "start_IST": ist(start), "start_UTC": start.isoformat()}
        else:
            when = {"kind": "window", "start_NY": ny(start), "end_NY": ny(end), "start_IST": ist(start), "end_IST": ist(end),
                    "start_UTC": start.isoformat(), "end_UTC": end.isoformat(),
                    "began_before_scan": h0.open_start, "continues_after_scan": h0.open_end,
                    "duration_days": round((end - start).total_seconds() / 86400, 2)}
        date_only = any("Combust/rise dates are civil dates" in q for r, _ in rules for q in r.quals)
        if date_only:
            when["precision"] = "date_only (combust/rise are civil dates)"
            when["start_NY"] = start.astimezone(IST).date().isoformat() + " (IST civil date)"
            if when.get("end_NY"):
                when["end_NY"] = end.astimezone(IST).date().isoformat() + " (IST civil date)"
        bodies = h0.bodies
        cond = []
        if bodies:
            cond.append(f"At start: {describe(bodies, max(start, utc(2026, 6, 1)))}")
            if end and end != start and when["kind"] == "window":
                cond.append(f"At end: {describe(bodies, end - dt.timedelta(minutes=1))}")
        facts = {}
        for r, h in rules:
            facts.update({k: v for k, v in h.facts.items() if k not in bodies})
        if facts:
            cond.append("Computed: " + fmt_facts(facts))
        verdicts = [f"{r.verdict}" for r, _ in rules]
        mk = sorted({m for r, _ in rules for m in r.markets})
        quals = []
        for r, _ in rules:
            for q in r.quals:
                if q and q not in quals:
                    quals.append(q)
            if r.effect and f"Effect timing per source: {r.effect}" not in quals:
                quals.append(f"Effect timing per source: {r.effect}")
        if "both_direct" in facts:
            quals.append(f"Direct-motion check at mid-window: both direct = {facts['both_direct']}")
        title = " / ".join(dict.fromkeys(r.title for r, _ in rules))
        tone = verdicts[0].split()[0] if verdicts else ""
        ev = {
            "uid": hashlib.sha1(("|".join(r.id for r, _ in rules) + str(start) + str(end)).encode()).hexdigest()[:16],
            "source": "reference_pdfs",
            "tier": tier,
            "event_title": title,
            "date_time": when,
            "planetary_condition": " | ".join(cond),
            "astrological_rule": " || ".join(dict.fromkeys(r.rule for r, _ in rules)),
            "source_interpretation": " || ".join(dict.fromkeys(f"{r.title}: {r.verdict}" for r, _ in rules)),
            "financial_market_significance": "; ".join(dict.fromkeys(
                f"{r.verdict} -> " + ", ".join(markets_text(r.markets)) for r, _ in rules)) +
                " (as the source states it; not a forecast)",
            "conditions_and_qualifications": quals,
            "source_reference": [ref for r, _ in rules for ref in r.refs],
            "calculation_method": " || ".join(dict.fromkeys(r.calc for r, _ in rules)) + " || " + ENGINE,
            "markets": mk,
            "rule_ids": [r.id for r, _ in rules],
            "gold_silver_relevance": ("gold" if "gold" in mk else "") + (" silver" if "silver" in mk else "") or "not stated by source",
        }
        events.append(ev)

    # ---------------- existing calendar rows (deduped) with PDF annotations ----------------
    exist = collections.OrderedDict()
    for x in cal_rows:
        k = (x["event"], x["date_et"], x["t_start_utc"] or x["t_utc"])
        if k not in exist:
            exist[k] = dict(x, instruments=[x["instrument"]])
        else:
            exist[k]["instruments"].append(x["instrument"])
    ex_events = []
    for (eid, d_et, t0), x in exist.items():
        start = parse(x["t_start_utc"]) if x["t_start_utc"] else parse(x["t_utc"]) if x["t_utc"] else None
        end = parse(x["t_end_utc"]) if x["t_end_utc"] else None
        when = {"kind": "window" if end else "instant" if start else "day", "date_ET": d_et or x.get("date"),
                "start_NY": ny(start) if start else (d_et or x.get("date")), "end_NY": ny(end) if end else None,
                "start_IST": ist(start) if start else x.get("date_ist")}
        ann = []
        dd = (dt.datetime.strptime(d_et, "%d-%b-%Y").date() if d_et else
              start.astimezone(NY).date() if start else dt.datetime.strptime(x["date"], "%d-%b-%Y").date())
        for r, h in annotations.get(eid, []):
            hd = h.day or h.start.astimezone(NY).date()
            he = (h.end or h.start).astimezone(NY).date() if not h.day else h.day
            same = hd <= dd <= he
            ann.append({"pdf_rule": r.title, "refs": list(r.refs), "pdf_verdict": r.verdict, "date_match": same,
                        "qualifications": [q for q in r.quals if q]})
        # rule-level annotation even when no hit lands on this date
        rl = {}
        for r in C.RULES:
            if eid in r.existing and r.id not in rl:
                rl[r.id] = {"pdf_rule": r.title, "refs": list(r.refs), "pdf_verdict": r.verdict, "qualifications": [q for q in r.quals if q]}
        ex_events.append({
            "uid": hashlib.sha1((eid + str(d_et) + str(t0) + str(x.get("date"))).encode()).hexdigest()[:16],
            "source": "existing_calendar (2026 document port)",
            "tier": "major",
            "event_title": x["event_section"],
            "date_time": when,
            "planetary_condition": x.get("financial_theme") or "",
            "astrological_rule": x["event_section"],
            "source_interpretation": (x.get("vedic_interpretation") or "(no verdict printed)") +
                (" || PDF: " + " || ".join(f"{a['pdf_rule']}: {a['pdf_verdict']}" for a in rl.values()) if rl else ""),
            "financial_market_significance": f"Instruments in the existing calendar: {', '.join(sorted(set(x['instruments'])))}",
            "conditions_and_qualifications": [f for f in x.get("flags", [])] + [q for a in rl.values() for q in a["qualifications"]],
            "source_reference": [x["event_section"] + " (data/source_2026.html)"] + [ref for a in rl.values() for ref in a["refs"]],
            "calculation_method": "Existing calendar (finastro/rules; see build/RULE_LAYER_STATUS.md). PDF annotation attached by tools/build_pdf_calendar.py.",
            "markets": sorted(set(x["instruments"])),
            "rule_ids": [eid] + list(rl),
            "pdf_annotations_on_this_date": ann,
            "tier_existing": x["tier"], "claim_tag": x.get("claim_tag"),
            "gold_silver_relevance": ", ".join(i for i in sorted(set(x["instruments"])) if i in ("GC", "MCXGOLD", "SI", "MCXSILVER")) or "not in a gold/silver instrument",
        })

    def sort_key(e):
        w = e["date_time"]
        return w.get("start_UTC") or w.get("start_NY") or ""
    major = sorted([e for e in events if e["tier"] in ("major", "yearly")] + ex_events, key=lambda e: (e["date_time"].get("start_NY") or "")[:16])
    moon = sorted([e for e in events if e["tier"] == "moon"], key=lambda e: (e["date_time"].get("start_NY") or "")[:16])

    meta = {"year": YEAR, "time_zone": "America/New_York (EST/EDT); IST alongside", "engine": ENGINE,
            "sources": ["Reference_materials/Tech Astro Analysis pages 1 to 265 all final new printout cq 10 2 2020.pdf (TA)",
                        "Reference_materials/KD Final PPT PDF 2026.pdf (KD)", "build/calendar_2027.json (existing calendar)"],
            "counts": {"pdf_rules": len(C.RULES), "pdf_rules_with_detector": sum(1 for r in C.RULES if r.detector),
                       "pdf_rules_mapped_to_existing": sum(1 for r in C.RULES if any(e in cal_ids for e in r.existing)),
                       "new_events_major_yearly": sum(1 for e in events if e["tier"] in ("major", "yearly")),
                       "new_events_moon_layer": len(moon), "existing_rows_carried": len(ex_events),
                       "existing_rows_with_pdf_text": sum(1 for e in ex_events if " || PDF: " in e["source_interpretation"])},
            "disclaimer": ("Financial astrology is a speculative interpretive framework. Dates are computed; interpretations are the "
                           "sources' own claims, quoted. Nothing here is a forecast or investment advice.")}
    json.dump({"meta": meta, "events": major}, open(OUT / "calendar_2027_NY_master.json", "w", encoding="utf-8"), indent=1, default=str)
    json.dump({"meta": meta, "events": moon}, open(OUT / "calendar_2027_NY_moon_layer.json", "w", encoding="utf-8"), indent=1, default=str)
    json.dump(crosscheck, open(OUT / "existing_crosscheck.json", "w", encoding="utf-8"), indent=1)
    json.dump({"rules": [{"id": r.id, "title": r.title, "refs": r.refs, "verdict": r.verdict, "markets": r.markets, "rule": r.rule,
                          "calc": r.calc, "quals": [q for q in r.quals if q], "tier": r.tier, "existing": r.existing, "effect": r.effect,
                          "hits_2027": counts.get(r.id)} for r in C.RULES],
               "not_computable": C.NOT_COMPUTABLE}, open(OUT / "rules_catalogue.json", "w", encoding="utf-8"), indent=1, default=str)
    write_csv(OUT / "calendar_2027_NY_master.csv", major)
    write_csv(OUT / "calendar_2027_NY_moon_layer.csv", moon)
    write_ics(OUT / "calendar_2027_NY_master.ics", major, "FinAstro 2027 - New York (PDF rules + existing)")
    write_ics(OUT / "calendar_2027_NY_moon_layer.ics", moon, "FinAstro 2027 - Moon layer (low reliability)")
    write_html(OUT / "calendar_2027_NY_master.html", major, meta)
    print(json.dumps(meta["counts"], indent=1))


FIELDS = ("event_title", "date_time", "planetary_condition", "astrological_rule", "source_interpretation",
          "financial_market_significance", "conditions_and_qualifications", "source_reference", "calculation_method")


def write_csv(path, evs):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "tier", "start_NY", "end_NY", "start_IST", "event_title", "planetary_condition", "astrological_rule",
                    "source_interpretation", "financial_market_significance", "conditions_and_qualifications", "source_reference",
                    "calculation_method", "markets", "rule_ids"])
        for e in evs:
            d = e["date_time"]
            w.writerow([e["source"], e["tier"], d.get("start_NY") or d.get("date_NY"), d.get("end_NY") or "", d.get("start_IST") or "",
                        e["event_title"], e["planetary_condition"], e["astrological_rule"], e["source_interpretation"],
                        e["financial_market_significance"], " | ".join(e["conditions_and_qualifications"]),
                        " | ".join(e["source_reference"]), e["calculation_method"], ", ".join(e["markets"]), ", ".join(e["rule_ids"])])


def _ics_text(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line):
    b = line.encode("utf-8")
    out = []
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode("utf-8"))
        b = b" " + b[cut:]
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)


def write_ics(path, evs, calname):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FinAstro2027//pdfref//EN", "CALSCALE:GREGORIAN",
             f"X-WR-CALNAME:{calname}", "X-WR-TIMEZONE:America/New_York"]
    stamp = dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for e in evs:
        d = e["date_time"]
        start = d.get("start_UTC")
        lines += ["BEGIN:VEVENT", f"UID:{e['uid']}@finastro2027", f"DTSTAMP:{stamp}"]
        if d["kind"] == "day" or not start or "date_only" in d.get("precision", ""):
            day = (d.get("date_NY") or d.get("start_NY") or d.get("date_ET") or "")[:10]
            try:
                dd = dt.date.fromisoformat(day)
            except ValueError:
                dd = dt.datetime.strptime(d.get("date_ET") or "01-Jan-2027", "%d-%b-%Y").date()
            lines += [f"DTSTART;VALUE=DATE:{dd:%Y%m%d}", f"DTEND;VALUE=DATE:{dd + dt.timedelta(days=1):%Y%m%d}"]
        else:
            s = dt.datetime.fromisoformat(start).astimezone(UTC)
            lines.append(f"DTSTART:{s:%Y%m%dT%H%M%SZ}")
            if d.get("end_UTC"):
                en = dt.datetime.fromisoformat(d["end_UTC"]).astimezone(UTC)
                lines.append(f"DTEND:{en:%Y%m%dT%H%M%SZ}")
        desc = "\n".join([f"Date/Time (NY): {d.get('start_NY')}" + (f" -> {d.get('end_NY')}" if d.get("end_NY") else ""),
                          f"Planetary condition: {e['planetary_condition']}", f"Astrological rule: {e['astrological_rule']}",
                          f"Source interpretation: {e['source_interpretation']}",
                          f"Financial market significance: {e['financial_market_significance']}",
                          "Conditions & qualifications: " + " | ".join(e["conditions_and_qualifications"]),
                          "Source reference: " + " | ".join(e["source_reference"]), f"Calculation method: {e['calculation_method']}"])
        lines += [_fold("SUMMARY:" + _ics_text(e["event_title"][:240])), _fold("DESCRIPTION:" + _ics_text(desc)),
                  _fold("CATEGORIES:" + _ics_text(",".join(e["markets"][:6]) or "general")), "END:VEVENT"]
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def write_html(path, evs, meta):
    rows = []
    for e in evs:
        d = e["date_time"]
        when = html.escape(str(d.get("start_NY") or d.get("date_NY") or "")) + (("<br>&rarr; " + html.escape(d["end_NY"])) if d.get("end_NY") else "")
        tone = e["source_interpretation"].lower()
        cls = "bull" if "bullish" in tone and "bearish" not in tone else "bear" if "bearish" in tone and "bullish" not in tone else "mix"
        details = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v if isinstance(v, str) else ' | '.join(v))}</dd>"
                          for k, v in (("Planetary condition", e["planetary_condition"]), ("Astrological rule", e["astrological_rule"]),
                                       ("Source interpretation", e["source_interpretation"]),
                                       ("Financial market significance", e["financial_market_significance"]),
                                       ("Conditions & qualifications", e["conditions_and_qualifications"]),
                                       ("Source reference", e["source_reference"]), ("Calculation method", e["calculation_method"])))
        rows.append(f"<tr class='{cls}' data-src='{'pdf' if e['source'] == 'reference_pdfs' else 'existing'}' data-mk='{html.escape(' '.join(e['markets']).lower())}'>"
                    f"<td class='when'>{when}</td><td><details><summary>{html.escape(e['event_title'])}</summary><dl>{details}</dl></details></td>"
                    f"<td>{html.escape(', '.join(e['markets']))}</td><td>{'PDF' if e['source'] == 'reference_pdfs' else 'Existing'}</td></tr>")
    c = meta["counts"]
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinAstro 2027 New York</title>
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1f;--mut:#6b6b70;--line:#e3e1db;--bull:#1f7a4d;--bear:#b3261e;--mix:#7a5b00;--card:#fff}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--bull:#5fc48f;--bear:#ff8a80;--mix:#e0c060;--card:#1d1d20}}}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}} p.m{{color:var(--mut);margin:0 0 12px;max-width:70em}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 12px}} input,select{{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}}
table{{border-collapse:collapse;width:100%;background:var(--card)}} td{{border-top:1px solid var(--line);padding:6px 8px;vertical-align:top}}
td.when{{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--mut);width:13em}}
tr.bull summary{{color:var(--bull)}} tr.bear summary{{color:var(--bear)}} tr.mix summary{{color:var(--mix)}}
summary{{cursor:pointer;font-weight:600}} dl{{margin:6px 0 0}} dt{{font-weight:600;color:var(--mut);margin-top:4px}} dd{{margin:0 0 0 0}}
@media (max-width:700px){{td.when{{width:auto;white-space:normal}} td:nth-child(3),td:nth-child(4){{display:none}}}}
</style></head><body>
<h1>FinAstro 2027 &mdash; New York calendar</h1>
<p class="m">{html.escape(meta['disclaimer'])} Times: {html.escape(meta['time_zone'])}. {c['new_events_major_yearly']} events from the two reference PDFs, {c['existing_rows_carried']} existing calendar rows ({c['existing_rows_with_pdf_text']} carry PDF text). Moon-only conditions ({c['new_events_moon_layer']}) are in the separate Moon-layer files.</p>
<div class="bar"><input id="q" placeholder="Filter text (e.g. Mercury, gold, Bearish)" size="34"><select id="src"><option value="">All sources</option><option value="pdf">PDF rules</option><option value="existing">Existing calendar</option></select><select id="mk"><option value="">All markets</option><option value="gold">Gold</option><option value="silver">Silver</option><option value="sugar">Sugar</option><option value="general">General</option></select></div>
<table><tbody id="t">{''.join(rows)}</tbody></table>
<script>
const q=document.getElementById('q'),s=document.getElementById('src'),m=document.getElementById('mk');
function f(){{const v=q.value.toLowerCase();for(const r of document.getElementById('t').rows){{const ok=(!v||r.textContent.toLowerCase().includes(v))&&(!s.value||r.dataset.src===s.value)&&(!m.value||r.dataset.mk.includes(m.value)||(m.value==='gold'&&/gc|gold/.test(r.dataset.mk))||(m.value==='silver'&&/\\bsi\\b|silver/.test(r.dataset.mk)));r.style.display=ok?'':'none'}}}}
q.oninput=f;s.onchange=f;m.onchange=f;
</script></body></html>"""
    path.write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    main()
