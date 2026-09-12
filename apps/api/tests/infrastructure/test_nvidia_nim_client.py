import json

import httpx
import pytest

from app.infrastructure.gemini_client import GeminiJsonRequest
from app.infrastructure.nvidia_nim_client import NvidiaNimClient


def _request(**updates: object) -> GeminiJsonRequest:
    values: dict[str, object] = {
        "model_id": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "system_instruction": "Return only a bounded JSON verdict.",
        "prompt": "Evaluate the supplied evidence packet.",
        "response_schema": {
            "type": "object",
            "properties": {"verdict": {"type": "string"}},
            "required": ["verdict"],
            "additionalProperties": False,
        },
    }
    values.update(updates)
    return GeminiJsonRequest.model_validate(values)


@pytest.mark.asyncio
async def test_nvidia_nim_client_uses_bearer_auth_guided_json_and_ignores_reasoning() -> None:
    api_key = "test-nvidia-secret"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.url.query == b""
        assert request.headers["authorization"] == f"Bearer {api_key}"
        body = json.loads(request.content)
        assert body == {
            "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "messages": [
                {"role": "system", "content": "Return only a bounded JSON verdict."},
                {"role": "user", "content": "Evaluate the supplied evidence packet."},
            ],
            "max_tokens": 2_048,
            "temperature": 0.1,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
            "guided_json": {
                "type": "object",
                "properties": {"verdict": {"type": "string"}},
                "required": ["verdict"],
                "additionalProperties": False,
            },
        }
        assert api_key.encode() not in request.url.raw_path
        return httpx.Response(
            200,
            headers={"x-request-id": "nvidia-request-1"},
            json={
                "id": "chatcmpl-provider-id",
                "choices": [
                    {
                        "message": {
                            "content": "```json\n{\"verdict\":\"ok\"}\n```",
                            "reasoning_content": "this is deliberately not JSON",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 8,
                    "completion_tokens_details": {"reasoning_tokens": 3},
                },
            },
        )

    client = NvidiaNimClient(api_key, transport=httpx.MockTransport(handler))
    try:
        result = await client.generate_json(_request())
    finally:
        await client.close()
    assert result.output == {"verdict": "ok"}
    assert result.provider_request_id == "nvidia-request-1"
    assert result.prompt_token_count == 12
    assert result.candidates_token_count == 5
    assert result.thoughts_token_count == 3
    assert result.grounding_sources == ()


@pytest.mark.asyncio
async def test_nvidia_nim_client_accepts_object_content_and_provider_id() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-2",
                "choices": [{"message": {"content": {"verdict": "object"}}}],
                "usage": {"prompt_tokens": "7", "completion_tokens": "4"},
            },
        )

    client = NvidiaNimClient("test-key", transport=httpx.MockTransport(handler))
    try:
        result = await client.generate_json(_request())
    finally:
        await client.close()
    assert result.output == {"verdict": "object"}
    assert result.provider_request_id == "chatcmpl-2"
    assert result.prompt_token_count == 7
    assert result.candidates_token_count == 4
    assert result.thoughts_token_count == 0


@pytest.mark.asyncio
async def test_nvidia_nim_client_retries_rate_limit_and_timeout() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("provider timeout", request=request)
        if calls == 2:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"verdict":"ok"}'}}]},
        )

    client = NvidiaNimClient("test-key", transport=httpx.MockTransport(handler))
    try:
        result = await client.generate_json(_request())
    finally:
        await client.close()
    assert calls == 3
    assert result.output == {"verdict": "ok"}


@pytest.mark.asyncio
async def test_nvidia_nim_client_does_not_retry_422_or_expose_secret() -> None:
    calls = 0
    api_key = "never-print-this-secret"

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(422, json={"detail": "schema rejected"})

    client = NvidiaNimClient(api_key, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(httpx.HTTPStatusError, match="NVIDIA_HTTP_422") as captured:
            await client.generate_json(_request())
    finally:
        await client.close()
    assert calls == 1
    assert api_key not in str(captured.value)
    assert "authorization" not in captured.value.request.headers


@pytest.mark.asyncio
async def test_nvidia_nim_client_rejects_search_and_invalid_structured_output() -> None:
    calls = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "[1, 2, 3]"}}]},
        )

    client = NvidiaNimClient("test-key", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError, match="NVIDIA_GOOGLE_SEARCH_UNSUPPORTED"):
            await client.generate_json(_request(enable_google_search=True))
        with pytest.raises(ValueError, match="NVIDIA_OBJECT_OUTPUT_REQUIRED"):
            await client.generate_json(_request())
    finally:
        await client.close()
    assert calls == 1


@pytest.mark.asyncio
async def test_nvidia_nim_client_lists_and_asserts_configured_models() -> None:
    paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "nvidia/nemotron-3.5-lightning-30b-a3b"},
                    {"id": "openai/gpt-oss-120b"},
                    {"unexpected": "ignored"},
                ]
            },
        )

    client = NvidiaNimClient("test-key", transport=httpx.MockTransport(handler))
    try:
        assert await client.list_models() == (
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            "openai/gpt-oss-120b",
        )
        assert await client.assert_models_available(
            ("openai/gpt-oss-120b", "nvidia/nemotron-3.5-lightning-30b-a3b")
        ) == ("openai/gpt-oss-120b", "nvidia/nemotron-3.5-lightning-30b-a3b")
        with pytest.raises(ValueError, match="NVIDIA_MODELS_UNAVAILABLE:missing/model"):
            await client.assert_models_available(("missing/model",))
    finally:
        await client.close()
    assert paths == ["/v1/models", "/v1/models", "/v1/models"]


def test_nvidia_nim_client_rejects_missing_key_and_unsafe_base_url() -> None:
    with pytest.raises(ValueError, match="NVIDIA_API_KEY_MISSING"):
        NvidiaNimClient("")
    with pytest.raises(ValueError, match="NVIDIA_API_KEY_MISSING"):
        NvidiaNimClient("   ")
    with pytest.raises(ValueError, match="NVIDIA_BASE_URL_UNSAFE"):
        NvidiaNimClient("test-key", "https://test:secret@example.com/v1")
    with pytest.raises(ValueError, match="NVIDIA_BASE_URL_UNSAFE"):
        NvidiaNimClient("test-key", "https://example.com/v1?api_key=unsafe")


def test_nvidia_nim_client_bounds_retry_delays() -> None:
    assert NvidiaNimClient._bounded_retry_delay(0.0) == 0.0
    assert NvidiaNimClient._bounded_retry_delay(0.1) == pytest.approx(1.0)
    assert NvidiaNimClient._bounded_retry_delay(17.6) == pytest.approx(18.1)
    assert NvidiaNimClient._bounded_retry_delay(60.0) == pytest.approx(30.0)
