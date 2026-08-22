import hashlib
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.application.scans import ScanResult, ScanService, utc_now
from app.infrastructure.fixture_runtime import fixture_provider


class StartScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    timezone: str = "Europe/Istanbul"
    ui_config_version: str = "dashboard.v1"


router = APIRouter(prefix="/scans", tags=["scans"])
scan_service = ScanService(fixture_provider, fixture_provider, utc_now)


@router.post("", response_model=ScanResult, status_code=status.HTTP_201_CREATED)
async def start_scan(
    body: StartScanRequest,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    correlation_header: str | None = Header(default=None, alias="X-Correlation-ID"),
) -> ScanResult:
    if body.timezone != "Europe/Istanbul":
        raise HTTPException(status_code=422, detail={"code": "INVALID_TIMEZONE"})
    try:
        correlation_id = UUID(correlation_header) if correlation_header else uuid4()
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": "INVALID_CORRELATION_ID"}) from error
    try:
        return await scan_service.start(
            idempotency_key=idempotency_key,
            request_hash=hashlib.sha256(body.model_dump_json().encode()).hexdigest(),
            correlation_id=correlation_id,
        )
    except ValueError as error:
        if str(error) == "IDEMPOTENCY_CONFLICT":
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from error
        raise
