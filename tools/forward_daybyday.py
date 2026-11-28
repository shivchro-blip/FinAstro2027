"""Day by day, from a start date to an end date: every transit, every rule and every analysis we have, in one page.

    python tools/forward_daybyday.py [START] [END]        # default: 2026-11-24 to 2026-12-31 (US Eastern dates)

For a past range (e.g. 2026-11-01 2026-11-23) the combined model is fitted only on data before START, the tables'
labels before they were published are rebuilt with the same rules, and every method is scored against the markets
(share of bullish / bearish readings matched by the same-day move and by the next 5 sessions; big days).

For each day:
  * the sky: positions of all twelve bodies (sign, degree, nakshatra-pada, retrograde, dignity, combustion), the
    panchang, and every change during the day (tools/sky_changes.py: ingresses, nakshatra / pada / navamsa changes,
    tithi, karana, yoga, lunations, stations, combustion, whole-sign aspects beginning and ending, exact degree aspects);
  * every catalogue rule (gold, silver and general-market sets) active, with its 26-year record and status;
  * every calendar-layer row (S&P, Nifty/Sensex, gold, silver) with the calendar rule's record;
  * the four signal tables, the big-move watch windows, the outlook items, the agreement windows, the fast-trigger
    picks, the robust volatility factors and Model v1.0 (gold);
  * gochara, Chandra bala and Tara bala for the USA and NYSE charts (the dasha blocks are switched off by USE_DASHA:
    dashas were tested and parked, user 24 Nov 2026);
  * Solar return (the NYSE monthly solar-return astrologer): forecasts covering the day, transit rules active, and the Mars-Jupiter-node lead;
  * the combined probability (tools/combined_probability.py) for each market: up that day, up over the next
    5 sessions, a big day - from all layers and from the kept layers, fitted on 2000 - 23 Nov 2026.
Writes build/pdfref/daybyday_<start>_to_<end>_ET.{html,json}. Market prices and astrology only.
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import html
import json
import pathlib
import subprocess
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load, robust_vol, table_rows  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
FIT_END = dt.date(2026, 11, 23)
MKS = ("spx", "sensex", "gold", "silver")
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}
_US = {dt.date(2026, 11, 26): "Thanksgiving", dt.date(2026, 12, 25): "Christmas",
       dt.date(2027, 1, 1): "New Year's Day", dt.date(2027, 1, 18): "Martin Luther King Jr. Day",
       dt.date(2027, 2, 15): "Presidents' Day", dt.date(2027, 3, 26): "Good Friday"}   # no ^GSPC / GC=F / SI=F bar on past Presidents' Days or Good Fridays
CLOSED = {"spx": dict(_US),             # COMEX has no settlement on these days either (no GC=F / SI=F bar on past MLK and New Year days)
          "gold": dict(_US),
          "silver": dict(_US),
          "sensex": {dt.date(2026, 11, 10): "Diwali Balipratipada", dt.date(2026, 11, 24): "Guru Nanak Jayanti", dt.date(2026, 12, 25): "Christmas",
                     dt.date(2027, 1, 26): "Republic Day", dt.date(2027, 3, 26): "Good Friday",
                     dt.date(2027, 4, 14): "Dr. Ambedkar Jayanti"}}   # fixed date; no ^BSESN bar on any weekday 14 Apr since 2015
# BSE's 2027 list is not out yet: only holidays with certain dates are assumed (Republic Day; Good Friday, no ^BSESN bar on any of
# the last six); lunar-calendar holidays such as Holi are not (their BSE dates shift by a day between calendars)
EARLY = {dt.date(2026, 11, 27): "US early close (13:00 ET)", dt.date(2026, 12, 24): "US early close (13:00 ET)"}
GOOD = ("Strongest", "Supported", "Consistent")
USE_DASHA = False            # dashas parked (user, 24 Nov 2026): tested in dasha_transits.py / dasha_combinations.py, no S&P edge
MINOR = ("pada change", "navamsa change", "tithi", "karana", "yoga")


def et_day(iso):
    return dt.datetime.fromisoformat(iso).astimezone(ET).date()


# ------------------------------------------------------------------ rules (catalogue, calendar)
def catalogue(a, b):
    """Active catalogue rules per day (same logic as tools/day_report.py, collected once for the range)."""
    from finastro.sky import Sky
    from finastro.pdfref.detect import Ctx
    from finastro.pdfref.engine import Grid, utc
    B = load(ROOT / "tools" / "backtest_gold.py", "bt")
    grid = Grid(utc(a.year - 1, 6, 1), utc(b.year + 1, 6, 30))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in (a.year - 1, a.year, a.year + 1)
            if (ROOT / "build" / f"astronomy_{y}.json").exists()]
    evs = []
    for metal in ("gold", "silver", "general"):
        if metal == "general":
            B.M.METAL = "general"
            B.M.EXCLUDE["general"] = set()
            B.M.EXTRA["general"] = []
            B.METAL = "general"
        else:
            B.configure_metal(metal)
        B.P0 = dt.datetime.combine(a - dt.timedelta(days=7), dt.time(0), ET)
        B.P1 = dt.datetime.combine(b + dt.timedelta(days=1), dt.time(0), ET)
        for e in B.collect(ctxs):
            if e["tone"] in ("Bullish", "Bearish", "Mixed", "Neutral"):
                evs.append((metal, e))
    DR = load(ROOT / "tools" / "day_report.py", "drp")
    rec = DR.records()
    per = collections.defaultdict(list)
    d = a
    while d <= b:
        d0 = dt.datetime.combine(d, dt.time(0), ET)
        d1 = d0 + dt.timedelta(days=1)
        seen = set()
        for metal, e in evs:
            if e["day"] is not None:
                ok, kind = e["day"] == d, "day rule"
            elif e["end"] and (e["end"] - e["start"]).days >= 1:
                ok, kind = e["start"] < d1 and e["end"] >= d0, "window"
            else:
                t = e["start"].astimezone(ET)
                ok, kind = (d0 - dt.timedelta(days=6) <= t < d1), ("instant today" if t >= d0 else f"instant {t:%d %b} (5-session horizon)")
            if not ok:
                continue
            k = (metal, e["rule_id"], e["tone"], kind)
            if k in seen:
                continue
            seen.add(k)
            r = dict(set=metal, rule_id=e["rule_id"], title=e["title"], tone=e["tone"], kind=kind, refs="; ".join(e["refs"]),
                     span=(e["start"].astimezone(ET).strftime("%d %b %H:%M") if e["start"] else str(e["day"])) + (f" – {e['end'].astimezone(ET):%d %b %H:%M}" if e["end"] else ""),
                     record={})
            if metal in ("gold", "silver"):
                r["record"][metal] = rec.get((metal, e["rule_id"]))
            else:
                for mk in ("spx", "sensex"):
                    r["record"][mk] = rec.get((mk, e["rule_id"])) or rec.get((mk, f"{e['rule_id']}::{e['tone']}"))
            per[d].append(r)
        d += dt.timedelta(days=1)
    return per


def calendar(a, b):
    rows = []
    for y in range(a.year, b.year + 1):
        f = OUT / "backtest" / "calendar_verdicts" / f"{y}.json.gz"
        if not f.exists():
            subprocess.run([sys.executable, "tools/calendar_rules_backtest.py", "--gen", str(y)], cwd=ROOT, check=True)
        rows += json.load(gzip.open(f, "rt", encoding="utf-8"))
    cb = json.load(open(OUT / "calendar_rules_backtest_2000-2026_ET.json"))
    mk = {"SPX": "spx", "NIFTY": "sensex", "GC": "gold", "SI": "silver"}
    rec = {}
    for x in cb["rules"]:
        for m in mk.values():
            r = x.get(m)
            if not r:
                continue
            if r["kind"] == "direction" and r["worked"] + r["failed"]:
                rec[(x["rule_id"], m)] = (f"{r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%), p {r['p_value']}", r.get("status", ""))
            elif r["kind"] == "volatility" and r.get("n_episodes"):
                rec[(x["rule_id"], m)] = (f"big day in {r['big']} of {r['n_episodes']} episodes vs {r['big_exp']} expected", r.get("status", ""))
    per = collections.defaultdict(list)
    for r in rows:
        d = dt.date.fromisoformat(r["date"])
        if a <= d <= b and r["instrument"] in mk:
            m = mk[r["instrument"]]
            t, s = rec.get((r["rule_id"], m), ("–", ""))
            per[d].append(dict(rule_id=r["rule_id"], market=m, verdict=r["verdict"] or "condition only", provenance=r["provenance"], record=t, status=s))
    return per


# ------------------------------------------------------------------ the other analyses
def windows_on(d):
    out = []
    o = json.load(open(OUT / "gold_outlook_2026-11-22_to_2027-12-31_ET.json"))
    for it in o["items"]:
        if it["frm"] <= str(d) <= it["to"]:
            out.append(dict(src=f"outlook ({it['metal']})", text=f"{it['kind']}: {it['title']} – lean {it['lean']}; {it['evidence']} ({it['weight']})"))
    for metal in ("gold", "silver"):
        f = OUT / f"{metal}_forward_2026-11-20_to_2027-12-31_ET.json"
        if f.exists():
            j = json.load(open(f))
            for w in j["best_windows"]:
                if et_day(w["start"]) <= d <= et_day(w["end"]):
                    out.append(dict(src=f"best rule window ({metal})", text=f"{w['title']} – {w['tone']}; {w['hist']}"))
            for w in j["agreement"]:
                if w["frm"] <= str(d) <= w["to"] and (w["up"] or w["down"]):
                    out.append(dict(src=f"agreement stretch ({metal})", text=f"up: {', '.join(w['up']) or '–'}; down: {', '.join(w['down']) or '–'}"))
        f = OUT / f"{metal}_fast_triggers_2026-11-22_to_2027-12-31_ET.json"
        if f.exists():
            j = json.load(open(f))
            for x in j["days"]:
                if x["date"] == str(d):
                    trg = ", ".join(t if isinstance(t, str) else t.get("factor", str(t)) for t in x.get("triggers", []))
                    out.append(dict(src=f"fast-trigger day ({metal})", text=f"{x['item']} – lean {x['window_lean']}; triggers: {trg or ', '.join(x['fast'])}"))
    return out


def author_rules(d):
    """Solar return transit rules, evaluated as tools/author_forecasts.py tests them (19:00 UT)."""
    fl_s = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    jd = swe.julday(d.year, d.month, d.day, 19)
    B = {"Sun": swe.SUN, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Rahu": swe.MEAN_NODE, "Uranus": swe.URANUS}
    x = {b: swe.calc_ut(jd, k, fl_s)[0][0] % 360 for b, k in B.items()}
    x["Ketu"] = (x["Rahu"] + 180) % 360
    mars_spd = swe.calc_ut(jd, swe.MARS, fl_s)[0][3]
    mer_t = swe.calc_ut(jd, swe.MERCURY, swe.FLG_SWIEPH)[0][0] % 360

    def sep(a, b):
        return abs((a - b + 180) % 360 - 180)
    conds = {"Sun square Mars (within 3°) – Solar return: bearish": abs(sep(x["Sun"], x["Mars"]) - 90) < 3,
             "Sun square Mars with Mars-Ketu within 8° – Solar return: bearish": abs(sep(x["Sun"], x["Mars"]) - 90) < 3 and sep(x["Mars"], x["Ketu"]) < 8,
             "Mars conjunct Ketu (within 5°) – Solar return: disruption": sep(x["Mars"], x["Ketu"]) < 5,
             "Jupiter sextile Venus (within 2°) – Solar return: bullish": abs(sep(x["Jupiter"], x["Venus"]) - 60) < 2,
             "Mars square Uranus (within 3°) – Solar return: volatility": abs(sep(x["Mars"], x["Uranus"]) - 90) < 3,
             "Mars retrograde": mars_spd < 0,
             "Mercury in Pisces, tropical – Solar return: unfavourable": int(mer_t // 30) == 11,
             "Mercury in Pisces, sidereal": int(x["Mercury"] // 30) == 11}
    detail = f"Sun–Mars {sep(x['Sun'], x['Mars']):.1f}°, Mars–Ketu {sep(x['Mars'], x['Ketu']):.1f}°, Jupiter–Venus {sep(x['Jupiter'], x['Venus']):.1f}°, Mars–Uranus {sep(x['Mars'], x['Uranus']):.1f}°"
    return [k for k, v in conds.items() if v], detail


def mars_jupiter_node(p):
    s = {b: int(p[b][0] // 30) for b in ("Mars", "Jupiter", "Rahu", "Ketu")}
    if s["Mars"] == s["Jupiter"] and s["Mars"] in (s["Rahu"], s["Ketu"]):
        return "Rahu" if s["Mars"] == s["Rahu"] else "Ketu"
    return None


# ------------------------------------------------------------------ main
def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 24)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2026, 12, 31)
    res = build(a, b)
    stem = f"daybyday_{a}_to_{b}_ET"
    json.dump(res, open(OUT / f"{stem}.json", "w"), indent=1, default=str)
    (OUT / f"{stem}.html").write_text(page(res), encoding="utf-8")
    print("wrote", stem)


def build(a, b):
    """Every layer for every day a..b (also used by tools/calendar_2026.py)."""
    fit_end = min(FIT_END, a - dt.timedelta(days=1))           # past ranges: weights from before the range only
    CP = load(ROOT / "tools" / "combined_probability.py", "cpm")
    DT = CP.DT
    DR = load(ROOT / "tools" / "day_report.py", "drp2")
    from finastro.pdfref import bs41_model as M

    skyf = OUT / f"sky_changes_{a}_to_{b}_ET.json"
    if not skyf.exists():
        subprocess.run([sys.executable, "tools/sky_changes.py", str(a), str(b)], cwd=ROOT, check=True)
    sky_ev = collections.defaultdict(list)
    seen = set()
    for x in json.load(open(skyf))["events"]:
        k = (x["kind"], x["text"], x["utc"][:16])
        if k not in seen:
            seen.add(k)
            sky_ev[et_day(x["utc"])].append(x)

    print("catalogue rules ...")
    cat = catalogue(a, b)
    cal = calendar(a, b)
    vol = robust_vol(a, b)
    V = load(ROOT / "tools" / "validate_external_model.py", "vem2")
    vol_names = {mk: {} for mk in V.ROBUST}
    for mk, fs in V.ROBUST.items():
        d = a
        while d <= b:
            vol_names[mk][d] = [n for n, f in fs.items() if f(d)]
            d += dt.timedelta(days=1)

    print("combined probability model ...")
    data = CP.build(min(b, FIT_END))
    cj = json.load(open(OUT / "combined_probability_60d_ET.json"))
    models = {}
    for mk in MKS:
        layers = CP.LAYERS[mk]
        models[mk] = {}
        for t in CP.TARGETS:
            tr = [r for r in data[mk] if r["d"] <= fit_end and (t != "up5" or (r["end5"] and r["end5"] <= fit_end))]
            kept = cj["markets"][mk]["kept"][t]
            models[mk][t] = (CP.fit(tr, layers, t), CP.fit(tr, kept, t) if kept else None)
    actual = {mk: {r["d"]: r for r in data[mk]} for mk in MKS}
    pub = {mk: table_rows(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json") for mk in ("gold", "silver")}
    for mk in ("spx", "sensex"):
        pub[mk] = table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", mk)
    pub_from = {"gold": dt.date(2026, 11, 22), "silver": dt.date(2026, 11, 22), "spx": dt.date(2026, 11, 23), "sensex": dt.date(2026, 11, 23)}
    lab = {}                                                   # before the tables were published: the same rules, rebuilt
    for mk in ("gold", "silver"):
        h = json.load(gzip.open(OUT / "backtest" / f"{mk}_label_history.json.gz", "rt", encoding="utf-8"))
        lab[mk] = {dt.date.fromisoformat(k): tuple(v) for k, v in h["in_sample"].items()}
    mh = CP.market_history(min(b, dt.date(2026, 11, 22)))
    lab.update(mh)
    for mk in MKS:
        lab[mk] = {**{d: v for d, v in lab[mk].items() if d < pub_from[mk]}, **pub[mk]}
    charts = {n: (DT.CHARTS[n], CP.natal(DT.CHARTS[n])) for n in ("USA", "NYSE")}
    seq = {n: {lv: DT.sequence(DT.CHARTS[n], lv, dt.datetime.combine(a, dt.time(0), ET), dt.datetime.combine(b + dt.timedelta(days=1), dt.time(0), ET))
               for lv in (1, 2, 3, 4)} for n in charts}
    AF = load(ROOT / "tools" / "author_forecasts.py", "afm")
    DC = load(ROOT / "tools" / "dasha_combinations.py", "dcm") if USE_DASHA else None
    dnat = {n: DC.natal(n) for n in charts} if USE_DASHA else {}
    dctest = {}
    if USE_DASHA and (OUT / "dasha_combinations_ET.json").exists():
        for t in json.load(open(OUT / "dasha_combinations_ET.json"))["tests"]:
            if t["level"] == "Prana" and "chain" in t["group"]:
                dctest[(t["chart"], "hurts" if "hurts" in t["group"] else "helps")] = t
    atests = json.load(open(OUT / "author_forecasts_ET.json"))["tests"]
    nyse = json.load(open(OUT / "nyse_usa_charts_ET.json"))
    ts = json.load(open(OUT / "trigger_study_2000-2026_ET.json"))
    mjn_hist = ts["mars_jupiter_node"]
    falls15 = sum(1 for e in mjn_hist if e["worst"] is not None and e["worst"] <= -15)

    days = []
    d = a
    while d <= b:
        print(d)
        noon = dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET)
        pos, pan = DR.positions(d)
        p = CP.sky(d)
        r1 = M.evaluate(d)
        sb = {k: v["ratio"] for k, v in r1["shadbala"].items()}
        ved = CP.vedic_states(d, p, sb, charts)
        dash = {n: dict(lords=[], changes=[], state=None, gochara=ved[f"{n} gochara"], chandra=ved[f"{n} chandra"], tara=ved[f"{n} tara"]) for n in charts}
        for n, (ch, nat) in (charts.items() if USE_DASHA else ()):
            run = DT.dasha_at(ch, noon, 5)
            lords = []
            for lvl, (lo, s, e) in zip(DT.LEVELS, run):
                ts_ = DT.transit_state(lo, ch, noon)
                lords.append(dict(level=lvl, lord=lo, frm=f"{s.astimezone(ET):%d %b %Y}", to=f"{e.astimezone(ET):%d %b %Y}",
                                  transit=f"{ts_['sign']} {ts_['deg']}°, {ts_['nak']}, house {ts_['house_asc']}/{ts_['house_moon']}" + (f"; {', '.join(ts_['notes'])}" if ts_["notes"] else ""),
                                  score=CP.lord_score(lo, p, nat, sb) if lvl in ("Antardasha", "Pratyantar", "Sookshma") else None))
            changes = [f"{DT.LEVELS[lv]} → {path} at {s.astimezone(ET):%H:%M ET}" for lv in (1, 2, 3, 4) for path, s, e in seq[n][lv]
                       if s.astimezone(ET).date() == d]
            dash[n] = dict(lords=lords, changes=changes, state=ved[f"{n} dasha"], gochara=ved[f"{n} gochara"], chandra=ved[f"{n} chandra"], tara=ved[f"{n} tara"])
        dch = {}
        for n in (charts if USE_DASHA else ()):
            cc = DC.chain(n, dt.datetime(d.year, d.month, d.day, 12, 30, tzinfo=ET).astimezone(UTC), dnat[n])
            sc_ = DC.chain_score(cc)
            dch[n] = dict(score=sc_, reading="hurts" if sc_ <= -3 else "helps" if sc_ >= 3 else "mixed",
                          levels=[dict(level=c["level"], lord=c["lord"], parent=c["parent"], total=c["total"], verdict=c["verdict"],
                                       to=c["to"].astimezone(ET).strftime("%d %b %H:%M"),
                                       why=[f"{t} ({'+' if v > 0 else '−'})" for k, (t, v) in c["factors"].items() if v]) for c in cc])
        arules, adetail = author_rules(d)
        aforecasts = []
        for f in AF.FORECASTS:
            if f["kind"] == "range" and f["start"] <= str(d) <= f["end"]:
                aforecasts.append(f"{f['period']}: {f['text']}")
            elif f["kind"] == "days" and str(d) in f["days"]:
                aforecasts.append(f"{f['period']}: {f['text']} → this day: {f['days'][str(d)]}")
            elif f["kind"] == "path":
                for c0, c1, lean, txt in f["checkpoints"]:
                    if c0 <= str(d) < c1:
                        aforecasts.append(f"{f['period']}: {txt}")
        mjn = mars_jupiter_node(p)
        sig, watch = DR.table_signals(d)
        for mk in MKS:
            if d < pub_from[mk]:
                L = lab[mk].get(d)
                sig[NAME[mk]] = [dict(sig=L[0] if L and L[0] else "No signal", st=(L[1] or "") if L and L[0] else "",
                                      why="rebuilt with the table's rules (the table was published on " + f"{pub_from[mk]:%d %b})")]
        weekday = d.weekday() < 5
        prob = {}
        for mk in MKS:
            if not weekday or d in CLOSED[mk]:
                continue
            st = {"table": CP.tbl_state(lab[mk].get(d))}
            if mk == "gold":
                st["v1"] = CP.v1_state(r1["bias"])
            if mk in ("spx", "sensex"):
                st["bigmove"] = "on" if d in vol.get(mk, set()) else "off"
            if mk == "spx":
                st.update(ved)
            r = dict(st=st)
            prob[mk] = dict(st=st, all={t: round(CP.predict(models[mk][t][0], r) * 100, 1) for t in CP.TARGETS},
                            kept={t: round(CP.predict(models[mk][t][1], r) * 100, 1) if models[mk][t][1] else None for t in CP.TARGETS},
                            base={t: round(models[mk][t][0]["base"] * 100, 1) for t in CP.TARGETS})
            ac = actual[mk].get(d)
            if ac:
                prob[mk]["actual"] = dict(r1=round(ac["r1"], 2), r5=None if ac["r5"] is None or (ac["end5"] and ac["end5"] > FIT_END) else round(ac["r5"], 2), big=ac["big"])
        rules = cat.get(d, [])
        tally = {}
        for mk in MKS:
            sets = ("general",) if mk in ("spx", "sensex") else (mk,)
            good = [r for r in rules if r["set"] in sets and r["record"].get(mk) and r["record"][mk]["status"] in GOOD and r["tone"] in ("Bullish", "Bearish")]
            tally[mk] = dict(bull=sorted({r["title"] for r in good if r["tone"] == "Bullish"}), bear=sorted({r["title"] for r in good if r["tone"] == "Bearish"}))
        days.append(dict(date=str(d), weekday=d.strftime("%a"), closed={mk: CLOSED[mk].get(d) for mk in MKS if CLOSED[mk].get(d)}, early=EARLY.get(d),
                         positions=pos, panchang=pan, changes=sky_ev.get(d, []), rules=rules, tally=tally, calendar=cal.get(d, []),
                         signals=sig, watch=watch, windows=windows_on(d), vol={mk: vol_names[mk][d] for mk in vol_names},
                         v1=dict(S=r1["S"], V=r1["V"], bias=r1["bias"], confidence=r1["confidence"], agree=r1["agree"], against=r1["against"]),
                         shadbala=sb, dasha=dash, chain=dch, jupven=ved["jup-ven"], author=dict(rules=arules, detail=adetail, forecasts=aforecasts),
                         mjn=mjn, prob=prob))
        d += dt.timedelta(days=1)
    sr = [dict(period=f["period"], status=f["score"]["status"], detail=f["score"].get("detail", "")) for f in json.load(open(OUT / "author_forecasts_ET.json"))["forecasts"]]
    res = dict(start=str(a), end=str(b), fit_end=str(fit_end), days=days, sr_scores=sr, dctest={f"{k[0]} {k[1]}": v for k, v in dctest.items()}, atests=atests, solar_month=nyse["forecast"],
               mjn=dict(episodes=len(mjn_hist), falls15=falls15, base=ts["mjn_base"]), kept={mk: cj["markets"][mk]["kept"] for mk in MKS},
               skill={mk: {t: cj["markets"][mk]["walk_forward"][t] for t in CP.TARGETS} for mk in MKS})
    if any("actual" in pr for x in days for pr in x["prob"].values()):
        res["score"] = score(days, AF)
    return res


# ------------------------------------------------------------------ scoring a past range
def score(days, AF):
    """Share of directional calls that matched the move (same day; next 5 sessions from the previous close)."""
    tally = collections.defaultdict(lambda: {"d1": [0, 0], "d5": [0, 0]})
    fdays = {d: v for f in AF.FORECASTS if f["kind"] == "days" for d, v in f["days"].items()}

    def add(m, mk, h, call, ac):
        r = ac["r1"] if h == "d1" else ac["r5"]
        if not call or r is None or r == 0:
            return
        c = tally[(m, mk)][h]
        c[1] += 1
        c[0] += (r > 0) == (call > 0)

    def both(m, mk, call, ac):
        add(m, mk, "d1", call, ac)
        add(m, mk, "d5", call, ac)
    big = collections.defaultdict(lambda: dict(pbig=[], poth=[], watch=[0, 0], other=[0, 0], vol=[0, 0], novol=[0, 0]))
    for x in days:
        d = x["date"]
        for mk, pr in x["prob"].items():
            ac = pr.get("actual")
            if not ac:
                continue
            sg = x["signals"][NAME[mk]][0]["sig"]
            both("Signal table", mk, 1 if sg == "Bullish" else -1 if sg == "Bearish" else 0, ac)
            for name, key in (("Combined probability, all layers", "all"), ("Combined probability, kept layers", "kept")):
                for h, t in (("d1", "up1"), ("d5", "up5")):
                    v, b = pr[key][t], pr["base"][t]
                    if v is not None:
                        add(name, mk, h, 1 if v >= b + 2 else -1 if v <= b - 2 else 0, ac)
            for h, t in (("d1", "up1"), ("d5", "up5")):
                add("Combined lean, every day (above / below base)", mk, h, 1 if pr["all"][t] > pr["base"][t] else -1, ac)
            tl = x["tally"][mk]
            both("Supported catalogue rules (net bullish - bearish)", mk, len(tl["bull"]) - len(tl["bear"]), ac)
            cal = sum(1 if c["verdict"].startswith("Bullish") else -1 if c["verdict"].startswith("Bearish") else 0 for c in x["calendar"] if c["market"] == mk)
            both("Calendar-layer verdicts (net)", mk, cal, ac)
            if mk == "gold":
                bias = x["v1"]["bias"]
                both("Model v1.0 (Ch.41 + Shadbala)", mk, 1 if "bullish" in bias else -1 if "bearish" in bias else 0, ac)
            if mk == "spx":
                st = pr["st"]
                for n in ("USA", "NYSE"):
                    if USE_DASHA:
                        both(f"{n} dasha condition", mk, {"strong": 1, "afflicted": -1}.get(st[f"{n} dasha"], 0), ac)
                    both(f"{n} gochara", mk, {"favourable": 1, "adverse": -1}.get(st[f"{n} gochara"], 0), ac)
                    both(f"{n} Chandra bala", mk, 1 if st[f"{n} chandra"] == "good" else -1, ac)
                    both(f"{n} Tara bala", mk, {"good": 1, "bad": -1}.get(st[f"{n} tara"], 0), ac)
                both("Solar return: day-by-day forecasts", mk, {"up": 1, "down": -1}.get(fdays.get(d), 0), ac)
                both("Solar return: month view (bearish)", mk, -1, ac)
                ar = x["author"]["rules"]
                both("Solar return: Jupiter sextile Venus (bullish)", mk, 1 if any(r.startswith("Jupiter sextile Venus") for r in ar) else 0, ac)
                both("Solar return: Sun square Mars (bearish)", mk, -1 if any(r.startswith("Sun square Mars (") for r in ar) else 0, ac)
                both("Mars-Jupiter-node lead (bearish)", mk, -1 if x["mjn"] else 0, ac)
                for n in (("USA", "NYSE") if USE_DASHA else ()):
                    both(f"{n} dasha chain, classical reading (Pratyantar + Sookshma + Prana)", mk, {"hurts": -1, "helps": 1}.get(x["chain"][n]["reading"], 0), ac)
            B = big[mk]
            (B["pbig"] if ac["big"] else B["poth"]).append(pr["all"]["big"])
            w = any(v["market"] == mk for v in x["watch"])
            B["watch" if w else "other"][0] += ac["big"]
            B["watch" if w else "other"][1] += 1
            vv = bool(x["vol"].get(mk))
            B["vol" if vv else "novol"][0] += ac["big"]
            B["vol" if vv else "novol"][1] += 1
    rows = []
    for (m, mk), v in tally.items():
        rows.append(dict(method=m, market=mk, d1_right=v["d1"][0], d1_calls=v["d1"][1], d5_right=v["d5"][0], d5_calls=v["d5"][1]))
    pooled = collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        if r["method"].startswith("Combined lean"):
            continue
        for k in (r["market"], "all"):
            q = pooled[k]
            q[0] += r["d1_right"]
            q[1] += r["d1_calls"]
            q[2] += r["d5_right"]
            q[3] += r["d5_calls"]
    ups = {}
    for x in days:
        for mk, pr in x["prob"].items():
            ac = pr.get("actual")
            if ac:
                u = ups.setdefault(mk, [0, 0, 0, 0])
                u[0] += ac["r1"] > 0
                u[1] += 1
                if ac["r5"] is not None:
                    u[2] += ac["r5"] > 0
                    u[3] += 1
    bigs = {mk: dict(p_big=round(sum(B["pbig"]) / len(B["pbig"]), 1) if B["pbig"] else None, p_other=round(sum(B["poth"]) / len(B["poth"]), 1) if B["poth"] else None,
                     n_big=len(B["pbig"]), watch=B["watch"], other=B["other"], vol=B["vol"], novol=B["novol"]) for mk, B in big.items()}
    return dict(rows=rows, pooled={k: dict(d1_right=v[0], d1_calls=v[1], d5_right=v[2], d5_calls=v[3]) for k, v in pooled.items()}, ups=ups, big=bigs)


# ------------------------------------------------------------------ page
E = html.escape


def tone_cls(t):
    return "g" if t in ("Bullish", "up") else "r" if t in ("Bearish", "down") else ""


def sigcell(sig):
    s = sig[0]
    return f"<span class='{tone_cls(s['sig'])}'>{E(s['sig'])}{' ' + E(s['st']) if s['st'] and s['st'] != '–' else ''}</span>"


def pcell(pr, t):
    v, b = pr["all"][t], pr["base"][t]
    cls = "" if t == "big" else "g" if v >= b + 2 else "r" if v <= b - 2 else ""
    return f"<span class='{cls}'>{v:.0f}%</span>"


def key_changes(ch):
    out = []
    for x in ch:
        if x["kind"] in MINOR or x["kind"].startswith("rule ") or x["text"].startswith("Moon") or "Moon" in x["text"].split(" ")[0]:
            continue
        if x["kind"] in ("aspect begins", "aspect ends") and "Moon" in x["text"]:
            continue
        t = f"{x['text']} ({x['et'].split(' ')[3]})"
        if t not in out:
            out.append(t)
    return out


def score_html(res):
    sc = res["score"]

    def pc(r, n):
        return "–" if not n else f"{round(r / n * 100)}% <span class='s'>({r}/{n})</span>"
    o = ["<h2>How it did: share of calls that matched the market</h2>",
         "<p class='s'>A call is a bullish or bearish reading; it is right when the market moved that way the same day (close to close) or over the next "
         "5 sessions (from the previous close). Days with no reading are not counted. Compare each figure with how often the market rose in the period: "
         f"a method that always says 'down' scores the down share. The combined model's weights were fitted on data up to {res['fit_end']} only.</p>",
         "<div class='wrap'><table><thead><tr><th>Market</th><th>Up days</th><th>Up over 5 sessions</th><th>All methods pooled: same day</th><th>All methods pooled: 5 sessions</th></tr></thead><tbody>"]
    for mk in MKS + ("all",):
        u = sc["ups"].get(mk)
        p = sc["pooled"].get(mk)
        if not p:
            continue
        o.append(f"<tr><td><b>{NAME.get(mk, 'All markets')}</b></td><td class='n'>{pc(u[0], u[1]) if u else ''}</td><td class='n'>{pc(u[2], u[3]) if u else ''}</td>"
                 f"<td class='n'>{pc(p['d1_right'], p['d1_calls'])}</td><td class='n'>{pc(p['d5_right'], p['d5_calls'])}</td></tr>")
    o.append("</tbody></table></div><div class='wrap'><table><thead><tr><th>Method</th>" + "".join(f"<th>{NAME[mk]}<br><span class='s'>same day · 5 sessions</span></th>" for mk in MKS) + "</tr></thead><tbody>")
    methods = list(dict.fromkeys(r["method"] for r in sc["rows"]))
    by = {(r["method"], r["market"]): r for r in sc["rows"]}
    for m in methods:
        cells = ""
        for mk in MKS:
            r = by.get((m, mk))
            cells += f"<td class='n'>{pc(r['d1_right'], r['d1_calls'])} · {pc(r['d5_right'], r['d5_calls'])}</td>" if r and (r["d1_calls"] or r["d5_calls"]) else "<td class='n s'>–</td>"
        o.append(f"<tr><td>{E(m)}</td>{cells}</tr>")
    o.append("</tbody></table></div><h3>Big days</h3><div class='wrap'><table><thead><tr><th>Market</th><th>Big days</th><th>Avg P(big) on big days</th><th>Avg P(big) other days</th>"
             "<th>Big days in watch windows</th><th>Big days outside</th><th>On robust-factor days</th><th>Other days</th></tr></thead><tbody>")
    for mk, B in sc["big"].items():
        o.append(f"<tr><td>{NAME[mk]}</td><td class='n'>{B['n_big']}</td><td class='n'>{pct(B['p_big'])}</td><td class='n'>{pct(B['p_other'])}</td>"
                 f"<td class='n'>{B['watch'][0]} of {B['watch'][1]}</td><td class='n'>{B['other'][0]} of {B['other'][1]}</td><td class='n'>{B['vol'][0]} of {B['vol'][1]}</td><td class='n'>{B['novol'][0]} of {B['novol'][1]}</td></tr>")
    o.append("</tbody></table></div>")
    return "".join(o)


def pct(x):
    return "–" if x is None else f"{x}%"


def page(res):
    css = """:root{color-scheme:light} body{margin:0;padding:16px;background:#fff;color:#1f2328;font:13.5px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
h1{font-size:20px;margin:0 0 6px} h2{font-size:17px;margin:24px 0 8px;border-bottom:1px solid #d0d7de;padding-bottom:4px} h3{font-size:14px;margin:14px 0 4px}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:4px 0 10px} th,td{border-bottom:1px solid #d0d7de;padding:4px 7px;text-align:left;vertical-align:top}
th{background:#f6f8fa;position:sticky;top:0} td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .s{font-size:12px;color:#57606a}
.g{color:#1e7b3a;font-weight:600} .r{color:#b42318;font-weight:600} .w{background:#f6f8fa;color:#57606a} .x{background:#fff6e0}
details.day{border:1px solid #d0d7de;border-radius:6px;margin:8px 0;padding:4px 10px} details.day>summary{cursor:pointer;font-weight:600;padding:4px 0}
details details{margin:4px 0} details details>summary{cursor:pointer;color:#0969da} .pill{display:inline-block;padding:0 6px;border-radius:9px;background:#eef1f4;margin:1px 2px;font-size:12px}
.ov td{font-size:12.5px}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Day by Day</title><style>{css}</style></head><body>",
         f"<h1>Day by day, {res['start']} – {res['end']}: transits, every rule and every analysis{' – checked against the markets' if res.get('score') else ''}</h1>",
         "<p class='s'>US Eastern dates; sidereal Lahiri, mean node, whole-sign drishti. Probabilities come from the combined model "
         f"(all layers, fitted on 2000 – {res['fit_end']}); green / red = 2+ points above / below the market's base rate. Over 2013–2026 that model "
         "was right 51–55% of the time: read the probabilities as leanings, not certainties. Rules count as <b>supported</b> when their 26-year status "
         "is Strongest, Supported or Consistent. Market prices and astrology only.</p>"]
    if res.get("score"):
        o.append(score_html(res))
    # standing items
    sm = res["solar_month"]
    o.append("<h2>Standing through the period</h2><ul>")
    o.append(f"<li><b>Solar return, NYSE month {E(sm['month'])}:</b> {E(sm['text'])} (from {sm['start_level']}).</li>")
    if res.get("sr_scores"):
        o.append("<li><b>Solar return scorecard so far:</b> " + "; ".join(f"{E(f['period'])}: {E(f['status'])}" + (f" ({E(f['detail'])})" if f['detail'] else "") for f in res["sr_scores"]) + "</li>")
    m = res["mjn"]
    mj = [x["date"] for x in res["days"] if x["mjn"]]
    if mj:
        o.append(f"<li><b>Mars and Jupiter with a node</b> (our lead from the trigger study): active {mj[0]} – {mj[-1]}. Since 1928, {m['falls15']} of {m['episodes']} "
                 f"such episodes saw a fall of 15% or more, against {m['base']['worst15']}% of random stretches of the same length. A lead, not proven.</li>")
    d0 = res["days"][0]["dasha"]
    for n in (("USA", "NYSE") if USE_DASHA else ()):
        L = d0[n]["lords"]
        o.append(f"<li><b>{n} dashas at the start:</b> " + " / ".join(f"{x['lord']} ({x['level']}, to {x['to']})" for x in L[:3]) + ".</li>")
    long_rules = collections.Counter()
    for x in res["days"]:
        for r in x["rules"]:
            if r["kind"] == "window":
                long_rules[(r["set"], r["title"], r["tone"], r["span"])] += 1
    full = [k for k, v in long_rules.items() if v == len(res["days"])]
    if full:
        o.append("<li><b>Rules active on every day of the period:</b> " + "; ".join(f"{E(t)} ({s}, {tn})" for s, t, tn, _ in sorted(full)) + ".</li>")
    o.append("</ul>")
    # overview
    o.append("<h2>Overview</h2><div class='wrap'><table class='ov'><thead><tr><th>Date</th><th>Moon / tithi</th><th>Main sky changes</th>")
    for mk in MKS:
        o.append(f"<th>{NAME[mk]}<br><span class='s'>table · P(up) · P(5d up) · P(big)</span></th>")
    o.append("<th>Dashas, Solar return, watch</th></tr></thead><tbody>")
    for x in res["days"]:
        we = x["weekday"] in ("Sat", "Sun")
        cls = "w" if we else "x" if x["closed"] or x["early"] else ""
        pan = x["panchang"]
        cells = ""
        for mk in MKS:
            pr = x["prob"].get(mk)
            tl = x["tally"][mk]
            sg = sigcell(x["signals"][NAME[mk]]) if NAME[mk] in x["signals"] else ""
            if pr:
                ac = pr.get("actual")
                act = ""
                if ac:
                    act = f"<br><b>actual</b> <span class='{'g' if ac['r1'] > 0 else 'r'}'>{ac['r1']:+.2f}%</span>" + (f" · 5d <span class='{'g' if ac['r5'] > 0 else 'r'}'>{ac['r5']:+.2f}%</span>" if ac["r5"] is not None else "")
                cells += f"<td>{sg}<br>{pcell(pr, 'up1')} · {pcell(pr, 'up5')} · {pcell(pr, 'big')}<br><span class='s'>rules +{len(tl['bull'])} / −{len(tl['bear'])}</span>{act}</td>"
            else:
                cells += f"<td class='s'>{'closed: ' + x['closed'][mk] if mk in x['closed'] else 'weekend'}<br>{sg}</td>"
        notes = []
        for n in (("USA", "NYSE") if USE_DASHA else ()):
            notes += [f"{n}: {c}" for c in x["dasha"][n]["changes"] if not c.startswith("Prana")]
            if x["chain"][n]["reading"] != "mixed":
                notes.append(f"{n} dasha chain {x['chain'][n]['score']:+d} ({x['chain'][n]['reading']})")
        notes += [f"Solar return: {f.split(': ', 1)[1]}" for f in x["author"]["forecasts"] if "this day" in f]
        notes += [f"Solar return rule: {r.split(' – ')[0]}" for r in x["author"]["rules"] if "retrograde" not in r and "Pisces" not in r]
        for w in x["watch"]:
            t = f"Watch ({w['market']}): " + w["factor"].replace("Rule: ", "").replace("Event: ", "").split(" [")[0]
            if t not in notes:
                notes.append(t)
        if x["early"]:
            notes.append(x["early"])
        kc = key_changes(x["changes"])
        o.append(f"<tr class='{cls}'><td><a href='#d{x['date']}'>{x['weekday']} {x['date'][5:]}</a></td><td class='s'>{E(pan['moon_nakshatra'])}<br>tithi {E(str(pan['tithi']))}</td>"
                 f"<td class='s'>{E('; '.join(kc[:6]))}{' …' if len(kc) > 6 else ''}</td>{cells}<td class='s'>{E('; '.join(notes[:6]))}</td></tr>")
    o.append("</tbody></table></div>")
    # details
    o.append("<h2>Each day in full</h2>")
    for x in res["days"]:
        pan = x["panchang"]
        head = f"{x['weekday']} {x['date']} — Moon in {pan['moon_nakshatra']}, {pan['tithi']} ({pan['paksha']})"
        if x["closed"]:
            head += " — closed: " + ", ".join(f"{NAME[k]} ({v})" for k, v in x["closed"].items())
        o.append(f"<details class='day' id='d{x['date']}'><summary>{E(head)}</summary>")
        # probabilities
        if x["prob"]:
            o.append("<h3>Combined probability (all layers; kept layers in brackets)</h3><div class='wrap'><table><thead><tr><th>Market</th><th>Table</th><th>Up that day</th>"
                     "<th>Up over 5 sessions</th><th>Big day</th><th>Base (up / 5d / big)</th><th>Layer states</th></tr></thead><tbody>")
            for mk, pr in x["prob"].items():
                def c(t, pr=pr):
                    k = pr["kept"][t]
                    return f"{pcell(pr, t)}" + (f" <span class='s'>({k:.0f}%)</span>" if k is not None else "")
                st = "; ".join(f"{k}: {v}" for k, v in pr["st"].items())
                o.append(f"<tr><td>{NAME[mk]}</td><td>{sigcell(x['signals'][NAME[mk]])}</td><td class='n'>{c('up1')}</td><td class='n'>{c('up5')}</td><td class='n'>{c('big')}</td>"
                         f"<td class='n s'>{pr['base']['up1']:.0f} / {pr['base']['up5']:.0f} / {pr['base']['big']:.0f}%</td><td class='s'>{E(st)}</td></tr>")
            o.append("</tbody></table></div>")
        # signals
        o.append("<h3>Signal tables</h3><ul>")
        for nm, ss in x["signals"].items():
            for s in ss:
                o.append(f"<li><b>{E(nm)}:</b> <span class='{tone_cls(s['sig'])}'>{E(s['sig'])} {E(s['st'] or '')}</span> <span class='s'>{E(s['why'])}</span></li>")
        o.append("</ul>")
        # sky
        rows = "".join(f"<tr><td>{E(p['planet'])}</td><td>{E(p['sign'])} {E(p['deg'])}</td><td>{E(p['nakshatra'])}</td><td>{'R' if p['retro'] else ''}</td>"
                       f"<td>{E(p['dignity'])}</td><td>{'combust' if p['combust'] else ''}</td><td class='n'>{p['speed']}</td></tr>" for p in x["positions"])
        grp = "; ".join(f"{k}: {', '.join(v)}" for k, v in pan["groups"].items())
        o.append(f"<details><summary>Sky at 12:00 ET and panchang</summary><p class='s'>{E(pan['weekday'])} (lord {E(pan['day_lord'])}); {E(str(pan['tithi']))}, {E(pan['paksha'])}; "
                 f"Moon nakshatra {E(pan['moon_nakshatra'])}; yoga {E(str(pan['yoga']))}; together: {E(grp) or '–'}</p><div class='wrap'><table><thead><tr><th>Body</th>"
                 f"<th>Position</th><th>Nakshatra-pada</th><th>R</th><th>Dignity</th><th>Combust</th><th>Speed °/day</th></tr></thead><tbody>{rows}</tbody></table></div></details>")
        ch = "".join(f"<tr><td class='n'>{E(c['et'].split(' ', 3)[3])}</td><td class='s'>{E(c['ist'])}</td><td>{E(c['kind'])}</td><td>{E(c['text'])}</td><td class='s'>{E(c['pos'])}</td></tr>"
                     for c in x["changes"])
        o.append(f"<details><summary>All planetary changes during the day ({len(x['changes'])})</summary><div class='wrap'><table><thead><tr><th>ET</th><th>IST</th><th>Kind</th>"
                 f"<th>Change</th><th>Position / status</th></tr></thead><tbody>{ch}</tbody></table></div></details>")
        if not USE_DASHA:
            o.append("<p class='s'><b>Classical layers (S&amp;P):</b> " + E("; ".join(f"{n}: gochara {dd['gochara']}, Chandra bala {dd['chandra']}, Tara bala {dd['tara']}" for n, dd in x["dasha"].items())) + "</p>")
        # dashas (parked)
        drow = ""
        for n, dd in x["dasha"].items():
            for L in dd["lords"]:
                drow += (f"<tr><td>{n}</td><td>{L['level']}</td><td><b>{L['lord']}</b></td><td class='s'>{L['frm']} – {L['to']}</td><td class='s'>{E(L['transit'])}</td>"
                         f"<td class='n'>{'' if L['score'] is None else format(L['score'], '+d')}</td></tr>")
        dsum = "; ".join(f"{n}: dasha {dd['state']}, gochara {dd['gochara']}, Chandra bala {dd['chandra']}, Tara bala {dd['tara']}" + (f"; changes: {', '.join(dd['changes'])}" if dd["changes"] else "")
                         for n, dd in x["dasha"].items())
        crow = ""
        for n, cdat in x["chain"].items():
            for L in cdat["levels"]:
                cl = "r" if L["verdict"] == "hurts" else "g" if L["verdict"] == "helps" else ""
                crow += (f"<tr><td>{n}</td><td>{L['level']}</td><td><b>{L['lord']}</b> under {L['parent']} <span class='s'>(to {L['to']})</span></td>"
                         f"<td class='n {cl}'>{L['total']:+d}</td><td class='{cl}'>{L['verdict']}</td><td class='s'>{E('; '.join(L['why']))}</td></tr>")
        hist = "; ".join(f"{k}: S&P {v['mean']:+.1f}%/yr vs {v['base']:+.1f}% on all days (t {v['t']})" for k, v in res.get("dctest", {}).items())
        csum = "; ".join(f"{n}: chain score {c['score']:+d} → {c['reading']}" for n, c in x["chain"].items())
        if USE_DASHA:
            o.append(f"<details><summary>Dasha chain read classically: {E(csum)}</summary><p class='s'>Each lord judged against its parent lord, the natal chart and its transit "
                 f"(tools/dasha_combinations.py); the chain score adds the Pratyantar, Sookshma and Prana scores (hurts ≤ −3, helps ≥ +3). Since 1928: {E(hist) or 'run tools/dasha_combinations.py'}.</p>"
                 f"<div class='wrap'><table><thead><tr><th>Chart</th><th>Level</th><th>Lord</th><th>Score</th><th>Reading</th><th>Factors that count</th></tr></thead><tbody>{crow}</tbody></table></div></details>")
        if USE_DASHA:
            o.append(f"<details><summary>USA and NYSE dashas and the transits of their lords</summary><p class='s'>{E(dsum)}</p><div class='wrap'><table><thead><tr><th>Chart</th><th>Level</th>"
                 f"<th>Lord</th><th>Period</th><th>Transit (house from ascendant / Moon)</th><th>Condition score</th></tr></thead><tbody>{drow}</tbody></table></div></details>")
        # rules
        for setname, label in (("general", "General-market rules (S&P, Sensex)"), ("gold", "Gold rules"), ("silver", "Silver rules")):
            rs = [r for r in x["rules"] if r["set"] == setname]
            if not rs:
                continue
            rs.sort(key=lambda r: (not any(v and v["status"] in GOOD for v in r["record"].values()), r["tone"], r["title"]))
            body = ""
            for r in rs:
                recs = "; ".join(f"{k}: {v['text']} [{v['status']}]" for k, v in r["record"].items() if v) or "no record"
                good = any(v and v["status"] in GOOD for v in r["record"].values())
                body += (f"<tr><td class='{tone_cls(r['tone'])}'>{E(r['tone'])}</td><td>{'<b>' if good else ''}{E(r['title'])}{'</b>' if good else ''}</td><td class='s'>{E(r['kind'])}<br>{E(r['span'])}</td>"
                         f"<td class='s'>{E(recs)}</td><td class='s'>{E(r['refs'])}</td></tr>")
            ngood = sum(1 for r in rs if any(v and v["status"] in GOOD for v in r["record"].values()))
            o.append(f"<details><summary>{label}: {len(rs)} active, {ngood} with a supported record</summary><div class='wrap'><table><thead><tr><th>Tone</th><th>Rule</th><th>When</th>"
                     f"<th>26-year record [status]</th><th>Source</th></tr></thead><tbody>{body}</tbody></table></div></details>")
        if x["calendar"]:
            body = "".join(f"<tr><td>{NAME[c['market']]}</td><td>{E(c['verdict'])}</td><td class='s'>{E(c['provenance'] or c['rule_id'])}</td><td class='s'>{E(c['record'])} {E(c['status'])}</td></tr>"
                           for c in x["calendar"])
            o.append(f"<details><summary>Calendar-layer rows: {len(x['calendar'])}</summary><div class='wrap'><table><thead><tr><th>Market</th><th>Verdict</th><th>Rule</th>"
                     f"<th>Record 2000–2026</th></tr></thead><tbody>{body}</tbody></table></div></details>")
        # other analyses
        other = []
        for w in x["watch"]:
            other.append(f"<li><b>Big-move watch ({E(w['market'])}):</b> {E(w['factor'])}{' – exact ' + E(w['exact']) if w['exact'] else ''}</li>")
        for mk, vs in x["vol"].items():
            if vs:
                other.append(f"<li><b>Robust big-move factor ({NAME[mk]}):</b> {E(', '.join(vs))}</li>")
        for w in x["windows"]:
            other.append(f"<li><b>{E(w['src'])}:</b> {E(w['text'])}</li>")
        v1 = x["v1"]
        other.append(f"<li><b>Model v1.0 (gold, Ch.41 + Shadbala):</b> {E(v1['bias'])} (S {v1['S']}, V {v1['V']}, confidence {E(v1['confidence'])}); for: {E(', '.join(v1['agree']))}; against: {E(', '.join(v1['against']))}. "
                     f"Shadbala ratios: {E(', '.join(f'{k} {v:.2f}' for k, v in x['shadbala'].items()))}</li>")
        if x["mjn"]:
            other.append(f"<li><b>Mars and Jupiter with {x['mjn']}:</b> the crash lead is active.</li>")
        if x["author"]["forecasts"]:
            other.append("<li><b>Solar return forecasts covering the day:</b> " + E(" | ".join(x["author"]["forecasts"])) + "</li>")
        ar = []
        for r in x["author"]["rules"]:
            t = res["atests"].get(r)
            ar.append(r + (f" (since 1928: next 5 sessions up {t['up5']}% vs {t['exp5']}%, p {t['p5']}; big days {t['big']} vs {t['exp_big']})" if t else ""))
        other.append(f"<li><b>Solar return transit rules active:</b> {E('; '.join(ar) or 'none')}. <span class='s'>{E(x['author']['detail'])}</span></li>")
        o.append("<h3>Other analyses</h3><ul>" + "".join(other) + "</ul></details>")
    o.append("<p class='s'>Sources: catalogue rules (TA, KD, the 2026 document, the user's notes, Brihat Samhita), the 2027/2026 calendar layer, the backtests and tables "
             "in PROJECT_KNOWLEDGE.md, Model v1.0, the USA/NYSE charts, the Solar return material (NYSE monthly solar returns), and classical gochara / Chandra bala / Tara bala "
             "(included at the user's request). Dasha levels below Antardasha depend on birth times known to the hour or not at all.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
