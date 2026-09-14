"""Generate the 2027 astronomy layer.

Astronomy only. No interpretation, no market theme, no verdict, no confidence:
those are Step 4, and the record schema in finastro/events.py has no field they
could leak into.

Every value here is computed through finastro/ephem.py. Nothing is transcribed.
The 2026 source was wrong by 12h42m on its headline Saturn-Neptune conjunction
precisely because someone typed a time they already "knew" instead of computing
it, so this script never contains a date or a time it did not derive.

Span: 01-Dec-2026 through 31-Jan-2028, in Mumbai civil time. The carry-in and
carry-out are not padding. The 2026 source truncated windows at the year
boundary, which silently cut real events in half; anything overlapping calendar
2027 is generated whole.

    python build_2027.py
"""
from __future__ import annotations

import collections
import datetime as dt
import itertools
import json
import pathlib
import sys
import time
from dataclasses import replace
from zoneinfo import ZoneInfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from finastro import combustion as cb
from finastro import ephem, events as ev, panchang as pn
from finastro.config import CONF, PRIMARY
from finastro.events import SPAN_START, SPAN_END
from finastro.timezones import IST, UTC, civil_day_bounds

ROOT = pathlib.Path(__file__).resolve().parent
OUT_JSON = ROOT / "build" / "astronomy_2027.json"
OUT_SUMMARY = ROOT / "build" / "astronomy_2027_summary.txt"

YEAR = CONF["year"]

# --------------------------------------------------------------------- span
# Defined in finastro/events.py and imported, not redeclared: the record layer
# anchors a node's lord_relationship to an ingress that can sit in the
# carry-in, so the span has to be one value both layers read.

# ------------------------------------------------------------------- bodies
ALL_BODIES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
              "Uranus", "Neptune", "Pluto", "Rahu", "Ketu"]

#: Task excludes the Moon from D9: its navamsa changes every four hours or so,
#: and a D9 series for the Moon would be noise rather than signal.
NAVAMSA_BODIES = [b for b in ALL_BODIES if b != "Moon"]

#: The luminaries never station. The mean node is retrograde by construction,
#: so under config's `node: mean` the nodes never station either -- scanning
#: them would be a guaranteed empty result, not a check.
STATION_BODIES = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                  "Uranus", "Neptune", "Pluto"]

#: Inner planets pass through a station quickly enough for the instant to be
#: meaningful to the minute. The outers do not: longitude is stationary to
#: second order at a station, so a sub-arcsecond ephemeris difference moves the
#: clock time by many minutes. Claiming minutes for Saturn would be a lie.
STATION_PRECISION = {"Mercury": "minutes", "Venus": "minutes", "Mars": "minutes"}

COMBUST_BODIES = [b.capitalize() for b in CONF["combustion"]["thresholds_deg"]]

# ------------------------------------------------------- speed-class crossings
#: The bodies whose Fast/Normal level is CALIBRATED, with the level and the
#: interval of levels that also reproduce the source's printed boundaries. Read
#: from config so there is one copy of the number.
#:
#: Jupiter, Saturn and the outers are deliberately absent. Their missing input is
#: a slow-planet speed doctrine, not a threshold: B30 "Demoted and Shadow Speed
#: of Saturn" p.26 defines its interval by LONGITUDE (Saturn at 20 deg 31' of
#: Pisces, crossed retrograde 27-Jul-2026 and direct again 15-Mar-2027) and
#: supplies no speed level. Emitting a threshold record for them would be
#: inventing one.
#: Bodies the series is generated for, named explicitly. `speed_classes` also
#: carries `retrograde_rule` and `slow_planet_doctrine`, which are metadata and
#: not planets -- iterating the block's keys would try to generate a series for
#: the string "slow_planet_doctrine".
SPEED_CLASS_PLANETS = ("Mercury", "Venus", "Mars")
SPEED_CLASS_BODIES = {
    body: (CONF["speed_classes"][body]["threshold"],
           tuple(CONF["speed_classes"][body]["interval"]),
           CONF["speed_classes"][body]["precision_days"],
           CONF["speed_classes"][body]["section"])
    for body in SPEED_CLASS_PLANETS
    if CONF["speed_classes"][body].get("threshold") is not None
}

#: Config records why the Moon is absent: the 2026 source excludes it by name
#: in its own section headings.
CONJ_BODIES = CONF["conjunctions"]["bodies"]

ARC_SIGN = 30.0
ARC_NAKSHATRA = 360.0 / CONF["nakshatra_scheme"]
ARC_NAVAMSA = 30.0 / 9.0

# ------------------------------------------------------ source correspondence
# Every title below was read out of data/source_2026.html (437578 bytes,
# md5 5e098446d6dd13d3df8443528db5dd95) by enumerating the document's own <h3>
# headings. They are quoted exactly as printed, page marker included, because a
# title typed from memory is exactly the transcription error this project
# exists to avoid.
#
# The source names Uranus "Herschel" throughout. The key is our body name and
# the value is the source's, so the correspondence stays honest in both
# directions rather than renaming a planet to make a lookup succeed.
#
# The second element of the key is the record's subject: a body for the
# positional classes, a lunation phase or an apsis kind for the classes the
# source splits that way instead.
SOURCE_SECTIONS = {
    # Journey tables -- one per body. The Sun's equivalent is the Sankranti
    # table; the Moon has no journey table in the document.
    ("sign_ingress", "Sun"): "Sun Transgression (Sankranti) p.2",
    ("sign_ingress", "Mars"): "Journey of Mars p.5",
    ("sign_ingress", "Mercury"): "Journey of Mercury p.8",
    ("sign_ingress", "Venus"): "Journey of Venus p.12-13",
    ("sign_ingress", "Jupiter"): "Journey of Jupiter p.18-19",
    ("sign_ingress", "Saturn"): "Journey of Saturn p.23",
    ("sign_ingress", "Rahu"): "Journey of Rahu p.26",
    ("sign_ingress", "Ketu"): "Journey of Ketu p.28",
    ("sign_ingress", "Uranus"): "Journey of Herschel p.30",
    ("sign_ingress", "Neptune"): "Journey of Neptune p.34",
    ("sign_ingress", "Pluto"): "Journey of Pluto p.38",

    # Constellation (Nakshtra) tables. Mars, Mercury, Venus and the Moon have
    # none: the document tracks their nakshatra only inside the Vedh sections,
    # which are a different rule family and not this class's equivalent.
    ("nakshatra_ingress", "Sun"):
        "Sun Nakshtra Journey and Relationship with Nakshtra Lord pp.3-4",
    ("nakshatra_ingress", "Jupiter"): "Jupiter Constellation (Nakshtra) p.21",
    ("nakshatra_ingress", "Saturn"): "Saturn Constellation (Nakshtra) p.24",
    ("nakshatra_ingress", "Rahu"): "Rahu Constellation (Nakshtra) p.27",
    ("nakshatra_ingress", "Ketu"): "Ketu Constellation (Nakshtra) p.29",
    ("nakshatra_ingress", "Uranus"): "Herschel Constellation (Nakshtra) p.32",
    ("nakshatra_ingress", "Neptune"): "Neptune Constellation (Nakshtra) p.36",
    ("nakshatra_ingress", "Pluto"): "Pluto Constellation (Nakshtra) p.39",

    # Navamsa (D9) tables. Mars, Mercury, Venus, the Sun and the Moon have none.
    #
    # Mars was mapped here to "Mars in Pisces Navmansh (D9) p.6" and that was
    # wrong, so the mapping is gone rather than qualified. That table is not a
    # D9 ingress series: its Sign column is Mars's RASHI sign during the six
    # windows in which Mars's NAVAMSA is Pisces, verified 6/6 -- rashi runs
    # Capricorn, Aquarius, Pisces, Taurus, Gemini, Cancer while the navamsa is
    # Pisces at the start, midpoint and end of every row. Its dignity labels
    # are therefore rashi labels ("Capricorn (Exalted)", "Cancer
    # (Debilitated)"), and Mars holds neither dignity in Pisces. Pointing a
    # navamsa_ingress record at it would have cited a rashi-frame table as the
    # source equivalent for a D9 crossing. The table is carried in config's
    # rule_layer_pending instead, where its frame is stated.
    ("navamsa_ingress", "Jupiter"): "Jupiter in Navmansh (D9) p.22",
    ("navamsa_ingress", "Saturn"): "Saturn in Navmansh (D9) p.25",
    ("navamsa_ingress", "Rahu"): "Rahu in Navmansh (D9) p.28",
    ("navamsa_ingress", "Ketu"): "Ketu in Navmansh (D9) p.30",
    ("navamsa_ingress", "Uranus"): "Herschel in Navmansh (D9) p.32",
    ("navamsa_ingress", "Neptune"): "Neptune in Navmansh (D9) p.36",
    ("navamsa_ingress", "Pluto"): "Pluto in Navmansh (D9) p.40",

    # Motion tables carry the stations. Mars has none: Mars does not station in
    # 2026, so the document had no occasion to print one.
    ("station", "Mercury"): "Mercury Motion pp.8-9",
    ("station", "Venus"): "Venus Motion p.14",
    ("station", "Jupiter"): "Jupiter Motion p.20",
    ("station", "Saturn"): "Saturn Motion p.23",
    ("station", "Uranus"): "Herschel Motion p.31",
    ("station", "Neptune"): "Neptune Motion p.35",
    ("station", "Pluto"): "Pluto Motion p.38",

    ("combustion", "Mars"): "Mars Combust Rise Cycle p.6",
    ("combustion", "Mercury"): "Mercury Combust Rise Cycle p.10",
    ("combustion", "Venus"): "Venus Combust Rise Cycle p.14",
    ("combustion", "Jupiter"): "Jupiter Combust Rise Cycle p.20",
    ("combustion", "Saturn"): "Saturn Combust Rise Cycle p.24",

    # Pair tables. Only these three bodies get one; the document has no general
    # conjunction table, and its two pair-specific sections ("Mars Mercury
    # Conjunction p.12", "Venus Mercury Conjunction p.16") are keyed on a PAIR,
    # which this single-body lookup cannot express without mislabelling every
    # other Mars or Venus conjunction. They are deliberately left out.
    ("conjunction", "Uranus"): "Herschel Conjunction with Other Planets p.34",
    ("opposition", "Uranus"): "Herschel Opposition with Other Planets p.34",
    ("conjunction", "Neptune"): "Neptune Conjunction with Other Planets p.37",
    ("opposition", "Neptune"): "Neptune Opposition with Other Planets p.37",
    ("conjunction", "Pluto"):
        "Pluto Conjunction with Other Planets (Except Moon) p.41",
    ("opposition", "Pluto"):
        "Pluto Opposition with Other Planets (Except Moon) p.42",

    ("eclipse", None): "Eclipse",

    # One section per phase, not one per class. The quarters have no section:
    # the document tracks only the syzygies and the first crescent sighting.
    ("lunation", "new_moon"): "Amavasya (No Moon Day) p.48",
    ("lunation", "full_moon"): "Purnima (Full Moon) p.49",

    ("apsis", "apogee"): "Apogee Dates p.44",
    ("apsis", "perigee"): "Perigee Dates p.46",
    ("apsis", "perihelion"): "Perihelion and Aphelion Dates p.47",
    ("apsis", "aphelion"): "Perihelion and Aphelion Dates p.47",

    ("total_day", None): "Total Days in Year",
}

#: The panchang boundary classes have no section of their own in the 2026
#: document, and that is not the same absence as a missing journey table. The
#: document prints these instants to the minute -- 36 tithi boundary times
#: across B65, B73, B74, B75, B76 and B109, and 11 yoga boundary times across
#: B96 and B56 -- but always inside a rule section's own table and never as a
#: series. So they are neither given a SOURCE_SECTIONS title (there is no one
#: section to cite) nor filed under EVIDENCED_IN_SOURCE (which would say the
#: document prints nothing), and carry this flag instead, which says what is
#: actually the case.
PANCHANG_SERIES_FLAG =     "source_prints_these_instants_inside_rule_sections_not_as_a_series"

#: The horizon classes are a third kind of source correspondence again, and the
#: difference from the panchang series is worth stating rather than collapsing.
#: The 2026 document prints no sunrise or sunset table -- but it does print four
#: Mumbai times to the minute, inside the Bhadra section's own prose, where it
#: explains why the reference place matters: "09-Jan (opens 07:06, before Mumbai
#: sunrise 07:13), 27-Apr (opens 06:08, before sunrise 06:16), 28-Jul (opens
#: 18:20, before sunset 19:16) and 29-Sep (opens 06:14, before sunrise 06:29)".
#: Those four are a real fixture and the regression suite uses them. What the
#: document does not have is a section, so there is no title to cite, and it
#: covers Mumbai alone -- it names Mumbai "the reference place declared by this
#: calendar" -- so the New York half of this series has no source counterpart at
#: all. The flag says both of those things instead of leaving the absence to be
#: read as "new for 2027".
HORIZON_SERIES_FLAG = (
    "source_prints_four_mumbai_times_in_the_bhadra_prose_not_as_a_series")

#: The speed-class series is a fourth kind again. The source DOES print the
#: Fast/Normal boundaries -- one table per planet, B120-B127 -- but it prints
#: them as date ranges in a rule section, not as a series of crossings, and it
#: prints them for 2026 only. So a speed_crossing record has a real source
#: counterpart to cite and its instants are still ours, which is exactly what
#: this flag says.
SPEED_CLASS_SERIES_FLAG = (
    "source_prints_these_boundaries_as_date_ranges_not_as_crossings")

#: The section each calibrated body's level was fitted against. Only the three
#: inner planets appear; see SPEED_CLASS_BODIES.
SPEED_CLASS_SOURCE = {
    "Mercury": "Mercury Speed and Vedh p.96",
    "Venus": "Venus Speed and Vedh p.97",
    "Mars": "Mars Speed and Vedh p.94",
}

#: Classes the source demonstrably contains, so a record of that class with no
#: quotable section is a real gap in the source and not a gap in this repo.
#: Flagged so the difference stays auditable instead of looking like "new for
#: 2027". With data/source_2026.html present, every remaining flag means the
#: document prints no section for that body or phase -- the Moon's journey, the
#: quarter moons, Mars's stations -- and no longer means "we could not look".
EVIDENCED_IN_SOURCE = {
    "sign_ingress", "nakshatra_ingress", "navamsa_ingress", "station",
    "combustion", "eclipse", "conjunction", "opposition", "lunation", "apsis",
}
UNNAMED_FLAG = "source_section_not_printed_in_2026"


def source_ref(event_class: str, subject: str | None):
    """(section title, flags) for the 2026 correspondence of a record.

    `subject` is the body for the positional classes and the phase or apsis
    kind for the classes the source splits that way instead.
    """
    title = SOURCE_SECTIONS.get((event_class, subject))
    if title:
        return title, []
    if event_class in EVIDENCED_IN_SOURCE:
        return None, [UNNAMED_FLAG]
    return None, []


# ---------------------------------------------------------------- generators

def sign_ingresses():
    """Every sign change, including retrograde re-entry.

    A planet that stations back across a cusp and returns produces one record
    per crossing. Collapsing them would erase the fact that the cusp was
    crossed three times, which for Saturn in 2027 is the story of the year.
    """
    out = []
    for body in ALL_BODIES:
        for inst, frm, to in ephem.ingresses(body, SPAN_START, SPAN_END, ARC_SIGN):
            retro = (to - frm) % 12 != 1
            title, flags = source_ref("sign_ingress", body)
            # A sign cusp is also a navamsa cusp, so the sampled navamsa lands in
            # the PREVIOUS sign's last navamsa about half the time. The crossing
            # index settles it: forward into the sign's first navamsa, backwards
            # into its last. Without this, vargottama on a sign ingress would be
            # decided by sampling noise rather than by the cusp.
            astro, pflags = ev.positional(
                inst, body,
                sign_from=ephem.SIGNS[frm], sign_to=ephem.SIGNS[to],
                sign_override=ephem.SIGNS[to],
                navamsa_override=ephem.navamsa_at_sign_cusp(to, not retro),
                extra_flags=["retrograde_re_entry"] if retro else [])
            out.append(ev.build(
                "sign_ingress", "ingress/sign", [body], "instant", inst,
                astro,
                ev.qa_for(inst, "A", source_2026_equivalent=title,
                          flags=flags + pflags),
                precision="exact"))
    return out


def nakshatra_ingresses():
    """27-scheme nakshatra changes. Config sets `nakshatra_scheme: 27` for
    transits; the 28-division with Abhijit is reserved for Vedha tables."""
    out = []
    for body in ALL_BODIES:
        for inst, frm, to in ephem.ingresses(body, SPAN_START, SPAN_END,
                                             ARC_NAKSHATRA):
            title, flags = source_ref("nakshatra_ingress", body)
            astro, pflags = ev.positional(inst, body)
            # A nakshatra boundary is not a sign boundary, so it gets its own
            # from/to fields rather than being stuffed into sign_from/sign_to.
            astro = replace(astro,
                            nakshatra_from=ephem.NAKSHATRAS[frm],
                            nakshatra_to=ephem.NAKSHATRAS[to],
                            nakshatra=ephem.NAKSHATRAS[to])
            out.append(ev.build(
                "nakshatra_ingress", "ingress/nakshatra", [body], "instant",
                inst, astro,
                ev.qa_for(inst, "A", source_2026_equivalent=title,
                          flags=flags + pflags),
                precision="exact"))
    return out


def navamsa_ingresses():
    """D9 changes for every body except the Moon."""
    out = []
    for body in NAVAMSA_BODIES:
        for inst, frm, to in ephem.ingresses(body, SPAN_START, SPAN_END,
                                             ARC_NAVAMSA):
            title, flags = source_ref("navamsa_ingress", body)
            # These are D9 divisions, not rasi signs. Writing them into
            # sign_from/sign_to would make a Saturn-in-Pisces record claim it
            # had just entered Sagittarius. navamsa_override carries the
            # authoritative crossing index into the record AND sets the D9
            # dignity from it, the same way sign_override does one chart up --
            # so this record's dignity is the dignity of the chart it is a
            # record of, and the rashi dignity stays under its own name.
            # ...and the rashi sign is taken from the same crossing index for
            # the same reason: every ninth navamsa cusp IS a sign cusp, and there
            # the sampled rashi sign lands on the far side. Each sign is nine
            # whole navamsas, so the arc index gives the sign exactly.
            astro, pflags = ev.positional(
                inst, body,
                navamsa_from=ephem.SIGNS[frm % 12],
                navamsa_to=ephem.SIGNS[to % 12],
                navamsa_override=ephem.SIGNS[to % 12],
                sign_override=ephem.sign_of_navamsa_index(to))
            out.append(ev.build(
                "navamsa_ingress", "ingress/navamsa", [body], "instant", inst,
                astro,
                ev.qa_for(inst, "A", source_2026_equivalent=title,
                          flags=flags + pflags),
                precision="exact"))
    return out


def tithi_ingresses():
    """All 30 tithi boundaries of every lunation in the span.

    A tithi is a 12-degree step of the Moon-Sun elongation, bisected to the
    second -- the method the 2026 source states for its own Bhadra windows,
    applied to twice the karana's arc. Eight of the Bhadra section's sixteen
    January boundaries are also tithi boundaries (the even multiples of 6
    degrees), and this series reproduces all eight within 25 seconds, which is
    the same agreement the Bhadra check itself records.

    Certainty A, and frame-free with it: elongation is a DIFFERENCE of two
    longitudes, so the ayanamsha subtracts from both and cancels. Recomputed
    under Lahiri, Krishnamurti, Raman, Fagan-Bradley and in the tropical frame,
    every one of these instants is identical to the second.
    """
    out = []
    for b in pn.tithi_boundaries(SPAN_START, SPAN_END):
        title, flags = source_ref("tithi_ingress", None)
        # The astronomy block is the Moon's. The Sun is the other half of the
        # angle and is named in `bodies`, but a block carrying two bodies'
        # positions in one set of fields is the merge this schema exists to
        # prevent, so the block names whose position it reports.
        astro, pflags = ev.positional(b.instant, "Moon")
        astro = replace(astro,
                        tithi_from=b.num_from, tithi_to=b.num_to,
                        tithi_name_from=b.name_from, tithi_name_to=b.name_to,
                        paksha_from=b.paksha_from, paksha_to=b.paksha_to)
        out.append(ev.build(
            "tithi_ingress", "ingress/tithi", ["Moon", "Sun"], "instant",
            b.instant, astro,
            ev.qa_for(b.instant, "A", source_2026_equivalent=title,
                      flags=flags + pflags + [
                          PANCHANG_SERIES_FLAG,
                          "astronomy_block_body=Moon",
                          "frame_free_elongation_ayanamsha_cancels"]),
            precision="exact",
            # The instant IS the cusp, so a sampled panchang lands on the far
            # side of it about half the time. The crossing index settles it,
            # exactly as sign_override settles a sign ingress one layer up.
            panchang_override={"tithi": b.num_to, "tithi_name": b.name_to,
                               "paksha": b.paksha_to},
            id_suffix=f"t{b.num_to:02d}"))
    return out


def yoga_ingresses():
    """All 27 yoga boundaries of every turn of the Moon-Sun SUM in the span.

    Certainty A, but NOT for the tithi's reason, and the difference is carried
    on every record rather than left to be assumed. A yoga is the sum of the
    two longitudes, so the ayanamsha subtracts twice and cancels nothing: a
    yoga boundary is exactly as ayanamsha-dependent as a sign ingress, and
    rests on the same evidence -- config's Lahiri, chosen in Step 3 because it
    alone reproduces the source.

    Measured against the source rather than argued: the eleven yoga boundary
    times printed in B96 and B56 come back within 64 seconds under Lahiri, 22
    minutes under Krishnamurti, 3h17m under Fagan-Bradley and 5h24m under
    Raman. Read tropically they do not merely shift -- they land on different
    yogas entirely (4, 21 and 22 in place of 17, 18 and 27), so the source's
    yoga is sidereal and the frame is not a matter of taste.
    """
    out = []
    for b in pn.yoga_boundaries(SPAN_START, SPAN_END):
        title, flags = source_ref("yoga_ingress", None)
        astro, pflags = ev.positional(b.instant, "Moon")
        astro = replace(astro,
                        yoga_from=b.num_from, yoga_to=b.num_to,
                        yoga_name_from=b.name_from, yoga_name_to=b.name_to)
        out.append(ev.build(
            "yoga_ingress", "ingress/yoga", ["Moon", "Sun"], "instant",
            b.instant, astro,
            ev.qa_for(b.instant, "A", source_2026_equivalent=title,
                      flags=flags + pflags + [
                          PANCHANG_SERIES_FLAG,
                          "astronomy_block_body=Moon",
                          "ayanamsha_dependent_sum_of_longitudes"]),
            precision="exact",
            panchang_override={"yoga": b.name_to},
            id_suffix=f"y{b.num_to:02d}"))
    return out


def sunrises_and_sunsets():
    """The Sun's rise and set at every configured venue, every civil day.

    The third event class, and the first one that is not a fact about the sky.
    A tithi boundary is an angle reaching an exact multiple of twelve degrees:
    it happens once and the whole Earth shares the instant, which is why those
    records carry no location and why asking for one would be a category error.
    A rise or a set is the opposite. It is a LOCATION PROPERTY -- the Sun meets
    one horizon at one place, at a time no other place shares -- so every record
    below carries its venue explicitly, and `events.LOCATION_REQUIRED` makes a
    location-free one a build error rather than a Mumbai one by default.

    Both venues are generated. Neither is a fallback for the other, and the
    primary role in config does not make Mumbai a default here: the 2026 source
    declares Mumbai as its own reference place, which is a fact about the
    source and not a rule about this layer.

    **Certainty B, and this is the class that earns the grade.** A tithi ingress
    is A because the angle is the definition. A rise is not: it depends on which
    part of the disc is taken to touch the horizon, on whether refraction is
    applied, and on the horizon's own height. The four conventions swing a
    Mumbai sunrise by about four and a half minutes. Step 3's kalamsha work
    pinned disc-centre with no refraction, and that is the one used here -- the
    pair has to agree, because kalamsha is the gap between a planet's rise and
    the Sun's, and a gap measured between two different conventions is not a
    gap. `panchang.RISE_SET_CONVENTION` is the single place it is stated and
    every record repeats it, so no reader has to know which build produced the
    file to know what the time means.
    """
    out = []
    for loc_key, loc in CONF["locations"].items():
        tz = ZoneInfo(loc["tz"])
        title, flags = source_ref("sunrise", None)
        geo = f"{loc['lat']:.4f},{loc['lon']:.4f},{loc['alt']}"
        # Candidate LOCAL dates, one venue's calendar at a time, widened a day
        # at each end so a venue whose civil day straddles the span edge is not
        # silently clipped. Membership is then decided by the instant itself.
        day = SPAN_START.astimezone(tz).date() - dt.timedelta(days=1)
        last = SPAN_END.astimezone(tz).date() + dt.timedelta(days=1)
        while day <= last:
            for event_class, fn in (("sunrise", pn.sunrise),
                                    ("sunset", pn.sunset)):
                inst = fn(day, loc)
                if not SPAN_START <= inst < SPAN_END:
                    continue        # outside the generated period
                astro, pflags = ev.positional(inst, "Sun")
                out.append(ev.build(
                    event_class, f"horizon/{event_class}", ["Sun"], "instant",
                    inst, astro,
                    ev.qa_for(inst, "B", source_2026_equivalent=title,
                              flags=flags + pflags + [
                                  HORIZON_SERIES_FLAG,
                                  f"rise_set_convention={pn.RISE_SET_CONVENTION}",
                                  "disc=center",
                                  "refraction=none",
                                  f"horizon_geo_lat_lon_alt={geo}",
                                  f"civil_date_at_venue={day:%Y-%m-%d}"]),
                    precision="exact", location=loc_key,
                    id_suffix=loc_key))
            day += dt.timedelta(days=1)
    return out


def stations():
    """Retrograde and direct stations.

    Certainty B, per config's own label: a station is definition-sensitive
    because longitude is stationary to second order there.
    """
    out = []
    for body in STATION_BODIES:
        for inst, kind in ephem.stations(body, SPAN_START, SPAN_END):
            title, flags = source_ref("station", body)
            astro, pflags = ev.positional(inst, body)
            astro = replace(astro, motion="stationary")
            out.append(ev.build(
                "station", f"motion/station_{kind}", [body], "instant", inst,
                astro,
                ev.qa_for(inst, "B", source_2026_equivalent=title,
                          flags=flags + pflags + [f"station={kind}"]),
                precision=STATION_PRECISION.get(body, "hours"),
                id_suffix=kind))
    return out


def combustions():
    """Asta and udaya by classical kalamsha, evaluated at the primary location.

    Carries the kalamsha value, the direction, and the per-body precision_days
    from config -- which is a measured limit from calibration scatter, not a
    target.
    """
    out = []
    for body in COMBUST_BODIES:
        for e in cb.find_events(body, SPAN_START.date(), SPAN_END.date()):
            title, flags = source_ref("combustion", body)
            astro, pflags = ev.positional(e.instant, body)
            lo, hi = civil_day_bounds(e.instant.date(), IST)
            out.append(ev.build(
                "combustion", f"visibility/{e.kind}", [body, "Sun"],
                "civil_day", lo, astro,
                ev.qa_for(e.instant, e.certainty,
                          precision_days=e.precision_days,
                          source_2026_equivalent=title,
                          flags=flags + pflags + [
                              f"kalamsha={e.kalamsha}",
                              f"direction={e.direction}",
                              f"method={CONF['combustion']['method']}"]),
                t_end=hi, precision="date_only", location="mumbai",
                id_suffix=e.kind))
    return out


def speed_class_crossings():
    """Where each calibrated planet enters and leaves Fast, and where it turns.

    The speed-class series, and the fourth of the boundary series Step 3 grew
    late (after the tithi/yoga pair, then the horizon pair). Two kinds of
    crossing, emitted as TWO CLASSES so the distinction is structural:

    * ``speed_crossing`` -- the speed crosses the planet's calibrated
      Fast/Normal level. ``motion/fast_start`` rising, ``motion/fast_end``
      falling. Only Mercury, Venus and Mars have a level.
    * ``station`` -- the speed crosses zero. Already emitted by `stations()`;
      listed here because it is the RETROGRADE boundary, and separating the two
      kinds is what makes a ``Retrograde -> Normal`` transition impossible to
      mistake for a Fast/Normal one. That confusion was a real bug in the
      calibration this series comes from, and it is now prevented by the shape
      of the output rather than by remembering not to make it.

    Certainty B. Not because the instant is imprecise -- it is bisected to the
    second like every other crossing -- but because the LEVEL is a calibrated
    quantity with an interval, and `precision_days` on each record is that
    interval's width divided by the acceleration at the crossing. Mercury's
    0.08 d is small; Venus's and Mars's 2.00 d say the level is only good to
    about two days of boundary.
    """
    out = []
    for body, (level, interval, pdays, section) in SPEED_CLASS_BODIES.items():
        title = SPEED_CLASS_SOURCE.get(body)
        for inst, kind, family, lvl in ephem.speed_crossings(
                body, SPAN_START, SPAN_END, level):
            if kind == "station":
                continue          # stations() already emits these
            astro, pflags = ev.positional(inst, body)
            astro = replace(
                astro, speed_threshold=level,
                speed_threshold_interval=[interval[0], interval[1]],
                speed_crossing_kind="threshold",
                speed_crossing_direction=("into_fast"
                                          if family.endswith("start")
                                          else "out_of_fast"))
            out.append(ev.build(
                "speed_crossing", family, [body], "instant", inst, astro,
                ev.qa_for(inst, "B", precision_days=pdays,
                          source_2026_equivalent=title,
                          flags=pflags + [
                              SPEED_CLASS_SERIES_FLAG,
                              f"threshold={level}",
                              f"threshold_interval={interval[0]}..{interval[1]}",
                              f"precision_days={pdays}",
                              f"calibrated_against={section}"]),
                precision="exact",
                id_suffix=family.split("/")[-1]))
    return out


def eclipses():
    """All solar and lunar eclipses in the span.

    Global contact times and the circumstances visible from India are stored
    separately in the time layer, never merged. Penumbral lunar eclipses are
    included and flagged low-impact, per config.
    """
    out = []
    penumbral_impact = CONF["eclipses"]["penumbral_impact"]

    for e in ephem.solar_eclipses_detailed(SPAN_START, SPAN_END, PRIMARY):
        g = e["global"]
        title, flags = source_ref("eclipse", None)
        astro, pflags = ev.positional(g["max"], "Sun")
        astro = replace(astro, eclipse_type=e["type"], magnitude=e["magnitude"])
        if e["central"]:
            flags.append("central")
        if not e["local"].get("visible"):
            flags.append("not_visible_from_india")
        out.append(ev.build(
            "eclipse", "eclipse/solar", ["Sun", "Moon"], "window",
            g["begin"] or g["max"], astro,
            ev.qa_for(g["max"], "A", source_2026_equivalent=title,
                      flags=flags + pflags),
            t_end=g["end"] or g["max"], precision="exact", location="mumbai",
            contacts_global=g, contacts_local=e["local"]))

    for e in ephem.lunar_eclipses_detailed(SPAN_START, SPAN_END, PRIMARY):
        g = e["global"]
        title, flags = source_ref("eclipse", None)
        astro, pflags = ev.positional(g["max"], "Moon")
        astro = replace(astro, eclipse_type=e["type"], magnitude=e["magnitude"])
        if e["penumbral"]:
            flags += ["penumbral", f"impact={penumbral_impact}"]
        if not e["local"].get("visible"):
            flags.append("not_visible_from_india")
        out.append(ev.build(
            "eclipse", "eclipse/lunar", ["Moon", "Sun"], "window",
            g["penumbral_begin"] or g["max"], astro,
            ev.qa_for(g["max"], "A", source_2026_equivalent=title,
                      flags=flags + pflags),
            t_end=g["penumbral_end"] or g["max"], precision="exact",
            location="mumbai", contacts_global=g, contacts_local=e["local"]))
    return out


def lunations():
    """New moon, both quarters, full moon.

    The Sun-Moon conjunction and opposition live here and only here. They are
    the new and full moon; emitting them again in the conjunction class would
    be the same event typed twice.
    """
    # An eclipse happens at a syzygy, so every eclipse coincides with a new or
    # full moon. They are still two events -- the syzygy is an alignment, the
    # eclipse is a shadow passage with its own contacts and magnitude -- but a
    # reader must not take them for independent ones, so the lunation record
    # points at the eclipse rather than staying silent about it.
    maxima = [e["global"]["max"] for e in
              ephem.solar_eclipses_detailed(SPAN_START, SPAN_END, PRIMARY)]
    maxima += [e["global"]["max"] for e in
               ephem.lunar_eclipses_detailed(SPAN_START, SPAN_END, PRIMARY)]

    out = []
    for inst, phase in ephem.lunations(SPAN_START, SPAN_END):
        title, flags = source_ref("lunation", phase)
        astro, pflags = ev.positional(inst, "Moon")
        if any(abs((m - inst).total_seconds()) < 12 * 3600 for m in maxima):
            flags.append("coincides_with_eclipse")
        out.append(ev.build(
            "lunation", f"lunation/{phase}", ["Moon", "Sun"], "instant", inst,
            astro,
            ev.qa_for(inst, "A", source_2026_equivalent=title,
                      flags=flags + pflags + [phase]),
            precision="exact", id_suffix=phase))
    return out


def total_days():
    """dd + mm == yy. Arithmetic, no ephemeris, certainty A per config.

    Calendar year only: the rule is defined against the two-digit year, so a
    carry-in or carry-out day would be a different year's rule.
    """
    out = []
    title, flags = source_ref("total_day", None)
    for day in pn.total_days(YEAR):
        lo, hi = civil_day_bounds(day, IST)
        astro, pflags = ev.positional(lo, "Sun")
        out.append(ev.build(
            "total_day", "calendar/total_day", [], "civil_day", lo, astro,
            ev.qa_for(lo, CONF["total_days"]["certainty"],
                      source_2026_equivalent=title,
                      flags=flags + pflags
                      + [f"rule={CONF['total_days']['rule']}"]),
            t_end=hi, precision="date_only", location="mumbai"))
    return out


def conjunctions_and_oppositions():
    """Exact conjunctions and oppositions among the bodies config names.

    The Moon is excluded by config, which records the source's own reason: its
    section headings say "Except Moon" and no conjunction or opposition table
    in the document carries a Moon row.
    """
    out = []
    for a, b in itertools.combinations(CONJ_BODIES, 2):
        for event_class, angle in (("conjunction", 0.0), ("opposition", 180.0)):
            for inst in ephem.aspect_exact(a, b, angle, SPAN_START, SPAN_END):
                title, flags = source_ref(event_class, a)
                if title is None:
                    title, flags = source_ref(event_class, b)
                astro, pflags = ev.positional(inst, a)
                out.append(ev.build(
                    event_class, f"aspect/{event_class}", [a, b], "instant",
                    inst, astro,
                    ev.qa_for(inst, "A", source_2026_equivalent=title,
                              flags=flags + pflags + [
                                  f"separation_deg={angle:.0f}",
                                  f"astronomy_block_body={a}"]),
                    precision="exact"))
    return out


def apsides():
    """Moon apogee and perigee, Sun perihelion and aphelion.

    Certainty B and no claim of exactness: an apsis is a turning point in
    distance, so distance is flat around it and the instant is the loosely
    determined quantity, exactly as at a station. The Moon's apsides are quoted
    to the minute and the Sun's to the hour, which is as far as the geometry
    honestly supports.
    """
    out = []
    series = [("Moon", ephem.moon_apsides(SPAN_START, SPAN_END), "minutes"),
              ("Sun", ephem.sun_apsides(SPAN_START, SPAN_END), "hours")]
    for body, found, precision in series:
        for inst, kind in found:
            title, flags = source_ref("apsis", kind)
            astro, pflags = ev.positional(inst, body)
            out.append(ev.build(
                "apsis", f"orbit/{kind}", [body], "instant", inst, astro,
                ev.qa_for(inst, "B", source_2026_equivalent=title,
                          flags=flags + pflags + [kind]),
                precision=precision, id_suffix=kind))
    return out


GENERATORS = [
    ("sign ingresses", sign_ingresses),
    ("nakshatra ingresses", nakshatra_ingresses),
    ("navamsa ingresses", navamsa_ingresses),
    ("tithi ingresses", tithi_ingresses),
    ("yoga ingresses", yoga_ingresses),
    ("sunrise / sunset", sunrises_and_sunsets),
    ("stations", stations),
    ("speed-class crossings", speed_class_crossings),
    ("combust / rise", combustions),
    ("eclipses", eclipses),
    ("lunations", lunations),
    ("total days", total_days),
    ("conjunctions / oppositions", conjunctions_and_oppositions),
    ("apsides", apsides),
]


# -------------------------------------------------------------------- output

def main() -> int:
    backend = ephem.init()
    print(f"ephemeris backend: {backend}")
    print(f"span: {SPAN_START.astimezone(IST):%d-%b-%Y %H:%M} IST "
          f"-> {SPAN_END.astimezone(IST):%d-%b-%Y %H:%M} IST\n")

    records = []
    for label, fn in GENERATORS:
        t0 = time.time()
        got = fn()
        records += got
        print(f"  {label:<28} {len(got):>5}   {time.time() - t0:6.1f}s")

    records.sort(key=lambda r: r.sort_key())

    dupes = [i for i, n in collections.Counter(r.id for r in records).items()
             if n > 1]
    if dupes:
        raise SystemExit(f"duplicate ids: {dupes[:5]}")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "year": YEAR,
            "generated_layer": "astronomy",
            "engine": ev.ENGINE,
            "ephemeris_backend": backend,
            "ayanamsha": CONF["ayanamsha"],
            "node": CONF["node"],
            "nakshatra_scheme": CONF["nakshatra_scheme"],
            "span_start_utc": SPAN_START.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "span_end_utc": SPAN_END.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "primary_tz": CONF["display"]["primary_tz"],
            "secondary_tz": CONF["display"]["secondary_tz"],
            "record_count": len(records),
        },
        "records": [r.as_dict() for r in records],
    }
    with OUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")

    counts = collections.Counter(r.event_class for r in records)
    certainty = collections.Counter(r.qa.data_certainty for r in records)
    width = max(len(k) for k in counts)
    lines = [
        f"FinAstro {YEAR} - astronomy layer",
        f"generated by       {ev.ENGINE}",
        f"ephemeris backend  {backend}",
        f"ayanamsha          {CONF['ayanamsha']}",
        f"node               {CONF['node']}",
        f"span               {SPAN_START.astimezone(IST):%d-%b-%Y}"
        f" -> {SPAN_END.astimezone(IST):%d-%b-%Y} (IST)",
        "",
        "records per event_class:",
    ]
    lines += [f"  {k.ljust(width)}  {counts[k]:>5}" for k in sorted(counts)]
    lines += ["", f"  {'TOTAL'.ljust(width)}  {len(records):>5}", "",
              "records per certainty grade:"]
    lines += [f"  {k}  {certainty[k]:>5}" for k in sorted(certainty)]
    lines.append("")
    OUT_SUMMARY.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{len(records)} records -> {OUT_JSON.relative_to(ROOT)}")
    print(f"summary          -> {OUT_SUMMARY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
