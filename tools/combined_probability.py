"""All layers together, weighed as a Vedic astrologer weighs a day: a probability for every day, scored on the last 60 days.

    python tools/combined_probability.py [END_DATE]        # default 2026-11-23; window = the 60 calendar days to END_DATE

Layers (each day is in one state per layer):
  every market   table    our signal table's label (gold/silver: test_signal_table definitions; S&P/Sensex: the
                          market table's qualifying PDF and calendar rules)
  gold           v1       Model v1.0 bias (Brihat Samhita Ch.41 + BPHS Shadbala + Ashtakavarga)
  S&P / Sensex   bigmove  a robust big-move factor is active (market_summary)
  S&P only, for each of the USA (Sibly) and NYSE (10:00 LMT) charts:
                 dasha    condition of the running Antardasha, Pratyantar and Sookshma lords in transit (BPHS dasha
                          principles): +1 exalted or own sign, -1 debilitated, -1 combust, +1 in houses 1/4/5/7/9/10
                          from the natal ascendant, -1 in 6/8/12, -1 joined or aspected by Saturn or Mars, +1 joined or
                          aspected by Jupiter, +1 Shadbala ratio >= 1.1, -1 below 0.9; summed: strong >= 2, afflicted <= -2
                 gochara  slow planets (Jupiter, Saturn, Rahu) from the natal Moon, Phaladeepika ch.26 good houses
                          (Jupiter 2/5/7/9/11; Saturn and Rahu 3/6/11; +1 good, -1 elsewhere): favourable if most are
                          good, adverse if none is
                 chandra  Chandra bala: transit Moon in 1/3/6/7/10/11 from the natal Moon
                 tara     Tara bala: transit Moon's nakshatra counted from the natal one (good 2/4/6/8/9, bad 3/5/7, janma 1)
           and   jup-ven  Solar return's Jupiter sextile Venus (within 2 degrees)
  Gochara, Chandra bala and Tara bala are classical practice that our listed sources do not state; they are used here
  because the user asked for a pro Vedic reading (24 Nov 2026), and each is tested on its own like the rest.
Weights: for each state, how often the market rose in it before the scoring period, shrunk toward the base rate
(200 pseudo-days). Combination: naive Bayes on log-odds - start at the base rate, each layer adds its log
likelihood ratio. Three probabilities per day: up today, up over the next 5 sessions (entry = previous close), big day.
Checks:
  walk-forward  weights from 2000-2012, scored 2013 up to the window (gold/silver use walk-forward table labels);
                a layer is "kept" for a target when on its own it improves that target's Brier score there.
  60 days       weights from 2000 up to the day before the window; all layers and kept layers.
Writes build/pdfref/combined_probability_60d_ET.{html,json}. Market prices and astrology only.
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import html
import json
import math
import pathlib
import sys
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
CACHE = OUT / "backtest"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from model_check_60d import BIG, NAME, load, market_labels, prices, robust_vol, table_rows  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
DT = load(ROOT / "tools" / "dasha_transits.py", "dtr")
swe.set_sid_mode(swe.SIDM_LAHIRI)
FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
BODIES = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
          "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
SIGNS = DT.SIGNS
SHRINK = 200
SPLIT = dt.date(2013, 1, 1)
LAYERS = {"gold": ["table", "v1"], "silver": ["table"], "sensex": ["table", "bigmove"],
          "spx": ["table", "bigmove", "USA dasha", "NYSE dasha", "USA gochara", "NYSE gochara", "USA chandra", "NYSE chandra",
                  "USA tara", "NYSE tara", "jup-ven"]}
CLASSICAL = {"USA gochara", "NYSE gochara", "USA chandra", "NYSE chandra", "USA tara", "NYSE tara"}
DESC = {"table": "our signal table's label", "v1": "Model v1.0 bias (Ch.41 + Shadbala)", "bigmove": "robust big-move factor",
        "dasha": "dasha lords' condition (Antar + Pratyantar + Sookshma)", "gochara": "Jupiter, Saturn, Rahu from the natal Moon",
        "chandra": "Chandra bala", "tara": "Tara bala", "jup-ven": "Solar return: Jupiter sextile Venus"}
TARA = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhaka", "Naidhana", "Mitra", "Param Mitra"]
GOOD_FROM_MOON = {"Jupiter": (2, 5, 7, 9, 11), "Saturn": (3, 6, 11), "Rahu": (3, 6, 11)}
TARGETS = ("up1", "up5", "big")
TNAME = {"up1": "up today", "up5": "up over the next 5 sessions", "big": "big day"}


# ------------------------------------------------------------------ sky and natal data
def sky(d):
    jd = swe.julday(d.year, d.month, d.day, 12 + (5 if dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET).utcoffset().total_seconds() == -18000 else 4))
    p = {}
    for b, k in BODIES.items():
        r = swe.calc_ut(jd, k, FL)[0]
        p[b] = (r[0] % 360, r[3])
    p["Ketu"] = ((p["Rahu"][0] + 180) % 360, p["Rahu"][1])
    return p


def natal(ch):
    return dict(asc=int(DT.asc(ch["ut"], ch["lat"], ch["lon"]) // 30), moon=int(DT.pos(ch["ut"], "Moon")[0] // 30),
                nak=int(DT.pos(ch["ut"], "Moon")[0] // (360 / 27)))


def lord_score(lord, p, nat, sb):
    lon = p[lord][0]
    si = int(lon // 30)
    sign = SIGNS[si]
    s = 0
    s += 1 if DT.EXALT.get(lord) == sign or sign in DT.OWN.get(lord, ()) else 0
    s -= 1 if DT.DEBIL.get(lord) == sign else 0
    if lord in DT.COMBUST and min((lon - p["Sun"][0]) % 360, (p["Sun"][0] - lon) % 360) <= DT.COMBUST[lord]:
        s -= 1
    h = (si - nat["asc"]) % 12 + 1
    s += 1 if h in (1, 4, 5, 7, 9, 10) else -1 if h in (6, 8, 12) else 0
    asp = {"Saturn": (1, 3, 7, 10), "Mars": (1, 4, 7, 8), "Jupiter": (1, 5, 7, 9)}
    hit = {b: b != lord and (si - int(p[b][0] // 30)) % 12 + 1 in asp[b] for b in asp}
    s -= 1 if hit["Saturn"] or hit["Mars"] else 0
    s += 1 if hit["Jupiter"] else 0
    if lord in sb:
        s += 1 if sb[lord] >= 1.1 else -1 if sb[lord] < 0.9 else 0
    return s


def vedic_states(d, p, sb, charts):
    st = {}
    noon = dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET)
    for name, (ch, nat) in charts.items():
        lords = [x[0] for x in DT.dasha_at(ch, noon, 4)[1:]]
        sc = sum(lord_score(lo, p, nat, sb) for lo in lords)
        st[f"{name} dasha"] = "strong" if sc >= 2 else "afflicted" if sc <= -2 else "mixed"
        g = sum(1 if (int(p[b][0] // 30) - nat["moon"]) % 12 + 1 in good else -1 for b, good in GOOD_FROM_MOON.items())
        st[f"{name} gochara"] = "favourable" if g > 0 else "adverse" if g == -3 else "mixed"
        hm = (int(p["Moon"][0] // 30) - nat["moon"]) % 12 + 1
        st[f"{name} chandra"] = "good" if hm in (1, 3, 6, 7, 10, 11) else "weak"
        t = ((int(p["Moon"][0] // (360 / 27)) - nat["nak"]) % 27) % 9
        st[f"{name} tara"] = "janma" if t == 0 else "good" if t in (1, 3, 5, 7, 8) else "bad"
    sep = abs((p["Jupiter"][0] - p["Venus"][0] + 180) % 360 - 180)
    st["jup-ven"] = "on" if abs(sep - 60) < 2 else "off"
    return st


def v1_state(bias):
    return "bearish" if "bearish" in bias else {"Neutral / mixed": "neutral"}.get(bias, bias.lower())


def tbl_state(lab):
    return "no signal" if not lab or not lab[0] else f"{lab[0]} {lab[1]}" if lab[0] in ("Bullish", "Bearish") else lab[0]


# ------------------------------------------------------------------ data
def market_history(end):
    f = CACHE / "market_label_history.json.gz"
    if f.exists():
        h = json.load(gzip.open(f, "rt", encoding="utf-8"))
        if h.get("to", "") >= str(end):
            return {mk: {dt.date.fromisoformat(k): tuple(v) for k, v in h[mk].items()} for mk in ("spx", "sensex")}
    out = {"spx": {}, "sensex": {}}
    for y in range(2000, end.year + 1):
        ml = market_labels(dt.date(y, 1, 1), min(dt.date(y, 12, 31), end))
        for mk in out:
            out[mk].update(ml[mk])
    with gzip.open(f, "wt", encoding="utf-8") as fh:
        json.dump(dict(to=str(end), **{mk: {str(k): list(v) for k, v in out[mk].items()} for mk in out}), fh)
    return out


def build(end):
    """Per market: list of day records with states and outcomes, 2000 -> end."""
    from finastro.pdfref import bs41_model as M
    charts = {n: (DT.CHARTS[n], natal(DT.CHARTS[n])) for n in ("USA", "NYSE")}
    mh = market_history(min(end, dt.date(2026, 11, 22)))
    pub = table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", "spx"), table_rows(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json", "sensex")
    mh["spx"].update(pub[0])
    mh["sensex"].update(pub[1])
    labels = {}
    for mk in ("gold", "silver"):
        h = json.load(gzip.open(CACHE / f"{mk}_label_history.json.gz", "rt", encoding="utf-8"))
        ins = {dt.date.fromisoformat(k): tuple(v) for k, v in h["in_sample"].items()}
        wf = {dt.date.fromisoformat(k): tuple(v) for k, v in h["walk_forward"].items()}
        pubm = table_rows(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json")
        ins.update(pubm)
        wf.update(pubm)
        labels[mk] = (ins, wf)
    vol = robust_vol(dt.date(2000, 1, 1), end)
    skyc, v1c, sbc, ved = {}, {}, {}, {}
    data = {}
    for mk in ("gold", "silver", "spx", "sensex"):
        P = prices(mk, end)
        D = [d for d in P if d >= dt.date(2000, 1, 1)]
        recs = []
        for i in range(1, len(D)):
            d = D[i]
            if d > end:
                break
            r1 = (P[d] / P[D[i - 1]] - 1) * 100
            r5 = (P[D[i + 4]] / P[D[i - 1]] - 1) * 100 if i + 4 < len(D) else None
            st, st_wf = {}, {}
            if mk in ("gold", "silver"):
                if d < dt.date(2000, 11, 20):
                    continue
                st["table"] = tbl_state(labels[mk][0].get(d))
                st_wf["table"] = tbl_state(labels[mk][1].get(d))
            else:
                st["table"] = tbl_state(mh[mk].get(d))
                st["bigmove"] = "on" if d in vol.get(mk, set()) else "off"
            if mk == "gold" or mk == "spx":
                if d not in v1c:
                    r = M.evaluate(d)
                    v1c[d] = v1_state(r["bias"])
                    sbc[d] = {k: v["ratio"] for k, v in r["shadbala"].items()}
                if mk == "gold":
                    st["v1"] = v1c[d]
            if mk == "spx":
                if d not in ved:
                    skyc[d] = sky(d)
                    ved[d] = vedic_states(d, skyc[d], sbc[d], charts)
                st.update(ved[d])
            recs.append(dict(d=d, r1=r1, r5=r5, st=st, st_wf={**st, **st_wf}, end5=D[i + 4] if i + 4 < len(D) else None,
                             up1=r1 > 0, up5=None if r5 is None else r5 > 0, big=abs(r1) >= BIG[mk]))
        data[mk] = recs
    return data


# ------------------------------------------------------------------ model
def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def fit(recs, layers, target, key="st"):
    rows = [r for r in recs if r[target] is not None]
    base = sum(r[target] for r in rows) / len(rows)
    w = {}
    for L in layers:
        cnt = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            c = cnt[r[key][L]]
            c[0] += 1
            c[1] += r[target]
        w[L] = {s: dict(n=n, rate=k / n, llr=logit((k + SHRINK * base) / (n + SHRINK)) - logit(base)) for s, (n, k) in cnt.items()}
    return dict(base=base, w=w, layers=list(layers))


def predict(model, r, key="st"):
    z = logit(model["base"]) + sum(model["w"][L].get(r[key][L], {}).get("llr", 0.0) for L in model["layers"])
    return 1 / (1 + math.exp(-z))


def score(model, recs, target, key="st"):
    rows = [r for r in recs if r[target] is not None]
    if not rows:
        return None
    b = model["base"]
    ps = [predict(model, r, key) for r in rows]
    ys = [1 if r[target] else 0 for r in rows]
    bm = sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)
    bb = sum((b - y) ** 2 for y in ys) / len(ys)
    res = dict(n=len(ys), actual=round(sum(ys) / len(ys) * 100, 1), base=round(b * 100, 1), brier=round(bm, 4), brier_base=round(bb, 4),
               skill=round((1 - bm / bb) * 100, 2) if bb else None, avg_p=round(sum(ps) / len(ps) * 100, 1))
    if target != "big":
        cu = [(p, y) for p, y in zip(ps, ys) if p > b + 0.02]
        cd = [(p, y) for p, y in zip(ps, ys) if p < b - 0.02]
        res.update(calls_up=len(cu), right_up=round(sum(y for _, y in cu) / len(cu) * 100) if cu else None,
                   calls_down=len(cd), right_down=round(sum(1 - y for _, y in cd) / len(cd) * 100) if cd else None,
                   hit=round((sum(y for _, y in cu) + sum(1 - y for _, y in cd)) / (len(cu) + len(cd)) * 100) if cu or cd else None)
    else:
        bigp = [p for p, y in zip(ps, ys) if y]
        oth = [p for p, y in zip(ps, ys) if not y]
        res.update(p_on_big=round(sum(bigp) / len(bigp) * 100, 1) if bigp else None, p_on_other=round(sum(oth) / len(oth) * 100, 1) if oth else None)
    bands = collections.OrderedDict()
    for lo, hi in ((0, .4), (.4, .45), (.45, .5), (.5, .55), (.55, .6), (.6, 1.01)) if target != "big" else ((0, .03), (.03, .06), (.06, .1), (.1, .2), (.2, 1.01)):
        sel = [y for p, y in zip(ps, ys) if lo <= p < hi]
        if sel:
            bands[f"{lo * 100:.0f}-{min(hi, 1) * 100:.0f}%"] = dict(n=len(sel), actual=round(sum(sel) / len(sel) * 100))
    res["bands"] = bands
    return res


def main():
    end = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date(2026, 11, 23)
    start = end - dt.timedelta(days=60)
    data = build(end)
    res = dict(start=str(start), end=str(end), shrink=SHRINK, markets={})
    for mk, recs in data.items():
        layers = LAYERS[mk]
        before = [r for r in recs if r["d"] < start]
        win = [r for r in recs if start <= r["d"] <= end]
        wf_tr = [r for r in recs if r["d"] < SPLIT]
        wf_te = [r for r in recs if SPLIT <= r["d"] < start]
        m = dict(name=NAME[mk], layers=layers, walk_forward={}, window={}, kept={}, layer_test={}, weights={})
        for t in TARGETS:
            tr_before = [r for r in before if t != "up5" or (r["end5"] and r["end5"] < start)]
            m["layer_test"][t] = {L: score(fit(wf_tr, [L], t, "st_wf"), wf_te, t, "st_wf") for L in layers}
            kept = [L for L in layers if (m["layer_test"][t][L]["skill"] or 0) > 0] or []
            m["kept"][t] = kept
            m["walk_forward"][t] = dict(all=score(fit(wf_tr, layers, t, "st_wf"), wf_te, t, "st_wf"),
                                        kept=score(fit(wf_tr, kept, t, "st_wf"), wf_te, t, "st_wf") if kept else None)
            full = fit(tr_before, layers, t)
            kmod = fit(tr_before, kept, t) if kept else None
            m["window"][t] = dict(all=score(full, win, t), kept=score(kmod, win, t) if kmod else None)
            m["weights"][t] = dict(base=round(full["base"] * 100, 1), w={L: {s: dict(n=v["n"], rate=round(v["rate"] * 100, 1), shift=round(v["llr"], 3))
                                                                          for s, v in sorted(full["w"][L].items())} for L in layers})
            for r in win:
                r.setdefault("p", {})[t] = round(predict(full, r) * 100, 1)
                r.setdefault("pk", {})[t] = round(predict(kmod, r) * 100, 1) if kmod else None
        m["days"] = [dict(date=str(r["d"]), r1=round(r["r1"], 2), r5=None if r["r5"] is None else round(r["r5"], 2), big=r["big"],
                          p=r["p"], pk=r["pk"], st=r["st"]) for r in win]
        res["markets"][mk] = m
    json.dump(res, open(OUT / "combined_probability_60d_ET.json", "w"), indent=1, default=str)
    (OUT / "combined_probability_60d_ET.html").write_text(page(res), encoding="utf-8")
    for mk, m in res["markets"].items():
        print("==", m["name"])
        for t in TARGETS:
            w, wf = m["window"][t], m["walk_forward"][t]
            print(f"  {t}: kept {m['kept'][t]}")
            for lab, x in (("WF all", wf["all"]), ("WF kept", wf["kept"]), ("60d all", w["all"]), ("60d kept", w["kept"])):
                if x:
                    print(f"     {lab:8s} n {x['n']:5d} actual {x['actual']}% base {x['base']}% avg_p {x['avg_p']} skill {x['skill']}% "
                          + (f"hit {x.get('hit')}% (up {x.get('calls_up')}/{x.get('right_up')}% down {x.get('calls_down')}/{x.get('right_down')}%)" if t != "big" else f"p on big {x['p_on_big']} other {x['p_on_other']}"))
            for L in m["layers"]:
                x = m["layer_test"][t][L]
                print(f"        layer {L:13s} WF skill {x['skill']}%")


# ------------------------------------------------------------------ page
def pct(x, suf="%"):
    return "–" if x is None else f"{x}{suf}"


def page(res):
    css = """:root{color-scheme:light} body{margin:0;padding:16px;background:#fff;color:#1f2328;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1250px}
h1{font-size:20px;margin:0 0 6px} h2{font-size:17px;margin:26px 0 8px;border-bottom:1px solid #d0d7de;padding-bottom:4px} h3{font-size:15px;margin:18px 0 6px}
.wrap{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0 12px} th,td{border-bottom:1px solid #d0d7de;padding:5px 8px;text-align:left;vertical-align:top}
th{background:#f6f8fa} td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap} .s{font-size:12px;color:#57606a}
.g{color:#1e7b3a;font-weight:600} .r{color:#b42318;font-weight:600} details{margin:8px 0} summary{cursor:pointer;color:#0969da}"""
    out = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Combined Probability</title><style>{css}</style></head><body>",
           f"<h1>All layers together: a probability for every day, {res['start']} – {res['end']}</h1>",
           "<p class='s'>Each layer puts the day in a state (for example Tara bala good / bad / janma). A state's weight is how often the market rose in it "
           f"before the scored period, shrunk toward the base rate ({res['shrink']} pseudo-days). The layers are joined on log-odds (naive Bayes): start at the base "
           "rate and let each layer move it. <b>Skill</b> = how much better the probabilities are than always quoting the base rate (Brier score; 0% = no better, "
           "negative = worse). <b>Calls</b>: up when the probability is 2+ points above the base rate, down when 2+ below. <b>Kept</b> layers improved the "
           "forecast of that target on their own over 2013–2026 (fitted on 2000–2012), chosen before looking at the 60 days.</p>"]
    out.append("<h2>Bottom line, last 60 days</h2><div class='wrap'><table><thead><tr><th>Market</th><th>Forecast</th><th>Market went up</th>"
               "<th>Combined call right (all layers)</th><th>Kept layers only</th><th>Same model 2013–2026, kept layers</th><th>Skill 2013–2026 (kept)</th></tr></thead><tbody>")
    for mk, m in res["markets"].items():
        for t in ("up1", "up5"):
            a, k, wk = m["window"][t]["all"], m["window"][t]["kept"], m["walk_forward"][t]["kept"] or m["walk_forward"][t]["all"]
            def hit(x):
                return "no calls" if not x or x["hit"] is None else f"{x['hit']}% of {x['calls_up'] + x['calls_down']} calls"
            out.append(f"<tr><td>{m['name']}</td><td>{TNAME[t]}</td><td class='n'>{a['actual']}% of {a['n']} days</td><td class='n'>{hit(a)}</td>"
                       f"<td class='n'>{hit(k)}</td><td class='n'>{hit(wk)}</td><td class='n'>{pct(wk['skill'])}</td></tr>")
    out.append("</tbody></table></div><p class='s'>A call is a probability 2+ points away from the base rate. Compare each hit rate with the market's own up share: "
               "in a falling 60 days, a model that leans bearish is right often without skill. The 2013–2026 column is the long-run figure to trust.</p>")
    for t in TARGETS:
        out.append(f"<h2>Probability of {TNAME[t]}</h2><div class='wrap'><table><thead><tr><th>Market</th><th>Check</th><th>Layers</th><th>Days</th><th>Actual</th>"
                   f"<th>Base</th><th>Avg probability</th><th>Skill</th>" + ("<th>Calls up (right)</th><th>Calls down (right)</th><th>Hit rate</th>" if t != "big" else "<th>Avg P on big days</th><th>Avg P other days</th>") + "</tr></thead><tbody>")
        for mk, m in res["markets"].items():
            for chk, blk in (("2013–2026 walk-forward", m["walk_forward"][t]), ("last 60 days", m["window"][t])):
                for lay in ("all", "kept"):
                    x = blk[lay]
                    if not x:
                        continue
                    ls = "all: " + ", ".join(m["layers"]) if lay == "all" else "kept: " + (", ".join(m["kept"][t]) or "none")
                    sk = x["skill"]
                    cls = "g" if sk and sk > 0 else "r" if sk and sk < 0 else ""
                    extra = (f"<td class='n'>{x['calls_up']} ({pct(x['right_up'])})</td><td class='n'>{x['calls_down']} ({pct(x['right_down'])})</td><td class='n'>{pct(x['hit'])}</td>"
                             if t != "big" else f"<td class='n'>{pct(x['p_on_big'])}</td><td class='n'>{pct(x['p_on_other'])}</td>")
                    out.append(f"<tr><td>{m['name']}</td><td>{chk}</td><td class='s'>{html.escape(ls)}</td><td class='n'>{x['n']}</td><td class='n'>{x['actual']}%</td>"
                               f"<td class='n'>{x['base']}%</td><td class='n'>{x['avg_p']}%</td><td class='n {cls}'>{pct(sk)}</td>{extra}</tr>")
        out.append("</tbody></table></div>")
    out.append("<h2>Each layer on its own, 2013–2026 walk-forward (skill, %)</h2><div class='wrap'><table><thead><tr><th>Market</th><th>Layer</th><th>What it is</th>"
               + "".join(f"<th>{TNAME[t]}</th>" for t in TARGETS) + "</tr></thead><tbody>")
    for mk, m in res["markets"].items():
        for L in m["layers"]:
            key = L.split(" ", 1)[-1] if L.startswith(("USA", "NYSE")) else L
            cells = ""
            for t in TARGETS:
                sk = m["layer_test"][t][L]["skill"]
                cells += f"<td class='n {'g' if sk and sk > 0 else 'r' if sk and sk < 0 else ''}'>{pct(sk)}</td>"
            out.append(f"<tr><td>{m['name']}</td><td>{html.escape(L)}{' *' if L in CLASSICAL else ''}</td><td class='s'>{html.escape(DESC.get(key, ''))}</td>{cells}</tr>")
    out.append("</tbody></table></div><p class='s'>* classical practice (Phaladeepika gochara, Chandra bala, Tara bala), not stated in our listed sources; included at the user's request for a pro Vedic reading.</p>")
    out.append("<h2>How each state moves the odds (weights used for the 60 days, 5-session target)</h2>")
    for mk, m in res["markets"].items():
        wt = m["weights"]["up5"]
        rows = ""
        for L, states in wt["w"].items():
            for s, v in states.items():
                cls = "g" if v["shift"] > 0.02 else "r" if v["shift"] < -0.02 else ""
                rows += f"<tr><td>{html.escape(L)}</td><td>{html.escape(s)}</td><td class='n'>{v['n']}</td><td class='n'>{v['rate']}%</td><td class='n {cls}'>{v['shift']:+.3f}</td></tr>"
        out.append(f"<details><summary>{m['name']} (base {wt['base']}% up over 5 sessions)</summary><div class='wrap'><table><thead><tr><th>Layer</th><th>State</th>"
                   f"<th>Days</th><th>Up over 5 sessions</th><th>Log-odds shift</th></tr></thead><tbody>{rows}</tbody></table></div></details>")
    out.append("<h2>Day by day, last 60 days (probabilities from all layers; kept layers in brackets)</h2>")
    for mk, m in res["markets"].items():
        rows = ""
        for r in m["days"]:
            def cell(t, r=r):
                k = r["pk"][t]
                return f"{r['p'][t]}%" + (f" <span class='s'>({k}%)</span>" if k is not None else "")
            st = "; ".join(f"{k}: {v}" for k, v in r["st"].items() if v not in ("off", "no signal"))
            c1 = "g" if r["r1"] > 0 else "r"
            c5 = "" if r["r5"] is None else "g" if r["r5"] > 0 else "r"
            r5 = "–" if r["r5"] is None else f"{r['r5']:+.2f}%"
            rows += (f"<tr><td>{r['date']}</td><td class='n'>{cell('up1')}</td><td class='n {c1}'>{r['r1']:+.2f}%</td><td class='n'>{cell('up5')}</td>"
                     f"<td class='n {c5}'>{r5}</td><td class='n'>{cell('big')}</td><td>{'yes' if r['big'] else ''}</td><td class='s'>{html.escape(st)}</td></tr>")
        out.append(f"<details{' open' if mk == 'spx' else ''}><summary>{m['name']}</summary><div class='wrap'><table><thead><tr><th>Date</th><th>P(up today)</th><th>Today</th>"
                   f"<th>P(up, 5 sessions)</th><th>5 sessions</th><th>P(big day)</th><th>Big?</th><th>States</th></tr></thead><tbody>{rows}</tbody></table></div></details>")
    out.append("<p class='s'>Caveats: the table layers' rules were chosen on 2000–2026 data, which overlaps the walk-forward period for the S&amp;P and Sensex (gold and silver "
               "use their walk-forward labels there). Dasha levels below Antardasha depend on birth times known only to the hour or not at all. "
               "Sixty days is about 40 sessions: a health check, not a test.</p></body></html>")
    return "".join(out)


if __name__ == "__main__":
    main()
