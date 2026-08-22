from datetime import UTC, datetime

import pytest

from app.domain.time_window import three_day_window


def test_inv_001_uses_exactly_three_istanbul_calendar_dates() -> None:
    window = three_day_window(datetime(2026, 8, 22, 20, 30, tzinfo=UTC))

    assert [item.isoformat() for item in window.local_dates] == [
        "2026-08-22",
        "2026-08-23",
        "2026-08-24",
    ]
    assert window.start_utc == datetime(2026, 8, 21, 21, 0, tzinfo=UTC)
    assert window.end_exclusive_utc == datetime(2026, 8, 24, 21, 0, tzinfo=UTC)


def test_inv_001_rejects_naive_clock() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        three_day_window(datetime(2026, 8, 22, 12, 0))
