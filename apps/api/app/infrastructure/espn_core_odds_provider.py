import asyncio
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.domain.auto_coupon import TOP_LEAGUES, MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture, TriageFactors

ESPN_CORE_LEAGUES: dict[str, str] = {
    "epl": "eng.1",
    "laliga": "esp.1",
    "bundesliga": "ger.1",
    "serie_a": "ita.1",
    "ligue_1": "fra.1",
    "eredivisie": "ned.1",
    "primeira": "por.1",
    "super_lig": "tur.1",
    "championship": "eng.2",
    "mls": "usa.1",
}


class EspnCoreOddsProvider:
    source_name = "espn_core_odds"
    supported_market_keys: tuple[str, ...] = ("h2h", "totals", "spread")

    def __init__(
        self,
        *,
        base_url: str = "https://sports.core.api.espn.com/v2/sports/soccer",
        league_paths: tuple[str, ...] = tuple(ESPN_CORE_LEAGUES.values()),
        refresh_seconds: int = 300,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._league_paths = tuple(path.strip().strip("/") for path in league_paths if path.strip())
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 espn-core-odds-reader"},
        )
        self._owns_client = client is None
        self._refresh_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()
        self._next_request_at = 0.0
        self._request_interval = 0.0 if client is not None else 0.15
        self._fixtures: dict[UUID, CanonicalFixture] = {}
        self._markets: dict[UUID, MarketOdds] = {}
        self._events: dict[UUID, dict[str, Any]] = {}
        self._last_window: tuple[str, str] | None = None
        self.observed_at: datetime | None = None

    @property
    def available(self) -> bool:
        return bool(self._league_paths)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]:
        await self.refresh(start_utc=start_utc, end_utc=end_utc)
        return tuple(
            (fixture, self._markets[fixture.id])
            for fixture in sorted(self._fixtures.values(), key=lambda item: item.kickoff_at)
            if start_utc <= fixture.kickoff_at < end_utc and fixture.status == "scheduled"
        )

    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]:
        pairs = await self.list_market_fixtures(start_utc=start_utc, end_utc=end_utc)
        return tuple(
            fixture
            for fixture, _ in pairs
            if not competition_ids or fixture.competition_key in competition_ids
        )

    async def search_fixtures(
        self,
        *,
        query: str,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> tuple[CanonicalFixture, ...]:
        now = datetime.now(UTC)
        await self.refresh(start_utc=start_utc or now, end_utc=end_utc or now + timedelta(days=1))
        needle = self._normalize(query)
        return tuple(
            fixture
            for fixture in self._fixtures.values()
            if len(needle) >= 2
            and needle in self._normalize(f"{fixture.home_team} {fixture.away_team}")
            and (start_utc is None or fixture.kickoff_at >= start_utc)
            and (end_utc is None or fixture.kickoff_at < end_utc)
        )

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        try:
            return self._fixtures[fixture_id]
        except KeyError as error:
            raise KeyError(str(fixture_id)) from error

    async def market_for(self, fixture_id: UUID) -> MarketOdds | None:
        return self._markets.get(fixture_id)

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds:
        market = self._markets.get(fixture_id)
        if market is None:
            raise KeyError(str(fixture_id))
        return market

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = await self.get_fixture(fixture_id)
        event = self._events.get(fixture_id)
        if not event:
            return await self.refresh_fixture_result(fixture)
        return await self._result_from_event(fixture, event)

    async def refresh_fixture_result(self, fixture: CanonicalFixture) -> CanonicalFixture:
        if not fixture.provider_fixture_id:
            return fixture
        league_path = self._league_path_for_fixture(fixture)
        if league_path is None:
            return fixture
        event = await self._fetch_json(
            f"{self._base_url}/leagues/{league_path}/events/{fixture.provider_fixture_id}",
            params={"lang": "en", "region": "us"},
        )
        return await self._result_from_event(fixture, event)

    async def _result_from_event(
        self, fixture: CanonicalFixture, event: Mapping[str, Any]
    ) -> CanonicalFixture:
        if not await self._event_completed(event):
            return fixture
        scores = await self._result_scores(event)
        if scores is None:
            return fixture
        home_score, away_score = scores
        return fixture.model_copy(
            update={
                "status": "finished",
                "home_score": home_score,
                "away_score": away_score,
                "observed_at": datetime.now(UTC),
            }
        )

    async def _event_completed(self, event: Mapping[str, Any]) -> bool:
        status = self._nested(event, "competitions", 0, "status", "type")
        if isinstance(status, Mapping):
            return bool(status.get("completed"))
        status_ref = self._ref_value(self._nested(event, "competitions", 0, "status"))
        if not status_ref:
            return False
        try:
            payload = await self._fetch_json(status_ref)
        except (RuntimeError, ValueError, httpx.HTTPError):
            return False
        status_type = payload.get("type")
        return isinstance(status_type, Mapping) and bool(status_type.get("completed"))

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        market = self._markets.get(fixture.id)
        if market is None:
            raise KeyError(str(fixture.id))
        return TriageFactors(
            coverage_score=Decimal(".82"),
            source_freshness_score=Decimal(".94"),
            competitive_relevance_score=Decimal(".90"),
            model_information_gain_score=Decimal(".84"),
            market_coverage_score=min(Decimal("1"), Decimal(market.bookmaker_count) / Decimal("2")),
            lineup_uncertainty_resolvability=Decimal(".42"),
            user_interest_score=Decimal(".88"),
            historical_case_support=Decimal(".48"),
            kickoff_time_practicality=Decimal(".90"),
            estimated_cost_penalty=Decimal("0"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0"),
        )

    async def refresh(
        self, *, start_utc: datetime, end_utc: datetime, force: bool = False
    ) -> None:
        if not self.available:
            return
        window = (start_utc.date().isoformat(), end_utc.date().isoformat())
        async with self._refresh_lock:
            now = datetime.now(UTC)
            if (
                not force
                and self.observed_at is not None
                and self._last_window == window
                and now - self.observed_at < self._refresh_interval
            ):
                return
            fixtures: dict[UUID, CanonicalFixture] = {}
            markets: dict[UUID, MarketOdds] = {}
            events: dict[UUID, dict[str, Any]] = {}
            league_dates = self._date_strings(start_utc, end_utc)
            for league_path in self._league_paths:
                league_key = self._league_key(league_path)
                if league_key is None:
                    continue
                for fixture_date in league_dates:
                    for event_ref in await self._event_refs(league_path, fixture_date):
                        try:
                            event = await self._fetch_json(event_ref)
                            hydrated = await self._hydrate_event(event)
                            normalized = await self._normalize_event(hydrated, league_key, now)
                        except (RuntimeError, ValueError, KeyError, httpx.HTTPError):
                            continue
                        if normalized is None:
                            continue
                        fixture, market = normalized
                        if not (start_utc <= fixture.kickoff_at < end_utc):
                            continue
                        fixtures[fixture.id] = fixture
                        markets[fixture.id] = market
                        events[fixture.id] = hydrated
            self._fixtures = fixtures
            self._markets = markets
            self._events = events
            self._last_window = window
            self.observed_at = now

    async def _event_refs(self, league_path: str, fixture_date: str) -> tuple[str, ...]:
        payload = await self._fetch_json(
            f"{self._base_url}/leagues/{league_path}/events",
            params={"dates": fixture_date, "lang": "en", "region": "us"},
        )
        items = payload.get("items")
        if not isinstance(items, list):
            return ()
        return tuple(
            self._https_url(str(item.get("$ref")))
            for item in items
            if isinstance(item, dict) and item.get("$ref")
        )

    async def _hydrate_event(self, event: dict[str, Any]) -> dict[str, Any]:
        competitors = self._nested(event, "competitions", 0, "competitors")
        if not isinstance(competitors, list):
            return event
        refs = tuple(
            self._https_url(str(team.get("$ref")))
            for competitor in competitors
            if isinstance(competitor, dict)
            and isinstance((team := competitor.get("team")), dict)
            and team.get("$ref")
        )
        results = await asyncio.gather(
            *(self._fetch_json(ref) for ref in refs), return_exceptions=True
        )
        hydrated_by_ref = {
            ref: result
            for ref, result in zip(refs, results, strict=True)
            if isinstance(result, dict)
        }
        for competitor in competitors:
            if not isinstance(competitor, dict):
                continue
            team = competitor.get("team")
            if isinstance(team, dict) and team.get("$ref"):
                hydrated = hydrated_by_ref.get(self._https_url(str(team.get("$ref"))))
                if hydrated:
                    competitor["team"] = hydrated
        return event

    async def _result_scores(self, event: Mapping[str, Any]) -> tuple[int, int] | None:
        competitors = self._nested(event, "competitions", 0, "competitors")
        if not isinstance(competitors, list):
            return None
        scores: dict[str, int] = {}
        for competitor in competitors:
            if not isinstance(competitor, Mapping):
                continue
            side = str(competitor.get("homeAway") or "").strip()
            score_ref = self._ref_value(competitor.get("score"))
            if side not in {"home", "away"} or not score_ref:
                continue
            try:
                payload = await self._fetch_json(score_ref)
            except (RuntimeError, ValueError, httpx.HTTPError):
                continue
            score = self._int_score(payload.get("value"))
            if score is not None:
                scores[side] = score
        if "home" not in scores or "away" not in scores:
            return None
        return scores["home"], scores["away"]

    async def _normalize_event(
        self, event: dict[str, Any], league_key: str, observed_at: datetime
    ) -> tuple[CanonicalFixture, MarketOdds] | None:
        event_id = str(event.get("id") or "")
        kickoff_raw = str(event.get("date") or "")
        if not event_id or not kickoff_raw:
            return None
        kickoff = datetime.fromisoformat(kickoff_raw.replace("Z", "+00:00"))
        if kickoff <= observed_at:
            return None
        competition = self._nested(event, "competitions", 0)
        if not isinstance(competition, dict):
            return None
        home_team, away_team = self._teams(competition)
        home_name = str(home_team.get("displayName") or home_team.get("name") or "").strip()
        away_name = str(away_team.get("displayName") or away_team.get("name") or "").strip()
        if not home_name or not away_name:
            return None
        odds_ref = self._ref_value(competition.get("odds"))
        if not odds_ref:
            return None
        odds_payload = await self._fetch_json(odds_ref)
        odds_items = tuple(
            item for item in odds_payload.get("items", []) if isinstance(item, dict)
        )
        if not odds_items:
            return None
        market = self._market(event_id, odds_items[0], home_name, away_name, observed_at)
        if market is None:
            return None
        fixture = CanonicalFixture(
            id=uuid5(NAMESPACE_URL, f"miron-baba-ai:espn-core:{league_key}:{event_id}"),
            competition_key=f"espn-core:{league_key}:{event_id}",
            competition_name=self._league_name(league_key),
            home_team=home_name,
            away_team=away_name,
            kickoff_at=kickoff,
            venue_name=str(self._nested(competition, "venue", "fullName") or "") or None,
            source_provider=self.source_name,
            provider_fixture_id=event_id,
            status="scheduled",
            observed_at=observed_at,
        )
        return fixture, market

    def _market(
        self,
        event_id: str,
        odds: Mapping[str, Any],
        home_name: str,
        away_name: str,
        observed_at: datetime,
    ) -> MarketOdds | None:
        bookmaker = str(self._nested(odds, "provider", "name") or "ESPN").strip()
        home_decimal = self._team_decimal(odds.get("homeTeamOdds"), "moneyLine")
        away_decimal = self._team_decimal(odds.get("awayTeamOdds"), "moneyLine")
        draw_decimal = self._american_to_decimal(self._nested(odds, "drawOdds", "moneyLine"))
        if home_decimal is None or away_decimal is None or draw_decimal is None:
            return None
        fair_home, fair_draw, fair_away = self._fair_probabilities(
            home_decimal, draw_decimal, away_decimal
        )
        quotes = [
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="h2h",
                market_label="Maç sonucu",
                outcome_key="home",
                outcome_label=home_name,
                description=home_name,
                decimal_odds=home_decimal,
                fair_probability=fair_home,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="h2h",
                market_label="Maç sonucu",
                outcome_key="draw",
                outcome_label="Beraberlik",
                description="Beraberlik",
                decimal_odds=draw_decimal,
                fair_probability=fair_draw,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="h2h",
                market_label="Maç sonucu",
                outcome_key="away",
                outcome_label=away_name,
                description=away_name,
                decimal_odds=away_decimal,
                fair_probability=fair_away,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
        ]
        quotes.extend(
            self._spread_quotes(odds, home_name, away_name, observed_at, bookmaker)
        )
        quotes.extend(self._total_quotes(odds, observed_at, bookmaker))
        return MarketOdds(
            provider=self.source_name,
            event_id=event_id,
            observed_at=observed_at,
            bookmaker_count=1,
            home_decimal=home_decimal,
            draw_decimal=draw_decimal,
            away_decimal=away_decimal,
            fair_home_probability=fair_home,
            fair_draw_probability=fair_draw,
            fair_away_probability=fair_away,
            quotes=tuple(quotes),
        )

    def _spread_quotes(
        self,
        odds: Mapping[str, Any],
        home_name: str,
        away_name: str,
        observed_at: datetime,
        bookmaker: str,
    ) -> tuple[MarketQuote, ...]:
        home_decimal = self._team_decimal(odds.get("homeTeamOdds"), "spread")
        away_decimal = self._team_decimal(odds.get("awayTeamOdds"), "spread")
        home_point = self._point(self._nested(odds, "homeTeamOdds", "current", "pointSpread"))
        away_point = self._point(self._nested(odds, "awayTeamOdds", "current", "pointSpread"))
        if (
            home_decimal is None
            or away_decimal is None
            or home_point is None
            or away_point is None
        ):
            return ()
        fair_home, fair_away = self._fair_probabilities(home_decimal, away_decimal)
        return (
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="spread",
                market_label="Handikap",
                outcome_key="home",
                outcome_label=home_name,
                description=home_name,
                point=home_point,
                decimal_odds=home_decimal,
                fair_probability=fair_home,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="spread",
                market_label="Handikap",
                outcome_key="away",
                outcome_label=away_name,
                description=away_name,
                point=away_point,
                decimal_odds=away_decimal,
                fair_probability=fair_away,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
        )

    def _total_quotes(
        self, odds: Mapping[str, Any], observed_at: datetime, bookmaker: str
    ) -> tuple[MarketQuote, ...]:
        line = self._decimal(odds.get("overUnder"))
        over_decimal = self._american_to_decimal(odds.get("overOdds"))
        under_decimal = self._american_to_decimal(odds.get("underOdds"))
        if line is None or over_decimal is None or under_decimal is None:
            return ()
        fair_over, fair_under = self._fair_probabilities(over_decimal, under_decimal)
        return (
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="totals",
                market_label="Toplam gol",
                outcome_key="over",
                outcome_label="Üst",
                point=line,
                decimal_odds=over_decimal,
                fair_probability=fair_over,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
            MarketQuote(
                provider=self.source_name,
                observed_at=observed_at,
                market_key="totals",
                market_label="Toplam gol",
                outcome_key="under",
                outcome_label="Alt",
                point=line,
                decimal_odds=under_decimal,
                fair_probability=fair_under,
                bookmaker_count=1,
                bookmaker=bookmaker,
            ),
        )

    async def _fetch_json(
        self, url: str, params: Mapping[str, str] | None = None
    ) -> dict[str, Any]:
        async with self._request_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(self._https_url(url), params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("ESPN_CORE_ODDS_INVALID_RESPONSE")
        return payload

    @staticmethod
    def _date_strings(start_utc: datetime, end_utc: datetime) -> tuple[str, ...]:
        days: list[str] = []
        current = start_utc.date()
        last = (end_utc - timedelta(microseconds=1)).date()
        while current <= last and len(days) < 3:
            days.append(current.strftime("%Y%m%d"))
            current = current + timedelta(days=1)
        return tuple(days)

    @staticmethod
    def _league_key(league_path: str) -> str | None:
        for key, candidate in ESPN_CORE_LEAGUES.items():
            if candidate == league_path:
                return key
        return None

    @staticmethod
    def _league_path_for_fixture(fixture: CanonicalFixture) -> str | None:
        parts = fixture.competition_key.split(":")
        if len(parts) >= 3 and parts[0] == "espn-core":
            return ESPN_CORE_LEAGUES.get(parts[1])
        league = next(
            (item for item in TOP_LEAGUES if item.key in fixture.competition_key),
            None,
        )
        if league is None:
            return None
        return ESPN_CORE_LEAGUES.get(league.key)

    @staticmethod
    def _league_name(league_key: str) -> str:
        return next((league.name for league in TOP_LEAGUES if league.key == league_key), league_key)

    @staticmethod
    def _teams(competition: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        home: Mapping[str, Any] = {}
        away: Mapping[str, Any] = {}
        competitors = competition.get("competitors")
        if not isinstance(competitors, list):
            return home, away
        for competitor in competitors:
            if not isinstance(competitor, dict):
                continue
            team = competitor.get("team")
            if not isinstance(team, dict):
                continue
            if competitor.get("homeAway") == "home":
                home = team
            elif competitor.get("homeAway") == "away":
                away = team
        return home, away

    @classmethod
    def _team_decimal(cls, value: object, key: str) -> Decimal | None:
        if not isinstance(value, Mapping):
            return None
        return cls._decimal(cls._nested(value, "current", key, "decimal"))

    @classmethod
    def _point(cls, value: object) -> Decimal | None:
        if not isinstance(value, Mapping):
            return None
        raw = value.get("alternateDisplayValue") or value.get("american")
        return cls._decimal(raw)

    @staticmethod
    def _fair_probabilities(*odds: Decimal) -> tuple[Decimal, ...]:
        implied = tuple(Decimal("1") / item for item in odds)
        total = sum(implied, Decimal("0"))
        return tuple(
            (item / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
            for item in implied
        )

    @classmethod
    def _american_to_decimal(cls, value: object) -> Decimal | None:
        american = cls._decimal(value)
        if american is None:
            return None
        if american > 0:
            decimal = Decimal("1") + american / Decimal("100")
        else:
            decimal = Decimal("1") + Decimal("100") / abs(american)
        return decimal.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _decimal(value: object) -> Decimal | None:
        try:
            return Decimal(str(value).strip().replace("+", ""))
        except (InvalidOperation, AttributeError):
            return None

    @staticmethod
    def _int_score(value: object) -> int | None:
        try:
            return int(Decimal(str(value).strip()))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    def _nested(value: Any, *path: str | int) -> Any:
        current = value
        for key in path:
            if isinstance(key, int) and isinstance(current, list) and len(current) > key:
                current = current[key]
            elif isinstance(key, str) and isinstance(current, Mapping):
                current = current.get(key)
            else:
                return None
        return current

    @classmethod
    def _ref_value(cls, value: Any) -> str:
        if isinstance(value, Mapping) and value.get("$ref"):
            return cls._https_url(str(value.get("$ref")))
        return ""

    @staticmethod
    def _https_url(url: str) -> str:
        if url.startswith("http://"):
            return "https://" + url.removeprefix("http://")
        return url

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        plain = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        return " ".join(re.sub(r"[^a-z0-9]+", " ", plain).split())
