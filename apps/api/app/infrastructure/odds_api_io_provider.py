import asyncio
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from pydantic import BaseModel, ConfigDict

from app.domain.auto_coupon import TOP_LEAGUES, MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture, TriageFactors

ODDS_API_IO_LEAGUE_SLUGS: dict[str, str] = {
    "epl": "england-premier-league",
    "laliga": "spain-laliga",
    "bundesliga": "germany-bundesliga",
    "serie_a": "italy-serie-a",
    "ligue_1": "france-ligue-1",
    "eredivisie": "netherlands-eredivisie",
    "primeira": "portugal-liga-portugal",
    "super_lig": "turkiye-super-lig",
    "championship": "england-championship",
    "mls": "usa-mls",
}


class _SportRef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    slug: str


class _OddsApiIoEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | str
    home: str
    away: str
    date: datetime
    status: str = "pending"
    sport: _SportRef | None = None
    league: _SportRef
    scores: dict[str, int | str | None] | None = None


class OddsApiIoProvider:
    source_name = "odds_api_io"
    supported_market_keys: tuple[str, ...] = (
        "h2h",
        "draw_no_bet",
        "double_chance",
        "btts",
        "totals",
        "spread",
        "odd_even",
        "first_half_h2h",
        "first_half_totals",
        "corners_spread",
        "cards_spread",
    )

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        refresh_seconds: int,
        bookmakers: str,
        events_per_league: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._bookmakers = bookmakers
        self._events_per_league = max(1, min(events_per_league, 10))
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(25.0, connect=5.0),
            headers={"User-Agent": "MIRON-BABA-AI/0.1 allowed-odds-reader"},
        )
        self._owns_client = client is None
        self._fixtures: dict[UUID, CanonicalFixture] = {}
        self._markets: dict[UUID, MarketOdds] = {}
        self._event_ids: dict[UUID, str] = {}
        self._league_slugs: dict[UUID, str] = {}
        self._refresh_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()
        self._next_request_at = 0.0
        self._request_interval = 0.0 if client is not None else 0.85
        self._retry_base_seconds = 0.0 if client is not None else 2.0
        self._retry_step_seconds = 0.0 if client is not None else 2.0
        self.observed_at: datetime | None = None

    @property
    def available(self) -> bool:
        return bool(self._api_key and self._bookmakers)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def refresh(
        self,
        *,
        force: bool = False,
        start_utc: datetime | None = None,
        end_utc: datetime | None = None,
    ) -> None:
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
            fixtures: dict[UUID, CanonicalFixture] = {}
            markets: dict[UUID, MarketOdds] = {}
            event_ids: dict[UUID, str] = {}
            league_slugs: dict[UUID, str] = {}
            success_count = 0
            events: list[_OddsApiIoEvent] = []
            for league in TOP_LEAGUES:
                try:
                    response = await self._fetch_league_events(ODDS_API_IO_LEAGUE_SLUGS[league.key])
                except (RuntimeError, ValueError):
                    continue
                success_count += 1
                events.extend(response)
            if start_utc is not None and end_utc is not None:
                events = [
                    event
                    for event in events
                    if start_utc <= self._as_utc(event.date) < end_utc
                    and event.status.casefold() in {"pending", "scheduled"}
                ]
            for chunk_start in range(0, len(events), 10):
                event_chunk = events[chunk_start : chunk_start + 10]
                try:
                    odds_payloads = await self._fetch_multi_event_odds(
                        tuple(event.id for event in event_chunk)
                    )
                except (RuntimeError, ValueError):
                    odds_payloads = tuple()
                payload_by_id = {str(item.get("id")): item for item in odds_payloads}
                for event in event_chunk:
                    odds_payload = payload_by_id.get(str(event.id))
                    if odds_payload is None:
                        try:
                            odds_payload = await self._fetch_event_odds(event.id)
                        except (RuntimeError, ValueError):
                            continue
                    normalized = self._normalize_event(odds_payload, now)
                    if normalized is None:
                        continue
                    fixture, market = normalized
                    fixtures[fixture.id] = fixture
                    markets[fixture.id] = market
                    event_ids[fixture.id] = str(event.id)
                    league_slugs[fixture.id] = event.league.slug
            if success_count == 0:
                if self._fixtures:
                    return
                raise RuntimeError("ODDS_API_IO_UNAVAILABLE")
            self._fixtures = fixtures
            self._markets = markets
            self._event_ids = event_ids
            self._league_slugs = league_slugs
            self.observed_at = now

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
        event_id = self._event_ids.get(fixture_id)
        if event_id is None:
            raise KeyError(str(fixture_id))
        payload = await self._fetch_event_odds(event_id)
        normalized = self._normalize_event(payload, datetime.now(UTC))
        if normalized is None:
            raise ValueError("AUTO_COUPON_WIDE_MARKET_UNAVAILABLE")
        _, market = normalized
        self._markets[fixture_id] = market
        return market

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = await self.get_fixture(fixture_id)
        return await self.refresh_fixture_result(fixture)

    async def refresh_fixture_result(self, fixture: CanonicalFixture) -> CanonicalFixture:
        league_slug = self._league_slugs.get(fixture.id) or self._league_slug_for_fixture(fixture)
        if not league_slug:
            return fixture
        response = await self._client.get(
            "/events",
            params={
                "apiKey": self._api_key,
                "sport": "football",
                "league": league_slug,
                "status": "settled",
                "limit": 50,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return fixture
        events = tuple(_OddsApiIoEvent.model_validate(item) for item in payload)
        event = next((item for item in events if str(item.id) == fixture.provider_fixture_id), None)
        if event is None or event.scores is None:
            return fixture
        home_score = self._int_score(event.scores.get("home"))
        away_score = self._int_score(event.scores.get("away"))
        if home_score is None or away_score is None:
            return fixture
        updated = fixture.model_copy(
            update={
                "status": "finished",
                "home_score": home_score,
                "away_score": away_score,
                "observed_at": datetime.now(UTC),
            }
        )
        self._fixtures[fixture.id] = updated
        return updated

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        market = await self.market_for(fixture.id)
        if market is None:
            raise KeyError(str(fixture.id))
        coverage = min(Decimal("1"), Decimal(market.bookmaker_count) / Decimal("2"))
        return TriageFactors(
            coverage_score=Decimal(".86"),
            source_freshness_score=Decimal(".96"),
            competitive_relevance_score=Decimal(".94"),
            model_information_gain_score=Decimal(".90"),
            market_coverage_score=coverage,
            lineup_uncertainty_resolvability=Decimal(".45"),
            user_interest_score=Decimal(".92"),
            historical_case_support=Decimal(".50"),
            kickoff_time_practicality=Decimal(".90"),
            estimated_cost_penalty=Decimal(".03"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0"),
        )

    async def _fetch_league_events(self, league_slug: str) -> tuple[_OddsApiIoEvent, ...]:
        payload = await self._get_json(
            "/events",
            params={
                "apiKey": self._api_key,
                "sport": "football",
                "league": league_slug,
                "status": "pending",
                "limit": self._events_per_league,
            },
        )
        if not isinstance(payload, list):
            raise ValueError("ODDS_API_IO_INVALID_RESPONSE")
        return tuple(_OddsApiIoEvent.model_validate(item) for item in payload)

    async def _fetch_event_odds(self, event_id: int | str) -> Mapping[str, object]:
        payload = await self._get_json(
            "/odds",
            params={
                "apiKey": self._api_key,
                "eventId": str(event_id),
                "bookmakers": self._bookmakers,
            },
        )
        if not isinstance(payload, dict):
            raise ValueError("ODDS_API_IO_INVALID_RESPONSE")
        return payload

    async def _fetch_multi_event_odds(
        self, event_ids: tuple[int | str, ...]
    ) -> tuple[Mapping[str, object], ...]:
        if not event_ids:
            return ()
        payload = await self._get_json(
            "/odds/multi",
            params={
                "apiKey": self._api_key,
                "eventIds": ",".join(str(event_id) for event_id in event_ids[:10]),
                "bookmakers": self._bookmakers,
            },
        )
        if not isinstance(payload, list):
            raise ValueError("ODDS_API_IO_INVALID_RESPONSE")
        return tuple(item for item in payload if isinstance(item, dict))

    async def _get_json(self, endpoint: str, params: Mapping[str, str | int]) -> object:
        for attempt in range(3):
            async with self._request_lock:
                loop = asyncio.get_running_loop()
                wait_seconds = self._next_request_at - loop.time()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                self._next_request_at = loop.time() + self._request_interval
                response = await self._client.get(endpoint, params=params)
            if response.status_code == 429 and attempt < 2:
                retry_after = self._decimal(response.headers.get("retry-after"))
                default_retry = Decimal(
                    str(self._retry_base_seconds + attempt * self._retry_step_seconds)
                )
                await asyncio.sleep(float(retry_after or default_retry))
                continue
            if response.status_code == 429:
                raise RuntimeError("ODDS_API_IO_RATE_LIMITED")
            if response.is_error:
                raise RuntimeError(f"ODDS_API_IO_HTTP_{response.status_code}")
            try:
                return response.json()
            except ValueError as error:
                raise ValueError("ODDS_API_IO_INVALID_RESPONSE") from error
        raise RuntimeError("ODDS_API_IO_RATE_LIMITED")

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @classmethod
    def _normalize_event(
        cls, payload: Mapping[str, object], observed_at: datetime
    ) -> tuple[CanonicalFixture, MarketOdds] | None:
        event = _OddsApiIoEvent.model_validate(payload)
        kickoff = event.date
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)
        if kickoff <= observed_at:
            return None
        league = next(
            (
                item
                for item in TOP_LEAGUES
                if ODDS_API_IO_LEAGUE_SLUGS[item.key] == event.league.slug
            ),
            None,
        )
        if league is None:
            return None
        bookmakers = payload.get("bookmakers")
        if not isinstance(bookmakers, dict):
            return None
        quote_groups: dict[
            tuple[str, str | None, Decimal | None],
            dict[str, list[tuple[Decimal, datetime]]],
        ] = {}
        latest_updates: list[datetime] = []
        for market_items in bookmakers.values():
            if not isinstance(market_items, list):
                continue
            for market_item in market_items:
                if not isinstance(market_item, dict):
                    continue
                market_key = cls._market_key(str(market_item.get("name", "")))
                if market_key is None:
                    continue
                updated = cls._parse_datetime(market_item.get("updatedAt"), observed_at)
                odds_rows = market_item.get("odds")
                if not isinstance(odds_rows, list):
                    continue
                for row in odds_rows:
                    if not isinstance(row, dict):
                        continue
                    point = cls._decimal(row.get("hdp"))
                    for raw_outcome, outcome_key in cls._outcome_mapping(market_key).items():
                        price = cls._decimal(row.get(raw_outcome))
                        if price is None or price <= 1:
                            continue
                        quote_groups.setdefault((market_key, None, point), {}).setdefault(
                            outcome_key, []
                        ).append((price, updated))
                        latest_updates.append(updated)
        h2h = quote_groups.get(("h2h", None, None), {})
        if not all(outcome in h2h for outcome in ("home", "draw", "away")):
            return None
        home_prices = [item[0] for item in h2h["home"]]
        draw_prices = [item[0] for item in h2h["draw"]]
        away_prices = [item[0] for item in h2h["away"]]
        avg_home = sum(home_prices, Decimal("0")) / len(home_prices)
        avg_draw = sum(draw_prices, Decimal("0")) / len(draw_prices)
        avg_away = sum(away_prices, Decimal("0")) / len(away_prices)
        raw = (Decimal("1") / avg_home, Decimal("1") / avg_draw, Decimal("1") / avg_away)
        total = sum(raw, Decimal("0"))
        fair_home = (raw[0] / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        fair_draw = (raw[1] / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        fair_away = Decimal("1") - fair_home - fair_draw
        normalized_quotes: list[MarketQuote] = []
        for (market_key, description, point), outcomes in quote_groups.items():
            required = cls._required_outcomes(market_key)
            if required is None or not all(outcome in outcomes for outcome in required):
                continue
            averages = {
                outcome: sum((item[0] for item in outcomes[outcome]), Decimal("0"))
                / len(outcomes[outcome])
                for outcome in required
            }
            raw_probabilities = {outcome: Decimal("1") / averages[outcome] for outcome in required}
            overround = sum(raw_probabilities.values(), Decimal("0"))
            for outcome in required:
                samples = outcomes[outcome]
                normalized_quotes.append(
                    MarketQuote(
                        provider="odds_api_io",
                        observed_at=max(item[1] for item in samples),
                        market_key=market_key,
                        market_label=cls._market_label(market_key),
                        outcome_key=outcome,
                        outcome_label=cls._outcome_label(outcome),
                        description=description,
                        point=point,
                        decimal_odds=averages[outcome].quantize(
                            Decimal(".001"), rounding=ROUND_HALF_UP
                        ),
                        fair_probability=(raw_probabilities[outcome] / overround).quantize(
                            Decimal(".000001"), rounding=ROUND_HALF_UP
                        ),
                        bookmaker_count=len(samples),
                    )
                )
        fixture_id = uuid5(NAMESPACE_URL, f"odds-api-io:event:{event.id}")
        fixture = CanonicalFixture(
            id=fixture_id,
            competition_key=f"oddsapiio:{event.league.slug}",
            competition_name=league.name,
            home_team=event.home,
            away_team=event.away,
            kickoff_at=kickoff,
            source_provider="odds_api_io",
            provider_fixture_id=str(event.id),
            observed_at=observed_at,
        )
        market = MarketOdds(
            provider="odds_api_io",
            event_id=str(event.id),
            observed_at=max(latest_updates) if latest_updates else observed_at,
            bookmaker_count=min(len(home_prices), len(draw_prices), len(away_prices)),
            home_decimal=avg_home.quantize(Decimal(".001"), rounding=ROUND_HALF_UP),
            draw_decimal=avg_draw.quantize(Decimal(".001"), rounding=ROUND_HALF_UP),
            away_decimal=avg_away.quantize(Decimal(".001"), rounding=ROUND_HALF_UP),
            fair_home_probability=fair_home,
            fair_draw_probability=fair_draw,
            fair_away_probability=fair_away,
            quotes=tuple(normalized_quotes),
        )
        return fixture, market

    @staticmethod
    def _market_key(name: str) -> str | None:
        normalized = " ".join(name.casefold().split())
        return {
            "ml": "h2h",
            "moneyline": "h2h",
            "draw no bet": "draw_no_bet",
            "double chance": "double_chance",
            "both teams to score": "btts",
            "totals": "totals",
            "goals over/under": "totals",
            "spread": "spread",
            "asian handicap": "spread",
            "handicap": "spread",
            "odd/even": "odd_even",
            "odd even": "odd_even",
            "ml ht": "first_half_h2h",
            "moneyline ht": "first_half_h2h",
            "1st half ml": "first_half_h2h",
            "1st half moneyline": "first_half_h2h",
            "totals ht": "first_half_totals",
            "goals over/under ht": "first_half_totals",
            "1st half totals": "first_half_totals",
            "1st half goals over/under": "first_half_totals",
            "corners spread": "corners_spread",
            "cards spread": "cards_spread",
        }.get(normalized)

    @staticmethod
    def _outcome_mapping(market_key: str) -> dict[str, str]:
        return {
            "h2h": {"home": "home", "draw": "draw", "away": "away"},
            "draw_no_bet": {"home": "home", "away": "away"},
            "double_chance": {
                "1X": "1x",
                "12": "12",
                "X2": "x2",
                "1x": "1x",
                "x2": "x2",
            },
            "btts": {"yes": "yes", "no": "no"},
            "totals": {"over": "over", "under": "under"},
            "spread": {"home": "home", "away": "away"},
            "odd_even": {"odd": "odd", "even": "even"},
            "first_half_h2h": {"home": "home", "draw": "draw", "away": "away"},
            "first_half_totals": {"over": "over", "under": "under"},
            "corners_spread": {"home": "home", "away": "away"},
            "cards_spread": {"home": "home", "away": "away"},
        }.get(market_key, {})

    @staticmethod
    def _required_outcomes(market_key: str) -> tuple[str, ...] | None:
        return {
            "h2h": ("home", "draw", "away"),
            "draw_no_bet": ("home", "away"),
            "double_chance": ("1x", "12", "x2"),
            "btts": ("yes", "no"),
            "totals": ("over", "under"),
            "spread": ("home", "away"),
            "odd_even": ("odd", "even"),
            "first_half_h2h": ("home", "draw", "away"),
            "first_half_totals": ("over", "under"),
            "corners_spread": ("home", "away"),
            "cards_spread": ("home", "away"),
        }.get(market_key)

    @staticmethod
    def _market_label(market_key: str) -> str:
        return {
            "h2h": "Maç sonucu",
            "draw_no_bet": "Beraberlikte iade",
            "double_chance": "Çifte şans",
            "btts": "Karşılıklı gol",
            "totals": "Toplam gol",
            "spread": "Handikap",
            "odd_even": "Tek/Çift gol",
            "first_half_h2h": "İlk yarı sonucu",
            "first_half_totals": "İlk yarı toplam gol",
            "corners_spread": "Korner handikap",
            "cards_spread": "Kart handikap",
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
            "1x": "Ev sahibi veya beraberlik",
            "12": "Ev sahibi veya deplasman",
            "x2": "Beraberlik veya deplasman",
            "odd": "Tek",
            "even": "Çift",
        }[outcome]

    @staticmethod
    def _parse_datetime(raw: object, default: datetime) -> datetime:
        if not isinstance(raw, str):
            return default
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return default
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @staticmethod
    def _decimal(raw: object) -> Decimal | None:
        if raw is None:
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _int_score(raw: object) -> int | None:
        try:
            return int(str(raw))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _league_slug_for_fixture(fixture: CanonicalFixture) -> str | None:
        if fixture.competition_key.startswith("oddsapiio:"):
            return fixture.competition_key.split(":", 1)[1]
        league = next(
            (item for item in TOP_LEAGUES if item.key in fixture.competition_key),
            None,
        )
        if league is None:
            return None
        return ODDS_API_IO_LEAGUE_SLUGS.get(league.key)
