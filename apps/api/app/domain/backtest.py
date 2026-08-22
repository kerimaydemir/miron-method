import hashlib
import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.quant import brier_score

FORBIDDEN_PRE_MATCH_FEATURES = frozenset(
    {
        "final_score",
        "post_match_xg",
        "closing_odds_after_cutoff",
        "confirmed_lineup_after_cutoff",
        "future_elo",
        "case_outcome_text",
    }
)


@dataclass(frozen=True, slots=True)
class TemporalFeature:
    name: str
    value: Decimal | str
    knowledge_time: datetime

    def __post_init__(self) -> None:
        if self.knowledge_time.tzinfo is None:
            raise ValueError("knowledge_time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class BacktestCase:
    fixture_id: UUID
    kickoff_at: datetime
    cutoff_at: datetime
    probabilities: tuple[Decimal, Decimal, Decimal]
    realized_index: int
    features: tuple[TemporalFeature, ...]

    def __post_init__(self) -> None:
        if self.kickoff_at.tzinfo is None or self.cutoff_at.tzinfo is None:
            raise ValueError("backtest timestamps must be timezone-aware")
        if self.cutoff_at >= self.kickoff_at:
            raise ValueError("cutoff must precede kickoff")


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    train: tuple[BacktestCase, ...]
    test: tuple[BacktestCase, ...]


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    case_count: int
    mean_brier: Decimal
    mean_log_loss: Decimal


def assert_no_lookahead(case: BacktestCase) -> None:
    for feature in case.features:
        if feature.name in FORBIDDEN_PRE_MATCH_FEATURES:
            raise ValueError(f"LEAKAGE_SENTINEL:{feature.name}")
        if feature.knowledge_time > case.cutoff_at:
            raise ValueError(f"LOOKAHEAD_DETECTED:{feature.name}")


def walk_forward_folds(
    cases: tuple[BacktestCase, ...], min_train_size: int, test_size: int
) -> tuple[WalkForwardFold, ...]:
    if min_train_size < 1 or test_size < 1:
        raise ValueError("fold sizes must be positive")
    ordered = tuple(sorted(cases, key=lambda item: item.kickoff_at))
    folds: list[WalkForwardFold] = []
    cursor = min_train_size
    while cursor < len(ordered):
        test = ordered[cursor : cursor + test_size]
        if not test:
            break
        train = ordered[:cursor]
        if train[-1].kickoff_at >= test[0].kickoff_at:
            raise ValueError("WALK_FORWARD_ORDER_VIOLATION")
        folds.append(WalkForwardFold(train=train, test=test))
        cursor += test_size
    return tuple(folds)


def evaluate_cases(cases: tuple[BacktestCase, ...]) -> BacktestMetrics:
    if not cases:
        raise ValueError("at least one test case is required")
    for case in cases:
        assert_no_lookahead(case)
    brier_values = tuple(brier_score(case.probabilities, case.realized_index) for case in cases)
    log_losses = tuple(
        Decimal(str(-math.log(float(case.probabilities[case.realized_index])))) for case in cases
    )
    count = Decimal(len(cases))
    return BacktestMetrics(
        case_count=len(cases),
        mean_brier=sum(brier_values, Decimal("0")) / count,
        mean_log_loss=sum(log_losses, Decimal("0")) / count,
    )


def shadow_variant(fixture_id: UUID, salt: str, variants: tuple[str, ...]) -> str:
    if not variants:
        raise ValueError("at least one variant is required")
    digest = hashlib.sha256(f"{fixture_id}:{salt}".encode()).digest()
    return variants[int.from_bytes(digest[:8], "big") % len(variants)]
