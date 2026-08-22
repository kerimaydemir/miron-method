from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.fixtures import CanonicalFixture, TriageFactors


class FixtureProvider(Protocol):
    source_name: str
    observed_at: datetime | None

    async def list_fixtures(
        self, *, start_utc: datetime, end_utc: datetime, competition_ids: Sequence[str]
    ) -> tuple[CanonicalFixture, ...]: ...
    async def search_fixtures(
        self, *, query: str, start_utc: datetime | None, end_utc: datetime | None
    ) -> tuple[CanonicalFixture, ...]: ...

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture: ...


class TriageFeatureProvider(Protocol):
    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors: ...


class AnalysisFixtureProvider(Protocol):
    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture: ...

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors: ...


class LiveFixtureProvider(FixtureProvider, TriageFeatureProvider, Protocol):
    pass
