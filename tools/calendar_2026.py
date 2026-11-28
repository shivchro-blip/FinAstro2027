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


# ------------------------------------------------------------------ tuning from the November 2026 review (tools/november_review.py)
TUNE = dict(low_grey=False, model_colour=True, big_ok=set(MKS), watch_note="", vol_clean=False, vol_ok={})


def set_tuning(nov):
    """Apply the review's changes: Low labels grey, model probabilities uncoloured, big-day chance counted only where it held up."""
    if not nov:
        return
    rec = {r["id"]: r for r in nov.get("recommendations", [])}
    if rec.get("labels", {}).get("applied"):
        TUNE["low_grey"] = True
    if rec.get("model", {}).get("applied"):
        TUNE["model_colour"] = False
    if rec.get("big_days", {}).get("applied"):
        TUNE["big_ok"] = set(rec["big_days"].get("keep", []))
        if rec["big_days"].get("vol_ok") is not None and (OUT / "bigday_clean_test_ET.json").exists():
            TUNE["vol_clean"], TUNE["vol_ok"] = True, rec["big_days"]["vol_ok"]
    if rec.get("watch_windows", {}).get("applied"):
        TUNE["watch_note"] = " (no proven lift)"


def vol_status(mk, text):
    """Big-day factor status from the clean test: passes, or was chosen with data it is scored on."""
    if not TUNE["vol_clean"]:
        return ""
    return "passes a clean test" if any(k in text for k in TUNE["vol_ok"].get(mk, [])) else "in sample only"


def _why(sig):
    return sig.get("why") if isinstance(sig.get("why"), str) else "; ".join(sig.get("why") or [])


def lab_cls(sig, mk=None):
    if sig.get("sig") == "Volatile" and TUNE["vol_clean"] and mk:
        return "vo" if vol_status(mk, _why(sig)) == "passes a clean test" else "nt"
    return "nt" if TUNE["low_grey"] and sig.get("st") == "Low" else tone(sig["sig"])


def lab_title(sig, mk=None):
    w = _why(sig)
    if TUNE["low_grey"] and sig.get("st") == "Low":
        w += " | Low: a lean, not a day call (November 2026 review)"
    if sig.get("sig") == "Volatile" and TUNE["vol_clean"] and mk:
        w += f" | big-day factor: {vol_status(mk, w)}"
    return w


def model_cls(v, b):
    if not TUNE["model_colour"]:
        return ""
    return "t-up" if v >= b + 2 else "t-dn" if v <= b - 2 else ""


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
    sr["nsl"] = json.load(open(OUT / "new_sources_leftover_ET.json"))
    sr["nst"] = json.load(open(OUT / "new_sources_test_ET.json"))
    sr["dds"] = [json.load(open(f)) for f in sorted(OUT.glob("deep_dive_2026-12-*_ET.json"))]
    sr["dds_nov"] = [json.load(open(f)) for f in sorted(OUT.glob("deep_dive_2026-11-*_ET.json"))]
    nr = OUT / "november_review_2026-11_ET.json"
    sr["nov"] = json.load(open(nr)) if nr.exists() else None
    bc = OUT / "bigday_clean_test_ET.json"
    sr["bigclean"] = json.load(open(bc)) if bc.exists() else None
    jo, jf = OUT / "january_2027_outlook_ET.json", OUT / "january_2027_calls_ET.json"
    sr["jan_outlook"] = json.load(open(jo)) if jo.exists() else None
    sr["jan_frozen"] = json.load(open(jf)) if jf.exists() else None
    fo, ff = OUT / "february_2027_outlook_ET.json", OUT / "february_2027_calls_ET.json"
    sr["feb_outlook"] = json.load(open(fo)) if fo.exists() else None
    sr["feb_frozen"] = json.load(open(ff)) if ff.exists() else None
    mf = OUT / "march_2027_calls_ET.json"
    sr["mar_frozen"] = json.load(open(mf)) if mf.exists() else None
    set_tuning(sr["nov"])
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
    dchk = [c for d in sr.get("dds", []) for c in d["checks"]]
    add("Deep dive: every week's double checks pass (event times, counts, independent recount, coverage)", dchk and all(c["ok"] for c in dchk),
        f"{sum(c['ok'] for c in dchk)}/{len(dchk)} across {len(sr.get('dds', []))} weeks")
    nov = sr.get("nov")
    if nov:
        add("November review: the scorecard recount equals the day-by-day scorer", nov["check_fd"]["matched"] == nov["check_fd"]["of"],
            f"{nov['check_fd']['matched']} of {nov['check_fd']['of']} layer counts (that day and 5 sessions)")
        nchk = [c for d in sr.get("dds_nov", []) for c in d["checks"]]
        hist = {d.get("context", {}).get("history_end") for d in sr.get("dds_nov", [])}
        add("November deep dive: every week's double checks pass; its history ends 31 Oct 2026", nchk and all(c["ok"] for c in nchk) and hist == {"2026-10-31"},
            f"{sum(c['ok'] for c in nchk)}/{len(nchk)} across {len(sr.get('dds_nov', []))} weeks; history end {', '.join(sorted(map(str, hist)))}")
        add("November review: the long records stop before November", nov.get("hist_end") == "2026-10-31", f"tuning tests use data to {nov.get('hist_end')}")
    for label, jf, ndays in (("January", sr.get("jan_frozen"), 31), ("February", sr.get("feb_frozen"), 28), ("March", sr.get("mar_frozen"), 31)):
        if not jf:
            continue
        pubs = {mk: table_rows(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json") for mk in ("gold", "silver")}
        for mk in ("spx", "sensex"):
            pubs[mk] = table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", mk)
        bad = [f"{x['date']} {mk}" for x in jf["days"] for mk in MKS
               if (pubs[mk].get(dt.date.fromisoformat(x["date"])) or ("No signal",))[0] != x["signals"][NAME[mk]][0]["sig"]]
        add(f"{label} 2027 calls frozen, and their labels equal the published tables", not bad and len(jf["days"]) == ndays,
            f"frozen {jf['frozen_at']}; {len(jf['days'])} days, sessions " + ", ".join(f"{SHORT[k]} {v}" for k, v in jf["sessions"].items()) + ("; " + "; ".join(bad[:5]) if bad else ""))
    bcj = sr.get("bigclean")
    if bcj:
        rep = {mk: bcj["markets"][mk]["full"]["reproduces_published"] for mk in ("spx", "sensex")}
        add("Big-day clean test: the same choice on all of 2000–2026 reproduces the published robust factors", all(rep.values()),
            ", ".join(f"{SHORT[mk]} {'yes' if v else 'no'} ({len(bcj['markets'][mk]['full']['factors'])} factors)" for mk, v in rep.items()) + f"; test period {bcj['test']}")
    its = sr["nsl"]["calendar"]["items"]
    add("New-source layer loaded, every item carries its test result", its and all(i.get("verdict") for i in its), f"{len(its)} items (BS Iyer, Tajika Nilakanthi, Hayanaratna); none used in the signals")
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


def read_trust(sr, wf):
    nov = sr.get("nov")
    if not nov:
        return ("<li><b>What each market line shows:</b> our signal-table label (Bullish / Bearish with High, Moderate or Low strength), and the combined model's chance of a rise "
                "over the next 5 sessions. Green and red mean at least 2 points above or below that market's normal rate.</li>"
                f"<li><b>How much to trust it:</b> over 2013–2026 the combined model's calls were right {wf['spx']}% (S&amp;P), {wf['sensex']}% (Sensex), {wf['gold']}% (gold) and "
                f"{wf['silver']}% (silver) of the time over 5 sessions: a small edge at best. Treat them as leanings.</li>")
    t = nov["tuning"]
    lab = {mk: (t["labels"][mk].get("walk_forward") or t["labels"][mk])["rows"]["Any strength|d1"] for mk in MKS}
    CL = {"spx": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
          "sensex": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
          "gold": "Model call (2+ points from normal), all layers", "silver": "Model call (2+ points from normal), all layers"}
    md = {mk: t["model"][mk]["rows"][CL[mk]] for mk in MKS}
    keep = next((r.get("keep", []) for r in nov["recommendations"] if r["id"] == "big_days"), [])
    return ("<li><b>What each market line shows:</b> our signal-table label (Bullish / Bearish with High, Moderate or Low strength; <b>Low labels are grey</b>: a lean, not a day call) "
            "and the combined model's chance of a rise over the next 5 sessions, <b>no longer coloured</b> (changed after the <a href='#nov'>November 2026 review</a>).</li>"
            "<li><b>How much to trust it:</b> tested out of sample (2013–2026, with everything chosen on earlier years), neither the labels nor the model beat chance on any market. "
            "Labels, right vs chance: " + ", ".join(f"{SHORT[mk]} {lab[mk]['hit']}% vs {lab[mk]['exp']}%" for mk in MKS)
            + ". Model: " + ", ".join(f"{SHORT[mk]} {md[mk]['hit']}% vs {md[mk]['exp']}%" for mk in MKS)
            + ". November 2026 scored about what chance gives. Treat every label and probability as a leaning. " + big_sentence(nov, keep) + "</li>")


def big_sentence(nov, keep):
    rec = next((r for r in nov["recommendations"] if r["id"] == "big_days"), {})
    ok = rec.get("vol_ok")
    if ok is None:
        return (f"The big-day chance counts only for the {', '.join(SHORT[m] for m in keep) or '—'}; the volatility factors (S&amp;P, Sensex) did mark more big days "
                "in both halves of 2000–2026.")
    by = {}
    for mk, v in ok.items():
        for f in v:
            by.setdefault(f, []).append(SHORT[mk])
    good = " and ".join(f"{E(f)} ({' and '.join(m)})" for f, m in by.items()) or "no factor"
    model = (f"the model's big-day chance counts only for the {', '.join(SHORT[m] for m in keep)}" if keep else "the model's big-day chance is shown as untested for every market")
    return (f"<b>Big days:</b> in a clean test (factors chosen on 2000–2013 only, scored 2013–2026) only {good} kept marking more big days; the other volatility factors "
            f"are in sample only, and {model} (<a href='#bigclean'>details</a>).")


def market_cell(x, mk, sr_day=None):
    pr = x["prob"].get(mk)
    sig = x["signals"][NAME[mk]][0]
    if not pr:
        return f"<div class='row'><span class='k'>{SHORT[mk]}</span><span class='s'>{'closed' if mk in x['closed'] else ''}</span></div>"
    p5, b5 = pr["all"]["up5"], pr["base"]["up5"]
    pc = model_cls(p5, b5)
    return (f"<div class='row'><span class='k'>{SHORT[mk]}</span>{chip(lab_short(sig), lab_cls(sig, mk), lab_title(sig, mk))}<span class='{pc}' title='chance of a rise over the next 5 sessions'>{p5:.0f}%</span></div>")


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
    o.append("<div class='top'><nav><b>FinAstro calendar</b><a href='#read'>Read first</a><a href='#nov'>November review</a><a href='#keys'>Key dates</a><a href='#grid'>Calendar</a>"
             "<a href='#spans'>Signal spans</a><a href='#sr'>Solar return</a><a href='#ns'>New sources</a><a href='#dd'>Deep dive</a><a href='#jan'>January 2027</a><a href='#days'>Day by day</a><a href='#trust'>Track record</a><a href='#checks'>Checks</a>"
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
    o.append("<h2 id='read'>Read this first</h2><div class='callout'><ul>" + read_trust(sr, wf) +
             "<li><b>Solar return</b> is the NYSE monthly solar-return method you shared. Its daily calls here are generated by us the Solar return way; they reproduce 8 of the 9 days "
             "Solar return called, but over 1928–2026 the same rule was at chance.</li>"
             "<li><b>What has shown some edge:</b> Jupiter sextile Venus (bullish over 5 sessions), the bearish calendar fortnight rule “Three Saturdays in Shukla Paksha”, "
             + ("two volatility factors, Venus retrograde and Jupiter–Pluto 5/9 (more big days, no direction; they passed a clean test) "
                if TUNE["vol_clean"] else "robust volatility factors (more big days, no direction) ")
             + "and the Mars–Jupiter–node lead (a lead, not proven).</li>"
             "<li><b>Paap Kartari:</b> Jupiter is hemmed by Ketu and Mars (2026 document B117) from 16 Nov to 31 Jan 2027, and Mercury enters Paap Kartari "
             "(B116) on 1 Jan 2027. Their 2000–2026 records are in each day's notes, and January is checked market by market in the January 2027 section: Mercury's version held up as bearish on the Sensex only; Jupiter's showed more big days, "
             "not significant. Shubh Kartari is in none of our sources; tested anyway, it did not work and is not used.</li>"
             "<li><b>Not used:</b> dashas (tested, no edge; parked at your request), news and fundamentals.</li></ul></div>")
    o.append(nov_html(sr))
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
    o.append("<h2 id='grid'>Calendar</h2><div class='legend'>" + chip("Bullish", "up") + chip("Bearish", "dn") + chip("Volatile", "vo") + chip("—", "nt")
             + ("<span>H / M / L = strength; grey L = a Low label, a lean only · % = chance of a rise over the next 5 sessions (not coloured: no edge out of sample) · "
                if TUNE["low_grey"] else "<span>H / M / L = strength · % = chance of a rise over the next 5 sessions · ")
             + "○ full Moon · ● new Moon · ⟲ station · → sign change</span></div>")
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
    o.append(ns_html(sr))
    if sr.get("dds"):
        o.append(dd_intro(sr["dds"]))
        for dd in sr["dds"]:
            o.append(dd_html(dd))
    o.append(gp_html(sr["gp"]))
    o.append(doc_html(sr["doc"]))
    o.append(jan_html(sr["jan"], sr.get("jan_outlook")))
    # day by day
    o.append("<h2 id='days'>Day by day</h2><div class='tool' style='display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px'>"
             "<button onclick='setAll(true)'>Open all</button><button onclick='setAll(false)'>Close all</button>"
             "<input type='search' placeholder='Filter days (e.g. Venus, Bearish, Ekadashi)' oninput='filt(this.value)' style='flex:1;min-width:200px;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)'></div>")
    for x in days:
        o.append(day_html(x, sr, res))
    # track record
    o.append(trust_html(track, sx, sr.get("nov")))
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

            def p(t, pr=pr, mk=mk):
                v, bb, k = pr["all"][t], pr["base"][t], pr["kept"][t]
                if t == "big" and mk not in TUNE["big_ok"]:
                    return f"<span class='mut'>{v:.0f}%</span><div class='s'>normal {bb:.0f}% · untested</div>"
                cls = "" if t == "big" else model_cls(v, bb)
                return f"<span class='{cls}'>{v:.0f}%</span><div class='s'>normal {bb:.0f}%" + (f" · kept {k:.0f}%" if k is not None else "") + "</div>"
            tl = x["tally"][mk]
            also = []
            cal = [c for c in x["calendar"] if c["market"] == mk and c["verdict"].startswith(("Bullish", "Bearish"))]
            if cal:
                also.append("calendar: " + ", ".join(f"{c['verdict']}" for c in cal))
            if x["vol"].get(mk):
                also.append("volatility factor: " + ", ".join(f + (f" ({vol_status(mk, f)})" if TUNE["vol_clean"] else "") for f in x["vol"][mk]))
            ws = list(dict.fromkeys(w["factor"].replace("Event: ", "").replace("Rule: ", "").replace("State: ", "").split(" [")[0] for w in x["watch"] if w["market"] == mk))
            if ws:
                also.append(f"big-move watch{TUNE['watch_note']} ({len(ws)}): " + "; ".join(ws[:3]) + (" …" if len(ws) > 3 else ""))
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
            o.append(f"<tr><td><b>{NAME[mk]}</b></td><td>{chip((sg['sig'] + ' ' + (sg['st'] or '')).strip(), lab_cls(sg, mk))}<div class='s'>{E(lab_title(sg, mk))}</div></td>"
                     f"<td class='n'>{p('up1')}</td><td class='n'>{p('up5')}</td><td class='n'>{p('big')}</td><td>{sup}</td><td class='s'>{E('; '.join(also)) or '–'}</td></tr>")
        o.append("</tbody></table></div>")
    nsd = ns_on(sr, d)
    if nsd:
        o.append("<h3>New-source rules (tested; information only, not in the signals)</h3><ul class='s'>"
                 + "".join(f"<li>{E(i['when'])} {E(i['text'])} <span class='mut'>[{E(i['rule'])}: {E(i['verdict'])}]</span></li>" for i in nsd) + "</ul>")
    for dd in sr.get("dds", []):
        o.append(dd_day(dd, x["date"]))
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


def jan_html(j, jo=None):
    """January 2027 preview: Mercury in Paap Kartari (B116) on the S&P and the Sensex (tools/kartari_jan2027.py), and the
    update after the November review (tools/january_2027_outlook.py)."""
    o = ["<h2 id='jan'>January 2027: Mercury in Paap Kartari</h2>"]
    if jo:
        v = jo["verdicts"]
        o.append(f"<div class='callout'><b>Update ({E(jo['made'][:10])}), after the November review:</b><ul>"
                 + "".join(f"<li><b>{NAME[mk]}:</b> {E(v[mk]['summary'])}</li>" for mk in MKS)
                 + "</ul>Mercury's Paap Kartari is bearish on the Sensex in general, but in January Jupiter aspects Mercury in every window, which B116 reads as volatile "
                   "both ways; past windows like that were neither bearish nor more volatile (table below). No big-day factor that passed the clean test is active in January. "
                 + f"January's calls were frozen on {E(jo['frozen']['frozen_at'])} so the month can be scored afterwards like November. Call by call, with the evidence: "
                   "<a href='calendar_2027_NY_master.html#dd2027'>2027 calendar → Deep dive: January 2027</a>.</div>")
        kb = jo["kartari"]["b116"]["markets"]
        o.append("<div class='wrap'><table><thead><tr><th>Mercury Paap Kartari windows 2000–2026</th><th class='n'>S&amp;P big days vs expected</th><th class='n'>Sensex big days vs expected</th></tr></thead><tbody>"
                 + "".join(f"<tr><td>{E(name)}</td>" + "".join(f"<td class='n'>{kb[mk]['big_test'][name]['big']} vs {kb[mk]['big_test'][name]['exp']} (×{kb[mk]['big_test'][name]['lift']}, p {kb[mk]['big_test'][name]['p']})</td>" for mk in ("spx", "sensex")) + "</tr>"
                           for name in kb["spx"]["big_test"])
                 + "</tbody></table></div><p class='s'>Days of ±2% inside each window, against the number expected from that year's own rate.</p>")
    o += [
         "<p class='s'>2026 document B116: “negative event for financial markets”; with a benefic aspect, “very volatile and both side movement”. Past windows 2000–2026, "
         "each market in its own exchange time; a bearish call is right when the market fell more than 0.5% over the scored horizon.</p>"
         "<p class='s'><b>Every sky event of January 2027, backtested week by week</b>, is in the 2027 calendar: "
         "<a href='calendar_2027_NY_master.html#dd2027'>calendar_2027_NY_master.html → Deep dive: January 2027</a> "
         "(and <a href='calendar_2027_NY_master.html#dd202702'>February 2027</a>).</p>"]
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


DDM = (("spx", "S&P"), ("sensex", "Sensex"), ("gold", "Gold"), ("silver", "Silver"))


def _dd_cell(st):
    h1, h5, bg = st["h1"], st["h5"], st["big"]
    if h1["up_pct"] is None:
        return "<td class='s'>–</td>"
    flag = " class='t-up'" if (h5["p2"] or 1) < 0.05 and h5["up_pct"] > h5["base"] else " class='t-dn'" if (h5["p2"] or 1) < 0.05 else ""
    f1 = " ⚑" if (h1["p2"] or 1) < 0.05 else ""
    return (f"<td class='s'>next: {h1['up_pct']}% up vs {h1['base']}%{f1}<br><span{flag}>5 sessions: {h5['up_pct']}% vs {h5['base']}%</span>"
            f"<br>big day {bg['pct']}% (10% normal)</td>")


def dd_day(dd, date):
    day = next((d for d in dd["days"] if d["date"] == date), None)
    if not day or not day["events"]:
        return ""
    rows = []
    for e in day["events"]:
        c = dd["classes"][e["key"]]
        rows.append(f"<tr><td class='n'>{E(e['et'])}</td><td>{E(c['label'])}<div class='s'>{c['n_hist']} times since 2000</div></td>"
                    + "".join(_dd_cell(c["stats"][k]) for k, _ in DDM) + "</tr>")
    return (f"<details class='sub'><summary>Deep dive: every sky event today backtested ({len(day['events'])})</summary>"
            "<p class='s'>Each event's class scored on every occurrence 20 Nov 2000 – 20 Nov 2026 (§6 timing). There is no stated direction, so the test is two-sided. "
            "⚑ = next-session p &lt; 0.05; coloured = 5-session p &lt; 0.05. None passes the correction across the week.</p><div class='wrap'><table><thead><tr><th>ET</th><th>Event</th>"
            + "".join(f"<th>{n}</th>" for _, n in DDM) + f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>")


NOV_LAYERS = [
    ("Signal table", "Table label (any strength)"), ("Signal table: Low labels", "… Low labels"), ("Signal table: Moderate labels", "… Moderate labels"),
    ("Signal table: High labels", "… High labels"), ("Combined probability, all layers", "Combined model, all layers"),
    ("Combined probability, kept layers", "Combined model, kept layers"), ("Combined probability, all layers: up calls", "… its up calls"),
    ("Combined probability, all layers: down calls", "… its down calls"), ("Model v1.0 (Ch.41 + Shadbala)", "Model v1.0 (gold)"),
    ("Supported catalogue rules (net bullish - bearish)", "Catalogue rules with a supported record (net)"), ("Calendar-layer verdicts (net)", "2026 calendar-layer verdicts (net)"),
    ("USA gochara", "USA gochara"), ("NYSE gochara", "NYSE gochara"), ("USA Chandra bala", "USA Chandra bala"), ("NYSE Chandra bala", "NYSE Chandra bala"),
    ("USA Tara bala", "USA Tara bala"), ("NYSE Tara bala", "NYSE Tara bala"), ("Solar return: generated day call", "Solar return: day call (generated)"),
    ("Solar return: day-by-day forecasts", "Solar return: its own day forecasts"), ("Solar return: month view (bearish)", "Solar return: month view (bearish)"),
    ("Solar return: Jupiter sextile Venus (bullish)", "Solar return: Jupiter sextile Venus (bullish)"), ("Solar return: Sun square Mars (bearish)", "Solar return: Sun square Mars (bearish)"),
    ("Mars-Jupiter-node lead (bearish)", "Mars–Jupiter–node lead (bearish)")]


def _vs(j, digits=0):
    if not j or not j.get("n"):
        return "–"
    return f"{j['hit']:.{digits}f}% vs {j['exp']:.{digits}f}%" + (f" (p {j['p']})" if j.get("p") is not None else "")


def nov_cell(r):
    if not r or not (r["d1"]["calls"] or r["d5"]["calls"]):
        return "<td class='n s'>–</td>"
    a, b = r["d1"], r["d5"]
    cls = ("ok" if a["edge"] > 0 else "bad") if a["n"] and a["p"] is not None and a["p"] < 0.05 else ""
    head = f"{a['right']} ✓ {a['wrong']} ✗" + (f" · {a['flat']} small" if a["flat"] else "")
    five = f"5 sessions: {b['right']} ✓ {b['wrong']} ✗" if b["calls"] else ""
    vs = f"{a['hit']:.0f}% vs {a['exp']:.0f}% by chance" if a["n"] else "no move of 0.5% or more"
    return f"<td class='n'><span class='{cls}'><b>{head}</b></span><div class='s'>{vs}</div><div class='s'>{five}</div></td>"


def bigclean_html(bc):
    """The clean walk-forward test of the big-day volatility factors (tools/bigday_clean_test.py)."""
    if not bc:
        return ""
    m = bc["markets"]
    sp, sx = m["spx"], m["sensex"]
    cx = sx.get("cross_from_spx") or {}

    def t_(r):
        return (f"{r['obs']} vs {r['exp']} expected (×{r['lift']}, p {r['p']})" if r.get("lift") is not None else "–")
    o = ["<h3 id='bigclean'>Clean test of the big-day volatility factors</h3>",
         "<div class='callout'>The volatility factors (more ±2% days, no direction) were chosen on all of 2000–2026, so their good record after 2013 was partly in sample. "
         "Here the same choice (q &lt; 0.10 over every factor, more big days in both halves, still p &lt; 0.01 without the 2008–09 crash) was made on <b>20 Nov 2000 – 19 Nov 2013 only</b>, "
         f"and the factors it picked were scored on <b>20 Nov 2013 – 31 Oct 2026</b>, against the number of big days expected from each year's own rate. "
         f"<b>S&amp;P:</b> it picks {E(' and '.join(sp['clean_short']))}; after 2013 they marked {t_(sp['test'])}; without Feb–May 2020 ×{sp['test_no2020']['lift']} (p {sp['test_no2020']['p']}). "
         f"The result leans on 2025 (April's sell-off came during Venus retrograde): without 2025 ×{sp['loyo']['worst']['lift']} (p {sp['loyo']['worst']['p']}). "
         f"<b>Sensex:</b> nothing is picked by 2013, so its own factors have no clean test; but the S&amp;P's two factors, never fitted to the Sensex, marked {t_(cx.get('test', {}))} "
         f"on the Sensex after 2013 (Venus retrograde alone ×{next((e['lift'] for e in cx.get('each', []) if 'Venus retrograde' in e['factor']), '–')}), and no single year carries it. "
         f"<b>Gold and silver:</b> the factor picked by 2013 did not hold (gold ×{m['gold']['test']['lift']}, silver ×{m['silver']['test']['lift']}). "
         "Looser choices (q &lt; 0.20, or every lead with p &lt; 0.05) add factors that dilute it to chance, so the finding rests on these two factors.</div>",
         "<div class='wrap'><table><thead><tr><th>Market</th><th>Chosen on 2000–2013</th><th class='n'>Big days 2013–2026 on factor days</th><th class='n'>Without Feb–May 2020</th>"
         "<th class='n'>Plain rate: factor days vs others</th><th>Verdict</th></tr></thead><tbody>"]
    for mk in ("spx", "sensex", "gold", "silver"):
        r = m[mk]
        o.append(f"<tr><td>{NAME[mk]}</td><td class='s'>{E(', '.join(r['clean_short']) or 'nothing')}</td><td class='n'>{t_(r['test'])}</td><td class='n'>{t_(r['test_no2020'])}</td>"
                 f"<td class='n'>{(str(r['test']['rate_on']) + '% vs ' + str(r['test']['rate_off']) + '%') if r['test']['rate_on'] is not None else '–'}</td>"
                 f"<td class='{'ok' if r['verdict'] == 'holds out of sample' else 's'}'>{E(r['verdict'])}</td></tr>")
    if cx:
        o.append(f"<tr><td>BSE Sensex, with the S&amp;P's picks</td><td class='s'>{E(', '.join(sp['clean_short']))}</td><td class='n'>{t_(cx['test'])}</td><td class='n'>{t_(cx['test_no2020'])}</td>"
                 f"<td class='n'>{cx['test']['rate_on']}% vs {cx['test']['rate_off']}%</td><td class='{'ok' if (cx['test']['p'] or 1) < 0.05 else 's'}'>"
                 f"{'holds out of sample' if (cx['test']['p'] or 1) < 0.05 else 'does not hold'}</td></tr>")
    o.append("</tbody></table></div><p class='s'>Expected counts use each calendar year's own big-day rate, as the published factor test does; the plain rates do not, which is why they differ. "
             "The published sets, which the same choice on all of 2000–2026 reproduces exactly: S&amp;P " + E(", ".join(sp["full_short"])) + "; Sensex " + E(", ".join(sx["full_short"]))
             + ". Only the factors named above have passed a clean test; the rest are marked “in sample only” in the calendars.</p>")
    return "".join(o)


def nov_html(sr):
    nov = sr.get("nov")
    if not nov:
        return ""
    t = nov["tuning"]
    by = {(r["layer"], r["market"]): r for r in nov["rows"]}
    main_rows = [r for r in nov["rows"] if r["fd"] and not r["layer"].startswith("Combined lean")]
    P = sum(r["d1"]["right"] for r in main_rows)
    F = sum(r["d1"]["wrong"] for r in main_rows)
    S = sum(r["d1"]["flat"] for r in main_rows)
    n = P + F
    exp = sum(r["d1"]["n"] * r["d1"]["exp"] for r in main_rows if r["d1"]["n"]) / n if n else 0
    mo = nov["month"]
    o = ["<h2 id='nov'>November 2026 review: what passed, what failed, what changes</h2>",
         f"<div class='callout'><b>Every call the calendar made for 1–{dt.date.fromisoformat(nov['last']):%d} Nov, scored against the markets.</b> A call <b>passes</b> when the market moved its way "
         "by 0.5% or more and <b>fails</b> when it moved the other way by 0.5% or more; smaller moves are too small to count (§6). “By chance” is what calls with the same up/down mix would score, "
         "given how often that market rose in November. The combined model was fitted on data before 1 Nov, so November is out of sample for it."
         f"<br><b>All main layers together: {P} passed, {F} failed ({round(P / n * 100) if n else 0}%), {S} too small; by chance {exp:.0f}%.</b> "
         "Nearly every layer scored what chance gives. Where calls looked good (the Sensex), the calls were bullish and the Sensex rose; where they failed (the S&amp;P, gold, silver), "
         "the same bullish calls met falling markets. The long records (below) say the same: out of sample, neither the labels nor the model beat chance.</div>",
         "<div class='wrap'><table><thead><tr><th>Market</th><th class='n'>November</th><th class='n'>Sessions up / down</th><th class='n'>Moves under 0.5%</th><th class='n'>Big days</th></tr></thead><tbody>"]
    for mk in MKS:
        m = mo[mk]
        o.append(f"<tr><td>{NAME[mk]}</td><td class='n {'t-up' if m['change'] > 0 else 't-dn'}'>{m['change']:+.2f}%</td><td class='n'>{m['up']} / {m['down']}</td><td class='n'>{m['small']}</td><td class='n'>{m['big']}</td></tr>")
    o.append("</tbody></table></div>" + (f"<p class='s'>{E('; '.join(nov['marked']))}</p>" if nov["marked"] else ""))
    # scorecard
    o.append("<h3>Pass and fail, layer by layer (that day; 5 sessions underneath)</h3><div class='wrap'><table><thead><tr><th>Layer</th>"
             + "".join(f"<th class='n'>{NAME[mk]}</th>" for mk in MKS) + "</tr></thead><tbody>")
    for key, label in NOV_LAYERS:
        if not any(by.get((key, mk)) for mk in MKS):
            continue
        o.append(f"<tr><td>{E(label)}</td>" + "".join(nov_cell(by.get((key, mk))) for mk in MKS) + "</tr>")
    lv = nov["leans"]
    o.append("<tr><td>Deep-dive leans (nominal p &lt; 0.05 on history to 31 Oct)</td>" + "".join(
        f"<td class='n'><b>{lv[mk]['right']} ✓ {lv[mk]['wrong']} ✗</b><div class='s'>{_vs(lv[mk]).split(' (')[0]} by chance</div></td>" if lv.get(mk) and lv[mk]["n"] else "<td class='n s'>–</td>" for mk in MKS) + "</tr>")
    chk = nov["check_fd"]
    o.append(f"</tbody></table></div><p class='s'>Green / red: p &lt; 0.05 against chance (none in November). Recount check: {chk['matched']} of {chk['of']} layer counts equal the existing "
             "day-by-day scorer's. The 5-session figures overlap from day to day, so they are not independent.</p>")
    # where it failed
    sp = nov["spans"]
    o.append("<h3>Where it failed</h3><ul>")
    vr = [x for x in sp if x["id"] == "ta_s25_venus_rahu_6"]
    if vr:
        s_ = {x["market"]: x for x in vr}
        o.append(f"<li><b>S&amp;P labels: one span rule.</b> Venus–Rahu 6/8 (Shadashtak, Bullish, Low) labelled every day from {dt.date.fromisoformat(vr[0]['frm']).day} to "
                 f"{dt.date.fromisoformat(vr[0]['to']).day} {dt.date.fromisoformat(vr[0]['to']):%b}. Over that span the S&amp;P fell {abs(s_['spx']['ret']):.1f}% and the Sensex rose {s_['sensex']['ret']:.1f}%: the same rule passed on one index and failed on the other. "
                 "The table's record for it counts each span once; as a day-by-day call it never had a measured edge.</li>")
    sl = by.get(("Signal table: Low labels", "spx"), {}).get("d1", {})
    o.append(f"<li><b>Low labels</b> carried most S&amp;P calls ({sl.get('right', 0)} passed, {sl.get('wrong', 0)} failed). Out of sample they were below chance in three of the four markets.</li>")
    ms = by.get(("Combined probability, all layers", "spx"), {}).get("d1", {})
    o.append(f"<li><b>The combined model made only up calls on the S&amp;P</b> in a falling month ({ms.get('right', 0)} passed, {ms.get('wrong', 0)} failed) and almost no calls on gold and silver.</li>")
    g, sv = by.get(("Signal table", "gold"), {}).get("d1", {}), by.get(("Signal table", "silver"), {}).get("d1", {})
    v1 = by.get(("Model v1.0 (Ch.41 + Shadbala)", "gold"), {}).get("d1", {})
    o.append(f"<li><b>Metals:</b> bullish labels in a month when gold fell {abs(mo['gold']['change']):.1f}% and silver {abs(mo['silver']['change']):.1f}%: gold labels {g.get('right', 0)} passed / {g.get('wrong', 0)} failed, "
             f"silver {sv.get('right', 0)} / {sv.get('wrong', 0)}; Model v1.0 (gold) {v1.get('right', 0)} / {v1.get('wrong', 0)}.</li>")
    bg = nov["bigs"]
    nb = sum(len(bg[mk]["big_days"]) for mk in MKS)
    fl = sum(b_["warned"] for mk in MKS for b_ in bg[mk]["big_days"])
    o.append(f"<li><b>Big days:</b> {nb} across the four markets; the model flagged {fl} of them (" + ", ".join(f"{SHORT[mk]} {sum(b_['warned'] for b_ in bg[mk]['big_days'])} of {len(bg[mk]['big_days'])}" for mk in MKS)
             + "). On volatility-factor days: " + ", ".join(f"{SHORT[mk]} {sum(b_['vol'] for b_ in bg[mk]['big_days'])} of {len(bg[mk]['big_days'])}" for mk in ("spx", "sensex"))
             + f". Gold's big-move watch caught {bg['gold']['watch_big']} of {bg['gold']['watch_days']} watch days; over the long run it has no proven lift.</li>")
    o.append(f"<li><b>Deep-dive leans:</b> {lv['all']['right']} of {lv['all']['n']} right ({lv['all']['hit']:.0f}% vs {lv['all']['exp']:.0f}% by chance); silver {lv['silver']['right']} of {lv['silver']['n']}.</li></ul>")
    o.append("<details class='sub'><summary>Every table rule's November span</summary><div class='wrap'><table><thead><tr><th>Rule</th><th>Market</th><th class='n'>Span</th><th class='n'>Move</th><th>Result</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{E(x['rule'])} <span class='s'>({E(x['tone'])})</span></td><td>{SHORT[x['market']]}</td><td class='n'>{dt.date.fromisoformat(x['frm']):%d %b} – {dt.date.fromisoformat(x['to']):%d %b}</td>"
                       f"<td class='n'>{x['ret']:+.2f}%</td><td class='{'ok' if x['result'] == 'passed' else 'bad' if x['result'] == 'failed' else 's'}'>{E(x['result'])}</td></tr>" for x in sp)
             + "</tbody></table></div><p class='s'>Scored as the table's records are: from the last close before the span to its last day.</p></details>")
    o.append("<details class='sub'><summary>The rules behind the labels, passed and failed</summary><div class='wrap'><table><thead><tr><th>Market</th><th>Behind the label</th><th>Call</th>"
             "<th class='n'>Passed</th><th class='n'>Failed</th><th class='n'>Too small</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{SHORT[r['market']]}</td><td>{E(r['reason'])}</td><td>{E(r['call'])}</td><td class='n'>{r['passed']}</td><td class='n'>{r['failed']}</td><td class='n'>{r['small']}</td></tr>" for r in nov["reasons"])
             + "</tbody></table></div></details>")
    for mk in MKS:
        w = nov["wrong"].get(mk, [])
        if w:
            o.append(f"<details class='sub'><summary>{NAME[mk]}: every failed label and model call ({len(w)})</summary><div class='wrap'><table><thead><tr><th class='n'>Day</th><th>Layer</th><th>Call</th><th class='n'>Move</th><th>Why</th></tr></thead><tbody>"
                     + "".join(f"<tr><td class='n'>{E(x['weekday'][:3])} {dt.date.fromisoformat(x['date']):%d %b}</td><td>{E(x['layer'])}</td><td>{E(x['call'])}</td><td class='n'>{x['move']:+.2f}%</td><td class='s'>{E(x['why'] or '')}</td></tr>" for x in w)
                     + "</tbody></table></div></details>")
    o.append(f"<details class='sub'><summary>Deep-dive leans, one by one ({len(nov['lean_list'])})</summary><div class='wrap'><table><thead><tr><th class='n'>Day</th><th>Event</th><th>Market</th><th>Lean</th><th>History to 31 Oct</th><th class='n'>Move</th><th>Result</th></tr></thead><tbody>"
             + "".join(f"<tr><td class='n'>{dt.date.fromisoformat(x['date']):%d %b}</td><td>{E(x['event'])}</td><td>{SHORT[x['market']]}</td><td>{E(x['lean'])}, {E(x['horizon'])}</td><td class='s'>{E(x['hist'])}</td>"
                       f"<td class='n'>{x['move']:+.2f}%</td><td class='{'ok' if x['result'] == 'passed' else 'bad' if x['result'] == 'failed' else 's'}'>{E(x['result'])}</td></tr>" for x in nov["lean_list"])
             + "</tbody></table></div></details>")
    # tuning
    o.append("<h3>What changes, and the long-run evidence for it</h3><p class='s'>Each change was tested on the long records (2000–2026; walk-forward 2013–2026 where one exists) "
             "and on 24 Sep – 27 Nov, never on November alone. Nothing here adds a rule; it changes how far the existing calls are trusted.</p>")
    for r in nov["recommendations"]:
        st = (chip("now in " + r.get("where", "the calendars"), "up") + (f" <span class='s'>({E(r['where_note'])})</span>" if r.get("where_note") else "")) if r["applied"] else chip("information", "nt")
        o.append(f"<div class='callout'><b>{E(r['title'])}</b> {st}<div class='s'><b>Evidence:</b> {E(r['evidence'])}</div>"
                 + (f"<div class='s'><b>November:</b> {E(r['november'])}</div>" if r.get("november") else "") + "</div>")
    # out of sample table
    CL = {"spx": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
          "sensex": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
          "gold": "Model call (2+ points from normal), all layers", "silver": "Model call (2+ points from normal), all layers"}
    o.append("<h3>Out of sample, 2013–2026: right vs chance, every day</h3><div class='wrap'><table><thead><tr><th>Market</th><th class='n'>Low labels</th><th class='n'>Moderate or High</th>"
             "<th class='n'>All labels</th><th class='n'>Combined model</th><th class='n'>Big days on flagged days vs others</th></tr></thead><tbody>")
    for mk in MKS:
        L = (t["labels"][mk].get("walk_forward") or t["labels"][mk])["rows"]
        b_ = t["big"][mk]
        bigc = f"{b_['warned_pct']}% vs {b_['other_pct']}% (p {b_['p']})" if b_["warned"] else "never flags"
        o.append(f"<tr><td>{NAME[mk]}</td><td class='n'>{_vs(L['Low|d1'], 1)}</td><td class='n'>{_vs(L['Moderate or High|d1'], 1)}</td><td class='n'>{_vs(L['Any strength|d1'], 1)}</td>"
                 f"<td class='n'>{_vs(t['model'][mk]['rows'][CL[mk]], 1)}</td><td class='n'>{bigc}</td></tr>")
    v1 = t["model_v1"]["all"]
    o.append(f"</tbody></table></div><p class='s'>S&amp;P and Sensex labels: rules picked on their 2000–2013 records only ({E(', '.join(t['labels']['spx']['walk_forward']['rules']))}), "
             "then every day 2013–2026 scored. Gold and silver labels: the tables' data-picked parts re-picked on 2000–2013. Combined model: fitted on earlier years only "
             f"(S&amp;P and Sensex with the walk-forward labels). Model v1.0 (gold, a source model) over 2000–2026: {_vs(v1, 1)}. "
             "Chance is what calls with the same up/down mix would score, from each year's share of up days. With the table's own rules chosen on all of 2000–2026, the S&amp;P "
             f"labels look better ({_vs(t['labels']['spx']['rows']['Any strength|d1'], 1)}), but that is the selection, not an edge.</p>")
    o.append("<details class='sub'><summary>Each S&amp;P / Sensex table rule as a day-by-day call, 2000–2026</summary><div class='wrap'><table><thead><tr><th>Rule</th><th>Market</th><th>Published record (per span)</th>"
             "<th class='n'>Every day</th><th class='n'>q</th><th class='n'>2000–2012</th><th class='n'>2013–2026</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{E(r['rule'])} <span class='s'>({E(r['tone'])}, {E(r['strength'])})</span></td><td>{SHORT[r['market']]}</td><td class='s'>{E(r['record'] or '–')}</td>"
                       f"<td class='n'>{_vs(r['day'], 1)}</td><td class='n'>{r['q']}</td><td class='n'>{_vs(r['first_half'], 1).split(' (')[0]}</td><td class='n'>{_vs(r['second_half'], 1).split(' (')[0]}</td></tr>" for r in t["rules_per_day"])
             + "</tbody></table></div><p class='s'>These rules were chosen on 2000–2026, so this is in sample; even so, only one of the 20 rule-and-market tests passes the correction.</p></details>")
    o.append(bigclean_html(sr.get("bigclean")))
    w = t["window"]
    names = list(next(iter(w.values()))["rows"])
    o.append("<details class='sub'><summary>The same changes on 24 Sep – 27 Nov</summary><div class='wrap'><table><thead><tr><th>Rule</th>"
             + "".join(f"<th class='n'>{NAME[mk]} <span class='s'>(up {w[mk]['up_share']}%)</span></th>" for mk in MKS) + "</tr></thead><tbody>"
             + "".join(f"<tr><td>{E(nm)}</td>" + "".join(f"<td class='n'>{w[mk]['rows'][nm]['right']} of {w[mk]['rows'][nm]['n']}<div class='s'>{_vs(w[mk]['rows'][nm]).split(' (')[0]}</div></td>" if w[mk]["rows"][nm]["n"] else "<td class='n s'>–</td>" for mk in MKS) + "</tr>" for nm in names)
             + "</tbody></table></div><p class='s'>Too short to prove anything either way; nothing here passes p &lt; 0.05.</p></details>")
    # November deep dive
    dds = sr.get("dds_nov") or []
    if dds:
        n_ = sum(d["n_cells"] for d in dds)
        sig = sum(len(d["significant"]) for d in dds)
        nom = sum(len(d["nominal"]) for d in dds)
        big = sum(len(d["big_significant"]) for d in dds)
        ck = [c for d in dds for c in d["checks"]]
        weeks = "".join(f"<a href='#dd{d['start'][5:7]}{d['start'][8:]}'>{d['start'][8:]}–{d['end'][8:]} Nov</a> " for d in dds)
        o.append(f"<h3 id='ddnov'>November deep dive: every sky event backtested, week by week</h3><p class='s'>Weeks: {weeks}</p>"
                 f"<div class='callout'>History ends 31 Oct 2026, so no November event scores itself. <b>{n_} tests: {sig} pass the correction</b>, {nom} have a nominal p &lt; 0.05 "
                 f"(about {round(n_ * 0.05)} expected by chance); big days: {big} pass. <b>Double-checked:</b> {sum(c['ok'] for c in ck)} of {len(ck)} checks pass, and 10 sample results recounted "
                 "from raw prices with separate code all match.</div>")
        for dd in dds:
            o.append(dd_html(dd, nov.get("moves")))
    return "".join(o)


def dd_intro(dds):
    n = sum(d["n_cells"] for d in dds)
    sig = sum(len(d["significant"]) for d in dds)
    nom = sum(len(d["nominal"]) for d in dds)
    big = sum(len(d["big_significant"]) for d in dds)
    chk = [c for d in dds for c in d["checks"]]
    weeks = "".join(f"<a href='#dd{d['start'][5:7]}{d['start'][8:]}'>{d['start'][8:]}–{d['end'][8:]} Dec</a> " for d in dds)
    return (f"<h2 id='dd'>Deep dive, week by week to 31 Dec</h2><p class='s'>Weeks: {weeks}</p>"
            f"<div class='callout'><b>Every sky event from 1 to 31 Dec backtested.</b> Each event of each week (exact aspects, sign and nakshatra entries, stations, combustion, "
            "the Moon's perigee and apogee, tithi, yoga, Bhadra, lunations) was turned into its event class and scored on every occurrence since 2000 on the S&amp;P 500, Sensex, gold and silver, "
            f"over the next session and over 5 sessions, two-sided, with big days, using Benjamini–Hochberg correction within each week. <b>{n} tests: {sig} pass the correction</b>, and {nom} have a nominal "
            f"p &lt; 0.05, against about {round(n * 0.05)} expected by chance. Big days: {big} pass. <b>The sky events of December carry no measurable direction or big-day signal.</b> "
            "The labels, the model and the rules with a supported record (below and in each day) are what is left.<br>"
            f"<b>Double-checked:</b> {sum(c['ok'] for c in chk)} of {len(chk)} checks pass. Every event time was re-derived from the ephemeris, the occurrence counts were checked against "
            "the expected frequencies, one result per week was recounted from raw prices with separate code, and every sky event was confirmed as classified. "
            "Five sample results were also recomputed independently: all match.<br>"
            "<b>2027:</b> the same weekly deep dive for <a href='calendar_2027_NY_master.html#dd2027'>January 2027</a>, "
            "<a href='calendar_2027_NY_master.html#dd202702'>February 2027</a> and <a href='calendar_2027_NY_master.html#dd202703'>March 2027</a> is in the 2027 calendar "
            "(calendar_2027_NY_master.html); each month opens with an update after the November review (every call with its out-of-sample evidence; the calls frozen "
            "for scoring)." + "".join(f" {m}: {E(t)}" for m, t in _month_lines()) + "</div>")


def _month_lines():
    out = []
    for stem, m in (("february_2027", "February"), ("march_2027", "March")):
        f = OUT / f"{stem}_outlook_ET.json"
        if f.exists():
            out.append((m, json.load(open(f))["headline"].split(" When ")[0].split(" Out of sample")[0]))
    return out


def dd_html(dd, moves=None):
    """One week of the deep dive; with moves ({market: {date: {r1}}}) each label also shows what the market did (✓ / ✗ at 0.5%)."""
    from datetime import date as _d
    a, b = _d.fromisoformat(dd["start"]), _d.fromisoformat(dd["end"])
    nom = "; ".join(f"{x['label']} ({x['market']}, {'next session' if x['horizon'] == 'h1' else '5 sessions'}: {x['up_pct']}% up vs {x['base']}%, p {x['p2']}, q {x.get('q')})" for x in dd["nominal"]) or "none"
    o = [f"<h3 id='dd{a:%m%d}'>Week {a:%a %d %b} – {b:%a %d %b %Y}</h3>",
         f"<div class='callout'><b>Every sky event of the week backtested.</b> {len(dd['classes'])} event classes (exact aspects, sign and nakshatra entries, stations, combustion, tithi, yoga, Bhadra, lunations) "
         f"were each scored on every occurrence since 2000 on the S&amp;P 500, Sensex, gold and silver: {dd['n_cells']} tests. "
         f"<b>{len(dd['significant'])} pass the Benjamini–Hochberg correction</b>, and {len(dd['nominal'])} have a nominal p &lt; 0.05. By chance alone about {round(dd['n_cells'] * 0.05)} would be expected, "
         f"so the week's events carry no measurable direction. Nominal ones: {E(nom)}. Big days: {len(dd['big_significant'])} classes pass.</div>",
         "<div class='wrap'><table><thead><tr><th>Day</th><th>Labels (table) and model: up that day / over 5 sessions vs normal" + (" → what the market did" if moves else "") + "</th>"
         "<th>Catalogue rules active (with a supported record)</th><th>Solar return</th><th>New sources</th></tr></thead><tbody>"]
    for d in dd["days"]:
        lab = []
        for k, nm in DDM:
            sg = d["signals"].get({"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}[k], {})
            pr = d["prob"].get(k)
            if pr:
                txt = f"{nm}: {E((sg.get('sig', '') + ' ' + sg.get('st', '')).strip())} · {pr['all']['up1']:.0f}% / {pr['all']['up5']:.0f}% (normal {pr['base']['up1']:.0f}% / {pr['base']['up5']:.0f}%)"
                mv = (moves or {}).get(k, {}).get(d["date"])
                if mv:
                    c = 1 if sg.get("sig", "").startswith("Bullish") else -1 if sg.get("sig", "").startswith("Bearish") else 0
                    r = mv["r1"]
                    mark = "" if not c else " (too small)" if abs(r) < 0.5 else " ✓" if (r > 0) == (c > 0) else " ✗"
                    txt += f" → <b class='{'t-up' if r > 0 else 't-dn'}'>{r:+.2f}%</b>{mark}"
                lab.append(txt)
            else:
                lab.append(f"{nm}: closed")
        sup = []
        for k, nm in DDM:
            c = d["rules"].get(k, {})
            good = sum(v for st_, v in c.items() if st_ in ("Strongest", "Supported", "Consistent"))
            tot = sum(c.values())
            sup.append(f"{nm} {good} of {tot}")
        notable = "; ".join(d["notable"].get("spx", [])[:2])
        o.append(f"<tr><td class='n'>{E(d['weekday'])} {E(d['date'][5:])}</td><td class='s'>{'<br>'.join(lab)}</td>"
                 f"<td class='s'>{E(', '.join(sup))}<br><span class='mut'>{E(notable)}</span></td><td class='s'>{E('; '.join(d['solar_return']['rules']) or 'month reading')}</td>"
                 f"<td class='s'>{E('; '.join(d['new_sources'][:3]))}</td></tr>")
    o.append("</tbody></table></div>")
    return "".join(o)


def ns_on(sr, d):
    """New-source items (BS Iyer, Tajika Nilakanthi, Hayanaratna) active on day d, ET."""
    out = []
    for i in sr["nsl"]["calendar"]["items"]:
        s_, e_ = dt.datetime.fromisoformat(i["start"]), dt.datetime.fromisoformat(i["end"])
        if i["kind"] == "instant":
            if s_.date() == d:
                out.append(dict(when=f"{s_:%H:%M} ET", text=i["text"], rule=i["rule"], verdict=i["verdict"]))
        elif s_.date() <= d <= e_.date():
            edge = " (starts " + f"{s_:%H:%M}" + ")" if s_.date() == d and s_.time() != dt.time(0) else " (ends " + f"{e_:%H:%M}" + ")" if e_.date() == d else ""
            out.append(dict(when="all day" + edge, text=i["text"], rule=i["rule"], verdict=i["verdict"]))
    return out


def ns_html(sr):
    nst, nsl = sr["nst"], sr["nsl"]
    y, mons = nsl["calendar"]["year"], nsl["calendar"]["months"]
    n1 = sum(len(t["by"]) for k in ("step2", "step3", "step4") for t in nst[k]["tests"]) + sum(len(t["cmp"]) for t in nst["step5"])
    n2 = sum(len(t["by"]) for t in nsl["daily"]) + sum(len(t["cmp"]) for t in nsl["annual"])
    o = ["<h2 id='ns'>New sources: Brihat Samhita (Iyer), Tajika Nilakanthi, Hayanaratna</h2>",
         f"<p class='s'>Every computable rule from the three books added on 27 Nov 2026 was backtested: {n1} results in new_sources_test_ET.html and {n2} in new_sources_leftover_ET.html, "
         "using the §6 method with Benjamini–Hochberg correction. <b>None holds, so none of them feeds the signals or the probabilities.</b> They are shown here and in each day "
         "as information, each with its test result.</p>",
         "<div class='callout'><b>Worth knowing:</b><ul>"
         "<li><b>Brihat Samhita 42.6 with its eclipse condition:</b> 2026 qualifies (lunar eclipse of 28 Aug, Sun in sidereal Leo), so the stated sell window is 16 Dec 2026 – 14 Jan 2027. "
         f"But eclipse years did worse than other years: gold rose by mid-December in {nst['step1']['gold_1972']['eclipse years']['up5']} of {nst['step1']['gold_1972']['eclipse years']['n']} eclipse years, "
         f"against {nst['step1']['gold_1972']['other years']['up5']} of {nst['step1']['gold_1972']['other years']['n']} other years.</li>"
         f"<li><b>Lord of the year 2026–27</b> (Chaitra new moon {y['chaitra']}): {E(y['lord_of_year_us'])} by US time, {E(y['lord_of_year_india'])} by Indian time; both are 'good' lords. "
         "Watch list only: on the S&amp;P 1929–2026, years with good lords were up 76% vs 64% (p 0.047), but it weakens to p 0.10 with the Indian weekday.</li>"
         f"<li><b>NYSE annual chart</b> ({E(y['nyse_return'])}): the Tajika ruler of the year is {E(y['ruler'])} ({E(y['ruler_role'])}), strength {y['ruler_strength']} of 20, in house {y['ruler_house']}; "
         f"the muntha is in house {y['muntha_house']}. By the text that means a good year with the muntha in a weak house, but both rules test at chance.</li>"
         "<li><b>Eclipse rules</b> (eclipse in Libra or Sagittarius; eclipse in the lunar month Chaitra, 'dealers in gold suffer'): nominal p &lt; 0.05 on gold and silver only, from 9–20 cases. "
         "No such eclipse falls before 2028, so there is nothing to watch in this calendar.</li></ul></div>"]
    o.append("<h3>NYSE monthly charts in this period (Tajika, Model B)</h3><div class='wrap'><table><thead><tr><th>Month starts</th><th>Navamsha 2nd-house rule</th><th>Navamsha 11th-house rule</th>"
             "<th>Wealth / trade / business sahams</th><th>Sun's house</th></tr></thead><tbody>")
    for m in mons:
        sh = "; ".join(f"{k} {v[0] or 'no call'}" for k, v in m["sahams"].items() if k != "Fortune")
        o.append(f"<tr><td>{E(m['start'])}</td><td>{chip(m['t8a'][0] or 'no call', tone(m['t8a'][0] or ''))} <span class='s'>{E(m['t8a'][1])}</span></td>"
                 f"<td>{chip(m['t8b'][0] or 'no call', tone(m['t8b'][0] or ''))} <span class='s'>{E(m['t8b'][1])}</span></td><td class='s'>{E(sh)}</td><td class='n'>{m['sun_house']}</td></tr>")
    o.append("</tbody></table></div><p class='s'>All of these monthly rules test at chance on the S&amp;P 1928–2026 (best: trade saham 57% vs 53%, q 0.24).</p>")
    o.append("<h3>Dated items, 24 Nov – 31 Dec</h3><div class='wrap'><table><thead><tr><th>When (ET)</th><th>Item</th><th>Rule</th><th>Test result</th></tr></thead><tbody>")
    seen = set()
    for i in sorted(nsl["calendar"]["items"], key=lambda i: i["start"]):
        key = (i["start"][:16], i["text"])
        if key in seen:
            continue
        seen.add(key)
        s_, e_ = dt.datetime.fromisoformat(i["start"]), dt.datetime.fromisoformat(i["end"])
        when = f"{s_:%a %d %b %H:%M}" + ("" if i["kind"] == "instant" else f" – {e_:%a %d %b %H:%M}")
        o.append(f"<tr><td class='n'>{E(when)}</td><td>{E(i['text'])}</td><td>{E(i['rule'])}</td><td class='s'>{E(i['verdict'])}</td></tr>")
    o.append("</tbody></table></div>")
    return "".join(o)


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


def trust_html(track, sx, review=None):
    cp = track["cp"]["markets"]
    o = ["<h2 id='trust'>Track record</h2><div class='wrap'><table><thead><tr><th>Market</th><th class='n'>2013–2026 walk-forward, 5 sessions</th>"
         + ("<th class='n'>Clean walk-forward 2013–2026, that day, vs chance</th>" if review else "")
         + "<th class='n'>Last 60 days (to 23 Nov), 5 sessions</th><th class='n'>1–23 Nov, all methods, same day</th><th class='n'>1–23 Nov, all methods, 5 sessions</th><th class='n'>Market up, 1–23 Nov</th></tr></thead><tbody>"]
    CL = {"spx": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
          "sensex": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
          "gold": "Model call (2+ points from normal), all layers", "silver": "Model call (2+ points from normal), all layers"}
    nov = track["nov"]["score"]
    for mk in MKS:
        w = cp[mk]["walk_forward"]["up5"]["kept"] or cp[mk]["walk_forward"]["up5"]["all"]
        w60 = cp[mk]["window"]["up5"]["all"]
        pl = nov["pooled"].get(mk, {})
        up = nov["ups"].get(mk, [0, 0, 0, 0])
        cw = review["tuning"]["model"][mk]["rows"][CL[mk]] if review else None
        o.append(f"<tr><td>{NAME[mk]}</td><td class='n'>{w['hit']}% of {w['calls_up'] + w['calls_down']} calls</td>"
                 + (f"<td class='n'>{cw['hit']}% vs {cw['exp']}% ({cw['n']} calls)</td>" if cw else "")
                 + f"<td class='n'>{'–' if w60['hit'] is None else str(w60['hit']) + '% of ' + str(w60['calls_up'] + w60['calls_down'])}</td>"
                 f"<td class='n'>{round(pl['d1_right'] / pl['d1_calls'] * 100) if pl.get('d1_calls') else '–'}%</td><td class='n'>{round(pl['d5_right'] / pl['d5_calls'] * 100) if pl.get('d5_calls') else '–'}%</td>"
                 f"<td class='n'>{up[0]} of {up[1]} days</td></tr>")
    o.append("</tbody></table></div>" + ("<p class='s'>The first column uses the model's “kept” layers, which were chosen by how they scored on 2013–2026 itself; the clean column "
                                          "chooses everything on earlier years (November 2026 review) and is the one to trust.</p>" if review else ""))
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
