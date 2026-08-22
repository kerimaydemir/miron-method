from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.api.analysis_runs import locks_router
from app.api.analysis_runs import router as analysis_router
from app.api.auto_coupons import router as auto_coupons_router
from app.api.fixtures import router as fixtures_router
from app.api.post_match import router as post_match_router
from app.api.scans import router as scans_router
from app.settings import get_settings


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    product: str
    version: str
    observed_at: datetime


api_router = APIRouter()
api_router.include_router(scans_router)
api_router.include_router(fixtures_router)
api_router.include_router(analysis_router)
api_router.include_router(locks_router)
api_router.include_router(post_match_router)
api_router.include_router(auto_coupons_router)


@api_router.get("/health/live", response_model=HealthResponse, tags=["health"])
async def live() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="live",
        product=settings.PRODUCT_NAME,
        version="0.1.0",
        observed_at=datetime.now(UTC),
    )


@api_router.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def ready() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ready",
        product=settings.PRODUCT_NAME,
        version="0.1.0",
        observed_at=datetime.now(UTC),
    )


@api_router.get("/version", response_model=dict[str, str], tags=["platform"])
async def version() -> dict[str, str]:
    return {"product": "MİRON BABA AI", "version": "0.1.0"}
