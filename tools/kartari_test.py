"""Paap Kartari and Shubh Kartari: when they occur, and what the S&P 500 and the Sensex did, 2000-2026.

    python tools/kartari_test.py

Kartari = a planet hemmed: the nearest body behind it and the nearest ahead in longitude (Moon excluded) both belong
to one class and each sits in the planet's own sign or the sign either side (config/conventions.yaml valence.kartari,
which reproduces every printed 2026-document row).
  B116  Mercury in Paap Kartari (2026 document p.90): "negative event for financial markets"; "very volatile and both
        side movement" if aspected by benefics; "more profound" if Mercury is combust and the malefics are not the Sun.
  B117  Jupiter in Paap Kartari (2026 document p.91): no direction printed; tested as bearish, the direction B116 gives
        the yoga (an inference, labelled as such); "ineffective while the Moon runs from Jupiter to Ketu" is recorded,
        not applied (as in the calendar layer).
  TA s31 Mercury Paap Kartari (TA p.128, stricter: the planet ahead retrograde) is already in the market backtest and
        is quoted from it.
  Shubh Kartari (hemmed by benefics: Jupiter, Venus, Mercury) is NOT stated in any of our sources. It is tested here
        only because the user asked, as bullish for Mercury and Jupiter, and is not added to any table or calendar.
Scoring: PROJECT_KNOWLEDGE section 6 via tools/backtest_market.py (entry = last close before the start; windows of
3+ days to the last close inside; otherwise 5 sessions; FLAT < 0.5%; base = same horizon in the same Nov-Nov year),
both halves (2000-2013, 2013-2026); big days (|move| >= 2%) inside windows against all sessions.
Writes build/pdfref/kartari_test_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import datetime as dt
import gzip
import html
import json
import pathlib
import sys

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402
from finastro.sky import Sky, Span  # noqa: E402
from finastro.rules import valence as VAL  # noqa: E402

BM = load(ROOT / "tools" / "backtest_market.py", "bm_k")
ET = BM.MARKETS["spx"]["tz"]
UTC = dt.timezone.utc


def kartari(sky, body, cls):
    """VAL.paap_kartari with the class as a parameter ('malefic' = Paap, 'benefic' = Shubh)."""
    nb = VAL.neighbour_spans(sky, body)
    starts = [s.start for s in nb]
    others = sorted({x for s in nb for x in s.value})
    st = VAL.State(sky, [body] + others)
    pts = sorted(set(st.boundaries()) | set(starts) | {s.end for s in nb})

    def at(t):
        i = bisect.bisect_right(starts, t) - 1
        return nb[i].value if i >= 0 and t < nb[i].end else None
    out = []
    for a, b in zip(pts, pts[1:]):
        if b <= a:
            continue
        t = a + (b - a) / 2
        pair = at(t)
        if not pair:
            continue
        me = st.at(body, "sign", t)
        if not all(st.valence(x, t) == cls and VAL.house_from(me, st.at(x, "sign", t)) in (12, 1, 2) for x in pair):
            continue
        v = (pair[0], pair[1])
        if out and out[-1][1] == a and out[-1][2] == v:
            out[-1] = (out[-1][0], b, v)
        else:
            out.append((a, b, v))
    return out


def spans_all(body, cls):
    res = []
    for y in range(1999, 2029):
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        for a, b, v in kartari(Sky.load(f), body, cls):
            if res and abs((a - res[-1][1]).total_seconds()) < 120 and res[-1][2] == v:
                res[-1] = (res[-1][0], b, v)
            elif not res or a > res[-1][1]:
                res.append((a, b, v))
    return res


def combust_mercury(t):
    jd = swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60)
    m = swe.calc_ut(jd, swe.MERCURY, swe.FLG_SWIEPH)[0][0]
    s = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    return abs((m - s + 180) % 360 - 180) <= 14


def test(spans, tone):
    out = {}
    for mk in ("spx", "sensex"):
        M = BM.Market(mk)
        rows = []
        for a, b, v in spans:
            e = dict(start=a.isoformat(), end=b.isoformat(), day=None, tone=tone)
            s = M.score(e)
            if s:
                rows.append((e, s))
        rec = dict(all=BM.aggregate(rows, M), h1=BM.aggregate(rows, M, BM.P0, BM.SPLIT), h2=BM.aggregate(rows, M, BM.SPLIT, BM.P1))
        # big days inside the windows
        inside = set()
        for a, b, v in spans:
            d0, d1 = M.session_day(a), M.session_day(b)
            i = bisect.bisect_left(M.D, d0)
            while i < len(M.D) and M.D[i] <= d1:
                inside.add(i)
                i += 1
        idx = [i for i in range(1, len(M.D)) if BM.P0 <= M.D[i] <= BM.P1]
        big = lambda i: abs(M.C[i] / M.C[i - 1] - 1) >= 0.02  # noqa: E731
        ins = [i for i in idx if i in inside]
        rec["big_in"] = round(sum(big(i) for i in ins) / len(ins) * 100, 1) if ins else None
        rec["big_all"] = round(sum(big(i) for i in idx) / len(idx) * 100, 1)
        rec["sessions_in"] = len(ins)
        out[mk] = rec
    return out


def episode_big(spans, reps=1000):
    """Big-day rate inside the windows: windows above their year's rate, and a permutation p (random windows of the same lengths)."""
    import random
    out = {}
    for mk in ("spx", "sensex"):
        M = BM.Market(mk)
        big = [False] + [abs(M.C[i] / M.C[i - 1] - 1) >= 0.02 for i in range(1, len(M.D))]
        idx = [i for i in range(1, len(M.D)) if BM.P0 <= M.D[i] <= BM.P1]
        above, ins, L = 0, set(), []
        for a, b, v in spans:
            i0, i1 = bisect.bisect_left(M.D, M.session_day(a)), bisect.bisect_right(M.D, M.session_day(b))
            if i1 <= i0:
                continue
            yr = [i for i in range(1, len(M.D)) if M.D[i].year == M.D[i0].year]
            above += sum(big[i] for i in range(i0, i1)) / (i1 - i0) > sum(big[i] for i in yr) / len(yr)
            ins.update(range(i0, i1))
            L.append(i1 - i0)
        obs = sum(big[i] for i in ins) / len(ins)
        rnd = random.Random(1)
        cnt = 0
        for _ in range(reps):
            s_ = set()
            for n in L:
                st = rnd.randint(idx[0], idx[-1] - n)
                s_.update(range(st, st + n))
            cnt += sum(big[i] for i in s_) / len(s_) >= obs
        out[mk] = dict(windows=len(L), above=above, perm_p=round(cnt / reps, 3))
    return out


def fmt(r):
    a = r["all"]
    if not a["worked"] + a["failed"]:
        return "no decided cases"
    return f"{a['worked']}/{a['worked'] + a['failed']} ({a['hit_rate']}% vs {a['base_rate']}%), p {a['p_value']}"


def main():
    A, B = dt.datetime(2026, 11, 24, tzinfo=ET), dt.datetime(2027, 12, 31, 23, 59, tzinfo=ET)    # every window to the end of the 2027 calendar
    defs = [("b116", "Mercury in Paap Kartari (2026 document B116)", "Mercury", "malefic", "Bearish", "source: “negative event for financial markets”"),
            ("b117", "Jupiter in Paap Kartari (2026 document B117)", "Jupiter", "malefic", "Bearish", "source prints no direction; tested as bearish (inferred from B116)"),
            ("sk_mercury", "Mercury in Shubh Kartari (not in our sources)", "Mercury", "benefic", "Bullish", "exploratory: no source states it"),
            ("sk_jupiter", "Jupiter in Shubh Kartari (not in our sources)", "Jupiter", "benefic", "Bullish", "exploratory: no source states it")]
    res = dict(rules=[])
    for key, title, body, cls, tone, basis in defs:
        sp = spans_all(body, cls)
        hist = [s for s in sp if dt.datetime(2000, 11, 20, tzinfo=UTC) <= s[0] < dt.datetime(2026, 11, 21, tzinfo=UTC)]
        rec = test(hist, tone)
        sub = None
        if key == "b116":
            strong = [s for s in hist if combust_mercury(s[0]) and "Sun" not in s[2]]
            sub = dict(n=len(strong), rec=test(strong, tone)) if strong else None
        now = [dict(frm=a.astimezone(ET).strftime("%a %d %b %Y %H:%M"), to=b.astimezone(ET).strftime("%a %d %b %Y %H:%M"), pair=" | ".join(v),
                    frm_iso=a.astimezone(ET).isoformat(), to_iso=b.astimezone(ET).isoformat())
               for a, b, v in sp if b > A and a < B]
        if key == "b117":
            rec["episode_big"] = episode_big(hist)
        res["rules"].append(dict(key=key, title=title, tone=tone, basis=basis, n=len(hist), record=rec, combust_subset=sub, upcoming=now,
                                 days=round(sum((b - a).total_seconds() for a, b, v in hist) / 86400 / max(len(hist), 1), 1)))
    mb = json.load(open(OUT / "market_backtest_2000-2026_ET.json"))
    ta = next((x for x in mb["rules"] if x["rule_id"].startswith("ta_s31_mercury_paap_kartari")), None)
    res["ta_s31"] = {k: ta[k] for k in ("spx", "sensex")} if ta else None
    cache = OUT / "backtest" / "market_events_2000-2026.json.gz"
    if cache.exists():
        evs = [e for e in json.load(gzip.open(cache, "rt", encoding="utf-8")) if e["rule_id"].startswith("ta_s31_mercury_paap_kartari")]
        res["ta_s31_last"] = sorted({e["start"][:10] for e in evs})[-3:]
    json.dump(res, open(OUT / "kartari_test_ET.json", "w"), indent=1, default=str)
    (OUT / "kartari_test_ET.html").write_text(page(res), encoding="utf-8")
    for r in res["rules"]:
        print(r["title"], "| windows", r["n"], "avg days", r["days"])
        for mk in ("spx", "sensex"):
            x = r["record"][mk]
            print(f"   {mk}: {fmt(x)}; halves {x['h1']['hit_rate']} vs {x['h1']['base_rate']} / {x['h2']['hit_rate']} vs {x['h2']['base_rate']}; big days {x['big_in']}% vs {x['big_all']}% ({x['sessions_in']} sessions)")
        if r["combust_subset"]:
            print("   combust subset", r["combust_subset"]["n"], {mk: fmt(v) for mk, v in r["combust_subset"]["rec"].items()})
        print("   upcoming:", r["upcoming"])
    print("TA s31:", {k: (v["worked"], v["failed"], v["hit_rate"], v["base_rate"], v["p_value"], v["status"]) for k, v in (res["ta_s31"] or {}).items() if v})


def page(res):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--dn:#cf222e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1150px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Paap and Shubh Kartari</title><style>{css}</style></head><body>",
         "<h1>Paap Kartari and Shubh Kartari: tested on the S&amp;P 500 and the Sensex, 2000–2026</h1>",
         "<p class='s'>Kartari = a planet hemmed between the nearest bodies behind and ahead of it (Moon excluded), both of one class and each within one sign of it. "
         "Paap = both malefic (Sun, Mars, Saturn, Rahu, Ketu, Uranus, Pluto); Shubh = both benefic (Jupiter, Venus, Mercury). Scored by the project's standard method.</p>",
         "<div class='wrap'><table><thead><tr><th>Yoga</th><th>Basis</th><th>Windows</th><th>S&amp;P 500</th><th>Sensex</th><th>Big days inside (S&amp;P / Sensex)</th></tr></thead><tbody>"]
    for r in res["rules"]:
        s, x = r["record"]["spx"], r["record"]["sensex"]
        o.append(f"<tr><td><b>{E(r['title'])}</b><div class='s'>tested as {r['tone'].lower()}</div></td><td class='s'>{E(r['basis'])}</td><td class='n'>{r['n']} (avg {r['days']} d)</td>"
                 f"<td>{E(fmt(s))}<div class='s'>halves {s['h1']['hit_rate']}% vs {s['h1']['base_rate']}% · {s['h2']['hit_rate']}% vs {s['h2']['base_rate']}%</div></td>"
                 f"<td>{E(fmt(x))}<div class='s'>halves {x['h1']['hit_rate']}% vs {x['h1']['base_rate']}% · {x['h2']['hit_rate']}% vs {x['h2']['base_rate']}%</div></td>"
                 f"<td class='s'>{s['big_in']}% vs {s['big_all']}% · {x['big_in']}% vs {x['big_all']}%</td></tr>")
    ta = res.get("ta_s31")
    if ta:
        o.append("<tr><td><b>Mercury Paap Kartari, TA definition (planet ahead retrograde)</b><div class='s'>tested as bearish</div></td><td class='s'>TA p.128: bearish for the market and banks</td><td></td>"
                 + "".join(f"<td>{ta[k]['worked']}/{ta[k]['worked'] + ta[k]['failed']} ({ta[k]['hit_rate']}% vs {ta[k]['base_rate']}%), p {ta[k]['p_value']} <div class='s'>{E(ta[k]['status'])}</div></td>" for k in ("spx", "sensex"))
                 + "<td></td></tr>")
    o.append("</tbody></table></div>")
    b116 = next(r for r in res["rules"] if r["key"] == "b116")
    b117 = next(r for r in res["rules"] if r["key"] == "b117")
    eb = b117["record"].get("episode_big")
    if eb:
        o.append("<p class='s'>B117 big days: the pooled excess comes from a few windows — " + "; ".join(
            f"{'S&P' if k == 'spx' else 'Sensex'}: {v['above']} of {v['windows']} windows above their year's big-day rate, permutation p {v['perm_p']}" for k, v in eb.items())
            + ". Not significant; a lead at most.</p>")
    if b116["combust_subset"]:
        c = b116["combust_subset"]
        o.append(f"<p class='s'>B116's “more profound” case (Mercury combust, malefics other than the Sun): {c['n']} windows; S&amp;P {E(fmt(c['rec']['spx']))}; Sensex {E(fmt(c['rec']['sensex']))}.</p>")
    o.append("<h2>When they occur, 24 Nov 2026 – 28 Feb 2027</h2><ul>")
    for r in res["rules"]:
        o.append(f"<li><b>{E(r['title'])}:</b> " + (E("; ".join(f"{u['frm']} → {u['to']} ({u['pair']})" for u in r["upcoming"])) or "not in this period") + "</li>")
    o.append("</ul><p class='s'>Generated by tools/kartari_test.py. Shubh Kartari is exploratory: no source we use states it, so it is not added to any table or calendar.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
