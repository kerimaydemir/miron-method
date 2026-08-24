import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

import httpx

from app.domain.auto_coupon import MarketOdds
from app.domain.fixtures import CanonicalFixture, TriageFactors

logger = logging.getLogger(__name__)


class BookmakerProvider(Protocol):
    source_name: str
    supported_market_keys: tuple[str, ...]

    @property
    def observed_at(self) -> datetime | None: ...

    @property
    def available(self) -> bool: ...

    async def close(self) -> None: ...

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]: ...

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]: ...

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]: ...

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture: ...

    async def market_for(self, fixture_id: UUID) -> MarketOdds | None: ...

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds: ...

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture: ...

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors: ...


class CompositeOddsProvider:
    """Fail-soft bookmaker adapter: try providers in order, keep daily automation alive."""

    def __init__(self, providers: Sequence[BookmakerProvider]) -> None:
        self._providers = tuple(providers)
        self.source_name = "+".join(str(provider.source_name) for provider in self._providers)
        self.supported_market_keys = tuple(
            dict.fromkeys(
                market for provider in self._providers for market in provider.supported_market_keys
            )
        )

    @property
    def observed_at(self) -> datetime | None:
        return next(
            (provider.observed_at for provider in self._providers if provider.observed_at),
            None,
        )

    @property
    def available(self) -> bool:
        return any(provider.available for provider in self._providers)

    async def close(self) -> None:
        for provider in self._providers:
            await provider.close()

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]:
        last_error: BaseException | None = None
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                pairs = await provider.list_market_fixtures(start_utc=start_utc, end_utc=end_utc)
            except (httpx.HTTPError, RuntimeError, ValueError) as error:
                last_error = error
                logger.warning(
                    "Bookmaker provider failed; trying fallback",
                    extra={
                        "provider": provider.source_name,
                        "error_type": type(error).__name__,
                    },
                )
                continue
            if pairs:
                return pairs
        if last_error is not None:
            raise last_error
        return ()

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        pairs = await self.list_market_fixtures(start_utc=start_utc, end_utc=end_utc)
        return tuple(
            fixture
            for fixture, _ in pairs
            if not competition_ids or fixture.competition_key in competition_ids
        )

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        results: dict[UUID, CanonicalFixture] = {}
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                for item in await provider.search_fixtures(
                    query=query, start_utc=start_utc, end_utc=end_utc
                ):
                    results[item.id] = item
            except (httpx.HTTPError, RuntimeError, ValueError):
                continue
        return tuple(results.values())

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                return await provider.get_fixture(fixture_id)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
        raise KeyError(str(fixture_id))

    async def market_for(self, fixture_id: UUID) -> MarketOdds | None:
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                market = await provider.market_for(fixture_id)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
            if market is not None:
                return market
        return None

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds:
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                return await provider.wide_market_for(fixture_id)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
        raise KeyError(str(fixture_id))

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                return await provider.refresh_result(fixture_id)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
        raise KeyError(str(fixture_id))

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                return await provider.features_for(fixture)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
        raise KeyError(str(fixture.id))
