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
    if k == "exact degree aspect":
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
        if m and m.group(1) in YOGAS:
            yi = YOGAS.index(m.group(1))
            return (f"yoga|{yi}", f"Yoga {m.group(1)} begins", lambda yi=yi: entries("yoga", yoga_fn, 0.1, yi))
    if k == "karana" and "Bhadra (Vishti) begins" in t:
        return ("bhadra", "Bhadra (Vishti) begins", lambda: entries("karana", karana_fn, 0.05, "Vishti"))
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


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 12, 1)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2026, 12, 7)
    cal = json.load(open(OUT / "calendar_2026-11-24_to_2026-12-31_ET.json"))
    nsl = json.load(open(OUT / "new_sources_leftover_ET.json"))
    days = [x for x in cal["days"] if a.isoformat() <= x["date"] <= b.isoformat()]
    MK = T.markets()
    classes, per_day = {}, []
    for x in days:
        evs = []
        for ch in x["changes"]:
            c = classify(ch)
            if not c:
                continue
            key, label, finder = c
            if key not in classes:
                print("class", label, flush=True)
                times = finder()
                classes[key] = dict(label=label, n_hist=len(times), stats=score_class(times, MK))
            evs.append(dict(et=ch["et"].split(" ", 3)[3], ist=ch["ist"].split(" ", 3)[3], kind=ch["kind"], text=ch["text"], key=key))
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
               n_cells=len(cells), significant=[dict(label=l, market=k, horizon=h, **s) for l, k, h, s in sig],
               nominal=[dict(label=l, market=k, horizon=h, **s) for l, k, h, s in nom],
               big_significant=[dict(label=l, market=k, **s) for l, k, s in bigsig])
    f = OUT / f"deep_dive_{a}_to_{b}_ET.json"
    f.write_text(json.dumps(res, indent=1, default=str))
    print(f"{len(classes)} event classes, {len(cells)} tests; q<0.10: {len(sig)}; nominal p<0.05: {len(nom)}; big-day q<0.10: {len(bigsig)}")
    for l, k, h, s in nom:
        print("  nominal", l, k, h, s)
    for l, k, s in bigsig:
        print("  big", l, k, s)


if __name__ == "__main__":
    main()
