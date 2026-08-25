from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.infrastructure.composite_fixture_provider import CompositeAnalysisFixtureProvider


class _MissingFeatureProvider:
    observed_at = None

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        del start_utc, end_utc, competition_ids
        return ()

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        del query, start_utc, end_utc
        return ()

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        raise KeyError(str(fixture_id))

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        raise KeyError(str(fixture.id))


class _MissingOddsProvider(_MissingFeatureProvider):
    source_name = "missing"
    supported_market_keys = ("h2h",)
    available = True

    async def close(self) -> None:
        return None

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, object], ...]:
        del start_utc, end_utc
        return ()

    async def market_for(self, fixture_id: UUID) -> None:
        del fixture_id
        return None

    async def wide_market_for(self, fixture_id: UUID) -> None:
        raise KeyError(str(fixture_id))

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        raise KeyError(str(fixture_id))


@pytest.mark.asyncio
async def test_composite_fixture_features_degrade_for_odds_only_fixture() -> None:
    fixture = CanonicalFixture(
        id=uuid4(),
        competition_key="oddsapiio:spain-laliga",
        competition_name="LaLiga",
        home_team="Valencia",
        away_team="Real Betis",
        kickoff_at=datetime(2026, 8, 26, 19, tzinfo=UTC),
        source_provider="odds_api_io",
    )
    provider = CompositeAnalysisFixtureProvider(
        _MissingFeatureProvider(),
        _MissingOddsProvider(),
        odds_timeout_seconds=0.1,
    )

    factors = await provider.features_for(fixture)

    assert factors.coverage_score > 0
    assert factors.unresolved_identity_penalty > 0
