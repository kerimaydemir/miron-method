import hashlib
import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.application.analysis_runs import AnalysisRunService
from app.application.gemini_coupon_funnel import GeminiCouponFunnel
from app.application.post_match import PostMatchService
from app.domain.analysis import FinalForecast
from app.domain.auto_coupon import (
    AutoCandidate,
    AutoCouponPerformance,
    AutoCouponReadiness,
    AutoCouponRun,
    CouponSelection,
    CouponTicket,
    DecisionRationale,
    FunnelDecision,
    MarketOdds,
    MarketQuote,
    Pick,
    league_for_fixture,
)
from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.domain.post_match import MatchResult, result_outcome
from app.domain.scoring import worthwhile_score
from app.infrastructure.auto_coupon_repository import AutoCouponRepository
from app.infrastructure.composite_fixture_provider import CompositeAnalysisFixtureProvider

BIG_CLUB_MARKERS = (
    "arsenal",
    "chelsea",
    "liverpool",
    "manchester",
    "tottenham",
    "real madrid",
    "barcelona",
    "atletico",
    "bayern",
    "dortmund",
    "leverkusen",
    "inter",
    "milan",
    "juventus",
    "napoli",
    "paris saint",
    "marseille",
    "ajax",
    "psv",
    "benfica",
    "porto",
    "sporting",
    "galatasaray",
    "fenerbahce",
    "fenerbahçe",
    "besiktas",
    "beşiktaş",
)

# Publish only selections that clear the user's explicit value gate. There is
# deliberately no maximum price: a 2.40+ quote remains eligible when the
# independently produced probability and margin-free market comparison agree.
MIN_SELECTION_PROBABILITY = Decimal(".70")
MIN_SELECTION_DECIMAL_ODDS = Decimal("1.80")


class FixtureSelectionProvider(Protocol):
    async def list_fixtures(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        competition_ids: Sequence[str],
    ) -> tuple[CanonicalFixture, ...]: ...

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors: ...


class OddsSelectionProvider(FixtureSelectionProvider, Protocol):
    source_name: str
    supported_market_keys: tuple[str, ...]

    @property
    def available(self) -> bool: ...

    async def list_market_fixtures(
        self, *, start_utc: datetime, end_utc: datetime
    ) -> tuple[tuple[CanonicalFixture, MarketOdds], ...]: ...

    async def wide_market_for(self, fixture_id: UUID) -> MarketOdds: ...


class AutoCouponService:
    def __init__(
        self,
        *,
        fixtures: FixtureSelectionProvider,
        analysis_fixtures: CompositeAnalysisFixtureProvider,
        odds: OddsSelectionProvider,
        analysis: AnalysisRunService,
        post_match: PostMatchService,
        repository: AutoCouponRepository,
        funnel: GeminiCouponFunnel | None,
        live_fixtures_available: bool,
        window_days: int,
        reuse_seconds: int,
    ) -> None:
        self._fixtures = fixtures
        self._analysis_fixtures = analysis_fixtures
        self._odds = odds
        self._analysis = analysis
        self._post_match = post_match
        self._repository = repository
        self._funnel = funnel
        self._live_fixtures_available = live_fixtures_available
        self._window_days = window_days
        self._reuse_interval = timedelta(seconds=reuse_seconds)

    async def create(self, *, idempotency_key: str) -> AutoCouponRun:
        if not self._odds.available:
            raise ValueError("AUTO_COUPON_LIVE_MARKET_REQUIRED")
        if self._funnel is None:
            raise ValueError("AUTO_COUPON_GEMINI_REQUIRED")
        if not self._analysis.deep_data_ready:
            raise ValueError("AUTO_COUPON_DEEP_DATA_REQUIRED")
        if not self._analysis.deep_analysis_ready:
            raise ValueError("AUTO_COUPON_DEEP_ANALYSIS_NOT_READY")
        run_id = uuid5(NAMESPACE_URL, f"miron-baba-ai:auto-coupon:{idempotency_key}")
        existing = self._repository.load(run_id)
        if existing is not None:
            return existing
        now = datetime.now(UTC)
        latest = self._repository.latest()
        if latest is not None and self._is_reusable(latest, now):
            return latest
        end = now + timedelta(days=self._window_days)
        market_pairs = await self._odds.list_market_fixtures(start_utc=now, end_utc=end)
        markets = {fixture.id: market for fixture, market in market_pairs}
        fixtures = tuple(fixture for fixture, _ in market_pairs)
        if not fixtures:
            raise ValueError("AUTO_COUPON_NO_CURRENT_LIVE_MARKETS")
        memory_context = self._repository.memory_context("", limit=20)
        candidates = await self._rank_candidates(fixtures, markets, memory_context)
        initial = candidates[:10]
        if not initial:
            raise ValueError("AUTO_COUPON_NO_CURRENT_TOP_LEAGUE_FIXTURES")
        rough, critic, funnel_cost = await self._funnel.select(initial, memory_context)

        by_id = {item.fixture.id: item for item in initial}
        selections: list[CouponSelection] = []
        analysis_cost = Decimal("0")
        for fixture_id in critic.selected_fixture_ids:
            candidate = by_id[fixture_id]
            market = await self._odds.wide_market_for(fixture_id)
            analysis_key = f"auto-{run_id.hex[:16]}-{fixture_id.hex[:16]}"
            analysis_run = await self._analysis.start(
                fixture_id,
                analysis_key,
                hashlib.sha256(str(fixture_id).encode()).hexdigest(),
                uuid5(NAMESPACE_URL, f"auto-correlation:{run_id}:{fixture_id}"),
            )
            locked = await self._analysis.lock(analysis_run.run_id)
            if locked.lock_id is None:
                raise RuntimeError("AUTO_COUPON_LOCK_REQUIRED")
            best = self._best_market_selection(market, locked.forecast, candidate.fixture, now)
            if best is None:
                continue
            quote, model_probability, edge, value_score = best
            pick: Pick = self._pick_key(quote)
            model_fair_odds = (Decimal("1") / model_probability).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )
            selections.append(
                CouponSelection(
                    fixture=candidate.fixture,
                    league=candidate.league,
                    analysis_run_id=locked.run_id,
                    lock_id=locked.lock_id,
                    pick=pick,
                    market_key=quote.market_key,
                    market_label=quote.market_label,
                    outcome_label=self._selection_label(quote),
                    market_description=quote.description,
                    line=quote.point,
                    probability=model_probability,
                    model_fair_odds=model_fair_odds,
                    market_decimal_odds=quote.decimal_odds,
                    market_fair_probability=quote.fair_probability,
                    edge=edge,
                    bookmaker_count=quote.bookmaker_count,
                    price_observed_at=quote.observed_at,
                    confidence=locked.forecast.confidence,
                    value_score=value_score,
                    reason=(
                        f"{quote.market_label} / {self._selection_label(quote)} için model "
                        f"olasılığı %{(model_probability * 100).quantize(Decimal('.1'))}; "
                        f"marjı temizlenmiş piyasa %{(quote.fair_probability * 100).quantize(Decimal('.1'))}."
                    ),
                    uncertainty=locked.forecast.uncertainty_drivers[0],
                    rationale=DecisionRationale(
                        market_thesis=(
                            f"{quote.market_label} pazarında {self._selection_label(quote)} "
                            f"seçimi model ve piyasa arasında ölçülebilir değer farkı taşıyor."
                        ),
                        supporting_evidence=tuple(locked.forecast.decisive_evidence),
                        counter_evidence=tuple(locked.forecast.uncertainty_drivers),
                        price_rationale=(
                            f"Kilit anı oranı {quote.decimal_odds}; model olasılığı "
                            f"%{(model_probability * 100).quantize(Decimal('.1'))}, marjı "
                            f"temizlenmiş piyasa olasılığı "
                            f"%{(quote.fair_probability * 100).quantize(Decimal('.1'))}."
                        ),
                        invalidation_conditions=(
                            "Kilit sonrası ilk 11 veya kilit oyuncu durumu anlamlı değişirse",
                            "Oran kayması hesaplanan değeri sıfırın altına indirirse",
                            "Kaynak verisi sonradan düzeltme veya kimlik uyuşmazlığı gösterirse",
                        ),
                        model_disagreement=(
                            "Model-piyasa farkı "
                            f"%{(edge * 100).quantize(Decimal('.1'))}; tek maçta nedensel "
                            "doğruluk kanıtı sayılmaz."
                        ),
                        evidence_cutoff_at=locked.forecast.cutoff_at,
                    ),
                )
            )
            analysis_cost += locked.actual_cost_usd

        ordered = tuple(
            sorted(
                selections,
                key=lambda item: (item.value_score, item.probability),
                reverse=True,
            )
        )
        auto_run = AutoCouponRun(
            run_id=run_id,
            state="completed",
            source_mode="bookmaker_live",
            observed_at=now,
            covered_league_keys=tuple(dict.fromkeys(item.league.key for item in initial)),
            initial_candidates=initial,
            rough_decision=rough,
            critic_decision=critic,
            selections=ordered,
            tickets=self._tickets(ordered),
            rag_case_count=len(memory_context),
            actual_cost_usd=(funnel_cost + analysis_cost).quantize(
                Decimal(".000001"), rounding=ROUND_HALF_UP
            ),
            notice=(
                "Bugün kanıt, fiyat ve belirsizlik eşiklerini birlikte geçen seçim yok; "
                "sistem kota doldurmak için kupon üretmedi."
                if not ordered
                else "Olasılıksal seçimdir; kesinlik veya bahis tavsiyesi değildir."
            ),
        )
        self._repository.save(auto_run)
        return auto_run

    def _is_reusable(self, run: AutoCouponRun, now: datetime) -> bool:
        return (
            run.state == "completed"
            and run.source_mode == "bookmaker_live"
            and now - run.observed_at <= self._reuse_interval
            and bool(run.selections)
            and all(
                item.settlement_status == "pending"
                and item.fixture.kickoff_at > now
                and item.market_decimal_odds is not None
                for item in run.selections
            )
        )

    def readiness(self) -> AutoCouponReadiness:
        bookmaker_ready = self._odds.available
        gemini_ready = self._funnel is not None
        deep_data_ready = self._analysis.deep_data_ready
        deep_ready = self._analysis.deep_analysis_ready
        blockers: list[str] = []
        if not bookmaker_ready:
            blockers.append("AUTO_COUPON_LIVE_MARKET_REQUIRED")
        if not gemini_ready:
            blockers.append("AUTO_COUPON_GEMINI_REQUIRED")
        if not deep_data_ready:
            blockers.append("AUTO_COUPON_DEEP_DATA_REQUIRED")
        if not deep_ready:
            blockers.append("AUTO_COUPON_DEEP_ANALYSIS_NOT_READY")
        return AutoCouponReadiness(
            ready=not blockers,
            live_fixtures=self._live_fixtures_available,
            live_bookmaker_odds=bookmaker_ready,
            gemini_analysis=gemini_ready,
            deep_structured_data=deep_data_ready,
            deep_analysis_ready=deep_ready,
            implemented_analysis_stages=self._analysis.implemented_stage_ids,
            required_analysis_stages=self._analysis.required_deep_stage_ids,
            supported_market_keys=self._odds.supported_market_keys,
            blockers=tuple(blockers),
            notice=self._readiness_notice(
                bookmaker_ready, gemini_ready, deep_data_ready, deep_ready
            ),
        )

    @staticmethod
    def _readiness_notice(
        bookmaker_ready: bool,
        gemini_ready: bool,
        deep_data_ready: bool,
        deep_ready: bool,
    ) -> str:
        if not bookmaker_ready:
            return (
                "Canlı fikstür ve derin analiz hazır; canlı bookmaker oranı olmadan "
                "otomatik kupon üretilmez."
            )
        if not gemini_ready:
            return "Gemini analiz rotası kapalı; analiz veya kupon üretilmez."
        if not deep_data_ready:
            return (
                "API-Football derin veri bağlantısı yok; kadro, form, istatistik, sakatlık, "
                "H2H ve teknik direktör kanıtı olmadan kupon üretilmez."
            )
        if not deep_ready:
            return (
                "Derin veri bağlı fakat 30 aşamalı Gemini kanıt zinciri eksik; "
                "tamamlanmadan kupon üretilmez."
            )
        return "Canlı bookmaker verisi ve derin analiz aşamaları hazır."

    def get(self, run_id: UUID) -> AutoCouponRun:
        run = self._repository.load(run_id)
        if run is None:
            raise KeyError("AUTO_COUPON_NOT_FOUND")
        if run.source_mode != "bookmaker_live" or any(
            item.market_decimal_odds is None for item in run.selections
        ):
            return run.model_copy(
                update={
                    "selections": (),
                    "tickets": (),
                    "notice": (
                        "Bu eski çalışma gerçek bookmaker oranı içermediği için geçersiz sayıldı; "
                        "seçim ve kuponlar gösterilmiyor."
                    ),
                }
            )
        return run

    def performance(self) -> AutoCouponPerformance:
        return self._repository.performance()

    async def settle_pending(self, run_id: UUID | None = None) -> int:
        settled = 0
        for pending in self._repository.list_pending():
            if run_id is not None and pending.auto_run_id != run_id:
                continue
            try:
                fixture = await self._analysis_fixtures.refresh_result(pending.fixture_id)
            except (KeyError, RuntimeError, httpx.HTTPError):
                continue
            if (
                fixture.status != "finished"
                or fixture.home_score is None
                or fixture.away_score is None
            ):
                continue
            try:
                lock = self._analysis.get_lock(pending.lock_id)
            except KeyError:
                continue
            autopsy = self._post_match.ingest(
                lock,
                MatchResult(
                    fixture_id=fixture.id,
                    home_score=fixture.home_score,
                    away_score=fixture.away_score,
                    observed_at=fixture.observed_at or datetime.now(UTC),
                    source=fixture.source_provider,
                ),
            )
            actual = result_outcome(autopsy.result)
            settlement_status = self._settlement_status(pending.pick, fixture, actual)
            self._repository.mark_settled(
                auto_run_id=pending.auto_run_id,
                fixture_id=pending.fixture_id,
                status=settlement_status,
                autopsy_id=autopsy.autopsy_id,
                home_score=fixture.home_score,
                away_score=fixture.away_score,
                post_match={
                    "autopsy_id": str(autopsy.autopsy_id),
                    "result_verdict": autopsy.result_verdict,
                    "process_verdict": autopsy.process_verdict,
                    "predicted_outcome": autopsy.predicted_outcome,
                    "realized_outcome": autopsy.realized_outcome,
                    "brier_score": str(autopsy.brier_score),
                    "explanation": autopsy.post_match_explanation,
                    "variance": [item.model_dump(mode="json") for item in autopsy.variance],
                    "lesson": autopsy.lesson.model_dump(mode="json"),
                },
            )
            settled += 1
        return settled

    @staticmethod
    def _settlement_status(pick: str, fixture: CanonicalFixture, actual_result: str) -> str:
        if pick in ("home", "draw", "away"):
            return "won" if pick == actual_result else "lost"
        parts = pick.split(":", maxsplit=3)
        if len(parts) != 4 or fixture.home_score is None or fixture.away_score is None:
            return "void"
        market_key, description, outcome, raw_line = parts
        if market_key == "h2h":
            return "won" if outcome == actual_result else "lost"
        if market_key == "draw_no_bet":
            if actual_result == "draw":
                return "void"
            return "won" if outcome == actual_result else "lost"
        if market_key == "btts":
            realized = "yes" if fixture.home_score > 0 and fixture.away_score > 0 else "no"
            return "won" if outcome == realized else "lost"
        try:
            line = Decimal(raw_line)
        except (InvalidOperation, ValueError):
            return "void"
        if market_key in ("totals", "alternate_totals"):
            goals = Decimal(fixture.home_score + fixture.away_score)
        elif market_key in ("team_totals", "alternate_team_totals"):
            if description.casefold() == fixture.home_team.casefold():
                goals = Decimal(fixture.home_score)
            elif description.casefold() == fixture.away_team.casefold():
                goals = Decimal(fixture.away_score)
            else:
                return "void"
        else:
            return "void"
        if goals == line:
            return "void"
        realized = "over" if goals > line else "under"
        return "won" if outcome == realized else "lost"

    async def _rank_candidates(
        self,
        fixtures: tuple[CanonicalFixture, ...],
        markets: dict[UUID, MarketOdds],
        memories: tuple[str, ...],
    ) -> tuple[AutoCandidate, ...]:
        items: list[AutoCandidate] = []
        for fixture in fixtures:
            league = league_for_fixture(fixture)
            if league is None:
                continue
            factors = await self._analysis_fixtures.features_for(fixture)
            memory_count = sum(
                1
                for item in memories
                if fixture.home_team.casefold() in item.casefold()
                or fixture.away_team.casefold() in item.casefold()
                or league.name.casefold() in item.casefold()
            )
            market = markets.get(fixture.id)
            team_text = f"{fixture.home_team} {fixture.away_team}".casefold()
            big_club = any(marker in team_text for marker in BIG_CLUB_MARKERS)
            score = int(Decimal(worthwhile_score(factors)) * Decimal(".72"))
            score += league.prestige_weight
            score += 5 if big_club else 0
            score += min(8, market.bookmaker_count) if market is not None else 0
            score += min(3, memory_count)
            positives = [f"{league.name} izin listesinde", "Fikstür güncel"]
            risks: list[str] = []
            if big_club:
                positives.append("Tanınan takım kapsamı")
            if market is not None:
                positives.append(f"{market.bookmaker_count} bookmaker ile taze 1X2 ön taraması")
            else:
                risks.append("Canlı bookmaker oranı yok; aday yayınlanamaz")
            if memory_count:
                positives.append(f"{memory_count} doğrulanmış benzer vaka")
            else:
                risks.append("Doğrulanmış benzer vaka hafızası henüz yok")
            items.append(
                AutoCandidate(
                    fixture=fixture,
                    league=league,
                    auto_score=min(100, score),
                    market_odds=market,
                    memory_case_count=memory_count,
                    positive_factors=tuple(positives),
                    risk_flags=tuple(risks),
                )
            )
        return tuple(sorted(items, key=lambda item: (-item.auto_score, item.fixture.kickoff_at)))

    @staticmethod
    def _deterministic_funnel(
        candidates: tuple[AutoCandidate, ...],
    ) -> tuple[FunnelDecision, FunnelDecision]:
        rough_ids = tuple(item.fixture.id for item in candidates[: min(5, len(candidates))])
        critic_ids = rough_ids[:3]
        all_ids = tuple(item.fixture.id for item in candidates)
        return (
            FunnelDecision(
                stage="rough",
                input_count=len(candidates),
                selected_fixture_ids=rough_ids,
                eliminated_fixture_ids=tuple(item for item in all_ids if item not in rough_ids),
                rationale="Test modunda puan sırası kullanılarak düşük maliyetli ilk eleme yapıldı.",
                model_id="deterministic-test-policy",
            ),
            FunnelDecision(
                stage="critic",
                input_count=len(rough_ids),
                selected_fixture_ids=critic_ids,
                eliminated_fixture_ids=tuple(item for item in rough_ids if item not in critic_ids),
                rationale="Test modunda en yüksek üç puan MİRON BABA analizine geçirildi.",
                model_id="deterministic-test-policy",
            ),
        )

    @staticmethod
    def _market_values(
        market: MarketOdds | None, pick: str
    ) -> tuple[Decimal | None, Decimal | None]:
        if market is None:
            return None, None
        decimal_map = {
            "home": market.home_decimal,
            "draw": market.draw_decimal,
            "away": market.away_decimal,
        }
        fair_map = {
            "home": market.fair_home_probability,
            "draw": market.fair_draw_probability,
            "away": market.fair_away_probability,
        }
        return decimal_map[pick], fair_map[pick]

    @classmethod
    def _best_market_selection(
        cls,
        market: MarketOdds,
        forecast: FinalForecast,
        fixture: CanonicalFixture,
        now: datetime,
    ) -> tuple[MarketQuote, Decimal, Decimal, Decimal] | None:
        candidates: list[tuple[Decimal, MarketQuote, Decimal, Decimal]] = []
        for quote in market.quotes:
            minimum_books = 1 if quote.provider == "rapidapi_football" else 2
            if quote.bookmaker_count < minimum_books or now - quote.observed_at > timedelta(
                minutes=15
            ):
                continue
            probability = cls._model_market_probability(forecast, fixture, quote)
            if probability is None or probability < MIN_SELECTION_PROBABILITY:
                continue
            edge = probability - quote.fair_probability
            minimum_edge = Decimal(".05") if quote.bookmaker_count == 1 else Decimal(".02")
            if edge < minimum_edge:
                continue
            if quote.decimal_odds < MIN_SELECTION_DECIMAL_ODDS:
                continue
            price_quality = min(quote.decimal_odds, Decimal("10")) - MIN_SELECTION_DECIMAL_ODDS
            score = (
                probability * Decimal("55")
                + edge * Decimal("250")
                + forecast.confidence * Decimal("15")
                + price_quality * Decimal("10")
                + min(Decimal(quote.bookmaker_count), Decimal("10"))
            ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
            candidates.append((score, quote, probability, edge))
        if not candidates:
            return None
        score, quote, probability, edge = max(candidates, key=lambda item: item[0])
        return quote, probability, edge, score

    @staticmethod
    def _model_market_probability(
        forecast: FinalForecast, fixture: CanonicalFixture, quote: MarketQuote
    ) -> Decimal | None:
        outcomes = {item.outcome: item.probability for item in forecast.outcome_probabilities}
        home_xg = max(Decimal(".01"), forecast.expected_home_goals)
        away_xg = max(Decimal(".01"), forecast.expected_away_goals)
        if quote.market_key == "h2h":
            if quote.outcome_key not in ("home", "draw", "away"):
                return None
            return outcomes[quote.outcome_key]
        if quote.market_key == "draw_no_bet":
            if quote.outcome_key not in ("home", "away"):
                return None
            non_draw = Decimal("1") - outcomes["draw"]
            return outcomes[quote.outcome_key] / non_draw if non_draw > 0 else None
        if quote.market_key == "btts":
            yes = (Decimal("1") - Decimal(str(math.exp(-float(home_xg))))) * (
                Decimal("1") - Decimal(str(math.exp(-float(away_xg))))
            )
            return yes if quote.outcome_key == "yes" else Decimal("1") - yes
        if quote.market_key in ("totals", "alternate_totals"):
            return AutoCouponService._over_under_probability(
                home_xg + away_xg, quote.point, quote.outcome_key
            )
        if quote.market_key in ("team_totals", "alternate_team_totals"):
            description = (quote.description or "").casefold()
            if description == fixture.home_team.casefold():
                intensity = home_xg
            elif description == fixture.away_team.casefold():
                intensity = away_xg
            else:
                return None
            return AutoCouponService._over_under_probability(
                intensity, quote.point, quote.outcome_key
            )
        return None

    @staticmethod
    def _over_under_probability(
        intensity: Decimal, point: Decimal | None, outcome: str
    ) -> Decimal | None:
        if point is None or outcome not in ("over", "under"):
            return None
        doubled = point * Decimal("2")
        if doubled != doubled.to_integral_value() or int(doubled) % 2 == 0:
            return None
        threshold = math.floor(float(point))
        under = sum(
            (
                Decimal(str(math.exp(-float(intensity))))
                * (intensity**goals)
                / Decimal(math.factorial(goals))
                for goals in range(threshold + 1)
            ),
            Decimal("0"),
        )
        probability = Decimal("1") - under if outcome == "over" else under
        return min(Decimal("1"), max(Decimal("0"), probability))

    @staticmethod
    def _pick_key(quote: MarketQuote) -> str:
        description = (quote.description or "match").replace(":", "-")
        line = str(quote.point) if quote.point is not None else "none"
        return f"{quote.market_key}:{description}:{quote.outcome_key}:{line}"

    @staticmethod
    def _selection_label(quote: MarketQuote) -> str:
        parts = [quote.description, quote.outcome_label]
        if quote.point is not None:
            parts.append(str(quote.point))
        return " ".join(item for item in parts if item)

    @staticmethod
    def _tickets(selections: tuple[CouponSelection, ...]) -> tuple[CouponTicket, ...]:
        groups = (
            ("single", "En güvenli tekli", selections[:1], "düşük", 1),
            ("double", "Dengeli ikili", selections[:2], "orta", 2),
            ("treble", "MİRON BABA üçlüsü", selections[:3], "yüksek", 3),
        )
        tickets: list[CouponTicket] = []
        for kind, label, group, risk, required_count in groups:
            probability = Decimal("1")
            decimal_odds = Decimal("1")
            if len(group) != required_count or any(
                item.market_decimal_odds is None for item in group
            ):
                continue
            for item in group:
                probability *= item.probability
                if item.market_decimal_odds is None:
                    raise ValueError("AUTO_COUPON_LIVE_MARKET_REQUIRED")
                decimal_odds *= item.market_decimal_odds
            if probability < MIN_SELECTION_PROBABILITY or decimal_odds < MIN_SELECTION_DECIMAL_ODDS:
                continue
            tickets.append(
                CouponTicket(
                    kind=kind,
                    label=label,
                    selection_fixture_ids=tuple(item.fixture.id for item in group),
                    combined_probability=probability.quantize(
                        Decimal(".000001"), rounding=ROUND_HALF_UP
                    ),
                    combined_decimal_odds=decimal_odds.quantize(
                        Decimal(".01"), rounding=ROUND_HALF_UP
                    ),
                    odds_source="bookmaker_average",
                    risk_label=risk,
                )
            )
        return tuple(tickets)
