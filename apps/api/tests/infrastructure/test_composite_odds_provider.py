from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.domain.auto_coupon import MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.infrastructure.composite_odds_provider import CompositeOddsProvider


def _fixture(name: str, kickoff: datetime) -> CanonicalFixture:
    return CanonicalFixture(
        id=uuid4(),
        competition_key="espn-core:laliga:test",
        competition_name="LaLiga",
        home_team=f"{name} Home",
        away_team=f"{name} Away",
        kickoff_at=kickoff,
        source_provider="espn_core_odds",
    )


def _market() -> MarketOdds:
    observed_at = datetime(2026, 8, 26, 9, tzinfo=UTC)
    quote = MarketQuote(
        provider="espn_core_odds",
        observed_at=observed_at,
        market_key="h2h",
        market_label="Maç sonucu",
        outcome_key="home",
        outcome_label="Home",
        decimal_odds=Decimal("1.90"),
        fair_probability=Decimal(".50"),
        bookmaker_count=1,
    )
    return MarketOdds(
        provider="espn_core_odds",
        observed_at=observed_at,
        bookmaker_count=1,
        home_decimal=Decimal("1.90"),
        draw_decimal=Decimal("3.40"),
        away_decimal=Decimal("4.40"),
        fair_home_probability=Decimal(".502351"),
        fair_draw_probability=Decimal(".280725"),
        fair_away_probability=Decimal(".216924"),
        quotes=(quote,),
    )


class _Provider:
    source_name = "fake"
    supported_market_keys = ("h2h",)
    observed_at = datetime(2026, 8, 26, 9, tzinfo=UTC)
    available = True

    def __init__(self, fixture: CanonicalFixture) -> None:
        self._fixture = fixture

    async def close(self) -> None:
        return None

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]:
        del start_utc, end_utc
        return ((self._fixture, _market()),)

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: tuple[str, ...],
    ) -> tuple[CanonicalFixture, ...]:
        del start_utc, end_utc, competition_ids
        return (self._fixture,)

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        del query, start_utc, end_utc
        return (self._fixture,)

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        if fixture_id != self._fixture.id:
            raise KeyError(str(fixture_id))
        return self._fixture

    async def market_for(self, fixture_id: UUID) -> MarketOdds | None:
        if fixture_id != self._fixture.id:
            return None
        return _market()

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds:
        if fixture_id != self._fixture.id:
            raise KeyError(str(fixture_id))
        return _market()

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        return await self.get_fixture(fixture_id)

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        del fixture
        return TriageFactors(
            coverage_score=Decimal(".9"),
            source_freshness_score=Decimal(".9"),
            competitive_relevance_score=Decimal(".9"),
            model_information_gain_score=Decimal(".9"),
            market_coverage_score=Decimal(".9"),
            lineup_uncertainty_resolvability=Decimal(".5"),
            user_interest_score=Decimal(".9"),
            historical_case_support=Decimal(".5"),
            kickoff_time_practicality=Decimal(".9"),
            estimated_cost_penalty=Decimal(".05"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0"),
        )


class _ResultProvider(_Provider):
    def __init__(self, fixture: CanonicalFixture, result: CanonicalFixture) -> None:
        super().__init__(fixture)
        self._result = result

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        if fixture_id != self._fixture.id:
            raise KeyError(str(fixture_id))
        return self._result


@pytest.mark.asyncio
async def test_composite_odds_merges_all_available_provider_fixtures() -> None:
    now = datetime(2026, 8, 26, 9, tzinfo=UTC)
    early = _fixture("Early", now + timedelta(hours=2))
    late = _fixture("Late", now + timedelta(hours=4))
    provider = CompositeOddsProvider((_Provider(late), _Provider(early)))

    pairs = await provider.list_market_fixtures(start_utc=now, end_utc=now + timedelta(days=1))

    assert [fixture.home_team for fixture, _ in pairs] == ["Early Home", "Late Home"]


@pytest.mark.asyncio
async def test_composite_odds_refresh_result_skips_finished_result_without_score() -> None:
    now = datetime(2026, 8, 26, 9, tzinfo=UTC)
    fixture = _fixture("Valencia", now - timedelta(hours=2))
    finished_without_score = fixture.model_copy(update={"status": "finished"})
    finished_with_score = fixture.model_copy(
        update={"status": "finished", "home_score": 0, "away_score": 1}
    )
    provider = CompositeOddsProvider(
        (
            _ResultProvider(fixture, finished_without_score),
            _ResultProvider(fixture, finished_with_score),
        )
    )

    refreshed = await provider.refresh_result(fixture.id)

    assert refreshed.home_score == 0
    assert refreshed.away_score == 1
