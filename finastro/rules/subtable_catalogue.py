"""The nine `<h2>` sub-tables of the configuration chapter, read from the source.

THE THIRD SHAPE OF MARKUP, AND THE THIRD DENOMINATOR
    Catalogue B is `<h3 class="section">` and there are 141 of those.
    The instrument configuration blocks are `<section id="...">` carrying an
    `<h2>` and named groups under it, and there are 6 of those holding 58
    groups. These are a THIRD thing: `<section id="...">` with an `<h2>` and
    NO named groups -- one table per section, standing on its own.

    `cfgsections.other_h2_tables()` has counted them since the configuration
    scope survey and named them on three pages, precisely so the 58 would not
    be read as the whole of the unported material. What it could not do is
    give them somewhere to be ported TO. This module does, and it keeps them
    out of both existing denominators for the same reason `config_catalogue`
    keeps the groups out of catalogue B's: a number that quietly changes
    meaning is the failure this build has shipped twice.

    `SubTable.b` is None and never a number, so `rules.sections_ported()`
    cannot see one; the rules live in `subtables.SUBTABLE_REGISTRY`, which is
    neither `REGISTRY` nor `CONFIG_REGISTRY`. Three registries, three
    denominators, and no row whose provenance is ambiguous: a sub-table rule
    id begins `sub_`.

WHAT THESE SECTIONS DO NOT CARRY, AND WHY THAT MATTERS AT REGISTRATION
    A configuration block's `<h2>` states a DIRECTION -- *Gold -- Bullish
    Configuration* -- and `config_catalogue.check_verdict` exists because
    slicing only the group heading loses half of that statement.

    These nine `<h2>` headings state no direction at all. *Total Days in
    Year* and *Rahu or Ketu Nakshtra on a Thursday* are conditions and
    nothing else, and neither section prints a verdict anywhere in its body.
    So a sub-table rule's `verdict_text` is None, and that is the DOCUMENT's
    silence rather than a slice that went missing. The check here is the
    mirror of the configuration one and runs at the same moment: a sub-table
    rule that arrives CARRYING a verdict is refused, because the only place
    such a word could have come from is us.

    The source's monthly calendar does print a tone against some of these
    rows -- 'Positive' against every Rahu/Ketu Thursday window, 'Turning
    Date' against Total Day. That is a different table in a different
    chapter, and importing it here would be the B87 colon failure in a third
    costume: a verdict attached to a section that does not state one, from a
    neighbour that does. It is recorded in the rule's notes and is not its
    verdict.

Financial astrology is a speculative interpretive framework. Nothing this
module produces is investment advice.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass

from ..cfgsections import SOURCE, h2_sections
from .catalogue import Table

_TAG = re.compile(r"<[^>]+>")
_H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)
_PAGE = re.compile(r'<span class="page-tag">(.*?)</span>', re.S)
_SECTION_OPEN = re.compile(r'<section id="([^"]+)"')

#: Membership comes from `cfgsections.h2_sections()` -- the SHAPE, read over
#: the whole document -- and not from a byte range. The two cannot drift apart
#: because there is now only one of them: `other_h2_tables()` is the same call
#: with the headings taken where this takes the ids.


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(_TAG.sub(" ", fragment))).strip()


def _tables(fragment: str) -> tuple[Table, ...]:
    out = []
    for tbl in re.findall(r"<table[^>]*>(.*?)</table>", fragment, re.S):
        headers = tuple(_text(h) for h in
                        re.findall(r"<th[^>]*>(.*?)</th>", tbl, re.S))
        rows = tuple(
            tuple(_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S))
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S)
            if "<td" in tr)
        out.append(Table(headers=headers, rows=rows))
    return tuple(out)


@dataclass(frozen=True)
class SubTable:
    """One `<h2>` sub-table, shaped like a `Section`.

    Carries the fields `Rule` reads off a section -- `title`, `page`,
    `heading`, `b` -- so a sub-table rule is written with exactly the
    apparatus a catalogue-B rule is written with and nothing new.
    """

    sid: str                            #: the `<section id>`, document order
    n: int                              #: 1-based, 1..9
    title: str                          #: the `<h2>`, verbatim
    page: str                           #: the page tag, as printed
    body_text: str = ""
    tables: tuple[Table, ...] = ()

    #: Not a catalogue-B section, and not a configuration group. None, and
    #: never a number: see the module docstring on the three denominators.
    b = None

    @property
    def heading(self) -> str:
        return self.title

    @property
    def key(self) -> str:
        return self.sid

    @property
    def printed_rows(self) -> int:
        return sum(len(t.rows) for t in self.tables)

    def cite(self) -> str:
        return f"{self.title} ({self.page})"

    def carries(self, text: str) -> bool:
        """True where `text` is a verbatim substring of this section.

        The test every condition on a sub-table rule is held to. There is no
        second element to fall back on here, unlike a configuration group,
        because these sections have no enclosing directional heading -- which
        is the same fact that makes their verdicts null.
        """
        flat = re.sub(r"\s+", " ", text).strip()
        return bool(flat) and (flat in self.title or flat in self.body_text)


def _parse() -> tuple[SubTable, ...]:
    """The sub-tables, discovered by shape and sliced one section at a time.

    `h2_sections()` decides membership; this only finds each member's bounds.
    A section ends at its own `</section>`, not at the next section's opening
    tag: Bhadra's close is followed by the chapter's `<nav>` Contents, and
    swallowing that would put nine headings into one section's body text and
    make `carries()` accept a condition sliced from a neighbour.
    """
    src = SOURCE.read_text(encoding="utf-8", errors="replace")
    out = []
    for n, sid in enumerate(
            (s for s, _, cfg in h2_sections() if not cfg), start=1):
        a = src.index(f'<section id="{sid}"')
        close = src.find("</section>", a)
        frag = src[a: close if close != -1 else len(src)]
        h2 = _H2.search(frag)
        page = _PAGE.search(frag)
        out.append(SubTable(
            sid=sid, n=n,
            title=_text(h2.group(1)) if h2 else "",
            page=_text(page.group(1)) if page else "",
            body_text=_text(frag),
            tables=_tables(frag)))
    return tuple(out)


SUBTABLES: tuple[SubTable, ...] = _parse()
BY_ID = {s.sid: s for s in SUBTABLES}


def S(sid: str) -> SubTable:
    """The sub-table with this `<section id>`, or a hard failure.

    A KeyError here means the document moved under us, which is the one
    outcome worth an import crash: every count on the status page is taken
    off this tuple.
    """
    return BY_ID[sid]


class SuppliedVerdict(ValueError):
    """Raised where a sub-table rule arrives carrying a verdict.

    None of the nine sections prints one. A verdict on such a rule can only
    have been supplied by us, and a supplied verdict that renders in the
    verdict column is indistinguishable from the source's own -- which is
    the whole of what `config_catalogue.check_verdict` was built to stop,
    pointed the other way.
    """


def check_no_verdict(rule_id: str, sub: SubTable, verdict, verdict_from) -> None:
    if verdict is not None or verdict_from is not None:
        raise SuppliedVerdict(
            f"{rule_id}: {sub.key} prints no verdict anywhere in its body, so "
            f"{verdict!r} from {verdict_from!r} is ours and not the "
            "document's. A sub-table rule is condition-only by construction")
