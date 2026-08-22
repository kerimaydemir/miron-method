import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict

from app.domain.fixtures import RankedFixture
from app.domain.ports import FixtureProvider, TriageFeatureProvider
from app.domain.scoring import worthwhile_score
from app.domain.time_window import three_day_window


class ScanResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scan_id: UUID
    status: str
    timezone: str
    local_dates: tuple[str, str, str]
    start_utc: datetime
    end_exclusive_utc: datetime
    candidates: tuple[RankedFixture, ...]
    correlation_id: UUID
    created_at: datetime
    source: str
    source_observed_at: datetime | None


class ScanService:
    def __init__(
        self,
        provider: FixtureProvider,
        triage: TriageFeatureProvider,
        clock: Callable[[], datetime],
    ) -> None:
        self.provider, self.triage, self.clock = provider, triage, clock
        self._results: dict[str, tuple[str, ScanResult]] = {}
        self._lock = asyncio.Lock()

    async def start(
        self, *, idempotency_key: str, request_hash: str, correlation_id: UUID
    ) -> ScanResult:
        async with self._lock:
            replay = self._results.get(idempotency_key)
            if replay:
                if replay[0] != request_hash:
                    raise ValueError("IDEMPOTENCY_CONFLICT")
                return replay[1]
            now = self.clock()
            window = three_day_window(now)
            fixtures = await self.provider.list_fixtures(
                start_utc=window.start_utc, end_utc=window.end_exclusive_utc, competition_ids=[]
            )
            candidates = []
            for fixture in fixtures:
                factors = await self.triage.features_for(fixture)
                score = worthwhile_score(factors)
                negatives = (
                    ("Kimlik eşleşmesi incelenmeli",)
                    if factors.unresolved_identity_penalty > 0
                    else (("Bazı veriler eski",) if factors.stale_data_penalty > 0 else ())
                )
                candidates.append(
                    RankedFixture(
                        fixture=fixture,
                        worthwhile_score=score,
                        estimated_cost_usd=Decimal("0.21") if score >= 80 else Decimal("0.12"),
                        positive_factors=("Canlı OpenLigaDB verisi", "Güncel fikstür")
                        if self.provider.source_name == "openligadb"
                        else (
                            ("Güçlü veri kapsamı", "Güncel kaynaklar")
                            if score >= 80
                            else ("Analiz bilgi kazanımı",)
                        ),
                        negative_factors=negatives,
                        coverage_label="Mükemmel"
                        if factors.coverage_score >= Decimal(".9")
                        else "Orta",
                        market_label="Güçlü"
                        if factors.market_coverage_score >= Decimal(".75")
                        else "Sınırlı",
                    )
                )
            result = ScanResult(
                scan_id=uuid5(NAMESPACE_URL, f"miron-baba-ai:scan:{idempotency_key}"),
                status="completed",
                timezone="Europe/Istanbul",
                local_dates=tuple(item.isoformat() for item in window.local_dates),
                start_utc=window.start_utc,
                end_exclusive_utc=window.end_exclusive_utc,
                candidates=tuple(
                    sorted(candidates, key=lambda item: item.worthwhile_score, reverse=True)
                ),
                correlation_id=correlation_id,
                created_at=now,
                source=self.provider.source_name,
                source_observed_at=self.provider.observed_at,
            )
            self._results[idempotency_key] = (request_hash, result)
            return result


def utc_now() -> datetime:
    return datetime.now(UTC)
