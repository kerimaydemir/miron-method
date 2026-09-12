from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from app.domain.analysis import PredictionLockView
from app.domain.post_match import (
    AutopsyView,
    MatchResult,
    ValidatedLesson,
    VarianceAttribution,
    result_outcome,
    score_locked_forecast,
    validate_lesson_statement,
)


class PostMatchRepository(Protocol):
    def load_by_lock(self, lock_id: UUID) -> AutopsyView | None: ...

    def save(self, autopsy: AutopsyView) -> None: ...


class NullPostMatchRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, AutopsyView] = {}

    def load_by_lock(self, lock_id: UUID) -> AutopsyView | None:
        return self._items.get(lock_id)

    def save(self, autopsy: AutopsyView) -> None:
        self._items.setdefault(autopsy.lock_id, autopsy)


class PostMatchService:
    def __init__(
        self,
        clock: Callable[[], datetime],
        repository: PostMatchRepository | None = None,
    ) -> None:
        self.clock = clock
        self.repository = repository or NullPostMatchRepository()

    def ingest(self, lock: PredictionLockView, result: MatchResult) -> AutopsyView:
        existing = self.repository.load_by_lock(lock.lock_id)
        if existing is not None:
            if existing.result != result:
                raise ValueError("RESULT_CONFLICT")
            return existing

        now = self.clock()
        if now < lock.manifest.kickoff_at_snapshot:
            raise ValueError("MATCH_NOT_STARTED")
        if result.fixture_id != lock.manifest.fixture_id:
            raise ValueError("FIXTURE_MISMATCH")
        if result.observed_at < lock.manifest.kickoff_at_snapshot:
            raise ValueError("RESULT_BEFORE_KICKOFF")
        if result.observed_at > now:
            raise ValueError("RESULT_FROM_FUTURE")

        outcome = result_outcome(result)
        top_label = max(
            lock.manifest.forecast.outcome_probabilities,
            key=lambda item: item.probability,
        ).outcome
        result_verdict = "top_label_correct" if top_label == outcome else "top_label_incorrect"
        pre_match_thesis = tuple(lock.manifest.forecast.decisive_evidence)
        uncertainty = "; ".join(lock.manifest.forecast.uncertainty_drivers)
        post_match_explanation = (
            f"Ana seçim ({top_label}) gerçekleşti. Skor, ön maç tezlerinin nedenlerini doğrulamaz; "
            "yine de başarı tek maçta model doğruluğunu kanıtlamaz."
            if result_verdict == "top_label_correct"
            else (
                f"Ana seçim ({top_label}) gerçekleşmedi; maç {outcome} sonucu verdi. "
                f"Analiz anında açıkça kayıtlı belirsizlikler: {uncertainty}. "
                "Bu fark sonuçtan geriye doğru yeni neden uydurmadan vaka hafızasına kaydedildi."
            )
        )
        variance = (
            VarianceAttribution(
                category="unknown",
                weight=Decimal("1"),
                rationale=(
                    "Yalnız final skoruyla şans, veri eksikliği veya taktik hata "
                    "ayrıştırılamaz; olay düzeyi kanıt olmadan nedensel pay atanmamıştır."
                ),
            ),
        )
        statement = (
            "Bu skor sonucu kilitli tahminle karşılaştırıldı; süreç kalitesi ve şans etkisi "
            "için olay düzeyi kanıt ve birden fazla maçta kalibrasyon incelemesi gereklidir."
        )
        validate_lesson_statement(statement)
        autopsy = AutopsyView(
            autopsy_id=uuid5(NAMESPACE_URL, f"miron-baba-ai:autopsy:{lock.lock_id}"),
            lock_id=lock.lock_id,
            analysis_run_id=lock.analysis_run_id,
            fixture_id=lock.manifest.fixture_id,
            pre_match_lock_sha256=lock.manifest_sha256,
            result=result,
            realized_outcome=outcome,
            predicted_outcome=top_label,
            brier_score=score_locked_forecast(lock, result),
            result_verdict=result_verdict,
            process_verdict="needs_review",
            pre_match_thesis=pre_match_thesis,
            post_match_explanation=post_match_explanation,
            variance=variance,
            lesson=ValidatedLesson(
                lesson_id=uuid5(NAMESPACE_URL, f"miron-baba-ai:lesson:{lock.lock_id}"),
                scope="football/post-match/outcome-only-review",
                statement=statement,
                confidence=Decimal("0"),
                supporting_lock_sha256=lock.manifest_sha256,
            ),
            created_at=now,
        )
        self.repository.save(autopsy)
        return autopsy

    def get(self, lock_id: UUID) -> AutopsyView:
        item = self.repository.load_by_lock(lock_id)
        if item is None:
            raise KeyError("AUTOPSY_NOT_FOUND")
        return item
