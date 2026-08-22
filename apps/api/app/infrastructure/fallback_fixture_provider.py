import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.domain.ports import LiveFixtureProvider

logger = logging.getLogger(__name__)


class FallbackFixtureProvider:
    source_name = "football_data_org_with_openligadb_fallback"

    def __init__(
        self,
        primary: LiveFixtureProvider,
        fallback: LiveFixtureProvider,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._observed_at: datetime | None = None

    @property
    def observed_at(self) -> datetime | None:
        return self._observed_at or self._primary.observed_at or self._fallback.observed_at

    @observed_at.setter
    def observed_at(self, value: datetime | None) -> None:
        self._observed_at = value

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        try:
            primary = await self._primary.list_fixtures(
                start_utc=start_utc,
                end_utc=end_utc,
                competition_ids=competition_ids,
            )
            if primary:
                return primary
        except Exception as error:
            logger.warning(
                "Primary fixture provider failed; using fallback",
                extra={"error_type": type(error).__name__},
            )
        return await self._fallback.list_fixtures(
            start_utc=start_utc,
            end_utc=end_utc,
            competition_ids=competition_ids,
        )

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        try:
            primary = await self._primary.search_fixtures(
                query=query,
                start_utc=start_utc,
                end_utc=end_utc,
            )
            if primary:
                return primary
        except Exception as error:
            logger.warning(
                "Primary fixture search failed; using fallback",
                extra={"error_type": type(error).__name__},
            )
        return await self._fallback.search_fixtures(
            query=query,
            start_utc=start_utc,
            end_utc=end_utc,
        )

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            return await self._primary.get_fixture(fixture_id)
        except KeyError:
            return await self._fallback.get_fixture(fixture_id)

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        if fixture.source_provider == self._primary.source_name:
            return await self._primary.features_for(fixture)
        return await self._fallback.features_for(fixture)

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            primary_refresh = getattr(self._primary, "refresh_result", None)
            if callable(primary_refresh):
                result: Any = await primary_refresh(fixture_id)
                return cast(CanonicalFixture, result)
            return await self._primary.get_fixture(fixture_id)
        except KeyError:
            refresh = getattr(self._fallback, "refresh", None)
            if callable(refresh):
                await refresh(force=True)
            return await self._fallback.get_fixture(fixture_id)
