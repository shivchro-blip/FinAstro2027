"""The six instrument configuration blocks, read from the source.

Catalogue B is `<h3 class="section">` and there are 141 of those. These are a
DIFFERENT shape -- `<section id="...">` carrying an `<h2>` and, under it, named
groups -- and they were never in the rule layer's denominator. `cfgsections`
counts them from the document; this module turns each group into the same kind
of object a rule cites, so a configuration rule can be written with exactly the
apparatus a catalogue-B rule is written with and nothing new.

WHY THIS MODULE EXISTS SEPARATELY FROM `catalogue.py`
    Because a configuration group is not a catalogue-B section and must never
    be counted as one. `Section.b` is 1..141 and `rules.sections_ported()` is
    built on it; a group given a `b` would silently inflate the number the
    status page prints. `ConfigGroup.b` is None, and configuration rules live
    in their own registry (`config_rules.CONFIG_REGISTRY`), so the two counts
    cannot contaminate each other.

THE TRAP THIS MODULE IS BUILT AROUND
    **The block's `<h2>` and the group's heading are two halves of one verdict
    statement.** *Silver -- Bullish Configuration* is not a title only; it is
    the claim. *Moon Darshan on Friday/Saturday* carries no direction on its
    own, and *Venus Mars Together* carries none either. A porter who slices
    only the group heading produces rows with no verdict and concludes the
    source was silent -- which is the `family` failure exactly: a reading
    matched on one of its two halves, attaching five of eleven, and nothing
    downstream distinguishing "no verdict printed" from "verdict not found".

    That failure renders as a quiet blank rather than an error, which is why
    the check is HERE and runs at import: `check_verdict` refuses to let a rule
    be registered against a directional block while carrying a null verdict. It
    is deliberately not a report, not a warning and not a test-only assertion
    -- it raises, and the import fails, because the whole point is that this
    particular defect is invisible in the output.

Financial astrology is a speculative interpretive framework. Nothing this
module produces is investment advice.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass

from ..cfgsections import BLOCKS, SOURCE, groups as _groups
from .catalogue import Table

_TAG = re.compile(r"<[^>]+>")
_H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)

#: The direction words the blocks' own `<h2>` headings carry. Matched
#: case-insensitively against the heading, and used for two things that must
#: stay the same test: deciding whether a block states a direction at all, and
#: SLICING that direction out of the heading as the verdict. A typed constant
#: would be a second copy of the document's word; this is a slice of it.
DIRECTION_WORDS = ("Bullish", "Bearish")
_DIR_RE = re.compile("|".join(DIRECTION_WORDS), re.I)


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(_TAG.sub(" ", fragment))).strip()


@dataclass(frozen=True)
class ConfigBlock:
    """One `<section id>` -- an instrument and a direction."""

    id: str
    instrument: str
    direction: str          #: "bullish" / "bearish", from BLOCKS
    pages: str              #: as the document prints them
    h2: str                 #: the block heading, verbatim

    @property
    def is_directional(self) -> bool:
        """True where the block's own heading states a direction.

        The predicate the silent-verdict check keys on. It reads the HEADING
        and not our `direction` field, because the field is ours and the
        heading is the document's, and the check has to be about the document.
        """
        return _DIR_RE.search(self.h2) is not None

    @property
    def verdict(self) -> str:
        """The direction half of this block's own `<h2>`, sliced verbatim.

        This is the second half of every group verdict that the group heading
        does not state for itself. It is a substring of the document, so a rule
        carrying it is carrying the source's word and not ours.
        """
        m = _DIR_RE.search(self.h2)
        if m is None:
            raise ValueError(f"{self.id}: heading {self.h2!r} states no "
                             "direction; it has no verdict half to lend")
        return m.group(0)


@dataclass(frozen=True)
class ConfigGroup:
    """One named group under a block's `<h2>`, shaped like a `Section`.

    Carries the fields `Rule` reads off a section -- `title`, `page`,
    `heading`, `b` -- so the same `Rule` dataclass, the same validation and the
    same `fire()` serve both catalogues.
    """

    block: ConfigBlock
    n: int                              #: 1-based, document order in the block
    title: str                          #: the group heading, verbatim
    paras: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()         #: plain-note / bullish-note divs
    tables: tuple[Table, ...] = ()
    body_text: str = ""

    #: Not a catalogue-B section. None, and never a number: see the module
    #: docstring on why a `b` here would corrupt `sections_ported()`.
    b = None

    @property
    def heading(self) -> str:
        return self.title

    @property
    def page(self) -> str:
        return self.block.pages

    @property
    def key(self) -> str:
        return f"{self.block.id}#{self.n}"

    @property
    def printed_rows(self) -> int:
        return sum(len(t.rows) for t in self.tables)

    def cite(self) -> str:
        """The citation a verdict carries: BOTH halves, because both are the
        statement. A citation naming only the group would be the same elision
        the verdict check exists to catch, one layer down."""
        return f"{self.block.h2} -- {self.title} ({self.block.pages})"

    def carries(self, text: str) -> bool:
        """True where `text` is a verbatim substring of this group OR of its
        block's heading. The verbatim test every condition and verdict on a
        configuration rule is held to."""
        return (text in self.title or text in self.body_text
                or text in self.block.h2)


def _block_headings() -> dict[str, str]:
    html = SOURCE.read_text(encoding="utf-8", errors="replace")
    out = {}
    for sid in BLOCKS:
        i = html.index('<section id="' + sid + '"')
        m = _H2.search(html, i)
        if m is None:                                   # pragma: no cover
            raise SystemExit(sid + ": no <h2> under the section tag")
        out[sid] = _text(m.group(1))
    return out


def _tables_of(body: str) -> tuple[Table, ...]:
    out = []
    for t in re.findall(r"<table>(.*?)</table>", body, re.S):
        trs = re.findall(r"<tr>(.*?)</tr>", t, re.S)
        hdr = tuple(_text(c) for c in
                    re.findall(r"<th[^>]*>(.*?)</th>", trs[0], re.S)) \
            if trs else ()
        rows = tuple(tuple(_text(c) for c in
                           re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S))
                     for tr in trs[1:])
        out.append(Table(hdr, tuple(r for r in rows if r)))
    return tuple(out)


def _parse() -> tuple[ConfigGroup, ...]:
    headings = _block_headings()
    out: list[ConfigGroup] = []
    for sid, (instrument, direction, pages) in BLOCKS.items():
        block = ConfigBlock(sid, instrument, direction, pages, headings[sid])
        for n, (title, body) in enumerate(_groups(sid), 1):
            notes = tuple(
                _text(m) for cls in ("plain-note", "bullish-note")
                for m in re.findall(
                    '<div class="' + cls + '">(.*?)</div>', body, re.S))
            out.append(ConfigGroup(
                block=block, n=n, title=title,
                paras=tuple(_text(p) for p in
                            re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)
                            if _text(p)),
                notes=notes, tables=_tables_of(body), body_text=_text(body)))
    return tuple(out)


GROUPS: tuple[ConfigGroup, ...] = _parse()

#: The document's own count, asserted on import exactly as catalogue B's 141 is.
CONFIG_GROUP_COUNT = 58

if len(GROUPS) != CONFIG_GROUP_COUNT:                   # pragma: no cover
    raise SystemExit(
        f"the configuration blocks hold {len(GROUPS)} groups, expected "
        f"{CONFIG_GROUP_COUNT} -- data/source_2026.html has changed under the "
        "configuration port")

_BY_KEY = {g.key: g for g in GROUPS}


def G(block: str, n: int) -> ConfigGroup:
    """Group `n` of `block`, 1-based in document order."""
    return _BY_KEY[f"{block}#{n}"]


# --------------------------------------------- the silent-verdict check
class SilentVerdict(AssertionError):
    """A rule was registered against a directional block with no verdict.

    Its own class, so a test can require THIS failure rather than any
    AssertionError, and so a reader of a traceback is told what the defect is
    rather than being handed a bare assert.
    """


def check_verdict(rule_id: str, group: ConfigGroup, verdict: str | None,
                  verdict_from: str | None) -> None:
    """Raise unless a rule under a directional block states a verdict.

    Three separate things are checked, and each is a way the same elision shows
    up:

    1. **A directional block lends its direction to every group under it.** So
       a null verdict here is never "the source was silent"; it is the slice
       having missed the half of the statement that lives in the `<h2>`. This
       is the check the port was required to have BEFORE it started, and it
       raises rather than reporting, because a missing verdict renders as an
       ordinary blank and is invisible in the output.
    2. **A verdict must be verbatim.** It is required to be a substring of the
       group or of its block heading, so no rule can carry a direction nobody
       printed.
    3. **A verdict must say where it came from.** `title` and `block_h2` are
       different provenance claims and the difference is exactly what the trap
       is about, so an unattributed verdict is refused.
    """
    if not group.block.is_directional:
        return
    if verdict is None:
        raise SilentVerdict(
            f"{rule_id}: the block heading {group.block.h2!r} states a "
            f"direction and the group {group.title!r} was ported with no "
            "verdict. The heading and the group title are two halves of ONE "
            "statement -- slicing only the group half yields a null verdict "
            "and renders as a quiet blank. Carry the block's own word "
            f"({group.block.verdict!r}) with verdict_from='block_h2', or "
            "state why this group escapes its block's direction.")
    if not group.carries(verdict):
        raise SilentVerdict(
            f"{rule_id}: verdict {verdict!r} is not a substring of the group "
            f"{group.key} or of its block heading {group.block.h2!r}; a "
            "configuration verdict is sliced from the document, never typed")
    if not verdict_from:
        raise SilentVerdict(
            f"{rule_id}: verdict carries no attribution. 'title' and "
            "'block_h2' are different claims about where the direction was "
            "found, and that difference is the whole subject of this check")


def assert_no_silent_verdicts(rules) -> list[str]:
    """Sweep a whole registry. Returns the ids checked; raises on the first
    offender. Run at the end of `config_rules` and again from the harness, so
    the guarantee does not depend on any one call site surviving an edit."""
    seen = []
    for r in rules:
        check_verdict(r.id, r.section, r.verdict_text, r.verdict_from)
        seen.append(r.id)
    return seen
