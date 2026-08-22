from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.domain.post_match import AutopsyView, MatchResult
from app.infrastructure.analysis_runtime import analysis_service
from app.infrastructure.post_match_runtime import post_match_service as service


class PostMatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    home_score: int = Field(ge=0, le=30)
    away_score: int = Field(ge=0, le=30)
    observed_at: datetime
    source: str = Field(min_length=2, max_length=80)


router = APIRouter(prefix="/prediction-locks", tags=["post-match"])


@router.post(
    "/{lock_id}/post-match",
    response_model=AutopsyView,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_post_match(
    lock_id: UUID,
    body: PostMatchRequest,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
) -> AutopsyView:
    del idempotency_key
    try:
        lock = analysis_service.get_lock(lock_id)
        return service.ingest(
            lock,
            MatchResult(
                fixture_id=lock.manifest.fixture_id,
                home_score=body.home_score,
                away_score=body.away_score,
                observed_at=body.observed_at,
                source=body.source,
            ),
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": str(error.args[0])}) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error


@router.get("/{lock_id}/autopsy", response_model=AutopsyView)
async def get_autopsy(lock_id: UUID) -> AutopsyView:
    try:
        return service.get(lock_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "AUTOPSY_NOT_FOUND"}) from error
