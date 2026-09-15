"""The document's own count of the configuration sections.

Catalogue B is `<h3 class="section">` and there are 141 of those. The instrument
configuration sections are a DIFFERENT shape -- `<section id="...">` with an
`<h2>` heading -- and they were never in the rule layer's denominator. So the
coverage page needs a second count, and the second count has to come from the
document rather than from our own config, or it is the same circular claim that
produced "141/141" in the first place.

This module is the one place that reads the six blocks out of
`data/source_2026.html`. Everything downstream (the status page, the HTML
apparatus panel, the scope report) takes the numbers from here.

WHAT COUNTS AS A GROUP
    A named configuration group is one entry under a block's `<h2>`:
      * gold: an `<h3>` heading, 13 bullish + 6 bearish;
      * silver and sugar: a `<div class="config-title">`, 20/10 and 7/2.
    The two shapes are how the document carries them; they are counted the same
    way because they play the same role. The source itself is what disagrees --
    config's own tier-1 note says 17 groups for gold and 29 for silver -- and
    the document wins, because the document is the thing being claimed about.

NOT COUNTED, deliberately:
    * the eight other `<h2>` sub-tables between p.135 and p.152 (Kshin Moon,
      Total Days, Rahu/Ketu on a Thursday, Moon-Mercury D9, Rainfall, Mars
      aspecting Mercury, Eclipse, Vargottam in own nakshatra, Rashi Parivartan).
      They are configuration material and they are also unported, but they are
      not the per-instrument blocks this count is about. Reported separately.
    * anything past p.191, which is the 2023-2026 narrative.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "source_2026.html"

#: block id -> (instrument, direction, pages as printed in the document)
BLOCKS = {
    "gold-bullish": ("gold", "bullish", "pp.136-144"),
    "gold-bearish": ("gold", "bearish", "pp.145-148"),
    "silver-bullish": ("silver", "bullish", "pp.149-161"),
    "silver-bearish": ("silver", "bearish", "pp.162-167"),
    "sugar-bullish": ("sugar", "bullish", "pp.168-173"),
    "sugar-bearish": ("sugar", "bearish", "pp.174-175"),
}

#: Instruments the configuration sections belong to. Printed on the status page
#: because a reader seeing 141/141 needs to know WHICH instruments that number
#: does not reach.
INSTRUMENTS = ("gold", "silver", "sugar")

_H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)
_CFG_TITLE = re.compile(r'<div class="config-title">(.*?)</div>', re.S)
_H3 = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S)


def _text(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    for ent, ch in (("&mdash;", "--"), ("&ndash;", "-"), ("&amp;", "&"),
                    ("&nbsp;", " "), ("&rarr;", "->"), ("&#8593;", "^")):
        raw = raw.replace(ent, ch)
    return re.sub(r"\s+", " ", raw).strip()


def _blocks() -> dict[str, tuple[int, int]]:
    """Byte bounds of each configuration block, from the <section id> tags."""
    found = [(m.start(), m.group(1))
             for m in re.finditer(r'<section id="([^"]+)"', SOURCE.read_text(
                 encoding="utf-8", errors="replace"))]
    out: dict[str, tuple[int, int]] = {}
    for i, (pos, sid) in enumerate(found):
        if sid in BLOCKS:
            end = found[i + 1][0] if i + 1 < len(found) else None
            out[sid] = (pos, end if end is not None else pos + 200_000)
    return out


def groups(block: str) -> list[tuple[str, str]]:
    """The named groups of one block, as (title, body_html).

    The body is everything up to the next group boundary -- a `config-title` for
    silver and sugar, an `<h3>` for gold.
    """
    html = SOURCE.read_text(encoding="utf-8", errors="replace")
    pos, end = _blocks()[block]
    seg = html[pos:end]
    # The last block's neighbour is the 2023 narrative; stop at it.
    m = _H2.search(seg, 0)
    if m:                                     # drop the block's own <h2>
        seg = seg[m.end():]
    stop = re.search(r"<h2[^>]*>Astrologically", seg)
    if stop:
        seg = seg[: stop.start()]
    parts = re.split(r'(?:<div class="config-title">.*?</div>|<h3[^>]*>.*?</h3>)',
                     seg, flags=re.S)
    heads = re.findall(r'(?:<div class="config-title">(.*?)</div>|<h3[^>]*>(.*?)</h3>)',
                       seg, flags=re.S)
    titles = [_text(a or b) for a, b in heads]
    return [(t, parts[i + 1] if i + 1 < len(parts) else "")
            for i, t in enumerate(titles)]


def counts() -> dict[str, int]:
    """Named groups per block, counted from the document."""
    return {b: len(groups(b)) for b in BLOCKS}


def total() -> int:
    return sum(counts().values())


def by_instrument() -> dict[str, int]:
    per = counts()
    out = {i: 0 for i in INSTRUMENTS}
    for b, n in per.items():
        out[BLOCKS[b][0]] += n
    return out


def other_h2_tables() -> list[str]:
    """The `<h2>` sub-tables in the configuration chapter that are NOT the six
    per-instrument blocks. Reported so the 58 is not read as the whole of the
    unported configuration material."""
    html = SOURCE.read_text(encoding="utf-8", errors="replace")
    pos = html.index('<section id="kshin-moon"')
    end = html.index('<section id="gold-bullish"')
    seg = html[pos:end]
    return [_text(m.group(1)) for m in _H2.finditer(seg)
            if _text(m.group(1))]


if __name__ == "__main__":
    c = counts()
    for b, n in c.items():
        inst, direction, pages = BLOCKS[b]
        print(f"{b:<16} {inst:<7} {direction:<8} {pages:<12} {n:>3} groups")
    print(f"{'TOTAL':<16} {'':<7} {'':<8} {'':<12} {total():>3} groups")
    print()
    for i, n in by_instrument().items():
        print(f"  {i:<8} {n:>3}")
    print()
    print("other <h2> sub-tables in the same chapter (not counted):")
    for t in other_h2_tables():
        print("  -", t)
