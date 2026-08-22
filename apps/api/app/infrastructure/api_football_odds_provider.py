import asyncio
import re
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.domain.auto_coupon import TOP_LEAGUES, MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture, TriageFactors

API_FOOTBALL_LEAGUES = {
    "epl": 39,
    "laliga": 140,
    "bundesliga": 78,
    "serie_a": 135,
    "ligue_1": 61,
    "eredivisie": 88,
    "primeira": 94,
    "super_lig": 203,
}


class ApiFootballOddsProvider:
    """Quota-aware pre-match bookmaker adapter for the eight approved leagues."""

    source_name = "api_football"
    supported_market_keys: tuple[str, ...] = (
        "h2h",
        "draw_no_bet",
        "btts",
        "totals",
        "team_totals",
    )

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        refresh_seconds: int,
        requests_per_minute: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._refresh_interval = timedelta(seconds=refresh_seconds)
        self._request_interval = 60.0 / float(requests_per_minute)
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(25.0, connect=5.0),
            headers={
                "x-apisports-key": api_key,
                "User-Agent": "MIRON-BABA-AI/0.1 quota-aware-odds-reader",
            },
        )
        self._owns_client = client is None
        self._rate_lock = asyncio.Lock()
        self._refresh_lock = asyncio.Lock()
        self._next_request_at = 0.0
        self._fixtures: dict[UUID, CanonicalFixture] = {}
        self._markets: dict[UUID, MarketOdds] = {}
        self._last_window: tuple[date, date] | None = None
        self.observed_at: datetime | None = None

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]:
        await self._refresh(start_utc, end_utc)
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
        await self._refresh(start_utc or now, end_utc or now + timedelta(days=1))
        needle = " ".join(query.casefold().split())
        return tuple(
            fixture
            for fixture in self._fixtures.values()
            if len(needle) >= 2
            and needle
            in f"{fixture.home_team} {fixture.away_team} {fixture.competition_name}".casefold()
            and (start_utc is None or fixture.kickoff_at >= start_utc)
            and (end_utc is None or fixture.kickoff_at < end_utc)
        )

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = self._fixtures.get(fixture_id)
        if fixture is None:
            raise KeyError(str(fixture_id))
        return fixture

    async def market_for(self, fixture_id: UUID) -> MarketOdds | None:
        return self._markets.get(fixture_id)

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds:
        market = self._markets.get(fixture_id)
        if market is None:
            raise KeyError(str(fixture_id))
        return market

    async def refresh_result(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = await self.get_fixture(fixture_id)
        if fixture.provider_fixture_id is None:
            return fixture
        records, _ = await self._fetch("/fixtures", {"id": fixture.provider_fixture_id})
        if not records:
            return fixture
        record = records[0]
        fixture_data = self._mapping(record, "fixture")
        goals = self._mapping(record, "goals")
        status = self._mapping(fixture_data, "status")
        short = str(status.get("short", ""))
        if short not in {"FT", "AET", "PEN"}:
            return fixture
        updated = fixture.model_copy(
            update={
                "status": "finished",
                "home_score": self._optional_int(goals.get("home")),
                "away_score": self._optional_int(goals.get("away")),
                "observed_at": datetime.now(UTC),
            }
        )
        self._fixtures[fixture_id] = updated
        return updated

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        market = self._markets.get(fixture.id)
        if market is None:
            raise KeyError(str(fixture.id))
        freshness = (
            Decimal(".98")
            if datetime.now(UTC) - market.observed_at <= timedelta(minutes=15)
            else Decimal(".60")
        )
        return TriageFactors(
            coverage_score=Decimal(".95"),
            source_freshness_score=freshness,
            competitive_relevance_score=Decimal(".95"),
            model_information_gain_score=Decimal(".90"),
            market_coverage_score=min(Decimal("1"), Decimal(market.bookmaker_count) / Decimal("8")),
            lineup_uncertainty_resolvability=Decimal(".70"),
            user_interest_score=Decimal(".92"),
            historical_case_support=Decimal(".55"),
            kickoff_time_practicality=Decimal(".90"),
            estimated_cost_penalty=Decimal(".10"),
            unresolved_identity_penalty=Decimal("0"),
            stale_data_penalty=Decimal("0") if freshness > Decimal(".8") else Decimal(".3"),
        )

    async def _refresh(
        self, start_utc: datetime, end_utc: datetime, *, force: bool = False
    ) -> None:
        if not self.available:
            return
        first_day = start_utc.date()
        last_day = min((end_utc - timedelta(microseconds=1)).date(), first_day)
        window = (first_day, last_day)
        async with self._refresh_lock:
            now = datetime.now(UTC)
            if (
                not force
                and self.observed_at is not None
                and self._last_window == window
                and now - self.observed_at < self._refresh_interval
            ):
                return
            season = first_day.year
            responses = await asyncio.gather(
                *(
                    self._fetch(
                        "/odds",
                        {
                            "league": league_id,
                            "season": season,
                            "date": first_day.isoformat(),
                            "page": 1,
                        },
                    )
                    for league_id in API_FOOTBALL_LEAGUES.values()
                ),
                return_exceptions=True,
            )
            raw_records: list[tuple[str, dict[str, Any]]] = []
            successful = 0
            for league_key, response in zip(API_FOOTBALL_LEAGUES, responses, strict=True):
                if isinstance(response, BaseException):
                    continue
                successful += 1
                records, _ = response
                raw_records.extend((league_key, record) for record in records)
            provider_ids = [
                str(fixture_data["id"])
                for _, record in raw_records
                if isinstance((fixture_data := record.get("fixture")), dict)
                and fixture_data.get("id") is not None
            ]
            detail_responses = await asyncio.gather(
                *(
                    self._fetch("/fixtures", {"ids": "-".join(provider_ids[index : index + 20])})
                    for index in range(0, len(provider_ids), 20)
                ),
                return_exceptions=True,
            )
            fixture_details: dict[str, dict[str, Any]] = {}
            for response in detail_responses:
                if isinstance(response, BaseException):
                    continue
                records, _ = response
                for detail in records:
                    detail_fixture = detail.get("fixture")
                    if isinstance(detail_fixture, dict) and detail_fixture.get("id") is not None:
                        fixture_details[str(detail_fixture["id"])] = detail
            fixtures: dict[UUID, CanonicalFixture] = {}
            markets: dict[UUID, MarketOdds] = {}
            for league_key, record in raw_records:
                odds_fixture = record.get("fixture")
                provider_id = str(odds_fixture.get("id")) if isinstance(odds_fixture, dict) else ""
                fixture_detail_record = fixture_details.get(provider_id)
                if fixture_detail_record is None:
                    continue
                normalized = self._normalize_record(record, fixture_detail_record, league_key, now)
                if normalized is None:
                    continue
                fixture, market = normalized
                fixtures[fixture.id] = fixture
                markets[fixture.id] = market
            if successful == 0:
                if self._fixtures:
                    return
                raise RuntimeError("API_FOOTBALL_ODDS_UNAVAILABLE")
            self._fixtures = fixtures
            self._markets = markets
            self._last_window = window
            self.observed_at = now

    async def _fetch(
        self, endpoint: str, params: dict[str, str | int]
    ) -> tuple[tuple[dict[str, Any], ...], int]:
        async with self._rate_lock:
            loop = asyncio.get_running_loop()
            wait_seconds = self._next_request_at - loop.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_request_at = loop.time() + self._request_interval
            response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("errors"):
            raise ValueError("API_FOOTBALL_ODDS_INVALID_RESPONSE")
        records = payload.get("response")
        paging = payload.get("paging", {})
        if not isinstance(records, list) or not isinstance(paging, dict):
            raise ValueError("API_FOOTBALL_ODDS_INVALID_RESPONSE")
        return tuple(item for item in records if isinstance(item, dict)), int(
            paging.get("total") or 1
        )

    @classmethod
    def _normalize_record(
        cls,
        record: dict[str, Any],
        fixture_detail: dict[str, Any],
        league_key: str,
        fallback_observed_at: datetime,
    ) -> tuple[CanonicalFixture, MarketOdds] | None:
        fixture_data = cls._mapping(record, "fixture")
        detail_fixture = cls._mapping(fixture_detail, "fixture")
        teams = cls._mapping(fixture_detail, "teams")
        home = cls._mapping(teams, "home")
        away = cls._mapping(teams, "away")
        league_data = cls._mapping(record, "league")
        fixture_id_raw = fixture_data.get("id")
        kickoff_raw = detail_fixture.get("date") or fixture_data.get("date")
        if fixture_id_raw is None or not isinstance(kickoff_raw, str):
            return None
        kickoff = datetime.fromisoformat(kickoff_raw.replace("Z", "+00:00"))
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)
        if kickoff <= fallback_observed_at:
            return None
        observed_at = cls._parse_datetime(record.get("update")) or fallback_observed_at
        home_team = str(home.get("name") or "").strip()
        away_team = str(away.get("name") or "").strip()
        if not home_team or not away_team:
            return None
        quote_groups: dict[
            tuple[str, str | None, Decimal | None],
            dict[str, list[Decimal]],
        ] = {}
        bookmakers = record.get("bookmakers")
        if not isinstance(bookmakers, list):
            return None
        for bookmaker in bookmakers:
            if not isinstance(bookmaker, dict):
                continue
            bets = bookmaker.get("bets")
            if not isinstance(bets, list):
                continue
            for bet in bets:
                if not isinstance(bet, dict):
                    continue
                normalized_bet = cls._market_key(str(bet.get("name") or ""))
                if normalized_bet is None:
                    continue
                market_key, description = normalized_bet
                if description == "home":
                    description = home_team
                elif description == "away":
                    description = away_team
                values = bet.get("values")
                if not isinstance(values, list):
                    continue
                for value in values:
                    if not isinstance(value, dict):
                        continue
                    parsed = cls._parse_outcome(
                        market_key, str(value.get("value") or ""), home_team, away_team
                    )
                    if parsed is None:
                        continue
                    outcome, point = parsed
                    try:
                        price = Decimal(str(value.get("odd")))
                    except (InvalidOperation, TypeError):
                        continue
                    if price <= 1:
                        continue
                    quote_groups.setdefault((market_key, description, point), {}).setdefault(
                        outcome, []
                    ).append(price)
        quotes: list[MarketQuote] = []
        for (market_key, description, point), outcomes in quote_groups.items():
            required = cls._required_outcomes(market_key)
            if required is None or not all(outcome in outcomes for outcome in required):
                continue
            averages = {
                outcome: sum(outcomes[outcome], Decimal("0")) / len(outcomes[outcome])
                for outcome in required
            }
            raw = {outcome: Decimal("1") / averages[outcome] for outcome in required}
            overround = sum(raw.values(), Decimal("0"))
            for outcome in required:
                quotes.append(
                    MarketQuote(
                        provider="api_football",
                        observed_at=observed_at,
                        market_key=market_key,
                        market_label=cls._market_label(market_key),
                        outcome_key=outcome,
                        outcome_label=cls._outcome_label(outcome),
                        description=description,
                        point=point,
                        decimal_odds=averages[outcome].quantize(
                            Decimal(".001"), rounding=ROUND_HALF_UP
                        ),
                        fair_probability=(raw[outcome] / overround).quantize(
                            Decimal(".000001"), rounding=ROUND_HALF_UP
                        ),
                        bookmaker_count=len(outcomes[outcome]),
                    )
                )
        h2h = [item for item in quotes if item.market_key == "h2h"]
        prices = {item.outcome_key: item.decimal_odds for item in h2h}
        fair = {item.outcome_key: item.fair_probability for item in h2h}
        if not all(key in prices for key in ("home", "draw", "away")):
            return None
        policy = next(item for item in TOP_LEAGUES if item.key == league_key)
        canonical_id = uuid5(NAMESPACE_URL, f"api-football:event:{fixture_id_raw}")
        fixture = CanonicalFixture(
            id=canonical_id,
            competition_key=f"api-football:{league_key}:{league_data.get('id')}",
            competition_name=policy.name,
            home_team=home_team,
            away_team=away_team,
            kickoff_at=kickoff,
            source_provider="api_football",
            provider_fixture_id=str(fixture_id_raw),
            venue_name=(
                str(venue.get("name"))
                if isinstance((venue := detail_fixture.get("venue")), dict) and venue.get("name")
                else None
            ),
            observed_at=observed_at,
        )
        market = MarketOdds(
            provider="api_football",
            event_id=str(fixture_id_raw),
            observed_at=observed_at,
            bookmaker_count=max(item.bookmaker_count for item in h2h),
            home_decimal=prices["home"],
            draw_decimal=prices["draw"],
            away_decimal=prices["away"],
            fair_home_probability=fair["home"],
            fair_draw_probability=fair["draw"],
            fair_away_probability=Decimal("1") - fair["home"] - fair["draw"],
            quotes=tuple(quotes),
        )
        return fixture, market

    @staticmethod
    def _market_key(name: str) -> tuple[str, str | None] | None:
        normalized = " ".join(name.casefold().split())
        aliases = {
            "match winner": ("h2h", None),
            "draw no bet": ("draw_no_bet", None),
            "both teams score": ("btts", None),
            "both teams to score": ("btts", None),
            "goals over/under": ("totals", None),
            "over/under": ("totals", None),
            "home team total goals": ("team_totals", "home"),
            "away team total goals": ("team_totals", "away"),
        }
        return aliases.get(normalized)

    @staticmethod
    def _parse_outcome(
        market_key: str, value: str, home_team: str, away_team: str
    ) -> tuple[str, Decimal | None] | None:
        normalized = " ".join(value.casefold().split())
        aliases = {
            "home": "home",
            home_team.casefold(): "home",
            "draw": "draw",
            "away": "away",
            away_team.casefold(): "away",
            "yes": "yes",
            "no": "no",
        }
        direct = aliases.get(normalized)
        if direct is not None:
            return direct, None
        match = re.fullmatch(r"(over|under)\s+([0-9]+(?:\.[0-9]+)?)", normalized)
        if match is None or market_key not in {"totals", "team_totals"}:
            return None
        return match.group(1), Decimal(match.group(2))

    @staticmethod
    def _required_outcomes(market_key: str) -> tuple[str, ...] | None:
        return {
            "h2h": ("home", "draw", "away"),
            "draw_no_bet": ("home", "away"),
            "btts": ("yes", "no"),
            "totals": ("over", "under"),
            "team_totals": ("over", "under"),
        }.get(market_key)

    @staticmethod
    def _market_label(market_key: str) -> str:
        return {
            "h2h": "Maç sonucu",
            "draw_no_bet": "Beraberlikte iade",
            "btts": "Karşılıklı gol",
            "totals": "Toplam gol",
            "team_totals": "Takım toplam gol",
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

    @staticmethod
    def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
        item = value.get(key)
        if not isinstance(item, dict):
            raise ValueError("API_FOOTBALL_ODDS_INVALID_RESPONSE")
        return item

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed

    @staticmethod
    def _optional_int(value: object) -> int | None:
        return int(value) if isinstance(value, int | str) and str(value).isdigit() else None
