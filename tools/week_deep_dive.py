"""Deep dive for one week: every sky event backtested, every active rule with its record.

    python tools/week_deep_dive.py [start] [end]        # default 2026-12-01 2026-12-07

For each day of the week (from the 2026 calendar JSON):
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


def combust_times(b):
    """Combustion starts by the project's classical kalamsha method (finastro/combustion.py, the same as the calendar)."""
    from finastro import combustion as CB
    return [e.instant for e in CB.find_events(b, H0.date(), H1.date()) if e.kind == "combust"]


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
    if k == "apsis":
        m = re.search(r"(perigee|apogee)", t)
        if m:
            return (f"apsis|{m.group(1)}", f"Moon at {m.group(1)}", lambda w=m.group(1): apsis_times(w))
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
              "pada change", "navamsa change", "aspect begins", "aspect ends", "karana"}


def week(a, b, cal, nsl, MK, cache):
    days = [x for x in cal["days"] if a.isoformat() <= x["date"] <= b.isoformat()]
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
        for i in nsl["calendar"]["items"]:
            s_, e_ = dt.datetime.fromisoformat(i["start"]), dt.datetime.fromisoformat(i["end"])
            if (i["kind"] == "instant" and s_.date() == d) or (i["kind"] != "instant" and s_.date() <= d <= e_.date()):
                ns.append(f"{i['text']} [{i['rule']}: {i['verdict']}]")
        out_days.append(dict(date=x["date"], weekday=x["weekday"], closed=x["closed"], early=x["early"], panchang=x["panchang"], events=evs,
                             signals={k: v[0] for k, v in x["signals"].items()}, prob=x["prob"], tally={k: [len(v["bull"]), len(v["bear"])] for k, v in x["tally"].items()},
                             rules={k: dict(v) for k, v in rules.items()}, notable={k: list(dict.fromkeys(v)) for k, v in notable.items()},
                             solar_return=x["author"], watch=list(dict.fromkeys(f"{w['market']}: {w['factor']}" for w in x["watch"])), new_sources=ns))
    sig = [(c["label"], k, h, c["stats"][k][h]) for c in classes.values() for k in MK for h in ("h1", "h5") if c["stats"][k][h].get("q", 1) < 0.10]
    nom = [(c["label"], k, h, c["stats"][k][h]) for c in classes.values() for k in MK for h in ("h1", "h5") if (c["stats"][k][h]["p2"] or 1) < 0.05]
    bigsig = [(c["label"], k, c["stats"][k]["big"]) for c in classes.values() for k in MK if c["stats"][k]["big"].get("q", 1) < 0.10]
    res = dict(made=dt.datetime.now(ET).strftime("%Y-%m-%d %H:%M ET"), start=a.isoformat(), end=b.isoformat(), classes=classes, days=out_days,
               unclassified=unclassified, checks=checks(per_day, classes, cache, MK, unclassified),
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
          "tithi": (310, 335), "yoga": (360, 385), "bhadra": (2500, 2650), "lun": (310, 335), "apsis": (330, 360)}


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
            elif k[0] == "comb":
                from finastro import combustion as CB
                ev_ = [c.instant.date() for c in CB.find_events(k[1], t.date() - dt.timedelta(days=3), t.date() + dt.timedelta(days=3)) if c.kind == "combust"]
                if t.astimezone(T.IST).date() not in ev_:      # combustion is resolved to the civil day in IST (00:00 IST), as the calendar shows it
                    bad.append(f"{e['text']}: kalamsha method gives {ev_}")
            elif k[0] == "station":
                s0, s1 = speed(T.jd(t - dt.timedelta(hours=12)), k[1]), speed(T.jd(t + dt.timedelta(hours=12)), k[1])
                if not ((s0 < 0 <= s1) if k[2] == "direct" else (s0 >= 0 > s1)):
                    bad.append(f"{e['text']}: speed {s0:.5f} -> {s1:.5f}")
            elif k[0] == "apsis":
                g = lambda y: swe.calc_ut(y, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][5]
                a0, a1 = g(T.jd(t - dt.timedelta(hours=3))), g(T.jd(t + dt.timedelta(hours=3)))
                if not ((a0 < 0 <= a1) if k[1] == "perigee" else (a0 >= 0 > a1)):
                    bad.append(f"{e['text']}: distance speed {a0:.5f} -> {a1:.5f}")
            elif k[0] == "bhadra":
                if not (karana_fn(y1) == "Vishti" and karana_fn(y0) != "Vishti"):
                    bad.append(f"{e['text']}: karana {karana_fn(y0)}->{karana_fn(y1)}")
    add("Every event time re-derived from the ephemeris (±6 min; Moon aspects ±0.15°, stations ±12 h, apsides ±3 h)", not bad, f"{n} events checked" + ("; " + "; ".join(bad[:5]) if bad else ""))
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
    add("Every sky event of the week classified (rule starts/ends, padas, navamsas and whole-sign aspect begin/end are covered by the rule records)",
        not unclassified, f"{len(unclassified)} not classified" + ("; " + "; ".join(unclassified[:5]) if unclassified else ""))
    return out


def main():
    cal = json.load(open(OUT / "calendar_2026-11-24_to_2026-12-31_ET.json"))
    nsl = json.load(open(OUT / "new_sources_leftover_ET.json"))
    MK = T.markets()
    if len(sys.argv) > 2:
        weeks = [(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))]
    else:                                                    # every week from 1 Dec to 31 Dec 2026
        weeks, a = [], dt.date(2026, 12, 1)
        while a <= dt.date(2026, 12, 31):
            weeks.append((a, min(a + dt.timedelta(days=6), dt.date(2026, 12, 31))))
            a += dt.timedelta(days=7)
    cache = {}
    for a, b in weeks:
        week(a, b, cal, nsl, MK, cache)


if __name__ == "__main__":
    main()
