from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.application.auto_coupons import AutoCouponService
from app.domain.auto_coupon import (
    TOP_LEAGUES,
    AutoCandidate,
    CouponSelection,
    LeaguePolicy,
    MarketOdds,
    MarketQuote,
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
    assert (
        AutoCouponService._settlement_status("double_chance:match:1x:none", finished, "home")
        == "won"
    )
    assert (
        AutoCouponService._settlement_status("double_chance:match:x2:none", finished, "home")
        == "lost"
    )
    assert AutoCouponService._settlement_status("spread:match:home:-0.5", finished, "home") == "won"
    assert (
        AutoCouponService._settlement_status("spread:match:away:-0.5", finished, "home") == "lost"
    )
    assert (
        AutoCouponService._settlement_status("odd_even:match:odd:none", finished, "home") == "won"
    )
    assert (
        AutoCouponService._settlement_status("first_half_h2h:match:home:none", finished, "home")
        == "void"
    )


def test_daily_journal_prefers_richer_settleable_market_over_plain_h2h() -> None:
    now = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)
    league = TOP_LEAGUES[0]
    candidate = AutoCandidate(
        fixture=fixture("epl"),
        league=league,
        auto_score=88,
        memory_case_count=0,
        positive_factors=("Premier League izin listesinde",),
        risk_flags=("Kadro kapanışa kadar değişebilir",),
    )
    market = MarketOdds(
        provider="odds_api_io",
        event_id="fixture-1",
        observed_at=now,
        bookmaker_count=5,
        home_decimal=Decimal("1.80"),
        draw_decimal=Decimal("3.50"),
        away_decimal=Decimal("4.50"),
        fair_home_probability=Decimal(".55"),
        fair_draw_probability=Decimal(".25"),
        fair_away_probability=Decimal(".20"),
        quotes=(
            MarketQuote(
                provider="odds_api_io",
                observed_at=now,
                market_key="h2h",
                market_label="Maç sonucu",
                outcome_key="home",
                outcome_label="Ev sahibi",
                decimal_odds=Decimal("1.80"),
                fair_probability=Decimal(".55"),
                bookmaker_count=5,
            ),
            MarketQuote(
                provider="odds_api_io",
                observed_at=now,
                market_key="totals",
                market_label="Toplam gol",
                outcome_key="over",
                outcome_label="Üst",
                point=Decimal("2.5"),
                decimal_odds=Decimal("1.76"),
                fair_probability=Decimal(".52"),
                bookmaker_count=5,
            ),
        ),
    )

    quote = AutoCouponService._journal_quote(candidate, market, now)

    assert quote is not None
    assert quote.market_key == "totals"


def test_daily_journal_can_surface_exotic_watchlist_market_without_coupon_lock() -> None:
    now = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)
    league = TOP_LEAGUES[0]
    candidate = AutoCandidate(
        fixture=fixture("epl"),
        league=league,
        auto_score=88,
        memory_case_count=0,
        positive_factors=("Premier League izin listesinde",),
        risk_flags=("Kadro kapanışa kadar değişebilir",),
    )
    market = MarketOdds(
        provider="odds_api_io",
        event_id="fixture-1",
        observed_at=now,
        bookmaker_count=4,
        home_decimal=Decimal("1.80"),
        draw_decimal=Decimal("3.50"),
        away_decimal=Decimal("4.50"),
        fair_home_probability=Decimal(".55"),
        fair_draw_probability=Decimal(".25"),
        fair_away_probability=Decimal(".20"),
        quotes=(
            MarketQuote(
                provider="odds_api_io",
                observed_at=now,
                market_key="h2h",
                market_label="Maç sonucu",
                outcome_key="home",
                outcome_label="Ev sahibi",
                decimal_odds=Decimal("1.80"),
                fair_probability=Decimal(".55"),
                bookmaker_count=4,
            ),
            MarketQuote(
                provider="odds_api_io",
                observed_at=now,
                market_key="corners_spread",
                market_label="Korner handikap",
                outcome_key="away",
                outcome_label="Deplasman",
                point=Decimal("1.5"),
                decimal_odds=Decimal("1.92"),
                fair_probability=Decimal(".58"),
                bookmaker_count=4,
            ),
        ),
    )

    quote = AutoCouponService._journal_quote(candidate, market, now)

    assert quote is not None
    assert quote.market_key == "corners_spread"
    assert (
        AutoCouponService._settlement_status(
            "corners_spread:match:away:1.5",
            fixture("epl").model_copy(
                update={"home_score": 2, "away_score": 1, "status": "finished"}
            ),
            "home",
        )
        == "void"
    )
