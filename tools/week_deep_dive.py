"""Deep dive for one week: every sky event backtested, every active rule with its record.

    python tools/week_deep_dive.py [nov] [dec] [jan] [feb] [mar] [apr] [may] [jun] [jul] [--reuse-days]   # default: every week of Nov and Dec 2026, Jan to Jul 2027
                                                                              # (November uses history to 31 Oct 2026 only)

For each day of the week (December 2026 from the 2026 calendar JSON; January 2027 built with forward_daybyday.build and
the same extra layers, shown in the 2027 calendar):
  * every sky event (exact degree aspects, sign and nakshatra entries, tithi and yoga changes, Bhadra, lunations) is
    turned into its event class ("Moon-Saturn exact opposition", "Mercury enters Scorpio", "Krishna Dashami begins")
    and every occurrence of that class from 20 Nov 2000 to 20 Nov 2026 is scored on the S&P 500, Sensex, gold and
    silver (PROJECT_KNOWLEDGE section 6 timing: entry = last close before the event, next session and 5 sessions,
    |move| < 0.5% FLAT, base = same-length moves in the same Nov-Nov year). An event class has no stated direction,
    so the test is two-sided (up share vs the base, p = 2 x the smaller one-sided p); big days = |1-session move| above
    that year's 90th percentile (10% expected). Benjamini-Hochberg q over every class x market x horizon in the week.
  * every catalogue rule active that day (TA, KD, the 2026 document, user notes, Brihat Samhita) with its 26-year
    record and status, as already scored by the rule backtests;
  * the day's combined-model probabilities, table labels, Solar return call and new-source items.
Writes build/pdfref/deep_dive_{start}_to_{end}_ET.json (read by tools/calendar_2026.py; HTML pages other than the
two calendars are not kept, user 27 Nov 2026).
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import re
import statistics
import sys

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import backtest_market as BM  # noqa: E402
import new_sources_test as T  # noqa: E402

OUT = ROOT / "build" / "pdfref"
UTC, ET = T.UTC, T.ET
H0, H1 = dt.datetime(2000, 11, 1, tzinfo=UTC), dt.datetime(2026, 11, 25, tzinfo=UTC)
EXTRA = {"Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO}
ANG = {"conjunction": 0, "sextile": 60, "square": 90, "trine": 120, "opposition": 180}
TITHI = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi",
         "Dwadashi", "Trayodashi", "Chaturdashi"]
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
         "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
         "Brahma", "Indra", "Vaidhriti"]
PHASE = {"New Moon": 0, "First Quarter": 90, "Full Moon": 180, "Last Quarter": 270}


def lon(x, b, sid=True):
    if b in T.BODY:
        return T.pos(x, b, sid)[0]
    if b in EXTRA:
        r = swe.calc_ut(x, EXTRA[b], swe.FLG_SWIEPH | (swe.FLG_SIDEREAL if sid else 0))[0][0]
        return r % 360
    n = swe.calc_ut(x, swe.MEAN_NODE, swe.FLG_SWIEPH | (swe.FLG_SIDEREAL if sid else 0))[0][0] % 360
    return n if b == "Rahu" else (n + 180) % 360


def step_for(*bodies):
    return 0.2 if "Moon" in bodies else 0.5 if any(b in ("Sun", "Mercury", "Venus", "Mars") for b in bodies) else 2.0


def aspect_times(a, b, ang):
    offs = [0.0] if ang == 0 else [180.0] if ang == 180 else [float(ang), -float(ang)]
    out, st = [], step_for(a, b)
    for o in offs:
        f = lambda y, o=o: T.wrap(lon(y, a, False) - lon(y, b, False) - o)
        x, end = T.jd(H0), T.jd(H1)
        fx = f(x)
        while x < end:
            y = x + st
            fy = f(y)
            if (fx < 0) != (fy < 0) and abs(fx) < 30 and abs(fy) < 30:
                out.append(T.from_jd(T.solve(f, x, y, 40)))
            x, fx = y, fy
    return sorted(out)


def speed(x, b):
    code = T.BODY.get(b) or EXTRA.get(b)
    return swe.calc_ut(x, code, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3]


L_COMB = {"Mercury", "Venus", "Mars", "Jupiter", "Saturn"}


def combust_times(b, kind="combust"):
    """Combustion starts (or rises) by the project's classical kalamsha method (finastro/combustion.py, as the calendar)."""
    from finastro import combustion as CB
    key = f"_comb_{b}"
    if key not in _series:
        _series[key] = CB.find_events(b, H0.date(), H1.date())
    return [e.instant for e in _series[key] if e.kind == kind]


def sun_apsis_times(which):
    """The Sun at perihelion (distance minimum, early January) or aphelion (maximum, early July)."""
    out, x, end = [], T.jd(H0), T.jd(H1)
    f = lambda y: swe.calc_ut(y, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][5]
    fx = f(x)
    while x < end:
        y = x + 1.0
        fy = f(y)
        if (fx < 0 <= fy and which == "perihelion") or (fx >= 0 > fy and which == "aphelion"):
            out.append(T.from_jd(T.solve(f, x, y, 40)))
        x, fx = y, fy
    return out


def eclipse_start(which, x):
    """(start, maximum) of the next eclipse after jd x. The calendar (build_2027.py) marks an eclipse at the start of its window:
    a solar eclipse at its global first contact (tret[2]), a lunar eclipse at its penumbral first contact (tret[6])."""
    fn = swe.sol_eclipse_when_glob if which == "solar" else swe.lun_eclipse_when
    tret = fn(x, swe.FLG_SWIEPH)[1]
    st = tret[2] if which == "solar" else tret[6]
    return (st or tret[0]), tret[0]


def eclipse_times(which):
    """Every solar (global) or lunar (penumbral included) eclipse, at its start, as the calendar counts them."""
    out, x = [], T.jd(H0)
    while True:
        st, peak = eclipse_start(which, x)
        if peak > T.jd(H1):
            return out
        out.append(T.from_jd(st))
        x = peak + 1


def overtake_times(fast, slow):
    """Instants the signed longitude speed of `fast` rises through that of `slow` (ephem.relative_speed_crossings)."""
    f = lambda y: speed(y, fast) - speed(y, slow)
    out, x, end = [], T.jd(H0), T.jd(H1)
    fx = f(x)
    while x < end:
        y = x + 0.25
        fy = f(y)
        if fx < 0 <= fy:
            out.append(T.from_jd(T.solve(f, x, y, 40)))
        x, fx = y, fy
    return out


def speed_levels():
    """The calibrated Fast/Normal speed levels (config/conventions.yaml speed_classes; as build_2027.py emits speed_crossing records)."""
    import yaml
    conf = yaml.safe_load(open(ROOT / "config" / "conventions.yaml"))["speed_classes"]
    return {b: v["threshold"] for b, v in conf.items() if isinstance(v, dict) and v.get("threshold") is not None}


SPEED_LEVEL = speed_levels()


def fast_times(body, fam):
    """Instants the planet's speed crosses its Fast level going up (fast_start) or down (fast_end), ephem.speed_crossings."""
    from finastro import ephem
    return [inst for inst, kind, family, lvl in ephem.speed_crossings(body, H0, H1, SPEED_LEVEL[body]) if kind == "threshold" and family == f"motion/{fam}"]


def station_times(b, direction):
    """Instants the planet's longitude speed changes sign (direct: - to +, retrograde: + to -)."""
    out, x, end = [], T.jd(H0), T.jd(H1)
    f = lambda y: speed(y, b)
    fx = f(x)
    while x < end:
        y = x + 1.0
        fy = f(y)
        if (fx < 0 <= fy and direction == "direct") or (fx >= 0 > fy and direction == "retrograde"):
            out.append(T.from_jd(T.solve(f, x, y, 40)))
        x, fx = y, fy
    return out


def apsis_times(which):
    """Moon perigee (distance minimum) or apogee (maximum)."""
    out, x, end = [], T.jd(H0), T.jd(H1)
    f = lambda y: swe.calc_ut(y, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][5]        # distance speed
    fx = f(x)
    while x < end:
        y = x + 0.25
        fy = f(y)
        if (fx < 0 <= fy and which == "perigee") or (fx >= 0 > fy and which == "apogee"):
            out.append(T.from_jd(T.solve(f, x, y, 40)))
        x, fx = y, fy
    return out


_series = {}


def entries(key, fn, step, value):
    """Start times of every stay where fn(jd) == value, 2000-2026 (one pass per key, cached)."""
    if key not in _series:
        _series[key] = T.spans(fn, H0, H1, step)
    return [s for s, e, v in _series[key] if v == value and s > H0 + dt.timedelta(days=1)]


def tithi_fn(y):
    return int(((lon(y, "Moon", False) - lon(y, "Sun", False)) % 360) // 12)


def yoga_fn(y):
    return int(((lon(y, "Moon") + lon(y, "Sun")) % 360) // (360 / 27))


def karana_fn(y):
    i = int(((lon(y, "Moon", False) - lon(y, "Sun", False)) % 360) // 6)
    return "Vishti" if 1 <= i <= 56 and (i - 1) % 7 == 6 else "other"


def classify(ch):
    """Calendar change -> (class key, label, instance-finder) or None."""
    k, t = ch["kind"], ch["text"]
    if k in ("exact degree aspect", "exact aspect"):
        m = re.match(r"(\w+)–(\w+) exact (\w+)", t)
        if m and m.group(3) in ANG:
            a, b, nm = m.groups()
            return (f"asp|{a}|{b}|{nm}", f"{a}–{b} exact {nm}", lambda a=a, b=b, nm=nm: aspect_times(a, b, ANG[nm]))
    if k == "sign change":
        m = re.match(r"(\w+) enters (\w+) \(", t)
        if m:
            p, s = m.groups()
            si = T.SIGNS.index(s)
            return (f"sign|{p}|{s}", f"{p} enters {s}", lambda p=p, si=si: entries(f"sign|{p}", lambda y, p=p: int(lon(y, p) // 30), step_for(p), si))
    if k == "nakshatra change":
        m = re.match(r"(\w+) enters ([\w ]+?) nakshatra", t)
        if m:
            p, n = m.groups()
            ni = T.NAKS.index(n) if n in T.NAKS else None
            if ni is not None:
                return (f"nak|{p}|{n}", f"{p} enters {n}", lambda p=p, ni=ni: entries(f"nak|{p}", lambda y, p=p: int(lon(y, p) // (360 / 27)), step_for(p), ni))
    if k == "tithi":
        m = re.search(r"→ (\w+) \((\w+) paksha\)", t)
        if m:
            nm, pk = m.groups()
            idx = 29 if nm == "Amavasya" else 14 if nm == "Purnima" else TITHI.index(nm) + (15 if pk == "Krishna" else 0)
            return (f"tithi|{idx}", f"{nm if nm in ('Amavasya', 'Purnima') else pk + ' ' + nm} begins", lambda idx=idx: entries("tithi", tithi_fn, 0.1, idx))
    if k == "yoga":
        m = re.search(r"→ (\w+)", t)
        nm_ = {"Variyana": "Variyan"}.get(m.group(1), m.group(1)) if m else None
        if nm_ in YOGAS:
            yi = YOGAS.index(nm_)
            return (f"yoga|{yi}", f"Yoga {nm_} begins", lambda yi=yi: entries("yoga", yoga_fn, 0.1, yi))
    if k == "karana" and "Bhadra (Vishti) begins" in t:
        return ("bhadra", "Bhadra (Vishti) begins", lambda: entries("karana", karana_fn, 0.05, "Vishti"))
    if k == "station":
        m = re.match(r"(\w+) stations (direct|retrograde)", t)
        if m:
            p, dr = m.groups()
            return (f"station|{p}|{dr}", f"{p} stations {dr}", lambda p=p, dr=dr: station_times(p, dr))
    if k == "combustion":
        m = re.match(r"(\w+) becomes combust", t)
        if m and m.group(1) in L_COMB:
            p = m.group(1)
            return (f"comb|{p}", f"{p} becomes combust", lambda p=p: combust_times(p))
        m = re.match(r"(\w+) rises from combustion", t)
        if m and m.group(1) in L_COMB:
            p = m.group(1)
            return (f"rise|{p}", f"{p} rises from combustion", lambda p=p: combust_times(p, "rise"))
    if k == "apsis":
        m = re.search(r"Sun \(orbit/(perihelion|aphelion)\)", t)
        if m:
            return (f"sunapsis|{m.group(1)}", f"Sun at {m.group(1)}", lambda w=m.group(1): sun_apsis_times(w))
        m = re.search(r"(perigee|apogee)", t)
        if m:
            return (f"apsis|{m.group(1)}", f"Moon at {m.group(1)}", lambda w=m.group(1): apsis_times(w))
    if k == "eclipse":
        m = re.match(r"(Solar|Lunar) eclipse", t)
        if m:
            w = m.group(1).lower()
            return (f"eclipse|{w}", f"{m.group(1)} eclipse begins" + (" (penumbral contact)" if w == "lunar" else ""), lambda w=w: eclipse_times(w))
    if k == "speed crossing":
        m = re.search(r"(\w+) \(motion/(fast_start|fast_end)\)", t)
        if m and m.group(1) in SPEED_LEVEL:
            b, fam = m.group(1), m.group(2)
            return (f"fast|{b}|{fam}", f"{b} {'enters' if fam == 'fast_start' else 'leaves'} fast motion",
                    lambda b=b, fam=fam: fast_times(b, fam))
    if k == "speed overtake":
        m = re.search(r"motion/(\w+)_overtakes_(\w+)", t)
        if m:
            fa, sl = m.group(1).title(), m.group(2).title()
            return (f"overtake|{fa}|{sl}", f"{fa} overtakes {sl} in speed", lambda fa=fa, sl=sl: overtake_times(fa, sl))
    if k == "lunation":
        for nm, ang in PHASE.items():
            if t.startswith(nm):
                return (f"lun|{ang}", nm, lambda ang=ang: aspect_times("Moon", "Sun", ang) if ang in (0, 180) else
                        [t_ for t_ in aspect_times("Moon", "Sun", 90) if ((lon(T.jd(t_), "Moon", False) - lon(T.jd(t_), "Sun", False)) % 360 > 180) == (ang == 270)])
    return None


def score_class(times, MK):
    out = {}
    for k, mk in MK.items():
        rec = {}
        for h in (1, 5):
            evs = [T.ev(t, "Bullish", None, h=h) for t in times]
            rows = [(e, s) for e in evs if (s := mk.score(e))]
            up = BM.aggregate(rows, mk)
            dn = BM.aggregate([(dict(e, tone="Bearish"), s) for e, s in rows], mk)
            dec = up["worked"] + up["failed"]
            p2 = min(1.0, 2 * min(up["p_value"] or 1, dn["p_value"] or 1)) if dec else None
            rec[f"h{h}"] = dict(n=up["n"], up=up["worked"], down=up["failed"], up_pct=up["hit_rate"], base=up["base_rate"],
                                mean=round(statistics.fmean([s["ret"] for _, s in rows]), 2) if rows else None, p2=round(p2, 4) if p2 is not None else None)
        # big days: |1-session move| above that Nov-Nov year's 90th percentile
        thr, big, tot = {}, 0, 0
        for t in times:
            s = mk.score(T.ev(t, "Bullish", None, h=1))
            if not s or not (mk.p0 <= s["entry"] < mk.p1):
                continue
            y = s["year"]
            if y not in thr:
                mv = sorted(abs(mk.C[i + 1] / mk.C[i] - 1) * 100 for i in range(1, len(mk.D) - 1) if BM.nov_year(mk.D[i]) == y)
                thr[y] = mv[int(len(mv) * 0.9)] if mv else 99
            tot += 1
            big += abs(s["ret"]) > thr[y]
        rec["big"] = dict(n=tot, big=big, pct=round(big / tot * 100) if tot else None, p=round(BM.binom_p(big, tot, 0.10), 4) if tot else None)
        out[k] = rec
    return out


SKIP_KINDS = {"rule starts (general)", "rule ends (general)", "rule starts (gold)", "rule ends (gold)", "rule starts (silver)", "rule ends (silver)",
              "pada change", "navamsa change", "aspect begins", "aspect ends", "karana",
              "neighbour change"}          # a planet's zodiac neighbours change = a Paap Kartari window starts or ends (B116/B117, tested in kartari_test.py)


def week(a, b, all_days, ns_items, MK, cache, context=None):
    days = [x for x in all_days if a.isoformat() <= x["date"] <= b.isoformat()]
    classes, per_day, unclassified = {}, [], []
    for x in days:
        evs = []
        for ch in x["changes"]:
            c = classify(ch)
            if not c:
                if ch["kind"] not in SKIP_KINDS:
                    unclassified.append(f"{x['date']} {ch['kind']}: {ch['text']}")
                continue
            key, label, finder = c
            if key not in cache:
                print("class", label, flush=True)
                times = finder()
                cache[key] = dict(label=label, n_hist=len(times), times=times, stats=score_class(times, MK))
            classes[key] = {k: v for k, v in cache[key].items() if k != "times"}
            classes[key]["stats"] = json.loads(json.dumps(cache[key]["stats"]))     # own copy: q values are per week
            evs.append(dict(et=ch["et"].split(" ", 3)[3], ist=ch["ist"].split(" ", 3)[3], kind=ch["kind"], text=ch["text"], key=key, utc=ch.get("utc")))
        per_day.append((x, evs))
    # BH over every class x market x horizon (two-sided)
    cells = [(c, k, h) for c in classes.values() for k in MK for h in ("h1", "h5") if c["stats"][k][h]["p2"] is not None]
    qs = BM.bh([c["stats"][k][h]["p2"] for c, k, h in cells]) if cells else []
    for (c, k, h), q in zip(cells, qs):
        c["stats"][k][h]["q"] = round(q, 4)
    bcells = [(c, k) for c in classes.values() for k in MK if c["stats"][k]["big"]["p"] is not None]
    for (c, k), q in zip(bcells, BM.bh([c["stats"][k]["big"]["p"] for c, k in bcells]) if bcells else []):
        c["stats"][k]["big"]["q"] = round(q, 4)
    out_days = []
    for x, evs in per_day:
        rules = collections.defaultdict(lambda: collections.Counter())
        notable = collections.defaultdict(list)
        for r in x["rules"]:
            for mk, rec in (r.get("record") or {}).items():
                rec = rec or {}
                st = rec.get("status", "no record")
                rules[mk][st] += 1
                if st in ("Strongest", "Supported", "Consistent"):
                    notable[mk].append(f"{r['title']} [{r['tone']}] {rec['text']} ({st})")
        d = dt.date.fromisoformat(x["date"])
        ns = []
        for i in ns_items:
            s_, e_ = dt.datetime.fromisoformat(i["start"]), dt.datetime.fromisoformat(i["end"])
            if (i["kind"] == "instant" and s_.date() == d) or (i["kind"] != "instant" and s_.date() <= d <= e_.date()):
                ns.append(f"{i['text']} [{i['rule']}: {i['verdict']}]")
        out_days.append(dict(date=x["date"], weekday=x["weekday"], closed=x["closed"], early=x["early"], panchang=x["panchang"], events=evs,
                             signals={k: v[0] for k, v in x["signals"].items()}, prob=x["prob"], tally={k: [len(v["bull"]), len(v["bear"])] for k, v in x["tally"].items()},
                             rules={k: dict(v) for k, v in rules.items()}, notable={k: list(dict.fromkeys(v)) for k, v in notable.items()},
                             solar_return=x["author"], watch=list(dict.fromkeys(f"{w['market']}: {w['factor']}" for w in x["watch"])), new_sources=ns,
                             sr_call=x.get("sr_call"), sr_month=x.get("sr_month"), notes=x.get("notes", [])))
    sig = [(c["label"], k, h, c["stats"][k][h]) for c in classes.values() for k in MK for h in ("h1", "h5") if c["stats"][k][h].get("q", 1) < 0.10]
    nom = [(c["label"], k, h, c["stats"][k][h]) for c in classes.values() for k in MK for h in ("h1", "h5") if (c["stats"][k][h]["p2"] or 1) < 0.05]
    bigsig = [(c["label"], k, c["stats"][k]["big"]) for c in classes.values() for k in MK if c["stats"][k]["big"].get("q", 1) < 0.10]
    res = dict(made=dt.datetime.now(ET).strftime("%Y-%m-%d %H:%M ET"), start=a.isoformat(), end=b.isoformat(), classes=classes, days=out_days,
               unclassified=unclassified, checks=checks(per_day, classes, cache, MK, unclassified), context=context or {},
               n_cells=len(cells), significant=[dict(label=l, market=k, horizon=h, **s) for l, k, h, s in sig],
               nominal=[dict(label=l, market=k, horizon=h, **s) for l, k, h, s in nom],
               big_significant=[dict(label=l, market=k, **s) for l, k, s in bigsig])
    f = OUT / f"deep_dive_{a}_to_{b}_ET.json"
    f.write_text(json.dumps(res, indent=1, default=str))
    print(f"{a}..{b}: {len(classes)} event classes, {len(cells)} tests; q<0.10: {len(sig)}; nominal p<0.05: {len(nom)}; big-day q<0.10: {len(bigsig)}; "
          f"checks {sum(c['ok'] for c in res['checks'])}/{len(res['checks'])}")
    for l, k, h, s_ in nom:
        print("  nominal", l, k, h, s_)
    for l, k, s_ in bigsig:
        print("  big", l, k, s_)
    for c in res["checks"]:
        if not c["ok"]:
            print("  CHECK FAILED", c)
    return res


# ------------------------------------------------------------------ double checks
EXPECT = {"asp_moon_0": (300, 360), "asp_moon_180": (300, 360), "asp_moon_x": (620, 720), "sign_moon": (330, 365), "nak_moon": (330, 365),
          "tithi": (310, 335), "yoga": (360, 385), "bhadra": (2500, 2650), "lun": (310, 335), "apsis": (330, 360), "eclipse": (50, 70)}


def expect_range(key):
    k = key.split("|")
    if k[0] == "asp" and "Moon" in k[1:3] and k[1:3] != ["Moon", "Sun"] and k[1:3] != ["Sun", "Moon"]:
        return EXPECT["asp_moon_0"] if k[3] == "conjunction" else EXPECT["asp_moon_180"] if k[3] == "opposition" else EXPECT["asp_moon_x"]
    if k[0] == "asp" and set(k[1:3]) == {"Sun", "Moon"}:
        return EXPECT["lun"] if k[3] in ("conjunction", "opposition") else (620, 680)
    if k[0] == "sign" and k[1] == "Moon":
        return EXPECT["sign_moon"]
    if k[0] == "nak" and k[1] == "Moon":
        return EXPECT["nak_moon"]
    if k[0] in ("tithi", "yoga", "bhadra", "apsis"):
        return EXPECT[k[0]]
    if k[0] == "sunapsis":
        return (25, 27)
    if k[0] == "eclipse":
        return EXPECT["eclipse"]
    if k[0] == "overtake" and set(k[1:3]) == {"Mercury", "Venus"}:
        return (75, 90)                 # once per Mercury synodic cycle (115.88 d): 26 x 365.25 / 115.88 = 82 each way
    if k[0] in ("comb", "rise") and k[1] == "Mercury":
        return (120, 190)
    if k[0] == "fast":                  # at most once per synodic cycle each way (Mercury 82, Venus 16.3, Mars 12.2 in 26 years);
        return {"Mercury": (55, 85), "Venus": (14, 18), "Mars": (11, 14)}.get(k[1])   # Mercury's peak speed misses its level in some cycles
    if k[0] == "lun":
        return EXPECT["lun"]
    return None


def event_time(e):
    return dt.datetime.fromisoformat(e["utc"]) if e.get("utc") else None


def checks(per_day, classes, cache, MK, unclassified):
    out = []

    def add(name, ok, detail):
        out.append(dict(name=name, ok=bool(ok), detail=detail))
    # 1. every event time re-derived from the ephemeris
    bad, n = [], 0
    for x, evs in per_day:
        for e in evs:
            t = event_time(e)
            if t is None:
                continue
            k = e["key"].split("|")
            y0, y1 = T.jd(t - dt.timedelta(minutes=6)), T.jd(t + dt.timedelta(minutes=6))
            n += 1
            if k[0] == "asp":
                d = min(abs(abs(T.wrap(lon(T.jd(t), k[1], False) - lon(T.jd(t), k[2], False))) - ANG[k[3]]), 360)
                if d > (0.15 if "Moon" in k[1:3] else 0.05):          # the calendar lists Moon aspects to the nearest 10 minutes
                    bad.append(f"{e['text']} off by {d:.2f} deg")
            elif k[0] in ("sign", "nak"):
                w = 30 if k[0] == "sign" else 360 / 27
                tgt = T.SIGNS.index(k[2]) if k[0] == "sign" else T.NAKS.index(k[2])
                before, after = int(lon(y0, k[1]) // w), int(lon(y1, k[1]) // w)
                if not (after == tgt and before != tgt):
                    bad.append(f"{e['text']}: before {before}, after {after}, want {tgt}")
            elif k[0] == "tithi":
                if not (tithi_fn(y1) == int(k[1]) and tithi_fn(y0) != int(k[1])):
                    bad.append(f"{e['text']}: tithi {tithi_fn(y0)}->{tithi_fn(y1)}")
            elif k[0] == "yoga":
                if not (yoga_fn(y1) == int(k[1]) and yoga_fn(y0) != int(k[1])):
                    bad.append(f"{e['text']}: yoga {yoga_fn(y0)}->{yoga_fn(y1)}")
            elif k[0] in ("comb", "rise"):
                from finastro import combustion as CB
                kind_ = "combust" if k[0] == "comb" else "rise"
                ev_ = [c.instant.date() for c in CB.find_events(k[1], t.date() - dt.timedelta(days=3), t.date() + dt.timedelta(days=3)) if c.kind == kind_]
                if t.astimezone(T.IST).date() not in ev_:      # combustion is resolved to the civil day in IST (00:00 IST), as the calendar shows it
                    bad.append(f"{e['text']}: kalamsha method gives {ev_}")
            elif k[0] == "station":
                s0, s1 = speed(T.jd(t - dt.timedelta(hours=12)), k[1]), speed(T.jd(t + dt.timedelta(hours=12)), k[1])
                if not ((s0 < 0 <= s1) if k[2] == "direct" else (s0 >= 0 > s1)):
                    bad.append(f"{e['text']}: speed {s0:.5f} -> {s1:.5f}")
            elif k[0] == "eclipse":
                st, _ = eclipse_start(k[1], T.jd(t - dt.timedelta(days=2)))
                st = T.from_jd(st)
                if abs((st - t).total_seconds()) > 600:
                    bad.append(f"{e['text']}: first contact at {st:%Y-%m-%d %H:%M} UT")
            elif k[0] == "overtake":
                d0 = speed(T.jd(t - dt.timedelta(hours=6)), k[1]) - speed(T.jd(t - dt.timedelta(hours=6)), k[2])
                d1 = speed(T.jd(t + dt.timedelta(hours=6)), k[1]) - speed(T.jd(t + dt.timedelta(hours=6)), k[2])
                if not (d0 < 0 <= d1):
                    bad.append(f"{e['text']}: speed difference {d0:.4f} -> {d1:.4f}")
            elif k[0] == "fast":                # the levels are crossed by the sidereal speed (ephem.position().speed), not the tropical one
                from finastro import ephem
                lv = SPEED_LEVEL[k[1]]
                s0, s1 = ephem.position(t - dt.timedelta(hours=6), k[1]).speed, ephem.position(t + dt.timedelta(hours=6), k[1]).speed
                if not ((s0 < lv <= s1) if k[2] == "fast_start" else (s0 >= lv > s1)):
                    bad.append(f"{e['text']}: speed {s0:.4f} -> {s1:.4f} around level {lv}")
            elif k[0] == "sunapsis":
                g = lambda y: swe.calc_ut(y, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][5]
                a0, a1 = g(T.jd(t - dt.timedelta(hours=12))), g(T.jd(t + dt.timedelta(hours=12)))
                if not ((a0 < 0 <= a1) if k[1] == "perihelion" else (a0 >= 0 > a1)):
                    bad.append(f"{e['text']}: distance speed {a0:.6f} -> {a1:.6f}")
            elif k[0] == "apsis":
                g = lambda y: swe.calc_ut(y, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][5]
                a0, a1 = g(T.jd(t - dt.timedelta(hours=3))), g(T.jd(t + dt.timedelta(hours=3)))
                if not ((a0 < 0 <= a1) if k[1] == "perigee" else (a0 >= 0 > a1)):
                    bad.append(f"{e['text']}: distance speed {a0:.5f} -> {a1:.5f}")
            elif k[0] == "bhadra":
                if not (karana_fn(y1) == "Vishti" and karana_fn(y0) != "Vishti"):
                    bad.append(f"{e['text']}: karana {karana_fn(y0)}->{karana_fn(y1)}")
    add("Every event time re-derived from the ephemeris (±6 min; Moon aspects ±0.15°, eclipse first contacts ±10 min, speed overtakes and fast-motion crossings ±6 h, stations and the Sun's apsides ±12 h, Moon apsides ±3 h, combustion by IST day)", not bad, f"{n} events checked" + ("; " + "; ".join(bad[:5]) if bad else ""))
    # 2. history counts sensible
    off = []
    for key, c in classes.items():
        r = expect_range(key)
        if r and not (r[0] <= c["n_hist"] <= r[1]):
            off.append(f"{c['label']}: {c['n_hist']} (expected {r[0]}-{r[1]})")
    add("Occurrence counts 2000-2026 within the expected range", not off, f"{len(classes)} classes" + ("; " + "; ".join(off[:5]) if off else ""))
    # 3. an independent recount from raw prices for the largest class (S&P, 5 sessions)
    key = max(classes, key=lambda k: classes[k]["n_hist"])
    times = cache[key]["times"]
    mk = MK["spx"]
    up = dn = 0
    for t in times:
        x = t.astimezone(ET)
        sday = x.date() + (dt.timedelta(days=1) if x.time() >= dt.time(16, 0) else dt.timedelta(0))
        i = max(j for j in range(len(mk.D)) if mk.D[j] < sday) if mk.D[0] < sday else None
        if i is None or i + 5 >= len(mk.D) or not (mk.p0 <= mk.D[i] < mk.p1) or sday > mk.p1:
            continue
        r = (mk.C[i + 5] / mk.C[i] - 1) * 100
        up += r > 0.5
        dn += r < -0.5
    st = classes[key]["stats"]["spx"]["h5"]
    add("Independent recount of one result from raw prices", (up, dn) == (st["up"], st["down"]),
        f"{classes[key]['label']} S&P 5 sessions: recount {up} up / {dn} down vs tool {st['up']} / {st['down']}")
    # 4. coverage
    add("Every sky event of the week classified (rule starts/ends, padas, navamsas, whole-sign aspect begin/end and Paap Kartari neighbour changes are covered by the rule records)",
        not unclassified, f"{len(unclassified)} not classified" + ("; " + "; ".join(unclassified[:5]) if unclassified else ""))
    return out


def load_tool(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"wdd_{name}", ROOT / "tools" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def month_days(a, b, nsl):
    """Day data for a range beyond the 2026 calendar (January 2027): the same layers, built with forward_daybyday.build,
    plus the Solar return day call and month reading, Paap Kartari spans, gold notes and the new-source items."""
    cachef = OUT / "backtest" / f"days_{a}_to_{b}.json.gz"
    if "--reuse-days" in sys.argv and cachef.exists():
        import gzip
        c = json.load(gzip.open(cachef, "rt", encoding="utf-8"))
        print("reusing", cachef.name)
        add_notes(c["days"])
        return c["days"], c["items"], c["context"]
    FD = load_tool("forward_daybyday")
    res = FD.build(a, b)
    days = res["days"]
    SRG = load_tool("solar_return_generate")
    _, ms = SRG.NC.backtest("A")
    SRG.START_DATES[:] = [m["start"].astimezone(ET).date() for m in ms]
    atests = json.load(open(OUT / "author_forecasts_ET.json"))["tests"]
    mons = SRG.months(dt.datetime(2026, 10, 1), dt.datetime(b.year, b.month, b.day) + dt.timedelta(days=50))
    srd = {r["d"]: r for r in SRG.daily(a, b, mons, atests)}
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        r = srd.get(d)
        x["sr_call"] = f"{r['call']}: {r['why']}" if r else None
        m = SRG.month_of(mons, d)
        x["sr_month"] = f"Solar month {m['start']:%d %b} – {m['end']:%d %b}: {m['asc']} rising, {m['reading']}" if m else None
    L = load_tool("new_sources_leftover")
    vd = dict(L.VERDICTS)
    for key, prefix in L.RULE_TEST.items():
        mm = [t for t in nsl["daily"] if t["name"].startswith(prefix)]
        if mm:
            vd[key] = "tested: " + mm[0]["verdict"]
    lay = L.calendar_layer(vd, dt.datetime.combine(a, dt.time(5), UTC), dt.datetime.combine(b + dt.timedelta(days=1), dt.time(5), UTC))
    context = dict(months=lay["months"], year=lay["year"], holidays={x["date"]: x["closed"] for x in days if x["closed"]})
    import gzip
    with gzip.open(cachef, "wt", encoding="utf-8") as fh:
        json.dump(dict(days=days, items=lay["items"], context=context), fh, default=str)
    add_notes(days)
    return days, lay["items"], context


def krec(k):
    """Short record of a Paap Kartari rule (kartari_test.py): S&P and Sensex, all windows."""
    parts = []
    for mk, nm in (("spx", "S&P"), ("sensex", "Sensex")):
        r = k["record"].get(mk, {}).get("all")
        if r:
            parts.append(f"{nm} {r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%, p {r['p_value']})")
    return "; ".join(parts)


def add_notes(days):
    """Paap Kartari spans, the gold-Jupiter note and the gold turn-watch markers for each day."""
    kart = json.load(open(OUT / "kartari_test_ET.json"))
    gjc = json.load(open(OUT / "gold_jupiter_crash_ET.json"))
    turns = json.load(open(OUT / "gold_turns_ET.json"))
    GJC_KEYS = ("Jupiter with Rahu or Ketu", "Jupiter–Saturn trine (5/9)", "Jupiter–Saturn opposite (7)", "Saturn aspects Jupiter",
                "Jupiter hemmed by malefics (12th and 2nd)", "Malefic vedha on Jupiter")
    for x in days:
        d = dt.date.fromisoformat(x["date"])
        notes = []
        for k in kart["rules"]:
            if k["key"] in ("b116", "b117"):
                for u in k["upcoming"]:
                    if dt.date.fromisoformat(u["frm_iso"][:10]) <= d <= dt.date.fromisoformat(u["to_iso"][:10]):
                        notes.append(f"{k['title'].split(' (')[0]} ({u['pair']}), {k['tone']} per the 2026 document; record {krec(k)}")
        for key in GJC_KEYS:
            for s0, s1 in gjc["spans"].get(key, []):
                if dt.date.fromisoformat(s0) <= d <= dt.date.fromisoformat(s1):
                    notes.append(f"Gold–Jupiter note: {key} (holds in 69% of months, so not specific to crashes)")
        wk = (d - dt.timedelta(days=d.weekday())).isoformat()
        for w in turns["weeks"]:
            if w["week"] == wk and (w["bottom_hits"] or w["peak_hits"]):
                notes.append("Gold turn-watch markers this week: " + "; ".join([f"bottom: {h}" for h in w["bottom_hits"]] + [f"top: {h}" for h in w["peak_hits"]]))
        x["notes"] = notes


def main():
    cal = json.load(open(OUT / "calendar_2026-11-24_to_2026-12-31_ET.json"))
    nsl = json.load(open(OUT / "new_sources_leftover_ET.json"))
    MK = T.markets()

    def chunks(a, b):
        out = []
        while a <= b:
            out.append((a, min(a + dt.timedelta(days=6), b)))
            a += dt.timedelta(days=7)
        return out
    cache = {}
    want = [w for w in sys.argv[1:] if not w.startswith("--")]
    if not want or "dec" in want:                            # every week from 1 Dec to 31 Dec 2026, from the 2026 calendar
        for a, b in chunks(dt.date(2026, 12, 1), dt.date(2026, 12, 31)):
            week(a, b, cal["days"], nsl["calendar"]["items"], MK, cache)
    for tok, (a, b) in MONTHS_2027.items():                  # 2027 months, built with the same layers
        if not want or tok in want:
            days, items, context = month_days(a, b, nsl)
            for wa, wb in chunks(a, b):
                week(wa, wb, days, items, MK, cache, context)
    if not want or "nov" in want:                            # November 2026, scored afterwards against what markets did
        a, b = dt.date(2026, 11, 1), dt.date(2026, 11, 30)
        MKN = T.markets()
        for mk in MKN.values():                              # history ends 31 Oct 2026: no November occurrence scores itself
            mk.p1 = dt.date(2026, 10, 31)
        days, items, context = month_days(a, b, nsl)
        context["history_end"] = "2026-10-31"
        cache_n = {}
        for wa, wb in chunks(a, b):
            week(wa, wb, days, items, MKN, cache_n, context)


MONTHS_2027 = {"jan": (dt.date(2027, 1, 1), dt.date(2027, 1, 31)), "feb": (dt.date(2027, 2, 1), dt.date(2027, 2, 28)),
               "mar": (dt.date(2027, 3, 1), dt.date(2027, 3, 31)), "apr": (dt.date(2027, 4, 1), dt.date(2027, 4, 30)),
               "may": (dt.date(2027, 5, 1), dt.date(2027, 5, 31)), "jun": (dt.date(2027, 6, 1), dt.date(2027, 6, 30)),
               "jul": (dt.date(2027, 7, 1), dt.date(2027, 7, 31))}

if __name__ == "__main__":
    main()
