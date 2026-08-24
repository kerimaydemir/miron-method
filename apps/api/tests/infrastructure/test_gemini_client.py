import json

import httpx
import pytest

from app.infrastructure.gemini_client import GeminiClient, GeminiJsonRequest


@pytest.mark.asyncio
async def test_gemini_client_uses_only_selected_gemini_model_and_structured_output() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/interactions")
        assert request.headers["x-goog-api-key"] == "test-key"
        body = json.loads(request.content)
        assert body["model"] == "gemini-3.7-flash"
        assert body["response_format"]["mime_type"] == "application/json"
        assert body["store"] is False
        assert body["tools"] == [{"type": "google_search"}]
        return httpx.Response(
            200,
            headers={"x-request-id": "gemini-request-1"},
            json={
                "steps": [
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": '{"verdict":"ok"}'}],
                    }
                ],
                "grounding_metadata": {
                    "grounding_chunks": [
                        {
                            "web": {
                                "uri": "https://club.example/team-news",
                                "title": "Official team news",
                            }
                        }
                    ]
                },
                "usage": {
                    "total_input_tokens": 12,
                    "total_output_tokens": 5,
                    "total_thought_tokens": 3,
                },
            },
        )

    client = GeminiClient("test-key", transport=httpx.MockTransport(handler))
    try:
        result = await client.generate_json(
            GeminiJsonRequest(
                model_id="gemini-3.7-flash",
                system_instruction="Return a bounded football evidence verdict.",
                prompt="Evaluate the supplied evidence packet.",
                response_schema={
                    "type": "object",
                    "properties": {"verdict": {"type": "string"}},
                    "required": ["verdict"],
                },
                enable_google_search=True,
            )
        )
    finally:
        await client.close()
    assert result.output == {"verdict": "ok"}
    assert result.provider_request_id == "gemini-request-1"
    assert result.prompt_token_count == 12
    assert result.candidates_token_count + result.thoughts_token_count == 8
    assert result.grounding_sources[0].url == "https://club.example/team-news"


def test_gemini_client_rejects_missing_key_and_non_gemini_model() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY_MISSING"):
        GeminiClient("")
    with pytest.raises(ValueError, match="string_pattern_mismatch"):
        GeminiJsonRequest(
            model_id="other-model",
            system_instruction="System",
            prompt="Prompt",
            response_schema={"type": "object"},
        )


def test_gemini_client_adds_a_boundary_buffer_to_positive_provider_delays() -> None:
    assert GeminiClient._bounded_retry_delay(0.147) == pytest.approx(1.0)
    assert GeminiClient._bounded_retry_delay(17.6) == pytest.approx(18.1)
    assert GeminiClient._bounded_retry_delay(40.0) == pytest.approx(30.0)


@pytest.mark.asyncio
async def test_gemini_client_honors_zero_retry_after_before_success() -> None:
    calls = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": {}})
        return httpx.Response(
            200,
            json={
                "steps": [
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": '{"ok":true}'}],
                    }
                ]
            },
        )

    client = GeminiClient("test-key", transport=httpx.MockTransport(handler))
    try:
        result = await client.generate_json(
            GeminiJsonRequest(
                model_id="gemini-3.5-flash",
                system_instruction="Return JSON.",
                prompt="Return success.",
                response_schema={"type": "object"},
            )
        )
    finally:
        await client.close()
    assert calls == 2
    assert result.output == {"ok": True}
