import asyncio
import unicodedata
from datetime import UTC, datetime
from typing import Any

import httpx

from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
from app.domain.fixtures import CanonicalFixture
from app.infrastructure.open_meteo_provider import OpenMeteoProvider

ApiParam = str | int | float | bool | None


class ApiFootballProvider:
    source_name = "api_football"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://v3.football.api-sports.io",
        client: httpx.AsyncClient | None = None,
        weather_provider: OpenMeteoProvider | None = None,
        requests_per_minute: int = 10,
    ) -> None:
        if requests_per_minute <= 0:
            raise ValueError("API_FOOTBALL_RATE_LIMIT_INVALID")
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(25.0, connect=5.0),
            headers={
                "x-apisports-key": api_key,
                "User-Agent": "MIRON-BABA-AI/0.1 deep-football-evidence",
            },
        )
        self._owns_client = client is None
        self._weather = weather_provider
        self._request_interval = 60.0 / float(requests_per_minute)
        self._rate_lock = asyncio.Lock()
        self._next_request_at = 0.0

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
        if self._weather is not None:
            await self._weather.close()

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        if not self.available:
            raise PermissionError("API_FOOTBALL_KEY_REQUIRED")
        observed_at = datetime.now(UTC)
        fixture_record = await self._resolve_fixture(fixture)
        api_fixture = self._mapping(fixture_record, "fixture")
        league = self._mapping(fixture_record, "league")
        teams = self._mapping(fixture_record, "teams")
        home = self._mapping(teams, "home")
        away = self._mapping(teams, "away")
        fixture_id = int(api_fixture["id"])
        league_id = int(league["id"])
        season = int(league["season"])
        home_id = int(home["id"])
        away_id = int(away["id"])
        venue = api_fixture.get("venue")
        city = str(venue.get("city", "")) if isinstance(venue, dict) else ""

        requests: tuple[tuple[str, str, dict[str, ApiParam]], ...] = (
            ("statistics", "/fixtures/statistics", {"fixture": fixture_id}),
            ("lineups", "/fixtures/lineups", {"fixture": fixture_id}),
            ("players", "/fixtures/players", {"fixture": fixture_id}),
            ("injuries", "/injuries", {"fixture": fixture_id}),
            ("predictions", "/predictions", {"fixture": fixture_id}),
            ("odds", "/odds", {"fixture": fixture_id}),
            ("standings", "/standings", {"league": league_id, "season": season}),
            (
                "head_to_head",
                "/fixtures/headtohead",
                {"h2h": f"{home_id}-{away_id}", "last": 10},
            ),
            ("home_coach", "/coachs", {"team": home_id}),
            ("away_coach", "/coachs", {"team": away_id}),
            (
                "home_team_statistics",
                "/teams/statistics",
                {"team": home_id, "league": league_id, "season": season},
            ),
            (
                "away_team_statistics",
                "/teams/statistics",
                {"team": away_id, "league": league_id, "season": season},
            ),
            ("home_squad", "/players/squads", {"team": home_id}),
            ("away_squad", "/players/squads", {"team": away_id}),
            (
                "home_form",
                "/fixtures",
                {"team": home_id, "last": 10, "season": season},
            ),
            (
                "away_form",
                "/fixtures",
                {"team": away_id, "last": 10, "season": season},
            ),
        )
        results = await asyncio.gather(
            *(self._fetch(endpoint, params) for _, endpoint, params in requests),
            return_exceptions=True,
        )
        artifacts: list[EvidenceArtifact] = [
            EvidenceArtifact(
                kind="fixture",
                endpoint="/fixtures",
                observed_at=observed_at,
                records=(fixture_record,),
            )
        ]
        coverage: dict[str, bool] = {"fixture": True}
        for (kind, endpoint, _), result in zip(requests, results, strict=True):
            records = () if isinstance(result, BaseException) else result
            coverage[kind] = bool(records)
            artifacts.append(
                EvidenceArtifact(
                    kind=kind,
                    endpoint=endpoint,
                    observed_at=observed_at,
                    records=records,
                )
            )
        if self._weather is not None and city:
            try:
                weather = await self._weather.collect(city, fixture.kickoff_at)
            except (httpx.HTTPError, ValueError):
                weather = EvidenceArtifact(
                    kind="weather",
                    endpoint="open-meteo/geocoding+forecast",
                    observed_at=observed_at,
                )
            artifacts.append(weather)
            coverage["weather"] = bool(weather.records)
        return DeepFootballEvidence(
            provider=self.source_name,
            provider_fixture_id=str(fixture_id),
            observed_at=observed_at,
            home_team_id=home_id,
            away_team_id=away_id,
            league_id=league_id,
            season=season,
            artifacts=tuple(artifacts),
            coverage=coverage,
        )

    async def _resolve_fixture(self, fixture: CanonicalFixture) -> dict[str, Any]:
        records = await self._fetch("/fixtures", {"date": fixture.kickoff_at.date().isoformat()})
        target_home = self._normalize(fixture.home_team)
        target_away = self._normalize(fixture.away_team)
        for record in records:
            teams = record.get("teams", {})
            home = teams.get("home", {}) if isinstance(teams, dict) else {}
            away = teams.get("away", {}) if isinstance(teams, dict) else {}
            if self._normalize(str(home.get("name", ""))) != target_home:
                continue
            if self._normalize(str(away.get("name", ""))) != target_away:
                continue
            return record
        raise KeyError("API_FOOTBALL_FIXTURE_MAPPING_FAILED")

    async def _fetch(
        self, endpoint: str, params: dict[str, ApiParam]
    ) -> tuple[dict[str, Any], ...]:
        async with self._rate_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(
                endpoint,
                params=params,
                headers={"x-apisports-key": self._api_key},
            )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("errors"):
            raise ValueError("API_FOOTBALL_INVALID_RESPONSE")
        records = payload.get("response")
        if isinstance(records, dict):
            return (records,)
        if isinstance(records, list):
            return tuple(item for item in records if isinstance(item, dict))
        raise ValueError("API_FOOTBALL_INVALID_RESPONSE")

    @staticmethod
    def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
        item = value.get(key)
        if not isinstance(item, dict):
            raise ValueError("API_FOOTBALL_INVALID_RESPONSE")
        return item

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        plain = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        return " ".join(token for token in plain.split() if token not in {"fc", "cf", "sc"})
