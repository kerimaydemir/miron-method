from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

import pytest

from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.infrastructure.composite_fixture_provider import CompositeAnalysisFixtureProvider
from app.infrastructure.fallback_fixture_provider import FallbackFixtureProvider
from app.infrastructure.mock_fixture_provider import FEATURES, FIXTURES, MockFixtureProvider


class _CacheMissThenRefreshOddsProvider(MockFixtureProvider):
    source_name = "odds_api_io"

    def __init__(self) -> None:
        self.refreshed = False

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        if not self.refreshed:
            raise KeyError(str(fixture_id))
        return FIXTURES[2].model_copy(update={"source_provider": self.source_name})

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        self.refreshed = True
        return (FIXTURES[2].model_copy(update={"source_provider": self.source_name}),)


class _BrokenPrimaryFixtureProvider(MockFixtureProvider):
    source_name = "rapidapi_football"

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        raise RuntimeError("primary quota exceeded")

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        raise RuntimeError("primary quota exceeded")


@pytest.mark.asyncio
async def test_analysis_fixture_provider_refreshes_odds_cache_before_base_fallback() -> None:
    odds = _CacheMissThenRefreshOddsProvider()
    provider = CompositeAnalysisFixtureProvider(MockFixtureProvider(), odds)

    fixture = await provider.get_fixture(FIXTURES[2].id)

    assert fixture.id == FIXTURES[2].id
    assert fixture.source_provider == "odds_api_io"
    assert odds.refreshed is True


@pytest.mark.asyncio
async def test_fallback_fixture_provider_uses_fallback_when_primary_lookup_fails() -> None:
    provider = FallbackFixtureProvider(_BrokenPrimaryFixtureProvider(), MockFixtureProvider())

    fixture = await provider.get_fixture(FIXTURES[2].id)
    factors = await provider.features_for(
        FIXTURES[2].model_copy(update={"source_provider": "rapidapi_football"})
    )

    assert fixture.id == FIXTURES[2].id
    assert factors == FEATURES[2]
