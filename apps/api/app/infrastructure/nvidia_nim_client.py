import asyncio
import json
import re
from collections.abc import Iterable
from typing import Any

import httpx

from app.infrastructure.gemini_client import GeminiJsonRequest, GeminiJsonResult


class NvidiaNimClient:
    _MAX_ATTEMPTS = 4
    _FENCED_JSON = re.compile(
        r"\A```(?:json)?[ \t\r\n]*(.*?)[ \t\r\n]*```\Z",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        transport: httpx.AsyncBaseTransport | None = None,
        max_concurrency: int = 2,
        max_calls: int = 24,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("NVIDIA_API_KEY_MISSING")
        parsed_base_url = httpx.URL(base_url)
        if (
            parsed_base_url.username
            or parsed_base_url.password
            or parsed_base_url.query
            or parsed_base_url.fragment
        ):
            raise ValueError("NVIDIA_BASE_URL_UNSAFE")
        if not 1 <= max_concurrency <= 4:
            raise ValueError("NVIDIA_MAX_CONCURRENCY_INVALID")
        self._api_key = api_key
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._max_calls = max_calls
        self._calls = 0
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            timeout=httpx.Timeout(120.0, connect=10.0),
            transport=transport,
        )

    async def generate_json(self, request: GeminiJsonRequest) -> GeminiJsonResult:
        if request.enable_google_search:
            raise ValueError("NVIDIA_GOOGLE_SEARCH_UNSUPPORTED")
        request_body: dict[str, Any] = {
            "model": request.model_id,
            "messages": [
                {"role": "system", "content": request.system_instruction},
                {"role": "user", "content": request.prompt},
            ],
            "max_tokens": request.max_output_tokens,
            "temperature": 0.1,
            "stream": False,
            "guided_json": request.response_schema,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        async with self._semaphore:
            if self._calls >= self._max_calls:
                raise RuntimeError("NVIDIA_CALL_BUDGET_EXHAUSTED")
            self._calls += 1
            response, payload = await self._request_json(
                "POST", "chat/completions", request_body=request_body
            )
        output = self._structured_output(payload)
        returned_model = payload.get("model")
        if returned_model is not None and returned_model != request.model_id:
            raise ValueError("NVIDIA_RESPONSE_MODEL_MISMATCH")
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        prompt_tokens = self._non_negative_int(usage.get("prompt_tokens"))
        completion_tokens = self._non_negative_int(usage.get("completion_tokens"))
        completion_details = usage.get("completion_tokens_details")
        if not isinstance(completion_details, dict):
            completion_details = {}
        reasoning_tokens = min(
            completion_tokens,
            self._non_negative_int(completion_details.get("reasoning_tokens")),
        )
        provider_request_id = response.headers.get("x-request-id")
        if provider_request_id is None and isinstance(payload.get("id"), str):
            provider_request_id = payload["id"]
        return GeminiJsonResult(
            model_id=request.model_id,
            provider_request_id=provider_request_id,
            output=output,
            prompt_token_count=prompt_tokens,
            candidates_token_count=completion_tokens - reasoning_tokens,
            thoughts_token_count=reasoning_tokens,
            grounding_sources=(),
        )

    async def list_models(self) -> tuple[str, ...]:
        async with self._semaphore:
            _, payload = await self._request_json("GET", "models")
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValueError("NVIDIA_MODELS_RESPONSE_INVALID")
        model_ids = {
            item["id"]
            for item in data
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item["id"].strip()
        }
        if not model_ids:
            raise ValueError("NVIDIA_MODELS_RESPONSE_INVALID")
        return tuple(sorted(model_ids))

    async def assert_models_available(self, model_ids: Iterable[str]) -> tuple[str, ...]:
        configured = tuple(dict.fromkeys(model_ids))
        if not configured or any(not isinstance(item, str) or not item for item in configured):
            raise ValueError("NVIDIA_MODEL_IDS_REQUIRED")
        available = set(await self.list_models())
        missing = tuple(sorted(set(configured) - available))
        if missing:
            raise ValueError(f"NVIDIA_MODELS_UNAVAILABLE:{','.join(missing)}")
        return configured

    async def close(self) -> None:
        await self._client.aclose()

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        request_body: dict[str, Any] | None = None,
    ) -> tuple[httpx.Response, dict[str, Any]]:
        response: httpx.Response | None = None
        for attempt in range(self._MAX_ATTEMPTS):
            try:
                response = await self._client.request(
                    method,
                    path,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                )
            except httpx.TimeoutException as error:
                if attempt == self._MAX_ATTEMPTS - 1:
                    try:
                        original_request = error.request
                    except RuntimeError:
                        safe_request = httpx.Request(method, self._client.base_url.join(path))
                    else:
                        safe_request = httpx.Request(
                            original_request.method, original_request.url
                        )
                    raise httpx.TimeoutException(
                        "NVIDIA_TIMEOUT", request=safe_request
                    ) from None
                await asyncio.sleep(0.5 * float(2**attempt))
                continue
            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt < self._MAX_ATTEMPTS - 1:
                    await asyncio.sleep(self._retry_delay(response, attempt))
                    continue
            if response.is_error:
                raise self._safe_http_error(response)
            try:
                payload = response.json()
            except json.JSONDecodeError as error:
                raise ValueError("NVIDIA_RESPONSE_INVALID_JSON") from error
            if not isinstance(payload, dict):
                raise ValueError("NVIDIA_RESPONSE_INVALID_JSON")
            return response, payload
        if response is None:
            raise RuntimeError("NVIDIA_REQUEST_NOT_EXECUTED")
        raise self._safe_http_error(response)

    @classmethod
    def _structured_output(cls, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("NVIDIA_INVALID_STRUCTURED_OUTPUT") from error
        if isinstance(content, dict):
            return dict(content)
        if not isinstance(content, str):
            raise ValueError("NVIDIA_INVALID_STRUCTURED_OUTPUT")
        text = content.strip()
        fenced = cls._FENCED_JSON.fullmatch(text)
        if fenced is not None:
            text = fenced.group(1).strip()
        try:
            output = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError("NVIDIA_INVALID_STRUCTURED_OUTPUT") from error
        if not isinstance(output, dict):
            raise ValueError("NVIDIA_OBJECT_OUTPUT_REQUIRED")
        return output

    @staticmethod
    def _non_negative_int(value: Any) -> int:
        if isinstance(value, bool):
            return 0
        try:
            parsed = int(value)
        except (TypeError, ValueError, OverflowError):
            return 0
        return max(0, parsed)

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after is not None:
            try:
                return NvidiaNimClient._bounded_retry_delay(float(retry_after))
            except ValueError:
                pass
        return 0.5 * float(2**attempt)

    @staticmethod
    def _bounded_retry_delay(provider_seconds: float) -> float:
        if provider_seconds <= 0:
            return 0.0
        return min(30.0, max(1.0, provider_seconds + 0.5))

    @staticmethod
    def _safe_http_error(response: httpx.Response) -> httpx.HTTPStatusError:
        safe_request = httpx.Request(response.request.method, response.request.url)
        safe_response = httpx.Response(response.status_code, request=safe_request)
        return httpx.HTTPStatusError(
            f"NVIDIA_HTTP_{response.status_code}",
            request=safe_request,
            response=safe_response,
        )
