"""Sanity harness for the generated 2027 astronomy layer.

These are not unit tests of arithmetic. They are the checks that would catch
real corruption of build/astronomy_2027.json: a silently dropped body, an
ingress that drifted off its boundary, a station that is not a station, a
dignity that started varying by degree, the Moon leaking back into the
conjunction class, or the year-boundary truncation that disfigured the 2026
source.

Every positional assertion recomputes from finastro/ephem.py rather than
trusting the file, so a record whose time was corrupted fails against the
engine and not against another copy of itself.

Run:  python tests/test_2027_astronomy.py      (after python build_2027.py)
"""
from __future__ import annotations

import collections
import datetime as dt
import itertools
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from finastro import ephem                      # noqa: E402
from finastro import events as ev               # noqa: E402
from finastro.events import SPAN_START, SPAN_END  # noqa: E402
from finastro.config import CONF                # noqa: E402
from finastro.timezones import IST, UTC, stamp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "build" / "astronomy_2027.json"

Y = CONF["year"]
PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str]] = []

ARC = {"sign_ingress": 30.0,
       "nakshatra_ingress": 360.0 / CONF["nakshatra_scheme"],
       "navamsa_ingress": 30.0 / 9.0}

#: One arcminute. Tighter than any real corruption, looser than the
#: sub-arcsecond scatter between ephemeris backends.
ARCMIN = 1.0 / 60.0

#: Expected record counts per class over the full carry-in/carry-out span.
#: Wide enough to survive a backend swap, tight enough that a dropped body or a
#: doubled generator fails loudly.
EXPECTED_RANGE = {
    "sign_ingress":      (200, 320),
    "nakshatra_ingress": (480, 700),
    # The Moon is nine-tenths of this class on its own. It joined on
    # 21-Sep-2026 and took the count from 542 to 2226, which is why this range
    # is not the nakshatra's: 1,684 Moon records over the 427-day span against
    # 542 for the other eleven bodies together. See test_the_moons_navamsa
    # _series_is_bounded_by_its_own_sign_ingresses for what pins the shape.
    "navamsa_ingress":   (2100, 2400),
    "station":           (14, 32),
    "combustion":        (14, 36),
    "eclipse":           (5, 9),
    "lunation":          (50, 64),
    "total_day":         (12, 12),
    "conjunction":       (18, 60),
    "opposition":        (14, 48),
    "apsis":             (26, 42),
    "tithi_ingress":     (400, 470),
    # Exactly twice the tithi's, because a karana is a 6-degree step of the
    # same angle the tithi steps by 12. The range is the tithi's doubled, and
    # the EQUALITY is checked separately below -- a range this wide would admit
    # a scan that had skipped a division, and the equality will not.
    "karana_ingress":    (800, 940),
    "yoga_ingress":      (420, 490),
    # One per venue per civil day across a 427-day span, so this range is
    # narrow on purpose: unlike an ingress series it has no astronomical
    # reason to vary, and a missing venue halves it.
    "sunrise":           (840, 870),
    "sunset":            (840, 870),
    # Speed-class crossings, for the three calibrated planets only. Mercury has
    # three Fast windows in a year and each contributes two crossings, Venus one
    # or two, Mars one -- and a Fast window that runs to a span edge contributes
    # only its opening, which is why the lower bound is well under 12.
    "speed_crossing":    (4, 14),
}


def record(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, PASS if ok else FAIL, detail))


def load() -> dict:
    if not DATA.exists():
        raise SystemExit(f"{DATA} missing -- run python build_2027.py first")
    with DATA.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse(ts: str) -> dt.datetime:
    return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def body_of(rec: dict):
    """First body, or None for a class that names no body (Total Days is a
    calendar rule, not a body's event)."""
    return rec["bodies"][0] if rec["bodies"] else None


def in_2027(rec: dict) -> bool:
    """Calendar year by the primary zone, which is what the year means here."""
    return parse(rec["time"]["t_start_utc"]).astimezone(IST).year == Y


# -------------------------------------------------------------- 1. shape
def test_speed_class_crossings(doc: dict) -> None:
    """The speed-class series: calibrated levels, right bodies, right shape.

    The series exists so a rule can build Fast/Normal spans without touching the
    ephemeris, and so a Retrograde boundary can never be mistaken for a
    Fast/Normal one. Both of those are checked here rather than assumed, and the
    calibration itself is recomputed from the source's printed 2026 boundaries
    so the levels cannot drift away from the evidence.
    """
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(
        "_cat", ROOT / "finastro" / "rules" / "catalogue.py")
    cat = ilu.module_from_spec(spec)
    sys.modules["_cat"] = cat
    spec.loader.exec_module(cat)

    sc = [r for r in doc["records"] if r["event_class"] == "speed_crossing"]
    calibrated = tuple(CONF["speed_classes"][b]["threshold"]
                       for b in ("Mercury", "Venus", "Mars"))

    # Every level is one of the three calibrated numbers, and every record
    # carries the interval it came from.
    bad_level = [r["id"] for r in sc
                 if r["astronomy"]["speed_threshold"] not in calibrated]
    record("Every speed crossing is of a calibrated level",
           not bad_level, str(bad_level) or f"levels {calibrated}")

    bad_int = [r["id"] for r in sc
               if len(r["astronomy"]["speed_threshold_interval"]) != 2
               or not (r["astronomy"]["speed_threshold_interval"][0]
                       <= r["astronomy"]["speed_threshold"]
                       <= r["astronomy"]["speed_threshold_interval"][1])]
    record("Every record carries the feasible interval and the level lies in it",
           not bad_int, str(bad_int) or
           "thresholds are auditable from the output alone")

    # Bodies: the three calibrated planets only. Jupiter, Saturn and the outers
    # have no threshold, and a record for one would be an invented level.
    bodies = {r["bodies"][0] for r in sc}
    record("No speed crossing exists for an uncalibrated body",
           bodies == {"Mercury", "Venus", "Mars"}, str(sorted(bodies)))

    # The speed at the crossing equals the level (that is what a crossing IS).
    off = [r["id"] for r in sc
           if abs(r["astronomy"]["speed_deg_day"]
                  - r["astronomy"]["speed_threshold"]) > 1e-6]
    record("Each crossing's emitted speed equals its level",
           not off, str(off) or "the series is self-consistent")

    # certainties and precision_days come from the calibration
    # The GRADE is per body and is the withdrawal's footprint. Mercury's level
    # is overdetermined -- six crossings constrain one number -- so it supports
    # certainty B. Mars's and Venus's levels are single-point fits with zero
    # degrees of freedom, so they cannot, and their crossings are graded C with
    # the reason on the record. A datum is still emitted; what changed is how
    # much it is claimed to be worth.
    want = CONF["speed_classes"]["series_certainty"]
    bad_cert = [r["id"] for r in sc
                if r["qa"]["data_certainty"] != want[r["bodies"][0]]
                or r["qa"]["precision_days"] is None]
    record("Each speed crossing carries the grade its level can support",
           not bad_cert, str(bad_cert) or
           "; ".join(f"{b} {want[b]}" for b in sorted(want)))

    no_flag = [r["id"] for r in sc
               if r["qa"]["data_certainty"] == "C"
               and "single_point_fit_zero_degrees_of_freedom"
               not in r["qa"]["flags"]]
    record("A single-point fit says so on its own record",
           not no_flag, str(no_flag) or
           "the reason travels with the datum rather than living in config")

    # C has TWO grounds with different remedies -- a missing rule and an
    # unevidenced parameter -- so a bare C would hide which applies. Checked
    # across EVERY record, not just this series, because the invariant is
    # strongest where it is least expected.
    grounds = tuple(CONF["labels"]["data_certainty_grounds"])
    bare = [r["id"] for r in doc["records"]
            if r["qa"]["data_certainty"] == "C"
            and r["qa"].get("certainty_ground") not in grounds]
    record("Every C record names which ground it sits on", not bare,
           str(bare) or f"the two grounds are {list(grounds)}")
    stray = [r["id"] for r in doc["records"]
             if r["qa"]["data_certainty"] != "C"
             and r["qa"].get("certainty_ground") is not None]
    record("Only a C record carries a ground", not stray,
           str(stray) or "A and B have nothing missing to name")
    # THE STRUCTURAL CHECK. A threshold record's speed must be above the dead
    # band, which is what stops a retrograde-loop arc being emitted as a Fast
    # boundary. And no station record may be a threshold record.
    import finastro.ephem as _e
    band = _e.SPEED_DEADBAND
    too_slow = [r["id"] for r in sc
                if abs(r["astronomy"]["speed_deg_day"])
                < r["astronomy"]["speed_threshold"] - band]
    record("No threshold crossing sits inside the dead band",
           not too_slow, str(too_slow) or
           f"dead band is {band} deg/day, which no retrograde loop reaches")

    kinds = {r["astronomy"]["speed_crossing_kind"] for r in sc}
    record("A Retrograde boundary is never emitted as a threshold crossing",
           kinds == {"threshold"},
           f"kinds present {sorted(kinds)}; the stations stay in `station`")

    # Reproduce the source's printed 2026 boundaries from the levels, so the
    # calibration is re-derived on every run rather than trusted.
    import datetime as _dt
    isttz = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
    worst = {}
    for body, b in (("Mercury", 122), ("Venus", 123), ("Mars", 120)):
        level = CONF["speed_classes"][body]["threshold"]
        printed = []
        t = cat.B(b).tables[0]
        hp = t.headers[0].strip().lower() == "planet"
        rows = []
        for raw in t.rows:
            c = list(raw)[1:] if hp else list(raw)
            rows.append((c[0].strip(), c[1].strip(), c[2]))
        for i in range(1, len(rows)):
            d0s, _, cls = rows[i]
            prev = rows[i - 1][2]
            if "Retrograde" in (cls, prev) or not d0s:
                continue
            try:
                d0 = _dt.datetime.strptime(d0s, "%d-%b-%y").replace(
                    tzinfo=isttz)
            except ValueError:
                continue
            printed.append((d0, prev, cls))
        lo = _dt.datetime(2026, 1, 1, tzinfo=isttz)
        hi = _dt.datetime(2027, 1, 1, tzinfo=isttz)
        xs = [t for t, k, f, _ in _e.speed_crossings(body, lo, hi, level)
              if k == "threshold"]
        worst[body] = max(
            min(abs((x - d0).total_seconds()) / 86400 for x in xs)
            for d0, _, _ in printed) if xs else 99

    record("Calibrated levels reproduce 2026's printed Fast/Normal boundaries",
           worst.get("Venus", 99) <= 0.05 and worst.get("Mars", 99) <= 0.05
           and worst.get("Mercury", 99) <= 1.1,
           "worst offset per planet (days): "
           + ", ".join(f"{k} {v:.3f}" for k, v in sorted(worst.items()))
           + " -- Mercury's two February boundaries are ~1 day adrift at EVERY "
             "level in its interval, which is the source's own imprecision")


def test_counts(doc: dict) -> None:
    counts = collections.Counter(r["event_class"] for r in doc["records"])
    unexpected = set(counts) - set(EXPECTED_RANGE)
    record("No unexpected event_class in the output",
           not unexpected, str(sorted(unexpected)) if unexpected else "")
    for cls, (lo, hi) in EXPECTED_RANGE.items():
        n = counts.get(cls, 0)
        record(f"Count in range: {cls} ({lo}-{hi})", lo <= n <= hi, str(n))


def test_the_karana_series_is_the_tithi_series_at_half_the_arc(doc: dict) -> None:
    """The karana scan, checked against a series it cannot be fitted to.

    A karana is a 6-degree step of exactly the angle a tithi steps by 12, so
    two facts follow BY CONSTRUCTION and neither is a tolerance:

      * there are exactly twice as many karana ingresses as tithi ingresses;
      * every tithi ingress instant IS a karana ingress instant, to the
        second, because a 12-degree multiple is also a 6-degree multiple.

    That second one is the check worth having. A count in a range would pass
    for a scan that skipped a division and found a spurious one elsewhere;
    this will not, because a skipped karana at an even multiple deletes a
    tithi edge from the karana series and the set difference names it.

    It also pins the STEP. `ephem.KARANA_STEP` is an hour against a shortest
    karana of about 9h55m, and the failure mode of too coarse a step is a
    silently missing division -- which renders as a quiet month, not an error.
    """
    kar = [r for r in doc["records"] if r["event_class"] == "karana_ingress"]
    tit = [r for r in doc["records"] if r["event_class"] == "tithi_ingress"]
    record("The karana series is exactly twice the tithi series",
           len(kar) == 2 * len(tit),
           f"{len(kar)} karana against {len(tit)} tithi ingresses")

    k_at = {r["time"]["t_start_utc"] for r in kar}
    t_at = {r["time"]["t_start_utc"] for r in tit}
    missing = sorted(t_at - k_at)
    record("Every tithi boundary is also a karana boundary, to the second",
           not missing,
           f"{len(t_at)} tithi instants, all present in the karana series"
           if not missing else f"{len(missing)} absent, first {missing[:3]}")

    nums = {r["astronomy"]["karana_to"] for r in kar}
    record("Karana numbers span 1..60 and nothing else",
           nums <= set(range(1, 61)) and len(nums) == 60,
           f"{len(nums)} distinct karana numbers")

    # The eight the source names, against the eight the layer derives. The
    # document prints them in its own prose ("karana numbers 8, 15, 22, 29,
    # 36, 43, 50 and 57"), so this compares two independent answers.
    from finastro.panchang import VISHTI_KARANAS
    record("The derived Vishti karanas are the eight the source prints",
           VISHTI_KARANAS == (8, 15, 22, 29, 36, 43, 50, 57),
           str(VISHTI_KARANAS))
    named = {r["astronomy"]["karana_name_to"] for r in kar
             if r["astronomy"]["karana_to"] in VISHTI_KARANAS}
    record("Every one of them is NAMED Vishti, including 57",
           named == {"Vishti"},
           f"names on the eight: {sorted(named)} -- 57 read 'Shakuni' until "
           "20-Sep-2026, so seven were named where the source names eight")


def test_unique_ids(doc: dict) -> None:
    ids = [r["id"] for r in doc["records"]]
    dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
    record("No duplicate ids", not dupes,
           f"{len(ids)} records, {len(dupes)} duplicated"
           + (f" e.g. {dupes[:3]}" if dupes else ""))


def test_span(doc: dict) -> None:
    lo = parse(doc["meta"]["span_start_utc"])
    hi = parse(doc["meta"]["span_end_utc"])
    bad = [r["id"] for r in doc["records"]
           if not lo <= parse(r["time"]["t_start_utc"]) <= hi]
    record("Every t_start_utc inside the generated span", not bad,
           f"{lo:%d-%b-%Y} -> {hi:%d-%b-%Y}, {len(bad)} outside"
           + (f" e.g. {bad[:2]}" if bad else ""))


def test_ordering(doc: dict) -> None:
    keys = [(r["time"]["t_start_utc"], r["id"]) for r in doc["records"]]
    record("Deterministic ordering by t_start_utc then id",
           keys == sorted(keys), "")


def test_certainty(doc: dict) -> None:
    grades = set(CONF["labels"]["data_certainty"])
    bad = [r["id"] for r in doc["records"]
           if r["qa"].get("data_certainty") not in grades]
    record("Every record carries a certainty grade", not bad,
           f"{len(bad)} missing or invalid")


def test_carry_in_out(doc: dict) -> None:
    """The 2026 source truncated windows at the year boundary. If nothing lands
    outside calendar 2027, the carry-in and carry-out did not happen."""
    outside = [r for r in doc["records"] if not in_2027(r)]
    before = [r for r in outside
              if parse(r["time"]["t_start_utc"]).astimezone(IST).year < Y]
    after = [r for r in outside
             if parse(r["time"]["t_start_utc"]).astimezone(IST).year > Y]
    record("Carry-in from Dec-2026 and carry-out to Jan-2028 both present",
           bool(before) and bool(after),
           f"{len(before)} before, {len(after)} after")


def test_no_interpretation_leaked(doc: dict) -> None:
    """Step 4 vocabulary must not be able to appear in a Step 3 record."""
    banned = {"confidence", "claim_tag", "verdict", "theme", "sector",
              "probability", "source_probability", "impact_tier", "bias"}
    found = set()
    for r in doc["records"]:
        for layer in ("astronomy", "panchang", "qa"):
            found |= banned & set(r[layer])
        found |= banned & set(r)
    record("No interpretation field leaked into the astronomy layer",
           not found, str(sorted(found)))


# ----------------------------------------------------- 2. ingress accuracy
def test_ingress_boundaries(doc: dict) -> None:
    """Each ingress must sit on its own boundary, recomputed from the engine.

    The longitude is read back from ephem at the stored instant, so a record
    whose time drifted fails here even if its own stored longitude had been
    edited to match.
    """
    for cls, arc in ARC.items():
        worst, worst_id = 0.0, ""
        for r in doc["records"]:
            if r["event_class"] != cls:
                continue
            t = parse(r["time"]["t_start_utc"])
            off = ephem.longitude(t, r["bodies"][0]) % arc
            miss = min(off, arc - off)
            if miss > worst:
                worst, worst_id = miss, r["id"]
        record(f"{cls}: every crossing within 1 arcminute of its boundary",
               worst <= ARCMIN,
               f"worst {worst * 60:.3f} arcmin ({worst_id})")


def test_ingress_direction(doc: dict) -> None:
    """Retrograde re-entry is its own record, never collapsed into the forward
    crossing. If the flag never appears, the collapse crept back in."""
    retro = [r for r in doc["records"]
             if r["event_class"] == "sign_ingress"
             and "retrograde_re_entry" in r["qa"]["flags"]]
    record("Retrograde sign re-entries emitted as their own records",
           bool(retro), f"{len(retro)} retrograde re-entries")


def test_saturn_round_trip(doc: dict) -> None:
    """Saturn Pisces -> Aries -> Pisces. The defining slow-planet sequence of
    2027, and the one a truncated span would cut in half."""
    legs = [(r["astronomy"]["sign_from"], r["astronomy"]["sign_to"],
             stamp(parse(r["time"]["t_start_utc"])).ist_date)
            for r in doc["records"]
            if r["event_class"] == "sign_ingress" and r["bodies"] == ["Saturn"]]
    got = [(a, b) for a, b, _ in legs]
    record("Saturn Pisces -> Aries -> Pisces round trip present",
           got[:2] == [("Pisces", "Aries"), ("Aries", "Pisces")],
           " | ".join(f"{a}->{b} {d}" for a, b, d in legs))


# ------------------------------------------------------------- 3. stations
def test_stations(doc: dict) -> None:
    """Speed must actually be zero at the reported instant, recomputed.

    The speed OF DATE, which is what a station is a zero of -- see
    `ephem.Position.speed_of_date`. The record's own `speed_deg_day` is the
    sidereal speed and sits ~6e-5 deg/day off zero at a true station.
    """
    worst, worst_id = 0.0, ""
    for r in doc["records"]:
        if r["event_class"] != "station":
            continue
        t = parse(r["time"]["t_start_utc"])
        speed = abs(ephem.position(t, r["bodies"][0]).speed_of_date)
        if speed > worst:
            worst, worst_id = speed, r["id"]
    record("Stations: |speed| within 1e-4 deg/day of zero",
           worst <= 1e-4, f"worst {worst:.3e} deg/day ({worst_id})")


def test_station_precision(doc: dict) -> None:
    """Minutes for the inner planets, hours for the outers. A station is
    stationary to second order, so claiming minutes for Saturn would be a
    precision the geometry does not support."""
    inner = {"Mercury", "Venus", "Mars"}
    bad = [r["id"] for r in doc["records"] if r["event_class"] == "station"
           and r["time"]["precision"] != ("minutes" if r["bodies"][0] in inner
                                          else "hours")]
    record("Station precision: minutes for inner, hours for outer planets",
           not bad, f"{len(bad)} mislabelled")


# ------------------------------------------------------------- 4. eclipses
def test_eclipses(doc: dict) -> None:
    ecl = [r for r in doc["records"] if r["event_class"] == "eclipse"]
    in_year = [r for r in ecl if in_2027(r)]
    pen = [r for r in in_year if "penumbral" in r["qa"]["flags"]]
    record("Exactly 5 eclipses in calendar 2027", len(in_year) == 5,
           " | ".join(f"{r['astronomy']['eclipse_type']} "
                      f"{stamp(parse(r['time']['t_start_utc'])).ist_date}"
                      for r in in_year))
    record("Exactly 3 of them flagged penumbral", len(pen) == 3,
           f"{len(pen)} penumbral")
    record("Penumbral eclipses carry the config impact label",
           all(f"impact={CONF['eclipses']['penumbral_impact']}"
               in r["qa"]["flags"] for r in pen),
           CONF["eclipses"]["penumbral_impact"])
    record("Eclipses store global and local contacts separately",
           all("contacts_global" in r["time"] and "contacts_local" in r["time"]
               for r in ecl),
           f"{len(ecl)} eclipse records in span")
    record("Eclipse windows run begin -> end, not a bare instant",
           all(r["time"]["t_end_utc"]
               and r["time"]["t_end_utc"] > r["time"]["t_start_utc"]
               for r in ecl), "")


# -------------------------------------------------------------- 5. dignity
def test_dignity_is_sign_level(doc: dict) -> None:
    """The 2026 source labels dignity across a whole sign and never splits it
    at the exaltation degree. If a label ever varies by degree inside one sign,
    degree-gating has crept in."""
    seen = collections.defaultdict(set)
    for r in doc["records"]:
        a = r["astronomy"]
        if a.get("dignity") is None or "sign" not in a:
            continue
        seen[(body_of(r), a["sign"])].add(tuple(a["dignity"]))
    varying = {k: v for k, v in seen.items() if len(v) > 1}
    record("No dignity label varies by degree within a single sign",
           not varying, f"{len(seen)} body/sign pairs checked"
           + (f", varying: {list(varying)[:3]}" if varying else ""))


def test_dignity_known_cases(doc: dict) -> None:
    record("Mercury in Virgo returns own + trine + exalted",
           ephem.dignity_states("Mercury", "Virgo")
           == ["own", "trine", "exalted"],
           str(ephem.dignity_states("Mercury", "Virgo")))
    record("Mercury in Virgo also carries the standalone trine flag",
           ephem.is_trine("Mercury", "Virgo") is True, "")
    record("Saturn in Libra is exalted and flagged as a source omission",
           ephem.dignity_states("Saturn", "Libra") == ["exalted"]
           and ephem.corrects_source_omission("Saturn", "Libra"),
           str(ephem.dignity_states("Saturn", "Libra")))
    record("Saturn in Aries is debilitated under the same scheme",
           ephem.dignity_states("Saturn", "Aries") == ["debilitated"],
           str(ephem.dignity_states("Saturn", "Aries")))
    corrected = [r["id"] for r in doc["records"]
                 if "dignity_corrects_source_omission" in r["qa"]["flags"]]
    unflagged = [r["id"] for r in doc["records"]
                 if body_of(r) and r["astronomy"].get("dignity")
                 and ephem.corrects_source_omission(
                     body_of(r), r["astronomy"].get("sign", ""))
                 and "dignity_corrects_source_omission" not in r["qa"]["flags"]]
    record("Source-omitted dignities are flagged wherever they occur",
           not unflagged,
           f"{len(corrected)} flagged, {len(unflagged)} unflagged")


def test_nodes_have_no_dignity(doc: dict) -> None:
    bad = [r["id"] for r in doc["records"]
           if body_of(r) in ephem.NODES
           and r["astronomy"].get("dignity") is not None]
    record("Rahu and Ketu never carry a non-null dignity", not bad,
           f"{len(bad)} offending records")
    # A null is legitimate only where the node's sign-period opened before the
    # span, which is declared with a flag. A silent null is not.
    missing = [r["id"] for r in doc["records"]
               if body_of(r) in ephem.NODES
               and r["astronomy"].get("lord_relationship") is None
               and ephem.NO_ANCHOR_FLAG not in r["qa"]["flags"]]
    record("Rahu and Ketu carry lord_relationship instead", not missing,
           f"{len(missing)} unflagged nulls")


#: The source's Relationship column, reproduced. All four are read at one
#: instant -- the node sign ingress of 05-Dec-2026 -- because the value is a
#: property of the sign-period, not of the moment a record happens to fall on.
#: No case names an instant of its own: a per-case instant would be fitted to
#: the answer, which is exactly how the luminary pairs were wrong before.
NODE_CASES = [
    ("Rahu", "Aquarius", "Saturn", "Semi-Sextile"),
    ("Rahu", "Capricorn", "Saturn", "Sextile"),
    ("Ketu", "Leo", "Sun", "Square"),
    ("Ketu", "Cancer", "Moon", "Square"),
]

#: The source prints this ingress at 21:52 IST; the mean node computes to
#: 22:32, the same 40-minute gap config already records under `node: mean`.
#: The date is asserted, the minute is not.
ANCHOR_DATE = dt.date(2026, 12, 5)


def test_node_lord_relationship(doc: dict) -> None:
    mid = dt.datetime(Y, 6, 1, tzinfo=UTC)
    anchors = {n: ephem.node_anchor(mid, n, SPAN_START, SPAN_END)
               for n in ephem.NODES}
    missing = [n for n, a in anchors.items() if a is None]
    record("Both nodes anchor to a sign ingress inside the span", not missing,
           f"missing: {missing}" if missing else "")
    if missing:
        return

    instants = {a[0] for a in anchors.values()}
    record("Rahu and Ketu share one anchoring ingress instant",
           len(instants) == 1,
           ", ".join(sorted(f"{a[0].astimezone(IST):%d-%b-%Y %H:%M} {a[1]}"
                            for a in anchors.values())))
    inst = sorted(instants)[0]
    record(f"Anchoring ingress falls on {ANCHOR_DATE:%d-%b-%Y}",
           inst.astimezone(IST).date() == ANCHOR_DATE,
           f"{inst.astimezone(IST):%d-%b-%Y %H:%M} IST"
           " (source prints 21:52; mean node computes 22:32)")

    for node, sign, lord, want in NODE_CASES:
        lord_sign = ephem.position(inst, lord).sign
        got = ephem.sign_distance_aspect(sign, lord_sign)
        ok = ephem.SIGN_LORDS[sign] == lord and got == want
        record(f"{node} in {sign} (lord {lord}) = {want}", ok,
               f"at anchor: {lord} in {lord_sign} -> {got}")


def test_node_lord_relationship_is_period_constant(doc: dict) -> None:
    """One value per sign-period, for every record inside it.

    Grouped by the record's own anchoring ingress, not by sign, so a node that
    re-entered a sign would be two periods here and not one.
    """
    periods = collections.defaultdict(set)
    for r in doc["records"]:
        body = body_of(r)
        if body not in ephem.NODES:
            continue
        anchor = ephem.node_anchor(parse(r["time"]["t_start_utc"]), body,
                                   SPAN_START, SPAN_END)
        key = (body, anchor[0] if anchor else None)
        periods[key].add(r["astronomy"].get("lord_relationship"))

    varying = {k: v for k, v in periods.items() if len(v) > 1}
    record("lord_relationship is constant within each node sign-period",
           not varying,
           f"{len(periods)} periods, {len(varying)} varying"
           + (f" e.g. {sorted(varying)[0]} -> {sorted(map(str, list(varying.values())[0]))}"
              if varying else ""))

    # The carry-in reaches only to 01-Dec, so a record before the 05-Dec
    # ingress sits in a period that opened outside the span. Those must be
    # null and flagged, never instant-evaluated into a plausible-looking value.
    unanchored = periods.get(("Rahu", None), set()) | periods.get(("Ketu", None), set())
    record("Records with no anchoring ingress carry null, not a fallback",
           unanchored <= {None}, f"values seen: {sorted(map(str, unanchored))}")


# ---------------------------------------------- 6. conjunction pair policy
def test_moon_excluded_from_pairs(doc: dict) -> None:
    pair_classes = ("conjunction", "opposition")
    with_moon = [r["id"] for r in doc["records"]
                 if r["event_class"] in pair_classes and "Moon" in r["bodies"]]
    record("No conjunction or opposition record contains the Moon",
           not with_moon, f"{len(with_moon)} offending records")

    universe = set(map(frozenset, itertools.combinations(
        CONF["conjunctions"]["bodies"], 2)))
    record("Configured conjunction universe is exactly 36 pairs",
           len(universe) == 36, f"{len(universe)} pairs")

    seen = {frozenset(r["bodies"]) for r in doc["records"]
            if r["event_class"] in pair_classes}
    record("Every pair emitted is drawn from that universe",
           seen <= universe,
           f"{len(seen)} distinct pairs exact in span, "
           f"{len(universe - seen)} of 36 never exact here")

    # The Sun-Moon conjunction and opposition are the new and full moon, so
    # they belong to the lunation class and must never be re-emitted as a
    # conjunction. The eclipse class also names both bodies, legitimately: an
    # eclipse is a shadow passage, not the syzygy itself, and its lunation
    # record is flagged to say so.
    sun_moon = {r["event_class"] for r in doc["records"]
                if set(r["bodies"]) == {"Sun", "Moon"}}
    record("Sun-Moon never appears in the conjunction or opposition class",
           not (sun_moon & set(pair_classes)), str(sorted(sun_moon)))
    linked = [r for r in doc["records"] if r["event_class"] == "lunation"
              and "coincides_with_eclipse" in r["qa"]["flags"]]
    eclipses = [r for r in doc["records"] if r["event_class"] == "eclipse"]
    record("Every eclipse has its syzygy flagged in the lunation class",
           len(linked) == len(eclipses),
           f"{len(linked)} lunations flagged, {len(eclipses)} eclipses")


# ------------------------------------------------------------ 7. dual time
def test_dual_stamps(doc: dict) -> None:
    bad = [r["id"] for r in doc["records"]
           if r["time"]["start_stamp"]["et_abbr"] not in ("EST", "EDT")]
    record("Every record carries a resolved Eastern abbreviation", not bad,
           f"{len(bad)} bad")
    abbrs = {r["time"]["start_stamp"]["et_abbr"] for r in doc["records"]}
    record("Both EST and EDT occur across the span", abbrs == {"EST", "EDT"},
           str(sorted(abbrs)))
    shifted = [r for r in doc["records"]
               if r["time"]["start_stamp"]["day_shift"] == -1]
    record("Eastern day_shift is detected where the dates differ",
           bool(shifted), f"{len(shifted)} records shift a day")


def test_dst_not_hardcoded() -> None:
    """Resolved through the IANA zone, so the switch instants are found rather
    than known. Nothing in the codebase names 14-Mar or 07-Nov 2027."""
    spring = [stamp(dt.datetime(Y, 3, d, 12, tzinfo=UTC)).et_abbr
              for d in (1, 31)]
    autumn = [stamp(dt.datetime(Y, 11, d, 12, tzinfo=UTC)).et_abbr
              for d in (1, 30)]
    record("zoneinfo resolves the 2027 EST/EDT transitions",
           spring == ["EST", "EDT"] and autumn == ["EDT", "EST"],
           f"Mar {spring}, Nov {autumn}")

    src = "\n".join(p.read_text(encoding="utf-8")
                    for p in [ROOT / "build_2027.py"]
                    + sorted((ROOT / "finastro").glob("*.py")))
    leaked = [s for s in ("2027-03-14", "2027-11-07", "14-Mar-2027",
                          "07-Nov-2027") if s in src]
    record("No 2027 DST switch date hardcoded in the engine or build script",
           not leaked, str(leaked))


# ----------------------------------------------------------- 8. provenance
def test_provenance(doc: dict) -> None:
    backend = ephem.init()
    record("Recorded backend matches the engine in use",
           doc["meta"]["ephemeris_backend"] == backend,
           doc["meta"]["ephemeris_backend"])
    bad = [r["id"] for r in doc["records"]
           if r["qa"]["ephemeris"] != backend
           or r["qa"]["ayanamsha"] != CONF["ayanamsha"]
           or r["qa"]["node"] != CONF["node"]]
    record("Every record's qa names the backend, ayanamsha and node in force",
           not bad, f"{len(bad)} mismatched")
    combust = [r for r in doc["records"] if r["event_class"] == "combustion"]
    record("Combustion records carry precision_days from config",
           all(isinstance(r["qa"]["precision_days"], int) for r in combust),
           f"{len(combust)} combust/rise records")
    record("Combustion records are located at the primary location",
           all(r["location"] == "mumbai" for r in combust), "")


def test_navamsa_dignity_frame(doc: dict) -> None:
    """A record carries the dignity of the chart it is a record of.

    `dignity` is always the rashi answer, read off `sign`; `navamsa_dignity` is
    always the D9 answer, read off `navamsa`. The two are never collapsed, and a
    navamsa record never presents the rashi answer as its own.
    """
    nav = [r for r in doc["records"] if r["event_class"] == "navamsa_ingress"]

    missing = [r["id"] for r in nav
               if body_of(r) not in ev.NO_DIGNITY
               and "navamsa_dignity" not in r["astronomy"]]
    record("Every navamsa_ingress record carries navamsa_dignity",
           not missing, f"{len(nav)} records, {len(missing)} without it")

    # The substantive assertion: the value is derived from the D9 sign.
    wrong_frame = []
    rashi_derived = []
    discriminating = 0
    for r in nav:
        b = body_of(r)
        if b in ev.NO_DIGNITY or b in ephem.NODES:
            continue
        a = r["astronomy"]
        want_nav = ephem.dignity_states(b, a["navamsa"])
        want_rashi = ephem.dignity_states(b, a["sign"])
        if a.get("navamsa_dignity") != want_nav:
            wrong_frame.append(r["id"])
        if want_nav != want_rashi:
            discriminating += 1
            # Where the frames disagree the navamsa field must not be holding
            # the rashi answer. This is the failure the field exists to prevent.
            if a.get("navamsa_dignity") == want_rashi:
                rashi_derived.append(r["id"])
    record("navamsa_dignity is computed from the navamsa sign on every record",
           not wrong_frame, f"{len(wrong_frame)} mismatched")
    record("No navamsa record carries a dignity derived from the rashi sign",
           not rashi_derived,
           f"{len(rashi_derived)} offending, {discriminating} records where "
           f"the two frames actually differ")
    # A vacuous pass would be the real failure here: if every record happened to
    # be vargottam the check above could not distinguish anything.
    record("The two frames actually diverge across the generated year",
           discriminating > 0, f"{discriminating} divergent records")

    # ...and the rashi answer is still on the record, under its own name.
    rashi_bad = [r["id"] for r in nav
                 if body_of(r) not in ev.NO_DIGNITY
                 and body_of(r) not in ephem.NODES
                 and r["astronomy"].get("dignity")
                 != ephem.dignity_states(body_of(r), r["astronomy"]["sign"])]
    record("dignity on a navamsa record is still the rashi answer, kept "
           "distinct", not rashi_bad, f"{len(rashi_bad)} mismatched")

    # Nodes carry no dignity in either chart, stated rather than absent.
    node_bad = [r["id"] for r in nav
                if body_of(r) in ephem.NODES
                and r["astronomy"].get("navamsa_dignity", "absent") is not None]
    record("Rahu and Ketu carry an explicit null navamsa_dignity",
           not node_bad, f"{len(node_bad)} offending records")

    # Non-D9 records must not sprout a D9 dignity: the field is the D9 record's
    # own, not a second opinion bolted onto every position.
    leaked = [r["id"] for r in doc["records"]
              if r["event_class"] != "navamsa_ingress"
              and "navamsa_dignity" in r["astronomy"]]
    record("No non-navamsa record carries navamsa_dignity", not leaked,
           f"{len(leaked)} offending records")


def test_navamsa_source_omission_is_checked_in_the_D9_frame() -> None:
    """Config's one recorded omission -- Saturn in Libra -- is a row in the D9
    table. Saturn's rashi sign never reaches Libra in 2026 or 2027, so a check
    in the rashi frame could never fire. Asserted directly against positional()
    at an instant inside the source's own unlabelled window, which sits outside
    the 2027 span and so cannot be reached by a record in this build."""
    when = dt.datetime(2026, 4, 1, 12, 0, tzinfo=IST)
    astro, flags = ev.positional(
        when, "Saturn",
        navamsa_from="Virgo", navamsa_to="Libra", navamsa_override="Libra")
    record("Saturn's D9 Libra window gets the exalted label the source omits",
           astro.navamsa_dignity == ["exalted"], str(astro.navamsa_dignity))
    record("...and is flagged in the navamsa frame, not the rashi one",
           "navamsa_dignity_corrects_source_omission" in flags
           and "dignity_corrects_source_omission" not in flags,
           f"rashi sign at that instant: {astro.sign}, flags: {flags}")


def test_the_moons_navamsa_series_is_bounded_by_its_own_sign_ingresses(
        doc: dict) -> None:
    """THE STRUCTURAL CHECK. Every Moon sign ingress is a Moon navamsa ingress.

    Thirty degrees is nine whole navamsas, so a sign cusp is always also a
    navamsa cusp. That makes the two series checkable against each other with
    no ephemeris call and no tolerance: each `sign_ingress` instant for the
    Moon must appear, TO THE SECOND, among its `navamsa_ingress` instants. The
    two are produced by separate scans at separate step sizes -- 30 minutes and
    13 -- and bisected independently, so agreement is evidence about the
    generator and not a tautology.

    It is also the answer to the claim that excluded the Moon from D9 until
    21-Sep-2026, that "a D9 series for the Moon would be noise rather than
    signal". A ninth of this series was already in the build, graded A, under
    the name `sign_ingress`.
    """
    moon_nav = sorted(r["time"]["t_start_utc"] for r in doc["records"]
                      if r["event_class"] == "navamsa_ingress"
                      and r["bodies"][0] == "Moon")
    moon_sign = sorted(r["time"]["t_start_utc"] for r in doc["records"]
                       if r["event_class"] == "sign_ingress"
                       and r["bodies"][0] == "Moon")
    record("The Moon has a navamsa ingress series at all",
           len(moon_nav) > 1000,
           f"{len(moon_nav)} Moon navamsa_ingress records over the span")

    missing = [t for t in moon_sign if t not in set(moon_nav)]
    record("Every Moon sign-ingress instant coincides TO THE SECOND with a "
           "Moon navamsa-ingress instant", not missing,
           f"{len(moon_sign)} sign ingresses, {len(moon_sign) - len(missing)} "
           f"coincident; missing {missing[:4]}")

    # And the ratio, which is the other half of the same fact: nine navamsas
    # to a sign. It is not exactly 9 because the span opens and closes
    # mid-sign, so the tolerance is one sign's worth at each end.
    ratio = len(moon_nav) / len(moon_sign)
    record("...and the series is nine times the sign series, to within the "
           "two partial signs the span's ends cut",
           8.9 <= ratio <= 9.1, f"{len(moon_nav)}/{len(moon_sign)} = "
           f"{ratio:.4f}")

    # The interval the exclusion was argued on. Three figures were carried in
    # the tree -- four hours, two hours, 105 minutes -- and none of them was
    # this one. Pinned as a range so it is a measurement and not a slogan.
    span = (parse(doc["meta"]["span_end_utc"])
            - parse(doc["meta"]["span_start_utc"])).total_seconds() / 3600
    mean_h = span / len(moon_nav)
    record("The Moon crosses a navamsa every 6.0 to 6.1 hours, which is none "
           "of the three intervals the exclusion was argued on",
           6.0 <= mean_h <= 6.1,
           f"mean {mean_h:.4f} h over {span / 24:.0f} days; the tree carried "
           "four hours, two hours and 105 minutes")


def test_a_dignity_the_source_never_labels_says_so_on_the_record(
        doc: dict) -> None:
    """Provenance for the two bodies config puts in `not_witnessed`.

    The Moon is why this exists. The 2026 document gives it no journey table
    and no navamsa table, so it labels the Moon's dignity nowhere -- and from
    21-Sep-2026 the engine emits a D9 dignity for it on 421 records. The value
    is the same Parashari rule every other body gets; what the flag carries is
    that no printed label has ever tested it.
    """
    not_witnessed = set(CONF["dignity"]["source_witness"]["not_witnessed"])
    record("Config still names the two bodies this flag is derived from",
           not_witnessed == {"Sun", "Moon"}, f"{sorted(not_witnessed)}")

    nav = [r for r in doc["records"] if r["event_class"] == "navamsa_ingress"]
    want = {r["id"] for r in nav
            if r["bodies"][0] in not_witnessed
            and r["astronomy"].get("navamsa_dignity")}
    got = {r["id"] for r in doc["records"]
           if ev.DIGNITY_NOT_WITNESSED_FLAG in r["qa"]["flags"]}
    record("Every navamsa_dignity on an unwitnessed body is flagged, and "
           "nothing else is", want == got,
           f"{len(got)} flagged; {len(want - got)} unflagged, "
           f"{len(got - want)} spurious")

    by_body = collections.Counter(
        r["bodies"][0] for r in doc["records"]
        if ev.DIGNITY_NOT_WITNESSED_FLAG in r["qa"]["flags"])
    record("...and both bodies are represented, so the flag is not the Moon's "
           "alone by accident",
           set(by_body) == not_witnessed and min(by_body.values()) > 0,
           f"{dict(by_body)}")

    # Non-vacuity the other way: a witnessed body with a D9 dignity must NOT
    # carry it, or the flag would mean nothing.
    leaked = [r["id"] for r in nav
              if r["bodies"][0] not in not_witnessed
              and ev.DIGNITY_NOT_WITNESSED_FLAG in r["qa"]["flags"]]
    witnessed_with_dignity = [r["id"] for r in nav
                              if r["bodies"][0] == "Saturn"
                              and r["astronomy"].get("navamsa_dignity")]
    record("A witnessed body's D9 dignity carries no such flag",
           not leaked and witnessed_with_dignity,
           f"{len(witnessed_with_dignity)} Saturn D9 dignities, none flagged")


def test_vargottama_on_records(doc: dict) -> None:
    """vargottama is a property of a position, so every positional record carries
    it -- and it is the equality of the record's own two frames, not a third
    opinion computed somewhere else."""
    have = [r for r in doc["records"] if "vargottama" in r["astronomy"]]
    record("Every record with both frames carries vargottama",
           len(have) == len(doc["records"]),
           f"{len(have)}/{len(doc['records'])}")

    wrong = [r["id"] for r in have
             if r["astronomy"]["vargottama"]
             != (r["astronomy"]["sign"] == r["astronomy"]["navamsa"])]
    record("vargottama equals sign == navamsa on every record", not wrong,
           f"{len(wrong)} mismatched")

    by_class = collections.Counter(
        r["event_class"] for r in have if r["astronomy"]["vargottama"])
    record("vargottama is emitted beyond navamsa_ingress",
           len(by_class) > 1, f"true on {sum(by_class.values())} records across "
           f"{len(by_class)} classes: {dict(by_class)}")
    # Non-vacuity in both directions: a field that were always false, or always
    # true, would satisfy the equality check above and mean nothing.
    t = sum(1 for r in have if r["astronomy"]["vargottama"])
    record("vargottama is neither always true nor always false",
           0 < t < len(have), f"{t} true of {len(have)}")


def test_vargottama_is_not_folded_into_dignity(doc: dict) -> None:
    """The source prints Cancer (Exalted, Vargottam): two states at once. The
    engine must keep them in two fields."""
    leaked = [r["id"] for r in doc["records"]
              for key in ("dignity", "navamsa_dignity")
              if isinstance(r["astronomy"].get(key), list)
              and any("vargottam" in st for st in r["astronomy"][key])]
    record("No dignity list contains a vargottama state", not leaked,
           f"{len(leaked)} offending records")
    both = [r for r in doc["records"]
            if r["astronomy"].get("vargottama")
            and r["astronomy"].get("navamsa_dignity")]
    record("Records hold vargottama and a D9 dignity at the same time",
           bool(both), f"{len(both)} records carry both, e.g. "
           + (both[0]["id"] if both else "none"))


def test_ingress_frames_are_cusp_consistent(doc: dict) -> None:
    """At an ingress the sampled position can sit on the far side of the cusp, so
    both frames are taken from the crossing index. A sign cusp is always also a
    navamsa cusp, which is what makes this necessary rather than tidy: without it
    vargottama on an ingress record is decided by sampling noise."""
    bad_n = [r["id"] for r in doc["records"]
             if r["event_class"] == "sign_ingress"
             and ephem.SIGNS.index(r["astronomy"]["navamsa"])
             != (ephem.SIGNS.index(r["astronomy"]["sign"]) * 9
                 + (8 if "retrograde_re_entry" in r["qa"]["flags"] else 0)) % 12]
    record("sign_ingress navamsa is the entered sign's first (or last) navamsa",
           not bad_n, f"{len(bad_n)} inconsistent")

    bad_s = [r["id"] for r in doc["records"]
             if r["event_class"] == "navamsa_ingress"
             and r["astronomy"]["sign"] != ephem.sign_of_navamsa_index(
                 _nav_index(r["astronomy"]["navamsa"], r["astronomy"]["sign"]))]
    record("navamsa_ingress sign is the sign containing that navamsa arc",
           not bad_s, f"{len(bad_s)} inconsistent")

    # Movable signs begin with their own navamsa, so a forward ingress into one
    # is vargottama at the instant of the cusp. The source's own Vargottam Mars
    # row for Aries opens at exactly the Aries ingress.
    movable = {"Aries", "Cancer", "Libra", "Capricorn"}
    fwd = [r for r in doc["records"]
           if r["event_class"] == "sign_ingress"
           and "retrograde_re_entry" not in r["qa"]["flags"]
           and r["astronomy"]["sign"] in movable]
    record("Every forward ingress into a movable sign is vargottama",
           fwd and all(r["astronomy"]["vargottama"] for r in fwd),
           f"{len(fwd)} such records, all true")


def _nav_index(navamsa: str, sign: str) -> int:
    """Global navamsa arc index (0-107) for a navamsa sign inside a rashi sign.
    Each sign spans nine consecutive navamsas starting at sign_index * 9."""
    base = ephem.SIGNS.index(sign) * 9
    for k in range(base, base + 9):
        if ephem.SIGNS[k % 12] == navamsa:
            return k
    return -1


# ------------------------------------- 13. source_probability population
#: The carried labels attach to these families and to no others. Keyed per BODY
#: for the visibility classes, because that is the ruling the config records: at
#: family level visibility/combust would carry three different values, per body
#: it carries one each. See config/conventions.yaml, source_probability.
CARRIED_CATALOGUE_A = {
    "conj_sun_mercury":   lambda r: r["rule_family"] == "aspect/conjunction"
                                    and set(r["bodies"]) == {"Sun", "Mercury"},
    "conj_mercury_venus": lambda r: r["rule_family"] == "aspect/conjunction"
                                    and set(r["bodies"]) == {"Mercury", "Venus"},
    "conj_venus_uranus":  lambda r: r["rule_family"] == "aspect/conjunction"
                                    and set(r["bodies"]) == {"Venus", "Uranus"},
    "combust_venus":      lambda r: r["rule_family"] == "visibility/combust"
                                    and body_of(r) == "Venus",
    "combust_saturn":     lambda r: r["rule_family"] == "visibility/combust"
                                    and body_of(r) == "Saturn",
    "combust_jupiter":    lambda r: r["rule_family"] == "visibility/combust"
                                    and body_of(r) == "Jupiter",
    "rise_venus":         lambda r: r["rule_family"] == "visibility/rise"
                                    and body_of(r) == "Venus",
}

#: Bodies whose sign residency the catalogue-B families are computed over. The
#: Moon is excluded throughout, exactly as the source excludes it from its pair
#: rules ("Except Moon", conjunctions.source): its sign changes every 2.2 days
#: and would make every co-location window a lunar artefact.
RESIDENCY_BODIES = ["Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn",
                    "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]


def _sign_timeline(doc: dict, body: str, span: tuple) -> list:
    """[(start, end, sign), ...] over the whole span, from the ingress records.

    A body with no ingress in the span holds one sign throughout; that sign is
    read off a record of its own rather than recomputed, so this stays a check
    on the FILE.
    """
    lo, hi = span
    evs = sorted((r for r in doc["records"]
                  if r["event_class"] == "sign_ingress" and r["bodies"] == [body]),
                 key=lambda r: r["time"]["t_start_utc"])
    if not evs:
        for r in doc["records"]:
            if body_of(r) == body:
                return [(lo, hi, r["astronomy"]["sign"])]
        return []
    out, cur, t = [], evs[0]["astronomy"]["sign_from"], lo
    for e in evs:
        when = parse(e["time"]["t_start_utc"])
        out.append((t, when, cur))
        cur, t = e["astronomy"]["sign_to"], when
    out.append((t, hi, cur))
    return [(a, b, v) for a, b, v in out if b > a]


def _nakshatra_timeline(doc: dict, body: str, span: tuple) -> list:
    lo, hi = span
    evs = sorted((r for r in doc["records"]
                  if r["event_class"] == "nakshatra_ingress" and r["bodies"] == [body]),
                 key=lambda r: r["time"]["t_start_utc"])
    if not evs:
        return []
    out, cur, t = [], evs[0]["astronomy"]["nakshatra_from"], lo
    for e in evs:
        when = parse(e["time"]["t_start_utc"])
        out.append((t, when, cur))
        cur, t = e["astronomy"]["nakshatra_to"], when
    out.append((t, hi, cur))
    return [(a, b, v) for a, b, v in out if b > a]


def _value_at(timeline: list, when):
    for a, b, v in timeline:
        if a <= when < b:
            return v
    return None


def _windows(timelines: list, predicate) -> list:
    """Merged intervals over the union of all timeline edges, kept where the
    predicate evaluated at the interval midpoint returns a truthy value."""
    edges = sorted({e for tl in timelines for a, b, _ in tl for e in (a, b)})
    merged = []
    for a, b in zip(edges, edges[1:]):
        got = predicate(a + (b - a) / 2)
        if not got:
            continue
        if merged and merged[-1][1] == a and merged[-1][2] == got:
            merged[-1][1] = b
        else:
            merged.append([a, b, got])
    return merged


def test_source_probability_population(doc: dict) -> None:
    """The field would populate 26 rows, and must never drift off that number.

    A field this sparse drifts invisibly: 400 populated rows or zero would both
    look plausible in a spot check. The counts are therefore asserted EXACTLY,
    against the config's declared numbers, so either direction fails loudly.
    """
    conf = CONF["source_probability"]
    pop = conf["projected_population"]
    span = (parse(doc["meta"]["span_start_utc"]), parse(doc["meta"]["span_end_utc"]))

    # ------------------------------------------------ catalogue A: 15 records
    got = {k: sum(1 for r in doc["records"] if f(r))
           for k, f in CARRIED_CATALOGUE_A.items()}
    record("Carried catalogue-A families populate exactly the declared counts",
           got == pop["astronomy_records_by_family"], str(sorted(got.items())))

    total = sum(got.values())
    record(f"source_probability populates exactly {pop['astronomy_records_total']} "
           f"astronomy records, no more and no fewer",
           total == pop["astronomy_records_total"] == 15,
           f"{total} of {len(doc['records'])} records "
           f"({100 * total / len(doc['records']):.2f}%)")

    hit = [r for r in doc["records"] if any(f(r) for f in CARRIED_CATALOGUE_A.values())]
    record("All of them fall inside IST civil 2027",
           all(in_2027(r) for r in hit) is pop["all_15_fall_in_ist_civil_2027"],
           f"{sum(in_2027(r) for r in hit)}/{len(hit)}")

    # ------------------------------------ catalogue B: 11 rule-layer firings
    sg = {b: _sign_timeline(doc, b, span) for b in RESIDENCY_BODIES}
    nk = {b: _nakshatra_timeline(doc, b, span) for b in ("Mars", "Rahu")}
    others = [b for b in RESIDENCY_BODIES if b not in ("Mercury", "Venus")]

    def alone(when):
        sign = _value_at(sg["Mercury"], when)
        if (sign and sign == _value_at(sg["Venus"], when)
                and not any(_value_at(sg[o], when) == sign for o in others)):
            return sign
        return None

    def shared(tls, a, b):
        def pred(when):
            x = _value_at(tls[a], when)
            return x if x and x == _value_at(tls[b], when) else None
        return pred

    fired = {
        "mercury_venus_alone": len(_windows(list(sg.values()), alone)),
        "rahu_mars_together":
            len(_windows([sg["Mars"], sg["Rahu"]], shared(sg, "Mars", "Rahu")))
            + len(_windows([nk["Mars"], nk["Rahu"]], shared(nk, "Mars", "Rahu"))),
        "venus_jupiter_same_sign":
            len(_windows([sg["Venus"], sg["Jupiter"]], shared(sg, "Venus", "Jupiter"))),
        "mars_ahead_of_jupiter": 0,          # set below, by the ahead/behind test
    }

    mj = _windows([sg["Mars"], sg["Jupiter"]], shared(sg, "Mars", "Jupiter"))
    ahead = []
    for a, b, _sign in mj:
        seps = [(ephem.longitude(t, "Mars") - ephem.longitude(t, "Jupiter") + 180) % 360 - 180
                for t in (a + dt.timedelta(hours=1), a + (b - a) / 2,
                          b - dt.timedelta(hours=1))]
        ahead.append(all(x > 0 for x in seps))
    fired["mars_ahead_of_jupiter"] = sum(ahead)

    record("Mars is ahead of Jupiter throughout every shared-sign window, so the "
           "'ahead' block fires and the 'behind' block does not",
           len(mj) == 3 and all(ahead),
           f"{len(mj)} shared-sign windows, ahead in {sum(ahead)}")

    record("Carried catalogue-B families fire exactly the declared number of times",
           fired == pop["rule_layer_firings_by_family"], str(sorted(fired.items())))

    record(f"Combined populated rows = {pop['combined_total']}, the number the "
           f"field's description is written around",
           total + sum(fired.values()) == pop["combined_total"] == 26,
           f"{total} astronomy + {sum(fired.values())} rule-layer")

    # -------------------------------------------- the exclusion, and the ban
    sat_nep = [r for r in doc["records"] if r["event_class"] == "conjunction"
               and set(r["bodies"]) == {"Saturn", "Neptune"}]
    record("Saturn-Neptune does not recur in the span, which is what excludes the "
           "source's single highest label",
           not sat_nep,
           f"{len(sat_nep)} records; excluded_by "
           f"{conf['exclusions']['saturn_neptune_conjunction']['excluded_by']}")

    leaked = [r["id"] for r in doc["records"]
              if "source_probability" in r or "source_probability" in r["qa"]]
    record("The field is absent from every astronomy record, as the config declares",
           not leaked and conf["emitted_on_astronomy_records"] is False,
           f"{len(leaked)} records carry it")


# ------------------------------------------- 12. the panchang ingress classes
#: Both classes are crossings of an angle BETWEEN the Moon and the Sun rather
#: than of one body's longitude, so the checks the position classes get -- the
#: crossing sits on an exact multiple of the arc, the from/to indices are
#: consecutive, the series never skips a division -- are re-stated here against
#: that angle instead of against `lon_sid`.
#:
#: The source-side validation lives in tests/test_2026_regression.py, where it
#: belongs: a check that reads only the generated file can compare the engine
#: with itself and with nothing else.

def _tithi_records(doc):
    return [r for r in doc["records"] if r["event_class"] == "tithi_ingress"]


def _yoga_records(doc):
    return [r for r in doc["records"] if r["event_class"] == "yoga_ingress"]


def test_panchang_ingress_shape(doc: dict) -> None:
    tithi, yoga = _tithi_records(doc), _yoga_records(doc)

    bad = [r["id"] for r in tithi + yoga
           if r["bodies"] != ["Moon", "Sun"] or r["kind"] != "instant"
           or r["qa"]["data_certainty"] != "A"]
    record("Every panchang ingress names both bodies, is an instant, and is "
           "certainty A", not bad, f"{len(bad)} bad of {len(tithi + yoga)}")

    bad = [r["id"] for r in tithi
           if "frame_free_elongation_ayanamsha_cancels" not in r["qa"]["flags"]]
    record("Every tithi ingress states on its own record that the ayanamsha "
           "cancels", not bad, f"{len(bad)} missing the flag")

    bad = [r["id"] for r in yoga
           if "ayanamsha_dependent_sum_of_longitudes" not in r["qa"]["flags"]]
    record("Every yoga ingress states the opposite on its own record -- the "
           "sum carries the ayanamsha twice", not bad,
           f"{len(bad)} missing the flag")

    both = [r["id"] for r in tithi + yoga
            if "frame_free_elongation_ayanamsha_cancels" in r["qa"]["flags"]
            and "ayanamsha_dependent_sum_of_longitudes" in r["qa"]["flags"]]
    record("No record claims both, which would make the distinction "
           "decorative", not both, f"{len(both)} carry both")


def test_panchang_ingress_indices(doc: dict) -> None:
    """from/to are consecutive divisions, and the fortnight follows the number.

    The paksha is not an independent field to be filled in: tithis 1-15 are the
    bright half by definition, so a record whose paksha disagrees with its own
    number was assembled from two different instants.
    """
    tithi = _tithi_records(doc)
    bad = [r["id"] for r in tithi
           if (r["astronomy"]["tithi_from"] % 30) + 1
           != r["astronomy"]["tithi_to"]]
    record("Every tithi ingress steps exactly one tithi forward, 30 wrapping "
           "to 1", not bad, f"{len(bad)} bad of {len(tithi)}")

    bad = [r["id"] for r in tithi
           if r["astronomy"]["paksha_to"]
           != ("Shukla" if r["astronomy"]["tithi_to"] <= 15 else "Krishna")]
    record("Every tithi ingress's fortnight follows from its own tithi number",
           not bad, f"{len(bad)} disagree with their own number")

    bad = [r["id"] for r in tithi
           if (r["panchang"]["tithi"], r["panchang"]["paksha"])
           != (r["astronomy"]["tithi_to"], r["astronomy"]["paksha_to"])]
    record("The panchang layer carries the tithi ENTERED, not the one sampled "
           "at the cusp", not bad,
           f"{len(bad)} of {len(tithi)} disagree with the crossing index -- "
           f"without the override about half would, since the instant IS the "
           f"boundary and is rounded to the second")

    yoga = _yoga_records(doc)
    bad = [r["id"] for r in yoga
           if (r["astronomy"]["yoga_from"] % 27) + 1
           != r["astronomy"]["yoga_to"]]
    record("Every yoga ingress steps exactly one yoga forward, 27 wrapping "
           "to 1", not bad, f"{len(bad)} bad of {len(yoga)}")

    bad = [r["id"] for r in yoga
           if r["panchang"]["yoga"] != r["astronomy"]["yoga_name_to"]]
    record("The panchang layer carries the yoga ENTERED", not bad,
           f"{len(bad)} of {len(yoga)} disagree with the crossing index")


def test_panchang_ingress_lands_on_the_arc(doc: dict) -> None:
    """The instant sits on an exact multiple of the arc, checked in the angle.

    The position classes are checked against `lon_sid`; these cannot be,
    because the quantity that crosses is a difference and a sum. So the angle
    is recomputed at each record's own instant -- which is what the position
    checks in this file already do for their own frames.
    """
    for cls, records, angle_fn, arc in (
            ("tithi", _tithi_records(doc), ephem.elongation_angle, 12.0),
            ("yoga", _yoga_records(doc), ephem.sum_angle, 360.0 / 27.0)):
        worst, worst_id = 0.0, None
        for r in records:
            when = parse(r["time"]["t_start_utc"])
            deg = angle_fn(when)
            off = min(deg % arc, arc - (deg % arc))
            if off > worst:
                worst, worst_id = off, r["id"]
        # The instant is rounded to the second and the elongation moves about
        # 1.4e-4 degrees in one, so a boundary can sit that far off and no
        # further. An arcminute is the tolerance the position classes use.
        record(f"Every {cls} ingress sits on an exact multiple of its arc",
               worst <= ARCMIN, f"worst offset {worst * 3600:.2f} arcsec"
               + (f" at {worst_id}" if worst_id else ""))


def test_panchang_series_is_unbroken(doc: dict) -> None:
    """In time order the divisions advance one at a time and never repeat.

    A skipped division is what a scan step too coarse for the fastest
    elongation would produce, and it would be invisible in a spot check: the
    series would still read as a plausible list of dates.
    """
    for cls, records, field, n in (
            ("tithi", _tithi_records(doc), "tithi_to", 30),
            ("yoga", _yoga_records(doc), "yoga_to", 27)):
        ordered = sorted(records, key=lambda r: r["time"]["t_start_utc"])
        breaks = [b["id"] for a, b in zip(ordered, ordered[1:])
                  if (a["astronomy"][field] % n) + 1 != b["astronomy"][field]]
        record(f"The {cls} series advances one division per record across the "
               f"whole span", not breaks,
               f"{len(ordered)} records, {len(breaks)} breaks"
               + (f" e.g. {breaks[:2]}" if breaks else ""))

        gaps = [(a["time"]["t_start_utc"], b["time"]["t_start_utc"])
                for a, b in zip(ordered, ordered[1:])
                if (parse(b["time"]["t_start_utc"])
                    - parse(a["time"]["t_start_utc"])) > dt.timedelta(hours=30)]
        record(f"No {cls} runs longer than 30 hours, the margin the scan step "
               f"was chosen against", not gaps,
               f"{len(gaps)} over-long" + (f" e.g. {gaps[0]}" if gaps else ""))


# ------------------------------------------------------- the horizon classes
# The third event series, and the first that is not a fact about the sky. Every
# check below is about the thing that makes it different: a rise or a set
# belongs to ONE place, so the location is the load-bearing field and the
# convention is the load-bearing flag.

#: Daylight hours at each latitude, wide enough that a real year fits and
#: narrow enough that a day-shifted or wrong-venue series does not. Mumbai sits
#: at 19N and swings about two hours over the year; New York at 41N swings six.
_PLAUSIBLE_DAY = {"mumbai": (10.5, 13.5), "new_york": (8.5, 15.5)}


def _horizon_flag(rec: dict, key: str):
    for f in rec["qa"]["flags"]:
        if f.startswith(key + "="):
            return f.split("=", 1)[1]
    return None


def _missing_dates(dates) -> list:
    have = set(dates)
    out, day = [], min(have)
    while day <= max(have):
        if day not in have:
            out.append(day)
        day += dt.timedelta(days=1)
    return out


def test_horizon_records_all_carry_a_location(doc: dict) -> None:
    """The rule the schema enforces, asserted again on the emitted file.

    `events.LOCATION_REQUIRED` raises at build time, so this cannot fail while
    the build is the only writer. It is here because the claim being made is
    about the FILE: a reader trusting the location field is trusting it on
    every row, and a guard that only ever ran inside the generator would not
    say so. It would also catch a record edited into the file by hand, which is
    the one failure a construction-time guard cannot see.
    """
    horizon = [r for r in doc["records"]
               if r["event_class"] in ev.LOCATION_REQUIRED]
    missing = [r["id"] for r in horizon if not r["location"]]
    record("Every sunrise and sunset record names its location",
           bool(horizon) and not missing,
           f"{len(horizon)} horizon records, {len(missing)} with no location")

    venues = {r["location"] for r in horizon}
    unknown = sorted(venues - set(CONF["locations"]))
    record("Every horizon location is one config declares", not unknown,
           str(unknown) or f"venues: {sorted(venues)}")


def test_both_venues_are_generated(doc: dict) -> None:
    """Neither venue is a default for the other, so neither may be absent.

    The 2026 source computes rise and set for Mumbai alone and says so -- "the
    reference place declared by this calendar". That is a fact about the
    source. It is not a licence to emit one venue and leave a New York reader
    to infer the other, which is what a single-venue series would amount to:
    the two sunrises are about ten and a half hours apart and no fixed offset
    recovers one from the other across a year.
    """
    for cls in ("sunrise", "sunset"):
        per = collections.Counter(r["location"] for r in doc["records"]
                                  if r["event_class"] == cls)
        record(f"{cls} is generated for every configured venue",
               set(per) == set(CONF["locations"]) and all(per.values()),
               ", ".join(f"{k} {v}" for k, v in sorted(per.items())))


def test_one_crossing_per_venue_civil_day(doc: dict) -> None:
    """Exactly one rise and one set per venue per civil day, none missing.

    Counted in each venue's OWN zone, which is the point: the same UTC instant
    is 01-Dec in Mumbai and 30-Nov in New York, so a series keyed on the
    primary zone would drop or double a New York day. Each record states its
    venue date as a flag, and this confirms the flag agrees with the instant
    rather than trusting either one alone.
    """
    for cls in ("sunrise", "sunset"):
        for loc_key, loc in CONF["locations"].items():
            tz = ZoneInfo(loc["tz"])
            rows = [r for r in doc["records"]
                    if r["event_class"] == cls and r["location"] == loc_key]
            dates = [parse(r["time"]["t_start_utc"]).astimezone(tz).date()
                     for r in rows]
            dupes = [d for d, n in collections.Counter(dates).items() if n > 1]
            gaps = _missing_dates(dates)
            stale = [r["id"] for r, d in zip(rows, dates)
                     if _horizon_flag(r, "civil_date_at_venue")
                     != d.strftime("%Y-%m-%d")]
            record(f"{cls} at {loc_key}: one per civil day, no gap, no repeat",
                   not dupes and not gaps and not stale,
                   f"{len(rows)} days {min(dates)}..{max(dates)}; "
                   f"{len(dupes)} repeated, {len(gaps)} missing, {len(stale)} "
                   "whose stated venue date disagrees with the instant")


def test_the_sun_rises_before_it_sets(doc: dict) -> None:
    """At both venues, every civil day, with a day length its latitude allows.

    The cheapest check that would have caught the defect this series was built
    on top of. `panchang.sunrise` searched from local NOON and so returned the
    rise of the FOLLOWING day: a true instant filed under the wrong date, which
    no comparison against a tithi span could see, because a set of sunrise
    instants shifted by one day still covers the same interval and still counts
    the same crossings. Anchored at the venue's own civil midnight the pair
    brackets its own day, and a regression to the old anchor fails every one of
    these at once.
    """
    for loc_key, loc in CONF["locations"].items():
        tz = ZoneInfo(loc["tz"])

        def by_date(cls):
            return {parse(r["time"]["t_start_utc"]).astimezone(tz).date():
                    parse(r["time"]["t_start_utc"])
                    for r in doc["records"]
                    if r["event_class"] == cls and r["location"] == loc_key}

        rises, sets = by_date("sunrise"), by_date("sunset")
        shared = sorted(set(rises) & set(sets))
        inverted = [d for d in shared if not rises[d] < sets[d]]
        hours = [(sets[d] - rises[d]).total_seconds() / 3600 for d in shared]
        lo, hi = _PLAUSIBLE_DAY[loc_key]
        record(f"At {loc_key} the Sun rises before it sets on every day",
               not inverted, f"{len(shared)} days, {len(inverted)} inverted")
        record(f"At {loc_key} the day length stays inside its latitude's range",
               all(lo <= h <= hi for h in hours),
               f"{min(hours):.2f}h to {max(hours):.2f}h over {len(hours)} days, "
               f"expected {lo}-{hi}h")


def test_every_horizon_record_states_its_convention(doc: dict) -> None:
    """The grade is B because the convention is a choice, so it must be stated.

    A time with no convention on it is not reproducible: disc centre against
    upper limb, and refraction against none, move a Mumbai sunrise by about
    four and a half minutes between them. The flag names the one in force and
    is required to be the one `panchang` actually used, read from the module
    rather than retyped here, so the record and the code cannot drift apart.
    """
    from finastro import panchang as pn
    want = f"rise_set_convention={pn.RISE_SET_CONVENTION}"
    horizon = [r for r in doc["records"]
               if r["event_class"] in ev.LOCATION_REQUIRED]
    bad = [r["id"] for r in horizon if want not in r["qa"]["flags"]]
    record("Every horizon record names the rise/set convention it was computed "
           "under", not bad,
           f"{want} on {len(horizon) - len(bad)} of {len(horizon)}")

    graded = {r["qa"]["data_certainty"] for r in horizon}
    record("Every horizon record is graded B and not A", graded == {"B"},
           f"grades present {sorted(graded)}; a rise depends on disc, "
           "refraction and horizon height, so it is definition-sensitive by "
           "construction and cannot be A")

    nogeo = [r["id"] for r in horizon
             if _horizon_flag(r, "horizon_geo_lat_lon_alt") is None]
    record("Every horizon record states the horizon it was taken from",
           not nogeo, f"{len(horizon) - len(nogeo)} carry lat,lon,alt")


def test_the_convention_matches_the_combustion_calibration() -> None:
    """One convention, stated in two places, checked to be the same one.

    Kalamsha is the gap between a planet's rise and the Sun's rise. Measured
    between two different conventions it is not a gap at all, and the 2026
    thresholds were calibrated under the one `combustion.rise_set_flags` names.
    Were the sunrise series to move off it, every threshold in config would
    quietly become a threshold on a different quantity.
    """
    from finastro import panchang as pn
    record("The sunrise series and the combustion calibration use one "
           "rise/set convention",
           pn.RISE_SET_CONVENTION == CONF["combustion"]["rise_set_flags"],
           f"panchang {pn.RISE_SET_CONVENTION!r} vs config "
           f"{CONF['combustion']['rise_set_flags']!r}")


def test_a_location_free_horizon_record_is_refused() -> None:
    """The schema guard exercised rather than assumed.

    "There is no default venue" is a claim about what the code does, and the
    only way to check a refusal is to attempt the thing being refused.
    """
    t = SPAN_START + dt.timedelta(days=1)
    astro, _ = ev.positional(t, "Sun")
    try:
        ev.build("sunrise", "horizon/sunrise", ["Sun"], "instant", t, astro,
                 ev.qa_for(t, "B"))
        ok, detail = False, "a location-free sunrise record was ACCEPTED"
    except ValueError as exc:
        ok, detail = True, str(exc).split(":", 1)[-1].strip()[:88]
    record("A sunrise record with no location is refused by the schema",
           ok, detail)


def main() -> int:
    doc = load()
    print(f"ephemeris backend: {ephem.init()}")
    print(f"records: {doc['meta']['record_count']}\n")
    test_counts(doc)
    test_the_karana_series_is_the_tithi_series_at_half_the_arc(doc)
    test_unique_ids(doc)
    test_span(doc)
    test_ordering(doc)
    test_certainty(doc)
    test_carry_in_out(doc)
    test_no_interpretation_leaked(doc)
    test_ingress_boundaries(doc)
    test_ingress_direction(doc)
    test_saturn_round_trip(doc)
    test_stations(doc)
    test_station_precision(doc)
    test_eclipses(doc)
    test_dignity_is_sign_level(doc)
    test_dignity_known_cases(doc)
    test_navamsa_dignity_frame(doc)
    test_navamsa_source_omission_is_checked_in_the_D9_frame()
    test_the_moons_navamsa_series_is_bounded_by_its_own_sign_ingresses(doc)
    test_a_dignity_the_source_never_labels_says_so_on_the_record(doc)
    test_vargottama_on_records(doc)
    test_vargottama_is_not_folded_into_dignity(doc)
    test_ingress_frames_are_cusp_consistent(doc)
    test_nodes_have_no_dignity(doc)
    test_node_lord_relationship(doc)
    test_node_lord_relationship_is_period_constant(doc)
    test_moon_excluded_from_pairs(doc)
    test_dual_stamps(doc)
    test_dst_not_hardcoded()
    test_provenance(doc)
    test_source_probability_population(doc)
    test_panchang_ingress_shape(doc)
    test_panchang_ingress_indices(doc)
    test_panchang_ingress_lands_on_the_arc(doc)
    test_panchang_series_is_unbroken(doc)
    test_horizon_records_all_carry_a_location(doc)
    test_both_venues_are_generated(doc)
    test_one_crossing_per_venue_civil_day(doc)
    test_the_sun_rises_before_it_sets(doc)
    test_every_horizon_record_states_its_convention(doc)
    test_the_convention_matches_the_combustion_calibration()
    test_a_location_free_horizon_record_is_refused()
    test_speed_class_crossings(doc)

    width = max(len(n) for n, _, _ in _results)
    failed = 0
    for name, status, detail in _results:
        failed += status == FAIL
        print(f"[{status}] {name.ljust(width)}  {detail}")
    print(f"\n{len(_results) - failed}/{len(_results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
