from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from app.domain.fixtures import CanonicalFixture, TriageFactors


def _fixture(
    seed: str, kickoff: datetime, home: str, away: str, competition: str, competition_name: str
) -> CanonicalFixture:
    return CanonicalFixture(
        id=uuid5(NAMESPACE_URL, f"miron-baba-ai:{seed}"),
        competition_key=competition,
        competition_name=competition_name,
        home_team=home,
        away_team=away,
        kickoff_at=kickoff,
        venue_name=f"{home} Stadyumu",
    )


FIXTURES = (
    _fixture(
        "FIX-IST-001",
        datetime(2026, 8, 22, 17, 0, tzinfo=UTC),
        "Anka FK",
        "Boğaz SK",
        "TR-SEED",
        "Marmara Ligi",
    ),
    _fixture(
        "FIX-IST-002",
        datetime(2026, 8, 23, 13, 0, tzinfo=UTC),
        "Marmara 1923",
        "Ege Atletik",
        "TR-SEED",
        "Marmara Ligi",
    ),
    _fixture(
        "FIX-IST-003",
        datetime(2026, 8, 24, 18, 45, tzinfo=UTC),
        "Toros Birlik",
        "Trakya Spor",
        "TR-SEED",
        "Marmara Ligi",
    ),
    _fixture(
        "FIX-IST-004",
        datetime(2026, 8, 24, 20, 30, tzinfo=UTC),
        "Başkent Gücü",
        "Karadeniz FK",
        "TR-CUP",
        "Anadolu Kupası",
    ),
)


def _f(*values: str) -> TriageFactors:
    return TriageFactors(
        **dict(zip(TriageFactors.model_fields, (Decimal(value) for value in values), strict=True))
    )


FEATURES = (
    _f(".98", ".95", ".92", ".86", ".90", ".85", ".90", ".80", ".95", ".08", "0", "0"),
    _f(".74", ".55", ".76", ".72", ".62", ".55", ".65", ".70", ".82", ".12", "0", ".25"),
    _f(".68", ".78", ".72", ".80", ".50", ".72", ".60", ".52", ".78", ".10", ".55", "0"),
    _f(".88", ".90", ".84", ".79", ".76", ".70", ".78", ".66", ".58", ".09", "0", "0"),
)


class MockFixtureProvider:
    source_name = "mock_fixture"
    observed_at: datetime | None = None

    async def list_fixtures(
        self, *, start_utc: datetime, end_utc: datetime, competition_ids: Sequence[str]
    ) -> tuple[CanonicalFixture, ...]:
        return tuple(
            item
            for item in FIXTURES
            if start_utc <= item.kickoff_at < end_utc
            and (not competition_ids or item.competition_key in competition_ids)
        )

    async def search_fixtures(
        self, *, query: str, start_utc: datetime | None, end_utc: datetime | None
    ) -> tuple[CanonicalFixture, ...]:
        normalized = " ".join(query.casefold().split())
        if len(normalized) < 2:
            return ()
        return tuple(
            item
            for item in FIXTURES
            if normalized in f"{item.home_team} {item.away_team} {item.competition_name}".casefold()
            and (start_utc is None or item.kickoff_at >= start_utc)
            and (end_utc is None or item.kickoff_at < end_utc)
        )

    async def features_for(self, fixture: CanonicalFixture) -> TriageFactors:
        for candidate, factors in zip(FIXTURES, FEATURES, strict=True):
            if candidate.id == fixture.id:
                return factors
        raise KeyError(str(fixture.id))

    async def get_fixture(self, fixture_id: UUID) -> CanonicalFixture:
        fixture = next((item for item in FIXTURES if item.id == fixture_id), None)
        if fixture is None:
            raise KeyError(str(fixture_id))
        return fixture
