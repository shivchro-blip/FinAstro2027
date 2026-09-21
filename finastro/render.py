"""Render the 2027 calendar: JSON master, generated HTML, CSV.

The verdict layer produces one row per rule, instrument and venue civil day. This
turns those into a calendar a reader can use, in the display format the project
specified:

    Date - Time IST | Time ET (EDT/EST) | Event | Vedic interpretation |
    Financial-market theme | Confidence/risk label

Three things this module is careful about, because each is a place a calendar
quietly lies:

* **Tagged uncertainty.** Every row carries its axes pair, its derived tier, its
  claim tag, its confidence and its flags. A row rendered without those would read
  as a prediction rather than as a condition with a provenance.
* **The dual date.** When the Eastern civil date differs from the IST one the row
  shows both, with the marker, and the SHIFT IS ALWAYS ZERO OR MINUS ONE --
  Eastern is never ahead of IST. Window ends are converted independently, so a
  window spanning a DST change shows two different Eastern offsets.
* **The epistemic apparatus is visible, not buried.** The HTML carries the
  certainty grades and both C grounds, the claim tags, all 33 blocked sections
  with what each waits for, the source defects found, and the standing statement
  that this is a speculative interpretive framework and not investment advice.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import html
import json
import pathlib

from .basetrack import EVIDENCE_SOURCE, build_base_events
from .config import CONF
from .timezones import ET, IST, SHIFT_MARK, date_stamp, span_dates, stamp
from .verdicts import INSTRUMENTS, build_verdicts

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
YEAR = CONF["year"]

OUT_JSON = BUILD / "calendar_2027.json"
OUT_HTML = BUILD / "calendar_2027.html"
OUT_CSV = BUILD / "calendar_2027.csv"

#: Carried into every output and rendered at the top of the HTML. The project's
#: own framing, stated once rather than left to be inferred from the column
#: names.
DISCLAIMER = (
    "Financial astrology is a speculative interpretive framework. The dates and "
    "conditions in this calendar are computed from an ephemeris and ported from "
    "a 2026 source document; the interpretations are that source's claims, "
    "carried verbatim or absent. Nothing here is a forecast, a prediction, or "
    "investment advice, and no confidence has been raised above `untested` for "
    "any row.")


def _sector_of(instrument: str) -> str:
    return INSTRUMENTS[instrument]["label"]


#: The two values `row_kind` takes, read from config rather than restated. The
#: whole point of the field is that a consumer can key on it, so the set it may
#: take is a ruling on record.
ROW_KINDS = tuple(v["id"] for v in CONF["row_kinds"]["values"])
ROW_KIND_VERDICT, ROW_KIND_EVENT = "verdict", "event"

#: THE SECOND DISCRIMINATOR, and it is a second FIELD rather than two more
#: values of the first. `row_kind` means verdict vs sky; this means window vs
#: day. Giving `row_kind` the second axis would have made `records_by_row_kind`
#: a count over a cross product no denominator in `meta` is keyed to, which is
#: the stale-denominator failure this build has recorded four times --
#: SPAN_VS_DAILY_PROPOSAL.md section 3 named the remedy before the collapse
#: existed. See `conventions.yaml -> row_kinds.row_span`.
#:
#: It is set on EVERY row by `render_rows` and `render_base_rows`, before
#: `collapse_windows` runs and whether or not that row is ever collapsed. A row
#: that still stands for one civil day says so positively; there is no row in
#: the file whose shape has to be inferred from the presence of another field.
ROW_SPANS = tuple(v["id"] for v in CONF["row_kinds"]["row_span"]["values"])
ROW_SPAN_DAY, ROW_SPAN_WINDOW = "day", "window"

#: The `no_instant_reason` values Model A folds, and the two it does not.
#:
#: `date_only` covers BOTH halves the census splits by rule id -- the ephemeris
#: date-granular windows and b101's `sky.civil_day_span`. The split matters to
#: the FIGURES, because one half is population-sensitive and the other is not;
#: it does not matter here, because neither half has an instant at either end
#: and both reprint one pair of endpoints on every day they cover.
#:
#: `anchored` and `named_contacts` are absent by DECISION and not by oversight.
#: An anchored row's date was chosen by this build because the body never
#: crossed its frame, so widening it to a year would read as a state somebody
#: observed. An eclipse has several instants, not none.
COLLAPSED_REASONS = ("date_only", "period_cut")


def _time_fields(row) -> dict:
    """The time block of a row, and the ONE PLACE that decides about clock times.

    Two branches, and they are handed two DIFFERENT OBJECTS. A row whose start
    is a measured instant gets a `DualStamp`, which has `ist_time`, `et_time`,
    `et_abbr` and `et_offset`. A row whose start is not gets a `DateStamp`,
    which HAS NONE OF THOSE ATTRIBUTES -- reading one raises AttributeError
    here, at build time.

    That is the difference between this and the arrangement it replaced. Before
    15-Sep-2026 there was one stamp type, it always carried a time, and every
    row without an instant rendered `00:00 IST` beside a previous-Eastern-day
    afternoon. None of them was an event at midnight, and no amount of care in
    this function could have stopped it, because the object it was handed had a
    time on it.

    RE-DERIVED 15-Sep-2026, and the figures this docstring used to carry --
    `662 rows across 27 rules`, `249 / 147 / 45 / 12` -- are WITHDRAWN rather
    than corrected in place. They were measured against a transient build that
    was never committed, no generator for them exists, and no slicing of this
    build or of the 5,209-row build before it reproduces three of the four. The
    population is measurable and is stated where it can be checked --
    `meta.time.rows_without` on the rendered artifact. THAT KEY CHANGED UNIT ON
    21-Sep-2026 and the figure here is restated rather than left standing: 894
    was a count of DAILY rows, over 99 spans, in the 15-Sep build. Since the
    collapse `rows_without` counts RENDERED rows -- 135 -- and the daily figure
    lives beside it as `by_no_instant_reason_daily_row_equivalent`, summing to
    930 over the grown build. Neither number is wrong and they are not the same
    measurement.
    Per cause, as catalogue-B firings, distinct (rule, location, civil day):
    331 date-granular combust and rise windows, 142 shared-sign windows already
    running at the carry-in, 105 civil-day windows across two venues, and 11
    reference-table anchors carrying 12 rows. `45` was the Mumbai half of `105`,
    and `12` counted ROWS where its three neighbours counted FIRINGS.

    `t_utc` / `t_start_utc` / `t_end_utc` are the other half, and they are what
    makes the calendar REJOINABLE: before them, checking a row against the
    ephemeris meant matching on event name and date.
    """
    out: dict = {
        "instant_precision": row.precision,
        "open_start": row.open_start,
        "open_end": row.open_end,
        # THE SECOND CUT, and the one `open_*` was silently standing in for.
        # `open_*` marks `Sky.span_start`'s edge; these mark `civil_days`'
        # civil-year clip, which a daily render never had to name because the
        # out-of-year days simply had no rows. A base-track row is one record
        # rendered as itself and is never expanded across days, so nothing is
        # ever clipped off one -- `getattr` returns False for it, which is the
        # measured answer and not a default standing in for an unasked
        # question. See `sky.year_clip`.
        "clipped_start": getattr(row, "clipped_start", False),
        "clipped_end": getattr(row, "clipped_end", False),
        "t_utc": None,
        "t_start_utc": None,
        "t_end_utc": None,
        "no_instant_reason": None,
    }
    # An INSTANT row carries one time and says so; a SPAN row carries two. One
    # time cannot stand for two, and `t_utc` on a 220-day window would be a
    # date pretending to be a moment.
    if row.is_instant:
        out["t_utc"] = _iso(row.start_utc)
    else:
        out["t_start_utc"] = _iso(row.start_utc)
        out["t_end_utc"] = _iso(row.end_utc)

    if row.has_instant_start:
        st = stamp(row.start_utc)
        out.update({
            "date_ist": st.ist_date,
            "date_et": st.et_date,
            "day_shift": st.day_shift,
            "time_ist": f"{st.ist_time} IST",
            "time_et": f"{st.et_time} {st.et_abbr}",
            "et_offset": st.et_offset,
            "dual_date": bool(st.day_shift),
        })
        return out

    # No single printable time. `date_stamp` returns an object with no time
    # attribute at all, so nothing below can reach for one.
    #
    # A verdict row's reason is its span precision, or `period_cut` where the
    # span is exact but the boundary is the generated period's. A base-track
    # row states its own, because it has a fourth case: an eclipse has SEVERAL
    # instants, not none.
    reason = getattr(row, "no_instant_reason", None) or (
        row.precision if row.precision != "exact" else "period_cut")
    ds = date_stamp(row.civil_date, reason)
    out.update({
        "date_ist": ds.ist_date,
        # A day shift is a statement about where an INSTANT falls in two
        # calendars. A civil day at a venue does not shift; it is that venue's
        # day. So there is no Eastern date to print and no marker to print it
        # with, and printing one would be the same invention in a second field.
        "date_et": None,
        "day_shift": 0,
        "time_ist": None,
        "time_et": None,
        "et_offset": None,
        "dual_date": False,
        "no_instant_reason": ds.no_instant_reason,
    })
    return out


def _iso(when) -> str | None:
    return when.strftime("%Y-%m-%dT%H:%M:%SZ") if when else None


def render_rows(verdicts) -> list[dict]:
    """One display row per verdict, in the specified column order."""
    rows = []
    for v in verdicts:
        rows.append({
            "row_kind": ROW_KIND_VERDICT,
            # Every row is born a day row. `collapse_windows` is the only thing
            # that turns one into a window, and it does so by rewriting this
            # field rather than by adding one.
            "row_span": ROW_SPAN_DAY,
            "date": v.civil_date.strftime("%d-%b-%Y"),
            **_time_fields(v),
            "instrument": v.instrument,
            "instrument_label": _sector_of(v.instrument),
            "venue": v.venue,
            "event": v.rule_id,
            "event_section": v.provenance,
            "vedic_interpretation": v.verdict_text,
            "interpretation_basis": v.significance,
            "financial_theme": f"{_sector_of(v.instrument)} - {v.rule_id.split('_', 1)[-1].replace('_', ' ')}",
            "confidence": v.confidence,
            "claim_tag": v.claim_tag,
            "evidence_source": v.evidence_source,
            "construction": v.construction,
            "tier": v.tier,
            "source_probability": v.source_probability,
            "source_probability_disputed": v.source_probability_disputed,
            "crude_path": v.crude_path,
            "flags": v.flags,
        })
    return rows


def render_base_rows(events) -> list[dict]:
    """One display row per astronomy record. THE BASE TRACK.

    The forbidden keys are forbidden by ABSENCE, not by a null. `BaseEvent` has
    no instrument, tier, claim_tag, construction, verdict_text,
    source_probability or confidence attribute, so there is nothing here to
    read one from -- the row is not a verdict row with the interpretation left
    empty, it is a different row. `basetrack.FORBIDDEN_FIELDS` lists them and
    the harness asserts none appears, because a dict is still a dict and a
    later hand could add the key even though the dataclass could not.

    `evidence_source` IS emitted, as `none`, and `tier` is not emitted at all.
    That pairing is deliberate: `tier_derivation` maps (none, null) to
    `no_rule`, so an event row that carried a derived tier would arrive as 405
    more `no_rule` rows and disappear into the 3,285 that were already there.
    The tier of an ingress is not `no_rule`; an ingress has no tier.
    """
    rows = []
    for e in events:
        row = {
            "row_kind": ROW_KIND_EVENT,
            "row_span": ROW_SPAN_DAY,
            "date": e.civil_date.strftime("%d-%b-%Y"),
            **_time_fields(e),
            "event": e.label,
            "event_section": e.rule_family,
            "record_id": e.record_id,
            "event_class": e.event_class,
            "rule_family": e.rule_family,
            "bodies": list(e.bodies),
            "kind": e.kind,
            "evidence_source": EVIDENCE_SOURCE,
            "data_certainty": e.data_certainty,
            "record_precision": e.record_precision,
            "sign": e.astronomy.get("sign"),
            "nakshatra": e.astronomy.get("nakshatra"),
            "motion": e.astronomy.get("motion"),
            "location": e.location,
            "flags": list(e.qa_flags),
        }
        if e.contacts:
            row["contacts"] = _contact_rows(e)
        rows.append(row)
    return rows


def _contact_rows(event) -> list[dict]:
    """An eclipse row's named contacts. See row_kinds.eclipse_contacts.

    Each contact carries its NAME and the record key it was read from, so the
    row states which of the five moments it is showing. An eclipse row that
    emitted one unlabelled time was choosing among begin, totality_begin, max,
    totality_end and end and not saying which -- and the record has carried all
    of them, fully stamped, the whole time.
    """
    out = []
    for name, key, st in event.contacts:
        out.append({
            "contact": name,
            "record_key": key,
            "t_utc": st["utc"],
            "date_ist": st["ist_date"],
            "time_ist": f"{st['ist_time']} IST",
            "date_et": st["et_date"],
            "time_et": f"{st['et_time']} {st['et_abbr']}",
            "et_offset": st["et_offset"],
            "day_shift": st["day_shift"],
        })
    return out


# ------------------------------------------------------------- the collapse

def _span_key(row: dict) -> tuple:
    """The `(row_kind, rule, instrument, venue, window)` group one row stands for.

    THE SAME KEY `tools/cause_census.py` COUNTS SPANS WITH, deliberately, so the
    number of window rows this produces and the number of spans the census
    reports are the same measurement rather than two that happen to agree.

    It carries no location: a verdict row's venue determines its firing location
    and an event row's `venue` is absent, and adding one was measured to split
    no group of the 118.
    """
    return (row["row_kind"], row["event"], row.get("instrument"),
            row.get("venue"), row["t_start_utc"], row["t_end_utc"])


def _date(row: dict) -> dt.date:
    return dt.datetime.strptime(row["date"], "%d-%b-%Y").date()


def covered_days(row: dict) -> list[dt.date]:
    """Every civil day in view this row stands for. ONE for a day row.

    THE ONE PLACE THE TWO SHAPES ARE RECONCILED, and the reason no count in
    this build changed meaning at the collapse. A figure keyed on days -- the
    three empty-day figures here, the census's firing, rule-venue-day and
    venue-date units, the HTML date filter -- is asking which days a row exists
    for, and that question had one answer under a daily render because the row
    WAS the day. It still has one answer; it is just no longer free.

    A window row is contiguous by construction: `collapse_windows` refuses to
    fold a group with a hole, so the range below cannot claim a day no daily
    row was built for.
    """
    if row["row_span"] == ROW_SPAN_DAY:
        return [_date(row)]
    first = dt.datetime.strptime(row["first_held"], "%d-%b-%Y").date()
    last = dt.datetime.strptime(row["last_held"], "%d-%b-%Y").date()
    return [first + dt.timedelta(days=i)
            for i in range((last - first).days + 1)]


def collapse_windows(rows: list[dict]) -> list[dict]:
    """Model A: one row per span wherever the row has no instant to lose.

    A PURE RENDERING OPERATION OVER ROWS THAT ALREADY EXIST -- group and drop.
    Every daily row already carries its parent span's endpoints unchanged,
    because `rules.base.fire` copies the span whole onto every day it covers and
    only `civil_date` differs. Nothing is recomputed here and no ephemeris is
    consulted; what is dropped is duplication, and the measurement that says so
    is the `varying` check below rather than the argument.

    **THE DISPLAYED END COMES FROM `span_dates`, NOT FROM `t_end_utc`.** A span
    is half-open: `t_end_utc` is the instant the condition CEASES and the civil
    day it lands in is a day the condition does not hold. `b101`'s February
    Mumbai window ends at `2027-02-20T18:30:00Z`, which is 21-Feb 00:00 IST, and
    the last day it holds is 20-Feb. `timezones.span_dates` takes the civil DAYS
    and raises `TypeError` on a `datetime`, so the off-by-one is refused by the
    type rather than avoided by care -- and until this function existed that
    guard had no reader. It does now.

    **A NON-CONTIGUOUS GROUP IS NOT COLLAPSED.** `SpanDates` says a window over
    one must carry its `dates` list or must not be collapsed, and this takes the
    second. All 118 groups in the 2027 build are contiguous, so the branch costs
    nothing today; what it buys is that a weekday-filtered rule arriving later in
    a no-instant family leaves its days visible and moves the row count, instead
    of asserting a run through days it never fired on.

    **AND IT REFUSES TO FOLD A DISAGREEMENT.** Section 3's case for Model A is
    that a daily row in this population carries nothing its window does not --
    "there is no field in which day 7 differs from day 8". That is measurable and
    is measured: over the 118 groups, `date` and `date_ist` are the only fields
    that ever differ. A later rule that makes a genuine per-day statement inside
    a no-instant span would break the premise, so it raises here rather than
    collapsing the statement away.
    """
    groups: dict[tuple, list[dict]] = collections.defaultdict(list)
    out: list[dict] = []
    for r in rows:
        if r["no_instant_reason"] in COLLAPSED_REASONS:
            groups[_span_key(r)].append(r)
        else:
            out.append(r)

    for key, rs in groups.items():
        rs = sorted(rs, key=_date)
        days = [_date(r) for r in rs]
        sd = span_dates(days)
        if not sd.contiguous:
            # Left daily, and visibly: the rows go back into the file as they
            # were and the row count says so. See the docstring.
            out.extend(rs)
            continue
        varying = sorted(
            f for f in set().union(*(set(r) for r in rs))
            if len({json.dumps(r.get(f), sort_keys=True) for r in rs}) > 1)
        if varying != ["date", "date_ist"] and len(rs) > 1:
            raise ValueError(
                f"{key[1]} over {sd.line()}: the daily rows of one no-instant "
                f"span disagree on {varying}. Model A rests on a daily row in "
                "this population carrying nothing its window does not; a field "
                "that differs between day 7 and day 8 is a per-day statement, "
                "and collapsing it would delete a measurement rather than a "
                "repetition")
        row = dict(rs[0])
        row["row_span"] = ROW_SPAN_WINDOW
        # `date` stays the SORT KEY and is the window's first day in view. Every
        # day-keyed figure in the build reads `covered_days` instead, so the key
        # does not have to double as the answer to "which days is this row on".
        row["date"] = sd.first_held
        row["date_ist"] = sd.first_held
        # `first_held` / `last_held` are VIEW properties by construction --
        # `civil_days` has already applied both the period cut and the year clip
        # before `span_dates` ever sees a day -- so neither asserts a boundary.
        # Which of the two ends is real is what `open_*` and `clipped_*` say,
        # and both pairs ride on the row unchanged. Duration stays absent:
        # `days_in_view` is days IN VIEW, and on an open or clipped span a
        # duration would assert two boundaries the file does not have.
        row.update(sd.as_dict())
        out.append(row)
    return out


# --------------------------------------------------------------------- JSON

def _tally(rows: list[dict], key: str) -> dict:
    """Counter over one key, as a dict with string keys and a stable order."""
    c = collections.Counter(str(r.get(key)) for r in rows)
    return dict(sorted(c.items()))


def _meta_counts(rows: list[dict]) -> dict:
    """Every count in `meta`, KEYED BY row_kind FIRST.

    RULED 15-Sep-2026, and the ruling is about denominators rather than tidiness.
    `records` was 6,677 and every figure under it counted verdict rows, because
    verdict rows were all there were. With the base track in the same file
    `records` became a total over both, and a count that did not name its
    population would say one number while meaning one of two -- which is the
    stale-denominator failure this build has recorded three times already, each
    time as a figure that stayed true-looking while its basis moved underneath
    it.

    IT HAPPENED A FOURTH TIME ON 21-Sep-2026, ON THE OTHER AXIS, and the remedy
    is the same shape. `records` was 8,916 and every row was one civil day; the
    collapse made it 8,121 with 118 of those standing for 913 days. So
    `records_by_row_span`, `daily_row_equivalent` and the signed delta sit
    beside `records_by_row_kind`, and no reader has to know a collapse happened
    in order to avoid comparing this file's total with last week's.

    So the only unsplit number here is the grand total, and its two splits sit
    immediately beside it. Nothing else in `meta` is a bare count.
    """
    by_kind = collections.Counter(r["row_kind"] for r in rows)
    by_span = collections.Counter(r["row_span"] for r in rows)
    verdict = [r for r in rows if r["row_kind"] == ROW_KIND_VERDICT]
    event = [r for r in rows if r["row_kind"] == ROW_KIND_EVENT]
    daily = sum(len(covered_days(r)) for r in rows)
    return {
        # The one total over both populations. Named `records` because that is
        # what it has always been named, and never usable alone: the split is
        # the next key.
        "records": len(rows),
        "records_by_row_kind": dict(sorted(by_kind.items())),
        # THE SECOND SPLIT, and it is the one that moved on 21-Sep-2026.
        # `records` was 8,916 and every row was one civil day. It is 8,121 now
        # and 118 of those rows are windows, so a consumer reading `records` as
        # a day count would be wrong by 795 and would have no way to find out --
        # unless the two numbers sit beside each other, which is what these are.
        "records_by_row_span": dict(sorted(by_span.items())),
        "daily_row_equivalent": daily,
        # SIGNED, and named for what it is measured against, because the same
        # number said two ways is how a figure comes apart. `conventions.yaml`
        # -> row_kinds.row_span.measured_2027.delta is this key and carries this
        # sign.
        "delta_vs_daily_row_equivalent": len(rows) - daily,
        "what_the_collapse_did": (
            "Model A of build/SPAN_VS_DAILY_PROPOSAL.md. A row whose condition "
            "has no instant at either end -- date_only, whether the ephemeris "
            "emitted it as a date or sky.civil_day_span built it, and "
            "period_cut -- reprinted one pair of endpoints on every civil day "
            "it covered, and the days differed in nothing else. Those are now "
            "one row per span carrying first_held and last_held. anchored and "
            "named_contacts rows are NOT collapsed, by decision, and neither "
            "is any span with a clock time: see row_kinds.row_span in "
            "config/conventions.yaml. daily_row_equivalent is what this file "
            "would hold under the old shape, so no figure here has to be "
            "compared against a number that no longer means what it did."),
        "verdict_rows": {
            "total": len(verdict),
            "daily_row_equivalent": sum(len(covered_days(r)) for r in verdict),
            "rows_with_verdict": sum(1 for r in verdict
                                     if r["vedic_interpretation"]),
            "rows_without_verdict": sum(1 for r in verdict
                                        if not r["vedic_interpretation"]),
            "by_instrument": _tally(verdict, "instrument"),
            "by_tier": _tally(verdict, "tier"),
            "by_confidence": _tally(verdict, "confidence"),
            "by_evidence_source": _tally(verdict, "evidence_source"),
        },
        "event_rows": {
            "total": len(event),
            # Stated although it equals `total`: no event row was collapsible
            # with another, because each of the 31 date-granular records is its
            # own span. An absent key would read as an oversight where this
            # reads as the result it is.
            "daily_row_equivalent": sum(len(covered_days(r)) for r in event),
            "by_event_class": _tally(event, "event_class"),
            "by_rule_family": _tally(event, "rule_family"),
            "by_data_certainty": _tally(event, "data_certainty"),
            # An event row has no tier and no verdict, so there is nothing to
            # split by. Stated rather than omitted: an absent key reads as an
            # oversight, and this one is the whole point of `row_kind`.
            "by_tier": None,
            "by_tier_note": (
                "an event row carries no tier. tier_derivation maps "
                "(none, null) to no_rule, so a tier derived here would arrive "
                "as 405 more no_rule rows and vanish into the 3,285 verdict "
                "rows that already carry it. The sky has no tier."),
        },
        # Across both kinds, because it is a property of the ROW and not of the
        # population: how many rows print a clock time, and why the rest do not.
        "time": {
            "rows_with_a_clock_time": sum(1 for r in rows if r["time_ist"]),
            "rows_without": sum(1 for r in rows if not r["time_ist"]),
            "by_no_instant_reason": _tally(
                [r for r in rows if not r["time_ist"]], "no_instant_reason"),
            "by_instant_precision": _tally(rows, "instant_precision"),
            # The same split in the unit the proposal argued in, so the two
            # are readable against each other without arithmetic. Three of
            # these five moved and two did not, and which is which IS the
            # ruling: anchored and named_contacts are point rows by decision.
            "by_no_instant_reason_daily_row_equivalent": {
                k: sum(len(covered_days(r)) for r in rows
                       if not r["time_ist"] and r["no_instant_reason"] == k)
                for k in sorted({r["no_instant_reason"] for r in rows
                                 if not r["time_ist"]})},
        },
        # THREE empty-day figures, not one, and the order matters: the first is
        # the fact about the year, the second is the one a reader meets, and
        # the third is why they differ. See `_days_without`.
        "days": {
            "days_in_year": len({d for r in rows for d in covered_days(r)}),
            "a_day_figure_is_an_overlap_test_since_the_collapse": (
                "every figure under `days` counts a window row on every civil "
                "day it covers, not on its sort date. That is what keeps these "
                "three the same numbers they were under the daily render -- "
                "365, 105, 0 and 2 are identical before and after the collapse "
                "-- and it is the same overlap rule the HTML date filter "
                "applies. See render.covered_days."),
            "days_with_no_event_row": _days_without(rows, ROW_KIND_EVENT),
            "days_with_no_row_of_any_kind": _days_without(rows),
            "days_with_no_row_carrying_a_verdict_text": _days_without(
                rows, predicate=lambda r: bool(r.get("vedic_interpretation"))),
            "empty_days_are_output": (
                "a day carrying no row is a day on which nothing the astronomy "
                "layer tracks happened. Before the base track the calendar "
                "could not be empty on any day a rule fired, so it could not "
                "report absence at all."),
            # The second figure is zero and the first is not, and a reader who
            # met only the second would conclude the year has no quiet days.
            "why_no_day_is_empty_in_the_unfiltered_view": (
                "days_with_no_row_of_any_kind is 0 and that is NOT because "
                "every day carries an event. tier_4 emits a verdict-null "
                "USDINR row for every catalogue-B firing, and those blanket "
                "all 365 days. So the calendar read whole can never be empty, "
                "and the "
                f"{_days_without(rows, ROW_KIND_EVENT)} days that carry no "
                "astronomical event are visible only through row_kind: filter "
                "to row_kind=event and they appear. Absence is reportable on "
                "the base track and only through the discriminator."),
        },
    }


def _days_without(rows: list[dict], row_kind: str | None = None,
                  predicate=None) -> int:
    """Days of the year carrying no row that satisfies the filter.

    One function and not three, because the three empty-day figures differ only
    in which rows they count and stating them side by side is the whole point:
    **105 days carry no event row, 0 carry no row at all, and 2 carry no row
    with a verdict text.** The argument that produced the base track assumed a
    single number (and assumed 32); it is three, and the gap between the first
    two is `tier_4`, not the sky.

    OVER `covered_days`, NOT OVER `date`, since the collapse. A window row's
    `date` is its first day in view; the days it stands for are all of them, and
    a figure that read the sort key would have reported a day as empty on the
    strength of a row being rendered one line higher. All three figures are
    identical before and after the collapse, and this is why.
    """
    keep = [r for r in rows
            if (row_kind is None or r["row_kind"] == row_kind)
            and (predicate is None or predicate(r))]
    have = {d for r in keep for d in covered_days(r)}
    day, last, n = dt.date(YEAR, 1, 1), dt.date(YEAR, 12, 31), 0
    while day <= last:
        if day not in have:
            n += 1
        day += dt.timedelta(days=1)
    return n


def write_json(rows: list[dict], verdicts) -> pathlib.Path:
    doc = {
        "meta": {
            "year": YEAR,
            "generated_by": "finastro/render.py",
            "row_kinds": list(ROW_KINDS),
            **_meta_counts(rows),
            "timezones": {"primary": CONF["display"]["primary_tz"],
                          "secondary": CONF["display"]["secondary_tz"]},
            "source_astronomy": {
                "path": "build/astronomy_2027.json",
                "sha256": __import__("hashlib").sha256(
                    (BUILD / "astronomy_2027.json").read_bytes()
                ).hexdigest(),
            },
            "disclaimer": DISCLAIMER,
        },
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    return OUT_JSON


# ---------------------------------------------------------------------- CSV

#: `row_kind` FIRST, because a reader who sorts the CSV by date is otherwise
#: looking at two populations in one column and cannot see it. `row_span`
#: SECOND, for the same reason one field along: a reader summing a CSV of
#: 8,121 rows is looking at two SHAPES in one column, and the three span
#: columns beside it are what a window row means by its date.
CSV_COLS = ["row_kind", "row_span", "date", "first_held", "last_held",
            "days_in_view", "contiguous",
            "date_ist", "date_et", "day_shift",
            "time_ist", "time_et", "et_offset",
            "t_utc", "t_start_utc", "t_end_utc",
            "instant_precision", "no_instant_reason", "open_start", "open_end",
            "instrument", "instrument_label", "venue", "event",
            "event_section", "vedic_interpretation", "interpretation_basis",
            "financial_theme", "confidence", "claim_tag", "evidence_source",
            "construction", "tier", "source_probability",
            "source_probability_disputed", "crude_path", "flags",
            # base-track columns; empty on a verdict row
            "record_id", "event_class", "rule_family", "bodies", "kind",
            "data_certainty", "record_precision", "sign", "nakshatra",
            "motion", "location", "contacts"]


def write_csv(rows: list[dict]) -> pathlib.Path:
    """The same rows, rectangular.

    A CSV has one header, so the two row kinds share one column list and each
    leaves the other's columns EMPTY. The JSON does not: there an event row
    simply has no `tier` key. The difference is deliberate and is the reason
    `r.get(col, "")` is used below rather than filling every row with nulls
    upstream -- filling them would put a `tier` key on an event row, which is
    exactly what `row_kind` exists to prevent, for the sake of a format that
    cannot tell an empty cell from an absent one anyway.
    """
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {c: r.get(c, "") for c in CSV_COLS}
            out["source_probability"] = (
                "|".join(r["source_probability"])
                if r.get("source_probability") else "")
            out["flags"] = "|".join(r.get("flags") or ())
            out["bodies"] = "|".join(r.get("bodies") or ())
            out["contacts"] = " | ".join(
                f"{c['contact']} {c['date_ist']} {c['time_ist']}"
                for c in (r.get("contacts") or ()))
            w.writerow(out)
    return OUT_CSV


def main() -> int:
    """Render all three artifacts and print the counts, BY ROW KIND.

    Printing one total was fine while there was one population. It is not now,
    and the build log is the first place a changed denominator would have gone
    unnoticed.
    """
    verdicts = build_verdicts()
    events = build_base_events()
    daily = render_rows(verdicts) + render_base_rows(events)
    rows = collapse_windows(daily)
    rows.sort(key=lambda r: (_sortable(r["date"]), r["row_kind"],
                             r.get("instrument") or "", r["event"]))
    j = write_json(rows, verdicts)
    c = write_csv(rows)
    from .html_calendar import write_html
    h = write_html(rows, verdicts)
    # COUNTED OFF THE RENDERED ROWS, not off `verdicts` and `events`. Those two
    # are what the layers produced -- 8,511 verdicts and 405 events -- and the
    # collapse is downstream of both, so printing them beside a rendered total
    # would put three numbers on one line of which only the first was about the
    # file being written.
    n_v = sum(1 for r in rows if r["row_kind"] == ROW_KIND_VERDICT)
    n_e = sum(1 for r in rows if r["row_kind"] == ROW_KIND_EVENT)
    for path in (j, c, h):
        print(f"{len(rows)} rows ({n_v} verdict + {n_e} event) "
              f"-> {path.relative_to(ROOT)}")
    # THE COLLAPSE, IN THE BUILD LOG. `len(rows)` alone would report 8,121 as
    # though it were the 8,916 it replaced, and the build log is the first
    # place a changed denominator goes unnoticed -- which is the argument that
    # split this print by row kind in the first place.
    n_win = sum(1 for r in rows if r["row_span"] == ROW_SPAN_WINDOW)
    print(f"{n_win} window rows stand for {sum(len(covered_days(r)) for r in rows if r['row_span'] == ROW_SPAN_WINDOW)} "
          f"civil days; {len(daily)} daily rows -> {len(rows)} rendered "
          f"({len(rows) - len(daily):+d})")
    print(f"{sum(1 for r in rows if r['time_ist'])} rows print a clock time; "
          f"{sum(1 for r in rows if not r['time_ist'])} print a date only")
    print(f"{_days_without(rows, ROW_KIND_EVENT)} days of {YEAR} carry no "
          f"astronomical event; {_days_without(rows)} carry no row of either "
          f"kind (tier_4's USDINR rows blanket the year)")
    return 0


def _sortable(date_str: str):
    import datetime as _dt
    return _dt.datetime.strptime(date_str, "%d-%b-%Y").date()


if __name__ == "__main__":
    raise SystemExit(main())

