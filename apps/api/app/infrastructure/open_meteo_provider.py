from datetime import datetime
from typing import Any

import httpx

from app.domain.deep_evidence import EvidenceArtifact

OpenMeteoParam = str | int | float | bool | None


class OpenMeteoProvider:
    source_name = "open_meteo"

    def __init__(
        self,
        *,
        forecast_base_url: str = "https://api.open-meteo.com/v1",
        geocoding_base_url: str = "https://geocoding-api.open-meteo.com/v1",
        forecast_client: httpx.AsyncClient | None = None,
        geocoding_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._forecast = forecast_client or httpx.AsyncClient(
            base_url=forecast_base_url.rstrip("/"), timeout=15.0
        )
        self._geocoding = geocoding_client or httpx.AsyncClient(
            base_url=geocoding_base_url.rstrip("/"), timeout=15.0
        )
        self._owns_forecast = forecast_client is None
        self._owns_geocoding = geocoding_client is None

    async def close(self) -> None:
        if self._owns_forecast:
            await self._forecast.aclose()
        if self._owns_geocoding:
            await self._geocoding.aclose()

    async def collect(self, city: str, kickoff_at: datetime) -> EvidenceArtifact:
        observed_at = datetime.now(kickoff_at.tzinfo)
        location = await self._get_json(
            self._geocoding,
            "/search",
            {"name": city, "count": 1, "language": "en", "format": "json"},
        )
        results = location.get("results")
        if not isinstance(results, list) or not results or not isinstance(results[0], dict):
            return EvidenceArtifact(
                kind="weather",
                endpoint="open-meteo/geocoding+forecast",
                observed_at=observed_at,
            )
        place = results[0]
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return EvidenceArtifact(
                kind="weather",
                endpoint="open-meteo/geocoding+forecast",
                observed_at=observed_at,
            )
        match_date = kickoff_at.date().isoformat()
        forecast = await self._get_json(
            self._forecast,
            "/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ("temperature_2m,precipitation_probability,wind_speed_10m,weather_code"),
                "timezone": "UTC",
                "start_date": match_date,
                "end_date": match_date,
            },
        )
        record: dict[str, Any] = {
            "requested_city": city,
            "resolved_location": {
                key: place.get(key)
                for key in ("name", "country", "latitude", "longitude", "timezone")
            },
            "kickoff_at": kickoff_at.isoformat(),
            "hourly_units": forecast.get("hourly_units", {}),
            "hourly": forecast.get("hourly", {}),
        }
        return EvidenceArtifact(
            kind="weather",
            endpoint="open-meteo/geocoding+forecast",
            observed_at=observed_at,
            records=(record,),
        )

    @staticmethod
    async def _get_json(
        client: httpx.AsyncClient, endpoint: str, params: dict[str, OpenMeteoParam]
    ) -> dict[str, Any]:
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("OPEN_METEO_INVALID_RESPONSE")
        return payload
