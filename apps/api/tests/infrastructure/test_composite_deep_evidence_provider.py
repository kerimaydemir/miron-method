from datetime import UTC, datetime

import httpx
import pytest

from app.domain.deep_evidence import DeepFootballEvidence
from app.domain.fixtures import CanonicalFixture
from app.infrastructure.composite_deep_evidence_provider import CompositeDeepEvidenceProvider
from app.infrastructure.mock_fixture_provider import FIXTURES


class _BrokenProvider:
    @property
    def available(self) -> bool:
        return True

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        del fixture
        raise httpx.ConnectError("network down")


class _WorkingProvider:
    @property
    def available(self) -> bool:
        return True

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        return DeepFootballEvidence(
            provider="working",
            provider_fixture_id=str(fixture.provider_fixture_id or fixture.id),
            observed_at=datetime(2026, 8, 22, tzinfo=UTC),
            home_team_id=1,
            away_team_id=2,
            league_id=3,
            season=2026,
            artifacts=(),
            coverage={"fixture": True},
        )


class _UnavailableProvider:
    @property
    def available(self) -> bool:
        return False

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        del fixture
        raise AssertionError("unavailable provider must not be called")


@pytest.mark.asyncio
async def test_composite_deep_evidence_falls_back_to_next_provider() -> None:
    provider = CompositeDeepEvidenceProvider(
        (_UnavailableProvider(), _BrokenProvider(), _WorkingProvider())
    )

    evidence = await provider.collect(FIXTURES[0])

    assert evidence.provider == "working"


@pytest.mark.asyncio
async def test_composite_deep_evidence_fails_closed_when_all_sources_fail() -> None:
    provider = CompositeDeepEvidenceProvider((_BrokenProvider(),))

    with pytest.raises(RuntimeError, match="DEEP_EVIDENCE_UNAVAILABLE"):
        await provider.collect(FIXTURES[0])
