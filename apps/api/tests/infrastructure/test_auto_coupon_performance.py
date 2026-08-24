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
    assert len(performance.calibration) == 5
    band_60 = next(item for item in performance.calibration if item.label == "0.60-0.70")
    assert band_60.settled == 1
    assert band_60.hit_rate == Decimal("1.0000")
    assert band_60.average_predicted_probability == Decimal(".6000")
    assert band_60.calibration_error == Decimal(".4000")
    band_70 = next(item for item in performance.calibration if item.label == "0.70-0.80")
    assert band_70.settled == 1
    assert band_70.hit_rate == Decimal("0.0000")
    assert band_70.average_predicted_probability == Decimal(".7000")
    assert band_70.calibration_error == Decimal(".7000")
    assert performance.sample_size_status == "early"
