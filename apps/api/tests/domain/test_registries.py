from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.registries import ModelRegistry, ModelRoute
from app.infrastructure.config_loader import load_model_registry, load_provider_registry


def test_model_registry_contains_only_verified_gemini_routes() -> None:
    registry = load_model_registry(Path("/workspace/config/models.yaml"))
    assert len(registry.routes) == 4
    assert {route.provider for route in registry.routes.values()} == {"google_gemini"}
    assert all(route.model_id.startswith("gemini-") for route in registry.routes.values())
    route = registry.assert_route_eligible(
        "committee", {"structured_output", "thinking"}, datetime(2026, 8, 22, tzinfo=UTC)
    )
    assert route.model_id == "gemini-3.5-flash"


def test_expired_or_unknown_price_model_is_rejected() -> None:
    now = datetime(2026, 8, 22, tzinfo=UTC)
    route = ModelRoute(
        provider="test",
        model_id="test-1",
        capabilities=frozenset({"structured_output"}),
        input_usd_per_mtok=Decimal("1"),
        output_usd_per_mtok=Decimal("2"),
        max_calls_per_run=1,
    )
    registry = ModelRegistry(
        schema_version="model-registry.v1",
        verified_at=now - timedelta(days=8),
        verification_expires_at=now - timedelta(days=1),
        currency="USD",
        routes={"committee": route},
        policies={},
    )
    with pytest.raises(ValueError, match="MODEL_VERIFICATION_EXPIRED"):
        registry.assert_route_eligible("committee", {"structured_output"}, now)


def test_only_user_approved_read_providers_are_enabled() -> None:
    registry = load_provider_registry(Path("/workspace/config/providers.yaml"))
    registry.require_enabled("mock_fixture", "GET")
    registry.require_enabled("openligadb", "GET")
    registry.require_enabled("football_data", "GET")
    registry.require_enabled("the_odds_api", "GET")
    with pytest.raises(PermissionError, match="PROVIDER_METHOD_FORBIDDEN"):
        registry.require_enabled("the_odds_api", "POST")
