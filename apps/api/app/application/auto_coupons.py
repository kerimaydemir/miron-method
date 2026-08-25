import asyncio
import hashlib
import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Literal, Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.application.analysis_runs import AnalysisRunService
from app.application.gemini_coupon_funnel import GeminiCouponFunnel
from app.application.post_match import PostMatchService
from app.domain.analysis import FinalForecast, OutcomeProbability
from app.domain.auto_coupon import (
    AutoCandidate,
    AutoCouponPerformance,
    AutoCouponReadiness,
    AutoCouponRun,
    CouponSelection,
    CouponTicket,
    DailyPrediction,
    DailyPredictionReviewItem,
    DailyReviewReport,
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

# Publish only tickets that clear the user's explicit value gate. A single
# selection still needs 1.80+ on its own, but two safer legs can form the coupon
# when their combined bookmaker price reaches 1.80+ and their combined model
# probability remains at least 70%.
MIN_SELECTION_PROBABILITY = Decimal(".70")
MIN_SELECTION_DECIMAL_ODDS = Decimal("1.80")
MIN_COMBO_LEG_DECIMAL_ODDS = Decimal("1.20")


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
        finalist_analysis_timeout_seconds: int = 240,
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
        self._finalist_analysis_timeout_seconds = finalist_analysis_timeout_seconds

    async def create(self, *, idempotency_key: str) -> AutoCouponRun:
        if not self._odds.available and (
            self._funnel is None
            or not self._analysis.deep_data_ready
            or not self._analysis.deep_analysis_ready
        ):
            raise ValueError("AUTO_COUPON_LIVE_MARKET_REQUIRED")
        if self._funnel is None:
            raise ValueError("AUTO_COUPON_GEMINI_REQUIRED")
        if not self._analysis.deep_data_ready:
            raise ValueError("AUTO_COUPON_DEEP_DATA_REQUIRED")
        if not self._analysis.deep_analysis_ready:
            raise ValueError("AUTO_COUPON_DEEP_ANALYSIS_NOT_READY")
        run_id = uuid5(NAMESPACE_URL, f"miron-baba-ai:auto-coupon:{idempotency_key}")
        existing = self._repository.load(run_id)
        refresh_existing_journal = existing is not None and not existing.selections
        if existing is not None and not refresh_existing_journal:
            return existing
        now = datetime.now(UTC)
        latest = self._repository.latest()
        if latest is not None and self._is_reusable(latest, now):
            return latest
        end = now + timedelta(days=self._window_days)
        source_mode: Literal["bookmaker_live", "fixture_live_no_odds"] = "bookmaker_live"
        try:
            market_pairs = (
                await asyncio.wait_for(
                    self._odds.list_market_fixtures(start_utc=now, end_utc=end),
                    timeout=60,
                )
                if self._odds.available
                else ()
            )
        except (TimeoutError, httpx.HTTPError, RuntimeError, ValueError):
            market_pairs = ()
        markets = {fixture.id: market for fixture, market in market_pairs}
        fixtures = tuple(fixture for fixture, _ in market_pairs)
        if not fixtures:
            source_mode = "fixture_live_no_odds"
            fixtures = await self._fixtures.list_fixtures(
                start_utc=now, end_utc=end, competition_ids=()
            )
        if not fixtures:
            raise ValueError("AUTO_COUPON_NO_CURRENT_LIVE_MARKETS")
        memory_context = self._repository.memory_context("", limit=20)
        candidates = await self._rank_candidates(fixtures, markets, memory_context)
        initial = candidates[:10]
        if not initial:
            raise ValueError("AUTO_COUPON_NO_CURRENT_TOP_LEAGUE_FIXTURES")
        daily_predictions = self._daily_predictions(run_id, initial, markets, now)
        if markets:
            try:
                rough, critic, funnel_cost = await asyncio.wait_for(
                    self._funnel.select(initial, memory_context), timeout=45
                )
            except (TimeoutError, httpx.HTTPError):
                rough, critic = self._empty_funnel_after_journal(
                    initial,
                    "Gemini eleme çağrısı zamanında tamamlanmadı; günlük jurnal kaydedildi, kupon üretilmedi.",
                )
                funnel_cost = Decimal("0")
        else:
            rough, critic = self._empty_funnel_after_journal(
                initial,
                "Canlı bookmaker oranı alınamadı; günlük fixture jurnali kaydedildi, kupon analizi başlatılmadı.",
            )
            funnel_cost = Decimal("0")

        by_id = {item.fixture.id: item for item in initial}
        if markets and not critic.selected_fixture_ids:
            rough, critic = self._deterministic_funnel_after_empty_gemini(initial, rough, critic)
        selections: list[CouponSelection] = []
        analysis_cost = Decimal("0")
        finalist_analysis_timed_out = False
        for fixture_id in critic.selected_fixture_ids:
            candidate = by_id[fixture_id]
            try:
                market = await asyncio.wait_for(self._odds.wide_market_for(fixture_id), timeout=45)
            except TimeoutError:
                finalist_analysis_timed_out = True
                break
            except (KeyError, httpx.HTTPError, RuntimeError, ValueError):
                continue
            analysis_key = f"auto-{run_id.hex[:16]}-{fixture_id.hex[:16]}"
            try:
                analysis_run = await asyncio.wait_for(
                    self._analysis.start(
                        fixture_id,
                        analysis_key,
                        hashlib.sha256(str(fixture_id).encode()).hexdigest(),
                        uuid5(NAMESPACE_URL, f"auto-correlation:{run_id}:{fixture_id}"),
                    ),
                    timeout=self._finalist_analysis_timeout_seconds,
                )
                locked = await asyncio.wait_for(
                    self._analysis.lock(analysis_run.run_id), timeout=10
                )
            except TimeoutError:
                finalist_analysis_timed_out = True
                break
            except (PermissionError, RuntimeError, ValueError, KeyError, httpx.HTTPError):
                continue
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

        ordered_candidates = tuple(
            sorted(
                selections,
                key=lambda item: (item.value_score, item.probability),
                reverse=True,
            )
        )
        tickets = self._tickets(ordered_candidates)
        ticketed_fixture_ids = {
            fixture_id for ticket in tickets for fixture_id in ticket.selection_fixture_ids
        }
        ordered = tuple(
            item for item in ordered_candidates if item.fixture.id in ticketed_fixture_ids
        )
        auto_run = AutoCouponRun(
            run_id=run_id,
            state="completed",
            source_mode=source_mode,
            observed_at=now,
            covered_league_keys=tuple(dict.fromkeys(item.league.key for item in initial)),
            initial_candidates=initial,
            rough_decision=rough,
            critic_decision=critic,
            daily_predictions=daily_predictions,
            selections=ordered,
            tickets=tickets,
            rag_case_count=len(memory_context),
            actual_cost_usd=(funnel_cost + analysis_cost).quantize(
                Decimal(".000001"), rounding=ROUND_HALF_UP
            ),
            notice=(
                "Bugün canlı bookmaker oranı alınamadı; sistem oran uydurmadı, sadece "
                "büyük lig fixture jurnalini kaydetti."
                if source_mode == "fixture_live_no_odds"
                else "Derin finalist analizi süre sınırına takıldı; günlük jurnal kaydedildi, "
                "kota doldurmak için kör kupon üretilmedi."
                if finalist_analysis_timed_out and not ordered
                else "Bugün kanıt, fiyat ve belirsizlik eşiklerini birlikte geçen seçim yok; "
                "sistem kota doldurmak için kupon üretmedi."
                if not tickets
                else "Olasılıksal seçimdir; kesinlik veya bahis tavsiyesi değildir."
            ),
        )
        if refresh_existing_journal:
            self._repository.update_run(auto_run)
        else:
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
        if run.source_mode == "fixture_live_no_odds":
            return run
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

    def journal(self, *, limit: int = 30) -> tuple[AutoCouponRun, ...]:
        return self._repository.recent(limit)

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

    async def review_daily_predictions(self) -> int:
        reviewed = 0
        now = datetime.now(UTC)
        for run in self._repository.recent(45):
            if not run.daily_predictions:
                continue
            current_reviewed = (
                {item.prediction_id for item in run.post_match_review.items}
                if run.post_match_review is not None
                else set()
            )
            items = list(run.post_match_review.items) if run.post_match_review is not None else []
            for prediction in run.daily_predictions:
                if prediction.prediction_id in current_reviewed:
                    continue
                try:
                    fixture = await self._analysis_fixtures.refresh_result(prediction.fixture.id)
                except (KeyError, RuntimeError, httpx.HTTPError):
                    continue
                if (
                    fixture.status != "finished"
                    or fixture.home_score is None
                    or fixture.away_score is None
                ):
                    continue
                actual = result_outcome(
                    MatchResult(
                        fixture_id=fixture.id,
                        home_score=fixture.home_score,
                        away_score=fixture.away_score,
                        observed_at=fixture.observed_at or now,
                        source=fixture.source_provider,
                    )
                )
                status = self._settlement_status(prediction.pick, fixture, actual)
                review_item = self._daily_review_item(prediction, fixture, status)
                items.append(review_item)
                reviewed += 1
            if items:
                report = self._daily_review_report(run, tuple(items), now)
                state = (
                    "settled"
                    if len(items) == len(run.daily_predictions)
                    and all(item.settlement_status != "pending" for item in run.selections)
                    else run.state
                )
                self._repository.update_run(
                    run.model_copy(update={"post_match_review": report, "state": state})
                )
        return reviewed

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
        if market_key == "double_chance":
            covered = {
                "1x": {"home", "draw"},
                "12": {"home", "away"},
                "x2": {"draw", "away"},
            }.get(outcome)
            return "won" if covered is not None and actual_result in covered else "lost"
        if market_key == "btts":
            realized = "yes" if fixture.home_score > 0 and fixture.away_score > 0 else "no"
            return "won" if outcome == realized else "lost"
        if market_key == "odd_even":
            realized = "even" if (fixture.home_score + fixture.away_score) % 2 == 0 else "odd"
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
        elif market_key == "spread":
            if outcome == "home":
                adjusted_margin = Decimal(fixture.home_score - fixture.away_score) + line
            elif outcome == "away":
                adjusted_margin = Decimal(fixture.away_score - fixture.home_score) - line
            else:
                return "void"
            if adjusted_margin == 0:
                return "void"
            return "won" if adjusted_margin > 0 else "lost"
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
                risks.append("Canlı bookmaker oranı yok; aday kupon olarak yayınlanamaz")
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

    @classmethod
    def _daily_predictions(
        cls,
        run_id: UUID,
        candidates: tuple[AutoCandidate, ...],
        markets: dict[UUID, MarketOdds],
        now: datetime,
    ) -> tuple[DailyPrediction, ...]:
        predictions: list[DailyPrediction] = []
        for candidate in candidates:
            market = markets.get(candidate.fixture.id)
            quote = cls._journal_quote(candidate, market, now) if market is not None else None
            if quote is not None:
                probability = cls._journal_probability(candidate, quote)
                score = cls._journal_score(candidate, quote, probability)
                tier: Literal["journal_only", "watchlist", "coupon_candidate"] = (
                    "coupon_candidate"
                    if probability >= MIN_SELECTION_PROBABILITY
                    and quote.decimal_odds >= MIN_COMBO_LEG_DECIMAL_ODDS
                    else "watchlist"
                    if probability >= Decimal(".58") and quote.decimal_odds >= Decimal("1.45")
                    else "journal_only"
                )
                pick = cls._pick_key(quote)
                market_key = quote.market_key
                market_label = quote.market_label
                outcome_label = cls._selection_label(quote)
                market_description = quote.description
                line = quote.point
                market_decimal_odds = quote.decimal_odds
                market_fair_probability = quote.fair_probability
                bookmaker_count = quote.bookmaker_count
                confidence = cls._journal_confidence(candidate, quote)
                observed_at = quote.observed_at
                price_reason = (
                    f"{quote.bookmaker_count} bookmaker ortalaması {quote.decimal_odds} oran ve "
                    f"%{(quote.fair_probability * 100).quantize(Decimal('.1'))} marj temizlenmiş piyasa olasılığı veriyor."
                )
                price_risk = "Bookmaker piyasası tek başına gerçek sebep kanıtı değildir."
            else:
                probability = cls._fixture_only_probability(candidate)
                score = cls._fixture_only_score(candidate, probability)
                tier = "journal_only"
                pick = "watch"
                market_key = "h2h"
                market_label = "Oran bekleniyor"
                outcome_label = "Kupon kilidi yok"
                market_description = None
                line = None
                market_decimal_odds = None
                market_fair_probability = None
                bookmaker_count = 0
                confidence = min(
                    Decimal(".62"),
                    (Decimal(".30") + Decimal(candidate.auto_score) / Decimal("300")).quantize(
                        Decimal(".000001"), rounding=ROUND_HALF_UP
                    ),
                )
                observed_at = candidate.fixture.observed_at or now
                price_reason = (
                    "Canlı bookmaker oranı alınamadı; oran uydurulmadı ve bu kayıt kupon "
                    "değil, ertesi gün kontrol edilecek fixture takip notudur."
                )
                price_risk = "Oran/piyasa verisi olmadığı için isabet metriklerine void/eksik veri olarak yazılır."
            prediction_id = uuid5(
                NAMESPACE_URL,
                ":".join(
                    (
                        "miron-baba-ai:daily-prediction",
                        str(run_id),
                        str(candidate.fixture.id),
                        market_key,
                        pick,
                        str(market_description or "match"),
                        str(line or "none"),
                    )
                ),
            )
            predictions.append(
                DailyPrediction(
                    prediction_id=prediction_id,
                    fixture=candidate.fixture,
                    league=candidate.league,
                    pick=pick,
                    market_key=market_key,
                    market_label=market_label,
                    outcome_label=outcome_label,
                    market_description=market_description,
                    line=line,
                    probability=probability,
                    market_decimal_odds=market_decimal_odds,
                    market_fair_probability=market_fair_probability,
                    bookmaker_count=bookmaker_count,
                    confidence=confidence,
                    score=score,
                    tier=tier,
                    reasons=(
                        f"{candidate.league.name} izin listesinde ve aday skoru {candidate.auto_score}/100.",
                        price_reason,
                        f"Günlük takip olasılığı %{(probability * 100).quantize(Decimal('.1'))}; "
                        "bu kupon kilidi değil, ertesi gün ölçülecek jurnal tahminidir.",
                    ),
                    risks=(
                        *candidate.risk_flags[:2],
                        "Kadro, sakatlık, rotasyon ve haber akışı kapanışa kadar değişebilir.",
                        price_risk,
                    ),
                    observed_at=observed_at,
                )
            )
        return tuple(sorted(predictions, key=lambda item: item.score, reverse=True)[:5])

    @classmethod
    def _journal_quote(
        cls, candidate: AutoCandidate, market: MarketOdds, now: datetime
    ) -> MarketQuote | None:
        del candidate
        fresh_quotes = tuple(
            quote
            for quote in market.quotes
            if quote.bookmaker_count >= 1 and now - quote.observed_at <= timedelta(hours=24)
        )
        quotes = fresh_quotes or market.quotes
        reviewable = tuple(quote for quote in quotes if cls._journalable_market(quote.market_key))
        quotes = reviewable or quotes
        preferred = tuple(quote for quote in quotes if quote.decimal_odds >= Decimal("1.35"))
        pool = preferred or quotes
        richer_pool = tuple(quote for quote in pool if quote.market_key != "h2h")
        pool = richer_pool or pool
        if not pool:
            return None
        return max(
            pool,
            key=lambda quote: (
                quote.fair_probability * Decimal("100")
                + min(quote.decimal_odds, Decimal("4")) * Decimal("7")
                + Decimal(min(quote.bookmaker_count, 8)),
                cls._market_depth_bonus(quote.market_key) * Decimal("3"),
                quote.decimal_odds,
            ),
        )

    @staticmethod
    def _settleable_market(market_key: str) -> bool:
        return market_key in {
            "h2h",
            "draw_no_bet",
            "double_chance",
            "btts",
            "totals",
            "alternate_totals",
            "team_totals",
            "alternate_team_totals",
            "spread",
            "odd_even",
        }

    @staticmethod
    def _journalable_market(market_key: str) -> bool:
        return market_key in {
            "h2h",
            "draw_no_bet",
            "double_chance",
            "btts",
            "totals",
            "alternate_totals",
            "team_totals",
            "alternate_team_totals",
            "spread",
            "odd_even",
            "first_half_h2h",
            "first_half_totals",
            "corners_spread",
            "cards_spread",
        }

    @staticmethod
    def _market_depth_bonus(market_key: str) -> Decimal:
        return {
            "spread": Decimal("9"),
            "totals": Decimal("8"),
            "alternate_totals": Decimal("8"),
            "btts": Decimal("7"),
            "draw_no_bet": Decimal("6"),
            "corners_spread": Decimal("6"),
            "cards_spread": Decimal("5"),
            "first_half_totals": Decimal("5"),
            "first_half_h2h": Decimal("4"),
            "odd_even": Decimal("4"),
            "double_chance": Decimal("3"),
            "h2h": Decimal("0"),
        }.get(market_key, Decimal("-10"))

    @staticmethod
    def _journal_probability(candidate: AutoCandidate, quote: MarketQuote) -> Decimal:
        score_lift = (Decimal(candidate.auto_score) - Decimal("70")) / Decimal("1000")
        coverage_lift = Decimal(min(quote.bookmaker_count, 8)) / Decimal("1000")
        probability = quote.fair_probability + score_lift + coverage_lift
        return min(Decimal(".92"), max(Decimal(".05"), probability)).quantize(
            Decimal(".000001"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _journal_confidence(candidate: AutoCandidate, quote: MarketQuote) -> Decimal:
        confidence = (
            Decimal(".40")
            + Decimal(candidate.auto_score) / Decimal("250")
            + Decimal(min(quote.bookmaker_count, 8)) / Decimal("100")
        )
        return min(Decimal(".88"), confidence).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _journal_score(
        candidate: AutoCandidate, quote: MarketQuote, probability: Decimal
    ) -> Decimal:
        price_balance = min(quote.decimal_odds, Decimal("4")) - Decimal("1")
        score = (
            probability * Decimal("55")
            + Decimal(candidate.auto_score) * Decimal(".25")
            + price_balance * Decimal("8")
            + Decimal(min(quote.bookmaker_count, 8))
            + AutoCouponService._market_depth_bonus(quote.market_key)
        )
        return min(Decimal("100"), score).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _fixture_only_probability(candidate: AutoCandidate) -> Decimal:
        probability = Decimal(".38") + Decimal(candidate.auto_score) / Decimal("450")
        return min(Decimal(".69"), max(Decimal(".35"), probability)).quantize(
            Decimal(".000001"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _fixture_only_score(candidate: AutoCandidate, probability: Decimal) -> Decimal:
        score = probability * Decimal("70") + Decimal(candidate.auto_score) * Decimal(".30")
        return min(Decimal("100"), score).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

    @classmethod
    def _daily_review_item(
        cls,
        prediction: DailyPrediction,
        fixture: CanonicalFixture,
        status: str,
    ) -> DailyPredictionReviewItem:
        sound = prediction.confidence >= Decimal(".58") and prediction.bookmaker_count >= 2
        if status == "void":
            verdict = "insufficient_data"
        elif status == "won":
            verdict = "sound_win" if sound else "lucky_win"
        else:
            verdict = "sound_but_unlucky_loss" if sound else "bad_process_loss"
        final_score = (
            f"{fixture.home_team} {fixture.home_score}-{fixture.away_score} {fixture.away_team}"
        )
        if status == "won":
            explanation = (
                f"Tahmin tuttu: {prediction.market_label} / {prediction.outcome_label}. "
                f"Final skor {final_score}. Ön maçta piyasa olasılığı ve aday skoru aynı yöne bakıyordu."
            )
            lesson = (
                "Bu sonuç tek başına modelin doğru olduğunu kanıtlamaz; kapanış öncesi fiyat "
                "ve kadro değişimiyle birlikte tekrar ölçülmeli."
            )
        elif status == "lost":
            explanation = (
                f"Tahmin kaybetti: {prediction.market_label} / {prediction.outcome_label}. "
                f"Final skor {final_score}. Ön maç sinyali gerçekleşen maç akışıyla uyuşmadı."
            )
            lesson = (
                "Kaybeden tahminde ana kontrol noktası; oran-fiyat dengesi, kadro haberi ve "
                "gol/tempo varsayımı kapanıştan önce zayıflamış mıydı."
            )
        else:
            if prediction.market_decimal_odds is None:
                explanation = (
                    f"Tahmin ölçüm dışı kaldı: {prediction.market_label} / "
                    f"{prediction.outcome_label}. Final skor {final_score}; ön maçta canlı "
                    "bookmaker oranı olmadığı için kupon/isabet metriğine dahil edilmedi."
                )
                lesson = (
                    "Odds olmayan günler veri sürekliliği için saklanır, fakat model "
                    "başarısı hesabında fiyatlı seçim gibi okunmaz."
                )
            else:
                explanation = (
                    f"Tahmin void sayıldı: {prediction.market_label} / {prediction.outcome_label}. "
                    f"Final skor {final_score}; çizgi veya pazar sonucu net kazanç/kayıp üretmedi."
                )
                lesson = (
                    "Void sonuçlar isabet oranına kalite kanıtı olarak eklenmez; yalnız veri "
                    "kapsamını artırır."
                )
        return DailyPredictionReviewItem(
            prediction_id=prediction.prediction_id,
            fixture_id=prediction.fixture.id,
            pick=prediction.pick,
            status=cast(Literal["won", "lost", "void"], status),
            final_home_score=fixture.home_score or 0,
            final_away_score=fixture.away_score or 0,
            probability=prediction.probability,
            market_decimal_odds=prediction.market_decimal_odds,
            process_verdict=cast(
                Literal[
                    "sound_win",
                    "lucky_win",
                    "sound_but_unlucky_loss",
                    "bad_process_loss",
                    "insufficient_data",
                ],
                verdict,
            ),
            explanation=explanation,
            lesson=lesson,
        )

    @staticmethod
    def _daily_review_report(
        run: AutoCouponRun,
        items: tuple[DailyPredictionReviewItem, ...],
        reviewed_at: datetime,
    ) -> DailyReviewReport:
        wins = sum(1 for item in items if item.status == "won")
        losses = sum(1 for item in items if item.status == "lost")
        voids = sum(1 for item in items if item.status == "void")
        decided = wins + losses
        odds_items = tuple(
            item
            for item in items
            if item.status in ("won", "lost", "void") and item.market_decimal_odds is not None
        )
        odds_values = tuple(
            item.market_decimal_odds for item in odds_items if item.market_decimal_odds is not None
        )
        profit = sum(
            (
                odds - Decimal("1")
                if item.status == "won"
                else Decimal("0")
                if item.status == "void"
                else Decimal("-1")
                for item, odds in zip(odds_items, odds_values, strict=True)
            ),
            Decimal("0"),
        )
        brier_items = tuple(
            (item.probability - (Decimal("1") if item.status == "won" else Decimal("0"))) ** 2
            for item in items
            if item.status in ("won", "lost")
        )
        hit_rate = (
            (Decimal(wins) / Decimal(decided)).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)
            if decided
            else None
        )
        summary = (
            f"{run.observed_at.date().isoformat()} jurnali: {len(items)}/"
            f"{len(run.daily_predictions)} tahmin sonuçlandı; {wins} tuttu, {losses} kaybetti, "
            f"{voids} void. Bu rapor kupon garantisi değil, süreç kalibrasyonu içindir."
        )
        return DailyReviewReport(
            reviewed_at=reviewed_at,
            total_predictions=len(run.daily_predictions),
            settled_predictions=len(items),
            wins=wins,
            losses=losses,
            voids=voids,
            hit_rate=hit_rate,
            average_odds=(
                (sum(odds_values, Decimal("0")) / len(odds_values)).quantize(
                    Decimal(".001"), rounding=ROUND_HALF_UP
                )
                if odds_values
                else None
            ),
            brier_score=(
                (sum(brier_items, Decimal("0")) / len(brier_items)).quantize(
                    Decimal(".0001"), rounding=ROUND_HALF_UP
                )
                if brier_items
                else None
            ),
            equal_stake_roi=(
                (profit / len(odds_values)).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)
                if odds_values
                else None
            ),
            summary=summary,
            items=items,
        )

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
    def _empty_funnel_after_journal(
        candidates: tuple[AutoCandidate, ...],
        rationale: str,
    ) -> tuple[FunnelDecision, FunnelDecision]:
        all_ids = tuple(item.fixture.id for item in candidates)
        return (
            FunnelDecision(
                stage="rough",
                input_count=len(candidates),
                selected_fixture_ids=(),
                eliminated_fixture_ids=all_ids,
                rationale=rationale,
                model_id="journal-fail-soft",
            ),
            FunnelDecision(
                stage="critic",
                input_count=0,
                selected_fixture_ids=(),
                eliminated_fixture_ids=(),
                rationale="Kaba eleme boş kaldığı için derin kupon analizi başlatılmadı.",
                model_id="journal-fail-soft",
            ),
        )

    @staticmethod
    def _deterministic_funnel_after_empty_gemini(
        candidates: tuple[AutoCandidate, ...],
        rough: FunnelDecision,
        critic: FunnelDecision,
    ) -> tuple[FunnelDecision, FunnelDecision]:
        fallback_ids = tuple(item.fixture.id for item in candidates[: min(3, len(candidates))])
        all_ids = tuple(item.fixture.id for item in candidates)
        return (
            FunnelDecision(
                stage=rough.stage,
                input_count=rough.input_count,
                selected_fixture_ids=fallback_ids,
                eliminated_fixture_ids=tuple(item for item in all_ids if item not in fallback_ids),
                rationale=(
                    f"{rough.rationale} Canlı gerçek odds bulunduğu için boş Gemini ön elemesi "
                    "nihai karar sayılmadı; en yüksek puanlı adaylar derin finalist analizine "
                    "gönderildi."
                ),
                model_id=f"{rough.model_id}+score-fallback",
            ),
            FunnelDecision(
                stage=critic.stage,
                input_count=len(fallback_ids),
                selected_fixture_ids=fallback_ids,
                eliminated_fixture_ids=(),
                rationale=(
                    f"{critic.rationale} Fail-soft kuralı: canlı odds olan günlerde sistem "
                    "aday varken sessiz kalmaz; kupon yine yalnız derin analiz, gerçek oran, "
                    "%70+ olasılık ve 1.80+ toplam oran kapısından geçerse yayınlanır."
                ),
                model_id=f"{critic.model_id}+score-fallback",
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
            if not cls._settleable_market(quote.market_key):
                continue
            probability = cls._model_market_probability(forecast, fixture, quote)
            if probability is None or probability < MIN_SELECTION_PROBABILITY:
                continue
            edge = probability - quote.fair_probability
            minimum_edge = Decimal(".05") if quote.bookmaker_count == 1 else Decimal(".02")
            if edge < minimum_edge:
                continue
            if quote.decimal_odds < MIN_COMBO_LEG_DECIMAL_ODDS:
                continue
            price_quality = min(quote.decimal_odds, Decimal("10")) - MIN_COMBO_LEG_DECIMAL_ODDS
            score = (
                probability * Decimal("55")
                + edge * Decimal("250")
                + forecast.confidence * Decimal("15")
                + price_quality * Decimal("10")
                + min(Decimal(quote.bookmaker_count), Decimal("10"))
                + cls._market_depth_bonus(quote.market_key) * Decimal("1.5")
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
        direct_probability = AutoCouponService._forecast_market_probability(forecast, quote)
        if direct_probability is not None:
            return direct_probability
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
        if quote.market_key == "double_chance":
            return {
                "1x": outcomes["home"] + outcomes["draw"],
                "12": outcomes["home"] + outcomes["away"],
                "x2": outcomes["draw"] + outcomes["away"],
            }.get(quote.outcome_key)
        if quote.market_key == "btts":
            yes = (Decimal("1") - Decimal(str(math.exp(-float(home_xg))))) * (
                Decimal("1") - Decimal(str(math.exp(-float(away_xg))))
            )
            return yes if quote.outcome_key == "yes" else Decimal("1") - yes
        if quote.market_key == "odd_even":
            total_xg = home_xg + away_xg
            even = (Decimal("1") + Decimal(str(math.exp(-2 * float(total_xg))))) / Decimal("2")
            return Decimal("1") - even if quote.outcome_key == "odd" else even
        if quote.market_key in ("totals", "alternate_totals"):
            return AutoCouponService._over_under_probability(
                home_xg + away_xg, quote.point, quote.outcome_key
            )
        if quote.market_key == "spread":
            return AutoCouponService._spread_probability(
                home_xg, away_xg, quote.point, quote.outcome_key
            )
        if quote.market_key == "first_half_h2h":
            if quote.outcome_key not in ("home", "draw", "away"):
                return None
            half_outcomes = {
                item.outcome: item.probability
                for item in AutoCouponService._poisson_outcome_probabilities(
                    home_xg * Decimal(".45"), away_xg * Decimal(".45")
                )
            }
            return half_outcomes[quote.outcome_key]
        if quote.market_key == "first_half_totals":
            return AutoCouponService._over_under_probability(
                (home_xg + away_xg) * Decimal(".45"), quote.point, quote.outcome_key
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
    def _forecast_market_probability(forecast: FinalForecast, quote: MarketQuote) -> Decimal | None:
        candidates = [
            item
            for item in forecast.market_probabilities
            if item.market_key == quote.market_key and item.outcome_key == quote.outcome_key
        ]
        if quote.point is not None:
            candidates = [
                item
                for item in candidates
                if item.line is not None and abs(item.line - quote.point) <= Decimal(".05")
            ]
        if quote.description:
            normalized_description = quote.description.casefold()
            exact = [
                item
                for item in candidates
                if item.description is not None
                and item.description.casefold() == normalized_description
            ]
            candidates = exact or candidates
        if not candidates:
            return None
        return max(item.probability for item in candidates)

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
    def _spread_probability(
        home_xg: Decimal, away_xg: Decimal, point: Decimal | None, outcome: str
    ) -> Decimal | None:
        if point is None or outcome not in ("home", "away"):
            return None
        probability = Decimal("0")
        for home_goals in range(11):
            home_prob = AutoCouponService._poisson_probability(home_xg, home_goals)
            for away_goals in range(11):
                away_prob = AutoCouponService._poisson_probability(away_xg, away_goals)
                if outcome == "home":
                    adjusted = Decimal(home_goals - away_goals) + point
                else:
                    adjusted = Decimal(away_goals - home_goals) - point
                if adjusted > 0:
                    probability += home_prob * away_prob
        return min(Decimal("1"), max(Decimal("0"), probability))

    @staticmethod
    def _poisson_probability(intensity: Decimal, goals: int) -> Decimal:
        return (
            Decimal(str(math.exp(-float(intensity))))
            * (intensity**goals)
            / Decimal(math.factorial(goals))
        )

    @staticmethod
    def _poisson_outcome_probabilities(
        home_xg: Decimal, away_xg: Decimal
    ) -> tuple[OutcomeProbability, OutcomeProbability, OutcomeProbability]:
        home = Decimal("0")
        draw = Decimal("0")
        away = Decimal("0")
        for home_goals in range(11):
            home_prob = AutoCouponService._poisson_probability(home_xg, home_goals)
            for away_goals in range(11):
                item = home_prob * AutoCouponService._poisson_probability(away_xg, away_goals)
                if home_goals > away_goals:
                    home += item
                elif home_goals == away_goals:
                    draw += item
                else:
                    away += item
        total = home + draw + away
        home = (home / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        draw = (draw / total).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)
        away = Decimal("1") - home - draw
        return (
            OutcomeProbability(outcome="home", probability=home, lower=home, upper=home),
            OutcomeProbability(outcome="draw", probability=draw, lower=draw, upper=draw),
            OutcomeProbability(outcome="away", probability=away, lower=away, upper=away),
        )

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
