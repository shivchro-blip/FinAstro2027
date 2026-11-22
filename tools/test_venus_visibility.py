"""Test of the TA Section 18 Venus combustion / rising rules on gold and silver, 2000-2026,
with a close look at the 30 Jan 2026 gold crash and Venus rising in the West on 31 Jan 2026.

    python tools/test_venus_visibility.py

Rules (TA p.71 [printed 41] Section 18; silver S35 A15 / B16; KD p.122 / p.124):
  Venus combust in West  - Extreme Bullish (silver Bullish till it rises in East)
  Venus combust in East  - Bullish (the 2026 document: Bearish for 15 days, then Bullish)
  Venus rises in East    - Bullish for 2 to 3 months
  Venus rises in West    - Bearish; in Aries, Leo, Libra, Capricorn or Aquarius with Sun,
                           Mars, Saturn or Rahu - sharp upturn after a small dip
Events come from the catalogue detectors (astronomy layer, kalamsha method at Mumbai,
date-only). Scoring follows PROJECT_KNOWLEDGE section 6: entry = last close before the
event; instants (rises) scored on the 5-trading-day move, windows (combustion) from
entry to the last close inside; FLAT under 0.5%; base = same-horizon moves in the same
Nov-Nov year; one-sided binomial p. Also shown: 20- and 40-session moves (the "2 to 3
months" claim), the move in the 3 sessions BEFORE entry (date-only events can be early or
late by a day), whether a +/-2% day fell within +/-3 calendar days, and the qualified
West-rising pattern (a dip below entry within 5 sessions, then above entry 20 sessions on).
Writes build/pdfref/venus_visibility_test_2000-2026_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import csv
import datetime as dt
import html
import json
import math
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky  # noqa: E402
from finastro.pdfref import catalogue as C  # noqa: E402
from finastro.pdfref.detect import Ctx  # noqa: E402
from finastro.pdfref.engine import Grid, snapshot, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
P0, P1 = dt.date(2000, 11, 20), dt.date(2026, 11, 20)
FLAT = 0.5
RULES = (("ta_s18_venus_combust_west", "Bullish", "window"), ("ta_s18_venus_combust_east", "Bullish", "window"),
         ("ta_s18_venus_rise_east", "Bullish", "instant"), ("ta_s18_venus_rise_west", "Bearish", "instant"))
QUAL_SIGNS = ("Aries", "Leo", "Libra", "Capricorn", "Aquarius")
PRICE = {"gold": "gold_GC_F_daily_2000.csv", "silver": "silver_SI_F_daily_2000.csv"}


def prices(metal):
    rows = list(csv.DictReader(open(OUT / "backtest" / PRICE[metal])))
    return [dt.date.fromisoformat(r["date"]) for r in rows], [float(r["close"]) for r in rows]


def nov_year(d):
    return d.year if d >= dt.date(d.year, 11, 20) else d.year - 1


def binom_p(k, n, p):
    if n == 0:
        return None
    p = min(max(p, 1e-9), 1 - 1e-9)
    lg = math.lgamma
    return min(1.0, sum(math.exp(lg(n + 1) - lg(i + 1) - lg(n - i + 1) + i * math.log(p) + (n - i) * math.log(1 - p)) for i in range(k, n + 1)))


def events():
    rules = {r.id: r for r in C.RULES}
    grid = Grid(utc(2000, 1, 1), utc(2000, 1, 2))
    out = []
    for y in range(2000, 2028):
        f = ROOT / "build" / f"astronomy_{y}.json"
        if not f.exists():
            continue
        ctx = Ctx(grid, Sky.load(f), y)
        for rid, tone, kind in RULES:
            for h in rules[rid].detector(ctx):
                s = h.start.astimezone(ET)
                e = h.end.astimezone(ET) if h.end else None
                key = (rid, s.date())
                if any((x["rule_id"], x["start"].date()) == key for x in out):
                    continue
                info = dict(h.facts)
                sk = snapshot(h.start.replace(microsecond=0))
                ven = sk["Venus"]
                withp = [p for p in ("Sun", "Mars", "Saturn", "Rahu") if sk[p].sign_i == ven.sign_i]
                out.append(dict(rule_id=rid, title=rules[rid].title, tone=tone, kind=kind, start=s, end=e, sign=ven.sign, nak=ven.nak, with_=withp,
                                qualified=rid == "ta_s18_venus_rise_west" and ven.sign in QUAL_SIGNS and bool(withp),
                                days=info.get("days")))
    return sorted(out, key=lambda x: x["start"])


def score(ev, D, Cl):
    def idx_before(t):
        day = t.date() + (dt.timedelta(days=1) if t.hour >= 17 else dt.timedelta(0))
        return bisect.bisect_left(D, day) - 1
    a = idx_before(ev["start"])
    if a < 5 or a + 40 >= len(D):
        fwd = lambda n: None if a + n >= len(D) else round((Cl[a + n] / Cl[a] - 1) * 100, 2)  # noqa: E731
    else:
        fwd = lambda n: round((Cl[a + n] / Cl[a] - 1) * 100, 2)  # noqa: E731
    if ev["kind"] == "window" and ev["end"]:
        b = idx_before(ev["end"] + dt.timedelta(minutes=1))
        b = max(b, a + 1)
        main = round((Cl[b] / Cl[a] - 1) * 100, 2) if b < len(D) else None
        horizon = b - a
    else:
        main, horizon = fwd(5), 5
    d0 = ev["start"].date()
    near = [(D[i], round((Cl[i] / Cl[i - 1] - 1) * 100, 2)) for i in range(max(1, a - 6), min(len(D), a + 7)) if abs((D[i] - d0).days) <= 3]
    big = [x for x in near if abs(x[1]) >= 2]
    dip = min(Cl[a + 1:a + 6]) < Cl[a] if a + 6 <= len(D) else None
    pattern = None if fwd(20) is None or dip is None else bool(dip and fwd(20) > 0)
    return dict(entry=D[a].isoformat(), entry_close=Cl[a], pre3=round((Cl[a] / Cl[a - 3] - 1) * 100, 2), main=main, horizon=horizon,
                f5=fwd(5), f20=fwd(20), f40=fwd(40), big_near=[(d.isoformat(), r) for d, r in big], dip_then_up=pattern,
                outcome=None if main is None else "FLAT" if abs(main) < FLAT else ("WORKED" if (main > 0) == (ev["tone"] == "Bullish") else "FAILED"))


def base_tables(D, Cl):
    """Per Nov-Nov year: P(up | |move| > FLAT) for horizons 1-60, share of 7-day windows with a +/-2% day, dip-then-up share."""
    out = {}
    for y in range(P0.year, P1.year):
        idx = [i for i in range(6, len(D) - 41) if nov_year(D[i]) == y]
        if not idx:
            continue
        t = {}
        for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 40):
            rs = [(Cl[i + n] / Cl[i] - 1) * 100 for i in idx]
            up, dn = sum(r > FLAT for r in rs), sum(r < -FLAT for r in rs)
            t[n] = up / max(up + dn, 1)
        bigd = {D[i] for i in idx if abs(Cl[i] / Cl[i - 1] - 1) >= 0.02}
        t["big7"] = sum(1 for i in idx if any(abs((b - D[i]).days) <= 3 for b in bigd)) / len(idx)
        t["dip_up"] = sum(1 for i in idx if min(Cl[i + 1:i + 6]) < Cl[i] and Cl[i + 20] > Cl[i]) / len(idx)
        out[y] = t
    return out


def summarise(rows, tone, base, key="main"):
    sel = [r for r in rows if r["s"][key] is not None and P0 <= r["start"].date() < P1]
    if not sel:
        return dict(n=0)
    w = f_ = 0
    exp = 0.0
    for r in sel:
        v = r["s"][key]
        if abs(v) < FLAT:
            continue
        y = nov_year(r["start"].date())
        n = {"main": r["s"]["horizon"], "f5": 5, "f20": 20, "f40": 40}[key]
        bt = base.get(y)
        if not bt:
            continue
        k = min((x for x in bt if isinstance(x, int)), key=lambda x: abs(x - n))
        pu = bt[k]
        exp += pu if tone == "Bullish" else 1 - pu
        if (v > 0) == (tone == "Bullish"):
            w += 1
        else:
            f_ += 1
    dec = w + f_
    b = exp / dec if dec else None
    return dict(n=len(sel), worked=w, failed=f_, hit=round(w / dec * 100) if dec else None, base=round(b * 100) if b else None,
                p=round(binom_p(w, dec, b), 3) if dec else None, avg=round(sum(r["s"][key] for r in sel) / len(sel), 2))


def main():
    evs = events()
    res = dict(rules=[], events=[], case_2026={}, forward=[])
    tables = {}
    for metal in ("gold", "silver"):
        D, Cl = prices(metal)
        base = base_tables(D, Cl)
        tables[metal] = base
        for ev in evs:
            if ev["start"].date() < P1:
                ev.setdefault("by", {})[metal] = score(ev, D, Cl)
    for rid, tone, kind in RULES:
        rule = dict(rule_id=rid, title=next(e["title"] for e in evs if e["rule_id"] == rid), tone=tone, kind=kind, metals={})
        for metal in ("gold", "silver"):
            rows = [dict(e, s=e["by"][metal]) for e in evs if e["rule_id"] == rid and "by" in e]
            base = tables[metal]
            m = dict(main=summarise(rows, tone, base), f20=summarise(rows, tone, base, "f20"), f40=summarise(rows, tone, base, "f40"))
            dec = [r for r in rows if P0 <= r["start"].date() < P1]
            m["big_near"] = sum(1 for r in dec if r["s"]["big_near"])
            m["big_near_exp"] = round(sum(base[nov_year(r["start"].date())]["big7"] for r in dec if nov_year(r["start"].date()) in base), 1)
            m["pre3_avg"] = round(sum(r["s"]["pre3"] for r in dec) / len(dec), 2) if dec else None
            m["pre3_down"] = sum(1 for r in dec if r["s"]["pre3"] < -FLAT)
            if rid == "ta_s18_venus_rise_west":
                q = [r for r in dec if r["qualified"] and r["s"]["dip_then_up"] is not None]
                m["qualified"] = dict(n=len(q), pattern=sum(1 for r in q if r["s"]["dip_then_up"]),
                                      expected=round(sum(base[nov_year(r["start"].date())]["dip_up"] for r in q), 1),
                                      dates=[r["start"].date().isoformat() for r in q])
                nq = [r for r in dec if not r["qualified"]]
                m["unqualified"] = summarise(nq, tone, base)
            rule["metals"][metal] = m
        res["rules"].append(rule)
    for e in evs:
        res["events"].append(dict(rule_id=e["rule_id"], title=e["title"], tone=e["tone"], start=e["start"].isoformat(), end=e["end"].isoformat() if e["end"] else None,
                                  sign=e["sign"], nakshatra=e["nak"], with_=e["with_"], qualified=e["qualified"], days=e["days"], by=e.get("by", {})))
    # 2026 case study
    D, Cl = prices("gold")
    sD, sC = prices("silver")
    S = dict(zip(sD, sC))
    case = []
    for i in range(len(D)):
        if dt.date(2026, 1, 14) <= D[i] <= dt.date(2026, 2, 27):
            j = sD.index(D[i]) if D[i] in S else None
            case.append(dict(date=D[i].isoformat(), gold=Cl[i], gold_ret=round((Cl[i] / Cl[i - 1] - 1) * 100, 2),
                             silver=S.get(D[i]), silver_ret=round((sC[j] / sC[j - 1] - 1) * 100, 2) if j else None))
    rw = next(e for e in evs if e["rule_id"] == "ta_s18_venus_rise_west" and e["start"].year == 2026)
    sk = snapshot(dt.datetime(2026, 1, 31, 12, tzinfo=ET).astimezone(dt.timezone.utc))
    res["case_2026"] = dict(rise=rw["start"].isoformat(), sign=rw["sign"], nakshatra=rw["nak"], with_=rw["with_"], qualified=rw["qualified"], days=case,
                            sky={p: f"{sk[p].sign} {sk[p].nak}{' R' if getattr(sk[p], 'retro', False) else ''}" for p in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")},
                            gold_by=rw["by"]["gold"], silver_by=rw["by"]["silver"])
    res["forward"] = [dict(rule_id=e["rule_id"], title=e["title"], tone=e["tone"], start=e["start"].isoformat(), end=e["end"].isoformat() if e["end"] else None,
                           sign=e["sign"], nakshatra=e["nak"], with_=e["with_"], qualified=e["qualified"]) for e in evs if e["start"].date() >= P1]
    json.dump(res, open(OUT / "venus_visibility_test_2000-2026_ET.json", "w"), indent=1, default=str)
    write(res)
    for r in res["rules"]:
        for metal, m in r["metals"].items():
            mm = m["main"]
            print(f"{r['title']:24s} {metal:6s} {mm.get('worked')}/{(mm.get('worked') or 0) + (mm.get('failed') or 0)} hit {mm.get('hit')}% base {mm.get('base')}% p {mm.get('p')} avg {mm.get('avg')}  "
                  f"20d {m['f20'].get('hit')}%/{m['f20'].get('base')}%  40d {m['f40'].get('hit')}%/{m['f40'].get('base')}%  big±3d {m['big_near']}/{m['big_near_exp']}  pre3 avg {m['pre3_avg']} down {m['pre3_down']}"
                  + (f"  qualified {m['qualified']}" if "qualified" in m else ""))
    print("2026:", res["case_2026"]["rise"], res["case_2026"]["sign"], res["case_2026"]["with_"], res["case_2026"]["gold_by"])
    for f in res["forward"]:
        print("fwd", f["start"][:10], f["title"], f["sign"], f["with_"], f["qualified"])


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]

    def fmt(v, pct=True):
        return "–" if v is None else (f"{v:+.2f}%" if pct else str(v))

    def rec(m):
        if not m.get("n"):
            return "–"
        dec = (m["worked"] or 0) + (m["failed"] or 0)
        return f"{m['worked']}/{dec} ({m['hit']}% vs {m['base']}%, p {m['p']})" if dec else "0 decided"
    rrows = ""
    for r in res["rules"]:
        for metal, m in r["metals"].items():
            ok = m["main"].get("hit") is not None and m["main"].get("base") is not None and m["main"]["hit"] >= m["main"]["base"] + 10
            bad = m["main"].get("hit") is not None and m["main"].get("base") is not None and m["main"]["hit"] <= m["main"]["base"] - 10
            rrows += (f"<tr class='{'bullish' if ok else 'bearish' if bad else 'mixed'}'><td><b>{html.escape(r['title'])}</b></td><td>{r['tone']}</td><td>{metal}</td><td class='n'>{m['main']['n']}</td>"
                      f"<td class='n'>{rec(m['main'])}</td><td class='n'>{fmt(m['main'].get('avg'))}</td><td class='n'>{rec(m['f20'])}</td><td class='n'>{rec(m['f40'])}</td>"
                      f"<td class='n'>{m['big_near']} vs {m['big_near_exp']}</td><td class='n'>{fmt(m['pre3_avg'])} ({m['pre3_down']} down)</td></tr>")
    rw = next(r for r in res["rules"] if r["rule_id"] == "ta_s18_venus_rise_west")
    qual = "".join(f"<li><b>{metal}:</b> qualified rises (Venus in Aries, Leo, Libra, Capricorn or Aquarius with Sun, Mars, Saturn or Rahu) {m['qualified']['n']}: "
                   f"dip-then-upturn in {m['qualified']['pattern']} against {m['qualified']['expected']} expected from the same years ({', '.join(m['qualified']['dates'])}). "
                   f"Unqualified rises, scored Bearish: {rec(m['unqualified'])}.</li>" for metal, m in rw["metals"].items())
    erows = ""
    for e in res["events"]:
        if not e["by"]:
            continue
        g, s = e["by"]["gold"], e["by"]["silver"]
        cls = {"WORKED": "bullish", "FAILED": "bearish"}.get(g["outcome"], "mixed")
        erows += (f"<tr class='{cls}'><td class='w'>{e['start'][:10]}{' – ' + e['end'][:10] if e['end'] else ''}</td><td>{html.escape(e['title'])}</td><td>{e['tone']}</td>"
                  f"<td>{e['sign']} / {e['nakshatra']}{' with ' + ', '.join(e['with_']) if e['with_'] else ''}{' <b>(qualified)</b>' if e['qualified'] else ''}</td>"
                  f"<td class='n'>{fmt(g['pre3'])}</td><td class='n'><b>{fmt(g['main'])}</b> {g['outcome'] or ''}</td><td class='n'>{fmt(g['f20'])}</td><td class='n'>{fmt(g['f40'])}</td>"
                  f"<td class='s'>{', '.join(f'{d} {r:+.1f}%' for d, r in g['big_near']) or '-'}</td><td class='n'>{fmt(s['main'])} {s['outcome'] or ''}</td></tr>")
    c = res["case_2026"]
    def crow(x):
        cls = "bearish" if x["gold_ret"] <= -2 else "bullish" if x["gold_ret"] >= 2 else ""
        mark = " <b>← last close before Venus rises in the West</b>" if x["date"] == c["gold_by"]["entry"] else ""
        sv = "" if x["silver"] is None else f"{x['silver']:,.2f}"
        sr = "" if x["silver_ret"] is None else f"{x['silver_ret']:+.2f}%"
        return (f"<tr class='{cls}'><td class='w'>{dt.date.fromisoformat(x['date']):%a %d %b %Y}{mark}</td><td class='n'>{x['gold']:,.1f}</td>"
                f"<td class='n'><b>{x['gold_ret']:+.2f}%</b></td><td class='n'>{sv}</td><td class='n'>{sr}</td></tr>")
    crows = "".join(crow(x) for x in c["days"])
    sky = "; ".join(f"{p} {v}" for p, v in c["sky"].items())
    frows = "".join(f"<tr><td class='w'>{f['start'][:10]}{' – ' + f['end'][:10] if f['end'] else ''}</td><td>{html.escape(f['title'])}</td><td>{f['tone']}</td>"
                    f"<td>{f['sign']} / {f['nakshatra']}{' with ' + ', '.join(f['with_']) if f['with_'] else ''}{' (qualified)' if f['qualified'] else ''}</td></tr>" for f in res["forward"])
    g = c["gold_by"]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Venus Rising Test</title><style>{css}</style></head><body>
<h1>Venus combust and rising (TA Section 18) on gold and silver, 2000–2026, and the January 2026 gold crash</h1>
<p class="m">Rules, TA p.71 [printed 41] Section 18 (silver S35 A15 / B16; KD p.122, p.124): Venus combust in West – Extreme Bullish; combust in East – Bullish; rises in East – Bullish for 2–3 months;
<b>rises in West – Bearish; in Aries, Leo, Libra, Capricorn or Aquarius with Sun, Mars, Saturn or Rahu – sharp upturn after a small dip</b>.
Dates are the astronomy layer's (kalamsha method at Mumbai, date-only). Scoring as in PROJECT_KNOWLEDGE §6: entry = last close before the event; rises on the 5-session move, combustion from entry to the last close inside it; base = same horizon, same Nov–Nov year.</p>
<h2>The January 2026 case</h2>
<p class="m">Venus rose in the West on <b>{dt.date.fromisoformat(c['rise'][:10]):%a %d %b %Y}</b> (1 Feb IST), in {c['sign']} / {c['nakshatra']} with {', '.join(c['with_'])} – so the <b>qualified</b> form of the rule applies (sharp upturn after a small dip).
Sky at noon ET on 31 Jan: {html.escape(sky)}.</p>
<p class="m">Gold fell <b>10.8%</b> on Fri 30 Jan and 1.95% on Mon 2 Feb, then rose 6.1% on Tue 3 Feb and was back above 5,000 by 9 Feb. The fall came the session <b>before</b> the date the layer gives for the rising, so under the standard scoring (entry {g['entry']} at {g['entry_close']:,.1f}) the event is credited with the move after the crash:
5 sessions {fmt(g['f5'])}, 20 sessions {fmt(g['f20'])}, 40 sessions {fmt(g['f40'])}; the 3 sessions into the event {fmt(g['pre3'])}. Read loosely – a fall around the rising followed by a sharp recovery – it matches the qualified rule's “dip then sharp upturn”, but the dip was not small and it came first.</p>
<div class="wrap"><table><thead><tr><th>Date</th><th>Gold (GC=F)</th><th>Change</th><th>Silver (SI=F)</th><th>Change</th></tr></thead><tbody>{crows}</tbody></table></div>
<h2>26-year record</h2>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Says</th><th>Metal</th><th>Events</th><th>Scored move: worked / decided (hit vs base, p)</th><th>Average move</th><th>20 sessions</th><th>40 sessions</th><th>±2% day within ±3 days (vs expected)</th><th>3 sessions before entry (avg; times down)</th></tr></thead><tbody>{rrows}</tbody></table></div>
<ul class="m">{qual}</ul>
<h2>Every event</h2>
<div class="wrap"><table><thead><tr><th>Date(s)</th><th>Rule</th><th>Says</th><th>Venus</th><th>Gold: 3 sessions before</th><th>Gold: scored move</th><th>Gold 20 s.</th><th>Gold 40 s.</th><th>Gold ±2% days within ±3 days</th><th>Silver: scored move</th></tr></thead><tbody>{erows}</tbody></table></div>
<h2>Next dates (20 Nov 2026 – 2027)</h2>
<div class="wrap"><table><thead><tr><th>Date(s)</th><th>Rule</th><th>Says</th><th>Venus</th></tr></thead><tbody>{frows}</tbody></table></div>
<p class="s">Generated by tools/test_venus_visibility.py.</p></body></html>"""
    (OUT / "venus_visibility_test_2000-2026_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
