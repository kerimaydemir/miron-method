from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.router import api_router
from app.infrastructure.analysis_runtime import stop_analysis_runtime
from app.infrastructure.auto_coupon_runtime import (
    start_auto_coupon_runtime,
    stop_auto_coupon_runtime,
)
from app.infrastructure.fixture_runtime import start_fixture_runtime, stop_fixture_runtime
from app.observability import OperationalMiddleware, metrics
from app.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()
    await start_fixture_runtime()
    await start_auto_coupon_runtime()
    try:
        yield
    finally:
        await stop_auto_coupon_runtime()
        await stop_analysis_runtime()
        await stop_fixture_runtime()


settings = get_settings()
app = FastAPI(
    title=settings.PRODUCT_NAME,
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(OperationalMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Correlation-ID"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/metrics", include_in_schema=False, response_class=PlainTextResponse)
async def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")
