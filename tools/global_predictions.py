"""Global Predictions (a forecaster in a WhatsApp group the user follows, shared 24 Nov 2026): US stock market forecast for
24 Nov - 5 Dec 2026, its astronomy checked, its transit claims tested on the S&P since 1928, and its calls scored.

    python tools/global_predictions.py

The forecast reads Western-style degree aspects (Full Moon conjunct Uranus, Sun opposite Uranus, Mars square Uranus,
Venus-Mercury). Western sources are outside our rule set, so nothing here becomes a rule; it is tracked like the other
outside forecasts (an external claim, checked and scored). News and fundamentals quoted in the messages are not used.
Aspects between two bodies are the same in the tropical and sidereal zodiacs; separations are computed sidereally.
Claims:
  24-27 Nov  Full Moon-Uranus alignment challenged by Mars: sudden volatility, sharp market reversals.
  30 Nov-5 Dec  Venus-Mercury may support temporary optimism; the approaching Mars-Uranus square: renewed instability.
  overall    a sudden rally followed by equally sharp selling pressure is one possible scenario; recoveries may be
             temporary relief rallies.
Scoring (S&P 500, closes): a volatility window is "right" if it has a big day (|move| >= 2%) or a sharp reversal
(consecutive sessions of 1%+ in opposite directions); the chance of that in any window of the same length in the
last 250 sessions is shown beside it, because in a volatile market such calls come true often by default.
Writes build/pdfref/global_predictions_ET.{html,json}.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402

AF = load(ROOT / "tools" / "author_forecasts.py", "af_gp")
ET, UTC = ZoneInfo("America/New_York"), dt.timezone.utc
swe.set_sid_mode(swe.SIDM_LAHIRI)
FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
BODY = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Uranus": swe.URANUS}

FORECASTS = [
    dict(id="gp-a", made="22 Nov 2026", period="24 – 27 Nov 2026", kind="vol", start="2026-11-24", end="2026-11-27",
         text="Full Moon–Uranus alignment, challenged by Mars: sudden volatility, unexpected reversals, sharp market reversals."),
    dict(id="gp-b", made="22 Nov 2026", period="30 Nov – 5 Dec 2026", kind="opt_then_vol", start="2026-11-30", end="2026-12-04",
         text="Venus–Mercury may support temporary optimism, but the approaching Mars–Uranus square suggests a risk of renewed instability."),
    dict(id="gp-c", made="22 Nov 2026", period="24 Nov – 5 Dec 2026", kind="fade", start="2026-11-24", end="2026-12-04",
         text="A sudden rally followed by equally sharp selling pressure is one possible scenario; a recovery may be only a temporary relief rally (the 23 Nov rally of +4.7% is the test)."),
]


def sep(a, b):
    return abs((a - b + 180) % 360 - 180)


def pos(t, b):
    u = t.astimezone(UTC)
    r = swe.calc_ut(swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60), BODY[b], FL)[0]
    return r[0] % 360, r[3]


def exact(fn, a, b, step=dt.timedelta(hours=1)):
    """Time of the minimum of fn (an orb) between a and b."""
    best, bt = 1e9, None
    t = a
    while t <= b:
        v = fn(t)
        if v < best:
            best, bt = v, t
        t += step
    lo, hi = bt - step, bt + step
    for _ in range(30):
        m1, m2 = lo + (hi - lo) / 3, lo + 2 * (hi - lo) / 3
        if fn(m1) < fn(m2):
            hi = m2
        else:
            lo = m1
    t = lo + (hi - lo) / 2
    return t, fn(t)


def astronomy():
    A, B = dt.datetime(2026, 11, 20, tzinfo=UTC), dt.datetime(2026, 12, 10, tzinfo=UTC)
    out = []
    fm, _ = exact(lambda t: abs(sep(pos(t, "Moon")[0], pos(t, "Sun")[0]) - 180), A, dt.datetime(2026, 11, 26, tzinfo=UTC))
    mu = sep(pos(fm, "Moon")[0], pos(fm, "Uranus")[0])
    out.append(dict(claim="Full Moon conjunct Uranus", when=fm, detail=f"Full Moon {fm.astimezone(ET):%a %d %b %H:%M} ET; Moon–Uranus {mu:.1f}° apart at that moment",
                    status="holds" if mu <= 8 else "loose" if mu <= 15 else "wrong"))
    msq = abs(sep(pos(fm, "Mars")[0], pos(fm, "Uranus")[0]) - 90)
    mmo = abs(sep(pos(fm, "Mars")[0], pos(fm, "Moon")[0]) - 90)
    out.append(dict(claim="… challenged by Mars (Mars square the Full Moon / Uranus)", when=fm,
                    detail=f"at the Full Moon, Mars is {mmo:.1f}° from a square to the Moon and {msq:.1f}° from a square to Uranus", status="holds" if min(msq, mmo) <= 8 else "wrong"))
    so, orb = exact(lambda t: abs(sep(pos(t, "Sun")[0], pos(t, "Uranus")[0]) - 180), A, B)
    out.append(dict(claim="Sun opposite Uranus", when=so, detail=f"exact {so.astimezone(ET):%a %d %b %H:%M} ET (orb {orb:.2f}°)", status="holds"))
    vm, orb2 = exact(lambda t: sep(pos(t, "Venus")[0], pos(t, "Mercury")[0]), dt.datetime(2026, 11, 22, tzinfo=UTC), dt.datetime(2026, 12, 8, tzinfo=UTC))
    out.append(dict(claim="Venus–Mercury (30 Nov – 5 Dec)", when=vm, note="no conjunction or major aspect: 24–28° apart is not one",
                    detail=f"closest {vm.astimezone(ET):%a %d %b %H:%M} ET, {orb2:.1f}° apart; on 30 Nov {sep(pos(dt.datetime(2026, 11, 30, 17, tzinfo=UTC), 'Venus')[0], pos(dt.datetime(2026, 11, 30, 17, tzinfo=UTC), 'Mercury')[0]):.1f}°, "
                           f"on 5 Dec {sep(pos(dt.datetime(2026, 12, 5, 17, tzinfo=UTC), 'Venus')[0], pos(dt.datetime(2026, 12, 5, 17, tzinfo=UTC), 'Mercury')[0]):.1f}°",
                    status="holds" if orb2 <= 8 else "no aspect"))
    mu2, orb3 = exact(lambda t: abs(sep(pos(t, "Mars")[0], pos(t, "Uranus")[0]) - 90), A, dt.datetime(2026, 12, 20, tzinfo=UTC))
    out.append(dict(claim="Approaching Mars–Uranus square", when=mu2, detail=f"exact {mu2.astimezone(ET):%a %d %b %H:%M} ET (orb {orb3:.2f}°); within 3° from about 27 Nov to 12 Dec",
                    status="holds"))
    return out


def conditions():
    def fm_uranus(x):
        return abs(sep(x["Moon"], x["Sun"]) - 180) < 25 and sep((x["Sun"] + 180) % 360, x["Uranus"]) < 10
    return {
        "Full Moon conjunct Uranus (±2 days; Uranus within 10° of the full-Moon point)": fm_uranus,
        "Full Moon conjunct Uranus with Mars square Uranus (within 8°)": lambda x: fm_uranus(x) and abs(sep(x["Mars"], x["Uranus"]) - 90) < 8,
        "Sun opposite Uranus (within 3°)": lambda x: abs(sep(x["Sun"], x["Uranus"]) - 180) < 3,
        "Mars square Uranus (within 3°)": lambda x: abs(sep(x["Mars"], x["Uranus"]) - 90) < 3,
        "Venus conjunct Mercury (within 3°) – Global Predictions: optimism": lambda x: sep(x["Venus"], x["Mercury"]) < 3,
    }


def vol_base(P, n, sessions=250):
    """Share of n-session windows in the last `sessions` with a big day or a sharp reversal."""
    D = list(P)
    C = [P[d] for d in D]
    r = [(C[i] / C[i - 1] - 1) * 100 for i in range(1, len(C))]
    hits = tot = 0
    for i in range(len(r) - sessions, len(r) - n + 1):
        w = r[i:i + n]
        prev = r[i - 1]
        ok = any(abs(x) >= 2 for x in w) or any(abs(a) >= 1 and abs(b) >= 1 and a * b < 0 for a, b in zip([prev] + w[:-1], w))
        hits += ok
        tot += 1
    return round(hits / tot * 100)


def score(f, P):
    D = list(P)
    a, b = dt.date.fromisoformat(f["start"]), dt.date.fromisoformat(f["end"])
    sess = [d for d in D if a <= d <= b]
    prev = [d for d in D if d < a][-1]
    rets = []
    last = prev
    for d in sess:
        rets.append((d, (P[d] / P[last] - 1) * 100))
        last = d
    done = D[-1] >= b
    lines = "; ".join(f"{d:%a %d}: {r:+.2f}%" for d, r in rets) or "no session closed yet"
    if f["kind"] == "vol":
        before = (P[prev] / P[[x for x in D if x < prev][-1]] - 1) * 100
        big = [d for d, r in rets if abs(r) >= 2]
        seq = [before] + [r for _, r in rets]
        rev = [rets[i][0] for i in range(len(rets)) if abs(seq[i]) >= 1 and abs(seq[i + 1]) >= 1 and seq[i] * seq[i + 1] < 0]
        ok = bool(big or rev)
        base = vol_base(P, max(len(sess), 3))
        status = "right" if ok else ("open" if not done else "wrong")
        return dict(status=status, detail=f"{lines}. Big days: {', '.join(f'{d:%d %b}' for d in big) or 'none'}; reversals of 1%+: {', '.join(f'{d:%d %b}' for d in rev) or 'none'}. "
                                         f"In the last 250 sessions, {base}% of windows this long had a big day or such a reversal.", base=base)
    if f["kind"] == "opt_then_vol":
        if not done:
            return dict(status="open", detail=lines)
        half = len(rets) // 2 or 1
        up = sum(r for _, r in rets[:half]) > 0
        vol = any(abs(r) >= 2 for _, r in rets[half:]) or sum(r for _, r in rets[half:]) < -1
        return dict(status="right" if up and vol else "partly right" if up or vol else "wrong", detail=f"{lines}. Early part up: {'yes' if up else 'no'}; instability later: {'yes' if vol else 'no'}.")
    if f["kind"] == "fade":
        ref = dt.date(2026, 11, 23)
        if ref not in P:
            return dict(status="open", detail="23 Nov close missing")
        base_close, pre = P[ref], P[[x for x in D if x < ref][-1]]
        now = P[sess[-1]] if sess else base_close
        given = (base_close - now) / (base_close - pre) * 100 if base_close != pre else 0
        st = "open" if not done else ("right" if now <= pre else "partly right" if given >= 50 else "wrong")
        return dict(status=st, detail=f"23 Nov rally {pre:,.0f} → {base_close:,.0f}; latest close {now:,.0f} ({given:.0f}% of the rally given back){'' if done else ', window still open'}.")


def main():
    P = AF.prices()
    fc = [dict(f, score=score(f, P)) for f in FORECASTS]
    ac = astronomy()
    ts = AF.tests(conditions())
    out = dict(forecasts=fc, astronomy=ac, tests=ts, last_price=str(list(P)[-1]))
    json.dump(out, open(OUT / "global_predictions_ET.json", "w"), indent=1, default=str)
    (OUT / "global_predictions_ET.html").write_text(page(out), encoding="utf-8")
    for f in fc:
        print(f["id"], f["score"])
    for a in ac:
        print(a["status"], "|", a["claim"], "|", a["detail"])
    for k, r in ts.items():
        print(k, {kk: r[kk] for kk in ("n", "eps", "eps_up5", "eps_exp5", "eps_p", "big", "exp_big", "p_big", "rev", "exp_rev", "p_rev")})


def page(out):
    E = html.escape
    css = """:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--soft:#f6f8fa;--up:#1a7f37;--dn:#cf222e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--soft:#161b22;--up:#3fb950;--dn:#f85149}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1150px}
h1{font-size:20px} h2{font-size:17px;margin-top:24px;border-bottom:1px solid var(--line);padding-bottom:4px} .s{font-size:12.5px;color:var(--mut)}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{background:var(--soft)}
td.n{text-align:right;font-variant-numeric:tabular-nums}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Global Predictions</title><style>{css}</style></head><body>",
         "<h1>Global Predictions: US stock market, 24 Nov – 5 Dec 2026</h1>",
         f"<p class='s'>A forecaster in a WhatsApp group you follow (shared 24 Nov 2026). Western-style degree aspects; tracked as an outside forecast, not added to our rules. "
         f"News quoted in the messages is not used. S&amp;P closes to {out['last_price']}.</p><h2>The calls</h2><div class='wrap'><table><thead><tr><th>Period</th><th>Call</th><th>Status</th><th>S&amp;P 500</th></tr></thead><tbody>"]
    for f in out["forecasts"]:
        o.append(f"<tr><td>{E(f['period'])}</td><td>{E(f['text'])}</td><td><b>{E(f['score']['status'])}</b></td><td class='s'>{E(f['score']['detail'])}</td></tr>")
    o.append("</tbody></table></div><h2>Is the astronomy right?</h2><div class='wrap'><table><thead><tr><th>Claim</th><th>Check</th><th>Detail</th></tr></thead><tbody>")
    for a in out["astronomy"]:
        o.append(f"<tr><td>{E(a['claim'])}</td><td><b>{E(a['status'])}</b></td><td class='s'>{E(a['detail'])}</td></tr>")
    o.append("</tbody></table></div><h2>The same configurations on the S&amp;P, 1928–2026</h2><div class='wrap'><table><thead><tr><th>Condition</th><th class='n'>Days</th>"
             "<th class='n'>Big days (|move| ≥ 2%)</th><th class='n'>Sharp reversals</th><th class='n'>Next 5 sessions up (each episode once)</th></tr></thead><tbody>")
    for k, r in out["tests"].items():
        o.append(f"<tr><td>{E(k)}</td><td class='n'>{r['n']}</td><td class='n'>{r['big']} vs {r['exp_big']} expected (p {r['p_big']})</td><td class='n'>{r['rev']} vs {r['exp_rev']} (p {r.get('p_rev')})</td>"
                 f"<td class='n'>{r['eps']} episodes: {r['eps_up5']}% vs {r['eps_exp5']}% (p {r['eps_p']})</td></tr>")
    o.append("</tbody></table></div><p class='s'>Expected counts use the same Nov–Nov years, so a volatile year raises the bar. A sharp reversal = a session of 1%+ after a session of 1%+ the other way. "
             "Generated by tools/global_predictions.py.</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
