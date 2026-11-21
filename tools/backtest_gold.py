"""Gold backtest: every gold rule in the project over the N years to 20 Nov 2026.

    python tools/backtest_gold.py            # 1 year:  20 Nov 2025 - 20 Nov 2026
    python tools/backtest_gold.py --years 5  # 5 years: 20 Nov 2021 - 20 Nov 2026

Missing astronomy layers (build/astronomy_<year>.json) are generated on demand
with tools/build_year.py.

Rules: exactly the set the gold report uses (tools/build_metal_report.py
metal_rules(): TA S34 + other TA/KD gold items, the 2026 document's gold
section, the user's Sun notes U1-U4). U2 and U4 are also scored per contact
planet (U2-Venus, U2-Mercury, ...), and the user's combined Sun-state
(rise-signals vs fall-signals) is scored as one model.

Prices: COMEX gold front-month continuous (Yahoo Finance GC=F) daily closes,
build/pdfref/backtest/gold_GC_F_daily.csv. Dates are New York trading dates.

Scoring (fixed before looking at results):
  * entry  = the last daily close before the event (an event at/after 17:00 ET
             counts after that day's close; a day-hit counts from the day's open);
  * windows of >= 3 calendar days with >= 2 trading days inside the backtest
    year: return from entry to the last close inside the window (clipped to the
    backtest year; 'open' if still running on 20 Nov 2026);
  * instants, day-hits and windows < 3 days: 5-trading-day forward return
    (1, 3 and 10-day returns shown as a sensitivity check);
  * |return| < 0.5 % = FLAT (neither worked nor failed);
  * Bullish rule worked if the return > +0.5 %, Bearish if < -0.5 %.
  * Base rate = among all 5-day (or same-length) windows of the same backtest
    year (Nov-Nov) that moved more than 0.5 %, the share that moved the rule's
    way. Hit rate (worked / (worked + failed)) is compared with it, so a rule
    gets no credit for simply riding that year's drift. With several years a
    one-sided binomial p-value against that base rate is shown per rule.

For every failed occurrence the script lists what else was on the sky:
opposite-tone gold rules active at the same time, the Sun's (gold's karaka per
the user's notes) nakshatra lord and whole-sign contacts, Jupiter's state,
stations, sign ingresses of the slow planets, eclipses and combustion inside
the evaluation interval.

Writes build/pdfref/gold_backtest_<start>_to_2026-11-20_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import html
import importlib.util
import json
import math
import pathlib
import statistics
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky, parse  # noqa: E402
from finastro.pdfref.detect import Ctx, NAK_LORD, aspects, windows  # noqa: E402
from finastro.pdfref.engine import Grid, name, snapshot, utc, value_windows  # noqa: E402
from finastro.pdfref.user_rules import _contacts, sun_state  # noqa: E402

_spec = importlib.util.spec_from_file_location("bmr", ROOT / "tools" / "build_metal_report.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
M.METAL = "gold"

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
P1 = dt.datetime(2026, 11, 21, tzinfo=ET)          # exclusive: last day scored is 20 Nov 2026
YEARS = 1
P0 = dt.datetime(2025, 11, 20, tzinfo=ET)
OUT = ROOT / "build" / "pdfref"
PRICES = OUT / "backtest" / "gold_GC_F_daily.csv"
FLAT = 0.5          # percent
H = 5               # trading days, instants
SENS = (1, 3, 10)
MAJOR = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
SLOW = ("Sun", "Mars", "Venus", "Mercury", "Jupiter", "Saturn", "Rahu")


# ------------------------------------------------------------------ prices
def load_prices():
    rows = list(csv.DictReader(open(PRICES)))
    d = [dt.date.fromisoformat(r["date"]) for r in rows]
    c = [float(r["close"]) for r in rows]
    return d, c


D, CL = load_prices()
I0 = I1 = 0


def configure(years):
    """Set the backtest period: the `years` years ending 20 Nov 2026."""
    global YEARS, P0, I0, I1
    YEARS = years
    P0 = dt.datetime(2026 - years, 11, 20, tzinfo=ET)
    I0 = bisect.bisect_left(D, P0.date()) - 1           # close before the period starts
    I1 = bisect.bisect_right(D, (P1 - dt.timedelta(days=1)).date()) - 1   # last close in the period
    assert I0 >= 0, f"price file starts {D[0]}, after {P0.date()}"


def year_of(idx_or_date):
    """Backtest-year index (0 = first Nov-Nov year) of a trading index or date."""
    d = D[idx_or_date] if isinstance(idx_or_date, int) else idx_or_date
    k = YEARS - 1
    while k > 0 and d < dt.date(2026 - YEARS + k, 11, 20):
        k -= 1
    return k


def year_label(k):
    return f"{2026 - YEARS + k}-{(2027 - YEARS + k) % 100:02d}"


def entry_idx(t=None, day=None):
    if day is None:
        x = t.astimezone(ET)
        day = x.date() + (dt.timedelta(days=1) if x.hour >= 17 else dt.timedelta(0))
    return bisect.bisect_left(D, day) - 1             # last close strictly before `day`


def exit_idx(t):
    x = t.astimezone(ET)
    day = x.date() + (dt.timedelta(days=1) if x.hour >= 17 else dt.timedelta(0))
    return bisect.bisect_left(D, day) - 1


def pct(a, b):
    return (CL[b] / CL[a] - 1) * 100


def et(t):
    x = t.astimezone(ET)
    return f"{x:%a %d %b %Y %H:%M} {x.tzname()}"


# ------------------------------------------------------------------ events
def tone_of(r, h):
    v = r.verdict
    if "Malefic Vedha" in v and h.facts.get("value"):
        fv = str(h.facts["value"])
        bu, be = "MALEFIC" in fv, "BENEFIC" in fv
        return ("Mixed" if bu and be else "Bullish" if bu else "Bearish" if be else "Neutral"), \
            (("MALEFIC vedha -> gold Bullish" if bu else "") + (" / " if bu and be else "") + ("BENEFIC vedha -> gold Bearish" if be else ""))
    return M.verdict_tone(v), v


SPLIT = {  # user_u2 / user_u4 per contact planet
    "user_u2_venus": ("U2 - Venus with / aspecting the Sun", ("Venus",), False, "Bullish"),
    "user_u2_mercury": ("U2 - Mercury with the Sun", ("Mercury",), False, "Bullish"),
    "user_u2_jupiter": ("U2 - Jupiter with / aspecting the Sun", ("Jupiter",), False, "Bullish"),
    "user_u2_waxing_moon": ("U2 - waxing Moon with / aspecting the Sun", (), True, "Bullish"),
    "user_u4_saturn": ("U4 - Saturn with / aspecting the Sun", ("Saturn",), False, "Bearish"),
    "user_u4_rahu": ("U4 - Rahu with / aspecting the Sun (incl. Sun with Ketu)", ("Rahu",), False, "Bearish"),
}


#: scored through their per-planet components instead: the whole rule's window
#: restarts every time the set of contacts changes (e.g. the waxing Moon joining
#: Mercury), which would score one stretch several times.
WHOLE_SPLIT = ("user_u2_sun_with_or_aspected_by_benefics", "user_u4_sun_with_or_aspected_by_saturn_rahu")


def collect(ctxs):
    out = {}
    for r in M.metal_rules():
        if r.id in WHOLE_SPLIT:
            continue
        for c in ctxs:
            for h in r.detector(c):
                end = h.end or h.start
                if h.day is not None:
                    if not (P0.date() <= h.day < P1.date()):
                        continue
                elif not (h.start < P1 and end >= P0):
                    continue
                k = (r.id, h.start.replace(second=0, microsecond=0), end.replace(second=0, microsecond=0), h.day)
                if k in out:
                    continue
                tone, verdict = tone_of(r, h)
                out[k] = dict(rule_id=r.id, title=r.title, refs=list(r.refs), tone=tone, verdict=verdict, rule=r.rule,
                              start=h.start, end=h.end, day=h.day, open_start=h.open_start, open_end=h.open_end,
                              bodies=list(h.bodies), facts={k2: str(v) for k2, v in h.facts.items() if k2 != "condition_ends_utc"},
                              effect=r.effect or "")
    grid = ctxs[0].grid
    for rid, (title, group, moon, tone) in SPLIT.items():
        for h in windows(_contacts(group, moon), ("Sun",))(ctxs[0]):
            if not (h.start < P1 and h.end >= P0):
                continue
            out[(rid, h.start, h.end, None)] = dict(rule_id=rid, title=title, refs=[M.ROOT.name and "User note (Sun)"], tone=tone,
                                                    verdict=tone, rule=title, start=h.start, end=h.end, day=None,
                                                    open_start=h.open_start, open_end=h.open_end, bodies=["Sun"] + list(group),
                                                    facts={"value": str(h.facts.get("value", ""))}, effect="")
    # combined Sun-state model (user notes, Moon left out as in the report timeline)
    for w in value_windows(grid, sun_state):
        if not (w.start < P1 and w.end >= P0):
            continue
        nak, rise, fall = w.value
        net = len(rise) - len(fall)
        tone = "Bullish" if net > 0 else "Bearish" if net < 0 else "Neutral"
        out[("user_sun_state_net", w.start, w.end, None)] = dict(
            rule_id="user_sun_state_net", title="User Sun model: net rise vs fall signals", refs=["User note (Sun) - combined"],
            tone=tone, verdict=f"{len(rise)} rise : {len(fall)} fall", rule="U1-U4 counted together per Sun-state stretch",
            start=w.start, end=w.end, day=None, open_start=w.open_start, open_end=w.open_end, bodies=["Sun"],
            facts={"Sun nakshatra": nak, "rise": "; ".join(rise) or "-", "fall": "; ".join(fall) or "-"}, effect="", component=True)
    return list(out.values())


# ------------------------------------------------------------------ scoring
def score(e):
    s = max(e["start"], P0)
    if e["day"] is not None:
        a = entry_idx(day=e["day"])
    else:
        a = entry_idx(t=s)
    a = max(a, I0)
    e["entry_date"], e["entry_close"] = D[a].isoformat(), CL[a]
    fw = {n: (round(pct(a, a + n), 2) if a + n <= I1 + 0 or a + n < len(D) else None) for n in SENS + (H,)}
    for n in list(fw):
        if a + n >= len(D):
            fw[n] = None
    e["fwd"] = fw
    span_days = ((e["end"] - e["start"]).total_seconds() / 86400) if e["end"] else 0
    mode, b, still_open = "instant", None, False
    if e["end"] and span_days >= 3:
        end = min(e["end"], P1)
        b = min(exit_idx(end), I1)
        if b - a >= 2:
            mode = "window"
            still_open = e["end"] >= P1
    if mode == "window":
        ret = pct(a, b)
        e["exit_date"], e["exit_close"] = D[b].isoformat(), CL[b]
        e["horizon"] = f"window, {b - a} trading days"
        e["n_days"] = b - a
        seg = CL[a:b + 1]
        e["max_up"] = round((max(seg) / CL[a] - 1) * 100, 2)
        e["max_dn"] = round((min(seg) / CL[a] - 1) * 100, 2)
    else:
        b = a + H
        if b >= len(D):
            b = len(D) - 1
        if b <= a:
            e["outcome"] = "NO DATA"
            e["ret"] = None
            e["mode"] = mode
            return e
        ret = pct(a, b)
        e["exit_date"], e["exit_close"] = D[b].isoformat(), CL[b]
        e["horizon"] = f"{b - a} trading days after"
        e["n_days"] = b - a
        seg = CL[a:b + 1]
        e["max_up"] = round((max(seg) / CL[a] - 1) * 100, 2)
        e["max_dn"] = round((min(seg) / CL[a] - 1) * 100, 2)
    e["mode"], e["ret"], e["still_open"] = mode, round(ret, 2), still_open
    e["year"] = year_of(a + 1 if a < I1 else a)
    e["eval_from"], e["eval_to"] = a, b
    if e["tone"] not in ("Bullish", "Bearish"):
        e["outcome"] = "NOT SCORED"
    elif abs(ret) < FLAT:
        e["outcome"] = "FLAT"
    elif (ret > 0) == (e["tone"] == "Bullish"):
        e["outcome"] = "WORKED"
    else:
        e["outcome"] = "FAILED"
    return e


HORIZONS = (1, 3, 5, 10, 20, 40, 80, 120)


def base_rates(year=None):
    out = {}
    for n in HORIZONS:
        rs = [pct(i, i + n) for i in range(I0, I1 - n + 1) if year is None or year_of(i) == year]
        if not rs:
            continue
        up, dn = sum(r > FLAT for r in rs), sum(r < -FLAT for r in rs)
        out[n] = dict(up=up / len(rs), dn=dn / len(rs), cond_up=up / max(up + dn, 1), n=len(rs))
    return out


def base_for(n, tone, year):
    """P(move goes the rule's way | |move| > FLAT), same horizon, same backtest year."""
    b = BASE_Y.get(year) or BASE
    k = min(b, key=lambda x: abs(x - n))
    return b[k]["cond_up"] if tone == "Bullish" else 1 - b[k]["cond_up"]


def binom_p(k, n, p):
    """One-sided P(X >= k), X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)) if n else None


# ------------------------------------------------------------------ sky context
REC = []


def load_records():
    for f in (f"astronomy_{y}.json" for y in range(P0.year, P1.year + 1)):
        for r in json.load(open(ROOT / "build" / f, encoding="utf-8"))["records"]:
            ec = r["event_class"]
            b = r["bodies"]
            keep = (ec == "eclipse" or ec == "combustion" or (ec == "station" and b[0] in MAJOR)
                    or (ec == "sign_ingress" and b[0] in SLOW)
                    or (ec in ("conjunction", "opposition") and all(x in MAJOR for x in b)))
            if keep:
                t0 = parse(r["time"]["t_start_utc"])
                t1 = parse(r["time"]["t_end_utc"]) if r["time"].get("t_end_utc") else None
                a = dict(r.get("astronomy", {}))
                a["family"] = r.get("rule_family", "")
                REC.append((t0, t1, ec, b, a))
    REC.sort(key=lambda x: x[0])
    seen, uniq = set(), []
    for x in REC:
        k = (x[0].replace(second=0), x[2], tuple(x[3]))
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    REC[:] = uniq


def rec_text(x):
    t0, t1, ec, b, a = x
    when = f"{t0.astimezone(ET):%d %b}"
    if ec == "sign_ingress":
        return f"{when}: {name(b[0])} enters {a.get('sign_to', a.get('sign'))}"
    if ec == "station":
        return f"{when}: {name(b[0])} stations {'retrograde' if a['family'].endswith('_R') else 'direct'} in {a.get('sign', '?')}"
    if ec == "eclipse":
        return f"{when}: {'lunar' if a['family'].endswith('lunar') else 'solar'} eclipse in {a.get('sign', '?')} ({a.get('nakshatra', '?')})"
    if ec == "combustion":
        return f"{t0.astimezone(ET):%d %b}-{t1.astimezone(ET):%d %b}: {name(b[0])} combust" if t1 else f"{when}: {name(b[0])} combust"
    return f"{when}: {name(b[0])} {ec} {name(b[1])} in {a.get('sign', '?')}"


def records_between(t0, t1):
    out = []
    for x in REC:
        if x[2] == "combustion":
            e = x[1] or x[0]
            if x[0] <= t1 and e >= t0:
                out.append(x)
        elif t0 <= x[0] <= t1:
            out.append(x)
    return out


def sky_at(t):
    s = snapshot(t.replace(microsecond=0, second=0))
    pos = []
    for b in MAJOR + ("Moon",):
        p = s[b]
        r = " R" if p.retro and b not in ("Rahu", "Ketu") else ""
        pos.append(f"{name(b)} {p.sign} {p.deg:.0f}° {p.nak}{r}")
    sun_lord = NAK_LORD[s["Sun"].nak_i]
    contacts = []
    for b in ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"):
        if s[b].sign_i == s["Sun"].sign_i:
            contacts.append(f"{name(b)} with Sun")
        elif b not in ("Ketu",) and aspects(s, b, "Sun"):
            n = s.sign_dist(b, "Sun")
            contacts.append(f"{name(b)} aspects Sun ({n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n, 'th') })")
    jup = []
    for b in ("Saturn", "Rahu", "Ketu", "Mars"):
        if s[b].sign_i == s["Jupiter"].sign_i:
            jup.append(f"{name(b)} with Jupiter")
        elif b != "Ketu" and aspects(s, b, "Jupiter"):
            jup.append(f"{name(b)} aspects Jupiter")
    return dict(positions=pos, sun=f"Sun in {s['Sun'].nak} (lord {sun_lord}), {s['Sun'].sign}",
                sun_contacts=contacts, jupiter=f"Jupiter {s['Jupiter'].sign} {s['Jupiter'].nak}{' R' if s['Jupiter'].retro else ''}" + (f" - {', '.join(jup)}" if jup else ""),
                paksha=s.paksha, s=s)


def malefic_load(sk):
    """Plain counts used in the failure notes: malefic vs benefic contacts on the Sun."""
    mal = [c for c in sk["sun_contacts"] if c.split()[0] in ("Saturn", "Rahu", "Ketu", "Mars")]
    ben = [c for c in sk["sun_contacts"] if c.split()[0] in ("Jupiter", "Venus", "Mercury", "Moon")]
    return mal, ben


def active_between(events, t0, t1, exclude_id=None):
    act = []
    for e in events:
        if e["rule_id"] == exclude_id or e.get("component") or e["tone"] not in ("Bullish", "Bearish"):
            continue
        s = e["start"] if e["day"] is None else dt.datetime.combine(e["day"], dt.time(6), ET)
        en = e["end"] or s + dt.timedelta(days=7)          # instants: effect taken as one trading week
        if s <= t1 and en >= t0:
            act.append(e)
    return act


def explain(e, events):
    t0 = dt.datetime.combine(D[e["eval_from"]], dt.time(17), ET)
    t1 = dt.datetime.combine(D[e["eval_to"]], dt.time(17), ET)
    st = max(e["start"], P0)
    sk0 = sky_at(st)
    # worst adverse day inside the evaluation interval
    seg = list(range(e["eval_from"] + 1, e["eval_to"] + 1))
    rets = [(pct(i - 1, i), i) for i in seg]
    worst = (min(rets) if e["tone"] == "Bullish" else max(rets)) if rets else None
    skw = sky_at(dt.datetime.combine(D[worst[1]], dt.time(12), ET)) if worst else None
    act = active_between(events, t0, t1, e["rule_id"])
    opp = list({a["rule_id"]: a for a in act if a["tone"] != e["tone"]}.values())     # one entry per rule
    same = list({a["rule_id"]: a for a in act if a["tone"] == e["tone"]}.values())
    recs = [rec_text(x) for x in records_between(t0 - dt.timedelta(days=1), t1)]
    mal, ben = malefic_load(sk0)
    causes, flags = [], {}
    bull = e["tone"] == "Bullish"
    flags["Opposite-tone rules outnumbered supporting ones"] = len(opp) > len(same)
    if opp:
        names = collections.Counter(a["title"] for a in opp)
        causes.append(f"{len(opp)} opposite-tone gold rule(s) active vs {len(same)} supporting: " +
                      "; ".join(k for k, v in names.most_common(8)))
    sat_rahu = [c for c in mal if c.split()[0] in ("Saturn", "Rahu", "Ketu")]
    mars = [c for c in mal if c.startswith("Mars")]
    jup = [c for c in ben if c.startswith("Jupiter")]
    flags["Saturn / Rahu / Ketu on the Sun at the start"] = bool(sat_rahu)
    flags["Mars on the Sun at the start"] = bool(mars)
    flags["Jupiter on the Sun at the start"] = bool(jup)
    if bull and sat_rahu:
        causes.append("Sun (gold) under Saturn/Rahu contact at the start (user U4: crash): " + ", ".join(sat_rahu))
    if bull and mars:
        causes.append("Sun (gold) with or aspected by Mars at the start: " + ", ".join(mars))
    if not bull and ben:
        causes.append("Sun (gold) supported by benefic contact at the start (user U2: hike): " + ", ".join(ben))
    s0 = sk0["s"]
    jaff = [b for b in ("Rahu", "Ketu", "Mars", "Saturn") if s0[b].sign_i == s0["Jupiter"].sign_i]
    flags["Jupiter sharing a sign with Rahu / Ketu / Mars / Saturn"] = bool(jaff)
    if bull and jaff:
        causes.append(f"Jupiter in {s0['Jupiter'].sign} with {', '.join(jaff)}")
    lord = NAK_LORD[s0["Sun"].nak_i]
    flags["Sun's nakshatra lord against the rule (user U1/U3)"] = (bull and lord in ("Saturn", "Rahu")) or (not bull and lord in ("Venus", "Mercury", "Jupiter"))
    if bull and lord in ("Saturn", "Rahu"):
        causes.append(f"Sun in {s0['Sun'].nak}, a {lord} nakshatra (user U3: fall)")
    if not bull and lord in ("Venus", "Mercury", "Jupiter"):
        causes.append(f"Sun in {s0['Sun'].nak}, a {lord} nakshatra (user U1: rise)")
    st_list = [r for r in recs if "station" in r]
    flags["A planet stations inside the interval"] = bool(st_list)
    if st_list:
        causes.append("Station(s) inside the interval: " + "; ".join(st_list))
    ecl = [r for r in recs if "eclipse" in r]
    flags["Eclipse inside the interval"] = bool(ecl)
    if ecl:
        causes.append("Eclipse inside the interval: " + "; ".join(ecl))
    ing = [r for r in recs if "enters" in r and any(p in r for p in ("Jupiter", "Saturn", "Rahu", "Mars", "Sun"))]
    if ing:
        causes.append("Ingress(es): " + "; ".join(ing))
    e["flags"] = flags
    e["analysis"] = dict(
        sky_at_start=sk0["positions"], sun=sk0["sun"], sun_contacts=sk0["sun_contacts"], jupiter=sk0["jupiter"], paksha=sk0["paksha"],
        worst_day=(f"{D[worst[1]]:%a %d %b %Y} ({worst[0]:+.2f} %)" if worst else ""),
        sky_worst=(skw["sun"] + "; " + ", ".join(skw["sun_contacts"]) + "; " + skw["jupiter"]) if skw else "",
        opposite=[f"{a['title']} [{a['tone']}] {et(a['start']) if a['day'] is None else a['day'].isoformat()}" for a in opp][:12],
        supporting=len(same), records=recs[:25], causes=causes)
    return e


# ------------------------------------------------------------------ big moves
def big_moves(events, n=5, k=8):
    rets = [(pct(i, i + n), i) for i in range(I0, I1 - n + 1)]
    picks = []
    for sign in (-1, 1):
        used = set()
        for r, i in sorted(rets, key=lambda x: sign * -x[0] if sign > 0 else x[0]):
            if any(abs(i - j) < n for j in used):
                continue
            used.add(i)
            t0 = dt.datetime.combine(D[i], dt.time(17), ET)
            t1 = dt.datetime.combine(D[i + n], dt.time(17), ET)
            act = active_between(events, t0, t1)
            bu = list({a["rule_id"]: a for a in act if a["tone"] == "Bullish"}.values())
            be = list({a["rule_id"]: a for a in act if a["tone"] == "Bearish"}.values())
            sk = sky_at(t0 + dt.timedelta(days=n / 2))
            recs = [rec_text(x) for x in records_between(t0, t1)]
            picks.append(dict(dir="fall" if sign < 0 else "rise", start=D[i].isoformat(), end=D[i + n].isoformat(), ret=round(r, 2),
                              bull=sorted({a["title"] for a in bu}), bear=sorted({a["title"] for a in be}), n_bull=len(bu), n_bear=len(be),
                              sun=sk["sun"], sun_contacts=sk["sun_contacts"], jupiter=sk["jupiter"], positions=sk["positions"], records=recs))
            if len([p for p in picks if p["dir"] == ("fall" if sign < 0 else "rise")]) >= k:
                break
    return picks


def _with_or_asp(s, b, tgt):
    return s[b].sign_i == s[tgt].sign_i or (b not in ("Ketu",) and aspects(s, b, tgt))


FACTORS = (
    ("Saturn with / aspecting the Sun", lambda s, t0, t1: _with_or_asp(s, "Saturn", "Sun")),
    ("Rahu with / aspecting the Sun (or Sun with Ketu)", lambda s, t0, t1: _with_or_asp(s, "Rahu", "Sun") or s["Ketu"].sign_i == s["Sun"].sign_i),
    ("Mars with / aspecting the Sun", lambda s, t0, t1: _with_or_asp(s, "Mars", "Sun")),
    ("Jupiter with / aspecting the Sun", lambda s, t0, t1: _with_or_asp(s, "Jupiter", "Sun")),
    ("Venus with the Sun", lambda s, t0, t1: s["Venus"].sign_i == s["Sun"].sign_i),
    ("Sun in a Saturn or Rahu nakshatra", lambda s, t0, t1: NAK_LORD[s["Sun"].nak_i] in ("Saturn", "Rahu")),
    ("Sun in a Venus, Mercury or Jupiter nakshatra", lambda s, t0, t1: NAK_LORD[s["Sun"].nak_i] in ("Venus", "Mercury", "Jupiter")),
    ("Jupiter with Rahu, Ketu or Mars (same sign)", lambda s, t0, t1: any(s[b].sign_i == s["Jupiter"].sign_i for b in ("Rahu", "Ketu", "Mars"))),
    ("Jupiter retrograde", lambda s, t0, t1: s["Jupiter"].retro),
    ("Mercury retrograde", lambda s, t0, t1: s["Mercury"].retro),
    ("Venus retrograde", lambda s, t0, t1: s["Venus"].retro),
    ("Waxing Moon (Shukla paksha)", lambda s, t0, t1: s.paksha == "Shukla"),
    ("Eclipse within the window (+/-3 days)", lambda s, t0, t1: any(x[2] == "eclipse" for x in records_between(t0 - dt.timedelta(days=3), t1 + dt.timedelta(days=3)))),
    ("A planet stations within the window", lambda s, t0, t1: any(x[2] == "station" for x in records_between(t0, t1))),
)


def factor_table(moves, n=5):
    def present(i):
        t0 = dt.datetime.combine(D[i], dt.time(17), ET)
        t1 = dt.datetime.combine(D[min(i + n, len(D) - 1)], dt.time(17), ET)
        s = snapshot((t0 + (t1 - t0) / 2).astimezone(UTC).replace(microsecond=0, second=0))
        return [f(s, t0, t1) for _, f in FACTORS]
    allw = [present(i) for i in range(I0, I1 - n + 1)]
    idx = {d: i for i, d in enumerate(D)}
    falls = [present(idx[dt.date.fromisoformat(m["start"])]) for m in moves if m["dir"] == "fall"]
    rises = [present(idx[dt.date.fromisoformat(m["start"])]) for m in moves if m["dir"] == "rise"]
    out = []
    for k, (lab, _) in enumerate(FACTORS):
        out.append(dict(factor=lab, falls=sum(x[k] for x in falls), n_falls=len(falls), rises=sum(x[k] for x in rises), n_rises=len(rises),
                        all_pct=round(sum(x[k] for x in allw) / len(allw) * 100)))
    return out


def daily_net(events):
    """Net signal each trading day (bull - bear active) vs next 1/5-day return."""
    rows = []
    for i in range(I0 + 1, I1):
        t = dt.datetime.combine(D[i], dt.time(17), ET)
        act = {(a["rule_id"], a["tone"]) for a in active_between(events, t, t)}     # one vote per rule and direction
        net = sum(1 if tone == "Bullish" else -1 for _, tone in act)
        rows.append((D[i], net, pct(i, i + 1), pct(i, min(i + 5, len(D) - 1))))
    def corr(x, y):
        mx, my = statistics.fmean(x), statistics.fmean(y)
        sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
        return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else 0
    nets = [r[1] for r in rows]
    buckets = {}
    for lab, f in (("net > 0 (more bullish rules active)", lambda v: v > 0), ("net = 0", lambda v: v == 0), ("net < 0 (more bearish rules active)", lambda v: v < 0)):
        sel = [r for r in rows if f(r[1])]
        if sel:
            buckets[lab] = dict(days=len(sel), avg1=round(statistics.fmean(r[2] for r in sel), 3), avg5=round(statistics.fmean(r[3] for r in sel), 3),
                                up1=round(sum(r[2] > 0 for r in sel) / len(sel) * 100, 1), up5=round(sum(r[3] > 0 for r in sel) / len(sel) * 100, 1))
    return dict(corr1=round(corr(nets, [r[2] for r in rows]), 3), corr5=round(corr(nets, [r[3] for r in rows]), 3), buckets=buckets,
                series=[(d.isoformat(), n) for d, n, _, _ in rows])


# ------------------------------------------------------------------ main
def main():
    global BASE, BASE_Y
    years = 1
    if "--years" in sys.argv:
        years = int(sys.argv[sys.argv.index("--years") + 1])
    configure(years)
    for y in range(P0.year, P1.year + 1):
        if not (ROOT / "build" / f"astronomy_{y}.json").exists():
            subprocess.run([sys.executable, str(ROOT / "tools" / "build_year.py"), str(y)], check=True, stdout=subprocess.DEVNULL)
    load_records()
    grid = Grid(utc(P0.year, 5, 1), utc(2027, 1, 31))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in range(P0.year, P1.year + 1)]
    events = collect(ctxs)
    events.sort(key=lambda e: (e["start"], e["rule_id"]))
    BASE = base_rates()
    BASE_Y = {k: base_rates(k) for k in range(YEARS)}
    for e in events:
        score(e)
    scored = [e for e in events if e.get("outcome") in ("WORKED", "FAILED", "FLAT")]
    for e in scored:
        if e["outcome"] in ("FAILED", "WORKED"):
            explain(e, events)          # worked ones too, so each condition's rate can be compared
    # per rule
    per = collections.OrderedDict()
    for r in M.metal_rules():
        if r.id in WHOLE_SPLIT:
            continue
        per.setdefault(r.id, dict(rule_id=r.id, title=r.title, tone=collections.Counter({M.verdict_tone(r.verdict): 0}), n=0, worked=0, failed=0, flat=0,
                                  not_scored=0, rets=[], base=[], component=False, refs=list(r.refs), sens={n: [0, 0] for n in SENS + (H,)},
                                  by_year={k: [0, 0] for k in range(YEARS)}))
    for e in events:
        p = per.setdefault(e["rule_id"], dict(rule_id=e["rule_id"], title=e["title"], tone=collections.Counter(), n=0, worked=0, failed=0, flat=0,
                                             not_scored=0, rets=[], base=[], component=e.get("component", False), refs=e["refs"],
                                             sens={n: [0, 0] for n in SENS + (H,)}, by_year={k: [0, 0] for k in range(YEARS)}))
        p["n"] += 1
        p["tone"][e["tone"]] += 1
        o = e.get("outcome")
        if o == "WORKED":
            p["worked"] += 1
        elif o == "FAILED":
            p["failed"] += 1
        elif o == "FLAT":
            p["flat"] += 1
        else:
            p["not_scored"] += 1
        if o in ("WORKED", "FAILED", "FLAT"):
            sgn = 1 if e["tone"] == "Bullish" else -1
            p["rets"].append(sgn * e["ret"])
            if o != "FLAT":
                p["base"].append(base_for(e["n_days"], e["tone"], e["year"]))
                p["by_year"][e["year"]][0] += 1
                p["by_year"][e["year"]][1] += o == "WORKED"
            for n in SENS + (H,):
                v = e["fwd"].get(n)
                if v is not None and abs(v) >= FLAT:
                    p["sens"][n][0] += 1
                    p["sens"][n][1] += (v > 0) == (e["tone"] == "Bullish")
    for p in per.values():
        dec = p["worked"] + p["failed"]
        p["hit_rate"] = round(p["worked"] / dec * 100) if dec else None
        p["avg_dir_ret"] = round(statistics.fmean(p["rets"]), 2) if p["rets"] else None
        p["base_rate"] = round(statistics.fmean(p["base"]) * 100) if p["base"] else None
        p["p_value"] = round(binom_p(p["worked"], dec, statistics.fmean(p["base"])), 3) if p["base"] else None
        p["p_value_fail"] = round(binom_p(p["failed"], dec, 1 - statistics.fmean(p["base"])), 3) if p["base"] else None
        yrs = [v for v in p["by_year"].values() if v[0]]
        p["years_right"] = sum(1 for v in yrs if v[1] * 2 > v[0])
        p["years_wrong"] = sum(1 for v in yrs if v[1] * 2 < v[0])
        p["years_active"] = len(yrs)
        p["tone"] = "/".join(k for k, _ in p["tone"].most_common())
        # relative to the drift-aware base rate: +/-10 points and the average move on the same side
        p["verdict"] = ("did not occur" if not p["n"] else "not scored" if not p["worked"] + p["failed"] + p["flat"] else "n/a" if not dec else
                        "Worked" if p["hit_rate"] >= p["base_rate"] + 10 and p["avg_dir_ret"] > 0 else
                        "Failed" if p["hit_rate"] <= p["base_rate"] - 10 and p["avg_dir_ret"] < 0 else "Mixed")
        del p["rets"], p["base"]
    moves = big_moves(events, k=8 if YEARS == 1 else 15)
    net = daily_net(events)
    global FT
    FT = factor_table(moves)
    write(events, per, moves, net)


def findings(per, moves, net, fails, cause_count, events):
    P = per
    main = [p for p in P.values() if not p["component"]]
    W = sum(p["worked"] for p in main)
    F = sum(p["failed"] for p in main)
    dec_ev = [e for e in events if e.get("outcome") in ("WORKED", "FAILED") and not e.get("component")]
    exp = statistics.fmean(base_for(e["n_days"], e["tone"], e["year"]) for e in dec_ev) if dec_ev else 0
    b = net["buckets"]
    neg, pos = b.get("net < 0 (more bearish rules active)"), b.get("net > 0 (more bullish rules active)")
    sun = P.get("user_sun_state_net", {})

    def li(p):
        extra = ""
        if YEARS > 1 and p.get("p_value") is not None:
            extra = f"; p = {p['p_value']:.3f}; right in {p['years_right']} of {p['years_active']} years with a result"
        return (f"<li><b>{html.escape(p['title'])}</b> ({p['tone']}): {p['worked']} of {p['worked'] + p['failed']} worked ({p['hit_rate']}% vs base {p['base_rate']}%), "
                f"average move {fmt_ret(p['avg_dir_ret'])} in the stated direction{extra}</li>")
    key = lambda p: (-(p["worked"] + p["failed"]), -(p["avg_dir_ret"] or 0))
    good = sorted((p for p in P.values() if p["verdict"] == "Worked"), key=key)
    bad = sorted((p for p in P.values() if p["verdict"] == "Failed"), key=key)
    out = [f"<li><b>Overall.</b> {W} of {W + F} decided occurrences worked ({W / max(W + F, 1) * 100:.0f}%), against {exp * 100:.0f}% expected by chance from the base rates of those same occurrences "
           f"(p = {binom_p(W, W + F, exp):.3f} for doing this well or better by luck)."
           + (f" On the {neg['days']} trading days when more bearish than bullish gold rules were active, gold moved {neg['avg5']:+.2f}% on average over the next 5 days ({neg['up5']:.0f}% up); "
              f"on the {pos['days']} bullish-majority days, {pos['avg5']:+.2f}% ({pos['up5']:.0f}% up). Correlation of the daily net count with the next 5-day move: {net['corr5']:+.3f}." if neg and pos else "") + "</li>"]
    if YEARS > 1:
        sig = sorted((p for p in P.values() if p.get("p_value") is not None and p["p_value"] < 0.05), key=lambda p: p["p_value"])
        sigf = sorted((p for p in P.values() if p.get("p_value_fail") is not None and p["p_value_fail"] < 0.05), key=lambda p: p["p_value_fail"])
        out.append("<li><b>Statistically clear results</b> (p &lt; 0.05 against the base rate):<ul>"
                   + ("".join(li(p) for p in sig) or "<li>None of the rules beat chance at that level.</li>")
                   + ("".join(li(p).replace("<li>", "<li>Significantly <i>wrong</i>: ", 1) for p in sigf)) + "</ul></li>")
    out.append("<li><b>What worked</b> (most decided occurrences first):<ul>" + ("".join(li(p) for p in good[:12]) or "<li>none</li>") + "</ul>"
               + (f"Your combined Sun model (U1–U4 counted together): {sun['worked']} of {sun['worked'] + sun['failed']} stretches ({sun['hit_rate']}% vs base {sun['base_rate']}%), average {fmt_ret(sun['avg_dir_ret'])}"
                  + (f", p = {sun['p_value']:.3f}, right in {sun['years_right']} of {sun['years_active']} years" if YEARS > 1 and sun.get('p_value') is not None else "") + "." if sun.get("hit_rate") is not None else "") + "</li>")
    out.append("<li><b>What failed</b>:<ul>" + ("".join(li(p) for p in bad[:14]) or "<li>none</li>") + "</ul></li>")
    for tone in ("Bullish", "Bearish"):
        rows_ = cause_count.get(tone, [])
        if not rows_ or not rows_[0][2]:
            continue
        txt = lambda r: f"{html.escape(r[0])} ({r[1] / max(r[2], 1) * 100:.0f}% of failures vs {r[3] / max(r[4], 1) * 100:.0f}% of successes)"
        hurt = [r for r in rows_ if (r[1] / max(r[2], 1) - r[3] / max(r[4], 1)) >= 0.10][:4]
        helped = [r for r in reversed(rows_) if (r[3] / max(r[4], 1) - r[1] / max(r[2], 1)) >= 0.10][:3]
        out.append(f"<li><b>Why {tone.lower()} rules failed.</b> Conditions clearly more common when they failed: " + ("; ".join(txt(r) for r in hurt) or "none stood out")
                   + ". More common when they worked: " + ("; ".join(txt(r) for r in helped) or "none stood out") + ".</li>")
    jan = next((m for m in moves if m["start"].startswith("2026-01-2") and m["dir"] == "fall"), None)
    mar = next((m for m in moves if m["start"].startswith("2026-03-1") and m["dir"] == "fall"), None)
    if jan:
        out.append(f"<li><b>Biggest single miss: the late-January 2026 crash</b> ({jan['start']} → {jan['end']}, {jan['ret']:+.1f}%, including the −10.8% day on 30 Jan after the 29 Jan peak). "
                   f"Gold rules active: {jan['n_bull']} bullish, {jan['n_bear']} bearish. Sky: {html.escape(jan['sun'])}; {html.escape(', '.join(jan['sun_contacts']))}; {html.escape(jan['jupiter'])}; "
                   f"{html.escape('; '.join(jan['records']))}. The Sun, Mercury, Venus and Mars were all in Capricorn (Mars exalted), Venus was about to combust and Jupiter was retrograde. "
                   "No rule in the set describes a four-planet stellium on the Sun or a Venus combustion, and none of your Sun rules treats Mars, Mercury or Venus crowding the Sun as negative.</li>")
    if mar:
        out.append(f"<li><b>March 2026</b> ({mar['start']} → {mar['end']}, {mar['ret']:+.1f}%): bearish rules active: {html.escape('; '.join(mar['bear']) or 'none')}; {mar['n_bull']} bullish rules active at the same time. "
                   f"Sky: {html.escape(mar['sun'])}; {html.escape(', '.join(mar['sun_contacts']))}.</li>")
    falls = [m for m in moves if m["dir"] == "fall"]
    if falls:
        warned = sum(1 for m in falls if m["n_bear"] > m["n_bull"])
        share = pos["days"] / max(sum(v["days"] for v in b.values()), 1) * 100 if pos else 0
        out.append(f"<li><b>The {len(falls)} biggest 5-day falls:</b> bearish rules outnumbered bullish ones in {warned} of them; in the rest the rule set leaned bullish going into the fall "
                   f"(it leans bullish on {share:.0f}% of all trading days, so a bullish majority by itself carries little information). "
                   + "; ".join(f"{m['start']} {m['ret']:+.1f}% ({m['n_bull']}:{m['n_bear']})" for m in sorted(falls, key=lambda m: m["ret"])[:8]) + ".</li>")
    rises = [m for m in moves if m["dir"] == "rise"]
    if rises:
        warned = sum(1 for m in rises if m["n_bull"] > m["n_bear"])
        out.append(f"<li><b>The {len(rises)} biggest 5-day rises:</b> bullish rules outnumbered bearish ones in {warned} of them.</li>")
    if YEARS == 1:
        out.append("<li><b>How far to trust this.</b> Most rules fired only 1–3 times in the year, so a 100% or 0% record is one or two data points; see the 5-year run for which results hold up.</li>")
    else:
        rare = sum(1 for p in main if 0 < p["worked"] + p["failed"] < 5)
        out.append(f"<li><b>How far to trust this.</b> {YEARS} years give the frequent rules (Sun contacts, new moons, vedha, darshan) enough occurrences to judge; {rare} rules still have fewer than 5 decided occurrences, and their records stay anecdotal. "
                   "A rule that is right in most individual years is more trustworthy than one whose total comes from a single year; check the per-year columns.</li>")
    return "<h2>Key findings</h2><ol>" + "".join(out) + "</ol>"


def fmt_ret(v):
    return "" if v is None else f"{v:+.2f}%"


def write(events, per, moves, net):
    main_rules = [p for p in per.values() if not p["component"]]
    comp = [p for p in per.values() if p["component"]]
    tot = collections.Counter(e.get("outcome") for e in events if not e.get("component"))
    dec = tot["WORKED"] + tot["FAILED"]
    year_ret = pct(I0, I1)
    YB = []
    for k in range(YEARS):
        idx = [i for i in range(I0 + 1, I1 + 1) if year_of(i) == k]
        YB.append((idx[0] - 1, idx[-1]))
    p0s, p1s = f"{P0:%d %b %Y}", f"{P1 - dt.timedelta(days=1):%d %b %Y}"
    span = "1 year" if YEARS == 1 else f"{YEARS} years"
    imax = I0 + CL[I0:I1 + 1].index(max(CL[I0:I1 + 1]))

    def rule_row(p):
        cls = {"Worked": "bullish", "Failed": "bearish", "Mixed": "mixed"}.get(p["verdict"], "")
        sens = " · ".join(f"{n}d {p['sens'][n][1]}/{p['sens'][n][0]}" for n in SENS + (H,) if p["sens"][n][0])
        return (f"<tr class='{cls}'><td><b>{html.escape(p['title'])}</b><div class='s'>{html.escape(p['rule_id'])}</div></td><td>{p['tone']}</td>"
                f"<td class='n'>{p['n']}</td><td class='n'>{p['worked']}</td><td class='n'>{p['failed']}</td><td class='n'>{p['flat']}</td><td class='n'>{p['not_scored']}</td>"
                f"<td class='n'><b>{'' if p['hit_rate'] is None else str(p['hit_rate']) + '%'}</b></td><td class='n'>{'' if p['base_rate'] is None else str(p['base_rate']) + '%'}</td>"
                f"<td class='n'>{fmt_ret(p['avg_dir_ret'])}</td><td><span class='tag {cls}'>{p['verdict']}</span></td>"
                + (f"<td class='n'>{pv(p)}</td>" + "".join(f"<td class='n s'>{yc(p['by_year'][k])}</td>" for k in range(YEARS)) if YEARS > 1 else "")
                + f"<td class='s'>{sens}</td></tr>")

    def pv(p):
        if p.get("p_value") is None:
            return ""
        if p["p_value"] < 0.05:
            return f"<b style='color:var(--bu2)'>{p['p_value']:.3f}</b>"
        if p["p_value_fail"] is not None and p["p_value_fail"] < 0.05:
            return f"<b style='color:var(--be2)'>{p['p_value']:.3f}</b>"
        return f"{p['p_value']:.2f}"

    def yc(v):
        if not v[0]:
            return "–"
        col = "var(--bu2)" if v[1] * 2 > v[0] else "var(--be2)" if v[1] * 2 < v[0] else "var(--mx2)"
        return f"<span style='color:{col}'>{v[1]}/{v[0]}</span>"

    yhead = ("<th>p-value vs base</th>" + "".join(f"<th>{year_label(k)}</th>" for k in range(YEARS))) if YEARS > 1 else ""

    def ev_row(e):
        o = e.get("outcome", "")
        cls = {"WORKED": "bullish", "FAILED": "bearish", "FLAT": "mixed"}.get(o, "")
        when = (e["day"].strftime("%a %d %b %Y") if e["day"] else et(e["start"]) + (f" → {et(e['end'])}" if e["end"] else ""))
        if e["open_start"] or e["start"] < P0:
            when += " (began before the backtest period)"
        fw = " ".join(f"{n}d {fmt_ret(e['fwd'].get(n))}" for n in SENS if e.get("fwd", {}).get(n) is not None)
        det = "; ".join(f"{k}: {v}" for k, v in e["facts"].items())
        a = e.get("analysis")
        an = ""
        if a and o == "FAILED":
            an = ("<details><summary>Why it may have failed</summary><ul>" + "".join(f"<li>{html.escape(c)}</li>" for c in a["causes"]) +
                  f"</ul><p class='s'><b>Sky at start:</b> {html.escape(' · '.join(a['sky_at_start']))}<br><b>Sun:</b> {html.escape(a['sun'])}; contacts: {html.escape(', '.join(a['sun_contacts']) or 'none')}; "
                  f"<b>{html.escape(a['jupiter'])}</b>; {a['paksha']} paksha<br><b>Worst day:</b> {html.escape(a['worst_day'])} — {html.escape(a['sky_worst'])}"
                  + (f"<br><b>Transits in the interval:</b> {html.escape(' · '.join(a['records']))}" if a["records"] else "") + "</p></details>")
        return (f"<tr class='{cls}'><td class='w'>{html.escape(when)}</td><td><b>{html.escape(e['title'])}</b><div class='s'>{html.escape(det)[:400]}</div>{an}</td>"
                f"<td>{e['tone']}</td><td class='s'>{e.get('entry_date', '')} {e.get('entry_close', 0):,.1f} → {e.get('exit_date', '')} {e.get('exit_close', 0):,.1f}<br>{e.get('horizon', '')}{' (still open)' if e.get('still_open') else ''}</td>"
                f"<td class='n'><b>{fmt_ret(e.get('ret'))}</b><div class='s'>max ↑{fmt_ret(e.get('max_up'))} ↓{fmt_ret(e.get('max_dn'))}</div></td><td class='s'>{fw}</td><td><span class='tag {cls}'>{o}</span></td></tr>")

    fails = [e for e in events if e.get("outcome") == "FAILED" and not e.get("component")]
    wins = [e for e in events if e.get("outcome") == "WORKED" and not e.get("component")]
    cause_count = {}
    for tone in ("Bullish", "Bearish"):
        fl = [e for e in fails if e["tone"] == tone]
        wn = [e for e in wins if e["tone"] == tone]
        rows_ = []
        for k in (fl or wn)[0]["flags"]:
            f_, w_ = sum(e["flags"][k] for e in fl), sum(e["flags"][k] for e in wn)
            rows_.append((k, f_, len(fl), w_, len(wn)))
        cause_count[tone] = sorted(rows_, key=lambda x: -(x[1] / max(x[2], 1) - x[3] / max(x[4], 1)))
    opp_titles = collections.Counter(a.split(" [")[0] for e in fails for a in e["analysis"]["opposite"])

    mv_rows = "".join(
        f"<tr class='{'bearish' if m['dir'] == 'fall' else 'bullish'}'><td class='w'>{m['start']} → {m['end']}</td><td class='n'><b>{m['ret']:+.2f}%</b></td>"
        f"<td class='n'>{m['n_bull']} : {m['n_bear']}</td><td class='s'><b>Bullish:</b> {html.escape('; '.join(m['bull']) or '-')}<br><b>Bearish:</b> {html.escape('; '.join(m['bear']) or '-')}</td>"
        f"<td class='s'>{html.escape(m['sun'])}; {html.escape(', '.join(m['sun_contacts']) or 'no contacts')}<br>{html.escape(m['jupiter'])}<br>{html.escape(' · '.join(m['records'][:10]))}</td></tr>"
        for m in moves)
    nb = "".join(f"<tr><td>{html.escape(k)}</td><td class='n'>{v['days']}</td><td class='n'>{v['avg1']:+.3f}%</td><td class='n'>{v['up1']}%</td><td class='n'>{v['avg5']:+.3f}%</td><td class='n'>{v['up5']}%</td></tr>" for k, v in net["buckets"].items())
    base_tbl = "".join(f"<tr><td>{n} trading days</td><td class='n'>{BASE[n]['up'] * 100:.0f}%</td><td class='n'>{BASE[n]['dn'] * 100:.0f}%</td><td class='n'>{BASE[n]['cond_up'] * 100:.0f}%</td><td class='n'>{BASE[n]['n']}</td>"
                       + "".join(f"<td class='n'>{BASE_Y[k][n]['cond_up'] * 100:.0f}%</td>" if n in BASE_Y[k] else "<td></td>" for k in range(YEARS) if YEARS > 1) + "</tr>" for n in sorted(BASE))
    yr_rows = "".join(f"<tr><td>{year_label(k)}</td><td class='n'>{CL[a]:,.0f}</td><td class='n'>{CL[b]:,.0f}</td><td class='n'>{pct(a, b):+.1f}%</td>"
                      f"<td class='n'>{sum(1 for e in events if e.get('year') == k and e.get('outcome') == 'WORKED' and not e.get('component'))}</td>"
                      f"<td class='n'>{sum(1 for e in events if e.get('year') == k and e.get('outcome') == 'FAILED' and not e.get('component'))}</td></tr>"
                      for k, (a, b) in enumerate(YB))

    worked_rules = [p for p in main_rules if p["verdict"] == "Worked"]
    failed_rules = [p for p in main_rules if p["verdict"] == "Failed"]
    mixed_rules = [p for p in main_rules if p["verdict"] == "Mixed"]
    css = """
:root{--bg:#fff;--fg:#1d1d1f;--mut:#666;--line:#e3e3e8;--bu:#e8f6ec;--bu2:#1b7f3b;--be:#fdecec;--be2:#b42318;--mx:#fff7e0;--mx2:#8a6100;--head:#f5f5f7}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141416;--fg:#ececf0;--mut:#9a9aa3;--line:#2c2c31;--bu:#13291b;--bu2:#5fd07f;--be:#331617;--be2:#ff8a80;--mx:#2e260f;--mx2:#f0c35a;--head:#1d1d21}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:16px;max-width:1500px}
h1{font-size:22px}h2{font-size:18px;margin-top:32px;border-bottom:1px solid var(--line);padding-bottom:4px}
.m{color:var(--mut)}.s{font-size:12px;color:var(--mut)}.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border:1px solid var(--line);padding:5px 7px;vertical-align:top;text-align:left}
th{background:var(--head);position:sticky;top:0}td.n{text-align:right;white-space:nowrap}td.w{white-space:nowrap;font-size:12px}
tr.bullish td:first-child{border-left:4px solid var(--bu2)}tr.bearish td:first-child{border-left:4px solid var(--be2)}tr.mixed td:first-child{border-left:4px solid var(--mx2)}
.tag{display:inline-block;padding:1px 7px;border-radius:9px;font-size:12px;font-weight:600}.tag.bullish{background:var(--bu);color:var(--bu2)}.tag.bearish{background:var(--be);color:var(--be2)}.tag.mixed{background:var(--mx);color:var(--mx2)}
.kpi{display:flex;flex-wrap:wrap;gap:10px}.kpi div{border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:130px}.kpi b{display:block;font-size:20px}
details summary{cursor:pointer;color:var(--be2);font-size:12px;margin-top:4px}ul{margin:4px 0 4px 18px;padding:0}
"""
    ev_main = [e for e in events if not e.get("component")]
    FINDINGS = findings(per, moves, net, fails, cause_count, events)
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gold Rules Backtest{'' if YEARS == 1 else f' {YEARS}Y'}</title><style>{css}</style></head><body>
<h1>Gold rules backtest, {span}: {p0s} to {p1s} (US Eastern time)</h1>
<p class="m">Every gold rule in the project (TA Section 34 and other TA/KD gold items, the 2026 document's gold section, your Sun notes U1–U4), recomputed with the Swiss-Ephemeris engine (Lahiri, mean node, whole-sign drishti) and scored against COMEX gold futures daily closes (Yahoo Finance GC=F continuous front month). Gold went from {CL[I0]:,.1f} ({D[I0]:%d %b %Y}) to {CL[I1]:,.1f} ({D[I1]:%d %b %Y}), {year_ret:+.1f}%, peaking at {CL[imax]:,.1f} on {D[imax]:%d %b %Y} (largest one-day fall {min(pct(i - 1, i) for i in range(I0 + 1, I1 + 1)):+.1f}%).</p>
<div class="kpi"><div>Rules checked (U2, U4 split by planet)<b>{len(main_rules)}</b></div><div>Rules that fired<b>{sum(1 for p in main_rules if p['n'])}</b></div><div>Scored occurrences<b>{dec + tot['FLAT']}</b></div>
<div>Worked<b style="color:var(--bu2)">{tot['WORKED']}</b></div><div>Failed<b style="color:var(--be2)">{tot['FAILED']}</b></div><div>Flat (&lt;0.5%)<b>{tot['FLAT']}</b></div>
<div>Hit rate<b>{tot['WORKED'] / dec * 100:.0f}%</b></div><div>Rules: worked / mixed / failed<b>{len(worked_rules)} / {len(mixed_rules)} / {len(failed_rules)}</b></div></div>
{FINDINGS}
<h2>How each occurrence was scored</h2>
<ul class="m"><li><b>Entry</b> = the last daily close before the event (events at or after 17:00 ET count from the next session; panchang day-rules from that day's open).</li>
<li><b>Windows</b> of 3 days or more (a planet in a nakshatra or sign, Sun contacts…) are scored from entry to the last close inside the window, clipped to the backtest period. <b>Instants and short windows</b> (new moon, darshan, rise/set, ingress, vedha starts) are scored on the 5-trading-day move; 1-, 3- and 10-day moves are shown as a sensitivity check.</li>
<li>Moves under ±0.5% are <b>FLAT</b>. Rules whose verdict is Mixed or Neutral (both vedha kinds at once; the Indian festival-demand dates) are listed but <b>not scored</b>.</li>
<li><b>Hit rate</b> = worked ÷ (worked + failed); flat occurrences are left out of both.</li>
<li><b>Base rate</b> = the hit rate a rule would get by chance: among all windows of the same length <i>in the same backtest year</i> that moved more than 0.5%, the share that moved the rule's way. Over the whole period a 5-day window that moved went up {BASE[5]['cond_up'] * 100:.0f}% of the time, so a bullish rule needs to beat {BASE[5]['cond_up'] * 100:.0f}% and a bearish rule {100 - BASE[5]['cond_up'] * 100:.0f}% to show any edge. Using each year's own base rate means a bullish rule gets no credit just for firing in a rising year.</li>
<li><b>Rule verdict</b>: Worked = hit rate at least 10 points above its base rate and the average move went the stated way; Failed = at least 10 points below and the average move went the wrong way; otherwise Mixed.""" + (""" <b>p-value</b> = the chance of doing at least this well by luck at the base rate (one-sided binomial); green if below 0.05, red if the rule did significantly <i>worse</i> than chance. The per-year columns show worked/decided in each Nov–Nov year, so a rule that only worked in one year stands out.""" if YEARS > 1 else """ Most rules fire only 1–6 times a year, so <b>one year is not enough to be statistically sure of any single rule</b>: read these numbers as evidence, not proof.""") + f"""</li></ul>
<div class="wrap"><table><thead><tr><th>Horizon</th><th>Rose &gt;0.5%</th><th>Fell &gt;0.5%</th><th>Of moves &gt;0.5%, share up (base rate for bullish rules)</th><th>Windows</th>{''.join(f"<th>{year_label(k)} share up</th>" for k in range(YEARS) if YEARS > 1)}</tr></thead><tbody>{base_tbl}</tbody></table></div>
<div class="wrap"><table><thead><tr><th>Backtest year</th><th>Gold at start</th><th>Gold at end</th><th>Change</th><th>Rule occurrences worked</th><th>Failed</th></tr></thead><tbody>{yr_rows}</tbody></table></div>

<h2>Scorecard by rule</h2>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Stated effect</th><th>Fired</th><th>Worked</th><th>Failed</th><th>Flat</th><th>Not scored</th><th>Hit rate</th><th>Base rate</th><th>Avg move in stated direction</th><th>Verdict</th>{yhead}<th>Instant-horizon check (hits/decided)</th></tr></thead>
<tbody>{''.join(rule_row(p) for p in sorted(main_rules, key=(lambda p: (p['hit_rate'] is None, -(p['hit_rate'] or 0), -p['n'])) if YEARS == 1 else (lambda p: (p['hit_rate'] is None, -(p['worked'] + p['failed']), -(p['hit_rate'] or 0)))))}</tbody></table></div>
<h3>Your Sun notes as one combined model</h3>
<p class="m">U2 and U4 are scored above per contact planet (U2 – Venus, U2 – Mercury, U2 – Jupiter, U2 – waxing Moon; U4 – Saturn, U4 – Rahu), because the whole rule's window restarts each time the set of contacts changes. Here every Sun-state stretch is scored by its rise-minus-fall count across U1–U4 (the Moon left out, as in the gold report's timeline; stretches with equal counts are not scored).</p>
<div class="wrap"><table><thead><tr><th>Component</th><th>Stated effect</th><th>Fired</th><th>Worked</th><th>Failed</th><th>Flat</th><th>Not scored</th><th>Hit rate</th><th>Base rate</th><th>Avg move in stated direction</th><th>Verdict</th>{yhead}<th>Instant-horizon check</th></tr></thead>
<tbody>{''.join(rule_row(p) for p in comp)}</tbody></table></div>

<h2>Do the rules add up? Net signal each day vs the next move</h2>
<p class="m">Each trading day: (number of distinct bullish gold rules active) − (number of distinct bearish gold rules active), with instants counted as active for one week; the combined Sun model is left out so nothing is counted twice. Correlation of that net count with the next day's return: <b>{net['corr1']:+.3f}</b>; with the next 5 days: <b>{net['corr5']:+.3f}</b> (0 = no relation, positive = the rules pointed the right way).</p>
<div class="wrap"><table><thead><tr><th>Days when…</th><th>Days</th><th>Avg next-day move</th><th>Next day up</th><th>Avg next-5-day move</th><th>Next 5 days up</th></tr></thead><tbody>{nb}</tbody></table></div>

<h2>Why rules failed: what keeps showing up</h2>
<p class="m">Each condition is checked for every failed occurrence <i>and</i> every occurrence that worked. A condition only helps explain failures if it is clearly more common among the failures; "Sun contacts" are read at the start of the occurrence. These are pointers, not proof of cause.</p>
{''.join(f"""<h3>{tone} rules</h3><div class="wrap"><table><thead><tr><th>Condition on the sky</th><th>In failed occurrences</th><th>In occurrences that worked</th><th>Difference</th></tr></thead><tbody>""" + ''.join(f'<tr><td>{html.escape(k)}</td><td class="n">{f_}/{nf} ({f_ / max(nf, 1) * 100:.0f}%)</td><td class="n">{w_}/{nw} ({w_ / max(nw, 1) * 100:.0f}%)</td><td class="n"><b>{(f_ / max(nf, 1) - w_ / max(nw, 1)) * 100:+.0f} pts</b></td></tr>' for k, f_, nf, w_, nw in rows_) + "</tbody></table></div>" for tone, rows_ in cause_count.items())}
<p class="m">Opposite-tone rules most often active during failures: {html.escape('; '.join(f'{k} ({v})' for k, v in opp_titles.most_common(10)))}.</p>

<h2>The biggest 5-day moves: what the rules said</h2>
<p class="m">The {sum(1 for m in moves if m['dir'] == 'fall')} largest non-overlapping 5-trading-day falls and rises, the gold rules active then (bullish : bearish count), and the sky.</p>
<div class="wrap"><table><thead><tr><th>Dates</th><th>Move</th><th>Bull : Bear</th><th>Rules active</th><th>Sky (Sun = gold karaka in your notes; Jupiter; transits in the interval)</th></tr></thead><tbody>{mv_rows}</tbody></table></div>

<h3>Which sky factors were present in the biggest moves?</h3>
<p class="m">Each factor is tested at the middle of each 5-day move. "All windows" is how often the factor was present across every 5-day window of the period; a factor only says something if it shows up clearly more often in the falls than in the rises (or the reverse) <i>and</i> more often than its all-period share. {sum(1 for m in moves if m['dir'] == 'fall')} moves each way is a small sample; treat this as a lead to examine, not a rule.</p>
<div class="wrap"><table><thead><tr><th>Factor</th><th>In the biggest falls</th><th>In the biggest rises</th><th>All windows</th></tr></thead><tbody>{''.join(f"<tr><td>{html.escape(f['factor'])}</td><td class='n'>{f['falls']}/{f['n_falls']}</td><td class='n'>{f['rises']}/{f['n_rises']}</td><td class='n'>{f['all_pct']}%</td></tr>" for f in FT)}</tbody></table></div>

<h2>Every occurrence (failed ones carry a "Why it may have failed" panel)</h2>
<div class="wrap"><table><thead><tr><th>When (ET)</th><th>Rule</th><th>Stated</th><th>Price used</th><th>Move</th><th>1/3/10-day</th><th>Result</th></tr></thead>
<tbody>{''.join(ev_row(e) for e in ev_main)}</tbody></table></div>
<h3>Combined Sun-model occurrences</h3>
<div class="wrap"><table><thead><tr><th>When (ET)</th><th>Rule</th><th>Stated</th><th>Price used</th><th>Move</th><th>1/3/10-day</th><th>Result</th></tr></thead>
<tbody>{''.join(ev_row(e) for e in events if e.get('component'))}</tbody></table></div>
<p class="s">Source: tools/backtest_gold.py; prices build/pdfref/backtest/gold_GC_F_daily.csv (Yahoo Finance GC=F, downloaded 20 Nov 2026; the continuous contract rolls between months, which can add small jumps). Astronomy: build/astronomy_{P0.year}.json … _2026.json (tools/build_year.py). Rule texts and page references: build/pdfref/gold_2026-11-20_to_2027-12-31_ET.html and REFERENCE_PDF_RULES.md.</p>
</body></html>"""
    stem = f"gold_backtest_{P0:%Y-%m-%d}_to_2026-11-20_ET"
    (OUT / f"{stem}.html").write_text(page, encoding="utf-8")

    def ser(e):
        x = {k: v for k, v in e.items() if k not in ("eval_from", "eval_to")}
        for k in ("start", "end"):
            x[k] = x[k].astimezone(ET).isoformat() if x.get(k) else None
        x["day"] = x["day"].isoformat() if x.get("day") else None
        return x
    json.dump(dict(period=f"{P0:%Y-%m-%d}..2026-11-20", base_rates_by_year={year_label(k): v for k, v in BASE_Y.items()}, time_zone="America/New_York", prices="Yahoo Finance GC=F daily close",
                   flat_band_pct=FLAT, instant_horizon_days=H, base_rates=BASE, totals=dict(tot), rules=list(per.values()),
                   big_moves=moves, net_signal={k: v for k, v in net.items() if k != "series"}, events=[ser(e) for e in events]),
              open(OUT / f"{stem}.json", "w", encoding="utf-8"), indent=1, default=str)
    print(f"{len(events)} events; totals {dict(tot)}; rules {len(main_rules)}; worked/mixed/failed {len(worked_rules)}/{len(mixed_rules)}/{len(failed_rules)}")
    print("net corr", net["corr1"], net["corr5"], net["buckets"])


BASE = {}
BASE_Y = {}
FT = []
if __name__ == "__main__":
    main()
