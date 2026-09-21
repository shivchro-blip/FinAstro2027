"""Which rule, if any, claims each event name the monthly calendar prints.

THIS FILE IS THE EXPECTED LIST, and it is written by hand on purpose.

§12.16's finding is that a check whose expected value comes from the code under
test cannot fail. The monthly fixture compares the rule layer against the
source's own finished output, so the correspondence between the source's 147
event names and our rule ids has to be stated somewhere OTHER than the rule
layer -- otherwise "which rule should have fired here" would be answered by the
same registry whose behaviour is being measured, and every row would match by
construction.

So each name below is assigned by reading the document's row against the
catalogue-B section titles and the 58 configuration groups. Nothing is matched
by string similarity. A name with no rule gets a REASON rather than a silent
absence, because "no rule claims this" is the single most informative result
the fixture can produce and it must not look like a lookup failure.

THE FIVE KINDS OF ASSIGNMENT

    B              one or more catalogue-B rule ids claim this event
    CFG            one or more configuration-group ids claim it, and NO
                   catalogue-B section does. The two registries stay separate
                   -- a group must never inflate 141/141 -- but `verdicts.py`
                   has fired BOTH since 14-Sep-2026, so a CFG row is now
                   reproducible rather than a wiring gap, and two of them are.
                   (This entry read "those groups are NOT wired into the
                   calendar" until 16-Sep-2026. The kind itself still means
                   what it always meant: only a configuration group states
                   this event.)
    SERIES_NO_RULE the astronomy layer emits the series, and no rule anywhere
                   states a condition on it
    SUBTABLE       the event is one of the ten `<h2>` sub-tables
                   that `CONFIG_SECTIONS_SCOPE.md` reports as outside the 58
    NO_SECTION     neither catalogue B nor the configuration blocks contain a
                   section for it, and the layer emits no series for it either

A `B` assignment naming a BLOCKED rule is still a `B` assignment. The row is
claimed by a section we ported; the reason it produces nothing is recorded on
the rule as a named missing input, which is a different fact from nobody having
looked at the row. The matcher counts those separately and says so.
"""
from __future__ import annotations

B = "B"
CFG = "CFG"
SERIES_NO_RULE = "SERIES_NO_RULE"
SUBTABLE = "SUBTABLE"
#: A sub-table rule claims this event -- the third registry, wired
#: 20-Sep-2026. Parallel to CFG and for the same reason: only an `<h2>`
#: sub-table states this event, and no catalogue-B section does.
#: SUBTABLE still means what it always meant -- a sub-table states it and
#: NOBODY has written the rule -- so the two kinds must not be merged: the
#: whole value of this file is that "no rule claims this" is a result.
SUB = "SUB"
NO_SECTION = "NO_SECTION"

#: event name as the document prints it -> (kind, targets, note)
MAP: dict = {

    # ------------------------------------------------------------ panchang
    "Pradosh": (B, ["b064_pradosh"], ""),
    "Ekadashi on Friday": (B, ["b065_ekadashi_on_friday"], ""),
    "Asadh Shukla Ekadashi on Friday": (
        B, ["b065_ekadashi_on_friday"],
        "the month name Asadh is the open `month_system_confirmation`; the "
        "tithi-and-weekday half is b065's own condition"),
    "Ekadashi on Friday (Kshay of Ekadahsi)": (
        B, ["b065_ekadashi_on_friday"], "the Kshay half is b066/b067"),
    "Ekadashi on Friday, Shukla Ekadashi Kshay Tithi": (
        B, ["b065_ekadashi_on_friday", "b066_kshay_tithi_shukla_paksha"], ""),
    "Kshay Tithi in Shukla Paksh": (B, ["b066_kshay_tithi_shukla_paksha"], ""),
    "Shukla Chaturthi Kshay": (B, ["b066_kshay_tithi_shukla_paksha"], ""),
    "Shukla Pratipada Kshay": (B, ["b066_kshay_tithi_shukla_paksha"], ""),
    "Shukla Purnima Kshay Tithi": (B, ["b066_kshay_tithi_shukla_paksha"], ""),
    "Shukla Saptmi Kshay": (B, ["b066_kshay_tithi_shukla_paksha"], ""),
    "Kshay Tithi in Krishna Paksh": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Chaturthi Kshay Tithi in Krishna Paksh": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Krishna Asthami Kshay Tithi": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Krishna Chaturthi Kshay Tithi": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Krishna Dwitiya Kshay Tithi": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Krishna Panchmi Kshay Tithi": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Krishna Trayodashi Kshay Tithi": (
        B, ["b067_kshay_tithi_krishna_paksha"], ""),
    "Shukla Ekadashi Vriddhi Tithi": (
        B, ["b068_vriddhi_tithi_shukla_paksha"], ""),
    "Shukla Navmi Vriddhi Tithi": (
        B, ["b068_vriddhi_tithi_shukla_paksha"], ""),
    "Shukla Pratipada Vriddhi Tithi": (
        B, ["b068_vriddhi_tithi_shukla_paksha"], ""),
    "Shukla Saptmi Vriddhi Tithi": (
        B, ["b068_vriddhi_tithi_shukla_paksha"], ""),
    "Shukla Trayodashi Vriddhi Tithi": (
        B, ["b068_vriddhi_tithi_shukla_paksha"], ""),
    "Vriddhi Tithi in Krishna Paksh": (
        B, ["b069_vriddhi_tithi_krishna_paksha"], ""),
    "Dashmi Vriddhi Tithi in Krishna Paksh": (
        B, ["b069_vriddhi_tithi_krishna_paksha"], ""),
    "Krishna Chaturthi Vriddhi Tithi": (
        B, ["b069_vriddhi_tithi_krishna_paksha"], ""),
    "Krishna Pratipada Vriddhi Tithi": (
        B, ["b069_vriddhi_tithi_krishna_paksha"], ""),
    "Shukla Pratipada on Saturday": (
        B, ["b095_shukla_pratipada_on_saturday_or_sunday"], ""),
    "Shukla Pratipada on Sunday": (
        B, ["b095_shukla_pratipada_on_saturday_or_sunday"], ""),
    "Shukla Trayodashi on Tuesday": (
        B, ["b109_shukla_trayodashi_on_tuesday_or_saturday"], ""),
    "Shukla Trayodashi on Saturday": (
        B, ["b109_shukla_trayodashi_on_tuesday_or_saturday"], ""),
    "Three Saturdays in Shukla Paksh": (
        B, ["b101_three_saturdays_in_shukla_paksha"], ""),
    "Amavsya Ghadi lesser than Chaturdashi": (
        B, ["b106_amavasya_ghadi_lesser_than_chaturdashi"], ""),
    "Vyatipath Yog on Tuesday": (
        B, ["b096_vyatipata_yoga_on_tuesday_saturday_or_sunday"], ""),
    "Vyathipath Yog on Saturday": (
        B, ["b096_vyatipata_yoga_on_tuesday_saturday_or_sunday"], ""),
    "Vyatipath Yog on Sunday": (
        B, ["b096_vyatipata_yoga_on_tuesday_saturday_or_sunday"], ""),
    "Vyatipath Yog in Panchak": (
        B, ["b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak"], ""),
    "Vaidhriti Yog in Panchak": (
        B, ["b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak"], ""),
    "Eindra Yog in Panchak": (
        B, ["b056_aindra_vaidhriti_or_vyatipata_yoga_in_panchak"], ""),

    # -------------------------------------------------- karana and the day
    "Bhadra": (
        SUB, ["sub_bhadra"],
        "PORTED 20-Sep-2026, and it needed a REGISTRY before it needed code. "
        "Bhadra is `<section id=\"sec-142\">` carrying an `<h2>` -- the "
        "sub-table shape, not catalogue B's `<h3 class=\"section\">` -- so it "
        "belonged to the third registry and was excluded from it only because "
        "membership was a byte range beginning at `kshin-moon`. Counting the "
        "shape over the whole document found exactly one section outside that "
        "range, this one, so the range was widened to the shape: 9 -> 10. The "
        "karana ingress series is new with the port (866 records a year, the "
        "tithi scan at half its arc) and the rule selects the eight Vishti "
        "karanas the section's own prose names. Verified against the "
        "section's first table before wiring: 99 of 99 windows on both "
        "boundaries within 30 s, nothing unmatched in either direction. This "
        "note read NO_SECTION and '54 windows' until today -- 54 is the "
        "MONTHLY calendar's count and the section prints 99"),
    "Total Day": (
        SUB, ["sub_total_days_in_year"],
        "PORTED 20-Sep-2026. `panchang.total_days` reproduces the source's "
        "own dd+mm rule 12/12 for 2026 and the astronomy layer emits 12 "
        "`total_day` records, which reached the base track for days while no "
        "rule read them. This entry read SERIES_NO_RULE until the rule was "
        "written, and that kind was the correct answer at the time"),

    # ------------------------------------------------------------ lunation
    "Solar Eclipse": (
        SERIES_NO_RULE, ["eclipse"],
        "the eclipse series is emitted and carries the weekday; catalogue B's "
        "two eclipse sections (b110, b111) are both LUNAR. The one "
        "solar-eclipse group in the document is cfg_silver_bullish_18, blocked "
        "on `month_system`"),
    "Lunar Eclipse": (
        B, ["b110_lunar_eclipse_on_tuesday",
            "b111_lunar_eclipse_in_vaishakha_shravana_or_ashwin"],
        "b110 is narrower than the printed row (Tuesday only) and b111 is "
        "blocked on `month_system`"),
    "Lunar Moon Eclipse in Shravan": (
        B, ["b111_lunar_eclipse_in_vaishakha_shravana_or_ashwin"],
        "blocked: naming the month Shravan is `month_system_confirmation`"),

    # ------------------------------------------------------------- apsides
    "Apogee": (B, ["b057_moon_apogee", "b057a_apogee_with_amavasya"], ""),
    "Perigee": (B, ["b058_moon_perigee"], ""),
    "Perigee Dates": (B, ["b058_moon_perigee"], ""),
    "Northern Hemisphere (Basant Golaarambh)": (
        B, ["b063_hemisphere_range"],
        "blocked: the +/- 2/3 day range is undocumented"),
    "South Hemisphere - Dakshin Golarambh": (
        B, ["b063_hemisphere_range"], "blocked, as above"),

    # ----------------------------------------- Moon nakshatra by weekday
    "Mrigsira on Thursday": (B, ["b104_mrigashira_on_thursday"], ""),
    "Moon on Mrigsira on Monday": (
        B, ["b097_moon_in_mrigashira_on_monday"], ""),
    "Shatbisha on Tuesday": (B, ["b103_shatabhisha_on_tuesday"], ""),
    "Uttra Shada on Monday": (B, ["b105_uttara_ashadha_on_monday"], ""),
    "Mangal Ashwini Yog": (B, ["b072_ashwini_on_tuesday"], ""),
    "Uttra Falguni Nakshtra": (B, ["b071_moon_in_uttara_phalguni"], ""),
    "Uttra Falguni Nakshtra (Pisces D9)": (
        B, ["b071d_uttara_phalguni_by_navamsa"],
        "blocked: the D9 half is the section's own unstated observation"),
    "Uttra Falguni Nakshtra (Sagittarius D9)": (
        B, ["b071d_uttara_phalguni_by_navamsa"], "blocked, as above"),
    "Uttra Falguni Nakshtra in Sagittarius and Capricorn D9": (
        B, ["b071d_uttara_phalguni_by_navamsa"], "blocked, as above"),

    # --------------------------------------------- planet in a nakshatra
    "Sun in Uttra Shada Nakshtra": (
        B, ["b091_sun_in_uttara_ashadha_ashwini_or_chitra"], ""),
    "Sun in the Chitra Nakshtra": (
        B, ["b091_sun_in_uttara_ashadha_ashwini_or_chitra"], ""),
    "Sun in the Nakshatra of Ashwini": (
        B, ["b091_sun_in_uttara_ashadha_ashwini_or_chitra"], ""),
    "Sun in Kritika": (B, ["b092_sun_in_krittika"], ""),
    "Sun in Shatbisha": (B, ["b115_sun_or_venus_in_shatabhisha"], ""),
    "Venus in Shatbisha": (B, ["b115_sun_or_venus_in_shatabhisha"], ""),
    "Mercury alone in Mool Nakshtra": (B, ["b098_mercury_in_mula"], ""),
    "Mercury in Purva Bhadrapad": (B, ["b114_mercury_in_purva_bhadrapada"], ""),
    "Mars in Dhanistha": (
        B, ["b113_mars_in_dhanishta"],
        "cfg_sugar_bearish_01 states the same residency for sugar and is not "
        "wired"),
    "Mars in Rohini": (
        B, ["b089s_mars_in_rohini", "b089_mars_in_rohini_or_chitra"], ""),
    "Mars in Ardra": (
        NO_SECTION, [],
        "b089 covers Rohini and Chitra only; no section names Mars in Ardra"),
    "Jupiter in Magha Nakshtra": (
        B, ["b099_jupiter_in_magha_purva_phalguni_uttara_phalguni_or_hasta"],
        ""),
    "Venus alone in Shravan Nakshtra": (B, ["b107_venus_alone_in_shravana"], ""),
    "Venus Mercury alone in any sign": (
        B, ["b016_mercury_venus_alone_in_a_sign"], ""),
    "Venus Mercury alone in any sign - Gemini": (
        B, ["b016_mercury_venus_alone_in_a_sign"], ""),

    # ---------------------------------------------------------- colocation
    "Venus Mars in the same Nakshtra (Purva Shada)": (
        B, ["b090_venus_mars_same_nakshatra"], ""),
    "Venus Mars in the same Nakshtra (Shravan)": (
        B, ["b090_venus_mars_same_nakshatra"], ""),
    "Venus Mars in the same Nakshtra (Uttra Shada)": (
        B, ["b090_venus_mars_same_nakshatra"], ""),
    "Mars ahead of Jupiter in the same sign": (
        B, ["b086_mars_ahead_of_jupiter_same_sign"], ""),
    "Mars behind Jupiter in the same sign": (
        B, ["b085_mars_behind_jupiter_same_sign"], ""),
    "Mars behind Jupiter in Cancer": (
        B, ["b085_mars_behind_jupiter_same_sign"], ""),
    "Venus ahead of Jupiter in the same sign": (
        B, ["b080_venus_ahead_of_jupiter_same_sign"], ""),
    "Venus behind Jupiter in the same sign": (
        B, ["b079_venus_behind_jupiter_same_sign"], ""),
    "Rahu Mars in the same sign": (
        CFG, ["cfg_gold_bullish_03_rahu_mars_same_sign",
              "cfg_silver_bullish_07_rahu_mars_same_sign"],
        "Catalogue B has no Rahu-Mars section. Wired 14-Sep-2026; this is "
        "one of the two windows the port moved"),
    "Rahu Mars in the same Nakshatra": (
        CFG, ["cfg_gold_bullish_03_rahu_mars_same_sign",
              "cfg_silver_bullish_07_rahu_mars_same_sign"],
        "the same-nakshatra sub-window of the same groups"),
    "Sun, Mars, Mercury and Venus together in Capricorn": (
        NO_SECTION, [],
        "a four-body stellium. Every same-sign section in the catalogue is a "
        "PAIR (b078, b084, b093), and no section states a three- or four-body "
        "residency"),
    "Shani Chandra Dwidwadash Yog along negative axis": (
        B, ["b094_shani_chandra_dwidwadash_yog"], ""),

    # -------------------------------------------------------------- motion
    "Jupiter, Mercury both Retrograde": (
        B, ["b082_jupiter_mercury_both_retrograde"],
        "cfg_silver_bullish_16 states the same pair for silver and is not "
        "wired"),
    "Mercury and Venus both Retrograde": (
        B, ["b083_mercury_venus_both_retrograde"], ""),
    "Saturn and Venus both Retrograde": (
        NO_SECTION, [],
        "the catalogue's three both-retrograde sections are Saturn+Mercury, "
        "Jupiter+Mercury and Mercury+Venus. Saturn+Venus is not among them"),

    # ---------------------------------------------------------- visibility
    "Venus Combust in East and Rise in West": (
        B, ["b015a_venus_combust_east", "b015b_venus_rise_west"], ""),
    "Combust Venus in West": (B, ["b015_venus_combust_cycle"], ""),
    "Venus Rise": (B, ["b015_venus_combust_cycle"], ""),
    "Venus Rise in East": (B, ["b015_venus_combust_cycle"], ""),
    "Combust Jupiter": (
        B, ["b022_jupiter_combust_cycle", "b022w_jupiter_combust_west"], ""),
    "Saturn Combust": (B, ["b027_saturn_combust_cycle"], ""),
    "Mercury Rise in West": (
        B, ["b009_mercury_combust_cycle"],
        "cfg_gold_bearish_04 states the same rise for gold, and is wired"),
    "Mercury goes Combust in the East in Vimishra speed": (
        B, ["b009_mercury_combust_cycle", "b122_mercury_speed_and_vedh"],
        "the Vimishra (mixed) speed class is b122's calibration"),
    "Mercury Manifestation": (
        B, ["b010_mercury_manifestation"],
        "blocked: the section states no measurable threshold for 'real "
        "strength'"),
    "Mercury Manifestation, Mars Rise and Saturn Rise": (
        B, ["b010_mercury_manifestation", "b004_mars_combust_cycle",
            "b027_saturn_combust_cycle"], ""),
    "Mercury furthest from Sun": (
        B, ["b011_mercury_furthest_from_sun"],
        "blocked: the maximum-elongation series is not emitted"),

    # --------------------------------------------------------- conjunction
    "Sun Mercury Conjunction": (
        SERIES_NO_RULE, ["aspect/conjunction"],
        "the conjunction series carries it. The catalogue's conjunction "
        "sections are Mars-Mercury (b012), Venus-Mercury (b017) and the outer "
        "planets (b041, b047, b053); none is Sun-Mercury, which the document "
        "treats as a turning date rather than as a rule"),
    "Venus Mercury Conjunction": (B, ["b017_venus_mercury_conjunction"], ""),
    "Mercury Venus Conjunction in Contra-Directional Mode": (
        B, ["b017_venus_mercury_conjunction"],
        "the contra-directional qualifier is the motion pair, not a further "
        "section"),
    "Saturn Mars Conjunction": (
        SERIES_NO_RULE, ["aspect/conjunction"],
        "emitted; no catalogue-B section states a Saturn-Mars conjunction"),
    "Sun Herschel Conjunction": (B, ["b041_herschel_conjunction_sun"], ""),
    "Sun Neptune Conjunction": (B, ["b047_neptune_conjunction_sun"], ""),
    "Neptune Conjuncts Mars": (B, ["b047_neptune_conjunction_mars"], ""),
    "Neptune Conjuncts Mercury": (B, ["b047_neptune_conjunction_mercury"], ""),
    "Neptune Conjuncts Saturn": (
        B, ["b047_neptune_conjunction_saturn"],
        "cfg_silver_bullish_20 states the same conjunction for silver, and "
        "is wired"),
    "Neptune Conjuncts Venus": (B, ["b047_neptune_conjunction_venus"], ""),
    "Neptune Opposite Venus": (B, ["b048_neptune_opposition_venus"], ""),
    "Netpune Opposite Mercury": (B, ["b048_neptune_opposition_mercury"], ""),
    "Netpune Opposite Sun": (B, ["b048_neptune_opposition_sun"], ""),
    "Pluto Conjuncts Mars": (B, ["b053_pluto_conjunction_mars"], ""),

    # -------------------------------------------------------------- aspect
    "Mars tenth to Saturn": (
        NO_SECTION, [],
        "a tenth-house graha drishti. The layer emits conjunction and "
        "opposition only, and `aspect_orbs` is the open question that blocks "
        "cfg_gold_bullish_06 for the same reason"),
    "Mars twelveth to Saturn": (
        NO_SECTION, [], "a twelfth-house relation, as above"),
    "Jupiter in Cancer making Trine with Neptune in Pisces": (
        NO_SECTION, [],
        "a trine. cfg_sugar_bullish_01 states the Jupiter-in-Cancer residency "
        "alone -- wired, but only half the condition; the trine half has no "
        "series"),

    # -------------------------------------------------------- paap kartari
    "Mercury in Paap Kartari between Mars Sun": (
        B, ["b116_mercury_in_paap_kartari"], "blocked on `valence`"),
    "Mercury in Paap Kartari between Mars and Sun": (
        B, ["b116_mercury_in_paap_kartari"], "blocked on `valence`"),
    "Mercury in Paap Kartari between Rahu Mars": (
        B, ["b116_mercury_in_paap_kartari"], "blocked on `valence`"),
    "Mercury in Paap Kartari between Rahu Sun": (
        B, ["b116_mercury_in_paap_kartari"], "blocked on `valence`"),
    "Jupiter in Paap Kartari between Mars Ketu 7th aspect of Rahu": (
        B, ["b117_jupiter_in_paap_kartari"], "blocked on `valence`"),

    # ---------------------------------------------------------- vargottama
    "Vargottam Mars": (
        B, ["b006_not_an_ingress_view"],
        "blocked: the section is a view over a FIELD the records carry, not "
        "over an ingress series"),
    "Vargottam Mars in Aquarius": (B, ["b006_not_an_ingress_view"], "blocked"),
    "Vargottam Mars in Aries": (B, ["b006_not_an_ingress_view"], "blocked"),
    "Vargottam Mars in Cancer (Debilitated)": (
        B, ["b006_not_an_ingress_view"], "blocked"),
    "Vargottam Mars in Capricorn": (B, ["b006_not_an_ingress_view"], "blocked"),
    "Vargottam Mars in Gemini": (B, ["b006_not_an_ingress_view"], "blocked"),
    "Vargottam Mars in Sagittarius": (
        B, ["b006_not_an_ingress_view"], "blocked"),
    "Mars in Pisces D9": (
        B, ["b005_not_an_ingress_view"],
        "blocked, for the same reason as b006"),
    "Mars in Pisces D9 - Vargottam": (
        B, ["b005_not_an_ingress_view", "b006_not_an_ingress_view"], "blocked"),
    "Jupiter Vargottam in Cancer": (
        NO_SECTION, [],
        "the catalogue's only vargottama section is b006, and it is MARS's. "
        "The field is on every record; no section reads it for Jupiter"),
    "Jupiter Vargottam in Gemini": (NO_SECTION, [], "as above"),

    # ----------------------------------------------------- speed and vedh
    "Atichari Mars in Purva Bhadrapad": (
        B, ["b120_mars_speed_and_vedh"],
        "WITHDRAWN in §12.10: Mars's Fast level is a single-point fit"),
    "Exalted Mars, if Atichari, may create sudden Negative Events in "
    "Geo-Politics": (
        B, ["b120_mars_speed_and_vedh"], "withdrawn, as above"),
    "Mars Vedh of Pushya": (
        B, ["b132_mars_nakshatra_vedh"], "withdrawn in §12.10"),
    "Rahu Vedh of Pushya, Swati and Abhijeet": (
        B, ["b137_rahu_vedha_unreached"],
        "blocked: no calibration reaches Rahu's wheel"),
    "Rahu does Vedh of Ashlesha, Vishaka and Shravan": (
        B, ["b137_rahu_vedha_unreached"], "blocked, as above"),
    "Saturn Vehda of Ardra": (B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Saturn Vehda of Chitra": (B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Saturn Vehda of Hast": (B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Saturn Vehda of Mool": (B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Saturn Vehda of Mrigsira": (B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Saturn Vehda of Purva Shada": (
        B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Saturn Vehda of Uttra Falguni": (
        B, ["b136_saturn_nakshatra_vedh"], "blocked"),
    "Jupiter in Pushya Nakshatra (Vedh by Rahu)": (
        B, ["b135_jupiter_nakshatra_vedh"],
        "blocked: Jupiter has no speed doctrine"),
    "Jupiter in Pushya Nakshtra (Vedh by Rahu)": (
        B, ["b135_jupiter_nakshatra_vedh"],
        "blocked, as above -- the document spells the same event two ways"),

    # ------------------------------------------------- the ten sub-tables
    "Moon Mercury in the same D9": (
        SUBTABLE, ["sub_moon_mercury_in_the_same_navamsh"],
        "one of the ten `<h2>` sub-tables. PORTED 21-Sep-2026, verified "
        "against the section's own table first: 36 of 36 printed windows, "
        "each on the navamsa its Navmansh (D9) cell names, with 37 of the 40 "
        "stated clock boundaries inside five minutes. This note was wrong "
        "twice before that and both readings are on record in "
        "`subtables.sub_moon_mercury_in_the_same_navamsh`: first that the "
        "condition was already computable, which the artifact refuted, then "
        "that the Moon's D9 residency was a series the build could not "
        "supply, which was true until the build supplied it"),
    "Rahu/Ketu Nakshtra on Thursday": (
        SUB, ["sub_rahu_or_ketu_nakshatra_on_a_thursday"],
        "PORTED 20-Sep-2026, verified against the section's own table first: "
        "13 of 13 dates, 13 of 13 nakshatra cells, and all five of its "
        "clock-time boundaries within 50 s. Both halves -- the node's "
        "nakshatra and the weekday -- are emitted"),
}


def kinds() -> dict:
    """Assignment kind -> how many event names carry it."""
    out: dict = {}
    for kind, _targets, _note in MAP.values():
        out[kind] = out.get(kind, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def unmapped(event_names) -> list:
    """Event names the document prints that this file does not assign."""
    return sorted(n for n in event_names if n not in MAP)


def unknown(event_names) -> list:
    """Names assigned here that the document does not print.

    A stale entry is as much a defect as a missing one: it would mean this file
    is describing a document it no longer matches.
    """
    return sorted(n for n in MAP if n not in set(event_names))
