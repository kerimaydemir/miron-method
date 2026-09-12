from contextlib import AbstractContextManager
from datetime import UTC, datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import Engine

from app.domain.auto_coupon import TOP_LEAGUES, AutoCouponRun, CouponSelection, FunnelDecision
from app.domain.fixtures import CanonicalFixture
from app.infrastructure.auto_coupon_repository import PostgresAutoCouponRepository


class _Result:
    rowcount = 1


class _Connection:
    def execute(self, statement: object, params: object) -> _Result:
        del statement, params
        return _Result()


class _Begin(AbstractContextManager[_Connection]):
    def __init__(self) -> None:
        self.connection = _Connection()

    def __enter__(self) -> _Connection:
        return self.connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback


class _Engine:
    def begin(self) -> _Begin:
        return _Begin()


class _Run:
    run_id = uuid4()
    state = "completed"
    actual_cost_usd = Decimal("0")

    @staticmethod
    def model_dump(*, mode: str) -> dict[str, object]:
        del mode
        return {"run_id": str(_Run.run_id), "state": "completed"}


def test_update_run_inserts_legs_discovered_after_empty_journal(monkeypatch: Any) -> None:
    repository = PostgresAutoCouponRepository.__new__(PostgresAutoCouponRepository)
    repository._engine = cast(Engine, cast(Any, _Engine()))
    inserted: list[AutoCouponRun] = []
    monkeypatch.setattr(
        repository,
        "_insert_selections",
        lambda connection, run: inserted.append(run),
    )
    run = cast(AutoCouponRun, cast(Any, _Run()))

    repository.update_run(run)

    assert inserted == [run]


@pytest.mark.parametrize("has_row", [True, False])
@pytest.mark.parametrize("has_real_analysis", [True, False])
def test_load_replaces_stale_json_references_without_losing_settlement(
    has_row: bool, has_real_analysis: bool,
) -> None:
    now = datetime(2026, 9, 12, tzinfo=UTC)
    selection = CouponSelection(
        fixture=CanonicalFixture(
            id=uuid4(), competition_key="test:league", competition_name="Test League",
            home_team="Home Club", away_team="Away Club", kickoff_at=now,
            source_provider="openligadb",
        ),
        league=TOP_LEAGUES[0], analysis_run_id=uuid4(), lock_id=uuid4(), pick="home",
        probability=Decimal(".60"), model_fair_odds=Decimal("1.67"),
        confidence=Decimal(".60"), reason="Recorded evidence", uncertainty="Lineup uncertain",
    )
    rough = FunnelDecision(
        stage="rough", input_count=1, selected_fixture_ids=(selection.fixture.id,),
        eliminated_fixture_ids=(), rationale="Recorded shortlist", model_id="test-model",
    )
    run = AutoCouponRun(
        run_id=uuid4(), state="completed", source_mode="bookmaker_live", observed_at=now,
        covered_league_keys=(), initial_candidates=(), rough_decision=rough,
        critic_decision=rough.model_copy(update={"stage": "critic"}),
        selections=(selection,), tickets=(), rag_case_count=0, actual_cost_usd=Decimal("0"),
    )
    real_analysis = uuid4() if has_real_analysis else None
    real_lock = uuid4() if has_real_analysis else None

    class Rows:
        def __init__(self, rows: list[dict[str, object]]) -> None:
            self.rows = rows

        def mappings(self) -> "Rows":
            return self

        def one_or_none(self) -> dict[str, object]:
            return self.rows[0]

        def __iter__(self) -> Any:
            return iter(self.rows)

    class Connection(_Connection):
        def execute(self, statement: object, params: object) -> Any:
            if "SELECT run_json" in str(statement):
                return Rows([{"run_json": run.model_dump(mode="json"), "state": "settled"}])
            return Rows([{
                "fixture_id": selection.fixture.id, "settlement_status": "lost",
                "process_verdict": "insufficient_data", "final_home_score": 0,
                "final_away_score": 1, "post_match_json": {"explanation": "Away club won 0-1"},
                "analysis_run_id": real_analysis, "prediction_lock_id": real_lock,
            }] if has_row else [])

    class TestEngine:
        def connect(self) -> _Begin:
            context = _Begin()
            context.connection = Connection()
            return context

    repository = PostgresAutoCouponRepository.__new__(PostgresAutoCouponRepository)
    repository._engine = cast(Engine, cast(Any, TestEngine()))
    loaded = repository.load(run.run_id)
    assert loaded is not None
    restored = loaded.selections[0]
    assert restored.analysis_run_id == (real_analysis if has_row else None)
    assert restored.lock_id == (real_lock if has_row else None)
    assert restored.settlement_status == ("lost" if has_row else "pending")
    assert restored.final_home_score == (0 if has_row else None)
    assert restored.final_away_score == (1 if has_row else None)
    assert restored.probability == selection.probability
