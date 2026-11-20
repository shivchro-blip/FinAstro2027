"""Gold rules supplied by the user (Reference_materials/user_notes_gold.md).

U1  Sun in a nakshatra ruled by Venus, Mercury or Jupiter    -> gold price rise
U2  Venus, Mercury, Jupiter or a waxing Moon conjunct or      -> gold price hike
    aspecting the Sun
U3  Sun in a nakshatra ruled by Saturn or Rahu                -> gold price fall
U4  Saturn or Rahu conjunct or aspecting the Sun              -> gold price crash

HOW THE WORDS WERE MADE COMPUTABLE
* Nakshatra lords: Vimshottari, as TA pp.47-48 print them. Venus: Bharani,
  Purva Phalguni, Purva Ashadha. Mercury: Ashlesha, Jyeshtha, Revati. Jupiter:
  Punarvasu, Vishakha, Purva Bhadrapada. Saturn: Pushya, Anuradha, Uttara
  Bhadrapada. Rahu: Ardra, Swati, Shatabhisha.
* "Conjunction" = the same sidereal sign (the books' usage for "together");
  the exact separation in degrees is printed in each event.
* "Aspect" = whole-sign graha drishti, the project convention
  (config valence.drishti): every planet 7th; Jupiter also 5th and 9th; Saturn
  also 3rd and 10th; Rahu 7th only (the "some schools" 5th/9th for Rahu is not
  used, as elsewhere in the project). Venus and Mercury never get more than
  ~47 / ~28 deg from the Sun, so for them only conjunction is possible. Rahu's
  7th aspect falls on Ketu's sign, so "Sun with Ketu" counts as Rahu's aspect.
* "Waxing Moon" = Shukla paksha (Moon-Sun elongation 0-180 deg). Its
  conjunction is the first ~2 days after the new moon; its 7th aspect is the
  days just before the full moon.

AGREEMENT AND CONFLICT WITH THE PDFs / 2026 DOCUMENT (shown on every event)
* Agrees with: TA S34 A10 for Bharani and Punarvasu (Venus/Jupiter
  nakshatras, gold rally); TA S34 B1 for Anuradha (Saturn nakshatra, gold
  falls).
* Conflicts with: TA S34 A10, which puts Pushya (a Saturn nakshatra) among the
  gold-RALLY stars and says the Sun there is "more Bullish if Aspected by
  Malefic" and bearish-neutral when aspected by a benefic; TA S34 A3 and the
  2026 document's gold-bullish #2, which make the Sun in Libra WITH or
  ASPECTED BY malefics (Saturn, Mars, Rahu) BULLISH for gold; TA S34 B1, which
  makes the Sun on Anuradha with a BENEFIC bearish.
"""
from __future__ import annotations

from .catalogue import RULES, Rule, SIGNCALC, NAKCALC, placed_facts
from .detect import NAK_LORD, aspects, windows

SRC = "User note (project chat, 20 Nov 2026; Reference_materials/user_notes_gold.md)"
CONFLICT_U13 = ("Conflict: TA p.155 S34 A10 lists Sun on Bharani, Krittika, Punarvasu and Pushya as gold-RALLY stars (Pushya is a Saturn nakshatra), "
                "'not aspected by Benefic - More Bullish if aspected by Malefic'; TA p.156 S34 B1: Sun on Anuradha (Saturn nakshatra) with or aspected by a benefic - gold can fall. Both sources are shown.")
CONFLICT_U24 = ("Conflict: TA p.154 S34 A3 and the 2026 document's gold-bullish #2 make the Sun in Libra with/aspected by malefics (Saturn, Mars, Rahu) BULLISH for gold, "
                "and TA S34 A10 says a malefic aspect makes the Sun's rally stars MORE bullish; TA S34 B1 makes a benefic with the Sun on Anuradha bearish. Both sources are shown.")
ASPECT_NOTE = ("Aspect = whole-sign graha drishti (Jupiter 5/7/9, Saturn 3/7/10, Rahu 7 - project convention; Rahu's 7th falls on Ketu's sign); "
               "conjunction = same sign. Venus and Mercury can only conjoin the Sun (they never get far enough to aspect it).")
GOLD_SUN = "Gold is ruled by the Sun (user note; TA S29 lists no gold sector, the PDFs' gold rules are mostly Sun placements)."


def _lord_is(lords):
    def p(s):
        lord = NAK_LORD[s["Sun"].nak_i]
        return lord in lords and f"Sun in {s['Sun'].nak} (lord {lord})"
    return p


def _contacts(group, waxing_moon):
    def p(s):
        hits = []
        for b in group:
            if s[b].sign_i == s["Sun"].sign_i:
                hits.append(f"{b} conjunct (same sign)")
            elif aspects(s, b, "Sun"):
                n = s.sign_dist(b, "Sun")
                hits.append(f"{b} aspects ({n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n, 'th') } from {b})")
        if waxing_moon and s.paksha == "Shukla":
            if s["Moon"].sign_i == s["Sun"].sign_i:
                hits.append("waxing Moon conjunct (same sign)")
            elif aspects(s, "Moon", "Sun"):
                hits.append("waxing Moon aspects (7th)")
        if "Rahu" in group and s["Ketu"].sign_i == s["Sun"].sign_i:
            hits.append("Rahu aspects via 7th (Sun with Ketu)")
        return "; ".join(dict.fromkeys(hits)) or False
    return p


def _sep_facts(group):
    """Separation from the Sun at the window's start, for the event detail."""
    def f(s, w):
        from .engine import snapshot
        s0 = snapshot(w.start.replace(microsecond=0))
        return {"separation_from_Sun_at_start": ", ".join(
            f"{b} {abs(((s0[b].lon - s0['Sun'].lon + 180) % 360) - 180):.1f} deg" for b in group)}
    return f


def _rule(**kw):
    r = Rule(**kw)
    RULES.append(r)


_rule(id="user_u1_sun_in_venus_mercury_jupiter_nakshatra", title="Sun in a Venus, Mercury or Jupiter nakshatra (user note)",
      refs=(SRC,), verdict="Can trigger gold price rise (Bullish)", markets=("gold",),
      rule="Sun in Bharani, Purva Phalguni, Purva Ashadha (Venus), Ashlesha, Jyeshtha, Revati (Mercury), Punarvasu, Vishakha or Purva Bhadrapada (Jupiter).",
      calc=NAKCALC + " Lords per Vimshottari (TA pp.47-48).", detector=windows(_lord_is(("Venus", "Mercury", "Jupiter")), ("Sun",), placed_facts("Sun")),
      quals=(GOLD_SUN, CONFLICT_U13))
_rule(id="user_u2_sun_with_or_aspected_by_benefics", title="Venus, Mercury, Jupiter or waxing Moon with / aspecting the Sun (user note)",
      refs=(SRC,), verdict="Can trigger gold price hike (Bullish)", markets=("gold",),
      rule="Venus, Mercury or Jupiter in the Sun's sign or casting drishti on it, or the Moon doing so during Shukla paksha.",
      calc=SIGNCALC + " Waxing = Shukla paksha (elongation 0-180 deg). Window changes whenever the set of contacts changes.",
      detector=windows(_contacts(("Venus", "Mercury", "Jupiter"), True), ("Sun",), _sep_facts(("Venus", "Mercury", "Jupiter", "Moon"))),
      quals=(ASPECT_NOTE, CONFLICT_U24, "Mercury is never more than ~28 deg from the Sun, so it shares the Sun's sign for long stretches of the year."))
_rule(id="user_u3_sun_in_saturn_rahu_nakshatra", title="Sun in a Saturn or Rahu nakshatra (user note)",
      refs=(SRC,), verdict="Can trigger fall in gold prices (Bearish)", markets=("gold",),
      rule="Sun in Pushya, Anuradha, Uttara Bhadrapada (Saturn) or Ardra, Swati, Shatabhisha (Rahu).",
      calc=NAKCALC + " Lords per Vimshottari (TA pp.47-48).", detector=windows(_lord_is(("Saturn", "Rahu")), ("Sun",), placed_facts("Sun")),
      quals=(GOLD_SUN, CONFLICT_U13, "User note: 'fear, greed and market illusions are Rahu's territory'."))
_rule(id="user_u4_sun_with_or_aspected_by_saturn_rahu", title="Saturn or Rahu with / aspecting the Sun (user note)",
      refs=(SRC,), verdict="Can crash the gold price (Bearish)", markets=("gold",),
      rule="Saturn or Rahu in the Sun's sign or casting drishti on it (Rahu's 7th = Sun with Ketu).",
      calc=SIGNCALC + " Window changes whenever the set of contacts changes.",
      detector=windows(_contacts(("Saturn", "Rahu"), False), ("Sun",), _sep_facts(("Saturn", "Rahu", "Ketu"))),
      quals=(ASPECT_NOTE, CONFLICT_U24, "User note: 'fear, greed and market illusions are Rahu's territory'."))


def sun_state(s):
    """Combined state for the timeline view (the Moon left out: its contacts
    come and go every few days and are listed as their own rows)."""
    lord = NAK_LORD[s["Sun"].nak_i]
    rise, fall = [], []
    if lord in ("Venus", "Mercury", "Jupiter"):
        rise.append(f"Sun in {s['Sun'].nak} ({lord} nakshatra) [U1]")
    if lord in ("Saturn", "Rahu"):
        fall.append(f"Sun in {s['Sun'].nak} ({lord} nakshatra) [U3]")
    for b in ("Venus", "Mercury", "Jupiter"):
        if s[b].sign_i == s["Sun"].sign_i:
            rise.append(f"{b} with Sun [U2]")
        elif aspects(s, b, "Sun"):
            rise.append(f"{b} aspects Sun [U2]")
    for b in ("Saturn", "Rahu"):
        if s[b].sign_i == s["Sun"].sign_i:
            fall.append(f"{b} with Sun [U4]")
        elif aspects(s, b, "Sun"):
            fall.append(f"{b} aspects Sun [U4]")
    if s["Ketu"].sign_i == s["Sun"].sign_i:
        fall.append("Sun with Ketu = Rahu's 7th aspect [U4]")
    return (s["Sun"].nak, tuple(rise), tuple(fall))
