from decimal import Decimal

from app.domain.fixtures import TriageFactors
from app.domain.scoring import worthwhile_score


def test_worthwhile_score_is_bounded_and_reproducible() -> None:
    values = {name: Decimal("1") for name in TriageFactors.model_fields}
    values.update(
        estimated_cost_penalty=Decimal("0"),
        unresolved_identity_penalty=Decimal("0"),
        stale_data_penalty=Decimal("0"),
    )
    assert worthwhile_score(TriageFactors(**values)) == 100
