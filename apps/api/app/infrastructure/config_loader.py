from pathlib import Path

import yaml

from app.domain.agent_policy import AgentRegistry
from app.domain.registries import ModelRegistry, ProviderRegistry


def load_agent_registry(path: Path) -> AgentRegistry:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry = AgentRegistry.model_validate(payload)
    registry.validate_authority()
    return registry


def load_model_registry(path: Path) -> ModelRegistry:
    return ModelRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_provider_registry(path: Path) -> ProviderRegistry:
    return ProviderRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
