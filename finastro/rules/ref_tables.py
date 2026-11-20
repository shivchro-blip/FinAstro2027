"""Batch 6 -- the reference tables, and the sections no calibration reaches.

TWO KINDS OF SECTION HERE, and neither is a rule in the ordinary sense.

1. THE REFERENCE TABLES (32 sections). "Journey of <planet>", "<planet> Motion",
   "<planet> Constellation (Nakshtra)" and "<planet> in Navmansh (D9)" are views
   of ingress series the astronomy layer already emits --
   `sign_ingress`, `motion/station`, `nakshatra_ingress`, `navamsa_ingress`.
   They are ported as rules so that every catalogue-B section has a status, and
   each fires one row per record of the series it renders. **They print no
   verdict**: a Journey table states where a planet was and when it moved, and
   nothing about the market, so `verdict_text` is None and that is a correct
   outcome rather than a gap.

   This is confirmation work, not derivation: the survey in
   `build/STEP4_DECISIONS.md` section 12.7 established the mapping by checking
   that each section's table columns are that class's own facts. Two exceptions
   are recorded rather than smoothed and are carried in the notes below -- B49
   "Journey of Pluto" prints NO TABLE at all, and the Constellation tables head
   their nakshatra column "Constellation".

2. THE VEDHA SECTIONS NO CALIBRATION REACHES (13 sections). B125-B127 and
   B131-B141 are the speed-and-vedh and nakshtra-vedh tables for bodies with no
   calibrated level; B128-B130 key on the Moon's and the inner pair's speed
   classes. They are registered `blocked` with the missing input named, which for
   the slow planets and the outers is the slow-planet doctrine and for the Moon
   tables is the absence of any threshold work for the Moon at all.

B116 "Mercury in Paap Kartari" joins B19 and B117 on the benefic/malefic
valence, which is the same missing input for the third time and is registered
here rather than left unported.
"""
from __future__ import annotations

from ..events import GROUND_UNDOCUMENTED
from ..sky import Span, parse
from . import valence as VAL
from .base import blocked, rule
from .catalogue import B

#: Which ingress class each reference shape renders, and the astronomy field
#: that names the position it moved into.
FRAME_OF = {
    "sign_ingress": "sign",
    "nakshatra_ingress": "nakshatra",
    "navamsa_ingress": "navamsa",
}

#: The source calls Uranus "Herschel" throughout, including in these section
#: titles. The astronomy layer emits it under the modern name, so the bridge
#: lives here and every rule that names the source's spelling goes through it.
#: Without it the four Herschel views rendered blank -- the failure mode being
#: that a body which matched no record looks exactly like a quiet year.
SOURCE_BODY_NAME = {"Herschel": "Uranus"}


def _layer_name(body: str) -> str:
    return SOURCE_BODY_NAME.get(body, body)

#: section -> (event class, body). Covers the 10 Journey tables, the 7 Motion
#: tables, the 7 Constellation tables and the 8 Navmansh tables.
REFERENCE_TABLES = {
    # Journey of <planet> -- sign ingresses.
    1: ("sign_ingress", "Sun"),           # Sun Transgression (Sankranti)
    3: ("sign_ingress", "Mars"),
    7: ("sign_ingress", "Mercury"),
    13: ("sign_ingress", "Venus"),
    20: ("sign_ingress", "Jupiter"),
    25: ("sign_ingress", "Saturn"),
    31: ("sign_ingress", "Rahu"),
    34: ("sign_ingress", "Ketu"),
    37: ("sign_ingress", "Herschel"),
    43: ("sign_ingress", "Neptune"),
    49: ("sign_ingress", "Pluto"),        # prints no table; see note
    # <planet> Motion -- stations.
    8: ("motion/station", "Mercury"),
    14: ("motion/station", "Venus"),
    21: ("motion/station", "Jupiter"),
    26: ("motion/station", "Saturn"),
    38: ("motion/station", "Herschel"),
    44: ("motion/station", "Neptune"),
    50: ("motion/station", "Pluto"),
    # <planet> Constellation (Nakshtra) -- nakshatra ingresses.
    23: ("nakshatra_ingress", "Jupiter"),
    28: ("nakshatra_ingress", "Saturn"),
    32: ("nakshatra_ingress", "Rahu"),
    35: ("nakshatra_ingress", "Ketu"),
    39: ("nakshatra_ingress", "Herschel"),
    45: ("nakshatra_ingress", "Neptune"),
    51: ("nakshatra_ingress", "Pluto"),
    # <planet> in Navmansh (D9) -- navamsa ingresses.
    24: ("navamsa_ingress", "Jupiter"),
    29: ("navamsa_ingress", "Saturn"),
    33: ("navamsa_ingress", "Rahu"),
    36: ("navamsa_ingress", "Ketu"),
    40: ("navamsa_ingress", "Herschel"),
    46: ("navamsa_ingress", "Neptune"),
    52: ("navamsa_ingress", "Pluto"),
}

#: Sections that print no table, or whose shape differs from its siblings. Kept
#: apart so the notes can say so without a per-section conditional.
NO_TABLE = {49: "prints no table in the document at all"}
ODD_COLUMNS = {
    28: "heads its nakshatra column 'Constellation' and omits the Sign column "
        "its siblings carry",
    45: "heads its nakshatra column 'Constellation' and omits the End Time "
        "column its siblings carry",
}

#: Sections whose port is withheld because the series they render has not been
#: checked against the source. B5 is a residency rule over a D9 position, not a
#: D9 ingress series, and is recorded in config's `rule_layer_pending`.
NOT_A_VIEW = {
    5: "Mars's rashi windows while its navamsa is Pisces -- a residency rule "
       "over a D9 position, not a D9 ingress series, and the layer emits no Mars "
       "D9 ingress table because the source prints none",
    6: "Vargottam Mars -- needs the D1 and D9 signs to agree at an instant, and "
       "the config already notes the source prints no Mars D9 ingress table to "
       "bound it",
}


def _view(event_class: str, body: str):
    """One row per record of the series this reference table renders.

    PLUS a leading row for the state carried in. The source's own Journey,
    Constellation and Navmansh tables all open with a "Start of the year" row --
    they state where the body WAS before its first movement -- and the Motion
    tables open with a direction that is already in force. So a view renders
    that row too, which is what stops a body that does not cross at all inside
    the span (Uranus, Neptune and Pluto move too slowly; the nodes barely move)
    from rendering as a blank table. An earlier version emitted only crossing
    records and did exactly that.

    The carried-in state is read from the layer, never from the engine: the
    first crossing record names what the body moved out of, and where there is
    no crossing at all the nearest record's own position stands in, with the
    approximation marked on the row.
    """
    def fn(sky):
        out: list[Span] = []
        layer_body = _layer_name(body)
        mine = [r for r in sky.class_records(event_class)
                if layer_body in r["bodies"]]
        if event_class == "motion/station":
            mine = [r for r in mine
                    if r["rule_family"].startswith("motion/station")]

        # ---- the carried-in row
        field = FRAME_OF.get(event_class)
        carried, how = None, None
        if field and mine:
            first = min(mine, key=lambda r: r["time"]["t_start_utc"])
            carried = first["astronomy"].get(f"{field}_from")
            how = "read_from_the_first_ingresss_from_field"
        if carried is None:
            # No crossing of this frame in the span, or a Motion view. Fall back
            # to the body's own state on the record nearest the span start --
            # still the astronomy layer, and marked as an approximation so no
            # reader mistakes it for a crossing.
            allrec = [r for r in sky.records if r["bodies"]
                      and r["bodies"][0] == layer_body]
            if allrec:
                near = min(allrec,
                           key=lambda r: abs((parse(r["time"]["t_start_utc"])
                                              - sky.span_start).total_seconds()))
                astro = near["astronomy"]
                carried = (astro.get(field) if field
                           else astro.get("motion"))
                how = ("nearest_record_position_no_crossing_in_span"
                       if field else "nearest_record_motion_no_station_in_span")
        if carried is not None:
            # A crossing row is dated where the crossing happened. A CARRIED-IN
            # row is a statement about the whole span, because there is no
            # crossing to date it at -- so it is anchored at the span end. That
            # anchor is a choice, and this is the reasoning: the state holds
            # throughout, so any day in the span is equally true of it, and the
            # span end is the only one `fire` will not drop. Anchoring at the
            # span start put it in calendar 2026 and rendered the section blank.
            # A body that DOES cross keeps the start anchor, because a 2026 row
            # would then be noise beside its real crossings.
            anchor = sky.span_end if not mine else sky.span_start
            if not mine:
                # ...and the span end is itself outside the calendar year in
                # IST (it is 01-Feb-2028), so it would be filtered out too. The
                # named year's own first instant is the one anchor guaranteed to
                # be inside the year and inside every span this layer emits.
                from ..config import CONF as _C
                from ..timezones import IST as _IST
                import datetime as _dt
                anchor = _dt.datetime(_C["year"], 1, 1, tzinfo=_IST)
            # `anchored`. The paragraph above describes a CHOICE, and until
            # 15-Sep-2026 the row had no way to say so: these twelve rows
            # rendered a clock time at the anchor, stating a crossing that by
            # definition did not occur -- a carried-in row exists precisely
            # BECAUSE the body did not cross. See Span.precision.
            out.append(Span(anchor, anchor, {
                "at": anchor.strftime("%d-%b-%Y"),
                "carried_in": True,
                "position": carried,
                "sign": (mine[0]["astronomy"].get("sign") if mine else None),
                "nakshatra": (mine[0]["astronomy"].get("nakshatra")
                              if mine else None),
                "how_read": how,
                "anchor": ("span_end_because_the_state_holds_throughout"
                           if not mine else "span_start_before_the_first_crossing"),
            }, precision="anchored"))
        elif not mine:
            return out          # nothing known about this body at all

        # ---- one row per crossing
        for r in mine:
            t = parse(r["time"]["t_start_utc"])
            astro = r["astronomy"]
            d = {"at": r["time"]["start_stamp"]["ist_date"],
                 "bodies": list(r["bodies"]),
                 "carried_in": False,
                 "sign": astro.get("sign"),
                 "nakshatra": astro.get("nakshatra")}
            if field:
                d["position"] = astro.get(field)
                d["from"] = astro.get(f"{field}_from")
            if event_class == "motion/station":
                d["station"] = r["rule_family"].rsplit("_", 1)[-1]
                d["motion"] = astro.get("motion")
            out.append(Span(t, t, d))
        return out
    return fn


for _b, (_cls, _body) in sorted(REFERENCE_TABLES.items()):
    _sec = B(_b)
    _notes = (f"{_body}'s {_cls.replace('_ingress', ' ingress').replace('/', ' ')} "
              "series, rendered as this section's table renders it. The section "
              "prints NO VERDICT -- it states where the body was and when it "
              "moved, and nothing about the market -- so verdict_text is None, "
              "which is the correct outcome for a reference table and not a "
              "gap.")
    if _b in NO_TABLE:
        _notes += (" RECORDED ODDITY: this section " + NO_TABLE[_b] +
                   ", so the rule renders a series the source never tabulated "
                   "here. The class is still evidenced: the source prints the "
                   "same series for the other nine bodies and names Pluto in "
                   "its own planet lists.")
    if _b in ODD_COLUMNS:
        _notes += " COLUMN NOTE: it " + ODD_COLUMNS[_b] + "."
    rule(
        id=f"b{_b:03d}_reference_view_{_body.lower()}",
        section=_sec,
        rule_family="reference/view",
        condition_text=_sec.title,
        condition_from="title",
        inputs=(f"ingress/{FRAME_OF[_cls]}" if _cls in FRAME_OF
                else "motion/station",),
        flags=("reference_table_view_of_an_emitted_series",
               "section_prints_no_verdict"),
        notes=_notes,
    )(_view(_cls, _body))


for _b, _why in NOT_A_VIEW.items():
    blocked(
        id=f"b{_b:03d}_not_an_ingress_view",
        section=B(_b),
        rule_family="reference/not_a_view",
        condition_text=B(_b).title,
        condition_from="title",
        inputs=("source_selection_rule",),
        data_certainty="C",
        certainty_ground=GROUND_UNDOCUMENTED,
        missing_inputs=(_why,),
        flags=("not_a_view_of_an_emitted_series",),
        notes="Registered so the section has a status rather than an omission. "
              "It looks like its neighbours -- it sits between two Navmansh "
              "tables -- and it is not one of them, which is exactly the kind of "
              "thing an omission would hide.",
    )


# ------------------------------------- B2: the Sun's nakshatra journey
# THE LORD SEQUENCE IS SLICED FROM THIS SECTION'S OWN TABLE, not recalled. B2
# prints 28 rows -- one per sidereal day of the Sun's circuit, closing back on
# Purva Shada -- each carrying its nakshatra and that nakshatra's lord. So the
# document is its own witness for the sequence, and the table below is a slice
# of it: nine lords cycling 3,3,3,3,3,3,3,3,3 across the 27 nakshatras. A
# recalled Vimshottari sequence would have been an unchecked transcription,
# which is the error this project exists to avoid.
_NAK_LORDS = {}


def _slice_lord_table():
    rows = B(2).tables[0].rows
    for _r in rows:
        _nak, _lord = _r[0].strip(), _r[3].strip()
        # The table closes on Purva Shada, so the repeat is dropped rather than
        # overwriting: 27 distinct nakshatras and 28 printed rows.
        _NAK_LORDS.setdefault(_nak, _lord)
    return _NAK_LORDS


_slice_lord_table()
assert len(_NAK_LORDS) == 27, (
    f"B2's table yielded {len(_NAK_LORDS)} nakshatras, expected 27 -- the "
    "slice is wrong and the lord map must not be used")


def _sun_nakshatra_journey(sky):
    """One row per nakshatra the Sun holds, with that nakshatra's lord.

    The RELATIONSHIP column is deliberately not carried. It states an aspect
    between the Sun and the nakshatra's lord, and rendering it needs to know
    which aspect the source is measuring -- it prints Conjunction, Sextile,
    Trine, Semi-Sextile, Opposition and Own, which is an angular scale, but
    nothing says whether it is the exact aspect or one under an orb. Guessing
    would be an authored step, so the column is named as missing instead.
    """
    out: list[Span] = []
    for s in sky.spans("Sun", "nakshatra"):
        out.append(Span(s.start, s.start, {
            "nakshatra": s.value,
            "nakshatra_lord": _NAK_LORDS.get(s.value),
            "relationship": None,
            "relationship_unavailable_because":
                "the source states an aspect to the nakshatra's lord and does "
                "not say whether it is exact or under an orb",
            "at": s.start.strftime("%d-%b-%Y"),
        }, open_start=s.open_start))
    return out


rule(
    id="b002_sun_nakshatra_journey",
    section=B(2),
    rule_family="reference/sun_nakshatra",
    condition_text=B(2).title,
    condition_from="title",
    inputs=("ingress/nakshatra",),
    flags=("lord_sequence_sliced_from_this_section's_own_table",
           "relationship_column_not_carried_see_notes"),
    notes="The Sun's nakshatra residencies with each nakshatra's lord. The lord "
          "sequence is sliced from this section's own 28 printed rows rather "
          "than recalled from the Vimshottari cycle, so the document witnesses "
          "its own table. The RELATIONSHIP column is not rendered: it is an "
          "aspect between the Sun and the nakshatra's lord and the source never "
          "says whether it measures the exact aspect or one under an orb, so "
          "each row carries relationship=None with the reason rather than a "
          "value computed from an unstated convention."
)(_sun_nakshatra_journey)


# ------------------------------------------- B30: the slow-planet doctrine
blocked(
    id="b030_demoted_shadow_speed_of_saturn",
    section=B(30),
    rule_family="orbit/demoted_speed",
    condition_text=B(30).title,
    condition_from="title",
    inputs=("source_selection_rule",),
    data_certainty="C",
    certainty_ground=GROUND_UNDOCUMENTED,
    missing_inputs=(
        "a rule, not merely the interval. B30 states when Saturn is in Demoted "
        "or Shadow Speed -- from 11-Dec-2026 until it crosses back over 20 deg "
        "31' of Pisces direct on 15-Mar-2027 -- and its two printed values are "
        "VERIFIED to the arcminute (the engine puts Saturn at 20.508963 deg on "
        "27-Jul-2026 and 20.507990 deg on 15-Mar-2027, and at 13.694991 deg on "
        "11-Dec-2026). What the section never states is what makes a planet "
        "Demoted or Shadow: it names the band and the two dates and no "
        "condition. So the interval can be reproduced and the rule that "
        "generates it in another year cannot",
    ),
    flags=("interval_verified_to_the_arcminute",
           "the_section_gives_dates_and_a_band_not_a_rule"),
    notes="Registered because it is the section the slow-planet blocks point "
          "at, and leaving it unported would have made the thing they cite "
          "invisible. It is not a threshold and it is not a rule: it is a "
          "worked example for one year. Reported in build/RULE_LAYER_STATUS.md "
          "under the slow-planet doctrine.",
)

rule(
    id="b116_mercury_in_paap_kartari",
    section=B(116),
    rule_family="colocation/paap_kartari",
    condition_text=B(116).title,
    condition_from="title",
    inputs=("order/neighbours", "ingress/sign", "panchang/tithi"),
    notes="PORTED 20-Nov-2026 (blocked on valence until then). Valence and the "
          "hemming rule are config `valence` (Reference_materials Ch 0 plus the "
          "document's own rows); the neighbours are the astronomy layer's "
          "`neighbour_change` series. "
          + ("VERIFIED: all 9 printed 2026 rows reproduce on both planets; one "
             "start (14-Jul-26) is printed a day after the Sun-Mercury "
             "conjunction that opens it. Two short unprinted windows are "
             "carried (13-18 Feb, Rahu|Saturn; 20-Apr, 11 h)."
             if 116 == 116 else
             "VERIFIED: the printed 25-Aug to 12-Nov-26 window (split at "
             "Jupiter's 31-Oct sign change) reproduces on Mars|Ketu. Two "
             "unprinted windows are carried: 13-29 Jul (Sun|Ketu) and one from "
             "16-Nov the printed table stops before."),
)(lambda sky: VAL.paap_kartari(sky, "Mercury"))


# ------------------------- the Vedha sections no calibration reaches
# The speed-and-vedh and nakshtra-vedh tables for bodies with no calibrated
# level. Each is a real section with a real condition that cannot be evaluated.
_UNREACHED = {
    125: ("Herschel", "outer_planet_no_threshold"),
    126: ("Neptune", "outer_planet_no_threshold"),
    127: ("Pluto", "outer_planet_no_threshold"),
    129: ("Venus", "keyed_on_a_withdrawn_single_point_fit"),
    130: ("Mercury", "keyed_on_mercury_which_is_calibrated_but_out_of_scope"),
    131: ("Sun", "no_threshold_work_for_this_body"),
    137: ("Rahu", "no_threshold_work_for_this_body"),
    138: ("Ketu", "no_threshold_work_for_this_body"),
    139: ("Herschel", "outer_planet_no_threshold"),
    140: ("Neptune", "outer_planet_no_threshold"),
    141: ("Pluto", "outer_planet_no_threshold"),
}

_REASON = {
    "outer_planet_no_threshold":
        "a calibrated speed level for an outer planet. No outer planet has one "
        "-- the source prints no Fast/Normal boundaries for them at all -- and "
        "B30 shows the slow planets answer to a longitude doctrine instead, so "
        "there is no level to fit and no class to select a direction from",
    "no_threshold_work_for_this_body":
        "a calibrated speed level for this body. The threshold calibration "
        "covered Mercury, Venus and Mars only; the Sun has no Fast/Normal table "
        "in the source and the nodes have none either, so no level exists to fit",
    "keyed_on_a_withdrawn_single_point_fit":
        "the same input that withdrew B123: Venus's level was fitted to a single "
        "crossing and carries no evidence, so the class this table keys on is "
        "unearned",
    "keyed_on_the_moon_not_a_calibrated_body":
        "a speed level for the Moon. This table keys on the Moon's class and no "
        "threshold work has been done for the Moon at all -- it has no "
        "Fast/Normal table in the source",
    "keyed_on_mercury_which_is_calibrated_but_out_of_scope":
        "scope rather than an input: this table's key (Mercury's class) IS "
        "calibrated and overdetermined, so the section is portable in principle "
        "and was not ported in this batch. Registered blocked rather than "
        "omitted so the gap is visible as scope and not mistaken for a missing "
        "input",
}

for _b, (_body, _why) in sorted(_UNREACHED.items()):
    blocked(
        id=f"b{_b:03d}_{_body.lower()}_vedha_unreached",
        section=B(_b),
        rule_family="vedha/unreached",
        condition_text=B(_b).title,
        condition_from="title",
        inputs=("source_selection_rule",),
        data_certainty="C",
        certainty_ground=GROUND_UNDOCUMENTED,
        missing_inputs=(_REASON[_why],),
        flags=(f"unreached_because={_why}",),
        notes="Registered so the Vedha family's coverage is visible rather than "
              "implied. The section is a real condition with a real table; what "
              "is absent is the level its direction branch keys on.",
    )

# B128 is the Moon-Rahu pair and keys on the Moon, like B130.
blocked(
    id="b128_moon_rahu_vedha_unreached",
    section=B(128),
    rule_family="vedha/unreached",
    condition_text=B(128).title,
    condition_from="title",
    inputs=("source_selection_rule",),
    data_certainty="C",
    certainty_ground=GROUND_UNDOCUMENTED,
    missing_inputs=(_REASON["keyed_on_the_moon_not_a_calibrated_body"],),
    flags=("unreached_because=keyed_on_the_moon_not_a_calibrated_body",),
    notes="Chandra Rahu Vedh prints Front/Left/Right Vedh windows and keys them "
          "on the Moon's speed class, for which no level exists.",
)
