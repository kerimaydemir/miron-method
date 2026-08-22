from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.application.auto_coupons import AutoCouponService
from app.domain.auto_coupon import (
    TOP_LEAGUES,
    AutoCandidate,
    CouponSelection,
    LeaguePolicy,
    league_for_fixture,
)
from app.domain.fixtures import CanonicalFixture


def fixture(shortcut: str, name: str = "Allowed League") -> CanonicalFixture:
    return CanonicalFixture(
        id=uuid4(),
        competition_key=f"openligadb:{shortcut}:2026",
        competition_name=name,
        home_team="Home Club",
        away_team="Away Club",
        kickoff_at=datetime(2026, 8, 24, 18, 0, tzinfo=UTC),
        source_provider="openligadb",
    )


def test_top_league_allowlist_excludes_mexico_and_colombia() -> None:
    assert len(TOP_LEAGUES) == 8
    assert len({item.key for item in TOP_LEAGUES}) == 8
    assert league_for_fixture(fixture("la1")) is not None
    assert league_for_fixture(fixture("mex1", "Liga MX")) is None
    assert league_for_fixture(fixture("col1", "Primera A Colombia")) is None


def test_legacy_league_payload_without_football_data_code_remains_readable() -> None:
    policy = LeaguePolicy.model_validate(
        {
            "key": "laliga",
            "name": "LaLiga",
            "country_code": "ES",
            "openligadb_shortcut": "la1",
            "odds_sport_key": "soccer_spain_la_liga",
            "prestige_weight": 10,
        }
    )
    assert policy.football_data_code is None


def test_deterministic_funnel_is_ten_to_five_to_three() -> None:
    league = TOP_LEAGUES[1]
    candidates = tuple(
        AutoCandidate(
            fixture=fixture("la1"),
            league=league,
            auto_score=90 - index,
            memory_case_count=0,
            positive_factors=("Güncel",),
            risk_flags=("Oran yok",),
        )
        for index in range(10)
    )
    rough, critic = AutoCouponService._deterministic_funnel(candidates)
    assert rough.input_count == 10
    assert len(rough.selected_fixture_ids) == 5
    assert len(critic.selected_fixture_ids) == 3


def test_ticket_math_rejects_combined_coupon_below_seventy_percent() -> None:
    league = TOP_LEAGUES[1]
    selections = tuple(
        CouponSelection(
            fixture=fixture("la1"),
            league=league,
            analysis_run_id=uuid4(),
            lock_id=uuid4(),
            pick="home",
            probability=probability,
            model_fair_odds=(Decimal("1") / probability).quantize(Decimal(".01")),
            market_decimal_odds=Decimal("1.80") + Decimal(index) / Decimal("10"),
            market_fair_probability=Decimal(".55"),
            edge=probability - Decimal(".55"),
            bookmaker_count=3,
            price_observed_at=datetime(2026, 8, 22, 8, 0, tzinfo=UTC),
            confidence=Decimal(".60"),
            reason="İzinli lig ve güncel veri desteği.",
            uncertainty="Kadro bilgisi henüz doğrulanmadı.",
        )
        for index, probability in enumerate((Decimal(".70"), Decimal(".60"), Decimal(".50")))
    )
    tickets = AutoCouponService._tickets(selections)
    assert [item.kind for item in tickets] == ["single"]
    assert tickets[0].combined_probability == Decimal(".700000")
    assert tickets[0].combined_decimal_odds == Decimal("1.80")
    assert all(item.odds_source == "bookmaker_average" for item in tickets)


def test_ticket_math_fails_closed_without_bookmaker_odds() -> None:
    league = TOP_LEAGUES[1]
    selection = CouponSelection(
        fixture=fixture("la1"),
        league=league,
        analysis_run_id=uuid4(),
        lock_id=uuid4(),
        pick="h2h:match:home:none",
        probability=Decimal(".70"),
        model_fair_odds=Decimal("1.43"),
        confidence=Decimal(".60"),
        reason="İzinli lig ve güncel veri desteği.",
        uncertainty="Kadro bilgisi henüz doğrulanmadı.",
    )
    assert AutoCouponService._tickets((selection,)) == ()


def test_multi_market_settlement_handles_totals_btts_and_draw_no_bet() -> None:
    finished = fixture("la1").model_copy(
        update={"home_score": 2, "away_score": 1, "status": "finished"}
    )
    assert AutoCouponService._settlement_status("totals:match:over:2.5", finished, "home") == "won"
    assert AutoCouponService._settlement_status("btts:match:yes:none", finished, "home") == "won"
    assert (
        AutoCouponService._settlement_status("draw_no_bet:match:home:none", finished, "home")
        == "won"
    )
    assert (
        AutoCouponService._settlement_status("team_totals:Home Club:over:1.5", finished, "home")
        == "won"
    )
