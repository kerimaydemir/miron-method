import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.domain.auto_coupon import TOP_LEAGUES, MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture, TriageFactors


class _Outcome(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    price: Decimal = Field(gt=1)
    point: Decimal | None = None
    description: str | None = None


class _Market(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    last_update: datetime | None = None
    outcomes: tuple[_Outcome, ...]


class _Bookmaker(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    last_update: datetime | None = None
    markets: tuple[_Market, ...]


class _OddsEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    bookmakers: tuple[_Bookmaker, ...] = ()


class _Score(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    score: str


class _ScoreEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    completed: bool
    home_team: str
    away_team: str
    scores: tuple[_Score, ...] | None = None


class TheOddsApiProvider:
    source_name = "the_odds_api"
    default_supported_market_keys: tuple[str, ...] = (
        "h2h",
        "draw_no_bet",
        "btts",
        "totals",
        "alternate_totals",
        "team_totals",
        "alternate_team_totals",
    )

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        refresh_seconds: int,
        wide_markets: Sequence[str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self.supported_market_keys = self._allowed_market_keys(wide_markets)
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(25.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 allowed-odds-reader"},
        )
        self._owns_client = client is None
        self._fixtures: dict[UUID, CanonicalFixture] = {}
        self._markets: dict[UUID, MarketOdds] = {}
        self._sport_keys: dict[UUID, str] = {}
        self._refresh_lock = asyncio.Lock()
        self.observed_at: datetime | None = None

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def refresh(self, *, force: bool = False) -> None:
        if not self.available:
            return
        async with self._refresh_lock:
            now = datetime.now(UTC)
            if (
                not force
                and self.observed_at is not None
                and now - self.observed_at < self._refresh_interval
            ):
                return
            responses = await asyncio.gather(
                *(self._fetch_sport(league.odds_sport_key) for league in TOP_LEAGUES),
                return_exceptions=True,
            )
            fixtures: dict[UUID, CanonicalFixture] = {}
            markets: dict[UUID, MarketOdds] = {}
            success_count = 0
            for response in responses:
                if isinstance(response, BaseException):
                    continue
                success_count += 1
                for event in response:
                    normalized = self._normalize_event(event, now)
                    if normalized is None:
                        continue
                    fixture, market = normalized
                    fixtures[fixture.id] = fixture
                    markets[fixture.id] = market
            if success_count == 0:
                if self._fixtures:
                    return
                raise RuntimeError("THE_ODDS_API_UNAVAILABLE")
            self._fixtures = fixtures
            self._markets = markets
            self._sport_keys = {
                fixture.id: fixture.competition_key.removeprefix("theodds:")
                for fixture in fixtures.values()
            }
            self.observed_at = now

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]:
        await self.refresh()
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
        items = await self.list_market_fixtures(start_utc=start_utc, end_utc=end_utc)
        return tuple(
            fixture
            for fixture, _ in items
            if not competition_ids or fixture.competition_key in competition_ids
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
        return tuple(
            fixture
            for fixture in self._fixtures.values()
            if len(normalized) >= 2
            and normalized
            in f"{fixture.home_team} {fixture.away_team} {fixture.competition_name}".casefold()
            and (start_utc is None or fixture.kickoff_at >= start_utc)
            and (end_utc is None or fixture.kickoff_at < end_utc)
        )

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        await self.refresh()
        try:
            return self._fixtures[fixture_id]
        except KeyError as error:
            raise KeyError(str(fixture_id)) from error

    async def market_for(self, fixture_id: UUID) -> MarketOdds | None:
        await self.refresh()
        return self._markets.get(fixture_id)

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds:
        await self.refresh()
        fixture = self._fixtures.get(fixture_id)
        if fixture is None or fixture.provider_fixture_id is None:
            raise KeyError(str(fixture_id))
        sport_key = self._sport_keys[fixture_id]
        response = await self._client.get(
            f"/sports/{sport_key}/events/{fixture.provider_fixture_id}/odds",
            params={
                "apiKey": self._api_key,
                "regions": "eu",
                "markets": ",".join(self.supported_market_keys),
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            },
        )
        response.raise_for_status()
        event = _OddsEvent.model_validate(response.json())
        normalized = self._normalize_event(event, datetime.now(UTC))
        if normalized is None:
            raise ValueError("AUTO_COUPON_WIDE_MARKET_UNAVAILABLE")
        _, market = normalized
        self._markets[fixture_id] = market
        return market

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = await self.get_fixture(fixture_id)
        sport_key = self._sport_keys[fixture_id]
        response = await self._client.get(
            f"/sports/{sport_key}/scores",
            params={"apiKey": self._api_key, "daysFrom": 3, "dateFormat": "iso"},
        )
        response.raise_for_status()
        events = tuple(_ScoreEvent.model_validate(item) for item in response.json())
        event = next((item for item in events if item.id == fixture.provider_fixture_id), None)
        if event is None or not event.completed or not event.scores:
            return fixture
        scores = {item.name.casefold(): int(item.score) for item in event.scores}
        updated = fixture.model_copy(
            update={
                "status": "finished",
                "home_score": scores.get(event.home_team.casefold()),
                "away_score": scores.get(event.away_team.casefold()),
                "observed_at": datetime.now(UTC),
            }
        )
        self._fixtures[fixture_id] = updated
        return updated

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        market = await self.market_for(fixture.id)
        if market is None:
            raise KeyError(str(fixture.id))
        coverage = min(Decimal("1"), Decimal(market.bookmaker_count) / Decimal("8"))
        return TriageFactors(
            coverage_score=Decimal(".90"),
            source_freshness_score=Decimal(".98"),
            competitive_relevance_score=Decimal(".94"),
            model_information_gain_score=Decimal(".88"),
            market_coverage_score=coverage,
            lineup_uncertainty_resolvability=Decimal(".45"),
            user_interest_score=Decimal(".92"),
            historical_case_support=Decimal(".50"),
            kickoff_time_practicality=Decimal(".90"),
            estimated_cost_penalty=Decimal(".05"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0"),
        )

    async def _fetch_sport(self, sport_key: str) -> tuple[_OddsEvent, ...]:
        response = await self._client.get(
            f"/sports/{sport_key}/odds",
            params={
                "apiKey": self._api_key,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("THE_ODDS_API_INVALID_RESPONSE")
        return tuple(_OddsEvent.model_validate(item) for item in payload)

    @staticmethod
    def _normalize_event(
        event: _OddsEvent, observed_at: datetime
    ) -> tuple[CanonicalFixture, MarketOdds] | None:
        kickoff = event.commence_time
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)
        if kickoff <= observed_at:
            return None
        h2h_by_bookmaker: dict[str, tuple[Decimal, Decimal, Decimal, datetime]] = {}
        quote_groups: dict[
            tuple[str, str | None, Decimal | None],
            dict[str, dict[str, tuple[Decimal, datetime]]],
        ] = {}
        for bookmaker in event.bookmakers:
            for market in bookmaker.markets:
                market_observed_at = market.last_update or bookmaker.last_update
                if market_observed_at is None:
                    continue
                if market_observed_at.tzinfo is None:
                    market_observed_at = market_observed_at.replace(tzinfo=UTC)
                else:
                    market_observed_at = market_observed_at.astimezone(UTC)
                age = observed_at - market_observed_at
                if age < -timedelta(minutes=5) or age > timedelta(hours=6):
                    continue
                if market.key not in TheOddsApiProvider.default_supported_market_keys:
                    continue
                for item in market.outcomes:
                    normalized_outcome = TheOddsApiProvider._outcome_key(
                        event, market.key, item.name
                    )
                    if normalized_outcome is None:
                        continue
                    group_key = (market.key, item.description, item.point)
                    outcomes = quote_groups.setdefault(group_key, {}).setdefault(
                        bookmaker.key, {}
                    )
                    existing = outcomes.get(normalized_outcome)
                    if existing is None or market_observed_at > existing[1] or (
                        market_observed_at == existing[1] and item.price > existing[0]
                    ):
                        outcomes[normalized_outcome] = (item.price, market_observed_at)
                if market.key != "h2h":
                    continue
                prices = {item.name.casefold(): item.price for item in market.outcomes}
                home = prices.get(event.home_team.casefold())
                draw = prices.get("draw")
                away = prices.get(event.away_team.casefold())
                if home is not None and draw is not None and away is not None:
                    h2h_by_bookmaker[bookmaker.key] = (
                        home,
                        draw,
                        away,
                        market_observed_at,
                    )
        if not h2h_by_bookmaker:
            return None
        home_prices = [item[0] for item in h2h_by_bookmaker.values()]
        draw_prices = [item[1] for item in h2h_by_bookmaker.values()]
        away_prices = [item[2] for item in h2h_by_bookmaker.values()]
        avg_home = sum(home_prices, Decimal("0")) / len(home_prices)
        avg_draw = sum(draw_prices, Decimal("0")) / len(draw_prices)
        avg_away = sum(away_prices, Decimal("0")) / len(away_prices)
        raw = (Decimal("1") / avg_home, Decimal("1") / avg_draw, Decimal("1") / avg_away)
        total = sum(raw, Decimal("0"))
        fair_home = (raw[0] / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        fair_draw = (raw[1] / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        fair_away = Decimal("1") - fair_home - fair_draw
        normalized_quotes: list[MarketQuote] = []
        for (market_key, description, point), outcomes_by_bookmaker in quote_groups.items():
            required = TheOddsApiProvider._required_outcomes(market_key)
            if required is None:
                continue
            complete_bookmakers = {
                bookmaker: outcomes
                for bookmaker, outcomes in outcomes_by_bookmaker.items()
                if all(outcome in outcomes for outcome in required)
            }
            if not complete_bookmakers:
                continue
            averages = {
                outcome: sum(
                    (outcomes[outcome][0] for outcomes in complete_bookmakers.values()),
                    Decimal("0"),
                )
                / len(complete_bookmakers)
                for outcome in required
            }
            raw_probabilities = {outcome: Decimal("1") / averages[outcome] for outcome in required}
            overround = sum(raw_probabilities.values(), Decimal("0"))
            for outcome in required:
                fair_probability = (raw_probabilities[outcome] / overround).quantize(
                    Decimal(".000001"), rounding=ROUND_HALF_UP
                )
                for bookmaker_key, outcomes in complete_bookmakers.items():
                    normalized_quotes.append(
                        MarketQuote(
                            provider="the_odds_api",
                            observed_at=min(outcomes[item][1] for item in required),
                            market_key=market_key,
                            market_label=TheOddsApiProvider._market_label(market_key),
                            outcome_key=outcome,
                            outcome_label=TheOddsApiProvider._outcome_label(outcome),
                            description=description,
                            point=point,
                            decimal_odds=outcomes[outcome][0].quantize(
                                Decimal(".001"), rounding=ROUND_HALF_UP
                            ),
                            fair_probability=fair_probability,
                            bookmaker_count=len(complete_bookmakers),
                            bookmaker=bookmaker_key,
                        )
                    )
        league = next(item for item in TOP_LEAGUES if item.odds_sport_key == event.sport_key)
        fixture_id = uuid5(NAMESPACE_URL, f"the-odds-api:event:{event.id}")
        fixture = CanonicalFixture(
            id=fixture_id,
            competition_key=f"theodds:{event.sport_key}",
            competition_name=league.name,
            home_team=event.home_team,
            away_team=event.away_team,
            kickoff_at=kickoff,
            source_provider="the_odds_api",
            provider_fixture_id=event.id,
            observed_at=observed_at,
        )
        normalized_market = MarketOdds(
            event_id=event.id,
            observed_at=min(item[3] for item in h2h_by_bookmaker.values()),
            bookmaker_count=len(h2h_by_bookmaker),
            home_decimal=avg_home.quantize(Decimal(".001"), rounding=ROUND_HALF_UP),
            draw_decimal=avg_draw.quantize(Decimal(".001"), rounding=ROUND_HALF_UP),
            away_decimal=avg_away.quantize(Decimal(".001"), rounding=ROUND_HALF_UP),
            fair_home_probability=fair_home,
            fair_draw_probability=fair_draw,
            fair_away_probability=fair_away,
            quotes=tuple(normalized_quotes),
        )
        return fixture, normalized_market

    @staticmethod
    def _outcome_key(event: _OddsEvent, market_key: str, name: str) -> str | None:
        normalized = name.casefold()
        if normalized == event.home_team.casefold():
            return "home"
        if normalized == event.away_team.casefold():
            return "away"
        aliases = {
            "draw": "draw",
            "over": "over",
            "under": "under",
            "yes": "yes",
            "no": "no",
        }
        outcome = aliases.get(normalized)
        if outcome == "draw" and market_key != "h2h":
            return None
        return outcome

    @staticmethod
    def _required_outcomes(market_key: str) -> tuple[str, ...] | None:
        return {
            "h2h": ("home", "draw", "away"),
            "draw_no_bet": ("home", "away"),
            "btts": ("yes", "no"),
            "totals": ("over", "under"),
            "alternate_totals": ("over", "under"),
            "team_totals": ("over", "under"),
            "alternate_team_totals": ("over", "under"),
        }.get(market_key)

    @staticmethod
    def _market_label(market_key: str) -> str:
        return {
            "h2h": "Maç sonucu",
            "draw_no_bet": "Beraberlikte iade",
            "btts": "Karşılıklı gol",
            "totals": "Toplam gol",
            "alternate_totals": "Alternatif toplam gol",
            "team_totals": "Takım toplam gol",
            "alternate_team_totals": "Alternatif takım toplam gol",
        }[market_key]

    @staticmethod
    def _outcome_label(outcome: str) -> str:
        return {
            "home": "Ev sahibi",
            "draw": "Beraberlik",
            "away": "Deplasman",
            "over": "Üst",
            "under": "Alt",
            "yes": "Var",
            "no": "Yok",
        }[outcome]

    @classmethod
    def _allowed_market_keys(cls, raw_markets: Sequence[str] | None) -> tuple[str, ...]:
        if not raw_markets:
            return ("h2h", "totals")
        normalized = tuple(dict.fromkeys(item.strip() for item in raw_markets if item.strip()))
        allowed = tuple(item for item in normalized if item in cls.default_supported_market_keys)
        return allowed or ("h2h", "totals")
