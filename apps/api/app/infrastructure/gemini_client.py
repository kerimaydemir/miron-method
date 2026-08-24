import asyncio
import json
import re
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field


class GeminiJsonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(pattern=r"^gemini-")
    system_instruction: str = Field(min_length=1, max_length=20_000)
    prompt: str = Field(min_length=1, max_length=200_000)
    response_schema: dict[str, Any]
    max_output_tokens: int = Field(default=2_048, ge=64, le=8_192)
    thinking_level: Literal["minimal", "low", "medium", "high"] | None = None
    thinking_budget: int | None = Field(default=None, ge=0, le=32_768)
    enable_google_search: bool = False


class GeminiGroundingSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    url: str


class GeminiJsonResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str
    provider_request_id: str | None
    output: dict[str, Any]
    prompt_token_count: int = Field(default=0, ge=0)
    candidates_token_count: int = Field(default=0, ge=0)
    thoughts_token_count: int = Field(default=0, ge=0)
    grounding_sources: tuple[GeminiGroundingSource, ...] = ()


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY_MISSING")
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(120.0, connect=10.0),
            transport=transport,
        )

    async def generate_json(self, request: GeminiJsonRequest) -> GeminiJsonResult:
        response: httpx.Response | None = None
        output: dict[str, Any] | None = None
        payload: dict[str, Any] = {}
        prompt_token_count = 0
        candidates_token_count = 0
        thoughts_token_count = 0
        grounding_sources: tuple[GeminiGroundingSource, ...] = ()
        generation_config: dict[str, Any] = {"max_output_tokens": request.max_output_tokens}
        if request.thinking_budget is not None:
            generation_config["thinking_config"] = {"thinking_budget": request.thinking_budget}
        for attempt in range(4):
            request_body: dict[str, Any] = {
                "model": request.model_id,
                "input": request.prompt,
                "system_instruction": request.system_instruction,
                "response_format": {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": self._gemini_safe_schema(request.response_schema),
                },
                "generation_config": generation_config,
                "store": False,
            }
            if request.enable_google_search:
                request_body["tools"] = [{"type": "google_search"}]
            try:
                response = await self._client.post(
                    "/interactions",
                    headers={"x-goog-api-key": self._api_key},
                    json=request_body,
                )
            except httpx.TimeoutException:
                if request.enable_google_search or attempt == 3:
                    raise
                await asyncio.sleep(0.5 * (2**attempt))
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                await asyncio.sleep(self._retry_delay(response, attempt))
                continue
            response.raise_for_status()
            payload = response.json()
            usage = payload.get("usage", {})
            prompt_token_count += int(usage.get("total_input_tokens", 0))
            candidates_token_count += int(usage.get("total_output_tokens", 0))
            thoughts_token_count += int(usage.get("total_thought_tokens", 0))
            grounding_sources = self._grounding_sources(payload)
            try:
                text_output = "".join(self._model_output_texts(payload))
                parsed_output = json.loads(text_output)
                if not isinstance(parsed_output, dict):
                    raise ValueError("GEMINI_OBJECT_OUTPUT_REQUIRED")
                output = parsed_output
                break
            except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as error:
                if attempt == 3:
                    raise ValueError("GEMINI_INVALID_STRUCTURED_OUTPUT") from error
                await asyncio.sleep(0.5 * (2**attempt))
        if response is None:
            raise RuntimeError("GEMINI_REQUEST_NOT_EXECUTED")
        if output is None:
            raise ValueError("GEMINI_INVALID_STRUCTURED_OUTPUT")
        return GeminiJsonResult(
            model_id=request.model_id,
            provider_request_id=response.headers.get("x-request-id") or payload.get("id"),
            output=output,
            prompt_token_count=prompt_token_count,
            candidates_token_count=candidates_token_count,
            thoughts_token_count=thoughts_token_count,
            grounding_sources=grounding_sources,
        )

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after is not None:
            try:
                return GeminiClient._bounded_retry_delay(float(retry_after))
            except ValueError:
                pass
        try:
            payload = response.json()
            details = payload.get("error", {}).get("details", [])
            for detail in details:
                delay = detail.get("retryDelay") if isinstance(detail, dict) else None
                if isinstance(delay, str) and delay.endswith("s"):
                    delay_seconds: float = float(delay.removesuffix("s"))
                    return GeminiClient._bounded_retry_delay(delay_seconds)
            message = str(payload.get("error", {}).get("message", ""))
            match = re.search(r"retry in ([0-9.]+)s", message, re.IGNORECASE)
            if match:
                return GeminiClient._bounded_retry_delay(float(match.group(1)))
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        return 0.5 * float(2**attempt)

    @staticmethod
    def _bounded_retry_delay(provider_seconds: float) -> float:
        if provider_seconds <= 0:
            return 0.0
        return min(30.0, max(1.0, provider_seconds + 0.5))

    @staticmethod
    def _grounding_sources(payload: dict[str, Any]) -> tuple[GeminiGroundingSource, ...]:
        chunks = payload.get("grounding_metadata", {}).get("grounding_chunks", [])
        if not chunks:
            chunks = payload.get("groundingMetadata", {}).get("groundingChunks", [])
        sources: list[GeminiGroundingSource] = []
        seen: set[str] = set()
        for chunk in chunks:
            web = chunk.get("web") if isinstance(chunk, dict) else None
            if not isinstance(web, dict):
                continue
            url = web.get("uri")
            title = web.get("title")
            if not isinstance(url, str) or not url.startswith("http") or url in seen:
                continue
            seen.add(url)
            sources.append(
                GeminiGroundingSource(
                    title=title if isinstance(title, str) and title else url,
                    url=url,
                )
            )
        return tuple(sources)

    @staticmethod
    def _model_output_texts(payload: dict[str, Any]) -> tuple[str, ...]:
        texts: list[str] = []
        for step in payload.get("steps", []):
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue
            for item in step.get("content", []):
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    texts.append(item["text"])
        if texts:
            return tuple(texts)
        try:
            parts = payload["candidates"][0]["content"]["parts"]
            return tuple(part["text"] for part in parts if "text" in part)
        except (KeyError, IndexError, TypeError):
            return ()

    @staticmethod
    def _gemini_safe_schema(schema: dict[str, Any]) -> dict[str, Any]:
        definitions = schema.get("$defs", {})

        def sanitize(node: Any) -> Any:
            if not isinstance(node, dict):
                return node
            if "$ref" in node:
                ref = str(node["$ref"])
                prefix = "#/$defs/"
                if ref.startswith(prefix) and isinstance(definitions, dict):
                    target = definitions.get(ref.removeprefix(prefix), {})
                    return sanitize(target)
            cleaned: dict[str, Any] = {}
            for key, value in node.items():
                if key in {
                    "$defs",
                    "$ref",
                    "title",
                    "description",
                    "pattern",
                    "format",
                    "minLength",
                    "maxLength",
                    "minItems",
                    "maxItems",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "additionalProperties",
                }:
                    continue
                if key == "properties" and isinstance(value, dict):
                    cleaned[key] = {
                        str(prop_name): sanitize(prop_schema)
                        for prop_name, prop_schema in value.items()
                    }
                    continue
                if key == "items":
                    cleaned[key] = sanitize(value)
                    continue
                if key == "anyOf" and isinstance(value, list):
                    types = [
                        item.get("type")
                        for item in value
                        if isinstance(item, dict) and isinstance(item.get("type"), str)
                    ]
                    if len(types) == len(value):
                        cleaned["type"] = types
                        continue
                cleaned[key] = sanitize(value)
            return cleaned

        sanitized = sanitize(schema)
        if not isinstance(sanitized, dict):
            raise ValueError("GEMINI_SCHEMA_INVALID")
        return sanitized
