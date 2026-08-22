from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    artifact_id: UUID
    artifact_type: str
    schema_version: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SourceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    source_type: str
    canonical_url: str | None
    provider_id: str | None
    published_at: datetime | None
    provider_updated_at: datetime | None
    observed_at: datetime
    retrieved_at: datetime
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    object_uri: str
    license_policy_version: str

    @field_validator("observed_at", "retrieved_at", "published_at", "provider_updated_at")
    @classmethod
    def aware_times(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("evidence timestamps must be timezone-aware")
        return value


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_snapshot_id: UUID
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    observed_at: datetime
    note: str = Field(min_length=1, max_length=500)


class NormalizedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    subject_entity_type: str
    subject_entity_id: UUID
    predicate: str
    object_json: dict[str, object]
    effective_start: datetime | None
    effective_end: datetime | None
    observed_at: datetime
    confidence: Decimal = Field(ge=0, le=1)
    status: Literal["accepted", "unresolved", "rejected", "superseded"]
    citations: tuple[Citation, ...]


class EvidencePacket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: UUID
    fixture_id: UUID
    cutoff_at: datetime
    sources: tuple[SourceSnapshot, ...]
    claims: tuple[NormalizedClaim, ...]
    excluded_source_ids: tuple[UUID, ...]
    degraded_reasons: tuple[str, ...]


def build_cutoff_safe_packet(
    *,
    run_id: UUID,
    fixture_id: UUID,
    cutoff_at: datetime,
    sources: tuple[SourceSnapshot, ...],
    claims: tuple[NormalizedClaim, ...],
) -> EvidencePacket:
    if cutoff_at.tzinfo is None or cutoff_at.utcoffset() is None:
        raise ValueError("cutoff_at must be timezone-aware")
    included_sources = tuple(source for source in sources if source.observed_at <= cutoff_at)
    included_ids = {source.id for source in included_sources}
    safe_claims = tuple(
        claim
        for claim in claims
        if claim.observed_at <= cutoff_at
        and claim.citations
        and all(
            citation.observed_at <= cutoff_at and citation.source_snapshot_id in included_ids
            for citation in claim.citations
        )
    )
    excluded = tuple(source.id for source in sources if source.id not in included_ids)
    reasons = ("SOURCE_AFTER_CUTOFF",) if excluded else ()
    return EvidencePacket(
        run_id=run_id,
        fixture_id=fixture_id,
        cutoff_at=cutoff_at,
        sources=included_sources,
        claims=safe_claims,
        excluded_source_ids=excluded,
        degraded_reasons=reasons,
    )
