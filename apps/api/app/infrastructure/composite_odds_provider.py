import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime
from typing import Protocol, cast
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

    def __init__(
        self, providers: Sequence[BookmakerProvider], *, provider_timeout_seconds: float = 12.0
    ) -> None:
        self._providers = tuple(providers)
        self._provider_timeout_seconds = provider_timeout_seconds
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
        results: dict[UUID, tuple[CanonicalFixture, MarketOdds]] = {}
        providers = tuple(provider for provider in self._providers if provider.available)
        responses = await asyncio.gather(
            *(
                asyncio.wait_for(
                    provider.list_market_fixtures(start_utc=start_utc, end_utc=end_utc),
                    timeout=self._provider_timeout_seconds,
                )
                for provider in providers
            ),
            return_exceptions=True,
        )
        for provider, response in zip(providers, responses, strict=True):
            if isinstance(response, BaseException):
                last_error = response
                logger.warning(
                    "Bookmaker provider failed; trying fallback",
                    extra={
                        "provider": provider.source_name,
                        "error_type": type(response).__name__,
                    },
                )
                continue
            pairs = response
            if pairs:
                results.update({fixture.id: (fixture, market) for fixture, market in pairs})
        if results:
            return tuple(
                sorted(
                    results.values(),
                    key=lambda item: (item[0].kickoff_at, item[0].home_team, item[0].away_team),
                )
            )
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
                return await asyncio.wait_for(
                    provider.wide_market_for(fixture_id),
                    timeout=self._provider_timeout_seconds,
                )
            except (TimeoutError, KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
        raise KeyError(str(fixture_id))

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        last_fixture: CanonicalFixture | None = None
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                fixture = await provider.refresh_result(fixture_id)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
            if (
                fixture.status == "finished"
                and fixture.home_score is not None
                and fixture.away_score is not None
            ):
                return fixture
            last_fixture = fixture
        if last_fixture is not None:
            return last_fixture
        raise KeyError(str(fixture_id))

    async def refresh_fixture_result(self, fixture: CanonicalFixture) -> CanonicalFixture:
        last_fixture: CanonicalFixture | None = None
        for provider in self._providers:
            if not provider.available:
                continue
            refresh_snapshot = getattr(provider, "refresh_fixture_result", None)
            if refresh_snapshot is None:
                continue
            try:
                refresh_fixture_result = cast(
                    Callable[[CanonicalFixture], Awaitable[CanonicalFixture]],
                    refresh_snapshot,
                )
                updated = await refresh_fixture_result(fixture)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
            if (
                updated.status == "finished"
                and updated.home_score is not None
                and updated.away_score is not None
            ):
                return updated
            last_fixture = updated
        if last_fixture is not None:
            return last_fixture
        return fixture

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                return await provider.features_for(fixture)
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
        raise KeyError(str(fixture.id))
