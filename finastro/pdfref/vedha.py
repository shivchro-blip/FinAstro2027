"""Sarvatobhadra Vedha from TA pp.130-141 (printed pp.100-111).

THE WHEEL (TA pp.131-133, "VEDHA -- BY PLANET VEDHA TO THE PLANET") is a
28-row table: for each nakshatra a planet occupies, the nakshatra it vedhas
"TO SOUTH/RIGHT", "TO EAST/LEFT" and "TO FRONT". Transcribed from the page
images below, in the project's nakshatra spelling.

CROSS-CHECK AGAINST THE 2026 DOCUMENT (tests/test_pdfref.py):
* every one of the 95 wheel entries finastro/rules/vedha.py transcribed from
  the 2026 Mars/Mercury/Venus tables is one of TA's three targets for that
  nakshatra;
* 217 of the 227 printed target cells in 2026 B131-B141 equal TA's cell once
  the 2026 labels are mapped -- the 2026 "Left"/"Right" equal TA's
  "East/Left"/"South/Right" for Revati, Ashwini, Bharani and Krittika and are
  the other way round for the remaining 24 nakshatras. TA's "Front" column is
  fully mutual and equals the 2026 "Front" everywhere but one cell. The ten
  exceptions are listed in EXCEPTIONS_2026 and are 2026 printing defects (a
  one-row shift in B131's Right column, two Saturn targets printed in the
  wrong column, one Herschel Front cell).

THE DIRECTION DOCTRINE. TA p.134 rule 1: Sun, Moon, Rahu & Ketu vedha all
three sides. Rule 2: Jupiter, Mars, Venus, Saturn & Mercury vedha the right
side while retrograde and the left side while direct. Rules 3-7: after
turning direct, Mars 4 / Mercury 3 / Jupiter 8 / Venus 5 / Saturn 10 days
before rule 2 applies. The 2026 tables instead key the five star planets on
speed class: Atichari -> Left, Normal -> Front, Retrograde -> Right. The two
agree on Retrograde -> Right and on fast-direct -> Left; TA has no Front for
the star planets. `targets()` applies the 2026 class doctrine (it is the one
the 2026 tables evidence, 95/95) with TA's own normal speeds (p.144) as the
Atichari threshold and TA's post-station lag, and every result carries the
doctrine it used. The conflict is recorded in REFERENCE_PDF_RULES.md.
"""
from __future__ import annotations

R, L, F = "Right", "Left", "Front"

TA_WHEEL = {   # nakshatra -> (TO SOUTH/RIGHT, TO EAST/LEFT, TO FRONT)
    "Ashwini": ("Jyeshtha", "Rohini", "Purva Phalguni"),
    "Bharani": ("Anuradha", "Krittika", "Magha"),
    "Krittika": ("Bharani", "Vishakha", "Shravana"),
    "Rohini": ("Swati", "Ashwini", "Abhijeet"),
    "Mrigashira": ("Chitra", "Revati", "Uttara Ashadha"),
    "Ardra": ("Hasta", "Uttara Bhadrapada", "Purva Ashadha"),
    "Punarvasu": ("Uttara Phalguni", "Purva Bhadrapada", "Mula"),
    "Pushya": ("Purva Phalguni", "Shatabhisha", "Jyeshtha"),
    "Ashlesha": ("Magha", "Dhanishta", "Anuradha"),
    "Magha": ("Shravana", "Ashlesha", "Bharani"),
    "Purva Phalguni": ("Abhijeet", "Pushya", "Ashwini"),
    "Uttara Phalguni": ("Uttara Ashadha", "Punarvasu", "Revati"),
    "Hasta": ("Purva Ashadha", "Ardra", "Uttara Bhadrapada"),
    "Chitra": ("Mula", "Mrigashira", "Purva Bhadrapada"),
    "Swati": ("Jyeshtha", "Rohini", "Shatabhisha"),
    "Vishakha": ("Anuradha", "Krittika", "Dhanishta"),
    "Anuradha": ("Vishakha", "Bharani", "Ashlesha"),
    "Jyeshtha": ("Ashwini", "Swati", "Pushya"),
    "Mula": ("Revati", "Chitra", "Punarvasu"),
    "Purva Ashadha": ("Uttara Bhadrapada", "Hasta", "Ardra"),
    "Uttara Ashadha": ("Purva Bhadrapada", "Uttara Phalguni", "Mrigashira"),
    "Abhijeet": ("Shatabhisha", "Purva Phalguni", "Rohini"),
    "Shravana": ("Dhanishta", "Magha", "Krittika"),
    "Dhanishta": ("Ashlesha", "Shravana", "Vishakha"),
    "Shatabhisha": ("Pushya", "Abhijeet", "Swati"),
    "Purva Bhadrapada": ("Punarvasu", "Uttara Ashadha", "Chitra"),
    "Uttara Bhadrapada": ("Ardra", "Purva Ashadha", "Hasta"),
    "Revati": ("Mula", "Mrigashira", "Uttara Phalguni"),
}

#: Where the 2026 document's Left/Right labels coincide with TA's.
SAME_LABELS = {"Revati", "Ashwini", "Bharani", "Krittika"}

#: The ten 2026 cells that disagree with TA (section, own nakshatra, column,
#: printed, TA value).
EXCEPTIONS_2026 = (
    (131, "Chitra", R, "Jyeshtha", "Mrigashira"),
    (131, "Swati", R, "Anuradha", "Rohini"),
    (131, "Vishakha", R, "Vishakha", "Krittika"),
    (131, "Anuradha", L, "Bharani", "Vishakha"),
    (131, "Anuradha", R, "Swati", "Bharani"),
    (131, "Jyeshtha", R, "Chitra", "Swati"),
    (131, "Mula", R, "Hasta", "Chitra"),
    (136, "Uttara Bhadrapada", R, "Ardra", "Purva Ashadha"),
    (136, "Revati", R, "Mrigashira", "Mula"),
    (139, "Rohini", F, "Uttara Ashadha", "Abhijeet"),
)


def cells_2026_labels(nak: str) -> dict:
    """TA's three targets under the 2026 document's Left/Right labels."""
    right, left, front = TA_WHEEL[nak]
    if nak in SAME_LABELS:
        return {L: left, R: right, F: front}
    return {L: right, R: left, F: front}


ALL_SIDES = ("Sun", "Moon", "Rahu", "Ketu")
#: TA p.134-135 rules 3-7: days after a direct station before rule 2 applies.
POST_STATION_LAG = {"Mars": 4, "Mercury": 3, "Jupiter": 8, "Venus": 5,
                    "Saturn": 10}
#: TA p.137: benefic vs malefic Vedha.
BENEFIC = ("Moon", "Mercury", "Jupiter", "Venus")
MALEFIC = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")


def direction(body: str, retro: bool, fast: bool, lag_active: bool) -> tuple:
    """The side(s) `body` vedhas, with the doctrine that chose them."""
    if body in ALL_SIDES:
        return (L, R, F), "TA p.134 rule 1: all three sides"
    if retro or lag_active:
        why = ("TA p.134-135: within the post-direct lag" if lag_active and not retro
               else "Retrograde -> Right (TA rule 2; 2026 tables)")
        return (R,), why
    if fast:
        return (L,), "Atichari (above TA p.144 normal speed) -> Left (2026 tables; TA rule 2 'direct -> left')"
    return (F,), "Normal speed -> Front (2026 tables; TA p.134 names no Front for star planets)"


def targets(body: str, nak28: str, retro: bool, fast: bool,
            lag_active: bool = False) -> tuple[dict, str]:
    sides, why = direction(body, retro, fast, lag_active)
    cells = cells_2026_labels(nak28)
    return {s: cells[s] for s in sides}, why
