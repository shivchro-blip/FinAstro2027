"""Dual-timezone rendering: IST primary, US Eastern secondary.

Eastern offset is resolved through the IANA database, never hardcoded, so the
EDT/EST label and the -9:30 / -10:30 gap from IST are always correct. In 2027
the switch dates are 14-Mar and 07-Nov, but nothing here depends on knowing that.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, asdict
from zoneinfo import ZoneInfo

from .config import CONF

UTC = dt.timezone.utc
IST = ZoneInfo(CONF["display"]["primary_tz"])
ET = ZoneInfo(CONF["display"]["secondary_tz"])

DATE_FMT = CONF["display"]["date_format"]
TIME_FMT = CONF["display"]["time_format"]
SHIFT_MARK = CONF["display"]["day_shift_marker"]


@dataclass(frozen=True)
class DualStamp:
    utc: str
    ist_date: str
    ist_time: str
    ist_weekday: str
    et_date: str
    et_time: str
    et_weekday: str
    et_abbr: str          # EDT or EST
    et_offset: str        # e.g. "-04:00"
    day_shift: int        # ET date relative to IST date: 0 or -1

    def as_dict(self) -> dict:
        return asdict(self)

    def line(self) -> str:
        """`06-Feb-2027 (Sat) - 21:30 IST | 11:00 EST`, with a marker when the
        Eastern date differs."""
        et = f"{self.et_time} {self.et_abbr}"
        if self.day_shift:
            et = f"{SHIFT_MARK} {self.et_date} ({self.et_weekday}) {et}"
        return f"{self.ist_date} ({self.ist_weekday}) - {self.ist_time} IST | {et}"


def stamp(when: dt.datetime) -> DualStamp:
    if when.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    u = when.astimezone(UTC)
    i = u.astimezone(IST)
    e = u.astimezone(ET)
    off = e.utcoffset()
    hours, rem = divmod(int(abs(off.total_seconds())), 3600)
    sign = "-" if off.total_seconds() < 0 else "+"
    return DualStamp(
        utc=u.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ist_date=i.strftime(DATE_FMT),
        ist_time=i.strftime(TIME_FMT),
        ist_weekday=i.strftime("%a"),
        et_date=e.strftime(DATE_FMT),
        et_time=e.strftime(TIME_FMT),
        et_weekday=e.strftime("%a"),
        et_abbr=e.tzname(),
        et_offset=f"{sign}{hours:02d}:{rem // 60:02d}",
        day_shift=(e.date() - i.date()).days,
    )


@dataclass(frozen=True)
class DateStamp:
    """A stamp for something that has a DATE and no instant.

    IT HAS NO TIME ATTRIBUTE, and that absence is the whole point. A row whose
    condition is date-granular -- a combust window the ephemeris emits as a
    date, a span built from civil-day boundaries, a reference-table row anchored
    at a date this build chose -- used to be stamped by `stamp()` like everything
    else, and `stamp()` always has a time. So 662 rows rendered `00:00 IST` with
    a previous-Eastern-day afternoon beside it, and every one of them read as a
    measured moment.

    Nothing about that was fixable by discipline: there was no way to write the
    renderer that did not produce a clock time, because the object it was handed
    had one. Here there is no `ist_time`, no `et_time`, no `et_abbr` and no
    `et_offset`, so the branch that handles a row without an instant cannot emit
    one -- it raises AttributeError at build time instead.

    `day_shift` is absent for the same reason. A day shift is a statement about
    where an INSTANT falls in two calendars; a civil day at a venue does not
    shift, it simply is that venue's day.
    """

    ist_date: str
    ist_weekday: str
    #: WHY there is no instant, which is not one answer but three:
    #:
    #: * `date_only` -- the ephemeris never resolved this to a moment. A
    #:   combust or rise window, a total day;
    #: * `period_cut` -- the boundary is where the GENERATED PERIOD was cut,
    #:   not where the sky changed. `Span.open_start` / `open_end`;
    #: * `anchored` -- the date was chosen by this build because the thing the
    #:   row reports never happened inside the span at all;
    #: * `named_contacts` -- the row has SEVERAL instants and names them, so a
    #:   single unlabelled time would be choosing one of five without saying
    #:   which. Eclipses.
    #:
    #: Kept as four values rather than one flag because the remedies differ: a
    #: date_only endpoint would need a new ephemeris scan, a period_cut one a
    #: wider span, an anchored one cannot be remedied at all, and a
    #: named_contacts row is not missing anything -- it has more times than one
    #: field can hold.
    no_instant_reason: str

    def as_dict(self) -> dict:
        return asdict(self)

    def line(self) -> str:
        return f"{self.ist_date} ({self.ist_weekday})"


NO_INSTANT_REASONS = ("date_only", "period_cut", "anchored", "named_contacts")


def date_stamp(day: dt.date, reason: str) -> DateStamp:
    """Stamp a civil date with no instant. See `DateStamp`."""
    if reason not in NO_INSTANT_REASONS:
        raise ValueError(
            f"date_stamp reason {reason!r}: expected one of "
            f"{NO_INSTANT_REASONS}. A row that HAS an instant is stamped by "
            "stamp(), and a reason nobody chose is not a default")
    return DateStamp(ist_date=day.strftime(DATE_FMT),
                     ist_weekday=day.strftime("%a"),
                     no_instant_reason=reason)


def window_line(start: dt.datetime, end: dt.datetime) -> str:
    """Render a two-ended window. Each end is converted independently, so a
    window spanning a DST change correctly shows different Eastern offsets."""
    return f"{stamp(start).line()}  ->  {stamp(end).line()}"


def civil_day_bounds(day: dt.date, tz: ZoneInfo) -> tuple[dt.datetime, dt.datetime]:
    """Midnight-to-midnight in the given zone, returned as UTC instants."""
    start = dt.datetime(day.year, day.month, day.day, tzinfo=tz)
    end = start + dt.timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def ist_cutoff_for_previous_et_day(when: dt.datetime) -> bool:
    """True when the Eastern calendar date is one day behind the IST date."""
    return stamp(when).day_shift != 0
