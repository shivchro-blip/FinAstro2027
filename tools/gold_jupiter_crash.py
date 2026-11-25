"""Gold crashes and Jupiter's afflictions (user note, 25 Nov 2026): the claims checked year by year, tested on gold since
1972, and the current configuration's end dates.

    python tools/gold_jupiter_crash.py

The note: in the gold crashes of 1974, 1980, 2008, 2011, 2020, 2022 and 2026 Jupiter was in a trine / mutual aspect /
conjunction with Saturn, or with a node or Pluto, or hemmed by malefics, and in all of them Jupiter was under the
Vedha (Sarvatobhadra) of malefics. Sidereal Lahiri, mean node, whole-sign relations and drishti (Saturn 3/7/10,
Jupiter 5/7/9, all 7). Vedha: TA pp.130-141 wheel and doctrine (finastro/pdfref/vedha.py; malefics = Sun, Mars,
Saturn, Rahu, Ketu, TA p.137); the post-station lag is not applied here.
Crashes: falls of 15%+ from a peak on monthly gold prices since 1972 (datasets/gold-prices, monthly averages; saved
as build/pdfref/backtest/gold_monthly_1833.csv), and of 10%+ on daily COMEX gold since 2000.
Test: how often each condition holds at all (share of months), how often it held at crash peaks, and gold's next
3 and 6 months when it holds against when it does not. Writes build/pdfref/gold_jupiter_crash_ET.{html,json}.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
from finastro.pdfref.engine import snapshot  # noqa: E402
from finastro.pdfref import vedha as V  # noqa: E402

ET, UTC = ZoneInfo("America/New_York"), dt.timezone.utc
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
MALEFIC = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
CLAIMS = {1974: "Jupiter in Aquarius, Saturn in Gemini: trine and aspect", 1980: "Jupiter and Saturn in Leo with Rahu; later with Pluto in Virgo",
          2008: "Jupiter and Pluto in Sagittarius, Saturn in Leo: trine and aspect", 2011: "Jupiter in Aries, Saturn in Libra: mutual aspect (Pisces / Virgo early in the year)",
          2020: "Jupiter in Sagittarius with Ketu and Pluto", 2022: "Jupiter in Pisces aspected by Saturn in Capricorn with Pluto; then hemmed by Rahu and Saturn",
          2026: "Jupiter in Cancer, Saturn in Pisces: trine and aspect; then Jupiter with Ketu in Leo"}


def h(a, b):
    """House of sign b counted from sign a (1-12)."""
    return (b - a) % 12 + 1


def state(t):
    s = snapshot(t)
    j, sa = s["Jupiter"], s["Saturn"]
    js, ss = j.sign_i, sa.sign_i
    rel = h(js, ss)
    r = {}
    r["Jupiter sign"] = j.sign
    r["Saturn sign"] = sa.sign
    r["Jupiter–Saturn conjunct"] = rel == 1
    r["Jupiter–Saturn trine (5/9)"] = rel in (5, 9)
    r["Jupiter–Saturn opposite (7)"] = rel == 7
    r["Saturn aspects Jupiter"] = h(ss, js) in (3, 7, 10) or rel == 1
    r["Jupiter with Rahu or Ketu"] = js in (s["Rahu"].sign_i, s["Ketu"].sign_i)
    r["Jupiter with Pluto"] = js == s["Pluto"].sign_i
    mal_signs = {b: s[b].sign_i for b in ("Sun", "Mars", "Saturn", "Rahu", "Ketu", "Pluto", "Uranus")}
    r["Jupiter hemmed by malefics (12th and 2nd)"] = any(v == (js - 1) % 12 for v in mal_signs.values()) and any(v == (js + 1) % 12 for v in mal_signs.values())
    vd = []
    for b in MALEFIC:
        p = s[b]
        tg, _ = V.targets(b, p.nak28, p.retro, V.vedha_fast(b, p.speed, p.retro) if b in ("Mars",) else False)
        if j.nak28 in tg.values():
            vd.append(b)
    r["Malefic vedha on Jupiter"] = vd
    r["Jupiter nakshatra"] = j.nak28
    r["afflicted"] = (r["Jupiter–Saturn conjunct"] or r["Jupiter–Saturn trine (5/9)"] or r["Jupiter–Saturn opposite (7)"] or r["Saturn aspects Jupiter"]
                      or r["Jupiter with Rahu or Ketu"] or r["Jupiter with Pluto"] or r["Jupiter hemmed by malefics (12th and 2nd)"])
    return r


def monthly():
    rows = [(r["Date"], float(r["Price"])) for r in csv.DictReader(open(OUT / "backtest" / "gold_monthly_1833.csv"))]
    return [(dt.date(int(d[:4]), int(d[5:7]), 15), p) for d, p in rows if d >= "1971-08"]


def daily():
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "gold_GC_F_daily_2000.csv"))]
    return rows


def drawdowns(series, thr):
    """Peak-to-trough falls of `thr`%+; a new peak starts after recovery above the old one."""
    out = []
    peak_d, peak = series[0]
    trough_d, trough = peak_d, peak
    for d, p in series[1:]:
        if p > peak:
            if (trough / peak - 1) * 100 <= -thr:
                out.append(dict(peak=peak_d, trough=trough_d, depth=round((trough / peak - 1) * 100, 1), p0=peak, p1=trough))
            peak_d, peak, trough_d, trough = d, p, d, p
        elif p < trough:
            trough_d, trough = d, p
    if (trough / peak - 1) * 100 <= -thr:
        out.append(dict(peak=peak_d, trough=trough_d, depth=round((trough / peak - 1) * 100, 1), p0=peak, p1=trough, open=True))
    return out


def at(d):
    return dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET).astimezone(UTC)


def main():
    M = monthly()
    Dd = daily()
    crashes_m = drawdowns(M, 15)
    crashes_d = drawdowns(Dd, 10)
    # claim check: the year's highest price and the low of the following 12 months
    claims = []
    for y, txt in CLAIMS.items():
        ser = Dd if y >= 2001 else M
        yr = [(d, p) for d, p in ser if d.year == y]
        pd_, pv = max(yr, key=lambda x: x[1])
        after = [(d, p) for d, p in ser if pd_ < d <= pd_ + dt.timedelta(days=366)]
        td, tv = min(after, key=lambda x: x[1]) if after else (pd_, pv)
        st0 = state(at(pd_))
        # every day (monthly before 2001) of the fall
        step = dt.timedelta(days=1 if y >= 2001 else 15)
        d, n, cnt, vd_any = pd_, 0, {}, set()
        while d <= td:
            st = state(at(d))
            n += 1
            for k, v in st.items():
                if v is True:
                    cnt[k] = cnt.get(k, 0) + 1
            vd_any.update(st["Malefic vedha on Jupiter"])
            if st["Malefic vedha on Jupiter"]:
                cnt["Malefic vedha on Jupiter"] = cnt.get("Malefic vedha on Jupiter", 0) + 1
            d += step
        claims.append(dict(year=y, claim=txt, episodes=[dict(peak=str(pd_), trough=str(td), depth=round((tv / pv - 1) * 100, 1), at_peak=st0,
                                                             during={k: round(v / n * 100) for k, v in cnt.items()}, vedha_by=sorted(vd_any), samples=n)]))
    # specificity: monthly 1972-2026
    mstates = []
    for i, (d, p) in enumerate(M):
        if d.year < 1972:
            continue
        st = state(at(d))
        f3 = (M[i + 3][1] / p - 1) * 100 if i + 3 < len(M) else None
        f6 = (M[i + 6][1] / p - 1) * 100 if i + 6 < len(M) else None
        mstates.append(dict(d=d, st=st, f3=f3, f6=f6))
    peaks = {c["peak"] for c in crashes_m}
    conds = ["Jupiter–Saturn conjunct", "Jupiter–Saturn trine (5/9)", "Jupiter–Saturn opposite (7)", "Saturn aspects Jupiter", "Jupiter with Rahu or Ketu",
             "Jupiter with Pluto", "Jupiter hemmed by malefics (12th and 2nd)", "afflicted", "Malefic vedha on Jupiter", "afflicted and malefic vedha"]

    def val(st, c):
        if c == "Malefic vedha on Jupiter":
            return bool(st[c])
        if c == "afflicted and malefic vedha":
            return st["afflicted"] and bool(st["Malefic vedha on Jupiter"])
        return bool(st[c])
    spec = {}
    for c in conds:
        on = [m for m in mstates if val(m["st"], c)]
        off = [m for m in mstates if not val(m["st"], c)]
        pk = [m for m in mstates if m["d"] in peaks]
        spec[c] = dict(share=round(len(on) / len(mstates) * 100, 1), at_peaks=sum(val(m["st"], c) for m in pk), peaks=len(pk),
                       f3_on=round(statistics.fmean(m["f3"] for m in on if m["f3"] is not None), 2) if on else None,
                       f3_off=round(statistics.fmean(m["f3"] for m in off if m["f3"] is not None), 2) if off else None,
                       f6_on=round(statistics.fmean(m["f6"] for m in on if m["f6"] is not None), 2) if on else None,
                       f6_off=round(statistics.fmean(m["f6"] for m in off if m["f6"] is not None), 2) if off else None,
                       down6_on=round(sum(m["f6"] <= -10 for m in on if m["f6"] is not None) / max(1, sum(m["f6"] is not None for m in on)) * 100, 1),
                       down6_off=round(sum(m["f6"] <= -10 for m in off if m["f6"] is not None) / max(1, sum(m["f6"] is not None for m in off)) * 100, 1))
    # the current configuration: day by day to the end of 2027
    d = dt.date(2026, 11, 25)
    keys = conds[:-1]
    spans = {k: [] for k in keys + ["afflicted and malefic vedha"]}
    prev = {}
    while d <= dt.date(2027, 12, 31):
        st = state(at(d))
        for k in spans:
            v = val(st, k)
            if v and not prev.get(k):
                spans[k].append([d, d, st["Malefic vedha on Jupiter"] if k.startswith("Malefic") else None])
            if v:
                spans[k][-1][1] = d
            prev[k] = v
        d += dt.timedelta(days=1)
    now = state(at(dt.date(2026, 11, 25)))
    res = dict(claims=claims, crashes_m=[dict(c, peak=str(c["peak"]), trough=str(c["trough"])) for c in crashes_m],
               crashes_d=[dict(c, peak=str(c["peak"]), trough=str(c["trough"])) for c in crashes_d], spec=spec,
               spans={k: [[str(a), str(b)] for a, b, _ in v] for k, v in spans.items()}, now=now, months=len(mstates))
    json.dump(res, open(OUT / "gold_jupiter_crash_ET.json", "w"), indent=1, default=str)
    (OUT / "gold_jupiter_crash_ET.html").write_text(page(res), encoding="utf-8")
    print("monthly crashes >=15%:", [(c["peak"], c["trough"], c["depth"]) for c in crashes_m])
    print("daily crashes >=10% since 2000:", [(c["peak"], c["trough"], c["depth"]) for c in crashes_d])
    for c in claims:
        print("==", c["year"], c["claim"])
        for e in c["episodes"]:
            a = e["at_peak"]
            print("   ", e["peak"], "->", e["trough"], e["depth"], "| J", a["Jupiter sign"], "S", a["Saturn sign"], {k: v for k, v in a.items() if v and k not in ("Jupiter sign", "Saturn sign", "Jupiter nakshatra")}, "| during %", e["during"], "vedha by", e["vedha_by"])
    for k, v in spec.items():
        print(f"{k:45s} {v}")
    print("now", now)
    for k, v in res["spans"].items():
        print(k, v)


def page(res):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--dn:#cf222e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1200px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Gold and Jupiter</title><style>{css}</style></head><body>",
         "<h1>Gold crashes and Jupiter's afflictions: the note checked</h1>",
         "<p class='s'>Sidereal Lahiri, mean node, whole-sign relations; Vedha by TA's Sarvatobhadra wheel. Crashes: 15%+ falls on monthly gold since 1972 and 10%+ on daily COMEX gold since 2000.</p>",
         "<h2>1. Year by year</h2><div class='wrap'><table><thead><tr><th>Year and claim</th><th>Crash (peak → trough)</th><th>At the peak</th><th>Malefic vedha on Jupiter</th></tr></thead><tbody>"]

    def facts(st):
        keys = [k for k, v in st.items() if v is True]
        return f"Jupiter {st['Jupiter sign']} ({st['Jupiter nakshatra']}), Saturn {st['Saturn sign']}; " + ("; ".join(keys) if keys else "no affliction")
    for c in res["claims"]:
        if not c["episodes"]:
            o.append(f"<tr><td><b>{c['year']}</b> {E(c['claim'])}</td><td colspan='3'>no qualifying crash found</td></tr>")
        for e in c["episodes"]:
            dur = "; ".join(f"{k} {v}%" for k, v in e["during"].items() if k != "afflicted")
            o.append(f"<tr><td><b>{c['year']}</b> {E(c['claim'])}</td><td class='n'>{e['peak']} → {e['trough']} ({e['depth']}%)</td><td class='s'>{E(facts(e['at_peak']))}<br>share of the fall: {E(dur) or '–'}</td>"
                     f"<td>at the peak: {E(', '.join(e['at_peak']['Malefic vedha on Jupiter']) or 'none')}<br><span class='s'>during the fall: {e['during'].get('Malefic vedha on Jupiter', 0)}% of the time, by {E(', '.join(e['vedha_by']) or 'none')}</span></td></tr>")
    o.append("</tbody></table></div><h2>2. How unusual is it? Monthly gold, 1972–2026</h2><div class='wrap'><table><thead><tr><th>Condition</th><th class='n'>Share of all months</th>"
             "<th class='n'>At crash peaks</th><th class='n'>Gold next 6 months: on / off</th><th class='n'>Next 6 months fell 10%+: on / off</th></tr></thead><tbody>")
    for k, v in res["spec"].items():
        o.append(f"<tr><td>{E(k)}</td><td class='n'>{v['share']}%</td><td class='n'>{v['at_peaks']} of {v['peaks']}</td><td class='n'>{v['f6_on']:+.2f}% / {v['f6_off']:+.2f}%</td>"
                 f"<td class='n'>{v['down6_on']}% / {v['down6_off']}%</td></tr>")
    o.append("</tbody></table></div><h2>3. The current configuration and when it ends</h2><ul>")
    for k, v in res["spans"].items():
        o.append(f"<li><b>{E(k)}:</b> " + (E("; ".join(f"{a} – {b}" for a, b in v)) or "not active before 2028") + "</li>")
    o.append("</ul><p class='s'>Generated by tools/gold_jupiter_crash.py. Monthly prices: datasets/gold-prices (monthly averages). Market prices and astrology only.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
