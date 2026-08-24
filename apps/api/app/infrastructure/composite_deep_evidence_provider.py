import asyncio
from collections.abc import Sequence

import httpx

from app.domain.deep_evidence import DeepEvidenceProvider, DeepFootballEvidence
from app.domain.fixtures import CanonicalFixture


class CompositeDeepEvidenceProvider:
    source_name = "composite_deep_evidence"

    def __init__(self, providers: Sequence[DeepEvidenceProvider]) -> None:
        self._providers = tuple(providers)

    @property
    def available(self) -> bool:
        return any(provider.available for provider in self._providers)

    async def collect(self, fixture: CanonicalFixture) -> DeepFootballEvidence:
        last_error: Exception | None = None
        for provider in self._providers:
            if not provider.available:
                continue
            try:
                return await asyncio.wait_for(provider.collect(fixture), timeout=35)
            except (
                TimeoutError,
                PermissionError,
                KeyError,
                RuntimeError,
                ValueError,
                httpx.HTTPError,
            ) as error:
                last_error = error
        if last_error is not None:
            raise RuntimeError("DEEP_EVIDENCE_UNAVAILABLE") from last_error
        raise PermissionError("DEEP_EVIDENCE_PROVIDER_REQUIRED")

    async def close(self) -> None:
        for provider in self._providers:
            close = getattr(provider, "close", None)
            if close is not None:
                await close()
