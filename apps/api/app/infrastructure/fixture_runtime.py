from typing import cast

from app.domain.ports import LiveFixtureProvider
from app.infrastructure.api_football_odds_provider import ApiFootballOddsProvider
from app.infrastructure.composite_fixture_provider import (
    CompositeAnalysisFixtureProvider,
    OddsFixtureProvider,
)
from app.infrastructure.composite_odds_provider import BookmakerProvider, CompositeOddsProvider
from app.infrastructure.fallback_fixture_provider import FallbackFixtureProvider
from app.infrastructure.football_data_org_provider import FootballDataOrgProvider
from app.infrastructure.mock_fixture_provider import MockFixtureProvider
from app.infrastructure.odds_api_io_provider import OddsApiIoProvider
from app.infrastructure.openligadb_provider import OpenLigaDbProvider
from app.infrastructure.rapidapi_football_provider import RapidApiFootballProvider
from app.infrastructure.the_odds_api_provider import TheOddsApiProvider
from app.settings import get_settings

settings = get_settings()

openligadb_provider: OpenLigaDbProvider | None = None
football_data_provider: FootballDataOrgProvider | None = None
rapidapi_provider: RapidApiFootballProvider | None = None

if settings.LIVE_FIXTURES_ENABLED:
    openligadb_provider = OpenLigaDbProvider(
        base_url=settings.OPENLIGADB_BASE_URL,
        league_shortcuts=settings.openligadb_leagues,
        refresh_seconds=settings.OPENLIGADB_REFRESH_SECONDS,
    )
    fixture_provider: LiveFixtureProvider = openligadb_provider
    if settings.rapidapi_enabled:
        rapidapi_provider = RapidApiFootballProvider(
            api_key=settings.RAPIDAPI_KEY.get_secret_value(),
            host=settings.RAPIDAPI_HOST,
            timezone=settings.APP_TIMEZONE,
            refresh_seconds=settings.RAPIDAPI_REFRESH_SECONDS,
            deep_request_limit=settings.RAPIDAPI_DEEP_REQUEST_LIMIT,
        )
        fixture_provider = FallbackFixtureProvider(
            primary=rapidapi_provider,
            fallback=fixture_provider,
        )
    if settings.football_data_enabled:
        football_data_provider = FootballDataOrgProvider(
            api_key=settings.FOOTBALL_DATA_API_KEY.get_secret_value(),
            base_url=settings.FOOTBALL_DATA_BASE_URL,
            refresh_seconds=settings.FOOTBALL_DATA_REFRESH_SECONDS,
        )
        fixture_provider = FallbackFixtureProvider(
            primary=football_data_provider,
            fallback=fixture_provider,
        )
else:
    fixture_provider = MockFixtureProvider()

wide_markets = tuple(
    item.strip() for item in settings.THE_ODDS_WIDE_MARKETS.split(",") if item.strip()
)

configured_odds_providers: list[BookmakerProvider] = []
if settings.odds_api_io_enabled:
    configured_odds_providers.append(
        OddsApiIoProvider(
            api_key=settings.ODDS_API_IO_KEY.get_secret_value(),
            base_url=settings.ODDS_API_IO_BASE_URL,
            refresh_seconds=settings.ODDS_REFRESH_SECONDS,
            bookmakers=settings.ODDS_API_IO_BOOKMAKERS,
            events_per_league=settings.ODDS_API_IO_EVENTS_PER_LEAGUE,
        )
    )
if settings.odds_enabled:
    the_odds_provider = TheOddsApiProvider(
        api_key=settings.THE_ODDS_API_KEY.get_secret_value(),
        base_url=settings.THE_ODDS_API_BASE_URL,
        refresh_seconds=settings.ODDS_REFRESH_SECONDS,
        wide_markets=wide_markets,
    )
    configured_odds_providers.append(the_odds_provider)
if settings.api_football_current_odds_enabled or (
    settings.api_football_enabled and configured_odds_providers
):
    configured_odds_providers.append(
        ApiFootballOddsProvider(
            api_key=settings.API_FOOTBALL_API_KEY.get_secret_value(),
            base_url=settings.API_FOOTBALL_BASE_URL,
            refresh_seconds=settings.ODDS_REFRESH_SECONDS,
            requests_per_minute=settings.API_FOOTBALL_REQUESTS_PER_MINUTE,
        )
    )

odds_provider: BookmakerProvider
if len(configured_odds_providers) > 1:
    odds_provider = CompositeOddsProvider(tuple(configured_odds_providers))
elif len(configured_odds_providers) == 1:
    odds_provider = configured_odds_providers[0]
else:
    odds_provider = TheOddsApiProvider(
        api_key="",
        base_url=settings.THE_ODDS_API_BASE_URL,
        refresh_seconds=settings.ODDS_REFRESH_SECONDS,
        wide_markets=wide_markets,
    )
analysis_fixture_provider = CompositeAnalysisFixtureProvider(
    fixture_provider, cast(OddsFixtureProvider, odds_provider)
)


async def start_fixture_runtime() -> None:
    if openligadb_provider is not None:
        await openligadb_provider.start()
    if football_data_provider is not None:
        await football_data_provider.start()


async def stop_fixture_runtime() -> None:
    if football_data_provider is not None:
        await football_data_provider.stop()
    if openligadb_provider is not None:
        await openligadb_provider.stop()
    if rapidapi_provider is not None:
        await rapidapi_provider.close()
    await odds_provider.close()
