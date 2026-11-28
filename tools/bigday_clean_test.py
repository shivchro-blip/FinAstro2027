"""Clean walk-forward test of the big-day volatility factors (S&P 500, BSE Sensex; gold and silver for comparison).

    python tools/bigday_clean_test.py

The robust big-move factors behind the calendars' "volatility factor" notes, the market tables' Volatile label and the
combined model's big-move layer (tools/market_summary.py) were chosen on all of 2000-2026, so their record on 2013-2026
is partly in sample. Here the same procedure is run on 2000-2013 only, and the factors it picks are scored on 2013-2026:
  * universe: every factor of tools/big_move_analysis.py for that market (events within +/-3 days, states on the day,
    every rule active), built with that tool's own code;
  * pick, 20 Nov 2000 - 19 Nov 2013: q < 0.10 over all factors (Benjamini-Hochberg), lift > 1 in both halves of that
    period (split 20 May 2007), and p < 0.01 with Sep 2008 - Jun 2009 removed. These are the published criteria, moved
    inside the first half;
  * test, 20 Nov 2013 - 31 Oct 2026: days with any picked factor, big days against the year-stratified expectation
    (Poisson, one-sided: more big days), the plain big-day rates on factor days and on other days, the same without
    Feb-May 2020, and each picked factor's own lift;
  * checks: the same procedure on all of 2000-2026 reproduces the published robust set; looser picks (q < 0.20, and
    p < 0.05 with 5+ episodes as in the watch-window split test) show whether the answer depends on the threshold.
Big day: |close-to-close| >= 2% (S&P, Sensex, gold), 3.5% (silver). Market prices and astrology only.
Writes build/pdfref/bigday_clean_test_ET.json (read by the 2026 and 2027 calendars).
"""
from __future__ import annotations

import collections
import datetime as dt
import importlib.util
import json
import math
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
MKS = ("spx", "sensex", "gold", "silver")
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}
P0, SPLIT, MID, END = dt.date(2000, 11, 20), dt.date(2013, 11, 20), dt.date(2007, 5, 20), dt.date(2026, 10, 31)
CRISIS = [(dt.date(2008, 9, 1), dt.date(2009, 6, 30)), (dt.date(2020, 2, 15), dt.date(2020, 5, 31))]
COVID = [CRISIS[1]]


def bma(key):
    """tools/big_move_analysis.py loaded for one market (it reads the market from FINASTRO_METAL)."""
    os.environ["FINASTRO_METAL"] = key
    for m in ("metal_cfg", "bma"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("bma", ROOT / "tools" / "big_move_analysis.py")
    M = importlib.util.module_from_spec(spec)
    sys.modules["bma"] = M
    spec.loader.exec_module(M)
    return M


def within(d, spans):
    return any(a <= d <= b for a, b in spans)


def pick(M, days, lo, hi, mid, crisis, min_days, inner_min, mode="robust", q_max=0.10, p_xc=0.01):
    """Factors chosen on lo <= date < hi only. mode robust: the published criteria; leads: p < 0.05, 5+ episodes, either direction."""
    h = [x for x in days if lo <= x["date"] < hi]
    rows, _, _ = M.factor_table(h, min_days)
    if mode == "leads":
        return [dict(factor=r["factor"], lift=r["lift"], big=r["big"], exp=r["exp_big"], p=round(r["p"], 4), q=round(r["q"], 3))
                for r, side in M.leads(rows) if side == "any"]
    a = {r["factor"]: r for r in M.factor_table([x for x in h if x["date"] < mid], inner_min)[0]}
    b = {r["factor"]: r for r in M.factor_table([x for x in h if x["date"] >= mid], 1)[0]}
    xc = {r["factor"]: r for r in M.factor_table([x for x in h if not within(x["date"], crisis)], min_days)[0]}
    out = []
    for r in sorted(rows, key=lambda r: r["p"]):
        if r["q"] >= q_max:
            continue
        la, lb, x = (a.get(r["factor"]) or {}).get("lift"), (b.get(r["factor"]) or {}).get("lift"), xc.get(r["factor"])
        if (la or 0) > 1 and (lb or 0) > 1 and x and x["p"] < p_xc:
            out.append(dict(factor=r["factor"], lift=r["lift"], big=r["big"], exp=r["exp_big"], p=round(r["p"], 6), q=round(r["q"], 3),
                            lift_a=la, lift_b=lb, xc_p=round(x["p"], 4)))
    return out


def two_prop(k1, n1, k2, n2):
    if not (n1 and n2):
        return None
    pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    return round(math.erfc(abs(k1 / n1 - k2 / n2) / se / math.sqrt(2)), 4) if se else None


def test(M, days, factors, lo, hi, drop=()):
    """Days with any of `factors` in lo..hi: big days against the year-stratified expectation, and plain rates."""
    t = [x for x in days if lo <= x["date"] <= hi and not within(x["date"], drop)]
    if not factors or not t:
        return dict(days=len(t), factor_days=0, share=0, big=sum(abs(x["ret"]) >= M.TH for x in t), obs=0, exp=0, lift=None, p=None,
                    rate_on=None, rate_off=None, p_rates=None)
    fs = set(factors)
    on = [bool(fs & x["f"]) for x in t]
    big = [abs(x["ret"]) >= M.TH for x in t]
    yr = collections.defaultdict(lambda: [0, 0, 0])
    for x, o, g in zip(t, on, big):
        c = yr[x["date"].year]
        c[0] += 1
        c[1] += g
        c[2] += o
    exp = sum(b * o / n for n, b, o in yr.values() if n)
    obs = sum(o and g for o, g in zip(on, big))
    n_on, k_off = sum(on), sum(big) - obs
    n_off = len(t) - n_on
    return dict(days=len(t), factor_days=n_on, share=round(n_on / len(t) * 100, 1), big=sum(big), obs=obs, exp=round(exp, 1),
                lift=round(obs / exp, 2) if exp else None, p=round(M.poisson_sf(obs, exp), 4) if exp else None,
                rate_on=round(obs / n_on * 100, 1) if n_on else None, rate_off=round(k_off / n_off * 100, 1) if n_off else None,
                p_rates=two_prop(obs, n_on, k_off, n_off))


def by_year(M, days, factors, lo, hi):
    """Where the test-period big days on factor days came from, year by year (expected from that year's big-day rate)."""
    fs, yr = set(factors), collections.defaultdict(lambda: [0, 0, 0, 0])
    for x in days:
        if lo <= x["date"] <= hi:
            c = yr[x["date"].year]
            g = abs(x["ret"]) >= M.TH
            c[0] += 1
            c[1] += g
            if fs & x["f"]:
                c[2] += 1
                c[3] += g
    return [dict(year=y, factor_days=c[2], big=c[3], exp=round(c[1] * c[2] / c[0], 1)) for y, c in sorted(yr.items()) if c[2]]


def loyo(M, days, factors, lo, hi):
    """Leave one year out: the test again without each year in turn (does one year carry the result?)."""
    out = []
    for y in range(lo.year, hi.year + 1):
        r = test(M, days, factors, lo, hi, [(dt.date(y, 1, 1), dt.date(y, 12, 31))])
        out.append(dict(year=y, lift=r["lift"], p=r["p"], obs=r["obs"], exp=r["exp"]))
    worst = max(out, key=lambda r: r["p"] if r["p"] is not None else -1) if out else None
    return dict(rows=out, worst=worst)


def short(f):
    return f.split(": ", 1)[-1].split(" (")[0].split(" [")[0]


def each(M, days, factors, lo, hi):
    t = [x for x in days if lo <= x["date"] <= hi]
    rows = {r["factor"]: r for r in M.factor_table(t, 1)[0]}
    return [dict(factor=f, big=(rows.get(f) or {}).get("big", 0), exp=(rows.get(f) or {}).get("exp_big", 0.0), lift=(rows.get(f) or {}).get("lift"),
                 p=round((rows.get(f) or {}).get("p", 1.0), 4), days=(rows.get(f) or {}).get("days", 0)) for f in factors]


def verdict(r):
    if not r["factor_days"]:
        return "nothing picked on 2000-2013"
    if r["p"] is not None and r["p"] < 0.05 and (r["lift"] or 0) > 1:
        return "holds out of sample"
    return "does not hold out of sample"


def main():
    res = dict(made=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), pick=f"{P0} to {SPLIT - dt.timedelta(days=1)}",
               test=f"{SPLIT} to {END}", markets={})
    summ = json.load(open(OUT / "market_summary_2000-2026_ET.json"))["markets"]
    for mk in MKS:
        M = bma(mk)
        days = M.build_days()
        clean = pick(M, days, P0, SPLIT, MID, CRISIS[:1], 15, 8)
        loose_q = pick(M, days, P0, SPLIT, MID, CRISIS[:1], 15, 8, q_max=0.20)
        loose_l = pick(M, days, P0, SPLIT, MID, CRISIS[:1], 15, 8, mode="leads")
        full = pick(M, days, P0, dt.date(2026, 11, 21), SPLIT, CRISIS, 30, 15)
        pub = sorted(x["factor"] for x in summ[mk]["fdr"] if x["robust"]) if mk in summ else None
        cf = [x["factor"] for x in clean]
        m = dict(name=NAME[mk], threshold=M.TH, n_factors=len(set().union(*(x["f"] for x in days))), clean=clean,
                 test=test(M, days, cf, SPLIT, END), test_no2020=test(M, days, cf, SPLIT, END, COVID), each=each(M, days, cf, SPLIT, END),
                 first_half=test(M, days, cf, P0, SPLIT - dt.timedelta(days=1)),
                 loose_q=dict(factors=[x["factor"] for x in loose_q], test=test(M, days, [x["factor"] for x in loose_q], SPLIT, END)),
                 loose_leads=dict(factors=[x["factor"] for x in loose_l], test=test(M, days, [x["factor"] for x in loose_l], SPLIT, END)),
                 full=dict(factors=[x["factor"] for x in full], reproduces_published=(sorted(x["factor"] for x in full) == pub) if pub is not None else None,
                           published=pub, test=test(M, days, [x["factor"] for x in full], SPLIT, END),
                           test_no2020=test(M, days, [x["factor"] for x in full], SPLIT, END, COVID)))
        m["overlap"] = sorted(set(cf) & set(m["full"]["factors"]))
        m["by_year"] = by_year(M, days, cf, SPLIT, END)
        m["loyo"] = loyo(M, days, cf, SPLIT, END) if cf else None
        m["clean_short"] = [short(f) for f in cf]
        m["full_short"] = [short(f) for f in m["full"]["factors"]]
        res["markets"][mk] = m
        if mk == "sensex":                                   # the S&P's clean picks, scored on the Sensex (other market, later years)
            sp = res["markets"]["spx"]["clean"]
            f = [x["factor"] for x in sp]
            m["cross_from_spx"] = dict(factors=f, test=test(M, days, f, SPLIT, END), test_no2020=test(M, days, f, SPLIT, END, COVID), each=each(M, days, f, SPLIT, END),
                                       by_year=by_year(M, days, f, SPLIT, END), loyo=loyo(M, days, f, SPLIT, END))
        m["verdict"] = verdict(m["test"])
        m["verdict_no2020"] = verdict(m["test_no2020"])
    (OUT / "bigday_clean_test_ET.json").write_text(json.dumps(res, indent=1, default=str))
    for mk, m in res["markets"].items():
        t, t2, f = m["test"], m["test_no2020"], m["full"]
        print(f"{mk}: {len(m['clean'])} picked on 2000-2013 of {m['n_factors']} factors; test: {t['obs']} big vs {t['exp']} expected (x{t['lift']}, p {t['p']}), "
              f"rate {t['rate_on']}% on {t['factor_days']} factor days vs {t['rate_off']}% (p {t['p_rates']}); no 2020: x{t2['lift']} p {t2['p']} -> {m['verdict']}")
        for x in m["clean"]:
            print(f"     picked: {x['factor']} (2000-13 x{x['lift']}, q {x['q']})")
        for x in m["each"]:
            print(f"     2013-26: x{x['lift']} {x['big']}/{x['exp']} p {x['p']}  {x['factor']}")
        print(f"   loose q<0.20: {len(m['loose_q']['factors'])} -> x{m['loose_q']['test']['lift']} p {m['loose_q']['test']['p']}; "
              f"leads: {len(m['loose_leads']['factors'])} -> x{m['loose_leads']['test']['lift']} p {m['loose_leads']['test']['p']}")
        print(f"   full-period set reproduces published: {f['reproduces_published']} ({len(f['factors'])}); its 2013-26 record x{f['test']['lift']} p {f['test']['p']} (in sample)")
        print("   by year:", [(r["year"], r["factor_days"], r["big"], r["exp"]) for r in m["by_year"]])
        if m["loyo"]:
            print("   leave one year out:", [(r["year"], r["lift"], r["p"]) for r in m["loyo"]["rows"]], "worst", m["loyo"]["worst"])
        if m.get("cross_from_spx"):
            c = m["cross_from_spx"]
            print(f"   S&P picks on the Sensex 2013-26: x{c['test']['lift']} p {c['test']['p']}; no 2020 x{c['test_no2020']['lift']} p {c['test_no2020']['p']}", [(x["factor"][:30], x["lift"], x["p"]) for x in c["each"]])
            print("   cross by year:", [(r["year"], r["factor_days"], r["big"], r["exp"]) for r in c["by_year"]], "worst", c["loyo"]["worst"])


if __name__ == "__main__":
    main()
