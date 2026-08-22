import asyncio
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

import httpx

from app.domain.auto_coupon import TOP_LEAGUES
from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
from app.domain.fixtures import CanonicalFixture, TriageFactors

RAPID_LEAGUES = {
    47: ("epl", "Premier League"),
    87: ("laliga", "LaLiga"),
    54: ("bundesliga", "Bundesliga"),
    55: ("serie_a", "Serie A"),
    53: ("ligue_1", "Ligue 1"),
    57: ("eredivisie", "Eredivisie"),
    61: ("primeira", "Primeira Liga"),
    71: ("super_lig", "Süper Lig"),
}
ApiParam = str | int | float | bool | None


class RapidApiFootballProvider:
    """Quota-aware adapter for the user's 100 request/month RapidAPI BASIC plan."""

    source_name = "rapidapi_football"

    def __init__(
        self,
        *,
        api_key: str,
        host: str,
        timezone: str,
        refresh_seconds: int = 900,
        deep_request_limit: int = 4,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._host = host
        self._timezone = ZoneInfo(timezone)
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._deep_request_limit = deep_request_limit
        self._client = client or httpx.AsyncClient(
            base_url=f"https://{host}",
            timeout=httpx.Timeout(25.0, connect=5.0),
            headers={
                "x-rapidapi-host": host,
                "x-rapidapi-key": api_key,
                "User-Agent": "MIRON-BABA-AI/0.1 quota-aware-football-reader",
            },
        )
        self._owns_client = client is None
        self._fixtures: dict[UUID, CanonicalFixture] = {}
        self._last_window: tuple[date, date] | None = None
        self.observed_at: datetime | None = None
        self._refresh_lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return bool(self._api_key and self._host)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        await self._refresh(start_utc, end_utc)
        return tuple(
            item
            for item in sorted(self._fixtures.values(), key=lambda fixture: fixture.kickoff_at)
            if start_utc <= item.kickoff_at < end_utc
            and (not competition_ids or item.competition_key in competition_ids)
        )

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        now = datetime.now(UTC)
        await self._refresh(
            start_utc or now - timedelta(days=1), end_utc or now + timedelta(days=2)
        )
        normalized = self._normalize(query)
        return tuple(
            item
            for item in self._fixtures.values()
            if len(normalized) >= 2
            and normalized
            in self._normalize(f"{item.home_team} {item.away_team} {item.competition_name}")
            and (start_utc is None or item.kickoff_at >= start_utc)
            and (end_utc is None or item.kickoff_at < end_utc)
        )

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        item = self._fixtures.get(fixture_id)
        if item is not None:
            return item
        now = datetime.now(UTC)
        await self._refresh(now - timedelta(days=1), now + timedelta(days=2), force=True)
        try:
            return self._fixtures[fixture_id]
        except KeyError as error:
            raise KeyError(str(fixture_id)) from error

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = await self.get_fixture(fixture_id)
        await self._refresh(
            fixture.kickoff_at - timedelta(days=1),
            fixture.kickoff_at + timedelta(days=1),
            force=True,
        )
        return self._fixtures.get(fixture_id, fixture)

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        age = datetime.now(UTC) - (fixture.observed_at or datetime.now(UTC))
        freshness = Decimal(".95") if age <= timedelta(minutes=20) else Decimal(".65")
        return TriageFactors(
            coverage_score=Decimal(".82"),
            source_freshness_score=freshness,
            competitive_relevance_score=Decimal(".95"),
            model_information_gain_score=Decimal(".78"),
            market_coverage_score=Decimal("0"),
            lineup_uncertainty_resolvability=Decimal(".45"),
            user_interest_score=Decimal(".90"),
            historical_case_support=Decimal(".45"),
            kickoff_time_practicality=Decimal(".90"),
            estimated_cost_penalty=Decimal(".35"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0") if freshness > Decimal(".8") else Decimal(".2"),
        )

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        if not self.available:
            raise PermissionError("RAPIDAPI_KEY_REQUIRED")
        resolved = await self._resolve_fixture(fixture)
        event_id = int(resolved["id"])
        league_id = int(resolved["leagueId"])
        home = self._dict(resolved.get("home"))
        away = self._dict(resolved.get("away"))
        observed = datetime.now(UTC)
        requests: tuple[tuple[str, str, Mapping[str, ApiParam]], ...] = (
            ("fixture", "/football-get-match-detail", {"eventid": event_id}),
            ("head_to_head", "/football-get-head-to-head", {"eventid": event_id}),
            ("standings", "/football-get-standing-all", {"leagueid": league_id}),
            ("league_form", "/football-get-all-matches-by-league", {"leagueid": league_id}),
        )[: self._deep_request_limit]
        results = await asyncio.gather(
            *(self._fetch(path, params) for _, path, params in requests),
            return_exceptions=True,
        )
        artifacts: list[EvidenceArtifact] = []
        coverage = {
            "fixture": False,
            "head_to_head": False,
            "standings": False,
            "home_form": False,
            "away_form": False,
            "statistics": False,
            "lineups": False,
            "players": False,
            "injuries": False,
            "predictions": False,
            "odds": False,
            "weather": False,
        }
        for (kind, path, _), result in zip(requests, results, strict=True):
            records = () if isinstance(result, BaseException) else self._records(result)
            coverage[kind] = bool(records)
            if kind == "league_form" and records:
                coverage["home_form"] = True
                coverage["away_form"] = True
            artifacts.append(
                EvidenceArtifact(kind=kind, endpoint=path, observed_at=observed, records=records)
            )
        return DeepFootballEvidence(
            provider=self.source_name,
            provider_fixture_id=str(event_id),
            observed_at=observed,
            home_team_id=int(home.get("id") or 0),
            away_team_id=int(away.get("id") or 0),
            league_id=league_id,
            season=fixture.kickoff_at.year,
            artifacts=tuple(artifacts),
            coverage=coverage,
        )

    async def _refresh(
        self, start_utc: datetime, end_utc: datetime, *, force: bool = False
    ) -> None:
        if not self.available:
            return
        start_date = start_utc.astimezone(self._timezone).date()
        end_date = (end_utc - timedelta(microseconds=1)).astimezone(self._timezone).date()
        async with self._refresh_lock:
            now = datetime.now(UTC)
            if (
                not force
                and self.observed_at is not None
                and now - self.observed_at < self._refresh_interval
                and self._last_window == (start_date, end_date)
            ):
                return
            days = min(2, (end_date - start_date).days + 1)
            payloads = await asyncio.gather(
                *(
                    self._fetch(
                        "/football-get-matches-by-date",
                        {"date": (start_date + timedelta(days=index)).strftime("%Y%m%d")},
                    )
                    for index in range(days)
                )
            )
            fixtures: dict[UUID, CanonicalFixture] = {}
            for payload in payloads:
                response = payload.get("response")
                matches = response.get("matches") if isinstance(response, dict) else None
                if not isinstance(matches, list):
                    continue
                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    item = self._normalize_match(match, now)
                    if item is not None:
                        fixtures[item.id] = item
            self._fixtures.update(fixtures)
            self.observed_at = now
            self._last_window = (start_date, end_date)

    async def _resolve_fixture(self, fixture: CanonicalFixture) -> dict[str, Any]:
        if fixture.source_provider == self.source_name and fixture.provider_fixture_id:
            target_id = int(fixture.provider_fixture_id)
            await self._refresh(
                fixture.kickoff_at - timedelta(days=1),
                fixture.kickoff_at + timedelta(days=1),
            )
            for item in self._fixtures.values():
                if item.provider_fixture_id == str(target_id):
                    return {
                        "id": target_id,
                        "leagueId": int(item.competition_key.split(":")[2]),
                        "home": {"id": 0, "name": item.home_team},
                        "away": {"id": 0, "name": item.away_team},
                    }
        payload = await self._fetch(
            "/football-get-matches-by-date",
            {"date": fixture.kickoff_at.astimezone(self._timezone).strftime("%Y%m%d")},
        )
        response = payload.get("response")
        matches = response.get("matches") if isinstance(response, dict) else []
        for match in matches if isinstance(matches, list) else []:
            if not isinstance(match, dict):
                continue
            home = self._dict(match.get("home"))
            away = self._dict(match.get("away"))
            if self._normalize(str(home.get("name", ""))) == self._normalize(
                fixture.home_team
            ) and self._normalize(str(away.get("name", ""))) == self._normalize(fixture.away_team):
                return match
        raise KeyError("RAPIDAPI_FIXTURE_MAPPING_FAILED")

    async def _fetch(self, path: str, params: Mapping[str, ApiParam]) -> dict[str, Any]:
        response = await self._client.get(
            path,
            params=params,
            headers={"x-rapidapi-host": self._host, "x-rapidapi-key": self._api_key},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise ValueError("RAPIDAPI_INVALID_RESPONSE")
        return payload

    @staticmethod
    def _records(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        response = payload.get("response")
        if isinstance(response, list):
            return tuple(item for item in response if isinstance(item, dict))
        if isinstance(response, dict):
            return (response,) if response else ()
        return ()

    @staticmethod
    def _normalize_match(match: dict[str, Any], observed: datetime) -> CanonicalFixture | None:
        league_id = match.get("leagueId")
        if not isinstance(league_id, int) or league_id not in RAPID_LEAGUES:
            return None
        home = RapidApiFootballProvider._dict(match.get("home"))
        away = RapidApiFootballProvider._dict(match.get("away"))
        status = RapidApiFootballProvider._dict(match.get("status"))
        utc_time = status.get("utcTime")
        if not isinstance(utc_time, str):
            return None
        kickoff = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
        finished = bool(status.get("finished"))
        started = bool(status.get("started"))
        provider_id = str(match.get("id"))
        league_key, league_name = RAPID_LEAGUES[league_id]
        return CanonicalFixture(
            id=uuid5(NAMESPACE_URL, f"rapidapi-football:event:{provider_id}"),
            competition_key=f"rapidapi:{league_key}:{league_id}",
            competition_name=league_name,
            home_team=str(home.get("name") or home.get("longName") or "Unknown home"),
            away_team=str(away.get("name") or away.get("longName") or "Unknown away"),
            kickoff_at=kickoff,
            source_provider="rapidapi_football",
            provider_fixture_id=provider_id,
            status="finished" if finished else "live" if started else "scheduled",
            home_score=int(home["score"])
            if finished and isinstance(home.get("score"), int)
            else None,
            away_score=int(away["score"])
            if finished and isinstance(away.get("score"), int)
            else None,
            observed_at=observed,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        return " ".join(
            "".join(character for character in token if not unicodedata.combining(character))
            for token in decomposed.split()
            if token not in {"fc", "cf", "sc"}
        )

    @staticmethod
    def _dict(value: object) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}


assert {item.key for item in TOP_LEAGUES} == {item[0] for item in RAPID_LEAGUES.values()}
