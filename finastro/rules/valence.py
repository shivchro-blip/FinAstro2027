"""Benefic / malefic, as config/conventions.yaml `valence` rules it.

Read off the astronomy layer only: the Moon's valence comes from the Kshin
(Malefic) Moon window (`subtables._kshin_moon`, off the tithi series), every
other body's is fixed. Aspects are Vedic drishti counted in whole signs.

`piecewise` turns a predicate over the sky's state into spans: it collects the
boundaries of every series the predicate can read (sign and nakshatra spans
of the named bodies, the Kshin windows), evaluates the predicate once per
interval, and merges equal neighbours. Nothing here computes a longitude.
"""
from __future__ import annotations

import bisect

from ..config import CONF
from ..sky import Span

V = CONF["valence"]
BENEFIC = frozenset(V["benefic"])
MALEFIC = frozenset(V["malefic"])
CLASSICAL = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
             "Rahu", "Ketu")
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def drishti_houses(body: str) -> tuple[int, ...]:
    d = V["drishti"]
    if body in ("Uranus", "Neptune", "Pluto"):
        return tuple(d["outers"])
    if body in ("Rahu", "Ketu"):
        return tuple(d["nodes"])
    return tuple(d.get(body, d["all"]))


def ordinal(n: int) -> str:
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def house_from(src_sign: str, dst_sign: str) -> int:
    return (SIGNS.index(dst_sign) - SIGNS.index(src_sign)) % 12 + 1


def aspects(body: str, body_sign: str, target_sign: str) -> int | None:
    """The drishti house if `body` in `body_sign` aspects `target_sign`."""
    h = house_from(body_sign, target_sign)
    return h if h in drishti_houses(body) else None


class State:
    """The sky between two boundaries: each tracked body's sign/nakshatra and
    whether the Moon is Kshin."""

    def __init__(self, sky, bodies, frames=("sign",)):
        from .subtables import _kshin_moon
        self.series = {}
        for b in bodies:
            for fr in frames:
                sp = list(sky.spans(b, fr))
                self.series[(b, fr)] = ([s.start for s in sp], sp)
        k = _kshin_moon(sky)
        self.kshin = ([s.start for s in k], k)
        self.sky = sky

    def boundaries(self):
        out = set()
        for starts, sp in self.series.values():
            out.update(starts)
            out.update(s.end for s in sp)
        out.update(self.kshin[0])
        out.update(s.end for s in self.kshin[1])
        return sorted(out)

    def at(self, body, frame, t):
        starts, sp = self.series[(body, frame)]
        i = bisect.bisect_right(starts, t) - 1
        return sp[i].value if i >= 0 and t < sp[i].end else None

    def kshin_at(self, t):
        starts, sp = self.kshin
        i = bisect.bisect_right(starts, t) - 1
        return i >= 0 and t < sp[i].end

    def valence(self, body, t):
        if body == "Moon":
            return "malefic" if self.kshin_at(t) else "benefic"
        if body in BENEFIC:
            return "benefic"
        if body in MALEFIC:
            return "malefic"
        return None


def piecewise(sky, bodies, pred, frames=("sign",)):
    """Spans where pred(state, t) is truthy, its value on the span."""
    st = State(sky, bodies, frames)
    pts = st.boundaries()
    out = []
    for a, b in zip(pts, pts[1:]):
        if b <= a:
            continue
        v = pred(st, a + (b - a) / 2)
        if not v:
            continue
        if out and out[-1].end == a and out[-1].value == v:
            out[-1] = Span(out[-1].start, b, v, out[-1].open_start,
                           b >= sky.span_end)
        else:
            out.append(Span(a, b, v, a <= sky.span_start, b >= sky.span_end))
    return out


def neighbour_spans(sky, body):
    """Spans of (behind, ahead) for `body` off its neighbour_change records."""
    from ..sky import parse
    recs = sky.class_records("neighbour_change", body=body)
    if not recs:
        return []
    out = []
    first = recs[0]["astronomy"]
    t0 = parse(recs[0]["time"]["t_start_utc"])
    out.append(Span(sky.span_start, t0, (first["neighbour_behind_from"],
                                         first["neighbour_ahead_from"]),
                    open_start=True))
    for r, nxt in zip(recs, recs[1:] + [None]):
        a = r["astronomy"]
        start = parse(r["time"]["t_start_utc"])
        end = parse(nxt["time"]["t_start_utc"]) if nxt else sky.span_end
        out.append(Span(start, end, (a["neighbour_behind"], a["neighbour_ahead"]),
                        open_end=nxt is None))
    return out


def paap_kartari(sky, body):
    """Spans where `body` is hemmed by malefics (config valence.kartari): the
    nearest body behind and ahead are both malefic and each sits in `body`'s
    sign or the sign either side. Value {planet_1, planet_2, sign}."""
    nb = neighbour_spans(sky, body)
    starts = [s.start for s in nb]
    others = sorted({x for s in nb for x in s.value})
    st = State(sky, [body] + others)
    pts = sorted(set(st.boundaries()) | set(starts) | {s.end for s in nb})

    def at(t):
        i = bisect.bisect_right(starts, t) - 1
        return nb[i].value if i >= 0 and t < nb[i].end else None
    out = []
    for a, b in zip(pts, pts[1:]):
        if b <= a:
            continue
        t = a + (b - a) / 2
        pair = at(t)
        if not pair:
            continue
        me = st.at(body, "sign", t)
        ok = all(st.valence(x, t) == "malefic"
                 and house_from(me, st.at(x, "sign", t)) in (12, 1, 2)
                 for x in pair)
        if not ok:
            continue
        # The printed rows run across the hemmed planet's sign change
        # ("Aquarius, till 11th Apr Pisces"), so the sign is not in the value.
        v = {"planet_1": pair[0], "planet_2": pair[1]}
        if out and out[-1].end == a and out[-1].value == v:
            out[-1] = Span(out[-1].start, b, v, out[-1].open_start)
        else:
            out.append(Span(a, b, v, a <= sky.span_start))
    return out
