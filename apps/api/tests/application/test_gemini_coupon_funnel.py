import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from app.application.gemini_coupon_funnel import GeminiCouponFunnel
from app.domain.auto_coupon import TOP_LEAGUES, AutoCandidate, MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture
from app.domain.registries import ModelRoute

NOW = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)


def test_funnel_request_uses_compact_market_snapshot_for_large_quote_sets() -> None:
    fixture = CanonicalFixture(
        id=uuid5(NAMESPACE_URL, "large-funnel-fixture"),
        competition_key="oddsapiio:england-premier-league",
        competition_name="Premier League",
        home_team="Fulham FC",
        away_team="Chelsea FC",
        kickoff_at=NOW + timedelta(hours=8),
        source_provider="odds_api_io",
        provider_fixture_id="72221172",
    )
    quotes = tuple(
        MarketQuote(
            provider="odds_api_io",
            observed_at=NOW,
            market_key="totals" if index % 2 else "spread",
            market_label="Toplam gol" if index % 2 else "Handikap",
            outcome_key="over" if index % 2 else "home",
            outcome_label="Üst" if index % 2 else "Ev sahibi",
            point=Decimal("2.5") if index % 2 else Decimal("-0.5"),
            decimal_odds=Decimal("1.80") + Decimal(index % 50) / Decimal("100"),
            fair_probability=Decimal(".45") + Decimal(index % 20) / Decimal("1000"),
            bookmaker_count=2 + index % 4,
        )
        for index in range(140)
    )
    candidate = AutoCandidate(
        fixture=fixture,
        league=TOP_LEAGUES[0],
        auto_score=91,
        market_odds=MarketOdds(
            provider="odds_api_io",
            event_id="72221172",
            observed_at=NOW,
            bookmaker_count=4,
            home_decimal=Decimal("3.80"),
            draw_decimal=Decimal("4.10"),
            away_decimal=Decimal("1.87"),
            fair_home_probability=Decimal(".25"),
            fair_draw_probability=Decimal(".24"),
            fair_away_probability=Decimal(".51"),
            quotes=quotes,
        ),
        memory_case_count=0,
        positive_factors=("Premier League izin listesinde",),
        risk_flags=("Kadro kapanışa kadar değişebilir",),
    )
    route = ModelRoute(
        provider="google_gemini",
        model_id="gemini-test",
        capabilities=frozenset({"structured_output"}),
        input_usd_per_mtok=Decimal(".10"),
        output_usd_per_mtok=Decimal(".40"),
        max_calls_per_run=1,
    )

    request = GeminiCouponFunnel._request(
        route=route,
        candidates=(candidate,),
        memory_context=tuple(f"case-{index}" for index in range(30)),
        stage="rough",
        target="test target",
        thinking_level="minimal",
    )
    packet = json.loads(request.prompt.split("\n", maxsplit=1)[1])

    assert len(request.prompt) < 200_000
    assert len(packet["candidates"][0]["market"]["quotes"]) == 24
    assert len(packet["validated_case_memory"]) == 12
