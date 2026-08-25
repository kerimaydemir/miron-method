from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.application.auto_coupons import scan_end_for_window


def test_one_day_auto_coupon_window_ends_at_istanbul_midnight() -> None:
    now = datetime(2026, 8, 25, 16, 15, tzinfo=UTC)

    scan_end = scan_end_for_window(
        now, window_days=1, app_timezone=ZoneInfo("Europe/Istanbul")
    )

    assert scan_end == datetime(2026, 8, 25, 21, 0, tzinfo=UTC)


def test_multi_day_auto_coupon_window_keeps_rolling_behavior() -> None:
    now = datetime(2026, 8, 25, 16, 15, tzinfo=UTC)

    scan_end = scan_end_for_window(
        now, window_days=3, app_timezone=ZoneInfo("Europe/Istanbul")
    )

    assert scan_end == now + timedelta(days=3)
