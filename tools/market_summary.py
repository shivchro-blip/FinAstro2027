"""One page of the stock-market findings (S&P 500 and BSE Sensex, 2000-2026) and the robust dates to end-2027.

    python tools/market_summary.py

Inputs: market_backtest_2000-2026_ET.json (rule direction test), {spx,sensex}_big_moves_2000-2026_ET.json
(+/-2% days), {spx,sensex}_big_move_watch_2026-11-22_to_2027-12-31_ET.json (forward windows).
A big-move factor is called ROBUST when it
  * passes the false-discovery-rate correction (q < 0.10) over all factors,
  * has lift > 1 in both 2000-2013 and 2013-2026, and
  * still has p < 0.01 with Sep 2008 - Jun 2009 and mid-Feb - May 2020 removed (so it is
    not just the two crashes).
Writes build/pdfref/market_summary_2000-2026_ET.html (+ .json).
"""
from __future__ import annotations

import datetime as dt
import html
import importlib.util
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
CRISIS = [(dt.date(2008, 9, 1), dt.date(2009, 6, 30)), (dt.date(2020, 2, 15), dt.date(2020, 5, 31))]
NAMES = {"spx": "S&P 500", "sensex": "BSE Sensex"}


def ex_crisis(key):
    os.environ["FINASTRO_METAL"] = key
    for m in ("metal_cfg", "bma"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("bma", ROOT / "tools" / "big_move_analysis.py")
    M = importlib.util.module_from_spec(spec)
    sys.modules["bma"] = M
    spec.loader.exec_module(M)
    days = [x for x in M.build_days() if not any(a <= x["date"] <= b for a, b in CRISIS)]
    rows, big, _ = M.factor_table(days)
    return {r["factor"]: r for r in rows}, len(big), len(days)


def main():
    bt = json.load(open(OUT / "market_backtest_2000-2026_ET.json"))
    res = dict(markets={})
    for key in NAMES:
        bm = json.load(open(OUT / f"{key}_big_moves_2000-2026_ET.json"))
        wa = json.load(open(OUT / f"{key}_big_move_watch_2026-11-22_to_2027-12-31_ET.json"))
        xc, nbig, ndays = ex_crisis(key)
        robust = []
        for r in sorted(bm["factors"], key=lambda r: r["p"]):
            if r["q"] >= 0.10:
                continue
            x = xc.get(r["factor"])
            ok = bool((r["lift_h1"] or 0) > 1 and (r["lift_h2"] or 0) > 1 and x and x["p"] < 0.01)
            robust.append(dict(factor=r["factor"], lift=r["lift"], big=r["big"], exp=r["exp_big"], q=round(r["q"], 3), episodes=r["episodes"],
                               up_share=r["up_share"], h1=r["lift_h1"], h2=r["lift_h2"], xc_lift=x["lift"] if x else None,
                               xc_p=round(x["p"], 4) if x else None, robust=ok,
                               big_rate=round(r["big"] / r["days"] * 100, 1)))
        names = {x["factor"] for x in robust if x["robust"]}
        fwd = [w for w in wa["windows"] if w["factor"] in names]
        m = bt["markets"][key]
        res["markets"][key] = dict(name=NAMES[key], n_big=bm["n_big"], n_days=bm["n_days"], base_rate=round(bm["n_big"] / bm["n_days"] * 100, 1),
                                   split={k: v for k, v in bm["split"].items() if k != "leads"}, fdr=robust, forward=fwd,
                                   rules=dict(n_scored=m["n_scored"], pooled=m["pooled"], p05=m["p05"], expected_p05=m["expected_p05"], q10=m["q10"],
                                              walk_forward={k: v for k, v in m["walk_forward"].items() if k != "rules"}),
                                   xc=dict(big=nbig, days=ndays))
    res["both_best"] = [dict(title=r["title"], tone=r["tone"],
                             spx=f"{r['spx']['worked']}/{r['spx']['worked'] + r['spx']['failed']} ({r['spx']['hit_rate']}% vs {r['spx']['base_rate']}%, p {r['spx']['p_value']})",
                             sensex=f"{r['sensex']['worked']}/{r['sensex']['worked'] + r['sensex']['failed']} ({r['sensex']['hit_rate']}% vs {r['sensex']['base_rate']}%, p {r['sensex']['p_value']})")
                        for r in bt["rules"] if r["both_best"]]
    json.dump(res, open(OUT / "market_summary_2000-2026_ET.json", "w"), indent=1, default=str)
    write(res)
    for key, m in res["markets"].items():
        print(m["name"], "rules:", m["rules"])
        for x in m["fdr"]:
            print(f"   {'ROBUST' if x['robust'] else '      '} x{x['lift']} q {x['q']} h1 {x['h1']} h2 {x['h2']} ex-crisis x{x['xc_lift']} p {x['xc_p']}  {x['factor']}")
        for w in m["forward"]:
            print("   fwd", w["frm"], w["to"], w["factor"], w["exact"])


def write(res):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]

    def short(f):
        return f.split(": ", 1)[1]
    blocks = ""
    for key, m in res["markets"].items():
        r = m["rules"]
        wf = r["walk_forward"]
        rows = "".join(
            f"<tr class='{'bullish' if x['robust'] else ''}'><td><b>{html.escape(short(x['factor']))}</b></td><td class='n'>{x['big']} / {x['exp']}</td><td class='n'><b>×{x['lift']}</b></td>"
            f"<td class='n'>{x['q']}</td><td class='n'>{x['episodes']}</td><td class='n'>×{x['h1']} / ×{x['h2']}</td><td class='n'>×{x['xc_lift']} (p {x['xc_p']})</td>"
            f"<td class='n'>{x['big_rate']}% vs {m['base_rate']}%</td><td class='n'>{x['up_share']}%</td><td>{'yes' if x['robust'] else ''}</td></tr>" for x in m["fdr"])
        frows = "".join(f"<tr><td class='w'>{dt.date.fromisoformat(w['frm']):%a %d %b %Y}{'' if w['to'] == w['frm'] else ' – ' + format(dt.date.fromisoformat(w['to']), '%a %d %b %Y')}</td>"
                        f"<td>{html.escape(short(w['factor']))}</td><td class='s'>{', '.join(w['exact']) or 'state / rule window'}</td></tr>" for w in m["forward"]) or \
            "<tr><td colspan='3'>none of the robust factors occurs before 2028</td></tr>"
        blocks += f"""<h2>{m['name']}</h2>
<p class="m"><b>Direction rules:</b> {r['n_scored']} document rules with 10+ decided cases; all their calls together were right {r['pooled']['hit']}% of the time against {r['pooled']['base']}% by chance.
{r['p05']} rules reached p &lt; 0.05 where luck alone would give about {r['expected_p05']}; none passes the false-discovery-rate test. Walk-forward: {wf['n_rules']} rules picked on 2000–2013 gave {wf['hit']}% vs {wf['base']}% on 2013–2026 (p {wf['p']}).
<b>The documents' rules do not call the direction of this index.</b></p>
<p class="m"><b>Big days (±2%):</b> {m['n_big']} of {m['n_days']} sessions ({m['base_rate']}%). Leads picked on 2000–2013 gave ×{m['split']['pooled_lift']} on 2013–2026 (p {m['split']['pooled_p']:.4f}).
Factors that pass the false-discovery-rate test (q &lt; 0.10); green = robust (both halves, and still p &lt; 0.01 without the 2008–09 and 2020 crashes):</p>
<div class="wrap"><table><thead><tr><th>Factor (on the day / events ±3 days)</th><th>Big days / expected</th><th>Lift</th><th>q</th><th>Episodes</th><th>2000–13 / 2013–26</th><th>Without the two crashes</th><th>Chance of a ±2% day when present (raw; the lift is adjusted for the year)</th><th>Up share</th><th>Robust</th></tr></thead><tbody>{rows}</tbody></table></div>
<h3>Robust factors' dates, 22 Nov 2026 – 31 Dec 2027</h3>
<div class="wrap"><table><thead><tr><th>Dates</th><th>Factor</th><th>Exact event</th></tr></thead><tbody>{frows}</tbody></table></div>"""
    both = "".join(f"<tr><td>{html.escape(b['title'])}</td><td>{b['tone']}</td><td class='n'>{b['spx']}</td><td class='n'>{b['sensex']}</td></tr>" for b in res["both_best"])
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Market Findings</title><style>{css}</style></head><body>
<h1>Stock market (S&amp;P 500 and BSE Sensex), 2000–2026: what the planets show</h1>
<p class="m">Two tests, as for gold: (1) every computable general-market rule in TA, KD and the 2026 document, scored on direction (details: <code>market_backtest_2000-2026_ET.html</code>);
(2) every ±2% day compared with the sky ±3 days (<code>spx_big_moves_…</code>, <code>sensex_big_moves_…</code>). Big days are counted against the same years, so a crisis year does not inflate a slow planet.</p>
{blocks}
<h2>Rules marked “best” in both markets by the tracker rule (for reference)</h2>
<p class="s">The tracker's “best” test (15+ decided, above base, right in 70% of years or p &lt; 0.10) is lenient; with ~360 rules per market some pass by chance. None passes the false-discovery-rate test.</p>
<div class="wrap"><table><thead><tr><th>Rule</th><th>Says</th><th>S&amp;P 500</th><th>BSE Sensex</th></tr></thead><tbody>{both}</tbody></table></div>
<p class="s">Generated by tools/market_summary.py.</p></body></html>"""
    (OUT / "market_summary_2000-2026_ET.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
