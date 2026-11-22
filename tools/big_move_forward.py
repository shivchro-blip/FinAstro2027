"""Where the big-move leads (tools/big_move_analysis.py) fall from 22 Nov 2026 to 31 Dec 2027.

    python tools/big_move_forward.py [start] [end] [--metal silver]

A lead is a factor that was over-represented on gold's +/-2% days in 2000-2026
(lift > 1, p < 0.05 on a side, at least 5 separate episodes). For each lead the
script finds its dates in the forward period with the same definitions as the
history (events within +/-3 days, states at 12:00 ET, gold rule windows), marks
whether it held in both halves (2000-2013 and 2013-2026) and whether it involves an
outer planet (Uranus, Neptune, Pluto are not Vedic grahas), and sums the leads per
day into a watch level. None of the leads passed the FDR correction and the
leads picked on 2000-2013 were at chance on 2013-2026 (pooled lift about 1.0), so
this is a list of dates to watch, not a forecast.
Writes build/pdfref/gold_big_move_watch_{start}_to_{end}_ET.{html,json,ics}.
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import importlib.util
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "tools"))
import metal_cfg as MC  # noqa: E402
from finastro.sky import Sky  # noqa: E402
from finastro.pdfref.detect import Ctx  # noqa: E402
from finastro.pdfref.engine import Grid, utc  # noqa: E402

ET = ZoneInfo("America/New_York")
OUT = ROOT / "build" / "pdfref"
OUTER = ("Uranus", "Neptune", "Pluto")
LK = {"any": "lift", "up": "lift_up", "down": "lift_down"}
NK = {"any": "big", "up": "up", "down": "down"}
EK = {"any": "exp_big", "up": "exp_up", "down": "exp_down"}
PK = {"any": "p", "up": "p_up", "down": "p_down"}


def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[modname] = m
    spec.loader.exec_module(m)
    return m


def as_date(x):
    if x is None:
        return None
    if isinstance(x, dt.datetime):
        return (x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)).astimezone(ET).date()
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def forward_rules(a, b):
    """Gold rule windows in [a, b], named and expanded exactly as in big_move_analysis.rule_days."""
    B = load(ROOT / "tools" / "backtest_gold.py", "bt")
    B.configure_metal(MC.METAL)
    B.P0 = dt.datetime.combine(a - dt.timedelta(days=7), dt.time(0), ET)
    B.P1 = dt.datetime.combine(b + dt.timedelta(days=8), dt.time(0), ET)
    grid = Grid(utc(a.year - 1, 6, 1), utc(b.year + 1, 6, 30))
    ctxs = [Ctx(grid, Sky.load(ROOT / "build" / f"astronomy_{y}.json"), y) for y in sorted({a.year, b.year, b.year + 1})
            if (ROOT / "build" / f"astronomy_{y}.json").exists()]
    act = collections.defaultdict(set)
    for e in B.collect(ctxs):
        if e.get("tone") not in ("Bullish", "Bearish", "Mixed"):
            continue
        s = as_date(e["day"] or e["start"])
        en = as_date(e.get("end"))
        if en is None or (en - s).days < 1:
            s, en = s - dt.timedelta(days=3), s + dt.timedelta(days=3)
        d = max(s, a)
        while d <= min(en, b):
            act[d].add(f"Rule: {e['title']} [{e['tone']}]")
            d += dt.timedelta(days=1)
    return act


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 22)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2027, 12, 31)
    M = load(ROOT / "tools" / "big_move_analysis.py", "bma")
    hist = json.load(open(OUT / f"{MC.METAL}_big_moves_2000-2026_ET.json"))
    base = hist["n_big"] / hist["n_days"] * 100

    lead = {}
    for r, side in M.leads(hist["factors"]):
        L = lead.setdefault(r["factor"], dict(factor=r["factor"], sides=[], row=r))
        h1, h2 = r.get(LK[side] + "_h1"), r.get(LK[side] + "_h2")
        L["sides"].append(dict(side=side, obs=r[NK[side]], exp=r[EK[side]], lift=r[LK[side]], p=r[PK[side]], h1=h1, h2=h2, held=bool(h1 and h2 and h1 > 1 and h2 > 1)))
    for L in lead.values():
        r, sides = L["row"], {s["side"] for s in L["sides"]}
        L["lean"] = "up" if sides >= {"up"} and "down" not in sides else "down" if "down" in sides and "up" not in sides else "either"
        L["both_halves"] = all(s["held"] for s in L["sides"])
        L["outer"] = any(p in L["factor"] for p in OUTER)
        L["kind"] = L["factor"].split(":")[0]
        L["big_rate"] = round(r["big"] / r["days"] * 100, 1)
        L["up_share"] = r["up_share"]
        L["episodes"] = r["episodes"]
        del L["row"]

    ev = M.load_events(range(a.year - 1, b.year + 2))
    rules = forward_rules(a, b)
    days = []
    d = a
    while d <= b:
        f = M.day_factors(d, ev, rules)
        on = sorted(x for x in f if x in lead)
        days.append(dict(date=d.isoformat(), weekday=d.weekday() < 5, leads=on,
                         n=len(on), n_strong=sum(1 for x in on if lead[x]["both_halves"] and not lead[x]["outer"]),
                         up=sum(1 for x in on if lead[x]["lean"] == "up"), down=sum(1 for x in on if lead[x]["lean"] == "down")))
        d += dt.timedelta(days=1)

    # windows per lead (consecutive days), with the exact event dates for events
    exact = collections.defaultdict(list)
    for day, names in ev.items():
        if a - dt.timedelta(days=3) <= day <= b + dt.timedelta(days=3):
            for nm in names:
                if nm in lead:
                    exact[nm].append(day)
    wins = []
    for fac in lead:
        cur = None
        for x in days:
            if fac in x["leads"]:
                if cur and (dt.date.fromisoformat(x["date"]) - dt.date.fromisoformat(cur["to"])).days == 1:
                    cur["to"] = x["date"]
                else:
                    cur = dict(factor=fac, frm=x["date"], to=x["date"])
                    wins.append(cur)
        for w in (w for w in wins if w["factor"] == fac):
            f0, t0 = dt.date.fromisoformat(w["frm"]), dt.date.fromisoformat(w["to"])
            w["exact"] = [e.isoformat() for e in sorted(exact.get(fac, [])) if f0 - dt.timedelta(days=3) <= e <= t0 + dt.timedelta(days=3)]
    wins.sort(key=lambda w: (w["frm"], w["factor"]))

    # watch stretches: weekdays with 3+ leads, or 2+ leads that held in both halves (Vedic grahas only)
    def hot(x):
        return x["weekday"] and (x["n"] >= 3 or x["n_strong"] >= 2)
    stretches, cur = [], None
    for x in days:
        if hot(x):
            if cur and (dt.date.fromisoformat(x["date"]) - dt.date.fromisoformat(cur["to"])).days <= 3:
                cur["to"] = x["date"]
                cur["days"].append(x)
            else:
                cur = dict(frm=x["date"], to=x["date"], days=[x])
                stretches.append(cur)
    for s in stretches:
        facs = collections.Counter(f for x in s["days"] for f in x["leads"])
        s["leads"] = sorted(facs, key=lambda f: -facs[f])
        s["peak"] = max(x["n"] for x in s["days"])
        s["peak_day"] = max(s["days"], key=lambda x: (x["n"], x["n_strong"]))["date"]
        s["up"] = sum(1 for f in s["leads"] if lead[f]["lean"] == "up")
        s["down"] = sum(1 for f in s["leads"] if lead[f]["lean"] == "down")
        s["lean"] = "up" if s["up"] > s["down"] else "down" if s["down"] > s["up"] else "either"
        del s["days"]

    res = dict(start=a.isoformat(), end=b.isoformat(), base_big_rate=round(base, 1), min_q=min(min(r[k] for r in hist['factors']) for k in ('q', 'q_up', 'q_down')), split=hist["split"],
               leads=sorted(lead.values(), key=lambda L: (not L["both_halves"], L["outer"], -max(s["lift"] for s in L["sides"]))),
               windows=wins, stretches=stretches, days=days)
    stem = f"{MC.METAL}_big_move_watch_{a}_to_{b}_ET"
    json.dump(res, open(OUT / f"{stem}.json", "w"), indent=1, default=str)
    (OUT / f"{stem}.html").write_text(page(res, lead), encoding="utf-8")
    (OUT / f"{stem}.ics").write_text(ics(res, lead), encoding="utf-8")
    print(f"{len(lead)} leads, {len(wins)} windows, {len(stretches)} watch stretches")
    for s in stretches:
        print(f"  {s['frm']} - {s['to']}  peak {s['peak']} on {s['peak_day']}  lean {s['lean']}  {'; '.join(x.split(': ', 1)[1] for x in s['leads'][:5])}")


def fmt(d):
    return dt.date.fromisoformat(d).strftime("%a %d %b %Y")


def span(f, t):
    return fmt(f) if f == t else f"{fmt(f)} – {fmt(t)}"


def short(f):
    return f.split(": ", 1)[1]


def page(res, lead):
    css = (ROOT / "tools" / "backtest_gold.py").read_text().split('css = """', 1)[1].split('"""', 1)[0]
    sp = res["split"]

    def lrow(L):
        sides = "<br>".join(f"{s['side']}: {s['obs']} / {s['exp']} (×{s['lift']:.2f}, p {s['p']:.3f}); 2000–13 ×{s['h1']}, 2013–26 ×{s['h2']}" for s in L["sides"])
        tag = "bullish" if L["both_halves"] and not L["outer"] else "mixed" if L["both_halves"] else ""
        return (f"<tr class='{tag}'><td><b>{html.escape(short(L['factor']))}</b><div class='s'>{L['kind']}{' · outer planet, not a Vedic graha' if L['outer'] else ''}</div></td>"
                f"<td>{L['lean']}</td><td class='s'>{sides}</td><td class='n'>{L['big_rate']}%</td><td class='n'>{L['episodes']}</td><td>{'yes' if L['both_halves'] else 'no'}</td></tr>")
    lrows = "".join(lrow(L) for L in res["leads"])

    def cls(lean):
        return {"up": "bullish", "down": "bearish"}.get(lean, "mixed")
    srows = "".join(
        f"<tr class='{cls(s['lean'])}'><td class='w'><b>{span(s['frm'], s['to'])}</b></td><td class='n'>{s['peak']}</td><td class='w'>{fmt(s['peak_day'])}</td>"
        f"<td>{s['lean']} ({s['up']} up / {s['down']} down leads)</td><td class='s'>{html.escape('; '.join(short(f) for f in s['leads']))}</td></tr>" for s in res["stretches"])
    wrows = "".join(
        f"<tr class='{cls(lead[w['factor']]['lean'])}'><td class='w'>{span(w['frm'], w['to'])}</td><td>{html.escape(short(w['factor']))}</td><td>{lead[w['factor']]['lean']}</td>"
        f"<td>{'yes' if lead[w['factor']]['both_halves'] else 'no'}{' (outer)' if lead[w['factor']]['outer'] else ''}</td>"
        f"<td class='s'>{', '.join(fmt(e) for e in w['exact']) or '-'}</td></tr>" for w in res["windows"])
    months = collections.defaultdict(lambda: [0, 0, 0])
    for x in res["days"]:
        if x["weekday"]:
            m = months[x["date"][:7]]
            m[0] += 1
            m[1] += x["n"] >= 3 or x["n_strong"] >= 2
            m[2] = max(m[2], x["n"])
    mrows = "".join(f"<tr><td>{dt.date.fromisoformat(k + '-01'):%b %Y}</td><td class='n'>{v[1]} of {v[0]}</td><td class='n'>{v[2]}</td></tr>" for k, v in sorted(months.items()))
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{MC.NAME} Big-Move Watch</title><style>{css}</style></head><body>
<h1>{MC.NAME} big-move watch, {fmt(res['start'])} – {fmt(res['end'])} (US Eastern)</h1>
<p class="m">Dates when the factors that were over-represented on {MC.METAL}'s ±{MC.TH:g}% days in 2000–2026 (<code>{MC.METAL}_big_moves_2000-2026_ET.html</code>) come round again.
On a normal day the chance of a ±{MC.TH:g}% close was <b>{res['base_big_rate']}%</b>; the last column of the first table gives the historical rate when each lead was present (not adjusted for year, so it flatters factors active in volatile years).</p>
<p class="m"><b>How much to trust it.</b> No lead passed the false-discovery-rate correction (lowest q {res['min_q']:.2f}). When leads were picked on 2000–2013 only, {sp['n_held']} of {sp['n_leads']} stayed above 1 on 2013–2026, but taken together they gave {sp['pooled_obs']} big days against {sp['pooled_exp']} expected (×{sp['pooled_lift']}): no edge out of sample.
Read the dates below as times to expect volatility to be possible, not as calls. Green rows held in both halves and use Vedic grahas only; amber rows held in both halves but involve Uranus, Neptune or Pluto, which are outside the Vedic scope and cannot become rules.</p>
<h2>Watch stretches</h2>
<p class="s">Weekdays with 3 or more leads at once, or 2 or more leads that held in both halves (Vedic grahas only); stretches bridge weekends (days up to 3 apart). Lean counts the leads whose big days leaned up or down historically.</p>
<div class="wrap"><table><thead><tr><th>Dates</th><th>Most leads on one day</th><th>Peak day</th><th>Lean</th><th>Leads in the stretch (most days first)</th></tr></thead><tbody>{srows}</tbody></table></div>
<h2>Leads used</h2>
<div class="wrap"><table><thead><tr><th>Lead</th><th>Lean</th><th>2000–2026 big days: observed / expected (lift, p); each half</th><th>Historical chance of a ±{MC.TH:g}% day when present</th><th>Episodes</th><th>Held in both halves</th></tr></thead><tbody>{lrows}</tbody></table></div>
<h2>Every lead window</h2>
<p class="s">Events count from 3 days before to 3 days after the exact moment (exact dates in the last column); states and rules count while they hold. Where a sign boundary is also a nakshatra boundary (Cancer/Leo, Scorpio/Sagittarius, Pisces/Aries), one ingress counts as both a sign change and a nakshatra change.</p>
<div class="wrap"><table><thead><tr><th>Dates</th><th>Lead</th><th>Lean</th><th>Held in both halves</th><th>Exact event date(s)</th></tr></thead><tbody>{wrows}</tbody></table></div>
<h2>By month</h2>
<div class="wrap"><table><thead><tr><th>Month</th><th>Watch weekdays</th><th>Most leads on one day</th></tr></thead><tbody>{mrows}</tbody></table></div>
<p class="s">Generated by tools/big_move_forward.py from build/pdfref/{MC.METAL}_big_moves_2000-2026_ET.json; same factor definitions as tools/big_move_analysis.py.</p></body></html>"""


def ics(res, lead):
    def esc(t):
        return t.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//finastro2027//{MC.METAL} big-move watch//EN", "CALSCALE:GREGORIAN", f"X-WR-CALNAME:{MC.NAME} big-move watch"]
    sp = res["split"]
    for s in res["stretches"]:
        f, t = dt.date.fromisoformat(s["frm"]), dt.date.fromisoformat(s["to"]) + dt.timedelta(days=1)
        desc = (f"{MC.NAME} big-move watch ({s['lean']} lean; peak {s['peak']} leads on {fmt(s['peak_day'])}).\nLeads: " + "; ".join(short(x) for x in s["leads"]) +
                f"\nNormal chance of a +/-{MC.TH:g}% day {res['base_big_rate']}%. No lead passed FDR; out of sample x{sp['pooled_lift']}. A watch date, not a call.")
        lines += ["BEGIN:VEVENT", f"UID:bigmove-{MC.METAL}-{s['frm']}@finastro2027", f"DTSTAMP:{now}", f"DTSTART;VALUE=DATE:{f:%Y%m%d}", f"DTEND;VALUE=DATE:{t:%Y%m%d}",
                  f"SUMMARY:{esc(MC.NAME + ' volatility watch (' + s['lean'] + ')')}", f"DESCRIPTION:{esc(desc)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


if __name__ == "__main__":
    main()
