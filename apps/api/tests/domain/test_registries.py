from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.registries import ModelRegistry, ModelRoute
from app.infrastructure.config_loader import load_model_registry, load_provider_registry


def test_model_registry_contains_explicit_trial_nvidia_routes() -> None:
    registry = load_model_registry(Path("/workspace/config/models.yaml"))
    assert set(registry.routes) == {
        "grounded_research", "normalization", "specialist", "critic", "committee", "final_critic"
    }
    assert {route.provider for route in registry.routes.values()} == {"nvidia_nim"}
    assert all(route.model_id.startswith("nvidia/") for route in registry.routes.values())
    assert all(route.billing_mode == "trial_rate_limited" for route in registry.routes.values())
    assert all(route.input_usd_per_mtok == 0 for route in registry.routes.values())
    assert all(route.output_usd_per_mtok == 0 for route in registry.routes.values())
    assert all("search_grounding" not in route.capabilities for route in registry.routes.values())
    route = registry.assert_route_eligible(
        "committee", {"structured_output", "thinking"}, datetime(2026, 9, 7, tzinfo=UTC)
    )
    assert route.model_id == "nvidia/nemotron-3-super-120b-a12b"
    with pytest.raises(ValueError, match="MODEL_CAPABILITY_MISSING"):
        registry.assert_route_eligible(
            "grounded_research", {"search_grounding"}, datetime(2026, 9, 7, tzinfo=UTC)
        )


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

    unknown_price = registry.model_copy(
        update={
            "verification_expires_at": now + timedelta(days=1),
            "routes": {"committee": route.model_copy(update={"input_usd_per_mtok": None})},
        }
    )
    with pytest.raises(ValueError, match="MODEL_PRICE_UNKNOWN"):
        unknown_price.assert_route_eligible("committee", {"structured_output"}, now)


@pytest.mark.parametrize("input_price,output_price", [(None, None), (".01", "0"), ("0", ".01")])
def test_trial_billing_cannot_hide_unknown_or_metered_prices(
    input_price: str | None, output_price: str | None
) -> None:
    with pytest.raises(ValueError, match="TRIAL_ROUTE_PRICE_MUST_BE_ZERO"):
        ModelRoute(
            provider="nvidia_nim",
            model_id="nvidia/test-model",
            capabilities=frozenset({"structured_output"}),
            billing_mode="trial_rate_limited",
            input_usd_per_mtok=Decimal(input_price) if input_price is not None else None,
            output_usd_per_mtok=Decimal(output_price) if output_price is not None else None,
            max_calls_per_run=1,
        )


def test_only_user_approved_read_providers_are_enabled() -> None:
    registry = load_provider_registry(Path("/workspace/config/providers.yaml"))
    registry.require_enabled("mock_fixture", "GET")
    registry.require_enabled("openligadb", "GET")
    registry.require_enabled("football_data", "GET")
    registry.require_enabled("the_odds_api", "GET")
    registry.require_enabled("nvidia_nim", "POST")
    with pytest.raises(PermissionError, match="PROVIDER_METHOD_FORBIDDEN"):
        registry.require_enabled("the_odds_api", "POST")
