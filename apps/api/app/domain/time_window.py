from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")


@dataclass(frozen=True, slots=True)
class ThreeDayWindow:
    start_utc: datetime
    end_exclusive_utc: datetime
    local_dates: tuple[date, date, date]


def three_day_window(now: datetime) -> ThreeDayWindow:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    local_now = now.astimezone(ISTANBUL)
    first_date = local_now.date()
    dates = tuple(first_date + timedelta(days=offset) for offset in range(3))
    start_local = datetime.combine(dates[0], time.min, tzinfo=ISTANBUL)
    end_local = datetime.combine(dates[-1] + timedelta(days=1), time.min, tzinfo=ISTANBUL)
    return ThreeDayWindow(
        start_utc=start_local.astimezone(UTC),
        end_exclusive_utc=end_local.astimezone(UTC),
        local_dates=(dates[0], dates[1], dates[2]),
    )
