from contextlib import AbstractContextManager
from decimal import Decimal
from types import TracebackType
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import Engine

from app.domain.auto_coupon import AutoCouponRun
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
