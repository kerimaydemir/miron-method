from typing import Literal

from pydantic import BaseModel, ConfigDict


class AgentRolePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage: str
    name: str
    route: Literal["deterministic", "grounded_research", "normalization", "critic", "committee"]
    prediction_authorized: bool
    post_match_access: bool


class AgentRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["agent-registry.v1"]
    roles: dict[str, AgentRolePolicy]

    def validate_authority(self) -> None:
        if set(self.roles) != {f"A{index:02d}" for index in range(43)}:
            raise ValueError("agent registry must define exactly A00 through A42")
        authorized = {
            agent_id for agent_id, role in self.roles.items() if role.prediction_authorized
        }
        if authorized != {"A30", "A32"}:
            raise ValueError("only Chief and bounded Chief Revision may author final probabilities")
        if any(
            role.post_match_access
            for agent_id, role in self.roles.items()
            if int(agent_id[1:]) < 34
        ):
            raise ValueError("pre-match roles cannot access post-match data")


def enforce_prediction_authority(
    registry: AgentRegistry, agent_id: str, output_keys: set[str]
) -> None:
    role = registry.roles[agent_id]
    forbidden_keys = {"outcome_probabilities", "final_probability_vector", "selected_winner"}
    if output_keys & forbidden_keys and not role.prediction_authorized:
        raise PermissionError(f"PREDICTION_FORBIDDEN:{agent_id}")
