import hashlib
import logging
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Header, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict

from app.domain.analysis import (
    AnalysisEvidenceDossier,
    AnalysisRunView,
    FinalForecast,
    PredictionLockView,
    StageView,
)
from app.infrastructure.analysis_repository import canonical_json
from app.infrastructure.analysis_runtime import analysis_service as service


class StartAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    fixture_id: UUID


router = APIRouter(prefix="/analysis-runs", tags=["analysis"])
logger = logging.getLogger(__name__)


@router.post("", response_model=AnalysisRunView, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    body: StartAnalysisRequest,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    correlation_header: str | None = Header(default=None, alias="X-Correlation-ID"),
) -> AnalysisRunView:
    correlation_id = UUID(correlation_header) if correlation_header else uuid4()
    try:
        return await service.start(
            body.fixture_id,
            idempotency_key,
            hashlib.sha256(body.model_dump_json().encode()).hexdigest(),
            correlation_id,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": str(error.args[0])}) from error
    except ValueError as error:
        code = str(error)
        if code in {"IDEMPOTENCY_CONFLICT", "INVALID_CUTOFF"}:
            raise HTTPException(status_code=409, detail={"code": code}) from error
        logger.warning(
            "Gemini analysis validation failed type=%s detail=%s",
            type(error).__name__,
            str(error)[:600],
            extra={"correlation_id": str(correlation_id)},
        )
        raise HTTPException(status_code=502, detail={"code": "GEMINI_ANALYSIS_FAILED"}) from error
    except httpx.HTTPError as error:
        status_code = (
            error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
        )
        logger.warning(
            "Gemini provider request failed type=%s status=%s detail=%s",
            type(error).__name__,
            status_code,
            (
                error.response.text[:600]
                if isinstance(error, httpx.HTTPStatusError)
                else "unavailable"
            ),
            extra={"correlation_id": str(correlation_id)},
        )
        raise HTTPException(status_code=502, detail={"code": "GEMINI_PROVIDER_FAILED"}) from error
    except (PermissionError, RuntimeError) as error:
        logger.warning(
            "Gemini analysis unavailable",
            extra={"correlation_id": str(correlation_id), "error_type": type(error).__name__},
        )
        raise HTTPException(status_code=503, detail={"code": str(error)}) from error


@router.get("/{run_id}", response_model=AnalysisRunView)
async def get_analysis(run_id: UUID) -> AnalysisRunView:
    try:
        return service.get(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND"}) from error


@router.get("/{run_id}/stages", response_model=tuple[StageView, ...])
async def get_stages(run_id: UUID) -> tuple[StageView, ...]:
    return (await get_analysis(run_id)).stages


@router.get("/{run_id}/forecast", response_model=FinalForecast)
async def get_forecast(run_id: UUID) -> FinalForecast:
    return (await get_analysis(run_id)).forecast


@router.get("/{run_id}/evidence", response_model=AnalysisEvidenceDossier)
async def get_evidence(run_id: UUID) -> AnalysisEvidenceDossier:
    try:
        return service.get_evidence(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "EVIDENCE_NOT_FOUND"}) from error


@router.post("/{run_id}/lock", response_model=AnalysisRunView)
async def lock_analysis(run_id: UUID) -> AnalysisRunView:
    try:
        return await service.lock(run_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND"}) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error


locks_router = APIRouter(prefix="/prediction-locks", tags=["locks"])


@locks_router.get("/{lock_id}", response_model=PredictionLockView)
async def get_prediction_lock(lock_id: UUID) -> PredictionLockView:
    try:
        return service.get_lock(lock_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "LOCK_NOT_FOUND"}) from error


@locks_router.get("/{lock_id}/export.json")
async def export_prediction_lock_json(lock_id: UUID) -> dict[str, object]:
    lock = await get_prediction_lock(lock_id)
    return lock.model_dump(mode="json")


@locks_router.get("/{lock_id}/export.md", response_class=Response)
async def export_prediction_lock_markdown(lock_id: UUID) -> Response:
    lock = await get_prediction_lock(lock_id)
    manifest_json = canonical_json(lock.manifest.model_dump(mode="json"))
    content = "\n".join(
        (
            "# MİRON BABA AI — Kilitli Tahmin",
            "",
            f"- Lock ID: `{lock.lock_id}`",
            f"- Manifest SHA-256: `{lock.manifest_sha256}`",
            f"- Cutoff: `{lock.manifest.cutoff_at.isoformat()}`",
            f"- Kickoff: `{lock.manifest.kickoff_at_snapshot.isoformat()}`",
            "",
            "```json",
            manifest_json,
            "```",
        )
    )
    return Response(content=content, media_type="text/markdown; charset=utf-8")
