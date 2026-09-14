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
