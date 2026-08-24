from datetime import UTC, datetime

import httpx
import pytest

from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
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
    def __init__(self, provider: str = "working", *, coverage_key: str = "fixture") -> None:
        self._provider = provider
        self._coverage_key = coverage_key

    @property
    def available(self) -> bool:
        return True

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        return DeepFootballEvidence(
            provider=self._provider,
            provider_fixture_id=str(fixture.provider_fixture_id or fixture.id),
            observed_at=datetime(2026, 8, 22, tzinfo=UTC),
            home_team_id=1,
            away_team_id=2,
            league_id=3,
            season=2026,
            artifacts=(
                EvidenceArtifact(
                    kind=self._coverage_key,
                    endpoint=f"/{self._provider}",
                    observed_at=datetime(2026, 8, 22, tzinfo=UTC),
                    records=({"provider": self._provider},),
                ),
            ),
            coverage={self._coverage_key: True},
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
async def test_composite_deep_evidence_merges_all_successful_providers() -> None:
    provider = CompositeDeepEvidenceProvider(
        (
            _WorkingProvider("sportmonks", coverage_key="fixture"),
            _BrokenProvider(),
            _WorkingProvider("thesportsdb", coverage_key="lineups"),
        )
    )

    evidence = await provider.collect(FIXTURES[0])

    assert evidence.provider == "sportmonks+thesportsdb"
    assert evidence.coverage == {"fixture": True, "lineups": True}
    assert tuple(artifact.kind for artifact in evidence.artifacts) == ("fixture", "lineups")


@pytest.mark.asyncio
async def test_composite_deep_evidence_fails_closed_when_all_sources_fail() -> None:
    provider = CompositeDeepEvidenceProvider((_BrokenProvider(),))

    with pytest.raises(RuntimeError, match="DEEP_EVIDENCE_UNAVAILABLE"):
        await provider.collect(FIXTURES[0])
