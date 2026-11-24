"""Dasha combinations read the way a Vedic astrologer reads them, for the USA and NYSE charts, and tested on the S&P since 1928.

    python tools/dasha_combinations.py [START] [END]        # forward list, default 2026-11-24 to 2026-12-31

Each running lord (Antardasha, Pratyantar, Sookshma, Prana) is judged against its parent lord and the natal chart
(BPHS dasha principles; whole-sign houses from the sidereal Lahiri ascendant):
  natal (fixed for the pair)
    relation   house of the lord counted from its parent lord in the natal chart: 6/8 and 2/12 hurt; kendra (4/7/10),
               trine (5/9) and 3/11 help; together (same sign) neutral
    friendship the lord's natural relationship to its parent (BPHS ch.3): friend helps, enemy hurts; nodes neutral
    lordship   houses the lord rules: 1/5/9 and 2/11 help, 6/8/12 hurt (Rahu and Ketu take their dispositor's)
    placement  the lord's natal house: 1/4/5/7/9/10 help, 6/8/12 hurt
    dignity    exalted or own sign helps, debilitated hurts
  transit (at the start of the period; for Prana, on the day)
    house      the lord's transit house from the natal ascendant: 1/4/5/7/9/10 help, 6/8/12 hurt
    malefic    Saturn, Mars, Rahu or Ketu on the lord's natal sign, or Saturn / Mars aspecting it, hurts
    Jupiter    Jupiter on or aspecting (5/7/9) the lord's natal sign helps
    condition  transit exalted / own sign helps; debilitated or combust hurts
Each factor counts +1 / -1; the sum is the combination's score: "hurts" at -2 or below, "helps" at +2 or above.
The factors and thresholds are fixed in advance. The test: S&P mean daily return inside each period (Antardasha,
Pratyantar and Sookshma as whole periods; Prana day by day), 1928 - 20 Nov 2026, by factor and by score, against
all periods; Welch t, both halves (1928-1976, 1977-2026), BH FDR over every test.
Writes build/pdfref/dasha_combinations_ET.{html,json}.
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import html
import json
import math
import pathlib
import statistics
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import load  # noqa: E402

DT = load(ROOT / "tools" / "dasha_transits.py", "dtr_dc")
ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
SIGNS = DT.SIGNS
LORD_OF = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
FRIENDS = {"Sun": (("Moon", "Mars", "Jupiter"), ("Venus", "Saturn")), "Moon": (("Sun", "Mercury"), ()),
           "Mars": (("Sun", "Moon", "Jupiter"), ("Mercury",)), "Mercury": (("Sun", "Venus"), ("Moon",)),
           "Jupiter": (("Sun", "Moon", "Mars"), ("Mercury", "Venus")), "Venus": (("Mercury", "Saturn"), ("Sun", "Moon")),
           "Saturn": (("Mercury", "Venus"), ("Sun", "Moon", "Mars"))}
LEVEL_NAME = {1: "Antardasha", 2: "Pratyantar", 3: "Sookshma", 4: "Prana"}
START, STOP = dt.datetime(1928, 1, 3, tzinfo=UTC), dt.datetime(2026, 11, 21, tzinfo=UTC)
SPLIT = dt.date(1977, 1, 1)
FACTORS = ("relation", "friendship", "lordship", "placement", "dignity", "t_house", "t_malefic", "t_jupiter", "t_condition")
FNAME = {"relation": "relation to the parent lord", "friendship": "natural friendship with the parent", "lordship": "houses ruled",
         "placement": "natal house", "dignity": "natal dignity", "t_house": "transit house", "t_malefic": "malefic on its natal sign",
         "t_jupiter": "Jupiter on its natal sign", "t_condition": "transit dignity / combustion"}


# ------------------------------------------------------------------ chart data
def natal(name):
    ch = DT.CHARTS[name]
    asc = int(DT.asc(ch["ut"], ch["lat"], ch["lon"]) // 30)
    lon = {p: DT.pos(ch["ut"], p)[0] for p in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")}
    sign = {p: int(v // 30) for p, v in lon.items()}
    owns = collections.defaultdict(list)
    for s in range(12):
        owns[LORD_OF[s]].append((s - asc) % 12 + 1)
    return dict(name=name, asc=asc, sign=sign, lon=lon, owns=dict(owns))


def house(nat, s):
    return (s - nat["asc"]) % 12 + 1


def static_factors(nat, lord, parent):
    """Natal factors of `lord` running under `parent`: dict factor -> (value text, +1/0/-1)."""
    f = {}
    if parent:
        h = (nat["sign"][lord] - nat["sign"][parent]) % 12 + 1
        if h in (6, 8):
            f["relation"] = (f"{lord} is {h}th from {parent} (6/8)", -1)
        elif h in (2, 12):
            f["relation"] = (f"{lord} is {h}{'nd' if h == 2 else 'th'} from {parent} (2/12)", -1)
        elif h == 1:
            f["relation"] = (f"{lord} is with {parent}", 0)
        else:
            f["relation"] = (f"{lord} is {h}{'rd' if h == 3 else 'th'} from {parent} ({'kendra' if h in (4, 7, 10) else 'trine' if h in (5, 9) else '3/11'})", 1)
        fr, en = FRIENDS.get(lord, ((), ()))
        rel = "friend" if parent in fr else "enemy" if parent in en else "neutral"
        f["friendship"] = (f"{lord} regards {parent} as {rel}" if lord in FRIENDS else f"{lord}: node, neutral", 1 if rel == "friend" else -1 if rel == "enemy" else 0)
    ruler = LORD_OF[nat["sign"][lord]] if lord in ("Rahu", "Ketu") else lord
    owned = nat["owns"].get(ruler, [])
    v = sum(1 for h in owned if h in (1, 5, 9, 2, 11)) - sum(1 for h in owned if h in (6, 8, 12))
    f["lordship"] = (("via dispositor " + ruler + ": " if ruler != lord else "") + "rules " + ", ".join(str(h) for h in sorted(owned)), (v > 0) - (v < 0))
    h = house(nat, nat["sign"][lord])
    f["placement"] = (f"natal house {h}", 1 if h in (1, 4, 5, 7, 9, 10) else -1 if h in (6, 8, 12) else 0)
    sg = SIGNS[nat["sign"][lord]]
    dg = 1 if DT.EXALT.get(lord) == sg or sg in DT.OWN.get(lord, ()) else -1 if DT.DEBIL.get(lord) == sg else 0
    f["dignity"] = (f"natal {sg}" + (" (exalted / own)" if dg > 0 else " (debilitated)" if dg < 0 else ""), dg)
    return f


def sky(t):
    jd = swe.julday(t.year, t.month, t.day, t.hour + t.minute / 60)
    p = {}
    for b, k in DT.BODY.items():
        r = swe.calc_ut(jd, k, FL)[0]
        p[b] = (r[0] % 360, r[3])
    p["Ketu"] = ((p["Rahu"][0] + 180) % 360, p["Rahu"][1])
    return p


def transit_factors(nat, lord, p):
    f = {}
    si = int(p[lord][0] // 30)
    h = house(nat, si)
    f["t_house"] = (f"transit {SIGNS[si]}, house {h}", 1 if h in (1, 4, 5, 7, 9, 10) else -1 if h in (6, 8, 12) else 0)
    ns = nat["sign"][lord]
    hits = []
    for b in ("Saturn", "Mars", "Rahu", "Ketu"):
        if b == lord:
            continue
        bs = int(p[b][0] // 30)
        hh = (ns - bs) % 12 + 1
        if hh == 1 or (b == "Saturn" and hh in (3, 7, 10)) or (b == "Mars" and hh in (4, 7, 8)):
            hits.append(f"{b} {'on' if hh == 1 else 'aspects'} natal {lord} ({SIGNS[ns]})")
    f["t_malefic"] = ("; ".join(hits) or "none", -1 if hits else 0)
    js = int(p["Jupiter"][0] // 30)
    hj = (ns - js) % 12 + 1
    jh = lord != "Jupiter" and hj in (1, 5, 7, 9)
    f["t_jupiter"] = (f"Jupiter {'on' if hj == 1 else 'aspects'} natal {lord}" if jh else "none", 1 if jh else 0)
    sg = SIGNS[si]
    c = 0
    notes = []
    if DT.EXALT.get(lord) == sg or sg in DT.OWN.get(lord, ()):
        c += 1
        notes.append("exalted / own sign")
    if DT.DEBIL.get(lord) == sg:
        c -= 1
        notes.append("debilitated")
    if lord in DT.COMBUST and min((p[lord][0] - p["Sun"][0]) % 360, (p["Sun"][0] - p[lord][0]) % 360) <= DT.COMBUST[lord]:
        c -= 1
        notes.append("combust")
    f["t_condition"] = (", ".join(notes) or "plain", max(-1, min(1, c)))
    return f


def judge(nat, lord, parent, when):
    f = static_factors(nat, lord, parent)
    f.update(transit_factors(nat, lord, sky(when)))
    st = sum(v for k, (_, v) in f.items() if not k.startswith("t_"))
    tr = sum(v for k, (_, v) in f.items() if k.startswith("t_"))
    tot = st + tr
    return dict(factors=f, static=st, transit=tr, total=tot, verdict="hurts" if tot <= -2 else "helps" if tot >= 2 else "mixed")


def chain(name, when, nat=None):
    """The running Antar -> Pratyantar -> Sookshma -> Prana chain at `when`, each judged against its parent."""
    nat = nat or natal(name)
    run = DT.dasha_at(DT.CHARTS[name], when, 5)
    out = []
    for i in range(1, 5):
        lord, s, e = run[i]
        j = judge(nat, lord, run[i - 1][0], max(s, START) if i < 4 else when)
        out.append(dict(level=LEVEL_NAME[i], lord=lord, parent=run[i - 1][0], frm=s, to=e, **j))
    return out


def chain_score(ch):
    """Daily reading of the chain: the Pratyantar, Sookshma and Prana scores added."""
    return sum(x["total"] for x in ch if x["level"] in ("Pratyantar", "Sookshma", "Prana"))


# ------------------------------------------------------------------ test
def spx():
    rows = [(dt.date.fromisoformat(r["date"]), float(r["close"])) for r in csv.DictReader(open(OUT / "backtest" / "spx_GSPC_daily_1928.csv")) if r["date"] <= "2026-11-20"]
    return [r[0] for r in rows[1:]], [(rows[i][1] / rows[i - 1][1] - 1) * 100 for i in range(1, len(rows))]


def welch(a, b):
    if len(a) < 5 or len(b) < 5:
        return None
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    se = math.sqrt(va / len(a) + vb / len(b))
    return (ma - mb) / se if se else None


def p_from_t(t):
    return math.erfc(abs(t) / math.sqrt(2)) if t is not None else None


def test(name, D, R):
    nat = natal(name)
    units = {}                     # level -> list of (date, value, factors dict, total)
    for lv in (1, 2, 3):
        seq = DT.sequence(DT.CHARTS[name], lv, START, STOP)
        rows = []
        for path, s, e in seq:
            lords = path.split("/")
            lord, parent = lords[-1], lords[-2]
            i0 = bisect.bisect_left(D, s.astimezone(ET).date())
            i1 = bisect.bisect_left(D, e.astimezone(ET).date())
            if i1 <= i0:
                continue
            j = judge(nat, lord, parent, max(s, START))
            rows.append(dict(d=D[i0], r=statistics.fmean(R[i0:i1]), n=i1 - i0, cum=(math.prod(1 + x / 100 for x in R[i0:i1]) - 1) * 100,
                             f={k: v for k, (_, v) in j["factors"].items()}, total=j["total"], static=j["static"], transit=j["transit"]))
        units[lv] = rows
    rows = []
    for i, d in enumerate(D):                                   # Prana and the daily chain, at 12:30 ET each session
        when = dt.datetime(d.year, d.month, d.day, 12, 30, tzinfo=ET).astimezone(UTC)
        ch = chain(name, when, nat)
        pr = ch[3]
        rows.append(dict(d=d, r=R[i], n=1, f={k: v for k, (_, v) in pr["factors"].items()}, total=pr["total"], static=pr["static"], transit=pr["transit"],
                         chain=chain_score(ch)))
    units[4] = rows
    tests = []
    for lv, rows in units.items():
        allr = [x["r"] for x in rows]
        base_dn = sum(x["r"] < 0 for x in rows) / len(rows)
        groups = [(f"{FNAME[k]}: {lab}", k, val) for k in FACTORS for val, lab in ((-1, "hurts"), (1, "helps"))]
        groups += [("combination score: hurts (≤ −2)", "total", "hurts"), ("combination score: helps (≥ +2)", "total", "helps")]
        if lv == 4:
            groups += [("daily chain (Pratyantar + Sookshma + Prana): hurts (≤ −3)", "chain", "hurts"), ("daily chain: helps (≥ +3)", "chain", "helps")]
        for label, k, val in groups:
            if k == "total":
                sel = [x for x in rows if (x["total"] <= -2 if val == "hurts" else x["total"] >= 2)]
            elif k == "chain":
                sel = [x for x in rows if (x["chain"] <= -3 if val == "hurts" else x["chain"] >= 3)]
            else:
                sel = [x for x in rows if x["f"].get(k) == val]
            if len(sel) < 5:
                continue
            a = [x["r"] for x in sel]
            ids = {id(x) for x in sel}
            rest = [x["r"] for x in rows if id(x) not in ids]
            t = welch(a, rest)
            halves = []
            for lo, hi in ((dt.date(1900, 1, 1), SPLIT), (SPLIT, dt.date(2100, 1, 1))):
                aa = [x["r"] for x in sel if lo <= x["d"] < hi]
                bb = [x["r"] for x in rows if lo <= x["d"] < hi]
                halves.append(round((statistics.fmean(aa) - statistics.fmean(bb)) * 252, 1) if len(aa) >= 3 else None)
            tests.append(dict(chart=name, level=LEVEL_NAME[lv], group=label, units=len(sel), of=len(rows), mean=round(statistics.fmean(a) * 252, 1),
                              base=round(statistics.fmean(allr) * 252, 1), down=round(sum(v < 0 for v in a) / len(a) * 100, 1), base_down=round(base_dn * 100, 1),
                              t=None if t is None else round(t, 2), p=None if t is None else p_from_t(t), h1=halves[0], h2=halves[1],
                              expect=-1 if "hurts" in label else 1))
    return tests, units


def bh(tests):
    ps = sorted((x["p"], i) for i, x in enumerate(tests) if x["p"] is not None)
    m = len(ps)
    q = [None] * len(tests)
    prev = 1.0
    for rank in range(m, 0, -1):
        p, i = ps[rank - 1]
        prev = min(prev, p * m / rank)
        q[i] = prev
    for x, qq in zip(tests, q):
        x["q"] = None if qq is None else round(qq, 3)
        x["p"] = None if x["p"] is None else round(x["p"], 4)
        x["holds"] = bool(x["t"] is not None and x["q"] is not None and x["q"] < 0.10 and (x["t"] > 0) == (x["expect"] > 0)
                          and x["h1"] is not None and x["h2"] is not None and (x["h1"] > 0) == (x["h2"] > 0) == (x["expect"] > 0))
    return tests


# ------------------------------------------------------------------ forward list
def forward(name, a, b):
    nat = natal(name)
    A = dt.datetime.combine(a, dt.time(0), ET).astimezone(UTC)
    B = dt.datetime.combine(b + dt.timedelta(days=1), dt.time(0), ET).astimezone(UTC)
    out = {}
    for lv in (2, 3, 4):
        rows = []
        for path, s, e in DT.sequence(DT.CHARTS[name], lv, A if lv > 2 else A, B if lv > 2 else B + dt.timedelta(days=240)):
            lords = path.split("/")
            j = judge(nat, lords[-1], lords[-2], max(s, A) if lv == 4 else s)
            rows.append(dict(path=path, lord=lords[-1], parent=lords[-2], frm=s.astimezone(ET).strftime("%a %d %b %Y %H:%M"),
                             to=e.astimezone(ET).strftime("%a %d %b %Y %H:%M"), total=j["total"], static=j["static"], transit=j["transit"],
                             verdict=j["verdict"], factors={k: list(v) for k, v in j["factors"].items()}))
        out[LEVEL_NAME[lv]] = rows
    return out


def main():
    a = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 24)
    b = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2026, 12, 31)
    D, R = spx()
    tests = []
    nats = {}
    for name in ("USA", "NYSE"):
        print("testing", name)
        t, _ = test(name, D, R)
        tests += t
        nats[name] = natal(name)
    bh(tests)
    fw = {name: forward(name, a, b) for name in ("USA", "NYSE")}
    res = dict(start=str(a), end=str(b), tests=tests, forward=fw,
               natal={n: dict(asc=SIGNS[v["asc"]], planets={p: f"{SIGNS[s]} (house {house(v, s)})" for p, s in v["sign"].items()},
                              owns={p: sorted(h) for p, h in v["owns"].items()}) for n, v in nats.items()})
    json.dump(res, open(OUT / "dasha_combinations_ET.json", "w"), indent=1, default=str)
    (OUT / "dasha_combinations_ET.html").write_text(page(res), encoding="utf-8")
    for x in tests:
        if x["holds"] or (x["q"] is not None and x["q"] < 0.2):
            print(x)
    print("tests", len(tests), "holding", sum(x["holds"] for x in tests))


def page(res):
    E = html.escape
    css = """:root{color-scheme:light} body{margin:0;padding:16px;background:#fff;color:#1f2328;font:13.5px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1300px}
h1{font-size:20px;margin:0 0 6px} h2{font-size:17px;margin:24px 0 8px;border-bottom:1px solid #d0d7de;padding-bottom:4px} h3{font-size:14.5px;margin:16px 0 6px}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:4px 0 12px} th,td{border-bottom:1px solid #d0d7de;padding:4px 7px;text-align:left;vertical-align:top}
th{background:#f6f8fa} td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .s{font-size:12px;color:#57606a}
.g{color:#1e7b3a;font-weight:600} .r{color:#b42318;font-weight:600} details{margin:6px 0} summary{cursor:pointer;color:#0969da}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Dasha Combinations</title><style>{css}</style></head><body>",
         "<h1>Dasha combinations of the USA and NYSE charts: which ones hurt, and does the S&amp;P agree?</h1>",
         "<p class='s'>Each running lord is judged against its parent lord and the natal chart, and by its transit (BPHS dasha principles; the factors are listed at the "
         "bottom). +1 / −1 per factor; a combination <b>hurts</b> at −2 or below and <b>helps</b> at +2 or above. Tested on the S&amp;P 1928 – 20 Nov 2026: "
         "Antardasha, Pratyantar and Sookshma as whole periods, Prana day by day. A finding <b>holds</b> when it points the classical way, passes the false-discovery "
         "check (q &lt; 0.10) and points the same way in 1928–1976 and 1977–2026. Dasha levels below Antardasha depend on birth times known to the hour (USA) or not at all (NYSE).</p>"]
    held = [x for x in res["tests"] if x["holds"]]
    o.append(f"<h2>What the test says</h2><p><b>{len(held)} of {len(res['tests'])}</b> factor tests hold.</p>")
    o.append("<div class='wrap'><table><thead><tr><th>Chart</th><th>Level</th><th>Group</th><th>Periods / days</th><th>S&amp;P per year inside</th><th>All</th>"
             "<th>Down share</th><th>t</th><th>q</th><th>1928–76</th><th>1977–2026</th><th>Holds</th></tr></thead><tbody>")
    for x in sorted(res["tests"], key=lambda x: (not x["holds"], x["q"] if x["q"] is not None else 9)):
        cls = "g" if x["mean"] > x["base"] else "r"
        o.append(f"<tr><td>{x['chart']}</td><td>{x['level']}</td><td>{E(x['group'])}</td><td class='n'>{x['units']} / {x['of']}</td><td class='n {cls}'>{x['mean']:+.1f}%</td>"
                 f"<td class='n'>{x['base']:+.1f}%</td><td class='n'>{x['down']}% <span class='s'>vs {x['base_down']}%</span></td><td class='n'>{x['t']}</td><td class='n'>{x['q']}</td>"
                 f"<td class='n'>{'' if x['h1'] is None else format(x['h1'], '+.1f')}</td><td class='n'>{'' if x['h2'] is None else format(x['h2'], '+.1f')}</td><td>{'yes' if x['holds'] else ''}</td></tr>")
    o.append("</tbody></table></div><p class='s'>S&amp;P per year inside = mean daily return × 252 while the group runs; the half columns are the difference from all periods in each half.</p>")
    o.append(f"<h2>The coming combinations, {res['start']} – {res['end']}</h2>")
    for name, fw in res["forward"].items():
        nat = res["natal"][name]
        o.append(f"<h3>{name} — ascendant {nat['asc']}; " + "; ".join(f"{p} {v}" for p, v in nat["planets"].items()) + "</h3>")
        for lv in ("Pratyantar", "Sookshma", "Prana"):
            rows = ""
            for r in fw[lv]:
                cls = "r" if r["verdict"] == "hurts" else "g" if r["verdict"] == "helps" else ""
                why = "; ".join(f"{t} ({'+' if v > 0 else '−' if v < 0 else '0'})" for k, (t, v) in r["factors"].items() if v)
                rows += (f"<tr><td class='s'>{E(r['frm'])} → {E(r['to'])}</td><td><b>{E(r['path'])}</b></td><td class='n {cls}'>{r['total']:+d}</td>"
                         f"<td class='{cls}'>{r['verdict']}</td><td class='s'>{E(why)}</td></tr>")
            body = (f"<div class='wrap'><table><thead><tr><th>Period (ET)</th><th>Chain</th><th>Score</th><th>Reading</th><th>Why (factors that count)</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table></div>")
            o.append(f"<details{' open' if lv != 'Prana' else ''}><summary>{name} {lv} periods ({len(fw[lv])})</summary>{body}</details>")
    o.append("<h2>The factors</h2><ul>" + "".join(f"<li><b>{E(FNAME[k])}</b></li>" for k in FACTORS) + "</ul><p class='s'>"
             + E(__doc__.split("Each running lord")[1].split("Writes")[0]) + "</p></body></html>")
    return "".join(o)


if __name__ == "__main__":
    main()
