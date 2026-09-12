"""Exercise the configured NVIDIA trial models without loading application state."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel, ConfigDict

from app.domain.registries import ModelRegistry
from app.infrastructure.config_loader import load_model_registry
from app.infrastructure.gemini_client import GeminiJsonRequest, GeminiJsonResult
from app.infrastructure.nvidia_nim_client import NvidiaNimClient
from app.settings import Settings


class ProbeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ok: Literal[True]


class ProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str
    provider_request_id: str | None
    prompt_tokens: int
    output_tokens: int


class ProbeClient(Protocol):
    async def generate_json(self, request: GeminiJsonRequest) -> GeminiJsonResult: ...


async def probe_registry(
    registry: ModelRegistry,
    client: ProbeClient,
    *,
    now: datetime | None = None,
) -> tuple[ProbeResult, ...]:
    checked_at = now or datetime.now(UTC)
    model_ids: dict[str, None] = {}
    for route_name in registry.routes:
        route = registry.assert_route_eligible(route_name, {"structured_output"}, checked_at)
        if route.provider != "nvidia_nim" or route.billing_mode != "trial_rate_limited":
            raise ValueError("NVIDIA_PROBE_REQUIRES_TRIAL_ROUTES")
        model_ids[route.model_id] = None
    if not model_ids:
        raise ValueError("NVIDIA_PROBE_NO_MODELS")

    results: list[ProbeResult] = []
    for model_id in model_ids:
        async with asyncio.timeout(120):
            response = await client.generate_json(
                GeminiJsonRequest(
                    model_id=model_id,
                    system_instruction="Return exactly the requested JSON object. No commentary.",
                    prompt='Return {"ok":true}.',
                    response_schema=ProbeOutput.model_json_schema(),
                    max_output_tokens=256,
                    thinking_level="minimal",
                    thinking_budget=0,
                )
            )
        ProbeOutput.model_validate(response.output)
        if response.model_id != model_id:
            raise ValueError("NVIDIA_PROBE_MODEL_MISMATCH")
        result = ProbeResult(
            model_id=response.model_id,
            provider_request_id=response.provider_request_id,
            prompt_tokens=response.prompt_token_count,
            output_tokens=response.candidates_token_count + response.thoughts_token_count,
        )
        results.append(result)
        print(result.model_dump_json(), flush=True)
    return tuple(results)


async def main() -> int:
    client: NvidiaNimClient | None = None
    try:
        settings = Settings()
        if settings.selected_ai_provider != "nvidia_nim":
            raise ValueError("NVIDIA_PROBE_PROVIDER_NOT_ENABLED")
        registry = load_model_registry(settings.CONFIG_DIR / "models.yaml")
        client = NvidiaNimClient(
            api_key=settings.NVIDIA_API_KEY.get_secret_value(),
            base_url=settings.NVIDIA_API_BASE_URL,
            max_concurrency=1,
        )
        await probe_registry(registry, client)
        return 0
    except Exception as error:
        # Provider bodies and validation inputs can contain arbitrary text; never echo them.
        safe_error: dict[str, str | int] = {
            "error": "NVIDIA_PROBE_FAILED",
            "type": type(error).__name__,
        }
        if isinstance(error, httpx.HTTPStatusError):
            safe_error["http_status"] = error.response.status_code
        print(json.dumps(safe_error))
        return 1
    finally:
        if client is not None:
            await client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
