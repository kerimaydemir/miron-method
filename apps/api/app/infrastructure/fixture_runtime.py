from typing import cast

from app.domain.ports import LiveFixtureProvider
from app.infrastructure.api_football_odds_provider import ApiFootballOddsProvider
from app.infrastructure.composite_fixture_provider import (
    CompositeAnalysisFixtureProvider,
    OddsFixtureProvider,
)
from app.infrastructure.composite_odds_provider import CompositeOddsProvider
from app.infrastructure.fallback_fixture_provider import FallbackFixtureProvider
from app.infrastructure.football_data_org_provider import FootballDataOrgProvider
from app.infrastructure.mock_fixture_provider import MockFixtureProvider
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

odds_provider: ApiFootballOddsProvider | CompositeOddsProvider | TheOddsApiProvider
if settings.odds_enabled:
    the_odds_provider = TheOddsApiProvider(
        api_key=settings.THE_ODDS_API_KEY.get_secret_value(),
        base_url=settings.THE_ODDS_API_BASE_URL,
        refresh_seconds=settings.ODDS_REFRESH_SECONDS,
        wide_markets=wide_markets,
    )
    if settings.api_football_enabled:
        odds_provider = CompositeOddsProvider(
            (
                the_odds_provider,
                ApiFootballOddsProvider(
                    api_key=settings.API_FOOTBALL_API_KEY.get_secret_value(),
                    base_url=settings.API_FOOTBALL_BASE_URL,
                    refresh_seconds=settings.ODDS_REFRESH_SECONDS,
                    requests_per_minute=settings.API_FOOTBALL_REQUESTS_PER_MINUTE,
                ),
            )
        )
    else:
        odds_provider = the_odds_provider
elif settings.api_football_current_odds_enabled:
    odds_provider = ApiFootballOddsProvider(
        api_key=settings.API_FOOTBALL_API_KEY.get_secret_value(),
        base_url=settings.API_FOOTBALL_BASE_URL,
        refresh_seconds=settings.ODDS_REFRESH_SECONDS,
        requests_per_minute=settings.API_FOOTBALL_REQUESTS_PER_MINUTE,
    )
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
