from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.application.auto_coupons import AutoCouponService
from app.domain.auto_coupon import (
    TOP_LEAGUES,
    AutoCandidate,
    CouponSelection,
    FunnelDecision,
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


def market_for_quote(
    quote: MarketQuote,
    *,
    home: str = "1.60",
    draw: str = "3.60",
    away: str = "5.00",
) -> MarketOdds:
    raw_home = Decimal(home)
    raw_draw = Decimal(draw)
    raw_away = Decimal(away)
    implied = Decimal("1") / raw_home + Decimal("1") / raw_draw + Decimal("1") / raw_away
    return MarketOdds(
        observed_at=quote.observed_at,
        bookmaker_count=quote.bookmaker_count,
        home_decimal=raw_home,
        draw_decimal=raw_draw,
        away_decimal=raw_away,
        fair_home_probability=((Decimal("1") / raw_home) / implied).quantize(Decimal(".000001")),
        fair_draw_probability=((Decimal("1") / raw_draw) / implied).quantize(Decimal(".000001")),
        fair_away_probability=(
            Decimal("1")
            - ((Decimal("1") / raw_home) / implied).quantize(Decimal(".000001"))
            - ((Decimal("1") / raw_draw) / implied).quantize(Decimal(".000001"))
        ),
        quotes=(quote,),
    )


def test_top_league_allowlist_excludes_mexico_and_colombia() -> None:
    assert len(TOP_LEAGUES) == 8
    assert len({item.key for item in TOP_LEAGUES}) == 8
    assert league_for_fixture(fixture("la1")) is not None
    assert league_for_fixture(fixture("mex1", "Liga MX")) is None
    assert league_for_fixture(fixture("col1", "Primera A Colombia")) is None


def test_free_mode_readiness_does_not_require_paid_gemini() -> None:
    class _ReadyOdds:
        available = True
        supported_market_keys = ("h2h", "totals")

    class _FreeModeAnalysis:
        deep_data_ready = True
        deep_analysis_ready = False
        implemented_stage_ids = ()
        required_deep_stage_ids = ("S00",)

    service = AutoCouponService.__new__(AutoCouponService)
    service._odds = _ReadyOdds()
    service._analysis = _FreeModeAnalysis()
    service._funnel = None
    service._live_fixtures_available = True

    readiness = service.readiness()

    assert readiness.ready is True
    assert readiness.gemini_analysis is False
    assert readiness.blockers == ()
    assert "ücretsiz maliyet korumalı mod" in readiness.notice


def test_selection_label_uses_turkish_coupon_style_for_h2h() -> None:
    quote = MarketQuote(
        provider="espn_core_odds",
        observed_at=datetime(2026, 8, 24, 9, 0, tzinfo=UTC),
        market_key="h2h",
        market_label="Maç sonucu",
        outcome_key="home",
        outcome_label="Barcelona",
        description="Barcelona",
        decimal_odds=Decimal("1.22"),
        fair_probability=Decimal(".78"),
        bookmaker_count=1,
    )

    assert AutoCouponService._selection_label(quote) == "MS 1 (Barcelona)"


def test_selection_label_uses_turkish_coupon_style_for_common_markets() -> None:
    observed_at = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)
    total_quote = MarketQuote(
        provider="odds_api_io",
        observed_at=observed_at,
        market_key="totals",
        market_label="Toplam gol",
        outcome_key="over",
        outcome_label="Üst",
        decimal_odds=Decimal("1.52"),
        fair_probability=Decimal(".62"),
        bookmaker_count=1,
        point=Decimal("1.75"),
    )
    btts_quote = total_quote.model_copy(
        update={
            "market_key": "btts",
            "market_label": "Karşılıklı gol",
            "outcome_key": "yes",
            "outcome_label": "Var",
            "point": None,
        }
    )
    double_chance_quote = total_quote.model_copy(
        update={
            "market_key": "double_chance",
            "market_label": "Çifte şans",
            "outcome_key": "1x",
            "outcome_label": "1X",
            "point": None,
        }
    )

    assert AutoCouponService._selection_label(total_quote) == "1.75 Üst"
    assert AutoCouponService._selection_label(btts_quote) == "KG Var"
    assert AutoCouponService._selection_label(double_chance_quote) == "Çifte Şans 1X"


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


def test_empty_gemini_funnel_falls_back_to_top_three_for_live_odds_day() -> None:
    league = TOP_LEAGUES[1]
    candidates = tuple(
        AutoCandidate(
            fixture=fixture("la1"),
            league=league,
            auto_score=90 - index,
            memory_case_count=0,
            positive_factors=("Güncel", "Canlı oran var"),
            risk_flags=(),
        )
        for index in range(5)
    )
    rough = FunnelDecision(
        stage="rough",
        input_count=5,
        selected_fixture_ids=(),
        eliminated_fixture_ids=tuple(item.fixture.id for item in candidates),
        rationale="Kaba elemede kanıt ve fiyat eşiğini geçen maç bulunmadı.",
        model_id="gemini-test",
    )
    critic = FunnelDecision(
        stage="critic",
        input_count=0,
        selected_fixture_ids=(),
        eliminated_fixture_ids=(),
        rationale="Kaba eleme boş kaldı.",
        model_id="gemini-test",
    )

    fallback_rough, fallback_critic = AutoCouponService._deterministic_funnel_after_empty_gemini(
        candidates, rough, critic
    )

    assert fallback_rough.selected_fixture_ids == tuple(item.fixture.id for item in candidates[:3])
    assert fallback_critic.selected_fixture_ids == fallback_rough.selected_fixture_ids
    assert fallback_critic.input_count == 3
    assert "canlı odds olan günlerde sistem aday varken sessiz kalmaz" in fallback_critic.rationale


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


def test_ticket_math_accepts_two_safe_legs_when_combined_price_reaches_gate() -> None:
    league = TOP_LEAGUES[1]
    selections = tuple(
        CouponSelection(
            fixture=fixture(f"la{index}"),
            league=league,
            analysis_run_id=uuid4(),
            lock_id=uuid4(),
            pick="home",
            probability=Decimal(".84"),
            model_fair_odds=Decimal("1.19"),
            market_decimal_odds=odds,
            market_fair_probability=Decimal(".74"),
            edge=Decimal(".10"),
            bookmaker_count=3,
            price_observed_at=datetime(2026, 8, 22, 8, 0, tzinfo=UTC),
            confidence=Decimal(".70"),
            reason="Yüksek olasılıklı düşük oran kombine ayağı.",
            uncertainty="Kadro bilgisi henüz doğrulanmadı.",
        )
        for index, odds in enumerate((Decimal("1.35"), Decimal("1.34")), start=1)
    )

    tickets = AutoCouponService._tickets(selections)

    assert [item.kind for item in tickets] == ["double"]
    assert tickets[0].combined_probability == Decimal(".705600")
    assert tickets[0].combined_decimal_odds == Decimal("1.81")


def test_forced_daily_coupon_combines_two_banko_legs_when_strict_gate_is_empty() -> None:
    now = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)
    league = TOP_LEAGUES[1]
    first_fixture = fixture("la1")
    second_fixture = fixture("la1").model_copy(
        update={"home_team": "Second Home", "away_team": "Second Away"}
    )
    candidates = (
        AutoCandidate(
            fixture=first_fixture,
            league=league,
            auto_score=85,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
        AutoCandidate(
            fixture=second_fixture,
            league=league,
            auto_score=85,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
    )
    first_quote = MarketQuote(
        provider="espn_core_odds",
        observed_at=now,
        market_key="spread",
        market_label="Handikap",
        outcome_key="home",
        outcome_label="Ev sahibi",
        description="Home Club",
        point=Decimal("0.5"),
        decimal_odds=Decimal("1.48"),
        fair_probability=Decimal(".62"),
        bookmaker_count=1,
    )
    second_quote = MarketQuote(
        provider="espn_core_odds",
        observed_at=now,
        market_key="h2h",
        market_label="Maç sonucu",
        outcome_key="home",
        outcome_label="Ev sahibi",
        description="Home Club",
        decimal_odds=Decimal("1.33"),
        fair_probability=Decimal(".72"),
        bookmaker_count=1,
    )
    service = AutoCouponService.__new__(AutoCouponService)
    service._forced_min_combined_odds = Decimal("1.80")
    service._forced_max_combined_odds = Decimal("2.20")

    selections, tickets = service._forced_daily_coupon(
        uuid4(),
        candidates,
        {
            first_fixture.id: market_for_quote(first_quote),
            second_fixture.id: market_for_quote(second_quote),
        },
        now,
    )

    assert len(selections) == 2
    assert [item.kind for item in tickets] == ["double"]
    assert tickets[0].label == "Zorunlu günlük banko ikilisi"
    assert tickets[0].combined_decimal_odds == Decimal("1.97")
    assert tickets[0].combined_probability < Decimal(".70")
    assert "Forced mod %70 garanti iddiası değildir" in selections[0].uncertainty


def test_forced_daily_coupon_rejects_duplicate_match_from_different_providers() -> None:
    now = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)
    league = TOP_LEAGUES[1]
    first_fixture = fixture("la1").model_copy(
        update={"home_team": "Valencia CF", "away_team": "Real Betis Seville"}
    )
    duplicate_fixture = fixture("la1").model_copy(
        update={"home_team": "Valencia", "away_team": "Real Betis"}
    )
    candidates = (
        AutoCandidate(
            fixture=first_fixture,
            league=league,
            auto_score=85,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
        AutoCandidate(
            fixture=duplicate_fixture,
            league=league,
            auto_score=83,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
    )
    first_quote = MarketQuote(
        provider="api_football",
        observed_at=now,
        market_key="spread",
        market_label="Handikap",
        outcome_key="home",
        outcome_label="Ev sahibi",
        description="Valencia",
        point=Decimal("1"),
        decimal_odds=Decimal("1.23"),
        fair_probability=Decimal(".77"),
        bookmaker_count=1,
    )
    duplicate_quote = MarketQuote(
        provider="espn_core_odds",
        observed_at=now,
        market_key="spread",
        market_label="Handikap",
        outcome_key="home",
        outcome_label="Ev sahibi",
        description="Valencia",
        point=Decimal("0.5"),
        decimal_odds=Decimal("1.48"),
        fair_probability=Decimal(".62"),
        bookmaker_count=1,
    )
    service = AutoCouponService.__new__(AutoCouponService)
    service._forced_min_combined_odds = Decimal("1.80")
    service._forced_max_combined_odds = Decimal("2.20")

    selections, tickets = service._forced_daily_coupon(
        uuid4(),
        candidates,
        {
            first_fixture.id: market_for_quote(first_quote),
            duplicate_fixture.id: market_for_quote(duplicate_quote),
        },
        now,
    )

    assert selections == ()
    assert tickets == ()


def test_candidate_deduplication_collapses_provider_name_variants() -> None:
    league = TOP_LEAGUES[1]
    first_fixture = fixture("la1").model_copy(
        update={"home_team": "Valencia CF", "away_team": "Real Betis Seville"}
    )
    duplicate_fixture = fixture("la1").model_copy(
        update={"home_team": "Valencia", "away_team": "Real Betis"}
    )
    other_fixture = fixture("la1").model_copy(
        update={"home_team": "Celta Vigo", "away_team": "Osasuna"}
    )
    candidates = (
        AutoCandidate(
            fixture=first_fixture,
            league=league,
            auto_score=85,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
        AutoCandidate(
            fixture=duplicate_fixture,
            league=league,
            auto_score=83,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
        AutoCandidate(
            fixture=other_fixture,
            league=league,
            auto_score=80,
            memory_case_count=0,
            positive_factors=("LaLiga",),
            risk_flags=(),
        ),
    )

    unique = AutoCouponService._dedupe_candidates_by_match(candidates)

    assert [item.fixture.home_team for item in unique] == ["Valencia CF", "Celta Vigo"]


def test_match_key_collapses_real_sociedad_san_sebastian_suffix() -> None:
    first_fixture = fixture("la1").model_copy(
        update={"home_team": "Real Madrid", "away_team": "Real Sociedad San Sebastian"}
    )
    duplicate_fixture = fixture("la1").model_copy(
        update={"home_team": "Real Madrid", "away_team": "Real Sociedad"}
    )

    assert AutoCouponService._fixture_match_key(first_fixture) == (
        AutoCouponService._fixture_match_key(duplicate_fixture)
    )


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
