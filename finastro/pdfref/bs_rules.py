"""Gold / silver price rules from Brihat Samhita (Varahamihira).

Source: Brihat Samhita, tr. P.S. Sastri (1946),
Reference_materials/Others/jyotish_brihat-samhita_p-s-sastri-vol-1-2_full_1946_Important_For_Financial.pdf
(PDF page numbers). Review and tests: Reference_materials/extracted/OTHERS_FINANCIAL_REVIEW.md,
build/pdfref/source_rules_test_2000-2026_ET.html.

BS1  42.14a  New or full Moon in Mesha or Makara (gold's signs, 41.2 / 41.7),
             with or aspected by a benefic           -> gold price promoted
BS2  42.14b  Sun in Mesha or Makara with or aspected by a malefic
                                                     -> gold price destroyed
BS3  10.17   Saturn in Uttara Bhadrapada             -> gold afflicted
BS4  42.6    Sun enters Simha: store gold and silver, sell in the 5th month
                                                     -> gold / silver profit

HOW THE WORDS WERE MADE COMPUTABLE
* Gold's signs: 41.2 Mesha "... and gold"; 41.7 Makara "... gold and black
  metal". Ch.41 assigns no sign to silver, so BS1/BS2 apply to gold only.
* Benefics: Mercury, Jupiter, Venus, the list BS 40.13 gives in brackets.
  Malefics: Saturn, Mars, Rahu, Ketu.
* "Associated with" / "conjoined" = the same sidereal sign; "aspected" =
  whole-sign graha drishti (project convention: all 7th; Mars 4/8, Jupiter
  5/9, Saturn 3/10; Rahu 7th only; Ketu by conjunction only).
* New / full Moon = the instant the Moon-Sun elongation crosses 0 / 180 deg;
  the Moon's sign is read at that instant.
* 42.6 "sell them in the 5th month": the 5th solar month counted from Simha is
  Dhanus (Sun in Sagittarius); the window runs from the Sun's entry into Simha
  to its entry into Makara (end of the 5th month).

NOT IMPLEMENTED: 41.9-13 (positions counted from a sign's house). The text
says strong malefics make its articles "very costly and scarce" and strong
benefics make them "thrive, fetch good price"; whether each means a price rise
or fall for a trader, and what "strong" means, is not settled (left to the user).
"""
from __future__ import annotations

from .catalogue import RULES, Rule, SIGNCALC, NAKCALC
from .detect import Hit, aspects, windows
from .engine import crossings, snapshot

SRC = "Brihat Samhita, tr. P.S. Sastri 1946"
GOLD_SIGNS = ("Aries", "Capricorn")
BENEFICS = ("Mercury", "Jupiter", "Venus")
MALEFICS = ("Saturn", "Mars", "Rahu", "Ketu")
SIGN_NOTE = "Gold's signs per BS 41.2 (Mesha: '... and gold', PDF p.327) and 41.7 (Makara: '... gold and black metal', PDF p.329)."
ASP_NOTE = ("With = same sidereal sign; aspect = whole-sign graha drishti (all 7th; Mars 4/8, Jupiter 5/9, Saturn 3/10; Rahu 7th; Ketu by conjunction only). "
            "Benefics Mercury, Jupiter, Venus as BS 40.13 lists them; malefics Saturn, Mars, Rahu, Ketu.")


def contacts(s, target, group):
    out = []
    for b in group:
        if s[b].sign_i == s[target].sign_i:
            out.append(f"{b} with {target}")
        elif b != "Ketu" and aspects(s, b, target):
            out.append(f"{b} aspects {target}")
    return out


def _lunation_gold(ctx):
    out = []
    for t, a, b in crossings(ctx.grid, lambda s: int(((s["Moon"].lon - s["Sun"].lon) % 360) // 180)):
        if t.year != ctx.year:
            continue
        s = snapshot(t.replace(second=0, microsecond=0))
        if s["Moon"].sign not in GOLD_SIGNS:
            continue
        ben = contacts(s, "Moon", BENEFICS)
        if ben:
            out.append(Hit(t, None, ("Moon", "Sun"), {"lunation": "Full Moon" if b == 1 else "New Moon",
                                                     "Moon_sign": s["Moon"].sign, "benefics": "; ".join(ben)}))
    return out


def _sun_malefic(s):
    if s["Sun"].sign not in GOLD_SIGNS:
        return False
    m = contacts(s, "Sun", MALEFICS)
    return "; ".join(m) if m else False


def _leo_store(ctx):
    ing = [(t, b) for t, a, b in crossings(ctx.grid, lambda s: s["Sun"].sign)]
    out = []
    for t, sg in ing:
        if sg != "Leo" or t.year != ctx.year:
            continue
        sag = next((u for u, s2 in ing if u > t and s2 == "Sagittarius"), None)
        cap = next((u for u, s2 in ing if u > t and s2 == "Capricorn"), None)
        if cap is None:
            continue
        out.append(Hit(t, cap, ("Sun",), {"buy": "Sun enters Simha", "5th_month_begins_utc": sag, "sell_by": "Sun enters Makara (5th month ends)"}))
    return out


def _rule(**kw):
    RULES.append(Rule(**kw))


_rule(id="bs_42_14a_lunation_benefic_gold", title="New / full Moon in Aries or Capricorn with a benefic (Brihat Samhita 42.14)",
      refs=(f"{SRC}, Ch.42 sl.14 (PDF p.334)", f"{SRC}, Ch.41 sl.2, 7 (PDF pp.327, 329)"),
      verdict="Gold price promoted (Bullish): 'promotes invariably the price of articles belonging to that particular Rasi occupied by her'",
      markets=("gold",),
      rule="New Moon or full Moon with the Moon in Mesha or Makara, and Mercury, Jupiter or Venus in the Moon's sign or aspecting it.",
      calc="New / full Moon = Moon-Sun elongation crossing 0 / 180 deg (bisected to 30 s); Moon's sidereal sign at that instant; " + ASP_NOTE,
      detector=_lunation_gold,
      quals=(SIGN_NOTE, "The source gives no time span for the effect. 2000-2026 test: 84 cases, gold up to the next lunation in 50 (60%), average +0.89% (lunations in these signs without a benefic: +0.03%); weak, not significant on its own."))
_rule(id="bs_42_14b_sun_malefic_gold", title="Sun in Aries or Capricorn with or aspected by a malefic (Brihat Samhita 42.14)",
      refs=(f"{SRC}, Ch.42 sl.14 (PDF p.334)", f"{SRC}, Ch.41 sl.2, 7 (PDF pp.327, 329)"),
      verdict="Gold price destroyed (Bearish): 'the Sun, conjoined with and aspected by malefics, destroys the price of the articles of that Rasi'",
      markets=("gold",),
      rule="Sun in Mesha or Makara, with Saturn, Mars, Rahu or Ketu in the same sign or aspecting it.",
      calc=SIGNCALC + " " + ASP_NOTE + " Window changes whenever the set of malefic contacts changes.",
      detector=windows(_sun_malefic, ("Sun",)),
      quals=(SIGN_NOTE, "Text says 'conjoined with and aspected by'; implemented as either, the reading used for 'with or aspected' elsewhere in the project. 2000-2026 test: 38 windows, gold fell in 20 (53% vs 44% of all same-length windows) but averaged +0.80%."))
_rule(id="bs_10_17_saturn_uttarabhadra_gold", title="Saturn in Uttara Bhadrapada (Brihat Samhita 10.17)",
      refs=(f"{SRC}, Ch.10 sl.17 (PDF p.144)",),
      verdict="Gold afflicted (Bearish): '... so do those living on the banks of rivers, cart-wrights, women and gold when he is in Uttarabhadra'",
      markets=("gold",),
      rule="Saturn in Uttara Bhadrapada nakshatra (333deg20' - 346deg40' sidereal).",
      calc=NAKCALC,
      detector=windows(lambda s: s["Saturn"].nak == "Uttara Bhadrapada" and "Saturn in Uttara Bhadrapada", ("Saturn",)),
      quals=("Recurs every ~29.5 years; 2000-2026 holds one passage in three windows: 28 Apr - 3 Oct 2025 gold +17%, 20 Jan - 17 May 2026 -0.7%, 9 Oct 2026 - 8 Feb 2027 (current) -15% to 20 Nov 2026.",
             "Same verse: Saturn in Satabhishak and Purvabhadra makes 'traders' suffer (general market, not gold)."))
_rule(id="bs_42_06_sun_leo_store_gold_silver", title="Sun in Leo: store gold and silver, sell in the 5th month (Brihat Samhita 42.6)",
      refs=(f"{SRC}, Ch.42 sl.6 (PDF p.332)",),
      verdict="Profit on gold and silver (Bullish): 'If one stores up gold, gems, skins, armours, weapons, pearls and silver when the Sun is in Simha, and sell them in the 5th month, he will get profit and sustain loss otherwise'",
      markets=("gold", "silver"),
      rule="Buy when the Sun enters Simha; sell in the 5th solar month (Sun in Dhanus).",
      calc="Sun's sidereal sign ingresses; window = Sun enters Simha -> Sun enters Makara (end of the 5th month); the 5th month begins at the Sun's entry into Dhanus.",
      detector=_leo_store,
      effect="Sell in the 5th month (Sun in Sagittarius, about mid-December to mid-January)",
      quals=("2000-2025 test (25 years): gold up by mid-December in 14 and by mid-January in 18, while 66% of all same-length holds rose; silver 14 and 17. No edge over the normal drift.",
             "42.13: the profit 'depends upon ... the Sun or the Moon ... being conjoined with very friendly planets and aspected by planets who are very friendly' - not applied (the friendship table to use is not given)."))
