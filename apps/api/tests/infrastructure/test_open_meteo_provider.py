from datetime import UTC, datetime

import httpx
import pytest

from app.infrastructure.open_meteo_provider import OpenMeteoProvider


@pytest.mark.asyncio
async def test_collects_no_key_weather_evidence_for_fixture_city() -> None:
    def geocoding_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Istanbul",
                        "country": "Türkiye",
                        "latitude": 41.01,
                        "longitude": 28.97,
                        "timezone": "Europe/Istanbul",
                    }
                ]
            },
        )

    def forecast_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["start_date"] == "2026-08-22"
        return httpx.Response(
            200,
            json={
                "hourly_units": {"temperature_2m": "°C"},
                "hourly": {
                    "time": ["2026-08-22T17:00"],
                    "temperature_2m": [24.1],
                    "precipitation_probability": [10],
                    "wind_speed_10m": [8.0],
                    "weather_code": [1],
                },
            },
        )

    geocoding_client = httpx.AsyncClient(
        base_url="https://geocoding.test",
        transport=httpx.MockTransport(geocoding_handler),
    )
    forecast_client = httpx.AsyncClient(
        base_url="https://forecast.test",
        transport=httpx.MockTransport(forecast_handler),
    )
    provider = OpenMeteoProvider(
        geocoding_client=geocoding_client,
        forecast_client=forecast_client,
    )

    artifact = await provider.collect("Istanbul", datetime(2026, 8, 22, 17, tzinfo=UTC))

    assert artifact.kind == "weather"
    assert artifact.records[0]["resolved_location"]["name"] == "Istanbul"
    assert artifact.records[0]["hourly"]["temperature_2m"] == [24.1]
    await geocoding_client.aclose()
    await forecast_client.aclose()
