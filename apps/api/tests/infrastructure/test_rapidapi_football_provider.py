from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.domain.auto_coupon import league_for_fixture
from app.infrastructure.rapidapi_football_provider import RapidApiFootballProvider


@pytest.mark.anyio
async def test_rapidapi_provider_keeps_only_supported_top_league_subset() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-rapidapi-key"] == "secret"
        return httpx.Response(
            200,
            json={
                "status": "success",
                "response": {
                    "matches": [
                        {
                            "id": 5795364,
                            "leagueId": 47,
                            "home": {"id": 1, "name": "Hull"},
                            "away": {"id": 2, "name": "Man United"},
                            "status": {
                                "utcTime": "2026-08-22T11:30:00.000Z",
                                "finished": False,
                                "started": False,
                            },
                        },
                        {
                            "id": 999,
                            "leagueId": 230,
                            "home": {"id": 3, "name": "Liga MX Home"},
                            "away": {"id": 4, "name": "Liga MX Away"},
                            "status": {
                                "utcTime": "2026-08-22T12:00:00.000Z",
                                "finished": False,
                                "started": False,
                            },
                        },
                    ]
                },
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://test")
    provider = RapidApiFootballProvider(
        api_key="secret",
        host="example.rapidapi.com",
        timezone="Europe/Istanbul",
        client=client,
    )
    start = datetime(2026, 8, 22, 8, 0, tzinfo=UTC)
    fixtures = await provider.list_fixtures(
        start_utc=start,
        end_utc=start + timedelta(days=1),
        competition_ids=(),
    )

    assert len(fixtures) == 1
    assert fixtures[0].source_provider == "rapidapi_football"
    assert fixtures[0].competition_name == "Premier League"
    assert league_for_fixture(fixtures[0]) is not None
    await client.aclose()
