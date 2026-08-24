import asyncio
import unicodedata
from datetime import UTC, datetime
from typing import Any

import httpx

from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
from app.domain.fixtures import CanonicalFixture

SportmonksParam = str | int | float | bool | None

RICH_FIXTURE_INCLUDE = (
    "participants;scores;events;lineups.player;statistics;xgfixture;predictions;"
    "sidelined.player;sidelined.type;venue;state;referees;odds"
)
SEARCH_FIXTURE_INCLUDE = "participants;scores;state;venue"


class SportmonksProvider:
    source_name = "sportmonks"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.sportmonks.com/v3/football",
        client: httpx.AsyncClient | None = None,
        requests_per_minute: int = 30,
    ) -> None:
        if requests_per_minute <= 0:
            raise ValueError("SPORTMONKS_RATE_LIMIT_INVALID")
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(25.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 sportmonks-evidence"},
        )
        self._owns_client = client is None
        self._request_interval = 60.0 / float(requests_per_minute)
        self._rate_lock = asyncio.Lock()
        self._next_request_at = 0.0

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        if not self.available:
            raise PermissionError("SPORTMONKS_KEY_REQUIRED")
        observed_at = datetime.now(UTC)
        fixture_record = await self._resolve_fixture(fixture)
        fixture_id = int(fixture_record["id"])
        rich_record = fixture_record
        try:
            rich_record = await self._fetch_one(
                f"/fixtures/{fixture_id}", {"include": RICH_FIXTURE_INCLUDE}
            )
        except (httpx.HTTPError, ValueError, KeyError):
            # Some free tokens reject specific includes. Keep the resolved fixture
            # instead of taking the whole deep-analysis path down.
            rich_record = fixture_record

        home_id, away_id = self._participant_ids(rich_record)
        league_id = self._int_value(rich_record.get("league_id"))
        season = self._int_value(rich_record.get("season_id")) or fixture.kickoff_at.year
        artifacts = (
            EvidenceArtifact(
                kind="fixture",
                endpoint="/fixtures/between/{start}/{end}",
                observed_at=observed_at,
                records=(fixture_record,),
            ),
            EvidenceArtifact(
                kind="fixture_rich",
                endpoint=f"/fixtures/{fixture_id}",
                observed_at=observed_at,
                records=(rich_record,),
            ),
        )
        coverage = {
            "fixture": True,
            "participants": bool(self._records(rich_record.get("participants"))),
            "scores": bool(self._records(rich_record.get("scores"))),
            "events": bool(self._records(rich_record.get("events"))),
            "lineups": bool(self._records(rich_record.get("lineups"))),
            "statistics": bool(self._records(rich_record.get("statistics"))),
            "xgfixture": bool(self._records(rich_record.get("xgfixture"))),
            "predictions": bool(self._records(rich_record.get("predictions"))),
            "sidelined": bool(self._records(rich_record.get("sidelined"))),
            "odds": bool(self._records(rich_record.get("odds"))),
            "venue": bool(rich_record.get("venue")),
            "state": bool(rich_record.get("state")),
            "referees": bool(self._records(rich_record.get("referees"))),
        }
        return DeepFootballEvidence(
            provider=self.source_name,
            provider_fixture_id=str(fixture_id),
            observed_at=observed_at,
            home_team_id=home_id,
            away_team_id=away_id,
            league_id=league_id,
            season=season,
            artifacts=artifacts,
            coverage=coverage,
        )

    async def _resolve_fixture(self, fixture: CanonicalFixture) -> dict[str, Any]:
        if fixture.source_provider == self.source_name and fixture.provider_fixture_id:
            return await self._fetch_one(
                f"/fixtures/{fixture.provider_fixture_id}", {"include": SEARCH_FIXTURE_INCLUDE}
            )
        date = fixture.kickoff_at.date().isoformat()
        records = await self._fetch_many(
            f"/fixtures/between/{date}/{date}", {"include": SEARCH_FIXTURE_INCLUDE}
        )
        target_home = self._normalize(fixture.home_team)
        target_away = self._normalize(fixture.away_team)
        for record in records:
            names = self._participant_names(record)
            if names == (target_home, target_away):
                return record
        raise KeyError("SPORTMONKS_FIXTURE_MAPPING_FAILED")

    async def _fetch_one(self, endpoint: str, params: dict[str, SportmonksParam]) -> dict[str, Any]:
        records = await self._fetch(endpoint, params)
        if len(records) != 1:
            raise ValueError("SPORTMONKS_INVALID_RESPONSE")
        return records[0]

    async def _fetch_many(
        self, endpoint: str, params: dict[str, SportmonksParam]
    ) -> tuple[dict[str, Any], ...]:
        return await self._fetch(endpoint, params)

    async def _fetch(
        self, endpoint: str, params: dict[str, SportmonksParam]
    ) -> tuple[dict[str, Any], ...]:
        async with self._rate_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(
                endpoint,
                params={**params, "api_token": self._api_key},
            )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or "data" not in payload:
            raise ValueError("SPORTMONKS_INVALID_RESPONSE")
        data = payload["data"]
        if isinstance(data, dict):
            return (data,)
        if isinstance(data, list):
            return tuple(item for item in data if isinstance(item, dict))
        raise ValueError("SPORTMONKS_INVALID_RESPONSE")

    @classmethod
    def _participant_names(cls, record: dict[str, Any]) -> tuple[str, str] | None:
        home_name = ""
        away_name = ""
        for participant in cls._records(record.get("participants")):
            name = cls._normalize(str(participant.get("name", "")))
            location = cls._participant_location(participant)
            if location == "home":
                home_name = name
            elif location == "away":
                away_name = name
        return (home_name, away_name) if home_name and away_name else None

    @classmethod
    def _participant_ids(cls, record: dict[str, Any]) -> tuple[int, int]:
        home_id = 0
        away_id = 0
        for participant in cls._records(record.get("participants")):
            participant_id = cls._int_value(participant.get("id"))
            location = cls._participant_location(participant)
            if location == "home":
                home_id = participant_id
            elif location == "away":
                away_id = participant_id
        return home_id, away_id

    @staticmethod
    def _participant_location(participant: dict[str, Any]) -> str:
        meta = participant.get("meta")
        if isinstance(meta, dict):
            location = meta.get("location")
            if isinstance(location, str):
                return location.casefold()
        location = participant.get("location")
        return location.casefold() if isinstance(location, str) else ""

    @staticmethod
    def _records(value: object) -> tuple[dict[str, Any], ...]:
        if isinstance(value, dict):
            data = value.get("data")
            if isinstance(data, list):
                return tuple(item for item in data if isinstance(item, dict))
            if isinstance(data, dict):
                return (data,)
            return (value,)
        if isinstance(value, list):
            return tuple(item for item in value if isinstance(item, dict))
        return ()

    @staticmethod
    def _int_value(value: object) -> int:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        plain = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        return " ".join(token for token in plain.split() if token not in {"fc", "cf", "sc"})
