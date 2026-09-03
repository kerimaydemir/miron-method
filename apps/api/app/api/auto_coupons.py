import asyncio
import logging
import secrets
from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, status

from app.domain.auto_coupon import (
    AutoCouponPerformance,
    AutoCouponReadiness,
    AutoCouponRun,
    CouponSelection,
)
from app.infrastructure.auto_coupon_runtime import auto_coupon_service
from app.settings import get_settings

router = APIRouter(prefix="/auto-coupons", tags=["auto-coupons"])
logger = logging.getLogger(__name__)
settings = get_settings()


def _reviewed_prediction_ids(runs: tuple[AutoCouponRun, ...]) -> set[UUID]:
    return {
        item.prediction_id
        for run in runs
        if run.post_match_review is not None
        for item in run.post_match_review.items
    }


def _settled_selection_ids(runs: tuple[AutoCouponRun, ...]) -> set[tuple[UUID, UUID]]:
    """Identify freshly settled coupon legs independently from the daily journal."""
    return {
        (run.run_id, selection.fixture.id)
        for run in runs
        for selection in run.selections
        if selection.settlement_status != "pending"
    }


def _daily_review_payloads(
    runs: tuple[AutoCouponRun, ...],
    *,
    newly_reviewed: set[UUID],
    newly_settled: set[tuple[UUID, UUID]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Build Telegram-ready settlement details for predictions and coupon tickets."""
    daily_reviews: list[dict[str, object]] = []
    ticket_reviews: list[dict[str, object]] = []
    for run in runs:
        report = run.post_match_review
        if report is None:
            continue
        predictions = {item.prediction_id: item for item in run.daily_predictions}
        fresh = [item for item in report.items if item.prediction_id in newly_reviewed]
        for review in fresh:
            prediction = predictions.get(review.prediction_id)
            if prediction is None:
                continue
            daily_reviews.append(
                {
                    "fixture": f"{prediction.fixture.home_team} - {prediction.fixture.away_team}",
                    "league": prediction.league.name,
                    "market": prediction.market_label,
                    "pick": prediction.outcome_label,
                    "odds": str(review.market_decimal_odds)
                    if review.market_decimal_odds is not None
                    else None,
                    "probability": str(review.probability),
                    "status": review.status,
                    "score": f"{review.final_home_score}-{review.final_away_score}",
                    "process_verdict": review.process_verdict,
                    "explanation": review.explanation,
                    "lesson": review.lesson,
                }
            )

        for ticket in run.tickets:
            selections = tuple(
                item
                for fixture_id in ticket.selection_fixture_ids
                for item in run.selections
                if item.fixture.id == fixture_id
            )
            if not selections or not any(
                (run.run_id, selection.fixture.id) in newly_settled for selection in selections
            ):
                continue
            statuses = {selection.settlement_status for selection in selections}
            if "pending" in statuses:
                ticket_status = "pending"
            elif "lost" in statuses:
                ticket_status = "lost"
            elif statuses == {"won"}:
                ticket_status = "won"
            elif statuses == {"void"}:
                ticket_status = "void"
            else:
                ticket_status = "pending"
            ticket_reviews.append(
                {
                    "label": ticket.label,
                    "odds": str(ticket.combined_decimal_odds),
                    "status": ticket_status,
                    "legs": [
                        {
                            "fixture": f"{selection.fixture.home_team} - {selection.fixture.away_team}",
                            "market": selection.market_label,
                            "pick": selection.outcome_label,
                            "odds": str(selection.market_decimal_odds)
                            if selection.market_decimal_odds is not None
                            else None,
                            "status": selection.settlement_status,
                            "score": (
                                f"{selection.final_home_score}-{selection.final_away_score}"
                                if selection.final_home_score is not None
                                and selection.final_away_score is not None
                                else "-"
                            ),
                        }
                        for selection in selections
                    ],
                }
            )
    return daily_reviews, ticket_reviews


@router.get("/readiness", response_model=AutoCouponReadiness)
async def get_auto_coupon_readiness() -> AutoCouponReadiness:
    return auto_coupon_service.readiness()


@router.post("", response_model=AutoCouponRun, status_code=status.HTTP_201_CREATED)
async def create_auto_coupon(
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
) -> AutoCouponRun:
    try:
        return await asyncio.wait_for(
            auto_coupon_service.create(idempotency_key=idempotency_key),
            timeout=settings.AUTO_COUPON_REQUEST_TIMEOUT_SECONDS,
        )
    except TimeoutError as error:
        raise HTTPException(
            status_code=503,
            detail={"code": "AUTO_COUPON_TIMED_OUT"},
        ) from error
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
            "daily_prediction_count": len(run.daily_predictions),
            "daily_predictions": [
                {
                    "fixture": (f"{item.fixture.home_team} - {item.fixture.away_team}"),
                    "league": item.league.name,
                    "market": item.market_label,
                    "pick": item.outcome_label,
                    "probability": str(item.probability),
                    "odds": str(item.market_decimal_odds)
                    if item.market_decimal_odds is not None
                    else None,
                    "tier": item.tier,
                    "reasons": item.reasons,
                    "risks": item.risks,
                }
                for item in run.daily_predictions
            ],
            "selection_count": len(run.selections),
            "ticket_count": len(run.tickets),
            "tickets": [
                {
                    "kind": ticket.kind,
                    "label": ticket.label,
                    "combined_probability": str(ticket.combined_probability),
                    "combined_decimal_odds": str(ticket.combined_decimal_odds),
                    "risk_label": ticket.risk_label,
                    "legs": [
                        {
                            "fixture": f"{selection.fixture.home_team} - {selection.fixture.away_team}",
                            "league": selection.league.name,
                            "market": selection.market_label,
                            "pick": selection.outcome_label,
                            "probability": str(selection.probability),
                            "odds": str(selection.market_decimal_odds)
                            if selection.market_decimal_odds is not None
                            else None,
                            "reason": selection.reason,
                        }
                        for fixture_id in ticket.selection_fixture_ids
                        for selection in run.selections
                        if selection.fixture.id == fixture_id
                    ],
                }
                for ticket in run.tickets
            ],
            "notice": run.notice,
        }
    before_runs = auto_coupon_service.journal(limit=45)
    before_reviewed = _reviewed_prediction_ids(before_runs)
    before_settled = _settled_selection_ids(before_runs)
    settled = await auto_coupon_service.settle_pending()
    reviewed = await auto_coupon_service.review_daily_predictions()
    after_runs = auto_coupon_service.journal(limit=45)
    after_reviewed = _reviewed_prediction_ids(after_runs)
    after_settled = _settled_selection_ids(after_runs)
    daily_reviews, ticket_reviews = _daily_review_payloads(
        after_runs,
        newly_reviewed=after_reviewed - before_reviewed,
        newly_settled=after_settled - before_settled,
    )
    return {
        "phase": phase,
        "day": day,
        "settled_count": settled,
        "daily_reviewed_count": reviewed,
        "daily_reviews": daily_reviews,
        "ticket_reviews": ticket_reviews,
        "performance": auto_coupon_service.performance().model_dump(mode="json"),
    }


@router.get("/journal", response_model=tuple[AutoCouponRun, ...])
async def get_auto_coupon_journal(
    limit: int = Query(default=30, ge=1, le=90),
) -> tuple[AutoCouponRun, ...]:
    return auto_coupon_service.journal(limit=limit)


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
