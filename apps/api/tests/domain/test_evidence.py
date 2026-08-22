from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.domain.evidence import Citation, NormalizedClaim, SourceSnapshot, build_cutoff_safe_packet


def test_inv_003_excludes_source_and_claim_after_cutoff() -> None:
    cutoff = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)
    safe_id, late_id = uuid4(), uuid4()
    safe = SourceSnapshot(
        id=safe_id,
        source_type="official",
        canonical_url="https://example.test/a",
        provider_id=None,
        published_at=cutoff - timedelta(hours=1),
        provider_updated_at=None,
        observed_at=cutoff,
        retrieved_at=cutoff,
        content_sha256="a" * 64,
        object_uri="s3://private/a",
        license_policy_version="v1",
    )
    late = safe.model_copy(
        update={
            "id": late_id,
            "observed_at": cutoff + timedelta(seconds=1),
            "content_sha256": "b" * 64,
            "object_uri": "s3://private/b",
        }
    )
    claim = NormalizedClaim(
        id=uuid4(),
        subject_entity_type="player",
        subject_entity_id=uuid4(),
        predicate="availability_status",
        object_json={"status": "available"},
        effective_start=None,
        effective_end=None,
        observed_at=late.observed_at,
        confidence=Decimal(".7"),
        status="unresolved",
        citations=(
            Citation(source_snapshot_id=late_id, observed_at=late.observed_at, note="late"),
        ),
    )
    packet = build_cutoff_safe_packet(
        run_id=uuid4(), fixture_id=uuid4(), cutoff_at=cutoff, sources=(safe, late), claims=(claim,)
    )
    assert packet.sources == (safe,)
    assert packet.claims == ()
    assert packet.excluded_source_ids == (late_id,)
    assert packet.degraded_reasons == ("SOURCE_AFTER_CUTOFF",)
