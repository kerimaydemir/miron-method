from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.budget import BudgetLedger, BudgetPolicy


def test_inv_009_hard_stop_accounts_for_concurrent_reservations() -> None:
    ledger = BudgetLedger(
        BudgetPolicy(
            monthly_cap_usd=Decimal("10"),
            run_soft_cap_usd=Decimal(".5"),
            run_hard_cap_usd=Decimal("2"),
        )
    )
    run_id = uuid4()
    ledger.reserve(run_id, "S18", Decimal("1.25"))
    with pytest.raises(RuntimeError, match="BUDGET_EXHAUSTED"):
        ledger.reserve(run_id, "S19", Decimal("1"))


def test_budget_replay_is_idempotent_and_release_returns_capacity() -> None:
    ledger = BudgetLedger(
        BudgetPolicy(
            monthly_cap_usd=Decimal("1"),
            run_soft_cap_usd=Decimal(".5"),
            run_hard_cap_usd=Decimal("1"),
        )
    )
    run_id = uuid4()
    first = ledger.reserve(run_id, "S01", Decimal(".8"))
    assert ledger.reserve(run_id, "S01", Decimal(".8")) == first
    ledger.release(run_id, "S01")
    ledger.reserve(run_id, "S02", Decimal("1"))
