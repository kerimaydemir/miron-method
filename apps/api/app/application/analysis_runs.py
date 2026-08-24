import asyncio
import hashlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from app.application.gemini_analysis import GeminiAnalysisService
from app.domain.analysis import (
    PRE_MATCH_STAGES,
    AnalysisEvidenceDossier,
    AnalysisRunView,
    FinalForecast,
    OutcomeProbability,
    PredictionLockManifest,
    PredictionLockView,
    StageView,
)
from app.domain.deep_evidence import DeepEvidenceProvider
from app.domain.fixtures import CanonicalFixture, TriageFactors
from app.domain.ports import AnalysisFixtureProvider
from app.infrastructure.analysis_repository import (
    AnalysisRepository,
    NullAnalysisRepository,
    canonical_json,
)
from app.infrastructure.mock_fixture_provider import FEATURES, FIXTURES

logger = logging.getLogger(__name__)


class AnalysisRunService:
    required_deep_stage_ids = tuple(
        stage_id for stage_id, _ in PRE_MATCH_STAGES if stage_id != "S30"
    )

    def __init__(
        self,
        clock: Callable[[], datetime],
        repository: AnalysisRepository | None = None,
        analyzer: GeminiAnalysisService | None = None,
        fixture_provider: AnalysisFixtureProvider | None = None,
        deep_evidence_provider: DeepEvidenceProvider | None = None,
        analysis_timeout_seconds: int = 240,
    ) -> None:
        self.clock = clock
        self.repository = repository or NullAnalysisRepository()
        self.analyzer = analyzer
        self.fixture_provider = fixture_provider
        self.deep_evidence_provider = deep_evidence_provider
        self._analysis_timeout_seconds = analysis_timeout_seconds
        self._runs: dict[UUID, AnalysisRunView] = {}
        self._keys: dict[str, tuple[str, UUID]] = {}
        self._locks: dict[UUID, PredictionLockView] = {}
        self._evidence: dict[UUID, AnalysisEvidenceDossier] = {}
        self._lock = asyncio.Lock()

    @property
    def implemented_stage_ids(self) -> tuple[str, ...]:
        if self.analyzer is None:
            return ()
        return ("S00", *self.analyzer.covered_stage_ids)

    @property
    def deep_analysis_ready(self) -> bool:
        return self.deep_data_ready and set(self.required_deep_stage_ids).issubset(
            self.implemented_stage_ids
        )

    @property
    def deep_data_ready(self) -> bool:
        return bool(
            self.deep_evidence_provider is not None and self.deep_evidence_provider.available
        )

    async def start(
        self, fixture_id: UUID, idempotency_key: str, request_hash: str, correlation_id: UUID
    ) -> AnalysisRunView:
        async with self._lock:
            replay = self._keys.get(idempotency_key) or self.repository.load_idempotency(
                idempotency_key
            )
            if replay:
                if replay[0] != request_hash:
                    raise ValueError("IDEMPOTENCY_CONFLICT")
                replayed_run = self._runs.get(replay[1]) or self.repository.load_run(replay[1])
                if replayed_run is None:
                    raise ValueError("IDEMPOTENCY_RESOURCE_MISSING")
                self._keys[idempotency_key] = replay
                self._runs[replay[1]] = replayed_run
                return replayed_run
            if self.fixture_provider is not None:
                try:
                    fixture = await self.fixture_provider.get_fixture(fixture_id)
                except KeyError as error:
                    raise KeyError("FIXTURE_NOT_FOUND") from error
                try:
                    factors = await self.fixture_provider.features_for(fixture)
                except (
                    TimeoutError,
                    PermissionError,
                    KeyError,
                    RuntimeError,
                    ValueError,
                    httpx.HTTPError,
                ) as error:
                    logger.warning(
                        "Fixture feature enrichment unavailable; using degraded triage factors",
                        extra={
                            "fixture_id": str(fixture.id),
                            "error_type": type(error).__name__,
                            "error": str(error),
                        },
                    )
                    factors = self._degraded_factors(fixture)
            else:
                fixture_index = next(
                    (index for index, item in enumerate(FIXTURES) if item.id == fixture_id), None
                )
                if fixture_index is None:
                    raise KeyError("FIXTURE_NOT_FOUND")
                fixture = FIXTURES[fixture_index]
                factors = FEATURES[fixture_index]
            now = self.clock()
            if fixture.kickoff_at <= now:
                raise ValueError("INVALID_CUTOFF")
            run_id = uuid5(NAMESPACE_URL, f"miron-baba-ai:analysis:{idempotency_key}")
            deep_evidence = None
            if self.deep_data_ready and self.deep_evidence_provider is not None:
                try:
                    deep_evidence = await self.deep_evidence_provider.collect(fixture)
                except (
                    TimeoutError,
                    PermissionError,
                    KeyError,
                    RuntimeError,
                    ValueError,
                    httpx.HTTPError,
                ) as error:
                    logger.warning(
                        "Deep evidence unavailable; continuing with fixture and odds evidence",
                        extra={
                            "fixture_id": str(fixture.id),
                            "error_type": type(error).__name__,
                            "error": str(error),
                        },
                    )
            try:
                gemini_result = (
                    await asyncio.wait_for(
                        self.analyzer.analyze(fixture, factors, now, deep_evidence),
                        timeout=self._analysis_timeout_seconds,
                    )
                    if self.analyzer is not None
                    else None
                )
            except TimeoutError as error:
                logger.warning(
                    "Gemini analysis timed out",
                    extra={
                        "fixture_id": str(fixture.id),
                        "timeout_seconds": self._analysis_timeout_seconds,
                    },
                )
                raise RuntimeError("GEMINI_ANALYSIS_TIMED_OUT") from error
            stage_summaries = gemini_result.stage_summaries if gemini_result else {}
            stage_costs = gemini_result.stage_costs if gemini_result else {}
            completed_stage_ids = {"S00", "S30", *stage_summaries}
            stages = tuple(
                StageView(
                    stage_id=stage_id,
                    name=name,
                    status="completed" if stage_id in completed_stage_ids else "degraded",
                    summary=stage_summaries.get(
                        stage_id,
                        self._summary(stage_id, live_gemini=gemini_result is not None),
                    ),
                    started_at=now + timedelta(milliseconds=index * 3),
                    completed_at=now + timedelta(milliseconds=index * 3 + 2),
                    cost_usd=stage_costs.get(stage_id, Decimal("0")),
                )
                for index, (stage_id, name) in enumerate(PRE_MATCH_STAGES)
            )
            forecast = (
                gemini_result.forecast if gemini_result else self._mock_forecast(fixture.id, now)
            )
            run = AnalysisRunView(
                run_id=run_id,
                fixture_id=fixture.id,
                state="LOCKING",
                cutoff_at=now,
                kickoff_at_snapshot=fixture.kickoff_at,
                stages=stages,
                forecast=forecast,
                actual_cost_usd=(gemini_result.actual_cost_usd if gemini_result else Decimal("0")),
                correlation_id=correlation_id,
                created_at=now,
            )
            self._runs[run_id] = run
            self._keys[idempotency_key] = (request_hash, run_id)
            self.repository.ensure_fixture(fixture)
            stage_outputs = gemini_result.stage_outputs if gemini_result else {}
            self.repository.save_started(
                run,
                idempotency_key,
                request_hash,
                deep_evidence,
                stage_outputs,
            )
            if deep_evidence is not None:
                evidence_json = deep_evidence.model_dump(mode="json")
                self._evidence[run_id] = AnalysisEvidenceDossier(
                    analysis_run_id=run_id,
                    provider=deep_evidence.provider,
                    observed_at=deep_evidence.observed_at,
                    coverage=deep_evidence.coverage,
                    evidence=evidence_json,
                    evidence_sha256=hashlib.sha256(
                        canonical_json(evidence_json).encode()
                    ).hexdigest(),
                    stage_outputs=stage_outputs,
                )
            return run

    def get(self, run_id: UUID) -> AnalysisRunView:
        run = self._runs.get(run_id) or self.repository.load_run(run_id)
        if run is None:
            raise KeyError("RUN_NOT_FOUND")
        self._runs[run_id] = run
        return run

    async def lock(self, run_id: UUID) -> AnalysisRunView:
        async with self._lock:
            run = self.get(run_id)
            if run.state == "LOCKED":
                return run
            now = self.clock()
            if now >= run.kickoff_at_snapshot:
                raise ValueError("LOCK_AFTER_KICKOFF")
            manifest = PredictionLockManifest(
                analysis_run_id=run.run_id,
                fixture_id=run.fixture_id,
                cutoff_at=run.cutoff_at,
                locked_at=now,
                kickoff_at_snapshot=run.kickoff_at_snapshot,
                forecast=run.forecast,
            )
            digest = hashlib.sha256(
                canonical_json(manifest.model_dump(mode="json")).encode()
            ).hexdigest()
            locked = run.model_copy(
                update={
                    "state": "LOCKED",
                    "lock_id": uuid5(NAMESPACE_URL, f"miron-baba-ai:lock:{run_id}"),
                    "lock_sha256": digest,
                }
            )
            self.repository.save_locked(locked, manifest, digest)
            if locked.lock_id is None:
                raise ValueError("LOCK_ID_REQUIRED")
            persisted_lock = self.repository.load_lock(locked.lock_id)
            self._locks[locked.lock_id] = persisted_lock or PredictionLockView(
                lock_id=locked.lock_id,
                analysis_run_id=locked.run_id,
                manifest=manifest,
                manifest_sha256=digest,
                object_uri=f"memory://locks/{locked.lock_id}/{digest}.json",
            )
            self._runs[run_id] = locked
            return locked

    def get_lock(self, lock_id: UUID) -> PredictionLockView:
        lock = self._locks.get(lock_id) or self.repository.load_lock(lock_id)
        if lock is None:
            raise KeyError("LOCK_NOT_FOUND")
        self._locks[lock_id] = lock
        return lock

    def get_evidence(self, run_id: UUID) -> AnalysisEvidenceDossier:
        dossier = self._evidence.get(run_id) or self.repository.load_evidence(run_id)
        if dossier is None:
            raise KeyError("EVIDENCE_NOT_FOUND")
        self._evidence[run_id] = dossier
        return dossier

    @staticmethod
    def _degraded_factors(fixture: CanonicalFixture) -> TriageFactors:
        odds_backed = fixture.source_provider in {"the_odds_api", "odds_api_io", "api_football"}
        return TriageFactors(
            coverage_score=Decimal("0.45"),
            source_freshness_score=Decimal("0.45"),
            competitive_relevance_score=Decimal("0.75"),
            model_information_gain_score=Decimal("0.55"),
            market_coverage_score=Decimal("0.80") if odds_backed else Decimal("0.40"),
            lineup_uncertainty_resolvability=Decimal("0.35"),
            user_interest_score=Decimal("0.65"),
            historical_case_support=Decimal("0.35"),
            kickoff_time_practicality=Decimal("0.70"),
            estimated_cost_penalty=Decimal("0.12"),
            unresolved_identity_penalty=Decimal("0.20"),
            stale_data_penalty=Decimal("0.30"),
        )

    @staticmethod
    def _summary(stage_id: str, *, live_gemini: bool = False) -> str:
        if live_gemini:
            live_summaries = {
                "S00": "Fikstür kimliği, kesme zamanı ve Gemini bütçe sınırı doğrulandı.",
                "S30": "Değiştirilemez tahmin manifesti için bütünlük paketi hazırlandı.",
            }
            return live_summaries.get(
                stage_id,
                "Bu uzmanlık aşaması uygulanmadı veya doğrulanmış girdisi yok; sonuç degraded durumundadır.",
            )
        summaries = {
            "S00": "Kimlik, cutoff ve bütçe doğrulandı.",
            "S15": "Elo, Poisson ve piyasa-prior mock dağılımları üretildi.",
            "S27": "İlk nihai olasılık vektörü Chief tarafından üretildi.",
            "S28": "Final Critic mock tahmini kontrollü yayıma onayladı.",
            "S30": "Lock manifesti için bütünlük paketi hazır.",
        }
        return summaries.get(
            stage_id, "Kesme zamanına uygun yapılandırılmış mock rapor tamamlandı."
        )

    @staticmethod
    def _mock_forecast(fixture_id: UUID, now: datetime) -> FinalForecast:
        return FinalForecast(
            fixture_id=fixture_id,
            cutoff_at=now,
            outcome_probabilities=(
                OutcomeProbability(
                    outcome="home",
                    probability=Decimal(".44"),
                    lower=Decimal(".36"),
                    upper=Decimal(".52"),
                ),
                OutcomeProbability(
                    outcome="draw",
                    probability=Decimal(".29"),
                    lower=Decimal(".23"),
                    upper=Decimal(".35"),
                ),
                OutcomeProbability(
                    outcome="away",
                    probability=Decimal(".27"),
                    lower=Decimal(".20"),
                    upper=Decimal(".34"),
                ),
            ),
            expected_home_goals=Decimal("1.48"),
            expected_away_goals=Decimal("1.09"),
            confidence=Decimal(".61"),
            uncertainty_drivers=(
                "Kadrolar henüz doğrulanmadı",
                "Mock piyasa derinliği sınırlı",
            ),
            decisive_evidence=(
                "Elo ve Poisson tabanı ev tarafını önde tutuyor",
                "Dinlenme süresi dengeli",
            ),
            dissent_summary=("Beraberlik senaryosu düşük tempoda güçleniyor",),
        )


def utc_now() -> datetime:
    return datetime.now(UTC)
