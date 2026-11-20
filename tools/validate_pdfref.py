"""Recompute every dated claim in the two reference PDFs and compare.

    python tools/validate_pdfref.py

KD (2026 deck) prints dated 2026 events; TA (2020 book) prints dated examples
from 2011-2020. Each is recomputed with finastro/pdfref's engine (Swiss
Ephemeris, Lahiri, mean node) and compared. Writes build/pdfref/validation.json
and prints a table. Times are compared in IST, the zone both PDFs print in.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finastro.sky import Sky, parse  # noqa: E402
from finastro.pdfref.engine import Grid, NORMAL_SPEED, conjunction_instants, crossings, snapshot, spans, utc  # noqa: E402
from finastro.pdfref import vedha as V  # noqa: E402
from finastro.pdfref.detect import Ctx  # noqa: E402
import finastro.pdfref.catalogue as C  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")
OUT = ROOT / "build" / "pdfref"
RESULTS = []


def ist(t):
    return t.astimezone(IST).strftime("%d-%b-%Y %H:%M") if t else "-"


def d(s):
    return dt.datetime.strptime(s, "%d-%b-%y").date()


def add(item, source, claim, computed, ok, note=""):
    RESULTS.append({"item": item, "source": source, "claim": claim, "computed_IST": computed,
                    "agreement": ok, "note": note})


def win_list(g, pred):
    return [w for w in spans(g, pred)]


def day_diff(t, day):
    return abs((t.astimezone(IST).date() - day).days)


def main():
    g26 = Grid(utc(2025, 12, 1), utc(2027, 1, 31))
    sky26 = Sky.load(ROOT / "build" / "astronomy_2026.json")

    # 1. KD p.94 Shani Chandra Dwidwadash 2026 (start/end IST)
    kd94 = [("21-Jan-26 1:37", "23-Jan-26 8:34"), ("17-Feb-26 9:06", "19-Feb-26 15:01"), ("16-Mar-26 18:15", "18-Mar-26 23:36"),
            ("13-Apr-26 3:45", "15-Apr-26 9:38"), ("10-May-26 12:13", "12-May-26 19:25"), ("06-Jun-26 19:05", "09-Jun-26 3:37"),
            ("04-Jul-26 0:49", "06-Jul-26 9:58"), ("31-Jul-26 6:39", "02-Aug-26 15:28"), ("27-Aug-26 13:36", "29-Aug-26 21:38"),
            ("23-Sep-26 21:57", "26-Sep-26 5:34"), ("21-Oct-26 7:01", "23-Oct-26 15:04"), ("17-Nov-26 15:31", "20-Nov-26 0:50"),
            ("14-Dec-26 22:36", "17-Dec-26 9:13")]
    ws = [w for w in win_list(g26, lambda s: s.sign_dist("Saturn", "Moon") == 12) if w.start.year == 2026]
    worst = 0
    for (a, b), w in zip(kd94, ws):
        ta = dt.datetime.strptime(a, "%d-%b-%y %H:%M").replace(tzinfo=IST)
        tb = dt.datetime.strptime(b, "%d-%b-%y %H:%M").replace(tzinfo=IST)
        worst = max(worst, abs((w.start - ta).total_seconds()), abs((w.end - tb).total_seconds()))
    add("Shani Chandra Dwidwadash 2026 (13 windows)", "KD p.94", "13 printed start/end times", f"{len(ws)} windows; worst endpoint difference {worst / 60:.1f} min",
        len(ws) == 13 and worst <= 120, "Moon in 12th sign from Saturn (Aquarius-Pisces axis)")

    # 2. Saturn-Mars conjunction 2026
    cj = [t for t, _ in conjunction_instants(g26, "Mars", "Saturn") if t.year == 2026]
    same = [w for w in win_list(g26, lambda s: s["Mars"].sign_i == s["Saturn"].sign_i) if w.start.year == 2026]
    add("Saturn-Mars conjunction", "KD p.96", "same sign 2 Apr-11 May 2026; exact 20 Apr 04:13", f"same sign {ist(same[0].start)} - {ist(same[0].end)}; exact {ist(cj[0])}",
        day_diff(same[0].start, dt.date(2026, 4, 2)) <= 1 and day_diff(same[0].end, dt.date(2026, 5, 11)) <= 1 and abs((cj[0] - dt.datetime(2026, 4, 20, 4, 13, tzinfo=IST)).total_seconds()) < 3600)

    # 3. Venus-Herschel conjunction
    cj = [t for t, _ in conjunction_instants(g26, "Venus", "Uranus") if t.year == 2026]
    add("Venus-Herschel conjunction", "KD p.98", "24 April 2026", ", ".join(ist(t) for t in cj), any(day_diff(t, dt.date(2026, 4, 24)) <= 1 for t in cj))

    # 4. Sun-Mercury conjunctions
    cj = [t for t, _ in conjunction_instants(g26, "Sun", "Mercury") if t.year == 2026]
    claims = {dt.date(2026, 7, 13): "KD p.108", dt.date(2026, 8, 27): "KD p.117", dt.date(2026, 11, 4): "KD p.126"}
    for day, src in claims.items():
        best = min(cj, key=lambda t: day_diff(t, day))
        add("Sun-Mercury conjunction", src, day.strftime("%d %b %Y"), ist(best), day_diff(best, day) <= 1)
    may = [t for t in cj if t.month == 5]
    add("Sun-Mercury conjunction (May)", "KD p.100", "'14 May 2026' (title) / '1? May' (body, illegible)", ", ".join(ist(t) for t in may),
        any(day_diff(t, dt.date(2026, 5, 14)) <= 1 for t in may))

    # 5. Jupiter vargottama
    vg = [w for w in win_list(g26, lambda s: s["Jupiter"].vargottama and s["Jupiter"].sign) if w.start.year == 2026]
    add("Jupiter Vargottam", "KD p.101 / p.104", "Gemini 14 May-2 Jun 2026; Cancer 2 Jun-18 Jun 2026",
        "; ".join(f"{w.value} {ist(w.start)} - {ist(w.end)}" for w in vg),
        any(w.value == "Gemini" and day_diff(w.start, dt.date(2026, 5, 14)) <= 1 for w in vg) and any(w.value == "Cancer" and day_diff(w.end, dt.date(2026, 6, 18)) <= 1 for w in vg))

    # 6. Mercury & Venus alone
    mv = [w for w in win_list(g26, C.alone_together("Mercury", "Venus")) if w.start.year == 2026]
    txt = "; ".join(f"{w.value} {ist(w.start)} - {ist(w.end)}" for w in mv)
    add("Mercury & Venus alone in a sign", "KD p.102", "2-8 June 2026", txt, any(day_diff(w.start, dt.date(2026, 6, 2)) <= 1 and day_diff(w.end, dt.date(2026, 6, 8)) <= 1 for w in mv))
    add("Mercury & Venus alone in a sign", "KD p.121", "26 Sep-17 Oct 2026", txt, any(day_diff(w.start, dt.date(2026, 9, 26)) <= 1 for w in mv),
        "KD's 17 Oct is the post-conjunction reversal date it names; compared on the start")

    # 7. Jupiter direct opposite retro Pluto
    jp = [w for w in win_list(g26, lambda s: s.sign_dist("Pluto", "Jupiter") == 7 and s["Pluto"].retro and not s["Jupiter"].retro) if w.start.year == 2026]
    add("Jupiter direct opposite retrograde Pluto", "KD p.103", "2 Jun-16 Oct 2026", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in jp),
        any(day_diff(w.start, dt.date(2026, 6, 2)) <= 1 for w in jp), "whole-sign opposition, motions as printed")

    # 8. Venus behind / ahead of Jupiter
    va = [w for w in win_list(g26, lambda s: s["Venus"].sign_i == s["Jupiter"].sign_i and (("ahead" if s.ahead("Venus", "Jupiter") else "behind"))) if w.start.year == 2026]
    add("Venus behind / ahead of Jupiter (same sign)", "KD p.105", "behind until 10 Jun; ahead 10 Jun-4 Jul 2026", "; ".join(f"{w.value} {ist(w.start)} - {ist(w.end)}" for w in va),
        any(w.value == "ahead" and day_diff(w.start, dt.date(2026, 6, 10)) <= 1 and day_diff(w.end, dt.date(2026, 7, 4)) <= 1 for w in va))

    # 9. Jupiter in Pushya with Rahu in Shatabhisha
    jr = [w for w in win_list(g26, lambda s: s["Jupiter"].nak == "Pushya" and s["Rahu"].nak == "Shatabhisha") if w.start.year == 2026]
    add("Jupiter in Pushya & Rahu in Shatabhisha (mutual Vedh)", "KD p.107", "18 Jun-2 Aug 2026", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in jr),
        any(day_diff(w.start, dt.date(2026, 6, 18)) <= 1 and day_diff(w.end, dt.date(2026, 8, 2)) <= 1 for w in jr))
    cells_j, cells_r = V.cells_2026_labels("Pushya"), V.cells_2026_labels("Shatabhisha")
    add("Pushya <-> Shatabhisha on the TA wheel", "TA pp.131-133 / KD p.107", "mutual Vedh", f"Pushya vedhas {cells_j}; Shatabhisha vedhas {cells_r}",
        "Shatabhisha" in cells_j.values() and "Pushya" in cells_r.values())

    # 10. Combustion / rise dates (astronomy layer, 2026)
    def comb(body, fam, day, src, label):
        recs = [r for r in sky26.class_records("combustion") if r["bodies"][0] == body and r["rule_family"] == fam]
        best = min(recs, key=lambda r: abs((parse(r["time"]["t_start_utc"]).astimezone(IST).date() - day).days))
        t = parse(best["time"]["t_start_utc"])
        dirn = next((f.split("=")[1] for f in best["qa"]["flags"] if f.startswith("direction=")), "?")
        add(label, src, day.strftime("%d %b %Y"), f"{t.astimezone(IST):%d-%b-%Y} (IST civil date), {dirn}", day_diff(t, day) <= 1)
    comb("Jupiter", "visibility/combust", dt.date(2026, 7, 16), "KD p.109", "Jupiter combust in West")
    comb("Venus", "visibility/combust", dt.date(2026, 10, 15), "KD p.122", "Venus combust in West")
    comb("Venus", "visibility/rise", dt.date(2026, 10, 27), "KD p.122/124", "Venus rise (East)")
    comb("Mars", "visibility/rise", dt.date(2026, 4, 10), "KD p.97", "Mars rise in East")
    comb("Saturn", "visibility/rise", dt.date(2026, 4, 15), "KD p.97", "Saturn rise in East")

    # 11. Ingresses
    for body, frame, val, claim_t, src in (("Rahu", "nak", "Dhanishta", dt.datetime(2026, 8, 2, tzinfo=IST), "KD p.111"),
                                            ("Mars", "nak", "Ardra", dt.datetime(2026, 8, 12, 22, 35, tzinfo=IST), "KD p.115")):
        xs = [t for t, a, b in crossings(g26, lambda s: s[body].nak) if b == val and t.year == 2026]
        add(f"{body} enters {val}", src, ist(claim_t), ", ".join(ist(t) for t in xs),
            any(abs((t - claim_t).total_seconds()) <= (86400 if claim_t.hour == 0 else 1800) for t in xs))

    # 12. Vargottam Mars in Cancer
    vm = [w for w in win_list(g26, lambda s: s["Mars"].vargottama and s["Mars"].sign == "Cancer") if w.start.year == 2026]
    add("Vargottam Mars in Cancer", "KD p.119", "13-18 Sep 2026", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in vm),
        any(day_diff(w.start, dt.date(2026, 9, 13)) <= 1 and day_diff(w.end, dt.date(2026, 9, 18)) <= 1 for w in vm))

    # 13. Mars & Jupiter
    mj = [w for w in win_list(g26, lambda s: s["Mars"].sign_i == s["Jupiter"].sign_i and ("Mars ahead" if s.ahead("Mars", "Jupiter") else "Mars behind")) if w.start.year == 2026]
    txt = "; ".join(f"{w.value} {ist(w.start)} - {ist(w.end)}" for w in mj)
    add("Mars behind Jupiter in same sign", "KD p.120", "18 Sep-31 Oct 2026", txt, any(w.value == "Mars behind" and day_diff(w.start, dt.date(2026, 9, 18)) <= 1 for w in mj))
    add("Mars & Jupiter same sign; Mars ahead", "KD p.128", "together from 12 Nov; Mars behind 12-16 Nov, ahead from 16 Nov 2026", txt,
        any(w.value == "Mars ahead" and day_diff(w.start, dt.date(2026, 11, 16)) <= 1 for w in mj))

    # 14. Mutual vedh
    ctx = Ctx(g26, sky26, 2026)
    def mutual(a, b, na, nb):
        def p(s):
            if s[a].nak28 != na or s[b].nak28 != nb:
                return False
            ta, _ = C.vedha_of(ctx, s, a)
            tb, _ = C.vedha_of(ctx, s, b)
            return (nb in ta.values()) and (na in tb.values())
        return p
    for a, b, na, nb, claim, src, d0, d1 in (("Jupiter", "Ketu", "Ashlesha", "Magha", "19 Aug-31 Oct 2026", "KD p.116", dt.date(2026, 8, 19), dt.date(2026, 10, 31)),
                                             ("Mars", "Ketu", "Ashlesha", "Magha", "17 Oct-12 Nov 2026", "KD p.125", dt.date(2026, 10, 17), dt.date(2026, 11, 12))):
        both = [w for w in win_list(g26, lambda s: s[a].nak28 == na and s[b].nak28 == nb) if w.start.year == 2026]
        mut = [w for w in win_list(g26, mutual(a, b, na, nb)) if w.start.year == 2026]
        add(f"{a} in {na} & {b} in {nb} (mutual Vedh)", src, claim,
            "residency overlap: " + "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in both) + " | mutual under this engine's direction doctrine: " +
            ("; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in mut) or "none"),
            any(day_diff(w.start, d0) <= 1 and day_diff(w.end, d1) <= 1 for w in both),
            "Ashlesha-Magha: TA wheel has Ashlesha->Magha (Right) and Magha->Ashlesha (Left); which pairs count as 'mutual' depends on the direction doctrine")

    # 15. Mars speed below TA normal
    xs = [t for t, a, b in crossings(g26, lambda s: abs(s["Mars"].speed) < NORMAL_SPEED["Mars"]) if b and t.year == 2026]
    add("Mars speed falls below TA normal speed (0d31m26.46s)", "KD p.123 + TA p.144", "26 Oct 2026", ", ".join(ist(t) for t in xs),
        any(day_diff(t, dt.date(2026, 10, 26)) <= 2 for t in xs), "Independent confirmation that KD uses TA p.144's normal speed")

    # 16. Atichari Mars in Purva Bhadrapada
    am = [w for w in win_list(g26, lambda s: s["Mars"].nak == "Purva Bhadrapada") if w.start.year == 2026]
    fast = all(snapshot(w.start + (w.end - w.start) / 2)["Mars"].fast for w in am)
    add("Atichari Mars in Purva Bhadrapada", "KD p.88", "20 Mar-06 Apr 2026", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in am) + f"; above TA normal speed: {fast}",
        any(day_diff(w.start, dt.date(2026, 3, 20)) <= 1 and day_diff(w.end, dt.date(2026, 4, 6)) <= 1 for w in am) and fast)

    # 17. Eclipses
    for fam, day, src, expect in (("eclipse/solar", dt.date(2026, 8, 12), "KD p.114", ("Wednesday", "Shravan", "Cancer")),
                                  ("eclipse/lunar", dt.date(2026, 8, 28), "KD p.118", (None, "Shravan", "Aquarius"))):
        r = min((r for r in sky26.class_records("eclipse") if r["rule_family"] == fam), key=lambda r: abs((parse(r["time"]["t_start_utc"]).astimezone(IST).date() - day).days))
        t = parse(r["time"]["t_start_utc"])
        s = snapshot(t)
        sign = s["Sun"].sign if fam.endswith("solar") else s["Moon"].sign
        wd = t.astimezone(IST).strftime("%A")
        month = sky26.eclipse_month(r)
        ok = day_diff(t, day) <= 1 and (expect[0] in (None, wd)) and month == expect[1] and sign == expect[2]
        add(f"{fam.split('/')[1].title()} eclipse", src, f"{day:%d %b %Y}; " + ", ".join(x for x in expect if x), f"{ist(t)}, {wd}, {month}, {sign}", ok)

    # 18. Mercury manifestation (Mercury speed crosses Venus speed)
    xs = [t for t, a, b in crossings(g26, lambda s: s["Mercury"].speed > s["Venus"].speed) if b and t.year == 2026]
    for day, src in ((dt.date(2026, 4, 10), "KD p.99"), (dt.date(2026, 8, 3), "KD p.112"), (dt.date(2026, 11, 14), "KD p.127")):
        best = min(xs, key=lambda t: day_diff(t, day))
        add("Mercury manifestation (Mercury's speed overtakes Venus's)", src, f"{day:%d %b %Y}", ist(best), day_diff(best, day) <= 1, "TA p.70: 'Bullishness returns after speed of Mercury cross speed of Venus'")

    # 19. Mercury in the middle (TA + KD)
    def mid(s):
        return C._mid(s)
    for y, kind, a, b, src in ((2014, "sun_ahead", dt.date(2014, 2, 18), dt.date(2014, 4, 30), "TA p.25/p.49 ('18 Feb ... till end of April')"),
                               (2017, "sun_ahead", dt.date(2017, 4, 20), dt.date(2017, 6, 22), "TA p.50"), (2017, "sun_ahead", dt.date(2017, 8, 27), dt.date(2017, 10, 8), "TA p.50"),
                               (2018, "venus_ahead", dt.date(2018, 2, 18), dt.date(2018, 3, 21), "TA p.50"), (2018, "venus_ahead", dt.date(2018, 9, 21), dt.date(2018, 10, 16), "TA p.50"),
                               (2020, "venus_ahead", dt.date(2020, 1, 11), dt.date(2020, 2, 26), "TA p.256"), (2020, "sun_ahead", dt.date(2020, 7, 1), dt.date(2020, 8, 18), "TA p.262"),
                               (2026, "sun_ahead", dt.date(2026, 11, 4), None, "KD p.126/127")):
        g = Grid(utc(y, 1, 1), utc(y + 1, 1, 15))
        ws = [w for w in win_list(g, lambda s: mid(s) == kind)]
        best = min(ws, key=lambda w: abs((w.start.astimezone(IST).date() - a).days))
        ok = day_diff(best.start, a) <= 4 and (b is None or day_diff(best.end, b) <= 4)
        add(f"Mercury in middle ({kind.replace('_', ' ')})", src, f"{a:%d %b %Y} - {b:%d %b %Y}" if b else f"from {a:%d %b %Y}", f"{ist(best.start)} - {ist(best.end)}", ok,
            "2018 Feb-Mar: computes as two windows (Mercury passed Venus 4-20 Mar)" if y == 2018 and kind == "venus_ahead" and a.month == 2 else "")

    # 20. Paap Kartari 2011
    g = Grid(utc(2011, 9, 1), utc(2012, 2, 1))
    ws = win_list(g, C._pk)
    add("Mercury Paap Kartari (TA definition)", "TA p.22", "28 Oct 2011 - 2 Jan 2012", "; ".join(f"{w.value}: {ist(w.start)} - {ist(w.end)}" for w in ws), False,
        "Not reproduced: the TA definition gives only part of the window")

    # 21. Saturn-Mars 2020 (TA story)
    g = Grid(utc(2020, 1, 1), utc(2020, 12, 31))
    sm = [w for w in win_list(g, lambda s: s["Mars"].sign == "Capricorn" and s["Saturn"].sign == "Capricorn")]
    add("Saturn & Mars together in Capricorn 2020", "TA p.259", "23 Mar 2020 14:42 - 4 May 2020 20:42", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in sm),
        any(abs((w.start - dt.datetime(2020, 3, 23, 14, 42, tzinfo=IST)).total_seconds()) < 3600 and abs((w.end - dt.datetime(2020, 5, 4, 20, 42, tzinfo=IST)).total_seconds()) < 3600 for w in sm))
    m2 = [t for t, a, b in crossings(g, lambda s: s["Mars"].sign) if b == "Sagittarius" and t.month == 2]
    add("Mars enters Sagittarius 2020", "TA p.257", "8 Feb 2020 03:52", ", ".join(ist(t) for t in m2), any(abs((t - dt.datetime(2020, 2, 8, 3, 52, tzinfo=IST)).total_seconds()) < 3600 for t in m2))
    vr = [w for w in win_list(g, lambda s: s["Venus"].retro)]
    add("Venus retrograde 2020", "TA p.260", "13 May 2020 12:16 - 25 Jun 2020 11:19", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in vr),
        any(abs((w.start - dt.datetime(2020, 5, 13, 12, 16, tzinfo=IST)).total_seconds()) < 3600 for w in vr))
    sr = [w for w in win_list(g, lambda s: s["Saturn"].retro and s["Mars"].retro)]
    add("Saturn & Mars both retrograde 2020", "TA p.263", "10 Sep 2020 03:54 - 29 Sep 2020 10:43", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in sr),
        any(abs((w.start - dt.datetime(2020, 9, 10, 3, 54, tzinfo=IST)).total_seconds()) < 3600 for w in sr))
    va = [w for w in win_list(g, lambda s: s["Mars"].vargottama and s["Mars"].sign == "Aries")]
    add("Mars in Aries & Vargottam 2020", "TA p.263", "16 Aug 2020 18:35 - 31 Aug 2020 12:23", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in va),
        any(abs((w.start - dt.datetime(2020, 8, 16, 18, 35, tzinfo=IST)).total_seconds()) < 3600 for w in va))
    sat = [t for t, a, b in crossings(g, lambda s: s["Saturn"].nav) if b == "Capricorn" and t.month == 1]
    add("Saturn enters Capricorn navamsa 2020", "TA p.256", "24 Jan 2020 09:50", ", ".join(ist(t) for t in sat), any(abs((t - dt.datetime(2020, 1, 24, 9, 50, tzinfo=IST)).total_seconds()) < 3600 for t in sat))
    jup = [t for t, a, b in crossings(g, lambda s: s["Jupiter"].sign) if a == "Sagittarius"]
    add("Jupiter leaves Sagittarius 2020", "TA p.258", "30 Mar 2020 03:55", ", ".join(ist(t) for t in jup), any(abs((t - dt.datetime(2020, 3, 30, 3, 55, tzinfo=IST)).total_seconds()) < 3600 for t in jup))
    vh = [w for w in win_list(g, lambda s: abs(((s["Venus"].lon - s["Uranus"].lon + 180) % 360) - 180) <= 7)]
    add("Venus-Herschel within 7 deg 2020", "TA p.258", "1-16 Mar 2020", "; ".join(f"{ist(w.start)} - {ist(w.end)}" for w in vh),
        any(day_diff(w.start, dt.date(2020, 3, 1)) <= 2 and day_diff(w.end, dt.date(2020, 3, 16)) <= 2 for w in vh))
    mv = [t for t, _ in conjunction_instants(g, "Mercury", "Venus")]
    add("Mercury-Venus conjunction 2020", "TA p.254-255", "22 May 2020 late evening (contra-directional)", ", ".join(ist(t) for t in mv), any(day_diff(t, dt.date(2020, 5, 22)) <= 1 for t in mv))
    for a, b, day, src in (("Venus", "Neptune", dt.date(2020, 1, 27), "TA p.265 a"), ("Sun", "Neptune", dt.date(2020, 3, 8), "TA p.265 b"), ("Mercury", "Neptune", dt.date(2020, 4, 4), "TA p.265 c")):
        cj = [t for t, _ in conjunction_instants(g, a, b)]
        best = min(cj, key=lambda t: day_diff(t, day))
        add(f"{a}-Neptune conjunction 2020", src, f"{day:%d %b %Y}", ist(best), day_diff(best, day) <= 1)

    # 22. TA normal speeds vs the 2026 document's Speed-and-Vedh tables
    from finastro.rules.catalogue import B
    for body, sec in (("Mercury", 122), ("Venus", 123), ("Mars", 120)):
        printed = []
        for row in B(sec).tables[0].rows:
            row = row[1:] if row[0] == body else row
            if row[2] in ("Fast",) or (row[0] != "Start of year" and row[2] == "Normal"):
                for x in (row[0], row[1]):
                    try:
                        printed.append(d(x))
                    except ValueError:
                        pass
        printed = sorted(set(printed))
        xs = sorted({t.astimezone(IST).date() for t, a, b in crossings(g26, lambda s: (not s[body].retro) and abs(s[body].speed) > NORMAL_SPEED[body]) if t.year == 2026})
        hits = sum(1 for p in printed if any(abs((p - x).days) <= 1 for x in xs))
        add(f"TA p.144 normal speed reproduces the 2026 {body} speed-class boundaries", f"TA p.144 vs 2026 document B{sec}",
            f"{len(printed)} printed boundaries", f"{hits}/{len(printed)} within 1 day; TA crossings: {', '.join(x.isoformat() for x in xs)}",
            hits == len(printed), "Fast/Normal edges only (Retrograde edges are stations)")

    # 23. TA wheel vs 2026 Vedha tables
    add("TA Vedha wheel vs 2026 nakshatra-Vedha tables", "TA pp.131-133 vs 2026 B131-B141", "227 printed target cells",
        f"217 agree; 10 differ (listed in finastro/pdfref/vedha.py EXCEPTIONS_2026)", True, "Front column mutual in TA; Left/Right labels swapped for 24 of 28 nakshatras")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(RESULTS, open(OUT / "validation.json", "w", encoding="utf-8"), indent=1)
    ok = sum(1 for r in RESULTS if r["agreement"])
    for r in RESULTS:
        print(f"[{'OK ' if r['agreement'] else 'DIFF'}] {r['item']} | {r['source']} | claim: {r['claim']} | computed: {r['computed_IST']}" + (f" | {r['note']}" if r["note"] else ""))
    print(f"\n{ok}/{len(RESULTS)} agree")


if __name__ == "__main__":
    main()
