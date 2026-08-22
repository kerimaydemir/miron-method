from decimal import Decimal

from app.infrastructure.auto_coupon_repository import _performance_from_records


def test_performance_reports_calibration_roi_and_process_cohorts() -> None:
    performance = _performance_from_records(
        [
            {
                "market_key": "totals",
                "settlement_status": "won",
                "probability": Decimal(".60"),
                "market_decimal_odds": Decimal("1.90"),
                "process_verdict": "sound_win",
            },
            {
                "market_key": "totals",
                "settlement_status": "lost",
                "probability": Decimal(".70"),
                "market_decimal_odds": Decimal("1.80"),
                "process_verdict": "sound_but_unlucky_loss",
            },
        ]
    )

    assert performance.hit_rate == Decimal(".5000")
    assert performance.brier_score == Decimal(".3250")
    assert performance.equal_stake_roi == Decimal("-.0500")
    assert performance.process_verdicts == {
        "sound_win": 1,
        "sound_but_unlucky_loss": 1,
    }
    assert performance.sample_size_status == "early"
