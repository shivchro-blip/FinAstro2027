"""The source's spellings, mapped to the engine's.

The 2026 document does not spell a nakshatra the same way twice. Across its
tables it prints **36 distinct spellings for 27 nakshatras** -- `Mrigsira`,
`Mrigshira` and `Mrigsria` are all Mrigashira; `Shatbisha` and `Shatbhisha` are
both Shatabhisha; `Visahka`, `Visaka` and `Vishaka` are all Vishakha. Some of
those are house style and some are plain typos, and there is no way to tell
which from the document.

That matters more than it looks. A rule that matched on the source's string
would silently stop firing the moment the document used its other spelling of
the same star, and nothing downstream could catch it. So every rule matches on
the ENGINE's name, and this module is the single place the two vocabularies
meet. The map is asserted complete in both directions: every engine name is
reachable (checked on import, below), and every spelling here occurs in the
document (checked by the harness against data/source_2026.html).

`Abhijeet` is the one entry with no engine name, and deliberately. Config sets
`nakshatra_scheme: 27` for transits and reserves the 28-division with Abhijit
for the Vedha tables alone, so the astronomy layer emits no Abhijit and a rule
that needs one is blocked rather than mapped onto its neighbour.
"""
from __future__ import annotations

import re

from ..ephem import NAKSHATRAS, SIGNS
from ..panchang import YOGA_NAMES, tithi_name

#: The 28th nakshatra. Present in the source's Vedha tables, absent from the
#: 27-division the astronomy layer is built on. Not an engine name.
ABHIJIT = "Abhijeet"

#: Source spelling -> engine name. Every key was swept out of the document's own
#: nakshatra columns; none was invented to make a lookup succeed.
NAKSHATRA_SPELLINGS = {
    "Ashwini": "Ashwini",
    "Bharni": "Bharani",
    "Kritika": "Krittika",
    "Rohini": "Rohini",
    "Mrigsira": "Mrigashira",
    "Mrigshira": "Mrigashira",
    "Mrigsria": "Mrigashira",
    "Ardra": "Ardra",
    "Punarvasu": "Punarvasu",
    "Pushya": "Pushya",
    "Ashlesha": "Ashlesha",
    "Magha": "Magha",
    "Purva Falguni": "Purva Phalguni",
    "Uttra Falguni": "Uttara Phalguni",
    "Hast": "Hasta",
    "Hasta": "Hasta",
    "Chitra": "Chitra",
    "Swati": "Swati",
    "Vishaka": "Vishakha",
    "Visaka": "Vishakha",
    "Visahka": "Vishakha",
    "Anuradha": "Anuradha",
    "Jyestha": "Jyeshtha",
    "Mool": "Mula",
    "Purva Shada": "Purva Ashadha",
    "Uttra Shada": "Uttara Ashadha",
    "Shravan": "Shravana",
    "Sharvan": "Shravana",
    "Dhanistha": "Dhanishta",
    "Shatbisha": "Shatabhisha",
    "Shatbhisha": "Shatabhisha",
    "Purva Bhadrapad": "Purva Bhadrapada",
    "Purva Bhadrpad": "Purva Bhadrapada",
    "Uttra Bhadrapad": "Uttara Bhadrapada",
    "Uttra Bhadrpad": "Uttara Bhadrapada",
    "Revati": "Revati",
}

# ------------------------------------------------------- yogas and tithis
# The same treatment as the nakshatras, with one difference that has to be
# stated rather than assumed: these two maps are **partial by construction**.
# The document names all 27 nakshatras and so that map is asserted complete in
# both directions; it names three of the 27 yogas and fifteen of the thirty
# tithis, and a map padded out to the full list would carry keys no reader
# could check against the page.
#
# Two yoga names are deliberately absent, and their absence is the load-bearing
# part. Yoga 24 is **Shukla** and yoga 11 is **Vriddhi**, and this document uses
# both words for something else entirely -- Shukla 99 times as the bright
# fortnight, Vriddhi 27 times as the repeated tithi -- and never once as a yoga.
# Reading "Shukla Ekadashi Vyatipath or Vaidhrati Yog" for the yogas it names
# must return Vyatipata and Vaidhriti, not a third yoga called Shukla. The only
# other yoga the document prints anywhere is in a panchanga block reading "Yoga
# Shubha (Sun)", which is a sample of the five limbs on one day, not a rule.

#: Source spelling -> engine name, for the three yogas the document names.
#: Five spellings of Vyatipata and three of Vaidhriti, all swept from the page.
YOGA_SPELLINGS = {
    "Vyatipat": "Vyatipata",
    "Vyatipath": "Vyatipata",
    "Vyathipat": "Vyatipata",
    "Vyathipath": "Vyatipata",
    "Vyathiphat": "Vyatipata",
    "Vaidhriti": "Vaidhriti",
    "Vaidhrati": "Vaidhriti",
    "Vaidhrathi": "Vaidhriti",
    "Aindra": "Indra",
    "Endra": "Indra",
}

#: Source spelling -> engine name, for the tithis. Fifteen names, one per
#: fortnight; which fortnight is a separate word the title prints separately,
#: which is why `paksha_in` is a reader of its own.
TITHI_SPELLINGS = {
    "Pratipada": "Pratipada",
    "Dwitiya": "Dwitiya",
    "Tritiya": "Tritiya",
    "Chaturthi": "Chaturthi",
    "Chaturhti": "Chaturthi",
    "Panchami": "Panchami",
    "Panchmi": "Panchami",
    "Shasthi": "Shashthi",
    "Shashti": "Shashthi",
    "Saptami": "Saptami",
    "Saptmi": "Saptami",
    "Ashtami": "Ashtami",
    "Asthami": "Ashtami",
    "Navami": "Navami",
    "Navmi": "Navami",
    "Dashmi": "Dashami",
    "Ekadashi": "Ekadashi",
    "Ekadahsi": "Ekadashi",
    "Dwadashi": "Dwadashi",
    "Trayodashi": "Trayodashi",
    "Chaturdashi": "Chaturdashi",
    "Purnima": "Purnima",
    "Poornima": "Purnima",
    "Amavasya": "Amavasya",
    "Amavsya": "Amavasya",
}

#: The two fortnights, in the document's own words -- both the Sanskrit name
#: and the English gloss it prints beside it, "(Bright Fortnight)".
PAKSHA_SPELLINGS = {"Shukla": "Shukla", "Bright": "Shukla",
                    "Krishna": "Krishna", "Dark": "Krishna"}

#: The source names Uranus "Herschel" throughout, as build_2027.py records.
BODY_SPELLINGS = {"Herschel": "Uranus"}

#: The source's weekday names, in Python's Monday=0 convention.
WEEKDAYS = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6}


def nakshatra(spelling: str) -> str:
    """Engine name for a source spelling. Raises rather than guessing."""
    key = spelling.strip()
    if key == ABHIJIT:
        raise KeyError(
            "Abhijit is not in the 27-division the astronomy layer emits; a "
            "rule needing it is blocked, not mapped onto a neighbour")
    try:
        return NAKSHATRA_SPELLINGS[key]
    except KeyError:
        raise KeyError(f"unmapped nakshatra spelling {spelling!r}") from None


def body(spelling: str) -> str:
    return BODY_SPELLINGS.get(spelling.strip(), spelling.strip())


def sign(spelling: str) -> str:
    name = spelling.strip()
    if name not in SIGNS:
        raise KeyError(f"unmapped sign {spelling!r}")
    return name


# ------------------------------------------------- reading a source string
# Both functions READ a string the document printed and return engine
# vocabulary. Nothing is typed twice: "Anuradha on Sunday - Bearish" carries its
# own nakshatra and its own weekday, and a rule that retyped either could drift
# from the section it cites without anything catching it.

def weekdays_in(text: str) -> tuple[int, ...]:
    """The weekdays a source string names, Monday=0, in calendar order.

    Full names only. The document abbreviates inside prose -- "particularly on
    Tue, Sat or Sun" -- and those sections are blocked on other grounds; adding
    abbreviations here would make this function match half a word elsewhere for
    no rule's benefit.
    """
    return tuple(sorted({i for w, i in WEEKDAYS.items()
                         if re.search(rf"\b{w}\b", text)}))


def nakshatras_in(text: str) -> tuple[str, ...]:
    """The nakshatras a source string names, as engine names, in text order.

    Longest spelling first, and matched regions are not re-matched: "Uttra
    Shada" must not also register as an "Uttra" that is not in the map at all,
    and "Purva Bhadrapad" must not be read as a bare "Purva". Repeats are
    collapsed -- B72's title names Ashwini twice, in its yoga name and in its
    parenthetical gloss, and that is one condition.
    """
    return _read(text, NAKSHATRA_SPELLINGS)


def _read(text: str, table: dict) -> tuple[str, ...]:
    """Engine names a source string contains, longest spelling first.

    This was `nakshatras_in`'s body, lifted so the tithi and yoga readers
    cannot drift from it. Matched regions are not re-matched, which is what
    keeps "Chaturdashi" from also registering as the "Chaturthi" it resembles,
    and "Uttra Shada" from registering as a bare "Uttra".
    """
    taken: list[tuple[int, int]] = []
    hits: list[tuple[int, str]] = []
    for spelling in sorted(table, key=len, reverse=True):
        for m in re.finditer(rf"\b{re.escape(spelling)}\b", text):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            hits.append((m.start(), table[spelling]))
    out: list[str] = []
    for _, name in sorted(hits):
        if name not in out:
            out.append(name)
    return tuple(out)


def yogas_in(text: str) -> tuple[str, ...]:
    """The yogas a source string names, as engine names, in text order."""
    return _read(text, YOGA_SPELLINGS)


def tithis_in(text: str) -> tuple[str, ...]:
    """The tithis a source string names, as engine names, in text order."""
    return _read(text, TITHI_SPELLINGS)


def paksha_in(text: str) -> str | None:
    """The fortnight a source string names, or None where it names neither.

    A string naming both raises rather than silently taking the first: a rule
    restricted to the wrong half of the month fires on a disjoint set of days
    and looks perfectly healthy from the outside.
    """
    found = {v for k, v in PAKSHA_SPELLINGS.items()
             if re.search(rf"\b{k}\b", text)}
    if len(found) > 1:
        raise KeyError(f"both fortnights named in {text!r}: {sorted(found)}")
    return found.pop() if found else None


#: Reachability, checked on import so a gap fails immediately rather than as a
#: rule that quietly never matches. The yoga and tithi maps are partial by
#: construction, so they are checked one way only -- every engine name they
#: produce must be a real one -- while the nakshatra map is checked both ways.
_yoga_reached = set(YOGA_SPELLINGS.values())
if not _yoga_reached <= set(YOGA_NAMES):               # pragma: no cover
    raise SystemExit("yoga spelling map names non-yogas: "
                     f"{sorted(_yoga_reached - set(YOGA_NAMES))}")
_tithi_reached = set(TITHI_SPELLINGS.values())
_engine_tithis = {tithi_name(n) for n in range(1, 31)}
if not _tithi_reached <= _engine_tithis:               # pragma: no cover
    raise SystemExit("tithi spelling map names non-tithis: "
                     f"{sorted(_tithi_reached - _engine_tithis)}")

_reached = set(NAKSHATRA_SPELLINGS.values())
if _reached != set(NAKSHATRAS):                        # pragma: no cover
    raise SystemExit(
        "nakshatra spelling map does not reach every engine name: "
        f"missing {sorted(set(NAKSHATRAS) - _reached)}, "
        f"unknown {sorted(_reached - set(NAKSHATRAS))}")
