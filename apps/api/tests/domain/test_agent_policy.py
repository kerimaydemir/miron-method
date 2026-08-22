from pathlib import Path

import pytest

from app.domain.agent_policy import enforce_prediction_authority
from app.infrastructure.config_loader import load_agent_registry


def test_inv_043_only_chief_roles_can_author_final_vector() -> None:
    registry = load_agent_registry(Path("/workspace/config/agents.yaml"))
    enforce_prediction_authority(registry, "A30", {"outcome_probabilities"})
    enforce_prediction_authority(registry, "A32", {"outcome_probabilities"})
    with pytest.raises(PermissionError, match="PREDICTION_FORBIDDEN:A21"):
        enforce_prediction_authority(registry, "A21", {"outcome_probabilities"})


def test_agent_registry_has_all_43_bounded_roles() -> None:
    registry = load_agent_registry(Path("/workspace/config/agents.yaml"))
    assert len(registry.roles) == 43
    assert registry.roles["A34"].post_match_access is True
