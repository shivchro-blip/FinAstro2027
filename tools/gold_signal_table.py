"""A plain table of gold's bullish / bearish days to end-2027 with a strength label.

    python tools/gold_signal_table.py [start] [end] [--metal silver]

Silver points: +2 retrograde Mercury or Jupiter (its strongest rule, p 0.05), +1 Moon and
Mercury alone in a sign, +1 Venus combust in East (silver p 0.18), watch windows and
trigger days as for gold (±3.5% days); no Nov 2026 phase (that was a gold Sun-note reading).

Built from the tested outlook (gold_outlook_*.json), the narrowed days
(gold_fast_triggers_*.json) and the 22 Nov - 2 Dec 2026 phase of the deep analysis.
Points per weekday:
  bullish  +1 U2 Mercury with the Sun (small edge)   +2 Venus combust in East (lead, p ~0.1)
           +1 volatility window leaning up            +1 narrowed trigger day in an up window
  bearish  +1 volatility window leaning down          +1 narrowed trigger day in a down window
  (the untested 22 Nov - 1 Dec 2026 "bearish phase" was removed on 27 Nov 2026; see the note in main())
Net > 0 bullish, < 0 bearish, 0 with a volatility window = volatile. Strength from the
size of the net score: 3+ High, 2 Moderate, 1 Low. Consecutive weekdays with the same reasons,
signal and strength are merged. Nothing here passed a strict significance test.
The last column is each label's walk-forward record from tools/test_signal_table.py.
Writes build/pdfref/gold_signals_{start}_to_{end}_ET.html.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
import metal_cfg as MC  # noqa: E402
TEST_JSON = OUT / ("signal_table_test_2000-2026_ET.json" if MC.METAL == "gold" else f"{MC.METAL}_signal_table_test_2000-2026_ET.json")


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 22)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2027, 12, 31)
    outl = json.load(open(OUT / f"{MC.METAL}_outlook_{a}_to_{b}_ET.json"))
    fast = json.load(open(OUT / f"{MC.METAL}_fast_triggers_{a}_to_{b}_ET.json"))
    narrowed = {}
    for p in fast["picks"]:
        for x in p["best"]:
            narrowed[x["date"]] = p["window_lean"]
    items = [dict(it, frm=dt.date.fromisoformat(it["frm"]), to=dt.date.fromisoformat(it["to"])) for it in outl["items"] if it["metal"] in (MC.METAL, "gold & silver")]
    # The hand-added "22 Nov - 1 Dec 2026 bearish phase" (Sun in Anuradha, a Saturn nakshatra, with Mars aspecting the
    # Sun; user note U3) was removed on 27 Nov 2026: U3 is at chance (60/134 = 45% vs 43% since 2000) and the phase was
    # the only input behind the gold "Bearish Low" label of 23 Nov - 1 Dec, which gold contradicted (+4.4% to 27 Nov).
    days = []
    d = a
    while d <= b:
        if d.weekday() < 5:
            bull = bear = 0
            why, vol = [], False
            for it in items:
                if not (it["frm"] <= d <= it["to"]):
                    continue
                t = it["title"]
                if it["kind"] == "Best rule":
                    if t in why or (t.startswith("U2") and "Mercury with the Sun" in why):
                        continue                          # overlapping windows of one rule count once
                    bull += 2 if t.startswith("Retrograde Mercury or Jupiter") else 1
                    why.append("Mercury with the Sun" if t.startswith("U2") else t)
                elif it["kind"].startswith("Venus"):
                    if "combust in East" in t:
                        bull += 2 if MC.METAL == "gold" else 1
                        why.append("Venus combust in East")
                    else:
                        vol = True
                        why.append("Venus rises in West (dip then upturn)")
                elif it["kind"] == "Phase":
                    bear += 1
                    why.append("Sun in Anuradha, Mars aspects the Sun")
                elif it["kind"] == "Volatility watch":
                    short = t.split(": ", 1)[1].replace(" [Bullish]", "").replace(" [Bearish]", "")
                    if it["lean"] == "up":
                        bull += 1
                    elif it["lean"] == "down":
                        bear += 1
                    else:
                        vol = True
                    why.extend(short.split("; "))
            nl = narrowed.get(d.isoformat())
            if nl:
                if nl == "up":
                    bull += 1
                elif nl == "down":
                    bear += 1
                else:
                    vol = True
                why.append("fast-planet trigger day")
            net = bull - bear
            sig = "Bullish" if net > 0 else "Bearish" if net < 0 else ("Volatile" if (vol or bull or bear) else None)
            if sig:
                st = "High" if abs(net) >= 3 else "Moderate" if abs(net) == 2 else "Low"
                days.append(dict(d=d, sig=sig, st=st, why=list(dict.fromkeys(why))))
        d += dt.timedelta(days=1)
    rows = []
    for x in days:
        if rows and rows[-1]["sig"] == x["sig"] and rows[-1]["st"] == x["st"] and rows[-1]["why"] == x["why"] and (x["d"] - rows[-1]["to"]).days <= 3:
            rows[-1]["to"] = x["d"]
            rows[-1]["why"] = list(dict.fromkeys(rows[-1]["why"] + x["why"]))
        else:
            rows.append(dict(frm=x["d"], to=x["d"], sig=x["sig"], st=x["st"], why=x["why"]))
    (OUT / f"{MC.METAL}_signals_{a}_to_{b}_ET.html").write_text(page(rows, a, b), encoding="utf-8")
    json.dump([dict(frm=str(r["frm"]), to=str(r["to"]), sig=r["sig"], st=r["st"], why=r["why"]) for r in rows],
              open(OUT / f"{MC.METAL}_signals_{a}_to_{b}_ET.json", "w"), indent=1)
    for r in rows:
        print(f"{r['frm']} {r['to']} {r['sig']:8s} {r['st']:8s} {'; '.join(r['why'])}")


def record():
    """Walk-forward record (2013-2026) of each signal / strength from tools/test_signal_table.py."""
    f = TEST_JSON
    if not f.exists():
        return {}
    out = {}
    for r in json.load(open(f))["walk_forward"]:
        k = (r["signal"], r["strength"])
        if r["signal"] == "Volatile":
            out[k] = f"±{MC.TH:g}% day in {r['big']} of {r['episodes']} (≈{r['big_exp']} by chance)"
        elif r["decided"] >= 10:
            edge = r["hit"] - r["base"]
            out[k] = f"{r['hit']}% right vs {r['base']}% by chance ({'+' if edge >= 0 else ''}{edge} pts, {r['decided']} cases)"
        else:
            out[k] = f"too few ({r['worked']}/{r['decided']})"
    return out


def page(rows, a, b):
    rec = record()
    col = {"Bullish": ("#e7f6ec", "#1e7b3a"), "Bearish": ("#fdecec", "#b42318"), "Volatile": ("#fff6e0", "#9a6700")}
    dot = {"High": "●●●", "Moderate": "●●○", "Low": "●○○"}

    def span(r):
        return f"{r['frm']:%a %d %b %Y}" if r["frm"] == r["to"] else f"{r['frm']:%a %d %b %Y} – {r['to']:%a %d %b %Y}"
    body = "".join(
        f"<tr style='background:{col[r['sig']][0]}'><td>{span(r)}</td><td style='color:{col[r['sig']][1]};font-weight:600'>{r['sig']}</td>"
        f"<td><span style='color:{col[r['sig']][1]}'>{dot[r['st']]}</span> {r['st']}</td><td>{html.escape('; '.join(r['why']))}</td>"
        f"<td>{html.escape(rec.get((r['sig'], r['st']), '-'))}</td></tr>" for r in rows)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{MC.NAME} Signal Days</title>
<style>
:root{{color-scheme:light}} body{{margin:0;padding:16px;background:#fff;color:#1f2328;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:640px}}
caption{{text-align:left;font-weight:700;font-size:16px;padding:0 0 10px}}
th,td{{border-bottom:1px solid #d0d7de;padding:8px 10px;text-align:left;vertical-align:top}} th{{background:#f6f8fa;position:sticky;top:0}}
td:nth-child(-n+3){{white-space:nowrap}}
</style></head><body><div class="wrap"><table>
<caption>{MC.NAME} – bullish / bearish days, {a:%d %b %Y} – {b:%d %b %Y} (US Eastern)</caption>
<thead><tr><th>Dates</th><th>Signal</th><th>Strength</th><th>Why</th><th>Past record of this label (2013–2026, unseen data)</th></tr></thead><tbody>{body}</tbody></table></div></body></html>"""


if __name__ == "__main__":
    main()
