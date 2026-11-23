"""Plain bullish / bearish tables for the S&P 500 and the BSE Sensex, 23 Nov 2026 - 31 Dec 2027.

    python tools/market_signal_table.py

Which rules go in (fixed before building the table): a direction rule is used only if,
over 2000-2026, it reached p < 0.05 on at least one index AND beat its base in both halves
(2000-2013, 2013-2026) on BOTH indices, with 15+ decided cases on each. That covers the PDF
rules (market_backtest_2000-2026_ET.json) and the calendar's own rules
(calendar_rules_backtest_2000-2026_ET.json). Strength per rule:
  High     p < 0.05 on both indices
  Moderate p < 0.05 on one and p < 0.15 on the other
  Low      p < 0.05 on one only
Points per weekday (High 3, Moderate 2, Low 1; bullish +, bearish -); the net decides the
signal and its size the strength (3+ High, 2 Moderate, 1 Low). Instants count for the 5
sessions they were scored on; windows while they last. Robust big-move factors
(market_summary_2000-2026_ET.json) are shown as Volatile on days with no direction call.
Check of the selection itself: picked the same way on 2000-2013, these rules gave 61.8% vs
59.2% (S&P) and 57.3% vs 56.4% (Sensex) on 2013-2026 - a small edge, not significant.
Writes build/pdfref/market_signals_2026-11-23_to_2027-12-31_ET.html (+ .json).
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
A, B = dt.date(2026, 11, 23), dt.date(2027, 12, 31)
NAMES = {"spx": "S&P 500", "sensex": "BSE Sensex"}
CAL_INSTR = {"SPX": "spx", "NIFTY": "sensex"}
PTS = {"High": 3, "Moderate": 2, "Low": 1}


def held(r):
    return bool(r and r["worked"] + r["failed"] >= 15 and r["h1"]["hit_rate"] is not None and r["h2"]["hit_rate"] is not None
                and r["h1"]["hit_rate"] > r["h1"]["base_rate"] and r["h2"]["hit_rate"] > r["h2"]["base_rate"])


def strength(pa, pb):
    lo, hi = sorted((pa, pb))
    if hi < 0.05:
        return "High"
    if lo < 0.05 and hi < 0.15:
        return "Moderate"
    if lo < 0.05:
        return "Low"
    return None


def rec(r):
    return f"{r['worked']}/{r['worked'] + r['failed']} ({r['hit_rate']}% vs {r['base_rate']}%, p {r['p_value']})"


def sessions_from(d, n=5):
    out, x = [], d
    while len(out) < n:
        if x.weekday() < 5:
            out.append(x)
        x += dt.timedelta(days=1)
    return out


def main():
    mb = json.load(open(OUT / "market_backtest_2000-2026_ET.json"))
    cb = json.load(open(OUT / "calendar_rules_backtest_2000-2026_ET.json"))
    ms = json.load(open(OUT / "market_summary_2000-2026_ET.json"))
    rules = {}
    for x in mb["rules"]:
        a, b = x["spx"], x["sensex"]
        if held(a) and held(b) and min(a["p_value"], b["p_value"]) < 0.05:
            rules[x["rule_id"]] = dict(title=x["title"], tone=x["tone"], st=strength(a["p_value"], b["p_value"]), src="PDF",
                                       record=f"S&P {rec(a)}; Sensex {rec(b)}")
    for x in cb["rules"]:
        a, b = x.get("spx"), x.get("sensex")
        if a and b and a["kind"] == "direction" and held(a) and held(b) and min(a["p_value"], b["p_value"]) < 0.05:
            rules[x["rule_id"]] = dict(title=x["provenance"].split(" p.")[0].split(" — ")[0] if x["provenance"] else x["rule_id"], tone=x["tone"],
                                       st=strength(a["p_value"], b["p_value"]), src="calendar", record=f"S&P {rec(a)}; Sensex {rec(b)}")
    # day-level calls per index
    calls = {k: collections.defaultdict(list) for k in NAMES}
    for f in mb["forward"]:
        r = rules.get(f["rule_id"])
        if not r:
            continue
        f0, t0 = dt.date.fromisoformat(f["frm"]), dt.date.fromisoformat(f["to"])
        days = sessions_from(f0) if (t0 - f0).days < 2 else [f0 + dt.timedelta(days=i) for i in range((t0 - f0).days + 1)]
        for k in NAMES:
            for d in days:
                calls[k][d].append(f["rule_id"])
    for f in cb.get("forward_2027", []):
        k = CAL_INSTR.get(f["instrument"])
        if not k or f["rule_id"] not in rules:
            continue
        for a0, _ in f["windows"]:
            d0 = dt.date.fromisoformat(a0)
            start = d0 + dt.timedelta(days=(7 - d0.weekday()) % 7) if d0.weekday() >= 5 else d0
            for d in sessions_from(start):
                calls[k][d].append(f["rule_id"])
    vol = {k: collections.defaultdict(list) for k in NAMES}
    for k, m in ms["markets"].items():
        for w in m["forward"]:
            f0, t0 = dt.date.fromisoformat(w["frm"]), dt.date.fromisoformat(w["to"])
            for i in range((t0 - f0).days + 1):
                vol[k][f0 + dt.timedelta(days=i)].append(w["factor"].split(": ", 1)[1].split(" [")[0].split(" (Strong")[0])
    res = dict(rules=rules, tables={})
    for k in NAMES:
        days = []
        d = A
        while d <= B:
            if d.weekday() < 5:
                ids = list(dict.fromkeys(calls[k].get(d, [])))
                net = sum(PTS[rules[i]["st"]] * (1 if rules[i]["tone"] == "Bullish" else -1) for i in ids)
                vv = list(dict.fromkeys(vol[k].get(d, [])))
                if net:
                    sig, st = ("Bullish" if net > 0 else "Bearish"), ("High" if abs(net) >= 3 else "Moderate" if abs(net) == 2 else "Low")
                elif ids or vv:
                    sig, st = "Volatile", "–"
                else:
                    sig = None
                if sig:
                    why = [rules[i]["title"] for i in ids] + [f"big-move factor: {v}" for v in vv]
                    days.append(dict(d=d, sig=sig, st=st, why=why, ids=ids))
            d += dt.timedelta(days=1)
        rows = []
        for x in days:
            if rows and rows[-1]["sig"] == x["sig"] and rows[-1]["st"] == x["st"] and rows[-1]["why"] == x["why"] and (x["d"] - rows[-1]["to"]).days <= 3:
                rows[-1]["to"] = x["d"]
            else:
                rows.append(dict(frm=x["d"], to=x["d"], sig=x["sig"], st=x["st"], why=x["why"], ids=x["ids"]))
        res["tables"][k] = rows
    json.dump(res, open(OUT / f"market_signals_{A}_to_{B}_ET.json", "w"), indent=1, default=str)
    (OUT / f"market_signals_{A}_to_{B}_ET.html").write_text(page(res), encoding="utf-8")
    for i, r in rules.items():
        print(f"{r['st']:8s} {r['tone']:7s} {r['src']:8s} {r['title']} | {r['record']}")
    for k, rows in res["tables"].items():
        print(NAMES[k], len(rows), collections.Counter((r["sig"], r["st"]) for r in rows))


def page(res):
    col = {"Bullish": ("#e7f6ec", "#1e7b3a"), "Bearish": ("#fdecec", "#b42318"), "Volatile": ("#fff6e0", "#9a6700")}
    dot = {"High": "●●●", "Moderate": "●●○", "Low": "●○○", "–": ""}

    def span(r):
        return f"{r['frm']:%a %d %b %Y}" if r["frm"] == r["to"] else f"{r['frm']:%a %d %b %Y} – {r['to']:%a %d %b %Y}"
    tables = ""
    for k, rows in res["tables"].items():
        body = ""
        for r in rows:
            c = col[r["sig"]]
            past = "; ".join(f"{res['rules'][i]['title']}: {res['rules'][i]['record']}" for i in r["ids"]) or "big-move factor (q < 0.10, both halves, holds without the 2008 and 2020 crashes); no direction"
            body += (f"<tr style='background:{c[0]}'><td>{span(r)}</td><td style='color:{c[1]};font-weight:600'>{r['sig']}</td>"
                     f"<td><span style='color:{c[1]}'>{dot[r['st']]}</span> {r['st']}</td><td>{html.escape('; '.join(r['why']))}</td><td class='s'>{html.escape(past)}</td></tr>")
        tables += (f"<div class='wrap'><table><caption>{NAMES[k]} – bullish / bearish days, {A:%d %b %Y} – {B:%d %b %Y} (US Eastern dates)</caption>"
                   f"<thead><tr><th>Dates</th><th>Signal</th><th>Strength</th><th>Why</th><th>Past record 2000–2026 (both indices)</th></tr></thead><tbody>{body}</tbody></table></div>")
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Market Signal Days</title>
<style>
:root{{color-scheme:light}} body{{margin:0;padding:16px;background:#fff;color:#1f2328;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{overflow-x:auto;margin-bottom:28px}} table{{border-collapse:collapse;width:100%;min-width:720px}}
caption{{text-align:left;font-weight:700;font-size:16px;padding:0 0 10px}}
th,td{{border-bottom:1px solid #d0d7de;padding:8px 10px;text-align:left;vertical-align:top}} th{{background:#f6f8fa}}
td:nth-child(-n+3){{white-space:nowrap}} .s{{font-size:12px;color:#57606a}}
</style></head><body>{tables}
<p class="s">Only rules that beat chance in both halves of 2000–2026 on both indices are used. Picked this way on 2000–2013, they were right 61.8% vs 59.2% (S&amp;P) and 57.3% vs 56.4% (Sensex) on 2013–2026: a small edge, not proven. Volatile = more ±2% days than usual, either direction.</p>
</body></html>"""


if __name__ == "__main__":
    main()
