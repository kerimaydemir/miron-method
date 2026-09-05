import asyncio
from collections.abc import Sequence

import httpx

from app.domain.deep_evidence import DeepEvidenceProvider, DeepFootballEvidence
from app.domain.fixtures import CanonicalFixture


class CompositeDeepEvidenceProvider:
    source_name = "composite_deep_evidence"

    def __init__(
        self,
        providers: Sequence[DeepEvidenceProvider],
        *,
        provider_timeout_seconds: float = 120,
    ) -> None:
        self._providers = tuple(providers)
        self._provider_timeout_seconds = provider_timeout_seconds

    @property
    def available(self) -> bool:
        return any(provider.available for provider in self._providers)

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        last_error: Exception | None = None
        collected: list[DeepFootballEvidence] = []
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                collected.append(
                    await asyncio.wait_for(
                        provider.collect(fixture), timeout=self._provider_timeout_seconds
                    )
                )
            except (
                TimeoutError,
                PermissionError,
                KeyError,
                RuntimeError,
                ValueError,
                httpx.HTTPError,
            ) as error:
                last_error = error
        if collected:
            return self._merge(collected)
        if last_error is not None:
            raise RuntimeError("DEEP_EVIDENCE_UNAVAILABLE") from last_error
        raise PermissionError("DEEP_EVIDENCE_PROVIDER_REQUIRED")

    async def close(self) -> None:
        for provider in self._providers:
            close = getattr(provider, "close", None)
            if close is not None:
                await close()

    @staticmethod
    def _merge(items: list[DeepFootballEvidence]) -> DeepFootballEvidence:
        primary = items[0]
        coverage: dict[str, bool] = {}
        for item in items:
            for key, value in item.coverage.items():
                coverage[key] = coverage.get(key, False) or value
        return DeepFootballEvidence(
            provider="+".join(item.provider for item in items),
            provider_fixture_id=primary.provider_fixture_id,
            observed_at=max(item.observed_at for item in items),
            home_team_id=next((item.home_team_id for item in items if item.home_team_id), 0),
            away_team_id=next((item.away_team_id for item in items if item.away_team_id), 0),
            league_id=next((item.league_id for item in items if item.league_id), 0),
            season=next((item.season for item in items if item.season), primary.season),
            artifacts=tuple(artifact for item in items for artifact in item.artifacts),
            coverage=coverage,
        )
