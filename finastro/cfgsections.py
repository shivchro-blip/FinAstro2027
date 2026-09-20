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
    * the other `<h2>` sub-tables of the same run -- Bhadra, Kshin Moon, Total
      Days, Rahu/Ketu on a Thursday, Moon-Mercury D9, Rainfall, Mars aspecting
      Mercury, Eclipse, Vargottam in own nakshatra, Rashi Parivartan. They are
      configuration material and they are also unported, but they are not the
      per-instrument blocks this count is about. Reported separately, by
      `other_h2_tables()`, which does not state how many there are.
    * anything past p.191, which is the 2023-2026 narrative.

HOW THE TWO SETS ARE TOLD APART, AND WHY IT IS NO LONGER A DOCUMENT RANGE
    `other_h2_tables()` used to be a byte slice -- from `<section id="kshin-moon">`
    to `<section id="gold-bullish">` -- which is a membership rule that states
    where we happened to be parsing and nothing about the document. It missed
    Bhadra, which carries exactly this markup and which the document's own table
    of contents lists in the same run, one row above Kshin Moon.

    The rule is now the SHAPE plus a positive predicate on the heading:

      * the universe is every `<section id="...">` in the document that carries
        an `<h2>`. There are 16, and nothing else in the file has that shape --
        catalogue B is `<h3 class="section">`, 141 of those;
      * a CONFIGURATION BLOCK is one whose `<h2>` states a direction --
        *Gold -- Bullish Configuration*. Six do;
      * a SUB-TABLE is one whose `<h2>` states no direction. Ten do.

    The direction is not a string convenience. It is the same fact
    `config_catalogue.check_verdict` and `subtable_catalogue.check_no_verdict`
    already turn on: a block's heading carries half its verdict, and a
    sub-table's carries none because the section prints none. So membership and
    the verdict rule read the ONE property of the heading, and a section cannot
    be in one set for one purpose and the other set for another.

    `BLOCKS` below stays, because it carries instrument, direction and printed
    pages, which the heading does not. It is no longer the enumeration: its keys
    are CHECKED against the six the predicate discovers, so a seventh
    configuration block in the document fails loudly here instead of being
    dropped for not being on a list.
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
_SECTION_OPEN = re.compile(r'<section id="([^"]+)"')

#: The positive predicate that makes a `<section id>` + `<h2>` a configuration
#: block: its heading states a DIRECTION. Positive on purpose -- "not a
#: configuration block" is the negative identity that stood in for "sub-table"
#: in four places and was wrong in all four the moment a third registry
#: existed (STEP4_DECISIONS section 12.16).
_DIRECTIONAL_HEADING = re.compile(r"\b(?:Bullish|Bearish)\s+Configuration\b",
                                  re.I)


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


def is_config_heading(heading: str) -> bool:
    """True where an `<h2>` states a direction, and so names a config block.

    The whole of the membership rule, and the same property
    `config_catalogue.check_verdict` reads: a block's heading carries half of
    the section's verdict, which is why losing it is a defect there and why
    having it is an identity here.
    """
    return bool(_DIRECTIONAL_HEADING.search(heading))


def h2_sections() -> list[tuple[str, str, bool]]:
    """Every `<section id>` carrying an `<h2>`, in document order.

    Returns `(section_id, heading, is_config_block)`. THE WHOLE DOCUMENT is
    scanned, with no range: the shape is the membership rule and a byte slice
    is not. Sixteen today -- six blocks and ten sub-tables.
    """
    html = SOURCE.read_text(encoding="utf-8", errors="replace")
    found = [(m.start(), m.group(1)) for m in _SECTION_OPEN.finditer(html)]
    out: list[tuple[str, str, bool]] = []
    for i, (pos, sid) in enumerate(found):
        end = found[i + 1][0] if i + 1 < len(found) else len(html)
        m = _H2.search(html, pos, end)
        if not m:
            continue
        heading = _text(m.group(1))
        if heading:
            out.append((sid, heading, is_config_heading(heading)))
    return out


def config_sections() -> list[str]:
    """The `<section id>`s whose `<h2>` states a direction, discovered.

    `BLOCKS` is checked against this rather than trusted as the enumeration:
    a seventh block in the document must fail here, not vanish.
    """
    return [sid for sid, _, cfg in h2_sections() if cfg]


def other_h2_tables() -> list[str]:
    """The `<h2>` sub-tables that are NOT the six per-instrument blocks.

    Reported so the 58 is not read as the whole of the unported configuration
    material. Derived from the shape, not from a document range -- see the
    module docstring -- and deliberately returning a LIST rather than a count,
    so no page can print a number this function did not produce.
    """
    return [h for _, h, cfg in h2_sections() if not cfg]


def _check_blocks_are_the_discovered_six() -> None:
    """The literal `BLOCKS` list, held to what the document actually carries.

    Runs at import, because every count downstream is taken off `BLOCKS` and a
    block the document gained after this dict was typed would otherwise be
    dropped in silence -- the exact failure that hid Bhadra for four days.
    """
    discovered = set(config_sections())
    if discovered != set(BLOCKS):
        raise SystemExit(
            f"configuration blocks discovered from the document {sorted(discovered)} "
            f"are not the ones BLOCKS names {sorted(BLOCKS)}. BLOCKS carries "
            "instrument, direction and printed pages and cannot be derived; it "
            "is not allowed to disagree with the document about WHICH sections "
            "those facts describe")


_check_blocks_are_the_discovered_six()


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
