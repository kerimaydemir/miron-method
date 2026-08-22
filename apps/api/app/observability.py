import json
import threading
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "password",
        "secret",
        "secret_access_key",
        "token",
        "api_key",
    }
)


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if str(key).casefold() in SENSITIVE_KEYS
            else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive(item) for item in value]
    return value


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration_seconds: dict[tuple[str, str], float] = defaultdict(float)

    def observe(self, method: str, route: str, status_code: int, duration: float) -> None:
        with self._lock:
            self._requests[(method, route, status_code)] += 1
            self._duration_seconds[(method, route)] += duration

    def render(self) -> str:
        lines = [
            "# HELP miron_baba_ai_http_requests_total HTTP requests by route and status.",
            "# TYPE miron_baba_ai_http_requests_total counter",
        ]
        with self._lock:
            for (method, route, status_code), count in sorted(self._requests.items()):
                labels = _labels(method=method, route=route, status=str(status_code))
                lines.append(f"miron_baba_ai_http_requests_total{{{labels}}} {count}")
            lines.extend(
                (
                    "# HELP miron_baba_ai_http_request_duration_seconds_sum Cumulative request latency.",
                    "# TYPE miron_baba_ai_http_request_duration_seconds_sum counter",
                )
            )
            for (method, route), duration in sorted(self._duration_seconds.items()):
                labels = _labels(method=method, route=route)
                lines.append(
                    f"miron_baba_ai_http_request_duration_seconds_sum{{{labels}}} {duration:.6f}"
                )
        return "\n".join(lines) + "\n"


def _labels(**values: str) -> str:
    return ",".join(
        f"{name}={json.dumps(value, ensure_ascii=True)}" for name, value in values.items()
    )


metrics = MetricsRegistry()


class OperationalMiddleware(BaseHTTPMiddleware):
    MAX_BODY_BYTES = 1_048_576

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.monotonic()
        correlation_raw = request.headers.get("X-Correlation-ID")
        try:
            correlation_id = UUID(correlation_raw) if correlation_raw else uuid4()
        except ValueError:
            correlation_id = uuid4()
            return self._secure(
                JSONResponse(
                    status_code=422,
                    content={
                        "type": "about:blank",
                        "title": "Invalid correlation identifier",
                        "status": 422,
                        "code": "INVALID_CORRELATION_ID",
                        "correlation_id": str(correlation_id),
                    },
                    media_type="application/problem+json",
                ),
                correlation_id,
            )

        content_length = request.headers.get("content-length")
        try:
            body_too_large = bool(content_length and int(content_length) > self.MAX_BODY_BYTES)
        except ValueError:
            body_too_large = True
        if body_too_large:
            return self._secure(
                JSONResponse(
                    status_code=413,
                    content={
                        "type": "about:blank",
                        "title": "Request body too large",
                        "status": 413,
                        "code": "REQUEST_TOO_LARGE",
                        "correlation_id": str(correlation_id),
                    },
                    media_type="application/problem+json",
                ),
                correlation_id,
            )

        request.state.correlation_id = correlation_id
        response = await call_next(request)
        route_object = request.scope.get("route")
        route = getattr(route_object, "path", request.url.path)
        metrics.observe(
            request.method,
            str(route),
            response.status_code,
            time.monotonic() - started,
        )
        return self._secure(response, correlation_id)

    @staticmethod
    def _secure(response: Response, correlation_id: UUID) -> Response:
        response.headers["X-Correlation-ID"] = str(correlation_id)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'"
        )
        return response
