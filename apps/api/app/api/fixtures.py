from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.domain.fixtures import CanonicalFixture
from app.infrastructure.fixture_runtime import fixture_provider


class FixtureSearchPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    query: str
    items: tuple[CanonicalFixture, ...]
    count: int
    source: str


class FixtureSourceStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source: str
    mode: str
    observed_at: datetime | None


router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("/search", response_model=FixtureSearchPage)
async def search_fixtures(
    query: str = Query(min_length=2, max_length=80),
    start_utc: datetime | None = None,
    end_utc: datetime | None = None,
) -> FixtureSearchPage:
    items = await fixture_provider.search_fixtures(
        query=query, start_utc=start_utc, end_utc=end_utc
    )
    return FixtureSearchPage(
        query=query,
        items=items,
        count=len(items),
        source=fixture_provider.source_name,
    )


@router.get("/source-status", response_model=FixtureSourceStatus)
async def fixture_source_status() -> FixtureSourceStatus:
    return FixtureSourceStatus(
        source=fixture_provider.source_name,
        mode="live" if fixture_provider.source_name == "openligadb" else "mock",
        observed_at=fixture_provider.observed_at,
    )


@router.get("/{fixture_id}", response_model=CanonicalFixture)
async def get_fixture(fixture_id: UUID) -> CanonicalFixture:
    try:
        return await fixture_provider.get_fixture(fixture_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "FIXTURE_NOT_FOUND"}) from error
