import logging
import secrets
from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, status

from app.domain.auto_coupon import AutoCouponPerformance, AutoCouponReadiness, AutoCouponRun
from app.infrastructure.auto_coupon_runtime import auto_coupon_service
from app.settings import get_settings

router = APIRouter(prefix="/auto-coupons", tags=["auto-coupons"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/readiness", response_model=AutoCouponReadiness)
async def get_auto_coupon_readiness() -> AutoCouponReadiness:
    return auto_coupon_service.readiness()


@router.post("", response_model=AutoCouponRun, status_code=status.HTTP_201_CREATED)
async def create_auto_coupon(
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
) -> AutoCouponRun:
    try:
        return await auto_coupon_service.create(idempotency_key=idempotency_key)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": str(error.args[0])}) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error
    except httpx.HTTPError as error:
        status_code = (
            error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
        )
        logger.warning(
            "Automatic coupon provider request failed type=%s status=%s detail=%s",
            type(error).__name__,
            status_code,
            (
                error.response.text[:600]
                if isinstance(error, httpx.HTTPStatusError)
                else "unavailable"
            ),
        )
        raise HTTPException(status_code=502, detail={"code": "AUTO_PROVIDER_FAILED"}) from error
    except (PermissionError, RuntimeError) as error:
        raise HTTPException(status_code=503, detail={"code": str(error)}) from error


@router.get("/performance", response_model=AutoCouponPerformance)
async def get_auto_coupon_performance() -> AutoCouponPerformance:
    return auto_coupon_service.performance()


@router.post("/automation/daily")
async def run_daily_automation(
    phase: Literal["pre_match", "post_match"] = Query(),
    authorization: str = Header(default=""),
) -> dict[str, object]:
    expected = settings.AUTOMATION_TOKEN.get_secret_value()
    supplied = authorization.removeprefix("Bearer ").strip()
    if not expected:
        raise HTTPException(status_code=503, detail={"code": "AUTOMATION_TOKEN_REQUIRED"})
    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail={"code": "AUTOMATION_UNAUTHORIZED"})
    day = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date().isoformat()
    if phase == "pre_match":
        try:
            run = await auto_coupon_service.create(idempotency_key=f"daily-{day}-pre-match")
        except ValueError as error:
            if str(error) not in {
                "AUTO_COUPON_NO_CURRENT_LIVE_MARKETS",
                "AUTO_COUPON_NO_CURRENT_TOP_LEAGUE_FIXTURES",
            }:
                raise HTTPException(status_code=409, detail={"code": str(error)}) from error
            return {
                "phase": phase,
                "day": day,
                "run_id": None,
                "selection_count": 0,
                "notice": "Bugün otomasyon eşiğini geçen canlı market bulunmadı.",
                "code": str(error),
            }
        return {
            "phase": phase,
            "day": day,
            "run_id": str(run.run_id),
            "selection_count": len(run.selections),
            "notice": run.notice,
        }
    settled = await auto_coupon_service.settle_pending()
    return {
        "phase": phase,
        "day": day,
        "settled_count": settled,
        "performance": auto_coupon_service.performance().model_dump(mode="json"),
    }


@router.get("/{run_id}", response_model=AutoCouponRun)
async def get_auto_coupon(run_id: UUID) -> AutoCouponRun:
    try:
        return auto_coupon_service.get(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "AUTO_COUPON_NOT_FOUND"}) from error


@router.post("/{run_id}/settle", response_model=AutoCouponRun)
async def settle_auto_coupon(run_id: UUID) -> AutoCouponRun:
    try:
        await auto_coupon_service.settle_pending(run_id)
        return auto_coupon_service.get(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": str(error.args[0])}) from error
