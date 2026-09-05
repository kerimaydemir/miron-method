from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

from app.api.auto_coupons import _daily_review_payloads, _ticket_settlement
from app.domain.auto_coupon import AutoCouponRun, CouponSelection


def _selection(status: str, odds: str) -> CouponSelection:
    return cast(
        CouponSelection,
        cast(
            Any,
            SimpleNamespace(
                settlement_status=status,
                market_decimal_odds=Decimal(odds),
            ),
        ),
    )


def test_ticket_with_won_and_void_leg_is_won_at_adjusted_odds() -> None:
    status, odds = _ticket_settlement(
        (_selection("won", "1.45"), _selection("void", "1.40"))
    )

    assert status == "won"
    assert odds == Decimal("1.45")


def test_ticket_is_decisively_lost_even_if_another_leg_is_pending() -> None:
    status, odds = _ticket_settlement(
        (_selection("lost", "1.45"), _selection("pending", "1.40"))
    )

    assert status == "lost"
    assert odds is None


def test_fresh_ticket_settlement_is_reported_without_daily_prediction_review() -> None:
    run_id = uuid4()
    fixture_id = uuid4()
    fixture = SimpleNamespace(id=fixture_id, home_team="Home", away_team="Away")
    selection = SimpleNamespace(
        fixture=fixture,
        market_label="Toplam gol",
        outcome_label="2.5 Alt",
        market_decimal_odds=Decimal("1.80"),
        bookmaker="Bet365",
        settlement_status="won",
        final_home_score=1,
        final_away_score=0,
    )
    ticket = SimpleNamespace(
        label="Günlük piyasa ikilisi",
        combined_decimal_odds=Decimal("1.80"),
        selection_fixture_ids=(fixture_id,),
    )
    run = cast(
        AutoCouponRun,
        cast(
            Any,
            SimpleNamespace(
                run_id=run_id,
                post_match_review=None,
                daily_predictions=(),
                selections=(selection,),
                tickets=(ticket,),
            ),
        ),
    )

    daily_reviews, ticket_reviews = _daily_review_payloads(
        (run,), newly_reviewed=set(), newly_settled={(run_id, fixture_id)}
    )

    assert daily_reviews == []
    assert ticket_reviews[0]["status"] == "won"
    legs = ticket_reviews[0]["legs"]
    assert isinstance(legs, list)
    assert legs[0]["bookmaker"] == "Bet365"
