from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.domain.ports import LiveFixtureProvider
from app.infrastructure.fallback_fixture_provider import FallbackFixtureProvider
from app.infrastructure.openligadb_provider import OpenLigaDbProvider


class OddsFixtureProvider(LiveFixtureProvider, Protocol):
    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture: ...


class CompositeAnalysisFixtureProvider:
    source_name = "composite"

    def __init__(self, base: LiveFixtureProvider, odds: OddsFixtureProvider) -> None:
        self._base = base
        self._odds = odds

    @property
    def observed_at(self) -> datetime | None:
        return self._odds.observed_at or self._base.observed_at

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        base = await self._base.list_fixtures(
            start_utc=start_utc,
            end_utc=end_utc,
            competition_ids=competition_ids,
        )
        odds = await self._odds.list_fixtures(
            start_utc=start_utc,
            end_utc=end_utc,
            competition_ids=competition_ids,
        )
        return tuple(
            sorted(
                {item.id: item for item in (*odds, *base)}.values(),
                key=lambda item: item.kickoff_at,
            )
        )

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        base = await self._base.search_fixtures(query=query, start_utc=start_utc, end_utc=end_utc)
        odds = await self._odds.search_fixtures(query=query, start_utc=start_utc, end_utc=end_utc)
        return tuple({item.id: item for item in (*odds, *base)}.values())

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            return await self._odds.get_fixture(fixture_id)
        except KeyError:
            now = datetime.now(UTC)
            await self._odds.list_fixtures(
                start_utc=now - timedelta(hours=12),
                end_utc=now + timedelta(days=3),
                competition_ids=(),
            )
        try:
            return await self._odds.get_fixture(fixture_id)
        except KeyError:
            return await self._base.get_fixture(fixture_id)

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        try:
            return await self._odds.features_for(fixture)
        except KeyError:
            pass
        return await self._base.features_for(fixture)

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            return await self._odds.refresh_result(fixture_id)
        except KeyError:
            if isinstance(self._base, FallbackFixtureProvider):
                return await self._base.refresh_result(fixture_id)
            if isinstance(self._base, OpenLigaDbProvider):
                await self._base.refresh(force=True)
            return await self._base.get_fixture(fixture_id)
