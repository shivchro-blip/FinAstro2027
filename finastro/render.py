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
from .timezones import ET, IST, SHIFT_MARK, date_stamp, stamp
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
    `meta.time.rows_without` on the rendered artifact: 894 rows over 99 spans.
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
    `records` is 7,082, and a count that did not name its population would say
    7,082 while meaning one of two numbers -- which is the stale-denominator
    failure this build has recorded three times already, each time as a figure
    that stayed true-looking while its basis moved underneath it.

    So the only unsplit number here is the grand total, and
    `records_by_row_kind` sits immediately beside it. Nothing else in `meta` is
    a bare count.
    """
    by_kind = collections.Counter(r["row_kind"] for r in rows)
    verdict = [r for r in rows if r["row_kind"] == ROW_KIND_VERDICT]
    event = [r for r in rows if r["row_kind"] == ROW_KIND_EVENT]
    return {
        # The one total over both populations. Named `records` because that is
        # what it has always been named, and never usable alone: the split is
        # the next key.
        "records": len(rows),
        "records_by_row_kind": dict(sorted(by_kind.items())),
        "verdict_rows": {
            "total": len(verdict),
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
        },
        # THREE empty-day figures, not one, and the order matters: the first is
        # the fact about the year, the second is the one a reader meets, and
        # the third is why they differ. See `_days_without`.
        "days": {
            "days_in_year": len({r["date"] for r in rows}),
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
    """
    import datetime as _dt
    keep = [r for r in rows
            if (row_kind is None or r["row_kind"] == row_kind)
            and (predicate is None or predicate(r))]
    have = {r["date"] for r in keep}
    day, last, n = _dt.date(YEAR, 1, 1), _dt.date(YEAR, 12, 31), 0
    while day <= last:
        if day.strftime("%d-%b-%Y") not in have:
            n += 1
        day += _dt.timedelta(days=1)
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
#: looking at two populations in one column and cannot see it.
CSV_COLS = ["row_kind", "date", "date_ist", "date_et", "day_shift",
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
    rows = render_rows(verdicts) + render_base_rows(events)
    rows.sort(key=lambda r: (_sortable(r["date"]), r["row_kind"],
                             r.get("instrument") or "", r["event"]))
    j = write_json(rows, verdicts)
    c = write_csv(rows)
    from .html_calendar import write_html
    h = write_html(rows, verdicts)
    n_v, n_e = len(verdicts), len(events)
    for path in (j, c, h):
        print(f"{len(rows)} rows ({n_v} verdict + {n_e} event) "
              f"-> {path.relative_to(ROOT)}")
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

