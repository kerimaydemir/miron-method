from uuid import UUID

from sqlalchemy import Engine, create_engine, text

from app.domain.post_match import AutopsyView
from app.infrastructure.analysis_repository import canonical_json


class PostgresPostMatchRepository:
    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url, pool_pre_ping=True)

    def load_by_lock(self, lock_id: UUID) -> AutopsyView | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("SELECT autopsy_json FROM autopsies WHERE prediction_lock_id = :lock_id"),
                    {"lock_id": lock_id},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else AutopsyView.model_validate(row["autopsy_json"])

    def save(self, autopsy: AutopsyView) -> None:
        payload = canonical_json(autopsy.model_dump(mode="json"))
        result_id = self._derived_id(autopsy.autopsy_id, "result")
        case_id = self._derived_id(autopsy.autopsy_id, "case")
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO match_results (
                  id, fixture_id, prediction_lock_id, home_score, away_score,
                  status, observed_at, source, result_version, result_json
                ) VALUES (
                  :id, :fixture_id, :lock_id, :home_score, :away_score,
                  'final', :observed_at, :source, 1, CAST(:result_json AS jsonb)
                ) ON CONFLICT (prediction_lock_id, result_version) DO NOTHING
                """),
                {
                    "id": result_id,
                    "fixture_id": autopsy.fixture_id,
                    "lock_id": autopsy.lock_id,
                    "home_score": autopsy.result.home_score,
                    "away_score": autopsy.result.away_score,
                    "observed_at": autopsy.result.observed_at,
                    "source": autopsy.result.source,
                    "result_json": canonical_json(autopsy.result.model_dump(mode="json")),
                },
            )
            connection.execute(
                text("""
                INSERT INTO autopsies (
                  id, prediction_lock_id, analysis_run_id, match_result_id,
                  pre_match_lock_sha256, brier_score, result_verdict,
                  process_verdict, autopsy_json, created_at
                ) VALUES (
                  :id, :lock_id, :run_id, :result_id, :lock_sha, :brier,
                  :result_verdict, :process_verdict, CAST(:payload AS jsonb), :created_at
                ) ON CONFLICT (prediction_lock_id) DO NOTHING
                """),
                {
                    "id": autopsy.autopsy_id,
                    "lock_id": autopsy.lock_id,
                    "run_id": autopsy.analysis_run_id,
                    "result_id": result_id,
                    "lock_sha": autopsy.pre_match_lock_sha256,
                    "brier": autopsy.brier_score,
                    "result_verdict": autopsy.result_verdict,
                    "process_verdict": autopsy.process_verdict,
                    "payload": payload,
                    "created_at": autopsy.created_at,
                },
            )
            connection.execute(
                text("""
                INSERT INTO variance_attributions (
                  autopsy_id, category, weight, rationale
                ) VALUES (:autopsy_id, :category, :weight, :rationale)
                ON CONFLICT (autopsy_id, category) DO NOTHING
                """),
                [
                    {
                        "autopsy_id": autopsy.autopsy_id,
                        "category": item.category,
                        "weight": item.weight,
                        "rationale": item.rationale,
                    }
                    for item in autopsy.variance
                ],
            )
            connection.execute(
                text("""
                INSERT INTO lessons (
                  id, autopsy_id, status, scope, statement, confidence,
                  hindsight_safe, supporting_lock_sha256, created_at, updated_at
                ) VALUES (
                  :id, :autopsy_id, 'validated', :scope, :statement, :confidence,
                  true, :lock_sha, :created_at, :created_at
                ) ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": autopsy.lesson.lesson_id,
                    "autopsy_id": autopsy.autopsy_id,
                    "scope": autopsy.lesson.scope,
                    "statement": autopsy.lesson.statement,
                    "confidence": autopsy.lesson.confidence,
                    "lock_sha": autopsy.pre_match_lock_sha256,
                    "created_at": autopsy.created_at,
                },
            )
            connection.execute(
                text("""
                INSERT INTO cases (
                  id, prediction_lock_id, autopsy_id, case_json, created_at
                ) VALUES (
                  :id, :lock_id, :autopsy_id, CAST(:payload AS jsonb), :created_at
                ) ON CONFLICT (prediction_lock_id) DO NOTHING
                """),
                {
                    "id": case_id,
                    "lock_id": autopsy.lock_id,
                    "autopsy_id": autopsy.autopsy_id,
                    "payload": payload,
                    "created_at": autopsy.created_at,
                },
            )
            search_text = " ".join(
                (
                    autopsy.predicted_outcome,
                    autopsy.realized_outcome,
                    autopsy.result_verdict,
                    *autopsy.pre_match_thesis,
                    autopsy.post_match_explanation,
                    autopsy.lesson.statement,
                    *(item.rationale for item in autopsy.variance),
                )
            )
            connection.execute(
                text("""
                INSERT INTO case_memory_chunks (
                  case_id, fixture_id, competition_key, home_team, away_team,
                  predicted_outcome, realized_outcome, result_verdict,
                  search_text, case_json
                )
                SELECT :case_id, f.id, c.competition_key, ht.name, at.name,
                       :predicted, :realized, :verdict, :search_text, CAST(:payload AS jsonb)
                FROM fixtures f
                JOIN competitions c ON c.id = f.competition_id
                JOIN teams ht ON ht.id = f.home_team_id
                JOIN teams at ON at.id = f.away_team_id
                WHERE f.id = :fixture_id
                ON CONFLICT (case_id) DO NOTHING
                """),
                {
                    "case_id": case_id,
                    "fixture_id": autopsy.fixture_id,
                    "predicted": autopsy.predicted_outcome,
                    "realized": autopsy.realized_outcome,
                    "verdict": autopsy.result_verdict,
                    "search_text": search_text,
                    "payload": payload,
                },
            )

    @staticmethod
    def _derived_id(seed: UUID, suffix: str) -> UUID:
        from uuid import NAMESPACE_URL, uuid5

        return uuid5(NAMESPACE_URL, f"miron-baba-ai:{suffix}:{seed}")
