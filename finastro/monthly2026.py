"""The source's own Chapter-4 monthly calendar, read as a 2026 fixture.

WHAT THIS IS FOR

Every convention in this build was validated in isolation -- the ayanamsha
against printed ingress times, the weekday rule against 75 dated rows, the
speed levels against the Fast/Normal boundaries, the civil-day overlap against
13 tables. **Nothing has ever checked whether the assembled layer reproduces
the source's own finished output.** Chapter 4 is that output: twelve month
blocks, 407 printed rows, each carrying a dated window and the source's own
inference for it.

So these rows are ported as a FIXTURE for 2026 and never as content for 2027.
Nothing downstream of this module may put one of them in a calendar; what they
are for is to be compared against what the rule layer emits when it is run over
the same year.

HOW IT IS READ

Out of `data/source_2026.html`, at call time, exactly like `cfgsections.py`
reads the configuration blocks. Not one date, time or inference in this file is
typed. A fixture transcribed by hand would be a second copy of the document
that could drift from it, and a comparison against a drifted copy measures the
transcription rather than the engine.

THE THREE COUNTS, and why they differ

    407   printed rows          -- what the twelve tables contain
    354   distinct dated rows   -- after the carry-overs are folded
    147   distinct event names  -- how many kinds of thing are printed

A window spanning a month boundary is REPRINTED in each month it touches: the
Rahu Vedh of 01-Jan to 02-Aug appears in seven month blocks. Those 53 extra
copies are the document's presentation and not 53 further claims, so a
reproduction rate over 407 would count the same window up to seven times. The
denominator this fixture reports against is 354.

INFERENCE IS NOT A PROPERTY OF THE WINDOW

Some rows are reprinted with a DIFFERENT inference in the later month -- the
Capricorn stellium is "Explained separately" in January and "Positive for
Sectors ruled by Rahu" in February. The dedup key is therefore the window and
not the inference, and every variant is carried on the folded row
(`inferences`) rather than one of them being picked. Which of two printed
inferences is "the" inference of a window is the document's question, not ours.
"""
from __future__ import annotations

import collections
import datetime as dt
import functools
import pathlib
import re
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "source_2026.html"

#: The fixture year. Every printed date in Chapter 4 is a 2026 date except the
#: carry-ins, which the document itself prints with their real (2025) year.
YEAR = 2026

_CHAPTER = "CHAPTER 4 DIVIDER"
_BLOCK = re.compile(
    r'<div class="month-block">(.*?)<div class="summary">(.*?)</div>', re.S)
_HEADER = re.compile(r'<div class="month-header">(.*?)</div>', re.S)
_ROW = re.compile(r"<tr([^>]*)>(.*?)</tr>", re.S)
_CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_TAG = re.compile(r"<[^>]+>")
_MONTH_NAME = re.compile(r"([A-Z]+)\s+2026")
_PAGES = re.compile(r"pg\.\s*([^<]+)")

#: The row classes the document uses to colour a row. They are the document's
#: own tone marking, read rather than inferred from the inference text.
TONES = ("positive", "negative", "neutral")


def _text(raw: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", raw)).replace("&amp;", "&").strip()


def _date(cell: str):
    """`01-Jan-26` -> a date. Empty means the window has no such end.

    Two end-date cells in the chapter read `Till year end` rather than a date.
    They are windows with a stated end, written in prose -- not instants, and
    not absent ends -- so they parse to None here and the raw cell is kept on
    the row, where `open_end_prose` can tell the two apart. Turning the phrase
    into 31-Dec-26 would be us supplying a date the document did not print.
    """
    cell = cell.strip()
    if not cell:
        return None
    try:
        return dt.datetime.strptime(cell, "%d-%b-%y").date()
    except ValueError:
        return None


def _time(cell: str):
    """`9:15`, `02:29` -> a time; empty -> None.

    One cell in the whole chapter reads `Till 14:26` -- a prose word inside a
    time column. The time is taken and the raw cell kept beside it, because
    dropping the row would lose a real window and silently rewriting the cell
    would lose the fact that the document wrote prose there.
    """
    cell = cell.strip()
    if not cell:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})", cell)
    if not m:
        return None
    return dt.time(int(m.group(1)), int(m.group(2)))


@dataclass(frozen=True)
class PrintedRow:
    """One `<tr>` of one month block, as printed."""

    month: int
    month_name: str
    pages: str
    event: str
    start_date: object
    start_time: object
    end_date: object
    end_time: object
    inference: str
    tone: object
    bold: bool
    raw_start_time: str
    raw_end_time: str
    raw_end_date: str = ""

    @property
    def window(self) -> tuple:
        """The dedup key: the dated window, WITHOUT the inference."""
        return (self.event, self.start_date, self.start_time,
                self.end_date, self.end_time, self.raw_end_date)

    @property
    def open_end_prose(self) -> bool:
        """The end is stated in words rather than as a date."""
        return self.end_date is None and bool(self.raw_end_date.strip())

    @property
    def is_instant(self) -> bool:
        return self.end_date is None and not self.open_end_prose


@dataclass
class FixtureRow:
    """One distinct dated window, with every month it is printed in."""

    event: str
    start_date: object
    start_time: object
    end_date: object
    end_time: object
    raw_end_date: str = ""
    months: list = field(default_factory=list)
    inferences: list = field(default_factory=list)
    tones: list = field(default_factory=list)

    @property
    def reprinted(self) -> bool:
        return len(self.months) > 1

    @property
    def inference_varies(self) -> bool:
        """True where the document printed two different inferences for it."""
        return len(set(self.inferences)) > 1

    @property
    def open_end_prose(self) -> bool:
        return self.end_date is None and bool(self.raw_end_date.strip())

    @property
    def is_instant(self) -> bool:
        return self.end_date is None and not self.open_end_prose

    @property
    def window(self) -> tuple:
        return (self.event, self.start_date, self.start_time,
                self.end_date, self.end_time, self.raw_end_date)


@dataclass(frozen=True)
class MonthBlock:
    month: int
    name: str
    pages: str
    rows: tuple
    summary: str


def _source() -> str:
    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE} missing")
    return SOURCE.read_text(encoding="utf-8")


@functools.lru_cache(maxsize=1)
def blocks() -> tuple:
    """The twelve month blocks of Chapter 4, in printed order."""
    doc = _source()
    chapter = doc[doc.index(_CHAPTER):]
    out = []
    for raw, summary in _BLOCK.findall(chapter):
        header = _text(_HEADER.search(raw).group(1))
        name = _MONTH_NAME.search(header).group(1)
        month = dt.datetime.strptime(name[:3].title(), "%b").month
        pages_m = _PAGES.search(header)
        pages = pages_m.group(1).strip() if pages_m else ""
        rows = []
        for attrs, body in _ROW.findall(raw):
            if "<th" in body:
                continue
            cells = [_text(c) for c in _CELL.findall(body)]
            if len(cells) != 6:
                raise ValueError(
                    f"{name}: a Chapter-4 row has {len(cells)} cells, not 6: "
                    f"{cells}")
            classes = attrs.lower()
            tone = next((t for t in TONES if t in classes), None)
            rows.append(PrintedRow(
                month=month, month_name=name.title(), pages=pages,
                event=cells[0],
                start_date=_date(cells[1]), start_time=_time(cells[2]),
                end_date=_date(cells[3]), end_time=_time(cells[4]),
                inference=cells[5], tone=tone, bold="bold-row" in classes,
                raw_start_time=cells[2], raw_end_time=cells[4],
                raw_end_date=cells[3] if _date(cells[3]) is None else ""))
        out.append(MonthBlock(month, name.title(), pages, tuple(rows),
                              _text(summary)))
    if len(out) != 12:
        raise ValueError(f"Chapter 4 has {len(out)} month blocks, not 12")
    return tuple(out)


def printed_rows() -> list:
    """All 407 rows as printed, carry-over copies included."""
    return [r for b in blocks() for r in b.rows]


@functools.lru_cache(maxsize=1)
def fixture_rows() -> tuple:
    """The 354 distinct dated windows, in order of first appearance."""
    folded = {}
    for r in printed_rows():
        f = folded.get(r.window)
        if f is None:
            f = FixtureRow(r.event, r.start_date, r.start_time,
                           r.end_date, r.end_time, r.raw_end_date)
            folded[r.window] = f
        f.months.append(r.month)
        f.inferences.append(r.inference)
        f.tones.append(r.tone)
    return tuple(folded.values())


def event_names() -> dict:
    """Distinct event names -> how many distinct windows each heads."""
    c = collections.Counter(r.event for r in fixture_rows())
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def counts() -> dict:
    """The denominators, computed from the document at call time."""
    rows = fixture_rows()
    return {
        "printed_rows": len(printed_rows()),
        "distinct_windows": len(rows),
        "reprinted_windows": sum(1 for r in rows if r.reprinted),
        "carry_over_copies": len(printed_rows()) - len(rows),
        "distinct_event_names": len(event_names()),
        "windows_with_varying_inference": sum(
            1 for r in rows if r.inference_varies),
        "instants": sum(1 for r in rows if r.is_instant),
        "spans": sum(1 for r in rows if not r.is_instant),
        "windows_starting_before_2026": sum(
            1 for r in rows if r.start_date and r.start_date.year < YEAR),
    }


if __name__ == "__main__":
    for k, v in counts().items():
        print(f"{k:<32} {v:>5}")
