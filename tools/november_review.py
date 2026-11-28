"""November 2026 review: every call the calendar made, scored against what the markets did, and what to tune.

    python tools/november_review.py      # after a price refresh (fetch_prices.py) and tools/week_deep_dive.py nov

Day data: the November days built with forward_daybyday.build for 1-30 Nov (combined model fitted only on data before
1 Nov, so out of sample), from the week_deep_dive day-data cache. Actual moves: the price files, with the model's own
definitions (model_check_60d / combined_probability): r1 = that session's close vs the previous close, r5 = the close 4
sessions later vs the previous close, big day = |r1| >= 2% (S&P, Sensex, gold) or 3.5% (silver). Sensex 27 Nov: Yahoo's
daily bar had no close when fetched; the quote's close (83,339.26, 15:32 IST) is used and marked.

A call passes when the market moved its way by 0.5% or more and fails when it moved the other way by 0.5% or more;
smaller moves are too small to count (section 6). Each pass rate is set against what calls with the same up/down mix
would score by chance, given how often the market rose in the same period (November here; each Nov-Nov year on the
long records), with a two-sided p-value.

Scored: every layer of forward_daybyday.score (recounted here and checked against it), the table labels by strength,
the model's up and down calls, the generated Solar return day calls, the deep-dive leans (event classes with a nominal
p < 0.05 on history to 31 Oct), the big-move warnings, and each table rule's November span. Where it failed: every
wrong table label and model call, with the rules behind it. Tuning: each candidate change is tested on the long records
(2000-2026; walk-forward 2013-2026 where one exists) and on 24 Sep - 27 Nov, never on November alone.
Writes build/pdfref/november_review_2026-11_ET.json (shown in the 2026 calendar).
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import importlib.util
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
MKS = ("spx", "sensex", "gold", "silver")
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}
SHORT = {"spx": "S&P", "sensex": "Sensex", "gold": "Gold", "silver": "Silver"}
BIG = {"gold": 2.0, "silver": 3.5, "spx": 2.0, "sensex": 2.0}
A, B = dt.date(2026, 11, 1), dt.date(2026, 11, 30)
LAST = dt.date(2026, 11, 27)
HIST_END = dt.date(2026, 10, 31)                               # long records stop before November
OVERRIDE = {("sensex", dt.date(2026, 11, 27)): 83339.26}       # Yahoo quote close; the daily bar's close was empty
FLAT = 0.5
HALF = dt.date(2013, 1, 1)
INNER = dt.date(2007, 1, 1)                                    # layer choice inside 2000-2012: fit before, score after
WF_LABELS = dt.date(2013, 11, 20)                              # gold / silver labels: leads re-picked on data before this
PUB = {"spx": dt.date(2026, 11, 23), "sensex": dt.date(2026, 11, 23), "gold": dt.date(2026, 11, 22), "silver": dt.date(2026, 11, 22)}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


def sgn(v):
    return 1 if v > 0 else -1 if v < 0 else 0


def direction(sig):
    return 1 if str(sig).startswith("Bullish") else -1 if str(sig).startswith("Bearish") else 0


def band(v, b, lo=2, hi=2):
    if v is None or b is None:
        return 0
    return 1 if v >= b + hi else -1 if v <= b - lo else 0


def pb_two(k, probs):
    """Two-sided p of k successes when trial i succeeds with probability probs[i] (exact up to 600 trials)."""
    n = len(probs)
    if not n:
        return None
    if n <= 600:
        dist = [1.0]
        for q in probs:
            new = [0.0] * (len(dist) + 1)
            for i, v in enumerate(dist):
                new[i] += v * (1 - q)
                new[i + 1] += v * q
            dist = new
        obs = dist[k]
        return round(min(1.0, sum(v for v in dist if v <= obs * (1 + 1e-9))), 4)
    mu, var = sum(probs), sum(q * (1 - q) for q in probs)
    return round(math.erfc(abs(k - mu) / math.sqrt(var) / math.sqrt(2)), 4) if var else None


def judge(items, overlap=1):
    """items: (call, move, up share of the period). Moves under 0.5% are too small to count. overlap=5 for 5-session moves
    on consecutive days: they share most of their sessions, so the p-value uses a variance 5 times larger."""
    its = [(c, r, u) for c, r, u in items if c and r is not None and abs(r) >= FLAT]
    n = len(its)
    if not n:
        return dict(n=0, right=0, wrong=0, hit=None, exp=None, edge=None, p=None, up_calls=0, down_calls=0)
    right = sum((r > 0) == (c > 0) for c, r, u in its)
    probs = [u if c > 0 else 1 - u for c, r, u in its]
    exp = sum(probs)
    if overlap > 1:
        var = sum(q * (1 - q) for q in probs) * overlap
        p = round(math.erfc(abs(right - exp) / math.sqrt(var) / math.sqrt(2)), 4) if var else None
    else:
        p = pb_two(right, probs)
    return dict(n=n, right=right, wrong=n - right, hit=round(right / n * 100, 1), exp=round(exp / n * 100, 1), edge=round((right - exp) / n * 100, 1),
                p=p, up_calls=sum(c > 0 for c, r, u in its), down_calls=sum(c < 0 for c, r, u in its))


def bh(ps):
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    q = [1.0] * m
    prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        prev = min(prev, ps[i] * m / rank)
        q[i] = round(prev, 4)
    return q


def actual_moves():
    MC = load(ROOT / "tools" / "model_check_60d.py", "mc_nr")
    out, marked = {}, []
    for mk in MKS:
        P = MC.prices(mk, LAST)
        for (m, d), v in OVERRIDE.items():
            if m == mk and d not in P:
                P[d] = v
                marked.append(f"{SHORT[mk]} {d:%d %b}: {v:,.2f} (Yahoo quote close; the daily bar had none)")
        P = dict(sorted(P.items()))
        D = list(P)
        out[mk] = {}
        for i in range(1, len(D)):
            d = D[i]
            if not (A <= d <= LAST):
                continue
            r1 = (P[d] / P[D[i - 1]] - 1) * 100
            r5 = (P[D[i + 4]] / P[D[i - 1]] - 1) * 100 if i + 4 < len(D) else None
            out[mk][d.isoformat()] = dict(r1=round(r1, 3), r5=None if r5 is None else round(r5, 3), big=abs(r1) >= BIG[mk],
                                          close=P[d], prev=P[D[i - 1]])
    return out, marked, MC


def up_shares(moves):
    """Up share of moves of 0.5% or more (same day, 5 sessions)."""
    r1 = [a["r1"] for a in moves.values() if abs(a["r1"]) >= FLAT]
    r5 = [a["r5"] for a in moves.values() if a["r5"] is not None and abs(a["r5"]) >= FLAT]
    return (sum(v > 0 for v in r1) / len(r1) if r1 else 0.5, sum(v > 0 for v in r5) / len(r5) if r5 else 0.5)


# ------------------------------------------------------------------ the November scorecard
FD_LAYERS = {"Signal table", "Combined probability, all layers", "Combined probability, kept layers", "Combined lean, every day (above / below base)",
             "Supported catalogue rules (net bullish - bearish)", "Calendar-layer verdicts (net)", "Model v1.0 (Ch.41 + Shadbala)",
             "USA gochara", "NYSE gochara", "USA Chandra bala", "NYSE Chandra bala", "USA Tara bala", "NYSE Tara bala",
             "Solar return: day-by-day forecasts", "Solar return: month view (bearish)", "Solar return: Jupiter sextile Venus (bullish)",
             "Solar return: Sun square Mars (bearish)", "Mars-Jupiter-node lead (bearish)"}


def layer_calls(x, mk, pr, fdays):
    """(layer, call for the day, call for 5 sessions): forward_daybyday.score's layers with its definitions, plus extras."""
    out = []
    sg = x["signals"][NAME[mk]][0]
    s = direction(sg["sig"])
    out.append(("Signal table", s, s))
    if s:
        out.append((f"Signal table: {sg.get('st') or 'no strength'} labels", s, s))
        if sg.get("st") in ("Moderate", "High"):
            out.append(("Signal table: Moderate or High labels", s, s))
    for name, key in (("Combined probability, all layers", "all"), ("Combined probability, kept layers", "kept")):
        out.append((name, band(pr[key]["up1"], pr["base"]["up1"]), band(pr[key]["up5"], pr["base"]["up5"])))
    out.append(("Combined lean, every day (above / below base)", 1 if pr["all"]["up1"] > pr["base"]["up1"] else -1,
                1 if pr["all"]["up5"] > pr["base"]["up5"] else -1))
    c1 = band(pr["all"]["up1"], pr["base"]["up1"])
    if c1:
        out.append((f"Combined probability, all layers: {'up' if c1 > 0 else 'down'} calls", c1, 0))
    tl = x["tally"][mk]
    n = sgn(len(tl["bull"]) - len(tl["bear"]))
    out.append(("Supported catalogue rules (net bullish - bearish)", n, n))
    cal = sgn(sum(direction(c["verdict"]) for c in x["calendar"] if c["market"] == mk))
    out.append(("Calendar-layer verdicts (net)", cal, cal))
    if mk == "gold":
        bias = x["v1"]["bias"]
        v = 1 if "bullish" in bias else -1 if "bearish" in bias else 0
        out.append(("Model v1.0 (Ch.41 + Shadbala)", v, v))
    if mk == "spx":
        st = pr["st"]
        for nm in ("USA", "NYSE"):
            for lab, key, f in ((f"{nm} gochara", f"{nm} gochara", lambda v: {"favourable": 1, "adverse": -1}.get(v, 0)),
                                (f"{nm} Chandra bala", f"{nm} chandra", lambda v: 1 if v == "good" else -1),
                                (f"{nm} Tara bala", f"{nm} tara", lambda v: {"good": 1, "bad": -1}.get(v, 0))):
                v = f(st[key])
                out.append((lab, v, v))
        v = {"up": 1, "down": -1}.get(fdays.get(x["date"]), 0)
        out.append(("Solar return: day-by-day forecasts", v, v))
        out.append(("Solar return: month view (bearish)", -1, -1))
        ar = x["author"]["rules"]
        v = 1 if any(r.startswith("Jupiter sextile Venus") for r in ar) else 0
        out.append(("Solar return: Jupiter sextile Venus (bullish)", v, v))
        v = -1 if any(r.startswith("Sun square Mars (") for r in ar) else 0
        out.append(("Solar return: Sun square Mars (bearish)", v, v))
        v = -1 if x["mjn"] else 0
        out.append(("Mars-Jupiter-node lead (bearish)", v, v))
        v = direction(x.get("sr_call") or "")
        out.append(("Solar return: generated day call", v, v))
    return out


def scorecard(days, act):
    ups = {mk: up_shares(act[mk]) for mk in MKS}
    items = collections.defaultdict(lambda: dict(d1=[], d5=[]))
    AF = load(ROOT / "tools" / "author_forecasts.py", "af_nr")
    fdays = {d: v for f in AF.FORECASTS if f["kind"] == "days" for d, v in f["days"].items()}
    for x in days:
        if x["date"] > str(LAST):
            continue
        for mk, pr in x["prob"].items():
            a = pr.get("actual")
            if not a:
                continue
            for layer, c1, c5 in layer_calls(x, mk, pr, fdays):
                if c1:
                    items[(layer, mk)]["d1"].append((x["date"], c1, a["r1"]))
                if c5 and a["r5"] is not None:
                    items[(layer, mk)]["d5"].append((x["date"], c5, a["r5"]))
    rows = []
    for (layer, mk), v in items.items():
        row = dict(layer=layer, market=mk, fd=layer in FD_LAYERS)
        for h, i in (("d1", 0), ("d5", 1)):
            its = v[h]
            j = judge([(c, r, ups[mk][i]) for d, c, r in its], overlap=1 if h == "d1" else 5)
            row[h] = dict(calls=len(its), flat=sum(1 for d, c, r in its if abs(r) < FLAT),
                          sign_right=sum(1 for d, c, r in its if r != 0 and (r > 0) == (c > 0)), sign_n=sum(1 for d, c, r in its if r != 0), **j)
        rows.append(row)
    return rows, ups


def check_fd(rows, fd):
    """Recount check: every forward_daybyday.score row must match this scorecard's sign-rule counts."""
    by = {(r["layer"], r["market"]): r for r in rows}
    ok, diffs = 0, []
    for r in fd["rows"]:
        m = by.get((r["method"], r["market"]))
        got = (m["d1"]["sign_right"], m["d1"]["sign_n"], m["d5"]["sign_right"], m["d5"]["sign_n"]) if m else (0, 0, 0, 0)
        want = (r["d1_right"], r["d1_calls"], r["d5_right"], r["d5_calls"])
        if got == want:
            ok += 1
        else:
            diffs.append(dict(layer=r["method"], market=r["market"], fd=want, here=got))
    return dict(matched=ok, of=len(fd["rows"]), diffs=diffs)


# ------------------------------------------------------------------ reasons and spans
def market_reasons(MC):
    """S&P / Sensex: the table rules behind each November day (rebuilt days from the rules; published days from the table)."""
    lab, why, rules = MC.market_labels(dt.date(2026, 10, 1), PUB["spx"] - dt.timedelta(days=1), ids=True)
    days = {mk: {d: list(v) for d, v in why[mk].items()} for mk in ("spx", "sensex")}
    j = json.load(open(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json"))
    titles = {k: v["title"] for k, v in j["rules"].items()}
    titles.update({k: v["title"] for k, v in rules.items()})
    tone = {k: v["tone"] for k, v in j["rules"].items()}
    tone.update({k: v["tone"] for k, v in rules.items()})
    for mk in ("spx", "sensex"):
        for r in j["tables"][mk]:
            d, e = dt.date.fromisoformat(str(r["frm"])[:10]), dt.date.fromisoformat(str(r["to"])[:10])
            while d <= min(e, B):
                days[mk][d] = list(r.get("ids") or [])
                d += dt.timedelta(days=1)
    return days, titles, tone, j["rules"]


def spans(rdays, titles, tone, act_all, MC):
    """Each table rule's November span, scored as its record is: from the last close before it to its last day."""
    out = []
    for mk in ("spx", "sensex"):
        P = MC.prices(mk, LAST)
        for (m, d), v in OVERRIDE.items():
            if m == mk and d not in P:
                P[d] = v
        D = sorted(P)
        by = collections.defaultdict(list)
        for d, ids in rdays[mk].items():
            for i in ids:
                by[i].append(d)
        for rid, ds in by.items():
            ds = sorted(set(ds))
            runs, cur = [], None
            for d in ds:
                if cur and (d - cur[1]).days <= 1:
                    cur[1] = d
                else:
                    cur = [d, d]
                    runs.append(cur)
            for d0, d1 in runs:
                if d1 < A or d0 > LAST:
                    continue
                before = [x for x in D if x < d0]
                upto = [x for x in D if x <= min(d1, LAST)]
                if not before or not upto or upto[-1] <= before[-1]:
                    continue
                ret = (P[upto[-1]] / P[before[-1]] - 1) * 100
                c = 1 if tone.get(rid) == "Bullish" else -1
                out.append(dict(market=mk, rule=titles.get(rid, rid), id=rid, tone=tone.get(rid), frm=str(d0), to=str(d1), open=d1 > LAST,
                                entry=str(before[-1]), exit=str(upto[-1]), ret=round(ret, 2),
                                result="too small" if abs(ret) < FLAT else "passed" if (ret > 0) == (c > 0) else "failed"))
    return sorted(out, key=lambda s: (s["frm"], s["market"]))


# ------------------------------------------------------------------ main
def main():
    cache = OUT / "backtest" / f"days_{A}_to_{B}.json.gz"
    if not cache.exists():
        sys.exit("run: python tools/week_deep_dive.py nov   (it builds the November day data)")
    days = json.load(gzip.open(cache, "rt", encoding="utf-8"))["days"]
    act, marked, MC = actual_moves()
    FD = load(ROOT / "tools" / "forward_daybyday.py", "fd_nr")
    AF = load(ROOT / "tools" / "author_forecasts.py", "af_nr2")
    for x in days:
        for mk, pr in x["prob"].items():
            a = act[mk].get(x["date"])
            if a:
                pr["actual"] = a
    fd = FD.score([x for x in days if x["date"] <= str(LAST)], AF)
    rows, ups = scorecard(days, act)
    chk = check_fd(rows, fd)

    # ---- where it failed: wrong labels and model calls, with the rules behind them
    rdays, titles, tone, trules = market_reasons(MC)
    wrong, reasons = collections.defaultdict(list), collections.defaultdict(lambda: dict(passed=0, failed=0, small=0))
    for x in days:
        if x["date"] > str(LAST):
            continue
        d = dt.date.fromisoformat(x["date"])
        for mk in MKS:
            pr = x["prob"].get(mk)
            a = pr.get("actual") if pr else None
            if not a:
                continue
            sg = x["signals"][NAME[mk]][0]
            call = direction(sg["sig"])
            if mk in ("spx", "sensex"):
                why = [titles.get(i, i) for i in rdays[mk].get(d, [])]
            elif str(sg.get("why", "")).startswith("rebuilt"):
                why = ["(label rebuilt from the table's rules; the reasons are not stored for days before 22 Nov)"]
            else:
                why = sg["why"] if isinstance(sg.get("why"), list) else [w.strip() for w in str(sg.get("why", "")).split(";") if w.strip()]
            res = "small" if abs(a["r1"]) < FLAT else "passed" if (a["r1"] > 0) == (call > 0) else "failed"
            if call:
                for w in why or ["(no reason given)"]:
                    reasons[(mk, w, sg["sig"])][res] += 1
                if res == "failed":
                    wrong[mk].append(dict(date=x["date"], weekday=x["weekday"], layer="table label", call=f"{sg['sig']} {sg.get('st') or ''}".strip(),
                                          move=a["r1"], why="; ".join(why)))
            c = band(pr["all"]["up1"], pr["base"]["up1"])
            if c and abs(a["r1"]) >= FLAT and (a["r1"] > 0) != (c > 0):
                wrong[mk].append(dict(date=x["date"], weekday=x["weekday"], layer="combined model", move=a["r1"],
                                      call=f"{'up' if c > 0 else 'down'} ({pr['all']['up1']:.0f}% vs normal {pr['base']['up1']:.0f}%)",
                                      why=", ".join(f"{k}: {s}" for k, s in pr["st"].items() if k in ("table", "v1", "bigmove", "NYSE gochara"))))
    sp = spans(rdays, titles, tone, act, MC)

    # ---- deep-dive leans on their November instance (history to 31 Oct)
    TM = load(ROOT / "tools" / "new_sources_test.py", "nst_nr")
    MK = TM.markets()
    for m in MK.values():
        m.p1 = LAST
    lean_items, lean_list = collections.defaultdict(list), []
    for f in sorted(glob.glob(str(OUT / "deep_dive_2026-11-*_ET.json"))):
        dd = json.load(open(f))
        for d in dd["days"]:
            for e in d["events"]:
                c = dd["classes"][e["key"]]
                for mk in MKS:
                    for h in ("h1", "h5"):
                        s = c["stats"][mk][h]
                        if (s.get("p2") or 1) >= 0.05:
                            continue
                        lean = 1 if s["up_pct"] > s["base"] else -1
                        r = MK[mk].score(TM.ev(dt.datetime.fromisoformat(e["utc"]), "Bullish", None, h=1 if h == "h1" else 5))
                        if r and r["entry"] >= dt.date(2026, 10, 30):
                            lean_items[mk].append((lean, r["ret"], ups[mk][0 if h == "h1" else 1]))
                            lean_list.append(dict(date=d["date"], event=c["label"], market=mk, horizon="next session" if h == "h1" else "5 sessions",
                                                  lean="up" if lean > 0 else "down", hist=f"{s['up_pct']}% up vs {s['base']}%, p {s['p2']}",
                                                  move=round(r["ret"], 2), result="small" if abs(r["ret"]) < FLAT else "passed" if (r["ret"] > 0) == (lean > 0) else "failed"))
    leans = {mk: judge(v) for mk, v in lean_items.items()}
    leans["all"] = judge([t for v in lean_items.values() for t in v])

    # ---- big days and warnings
    bigs = {}
    for mk in MKS:
        allx = [x for x in days if mk in x["prob"] and x["prob"][mk].get("actual")]
        warn = [x for x in allx if x["prob"][mk]["all"]["big"] >= x["prob"][mk]["base"]["big"] + 2]
        big_days = [x for x in allx if x["prob"][mk]["actual"]["big"]]
        watch = [x for x in allx if any(w["market"] == mk for w in x["watch"])]
        vol = [x for x in allx if x["vol"].get(mk)]
        bigs[mk] = dict(sessions=len(allx), big_days=[dict(date=x["date"], move=x["prob"][mk]["actual"]["r1"], warned=x in warn, watch=x in watch, vol=x in vol) for x in big_days],
                        warned=len(warn), warned_big=sum(x["prob"][mk]["actual"]["big"] for x in warn), watch_days=len(watch),
                        watch_big=sum(x["prob"][mk]["actual"]["big"] for x in watch), vol_days=len(vol), vol_big=sum(x["prob"][mk]["actual"]["big"] for x in vol))

    # ---- what the month did
    month = {}
    for mk in MKS:
        r = [a["r1"] for d, a in sorted(act[mk].items())]
        cl = [a for d, a in sorted(act[mk].items())]
        month[mk] = dict(sessions=len(r), up=sum(v > 0 for v in r), down=sum(v < 0 for v in r), small=sum(abs(v) < FLAT for v in r),
                         big=sum(abs(v) >= BIG[mk] for v in r), up_share=round(ups[mk][0] * 100), up5_share=round(ups[mk][1] * 100),
                         change=round((cl[-1]["close"] / cl[0]["prev"] - 1) * 100, 2))

    tuning = tune(days, act, MC)
    res = dict(made=dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z"), start=str(A), last=str(LAST), hist_end=str(HIST_END), marked=marked,
               month=month, rows=rows, check_fd=chk, fd_pooled=fd["pooled"], leans=leans, lean_list=lean_list, bigs=bigs, spans=sp,
               wrong={k: v for k, v in wrong.items()},
               moves={mk: {d: dict(r1=a["r1"], r5=a["r5"], big=a["big"]) for d, a in act[mk].items()} for mk in MKS},
               reasons=sorted([dict(market=mk, reason=w, call=s, **c) for (mk, w, s), c in reasons.items()], key=lambda r: -(r["passed"] + r["failed"] + r["small"])),
               tuning=tuning)
    res["recommendations"] = recommend(res)
    (OUT / "november_review_2026-11_ET.json").write_text(json.dumps(res, indent=1, default=str))
    report(res)


# ------------------------------------------------------------------ tuning on the long records
def tune(days, act, MC):
    out = {}
    CP = load(ROOT / "tools" / "combined_probability.py", "cp_nr")
    cp = json.load(open(OUT / "combined_probability_60d_ET.json"))
    data = CP.build(HIST_END)
    yr = {}
    for mk, rs in data.items():
        c = collections.defaultdict(lambda: [0, 0, 0, 0])
        for r in rs:
            y = nov_year(r["d"])
            if abs(r["r1"]) >= FLAT:
                c[y][0] += r["r1"] > 0
                c[y][1] += 1
            if r["r5"] is not None and abs(r["r5"]) >= FLAT:
                c[y][2] += r["r5"] > 0
                c[y][3] += 1
        yr[mk] = {y: (a / b if b else 0.5, e / f if f else 0.5) for y, (a, b, e, f) in c.items()}
    mv = {mk: {r["d"]: r for r in rs} for mk, rs in data.items()}

    # 1. each S&P / Sensex table rule as a day-by-day call, 2000-2026 (its published record is per span)
    why = {"spx": {}, "sensex": {}}
    rules = {}
    for y in range(2000, HIST_END.year + 1):
        _, w, rules = MC.market_labels(dt.date(y, 1, 1), min(dt.date(y, 12, 31), HIST_END), ids=True)
        for mk in why:
            why[mk].update(w[mk])
    trules = json.load(open(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json"))["rules"]
    per_rule = []
    for rid, ru in rules.items():
        c = 1 if ru["tone"] == "Bullish" else -1
        for mk in ("spx", "sensex"):
            it = collections.defaultdict(list)
            for d, ids in why[mk].items():
                if rid in ids and d in mv[mk] and d >= dt.date(2000, 11, 20):
                    r = mv[mk][d]
                    u1, u5 = yr[mk][nov_year(d)]
                    it["all"].append((c, r["r1"], u1))
                    it["a" if d < HALF else "b"].append((c, r["r1"], u1))
                    it["d5"].append((c, r["r5"], u5))
            per_rule.append(dict(id=rid, rule=ru["title"], tone=ru["tone"], strength=ru["st"], market=mk, record=trules.get(rid, {}).get("record"),
                                 day=judge(it["all"]), first_half=judge(it["a"]), second_half=judge(it["b"]), five=judge(it["d5"], overlap=5)))
    for r, q in zip(per_rule, bh([r["day"]["p"] if r["day"]["p"] is not None else 1 for r in per_rule])):
        r["q"] = q
    out["rules_per_day"] = per_rule

    # 2. labels by strength, every day
    lab = {}
    for mk in MKS:
        key, lo, src = ("st", dt.date(2000, 11, 20), "rebuilt from the table's rules, 2000-2026 (the rules were chosen on this period)") if mk in ("spx", "sensex") \
            else ("st_wf", WF_LABELS, "walk-forward: the table's data-picked parts re-picked on 2000-2013, scored 2013-2026")
        res = {}
        for name, keep in (("Low", lambda s: s == "Low"), ("Moderate", lambda s: s == "Moderate"), ("High", lambda s: s == "High"),
                           ("Moderate or High", lambda s: s in ("Moderate", "High")), ("Any strength", lambda s: True)):
            for h in ("d1", "d5"):
                it = []
                for r in data[mk]:
                    if r["d"] < lo:
                        continue
                    t = r[key]["table"].split()
                    if t and t[0] in ("Bullish", "Bearish") and keep(t[1] if len(t) > 1 else ""):
                        u = yr[mk][nov_year(r["d"])]
                        it.append((1 if t[0] == "Bullish" else -1, r["r1"] if h == "d1" else r["r5"], u[0] if h == "d1" else u[1]))
                res[f"{name}|{h}"] = judge(it, overlap=1 if h == "d1" else 5)
        if mk in ("spx", "sensex"):
            for name, keep in (("Low", "Low"), ("Moderate or High", ("Moderate", "High"))):
                it = []
                for r in data[mk]:
                    t = r["st"]["table"].split()
                    if r["d"] >= HALF and t and t[0] in ("Bullish", "Bearish") and len(t) > 1 and t[1] in keep:
                        it.append((1 if t[0] == "Bullish" else -1, r["r1"], yr[mk][nov_year(r["d"])][0]))
                res[f"{name}, 2013-2026|d1"] = judge(it)
        lab[mk] = dict(source=src, rows=res)
    # S&P / Sensex labels, walk-forward: rules picked on their 2000-2013 records only, labels scored 2013-2026
    MS = load(ROOT / "tools" / "market_signal_table.py", "mst_nr")

    def pick_h1(s, n):
        x, y = s["h1"], n["h1"]
        if x["hit_rate"] is None or y["hit_rate"] is None or x["worked"] + x["failed"] < 8 or y["worked"] + y["failed"] < 8:
            return None
        if not (x["hit_rate"] > x["base_rate"] and y["hit_rate"] > y["base_rate"]) or min(x["p_value"], y["p_value"]) >= 0.05:
            return None
        return MS.strength(x["p_value"], y["p_value"])
    wf_lab, wf_rules = {"spx": {}, "sensex": {}}, {}
    for y in range(2000, HIST_END.year + 1):
        lw, _, wf_rules = MC.market_labels(dt.date(y, 1, 1), min(dt.date(y, 12, 31), HIST_END), ids=True, pick=pick_h1)
        for mk in wf_lab:
            wf_lab[mk].update(lw[mk])
    for mk in ("spx", "sensex"):
        res = {}
        for name, keep in (("Low", lambda s: s == "Low"), ("Moderate", lambda s: s == "Moderate"), ("High", lambda s: s == "High"),
                           ("Moderate or High", lambda s: s in ("Moderate", "High")), ("Any strength", lambda s: True)):
            for h in ("d1", "d5"):
                it = []
                for d, (sig, st) in wf_lab[mk].items():
                    if d < WF_LABELS or d not in mv[mk] or not keep(st):
                        continue
                    r, u = mv[mk][d], yr[mk][nov_year(d)]
                    it.append((1 if sig == "Bullish" else -1, r["r1"] if h == "d1" else r["r5"], u[0] if h == "d1" else u[1]))
                res[f"{name}|{h}"] = judge(it, overlap=1 if h == "d1" else 5)
        lab[mk]["walk_forward"] = dict(source="walk-forward: rules picked on their 2000-2013 records only (both indices beat the base, p < 0.05 on one), "
                                              "labels scored every day 2013-2026", rules=sorted(v["title"] for v in wf_rules.values()), rows=res)
    out["labels"] = lab

    # 3. the combined model's calls, walk-forward: weights fitted on 2000-2012, every day 2013 - 31 Oct 2026 scored
    model, preds = {}, {}
    for mk, rs in data.items():
        tr = [r for r in rs if r["d"] < CP.SPLIT]
        te = [r for r in rs if CP.SPLIT <= r["d"] <= HIST_END]
        kept = cp["markets"][mk]["kept"]["up1"]
        inner_tr = [r for r in tr if r["d"] < INNER]
        inner_te = [r for r in tr if r["d"] >= INNER]
        kc = [L for L in CP.LAYERS[mk] if (CP.score(CP.fit(inner_tr, [L], "up1", "st_wf"), inner_te, "up1", "st_wf")["skill"] or 0) > 0]
        mkc = CP.fit(tr, kc, "up1", "st_wf") if kc else None
        bkc = mkc["base"] * 100 if mkc else None
        m1 = CP.fit(tr, CP.LAYERS[mk], "up1", "st_wf")
        m5 = CP.fit(tr, CP.LAYERS[mk], "up5", "st_wf")
        mk1 = CP.fit(tr, kept, "up1", "st_wf") if kept else None
        b1, b5 = m1["base"] * 100, m5["base"] * 100
        bk = mk1["base"] * 100 if mk1 else None
        pr = [dict(d=r["d"], p=CP.predict(m1, r, "st_wf") * 100, p5=CP.predict(m5, r, "st_wf") * 100,
                   pk=CP.predict(mk1, r, "st_wf") * 100 if mk1 else None, pc=CP.predict(mkc, r, "st_wf") * 100 if mkc else None,
                   label=r["st_wf"]["table"], r1=r["r1"], r5=r["r5"],
                   u1=yr[mk][nov_year(r["d"])][0], u5=yr[mk][nov_year(r["d"])][1]) for r in te]
        preds[mk] = (pr, b1)
        variants = {
            "Model call (2+ points from normal), all layers": [(band(r["p"], b1), r["r1"], r["u1"]) for r in pr],
            "Model call, kept layers (chosen on 2013-2026: not a clean test)": [(band(r["pk"], bk), r["r1"], r["u1"]) for r in pr] if mk1 else [],
            "Model call, layers chosen on 2000-2012 only": [(band(r["pc"], bkc), r["r1"], r["u1"]) for r in pr] if mkc else [],
            "Model up calls only": [(max(0, band(r["p"], b1)), r["r1"], r["u1"]) for r in pr],
            "Model down calls only": [(min(0, band(r["p"], b1)), r["r1"], r["u1"]) for r in pr],
            "Model: down calls only at 5+ points": [(-1 if r["p"] <= b1 - 5 else 0, r["r1"], r["u1"]) for r in pr],
        }
        model[mk] = dict(kept=kept, kept_clean=kc, base=round(b1, 1), rows={k: judge(v) for k, v in variants.items()})
        model[mk]["rows"]["Model call, 5 sessions"] = judge([(band(r["p5"], b5), r["r5"], r["u5"]) for r in pr], overlap=5)
        # label and model together (gold / silver walk-forward labels; S&P / Sensex rebuilt labels)
        ag, dis_l, dis_m = [], [], []
        for r in pr:
            lc, mc = direction(r["label"]), band(r["p"], b1)
            if lc and mc and lc == mc:
                ag.append((lc, r["r1"], r["u1"]))
            elif lc and mc:
                dis_l.append((lc, r["r1"], r["u1"]))
                dis_m.append((mc, r["r1"], r["u1"]))
        model[mk]["rows"]["Label and model agree"] = judge(ag)
        model[mk]["rows"]["Label and model disagree: the label's call"] = judge(dis_l)
        model[mk]["rows"]["Label and model disagree: the model's call"] = judge(dis_m)
    for mk in ("spx", "sensex"):
        rs = [dict(r, st_wf=dict(r["st_wf"], table=CP.tbl_state(wf_lab[mk].get(r["d"])))) for r in data[mk]]
        tr = [r for r in rs if r["d"] < WF_LABELS]
        te = [r for r in rs if WF_LABELS <= r["d"] <= HIST_END]
        m1 = CP.fit(tr, CP.LAYERS[mk], "up1", "st_wf")
        b1 = m1["base"] * 100
        it = [(band(CP.predict(m1, r, "st_wf") * 100, b1), r["r1"], yr[mk][nov_year(r["d"])][0]) for r in te]
        model[mk]["rows"]["Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)"] = judge(it)
        lt = [(direction(r["st_wf"]["table"]), r["r1"], yr[mk][nov_year(r["d"])][0]) for r in te]
        ag = [(c, r1, u) for (c, r1, u), (lc, _, _) in zip(it, lt) if c and c == lc]
        model[mk]["rows"]["Label and model agree, clean walk-forward"] = judge(ag)
    v1 = collections.defaultdict(list)
    for r in data["gold"]:
        c = 1 if "bullish" in r["st"]["v1"] else -1 if "bearish" in r["st"]["v1"] else 0
        u = yr["gold"][nov_year(r["d"])][0]
        v1["all"].append((c, r["r1"], u))
        v1["a" if r["d"] < HALF else "b"].append((c, r["r1"], u))
        v1["bull"].append((max(c, 0), r["r1"], u))
        v1["bear"].append((min(c, 0), r["r1"], u))
    out["model_v1"] = {k: judge(v) for k, v in v1.items()}
    out["model"] = model

    # 4. big-day warnings, walk-forward
    big = {}
    for mk, rs in data.items():
        tr = [r for r in rs if r["d"] < CP.SPLIT]
        te = [r for r in rs if CP.SPLIT <= r["d"] <= HIST_END]
        m = CP.fit(tr, CP.LAYERS[mk], "big", "st_wf")
        b = m["base"] * 100
        w = [r for r in te if CP.predict(m, r, "st_wf") * 100 >= b + 2]
        o = [r for r in te if CP.predict(m, r, "st_wf") * 100 < b + 2]
        k1, n1, k2, n2 = sum(r["big"] for r in w), len(w), sum(r["big"] for r in o), len(o)
        pool = (k1 + k2) / (n1 + n2)
        se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2)) if n1 and n2 else 0
        z = ((k1 / n1) - (k2 / n2)) / se if se else 0
        big[mk] = dict(warned=n1, warned_big=k1, warned_pct=round(k1 / n1 * 100, 1) if n1 else None, other=n2, other_big=k2,
                       other_pct=round(k2 / n2 * 100, 1) if n2 else None, p=round(math.erfc(abs(z) / math.sqrt(2)), 4) if se else None)
    out["big"] = big
    vf = {}
    for mk in ("spx", "sensex"):
        vf[mk] = {}
        for lo, hi, nm in ((dt.date(2000, 1, 1), HALF, "2000-2012"), (HALF, HIST_END + dt.timedelta(days=1), "2013-2026")):
            on = [r for r in data[mk] if lo <= r["d"] < hi and r["st"]["bigmove"] == "on"]
            off = [r for r in data[mk] if lo <= r["d"] < hi and r["st"]["bigmove"] == "off"]
            k1, n1, k2, n2 = sum(r["big"] for r in on), len(on), sum(r["big"] for r in off), len(off)
            pool = (k1 + k2) / (n1 + n2)
            se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2)) if n1 and n2 else 0
            z = (k1 / n1 - k2 / n2) / se if se else 0
            vf[mk][nm] = dict(on=n1, on_big=k1, on_pct=round(k1 / n1 * 100, 1) if n1 else None, off=n2, off_big=k2,
                              off_pct=round(k2 / n2 * 100, 1) if n2 else None, p=round(math.erfc(abs(z) / math.sqrt(2)), 4) if se else None)
    out["volatility_factors"] = vf

    # 5. 24 Sep - 27 Nov: the same rules on the two months before and including November
    recs = collections.defaultdict(list)
    for mk in MKS:
        wb = cp["markets"][mk]["window"]["up1"]["all"]["base"]
        for r in cp["markets"][mk]["days"]:
            if r["date"] < str(A):
                recs[mk].append(dict(p=r["p"]["up1"], b=wb, label=r["st"].get("table", "no signal"), r1=r["r1"]))
    for x in days:
        for mk, pr in x["prob"].items():
            a = pr.get("actual")
            if a and x["date"] <= str(LAST):
                sg = x["signals"][NAME[mk]][0]
                recs[mk].append(dict(p=pr["all"]["up1"], b=pr["base"]["up1"], label=(sg["sig"] + " " + (sg.get("st") or "")).strip(), r1=a["r1"]))
    win = {}
    for mk in MKS:
        dec = [r["r1"] for r in recs[mk] if abs(r["r1"]) >= FLAT]
        u = sum(v > 0 for v in dec) / len(dec) if dec else 0.5

        def strength(r):
            t = r["label"].split()
            return t[1] if len(t) > 1 else ""
        variants = {
            "Model call (2+ points from normal), all layers": [(band(r["p"], r["b"]), r["r1"], u) for r in recs[mk]],
            "Model up calls only": [(max(0, band(r["p"], r["b"])), r["r1"], u) for r in recs[mk]],
            "Model down calls only": [(min(0, band(r["p"], r["b"])), r["r1"], u) for r in recs[mk]],
            "Table label, any strength": [(direction(r["label"]), r["r1"], u) for r in recs[mk]],
            "Table label, Low": [(direction(r["label"]) if strength(r) == "Low" else 0, r["r1"], u) for r in recs[mk]],
            "Table label, Moderate or High": [(direction(r["label"]) if strength(r) in ("Moderate", "High") else 0, r["r1"], u) for r in recs[mk]],
            "Label and model agree": [(direction(r["label"]) if direction(r["label"]) and direction(r["label"]) == band(r["p"], r["b"]) else 0, r["r1"], u) for r in recs[mk]],
        }
        win[mk] = dict(sessions=len(recs[mk]), up_share=round(u * 100), rows={k: judge(v) for k, v in variants.items()})
    out["window"] = win

    # 6. other long records
    sr = json.load(open(OUT / "solar_return_generated_ET.json"))["bt_daily"]
    out["solar_return"] = dict(bullish=dict(hit=sr["Bullish"]["d1"], exp=sr["_base"]["up1"], n=sr["Bullish"]["n"], hit5=sr["Bullish"]["d5"], exp5=sr["_base"]["up5"]),
                               bearish=dict(hit=sr["Bearish"]["d1"], exp=round(100 - sr["_base"]["up1"], 1), n=sr["Bearish"]["n"], hit5=sr["Bearish"]["d5"],
                                            exp5=round(100 - sr["_base"]["up5"], 1)))
    out["watch_split"] = {mk: {k: json.load(open(OUT / f"{mk}_big_move_watch_2026-11-22_to_2027-12-31_ET.json"))["split"][k]
                               for k in ("split", "n_leads", "n_held", "pooled_obs", "pooled_exp", "pooled_lift", "pooled_p")} for mk in ("gold", "silver")}
    return out


CLEAN = {"spx": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
         "sensex": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
         "gold": "Model call (2+ points from normal), all layers", "silver": "Model call (2+ points from normal), all layers"}


def pooled(rows):
    rows = [r for r in rows if r and r["n"]]
    n = sum(r["n"] for r in rows)
    return round(sum(r["n"] * r["edge"] for r in rows) / n, 1) if n else None


def factor_markets(ok):
    """{'spx': ['Venus retrograde', 'Jupiter-Pluto 5/9'], 'sensex': ['Venus retrograde']} -> 'Venus retrograde (S&P and Sensex) and Jupiter-Pluto 5/9 (S&P)'."""
    by = {}
    for mk, v in ok.items():
        for f in v:
            by.setdefault(f, []).append(SHORT[mk])
    return " and ".join(f"{f} ({' and '.join(m)})" for f, m in by.items()) or "no factor"


def recommend(res):
    """What to change, from the long records (each with the evidence behind it); November is never the evidence.
    applied=True: the 2026 and 2027 calendars now show it this way."""
    t = res["tuning"]
    rows = {(r["layer"], r["market"]): r for r in res["rows"]}

    def nov(layer, mk):
        return (rows.get((layer, mk)) or {}).get("d1") or {}

    def nv(layer, mks=MKS):
        return "; ".join(f"{SHORT[mk]} {v['right']} of {v['n']}" for mk in mks if (v := nov(layer, mk)) and v["n"])
    rec = []
    lw = {mk: (t["labels"][mk].get("walk_forward") or t["labels"][mk])["rows"] for mk in MKS}
    li = {mk: t["labels"][mk]["rows"] for mk in ("spx", "sensex")}
    low, mh, anyl = ({mk: lw[mk][k] for mk in MKS} for k in ("Low|d1", "Moderate or High|d1", "Any strength|d1"))
    sig_low = [mk for mk in MKS if low[mk]["p"] is not None and low[mk]["p"] < 0.05 and low[mk]["edge"] > 0]
    sig_mh = [mk for mk in MKS if mh[mk]["p"] is not None and mh[mk]["p"] < 0.05 and mh[mk]["edge"] > 0]
    rec.append(dict(id="labels", applied=True, where="both calendars", supported=not sig_low,
                    title="Table labels are leans, not day calls; Low labels are now shown in grey",
                    evidence=("Out of sample (walk-forward, every day 2013-2026: S&P and Sensex labels from rules picked on 2000-2013 only; gold and silver with their data-picked parts re-picked on 2000-2013): "
                              + "; ".join(f"{SHORT[mk]} Low {low[mk]['hit']}% right vs {low[mk]['exp']}% by chance, Moderate or High {mh[mk]['hit']}% vs {mh[mk]['exp']}%"
                                          f" (p {mh[mk]['p']}), all labels {anyl[mk]['hit']}% vs {anyl[mk]['exp']}%" for mk in MKS)
                              + f". Pooled edge: Low {pooled(low.values()):+} points, Moderate or High {pooled(mh.values()):+} points; "
                              + (f"Moderate or High beats chance only on {', '.join(SHORT[m] for m in sig_mh)}. " if sig_mh else "no strength beats chance in any market. ")
                              + "The good figures in the published table (S&P Moderate or High " + f"{li['spx']['Moderate or High|d1']['hit']}% vs {li['spx']['Moderate or High|d1']['exp']}%, "
                              + f"Sensex {li['sensex']['Moderate or High|d1']['hit']}% vs {li['sensex']['Moderate or High|d1']['exp']}%) come from choosing and scoring the rules on the same years."),
                    november=nv("Signal table") + " (Low labels: " + nv("Signal table: Low labels") + ")"))
    m = {mk: t["model"][mk]["rows"][CLEAN[mk]] for mk in MKS}
    up = {mk: t["model"][mk]["rows"]["Model up calls only"] for mk in MKS}
    dn = {mk: t["model"][mk]["rows"]["Model down calls only"] for mk in MKS}
    ok = [mk for mk in MKS if m[mk]["n"] and m[mk]["p"] is not None and m[mk]["p"] < 0.05 and m[mk]["edge"] > 0]
    v1 = t["model_v1"]
    rec.append(dict(id="model", applied=True, where="both calendars", supported=not ok,
                    title="Combined model: its probabilities stay, but they are no longer coloured as calls" + (f" (except {', '.join(SHORT[x] for x in ok)})" if ok else ""),
                    evidence=("Walk-forward 2013-2026 (fitted on earlier years; S&P and Sensex also with labels from rules picked on 2000-2013): "
                              + "; ".join(f"{SHORT[mk]} {m[mk]['hit']}% right vs {m[mk]['exp']}% by chance (p {m[mk]['p']}, {m[mk]['n']} calls)" for mk in MKS)
                              + ". Up calls look right more often only because markets rise more often: " + "; ".join(f"{SHORT[mk]} up {up[mk]['hit']}% vs {up[mk]['exp']}%, down {dn[mk]['hit']}% vs {dn[mk]['exp']}%" for mk in MKS)
                              + f". Model v1.0 (gold, a source model, 2000-2026): {v1['all']['hit']}% vs {v1['all']['exp']}% (p {v1['all']['p']})."),
                    november=nv("Combined probability, all layers") + "; Model v1.0 " + nv("Model v1.0 (Ch.41 + Shadbala)", ("gold",))))
    bg, vf = t["big"], t["volatility_factors"]
    keep_big = [mk for mk in MKS if bg[mk]["p"] is not None and bg[mk]["p"] < 0.05 and (bg[mk]["warned_pct"] or 0) > (bg[mk]["other_pct"] or 0)]
    cf = OUT / "bigday_clean_test_ET.json"
    clean = json.load(open(cf))["markets"] if cf.exists() else None
    if clean:                                                  # the model's big-day layer is built from the published factors: keep it only where they pass a clean test
        keep_big = [mk for mk in keep_big if clean[mk]["verdict"] == "holds out of sample"]
        sp, sx = clean["spx"], clean["sensex"]
        cx = sx.get("cross_from_spx") or {}
        ok = {"spx": list(sp["clean_short"]) if sp["verdict"] == "holds out of sample" else [],
              "sensex": [e["factor"].split(": ", 1)[-1].split(" (")[0].split(" [")[0] for e in cx.get("each", []) if e["p"] < 0.05 and (e["lift"] or 0) > 1]}
        clean_txt = (f" Clean test (tools/bigday_clean_test.py: the same choice made on 2000-2013 only, scored 2013-2026): S&P picks {', '.join(sp['clean_short'])}; "
                     f"{sp['test']['obs']} big days vs {sp['test']['exp']} expected (x{sp['test']['lift']}, p {sp['test']['p']}; without Feb-May 2020 x{sp['test_no2020']['lift']}, "
                     f"p {sp['test_no2020']['p']}; without 2025 x{sp['loyo']['worst']['lift']}, p {sp['loyo']['worst']['p']}). Sensex: nothing is picked by 2013, but the S&P's two "
                     f"factors lift Sensex big days x{cx.get('test', {}).get('lift')} (p {cx.get('test', {}).get('p')}). Gold x{clean['gold']['test']['lift']}, "
                     f"silver x{clean['silver']['test']['lift']}: no.")
    else:
        ok, clean_txt = {}, " The factors were chosen on 2000-2026, so the lift is not a clean out-of-sample result."
    rec.append(dict(id="big_days", applied=True, where="both calendars" if clean else "the 2026 calendar", supported=True, keep=keep_big, vol_ok=ok,
                    title=("Big days: only " + factor_markets(ok) + " pass a clean test; the other volatility factors are in sample only, "
                           "and the model's big-day chance is shown as untested") if clean else
                          ("Big days: the volatility factors (S&P, Sensex) are the warning that holds up; the model's big-day chance counts only for the "
                           + (", ".join(SHORT[m] for m in keep_big) or "no market") + " and is shown as untested elsewhere"),
                    evidence=("Walk-forward 2013-2026, days the model flags (2+ points above normal) vs other days: "
                              + "; ".join(f"{SHORT[mk]} big on {bg[mk]['warned_pct']}% vs {bg[mk]['other_pct']}% (p {bg[mk]['p']}, {bg[mk]['warned']} flagged days)" if bg[mk]["warned"]
                                          else f"{SHORT[mk]} never flags a day" for mk in MKS)
                              + ". The volatility factors on their own: " + "; ".join(f"{SHORT[mk]} {nm}: {v['on_pct']}% big on factor days vs {v['off_pct']}% (p {v['p']})" for mk in vf for nm, v in vf[mk].items())
                              + "." + clean_txt),
                    november="; ".join(f"{SHORT[mk]} {len(res['bigs'][mk]['big_days'])} big days, {sum(b['warned'] for b in res['bigs'][mk]['big_days'])} flagged by the model"
                                       + (f", {sum(b['vol'] for b in res['bigs'][mk]['big_days'])} on volatility-factor days ({res['bigs'][mk]['vol_days']} factor days)" if mk in ("spx", "sensex") else "")
                                       for mk in MKS)))
    sr = t["solar_return"]
    nsr = nov("Solar return: generated day call", "spx")
    rec.append(dict(id="solar_return_days", applied=False, supported=True, title="Solar return day calls: November's run was luck; they stay as Solar return's view",
                    evidence=f"S&P since 1928: Bullish days {sr['bullish']['hit']}% right vs {sr['bullish']['exp']}% up days ({sr['bullish']['n']} days); "
                             f"Bearish days {sr['bearish']['hit']}% right vs {sr['bearish']['exp']}% down days ({sr['bearish']['n']} days)",
                    november=f"{nsr.get('right')} of {nsr.get('n')} ({nsr.get('hit')}% vs {nsr.get('exp')}% by chance, p {nsr.get('p')})" if nsr else ""))
    lv = res["leans"]["all"]
    rec.append(dict(id="deep_dive_leans", applied=False, supported=True, title="Deep-dive leans are not calls; November confirms it",
                    evidence="No month's deep dive has a test that passes the multiple-testing correction, and the nominal counts are below what chance gives",
                    november=f"{lv['right']} of {lv['n']} right ({lv['hit']}% vs {lv['exp']}% by chance)"))
    ws = t["watch_split"]
    rec.append(dict(id="watch_windows", applied=True, where="the 2026 calendar", where_note="the 2027 calendar shows no watch windows", supported=True, title="Gold and silver big-move watch windows are marked 'no proven lift'",
                    evidence="; ".join(f"{mk}: {ws[mk]['n_held']} of {ws[mk]['n_leads']} leads held in the second half; there {ws[mk]['pooled_obs']} big days vs {ws[mk]['pooled_exp']} expected "
                                       f"(lift {ws[mk]['pooled_lift']}, p {round(ws[mk]['pooled_p'], 2)})" for mk in ws),
                    november="; ".join(f"{SHORT[mk]} {res['bigs'][mk]['watch_big']} big of {res['bigs'][mk]['watch_days']} watch days" for mk in ("gold", "silver"))))
    pr = [r for r in t["rules_per_day"] if r["q"] < 0.10]
    rec.append(dict(id="span_rules", applied=False, supported=True, title="Span rules (Venus-Rahu and Moon-Rahu 6/8) are a lean over the whole span, not a call for each day",
                    evidence=f"Each S&P / Sensex table rule scored as a day-by-day call, 2000-2026: {len(pr)} of {len(t['rules_per_day'])} pass the correction (q < 0.10)"
                             + (": " + ", ".join(f"{r['rule']} on the {SHORT[r['market']]} ({r['day']['hit']}% vs {r['day']['exp']}%)" for r in pr) if pr else "")
                             + "; the table's records count each span once, from the close before it to its end",
                    november="; ".join(f"{s['rule'].split(' (')[0]} {dt.date.fromisoformat(s['frm']):%d %b}–{dt.date.fromisoformat(s['to']):%d %b} {SHORT[s['market']]} {s['ret']:+.2f}% ({s['result']})" for s in res["spans"])))
    return rec


def report(res):
    print("month:", res["month"])
    print("marked:", res["marked"])
    print("check vs forward_daybyday.score:", res["check_fd"]["matched"], "of", res["check_fd"]["of"], res["check_fd"]["diffs"][:3])
    for r in sorted(res["rows"], key=lambda r: (r["market"], r["layer"])):
        a, b = r["d1"], r["d5"]
        print(f"  {r['market']:6s} {r['layer'][:58]:58s} day {a['right']}/{a['n']} ({a['hit']}% vs {a['exp']}%, p {a['p']}) small {a['flat']} | 5s {b['right']}/{b['n']} ({b['hit']}% vs {b['exp']}%)")
    print("leans:", {k: (v["right"], v["n"], v["hit"], v["exp"]) for k, v in res["leans"].items()})
    print("bigs:", {mk: (v["warned"], v["warned_big"], len(v["big_days"]), v["watch_days"], v["watch_big"]) for mk, v in res["bigs"].items()})
    print("spans:", [(s["rule"][:24], s["market"], s["frm"], s["to"], s["ret"], s["result"]) for s in res["spans"]])
    print("reasons:", res["reasons"][:8])
    t = res["tuning"]
    for mk in MKS:
        print(mk, "labels:", {k: (v["hit"], v["exp"], v["p"], v["n"]) for k, v in t["labels"][mk]["rows"].items()})
        if t["labels"][mk].get("walk_forward"):
            print(mk, "labels WF:", t["labels"][mk]["walk_forward"]["rules"], {k: (v["hit"], v["exp"], v["p"], v["n"]) for k, v in t["labels"][mk]["walk_forward"]["rows"].items()})
        print(mk, "model:", {k[:40]: (v["hit"], v["exp"], v["p"], v["n"]) for k, v in t["model"][mk]["rows"].items()})
        print(mk, "window:", {k[:40]: (v["right"], v["n"], v["hit"], v["exp"], v["p"]) for k, v in t["window"][mk]["rows"].items()}, t["window"][mk]["up_share"])
    print("big:", t["big"])
    print("vol factors:", t["volatility_factors"])
    print("model v1:", t["model_v1"])
    for mk in ("spx", "sensex"):
        print(mk, "clean model:", {k[:60]: (v["right"], v["n"], v["hit"], v["exp"], v["p"]) for k, v in t["model"][mk]["rows"].items() if "clean" in k})
    for r in res["recommendations"]:
        print("REC", r["id"], r["applied"], "|", r["title"], "|", r["evidence"], "|", r["november"])


if __name__ == "__main__":
    main()
