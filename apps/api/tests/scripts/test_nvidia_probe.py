from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.registries import ModelRegistry, ModelRoute
from app.infrastructure.gemini_client import GeminiJsonRequest, GeminiJsonResult
from scripts import nvidia_probe
from scripts.nvidia_probe import probe_registry

NOW = datetime(2026, 9, 7, tzinfo=UTC)


def _registry() -> ModelRegistry:
    route = ModelRoute(
        provider="nvidia_nim",
        model_id="nvidia/test-model",
        capabilities=frozenset({"structured_output"}),
        billing_mode="trial_rate_limited",
        input_usd_per_mtok=Decimal("0"),
        output_usd_per_mtok=Decimal("0"),
        max_calls_per_run=2,
    )
    return ModelRegistry(
        schema_version="model-registry.v1",
        verified_at=NOW,
        verification_expires_at=NOW + timedelta(days=30),
        currency="USD",
        routes={
            "research": route,
            "specialist": route,
            "critic": route.model_copy(update={"model_id": "nvidia/critic-model"}),
        },
        policies={},
    )


class FakeClient:
    def __init__(self, output: dict[str, Any] | None = None) -> None:
        self.output = output if output is not None else {"ok": True}
        self.requests: list[GeminiJsonRequest] = []

    async def generate_json(self, request: GeminiJsonRequest) -> GeminiJsonResult:
        self.requests.append(request)
        return GeminiJsonResult(
            model_id=request.model_id,
            provider_request_id="probe-request-id",
            output=self.output,
            prompt_token_count=10,
            candidates_token_count=5,
            thoughts_token_count=2,
        )


@pytest.mark.asyncio
async def test_probe_requires_real_structured_success_for_each_distinct_model(
    capsys: pytest.CaptureFixture[str],
) -> None:
    client = FakeClient()

    results = await probe_registry(_registry(), client, now=NOW)

    assert [request.model_id for request in client.requests] == [
        "nvidia/test-model",
        "nvidia/critic-model",
    ]
    assert all(request.max_output_tokens == 256 for request in client.requests)
    assert all(not request.enable_google_search for request in client.requests)
    assert len(results) == 2
    assert results[0].output_tokens == 7
    output = capsys.readouterr().out
    assert "probe-request-id" in output
    assert '"ok"' not in output
    assert "Return exactly" not in output


@pytest.mark.asyncio
@pytest.mark.parametrize("output", [{"ok": False}, {"ok": "true"}, {"ok": True, "extra": 1}])
async def test_probe_rejects_valid_json_that_does_not_match_canary_contract(
    output: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client = FakeClient(output)

    with pytest.raises(ValidationError):
        await probe_registry(_registry(), client, now=NOW)

    assert len(client.requests) == 1
    assert capsys.readouterr().out == ""


@pytest.mark.asyncio
async def test_probe_rejects_any_paid_fallback_before_first_network_request() -> None:
    registry = _registry()
    routes = dict(registry.routes)
    routes["critic"] = routes["critic"].model_copy(update={"billing_mode": "metered"})
    client = FakeClient()

    with pytest.raises(ValueError, match="NVIDIA_PROBE_REQUIRES_TRIAL_ROUTES"):
        await probe_registry(registry.model_copy(update={"routes": routes}), client, now=NOW)

    assert client.requests == []


@pytest.mark.asyncio
async def test_probe_main_never_prints_secret_bearing_validation_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def invalid_settings() -> None:
        raise ValueError("sensitive-key-value must never reach logs")

    monkeypatch.setattr(nvidia_probe, "Settings", invalid_settings)

    assert await nvidia_probe.main() == 1
    output = capsys.readouterr().out
    assert "NVIDIA_PROBE_FAILED" in output
    assert "sensitive-key-value" not in output
