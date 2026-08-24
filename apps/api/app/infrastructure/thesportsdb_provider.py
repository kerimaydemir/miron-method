import asyncio
import unicodedata
from datetime import UTC, datetime
from typing import Any

import httpx

from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
from app.domain.fixtures import CanonicalFixture

TheSportsDbParam = str | int | float | bool | None


class TheSportsDbProvider:
    source_name = "thesportsdb"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://www.thesportsdb.com/api/v1/json",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(20.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 thesportsdb-evidence"},
        )
        self._owns_client = client is None
        self._request_lock = asyncio.Lock()
        self._next_request_at = 0.0
        self._request_interval = 0.0 if client is not None else 0.6

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        if not self.available:
            raise PermissionError("THESPORTSDB_KEY_REQUIRED")
        observed_at = datetime.now(UTC)
        home_team = await self._search_team(fixture.home_team)
        away_team = await self._search_team(fixture.away_team)
        home_id = self._int_value(home_team.get("idTeam"))
        away_id = self._int_value(away_team.get("idTeam"))
        artifacts: list[EvidenceArtifact] = [
            EvidenceArtifact(
                kind="home_team",
                endpoint="/searchteams.php",
                observed_at=observed_at,
                records=(home_team,),
            ),
            EvidenceArtifact(
                kind="away_team",
                endpoint="/searchteams.php",
                observed_at=observed_at,
                records=(away_team,),
            ),
        ]
        optional_requests: tuple[tuple[str, str, dict[str, TheSportsDbParam]], ...] = (
            ("home_next_events", "/eventsnext.php", {"id": home_id}),
            ("away_next_events", "/eventsnext.php", {"id": away_id}),
            ("home_last_events", "/eventslast.php", {"id": home_id}),
            ("away_last_events", "/eventslast.php", {"id": away_id}),
        )
        results = await asyncio.gather(
            *(self._fetch(endpoint, params) for _, endpoint, params in optional_requests),
            return_exceptions=True,
        )
        candidate_events: list[dict[str, Any]] = []
        for (kind, endpoint, _), result in zip(optional_requests, results, strict=True):
            records = () if isinstance(result, BaseException) else result
            candidate_events.extend(records)
            artifacts.append(
                EvidenceArtifact(
                    kind=kind,
                    endpoint=endpoint,
                    observed_at=observed_at,
                    records=records,
                )
            )

        matched_event = self._match_event(fixture, candidate_events)
        event_id = str(matched_event.get("idEvent") or fixture.provider_fixture_id or "")
        if matched_event:
            artifacts.append(
                EvidenceArtifact(
                    kind="event",
                    endpoint="/eventsnext.php|/eventslast.php",
                    observed_at=observed_at,
                    records=(matched_event,),
                )
            )
            event_requests: tuple[tuple[str, str], ...] = (
                ("event_detail", "/lookupevent.php"),
                ("lineups", "/lookuplineup.php"),
                ("timeline", "/lookuptimeline.php"),
                ("statistics", "/lookupeventstats.php"),
            )
            event_results = await asyncio.gather(
                *(self._fetch(endpoint, {"id": event_id}) for _, endpoint in event_requests),
                return_exceptions=True,
            )
            for (kind, endpoint), result in zip(event_requests, event_results, strict=True):
                artifacts.append(
                    EvidenceArtifact(
                        kind=kind,
                        endpoint=endpoint,
                        observed_at=observed_at,
                        records=() if isinstance(result, BaseException) else result,
                    )
                )

        coverage = {artifact.kind: bool(artifact.records) for artifact in artifacts}
        coverage["fixture"] = bool(matched_event)
        coverage["team_metadata"] = bool(home_team and away_team)
        return DeepFootballEvidence(
            provider=self.source_name,
            provider_fixture_id=event_id or f"{home_id}-{away_id}",
            observed_at=observed_at,
            home_team_id=home_id,
            away_team_id=away_id,
            league_id=self._int_value(matched_event.get("idLeague")) if matched_event else 0,
            season=self._season_value(matched_event, fixture),
            artifacts=tuple(artifacts),
            coverage=coverage,
        )

    async def _search_team(self, name: str) -> dict[str, Any]:
        records = await self._fetch("/searchteams.php", {"t": name})
        target = self._normalize(name)
        for record in records:
            if self._normalize(str(record.get("strTeam", ""))) == target:
                return record
        if records:
            return records[0]
        raise KeyError("THESPORTSDB_TEAM_NOT_FOUND")

    async def _fetch(
        self, endpoint: str, params: dict[str, TheSportsDbParam]
    ) -> tuple[dict[str, Any], ...]:
        async with self._request_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(f"{self._api_key}{endpoint}", params=params)
        if response.is_error:
            raise RuntimeError(f"THESPORTSDB_HTTP_{response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("THESPORTSDB_INVALID_RESPONSE")
        records: list[dict[str, Any]] = []
        for value in payload.values():
            if isinstance(value, list):
                records.extend(item for item in value if isinstance(item, dict))
            elif isinstance(value, dict):
                records.append(value)
        return tuple(records)

    @classmethod
    def _match_event(
        cls, fixture: CanonicalFixture, events: list[dict[str, Any]]
    ) -> dict[str, Any]:
        target_home = cls._normalize(fixture.home_team)
        target_away = cls._normalize(fixture.away_team)
        target_date = fixture.kickoff_at.date().isoformat()
        for event in events:
            home = cls._normalize(str(event.get("strHomeTeam", "")))
            away = cls._normalize(str(event.get("strAwayTeam", "")))
            date = str(event.get("dateEvent") or "")
            if home == target_home and away == target_away and date == target_date:
                return event
        for event in events:
            home = cls._normalize(str(event.get("strHomeTeam", "")))
            away = cls._normalize(str(event.get("strAwayTeam", "")))
            if home == target_home and away == target_away:
                return event
        return {}

    @staticmethod
    def _season_value(event: dict[str, Any], fixture: CanonicalFixture) -> int:
        raw = str(event.get("strSeason") or "")
        for token in raw.replace("-", " ").split():
            if token.isdigit() and len(token) == 4:
                return int(token)
        return fixture.kickoff_at.year

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
