import asyncio
import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.domain.fixtures import CanonicalFixture, TriageFactors

logger = logging.getLogger(__name__)


class _OpenLigaTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")

    team_id: int = Field(alias="teamId")
    team_name: str = Field(alias="teamName")


class _OpenLigaResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    points_team1: int = Field(alias="pointsTeam1")
    points_team2: int = Field(alias="pointsTeam2")
    result_order_id: int = Field(alias="resultOrderID")


class _OpenLigaGoal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score_team1: int = Field(alias="scoreTeam1")
    score_team2: int = Field(alias="scoreTeam2")


class _OpenLigaLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    stadium: str | None = Field(default=None, alias="locationStadium")


class _OpenLigaMatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    match_id: int = Field(alias="matchID")
    match_date_time_utc: datetime = Field(alias="matchDateTimeUTC")
    league_name: str = Field(alias="leagueName")
    league_season: int = Field(alias="leagueSeason")
    league_shortcut: str = Field(alias="leagueShortcut")
    match_is_finished: bool = Field(alias="matchIsFinished")
    team1: _OpenLigaTeam
    team2: _OpenLigaTeam
    match_results: tuple[_OpenLigaResult, ...] = Field(default=(), alias="matchResults")
    goals: tuple[_OpenLigaGoal, ...] = ()
    location: _OpenLigaLocation | None = None


class OpenLigaDbProvider:
    source_name = "openligadb"

    def __init__(
        self,
        *,
        base_url: str,
        league_shortcuts: tuple[str, ...],
        refresh_seconds: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not league_shortcuts:
            raise ValueError("OPENLIGADB_LEAGUES_REQUIRED")
        self._league_shortcuts = tuple(dict.fromkeys(league_shortcuts))
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(20.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 OpenLigaDB-ODbL-reader"},
        )
        self._owns_client = client is None
        self._fixtures: dict[UUID, CanonicalFixture] = {}
        self._refresh_lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._refresh_task: asyncio.Task[None] | None = None
        self.observed_at: datetime | None = None

    async def start(self) -> None:
        if self._refresh_task is None:
            self._refresh_task = asyncio.create_task(
                self._refresh_loop(), name="openligadb-refresh"
            )

    async def stop(self) -> None:
        self._stop_event.set()
        if self._refresh_task is not None:
            await self._refresh_task
            self._refresh_task = None
        if self._owns_client:
            await self._client.aclose()

    async def refresh(self, *, force: bool = False) -> None:
        async with self._refresh_lock:
            now = datetime.now(UTC)
            if (
                not force
                and self.observed_at is not None
                and now - self.observed_at < self._refresh_interval
            ):
                return
            responses = await asyncio.gather(
                *(self._fetch_league(shortcut) for shortcut in self._league_shortcuts),
                return_exceptions=True,
            )
            matches: list[_OpenLigaMatch] = []
            successful_leagues = 0
            for shortcut, response in zip(self._league_shortcuts, responses, strict=True):
                if isinstance(response, BaseException):
                    logger.warning(
                        "OpenLigaDB league refresh failed",
                        extra={"league": shortcut, "error_type": type(response).__name__},
                    )
                    continue
                successful_leagues += 1
                matches.extend(response)
            if successful_leagues == 0:
                if self._fixtures:
                    return
                raise RuntimeError("OPENLIGADB_UNAVAILABLE")
            self._fixtures = {
                fixture.id: fixture
                for match in matches
                if (fixture := self._canonical_fixture(match, now)) is not None
            }
            self.observed_at = now
            logger.info(
                "OpenLigaDB cache refreshed",
                extra={
                    "league_count": successful_leagues,
                    "fixture_count": len(self._fixtures),
                },
            )

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        await self.refresh()
        now = datetime.now(UTC)
        return tuple(
            sorted(
                (
                    fixture
                    for fixture in self._fixtures.values()
                    if start_utc <= fixture.kickoff_at < end_utc
                    and fixture.kickoff_at > now
                    and fixture.status == "scheduled"
                    and (not competition_ids or fixture.competition_key in competition_ids)
                ),
                key=lambda fixture: fixture.kickoff_at,
            )
        )

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        await self.refresh()
        normalized = " ".join(query.casefold().split())
        if len(normalized) < 2:
            return ()
        now = datetime.now(UTC)
        return tuple(
            fixture
            for fixture in sorted(self._fixtures.values(), key=lambda item: item.kickoff_at)
            if normalized
            in f"{fixture.home_team} {fixture.away_team} {fixture.competition_name}".casefold()
            and fixture.kickoff_at > now
            and (start_utc is None or fixture.kickoff_at >= start_utc)
            and (end_utc is None or fixture.kickoff_at < end_utc)
        )

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        await self.refresh()
        fixture = self._fixtures.get(fixture_id)
        if fixture is None:
            raise KeyError(str(fixture_id))
        return fixture

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        if fixture.source_provider != "openligadb":
            raise KeyError(str(fixture.id))
        freshness = (
            Decimal(".98")
            if fixture.observed_at is not None
            and datetime.now(UTC) - fixture.observed_at <= self._refresh_interval * 2
            else Decimal(".70")
        )
        relevance = (
            Decimal(".90")
            if any(
                marker in fixture.competition_key for marker in (":la1:", ":dfb:", ":bl1:", ":ucl:")
            )
            else Decimal(".76")
        )
        return TriageFactors(
            coverage_score=Decimal(".72"),
            source_freshness_score=freshness,
            competitive_relevance_score=relevance,
            model_information_gain_score=Decimal(".84"),
            market_coverage_score=Decimal(".40"),
            lineup_uncertainty_resolvability=Decimal(".35"),
            user_interest_score=Decimal(".86"),
            historical_case_support=Decimal(".55"),
            kickoff_time_practicality=Decimal(".95"),
            estimated_cost_penalty=Decimal(".05"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0") if freshness > Decimal(".9") else Decimal(".2"),
        )

    async def _fetch_league(self, shortcut: str) -> tuple[_OpenLigaMatch, ...]:
        response = await self._client.get(f"/getmatchdata/{shortcut}")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("OPENLIGADB_INVALID_RESPONSE")
        return tuple(_OpenLigaMatch.model_validate(item) for item in payload)

    async def _refresh_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.refresh(force=True)
            except Exception as error:
                logger.warning(
                    "OpenLigaDB background refresh failed",
                    extra={"error_type": type(error).__name__},
                )
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._refresh_interval.total_seconds()
                )
            except TimeoutError:
                continue

    @staticmethod
    def _canonical_fixture(match: _OpenLigaMatch, observed_at: datetime) -> CanonicalFixture | None:
        kickoff = match.match_date_time_utc
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        status = (
            "finished" if match.match_is_finished else ("live" if kickoff <= now else "scheduled")
        )
        score: tuple[int | None, int | None] = (None, None)
        if match.match_results:
            latest = max(match.match_results, key=lambda item: item.result_order_id)
            score = (latest.points_team1, latest.points_team2)
        elif match.goals:
            latest_goal = match.goals[-1]
            score = (latest_goal.score_team1, latest_goal.score_team2)
        return CanonicalFixture(
            id=uuid5(NAMESPACE_URL, f"openligadb:match:{match.match_id}"),
            competition_key=(
                f"openligadb:{match.league_shortcut.casefold()}:{match.league_season}"
            ),
            competition_name=match.league_name,
            home_team=match.team1.team_name,
            away_team=match.team2.team_name,
            kickoff_at=kickoff,
            venue_name=match.location.stadium if match.location else None,
            source_provider="openligadb",
            provider_fixture_id=str(match.match_id),
            status=status,
            home_score=score[0],
            away_score=score[1],
            observed_at=observed_at,
        )
