import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

import httpx

from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.domain.ports import LiveFixtureProvider
from app.infrastructure.fallback_fixture_provider import FallbackFixtureProvider
from app.infrastructure.openligadb_provider import OpenLigaDbProvider


class OddsFixtureProvider(LiveFixtureProvider, Protocol):
    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture: ...


class CompositeAnalysisFixtureProvider:
    source_name = "composite"
    _transient_provider_errors = (TimeoutError, RuntimeError, ValueError, httpx.HTTPError)

    def __init__(
        self,
        base: LiveFixtureProvider,
        odds: OddsFixtureProvider,
        *,
        odds_timeout_seconds: float = 15.0,
    ) -> None:
        self._base = base
        self._odds = odds
        self._odds_timeout_seconds = odds_timeout_seconds

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
        try:
            odds = await asyncio.wait_for(
                self._odds.list_fixtures(
                    start_utc=start_utc,
                    end_utc=end_utc,
                    competition_ids=competition_ids,
                ),
                timeout=self._odds_timeout_seconds,
            )
        except self._transient_provider_errors:
            odds = ()
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
        try:
            odds = await asyncio.wait_for(
                self._odds.search_fixtures(query=query, start_utc=start_utc, end_utc=end_utc),
                timeout=self._odds_timeout_seconds,
            )
        except self._transient_provider_errors:
            odds = ()
        return tuple({item.id: item for item in (*odds, *base)}.values())

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            return await asyncio.wait_for(
                self._odds.get_fixture(fixture_id),
                timeout=self._odds_timeout_seconds,
            )
        except KeyError:
            now = datetime.now(UTC)
            try:
                await asyncio.wait_for(
                    self._odds.list_fixtures(
                        start_utc=now - timedelta(hours=12),
                        end_utc=now + timedelta(days=3),
                        competition_ids=(),
                    ),
                    timeout=self._odds_timeout_seconds,
                )
            except self._transient_provider_errors:
                return await self._base.get_fixture(fixture_id)
        except self._transient_provider_errors:
            return await self._base.get_fixture(fixture_id)
        try:
            return await asyncio.wait_for(
                self._odds.get_fixture(fixture_id),
                timeout=self._odds_timeout_seconds,
            )
        except (KeyError, *self._transient_provider_errors):
            return await self._base.get_fixture(fixture_id)

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        try:
            return await asyncio.wait_for(
                self._odds.features_for(fixture),
                timeout=self._odds_timeout_seconds,
            )
        except (KeyError, *self._transient_provider_errors):
            pass
        return await self._base.features_for(fixture)

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            return await asyncio.wait_for(
                self._odds.refresh_result(fixture_id),
                timeout=self._odds_timeout_seconds,
            )
        except (KeyError, *self._transient_provider_errors):
            if isinstance(self._base, FallbackFixtureProvider):
                return await self._base.refresh_result(fixture_id)
            if isinstance(self._base, OpenLigaDbProvider):
                await self._base.refresh(force=True)
            return await self._base.get_fixture(fixture_id)
