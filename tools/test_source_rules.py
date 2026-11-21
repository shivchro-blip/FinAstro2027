"""Test the gold / silver rules found in the 'Others' documents, 2000-2026.

    python tools/test_source_rules.py

Sources (Reference_materials/Others, review in Reference_materials/extracted/OTHERS_FINANCIAL_REVIEW.md):
  BS   Brihat Samhita (P.S. Sastri 1946): Ch.41 (substances by sign: gold = Mesha
       and Makara, sl.2 and 7), Ch.42 (fluctuation of prices) and Ch.10 sl.17.
  TS   Timing Solutions for Swing Traders (Lee & Tryde 2012) Ch.9 pp.170-172.
  SG   'The Moon and Silver' guide (Reference_materials/Others/Silver/*.docx),
       a modern compilation that cites TS, BPHS and March & McEvers.

Every rule is tested exactly as its source states it; nothing is optimised.
Prices: Yahoo GC=F / SI=F daily closes, 30 Aug 2000 - 20 Nov 2026
(build/pdfref/backtest/*_daily_2000.csv). Positions: Swiss Ephemeris, Lahiri.

Daily rules use the COMEX session (18:00 ET the day before -> 17:00 ET): a
condition counts for a day when it holds in at least half of the session's
hourly samples, and is scored against that day's close-to-close move. The
state is known in advance from the ephemeris, so there is no look-ahead.

Writes build/pdfref/source_rules_test_2000-2026_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import csv
import datetime as dt
import html
import json
import math
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.pdfref.detect import aspects  # noqa: E402
from finastro.pdfref.engine import Grid, crossings, snapshot, spans, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
OUT = ROOT / "build" / "pdfref"
FILES = {"silver": OUT / "backtest" / "silver_SI_F_daily_2000.csv", "gold": OUT / "backtest" / "gold_GC_F_daily_2000.csv"}
BENEFICS = ("Jupiter", "Venus", "Mercury")
MALEFICS = ("Saturn", "Mars", "Rahu", "Ketu")
GOLD_SIGNS = ("Aries", "Capricorn")          # BS 41.2, 41.7
BLOCKS = [(2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020), (2020, 2027)]


def load(path):
    rows = list(csv.DictReader(open(path)))
    return [dt.date.fromisoformat(r["date"]) for r in rows], [float(r["close"]) for r in rows]


PX = {m: load(f) for m, f in FILES.items()}


def idx_before(D, t):
    """Last close strictly before instant t (ET; a close is at 17:00)."""
    x = t.astimezone(ET)
    day = x.date() + (dt.timedelta(days=1) if x.hour >= 17 else dt.timedelta(0))
    return bisect.bisect_left(D, day) - 1


def binom_p(k, n, p):
    if not n:
        return None
    lp, lq = math.log(p), math.log(1 - p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq) for i in range(k, n + 1)))


def tstat(a, b):
    if len(a) < 3 or len(b) < 3:
        return None
    va, vb = statistics.pvariance(a), statistics.pvariance(b)
    return (statistics.fmean(a) - statistics.fmean(b)) / math.sqrt(va / len(a) + vb / len(b))


def angle(a, b):
    return abs(((a - b + 180) % 360) - 180)


# ------------------------------------------------------------------ daily Moon factors (SG)
def session_samples(day):
    s = dt.datetime.combine(day - dt.timedelta(days=1), dt.time(18), ET)
    return [(s + dt.timedelta(hours=h)).astimezone(UTC).replace(microsecond=0) for h in range(0, 23, 2)]


DAILY = {
    # name: (source, stated effect, predicate on snapshot)
    "Shukla paksha (waxing Moon)": ("SG ch.4 (Paksha: Shukla = BULLISH); TS p.171 accumulation", "up", lambda s: s.paksha == "Shukla"),
    "Krishna paksha (waning Moon)": ("SG ch.4 (Krishna = BEARISH); TS p.171 redistribution", "down", lambda s: s.paksha == "Krishna"),
    "Moon in Taurus (exalted)": ("SG ch.2 (highest reliability) / ch.16 strongest BUY", "up", lambda s: s["Moon"].sign == "Taurus"),
    "Moon in Cancer (own sign)": ("SG ch.2 (very high)", "up", lambda s: s["Moon"].sign == "Cancer"),
    "Moon in Scorpio (debilitated)": ("SG ch.2 / ch.16 strongest SELL", "down", lambda s: s["Moon"].sign == "Scorpio"),
    "Moon in Rohini": ("SG ch.3 (supreme nakshatra for silver)", "up", lambda s: s["Moon"].nak == "Rohini"),
    "Moon in Rohini, Hasta or Shravana": ("SG ch.3 (Moon's own nakshatras)", "up", lambda s: s["Moon"].nak in ("Rohini", "Hasta", "Shravana")),
    "Rikta tithi (4, 9, 14)": ("SG ch.5 (avoid new trades)", "volatility", lambda s: s.tithi % 15 in (4, 9, 14)),
    "Jupiter conjunct or trine Moon (8 deg)": ("SG ch.6 (signal strengthened / confirmed)", "up",
                                               lambda s: angle(s["Jupiter"].lon, s["Moon"].lon) <= 8 or abs(angle(s["Jupiter"].lon, s["Moon"].lon) - 120) <= 8),
    "Saturn conjunct Moon (8 deg)": ("SG ch.6 (Moon suppressed; WAIT)", "down", lambda s: angle(s["Saturn"].lon, s["Moon"].lon) <= 8),
    "Mars conjunct or opposite Moon (8 deg)": ("SG ch.6 (DO NOT TRADE; extreme volatility)", "volatility",
                                               lambda s: angle(s["Mars"].lon, s["Moon"].lon) <= 8 or abs(angle(s["Mars"].lon, s["Moon"].lon) - 180) <= 8),
}


def daily_table(metal):
    D, C = PX[metal]
    rows = []
    for i in range(1, len(D)):
        if D[i] > dt.date(2026, 11, 20):
            break
        ss = [snapshot(t) for t in session_samples(D[i])]
        flags = {k: sum(f(s) for s in ss) * 2 >= len(ss) for k, (_, _, f) in DAILY.items()}
        rows.append((D[i], (C[i] / C[i - 1] - 1) * 100, flags))
    return rows


def score_daily(rows):
    out = []
    allr = [r for _, r, _ in rows]
    for k, (src, eff, _) in DAILY.items():
        on = [r for d, r, f in rows if f[k]]
        off = [r for d, r, f in rows if not f[k]]
        res = dict(rule=k, source=src, effect=eff, days=len(on), share=round(len(on) / len(rows) * 100, 1),
                   mean_on=round(statistics.fmean(on), 3), mean_off=round(statistics.fmean(off), 3), t=round(tstat(on, off), 2))
        if eff in ("up", "down"):
            base = sum(r > 0 for r in allr) / len(allr)
            p = base if eff == "up" else 1 - base
            hits = sum((r > 0) if eff == "up" else (r < 0) for r in on)
            res.update(hit=round(hits / len(on) * 100, 1), base=round(p * 100, 1), p_value=round(binom_p(hits, len(on), p), 3))
            blk = []
            for a, b in BLOCKS:
                sel = [r for d, r, f in rows if f[k] and a <= d.year < b]
                if sel:
                    blk.append(round(statistics.fmean(sel), 3))
            res["block_means"] = blk
            res["blocks_right"] = sum(1 for x in blk if (x > 0) == (eff == "up"))
        else:
            res.update(abs_on=round(statistics.fmean(abs(r) for r in on), 3), abs_off=round(statistics.fmean(abs(r) for r in off), 3),
                       t_abs=round(tstat([abs(r) for r in on], [abs(r) for r in off]), 2))
        out.append(res)
    return out


# ------------------------------------------------------------------ lunation cycle (TS / SG)
def lunations(grid):
    """New and full Moon instants from the elongation crossing 0 / 180 deg."""
    out = []
    for t, a, b in crossings(grid, lambda s: int(((s["Moon"].lon - s["Sun"].lon) % 360) // 180)):
        out.append((t, "full" if b == 1 else "new"))
    return out


def lunation_cycle(metal, lun):
    D, C = PX[metal]
    res = {"new_to_full": [], "full_to_new": []}
    for (t0, k0), (t1, k1) in zip(lun, lun[1:]):
        a, b = idx_before(D, t0), idx_before(D, t1)
        if a < 0 or b >= len(D) or b <= a:
            continue
        r = (C[b] / C[a] - 1) * 100
        res["new_to_full" if k0 == "new" else "full_to_new"].append((D[a], r))
    out = {}
    for k, v in res.items():
        rs = [r for _, r in v]
        blk = [round(statistics.fmean([r for d, r in v if a <= d.year < b]), 2) for a, b in BLOCKS if any(a <= d.year < b for d, _ in v)]
        comp = 1.0
        for r in rs:
            comp *= 1 + r / 100
        out[k] = dict(n=len(rs), mean=round(statistics.fmean(rs), 3), up=round(sum(r > 0 for r in rs) / len(rs) * 100, 1),
                      compounded=round((comp - 1) * 100, 1), block_means=blk)
    out["t"] = round(tstat([r for _, r in res["new_to_full"]], [r for _, r in res["full_to_new"]]), 2)
    return out


# ------------------------------------------------------------------ Brihat Samhita rules
def bs_leo_store(metal, grid):
    """BS 42.6: store gold ... silver when the Sun is in Simha; sell in the 5th month."""
    D, C = PX[metal]
    ing = [(t, b) for t, a, b in crossings(grid, lambda s: s["Sun"].sign)]
    trades = []
    for t, sg in ing:
        if sg != "Leo":
            continue
        sell5 = next((u for u, s2 in ing if u > t and s2 == "Sagittarius"), None)    # 5th solar month begins
        sell6 = next((u for u, s2 in ing if u > t and s2 == "Capricorn"), None)      # 5th month ends
        a = idx_before(D, t)
        if a < 0 or sell6 is None or idx_before(D, sell6) >= len(D) or sell6.astimezone(ET).date() > D[-1]:
            continue
        b5, b6 = idx_before(D, sell5), idx_before(D, sell6)
        trades.append(dict(buy=D[a].isoformat(), sell_start5=D[b5].isoformat(), sell_end5=D[b6].isoformat(),
                           ret_start5=round((C[b5] / C[a] - 1) * 100, 2), ret_end5=round((C[b6] / C[a] - 1) * 100, 2)))
    # base: same-length holds started on every other trading day of the year
    n5 = round(statistics.fmean([(dt.date.fromisoformat(x["sell_start5"]) - dt.date.fromisoformat(x["buy"])).days for x in trades]))
    base = []
    for i in range(len(D)):
        j = bisect.bisect_left(D, D[i] + dt.timedelta(days=n5))
        if j < len(D):
            base.append((C[j] / C[i] - 1) * 100)
    r5 = [x["ret_start5"] for x in trades]
    r6 = [x["ret_end5"] for x in trades]
    return dict(trades=trades, n=len(trades), up5=sum(r > 0 for r in r5), mean5=round(statistics.fmean(r5), 2), up6=sum(r > 0 for r in r6),
                mean6=round(statistics.fmean(r6), 2), base_mean=round(statistics.fmean(base), 2), base_up=round(sum(r > 0 for r in base) / len(base) * 100, 1),
                hold_days=n5, p_up5=round(binom_p(sum(r > 0 for r in r5), len(r5), sum(r > 0 for r in base) / len(base)), 3))


def with_or_asp(s, b, tgt):
    return s[b].sign_i == s[tgt].sign_i or (b != "Ketu" and aspects(s, b, tgt))


def bs_lunation_gold(lun):
    """BS 42.14a: New/Full Moon with or aspected by benefics raises prices of the
    Moon's sign's articles -> gold when that sign is Mesha or Makara."""
    D, C = PX["gold"]
    hits = []
    for (t, k), nxt in zip(lun, lun[1:] + [(None, None)]):
        s = snapshot(t.replace(second=0, microsecond=0))
        if s["Moon"].sign not in GOLD_SIGNS:
            continue
        ben = [b for b in BENEFICS if with_or_asp(s, b, "Moon")]
        a = idx_before(D, t)
        if a < 0 or a + 10 >= len(D):
            continue
        r5 = (C[a + 5] / C[a] - 1) * 100
        r10 = (C[a + 10] / C[a] - 1) * 100
        rn = (C[idx_before(D, nxt[0])] / C[a] - 1) * 100 if nxt[0] and idx_before(D, nxt[0]) < len(D) else None
        hits.append(dict(date=D[a].isoformat(), kind=k, sign=s["Moon"].sign, benefics=ben, r5=round(r5, 2), r10=round(r10, 2),
                         r_next=round(rn, 2) if rn is not None else None))
    def summ(sel, key):
        rs = [h[key] for h in sel if h[key] is not None]
        return dict(n=len(rs), mean=round(statistics.fmean(rs), 2) if rs else None, up=sum(r > 0 for r in rs))
    w = [h for h in hits if h["benefics"]]
    wo = [h for h in hits if not h["benefics"]]
    return dict(with_benefics={k: summ(w, k) for k in ("r5", "r10", "r_next")}, without={k: summ(wo, k) for k in ("r5", "r10", "r_next")}, events=hits)


def window_returns(metal, pred, grid, lo=dt.date(2000, 9, 1)):
    D, C = PX[metal]
    out = []
    for w in spans(grid, pred):
        if w.start.astimezone(ET).date() < lo:
            continue
        a, b = idx_before(D, w.start), idx_before(D, w.end)
        if b - a < 2:
            continue
        out.append(dict(start=D[a].isoformat(), end=D[b].isoformat(), days=b - a, ret=round((C[b] / C[a] - 1) * 100, 2)))
    return out


def base_same_len(metal, lens):
    D, C = PX[metal]
    rs = []
    for n in lens:
        for i in range(0, len(D) - n, 5):
            rs.append((C[i + n] / C[i] - 1) * 100)
    return round(sum(r < 0 for r in rs) / len(rs) * 100, 1)


def main():
    grid = Grid(utc(2000, 6, 1), utc(2026, 12, 31))
    lun = lunations(grid)
    res = {"daily": {}, "lunation_cycle": {}, "bs_leo_store": {}}
    for m in ("silver", "gold"):
        rows = daily_table(m)
        res["daily"][m] = score_daily(rows)
        res["lunation_cycle"][m] = lunation_cycle(m, lun)
        res["bs_leo_store"][m] = bs_leo_store(m, grid)
    res["bs_lunation_gold"] = bs_lunation_gold(lun)
    sun_mal = window_returns("gold", lambda s: s["Sun"].sign in GOLD_SIGNS and tuple(b for b in MALEFICS if with_or_asp(s, b, "Sun")) or False, grid)
    res["bs_sun_malefic_gold"] = dict(windows=sun_mal, n=len(sun_mal), down=sum(w["ret"] < 0 for w in sun_mal),
                                      mean=round(statistics.fmean(w["ret"] for w in sun_mal), 2) if sun_mal else None,
                                      base_down=base_same_len("gold", [w["days"] for w in sun_mal]))
    sat = window_returns("gold", lambda s: s["Saturn"].nak == "Uttara Bhadrapada", grid)
    res["bs_saturn_ubhadra_gold"] = dict(windows=sat, n=len(sat), down=sum(w["ret"] < 0 for w in sat))
    json.dump(res, open(OUT / "source_rules_test_2000-2026_ET.json", "w"), indent=1, default=str)
    write(res)


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]

    def drow(r, m):
        eff = r["effect"]
        if eff in ("up", "down"):
            right = r["hit"] > r["base"] and ((r["mean_on"] > r["mean_off"]) if eff == "up" else (r["mean_on"] < r["mean_off"]))
            cls = "bullish" if right and r["p_value"] < 0.05 else "mixed" if right else "bearish"
            res_ = f"{r['hit']}% vs {r['base']}% (p = {r['p_value']})"
            extra = f"{r['blocks_right']}/{len(r['block_means'])}"
        else:
            cls = "bullish" if abs(r["t_abs"]) >= 2 and r["abs_on"] > r["abs_off"] else "mixed"
            res_ = f"avg size of move {r['abs_on']}% vs {r['abs_off']}% (t = {r['t_abs']})"
            extra = ""
        return (f"<tr class='{cls}'><td><b>{html.escape(r['rule'])}</b><div class='s'>{html.escape(r['source'])}</div></td><td>{eff}</td><td class='n'>{r['days']} ({r['share']}%)</td>"
                f"<td class='n'>{r['mean_on']:+.3f}%</td><td class='n'>{r['mean_off']:+.3f}%</td><td class='n'>{r['t']}</td><td class='n'>{res_}</td><td class='n'>{extra}</td></tr>")

    daily_html = "".join(f"<h3>{m.capitalize()}</h3><div class='wrap'><table><thead><tr><th>Moon condition (source)</th><th>Stated effect</th><th>Days</th><th>Avg day when present</th><th>Avg day otherwise</th><th>t</th><th>Result</th><th>5-yr blocks right</th></tr></thead><tbody>"
                         + "".join(drow(r, m) for r in res["daily"][m]) + "</tbody></table></div>" for m in ("silver", "gold"))
    lc = "".join(f"<tr><td>{m.capitalize()}</td><td class='n'>{v['new_to_full']['n']}</td><td class='n'>{v['new_to_full']['mean']:+.3f}%</td><td class='n'>{v['new_to_full']['up']}%</td><td class='n'>{v['new_to_full']['compounded']:+.0f}%</td>"
                 f"<td class='n'>{v['full_to_new']['mean']:+.3f}%</td><td class='n'>{v['full_to_new']['up']}%</td><td class='n'>{v['full_to_new']['compounded']:+.0f}%</td><td class='n'>{v['t']}</td>"
                 f"<td class='s'>{' / '.join(f'{a:+.2f}' for a in v['new_to_full']['block_means'])}<br>{' / '.join(f'{a:+.2f}' for a in v['full_to_new']['block_means'])}</td></tr>" for m, v in res["lunation_cycle"].items())
    leo = "".join(f"<tr><td>{m.capitalize()}</td><td class='n'>{v['n']}</td><td class='n'>{v['up5']}/{v['n']}</td><td class='n'>{v['mean5']:+.2f}%</td><td class='n'>{v['up6']}/{v['n']}</td><td class='n'>{v['mean6']:+.2f}%</td>"
                  f"<td class='n'>{v['base_up']}% up, {v['base_mean']:+.2f}%</td><td class='n'>{v['p_up5']}</td></tr>" for m, v in res["bs_leo_store"].items())
    leo_tr = "".join(f"<tr><td>{x['buy']}</td><td>{x['sell_start5']}</td><td class='n'>{x['ret_start5']:+.1f}%</td><td>{x['sell_end5']}</td><td class='n'>{x['ret_end5']:+.1f}%</td></tr>" for x in res["bs_leo_store"]["gold"]["trades"])
    bl = res["bs_lunation_gold"]
    sm = res["bs_sun_malefic_gold"]
    sat = res["bs_saturn_ubhadra_gold"]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Source Rules Test</title><style>{css}</style></head><body>
<h1>Gold &amp; silver rules from the new documents: test 2000–2026</h1>
<p class="m">Rules taken as stated from Brihat Samhita (BS), Timing Solutions for Swing Traders (TS) and the 'Moon and Silver' guide (SG), tested on COMEX silver (SI=F) and gold (GC=F) daily closes, 30 Aug 2000 – 20 Nov 2026 (about 6,500 trading days). Swiss Ephemeris, Lahiri; nothing optimised. Source pages: Reference_materials/extracted/OTHERS_FINANCIAL_REVIEW.md.
Eleven daily conditions are tested on two metals (22 tests), so about one p-value under 0.05 is expected by chance alone; a real effect should also hold in most 5-year blocks.</p>

<h2>1. New Moon → Full Moon vs Full Moon → New Moon (TS pp.170-171; SG ch.1)</h2>
<p class="m">TS: "buying on the new moon and selling on the next full moon" (RBS 2010 study on FTSE/DAX/HSI; Mikula on soybeans); SG applies it to silver. Each half-cycle is held from the close before the lunation to the close before the next one.</p>
<div class="wrap"><table><thead><tr><th>Metal</th><th>Half-cycles</th><th>New→Full avg</th><th>Up</th><th>Compounded</th><th>Full→New avg</th><th>Up</th><th>Compounded</th><th>t (difference)</th><th>By 5-yr block (New→Full / Full→New)</th></tr></thead><tbody>{lc}</tbody></table></div>

<h2>2. Daily Moon conditions from the Silver guide (and TS paksha)</h2>
<p class="m">Each COMEX day scored by the Moon's state during the session. Directional rules: share of days moving the stated way vs the share for all days, one-sided binomial p. "Volatility" rules (the guide says avoid / do not trade): average size of the day's move when present vs absent.</p>
{daily_html}

<h2>3. Brihat Samhita 42.6: store gold and silver when the Sun is in Simha, sell in the 5th month</h2>
<p class="m">Bought at the close before the Sun's sidereal entry into Leo (mid-August); sold at the start of the 5th solar month (Sun into Sagittarius, mid-December) and at its end (Sun into Capricorn, mid-January). Base = every same-length hold in the data.</p>
<div class="wrap"><table><thead><tr><th>Metal</th><th>Years</th><th>Up, sold mid-Dec</th><th>Avg</th><th>Up, sold mid-Jan</th><th>Avg</th><th>Any same-length hold</th><th>p (up count vs base)</th></tr></thead><tbody>{leo}</tbody></table></div>
<details><summary>Gold, year by year</summary><div class="wrap"><table><thead><tr><th>Bought</th><th>Sold (5th month starts)</th><th>Move</th><th>Sold (5th month ends)</th><th>Move</th></tr></thead><tbody>{leo_tr}</tbody></table></div></details>

<h2>4. Brihat Samhita 42.14 applied to gold (gold's signs Mesha and Makara, 41.2 and 41.7)</h2>
<p class="m">(a) New or full Moon in Aries or Capricorn with a benefic (Jupiter, Venus, Mercury) in the same sign or aspecting it: "promotes invariably the price". Whole-sign drishti as elsewhere in the project.</p>
<div class="wrap"><table><thead><tr><th>Lunations in Aries/Capricorn</th><th>n</th><th>Next 5 days</th><th>Next 10 days</th><th>To next lunation</th></tr></thead><tbody>
<tr><td>With benefics (rule active)</td><td class='n'>{bl['with_benefics']['r5']['n']}</td><td class='n'>{bl['with_benefics']['r5']['mean']:+.2f}% ({bl['with_benefics']['r5']['up']} up)</td><td class='n'>{bl['with_benefics']['r10']['mean']:+.2f}% ({bl['with_benefics']['r10']['up']} up)</td><td class='n'>{bl['with_benefics']['r_next']['mean']:+.2f}% ({bl['with_benefics']['r_next']['up']} up)</td></tr>
<tr><td>Without benefics</td><td class='n'>{bl['without']['r5']['n']}</td><td class='n'>{bl['without']['r5']['mean']:+.2f}% ({bl['without']['r5']['up']} up)</td><td class='n'>{bl['without']['r10']['mean']:+.2f}% ({bl['without']['r10']['up']} up)</td><td class='n'>{bl['without']['r_next']['mean']:+.2f}% ({bl['without']['r_next']['up']} up)</td></tr></tbody></table></div>
<p class="m">(b) Sun in Aries or Capricorn with or aspected by a malefic (Saturn, Mars, Rahu, Ketu): "destroys the price". {sm['n']} windows; gold fell in {sm['down']} ({round(sm['down'] / max(sm['n'], 1) * 100)}% vs {sm['base_down']}% of all same-length windows); average {sm['mean']:+.2f}%.</p>
<h2>5. Brihat Samhita 10.17: Saturn in Uttara Bhadrapada afflicts gold</h2>
<p class="m">Saturn returns to this nakshatra every ~29.5 years, so the 2000–2026 data hold only the current passage: {', '.join(f"{w['start']} → {w['end']} {w['ret']:+.1f}%" for w in sat['windows'])}. Gold fell in {sat['down']} of {sat['n']} windows. The current window runs to 8 Feb 2027.</p>
<p class="s">Generated by tools/test_source_rules.py.</p></body></html>"""
    (OUT / "source_rules_test_2000-2026_ET.html").write_text(page, encoding="utf-8")
    for m in ("silver", "gold"):
        print(m, "lunation", res["lunation_cycle"][m])
        print(m, "leo", {k: v for k, v in res["bs_leo_store"][m].items() if k != "trades"})
        for r in res["daily"][m]:
            print("  ", {k: v for k, v in r.items() if k not in ("source",)})
    print("bs lunation", {k: v for k, v in bl.items() if k != "events"})
    print("sun malefic", {k: v for k, v in sm.items() if k != "windows"})
    print("saturn ubhadra", sat)


if __name__ == "__main__":
    main()
