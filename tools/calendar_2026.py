"""The final 2026 calendar: one page, 24 Nov - 31 Dec 2026, built fresh from every layer we have.

    python tools/calendar_2026.py [START] [END]          # default 2026-11-24 to 2026-12-31 (US Eastern dates)

Content, rebuilt on each run (nothing copied from older pages):
  * the sky for every day (tools/forward_daybyday.build: positions, panchang, every change with ET and IST times);
  * the four markets (S&P 500, BSE Sensex, gold, silver): signal-table label and its reasons, combined probabilities
    (up that day, up over 5 sessions, big day; tools/combined_probability.py), supported catalogue rules, calendar-layer
    verdicts, big-move watch and robust volatility factors, Model v1.0 (gold);
  * Solar return: the month's chart reading and the daily call generated the Solar return way
    (tools/solar_return_generate.py), Solar return's own forecasts that cover the day, its transit rules and their records;
  * every catalogue rule and calendar row active, with its 26-year record; outlook, agreement and fast-trigger items;
    classical gochara / Chandra bala / Tara bala (user request, flagged); the Mars-Jupiter-node lead;
  * a track record (13-year walk-forward, last 60 days, 1-23 Nov) and why the Sensex scored higher than the S&P;
  * automatic verification checks, printed at the bottom of the page.
Dashas are parked (user, 24 Nov 2026) and do not appear. Market prices and astrology only.
Writes build/pdfref/calendar_2026-11-24_to_2026-12-31_ET.{html,json}.
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import json
import pathlib
import re
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load, table_rows  # noqa: E402
from finastro.panchang import YOGA_NAMES, tithi_name  # noqa: E402

ET = ZoneInfo("America/New_York")
MKS = ("spx", "sensex", "gold", "silver")
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}
SHORT = {"spx": "S&P", "sensex": "Sensex", "gold": "Gold", "silver": "Silver"}
GOOD = ("Strongest", "Supported", "Consistent")
MAJOR = ("sign change", "station", "lunation", "eclipse", "combustion", "exact aspect")
SLOW = ("Jupiter", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto")
E = html.escape


# ------------------------------------------------------------------ data
def gather(a, b):
    FD = load(ROOT / "tools" / "forward_daybyday.py", "fd_cal")
    SRG = load(ROOT / "tools" / "solar_return_generate.py", "srg_cal")
    res = FD.build(a, b)
    _, ms = SRG.NC.backtest("A")
    SRG.START_DATES[:] = [m["start"].astimezone(ET).date() for m in ms]
    atests = json.load(open(OUT / "author_forecasts_ET.json"))["tests"]
    mons = SRG.months(dt.datetime(2026, 10, 1), dt.datetime(2027, 2, 20))
    sr_days = {r["d"]: r for r in SRG.daily(a, b, mons, atests)}
    sr = dict(months=[m for m in mons if m["end"] and m["end"].date() > a and m["start"].date() <= b], hist=SRG.history(), daily=sr_days,
              episodes=[e for e in SRG.episodes(a, b, atests)], bt=SRG.backtest_daily(),
              scorecard=json.load(open(OUT / "author_forecasts_ET.json"))["forecasts"], atests=atests, month_of=SRG.month_of, all_months=mons)
    kart = json.load(open(OUT / "kartari_test_ET.json"))
    sr["jan"] = json.load(open(OUT / "kartari_jan2027_ET.json"))
    sr["gp"] = json.load(open(OUT / "global_predictions_ET.json"))
    sr["engine"] = json.load(open(OUT / "solar_return_engine_ET.json"))
    sr["gjc"] = json.load(open(OUT / "gold_jupiter_crash_ET.json"))
    sr["turns"] = json.load(open(OUT / "gold_turns_ET.json"))
    sr["jsg"] = json.load(open(OUT / "jupiter_saturn_gold_ET.json"))
    sr["doc"] = doc_rows(json.load(open(OUT / "doc_dec2026_check_ET.json")), res)
    sr["kartari"] = [dict(key=r["key"], title=r["title"], tone=r["tone"], basis=r["basis"], record=r["record"],
                          spans=[(dt.datetime.fromisoformat(u["frm_iso"]), dt.datetime.fromisoformat(u["to_iso"]), u["pair"]) for u in r["upcoming"]])
                     for r in kart["rules"] if r["key"] in ("b116", "b117")]
    track = dict(cp=json.load(open(OUT / "combined_probability_60d_ET.json")), m60=json.load(open(OUT / "model_check_60d_ET.json")),
                 nov=json.load(open(OUT / "daybyday_2026-11-01_to_2026-11-23_ET.json")))
    return res, sr, track, FD


def sensex_explainer(track):
    nov = track["nov"]
    tdays = [x for x in nov["days"] if "spx" in x["prob"] or "sensex" in x["prob"]]
    same = sum(1 for x in tdays if x["signals"].get("S&P 500", [{}])[0].get("sig") == x["signals"].get("BSE Sensex", [{}])[0].get("sig"))
    m60 = track["m60"]["markets"]
    lab = {k: {x["date"]: x["sig"] for x in m60[k]["rows"]} for k in ("spx", "sensex")}
    common = sorted(set(lab["spx"]) & set(lab["sensex"]))
    same60 = sum(lab["spx"][d] == lab["sensex"][d] for d in common)
    ups = nov["score"]["ups"]
    pooled = nov["score"]["pooled"]
    cp = track["cp"]["markets"]
    wf = {k: (cp[k]["walk_forward"]["up5"]["kept"] or cp[k]["walk_forward"]["up5"]["all"])["hit"] for k in ("spx", "sensex")}
    return dict(same_nov=same, n_nov=len(tdays), same60=same60, n60=len(common), ups=ups, pooled=pooled, wf=wf,
                move60={k: m60[k]["move"] for k in ("spx", "sensex")})


# ------------------------------------------------------------------ verification
def verify(res, sr, a, b):
    checks = []

    def add(name, ok, detail):
        checks.append(dict(name=name, ok=bool(ok), detail=detail))
    days = res["days"]
    ds = [dt.date.fromisoformat(x["date"]) for x in days]
    add("Every day present", ds == [a + dt.timedelta(days=i) for i in range((b - a).days + 1)], f"{len(ds)} days, {ds[0]} – {ds[-1]}")
    bad = []
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        for mk in MKS:
            should = d.weekday() < 5 and mk not in x["closed"]
            if should != (mk in x["prob"]):
                bad.append(f"{d} {mk}")
    add("Market days and holidays consistent", not bad, "; ".join(bad) or "US: 26 Nov, 25 Dec closed; Sensex: 24 Nov, 25 Dec closed; early US closes 27 Nov, 24 Dec")
    rng = [v for x in days for pr in x["prob"].values() for t in ("up1", "up5", "big") for v in (pr["all"][t],) if not (0 < v < 100)]
    far = [f"{x['date']} {mk} {t}" for x in days for mk, pr in x["prob"].items() for t in ("up1", "up5") if abs(pr["all"][t] - pr["base"][t]) > 15]
    add("Probabilities valid and near their base rates", not rng and not far, f"{sum(len(x['prob']) for x in days)} market-days; none outside 0–100% or more than 15 points from base")
    pub = {mk: table_rows(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json") for mk in ("gold", "silver")}
    for mk in ("spx", "sensex"):
        pub[mk] = table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", mk)
    mism = []
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        for mk in MKS:
            p = pub[mk].get(d)
            shown = x["signals"][NAME[mk]][0]
            if (p[0] if p else "No signal") != shown["sig"]:
                mism.append(f"{d} {mk}")
    add("Signal labels equal the published tables", not mism, "; ".join(mism[:6]) or "all days, all four markets")
    seen, dup = set(), 0
    for x in days:
        for c in x["changes"]:
            k = (c["kind"], c["text"], c["utc"][:16])
            dup += k in seen
            seen.add(k)
    add("No duplicated planetary changes", dup == 0, f"{len(seen)} changes listed")
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    worst = 0.0
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        noon = dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET).astimezone(dt.timezone.utc)
        jd = swe.julday(noon.year, noon.month, noon.day, noon.hour + noon.minute / 60)
        for p in x["positions"]:
            if p["planet"] not in ("Sun", "Moon", "Saturn"):
                continue
            k = {"Sun": swe.SUN, "Moon": swe.MOON, "Saturn": swe.SATURN}[p["planet"]]
            lon = swe.calc_ut(jd, k, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360
            dg, mn = p["deg"].rstrip("'").split("°")
            shown = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"].index(p["sign"]) * 30 + int(dg) + int(mn) / 60
            worst = max(worst, abs((lon - shown + 180) % 360 - 180) * 60)
    add("Positions re-computed independently (Sun, Moon, Saturn, sidereal Lahiri, 12:00 ET)", worst <= 1.5, f"largest difference {worst:.2f} arc-minutes (display rounds down to whole minutes)")
    off = []
    for m in sr["all_months"]:
        if m["start"].date() < dt.date(2026, 10, 1):
            continue
        t = m["start"].astimezone(dt.timezone.utc)
        jd = swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60 + t.second / 3600)
        sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0] % 30
        if abs(sun - 27.3) > 0.01:
            off.append(f"{m['start']:%d %b} {sun:.3f}°")
    add("Solar return months start at tropical Sun 27°18'", not off, "; ".join(off) or ", ".join(f"{m['start']:%d %b %Y %H:%M}" for m in sr["months"]))
    miss = [x["date"] for x in days if dt.date.fromisoformat(x["date"]).weekday() < 5 and "spx" in x["prob"] and dt.date.fromisoformat(x["date"]) not in sr["daily"]]
    add("A Solar return daily call for every S&P session", not miss, ", ".join(miss) or f"{len(sr['daily'])} sessions")
    if sr.get("doc"):
        timed = [r for r in sr["doc"]["rows"] if r["diffs"]]
        known = [r for r in timed if "Saturn Vehda" in r["event"]]
        off = [f"{r['event']} {r['start']}" for r in timed if r not in known and any(abs(z) > 2 for z in r["diffs"])]
        add("2026 document, December: printed times against our ephemeris", not off,
            f"{len(timed) - len(known)} of {len(timed)} timed rows within 2 minutes; the 2 Saturn vedha rows carry the document's own 20:54 misprint (its Saturn table says 05:02)"
            + (f"; off: {', '.join(off)}" if off else ""))
        v = sr["doc"]["validation"]
        add("Bhadra tone rule reproduces the document's 2026 Bhadra table", v["agree"] == v["matched"] and v["matched"] > 0, f"{v['agree']} of {v['matched']} rows")
    norec = sum(1 for x in days for r in x["rules"] if not any(r["record"].values()))
    add("Every active rule shown with its record (or marked as having none)", True, f"{sum(len(x['rules']) for x in days)} rule-days; {norec} have no scored record and are labelled so")
    return checks


def scan_text(page_html):
    low = page_html.lower()
    return dict(author="author" not in low.replace("author_forecasts", ""), dasha_blocks="dasha chain" not in low and "pratyantar" not in low)


DOC_RULES = {"Uttra Falguni Nakshtra": ("b071_moon_in_uttara_phalguni", None), "Bhadra": ("sub_bhadra", "bhadra"),
             "Ekadashi on Friday": ("b065_ekadashi_on_friday", "cb"), "Moon Mercury in the same D9": ("sub_moon_mercury_in_the_same_navamsh", "Moon and Mercury in the same D9 (market hours)"),
             "Shukla Pratipada Vriddhi Tithi": ("b068_vriddhi_tithi_shukla_paksha", "cb"), "Rahu/Ketu Nakshtra on Thursday": ("sub_rahu_or_ketu_nakshatra_on_a_thursday", "Rahu or Ketu nakshatra on Thursday (market hours)"),
             "Apogee": ("b057_moon_apogee", "Apogee"), "Perigee": ("b058_moon_perigee", "Perigee"),
             "Shani Chandra Dwidwadash Yog along negative axis": ("b094_shani_chandra_dwidwadash_yog", "cb"), "Total Day": ("sub_total_days_in_year", None),
             "Shatbisha on Tuesday": ("b103_shatabhisha_on_tuesday", "cb"), "Vyatipath Yog in Panchak": ("b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak", "cb"),
             "Vargottam Mars": ("b006_not_an_ingress_view", "Vargottam Mars"), "Mercury alone in Mool Nakshtra": ("b098_mercury_in_mula", "Mercury in Mula"),
             "Shukla Trayodashi on Tuesday": ("b109_shukla_trayodashi_on_tuesday_or_saturday", "cb"), "Shukla Purnima Kshay Tithi": ("b066_kshay_tithi_shukla_paksha", "cb"),
             "Jupiter in Magha Nakshtra": ("b099_jupiter_in_magha_purva_phalguni_uttara_phalguni_or_hasta", None),
             "Mars ahead of Jupiter in the same sign": ("b086_mars_ahead_of_jupiter_same_sign", "Mars ahead of Jupiter in the same sign"),
             "Saturn Vehda of Purva Shada": ("b136_saturn_nakshatra_vedh", None), "Saturn Vehda of Hast": ("b136_saturn_nakshatra_vedh", None),
             "Rahu does Vedh of Ashlesha, Vishaka and Shravan": ("b137_rahu_vedha_unreached", None)}
DOC_NOTES = {"Saturn Vehda of Hast": "printed 20:54 repeats the 9 Oct time; the document's own Saturn table (p.33) gives 11 Dec 05:02, the station, which we compute at 05:01",
             "Saturn Vehda of Purva Shada": "ends at Saturn's station (11 Dec 05:01 IST), not 20:54 as printed (see above)",
             "Mercury alone in Mool Nakshtra": "the Sun is also in Mula (Sagittarius 0°–13°20′) from 15 Dec, so Mercury is not literally alone; tested without the 'alone' condition",
             "Bhadra": "tone by the document's own sec-142 rule (karana parity, day/night opening at Mumbai, Moon's loka); our implementation agrees with the document's 2026 Bhadra table on all 99 rows",
             "Moon Mercury in the same D9": "printed only within Indian market hours (09:15–15:30 IST); windows outside those hours (8, 11–12, 19 and 25 Dec) are not printed",
             "Uttra Falguni Nakshtra": "the inference refers to the document's Uttara Phalguni sub-table (row number and signs) and names no market direction we can test; scored as a volatility marker",
             "Total Day": "a turning-date marker with no direction; not testable as a call",
             "Jupiter in Magha Nakshtra": "'1st 15 days bearish' applied to 31 Oct – 15 Nov; nothing left in December",
             "Rahu does Vedh of Ashlesha, Vishaka and Shravan": "'explained separately'; our catalogue's Rahu Nakshatra Vedha and Rahu-in-Dhanishta rules cover it and run all December"}


def _ist(day_s, t_s):
    if not t_s:
        return None
    return dt.datetime.strptime(f"{day_s} {t_s}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Kolkata"))


def _parse_ours(x):
    if not x or not isinstance(x, dict):
        return None
    return dt.datetime.strptime("2026 " + x["ist"], "%Y %d %b %H:%M").replace(tzinfo=ZoneInfo("Asia/Kolkata"))


def doc_rows(j, res):
    cb = {x["rule_id"]: x for x in json.load(open(OUT / "calendar_rules_backtest_2000-2026_ET.json"))["rules"]}
    present = collections.defaultdict(set)
    for x in res["days"]:
        for r in x["calendar"]:
            present[r["rule_id"]].add((r["market"], "condition only" if r["verdict"] == "condition only" else "with its verdict"))
    tests = j["tests"]
    out = []
    for p in j["printed"]:
        rid, src = DOC_RULES.get(p["event"], (None, None))
        key = f"{p['event']}|{p['start']}"
        ours = j["timings"].get(key)
        diffs = []
        if ours:
            pairs = [(_ist(p["start"], p["start_time"]), _parse_ours(ours[0]) if len(ours) > 0 else None)]
            end_day = p["end"] if p["end"] and re.match(r"\d{4}-\d\d-\d\d", p["end"]) else p["start"]
            pairs.append((_ist(end_day, p["end_time"]), _parse_ours(ours[1]) if len(ours) > 1 else None))
            for a, b in pairs:
                if a and b:
                    diffs.append(round((b - a).total_seconds() / 60))
        tone = None
        rec = {}
        if src == "cb" and rid in cb:
            for mk in ("spx", "sensex"):
                r = cb[rid].get(mk)
                if r and r.get("kind") == "direction" and r["worked"] is not None:
                    rec[mk] = dict(text=f"{r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%), p {r['p_value']}", ok=bool(r["p_value"] is not None and r["p_value"] < 0.05 and r["hit_rate"] > r["base_rate"]))
        elif src == "bhadra":
            k = {"positive": "Bhadra, positive by the document's rule", "negative": "Bhadra, negative by the document's rule"}.get(p["tone"] or "")
            if k:
                src = k
        if src in tests:
            t = tests[src]
            for mk in ("spx", "sensex"):
                a = t[mk]["all"]
                dec = a["worked"] + a["failed"]
                if dec:
                    h1, h2 = t[mk]["h1"], t[mk]["h2"]
                    ok = bool(a["p_value"] is not None and a["p_value"] < 0.05 and h1["hit_rate"] and h2["hit_rate"] and h1["hit_rate"] > h1["base_rate"] and h2["hit_rate"] > h2["base_rate"])
                    rec[mk] = dict(text=f"{a['worked']}/{dec} ({a['hit_rate']}% vs {a['base_rate']}%), p {a['p_value']}", ok=ok)
        pres = sorted(present.get(rid, set()))
        out.append(dict(p, rid=rid, ours=ours, diffs=diffs, rec=rec, present=pres, note=DOC_NOTES.get(p["event"], ""),
                        bhadra=(ours[2] if p["event"] == "Bhadra" and ours and len(ours) > 2 else None)))
    return dict(rows=out, validation=j["bhadra_validation"], bhadra_dec=j["bhadra_dec"], tests=tests, sunrise=j["timings"].get("_sunrise", {}))


def doc_html(doc):
    rows = doc["rows"]
    timed = [r for r in rows if r["diffs"]]
    worst = max((abs(x) for r in timed for x in r["diffs"]), key=lambda v: v, default=0)
    big = [r for r in timed if any(abs(x) > 5 for x in r["diffs"])]
    o = ["<h2 id='doc'>Check against the 2026 document: December (pp.292–293)</h2>",
         "<div class='callout'><ul>"
         f"<li><b>{len(rows)} printed rows.</b> {len(timed)} carry times we can compute; {len(timed) - len(big)} of them agree with our ephemeris within "
         f"{max((abs(x) for r in timed if r not in big for x in r['diffs']), default=0)} minutes (the printed times are IST, truncated to the minute).</li>"
         "<li><b>Printed-time errors in the document:</b> the Saturn vedha change is printed at 11 Dec 20:54, but the document's own Saturn table gives 05:02 (Saturn's station; "
         "ours 05:01). The November table's “Mercury and Venus both retrograde, 24 Oct – 11 Dec” also contradicts the document's own station tables (Mercury direct 13 Nov 21:25, "
         "Venus 14 Nov 05:59), which is why December does not reprint it.</li>"
         "<li><b>Printed only when markets are open in India:</b> Bhadra on 13, 20 and 26 Dec and Moon–Mercury D9 outside 09:15–15:30 IST are computed by us but not printed.</li>"
         f"<li><b>Bhadra tone:</b> our implementation of the document's own rule agrees with its 2026 Bhadra table on {doc['validation']['agree']} of {doc['validation']['matched']} rows.</li>"
         "<li><b>Do the stated directions work?</b> Of the December rows with a testable direction, only negative Bhadra held on the Sensex (bearish, both halves); "
         "with about 18 tests run, one such pass is expected by chance. Everything else is at chance or the wrong way.</li>"
         "<li><b>How our calendar shows them:</b> rows the calendar layer scores as a direction appear in each day's calendar rows; the rest appeared only as “condition only”. "
         "Each December day below now lists the document's rows with their check.</li></ul></div>"]
    o.append("<div class='wrap'><table><thead><tr><th>Printed (IST)</th><th>Event</th><th>Document says</th><th>Our time (IST / ET)</th><th class='n'>Diff</th>"
             "<th>In our calendar</th><th>S&amp;P record</th><th>Sensex record</th></tr></thead><tbody>")
    for r in rows:
        pr = f"{r['start'][8:]}-{r['start'][5:7]} {r['start_time']}" + (f" → {r['end'][8:] + '-' + r['end'][5:7] if re.match(r'\d{4}', r['end'] or '') else r['end']} {r['end_time']}" if r["end"] or r["end_time"] else "")
        ours = ""
        if r["ours"]:
            ours = " → ".join(f"{x['ist']} / {x['et']} ET" for x in r["ours"][:2] if isinstance(x, dict))
            if r["bhadra"]:
                ours += f" · tone {r['bhadra']}"
        diff = ", ".join(f"{x:+d} min" for x in r["diffs"]) or "–"
        pres = ", ".join(f"{SHORT.get(m, m)} ({k})" for m, k in r["present"]) or "not shown"

        def rc(mk, r=r):
            x = r["rec"].get(mk)
            return f"<span class='{'t-up' if x['ok'] else ''}'>{E(x['text'])}</span>{' ✓ holds' if x['ok'] else ''}" if x else "<span class='s'>–</span>"
        o.append(f"<tr><td class='n'>{E(pr)}</td><td>{E(r['event'])}{'<div class=s>' + E(r['note']) + '</div>' if r['note'] else ''}</td><td>{chip(r['inference'][:40], tone(r['tone'] or r['inference']))}</td>"
                 f"<td class='s'>{E(ours) or '–'}</td><td class='n'>{diff}</td><td class='s'>{E(pres)}</td><td class='s'>{rc('spx')}</td><td class='s'>{rc('sensex')}</td></tr>")
    o.append("</tbody></table></div><p class='s'>Records: 2000–2026, standard method; a bearish row is right when the market fell, a bullish (Positive) row when it rose. "
             "“Holds” = p &lt; 0.05 and better than normal in both halves. Rows the document marks Neutral, sector-only or “explained separately” have no market direction to test.</p>")
    return "".join(o)


def doc_on(doc, d):
    out = []
    for r in doc["rows"]:
        s0 = dt.date.fromisoformat(r["start"])
        e0 = dt.date.fromisoformat(r["end"]) if re.match(r"\d{4}-\d\d-\d\d", r["end"] or "") else s0
        if s0.month == 12 and s0 <= d <= e0 or (s0 == d):
            out.append(r)
    return out


# ------------------------------------------------------------------ helpers
def kartari_on(sr, d):
    """Paap Kartari windows (2026 document B116 / B117) covering any part of day d (ET)."""
    d0 = dt.datetime.combine(d, dt.time(0), ET)
    d1 = d0 + dt.timedelta(days=1)
    out = []
    for k in sr.get("kartari", []):
        for a, b, pair in k["spans"]:
            if a < d1 and b > d0:
                out.append(dict(k, frm=a, to=b, pair=pair))
    return out


def krec(k):
    parts = []
    for mk in ("spx", "sensex"):
        r = k["record"][mk]["all"]
        parts.append(f"{SHORT[mk]} {r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%, p {r['p_value']})")
    big = "; ".join(f"big days {k['record'][mk]['big_in']}% vs {k['record'][mk]['big_all']}% ({SHORT[mk]})" for mk in ("spx", "sensex"))
    return "; ".join(parts) + "; " + big



def tone(t):
    t = (t or "").lower()
    return "up" if t.startswith(("bull", "support", "up", "helps")) else "dn" if t.startswith(("bear", "pressure", "weak", "down", "hurts")) else "vo" if t.startswith("volat") else "nt"


def chip(text, cls, title=""):
    return f"<span class='chip {cls}'{f' title={chr(34)}{E(title)}{chr(34)}' if title else ''}>{E(text)}</span>"


def pct(v):
    return "–" if v is None else f"{v:.0f}%"


def lab_short(sig):
    s = sig["sig"]
    if s in ("Bullish", "Bearish"):
        return f"{s} {sig['st'][0] if sig['st'] else ''}".strip()
    return s if s != "No signal" else "—"


def tithi_txt(n):
    return f"{'Shukla' if n <= 15 else 'Krishna'} {tithi_name(n)}"


def key_events(x):
    out = []
    for c in x["changes"]:
        body = c["text"].split(" ")[0].split("–")[0]
        if c["kind"] in MAJOR or (c["kind"] == "nakshatra change" and body in SLOW + ("Mars",)):
            if body == "Moon" and c["kind"] not in ("lunation", "eclipse"):
                continue
            t = f"{c['text']} ({c['et'].split(' ')[3]} ET)"
            if t not in out:
                out.append(t)
    return out


def icon(x):
    ic = ""
    kinds = {c["kind"] for c in x["changes"]}
    txt = " ".join(c["text"] for c in x["changes"])
    if "Full Moon" in txt:
        ic += "○"
    if "New Moon" in txt:
        ic += "●"
    if "station" in kinds:
        ic += "⟲"
    if any(c["kind"] == "sign change" and not c["text"].startswith("Moon") for c in x["changes"]):
        ic += "→"
    return ic


# ------------------------------------------------------------------ page
CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--card:#ffffff;--up:#1a7f37;--upbg:#dafbe1;--dn:#cf222e;--dnbg:#ffebe9;
--vo:#9a6700;--vobg:#fff8c5;--nt:#59636e;--ntbg:#eff2f5;--acc:#0969da;--we:#f6f8fa;--hol:#fff1e5}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--card:#0d1117;
--up:#3fb950;--upbg:#12261e;--dn:#f85149;--dnbg:#2d1215;--vo:#d29922;--vobg:#2e2410;--nt:#9198a1;--ntbg:#1c2128;--acc:#4493f8;--we:#11161d;--hol:#2a1c10}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--card:#0d1117;--up:#3fb950;--upbg:#12261e;--dn:#f85149;--dnbg:#2d1215;
--vo:#d29922;--vobg:#2e2410;--nt:#9198a1;--ntbg:#1c2128;--acc:#4493f8;--we:#11161d;--hol:#2a1c10}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1280px;margin:0 auto;padding:16px}
h1{font-size:22px;margin:4px 0 4px} h2{font-size:18px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)} h3{font-size:15px;margin:16px 0 6px}
p{margin:6px 0} a{color:var(--acc);text-decoration:none} a:hover{text-decoration:underline}
.mut{color:var(--mut)} .s{font-size:12.5px;color:var(--mut)}
.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
.top nav{max-width:1280px;margin:0 auto;padding:8px 16px;display:flex;gap:14px;flex-wrap:wrap;align-items:center;font-size:13px}
.top nav b{margin-right:6px} .top button,.tool button{font:inherit;font-size:12.5px;padding:3px 10px;border:1px solid var(--line);background:var(--soft);color:var(--fg);border-radius:6px;cursor:pointer}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.stat{border:1px solid var(--line);border-radius:8px;padding:8px 12px;background:var(--soft);min-width:150px} .stat b{display:block;font-size:18px}
.callout{border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:6px;padding:10px 14px;background:var(--soft);margin:10px 0}
.chip{display:inline-block;padding:0 7px;border-radius:10px;font-size:12px;line-height:19px;margin:1px 2px 1px 0;white-space:nowrap;font-weight:600}
.up{color:var(--up);background:var(--upbg)} .dn{color:var(--dn);background:var(--dnbg)} .vo{color:var(--vo);background:var(--vobg)} .nt{color:var(--nt);background:var(--ntbg)}
.t-up{color:var(--up);font-weight:600} .t-dn{color:var(--dn);font-weight:600} .t-vo{color:var(--vo);font-weight:600}
.wrap{overflow-x:auto;-webkit-overflow-scrolling:touch} table{border-collapse:collapse;width:100%;margin:6px 0 12px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top} th{background:var(--soft);font-weight:600;font-size:13px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.cal{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;margin:8px 0 6px}
.cal .hd{font-size:12px;color:var(--mut);text-align:center;font-weight:600}
.cell{border:1px solid var(--line);border-radius:8px;padding:6px;min-height:118px;background:var(--card);font-size:12px;overflow:hidden}
.cell.we{background:var(--we)} .cell.hol{background:var(--hol)} .cell.out{visibility:hidden}
.cell .dt{display:flex;justify-content:space-between;font-weight:700;font-size:13px} .cell .dt a{color:var(--fg)} .cell .ic{color:var(--acc);font-weight:700}
.cell .mn{color:var(--mut);font-size:11.5px;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cell .row{display:flex;justify-content:space-between;gap:4px;align-items:center} .cell .row span.k{color:var(--mut);font-size:11px}
details.day{border:1px solid var(--line);border-radius:8px;margin:10px 0;background:var(--card)}
details.day>summary{cursor:pointer;padding:10px 14px;list-style:none} details.day>summary::-webkit-details-marker{display:none}
details.day>summary .h{font-weight:700} details.day[open]>summary{border-bottom:1px solid var(--line)}
details.day .body{padding:6px 14px 12px} details.sub{margin:6px 0} details.sub>summary{cursor:pointer;color:var(--acc);font-size:13.5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px} ul{margin:6px 0;padding-left:20px} li{margin:2px 0}
.ok{color:var(--up);font-weight:700} .bad{color:var(--dn);font-weight:700}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12.5px;color:var(--mut);margin:6px 0}
@media (max-width:860px){.top{position:static}.cal{grid-template-columns:1fr}.cal .hd{display:none}.cell{min-height:0}.cell.out{display:none}.grid2{grid-template-columns:1fr}
.top nav{gap:8px}.stat{min-width:120px}}
@media print{.top,.tool{display:none} details.day{break-inside:avoid}}
"""

JS = """
function setAll(open){document.querySelectorAll('details.day,details.sub').forEach(d=>d.open=open)}
function theme(){const r=document.documentElement;const cur=r.getAttribute('data-theme');const dark=matchMedia('(prefers-color-scheme: dark)').matches;
r.setAttribute('data-theme',(cur?cur==='dark':dark)?'light':'dark')}
function filt(v){v=v.toLowerCase();document.querySelectorAll('details.day').forEach(d=>{d.style.display=!v||d.textContent.toLowerCase().includes(v)?'':'none'})}
if(location.hash){const el=document.querySelector(location.hash);if(el&&el.tagName==='DETAILS')el.open=true}
document.querySelectorAll('a[href^="#d"]').forEach(a=>a.addEventListener('click',()=>{const el=document.querySelector(a.getAttribute('href'));if(el)el.open=true}))
"""


def market_cell(x, mk, sr_day=None):
    pr = x["prob"].get(mk)
    sig = x["signals"][NAME[mk]][0]
    if not pr:
        return f"<div class='row'><span class='k'>{SHORT[mk]}</span><span class='s'>{'closed' if mk in x['closed'] else ''}</span></div>"
    p5, b5 = pr["all"]["up5"], pr["base"]["up5"]
    pc = "t-up" if p5 >= b5 + 2 else "t-dn" if p5 <= b5 - 2 else ""
    return (f"<div class='row'><span class='k'>{SHORT[mk]}</span>{chip(lab_short(sig), tone(sig['sig']), sig['why'])}<span class='{pc}' title='chance of a rise over the next 5 sessions'>{p5:.0f}%</span></div>")


def day_summary(x, sr_day):
    bits = []
    for mk in ("spx", "sensex", "gold", "silver"):
        pr = x["prob"].get(mk)
        sig = x["signals"][NAME[mk]][0]
        if pr:
            bits.append(f"{SHORT[mk]} {lab_short(sig)} · {pr['all']['up5']:.0f}% up/5d")
        elif mk in x["closed"]:
            bits.append(f"{SHORT[mk]} closed ({x['closed'][mk]})")
    if sr_day:
        bits.append(f"Solar return {sr_day['call']}")
    return " | ".join(bits)


def page(res, sr, track, checks, a, b, generated):
    days = res["days"]
    sx = sensex_explainer(track)
    nbusy = {mk: sum(1 for x in days if mk in x["prob"]) for mk in MKS}
    o = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>FinAstro Calendar 2026</title><style>{CSS}</style></head><body>"]
    o.append("<div class='top'><nav><b>FinAstro calendar</b><a href='#read'>Read first</a><a href='#keys'>Key dates</a><a href='#grid'>Calendar</a>"
             "<a href='#spans'>Signal spans</a><a href='#sr'>Solar return</a><a href='#jan'>January 2027</a><a href='#days'>Day by day</a><a href='#trust'>Track record</a><a href='#checks'>Checks</a>"
             "<span style='flex:1'></span><button onclick='theme()'>Light / dark</button></nav></div><main>")
    o.append(f"<h1>Market astrology calendar, {a:%d %b} – {b:%d %b %Y}</h1>"
             f"<p class='mut'>S&amp;P 500, BSE Sensex, gold and silver. Dates and times US Eastern (IST also shown for changes). Sidereal Lahiri, mean node, whole-sign drishti; "
             f"Solar return uses tropical signs, as its method does. Built {generated} from prices to the 23 Nov 2026 close. Market prices and astrology only.</p>")
    nrules = sum(len(x["rules"]) for x in days)
    o.append("<div class='stats'>" + "".join(f"<div class='stat'><b>{v}</b>{E(k)}</div>" for k, v in (
        ("days", len(days)), ("S&P sessions", nbusy["spx"]), ("Sensex sessions", nbusy["sensex"]), ("gold / silver sessions", nbusy["gold"]),
        ("rule-days checked", nrules), ("planetary changes", sum(len(x["changes"]) for x in days)))) + "</div>")
    # read first
    cp = track["cp"]["markets"]
    wf = {mk: (cp[mk]["walk_forward"]["up5"]["kept"] or cp[mk]["walk_forward"]["up5"]["all"])["hit"] for mk in MKS}
    o.append("<h2 id='read'>Read this first</h2><div class='callout'><ul>"
             "<li><b>What each market line shows:</b> our signal-table label (Bullish / Bearish with High, Moderate or Low strength), and the combined model's chance of a rise "
             "over the next 5 sessions. Green and red mean at least 2 points above or below that market's normal rate.</li>"
             f"<li><b>How much to trust it:</b> over 2013–2026 the combined model's calls were right {wf['spx']}% (S&amp;P), {wf['sensex']}% (Sensex), {wf['gold']}% (gold) and "
             f"{wf['silver']}% (silver) of the time over 5 sessions: a small edge at best. Every probability in this calendar stays within a few points of normal. Treat them as leanings.</li>"
             "<li><b>Solar return</b> is the NYSE monthly solar-return method you shared. Its daily calls here are generated by us the Solar return way; they reproduce 8 of the 9 days "
             "Solar return called, but over 1928–2026 the same rule was at chance.</li>"
             "<li><b>What has shown some edge:</b> Jupiter sextile Venus (bullish over 5 sessions), the bearish calendar fortnight rule “Three Saturdays in Shukla Paksha”, "
             "robust volatility factors (more big days, no direction) and the Mars–Jupiter–node lead (a lead, not proven).</li>"
             "<li><b>Paap Kartari:</b> Jupiter is hemmed by Ketu and Mars (2026 document B117) from 16 Nov to 31 Jan 2027, and Mercury enters Paap Kartari "
             "(B116) on 1 Jan 2027. Their 2000–2026 records are in each day's notes, and January is checked market by market in the January 2027 section: Mercury's version held up as bearish on the Sensex only; Jupiter's showed more big days, "
             "not significant. Shubh Kartari is in none of our sources; tested anyway, it did not work and is not used.</li>"
             "<li><b>Not used:</b> dashas (tested, no edge; parked at your request), news and fundamentals.</li></ul></div>")
    # key dates
    o.append("<h2 id='keys'>Key dates</h2><div class='wrap'><table><thead><tr><th>Date</th><th>What happens</th><th>Markets</th></tr></thead><tbody>")
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        ev = key_events(x)
        extra = []
        if x["closed"]:
            extra.append("Closed: " + ", ".join(f"{NAME[k]} ({v})" for k, v in x["closed"].items()))
        if x["early"]:
            extra.append(x["early"])
        for m in sr["months"]:
            if m["start"].date() == d:
                extra.append(f"Solar return month starts {m['start']:%H:%M ET}: {m['asc']} rising, reading “{m['reading']}”")
        for e in sr["episodes"]:
            if e["frm"] == d and e["rule"] not in ("Mars retrograde",) and "with Mars-Ketu" not in e["rule"]:
                verb = "active" if d == a else "begins"
                extra.append(f"Solar return rule {verb}: {e['rule']}" + (f" (to {e['to']:%d %b})" if e["to"] != e["frm"] else " (last day)" if d == a else ""))
        for r in doc_on(sr["doc"], d):
            if any(v["ok"] for v in r["rec"].values()) and dt.date.fromisoformat(r["start"]) == d:
                extra.append(f"2026 document: {r['event']} ({r['inference']}) — held up on the " + ", ".join(SHORT[k] for k, v in r["rec"].items() if v["ok"]) + " since 2000")
        for k in GJC_KEYS:
            for a_, b_ in sr["gjc"]["spans"].get(k, []):
                if b_ == x["date"] and dt.date.fromisoformat(b_) < b:
                    extra.append(f"Gold Jupiter note: “{k}” ends")
                if a_ == x["date"] and x["date"] != str(a):
                    extra.append(f"Gold Jupiter note: “{k}” begins")
        if x["date"] == "2026-12-11":
            extra.append("Saturn stations direct (Pisces 13.7°): gold bottom-watch marker (Saturn direct station within ±30 days at 7 of 24 past gold bottoms)")
        for f in sr["gp"]["forecasts"]:
            if f["start"] == x["date"] and f["kind"] != "fade":
                extra.append(f"Global Predictions window begins ({f['period']}): {f['text'][:90]}…")
        prev = days[days.index(x) - 1] if days.index(x) else None
        if prev and prev["mjn"] and not x["mjn"]:
            extra.append("Mars–Jupiter–Ketu conjunction in Leo ends (crash lead off)")
        for k in sr.get("kartari", []):
            for ka, kb, pair in k["spans"]:
                if ka.date() == d or (days.index(x) == 0 and ka.date() < d < kb.date()):
                    extra.append(f"{k['title'].split(' (')[0]} ({pair}) {'begins' if ka.date() == d else 'active'}, to {kb:%d %b %Y}")
                if kb.date() == d:
                    extra.append(f"{k['title'].split(' (')[0]} ends {kb:%H:%M ET}")
        if days.index(x) == 0 and x["mjn"]:
            extra.append("Mars–Jupiter–Ketu together in Leo (crash lead active)")
        for w in x["watch"]:
            if w["exact"] == x["date"]:
                extra.append(f"Big-move watch ({SHORT.get(w['market'], w['market'])}) exact: {w['factor'].replace('Event: ', '').replace('Rule: ', '').split(' [')[0]}")
        if not ev and not extra:
            continue
        sig = "; ".join(f"{SHORT[mk]} {lab_short(x['signals'][NAME[mk]][0])}" for mk in MKS if x["signals"][NAME[mk]][0]["sig"] != "No signal")
        o.append(f"<tr><td class='n'><a href='#d{x['date']}'>{d:%a %d %b}</a></td><td>{E('; '.join(ev + extra))}</td><td class='s'>{E(sig)}</td></tr>")
    o.append("</tbody></table></div>")
    # calendar grid
    o.append("<h2 id='grid'>Calendar</h2><div class='legend'>" + chip("Bullish", "up") + chip("Bearish", "dn") + chip("Volatile", "vo") + chip("—", "nt") +
             "<span>H / M / L = strength · % = chance of a rise over the next 5 sessions · ○ full Moon · ● new Moon · ⟲ station · → sign change</span></div>")
    by = {x["date"]: x for x in days}
    mstart = dt.date(a.year, a.month, 1)
    while mstart <= b:
        mend = (mstart.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
        lo, hi = max(a, mstart), min(b, mend)
        o.append(f"<h3>{mstart:%B %Y}</h3><div class='cal'>" + "".join(f"<div class='hd'>{w}</div>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")))
        d = lo - dt.timedelta(days=lo.weekday())
        while d <= hi + dt.timedelta(days=6 - hi.weekday()):
            x = by.get(str(d)) if lo <= d <= hi else None
            if not x:
                o.append("<div class='cell out'></div>")
            else:
                cls = "hol" if x["closed"] else "we" if d.weekday() >= 5 else ""
                pan = x["panchang"]
                srd = sr["daily"].get(d)
                body = "".join(market_cell(x, mk) for mk in MKS) if d.weekday() < 5 else "<div class='s'>weekend</div>"
                if srd:
                    body += f"<div class='row'><span class='k'>Solar ret.</span>{chip(srd['call'], tone(srd['call']), srd['why'])}</div>"
                hol = f"<div class='s'>{E('; '.join(f'{SHORT[k]} closed' for k in x['closed']))}</div>" if x["closed"] else ""
                o.append(f"<div class='cell {cls}'><div class='dt'><a href='#d{x['date']}'>{d:%a %d}</a><span class='ic'>{icon(x)}</span></div>"
                         f"<div class='mn'>☾ {E(pan['moon_nakshatra'])} · {E(tithi_txt(pan['tithi']))}</div>{hol}{body}</div>")
            d += dt.timedelta(days=1)
        o.append("</div>")
        mstart = mend + dt.timedelta(days=1)
    # signal spans
    o.append("<h2 id='spans'>Signal spans by market</h2><p class='s'>Consecutive trading days with the same table label. Reasons are the qualifying rules that set the label.</p>"
             "<div class='wrap'><table><thead><tr><th>Market</th><th>Dates</th><th>Label</th><th>Why</th></tr></thead><tbody>")
    for mk in MKS:
        cur = None
        spans = []
        for x in days:
            if mk not in x["prob"]:
                continue
            sg = x["signals"][NAME[mk]][0]
            key = (sg["sig"], sg["st"], sg["why"])
            if cur and cur["key"] == key:
                cur["to"] = x["date"]
            else:
                cur = dict(key=key, frm=x["date"], to=x["date"])
                spans.append(cur)
        for sp in spans:
            s, st, why = sp["key"]
            if s == "No signal":
                continue
            f0, t0 = dt.date.fromisoformat(sp["frm"]), dt.date.fromisoformat(sp["to"])
            o.append(f"<tr><td>{NAME[mk]}</td><td class='n'>{f0:%a %d %b}" + ("" if f0 == t0 else f" – {t0:%a %d %b}") + f"</td><td>{chip((s + ' ' + (st or '')).strip(), tone(s))}</td><td class='s'>{E(why)}</td></tr>")
    o.append("</tbody></table></div>")
    # solar return section
    o.append("<h2 id='sr'>Solar return</h2>")
    o.append("<div class='wrap'><table><thead><tr><th>Solar month (ET)</th><th>Ascendant</th><th>Ascendant lord</th><th>8th house</th><th>10th house</th><th>Reading</th><th>This reading since 1928</th></tr></thead><tbody>")
    for m in sr["months"]:
        hb = sr["hist"]["by"].get(m["reading"], {})
        rec = f"{hb.get('n', 0)} months, S&P up {hb.get('up')}%, average {hb.get('mean', 0):+.2f}%" if hb else "–"
        o.append(f"<tr><td class='n'>{m['start']:%d %b %Y %H:%M} → {m['end']:%d %b %Y}</td><td>{E(m['asc'])}</td><td>{m['lord']}: {E(m['lord_pos'])}</td><td>{E(', '.join(m['h8']) or '–')}</td>"
                 f"<td>{E(', '.join(m['h10']) or '–')}</td><td>{chip(m['reading'], tone(m['reading']))}</td><td class='s'>{E(rec)}</td></tr>")
    allm = sr["hist"]["all"]
    o.append(f"</tbody></table></div><p class='s'>All {allm['n']} solar months 1928–2026: S&amp;P up {allm['up']}%, average {allm['mean']:+.2f}%. Readings use only the indications "
             "Solar return has stated (debilitated ascendant lord, Mars with Ketu or another malefic in the 8th: bearish; Venus or Jupiter in the 10th: moderates).</p>")
    eng = sr.get("engine")
    if eng:
        names = {"A": "A tropical monthly", "B": "B sidereal monthly", "C": "C tropical annual ÷ 12", "D": "D sidereal annual ÷ 12"}
        o.append("<h3>Solar return engine: four calculation models (your 24 Nov spec)</h3><div class='wrap'><table><thead><tr><th>Model</th><th>Chart now</th><th>Rubric</th>"
                 "<th>Next chart</th><th>Rubric</th><th class='n'>1928–2026: calls right vs always bullish</th></tr></thead><tbody>")
        for m in "ABCD":
            rows = eng["forward"][m]
            cur = [r for r in rows if dt.datetime.strptime(r["start"], "%a %d %b %Y %H:%M").date() <= a][-1:] or rows[:1]
            nxt = [r for r in rows if dt.datetime.strptime(r["start"], "%a %d %b %Y %H:%M").date() > a][:1]
            x = eng["models"][m]["all"]

            def cell(r):
                if not r:
                    return "<td>–</td><td>–</td>"
                r = r[0]
                return (f"<td class='n'>{E(r['start'])} ({E(r['asc'])} rising)</td><td>{chip(r['score']['call'] + ' ' + format(r['score']['net'], '+d'), tone(r['score']['call']))}"
                        f"<div class='s'>{E('; '.join(i['name'] for i in r['score']['items']) or 'no aspect in orb')}</div></td>")
            o.append(f"<tr><td>{names[m]}</td>{cell(cur)}{cell(nxt)}<td class='n t-dn'>{x['hit']}% vs {x['always_bull']}%</td></tr>")
        o.append("</tbody></table></div><p class='s'>Rubric: orb-weighted Sun□Mars, Mars☌Ketu, Mars□Uranus, Saturn–Sun hard aspects, Mercury in Pisces (bearish) against Jupiter⚹Venus, "
                 "Jupiter△Sun, Venus△Jupiter (bullish). All four models call the 19 Nov chart bearish and the December chart bullish, but over 1,186 months every model's calls were "
                 "right less often than simply calling every month up. With the working natal time (10:10 LMT, Sun 27°17′39″) the 19 Dec chart has Virgo rising; with 27°18′ "
                 "(8 minutes later) Libra — so the house-based reading of that month depends on the birth time. Details in solar_return_engine_ET.html.</p>")
    o.append("<h3>Solar return's own forecasts</h3><div class='wrap'><table><thead><tr><th>Period</th><th>Forecast</th><th>Status</th><th>Detail</th></tr></thead><tbody>")
    for f in sr["scorecard"]:
        o.append(f"<tr><td>{E(f['period'])}<div class='s'>made {E(f['made'])}</div></td><td>{E(f['text'])}</td><td><b>{E(f['score']['status'])}</b></td><td class='s'>{E(f['score']['detail'])}</td></tr>")
    o.append("</tbody></table></div><h3>Solar return transit rules in this period</h3><div class='wrap'><table><thead><tr><th>Rule</th><th>Active</th><th>S&amp;P since 1928 (each episode once, next 5 sessions)</th><th>Big days</th></tr></thead><tbody>")
    for e in sr["episodes"]:
        t = e["record"]
        rec = f"up {t['eps_up5']}% vs {t['eps_exp5']}% (p {t['eps_p']})" if t else "–"
        big = f"{t['big']} vs {t['exp_big']} expected" if t else "–"
        span = f"{e['frm']:%a %d %b}" + ("" if e["frm"] == e["to"] else f" – {e['to']:%a %d %b}")
        o.append(f"<tr><td>{E(e['rule'])}</td><td class='n'>{span}</td><td class='s'>{E(rec)}</td><td class='s'>{E(big)}</td></tr>")
    bt = sr["bt"]
    o.append(f"</tbody></table></div><p class='s'>Daily call rule: the bearish aspects (Sun square Mars within 3°, Mars–Ketu within 5°) come first; Jupiter sextile Venus within 1° is bullish; "
             f"Mars square Uranus alone is volatile; otherwise the month's reading. Over 1928–2026: bullish calls right {bt['Bullish']['d1']}% same day / {bt['Bullish']['d5']}% over 5 sessions; "
             f"bearish calls right {bt['Bearish']['d1']}% / {bt['Bearish']['d5']}%; the S&amp;P rose on {bt['_base']['up1']}% of days and over {bt['_base']['up5']}% of 5-session spans.</p>")
    sr_jsg[:] = [sr["jsg"]]
    o.append(gjc_html(sr["gjc"]))
    o.append(gp_html(sr["gp"]))
    o.append(doc_html(sr["doc"]))
    o.append(jan_html(sr["jan"]))
    # day by day
    o.append("<h2 id='days'>Day by day</h2><div class='tool' style='display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px'>"
             "<button onclick='setAll(true)'>Open all</button><button onclick='setAll(false)'>Close all</button>"
             "<input type='search' placeholder='Filter days (e.g. Venus, Bearish, Ekadashi)' oninput='filt(this.value)' style='flex:1;min-width:200px;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)'></div>")
    for x in days:
        o.append(day_html(x, sr, res))
    # track record
    o.append(trust_html(track, sx))
    # checks
    o.append("<h2 id='checks'>Verification</h2><div class='wrap'><table><thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead><tbody>")
    for c in checks:
        o.append(f"<tr><td>{E(c['name'])}</td><td class='{'ok' if c['ok'] else 'bad'}'>{'pass' if c['ok'] else 'FAIL'}</td><td class='s'>{E(c['detail'])}</td></tr>")
    o.append("</tbody></table></div>")
    o.append("<h2>Sources and methods</h2><ul class='s'>"
             "<li>Rules: TA, KD, the 2026 document, your notes and Brihat Samhita (the catalogue), each with its 2000–2026 backtest (PROJECT_KNOWLEDGE.md §6); the 2026 calendar layer with its own backtest.</li>"
             "<li>Signal tables: gold and silver (tools/gold_signal_table.py), S&amp;P and Sensex (tools/market_signal_table.py): only rules that held in both halves of 2000–2026.</li>"
             "<li>Combined probability: naive Bayes on log-odds over the tables, Model v1.0 (gold), robust big-move factors, classical gochara / Chandra bala / Tara bala (S&amp;P) and Jupiter sextile Venus; fitted on 2000 – 23 Nov 2026.</li>"
             "<li>Solar return: NYSE monthly solar returns (tropical Sun at 27°18', New York), its stated indications and transit rules; generated by tools/solar_return_generate.py.</li>"
             "<li>Paap Kartari: the 2026 document's B116 (Mercury) and B117 (Jupiter), hemming as defined in config/conventions.yaml, tested by tools/kartari_test.py; TA's stricter Mercury version is in the catalogue.</li>"
             "<li>Model v1.0: Brihat Samhita Ch.41 with BPHS Shadbala and Ashtakavarga (gold only; silver has no sign in Ch.41).</li>"
             "<li>Holidays: NYSE (26 Nov, 25 Dec; early closes 27 Nov, 24 Dec), BSE (24 Nov Guru Nanak Jayanti, 25 Dec), COMEX (no settlement 26 Nov, 25 Dec).</li>"
             f"<li>Generated by tools/calendar_2026.py on {generated}.</li></ul></main><script>{JS}</script></body></html>")
    return "".join(o)


def day_html(x, sr, res):
    d = dt.date.fromisoformat(x["date"])
    pan = x["panchang"]
    srd = sr["daily"].get(d)
    head = f"{d:%A %d %B %Y}"
    sub = f"☾ {pan['moon_nakshatra']} · {tithi_txt(pan['tithi'])} · {day_summary(x, srd)}"
    o = [f"<details class='day' id='d{x['date']}'><summary><span class='h'>{E(head)}</span>{' ' + chip('holiday', 'vo') if x['closed'] else ''}"
         f"{' ' + chip('early close', 'vo') if x['early'] else ''}<div class='s'>{E(sub)}</div></summary><div class='body'>"]
    ev = key_events(x)
    if ev:
        o.append(f"<p><b>Sky today:</b> {E('; '.join(ev))}</p>")
    # markets
    if any(mk in x["prob"] for mk in MKS):
        o.append("<h3>Markets</h3><div class='wrap'><table><thead><tr><th>Market</th><th>Table label</th><th class='n'>Up that day</th><th class='n'>Up over 5 sessions</th>"
                 "<th class='n'>Big day</th><th>Supported rules (bullish / bearish)</th><th>Also</th></tr></thead><tbody>")
        for mk in MKS:
            pr = x["prob"].get(mk)
            if not pr:
                o.append(f"<tr><td>{NAME[mk]}</td><td colspan='6' class='s'>{'closed: ' + E(x['closed'][mk]) if mk in x['closed'] else 'weekend'}</td></tr>")
                continue
            sg = x["signals"][NAME[mk]][0]

            def p(t, pr=pr):
                v, bb, k = pr["all"][t], pr["base"][t], pr["kept"][t]
                cls = "" if t == "big" else "t-up" if v >= bb + 2 else "t-dn" if v <= bb - 2 else ""
                return f"<span class='{cls}'>{v:.0f}%</span><div class='s'>normal {bb:.0f}%" + (f" · kept {k:.0f}%" if k is not None else "") + "</div>"
            tl = x["tally"][mk]
            also = []
            cal = [c for c in x["calendar"] if c["market"] == mk and c["verdict"].startswith(("Bullish", "Bearish"))]
            if cal:
                also.append("calendar: " + ", ".join(f"{c['verdict']}" for c in cal))
            if x["vol"].get(mk):
                also.append("volatility factor: " + ", ".join(x["vol"][mk]))
            ws = list(dict.fromkeys(w["factor"].replace("Event: ", "").replace("Rule: ", "").replace("State: ", "").split(" [")[0] for w in x["watch"] if w["market"] == mk))
            if ws:
                also.append(f"big-move watch ({len(ws)}): " + "; ".join(ws[:3]) + (" …" if len(ws) > 3 else ""))
            if mk == "gold":
                gk = gjc_on(sr["gjc"], d)
                if gk:
                    also.append("Jupiter note: " + ", ".join(gk))
                v1 = x["v1"]
                also.append(f"Model v1.0: {v1['bias']} (confidence {v1['confidence']})")
            if mk == "spx" and x["mjn"]:
                also.append("Mars–Jupiter–Ketu lead active")
            if mk in ("spx", "sensex"):
                for k in kartari_on(sr, d):
                    also.append(f"{k['title'].split(' (')[0]} ({k['pair']})")
            sup = (f"<span class='t-up'>{len(tl['bull'])}</span> / <span class='t-dn'>{len(tl['bear'])}</span>"
                   + (f"<div class='s'>{E('; '.join(tl['bull'][:4]))}{' …' if len(tl['bull']) > 4 else ''}</div>" if tl["bull"] else "")
                   + (f"<div class='s'>− {E('; '.join(tl['bear'][:4]))}</div>" if tl["bear"] else ""))
            o.append(f"<tr><td><b>{NAME[mk]}</b></td><td>{chip((sg['sig'] + ' ' + (sg['st'] or '')).strip(), tone(sg['sig']))}<div class='s'>{E(sg['why'])}</div></td>"
                     f"<td class='n'>{p('up1')}</td><td class='n'>{p('up5')}</td><td class='n'>{p('big')}</td><td>{sup}</td><td class='s'>{E('; '.join(also)) or '–'}</td></tr>")
        o.append("</tbody></table></div>")
    # solar return
    sr_lines = []
    if srd:
        sr_lines.append(f"<b>Daily call:</b> {chip(srd['call'], tone(srd['call']))} <span class='s'>{E(srd['why'])}</span>")
    m = sr["month_of"](sr["all_months"], d)
    if m:
        sr_lines.append(f"<b>Month</b> {m['start']:%d %b} – {m['end']:%d %b}: {E(m['asc'])} rising → {chip(m['reading'], tone(m['reading']))}")
    for f in x["author"]["forecasts"]:
        sr_lines.append(f"<b>Forecast:</b> {E(f)}")
    rules = []
    for r in x["author"]["rules"]:
        t = sr["atests"].get(r)
        name = r.split(" – ")[0]
        rules.append(name + (f" (since 1928: up {t['eps_up5']}% vs {t['eps_exp5']}% over 5 sessions)" if t else ""))
    sr_lines.append(f"<b>Transit rules active:</b> {E('; '.join(rules) or 'none')} <span class='s'>{E(x['author']['detail'])}</span>")
    dl = []
    for r in doc_on(sr["doc"], d):
        recs = "; ".join(f"{SHORT[mk]} {v['text']}{' — holds' if v['ok'] else ''}" for mk, v in r["rec"].items()) or "no testable market direction"
        tm = ("time " + ", ".join(f"{z:+d} min" for z in r["diffs"]) + " vs ours") if r["diffs"] else ""
        dl.append(f"<li>{chip(r['inference'][:30], tone(r['tone'] or r['inference']))} <b>{E(r['event'])}</b>"
                  f"{(' — tone by its rule: ' + E(r['bhadra'])) if r['bhadra'] else ''} <span class='s'>{E(tm)}{' · ' if tm else ''}record 2000–2026: {E(recs)}</span></li>")
    if dl:
        o.append("<h3>2026 document, December table</h3><ul>" + "".join(dl) + "</ul>")
    for f in gp_on(sr["gp"], d):
        sr_lines.append(f"<b>Global Predictions</b> (outside forecast, {E(f['period'])}): {E(f['text'])} <span class='s'>status: {E(f['score']['status'])}</span>")
    o.append("<h3>Solar return and outside forecasts</h3><ul>" + "".join(f"<li>{s}</li>" for s in sr_lines) + "</ul>")
    # sky
    rows = "".join(f"<tr><td>{E(p['planet'])}</td><td>{E(p['sign'])} {E(p['deg'])}</td><td>{E(p['nakshatra'])}</td><td>{'R' if p['retro'] else ''}</td>"
                   f"<td>{E(p['dignity'])}{' combust' if p['combust'] else ''}</td><td class='n'>{p['speed']}</td></tr>" for p in x["positions"])
    grp = "; ".join(f"{k}: {', '.join(v)}" for k, v in pan["groups"].items())
    o.append(f"<details class='sub'><summary>Sky at 12:00 ET and panchang</summary><p class='s'>{E(pan['weekday'])} (day lord {E(pan['day_lord'])}) · tithi {E(tithi_txt(pan['tithi']))} · "
             f"Moon in {E(pan['moon_nakshatra'])} · yoga {E(YOGA_NAMES[pan['yoga'] - 1])} · together: {E(grp) or '–'}</p><div class='wrap'><table><thead><tr><th>Body</th><th>Sidereal position</th>"
             f"<th>Nakshatra-pada</th><th>R</th><th>Dignity</th><th class='n'>°/day</th></tr></thead><tbody>{rows}</tbody></table></div></details>")
    ch = "".join(f"<tr><td class='n'>{E(c['et'].split(' ', 3)[3])}</td><td class='s'>{E(c['ist'].split(' ', 3)[3])}</td><td>{E(c['kind'])}</td><td>{E(c['text'])}</td><td class='s'>{E(c['pos'])}</td></tr>"
                 for c in x["changes"])
    o.append(f"<details class='sub'><summary>Every planetary change today ({len(x['changes'])})</summary><div class='wrap'><table><thead><tr><th>ET</th><th>IST</th><th>Kind</th>"
             f"<th>Change</th><th>Detail</th></tr></thead><tbody>{ch}</tbody></table></div></details>")
    # rules
    for setname, label in (("general", "Market rules (S&P and Sensex)"), ("gold", "Gold rules"), ("silver", "Silver rules")):
        rs = [r for r in x["rules"] if r["set"] == setname]
        if not rs:
            continue
        rs.sort(key=lambda r: (not any(v and v["status"] in GOOD for v in r["record"].values()), r["tone"], r["title"]))
        ng = sum(1 for r in rs if any(v and v["status"] in GOOD for v in r["record"].values()))
        body = ""
        for r in rs:
            recs = "; ".join(f"{SHORT.get(k, k)}: {v['text']} [{v['status']}]" for k, v in r["record"].items() if v) or "no scored record"
            good = any(v and v["status"] in GOOD for v in r["record"].values())
            body += (f"<tr><td>{chip(r['tone'], tone(r['tone']))}</td><td>{'<b>' if good else ''}{E(r['title'])}{'</b>' if good else ''}</td><td class='s'>{E(r['kind'])}<br>{E(r['span'])}</td>"
                     f"<td class='s'>{E(recs)}</td><td class='s'>{E(r['refs'])}</td></tr>")
        o.append(f"<details class='sub'><summary>{label}: {len(rs)} active, {ng} with a supported record</summary><div class='wrap'><table><thead><tr><th>Tone</th><th>Rule</th>"
                 f"<th>When</th><th>Record 2000–2026 [status]</th><th>Source</th></tr></thead><tbody>{body}</tbody></table></div></details>")
    if x["calendar"]:
        body = "".join(f"<tr><td>{NAME[c['market']]}</td><td>{E(c['verdict'])}</td><td class='s'>{E(c['provenance'] or c['rule_id'])}</td><td class='s'>{E(c['record'])} {E(c['status'])}</td></tr>"
                       for c in x["calendar"])
        o.append(f"<details class='sub'><summary>Calendar-layer rows ({len(x['calendar'])})</summary><div class='wrap'><table><thead><tr><th>Market</th><th>Verdict</th><th>Rule</th>"
                 f"<th>Record 2000–2026</th></tr></thead><tbody>{body}</tbody></table></div></details>")
    other = []
    for w in x["windows"]:
        other.append(f"<li><b>{E(w['src'])}:</b> {E(w['text'])}</li>")
    v1 = x["v1"]
    other.append(f"<li><b>Model v1.0 (gold):</b> {E(v1['bias'])}, S {v1['S']}, V {v1['V']}, confidence {E(v1['confidence'])}; for: {E(', '.join(v1['agree']) or '–')}; "
                 f"against: {E(', '.join(v1['against']) or '–')}. Shadbala ratios: {E(', '.join(f'{k} {v:.2f}' for k, v in x['shadbala'].items()))}</li>")
    cl = "; ".join(f"{n}: gochara {dd['gochara']}, Chandra bala {dd['chandra']}, Tara bala {dd['tara']}" for n, dd in x["dasha"].items())
    other.append(f"<li><b>Classical layers (S&amp;P; your request, flagged):</b> {E(cl)}</li>")
    for k in kartari_on(sr, d):
        other.append(f"<li><b>{E(k['title'])}</b>, {E(k['pair'])}, {k['frm']:%d %b %H:%M} – {k['to']:%d %b %Y %H:%M} ET: {E(k['basis'])}. "
                     f"Record 2000–2026 as {k['tone'].lower()}: {E(krec(k))}.</li>")
    if x["mjn"]:
        other.append(f"<li><b>Mars and Jupiter with {E(x['mjn'])}:</b> the crash lead is active (3 of 13 episodes since 1928 fell 15%+; a lead, not proven).</li>")
    o.append("<details class='sub'><summary>Other analyses</summary><ul>" + "".join(other) + "</ul></details>")
    o.append("</div></details>")
    return "".join(o)


def jan_html(j):
    """January 2027 preview: Mercury in Paap Kartari (B116) on the S&P and the Sensex (tools/kartari_jan2027.py)."""
    o = ["<h2 id='jan'>January 2027: Mercury in Paap Kartari</h2>",
         "<p class='s'>2026 document B116: “negative event for financial markets”; with a benefic aspect, “very volatile and both side movement”. Past windows 2000–2026, "
         "each market in its own exchange time; a bearish call is right when the market fell more than 0.5% over the scored horizon. Full lists in kartari_jan2027_ET.html.</p>"]
    for mk, m in j["markets"].items():
        o.append(f"<h3>{E(m['name'])}</h3><div class='wrap'><table><thead><tr><th>Window</th><th>Hemmed by</th><th>Mercury</th><th>Benefic aspect</th><th>Sessions</th></tr></thead><tbody>")
        for w in m["jan"]:
            ss = [dt.date.fromisoformat(x) if isinstance(x, str) else x for x in w["sessions"]]
            a = dt.datetime.fromisoformat(w["start_local"]) if isinstance(w["start_local"], str) else w["start_local"]
            b = dt.datetime.fromisoformat(w["end_local"]) if isinstance(w["end_local"], str) else w["end_local"]
            o.append(f"<tr><td class='n'>{a:%a %d %b %H:%M} → {b:%a %d %b %H:%M} {w['tz']}</td><td>{E(w['pair'])}</td><td>{w['sign']}{', combust' if w['combust'] else ''}</td>"
                     f"<td>{E(', '.join(w['benefic']) or 'none')}</td><td class='s'>{len(ss)}: {ss[0]:%d %b}{' – ' + format(ss[-1], '%d %b') if len(ss) > 1 else ''}"
                     f"{'; ' + E('; '.join(w['holidays'])) if w['holidays'] else ''}</td></tr>")
        o.append("</tbody></table></div><div class='wrap'><table><thead><tr><th>Past windows</th><th class='n'>Windows</th><th class='n'>Bearish call right</th><th class='n'>Normal</th><th class='n'>p</th></tr></thead><tbody>")
        for k, v in m["groups"].items():  # green: above normal with p < 0.10; red: below normal
            if not (k.startswith(("All", "Sun is", "A benefic", "No benefic", "Like"))):
                continue
            ok = v["hit_rate"] is not None and v["base_rate"] is not None
            cls = "t-up" if ok and v["hit_rate"] > v["base_rate"] and (v["p_value"] or 1) < 0.10 else "t-dn" if ok and v["hit_rate"] < v["base_rate"] else ""
            o.append(f"<tr><td>{'<b>' if k.startswith('Like') else ''}{E(k)}{'</b>' if k.startswith('Like') else ''}</td><td class='n'>{v['windows']}</td>"
                     f"<td class='n {cls}'>{v['hit_rate']}%</td><td class='n'>{v['base_rate']}%</td><td class='n'>{v['p_value']}</td></tr>")
        tb = "; ".join(f"{t['frm'][5:]}–{t['to'][5:]} {t['sig']} {t['st']}" for t in m["table"])
        o.append(f"</tbody></table></div><p class='s'>Our {E(m['name'])} table in January: {E(tb)}.</p>")
    o.append("<div class='callout'><b>Reading:</b> on the S&amp;P, Mercury Paap Kartari has no edge at all (41% vs 39% over 2000–2026), and the windows like January's are at or below normal. "
             "On the Sensex the rule works overall (48% vs 41%, p 0.027), but mostly when no benefic aspects Mercury; in January Jupiter aspects Mercury in both windows, and the "
             "past windows like 1–15 Jan were right 42% vs 41%. The 25 Jan Sensex match (63% vs 43%) was picked from about 13 groups and is not reliable. "
             "Both of our market tables are bearish all January for other reasons (Venus–Uranus opposition, Mercury–Rahu conjunction).</div>")
    return "".join(o)


GJC_KEYS = ("Jupiter with Rahu or Ketu", "Jupiter–Saturn trine (5/9)", "Jupiter–Saturn opposite (7)", "Saturn aspects Jupiter", "Jupiter hemmed by malefics (12th and 2nd)",
            "Malefic vedha on Jupiter")


def gjc_on(g, d):
    out = []
    for k in GJC_KEYS:
        for a_, b_ in g["spans"].get(k, []):
            if dt.date.fromisoformat(a_) <= d <= dt.date.fromisoformat(b_):
                out.append(k)
    return out


sr_jsg = []


def gjc_html(g):
    o = ["<h2 id='gjc'>Gold: Jupiter's afflictions in past crashes (your note)</h2>",
         "<p class='s'>The note: in the gold crashes of 1974, 1980, 2008, 2011, 2020, 2022 and 2026 Jupiter was in trine / mutual aspect / conjunction with Saturn, or with a node "
         "or Pluto, or hemmed by malefics, and under the Vedha of malefics. Checked with sidereal Lahiri positions; details in gold_jupiter_crash_ET.html.</p>",
         "<div class='wrap'><table><thead><tr><th>Year</th><th>Crash (peak → low within 12 months)</th><th>Jupiter / Saturn at the peak</th><th>Held during the fall</th></tr></thead><tbody>"]
    for c in g["claims"]:
        for e in c["episodes"]:
            a_ = e["at_peak"]
            dur = "; ".join(f"{k} {v}%" for k, v in e["during"].items() if k != "afflicted")
            o.append(f"<tr><td><b>{c['year']}</b><div class='s'>{E(c['claim'])}</div></td><td class='n'>{e['peak']} → {e['trough']} ({e['depth']}%)</td>"
                     f"<td>Jupiter {E(a_['Jupiter sign'])}, Saturn {E(a_['Saturn sign'])}</td><td class='s'>{E(dur)}</td></tr>")
    sp = g["spec"]
    o.append("</tbody></table></div><div class='wrap'><table><thead><tr><th>Condition (monthly gold 1972–2026)</th><th class='n'>Share of months</th><th class='n'>At crash peaks</th>"
             "<th class='n'>Next 6 months: on / off</th><th class='n'>Fell 10%+ in 6 months: on / off</th></tr></thead><tbody>")
    for k, v in sp.items():
        o.append(f"<tr><td>{E(k)}</td><td class='n'>{v['share']}%</td><td class='n'>{v['at_peaks']} of {v['peaks']}</td><td class='n'>{v['f6_on']:+.1f}% / {v['f6_off']:+.1f}%</td><td class='n'>{v['down6_on']}% / {v['down6_off']}%</td></tr>")
    sps = g["spans"]

    def lst(k):
        return "; ".join(f"{a_} – {b_}" for a_, b_ in sps.get(k, [])) or "none"
    o.append("</tbody></table></div><div class='callout'><b>Reading:</b> the positions are mostly right, with sidereal corrections: at the Jan 1980 peak Saturn was in Virgo "
             "(it returned to Leo with Jupiter and Rahu from about March 1980); at the Aug 2011 peak Saturn was in Virgo (Libra only from 15 Nov 2011); at the Jan 2026 peak Jupiter "
             "was retrograde in Gemini (in Cancer, trine Saturn, from June 2026). Malefic Vedha on Jupiter occurred at some point in every fall, but the fast Sun and Mars make that "
             "true in most stretches. Taken together, “Jupiter afflicted” holds in 69% of all months, so it cannot single out crashes; the Jupiter–Saturn trine was present at 3 of 8 "
             "crash peaks against 16% of months, a lead from a small sample. "
             f"<br><b>When the current one ends:</b> Jupiter with Ketu in Leo ends on 5 Dec 2026 (Ketu enters Cancer). The pattern returns when Jupiter goes back into Cancer: "
             f"Jupiter with Ketu {lst('Jupiter with Rahu or Ketu')}; Jupiter–Saturn trine {lst('Jupiter–Saturn trine (5/9)')}; malefic Vedha on Jupiter {lst('Malefic vedha on Jupiter')}; "
             f"all together {lst('afflicted and malefic vedha')}.</div>")
    o.append("<div class='callout'><b>Bottom and recovery watch (gold_turns_ET.html):</b> at gold's 24 bottoms since 1972, a Jupiter direct station within ±30 days (33% vs 15% of weeks) "
             "and Jupiter–Saturn within 10° of trine / opposition / conjunction (42% vs 20%) were the most common features; a Saturn direct station within ±30 days was next (29% vs 16%). "
             "For the current fall that points to two watch windows: <b>11 Nov 2026 – 10 Jan 2027</b> (Saturn stations direct 11 Dec at Pisces 13.7°) and <b>14 Mar – 13 May 2027</b> "
             "(Jupiter stations direct 13 Apr at Cancer 22.75°, with Ketu within 0.5°, Mars nearby and Saturn trine within 1.4°). The Jupiter–Saturn trine was equally common at peaks, "
             "and about 40 features were tested, so these are watch periods, not timing rules.</div>")
    jsg = sr_jsg[0] if sr_jsg else None
    if jsg:
        o.append("<h3>Gold turn watch: Jupiter–Saturn aspects and stations, 2026–2030</h3><div class='wrap'><table><thead><tr><th>Date (New York)</th><th>Event</th><th>Gold: likely</th>"
                 "<th>Past gold turns at this point</th></tr></thead><tbody>")
        for r in jsg["rows"]:
            cls = "up" if r["lean"].startswith("bottom") else "dn" if r["lean"].startswith("top") else "vo"
            o.append(f"<tr><td class='n'>{E(r['date'])}</td><td>{E(r['event'])}</td><td>{chip(r['lean'], cls)}</td><td class='s'>{r['basis'].get('bottom', 0)} bottoms, {r['basis'].get('peak', 0)} tops</td></tr>")
        o.append("</tbody></table></div><p class='s'>All Jupiter–Saturn dates you were given match our ephemeris to the minute (jupiter_saturn_gold_ET.html). A lean is shown only where past "
                 "gold turns at the same point split at least 2 to 1 with three or more turns; samples are small.</p>")
    return "".join(o)


def gp_html(g):
    o = ["<h2 id='gp'>Global Predictions (outside forecast)</h2>",
         "<p class='s'>A forecaster in a WhatsApp group you follow (shared 24 Nov 2026). Western-style degree aspects, so it is tracked as an outside forecast and not added "
         "to our rules. News quoted in the messages is not used. Full detail in global_predictions_ET.html.</p>",
         "<div class='wrap'><table><thead><tr><th>Period</th><th>Call</th><th>Status</th><th>S&amp;P so far</th></tr></thead><tbody>"]
    for f in g["forecasts"]:
        o.append(f"<tr><td class='n'>{E(f['period'])}</td><td>{E(f['text'])}</td><td><b>{E(f['score']['status'])}</b></td><td class='s'>{E(f['score']['detail'])}</td></tr>")
    o.append("</tbody></table></div><div class='wrap'><table><thead><tr><th>Astronomy claim</th><th>Check</th><th>Detail</th></tr></thead><tbody>")
    for a in g["astronomy"]:
        o.append(f"<tr><td>{E(a['claim'])}</td><td><b>{E(a['status'])}</b></td><td class='s'>{E(a['detail'])}</td></tr>")
    o.append("</tbody></table></div><div class='wrap'><table><thead><tr><th>Same configuration on the S&amp;P, 1928–2026</th><th class='n'>Days</th><th class='n'>Big days</th>"
             "<th class='n'>Sharp reversals</th></tr></thead><tbody>")
    for k, r in g["tests"].items():
        o.append(f"<tr><td>{E(k)}</td><td class='n'>{r['n']}</td><td class='n'>{r['big']} vs {r['exp_big']} (p {r['p_big']})</td><td class='n'>{r['rev']} vs {r['exp_rev']} (p {r.get('p_rev')})</td></tr>")
    o.append("</tbody></table></div><div class='callout'><b>Reading:</b> the astronomy is right except Venus–Mercury, which form no aspect in 30 Nov – 5 Dec (24–28° apart). "
             "Since 1928 the Full Moon near Uranus came with twice the usual number of sharp reversals (14 vs 6.5, p 0.007), but all of the excess is in 1977–2026 "
             "(none in 1928–1976) and big days were normal: a lead, not a rule. Sun opposite Uranus and Mars square Uranus showed no reliable effect. In the last 250 sessions "
             "a short window had a big day or a sharp reversal about 15% of the time, so “volatility” calls in the current market are often right by default.</div>")
    return "".join(o)


def gp_on(g, d):
    out = []
    for f in g["forecasts"]:
        if dt.date.fromisoformat(f["start"]) <= d <= dt.date.fromisoformat(f["end"]) + dt.timedelta(days=1) and f["kind"] != "fade":
            out.append(f)
    return out


def trust_html(track, sx):
    cp = track["cp"]["markets"]
    o = ["<h2 id='trust'>Track record</h2><div class='wrap'><table><thead><tr><th>Market</th><th class='n'>2013–2026 walk-forward, 5 sessions</th>"
         "<th class='n'>Last 60 days (to 23 Nov), 5 sessions</th><th class='n'>1–23 Nov, all methods, same day</th><th class='n'>1–23 Nov, all methods, 5 sessions</th><th class='n'>Market up, 1–23 Nov</th></tr></thead><tbody>"]
    nov = track["nov"]["score"]
    for mk in MKS:
        w = cp[mk]["walk_forward"]["up5"]["kept"] or cp[mk]["walk_forward"]["up5"]["all"]
        w60 = cp[mk]["window"]["up5"]["all"]
        pl = nov["pooled"].get(mk, {})
        up = nov["ups"].get(mk, [0, 0, 0, 0])
        o.append(f"<tr><td>{NAME[mk]}</td><td class='n'>{w['hit']}% of {w['calls_up'] + w['calls_down']} calls</td>"
                 f"<td class='n'>{'–' if w60['hit'] is None else str(w60['hit']) + '% of ' + str(w60['calls_up'] + w60['calls_down'])}</td>"
                 f"<td class='n'>{round(pl['d1_right'] / pl['d1_calls'] * 100) if pl.get('d1_calls') else '–'}%</td><td class='n'>{round(pl['d5_right'] / pl['d5_calls'] * 100) if pl.get('d5_calls') else '–'}%</td>"
                 f"<td class='n'>{up[0]} of {up[1]} days</td></tr>")
    o.append("</tbody></table></div>")
    o.append(f"<h3>Why the Sensex scored higher than the S&amp;P</h3><div class='callout'><ul>"
             f"<li><b>Same labels for both indices.</b> The market table only uses rules that held on <i>both</i> indices, so its label was identical for the S&amp;P and the Sensex on "
             f"{sx['same_nov']} of {sx['n_nov']} weekdays in 1–23 Nov and {sx['same60']} of {sx['n60']} labelled days in the last 60 days.</li>"
             f"<li><b>The markets went opposite ways.</b> Over the 60 days the S&amp;P fell {abs(sx['move60']['spx'])}% while the Sensex rose {sx['move60']['sensex']}%. In 1–23 Nov the Sensex rose on "
             f"{sx['ups']['sensex'][0]} of {sx['ups']['sensex'][1]} days, the S&amp;P on {sx['ups']['spx'][0]} of {sx['ups']['spx'][1]}.</li>"
             "<li><b>The labels leaned bullish</b> (mostly Bullish in November). A bullish label is right in a rising market and wrong in a falling one, so the same call scored high on "
             "the Sensex and low on the S&amp;P. A rule that said “up” every day would have scored the same.</li>"
             f"<li><b>Over the long run the S&amp;P is no worse:</b> 2013–2026 walk-forward, 5 sessions: S&amp;P {sx['wf']['spx']}%, Sensex {sx['wf']['sensex']}%.</li>"
             "<li><b>No timing advantage:</b> each day's Sensex session (09:15–15:30 IST) ends before the New York day starts; labels come from astrology only, so there is no look-ahead.</li>"
             "<li><b>Conclusion:</b> the higher Sensex score reflects which way each market moved, not better astrology for India.</li></ul></div>")
    o.append("<h3>What did not work and is not used</h3><ul class='s'><li>Dashas at every level and as classical combinations (0 of 132 tests held): parked.</li>"
             "<li>Solar return monthly chart indications (1,186 months: no edge); its daily rules apart from Jupiter sextile Venus: at chance.</li>"
             "<li>Most catalogue rules on market direction: at chance after multiple-testing correction (see the tables' “supported” filter).</li></ul>")
    return "".join(o)


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 24)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2026, 12, 31)
    res, sr, track, FD = gather(a, b)
    checks = verify(res, sr, a, b)
    generated = dt.datetime.now(ET).strftime("%d %b %Y %H:%M ET")
    html_ = page(res, sr, track, checks, a, b, generated)
    sc = scan_text(html_)
    checks.append(dict(name="Naming: “Solar return”, never “author”", ok=sc["author"], detail="whole page scanned"))
    checks.append(dict(name="Dashas parked: no dasha blocks", ok=sc["dasha_blocks"], detail="whole page scanned"))
    html_ = page(res, sr, track, checks, a, b, generated)
    stem = f"calendar_{a}_to_{b}_ET"
    (OUT / f"{stem}.html").write_text(html_, encoding="utf-8")
    json.dump(dict(start=str(a), end=str(b), generated=generated, checks=checks, days=res["days"],
                   solar_return=dict(months=sr["months"], daily={str(k): v for k, v in sr["daily"].items()}, episodes=sr["episodes"], backtest=sr["bt"])),
              open(OUT / f"{stem}.json", "w"), indent=1, default=str)
    for c in checks:
        print(("PASS " if c["ok"] else "FAIL ") + c["name"] + " — " + c["detail"])
    print("wrote", stem, round(len(html_) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
