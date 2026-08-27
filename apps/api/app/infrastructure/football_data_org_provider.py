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

FREE_TOP_LEAGUE_CODES = ("PL", "PD", "BL1", "SA", "FL1", "DED", "PPL", "ELC")


class _Competition(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    name: str


class _Team(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str


class _FullTimeScore(BaseModel):
    model_config = ConfigDict(extra="ignore")

    home: int | None = None
    away: int | None = None


class _Score(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_time: _FullTimeScore = Field(alias="fullTime")


class _Match(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    utc_date: datetime = Field(alias="utcDate")
    status: str
    competition: _Competition
    home_team: _Team = Field(alias="homeTeam")
    away_team: _Team = Field(alias="awayTeam")
    score: _Score
    venue: str | None = None


class _MatchesResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    matches: tuple[_Match, ...] = ()


class FootballDataOrgProvider:
    source_name = "football_data_org"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        refresh_seconds: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY_MISSING")
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(20.0, connect=5.0),
            headers={
                "X-Auth-Token": api_key,
                "User-Agent": "MIRON-BABA-AI/0.1 football-data.org-reader",
            },
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
                self._refresh_loop(), name="football-data-org-refresh"
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
            response = await self._client.get(
                "/matches",
                params={
                    "competitions": ",".join(FREE_TOP_LEAGUE_CODES),
                    "dateFrom": (now - timedelta(days=3)).date().isoformat(),
                    "dateTo": (now + timedelta(days=14)).date().isoformat(),
                },
            )
            response.raise_for_status()
            payload = _MatchesResponse.model_validate(response.json())
            self._fixtures = {
                fixture.id: fixture
                for item in payload.matches
                if (fixture := self._canonical_fixture(item, now)) is not None
            }
            self.observed_at = now
            logger.info(
                "football-data.org cache refreshed",
                extra={"fixture_count": len(self._fixtures)},
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
        if fixture.source_provider != "football_data_org":
            raise KeyError(str(fixture.id))
        freshness = (
            Decimal(".98")
            if fixture.observed_at is not None
            and datetime.now(UTC) - fixture.observed_at <= self._refresh_interval * 2
            else Decimal(".70")
        )
        return TriageFactors(
            coverage_score=Decimal(".86"),
            source_freshness_score=freshness,
            competitive_relevance_score=Decimal(".90"),
            model_information_gain_score=Decimal(".84"),
            market_coverage_score=Decimal(".30"),
            lineup_uncertainty_resolvability=Decimal(".40"),
            user_interest_score=Decimal(".88"),
            historical_case_support=Decimal(".60"),
            kickoff_time_practicality=Decimal(".95"),
            estimated_cost_penalty=Decimal(".03"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0") if freshness > Decimal(".9") else Decimal(".2"),
        )

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        await self.refresh(force=True)
        fixture = self._fixtures.get(fixture_id)
        if fixture is None:
            raise KeyError(str(fixture_id))
        return fixture

    async def _refresh_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.refresh(force=True)
            except Exception as error:
                logger.warning(
                    "football-data.org background refresh failed",
                    extra={"error_type": type(error).__name__},
                )
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._refresh_interval.total_seconds()
                )
            except TimeoutError:
                continue

    @staticmethod
    def _canonical_fixture(item: _Match, observed_at: datetime) -> CanonicalFixture | None:
        code = item.competition.code.upper()
        if code not in FREE_TOP_LEAGUE_CODES:
            return None
        kickoff = (
            item.utc_date if item.utc_date.tzinfo is not None else item.utc_date.replace(tzinfo=UTC)
        )
        status = FootballDataOrgProvider._status(item.status, kickoff)
        return CanonicalFixture(
            id=uuid5(NAMESPACE_URL, f"football-data.org:match:{item.id}"),
            competition_key=f"football-data:{code.casefold()}:{kickoff.year}",
            competition_name=item.competition.name,
            home_team=item.home_team.name,
            away_team=item.away_team.name,
            kickoff_at=kickoff,
            venue_name=item.venue,
            source_provider="football_data_org",
            provider_fixture_id=str(item.id),
            status=status,
            home_score=item.score.full_time.home,
            away_score=item.score.full_time.away,
            observed_at=observed_at,
        )

    @staticmethod
    def _status(raw_status: str, kickoff: datetime) -> str:
        normalized = raw_status.upper()
        if normalized in {"FINISHED", "AWARDED"}:
            return "finished"
        if normalized in {"IN_PLAY", "PAUSED", "LIVE"}:
            return "live"
        if kickoff <= datetime.now(UTC) and normalized not in {"POSTPONED", "CANCELLED"}:
            return "live"
        return "scheduled"
