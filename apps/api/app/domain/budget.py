from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    monthly_cap_usd: Decimal
    run_soft_cap_usd: Decimal
    run_hard_cap_usd: Decimal

    def __post_init__(self) -> None:
        if self.monthly_cap_usd <= 0 or self.run_hard_cap_usd <= 0:
            raise ValueError("budget caps must be positive")
        if self.run_soft_cap_usd > self.run_hard_cap_usd:
            raise ValueError("soft cap cannot exceed hard cap")


@dataclass(frozen=True, slots=True)
class Reservation:
    run_id: UUID
    stage_id: str
    amount_usd: Decimal


class BudgetLedger:
    def __init__(self, policy: BudgetPolicy) -> None:
        self.policy = policy
        self._monthly_actual = Decimal("0")
        self._reservations: dict[tuple[UUID, str], Reservation] = {}
        self._run_actual: dict[UUID, Decimal] = {}

    @property
    def monthly_committed(self) -> Decimal:
        return self._monthly_actual + sum(
            (item.amount_usd for item in self._reservations.values()), start=Decimal("0")
        )

    def reserve(self, run_id: UUID, stage_id: str, amount_usd: Decimal) -> Reservation:
        if amount_usd <= 0:
            raise ValueError("reservation must be positive")
        key = (run_id, stage_id)
        if key in self._reservations:
            if self._reservations[key].amount_usd != amount_usd:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return self._reservations[key]
        run_committed = self._run_actual.get(run_id, Decimal("0")) + sum(
            (item.amount_usd for item in self._reservations.values() if item.run_id == run_id),
            start=Decimal("0"),
        )
        if run_committed + amount_usd > self.policy.run_hard_cap_usd:
            raise RuntimeError("BUDGET_EXHAUSTED")
        if self.monthly_committed + amount_usd > self.policy.monthly_cap_usd:
            raise RuntimeError("BUDGET_EXHAUSTED")
        reservation = Reservation(run_id=run_id, stage_id=stage_id, amount_usd=amount_usd)
        self._reservations[key] = reservation
        return reservation

    def reconcile(self, run_id: UUID, stage_id: str, actual_usd: Decimal) -> None:
        key = (run_id, stage_id)
        reservation = self._reservations.pop(key, None)
        if reservation is None:
            raise KeyError("RESERVATION_NOT_FOUND")
        if actual_usd < 0 or actual_usd > reservation.amount_usd:
            raise ValueError("actual cost must be covered by reservation")
        self._monthly_actual += actual_usd
        self._run_actual[run_id] = self._run_actual.get(run_id, Decimal("0")) + actual_usd

    def release(self, run_id: UUID, stage_id: str) -> None:
        self._reservations.pop((run_id, stage_id), None)
