"""January 2027 after the November review: what each call is worth, and January's calls frozen for scoring.

    python tools/january_2027_outlook.py          # after tools/week_deep_dive.py jan, bigday_clean_test.py, november_review.py

For every kind of call the calendars make for January 2027 it lists the January calls and the best evidence there is
for that kind of call, judged the way the November review judged November (against chance for the same up/down mix):
  * S&P / Sensex labels: the rules behind each January span, each rule's day-by-day record (in sample, 2000-2026),
    whether the walk-forward choice on 2000-2013 picked it, and the clean label-strength record (2013-2026);
  * gold / silver labels: the clean walk-forward strength record (2013-2026);
  * the combined model (clean walk-forward), Model v1.0 (2000-2026), the Solar return day calls (1928-2026);
  * Paap Kartari: B116 (Mercury) and B117 (Jupiter), source rules from the 2026 document, each window scored as in
    tools/kartari_test.py, in both halves of 2000-2026;
  * big days: the clean factors (tools/bigday_clean_test.py) active in January, and the in-sample ones;
  * the January deep dive (every sky event backtested).
It also freezes January's calls (the day records the November scorer reads: labels, model, rules, calendar verdicts,
Model v1.0, Solar return, the Mars-Jupiter-node lead, big-day factors) into january_2027_calls_ET.json, so January can
be scored afterwards exactly as November was. The file is rewritten on every run until 31 Dec 2026 (US Eastern) and
never from 1 Jan 2027.
Writes build/pdfref/january_2027_outlook_ET.json (shown in both calendars).
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import importlib.util
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
ET = ZoneInfo("America/New_York")
MKS = ("spx", "sensex", "gold", "silver")
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}
SHORT = {"spx": "S&P", "sensex": "Sensex", "gold": "Gold", "silver": "Silver"}
ON = {"spx": "the S&P", "sensex": "the Sensex", "gold": "gold", "silver": "silver"}
A, B = dt.date(2027, 1, 1), dt.date(2027, 1, 31)
FROZEN = OUT / "january_2027_calls_ET.json"
CLEAN = {"spx": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
         "sensex": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
         "gold": "Model call (2+ points from normal), all layers", "silver": "Model call (2+ points from normal), all layers"}
KEEP = ("date", "weekday", "closed", "early", "signals", "prob", "tally", "calendar", "v1", "author", "mjn", "sr_call", "sr_month", "vol", "watch")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def rng(a, b):
    a, b = dt.date.fromisoformat(str(a)[:10]), dt.date.fromisoformat(str(b)[:10])
    if a == b:
        return f"{a.day} {a:%b}"
    return f"{a.day}–{b.day} {b:%b}" if (a.year, a.month) == (b.year, b.month) else f"{a.day} {a:%b} – {b.day} {b:%b}"


def merge(rows):
    """Adjacent table rows with the same label and rules become one span."""
    out = []
    for r in rows:
        if out and out[-1]["sig"] == r["sig"] and out[-1]["st"] == r["st"] and out[-1].get("ids") == r.get("ids") \
                and (dt.date.fromisoformat(str(r["frm"])[:10]) - dt.date.fromisoformat(str(out[-1]["to"])[:10])).days <= 1:
            out[-1] = dict(out[-1], to=r["to"])
        else:
            out.append(dict(r))
    return out


def poisson_sf(k, lam):
    import math
    if k <= 0:
        return 1.0
    term = math.exp(-lam)
    cdf = term
    for i in range(1, k):
        term *= lam / i
        cdf += term
    return max(0.0, 1 - cdf)


def kartari_big(past, mk):
    """B116 windows 2000-2026: +/-2% days inside them against each year's own rate, with and without a benefic aspect on Mercury."""
    MC = load(ROOT / "tools" / "model_check_60d.py", "mc_jo")
    P = MC.prices(mk, dt.date(2026, 11, 20))
    D = sorted(P)
    yr = collections.defaultdict(lambda: [0, 0])
    for i in range(1, len(D)):
        yr[D[i].year][0] += 1
        yr[D[i].year][1] += abs(P[D[i]] / P[D[i - 1]] - 1) >= 0.02
    out = {}
    for name, keep in (("all windows", lambda w: True), ("with a benefic aspect (January's case)", lambda w: bool(w["benefic"])),
                       ("without a benefic aspect", lambda w: not w["benefic"])):
        obs = exp = 0.0
        nw = 0
        for w in past:
            if not keep(w) or not w.get("n"):
                continue
            y = dt.datetime.strptime(w["start"], "%d %b %Y").year
            n, b = yr.get(y, [0, 0])
            if not n:
                continue
            nw += 1
            obs += w["big"]
            exp += w["n"] * b / n
        out[name] = dict(windows=nw, big=int(obs), exp=round(exp, 1), lift=round(obs / exp, 2) if exp else None,
                         p=round(poisson_sf(int(obs), exp), 4) if exp else None)
    return out


def rec_txt(r):
    return f"{r['hit']}% vs {r['exp']}% by chance (p {r['p']}, {r['n']} days)" if r and r.get("n") else "no record"


def kartari_verdict(rec):
    a, h1, h2 = rec["all"], rec["h1"], rec["h2"]
    both = h1["hit_rate"] > h1["base_rate"] and h2["hit_rate"] > h2["base_rate"]
    if a["p_value"] < 0.05 and both:
        return "supported"
    return "not supported"


def freeze(days, now):
    """January's calls as the calendar shows them now; never rewritten once January has begun (US Eastern)."""
    if FROZEN.exists() and now.date() >= A:
        j = json.load(open(FROZEN))
        return dict(path=FROZEN.name, frozen_at=j["frozen_at"], rewritten=False, sessions=j["sessions"])
    slim = []
    for x in days:
        y = {k: x.get(k) for k in KEEP}
        y["calendar"] = [dict(market=c["market"], verdict=c["verdict"]) for c in x.get("calendar", [])]
        y["v1"] = dict(bias=x["v1"]["bias"], confidence=x["v1"].get("confidence"))
        y["author"] = dict(rules=x["author"]["rules"], forecasts=x["author"]["forecasts"])
        slim.append(y)
    sessions = {mk: sum(1 for x in days if mk in x["prob"]) for mk in MKS}
    FROZEN.write_text(json.dumps(dict(frozen_at=now.strftime("%Y-%m-%d %H:%M ET"), month="2027-01", sessions=sessions,
                                      note="January 2027 calls as the calendars showed them; scored after January with tools/november_review.py's scorer",
                                      days=slim), separators=(",", ":"), default=str))
    return dict(path=FROZEN.name, frozen_at=now.strftime("%Y-%m-%d %H:%M ET"), rewritten=True, sessions=sessions)


def main():
    cache = OUT / "backtest" / f"days_{A}_to_{B}.json.gz"
    if not cache.exists():
        sys.exit("run: python tools/week_deep_dive.py jan   (it builds the January day data)")
    days = json.load(gzip.open(cache, "rt", encoding="utf-8"))["days"]
    now = dt.datetime.now(ET)
    nov = json.load(open(OUT / "november_review_2026-11_ET.json"))
    t = nov["tuning"]
    rpd = {(r["id"], r["market"]): r for r in t["rules_per_day"]}
    msig = json.load(open(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json"))
    kt = {r["key"]: r for r in json.load(open(OUT / "kartari_test_ET.json"))["rules"]}
    kj = json.load(open(OUT / "kartari_jan2027_ET.json"))["markets"]
    bc = json.load(open(OUT / "bigday_clean_test_ET.json"))["markets"]
    vol_ok = next((r.get("vol_ok") for r in nov["recommendations"] if r["id"] == "big_days"), None) or {}
    out = dict(made=now.strftime("%Y-%m-%d %H:%M ET"), start=str(A), end=str(B), markets={})

    # ---- label spans
    for mk in MKS:
        m = dict(name=NAME[mk], sessions=[x["date"] for x in days if mk in x["prob"]],
                 closed=[f"{x['date']} {x['closed'][mk]}" for x in days if mk in x["closed"]])
        lw = t["labels"][mk].get("walk_forward") or t["labels"][mk]
        picked = set(lw.get("rules") or [])
        spans = []
        if mk in ("spx", "sensex"):
            rows = merge([r for r in msig["tables"][mk] if str(r["frm"])[:10] <= str(B) and str(r["to"])[:10] >= str(A)])
            for r in rows:
                rules = []
                for rid in r.get("ids") or []:
                    ru = msig["rules"].get(rid, {})
                    pd_ = rpd.get((rid, mk))
                    rules.append(dict(id=rid, title=ru.get("title", rid), tone=ru.get("tone"), strength=ru.get("st"), span_record=ru.get("record"),
                                      day=pd_["day"] if pd_ else None, second_half=pd_["second_half"] if pd_ else None,
                                      picked_2000_2013=ru.get("title") in picked))
                spans.append(dict(frm=str(r["frm"])[:10], to=str(r["to"])[:10], sig=r["sig"], st=r["st"], why=r["why"], rules=rules,
                                  strength_record=lw["rows"].get(f"{r['st']}|d1") if r["st"] in ("Low", "Moderate", "High") else None))
        else:
            rows = merge([dict(r, ids=r.get("why")) for r in json.load(open(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json"))
                          if str(r["frm"])[:10] <= str(B) and str(r["to"])[:10] >= str(A)])
            for r in rows:
                spans.append(dict(frm=str(r["frm"])[:10], to=str(r["to"])[:10], sig=r["sig"], st=r["st"], why=r["why"], rules=[],
                                  strength_record=lw["rows"].get(f"{r['st']}|d1") if r["st"] in ("Low", "Moderate", "High") else None))
        m["spans"] = spans
        m["label_any"] = lw["rows"]["Any strength|d1"]
        m["label_source"] = lw["source"]
        # ---- model
        lean = collections.Counter()
        for x in days:
            pr = x["prob"].get(mk)
            if pr:
                d = pr["all"]["up1"] - pr["base"]["up1"]
                lean["up" if d >= 2 else "down" if d <= -2 else "none"] += 1
        m["model"] = dict(lean=dict(lean), record=t["model"][mk]["rows"][CLEAN[mk]])
        # ---- big days: clean factors active in January, and the in-sample ones
        V = load(ROOT / "tools" / "validate_external_model.py", f"vem_{mk}")
        clean_days, insample = {}, collections.Counter()
        for f in vol_ok.get(mk, []):
            fn = V.ROBUST.get(mk, {}).get(f)
            if fn:
                ds = [str(A + dt.timedelta(days=i)) for i in range((B - A).days + 1) if fn(A + dt.timedelta(days=i))]
                if ds:
                    clean_days[f] = ds
        for x in days:
            for f in x["vol"].get(mk, []) or []:
                if f not in vol_ok.get(mk, []):
                    insample[f] += 1
        m["big"] = dict(clean_active=clean_days, insample_active=dict(insample), clean_test=bc[mk]["verdict"],
                        model_big="untested (November review)")
        out["markets"][mk] = m

    # ---- Paap Kartari (S&P and Sensex: the records are on those two)
    kart = {}
    for key in ("b116", "b117"):
        r = kt[key]
        k = dict(title=r["title"], tone=r["tone"], markets={})
        for mk in ("spx", "sensex"):
            rec = r["record"][mk]
            k["markets"][mk] = dict(all=rec["all"], h1=rec["h1"], h2=rec["h2"], big_in=rec.get("big_in"), big_all=rec.get("big_all"),
                                    verdict=kartari_verdict(rec))
        spans = [u for u in r["upcoming"] if u["frm_iso"][:10] <= str(B) and u["to_iso"][:10] >= str(A)]
        k["spans"] = [dict(frm=u["frm"], to=u["to"], pair=u["pair"]) for u in spans]
        kart[key] = k
    kart["b116"]["windows"] = {mk: [dict(start=w["start_local"][:16], end=w["end_local"][:16], pair=w["pair"], sessions=w["sessions"], combust=w["combust"],
                                         benefic=w["benefic"]) for w in kj[mk]["jan"]] for mk in ("spx", "sensex")}
    for mk in ("spx", "sensex"):
        g = kj[mk]["groups"]
        k = kart["b116"]["markets"][mk]
        k["benefic"] = {n: dict(windows=v["windows"], hit=v["hit_rate"], base=v["base_rate"], p=v["p_value"]) for n, v in g.items()
                        if n.startswith(("A benefic", "No benefic", "Like 01 Jan:", "Like 25 Jan"))}
        k["big_test"] = kartari_big(kj[mk]["past"], mk)
        jan_benefic = all(w["benefic"] for w in kj[mk]["jan"])
        bb = k["big_test"]["with a benefic aspect (January's case)"]
        ga = next(v for n, v in g.items() if n.startswith("A benefic"))
        k["january"] = dict(benefic_in_all_windows=jan_benefic,
                            direction=("not supported: a benefic aspects Mercury in every January window, and past windows with a benefic aspect "
                                       f"were right {ga['hit_rate']}% vs {ga['base_rate']}% (p {ga['p_value']})") if jan_benefic else k["verdict"],
                            volatility=("more big days than expected" if (bb["p"] or 1) < 0.05 and (bb["lift"] or 0) > 1 else "no more big days than expected"))
    out["kartari"] = kart

    # ---- the rest
    v1 = collections.Counter(x["v1"]["bias"] for x in days if "gold" in x["prob"])
    out["model_v1"] = dict(bias=dict(v1), record=t["model_v1"]["all"])
    out["solar_return"] = dict(day_calls=dict(collections.Counter((x["sr_call"] or "–").split(":")[0] for x in days if "spx" in x["prob"])),
                               months=list(dict.fromkeys(x["sr_month"] for x in days if x.get("sr_month"))), record=t["solar_return"])
    dds = [json.load(open(f)) for f in sorted(glob.glob(str(OUT / "deep_dive_2027-01-*_ET.json")))]
    out["deep_dive"] = dict(weeks=len(dds), tests=sum(d["n_cells"] for d in dds), significant=sum(len(d["significant"]) for d in dds),
                            nominal=sum(len(d["nominal"]) for d in dds), big=sum(len(d["big_significant"]) for d in dds),
                            checks=f"{sum(c['ok'] for d in dds for c in d['checks'])}/{sum(len(d['checks']) for d in dds)}")
    out["frozen"] = freeze(days, now)
    out["verdicts"] = verdicts(out)
    (OUT / "january_2027_outlook_ET.json").write_text(json.dumps(out, indent=1, default=str))
    for mk, v in out["verdicts"].items():
        print(f"{mk}: {v['summary']}")
        for i in v["items"]:
            print(f"   {i['topic']}: {i['call']} | {i['worth']}")
    print("frozen:", out["frozen"])


def verdicts(o):
    """Per market: every kind of January call, what it says, and what it is worth (items), plus a one-line summary."""
    res = {}
    b116, b117 = o["kartari"]["b116"], o["kartari"]["b117"]
    for mk in MKS:
        m = o["markets"][mk]
        sp = m["spans"]
        L, md = m["label_any"], m["model"]["record"]
        items = [dict(topic="Table labels", call="; ".join(f"{s['sig']} {s['st']} {rng(s['frm'], s['to'])}" for s in sp) or "none",
                      worth=f"out of sample this market's labels were right {L['hit']}% of the time vs {L['exp']}% by chance: leanings, not calls", ok=False)]
        if mk in ("spx", "sensex"):
            rl = {r["title"]: r for s_ in sp for r in s_["rules"]}
            for title, r in rl.items():
                d2 = r["second_half"] or {}
                items.append(dict(topic=f"… {title}", call=f"{r['tone']} ({r['strength']}); table record per span: {r['span_record']}",
                                  worth=f"day by day {r['day']['hit']}% vs {r['day']['exp']}% (2000–2026), {d2.get('hit')}% vs {d2.get('exp')}% after 2013; "
                                        + ("picked" if r["picked_2000_2013"] else "not picked") + " when the rules are chosen on 2000–2013 only", ok=False))
            k = b116["markets"][mk]
            a_, bb = k["all"], k["big_test"]["with a benefic aspect (January's case)"]
            items.append(dict(topic="Mercury in Paap Kartari (B116, 2026 document)",
                              call=f"{', '.join(rng(w['start'], w['end']) for w in b116['windows'][mk])}, bearish; Jupiter aspects Mercury in every window, which B116 reads as "
                                   "“very volatile and both side movement”",
                              worth=f"as a bearish rule in general: {a_['hit_rate']}% vs {a_['base_rate']}% (p {a_['p_value']}; halves {k['h1']['hit_rate']}% vs {k['h1']['base_rate']}% and "
                                    f"{k['h2']['hit_rate']}% vs {k['h2']['base_rate']}%), {k['verdict']}. January's case: direction {k['january']['direction']}; "
                                    f"volatility {bb['big']} big days vs {bb['exp']} expected (×{bb['lift']}, p {bb['p']}): {k['january']['volatility']}", ok=False))
            k = b117["markets"][mk]
            items.append(dict(topic="Jupiter in Paap Kartari (B117, 2026 document)", call=f"to 31 Jan (since 16 Nov), bearish",
                              worth=f"direction {k['verdict']} (2000–2026 {k['all']['hit_rate']}% vs {k['all']['base_rate']}%, second half {k['h2']['hit_rate']}% vs "
                                    f"{k['h2']['base_rate']}%); {k['big_in']}% big days in past windows vs {k['big_all']}% overall, not significant in the earlier test", ok=False))
        lean = m["model"]["lean"]
        items.append(dict(topic="Combined model", call=f"{lean.get('down', 0)} sessions lean down, {lean.get('up', 0)} up, {lean.get('none', 0)} near normal",
                          worth=f"clean walk-forward 2013–2026 {md['hit']}% vs {md['exp']}% by chance: no edge", ok=False))
        if mk == "gold":
            v1 = o["model_v1"]
            items.append(dict(topic="Model v1.0", call=", ".join(f"{k_} {v}" for k_, v in v1["bias"].items()) + " sessions",
                              worth=f"2000–2026 {v1['record']['hit']}% vs {v1['record']['exp']}%: no edge", ok=False))
        if mk == "spx":
            srr = o["solar_return"]
            items.append(dict(topic="Solar return", call="no stated indication in either January solar month (" + "; ".join(x.split(":")[0] for x in srr["months"]) + ")",
                              worth=f"its generated day calls since 1928: bullish {srr['record']['bullish']['hit']}% vs {srr['record']['bullish']['exp']}%, "
                                    f"bearish {srr['record']['bearish']['hit']}% vs {srr['record']['bearish']['exp']}%: no edge", ok=False))
        bg = m["big"]
        items.append(dict(topic="Big days", call=(", ".join(f"{f} on {len(ds)} days" for f, ds in bg["clean_active"].items()) or "no factor that passed the clean test is active")
                          + ("; in sample only: " + ", ".join(f"{f} ({n} days)" for f, n in bg["insample_active"].items()) if bg["insample_active"] else ""),
                          worth="the clean factors are Venus retrograde (S&P, Sensex) and Jupiter–Pluto 5/9 (S&P); the model's big-day chance is untested", ok=bool(bg["clean_active"])))
        res[mk] = dict(items=items, edge=any(i["ok"] for i in items),
                       summary=("No January call has a tested edge" if not any(i["ok"] for i in items) else "Some January calls have a tested edge")
                       + f" on {ON[mk]}: " + ("the bearish labels, the model and Paap Kartari are leanings" if mk in ("spx", "sensex")
                                              else "the bullish labels, the model and Model v1.0 are leanings" if mk == "gold" else "the bullish labels and the model are leanings") + ".")
    return res


if __name__ == "__main__":
    main()
