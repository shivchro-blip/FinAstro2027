"""A coming month after the November review: what each call is worth, and the month's calls frozen for scoring.

    python tools/month_outlook.py [2027-01] [2027-02]      # default: both; after week_deep_dive.py, bigday_clean_test.py, november_review.py

For every kind of call the calendars make for the month it lists the calls and the best evidence there is for that
kind of call, judged the way the November review judged November (against chance for the same up/down mix):
  * S&P / Sensex labels: the rules behind each span; each rule's day-by-day record (2000-2026, in sample); whether the
    choice made on 2000-2013 picks it, and if so its span record after 2013 (the clean test of a single rule, with the
    Benjamini-Hochberg q over the 22 such tests); the clean label record (2013-2026);
  * gold / silver labels: the clean walk-forward label record (2013-2026);
  * the combined model (clean walk-forward), Model v1.0 (2000-2026), Solar return (its day calls since 1928, and the
    record of each Solar return transit rule active in the month);
  * Paap Kartari B116 (Mercury) and B117 (Jupiter), source rules from the 2026 document: their 2000-2026 records in
    both halves, and for B116 the case that applies (with or without a benefic aspect on Mercury, which B116 reads as
    "very volatile and both side movement"), tested on direction and on big days against each year's own rate;
  * big days: the clean factors (tools/bigday_clean_test.py) active in the month, and the in-sample ones;
  * the month's deep dive (every sky event backtested).
It also freezes the month's calls (the day records the November scorer reads) into <month>_<year>_calls_ET.json. The
file is rewritten on every run until the day before the month starts (US Eastern) and never after, so the month can be
scored afterwards exactly as November was.
Writes build/pdfref/<month>_<year>_outlook_ET.json (shown in the 2027 calendar's deep dives; January also in the 2026 calendar).
"""
from __future__ import annotations

import calendar
import collections
import datetime as dt
import glob
import gzip
import importlib.util
import json
import math
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdfref"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
ET, IST = ZoneInfo("America/New_York"), ZoneInfo("Asia/Kolkata")
MKS = ("spx", "sensex", "gold", "silver")
NAME = {"spx": "S&P 500", "sensex": "BSE Sensex", "gold": "Gold", "silver": "Silver"}
SHORT = {"spx": "S&P", "sensex": "Sensex", "gold": "Gold", "silver": "Silver"}
ON = {"spx": "the S&P", "sensex": "the Sensex", "gold": "gold", "silver": "silver"}
TZ = {"spx": ET, "sensex": IST}
HOURS = {"spx": (dt.time(9, 30), dt.time(16, 0)), "sensex": (dt.time(9, 15), dt.time(15, 30))}
CLEAN = {"spx": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
         "sensex": "Model call, clean walk-forward (labels from rules picked on 2000-2013; fitted on 2000-2013)",
         "gold": "Model call (2+ points from normal), all layers", "silver": "Model call (2+ points from normal), all layers"}
KEEP = ("date", "weekday", "closed", "early", "signals", "prob", "tally", "calendar", "v1", "author", "mjn", "sr_call", "sr_month", "vol", "watch")
BEN, NOBEN = "with a benefic aspect", "without a benefic aspect"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def month(key):
    y, m = map(int, key.split("-"))
    a, b = dt.date(y, m, 1), dt.date(y, m, calendar.monthrange(y, m)[1])
    return a, b, f"{a:%B}".lower() + f"_{y}", f"{a:%B}"


def stem_paths(key):
    a, b, stem, mname = month(key)
    return OUT / f"{stem}_outlook_ET.json", OUT / f"{stem}_calls_ET.json"


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


def show_spans(sp):
    """Label spans for reading: neighbours with the same label (over a weekend too) are shown as one."""
    out = []
    for s_ in sp:
        if out and out[-1][0] == s_["sig"] and out[-1][1] == s_["st"] and (dt.date.fromisoformat(s_["frm"]) - dt.date.fromisoformat(out[-1][3])).days <= 3:
            out[-1][3] = s_["to"]
        else:
            out.append([s_["sig"], s_["st"], s_["frm"], s_["to"]])
    return "; ".join(f"{a} {b} {rng(c, d)}".replace(" – ", " ", 1) if b in ("–", "") else f"{a} {b} {rng(c, d)}" for a, b, c, d in out) or "none"


def poisson_sf(k, lam):
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
    MC = load(ROOT / "tools" / "model_check_60d.py", "mc_mo")
    P = MC.prices(mk, dt.date(2026, 11, 20))
    D = sorted(P)
    yr = collections.defaultdict(lambda: [0, 0])
    for i in range(1, len(D)):
        yr[D[i].year][0] += 1
        yr[D[i].year][1] += abs(P[D[i]] / P[D[i - 1]] - 1) >= 0.02
    out = {}
    for name, keep in (("all windows", lambda w: True), (BEN, lambda w: bool(w["benefic"])), (NOBEN, lambda w: not w["benefic"])):
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


def kartari_verdict(rec):
    a, h1, h2 = rec["all"], rec["h1"], rec["h2"]
    return "supported" if a["p_value"] < 0.05 and h1["hit_rate"] > h1["base_rate"] and h2["hit_rate"] > h2["base_rate"] else "not supported"


def freeze(days, now, key):
    """The month's calls as the calendars show them now; never rewritten once the month has begun (US Eastern)."""
    a, b, stem, mname = month(key)
    _, frozen = stem_paths(key)
    if frozen.exists() and now.date() >= a:
        j = json.load(open(frozen))
        return dict(path=frozen.name, frozen_at=j["frozen_at"], rewritten=False, sessions=j["sessions"])
    slim = []
    for x in days:
        y = {k: x.get(k) for k in KEEP}
        y["calendar"] = [dict(market=c["market"], verdict=c["verdict"]) for c in x.get("calendar", [])]
        y["v1"] = dict(bias=x["v1"]["bias"], confidence=x["v1"].get("confidence"))
        y["author"] = dict(rules=x["author"]["rules"], forecasts=x["author"]["forecasts"])
        slim.append(y)
    sessions = {mk: sum(1 for x in days if mk in x["prob"]) for mk in MKS}
    frozen.write_text(json.dumps(dict(frozen_at=now.strftime("%Y-%m-%d %H:%M ET"), month=key, sessions=sessions,
                                      note=f"{mname} {a.year} calls as the calendars showed them; scored after the month with tools/november_review.py's scorer",
                                      days=slim), separators=(",", ":"), default=str))
    return dict(path=frozen.name, frozen_at=now.strftime("%Y-%m-%d %H:%M ET"), rewritten=True, sessions=sessions)


def outlook(key, ctx, now):
    a, b, stem, mname = month(key)
    cache = OUT / "backtest" / f"days_{a}_to_{b}.json.gz"
    if not cache.exists():
        sys.exit(f"run: python tools/week_deep_dive.py {mname[:3].lower()}   (it builds the {mname} day data)")
    days = json.load(gzip.open(cache, "rt", encoding="utf-8"))["days"]
    t, msig, kt, kj, bc, vol_ok, picked, atests, KJ = (ctx[k] for k in ("t", "msig", "kt", "kj", "bc", "vol_ok", "picked", "atests", "KJ"))
    rpd = {(r["id"], r["market"]): r for r in t["rules_per_day"]}
    out = dict(made=now.strftime("%Y-%m-%d %H:%M ET"), month=key, name=f"{mname} {a.year}", start=str(a), end=str(b), markets={},
               picked_summary={k: v for k, v in t["picked_rules"].items() if k != "rules"})

    # ---- labels, model, big days, per market
    for mk in MKS:
        m = dict(name=NAME[mk], sessions=[x["date"] for x in days if mk in x["prob"]],
                 closed=[f"{x['date']} {x['closed'][mk]}" for x in days if mk in x["closed"]])
        lw = t["labels"][mk].get("walk_forward") or t["labels"][mk]
        spans = []
        if mk in ("spx", "sensex"):
            for r in merge([r for r in msig["tables"][mk] if str(r["frm"])[:10] <= str(b) and str(r["to"])[:10] >= str(a)]):
                rules = []
                for rid in r.get("ids") or []:
                    ru = msig["rules"].get(rid, {})
                    pd_, pk = rpd.get((rid, mk)), picked.get(rid)
                    rules.append(dict(id=rid, title=ru.get("title", rid), tone=ru.get("tone"), strength=ru.get("st"), span_record=ru.get("record"),
                                      day=pd_["day"] if pd_ else None, picked_2000_2013=bool(pk), after_2013=(pk or {}).get(mk)))
                spans.append(dict(frm=str(r["frm"])[:10], to=str(r["to"])[:10], sig=r["sig"], st=r["st"], why=r["why"], rules=rules,
                                  strength_record=lw["rows"].get(f"{r['st']}|d1") if r["st"] in ("Low", "Moderate", "High") else None))
        else:
            for r in merge([dict(r, ids=r.get("why")) for r in json.load(open(OUT / f"{mk}_signals_2026-11-22_to_2027-12-31_ET.json"))
                            if str(r["frm"])[:10] <= str(b) and str(r["to"])[:10] >= str(a)]):
                spans.append(dict(frm=str(r["frm"])[:10], to=str(r["to"])[:10], sig=r["sig"], st=r["st"], why=r["why"], rules=[],
                                  strength_record=lw["rows"].get(f"{r['st']}|d1") if r["st"] in ("Low", "Moderate", "High") else None))
        m["spans"], m["label_any"], m["label_source"] = spans, lw["rows"]["Any strength|d1"], lw["source"]
        lean = collections.Counter()
        for x in days:
            pr = x["prob"].get(mk)
            if pr:
                d = pr["all"]["up1"] - pr["base"]["up1"]
                lean["up" if d >= 2 else "down" if d <= -2 else "none"] += 1
        m["model"] = dict(lean=dict(lean), record=t["model"][mk]["rows"][CLEAN[mk]])
        V = load(ROOT / "tools" / "validate_external_model.py", f"vem_{mk}_{key}")
        clean_days, insample = {}, collections.Counter()
        for f in vol_ok.get(mk, []):
            fn = V.ROBUST.get(mk, {}).get(f)
            ds = [str(a + dt.timedelta(days=i)) for i in range((b - a).days + 1) if fn and fn(a + dt.timedelta(days=i))]
            if ds:
                clean_days[f] = ds
        for x in days:
            for f in x["vol"].get(mk, []) or []:
                if f not in vol_ok.get(mk, []):
                    insample[f] += 1
        m["big"] = dict(clean_active=clean_days, insample_active=dict(insample), clean_test=bc[mk]["verdict"], model_big="untested (November review)")
        out["markets"][mk] = m

    # ---- Paap Kartari windows in the month (records on the S&P and Sensex)
    kart = {}
    for keyk in ("b116", "b117"):
        r = kt[keyk]
        k = dict(title=r["title"], tone=r["tone"], markets={}, windows=[])
        for mk in ("spx", "sensex"):
            rec = r["record"][mk]
            k["markets"][mk] = dict(all=rec["all"], h1=rec["h1"], h2=rec["h2"], big_in=rec.get("big_in"), big_all=rec.get("big_all"), verdict=kartari_verdict(rec))
        for u in r["upcoming"]:
            s0, s1 = dt.datetime.fromisoformat(u["frm_iso"]), dt.datetime.fromisoformat(u["to_iso"])
            if s0.date() > b + dt.timedelta(days=1) or s1.date() < a - dt.timedelta(days=1):
                continue
            c = KJ.conditions(s0)
            w = dict(frm=u["frm"], to=u["to"], pair=u["pair"], sign=c["sign"], combust=c["combust"], benefic=c["benefic"], local={})
            for mk, tz in TZ.items():
                l0, l1 = s0.astimezone(tz), s1.astimezone(tz)
                op, cl = HOURS[mk]
                ses = [x["date"] for x in days if mk in x["prob"]
                       and l0 <= dt.datetime.combine(dt.date.fromisoformat(x["date"]), cl, tz) and l1 >= dt.datetime.combine(dt.date.fromisoformat(x["date"]), op, tz)]
                w["local"][mk] = dict(start=l0.strftime("%Y-%m-%d %H:%M"), end=l1.strftime("%Y-%m-%d %H:%M"), sessions=ses)
            if any(w["local"][mk]["sessions"] for mk in TZ):
                k["windows"].append(w)
        kart[keyk] = k
    for mk in ("spx", "sensex"):
        g = kj[mk]["groups"]
        k = kart["b116"]["markets"][mk]
        k["groups"] = {n: dict(windows=v["windows"], hit=v["hit_rate"], base=v["base_rate"], p=v["p_value"]) for n, v in g.items()
                       if n.startswith(("All B116", "A benefic", "No benefic"))}
        k["big_test"] = kartari_big(kj[mk]["past"], mk)
        cases = []
        for w in kart["b116"]["windows"]:
            ben = bool(w["benefic"])
            gr = next(v for n, v in g.items() if n.startswith("A benefic" if ben else "No benefic"))
            bt = k["big_test"][BEN if ben else NOBEN]
            cases.append(dict(window=rng(w["local"][mk]["start"], w["local"][mk]["end"]), benefic=w["benefic"], case=BEN if ben else NOBEN,
                              direction=dict(hit=gr["hit_rate"], base=gr["base_rate"], p=gr["p_value"],
                                             ok=gr["p_value"] < 0.05 and gr["hit_rate"] > gr["base_rate"]),
                              volatility=dict(**bt, ok=(bt["p"] or 1) < 0.05 and (bt["lift"] or 0) > 1)))
        k["cases"] = cases
    out["kartari"] = kart

    # ---- the rest
    v1 = collections.Counter(x["v1"]["bias"] for x in days if "gold" in x["prob"])
    out["model_v1"] = dict(bias=dict(v1), record=t["model_v1"]["all"])
    sr_rules = collections.Counter(r for x in days if "spx" in x["prob"] for r in x["author"]["rules"])
    out["solar_return"] = dict(day_calls=dict(collections.Counter((x["sr_call"] or "–").split(":")[0] for x in days if "spx" in x["prob"])),
                               months=list(dict.fromkeys(x["sr_month"] for x in days if x.get("sr_month"))), record=t["solar_return"],
                               rules=[dict(rule=rname, sessions=n, record=atests.get(rname)) for rname, n in sr_rules.items()])
    dds = [json.load(open(f)) for f in sorted(glob.glob(str(OUT / f"deep_dive_{key}-*_ET.json")))]
    out["deep_dive"] = dict(weeks=len(dds), tests=sum(d["n_cells"] for d in dds), significant=sum(len(d["significant"]) for d in dds),
                            nominal=sum(len(d["nominal"]) for d in dds), big=sum(len(d["big_significant"]) for d in dds),
                            checks=f"{sum(c['ok'] for d in dds for c in d['checks'])}/{sum(len(d['checks']) for d in dds)}")
    out["frozen"] = freeze(days, now, key)
    out["verdicts"] = verdicts(out, mname)
    out["headline"] = headline(out, mname)
    path, _ = stem_paths(key)
    path.write_text(json.dumps(out, indent=1, default=str))
    return out


def rule_item(r, mk, ps):
    d, af = r["day"] or {}, r["after_2013"]
    if r["picked_2000_2013"] and af:
        h = af["h2"]
        clean = (f"picked when the rules are chosen on 2000–2013 only; its span record after 2013: {h['hit']}% vs {h['base']}% (p {h['p']}, q {h.get('q')}): {af['verdict']}")
        level = "some" if af["verdict"] == "held after 2013" else "none"
    else:
        clean, level = "not picked when the rules are chosen on 2000–2013 only, so it has no clean test", "none"
    why = (f"picked on 2000–2013, it held after 2013 ({af['h2']['hit']}% vs {af['h2']['base']}%, p {af['h2']['p']}), but not once all "
           f"{ps['n_tests']} such tests are counted (q {af['h2'].get('q')})") if level == "some" else None
    return dict(topic=f"… {r['title']}", call=f"{r['tone']} ({r['strength']}); table record per span: {r['span_record']}",
                worth=f"day by day {d.get('hit')}% vs {d.get('exp')}% (2000–2026, in sample); {clean}", level=level, why=why)


def verdicts(o, mname):
    """Per market: every kind of call in the month, what it says, what it is worth, and how strong the evidence is
    (level: edge = passes a clean test after correction; some = passes a clean test, not after correction; none)."""
    res = {}
    ps = o["picked_summary"]
    b116, b117 = o["kartari"]["b116"], o["kartari"]["b117"]
    for mk in MKS:
        m = o["markets"][mk]
        sp = m["spans"]
        L, md = m["label_any"], m["model"]["record"]
        items = [dict(topic="Table labels", call=show_spans(sp),
                      worth=f"out of sample this market's labels were right {L['hit']}% of the time vs {L['exp']}% by chance: leanings, not calls", level="none")]
        if mk in ("spx", "sensex"):
            seen = {}
            for s_ in sp:
                for r in s_["rules"]:
                    seen.setdefault(r["title"], r)
            items += [rule_item(r, mk, ps) for r in seen.values()]
            k = b116["markets"][mk]
            for c in k["cases"]:
                dr, vo = c["direction"], c["volatility"]
                ok = dr["hit"] > dr["base"] and dr["p"] < 0.05
                items.append(dict(topic="Mercury in Paap Kartari (B116, 2026 document)", why=(
                    f"past windows {c['case']}, B116's own case for this window, were bearish {dr['hit']}% vs {dr['base']}% (p {dr['p']}), "
                    "a 2000–2026 record of a source rule rather than a walk-forward test") if ok else None,
                                  call=f"{c['window']}, bearish; " + (f"{', '.join(c['benefic'])} aspects Mercury, which B116 reads as “very volatile and both side movement”"
                                                                      if c["benefic"] else "no benefic aspects Mercury, so B116 reads it as a negative event"),
                                  worth=f"as a bearish rule overall {k['all']['hit_rate']}% vs {k['all']['base_rate']}% (p {k['all']['p_value']}; halves {k['h1']['hit_rate']}% vs "
                                        f"{k['h1']['base_rate']}% and {k['h2']['hit_rate']}% vs {k['h2']['base_rate']}%), {k['verdict']}. Windows {c['case']}: bearish right "
                                        f"{dr['hit']}% vs {dr['base']}% (p {dr['p']}); big days {vo['big']} vs {vo['exp']} expected (×{vo['lift']}, p {vo['p']}). The 2000–2026 "
                                        "record is a source rule's, not chosen from data, but it is not a walk-forward test",
                                  level="some" if ok else "none"))
            if b117["windows"]:
                k = b117["markets"][mk]
                items.append(dict(topic="Jupiter in Paap Kartari (B117, 2026 document)",
                                  call="; ".join(f"{w['frm']} – {w['to']}" for w in b117["windows"]) + ", bearish",
                                  worth=f"direction {k['verdict']} (2000–2026 {k['all']['hit_rate']}% vs {k['all']['base_rate']}%, second half {k['h2']['hit_rate']}% vs "
                                        f"{k['h2']['base_rate']}%); {k['big_in']}% big days in past windows vs {k['big_all']}% overall, not significant in the earlier test", level="none"))
        lean = m["model"]["lean"]
        items.append(dict(topic="Combined model", call=f"{lean.get('down', 0)} sessions lean down, {lean.get('up', 0)} up, {lean.get('none', 0)} near normal",
                          worth=f"clean walk-forward 2013–2026 {md['hit']}% vs {md['exp']}% by chance: no edge", level="none"))
        if mk == "gold":
            v1 = o["model_v1"]
            items.append(dict(topic="Model v1.0", call=", ".join(f"{k_} {v}" for k_, v in v1["bias"].items()) + " sessions",
                              worth=f"2000–2026 {v1['record']['hit']}% vs {v1['record']['exp']}%: no edge", level="none"))
        if mk == "spx":
            srr = o["solar_return"]
            dc = srr["day_calls"]
            rules = "; ".join(f"{r['rule'].split(' – ')[0]} ({r['sessions']} sessions" + (
                f": since 1928 big days {r['record']['big']} vs {r['record']['exp_big']} expected (p {r['record']['p_big']}), up over 5 sessions "
                f"{r['record']['eps_up5']}% vs {r['record']['eps_exp5']}% (p {r['record']['eps_p']}))"
                if r.get("record") else ")") for r in srr["rules"])
            items.append(dict(topic="Solar return", call="day calls " + ", ".join(f"{k_} {v}" for k_, v in dc.items()) + " sessions; solar months: "
                              + "; ".join(x.replace("Solar month ", "") for x in srr["months"]) + (f"; transit rules: {rules}" if rules else ""),
                              worth=f"its generated day calls since 1928: bullish {srr['record']['bullish']['hit']}% vs {srr['record']['bullish']['exp']}%, "
                                    f"bearish {srr['record']['bearish']['hit']}% vs {srr['record']['bearish']['exp']}%: no edge", level="none"))
        bg = m["big"]
        items.append(dict(topic="Big days", call=(", ".join(f"{f} on {len(ds)} days" for f, ds in bg["clean_active"].items()) or "no factor that passed the clean test is active")
                          + ("; in sample only: " + ", ".join(f"{f} ({n} days)" for f, n in bg["insample_active"].items()) if bg["insample_active"] else ""),
                          worth="the clean factors are Venus retrograde (S&P, Sensex) and Jupiter–Pluto 5/9 (S&P); the model's big-day chance is untested",
                          level="some" if bg["clean_active"] else "none"))
        best = [i for i in items if i["level"] in ("edge", "some")]
        if best:
            body = "; ".join(f"{i['topic'].lstrip('… ')}: {i['why']}" for i in best if i.get("why"))
            summary = (f"{mname} calls on {ON[mk]} with some support. {body}. Neither is proven; everything else is a leaning." if len(best) > 1 else
                       f"{mname}'s best-supported call on {ON[mk]}. {body}. Everything else is a leaning.")
        else:
            summary = f"No {mname} call has a tested edge on {ON[mk]}: " + ("the labels, the model and Paap Kartari are leanings." if mk in ("spx", "sensex")
                                                                         else "the labels, the model and Model v1.0 are leanings." if mk == "gold" else "the labels and the model are leanings.")
        res[mk] = dict(items=items, edge=any(i["level"] == "edge" for i in items), some=bool(best), summary=summary)
    return res


def headline(o, mname):
    v = o["verdicts"]
    ps = o["picked_summary"]
    some = [mk for mk in MKS if v[mk]["some"]]
    held = ps.get("held_both") or []
    txt = []
    if not some:
        txt.append(f"No {mname} call has a tested edge on any market.")
    else:
        by = collections.OrderedDict()
        for mk in some:
            for i in v[mk]["items"]:
                if i["level"] in ("edge", "some"):
                    by.setdefault(i["topic"].lstrip("… ").replace(", 2026 document", ""), []).append(SHORT[mk])
        txt.append(f"{mname} calls with some support: " + "; ".join(f"{k} ({' and '.join(m)})" for k, m in by.items()) + ".")
        if any(k in held for k in by):
            txt.append(f"When the table's rules are chosen on 2000–2013 only, {ps['held']} of {ps['n_tests']} rule-and-index tests held after 2013 "
                       f"({', '.join(held)} on both indices); about {round(ps['n_tests'] * 0.05, 1)} would by chance, so that is the best-supported table rule, not a proven one.")
        if any(k.startswith("Mercury in Paap Kartari") for k in by):
            txt.append("Mercury in Paap Kartari is a source rule; its record for this window's case (no benefic aspect) is bearish on the Sensex, but it is a 2000–2026 record, "
                       "not a walk-forward test.")
    txt.append("Out of sample the table labels as a whole and the combined model score what chance gives; treat the rest as leanings.")
    return " ".join(txt)


def main():
    keys = [k for k in sys.argv[1:] if not k.startswith("--")] or ["2027-01", "2027-02"]
    now = dt.datetime.now(ET)
    nov = json.load(open(OUT / "november_review_2026-11_ET.json"))
    t = nov["tuning"]
    ctx = dict(t=t, msig=json.load(open(OUT / "market_signals_2026-11-23_to_2027-12-31_ET.json")),
               kt={r["key"]: r for r in json.load(open(OUT / "kartari_test_ET.json"))["rules"]},
               kj=json.load(open(OUT / "kartari_jan2027_ET.json"))["markets"],
               bc=json.load(open(OUT / "bigday_clean_test_ET.json"))["markets"],
               vol_ok=next((r.get("vol_ok") for r in nov["recommendations"] if r["id"] == "big_days"), None) or {},
               picked={r["id"]: r for r in t["picked_rules"]["rules"]},
               atests=json.load(open(OUT / "author_forecasts_ET.json"))["tests"],
               KJ=load(ROOT / "tools" / "kartari_jan2027.py", "kj_mo"))
    for key in keys:
        o = outlook(key, ctx, now)
        print(f"== {o['name']}: {o['headline']}")
        for mk, v in o["verdicts"].items():
            print(f"{mk}: {v['summary']}")
            for i in v["items"]:
                print(f"   [{i['level']}] {i['topic']}: {i['call']} | {i['worth']}")
        print("frozen:", o["frozen"])


if __name__ == "__main__":
    main()
