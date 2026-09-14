"""Catalogue B -- the 141 Chapter-1 rule sections, read from the source.

Every rule in this package cites its section through here rather than carrying
a typed copy of the title. That is the project's founding rule applied to the
rule layer: nothing is typed twice. A title typed from memory is exactly the
transcription error the 2026 source is full of, and a page number typed from
memory is worse, because nothing downstream can catch it.

Catalogue B is defined in `config/conventions.yaml` under
`source_probability.transfer_test.catalogues.B` and locked by
`tests/test_2026_regression.py::test_source_probability_labels`: every
`h3.section` in the document except the Table of Contents heading. That is 141
sections. The definition is reproduced here structurally -- the same elements,
bounded to Chapter 1 -- and the count is asserted on import, so a document that
changed under us fails loudly instead of silently renumbering every rule.

Bounding to Chapter 1 matters. The last `h3.section` is followed by the Bhadra
chapter and then the monthly calendars and prophecy blocks, none of which is a
rule section; without the bound the final section would swallow 87 tables that
belong to other chapters.
"""
from __future__ import annotations

import html as _html
import pathlib
import re
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SOURCE = ROOT / "data" / "source_2026.html"

#: The chapter the rule catalogue lives in. Both markers are matched rather
#: than hardcoded as line numbers, so an edit above them cannot shift the slice.
CHAPTER_1_OPEN = '<h2 class="chapter">Chapter 1'
CHAPTER_1_CLOSE = "<h2>Bhadra"

#: Catalogue B's own size, per config and the 2026 harness.
CATALOGUE_B_SIZE = 141

_TAG = re.compile(r"<[^>]+>")
_SECTION = re.compile(r'<h3 class="section"')
_PAGE = re.compile(r'<span class="page-marker">(.*?)</span>')


def _text(fragment: str) -> str:
    """Tag-stripped, entity-decoded, whitespace-normalised text."""
    return re.sub(r"[ \t]+", " ",
                  _html.unescape(_TAG.sub(" ", fragment))).strip()


@dataclass(frozen=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Section:
    """One catalogue-B section, exactly as the document prints it."""

    b: int                       #: 1..141, document order
    line: int                    #: 1-based line in data/source_2026.html
    heading: str                 #: title WITH the page marker, as printed
    title: str                   #: title WITHOUT the page marker
    page: str                    #: "p.67", "pp.112-113", or "" if unmarked
    remarks: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    paras: tuple[str, ...] = ()
    tables: tuple[Table, ...] = field(default=())

    @property
    def printed_rows(self) -> int:
        return sum(len(t.rows) for t in self.tables)

    def cite(self) -> str:
        """The citation a verdict carries: the heading as printed."""
        return self.heading


def _parse() -> tuple[Section, ...]:
    lines = SOURCE.read_text(encoding="utf-8").split("\n")
    try:
        lo = next(i for i, l in enumerate(lines) if CHAPTER_1_OPEN in l)
        hi = next(i for i, l in enumerate(lines) if CHAPTER_1_CLOSE in l)
    except StopIteration:                              # pragma: no cover
        raise SystemExit("Chapter 1 markers not found in data/source_2026.html")

    heads = [i for i in range(lo, hi) if _SECTION.search(lines[i])]
    out = []
    # heads[0] is the Table of Contents heading, which catalogue B excludes.
    for k, i in enumerate(heads[1:]):
        end = heads[k + 2] if k + 2 < len(heads) else hi
        seg = "\n".join(lines[i:end])
        page_m = _PAGE.search(lines[i])
        page = _text(page_m.group(1)) if page_m else ""
        heading = _text(lines[i])
        title = _text(_PAGE.sub("", lines[i]))

        def divs(cls: str, _seg: str = seg) -> tuple[str, ...]:
            return tuple(_text(m) for m in re.findall(
                r'<div class="%s">(.*?)</div>' % cls, _seg, re.S))

        tables = []
        for t in re.findall(r"<table>(.*?)</table>", seg, re.S):
            trs = re.findall(r"<tr>(.*?)</tr>", t, re.S)
            hdr = tuple(_text(c) for c in
                        re.findall(r"<th[^>]*>(.*?)</th>", trs[0], re.S)) \
                if trs else ()
            rows = tuple(tuple(_text(c) for c in
                               re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S))
                         for tr in trs[1:])
            tables.append(Table(hdr, rows))

        out.append(Section(
            b=k + 1, line=i + 1, heading=heading, title=title, page=page,
            remarks=divs("remark"), notes=divs("note"),
            paras=tuple(_text(m) for m in
                        re.findall(r"<p[^>]*>(.*?)</p>", seg, re.S)),
            tables=tuple(tables)))
    return tuple(out)


SECTIONS: tuple[Section, ...] = _parse()

if len(SECTIONS) != CATALOGUE_B_SIZE:                  # pragma: no cover
    raise SystemExit(
        f"catalogue B is {len(SECTIONS)} sections, expected {CATALOGUE_B_SIZE}"
        " -- data/source_2026.html has changed under the rule layer")

_BY_B = {s.b: s for s in SECTIONS}


def B(n: int) -> Section:
    """Catalogue-B section `n`, 1-based in document order."""
    return _BY_B[n]


def find(fragment: str) -> Section:
    """The one section whose heading contains `fragment`.

    Used in the harness and in reports. A rule addresses its section by number,
    because a number cannot be matched by two sections whereas "Journey of
    Mars" nearly can.
    """
    hits = [s for s in SECTIONS if fragment in s.heading]
    if len(hits) != 1:
        raise KeyError(f"{fragment!r} matches {len(hits)} sections")
    return hits[0]


# ------------------------------------------------------- verbatim text tools
# Both functions SLICE the source string and never rewrite it, so a condition
# or a verdict carried by a rule is a substring of the document, checkable by
# `in`. The harness asserts exactly that for every ported rule.

_DASHES = ("—", "–", " - ")


def split_statement(text: str) -> tuple[str, str | None]:
    """Split "<condition> - <verdict>" at the source's own dash.

    The document states most of its rules in that shape, in the section title
    ("Anuradha on Sunday - Bearish") and in its remarks ("Jupiter Combust in
    West - first nine days fall, then bullish till Rise") alike. Returns the
    whole string and None where there is no dash: a statement with no dash is a
    condition with no verdict, or a verdict with no separable condition, and
    guessing which would be reading rather than slicing.
    """
    for d in _DASHES:
        if d in text:
            left, right = text.split(d, 1)
            return left.strip(), right.strip()
    return text.strip(), None


def split_proviso(verdict: str) -> tuple[str, str | None]:
    """Split "<verdict>: <case>" at the source's colon.

    Applied to the VERDICT half `split_statement` returns, in the two sections
    where the colon does not label the verdict but restricts it to a case. B87
    prints "Bullish: Rahu in Shatbisha" and B89 "Bullish: Mars in Rohini", and
    in both the named case is a condition the section's own table obeys rather
    than an instance appended to the outcome -- B87's eight printed windows are
    all Rahu-in-Shatabhisha windows and B88 continues the same series, verdict
    free, under the heading "Rahu in Dhanistha".

    Deliberately not applied blanket, and not applied to a title before its
    dash. B98 heads its condition with a colon -- "Mool Nakshtra: Mercury in
    Mool Nakshtra - Bearish" -- so the verdict half this sees is "Bearish" and
    there is nothing to split. Each use is a per-rule reading with its evidence
    recorded beside it.

    Returns the whole string and None where there is no colon.
    """
    if ":" in verdict:
        left, right = verdict.split(":", 1)
        return left.strip(), right.strip()
    return verdict.strip(), None


def split_final(text: str) -> tuple[str, str | None]:
    """Split at the source's LAST dash rather than its first.

    Six titles join two halves of one condition with a dash and then add the
    verdict with a second: "Kshay Tithi - Shukla Paksh (Bright Fortnight) -
    Bearish". `split_statement` takes the first dash and hands back "Shukla
    Paksh (Bright Fortnight) - Bearish" as the verdict, which puts half the
    condition inside the outcome -- the same failure B87's colon produced, in a
    different punctuation mark.

    Used only where the middle segment is plainly part of the condition, which
    is decided per rule and checked by the harness, never inferred from the
    dash count. A two-segment statement gives the same answer either way.
    """
    for d in _DASHES:
        if d in text:
            left, right = text.rsplit(d, 1)
            return left.strip(), right.strip()
    return text.strip(), None


def split_sentences(text: str) -> tuple[str, ...]:
    """The separate statements a paragraph packs together, verbatim.

    The document sometimes prints two whole rules in one `div`: B60's remark is
    "Amavasya on Tuesday - Bullish. Amavasya if Moon in Sagittarius or Pisces -
    Bearish", and read as one statement the second rule ends up inside the
    first one's verdict.

    The split is the full stop, and it is accepted **only** when every part it
    produces is itself a dash statement -- otherwise the function raises rather
    than hand back fragments. That condition is what keeps this from being a
    licence to cut prose wherever it reads conveniently: a period that does not
    separate two of the document's own statements will not satisfy it. Compare
    B18, where the separator on offer was a comma and no such test could be
    put to it, and the outcome stayed inside the condition.
    """
    parts = tuple(p.strip() for p in re.split(r"(?<=[a-z])\. (?=[A-Z])", text))
    if len(parts) > 1:
        bad = [p for p in parts if split_statement(p)[1] is None]
        if bad:
            raise ValueError(
                f"sentence split of {text[:60]!r}... produced a part with no "
                f"verdict dash: {bad[0][:60]!r}; the period is not separating "
                "two statements here")
    return parts


def lettered(note: str) -> dict[str, str]:
    """The `a)` / `b)` / `c)` items of a multi-part remark, verbatim.

    The source packs several distinct rules into one `div` this way -- Venus
    Combust Rise Cycle p.14 carries three. Splitting them is not authoring:
    each item is one of the document's own numbered statements, returned as the
    document prints it.
    """
    out, key, buf = {}, None, []
    for line in note.splitlines():
        stripped = line.strip()
        m = re.match(r"^([a-z])\)\s*(.*)$", stripped)
        if m:
            if key:
                out[key] = " ".join(buf).strip()
            key, buf = m.group(1), [m.group(2)]
        elif key:
            buf.append(stripped)
    if key:
        out[key] = " ".join(buf).strip()
    return out
