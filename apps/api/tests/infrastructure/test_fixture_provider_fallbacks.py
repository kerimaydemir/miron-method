import asyncio
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


class _BrokenOddsProvider(MockFixtureProvider):
    source_name = "api_football_odds"

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        raise RuntimeError("odds unavailable")

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        raise RuntimeError("odds unavailable")

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        raise RuntimeError("odds unavailable")

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        raise RuntimeError("odds unavailable")


class _SlowOddsProvider(_BrokenOddsProvider):
    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        await asyncio.sleep(1)
        return ()


@pytest.mark.asyncio
async def test_analysis_fixture_provider_refreshes_odds_cache_before_base_fallback() -> None:
    odds = _CacheMissThenRefreshOddsProvider()
    provider = CompositeAnalysisFixtureProvider(MockFixtureProvider(), odds)

    fixture = await provider.get_fixture(FIXTURES[2].id)

    assert fixture.id == FIXTURES[2].id
    assert fixture.source_provider == "odds_api_io"
    assert odds.refreshed is True


@pytest.mark.asyncio
async def test_analysis_fixture_provider_falls_back_when_odds_provider_is_unavailable() -> None:
    provider = CompositeAnalysisFixtureProvider(MockFixtureProvider(), _BrokenOddsProvider())

    fixture = await provider.get_fixture(FIXTURES[2].id)
    factors = await provider.features_for(fixture)
    refreshed = await provider.refresh_result(FIXTURES[2].id)

    assert fixture.id == FIXTURES[2].id
    assert factors == FEATURES[2]
    assert refreshed.id == FIXTURES[2].id


@pytest.mark.asyncio
async def test_analysis_fixture_provider_does_not_block_on_slow_odds_list() -> None:
    provider = CompositeAnalysisFixtureProvider(
        MockFixtureProvider(), _SlowOddsProvider(), odds_timeout_seconds=0.01
    )

    fixtures = await provider.list_fixtures(
        start_utc=FIXTURES[2].kickoff_at,
        end_utc=FIXTURES[2].kickoff_at.replace(hour=23),
        competition_ids=(),
    )

    assert FIXTURES[2].id in {fixture.id for fixture in fixtures}


@pytest.mark.asyncio
async def test_fallback_fixture_provider_uses_fallback_when_primary_lookup_fails() -> None:
    provider = FallbackFixtureProvider(_BrokenPrimaryFixtureProvider(), MockFixtureProvider())

    fixture = await provider.get_fixture(FIXTURES[2].id)
    factors = await provider.features_for(
        FIXTURES[2].model_copy(update={"source_provider": "rapidapi_football"})
    )

    assert fixture.id == FIXTURES[2].id
    assert factors == FEATURES[2]
