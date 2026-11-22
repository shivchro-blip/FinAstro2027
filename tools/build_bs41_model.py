"""Build the gold calendar and backtest of Financial Astrology Model v1.0 (Brihat Samhita Ch.41).

    python tools/build_bs41_model.py

Writes
  build/pdfref/gold_bs41_model_2026-11-20_to_2027-12-31_ET.{html,json,csv,ics}
      daily scarcity (S) and demand/value (V) indices, bias and confidence, and a
      calendar entry each time the bias class changes, with the full reasoning;
  build/pdfref/gold_bs41_model_backtest_2000-2026_ET.json
      the same model scored against COMEX gold (GC=F) daily closes, Aug 2000 - Nov 2026.
Model: finastro/pdfref/bs41_model.py; methodology:
Reference_materials/extracted/FINANCIAL_ASTROLOGY_MODEL_v1.md.
"""
from __future__ import annotations

import csv
import datetime as dt
import html
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.pdfref import bs41_model as M  # noqa: E402

OUT = ROOT / "build" / "pdfref"
STEM = "gold_bs41_model_2026-11-20_to_2027-12-31_ET"
PRICES = OUT / "backtest" / "gold_GC_F_daily_2000.csv"
ORDER = ["Strong bearish", "Bearish", "Mild bearish", "Neutral / mixed", "Mild bullish", "Bullish", "Strong bullish"]
CHECKLIST = ("Price structure: higher highs and higher lows (bullish) / lower highs and lower lows (bearish)",
             "Volume: confirmation of the move", "VWAP: price holding above (bullish) / below (bearish) VWAP",
             "Technical invalidation: a break of the relevant support / resistance")


def days(a, b):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def reasoning(r):
    out = []
    for ps in r["per_sign"]:
        for l in ps["planets"]:
            out.append(f"{ps['sign']}: {l['planet']} ({l['role']}, {l['strength'].lower()}, Shadbala {l['ratio']:.2f}x) in house {l['house']} - {l['effect']}")
        out += [f"{ps['sign']}: {a}" for a in ps["aspects"]]
        out.append(f"{ps['sign']}: Sarvashtakavarga {ps['SAV']} bindus; Rahu house {ps['nodes']['Rahu']}, Ketu house {ps['nodes']['Ketu']} (not scored)")
    return out


def forward():
    rows = [M.evaluate(d) for d in days(dt.date(2026, 11, 20), dt.date(2027, 12, 31))]
    regimes = []
    for r in rows:
        if regimes and regimes[-1]["bias"] == r["bias"]:
            regimes[-1]["to"] = r["date"]
            regimes[-1]["S"].append(r["S"])
            regimes[-1]["V"].append(r["V"])
        else:
            regimes.append(dict(frm=r["date"], to=r["date"], bias=r["bias"], S=[r["S"]], V=[r["V"]], first=r))
    return rows, regimes


def load_prices():
    rows = list(csv.DictReader(open(PRICES)))
    return [dt.date.fromisoformat(r["date"]) for r in rows], [float(r["close"]) for r in rows]


def backtest():
    D, C = load_prices()
    recs = []
    for i in range(1, len(D) - 10):
        if D[i] > dt.date(2026, 11, 20):
            break
        r = M.evaluate(D[i])
        fw = {n: (C[i - 1 + n] / C[i - 1] - 1) * 100 for n in (1, 5, 10)}     # entry = previous close (state known at sunrise)
        recs.append((D[i], r["S"], r["V"], r["bias"], r["confidence"], fw))
    def corr(x, y):
        mx, my = statistics.fmean(x), statistics.fmean(y)
        sx = math.sqrt(sum((a - mx) ** 2 for a in x))
        sy = math.sqrt(sum((b - my) ** 2 for b in y))
        return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)
    res = {"n_days": len(recs), "from": recs[0][0].isoformat(), "to": recs[-1][0].isoformat()}
    for n in (1, 5, 10):
        res[f"corr_S_{n}d"] = round(corr([r[1] for r in recs], [r[5][n] for r in recs]), 4)
        res[f"corr_V_{n}d"] = round(corr([r[2] for r in recs], [r[5][n] for r in recs]), 4)
    base = {n: dict(mean=round(statistics.fmean(r[5][n] for r in recs), 3), up=round(sum(r[5][n] > 0 for r in recs) / len(recs) * 100, 1)) for n in (1, 5, 10)}
    res["base"] = base
    by = {}
    for b in ORDER:
        sel = [r for r in recs if r[3] == b]
        if sel:
            by[b] = dict(days=len(sel), share=round(len(sel) / len(recs) * 100, 1),
                         **{f"mean_{n}d": round(statistics.fmean(r[5][n] for r in sel), 3) for n in (1, 5, 10)},
                         **{f"up_{n}d": round(sum(r[5][n] > 0 for r in sel) / len(sel) * 100, 1) for n in (1, 5, 10)})
    res["by_bias"] = by
    conf = {}
    for cl in ("Very high", "High", "Moderate", "Low"):
        for side, f in (("bullish", lambda s: s >= 15), ("bearish", lambda s: s <= -15)):
            sel = [r for r in recs if r[4] == cl and f(r[1])]
            if len(sel) >= 20:
                conf[f"{cl} / {side}"] = dict(days=len(sel), mean_5d=round(statistics.fmean(r[5][5] for r in sel), 3),
                                              right_5d=round(sum((r[5][5] > 0) == (side == "bullish") for r in sel) / len(sel) * 100, 1))
    res["by_confidence"] = conf
    blocks = []
    for a, b in ((2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020), (2020, 2027)):
        sel = [r for r in recs if a <= r[0].year < b]
        bu = [r[5][5] for r in sel if r[1] >= 15]
        be = [r[5][5] for r in sel if r[1] <= -15]
        blocks.append(dict(years=f"{a}-{b - 1}", corr_S_5d=round(corr([r[1] for r in sel], [r[5][5] for r in sel]), 3),
                           bull_mean_5d=round(statistics.fmean(bu), 3) if bu else None, bear_mean_5d=round(statistics.fmean(be), 3) if be else None))
    res["blocks"] = blocks
    return res


def ics(regimes):
    def esc(s):
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FinAstro2027//BS41 model v1.0//EN", "CALSCALE:GREGORIAN"]
    for g in regimes:
        f = dt.date.fromisoformat(g["frm"])
        t = dt.date.fromisoformat(g["to"]) + dt.timedelta(days=1)
        r = g["first"]
        desc = (f"Gold - Brihat Samhita Ch.41 model v1.0\nScarcity index {r['S']:+.1f} (avg {statistics.fmean(g['S']):+.1f}), demand/value {r['V']:+.1f}\n"
                f"Bias {g['bias']}; confidence {r['confidence']}\n" + "\n".join(reasoning(r)) + "\nMarket confirmation required: " + "; ".join(CHECKLIST))
        lines += ["BEGIN:VEVENT", f"UID:bs41-{g['frm']}@finastro2027", f"DTSTAMP:{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}",
                  f"DTSTART;VALUE=DATE:{f:%Y%m%d}", f"DTEND;VALUE=DATE:{t:%Y%m%d}", f"SUMMARY:{esc('Gold BS41: ' + g['bias'])}",
                  f"DESCRIPTION:{esc(desc)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def cls(b):
    b = b.lower()
    return "bullish" if "bullish" in b else "bearish" if "bearish" in b else "mixed"


def write(rows, regimes, bt):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    reg_html = "".join(
        f"<tr class='{cls(g['bias'])}'><td class='w'>{g['frm']}</td><td class='w'>{g['to']}</td><td class='n'>{(dt.date.fromisoformat(g['to']) - dt.date.fromisoformat(g['frm'])).days + 1}</td>"
        f"<td><span class='tag {cls(g['bias'])}'>{g['bias']}</span></td><td class='n'>{g['first']['S']:+.1f}<div class='s'>avg {statistics.fmean(g['S']):+.1f}</div></td>"
        f"<td class='n'>{g['first']['V']:+.1f}<div class='s'>avg {statistics.fmean(g['V']):+.1f}</div></td><td>{g['first']['confidence']}</td>"
        f"<td class='s'><details><summary>Planetary reasoning</summary><ul>{''.join(f'<li>{html.escape(x)}</li>' for x in reasoning(g['first']))}</ul>"
        f"<p><b>Agreeing indicators:</b> {html.escape(', '.join(g['first']['agree']) or '-')}. <b>Contradicting:</b> {html.escape(', '.join(g['first']['against']) or '-')}.</p>"
        f"<p><b>Market confirmation required:</b> {html.escape('; '.join(CHECKLIST))}.</p></details></td></tr>" for g in regimes)
    daily = "".join(f"<tr class='{cls(r['bias'])}'><td class='w'>{r['date']}</td><td class='n'>{r['S']:+.1f}</td><td class='n'>{r['per_sign'][0]['S']:+.1f} / {r['per_sign'][1]['S']:+.1f}</td>"
                    f"<td class='n'>{r['V']:+.1f}</td><td>{r['bias']}</td><td>{r['confidence']}</td>"
                    f"<td class='s'>{'; '.join(f'{p} {v}' for p, v in r['positions'].items())}</td></tr>" for r in rows)
    bb = "".join(f"<tr class='{cls(k)}'><td>{k}</td><td class='n'>{v['days']} ({v['share']}%)</td>" + "".join(f"<td class='n'>{v[f'mean_{n}d']:+.3f}%</td><td class='n'>{v[f'up_{n}d']}%</td>" for n in (1, 5, 10)) + "</tr>"
                 for k, v in bt["by_bias"].items())
    base = "".join(f"<td class='n'>{bt['base'][n]['mean']:+.3f}%</td><td class='n'>{bt['base'][n]['up']}%</td>" for n in (1, 5, 10))
    cf = "".join(f"<tr><td>{k}</td><td class='n'>{v['days']}</td><td class='n'>{v['mean_5d']:+.3f}%</td><td class='n'>{v['right_5d']}%</td></tr>" for k, v in bt["by_confidence"].items())
    blk = "".join(f"<tr><td>{b['years']}</td><td class='n'>{b['corr_S_5d']:+.3f}</td><td class='n'>{'' if b['bull_mean_5d'] is None else f'{b['bull_mean_5d']:+.3f}%'}</td><td class='n'>{'' if b['bear_mean_5d'] is None else f'{b['bear_mean_5d']:+.3f}%'}</td></tr>" for b in bt["blocks"])
    now = rows[1] if len(rows) > 1 else rows[0]
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gold BS41 Model</title><style>{css}</style></head><body>
<h1>Gold — Financial Astrology Model v1.0 (Brihat Samhita Ch.41), 20 Nov 2026 – 31 Dec 2027</h1>
<p class="m">Classical Combined Commodity Framework: Brihat Samhita 41.2/41.7 (gold = Mesha and Makara) and 41.9–13 (planets counted from those signs), with BPHS Shadbala for "strong", Sarvashtakavarga and Parashari aspects.
Daily chart: New York at Hindu sunrise, sidereal Lahiri. Two separate indices: <b>scarcity / price pressure (S)</b> and <b>demand / market value (V)</b>, −100 to +100, gold = average of the Aries and Capricorn readings.
Weights (placement 45%, strength 25%, aspects 20%, Ashtakavarga 10%) and cut-offs are documented research conventions, not classical prescriptions. Silver: <b>Insufficient data</b> — Ch.41 assigns no sign to silver.
Method: Reference_materials/extracted/FINANCIAL_ASTROLOGY_MODEL_v1.md.</p>
<div class="kpi"><div>Today ({now['date']})<b>{now['bias']}</b></div><div>Scarcity S<b>{now['S']:+.1f}</b></div><div>Demand/value V<b>{now['V']:+.1f}</b></div><div>Confidence<b>{now['confidence']}</b></div></div>

<h2>Backtest first: did this model mean anything for gold? (COMEX GC=F, {bt['from']} – {bt['to']}, {bt['n_days']} trading days)</h2>
<p class="m">Each trading day uses the model's state at that day's New York sunrise (known in advance) and the move from the previous close. Correlation of S with the next 1 / 5 / 10 trading days: <b>{bt['corr_S_1d']:+.3f} / {bt['corr_S_5d']:+.3f} / {bt['corr_S_10d']:+.3f}</b>; of V: <b>{bt['corr_V_1d']:+.3f} / {bt['corr_V_5d']:+.3f} / {bt['corr_V_10d']:+.3f}</b> (0 = no relation).</p>
<div class="wrap"><table><thead><tr><th>Bias class</th><th>Days</th><th>Avg 1d</th><th>Up 1d</th><th>Avg 5d</th><th>Up 5d</th><th>Avg 10d</th><th>Up 10d</th></tr></thead><tbody>{bb}
<tr><td><b>All days</b></td><td class='n'>{bt['n_days']}</td>{base}</tr></tbody></table></div>
<div class="wrap"><table><thead><tr><th>Confidence / side</th><th>Days</th><th>Avg 5d</th><th>Moved the stated way</th></tr></thead><tbody>{cf}</tbody></table></div>
<div class="wrap"><table><thead><tr><th>Years</th><th>corr(S, 5d)</th><th>Avg 5d when S ≥ +15</th><th>Avg 5d when S ≤ −15</th></tr></thead><tbody>{blk}</tbody></table></div>

<h2>Calendar: each change of bias class (ET dates)</h2>
<div class="wrap"><table><thead><tr><th>From</th><th>To</th><th>Days</th><th>Bias</th><th>Scarcity S</th><th>Demand/value V</th><th>Confidence</th><th>Details</th></tr></thead><tbody>{reg_html}</tbody></table></div>
<h2>Every day</h2>
<div class="wrap"><table><thead><tr><th>Date</th><th>S (gold)</th><th>S Aries / Capricorn</th><th>V</th><th>Bias</th><th>Confidence</th><th>Positions at NY sunrise (sidereal)</th></tr></thead><tbody>{daily}</tbody></table></div>
<p class="s">Generated by tools/build_bs41_model.py. Shadbala validated against B.V. Raman's worked example (tests/test_shadbala.py). Not a standalone buy/sell signal; market confirmation is listed on every entry.</p>
</body></html>"""
    (OUT / f"{STEM}.html").write_text(page, encoding="utf-8")
    json.dump(dict(model="Financial Astrology Model v1.0", commodity="gold", silver="Insufficient data (Brihat Samhita Ch.41 assigns no sign to silver)",
                   daily=rows, regimes=[{k: v for k, v in g.items() if k != "first"} | {"confidence": g["first"]["confidence"]} for g in regimes], backtest=bt),
              open(OUT / f"{STEM}.json", "w"), indent=1, default=str)
    with open(OUT / f"{STEM}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "S_gold", "S_aries", "S_capricorn", "V_gold", "bias", "confidence", "agree", "against"])
        for r in rows:
            w.writerow([r["date"], r["S"], r["per_sign"][0]["S"], r["per_sign"][1]["S"], r["V"], r["bias"], r["confidence"], "; ".join(r["agree"]), "; ".join(r["against"])])
    (OUT / f"{STEM}.ics").write_text(ics(regimes), encoding="utf-8")
    json.dump(bt, open(OUT / "gold_bs41_model_backtest_2000-2026_ET.json", "w"), indent=1)


def main():
    rows, regimes = forward()
    bt = backtest()
    write(rows, regimes, bt)
    print(len(rows), "days;", len(regimes), "regimes")
    print(json.dumps({k: v for k, v in bt.items()}, indent=0)[:3000])


if __name__ == "__main__":
    main()
