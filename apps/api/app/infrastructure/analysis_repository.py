import hashlib
import json
from typing import Any, Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import Engine, create_engine, text

from app.domain.analysis import (
    PRE_MATCH_STAGES,
    AnalysisEvidenceDossier,
    AnalysisRunView,
    FinalForecast,
    PredictionLockManifest,
    PredictionLockView,
    StageView,
)
from app.domain.deep_evidence import DeepFootballEvidence
from app.domain.fixtures import CanonicalFixture
from app.infrastructure.lock_object_store import LockObjectStore, NullLockObjectStore


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AnalysisRepository(Protocol):
    def ensure_fixture(self, fixture: CanonicalFixture) -> None: ...

    def save_started(
        self,
        run: AnalysisRunView,
        idempotency_key: str,
        request_hash: str,
        evidence: DeepFootballEvidence | None,
        stage_outputs: dict[str, dict[str, object]],
    ) -> None: ...

    def save_locked(
        self,
        run: AnalysisRunView,
        manifest: PredictionLockManifest,
        manifest_sha256: str,
    ) -> None: ...

    def load_run(self, run_id: UUID) -> AnalysisRunView | None: ...

    def load_lock(self, lock_id: UUID) -> PredictionLockView | None: ...

    def load_idempotency(self, idempotency_key: str) -> tuple[str, UUID] | None: ...

    def load_evidence(self, run_id: UUID) -> AnalysisEvidenceDossier | None: ...


class NullAnalysisRepository:
    def ensure_fixture(self, fixture: CanonicalFixture) -> None:
        del fixture

    def save_started(
        self,
        run: AnalysisRunView,
        idempotency_key: str,
        request_hash: str,
        evidence: DeepFootballEvidence | None,
        stage_outputs: dict[str, dict[str, object]],
    ) -> None:
        del run, idempotency_key, request_hash, evidence, stage_outputs

    def save_locked(
        self,
        run: AnalysisRunView,
        manifest: PredictionLockManifest,
        manifest_sha256: str,
    ) -> None:
        del run, manifest, manifest_sha256

    def load_run(self, run_id: UUID) -> AnalysisRunView | None:
        del run_id
        return None

    def load_lock(self, lock_id: UUID) -> PredictionLockView | None:
        del lock_id
        return None

    def load_idempotency(self, idempotency_key: str) -> tuple[str, UUID] | None:
        del idempotency_key
        return None

    def load_evidence(self, run_id: UUID) -> AnalysisEvidenceDossier | None:
        del run_id
        return None


class PostgresAnalysisRepository:
    def __init__(
        self,
        database_url: str,
        object_store: LockObjectStore | None = None,
    ) -> None:
        self._engine: Engine = create_engine(database_url, pool_pre_ping=True)
        self._object_store = object_store or NullLockObjectStore()

    def ensure_fixture(self, fixture: CanonicalFixture) -> None:
        sport_id = UUID("92e3fa97-f0c3-5298-83f7-1bf958ad4879")
        competition_id = uuid5(
            NAMESPACE_URL, f"miron-baba-ai:competition:{fixture.competition_key}"
        )
        home_team_id = uuid5(
            NAMESPACE_URL,
            f"miron-baba-ai:team:{fixture.source_provider}:{fixture.home_team}",
        )
        away_team_id = uuid5(
            NAMESPACE_URL,
            f"miron-baba-ai:team:{fixture.source_provider}:{fixture.away_team}",
        )
        observed_at = fixture.observed_at or fixture.kickoff_at
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO sports (id, sport_key, plugin_key)
                VALUES (:id, 'football', 'football.v1')
                ON CONFLICT (sport_key) DO NOTHING
                """),
                {"id": sport_id},
            )
            connection.execute(
                text("""
                INSERT INTO competitions (id, sport_id, competition_key, name)
                VALUES (:id, :sport_id, :competition_key, :name)
                ON CONFLICT (sport_id, competition_key)
                DO UPDATE SET name = EXCLUDED.name, updated_at = now()
                """),
                {
                    "id": competition_id,
                    "sport_id": sport_id,
                    "competition_key": fixture.competition_key,
                    "name": fixture.competition_name,
                },
            )
            connection.execute(
                text("""
                INSERT INTO teams (id, sport_id, name)
                VALUES (:id, :sport_id, :name)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = now()
                """),
                [
                    {"id": home_team_id, "sport_id": sport_id, "name": fixture.home_team},
                    {"id": away_team_id, "sport_id": sport_id, "name": fixture.away_team},
                ],
            )
            connection.execute(
                text("""
                INSERT INTO fixtures (
                  id, sport_id, competition_id, home_team_id, away_team_id,
                  kickoff_at, status
                ) VALUES (
                  :id, :sport_id, :competition_id, :home_team_id, :away_team_id,
                  :kickoff_at, :status
                ) ON CONFLICT (id) DO UPDATE SET
                  competition_id = EXCLUDED.competition_id,
                  home_team_id = EXCLUDED.home_team_id,
                  away_team_id = EXCLUDED.away_team_id,
                  kickoff_at = EXCLUDED.kickoff_at,
                  status = EXCLUDED.status,
                  updated_at = now(),
                  row_version = fixtures.row_version + 1
                """),
                {
                    "id": fixture.id,
                    "sport_id": sport_id,
                    "competition_id": competition_id,
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "kickoff_at": fixture.kickoff_at,
                    "status": fixture.status,
                },
            )
            connection.execute(
                text("""
                INSERT INTO fixture_versions (
                  fixture_id, version, kickoff_at, status, observed_at
                ) VALUES (:fixture_id, 1, :kickoff_at, :status, :observed_at)
                ON CONFLICT (fixture_id, version) DO UPDATE SET
                  kickoff_at = EXCLUDED.kickoff_at,
                  status = EXCLUDED.status,
                  observed_at = EXCLUDED.observed_at
                """),
                {
                    "fixture_id": fixture.id,
                    "kickoff_at": fixture.kickoff_at,
                    "status": fixture.status,
                    "observed_at": observed_at,
                },
            )

    def save_started(
        self,
        run: AnalysisRunView,
        idempotency_key: str,
        request_hash: str,
        evidence: DeepFootballEvidence | None,
        stage_outputs: dict[str, dict[str, object]],
    ) -> None:
        config = {
            "schema_version": "config-snapshot.v1",
            "mode": run.forecast.analysis_provider,
            "model_ids": run.forecast.model_ids,
        }
        config_json = canonical_json(config)
        config_sha256 = sha256_text(config_json)
        config_snapshot_id = uuid5(NAMESPACE_URL, f"miron-baba-ai:config:{config_sha256}")
        prompt_bundle_version = (
            "gemini-ensemble.v1"
            if run.forecast.analysis_provider == "google_gemini"
            else "mock-prompts.v1"
        )
        forecast_json = canonical_json(run.forecast.model_dump(mode="json"))
        forecast_id = self._forecast_id(run.run_id)
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO config_snapshots (id, schema_version, config_json, sha256)
                VALUES (:id, 'config-snapshot.v1', CAST(:payload AS jsonb), :sha256)
                ON CONFLICT DO NOTHING
                """),
                {
                    "id": config_snapshot_id,
                    "payload": config_json,
                    "sha256": config_sha256,
                },
            )
            connection.execute(
                text("""
                INSERT INTO idempotency_records (
                  workspace_id, route, caller_key, request_hash,
                  status, resource_id
                ) VALUES (
                  'personal-local', '/api/v1/analysis-runs', :caller_key,
                  :request_hash, 'completed', :resource_id
                ) ON CONFLICT (workspace_id, route, caller_key) DO NOTHING
                """),
                {
                    "caller_key": idempotency_key,
                    "request_hash": request_hash,
                    "resource_id": run.run_id,
                },
            )
            connection.execute(
                text("""
                INSERT INTO analysis_runs (
                  id, fixture_id, state, cutoff_at, kickoff_at_snapshot,
                  config_snapshot_id, prompt_bundle_version, actual_cost_usd,
                  correlation_id, created_at, updated_at
                ) VALUES (
                  :id, :fixture_id, :state, :cutoff_at, :kickoff_at,
                  :config_id, :prompt_bundle_version, :cost, :correlation_id,
                  :created_at, :created_at
                ) ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": run.run_id,
                    "fixture_id": run.fixture_id,
                    "state": run.state,
                    "cutoff_at": run.cutoff_at,
                    "kickoff_at": run.kickoff_at_snapshot,
                    "config_id": config_snapshot_id,
                    "prompt_bundle_version": prompt_bundle_version,
                    "cost": run.actual_cost_usd,
                    "correlation_id": run.correlation_id,
                    "created_at": run.created_at,
                },
            )
            connection.execute(
                text("""
                INSERT INTO forecast_versions (
                  id, analysis_run_id, version, forecast_json, forecast_sha256
                ) VALUES (
                  :id, :run_id, 1, CAST(:forecast AS jsonb), :sha256
                ) ON CONFLICT DO NOTHING
                """),
                {
                    "id": forecast_id,
                    "run_id": run.run_id,
                    "forecast": forecast_json,
                    "sha256": sha256_text(forecast_json),
                },
            )
            stage_rows = [
                {
                    "run_id": run.run_id,
                    "stage_id": stage.stage_id,
                    "status": stage.status,
                    "input_hash": sha256_text(f"{run.run_id}:{stage.stage_id}:v1"),
                    "output_hash": sha256_text(stage.model_dump_json()),
                    "started_at": stage.started_at,
                    "completed_at": stage.completed_at,
                    "cost": stage.cost_usd,
                    "summary": stage.summary,
                    "output": canonical_json(
                        stage_outputs.get(stage.stage_id, {"summary": stage.summary})
                    ),
                }
                for stage in run.stages
            ]
            connection.execute(
                text("""
                INSERT INTO stage_runs (
                  analysis_run_id, stage_id, status, input_hash, output_hash,
                  started_at, completed_at, cost_usd, summary
                  , output_json
                ) VALUES (
                  :run_id, :stage_id, :status, :input_hash, :output_hash,
                  :started_at, :completed_at, :cost, :summary, CAST(:output AS jsonb)
                ) ON CONFLICT DO NOTHING
                """),
                stage_rows,
            )
            if evidence is not None:
                evidence_json = canonical_json(evidence.model_dump(mode="json"))
                connection.execute(
                    text("""
                    INSERT INTO analysis_evidence_snapshots (
                      analysis_run_id, provider, observed_at, coverage_json,
                      evidence_json, evidence_sha256
                    ) VALUES (
                      :run_id, :provider, :observed_at, CAST(:coverage AS jsonb),
                      CAST(:evidence AS jsonb), :sha256
                    ) ON CONFLICT (analysis_run_id) DO NOTHING
                    """),
                    {
                        "run_id": run.run_id,
                        "provider": evidence.provider,
                        "observed_at": evidence.observed_at,
                        "coverage": canonical_json(evidence.coverage),
                        "evidence": evidence_json,
                        "sha256": sha256_text(evidence_json),
                    },
                )
            connection.execute(
                text("""
                INSERT INTO run_state_transitions (
                  analysis_run_id, from_state, to_state, reason_code,
                  actor_type, actor_id, occurred_at, correlation_id
                ) VALUES (
                  :run_id, NULL, :state, 'ANALYSIS_CREATED',
                  'system', 'analysis-service', :occurred_at, :correlation_id
                ) ON CONFLICT DO NOTHING
                """),
                {
                    "run_id": run.run_id,
                    "state": run.state,
                    "occurred_at": run.created_at,
                    "correlation_id": run.correlation_id,
                },
            )

    def save_locked(
        self,
        run: AnalysisRunView,
        manifest: PredictionLockManifest,
        manifest_sha256: str,
    ) -> None:
        if run.lock_id is None:
            raise ValueError("LOCK_ID_REQUIRED")
        manifest_json = canonical_json(manifest.model_dump(mode="json"))
        object_uri = self._object_store.put_manifest(
            run.lock_id,
            manifest_sha256,
            manifest_json,
        )
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO prediction_locks (
                  id, analysis_run_id, forecast_version_id, cutoff_at,
                  locked_at, kickoff_at_snapshot, manifest_json,
                  manifest_sha256, object_uri
                ) VALUES (
                  :id, :run_id, :forecast_id, :cutoff_at, :locked_at,
                  :kickoff_at, CAST(:manifest AS jsonb), :sha256, :object_uri
                ) ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": run.lock_id,
                    "run_id": run.run_id,
                    "forecast_id": self._forecast_id(run.run_id),
                    "cutoff_at": manifest.cutoff_at,
                    "locked_at": manifest.locked_at,
                    "kickoff_at": manifest.kickoff_at_snapshot,
                    "manifest": manifest_json,
                    "sha256": manifest_sha256,
                    "object_uri": object_uri,
                },
            )
            connection.execute(
                text("""
                UPDATE analysis_runs
                SET state = 'LOCKED', updated_at = :locked_at, row_version = row_version + 1
                WHERE id = :run_id
                """),
                {"run_id": run.run_id, "locked_at": manifest.locked_at},
            )
            connection.execute(
                text("""
                INSERT INTO run_state_transitions (
                  analysis_run_id, from_state, to_state, reason_code,
                  actor_type, actor_id, occurred_at, correlation_id
                ) VALUES (
                  :run_id, 'LOCKING', 'LOCKED', 'PREDICTION_LOCKED',
                  'system', 'lock-controller', :occurred_at, :correlation_id
                ) ON CONFLICT DO NOTHING
                """),
                {
                    "run_id": run.run_id,
                    "occurred_at": manifest.locked_at,
                    "correlation_id": run.correlation_id,
                },
            )

    def load_run(self, run_id: UUID) -> AnalysisRunView | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("""
                SELECT ar.*, fv.forecast_json, pl.id AS lock_id,
                       pl.manifest_sha256
                FROM analysis_runs ar
                JOIN forecast_versions fv
                  ON fv.analysis_run_id = ar.id AND fv.version = 1
                LEFT JOIN prediction_locks pl ON pl.analysis_run_id = ar.id
                WHERE ar.id = :run_id
                """),
                    {"run_id": run_id},
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            stage_rows = (
                connection.execute(
                    text("""
                SELECT stage_id, status, started_at, completed_at, cost_usd, summary
                FROM stage_runs WHERE analysis_run_id = :run_id
                ORDER BY stage_id
                """),
                    {"run_id": run_id},
                )
                .mappings()
                .all()
            )
        stage_names = dict(PRE_MATCH_STAGES)
        stages = tuple(
            StageView(
                stage_id=str(stage["stage_id"]),
                name=stage_names[str(stage["stage_id"])],
                status=cast(Any, stage["status"]),
                summary=str(stage["summary"]),
                started_at=cast(Any, stage["started_at"]),
                completed_at=cast(Any, stage["completed_at"]),
                cost_usd=cast(Any, stage["cost_usd"]),
            )
            for stage in stage_rows
        )
        forecast = FinalForecast.model_validate(row["forecast_json"])
        return AnalysisRunView(
            run_id=cast(Any, row["id"]),
            fixture_id=cast(Any, row["fixture_id"]),
            state=cast(Any, row["state"]),
            cutoff_at=cast(Any, row["cutoff_at"]),
            kickoff_at_snapshot=cast(Any, row["kickoff_at_snapshot"]),
            stages=stages,
            forecast=forecast,
            actual_cost_usd=cast(Any, row["actual_cost_usd"]),
            correlation_id=cast(Any, row["correlation_id"]),
            created_at=cast(Any, row["created_at"]),
            lock_id=cast(Any, row["lock_id"]),
            lock_sha256=cast(Any, row["manifest_sha256"]),
        )

    def load_lock(self, lock_id: UUID) -> PredictionLockView | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("""
                SELECT id, analysis_run_id, manifest_json, manifest_sha256, object_uri
                FROM prediction_locks WHERE id = :lock_id
                """),
                    {"lock_id": lock_id},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return None
        return PredictionLockView(
            lock_id=cast(Any, row["id"]),
            analysis_run_id=cast(Any, row["analysis_run_id"]),
            manifest=PredictionLockManifest.model_validate(row["manifest_json"]),
            manifest_sha256=str(row["manifest_sha256"]),
            object_uri=str(row["object_uri"]),
        )

    def load_idempotency(self, idempotency_key: str) -> tuple[str, UUID] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("""
                    SELECT request_hash, resource_id
                    FROM idempotency_records
                    WHERE workspace_id = 'personal-local'
                      AND route = '/api/v1/analysis-runs'
                      AND caller_key = :caller_key
                    """),
                    {"caller_key": idempotency_key},
                )
                .mappings()
                .one_or_none()
            )
        if row is None or row["resource_id"] is None:
            return None
        return str(row["request_hash"]), cast(Any, row["resource_id"])

    def load_evidence(self, run_id: UUID) -> AnalysisEvidenceDossier | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("""
                    SELECT provider, observed_at, coverage_json, evidence_json,
                           evidence_sha256
                    FROM analysis_evidence_snapshots
                    WHERE analysis_run_id = :run_id
                    """),
                    {"run_id": run_id},
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            stage_rows = (
                connection.execute(
                    text("""
                    SELECT stage_id, output_json
                    FROM stage_runs
                    WHERE analysis_run_id = :run_id
                    ORDER BY stage_id
                    """),
                    {"run_id": run_id},
                )
                .mappings()
                .all()
            )
        return AnalysisEvidenceDossier(
            analysis_run_id=run_id,
            provider=str(row["provider"]),
            observed_at=cast(Any, row["observed_at"]),
            coverage=cast(Any, row["coverage_json"]),
            evidence=cast(Any, row["evidence_json"]),
            evidence_sha256=str(row["evidence_sha256"]),
            stage_outputs={
                str(stage["stage_id"]): cast(dict[str, object], stage["output_json"])
                for stage in stage_rows
            },
        )

    @staticmethod
    def _forecast_id(run_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"miron-baba-ai:forecast:{run_id}:1")


def _stage_summary(stage_id: str) -> str:
    summaries = {
        "S00": "Kimlik, cutoff ve bütçe doğrulandı.",
        "S15": "Elo, Poisson ve piyasa-prior mock dağılımları üretildi.",
        "S27": "İlk nihai olasılık vektörü Chief tarafından üretildi.",
        "S28": "Final Critic mock tahmini kontrollü yayıma onayladı.",
        "S30": "Lock manifesti için bütünlük paketi hazır.",
    }
    return summaries.get(stage_id, "Kesme zamanına uygun yapılandırılmış mock rapor tamamlandı.")
