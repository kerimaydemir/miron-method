import asyncio
import hashlib
import logging
import math
import re
import unicodedata
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal, Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

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

logger = logging.getLogger(__name__)

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
TEAM_SIGNATURE_STOPWORDS = frozenset(
    {
        "afc",
        "cf",
        "club",
        "de",
        "fc",
        "football",
        "sc",
        "san",
        "sebastian",
        "sevilla",
        "seville",
        "the",
    }
)

# The deep-model route may publish only tickets that clear the explicit value
# gate. The separate daily market-consensus route is labelled as such and never
# claims to be a 70% model prediction.
MIN_SELECTION_PROBABILITY = Decimal(".70")
MIN_SELECTION_DECIMAL_ODDS = Decimal("1.80")
MIN_COMBO_LEG_DECIMAL_ODDS = Decimal("1.20")


def scan_end_for_window(
    now: datetime, *, window_days: int, app_timezone: ZoneInfo
) -> datetime:
    if window_days == 1:
        local_now = now.astimezone(app_timezone)
        next_midnight = datetime.combine(
            local_now.date() + timedelta(days=1),
            time.min,
            tzinfo=app_timezone,
        )
        return next_midnight.astimezone(UTC)
    return now + timedelta(days=window_days)


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
        force_daily_ticket: bool = True,
        forced_min_combined_odds: Decimal = Decimal("1.80"),
        forced_max_combined_odds: Decimal = Decimal("2.60"),
        app_timezone: str = "Europe/Istanbul",
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
        self._force_daily_ticket = force_daily_ticket
        self._forced_min_combined_odds = forced_min_combined_odds
        self._forced_max_combined_odds = forced_max_combined_odds
        self._app_timezone = ZoneInfo(app_timezone)

    async def create(self, *, idempotency_key: str) -> AutoCouponRun:
        if not self._odds.available:
            raise ValueError("AUTO_COUPON_LIVE_MARKET_REQUIRED")
        if self._funnel is not None:
            if not self._analysis.deep_data_ready:
                raise ValueError("AUTO_COUPON_DEEP_DATA_REQUIRED")
            if not self._analysis.deep_analysis_ready:
                raise ValueError("AUTO_COUPON_DEEP_ANALYSIS_NOT_READY")
        elif not self._analysis.deep_data_ready:
            logger.warning("Deep structured data unavailable; continuing with market-only free mode")
        now = datetime.now(UTC)
        run_id = uuid5(NAMESPACE_URL, f"miron-baba-ai:auto-coupon:{idempotency_key}")
        existing = self._repository.load(run_id)
        refresh_existing_journal = existing is not None and not existing.selections
        if (
            existing is not None
            and not refresh_existing_journal
            and self._is_reusable(existing, now)
        ):
            return existing
        if existing is not None and not refresh_existing_journal:
            run_id = uuid5(
                NAMESPACE_URL,
                f"miron-baba-ai:auto-coupon:{idempotency_key}:{now.isoformat(timespec='seconds')}",
            )
        latest = self._repository.latest()
        if latest is not None and self._is_reusable(latest, now):
            return latest
        end = self._scan_end(now)
        source_mode: Literal["bookmaker_live", "fixture_live_no_odds"] = "bookmaker_live"
        try:
            market_pairs = (
                await asyncio.wait_for(
                    self._odds.list_market_fixtures(start_utc=now, end_utc=end),
                    timeout=180,
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
        candidates = self._dedupe_candidates_by_match(
            await self._rank_candidates(fixtures, markets, memory_context)
        )
        initial = candidates[:10]
        if not initial:
            raise ValueError("AUTO_COUPON_NO_CURRENT_TOP_LEAGUE_FIXTURES")
        daily_predictions = self._daily_predictions(run_id, initial, markets, now)
        if markets and self._funnel is not None:
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
        elif markets:
            rough, critic = self._empty_funnel_after_journal(
                initial,
                "Gemini kapalı; bağımsız model analizi yapılmadı. Yalnız canlı piyasa "
                "konsensüsü jurnale alındı.",
            )
            funnel_cost = Decimal("0")
        else:
            rough, critic = self._empty_funnel_after_journal(
                initial,
                "Canlı bookmaker oranı alınamadı; günlük fixture jurnali kaydedildi, kupon analizi başlatılmadı.",
            )
            funnel_cost = Decimal("0")

        by_id = {item.fixture.id: item for item in initial}
        if markets and self._funnel is not None and not critic.selected_fixture_ids:
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
            if not self._publishable_forecast(locked.forecast):
                logger.warning(
                    "Mock forecast rejected from publishable coupon",
                    extra={"fixture_id": str(fixture_id), "run_id": str(run_id)},
                )
                continue
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
                    bookmaker=quote.bookmaker,
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
        forced_daily_ticket = False
        if not tickets and self._force_daily_ticket and markets and len(initial) >= 2:
            forced_selections, tickets = self._forced_daily_coupon(
                run_id, initial, markets, now
            )
            if tickets:
                ordered_candidates = forced_selections
                forced_daily_ticket = True
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
            notice=self._run_notice(
                source_mode=source_mode,
                finalist_analysis_timed_out=finalist_analysis_timed_out,
                has_ordered=bool(ordered),
                has_tickets=bool(tickets),
                forced_daily_ticket=forced_daily_ticket,
            ),
        )
        if refresh_existing_journal:
            self._repository.update_run(auto_run)
        else:
            self._repository.save(auto_run)
        return auto_run

    @staticmethod
    def _run_notice(
        *,
        source_mode: Literal["bookmaker_live", "fixture_live_no_odds"],
        finalist_analysis_timed_out: bool,
        has_ordered: bool,
        has_tickets: bool,
        forced_daily_ticket: bool,
    ) -> str:
        if source_mode == "fixture_live_no_odds":
            return (
                "Bugün canlı bookmaker oranı alınamadı; sistem oran uydurmadı, sadece "
                "büyük lig fixture jurnalini kaydetti."
            )
        if forced_daily_ticket:
            return (
                "Strict %70+ değer kapısından seçim çıkmadı; sezon/maç akışı aktif olduğu "
                "için gerçek oranlardan günlük piyasa ikilisi üretildi. Olasılıklar yalnız "
                "marjı temizlenmiş bookmaker konsensüsüdür; %70 model veya garanti iddiası değildir."
            )
        if finalist_analysis_timed_out and not has_ordered:
            return (
                "Derin finalist analizi süre sınırına takıldı; günlük jurnal kaydedildi, "
                "kota doldurmak için kör kupon üretilmedi."
            )
        if not has_tickets:
            return (
                "Bugün kanıt, fiyat ve belirsizlik eşiklerini birlikte geçen seçim yok; "
                "forced kupon için de en az iki ayrı gerçek oranlı maç bulunamadı."
            )
        return "Olasılıksal seçimdir; kesinlik veya bahis tavsiyesi değildir."

    @staticmethod
    def _publishable_forecast(forecast: FinalForecast) -> bool:
        return forecast.analysis_provider != "mock"

    def _is_reusable(self, run: AutoCouponRun, now: datetime) -> bool:
        scan_end = self._scan_end(now)
        return (
            run.state == "completed"
            and run.source_mode == "bookmaker_live"
            and now - run.observed_at <= self._reuse_interval
            and bool(run.selections)
            and all(
                item.settlement_status == "pending"
                and item.fixture.kickoff_at > now
                and item.fixture.kickoff_at <= scan_end
                and item.market_decimal_odds is not None
                for item in run.selections
            )
        )

    def _scan_end(self, now: datetime) -> datetime:
        return scan_end_for_window(
            now, window_days=self._window_days, app_timezone=self._app_timezone
        )

    def readiness(self) -> AutoCouponReadiness:
        bookmaker_ready = self._odds.available
        gemini_ready = self._funnel is not None
        deep_data_ready = self._analysis.deep_data_ready
        deep_ready = self._analysis.deep_analysis_ready
        blockers: list[str] = []
        if not bookmaker_ready:
            blockers.append("AUTO_COUPON_LIVE_MARKET_REQUIRED")
        if gemini_ready and not deep_data_ready:
            blockers.append("AUTO_COUPON_DEEP_DATA_REQUIRED")
        if gemini_ready and not deep_ready:
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
            return (
                "Gemini analiz rotası kapalı; ücretsiz maliyet korumalı modda canlı "
                "bookmaker oranları ve deterministik puanlama ile kupon üretilebilir."
            )
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
        now = datetime.now(UTC)
        for pending in self._repository.list_pending():
            if run_id is not None and pending.auto_run_id != run_id:
                continue
            snapshot = getattr(pending, "fixture", None)
            if isinstance(snapshot, CanonicalFixture) and snapshot.kickoff_at > now:
                continue
            fixture = await self._refresh_pending_fixture_result(pending)
            if fixture is None:
                continue
            if (
                fixture.status != "finished"
                or fixture.home_score is None
                or fixture.away_score is None
            ):
                continue
            match_result = MatchResult(
                fixture_id=fixture.id,
                home_score=fixture.home_score,
                away_score=fixture.away_score,
                observed_at=fixture.observed_at or datetime.now(UTC),
                source=fixture.source_provider,
            )
            actual = result_outcome(match_result)
            settlement_status = self._settlement_status(pending.pick, fixture, actual)
            if pending.lock_id is None:
                lock = None
            else:
                try:
                    lock = self._analysis.get_lock(pending.lock_id)
                except (KeyError, ValueError):
                    lock = None
            if lock is None or not self._is_match_result_pick(pending.pick):
                self._repository.mark_settled(
                    auto_run_id=pending.auto_run_id,
                    fixture_id=pending.fixture_id,
                    status=settlement_status,
                    autopsy_id=None,
                    home_score=fixture.home_score,
                    away_score=fixture.away_score,
                    post_match={
                        "autopsy_id": None,
                        "result_verdict": settlement_status,
                        "process_verdict": "selected_market_score_settlement",
                        "realized_outcome": actual,
                        "explanation": self._forced_settlement_explanation(
                            pending.pick, fixture, settlement_status
                        ),
                    },
                )
            else:
                autopsy = self._post_match.ingest(
                    lock,
                    match_result,
                )
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
                        "explanation": self._forced_settlement_explanation(
                            pending.pick, fixture, settlement_status
                        ),
                        "forecast_autopsy_explanation": autopsy.post_match_explanation,
                        "variance": [item.model_dump(mode="json") for item in autopsy.variance],
                        "lesson": autopsy.lesson.model_dump(mode="json"),
                    },
                )
            settled += 1
        return settled

    @staticmethod
    def _is_match_result_pick(pick: str) -> bool:
        if pick in ("home", "draw", "away"):
            return True
        return pick.split(":", maxsplit=1)[0] == "h2h"

    async def _refresh_pending_fixture_result(self, pending: Any) -> CanonicalFixture | None:
        snapshot = getattr(pending, "fixture", None)
        return await self._refresh_fixture_result(
            pending.fixture_id,
            snapshot if isinstance(snapshot, CanonicalFixture) else None,
        )

    async def _refresh_fixture_result(
        self, fixture_id: UUID, snapshot: CanonicalFixture | None
    ) -> CanonicalFixture | None:
        fixture: CanonicalFixture | None = None
        try:
            fixture = await self._analysis_fixtures.refresh_result(fixture_id)
        except (KeyError, RuntimeError, httpx.HTTPError):
            fixture = None
        if (
            fixture is not None
            and fixture.status == "finished"
            and fixture.home_score is not None
            and fixture.away_score is not None
        ):
            return fixture
        if snapshot is None:
            return fixture
        refresh_snapshot = getattr(self._odds, "refresh_fixture_result", None)
        if refresh_snapshot is None:
            return fixture or snapshot
        try:
            refresh_fixture_result = cast(
                Callable[[CanonicalFixture], Awaitable[CanonicalFixture]],
                refresh_snapshot,
            )
            return await refresh_fixture_result(snapshot)
        except (KeyError, RuntimeError, ValueError, httpx.HTTPError):
            return fixture or snapshot

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
                if prediction.fixture.kickoff_at > now:
                    continue
                fixture = await self._refresh_fixture_result(prediction.fixture.id, prediction.fixture)
                if fixture is None:
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
        if market_key in {
            "totals",
            "alternate_totals",
            "team_totals",
            "alternate_team_totals",
            "spread",
            "spread_v2",
        } and not AutoCouponService._line_is_fully_settleable(line):
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
        elif market_key in ("spread", "spread_v2"):
            if outcome == "home":
                adjusted_margin = Decimal(fixture.home_score - fixture.away_score) + line
            elif outcome == "away":
                adjusted_margin = Decimal(fixture.away_score - fixture.home_score)
                adjusted_margin += line if market_key == "spread_v2" else -line
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

    @staticmethod
    def _forced_settlement_explanation(
        pick: str, fixture: CanonicalFixture, status: str
    ) -> str:
        """Create an evidence-bound explanation for forced tickets.

        Market-consensus tickets do not have a deep-analysis lock, so their
        review must not invent tactical or late-goal narratives. It records
        only the observed score and the market rule that did or did not land.
        """
        home = fixture.home_score if fixture.home_score is not None else 0
        away = fixture.away_score if fixture.away_score is not None else 0
        score = f"{fixture.home_team} {home}-{away} {fixture.away_team}"
        parts = pick.split(":", maxsplit=3)
        market_key = parts[0] if len(parts) == 4 else "market"
        line = parts[3] if len(parts) == 4 else ""
        total_goals = home + away
        if market_key in ("totals", "alternate_totals", "first_half_totals"):
            detail = f"Toplam gol {total_goals}; seçilen çizgi {line}."
        elif market_key in ("spread", "spread_v2", "corners_spread", "cards_spread"):
            detail = f"Skor farkı {home - away}; seçilen handikap çizgisi {line}."
        elif market_key == "btts":
            detail = f"Karşılıklı gol {'var' if home > 0 and away > 0 else 'yok'}."
        elif market_key == "draw_no_bet":
            detail = "Maç sonucu beraberlik" if home == away else "Maç sonucu beraberlik değil."
        elif market_key in ("h2h", "double_chance"):
            direction = "ev sahibi" if home > away else "deplasman" if away > home else "beraberlik"
            detail = f"Gerçekleşen yön {direction}."
        else:
            detail = "Pazar kuralı nihai skor üzerinden hesaplandı."
        verdict = "tuttu" if status == "won" else "kaybetti" if status == "lost" else "void oldu"
        return (
            f"Piyasa konsensüsü bacağı {verdict}. Nihai skor: {score}. {detail} "
            "Gol dakikası veya kadro/haber olayı doğrulanmadığı için neden uydurulmadı; "
            "sonuç aynı marketin sonraki seçim cezasına dahil edildi."
        )

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
                fully_settleable = cls._fully_settleable_quote(quote)
                tier: Literal["journal_only", "watchlist", "coupon_candidate"] = (
                    "coupon_candidate"
                    if fully_settleable
                    and probability >= MIN_SELECTION_PROBABILITY
                    and quote.decimal_odds >= MIN_COMBO_LEG_DECIMAL_ODDS
                    else "watchlist"
                    if fully_settleable
                    and probability >= Decimal(".58")
                    and quote.decimal_odds >= Decimal("1.45")
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
                bookmaker = quote.bookmaker
                confidence = cls._journal_confidence(candidate, quote)
                observed_at = quote.observed_at
                price_reason = (
                    f"{quote.bookmaker or quote.provider} kaynağında alınabilir oran "
                    f"{quote.decimal_odds}; {quote.bookmaker_count} bookmaker konsensüsü "
                    f"%{(quote.fair_probability * 100).quantize(Decimal('.1'))} marjı "
                    "temizlenmiş piyasa olasılığı veriyor."
                )
                price_risk = (
                    "Bookmaker piyasası tek başına gerçek sebep kanıtı değildir."
                    if fully_settleable
                    else "Bu pazar için doğrulanmış sonuç alanı yok; yalnız gözlem, isabet metriği değil."
                )
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
                bookmaker = None
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
                    bookmaker=bookmaker,
                    confidence=confidence,
                    score=score,
                    tier=tier,
                    reasons=(
                        f"{candidate.league.name} izin listesinde ve aday skoru {candidate.auto_score}/100.",
                        price_reason,
                        f"Marjı temizlenmiş piyasa konsensüsü "
                        f"%{(probability * 100).quantize(Decimal('.1'))}; bu oran bağımsız "
                        "model tahmini veya garanti değildir.",
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
            if quote.bookmaker_count >= 1
            and -timedelta(minutes=5) <= now - quote.observed_at <= timedelta(hours=6)
        )
        if not fresh_quotes:
            return None
        reviewable = tuple(quote for quote in fresh_quotes if cls._fully_settleable_quote(quote))
        observable = tuple(
            quote for quote in fresh_quotes if cls._journalable_market(quote.market_key)
        )
        quotes = reviewable or observable
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
    def _line_is_fully_settleable(point: Decimal) -> bool:
        """Only integer and half lines have a binary won/lost/void settlement."""
        doubled = point * Decimal("2")
        return doubled == doubled.to_integral_value()

    @classmethod
    def _fully_settleable_quote(cls, quote: MarketQuote) -> bool:
        if not cls._settleable_market(quote.market_key):
            return False
        if quote.market_key in {
            "totals",
            "alternate_totals",
            "team_totals",
            "alternate_team_totals",
            "spread",
        }:
            return quote.point is not None and cls._line_is_fully_settleable(quote.point)
        return True

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
        del candidate
        return min(Decimal(".99"), max(Decimal(".01"), quote.fair_probability)).quantize(
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
        market_consensus_only = (
            prediction.market_fair_probability is not None
            and abs(prediction.probability - prediction.market_fair_probability)
            <= Decimal(".000001")
        )
        sound = (
            not market_consensus_only
            and prediction.confidence >= Decimal(".58")
            and prediction.bookmaker_count >= 2
        )
        market_result = cls._realized_market_summary(prediction, fixture)
        process_note = cls._process_review_note(prediction, status)
        if status == "void" or market_consensus_only:
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
                f"Final skor {final_score}. {market_result} {process_note}"
            )
            lesson = (
                "Tutan kupon tek başına modelin doğru olduğunu kanıtlamaz; kapanış oranı, "
                "kadro/haber değişimi ve seçilen market tipi sonraki örneklerle birlikte izlenmeli."
            )
        elif status == "lost":
            explanation = (
                f"Tahmin kaybetti: {prediction.market_label} / {prediction.outcome_label}. "
                f"Final skor {final_score}. {market_result} {process_note}"
            )
            lesson = (
                "Kaybeden seçimde ana kontrol: market çizgisi gereğinden agresif miydi, "
                "oran bu riski gerçekten ödüyor muydu, kapanış öncesi kadro/haber/tempo sinyali "
                "zayıflamış mıydı. Son dakika golü veya tek olay etkisi varsa süreç kötü diye "
                "otomatik damgalanmaz; aynı markette tekrar eden sapma aranır."
            )
        else:
            if prediction.market_decimal_odds is None:
                explanation = (
                    f"Tahmin ölçüm dışı kaldı: {prediction.market_label} / "
                    f"{prediction.outcome_label}. Final skor {final_score}. {market_result} "
                    "Ön maçta canlı bookmaker oranı olmadığı için kupon/isabet metriğine dahil edilmedi."
                )
                lesson = (
                    "Odds olmayan günler veri sürekliliği için saklanır, fakat model "
                    "başarısı hesabında fiyatlı seçim gibi okunmaz."
                )
            else:
                explanation = (
                    f"Tahmin void sayıldı: {prediction.market_label} / {prediction.outcome_label}. "
                    f"Final skor {final_score}. {market_result} Çizgi veya pazar sonucu net "
                    "kazanç/kayıp üretmedi."
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
    def _realized_market_summary(prediction: DailyPrediction, fixture: CanonicalFixture) -> str:
        home = fixture.home_score or 0
        away = fixture.away_score or 0
        goals = home + away
        line = prediction.line
        pick = prediction.pick.split(":", maxsplit=3)
        market_key = pick[0] if len(pick) == 4 else prediction.market_key
        outcome = pick[2] if len(pick) == 4 else ""
        description = pick[1] if len(pick) == 4 else (prediction.market_description or "")
        if market_key == "h2h":
            realized = "MS 1" if home > away else "MS 2" if away > home else "MS X"
            return f"Gerçekleşen maç sonucu {realized}; skor farkı {abs(home - away)}."
        if market_key == "draw_no_bet":
            realized = "beraberlik/iade" if home == away else "ev sahibi" if home > away else "deplasman"
            return f"Beraberlikte iade pazarı {realized} sonucuna gitti."
        if market_key == "double_chance":
            realized = "1X" if home >= away else "X2" if away >= home else "12"
            return f"Çifte şans açısından finalin kapsadığı ana yön {realized}; skor {home}-{away}."
        if market_key == "btts":
            realized = "KG Var" if home > 0 and away > 0 else "KG Yok"
            return f"Karşılıklı gol sonucu {realized}; iki takım gol dağılımı {home}-{away}."
        if market_key in ("totals", "alternate_totals", "first_half_totals"):
            line_text = str(line) if line is not None else "belirsiz"
            realized = "üst" if line is not None and Decimal(goals) > line else "alt"
            return f"Toplam gol {goals}; çizgi {line_text}, gerçekleşen yön {realized}."
        if market_key in ("team_totals", "alternate_team_totals"):
            target_goals = home if description.casefold() == fixture.home_team.casefold() else away
            team = prediction.market_description or description or "takım"
            line_text = str(line) if line is not None else "belirsiz"
            return f"{team} gol sayısı {target_goals}; takım gol çizgisi {line_text}."
        if market_key in ("spread", "spread_v2"):
            handicap = line or Decimal("0")
            adjusted = (
                Decimal(home - away) + handicap
                if outcome == "home"
                else Decimal(away - home)
                + (handicap if market_key == "spread_v2" else -handicap)
            )
            return f"Handikap hesabı {adjusted}; çıplak skor farkı {home - away}."
        if market_key == "odd_even":
            realized = "Çift" if goals % 2 == 0 else "Tek"
            return f"Toplam gol {goals}; tek/çift sonucu {realized}."
        return f"Market sonucu final skora göre {home}-{away} üzerinden hesaplandı."

    @staticmethod
    def _process_review_note(prediction: DailyPrediction, status: str) -> str:
        probability_pct = (prediction.probability * Decimal("100")).quantize(Decimal(".1"))
        odds_text = (
            f"oran {prediction.market_decimal_odds}"
            if prediction.market_decimal_odds is not None
            else "oran yok"
        )
        if prediction.bookmaker_count <= 1:
            depth = "piyasa derinliği zayıf"
        elif prediction.bookmaker_count <= 3:
            depth = "piyasa derinliği orta"
        else:
            depth = "piyasa derinliği iyi"
        if (
            prediction.market_fair_probability is not None
            and abs(prediction.probability - prediction.market_fair_probability)
            <= Decimal(".000001")
        ):
            return (
                f"Ön kayıt bookmaker konsensüsü %{probability_pct}, {odds_text}; {depth}. "
                "Bağımsız model olasılığı olmadığı için süreç başarısı olarak etiketlenmez."
            )
        if status == "won":
            return (
                f"Ön tahmin %{probability_pct}, {odds_text}; {depth}. "
                "Bu kayıt olumlu örnek olarak hafızaya girer ama tek başına başarı kanıtı sayılmaz."
            )
        if status == "lost":
            return (
                f"Ön tahmin %{probability_pct}, {odds_text}; {depth}. "
                "Bu kayıt kayıp sebebiyle negatif örnek olarak hafızaya girer ve aynı market/çizgi "
                "kombinasyonunda tekrar eden hata aranır."
            )
        return f"Ön tahmin %{probability_pct}, {odds_text}; {depth}. Ölçüm dışı/void olarak ayrılır."

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
                rationale="Ücretsiz maliyet korumalı modda canlı odds, lig kalitesi ve puan sırası ile ilk eleme yapıldı.",
                model_id="deterministic-free-policy",
            ),
            FunnelDecision(
                stage="critic",
                input_count=len(rough_ids),
                selected_fixture_ids=critic_ids,
                eliminated_fixture_ids=tuple(item for item in rough_ids if item not in critic_ids),
                rationale="Ücretsiz maliyet korumalı modda en yüksek üç aday finalist havuzuna alındı.",
                model_id="deterministic-free-policy",
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
            quote_age = now - quote.observed_at
            if (
                quote.bookmaker_count < minimum_books
                or quote_age < -timedelta(minutes=5)
                or quote_age > timedelta(minutes=15)
            ):
                continue
            if not cls._fully_settleable_quote(quote):
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
                    adjusted = Decimal(away_goals - home_goals) + point
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
        pick_market_key = "spread_v2" if quote.market_key == "spread" else quote.market_key
        return f"{pick_market_key}:{description}:{quote.outcome_key}:{line}"

    @staticmethod
    def _selection_label(quote: MarketQuote) -> str:
        side_labels = {
            "home": "1",
            "draw": "X",
            "away": "2",
        }
        if quote.market_key == "h2h":
            label = f"MS {side_labels.get(quote.outcome_key, quote.outcome_label)}"
            if quote.description and quote.outcome_key != "draw":
                return f"{label} ({quote.description})"
            return label
        if quote.market_key == "first_half_h2h":
            label = f"İY {side_labels.get(quote.outcome_key, quote.outcome_label)}"
            if quote.description and quote.outcome_key != "draw":
                return f"{label} ({quote.description})"
            return label
        if quote.market_key == "double_chance":
            return f"Çifte Şans {quote.outcome_key.upper()}"
        if quote.market_key == "btts":
            return "KG Var" if quote.outcome_key == "yes" else "KG Yok"
        if quote.market_key in ("totals", "alternate_totals", "first_half_totals"):
            prefix = "İY " if quote.market_key == "first_half_totals" else ""
            line = f"{quote.point} " if quote.point is not None else ""
            return f"{prefix}{line}{quote.outcome_label}".strip()
        if quote.market_key in ("team_totals", "alternate_team_totals"):
            line = f"{quote.point} " if quote.point is not None else ""
            team = f"{quote.description} " if quote.description else ""
            return f"{team}{line}{quote.outcome_label}".strip()
        if quote.market_key in ("spread", "corners_spread", "cards_spread"):
            market_prefix = {
                "spread": "Handikap",
                "corners_spread": "Korner Handikap",
                "cards_spread": "Kart Handikap",
            }[quote.market_key]
            side = side_labels.get(quote.outcome_key, quote.outcome_label)
            line = f" {quote.point}" if quote.point is not None else ""
            team = f" ({quote.description})" if quote.description else ""
            return f"{market_prefix} {side}{line}{team}".strip()
        if quote.market_key == "draw_no_bet":
            side = side_labels.get(quote.outcome_key, quote.outcome_label)
            team = f" ({quote.description})" if quote.description else ""
            return f"Beraberlikte İade {side}{team}".strip()
        if quote.market_key == "odd_even":
            return quote.outcome_label
        return " ".join(
            item
            for item in (quote.description, quote.outcome_label, str(quote.point or ""))
            if item
        )

    def _forced_daily_coupon(
        self,
        run_id: UUID,
        candidates: tuple[AutoCandidate, ...],
        markets: dict[UUID, MarketOdds],
        now: datetime,
    ) -> tuple[tuple[CouponSelection, ...], tuple[CouponTicket, ...]]:
        leg_pool: list[tuple[Decimal, AutoCandidate, MarketQuote, Decimal, Decimal]] = []
        market_penalties = self._market_learning_penalties()
        for candidate in candidates:
            market = markets.get(candidate.fixture.id)
            if market is None:
                continue
            for quote in market.quotes:
                quote_age = now - quote.observed_at
                if quote_age < -timedelta(minutes=5) or quote_age > timedelta(hours=6):
                    continue
                if quote.bookmaker_count < 2 or not self._fully_settleable_quote(quote):
                    continue
                if quote.decimal_odds < Decimal("1.30") or quote.decimal_odds > Decimal("2.05"):
                    continue
                if quote.market_key == "h2h" and quote.decimal_odds < Decimal("1.45"):
                    continue
                probability = self._journal_probability(candidate, quote)
                edge = probability - quote.fair_probability
                target_leg_price = Decimal("1.45")
                price_penalty = abs(quote.decimal_odds - target_leg_price) * Decimal("8")
                safety_bonus = Decimal("8") if quote.decimal_odds <= Decimal("1.65") else Decimal("0")
                score = (
                    probability * Decimal("100")
                    + self._market_depth_bonus(quote.market_key) * Decimal("1.2")
                    + safety_bonus
                    + Decimal(min(quote.bookmaker_count, 6))
                    - price_penalty
                    - market_penalties.get(quote.market_key, Decimal("0"))
                ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                leg_pool.append((score, candidate, quote, probability, edge))
        if len({self._fixture_match_key(item[1].fixture) for item in leg_pool}) < 2:
            return (), ()

        viable_pairs: list[
            tuple[
                Decimal,
                Decimal,
                Decimal,
                tuple[Decimal, AutoCandidate, MarketQuote, Decimal, Decimal],
                tuple[Decimal, AutoCandidate, MarketQuote, Decimal, Decimal],
            ]
        ] = []
        fallback_pairs: list[
            tuple[
                Decimal,
                Decimal,
                Decimal,
                tuple[Decimal, AutoCandidate, MarketQuote, Decimal, Decimal],
                tuple[Decimal, AutoCandidate, MarketQuote, Decimal, Decimal],
            ]
        ] = []
        for left_index, left in enumerate(leg_pool):
            for right in leg_pool[left_index + 1 :]:
                if self._fixture_match_key(left[1].fixture) == self._fixture_match_key(
                    right[1].fixture
                ):
                    continue
                if self._bookmaker_identity(left[2].bookmaker) != self._bookmaker_identity(
                    right[2].bookmaker
                ):
                    continue
                if self._bookmaker_identity(left[2].bookmaker) is None:
                    continue
                combined_odds = left[2].decimal_odds * right[2].decimal_odds
                if combined_odds < self._forced_min_combined_odds:
                    continue
                combined_probability = left[3] * right[3]
                target_odds = (self._forced_min_combined_odds + Decimal(".30")).quantize(
                    Decimal(".01"), rounding=ROUND_HALF_UP
                )
                closeness_penalty = abs(combined_odds - target_odds) * Decimal("12")
                score = (
                    combined_probability * Decimal("160")
                    + left[0]
                    + right[0]
                    - closeness_penalty
                ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                pair = (score, combined_probability, combined_odds, left, right)
                if combined_odds <= self._forced_max_combined_odds:
                    viable_pairs.append(pair)
                else:
                    fallback_pairs.append(pair)
        pair_pool = viable_pairs or fallback_pairs
        if not pair_pool:
            return (), ()
        _, combined_probability, combined_odds, left, right = max(
            pair_pool, key=lambda item: item[0]
        )
        selections = tuple(
            self._forced_selection(run_id, candidate, quote, probability, edge, now)
            for _, candidate, quote, probability, edge in (left, right)
        )
        ticket = CouponTicket(
            kind="double",
            label="Günlük piyasa ikilisi",
            selection_fixture_ids=tuple(item.fixture.id for item in selections),
            combined_probability=combined_probability.quantize(
                Decimal(".000001"), rounding=ROUND_HALF_UP
            ),
            combined_decimal_odds=combined_odds.quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            ),
            probability_source="bookmaker_consensus",
            odds_source="best_bookmaker_quotes",
            risk_label="orta" if combined_probability >= Decimal(".55") else "yüksek",
        )
        return selections, (ticket,)

    def _market_learning_penalties(self) -> dict[str, Decimal]:
        """Reduce forced-mode exposure to markets with enough negative settled evidence.

        A small sample never bans a market. Once a market has at least four
        settled selections and both hit rate and flat-stake ROI are negative,
        it receives a transparent ranking penalty on the next daily run.
        """
        repository = getattr(self, "_repository", None)
        if repository is None:
            return {}
        try:
            performance = repository.performance()
        except (AttributeError, RuntimeError, ValueError):
            return {}
        penalties: dict[str, Decimal] = {}
        for market in performance.by_market:
            if (
                market.settled >= 4
                and market.hit_rate is not None
                and market.equal_stake_roi is not None
                and market.hit_rate <= Decimal(".50")
                and market.equal_stake_roi < 0
            ):
                penalties[market.market_key] = Decimal("14")
        return penalties

    @classmethod
    def _dedupe_candidates_by_match(
        cls, candidates: tuple[AutoCandidate, ...]
    ) -> tuple[AutoCandidate, ...]:
        seen: set[tuple[str, str]] = set()
        unique: list[AutoCandidate] = []
        for candidate in candidates:
            key = cls._fixture_match_key(candidate.fixture)
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return tuple(unique)

    @staticmethod
    def _fixture_match_key(fixture: CanonicalFixture) -> tuple[str, str]:
        teams = sorted(
            (
                AutoCouponService._team_signature(fixture.home_team),
                AutoCouponService._team_signature(fixture.away_team),
            )
        )
        return teams[0], teams[1]

    @staticmethod
    def _team_signature(team_name: str) -> str:
        normalized = unicodedata.normalize("NFKD", team_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        tokens = [
            token
            for token in re.sub(r"[^a-z0-9]+", " ", ascii_name.lower()).split()
            if token not in TEAM_SIGNATURE_STOPWORDS
        ]
        return "".join(tokens) or ascii_name.lower().strip()

    @staticmethod
    def _bookmaker_identity(bookmaker: str | None) -> str | None:
        normalized = " ".join((bookmaker or "").casefold().split())
        return normalized or None

    def _forced_selection(
        self,
        run_id: UUID,
        candidate: AutoCandidate,
        quote: MarketQuote,
        probability: Decimal,
        edge: Decimal,
        now: datetime,
    ) -> CouponSelection:
        pick = self._pick_key(quote)
        model_fair_odds = (Decimal("1") / probability).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )
        value_score = (
            probability * Decimal("70")
            + self._market_depth_bonus(quote.market_key) * Decimal("2")
            + min(quote.decimal_odds, Decimal("2.20")) * Decimal("5")
        ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        return CouponSelection(
            fixture=candidate.fixture,
            league=candidate.league,
            analysis_run_id=None,
            lock_id=None,
            pick=pick,
            market_key=quote.market_key,
            market_label=quote.market_label,
            outcome_label=self._selection_label(quote),
            market_description=quote.description,
            line=quote.point,
            probability=probability,
            model_fair_odds=model_fair_odds,
            market_decimal_odds=quote.decimal_odds,
            market_fair_probability=quote.fair_probability,
            edge=edge,
            bookmaker_count=quote.bookmaker_count,
            bookmaker=quote.bookmaker,
            price_observed_at=quote.observed_at,
            confidence=min(Decimal(".72"), Decimal(".42") + probability / Decimal("3")),
            value_score=value_score,
            reason=(
                "Günlük piyasa modu: strict model değer kapısı boş kaldığı için gerçek "
                f"oranlı {quote.market_label} / {self._selection_label(quote)} bacağı seçildi; "
                f"marjı temizlenmiş bookmaker konsensüsü "
                f"%{(probability * 100).quantize(Decimal('.1'))}."
            ),
            uncertainty=(
                "Bu oran bağımsız model tahmini veya %70 garanti iddiası değildir; maç önü "
                "haber, kadro ve piyasa kayması kapanışa kadar değişebilir."
            ),
            rationale=DecisionRationale(
                market_thesis=(
                    "Strict model kuponu çıkmadığında günlük kayıt için en yüksek puanlı "
                    "gerçek oranlı piyasa bacaklarından biri seçildi."
                ),
                supporting_evidence=(
                    f"{candidate.league.name} izin listesinde",
                    f"{quote.bookmaker or quote.provider} kaynağında alınabilir oran",
                    f"{quote.bookmaker_count} bookmaker ile piyasa konsensüsü",
                    f"Aday skoru {candidate.auto_score}/100",
                ),
                counter_evidence=(
                    "Strict %70+ değer kapısı geçilmedi",
                    "Bu seçim bağımsız derin model kilidi değil, piyasa-temelli günlük kupondur",
                ),
                price_rationale=(
                    f"Kilit anı oranı {quote.decimal_odds}; marjı temizlenmiş piyasa "
                    f"olasılığı %{(quote.fair_probability * 100).quantize(Decimal('.1'))}."
                ),
                invalidation_conditions=(
                    "Kadro veya sakatlık haberi ters yönde değişirse",
                    "Oran hedef bandın dışına sert kayarsa",
                    "Provider kimliği veya maç eşleşmesi sonradan uyuşmazlık gösterirse",
                ),
                model_disagreement=(
                    f"Konsensüs edge %{(edge * 100).quantize(Decimal('.1'))}; bağımsız model "
                    "edge'i veya strict değer kanıtı sayılmaz."
                ),
                evidence_cutoff_at=now,
            ),
        )

    @classmethod
    def _tickets(cls, selections: tuple[CouponSelection, ...]) -> tuple[CouponTicket, ...]:
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
            bookmaker_ids = tuple(cls._bookmaker_identity(item.bookmaker) for item in group)
            if any(bookmaker is None for bookmaker in bookmaker_ids):
                continue
            if required_count > 1 and len(set(bookmaker_ids)) != 1:
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
                    odds_source="best_bookmaker_quotes",
                    risk_label=risk,
                )
            )
        return tuple(tickets)
